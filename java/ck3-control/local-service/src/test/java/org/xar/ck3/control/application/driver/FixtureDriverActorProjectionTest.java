package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
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

/** DATA regression for the sole guarded fixture publisher's exact projection; no Stage or Native grant is fabricated. */
final class FixtureDriverActorProjectionTest {
    private static final String DRIVER="""
        {"format_version":2,"pipe_name":"fixture-pipe","bridge_pid":42,"episode_character_id":311,"episode_run_id":"private-fixture-stage",
         "last_checkpoint":null,"command_history":[{"index":1,"command":"original-query","ok":true,"result":{"metric":12.00}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,"succession_lifecycle":null,
         "campaign_goal":{"original":"retained"},"rollback_war_failures":[]}
        """;
    private static byte[] bytes(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(byte[] wire){return new ExactRef("memory/actual-fixture-original",wire.length,DriverJson.sha256(wire));}
    private static GameGeneration game(){return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));}
    private static DriverSnapshotFacts.Known before(){
        return DriverFactsRepository.imported(ref(bytes(DRIVER)),bytes(DRIVER),7,3,game(),
                new OpportunityJson.Obj(Map.of("episode_projection",new OpportunityJson.Text("native_campaign"),
                        "original_auxiliary",new OpportunityJson.DecimalValue("-0.00"))));
    }
    private static NativeObservationPort.ObservedFrame actual(String actor,String episodeFields){
        String state="{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":53144328,"
                +"\"played_character\":{\"character_id\":"+actor+",\"alive\":true},\"active_event\":null,"
                +"\"pending_character_interaction\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{}"+episodeFields+"}";
        byte[] body=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"actual-fixture-read\",\"revision\":9,\"state\":"+state+"}");
        byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("fixture-machine",game(),BigInteger.valueOf(5),"fixture-session"),
                "actual-fixture-read",BigInteger.valueOf(9),new RawJson(bytes(state)),packet,Instant.parse("2026-10-24T23:00:00Z"));
    }

    @Test void actorChangeRetainsHistoryEpochRunGameAndAuxiliaryWithoutOneLifeLifecycle(){
        var before=before();var actual=actual("922","");
        var after=InitialDriverState.fixtureActorProjection(before,actual,before.auxiliary());
        assertEquals(BigInteger.valueOf(922),after.driver().session().actorId());
        assertEquals(before.stamp().driverVersion()+1,after.stamp().driverVersion());
        assertEquals(before.stamp().episodeEpoch(),after.stamp().episodeEpoch());
        assertEquals(before.stamp().episodeRunId(),after.stamp().episodeRunId());
        assertEquals(before.stamp().game(),after.stamp().game());
        assertEquals(before.originalHistoryBasis(),after.originalHistoryBasis());
        assertEquals(before.actionRows(),after.actionRows());assertEquals(before.auxiliary(),after.auxiliary());
        assertEquals(before.loop(),after.loop());assertTrue(after.observation().isEmpty());
        assertArrayEquals(before.driver().commandHistory().getFirst().originalRow().json(),after.driver().commandHistory().getFirst().originalRow().json());
        assertInstanceOf(org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue.class,after.driver().successionLifecycle());
        var known=DriverSnapshotFacts.encodeKnownOriginal(after);
        var replay=DriverSnapshotFacts.decodeKnownOriginal(known,java.util.Optional.empty());
        assertArrayEquals(after.driver().encode(),replay.driver().encode());assertEquals(after.stamp(),replay.stamp());
        assertEquals(after.auxiliary(),replay.auxiliary());
    }

    @Test void unchangedActorKeepsTheIdenticalOwnerAndInvalidNativeActorsNeverProject(){
        var before=before();assertSame(before,InitialDriverState.fixtureActorProjection(before,actual("311",""),before.auxiliary()));
        for(String token:List.of("true","922.0","-1","2147483648"))
            assertThrows(IllegalArgumentException.class,()->InitialDriverState.fixtureActorProjection(before,actual(token,""),before.auxiliary()));
    }

    @Test void actualManifestAndSoleAssemblerReplayProfileFourWithOriginalEpisodeDomains(){
        for(String episode:List.of("",",\"episode_run_id\":null,\"succession_lifecycle\":null",
                ",\"episode_run_id\":\"original-native-value\",\"succession_lifecycle\":{\"original\":true}")){
            var before=before();var actual=actual("922",episode);
            var after=InitialDriverState.fixtureActorProjection(before,actual,before.auxiliary());
            var source=new G2Source("fixture-machine","2026-10-24T23:00:00Z","actual-fixture-source",ref(bytes("original fixture sources")));
            var manifest=DriverObservationEvidenceReader.encode(after,actual,BigInteger.valueOf(12),
                    DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,source,after.auxiliary(),ref(after.driver().encode()));
            var manifestRef=ref(manifest.bytes());var restored=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,actual.originalPacket());
            var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,RawJson.fullMaterial(after.driver().encode()),restored);
            var assembler=new DriverObservationAssembler();var full=assembler.projectFull(restored,facts,ref(actual.originalPacket()));
            var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,assembler.assemble(restored,facts,ref(actual.originalPacket())));
            assertEquals(full.semantic(),complete.semantic());
            assertTrue(complete.originalProjection().isPresent());
            assertSame(restored,complete.originalProjection().orElseThrow().actual());
            assertThrows(IllegalArgumentException.class,()->new DriverObservationAssembler.Complete(complete.identity(),complete.source(),
                    complete.sessionId(),complete.connectionGeneration(),complete.semantic(),complete.originalEvidence(),complete.observedAt(),complete.fullBindingSha256()));
            assertEquals(new OpportunityJson.Text("native_campaign"),complete.semantic().get("episode_projection"));
            var raw=DriverObservationAssembler.originalNativeState(actual);
            for(String key:List.of("episode_run_id","episode_character_id","succession_lifecycle","one_life_terminal_reason","episode_identity_pending","one_life_terminal")){
                assertEquals(raw.members().containsKey(key),complete.semantic().members().containsKey(key));
                assertEquals(raw.get(key),complete.semantic().get(key));
            }
            assertEquals("private-fixture-stage",complete.identity().frame().episodeRunId());
            assertEquals(BigInteger.valueOf(922),complete.identity().frame().identity().player());
            NativeCampaignProjection.requireJoinedSnapshot(full,RawJson.fullMaterial(DriverJson.encode(complete.semantic())));
            assertArrayEquals(actual.originalPacket(),restored.originalPacket());
        }
    }
}
