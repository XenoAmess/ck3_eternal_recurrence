package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
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
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** DATA-only differential frontiers. No archive, writer, Session, Native or active cache is fabricated. */
final class DriverManifestOnceFrontierDataTest {
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



    @Test void acceptedOriginalsAndCallbackCountsStayExact() {
        for (boolean inactiveNominal : new boolean[] {false, true}) {
            Probe old = new Probe(), fast = new Probe();
            if (inactiveNominal) {
                old.decoder = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
                fast.decoder = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
            }
            byte[] oldPacket = old.packet.clone(), fastPacket = fast.packet.clone();
            byte[] driverBefore = fast.fixture.driver.bytes(), manifestBefore = fast.fixture.manifest.bytes();
            Complete expected = assertInstanceOf(Complete.class, old.run(false));
            Complete actual = assertInstanceOf(Complete.class, fast.run(true));
            assertEquals(List.of("driver", "decoder"), old.events);
            assertEquals(List.of("driver", "decoder"), fast.events);
            assertEquals(expected, actual);
            byte[] captured = DriverJson.encode(actual.semantic());
            assertArrayEquals(DriverJson.encode(expected.semantic()), captured);
            assertEquals("1.00", assertInstanceOf(OpportunityJson.DecimalValue.class,
                    actual.semantic().get("original_metric")).token());
            assertEquals(new BigInteger("9007199254740993"), actual.identity().game().creationFiletime().value());
            assertEquals(2, OpportunityJson.array(actual.semantic().get("native_command_history"), "history").size());
            assertEquals(fast.fixture.manifestRef,
                    DriverObservationEvidenceReader.reference(actual.semantic().get("java_driver_facts_evidence")));
            assertEquals(fast.fixture.nativeRef, actual.originalEvidence());
            assertArrayEquals(oldPacket, old.packet); assertArrayEquals(fastPacket, fast.packet);
            assertArrayEquals(driverBefore, fast.fixture.driver.bytes());
            assertArrayEquals(manifestBefore, fast.fixture.manifest.bytes());
            // Mutate only the caller arrays after both accepted calls. Captured DATA must stay unchanged.
            old.packet[0] ^= 1; fast.packet[0] ^= 1;
            assertEquals(expected, actual);
            assertArrayEquals(captured, DriverJson.encode(actual.semantic()));
            assertArrayEquals(driverBefore, fast.fixture.driver.bytes());
            assertArrayEquals(manifestBefore, fast.fixture.manifest.bytes());
        }
    }

    @Test void originalFailuresKeepTheirCallbackFrontier() {
        failurePair(p -> p.manifestRef = wrongDigest(p.manifestRef), ContractViolationException.class,
                "semantic facts manifest exact bytes/SHA differ", List.of(), null);
        failurePair(p -> p.changeManifest("unexpected", new OpportunityJson.Bool(true), false),
                ContractViolationException.class, "exact semantic evidence manifest contract required", List.of(), null);
        failurePair(p -> p.changeManifest("schema", new OpportunityJson.Text("wrong-schema"), false),
                ContractViolationException.class, "exact semantic evidence manifest contract required", List.of(), null);
        failurePair(p -> p.changeManifest("driver_ref", new OpportunityJson.Bool(false), false),
                IllegalArgumentException.class, "exact reference must be an object", List.of(), null);
        var material = new IllegalStateException("driver material sentinel");
        failurePair(p -> { p.driverFailure = material; p.packet = new byte[0]; }, IllegalStateException.class,
                material.getMessage(), List.of("driver"), material);
        var getter = new IllegalStateException("decoder getter sentinel");
        failurePair(p -> { p.driver = null; p.decoderFailure = getter; p.packet = new byte[0]; },
                IllegalStateException.class, getter.getMessage(), List.of("driver", "decoder"), getter);
        failurePair(p -> { p.driver = null; p.packet = new byte[0]; }, NullPointerException.class,
                null, List.of("driver", "decoder"), null);
        failurePair(p -> { p.decoderFailure = getter; p.packet = new byte[0]; }, IllegalStateException.class,
                getter.getMessage(), List.of("driver", "decoder"), getter);
    }

