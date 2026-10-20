"""Explicit, pinned peer loading for the external public product adapter."""
from __future__ import annotations
from collections.abc import Mapping
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Final
from ck3_mod_acceptance_background_types import file_pin, json_object, object_field, text_field

ORDER: Final[tuple[str,...]] = ('r04_county_entry_window', 'r04_county_entry', 'r08_writer_common_adapter',
         'r08_writer_one_day', 'r08_parent_entry_controller', 'r08_parent_entry_one_day')


def load(context: Mapping[str,object]) -> ModuleType:
    settings=object_field(json_object(context['case_inputs']),'r08_parent_entry_one_day')
    ref=file_pin(settings['bundle_index_pin'])
    path = Path(ref['path'])
    if not 0 < path.stat().st_size == ref['bytes'] <= 65536:
        raise ValueError('Bounded exact external source index required')
    payload = path.read_bytes()
    if len(payload)!=ref['bytes'] or hashlib.sha256(payload).hexdigest() != ref['sha256']:
        raise ValueError('External source index changed')
    value = json_object(json.loads(payload))
    if set(value) != {'schema', 'files', 'modules'} or value['schema'] != 'xar.e04.parent.public-source-bundle.v1':
        raise ValueError('External source schema')
    rows=value['files']
    if not isinstance(rows,list):raise ValueError('Explicit source file list required')
    files: set[str]=set()
    for row in rows:
        item=file_pin(row)
        p = Path(item['path'])
        if item['path'] in files:raise ValueError('Duplicate source pin')
        if p.stat().st_size != item['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Explicit bundle peer changed: '+str(p))
        files.add(item['path'])
    modules=object_field(value,'modules')
    if set(modules) != set(ORDER):
        raise ValueError('Exact finite peer module list required')
    sources={name:Path(text_field(modules,name)) for name in ORDER}
    for name,source in sources.items():
        if str(source) not in files or source.name!=name+'.py':raise ValueError('Module not in source pins')
    cached=True
    for name in ORDER:
        existing=sys.modules.get('ck3_mod_acceptance_cases.'+name)
        if existing is None or existing.__file__ is None or Path(existing.__file__).resolve()!=sources[name].resolve():
            cached=False
            break
    if cached:
        return sys.modules['ck3_mod_acceptance_cases.r08_parent_entry_one_day']
    for name in ORDER:
        source = sources[name]
        if str(source) not in files or source.name != name+'.py':
            raise ValueError('Module not in source pins')
        qualified = 'ck3_mod_acceptance_cases.'+name
        spec = importlib.util.spec_from_file_location(qualified, source)
        if spec is None or spec.loader is None:raise ValueError('Explicit source loader unavailable')
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
        package = sys.modules['ck3_mod_acceptance_cases']
        setattr(package, name, module)
    return sys.modules['ck3_mod_acceptance_cases.r08_parent_entry_one_day']
