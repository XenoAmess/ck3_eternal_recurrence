"""Finite source-pinned pointer-v2 peers; never infer an external package path."""
from __future__ import annotations
from collections.abc import Mapping
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Protocol, runtime_checkable

CORE = ('postload_wire','postload_models','postload_owner_binding','parent_postload_contract','postload_admission')
PUBLIC = ('r04_county_entry_window','r04_county_entry','r08_writer_common_adapter','ordinary_save_contract',
          'r08_writer_one_day','postload_public_models','r08_parent_postload_controller','r08_parent_postload_one_day','r10_prepare_adapter')


@runtime_checkable
class Entry(Protocol):
    def validate_contract(self, context: Mapping[str,object]) -> object: ...
    def run_case(self, context: Mapping[str,object], client: object) -> object: ...


def obj(value: object) -> dict[str,object]:
    if not isinstance(value,dict):
        raise ValueError('Source index object required')
    result: dict[str,object] = {}
    for key,item in value.items():
        if not isinstance(key,str):
            raise ValueError('Source key type')
        result[key] = item
    return result


def text(value: object) -> str:
    if not isinstance(value,str) or not value:
        raise ValueError('Source path/digest text required')
    return value


def verify(value: object) -> Path:
    row = obj(value)
    if set(row) != {'path','bytes','sha256'}:
        raise ValueError('Exact source pin required')
    path = Path(text(row['path'])).resolve()
    size = row['bytes']
    if not isinstance(size,int) or type(size) is not int or not 0 <= size <= 1048576 or path.stat().st_size != size:
        raise ValueError('Bounded source size')
    data = path.read_bytes()
    if len(data) != size or hashlib.sha256(data).hexdigest() != text(row['sha256']):
        raise ValueError('Source pin changed')
    return path


def load(context: Mapping[str,object]) -> Entry:
    cfg = obj(obj(context['case_inputs'])['r08_parent_postload_one_day'])
    ref = obj(cfg['bundle_index_pin'])
    index_path = verify(ref)
    if index_path.stat().st_size > 65536:
        raise ValueError('Bounded index required')
    value: object = json.loads(index_path.read_bytes())
    index = obj(value)
    if set(index) != {'schema','files','modules'} or index['schema'] != 'xar.e04.postload.public-source-bundle.v1':
        raise ValueError('Distinct pointer-v2 source index required')
    rows = index['files']
    if not isinstance(rows,list):
        raise ValueError('Explicit peer files required')
    files: set[Path] = set()
    for row in rows:
        path = verify(row)
        if path in files:
            raise ValueError('Duplicate source path')
        files.add(path)
    modules = obj(index['modules'])
    expected_names = set(CORE) | set(PUBLIC) | {'r08_postload_adapter','postload_bundle_loader'}
    if set(modules) != expected_names:
        raise ValueError('Exact finite pointer module graph required')
    sources = {name:Path(text(source)).resolve() for name,source in modules.items()}
    for name,source in sources.items():
        if source not in files or source.name != name+'.py':
            raise ValueError('Module missing source pin')
    for name in ('r08_postload_adapter','postload_bundle_loader'):
        # The real public entry loads this very external adapter. Do not silently
        # replace an unrelated canonical module to simulate a working route.
        existing = sys.modules.get('ck3_mod_acceptance_cases.'+name)
        if existing is None or existing.__file__ is None or Path(existing.__file__).resolve() != sources[name]:
            raise ValueError('Actual public bootstrap module differs: '+name)
    for name in (*CORE,*PUBLIC):
        qualified = name if name in CORE else 'ck3_mod_acceptance_cases.'+name
        source = sources[name]
        existing = sys.modules.get(qualified)
        if existing is not None and existing.__file__ is not None and Path(existing.__file__).resolve() == source:
            continue
        spec = importlib.util.spec_from_file_location(qualified,source)
        if spec is None or spec.loader is None:
            raise ValueError('Explicit source loader unavailable')
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
        if name in PUBLIC:
            setattr(sys.modules['ck3_mod_acceptance_cases'],name,module)
    actor = sys.modules['ck3_mod_acceptance_cases.r08_parent_postload_one_day']
    if not isinstance(actor,Entry):
        raise ValueError('Typed pointer actor interface unavailable')
    return actor
