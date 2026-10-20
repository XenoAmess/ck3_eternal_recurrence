"""Exact accepted A08 display to A09; RAM outputs, no runtime operations."""
from __future__ import annotations
import sys
import json
from pathlib import Path
from types import FunctionType
OWN = Path(__file__).resolve().parent
if str(OWN) not in sys.path:
    sys.path.insert(0, str(OWN))
import prepare_c23_a08_display_v1 as prior

MACHINE = prior.MACHINE
O = prior.O
U8 = prior.U8
U9 = U8.with_name('runtime-a09')
TASK9 = O / 'tasks/spec-display-a09'
QUOTE8 = O / 'A08-ROOT-QUOTE02.json'
QUOTE8_PIN = (138916, '71d0986d80e419dd26509646a1f5e38591ddc1720b2651391b3cf491339d3261')
PROFILE8_PIN = (2906, 'e50bfff08f2ea6187941e03161dda05d9ae2a12f36c8adf9a1ccb5a4f15c4af6')
PRIOR_PIN = (8180, 'f9976ccdd55dd35ff85be0fc97629ff21c3caa8940dbf31b42bd0ab5ac875afb')
GAME8 = [126468, 134369537928979603]
DISPLAY8_NONCE = '25d93caaadc845a786237d3be9b2a951'
TASK8_NONCE = '4db90fbdaf204ba8b79fb84b215be0ab'
INDEX8 = O / 'A08-SOURCE-CLOCK-FAILURE-INDEX01.json'
INDEX8_PIN = (5914, '43b28b31461e601ee1982667c92a00f2d0e0b3cfb02027e2aa9490c1e1ba0abf')
LAUNCH8_PIN = (6172, '19e9ad61d0abe20aa3384c2c49c698be7ada6c550d26c156183bf74b2e36eb85')
TASK8_PIN = (3992, '2657e0d6c70e22efa3c095bf947cf58470da7df018710bb07c2148d8cb659227')
require, sha, encode, pin, finite, checked = prior.require, prior.sha, prior.encode, prior.pin, prior.finite, prior.checked


def source(path, expected):
    raw = finite(path)
    require((len(raw), sha(raw)) == expected, 'exact A09 source input differs: ' + str(path))
    return raw, pin(path, raw)


def recipe():
    _, prior_ref = source(Path(prior.__file__), PRIOR_PIN)
    replacements = {
        "spec['generation'] == 'C23-A05'": "spec['generation'] == 'C23-A08'",
        "spec.update(generation='C23-A06', target_runtime=str(T6), display_nonce=display_nonce)":
            "spec.update(generation='C23-A09', target_runtime=str(T6), display_nonce=display_nonce, previous_Game_tuple=[126468,134369537928979603])",
        "A06_display_nonce=display_nonce": "A09_display_nonce=display_nonce",
        "profile.pop('A05_display_nonce', None)": "profile.pop('A08_display_nonce', None)",
        "xar.C23-A06-complete-display-RAM-review/v1": "xar.C23-A09-complete-display-RAM-review/v1",
        "xar.C23-A06-display-prepare-input/v1": "xar.C23-A09-display-prepare-input/v1",
        "spec['previous_Game_tuple'] == list(prior.OLD_GAME)": "spec['previous_Game_tuple'] == [244624,134369509365547275]",
    }
    require(len(prior.PATCHES) == 8 and set(replacements) < {before for before, after in prior.PATCHES},
            'exact accepted eight-seam recipe required')
    patches = tuple((before, replacements.get(before, after)) for before, after in prior.PATCHES)
    env = dict(prior.recipe.__globals__, U7=U8, U8=U9, TASK8=TASK9, QUOTE7=QUOTE8,
               QUOTE7_PIN=QUOTE8_PIN, PROFILE7_PIN=PROFILE8_PIN,
               DISPLAY7_NONCE=DISPLAY8_NONCE, PATCHES=patches)
    scope, underlying_ref = FunctionType(prior.recipe.__code__, env)()
    return scope, prior_ref, underlying_ref


