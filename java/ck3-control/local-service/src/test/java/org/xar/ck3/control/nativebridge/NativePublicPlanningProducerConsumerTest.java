package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.contracts.StrictJson;

/** Real collector/Driver/writer/archive consumers with controlled packet/process/source edges only. */
final class NativePublicPlanningProducerConsumerTest {
    @TempDir Path temporary;

    /** A finite software source verifier checks actual originals and pins; it grants no Managed or Game qualification. */
    static AtomicInteger bindSoftwareSource(ActionWriterIntegrationFixture actual) {
        AtomicInteger verified = new AtomicInteger();
        actual.collector.bindPublicSourceAuthority((same, owner, full, known, received, process, deadline) -> {
            actual.writer.requireSession(same);
            assertEquals(actual.observationIdentity(), owner); assertEquals(owner.game(), process.measured());
            assertEquals(actual.observationSource(), full.facts().source());
            assertEquals(full.actual().session(), received.session().orElseThrow());
            assertArrayEquals(known.driver().encode(), full.facts().driver().encode());
            var original = actual.observationSource().sourceRef();
            var sourcePin = same.capturePin(original, 65_536); same.verifyPin(sourcePin);
            var packetPin = same.capturePin(full.originalEvidence(), 64 * 1024 * 1024 + 4); same.verifyPin(packetPin);
            // This proof is the retained finite software source itself, never a generated live source manifest.
            return new NativeReadinessCollector.SourceQualification(original, borrowed -> {
                assertSame(same, borrowed); actual.writer.requireSession(borrowed);
                borrowed.verifyPin(sourcePin); borrowed.verifyPin(packetPin);
                assertEquals(full.actual().session(), actual.physicalInputs().transport().diagnostics().session().orElseThrow());
                verified.incrementAndGet();
            });
        });
        return verified;
    }
    static void publish(ActionWriterIntegrationFixture actual, Consumer<ObjectNode> change)
            throws IOException, InterruptedException {
        var before = actual.physicalInputs().transport().currentSnapshot(Instant.now().plusSeconds(10));
        ObjectNode state = assertInstanceOf(ObjectNode.class,
                org.xar.ck3.control.contracts.FullJsonTree.parse(before.state().bytes(), DriverJson.MAX_NATIVE_BYTES));
        change.accept(state);
        ObjectNode packet = StrictJson.object();
        packet.put("type", "state_snapshot").put("protocol_version", 1)
                .put("snapshot_id", before.snapshotId() + "-public")
                .put("revision", before.nativeRevision().add(BigInteger.ONE));
        packet.set("state", state);
        actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(packet)));
        actual.physicalInputs().transport().observe(Instant.now().plusSeconds(10));
    }

    @Test void missingActualSourceBinderRefusesBeforeAnyConsumerOrNativeIo() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("missing-binder"), false)) {
            actual.ready(); int packets = actual.nativePacketReads(); AtomicInteger calls = new AtomicInteger();
            actual.writer.locked(same -> {
                var failure = assertThrows(IllegalArgumentException.class, () -> actual.collector.withOwnedPublicPlanning(
                        same, actual.observationIdentity(), Instant.now().plusSeconds(10), ignored -> calls.incrementAndGet()));
                assertEquals("actual public physical-origin authority is not installed", failure.getMessage()); return null;
            });
            assertEquals(0, calls.get()); assertEquals(packets, actual.nativePacketReads());
        }
    }

    @Test void realRunningDeadChangedAndMissingPlayerPacketsReachObservedConsumerWithoutReadyPublication() throws Exception {
        for (String phase : List.of("running", "dead", "changed-player", "missing-player")) {
            try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(phase), false)) {
                actual.ready(); var published = actual.lastPublishedReady.get(); AtomicInteger sources = bindSoftwareSource(actual);
                publish(actual, state -> {
                    if (phase.equals("running")) state.put("paused", false);
                    else if (phase.equals("dead")) ((ObjectNode) state.get("played_character")).put("alive", false);
                    else if (phase.equals("changed-player")) ((ObjectNode) state.get("played_character")).put("character_id", 74);
                    else state.putNull("played_character");
                });
                var head = actual.ledgerBytes(); var actions = actual.snapshot().actions();
                int packets = actual.nativePacketReads(), reads = actual.nativeReadWrites(), writes = actual.nativeActionWrites();
                AtomicReference<NativeReadinessCollector.PublicPlanningFrame> escaped = new AtomicReference<>();
                actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same, actual.observationIdentity(),
                        Instant.now().plusSeconds(10), union -> {
                            union.assertCurrent(same);
                            var observed = assertInstanceOf(NativeReadinessCollector.PublicObserved.class, union);
                            assertTrue(observed.observation().isEmpty()); var frame = union.frame(); escaped.set(frame);
                            assertEquals(actions, frame.actions());
                            assertArrayEquals(frame.driver().driver().encode(), frame.snapshot().facts().driver().encode());
                            assertArrayEquals(frame.driver().driver().encode(), DriverStateSnapshot.decodeComplete(frame.driver().driver().encode()).encode());
                            assertEquals(frame.originalDriver().sha256(), DriverJson.sha256(frame.driver().driver().encode()));
                            assertEquals(frame.snapshot().actual().originalPacket().length, frame.snapshot().originalEvidence().bytes());
                            boolean joined = phase.equals("running") || phase.equals("dead");
                            assertEquals(joined, frame.joined() instanceof DriverObservationAssembler.Complete);
                            assertTrue(frame.receivedCapabilities().isPresent());
                            var received = frame.receivedCapabilities().orElseThrow();
                            var diagnostics = org.xar.ck3.control.planning.opportunity.OpportunityJson.object(received.get("diagnostics"), "diagnostics");
                            assertEquals(org.xar.ck3.control.application.readiness.RootNativeCapabilities.framedObject(
                                    actual.archive.readArtifact(same, frame.originalHello(), 1 << 20)), diagnostics.get("hello"));
                            assertEquals(org.xar.ck3.control.application.readiness.RootNativeCapabilities.framedObject(
                                    actual.archive.readArtifact(same, frame.originalHeartbeat(), 1 << 20)), diagnostics.get("last_heartbeat"));
                            assertEquals(received, DriverJson.object(DriverJson.encode(received), DriverJson.MAX_NATIVE_BYTES));
                            assertEquals(frame.sourceQualification().proof(), frame.originalSourceProof());
                            org.xar.ck3.control.application.planning.campaign.PublicTerminalDataContext terminal = frame;
                            terminal.assertCurrent(same); assertSame(frame.snapshot(), terminal.snapshot());
                            assertEquals(frame.driver(), terminal.driver());
                            if (!joined) {
                                var missing = assertThrows(IllegalArgumentException.class,
                                        () -> frame.collectTerminalInputs(same, Instant.now().plusSeconds(5)));
                                assertEquals("actual read-only public terminal input producer is not installed", missing.getMessage());
                            }
                            if (!joined) assertThrows(IllegalArgumentException.class, () -> frame.collectInputs(same, Instant.now().plusSeconds(5)));
                            assertTrue(frame.ordinarySemantic().isEmpty()); union.assertCurrent(same); return null;
                        }));
                actual.writer.locked(same -> {
                    assertThrows(IllegalArgumentException.class, () -> escaped.get().assertCurrent(same)); return null;
                });
                assertSame(published, actual.lastPublishedReady.get()); assertArrayEquals(head, actual.ledgerBytes());
                assertEquals(actions, actual.snapshot().actions()); assertEquals(packets, actual.nativePacketReads());
                assertEquals(reads, actual.nativeReadWrites()); assertEquals(writes, actual.nativeActionWrites()); assertTrue(sources.get() >= 2);
            }
        }
    }

    @Test void actualCanonicalUnknownRemainsObservedAndNeverResubmitsOrReplacesItsAttempt() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("unknown"), true)) {
            var command = actual.command("public-planning-unknown");
            ActionReceipt original = actual.coordinator.execute(command);
            var unknown = assertInstanceOf(ActionState.Unknown.class, original.state()); assertTrue(unknown.attempt().isPresent());
            bindSoftwareSource(actual); var before = actual.snapshot().actions(); var head = actual.ledgerBytes();
            var published = actual.lastPublishedReady.get(); int packets = actual.nativePacketReads(), writes = actual.nativeActionWrites();
            actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same, actual.observationIdentity(),
                    Instant.now().plusSeconds(10), union -> {
                        assertInstanceOf(NativeReadinessCollector.PublicObserved.class, union); union.assertCurrent(same);
                        assertInstanceOf(DriverStateSnapshot.Incomplete.class, union.frame().canonicalDriver());
                        assertEquals(before, union.frame().actions());
                        var missing = assertThrows(IllegalArgumentException.class,
                                () -> union.frame().collectInputs(same, Instant.now().plusSeconds(5)));
                        assertEquals("actual read-only public planning input producer is not installed", missing.getMessage());
                        ActionReceipt retained = union.frame().actions().stream().filter(row -> row.command().actionId().equals(command.actionId())).findFirst().orElseThrow();
                        assertEquals(original, retained); assertEquals(unknown, retained.state()); return null;
                    }));
            assertEquals(before, actual.snapshot().actions()); assertArrayEquals(head, actual.ledgerBytes());
            assertSame(published, actual.lastPublishedReady.get()); assertEquals(writes, actual.nativeActionWrites());
            assertEquals(packets, actual.nativePacketReads());
        }
    }

    @Test void actualReadyStillUsesOriginalPublicationAndTheExactOriginalRequest() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("ready"), false)) {
            actual.ready(); bindSoftwareSource(actual);
            actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same, actual.observationIdentity(),
                    Instant.now().plusSeconds(10), union -> {
                        var ready = assertInstanceOf(NativeReadinessCollector.PublicReady.class, union);
                        union.assertCurrent(same); assertSame(actual.lastPublishedReady.get(), ready.ready().request());
                        assertEquals(ready.lease().frame().identity(), ready.ready().request().before());
                        assertEquals(ready.frame().snapshot().fullBindingSha256(), ready.lease().frame().fullBindingSha256());
                        assertTrue(ready.frame().ordinarySemantic().isPresent());
                        var actualInputs = ready.frame().collectInputs(same, Instant.now().plusSeconds(5));
                        assertEquals(ready.lease().executableSteps(), actualInputs.actionSteps());
                        assertSame(actual.lastPublishedReady.get(), ready.ready().request()); return null;
                    }));
        }
    }

    @Test void originalSourceCorruptionAndConsumerFailureCannotLeaveAnEscapedScope() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("failure"), false)) {
            actual.ready(); bindSoftwareSource(actual); publish(actual, state -> state.put("paused", false));
            AtomicReference<NativeReadinessCollector.PublicPlanningFrame> escaped = new AtomicReference<>();
            actual.writer.locked(same -> {
                IOException failure = assertThrows(IOException.class, () -> actual.collector.withOwnedPublicPlanning(same,
                        actual.observationIdentity(), Instant.now().plusSeconds(10), union -> {
                            escaped.set(union.frame()); throw new IOException("real public consumer failure");
                        }));
                assertEquals("real public consumer failure", failure.getMessage());
                assertThrows(IllegalArgumentException.class, () -> escaped.get().assertCurrent(same)); return null;
            });
            actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same, actual.observationIdentity(),
                    Instant.now().plusSeconds(10), union -> { union.assertCurrent(same); return null; }));
            var source = actual.observationSource().sourceRef(); var path = Path.of(source.path()).toAbsolutePath().normalize();
            assertTrue(path.startsWith(actual.root.toAbsolutePath().normalize()));
            byte[] original = Files.readAllBytes(path);
            try {
                Files.write(path, Arrays.copyOf(original, original.length + 1));
                assertThrows(IOException.class, () -> actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same,
                        actual.observationIdentity(), Instant.now().plusSeconds(10), ignored -> fail("corrupt source cannot reach public consumer"))));
            } finally { Files.write(path, original); }
        }
    }
}
