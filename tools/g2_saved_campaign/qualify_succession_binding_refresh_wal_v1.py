"""Disjoint portable and exact-Source20 focused groups; no SDK materialization."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import prepare_succession_binding_refresh_wal_v1 as producer

REPO = producer.REPO
PREFIX = 'ck3_autonomous_player/src/'
HELPER = 'xar_autoplayer/bridge/succession_binding_refresh_wal_v1.py'
TEST = 'ck3_autonomous_player/tests/unit/test_succession_binding_refresh_wal_v1.py'
SCRATCH = REPO/'.task-tmp/succession-binding-wal-20261020-qualification01'
PROOF = REPO/'docs/ck3-native-ai/evidence/succession-binding-refresh-wal-source-ready-2026-10-20.json'
PATCH = REPO/'docs/ck3-native-ai/evidence/succession-binding-refresh-wal-v1.patch'
CARD = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/PERFORMANCE-SUCCESSION-BINDING-WAL-THIN192KiB-SOURCE-SCRATCH-COMMITMENT01.json')
CARD_SHA = '51661f419dda8df8c839e2a17601becd4017ca4404e1a45285848e8ac7a19c81'
OWN = (PREFIX+HELPER, 'tools/g2_saved_campaign/prepare_succession_binding_refresh_wal_v1.py', TEST,
       'tools/g2_saved_campaign/qualify_succession_binding_refresh_wal_v1.py')


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class Source20RAM(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Every production Python import comes from the one immutable Git tree."""
    def __init__(self, candidate):
        self.candidate = candidate
        self.loaded = []
        self.entries = {}
        raw = subprocess.check_output(['git', '-C', str(REPO), 'ls-tree', '-r', '-z', producer.BASE, '--', PREFIX])
        for row in raw.split(b'\0'):
            if row:
                header, name = row.split(b'\t', 1)
                mode, kind, oid = header.decode().split()
                self.entries[name.decode()[len(PREFIX):]] = (mode, kind, oid)

    def find_spec(self, fullname, path=None, target=None):
        if fullname != 'xar_autoplayer' and not fullname.startswith('xar_autoplayer.'):
            return None
        stem = fullname.replace('.', '/')
        package = stem+'/__init__.py' in self.entries
        relative = stem+'/__init__.py' if package else stem+'.py'
        if relative not in self.entries and relative != HELPER:
            raise ModuleNotFoundError('module absent from fixed Source20: '+fullname)
        return importlib.util.spec_from_loader(fullname, self, is_package=package)

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        stem = module.__name__.replace('.', '/')
        relative = stem+'/__init__.py' if stem+'/__init__.py' in self.entries else stem+'.py'
        if relative == HELPER:
            raw = (REPO/PREFIX/relative).read_bytes()
        elif relative == 'xar_autoplayer/bridge/native_driver.py':
            raw = self.candidate
        else:
            raw = subprocess.check_output(['git', '-C', str(REPO), 'show', producer.BASE+':'+PREFIX+relative])
            oid = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            producer.require(self.entries[relative][1:] == ('blob', oid), 'Source20 dependency differs')
        # A virtual inspect path, never a claim that a physical SDK was written.
        module.__file__ = str(REPO/PREFIX/relative)
        if module.__spec__.submodule_search_locations is not None:
            module.__path__ = [str((REPO/PREFIX/relative).parent)]
        exec(compile(raw, '<Source20-RAM/'+relative+'>', 'exec', dont_inherit=True), module.__dict__)
        self.loaded.append(dict(relative=relative, **pin(raw)))


