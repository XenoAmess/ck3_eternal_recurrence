"""Focused SOURCE_ONLY optional-target guard checks; no CK3 or native claims.

Evaluate actual generated Boolean/scope trees eagerly between sibling terms.
Only authored trigger_if limits suppress their branch. Scope fixtures are test
doubles; script-tree preservation binds every existing authority expression.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE.parent/'tools'))
from extract_auto_upgrade_buildings import Block, Entry, parse_clausewitz
from test_c2_preview_scope import Scope, MISSING, UndefinedRead, definition

C3='common/scripted_triggers/lyd_c3_leadership_triggers.txt'
I3='common/scripted_triggers/lyd_i3b_institution_triggers.txt'
FALSE=Block((Entry('always','=','no'),))
BASELINE_AST_SHA256={C3:'e9836265a7371777dca0d784fcd614a85d689267cbdf3f5e614412eb30f1dc0e',I3:'45b2043addbc812e2e7b41426f1451187d159708ec2df14f30a7d7bc659e8284'}
LIMITS={
 (('exists','faith.religious_head'),('exists','faith.religious_head_title'),('exists','faith.religious_head_title.holder')),
 (('exists','religious_head_title'),),
 (('has_variable','lyd_c2_owned_head_title'),('has_variable','lyd_c2_owner_faith')),
 (('exists','faith.religious_head'),),
 (('exists','faith.religious_head_title'),),
 (('has_variable','lyd_c3_delegate'),('exists','head_of_rite')),
 (('exists','rite.head_of_rite'),),
 (('has_variable','lyd_i3b_required_native_hor'),('exists','var:lyd_i3b_main.head_of_rite')),
 (('has_variable','lyd_i3b_result_native_hor'),('exists','var:lyd_i3b_main.head_of_rite')),
}

def walk(block):
    for e in block.entries:
        yield e
        if isinstance(e.value,Block): yield from walk(e.value)

def strip_added(block):
    """Invert only the nine declared, explicit-false conditional shapes."""
    result=[];i=0
    while i<len(block.entries):
        e=block.entries[i];i+=1
        if e.key=='trigger_if' and isinstance(e.value,Block):
            lim=e.value.entries[0]
            shape=tuple((x.key,x.value) for x in lim.value.entries) if lim.key=='limit' else ()
            if shape in LIMITS:
                if i>=len(block.entries) or block.entries[i]!=Entry('trigger_else','=',FALSE):
                    raise AssertionError('optional target guard must explicitly reject')
                i+=1
                result.extend(strip_added(Block(e.value.entries[1:])).entries)
                continue
        result.append(Entry(e.key,e.operator,strip_added(e.value) if isinstance(e.value,Block) else e.value))
    return Block(tuple(result))


def invert_phase2_mandate(block):
    """Undo only the reviewed AND wrapper, in its exact ready/rites context.

    The old SHA remains authoritative for every other expression. Requiring the
    entire current shape also rejects removal or drift of the reviewed fix.
    """
    mandate = Block((Entry('var:lyd_i3b_total','>','0'),
                     Entry('lyd_i3b_quorum_value','>=','0'),
                     Entry('var:lyd_i3b_signed','=','1'),
                     Entry('exists','=','var:lyd_i3b_delegate')))
    prefix = (Entry('variable','=','lyd_i3b_rites'),
              Entry('var:lyd_i3b_dormant','=','0'))
    declared = Entry('NOT','=',Block((Entry('any_in_list','=',Block(
        prefix + (Entry('NOT','=',Block((Entry('AND','=',mandate),))),))),)))
    previous = Entry('NOT','=',Block((Entry('any_in_list','=',Block(
        prefix + (Entry('NOT','=',mandate),))),)))
    ready = [e for e in block.entries if e.key=='lyd_i3b_ready_trigger']
    if len(ready)!=1 or not isinstance(ready[0].value,Block):
        raise ValueError('Expected one reviewed I3b ready definition')
    if sum(e==declared for e in ready[0].value.entries)!=1:
        raise ValueError('Reviewed phase2 mandate AST differs or is absent')
    projected = Block(tuple(previous if e==declared else e for e in ready[0].value.entries))
    return Block(tuple(Entry(e.key,e.operator,projected) if e is ready[0] else e for e in block.entries))

def strip_declared(block,relative):
    if relative==I3:
        block=invert_phase2_mandate(block)
    return strip_added(block)

class Evaluator:
    def __init__(self,actor,common):
        self.actor=actor;self.common=common;self.saved={};self.reads=[]
    def resolve(self,path,current,previous=None,safe=False):
        if path.startswith(('faith:','religion:','rite:')):
            answer=self.common if path=='faith:lyd_common_faith' else path
        else:
            parts=path.split('.')
            if parts[0] in ('root','$ACTOR$','this','prev'):
                answer={'root':self.actor,'$ACTOR$':self.actor,'this':current,'prev':previous}[parts.pop(0)]
            elif parts[0].startswith('scope:'):answer=self.saved.get(parts.pop(0)[6:],MISSING)
            else:answer=current
            for part in parts:
                if not isinstance(answer,Scope):answer=MISSING;break
                answer=(answer.variables if part.startswith('var:') else answer.values).get(part[4:] if part.startswith('var:') else part,MISSING)
        if answer is MISSING and not safe:raise UndefinedRead(path)
        if not safe:self.reads.append(path)
        return answer
    def atom(self,token,current,previous):
        if token in ('yes','no'):return token=='yes'
        if token=='tier_duchy':return 3
        try:return int(token)
        except ValueError:return self.resolve(token,current,previous)
    def block(self,block,current,previous=None):
        outcomes=[];i=0
        while i<len(block.entries):
            e=block.entries[i];i+=1;k,v=e.key,e.value
            if k=='trigger_if':
                assert v.entries[0].key=='limit'
                condition=self.block(v.entries[0].value,current,previous)
                fallback=None
                if i<len(block.entries) and block.entries[i].key=='trigger_else':fallback=block.entries[i].value;i+=1
                answer=self.block(Block(v.entries[1:]),current,previous) if condition else self.block(fallback,current,previous) if fallback is not None else True
            elif k=='trigger_else':raise AssertionError('orphan trigger_else')
            elif k in ('AND','NOT'):
                children=self.block(v,current,previous);answer=children if k=='AND' else not children
            elif k in ('OR','NOR','NAND'):
                children=[self.block(Block((x,)),current,previous) for x in v.entries]
                answer=any(children) if k=='OR' else not any(children) if k=='NOR' else not all(children)
            elif k=='always':answer=v=='yes'
            elif k=='exists':answer=self.resolve(v,current,previous,True) is not MISSING
            elif k=='has_variable':answer=v in current.variables
            elif k=='has_trait':answer=v in current.values['traits']
            elif k=='has_doctrine_parameter':answer=v in current.values['parameters']
            elif k=='rite_has_parameter':answer=v in current.values['parameters']
            elif k=='rite_has_allowed_gender_for_clergy':answer=current.values['gender_allowed'] and self.resolve(v,current,previous) is self.actor
            elif k=='save_temporary_scope_as':self.saved[v]=current;answer=True
            elif k in ('pam_is_antipope_trigger','pam_is_antipope_sponsor_trigger'):answer=current.values[k]==(v=='yes')
            elif k in ('lyd_i3b_only_owned_rites_faith_trigger',):answer=current.values['owned_rites']
            elif k=='lyd_i3b_detached_authority_trigger':answer=self.block(self.detached,current,previous)
            elif k=='any_faith_character':answer=any([self.block(v,c,current) for c in current.values['characters']])
            elif isinstance(v,Block):answer=self.block(v,self.resolve(k,current,previous),current)
            else:
                left=self.resolve(k,current,previous);right=self.atom(v,current,previous)
                answer={'=':lambda:left==right,'!=':lambda:left!=right,'>=':lambda:left>=right,'>':lambda:left>right,'<':lambda:left<right}[e.operator]()
            outcomes.append(answer)
        return all(outcomes)

def world():
    actor=Scope('actor',{'is_alive':True,'is_adult':True,'traits':set(),'highest_held_title_tier':3,'capital_county':Scope('capital'),'pam_is_antipope_trigger':False,'pam_is_antipope_sponsor_trigger':False})
    faith=Scope('faith',{'parameters':{'temporal_head_of_faith'},'owned_rites':True,'characters':[]})
    common=Scope('common',{'owned_rites':True})
    rite=Scope('rite',{'parameters':set(),'gender_allowed':True,'rite_counties':0,'faith':faith})
    head=Scope('head',{'is_alive':True,'is_adult':True,'traits':set(),'faith':faith,'rite':rite})
    title=Scope('title',{'holder':head},{'lyd_c2_owned_head_title':1,'lyd_c2_owner_faith':faith})
    actor.values.update(faith=faith,rite=rite)
    faith.values.update(religious_head=head,religious_head_title=title,main_rite=rite)
    common.values['main_rite']=rite
    rite.values['head_of_rite']=head
    actor.variables.update(lyd_c3_round_faith=faith,lyd_c3_round_head=head,lyd_c3_round_title=title,lyd_i3b_main=rite,lyd_i3b_authority_mode=1,lyd_i3b_required_native_hor=actor,lyd_i3b_result_authority_mode=1,lyd_i3b_result_native_hor=actor)
    rite.variables.update(lyd_c3_delegate_required=1,lyd_c3_delegate=head)
    return dict(actor=actor,faith=faith,common=common,rite=rite,head=head,title=title)

def run(source,baseline=None):
    trees={p:parse_clausewitz((source/p).read_text('utf-8-sig')) for p in (C3,I3)}
    previous={p:strip_declared(trees[p],p) for p in (C3,I3)}
    for p in trees:
        assert hashlib.sha256(repr(previous[p]).encode('utf-8')).hexdigest()==BASELINE_AST_SHA256[p],f'existing script expressions changed: {p}'
        if baseline is not None:
            assert previous[p]==parse_clausewitz((baseline/p).read_text('utf-8-sig')),f'copied baseline AST differs: {p}'
    c3,i3=trees[C3],trees[I3];oldc3,oldi3=previous[C3],previous[I3]
    delegate=lambda ast:next(Block((e,)) for e in walk(definition(ast,'lyd_c3_round_current_trigger')) if e.key=='OR' and any(x.key=='var:lyd_c3_delegate_required' for x in walk(e.value)))
    round_branch=lambda ast,name:next(Block(e.value.entries[1:]) for e in definition(ast,'lyd_c3_round_current_trigger').entries if e.key=='trigger_if' and e.value.entries[0].value==Block((Entry('has_variable','=',name),)))
    helpers={
      'eligible':(definition(c3,'lyd_c3_native_challenger_eligible_trigger'),definition(oldc3,'lyd_c3_native_challenger_eligible_trigger'),'actor'),
      'owned':(definition(c3,'lyd_c3_owned_current_head_trigger'),definition(oldc3,'lyd_c3_owned_current_head_trigger'),'faith'),
      'delegate':(delegate(c3),delegate(oldc3),'rite'),
      'round_head':(round_branch(c3,'lyd_c3_round_head'),round_branch(oldc3,'lyd_c3_round_head'),'actor'),
      'round_title':(round_branch(c3,'lyd_c3_round_title'),round_branch(oldc3,'lyd_c3_round_title'),'actor'),
      'detached':(definition(i3,'lyd_i3b_detached_authority_trigger'),definition(oldi3,'lyd_i3b_detached_authority_trigger'),'actor'),
      'captured':(definition(i3,'lyd_i3b_captured_authority_trigger'),definition(oldi3,'lyd_i3b_captured_authority_trigger'),'actor'),
      'post':(definition(i3,'lyd_i3b_native_authority_postcondition_trigger'),definition(oldi3,'lyd_i3b_native_authority_postcondition_trigger'),'actor'),
    }
    cases=[];mutants=[]
    def test(name,helper,change,expected,mutant=False):
        w=world();change(w);ev=Evaluator(w['actor'],w['common']);ev.saved.update(lyd_c3_checked_rite=w['rite'],lyd_c3_checked_faith=w['faith'])
        ev.detached=helpers['detached'][0]
        block,old,current=helpers[helper]
        actual=ev.block(block,w[current]);assert actual==expected,(name,actual,expected)
        cases.append({'name':name,'accepted':actual,'expected':expected,'undefined_reads':0})
        if mutant:
            ev=Evaluator(w['actor'],w['common']);ev.saved.update(lyd_c3_checked_rite=w['rite'],lyd_c3_checked_faith=w['faith']);ev.detached=helpers['detached'][0]
            try:old_result=ev.block(old,w[current])
            except UndefinedRead as err:mutants.append({'name':name,'without_guards':'UndefinedRead','path':str(err)})
            else:assert old_result!=expected,(name,'removed guards survived');mutants.append({'name':name,'without_guards':old_result})
    noop=lambda w:None
    test('native_eligible_existing_office','eligible',noop,True)
    test('native_missing_head','eligible',lambda w:w['faith'].values.pop('religious_head'),False,True)
    test('native_missing_title','eligible',lambda w:w['faith'].values.pop('religious_head_title'),False,True)
    test('native_missing_title_holder','eligible',lambda w:w['title'].values.pop('holder'),False,True)
    test('native_dead_head','eligible',lambda w:w['head'].values.update(is_alive=False),False)
    test('native_foreign_head_faith','eligible',lambda w:w['head'].values.update(faith=w['common']),False)
    test('native_holder_drift','eligible',lambda w:w['title'].values.update(holder=w['actor']),False)
    test('native_existing_antipope','eligible',lambda w:w['actor'].values.update(pam_is_antipope_trigger=True),False)
    test('native_existing_sponsor','eligible',lambda w:w['actor'].values.update(pam_is_antipope_sponsor_trigger=True),False)
    test('native_low_rank','eligible',lambda w:w['actor'].values.update(highest_held_title_tier=2),False)
    test('native_no_capital','eligible',lambda w:w['actor'].values.pop('capital_county'),False)
    test('native_no_head_parameter','eligible',lambda w:w['faith'].values.update(parameters=set()),False)
    test('native_disallowed_clergy','eligible',lambda w:w['rite'].values.update(gender_allowed=False),False)
    test('owned_matching_title','owned',noop,True)
    test('owned_no_title','owned',lambda w:w['faith'].values.pop('religious_head_title'),False,True)
    test('owned_foreign_no_metadata','owned',lambda w:w['title'].variables.clear(),False,True)
    test('owned_owner_missing','owned',lambda w:w['title'].variables.pop('lyd_c2_owner_faith'),False,True)
    test('owned_marker_missing','owned',lambda w:w['title'].variables.pop('lyd_c2_owned_head_title'),False,True)
    test('owned_marker_zero','owned',lambda w:w['title'].variables.update(lyd_c2_owned_head_title=0),False)
    test('owned_wrong_faith','owned',lambda w:w['title'].variables.update(lyd_c2_owner_faith=w['common']),False)
    test('delegate_existing_head','delegate',noop,True)
    test('delegate_required_missing','delegate',lambda w:w['rite'].variables.pop('lyd_c3_delegate'),False,True)
    test('delegate_current_head_missing','delegate',lambda w:w['rite'].values.pop('head_of_rite'),False,True)
    test('delegate_holder_drift','delegate',lambda w:w['rite'].values.update(head_of_rite=w['actor']),False)
    test('delegate_dead','delegate',lambda w:w['head'].values.update(is_alive=False),False)
    test('delegate_minor','delegate',lambda w:w['head'].values.update(is_adult=False),False)
    test('delegate_incapable','delegate',lambda w:w['head'].values['traits'].add('incapable'),False)
    test('delegate_wrong_rite','delegate',lambda w:w['head'].values.update(rite=Scope('other')),False)
    def dormant(w):
        w['rite'].variables.update(lyd_c3_delegate_required=0);w['rite'].variables.pop('lyd_c3_delegate');w['rite'].values.pop('head_of_rite')
    test('dormant_no_delegate_or_head','delegate',dormant,True,True)
    test('dormant_county_drift','delegate',lambda w:(dormant(w),w['rite'].values.update(rite_counties=1)),False)
    test('round_existing_head','round_head',noop,True)
    test('round_current_head_disappeared','round_head',lambda w:w['faith'].values.pop('religious_head'),False,True)
    test('round_head_drift','round_head',lambda w:w['faith'].values.update(religious_head=w['actor']),False)
    test('round_existing_title','round_title',noop,True)
    test('round_current_title_disappeared','round_title',lambda w:w['faith'].values.pop('religious_head_title'),False,True)
    def detached(w):w['rite'].values['head_of_rite']=w['actor']
    test('detached_actual_hor','detached',detached,True)
    test('detached_hor_missing','detached',lambda w:w['rite'].values.pop('head_of_rite'),False,True)
    test('detached_wrong_hor','detached',noop,False)
    test('detached_wrong_main','detached',lambda w:(detached(w),w['faith'].values.update(main_rite=Scope('other'))),False)
    def common(w):
        w['actor'].values['faith']=w['common'];w['actor'].variables['lyd_i3b_authority_mode']=0;w['actor'].variables.pop('lyd_i3b_required_native_hor')
    test('captured_common_mode_without_hor','captured',common,True,True)
    test('captured_detached_same_hor','captured',detached,True)
    test('captured_detached_missing_target','captured',lambda w:(detached(w),w['actor'].variables.pop('lyd_i3b_required_native_hor')),False,True)
    test('captured_detached_current_hor_missing','captured',lambda w:w['rite'].values.pop('head_of_rite'),False,True)
    test('captured_detached_target_drift','captured',lambda w:(detached(w),w['actor'].variables.update(lyd_i3b_required_native_hor=w['head'])),False)
    test('captured_mode0_wrong_faith','captured',lambda w:(detached(w),w['actor'].variables.update(lyd_i3b_authority_mode=0)),False)
    def common_result(w):w['actor'].variables.update(lyd_i3b_result_authority_mode=0);w['actor'].variables.pop('lyd_i3b_result_native_hor')
    test('post_common_mode_without_hor','post',common_result,True,True)
    test('post_detached_same_hor','post',detached,True)
    test('post_detached_missing_target','post',lambda w:(detached(w),w['actor'].variables.pop('lyd_i3b_result_native_hor')),False,True)
    test('post_detached_current_hor_missing','post',lambda w:w['rite'].values.pop('head_of_rite'),False,True)
    test('post_detached_hor_drift','post',lambda w:w['actor'].variables.update(lyd_i3b_result_native_hor=w['head']),False)
    return {'result':'PASS_SOURCE_ONLY','script_tree_preservation':'PASS_EXACT_AST_AFTER_FINITE_DECLARED_INVERSE','cases':cases,'guard_removal_mutants':mutants,'live':'NOT_RUN','boundary':'Focused test double evaluation. No old C2/11/118 tests run; no CK3 renderer or field proof.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,default=SOURCE);p.add_argument('--baseline-root',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    if a.report.exists():raise FileExistsError(a.report)
    report=run(a.source_root,a.baseline_root);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':report['result'],'cases':len(report['cases']),'mutants':len(report['guard_removal_mutants']),'script_tree_preservation':report['script_tree_preservation'],'live':report['live']},indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
