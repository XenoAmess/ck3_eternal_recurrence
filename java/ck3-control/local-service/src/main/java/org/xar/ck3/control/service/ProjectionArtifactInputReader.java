package org.xar.ck3.control.service;

import java.io.IOException;
import java.io.InputStream;
import java.net.URISyntaxException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionArtifactInputCodec;
import org.xar.ck3.control.contracts.projection.ProjectionArtifactInputContract;
import org.xar.ck3.control.contracts.projection.ProjectionArtifactInputRef;
import org.xar.ck3.control.contracts.projection.ProjectionArtifactInputScope;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.build.ProjectionArtifactAuthority;
import static org.xar.ck3.control.build.ProjectionArtifactAuthority.*;

/** One Root-configured read-only slot. It never creates, modifies, reserves or deletes an input or lease. */
public final class ProjectionArtifactInputReader implements ProjectionArtifactInputScope {
    record Observation(String machineId, ProcessIdentity owner, ProcessIdentity host) { }
    @FunctionalInterface interface Observer { Observation observe(Scope configured); }
    @FunctionalInterface interface BuildVerifier { ControlBuild.BuildReceipt verify(Path receipt) throws IOException; }
    private record Stamp(Path path, SharedSourceFiles.NativeFile key, long bytes, FileTime modified) { }
    private record RootStamp(Path path, SharedSourceFiles.DirectoryIdentity key) { }
    private record LeaseState(Active active, Stamp lease, List<Stamp> proofs, Lease decoded) { }
    private final ControlBuild.FileRef scopeRef;
    private final Scope configured;
    private final Stamp scopeStamp;
    private final List<RootStamp> ancestors;
    private final Observer observer;
    private final ClassLoader loader;
    private final Clock clock;
    private final BuildVerifier builds;
    private volatile boolean registeredOwner;

