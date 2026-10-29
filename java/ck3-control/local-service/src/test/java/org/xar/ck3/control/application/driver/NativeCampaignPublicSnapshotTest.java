package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Same-packet DATA regression through the actual manifest, assembler, public exporter and GUI context producer.
 * These software originals do not grant Stage, Native, Prepared, a one-life identity or gameplay admission. */
final class NativeCampaignPublicSnapshotTest {
    private static final String MARKER="xar_java_snapshot_projection";
    private static final List<String> EPISODE=List.of("episode_run_id","episode_character_id","succession_lifecycle",
            "episode_identity_pending","one_life_terminal","one_life_terminal_reason");
    private static final String DRIVER="""
        {"format_version":2,"pipe_name":"fixture-pipe","bridge_pid":42,"episode_character_id":311,"episode_run_id":"private-fixture-stage",
         "last_checkpoint":null,"command_history":[{"index":1,"command":"original-query","ok":true,"result":{"metric":12.00}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,"succession_lifecycle":null,
         "campaign_goal":{"original":"retained"},"rollback_war_failures":[]}
        """;
    private record Original(DriverObservationAssembler.Complete complete,DriverObservationAssembler.FullSnapshot full,
            RawJson facts,RawJson driver) { }
    private static byte[] bytes(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(byte[] wire){return new ExactRef("D:/fixture-data/original",wire.length,DriverJson.sha256(wire));}
    private static RawJson raw(Obj value){return RawJson.fullMaterial(DriverJson.encode(value));}
    private static Original original(String episodeFields){
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var auxiliary=new Obj(Map.of("episode_projection",new Text("native_campaign"),"original_auxiliary",new DecimalValue("-0.00")));
        var before=DriverFactsRepository.imported(ref(bytes(DRIVER)),bytes(DRIVER),7,3,game,auxiliary);
        String state="{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":53144328,"
                +"\"played_character\":{\"character_id\":922,\"alive\":true},\"active_event\":null,"
                +"\"pending_character_interaction\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{}"+episodeFields+"}";
        byte[] body=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"actual-fixture-read\",\"revision\":9,\"state\":"+state+"}");
        byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("fixture-machine",game,BigInteger.valueOf(5),"fixture-session"),
                "actual-fixture-read",BigInteger.valueOf(9),new RawJson(bytes(state)),packet,Instant.parse("2026-10-24T23:00:00Z"));
        var projected=InitialDriverState.fixtureActorProjection(before,actual,before.auxiliary());
        var source=new G2Source("fixture-machine","2026-10-24T23:00:00Z","actual-fixture-source",ref(bytes("original fixture sources")));
        var manifest=DriverObservationEvidenceReader.encode(projected,actual,BigInteger.valueOf(12),
                DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,source,projected.auxiliary(),ref(projected.driver().encode()));
        var restored=DriverObservationEvidenceReader.nativeFrame(ref(manifest.bytes()),manifest,packet);
        var driver=RawJson.fullMaterial(projected.driver().encode());
        var facts=DriverObservationEvidenceReader.decode(ref(manifest.bytes()),manifest,driver,restored);
        var assembler=new DriverObservationAssembler();
        var full=assembler.projectFull(restored,facts,ref(packet));
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,assembler.assemble(restored,facts,ref(packet)));
        return new Original(complete,full,manifest,driver);
    }
    @Test void actualProfileFourKeepsMissingNullAndOriginalValuesThroughAllSnapshotConsumers(){
        for(String fields:List.of("",
                ",\"episode_run_id\":null,\"episode_character_id\":null,\"succession_lifecycle\":null,\"episode_identity_pending\":null,\"one_life_terminal\":null,\"one_life_terminal_reason\":null",
                ",\"episode_run_id\":\"original-native-episode\",\"episode_character_id\":311,\"succession_lifecycle\":{\"original\":12.00},\"episode_identity_pending\":false,\"one_life_terminal\":true,\"one_life_terminal_reason\":\"original-reason\"")){
            var original=original(fields);var complete=original.complete();var semantic=complete.semantic();
            var wire=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(complete,true));
            var publicTree=DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES);
            assertEquals(BigInteger.valueOf(4),integer(object(publicTree.get(MARKER),MARKER).get("observation_version"),"profile"));
            assertFalse(semantic.members().containsKey(MARKER));
            assertEquals(semantic,PublicSnapshotCodec.decode(wire));
            assertEquals(semantic,DriverJson.object(PublicSnapshotCodec.decodeSemanticData(wire).bytes(),RawJson.MAXIMUM_BYTES));
            assertEquals(semantic,DriverJson.object(PublicSnapshotCodec.decodePlanningSnapshotData(wire).bytes(),RawJson.MAXIMUM_BYTES));
            var context=DriverPublicContext.from(complete);
            assertArrayEquals(wire.bytes(),context.snapshot().bytes());
            assertEquals(semantic,PublicSnapshotCodec.decode(context.snapshot()));
            assertEquals(object(publicTree.get("diagnostics"),"diagnostics"),DriverJson.object(context.diagnostics().bytes(),RawJson.MAXIMUM_BYTES));
            var nativeOriginal=DriverObservationAssembler.originalNativeState(original.full().actual());
            for(String key:EPISODE){
                assertEquals(nativeOriginal.members().containsKey(key),publicTree.members().containsKey(key),key);
                assertEquals(nativeOriginal.get(key),publicTree.get(key),key);
            }
            assertEquals("private-fixture-stage",complete.identity().frame().episodeRunId());
            assertEquals(BigInteger.valueOf(922),complete.identity().frame().identity().player());
            assertEquals(new Text("12"),publicTree.get("revision"));assertEquals(new Text("9"),publicTree.get("native_revision"));
            assertTrue(new String(wire.bytes(),StandardCharsets.UTF_8).contains("12.00"));
            assertTrue(new String(wire.bytes(),StandardCharsets.UTF_8).contains("-0.00"));
            var physical=ref(bytes("actual held proof DATA"));
            var originals=new PublicSnapshotCodec.FullSnapshotOriginals(original.full(),physical,physical,physical,original.facts(),original.driver());
            assertEquals(semantic,PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(PublicSnapshotCodec.exportFull(originals,true))));
            var omitted=PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(complete,false)));
            assertTrue(array(omitted.get("native_command_history"),"history").isEmpty());
            for(String key:EPISODE){assertEquals(semantic.members().containsKey(key),omitted.members().containsKey(key));assertEquals(semantic.get(key),omitted.get(key));}
            var semanticOnly=PublicSnapshotCodec.decodeSemanticOnly(PublicSnapshotCodec.exportSemanticOnly(complete));
            assertFalse(semanticOnly.members().containsKey("native_command_history"));
            for(String key:EPISODE){assertEquals(semantic.members().containsKey(key),semanticOnly.members().containsKey(key));assertEquals(semantic.get(key),semanticOnly.get(key));}
        }
    }
    @Test void rawNativeMarkerCannotIssueProfileFourAndMalformedPublicMarkersAreRejected(){
        var original=original("");var semantic=original.complete().semantic();
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodeSemanticData(raw(semantic)));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningSnapshotData(raw(semantic)));
        var wire=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(original.complete(),true));
        var publicTree=DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES);
        var fields=new LinkedHashMap<>(publicTree.members());fields.remove(MARKER);
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(raw(new Obj(fields))));
        for(Value malformed:List.<Value>of(Nil.INSTANCE,new Text("4"),
                new Obj(Map.of("schema",new Text("xar.java-public-snapshot-projection/v1"),"observation_version",new Text("4"))),
                new Obj(Map.of("schema",new Text("xar.java-public-snapshot-projection/v1"),"observation_version",new IntegerValue(BigInteger.valueOf(3)))),
                new Obj(Map.of("schema",new Text("xar.java-public-snapshot-projection/v1"),"observation_version",new IntegerValue(BigInteger.valueOf(4)),"extra",Nil.INSTANCE)))){
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(raw(publicTree.with(MARKER,malformed))));
        }
        var marker=publicTree.get(MARKER);
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(raw(publicTree.with("episode_projection",new Text("ordinary")))));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodeSemanticData(raw(semantic.with(MARKER,marker))));
        assertThrows(IllegalArgumentException.class,()->new DriverObservationAssembler.Complete(original.complete().identity(),original.complete().source(),
                original.complete().sessionId(),original.complete().connectionGeneration(),semantic,original.complete().originalEvidence(),
                original.complete().observedAt(),original.complete().fullBindingSha256()));
        assertThrows(IllegalArgumentException.class,()->new DriverObservationAssembler.Complete(original.complete().identity(),original.complete().source(),
                original.complete().sessionId(),original.complete().connectionGeneration(),semantic.with("episode_run_id",new Text("invented")),
                original.complete().originalEvidence(),original.complete().observedAt(),original.complete().fullBindingSha256(),original.complete().originalProjection()));
    }
    @Test void ordinaryDataRetainsItsOriginalEpisodeRequirementsAndDoesNotIssueTheNewMarker(){
        Obj original=original("").complete().semantic().with("episode_run_id",new Text("ordinary-episode"))
                .with("episode_character_id",new IntegerValue(BigInteger.valueOf(922))).with("one_life_terminal_reason",Nil.INSTANCE);
        var wire=PublicSnapshotCodec.encodeSemanticData(raw(original));
        assertEquals(original,PublicSnapshotCodec.decode(wire));
        assertFalse(DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES).members().containsKey(MARKER));
        for(Value wrong:List.<Value>of(Nil.INSTANCE,new IntegerValue(BigInteger.ONE),new Text("")))
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodeSemanticData(raw(original.with("episode_run_id",wrong))));
        for(Value wrong:List.<Value>of(Nil.INSTANCE,new Bool(true),new DecimalValue("922.0"),new IntegerValue(BigInteger.valueOf(2147483648L))))
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodeSemanticData(raw(original.with("episode_character_id",wrong))));
    }
}
