"""Pinned public loader for the bridge package's single running-input contract."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import TypedDict

from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field


class RuntimeInputSources(TypedDict):
    helper: FilePin
    contract: FilePin


def identity(path: str | Path) -> FilePin:
    path=Path(path).resolve();digest=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':digest.hexdigest()}


def runtime_input_source_pins() -> RuntimeInputSources:
    helper = Path(__file__).resolve()
    source = helper.parents[1] / 'ck3_autonomous_player/src/xar_autoplayer/bridge/runtime_input_contract_v1.py'
    return {'helper': identity(helper), 'contract': identity(source)}


def _load_source(source: Path) -> ModuleType:
    spec=importlib.util.spec_from_file_location('shared_bridge_runtime_input_contract',source)
    if spec is None or spec.loader is None:
        raise ValueError('Shared running-input source loader unavailable')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def load_runtime_input_sources(helper: Path) -> RuntimeInputSources:
    """Resolve through the actual selected consumer, including split C/S trees."""
    helper = helper.resolve()
    module = _load_source(helper)
    value = json_object(module.runtime_input_source_pins())
    if set(value) != {'helper', 'contract'}:
        raise ValueError('Closed actual running-input source closure required')
    result: RuntimeInputSources = {'helper': file_pin(value['helper']), 'contract': file_pin(value['contract'])}
    expected = helper.parents[1] / 'ck3_autonomous_player/src/xar_autoplayer/bridge/runtime_input_contract_v1.py'
    if result != {'helper': identity(helper), 'contract': identity(expected)}:
        raise ValueError('Running-input implementation crossed its actual helper source tree')
    return result


def validate_running_inputs(live: str | Path, frozen: JsonObject) -> JsonObject:
    sources = runtime_input_source_pins()
    files = object_field(frozen, 'files')
    for actual in (sources['helper'], sources['contract']):
        if files.get(actual['path']) != {'bytes': actual['bytes'], 'sha256': actual['sha256']}:
            raise ValueError('Shared bridge running-input implementation absent or changed in allocation pins')
    module = _load_source(Path(sources['contract']['path']))
    return json_object(module.validate_running_inputs(live, frozen))


def validate_allocated_running_inputs(helper: Path, live: Path, frozen: JsonObject) -> JsonObject:
    """Preview the very same running consumer before screen registration or Game."""
    load_runtime_input_sources(helper)
    module = _load_source(helper.resolve())
    return json_object(module.validate_running_inputs(live, frozen))
