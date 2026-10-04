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
    cloud.CfGetPlaceholderInfo.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    cloud.CfGetPlaceholderInfo.restype = ctypes.c_long
    cloud.CfGetSyncRootInfoByPath.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    cloud.CfGetSyncRootInfoByPath.restype = ctypes.c_long

    class AttributeTagInfo(ctypes.Structure):
        _fields_ = [('FileAttributes', wintypes.DWORD), ('ReparseTag', wintypes.DWORD)]

    class StandardInfo(ctypes.Structure):
        _fields_ = [('on_disk', ctypes.c_longlong), ('validated', ctypes.c_longlong), ('modified', ctypes.c_longlong), ('properties', ctypes.c_longlong), ('pin_state', wintypes.DWORD), ('in_sync_state', wintypes.DWORD), ('file_id', ctypes.c_longlong), ('sync_root_file_id', ctypes.c_longlong), ('identity_length', wintypes.DWORD)]

    before = path.stat()
    root_buffer = ctypes.create_string_buffer(4096)
    root_length = wintypes.DWORD()
    root_hr = cloud.CfGetSyncRootInfoByPath(str(path), 0, root_buffer, len(root_buffer), ctypes.byref(root_length))
    # Match the war-series probe: read attributes, OPEN_NO_RECALL|OPEN_REPARSE_POINT.
    handle = kernel.CreateFileW(str(path), 0x80, 7, None, 3, 0x300000, None)
    if handle == ctypes.c_void_p(-1).value:
        return {'state': 'query-failed', 'windows_error': ctypes.get_last_error()}
    try:
        attributes = AttributeTagInfo()
        if not kernel.GetFileInformationByHandleEx(handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
            return {'state': 'query-failed', 'windows_error': ctypes.get_last_error()}
        flags = int(cloud.CfGetPlaceholderStateFromAttributeTag(attributes.FileAttributes, attributes.ReparseTag))
        buffer = ctypes.create_string_buffer(4096)
        returned = wintypes.DWORD()
        hr = cloud.CfGetPlaceholderInfo(handle, 1, buffer, len(buffer), ctypes.byref(returned))
        result = {'placeholder_state': flags, 'file_attributes': int(attributes.FileAttributes), 'reparse_tag': int(attributes.ReparseTag), 'read_access': 'FILE_READ_ATTRIBUTES-only; OPEN_NO_RECALL', 'sync_root_hresult': f'0x{root_hr & 0xFFFFFFFF:08X}', 'placeholder_hresult': f'0x{hr & 0xFFFFFFFF:08X}', 'placeholder_returned_bytes': returned.value}
        if hr == 0:
            info = StandardInfo.from_buffer_copy(buffer)
            result.update({name: getattr(info, name) for name in ['on_disk', 'validated', 'modified', 'in_sync_state', 'sync_root_file_id']})
        after = path.stat()
        result['stable_size_mtime'] = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
        checks = {'sync_root_success': root_hr == 0, 'placeholder_success': hr == 0, 'expected_sync_root': result.get('sync_root_file_id') == 5910974510929700, 'in_sync': result.get('in_sync_state') == 1, 'validated_full_size': result.get('validated') == before.st_size, 'modified_zero': result.get('modified') == 0, 'stable_size_mtime': result['stable_size_mtime']}
        result.update(state='in-sync' if all(checks.values()) else 'not-yet-in-sync', checks=checks)
        return result
    finally:
        kernel.CloseHandle(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--movie', type=Path, required=True)
    parser.add_argument('--receipt-directory', type=Path, required=True)
    parser.add_argument('--maximum-wait-seconds', type=int, default=300)
    parser.add_argument('--name-prefix', default='超人强_越超人越强_宣传片_20261004')
    args = parser.parse_args()
    source = args.movie.resolve()
    assert source.is_file() and source.suffix.lower() == '.mp4'
    assert DELIVERY_DIRECTORY.is_dir(), 'The configured OneDrive delivery directory is unavailable.'
    receipt_directory = args.receipt_directory.resolve()
    receipt_directory.mkdir(parents=True, exist_ok=False)
    source_sha = sha(source)
    assert args.name_prefix and Path(args.name_prefix).name == args.name_prefix
    assert not any(character in args.name_prefix for character in '<>:"/\\|?*')
    destination = DELIVERY_DIRECTORY / f'{args.name_prefix}_{source_sha[:8]}.mp4'
    transferred = 0
    if destination.exists():
        assert sha(destination) == source_sha, 'Retain the existing generation; do not overwrite it.'
    else:
        shutil.copyfile(source, destination)
        transferred = 1
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
    report = {'format_version': 1, 'kind': 'superman_qiang_onedrive_delivery', 'confirmed_at_utc': datetime.now(timezone.utc).isoformat(), 'source_path': str(source), 'destination_path': str(destination), 'sha256': source_sha, 'bytes': source.stat().st_size, 'file_count_transferred_this_attempt': transferred, 'existing_copy_reused': transferred == 0, 'local_copy_verified': True, 'cloud_sync_confirmed': observation.get('state') == 'in-sync', 'cloud_observation': observation, 'confirmation_api': 'CfGetPlaceholderInfo / CF_PLACEHOLDER_STANDARD_INFO', 'confirmation_reference': 'https://learn.microsoft.com/en-us/windows/win32/api/cfapi/nf-cfapi-cfgetplaceholderinfo', 'war_series_reference': 'promo/ck3_native_war_ai/episode-02-battle-second-half/series-color-a06-20261001.md', 'remote_independent_readback_performed': False, 'other_cloud_files_downloaded': False, 'sync_settings_changed': False}
    (receipt_directory / 'delivery-receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['cloud_sync_confirmed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
