from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02')
preflight=json.loads((LIVE/'ck3-output/preflight.json').read_text(encoding='utf-8'))
profile=json.loads((ROOT/'operator-profile-a01.json').read_text(encoding='utf-8'))
def ident(path):
    p=Path(path).resolve();return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
print(json.dumps({'preflight_keys':list(preflight),'bridge_dll':preflight.get('bridge_dll'),
                 'bridge_injector':preflight.get('bridge_injector'),'checkpoint_source':preflight.get('checkpoint_source')},ensure_ascii=False))
text=(ROOT/'knight_saved_pair.py').read_text(encoding='utf-8')
new_binding='''def bind_current_research_session():
    source=FROZEN
    original=json.loads((OUTPUT/'preflight.json').read_text(encoding='utf-8'))
    observed=json.loads((OUTPUT/'native-start-readback.json').read_text(encoding='utf-8'))
    live_id=json.loads((OUTPUT/'live-run-identity.json').read_text(encoding='utf-8'))
    pins=[]
    for path,expected in [
      (source.parent/'build-attempt-01/build/xar_ck3_bridge.dll','ED537BEF5EE53271F0563A7FBAA0DC8BA572F37A6F859EE73F12C292D3E73A23'),
      (source.parent/'build-attempt-01/build/xar_ck3_bridge_injector.exe','091CECEF5617251085A3CACE07213B63BD391B40444C9F5E918B61C286D4E88F'),
      (source/'promo/ck3_native_war_ai/integration/capture_session.py','49162E48007028E9AE3D61CBAA194F014A978DD038A6514F2280A322159FFAE7'),
      (Path('D:/workspace/ck3_native_war_ai_promo_work/episode01-paired-counter-trace-attempt-010/d26-immutable.ck3'),'C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B')]:
        pin=identity(path)
        require(pin['sha256']==expected,'Current research pin changed: '+str(path))
        pins.append(pin)
    require(original['bridge_dll']['sha256'].upper()==pins[0]['sha256'] and original['bridge_injector']['sha256'].upper()==pins[1]['sha256'],
            'Current preflight DLL/injector differ from declared research source pair')
    require(original['checkpoint_source']['save']['sha256'].upper()==pins[3]['sha256'] and original['checkpoint_source']['date_raw']==53146848 and
            original['checkpoint_source']['actor']==29829,'Research checkpoint identity mismatch')
    require(len(live_id['identities'])==1 and live_id['identities'][0]['run_id']=='desktop-3fevhd2-1c74096080--vanilla--R0139',
            'This research consumer only binds this newly created run')
    return {'schema':'ck3.e2.current-research-source-binding/v1','purpose':'current source research; not old frozen film replay contract',
            'source_head':'1901473429deb1297be7d5d4451169082629858b','declared_pins':pins,'preflight':identity(OUTPUT/'preflight.json'),
            'readback':identity(OUTPUT/'native-start-readback.json'),'live_identity':live_id,
            'old_frozen_replay_contract_unchanged':True,'observed_readback':observed}

'''
text=text.replace('def main():',new_binding+'def main():').replace("step.bind_session(OUTPUT,'e2-05-d26')",'bind_current_research_session()')
text=text.replace("NEW/'evidence'","NEW/'research-pair-attempt-02'")
with (ROOT/'knight_research_pair_a02.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
record={'reason':'Historical film controller pins EB643 DLL; current research explicitly pins ED537 source190 pair and current R0139. No historical guard or source is modified.',
        'previous_consumer':ident(ROOT/'knight_saved_pair.py'),'current_consumer':ident(ROOT/'knight_research_pair_a02.py'),
        'changes':['new explicit current source/replay binding','new research-only evidence workdir'],'preflight':ident(LIVE/'ck3-output/preflight.json')}
with (ROOT/'current-research-consumer-delta.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
