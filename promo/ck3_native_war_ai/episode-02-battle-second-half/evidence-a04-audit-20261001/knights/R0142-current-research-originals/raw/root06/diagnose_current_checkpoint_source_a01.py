from pathlib import Path
import importlib.util
import json
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_checkpoint_source_diag',ROOT/'scoped_ui_research_a08.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cfg=m.read(ROOT/'current-run-bindings.json');live,out,evidence,transport,steps=m.bind(cfg)
body,receipt,values=m.snapshot(out,transport,steps,'checkpoint-source-diagnostic-readonly',cfg['before_date_raw'])
pair=m.read(evidence/'before-saved-pair.json');prior=m.read(out/'interactive-requests/scoped-chain-begin.json')
diff={key:{'before_main_save_source':pair['source_values'].get(key),'current':value} for key,value in values.items() if pair['source_values'].get(key)!=value}
report={'values':values,'differences':diff,'prior_rejected_begin_expected_revision':prior['expected_revision'],
        'current_checkpoint_sequence':pair['save_body']['submission']['sequence'],'receipt':receipt,'day_intent_exists':(evidence/'one-day-intent.json').exists()}
m.write(evidence/'checkpoint-source-diagnostic-readonly.json',report)
print(json.dumps(report,ensure_ascii=False))
