package org.xar.ck3.control.wave2.events.registered;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** Actual compatibility producer differential. No Game, RPC, writer, or generated expected implementation. */
final class RegisteredEventProducerParityTest {
    private record SourcePin(String relative,long bytes,String sha256) { }
    private static final List<SourcePin> SOURCE_PINS=List.of(
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/policy.py",72494,"ae4b7db00f385cd3634aee48cab23c99926e12ae167b2b42c8bad99c6d2b5bf9"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/registry.py",22036,"02610bfbf313233f08a375eb50409f50ad5383f7e812d965010d8ae0525f066b"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/source_index.py",18128,"f2a0afc16e3f69598802bf2e5a8ee999cf7c1b196413b65c26dd0bbe0c0ddfd3"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/builds.py",1859,"afd7f9fb5abf7ea91fb4888767135027db9f9390151e5df6edaa719d19e73712"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/poet_long_term_context.py",7815,"babcf58946991c79d4ca4c1b46d61988e70ecb67fd6b371e12b14d0a0260598e"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/feast_brawl_utility_context.py",8811,"1e9024724497da44dc2b65a5762e4cd411d9418aa4230a77235fc3691cacf15b"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/faction_demand1001_context.py",12005,"24032c2a96b0ffe49a334ff188ad4ee5fda6addfa48e3e9db3620a89620ef04b"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/occurrence.py",4434,"88f873a400962906934c067b202360373d754f38f515e9bd967eb0fd86c390d4"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/bookmark_raiktor_policy.py",7846,"c82e67925d34f6e283fb49c98956c85151ba472c2234efec5a38cc566898b558"),
        new SourcePin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/__init__.py",13061,"cd78bb588214e060d12a5609a98199e4e2dd23f76b044a2a579b53b244fd4fd8")
    );
    private static final BigInteger PLAYER = BigInteger.valueOf(27181);
    private static final int MAXIMUM_ORACLE_BYTES = 16 * 1024 * 1024;
    private static final String ORACLE = """
import json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(root/'ck3_autonomous_player'/'src')]
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.bookmark_raiktor_policy import recommend_robert_raiktor_option_v1
request=json.loads(sys.stdin.buffer.read(8*1024*1024+1))
if not isinstance(request,list) or len(request)>4096:raise RuntimeError('bounded exact producer request required')
result=[]
for row in request:
    if row['producer']=='registered':
        result.append(recommend_registered_vanilla_event_option_v1(row['context'],
            played_character_id=row['played_character_id'],snapshot_option_count=row['snapshot_option_count'],
            ck3_build=row['ck3_build'],played_character=row['played_character'],
            event_opinion_observations=row['opinion_observations'],event_history=row['event_history']))
    elif row['producer']=='raiktor':
        result.append(recommend_robert_raiktor_option_v1(row['context'],row['snapshot'],
            war_entry_assessments={int(k):v for k,v in row['assessments'].items()},
            action_steps=set(row['action_steps']),cross_run_focus=row['focus'],
            event_scope_query_supported=row['event_scope_query_supported']))
    else:raise RuntimeError('undeclared original producer')
raw=json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
if len(raw)>16*1024*1024:raise RuntimeError('original producer output exceeds differential limit')
sys.stdout.buffer.write(raw)
""";

