"""Read-only research observations of the fixed owned cache; never alter its transport."""
import os
import re
import socket
from urllib.parse import urlsplit
from evidence import atomic

KEYS = {'requests', 'upstream', 'hits', 'entries', 'bytes', 'uncached', 'errors', 'refused_handlers'}


def finite_stats(value):
    if (type(value) is not dict or set(value) != KEYS
            or any(type(v) is not int or not 0 <= v <= 8 * 1024 * 1024 for v in value.values())
            or value['entries'] > 1024 or value['requests'] > 4096
            or value['upstream'] + value['hits'] > value['requests']):
        raise ValueError()
    return dict(value)


def group_absent(pid):
    try:
        os.killpg(pid, 0)
        return False
    except ProcessLookupError:
        return True


def port_closed(port, timeout=.2):
    with socket.socket() as sock:
        sock.settimeout(timeout)
        return sock.connect_ex(('127.0.0.1', port)) != 0


def finite_row(row):
    fields = {'pid', 'pgid', 'port', 'returncode', 'stdin_closed', 'stdout_closed',
              'group_absent', 'port_closed', 'stats', 'closed'}
    if type(row) is not dict or set(row) != fields:
        raise ValueError()
    if type(row['pid']) is not int or row['pid'] <= 1 or row['pgid'] != row['pid'] or type(row['pgid']) is not int:
        raise ValueError()
    if row['port'] is not None and (type(row['port']) is not int or not 1 <= row['port'] <= 65535):
        raise ValueError()
    if row['returncode'] is not None and (type(row['returncode']) is not int or not -128 <= row['returncode'] <= 255):
        raise ValueError()
    for field in ['stdin_closed', 'stdout_closed', 'group_absent', 'port_closed']:
        if row[field] is not None and type(row[field]) is not bool:
            raise ValueError()
    if type(row['closed']) is not bool:
        raise ValueError()
    if row['closed'] and (row['returncode'] is None or row['port'] is None
            or any(row[name] is not True for name in ['stdin_closed', 'stdout_closed', 'group_absent', 'port_closed'])):
        raise ValueError()
    if row['stats'] is not None:
        finite_stats(row['stats'])
    return dict(row)


class CacheEvidence:
    def __init__(self, output, category):
        self.output, self.category = output, category
        self.rows, self.secondary = [], []

    def snapshot(self):
        atomic(self.output / 'owned-cache.json', self.rows, 16384)

    def failure(self, phase, error):
        if len(self.secondary) < 8:
            self.secondary.append({'phase': phase, 'category': self.category(error)})

    def launched(self, process):
        if self.rows or type(process.pid) is not int or process.pid <= 1:
            raise ValueError()
        self.rows.append({'pid': process.pid, 'pgid': process.pid, 'port': None,
                          'returncode': None, 'stdin_closed': None, 'stdout_closed': None,
                          'group_absent': None, 'port_closed': None, 'stats': None, 'closed': False})
        self.snapshot()

    def started(self, cache):
        parsed = urlsplit(cache.url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment
                or not re.fullmatch('/[0-9a-f]{32}', parsed.path)
                or parsed.port is None or not 1 <= parsed.port <= 65535
                or cache.process is None or len(self.rows) != 1
                or self.rows[0]['pid'] != cache.process.pid):
            raise ValueError()
        self.rows[0]['port'] = parsed.port
        self.snapshot()

    def closed(self, cache):
        # Failures here are secondary metadata; never replace a replay/cleanup error.
        if cache.process is None:
            return
        if len(self.rows) != 1 or self.rows[0]['pid'] != cache.process.pid:
            raise ValueError()
        row = self.rows[0]
        code = cache.process.poll()
        if code is not None and (type(code) is not int or not -128 <= code <= 255):
            raise ValueError()
        row['returncode'] = code
        row['stdin_closed'] = cache.process.stdin.closed if cache.process.stdin is not None else None
        row['stdout_closed'] = cache.process.stdout.closed if cache.process.stdout is not None else None
        for field, observe, arg in [('group_absent', group_absent, row['pid']),
                                    ('port_closed', port_closed, row['port'])]:
            if arg is not None:
                try:
                    row[field] = observe(arg)
                except BaseException as error:
                    self.failure(field, error)
        if cache.stats is not None:
            try:
                row['stats'] = finite_stats(cache.stats)
            except BaseException as error:
                self.failure('stats', error)
        row['closed'] = (code is not None and row['group_absent'] is True
                         and row['port_closed'] is True and row['stdin_closed'] is True
                         and row['stdout_closed'] is True)
        self.snapshot()
