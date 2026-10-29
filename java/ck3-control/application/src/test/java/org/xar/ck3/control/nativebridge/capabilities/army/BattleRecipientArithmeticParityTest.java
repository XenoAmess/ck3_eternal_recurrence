package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.File;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Fresh original numeric producers, native wrap boundaries, and the unchanged fixture constructors. */
final class BattleRecipientArithmeticParityTest {
    @Test void originalCachedAndUncachedValuesMatchWithoutMutatingSource() throws Exception {
        JsonNode corpus=capture();assertEquals("actual-recipient-numeric-producers",corpus.path("producer").asText());assertEquals(4,corpus.path("source_pins").size());
        int cached=0,uncached=0,ready=0,partial=0;
        for(JsonNode row:corpus.get("cases")) {
            ObjectNode input=(ObjectNode)row.get("input");byte[] before=StrictJson.canonical(input);
            BattleRecipientArithmetic.Result result;
            if(row.path("kind").asText().equals("absent")){result=BattleRecipientArithmetic.absent(input);cached++;}
            else{result=BattleRecipientArithmetic.uncached(input);uncached++;}
            assertEquals(number(row.path("expected").get("value_q64")),result.valueQ64(),row.path("id").asText());
            assertEquals(bool(row.path("expected").get("applicable")),result.applicable(),row.path("id").asText());
            assertEquals(row.path("expected").path("calculation_ready").asBoolean(),result.calculationReady(),row.path("id").asText());
            if(result.calculationReady())ready++;else partial++;
            assertArrayEquals(before,StrictJson.canonical(input),"arithmetic must leave its complete source unchanged");
            ObjectNode roundtrip=(ObjectNode)StrictJson.parse(before,8_388_608);
            assertEquals(result,row.path("kind").asText().equals("absent")?BattleRecipientArithmetic.absent(roundtrip):BattleRecipientArithmetic.uncached(roundtrip),"actual JSON persistence domain");
        }
        assertTrue(cached>=20);assertTrue(uncached>=100);assertTrue(ready>=20);assertTrue(partial>=10);
    }
    @Test void nativeFixedMultiplyKeepsDistinctDecomposedOperands() throws Exception {
        JsonNode corpus=capture();boolean differenceObserved=false;
        for(JsonNode row:corpus.get("multiply")) {
            long a=row.get("a").bigIntegerValue().longValueExact(),b=row.get("b").bigIntegerValue().longValueExact();
            long cached=BattleRecipientArithmetic.cachedFixedMultiplyQ64(a,b),uncached=BattleRecipientArithmetic.uncachedFixedMultiplyQ64(a,b);
            assertEquals(row.get("cached").bigIntegerValue().longValueExact(),cached,"cached signed minimum decomposition");
            assertEquals(row.get("uncached").bigIntegerValue().longValueExact(),uncached,"uncached signed maximum decomposition");
            differenceObserved|=cached!=uncached;
        }
        assertTrue(corpus.path("multiply").size()>=200);assertTrue(differenceObserved,"the two real instruction paths must not collapse into one multiply");
    }
    private static BigInteger number(JsonNode n){return n==null||n.isNull()?null:n.bigIntegerValue();}
    private static Boolean bool(JsonNode n){return n==null||n.isNull()?null:n.booleanValue();}
    private static JsonNode capture() throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");assertNotNull(repository,"missing original source root must fail");assertNotNull(python,"missing oracle interpreter must fail");Path root=Path.of(repository).toAbsolutePath().normalize();
        ProcessBuilder builder=new ProcessBuilder(python,"-B","-X","utf8","-c",PROGRAM,root.toString());builder.directory(root.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src")+File.pathSeparator+root);builder.redirectError(ProcessBuilder.Redirect.INHERIT);Process process=builder.start();byte[] data;
        try(var reader=Executors.newSingleThreadExecutor()){var future=reader.submit(()->{try(var in=process.getInputStream()){return in.readNBytes(8_388_609);}});if(!process.waitFor(60,TimeUnit.SECONDS)){process.descendants().forEach(ProcessHandle::destroyForcibly);process.destroyForcibly();fail("actual producer timeout");}data=future.get();}
        assertEquals(0,process.exitValue(),"original numeric producers must actually exit successfully");assertTrue(data.length>0&&data.length<=8_388_608,"bounded complete numeric corpus");return StrictJson.parse(data,8_388_608);
    }
    private static final String PROGRAM="""
        import ast,copy,hashlib,importlib,json,random,sys,types
        from pathlib import Path
        root=Path(sys.argv[1]);src=root/'ck3_autonomous_player/src';tests=root/'ck3_autonomous_player/tests/unit'
        import xar_autoplayer
        bridge=types.ModuleType('xar_autoplayer.bridge');bridge.__path__=[str(src/'xar_autoplayer/bridge')];sys.modules[bridge.__name__]=bridge
        cached=importlib.import_module('xar_autoplayer.simulation.battle_person_absent_recipient_12003')
        uncached=importlib.import_module('xar_autoplayer.simulation.battle_person_uncached_recipient_12003')
        numeric=importlib.import_module('xar_autoplayer.simulation.battle_trait_numeric_inputs_12003')
        fixture=tests/'test_battle_person_uncached_recipient_12003.py';tree=ast.parse(fixture.read_text(encoding='utf-8'));ns={}
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'family','raw'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(fixture),'exec'),ns)
        family,raw=ns['family'],ns['raw'];MIN=-(1<<63);MAX=(1<<63)-1;MASK=(1<<64)-1;cases=[]
        def add(name,kind,value):
            result=(cached.compute_absent_recipient_from_native_inputs_12003 if kind=='absent' else uncached.compute_uncached_recipient_from_native_inputs_12003)(copy.deepcopy(value))
            cases.append(dict(id=name,kind=kind,input=value,expected=dict(value_q64=result.value_q64,applicable=result.applicable,calculation_ready=result.calculation_ready)))
        def absent():
            value=copy.deepcopy(raw()['downstream_inputs']);value.update(carrier_present=False,associated_cache_440=1,cached_map_430={'count':0,'entries':[]},cached_map_458={'count':None,'entries':None});value['aggregate_properties']={'count':0,'keys_u16':None,'values_q64':None};return value
        def occupied(value=100000,key=0xffffffffffffffff,trait=17):
            v=absent();v['cached_map_430']={'count':1,'entries':[dict(bucket_index=3,key_object=key,trait_id_u32=trait,value_q64=value)]};v['trait_ids']={'count':1,'values_u32':[trait]};return v
        add('cached-empty-no-irrelevant-input-demand','absent',absent())
        for field,values in [('carrier_present',(None,True,False)),('associated_cache_440',(None,0,0xffffffff,1<<32)),('clamp_lower_q64',(None,True,0.0))]:
            for value in values:v=absent();v[field]=value;add('cached-'+field+'-'+repr(value),'absent',v)
        for guard in (0,-1,-2,None):
            v=occupied();v['membership_header_guard_raw']=guard;add('cached-membership-guard-'+str(guard),'absent',v)
            v=absent();v.update(aggregate_context_selection='inline_context_5d67b90',aggregate_context_guard_raw=guard);add('cached-aggregate-guard-'+str(guard),'absent',v)
        v=absent();v['cached_map_430']['count']=-1;v['trait_ids']={'count':None,'values_u32':None};add('cached-negative-map-count-no-trait-demand','absent',v)
        v=occupied(MIN);v['membership_ids']={'count':1,'values_u64':['0xffffffffffffffff']};v['cached_map_458']={'count':1,'entries':[dict(key_object=MASK,value_u64=MASK)]};v['member_multiplier_q64']=100003;add('cached-full-qword-membership-min-product','absent',v)
        v=occupied(MAX);v['cached_map_458']={'count':0,'entries':None};v['membership_ids']={'count':7,'values_u64':None};add('cached-absent-link-skips-membership-vector','absent',v)
        v=occupied(MAX);v['cached_map_430']['entries'].append(dict(key_object=MASK,trait_id_u32=17,value_q64=1));v['cached_map_430']['count']=2;v['aggregate_properties']={'count':1,'keys_u16':[0x25d],'values_q64':[MAX]};add('cached-last-assignment-then-wrap-sum','absent',v)
        v=occupied(77);v['cached_map_430']['entries'].insert(0,dict(key_object=MASK,trait_id_u32=17,value_q64=None));v['cached_map_430']['count']=2;add('cached-gap-survives-later-overwrite','absent',v)
        for keys,values in [([0,0x25c,0x25d,0xffff],[1,2,-999,4]),([0,0x25e],[1,None]),([0xffff,0x25d,0],[None,300,None]),([0x25d],None)]:
            v=absent();v['aggregate_properties']={'count':len(keys),'keys_u16':keys,'values_q64':values};add('cached-native-lower-bound-'+repr(keys),'absent',v)
        v=absent();v.update(clamp_lower_q64=5,clamp_upper_q64=-5);add('cached-native-clamp-order','absent',v)
        v=occupied(17);v['trait_ids']={'count':2,'values_u32':[17]};add('cached-trait-match-short-circuits-unread-tail','absent',v)
        v=occupied(17);v['trait_ids']={'count':2,'values_u32':[None,17]};add('cached-trait-match-retains-earlier-demand-gap','absent',v)
        v=raw();add('uncached-empty-original-fixture','uncached',v)
        for field,value in [('carrier_present',True),('carrier_present',None),('associated_cache_440',1),('associated_cache_440',None)]:v=raw();v[field]=value;add('uncached-skip-'+field+'-'+repr(value),'uncached',v)
        v=raw();v['seed_family']=family([(0x1010,17,100000,2)]);v['active_objects']={'count':1,'entries':[dict(native_index=0,object=0x7777,magic_u32=0x4744624f,intrinsic_family=family([(0x1010,17,200000,2)]))]};v['active_context']={'count':2,'entries':[dict(native_index=0,object=0x7777,flag_u8=4),dict(native_index=1,object=0x7777,flag_u8=1)]};v['removed_objects']={'count':1,'entries':[dict(native_index=0,object=0x6666,magic_u32=0x4744624f,intrinsic_family=family([(0x1010,17,300000,2)]))]};v['downstream_inputs']['membership_ids']={'count':1,'values_u64':[0x7777]};v['downstream_inputs']['member_multiplier_q64']=200000;add('uncached-actual-seed-active-first-context-removed-660000','uncached',v)
        v=raw();v['seed_family']=family([(0x1010,17,100000,2)]);v['removed_objects']={'count':1,'entries':[dict(native_index=0,object=0x6666,magic_u32=0x4744624f,intrinsic_family=family(second=[(0x1010,17,400000,2)]))]};add('uncached-kind-switch-minus390000','uncached',v)
        v=raw();v['cap_i32']=1;v['seed_boost_multiplier_q64']=0;v['seed_family']=family([(0x1010,17,100000,2),(0x2020,18,100000,2)]);v['downstream_inputs'].update(trait_ids={'count':None,'values_u32':None},membership_ids={'count':None,'values_u64':None},membership_header_guard_raw=None);v['positive_fallback_object']=v['positive_fallback_magic_u32']=None;add('uncached-equal-group-invalidated-no-link-demand','uncached',v)
        v=raw();v['seed_boost_multiplier_q64']=0;v['seed_family']=family([(None,None,120000,0)]);v['downstream_inputs']['trait_ids']={'count':1,'values_u32':[0xffffffff]};add('uncached-fallback-key-signed-id','uncached',v)
        v=raw();v['cap_i32']=100;v['seed_boost_multiplier_q64']=0;v['seed_family']=family([(0x1000+i*16,i-20,100000+i,2) for i in reversed(range(40))]);v['downstream_inputs']['trait_ids']={'count':40,'values_u32':[(i-20)&0xffffffff for i in range(40)]};add('uncached-large-stable-signed-id-sort','uncached',v)
        v=raw();v['seed_boost_multiplier_q64']=0;v['seed_family']=family([(0x1010,17,100000,2)],[(0x1010,17,100000,2)]);add('uncached-equal-positive-vector-first-kind','uncached',v)
        v=raw();v['seed_boost_multiplier_q64']=100003;v['seed_family']=family([(0x1010,17,4611686018427387921,2)]);add('uncached-decomposed-maximum-operand','uncached',v)
        v=raw();v['seed_boost_multiplier_q64']=0;v['seed_family']=family([(0x1010,-1,100000,2),(0x2020,0,90000,2),(0x1010,1,110000,2)]);v['downstream_inputs']['trait_ids']={'count':3,'values_u32':[0xffffffff,0,1]};add('uncached-sorted-only-adjacent-key-dedup','uncached',v)
        rng=random.Random(0x29216);quantities=[MIN,MAX,4611686018427387921,-4611686018427387921,0,1,-1,99999,100000,100003,300000,900000]
        for index in range(128):
            v=raw();v['cap_i32']=rng.choice([-1,0,1,2,3,5]);v['seed_boost_multiplier_q64']=rng.choice(quantities);v['positive_fallback_magic_u32']=rng.choice([0,0x4744624f]);v['negative_fallback_magic_u32']=rng.choice([0,0x4744624f]);v['active_flag4_multiplier_q64']=rng.choice(quantities);v['active_other_multiplier_q64']=rng.choice(quantities)
            def source_family():
                vectors=[]
                for kind in range(2):vectors.append([(0x1000+rng.randrange(5)*16,rng.choice([-2,-1,0,1,17,18]),rng.choice(quantities),2) for _ in range(rng.randrange(5))])
                return family(*vectors)
            v['seed_family']=source_family();pointers=[]
            for name in ('active_objects','removed_objects'):
                entries=[]
                for j in range(rng.randrange(4)):
                    pointer=0x7000+16*rng.randrange(4);pointers.append(pointer);entries.append(dict(native_index=j,object=pointer,magic_u32=rng.choice([0,0x4744624f]),intrinsic_family=source_family()))
                v[name]={'count':len(entries),'entries':entries}
            context_entries=[dict(native_index=j,object=p,flag_u8=rng.choice([0,1,4])) for j,p in enumerate(pointers)]
            v['active_context']={'count':len(context_entries),'entries':context_entries}
            d=v['downstream_inputs'];d['trait_ids']={'count':6,'values_u32':[0xfffffffe,0xffffffff,0,1,17,18]};d['membership_ids']={'count':len(pointers),'values_u64':pointers};d['member_multiplier_q64']=rng.choice(quantities)
            if index%7==0:d['membership_header_guard_raw']=rng.choice([0,-1,None])
            if index%11==0:v['seed_family']['first']['count']=None
            add('uncached-original-producer-seeded-corpus-'+str(index),'uncached',v)
        pairs=[];edges=[MIN,MIN+1,-4611686018427387921,-3037000500,-3037000499,-100003,-1,0,1,99999,100000,100003,3037000499,3037000500,4611686018427387921,MAX]
        for a in edges:
            for b in edges:pairs.append(dict(a=a,b=b,cached=numeric.native_fixed_mul_q_12003(a,b),uncached=uncached.native_uncached_fixed_mul_q_12003(a,b)))
        paths=[src/'xar_autoplayer/simulation'/name for name in ('battle_person_absent_recipient_12003.py','battle_person_uncached_recipient_12003.py','battle_trait_numeric_inputs_12003.py')]+[fixture]
        pins=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
        sys.stdout.write(json.dumps(dict(producer='actual-recipient-numeric-producers',cases=cases,multiply=pairs,source_pins=pins),ensure_ascii=False,separators=(',',':')))
        """;
}
