"""Read saved public receipts; never call SDK, game, native function or screen.

Supported arithmetic is only the reviewed ordinary nonnegative exact .3 path.
Each evidence admission gate is explicit. Missing data never becomes zero.
"""
from pathlib import Path
import argparse, hashlib, json, re, sys

Q=100000
I32=2**31-1
I64=2**63-1
EXE='94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6'
STEP=re.compile(r'merge-armies-(0|[1-9][0-9]*)-with-(0|[1-9][0-9]*)\Z')

class Unavailable(ValueError):pass
class Mismatch(ValueError):pass
class Unsupported(ValueError):pass

def integer(v,name,lo=0,hi=I64):
    if type(v) is not int or not lo<=v<=hi:raise Unavailable(f'{name}: explicit integer [{lo},{hi}] required, got {v!r}')
    return v
def require(ok,message):
    if not ok:raise Mismatch(message)
def same_json(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,list):return len(a)==len(b) and all(same_json(x,y) for x,y in zip(a,b))
    if isinstance(a,dict):return a.keys()==b.keys() and all(same_json(a[k],b[k]) for k in a)
    return a==b
def raw_pair(row,key,scale=Q,negative=False):
    raw=integer(row.get(key+'_raw'),key+'_raw',-I64-1 if negative else 0)
    require(type(row.get(key+'_scale')) is int and row[key+'_scale']==scale,key+': missing/wrong scale')
    return raw
def json_unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise Unavailable('duplicate JSON key '+k)
        d[k]=v
    return d
