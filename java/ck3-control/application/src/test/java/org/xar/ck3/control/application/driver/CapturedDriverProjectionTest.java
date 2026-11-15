package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Pure bounded software DATA through the original Driver/manifest/frame codecs and actual assembler.
 * No Root, Session, native port, source permission, clock freshness authority or projection counter.
 * The old public assemble path supplies an independent behavioral oracle; its bodies remain unchanged.
 */
final class CapturedDriverProjectionTest {
    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":null,
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;
    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained","bridge_pid":42,"connection_generation":5},
         "opaque_metric":-0.00e+2}
        """;
    private static final Instant OBSERVED = Instant.parse("2026-10-23T16:00:00Z");
    private record Input(ObservedFrame actual, DriverObservationFacts facts, ExactRef evidence) { }

    @Test void capturedProjectionMatchesTheOriginalPublicAssemblerAcrossAllFourProfiles() throws IOException {
        var assembler = new DriverObservationAssembler();
        for (long profile : List.of(1L, 2L, 3L, 4L)) {
            var input = input(profile);
            byte[] packetBefore = input.actual().originalPacket(), stateBefore = input.actual().state().bytes();
            var original = assertInstanceOf(DriverObservationAssembler.Complete.class,
                    assembler.assemble(input.actual(), input.facts(), input.evidence()));
            var capturedResult = assembler.withCapturedProjection(input.actual(), input.facts(), input.evidence(), full -> () -> {
                assertSame(input.actual(), full.actual());
                assertSame(input.facts(), full.facts());
                assertSame(input.evidence(), full.originalEvidence());
                var result = assertInstanceOf(DriverObservationAssembler.Complete.class,
                        assembler.assembleCapturedProjection(full, input.actual(), input.facts(), input.evidence()));
                equivalent(original, result);
                if (profile == DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION) {
                    assertSame(full, result.originalProjection().orElseThrow());
                    assertEquals(new OpportunityJson.Text("native_campaign"), result.semantic().get("episode_projection"));
                    NativeCampaignProjection.requireJoinedSnapshot(full, RawJson.fullMaterial(DriverJson.encode(result.semantic())));
                } else assertTrue(result.originalProjection().isEmpty());
                assertEquals(2, OpportunityJson.array(result.semantic().get("native_command_history"), "history").size());
                assertEquals(new OpportunityJson.DecimalValue("-0.00e+2"), result.semantic().get("opaque_metric"));
                assertEquals(OBSERVED, result.observedAt());
                assertArrayEquals(packetBefore, input.actual().originalPacket());
                assertArrayEquals(stateBefore, input.actual().state().bytes());
                return result;
            });
            // Returned immutable observation DATA remains usable; only its nominal callback capability expires.
            equivalent(original, capturedResult);
            assertArrayEquals(packetBefore, input.actual().originalPacket());
            assertArrayEquals(stateBefore, input.actual().state().bytes());
        }
    }

    @Test void nominalCaptureRejectsOtherInputObjectsForeignThreadsAndNormalOrExceptionalEscape() throws Exception {
        var assembler = new DriverObservationAssembler();
        var input = input(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION);
        var escaped = new AtomicReference<DriverObservationAssembler.FullSnapshot>();
        assembler.withCapturedProjection(input.actual(), input.facts(), input.evidence(), full -> () -> {
            escaped.set(full);
            var otherFrame = new ObservedFrame(input.actual().session(), input.actual().snapshotId(), input.actual().nativeRevision(),
                    input.actual().state(), input.actual().originalPacket(), input.actual().observedAt());
            assertNotSame(input.actual(), otherFrame);
            assertArrayEquals(input.actual().originalPacket(), otherFrame.originalPacket());
            assertThrows(IllegalArgumentException.class,
                    () -> assembler.assembleCapturedProjection(full, otherFrame, input.facts(), input.evidence()));
            var sameValueFacts = copiedFacts(input.facts(), input.facts().source());
            assertEquals(input.facts(), sameValueFacts);
            assertNotSame(input.facts(), sameValueFacts);
            assertThrows(IllegalArgumentException.class,
                    () -> assembler.assembleCapturedProjection(full, input.actual(), sameValueFacts, input.evidence()));
            var source = input.facts().source();
            var foreignSource = new G2Source(source.machineId(), source.observedAtUtc(), "other-software-source", source.sourceRef());
            var foreignFacts = copiedFacts(input.facts(), foreignSource);
            assertThrows(IllegalArgumentException.class,
                    () -> assembler.assembleCapturedProjection(full, input.actual(), foreignFacts, input.evidence()));
            var equalEvidence = new ExactRef(input.evidence().path(), input.evidence().bytes(), input.evidence().sha256());
            assertEquals(input.evidence(), equalEvidence);
            assertNotSame(input.evidence(), equalEvidence);
            assertThrows(IllegalArgumentException.class,
                    () -> assembler.assembleCapturedProjection(full, input.actual(), input.facts(), equalEvidence));

            var equalFull = new DriverObservationAssembler.FullSnapshot(full.actual(), full.facts(), full.semantic(),
                    full.originalEvidence(), full.fullBindingSha256());
            assertEquals(full, equalFull);
            assertNotSame(full, equalFull);
            assertThrows(IllegalArgumentException.class,
                    () -> assembler.assembleCapturedProjection(equalFull, input.actual(), input.facts(), input.evidence()),
                    "record value equality cannot manufacture identity membership in the issuer's private stack");
            var foreignIssuer = new DriverObservationAssembler();
            assertThrows(IllegalArgumentException.class,
                    () -> foreignIssuer.assembleCapturedProjection(full, input.actual(), input.facts(), input.evidence()));

            var failure = new AtomicReference<Throwable>();
            Thread foreign = new Thread(() -> {
                try {
                    assembler.assembleCapturedProjection(full, input.actual(), input.facts(), input.evidence());
                    failure.set(new AssertionError("foreign thread consumed a capture"));
                } catch (Throwable actual) { failure.set(actual); }
            }, "captured-projection-software-foreign");
            foreign.setDaemon(true);
            foreign.start();
            try { foreign.join(5000); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
            assertFalse(foreign.isAlive(), "bounded software thread did not finish");
            assertInstanceOf(IllegalArgumentException.class, failure.get());
            assertInstanceOf(DriverObservationAssembler.Complete.class,
                    assembler.assembleCapturedProjection(full, input.actual(), input.facts(), input.evidence()));
            var innerEscaped = new AtomicReference<DriverObservationAssembler.FullSnapshot>();
            assembler.withCapturedProjection(input.actual(), input.facts(), input.evidence(), inner -> () -> {
                innerEscaped.set(inner);
                assertNotSame(full, inner);
                assertEquals(full, inner);
                assertInstanceOf(DriverObservationAssembler.Complete.class,
                        assembler.assembleCapturedProjection(inner, input.actual(), input.facts(), input.evidence()));
                assertInstanceOf(DriverObservationAssembler.Complete.class,
                        assembler.assembleCapturedProjection(full, input.actual(), input.facts(), input.evidence()),
                        "the original active outer identity remains owned during nested capture");
                return null;
            });
            assertThrows(IllegalArgumentException.class,
                    () -> assembler.assembleCapturedProjection(innerEscaped.get(), input.actual(), input.facts(), input.evidence()));
            assertInstanceOf(DriverObservationAssembler.Complete.class,
                    assembler.assembleCapturedProjection(full, input.actual(), input.facts(), input.evidence()));
            return null;
        });
        // FullSnapshot stays ordinary immutable DATA after callback; it no longer grants a private consumer shortcut.
        assertSame(input.actual(), escaped.get().actual());
        assertThrows(IllegalArgumentException.class,
                () -> assembler.assembleCapturedProjection(escaped.get(), input.actual(), input.facts(), input.evidence()));
        var callbackFailure = new IOException("software projection callback original marker");
        assertSame(callbackFailure, assertThrows(IOException.class,
                () -> assembler.withCapturedProjection(input.actual(), input.facts(), input.evidence(), full -> () -> {
                    escaped.set(full);
                    throw callbackFailure;
                })));
        assertThrows(IllegalArgumentException.class,
                () -> assembler.assembleCapturedProjection(escaped.get(), input.actual(), input.facts(), input.evidence()));

        var factoryFailure = new IllegalStateException("software Function.apply original marker");
        assertSame(factoryFailure, assertThrows(IllegalStateException.class,
                () -> assembler.withCapturedProjection(input.actual(), input.facts(), input.evidence(), full -> {
                    escaped.set(full);
                    throw factoryFailure;
                })));
        assertThrows(IllegalArgumentException.class,
                () -> assembler.assembleCapturedProjection(escaped.get(), input.actual(), input.facts(), input.evidence()));
        var checkedFailure = new Exception("software Callable unexpected checked marker");
        var wrapped = assertThrows(IOException.class,
                () -> assembler.withCapturedProjection(input.actual(), input.facts(), input.evidence(), full -> () -> {
                    escaped.set(full);
                    throw checkedFailure;
                }));
        assertSame(checkedFailure, wrapped.getCause());
        assertThrows(IllegalArgumentException.class,
                () -> assembler.assembleCapturedProjection(escaped.get(), input.actual(), input.facts(), input.evidence()));
    }

    @Test void callerConstructedFullSnapshotsRemainUntrustedAndInvalidOriginalsCannotIssueACapture() throws IOException {
        var assembler = new DriverObservationAssembler();
        var input = input(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION);
        var original = assertInstanceOf(DriverObservationAssembler.Complete.class,
                assembler.assemble(input.actual(), input.facts(), input.evidence()));
        var full = assembler.withCapturedProjection(input.actual(), input.facts(), input.evidence(),
                issued -> () -> issued);
        // A public FullSnapshot is ordinary DATA. Its public Complete constructor must still replay the originals.
        equivalent(original, complete(original, full, original.observedAt()));
        var changedSemantic = full.semantic().with("software_forged_projection", new OpportunityJson.Bool(true));
        assertNotEquals(full.semantic(), changedSemantic);
        var forged = new DriverObservationAssembler.FullSnapshot(full.actual(), full.facts(), changedSemantic,
                full.originalEvidence(), full.fullBindingSha256());
        var semanticFailure = assertThrows(IllegalArgumentException.class,
                () -> complete(original, forged, original.observedAt()));
        assertTrue(semanticFailure.getMessage().contains("native campaign complete DATA crossed its actual full projection"));
        assertThrows(IllegalArgumentException.class, () -> complete(original, full, original.observedAt().plusNanos(1)));
        assertThrows(IllegalArgumentException.class,
                () -> new DriverObservationAssembler.Complete(original.identity(), original.source(), original.sessionId(),
                        original.connectionGeneration(), original.semantic(), original.originalEvidence(), original.observedAt(),
                        original.fullBindingSha256(), Optional.empty()));

        byte[] brokenPacket = input.actual().originalPacket();
        brokenPacket[0] ^= 1;
        var invalid = new ObservedFrame(input.actual().session(), input.actual().snapshotId(), input.actual().nativeRevision(),
                input.actual().state(), brokenPacket, input.actual().observedAt());
        var invalidEvidence = reference(brokenPacket);
        assertInstanceOf(DriverObservationAssembler.Incomplete.class,
                assembler.assemble(invalid, input.facts(), invalidEvidence));
        var callbacks = new AtomicInteger();
        assertThrows(IllegalArgumentException.class,
                () -> assembler.withCapturedProjection(invalid, input.facts(), invalidEvidence, issued -> {
                    callbacks.incrementAndGet();
                    return () -> issued;
                }));
        assertEquals(0, callbacks.get(), "a broken original packet must fail before nominal capture issuance");
        var recovered = assembler.withCapturedProjection(input.actual(), input.facts(), input.evidence(),
                issued -> () -> assembler.assembleCapturedProjection(issued, input.actual(), input.facts(), input.evidence()));
        equivalent(original, assertInstanceOf(DriverObservationAssembler.Complete.class, recovered));
    }

    private static DriverObservationAssembler.Complete complete(DriverObservationAssembler.Complete original,
            DriverObservationAssembler.FullSnapshot full, Instant observedAt) {
        return new DriverObservationAssembler.Complete(original.identity(), original.source(), original.sessionId(),
                original.connectionGeneration(), original.semantic(), original.originalEvidence(), observedAt,
                original.fullBindingSha256(), Optional.of(full));
    }

    private static void equivalent(DriverObservationAssembler.Complete original, DriverObservationAssembler.Complete actual) {
        assertEquals(original.identity(), actual.identity());
        assertEquals(original.source(), actual.source());
        assertEquals(original.sessionId(), actual.sessionId());
        assertEquals(original.connectionGeneration(), actual.connectionGeneration());
        assertEquals(original.originalEvidence(), actual.originalEvidence());
        assertEquals(original.observedAt(), actual.observedAt());
        assertEquals(original.fullBindingSha256(), actual.fullBindingSha256());
        assertEquals(original.semantic(), actual.semantic());
        assertArrayEquals(DriverJson.encode(original.semantic()), DriverJson.encode(actual.semantic()));
        assertEquals(original.originalProjection(), actual.originalProjection());
    }

    private static DriverObservationFacts copiedFacts(DriverObservationFacts old, G2Source source) {
        return new DriverObservationFacts(old.driver(), old.driverVersion(), old.episodeEpoch(), old.transport(), old.snapshotId(),
                old.nativeRevision(), old.nativeStateSha256(), old.publicRevision(), old.observationVersion(), source,
                old.originalSemanticFields(), old.semanticFactsEvidence());
    }

    private static Input input(long profile) {
        var driver = DriverStateSnapshot.decodeComplete(bytes(DRIVER));
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        String state = STATE.strip();
        byte[] envelope = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(envelope.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(envelope.length).put(envelope).array();
        var actual = new ObservedFrame(new TransportSession("test-machine", game, BigInteger.valueOf(5), "held-session"),
                "snapshot-9", BigInteger.valueOf(9), new RawJson(bytes(state)), packet, OBSERVED);
        var stamp = new DriverSnapshotFacts.Stamp(3, 7, game, driver.session().episodeRunId(), DriverJson.sha256(driver.encode()));
        var auxiliary = profile == DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                ? new OpportunityJson.Obj(Map.of("episode_projection", new OpportunityJson.Text(NativeCampaignProjection.WIRE_MODE)))
                : new OpportunityJson.Obj(Map.of());
        var driverRef = reference(driver.encode());
        var known = new DriverSnapshotFacts.Known(driver, stamp, driverRef, List.of(), auxiliary, Optional.empty(), Optional.empty());
        var source = new G2Source("test-machine", "2026-10-23T16:00:00Z", "test-source", reference(bytes("software original source")));
        var manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.valueOf(2), profile, source, auxiliary, driverRef);
        var facts = DriverObservationEvidenceReader.decode(reference(manifest.bytes()), manifest, RawJson.fullMaterial(driver.encode()), actual);
        return new Input(actual, facts, reference(packet));
    }

    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef reference(byte[] bytes) {
        // Reference-shaped software DATA only; this path is never read, written or treated as an actual original.
        return new ExactRef(Path.of(System.getProperty("java.io.tmpdir"), "captured-projection-data", DriverJson.sha256(bytes) + ".bin")
                .toAbsolutePath().toString(), bytes.length, DriverJson.sha256(bytes));
    }
}
