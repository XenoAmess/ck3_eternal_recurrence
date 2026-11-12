package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameBasis;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real public/captured replay DATA only. No world/Session issuer, private token reflection or implementation counter. */
final class DriverPublicReplay52DataTest {
    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true,"stress_points":10},
         "active_event":{"instance_id":17,"option_count":3},"pending_character_interaction":null,
         "one_life_terminal_reason":null,"active_wars":[],"player_armies":[],"diagnostics":{"bridge_pid":42,"connection_generation":5}}
        """.strip();

    @Test void publicAndCapturedReplayRetainCompleteMetadataForBothOriginalProfiles() {
        for (int profile : new int[] {1, 4}) {
            var original = originals(profile, STATE.replace("\"speed\":3", "\"speed\":3,\"original_metric\":1.00"));
            byte[] packetBefore = original.packet().clone();
            byte[] driverBefore = original.driver().bytes();
            byte[] manifestBefore = original.manifest().bytes();
            var expected = ordinary(original);
            assertCompleteData(expected, complete(DriverObservationEvidenceReader.replayOriginals(
                    original.manifestRef(), original.manifest(), original.driver(), original.packet(), original.nativeRef())));
            for (DriverFrameEvidenceLoader decoder : new DriverFrameEvidenceLoader[] {
                    null, new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true)}) {
                assertCompleteData(expected, complete(DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(
                        original.manifestRef(), original.manifest(), original.driver(), original.packet(), original.nativeRef(), decoder)));
                var events = new ArrayList<String>();
                var captured = complete(DriverObservationEvidenceReader.replayCapturedOriginals(
                        original.manifestRef(), original.manifest(), original.packet(), original.nativeRef(),
                        requested -> { events.add("driver"); assertEquals(original.driverRef(), requested); return original.driver(); },
                        () -> { events.add("decoder"); return decoder; }));
                assertEquals(List.of("driver", "decoder"), events);
                assertCompleteData(expected, captured);
                assertEquals(profile == 4, captured.originalProjection().isPresent());
                assertEquals(new OpportunityJson.DecimalValue("1.00"), captured.semantic().get("original_metric"));
                assertEquals(new OpportunityJson.Text("same-call-original"), captured.semantic().get("retained_semantic_marker"));
                assertEquals(2, OpportunityJson.array(captured.semantic().get("native_command_history"), "history").size());
                assertEquals(new BigInteger("9007199254740993"), captured.identity().game().creationFiletime().value());
                assertEquals(original.manifestRef(), DriverObservationEvidenceReader.reference(captured.semantic().get("java_driver_facts_evidence")));
            }
            assertArrayEquals(packetBefore, original.packet());
            assertArrayEquals(driverBefore, original.driver().bytes());
            assertArrayEquals(manifestBefore, original.manifest().bytes());
        }
    }

    @Test void originalProjectionFailuresRemainIncompleteButEarlierRawErrorsStillThrow() {
        var original = originals(1, STATE);
        var actual = DriverObservationEvidenceReader.nativeFrame(original.manifestRef(), original.manifest(), original.packet());
        var facts = DriverObservationEvidenceReader.decode(original.manifestRef(), original.manifest(), original.driver(), actual);
        var invalidEvidence = new ExactRef(original.nativeRef().path(), original.nativeRef().bytes(), "0".repeat(64));
        var expected = assertInstanceOf(DriverObservationAssembler.Incomplete.class,
                new DriverObservationAssembler().assemble(actual, facts, invalidEvidence));
        assertEquals(List.of("native_driver_fact_join: original native evidence differs"), expected.reasons());
        var decoder = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        assertIncomplete(expected, DriverObservationEvidenceReader.replayOriginals(
                original.manifestRef(), original.manifest(), original.driver(), original.packet(), invalidEvidence));
        assertIncomplete(expected, DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(
                original.manifestRef(), original.manifest(), original.driver(), original.packet(), invalidEvidence, decoder));
        for (DriverFrameEvidenceLoader selected : new DriverFrameEvidenceLoader[] {null, decoder}) {
            assertIncomplete(expected, DriverObservationEvidenceReader.replayCapturedOriginals(
                    original.manifestRef(), original.manifest(), original.packet(), invalidEvidence,
                    ref -> original.driver(), () -> selected));
        }
        // The distinct Source37 Loader raw entry keeps its original first-project exception boundary.
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.assembleValidatedOriginalsWithScopedDriverDecode(
                original.manifestRef(), original.manifest(), original.driver(), original.packet(), invalidEvidence,
                new DriverObservationAssembler(), decoder));
        assertThrows(NullPointerException.class, () -> DriverObservationEvidenceReader.replayOriginals(
                original.manifestRef(), original.manifest(), original.driver(), original.packet(), null));

        byte[] broken = original.packet().clone(); broken[0] ^= 1;
        var rawFailure = assertThrows(IllegalArgumentException.class,
                () -> DriverObservationEvidenceReader.nativeFrame(original.manifestRef(), original.manifest(), broken));
        var replayFailure = assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginals(
                original.manifestRef(), original.manifest(), original.driver(), broken, original.nativeRef()));
        assertEquals(rawFailure.getClass(), replayFailure.getClass());
        assertEquals(rawFailure.getMessage(), replayFailure.getMessage());
        var changedDriver = RawJson.fullMaterial(DriverStateAssemblerTest.bytes(new String(original.driver().bytes(),
                java.nio.charset.StandardCharsets.UTF_8).replace("campaign-original", "changed-campaign")));
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(
                original.manifestRef(), original.manifest(), changedDriver, original.packet(), original.nativeRef(), decoder));

        var mismatch = originals(1, STATE.replace("\"character_id\":73", "\"character_id\":74"));
        var frame = DriverObservationEvidenceReader.nativeFrame(mismatch.manifestRef(), mismatch.manifest(), mismatch.packet());
        var mismatchedFacts = DriverObservationEvidenceReader.decode(mismatch.manifestRef(), mismatch.manifest(), mismatch.driver(), frame);
        var oldMismatch = assertInstanceOf(DriverObservationAssembler.Incomplete.class,
                new DriverObservationAssembler().assemble(frame, mismatchedFacts, mismatch.nativeRef()));
        assertIncomplete(oldMismatch, DriverObservationEvidenceReader.replayOriginals(
                mismatch.manifestRef(), mismatch.manifest(), mismatch.driver(), mismatch.packet(), mismatch.nativeRef()));
        assertIncomplete(oldMismatch, DriverObservationEvidenceReader.replayCapturedOriginals(
                mismatch.manifestRef(), mismatch.manifest(), mismatch.packet(), mismatch.nativeRef(), ref -> mismatch.driver(), () -> decoder));
    }

    @Test void capturedCallbacksPreserveFailureNullCloneOrderAndPermitNestedRealReplayBeforeHandoff() {
        var original = originals(4, STATE);
        var expected = ordinary(original);
        var decoder = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        var events = new ArrayList<String>();
        var manifestWrong = new ExactRef(original.manifestRef().path(), original.manifestRef().bytes(), "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayCapturedOriginals(
                manifestWrong, original.manifest(), original.packet(), original.nativeRef(),
                ref -> { events.add("driver"); return original.driver(); }, () -> { events.add("decoder"); return decoder; }));
        assertTrue(events.isEmpty());
        var driverFailure = new IllegalStateException("original Driver callback sentinel");
        assertSame(driverFailure, assertThrows(IllegalStateException.class, () -> DriverObservationEvidenceReader.replayCapturedOriginals(
                original.manifestRef(), original.manifest(), original.packet(), original.nativeRef(),
                ref -> { events.add("driver"); throw driverFailure; }, () -> { events.add("decoder"); return decoder; })));
        assertEquals(List.of("driver"), events); events.clear();
        var getterFailure = new IllegalStateException("original decoder getter sentinel");
        assertSame(getterFailure, assertThrows(IllegalStateException.class, () -> DriverObservationEvidenceReader.replayCapturedOriginals(
                original.manifestRef(), original.manifest(), null, original.nativeRef(),
                ref -> { events.add("driver"); return null; }, () -> { events.add("decoder"); throw getterFailure; })));
        assertEquals(List.of("driver", "decoder"), events); events.clear();
        assertThrows(NullPointerException.class, () -> DriverObservationEvidenceReader.replayCapturedOriginals(
                original.manifestRef(), original.manifest(), null, original.nativeRef(),
                ref -> { events.add("driver"); return null; }, () -> { events.add("decoder"); return null; }));
        assertEquals(List.of("driver", "decoder"), events); events.clear();
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayCapturedOriginals(
                original.manifestRef(), original.manifest(), null, original.nativeRef(),
                ref -> { events.add("driver"); return original.driver(); }, () -> { events.add("decoder"); return null; }));
        assertEquals(List.of("driver", "decoder"), events); events.clear();

        byte[] changedByGetter = original.packet().clone();
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayCapturedOriginals(
                original.manifestRef(), original.manifest(), changedByGetter, original.nativeRef(),
                ref -> { events.add("driver"); return original.driver(); },
                () -> { events.add("decoder"); changedByGetter[0] ^= 1; return null; }));
        assertEquals(List.of("driver", "decoder"), events); events.clear();

        // Both callbacks are before the new nominal handoff. This does not invent an external
        // callback while the private constructor token is active.
        var nested = complete(DriverObservationEvidenceReader.replayCapturedOriginals(
                original.manifestRef(), original.manifest(), original.packet(), original.nativeRef(),
                ref -> {
                    events.add("driver-enter");
                    var inner = complete(DriverObservationEvidenceReader.replayOriginals(
                            original.manifestRef(), original.manifest(), original.driver(), original.packet(), original.nativeRef()));
                    assertCompleteData(expected, inner); rejectForgedFull(inner);
                    events.add("driver-exit"); return original.driver();
                }, () -> {
                    events.add("decoder");
                    var inner = complete(DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(
                            original.manifestRef(), original.manifest(), original.driver(), original.packet(), original.nativeRef(), decoder));
                    assertCompleteData(expected, inner); rejectForgedFull(inner); return decoder;
                }));
        assertEquals(List.of("driver-enter", "driver-exit", "decoder"), events);
        assertCompleteData(expected, nested); rejectForgedFull(nested);
    }

    @Test void publicForgedFullRemainsRejectedAfterReplaySuccessIncompleteAndSubsequentSuccess() {
        var original = originals(4, STATE);
        var first = complete(DriverObservationEvidenceReader.replayOriginals(
                original.manifestRef(), original.manifest(), original.driver(), original.packet(), original.nativeRef()));
        rejectForgedFull(first);
        var invalidEvidence = new ExactRef(original.nativeRef().path(), original.nativeRef().bytes(), "0".repeat(64));
        assertInstanceOf(DriverObservationAssembler.Incomplete.class, DriverObservationEvidenceReader.replayOriginals(
                original.manifestRef(), original.manifest(), original.driver(), original.packet(), invalidEvidence));
        rejectForgedFull(first);
        var next = complete(DriverObservationEvidenceReader.replayCapturedOriginals(
                original.manifestRef(), original.manifest(), original.packet(), original.nativeRef(), ref -> original.driver(), () -> null));
        assertCompleteData(first, next); rejectForgedFull(next);
        byte[] semanticBefore = DriverJson.encode(next.semantic());
        byte[] receivedBefore = next.originalProjection().orElseThrow().actual().originalPacket();
        original.packet()[0] ^= 1;
        assertArrayEquals(semanticBefore, DriverJson.encode(next.semantic()));
        assertArrayEquals(receivedBefore, next.originalProjection().orElseThrow().actual().originalPacket());
        rejectForgedFull(next);
    }

    private static DriverObservationAssembler.Complete complete(DriverObservationAssembler.Result result) {
        return assertInstanceOf(DriverObservationAssembler.Complete.class, result);
    }
    private static void assertIncomplete(DriverObservationAssembler.Incomplete expected, DriverObservationAssembler.Result result) {
        assertEquals(expected.reasons(), assertInstanceOf(DriverObservationAssembler.Incomplete.class, result).reasons());
    }
    private static DriverObservationAssembler.Complete ordinary(Originals original) {
        var actual = DriverObservationEvidenceReader.nativeFrame(original.manifestRef(), original.manifest(), original.packet());
        var facts = DriverObservationEvidenceReader.decode(original.manifestRef(), original.manifest(), original.driver(), actual);
        return complete(new DriverObservationAssembler().assemble(actual, facts, original.nativeRef()));
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

}
