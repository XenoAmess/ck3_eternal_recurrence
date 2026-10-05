"""Evaluate bounded read-only production AST policy, never CK3 native effects.

Synthetic scopes establish authorization logic only. They do not establish native
head creation, consent outcomes, native collection membership or save lifecycle.
"""
from pathlib import Path
from copy import deepcopy
from dataclasses import dataclass,field
import argparse,hashlib,json,sys
SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE.parent/'tools'))
from extract_auto_upgrade_buildings import Block,parse_clausewitz
from test_content_leadership import Corpus,one,scalar,walk,contains_direct_fragment
import content_data

@dataclass(eq=False)
class Scope:
    name:str
    fields:dict=field(default_factory=dict)
    variables:dict=field(default_factory=dict)
    lists:dict=field(default_factory=dict)

def world(detached=True,active=True):
    original=Scope('Faith32',{'faith_type':'lyd_common_faith'})
    target=Scope('Faith105',{'faith_type':'lyd_common_faith'}) if detached else original
    globals={'faith:lyd_common_faith':original}
    rites=[]
    for r in content_data.RITES:
        rite=Scope(r.script_id,{'faith':target,'doctrines':{'doctrine_no_head','doctrine_theocracy_lay_clergy'},'rite_counties':0,'allowed_gender':True})
        globals['rite:'+r.script_id]=rite
        if not detached or r.slug=='zhuxi':rites.append(rite)
    main=globals['rite:lyd_rite_zhuxi' if detached else 'rite:lyd_rite_kongmen']
    target.fields.update(main_rite=main,rites=rites,characters=[],challengers=[],religion='religion:confucianism_religion',doctrines={'doctrine_no_head'})
    actor=Scope('31254',{'faith':target,'rite':main,'religion':'religion:confucianism_religion','is_ai':False,'is_alive':True,'is_adult':True,'is_landed':True,'is_imprisoned':False,'traits':set(),'flags':{'lyd_enabled'},'learning':20,'highest_held_title_tier':3})
    npc=Scope('65865',dict(actor.fields));npc.fields.update(is_ai=True)
    political=[Scope('2230',{'holder':actor,'is_head_of_faith':False}),Scope('2231',{'holder':actor,'is_head_of_faith':False})]
    actor.fields['held_titles']=political; npc.fields['held_titles']=[]
    target.fields['characters']=[actor,npc]
    main.fields.update(head_of_rite=actor if detached else None,rite_counties=1)
    actor.variables.update(lyd_i3b_faith=target,lyd_i3b_main=main,lyd_i3b_serial=7,lyd_i3b_nonce=9,lyd_i3b_phase=2,lyd_i3b_authority_mode=int(detached),lyd_i3b_result_authority_mode=int(detached))
    if active:actor.variables['lyd_i3b_active']=1
    if detached:actor.variables.update(lyd_i3b_required_native_hor=actor,lyd_i3b_result_native_hor=actor)
    actor.lists.update(lyd_i3b_rites=rites[:],lyd_i3b_members=[actor,npc],lyd_i3b_political_titles=political[:])
    for rite in rites:
        live=rite is main
        rite.variables.update(lyd_i3b_owner=actor,lyd_i3b_serial=7,lyd_i3b_counties=int(live),lyd_i3b_dormant=int(not live),lyd_i3b_total=2 if live else 0,lyd_i3b_yes=2 if live else 0,lyd_i3b_signed=int(live))
        if live:rite.variables['lyd_i3b_delegate']=actor
    for member in target.fields['characters']:
        member.variables.update(lyd_i3b_member_owner=actor,lyd_i3b_member_serial=7,lyd_i3b_member_rite=main,lyd_i3b_was_elector=1,lyd_i3b_was_player=int(not member.fields['is_ai']),lyd_i3b_player_yes=int(not member.fields['is_ai']),lyd_i3b_vote=1)
    if not active:
        for rite in rites:rite.variables.clear()
        for member in target.fields['characters']:member.variables.clear()
        actor.lists.clear()
    env={'ACTOR':actor,'scope:lyd_i3b_actor':actor,'scope:lyd_i3b_event_serial':7,'scope:lyd_i3b_event_nonce':9,'scope:lyd_i3b_event_phase':2}
    return actor,npc,target,main,globals,env

