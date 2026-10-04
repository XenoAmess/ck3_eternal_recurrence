"""Deliver only this trailer through the pre-authorized OneDrive desktop folder."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time


DELIVERY_DIRECTORY = Path('C:/Users/1/OneDrive/CK3-War-AI-20260923')


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def cloud_state(path: Path) -> dict[str, object]:
    """Read cloud status attributes; never hydrate or download another file."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    cloud = ctypes.WinDLL('CldApi', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    cloud.CfGetPlaceholderStateFromAttributeTag.argtypes = [wintypes.DWORD, wintypes.DWORD]
    cloud.CfGetPlaceholderStateFromAttributeTag.restype = wintypes.DWORD

    class AttributeTagInfo(ctypes.Structure):
        _fields_ = [('FileAttributes', wintypes.DWORD), ('ReparseTag', wintypes.DWORD)]

    handle = kernel.CreateFileW(str(path), 0x80, 7, None, 3, 0x02000000, None)
    if handle == ctypes.c_void_p(-1).value:
        return {'state': 'query-failed', 'windows_error': ctypes.get_last_error()}
    try:
        attributes = AttributeTagInfo()
        if not kernel.GetFileInformationByHandleEx(handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
            return {'state': 'query-failed', 'windows_error': ctypes.get_last_error()}
        flags = int(cloud.CfGetPlaceholderStateFromAttributeTag(attributes.FileAttributes, attributes.ReparseTag))
        return {'state': 'in-sync' if flags != 0xFFFFFFFF and flags & 0x8 else 'not-yet-in-sync', 'placeholder_state': flags, 'file_attributes': int(attributes.FileAttributes), 'reparse_tag': int(attributes.ReparseTag), 'read_access': 'FILE_READ_ATTRIBUTES-only'}
    finally:
        kernel.CloseHandle(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--movie', type=Path, required=True)
    parser.add_argument('--receipt-directory', type=Path, required=True)
    parser.add_argument('--maximum-wait-seconds', type=int, default=300)
    args = parser.parse_args()
    source = args.movie.resolve()
    assert source.is_file() and source.suffix.lower() == '.mp4'
    assert DELIVERY_DIRECTORY.is_dir(), 'The configured OneDrive delivery directory is unavailable.'
    receipt_directory = args.receipt_directory.resolve()
    receipt_directory.mkdir(parents=True, exist_ok=False)
    source_sha = sha(source)
    destination = DELIVERY_DIRECTORY / f'超人强_越超人越强_宣传片_20261004_{source_sha[:8]}.mp4'
    if destination.exists():
        assert sha(destination) == source_sha, 'Retain the existing generation; do not overwrite it.'
    else:
        shutil.copyfile(source, destination)
    assert sha(destination) == source_sha
    journal = receipt_directory / 'sync-observations.jsonl'
    started = time.monotonic()
    observation: dict[str, object] = {}
    while True:
        observation = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), **cloud_state(destination)}
        with journal.open('a', encoding='utf-8') as output:
            output.write(json.dumps(observation, ensure_ascii=False) + '\n')
        print(json.dumps(observation, ensure_ascii=False), flush=True)
        if observation['state'] == 'in-sync' or time.monotonic() - started >= args.maximum_wait_seconds:
            break
        time.sleep(10)
    report = {'format_version': 1, 'kind': 'superman_qiang_onedrive_delivery', 'source_path': str(source), 'destination_path': str(destination), 'sha256': source_sha, 'bytes': source.stat().st_size, 'file_count_transferred': 1, 'local_copy_verified': True, 'cloud_sync_confirmed': observation.get('state') == 'in-sync', 'cloud_observation': observation, 'confirmation_api': 'CfGetPlaceholderStateFromAttributeTag / CF_PLACEHOLDER_STATE_IN_SYNC', 'confirmation_reference': 'https://learn.microsoft.com/en-us/windows/win32/api/cfapi/nf-cfapi-cfgetplaceholderstatefromattributetag'}
    (receipt_directory / 'delivery-receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['cloud_sync_confirmed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
