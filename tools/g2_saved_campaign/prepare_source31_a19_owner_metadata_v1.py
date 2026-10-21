"""Typed A19 metadata bridge; preserves the exact original four-output owner."""
from __future__ import annotations
import ast
import sys
import uuid
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Literal, TypedDict
import prepare_source31_a19_cold_union_v1 as graph
Doc=graph.Doc
ExactRef=graph.ExactRef
Outputs=graph.Outputs
MACHINE,OWN,TARGET,PREP=graph.MACHINE,graph.OWN,graph.TARGET,graph.PREP
OWNER_PIN=(32080,"9adb2ebc1e23f732115b9af9013f53dc6fc07af67d298b297684c12b6543340d")
class RecordingRefsV1(TypedDict):
    request: ExactRef
    job: ExactRef
    started: ExactRef
    first_frame_admission: ExactRef
    publisher_started: ExactRef
class OwnerInputV1(TypedDict):
    schema: Literal["xar.C23-A19-cold-owner-metadata-input/v1"]
    machine_id: str
    execution_owner: Literal["Root"]
    root_direct_execution_release: Literal[True]
    observed_at_utc: str
    runtime_root: str
    cold_graph_plan: ExactRef
    cold_graph_quote: ExactRef
    full_storage_ref: ExactRef
    live_storage_ref: ExactRef
    actual_game: ExactRef
    sdk_freeze: ExactRef
    business_anchor: ExactRef
    mod_absence: ExactRef
    recording: RecordingRefsV1
def _load_v1() -> ModuleType:
    path=OWN/"prepare_source31_a18_owner_metadata_v1.py"
    raw=graph.read_ref(graph.fixed(path,OWNER_PIN),65536).decode()
    # All A18 labels are current owner labels. A17 historical constants remain unchanged.
    source=raw.replace("A18","A19").replace("a18","a19")
    source=graph.one(source,'"ROOT-C23-A19-ACTUAL-RECORDING-BINDING.json"',
        '"ROOT-C23-A19-COLD-OWNER-RECORDING-BINDING.json"')
    source=graph.one(source,"        adapter.metadata_scope(plan, namespace, runtime)",
        "        adapter.metadata_scope(plan, namespace, runtime)\n"
        '        namespace["BINDING_NAME"]=OUTPUT_NAMES[0]\n'
        '        namespace["OUTPUT_NAMES"]=OUTPUT_NAMES')
    function=graph.function_source_v1(source,"validate_source31_owner_basis_v1")
    begin=function.index('    closed = checked(plan["closure_ref"], 16384)')
    end=function.index('    base_ref = parse_ref(plan["sdk_base_ref"])')
    function=function[:begin]+'''    import prepare_source31_a19_cold_union_v1
    prepare_source31_a19_cold_union_v1.validate_closed_basis_v1(plan)
'''+function[end:]
    source=graph.one(source,graph.function_source_v1(source,"validate_source31_owner_basis_v1"),function)
    module=ModuleType("_a19_exact_owner_"+uuid.uuid4().hex)
    module.__file__=__file__
    sys.modules[module.__name__]=module
    exec(compile(source,"<A19 exact owner projection>","exec"),vars(module))
    vars(module).update(graph=graph,TARGET=TARGET,PRIOR=graph.PREVIOUS,
                        CLOSURE_PIN=graph.CLOSURE_PIN,ADAPTER_NAME=Path(graph.__file__).name)
    return module
def parse_owner_inputs_v1(value: object, *, at_utc: datetime) -> OwnerInputV1:
    parsed=graph.record(graph.dynamic(_load_v1(),"parse_owner_inputs_v1")(value,at_utc=at_utc))
    graph.need(set(parsed)==set(OwnerInputV1.__annotations__),"single A19 owner shape")
    recording=graph.record(parsed["recording"])
    graph.need(set(recording)==set(RecordingRefsV1.__annotations__),"five recording refs")
    return {"schema":"xar.C23-A19-cold-owner-metadata-input/v1","machine_id":graph.text(parsed["machine_id"]),
        "execution_owner":"Root","root_direct_execution_release":True,
        "observed_at_utc":graph.text(parsed["observed_at_utc"]),"runtime_root":graph.text(parsed["runtime_root"]),
        "cold_graph_plan":graph.refs(parsed["cold_graph_plan"]),"cold_graph_quote":graph.refs(parsed["cold_graph_quote"]),
        "full_storage_ref":graph.refs(parsed["full_storage_ref"]),"live_storage_ref":graph.refs(parsed["live_storage_ref"]),
        "actual_game":graph.refs(parsed["actual_game"]),"sdk_freeze":graph.refs(parsed["sdk_freeze"]),
        "business_anchor":graph.refs(parsed["business_anchor"]),"mod_absence":graph.refs(parsed["mod_absence"]),
        "recording":{"request":graph.refs(recording["request"]),"job":graph.refs(recording["job"]),
            "started":graph.refs(recording["started"]),"first_frame_admission":graph.refs(recording["first_frame_admission"]),
            "publisher_started":graph.refs(recording["publisher_started"])}}
def build_owner_inputs_v1(*, adapter_value: object, cold_graph_plan: ExactRef,
        cold_graph_quote: ExactRef, mod_absence: ExactRef, recording: RecordingRefsV1,
        at_utc: datetime) -> OwnerInputV1:
    module=_load_v1()
    value=graph.dynamic(module,"build_owner_inputs_v1")(adapter_value=adapter_value,
        cold_graph_plan=cold_graph_plan,cold_graph_quote=cold_graph_quote,mod_absence=mod_absence,
        recording=recording,at_utc=at_utc)
    return parse_owner_inputs_v1(value,at_utc=at_utc)
def validate_source31_owner_basis_v1(inputs: OwnerInputV1, adapter_value: object) -> tuple[object,Doc]:
    result=graph.previous.pair(graph.dynamic(_load_v1(),"validate_source31_owner_basis_v1")(inputs,adapter_value))
    return result[0],graph.record(result[1])
def cold_owner(inputs_value: object, *, adapter_value: object) -> tuple[Outputs,Doc]:
    result=graph.previous.pair(graph.dynamic(_load_v1(),"cold_owner")(inputs_value,adapter_value=adapter_value))
    out=graph.previous.outputs(result[0]);quote=graph.record(result[1])
    graph.need(quote.get("schema")=="xar.C23-A19-owner-preparation/v1" and len(out)==4
        and quote.get("gate_must_be_last") is True,"original four outputs; gate last")
    order=graph.sequence(quote["publish_order"])
    admission=graph.record(__import__("json").loads(out[TARGET/graph.text(order[1])]))
    plan=graph.checked(graph.record(inputs_value)["cold_graph_plan"],16384)
    graph.need(graph.refs(admission["actual_A18_closure"])==graph.refs(plan["closure_ref"]),"actual A18 owner authority")
    return out,quote
