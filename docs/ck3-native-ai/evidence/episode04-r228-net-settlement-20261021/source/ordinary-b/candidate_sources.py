"""Read exact published blobs; reconstruct this thin offline candidate in RAM."""
from __future__ import annotations
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import types

HEAD = 'b887921f6b026f79b95a76a18dcd69f258c8e2b2'
W = 'C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree'
PREFIX = 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/'
NAMES = ('schema_source.py', 'strategy_b.py', 'strategy_b_next.py',
         'strategy_b_normal_stages.py', 'r10.schema.json')


def need(ok: object, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def blob(name: str) -> str:
    result = subprocess.run(['git', '--no-optional-locks', '-C', W, 'show', HEAD + ':' + PREFIX + name],
        env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'}, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True)
    return result.stdout.decode('utf-8')


def replacement(value: str, old: str, new: str) -> str:
    need(value.count(old) == 1, 'exact baseline replacement differs: ' + old[:65])
    return value.replace(old, new, 1)


def sources() -> tuple[dict[str, str], dict[str, str]]:
    old = {name: blob(name) for name in NAMES}
    new = dict(old)
    line = next(x for x in old['schema_source.py'].splitlines() if x.startswith('RUNTIME=obj('))
    props = "MANAGED_CAMPAIGN=obj({'run_id':S,'state_dir':S,'bridge_pipe':S,'host_path':S,'frozen_argv_sha256':SHA})\n"
    runtime = line.replace("'episode':S", "'episode':{'anyOf':[S,NULL]}")
    runtime = runtime[:-2] + ",'managed_campaign_run_binding':MANAGED_CAMPAIGN},required=" + repr(
        ['machine_id','started_at_utc','pid','process_create_time_100ns','connection_generation',
         'episode','player_character_id','source_head','native_dll_sha256','source_proof']) + ')'
    # Remove the old closing object brace before adding the optional ordinary field.
    runtime = runtime.replace("ref('pin')},'managed_campaign", "ref('pin'),'managed_campaign")
    guard = "\nRUNTIME['allOf']=[{'if':{'properties':{'episode':{'type':'null'}}},'then':{'required':['managed_campaign_run_binding']}}]"
    new['schema_source.py'] = replacement(old['schema_source.py'], line, props + runtime + guard)
    n = replacement(old['strategy_b.py'], 'import r10_compare as c\n',
        'import r10_compare as c\nfrom ordinary_campaign import check_runtime, episode_value, same_episode\n')
    n = replacement(n, "snapshot = c.frame(evidence.json(ep['snapshot']), runtime)",
        "snapshot = c.frame(evidence.json(ep['snapshot']), runtime)\n    check_runtime(snapshot, runtime)")
    n = replacement(n, "    need(a['episode_run_id'] == b['episode_run_id'] and\n         a['diagnostics']['connection_generation'] == b['diagnostics']['connection_generation'],",
        "    same_episode(a, b)\n    need(a['diagnostics']['connection_generation'] == b['diagnostics']['connection_generation'],")
    n = replacement(n, "action.get('submitted_' + field) == before['snapshot'][field]",
        "action.get('submitted_' + field) == (episode_value(before['snapshot']) if field == 'episode_run_id' else before['snapshot'][field])")
    n = replacement(n, "action.get('observed_episode_run_id') == after['snapshot']['episode_run_id']",
        "action.get('observed_episode_run_id') == episode_value(after['snapshot'])")
    new['strategy_b.py'] = n
    n = replacement(old['strategy_b_next.py'], "'date_raw', 'episode_run_id',", "'date_raw',")
    new['strategy_b_next.py'] = replacement(n, '    for field in fields:\n',
        '    b.check_runtime(actual, runtime)\n    b.same_episode(before, after)\n    b.same_episode(before, actual)\n    for field in fields:\n')
    new['strategy_b_normal_stages.py'] = replacement(old['strategy_b_normal_stages.py'],
        "('episode_run_id', frame['episode_run_id'])", "('episode_run_id', st.next.b.episode_value(frame))")
    module = types.ModuleType('generated_candidate_schema')
    exec(compile(new['schema_source.py'], 'schema_source.py', 'exec'), module.__dict__)
    new['r10.schema.json'] = json.dumps(module.SCHEMA, ensure_ascii=False, indent=2) + '\n'
    new['ordinary_campaign.py'] = Path(__file__).with_name('ordinary_campaign.py').read_text(encoding='utf-8')
    return old, new


def patch(old: dict[str, str], new: dict[str, str]) -> str:
    """Existing-file diff only; the new helper is a separate exact source row."""
    out: list[str] = []
    for name, value in new.items():
        if name not in old:
            continue
        prior = old.get(name, '')
        path = PREFIX + name
        out.extend(difflib.unified_diff(prior.splitlines(keepends=True), value.splitlines(keepends=True),
            fromfile='a/' + path if name in old else '/dev/null', tofile='b/' + path))
    return ''.join(out)