def predecessor():
    raw, index_ref = source(INDEX8, INDEX8_PIN)
    index = json.loads(raw)
    require(index.get('machine_id') == MACHINE
            and index.get('schema') == 'xar.A08-source-clock-failure-index/v1'
            and index['roots'] == {'U8': str(U8), 'O': str(O)}, 'actual A08 index differs')
    facts = [dict(path=str(Path(index['roots'][r['root']]) / r['relative']),
                  bytes=r['bytes'], sha256=r['sha256']) for r in index['files']]
    small = [row for row in facts if row['bytes'] <= 262144]
    for row in small:
        checked(row, 262144)
    byname = {Path(row['path']).name: row for row in small}
    media = json.loads(checked(byname['completed.json']))
    require(media.get('state') == 'completed' and index['closure']['recording_worker_exit'] == 0
            and index['closure']['publisher_exit'] == 0, 'actual A08 media closure differs')
    game_exit = json.loads(checked(byname['ROOT-ACTUAL-GAME-EXIT-C23.json']))
    supervisor = json.loads(checked(byname['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A08.json']))
    cleanup = supervisor.get('owned_cleanup') or {}
    sdk = supervisor.get('sdk_actual_exit') or {}
    require(game_exit.get('machine_id') == MACHINE and game_exit.get('kernel_signaled') is True
            and game_exit.get('exit_code') == 1
            and [game_exit.get('pid'), game_exit.get('creation_filetime')] == GAME8
            and cleanup.get('job_active_processes_final') == 0 and cleanup.get('tree_gone') is True
            and {p['role']: p['exit_code'] for p in sdk.get('processes', [])} ==
                {'sdk_queue': 1, 'sdk_application': 0}
            and all(p.get('kernel_exit_observed') is True for p in sdk['processes']),
            'actual A08 forced Game and Queue1/App0 closure differs')
    for name, code in (('spec-supervisor-a08', 1), ('spec-display-a08', 0)):
        ref = next(r for r in small if Path(r['path']).parent.name == name and Path(r['path']).name == 'CLOSED.json')
        value = json.loads(checked(ref))
        require(value.get('machine_id') == MACHINE and value.get('child_exit_code') == code
                and value.get('job_active_after_stage') == 0
                and value.get('forced_remaining_cleanup') is False, 'actual A08 Task closure differs')
    launch_raw, launch_ref = source(U8 / 'ROOT-ACTUAL-GAME-LAUNCH-C23.json', LAUNCH8_PIN)
    launch = json.loads(launch_raw)
    require(launch.get('machine_id') == MACHINE
            and [launch.get('pid'), launch.get('creation_filetime')] == GAME8, 'actual A08 launch differs')
    task_raw, task_ref = source(prior.TASK8 / 'SPEC.json', TASK8_PIN)
    require(json.loads(task_raw).get('nonce') == TASK8_NONCE, 'actual A08 display Task nonce differs')
    forbidden = {DISPLAY8_NONCE, TASK8_NONCE, supervisor['attempt_nonce'], supervisor['task_nonce']}
    return [index_ref, launch_ref, task_ref, *small], forbidden


def compose(plan):
    require(type(plan) is dict and set(plan) == {
        'schema', 'machine_id', 'full_storage_ref', 'observed_at_utc', 'display_nonce'}
        and plan['schema'] == 'xar.C23-A09-display-prepare-input/v1', 'exact A09 display plan required')
    refs, forbidden = predecessor()
    require(plan['display_nonce'] not in forbidden, 'fresh A09 display nonce required')
    scope, prior_ref, recipe_ref = recipe()
    values, review, companions = scope['compose'](plan)
    require(len(values) == 18 and review['unchanged_source_leaves'] == 15
            and review['new_owner_SPEC']['previous_Game_tuple'] == GAME8, 'complete A09 display graph required')
    review.pop('actual_A05_Game_created', None)
    review.update(source_closed_A08=refs[0], actual_A08_Game_tuple=GAME8,
                  source_recipe=recipe_ref, source_adapter=prior_ref,
                  actual_A08_Game_exit_kind='forced_exit1_preserved_not_normal',
                  saved_frontier_and_rollback_owned_by_feeder=True)
    review['inputs'].extend([*refs, prior_ref, pin(__file__, finite(__file__))])
    return values, review, companions


def build_sources(*, full_storage_ref, observed_at_utc, display_nonce, machine_id=MACHINE):
    return compose({'schema': 'xar.C23-A09-display-prepare-input/v1', 'machine_id': machine_id,
                    'full_storage_ref': full_storage_ref, 'observed_at_utc': observed_at_utc,
                    'display_nonce': display_nonce})


def build_task_spec(display_values, display_review, *, task_nonce, game_launch_ref, placement_ref):
    refs, forbidden = predecessor()
    require(task_nonce not in forbidden, 'old A08 nonce cannot recur')
    original = prior.base.prior.build_task_spec
    env = dict(original.__globals__, T5=U9, TASK5=TASK9, OLD_GAME=tuple(GAME8))
    binder = FunctionType(original.__code__, env)
    values, review = binder(display_values, display_review, task_nonce=task_nonce,
                           game_launch_ref=game_launch_ref, placement_ref=placement_ref)
    review.update(source_closed_A08=refs[0], previous_actual_Game=GAME8)
    return values, review

