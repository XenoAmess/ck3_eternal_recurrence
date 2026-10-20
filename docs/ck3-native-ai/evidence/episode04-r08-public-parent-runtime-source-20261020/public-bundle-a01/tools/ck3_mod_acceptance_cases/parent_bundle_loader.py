"""Explicit, pinned peer loading for the external public product adapter."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

ORDER = ('r04_county_entry_window', 'r04_county_entry', 'r08_writer_common_adapter',
         'r08_writer_one_day', 'r08_parent_entry_controller', 'r08_parent_entry_one_day')


def load(context: dict) -> ModuleType:
    ref = context['case_inputs']['r08_parent_entry_one_day']['bundle_index_pin']
    path = Path(ref['path'])
    if not 0 < path.stat().st_size == ref['bytes'] <= 65536:
        raise ValueError('Bounded exact external source index required')
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != ref['sha256']:
        raise ValueError('External source index changed')
    value = json.loads(payload)
    if set(value) != {'schema', 'files', 'modules'} or value['schema'] != 'xar.e04.parent.public-source-bundle.v1':
        raise ValueError('External source schema')
    for item in value['files']:
        p = Path(item['path'])
        if p.stat().st_size != item['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Explicit bundle peer changed: '+str(p))
    files = {item['path'] for item in value['files']}
    if set(value['modules']) != set(ORDER):
        raise ValueError('Exact finite peer module list required')
    if all('ck3_mod_acceptance_cases.'+name in sys.modules and
           Path(sys.modules['ck3_mod_acceptance_cases.'+name].__file__).resolve() == Path(value['modules'][name]).resolve()
           for name in ORDER):
        return sys.modules['ck3_mod_acceptance_cases.r08_parent_entry_one_day']
    for name in ORDER:
        source = Path(value['modules'][name])
        if str(source) not in files or source.name != name+'.py':
            raise ValueError('Module not in source pins')
        qualified = 'ck3_mod_acceptance_cases.'+name
        spec = importlib.util.spec_from_file_location(qualified, source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
        package = sys.modules['ck3_mod_acceptance_cases']
        setattr(package, name, module)
    return sys.modules['ck3_mod_acceptance_cases.r08_parent_entry_one_day']
