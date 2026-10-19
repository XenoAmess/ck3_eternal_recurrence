"""Root reviews composer and writer before --execute-root-writer.
Capacity alone is not Git release. No index/push/export/build/runtime; no replay.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
BASE = "f19864de1cc073eed62617faad2307c57ad45a97"
REF = "refs/heads/campaign/robert-v20261019-c22-wal-clock-diag-warm-01"
PREFIX = "ck3_autonomous_player/src/"
COMPOSER = REPO / "tools/g2_saved_campaign/prepare_source22_wal_clock_diagnostic_v1.py"
COMPOSER_SHA = "27141b999abd41e752323cc74831e9ea1c33389366da8630c2002ac2c8e4b24a"
PLAN = REPO / "docs/ck3-native-ai/evidence/source22-wal-clock-diagnostic-source-plan-2026-10-20.json"
PLAN_SHA = "48ecb6b2e5c8162d965efd30ed925838b92b2fb519870ceba6131d265905ac89"
CARD_SHA = "e8726e7cdd6fa93d80c7d283afca9c3bd1115dd3be30270c51c39535bb807e25"
MACHINE = "xenoamess-full-tower-eb9d2c1186"
ROWS_SHA = "7290b3370b64335b27ff375713dd92de331b0ca114bf99440014d40404593a85"


def require(ok, why):
  if not ok:
    raise RuntimeError("Source22 writer: " + why)


def pin(raw):
  return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def file_pin(path):
  return {"path": str(path.resolve()), **pin(path.read_bytes())}


def utc():
  return datetime.now(timezone.utc).isoformat()


def checked(path, sha):
  raw = path.read_bytes()
  require(pin(raw)["sha256"] == sha, "input changed: " + str(path))
  return raw


def main():
  parser = argparse.ArgumentParser(__doc__)
  parser.add_argument("--card", type=Path, required=True)
  parser.add_argument("--execute-root-writer", action="store_true")
  args = parser.parse_args()
  if not args.execute_root_writer:
    print('{"status":"DISABLED","Git_mutations":0,"runtime_calls":0}')
    return
  start = utc()
  card_raw = checked(args.card, CARD_SHA)
  c = json.loads(card_raw)
  require(c["machine_id"] == MACHINE, "card machine differs")
  require(datetime.now(timezone.utc) < datetime.fromisoformat(c["review_at_utc"].replace("Z", "+00:00")),
      "expired capacity")
  require(c["components"]["Source22_canonical_Git"] == c["Git"]["hard_bytes"] == 3932160
      and c["components"]["Root_writer_proof_metadata"] == 524288, "component caps differ")
  s = c["Root_writer_source"]
  own = file_pin(Path(__file__))
  require(Path(s["helper"]).resolve() == Path(__file__).resolve() and own["bytes"] <= 12288,
      "helper path/size differs")
  root, anchor = Path(s["integration_root"]), Path(s["future_anchor"])
  require(root.resolve() == (REPO / "_runtime/source22-integration16").resolve()
      and anchor.parent.resolve() == root.resolve() and anchor.name == "SOURCE22-CANONICAL-ANCHOR.json"
      and not root.is_symlink() and not anchor.exists(), "exact absent anchor required")
  machine = subprocess.check_output([sys.executable, "-B", str(REPO / "tools/ck3_live_run_id.py"), "machine"],
                   cwd=REPO).decode().strip()
  require(machine == MACHINE, "execution machine differs")
  require(shutil.disk_usage(REPO).free >= c["capacity"]["Z_conservative_floor_bytes"] + 4456448,
      "fresh free floor plus Git/writer envelopes unavailable")
  for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE"):
    require(not os.environ.get(key), "ambient Git redirection: " + key)
  env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
  hooks = root / "disabled-hooks-must-remain-absent"
  require(not hooks.exists(), "unexpected hooks path")
  prefix = ["git", "-C", str(REPO), "-c", "gc.auto=0", "-c", "maintenance.auto=false",
       "-c", "commit.gpgsign=false", "-c", "i18n.commitEncoding=utf-8", "-c", "core.hooksPath=" + str(hooks)]

  def command(*parts, data=None, allowed=(0,)):
    out = subprocess.run(prefix + list(parts), input=data, stdout=subprocess.PIPE,
              stderr=subprocess.PIPE, env=env, check=False)
    require(out.returncode in allowed, "Git " + parts[0] + " failed: " + out.stderr[:1024].decode(errors="replace"))
    require(len(out.stdout) <= 2*1024**2 and len(out.stderr) <= 65536, "Git metadata cap")
    return out.returncode, out.stdout

  def g(*parts, data=None):
    return command(*parts, data=data)[1]

  def oid(raw):
    value = raw.decode("ascii").strip()
    require(re.fullmatch("[0-9a-f]{40}", value), "one Git SHA1 required")
    return value

  require(g("rev-parse", "--show-object-format").strip() == b"sha1", "Git format differs")
  common = Path(os.fsdecode(g("rev-parse", "--git-common-dir").strip()))
  common = common.resolve() if common.is_absolute() else (REPO/common).resolve()
  require(common == Path(c["Git"]["root"]).resolve(), "canonical Git directory differs")
  require(command("show-ref", "--verify", "--quiet", REF, allowed=(0, 1))[0] == 1, "ref already exists")
  require(command("symbolic-ref", "--quiet", REF, allowed=(0, 1))[0] == 1, "symbolic ref exists")
  plan = json.loads(checked(PLAN, PLAN_SHA))
  checked(COMPOSER, COMPOSER_SHA)
  spec = importlib.util.spec_from_file_location("source22_frozen_composer", COMPOSER)
  p = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(p)
  outputs, rows, report = p.compose()
  expected = p.index_rows(rows)
  inventory = p.rows_bytes(expected)
  require(len(rows) == 1449 and sum(r["bytes"] for r in rows) == 59095358
      and pin(inventory) == {"bytes": 372481, "sha256": ROWS_SHA}, "full1449 inventory differs")
  planned = {r["relative"]: r for r in plan["participating_complete_output_pins"]}
  require(len(outputs) == len(planned) == 9 and set(outputs) == set(planned), "exact nine outputs required")
  for name, raw in outputs.items():
    row, frozen = expected[name], planned[name]
    require(type(raw) is bytes and pin(raw) == {"bytes": frozen["bytes"], "sha256": frozen["sha256"]}
        and row["git_blob_sha1"] == frozen["git_blob_sha1"] == p.blob_sha(raw), "output differs: " + name)
  quote = report["future_separate_phase_quotes"]
  require(quote["Git_peak_upper"] <= 3932160 and quote["compression_or_existing_object_dedup_credit"] == 0,
      "uncompressed Git quote exceeds envelope")
  tree_quote = {r["path"]: r["payload_bytes"] for r in quote["Git_object_metadata"] if r["kind"] == "tree"}
  require(len(g("var", "GIT_AUTHOR_IDENT")) + len(g("var", "GIT_COMMITTER_IDENT")) < 4096, "commit identity cap")
  root.mkdir(exist_ok=True)
  require(root.is_dir() and not root.is_symlink(), "integration root differs")
  record = {"schema": "xar.source22.canonical-git-anchor/v1", "machine_id": machine,
       "start_utc": start, "status": "RUNNING_OR_UNKNOWN", "execution_owner": "Root",
       "root_direct_execution_release": True, "capacity_card": {"path": str(args.card.resolve()), **pin(card_raw)},
       "writer": own, "composer": file_pin(COMPOSER), "source_plan": file_pin(PLAN),
       "ref": REF, "parent": BASE, "runtime_calls": 0, "SDK_export_calls": 0,
       "Native_Game_Task_calls": 0, "push_calls": 0, "index_or_tracked_worktree_mutations": 0}
  with anchor.open("xb") as receipt:
    def save():
      raw = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode()
      require(len(raw) <= 12288, "anchor cap")
      receipt.seek(0); receipt.truncate(); receipt.write(raw)
      receipt.flush(); os.fsync(receipt.fileno())
    save()
    try:
      changes = {}
      for name, raw in sorted(outputs.items()):
        blob = oid(g("hash-object", "-w", "--stdin", data=raw))
        require(blob == expected[name]["git_blob_sha1"], "written blob differs")
        changes[(PREFIX+name).encode()] = (expected[name]["git_mode"].encode(), b"blob", blob.encode())
      trees = []

      def rewrite(tree, pending, directory=b""):
        entries = {}
        for row in g("ls-tree", "-z", tree).split(b"\0"):
          if row:
            header, name = row.split(b"\t", 1)
            require(name not in entries, "duplicate tree name")
            entries[name] = tuple(header.split())
        groups = {}
        for name, value in pending.items():
          head, sep, tail = name.partition(b"/")
          if sep:
            groups.setdefault(head, {})[tail] = value
          else:
            require(entries.get(head, (None, b"blob"))[1] == b"blob", "leaf replaces tree")
            entries[head] = value
        for name, children in groups.items():
          require(name in entries and entries[name][1] == b"tree", "missing parent tree")
          subdir = directory + (b"/" if directory else b"") + name
          entries[name] = (b"040000", b"tree", rewrite(entries[name][2].decode(), children, subdir).encode())
        size = sum(len(mode.lstrip(b"0"))+1+len(name)+1+20 for name,(mode,kind,child) in entries.items())
        key = directory.decode() if directory else "<root>"
        require(tree_quote.get(key) == size, "tree exceeds exact native quote: " + key)
        raw = b"".join(mode+b" "+kind+b" "+child+b"\t"+name+b"\0"
               for name,(mode,kind,child) in sorted(entries.items()))
        result = oid(g("mktree", "-z", data=raw)); trees.append(key)
        return result

      tree = rewrite(oid(g("rev-parse", BASE+"^{tree}")), changes)
      require(set(trees) == set(tree_quote), "tree closure differs")

      def verify_tree(value):
        actual = {}
        for row in g("ls-tree", "-r", "-l", "-z", value, "--", PREFIX).split(b"\0"):
          if row:
            header, name = row.split(b"\t", 1)
            mode, kind, blob, size = header.split()
            require(kind == b"blob" and name.decode().startswith(PREFIX), "SDK file differs")
            actual[name.decode()[len(PREFIX):]] = (mode.decode(), blob.decode(), int(size))
        wanted = {n:(r["git_mode"],r["git_blob_sha1"],r["bytes"]) for n,r in expected.items()}
        require(actual == wanted, "all1449 mode/blob/size readback differs")

      verify_tree(tree)
      diff = set(v for v in g("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", BASE, tree).split(b"\0") if v)
      require(diff == set(changes), "tree changes more than nine paths")
      for name in outputs:
        require(pin(g("cat-file", "blob", tree+":"+PREFIX+name)) == pin(outputs[name]), "nine-body SHA256 differs")
      env.update(GIT_AUTHOR_DATE=utc(), GIT_COMMITTER_DATE=utc())
      commit = oid(g("commit-tree", tree, "-p", BASE, data=b"Source22: frozen WAL binding refresh and clock diagnostics\n"))
      body = g("cat-file", "commit", commit)
      headers = body.split(b"\n\n",1)[0].splitlines()
      require(len(body) <= 8192 and [v for v in headers if v.startswith(b"tree ")] == [b"tree "+tree.encode()]
          and [v for v in headers if v.startswith(b"parent ")] == [b"parent "+BASE.encode()], "actual commit differs")
      record.update(commit=commit, tree=tree, nine_output_pins=[expected[n] for n in sorted(outputs)])
      g("update-ref", "--no-deref", REF, commit, "0"*40)
      require(oid(g("rev-parse", "--verify", REF)) == commit, "published ref differs")
      verify_tree(commit)
      record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED", end_utc=utc(), future_writes=0,
             source_file_count=1449, source_bytes=59095358, complete_rows_JSON=pin(inventory),
             nine_SHA256_body_readbacks=True, all1449_SHA256_bodies_reread=False,
             all1449_Git_mode_blob_size_verified=True,
             Git_peak_quote=quote["Git_peak_upper"], Git_hard_bytes=3932160,
             compression_or_existing_object_dedup_credit=0, Source21_anchor_created=False,
             clock_root_cause="UNKNOWN; diagnostic only", Native30_bound=False,
             record_review_at_utc=(datetime.now(timezone.utc)+timedelta(days=180)).isoformat())
    except BaseException as error:
      record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY", end_utc=utc(), future_writes=None,
             error={"type":type(error).__name__,"text":str(error)[:1024]})
      save()
      raise
    save()
  print(json.dumps({"status":record["status"],"ref":REF,"commit":record["commit"],"tree":record["tree"],
           "anchor":file_pin(anchor),"runtime_calls":0}))


if __name__ == "__main__":
  main()

