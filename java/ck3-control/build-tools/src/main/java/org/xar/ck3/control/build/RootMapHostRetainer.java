package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

/** Holds the existing finite Map software host while Root independently observes a real native frame. */
public final class RootMapHostRetainer {
    private RootMapHostRetainer() { }
    public record Plan(String schema, String machineId, ControlBuild.FileRef captureRef, MapVerticalSoftwareHost.Config host,
            MapAdmissionCi.Config consumers, ControlBuild.FileRef directFixture,
            ControlBuild.FileRef projectionFixture, Path readyPath, Instant deadline) {
        public Plan {
            if (!"xar.root-map-software-host-retainer/v1".equals(schema)) throw new IllegalArgumentException("Map retainer schema");
            Objects.requireNonNull(machineId); Objects.requireNonNull(captureRef); Objects.requireNonNull(host); Objects.requireNonNull(consumers);
            Objects.requireNonNull(directFixture); Objects.requireNonNull(projectionFixture); Objects.requireNonNull(deadline);
            if (readyPath == null || !readyPath.isAbsolute() || !readyPath.normalize().equals(readyPath))
                throw new IllegalArgumentException("Exact absolute create-only readiness path required");
        }
    }
    public record Ready(String schema, String machineId, String purpose, String observedAtUtc,
            String deadlineUtc, WindowsJobProcess.ProcessIdentity identity,
            ControlBuild.FileRef runningRef, ControlBuild.FileRef programRef,
            ControlBuild.FileRef captureRef, ControlBuild.FileRef softwareProofRef) { }

