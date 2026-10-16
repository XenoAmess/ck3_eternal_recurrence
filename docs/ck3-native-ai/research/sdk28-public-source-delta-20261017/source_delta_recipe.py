"""Source-only W -> actual SDK28 recipe. Verify/reconstruct in memory only.

No Game, process, Native endpoint, Driver JSON, SAVE, video or W write operation.
Newline normalization is UTF-8/no-NUL CRLF or CR -> LF; nothing else is stripped.
"""
from pathlib import Path
import argparse
import ast
import base64
import collections
import datetime as dt
import difflib
import hashlib
import io
import json
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
N = HERE.parent
R3 = N / "native21-cold-generation03"
FREEZE_SHA = "6da46c57f3844522fa7cec516098f75b7987c8f7ac4bc2845311e3078c405587"
MODE_SHA = "5a4fee5b4069f09a061b196a260f31988c1abe9ae7ba0632b3a054efa2a4a4ac"
BASELINE = "00a70009ebb0daca44e697d7373e771f752ed2ca"
PACKAGE_ROOTS = {"xar_autoplayer": "ck3_autonomous_player/src",
                 "ck3_workshop_mcp": "ck3_workshop_mcp/src"}
PEAK = 8388608


class SourceVerificationError(ValueError):
    pass


def require(condition, detail="Source reconstruction verification failed"):
    if not condition:
        raise SourceVerificationError(detail)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized(raw):
    if raw is None:
        return None, False
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw, False
    if b"\x00" in raw:
        return raw, False
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n"), True