def parse(raw):return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=json_unique)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_new(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def fixed_trace(d_weight,s_weight,d_stock,s_stock,capacity,actual):
    for n,v in [('Dweight',d_weight),('Sweight',s_weight),('Dstock',d_stock),('Sstock',s_stock),('postcapacity',capacity),('poststock',actual)]:integer(v,n)
    total=d_weight+s_weight
    if not 0<total<=I64:raise Unsupported('zero total weight or signed64 overflow: special native path is unmodelled')
    trace=[];blend=0
    for role,w,stock in [('D',d_weight,d_stock),('S',s_weight,s_stock)]:
        if w==0:
            trace.append({'role':role,'weight_raw':0,'original_stock_raw':stock,'positive_weight_guard':False,'operation':'skip item; native does not divide/multiply a zero-weight item','share_raw':None,'contribution_raw':0,'accumulator_after_raw':blend});continue
        if w+0x53e2d6238da3>0xa7c5ac471b46:raise Unsupported(f'{role}: large-weight native divide branch unmodelled')
        numerator=w*Q;share,remainder=divmod(numerator,total)
        if any(v+0xb504f333>0x16a09e666 for v in (share,stock)):raise Unsupported(f'{role}: large-operand native multiply branch unmodelled')
        product=share*stock;contribution,mul_remainder=divmod(product,Q)
        if product>I64 or blend+contribution>I64:raise Unsupported('ordinary signed64 product/accumulator bounds exceeded')
        blend+=contribution
        trace.append({'role':role,'weight_raw':w,'original_stock_raw':stock,'positive_weight_guard':True,'divide_numerator_raw':numerator,'divide_denominator_raw':total,'share_raw':share,'divide_remainder_raw':remainder,'multiply_product_raw':product,'multiply_divisor_raw':Q,'contribution_raw':contribution,'multiply_remainder_raw':mul_remainder,'accumulator_after_raw':blend})
    expected=min(max(blend,0),capacity)
    condition='upper-clamp' if blend>capacity else 'equal-to-capacity-without-strict-upper-clamp' if blend==capacity else 'below-capacity'
    return {'domain':'reviewed ordinary nonnegative exact3 direct divide/multiply; no special branch approximation','scale':Q,'role_order':['D','S'],'total_weight_raw':total,'operations':trace,'preclamp_raw':blend,'observed_post_capacity_raw':capacity,'observed_post_stock_raw':actual,'expected_post_stock_raw':expected,'arithmetic_match':actual==expected,'arithmetic_condition':condition,'upper_clamp_required_by_arithmetic':blend>capacity,'upper_clamp_arithmetic_match':blend>capacity and actual==capacity,'note':'Actual post capacity is read after native commander selection; before capacities and commander quality are never used to calculate it.'}

class Reviewer:
    def __init__(self,manifest_path):
        self.mp=Path(manifest_path).resolve();self.manifest=parse(self.mp.read_bytes());self.inputs=[];self.checks=[];self.loaded={}
        self.report={'schema':'xar.episode04.actual-merge-receipt-review.v1','manifest':{'path':str(self.mp),'sha256':sha(self.mp)},'analysis_script':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'sdk_calls':0,'game_actions':0,'screen_actions':0,'new_live_execution_credit':0,'inputs':self.inputs,'checks':self.checks,'arithmetic':None}
    def check(self,name,fn):
        try:
            v=fn();self.checks.append({'id':name,'status':'verified','details':v});return v
        except (Unavailable,Mismatch,Unsupported,KeyError,TypeError,OSError) as e:
            self.checks.append({'id':name,'status':'unsupported' if isinstance(e,Unsupported) else 'mismatch' if isinstance(e,Mismatch) else 'unavailable','reason':str(e)});return None
    def load(self,label):
        spec=self.manifest.get('receipts',{}).get(label)
        if not isinstance(spec,str) or not spec:raise Unavailable(label+': file path required')
        p=Path(spec);p=p if p.is_absolute() else self.mp.parent/p;p=p.resolve();raw=p.read_bytes();w=parse(raw)
        if not isinstance(w,dict):raise Unavailable(label+': JSON object required')
        for flag in ['is_error','isError']:
            if flag in w:require(type(w[flag]) is bool,label+': malformed error flag')
        if w.get('is_error') is True or w.get('isError') is True or isinstance(w.get('sdk_result'),dict) and w['sdk_result'].get('isError') is True:raise Unavailable(label+': saved error receipt')
        b=w.get('body',w.get('structuredContent',w))
        if not isinstance(b,dict):raise Unavailable(label+': direct public body/body/structuredContent object required')
        self.inputs.append({'label':label,'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'request':w.get('request'),'recorded_at':w.get('at')})
        self.loaded[label]={'body':b,'wrapper':w};return {'loaded':True,'body_keys':list(b),'path':str(p)}
    def body(self,label):
        if label not in self.loaded:raise Unavailable(label+': receipt was not loaded')
        return self.loaded[label]['body']
    def snapshot(self,label):
        b=self.body(label)
        require(b.get('paused') is True and b.get('map_ready') is True,label+': fresh paused map required')
        for key in ['snapshot_id','episode_run_id']:
            if not isinstance(b.get(key),str) or not b[key]:raise Unavailable(label+': '+key+' required')
        integer(b.get('revision'),label+'.revision');integer(b.get('native_revision'),label+'.native_revision',1)
        integer(b.get('date_raw'),label+'.date_raw')
        actor=b.get('played_character',{}).get('character_id');integer(actor,label+'.actor',0,I32)
        for k in ['active_event','pending_character_interaction']:
            require(k in b and b[k] is None,label+': unknown/nonempty '+k)
        rows=b.get('player_armies')
        if not isinstance(rows,list):raise Unavailable(label+': player_armies array required')
        ids=[]
        for a in rows:
            if not isinstance(a,dict):raise Unavailable(label+': malformed army row')
            aid=integer(a.get('army_id'),label+'.army_id',0,I32)
            if a.get('controllable') is True:ids.append(aid)
        require(len(ids)==len(set(ids)),label+': duplicate controllable FullID')
        return {'snapshot_id':b['snapshot_id'],'revision':b['revision'],'native_revision':b['native_revision'],'date_raw':b['date_raw'],'episode_run_id':b['episode_run_id'],'actor_id':actor,'controllable_ids':sorted(ids)}
    def frame(self,b,expected,label,commander=False):
        for key in ['snapshot_id','revision','native_revision']:
            require(same_json(b.get('queried_'+key),expected[key]),label+': queried_'+key+' differs from bracket frame')
        integer(b.get('query_sequence'),label+'.query_sequence',1)
        require(b.get('accepted') is True,label+': accepted true required')
        if commander:
            require(b.get('status')=='completed' and b.get('read_only') is True,label+': completed readonly commander envelope required')
            require(same_json(b.get('snapshot_revision'),expected['native_revision']) and same_json(b.get('date_raw'),expected['date_raw']),label+': commander native envelope differs')
        else:
            require(b.get('status')=='available',label+': available Strength envelope required')
            src=b.get('source')
            if not isinstance(src,dict):raise Unavailable(label+': source object required')
            for k in ['snapshot_id','revision','native_revision','date_raw']:require(same_json(src.get(k),expected[k]),label+': source '+k+' differs')
            require(src.get('paused') is True,label+': Strength source must be paused')
        return {k:b.get('queried_'+k) for k in ['snapshot_id','revision','native_revision']}|{'query_sequence':b['query_sequence']}
    def army_snapshot(self,label,aid):
        matches=[a for a in self.body(label)['player_armies'] if a.get('army_id')==aid]
        require(len(matches)==1,label+f': exactly one public{aid} snapshot row required')
        a=matches[0];require(a.get('controllable') is True,label+f': public{aid} not controllable')
        integer(a.get('owner_character_id'),'owner',0,I32);integer(a.get('current_province_id'),'province',1,I32)
        require(a.get('in_combat') is False and a.get('retreating') is False,label+': explicit noncombat/nonretreat required')
        require(a.get('army_state')!='retreating' and a.get('army_state_code')!=6,label+': state contradicts nonretreat')
        return a
    def strength(self,label,aid):
        b=self.body(label);rows=b.get('army_strengths')
        if not isinstance(rows,list):raise Unavailable(label+': army_strengths array required')
        matches=[a for a in rows if isinstance(a,dict) and a.get('army_id')==aid]
        require(len(matches)==1,label+f': exactly one public{aid} Strength row required')
        a=matches[0];require(a.get('status')=='available',label+f': public{aid} status must be available')
        integer(a.get('army_id'),'Strength public CUnit FullID',0,I32)
        integer(a.get('native_carmy_id'),'native CArmy FullID',0,I32)
        require(a.get('scope_role')=='player',label+': selected army must be player scope')
        current=integer(a.get('current_soldiers'),'current',0,I32);maximum=integer(a.get('maximum_soldiers'),'maximum',0,I32)
        require(current<=maximum,label+': current exceeds maximum')
        rr=a.get('regiment_strengths')
        if not isinstance(rr,list):raise Unavailable(label+': full regiment_strengths missing')
        regiment_count=integer(a.get('regiment_count'),'regiment_count',0,I32);require(len(rr)==regiment_count,label+': regiment collection incomplete')
        byid={}
        for r in rr:
            if not isinstance(r,dict):raise Unavailable(label+': malformed regiment row')
            rid=integer(r.get('army_regiment_id'),'ArmyRegiment FullID',0,I32);require(rid not in byid,label+': duplicate full regiment ID')
            require(type(r.get('scale')) is int and r['scale']==1,label+': regiment scale must be1')
            cur=integer(r.get('current_soldiers'),'regiment current',0,I32);mx=integer(r.get('maximum_soldiers'),'regiment maximum',0,I32)
            require(cur<=mx,label+': regiment current exceeds maximum');byid[rid]={'current_soldiers':cur,'maximum_soldiers':mx}
        require(sum(r['current_soldiers'] for r in byid.values())==current,label+': complete current row sum differs from native-verified aggregate')
        require(sum(r['maximum_soldiers'] for r in byid.values())==maximum,label+': complete maximum row sum differs from aggregate')
        return a,byid
    def commander(self,label,aid,native,owner,frame):
        b=self.body(label);self.frame(b,frame,label,True);c=b.get('army_commander_candidates')
        if not isinstance(c,dict):raise Unavailable(label+': commander context missing')
        require(c.get('status') in ['available','partial'],label+': commander context unavailable')
        require(same_json(c.get('army_id'),aid) and same_json(c.get('native_carmy_id'),native) and same_json(c.get('owner_character_id'),owner),label+': current commander army/owner FullID mismatch')
        require(same_json(c.get('snapshot_revision'),frame['native_revision']) and same_json(c.get('date_raw'),frame['date_raw']),label+': commander nested frame mismatch')
        cur=c.get('current_commander')
        if not isinstance(cur,dict):raise Unavailable(label+': current_commander missing')
        if cur.get('status')=='available':integer(cur.get('character_id'),'commander FullID',0,I32)
        elif cur.get('status')=='absent':require(cur.get('character_id') is None,label+': absent commander has an ID')
        else:raise Unavailable(label+': current commander unavailable; absence cannot be guessed')
        return {'public_cunit_id':aid,'native_carmy_id':native,'current_commander':cur,'candidate_collection_complete':c.get('candidate_collection_complete'),'context_status':c.get('status'),'source_frame':frame,'quality_used_to_predict_capacity':False}
    def clock(self,a,frame,label):
        c=a.get('army_update_clock_v1')
        if not isinstance(c,dict) or c.get('status')!='available' or c.get('ready') is not True:raise Unavailable(label+': available ready clock required')
        require(c.get('current_date_raw')==frame['date_raw'],label+': clock current date differs')
        for k in ['native_day_index','selected_bucket_phase','observed_army_bucket_phase','last_supply_update_date_storage_raw64','last_supply_update_date_raw','grace_anchor_date_storage_raw64','grace_anchor_date_raw','loaded_grace_days']:integer(c.get(k),label+'.'+k)
        return dict(c)
    def roles(self):
        a=self.body('action');w=self.loaded['action']['wrapper'];request=w.get('request',{});step=a.get('step')
        if step is None and isinstance(request,dict):step=request.get('arguments',{}).get('step')
        m=STEP.fullmatch(step) if isinstance(step,str) else None
        if m is None:raise Unavailable('action: canonical merge literal required')
        d,s=[integer(int(v),'public FullID',0,I32) for v in m.groups()];require(d!=s,'self merge invalid')
        if isinstance(request,dict) and request.get('arguments',{}).get('step') is not None:require(request['arguments']['step']==step,'action body/request literal disagreement')
        for k,v in [('destination_public_cunit_id',d),('source_public_cunit_id',s)]:
            if k in self.manifest:require(type(self.manifest[k]) is int and self.manifest[k]==v,'manifest '+k+' disagrees with actual direction')
        require(a.get('accepted') is True,'action accepted required')
        wa=a.get('war_action')
        if not isinstance(wa,dict):raise Unavailable('action war_action missing')
        require(same_json(wa.get('destination_army_id'),d) and same_json(wa.get('source_army_id'),s),'action role IDs inconsistent')
        require(wa.get('status') in ['merge_submitted','merge_applied'],'action not a submitted/applied merge')
        return {'destination_public_cunit_id':d,'source_public_cunit_id':s,'literal':step,'receipt_status':wa['status'],'war_action':wa}
    def review(self):
        mode=self.manifest.get('mode');require(mode in ['saved-live-receipts','offline-fixture'],'manifest mode required')
        self.report['input_mode']=mode
        for label in ['before_snapshot','before_strength','before_d_commander','before_s_commander','before_bracket','action','after_snapshot','after_strength','after_d_commander','after_bracket']:self.check('load-'+label,lambda label=label:self.load(label))
        roles=self.check('canonical-direction',self.roles)
        before=self.check('before-paused-frame',lambda:self.snapshot('before_snapshot'))
        bb=self.check('before-bracket-paused-frame',lambda:self.snapshot('before_bracket'))
        after=self.check('after-paused-frame',lambda:self.snapshot('after_snapshot'))
        ab=self.check('after-bracket-paused-frame',lambda:self.snapshot('after_bracket'))
        if not all([roles,before,after,bb,ab]):return self.finish()
        d=roles['destination_public_cunit_id'];s=roles['source_public_cunit_id'];wa=roles['war_action']
        self.report['roles']={k:v for k,v in roles.items() if k!='war_action'};self.report['frames']={'before':before,'before_bracket':bb,'after':after,'after_bracket':ab}
        def frame_window():
            require(before==bb,'before query bundle crossed bracket frame')
            require(after==ab,'after query bundle crossed bracket frame')
            require(before['episode_run_id']==after['episode_run_id'] and before['actor_id']==after['actor_id'],'actor/episode changed')
            require(before['date_raw']==after['date_raw'],'no-tick date condition failed')
            require(after['revision']>before['revision'] and after['native_revision']>before['native_revision'] and after['snapshot_id']!=before['snapshot_id'],'independently newer post frame not established')
            return {'same_date_raw':before['date_raw'],'date_delta_raw':0,'same_episode':True,'same_actor':True,'independently_newer':True,'scope':'same observed paused rawdate and bracket frame; unobserved transient producers are not reconstructed'}
        self.check('no-tick-independent-frame-window',frame_window)
        self.check('before-strength-frame',lambda:self.frame(self.body('before_strength'),before,'before_strength'))
        self.check('after-strength-frame',lambda:self.frame(self.body('after_strength'),after,'after_strength'))
        bd=self.check('before-D-context',lambda:self.army_snapshot('before_snapshot',d));bs=self.check('before-S-context',lambda:self.army_snapshot('before_snapshot',s));ad=self.check('after-D-context',lambda:self.army_snapshot('after_snapshot',d))
        def action_post():
            if not all([bd,bs,ad]):raise Unavailable('complete D/S snapshot contexts required')
            require(bd['current_province_id']==bs['current_province_id']==ad['current_province_id'],'sameprovince pre/post failed')
            require(bd['owner_character_id']==bs['owner_character_id']==ad['owner_character_id'],'owner changed/not same owner')
            require(s not in [a.get('army_id') for a in self.body('after_snapshot')['player_armies']],'source still present in entire post player roster')
            require(set(after['controllable_ids'])==set(before['controllable_ids'])-{s},'post controllable set is not exactly pre minusS')
            expected={'submitted_snapshot_id':before['snapshot_id'],'submitted_public_revision':before['revision'],'submitted_native_revision':before['native_revision'],'submitted_date_raw':before['date_raw'],'submitted_episode_run_id':before['episode_run_id'],'destination_owner_character_id':bd['owner_character_id'],'source_owner_character_id':bs['owner_character_id'],'destination_province_id':bd['current_province_id'],'source_province_id':bs['current_province_id'],'player_army_ids_before':before['controllable_ids']}
            for k,v in expected.items():require(same_json(wa.get(k),v),'action submit binding '+k+' differs/missing')
            return {'D_retained_public_id':d,'S_absent_public_id':s,'current_province_id':ad['current_province_id'],'owner_character_id':ad['owner_character_id'],'exact_controllable_set_delta':True,'receipt_status':wa['status'],'ACK_alone_used':False}
        self.check('actual-merge-independent-roster-postcondition',action_post)
        drow=self.check('before-D-full-strength',lambda:self.strength('before_strength',d));srow=self.check('before-S-full-strength',lambda:self.strength('before_strength',s));post=self.check('after-D-full-strength',lambda:self.strength('after_strength',d))
        if not all([drow,srow,post,bd,bs,ad]):return self.finish()
        dr,di=drow;sr,si=srow;pr,pi=post
        def full_union():
            union=di|si
            rows=[{'army_regiment_id':rid,'before_public_cunit_id':d if rid in di else s if rid in si else None,'after_public_cunit_id':d if rid in pi else None,'before':union.get(rid),'after':pi.get(rid),'current_max_unchanged':rid in union and rid in pi and pi[rid]==union[rid]} for rid in sorted(set(union)|set(pi))]
            self.report['regiment_transfer_rows']=rows
            self.report['regiment_union_observation']={'before_D_ids':sorted(di),'before_S_ids':sorted(si),'before_overlap_ids':sorted(set(di)&set(si)),'post_D_ids':sorted(pi),'missing_after_ids':sorted(set(union)-set(pi)),'extra_after_ids':sorted(set(pi)-set(union)),'changed_current_max_ids':[r['army_regiment_id'] for r in rows if r['before'] is not None and r['after'] is not None and not r['current_max_unchanged']]}
            require(dr['native_carmy_id']!=sr['native_carmy_id'],'D/S native CArmy IDs must be distinct')
            require(pr['native_carmy_id']==dr['native_carmy_id'],'D native CArmy FullID did not survive')
            require(not set(di)&set(si),'before D/S regiment sets overlap')
            require(set(pi)==set(union),'post full regiment IDs differ from exact preunion')
            require(pi==union,'per-ID current/maximum changed in action window')
            expected=integer(self.manifest.get('expected_regiment_count',27),'expected count',1,I32)
            require(len(union)==expected,f'complete actual union count{len(union)} differs from requested case count{expected}')
            return {'expected_count':expected,'before_counts':[len(di),len(si)],'after_count':len(pi),'full_ids':sorted(union),'pre_disjoint':True,'post_exact_union':True,'per_ID_current_maximum_unchanged':True,'source_regiments_transferred_to_D':sorted(si),'destination_regiments_retained':sorted(di),'pre_current_sum':dr['current_soldiers']+sr['current_soldiers'],'post_current_sum':pr['current_soldiers'],'pre_maximum_sum':dr['maximum_soldiers']+sr['maximum_soldiers'],'post_maximum_sum':pr['maximum_soldiers'],'retained_native_carmy_id':pr['native_carmy_id']}
        self.check('full-regiment-union-and-transfer',full_union)
        commanders={}
        for label,aid,row,owner,frame in [('before_d_commander',d,dr,bd['owner_character_id'],before),('before_s_commander',s,sr,bs['owner_character_id'],before),('after_d_commander',d,pr,ad['owner_character_id'],after)]:
            commanders[label]=self.check('current-'+label,lambda label=label,aid=aid,row=row,owner=owner,frame=frame:self.commander(label,aid,row['native_carmy_id'],owner,frame))
        self.report['commanders']=commanders
        clocks={}
        for label,row,frame in [('pre_D',dr,before),('pre_S',sr,before),('post_D',pr,after)]:clocks[label]=self.check('clock-'+label,lambda label=label,row=row,frame=frame:self.clock(row,frame,label))
        self.report['clock_observations']=clocks
        if all(clocks.values()):
            keys=['last_supply_update_date_storage_raw64','last_supply_update_date_raw','grace_anchor_date_storage_raw64','grace_anchor_date_raw','observed_army_bucket_phase']
            self.report['clock_relations']={k:{'pre_D':clocks['pre_D'][k],'pre_S':clocks['pre_S'][k],'post_D':clocks['post_D'][k],'post_equal_to':[role for role in ['pre_D','pre_S'] if clocks[role][k]==clocks['post_D'][k]]} for k in keys}
            self.report['clock_relation_scope']='Observed equality/difference only; no unobserved update, inherited elapsed history, or grace-reset cause inferred.'
        def fields():
            result={}
            for role,row in [('pre_D',dr),('pre_S',sr),('post_D',pr)]:
                result[role]={k:raw_pair(row,k,negative=k=='current_supply_change_monthly') for k in ['current_supply','current_supply_capacity','current_supply_change_monthly','current_attrition_fraction']}
            self.report['actual_supply_fields']=result;return result
        self.check('complete-supply-capacity-month-attrition-fields',fields)
        def arithmetic():
            dw=raw_pair(dr,'merge_supply_destination_weight');sw=sr['current_soldiers']*Q
            require(dw<=dr['current_soldiers']*Q,'D weight exceeds same D current*Q; wrong/invalidproducer cannot be admitted')
            result=fixed_trace(dw,sw,raw_pair(dr,'current_supply'),raw_pair(sr,'current_supply'),raw_pair(pr,'current_supply_capacity'),raw_pair(pr,'current_supply'))
            result['role_operands']={'D':{'public_cunit_id':d,'native_carmy_id':dr['native_carmy_id'],'producer':'merge_supply_destination_weight_raw =24E0160(D,out,0)+24E02A0(D,out)','raw':dw,'same_D_current_bound_raw':dr['current_soldiers']*Q},'S':{'public_cunit_id':s,'native_carmy_id':sr['native_carmy_id'],'producer':'same S Strength current_soldiers, already native2A95740(S+38,flags0)+complete actual row sum verified by exact3 producer','raw':sw,'scale':Q},'no_post_weight_substitution':True,'no_quality_to_capacity_prediction':True}
            self.report['arithmetic']=result
            require(result['arithmetic_match'],'post stock differs from ordinary exact fixed-point expected stock')
            return result
        self.check('native-ordinary-fixed-arithmetic-match',arithmetic)
        self.check('exact-build-declared-binding',self.profile)
        return self.finish()
    def profile(self):
        declared=self.manifest.get('exact_build')
        if not isinstance(declared,dict):raise Unavailable('exact_build declaration and separate Root evidence paths required; raw null version/hash never filled in')
        require(declared.get('version')=='1.20.0.3' and declared.get('exe_sha256')==EXE,'declared exact build/hash unsupported')
        paths=declared.get('evidence_paths')
        if not isinstance(paths,list) or not paths:raise Unavailable('Root actual runtime admission/build binding evidence paths missing')
        refs=[]
        for value in paths:
            if not isinstance(value,str) or not value:raise Unavailable('invalid exact-build evidence path')
            p=Path(value);p=p if p.is_absolute() else self.mp.parent/p
            refs.append({'path':str(p.resolve()),'sha256':sha(p)})
        observations=[]
        for label in ['before_strength','after_strength']:
            source=self.body(label).get('source',{})
            for key,expected in [('game_version','1.20.0.3'),('executable_sha256',EXE)]:
                value=source.get(key)
                if value is not None:require(value==expected,label+': raw source exact build differs')
            observations.append({'label':label,'raw_game_version':source.get('game_version'),'raw_executable_sha256':source.get('executable_sha256')})
        return {'declared_version':declared['version'],'declared_exe_sha256':EXE,'evidence':refs,'raw_source_metadata_preserved':observations,'scope':'Evidence bytes/hash and declared profile checked only. Root separately reviews receipt semantics and actual process attribution; this analyzer never attests a running process.'}
    def finish(self):
        failures=[c for c in self.checks if c['status']!='verified'];self.report['failed_checks']=[c['id'] for c in failures]
        admitted=not failures and self.report.get('input_mode')=='saved-live-receipts'
        ar=self.report.get('arithmetic')
        self.report['all_required_receipt_checks_verified']=not failures
        self.report['observed_native_instance_admitted_from_supplied_receipts']=admitted
        self.report['upper_clamp_instance_admitted_from_supplied_receipts']=bool(admitted and ar and ar['upper_clamp_arithmetic_match'])
        self.report['nonclamp_blend_instance_admitted_from_supplied_receipts']=bool(admitted and ar and ar['arithmetic_match'] and not ar['upper_clamp_required_by_arithmetic'])
        self.report['status']='OBSERVED_RECEIPTS_MATCH_WITHIN_DECLARED_ROOT_BINDING' if admitted else 'OFFLINE_FIXTURE_ONLY' if not failures and self.report.get('input_mode')=='offline-fixture' else 'NOT_ADMITTED_FAIL_CLOSED'
        self.report['scope']='This is a saved-file review with zero new live execution credit. Arithmetic match alone is not native causality, complete video review, or signoff. No missing/partial/unavailable value is synthesized.'
        return self.report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    try:
        r=Reviewer(a.input);result=r.review()
    except (OSError,ValueError,KeyError,TypeError) as e:
        result={'schema':'xar.episode04.actual-merge-receipt-review.v1','status':'NOT_ADMITTED_FAIL_CLOSED','fatal_input_error':str(e),'arithmetic':None,'sdk_calls':0,'game_actions':0,'screen_actions':0,'new_live_execution_credit':0,'observed_native_instance_admitted_from_supplied_receipts':False}
    write_new(a.output,result)
    print(json.dumps({'report':str(a.output.resolve()),'sha256':sha(a.output),'status':result['status'],'arithmetic_match':result.get('arithmetic',{}).get('arithmetic_match') if result.get('arithmetic') else None,'clamp_admitted':result.get('upper_clamp_instance_admitted_from_supplied_receipts',False),'failed_checks':result.get('failed_checks',[]),'fatal_input_error':result.get('fatal_input_error')},ensure_ascii=False))
    return 0 if result.get('all_required_receipt_checks_verified') else 2
if __name__=='__main__':raise SystemExit(main())