    public ProjectionArtifactInputReader(ExactRef rootConfiguredScope, String expectedMachineId) {
        this(rootConfiguredScope, expectedMachineId, ProjectionArtifactInputReader::nativeObservation,
                Thread.currentThread().getContextClassLoader(), Clock.systemUTC(), ControlBuild::acceptedReceipt);
    }
    // Package-only native/clock/classpath seam: fixtures do not become an alternate production authority.
    ProjectionArtifactInputReader(ExactRef scope, String machine, Observer observer, ClassLoader loader, Clock clock, BuildVerifier builds) {
        this.scopeRef = ProjectionArtifactInputContract.fileRef(scope);
        this.observer = Objects.requireNonNull(observer); this.loader = Objects.requireNonNull(loader); this.clock = Objects.requireNonNull(clock);
        this.builds = Objects.requireNonNull(builds);
        try {
            if (scope.bytes() > METADATA_MAX_BYTES) throw new IOException("finite Root scope metadata required");
            scopeStamp = exact(scopeRef, true); configured = ProjectionArtifactInputCodec.decodeScope(read(scopeRef, METADATA_MAX_BYTES));
            if (!configured.machineId().equals(machine) || Path.of(scope.path()).normalize().startsWith(configured.inputRoot())) {
                throw new IOException("Root scope source or actual machine differs from startup configuration");
            }
            ancestors = rootWitnesses(configured.inputRoot());
            // Lease publication happens only after the original Owner has the actual child PID/birth.
        } catch (IOException | RuntimeException failure) { throw unavailable("configured artifact input authority unavailable", failure); }
    }
    public Active current() {
        try { return lease(null).active(); }
        catch (OutOfMemoryError | LinkageError resource) { throw unavailable("artifact authority observation resource unavailable", resource); }
        catch (IOException | RuntimeException failure) { throw unavailable("Root artifact input lease unavailable", failure); }
    }
    void bindCatalogOwner(List<ProjectionHost.CatalogOrigin> actualCatalogs) {
        registeredOwner = actualCatalogs.stream().anyMatch(catalog -> catalog.providerClass().equals(configured.producerClass())
                && Path.of(catalog.artifactPath()).normalize().equals(Path.of(configured.producerArtifactRef().path()).normalize())
                && catalog.operations().stream().anyMatch(profile -> profile.operation().wire().equals(configured.operation().wire())));
    }
    @Override public <T> T withInput(ProjectionOperation operation, ProjectionArtifactInputRef claim, Function<byte[], T> computation) {
        Objects.requireNonNull(operation); Objects.requireNonNull(claim); Objects.requireNonNull(computation);
        LeaseState admitted;
        Stamp input;
        byte[] raw;
        ControlBuild.FileRef inputRef = ProjectionArtifactInputContract.fileRef(claim.inputRef());
        ControlBuild.FileRef leaseRef = ProjectionArtifactInputContract.fileRef(claim.leaseRef());
        try {
            if (!operation.wire().equals(configured.operation().wire())) throw new IOException("artifact scope is not registered for this operation");
            admitted = lease(leaseRef);
            Path expected = configured.inputRoot().resolve(INPUT_NAME);
            if (!Path.of(claim.inputRef().path()).normalize().equals(expected)
                    || claim.inputRef().bytes() > configured.maxInputBytes()
                    || claim.inputRef().bytes() > Integer.MAX_VALUE - 8L) throw new IOException("artifact input exceeds its Root-owned slot or implementation resource budget");
            singleSlot(); input = exact(inputRef, true); raw = read(inputRef, configured.maxInputBytes());
            stable(input, exact(inputRef, false));
        } catch (OutOfMemoryError | LinkageError resource) { throw unavailable("artifact input allocation or runtime resource unavailable", resource); }
        catch (IOException | RuntimeException failure) { throw unavailable("artifact input custody or finite resource budget unavailable", failure); }
        try {
            return computation.apply(raw);
        } catch (OutOfMemoryError resource) { throw unavailable("artifact computation allocation resource unavailable", resource); }
        finally {
            // A callback's original domain/internal exception is preserved when custody is current.
            // Changed custody supersedes a result or rejection: neither is qualified against another lease/input.
            try {
                LeaseState after = lease(leaseRef); stable(admitted.lease(), after.lease());
                if (admitted.proofs().size() != after.proofs().size()) throw new IOException("accepted source/deployment proof closure changed");
                for (int index = 0; index < admitted.proofs().size(); index++) stable(admitted.proofs().get(index), after.proofs().get(index));
                singleSlot(); stable(input, exact(inputRef, true));
                requireCurrent(after.decoded());
            } catch (OutOfMemoryError | LinkageError resource) { throw unavailable("artifact post-computation custody resource unavailable", resource); }
            catch (IOException | RuntimeException failure) { throw unavailable("artifact authority or input changed during computation", failure); }
        }
    }
    private LeaseState lease(ControlBuild.FileRef claimed) throws IOException {
        if (!registeredOwner) throw new IOException("Root producer is not the actual registered owner of this operation");
        stable(scopeStamp, exact(scopeRef, true)); witnessRoots();
        Instant now = clock.instant(); currentInterval(configured.issuedAtUtc(), configured.expiresAtUtc(), now);
        Path leasePath = configured.leasePath(); Stamp stamp = stamp(leasePath);
        if (stamp.bytes() < 1 || stamp.bytes() > METADATA_MAX_BYTES) throw new IOException("finite Owner lease metadata required");
        ControlBuild.FileRef actualLease = new ControlBuild.FileRef(leasePath.toString(), stamp.bytes(), hash(leasePath, stamp.bytes()));
        if (claimed != null && (!Path.of(claimed.path()).normalize().equals(leasePath)
                || claimed.bytes() != actualLease.bytes() || !claimed.sha256().equals(actualLease.sha256()))) throw new IOException("call claim differs from the fixed Owner lease");
        var lease = ProjectionArtifactInputCodec.decodeLease(read(actualLease, METADATA_MAX_BYTES));
        stable(stamp, exact(actualLease, false));
        if (!lease.scopeRef().equals(scopeRef) || lease.issuedAtUtc().isBefore(configured.issuedAtUtc())
                || lease.expiresAtUtc().isAfter(configured.expiresAtUtc())) throw new IOException("Owner lease differs from the original Root scope");
        currentInterval(lease.issuedAtUtc(), lease.expiresAtUtc(), now);
        Observation actual = requireCurrent(lease);
        List<Stamp> proofs = new ArrayList<>();
        for (ControlBuild.FileRef proof : List.of(configured.sourceSnapshotRef(), configured.producerArtifactRef(), configured.buildReceiptRef(), configured.runtimeBindingRef())) proofs.add(exact(proof, true));
        // Use the existing full acceptance path: source/deployment closure growth, Maven terminal,
        // native machine, capacity deadline and capture-only exclusion are not reimplemented here.
        ControlBuild.BuildReceipt pinned = ControlBuild.strictMapper().readValue(read(configured.buildReceiptRef(), ControlBuild.BUILD_RECEIPT_MAX_BYTES), ControlBuild.BuildReceipt.class);
        ControlBuild.BuildReceipt accepted = builds.verify(Path.of(configured.buildReceiptRef().path()));
        if (!accepted.equals(pinned)) throw new IOException("accepted build differs from the exact original Root receipt");
        if (accepted.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR
                || !accepted.machineId().equals(configured.machineId()) || !"PASS".equals(accepted.status()) || accepted.error() != null
                || accepted.sourcePostcheck().state() != ControlBuild.SourceState.MATCH || accepted.compiledSourcePostcheck().state() != ControlBuild.SourceState.MATCH
                || accepted.sourcePins().isEmpty() || accepted.compiledSourcePins().isEmpty() || accepted.completeDeployment().isEmpty() || accepted.producerRuntimePins().isEmpty()) {
            throw new IOException("current full service build/source/deployment qualification required");
        }
        SourceBinding source = ProjectionArtifactAuthority.decodeSourceBinding(read(configured.sourceSnapshotRef(), BINDING_MAX_BYTES));
        RuntimeBinding runtime = ProjectionArtifactAuthority.decodeRuntimeBinding(read(configured.runtimeBindingRef(), BINDING_MAX_BYTES));
        ProjectionArtifactAuthority.requireBindings(configured, accepted, source, runtime);
        boolean ownsProducer = accepted.completeDeployment().stream().anyMatch(proof -> sameReference(proof, configured.producerArtifactRef()));
        if (!ownsProducer) throw new IOException("producer is outside the accepted complete deployment");
        for (List<ControlBuild.FileRef> closure : List.of(accepted.sourcePins(), accepted.compiledSourcePins(), accepted.completeDeployment(), accepted.producerRuntimePins(),
                source.sourceRefs(), source.compiledSourceRefs(), runtime.ownerSourceRefs(), runtime.ownerRuntimeRefs())) {
            for (ControlBuild.FileRef proof : closure) proofs.add(exact(proof, true));
        }
        Path producer = producerCodeSource();
        if (!producer.equals(Path.of(configured.producerArtifactRef().path()).normalize())) throw new IOException("actual producer class is not the Root-bound artifact");
        witnessRoots(); requireCurrent(lease);
        return new LeaseState(new Active(scopeRef, actualLease, configured, actual.host()), stamp, List.copyOf(proofs), lease);
    }
    private Observation requireCurrent(Lease lease) throws IOException {
        Observation actual = observer.observe(configured);
        Instant now = clock.instant();
        currentInterval(configured.issuedAtUtc(), configured.expiresAtUtc(), now);
        currentInterval(lease.issuedAtUtc(), lease.expiresAtUtc(), now);
        if (!actual.machineId().equals(configured.machineId()) || !actual.owner().equals(configured.ownerProcess())
                || !actual.host().equals(lease.hostProcess())) throw new IOException("actual Owner/host generation or machine differs from Root binding");
        return actual;
    }
    private Path producerCodeSource() throws IOException {
        try {
            Class<?> producer = Class.forName(configured.producerClass(), false, loader);
            var protection = producer.getProtectionDomain();
            if (protection == null || protection.getCodeSource() == null || protection.getCodeSource().getLocation() == null) throw new IOException("actual producer CodeSource unavailable");
            var uri = protection.getCodeSource().getLocation().toURI();
            if (!"file".equalsIgnoreCase(uri.getScheme())) throw new IOException("actual producer artifact must be a file");
            Path path = Path.of(uri).toAbsolutePath().normalize(); canonical(path); return path;
        } catch (ClassNotFoundException | URISyntaxException | LinkageError failure) { throw new IOException("actual producer class source unavailable", failure); }
    }
    private void singleSlot() throws IOException {
        witnessRoots(); int count = 0;
        try (DirectoryStream<Path> children = Files.newDirectoryStream(configured.inputRoot())) {
            for (Path path : children) {
                if (++count > 1 || !INPUT_NAME.equals(path.getFileName().toString())) throw new IOException("single owned artifact slot contains another entry");
                stamp(path);
            }
        }
        if (count != 1) throw new IOException("owned artifact input is absent");
    }
    private void witnessRoots() throws IOException {
        for (RootStamp expected : ancestors) {
            canonical(expected.path()); var attrs = Files.readAttributes(expected.path(), BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (!attrs.isDirectory() || !expected.key().equals(SharedSourceFiles.nativeDirectory(expected.path()))) throw new IOException("Root input directory identity changed");
        }
    }
    private static List<RootStamp> rootWitnesses(Path root) throws IOException {
        List<RootStamp> witnesses = new ArrayList<>();
        for (Path path = root; path != null; path = path.getParent()) {
            canonical(path); var attrs = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (!attrs.isDirectory()) throw new IOException("identity-bearing original input root required");
            witnesses.add(new RootStamp(path, SharedSourceFiles.nativeDirectory(path)));
        }
        return List.copyOf(witnesses);
    }
    private static void currentInterval(Instant issued, Instant expires, Instant now) throws IOException {
        if (issued.isAfter(now.plusSeconds(5)) || !now.isBefore(expires)) throw new IOException("Root artifact lease not current");
    }
    private static Stamp exact(ControlBuild.FileRef ref, boolean content) throws IOException {
        Path path = Path.of(ref.path());
        if (!path.isAbsolute() || !path.equals(path.normalize())) throw new IOException("original reference path must be normalized and absolute");
        Stamp before = stamp(path);
        if (before.bytes() != ref.bytes() || (content && !hash(path, ref.bytes()).equals(ref.sha256()))) throw new IOException("original artifact/proof bytes or SHA changed");
        Stamp after = stamp(path); stable(before, after); return after;
    }
    private static Stamp stamp(Path path) throws IOException {
        canonical(path); var attrs = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (!attrs.isRegularFile()) throw new IOException("identity-bearing regular file required");
        return new Stamp(path, SharedSourceFiles.nativeFile(path), attrs.size(), attrs.lastModifiedTime());
    }
    private static void stable(Stamp before, Stamp after) throws IOException {
        if (!before.path().equals(after.path()) || !before.key().equals(after.key()) || before.bytes() != after.bytes()
                || !before.modified().equals(after.modified())) throw new IOException("original file identity changed");
    }
    private static void canonical(Path path) throws IOException {
        if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IOException("normalized absolute owned path required");
        for (Path entry = path; entry != null; entry = entry.getParent()) {
            if (Files.isSymbolicLink(entry) || !entry.toRealPath().equals(entry)) throw new IOException("indirect owned artifact path refused");
        }
    }
    private static byte[] read(ControlBuild.FileRef ref, long maximum) throws IOException {
        if (ref.bytes() > maximum || ref.bytes() > Integer.MAX_VALUE - 8L) throw new IOException("bounded array resource unavailable");
        Stamp before = exact(ref, false); byte[] raw = new byte[(int) ref.bytes()];
        try (FileChannel channel = FileChannel.open(before.path(), StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS)) {
            ByteBuffer buffer = ByteBuffer.wrap(raw);
            while (buffer.hasRemaining()) if (channel.read(buffer) < 0) throw new IOException("short original artifact read");
            if (channel.read(ByteBuffer.allocate(1)) != -1) throw new IOException("original artifact grew during read");
        }
        stable(before, exact(ref, false));
        if (!HexFormat.of().formatHex(digest().digest(raw)).equals(ref.sha256())) throw new IOException("original input content differs from claim"); return raw;
    }
    private static String hash(Path path, long expectedBytes) throws IOException {
        MessageDigest digest = digest();
        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS);
                InputStream input = java.nio.channels.Channels.newInputStream(channel)) {
            byte[] chunk = new byte[65_536]; long count = 0; int read;
            while ((read = input.read(chunk)) != -1) {
                count += read;
                if (count > expectedBytes) throw new IOException("original file exceeded its finite declared resource budget");
                digest.update(chunk, 0, read);
            }
            if (count != expectedBytes) throw new IOException("short original file hash read");
        }
        return HexFormat.of().formatHex(digest.digest());
    }
    private static MessageDigest digest() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("JDK SHA-256 unavailable", impossible); }
    }
    private static Observation nativeObservation(Scope scope) {
        var self = WindowsJobProcess.observeLiveProcess(ProcessHandle.current().pid()).identity();
        var owner = WindowsJobProcess.observeLiveProcess(scope.ownerProcess().pid()).identity();
        if (ProcessHandle.current().parent().map(ProcessHandle::pid).orElse(-1L) != owner.pid()) throw unavailable("original Root Owner process unavailable", null);
        return new Observation(WindowsJobProcess.currentMachineId(), process(owner), process(self));
    }
    private static boolean sameReference(ControlBuild.FileRef actual, ControlBuild.FileRef expected) {
        return Path.of(actual.path()).normalize().equals(Path.of(expected.path()).normalize()) && actual.bytes() == expected.bytes() && actual.sha256().equals(expected.sha256());
    }
    private static ProcessIdentity process(WindowsJobProcess.ProcessIdentity value) {
        return new ProcessIdentity(value.pid(), value.creationFiletimeDecimal(), Path.of(value.executable()));
    }
    private static ProjectionProtocolException unavailable(String message, Throwable cause) {
        var error = new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, message);
        if (cause != null) error.initCause(cause); return error;
    }
}
