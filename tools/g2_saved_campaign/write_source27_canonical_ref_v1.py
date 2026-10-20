"""Default OFF. Finite Source27 canonical Git writer; Root executes after admission."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from typing import TypedDict

sys.dont_write_bytecode = True
MACHINE = "xenoamess-full-tower-eb9d2c1186"
BASE = "394865df3259be5db29014ab1d17db7bdd48c21d"
REF = "refs/heads/campaign/robert-v20261020-source27-unified-cold-01"
PREFIX = "ck3_autonomous_player/src/"
SOURCE_CARD = (5931, "acbc120ca34603f035a94a2881e0657bb23e68a1f0014c31a6ed3af8156ce4c8")
SOURCE26_ANCHOR = (7045, "d2bf903d4a0f18cc819721451d42e390a58529f76a19ad2df301e85df5b78e85")
SOURCE26_BASE = (389934, "30ba9778f6d4be917d29f1ab9a2a2b2aa414f5fedbfa03cdb7a8a9bebebd0517")
S = "ck3_autonomous_player/src/xar_autoplayer/"
U = "ck3_autonomous_player/tests/unit/"
W = "tools/g2_saved_campaign/"
NAMES = (
 S + "strategy.py", U + "test_wartime_moving_contact_preview_lease.py",
 S + "bridge/driver_state_wal_v1.py", U + "test_driver_state_wal_diagnostics.py",
 S + "cold_checkpoint_validator.py", S + "bridge/succession_transition_contract.py",
 U + "test_cold_checkpoint_type_contract.py", S + "native_session.py",
 "ck3_autonomous_player/pyproject.toml", W + "owner_prepare_contract_v1.py",
 W + "test_owner_prepare_contract_v1.py", W + "interactive_task_owner_v1.py",
 S + "bridge/native_driver.py", U + "test_driver_resume_type_contract.py",
 W + "test_interactive_task_owner_v1.py")
FUNCTIONS = {NAMES[0]: "_sole_committed_moving_contact_first",
             NAMES[12]: "load_native_driver_state_for_resume_payload"}

class Pin(TypedDict):
    bytes: int
    sha256: str

class FileRef(Pin):
    path: str

class Patch(TypedDict):
    relative: str
    source_commit: str | None
    input_pin: Pin
    before_pin: Pin | None
    output_pin: Pin

class Quote(TypedDict):
    retained_upper: int
    largest_temporary_upper: int
    peak_upper: int
    object_count: int

class Plan(TypedDict):
    schema: str
    machine_id: str
    observed_at_utc: str
    review_at_utc: str
    base: str
    ref: str
    target_tree: str
    patches: list[Patch]
    source_file_count: int
    source_bytes: int
    complete_rows_JSON: Pin
    source26_anchor: FileRef
    source26_BASE: FileRef
    qualifications: list[FileRef]
    Git_object_quote: Quote

class Row(TypedDict):
    relative: str
    bytes: int
    sha256: str
    git_blob_sha1: str
    git_mode: str

Entry = tuple[bytes, bytes, str]
Tree = tuple[str, bytes, str]

def require(ok: bool, why: str) -> None:
    if not ok:
        raise RuntimeError("Source27 writer: " + why)

def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        require(isinstance(key, str), "string key required")
        if isinstance(key, str):
            result[key] = item
    return result

def keys(value: object, names: str) -> dict[str, object]:
    result = obj(value)
    require(set(result) == set(names.split()), "fields differ: " + names)
    return result

def string(value: object) -> str:
    require(isinstance(value, str) and bool(value) and "\0" not in value, "nonempty string required")
    if not isinstance(value, str):
        raise ValueError("string required")
    return value

def integer(value: object) -> int:
    require(type(value) is int and value >= 0, "nonnegative int required")
    if type(value) is not int:
        raise ValueError("int required")
    return value

def sequence(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("list required")
    return [item for item in value]

def hexstr(value: object, count: int) -> str:
    result = string(value)
    require(re.fullmatch("[0-9a-f]{" + str(count) + "}", result) is not None, "hex required")
    return result

def pin(value: bytes) -> Pin:
    return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}

def parse_pin(value: object) -> Pin:
    d = keys(value, "bytes sha256")
    return {"bytes": integer(d["bytes"]), "sha256": hexstr(d["sha256"], 64)}

def parse_ref(value: object) -> FileRef:
    d = keys(value, "path bytes sha256")
    return {"path": string(d["path"]), "bytes": integer(d["bytes"]), "sha256": hexstr(d["sha256"], 64)}

def parse_plan(value: object) -> Plan:
    d = keys(value, "schema machine_id observed_at_utc review_at_utc base ref target_tree patches source_file_count source_bytes complete_rows_JSON source26_anchor source26_BASE qualifications Git_object_quote")
    patches: list[Patch] = []
    for value in sequence(d["patches"]):
        p = keys(value, "relative source_commit input_pin before_pin output_pin")
        patches.append({"relative": string(p["relative"]), "source_commit": None if p["source_commit"] is None else hexstr(p["source_commit"], 40),
                        "input_pin": parse_pin(p["input_pin"]), "before_pin": None if p["before_pin"] is None else parse_pin(p["before_pin"]), "output_pin": parse_pin(p["output_pin"])})
    q = keys(d["Git_object_quote"], "retained_upper largest_temporary_upper peak_upper object_count")
    quote: Quote = {"retained_upper": integer(q["retained_upper"]), "largest_temporary_upper": integer(q["largest_temporary_upper"]),
                    "peak_upper": integer(q["peak_upper"]), "object_count": integer(q["object_count"])}
    return {"schema": string(d["schema"]), "machine_id": string(d["machine_id"]), "observed_at_utc": string(d["observed_at_utc"]),
            "review_at_utc": string(d["review_at_utc"]), "base": hexstr(d["base"], 40), "ref": string(d["ref"]), "target_tree": hexstr(d["target_tree"], 40),
            "patches": patches, "source_file_count": integer(d["source_file_count"]), "source_bytes": integer(d["source_bytes"]),
            "complete_rows_JSON": parse_pin(d["complete_rows_JSON"]), "source26_anchor": parse_ref(d["source26_anchor"]), "source26_BASE": parse_ref(d["source26_BASE"]),
            "qualifications": [parse_ref(v) for v in sequence(d["qualifications"])], "Git_object_quote": quote}

def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def utc() -> datetime:
    return datetime.now(timezone.utc)

def date(value: object) -> datetime:
    result = datetime.fromisoformat(string(value).replace("Z", "+00:00"))
    require(result.tzinfo is not None, "aware date required")
    return result

def no_reparse(path: Path) -> None:
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            require(not part.is_symlink() and not part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, "reparse path: " + str(part))

def read(path: Path, cap: int) -> bytes:
    no_reparse(path)
    require(path.is_file() and path.stat().st_size <= cap, "file cap: " + str(path))
    body = path.read_bytes()
    require(len(body) <= cap, "read cap")
    return body

def checked(ref: FileRef, cap: int = 1048576) -> bytes:
    path = Path(ref["path"])
    require(path.is_absolute(), "absolute ref required")
    body = read(path, cap)
    require(pin(body) == {"bytes": ref["bytes"], "sha256": ref["sha256"]}, "ref differs: " + str(path))
    return body

def load(body: bytes) -> object:
    value: object = json.loads(body)
    return value

def file_ref(path: Path) -> FileRef:
    p = path.resolve()
    b = read(p, 4194304)
    return {"path": str(p), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}

def oid(kind: str, body: bytes) -> str:
    return hashlib.sha1(kind.encode() + b" " + str(len(body)).encode() + b"\0" + body).hexdigest()

def upper(kind: str, size: int) -> int:
    return ((size + len(kind) + len(str(size)) + 4098 + 4095) // 4096) * 4096

class Git:
    def __init__(self, repo: Path, metadata: Path) -> None:
        require(not any(k.startswith("GIT_") and k != "GIT_PAGER" for k in os.environ), "ambient Git environment")
        no_reparse(repo / ".git")
        self.env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1", GIT_PAGER="")
        hooks = metadata / "disabled-hooks-must-remain-absent"
        require(not hooks.exists(), "hooks path must remain absent")
        self.prefix = ["git", "-C", str(repo), "-c", "gc.auto=0", "-c", "maintenance.auto=false", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + str(hooks)]
    def run(self, *args: str, data: bytes | None = None, allowed: tuple[int, ...] = (0,)) -> tuple[int, bytes]:
        r = subprocess.run(self.prefix + list(args), input=data, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        require(r.returncode in allowed and len(r.stdout) <= 4194304 and len(r.stderr) <= 65536, "Git " + args[0] + ": " + r.stderr[:512].decode(errors="replace"))
        return r.returncode, r.stdout
    def get(self, *args: str, data: bytes | None = None) -> bytes:
        return self.run(*args, data=data)[1]

def entries(raw: bytes) -> dict[bytes, Entry]:
    result: dict[bytes, Entry] = {}
    for record in raw.split(b"\0"):
        if record:
            header, name = record.split(b"\t", 1)
            mode, kind, value = header.split()
            result[name] = (mode, kind, hexstr(value.decode(), 40))
    return result

def tree_body(e: dict[bytes, Entry]) -> bytes:
    return b"".join(m.lstrip(b"0") + b" " + n + b"\0" + bytes.fromhex(h)
                    for n, (m, k, h) in sorted(e.items(), key=lambda x: x[0] + (b"/" if x[1][1] == b"tree" else b"")))

def function(body: bytes, name: str) -> bytes:
    nodes = [n for n in ast.parse(body).body if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(nodes) == 1 and not nodes[0].decorator_list, "unique undecorated function required")
    lines = body.splitlines(keepends=True)
    result = b"".join(lines[nodes[0].lineno - 1:nodes[0].end_lineno])
    require(body.count(result) == 1, "function slice not unique")
    return result

def compose(plan: Plan, git: Git, repo: Path) -> tuple[dict[str, bytes], list[Row], list[Tree], Quote]:
    require(plan["schema"] == "xar.source27.canonical-plan/v1" and plan["machine_id"] == MACHINE and plan["base"] == BASE and plan["ref"] == REF, "plan identity")
    require(date(plan["observed_at_utc"]) <= utc() < date(plan["review_at_utc"]), "plan expired/future")
    require(len(plan["patches"]) == 15 and {p["relative"] for p in plan["patches"]} == set(NAMES), "canonical whitelist")
    require((plan["source26_anchor"]["bytes"], plan["source26_anchor"]["sha256"]) == SOURCE26_ANCHOR and (plan["source26_BASE"]["bytes"], plan["source26_BASE"]["sha256"]) == SOURCE26_BASE, "Source26 refs")
    anchor = obj(load(checked(plan["source26_anchor"])))
    require(anchor["commit"] == BASE and anchor["status"] == "CANONICAL_REF_CREATED_NOT_DEPLOYED", "actual Source26 anchor")
    base = obj(load(checked(plan["source26_BASE"])))
    rows: list[Row] = []
    for value in sequence(base["files"]):
        r = keys(value, "relative bytes sha256 git_blob_sha1 git_mode")
        rows.append({"relative": string(r["relative"]), "bytes": integer(r["bytes"]), "sha256": hexstr(r["sha256"], 64), "git_blob_sha1": hexstr(r["git_blob_sha1"], 40), "git_mode": string(r["git_mode"])})
    require(len(rows) == 1462 and len({r["relative"] for r in rows}) == 1462, "base rows")
    for ref in plan["qualifications"]:
        checked(ref)
    require(len(plan["qualifications"]) >= 2, "qualification refs required")
    actual: dict[str, tuple[str, str, int]] = {}
    for item in git.get("ls-tree", "-r", "-l", "-z", BASE, "--", PREFIX).split(b"\0"):
        if item:
            h, n = item.split(b"\t", 1)
            mode, kind, value, size = h.split()
            require(kind == b"blob", "SDK ordinary blob")
            actual[n.decode()[len(PREFIX):]] = (mode.decode(), value.decode(), int(size))
    require(actual == {r["relative"]: (r["git_mode"], r["git_blob_sha1"], r["bytes"]) for r in rows}, "Source26 complete Git inventory")
    out: dict[str, bytes] = {}
    for p in plan["patches"]:
        name = p["relative"]
        before = git.run("cat-file", "blob", BASE + ":" + name, allowed=(0, 128))
        require((pin(before[1]) if before[0] == 0 else None) == p["before_pin"], "preimage differs: " + name)
        source = p["source_commit"]
        body = git.get("cat-file", "blob", source + ":" + name) if source is not None else read(repo / name, 4194304)
        require(pin(body) == p["input_pin"], "input differs: " + name)
        if name in FUNCTIONS:
            old = before[1]
            a, b = function(old, FUNCTIONS[name]), function(body, FUNCTIONS[name])
            body = old.replace(a, b)
            require(body.replace(b, a) == old, "function inverse differs")
        require(pin(body) == p["output_pin"] and (before[0] != 0 or body != before[1]), "output differs/no change")
        if name.endswith(".py"):
            compile(body, name, "exec")
        out[name] = body
    changed = [name for name in out if name.startswith(PREFIX)]
    require(len(changed) == 6, "six SDK leaves required")
    for name in changed:
        target = next(r for r in rows if r["relative"] == name[len(PREFIX):])
        target.update({"bytes": len(out[name]), "sha256": pin(out[name])["sha256"], "git_blob_sha1": oid("blob", out[name]), "git_mode": "100644"})
    rows.sort(key=lambda r: r["relative"])
    require(plan["source_file_count"] == len(rows) == 1462 and plan["source_bytes"] == sum(r["bytes"] for r in rows) and pin(canonical(rows)) == plan["complete_rows_JSON"], "complete Source27 rows differ")
    dirs = {""}
    for name in out:
        d = name.rpartition("/")[0]
        while d:
            dirs.add(d)
            d = d.rpartition("/")[0]
    ids = {name: oid("blob", body) for name, body in out.items()}
    trees: list[Tree] = []
    amounts = [upper("blob", len(body)) for body in out.values()]
    for d in sorted(dirs, key=lambda s: (s.count("/") + bool(s), s), reverse=True):
        e = entries(git.get("ls-tree", "-z", BASE + (":" + d if d else "^{tree}")))
        for name in out:
            parent, _, leaf = name.rpartition("/")
            if parent == d:
                require(leaf.encode() not in e or e[leaf.encode()][1] == b"blob", "leaf replaces tree")
                e[leaf.encode()] = (b"100644", b"blob", ids[name])
        for child in dirs:
            if child and child.rpartition("/")[0] == d:
                e[child.rpartition("/")[2].encode()] = (b"040000", b"tree", ids[child])
        body = tree_body(e)
        ids[d] = oid("tree", body)
        trees.append((d, body, ids[d]))
        amounts.append(upper("tree", len(body)))
    require(ids[""] == plan["target_tree"], "target tree differs")
    amounts.append(upper("commit", 8192))
    q: Quote = {"retained_upper": sum(amounts), "largest_temporary_upper": max(amounts), "peak_upper": sum(amounts) + max(amounts) + 65536, "object_count": len(amounts)}
    require(q == plan["Git_object_quote"], "Git quote differs")
    return out, rows, trees, q

def main() -> None:
    ap = argparse.ArgumentParser(__doc__)
    for name in ("plan", "git-card"):
        ap.add_argument("--" + name, type=Path)
        ap.add_argument("--" + name + "-sha256")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not args.execute:
        print('{"status":"DISABLED","Git_mutations":0,"runtime_calls":0}')
        return
    require(isinstance(args.plan, Path) and isinstance(args.git_card, Path), "exact plan/card required")
    plan_path: Path = args.plan
    card_path: Path = args.git_card
    plan_raw, card_raw = read(plan_path, 1048576), read(card_path, 1048576)
    require(pin(plan_raw)["sha256"] == hexstr(args.plan_sha256, 64) and pin(card_raw)["sha256"] == hexstr(args.git_card_sha256, 64), "CLI pin")
    plan = parse_plan(load(plan_raw))
    card = obj(load(card_raw))
    require(card["schema"] == "xar.storage.Source27-root-canonical-Git.v1" and card["owner"] == "Root" and card["machine_id"] == MACHINE and card["status"] == "ADMITTED" and card["root_direct_execution_release"] is True, "Root Git release")
    require(0 <= (utc() - date(card["observed_at_utc"])).total_seconds() <= 600, "fresh Git card required")
    source_ref = parse_ref(card["source_admission"])
    require((source_ref["bytes"], source_ref["sha256"]) == SOURCE_CARD, "source admission pin")
    source = obj(load(checked(source_ref)))
    require(source["machine_id"] == MACHINE and source["status"] == "SOURCE_AND_METADATA_PREPARATION_ADMITTED", "source admission")
    limit = min(date(card["review_at_utc"]), date(source["source27_review_at_utc"]), date(plan["review_at_utc"]))
    require(utc() < limit, "admission expired")
    own = Path(__file__).resolve()
    repo = own.parents[2]
    src = obj(source["Source27"])
    metadata = Path(string(src["canonical_metadata_root"]))
    anchor = metadata / "SOURCE27-CANONICAL-ANCHOR.json"
    require(Path(string(src["writer_path"])).resolve() == own and integer(src["writer_logical_and_allocated_hard_bytes"]) == 16384, "original writer scope")
    amendment = obj(load(checked(parse_ref(card["writer_source_cap_amendment"]))))
    cap = obj(amendment["Source27"])
    realloc = obj(amendment["writer24_internal_reallocation"])
    require(amendment["machine_id"] == MACHINE and Path(string(cap["writer_path"])).resolve() == own and integer(cap["writer_logical_and_allocated_hard_bytes"]) == 24576 and parse_ref(realloc["previous"]) == source_ref and own.stat().st_size <= 24576, "writer cap amendment")
    require(parse_ref(card["writer"]) == file_ref(own) and parse_ref(card["plan"]) == file_ref(plan_path), "writer/plan refs")
    require(Path(string(card["metadata_root"])).resolve() == metadata.resolve() and Path(string(card["future_anchor"])).resolve() == anchor.resolve() and integer(card["anchor_hard_bytes"]) == 65536, "metadata scope")
    no_reparse(metadata)
    require(not anchor.exists() and not anchor.is_symlink(), "anchor consumed")
    machine = subprocess.check_output([sys.executable, "-B", str(repo / "tools/ck3_live_run_id.py"), "machine"]).decode().strip()
    require(machine == MACHINE, "actual machine")
    capacity, budget = obj(card["capacity"]), obj(card["Git"])
    zfloor, dfloor = integer(capacity["Z_free_floor_bytes"]), integer(capacity["D_free_floor_bytes"])
    def guard() -> None:
        require(utc() < limit and shutil.disk_usage(repo).free >= zfloor and shutil.disk_usage(metadata.parent).free >= dfloor, "fresh free floor/admission lost")
    guard()
    git = Git(repo, metadata)
    common_raw = Path(os.fsdecode(git.get("rev-parse", "--git-common-dir").strip()))
    common = (common_raw if common_raw.is_absolute() else repo / common_raw).resolve()
    no_reparse(common / "objects")
    require(not (common / "objects/info/alternates").exists(), "Git alternates forbidden")
    require(common == (repo / ".git").resolve() == Path(string(budget["root"])).resolve() and git.get("rev-parse", "--show-object-format").strip() == b"sha1", "Git root/format")
    require(git.get("rev-parse", BASE + "^{commit}").strip().decode() == BASE, "actual parent")
    require(git.run("show-ref", "--verify", "--quiet", REF, allowed=(0, 1))[0] == 1 and git.run("symbolic-ref", "--quiet", REF, allowed=(0, 1))[0] == 1, "ref consumed")
    out, rows, trees, quote = compose(plan, git, repo)
    hard = integer(budget["hard_bytes"])
    require(integer(budget["peak_upper_bytes"]) == quote["peak_upper"] <= hard and budget["prior_holds_retained"] is True, "Git budget")
    require(len(git.get("var", "GIT_AUTHOR_IDENT")) + len(git.get("var", "GIT_COMMITTER_IDENT")) < 4096, "commit identities cap")
    metadata.mkdir(exist_ok=True)
    record: dict[str, object] = {"schema": "xar.source27.canonical-git-anchor/v1", "machine_id": MACHINE, "status": "RUNNING_OR_UNKNOWN",
        "start_utc": utc().isoformat(), "execution_owner": "Root", "root_direct_execution_release": True, "parent": BASE, "ref": REF,
        "writer": file_ref(own), "source_plan": file_ref(plan_path), "capacity_card": file_ref(card_path), "source_admission": source_ref,
        "actual_Source26_anchor": plan["source26_anchor"], "Git_object_quote": quote, "runtime_calls": 0, "SDK_export_calls": 0,
        "push_calls": 0, "index_or_tracked_worktree_mutations": 0, "actual_loaded_provider": False, "canonical_patch_rows": plan["patches"]}
    charged = 0
    commit = ""
    with anchor.open("xb") as receipt:
        def save() -> None:
            body = canonical(record) + b"\n"
            require(len(body) <= 65536, "anchor cap")
            receipt.seek(0)
            receipt.truncate()
            receipt.write(body)
            receipt.flush()
            os.fsync(receipt.fileno())
        def write(kind: str, size: int, *argv: str, data: bytes | None = None) -> bytes:
            nonlocal charged
            charge = upper(kind, size)
            require(charged + charge <= quote["retained_upper"] and charged + charge + quote["largest_temporary_upper"] + 65536 <= hard, "cumulative Git bound")
            guard()
            charged += charge
            return git.get(*argv, data=data)
        save()
        try:
            for name, body in sorted(out.items()):
                require(write("blob", len(body), "hash-object", "-w", "--stdin", data=body).strip().decode() == oid("blob", body), "blob write differs")
            for _, body, expected in trees:
                e = entries_tree(body)
                data = b"".join(m + b" " + k + b" " + h.encode() + b"\t" + n + b"\0" for n, (m, k, h) in sorted(e.items()))
                require(write("tree", len(body), "mktree", "-z", data=data).strip().decode() == expected, "tree write differs")
            tree = plan["target_tree"]
            diff = {v.decode() for v in git.get("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", BASE, tree).split(b"\0") if v}
            require(diff == set(NAMES), "unowned path")
            for name, body in out.items():
                require(git.get("cat-file", "blob", tree + ":" + name) == body, "readback differs")
            commit = write("commit", 8192, "commit-tree", tree, "-p", BASE, data=b"Source27: finite route/WAL and strict resume/owner contracts\n").strip().decode()
            body = git.get("cat-file", "commit", commit)
            heads = body.split(b"\n\n", 1)[0].splitlines()
            require(len(body) <= 8192 and [v for v in heads if v.startswith(b"parent ")] == [b"parent " + BASE.encode()] and [v for v in heads if v.startswith(b"tree ")] == [b"tree " + tree.encode()], "commit ancestry")
            record.update(commit=commit, tree=tree, output_pins=[r for r in rows if PREFIX + r["relative"] in out],
                source_file_count=len(rows), source_bytes=sum(r["bytes"] for r in rows), complete_rows_JSON=pin(canonical(rows)), charged_retained_objects_upper=charged)
            save()
            require(charged == quote["retained_upper"], "retained accounting")
            checked(plan["source26_anchor"])
            guard()
            git.get("update-ref", "--no-deref", REF, commit, "0" * 40)
            require(git.get("rev-parse", REF).strip().decode() == commit, "ref readback")
            record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED", end_utc=utc().isoformat(), future_writes=0)
        except BaseException as error:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY", end_utc=utc().isoformat(), error={"type": type(error).__name__, "text": str(error)[:1024]})
            save()
            raise
        save()
    print(json.dumps({"status": record["status"], "commit": commit, "tree": plan["target_tree"], "anchor": file_ref(anchor), "runtime_calls": 0}))

def entries_tree(body: bytes) -> dict[bytes, Entry]:
    result: dict[bytes, Entry] = {}
    pos = 0
    while pos < len(body):
        space, zero = body.index(b" ", pos), body.index(b"\0", pos)
        mode, name = body[pos:space], body[space + 1:zero]
        value = body[zero + 1:zero + 21].hex()
        result[name] = (b"040000" if mode == b"40000" else mode, b"tree" if mode == b"40000" else b"blob", value)
        pos = zero + 21
    return result

if __name__ == "__main__":
    main()
