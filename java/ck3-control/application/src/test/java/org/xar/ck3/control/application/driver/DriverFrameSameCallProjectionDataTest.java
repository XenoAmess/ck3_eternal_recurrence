package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameBasis;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Strict material replay DATA only: no writer Session, Native operation, live token or permission. */
final class DriverFrameSameCallProjectionDataTest {
    // Exact final NativeEventEvidenceProducerTest33 STATE, including its strip/date/diagnostics contract.
    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true,"stress_points":10},
         "active_event":{"instance_id":17,"option_count":3},"pending_character_interaction":null,
         "one_life_terminal_reason":null,"active_wars":[],"player_armies":[],"diagnostics":{"bridge_pid":42,"connection_generation":5}}
        """.strip();

    @Test void loaderAndRawNominalEntryMatchPublicFullAndAssembleForProfilesOneAndFour() {
        for (int profile : new int[] {1, 4}) {
            var original = originals(profile, STATE.replace("\"speed\":3", "\"speed\":3,\"original_metric\":1.00"));
            byte[] originalPacket = original.packet().clone();
            byte[] originalManifest = original.manifest().bytes();
            byte[] originalDriver = original.driver().bytes();
            var assembler = new DriverObservationAssembler();
            for (boolean scoped : new boolean[] {false, true}) {
                var loader = new DriverFrameEvidenceLoader(assembler, scoped);
                var fullReads = new ArrayList<String>();
                var full = loader.loadFull(original.basis(), materialArchive(original, fullReads, null, null, null));
                assertEquals(List.of("manifest", "native", "driver"), fullReads);
                var expected = assertInstanceOf(DriverObservationAssembler.Complete.class,
                        assembler.assemble(full.actual(), full.facts(), full.originalEvidence()));

                var loadReads = new ArrayList<String>();
                var actual = loader.load(original.basis(), materialArchive(original, loadReads, null, null, null));
                assertEquals(List.of("manifest", "native", "driver"), loadReads);
                assertCompleteData(expected, actual);
                if (actual.originalProjection().isPresent()) assertFullData(full, actual.originalProjection().orElseThrow());

                var nominal = assertInstanceOf(DriverObservationAssembler.Complete.class,
                        DriverObservationEvidenceReader.assembleValidatedOriginalsWithScopedDriverDecode(
                                original.manifestRef(), original.manifest(), original.driver(), original.packet(),
                                original.nativeRef(), assembler, scoped ? loader : null));
                assertCompleteData(expected, nominal);
                assertEquals(profile == 4, actual.originalProjection().isPresent());
                assertEquals(BigInteger.valueOf(73), actual.identity().frame().identity().player());
                assertEquals(BigInteger.valueOf(53144328), actual.identity().frame().identity().dateRaw());
                assertEquals(BigInteger.valueOf(2), actual.identity().frame().revision());
                assertEquals(BigInteger.valueOf(9), actual.identity().frame().identity().nativeRevision());
                assertEquals(new OpportunityJson.DecimalValue("1.00"), actual.semantic().get("original_metric"));
                assertEquals(new OpportunityJson.Text("same-call-original"), actual.semantic().get("retained_semantic_marker"));
                assertEquals(2, OpportunityJson.array(actual.semantic().get("native_command_history"), "history").size());
                assertEquals(original.manifestRef(), DriverObservationEvidenceReader.reference(actual.semantic().get("java_driver_facts_evidence")));
                assertEquals(new BigInteger("9007199254740993"), actual.identity().game().creationFiletime().value());
            }
            assertArrayEquals(originalPacket, original.packet());
            assertArrayEquals(originalManifest, original.manifest().bytes());
            assertArrayEquals(originalDriver, original.driver().bytes());
        }
    }

    @Test void publicForgedFullCannotBorrowNominalSuccessAndFailedJoinDoesNotPoisonNextLoad() {
        var assembler = new DriverObservationAssembler();
        var loader = new DriverFrameEvidenceLoader(assembler, true);
        var legal = originals(4, STATE);
        var actual = loader.load(legal.basis(), materialArchive(legal, new ArrayList<>(), null, null, null));
        rejectForgedFull(actual);

        // The full projection can represent an unreconciled actor, but ordinary Complete cannot.
        var mismatch = originals(1, STATE.replace("\"character_id\":73", "\"character_id\":74"));
        var originalFull = loader.loadFull(mismatch.basis(), materialArchive(mismatch, new ArrayList<>(), null, null, null));
        var oldResult = assertInstanceOf(DriverObservationAssembler.Incomplete.class,
                assembler.assemble(originalFull.actual(), originalFull.facts(), originalFull.originalEvidence()));
        var nominal = assertInstanceOf(DriverObservationAssembler.Incomplete.class,
                DriverObservationEvidenceReader.assembleValidatedOriginalsWithScopedDriverDecode(
                        mismatch.manifestRef(), mismatch.manifest(), mismatch.driver(), mismatch.packet(),
                        mismatch.nativeRef(), assembler, loader));
        assertEquals(oldResult.reasons(), nominal.reasons());
        assertEquals(List.of("native_driver_fact_join: unreconciled played-character/episode transition"), nominal.reasons());
        assertThrows(IllegalArgumentException.class,
                () -> loader.load(mismatch.basis(), materialArchive(mismatch, new ArrayList<>(), null, null, null)));

        // Use the same Loader and thread after the failed join; no private state or diagnostic count is inspected.
        var recovered = loader.load(legal.basis(), materialArchive(legal, new ArrayList<>(), null, null, null));
        assertCompleteData(actual, recovered);
        rejectForgedFull(recovered);
    }

    @Test void archiveOriginalOrderFailuresAndCallerBufferOwnershipRemainObservable() {
        var original = originals(4, STATE);
        var loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        var baseline = loader.load(original.basis(), materialArchive(original, new ArrayList<>(), null, null, null));
        for (String stage : List.of("manifest", "native", "driver")) {
            var events = new ArrayList<String>();
            var sentinel = new IllegalStateException("original archive " + stage + " sentinel");
            assertSame(sentinel, assertThrows(IllegalStateException.class,
                    () -> loader.load(original.basis(), materialArchive(original, events, stage, sentinel, null))));
            assertEquals(stage.equals("manifest") ? List.of("manifest")
                    : stage.equals("native") ? List.of("manifest", "native")
                    : List.of("manifest", "native", "driver"), events);
            assertCompleteData(baseline,
                    loader.load(original.basis(), materialArchive(original, new ArrayList<>(), null, null, null)));
        }

        var badManifestReads = new ArrayList<String>();
        var differentManifest = new ExactRef(original.manifestRef().path(), original.manifestRef().bytes(), "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> loader.load(
                new FrameBasis(original.nativeRef(), differentManifest),
                materialArchive(original, badManifestReads, null, null, null)));
        assertEquals(List.of("manifest"), badManifestReads);

        var badNativeReads = new ArrayList<String>();
        byte[] changedPacket = original.packet().clone();
        changedPacket[0] ^= 1;
        assertThrows(IllegalArgumentException.class,
                () -> loader.load(original.basis(), materialArchive(original, badNativeReads, null, null, changedPacket)));
        assertEquals(List.of("manifest", "native"), badNativeReads);
        assertCompleteData(baseline,
                loader.load(original.basis(), materialArchive(original, new ArrayList<>(), null, null, null)));

        // The archive may own its returned buffer. The Loader must retain its original private copy
        // before the later Driver callback changes the caller-visible array.
        var ownership = originals(4, STATE);
        byte[] expectedPacket = ownership.packet().clone();
        var ownershipReads = new ArrayList<String>();
        OutcomeArchive mutatingDriverRead = (OutcomeArchive) Proxy.newProxyInstance(OutcomeArchive.class.getClassLoader(),
                new Class<?>[] {OutcomeArchive.class}, (proxy, method, arguments) -> {
                    ExactRef requested = (ExactRef) arguments[0];
                    if (method.getName().equals("loadFullMaterial")) {
                        if (requested.equals(ownership.manifestRef())) { ownershipReads.add("manifest"); return ownership.manifest(); }
                        assertEquals(ownership.driverRef(), requested);
                        ownershipReads.add("driver"); ownership.packet()[0] ^= 1; return ownership.driver();
                    }
                    assertEquals("loadNativeFrame", method.getName());
                    assertEquals(ownership.nativeRef(), requested);
                    ownershipReads.add("native"); return ownership.packet();
                });
        var captured = loader.load(ownership.basis(), mutatingDriverRead);
        assertEquals(List.of("manifest", "native", "driver"), ownershipReads);
        assertEquals(ownership.nativeRef(), captured.originalEvidence());
        assertArrayEquals(expectedPacket, captured.originalProjection().orElseThrow().actual().originalPacket());
        assertNotEquals(expectedPacket[0], ownership.packet()[0]);
        rejectForgedFull(captured);
    }

    private static void rejectForgedFull(DriverObservationAssembler.Complete actual) {
        var full = actual.originalProjection().orElseThrow();
        var forgedSemantic = full.semantic().with("public_forgery", new OpportunityJson.Bool(true));
        String forgedDigest = DriverObservationAssembler.bindingSha256(forgedSemantic);
        var forged = new DriverObservationAssembler.FullSnapshot(full.actual(), full.facts(), forgedSemantic,
                full.originalEvidence(), forgedDigest);
        var failure = assertThrows(IllegalArgumentException.class, () -> new DriverObservationAssembler.Complete(
                actual.identity(), actual.source(), actual.sessionId(), actual.connectionGeneration(), forgedSemantic,
                actual.originalEvidence(), actual.observedAt(), forgedDigest, Optional.of(forged)));
        assertEquals("native campaign complete DATA crossed its actual full projection", failure.getMessage());
    }

    private static void assertCompleteData(DriverObservationAssembler.Complete expected, DriverObservationAssembler.Complete actual) {
        assertEquals(expected.identity(), actual.identity());
        assertEquals(expected.source(), actual.source());
        assertEquals(expected.sessionId(), actual.sessionId());
        assertEquals(expected.connectionGeneration(), actual.connectionGeneration());
        assertEquals(expected.semantic(), actual.semantic());
        assertArrayEquals(DriverJson.encode(expected.semantic()), DriverJson.encode(actual.semantic()));
        assertEquals(expected.originalEvidence(), actual.originalEvidence());
        assertEquals(expected.observedAt(), actual.observedAt());
        assertEquals(expected.fullBindingSha256(), actual.fullBindingSha256());
        assertEquals(expected.originalProjection().isPresent(), actual.originalProjection().isPresent());
        if (expected.originalProjection().isPresent()) assertFullData(expected.originalProjection().orElseThrow(), actual.originalProjection().orElseThrow());
    }

    private static void assertFullData(DriverObservationAssembler.FullSnapshot expected, DriverObservationAssembler.FullSnapshot actual) {
        assertEquals(expected.semantic(), actual.semantic());
        assertArrayEquals(DriverJson.encode(expected.semantic()), DriverJson.encode(actual.semantic()));
        assertEquals(expected.originalEvidence(), actual.originalEvidence());
        assertEquals(expected.fullBindingSha256(), actual.fullBindingSha256());
        assertEquals(expected.actual().session(), actual.actual().session());
        assertEquals(expected.actual().snapshotId(), actual.actual().snapshotId());
        assertEquals(expected.actual().nativeRevision(), actual.actual().nativeRevision());
        assertEquals(expected.actual().observedAt(), actual.actual().observedAt());
        assertArrayEquals(expected.actual().originalPacket(), actual.actual().originalPacket());
        assertArrayEquals(expected.actual().state().bytes(), actual.actual().state().bytes());
        var ef = expected.facts(); var af = actual.facts();
        assertArrayEquals(ef.driver().encode(), af.driver().encode());
        assertEquals(ef.driverVersion(), af.driverVersion());
        assertEquals(ef.episodeEpoch(), af.episodeEpoch());
        assertEquals(ef.transport(), af.transport());
        assertEquals(ef.snapshotId(), af.snapshotId());
        assertEquals(ef.nativeRevision(), af.nativeRevision());
        assertEquals(ef.nativeStateSha256(), af.nativeStateSha256());
        assertEquals(ef.publicRevision(), af.publicRevision());
        assertEquals(ef.observationVersion(), af.observationVersion());
        assertEquals(ef.source(), af.source());
        assertEquals(ef.originalSemanticFields(), af.originalSemanticFields());
        assertEquals(ef.semanticFactsEvidence(), af.semanticFactsEvidence());
    }

    private record Originals(ObservedFrame actual, RawJson manifest, RawJson driver, byte[] packet,
            ExactRef manifestRef, ExactRef nativeRef, ExactRef driverRef) {
        FrameBasis basis() { return new FrameBasis(nativeRef, manifestRef); }
    }

    private static Originals originals(int profile, String suppliedState) {
        String wire = DriverStateAssemblerTest.WIRE;
        if (profile == 4) {
            String originalLifecycle = "\"succession_lifecycle\":{\"current\":{\"episode\":\"episode-real-1\"}}";
            assertTrue(wire.contains(originalLifecycle));
            wire = wire.replace(originalLifecycle, "\"succession_lifecycle\":null");
        }
        byte[] originalWire = DriverStateAssemblerTest.bytes(wire);
        var known = DriverFactsRepository.imported(DriverStateAssemblerTest.ref(originalWire), originalWire, 3, 7,
                DriverStateAssemblerTest.game(), new OpportunityJson.Obj(Map.of()));
        String state = suppliedState.strip();
        byte[] body = DriverStateAssemblerTest.bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var actual = new ObservedFrame(new TransportSession("test-machine", DriverStateAssemblerTest.game(), BigInteger.valueOf(5), "held-session"),
                "snapshot-9", BigInteger.valueOf(9), new RawJson(DriverStateAssemblerTest.bytes(state)), packet,
                Instant.parse("2026-10-23T16:00:09Z"));
        var extras = new OpportunityJson.Obj(profile == 4 ? Map.of(
                "retained_semantic_marker", new OpportunityJson.Text("same-call-original"),
                "episode_projection", new OpportunityJson.Text(NativeCampaignProjection.WIRE_MODE))
                : Map.of("retained_semantic_marker", new OpportunityJson.Text("same-call-original")));
        byte[] driverBytes = known.driver().encode();
        ExactRef driverRef = reference("driver", driverBytes);
        var driver = RawJson.fullMaterial(driverBytes);
        var manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.valueOf(2), profile,
                DriverStateAssemblerTest.source(), extras, driverRef);
        return new Originals(actual, manifest, driver, packet, reference("manifest", manifest.bytes()), reference("native", packet), driverRef);
    }

    private static ExactRef reference(String role, byte[] original) {
        return new ExactRef("memory/same-call-data/" + role, original.length, DriverJson.sha256(original));
    }

    /** Same three material reads as the real archive contract; no Session or issuer callback is supplied. */
    private static OutcomeArchive materialArchive(Originals original, List<String> events, String failAt,
            RuntimeException sentinel, byte[] nativeOverride) {
        return (OutcomeArchive) Proxy.newProxyInstance(OutcomeArchive.class.getClassLoader(),
                new Class<?>[] {OutcomeArchive.class}, (proxy, method, arguments) -> {
                    String stage;
                    Object value;
                    ExactRef requested = (ExactRef) arguments[0];
                    if (method.getName().equals("loadFullMaterial")) {
                        if (requested.path().equals(original.manifestRef().path())) {
                            stage = "manifest"; value = original.manifest();
                        } else {
                            assertEquals(original.driverRef(), requested);
                            stage = "driver"; value = original.driver();
                        }
                    } else if (method.getName().equals("loadNativeFrame")) {
                        assertEquals(original.nativeRef(), requested);
                        stage = "native"; value = nativeOverride == null ? original.packet() : nativeOverride;
                    } else throw new AssertionError("unexpected archive operation: " + method.getName());
                    events.add(stage);
                    if (stage.equals(failAt)) throw sentinel;
                    return value;
                });
    }
}
