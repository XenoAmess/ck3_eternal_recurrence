package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111EventObservation;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111RenderedOption;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore.Full111RendererObservation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeFull111OrdinaryEvent;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.CurrentFull111EventRenderer;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeGoalObservationFixture;
import org.xar.ck3.control.nativebridge.NativePacketPort;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeWire;

final class RootFull111EventReadMemoTest {
    private static final String MACHINE = "software-event-memo";
    private static final String SESSION = "event-memo";
    private static final String SHA = "0".repeat(64);
    private static final GameGeneration GAME = new GameGeneration(42, new PythonOnlyUInt64(BigInteger.TEN));

    @Test void successfulReadIsReusedForTheSameOccurrenceDuringItsOriginalWindow() throws Exception {
        var endpoint = new SoftwarePackets();
        String slash = Character.toString(92);
        var config = new NativePipeEndpoint.Config(slash + slash + "." + slash + "pipe" + slash + SESSION,
                MACHINE, GAME, SESSION, "software", SHA, "software-legacy-adapter");
        try (var transport = NativeGoalObservationFixture.receive(endpoint, config)) {
            var deadline = Instant.now().plusSeconds(10);
            var freshness = Duration.ofSeconds(30);
            var frame = transport.observe(deadline, freshness);
            assertSame(frame, transport.observe(deadline, freshness));
            var subject = subject(transport.acceptedSnapshotRevision(frame));
            var evidence = new Full111EventObservation(7, "lyd.1002", subject.full(), subject.semantic(),
                    example("core-read", "1"), example("lyd-read", "2"));
            var reads = new AtomicInteger();
            Instant now = Instant.parse("2026-11-27T00:00:00Z");
            Instant expires = now.plusSeconds(5);
            var memo = new RootFull111EventRead.HeldReadMemo();
            RootFull111EventRead.EventReadAttempt query = () -> {
                reads.incrementAndGet();
                return Optional.of(new RootFull111EventRead.VerifiedRead(expires.plusSeconds(5), evidence));
            };

            assertEquals(Optional.of(evidence), memo.observe(subject, now,
                    () -> Optional.of(new RootFull111EventRead.VerifiedRead(expires, evidence))));
            assertEquals(Optional.of(evidence), memo.observe(subject, now.plusSeconds(1), query));
            assertEquals(0, reads.get());
            assertTrue(memo.observe(subject, expires, () -> Optional.empty()).isEmpty());
            assertEquals(Optional.of(evidence), memo.observe(subject, expires, query));
            assertEquals(1, reads.get());

            var repeated = transport.observe(deadline);
            assertNotSame(frame, repeated);
            assertArrayEquals(frame.originalPacket(), repeated.originalPacket());
            assertEquals(frame.nativeRevision(), repeated.nativeRevision());
            assertEquals(Optional.of(evidence), memo.observe(subject(transport.acceptedSnapshotRevision(repeated)), expires, query));
            assertEquals(2, reads.get());
        }
    }

    @Test void attemptingPreparationReleasesOnlyItsOriginalRendererMemo() throws Exception {
        String slash = Character.toString(92);
        var config = new NativePipeEndpoint.Config(slash + slash + "." + slash + "pipe" + slash + SESSION,
                MACHINE, GAME, SESSION, "software", SHA, "software-legacy-adapter");
        try (var transport = NativeGoalObservationFixture.receive(new SoftwarePackets(), config)) {
            Instant now = Instant.now();
            var frame = transport.observe(now.plusSeconds(10), Duration.ofSeconds(30));
            var subject = subject(transport.acceptedSnapshotRevision(frame));
            var original = example("original-renderer", "6");
            var later = example("later-renderer", "7");
            var flags = List.of(new Full111RenderedOption(0, true, true, true));
            var evidence = new Full111EventObservation(7, "lyd.1002", subject.full(), subject.semantic(),
                    example("core-read", "1"), example("lyd-read", "2"));
            var memo = new RootFull111EventRead.HeldReadMemo();
            var initial = evidence.withRenderer(new Full111RendererObservation(original, flags));
            var replacement = evidence.withRenderer(new Full111RendererObservation(later, flags));
            assertEquals(Optional.of(initial), memo.observe(subject, now,
                    () -> Optional.of(new RootFull111EventRead.VerifiedRead(now.plusSeconds(5), initial))));
            memo.release(later);
            assertEquals(Optional.of(initial), memo.observe(subject, now, () -> { throw new AssertionError("unrelated quote"); }));
            memo.release(original);
            assertEquals(Optional.of(replacement), memo.observe(subject, now,
                    () -> Optional.of(new RootFull111EventRead.VerifiedRead(now.plusSeconds(5), replacement))));
        }
    }

