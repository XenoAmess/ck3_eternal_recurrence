package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaOwnedFocusTestSupport;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Actual shared production branches, public wire DATA and software Win32 IO only.
 * This test grants no Managed session, private Native issuer, Game or focus permission. */
final class RootBootstrapOwnedFocusTest {
    private static final Instant NOW = Instant.parse("2026-11-03T00:00:00Z");
    private static final Instant DEADLINE = NOW.plusSeconds(20);
    private static final GameGeneration GAME = new GameGeneration(1234,
            new PythonOnlyUInt64(new BigInteger("9007199254740993")));

    @Test void firstPartialReturnsTheSameRetainedAckWithoutFocus() throws Exception {
        for (boolean mapReady : List.of(false, true)) {
            var ack = ack("first", partial(mapReady));
            var reads = new AtomicInteger(); var focuses = new AtomicInteger();
            var actual = RootNativeFreshStartup.observeBootstrapCore(deadline -> {
                assertTrue(deadline.isAfter(NOW)); assertFalse(deadline.isAfter(DEADLINE));
                reads.incrementAndGet(); return ack;
            }, deadline -> focuses.incrementAndGet(), clock(), DEADLINE);
            assertSame(ack, actual); assertEquals(1, reads.get()); assertEquals(0, focuses.get());
        }
    }

    @Test void onlyTypedUnavailableGetsOneFocusAndOneFreshRead() throws Exception {
        for (boolean observed : List.of(false, true)) {
            var unavailable = ack("first", new CoreFrame.Unavailable(observed, "application_main_not_ready"));
            var ready = ack("second", partial(true));
            var events = new ArrayList<String>(); var reads = new AtomicInteger();
            var actual = RootNativeFreshStartup.observeBootstrapCore(deadline -> {
                assertFalse(deadline.isAfter(DEADLINE)); events.add("read");
                return switch (reads.incrementAndGet()) {
                    case 1 -> unavailable;
                    case 2 -> ready;
                    default -> throw new AssertionError("third core read forbidden");
                };
            }, deadline -> { assertFalse(deadline.isAfter(DEADLINE)); events.add("focus"); }, clock(), DEADLINE);
            assertSame(ready, actual); assertEquals(List.of("read", "focus", "read"), events);
        }
    }

    @Test void invalidNegativeAndUnknownResultsDoNotAuthorizeFocus() throws Exception {
        var ready = ack("negative", partial(true));
        var missing = new NativeActionPort.AckReceived(ready.requestId(), true, Optional.empty(),
                ready.originalFrame(), ready.originalPacket(), ready.outbound());
        List<NativeActionPort.DispatchOutcome> failures = List.of(
                new NativeActionPort.RejectedBeforeDispatch("rejected", new NativeActionPort.ZeroDispatchProof(
                        NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0, "software refused", Optional.empty())),
                new NativeActionPort.Unknown("unknown", "software missing result",
                        NativeWire.execute("unknown", CoreFrame.STEP, BigInteger.ZERO, "{}".getBytes(StandardCharsets.UTF_8)), Optional.empty()),
                wireAck("negative", false, CoreFramePublicCodec.encode(partial(true))), missing);
        for (var failure : failures) {
            var reads = new AtomicInteger(); var focuses = new AtomicInteger();
            var expiredAfterRead = new ControlledClock(NOW);
            // The original non-success polling delay is retained. Expire our controlled clock
            // after this one DATA read so its existing one-second delay cannot form a loop.
            assertThrows(IOException.class, () -> RootNativeFreshStartup.observeBootstrapCore(deadline -> {
                reads.incrementAndGet(); expiredAfterRead.set(DEADLINE); return failure;
            }, deadline -> focuses.incrementAndGet(), expiredAfterRead, DEADLINE));
            assertEquals(1, reads.get()); assertEquals(0, focuses.get());
        }
        var malformed = wireAck("malformed", true, raw("{}"));
        var malformedFocuses = new AtomicInteger();
        var returned = RootNativeFreshStartup.observeBootstrapCore(deadline -> malformed,
                deadline -> malformedFocuses.incrementAndGet(), clock(), DEADLINE);
        assertSame(malformed, returned); assertEquals(0, malformedFocuses.get());
        assertThrows(IOException.class, () -> RootNativeFreshStartup.decodeCore(returned.originalResultToken().orElseThrow()));
    }