class PolicyAST:
    """Only the exact trigger vocabulary exercised here; unknown words fail."""
    def __init__(self,definitions,actor,globals,env):self.defs=definitions;self.root=actor;self.globals=globals;self.env=env
    def resolve(self,token,current):
        if token is None:return None
        if token in self.globals:return self.globals[token]
        if token.startswith('religion:'):return token
        if token in self.env:return self.env[token]
        if token in {'yes','no'}:return token=='yes'
        if token=='tier_duchy':return 3
        try:return int(token)
        except ValueError:pass
        parts=token.split('.')
        obj=current
        for i,part in enumerate(parts):
            if part in {'this','root'}:obj=current if part=='this' else self.root
            elif part.startswith('$'):obj=self.env.get(part.strip('$'))
            elif part.startswith('scope:'):obj=self.env.get(part)
            elif part.startswith('var:'):obj=obj.variables.get(part[4:]) if isinstance(obj,Scope) else None
            elif isinstance(obj,Scope):obj=obj.fields.get(part)
            else:return None
        return obj
    def run(self,name,current=None):return self.block(self.defs[name],current or self.root)
    def block(self,body,current):
        results=[];branch=None
        for e in body.entries:
            if e.key=='trigger_if':
                limit=one(e.value,'limit');branch=self.block(limit,current)
                results.append(not branch or self.block(Block([x for x in e.value.entries if x.key!='limit']),current));continue
            if e.key=='trigger_else':
                assert branch is not None
                results.append(branch or self.block(e.value,current));branch=None;continue
            results.append(self.entry(e,current))
        return all(results)
    def entry(self,e,current):
        key,value=e.key,e.value
        if key=='save_temporary_scope_as':self.env['scope:'+value]=current;return True
        if key in {'AND','NOT','NOR','OR'}:
            if key in {'AND','NOT'}:
                conjunction=self.block(value,current)
                return conjunction if key=='AND' else not conjunction
            vals=[self.entry(x,current) for x in value.entries]
            return {'AND':lambda:all(vals),'NOT':lambda:not all(vals),'NOR':lambda:not any(vals),'OR':lambda:any(vals)}[key]()
        if key in self.defs:
            previous=self.env.copy()
            if isinstance(value,Block):
                for p in value.entries:self.env[p.key]=self.resolve(p.value,current)
            result=self.run(key,current)
            self.env.clear();self.env.update(previous)
            return result if isinstance(value,Block) or value=='yes' else not result
        if key.startswith('any_'):
            if key=='any_in_list':items=current.lists.get(scalar(value,'variable'),[])
            else:items=current.fields.get({'any_faith_rite':'rites','any_faith_character':'characters','any_held_title':'held_titles','any_religious_head_challenger':'challengers'}[key],[])
            predicate=Block([x for x in value.entries if x.key!='variable'])
            return any(self.block(predicate,item) for item in items)
        if isinstance(value,Block):
            target=self.resolve(key,current)
            return target is not None and self.block(value,target)
        if key=='always':left=True
        elif key=='exists':return self.resolve(value,current) is not None
        elif key=='has_variable':return value in current.variables
        elif key=='has_trait':return value in current.fields.get('traits',set())
        elif key=='has_character_flag':return value in current.fields.get('flags',set())
        elif key in {'has_doctrine','rite_has_doctrine'}:return value in current.fields.get('doctrines',set())
        elif key=='rite_has_allowed_gender_for_clergy':return current.fields['allowed_gender']
        elif key=='pam_title_is_antipope_office_trigger':left='pam_antipope_office' in current.variables
        elif key=='lyd_i3b_quorum_value':left=3*current.variables.get('lyd_i3b_yes',0)-2*current.variables.get('lyd_i3b_total',0)
        elif key in {'pam_is_antipope_trigger','pam_is_antipope_sponsor_trigger'}:
            titles=current.fields['faith'].fields.get('challengers',[])
            left=any((t.fields.get('holder') if key=='pam_is_antipope_trigger' else (t.fields.get('challenger_sponsor').fields.get('holder') if t.fields.get('challenger_sponsor') else None)) is current for t in titles)
        else:left=self.resolve(key,current)
        right=self.resolve(value,current)
        if right is None and not any(x in value for x in [':','.','$']) and value not in {'this','root'}:right=value
        if e.operator=='=':return left is not None and left==right
        if e.operator=='!=':return left is not None and left!=right
        if left is None or right is None:return False
        return {'>':lambda:left>right,'>=':lambda:left>=right,'<':lambda:left<right,'<=':lambda:left<=right}[e.operator]()

