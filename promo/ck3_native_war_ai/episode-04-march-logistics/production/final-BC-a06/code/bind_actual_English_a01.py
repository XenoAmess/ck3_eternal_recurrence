"""Actual seven English rows bound to real PCM, without provider/media calls."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import subprocess
import sys
CROOT=Path('C:/ck3-war-episode04-research-20261004-a01')
LAUNCH=CROOT/'e04-final-BC-English-bind-launch-a01';LAUNCH.mkdir(exist_ok=False)
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):
    with path.open('xb') as stream:stream.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
audio=CROOT/'e04-final-BC-audio-production-a01/AUDIO-READY.json'
English=CROOT/'e04-final-BC-subtitle-production-a01/English-diff-final-BC-a01.json'
assert pin(audio)['sha256']=='c258bf2d9906ec1c1bb9256fadc19b5b4fceaa05f922879602e6420b82b0dd41'
assert pin(English)['bytes']==7093 and pin(English)['sha256']=='b2243b8d3cd8d843f416b080f4ed96de15ade494a06e9fcd78aafefc643be944'
write(LAUNCH/'audio-delivery-pin.json',pin(audio));write(LAUNCH/'English-diff-pin.json',pin(English))
producer=CROOT/'e04-final-BC-audio-preparation-a01/final_BC_audio.py'
assert pin(producer)['sha256']=='80d35f1bc1bc08172aba4d66d6933813f063379a48445d84bd2a6f5a98e5173c'
output=CROOT/'e04-final-BC-audio-English-binding-a01'
argv=[sys.executable,'-I','-S','-B','-X','utf8',str(producer),'bind-english',
 '--request',str(CROOT/'e04-final-BC-audio-launch-a01/audio-actual-final-request.json'),
 '--audio-delivery-pin',str(LAUNCH/'audio-delivery-pin.json'),'--English-diff-pin',str(LAUNCH/'English-diff-pin.json'),
 '--output-dir',str(output),'--execute']
write(LAUNCH/'argv.json',argv)
result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
for name,raw in [('stdout.json',result.stdout),('stderr.txt',result.stderr)]:
    with (LAUNCH/name).open('xb') as stream:stream.write(raw)
write(LAUNCH/'RESULT.json',{'finished_utc':datetime.now(timezone.utc).isoformat(),'returncode':result.returncode,
 'argv':pin(LAUNCH/'argv.json'),'stdout':pin(LAUNCH/'stdout.json'),'stderr':pin(LAUNCH/'stderr.txt'),
 'audio_before':pin(audio),'English_diff':pin(English),'source_body_and_ledger_exact':True,
 'new_TTS_provider_calls':0,'new_PCM_WAVs':0,'actual_delivery':pin(output/'ROOT-DELIVERY.json') if (output/'ROOT-DELIVERY.json').is_file() else None,
 'human_listening_or_film_signoff':False})
print(json.dumps({'returncode':result.returncode,'launch_receipt':pin(LAUNCH/'RESULT.json'),
 'delivery':pin(output/'ROOT-DELIVERY.json') if (output/'ROOT-DELIVERY.json').is_file() else None}))
raise SystemExit(result.returncode)
