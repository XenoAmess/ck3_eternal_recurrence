"""Create-only a02 recipe producer; shares RawStat/Recipe with the consumer."""
from __future__ import annotations
import datetime
import json
from pathlib import Path
from r11_visual_contract_a02 import FilePin, RawStat, Recipe, decimal_from_native, integer, load_map, object_map, text

ROOT=Path("C:/ck3-e04-resume-20261020-a01/r11-r174-continuous-review-2200-a01")
OLD_RECIPE=ROOT/"R11-ONCE-CONTACT-RECIPE.prepared-a01.json"
NEW_RECIPE=ROOT/"R11-ONCE-CONTACT-RECIPE.prepared-a02.json"

def legacy_decimal(value: object, label: str) -> str:
    """Only immutable old Python JSON input may contain native uint64 numbers.
    Reject bool/float. Publish canonical text; never pass through JS Number.
    """
    if type(value) is not int:
        raise ValueError(label+" legacy native value must be exact int")
    return decimal_from_native(value,label)

def build_document() -> dict[str, object]:
    oldpin=FilePin.read(OLD_RECIPE)
    if oldpin.sha256!="45be441a3f3cbbcf7fc7e200fa96102c2a178aef42ed7bff6e2ed9df8c1175ff":
        raise ValueError("Immutable a01 recipe changed")
    row=load_map(OLD_RECIPE)
    legacy=object_map(row.get("retained_source_stat"),"legacy retained stat")
    expected=RawStat(integer(legacy.get("bytes"),"legacy bytes"),
        legacy_decimal(legacy.get("mtime_ns"),"mtime_ns"),
        legacy_decimal(legacy.get("st_dev"),"st_dev"),
        legacy_decimal(legacy.get("st_ino"),"st_ino"))
    raw=FilePin.parse(row.get("retained_source"),"retained_source")
    actual=RawStat.from_native(Path(raw.path).stat())
    if actual!=expected:
        raise ValueError("Retained source identity changed; no body read")
    binding=object_map(row.get("historical_binding"),"historical binding")
    binding["process_birth_filetime"]=legacy_decimal(binding.get("process_birth_filetime"),"process birth")
    row["schema"]="xar.e04.R11-R0174-prefix600-once-visual5-PROPOSAL.v2"
    row["status"]="TYPED_DECIMAL64_A02_SOURCE_ONLY_PENDING_UPDATED_CAP_ROOT_ONCE"
    row["prepared_at_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    row["retained_source_stat"]=actual.wire()
    row["historical_binding"]=binding
    row["source_stat_observed_at_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    row["runner"]=FilePin.read(ROOT/"r11_once_contacts_a02_final.py").wire()
    row["typed_contract"]=FilePin.read(ROOT/"r11_visual_contract_a02.py").wire()
    row["typed_recipe_producer"]=FilePin.read(Path(__file__)).wire()
    row["preserved_a01_recipe"]=oldpin.wire()
    row["preserved_a01_runner"]=FilePin.read(ROOT/"r11_once_contacts.prepared-a01.py").wire()
    row["execution_authorized"]=False
    row["producer_consumer_domain"]="RawStat.from_native/RawStat.wire producer; RawStat.parse consumer; canonical uint64 strings. Source legacy unchanged."
    row["type_check_policy"]="Actual mypy --check-untyped-defs --disallow-untyped-defs on producer/contract/runner/tests; no Any/cast/ignore suppressions."
    row["OS_process_readback"]="Typed standard-library tasklist process-name census and narrowly validated ctypes GetPriorityClass replace untyped psutil; no added observation of game/Steam."
    parsed=Recipe.parse(row)
    if parsed.retained_source_stat!=actual or parsed.process_birth_filetime!="134365505726865638":
        raise ValueError("Producer to consumer identity differs")
    return row

def freeze_recipe() -> FilePin:
    row=build_document()
    body=(json.dumps(row,ensure_ascii=True,indent=2)+"\n").encode()
    with NEW_RECIPE.open("xb") as stream:
        stream.write(body)
    parsed=Recipe.parse(load_map(NEW_RECIPE))
    if parsed.runner!=FilePin.read(ROOT/"r11_once_contacts_a02_final.py"):
        raise ValueError("Actual recipe readback differs")
    return FilePin.read(NEW_RECIPE)

def main() -> None:
    print(json.dumps(freeze_recipe().wire()))

if __name__=="__main__":
    main()
