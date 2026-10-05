"""Actual local reads only: Git opt-in, Defender service/WMI and broker task.

This probe never runs the broker task, registers a task, or writes WMI settings.
"""
from __future__ import annotations
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
sys.dont_write_bytecode = True

def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {'path': path.resolve().as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def actual_read_only_probe(repo: Path) -> dict:
    tools = repo / 'tools'
    probe = {'schema': 'xar.actual-defender-read-only-probe.v1',
             'utc': datetime.now(timezone.utc).isoformat(),
             'repo': repo.resolve().as_posix(), 'settings_writes': 0, 'TaskRun_calls': 0,
             'source_helpers': [pin(tools / name) for name in ['run_native_msvc.py', 'register_project_exe_exclusions.py', 'project_exe_exclusion_broker_client.py']],
             'CI_environment_present': bool(os.environ.get('CI')),
             'admin_token': bool(ctypes.windll.shell32.IsUserAnAdmin()) if os.name == 'nt' else None}
    process = subprocess.run(['git', '--no-optional-locks', '-C', str(repo), 'config', '--local', '--bool', '--get', 'xar.defenderProjectExeExclusions'], capture_output=True)
    probe['actual_git_local_opt_in'] = {'argv': ['git', '--no-optional-locks', '-C', str(repo), 'config', '--local', '--bool', '--get', 'xar.defenderProjectExeExclusions'], 'returncode': process.returncode, 'stdout': process.stdout.decode(errors='replace').strip(), 'stderr': process.stderr.decode(errors='replace').strip()}
    try:
        import win32service
        manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        try:
            service = win32service.OpenService(manager, 'WinDefend', win32service.SERVICE_QUERY_STATUS | win32service.SERVICE_QUERY_CONFIG)
            try:
                status = win32service.QueryServiceStatusEx(service)
                config = win32service.QueryServiceConfig(service)
                probe['actual_WinDefend'] = {'status': status, 'start_type': config[1], 'disabled_start_type': config[1] == win32service.SERVICE_DISABLED, 'running': status['CurrentState'] == win32service.SERVICE_RUNNING}
            finally: win32service.CloseServiceHandle(service)
        finally: win32service.CloseServiceHandle(manager)
    except Exception as error:
        probe['actual_WinDefend'] = {'available': False, 'error_type': type(error).__name__, 'error': str(error)}
    try:
        import pythoncom
        import win32com.client.dynamic
        pythoncom.CoInitialize()
        locator = win32com.client.dynamic.Dispatch('WbemScripting.SWbemLocator')
        services = locator.ConnectServer('.', r'root\Microsoft\Windows\Defender')
        rows = list(services.ExecQuery('SELECT AMServiceEnabled,AntivirusEnabled,AntispywareEnabled,RealTimeProtectionEnabled,IsTamperProtected FROM MSFT_MpComputerStatus'))
        if len(rows) != 1: raise ValueError('Defender current status is not a unique WMI row')
        keys = ['AMServiceEnabled', 'AntivirusEnabled', 'AntispywareEnabled', 'RealTimeProtectionEnabled', 'IsTamperProtected']
        probe['actual_Defender_WMI_status'] = {'available': True, 'fields': {key: rows[0].Properties_.Item(key).Value for key in keys}}
        preferences = list(services.ExecQuery('SELECT ExclusionPath,ExclusionExtension,ExclusionProcess FROM MSFT_MpPreference'))
        if len(preferences) != 1: raise ValueError('Defender preference is not a unique WMI row')
        probe['actual_current_exclusion_read'] = {'arrays': {key: list(preferences[0].Properties_.Item(key).Value or []) for key in ['ExclusionPath', 'ExclusionExtension', 'ExclusionProcess']}, 'administrative_visibility_verified': probe['admin_token'] is True, 'new_output_registration_credit': False, 'boundary': 'A nonadmin read may hide arrays; this read alone never proves before/after settings success.'}
    except Exception as error:
        probe['actual_Defender_WMI_status'] = {'available': False, 'error_type': type(error).__name__, 'error': str(error)}
    try:
        path = tools / 'project_exe_exclusion_broker_client.py'
        spec = importlib.util.spec_from_file_location('_r10_actual_broker_probe', path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        backend = module.WindowsBackend()
        owner = backend.current_sid()
        probe['actual_fixed_broker_task'] = {'read_only_contract': backend.task_contract(owner), 'actual_caller_sid': owner, 'TaskRun_calls': 0, 'setting_success_credit': False}
    except Exception as error:
        probe['actual_fixed_broker_task'] = {'available': False, 'error_type': type(error).__name__, 'error': str(error), 'TaskRun_calls': 0, 'setting_success_credit': False}
    return probe

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    value = actual_read_only_probe(arguments.repo)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())
    print(json.dumps({'output': pin(arguments.output), 'opt_in': value['actual_git_local_opt_in'], 'WinDefend': value['actual_WinDefend'], 'WMI_status': value['actual_Defender_WMI_status'], 'broker_available': value['actual_fixed_broker_task'].get('available', True)}, indent=2, ensure_ascii=False))