def evaluate(definitions,entry,detached=True,active=True,mutate=None):
    w=world(detached,active)
    if mutate:mutate(*w)
    return PolicyAST(definitions,w[0],w[4],w[5]).run(entry),w

def cases():
    result=[]
    def add(name,entry,expected,mutate=None,detached=True,active=True):result.append((name,entry,expected,mutate,detached,active))
    actor='lyd_i3b_actor_trigger';begin='lyd_i3b_can_begin_trigger';current='lyd_i3b_current_trigger';ready='lyd_i3b_ready_trigger';event='lyd_i3b_event_context_trigger';post='lyd_i3b_native_authority_postcondition_trigger'
    add('common32 qualified scholar without native HoR',begin,True,detached=False,active=False)
    add('detached105 actual native HoR',begin,True,active=False)
    add('same faith_type does not authorize Faith105 without HoR',begin,False,lambda a,n,f,r,g,e:r.fields.update(head_of_rite=None),active=False)
    add('different native HoR',begin,False,lambda a,n,f,r,g,e:r.fields.update(head_of_rite=n),active=False)
    add('foreign main rite',begin,False,lambda a,n,f,r,g,e:(g.pop('rite:'+r.name),r.fields.update(head_of_rite=a)),active=False)
    add('mixed foreign rite',begin,False,lambda a,n,f,r,g,e:f.fields['rites'].append(Scope('foreign',{'faith':f})),active=False)
    add('mixed foreign rite cannot admit detached actor authority',actor,False,lambda a,n,f,r,g,e:f.fields['rites'].append(Scope('foreign',{'faith':f})))
    add('existing native HoF',begin,False,lambda a,n,f,r,g,e:f.fields.update(religious_head=n),active=False)
    add('existing empty HoF title',begin,False,lambda a,n,f,r,g,e:f.fields.update(religious_head_title=Scope('foreignHoF')),active=False)
    add('Faith has temporal doctrine despite no-head rites',begin,False,lambda a,n,f,r,g,e:f.fields.update(doctrines={'doctrine_temporal_head'}),active=False)
    add('foreign native challenger without LYD metadata',begin,False,lambda a,n,f,r,g,e:f.fields['challengers'].append(Scope('foreignChallenge',{'holder':n})),active=False)
    add('holds foreign Faith HoF title',actor,False,lambda a,n,f,r,g,e:a.fields['held_titles'].append(Scope('foreignOffice',{'holder':a,'is_head_of_faith':True})))
    add('holds stock challenger office from different Faith',actor,False,lambda a,n,f,r,g,e:a.fields['held_titles'].append(Scope('foreignStockOffice',{'holder':a,'is_head_of_faith':False},{'pam_antipope_office':1})))
    add('holds partial LYD challenger office without actor pointer',actor,False,lambda a,n,f,r,g,e:a.fields['held_titles'].append(Scope('partialLYDOffice',{'holder':a,'is_head_of_faith':False},{'lyd_c3_owned_claim_title':1})))
    add('holds native challenger office',actor,False,lambda a,n,f,r,g,e:f.fields['challengers'].append(Scope('foreignChallenge',{'holder':a})))
    add('sponsors native challenger office',actor,False,lambda a,n,f,r,g,e:f.fields['challengers'].append(Scope('foreignChallenge',{'holder':n,'challenger_sponsor':a.fields['held_titles'][0]})))
    add('owns previous LYD challenger title',actor,False,lambda a,n,f,r,g,e:a.variables.update(lyd_c3_claim_title=Scope('ownedChallenge')))
    add('political claim without office is no mandate and no office veto',actor,True,lambda a,n,f,r,g,e:a.variables.update(lyd_c3_claim_faith=f))
    add('common captured route valid',current,True,detached=False)
    add('detached captured route valid',current,True)
    add('missing captured mode fails closed',current,False,lambda a,n,f,r,g,e:a.variables.pop('lyd_i3b_authority_mode'))
    add('forged common mode on same-type Faith105',current,False,lambda a,n,f,r,g,e:a.variables.update(lyd_i3b_authority_mode=0))
    add('forged detached mode on common Faith32',current,False,lambda a,n,f,r,g,e:a.variables.update(lyd_i3b_authority_mode=1),detached=False)
    add('actual HoR changes during round',current,False,lambda a,n,f,r,g,e:r.fields.update(head_of_rite=n))
    add('captured HoR substituted',current,False,lambda a,n,f,r,g,e:a.variables.update(lyd_i3b_required_native_hor=n))
    add('captured HoR missing',current,False,lambda a,n,f,r,g,e:a.variables.pop('lyd_i3b_required_native_hor'))
    add('new live human outside captured roster',current,False,lambda a,n,f,r,g,e:f.fields['characters'].append(Scope('newHuman',dict(n.fields))))
    add('member owner changes',current,False,lambda a,n,f,r,g,e:n.variables.update(lyd_i3b_member_owner=n))
    add('member serial changes',current,False,lambda a,n,f,r,g,e:n.variables.update(lyd_i3b_member_serial=6))
    add('rite serial changes',current,False,lambda a,n,f,r,g,e:r.variables.update(lyd_i3b_serial=6))
    add('member eligibility changes',current,False,lambda a,n,f,r,g,e:n.fields.update(learning=14))
    add('current ritual county drift',current,False,lambda a,n,f,r,g,e:r.fields.update(rite_counties=2))
    add('C2 foreign proposal lock',current,False,lambda a,n,f,r,g,e:r.variables.update(lyd_c2_proposal_owner=n))
    add('all detached mandates satisfied',ready,True)
    add('all common mandates satisfied',ready,True,detached=False)
    add('two thirds below threshold',ready,False,lambda a,n,f,r,g,e:r.variables.update(lyd_i3b_yes=1))
    add('missing human consent',ready,False,lambda a,n,f,r,g,e:a.variables.update(lyd_i3b_player_yes=0))
    add('missing representative signature',ready,False,lambda a,n,f,r,g,e:r.variables.update(lyd_i3b_signed=0))
    add('old political title transferred',ready,False,lambda a,n,f,r,g,e:a.fields['held_titles'][0].fields.update(holder=n))
    add('exact callback accepted',event,True)
    add('old callback nonce rejected',event,False,lambda a,n,f,r,g,e:e.update({'scope:lyd_i3b_event_nonce':8}))
    add('old callback serial rejected',event,False,lambda a,n,f,r,g,e:e.update({'scope:lyd_i3b_event_serial':6}))
    add('old callback phase rejected',event,False,lambda a,n,f,r,g,e:e.update({'scope:lyd_i3b_event_phase':1}))
    add('detached native HoR preserved postcondition',post,True)
    add('detached native HoR changed postcondition',post,False,lambda a,n,f,r,g,e:r.fields.update(head_of_rite=n))
    add('common postcondition does not invent a HoR',post,True,detached=False)
    def school_main(a,n,f,r,g,e,slug,wrong_head=False):
        chosen=g['rite:lyd_rite_'+slug]
        r.fields['head_of_rite']=None
        chosen.fields.update(head_of_rite=n if wrong_head else a,rite_counties=1)
        f.fields.update(main_rite=chosen,rites=[chosen])
        a.fields['rite']=chosen;n.fields['rite']=chosen
    for school in content_data.RITES:
        add('owned detached '+school.slug+' actual HoR allowed',begin,True,lambda a,n,f,r,g,e,s=school.slug:school_main(a,n,f,r,g,e,s),active=False)
        add('owned detached '+school.slug+' different HoR denied',begin,False,lambda a,n,f,r,g,e,s=school.slug:school_main(a,n,f,r,g,e,s,True),active=False)
    return result

