package org.xar.ck3.control.build;

import java.io.Closeable;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.channels.OverlappingFileLockException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Root-owned, one-shot native stage reservation with actual native allocation and OS lock. */
public final class NativeBridgeRootGate implements NativeBridgeBuild.Gate, Closeable {
    private static final long RECEIPT_RESERVE_BYTES = 16L << 20;
    private static final int MAX_CENSUS_ENTRIES = 100000;
    public record Limits(String ownerTask, ControlBuild.FileRef capacityEvidence, Instant deadline,
            long memoryLimitBytes, long outputAllocationLimitBytes, int timeoutSeconds) {
        public Limits {
            if (ownerTask == null || !ownerTask.matches("/root(?:/[a-z0-9_-]+)*"))
                throw new IllegalArgumentException("Exact Root task owner required");
            Objects.requireNonNull(capacityEvidence); Objects.requireNonNull(deadline);
            if (memoryLimitBytes < (64L << 20) || memoryLimitBytes > (4L << 30)
                    || outputAllocationLimitBytes < RECEIPT_RESERVE_BYTES
                    || timeoutSeconds < 1 || timeoutSeconds > 7200)
                throw new IllegalArgumentException("Finite Root native stage limits required");
        }
    }
    private final NativeBridgeBuild.Request request;
    private final NativeBridgeBuild.Grant grant;
    private final ControlBuild.CapacityRelease release;
    private final List<Path> censusRoots;
    private final FileChannel channel;
    private final FileLock lock;
    private boolean acquired;
    private boolean closed;

    private NativeBridgeRootGate(NativeBridgeBuild.Request request, NativeBridgeBuild.Grant grant,
            ControlBuild.CapacityRelease release, List<Path> censusRoots, FileChannel channel, FileLock lock) {
        this.request = request; this.grant = grant; this.release = release;
        this.censusRoots = List.copyOf(censusRoots); this.channel = channel; this.lock = lock;
    }

    /** Opening checks the real release, volumes and allocation before creating the lock file. */
    public static NativeBridgeRootGate open(ControlBuild.FileRef requestRef, Limits limits) throws IOException {
        Objects.requireNonNull(limits);
        var request = NativeBridgeBuild.readRequest(requestRef);
        NativeBridgeBuild.requireCurrentRequest(request);
        var grant = new NativeBridgeBuild.Grant(request.machineId(), limits.ownerTask(), request.stage(), requestRef,
                limits.capacityEvidence(), limits.deadline(), limits.memoryLimitBytes(),
                limits.outputAllocationLimitBytes(), limits.timeoutSeconds());
        Instant now = Instant.now();
        var release = validateEnvelope(request, grant, now, now);
        NativeBridgeBuild.require(request.machineId().equals(WindowsJobProcess.currentMachineId()), "Root gate machine differs");
        NativeBridgeBuild.plainDirectory(request.scratchRoot());
        NativeBridgeBuild.require(Files.notExists(request.stageRoot(), LinkOption.NOFOLLOW_LINKS),
                "Stage already has an INTENT or unknown outcome; reconcile without replay");
        List<Path> scopes = censusRoots(release);
        verifyLivePaths(request, release);
        liveStorage(request, grant, release, scopes, true);
        Path lockPath = request.scratchRoot().resolve("ROOT-NATIVE-BUILD.lock");
        SharedSourceFiles.plainAncestors(lockPath);
        FileChannel channel = FileChannel.open(lockPath, StandardOpenOption.CREATE, StandardOpenOption.WRITE);
        FileLock lock = null;
        try {
            try { lock = channel.tryLock(); }
            catch (OverlappingFileLockException busy) { throw new IOException("Native package already has a live Root owner", busy); }
            NativeBridgeBuild.require(lock != null, "Native package already has a live OS lock owner");
            var gate = new NativeBridgeRootGate(request, grant, release, scopes, channel, lock);
            gate.guard(true); return gate;
        } catch (IOException | RuntimeException failure) {
            if (lock != null) try { lock.release(); } catch (IOException close) { failure.addSuppressed(close); }
            try { channel.close(); } catch (IOException close) { failure.addSuppressed(close); }
            throw failure;
        }
    }

