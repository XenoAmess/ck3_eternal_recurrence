"""Shared-delete Windows reads for one external harness process only."""
from contextlib import contextmanager
import errno
import io
import json
import os
from pathlib import Path
import time

DELAYS = (.01, .02, .04, .08, .16)
_original_bytes = Path.read_bytes
_original_text = Path.read_text
_installed = False


def _read_once(path):
    if os.name != 'nt':
        return _original_bytes(Path(path))
    import ctypes
    from ctypes import wintypes
    import msvcrt
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL
    handle = create(str(Path(path)), 0x80000000, 1|2|4, None, 3, 0x08000080, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(int(handle), os.O_RDONLY|os.O_BINARY)
    except BaseException:
        close(handle)
        raise
    with os.fdopen(fd, 'rb') as stream:
        return stream.read()


def read_bytes(path, *, _reader=None, _sleep=None):
    reader, sleep = _reader or _read_once, _sleep or time.sleep
    for attempt in range(len(DELAYS)+1):
        try:
            return reader(Path(path))
        except OSError as error:
            code = getattr(error, 'winerror', None)
            transient = code in (5,32,33) or (code is None and error.errno in (errno.EACCES,errno.EBUSY))
            if not transient or attempt == len(DELAYS):
                raise
            sleep(DELAYS[attempt])


def read_text(path, encoding=None, errors=None, newline=None):
    # Decode once after the sharing retry. Invalid text/JSON is never retried.
    with io.TextIOWrapper(io.BytesIO(read_bytes(path)), encoding=encoding,
                          errors=errors, newline=newline) as stream:
        return stream.read()


def install():
    """Cover the unchanged Path callers in all imported helper modules."""
    global _installed
    if not _installed:
        Path.read_bytes = read_bytes
        Path.read_text = read_text
        _installed = True
    return {'scope':'this new external feeder interpreter only',
        'share_flags':['READ','WRITE','DELETE'],'retry_attempts':len(DELAYS)+1,
        'maximum_retry_sleep_seconds':sum(DELAYS),
        'SDK_process_or_sources_modified':False,'JSON_errors_retried':False}


def restore():
    """Restore only methods still installed by this module."""
    global _installed
    if Path.read_bytes is read_bytes:
        Path.read_bytes = _original_bytes
    if Path.read_text is read_text:
        Path.read_text = _original_text
    _installed = False


@contextmanager
def installed():
    """Temporary opt-in for an isolated harness process or a focused test."""
    prior = _installed
    install()
    try:
        yield
    finally:
        if not prior:
            restore()


def recovery_may_be_needed(sequence, root, queue, *, current_halt=None,
                          response_root=None, recovery_marker_pattern=None):
    """Avoid live cumulative-state reads before any exact failure/recovery marker."""
    root, queue = Path(root), Path(queue)
    if (queue/f'ROOT-REQUEST-HALTED-{sequence:04d}.json').exists():
        return True
    if any(queue.glob(recovery_marker_pattern or f'*FEEDER*{sequence:04d}.json')):
        return True
    prefix = queue.name.removesuffix('-queue')
    current = Path(current_halt) if current_halt is not None else root/f'ROOT-CURRENT-HALT-{prefix.upper()}.json'
    response_root = Path(response_root) if response_root is not None else root/(prefix+'-responses')
    if not current.exists():
        return False
    raw = read_bytes(current)
    if len(raw)>16384:
        raise ValueError('current HALT exceeds existing finite bound')
    halt = json.loads(raw)
    if not isinstance(halt,dict):
        raise ValueError('current HALT must be an object')
    request = halt.get('original_request') or {}
    number = request.get('sequence')
    return bool(type(number) is int and number>sequence
        and request.get('tool')=='ck3_auto_turn'
        and halt.get('original_response')==str(response_root/f'{number:04d}-1-result.json')
        and (queue/f'ROOT-REQUEST-HALTED-{number:04d}.json').exists())