def source_graph(c):
    begin=one(c.effects['lyd_i3b_begin_effect'],'if')
    assert contains_direct_fragment(one(begin,'limit'),'lyd_i3b_can_begin_trigger = yes')
    branch=[e.value for e in begin.entries if e.key=='if' and contains_direct_fragment(one(e.value,'limit'),'faith = faith:lyd_common_faith')]
    assert len(branch)==1;branch=branch[0]
    assert contains_direct_fragment(branch,'set_variable = { name = lyd_i3b_authority_mode value = 0 }')
    assert contains_direct_fragment(one(begin,'else'),'set_variable = { name = lyd_i3b_authority_mode value = 1 } set_variable = { name = lyd_i3b_required_native_hor value = rite.head_of_rite }')
    commit=one(c.effects['lyd_i3b_commit_effect'],'if')
    assert contains_direct_fragment(one(commit,'limit'),'lyd_i3b_native_admitted_trigger = yes')
    keys=[e.key for e in commit.entries]
    assert keys.index('lyd_i3b_capture_authority_receipt_effect')<keys.index('var:lyd_i3b_faith')
    assert contains_direct_fragment(one(one(commit,'if'),'limit'),'lyd_i3b_native_authority_postcondition_trigger = yes')
    failures=one(commit,'else')
    assert contains_direct_fragment(failures,'else_if = { limit = { NOT = { lyd_i3b_native_authority_postcondition_trigger = yes } } set_variable = { name = lyd_i3b_result_code value = 7 } }')
    close=c.effects['lyd_i3b_close_effect']
    assert not any(e.key=='remove_variable' and str(e.value).startswith('lyd_i3b_result_') for e,_ in walk(close))
    assert not any(e.key in {'set_head_of_rite','set_religious_head','set_government_type'} for b in c.effects.values() for e,_ in walk(b))
    return True

