from pathlib import Path
import argparse
import hashlib
import json

def verify(package):
    manifest = json.loads((package / 'manifest.json').read_bytes())
    seen = set()
    for row in manifest['files']:
        relative = Path(row['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        assert row['path'] not in seen
        seen.add(row['path'])
        raw = (package / relative).read_bytes()
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    source = json.loads((package / 'source-index.json').read_bytes())
    assert len(source['files']) == 10
    assert all(row['path'] in seen for row in source['files'])
    result = json.loads((package / 'arithmetic-result.json').read_bytes())
    assert result['source_files'] == source['files']
    assert result['arithmetic']['preclamp_raw'] == 11306109
    assert result['arithmetic']['expected_post_stock_raw'] == result['observed_post_stock_raw'] == result['observed_post_capacity_raw'] == 10000000
    assert result['upper_cap_observed_this_window'] is True
    assert result['cohort']['frozen_27_regiment_gate_pass'] is False
    assert result['commander']['frozen_destination_commander_gate_pass'] is False
    assert all(result[key] is None for key in ('cause_of_new_regiment_or_commander_change','Root_formal_B_terminal','B_London','C_terminal','winner'))
    overlay = json.loads((package / 'terminal-overlay.json').read_bytes())
    for row in overlay['sources']:
        raw = (package / row['path']).read_bytes()
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    terminal = overlay['Root_formal_B_terminal']
    assert terminal['status'] == 'STOPPED_GATE_INCOMPLETE'
    assert terminal['actual_days_used'] == 38 and terminal['remaining_actual_days'] == 52
    assert terminal['date_raw'] == result['date_raw'] == 53149344
    assert terminal['deadline_reached'] is False and terminal['arrival_comparable'] is False
    assert terminal['London_endpoint_metrics'] is None and terminal['winner'] is None
    assert overlay['new_TTS_requests'] == 0 and overlay['this_candidate_pixel_or_media_reads'] == 0
    return {'status':'PASS_EXACT_FROZEN_PACKAGE_RELATIVE_INPUTS', 'files':len(seen),
            'sources':10, 'upper_cap_window_matches':True, 'frozen_B_gates_pass':False,
            'TTS_media_SDK_GUI_Game_Git_calls':0, 'human_signoff':False}

def main():
    parser = argparse.ArgumentParser(description='Verify the pinned B merge research package with the Python standard library.')
    parser.add_argument('--package',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = verify(args.package)
    with args.output.open('xb') as stream:
        stream.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(result,ensure_ascii=False))

if __name__ == '__main__':
    main()
