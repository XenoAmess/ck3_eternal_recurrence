"""Exact .3 rules selected in the actual CGameRuleInstance, never GUI guesses."""
from __future__ import annotations
import re

QUERY_FRONTEND_APPLIED_GAME_RULES_V1_STEP = 'query-frontend-applied-game-rules-v1'
QUERY_FRONTEND_APPLIED_GAME_RULES_V1_CAPABILITY = 'game.command.' + QUERY_FRONTEND_APPLIED_GAME_RULES_V1_STEP
EXE_SHA256='94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'
_KEY=re.compile(r'[A-Za-z0-9_]{1,96}\Z',re.ASCII)


def normalize_frontend_applied_game_rules_v1(value: object) -> dict[str, object]:
    if not isinstance(value,dict):
        raise ValueError('applied game rule observation must be an object')
    for key,wanted in {'schema':'frontend_applied_game_rules_v1','schema_version':1,
            'game_version':'1.20.0.3','executable_sha256':EXE_SHA256,
            'source':'CGameRuleInstance.selected_settings','backend_id':'native-headless',
            'read_only':True,'uses_ocr':False,'uses_mouse':False,'uses_keyboard':False}.items():
        if type(value.get(key)) is not type(wanted) or value[key]!=wanted:
            raise ValueError(f'unverified actual-instance field: {key}')
    ready=value.get('ready');proof=value.get('applied_settings_proven')
    reason=value.get('unavailable_reason');count=value.get('selection_count');rows=value.get('selections')
    if type(ready) is not bool or type(proof) is not bool or proof!=ready:
        raise ValueError('actual-instance readiness and proof are inconsistent')
    if not isinstance(reason,str) or type(count) is not int or not 0<=count<=4096 or not isinstance(rows,list) or len(rows)!=count or (ready and (not count or reason)) or (not ready and (count or not reason)):
        raise ValueError('actual-instance readiness and collection are inconsistent')
    pairs=[]
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'rule_key','selected_setting_key'} or any(
                not isinstance(row[k],str) or not _KEY.fullmatch(row[k]) for k in ['rule_key','selected_setting_key']):
            raise ValueError('actual-instance selected pair is malformed')
        pairs.append(dict(row))
    keys=[p['rule_key'] for p in pairs]
    if keys!=sorted(keys) or len(set(keys))!=len(keys):
        raise ValueError('actual-instance rule keys are duplicated or unsorted')
    return {**value,'selections':pairs}
