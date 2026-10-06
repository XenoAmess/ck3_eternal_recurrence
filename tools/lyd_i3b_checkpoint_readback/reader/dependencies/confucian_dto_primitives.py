"""Exact pure normalization bodies projected from pinned actual SDK codec; no driver/provider calls."""
from copy import deepcopy
from types import SimpleNamespace
CK3_12003=SimpleNamespace(executable_sha256="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6")

OPERATIONS = {
    'assembly_predicates': ('query-confucian-assembly-predicates-v1',
        'confucian_assembly_predicates_v1', 'ck3-1.20.0.3-native-confucian-assembly-predicates-v1',
        'confucian_assembly_predicates', 'ck3_12003_confucian_assembly_predicates_v1'),
    'religious_title': ('query-confucian-religious-title-v1',
        'confucian_religious_title_v1', 'ck3-1.20.0.3-native-confucian-religious-title-v1',
        'confucian_religious_title', 'ck3_12003_confucian_religious_title_v1'),
}


ENVELOPE_KEYS = {'step','accepted','status','private_build','read_only','advertised',
    'game_version','executable_sha256','domain_key','backend_id','snapshot_revision','date_raw'}


PUBLIC_KEYS = {'schema','operation','native_result','queried_snapshot_id','queried_revision',
    'queried_native_revision','date_raw','game_pid','connection_generation','player_character_id',
    'business_postcondition_verified','full_product_acceptance_credit'}


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(label+' must be an exact integer in range')
    return value


def exact(value, keys, label):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError(label+' requires exact fields')
    return value


def optional(value, kind, label):
    if value is not None and type(value) is not kind:
        raise ValueError(label+' requires its actual type or null')


def full_id(value, label):
    return integer(value, 0, 2**32-2, label)


def nullable_id(value, label):
    if value is not None: full_id(value,label)


def reason(value, required, label):
    if not required:
        if value is not None:raise ValueError(label+' must have null reason when complete')
        return
    if type(value) is not str or not value or len(value)>4096:
        raise ValueError(label+' requires an explicit unavailable reason')


def _common_payload(value, schema, binding):
    if (value.get('schema')!=schema or value.get('game_version')!='1.20.0.3'
            or type(value.get('executable_sha256'))is not str
            or value['executable_sha256'].upper()!=CK3_12003.executable_sha256):
        raise ValueError('native payload exact build/schema differs')
    for name,wanted in (('date_raw',binding['date_raw']),
                        ('played_character_id',binding['played_character_id'])):
        actual=integer(value.get(name),-(2**31),2**31-1,name)
        # Public character projections may preserve the same full uint32 as unsigned.
        if actual!=(wanted if wanted<2**31 else wanted-2**32):
            raise ValueError('native payload '+name+' differs from actual bound frame')
    integer(value.get('capture_epoch'),1,2**64-1,'capture_epoch')
    if type(value.get('available'))is not bool: raise ValueError('available must be an actual bool')


def _ids(value,label):
    if type(value)is not list: raise ValueError(label+' requires a complete actual list')
    for item in value: full_id(item,label)
    if len(set(value))!=len(value): raise ValueError(label+' contains duplicate full identities')
    return value


