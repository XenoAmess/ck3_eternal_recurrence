"""A08 display RAM from exact accepted A07 inputs."""
from __future__ import annotations
import sys
import json
from pathlib import Path
from types import FunctionType
OWN = Path(__file__).resolve().parent
if str(OWN) not in sys.path:
    sys.path.insert(0, str(OWN))
import prepare_c23_a06_display_v1 as base

MACHINE = base.MACHINE
O = base.O
U7 = base.T6.with_name('runtime-a07')
U8 = U7.with_name('runtime-a08')
TASK8 = O / 'tasks/spec-display-a08'
QUOTE7 = O / 'A07-ROOT-QUOTE01.json'
QUOTE7_PIN = (136953, '7e472344be10e1ef0030da027d9417366fcae1205dd34eba45157fa5751cbbb1')
PROFILE7_PIN = (2906, '0f0a0b4661f469e86111681ea40f00b8c3077a43c5811f2cbe6900c67a1113cc')
BASE_PIN = (12181, 'a7b12aaf3a26a8aad011deb263630f942835e5edd1f584f4340040a227cbd9ad')
GAME7 = [244624, 134369509365547275]
DISPLAY7_NONCE = 'c354d342696b447abd6eb396173ec8a8'
TASK7_NONCE = '06c63705d5d1412ab8fa9286756dc9a6'
CLOSED7 = O / 'A07-SOURCE-POSTPROCESS-FAILURE-INDEX01.json'
CLOSED7_PIN = (4401, 'c9dadda8deba605681410586faec17eed9ce9c9b908b88dfc021dd057d24d6c8')
LAUNCH7_PIN = (6173, '8a2e62577584a8a661d49498db4853847b909511531277b7c36e2a8d9186c77e')
TASK7_PIN = (3992, 'ddadf974835f76d0877d53bb4988126ff964895214bdfcc0c7b0b6ea78fd81ea')
require, sha, encode, pin, finite, checked = base.require, base.sha, base.encode, base.pin, base.finite, base.checked

PATCHES = (
    ("spec['generation'] == 'C23-A05'", "spec['generation'] == 'C23-A07'"),
    ("spec.update(generation='C23-A06', target_runtime=str(T6), display_nonce=display_nonce)",
     "spec.update(generation='C23-A08', target_runtime=str(T6), display_nonce=display_nonce, previous_Game_tuple=[244624,134369509365547275])"),
    ("A06_display_nonce=display_nonce", "A08_display_nonce=display_nonce"),
    ("profile.pop('A05_display_nonce', None)", "profile.pop('A07_display_nonce', None)"),
    ("xar.C23-A06-complete-display-RAM-review/v1", "xar.C23-A08-complete-display-RAM-review/v1"),
    ("xar.C23-A06-display-prepare-input/v1", "xar.C23-A08-display-prepare-input/v1"),
    ("spec['previous_Game_tuple'] == list(prior.OLD_GAME)", "spec['previous_Game_tuple'] == [59668,134369485859890359]"),
    ("raw = finite(QUOTE5)", "raw = finite(QUOTE5, 262144)"),
)


def source(path, expected):
    raw = finite(path)
    require((len(raw), sha(raw)) == expected, 'exact A07 predecessor input differs: ' + str(path))
    return raw, pin(path, raw)


def recipe():
    raw, reference = source(Path(base.__file__), BASE_PIN)
    text = raw.decode('utf-8')
    for before, after in PATCHES:
        require(text.count(before) == 1, 'single exact A08 display source seam required')
        text = text.replace(before, after, 1)
    inverse = text
    for before, after in reversed(PATCHES):
        require(inverse.count(after) == 1, 'A08 inverse seam differs')
        inverse = inverse.replace(after, before, 1)
    require(inverse.encode('utf-8') == raw, 'recipe changed outside eight seams')
    scope = {'__file__': str(Path(base.__file__)), '__name__': '_isolated_A08_display_recipe'}
    exec(compile(text, '<exact-A08-display-RAM-recipe>', 'exec'), scope)
    scope.update(T5=U7, T6=U8, TASK6=TASK8, QUOTE5=QUOTE7,
                 QUOTE5_PIN=QUOTE7_PIN, PROFILE5_PIN=PROFILE7_PIN,
                 PREDECESSOR_NONCE=DISPLAY7_NONCE)
    return scope, reference