    @Test void changedOriginalsAndTheClonePointMatchTheOldReplay() {
        failurePair(p -> p.driver = RawJson.fullMaterial(bytes(new String(p.fixture.driver.bytes(),
                        StandardCharsets.UTF_8).replace("campaign-original", "changed-campaign"))),
                ContractViolationException.class, "archived complete Driver exact bytes/SHA differ",
                List.of("driver", "decoder"), null);
        failurePair(p -> p.mutateInDriver = true, ContractViolationException.class,
                "archived native framing/manifest differs", List.of("driver", "decoder"), null);
        failurePair(p -> p.mutateInDecoder = true, ContractViolationException.class,
                "archived native framing/manifest differs", List.of("driver", "decoder"), null);
        Probe old = new Probe(), fast = new Probe();
        old.evidence = ref(bytes("wrong-native-evidence")); fast.evidence = ref(bytes("wrong-native-evidence"));
        Incomplete expected = assertInstanceOf(Incomplete.class, old.run(false));
        Incomplete actual = assertInstanceOf(Incomplete.class, fast.run(true));
        assertEquals(expected, actual);
        assertTrue(actual.reasons().get(0).contains("original native evidence differs"));
        assertEquals(List.of("driver", "decoder"), old.events);
        assertEquals(List.of("driver", "decoder"), fast.events);
        // A preceding accepted call cannot hide a new invalid manifest/body at the same ref.
        old = new Probe(); fast = new Probe();
        assertEquals(assertInstanceOf(Complete.class, old.run(false)), assertInstanceOf(Complete.class, fast.run(true)));
        old.events.clear(); fast.events.clear();
        old.changeManifest("unexpected", new OpportunityJson.Bool(true), true);
        fast.changeManifest("unexpected", new OpportunityJson.Bool(true), true);
        Probe finalOld = old, finalFast = fast;
        Throwable oldFailure = assertThrows(ContractViolationException.class, () -> finalOld.run(false));
        Throwable newFailure = assertThrows(ContractViolationException.class, () -> finalFast.run(true));
        assertEquals("semantic facts manifest exact bytes/SHA differ", oldFailure.getMessage());
        assertEquals(oldFailure.getClass(), newFailure.getClass());
        assertEquals(oldFailure.getMessage(), newFailure.getMessage());
        assertTrue(old.events.isEmpty()); assertTrue(fast.events.isEmpty());
    }

    private static void failurePair(Consumer<Probe> setup, Class<? extends Throwable> type,
            String message, List<String> events, Throwable same) {
        Probe old = new Probe(), fast = new Probe(); setup.accept(old); setup.accept(fast);
        Throwable expected = assertThrows(type, () -> old.run(false));
        Throwable actual = assertThrows(type, () -> fast.run(true));
        assertEquals(expected.getClass(), actual.getClass());
        assertEquals(message, expected.getMessage()); assertEquals(message, actual.getMessage());
        if (same != null) { assertSame(same, expected); assertSame(same, actual); }
        assertEquals(events, old.events); assertEquals(events, fast.events);
    }

    private static ExactRef wrongDigest(ExactRef ref) {
        String other = (ref.sha256().charAt(0) == '0' ? "1" : "0") + ref.sha256().substring(1);
        return new ExactRef(ref.path(), ref.bytes(), other);
    }

    private static final class Fixture {
        final Known owner = known();
        final RawJson driver = RawJson.fullMaterial(owner.driver().encode());
        final ExactRef driverRef = ref(driver.bytes());
        final NativeObservationPort.ObservedFrame observed = actual(STATE);
        final RawJson manifest = DriverObservationEvidenceReader.encode(owner, observed, BigInteger.valueOf(2), 1,
                source(), new OpportunityJson.Obj(Map.of()), driverRef);
        final ExactRef manifestRef = ref(manifest.bytes()), nativeRef = ref(observed.originalPacket());
    }

    private static final class Probe {
        final Fixture fixture = new Fixture();
        final List<String> events = new ArrayList<>();
        RawJson manifest = fixture.manifest, driver = fixture.driver;
        ExactRef manifestRef = fixture.manifestRef, evidence = fixture.nativeRef;
        byte[] packet = fixture.observed.originalPacket().clone();
        DriverFrameEvidenceLoader decoder;
        RuntimeException driverFailure, decoderFailure;
        boolean mutateInDriver, mutateInDecoder;

        RawJson readDriver(ExactRef requested) {
            assertEquals(fixture.driverRef, requested);
            events.add("driver");
            if (driverFailure != null) throw driverFailure;
            if (mutateInDriver) packet[0] ^= 1;
            return driver;
        }
        DriverFrameEvidenceLoader decoder() {
            events.add("decoder");
            if (decoderFailure != null) throw decoderFailure;
            if (mutateInDecoder) packet[0] ^= 1;
            return decoder;
        }
        DriverObservationAssembler.Result run(boolean captured) {
            if (captured) return DriverObservationEvidenceReader.replayCapturedOriginals(
                    manifestRef, manifest, packet, evidence, this::readDriver, this::decoder);
            // Literal original production sequence, not a copy of the parser or new method.
            RawJson original = readDriver(DriverObservationEvidenceReader.currentDriverReference(manifestRef, manifest));
            return DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(
                    manifestRef, manifest, original, packet, evidence, decoder());
        }
        void changeManifest(String field, OpportunityJson.Value value, boolean keepReference) {
            manifest = RawJson.fullMaterial(DriverJson.encode(DriverJson.object(manifest.bytes(), DriverJson.MAX_NATIVE_BYTES)
                    .with(field, value)));
            if (!keepReference) manifestRef = ref(manifest.bytes());
        }
    }
}
