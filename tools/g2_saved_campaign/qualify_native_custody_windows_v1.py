"""Opt-in Win32 mechanics on own Python, one <=32B file and a new private pipe.

No Game, Native bridge, existing pipe or canonical custody issuer is invoked.
This cannot establish a loaded-provider token or cross-process transfer proof.
"""
from __future__ import annotations

import argparse
import ctypes as c
from ctypes import wintypes as w
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_loaded_provider_windows_v1.py'
DATA = b'owned native custody mechanics\n'
assert len(DATA) <= 32


def stamp():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def require(condition, text):
    if not condition:
        raise RuntimeError(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-owned-mechanical', action='store_true', required=True)
    parser.add_argument('--expected-adapter-sha256', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    require(os.name == 'nt', 'Windows only')
    require(not args.receipt.exists(), 'receipt must be create-only')
    adapter_pin = pin(ADAPTER)
    require(adapter_pin['sha256'] == args.expected_adapter_sha256, 'adapter source epoch differs')
    machine = subprocess.check_output([sys.executable, str(ROOT / 'tools/ck3_live_run_id.py'),
                                      'machine'], text=True, timeout=10).strip()
    require(bool(machine), 'machine_id missing')
    sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
    from xar_autoplayer.bridge import native_loaded_provider_windows_v1 as adapter

    receipt = {'schema': 'xar.native30.windows-custody-owned-mechanics/v1',
        'machine_id': machine, 'started_utc': stamp(),
        'machine_id_source': 'tools/ck3_live_run_id.py machine, same tool process invocation',
        'tool': pin(Path(__file__).resolve()), 'adapter': adapter_pin,
        'scope': 'OWN_PYTHON_TINY_FILE_RANDOM_PRIVATE_PIPE_ONLY',
        'observations': {}, 'cleanup': {}, 'status': 'INCOMPLETE',
        'ck3_loaded_custody_qualified': False, 'provider_dto_issued': False,
        'controller_sdk_private_transfer': 'unknown: adapter method remains NotImplemented',
        'limits': {'CK3_Game_Native_calls': 0, 'existing_pipe_access': 0,
                   'desktop_screen_OBS_calls': 0, 'new_EXE_builds': 0,
                   'Defender_changes': 0, 'live_Driver_SAVE_reads': 0},
        'api_sources': [
            'https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew',
            'https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info',
            'https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject',
            'https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-connectnamedpipe',
            'https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid',
            'https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-gethandleinformation']}
    facade = None
    directory = path = None
    owned_tool_handles = []
    failure = None
    try:
        # This is the first actual Win32 adapter construction in this tool.
        facade = adapter.WindowsNativeCustodyFacadeV1(enabled=True)
        raw = facade._os()
        H, D, P = w.HANDLE, w.DWORD, w.LPVOID
        def bind(name, inputs, output):
            fn = getattr(raw.k, name)
            fn.argtypes, fn.restype = inputs, output
            return fn
        delete_file = bind('DeleteFileW', [w.LPCWSTR], w.BOOL)
        handle_info = bind('GetHandleInformation', [H, c.POINTER(D)], w.BOOL)
        create_pipe = bind('CreateNamedPipeW', [w.LPCWSTR, D, D, D, D, D, D, P], H)
        connect_pipe = bind('ConnectNamedPipe', [H, P], w.BOOL)
        wait_pipe = bind('WaitNamedPipeW', [w.LPCWSTR, D], w.BOOL)
        invalid = c.c_void_p(-1).value

        def valid(handle):
            return handle not in (None, 0, invalid)

        def closed_readback(handle):
            # Immediate check, before any new handle creation could reuse it.
            flags = D()
            c.set_last_error(0)
            ok = bool(handle_info(handle, c.byref(flags)))
            error = c.get_last_error()
            require(not ok and error == 6, 'own handle closure readback not ERROR_INVALID_HANDLE')
            return {'GetHandleInformation_success': ok, 'winerror': error}

        directory = Path(tempfile.mkdtemp(prefix='xar-own-custody-'))
        path = directory / 'owned-lease.bin'
        with path.open('xb') as output:
            output.write(DATA)
        file_handle = facade.open_read_shared_preload_dll(str(path))
        observed = facade.observe_dll(file_handle)
        require(observed.sha256 == hashlib.sha256(DATA).hexdigest(), 'held hash differs')
        require(observed.size == len(DATA) and len(observed.file_id) == 16, 'FileID/size differs')
        lease = asdict(observed)
        lease['file_id'] = observed.file_id.hex()
        lease['observed_utc'] = stamp()
        lease['fixture_bytes'] = len(DATA)
        receipt['observations']['fixed_held_file'] = lease

        c.set_last_error(0)
        writer = raw.create(str(path), 0x40000000, 7, None, 3, 0x80, None)
        writer_error = c.get_last_error()
        if valid(writer):
            owned_tool_handles.append(int(writer))
        require(not valid(writer) and writer_error == 32, 'read-share-only lease did not reject writer with sharing violation')
        c.set_last_error(0)
        deleted = bool(delete_file(str(path)))
        delete_error = c.get_last_error()
        require(not deleted and delete_error == 32 and path.exists(), 'preload lease did not deny delete')
        receipt['observations']['lease_denials'] = {
            'write_open_success': False, 'write_winerror': writer_error,
            'DeleteFile_success': deleted, 'delete_winerror': delete_error,
            'file_still_exists': path.exists(), 'observed_utc': stamp()}

        pseudo = raw.current()
        duplicate = facade.duplicate_target_read_handle(pseudo)
        process = facade.observe_process(duplicate)
        original = facade.observe_process(pseudo)
        require(process.pid == original.pid == os.getpid() == raw.current_process_id(), 'not our Python PID')
        require(process.creation_filetime == original.creation_filetime and process.creation_date == original.creation_date,
                'kernel duplicate process birth differs')
        require(process.executable == adapter._normal_dos(sys.executable) and process.alive is True,
                'current Python image/liveness differs')
        require(raw.wait(duplicate, 0) == 0x102, 'own process handle not WAIT_TIMEOUT')
        process_row = asdict(process)
        process_row['creation_filetime'] = str(process.creation_filetime)
        process_row['FILETIME_encoding'] = 'decimal exact integer string, never JSON floating point'
        process_row['WaitForSingleObject_zero_result'] = 0x102
        process_row['original_pseudo_handle_closed'] = False
        process_row['observed_utc'] = stamp()
        facade.close_owned_handle(duplicate)
        process_row['owned_duplicate_closed_readback'] = closed_readback(duplicate)
        receipt['observations']['own_process'] = process_row

        facade.close_owned_handle(file_handle)
        receipt['observations']['file_handle_closed_readback'] = closed_readback(file_handle)
        writer = raw.create(str(path), 0x40000000, 7, None, 3, 0x80, None)
        require(valid(writer), 'writer remained blocked after owned lease release')
        owned_tool_handles.append(int(writer))
        raw.close_handle(int(writer))
        owned_tool_handles.remove(int(writer))
        receipt['observations']['writer_after_lease_release'] = {'opened': True, 'bytes_written': 0}

        # A new private self-peer pair; never inspect or connect an existing pipe.
        name = '\\\\.\\pipe\\xar-own-custody-' + uuid.uuid4().hex
        server = create_pipe(name, 3 | 0x80000, 8, 1, 32, 32, 1000, None)
        require(valid(server), 'CreateNamedPipe failed')
        server = int(server)
        owned_tool_handles.append(server)
        client = raw.create(name, 0xc0000000, 0, None, 3, 0, None)
        require(valid(client), 'own pipe client CreateFile failed')
        client = int(client)
        owned_tool_handles.append(client)
        c.set_last_error(0)
        connected = bool(connect_pipe(server, None))
        connect_error = c.get_last_error()
        require(connected or connect_error == 535, 'own synchronous pipe not connected')
        peer = raw.pipe_client_pid(server)
        require(peer == os.getpid(), 'kernel pipe peer is not own Python')
        try:
            raw.pipe_client_pid(client)
        except ValueError as error:
            client_rejected = str(error)
        else:
            raise RuntimeError('client end incorrectly admitted as a server end')
        require('not the server end' in client_rejected, 'wrong client-end negative')
        for own in (client, server):
            raw.close_handle(own)
            owned_tool_handles.remove(own)
            closed_readback(own)
        c.set_last_error(0)
        remains = bool(wait_pipe(name, 0))
        gone_error = c.get_last_error()
        require(not remains and gone_error == 2, 'private pipe closure not read back absent')
        receipt['observations']['private_pipe'] = {'name': name, 'kernel_client_pid': peer,
            'expected_own_pid': os.getpid(), 'ConnectNamedPipe_success': connected,
            'ConnectNamedPipe_winerror': connect_error, 'client_end_negative': client_rejected,
            'closed_owned_ends': 2, 'WaitNamedPipe_after_close_success': remains,
            'WaitNamedPipe_after_close_winerror': gone_error, 'observed_utc': stamp()}
        require(pin(ADAPTER)['sha256'] == adapter_pin['sha256'], 'adapter bytes changed during mechanical run')
        receipt['status'] = 'PASS_OWNED_WIN32_MECHANICS_ONLY'
    except Exception as error:
        failure = error
        receipt['status'] = 'FAIL_RETAIN_ACTUAL_BOUNDARY'
        receipt['failure'] = {'type': type(error).__name__, 'text': str(error),
                              'winerror': getattr(error, 'winerror', None), 'observed_utc': stamp()}
    finally:
        errors = []
        if facade is not None:
            for handle in tuple(owned_tool_handles):
                try:
                    facade._os().close_handle(handle)
                    owned_tool_handles.remove(handle)
                except Exception as error:
                    errors.append(type(error).__name__ + ':' + str(error))
            receipt['cleanup']['adapter'] = facade.close_all_owned()
        receipt['cleanup']['tool_owned_handles_remaining'] = len(owned_tool_handles)
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except Exception as error:
                errors.append(type(error).__name__ + ':' + str(error))
            receipt['cleanup']['temporary_file'] = str(path)
            receipt['cleanup']['temporary_file_absent'] = not path.exists()
        if directory is not None:
            try:
                directory.rmdir()
            except Exception as error:
                errors.append(type(error).__name__ + ':' + str(error))
            receipt['cleanup']['temporary_directory_absent'] = not directory.exists()
        receipt['cleanup']['errors'] = errors
        receipt['ended_utc'] = stamp()
        if (errors or owned_tool_handles or
                receipt['cleanup'].get('adapter', {}).get('owned_handles_remaining', 0) or
                receipt['cleanup'].get('adapter', {}).get('temporary_mappings_remaining', 0)):
            receipt['status'] = 'FAIL_CLEANUP_UNVERIFIED'
        raw_receipt = (json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        require(len(raw_receipt) + Path(__file__).stat().st_size <= 32 * 1024,
                'tool/receipt exceed 32KiB scope')
        with args.receipt.open('xb') as output:
            output.write(raw_receipt)
        print(json.dumps({'status': receipt['status'], 'receipt': pin(args.receipt),
                          'machine_id': machine, 'ended_utc': receipt['ended_utc']}))
    return 0 if receipt['status'] == 'PASS_OWNED_WIN32_MECHANICS_ONLY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
