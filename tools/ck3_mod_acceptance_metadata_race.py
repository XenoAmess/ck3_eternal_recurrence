"""Bounded metadata-only handling of a vanished enumerated scene entry.

Required-root/scandir, access, native identity and accounting failures still fail
closed. This does not credit space or claim an atomic directory snapshot.
"""
import ctypes
from pathlib import Path


def _vanished(path, stage, error, diagnostics, probe=None):
    probe = probe or (lambda value: Path(value).lstat())
    try:
        probe(path)
    except FileNotFoundError:
        diagnostics['confirmed_vanished_entries'] += 1
        if len(diagnostics['examples']) < 16:
            diagnostics['examples'].append({'path': str(path), 'stage': stage,
                                             'error': repr(error)})
        return None
    except OSError as check_error:
        raise RuntimeError(f'Metadata absence check failed: {stage} {path}: '
                           f'{check_error!r}; original={error!r}') from check_error
    raise RuntimeError(f'Metadata operation failed on present entry: '
                       f'{stage} {path}: {error!r}') from error


def entry_stat(entry, diagnostics, probe=None):
    try:
        return entry.stat(follow_symlinks=False)
    except FileNotFoundError as error:
        return _vanished(entry.path, 'entry.stat', error, diagnostics, probe)
    except OSError as error:
        raise RuntimeError(f'Metadata stat failed: {entry.path}: {error!r}') from error


def open_metadata(path, native, diagnostics, probe=None, error_factory=None):
    # Identical flags/access/sharing to the original metadata observer.
    handle = native.K.CreateFileW(path, 0, 7, None, 3, 0x00200080, None)
    if handle != native.W.HANDLE(-1).value:
        return handle
    error = (error_factory or (lambda: ctypes.WinError(ctypes.get_last_error())))()
    if getattr(error, 'winerror', None) in (2, 3):
        return _vanished(path, 'CreateFileW', error, diagnostics, probe)
    raise RuntimeError(f'Metadata open failed: {path}: {error!r}') from error


def project_source(source):
    """Four inverse-checked seams; original identity/budgets/decision untouched."""
    seams = [
        ('    started = time.monotonic()\n    entries_count = 0',
         "    started = time.monotonic()\n    vanished = {'confirmed_vanished_entries': 0, 'examples': []}\n    entries_count = 0"),
        ('                    info = entry.stat(follow_symlinks=False)',
         '                    info = _race.entry_stat(entry, vanished)\n'
         '                    if info is None:\n                        continue'),
        ('                    handle = b.m.K.CreateFileW(entry.path, 0, 7, None, 3, 0x00200080, None)\n'
         '                    if handle == b.m.W.HANDLE(-1).value:\n'
         '                        raise ctypes.WinError(ctypes.get_last_error())',
         '                    handle = _race.open_metadata(entry.path, b.m, vanished)\n'
         '                    if handle is None:\n                        continue'),
        ("    return {'roots': result, **totals(union),",
         "    return {'vanished_entry_diagnostics': vanished, 'roots': result, **totals(union),"),
    ]
    projected = source
    for old, new in seams:
        if projected.count(old) != 1:
            raise RuntimeError('Original metadata observer seam differs')
        projected = projected.replace(old, new)
    inverse = projected
    for old, new in reversed(seams):
        inverse = inverse.replace(new, old)
    if inverse != source:
        raise RuntimeError('Original metadata observer inverse differs')
    return projected
