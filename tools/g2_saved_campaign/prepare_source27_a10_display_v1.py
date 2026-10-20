"""A10 RAM display."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from types import FunctionType
OWN = Path(__file__).resolve().parent
if str(OWN) not in sys.path:
    sys.path.insert(0, str(OWN))
import prepare_c23_a09_display_v1 as prior
base = prior.prior
MACHINE, O, U9 = prior.MACHINE, prior.O, prior.U9
U10 = U9.with_name('runtime-a10')
TASK10 = O / 'tasks/spec-display-a10'
QUOTE9 = O / 'A09-ROOT-QUOTE01.json'
QUOTE9_PIN = (161691, '037b6b30959990e55c184f32a43aa2b582bc3a91b37370921a16917a5641bd85')
PROFILE9_PIN = (2906, '70f0a72bf7af1d74cfc2049343778c8e549da7bd14984971bb36b2079ca3666f')
PRIOR_PIN = (8040, '59e3200c0d309e16ea43b0f72d953412a55d4a259226e4a7244db67e7fb51014')
GAME9 = [251852, 134369595515684194]
DISPLAY9_NONCE = '90769411ac144d8eb5712aac5a978823'
INDEX9 = U9 / 'a09-readonly-diagnostics01/A09-ACTUAL-CLOSURE-INDEX01.json'
INDEX9_PIN = (7036, 'd0d13ae2cf51838092e1ae8c7b3a5bcb141bdd84313d56015ba12003f6cabfee')
FULL = O / 'source27-a10-prep01/STORAGE-CANONICAL-FULL-SOURCE27-A10-1230-02.json'
FULL_PIN = (28046, '74e1ec7ce3dfe56f0920f1175ee01b1d8c4a2e040787f336bf1eb8df3048400a')
BOOT_PIN = (30672, '7a36400ef563d05dcc309900e51970a87fcf5c01a09f6b92643c57ca3b2ec51b')
CONTRACT_PIN = (2615, '3d19624797c122960e52266a8bd5c89c6786cf3dfbdcdf0521e77228bcbb6c92')
require, sha, encode, pin, finite, checked = prior.require, prior.sha, prior.encode, prior.pin, prior.finite, prior.checked
source = prior.source
def recipe():
    _, adapter = source(Path(prior.__file__), PRIOR_PIN)
    _,p=source(Path(base.__file__),prior.PRIOR_PIN)
    edits = {
        "spec['generation'] == 'C23-A05'": "spec['generation'] == 'C23-A09'",
        "spec.update(generation='C23-A06', target_runtime=str(T6), display_nonce=display_nonce)":
            "spec.update(generation='Source27-A10', target_runtime=str(T6), display_nonce=display_nonce, previous_Game_tuple=[251852,134369595515684194])",
        "A06_display_nonce=display_nonce": "A10_display_nonce=display_nonce",
        "profile.pop('A05_display_nonce', None)": "profile.pop('A09_display_nonce', None)",
        "xar.C23-A06-complete-display-RAM-review/v1": "xar.Source27-A10-complete-display-RAM-review/v1",
        "xar.C23-A06-display-prepare-input/v1": "xar.Source27-A10-display-prepare-input/v1",
        "spec['previous_Game_tuple'] == list(prior.OLD_GAME)": "spec['previous_Game_tuple'] == [126468,134369537928979603]",
    }
    require(len(base.PATCHES) == 8 and set(edits) < {a for a,b in base.PATCHES},
            'recipe')
    patches = tuple((a, edits.get(a,b)) for a,b in base.PATCHES) + ((
        "profile['storage_review_at_utc'] == REVIEW_AT",
        "profile['storage_review_at_utc'] == '2026-10-20T10:30:00+00:00'"),)
    env = dict(base.recipe.__globals__, U7=U9, U8=U10, TASK8=TASK10, QUOTE7=QUOTE9,
               QUOTE7_PIN=QUOTE9_PIN, PROFILE7_PIN=PROFILE9_PIN,
               DISPLAY7_NONCE=DISPLAY9_NONCE, PATCHES=patches)
    scope, core = FunctionType(base.recipe.__code__, env)()
    scope['REVIEW_AT'] = '2026-10-20T12:30:00+00:00'
    return scope, [adapter,p,core]
def predecessor():
    raw, ref = source(INDEX9, INDEX9_PIN)
    index = json.loads(raw)
    require(index['machine_id'] == MACHINE and index['schema'] == 'xar.A09-actual-closure-index/v1'
            and index['roots'] == {'U9': str(U9), 'O': str(O)}
            and index['SDK_actual_exits'] == [1,0] and index['Game_forced'] is True
            and index['unknown_AUTO'] == 10519 and index['new_FULL_success'] is False,
            'A09 index')
    facts = [dict(path=str(Path(index['roots'][r['root']]) / r['relative']),
                  bytes=r['bytes'], sha256=r['sha256']) for r in index['files']]
    require(len(facts) == len({r['path'] for r in facts}) == 23, 'A09 facts')
    docs = {r['path']: json.loads(checked(r,262144)) for r in facts}
    def doc(name):
        return next(v for p,v in docs.items() if Path(p).name == name)
    game = doc('ROOT-ACTUAL-GAME-EXIT-C23.json')
    sup = doc('ROOT-FRESH-SUPERVISOR-CLOSED-C23-A09.json')
    require(game['machine_id'] == MACHINE and game['kernel_signaled'] is True
            and game['exit_code'] == 1 and [game['pid'],game['creation_filetime']] == GAME9
            and sup['owned_cleanup']['job_active_processes_final'] == 0
            and sup['owned_cleanup']['tree_gone'] is True, 'A09 forced Game')
    sdk = sup['sdk_actual_exit']['processes']
    require({p['role']:p['exit_code'] for p in sdk} == {'sdk_queue':1,'sdk_application':0}
            and all(p['kernel_exit_observed'] is True for p in sdk), 'SDK exits')
    old = {DISPLAY9_NONCE,sup['attempt_nonce'],sup['task_nonce']}
    for role,code in [('supervisor',1),('display',0),('feeder',0)]:
        closed = docs[str(O / ('tasks/spec-' + role + '-a09/CLOSED.json'))]
        require(closed['machine_id'] == MACHINE and closed['child_exit_code'] == code
                and closed['job_active_after_stage'] == 0 and closed['forced_remaining_cleanup'] is False,
                'A09 Task closed')
        old.add(closed['nonce'])
    require(index['screen_release_sequence'] == 7681, 'A09 screen release')
    media = index['recording_completed']
    require(json.loads(checked(media))['state'] == 'completed'
            and doc('ROOT-RECORDING-WORKER-CLOSED-C23-A09.json')['worker_exit_code'] == 0,
            'A09 completed')
    return [ref,*facts,media], old
def compose(plan):
    require(type(plan) is dict and set(plan) == {
        'schema','machine_id','full_storage_ref','observed_at_utc','display_nonce'}
        and plan['schema'] == 'xar.Source27-A10-display-prepare-input/v1', 'A10 plan')
    _, full = source(FULL,FULL_PIN)
    require(plan['full_storage_ref'] == full, 'Source27 full02')
    refs, old = predecessor()
    require(plan['display_nonce'] not in old, 'new display nonce')
    scope, recipes = recipe()
    values, review, extra = scope['compose'](plan)
    require(len(values) == 18 and len(extra) == 3 and review['unchanged_source_leaves'] == 15
            and review['new_owner_SPEC']['previous_Game_tuple'] == GAME9, '18 leaves')
    review.pop('actual_A05_Game_created',None)
    review.update(source_closed_A09=refs[0],actual_A09_Game_tuple=GAME9,
                  source_recipe=recipes, unknown10519_credit=0)
    review['inputs'].extend([*refs,*recipes,pin(__file__,finite(__file__))])
    return values,review,extra
def build_sources(*,full_storage_ref,observed_at_utc,display_nonce,machine_id=MACHINE):
    return compose(dict(schema='xar.Source27-A10-display-prepare-input/v1',machine_id=machine_id,
                        full_storage_ref=full_storage_ref,observed_at_utc=observed_at_utc,
                        display_nonce=display_nonce))
def build_task_spec(display_values,display_review,*,task_nonce,game_launch_ref,placement_ref,
                    bootstrap_ref,owner_contract_ref):
    refs, old = predecessor()
    require(task_nonce not in old, 'fresh Task nonce')
    for ref,name,want in [(bootstrap_ref,'interactive_task_owner_a10_v1.py',BOOT_PIN),
                              (owner_contract_ref,'owner_prepare_contract_v1.py',CONTRACT_PIN)]:
        require(Path(ref['path']).resolve() == U10 / name, 'A10 bootstrap path')
        source(U10 / name,want)
        require((ref['bytes'],ref['sha256']) == want, 'bootstrap pin')
    orig = base.base.prior.build_task_spec
    binder = FunctionType(orig.__code__,dict(orig.__globals__,T5=U10,TASK5=TASK10,OLD_GAME=tuple(GAME9)))
    values, review = binder(display_values,display_review,task_nonce=task_nonce,
                           game_launch_ref=game_launch_ref,placement_ref=placement_ref)
    path = TASK10 / 'SPEC.json'
    task = json.loads(values[path])
    task.update(bootstrap=str(U10 / 'interactive_task_owner_a10_v1.py'),bootstrap_sha256=BOOT_PIN[1])
    require(task['role'] == 'display_owner' and set(task['env']) == {'PYTHONDONTWRITEBYTECODE','PYTHONPATH'},
            'display env')
    values[path] = encode(task)
    review.update(Task_SPEC=pin(path,values[path]),source_closed_A09=refs[0],
                  previous_actual_Game=GAME9,bootstrap=bootstrap_ref,owner_contract=owner_contract_ref)
    return values,review
