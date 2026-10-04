"""Bounded exact world-character comparison, resource closure and source-elector origin evidence.

Existing immutable saves/reports only. Missing dead-character rite fields are
retained as unknown, never invented and never treated as a failed game effect.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
EXT = ROOT.parent
LIVE = EXT / 'live-attempt-006'
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game')
HELPER = EXT / 'r6-baseline-readback-001/helper-v2/r6_i2_readback.py'
spec = importlib.util.spec_from_file_location('r6_world_origin_support', HELPER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SAVES = {
    '0030-setup': ('0030-i2-setup-save', '3f03971940fe97653f392691a36acee63bd66544d49b35b57296c744fe47da37'),
    '0036-actual-dplus2': ('0036-i2-one-day-save', '97fe09b4d9ff9cfc59bfbeb4b9ff7bf795538cfa22c8fd07ac73c6dd2b61eee5'),
    '0040-resources': ('0040-i2-resources-save', '129616804d118c0ba035921e97e1e4a9f0d01abcb3687e1a8eb77ce57961ad23'),
    '0042-proposal-open': ('0042-i2-detach-open-save', '7b5adbc84232b6c1159f4d472cd87778b5910c4f1594399e118a6116edb1a42c'),
}
REPORTS = {
    '0030-setup': EXT / 'r6-i2-setup-readback-001/generic/report.json',
    '0036-actual-dplus2': EXT / 'r6-i2-after-two-days-readback-001/generic/report.json',
    '0040-resources': EXT / 'r6-i2-resources-readback-001/generic/report.json',
}
WANTED = {'31254', '65856', '65857', '65860', '65861', '34973', '34232', '59621'}
SECTIONS = [('living', 'dead_unprunable'), ('dead_unprunable', 'characters'), ('characters', 'units')]

def sha(path):
    return m.sha(path)

def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)

def js(path, obj):
    write(path, (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def value(entries, key):
    return m.unquote(m.one(entries, key))

def scalar(raw, key):
    matches = re.findall(r'(?m)^\t' + re.escape(key) + r'=([^\n]+)\s*$', raw)
    if len(matches) > 1:
        raise ValueError('Nonunique character scalar field: ' + key)
    return matches[0].strip() if matches else None

def parse_character(raw, section):
    entries = m.parsed(raw)
    alive = m.one(entries, 'alive_data') or []
    variables, lists, _ = m.stored(alive)
    skills = m.one(entries, 'skill')
    skill_array = [e['value'] for e in skills] if isinstance(skills, list) else None
    court = m.one(entries, 'court_data') or []
    return {'id': raw.split('=', 1)[0], 'section': section, 'first_name': value(entries, 'first_name'),
            'birth': value(entries, 'birth'), 'culture': value(entries, 'culture'), 'rite_id': value(entries, 'rite'),
            'organization': value(entries, 'organization'), 'traits': m.one(entries, 'traits'),
            'saved_skill_array': skill_array, 'saved_base_learning': m.numeric(skill_array[4]) if skill_array and len(skill_array) > 4 else None,
            'total_learning': None, 'total_learning_boundary': 'Not reconstructed from base skills or traits; current elector membership is separately saved.',
            'court_data': court, 'actual_court_employer': value(court, 'employer'),
            'actual_council_task': value(court, 'council_task'), 'join_court_date': value(court, 'join_court_date'),
            'is_in_the_council_saved_flag_present': bool(re.search(r'(?m)^\s*flag=is_in_the_council\s*$', raw)),
            'lyd_variables': variables, 'lyd_lists': lists, 'saved_entries': entries}

def scan_world(text, label, initial_ids):
    records, selected, selected_raw, counts, missing = {}, {}, {}, {}, {}
    for section, following in SECTIONS:
        body = m.r3.section(text, section, following)
        count = 0
        absent = []
        for match in re.finditer(r'(?ms)^([0-9]+)=\{\n.*?^\}', body):
            cid, raw = match.group(1), match.group(0)
            if cid in records:
                raise ValueError('Duplicate actual full character identity across stores: ' + cid)
            rite = scalar(raw, 'rite')
            records[cid] = {'section': section, 'normalized_record_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                            'normalized_record_characters': len(raw), 'rite_id': rite, 'rite_field_present': rite is not None}
            if rite is None:
                absent.append(cid)
            if cid in WANTED or (initial_ids is not None and cid not in initial_ids):
                selected[cid] = parse_character(raw, section)
                selected_raw[cid] = raw
                write(ROOT / 'evidence' / label / ('character-' + cid + '.excerpt.txt'), (raw + '\n').encode())
            count += 1
        counts[section], missing[section] = count, absent
    js(ROOT / 'evidence' / label / 'all-character-record-hash-map.json', records)
    js(ROOT / 'evidence' / label / 'selected-character-state.json', selected)
    return records, selected, selected_raw, counts, missing

def delta_ids(before, after):
    common = set(before) & set(after)
    return {'added_ids': sorted(set(after) - set(before), key=int), 'removed_ids': sorted(set(before) - set(after), key=int),
            'changed_record_ids': sorted((cid for cid in common if before[cid] != after[cid]), key=int),
            'changed_own_rite_ids': sorted((cid for cid in common if (before[cid]['rite_id'], before[cid]['rite_field_present']) != (after[cid]['rite_id'], after[cid]['rite_field_present'])), key=int),
            'changed_character_store_ids': sorted((cid for cid in common if before[cid]['section'] != after[cid]['section']), key=int)}

def main():
    assert not (ROOT / 'REPORT.json').exists()
    package = {'schema': 'lyd.r6-resources-and-elector-origin.v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
               'game_called': False, 'native_called': False, 'git_called': False, 'tracked_written': False,
               'frozen_r6_source_head_parent': '3d3305e75cf642a7a82bef5f9aee03dc76b3c10e',
               'character_record_normalization': 'Original whole save SHA is separately checked. Only UTF8-sig decode and CRLF-to-LF normalize records; complete raw record hashes preserve missing rite and all opaque fields.',
               'missing_policy': 'Absent character fields and type=value with omitted identity remain absent/unknown; no total Learning, zero numeric value, AI status or decision is manufactured.',
               'prior_failed_reader': str(EXT / 'r6-resource-closure-resume-20261005-001/execution-receipt.json'),
               'snapshots': {}, 'input_references': []}
    maps, selected, selected_raw, graphs, titles = {}, {}, {}, {}, {}
    initial_ids = None
    generic = {}
    for label, path in REPORTS.items():
        report = json.loads(path.read_bytes())
        assert report['artifact']['sha256'] == SAVES[label][1]
        generic[label] = report
        write(ROOT / 'inputs' / (label + '.generic-report.raw.json'), path.read_bytes())
        package['input_references'].append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)})
    for label, (dirname, expected) in SAVES.items():
        save = LIVE / 'checkpoints' / dirname / 'save.ck3'
        receipt = LIVE / 'checkpoints' / dirname / 'receipt.json'
        stat = save.stat()
        assert sha(save) == expected
        wrapper = json.loads(receipt.read_bytes())
        assert wrapper['sha256'] == expected and wrapper['bytes'] == stat.st_size and wrapper['played_character_id'] == 31254
        write(ROOT / 'inputs' / (label + '.wrapper.raw.json'), receipt.read_bytes())
        text = save.read_bytes().decode('utf-8-sig').replace('\r\n', '\n')
        maps[label], selected[label], selected_raw[label], counts, missing = scan_world(text, label, initial_ids)
        if initial_ids is None:
            initial_ids = set(maps[label])
        metadata = m.parsed(m.r3.extract_exact_indented_block(text, 'meta_data', 0))
        title_text = m.r3.section(text, 'landed_titles', 'dynasties')
        titles[label] = {'sha256_normalized_whole_title_section': hashlib.sha256(title_text.encode()).hexdigest(),
                         'normalized_characters': len(title_text), 'record_count': len(re.findall(r'(?m)^([0-9]+)=\{', title_text))}
        if label in generic:
            state = generic[label]['state']
            graphs[label] = {'all_faiths': state['all_faiths'], 'all_rites': state['all_rites']}
        else:
            graph_output = ROOT / 'evidence' / label / 'graph'
            graph_output.mkdir(parents=True)
            evidence = []
            graphs[label] = {'all_faiths': m.graph_section(text, 'faiths', graph_output, evidence),
                             'all_rites': m.graph_section(text, 'rites', graph_output, evidence)}
            js(graph_output / 'actual-graph-state.json', graphs[label])
        # Two task records provide saved role/owner correspondence, independent
        # of a guessed employer from the wrong alive_data level.
        taskrows = {}
        for taskid in ('506', '1359'):
            matches = list(re.finditer(r'(?ms)^\t\t' + taskid + r'=\{\n.*?^\t\t\}', text))
            relevant = [mt.group(0) for mt in matches if 'court_owner=' in mt.group(0) and 'type=task_' in mt.group(0)]
            if len(relevant) != 1:
                raise ValueError('Expected unique actual council task: ' + taskid)
            taskrows[taskid] = m.parsed(relevant[0])
            write(ROOT / 'evidence' / label / ('council-task-' + taskid + '.excerpt.txt'), (relevant[0] + '\n').encode())
        snapshot = {'artifact': {'path': str(save), 'bytes': stat.st_size, 'sha256': expected},
                    'saved_date': value(metadata, 'meta_date'), 'actual_native_date_raw_from_wrapper': wrapper['date_raw'],
                    'character_counts': counts, 'total_character_records': len(maps[label]), 'missing_own_rite_fields': missing,
                    'all_title_section': titles[label], 'selected_characters': selected[label], 'actual_council_tasks': taskrows}
        package['snapshots'][label] = snapshot
        assert sha(save) == expected and save.stat().st_mtime_ns == stat.st_mtime_ns
        print(json.dumps({'phase': label, 'characters': len(maps[label]), 'missing_rite_count': sum(len(v) for v in missing.values())}), flush=True)

    transitions = {}
    labels = list(SAVES)
    for before, after in zip(labels, labels[1:]):
        key = before + '--to--' + after
        transitions[key] = delta_ids(maps[before], maps[after])
        transitions[key]['all_title_section_exactly_equal'] = titles[before] == titles[after]
        transitions[key]['all_faith_objects_exactly_equal'] = graphs[before]['all_faiths'] == graphs[after]['all_faiths']
        transitions[key]['all_rite_objects_exactly_equal'] = graphs[before]['all_rites'] == graphs[after]['all_rites']
        js(ROOT / 'evidence' / (key + '.world-character-delta.json'), transitions[key])
    package['world_transitions'] = transitions

    before, after = generic['0036-actual-dplus2'], generic['0040-resources']
    old, new = before['state']['roles']['actor'], after['state']['roles']['actor']
    variables = new['variables']
    checks = []
    def eq(name, actual, expected):
        checks.append({'name': name, 'actual': actual, 'expected': expected, 'passed': actual == expected})
    eq('resource same saved actor and native actor31254', [old['id'], new['id'], after['native_receipt']['checkpoint']['sha256']], ['31254', '31254', SAVES['0040-resources'][1]])
    eq('resource actual saved and native dates unchanged', [before['state']['metadata']['meta_date'], after['state']['metadata']['meta_date'], before['native_receipt']['date_raw'], after['native_receipt']['date_raw']], ['1066.9.17', '1066.9.17', 53144376, 53144376])
    for currency, expected_delta in [('gold', '2000'), ('piety', '9000')]:
        eq('actual saved resource addition ' + currency, str(Decimal(new['saved_values'][currency]) - Decimal(old['saved_values'][currency])), expected_delta)
        eq('SDK independently agrees with saved ' + currency, after['native_receipt']['values'][currency], new['saved_values'][currency])
    for currency in ['prestige', 'stress', 'learning_lifestyle_xp']:
        eq('resource other saved value unchanged ' + currency, new['saved_values'][currency], old['saved_values'][currency])
    expected_records = {'lyd_r4_gold_before': '229', 'lyd_r4_piety_before': '185', 'lyd_r4_gold_expected': '2229',
                        'lyd_r4_piety_expected': '9185', 'lyd_r4_gold_after': '2229', 'lyd_r4_piety_after': '9185'}
    for key, number in expected_records.items():
        eq('actual resource recorder ' + key, variables[key].get('number'), number)
    eq('only resource six records and one prepared flag added', sorted(set(variables) - set(old['variables'])), sorted(set(expected_records) | {'lyd_r4_resources_prepared'}))
    eq('no LYD variable removed', sorted(set(old['variables']) - set(variables)), [])
    eq('every prior actor LYD variable exact unchanged', {key: variables[key] for key in old['variables']}, old['variables'])
    eq('every actor LYD list exact unchanged', new['lists'], old['lists'])
    for role in ['source_rep', 'receiving_rep']:
        eq('actual complete saved projection unchanged ' + role, after['state']['roles'][role], before['state']['roles'][role])
    resource_transition = transitions['0036-actual-dplus2--to--0040-resources']
    eq('resource all world character identities unchanged', [resource_transition['added_ids'], resource_transition['removed_ids'], resource_transition['changed_character_store_ids']], [[], [], []])
    eq('resource whole saved records only actor changed', resource_transition['changed_record_ids'], ['31254'])
    eq('resource all saved character own rite fields unchanged including absence', resource_transition['changed_own_rite_ids'], [])
    eq('resource all actual Faith objects exact unchanged', resource_transition['all_faith_objects_exactly_equal'], True)
    eq('resource all actual Rite objects exact unchanged', resource_transition['all_rite_objects_exactly_equal'], True)
    eq('resource entire title section exact unchanged', resource_transition['all_title_section_exactly_equal'], True)
    eq('resource actor political family skill traits projection unchanged',
       [new['saved_family_data'], new['saved_skill_array'], new['traits'], new['landed_data'], new['actual_saved_held_title_ids']],
       [old['saved_family_data'], old['saved_skill_array'], old['traits'], old['landed_data'], old['actual_saved_held_title_ids']])
    eq('resource no formal C2/C3 actor records seeded', sorted(key for key in variables if key.startswith(('lyd_c2_', 'lyd_c3_'))), [])
    actor_delta = m.r3.parsed(selected_raw['0036-actual-dplus2']['31254']), m.r3.parsed(selected_raw['0040-resources']['31254'])
    from xar_autoplayer.simulation.knight_causal_save_projection import delta
    js(ROOT / 'evidence/resource-actor-lossless-field-delta.json', delta(*actor_delta))
    resource = {'result': 'PASS_RESOURCE_FIXTURE_ONLY' if all(row['passed'] for row in checks) else 'FAIL_RESOURCE_FIXTURE_CHECKS',
                'checks': checks, 'failed_check_names': [row['name'] for row in checks if not row['passed']],
                'actual_before_resources': old['saved_values'], 'actual_after_resources': new['saved_values'],
                'scope': '0036 to0040 only: exact+2000 gold/+9000 piety and seven fixture records; all other world character raw records, all Faith/Rite objects and whole title section verified unchanged. Saved missing rite fields are compared as actual absent fields, without a fabricated resolved Faith.'}
    package['resource_closure'] = resource
    js(ROOT / 'RESOURCE-REPORT.json', resource)

    origin = {'observed_new_character_interval': '0030-setup to0036 actual D+2; not0040 resources to0042 proposal',
              'actual_source_elector_ids_0042': ['31254', '65856', '65860', '65861'],
              'source_total_0042': '4', 'source_yes_before_player_vote_0042': '2',
              'hypotheses': {
                  'proposal_preview_created65860_65861': 'Excluded by their complete actual existence already in0036 and0040.',
                  'birth_during_Dplus2': 'Excluded by actual saved birth1034.8.11 and1017.8.25; these are adults with join_court_date1066.9.16.',
                  'fixture_created65860_65861': 'Not supported: frozen fixture has exactly two create_character blocks, employer root, age40, Learning20, matching tracked reps65856/65857. These two new adults have foreign employers34973/34232, ages32/49 and baseLearning8/7.',
                  'native_court_chaplain_pool_appointment': 'Source-grounded inference: actual council tasks1359 and506 switch from previous religious-relations councillors to65860/65861, and current vanilla councillor_court_chaplain uses auto_fill, fill_from_pool and pool_court_chaplain with same-rite clergy age25-55. This readback does not contain the original native create/appoint call or prove unique causation.'},
              'learning_boundary': 'The engine saved both in the source-elector list under the loaded learning>=15 trigger. BaseLearning8/7 is not a total-Learning read; no exact total is reconstructed.',
              'collection_contract': 'Loaded lyd_c2_collect_source_effect iterates every_faith_character and filters moving rite plus elector trigger; it is not limited to the two fixture delegates or the initiating court.',
              'exact_world_delta_0040_to0042': transitions['0040-resources--to--0042-proposal-open'],
              'selected_character_projections': {label: {cid: state.get(cid) for cid in ['65856', '65857', '65860', '65861', '34973', '34232', '59621']} for label, state in selected.items()},
              'council_task_projections': {label: package['snapshots'][label]['actual_council_tasks'] for label in labels}}
    package['elector_origin'] = origin
    js(ROOT / 'ELECTOR-ORIGIN-REPORT.json', origin)
    sources = [HELPER, EXT / 'r3_checkpoint_readback.py',
               LIVE / 'content/i2-fixture/common/scripted_effects/lyd_r4_fixture_effects.txt',
               LIVE / 'content/i2-fixture/common/decisions/lyd_r4_fixture_decisions.txt',
               LIVE / 'content/production/common/scripted_effects/lyd_c2_setup_effects.txt',
               LIVE / 'content/production/common/scripted_triggers/lyd_c2_consent_triggers.txt',
               GAME / 'common/council_positions/00_council_positions.txt',
               GAME / 'common/council_positions/_council_positions.info',
               GAME / 'common/pool_character_selectors/00_clergy.txt',
               GAME / 'common/council_tasks/00_court_chaplain_tasks.txt']
    for index, source in enumerate(sources):
        dest = ROOT / 'source' / (str(index).zfill(2) + '-' + source.name)
        write(dest, source.read_bytes())
        package['input_references'].append({'path': str(source), 'bytes': source.stat().st_size, 'sha256': sha(source)})
    js(ROOT / 'REPORT.json', package)
    lines = ['# R6 resource closure and source-elector origin', '',
             'Resource comparison: **' + resource['result'] + '**. Checks: ' + str(len(checks)) + '; failed: ' + str(resource['failed_check_names']) + '.', '',
             resource['scope'], '',
             'The original partial comparator assumed every dead character had a rite field and rejected dead_unprunable/40982. Its failed run is preserved in the001 package. This002 reader hashes complete character records and retains missing rite fields instead of inserting a Rite/Faith identity.', '',
             '| Interval | Added characters | Removed characters | Changed complete records |', '| --- | --- | --- | --- |']
    for key, transition in transitions.items():
        lines.append('| ' + key + ' | ' + str(len(transition['added_ids'])) + ' | ' + str(len(transition['removed_ids'])) + ' | ' + str(len(transition['changed_record_ids'])) + ' |')
    lines += ['', '65860 (Goubert, birth1034.8.11, baseLearning8, rite169) and65861 (Jordan, birth1017.8.25, baseLearning7, rite169) are absent in0030, present in0036 and0040, and retained in0042. Both joined foreign courts on1066.9.16: employers34973 and34232, council tasks1359 and506. These actual tasks are religious-relations tasks. See per-checkpoint character/task excerpts and full world hash maps.', '',
              'The frozen fixture creates two age40, baseLearning20 representatives for root31254, identified by saved role pointers as65856 and65857. The resource effect and C2 source-collection effect create no character. C2 collects every qualifying same-rite character across the Faith. Actual source electorate is four:31254,65856,65860,65861. Do not reduce it to the two fixture delegates.', '',
              'Vanilla court-chaplain automatic filling from its same-rite clergy pool is supported by the saved replacement tasks and the current-build primary scripts (auto_fill/fill_from_pool/pool_court_chaplain, clergy age25-55). It is a source-grounded inference; the original native creator/appointment call is absent from this file-only evidence, so unique causation is not claimed.', '',
              'No game/native/Git/mount operation or tracked edit was performed. Missing fields, exact total Learning and vote choices are not manufactured. Whole source saves are hash-verified before and after read. This closes the authorized resource fixture check and character provenance observations, not complete C2/R6 acceptance.']
    write(ROOT / 'REPORT.md', ('\n'.join(lines) + '\n').encode())
    js(ROOT / 'INDEX.json', {'schema': 'lyd.r6-readback-evidence-index.v1', 'scenario': 'resource closure and exact elector origin',
                            'source_save_sha256': [row[1] for row in SAVES.values()],
                            'files': [{'path': str(p.relative_to(ROOT)).replace(chr(92), '/'), 'bytes': p.stat().st_size, 'sha256': sha(p)}
                                      for p in sorted(ROOT.rglob('*')) if p.is_file()]})
    print(json.dumps({'resource_result': resource['result'], 'resource_failed_checks': resource['failed_check_names'],
                      'transitions': {key: {field: val for field, val in row.items() if field not in ['changed_record_ids']} for key, row in transitions.items()},
                      'report_sha256': sha(ROOT / 'REPORT.json'), 'index_sha256': sha(ROOT / 'INDEX.json')}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