def lines(raw):
    if not raw:
        return []
    parts = raw.decode("utf-8").split("\n")
    return [p+"\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def eol_recipe(raw):
    runs = []
    for match in re.finditer(b"\r\n|\r|\n", raw):
        value = {b"\n": "lf", b"\r\n": "crlf", b"\r": "cr"}[match.group()]
        if runs and runs[-1][0] == value:
            runs[-1][1] += 1
        else:
            runs.append([value, 1])
    return runs


def restore_eol(norm, runs):
    parts = norm.split(b"\n")
    require(sum(n for _, n in runs) == len(parts)-1, "Source reconstruction verification failed")
    ends = {"lf": b"\n", "crlf": b"\r\n", "cr": b"\r"}
    out, index = [], 0
    for style, count in runs:
        for _ in range(count):
            out.extend((parts[index], ends[style]))
            index += 1
    out.append(parts[-1])
    return b"".join(out)


def git(w, *args):
    return subprocess.run(["git", "-C", str(w), *args], capture_output=True, check=True).stdout


def git_blobs(w, requests):
    requests = list(dict.fromkeys(requests))
    if not requests:
        return {}
    raw = subprocess.run(["git", "-C", str(w), "cat-file", "--batch"],
        input=("\n".join(requests)+"\n").encode(), capture_output=True, check=True).stdout
    stream, result = io.BytesIO(raw), {}
    for request in requests:
        header = stream.readline().decode().rstrip("\n")
        if header.endswith(" missing"):
            result[request] = None
            continue
        oid, kind, size = header.split()
        require(kind == "blob", (request, kind))
        result[request] = stream.read(int(size))
        require(stream.read(1) == b"\n", "Source reconstruction verification failed")
    require(not stream.read(), "Source reconstruction verification failed")
    return result


def repo_relative(relative):
    return PACKAGE_ROOTS[relative.split("/")[0]] + "/" + relative


def public_inventory(w, head, include_working=True):
    result = set()
    for package, root in PACKAGE_ROOTS.items():
        prefix = root + "/"
        data = git(w, "ls-tree", "-r", "--name-only", head, "--", root).decode("utf-8")
        for path in data.splitlines():
            if path.startswith(prefix+package+"/") and "__pycache__" not in path and not path.endswith(".pyc"):
                result.add(path[len(prefix):])
        physical = w / root / package
        if include_working and physical.is_dir():
            found = subprocess.run(["rg", "--files", str(physical)], capture_output=True, check=True, text=True, encoding="utf-8").stdout
            result.update(Path(p).relative_to(w/root).as_posix() for p in found.splitlines()
                          if "__pycache__" not in Path(p).parts and not p.endswith(".pyc"))
    return result


def public_bytes(w, relative, head, blobs):
    path = w / repo_relative(relative)
    if path.is_file():
        return path.read_bytes(), "working_tree"
    raw = blobs.get(head+":"+repo_relative(relative))
    return raw, "git_blob_sparse_checkout" if raw is not None else "absent"


def rebuild(base, edit):
    norm, text = normalized(base or b"")
    require(sha(norm) == edit["public_normalized_sha256"], "Source reconstruction verification failed")
    require((base is None) == edit["public_absent"], "Source reconstruction verification failed")
    if edit["target_absent"]:
        return None
    if edit.get("binary_raw"):
        raw = base64.b64decode(edit["target_bytes_base64"], validate=True)
        require(sha(raw) == edit["actual_raw_sha256"], "Source reconstruction verification failed")
        return raw
    source, out, cursor = lines(norm), [], 0
    for change in edit["edits"]:
        require(cursor <= change["start"] <= change["end"] <= len(source), "Source reconstruction verification failed")
        out.extend(source[cursor:change["start"]])
        out.append(change["new_text"])
        cursor = change["end"]
    out.extend(source[cursor:])
    target = "".join(out).encode("utf-8")
    require(sha(target) == edit["actual_normalized_sha256"], "Source reconstruction verification failed")
    raw = restore_eol(target, edit["actual_eol_runs"])
    require(sha(raw) == edit["actual_raw_sha256"], "Source reconstruction verification failed")
    return raw


def imports_and_markers(relative, raw):
    if raw is None or not relative.endswith(".py"):
        return [], [], ""
    source = raw.decode("utf-8-sig")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], ["not-parseable-by-audit-interpreter"], ""
    doc = ast.get_docstring(tree) or ""
    explicit = [s for s in ("research", "experimental", "prototype", "source-only", "qualification", "研究", "实验") if s in doc.lower()]
    module = relative[:-3].replace("/", ".")
    package = module[:-9] if module.endswith(".__init__") else module.rsplit(".", 1)[0]
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend(x.name for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                bits = package.split(".")
                prefix = ".".join(bits[:len(bits)-node.level+1])
                target = prefix+("."+node.module if node.module else "")
            else:
                target = node.module or ""
            result.append(target)
            result.extend(target+"."+x.name for x in node.names if x.name != "*")
    return result, explicit, doc[:300]


def prepare(w):
    freeze_path = R3 / "ROOT-FINAL-SDK-FREEZE-P28.json"
    mode_path = R3 / "ROOT-ACTUAL-DRIVER-MODE-P28.json"
    freeze_raw, mode_raw = freeze_path.read_bytes(), mode_path.read_bytes()
    require(sha(freeze_raw) == FREEZE_SHA and sha(mode_raw) == MODE_SHA, "Source reconstruction verification failed")
    freeze, mode = json.loads(freeze_raw), json.loads(mode_raw)
    actual = Path(freeze["source_root"])
    require(Path(mode["source_file"]).parent.parent == actual/"xar_autoplayer", "Source reconstruction verification failed")
    require(freeze["source_file_count"] == len(freeze["files"]) == 1317, "Source reconstruction verification failed")
    admission_path = R3 / "STORAGE-ADMISSION.json"
    admission_raw = admission_path.read_bytes()
    admission = json.loads(admission_raw)
    now = dt.datetime.now(dt.timezone.utc)
    require(now < dt.datetime.fromisoformat(admission["review_at_utc"]), "Source reconstruction verification failed")
    require(shutil.disk_usage(HERE).free-PEAK >= admission["disk_reserve_bytes"], "Source reconstruction verification failed")
    head = git(w, "rev-parse", "HEAD").decode().strip()
    inventory = public_inventory(w, head)
    frozen = {x["relative"]: x for x in freeze["files"]}
    all_paths = sorted(set(frozen)|inventory)
    sparse = [head+":"+repo_relative(p) for p in all_paths if not (w/repo_relative(p)).is_file()]
    blobs = git_blobs(w, sparse)
    records, contents, graph = [], {}, collections.defaultdict(list)
    for relative in all_paths:
        base, basis = public_bytes(w, relative, head, blobs)
        target = (actual/relative).read_bytes() if relative in frozen else None
        if target is not None:
            require(len(target) == frozen[relative]["bytes"] and sha(target) == frozen[relative]["sha256"], relative)
        pn, pt = normalized(base)
        an, at = normalized(target)
        category = ("public_only" if target is None else "actual_only" if base is None else
                    "raw_equal" if base == target else "newline_only" if pn == an else "code_changed")
        imported, markers, doc = imports_and_markers(relative, target)
        for module in imported:
            graph[module].append(relative)
        row = dict(relative=relative, public_repo_relative=repo_relative(relative), category=category,
            public_basis=basis, actual_bytes=None if target is None else len(target),
            public_bytes=None if base is None else len(base),
            actual_raw_sha256=None if target is None else sha(target),
            public_raw_sha256=None if base is None else sha(base),
            actual_normalized_sha256=None if target is None else sha(an),
            public_normalized_sha256=None if base is None else sha(pn),
            normalization_kind="utf8_newlines" if (base is None or pt) and (target is None or at) else "binary_raw",
            actual_eol_runs=[] if target is None or not at else eol_recipe(target),
            explicit_experiment_markers=markers, source_docstring=doc if category not in ("raw_equal", "newline_only") else "")
        records.append(row)
        if category != "raw_equal":
            contents[relative] = (base, target, pn, an)
    changed = [r for r in records if r["category"] != "raw_equal"]
    ancestry = git_blobs(w, [BASELINE+":"+r["public_repo_relative"] for r in changed])
    payload, patch_parts, rebuilt = {}, [], 0
    for number, row in enumerate(changed, 1):
        relative = row["relative"]
        base, target, pn, an = contents[relative]
        ancestor = ancestry[BASELINE+":"+row["public_repo_relative"]]
        ancestor_n, _ = normalized(ancestor)
        row["baseline_normalized_sha256"] = None if ancestor is None else sha(ancestor_n)
        if row["category"] == "newline_only":
            origin = "newline_only"
        elif an == ancestor_n and pn != ancestor_n:
            origin = "public_advanced_from_runtime_baseline"
        elif pn == ancestor_n and an != ancestor_n:
            origin = "actual_runtime_overlay_from_baseline"
        else:
            origin = "diverged_or_distinct_additions"
        row["three_way_origin"] = origin
        module = relative[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[:-9]
        row["static_possible_importers_in_actual"] = sorted(set(graph[module]))
        row["experiment_classification"] = ("public_only_not_in_actual_frozen_tree" if target is None else
            "actual_included_with_explicit_research_or_qualification_marker" if row["explicit_experiment_markers"] else
            "actual_included_source_delta_no_new_live_acceptance")
        binary = row["normalization_kind"] == "binary_raw"
        pl, al = ([] if binary else lines(pn or b"")), ([] if binary else lines(an or b""))
        matcher = difflib.SequenceMatcher(None, pl, al)
        edits = [dict(start=i1, end=i2, new_text="".join(al[j1:j2]))
            for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]
        edit = dict(relative=relative, public_repo_relative=row["public_repo_relative"],
            target_absent=target is None, public_absent=base is None,
            public_normalized_sha256=sha(pn or b""), actual_normalized_sha256=None if target is None else sha(an),
            actual_raw_sha256=None if target is None else sha(target),
            actual_eol_runs=[] if target is None or binary else eol_recipe(target), edits=edits)
        if binary:
            edit.update(binary_raw=True, target_bytes_base64=None if target is None else base64.b64encode(target).decode("ascii"))
        require(rebuild(base, edit) == target, relative)
        rebuilt += 1
        name = f"recipes/{number:04d}.json"
        payload[name] = (json.dumps(edit,ensure_ascii=False,separators=(",", ":"))+"\n").encode()
        row["recipe"] = name
        row["recipe_sha256"] = sha(payload[name])
        if binary:
            patch_parts.append("Binary recipe "+name+" reconstructs "+row["public_repo_relative"]+" exactly; see pinned JSON.\n")
        elif pn != an:
            patch = list(difflib.unified_diff(pl, al,
                fromfile="/dev/null" if base is None else "a/"+row["public_repo_relative"],
                tofile="/dev/null" if target is None else "b/"+row["public_repo_relative"], n=3))
            patch_parts.extend(x if x.endswith("\n") else x+"\n\\ No newline at end of file\n" for x in patch)
    payload["W-TO-ACTUAL-SDK28-NORMALIZED.patch"] = "".join(patch_parts).encode("utf-8")
    counts = dict(collections.Counter(r["category"] for r in records))
    origin_counts = dict(collections.Counter(r["three_way_origin"] for r in changed))
    metadata = dict(schema="xar.sdk28.public-source-delta-metadata.v1", at_utc=now.isoformat(),
        machine_id=admission["machine_id"],
        machine_id_basis=dict(path=str(admission_path), sha256=sha(admission_raw)),
        actual_source_root=str(actual), actual_frozen_file_count=1317,
        actual_freeze=dict(path=str(freeze_path), sha256=FREEZE_SHA),
        actual_mode=dict(path=str(mode_path), sha256=MODE_SHA),
        actual_candidate_source=freeze["candidate_source"], actual_candidate_delivery=freeze["candidate_delivery"],
        public_worktree=str(w), public_head_at_start=head, public_head_at_end=git(w,"rev-parse","HEAD").decode().strip(),
        public_tracked_source_dirty_at_end=git(w,"status","--porcelain","--",*PACKAGE_ROOTS.values()).decode(),
        package_mapping=PACKAGE_ROOTS, baseline_commit=BASELINE,
        normalization="Strict UTF8/noNUL only; CRLF/CR->LF. Binary remains raw. BOM/EOF/content/space retained. Exact target EOL runs retained in recipes.",
        counts=counts, three_way_origin_counts=origin_counts, files=records,
        source_status="Actual freeze/mode bind SDK28Rev2; no SDK29 used. Source inclusion/static import does not prove live exercise or feature acceptance.",
        recipe_status="Research reconstruction only. Public-only future source deletions and public-ahead regressions are included for exact comparison, never production recommendations.",
        verification=dict(frozen_raw_pins_verified=1317, differing_raw_leaves_reconstructed_exactly=rebuilt,
                          all_rebuilt_raw_bytes_equal_retained_actual_source=True, calls_or_live_driver_reads=0))
    payload["METADATA.json"]=(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n").encode()
    budget=dict(schema="xar.sdk28.source-delta-budget.v1", at_utc=now.isoformat(),
        own_peak_bytes=PEAK, retained_packet_estimated_bytes=sum(map(len,payload.values())),
        common_root_extra_peak_bytes=16777216, reservation_group=admission["reservation_id"],
        additional_global_reservation_bytes=0, parent_admission=str(admission_path), parent_sha256=sha(admission_raw),
        review_at_utc=admission["review_at_utc"], actual_D_free_bytes=shutil.disk_usage(HERE).free,
        disk_reserve_bytes=admission["disk_reserve_bytes"], source_only=True,
        scope="Root authorized small performance/fix packet group; no rawDriver/SAVE/video/SDK copies; future verifier in-memory only.")
    payload["BUDGET.json"]=(json.dumps(budget,ensure_ascii=False,indent=2)+"\n").encode()
    estimate=sum(map(len,payload.values()))+Path(__file__).stat().st_size
    require(estimate < PEAK, estimate)
    for name, raw in payload.items():
        path=HERE/name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)
    print(json.dumps(dict(counts=counts, origin_counts=origin_counts, output_bytes=estimate,
        patch_bytes=len(payload["W-TO-ACTUAL-SDK28-NORMALIZED.patch"]),
        metadata_sha256=sha(payload["METADATA.json"]), rebuilt=rebuilt),ensure_ascii=False))


def verify(w, git_only=False, public_commit=None):
    metadata=json.loads((HERE/"METADATA.json").read_text(encoding="utf-8"))
    rows=metadata["files"]
    head=public_commit or (metadata["public_head_at_end"] if git_only else git(w,"rev-parse","HEAD").decode().strip())
    expected_inventory={r["relative"] for r in rows if r["public_bytes"] is not None}
    require(public_inventory(w,head,include_working=not git_only)==expected_inventory, "Public source inventory changed")
    sparse=[head+":"+r["public_repo_relative"] for r in rows if git_only or not (w/r["public_repo_relative"]).is_file()]
    blobs=git_blobs(w,sparse)
    count=actual_count=0
    for row in rows:
        if git_only:
            base=blobs[head+":"+row["public_repo_relative"]]
        else:
            if row["public_basis"]=="working_tree":
                require((w/row["public_repo_relative"]).is_file(), row["relative"])
            base,basis=public_bytes(w,row["relative"],head,blobs)
        require((base is None)==(row["public_bytes"] is None), row["relative"])
        require((None if base is None else sha(normalized(base)[0]))==row["public_normalized_sha256"], row["relative"])
        if "recipe" in row:
            raw=(HERE/row["recipe"]).read_bytes()
            require(sha(raw)==row["recipe_sha256"], "Source reconstruction verification failed")
            result=rebuild(base,json.loads(raw))
            count+=1
        else:
            norm,text=normalized(base)
            result=restore_eol(norm,row["actual_eol_runs"]) if text else base
        require((None if result is None else sha(result))==row["actual_raw_sha256"], "Source reconstruction verification failed")
        actual_count+=result is not None
    print(json.dumps(dict(status="PASS", changed_leaves_reconstructed=count, public_head=head,
                          frozen_actual_leaves_reconstructed=actual_count, git_blob_only=git_only,
                          source_writes=0, actual_source_reads=0, live_state_or_runtime_calls=0)))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "verify"))
    parser.add_argument("--public-root", "--repo", dest="public_root", type=Path, required=True, help="Explicit public Git repository; verify needs no external runtime inputs")
    parser.add_argument("--git-only", action="store_true", help="Verify all1317 target raw leaves from committed public blobs only")
    parser.add_argument("--public-commit", help="Optional explicit source commit; git-only defaults to the pinned metadata public commit")
    args=parser.parse_args()
    if args.mode=="prepare":
        prepare(args.public_root)
    else:
        verify(args.public_root,args.git_only,args.public_commit)