    @Test @Timeout(90)
    void wholeRegisteredKeyUnionAndVariantsCompareToActualOriginalProducer() throws Exception {
        RegisteredEventKnowledge knowledge = RegisteredEventKnowledge.load();
        List<ObjectValue> requests = new ArrayList<>(); List<ObjectValue> actual = new ArrayList<>();
        RegisteredVanillaEventPolicy policy = new RegisteredVanillaEventPolicy(knowledge);
        for (String build : RegisteredEventKnowledge.EXE.keySet().stream().sorted().toList()) {
            int expectedKeys = build.equals("1.20.0.4") ? 198 : 195;
            assertEquals(expectedKeys,knowledge.keys(build).size(),"complete producer key union");
            for (String key : knowledge.keys(build).stream().sorted().toList()) {
                ObjectValue row = knowledge.query(build,key), contract = obj(materialize(row.get("contract"),PLAYER));
                List<ObjectValue> variants = new ArrayList<>(); variants.add(contract);
                for (Value raw : seq(contract.get("option_variants"))) if (raw instanceof ObjectValue variant)
                    variants.add(merge(remove(contract,"option_variants"),variant));
                for (Value raw : seq(contract.get("scope_variants"))) if (raw instanceof ObjectValue variant)
                    variants.add(merge(remove(contract,"scope_variants"),variant));
                for (ObjectValue candidate : variants) {
                    ObjectValue context = context(build,key,candidate);
                    Value count = candidate.get("snapshot_option_count");
                    if (integer(count)==null && !seq(candidate.get("snapshot_option_counts")).isEmpty()) count=seq(candidate.get("snapshot_option_counts")).getFirst();
                    if (integer(count)==null) count=candidate.getOrNull("option_count");
                    if (integer(count)==null) count=v(1);
                    addRegistered(requests,actual,policy,context,build,v(PLAYER),count);
                }
            }
        }
        assertTrue(requests.size()>=783,"all four exact build key unions must be consumed");
        assertEquals(new ArrayValue(actual.stream().map(Value.class::cast).toList()),oracle(requests),"complete original recommendation JSON");
    }

    @Test @Timeout(90)
    void wrongFieldsAndSerializationUseTheActualOriginalProducer() throws Exception {
        RegisteredEventKnowledge knowledge=RegisteredEventKnowledge.load();
        var policy=new RegisteredVanillaEventPolicy(knowledge); String build="1.19.0.6",key="tgp_travel_events.0030";
        ObjectValue base=context(build,key,obj(materialize(knowledge.query(build,key).get("contract"),PLAYER)));
        List<ObjectValue> requests=new ArrayList<>(),actual=new ArrayList<>();
        addRegistered(requests,actual,policy,base,build,v(PLAYER),v(2));
        for(String field:List.of("schema","schema_version","status","window_match_count","root_scope","saved_scopes","options","event_definition_key")) {
            addRegistered(requests,actual,policy,remove(base,field),build,v(PLAYER),v(2));
            addRegistered(requests,actual,policy,base.with(field,RetainedJson.NULL),build,v(PLAYER),v(2));
        }
        for(Value wrong:List.of(v(true),new FloatingValue(27181.0),v("27181"),RetainedJson.NULL))
            addRegistered(requests,actual,policy,base,build,wrong,v(2));
        for(Value wrong:List.of(v(true),new FloatingValue(2.0),v("2"),RetainedJson.NULL))
            addRegistered(requests,actual,policy,base,build,v(PLAYER),wrong);
        assertEquals(new ArrayValue(actual.stream().map(Value.class::cast).toList()),oracle(requests));
        assertThrows(IllegalArgumentException.class,()->RegisteredEventKnowledge.decode(new byte[216013]));
        assertEquals(knowledge.query(build,key),RetainedJson.parse(RetainedJson.encode(knowledge.query(build,key))));
    }

