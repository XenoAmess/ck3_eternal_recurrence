"""Unapplied future outer/feeder timing hunks; build only in memory.

The legacy canonical template says C17; actual C18 is alliance warm and future
canonical cold is C19. This tool supplies timing seams, not either admission.
"""
import ast,hashlib
from pathlib import Path

import prepare_canonical_c17_outer_sources_v1 as outer

OWN=Path(__file__).resolve().parent
T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
OUTER_SHA='e0713f8a56e3a2be280d140d4f3246d35af84222990bc353d6b268a7d1049ffe'
LIFECYCLE_SHA='dcbb92b3852123a24dac29f35f182eea6a731a46104d1837478c2990052a32ca'
FEEDER='root_p37c17_same_game_loop_feeder92.py'
FEEDER_SHA='512925bd435c77d9b767adef08b25c3893b2c8c5f642f94e22f4e9dfcab35428'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def _change(text,old,new,changes):
    if text.count(old)!=1:raise ValueError('exact timing seam missing/duplicated: '+old[:100])
    changes.append((old,new))
    return text.replace(old,new,1)


def _finish(original,text,changes,name):
    inverse=text
    for old,new in reversed(changes):
        if inverse.count(new)!=1:raise ValueError('ambiguous inverse timing seam')
        inverse=inverse.replace(new,old,1)
    if inverse!=original:raise ValueError('original source differs outside timing seams')
    if ast.dump(ast.parse(inverse),include_attributes=False)!=ast.dump(ast.parse(original),include_attributes=False):
        raise ValueError('original AST differs after timing inverse')
    compile(text,name,'exec')
    return text.encode()


def transform_queue(raw,*,enabled=False):
    if type(enabled) is not bool:raise ValueError('explicit timing source boolean required')
    original=raw.decode();text=original;changes=[]
    def patch(old,new):
        nonlocal text
        text=_change(text,old,new,changes)
    anchor='N = Path(__file__).resolve().parent\n'
    patch(anchor,anchor+'from full_batch_timing_v1 import (full_rows_v1 as _full_rows_v1, record_existing_rpc_row_v1 as _record_full_rpc_row_v1, current_full_row_fields_v1 as _current_full_row_fields_v1, failed_full_row_fields_v1 as _failed_full_row_fields_v1)\n')
    anchor='    async def full_loop(self, session, request, path):\n        """One batch <=30; cumulative cycles and fifth-cycle SAVE never reset."""\n'
    patch(anchor,'    @_full_rows_v1(enabled='+str(enabled)+')\n'+anchor)
    boundary=[n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Name) and n.value.func.id=='_control_rpc_boundary_v1'
        and any(isinstance(a,ast.Constant) and a.value=='rpc_end' for a in n.value.args)]
    if len(boundary)!=1:raise ValueError('exact existing RPC-end boundary required')
    anchor=text.splitlines(keepends=True)[boundary[0].lineno-1]
    indent=anchor[:len(anchor)-len(anchor.lstrip())]
    patch(anchor,anchor+indent+'_record_full_rpc_row_v1(request, row, mono)\n')
    anchor='        atomic(OUTBOX / path.name, {"request": request, "result": {"is_error": False, "structured_content": result}}, limit=16384)\n        self.held_control = None\n        return result\n'
    patch(anchor,'        result.update(_current_full_row_fields_v1())\n'+anchor)
    anchor='''                "client_error": failure["message"], "replay_allowed": False,
                "original_response": self.halted["response"]}, limit=16384)'''
    patch(anchor,'''                "client_error": failure["message"], "replay_allowed": False,
                **_failed_full_row_fields_v1(self, request),
                "original_response": self.halted["response"]}, limit=16384)''')
    return _finish(original,text,changes,'future-Queue-timing'),changes


def transform_handoff(raw):
    original=raw.decode();text=original;changes=[]
    tree=ast.parse(text)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_resident_make_call')
    # Scope the one insert to this existing custom MCP row path. It shares the
    # same process ContextVar as Queue.call; no Native or body collection added.
    lines=text.splitlines(keepends=True)
    piece=''.join(lines[function.lineno-1:function.end_lineno])
    old='        env["atomic"](response, row, limit=env["REPLY_RESERVE"])'
    if old not in piece:raise ValueError('resident existing row seam missing')
    indent=old[:len(old)-len(old.lstrip())]
    new=indent+'from full_batch_timing_v1 import record_existing_rpc_row_v1\n'+indent+'record_existing_rpc_row_v1(request, row, mono)\n'+old
    patched=_change(piece,old,new,[])
    changes.append((piece,patched));text=_change(text,piece,patched,[])
    return _finish(original,text,changes,'future-resident-row-timing'),changes


def transform_feeder(raw,*,enabled=False):
    if type(enabled) is not bool:raise ValueError('explicit timing source boolean required')
    original=raw.decode();text=original;changes=[]
    def patch(old,new):
        nonlocal text
        text=_change(text,old,new,changes)
    # The existing lifecycle helper is frozen; do not add clocks or metrics sinks.
    anchor='def publish_or_follow(sequence: int) -> str:\n'
    patch(anchor,'from full_lifecycle_timing_v1 import FullLifecycleTimingV1\nfrom full_batch_timing_v1 import batch_timing_fields_v1\n_FULL_TIMING_V1 = FullLifecycleTimingV1(enabled='+str(enabled)+')\n\n\n'+anchor)
    patch('    atomic(inbox, request)\n    return "published_new_exact_control"',
          '    _FULL_TIMING_V1.before_publish(sequence)\n    try:\n        atomic(inbox, request)\n    except BaseException:\n        _FULL_TIMING_V1.discard()\n        raise\n    return "published_new_exact_control"')
    anchor='            result, before, response = result_for(sequence, first=first, previous_cycles=previous_cycles)\n'
    patch(anchor,'            try:\n    '+anchor+'            except BaseException:\n                _FULL_TIMING_V1.discard()\n                raise\n            full_wall_fields = _FULL_TIMING_V1.after_receipt(sequence)\n')
    anchor='                "completed_control_sequence": sequence, "control_response": str(response),\n'
    patch(anchor,anchor+'                **batch_timing_fields_v1(result, full_wall_fields),\n')
    return _finish(original,text,changes,'future-feeder-timing'),changes


def build_sources(*,enabled=False):
    if sha(Path(outer.__file__).read_bytes())!=OUTER_SHA:raise ValueError('canonical outer source changed')
    lifecycle=(OWN/'full_lifecycle_timing_v1.py').read_bytes()
    if sha(lifecycle)!=LIFECYCLE_SHA:raise ValueError('frozen FULL lifecycle helper changed')
    graph,_=outer.build_sources(enabled=False)
    queue='root_p37c17_sdk_queue.py';handoff='root_p37c17_automatic_natural_succession_handoff.py'
    raw=(T/FEEDER).read_bytes()
    if sha(raw)!=FEEDER_SHA:raise ValueError('actual immutable feeder source changed')
    result={};changes={}
    result[queue],changes[queue]=transform_queue(graph[queue],enabled=enabled)
    result[handoff],changes[handoff]=transform_handoff(graph[handoff])
    result[FEEDER],changes[FEEDER]=transform_feeder(raw,enabled=enabled)
    result['full_batch_timing_v1.py']=(OWN/'full_batch_timing_v1.py').read_bytes()
    result['full_lifecycle_timing_v1.py']=lifecycle
    return result,changes
