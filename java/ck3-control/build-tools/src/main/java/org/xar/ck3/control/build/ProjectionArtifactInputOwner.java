package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import static org.xar.ck3.control.build.ProjectionArtifactAuthority.*;

/** Original service Owner's finite metadata writer. It neither publishes graphs nor acquires event/Game/ledger authority. */
public final class ProjectionArtifactInputOwner {
    public static final String GRANT_SCHEMA = "xar.projection-artifact-input-root-grant/v1";
    public static final String PRODUCER_CLASS = "org.xar.ck3.control.wave2.military.projection.MilitaryProjectionPortCatalog";
    public static final long JOB_MEMORY_BYTES = 512L << 20;
    private ProjectionArtifactInputOwner() { }

    /** Package-only build custody seam. Native identity, storage checks and writer lifecycle remain real. */
    interface Environment {
        ControlBuild.BuildReceipt acceptedBuild(Path receipt) throws IOException;
        List<ControlBuild.FileRef> runtimeClosure() throws IOException;
        ControlBuild.FileRef ownerCodeSource() throws IOException;
    }
    private static final Environment ACTUAL = new Environment() {
        @Override public ControlBuild.BuildReceipt acceptedBuild(Path receipt) throws IOException { return ControlBuild.acceptedReceipt(receipt); }
        @Override public List<ControlBuild.FileRef> runtimeClosure() throws IOException { return ControlBuild.producerClosure(); }
        @Override public ControlBuild.FileRef ownerCodeSource() throws IOException { return codeSource(); }
    };

    /** Only a trusted Root caller may supply this exact grant reference; public call payloads cannot construct an Owner. */
    public record Config(ControlBuild.FileRef rootGrantRef, String scopeId, String ownerSessionId) {
        public Config {
            reference(rootGrantRef); identifier(scopeId); identifier(ownerSessionId);
            if (rootGrantRef.bytes() > METADATA_MAX_BYTES) throw new IllegalArgumentException("finite Root grant metadata required");
        }
    }
    public record RootGrant(String schema, String machineId, String ownerTask, String observedAtUtc, String reviewAtUtc,
            String inputRoot, String scopePath, String leasePath, String sourceBindingPath, String runtimeBindingPath,
            long maxInputBytes, long jobMemoryLimitBytes, ControlBuild.FileRef producerArtifactRef, ControlBuild.FileRef policyRef,
            ControlBuild.FileRef capacityReleaseRef) {
        public RootGrant {
            machine(machineId); identifier(ownerTask); interval(Instant.parse(observedAtUtc), Instant.parse(reviewAtUtc));
            if (!GRANT_SCHEMA.equals(schema) || maxInputBytes < 1 || maxInputBytes > MAX_SAFE_INTEGER || jobMemoryLimitBytes != JOB_MEMORY_BYTES) {
                throw new IllegalArgumentException("explicit finite original input storage and unchanged service Job memory required");
            }
            for (String value : List.of(inputRoot, scopePath, leasePath, sourceBindingPath, runtimeBindingPath)) absolute(Path.of(value));
            reference(producerArtifactRef); reference(policyRef); reference(capacityReleaseRef);
        }
    }
    private record RootStamp(Path path, SharedSourceFiles.DirectoryIdentity key) { }

