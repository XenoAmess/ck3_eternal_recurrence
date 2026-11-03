package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Actual shared loop/gate with software control DATA; no process, Managed issuer or terminal. */
final class GameSupervisorStopDeadlineRefusalTest {
    @TempDir Path temporary;

    @Test @Timeout(20)
    void admittedStopExpiresInSharedGateKeepsPollingAndOrdinaryFailureStillEscapes() throws Exception {
        Path root = temporary.toAbsolutePath();
        Path stopPath = root.resolve("stop-request.json");
        var identity = new WindowsJobProcess.ProcessIdentity(42, "134376718582643410",
                root.resolve("software-control-data.exe").toString());
        String session = "software-stop-refusal";
        var fixtureClosed = new AtomicBoolean();
        var stops = new AtomicInteger();
        var rejected = new AtomicInteger();
        var wantedFirst = new AtomicReference<Instant>();
        var wantedSecond = new AtomicReference<Instant>();
        var receivedFirst = new AtomicReference<Instant>();
        var receivedSecond = new AtomicReference<Instant>();
        var actualRefusal = new AtomicReference<ManagedGameSession.StopDeadlineRefused>();
        var entered = new CountDownLatch(1);
        var refused = new CountDownLatch(1);
        var continuedPolls = new CountDownLatch(3);
        IOException ordinaryFailure = new IOException("ordinary software stop failure");

        GameSupervisor.Owner owner = new GameSupervisor.Owner() {
            @Override public String sessionId() { return session; }
            @Override public WindowsJobProcess.ProcessIdentity identity() { return identity; }
            @Override public boolean running() {
                if (fixtureClosed.get()) throw new AssertionError("software fixture closed");
                if (actualRefusal.get() != null) continuedPolls.countDown();
                return true;
            }
            @Override public GameSupervisor.Terminal stop(Instant deadline, GameLifecycle.TerminalKind kind)
                    throws IOException, InterruptedException {
                if (kind != GameLifecycle.TerminalKind.OWNER_STOP)
                    throw new IOException("unexpected natural-exit callback in running software fixture");
                int call = stops.incrementAndGet();
                if (call == 1) {
                    receivedFirst.set(deadline);
                    if (!deadline.equals(wantedFirst.get()) || !Instant.now().isBefore(deadline))
                        throw new IOException("fixture did not enter with the original future STOP deadline");
                    entered.countDown();
                    long waitLimit = System.nanoTime() + Duration.ofSeconds(4).toNanos();
                    while (Instant.now().isBefore(deadline)) {
                        if (fixtureClosed.get()) throw new AssertionError("software fixture closed");
                        if (System.nanoTime() - waitLimit >= 0)
                            throw new IOException("fixture could not cross original deadline within bounded wait");
                        Thread.sleep(10);
                    }
                    try {
                        ManagedGameSession.requireStopDeadline(deadline);
                    } catch (ManagedGameSession.StopDeadlineRefused actual) {
                        actualRefusal.set(actual);
                        refused.countDown();
                        throw actual;
                    }
                    throw new IOException("expired shared production gate returned without refusal");
                }
                if (call == 2 && deadline.equals(wantedSecond.get())) {
                    receivedSecond.set(deadline);
                    throw ordinaryFailure;
                }
                throw new IOException("unchanged original STOP was dispatched again or its deadline changed");
            }
        };
        var result = new FutureTask<>(() -> GameSupervisor.awaitOwner(owner, stopPath,
                detail -> rejected.incrementAndGet()));
        Thread monitor = new Thread(result, "software-stop-refusal-loop");
        monitor.setDaemon(true);
        monitor.start();
        try {
            Instant originalDeadline = Instant.now().plusSeconds(2);
            wantedFirst.set(originalDeadline);
            var original = new GameSupervisorControl.StopRequest("first-stop", session, identity, originalDeadline);
            byte[] originalBytes = GameSupervisorControl.encodeStop(original);
            GameSupervisorControl.writeStop(stopPath, original);
            await(entered, result, Duration.ofSeconds(5));
            await(refused, result, Duration.ofSeconds(5));
            await(continuedPolls, result, Duration.ofSeconds(3));
            assertFalse(result.isDone(), "accurate pre-mutation refusal must keep the real owner loop polling");
            assertEquals(1, stops.get(), "unchanged refused STOP bytes must not be dispatched again");
            assertEquals(1, rejected.get());
            assertEquals(originalDeadline, receivedFirst.get());
            assertNotNull(actualRefusal.get());
            assertInstanceOf(IOException.class, actualRefusal.get().getCause());
            assertArrayEquals(originalBytes, Files.readAllBytes(stopPath));
            assertEquals(original, GameSupervisorControl.readStop(stopPath));

            Instant nextDeadline = Instant.now().plusSeconds(5);
            wantedSecond.set(nextDeadline);
            GameSupervisorControl.writeStop(stopPath,
                    new GameSupervisorControl.StopRequest("distinct-stop", session, identity, nextDeadline));
            ExecutionException failure = assertThrows(ExecutionException.class,
                    () -> result.get(5, TimeUnit.SECONDS));
            assertSame(ordinaryFailure, failure.getCause(), "ordinary stop IO must escape, not continue as refusal");
            assertEquals(2, stops.get());
            assertEquals(nextDeadline, receivedSecond.get());
        } finally {
            fixtureClosed.set(true);
            monitor.interrupt();
            monitor.join(2000);
            assertFalse(monitor.isAlive(), "bounded software fixture cleanup must finish the owner loop");
        }
    }

    private static void await(CountDownLatch latch, FutureTask<?> result, Duration timeout) throws Exception {
        long limit = System.nanoTime() + timeout.toNanos();
        while (latch.getCount() != 0) {
            if (result.isDone()) {
                result.get();
                fail("owner loop returned before the required callback or continued observation");
            }
            if (System.nanoTime() - limit >= 0) fail("bounded software fixture observation expired");
            latch.await(10, TimeUnit.MILLISECONDS);
        }
    }
}