"""Pinned public loader for the bridge package's single running-input contract."""
import hashlib
import importlib.util
from pathlib import Path


def identity(path):
    path=Path(path).resolve();digest=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':digest.hexdigest()}


def validate_running_inputs(live,frozen):
    source=Path(__file__).resolve().parents[1]/'ck3_autonomous_player/src/xar_autoplayer/bridge/runtime_input_contract_v1.py'
    actual=identity(source)
    if frozen['files'].get(str(source.resolve()))!={key:actual[key] for key in ('bytes','sha256')}:
        raise ValueError('Shared bridge running-input implementation absent or changed in allocation pins')
    spec=importlib.util.spec_from_file_location('shared_bridge_runtime_input_contract',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.validate_running_inputs(live,frozen)