def normalize_assembly(value,binding):
    keys={'schema','read_only','game_version','executable_sha256','available','predicates_complete',
        'unavailable_reason','capture_epoch','date_raw','played_character_id','faith_id','played_rite_id',
        'religion_id','alive_source_pool_count','religion_county_source_pool_count',
        'complete_native_faith_member_ids','complete_native_faith_rite_ids','members','rites'}
    exact(value,keys,'Confucian assembly native payload')
    _common_payload(value,OPERATIONS['assembly_predicates'][4],binding)
    if value['read_only']is not True or type(value['predicates_complete'])is not bool:
        raise ValueError('assembly must preserve readonly and actual completeness')
    for name in ('faith_id','played_rite_id','religion_id'): nullable_id(value[name],name)
    for name in ('alive_source_pool_count','religion_county_source_pool_count'):
        if value[name]is not None:integer(value[name],0,2**31-1,name)
    if not value['available']:
        if value['predicates_complete']is not False or any(value[name]is not None for name in
                ('complete_native_faith_member_ids','complete_native_faith_rite_ids','members','rites')):
            raise ValueError('unavailable assembly must preserve null rosters')
        reason(value['unavailable_reason'],True,'assembly')
        return deepcopy(value)
    for name in ('faith_id','played_rite_id','religion_id'):full_id(value[name],name)
    members=_ids(value['complete_native_faith_member_ids'],'complete faith members')
    rites=_ids(value['complete_native_faith_rite_ids'],'complete faith rites')
    if binding['played_character_id']&0xFFFFFFFF not in members or value['played_rite_id']not in rites:
        raise ValueError('complete faith graph omits its played actor/rite')
    if type(value['members'])is not list or type(value['rites'])is not list:
        raise ValueError('actual member/rite rows must remain complete arrays')
    if [row.get('character_id')for row in value['members']if type(row)is dict]!=members:
        raise ValueError('member rows differ from the full native roster')
    if [row.get('rite_id')for row in value['rites']if type(row)is dict]!=rites:
        raise ValueError('rite rows differ from the full native roster')
    bools=('alive','adult','imprisoned','incapable','is_ai')
    for row in value['members']:
        exact(row,{'character_id','rite_id','faith_id',*bools,'effective_learning',
            'adult_measure_raw','adult_selector_raw','adult_threshold_raw','complete','unavailable_reason'},'member predicate row')
        full_id(row['character_id'],'member');nullable_id(row['rite_id'],'member rite');nullable_id(row['faith_id'],'member faith')
        for name in bools:optional(row[name],bool,name)
        for name,low,high in (('effective_learning',-(2**31),2**31-1),('adult_measure_raw',-(2**15),2**15-1),
                              ('adult_selector_raw',0,1),('adult_threshold_raw',-(2**31),2**31-1)):
            if row[name]is not None:integer(row[name],low,high,name)
        if type(row['complete'])is not bool:raise ValueError('member complete must be actual bool')
        if row['complete']:
            if (any(row[name]is None for name in (*bools,'rite_id','faith_id','effective_learning',
                    'adult_measure_raw','adult_selector_raw','adult_threshold_raw'))
                    or row['faith_id']!=value['faith_id']or row['rite_id']not in rites):
                raise ValueError('complete member lacks actual native predicates/membership')
            if row['adult']is not (row['adult_measure_raw']>=row['adult_threshold_raw']):
                raise ValueError('adult predicate differs from actual native raw threshold')
        reason(row['unavailable_reason'],not row['complete'],'member')
    for row in value['rites']:
        exact(row,{'rite_id','county_title_ids','native_county_count','complete','unavailable_reason'},'rite county row')
        full_id(row['rite_id'],'rite')
        if type(row['complete'])is not bool:raise ValueError('rite complete must be actual bool')
        if row['complete']:
            counties=_ids(row['county_title_ids'],'complete county titles')
            if integer(row['native_county_count'],0,2**31-1,'native_county_count')!=len(counties):
                raise ValueError('complete actual county count differs from array')
        elif row['county_title_ids']is not None or row['native_county_count']is not None:
            raise ValueError('unknown counties must remain null rather than empty/zero')
        reason(row['unavailable_reason'],not row['complete'],'rite')
    complete=all(row['complete']for row in value['members'])and all(row['complete']for row in value['rites'])
    if value['predicates_complete']is not complete:raise ValueError('overall predicates completeness differs from all rows')
    reason(value['unavailable_reason'],not complete,'assembly')
    return deepcopy(value)


