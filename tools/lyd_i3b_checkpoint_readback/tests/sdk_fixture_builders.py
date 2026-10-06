"""Only four pinned inert DTO builder bodies; no old tests or drivers executed."""
import confucian_dto_primitives as query

def frame():
    return {'revision':3,'native_revision':7,'snapshot_id':'native:7','date_raw':53144712,
        'paused':True,'speed':0,'map_ready':True,'episode_run_id':'synthetic-only-fixture',
        'played_character':{'character_id':31254,'alive':True},
        'active_event':None,'pending_character_interaction':None,'one_life_terminal_reason':None,
        'diagnostics':{'connected':True,'connection_generation':2,
            'hello':{'pid':991,'ck3_build_match':True,'game_adapter_id':'ck3-1.20.0.3-msvc-x64',
                'expected_ck3_version':'1.20.0.3','expected_ck3_sha256':query.CK3_12003.executable_sha256}}}


def assembly(binding):
    def member(identity):
        return {'character_id':identity,'rite_id':169,'faith_id':107,'alive':True,'adult':True,
            'imprisoned':False,'incapable':False,'is_ai':identity!=31254,'effective_learning':24,
            'adult_measure_raw':20,'adult_selector_raw':0,'adult_threshold_raw':16,
            'complete':True,'unavailable_reason':None}
    actor=binding['played_character_id']&0xFFFFFFFF
    ids=sorted({actor,0x80000002})
    return {'schema':query.OPERATIONS['assembly_predicates'][4],'read_only':True,'game_version':'1.20.0.3',
        'executable_sha256':query.CK3_12003.executable_sha256,'available':True,'predicates_complete':True,
        'unavailable_reason':None,'capture_epoch':42,'date_raw':binding['date_raw'],
        'played_character_id':actor if actor<2**31 else actor-2**32,
        'faith_id':107,'played_rite_id':169,'religion_id':4,'alive_source_pool_count':200,
        'religion_county_source_pool_count':100,'complete_native_faith_member_ids':ids,
        'complete_native_faith_rite_ids':[169,170],'members':[member(identity)for identity in ids],
        'rites':[{'rite_id':169,'county_title_ids':[0xF1000001],'native_county_count':1,
            'complete':True,'unavailable_reason':None},{'rite_id':170,'county_title_ids':[],
            'native_county_count':0,'complete':True,'unavailable_reason':None}]}


def title(binding):
    return {'schema':query.OPERATIONS['religious_title'][4],'game_version':'1.20.0.3',
        'executable_sha256':query.CK3_12003.executable_sha256,'available':True,'unavailable_reason':None,
        'capture_epoch':43,'date_raw':binding['date_raw'],'played_character_id':binding['played_character_id'],
        'played_character_full_id':binding['played_character_id']&0xFFFFFFFF,'graph_available':True,
        'graph_unavailable_reason':None,'legal_head_title_absent':False,'faith_full_id':107,
        'head_title_full_id':0xF1000001,'native_title_holder_full_id':0x80000002,
        'native_title_holder_absent':False,'native_title_class':'CLandedTitle',
        'title_holder':{'available':False,'unavailable_reason':'legacy_signed_title_id_boundary',
            'title_tier_raw':None,'title_tier_key':None,'holder_character_full_id':None,
            'holder_is_player':None,'holder_in_player_realm':None,
            'holder_immediate_liege_character_full_id':None,'holder_top_liege_character_full_id':None},
        'title_properties':{'available':True,'unavailable_reason':None,'destroy_if_invalid_heir':True,
            'no_automatic_claims':True,'definitive_form':True,'always_follows_primary_heir':True},
        'title_laws':{'available':True,'unavailable_reason':None,'native_count':2,
            'complete_laws':[{'native_definition_id':23,'key':'other_real_law'},
                {'native_definition_id':24,'key':'temporal_head_of_faith_succession_law'}],
            'expected_law_key':'temporal_head_of_faith_succession_law',
            'temporal_head_of_faith_succession_law_member':True},
        'mod_owned_marker':None,'mod_owner_faith_variable':None,
        'qualification':{'kind':'exact_current_static_abi',
            'title_properties_index_sha256':'14bf997b58a8ff33d7407ece6be2675917a2b7ed7e6ffdba70ca8ea938347a0a',
            'title_laws_index_sha256':'9d371bf97f50281c621d777890915d6767c354275222fa38d7e1127076afeb60',
            'head_getters_index_sha256':'d93f24e7be97fc7a59c35b76313e9b7a10f8d97dcb7534015b504373aa2dd973',
            'faith_reference_identity_offset':8,'title_full_id_offset':16,
            'faith_typed_fallback_slot_rva':'0x5D1E2E0','runtime_acceptance':None}}


def envelope(operation,binding,payload=None):
    step,domain,backend,nested,_=query.OPERATIONS[operation]
    payload=payload if payload is not None else (assembly if operation=='assembly_predicates'else title)(binding)
    return {'step':step,'accepted':True,'status':'observed'if payload['available']else'unavailable',
        'private_build':True,'read_only':True,'advertised':False,'game_version':'1.20.0.3',
        'executable_sha256':query.CK3_12003.executable_sha256,'domain_key':domain,'backend_id':backend,
        'snapshot_revision':binding['native_revision'],'date_raw':binding['date_raw'],nested:payload}
