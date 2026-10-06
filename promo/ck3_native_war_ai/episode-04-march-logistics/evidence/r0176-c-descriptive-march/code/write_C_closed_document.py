"""PLAN by default; render neutral knowledge from one exact closed values file.

This document generator is not an independent native observer or media audit.
It opens only the explicitly named bounded JSON values, never referenced paths.
"""
import argparse,hashlib,json
from pathlib import Path

def document(v):
 t=v['terminal'];n=v['normalized_C_result'];a=v['ABC_descriptive_rows']['A'];b=v['ABC_descriptive_rows']['B']
 if not t or n['closed'] is not True or v['winner'] is not None or n['controlled_comparison_eligibility']!='NOT_GRANTED':
  raise ValueError('actual closed descriptive C required, with no winner')
 used=t['elapsed_actual_days'];interval=n['observed_arrival_interval_days']
 event='Stationary London first observed' if t['London_stationary_arrival_observed'] else t['status']
 main=n['subject_scope'];arrival=f'({interval[0]:g}, {interval[1]:g}] actual days' if interval else 'Not observed'
 return f'''# Episode 04: C descriptive march and observed A/B dispositions

This package records a descriptive C march from the same immutable whole-army
checkpoint as A and B. It does not establish a controlled strategy winner.
C has {len(n['sampling_deviations'])} retained sampling deviations; its controlled
comparison eligibility is **NOT_GRANTED**. Each original STOP and subsequent
Root review remains part of the evidence.

| Arm | Prespecified action | Observed disposition | Comparison limit |
| --- | --- | --- | --- |
| A | Whole army directly to London | Closed, stationary London observed in (+49, +51] days | Separate archived actual observation |
| B | Split, rest at distinct sites, reunite and merge, then London | Gate stopped at day {b['days_used']:g}; London not observed | New Regiment and changed commander prevented the frozen postmerge gate; not a deadline censor |
| C | Whole army via 2176, then London | {event}, first terminal observation at day {used:g} | Descriptive continuation; planned one-day sampling eligibility not granted |

The three runs retain separate actual NPC and war-state histories. Different
observation dates, NPC developments and the failed B gate prevent these rows
from being treated as a causal comparison of route cost or military outcome.

The whole checkpoint is 73795635 bytes with SHA-256
`d052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a`.
Common T0 is 53148432 and the original absolute END is 53150592, a horizon of
90 game days. The shared 120 limit counts batches across both C phases;
it is not another game-time allowance.

C's first stationary waypoint 2176 was observed in (+27, +28] days. The London
order was issued on the same paused day 28 with route 729,965,686,628,629,1527.
The earlier camera centered on London did not prove Army arrival or follow.
The London arrival interval is {arrival}; the exact arrival tick remains null.

The required subject is the original Main0 cohort: 27 Regiments and 37 DATA
records, actor 33388 and commander 27357. The terminal required subject scope
reports native global health status `{main['global_health_status']}` and
unassessed CUnit IDs `{main['unassessed_CUnit_ids']}`. Excluded health and the
all-player troop total remain null. A same-position object is not automatically
a transport and an absent health read is not zero soldiers.

The observed Main count changed from {t['current_soldiers']['initial']} to
{t['current_soldiers']['terminal']} (net {t['current_soldiers']['net']:+d}), with
maximum {t['maximum_soldiers']}. Supply changed from
{t['supply_raw']['initial']} to {t['supply_raw']['terminal']} raw units
(net {t['supply_raw']['net']:+d}, scale 100000). Treasury changed from
{t['gold_raw']['initial']} to {t['gold_raw']['terminal']} raw units
(net {t['gold_raw']['net']:+d}, scale 100000). These are balance and row
differences. They do not identify a soldier application ledger, casualties,
travel payment, upkeep or another cause.

Separate cash windows remain visible: +31 net +93767, +59 net -1700000 and +60
net +24723 raw units. The day 59 difference and an earlier displayed embarkation
price do not establish an applied payment. Outside NPC changes remain outside
the required Main cohort and do not count as its losses.

The actual runtime closure and sealed recording metadata are separate sources.
Machine media checks and Root-selected encoded still reviews do not grant
continuous clean footage, exact native event PTS or human 1x full film signoff.
Raw video, screenshots and saves are not copied into this portable text package.

Run the package-relative `code/verify_C_review01.py --verify` using Python with
`-I -S -B` to reproduce the declared text-source joins. The verifier is file-only;
no CK3, SDK, UI, network, process inspection or original C-root path is required.
'''

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true')
 p.add_argument('--values',type=Path);p.add_argument('--sha256');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.write:print(json.dumps({'status':'PLAN_ONLY','source_reads':0,'output_created':False}));return 0
 if a.values is None or a.sha256 is None or a.output is None:p.error('explicit values/SHA/output required')
 try:
  if a.output.exists() or a.values.stat().st_size>2*1024*1024:raise ValueError('fresh output/bounded values required')
  raw=a.values.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact actual values SHA')
  rendered=document(json.loads(raw)).encode('utf-8')
  with a.output.open('xb') as f:f.write(rendered)
  print(json.dumps({'status':'CLOSED_C_DESCRIPTIVE_DOCUMENT_WRITTEN','bytes':len(rendered),'sha256':hashlib.sha256(rendered).hexdigest(),'new_native_or_media_credit':0}));return 0
 except (ValueError,OSError,KeyError,TypeError) as e:print(json.dumps({'status':'FAIL_DOCUMENT_PRESERVED','error':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
