package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class DriverObservationAssemblerTest {
    static final String STATE="""
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained"}}
        """;
    static byte[] packet(String state) {
        byte[] json=DriverStateAssemblerTest.bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":"+state+"}");
        return ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
    }
    static NativeObservationPort.ObservedFrame actual(String state) {
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",DriverStateAssemblerTest.game(),BigInteger.valueOf(5),"held-session"),
                "snapshot-9",BigInteger.valueOf(9),new RawJson(DriverStateAssemblerTest.bytes(state.strip())),packet(state),Instant.parse("2026-10-23T16:00:00Z"));
    }
    static DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual) {
        var known=DriverStateAssemblerTest.known();
        return new DriverObservationFacts(known.driver(),3,7,actual.session(),actual.snapshotId(),actual.nativeRevision(),DriverJson.sha256(actual.state().bytes()),
                BigInteger.valueOf(2),1,DriverStateAssemblerTest.source(),new OpportunityJson.Obj(Map.of()),DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("actual-facts")));
    }
    static DriverObservationAssembler.Result join(String state) {
        var actual=actual(state);return new DriverObservationAssembler().assemble(actual,facts(actual),DriverStateAssemblerTest.ref(actual.originalPacket()));
    }
    @Test void framedNativeProducerToFullDriverConsumerPreservesAllHistoryAndOriginalEvidence() {
        var actual=actual(STATE);var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,join(STATE));
        assertEquals(DriverStateAssemblerTest.identity(),complete.identity());
        assertEquals(2,OpportunityJson.array(complete.semantic().get("native_command_history"),"history").size());
        assertEquals(DriverJson.sha256(actual.originalPacket()),complete.originalEvidence().sha256());
        assertNotEquals(DriverJson.sha256(actual.state().bytes()),complete.originalEvidence().sha256());
    }
    @Test void invalidFramingAndPacketStateMismatchCannotBecomeComplete() {
        var actual=actual(STATE);byte[] broken=actual.originalPacket();broken[0]^=1;
        var invalid=new NativeObservationPort.ObservedFrame(actual.session(),actual.snapshotId(),actual.nativeRevision(),actual.state(),broken,actual.observedAt());
        assertInstanceOf(DriverObservationAssembler.Incomplete.class,new DriverObservationAssembler().assemble(invalid,facts(invalid),DriverStateAssemblerTest.ref(broken)));
        var mismatch=new NativeObservationPort.ObservedFrame(actual.session(),actual.snapshotId(),actual.nativeRevision(),new RawJson(DriverStateAssemblerTest.bytes(STATE.replace("\"speed\":3","\"speed\":4"))),actual.originalPacket(),actual.observedAt());
        assertInstanceOf(DriverObservationAssembler.Incomplete.class,new DriverObservationAssembler().assemble(mismatch,facts(mismatch),DriverStateAssemblerTest.ref(mismatch.originalPacket())));
    }
    @Test void absentNullAndUnreconciledPlayerStayDeathCapableWithoutInventedIdentity() {
        for(String state:List.of(STATE.replace("\"played_character\":{\"character_id\":73,\"alive\":true},",""),
                STATE.replace("{\"character_id\":73,\"alive\":true}","null"),STATE.replace("\"character_id\":73","\"character_id\":74"))) {
            var actual=actual(state);var full=new DriverObservationAssembler().projectFull(actual,facts(actual),DriverStateAssemblerTest.ref(actual.originalPacket()));
            assertEquals(DriverJson.object(DriverStateAssemblerTest.bytes(state),65536).get("played_character"),full.semantic().get("played_character"));
            assertInstanceOf(DriverObservationAssembler.Incomplete.class,join(state));
        }
    }
    @Test void wrongTypedNativeFieldsAndMissingExplicitModalCannotBecomeComplete() {
        for(String bad:List.of(STATE.replace("\"paused\":true","\"paused\":1"),STATE.replace("\"character_id\":73","\"character_id\":73.0"),
                STATE.replace("\"active_event\":null,","")))assertInstanceOf(DriverObservationAssembler.Incomplete.class,join(bad));
    }
    @Test void fullBindingIncludesPresenceAndEntireEventPayload() {
        var absent=DriverJson.object(DriverStateAssemblerTest.bytes("{}"),1000);
        var nil=DriverJson.object(DriverStateAssemblerTest.bytes("{\"active_event\":null}"),1000);
        var first=DriverJson.object(DriverStateAssemblerTest.bytes("{\"active_event\":{\"id\":\"event\",\"options\":[{\"id\":1,\"enabled\":true}]}}"),1000);
        var second=DriverJson.object(DriverStateAssemblerTest.bytes("{\"active_event\":{\"id\":\"event\",\"options\":[{\"id\":1,\"enabled\":false}]}}"),1000);
        assertNotEquals(DriverObservationAssembler.bindingSha256(absent),DriverObservationAssembler.bindingSha256(nil));
        assertNotEquals(DriverObservationAssembler.bindingSha256(first),DriverObservationAssembler.bindingSha256(second));
    }
    @Test void fullNativeFrameExceedsProposalBudgetAndRetainedBeforeRequiresExactEvidence() throws InterruptedException {
        String large=STATE.replace("\"original\":\"retained\"","\"original\":\""+"x".repeat(150000)+"\"");
        var actual=actual(large);
        var held=new HeldDriverObservationPort(deadline -> actual,frame -> new DriverObservationFacts.Known(facts(frame)),
                frame -> DriverStateAssemblerTest.ref(frame.originalPacket()),new DriverObservationAssembler(),2);
        var complete=held.observe(Instant.parse("2030-01-01T00:00:00Z"));
        assertSame(complete,held.requireRetained(complete.identity(),complete.originalEvidence()));
        assertThrows(IllegalStateException.class,() -> held.requireRetained(complete.identity(),DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("different actual evidence"))));
        var omitted=held.snapshot(Instant.parse("2030-01-01T00:00:00Z"),false);
        assertEquals(2,omitted.totalCount());assertEquals(0,omitted.includedCount());
        assertEquals(2,OpportunityJson.array(omitted.actual().semantic().get("native_command_history"),"actual history").size());
        assertTrue(OpportunityJson.array(omitted.semantic().get("native_command_history"),"export history").isEmpty());
    }
    @Test void archivedProducerManifestRebuildsCompleteObservationAndPreservesOriginalStateTokens() {
        var actual=actual(STATE.replace("\"speed\":3","\"speed\":3,\"original_metric\":1.00"));
        var known=DriverStateAssemblerTest.known();
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(2),1,
                DriverStateAssemblerTest.source(),new OpportunityJson.Obj(Map.of()),DriverStateAssemblerTest.ref(known.driver().encode()));
        var manifestRef=DriverStateAssemblerTest.ref(manifest.bytes());
        var replay=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,actual.originalPacket());
        assertArrayEquals(actual.state().bytes(),replay.state().bytes());
        var restoredFacts=DriverObservationEvidenceReader.decode(manifestRef,manifest,new RawJson(known.driver().encode()),replay);
        var result=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(replay,restoredFacts,
                DriverStateAssemblerTest.ref(replay.originalPacket())));
        assertEquals(2,OpportunityJson.array(result.semantic().get("native_command_history"),"native_command_history").size());
        assertEquals(manifestRef,DriverObservationEvidenceReader.reference(result.semantic().get("java_driver_facts_evidence")));
        assertEquals(DriverStateAssemblerTest.game(),result.identity().game());
        assertEquals(new BigInteger("9007199254740993"),result.identity().game().creationFiletime().value());
    }
    @Test void archivedManifestRejectsChangedDriverPacketAndNumericFiletime() {
        var actual=actual(STATE);var known=DriverStateAssemblerTest.known();
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(2),1,
                DriverStateAssemblerTest.source(),new OpportunityJson.Obj(Map.of()),DriverStateAssemblerTest.ref(known.driver().encode()));
        var exact=DriverStateAssemblerTest.ref(manifest.bytes());
        var changedDriver=new RawJson(DriverStateAssemblerTest.bytes(new String(known.driver().encode(),java.nio.charset.StandardCharsets.UTF_8).replace("campaign-original","changed-campaign")));
        assertThrows(IllegalArgumentException.class,() -> DriverObservationEvidenceReader.decode(exact,manifest,changedDriver,actual));
        byte[] changedPacket=actual.originalPacket();changedPacket[changedPacket.length-2]^=1;
        assertThrows(IllegalArgumentException.class,() -> DriverObservationEvidenceReader.nativeFrame(exact,manifest,changedPacket));
        var numericBirth=new RawJson(DriverStateAssemblerTest.bytes(new String(manifest.bytes(),java.nio.charset.StandardCharsets.UTF_8)
                .replace("\"creation_filetime\":\"9007199254740993\"","\"creation_filetime\":9007199254740993")));
        assertThrows(IllegalArgumentException.class,() -> DriverObservationEvidenceReader.nativeFrame(DriverStateAssemblerTest.ref(numericBirth.bytes()),numericBirth,actual.originalPacket()));
    }
}
