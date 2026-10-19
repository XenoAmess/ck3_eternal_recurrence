"""Exact canonical two-gate patch. Full capture output stays in RAM."""
import ast
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO/'tools/ck3_obs_capture.py'
BASE_BYTES = 69656
BASE_SHA = 'f0e66034173353c37ba3626e423a2e8139f815e3f8dfa938c4219bc41a16b4e2'
CANDIDATE_BYTES = 71770
CANDIDATE_SHA = '9af7bf7e2faa757ff07f759990cb10a1425852bde001554e924b228598515a0c'
HELPER = REPO/'tools/ck3_obs_pause_growth_v1.py'
HELPER_BYTES = 1566
HELPER_SHA = 'b3a645480af6840c3a784336ab03538d918efec6df0faf6134c09fe9440a030c'

PATCHES = (
('        previous, changed = 0, time.monotonic()\n',
 '        previous, changed = 0, time.monotonic()\n        was_paused, peer = False, None\n'),
('                    video, total = _job_bytes(job)\n',
 '''                    if peer is None:
                        peer = OwnedEngine(self.engine.profile, job)
                        peer.process, peer.generation = self.engine.process, self.engine.generation
                        peer.connect()
                    _output_binding(peer)
                    growth_status = peer.client.get_record_status()
                    peer.check()
                    video, total = _job_bytes(job)
'''),
('''                    if video > previous:
                        previous, changed = video, time.monotonic()
                    elif time.monotonic() - changed > 30:
                        raise RuntimeError("actual video file did not grow for over 30 seconds")
''',
 '''                    previous, changed, was_paused = advance_growth_deadline_v1(
                        previous, changed, was_paused, current=video, now=time.monotonic(),
                        output_active=growth_status.output_active,
                        output_paused=getattr(growth_status, "output_paused", None),
                        error_message="actual video file did not grow for over 30 seconds")
'''),
('''            peer = OwnedEngine(self.engine.profile, job)
            peer.process, peer.generation = self.engine.process, self.engine.generation
            try:
                peer.connect()
''',
 '''            if peer is None:
                peer = OwnedEngine(self.engine.profile, job)
                peer.process, peer.generation = self.engine.process, self.engine.generation
            try:
                if peer.client is None:
                    peer.connect()
'''),
('            last_bytes, last_growth, peak = 0, time.monotonic(), 0\n',
 '            last_bytes, last_growth, peak = 0, time.monotonic(), 0\n            was_paused = False\n'),
('                status = client.get_record_status()\n',
 '                status = client.get_record_status()\n                engine.check()\n'),
('''                if current_bytes > last_bytes:
                    last_bytes, last_growth = current_bytes, time.monotonic()
                elif time.monotonic() - last_growth > 30:
                    raise RuntimeError("actual recording file did not grow for over 30 seconds")
''',
 '''                last_bytes, last_growth, was_paused = advance_growth_deadline_v1(
                    last_bytes, last_growth, was_paused, current=current_bytes, now=time.monotonic(),
                    output_active=status.output_active,
                    output_paused=getattr(status, "output_paused", None),
                    error_message="actual recording file did not grow for over 30 seconds")
'''))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError('pause-aware capture patch denied: '+reason)


def transform_pause_aware_capture_v1(original):
    require(type(original) is bytes and len(original) == BASE_BYTES and sha(original) == BASE_SHA,
        'only the frozen canonical baseline is supported; not a live C16 patch')
    helper_raw = HELPER.read_bytes()
    require(len(helper_raw) == HELPER_BYTES and sha(helper_raw) == HELPER_SHA,
        'frozen pure helper source changed')
    helper = helper_raw.decode('utf-8')
    functions = [n for n in ast.parse(helper).body if isinstance(n,ast.FunctionDef)
        and n.name == 'advance_growth_deadline_v1']
    require(len(functions) == 1, 'one pure helper source function required')
    inline = ast.get_source_segment(helper,functions[0])
    patches = (('class FileGrowthWatch:',inline+'\n\n\nclass FileGrowthWatch:'),*PATCHES)
    candidate = original.decode('utf-8')
    for old,new in patches:
        require(candidate.count(old) == 1, 'one exact capture seam required')
        candidate = candidate.replace(old,new,1)
    restored = candidate
    for old,new in reversed(patches):
        require(restored.count(new) == 1, 'inverse seam differs')
        restored = restored.replace(new,old,1)
    require(restored.encode() == original, 'original bytes changed outside the exact hunks')
    compile(candidate,'future-pause-aware-canonical-capture','exec')
    tree = ast.parse(candidate)
    calls = [n for n in ast.walk(tree) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Name) and n.func.id == 'advance_growth_deadline_v1']
    require(len(calls) == 2, 'both original independent growth gates must be connected')
    return candidate.encode('utf-8')


def compose():
    original = BASE.read_bytes()
    helper = HELPER.read_bytes()
    require(len(helper) == HELPER_BYTES and sha(helper) == HELPER_SHA,
        'frozen pure helper source changed')
    if len(original) == CANDIDATE_BYTES and sha(original) == CANDIDATE_SHA:
        candidate = original
        compile(candidate,'exact-adopted-pause-aware-capture','exec')
        input_kind = 'exact_candidate_readback'
    else:
        candidate = transform_pause_aware_capture_v1(original)
        input_kind = 'exact_baseline_transformed'
    return {'canonical_capture_candidate':candidate, 'helper':helper,
        'base':{'path':str(BASE),'bytes':BASE_BYTES,'sha256':BASE_SHA},
        'actual_input':{'path':str(BASE),'bytes':len(original),'sha256':sha(original)},
        'input_kind':input_kind,
        'outputs_materialized':False, 'runtime_admitted':False,
        'deployment':'standalone capture includes exact pure helper function; no companion runtime import'}
