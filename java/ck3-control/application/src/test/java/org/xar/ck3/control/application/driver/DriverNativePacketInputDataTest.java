package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Incomplete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure same-call input regression; no private carrier constructor, owner, Session, Native or file operation. */
final class DriverNativePacketInputDataTest {
    private static final String WIRE = """
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;

    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained"},"original_metric":1.00}
        """;

    private static byte[] bytes(String text) {
        return text.getBytes(java.nio.charset.StandardCharsets.UTF_8);
    }

    private static ExactRef ref(byte[] raw) {
        return new ExactRef("memory/test-original.json", raw.length, DriverJson.sha256(raw));
    }

    private static GameGeneration game() {
        return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    }

    private static Known known() {
        return DriverFactsRepository.imported(ref(bytes(WIRE)), bytes(WIRE), 3, 7, game(), new OpportunityJson.Obj(Map.of()));
    }

    private static G2Source source() {
        return new G2Source("test-machine", "2026-10-23T16:00:00Z", "test-source", ref(bytes("original-source")));
    }

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

    private static DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual) {
        var k = known();
        return new DriverObservationFacts(k.driver(), 3, 7, actual.session(), actual.snapshotId(), actual.nativeRevision(),
                DriverJson.sha256(actual.state().bytes()), BigInteger.valueOf(2), 1, source(),
                new OpportunityJson.Obj(Map.of()), ref(bytes("actual-facts")));
    }



    @Test void packetMetadataFailuresPrecedeStateTokenAndKeepCallbacks() {
        String noState = "{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9}";
        packetFailure(p -> p.setPacket(noState.replace("state_snapshot", "wrong_type")),
                ContractViolationException.class, "archived native envelope differs from semantic manifest", List.of("driver", "decoder"));
        packetFailure(p -> p.setPacket(noState.replace("snapshot-9", "other-snapshot")),
                ContractViolationException.class, "archived native envelope differs from semantic manifest", List.of("driver", "decoder"));
        packetFailure(p -> p.setPacket(noState.replace("\"revision\":9", "\"revision\":10")),
                ContractViolationException.class, "archived native envelope differs from semantic manifest", List.of("driver", "decoder"));
        packetFailure(p -> p.setPacket(noState.replace("\"protocol_version\":1", "\"protocol_version\":2")),
                ContractViolationException.class, "archived native envelope differs from semantic manifest", List.of("driver", "decoder"));
        packetFailure(p -> p.setPacket(noState), IllegalArgumentException.class,
                "original native state token absent", List.of("driver", "decoder"));
        packetFailure(p -> p.changeManifest("native_state_sha256", new OpportunityJson.Text("0".repeat(64))),
                ContractViolationException.class, "original native state token differs from manifest", List.of("driver", "decoder"));
        packetFailure(p -> p.packet[0] ^= 1, ContractViolationException.class,
                "archived native framing/manifest differs", List.of("driver", "decoder"));
        packetFailure(p -> p.manifestRef = wrongDigest(p.manifestRef), ContractViolationException.class,
                "semantic facts manifest exact bytes/SHA differ", List.of());
    }

    @Test
    public void packetInputsKeepLexicalDataAndStrictFallback() {
        var actual = actual(STATE);
        var k = known();
        var driverBytes = k.driver().encode();
        var driverRef = ref(driverBytes);
        var manifest = DriverObservationEvidenceReader.encode(k, actual, BigInteger.valueOf(2), 1, source(), new OpportunityJson.Obj(Map.of()), driverRef);
        var manifestRef = ref(manifest.bytes());
        var fullDriver = RawJson.fullMaterial(driverBytes);
        var framedNative = actual.originalPacket();
        byte[] packetBefore=framedNative.clone(),driverBefore=fullDriver.bytes(),manifestBefore=manifest.bytes();
        var nativeRef = ref(framedNative);

        // Test with original_metric 1.00 (from STATE)
        var oldFrame = DriverObservationEvidenceReader.nativeFrame(manifestRef, manifest, framedNative);
        var oldFacts = DriverObservationEvidenceReader.decode(manifestRef, manifest, fullDriver, oldFrame);
        List<String> oldEvents=new ArrayList<>();
        var oldResult=legacy(manifestRef,manifest,fullDriver,framedNative,nativeRef,oldEvents);
        assertEquals(List.of("driver","decoder"),oldEvents);
        assertInstanceOf(Complete.class, oldResult);
        var oldComplete = (Complete) oldResult;
        // Null input is the real complete legacy packet path, not a forged parsed carrier.
        var nullInput=new DriverObservationAssembler().assembleWithNativePacket(oldFrame,oldFacts,nativeRef,null);
        assertEquals(oldComplete,assertInstanceOf(Complete.class,nullInput));

        // New path with replayCapturedOriginals and null decoder (strict fallback)
        List<String> fastEvents=new ArrayList<>();
        var newResult = DriverObservationEvidenceReader.replayCapturedOriginals(
            manifestRef, manifest, framedNative, nativeRef,
            requested -> { assertEquals(driverRef,requested);fastEvents.add("driver");return fullDriver; },
            () -> { fastEvents.add("decoder");return null; }
        );
        assertInstanceOf(Complete.class, newResult);
        assertEquals(List.of("driver","decoder"),fastEvents);
        var newComplete = (Complete) newResult;

        // Compare fields
        assertEquals(oldComplete.identity(), newComplete.identity());
        assertEquals(oldComplete.source(), newComplete.source());
        assertEquals(oldComplete.sessionId(), newComplete.sessionId());
        assertEquals(oldComplete.connectionGeneration(), newComplete.connectionGeneration());
        assertEquals(oldComplete.semantic(), newComplete.semantic());
        assertArrayEquals(DriverJson.encode(oldComplete.semantic()),DriverJson.encode(newComplete.semantic()));
        assertEquals(oldComplete.originalEvidence(), newComplete.originalEvidence());
        assertEquals(oldComplete.observedAt(), newComplete.observedAt());
        assertEquals(oldComplete.fullBindingSha256(), newComplete.fullBindingSha256());
        assertEquals(oldComplete.originalProjection(), newComplete.originalProjection());

        // Verify lexical preservation of 1.00 in semantic
        var semantic = newComplete.semantic();
        var originalMetric = semantic.get("original_metric");
        assertInstanceOf(OpportunityJson.DecimalValue.class, originalMetric);
        assertEquals("1.00", ((OpportunityJson.DecimalValue) originalMetric).token());

        // Verify command history preservation
        var history = semantic.get("native_command_history");
        assertInstanceOf(OpportunityJson.Arr.class, history);
        assertEquals(2, ((OpportunityJson.Arr) history).items().size());

        // Verify manifest-ref semantic binding
        var manifestRefInSemantic = semantic.get("java_driver_facts_evidence");
        assertInstanceOf(OpportunityJson.Obj.class, manifestRefInSemantic);
        assertEquals(manifestRef, DriverObservationEvidenceReader.reference((OpportunityJson.Obj) manifestRefInSemantic));

        // Verify large creation FILETIME
        assertEquals(new BigInteger("9007199254740993"), newComplete.identity().game().creationFiletime().value());

        // Test with different packet body (2.5000E-2)
        var state2 = STATE.replace("1.00", "2.5000E-2");
        var actual2 = actual(state2);
        var manifest2 = DriverObservationEvidenceReader.encode(k, actual2, BigInteger.valueOf(2), 1, source(), new OpportunityJson.Obj(Map.of()), driverRef);
        var manifestRef2 = ref(manifest2.bytes());
        var framedNative2 = actual2.originalPacket();
        var nativeRef2 = ref(framedNative2);

        var oldFrame2 = DriverObservationEvidenceReader.nativeFrame(manifestRef2, manifest2, framedNative2);
        var oldFacts2 = DriverObservationEvidenceReader.decode(manifestRef2, manifest2, fullDriver, oldFrame2);
        List<String> oldEvents2=new ArrayList<>();
        var oldResult2=legacy(manifestRef2,manifest2,fullDriver,framedNative2,nativeRef2,oldEvents2);
        assertEquals(List.of("driver","decoder"),oldEvents2);
        assertInstanceOf(Complete.class, oldResult2);
        var oldComplete2 = (Complete) oldResult2;

        List<String> fastEvents2=new ArrayList<>();
        var newResult2 = DriverObservationEvidenceReader.replayCapturedOriginals(
            manifestRef2, manifest2, framedNative2, nativeRef2,
            requested -> { assertEquals(driverRef,requested);fastEvents2.add("driver");return fullDriver; },
            () -> { fastEvents2.add("decoder");return null; }
        );
        assertInstanceOf(Complete.class, newResult2);
        assertEquals(List.of("driver","decoder"),fastEvents2);
        var newComplete2 = (Complete) newResult2;

        assertEquals(oldComplete2.identity(), newComplete2.identity());
        assertEquals(oldComplete2.source(), newComplete2.source());
        assertEquals(oldComplete2.sessionId(), newComplete2.sessionId());
        assertEquals(oldComplete2.connectionGeneration(), newComplete2.connectionGeneration());
        assertEquals(oldComplete2.semantic(), newComplete2.semantic());
        assertArrayEquals(DriverJson.encode(oldComplete2.semantic()),DriverJson.encode(newComplete2.semantic()));
        assertEquals(oldComplete2.originalEvidence(), newComplete2.originalEvidence());
        assertEquals(oldComplete2.observedAt(), newComplete2.observedAt());
        assertEquals(oldComplete2.fullBindingSha256(), newComplete2.fullBindingSha256());
        assertEquals(oldComplete2.originalProjection(), newComplete2.originalProjection());

        // Verify lexical preservation of 2.5000E-2
        var semantic2 = newComplete2.semantic();
        var originalMetric2 = semantic2.get("original_metric");
        assertInstanceOf(OpportunityJson.DecimalValue.class, originalMetric2);
        assertEquals("2.5000E-2", ((OpportunityJson.DecimalValue) originalMetric2).token());

        // Test with opaque integer
        var state3 = STATE.replace("1.00", "184467440737095516170000");
        var actual3 = actual(state3);
        var manifest3 = DriverObservationEvidenceReader.encode(k, actual3, BigInteger.valueOf(2), 1, source(), new OpportunityJson.Obj(Map.of()), driverRef);
        var manifestRef3 = ref(manifest3.bytes());
        var framedNative3 = actual3.originalPacket();
        var nativeRef3 = ref(framedNative3);

        var oldFrame3 = DriverObservationEvidenceReader.nativeFrame(manifestRef3, manifest3, framedNative3);
        var oldFacts3 = DriverObservationEvidenceReader.decode(manifestRef3, manifest3, fullDriver, oldFrame3);
        List<String> oldEvents3=new ArrayList<>();
        var oldResult3=legacy(manifestRef3,manifest3,fullDriver,framedNative3,nativeRef3,oldEvents3);
        assertEquals(List.of("driver","decoder"),oldEvents3);
        assertInstanceOf(Complete.class, oldResult3);
        var oldComplete3 = (Complete) oldResult3;

        List<String> fastEvents3=new ArrayList<>();
        var newResult3 = DriverObservationEvidenceReader.replayCapturedOriginals(
            manifestRef3, manifest3, framedNative3, nativeRef3,
            requested -> { assertEquals(driverRef,requested);fastEvents3.add("driver");return fullDriver; },
            () -> { fastEvents3.add("decoder");return null; }
        );
        assertInstanceOf(Complete.class, newResult3);
        assertEquals(List.of("driver","decoder"),fastEvents3);
        var newComplete3 = (Complete) newResult3;

        assertEquals(oldComplete3.identity(), newComplete3.identity());
        assertEquals(oldComplete3.source(), newComplete3.source());
        assertEquals(oldComplete3.sessionId(), newComplete3.sessionId());
        assertEquals(oldComplete3.connectionGeneration(), newComplete3.connectionGeneration());
        assertEquals(oldComplete3.semantic(), newComplete3.semantic());
        assertArrayEquals(DriverJson.encode(oldComplete3.semantic()),DriverJson.encode(newComplete3.semantic()));
        assertEquals(oldComplete3.originalEvidence(), newComplete3.originalEvidence());
        assertEquals(oldComplete3.observedAt(), newComplete3.observedAt());
        assertEquals(oldComplete3.fullBindingSha256(), newComplete3.fullBindingSha256());
        assertEquals(oldComplete3.originalProjection(), newComplete3.originalProjection());

        // Verify opaque integer preservation
        var semantic3 = newComplete3.semantic();
        var originalMetric3 = semantic3.get("original_metric");
        assertInstanceOf(OpportunityJson.IntegerValue.class, originalMetric3);
        assertEquals(new BigInteger("184467440737095516170000"), ((OpportunityJson.IntegerValue) originalMetric3).value());

        assertArrayEquals(packetBefore,framedNative);
        assertArrayEquals(driverBefore,fullDriver.bytes());
        assertArrayEquals(manifestBefore,manifest.bytes());
        // Test mutation after result
        var semanticBeforeMutation = DriverJson.encode(newComplete.semantic());
        framedNative[0] ^= 1;
        assertEquals(oldComplete, newComplete);
        assertArrayEquals(semanticBeforeMutation, DriverJson.encode(newComplete.semantic()));
        assertEquals(nativeRef, newComplete.originalEvidence());

        // Independent fresh arrays for the before-capture mutation, compared with the real old sequence.
        packetFailure(p -> p.mutateInDriver=true,ContractViolationException.class,
                "archived native framing/manifest differs",List.of("driver","decoder"));
    }

    private static DriverObservationAssembler.Result legacy(ExactRef manifestRef,RawJson manifest,RawJson driver,
            byte[] packet,ExactRef evidence,List<String> events) {
        ExactRef requested=DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest);
        assertEquals(ref(driver.bytes()),requested);
        events.add("driver");
        return DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(manifestRef,manifest,driver,packet,evidence,
                decoder(events));
    }
    private static org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader decoder(List<String> events) {
        events.add("decoder");return null;
    }
    private static void packetFailure(Consumer<PacketProbe> setup,Class<? extends Throwable> type,String message,List<String> events) {
        PacketProbe old=new PacketProbe(),fast=new PacketProbe();setup.accept(old);setup.accept(fast);
        Throwable expected=assertThrows(type,()->old.run(false));
        Throwable actual=assertThrows(type,()->fast.run(true));
        assertEquals(expected.getClass(),actual.getClass());
        assertEquals(message,expected.getMessage());assertEquals(message,actual.getMessage());
        assertEquals(events,old.events);assertEquals(events,fast.events);
    }
    private static ExactRef wrongDigest(ExactRef original) {
        return new ExactRef(original.path(),original.bytes(),(original.sha256().charAt(0)=='0'?"1":"0")+original.sha256().substring(1));
    }
    private static byte[] framedEnvelope(String json) {
        byte[] body=bytes(json);
        return ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
    }
    private static final class PacketProbe {
        final Known owner=known();
        final RawJson driver=RawJson.fullMaterial(owner.driver().encode());
        final ExactRef driverRef=ref(driver.bytes());
        final NativeObservationPort.ObservedFrame observed=actual(STATE);
        RawJson manifest=DriverObservationEvidenceReader.encode(owner,observed,BigInteger.valueOf(2),1,source(),new OpportunityJson.Obj(Map.of()),driverRef);
        ExactRef manifestRef=ref(manifest.bytes()),evidence=ref(observed.originalPacket());
        byte[] packet=observed.originalPacket().clone();
        final List<String> events=new ArrayList<>();
        boolean mutateInDriver;
        RawJson material(ExactRef requested) {
            assertEquals(driverRef,requested);events.add("driver");
            if(mutateInDriver)packet[0]^=1;
            return driver;
        }
        org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader decoder() {events.add("decoder");return null;}
        DriverObservationAssembler.Result run(boolean captured) {
            ExactRef capturedRef=manifestRef;RawJson capturedManifest=manifest;
            if(captured)return DriverObservationEvidenceReader.replayCapturedOriginals(capturedRef,capturedManifest,packet,evidence,this::material,this::decoder);
            RawJson original=material(DriverObservationEvidenceReader.currentDriverReference(capturedRef,capturedManifest));
            return DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(capturedRef,capturedManifest,original,packet,evidence,decoder());
        }
        void setPacket(String outerJson) {
            packet=framedEnvelope(outerJson);evidence=ref(packet);
            changeManifest("native_packet_bytes",new OpportunityJson.IntegerValue(BigInteger.valueOf(packet.length)));
            changeManifest("native_packet_sha256",new OpportunityJson.Text(DriverJson.sha256(packet)));
        }
        void changeManifest(String field,OpportunityJson.Value value) {
            manifest=RawJson.fullMaterial(DriverJson.encode(DriverJson.object(manifest.bytes(),DriverJson.MAX_NATIVE_BYTES).with(field,value)));
            manifestRef=ref(manifest.bytes());
        }
    }
}
