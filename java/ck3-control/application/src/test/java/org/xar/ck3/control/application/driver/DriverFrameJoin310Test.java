package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

public class DriverFrameJoin310Test {
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

    private static byte[] bytes(String text) { return text.getBytes(java.nio.charset.StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] raw) { return new ExactRef("memory/test-original.json", raw.length, DriverJson.sha256(raw)); }
    private static GameGeneration game() { return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    private static Known known() { return DriverFactsRepository.imported(ref(bytes(WIRE)), bytes(WIRE), 3, 7, game(), new OpportunityJson.Obj(Map.of())); }
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

    private record Fixture(NativeObservationPort.ObservedFrame actual, RawJson manifest, ExactRef manifestRef,
            RawJson driver, ExactRef driverRef, byte[] packet, ExactRef nativeRef) {
        NativeEffectEvidence.FrameBasis basis() { return new NativeEffectEvidence.FrameBasis(nativeRef, manifestRef); }
    }
    private static Fixture fixture(String state) {
        var k=known();var actual=actual(state);var driver=new RawJson(k.driver().encode());var driverRef=ref(driver.bytes());
        var manifest=DriverObservationEvidenceReader.encode(k,actual,BigInteger.valueOf(2),1,source(),
                new OpportunityJson.Obj(Map.of()),driverRef);
        var packet=actual.originalPacket();return new Fixture(actual,manifest,ref(manifest.bytes()),driver,driverRef,packet,ref(packet));
    }
    private static final class Originals implements InvocationHandler {
        private final Fixture f;
        private final ExactRef manifestRequested,nativeRequested;
        private final RawJson returnedDriver;
        private final UncheckedIOException lateFailure;
        private final List<ExactRef> reads=new ArrayList<>();
        private boolean mutateNativeOnDriver;
        Originals(Fixture f) { this(f,f.manifestRef(),f.nativeRef(),f.driver(),null); }
        Originals(Fixture f,ExactRef manifestRequested,ExactRef nativeRequested,RawJson returnedDriver,UncheckedIOException lateFailure) {
            this.f=f;this.manifestRequested=manifestRequested;this.nativeRequested=nativeRequested;
            this.returnedDriver=returnedDriver;this.lateFailure=lateFailure;
        }
        OutcomeArchive archive() {
            return (OutcomeArchive)Proxy.newProxyInstance(OutcomeArchive.class.getClassLoader(),
                    new Class<?>[]{OutcomeArchive.class},this);
        }
        @Override public Object invoke(Object proxy,Method method,Object[] args) {
            assertNotNull(args);assertEquals(1,args.length);var requested=assertInstanceOf(ExactRef.class,args[0]);
            int position=reads.size()%3;reads.add(requested);
            if(position==0) { assertEquals("loadFullMaterial",method.getName());assertEquals(manifestRequested,requested);return f.manifest(); }
            if(position==1) { assertEquals("loadNativeFrame",method.getName());assertEquals(nativeRequested,requested);return f.packet(); }
            assertEquals("loadFullMaterial",method.getName());assertEquals(f.driverRef(),requested);
            if(mutateNativeOnDriver)f.packet()[0]^=1;
            if(lateFailure!=null)throw lateFailure;
            return returnedDriver;
        }
        void assertReads(int cycles) {
            var expected=new ArrayList<ExactRef>();
            for(int i=0;i<cycles;i++)expected.addAll(List.of(manifestRequested,nativeRequested,f.driverRef()));
            assertEquals(expected,reads);
        }
    }
    private static DriverObservationAssembler.FullSnapshot oldPublic(Fixture f,DriverObservationAssembler assembler) {
        var frame=DriverObservationEvidenceReader.nativeFrame(f.manifestRef(),f.manifest(),f.packet());
        var facts=DriverObservationEvidenceReader.decode(f.manifestRef(),f.manifest(),f.driver(),frame);
        return assembler.projectFull(frame,facts,f.nativeRef());
    }
    private static void sameFull(DriverObservationAssembler.FullSnapshot expected,DriverObservationAssembler.FullSnapshot actual) {
        assertEquals(expected.actual().session(),actual.actual().session());
        assertEquals(expected.actual().snapshotId(),actual.actual().snapshotId());
        assertEquals(expected.actual().nativeRevision(),actual.actual().nativeRevision());
        assertArrayEquals(expected.actual().state().bytes(),actual.actual().state().bytes());
        assertArrayEquals(expected.actual().originalPacket(),actual.actual().originalPacket());
        assertEquals(expected.actual().observedAt(),actual.actual().observedAt());
        assertEquals(expected.facts(),actual.facts());assertEquals(expected.semantic(),actual.semantic());
        assertArrayEquals(DriverJson.encode(expected.semantic()),DriverJson.encode(actual.semantic()));
        assertEquals(expected.originalEvidence(),actual.originalEvidence());assertEquals(expected.fullBindingSha256(),actual.fullBindingSha256());
    }
    @Test
    public void fullProjectionPreservesOriginalPlayerShapesAndReadsEveryOriginal() {
        String player="\"played_character\":{\"character_id\":73,\"alive\":true},";
        var states=List.of(STATE,STATE.replace(player,""),STATE.replace(player,"\"played_character\":null,"),
                STATE.replace("\"character_id\":73","\"character_id\":74"));
        for(int index=0;index<states.size();index++) {
            var f=fixture(states.get(index));var assembler=new DriverObservationAssembler();var loader=new DriverFrameEvidenceLoader(assembler);
            var originals=new Originals(f);var archive=originals.archive();var expected=oldPublic(f,assembler);
            var actual=loader.loadFull(f.basis(),archive);sameFull(expected,actual);originals.assertReads(1);
            var repeated=loader.loadFull(f.basis(),archive);sameFull(expected,repeated);originals.assertReads(2);
            assertEquals("1.00",assertInstanceOf(OpportunityJson.DecimalValue.class,actual.semantic().get("original_metric")).token());
            assertEquals(2,assertInstanceOf(OpportunityJson.Arr.class,actual.semantic().get("native_command_history")).items().size());
            assertEquals(f.manifestRef(),DriverObservationEvidenceReader.reference(actual.semantic().get("java_driver_facts_evidence")));
            assertEquals(new BigInteger("9007199254740993"),actual.actual().session().game().creationFiletime().value());
            if(index==1)assertFalse(actual.semantic().members().containsKey("played_character"));
            if(index==2)assertSame(OpportunityJson.Nil.INSTANCE,actual.semantic().get("played_character"));
            if(index==3)assertEquals(BigInteger.valueOf(74),OpportunityJson.integer(
                    assertInstanceOf(OpportunityJson.Obj.class,actual.semantic().get("played_character")).get("character_id"),"character_id"));
            var ordinary=new Originals(f);
            if(index==0)assertInstanceOf(DriverObservationAssembler.Complete.class,loader.load(f.basis(),ordinary.archive()));
            else assertThrows(IllegalArgumentException.class,()->loader.load(f.basis(),ordinary.archive()));
            ordinary.assertReads(1);
            var replay=DriverObservationEvidenceReader.replayOriginals(f.manifestRef(),f.manifest(),f.driver(),f.packet(),f.nativeRef());
            if(index==0)assertInstanceOf(DriverObservationAssembler.Complete.class,replay);
            else assertInstanceOf(DriverObservationAssembler.Incomplete.class,replay);
            byte[] capturedPacket=actual.actual().originalPacket(),capturedState=actual.actual().state().bytes(),semantic=DriverJson.encode(actual.semantic());
            f.packet()[0]^=1;
            assertArrayEquals(capturedPacket,actual.actual().originalPacket());assertArrayEquals(capturedState,actual.actual().state().bytes());
            assertArrayEquals(semantic,DriverJson.encode(actual.semantic()));
        }
        // The native original is borrowed by an archive; capture must precede its next callback.
        var alias=fixture(STATE);var assembler=new DriverObservationAssembler();var expected=oldPublic(alias,assembler);
        byte originalFirstByte=alias.packet()[0];
        var aliasOriginals=new Originals(alias);aliasOriginals.mutateNativeOnDriver=true;
        var captured=new DriverFrameEvidenceLoader(assembler).loadFull(alias.basis(),aliasOriginals.archive());
        assertNotEquals(originalFirstByte,alias.packet()[0]);
        sameFull(expected,captured);aliasOriginals.assertReads(1);
    }
    @Test
    public void exactArchiveGuardsAndLateReadFailureRemainObservable() {
        var f=fixture(STATE);var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var wrongManifest=new ExactRef(f.manifestRef().path(),f.manifestRef().bytes(),"0".repeat(64));
        var manifestOriginals=new Originals(f,wrongManifest,f.nativeRef(),f.driver(),null);
        assertThrows(IllegalArgumentException.class,()->loader.loadFull(new NativeEffectEvidence.FrameBasis(f.nativeRef(),wrongManifest),manifestOriginals.archive()));
        assertEquals(List.of(wrongManifest),manifestOriginals.reads);
        var wrongNative=new ExactRef(f.nativeRef().path(),f.nativeRef().bytes(),"0".repeat(64));
        var nativeOriginals=new Originals(f,f.manifestRef(),wrongNative,f.driver(),null);
        assertThrows(IllegalArgumentException.class,()->loader.loadFull(new NativeEffectEvidence.FrameBasis(wrongNative,f.manifestRef()),nativeOriginals.archive()));
        assertEquals(List.of(f.manifestRef(),wrongNative),nativeOriginals.reads);
        var changedDriver=new RawJson(bytes(new String(f.driver().bytes(),StandardCharsets.UTF_8).replace("campaign-original","changed-campaign")));
        var driverOriginals=new Originals(f,f.manifestRef(),f.nativeRef(),changedDriver,null);
        assertThrows(IllegalArgumentException.class,()->loader.loadFull(f.basis(),driverOriginals.archive()));driverOriginals.assertReads(1);
        var marker=new IOException("owned late original read failure");var failure=new UncheckedIOException(marker);
        var lateOriginals=new Originals(f,f.manifestRef(),f.nativeRef(),f.driver(),failure);
        assertSame(failure,assertThrows(UncheckedIOException.class,()->loader.loadFull(f.basis(),lateOriginals.archive())));
        assertSame(marker,failure.getCause());lateOriginals.assertReads(1);
    }
}
