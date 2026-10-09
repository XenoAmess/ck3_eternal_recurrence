"""Original native administrative/meritocratic appointment GUI cells."""
from . import xqol_followup_common as common
from ck3_mod_acceptance_prepare import pin
import hashlib
import math
import re

require=common.require
validate_contract=common.validate_contract
verify_case=common.verify_case


def prepare_case(context):
    return common.prepare_case(context,song=False)


def actual_scope(raw,contract):
    """Bind the original post-switch current/saved dump, never its old Robert ROOT."""
    common.observe(raw,contract['required_markers'],contract['forbidden_markers'])
    text=raw.decode('utf-8-sig',errors='replace')
    start=text.index(contract['required_markers'][1]);end=text.index(contract['required_markers'][2],start)
    block=text[start:end]
    current=re.search(r'(?m)^\[\d{2}:\d{2}:\d{2}\]\[D\]\[effectimpl\.cpp:\d+\]: [^\r\n]*?\(Internal ID: ([1-9][0-9]*)(?: - Historical ID [^)]*)?\)',block)
    saved=list(re.finditer(r'(?m)^zqagov_actual_player: [^\r\n]*?\(Internal ID: ([1-9][0-9]*)(?: - Historical ID [^)]*)?\)',block))
    require(current is not None and saved and current.end()<block.index('Saved event targets:')<saved[0].start(),
            'Original post-switch current/saved government actor format unavailable')
    actor=int(current[1])
    require(1<=actor<=2**31-1 and {int(row[1]) for row in saved}=={actor},
            'Original government current/saved fullIDs differ')
    return {'runtime_character_id':actor,'raw_block_sha256':hashlib.sha256(block.encode('utf-8')).hexdigest(),
            'raw_block':block,'old_ROOT_not_used':True}


def verify_slots(slots,contract,actor):
    require(isinstance(slots,list) and len(slots)==len(contract['appointment_laws']), 'All original government appointment blocks required')
    seen=[]
    for slot,law in zip(slots,contract['appointment_laws']):
        title=slot.get('title_id')
        require(type(title) is int and title>0 and title not in seen and slot.get('law')==law,
                'Actual distinct government title/law missing')
        seen.append(title)
        require(slot.get('direct_original_review') is True and slot.get('full_candidates_reviewed') is True and
                slot.get('eligibility_and_score_breakdown_reviewed') is True, 'Original complete candidate/tooltip review missing')
        candidates=slot.get('candidates')
        require(isinstance(candidates,list) and candidates and all(type(x.get('character_id')) is int and x['character_id']>0 and
                type(x.get('eligible')) is bool and type(x.get('is_ai')) is bool for x in candidates),
                'Original actual complete candidate rows missing')
        require(len({x['character_id'] for x in candidates})==len(candidates), 'Actual candidate duplicated')
        require(any(x['character_id']==actor and x['eligible'] is True and x['is_ai'] is False for x in candidates) and
                slot.get('independent_human_candidate') is True, 'Original human must naturally be an eligible candidate')
        off,on,restored=slot.get('score_off'),slot.get('score_on'),slot.get('score_restored')
        require(all(type(v) in (int,float) and math.isfinite(v) for v in (off,on,restored)) and on==off-1000000 and restored==off,
                'Original exact million penalty/off restoration failed')
        require(slot.get('auto_appointment_enabled_off') is False and slot.get('auto_appointment_enabled_on') is True and
                slot.get('auto_appointment_enabled_restored_score') is False, 'Original actual off/on/off toggle readback missing')
        require(type(slot.get('original_switch_enabled')) is bool and slot.get('original_switch_restored') is True and
                slot.get('final_switch_enabled')==slot['original_switch_enabled'], 'Original appointment switch not restored')
        chosen=slot.get('chosen_character_id')
        require(chosen in [x['character_id'] for x in candidates if x['eligible'] is True and x['is_ai'] is True] and
                slot.get('actual_successor_character_id')==chosen and slot.get('native_appointment_confirmed') is True,
                'Original actual eligible AI appointment/successor missing')
    return True


def run_case(context,client):
    c=context['case_contract'];result=common.run_plan(context,client);frame=result['after']
    root=client.execute_plan([{'id':'qolf-government-root','tool':'ck3_query_campaign_root_context_v1',
        'args':{},'fresh_revision':True}],'qolf-government-root')[0]
    observed=root['result'].get('campaign_root_context',{})
    actor=frame['played_character']['character_id']
    proof=actual_scope(client.log_bytes(),c)
    require(proof['runtime_character_id']==actor, 'Actual native player differs from the original target holder scope')
    require(root['result'].get('campaign_root_context_ready') is True and observed.get('player_character_id')==actor and
            observed.get('date_raw')==frame['date_raw'] and observed.get('government',{}).get('key')==c['post_start']['government_key'] and
            observed.get('independent') is True, 'Actual government/actor/independence differs from original cell')
    response=client.root_checkpoint('qol-original-government-appointment',{
        'case':context['case'],'actual_actor_character_id':actor,'actual_frame':frame,
        'appointment_laws':c['appointment_laws'],'original_million_penalty':1000000,
        'requirements':['actual matching native law and complete candidates/eligibility/score tooltip',
          'independent human naturally in candidate pool; exact off/on/off million scores and original switch restore',
          'actual eligible AI chosen and actual successor/appointment confirmed',
          'fresh original images plus mapped input receipts when coordinates used; no guessed title/character IDs'],
        'required_response':{'completed':True,'current_scene_reviewed':True,'slots':[],'evidence':[]}})
    require(response.get('completed') is True and response.get('current_scene_reviewed') is True,
            'Original government GUI block incomplete/GAP')
    verify_slots(response.get('slots'),c,actor)
    evidence=response.get('evidence',[])
    require(evidence and all(pin(row['path'])==row for row in evidence),'Actual government original GUI evidence missing')
    after=client.snapshot()
    require(after['date_raw']==frame['date_raw'] and after['played_character']['character_id']==actor,
            'Original government GUI crossed paused date/actor')
    holders=[]
    for n,slot in enumerate(response['slots'],1):
        phase='qolf-actual-governor-holder-'+str(n)
        row=client.execute_plan([{'id':phase,'tool':'ck3_query_title_holder_v1','args':{'title_id':slot['title_id']},
                                 'fresh_revision':True}],phase)[0]
        holder=row['result'].get('title_holder',{})
        require(holder.get('available') is True and holder.get('status')=='available' and holder.get('title_id')==slot['title_id'] and
                holder.get('actor_character_id')==actor and holder.get('date_raw')==after['date_raw'],
                'Actual government title holder unavailable/crossed scene')
        if 'actual_holder_character_id' in slot: require(holder.get('holder_character_id')==slot['actual_holder_character_id'],
                                                       'Actual holder GUI/native readback differs')
        client.validate_frame(row['after_snapshot']);holders.append(row)
    result.update(government_root=root,actual_government_scope=proof,gui_slots=response['slots'],gui_evidence=evidence,actual_holder_rows=holders,
                  root_checkpoint_response=response)
    return common.preserve_result(context,client,result)