    /** stdin STOP followed by LF closes this same host. EOF leaves the finite deadline in force. */
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("usage: RootMapHostRetainer plan-path bytes sha256");
        run(new ControlBuild.FileRef(args[0], Long.parseLong(args[1]), args[2]), System.in);
    }
    public static void run(ControlBuild.FileRef planRef, InputStream control) throws IOException, InterruptedException {
        planRef.verify();
        if (planRef.bytes() < 1 || planRef.bytes() > 1_048_576) throw new IOException("Bounded exact Map host plan required");
        Plan plan = RootNativePlanJson.mapper().readValue(Files.readAllBytes(Path.of(planRef.path())), Plan.class);
        planRef.verify(); Objects.requireNonNull(control);
        if (!WindowsJobProcess.currentMachineId().equals(plan.machineId()) || !Instant.now().isBefore(plan.deadline())
                || Duration.between(Instant.now(), plan.deadline()).compareTo(Duration.ofMinutes(15)) > 0
                || plan.deadline().isAfter(plan.host().service().leaseDeadline()))
            throw new IOException("Current-machine finite Map host deadline required");
        SharedSourceFiles.plainAncestors(plan.readyPath().getParent());
        if (Files.exists(plan.readyPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS)) throw new IOException("Readiness output already exists");
        AtomicBoolean stop = new AtomicBoolean();
        Thread reader = new Thread(() -> {
            try {
                byte[] expected = "STOP\n".getBytes(StandardCharsets.US_ASCII);
                for (byte value : expected) { int actual = control.read(); if (actual < 0 || actual != value) return; }
                stop.set(true);
            } catch (IOException ignored) { /* Only a complete STOP command can shorten this finite lease. */ }
        }, "root-map-host-stop");
        reader.setDaemon(true);
        try (DelegatedGuard guard = DelegatedGuard.begin(plan.captureRef(), plan.readyPath().getParent());
                MapVerticalSoftwareHost.Session session = MapVerticalSoftwareHost.open(plan.host())) {
            if (!session.captureRef().equals(guard.captureRef())) throw new IOException("Retained host capture differs from full delegated source guard");
            var direct = session.post(MapAdmissionServiceOwner.COMPOSE_PATH, plan.directFixture());
            var projection = session.post("/v1/projections/call", plan.projectionFixture());
            var qualified = session.qualify(plan.consumers(), direct, projection);
            qualified.verifyCurrent(); session.requireCurrent(); planRef.verify();
            Ready ready = new Ready("xar.root-map-software-host-running/v1", plan.machineId(),
                    "MAP_VERTICAL_SOFTWARE_ONLY", Instant.now().toString(), plan.deadline().toString(),
                    session.identity(), session.runningRef(), session.programRef(), session.captureRef(), qualified.proofRef());
            byte[] raw = RootNativePlanJson.mapper().writeValueAsBytes(ready);
            Files.write(plan.readyPath(), raw, StandardOpenOption.CREATE_NEW);
            System.out.println(new String(raw, StandardCharsets.UTF_8)); System.out.flush(); reader.start();
            while (!stop.get() && Instant.now().isBefore(plan.deadline())) {
                session.requireCurrent(); qualified.verifyCurrent(); planRef.verify();
                Thread.sleep(Math.max(1, Math.min(1000, Duration.between(Instant.now(), plan.deadline()).toMillis())));
            }
        }
    }
    private record Counts(int sources, int compiled, int deployment, int runtime, int unique) { }
    private record Observation(String schema, String machineId, String observedAtUtc, String phase,
            ControlBuild.FileRef captureRef, Counts counts, List<SharedSourceFiles.Witness> witnesses) { }
    private record FailedPost(String machineId, String observedAtUtc, ControlBuild.FileRef captureRef,
            Counts counts, int checked, String error) { }
    record DelegatedGuard(ControlBuild.FileRef captureRef, ControlBuild.CaptureBuildReceipt receipt,
            Path output, Counts counts, List<SharedSourceFiles.Witness> witnesses) implements AutoCloseable {
        static DelegatedGuard begin(ControlBuild.FileRef ref, Path output) throws java.io.IOException {
            var receipt = ControlBuild.verifiedCompletedCaptureReceipt(ref);
            var observed = observeSources(List.of(receipt.sourcePins(), receipt.compiledSourcePins(),
                    receipt.completeDeployment(), receipt.producerRuntimePins(), List.of(ref, receipt.testCompilationRef())));
            var counts = new Counts(receipt.sourcePins().size(), receipt.compiledSourcePins().size(),
                    receipt.completeDeployment().size(), receipt.producerRuntimePins().size(), observed.size());
            var guard = new DelegatedGuard(ref, receipt, output, counts, observed);
            guard.persist("PRE", observed);
            return guard;
        }
        private void persist(String phase, List<SharedSourceFiles.Witness> observed) throws java.io.IOException {
            write(output.resolve("delegated-manifest-" + phase.toLowerCase(java.util.Locale.ROOT) + ".json"),
                    ControlBuild.strictMapper().writeValueAsBytes(new Observation("xar.map-delegated-manifest/v1",
                            WindowsJobProcess.currentMachineId(), Instant.now().toString(), phase, captureRef, counts, observed)));
        }
        @Override public void close() throws java.io.IOException {
            int checked = 0;
            try {
                if (!receipt.equals(ControlBuild.verifiedCompletedCaptureReceipt(captureRef))) throw new java.io.IOException("complete capture changed");
                var after = new java.util.ArrayList<SharedSourceFiles.Witness>();
                for (var witness : witnesses) {
                    SharedSourceFiles.assertUnchanged(witness);
                    after.add(SharedSourceFiles.observe(Path.of(witness.source().path())));
                    checked++;
                }
                persist("POST", List.copyOf(after));
            } catch (java.io.IOException | RuntimeException failure) {
                try { write(output.resolve("delegated-manifest-post-failure.json"),
                        ControlBuild.strictMapper().writeValueAsBytes(new FailedPost(WindowsJobProcess.currentMachineId(),
                                Instant.now().toString(), captureRef, counts, checked, failure.toString()))); }
                catch (java.io.IOException | RuntimeException recording) { failure.addSuppressed(recording); }
                throw failure;
            }
        }
    }
    static List<SharedSourceFiles.Witness> observeSources(List<List<ControlBuild.FileRef>> groups) throws java.io.IOException {
        var refs = new java.util.LinkedHashMap<Path, ControlBuild.FileRef>();
        for (var group : groups) for (var ref : group) {
            Path path = Path.of(ref.path()).toAbsolutePath().normalize();
            var previous = refs.putIfAbsent(path, ref);
            if (previous != null && !previous.equals(ref)) throw new java.io.IOException("conflicting exact manifest path");
        }
        var observed = new java.util.ArrayList<SharedSourceFiles.Witness>();
        for (var entry : refs.entrySet()) {
            var witness = SharedSourceFiles.observe(entry.getKey());
            if (!entry.getValue().equals(witness.source())) throw new java.io.IOException("manifest/native witness exact source differs");
            observed.add(witness);
        }
        return List.copyOf(observed);
    }
    private static ControlBuild.FileRef write(Path path, byte[] bytes) throws IOException {
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
        return ControlBuild.FileRef.measure(path);
    }
}
