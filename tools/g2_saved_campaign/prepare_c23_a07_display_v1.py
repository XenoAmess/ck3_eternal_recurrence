"""Exact A06 accepted display -> A07 in isolated RAM; Root alone adopts."""
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
U6 = base.T6
U7 = U6.with_name('runtime-a07')
TASK7 = O / 'tasks/spec-display-a07'
QUOTE6 = O / 'A06-ROOT-QUOTE01.json'
QUOTE6_PIN = (129813, '3df5cae9fae318de4462f1db99a274a968dd095ee715284d54b01c093c4a436a')
PROFILE6_PIN = (2906, '3f17b630ce12d46f80fa9ab1f2940fbf423bb0b8416dee83d521ef71bb7fe294')
BASE_PIN = (12181, 'a7b12aaf3a26a8aad011deb263630f942835e5edd1f584f4340040a227cbd9ad')
GAME6 = [59668, 134369485859890359]
DISPLAY6_NONCE = '3189a4ab25914a5ebc242df6296b255d'
TASK6_NONCE = '7d89a976472440f98dbf28741d89728f'
CLOSED6 = O / 'A06-SOURCE-PREFLIGHT-FAILURE-INDEX01.json'
CLOSED6_PIN = (4092, '56d898e80e8dac113844dcefedc669d26c9d906b0b0757becb2b337b2c99a44b')
LAUNCH6_PIN = (6160, 'ff18e4ffff91721edc1b74923c9b0d29113caef266737c3a67b67f8f28d6d348')
TASK6_PIN = (3991, '6bf3d3d60e47688804c22cb6dee47fd1d8c7f675fd7f2fb42d601f7b0d9a8b24')
require, sha, encode, pin, finite, checked = base.require, base.sha, base.encode, base.pin, base.finite, base.checked

PATCHES = (
    ("spec['generation'] == 'C23-A05'", "spec['generation'] == 'C23-A06'"),
    ("spec.update(generation='C23-A06', target_runtime=str(T6), display_nonce=display_nonce)",
     "spec.update(generation='C23-A07', target_runtime=str(T6), display_nonce=display_nonce, previous_Game_tuple=[59668,134369485859890359])"),
    ("A06_display_nonce=display_nonce", "A07_display_nonce=display_nonce"),
    ("profile.pop('A05_display_nonce', None)", "profile.pop('A06_display_nonce', None)"),
    ("xar.C23-A06-complete-display-RAM-review/v1", "xar.C23-A07-complete-display-RAM-review/v1"),
    ("xar.C23-A06-display-prepare-input/v1", "xar.C23-A07-display-prepare-input/v1"),
)


def source(path, expected):
    raw = finite(path)
    require((len(raw), sha(raw)) == expected, 'exact A07 predecessor input differs: ' + str(path))
    return raw, pin(path, raw)


def recipe():
    raw, reference = source(Path(base.__file__), BASE_PIN)
    text = raw.decode('utf-8')
    for before, after in PATCHES:
        require(text.count(before) == 1, 'single exact A07 display source seam required')
        text = text.replace(before, after, 1)
    inverse = text
    for before, after in reversed(PATCHES):
        require(inverse.count(after) == 1, 'single inverse A07 source seam required')
        inverse = inverse.replace(after, before, 1)
    require(inverse.encode('utf-8') == raw, 'A06 recipe changed outside six reviewed seams')
    scope = {'__file__': str(Path(base.__file__)), '__name__': '_isolated_A07_display_recipe'}
    exec(compile(text, '<exact-A07-display-RAM-recipe>', 'exec'), scope)
    scope.update(T5=U6, T6=U7, TASK6=TASK7, QUOTE5=QUOTE6,
                 QUOTE5_PIN=QUOTE6_PIN, PROFILE5_PIN=PROFILE6_PIN,
                 PREDECESSOR_NONCE=DISPLAY6_NONCE)
    return scope, reference


