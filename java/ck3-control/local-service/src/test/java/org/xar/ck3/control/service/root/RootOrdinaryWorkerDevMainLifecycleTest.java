package org.xar.ck3.control.service.root;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.*;

import io.quarkus.runtime.LaunchMode;
import io.quarkus.runtime.ShutdownEvent;
import io.quarkus.runtime.StartupEvent;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.io.PrintStream;
import java.nio.channels.FileChannel;
import java.nio.channels.OverlappingFileLockException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;
import org.eclipse.microprofile.config.spi.ConfigProviderResolver;
import org.eclipse.microprofile.config.spi.ConfigSource;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.CleanupMode;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual adapter lifecycle, with the real worker failing before any Game or Native setup. */
@Timeout(25)
public class RootOrdinaryWorkerDevMainLifecycleTest {
    @TempDir(cleanup = CleanupMode.NEVER) Path temp;
    private enum Stop { OWN, EXISTING_OPERATOR, REPLACED_BY_OPERATOR }
    private static final byte[] OPERATOR = "operator request, retained exactly\n".getBytes(UTF_8);

    @Test void failedWorkerRemovesItsStopOnlyAfterDelegateFinishes() throws Exception {
        exercise(Stop.OWN);
    }

    @Test void failedWorkerPreservesExistingOperatorStop() throws Exception {
        exercise(Stop.EXISTING_OPERATOR);
    }

    @Test void failedWorkerPreservesOperatorReplacementOfItsStop() throws Exception {
        exercise(Stop.REPLACED_BY_OPERATOR);
    }