    @Test void exactVisibleRendererLabelSurvivesWithoutUsingItsDisabledReason() {
        String label = "愿守旧约";
        var visible = new CurrentFull111EventRenderer.Option(4, true, true, true, label, "separate tooltip text");
        var hidden = new CurrentFull111EventRenderer.Option(4, true, false, true, label, "");
        var oversized = new CurrentFull111EventRenderer.Option(4, true, true, true, "界".repeat(171), "");
        var empty = new CurrentFull111EventRenderer.Option(4, true, true, true, "", "separate tooltip text");
        assertEquals(Optional.of(label), RootFull111EventRead.displayedOption(visible).displayLabel());
        for (var unavailable : List.of(hidden, oversized, empty))
            assertTrue(RootFull111EventRead.displayedOption(unavailable).displayLabel().isEmpty());
    }

    private static RootFull111EventRead.ReadSubject subject(NativeGameTransport.AcceptedSnapshotRevision original) {
        var identity = new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.ONE, BigInteger.valueOf(53144328));
        var frame = new JointBudgetSelector.ProposalFrame(identity, original.snapshotId(), original.publicRevision(), SESSION);
        var before = new ObservationIdentity(MACHINE, GAME, frame, 1);
        var source = new G2Source(MACHINE, "2026-11-27T00:00:00Z", SHA, example("software-source", "3"));
        return new RootFull111EventRead.ReadSubject(original, before, source, example("full", "4"), example("semantic", "5"),
                new NativeFull111OrdinaryEvent(7, 2));
    }

    private static ExactRef example(String path, String digest) {
        return new ExactRef(path, 1, digest.repeat(64));
    }

    /** A legacy software snapshot supplies occurrence identity without manufacturing Full111 source qualification. */
    private static final class SoftwarePackets implements NativePacketPort {
        private final ArrayDeque<byte[]> packets = new ArrayDeque<>();

        SoftwarePackets() throws IOException {
            var hello = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", GAME.pid())
                    .put("connection_generation", 1).put("bridge_version", "software").put("expected_ck3_sha256", SHA)
                    .put("game_adapter_id", "software-legacy-adapter").put("game_adapter_status", "ready").put("ck3_build_match", true);
            hello.putArray("capabilities").add("game.state.snapshot");
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
            var packet = StrictJson.object().put("type", "state_snapshot").put("protocol_version", 1)
                    .put("snapshot_id", "software:1").put("revision", 1);
            var state = packet.putObject("state").put("date_raw", 53144328).put("paused", true).put("map_ready", true).put("speed", 1);
            state.putObject("played_character").put("character_id", 73).put("alive", true);
            byte[] snapshot = NativeWire.packet(StrictJson.canonical(packet));
            packets.add(snapshot);
            packets.add(snapshot.clone());
        }

        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) throws IOException {
            if (packets.isEmpty()) throw new IOException("no additional software snapshot");
            return packets.removeFirst();
        }
        @Override public void writePacket(byte[] packet, Instant deadline) { fail("no Native command is part of this memo test"); }
        @Override public void close() { }
    }
}
