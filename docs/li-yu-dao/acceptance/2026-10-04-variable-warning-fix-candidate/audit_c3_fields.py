"""Read-only C3 writer/real-consumer audit; no runtime generation or CK3."""
from pathlib import Path
import collections
import hashlib
import json
import re
import sys

BASE = Path(__file__).resolve().parent
MOD = Path("C:/workspace/ck3_eternal_recurrence/mod_li_yu_dao")
sys.path.insert(0, str(MOD.parent / "tools"))
from extract_auto_upgrade_buildings import Block, parse_clausewitz


def main():
    target = BASE / "c3-global-fields-report.json"
    if target.exists():
        raise ValueError("Report exists; use a new attempt")
    fields = collections.defaultdict(lambda: {"writers": [], "consumers": [], "removals": []})
    sources = {}
    def record(field, kind, path, definition, operation):
        if not isinstance(field, str) or not field.startswith("lyd_c3_"):
            return
        fields[field][kind].append({"path": path, "definition": definition, "operation": operation})
    def visit(block, path, definition, ancestors=()):
        for entry in block.entries:
            key, value = entry.key, entry.value
            for field in re.findall(r"var:(lyd_c3_[A-Za-z0-9_]+)", key):
                record(field, "consumers", path, definition, key)
            if isinstance(value, str):
                for field in re.findall(r"var:(lyd_c3_[A-Za-z0-9_]+)", value):
                    record(field, "consumers", path, definition, key + "=" + value)
                if key in {"has_variable", "has_character_flag", "has_title_flag", "has_global_variable"}:
                    record(value, "consumers", path, definition, key)
                elif key in {"add_character_flag", "add_title_flag", "add_global_flag"}:
                    record(value, "writers", path, definition, key)
                elif key in {"remove_variable", "remove_character_flag", "remove_title_flag", "clear_variable_list"}:
                    record(value, "removals", path, definition, key)
                elif key == "variable" and any(parent in {"any_in_list", "every_in_list", "random_in_list", "ordered_in_list", "is_in_list"} for parent in ancestors):
                    record(value, "consumers", path, definition, ancestors[-1])
            if isinstance(value, Block):
                names = [child.value for child in value.entries if child.key == "name" and isinstance(child.value, str)]
                for name in names:
                    if key in {"set_variable", "change_variable", "add_to_variable_list"}:
                        record(name, "writers", path, definition, key)
                    if key == "change_variable":
                        record(name, "consumers", path, definition, key)
                    if key in {"remove_list_variable", "clear_variable_list"}:
                        record(name, "removals", path, definition, key)
                visit(value, path, definition, ancestors + (key,))
    for folder in ["common", "events"]:
        for path in sorted((MOD / folder).rglob("*.txt")):
            relative = path.relative_to(MOD).as_posix()
            sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            ast = parse_clausewitz(path.read_text(encoding="utf-8-sig"))
            for definition in ast.entries:
                if isinstance(definition.value, Block):
                    visit(definition.value, relative, definition.key)
    result = {"scope": "Current production common/events C3 persistent fields and flags only; temporary saved scopes and localization excluded",
              "rule": "remove/clear is not a consumer; conditions/value reads/list enumeration are consumers",
              "source_sha256": sources, "fields": dict(sorted(fields.items())),
              "undefined": sorted(field for field, rows in fields.items() if rows["consumers"] and not rows["writers"]),
              "unconsumed": sorted(field for field, rows in fields.items() if rows["writers"] and not rows["consumers"]),
              "native_after_fix": "NOT_RUN", "tracked_writes": False}
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fields": len(fields), "undefined": result["undefined"], "unconsumed": result["unconsumed"]}, indent=2))


if __name__ == "__main__":
    main()