    private void exercise(Stop scenario) throws Exception {
        Path configuration = configuration();
        Path state = temp.resolve("state");
        Path marker = state.resolve("worker-stop.request");
        Files.createDirectories(state);
        if (scenario == Stop.EXISTING_OPERATOR) Files.write(marker, OPERATOR);
        var adapter = new RootOrdinaryWorkerDevMain();
        adapter.arguments = new String[]{temp.resolve("missing-owner.json").toString(), configuration.toString()};

        // Bind a test-local Config to a distinct TCCL; do not replace the host's global config.
        ClassLoader previousLoader = Thread.currentThread().getContextClassLoader();
        ClassLoader testLoader = new ClassLoader(previousLoader) { };
        var resolver = ConfigProviderResolver.instance();
        var config = resolver.getBuilder().withSources(new EnabledSource()).build();
        resolver.registerConfig(config, testLoader);
        LaunchMode previousMode = LaunchMode.current();
        PrintStream previousOut = System.out;
        PrintStream previousErr = System.err;
        var gate = new StartedGate();
        var errors = new ByteArrayOutputStream();
        var capturedErrors = new PrintStream(errors, true, UTF_8);
        var stopped = new CompletableFuture<Void>();
        Thread shutdown = null;
        try {
            Thread.currentThread().setContextClassLoader(testLoader);
            LaunchMode.set(LaunchMode.DEVELOPMENT);
            System.setOut(gate);
            System.setErr(capturedErrors);
            adapter.start(new StartupEvent());
            assertTrue(gate.started.await(5, TimeUnit.SECONDS), "real DELEGATE_STARTED required");
            assertNotNull(gate.worker);
            shutdown = Thread.ofPlatform().name("test-dev-shutdown").start(() -> {
                try { adapter.shutdown(new ShutdownEvent()); stopped.complete(null); }
                catch (Throwable failure) { stopped.completeExceptionally(failure); }
            });
            Thread observer = shutdown;
            await(() -> observer.getState() == Thread.State.TIMED_WAITING, "shutdown must await real delegate");
            assertFalse(stopped.isDone(), "shutdown cannot complete before delegate returns");
            assertTrue(gate.worker.isAlive());
            assertEquals(1, gate.release.getCount(), "delegate remains paused at its real start observation");
            byte[] during = Files.readAllBytes(marker);
            if (scenario == Stop.EXISTING_OPERATOR) assertArrayEquals(OPERATOR, during);
            else assertTrue(new String(during, UTF_8).matches("ordinary-worker-dev [0-9a-f-]{36}\\n"));
            assertHeld(state.resolve("ordinary-worker-dev.lock"));
            Files.write(temp.resolve("marker-before-worker-return.bin"), during);
            if (scenario == Stop.REPLACED_BY_OPERATOR) Files.write(marker, OPERATOR);

            gate.release.countDown();
            gate.worker.join(5000);
            assertFalse(gate.worker.isAlive(), "real business thread must terminate");
            stopped.get(5, TimeUnit.SECONDS);
            shutdown.join(5000);
            assertFalse(shutdown.isAlive());
            assertNull(gate.failure.get(), "test output barrier must not time out");
            if (scenario == Stop.OWN) assertFalse(Files.exists(marker), "failed delegate must remove its own marker");
            else assertArrayEquals(OPERATOR, Files.readAllBytes(marker), "operator bytes must survive failure cleanup");
            try (FileChannel probe = FileChannel.open(state.resolve("ordinary-worker-dev.lock"), StandardOpenOption.WRITE);
                    var released = probe.tryLock()) {
                assertNotNull(released, "delegate exit must release ownership");
            }
            List<String> lifecycle = List.copyOf(gate.lines);
            assertEquals(2, lifecycle.size());
            var completed = StrictJson.parse(lifecycle.get(1).getBytes(UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
            assertEquals("DELEGATE_COMPLETED", completed.path("status").textValue());
            assertEquals("java.nio.file.NoSuchFileException", completed.path("failure_type").textValue());
            assertTrue(completed.path("exit_code").isNull(), "thrown real worker must retain non-clean outcome");
            assertTrue(errors.toString(UTF_8).contains("RootOrdinaryWorkerMain.run"));
            assertTrue(errors.toString(UTF_8).contains("retained worker failure/exit 4"));
            assertTrue(errors.toString(UTF_8).contains("no clean restart was claimed"));
            assertFalse(Files.exists(state.resolve("worker-restart-ticket.json")), "cleanup is not a clean ticket");
        } finally {
            gate.release.countDown();
            if (gate.worker != null) gate.worker.join(5000);
            if (shutdown != null) shutdown.join(5000);
            System.setOut(previousOut);
            System.setErr(previousErr);
            LaunchMode.set(previousMode);
            Thread.currentThread().setContextClassLoader(previousLoader);
            resolver.releaseConfig(config);
            Files.writeString(temp.resolve("lifecycle.stdout"), String.join("\n", gate.lines), UTF_8);
            Files.write(temp.resolve("lifecycle.stderr"), errors.toByteArray());
            gate.close();
            capturedErrors.close();
        }
    }

    private static void assertHeld(Path path) throws Exception {
        try (FileChannel probe = FileChannel.open(path, StandardOpenOption.WRITE)) {
            try (var unexpected = probe.tryLock()) {
                fail("delegate still paused: ownership lock was available: " + unexpected);
            } catch (OverlappingFileLockException expected) {
                // The actual adapter still owns it in this JVM.
            }
        }
    }

    private static void await(BooleanSupplier condition, String detail) throws Exception {
        long end = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (!condition.getAsBoolean() && System.nanoTime() < end) Thread.sleep(5);
        assertTrue(condition.getAsBoolean(), detail);
    }

    private Path configuration() throws Exception {
        Files.writeString(temp.resolve("initial-policy.json"), """
            {"schema":"xar.java.initial-episode-policy/v1","succession_lifecycle":{"schema":"xar.ck3.succession-lifecycle-binding/v1","lifecycle":"ordinary_campaign_succession","pact_contract":"not_applicable_to_vanilla_configuration","source":"ordinary_vanilla_configuration","xar_enabled":null,"environment_sha256":null}}
            """, UTF_8);
        Path path = temp.resolve("configuration.json");
        Files.writeString(path, """
            {"schema":"xar.java-ordinary-runtime-configuration/v1","machine_id":"xenoamess-full-tower-eb9d2c1186","state_dir":"state","stock_game_root":"unused-stock","native_implementation":"unused-native","launch_plan_file":"unused-launch.json","initial_policy_file":"initial-policy.json","campaign_deadline_file":"unused-deadline.json","formal_war_budget":"unused-budget.json","formal_war_model":"unused-model.json","configured_build":{"version":"1.20.0.4","exe_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"},"authority_id":"isolated-dev-lifecycle-test","operation_timeout_ms":100,"batch_wall_ms":100}
            """, UTF_8);
        return path;
    }

    private static final class EnabledSource implements ConfigSource {
        private static final Map<String, String> VALUES = Map.of(
                "xar.worker.dev.enabled", "true", "quarkus.package.main-class", "ordinary-worker-dev");
        @Override public Map<String, String> getProperties() { return VALUES; }
        @Override public Set<String> getPropertyNames() { return VALUES.keySet(); }
        @Override public String getValue(String propertyName) { return VALUES.get(propertyName); }
        @Override public String getName() { return "isolated-dev-lifecycle-test"; }
    }

    private static final class StartedGate extends PrintStream {
        private final CountDownLatch started = new CountDownLatch(1);
        private final CountDownLatch release = new CountDownLatch(1);
        private final ConcurrentLinkedQueue<String> lines = new ConcurrentLinkedQueue<>();
        private final AtomicReference<Throwable> failure = new AtomicReference<>();
        private volatile Thread worker;
        private StartedGate() { super(OutputStream.nullOutputStream(), true, UTF_8); }
        @Override public void println(String line) {
            lines.add(line);
            if (!line.contains("\"status\":\"DELEGATE_STARTED\"")) return;
            worker = Thread.currentThread();
            started.countDown();
            try {
                if (!release.await(15, TimeUnit.SECONDS)) failure.set(new IllegalStateException("output barrier timed out"));
            } catch (InterruptedException interrupted) {
                failure.set(interrupted);
                Thread.currentThread().interrupt();
            }
        }
    }
}