def group(name):
    producer.require(sys.dont_write_bytecode, 'run -B')
    producer.require(SCRATCH.is_dir() and not SCRATCH.is_symlink(), 'admitted scratch not initialized')
    producer.require(not any(n == 'xar_autoplayer' or n.startswith('xar_autoplayer.') for n in sys.modules), 'fresh process required')
    loader = None
    inverse = None
    if name == 'source20':
        base = producer.load_base(); candidate = producer.transform(base)
        producer.require(producer.transform(candidate, reverse=True) == base, 'whole Driver inverse differs')
        before, after = producer.methods(base), producer.methods(candidate)
        changed = {n for n in before if ast.dump(before[n], include_attributes=False) != ast.dump(after[n], include_attributes=False)}
        producer.require(changed == {'__init__', 'retain_succession_expectation_v1',
                         '_try_persist_driver_state_wal_append_v1', '_persist_driver_state'}, 'unrelated Driver method changed')
        delta = producer.patch_bytes(base, candidate)
        producer.require(len(delta) <= 8192, 'thin patch exceeds8KiB')
        inverse = dict(base=pin(base), candidate=pin(candidate), patch=pin(delta),
                       entire_inverse=True, changed_methods=sorted(changed), full_Driver_output=False)
        loader = Source20RAM(candidate); sys.meta_path.insert(0, loader)
    else:
        sys.path.insert(0, str(REPO/'ck3_autonomous_player/src'))
    sys.path.insert(0, str(REPO/'ck3_autonomous_player/tests/unit'))
    tempfile.tempdir = str(SCRATCH)
    import test_succession_binding_refresh_wal_v1 as tests
    tests.configure_scratch(SCRATCH)
    cls = tests.PortableProofAndReplay if name == 'portable' else tests.Source20DriverIntegration
    sink = io.StringIO()
    result = unittest.TextTestRunner(stream=sink, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    remaining = sum(p.stat().st_size for p in SCRATCH.rglob('*') if p.is_file())
    producer.require(remaining == 0, 'owned per-test scratch not clean')
    producer.require(tests.PEAK_BOUND <= 65536, 'scratch exceeded64KiB')
    return dict(group=name, tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                success=result.wasSuccessful(), transcript=sink.getvalue()[:18000], inverse=inverse,
                loaded_count=len(loader.loaded) if loader else None,
                loaded_rows_sha256=hashlib.sha256(json.dumps(loader.loaded, sort_keys=True).encode()).hexdigest() if loader else None,
                critical_imports=[r for r in loader.loaded if r['relative'] in {
                    HELPER, 'xar_autoplayer/bridge/native_driver.py', 'xar_autoplayer/bridge/driver_state_wal_v1.py',
                    'xar_autoplayer/bridge/succession_transition_contract.py'}] if loader else [],
                scratch_conservative_prewrite_peak_bound=tests.PEAK_BOUND,
                synthetic_atomic_writes=tests.WRITE_COUNT, scratch_after=remaining,
                Game_RPC_or_Native_commands=0, current_runtime_outputs=0)


def cleanup_owned(root):
    expected = SCRATCH.parent.resolve()/SCRATCH.name
    producer.require(root.resolve() == expected and root.parent.resolve() == SCRATCH.parent.resolve(), 'cleanup bounds differ')
    items = list(root.rglob('*'))
    for p in [root, *items]:
        stat = p.lstat()
        producer.require(not p.is_symlink() and not (getattr(stat, 'st_file_attributes', 0) & 0x400), 'unexpected reparse node')
    for p in sorted(items, key=lambda x: len(x.parts), reverse=True):
        p.rmdir() if p.is_dir() else p.unlink()
    root.rmdir()


def all_groups():
    raw = CARD.read_bytes()
    producer.require(pin(raw)['sha256'] == CARD_SHA, 'storage card differs')
    card = json.loads(raw)
    now = datetime.now(timezone.utc)
    producer.require(card['status'] == 'ADMITTED_SOURCE_ONLY' and card['machine_id'] == 'xenoamess-full-tower-eb9d2c1186'
                     and now < datetime.fromisoformat(card['review_at_utc']), 'source card unavailable or expired')
    producer.require(not SCRATCH.exists() and not PROOF.exists() and not PATCH.exists(), 'create-only output exists')
    producer.require(SCRATCH.parent.resolve().is_relative_to(REPO.resolve()), 'scratch escaped workspace')
    current = sum((REPO/p).stat().st_size for p in OWN)
    producer.require(current+65536+8192+16384 <= 196608, 'source aggregate cannot fit')
    SCRATCH.mkdir()
    groups = []
    try:
        for name in ('portable', 'source20'):
            result = subprocess.run([sys.executable, '-B', __file__, '--group', name], cwd=REPO,
                                    capture_output=True, text=True, encoding='utf-8')
            producer.require(result.returncode == 0, 'group process failed: '+result.stderr[-4000:])
            groups.append(json.loads(result.stdout))
    finally:
        cleanup_owned(SCRATCH)
    base = producer.load_base(); candidate = producer.transform(base); patch = producer.patch_bytes(base, candidate)
    success = all(g['success'] for g in groups)
    report = dict(schema='xar.succession-binding-refresh-wal-source-qualification/v1',
        machine_id=card['machine_id'], observed_at_utc=datetime.now(timezone.utc).isoformat(),
        machine_source='tools/ck3_live_run_id.py machine actual readback891a22, 2026-10-19T21:32:16Z',
        status='SOURCE_QUALIFIED_NOT_DEPLOYED' if success else 'FOCUSED_FAILED_NOT_QUALIFIED',
        base_commit=producer.BASE, base_source=pin(base), candidate_RAM_only=pin(candidate),
        thin_patch=pin(patch), source_card=dict(path=str(CARD), **pin(raw)), groups=groups,
        existing_16_or_144_matrix_repeated=False, benchmark=False, actual_runtime_benefit_seconds=None,
        actual_C20_WAL_writer_enabled='NOT_CLAIMED; App environment missing WAL variable is under separate readonly audit',
        current_SDK_Task_Game_Driver_state_SAVE_outputs=0,
        format_reader_once_and_Service_modified=False,
        outputs=[dict(path=p, **pin((REPO/p).read_bytes())) for p in OWN],
        scratch=dict(root=str(SCRATCH), hard_bytes=65536, removed=not SCRATCH.exists(),
                     allocated_bytes=None, observed_physical_peak=None, future_writes=0),
        old_and_new_functional_scope='portable helper+unchanged real WAL replay; separate complete f198 RAM imports and candidate actual methods; synthetic filesystem only',
        record_review_at_utc=card['review_at_utc'], future_writes_after_freeze=0)
    encoded = (json.dumps(report, ensure_ascii=False, indent=2)+'\n').encode()
    producer.require(len(encoded) <= 16384 and len(patch) <= 8192, 'proof/patch cap exceeded')
    producer.require(current+len(encoded)+len(patch)+65536 <= 196608, 'complete peak exceeds192KiB')
    # The initial failed attempt remains a small explicit receipt, never hidden.
    with PATCH.open('xb') as out:
        out.write(patch)
    with PROOF.open('xb') as out:
        out.write(encoded)
    return dict(status=report['status'], groups=[{k:g[k] for k in ('group','tests','failures','errors','success')} for g in groups],
                proof=dict(path=str(PROOF), **pin(encoded)), patch=dict(path=str(PATCH), **pin(patch)),
                retained_bytes=current+len(encoded)+len(patch), scratch_removed=not SCRATCH.exists())


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--group', choices=('portable', 'source20'))
    opts = args.parse_args()
    print(json.dumps(group(opts.group) if opts.group else all_groups(), ensure_ascii=False, indent=2))
