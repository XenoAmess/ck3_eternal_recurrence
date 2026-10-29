package org.xar.ck3.control.wave2.events.eventmaterial;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.eventoutcome.RegisteredEventMaterial;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Executes the actual compatibility producers and their existing fixture builders, never a copied oracle. */
final class DedicatedEventMaterialProducerParityTest {
    private record Pin(String path,long bytes,String sha) { }
    private static final List<Pin> PINS=List.of(
        new Pin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/bookmark1070_material.py",13883,"325afe1ec9b58ad87ee1a291127b7f66af5dfbb509bc3f611508875611367b9e"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/rite_growth_material.py",12086,"a963c5bc19285c86cd6e8dd3e72926cea3fdb9c2b091beb977fd431381d35568"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/outcome.py",16879,"1628d61ea0fe6f63632c8f5a63bb82e990f9c3153df3b7e2b852113dc9310691"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/player_religion_context_private_transport.py",23941,"59d34ed3cd432804495e129097ea86b88353f112a27b7c2cf2483c08ab192c06"),
        new Pin("ck3_autonomous_player/tests/unit/test_bookmark1070_material.py",8601,"829526f7e65a596ac69312220eae7ca30e39a57e30b9d2538be88c9ffb80b798"),
        new Pin("ck3_autonomous_player/tests/unit/test_rite_growth_fulfillment_material_12004.py",9916,"41148ed8e5611512af900510a7eed7e211bdf9e3fe754efbe18de49372863c0b")
    );
    private static final String ORACLE="""
import sys,json,copy
from pathlib import Path
root=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(root/'ck3_autonomous_player'/'src'),str(root/'ck3_autonomous_player'/'tests'/'unit')]
import test_bookmark1070_material as b
import test_rite_growth_fulfillment_material_12004 as r
from xar_autoplayer.vanilla_events.outcome import plan_registered_event_material_postcondition_v1,evaluate_registered_event_material_postcondition_v1
rows=[]
for mutation in ('none','no_new','owner','date','actor','generation','instance','revision','composition','strength','regiments','type','reason'):
    expected,selection=b.material_case()
    after=selection['ending_bookmark1070_armies']
    if mutation=='no_new':after['player_armies']=after['player_armies'][:1]
    elif mutation=='owner':after['player_armies'][1]['owner_character_id']=29830
    elif mutation=='date':after['date_raw']+=24
    elif mutation=='actor':after['character_id']=29830
    elif mutation=='generation':after['connection_generation']+=1
    elif mutation=='instance':selection['new_event_instance_id']=19
    elif mutation=='revision':after['native_revision']=selection['starting_bookmark1070_armies']['native_revision']
    elif mutation=='composition':after['army_strengths'][0]['regiment_strengths'][1]['maa_type_key']='pikemen'
    elif mutation=='strength':after['army_strengths'][0]['status']='unavailable'
    elif mutation=='regiments':after['army_strengths'][0]['regiment_strengths']=None
    elif mutation=='type':after['army_strengths'][0]['regiment_strengths'][1]['maa_type_status']='unavailable'
    elif mutation=='reason':after['army_strengths'][0]['regiment_strengths'][0]['composition_unavailable_reason']='unread'
    snapshot=b.snapshot()
    decision=b.decision()
    planned=plan_registered_event_material_postcondition_v1(decision,snapshot['played_character'],snapshot=snapshot,snapshot_id=snapshot['snapshot_id'],revision=snapshot['revision'],native_revision=snapshot['native_revision'],date_raw=snapshot['date_raw'])
    rows.append(dict(kind='bookmark',mutation=mutation,decision=decision,snapshot=snapshot,expected=planned,selection=selection,result=evaluate_registered_event_material_postcondition_v1(expected,selection)))
for start,end in ((0,125000),(0,0),(1000000,1000000),(1000000,900000),(-100000,0),(-(1<<63),(1<<63)-1)):
    for mutation in ('none','character_id','date_raw','faith_id','rite_id','native_revision','revision','capture_epoch','same_instance','ack_only','wrong_option','missing_after'):
        decision,expected,selection=r._case(start,end)
        if mutation in ('character_id','date_raw','faith_id','rite_id'):selection[r.ENDING_FIELD][mutation]+=1
        elif mutation in ('native_revision','revision','capture_epoch'):selection[r.ENDING_FIELD][mutation]=selection[r.STARTING_FIELD][mutation]
        elif mutation=='same_instance':selection['new_event_instance_id']=29
        elif mutation=='ack_only':selection['postcondition_verified']=False
        elif mutation=='wrong_option':selection['selected_native_option_index']=1
        elif mutation=='missing_after':selection.pop(r.ENDING_FIELD)
        snapshot=r._snapshot()
        query=r._query(snapshot,start)
        before=r.rite_growth_fulfillment_observation_v1(query,snapshot=snapshot)
        planned=plan_registered_event_material_postcondition_v1(decision,snapshot['played_character'],snapshot=snapshot,religion_context=before,snapshot_id=snapshot['snapshot_id'],revision=snapshot['revision'],native_revision=snapshot['native_revision'],date_raw=snapshot['date_raw'])
        rows.append(dict(kind='rite',mutation=mutation,decision=decision,snapshot=snapshot,query=query,observation=before,expected=planned,selection=selection,result=evaluate_registered_event_material_postcondition_v1(expected,selection)))
raw=json.dumps(rows,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
if len(raw)>4*1024*1024:raise RuntimeError('bounded original producer output exceeded')
sys.stdout.buffer.write(raw)
""";

    @Test @Timeout(90)
    void actualProducerToBothDedicatedConsumersAndUnifiedDispatcherRoundTrips() throws Exception {
        JsonNode cases=oracle();assertEquals(85,cases.size());
        for(JsonNode row:cases) {
            String label=row.get("kind").textValue()+":"+row.get("mutation").textValue();ObjectNode snapshot=row.get("snapshot").deepCopy();JsonNode actual;
            if("bookmark".equals(row.get("kind").textValue())) {
                var planned=Bookmark1070Material.plan(row.get("decision"),snapshot).orElseThrow();
                assertEquals(row.get("expected"),StrictJson.parse(Bookmark1070Material.encode(planned)),label+" original plan");
                var decoded=Bookmark1070Material.decodeExpectation(Bookmark1070Material.encode(planned));assertEquals(planned,decoded,label+" typed plan round trip");
                actual=StrictJson.parse(Bookmark1070Material.encode(Bookmark1070Material.evaluate(decoded,row.get("selection"))));
            } else {
                var observation=RiteGrowthMaterial.observe(row.get("query"),snapshot);assertEquals(row.get("observation"),StrictJson.parse(RiteGrowthMaterial.encode(observation)),label+" actual query projection");
                assertEquals(observation,RiteGrowthMaterial.decodeObservation(StrictJson.parse(RiteGrowthMaterial.encode(observation))));
                snapshot.set(RiteGrowthMaterial.SNAPSHOT_FIELD,StrictJson.parse(RiteGrowthMaterial.encode(observation)));
                var planned=RiteGrowthMaterial.plan(row.get("decision"),snapshot).orElseThrow();
                assertEquals(row.get("expected"),StrictJson.parse(RiteGrowthMaterial.encode(planned)),label+" original plan");
                var decoded=RiteGrowthMaterial.decodeExpectation(RiteGrowthMaterial.encode(planned));assertEquals(planned,decoded,label+" typed plan round trip");
                actual=StrictJson.parse(RiteGrowthMaterial.encode(RiteGrowthMaterial.evaluate(decoded,row.get("selection"))));
            }
            assertEquals(row.get("result"),actual,label+" actual original material consumer");
            var expected=RegisteredEventMaterial.plan(retained(row.get("decision")),retained(snapshot)).orElseThrow();
            assertEquals(row.get("expected"),StrictJson.parse(RetainedJson.encode(expected)),label+" complete dispatch plan");
            assertEquals(row.get("result"),StrictJson.parse(RetainedJson.encode(RegisteredEventMaterial.evaluate(expected,retained(row.get("selection"))))),label+" complete dispatch result");
        }
    }
    @Test @Timeout(90)
    void strictIdentityFieldsMissingNullBoolFloatAndWrongNamesCannotReceiveCredit() throws Exception {
        JsonNode cases=oracle();JsonNode first=cases.get(0);byte[] expected=StrictJson.canonical(first.get("expected"));
        for(String field:List.of("selected_option_number","selected_native_option_index","starting_revision","old_event_instance_id")) {
            ObjectNode malformed=first.get("expected").deepCopy();malformed.put(field,true);ObjectNode booleanCase=malformed;assertThrows(IllegalArgumentException.class,()->Bookmark1070Material.decodeExpectation(StrictJson.canonical(booleanCase)));
            malformed=first.get("expected").deepCopy();malformed.put(field,2.0);ObjectNode floatCase=malformed;assertThrows(IllegalArgumentException.class,()->Bookmark1070Material.decodeExpectation(StrictJson.canonical(floatCase)));
            malformed=first.get("expected").deepCopy();malformed.remove(field);ObjectNode missing=malformed;assertThrows(IllegalArgumentException.class,()->Bookmark1070Material.decodeExpectation(StrictJson.canonical(missing)));
        }
        var plan=Bookmark1070Material.decodeExpectation(expected);ObjectNode ack=StrictJson.object().put("accepted",true);
        assertEquals(Bookmark1070Material.Status.UNAVAILABLE,Bookmark1070Material.evaluate(plan,ack).status());
        JsonNode rite=cases.get(13);ObjectNode snapshot=rite.get("snapshot").deepCopy();
        for(String field:List.of("spiritual_fulfillment_raw","raw_scale","played_character_id","queried_revision","snapshot_revision","capture_epoch")) {
            ObjectNode query=rite.get("query").deepCopy();query.put(field,true);assertEquals(RiteGrowthMaterial.Status.UNAVAILABLE,RiteGrowthMaterial.observe(query,snapshot).status());
            query=rite.get("query").deepCopy();query.putNull(field);assertEquals(RiteGrowthMaterial.Status.UNAVAILABLE,RiteGrowthMaterial.observe(query,snapshot).status());
        }
        ObjectNode absent=rite.get("query").deepCopy();absent.remove("rite_id");assertEquals(RiteGrowthMaterial.Status.UNAVAILABLE,RiteGrowthMaterial.observe(absent,snapshot).status());
        assertEquals(RiteGrowthMaterial.Status.UNAVAILABLE,RiteGrowthMaterial.plan(rite.get("decision"),snapshot).orElseThrow().status());
        var readCount=new java.util.concurrent.atomic.AtomicInteger();RiteGrowthMaterial.capture(revision->{readCount.incrementAndGet();assertEquals(BigInteger.valueOf(7),revision);return rite.get("query");},snapshot);assertEquals(1,readCount.get());
    }
    private static RetainedJson.ObjectValue retained(JsonNode n) { return RetainedJson.object(RetainedJson.parse(StrictJson.canonical(n))); }
    private static void verify(Path root) throws Exception {
        for(Pin pin:PINS){Path path=root.resolve(pin.path()).toRealPath();assertTrue(path.startsWith(root));byte[] raw=Files.readAllBytes(path);assertEquals(pin.bytes(),raw.length);assertEquals(pin.sha(),java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)),pin.path());}
    }
    private static JsonNode oracle() throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        if(repository==null||python==null)throw new IllegalStateException("complete actual producer parity requires explicit xar.repository.root and xar.python; unavailable is not a pass");
        Path root=Path.of(repository).toRealPath();verify(root);ProcessBuilder builder=new ProcessBuilder(python,"-I","-B","-c",ORACLE,root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONUTF8","1");builder.environment().put("PYTHONNOUSERSITE","1");builder.redirectErrorStream(true);
        Process process=builder.start();CompletableFuture<byte[]> output=CompletableFuture.supplyAsync(()->{try{return process.getInputStream().readNBytes(4*1024*1024+1);}catch(IOException e){throw new java.io.UncheckedIOException(e);}});
        try {process.getOutputStream().close();if(!process.waitFor(Duration.ofSeconds(60).toMillis(),TimeUnit.MILLISECONDS))throw new IllegalStateException("original event material producer timed out");byte[] raw=output.get(5,TimeUnit.SECONDS);verify(root);
            assertEquals(0,process.exitValue(),new String(raw,StandardCharsets.UTF_8));assertTrue(raw.length<=4*1024*1024);return StrictJson.parse(raw,4*1024*1024);
        } finally {if(process.isAlive())process.destroyForcibly();}
    }
}