    /** Builds small source/runtime witnesses only after the normal accepted full service build has been read. */
    public static Prepared prepare(Config config, ControlBuild.BuildReceipt build, ControlBuild.FileRef buildRef,
            Path workRoot, Instant deadline, String machineId, List<Path> unrelatedRoots) throws IOException {
        return prepare(config, build, buildRef, workRoot, deadline, machineId, unrelatedRoots, ACTUAL);
    }
    // Fixtures cannot reach this overload through a public HTTP request or a public Owner configuration.
    static Prepared prepare(Config config, ControlBuild.BuildReceipt build, ControlBuild.FileRef buildRef,
            Path workRoot, Instant deadline, String machineId, List<Path> unrelatedRoots, Environment environment) throws IOException {
        Objects.requireNonNull(environment);
        Objects.requireNonNull(config); Objects.requireNonNull(build); reference(buildRef); absolute(workRoot);
        RootGrant grant = ControlBuild.strictMapper().readValue(readExact(config.rootGrantRef(), METADATA_MAX_BYTES), RootGrant.class);
        Instant now = Instant.now(), review = Instant.parse(grant.reviewAtUtc());
        if (!machineId.equals(grant.machineId()) || !machineId.equals(build.machineId()) || !"PASS".equals(build.status()) || build.error() != null
                || build.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR || build.sourcePostcheck().state() != ControlBuild.SourceState.MATCH
                || build.compiledSourcePostcheck().state() != ControlBuild.SourceState.MATCH || !build.completeDeployment().contains(grant.producerArtifactRef())
                || Instant.parse(grant.observedAtUtc()).isAfter(now.plusSeconds(5)) || !now.isBefore(review) || !now.isBefore(deadline)) {
            throw new IOException("current Root storage grant and complete same-machine full service build required");
        }
        validateBudget(grant);
        Path inputRoot = Path.of(grant.inputRoot()), logs = workRoot.resolve("logs");
        List<Path> metadata = List.of(Path.of(grant.scopePath()), Path.of(grant.leasePath()), Path.of(grant.sourceBindingPath()), Path.of(grant.runtimeBindingPath()));
        if (metadata.stream().distinct().count() != metadata.size()) throw new IOException("distinct immutable authority files required");
        for (Path output : metadata) {
            if (!logs.equals(output.getParent()) || Files.exists(output, LinkOption.NOFOLLOW_LINKS)) throw new IOException("new flat Owner metadata files in the original service logs root required");
        }
        for (Path other : List.of(workRoot, Path.of(build.sourceRoot()), Path.of(build.compiledSourceRoot()), Path.of(build.deploymentRoot()))) disjoint(inputRoot, other);
        for (Path other : unrelatedRoots) disjoint(inputRoot, other);
        List<RootStamp> roots = roots(inputRoot); requireEmpty(inputRoot);
        ProcessIdentity owner = ProcessIdentity.from(WindowsJobProcess.observeLiveProcess(ProcessHandle.current().pid()).identity());
        if (!owner.executable().equals(Path.of(build.javaExecutableRef().path()))) throw new IOException("Owner must use the exact build-qualified Java executable");
        List<ControlBuild.FileRef> actualRuntime = environment.runtimeClosure();
        if (!actualRuntime.equals(build.producerRuntimePins()) || !actualRuntime.contains(environment.ownerCodeSource())) throw new IOException("actual Owner CodeSource and complete runtime differ from the qualified producer closure");
        buildRef.verify();
        if (!environment.acceptedBuild(Path.of(buildRef.path())).equals(build)) throw new IOException("accepted build changed before authority publication");
        Path lockPath = Path.of(grant.scopePath() + ".writer.lock");
        canonical(logs);
        FileChannel channel = FileChannel.open(lockPath, StandardOpenOption.CREATE_NEW, StandardOpenOption.READ, StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS);
        FileLock lock = null;
        try {
            lock = channel.tryLock(); if (lock == null || !lock.isValid()) throw new IOException("original artifact Owner writer lock unavailable");
            SourceBinding source = new SourceBinding(machineId, buildRef, build.sourcePins(), build.compiledSourcePins());
            RuntimeBinding runtime = new RuntimeBinding(machineId, buildRef, config.ownerSessionId(), owner, ownerSources(build), actualRuntime);
            ControlBuild.FileRef sourceRef = publish(Path.of(grant.sourceBindingPath()), encodeSourceBinding(source));
            ControlBuild.FileRef runtimeRef = publish(Path.of(grant.runtimeBindingPath()), encodeRuntimeBinding(runtime));
            Instant expires = deadline.isBefore(review) ? deadline : review;
            Scope scope = new Scope(config.scopeId(), config.ownerSessionId(), machineId, owner, InputOperation.MILITARY_COMBAT_ROLES_NORMALIZE,
                    inputRoot, Path.of(grant.leasePath()), grant.maxInputBytes(), now, expires, sourceRef, grant.producerArtifactRef(), buildRef, runtimeRef, PRODUCER_CLASS);
            requireBindings(scope, build, source, runtime);
            ControlBuild.FileRef scopeRef = publish(Path.of(grant.scopePath()), encodeScope(scope));
            return new Prepared(config, grant, build, scope, scopeRef, source, runtime, roots, channel, lock, environment);
        } catch (IOException | RuntimeException | Error failure) {
            if (lock != null) try { lock.release(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
            try { channel.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
            throw failure;
        }
    }

    public static final class Prepared implements AutoCloseable {
        private final Config config;
        private final RootGrant grant;
        private final ControlBuild.BuildReceipt build;
        private final Scope scope;
        private final ControlBuild.FileRef scopeRef;
        private final SourceBinding source;
        private final RuntimeBinding runtime;
        private final List<RootStamp> roots;
        private final FileChannel channel;
        private final FileLock lock;
        private final Environment environment;
        private ControlBuild.FileRef leaseRef;
        private Lease lease;
        private boolean leaseAttempted;
        private boolean closed;
        private Prepared(Config config, RootGrant grant, ControlBuild.BuildReceipt build, Scope scope, ControlBuild.FileRef scopeRef,
                SourceBinding source, RuntimeBinding runtime, List<RootStamp> roots, FileChannel channel, FileLock lock, Environment environment) {
            this.config = config; this.grant = grant; this.build = build; this.scope = scope; this.scopeRef = scopeRef;
            this.source = source; this.runtime = runtime; this.roots = roots; this.channel = channel; this.lock = lock;
            this.environment = environment;
        }
        public ControlBuild.FileRef scopeRef() { return scopeRef; }
        public Scope scope() { return scope; }
        /** Cheap dispatch guard; complete source/build measurements remain at the explicit immutable-input boundaries. */
        public synchronized void requireLive(WindowsJobProcess.ProcessIdentity child) throws IOException {
            requireLiveOwner();
            if (leaseRef == null || !ProcessIdentity.from(child).equals(lease.hostProcess())
                    || !ProcessIdentity.from(WindowsJobProcess.observeLiveProcess(child.pid()).identity()).equals(lease.hostProcess())) throw new IOException("original live leased host required");
        }
        /** One immutable lease, issued only for the actual child generation. There is no renewal or replacement API. */
        public synchronized void publishLease(WindowsJobProcess.ProcessIdentity child) throws IOException {
            if (leaseAttempted) throw new IOException("this Owner already attempted its single immutable host lease; an unknown publication cannot be retried");
            leaseAttempted = true;
            requireOwner();
            ProcessIdentity host = ProcessIdentity.from(WindowsJobProcess.observeLiveProcess(child.pid()).identity());
            if (!host.equals(ProcessIdentity.from(child))) throw new IOException("actual child generation differs before lease publication");
            lease = new Lease(scopeRef, host, Instant.now(), scope.expiresAtUtc(), Purpose.FULL);
            leaseRef = publish(scope.leasePath(), encodeLease(lease));
            verifyCurrent(child);
        }
        public synchronized void verifyCurrent(WindowsJobProcess.ProcessIdentity child) throws IOException {
            requireOwner();
            if (leaseRef == null || !ProcessIdentity.from(child).equals(lease.hostProcess())
                    || !ProcessIdentity.from(WindowsJobProcess.observeLiveProcess(child.pid()).identity()).equals(lease.hostProcess())) throw new IOException("original leased host is unavailable");
            if (!decodeLease(readExact(leaseRef, METADATA_MAX_BYTES)).equals(lease)) throw new IOException("original Owner lease changed");
        }
        public synchronized Observed observe(Context observed, ControlBuild.FileRef responseRef, WindowsJobProcess.ProcessIdentity child,
                ProjectionDeploymentProof.Attestation proof) throws IOException {
            verifyCurrent(child); Instant now = Instant.now();
            Active expected = new Active(scopeRef, leaseRef, scope, lease.hostProcess());
            if (!observed.machineId().equals(scope.machineId()) || observed.observedAtUtc().isAfter(now.plusSeconds(5)) || observed.observedAtUtc().isBefore(now.minusSeconds(30))
                    || !observed.artifactInputs().equals(java.util.Optional.of(expected))) throw new IOException("actual host artifact context differs from original Root scope and Owner lease");
            boolean owns = proof.catalogs().stream().anyMatch(catalog -> catalog.providerClass().equals(PRODUCER_CLASS)
                    && catalog.artifactRef().equals(scope.producerArtifactRef()) && catalog.operations().stream().anyMatch(operation -> operation.operation().equals(scope.operation().wire())));
            if (!owns) throw new IOException("actual source-qualified catalog does not own this existing operation and producer artifact");
            if (!decodeContext(readExact(responseRef, CONTEXT_MAX_BYTES)).equals(observed)) throw new IOException("actual original artifact HTTP response does not match its typed observation");
            verifyCurrent(child); return new Observed(observed, responseRef);
        }
        private void requireOwner() throws IOException {
            requireLiveOwner();
            for (RootStamp root : roots) {
                canonical(root.path()); BasicFileAttributes current = Files.readAttributes(root.path(), BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                if (!current.isDirectory() || !root.key().equals(SharedSourceFiles.nativeDirectory(root.path()))) throw new IOException("original Root input directory identity changed");
            }
            exact(config.rootGrantRef()); validateBudget(grant);
            if (!decodeScope(readExact(scopeRef, METADATA_MAX_BYTES)).equals(scope)
                    || !decodeSourceBinding(readExact(scope.sourceSnapshotRef(), BINDING_MAX_BYTES)).equals(source)
                    || !decodeRuntimeBinding(readExact(scope.runtimeBindingRef(), BINDING_MAX_BYTES)).equals(runtime)
                    || !environment.acceptedBuild(Path.of(scope.buildReceiptRef().path())).equals(build)
                    || !environment.runtimeClosure().equals(runtime.ownerRuntimeRefs()) || !runtime.ownerRuntimeRefs().contains(environment.ownerCodeSource())) throw new IOException("original Owner source/runtime/build custody changed");
            scope.buildReceiptRef().verify(); requireBindings(scope, build, source, runtime);
        }
        private void requireLiveOwner() throws IOException {
            if (closed || !lock.isValid() || !Instant.now().isBefore(scope.expiresAtUtc())
                    || !WindowsJobProcess.currentMachineId().equals(scope.machineId())
                    || !ProcessIdentity.from(WindowsJobProcess.observeLiveProcess(ProcessHandle.current().pid()).identity()).equals(scope.ownerProcess())) throw new IOException("original live finite artifact Owner writer required");
        }
        @Override public synchronized void close() throws IOException {
            if (closed) return; closed = true;
            IOException failure = null;
            try { lock.release(); } catch (IOException error) { failure = error; }
            try { channel.close(); } catch (IOException error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
            if (failure != null) throw failure;
            // Scope/lease/proofs and an UNKNOWN graph remain original evidence. This writer never deletes them.
        }
    }
    private static ControlBuild.FileRef publish(Path path, byte[] raw) throws IOException {
        canonical(path.getParent()); Files.write(path, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS);
        ControlBuild.FileRef actual = ControlBuild.FileRef.measure(path); exact(actual); return actual;
    }
    private static void validateBudget(RootGrant grant) throws IOException {
        ControlBuild.CapacityRelease release = ControlBuild.strictMapper().readValue(readExact(grant.capacityReleaseRef(), BINDING_MAX_BYTES), ControlBuild.CapacityRelease.class);
        CiBootstrap.Policy policy = CiBootstrap.readPolicy(readExact(grant.policyRef(), METADATA_MAX_BYTES));
        CiBootstrap.VolumeBudget volume = requireBudget(grant, release, policy);
        var store = Files.getFileStore(Path.of(grant.inputRoot()));
        if (store.getTotalSpace() != volume.totalVolumeBytes() || store.getUsableSpace() < volume.requiredFree()) throw new IOException("actual input volume no longer satisfies the common Root reservation");
        CiBootstrap.QuotaOverride override = release.quotaOverrides().get(Path.of(grant.inputRoot()).getRoot().toString());
        if (override != null) exact(new ControlBuild.FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()));
    }
    /** Shared-policy calculation, with no new storage formula or authority inferred from a request body. */
    static CiBootstrap.VolumeBudget requireBudget(RootGrant grant, ControlBuild.CapacityRelease release, CiBootstrap.Policy policy) throws IOException {
        Instant now = Instant.now(), observed = Instant.parse(release.observedAtUtc()), review = Instant.parse(release.reviewAtUtc());
        Path root = Path.of(grant.inputRoot()).getRoot();
        CiBootstrap.VolumeBudget volume = release.volumes().get(root.toString());
        Long part = release.parts().get("projection_input");
        if (!release.machineId().equals(grant.machineId()) || !release.ownerTask().equals(grant.ownerTask())
                || !release.policyRef().equals(grant.policyRef()) || !release.approvedOutputRoots().contains(grant.inputRoot())
                || release.memoryLimitBytes() != grant.jobMemoryLimitBytes() || volume == null || part == null || part < grant.maxInputBytes()
                || volume.thisWritePeak() < grant.maxInputBytes() || observed.isAfter(now.plusSeconds(5)) || !now.isBefore(review)
                || Instant.parse(grant.observedAtUtc()).isBefore(observed) || Instant.parse(grant.reviewAtUtc()).isAfter(review)) {
            throw new IOException("explicit same-pool finite Root input/Job reservation required");
        }
        try {
            CiBootstrap.VolumeBudget calculated = CiBootstrap.calculate(policy, volume.totalVolumeBytes(), volume.availableBytes(), volume.thisWritePeak(),
                    volume.otherUnspentReservations(), volume.systemGrowthReserve(), volume.currentProjectUsageConservativeUpper(),
                    release.quotaOverrides().get(root.toString()), observed, review);
            if (!calculated.equals(volume)) throw new IOException("Root input reservation differs from the versioned shared storage policy");
        } catch (IllegalArgumentException | ArithmeticException failure) { throw new IOException("Root input reservation is unavailable", failure); }
        return volume;
    }
    private static byte[] readExact(ControlBuild.FileRef ref, int maximum) throws IOException {
        exact(ref); if (ref.bytes() > maximum) throw new IOException("finite original metadata required");
        SharedSourceFiles.NativeFile before = SharedSourceFiles.nativeFile(Path.of(ref.path()));
        byte[] raw; try (var input = Files.newInputStream(Path.of(ref.path()), LinkOption.NOFOLLOW_LINKS)) { raw = input.readNBytes(maximum + 1); }
        SharedSourceFiles.NativeFile after = SharedSourceFiles.nativeFile(Path.of(ref.path()));
        if (raw.length != ref.bytes() || !before.equals(after)) throw new IOException("original metadata file identity changed");
        try {
            if (!java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)).equals(ref.sha256())) throw new IOException("original metadata raw bytes differ from their exact reference");
        } catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        exact(ref); return raw;
    }
    private static void exact(ControlBuild.FileRef ref) throws IOException { reference(ref); canonical(Path.of(ref.path())); ref.verify(); }
    private static ControlBuild.FileRef codeSource() throws IOException {
        try { return ControlBuild.FileRef.measure(Path.of(ProjectionArtifactInputOwner.class.getProtectionDomain().getCodeSource().getLocation().toURI())); }
        catch (java.net.URISyntaxException failure) { throw new IOException("original Owner CodeSource unavailable", failure); }
    }
    private static void canonical(Path path) throws IOException {
        absolute(path);
        for (Path entry = path; entry != null; entry = entry.getParent()) if (Files.isSymbolicLink(entry) || !entry.toRealPath().equals(entry)) throw new IOException("indirect authority path refused");
    }
    private static List<RootStamp> roots(Path path) throws IOException {
        List<RootStamp> result = new ArrayList<>();
        for (Path entry = path; entry != null; entry = entry.getParent()) {
            canonical(entry); BasicFileAttributes attrs = Files.readAttributes(entry, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (!attrs.isDirectory()) throw new IOException("original identity-bearing directory required"); result.add(new RootStamp(entry, SharedSourceFiles.nativeDirectory(entry)));
        }
        return List.copyOf(result);
    }
    private static void requireEmpty(Path root) throws IOException { try (DirectoryStream<Path> entries = Files.newDirectoryStream(root)) { if (entries.iterator().hasNext()) throw new IOException("Root input slot is already occupied; UNKNOWN cannot be retried or reclaimed"); } }
    private static void disjoint(Path first, Path second) throws IOException { if (first.startsWith(second) || second.startsWith(first)) throw new IOException("input slot must be separate from service/source/deployment/event roots"); }
}
