"""Evaluate the generated C2 scope/Boolean subset against independent cases.

Missing dereferences raise even when a preceding sibling condition is false:
the test therefore checks the preview guards, not Python short-circuiting.
This is SOURCE_L0, never an engine/tooltip verification.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass, field
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE.parent/'tools'))
from extract_auto_upgrade_buildings import Block, Entry, parse_clausewitz
TRIG='common/scripted_triggers/lyd_c2_consent_triggers.txt'
EVENT='events/lyd_c2_consent_events.txt'
MISSING=object()

@dataclass(eq=False)
class Scope:
    name:str
    values:dict=field(default_factory=dict)
    variables:dict=field(default_factory=dict)

class UndefinedRead(AssertionError): pass

class Evaluator:
    def __init__(self,actor,doctrines=()):
        self.actor=actor; self.saved={}; self.doctrines=doctrines; self.reads=[]
    def resolve(self,path,current,previous=None,safe=False):
        if path=='lyd_c2_target_quorum_value':
            # Feed the independently computed original script-value result.
            result=current.variables.get(path,MISSING)
        elif path in ('this','prev','$ACTOR$','$TARGET$'):
            result={'this':current,'prev':previous,'$ACTOR$':self.actor,
                    '$TARGET$':self.actor.values.get('target',MISSING)}[path]
        else:
            pieces=path.split('.')
            if pieces[0] in ('$ACTOR$','$TARGET$','this','prev'):
                result=self.resolve(pieces.pop(0),current,previous,safe)
            elif pieces[0].startswith('scope:'):
                result=self.saved.get(pieces.pop(0)[6:],MISSING)
            else: result=current
            for part in pieces:
                if result is MISSING or not isinstance(result,Scope): result=MISSING; break
                store=result.variables if part.startswith('var:') else result.values
                key=part[4:] if part.startswith('var:') else part
                result=store.get(key,MISSING)
        if result is MISSING and not safe: raise UndefinedRead(path)
        if result is not MISSING and not safe: self.reads.append(path)
        return result
    def atom(self,token,current,previous):
        if token in ('yes','no'): return token=='yes'
        try: return int(token)
        except ValueError: return self.resolve(token,current,previous)
    def block(self,block,current,previous=None):
        outcomes=[]; entries=block.entries; i=0
        while i<len(entries):
            entry=entries[i]; key,value=entry.key,entry.value; i+=1
            if key=='trigger_if':
                limit=value.entries[0]
                if limit.key!='limit': raise AssertionError('limit must be first')
                condition=self.block(limit.value,current,previous)
                fallback=None
                if i<len(entries) and entries[i].key=='trigger_else': fallback=entries[i].value; i+=1
                answer=(self.block(Block(value.entries[1:]),current,previous) if condition else
                        self.block(fallback,current,previous) if fallback is not None else True)
            elif key=='trigger_else': raise AssertionError('orphan alternative')
            elif key in ('AND','NOT'):
                result=self.block(value,current,previous)
                answer=result if key=='AND' else not result
            elif key=='OR':
                results=[self.block(Block((e,)),current,previous) for e in value.entries]
                answer=any(results)
            elif key=='custom_tooltip': answer=self.block(value,current,previous)
            elif key=='text': answer=True
            elif key=='always': answer=value=='yes'
            elif key=='exists': answer=self.resolve(value,current,previous,safe=True) is not MISSING
            elif key=='has_variable': answer=value in current.variables
            elif key=='save_temporary_scope_as': self.saved[value]=current; answer=True
            elif key=='any_doctrine':
                answer=any([self.block(value,doctrine,current) for doctrine in self.doctrines])
            elif key=='rite_has_doctrine':
                if value!='prev': raise AssertionError('doctrine scope changed')
                answer=previous in current.values['doctrines']
            elif key=='any_in_list':
                first=value.entries[0]
                if first.key!='variable': raise AssertionError('list identity')
                answer=any([self.block(Block(value.entries[1:]),item,current)
                            for item in current.variables[first.value]])
            elif key=='lyd_c2_single_rite_faith_trigger': answer=current.values['rite_count']==1
            elif key=='lyd_c2_dormant_receiving_rite_trigger': answer=current.values['dormant']
            elif key=='has_trait': answer=value in current.values['traits']
            elif isinstance(value,Block): answer=self.block(value,self.resolve(key,current,previous),current)
            else:
                left=self.resolve(key,current,previous); right=self.atom(value,current,previous)
                answer={'=':lambda:left==right,'>':lambda:left>right,'>=':lambda:left>=right,
                        '<':lambda:left<right,'<=':lambda:left<=right}[entry.operator]()
            outcomes.append(answer)
        return all(outcomes)

def definition(ast,name): return next(e.value for e in ast.entries if e.key==name)
def terms(block): return [(e.key,e.operator,e.value) for e in block.entries]
FALSE=Block((Entry('always','=','no'),))
def project_scope_guards(block):
    out=[]; i=0
    while i<len(block.entries):
        e=block.entries[i]; i+=1
        if e.key=='custom_tooltip' and isinstance(e.value,Block):
            if e.value.entries[0]!=Entry('text','=','lyd_c2_same_main_doctrines_tt'):
                raise AssertionError('Changed doctrine display key')
            out.extend(e.value.entries[1:]); continue
        if e.key=='trigger_if' and isinstance(e.value,Block):
            limit=e.value.entries[0].value
            shape=terms(limit)
            if shape==[('has_variable','=','lyd_c2_source_head_retired')]:
                if len(e.value.entries)!=2 or e.value.entries[1].key!='trigger_if': raise AssertionError('Postcondition original branch missing')
                if i<len(block.entries) and block.entries[i].key=='trigger_else': raise AssertionError('No-retirement branch must skip')
                out.append(e.value.entries[1]); continue
            is_retire=(len(shape)==3 and shape[0]==('exists','=','var:lyd_c2_source_head')
                       and shape[1]==('exists','=','var:lyd_c2_source_head_title')
                       and limit.entries[2]==Entry('var:lyd_c2_source_faith','=',Block((Entry('exists','=','religious_head_title'),))))
            is_owner=shape==[('has_variable','=','lyd_c2_owner_faith'),('exists','=','holder')]
            is_endorser=shape==[('has_variable','=','lyd_c2_endorser'),('exists','=','head_of_rite')]
            if is_retire or is_owner or is_endorser:
                if i>=len(block.entries) or block.entries[i]!=Entry('trigger_else','=',FALSE):
                    raise AssertionError('Missing-object branch must explicitly reject')
                i+=1
                if is_retire: out.extend(limit.entries[:2])
                out.extend(project_scope_guards(Block(e.value.entries[1:])).entries); continue
        out.append(Entry(e.key,e.operator,project_scope_guards(e.value) if isinstance(e.value,Block) else e.value))
    return Block(tuple(out))
def project_hidden_commit(block):
    out=[]
    for e in block.entries:
        if e.key=='hidden_effect' and e.value==Block((Entry('lyd_c2_event_commit_effect','=','yes'),)):
            out.extend(e.value.entries)
        else: out.append(Entry(e.key,e.operator,project_hidden_commit(e.value) if isinstance(e.value,Block) else e.value))
    return Block(tuple(out))

def world():
    actor=Scope('actor',{'is_alive':True,'is_adult':True,'traits':set()},{'lyd_c2_serial':7,
        'lyd_c2_player_yes':2,'lyd_c2_player_total':2})
    moving=Scope('moving'); source=Scope('source',{'rite_count':1}); target=Scope('target')
    head=Scope('head',{'is_alive':True,'is_adult':True,'traits':set(),'rite':moving})
    title=Scope('title',{'holder':head},{'lyd_c2_owned_head_title':1,'lyd_c2_owner_faith':source})
    target_title=Scope('targettitle'); source.values['religious_head_title']=title
    receiving=Scope('receiving',{'head_of_rite':head,'dormant':False},
        {'lyd_c2_proposal_owner':actor,'lyd_c2_lock_serial':7,'lyd_c2_target_total':0,
         'lyd_c2_target_quorum_value':0,'lyd_c2_endorser':head,'lyd_c2_holder_endorsed':1})
    actor.variables.update({'lyd_c2_source_singleton':1,'lyd_c2_source_main':moving,
        'lyd_c2_moving_rite':moving,'lyd_c2_source_faith':source,'lyd_c2_target_faith':target,
        'lyd_c2_source_head':head,'lyd_c2_source_head_title':title,'lyd_c2_protected_head_titles':[]})
    target.values['religious_head_title']=target_title
    return dict(actor=actor,moving=moving,source=source,target=target,head=head,title=title,
                target_title=target_title,receiving=receiving)

def run_checks(source,baseline=None):
    ast=parse_clausewitz((source/TRIG).read_text('utf-8-sig'))
    events=parse_clausewitz((source/EVENT).read_text('utf-8-sig'))
    cases=[]; mutants=[]
    def check(name,helper,change,expected,current='actor'):
        w=world(); change(w); ev=Evaluator(w['actor']); result=ev.block(definition(ast,helper),w[current])
        if result!=expected: raise AssertionError((name,result,expected))
        cases.append({'name':name,'accepted':result,'expected':expected,'missing_dereferences':0})
        return w,ev
    noop=lambda w:None
    retire='lyd_c2_source_retirement_trigger'
    check('owned_singleton_retirement',retire,noop,True)
    for key in ('lyd_c2_source_head','lyd_c2_source_head_title'):
        check('retire_missing_'+key,retire,lambda w,k=key:w['actor'].variables.pop(k),False)
    check('retire_faith_title_missing',retire,lambda w:w['source'].values.pop('religious_head_title'),False)
    check('retire_owner_missing',retire,lambda w:w['title'].variables.pop('lyd_c2_owner_faith'),False)
    check('retire_holder_missing',retire,lambda w:w['title'].values.pop('holder'),False)
    check('retire_ownership_tag_missing',retire,lambda w:w['title'].variables.pop('lyd_c2_owned_head_title'),False)
    check('retire_foreign_title',retire,lambda w:w['title'].variables.update(lyd_c2_owner_faith=w['target']),False)
    check('retire_changed_holder',retire,lambda w:w['title'].values.update(holder=w['actor']),False)
    check('retire_dead_head',retire,lambda w:w['head'].values.update(is_alive=False),False)
    check('retire_head_wrong_rite',retire,lambda w:w['head'].values.update(rite=w['receiving']),False)
    check('retire_multiple_rites',retire,lambda w:w['source'].values.update(rite_count=2),False)
    check('retire_not_singleton_snapshot',retire,lambda w:w['actor'].variables.update(lyd_c2_source_singleton=0),False)
    check('retire_wrong_main',retire,lambda w:w['actor'].variables.update(lyd_c2_source_main=w['receiving']),False)
    check('retire_captured_title_mismatch',retire,lambda w:w['source'].values.update(religious_head_title=w['target_title']),False)
    check('retire_receiving_title_same',retire,lambda w:w['target'].values.update(religious_head_title=w['title']),False)
    check('retire_receiving_no_title',retire,lambda w:w['target'].values.pop('religious_head_title'),True)
    receiver='lyd_c2_receiver_rite_quorum_trigger'
    w,_=check('receiver_holder_endorsed_all_humans',receiver,
        lambda w:w['head'].values.update(rite=w['receiving']),True,'receiving')
    def holder(change):
        return lambda w:(w['head'].values.update(rite=w['receiving']),change(w))
    check('receiver_missing_endorser',receiver,holder(lambda w:w['receiving'].variables.pop('lyd_c2_endorser')),False,'receiving')
    check('receiver_missing_current_head',receiver,holder(lambda w:w['receiving'].values.pop('head_of_rite')),False,'receiving')
    check('receiver_missing_both',receiver,holder(lambda w:(w['receiving'].values.pop('head_of_rite'),w['receiving'].variables.pop('lyd_c2_endorser'))),False,'receiving')
    for name,change in [('dead',lambda w:w['head'].values.update(is_alive=False)),
                        ('minor',lambda w:w['head'].values.update(is_adult=False)),
                        ('incapable',lambda w:w['head'].values['traits'].add('incapable')),
                        ('wrong_rite',lambda w:w['head'].values.update(rite=w['moving'])),
                        ('head_changed',lambda w:w['receiving'].variables.update(lyd_c2_endorser=w['actor'])),
                        ('no_holder_signature',lambda w:w['receiving'].variables.update(lyd_c2_holder_endorsed=0)),
                        ('human_no',lambda w:w['actor'].variables.update(lyd_c2_player_yes=1)),
                        ('wrong_owner',lambda w:w['receiving'].variables.update(lyd_c2_proposal_owner=w['head'])),
                        ('wrong_serial',lambda w:w['receiving'].variables.update(lyd_c2_lock_serial=6)),
                        ('dormant_zero',lambda w:w['receiving'].values.update(dormant=True))]:
        check('receiver_'+name,receiver,holder(change),False,'receiving')
    def scholar(w):
        w['receiving'].variables.update(lyd_c2_target_total=3,lyd_c2_target_quorum_value=0)
        w['receiving'].variables.pop('lyd_c2_endorser'); w['receiving'].values.pop('head_of_rite')
    check('receiver_scholar_quorum_without_holder',receiver,scholar,True,'receiving')
    check('receiver_scholar_below_quorum',receiver,lambda w:(scholar(w),w['receiving'].variables.update(lyd_c2_target_quorum_value=-1)),False,'receiving')
    post='lyd_c2_retirement_postcondition_trigger'
    def no_objects(w):
        for key in ('lyd_c2_source_head','lyd_c2_source_faith','lyd_c2_source_head_title'):
            w['actor'].variables.pop(key)
    check('post_no_retirement_marker_skips_objects',post,no_objects,True)
    check('post_marker_zero_skips_objects',post,lambda w:(no_objects(w),w['actor'].variables.update(lyd_c2_source_head_retired=0)),True)
    def retired(w):
        w['actor'].variables['lyd_c2_source_head_retired']=1
        w['source'].values.pop('religious_head_title');w['title'].values.pop('holder')
    check('post_completed_retirement',post,retired,True)
    check('post_dead_head_rejects',post,lambda w:(retired(w),w['head'].values.update(is_alive=False)),False)
    check('post_faith_still_has_title_rejects',post,lambda w:(retired(w),w['source'].values.update(religious_head_title=w['title'])),False)
    check('post_retired_title_still_held_rejects',post,lambda w:(retired(w),w['title'].values.update(holder=w['head'])),False)
    check('post_protected_holder_changed_rejects',post,lambda w:(retired(w),w['actor'].variables.update(lyd_c2_protected_head_titles=[Scope('protected',{'holder':w['actor']})])),False)
    check('post_protected_holder_preserved',post,lambda w:(retired(w),w['actor'].variables.update(lyd_c2_protected_head_titles=[Scope('protected',{'holder':w['head']})])),True)
    # Actual CT child conditions determine equality; Tenet values stay outside this universe.
    doctrine=definition(ast,'lyd_c2_same_main_doctrines_trigger')
    for left,right,expected in [({'head','clergy'},{'head','clergy'},True),({'head'},{'head','clergy'},False),
                                 ({'head','clergy'},{'head'},False),(set(),set(),True),({'new'},set(),False)]:
        a=Scope('source',{'main_rite':Scope('sm',{'doctrines':left,'tenets':{'A'}})})
        b=Scope('target',{'main_rite':Scope('tm',{'doctrines':right,'tenets':{'B'}})})
        actor=Scope('actor',{'target':b}); result=Evaluator(actor,('head','clergy','new')).block(doctrine,a)
        if result!=expected: raise AssertionError('Doctrine symmetric equality changed')
        cases.append({'name':'doctrine_'+','.join(sorted(left))+'__'+','.join(sorted(right)),
                      'expected':expected,'accepted':result,'tenet_difference_ignored':True})
    ready=definition(ast,'lyd_c2_ready_to_confirm_trigger')
    flags=('lyd_c2_source_signed','lyd_c2_snapshot_valid','lyd_c2_target_signed','lyd_c2_target_head_yes')
    def walk(block):
        for e in block.entries:
            yield e
            if isinstance(e.value,Block): yield from walk(e.value)
    def flag_guards(block):
        for n,e in enumerate(block.entries):
            if e.key=='trigger_if' and isinstance(e.value,Block):
                limit=e.value.entries[0].value
                if len(limit.entries)==1 and limit.entries[0].key=='has_variable' and limit.entries[0].value in flags:
                    if block.entries[n+1]!=Entry('trigger_else','=',FALSE): raise AssertionError('Optional signature must reject absence')
                    yield limit.entries[0].value,Block((e,block.entries[n+1]))
            if isinstance(e.value,Block): yield from flag_guards(e.value)
    for flag,guard in flag_guards(ready):
        for val,expected in [(None,False),(0,False),(1,True),(2,False)]:
            actor=Scope('actor',variables={} if val is None else {flag:val})
            result=Evaluator(actor).block(guard,actor)
            if result!=expected: raise AssertionError('Ready optional flag rule')
            cases.append({'name':flag+'_'+str(val),'accepted':result,'expected':expected})
    if len([c for c in cases if c['name'].startswith(flags)])!=16: raise AssertionError('Ready coverage')
    # Show that removing guards restores the observed RED, then kill permissive mutations.
    def mutation(name,mutated,helper,w,current,expect_reject=True):
        caught=False
        try:
            result=Evaluator(w['actor']).block(mutated,w[current])
            caught=(result != expect_reject)
        except UndefinedRead: caught=True
        if not caught: raise AssertionError('Security/preview mutant survived: '+name)
        mutants.append({'name':name,'rejected':True})
    base_receiver=definition(ast,receiver)
    receiver_text=(source/TRIG).read_text('utf-8-sig')
    for name,old,new,helper,setup,current,expected in [
        ('endorser_guard_removed','has_variable = lyd_c2_endorser exists = head_of_rite','always = yes',receiver,
            lambda w:w['receiving'].variables.pop('lyd_c2_endorser'),'receiving',False),
        ('head_existence_guard_removed','has_variable = lyd_c2_endorser exists = head_of_rite','has_variable = lyd_c2_endorser',receiver,
            lambda w:w['receiving'].values.pop('head_of_rite'),'receiving',False),
        ('retired_presence_guard_removed','has_variable = lyd_c2_source_head_retired','always = yes',post,no_objects,'actor',True),
        ('retirement_owner_guard_removed','has_variable = lyd_c2_owner_faith exists = holder','always = yes',retire,
            lambda w:w['title'].variables.pop('lyd_c2_owner_faith'),'actor',False),
        ('endorser_absence_authorized','trigger_else = { always = no }','trigger_else = { always = yes }',receiver,
            lambda w:w['receiving'].variables.pop('lyd_c2_endorser'),'receiving',False)]:
        mutated_ast=parse_clausewitz(receiver_text.replace(old,new))
        w=world();w['head'].values['rite']=w['receiving'] if current=='receiving' else w['moving'];setup(w)
        mutation(name,definition(mutated_ast,helper),helper,w,current,expected)
    if baseline:
        old_ast=parse_clausewitz((baseline/TRIG).read_text('utf-8-sig'))
        old_events=parse_clausewitz((baseline/EVENT).read_text('utf-8-sig'))
        if project_scope_guards(ast)!=old_ast: raise AssertionError('Defined-case original trigger AST changed')
        if project_hidden_commit(events)!=old_events: raise AssertionError('Actual event effects or option permissions changed')
        if definition(ast,'lyd_c2_ready_to_confirm_trigger')!=definition(old_ast,'lyd_c2_ready_to_confirm_trigger'):
            raise AssertionError('Ready four flags changed')
        # All effect files retain exact bytes, including native migration and success-only fees.
        for p in (baseline/'common/scripted_effects').glob('lyd_c2_*.txt'):
            if p.read_bytes()!=(source/'common/scripted_effects'/p.name).read_bytes(): raise AssertionError('Effect altered '+p.name)
        # AST protection kills actual permission, fees/effect placement and doctrine mutations.
        for name,changed in [('scholar_quorum_relaxed',receiver_text.replace('lyd_c2_target_quorum_value >= 0','lyd_c2_target_quorum_value >= -1')),
                             ('human_unanimity_relaxed',receiver_text.replace('var:lyd_c2_player_yes = var:lyd_c2_player_total','var:lyd_c2_player_yes >= 0')),
                             ('foreign_title_authorized',receiver_text.replace('var:lyd_c2_owner_faith = $ACTOR$.var:lyd_c2_source_faith','always = yes')),
                             ('doctrine_condition_removed',receiver_text.replace('rite_has_doctrine = prev','always = yes')),
                             ('missing_retirement_authorized',receiver_text.replace('trigger_else = { always = no }','trigger_else = { always = yes }'))]:
            try:
                if project_scope_guards(parse_clausewitz(changed))!=old_ast: raise AssertionError('AST changed')
            except AssertionError: mutants.append({'name':name,'rejected':True})
            else: raise AssertionError('AST mutant survived '+name)
        altered=(source/EVENT).read_text('utf-8-sig').replace('hidden_effect = { lyd_c2_event_commit_effect = yes }','hidden_effect = { always = yes }')
        if project_hidden_commit(parse_clausewitz(altered))==old_events: raise AssertionError('Missing commit mutant survived')
        mutants.append({'name':'real_commit_deleted','rejected':True})
    confirm=next(e.value for e in definition(events,'lyd.220').entries if e.key=='option' and any(t.key=='name' and t.value=='lyd_c2_confirm' for t in e.value.entries))
    if Entry('custom_tooltip','=','lyd_c2_confirm_tt') not in confirm.entries: raise AssertionError('Readable fee tooltip missing')
    if Entry('hidden_effect','=',Block((Entry('lyd_c2_event_commit_effect','=','yes'),))) not in confirm.entries: raise AssertionError('Hidden real commit missing')
    from gen_school_consent import LOC
    if LOC['lyd_c2_confirm_tt'] != ('合流费用为300金币、1500虔诚；自立为200金币、1000虔诚。成功后本派调整期五年；不改变政治领属。', 'Reunion costs 300 gold and 1500 piety; separation costs 200 gold and 1000 piety. A successful transition sets a five-year school cooldown and changes no political allegiance.'):
        raise AssertionError('Fee/affiliation tooltip changed')
    return {'result':'PASS_SOURCE_L0','cases':cases,'case_count':len(cases),'mutants':mutants,
            'mutation_count':len(mutants),'defined_case_full_trigger_AST_exact':baseline is not None,
            'event_effect_AST_exact_after_hidden_wrapper':baseline is not None,'effect_files_byte_identical':baseline is not None,
            'evaluation':'Generated trigger subset; eager sibling evaluation, guarded branches, CT evaluates real children and ignores only text metadata.',
            'native':'NOT_RUN','known_red':'set_parent_faith_third actual dynamic localization not verified by this evaluator.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path);p.add_argument('--report',type=Path)
    a=p.parse_args();result=run_checks(SOURCE,a.baseline)
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        with a.report.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('result','case_count','mutation_count','native')},indent=2))
if __name__=='__main__':main()