def normalize_title(value,binding):
    exact(value,{'schema','game_version','executable_sha256','available','unavailable_reason','capture_epoch',
        'date_raw','played_character_id','played_character_full_id','graph_available','graph_unavailable_reason',
        'legal_head_title_absent','faith_full_id','head_title_full_id','native_title_holder_full_id',
        'native_title_holder_absent','native_title_class','title_holder','title_properties','title_laws',
        'mod_owned_marker','mod_owner_faith_variable','qualification'},'Confucian religious-title payload')
    _common_payload(value,OPERATIONS['religious_title'][4],binding)
    if value['played_character_full_id']!=(binding['played_character_id']&0xFFFFFFFF)or type(value['played_character_full_id'])is not int:
        raise ValueError('played full uint32 identity was lost')
    if type(value['graph_available'])is not bool:raise ValueError('graph availability must be actual bool')
    for name in ('legal_head_title_absent','native_title_holder_absent'):optional(value[name],bool,name)
    for name in ('faith_full_id','head_title_full_id','native_title_holder_full_id'):nullable_id(value[name],name)
    optional(value['native_title_class'],str,'native title class')
    if value['available']is not value['graph_available']:raise ValueError('actual title graph availability differs')
    for name in ('unavailable_reason','graph_unavailable_reason'):reason(value[name],not value['available'],name)
    if value['available']:
        full_id(value['faith_full_id'],'faith full ID')
        if type(value['legal_head_title_absent'])is not bool:raise ValueError('known graph requires explicit head absence')
        if value['legal_head_title_absent']:
            if any(value[name]is not None for name in ('head_title_full_id','native_title_holder_full_id','native_title_holder_absent','native_title_class')):
                raise ValueError('known absent head title cannot invent a title/holder')
        else:
            full_id(value['head_title_full_id'],'head title')
            if value['native_title_class']!='CLandedTitle'or type(value['native_title_holder_absent'])is not bool:
                raise ValueError('present title must retain its actual class and holder absence')
            if value['native_title_holder_absent']:
                if value['native_title_holder_full_id']is not None:raise ValueError('absent title holder cannot invent an ID')
            else:full_id(value['native_title_holder_full_id'],'actual title holder')
    else:
        if any(value[name]is not None for name in ('faith_full_id','head_title_full_id','native_title_holder_full_id',
                'legal_head_title_absent','native_title_holder_absent','native_title_class')):
            raise ValueError('unavailable title graph must preserve null identities')
    holder=exact(value['title_holder'],{'available','unavailable_reason','title_tier_raw','title_tier_key',
        'holder_character_full_id','holder_is_player','holder_in_player_realm',
        'holder_immediate_liege_character_full_id','holder_top_liege_character_full_id'},'legacy title holder')
    props=exact(value['title_properties'],{'available','unavailable_reason','destroy_if_invalid_heir',
        'no_automatic_claims','definitive_form','always_follows_primary_heir'},'title properties')
    laws=exact(value['title_laws'],{'available','unavailable_reason','native_count','complete_laws',
        'expected_law_key','temporal_head_of_faith_succession_law_member'},'title laws')
    for sub in (holder,props,laws):
        if type(sub['available'])is not bool:raise ValueError('title leaf availability must be actual bool')
        reason(sub['unavailable_reason'],not sub['available'],'title leaf')
    if holder['available']:
        integer(holder['title_tier_raw'],-(2**31),2**31-1,'title tier')
        if type(holder['title_tier_key'])is not str or not holder['title_tier_key']:raise ValueError('actual tier key required')
        for name in ('holder_character_full_id','holder_immediate_liege_character_full_id','holder_top_liege_character_full_id'):nullable_id(holder[name],name)
        for name in ('holder_is_player','holder_in_player_realm'):
            if type(holder[name])is not bool:raise ValueError('actual holder predicate required')
        if holder['holder_character_full_id']!=value['native_title_holder_full_id']:
            raise ValueError('legacy/direct holder full identities disagree')
    elif any(holder[name]is not None for name in set(holder)-{'available','unavailable_reason'}):
        raise ValueError('unavailable legacy holder must preserve null subfields')
    prop_fields=set(props)-{'available','unavailable_reason'}
    if props['available']:
        if any(type(props[name])is not bool for name in prop_fields):raise ValueError('four actual title properties required')
    elif any(props[name]is not None for name in prop_fields):raise ValueError('unavailable title properties must remain null')
    law_key='temporal_head_of_faith_succession_law'
    if laws['expected_law_key']!=law_key:raise ValueError('native law key contract differs')
    if laws['available']:
        rows=laws['complete_laws']
        if type(rows)is not list or integer(laws['native_count'],0,2**31-1,'native law count')!=len(rows):
            raise ValueError('actual full law array/count required')
        for row in rows:
            exact(row,{'native_definition_id','key'},'native law row')
            integer(row['native_definition_id'],0,2**32-1,'native law definition ID')
            if type(row['key'])is not str or not row['key']:raise ValueError('actual native law key required')
        if type(laws['temporal_head_of_faith_succession_law_member'])is not bool or laws['temporal_head_of_faith_succession_law_member']is not any(row['key']==law_key for row in rows):
            raise ValueError('native expected-law membership differs from complete array')
    elif any(laws[name]is not None for name in ('native_count','complete_laws','temporal_head_of_faith_succession_law_member')):
        raise ValueError('unavailable laws must remain null')
    if not value['available']or value['legal_head_title_absent']is True:
        if any(sub['available']for sub in (holder,props,laws)):raise ValueError('absent/unavailable graph cannot carry observed title leaves')
    if value['mod_owned_marker']is not None or value['mod_owner_faith_variable']is not None:
        raise ValueError('script-variable business markers are unobserved and must remain null')
    qualification=exact(value['qualification'],{'kind','title_properties_index_sha256','title_laws_index_sha256',
        'head_getters_index_sha256','faith_reference_identity_offset','title_full_id_offset',
        'faith_typed_fallback_slot_rva','runtime_acceptance'},'native static qualification')
    expected={'kind':'exact_current_static_abi','title_properties_index_sha256':'14bf997b58a8ff33d7407ece6be2675917a2b7ed7e6ffdba70ca8ea938347a0a',
        'title_laws_index_sha256':'9d371bf97f50281c621d777890915d6767c354275222fa38d7e1127076afeb60',
        'head_getters_index_sha256':'d93f24e7be97fc7a59c35b76313e9b7a10f8d97dcb7534015b504373aa2dd973',
        'faith_reference_identity_offset':8,'title_full_id_offset':16,'faith_typed_fallback_slot_rva':'0x5D1E2E0','runtime_acceptance':None}
    if any(type(qualification[name])is not type(wanted)or qualification[name]!=wanted for name,wanted in expected.items()):
        raise ValueError('native exact-current static qualification differs')
    return deepcopy(value)


