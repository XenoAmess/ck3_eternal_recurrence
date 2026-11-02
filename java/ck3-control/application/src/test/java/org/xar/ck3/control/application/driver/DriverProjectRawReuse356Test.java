package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public software DATA only; no physical archive, Root issuer or Native operation permission. */
public final class DriverProjectRawReuse356Test {
    private static final Instant AT=Instant.parse("2026-10-23T16:00:00Z");
    private static final String WIRE="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":null,
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;
    private static final String STATE="""
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained"},"original_metric":-0.00}
        """;

    @Test
    public void profilesThreeAndFourRetainOriginalValuesAndEpisodePresence() {
        for(long profile:new long[]{3,4}) {
            var actual=actual(STATE,packet(STATE));
            var known=known();
            byte[] driver=known.driver().encode();
            var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.TWO,profile,
                    source(),extras(profile),ref(driver));
            byte[] callerPacket=actual.originalPacket();
            var nativeRef=ref(callerPacket);
            var result=DriverObservationEvidenceReader.replayOriginals(ref(manifest.bytes()),manifest,
                    new RawJson(driver),callerPacket,nativeRef);
            var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,result);
            var semantic=complete.semantic();

            assertEquals("-0.00",assertInstanceOf(OpportunityJson.DecimalValue.class,semantic.get("original_metric")).token());
            var history=assertInstanceOf(OpportunityJson.Arr.class,semantic.get("native_command_history"));
            assertEquals(2,history.items().size());
            var first=assertInstanceOf(OpportunityJson.Obj.class,history.items().get(0));
            var originalResult=assertInstanceOf(OpportunityJson.Obj.class,first.get("result"));
            assertEquals("1.0",assertInstanceOf(OpportunityJson.DecimalValue.class,originalResult.get("scale")).token());
            assertEquals(new OpportunityJson.Bool(false),assertInstanceOf(OpportunityJson.Obj.class,history.items().get(1)).get("ok"));
            assertEquals(new OpportunityJson.Text("original native rejection"),assertInstanceOf(OpportunityJson.Obj.class,history.items().get(1)).get("error"));
            assertEquals(new OpportunityJson.Text("retained"),assertInstanceOf(OpportunityJson.Obj.class,semantic.get("diagnostics")).get("original"));
            assertEquals(OpportunityJson.Nil.INSTANCE,semantic.get("one_life_terminal_reason"));
            assertEquals(ref(manifest.bytes()),DriverObservationEvidenceReader.reference(
                    assertInstanceOf(OpportunityJson.Obj.class,semantic.get("java_driver_facts_evidence"))));
            assertEquals(new BigInteger("9007199254740993"),complete.identity().game().creationFiletime().value());
            assertEquals(profile,complete.identity().observationVersion());
            assertEquals(source(),complete.source());
            assertEquals("held-session",complete.sessionId());
            assertEquals(BigInteger.valueOf(5),complete.connectionGeneration());
            assertEquals(AT,complete.observedAt());
            assertEquals(nativeRef,complete.originalEvidence());
            assertEquals(profile==4,complete.originalProjection().isPresent());
            if(profile==3) {
                assertEquals(new OpportunityJson.Text("episode-real-1"),semantic.get("episode_run_id"));
                assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(73)),semantic.get("episode_character_id"));
                assertEquals(OpportunityJson.Nil.INSTANCE,semantic.get("succession_lifecycle"));
                assertFalse(semantic.members().containsKey("episode_projection"));
            } else {
                assertFalse(semantic.members().containsKey("episode_run_id"));
                assertFalse(semantic.members().containsKey("episode_character_id"));
                assertFalse(semantic.members().containsKey("succession_lifecycle"));
                assertEquals(new OpportunityJson.Text("native_campaign"),semantic.get("episode_projection"));
                assertArrayEquals(actual.state().bytes(),complete.originalProjection().orElseThrow().actual().state().bytes());
                assertArrayEquals(packet(STATE),complete.originalProjection().orElseThrow().actual().originalPacket());
            }
            byte[] before=DriverJson.encode(semantic);
            String binding=complete.fullBindingSha256();
            callerPacket[0]^=1;
            assertArrayEquals(before,DriverJson.encode(complete.semantic()));
            assertEquals(binding,complete.fullBindingSha256());
            assertEquals(nativeRef,complete.originalEvidence());
            assertArrayEquals(packet(STATE),actual.originalPacket());
        }
    }

    @Test
    public void publicEntryAndFreshReplayStillRejectChangedOriginals() {
        byte[] good=packet(STATE);
        var frame=actual(STATE,good);
        assertNotNull(DriverObservationAssembler.canonicalNativeState(frame));
        byte[] badLength=good.clone(); badLength[0]^=1;
        assertThrows(IllegalArgumentException.class,()->DriverObservationAssembler.canonicalNativeState(actual(STATE,badLength)));
        assertThrows(IllegalArgumentException.class,()->DriverObservationAssembler.canonicalNativeState(
                actual(STATE.replace("\"paused\":true","\"paused\":false"),good)));

        var known=known();
        byte[] driver=known.driver().encode();
        var manifest=DriverObservationEvidenceReader.encode(known,frame,BigInteger.TWO,3,source(),extras(3),ref(driver));
        var manifestRef=ref(manifest.bytes());
        var nativeRef=ref(good);
        assertInstanceOf(DriverObservationAssembler.Complete.class,DriverObservationEvidenceReader.replayOriginals(
                manifestRef,manifest,new RawJson(driver),good,nativeRef));
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.replayOriginals(
                manifestRef,manifest,new RawJson(driver),badLength,nativeRef));
        var changedDriver=new RawJson(bytes(new String(driver,StandardCharsets.UTF_8).replace("campaign-original","changed-campaign")));
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.replayOriginals(
                manifestRef,manifest,changedDriver,good,nativeRef));
        assertInstanceOf(DriverObservationAssembler.Incomplete.class,DriverObservationEvidenceReader.replayOriginals(
                manifestRef,manifest,new RawJson(driver),good,ref(bytes("bad-native-evidence"))));

        var contradictory=DriverObservationEvidenceReader.encode(known,frame,BigInteger.TWO,3,source(),
                new OpportunityJson.Obj(Map.of("paused",new OpportunityJson.Bool(false))),ref(driver));
        assertInstanceOf(DriverObservationAssembler.Incomplete.class,DriverObservationEvidenceReader.replayOriginals(
                ref(contradictory.bytes()),contradictory,new RawJson(driver),good,nativeRef));
    }

    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] bytes) { return new ExactRef("memory/test-original356.json",bytes.length,DriverJson.sha256(bytes)); }
    private static GameGeneration game() { return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    private static DriverSnapshotFacts.Known known() {
        return DriverFactsRepository.imported(ref(bytes(WIRE)),bytes(WIRE),3,7,game(),new OpportunityJson.Obj(Map.of()));
    }
    private static G2Source source() {
        return new G2Source("test-machine",AT.toString(),"test-source",ref(bytes("original-source356")));
    }
    private static OpportunityJson.Obj extras(long profile) {
        return new OpportunityJson.Obj(profile==4?Map.of("episode_projection",new OpportunityJson.Text("native_campaign")):Map.of());
    }
    private static byte[] packet(String state) {
        byte[] body=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":"+state+"}");
        return ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
    }
    private static NativeObservationPort.ObservedFrame actual(String state,byte[] packet) {
        var session=new NativeObservationPort.TransportSession("test-machine",game(),BigInteger.valueOf(5),"held-session");
        return new NativeObservationPort.ObservedFrame(session,"snapshot-9",BigInteger.valueOf(9),new RawJson(bytes(state.strip())),packet,AT);
    }
}