    @Test void readFocusAndSecondResultFailuresNeverLoopOrReplay() throws Exception {
        var readFailure = new IOException("software read failure");
        var reads = new AtomicInteger(); var focuses = new AtomicInteger();
        assertSame(readFailure, assertThrows(IOException.class, () -> RootNativeFreshStartup.observeBootstrapCore(deadline -> {
            reads.incrementAndGet(); throw readFailure;
        }, deadline -> focuses.incrementAndGet(), clock(), DEADLINE)));
        assertEquals(1, reads.get()); assertEquals(0, focuses.get());

        var interrupted = new InterruptedException("software interrupted");
        assertSame(interrupted, assertThrows(InterruptedException.class,
                () -> RootNativeFreshStartup.observeBootstrapCore(deadline -> { throw interrupted; },
                        deadline -> { throw new AssertionError("focus on interrupt"); }, clock(), DEADLINE)));

        var unavailable = ack("first", new CoreFrame.Unavailable(false, "unavailable"));
        var focusFailure = new IOException("software focus result uncertain");
        var focusReads = new AtomicInteger(); var failedFocuses = new AtomicInteger();
        assertSame(focusFailure, assertThrows(IOException.class, () -> RootNativeFreshStartup.observeBootstrapCore(deadline -> {
            focusReads.incrementAndGet(); return unavailable;
        }, deadline -> { failedFocuses.incrementAndGet(); throw focusFailure; }, clock(), DEADLINE)));
        assertEquals(1, focusReads.get()); assertEquals(1, failedFocuses.get());

        for (var second : List.of(ack("second", new CoreFrame.Unavailable(true, "still_unavailable")),
                wireAck("second", true, raw("{}")))) {
            var secondReads = new AtomicInteger(); var secondFocuses = new AtomicInteger();
            var returned = RootNativeFreshStartup.observeBootstrapCore(deadline -> {
                int index = secondReads.incrementAndGet();
                if (index > 2) throw new AssertionError("third core read forbidden");
                return index == 1 ? unavailable : second;
            }, deadline -> secondFocuses.incrementAndGet(), clock(), DEADLINE);
            assertSame(second, returned);
            if (returned.originalResultToken().orElseThrow().equals(raw("{}")))
                assertThrows(IOException.class, () -> RootNativeFreshStartup.decodeCore(returned.originalResultToken().orElseThrow()));
            else assertInstanceOf(CoreFrame.Unavailable.class,
                    RootNativeFreshStartup.decodeCore(returned.originalResultToken().orElseThrow()));
            assertEquals(2, secondReads.get()); assertEquals(1, secondFocuses.get());
        }
        var secondReadFailure = new IOException("software second read failed");
        var secondReads = new AtomicInteger(); var secondFocuses = new AtomicInteger();
        assertSame(secondReadFailure, assertThrows(IOException.class, () -> RootNativeFreshStartup.observeBootstrapCore(deadline -> {
            if (secondReads.incrementAndGet() == 1) return unavailable;
            throw secondReadFailure;
        }, deadline -> secondFocuses.incrementAndGet(), clock(), DEADLINE)));
        assertEquals(2, secondReads.get()); assertEquals(1, secondFocuses.get());
    }

    @Test void originalDeadlineCannotBeExtendedAcrossFocusOrRead() throws Exception {
        var expiredReads = new AtomicInteger(); var expiredFocuses = new AtomicInteger();
        assertThrows(IOException.class, () -> RootNativeFreshStartup.observeBootstrapCore(deadline -> {
            expiredReads.incrementAndGet(); throw new AssertionError("expired read");
        }, deadline -> expiredFocuses.incrementAndGet(), clock(), NOW));
        assertEquals(0, expiredReads.get()); assertEquals(0, expiredFocuses.get());

        var unavailable = ack("first", new CoreFrame.Unavailable(false, "unavailable"));
        var afterRead = new ControlledClock(NOW);
        var readCount = new AtomicInteger(); var focusCount = new AtomicInteger();
        assertThrows(IOException.class, () -> RootNativeFreshStartup.observeBootstrapCore(deadline -> {
            readCount.incrementAndGet(); afterRead.set(DEADLINE); return unavailable;
        }, deadline -> focusCount.incrementAndGet(), afterRead, DEADLINE));
        assertEquals(1, readCount.get()); assertEquals(0, focusCount.get());

        var afterFocus = new ControlledClock(NOW);
        var focusReads = new AtomicInteger(); var focuses = new AtomicInteger();
        assertThrows(IOException.class, () -> RootNativeFreshStartup.observeBootstrapCore(deadline -> {
            focusReads.incrementAndGet(); return unavailable;
        }, deadline -> { focuses.incrementAndGet(); afterFocus.set(DEADLINE); }, afterFocus, DEADLINE));
        assertEquals(1, focusReads.get()); assertEquals(1, focuses.get());
    }

