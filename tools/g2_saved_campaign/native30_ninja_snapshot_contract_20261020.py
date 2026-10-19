"""Read-only validation of the exact configured Ninja inputs, not a Ninja evaluator."""
import hashlib
import json
import os
from pathlib import Path
import re

def require(value, message):
    if not value: raise RuntimeError(message)

def pin(path):
    path = Path(path)
    stat = path.stat()
    with path.open("rb") as stream: digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path.resolve()), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": digest}

def glob_contract(build, source):
    script = build/"CMakeFiles/VerifyGlobs.cmake"
    require(script.stat().st_size <= 128*1024, "bounded exact glob metadata")
    text = script.read_text(encoding="utf-8", errors="surrogateescape")
    pattern = r'file\(GLOB NEW_GLOB LIST_DIRECTORIES true "([^"\n]+)"\)\s+set\(OLD_GLOB\s*((?:"[^"\n]+"\s*)*)\)'
    matches = list(re.finditer(pattern, text))
    expected = [(source/"src"/name).as_posix() for name in ("ck3_12002*.cpp", "ck3_12002_*_test.cpp")]
    require([m[1] for m in matches] == expected, "only the two actual configured glob families")
    report = []
    for match in matches:
        old = re.findall(r'"([^"\n]+)"', match[2])
        require(len(old) <= 4096 and len(old) == len(set(old)), "finite unique historical glob")
        literal = Path(match[1])
        actual = sorted(path.as_posix() for path in literal.parent.glob(literal.name))
        require(actual == old, "actual frozen source glob differs: "+literal.name)
        report.append({"pattern": match[1], "entries": len(actual),
            "ordered_paths_sha256": hashlib.sha256(json.dumps(actual).encode()).hexdigest(), "equal": True})
    return {"script": pin(script), "families": report, "script_executed": False}

def ninja_tokens(line):
    """Decode only a generated, literal build-edge word list; reject variables."""
    values, word, index = [], bytearray(), 0
    while index < len(line):
        char = line[index]
        if char == 36:
            index += 1
            require(index < len(line) and line[index] in (32, 36, 58), "unresolved Ninja path variable/escape")
            word.append(line[index])
        elif char in (32, 9):
            if word: values.append(bytes(word)); word.clear()
        else: word.append(char)
        index += 1
    if word: values.append(bytes(word))
    return values

def configured_inputs(build, source):
    manifest, rules = build/"build.ninja", build/"CMakeFiles/rules.ninja"
    require(manifest.stat().st_size <= 32*1024**2, "finite original manifest")
    logical, pending = [], bytearray()
    with manifest.open("rb") as stream:
        for raw in stream:
            line = raw.rstrip(b"\r\n")
            if line.endswith(b"$"):
                pending.extend(line[:-1]); continue
            pending.extend(line)
            require(len(pending) <= 1024**2, "finite generated logical edge")
            if pending.startswith((b"build build.ninja ", b"include ", b"subninja ", b"builddir ")):
                logical.append(bytes(pending))
            pending.clear()
    require(not pending, "unfinished manifest continuation")
    includes = [v for v in logical if v.startswith((b"include ", b"subninja "))]
    require(includes == [b"include CMakeFiles\\rules.ninja"], "unexpected manifest include graph")
    builddir = [v for v in logical if v.startswith(b"builddir ")]
    require(not builddir, "unexpected Ninja log/deps relocation")
    edges = [v for v in logical if v.startswith(b"build build.ninja ")]
    require(len(edges) == 1, "one original manifest regeneration edge")
    marker = b": RERUN_CMAKE "
    require(edges[0].count(marker) == 1, "literal generated regeneration rule")
    words = ninja_tokens(edges[0].split(marker, 1)[1])
    require(words.count(b"|") == 1 and b"||" not in words, "unexpected regeneration edge grammar")
    paths = [Path(os.fsdecode(word)) for word in words if word != b"|"]
    paths = [(p if p.is_absolute() else build/p).resolve() for p in paths]
    require(len(paths) <= 4096 and len(paths) == len(set(paths)), "finite unique regeneration inputs")
    require((build/"CMakeCache.txt").resolve() in paths, "cache missing from actual regeneration inputs")
    require((build.parent/"attempt04/fixture-only-override.cmake").resolve() in paths,
            "actual configured04 override missing from regeneration inputs")
    require((build.parent/"attempt02/runtime-source-macro-restore.cmake").resolve() in paths,
            "original source macro overlay missing from regeneration inputs")
    identity = pin(manifest)
    inputs = [pin(path) for path in paths]
    require(all(row["mtime_ns"] <= identity["mtime_ns"] for row in inputs),
            "a real regeneration input is newer than the configured manifest")
    return {"manifest": identity, "rules": pin(rules), "glob": glob_contract(build, source), "inputs": inputs,
        "inputs_sha256": hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
        "cwd": str(build.resolve()), "relative_include": "CMakeFiles\\rules.ninja",
        "logs": [str(build/".ninja_log"), str(build/".ninja_deps")],
        "snapshot_evaluation": "Explicit -f snapshot changes loader manifest only; all original bytes/rules/DAG/commands and build cwd remain identical."}

if __name__ == "__main__":
    import sys
    value = configured_inputs(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps({"manifest": value["manifest"], "glob": value["glob"],
        "regeneration_inputs": len(value["inputs"]), "inputs_sha256": value["inputs_sha256"]}))