    @Test @Timeout(90)
    void dedicatedRaiktorPrecedesRegistryAndRetainsBlockedCases() throws Exception {
        List<ObjectValue> requests=new ArrayList<>(),actual=new ArrayList<>();
        ObjectValue context=b().set("event_definition_key","bookmark.1071").set("status","available").set("window_match_count",1)
            .set("root_scope",scope("character",PLAYER)).set("saved_scopes",arr(
                b().set("name","byz_emperor").set("scope",scope("character",BigInteger.valueOf(50001))).build(),
                b().set("name","raiktor").set("scope",scope("character",BigInteger.valueOf(50002))).build()))
            .set("options",arr(option(0,0),option(1,1),option(2,2))).build();
        ObjectValue snapshot=b().set("active_event",b().set("option_count",3).build()).set("played_character",b().set("character_id",PLAYER).build())
            .set("played_character_gold",b().set("raw",10_000_000).set("scale",100_000).build()).set("active_wars",arr())
            .set("declarable_wars",arr(b().set("target_character_id",50001).build())).build();
        List<ObjectValue> contexts=List.of(context,context.with("window_match_count",v(2)),
            context.with("options",arr(option(0,0),option(1,1),option(2,2).with("enabled",v(false)))),
            context.with("root_scope",scope("character",BigInteger.valueOf(3))));
        List<ObjectValue> states=List.of(snapshot,snapshot.with("played_character_gold",b().set("raw",9_999_999).set("scale",100_000).build()),
            snapshot.with("active_wars",arr(b().set("war_id",1).build())));
        List<ObjectValue> powers=List.of(EMPTY,b().set("50001",b().set("actor_power_base_raw",125).set("target_power_total_raw",100).build()).build(),
            b().set("50001",b().set("actor_power_base_raw",124).set("target_power_total_raw",100).build()).build());
        for(ObjectValue c:contexts)for(ObjectValue s:states)for(ObjectValue power:powers)for(String focus:List.of("none","marriage")) {
            Map<BigInteger,ObjectValue> assessments=new LinkedHashMap<>();
            power.fields().forEach((k,v)->assessments.put(new BigInteger(k),obj(v)));
            Set<String> steps=Set.of("query-war-entry-assessments-v1-1-50001");
            Optional<String> typedFocus=focus.equals("none")?Optional.empty():Optional.of(focus);
            ObjectValue request=b().set("producer","raiktor").set("context",c).set("snapshot",s).set("assessments",power)
                .set("action_steps",arr(steps.stream().map(RegistryJson::v).toList())).set("focus",typedFocus.map(RegistryJson::v).orElse(RetainedJson.NULL))
                .set("event_scope_query_supported",false).build();
            requests.add(request);
            actual.add(BookmarkRaiktorPolicy.recommend(new BookmarkRaiktorPolicy.Input(c,s,assessments,steps,typedFocus,false)).orElseThrow().wire());
        }
        assertEquals(new ArrayValue(actual.stream().map(Value.class::cast).toList()),oracle(requests));
        assertTrue(BookmarkRaiktorPolicy.recommend(new BookmarkRaiktorPolicy.Input(context.with("event_definition_key",v("other.1")),
            snapshot,Map.of(),Set.of(),Optional.empty(),false)).isEmpty());
    }
    private static void addRegistered(List<ObjectValue> requests,List<ObjectValue> actual,RegisteredVanillaEventPolicy policy,
            ObjectValue context,String build,Value player,Value count) {
        ObjectValue request=b().set("producer","registered").set("context",context).set("ck3_build",build).set("played_character_id",player)
            .set("snapshot_option_count",count).set("played_character",RetainedJson.NULL).set("opinion_observations",RetainedJson.NULL).set("event_history",arr()).build();
        requests.add(request);
        var input=new RegisteredVanillaEventPolicy.Input(context,player,count,Optional.of(build),RetainedJson.NULL,RetainedJson.NULL,arr());
        ObjectValue response=policy.recommend(input).wire();
        assertEquals(response,RetainedJson.parse(RetainedJson.encode(response)),"serialized producer result must retain exact JSON domain");
        actual.add(response);
    }
    private static ObjectValue context(String build,String key,ObjectValue contract) {
        Map<String,Value> types=obj(contract.get("scope_types")).fields(); List<Value> names;
        if (!seq(contract.get("saved_scope_names")).isEmpty()) names=seq(contract.get("saved_scope_names"));
        else if (!seq(contract.get("saved_scope_name_sets")).isEmpty()) names=seq(seq(contract.get("saved_scope_name_sets")).getFirst());
        else names=types.keySet().stream().sorted().map(RegistryJson::v).map(Value.class::cast).toList();
        List<Value> scopes=new ArrayList<>(); int next=1;
        for(Value raw:names) {
            String name=str(raw),type=str(types.get(name));if(type.isEmpty())type="character";
            BigInteger id=integer(get(contract.get("character_scopes"),name));if(id==null)id=PLAYER.add(BigInteger.valueOf(next));
            scopes.add(b().set("name",name).set("name_identifier",next++).set("scope",scope(type,id)).build());
        }
        List<Value> options=new ArrayList<>();int rendered=0;
        for(Value raw:seq(contract.get("native_option_indices"))) {
            BigInteger nativeIndex=integer(raw); if(nativeIndex==null)continue;
            ObjectValue option=option(rendered++,nativeIndex.intValueExact());
            if(seq(contract.get("disabled_native_option_indices")).contains(raw))option=option.with("enabled",v(false));
            options.add(option);
        }
        return b().set("schema","current-event-window-context-v1").set("schema_version",1).set("status","available").set("window_match_count",1)
            .set("event_definition_key",key).set("ck3_build",build).set("current_event_instance_id",9).set("snapshot_revision",19).set("date_raw",53_284_680)
            .set("root_scope",scope("character",PLAYER)).set("saved_scopes",arr(scopes)).set("options",arr(options))
            .set("provenance",b().set("backend_id","ck3-"+build+"-native-event-window-v1").build()).build();
    }
    private static ObjectValue scope(String type,BigInteger character) {
        ObjectValue identity=type.equals("character")?b().set("status","available").set("kind","character").set("character_id",character).build()
            :b().set("status","unavailable").set("reason","generic_scope_payload_identity_not_closed").build();
        return b().set("status","available").set("type_key",type).set("raw_type_index",type.equals("character")?4:3)
            .set("subtype",0).set("typed_identity",identity).build();
    }
    private static ObjectValue option(int rendered,int nativeIndex) {
        return b().set("rendered_index",rendered).set("native_option_index",nativeIndex).set("shown",true).set("enabled",true).set("fallback",false).set("cancel",false).build();
    }
    private static void verifySources(Path root) throws Exception {
        for(SourcePin pin:SOURCE_PINS) {
            Path path=root.resolve(pin.relative()).toRealPath();
            if(!path.startsWith(root))throw new IllegalStateException("original producer source escaped explicit repository");
            byte[] raw=Files.readAllBytes(path);
            String sha=java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));
            if(raw.length!=pin.bytes()||!sha.equals(pin.sha256()))throw new IllegalStateException("original producer source drift: "+pin.relative());
        }
    }
    private static ArrayValue oracle(List<ObjectValue> requests) throws Exception {
        List<Value> result=new ArrayList<>();
        for(int start=0;start<requests.size();start+=64)result.addAll(oracleChunk(requests.subList(start,Math.min(start+64,requests.size()))).values());
        return new ArrayValue(result);
    }
    private static ArrayValue oracleChunk(List<ObjectValue> requests) throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        if(repository==null||python==null)throw new IllegalStateException("complete event parity requires explicit original repository and fixture Python interpreter; never skip as pass");
        Path root=Path.of(repository).toRealPath();
        if(!Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/policy.py")))throw new IllegalStateException("actual original producer source absent");
        verifySources(root);
        ProcessBuilder builder=new ProcessBuilder(python,"-I","-B","-c",ORACLE,root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONNOUSERSITE","1");builder.environment().put("PYTHONUTF8","1");
        builder.redirectErrorStream(true); Process process=builder.start();
        CompletableFuture<byte[]> output=CompletableFuture.supplyAsync(()->{
            try{return process.getInputStream().readNBytes(MAXIMUM_ORACLE_BYTES+1);}catch(IOException error){throw new java.io.UncheckedIOException(error);}
        });
        try {
            byte[] request=RetainedJson.encode(new ArrayValue(requests.stream().map(Value.class::cast).toList()));
            if(request.length>8*1024*1024)throw new IllegalStateException("bounded producer differential input exceeded");
            try(var stdin=process.getOutputStream()){stdin.write(request);}
            if(!process.waitFor(Duration.ofSeconds(60).toMillis(),TimeUnit.MILLISECONDS))throw new IllegalStateException("original producer differential timed out");
            byte[] raw=output.get(5,TimeUnit.SECONDS);
            verifySources(root);
            assertEquals(0,process.exitValue(),"actual original producer failed: "+new String(raw,StandardCharsets.UTF_8));
            assertTrue(raw.length<=MAXIMUM_ORACLE_BYTES,"bounded original producer output");
            return (ArrayValue)RetainedJson.parse(raw,new RetainedJson.ParseBudget(MAXIMUM_ORACLE_BYTES,1_000_000,128));
        } finally {if(process.isAlive())process.destroyForcibly();}
    }
}