    @Override public synchronized NativeBridgeBuild.Grant acquire(NativeBridgeBuild.Request selected,
            ControlBuild.FileRef exactRequest) throws IOException {
        NativeBridgeBuild.require(!acquired && request.equals(selected) && grant.requestRef().equals(exactRequest),
                "Root reservation is one-shot and bound to the exact request");
        guard(true); acquired = true; return grant;
    }
    @Override public synchronized void revalidate(NativeBridgeBuild.Grant selected, Path buildRoot,
            Path scratchRoot) throws IOException {
        NativeBridgeBuild.require(acquired && grant.equals(selected) && request.buildRoot().equals(buildRoot)
                && request.scratchRoot().equals(scratchRoot), "Root reservation or output roots differ");
        guard(true);
    }
    private void guard(boolean reserveReceipt) throws IOException {
        NativeBridgeBuild.require(!closed && lock.isValid() && channel.isOpen(), "Root native reservation was closed or lost");
        grant.requestRef().verify(); grant.capacityEvidence().verify(); release.policyRef().verify();
        NativeBridgeBuild.require(Instant.now().isBefore(grant.deadline()), "Root native reservation expired");
        verifyLivePaths(request, release); liveStorage(request, grant, release, censusRoots, reserveReceipt);
    }
    @Override public synchronized void close() throws IOException {
        if (closed) return;
        IOException failure = null;
        try { guard(false); } catch (IOException error) { failure = error; }
        closed = true;
        try { lock.release(); } catch (IOException error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
        try { channel.close(); } catch (IOException error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
        if (failure != null) throw failure;
    }

    /** Historical completion validation never renews this lease or issues a new reservation. */
    public static void verifyHistorical(NativeBridgeBuild.Request request, NativeBridgeBuild.Grant grant,
            Instant started, Instant observed) throws IOException {
        validateEnvelope(request, grant, started, observed);
        grant.requestRef().verify();
    }

    static ControlBuild.CapacityRelease validateEnvelope(NativeBridgeBuild.Request request,
            NativeBridgeBuild.Grant grant, Instant started, Instant observed) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(grant); Objects.requireNonNull(started); Objects.requireNonNull(observed);
        var release = ControlBuild.strictMapper().readValue(NativeBridgeBuild.read(grant.capacityEvidence(), 131072),
                ControlBuild.CapacityRelease.class);
        Instant opened = Instant.parse(release.observedAtUtc()), deadline = Instant.parse(release.reviewAtUtc());
        NativeBridgeBuild.require(grant.machineId().equals(request.machineId()) && release.machineId().equals(request.machineId())
                && release.ownerTask().equals(grant.ownerTask()) && grant.stage() == request.stage()
                && !started.isBefore(opened) && !observed.isBefore(started) && observed.isBefore(grant.deadline())
                && !grant.deadline().isAfter(deadline) && grant.memoryLimitBytes() <= release.memoryLimitBytes()
                && grant.outputAllocationLimitBytes() <= release.parts().getOrDefault("artifacts", 0L),
                "Historical Root owner/machine/stage/window/memory/allocation binding differs");
        NativeBridgeBuild.require(NativeBridgeBuild.readRequest(grant.requestRef()).equals(request),
                "Historical Root grant is not bound to this exact typed request");
        List<Path> scopes = censusRoots(release);
        for (Path mutable : List.of(request.buildRoot(), request.scratchRoot(), Path.of(release.temporaryRoot()))) {
            NativeBridgeBuild.require(scopes.stream().anyMatch(mutable::startsWith), "Native output scope is outside Root release");
            requireVolume(release, mutable);
        }
        for (Path scope : scopes) {
            NativeBridgeBuild.require(!scope.startsWith(request.sourceRoot()) && !request.sourceRoot().startsWith(scope),
                    "Native mutable scope overlaps its frozen source tree");
            requireVolume(release, scope);
        }
        release.policyRef().verify();
        var policy = CiBootstrap.readPolicy(NativeBridgeBuild.read(release.policyRef(), 131072));
        for (var entry : release.volumes().entrySet()) {
            var volume = entry.getValue(); var override = release.quotaOverrides().get(entry.getKey());
            if (override != null) {
                NativeBridgeBuild.require(override.task().equals(release.ownerTask())
                        && !Instant.parse(override.reviewAtUtc()).isAfter(deadline), "Root quota override owner/window differs");
                new ControlBuild.FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()).verify();
            }
            NativeBridgeBuild.require(volume.equals(CiBootstrap.calculate(policy, volume.totalVolumeBytes(), volume.availableBytes(),
                    volume.thisWritePeak(), volume.otherUnspentReservations(), volume.systemGrowthReserve(),
                    volume.currentProjectUsageConservativeUpper(), override, opened, deadline)),
                    "Root native volume does not follow the shared storage policy");
            if (scopes.stream().anyMatch(path -> path.getRoot().equals(Path.of(entry.getKey()).getRoot())))
                NativeBridgeBuild.require(volume.thisWritePeak() >= grant.outputAllocationLimitBytes(),
                        "Root volume reservation cannot cover the complete native output cap");
        }
        grant.capacityEvidence().verify(); return release;
    }

