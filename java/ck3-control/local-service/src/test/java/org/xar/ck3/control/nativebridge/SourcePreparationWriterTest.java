package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.*;
import java.nio.file.*;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.*;

/** Real borrowed preparation -> actual packet write/archive; source/data tests grant no Family or live Game effect. */
final class SourcePreparationWriterTest {
    @TempDir Path root;
    private static RawJson raw(String value) { return new RawJson(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
    @Test void actualRequestAwarePreparationRetainsItsOriginalFieldsAndMetadataThroughTheSoleWriterAndNativePacket() throws Exception {
        var owner = new AtomicReference<ActionWriterIntegrationFixture>();
        var originalSession = new AtomicReference<ContinuityStorePort.Session>(); var prepared = new AtomicReference<NativeRequest>();
        var callbacks = new AtomicInteger();
        ActionPorts.PreparationPort source = new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) { throw new AssertionError("must use original borrowed request-aware source"); }
            @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand command, String requestId) {
                var f = owner.get(); assertDoesNotThrow(() -> f.writer.requireSession(same)); originalSession.set(same); callbacks.incrementAndGet();
                assertEquals(RequestIds.forActionBody(ActionCodec.bodySha256(command)), requestId);
                var archive = f.archive.withSession(same);
                var basis = archive.preserveMaterial(raw("{\"controlled_original_preparation\":73}"));
                NativeRequest actual = new NativeRequest(command.operation().value(), Optional.of("game.command.pause-map"),
                        raw("{\"reviewed_selector\":73}"), List.of(basis));
                prepared.set(actual); return actual;
            }
        };
        var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"), "game.command.pause-map",
                (command, attempt, dispatch) -> new ActionPorts.Pending("no qualified domain effect claimed", List.of(attempt.guard().nativeEvidence())),
                () -> { }, Optional.empty(), Optional.empty(), false, Optional.of(source));
        try (var f = new ActionWriterIntegrationFixture(root.resolve("source"), false, scenario)) {
            owner.set(f); var command = f.command("source-request-original"); var receipt = f.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class, receipt.state()); assertEquals(1, callbacks.get()); assertEquals(1, f.nativeActionWrites());
            assertSame(originalSession.get(), f.originalHookSession.get()); assertSame(prepared.get(), f.originalPreparedAtHook.get());
            assertEquals(prepared.get(), ActionTransitions.attempt(receipt.state()).orElseThrow().preparedRequest());
            f.writer.locked(same -> f.archive.inSession(same, archive -> {
                var attempt = ActionTransitions.attempt(receipt.state()).orElseThrow();
                assertEquals(prepared.get(), archive.loadRequest(archive.requestReferenceOf(prepared.get())));
                var ack = assertInstanceOf(NativeActionPort.AckReceived.class, ActionTransitions.dispatch(receipt.state()).orElseThrow());
                var wire = assertDoesNotThrow(() -> NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket()));
                var fields = assertDoesNotThrow(() -> NativeWire.object(NativeWire.parse(wire.normalizedAdditionalFields().value())));
                assertEquals(73, fields.get("reviewed_selector").intValue()); assertFalse(fields.has("preparation_evidence"));
                assertEquals(raw("{\"controlled_original_preparation\":73}"), archive.loadMaterial(attempt.preparedRequest().preparationEvidence().getFirst()));
                assertDoesNotThrow(() -> ack.custody().orElseThrow().verify(ack)); return null;
            }));
            assertEquals(receipt, f.coordinator.execute(command)); assertEquals(1, callbacks.get()); assertEquals(1, f.nativeActionWrites());
        }
    }
    @Test void sourcePreparationFailureHasNoIntentPendingImportOrNativeWrite() throws Exception {
        ActionPorts.PreparationPort source = command -> { throw new IllegalArgumentException("controlled actual source unavailable before native submission"); };
        var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"), "game.command.pause-map",
                (command, attempt, dispatch) -> { throw new AssertionError("failed preparation cannot observe an attempt"); },
                () -> { throw new AssertionError("failed preparation cannot dispatch"); }, Optional.empty(), Optional.empty(), false, Optional.of(source));
        try (var f = new ActionWriterIntegrationFixture(root.resolve("source-failed"), false, scenario)) {
            var command = f.command("source-failed-original");
            assertThrows(IllegalArgumentException.class, () -> f.coordinator.execute(command));
            assertEquals(0, f.sequence()); assertEquals(0, f.nativeActionWrites()); assertEquals(0, f.pendingPreparations.get()); assertEquals(0, f.attemptCompletions.get());
            assertEquals(0, f.snapshot().actions().size());
        }
    }
    @Test void sameHeadSnapshotStillRejectsSameFileCasTamperingAtPreSubmissionGuard() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(root.resolve("same-head-cas"), false)) {
            var target = new AtomicReference<ExactRef>(); var changed = new AtomicBoolean();
            var intentSequence = new AtomicLong(); var intentHead = new AtomicReference<String>(); var intentEvent = new AtomicReference<byte[]>();
            var guardCalls = new AtomicInteger();
            f.bindGuardObserver((head, command) -> {
                if (!command.actionId().equals("same-head-cas-tamper")) return;
                int call = guardCalls.incrementAndGet();
                // Only corrupt on the second guard call (after IntentDurable append, before Submitting append)
                if (call != 2) return;
                var prior = ContinuityActionJournal.lookup(head.state(), command.actionId(), f.archive);
                if (prior.isEmpty() || !(prior.orElseThrow().state() instanceof ActionState.IntentDurable)) return;
                try {
                    var same = f.journal.borrowedWriterSession(); f.writer.requireSession(same);
                    assertEquals(head.digest(), same.head().digest()); assertEquals(command, prior.orElseThrow().command());
                    assertEquals(head.state().sequence(), prior.orElseThrow().sequence());
                    intentSequence.set(prior.orElseThrow().sequence()); intentHead.set(head.digest());
                    Path event = f.root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS").resolve(String.format(Locale.ROOT, "%08d.json", intentSequence.get()));
                    intentEvent.set(Files.readAllBytes(event));
                    ExactRef ref = Objects.requireNonNull(target.get()); Path path = Path.of(ref.path());
                    byte[] original = Files.readAllBytes(path); assertEquals(ref.sha256(), ActionCodec.sha256(original));
                    var before = IdentityBearingFileAttributes.read(path); byte[] corrupt = original.clone(); corrupt[corrupt.length - 1] ^= 1;
                    Files.write(path, corrupt); Files.setLastModifiedTime(path, before.lastModifiedTime());
                    var after = IdentityBearingFileAttributes.read(path);
                    assertEquals(before.fileKey(), after.fileKey()); assertEquals(before.size(), after.size());
                    assertEquals(before.lastModifiedTime(), after.lastModifiedTime());
                    assertNotEquals(ref.sha256(), ActionCodec.sha256(Files.readAllBytes(path))); changed.set(true);
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
            var command = f.command("same-head-cas-tamper", java.time.Duration.ofMinutes(2));
            var nativeFrame = f.physicalInputs().transport().latestObservedSnapshot().orElseThrow();
            target.set(f.writer.locked(same -> f.archive.inSession(same, archive -> archive.preserveNativeFrame(nativeFrame))));
            assertThrows(UncheckedIOException.class, () -> f.coordinator.execute(command));
            assertTrue(changed.get(), "actual pre-submission guard must reach the same-file tamper");
            assertEquals(0, f.nativeActionWrites()); assertTrue(intentSequence.get() > 0);
            assertEquals(intentHead.get(), f.writer.locked(same -> same.head().digest()));
            Path events = f.root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS");
            assertArrayEquals(intentEvent.get(), Files.readAllBytes(events.resolve(String.format(Locale.ROOT, "%08d.json", intentSequence.get()))));
            assertFalse(Files.exists(events.resolve(String.format(Locale.ROOT, "%08d.json", intentSequence.get() + 1))));
        }
    }
    @Test void mailboxHeartbeatComesFromTheSameNewOriginalSnapshotRatherThanTheBootstrapDate() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(root.resolve("heartbeat"), false)) {
            var first = f.ready(); var transport = f.physicalInputs().transport();
            var original = transport.latestObservedSnapshot().orElseThrow();
            var state = NativeWire.object(NativeWire.parse(original.state().bytes())); state.put("date_raw", ActionWriterIntegrationFixture.INITIAL_DATE_RAW + 24); state.put("paused", true);
            var publication = StrictJson.object(); publication.put("type", "state_snapshot").put("protocol_version", 1).put("snapshot_id", "source-date-1024").put("revision", 2); publication.set("state", state);
            f.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(publication)));
            var later = f.ready(); assertEquals(ActionWriterIntegrationFixture.INITIAL_DATE_RAW + 24, later.request().before().frame().identity().dateRaw().intValueExact());
            assertEquals(first.request().before().frame().episodeRunId(), later.request().before().frame().episodeRunId());
            assertEquals("source-date-1024", later.request().before().frame().snapshotId());
            assertEquals(0, f.nativeActionWrites()); assertEquals(0, f.sequence());
        }
    }
}

