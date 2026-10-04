"""Fixed owned-node view calls only. Not a signed consumer action or provider attestation."""
from hashlib import sha256
import math
import re
import time
from evidence import atomic
from entrotter_engine.rpc import RPCError, safe_diagnostics

ORACLE = '0x54586be62e3c3580375ae3723c145253060ca0c2'
WETH = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
PROXY = '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419'
ZERO = '0x' + '00' * 20
UNIT = 100_000_000
SELECTORS = {'source': '0x92bf2be0', 'price': '0xb3596f07',
             'base_currency': '0xe19f4700', 'base_unit': '0x8c89b64f'}
PHASES = {(branch, phase) for branch in ('baseline', 'candidate') for phase in ('before', 'after')}
CODE_MAX_BYTES = 65536
OUTPUT_MAX_BYTES = 65536


class SignalStop(BaseException):
    """Private watchdog/cancellation delivery, never a transport TimeoutError."""


def word(value):
    if type(value) is not str or re.fullmatch(r'0x[0-9a-fA-F]{64}', value) is None:
        raise ValueError()
    return bytes.fromhex(value[2:])


def address(value):
    raw = word(value)
    if raw[:12] != bytes(12):
        raise ValueError()
    return '0x' + raw[12:].hex()


def uint(value):
    return int.from_bytes(word(value), 'big')


def code_identity(value):
    if type(value) is not str or len(value) > 2 + 2 * CODE_MAX_BYTES or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', value) is None:
        raise ValueError()
    raw = bytes.fromhex(value[2:])
    # Persist hash/length only, never four full bytecode copies or arbitrary response text.
    return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest(), 'nonempty': bool(raw)}


def finite_category(error):
    if isinstance(error, (TimeoutError, SignalStop)):
        return 'timeout'
    if isinstance(error, RPCError):
        return 'rpc_error'
    if isinstance(error, ValueError):
        return 'invalid_response'
    return 'other'


