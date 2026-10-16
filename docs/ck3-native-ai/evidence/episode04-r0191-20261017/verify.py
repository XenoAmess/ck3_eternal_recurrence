"""Offline R191 small-evidence verification; never opens original large assets."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
PREFIX = 'docs/ck3-native-ai/evidence/episode04-r0191-20261017/'

def need(value, reason):
    if not value:
        raise ValueError(reason)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify(package=None, repo=None):
    outer = zipfile.ZipFile(package) if package else None
    def read(name):
        return outer.read(PREFIX+name) if outer else Path(__file__).with_name(name).read_bytes()
    index = json.loads(read('source-index.json'))
    archives = {}
    count = 0
    for label, entry in index['archives'].items():
        body = read(entry['file'])
        need(len(body) == entry['bytes'] and sha(body) == entry['sha256'], 'archive pin: '+label)
        z = zipfile.ZipFile(io.BytesIO(body)); archives[label] = z
        need(set(z.namelist()) == {x['member'] for x in entry['entries']}, 'archive member vector')
        for item in entry['entries']:
            b = z.read(item['member']); p = item['source']
            need(len(b) == p['bytes'] and sha(b) == p['sha256'], 'member pin: '+item['member'])
            count += 1
    def obj(label, name):
        return json.loads(archives[label].read(name))
    for item in index.get('standalone_originals', []):
        b = read(item['file']); s = item['source']
        need(len(b) == s['bytes'] and sha(b) == s['sha256'], 'standalone original pin')
        count += 1
    p, r = archives['provenance'], archives['results']
    facts_bytes = read('facts.derived-a01.json')
    need(sha(facts_bytes) == index['facts_sha256'], 'derived facts pin')
    facts = json.loads(facts_bytes)
    machine = 'desktop-3fevhd2-1c74096080'
    need(index['machine_id'] == facts['machine_id'] == machine, 'machine scope')
    q = obj('provenance', 'build/ROOT-PRODUCTION-QUALIFICATION.actual-a31.json')
    need(q['fixture_execution_count'] == 2 and q['prior_fixture_reuse_count'] == 4 and q['fixtures_once'], 'fixture counts')
    need(q['production_bytes_qualified'] and not q['gameplay_result_qualified'], 'build boundary')
    admission = obj('provenance', 'sampling/a04/ADMISSION.actual-a04.json')
    need(not admission['prior_attempts_complete_PASS'], 'old sampling RED retained')
    error = obj('results', 'sampling/r191-sampling-a03-06-natural-query.json')
    need('army_observer_research_sampling_frame_invalid' in json.dumps(error), 'sampling exact error')
    need(not facts['UI']['native_only_qualification'], 'UI scope')
    film = obj('provenance', 'scene/r191-film-a01-film-result.actual.json')
    media = obj('results', 'media/portable-media-facts.actual-a01.json')
    need(film['completed_days'] == media['native_completed_days'] == 2 and film['last_date_raw'] == 53148192, 'two days')
    need(abs(film['recorder_ready_to_resume_ack_seconds']-3.7233502) < 1e-7, 'handoff')
    need(media['video']['timeline']['frames'] == 3359 and abs(media['encoded_frame_end_seconds']-111.966) < .0001, 'encoded extent')
    need(media['encoded_110_seconds_met'] and media['wall_115_seconds_met'], 'separate duration tests')
    need(media['full_available_AV_decode_exit'] == 0 and media['full_available_AV_decode_diagnostics'] == '' and media['audio_stream_count'] == 0, 'decode/noaudio')
    tail = media['paused_tail']
    need(tail['readonly_snapshots_verified'] == 83 and tail['all_snapshots_paused'] and tail['all_date_raw'] == 53148192 and tail['additional_resume_count_reported'] == 0, 'pause tail')
    need(abs(tail['wall_seconds']-82.9820883) < 1e-7 and not tail['business_or_research_qualification_credit'], 'tail qualification')
    capture = media['capture_source']
    need(capture['kind'] == 'gdigrab-desktop-client-region' and capture['client_screen_rect'] == [640,360,1920,1080] and not capture['direct_hwnd_capture'] and capture['output_size'] == [1280,720], 'capture rect')
    need(not any(media['claims'].values()) and not media['Root_limited_review_report_received'], 'media review limits')
    result = obj('results', 'recorder/result.json')
    bootstrap = obj('results', 'close/bootstrap-result.json')
    release = obj('results', 'close/SCREEN-RELEASE.actual.json')
    need(result['state'] == 'NORMAL_TREE_EMPTY' and result['job']['returncode'] == 0 and result['job']['job_active_processes'] == 0, 'recorder cleanup')
    need(bootstrap['session']['process_exit_code'] == 0 and bootstrap['session']['exit_reason'] == 'process_exit' and bootstrap['session']['shutdown']['cleanup_proven'], 'normal game exit')
    need(bootstrap['recorder']['state'] == 'NORMAL_TREE_EMPTY' and bootstrap['sdk_thread_exited'] and bootstrap['sdk_error'] is None and bootstrap['supervisor_error'] is None, 'bootstrap cleanup')
    released = json.loads(release['stdout'])['task']
    need(release['normal_exit_zero'] and release['task_done_resources_empty'] and released['state'] == 'done' and released['resources'] == [] and released['last_sequence'] == 5923, 'release')
    preview = obj('results', 'preview/POSTPAIR-FACTS.actual-a01.json')
    need(preview['same_date_paused_actor_epoch_army_route_confirmed'] and preview['available_route']['route_with_origin'] == [2635,2645,2644], 'route')
    need(preview['county_actual']['target_province_id'] == 2645 and not preview['county_actual']['county_objects_differ'] and not preview['county_actual']['native_condition_passes'], 'first edge')
    need(all(s['call_count'] == 0 for s in preview['predicate_trace_actual']['stages']) and not preview['predicate_trace_actual']['neighbor_Q_observed'], 'predicate scope')
    need(not preview['target_supply_actual']['captured_target_land_supply_inputs_v1']['native_resupply_eligible'], 'rest target not qualified')
    analysis = obj('results', 'reader/ANALYSIS.actual.json')
    strict = obj('results', 'reader/STRICT-SOURCE-FACTS.actual.json')
    counts = {'0':1,'1':2,'2':1}
    need(analysis['total_raw_body_reads_by_day'] == strict['recovery']['total_raw_reads_by_day'] == counts, 'actual read correction')
    inner = zipfile.ZipFile(io.BytesIO(r.read('reader/R191-loss-three-endpoints.portable.zip')))
    need(inner.namelist() == ['loss-three-endpoint-witness.json'], 'witness members')
    witness = json.loads(inner.read(inner.namelist()[0]))
    endpoints = witness['endpoints']
    need(len(endpoints) == 3 and endpoints[0]['row'] is None and endpoints[0]['baseline_projection_only'], 'baseline DTO not held')
    keys = []
    for i, e in enumerate(endpoints):
        ph = e['physical']; slots = ph['physical_slots']
        key = {(s['persistent_regiment_id'],s['chunk_index']):s['maximum_soldiers'] for s in slots}; keys.append(key)
        need(len(slots) == len(key) == 21 and sum(s['current_soldiers'] for s in slots) == [1174,1174,1163][i] and sum(s['maximum_soldiers'] for s in slots) == 1185, 'physical slot arithmetic')
        need(ph['cached_current_max'] == [[1184,1195],[1184,1195],[1173,1195]][i] and ph['stock_raw'] == ph['capacity_raw'] == 30000000, 'cache/stock')
        need([a['army_regiment_id'] for a in ph['cached_regiments'] if a['empty_character_1_1_proved']] == [55,56,57,58,60,61,62,63,64,65], 'empty character roles')
        if i:
            for proof in e['value_projection_sources']:
                keyname = proof['json_pointer'].removeprefix('/army_strengths/0/')
                b = (json.dumps(e['row'][keyname],ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
                need(len(b) == proof['canonical_value_bytes'] and sha(b) == proof['canonical_value_sha256'], 'normalized value pin')
    need(keys[0] == keys[1] == keys[2], 'same physical cohort/maxima')
    actual = witness['intervals'][1]
    need(actual['writer_fence_coverage']['coverage_complete'] and actual['writer_fence_coverage']['before']['latest_sequence'] == 283 and actual['writer_fence_coverage']['after']['oldest_available_sequence'] == 2, 'interval retained despite old global overwrite')
    need(actual['positive_physical_writer_count'] == actual['same_callback_combined_stage_positive_count'] == actual['source_bound_siege_only_positive_count'] == 7 and actual['positive_physical_writer_debit_sum'] == 11 and actual['parent_unknown_reasons'] == [], 'strict positive')
    need(not actual['complete_interval_loss_total_claimed'] and not actual['R03_full_card_or_media_qualified'] and not actual['exact_event_PTS_claimed'], 'research boundary')
    events = strict['positive_writer_source_rows']
    need([e['strict_result']['sequence'] for e in events] == [478,479,480,492,494,495,497] and sum(e['strict_result']['actual_physical_soldier_debit'] for e in events) == 11, 'seven writer vector')
    for e in events:
        v = e['strict_result']; b = v['siege_budget_at_writer_v1']
        need(v['source_siege_only_budget_bound'] and v['callback_sequence'] == v['callback_invocation_token'] == 8 and b['original_supply_budget_soldiers'] == b['derived_original_raid_budget_soldiers'] == b['capture_failure_flags'] == 0 and b['original_siege_budget_soldiers'] == b['combined_siege_raid_budget_soldiers'] == 11 and b['siege_raid_capture_complete'], 'source-bound siege budget')
    need(strict['callback']['passed_date_raw64'] & 0xffffffff == 53148192, 'callback date low32')
    replay = False
    if repo:
        for pin in witness['consumer_source_pins']:
            b = (Path(repo)/pin['repo_relative_path']).read_bytes()
            need(len(b) == pin['bytes'] and sha(b) == pin['sha256'], 'production source changed: '+pin['repo_relative_path'])
        namespace = {'__name__':'r191_offline_reader','__file__':str(Path(__file__).resolve())}
        exec(compile(r.read('reader/loss_endpoints.py'),'exact-r191-offline-reader','exec'), namespace)
        api = namespace['production'](repo)
        for e in endpoints[1:]:
            need(namespace['physical_snapshot'](e['row'],api) == e['physical'], 'production physical replay')
        for i, (before, after) in enumerate(zip(endpoints,endpoints[1:])):
            interval, math = namespace['compare_interval'](before,after,witness,api)
            need(interval == witness['intervals'][i] and math == witness['production_math'][i], 'production strict replay')
        replay = True
    ledger = [json.loads(x) for x in gzip.decompress(p.read('storage/ITEMS.actual-a01.jsonl.gz')).splitlines()]
    need(len(ledger) == 1000 and all(x['status'] == 'deleted_unavailable' and not x['exists_after'] for x in ledger), 'deleted originals availability')
    need(sum(x['a'] for x in ledger) == 372740096 and sum(x['b'] for x in ledger) == 370675161, 'allocation/logical cleanup')
    daily = obj('provenance','storage/daily-validation-a01/DAILY-VALIDATION.actual-a01.json')
    need(daily['asset_groups'] == 157 and daily['actual_deletions'] == 0 and not facts['cleanup']['automatic_GC'], 'daily is manual zero delete')
    need(facts['future_R09']['state'] == 'PLAN_ONLY_NO_RUN_ALLOCATED' and not facts['qualification']['whole_R03_card'] and not facts['qualification']['human_signoff'], 'remaining gaps')
    return {'status':'PASS','machine_id':machine,'exact_original_members':count,'endpoint_count':3,'interval_count':2,'production_strict_replayed':replay,'source_bound_siege_positive_events':7,'source_bound_physical_debit_sum':11,'raw_body_read_by_this_verifier':0,'large_originals_reopened':0,'whole_R03_card':False,'full1x_or_human_signoff':False}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path)
    parser.add_argument('--repo',type=Path)
    a=parser.parse_args()
    print(json.dumps(verify(a.package,a.repo),ensure_ascii=False))
