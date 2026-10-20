"""Finite Mecca Knight public policy: read/present, or one reviewed original Demote26."""
from __future__ import annotations
import re

KNIGHT = 'ck3_query_character_knight_effectiveness_v1'
ACTOR = 'ck3_query_character_skill_effects_v1'
SITES = 'ck3_query_player_holy_site_v1'
RELIC = 'ck3_query_player_holy_site_relic_context_v1'
RELIGION = 'ck3_query_player_religion_context_v1'
DETAIL = 'ck3_query_player_holy_site_decision_detail_v1'
COOLDOWN = 'ck3_query_player_holy_site_decision_cooldown_v1'
CONFIRM = 'ck3_confirm_holy_site_decision_v1'
READONLY = frozenset({KNIGHT,ACTOR,SITES,RELIC,RELIGION,DETAIL,COOLDOWN})
PRESENT = frozenset({'ck3_open_holy_site_window_v1','ck3_open_holy_site_decision_v1',
                     'ck3_open_character_window_v1'})
TOOLS = READONLY | PRESENT | {CONFIRM,'ck3_get_capabilities','ck3_take_snapshot','ck3_query_ingame_ui_window_v1'}

def require(value,message):
    if not value: raise ValueError(message)

def ref(value): return type(value) is int and 0 <= value < 2**32-1

def step(name,tool,args=None):
    return {'id':name,'tool':tool,'args':args or {},'fresh_revision':True,
            'continue_on_error':True,'timeout':20}

def validate(plan):
    require(type(plan) is dict and set(plan)=={'steps'} and type(plan['steps']) is list
        and 1 <= len(plan['steps']) <= 4,'Finite Mecca Knight public steps required')
    if any(s.get('kind')=='advance_day'for s in plan['steps']):
        require(len(plan['steps'])==1,'One original natural day alone')
        s=plan['steps'][0]
        require(set(s)=={'id','kind','days','allow_event_boundary','allow_actor_change','timeout','continue_on_error'}
            and type(s.get('id'))is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}',s['id'])
            and type(s.get('days'))is int and s['days']==1 and s.get('allow_event_boundary')is True
            and s.get('allow_actor_change')is False and type(s.get('timeout'))in(int,float)and 0<s['timeout']<=60
            and s.get('continue_on_error')is True,'Only one explicit bounded event-aware natural day')
        return {'validated':True,'submitted':False,'automatic_retry':False,'natural_day_scope':True}
    ids=[]
    for index,s in enumerate(plan['steps']):
        require(type(s) is dict and set(s)<={'id','tool','args','fresh_revision','continue_on_error','timeout'},
                'No lifecycle/raw/day input in the Mecca Knight policy')
        require(type(s.get('id')) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}',s['id']), 'Portable step ID required')
        ids.append(s['id']); tool=s.get('tool'); args=s.get('args',{})
        require(tool in TOOLS and type(args) is dict and s.get('fresh_revision') is True
                and s.get('continue_on_error') is True,'Only listed fresh public calls')
        require(type(s.get('timeout',20)) in (int,float) and 0 < s.get('timeout',20) <=20,'Bounded public timeout required')
        needed=set(); optional={'expected_revision'}
        if tool=='ck3_get_capabilities': optional=set()
        elif tool=='ck3_take_snapshot': optional={'include_native_command_history'}
        elif tool==KNIGHT: needed={'character_id'}
        elif tool==ACTOR:
            needed={'character_id','skill'}
            require(args.get('skill')=='diplomacy','Only the selected original diplomacy breakdown')
        elif tool==SITES: optional.add('holy_site_id')
        elif tool==RELIC: needed={'holy_site_id'}
        elif tool in {DETAIL,CONFIRM,'ck3_open_holy_site_decision_v1'}:
            needed={'action','holy_site_id'}
            require(args.get('action')=='demote' and type(args.get('holy_site_id')) is int and args['holy_site_id']==26,
                    'Only current original Demote26, never another action/site')
        elif tool==COOLDOWN:
            needed={'action'}; require(args.get('action')=='demote','Only the fixed demote cooldown')
        elif tool=='ck3_open_holy_site_window_v1':
            needed={'holy_site_id'};require(args.get('holy_site_id')==26,'Only selected site27 is presented')
        elif tool=='ck3_open_character_window_v1': needed={'character_id'}
        elif tool=='ck3_query_ingame_ui_window_v1':
            needed={'window_kind'}
            require(args.get('window_kind') in {'holy_site','holy_site_adoption','character'},'Only original Mecca Knight windows')
        require(needed<=set(args)<=needed|optional,'Actual public argument set differs: '+str(tool))
        for key in ('holy_site_id','character_id'):
            require(key not in args or ref(args[key]),'Actual full reference required: '+key)
        if 'expected_revision' in args:require(type(args['expected_revision']) is int and args['expected_revision']>0,'Positive actual revision only')
        require(args.get('include_native_command_history',False) is False,'No command history export')
        if tool==CONFIRM:require(len(plan['steps'])==1,'One world confirm alone; independent readback is a later public batch')
        if tool in PRESENT:
            require(index+1<len(plan['steps']),'Presentation requires immediate independent readback')
            following=plan['steps'][index+1]
            expected=DETAIL if tool=='ck3_open_holy_site_decision_v1' else 'ck3_query_ingame_ui_window_v1'
            require(following.get('tool')==expected,'Wrong independent presentation reader')
            a=following.get('args',{})
            if expected==DETAIL:require(a.get('action')=='demote' and a.get('holy_site_id')==26,'Crossed decision readback')
            else:require(a.get('window_kind')==('holy_site' if tool=='ck3_open_holy_site_window_v1' else 'character'),'Wrong actual window')
    require(len(ids)==len(set(ids)),'Consumed step IDs cannot repeat')
    return {'validated':True,'submitted':False,'automatic_retry':False}