    /** Every additional body actually read by the historical envelope belongs to launch custody. */
    public static List<ControlBuild.FileRef> evidenceReferences(NativeBridgeBuild.Grant grant) throws IOException {
        var release = ControlBuild.strictMapper().readValue(NativeBridgeBuild.read(grant.capacityEvidence(), 131072),
                ControlBuild.CapacityRelease.class);
        var refs = new ArrayList<ControlBuild.FileRef>(); refs.add(grant.capacityEvidence()); refs.add(release.policyRef());
        for (var override : release.quotaOverrides().values())
            refs.add(new ControlBuild.FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()));
        var complete = NativeBridgeBuild.merge(refs); NativeBridgeBuild.verify(complete); return complete;
    }
    private static void verifyLivePaths(NativeBridgeBuild.Request request, ControlBuild.CapacityRelease release) throws IOException {
        Path temporary = NativeBridgeBuild.absolute(Path.of(release.temporaryRoot()));
        for (String property : List.of("java.io.tmpdir", "jna.tmpdir")) {
            String value = System.getProperty(property);
            NativeBridgeBuild.require(value != null && !value.isBlank(), "Native JVM must declare both private temporary properties");
            Path path = NativeBridgeBuild.absolute(Path.of(value));
            NativeBridgeBuild.require(path.startsWith(temporary), "Native JVM temporary path escaped the exact Root release");
            requireVolume(release, path); SharedSourceFiles.plainAncestors(path);
        }
        grantRoots(request, release);
    }
    private static void grantRoots(NativeBridgeBuild.Request request, ControlBuild.CapacityRelease release) throws IOException {
        var scopes = censusRoots(release);
        for (Path root : List.of(request.buildRoot(), request.scratchRoot(), Path.of(release.temporaryRoot())))
            NativeBridgeBuild.require(scopes.stream().anyMatch(root::startsWith), "Actual native output root escaped its release");
    }
    private static List<Path> censusRoots(ControlBuild.CapacityRelease release) throws IOException {
        var scopes = new ArrayList<Path>();
        for (String value : release.approvedOutputRoots()) {
            Path path = NativeBridgeBuild.absolute(Path.of(value));
            NativeBridgeBuild.require(!path.equals(path.getRoot()), "Whole-volume native mutable scope is forbidden");
            if (!scopes.contains(path)) scopes.add(path);
        }
        Path temporary = NativeBridgeBuild.absolute(Path.of(release.temporaryRoot()));
        NativeBridgeBuild.require(scopes.stream().anyMatch(temporary::startsWith), "ENTIRETMP must be an approved Root output scope");
        return scopes.stream().filter(path -> scopes.stream().noneMatch(other -> !other.equals(path) && path.startsWith(other))).toList();
    }
    private static void requireVolume(ControlBuild.CapacityRelease release, Path path) throws IOException {
        NativeBridgeBuild.require(release.volumes().keySet().stream().map(Path::of)
                .anyMatch(volume -> volume.equals(path.getRoot())), "Explicit native output/TMP volume budget missing");
    }
    private static void liveStorage(NativeBridgeBuild.Request request, NativeBridgeBuild.Grant grant,
            ControlBuild.CapacityRelease release, List<Path> scopes, boolean reserveReceipt) throws IOException {
        NativeBridgeBuild.require(request.machineId().equals(WindowsJobProcess.currentMachineId())
                && Instant.now().isBefore(grant.deadline()), "Fresh native machine/window guard failed");
        for (var entry : release.volumes().entrySet())
            NativeBridgeBuild.require(Files.getFileStore(Path.of(entry.getKey())).getUsableSpace() >= entry.getValue().requiredFree(),
                    "Native output volume no longer has its shared free-space reserve");
        long allocation = allocation(scopes, grant.deadline());
        long pending = reserveReceipt ? RECEIPT_RESERVE_BYTES : 0;
        NativeBridgeBuild.require(Math.addExact(allocation, pending) <= grant.outputAllocationLimitBytes(),
                "Native output/ENTIRETMP allocation plus terminal receipt reserve exceeds its cap");
    }
    /** Native AllocationSize, including retained outputs and a directory guard; no link release credit. */
    static long allocation(List<Path> roots, Instant deadline) throws IOException {
        Instant bound = Instant.now().plus(Duration.ofSeconds(120));
        if (deadline.isBefore(bound)) bound = deadline;
        final Instant until = bound;
        final long[] total = {0}; final int[] entries = {0};
        for (Path root : roots) {
            if (Files.notExists(root, LinkOption.NOFOLLOW_LINKS)) continue;
            NativeBridgeBuild.require(Files.exists(root, LinkOption.NOFOLLOW_LINKS), "Native census root existence unavailable");
            Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
                private void tick() throws IOException {
                    NativeBridgeBuild.require(++entries[0] <= MAX_CENSUS_ENTRIES && Instant.now().isBefore(until),
                            "Native output census exceeds the shared entry/time bound");
                }
                @Override public FileVisitResult preVisitDirectory(Path path, BasicFileAttributes attrs) throws IOException {
                    tick(); SharedSourceFiles.plainAncestors(path);
                    NativeBridgeBuild.require(!attrs.isSymbolicLink() && !attrs.isOther(), "Native output census requires ordinary directories");
                    total[0] = Math.addExact(total[0], 4096); return FileVisitResult.CONTINUE;
                }
                @Override public FileVisitResult visitFile(Path path, BasicFileAttributes attrs) throws IOException {
                    tick(); NativeBridgeBuild.require(attrs.isRegularFile() && !attrs.isSymbolicLink() && !attrs.isOther(),
                            "Native output census rejects nonordinary files");
                    try { total[0] = Math.addExact(total[0], SharedSourceFiles.nativeFile(path).allocatedBytes()); }
                    catch (IOException race) { if (!Files.notExists(path, LinkOption.NOFOLLOW_LINKS)) throw race; }
                    return FileVisitResult.CONTINUE;
                }
                @Override public FileVisitResult visitFileFailed(Path path, IOException failure) throws IOException {
                    if (!path.equals(root) && failure instanceof NoSuchFileException) return FileVisitResult.CONTINUE;
                    throw failure;
                }
                @Override public FileVisitResult postVisitDirectory(Path path, IOException failure) throws IOException {
                    if (failure != null && (path.equals(root) || !(failure instanceof NoSuchFileException))) throw failure;
                    return FileVisitResult.CONTINUE;
                }
            });
        }
        return total[0];
    }
}

