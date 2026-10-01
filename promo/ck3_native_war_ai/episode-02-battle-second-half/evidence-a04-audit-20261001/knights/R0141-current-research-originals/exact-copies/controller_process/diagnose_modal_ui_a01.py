"""Preserve actual unavailable UI return and paused original pixels without retrying action."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent

def main():
    helper = ROOT / 'scoped_ui_research_a08.py'
    spec = importlib.util.spec_from_file_location('_actual_ui_diagnostic',helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.require(module.identity(helper)['sha256'] == '169EE7EA1DBF979B3EBE0C6221A4287B908E4F0F7BFA01A14DB86AC5D671F640','Controller changed')
    bindings = ROOT / 'current-run-bindings.json'
    config = module.read(bindings)
    live,output,evidence,transport,steps = module.bind(config)
    before,br,values = module.snapshot(output,transport,steps,'modal-rejection-before-pixels',config['before_date_raw'])
    image = module.capture_window(live,evidence,'modal-rejection-diagnostic')
    after,ar,av = module.snapshot(output,transport,steps,'modal-rejection-after-pixels',config['before_date_raw'])
    module.require(values == av,'Paused source changed while reading diagnostic pixels')
    originals = []
    for path in sorted((live / 'ck3-state/native-session/ingame-ui-native-results').glob('*.json')):
        body = module.read(path)
        original = body['original_parsed_command_result']
        originals.append({'identity':module.identity(path),'request':body['request'],
                          'original_parsed_command_result':original})
    module.write(evidence / 'modal-rejection-diagnostic.json',{
        'binding':module.identity(bindings),'original_parsed_frames':originals,
        'before_snapshot':br,'before_values':values,'image':image,
        'after_snapshot':ar,'after_values':av,'day_advance_count':0,
        'action_retried':False,'gameplay_written':False,'human_movie_signoff':False})
    print(json.dumps({'image':image,'original_parsed_frames':originals},ensure_ascii=False))

if __name__ == '__main__':
    main()