def main():
    args=argparse.ArgumentParser();args.add_argument('--report',type=Path);options=args.parse_args()
    c=Corpus();matrix=[]
    for name,entry,expected,mutation,detached,active in cases():
        actual,_=evaluate(c.triggers,entry,detached,active,mutation)
        matrix.append({'name':name,'entry':entry,'expected':expected,'actual':actual,'pass':actual==expected})
    assert all(r['pass'] for r in matrix),[r for r in matrix if not r['pass']]
    source_graph(c)
    path=SOURCE/'common/scripted_triggers/lyd_i3b_institution_triggers.txt';original=path.read_text(encoding='utf-8-sig')
    # Bind the destructive identity mutant to its actual positive presence guard.
    # Removing both comparisons preserves the new missing-target rejection and
    # still tests that captured HoR substitution cannot authorize the actor.
    captured_guards=[e.value for e,_ in walk(c.triggers['lyd_i3b_captured_authority_trigger'])
                     if e.key=='trigger_if' and contains_direct_fragment(one(e.value,'limit'),
                        'has_variable = lyd_i3b_required_native_hor exists = var:lyd_i3b_main.head_of_rite')]
    assert len(captured_guards)==1,('captured HoR positive guard',len(captured_guards))
    captured_guard=captured_guards[0]
    assert contains_direct_fragment(captured_guard,
        'this = var:lyd_i3b_required_native_hor var:lyd_i3b_main.head_of_rite = var:lyd_i3b_required_native_hor')
    changes=[
        ('detached current HoR equality','    this = rite.head_of_rite\n',''),
        ('all-owned Faith rites','    NOT = { any_faith_rite = { NOT = { lyd_i3b_owned_rite_trigger = yes } } }\n',''),
        ('held foreign HoF title','            is_head_of_faith = yes\n',''),
        ('held stock challenger office across Faith','            pam_title_is_antipope_office_trigger = yes\n',''),
        ('held partial LYD challenger office','            has_variable = lyd_c3_owned_claim_title\n',''),
        ('native challenge collection','    NOT = { any_religious_head_challenger = { always = yes } }\n',''),
        ('native holder guard','    pam_is_antipope_trigger = no\n',''),
        ('native sponsor guard','    pam_is_antipope_sponsor_trigger = no\n',''),
        ('owned challenge title guard','    NOT = { has_variable = lyd_c3_claim_title }\n',''),
        ('captured authority at callbacks','    lyd_i3b_captured_authority_trigger = yes\n',''),
        ('captured HoR exact identity','                this = var:lyd_i3b_required_native_hor\n                var:lyd_i3b_main.head_of_rite = var:lyd_i3b_required_native_hor\n',''),
        ('post HoR actual reread','            var:lyd_i3b_main.head_of_rite = var:lyd_i3b_result_native_hor\n',''),
        ('Faith native head absence','    NOT = { exists = religious_head }\n',''),
        ('Faith native title absence','    NOT = { exists = religious_head_title }\n',''),
        ('Faith no-head doctrine','    has_doctrine = doctrine_no_head\n',''),
        ('each school quorum','lyd_i3b_quorum_value >= 0','always = yes'),
        ('every human consent','var:lyd_i3b_player_yes = 1','always = yes'),
        ('each representative signature','var:lyd_i3b_signed = 1','always = yes'),
        ('exact nonce','        var:lyd_i3b_nonce = scope:lyd_i3b_event_nonce\n','        always = yes\n'),
        ('exact serial','        var:lyd_i3b_serial = scope:lyd_i3b_event_serial\n','        always = yes\n'),
    ]
    mutants=[]
    for name,before,after in changes:
        assert original.count(before)==1,(name,original.count(before))
        mutated=original.replace(before,after);defs=dict(c.triggers)
        defs.update({e.key:e.value for e in parse_clausewitz(mutated).entries if isinstance(e.value,Block)})
        if name=='captured HoR exact identity':
            original_identity={('this','lyd_i3b_required_native_hor'),('var:lyd_i3b_main.head_of_rite','lyd_i3b_required_native_hor')}
            assert not any((e.key,str(e.value).removeprefix('var:')) in original_identity
                           for e,_ in walk(defs['lyd_i3b_captured_authority_trigger'])), 'captured exact identities survived mutation'
            mutated_guard=[e.value for e,_ in walk(defs['lyd_i3b_captured_authority_trigger'])
                           if e.key=='trigger_if' and contains_direct_fragment(one(e.value,'limit'),
                              'has_variable = lyd_i3b_required_native_hor exists = var:lyd_i3b_main.head_of_rite')]
            assert len(mutated_guard)==1 and one(mutated_guard[0],'limit')==one(captured_guard,'limit'), 'presence guard changed instead of identity'
        rejected=[]
        for case,entry,expected,mutation,detached,active in cases():
            actual,_=evaluate(defs,entry,detached,active,mutation)
            if actual!=expected:rejected.append(case)
        assert rejected,('undetected source mutant',name)
        if name=='captured HoR exact identity':
            assert 'captured HoR substituted' in rejected, 'captured substitution counterexample no longer detects identity mutant'
        mutants.append({'mutation':name,'detected_by_cases':rejected,'rejected':True,'mutated_runtime_sha256':hashlib.sha256(mutated.encode('utf-8')).hexdigest()})
    report={'schema':'lyd.i3b.detached-policy-ast.v1','status':'SOURCE_L0_PASS','scope':'bounded read-only AST policy, synthetic data; no native effects executed','runtime_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'matrix':matrix,'source_effect_graph_pass':True,'mutants':mutants,'native_positive':'NOT_RUN','native_creation':'NOT_RUN','native_save_reload':'NOT_RUN'}
    if options.report:
        assert not options.report.exists();options.report.parent.mkdir(parents=True,exist_ok=True);options.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'policy_cases':len(matrix),'source_mutants_rejected':len(mutants),'native':'NOT_RUN'}))

if __name__=='__main__':main()