class ConsumerObserver:
    def __init__(self, output, request_id):
        self.output, self.request_id = output, request_id
        self.rows = []
        self.secondary = []

    def save(self):
        try:
            atomic(self.output / 'consumer-observations.json', {'request_id': self.request_id, 'rows': self.rows}, OUTPUT_MAX_BYTES)
        except Exception as error:
            if len(self.secondary) < 8:
                self.secondary.append({'category': finite_category(error), 'code': 'consumer_snapshot_failed'})

    def skipped(self, branch, phase):
        self._append({'branch': branch, 'phase': phase, 'raw': {}, 'decoded': {}, 'code': {},
                      'errors': [{'query': 'none', 'category': 'skipped_primary_failure'}]})

    def check_phase(self, branch, phase):
        if (branch, phase) not in PHASES or len(self.rows) >= 4 or any((x['branch'], x['phase']) == (branch, phase) for x in self.rows):
            raise ValueError()

    def _append(self, row):
        self.check_phase(row['branch'], row['phase'])
        self.rows.append(row)
        self.save()

    def observe(self, rpc, branch, phase, deadline):
        self.check_phase(branch, phase)
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            raise ValueError()
        row = {'branch': branch, 'phase': phase, 'raw': {}, 'decoded': {}, 'code': {}, 'errors': []}
        asset_word = '0' * 24 + WETH[2:]
        queries = [('oracle_code', 'eth_getCode', [ORACLE, 'latest'], code_identity),
                   ('proxy_code', 'eth_getCode', [PROXY, 'latest'], code_identity)]
        for name, selector in SELECTORS.items():
            payload = selector + asset_word if name in ('source', 'price') else selector
            queries.append((name, 'eth_call', [{'to': ORACLE, 'data': payload}, 'latest'],
                            address if name in ('source', 'base_currency') else uint))
        if rpc is None:
            row['errors'].append({'query': 'none', 'category': 'owned_rpc_unavailable'})
            self._append(row)
            return
        previous_timeout = rpc.timeout
        try:
            for name, method, params, decoder in queries:
                remaining = deadline - time.monotonic() if type(deadline) in (int, float) else 0
                if remaining <= 0:
                    row['errors'].append({'query': name, 'category': 'timeout'})
                    break
                rpc.timeout = min(2.0, remaining)
                try:
                    value = rpc.call(method, params)
                    decoded = decoder(value)
                    if method == 'eth_getCode':
                        row['code'][name] = decoded
                    else:
                        # Only exactly checked one-word ABI values can be persisted.
                        row['raw'][name] = value
                        row['decoded'][name] = decoded
                except Exception as error:
                    failure = {'query': name, 'category': finite_category(error)}
                    if isinstance(error, RPCError):
                        failure['rpc_diagnostics'] = safe_diagnostics(error)
                    row['errors'].append(failure)
        finally:
            rpc.timeout = previous_timeout
        self._append(row)

    def classify(self, producer_rows, protocol_verified):
        # Flags describe these owned read-only calls, never signed transaction dependence.
        reasons = set()
        if self.secondary:
            reasons.add('consumer_evidence_snapshot_error')
        keys = [(x.get('branch'), x.get('phase')) for x in self.rows]
        producer_keys = [(x.get('branch'), x.get('phase')) for x in producer_rows]
        if len(keys) != 4 or set(keys) != PHASES or len(set(keys)) != 4:
            reasons.add('incomplete_consumer_phases')
        if len(producer_keys) != 4 or set(producer_keys) != PHASES or len(set(producer_keys)) != 4:
            reasons.add('incomplete_producer_phases')
        if protocol_verified is not True:
            reasons.add('replay_not_verified')
        producers = {key: row for key, row in zip(producer_keys, producer_rows)}
        codes = {name: set() for name in ('oracle_code', 'proxy_code')}
        for row in self.rows:
            key = row['branch'], row['phase']
            if row.get('errors') or set(row.get('decoded', {})) != set(SELECTORS):
                reasons.add('consumer_query_error')
            data = row.get('decoded', {})
            if data.get('source') != PROXY:
                reasons.add('source_mismatch')
            if data.get('base_currency') != ZERO or type(data.get('base_unit')) is not int or data.get('base_unit') != UNIT:
                reasons.add('base_currency_or_unit_mismatch')
            for name in codes:
                identity = row.get('code', {}).get(name)
                if not identity or identity.get('nonempty') is not True or type(identity.get('bytes')) is not int or not 0 < identity['bytes'] <= CODE_MAX_BYTES:
                    reasons.add('empty_or_missing_code')
                else:
                    codes[name].add((identity['sha256'], identity['bytes']))
            producer = producers.get(key, {})
            feed = producer.get('decoded', {}).get('latestRoundData', {})
            answer = feed.get('answer')
            if producer.get('errors') or set(feed) != {'answer', 'round_id', 'started_at', 'updated_at', 'answered_in_round'} or any(type(x) is not int for x in feed.values()) or type(answer) is not int or answer <= 0:
                reasons.add('producer_feed_unproven')
            elif type(data.get('price')) is not int or data.get('price') != answer:
                reasons.add('consumer_price_feed_mismatch')
            if producer.get('decoded', {}).get('aggregator') != '0xe62b71cf983019bff55bc83b48601ce8419650cc':
                reasons.add('producer_source_mismatch')
        if any(len(identities) != 1 for identities in codes.values()):
            reasons.add('code_identity_changed_or_unproven')
        if not reasons:
            by_phase = {key: producers[key]['decoded']['latestRoundData'] for key in PHASES}
            before = by_phase[('baseline', 'before')]
            if before != by_phase[('candidate', 'before')] or before != by_phase[('candidate', 'after')]:
                reasons.add('initial_or_omission_feed_mismatch')
            after = by_phase[('baseline', 'after')]
            if after['answer'] == before['answer'] or after['round_id'] != before['round_id'] + 1:
                reasons.add('producer_update_unproven')
        return {'owned_read_only_price_observation_complete': not reasons,
                'unproven_reasons': sorted(reasons), 'phase_count': len(self.rows),
                'base_currency_unit_expected': UNIT,
                'scope': 'Owned-node read-only price observations only. No signed consumer transaction, deployed-code/provider authentication, loan/liquidation/trade, benefit/profit, full-block/opcode/state-root proof or broader G1 completion.'}