def predecessor():
    closed_raw, closed_ref = source(CLOSED6, CLOSED6_PIN)
    closed = json.loads(closed_raw)
    require(closed.get('schema') == 'xar.C23-A06-source-preflight-failure-index/v1'
            and closed.get('machine_id') == MACHINE
            and closed.get('no_SEM_CAP_or_gameplay') is True
            and closed.get('first_sequence_not_submitted') == 10481
            and closed.get('Game_business_credit') == 0
            and closed.get('actual_Game_created_and_forced_exit1') is True,
            'actual A06 pre-business forced closure differs')
    facts = closed['actual_facts']
    for row in facts:
        checked(row)
    exit_ref = next(row for row in facts if Path(row['path']).name == 'ROOT-ACTUAL-GAME-EXIT-C23.json')
    game_exit = json.loads(checked(exit_ref))
    require(game_exit.get('machine_id') == MACHINE and game_exit.get('kernel_signaled') is True
            and game_exit.get('exit_code') == 1
            and [game_exit.get('pid'), game_exit.get('creation_filetime')] == GAME6,
            'actual A06 predecessor kernel exit differs')
    launch_raw, launch_ref = source(U6 / 'ROOT-ACTUAL-GAME-LAUNCH-C23.json', LAUNCH6_PIN)
    launch = json.loads(launch_raw)
    require(launch.get('machine_id') == MACHINE
            and [launch.get('pid'), launch.get('creation_filetime')] == GAME6,
            'actual A06 Game predecessor tuple differs')
    task_raw, task_ref = source(base.TASK6 / 'SPEC.json', TASK6_PIN)
    task = json.loads(task_raw)
    require(task.get('machine_id') == MACHINE and task.get('nonce') == TASK6_NONCE,
            'actual previous once-only display Task differs')
    return [closed_ref, launch_ref, task_ref, *facts]


def compose(plan):
    require(type(plan) is dict and set(plan) == {
        'schema', 'machine_id', 'full_storage_ref', 'observed_at_utc', 'display_nonce'}
        and plan['schema'] == 'xar.C23-A07-display-prepare-input/v1',
        'exact finite A07 display plan required')
    require(plan['display_nonce'] not in (DISPLAY6_NONCE, TASK6_NONCE),
            'new A07 display nonce must be independent')
    refs = predecessor()
    scope, recipe_ref = recipe()
    values, review, companions = scope['compose'](plan)
    require(review['new_owner_SPEC']['previous_Game_tuple'] == GAME6
            and review['unchanged_source_leaves'] == 15
            and len(values) == 18, 'complete exact A07 eighteen-leaf projection required')
    review.pop('actual_A05_Game_created', None)
    review.update(source_closed_A06=refs[0], actual_A06_Game_tuple=GAME6,
                  actual_A06_Game_exit_kind='forced_exit1_preserved_not_normal',
                  source_recipe=recipe_ref, source_recipe_exact_seams=6)
    review['inputs'].extend([*refs, pin(__file__, finite(__file__))])
    return values, review, companions


def build_sources(*, full_storage_ref, observed_at_utc, display_nonce, machine_id=MACHINE):
    return compose({'schema': 'xar.C23-A07-display-prepare-input/v1', 'machine_id': machine_id,
                    'full_storage_ref': full_storage_ref, 'observed_at_utc': observed_at_utc,
                    'display_nonce': display_nonce})


def build_task_spec(display_values, display_review, *, task_nonce, game_launch_ref, placement_ref):
    require(task_nonce not in (DISPLAY6_NONCE, TASK6_NONCE), 'previous A06 nonce cannot recur')
    predecessor()
    original = base.prior.build_task_spec
    env = dict(original.__globals__, T5=U7, TASK5=TASK7, OLD_GAME=tuple(GAME6))
    binder = FunctionType(original.__code__, env)
    values, review = binder(display_values, display_review, task_nonce=task_nonce,
                           game_launch_ref=game_launch_ref, placement_ref=placement_ref)
    review.update(source_closed_A06=pin(CLOSED6, finite(CLOSED6)),
                  previous_actual_Game=GAME6, previous_display_Task_nonce=TASK6_NONCE)
    return values, review