def project_native_query(raw,binding,operation):
    if operation not in OPERATIONS:raise ValueError('unsupported Confucian read operation')
    step,domain,backend,nested,schema=OPERATIONS[operation]
    exact(raw,ENVELOPE_KEYS|{nested},'native Confucian readonly envelope')
    expected={'step':step,'accepted':True,'private_build':True,'read_only':True,'advertised':False,
        'game_version':'1.20.0.3','domain_key':domain,'backend_id':backend,
        'snapshot_revision':binding['native_revision'],'date_raw':binding['date_raw']}
    if any(type(raw[name])is not type(wanted)or raw[name]!=wanted for name,wanted in expected.items()):
        raise ValueError('native Confucian envelope differs from actual operation/frame')
    if type(raw['executable_sha256'])is not str or raw['executable_sha256'].upper()!=CK3_12003.executable_sha256:
        raise ValueError('native Confucian envelope image differs')
    value=(normalize_assembly if operation=='assembly_predicates'else normalize_title)(raw[nested],binding)
    if raw['status']!=('observed'if value['available']else'unavailable'):
        raise ValueError('native Confucian envelope availability differs')
    return {'schema':'ck3-confucian-readonly-public-v1','operation':operation,'native_result':deepcopy(raw),
        'queried_snapshot_id':binding['snapshot_id'],'queried_revision':binding['revision'],
        'queried_native_revision':binding['native_revision'],'date_raw':binding['date_raw'],
        'game_pid':binding['game_pid'],'connection_generation':binding['connection_generation'],
        'player_character_id':binding['played_character_id'],'business_postcondition_verified':False,
        'full_product_acceptance_credit':False}


def normalize_public_query(raw,binding,operation):
    exact(raw,PUBLIC_KEYS,'public Confucian readonly result')
    projected=project_native_query(raw['native_result'],binding,operation)
    if any(type(raw[name])is not type(wanted)or raw[name]!=wanted for name,wanted in projected.items()):
        raise ValueError('public Confucian read binding or credit changed')
    return deepcopy(raw)
