package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Map;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

public class TypedDriverReplay313Test {

    private static final String WIRE = """
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}""";

    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained"},"original_metric":1.00}""";

    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] raw) { return new ExactRef("memory/test-original.json", raw.length, DriverJson.sha256(raw)); }
    private static GameGeneration game() { return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    private static G2Source source() { return new G2Source("test-machine", "2026-10-23T16:00:00Z", "test-source", ref(bytes("original-source"))); }

    private static byte[] packet(String state) {
        String json = "{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":" + state + "}";
        byte[] jsonBytes = bytes(json);
        ByteBuffer buffer = ByteBuffer.allocate(jsonBytes.length + 4).order(ByteOrder.LITTLE_ENDIAN);
        buffer.putInt(jsonBytes.length);
        buffer.put(jsonBytes);
        return buffer.array();
    }

    private static NativeObservationPort.ObservedFrame actual(String state) {
        var session = new NativeObservationPort.TransportSession("test-machine", game(), BigInteger.valueOf(5), "held-session");
        var rawState = new RawJson(bytes(state.strip()));
        var framed = packet(state);
        return new NativeObservationPort.ObservedFrame(session, "snapshot-9", BigInteger.valueOf(9), rawState, framed, Instant.parse("2026-10-23T16:00:00Z"));
    }

    private record Fixture(DriverStateSnapshot.Complete driver, NativeObservationPort.ObservedFrame actual,
            RawJson manifest, ExactRef manifestRef) { }
    private static Fixture fixture(DriverStateSnapshot.Complete driver) {
        byte[] wire=driver.encode();
        var known=DriverFactsRepository.imported(ref(wire),wire,3,7,game(),new OpportunityJson.Obj(Map.of()));
        var frame=actual(STATE);
        var manifest=DriverObservationEvidenceReader.encode(known,frame,BigInteger.valueOf(2),1,source(),
                new OpportunityJson.Obj(Map.of()),ref(wire));
        return new Fixture(driver,frame,manifest,ref(manifest.bytes()));
    }
    private static DriverStateSnapshot.Complete copy(DriverStateSnapshot.Complete base,
            List<DriverStateSnapshot.HistoryEntry> history, DriverStateSnapshot.Slot lifecycle,
            DriverStateSnapshot.Slot goal) {
        return new DriverStateSnapshot.Complete(base.session(),history,base.lastCheckpoint(),base.rollbackWarFailure(),
                base.managedRestoreTransaction(),base.successionExpectation(),lifecycle,goal,base.rollbackWarFailures());
    }
    private static Fixture manifest(Fixture before,OpportunityJson.Obj row) {
        var material=RawJson.fullMaterial(DriverJson.encode(row));
        return new Fixture(before.driver(),before.actual(),material,ref(material.bytes()));
    }
    private static NativeObservationPort.ObservedFrame changed(Fixture f,NativeObservationPort.TransportSession transport,
            String snapshot,BigInteger revision,RawJson state,byte[] packet,Instant observed) {
        return new NativeObservationPort.ObservedFrame(transport,snapshot,revision,state,packet,observed);
    }
    private static void equivalent(Fixture f) {
        var old=DriverObservationEvidenceReader.decode(f.manifestRef(),f.manifest(),new RawJson(f.driver().encode()),f.actual());
        var typed=DriverObservationEvidenceReader.decodeTypedDriver(f.manifestRef(),f.manifest(),f.driver(),f.actual());
        assertEquals(old,typed);
        assertArrayEquals(old.driver().encode(),typed.driver().encode());
        assertSame(f.driver(),typed.driver());
        assertEquals(new BigInteger("9007199254740993"),typed.transport().game().creationFiletime().value());
    }
    private static void rejects(Fixture f,DriverStateSnapshot.Complete driver,NativeObservationPort.ObservedFrame frame) {
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.decode(
                f.manifestRef(),f.manifest(),new RawJson(driver.encode()),frame));
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.decodeTypedDriver(
                f.manifestRef(),f.manifest(),driver,frame));
    }

    @Test
    public void typedFactsMatchOriginalPublicPathForImmutableNullableAndOpaqueData() {
        var base=DriverStateSnapshot.decodeComplete(bytes(WIRE));
        byte[] original=bytes("{\"opaque_source\":{\"nested\":[null,1.00,{\"name\":\"snowman-☃\"}]}}");
        var opaque=new DriverStateSnapshot.Value(original);
        original[0]='[';
        var missing=copy(base,base.commandHistory(),new DriverStateSnapshot.Missing(),opaque);
        var nullSlot=copy(base,base.commandHistory(),new DriverStateSnapshot.NullValue(),opaque);
        // Complete/HistoryEntry certify their wire/index, not ordinary action eligibility or command/ok fields.
        var opaqueHistory=List.of(new DriverStateSnapshot.HistoryEntry(1,new DriverStateSnapshot.Value(
                bytes("{\"index\":1,\"opaque\":{\"lifecycle_source\":[null,1.00,true]}}"))));
        var sourceData=copy(base,opaqueHistory,base.successionLifecycle(),opaque);
        var largeAllowed=copy(base,base.commandHistory(),base.successionLifecycle(),
                new DriverStateSnapshot.Value(bytes("{\"n\":"+"1".repeat(4300)+"}")));
        for(var driver:List.of(base,missing,nullSlot,sourceData,largeAllowed))equivalent(fixture(driver));
        assertInstanceOf(DriverStateSnapshot.Missing.class,missing.successionLifecycle());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,nullSlot.successionLifecycle());
        assertTrue(new String(missing.encode(),StandardCharsets.UTF_8).contains("1.00"));
        byte[] escaped=opaque.json();escaped[0]='[';
        equivalent(fixture(missing));
    }

    @Test
    public void originalProtocolRoundtripAndNativeSourceBindingsRemainStrict() {
        var base=DriverStateSnapshot.decodeComplete(bytes(WIRE));var f=fixture(base);var a=f.actual();
        var wrongRef=new ExactRef(f.manifestRef().path(),f.manifestRef().bytes(),"0".repeat(64));
        rejects(new Fixture(base,a,f.manifest(),wrongRef),base,a);
        var different=copy(base,base.commandHistory(),base.successionLifecycle(),new DriverStateSnapshot.NullValue());
        rejects(f,different,a);
        var changedTransport=new NativeObservationPort.TransportSession("other-machine",a.session().game(),
                a.session().connectionGeneration(),a.session().sessionId());
        rejects(f,base,changed(f,changedTransport,a.snapshotId(),a.nativeRevision(),a.state(),a.originalPacket(),a.observedAt()));
        var changedGame=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740994")));
        var changedBirth=new NativeObservationPort.TransportSession(a.session().machineId(),changedGame,
                a.session().connectionGeneration(),a.session().sessionId());
        rejects(f,base,changed(f,changedBirth,a.snapshotId(),a.nativeRevision(),a.state(),a.originalPacket(),a.observedAt()));
        byte[] tampered=a.originalPacket();tampered[tampered.length-2]^=1;
        rejects(f,base,changed(f,a.session(),a.snapshotId(),a.nativeRevision(),a.state(),tampered,a.observedAt()));
        rejects(f,base,changed(f,a.session(),a.snapshotId(),a.nativeRevision(),new RawJson(bytes(STATE.replace("\"speed\":3","\"speed\":4"))),a.originalPacket(),a.observedAt()));
        rejects(f,base,changed(f,a.session(),"another-snapshot",a.nativeRevision(),a.state(),a.originalPacket(),a.observedAt()));
        rejects(f,base,changed(f,a.session(),a.snapshotId(),a.nativeRevision().add(BigInteger.ONE),a.state(),a.originalPacket(),a.observedAt()));
        rejects(f,base,changed(f,a.session(),a.snapshotId(),a.nativeRevision(),a.state(),a.originalPacket(),a.observedAt().plusSeconds(1)));
        var row=DriverJson.object(f.manifest().bytes(),DriverJson.MAX_NATIVE_BYTES);
        var otherSource=OpportunityJson.object(row.get("source"),"source").with("machine_id",new OpportunityJson.Text("other-machine"));
        rejects(manifest(f,row.with("source",otherSource)),base,a);

        var tooManyDigits=copy(base,base.commandHistory(),base.successionLifecycle(),
                new DriverStateSnapshot.Value(bytes("{\"n\":"+"1".repeat(4301)+"}")));
        var huge=fixture(tooManyDigits);
        rejects(huge,tooManyDigits,huge.actual());
        // The arbitrary existing full-material API retains its wider numeric lane.
        var materialFacts=DriverObservationEvidenceReader.decode(huge.manifestRef(),huge.manifest(),
                RawJson.fullMaterial(tooManyDigits.encode()),huge.actual());
        assertArrayEquals(tooManyDigits.encode(),materialFacts.driver().encode());

        var deepValue=new DriverStateSnapshot.Value(bytes("[".repeat(64)+"0"+"]".repeat(64)));
        var deep=copy(base,base.commandHistory(),base.successionLifecycle(),deepValue);
        rejects(f,deep,a); // Complete.encode retains the whole-tree64 limit before either API path.

        byte[] pretty=bytes(" \n"+new String(base.encode(),StandardCharsets.UTF_8)+" \n");
        var noncanonical=manifest(f,row.with("driver_ref",DriverObservationEvidenceReader.reference(ref(pretty))));
        var old=DriverObservationEvidenceReader.decode(noncanonical.manifestRef(),noncanonical.manifest(),new RawJson(pretty),a);
        assertArrayEquals(base.encode(),old.driver().encode());
        // Both typed-expression paths correctly use canonical typed bytes and reject this different exact reference.
        rejects(noncanonical,base,a);
    }
}
