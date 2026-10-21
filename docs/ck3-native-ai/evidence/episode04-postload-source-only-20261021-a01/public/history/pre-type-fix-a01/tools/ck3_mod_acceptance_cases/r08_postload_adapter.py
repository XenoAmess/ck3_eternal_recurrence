"""Explicit finite R10/postload adapter; ordinary planner never auto-loads it."""
from __future__ import annotations
from collections.abc import Mapping
from pathlib import Path
import importlib.util
import sys
from types import ModuleType
from typing import Protocol,runtime_checkable

Object=dict[str,object]

@runtime_checkable
class Actor(Protocol):
    def validate_contract(self,context: Mapping[str,object]) -> object: ...
    def run_case(self,context: Mapping[str,object],client: object) -> object: ...

def object_value(value: object) -> Object:
    if not isinstance(value,dict) or type(value) is not dict:raise ValueError('actual case object')
    result: Object={}
    for key,item in value.items():
        if not isinstance(key,str):raise ValueError('case string key')
        result[key]=item
    return result

def actor(context: Mapping[str,object]) -> Actor:
    inputs=object_value(context.get('case_inputs'))
    keys=('r04_county_entry','r06_refill_one_day','r08_writer_one_day','r08_parent_entry_one_day',
        'r08_parent_pointer_read_one_day','r08_parent_postload_one_day')
    if inputs.get('r08_parent_postload_one_day') is None or sum(inputs.get(key) is not None for key in keys)!=1:
        raise ValueError('Explicit sole postload mode required; ordinary planner does not auto-load it')
    if object_value(context.get('case_contract')).get('schema')!='xar.e04.r10-common-preparation.v1':
        raise ValueError('Existing R10 common preparation contract required')
    path=Path(__file__).with_name('postload_bundle_loader.py')
    name='ck3_mod_acceptance_cases.postload_bundle_loader'
    existing=sys.modules.get(name)
    if existing is None or existing.__file__ is None or Path(existing.__file__).resolve()!=path.resolve():
        spec=importlib.util.spec_from_file_location(name,path)
        if spec is None or spec.loader is None:raise ValueError('source loader unavailable')
        existing=importlib.util.module_from_spec(spec);sys.modules[name]=existing;spec.loader.exec_module(existing)
    method: object=getattr(existing,'load',None)
    if not callable(method):raise ValueError('actual source loader interface')
    value: object=method(context)
    if not isinstance(value,Actor):raise ValueError('actual postload actor interface')
    return value

def common(context: Mapping[str,object]) -> ModuleType:
    actor(context)
    module=sys.modules.get('ck3_mod_acceptance_cases.r10_prepare_adapter')
    if module is None:raise ValueError('actual pinned R10 library unavailable')
    return module

def validate_contract(context: Mapping[str,object]) -> None:
    actor(context).validate_contract(context)

def prepare_case(context: Mapping[str,object]) -> object:
    validate_contract(context)
    method: object=getattr(common(context),'prepare_case',None)
    if not callable(method):raise ValueError('actual R10 prepare interface')
    # R10's unchanged prepare validates common S0/plain configs; it performs no
    # observer, day, sampling, Game or SDK operation.
    return method(context)

def run_case(context: Mapping[str,object],client: object) -> Object:
    value=actor(context);value.validate_contract(context)
    method: object=getattr(common(context),'_run_case_impl',None)
    if not callable(method):raise ValueError('actual R10 common bounded query interface')
    initial: object=method(context,client)
    # Same caller-provided object; no new client, launcher, owner or SDK session.
    result=object_value(value.run_case(context,client))
    result['initial_common_readiness']=initial
    result['full_R08_qualified']=False
    return result

def verify_case(context: Mapping[str,object]) -> Object:
    return {'case_contract_qualified':False,'business_pass':False,'full_R08_qualified':False,
        'scope':'Exact day and typed postload capture are separate; payment/payer/cadence remain unqualified'}
