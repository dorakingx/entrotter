"""Fixed research evidence hooks, preserving original values/errors without replay repairs."""
from hashlib import sha256
from pathlib import Path
from entrotter_engine.artifact import canonical
from entrotter_engine.evm import ExecutionError
from entrotter_engine.rpc import RPCError, safe_diagnostics, FAILURE_CODES, LOCAL, OwnedTraceRPC

MAX_REPORT = 8 * 1024 * 1024
# Existing exact literals still present in the reviewed candidate trace module.
# New cache errors remain finite 'other' codes; never stringify exceptions.
ERROR_CODES = {
    'Canonical trace execution budget exceeded': 'trace_budget_exceeded',
    'Trace upstream chain differs from source': 'source_chain_mismatch',
    'Pinned trace block is unavailable or mismatched': 'source_block_unavailable_or_mismatch',
    'Only the Ethereum mainnet Shanghai interval is supported': 'unsupported_interval',
    'Unsupported trace block gas limit': 'unsupported_block_gas_limit',
    'Trace parent block is unavailable or mismatched': 'parent_unavailable_or_mismatch',
    'Requested transaction prefix is unavailable': 'prefix_unavailable',
    'Trace transaction order or block binding differs': 'source_order_or_block_mismatch',
    'Original trace receipt is unavailable or mismatched': 'original_receipt_unavailable_or_mismatch',
    'Original receipt does not bind to transaction': 'original_receipt_binding_mismatch',
    'Trace prefix input exceeds 256 KiB': 'source_input_bound',
    'Owned trace node was not initialized': 'owned_node_uninitialized',
    'Owned trace fork does not match the original parent': 'owned_parent_mismatch',
    'Reconstructed signature does not match original transaction hash': 'signature_hash_mismatch',
    'Trace node did not mine the requested block': 'owned_block_not_mined',
    'Mined trace header differs from canonical input': 'owned_header_mismatch',
    'Mined trace coinbase or prevrandao differs': 'owned_header_mismatch',
    'Owned trace receipt transaction hash differs': 'owned_receipt_hash_mismatch',
    'Trace replay requires ENTROTTER_RPC_URL with archive state; no fallback': 'source_not_configured',
    'Canonical trace RPC failed; original inputs/state may be unavailable. No fixture substitution.': 'trace_rpc_failed',
}
RPC_METHODS = {'eth_chainId', 'eth_getBlockByNumber', 'eth_getTransactionReceipt', 'eth_getTransactionCount',
               'eth_sendRawTransaction', 'evm_setNextBlockTimestamp', 'evm_setBlockGasLimit', 'anvil_setCoinbase',
               'anvil_setNextBlockBaseFeePerGas', 'anvil_setNextBlockPrevRandao', 'evm_mine', 'eth_call'}


def error_code(error):
    # Access only a finite exact native args tuple. Subclasses can override args/str/repr.
    if type(error) is ExecutionError:
        args = error.args
        if type(args) is tuple and len(args) == 1 and type(args[0]) is str:
            code = ERROR_CODES.get(args[0])
            if code is not None:
                return code
            # New native suffix is accepted only by exact comparison against a
            # finite locally-generated set. Arbitrary args/text are never echoed.
            stem = 'Canonical trace RPC failed; original inputs/state may be unavailable. No fixture substitution.'
            for rpc_code in FAILURE_CODES:
                for method in LOCAL | OwnedTraceRPC.LOCAL_METHODS | {'unknown'}:
                    if args[0] == stem + f' [rpc_code={rpc_code}; rpc_method={method}]':
                        return 'trace_rpc_failed'
            return 'execution_error_other'
    return 'other_error'


def atomic(path: Path, value, limit):
    raw = canonical(value)
    if len(raw) > limit:
        raise ValueError()
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)


class Evidence:
    def __init__(self, output, request_id, prefix, category):
        self.output, self.request_id, self.prefix, self.category = output, request_id, prefix, category
        self.calls = 0
        self.stage = 'source_capture'
        self.source_sha256 = None
        self.secondary = []
        self.failures = []
        self.snapshots = []
        self.observing = False

    def failure(self, error, stage, method=None):
        if len(self.failures) < 8:
            row = {'stage': stage, 'method': method, 'category': self.category(error), 'code': error_code(error)}
            if isinstance(error, RPCError):
                row['rpc_diagnostics'] = safe_diagnostics(error)
                row['rpc_method_matches_observed'] = (row['rpc_diagnostics']['method'] == method) if method is not None else None
            self.failures.append(row)

    def snapshot(self, name, value, limit):
        try:
            atomic(self.output / name, value, limit)
            self.snapshots.append({'file': name, 'sha256': sha256((self.output / name).read_bytes()).hexdigest()})
        except Exception as error:
            self.secondary.append({'stage': self.stage, 'category': self.category(error), 'code': 'snapshot_failed'})

    def rpc_wrapper(self, rpc, location):
        original = rpc.call

        def call(method, *args, **kwargs):
            try:
                return original(method, *args, **kwargs)
            except BaseException as error:
                if not self.observing:
                    self.failure(error, location, method if type(method) is str and method in RPC_METHODS else 'other')
                raise
        return original, call

    def capture(self, original, plan, upstream, deadline):
        self.stage = 'source_capture'
        previous, observed = self.rpc_wrapper(upstream, 'source_capture')
        upstream.call = observed
        try:
            value = original(plan, upstream, deadline)
        except BaseException as error:
            self.failure(error, self.stage)
            raise
        finally:
            upstream.call = previous
        self.source_sha256 = sha256(canonical(value)).hexdigest()
        inputs = value['inputs']
        bound = len(inputs) == len(self.prefix) and all(
            (a['index'], a['hash'], a['raw'], a['sender']) == (b['index'], b['hash'], b['raw_signed_transaction'], b['recovered_signer'])
            for a, b in zip(inputs, self.prefix))
        self.stage = 'source_snapshot'
        self.snapshot('captured-source.json', {'request_id': self.request_id, 'source_sha256': self.source_sha256,
                                             'frozen_signed_prefix_bound': bound, 'source': value}, 512 * 1024)
        # Original capture return unchanged; diagnostics never replace or repair it.
        return value

    def replay(self, original, captured, url, skipped, deadline):
        self.calls += 1
        if self.calls > 2:
            raise ValueError()
        branch = 'baseline' if self.calls == 1 else 'candidate'
        self.stage = branch + '_replay'
        try:
            value = original(captured, url, skipped, deadline)
        except BaseException as error:
            self.failure(error, self.stage)
            raise
        self.stage = branch + '_snapshot'
        self.snapshot(branch + '-branch.json', {'request_id': self.request_id, 'source_sha256': self.source_sha256,
                                              'branch': branch, 'result': value}, MAX_REPORT)
        return value
