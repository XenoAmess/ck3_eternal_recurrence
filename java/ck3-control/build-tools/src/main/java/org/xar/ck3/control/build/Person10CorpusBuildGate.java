package org.xar.ck3.control.build;

import java.io.Closeable;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.channels.OverlappingFileLockException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Separate fixture authority, using the shared storage-policy calculator and native allocation observer. */
final class Person10CorpusBuildGate implements Closeable {
    private static final long RECEIPT_RESERVE = 16L << 20;
    private final Person10NativeCorpusBuild.Request request;
    private final ControlBuild.FileRef requestPin;
    private final ControlBuild.CapacityRelease release;
    private final List<Path> roots;
    private final FileChannel channel;
    private final FileLock lock;
    private boolean closed;
    private Person10CorpusBuildGate(Person10NativeCorpusBuild.Request request, ControlBuild.FileRef requestPin,
            ControlBuild.CapacityRelease release, List<Path> roots, FileChannel channel, FileLock lock) {
        this.request = request; this.requestPin = requestPin; this.release = release;
        this.roots = List.copyOf(roots); this.channel = channel; this.lock = lock;
    }
    static Person10CorpusBuildGate open(Person10NativeCorpusBuild.Request request, ControlBuild.FileRef requestPin,
            Path sourceRoot) throws IOException {
        requestPin.verify(); request.limits().capacityEvidence().verify();
        var release = ControlBuild.strictMapper().readValue(NativeBridgeBuild.read(request.limits().capacityEvidence(), 131072), ControlBuild.CapacityRelease.class);
        validate(request, requestPin, release, sourceRoot, Instant.now());
        List<Path> roots = roots(release);
        Path parent = request.outputRoot().getParent(); SharedSourceFiles.plainAncestors(parent);
        Person10NativeCorpusBuild.require(Files.isDirectory(parent, LinkOption.NOFOLLOW_LINKS), "Pre-admitted output parent required");
        // The new fixture lock is independent of the Bridge/ledger writer. It cannot confer those authorities.
        Path path = parent.resolve("ROOT-PERSON10-CORPUS.lock"); SharedSourceFiles.plainAncestors(path);
        Person10NativeCorpusBuild.require(roots.stream().anyMatch(path::startsWith), "Fixture OS lock parent needs explicit output admission");
        FileChannel channel = FileChannel.open(path, StandardOpenOption.CREATE, StandardOpenOption.WRITE); FileLock lock = null;
        try {
            try { lock = channel.tryLock(); }
            catch (OverlappingFileLockException busy) { throw new IOException("Person10 producer already has a live owner", busy); }
            Person10NativeCorpusBuild.require(lock != null, "Person10 producer already has a live owner");
            var gate = new Person10CorpusBuildGate(request, requestPin, release, roots, channel, lock);
            gate.check(); return gate;
        } catch (IOException | RuntimeException failure) {
            if (lock != null) try { lock.release(); } catch (IOException close) { failure.addSuppressed(close); }
            try { channel.close(); } catch (IOException close) { failure.addSuppressed(close); }
            throw failure;
        }
    }
    static void validate(Person10NativeCorpusBuild.Request request, ControlBuild.FileRef requestPin,
            ControlBuild.CapacityRelease release, Path sourceRoot, Instant now) throws IOException {
        Objects.requireNonNull(requestPin); var limits = request.limits();
        Instant opened = Instant.parse(release.observedAtUtc()), review = Instant.parse(release.reviewAtUtc());
        Person10NativeCorpusBuild.require(release.machineId().equals(request.machineId()) && release.ownerTask().equals(limits.ownerTask())
                && !now.isBefore(opened) && now.isBefore(limits.deadline()) && !limits.deadline().isAfter(review)
                && limits.memoryLimitBytes() <= release.memoryLimitBytes()
                && limits.outputAllocationLimitBytes() <= release.parts().getOrDefault("artifacts", 0L), "Independent current fixture capacity/owner/window required");
        List<Path> roots = roots(release);
        Person10NativeCorpusBuild.require(request.temporaryRoot().startsWith(Path.of(release.temporaryRoot())), "Child native TMP escaped admitted ENTIRETMP");
        for (Path path : List.of(request.buildRoot(), request.outputRoot(), request.temporaryRoot(), Path.of(release.temporaryRoot()))) {
            Person10NativeCorpusBuild.require(roots.stream().anyMatch(path::startsWith), "Native fixture root is not independently admitted");
            volume(release, path);
        }
        for (Path root : roots) {
            Person10NativeCorpusBuild.require(!Person10NativeCorpusBuild.overlap(root, sourceRoot), "Mutable fixture scope overlaps frozen source");
            volume(release, root);
        }
        release.policyRef().verify(); var policy = CiBootstrap.readPolicy(NativeBridgeBuild.read(release.policyRef(), 131072));
        for (var entry : release.volumes().entrySet()) {
            var value = entry.getValue(); var override = release.quotaOverrides().get(entry.getKey());
            if (override != null) {
                Person10NativeCorpusBuild.require(override.task().equals(release.ownerTask())
                        && !Instant.parse(override.reviewAtUtc()).isAfter(review), "Fixture quota override owner/window differs");
                new ControlBuild.FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()).verify();
            }
            Person10NativeCorpusBuild.require(value.equals(CiBootstrap.calculate(policy, value.totalVolumeBytes(), value.availableBytes(),
                    value.thisWritePeak(), value.otherUnspentReservations(), value.systemGrowthReserve(), value.currentProjectUsageConservativeUpper(),
                    override, opened, review)), "Fixture release does not follow the common storage policy");
            if (roots.stream().anyMatch(path -> path.getRoot().equals(Path.of(entry.getKey()))))
                Person10NativeCorpusBuild.require(value.thisWritePeak() >= limits.outputAllocationLimitBytes(), "Volume peak cannot cover the fixture cap");
        }
    }
    synchronized void check() throws IOException {
        Person10NativeCorpusBuild.require(!closed && channel.isOpen() && lock.isValid(), "Fixture OS reservation lost");
        requestPin.verify(); request.limits().capacityEvidence().verify(); release.policyRef().verify();
        Person10NativeCorpusBuild.require(WindowsJobProcess.currentMachineId().equals(request.machineId())
                && Instant.now().isBefore(request.limits().deadline()), "Fixture machine/window changed");
        Path temporary = Person10NativeCorpusBuild.absolute(Path.of(release.temporaryRoot()));
        for (String key : List.of("java.io.tmpdir", "jna.tmpdir")) {
            String value = System.getProperty(key);
            Person10NativeCorpusBuild.require(value != null && Path.of(value).isAbsolute()
                    && Path.of(value).normalize().startsWith(temporary), "Native JVM TMP escaped admitted ENTIRETMP");
            SharedSourceFiles.plainAncestors(Path.of(value));
        }
        for (var entry : release.volumes().entrySet())
            Person10NativeCorpusBuild.require(Files.getFileStore(Path.of(entry.getKey())).getUsableSpace() >= entry.getValue().requiredFree(), "Fixture free-space guard failed");
        long actual = NativeBridgeRootGate.allocation(roots, request.limits().deadline());
        Person10NativeCorpusBuild.require(Math.addExact(actual, RECEIPT_RESERVE) <= request.limits().outputAllocationLimitBytes(), "Native fixture allocation/TMP plus terminal reserve exceeded");
    }
    private static List<Path> roots(ControlBuild.CapacityRelease release) throws IOException {
        List<Path> result = new ArrayList<>();
        for (String value : release.approvedOutputRoots()) {
            Path path = Person10NativeCorpusBuild.absolute(Path.of(value));
            Person10NativeCorpusBuild.require(!path.equals(path.getRoot()), "Whole-volume fixture scope forbidden");
            if (!result.contains(path)) result.add(path);
        }
        return result.stream().filter(p -> result.stream().noneMatch(q -> !p.equals(q) && p.startsWith(q))).toList();
    }
    private static void volume(ControlBuild.CapacityRelease release, Path path) throws IOException {
        Person10NativeCorpusBuild.require(release.volumes().keySet().stream().map(Path::of).anyMatch(v -> v.equals(path.getRoot())), "Explicit fixture output volume budget required");
    }
    @Override public synchronized void close() throws IOException {
        if (closed) return; IOException failure = null;
        try { check(); } catch (IOException error) { failure = error; }
        closed = true;
        try { lock.release(); } catch (IOException error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
        try { channel.close(); } catch (IOException error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
        if (failure != null) throw failure;
    }
}