    @Test void sharedWindowFocusUsesOnlyTheBoundedForegroundOperations() throws Exception {
        for (var script : List.of(CoaOwnedFocusTestSupport.Script.FOREGROUND, CoaOwnedFocusTestSupport.Script.DIRECT,
                CoaOwnedFocusTestSupport.Script.WINDOW_DRIFT)) {
            var harness = CoaOwnedFocusTestSupport.create(GAME, script, clock());
            var result = CoaOwnedFocusTestSupport.focus(harness.capture(), DEADLINE);
            assertEquals(GAME, result.game());
            assertEquals("9007199254740993", result.window().hwnd());
            assertEquals(0, harness.captures().get()); assertTrue(harness.guards().get() >= 2);
            assertTrue(harness.show().get() <= 1); assertTrue(harness.bring().get() <= 1);
            assertTrue(harness.foreground().get() <= 1); assertTrue(harness.writes() <= 3);
            if (script == CoaOwnedFocusTestSupport.Script.FOREGROUND) assertEquals(0, harness.writes());
            else assertEquals(1, harness.foreground().get());
        }
    }

    @Test void sharedWindowFocusRejectsAmbiguityDriftFailureAndExpiryWithoutCapture() throws Exception {
        for (var script : List.of(CoaOwnedFocusTestSupport.Script.REMAINS_FOREIGN,
                CoaOwnedFocusTestSupport.Script.AMBIGUOUS,
                CoaOwnedFocusTestSupport.Script.GUARD_AFTER_WRITE)) {
            var harness = CoaOwnedFocusTestSupport.create(GAME, script, clock());
            if (script == CoaOwnedFocusTestSupport.Script.AMBIGUOUS)
                assertThrows(IllegalArgumentException.class, () -> CoaOwnedFocusTestSupport.focus(harness.capture(), DEADLINE));
            else assertThrows(IOException.class, () -> CoaOwnedFocusTestSupport.focus(harness.capture(), DEADLINE));
            assertEquals(0, harness.captures().get()); assertTrue(harness.writes() <= 3);
            assertTrue(harness.show().get() <= 1); assertTrue(harness.bring().get() <= 1);
            assertTrue(harness.foreground().get() <= 1);
            if (script == CoaOwnedFocusTestSupport.Script.AMBIGUOUS) assertEquals(0, harness.writes());
        }
        var expired = CoaOwnedFocusTestSupport.create(GAME, CoaOwnedFocusTestSupport.Script.DIRECT, clock());
        assertThrows(IOException.class, () -> CoaOwnedFocusTestSupport.focus(expired.capture(), NOW));
        assertEquals(0, expired.writes()); assertEquals(0, expired.captures().get());
    }

    private static CoreFrame.Partial partial(boolean mapReady) {
        return new CoreFrame.Partial(new CoreFrame.Prefix(53144328, 2, true, 7, mapReady, true, 7, true));
    }
    private static NativeActionPort.AckReceived ack(String id, CoreFrame frame) throws IOException {
        var result = wireAck(id, true, CoreFramePublicCodec.encode(frame));
        assertEquals(frame, CoreFramePublicCodec.decodeOutcome(result));
        return result;
    }
    private static NativeActionPort.AckReceived wireAck(String id, boolean ok, RawJson token) throws IOException {
        var payload = raw("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id
                + "\",\"ok\":" + ok + ",\"result\":" + new String(token.bytes(), StandardCharsets.UTF_8) + "}");
        byte[] packet = NativeWire.packet(payload.bytes());
        assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(packet));
        var outbound = new NativeActionPort.OutboundPacket(id,
                NativeWire.execute(id, CoreFrame.STEP, BigInteger.ZERO, "{}".getBytes(StandardCharsets.UTF_8)));
        return new NativeActionPort.AckReceived(id, ok, Optional.of(token), payload, packet, Optional.of(outbound));
    }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static Clock clock() { return Clock.fixed(NOW, ZoneOffset.UTC); }
    private static final class ControlledClock extends Clock {
        private Instant current;
        ControlledClock(Instant initial) { current = initial; }
        void set(Instant value) { current = value; }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) {
            if (!ZoneOffset.UTC.equals(zone)) throw new IllegalArgumentException("UTC software clock only");
            return this;
        }
        @Override public Instant instant() { return current; }
    }
}