def predecessor():
    closed_raw, closed_ref = source(CLOSED7, CLOSED7_PIN)
    closed = json.loads(closed_raw)
    require(closed.get('schema') == 'xar.C23-A07-source-postprocess-failure-index/v1'
            and closed.get('machine_id') == MACHINE
            and closed.get('actual_SEM10481_complete') is True
            and closed.get('CAP_FULL_submitted') is False
            and closed.get('new_game_day_credit') == 0
            and closed.get('NEXT', {}).get('next_sequence') == 10482,
            'actual A07 SEM-complete postprocess failure differs')
    facts = closed['actual_facts']
    for row in facts:
        checked(row)
    byname = {Path(row['path']).name: row for row in facts}
    game_exit = json.loads(checked(byname['ROOT-ACTUAL-GAME-EXIT-C23.json']))
    supervisor = json.loads(checked(byname['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A07.json']))
    cleanup = supervisor.get('owned_cleanup') or {}
    sdk = supervisor.get('sdk_actual_exit') or {}
    require(game_exit.get('machine_id') == MACHINE and game_exit.get('kernel_signaled') is True
            and game_exit.get('exit_code') == 1
            and [game_exit.get('pid'), game_exit.get('creation_filetime')] == GAME7
            and cleanup.get('job_active_processes_final') == 0 and cleanup.get('tree_gone') is True
            and {p['role']: p['exit_code'] for p in sdk.get('processes', [])} ==
                {'sdk_queue': 1, 'sdk_application': 0}
            and all(p.get('kernel_exit_observed') is True for p in sdk['processes']),
            'actual A07 forced Game and Queue1/App0 closure differs')
    for name, code in (('spec-supervisor-a07', 1), ('spec-display-a07', 0)):
        row = next(r for r in facts if Path(r['path']).parent.name == name and Path(r['path']).name == 'CLOSED.json')
        task_closed = json.loads(checked(row))
        require(task_closed.get('machine_id') == MACHINE and task_closed.get('child_exit_code') == code
                and task_closed.get('job_active_after_stage') == 0
                and task_closed.get('forced_remaining_cleanup') is False, 'actual A07 Task closure differs')
    launch_raw, launch_ref = source(U7 / 'ROOT-ACTUAL-GAME-LAUNCH-C23.json', LAUNCH7_PIN)
    launch = json.loads(launch_raw)
    require(launch.get('machine_id') == MACHINE
            and [launch.get('pid'), launch.get('creation_filetime')] == GAME7, 'actual A07 launch differs')
    task_raw, task_ref = source(base.O / 'tasks/spec-display-a07/SPEC.json', TASK7_PIN)
    require(json.loads(task_raw).get('nonce') == TASK7_NONCE, 'actual previous Task nonce differs')
    return [closed_ref, launch_ref, task_ref, *facts]


def compose(plan):
    require(type(plan) is dict and set(plan) == {
        'schema', 'machine_id', 'full_storage_ref', 'observed_at_utc', 'display_nonce'}
        and plan['schema'] == 'xar.C23-A08-display-prepare-input/v1',
        'exact finite A08 display plan required')
    require(plan['display_nonce'] not in (DISPLAY7_NONCE, TASK7_NONCE),
            'new A08 display nonce must be independent')
    refs = predecessor()
    scope, recipe_ref = recipe()
    values, review, companions = scope['compose'](plan)
    require(review['new_owner_SPEC']['previous_Game_tuple'] == GAME7
            and review['unchanged_source_leaves'] == 15
            and len(values) == 18, 'complete exact A08 eighteen-leaf projection required')
    review.pop('actual_A05_Game_created', None)
    review.update(source_closed_A07=refs[0], actual_A07_Game_tuple=GAME7,
                  actual_A07_Game_exit_kind='forced_exit1_preserved_not_normal', predecessor_SEM10481_completed=True,
                  source_recipe=recipe_ref, source_recipe_exact_seams=8)
    review['inputs'].extend([*refs, pin(__file__, finite(__file__))])
    return values, review, companions


def build_sources(*, full_storage_ref, observed_at_utc, display_nonce, machine_id=MACHINE):
    return compose({'schema': 'xar.C23-A08-display-prepare-input/v1', 'machine_id': machine_id,
                    'full_storage_ref': full_storage_ref, 'observed_at_utc': observed_at_utc,
                    'display_nonce': display_nonce})


def build_task_spec(display_values, display_review, *, task_nonce, game_launch_ref, placement_ref):
    require(task_nonce not in (DISPLAY7_NONCE, TASK7_NONCE), 'previous A06 nonce cannot recur')
    predecessor()
    original = base.prior.build_task_spec
    env = dict(original.__globals__, T5=U8, TASK5=TASK8, OLD_GAME=tuple(GAME7))
    binder = FunctionType(original.__code__, env)
    values, review = binder(display_values, display_review, task_nonce=task_nonce,
                           game_launch_ref=game_launch_ref, placement_ref=placement_ref)
    review.update(source_closed_A07=pin(CLOSED7, finite(CLOSED7)),
                  previous_actual_Game=GAME7, previous_display_Task_nonce=TASK7_NONCE)
    return values, review

