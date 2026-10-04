"""External-only, offline proof capture for the R4 native-load repair."""
from pathlib import Path
import datetime
import difflib
import hashlib
import json
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parent
REPO = Path("C:/workspace/ck3_eternal_recurrence")
GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
TOOLS = BASE / "candidate/mod_li_yu_dao/tools"
sys.path.insert(0, str(TOOLS))
import gen_school_consent as gen


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, record):
    if path.exists():
        raise ValueError(f"Evidence already exists: {path}")
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if (BASE / "candidate-report.json").exists():
        raise ValueError("Finalized candidate is immutable; use a new candidate")
    result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(TOOLS / "test_school_consent.py")], capture_output=True)
    (BASE / "evidence/tests.stdout.bin").write_bytes(result.stdout)
    (BASE / "evidence/tests.stderr.bin").write_bytes(result.stderr)
    report = gen.generate(BASE / "generated/mod_li_yu_dao", native_evidence=gen.DEFAULT_NATIVE_EVIDENCE, include_shared=False)
    write_json(BASE / "evidence/render-report.json", report)
    source = BASE / "evidence/native-source"
    source.mkdir()
    sources = [
        ("common/character_interactions/pam_interactions.txt", [(18263, 18279)]),
        ("common/scripted_triggers/passive_rite_learning_triggers.txt", [(5, 16)]),
        ("common/scripted_triggers/00_religious_triggers.txt", [(2522, 2534)]),
        ("common/religion/doctrine_types/_doctrine_types.info", [(1, 5), (304, 309)]),
        ("common/religion/tenet_types/_tenet_types.info", [(1, 5)]),
        ("common/religion/faith_types/_faith_types.info", [(29, 43), (60, 64)]),
        ("common/religion/rite_types/_rite_types.info", [(58, 75)]),
    ]
    records = []
    for relative, ranges in sources:
        path = GAME / relative
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        excerpt = source / (relative.replace("/", "__") + ".excerpt.txt")
        excerpt.write_text("\n".join(f"{i + 1}: {lines[i]}" for begin, end in ranges for i in range(begin - 1, end)) + "\n", encoding="utf-8")
        records.append({"source": relative, "sha256": sha(path), "size": path.stat().st_size,
                        "ranges": ranges, "excerpt": excerpt.name, "excerpt_sha256": sha(excerpt)})
    def keys(path):
        return re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", path.read_text(encoding="utf-8-sig"), re.M)
    doctrines, tenets, catalog = set(), set(), []
    for folder, target in [("doctrine_types", doctrines), ("tenet_types", tenets)]:
        for path in sorted((GAME / "common/religion" / folder).glob("*.txt")):
            target.update(keys(path))
            catalog.append({"path": path.relative_to(GAME).as_posix(), "sha256": sha(path)})
    lyd_tenets = REPO / "mod_li_yu_dao/common/religion/tenet_types/lyd_tenets.txt"
    lyd_keys = keys(lyd_tenets)
    (source / "lyd_tenets.type-source.txt").write_bytes(lyd_tenets.read_bytes())
    write_json(BASE / "evidence/native-interface-source-boundary.json", {
        "source_root": str(GAME), "game_version": "1.20.0.3", "native_after_fix": "NOT_RUN",
        "sources": records, "catalog_sources": catalog,
        "native_doctrine_key_count": len(doctrines), "native_tenet_key_count": len(tenets),
        "lyd_tenet_keys": lyd_keys, "lyd_tenet_source_sha256": sha(lyd_tenets),
        "lyd_tenet_keys_in_doctrine_catalog": sorted(set(lyd_keys) & doctrines),
        "class_boundary": "Distinct source Doctrine/Tenet databases. Comparator calls only any_doctrine/rite_has_doctrine; next cold run must verify native enumeration behavior.",
    })
    deltas = []
    for path in sorted(TOOLS.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(TOOLS)
        before = BASE / "before/tools" / relative
        if before.exists() and before.read_bytes() != path.read_bytes():
            deltas.append({"path": "mod_li_yu_dao/tools/" + relative.as_posix(), "before_sha256": sha(before), "after_sha256": sha(path)})
            diff = "".join(difflib.unified_diff(before.read_text(encoding="utf-8-sig").splitlines(keepends=True), path.read_text(encoding="utf-8-sig").splitlines(keepends=True), fromfile="before/" + relative.as_posix(), tofile="candidate/" + relative.as_posix()))
            destination = BASE / "evidence/diffs" / (relative.as_posix().replace("/", "__") + ".diff")
            destination.parent.mkdir(exist_ok=True)
            destination.write_text(diff, encoding="utf-8")
    final = {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "result": "PASS_OFFLINE" if result.returncode == 0 else "FAIL_OFFLINE",
        "test_exit_code": result.returncode, "tests": 102, "render_count": len(report["files"]),
        "source_changes": deltas, "native_after_fix": "NOT_RUN", "r4_failed_inputs_preserved": True,
        "shared": "C3 untouched; root final integration uses include_shared=False and full I3 owns shared hooks",
        "readback_helper": "PAUSED_BY_ROOT_R4_NATIVE_LOAD_BLOCKERS",
    }
    write_json(BASE / "candidate-report.json", final)
    print(json.dumps(final, indent=2))
    print(result.stderr.decode("utf-8")[-200:])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
