"""Authorized actual seven-paragraph TTS after exact Root NO_BLOCK."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

CROOT=Path('C:/ck3-war-episode04-research-20261004-a01')
STORY=CROOT/'e04-final-BC-story-a01/actual-story-a02'
PREP=CROOT/'e04-final-BC-audio-preparation-a01'
LAUNCH=CROOT/'e04-final-BC-audio-launch-a01';LAUNCH.mkdir(exist_ok=False)
PROD=CROOT/'e04-final-BC-audio-production-a01'
ROOT_REVIEW=CROOT/'e04-final-BC-Root-actual-source-review-a01/Root-NO-BLOCK.json'
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):
    raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with path.open('xb') as stream:stream.write(raw)
assert pin(ROOT_REVIEW)['bytes']==15648 and pin(ROOT_REVIEW)['sha256']=='5874bd3c5cc0557a61a47a66fb3788841ed1dd78c00eb02ebe6323cc6902428f'
review=json.loads(ROOT_REVIEW.read_bytes())
assert review['source_review_status']=='NO_BLOCK' and review['final_freeze'] is True
assert review['chinese_body_sha256']=='ce0c45dccc3ae5a2a7ce60f4f7a4c3025487c3b58daa2c561e5a7d97dfb7bcce'
assert review['chinese_ledger_sha256']=='2ef65357de29c0d4245886cb06dd5a0454089849b15623f7fcbf47666e1b83c9'
assert review['changed_paragraph_ids']==['C05-04','C05-05','C05-08','C05-10','C05-14','C05-16','C06-10']
write(LAUNCH/'Root-NO-BLOCK-exact-snapshot.json',ROOT_REVIEW.read_bytes())
oral=json.loads((STORY/'oral-final-request-PENDING-ROOT-REVIEW.json').read_bytes())
oral['future']['source_review']=pin(LAUNCH/'Root-NO-BLOCK-exact-snapshot.json')
oral_path=LAUNCH/'oral-actual-final-request.json';write(oral_path,oral)
write(LAUNCH/'oral-actual-final-pin.json',pin(oral_path))
tool=PREP/'final_BC_audio.py'
assert pin(tool)['sha256']=='80d35f1bc1bc08172aba4d66d6933813f063379a48445d84bd2a6f5a98e5173c'
spec=importlib.util.spec_from_file_location('pinned_final_BC_audio_producer',tool)
producer=importlib.util.module_from_spec(spec);spec.loader.exec_module(producer)
audio_request=LAUNCH/'audio-actual-final-request.json'
prepared=producer.prepare_final_request(PREP/'audio-request-current-TEMPLATE.json',pin(oral_path),audio_request)
write(LAUNCH/'prepare-final-request-receipt.json',prepared)
argv=[sys.executable,'-I','-B','-X','utf8',str(tool),'generate','--request',str(audio_request),
      '--output-dir',str(PROD),'--execute']
write(LAUNCH/'generate.argv.json',argv)
write(LAUNCH/'launch-input-pins.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
 'producer':pin(tool),'Root_source_review':pin(ROOT_REVIEW),'oral_request':pin(oral_path),'audio_request':pin(audio_request),
 'actual_production_dir':str(PROD),'workers':4,'only_actual_seven_voice_changes':True,
 'English_not_a_TTS_gate':True,'human_listening_or_film_signoff':False})
started=datetime.now(timezone.utc).isoformat()
with (LAUNCH/'generate.stdout.txt').open('xb') as stdout,(LAUNCH/'generate.stderr.txt').open('xb') as stderr:
    child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,shell=False)
    write(LAUNCH/'started.json',{'started_utc':started,'actual_own_child_pid':child.pid,'argv':argv})
    print(json.dumps({'event':'ACTUAL_FINAL_BC_SEVEN_TTS_STARTED','own_child_pid':child.pid,'workers':4,'production':str(PROD)}),flush=True)
    sent=False
    while child.poll() is None:
        ready=PROD/'AUDIO-READY.json'
        if not sent and ready.is_file():
            try:
                ready_value=json.loads(ready.read_bytes())
                print(json.dumps({'event':'ACTUAL_AUDIO_READY_BEFORE_NATIVE_ARCHIVE','delivery':pin(ready),
                    'actual_PCM':ready_value['actual_PCM'],'voice_changed_ids':ready_value['voice_changed_ids']}),flush=True)
                sent=True
            except json.JSONDecodeError:pass
        time.sleep(.25)
    code=child.wait()
result={'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'exit_code':code,
 'argv':pin(LAUNCH/'generate.argv.json'),'stdout':pin(LAUNCH/'generate.stdout.txt'),'stderr':pin(LAUNCH/'generate.stderr.txt'),
 'AUDIO_READY':pin(PROD/'AUDIO-READY.json') if (PROD/'AUDIO-READY.json').is_file() else None,
 'actual_delivery':pin(PROD/'ROOT-DELIVERY.json') if (PROD/'ROOT-DELIVERY.json').is_file() else None,
 'all_attempts_and_partial_preserved':True,'human_signoff':False}
write(LAUNCH/'RESULT.json',result)
print(json.dumps({'event':'ACTUAL_FINAL_BC_TTS_PROCESS_TERMINAL','result':pin(LAUNCH/'RESULT.json'),**result}),flush=True)
raise SystemExit(code)
