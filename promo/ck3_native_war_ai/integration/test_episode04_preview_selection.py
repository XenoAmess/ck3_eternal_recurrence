"""Focused selector tests; synthetic catalog, no native run or media execution."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import pytest
from xar_promo.model import ProjectConfig

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.cwd()/'promo/ck3_native_war_ai/integration/src'))

@pytest.fixture
def prepared(tmp_path,monkeypatch):
    local=Path(__file__).with_name('episode04_review02_preview_rough.py')
    if local.exists():
        spec=importlib.util.spec_from_file_location('preview_subject',local)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    else:
        from war_ai_promo import episode04_review02_mixed_rough as m
    ids=['C02-09','C03-08']+[f'UNSELECTED-{i:02}'for i in range(67)]
    rows=[];method=[];config_cues=[];overrides={};records=[];catalog={}
    position=0
    for i,key in enumerate(ids):
        frames=878 if i==0 else 846
        audio={'path':str(tmp_path/(key+'.mp3')),'bytes':0,'sha256':'0'*64}
        rows.append({'id':key,'zh':key+'-zh','en':key+'-en','audio':audio,'audio_artifact_id':'audio.'+key,'duration_seconds':frames/30})
        method.append({'id':key,'start_frame':position,'end_frame_exclusive':position+frames,'subtitle':{'path':key+'.ass','bytes':1,'sha256':'0'*64}})
        position+=frames
        config_cues.append({'id':key,'narration':{'zh-CN':key+'-zh'},'subtitles':{'zh-CN':key+'-zh','en':key+'-en'}})
        if i<2:
            first=i*2000
            source={'path':str(tmp_path/'shared.mkv'),'bytes':0,'sha256':'0'*64,'artifact_id':'raw.fixture'}
            overrides[key]={'role':'rough-context-only','continuous_clean':False,'event_PTS':None,'approval':'pending','source':source,'source_frames':[first,first+frames],'source_frame_count':10000}
            records.append(NS(artifact_id='audio.'+key,bytes=0,sha256='0'*64))
            catalog['audio.'+key]=Path(audio['path'])
            subtitle=tmp_path/(key+'.ass');subtitle.write_text('fixture subtitle',encoding='utf-8')
            records.append(NS(artifact_id='source-subtitle.'+key,bytes=1,sha256='0'*64))
            catalog['source-subtitle.'+key]=subtitle
    assert position==58406
    records.append(NS(artifact_id='raw.fixture',bytes=0,sha256='0'*64));catalog['raw.fixture']=tmp_path/'shared.mkv'
    data={'schema':'xar.e04.rough-review-inputs.v1','review_only':True,'human_signoff':False,'render_geometry':[1920,1080],'repo_root':str(tmp_path),'metadata':{'measured':'measured','method':'method','raster':{'path':str(tmp_path/'raster.json')}},'pending_cues':ids[2:],'visual_overrides':overrides,'preview_cue_ids':ids[:2]}
    metadata={'measured':{'cues':rows},'method':{'cues':method}}
    def read_metadata(ref,*args):return {'cards':[]}if isinstance(ref,dict)else metadata[ref]
    def artifact(run,run_path,key):
        if key=='production-inputs-v1':return tmp_path/'inputs.json'
        return catalog[key]
    monkeypatch.setattr(m,'load',lambda path:data)
    monkeypatch.setattr(m,'metadata',read_metadata)
    monkeypatch.setattr(m,'artifact',artifact)
    config=ProjectConfig.from_mapping({'format_version':1,'kind':'xar_promo_project_config','project':{'id':'preview-fixture','title':'Selector unit fixture'},'pipeline':{'adapter':'fixture-adapter','preset':'fixture-preset'},'locales':{'narration':'zh-CN','subtitles':['zh-CN','en']},'constraints':{'duration_limit_seconds':2400},'chapters':[{'id':'fixture','type':'documentary','state':'planned','title':{'zh-CN':'Fixture'},'artifact_ids':[],'cues':config_cues}]})
    run=NS(artifacts=records)
    def compose(validate_only=False):
        return m.compose(config,run,config_path=None,run_path=None,workdir=tmp_path/'NO_CREATE',adapter_factory=lambda:{'id':config.adapter},preset_factory=lambda:{'id':config.preset},validate_only=validate_only)
    return data,compose,tmp_path

def test_preview_uses_only_selected_preserved_inputs_and_labels(prepared):
    data,compose,tmp_path=prepared
    # The fixture deliberately has no catalog entries for 67 unselected voices.
    invocation=compose()
    assert [s.segment_id for s in invocation.draft.segments]==['C02-09','C03-08']
    assert [s.start_seconds for s in invocation.draft.segments]==[0,2000/30]
    assert 'PARTIAL-ROUGH-PREVIEW-NO-SIGNOFF' in str(invocation.draft.deliverable_relative_path)
    assert 'partial-rough-preview-no-signoff' in invocation.draft.deliverable_artifact_id
    body=invocation.dependencies.subtitle_renderer(invocation.draft.segments[0],None,workdir=tmp_path)
    assert 'PARTIAL PREVIEW / NO SIGNOFF' in body
    assert data['human_signoff'] is False
    assert not (tmp_path/'NO_CREATE').exists()

def test_pending_cannot_enter_preview(prepared):
    data,compose,_=prepared;data['preview_cue_ids']=['C02-09','UNSELECTED-00']
    with pytest.raises(ValueError,match='pending cue cannot enter preview'):compose()

def test_full69_default_stays_strict(prepared):
    data,compose,_=prepared;data.pop('preview_cue_ids')
    with pytest.raises(ValueError,match='key footage is pending; no static fallback allowed'):compose()

@pytest.mark.parametrize('selection,message',[
    (['C03-08','C02-09'],'preview cue order must match frozen69'),
    (['UNKNOWN'],'unknown preview cue'),
    (['C02-09','C02-09'],'duplicate preview cue'),
])
def test_invalid_selection_rejected(prepared,selection,message):
    data,compose,_=prepared;data['preview_cue_ids']=selection
    with pytest.raises(ValueError,match=message):compose()

def test_preview_rejects_source_card_without_actual_override(prepared):
    data,compose,_=prepared;data['pending_cues'].remove('UNSELECTED-00');data['preview_cue_ids']=['UNSELECTED-00']
    with pytest.raises(ValueError,match='preview requires actual rough inputs'):compose()
