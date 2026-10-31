package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.*;

/** Actual canonical writer/packet/archive failures; no synthesized Complete, ACK or successful semantic proof. */
final class ActionReconciliationWriterTest {
    @TempDir Path root;
    private static ActionWriterIntegrationFixture.SoftwareActionScenario action(AtomicInteger observations) {
        return new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"), "game.command.pause-map",
                (command, attempt, original) -> {
                    observations.incrementAndGet();
                    assertFalse(ActionReconciliationScope.activeFor(command), "ordinary execution never borrows reconciliation scope");
                    return new ActionPorts.Pending("controlled independent poststate remains unavailable", List.of(attempt.guard().nativeEvidence()));
                }, () -> { });
    }
    @Test void unboundGameplayRecoveryRetainsTheActualOriginalAttemptWithoutOrdinaryFallbackOrReplay() throws Exception {
        var observations = new AtomicInteger();
        try (var f = new ActionWriterIntegrationFixture(root.resolve("unbound"), false, action(observations))) {
            var original = f.coordinator.execute(f.command("original-unbound"));
            assertInstanceOf(ActionState.Unknown.class, original.state()); assertEquals(1, observations.get());
            int reads = f.nativeReadWrites(), packets = f.nativePacketReads();
            var recovered = f.coordinator.reconcile(original.command().actionId());
            assertInstanceOf(ActionState.Unknown.class, recovered.state());
            assertEquals(ActionTransitions.attempt(original.state()), ActionTransitions.attempt(recovered.state()));
            assertEquals(ActionTransitions.dispatch(original.state()), ActionTransitions.dispatch(recovered.state()));
            assertEquals(1, observations.get()); assertEquals(1, f.nativeActionWrites());
            assertEquals(reads, f.nativeReadWrites()); assertEquals(packets, f.nativePacketReads());
            assertFalse(ActionReconciliationScope.activeFor(original.command()));
            assertThrows(RuntimeException.class, () -> ActionReconciliationScope.requireFrame(original.command()));
            assertThrows(RuntimeException.class, () -> f.coordinator.bindReconciliationObservation((s, p, d, w) -> new ActionPorts.Pending("too late", List.of())));
            assertEquals(recovered, f.coordinator.execute(original.command()), "execute never implicitly reconciles the retained request");
        }
    }
    @Test void rawOnlyProviderPreservesItsActualPhysicalOriginalsWithoutMintingACompleteOrEnteringTheObserver() throws Exception {
        var observations = new AtomicInteger(); var provider = new AtomicInteger();
        try (var f = new ActionWriterIntegrationFixture(root.resolve("raw-only"), false, action(observations))) {
            f.coordinator.bindReconciliationObservation((same, pending, deadline, observer) -> {
                f.writer.requireSession(same); provider.incrementAndGet();
                assertEquals(pending, ContinuityActionJournal.lookup(same.head().state(), pending.command().actionId(), f.archive.withSession(same)).orElseThrow());
                assertTrue(Instant.now().isBefore(deadline)); assertFalse(ActionReconciliationScope.activeFor(pending.command()));
                var attempt = ActionTransitions.attempt(pending.state()).orElseThrow();
                return new ActionPorts.Pending("actual raw-only observation cannot join the unchanged player", List.of(attempt.guard().nativeEvidence(), attempt.guard().capabilityEvidence()));
            });
            var original = f.coordinator.execute(f.command("raw-only-original")); int packets = f.nativePacketReads();
            var recovered = f.coordinator.reconcile(original.command().actionId());
            var unknown = assertInstanceOf(ActionState.Unknown.class, recovered.state());
            var attempt = ActionTransitions.attempt(original.state()).orElseThrow();
            assertEquals(List.of(attempt.guard().nativeEvidence(), attempt.guard().capabilityEvidence()), unknown.evidence());
            assertEquals(1, observations.get()); assertEquals(1, provider.get()); assertEquals(1, f.nativeActionWrites());
            assertEquals(packets, f.nativePacketReads()); assertFalse(ActionReconciliationScope.activeFor(original.command()));
            assertThrows(RuntimeException.class, () -> f.coordinator.bindReconciliationObservation((s, p, d, w) -> new ActionPorts.Pending("replacement", List.of())));
        }
    }
    @Test void interruptedPhysicalObservationRetainsTheOriginalRequestAndClearsEveryPrivateCallbackScope() throws Exception {
        var observations = new AtomicInteger();
        try (var f = new ActionWriterIntegrationFixture(root.resolve("interrupted"), false, action(observations))) {
            f.coordinator.bindReconciliationObservation((same, pending, deadline, observer) -> { throw new InterruptedException("controlled observation interrupted"); });
            var original = f.coordinator.execute(f.command("interrupted-original"));
            try {
                var recovered = f.coordinator.reconcile(original.command().actionId());
                assertInstanceOf(ActionState.Unknown.class, recovered.state()); assertTrue(Thread.currentThread().isInterrupted());
                assertEquals(ActionTransitions.attempt(original.state()), ActionTransitions.attempt(recovered.state()));
                assertEquals(1, observations.get()); assertEquals(1, f.nativeActionWrites());
                assertFalse(ActionReconciliationScope.activeFor(original.command()));
                assertThrows(RuntimeException.class, () -> ActionReconciliationScope.requireIdentity(original.command()));
            } finally { Thread.interrupted(); }
        }
    }
    @Test void providerCannotInventCompleteIdentityOrGuardDataToEnterTheActualOriginalObserver() throws Exception {
        var observations = new AtomicInteger();
        try (var f = new ActionWriterIntegrationFixture(root.resolve("missing-qualified-data"), false, action(observations))) {
            f.coordinator.bindReconciliationObservation((same, pending, deadline, observer) -> observer.apply(null, null, null, null));
            var original = f.coordinator.execute(f.command("missing-qualified-original"));
            var recovered = f.coordinator.reconcile(original.command().actionId());
            assertInstanceOf(ActionState.Unknown.class, recovered.state());
            assertEquals(1, observations.get()); assertEquals(1, f.nativeActionWrites());
            assertFalse(ActionReconciliationScope.activeFor(original.command()));
            assertThrows(RuntimeException.class, () -> ActionReconciliationScope.requireObservationGuard(original.command()));
        }
    }
    @Test void installedReadCapabilitiesAndExplicitVersionComeFromTheActualControlledHelloPacket() throws Exception {
        var installed = new java.util.concurrent.atomic.AtomicReference<ReadContract<RawJson>>();
        var read = new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "fixture-adapter",
                reviewed -> {
                    var contract = new ReadContract<RawJson>("extra-software/v1", new OperationKey("query-extra-software"),
                            Optional.of("game.query.extra-software"), "extra-software", ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                            ReadContract.WireProfile.EXECUTE_STEP, reviewed,
                            request -> new NativeRequest("query-extra-software", "game.query.extra-software", new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))),
                            receipt -> receipt.original().originalResultToken().orElseThrow());
                    installed.set(contract); return List.of(contract);
                }, request -> new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                Optional.of("1.20.0.4"), Set.of("game.state.pending-character-interaction"));
        try (var f = new ActionWriterIntegrationFixture(root.resolve("hello"), false, read)) {
            f.ready(); var hello = f.physicalInputs().transport().originalHello();
            assertTrue(hello.capabilities().containsAll(Set.of("game.query.extra-software", "game.state.pending-character-interaction")));
            var raw = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello.packet().value(), 4, hello.packet().value().length)));
            assertEquals("1.20.0.4", NativeWire.text(raw.get("expected_ck3_version")));
            assertSame(installed.get(), f.extraReadContracts().getFirst());
            assertSame(f.frameLoader(), f.physicalInputs().frameLoader());
            assertEquals(0, f.nativeActionWrites());
        }
    }
    @Test void optInSaveBaselineIsParsedFromTheSameImmutableInitialPacketAndDoesNotGiveCycleOrDayCredit() throws Exception {
        var save = new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("save-checkpoint"), "game.save-checkpoint",
                (command, attempt, dispatch) -> new ActionPorts.Pending("no actual SAVE requested", List.of()), () -> { },
                Optional.empty(), Optional.empty(), true);
        try (var f = new ActionWriterIntegrationFixture(root.resolve("save-baseline"), false, save)) {
            var initial = f.writer.locked(same -> same.head().state().toJson());
            var binding = StrictJson.object(initial.get("latest_binding"), Set.of("date_raw", "actor_character_id", "episode_run_id", "snapshot_id", "revision", "native_revision"));
            var original = ExactRef.fromJson(initial.get("java_controlled_initial_native_packet"));
            byte[] packet = Files.readAllBytes(Path.of(original.path()));
            assertEquals(packet.length, original.bytes()); assertEquals(ActionCodec.sha256(packet), original.sha256());
            var snapshot = assertInstanceOf(NativeWire.Snapshot.class, NativeWire.decode(packet));
            assertEquals(snapshot.snapshotId(), StrictJson.text(binding.get("snapshot_id")));
            assertEquals(snapshot.revision(), binding.get("native_revision").bigIntegerValue());
            assertEquals(ActionWriterIntegrationFixture.INITIAL_DATE_RAW, binding.get("date_raw").intValue()); assertEquals(73, binding.get("actor_character_id").intValue());
            assertEquals(0, initial.get("last_settled_cycles").intValue()); assertEquals(0, f.sequence()); assertEquals(0, f.nativeActionWrites());
            assertEquals(f.ready().request().before().frame().snapshotId(), snapshot.snapshotId());
        }
    }
}

