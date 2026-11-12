package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.win32.StdCallLibrary;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.WindowsFileIdentity;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** The sole immutable byte publisher. It never writes canonical continuity state. */
public final class ImmutableArtifactStore {
    public static final int MAXIMUM_ARTIFACT_BYTES = WriterContracts.MAX_PIN_BYTES;
    private static final int COMMIT_LIMIT = 65_536;
    private static final int MAX_FILES = 100_000;
    private static final String SCHEMA = "xar.immutable-artifact-commit/v1";
    private static final String PLANNING_SCHEMA = "xar.immutable-artifact-commit/v1-planning";
    public record Config(Path root, Path originalWriterLock, long maximumStoredBytes) {
        public Config {
            root = Objects.requireNonNull(root).toAbsolutePath().normalize();
            originalWriterLock = Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();
            StrictJson.safe(maximumStoredBytes, 1);
            StrictJson.require(root.getParent() != null && originalWriterLock.getParent() != null
                    && root.startsWith(originalWriterLock.getParent()) && !root.equals(originalWriterLock.getParent()),
                    "artifact root must be an owned child of the original writer directory");
        }
    }
    enum Boundary { RAW_DURABLE, RAW_PUBLISHED, COMMIT_DURABLE, COMMIT_PUBLISHED, PLANNING_RAW_PUBLISHED, PLANNING_COMMIT_PUBLISHED }
    @FunctionalInterface interface FaultProbe { void reached(Boundary boundary) throws IOException; }
    private interface FileApi extends StdCallLibrary {
        boolean GetFileInformationByHandleEx(HANDLE handle, int infoClass, Pointer buffer, int bytes);
    }
    private static final class Api { static final FileApi VALUE = Native.load("kernel32", FileApi.class); }
    private record Stamp(String volume, String fileId, String created) {
        static Stamp of(FileIdentity value) { return new Stamp(value.volumeSerialDecimal(), value.fileIdDecimal(), value.creationFiletimeDecimal()); }
        static Stamp of(WindowsFileIdentity value) { return new Stamp(value.volumeSerialDecimal(), value.fileIdDecimal(), value.creationFiletimeDecimal()); }
    }
    private record Commit(Pin payload, Stamp self, boolean planningOrigin) { }
    private enum Publication { DURABLE, PLANNING_OBSERVATION }
    private record Published(LedgerFiles.Document data,LedgerFiles.Document metadata,boolean planningOrigin) { }
    private final Config config;
    private final Stamp rootIdentity;
    private final FileIdentity lockIdentity;
    private final FaultProbe faults;
    private final long allocationUnit;
    private final StorageWriteGuard storage;
    private final boolean sharedAggregateCoversArchive;
    private final boolean readonlyMode;

    @FunctionalInterface interface HistoricalReadAuthority { void require() throws IOException; }
    private final ThreadLocal<HistoricalReads> historicalReads = new ThreadLocal<>();
    void recordHistoricalFailure(Throwable failure) {
        HistoricalReads reads = historicalReads.get();
        if (reads != null) reads.recordFailure(failure);
    }
    @FunctionalInterface private interface OriginalRead<T> { T run() throws IOException; }
    private <T> T historicalRead(OriginalRead<T> operation) throws IOException {
        HistoricalReads reads = historicalReads.get();
        try {
            if (readonlyMode) StorageWriteGuard.requireNoWritesOpen(storage);
            return operation.run();
        }
        catch (IOException failure) {
            if (reads == null) throw failure;
            IOException actual = failure instanceof NoSuchFileException
                    ? new IOException("historical CAS original validation failed; not optional absence", failure) : failure;
            reads.recordFailure(actual); throw actual;
        } catch (RuntimeException | Error failure) {
            if (reads != null) reads.recordFailure(failure);
            throw failure;
        }
    }
    /** Same-call custody; both successful and caught failed reads belong to this exact scope. */
    final class HistoricalReads implements AutoCloseable {
        private final Thread thread = Thread.currentThread();
        private final ContinuityStorePort.Session session;
        private final HistoricalReadAuthority authority;
        private final int maximumEntries;
        private final long maximumBytes;
        private final int maximumHandles;
        private final java.util.Map<ExactRef, PublicationLease> entries = new java.util.LinkedHashMap<>();
        private long bytes;
        private boolean closed;
        private volatile Throwable firstFailure;
        private DependencyTrace dependencyTrace;
        private long publicationAttempts;
        private long heldPathAttempts;
        private long acquisitionAttempts;
        private long retainedPublications;
        private long unretainedPublications;
        private long fallbackAttempts;
        private long entryBoundFallbacks;
        private long handleBoundFallbacks;
        private long byteBoundFallbacks;
        private long largestFallbackExpectedBytes;
        private int peakEntries;
        private long peakBytes;
        private static long nextCount(long value) { return value == Long.MAX_VALUE ? value : value + 1; }
        private void recordRetained() {
            retainedPublications = nextCount(retainedPublications);
            peakEntries = Math.max(peakEntries, entries.size());
            peakBytes = Math.max(peakBytes, bytes);
        }
        private void recordFallback(ExactRef expected) {
            fallbackAttempts = nextCount(fallbackAttempts);
            largestFallbackExpectedBytes = Math.max(largestFallbackExpectedBytes, expected.bytes());
            // Classify the first failed predicate in the unchanged admission order.
            if (entries.size() >= maximumEntries) entryBoundFallbacks = nextCount(entryBoundFallbacks);
            else if (entries.size() * 2 > maximumHandles - 4) handleBoundFallbacks = nextCount(handleBoundFallbacks);
            else if (expected.bytes() > (maximumBytes - bytes) / 2) byteBoundFallbacks = nextCount(byteBoundFallbacks);
        }
        /** Best-effort completed-scope DATA only; never current or custody qualification. */
        void reportDiagnostics(boolean finishSucceeded) {
            if (Thread.currentThread() != thread) return;
            try {
                System.getLogger(ImmutableArtifactStore.class.getName()).log(System.Logger.Level.INFO,
                        "HISTORICAL_CAS_METRICS publication_attempts=" + publicationAttempts
                        + " held_path_attempts=" + heldPathAttempts + " acquisition_attempts=" + acquisitionAttempts
                        + " acquired_retained=" + retainedPublications + " acquired_unretained=" + unretainedPublications
                        + " fallback_attempts=" + fallbackAttempts + " entry_bound=" + entryBoundFallbacks
                        + " handle_bound=" + handleBoundFallbacks + " byte_bound=" + byteBoundFallbacks
                        + " largest_fallback_expected_bytes=" + largestFallbackExpectedBytes
                        + " peak_entries=" + peakEntries + " peak_retained_bytes=" + peakBytes
                        + " maximum_entries=" + maximumEntries + " maximum_retained_bytes=" + maximumBytes
                        + " maximum_handles=" + maximumHandles + " finish_succeeded=" + (finishSucceeded ? 1 : 0)
                        + " validation_failed=" + (firstFailure == null ? 0 : 1));
            } catch (RuntimeException | Error diagnosticFailure) {
                // Only this optional diagnostic outlet is contained. Work and close are outside this try.
            }
        }
        private HistoricalReads(ContinuityStorePort.Session session, int maximumEntries, long maximumBytes,
                int maximumHandles, HistoricalReadAuthority authority) {
            this.session = session; this.maximumEntries = maximumEntries; this.maximumBytes = maximumBytes;
            this.maximumHandles = maximumHandles; this.authority = authority;
        }
        synchronized void recordFailure(Throwable failure) {
            if (firstFailure == null) firstFailure = Objects.requireNonNull(failure);
        }
        void requireActive() throws IOException {
            try {
                if (Thread.currentThread() != thread || closed || historicalReads.get() != this)
                    throw new IOException("historical CAS read scope escaped its exact store/thread/lifetime");
                if (readonlyMode) StorageWriteGuard.requireNoWritesOpen(storage);
                if (firstFailure != null) throw new IOException("historical CAS read scope already failed", firstFailure);
                authority.require(); session.requireWriter(config.originalWriterLock());
            } catch (IOException | RuntimeException | Error failure) { recordFailure(failure); throw failure; }
        }
        /** Reads performed in this exact owned scope only; a snapshot alone grants no replay authority. */
        final class DependencyTrace implements AutoCloseable {
            private final DependencyTrace previous;
            private final java.util.LinkedHashSet<ExactRef> references = new java.util.LinkedHashSet<>();
            private boolean allRetained = true;
            private boolean traceClosed;
            private DependencyTrace(DependencyTrace previous) { this.previous = previous; }
            private void requireCurrent() throws IOException {
                requireActive();
                if (traceClosed || dependencyTrace != this) {
                    IOException failure = new IOException("historical dependency trace is not the current owned trace");
                    recordFailure(failure); throw failure;
                }
            }
            /** Immutable DATA snapshot; final fresh qualification is a separate operation. */
            java.util.Optional<Set<ExactRef>> retainedDependencies() throws IOException {
                requireCurrent();
                if (!allRetained) return java.util.Optional.empty();
                return java.util.Optional.of(java.util.Collections.unmodifiableSet(new java.util.LinkedHashSet<>(references)));
            }
            /** External/pinned/callback dependencies without this store's custody cannot enter a prefix cell. */
            void disqualify() throws IOException {
                requireCurrent(); disqualifyDependencyTraces();
            }
            @Override public void close() throws IOException {
                if (traceClosed) return;
                if (Thread.currentThread() != thread || historicalReads.get() != HistoricalReads.this || dependencyTrace != this) {
                    IOException failure = new IOException("historical dependency trace close crossed its owned nesting or lifetime");
                    recordFailure(failure); throw failure;
                }
                dependencyTrace = previous; traceClosed = true; references.clear();
            }
        }
        /** New traces nest without hiding the inner reads from an outer dependency closure. */
        DependencyTrace traceDependencies() throws IOException {
            requireActive();
            DependencyTrace trace = new DependencyTrace(dependencyTrace); dependencyTrace = trace; return trace;
        }
        /** Mark an actual external dependency without requiring an Archive callback to own the top trace. */
        void disqualifyDependencies() throws IOException { requireActive(); disqualifyDependencyTraces(); }
        private void disqualifyDependencyTraces() {
            for (DependencyTrace trace = dependencyTrace; trace != null; trace = trace.previous) {
                trace.allRetained = false; trace.references.clear();
            }
        }
        private void recordDependency(ExactRef reference, boolean retained) {
            for (DependencyTrace trace = dependencyTrace; trace != null; trace = trace.previous) {
                if (!trace.allRetained) continue;
                if (!retained) { trace.allRetained = false; trace.references.clear(); }
                else trace.references.add(reference);
            }
        }
        private void clearDependencyTraces() {
            while (dependencyTrace != null) {
                DependencyTrace trace = dependencyTrace; dependencyTrace = trace.previous;
                trace.traceClosed = true; trace.references.clear();
            }
        }
        /** No acquisition, byte copy, payload hash, parser or bound change. False means missing custody only. */
        boolean verifyRetainedDependencies(Set<ExactRef> dependencies) throws IOException {
            try {
                requireActive();
                var expected = new java.util.LinkedHashSet<>(Objects.requireNonNull(dependencies));
                var held = new java.util.ArrayList<java.util.Map.Entry<ExactRef, PublicationLease>>(expected.size());
                for (ExactRef reference : expected) {
                    requireReference(Objects.requireNonNull(reference), MAXIMUM_ARTIFACT_BYTES);
                    PublicationLease lease = entries.get(reference);
                    if (lease == null) { recordDependency(reference, false); requireActive(); return false; }
                    held.add(java.util.Map.entry(reference, lease));
                }
                for (var dependency : held) {
                    if (entries.get(dependency.getKey()) != dependency.getValue())
                        throw new IOException("historical dependency custody changed during fresh qualification");
                    readLeasedPublication(dependency.getValue(), dependency.getKey(), MAXIMUM_ARTIFACT_BYTES);
                    // A caller reusing a verified prefix must include its original dependencies in its own trace.
                    recordDependency(dependency.getKey(), true);
                }
                requireActive(); return true;
            } catch (IOException | RuntimeException | Error failure) { recordFailure(failure); throw failure; }
        }
        /** Preserve an already escaping original exception, adding all cleanup errors to it. */
        void finish(Throwable escaping) throws IOException {
            if (Thread.currentThread() != thread) throw new IOException("historical CAS close crossed its owner thread");
            if (closed) return;
            if (historicalReads.get() != this) recordFailure(new IOException("historical CAS scope detached from its exact store"));
            closed = true;
            IOException cleanup = null;
            try {
                for (PublicationLease entry : entries.values()) {
                    try { entry.close(); }
                    catch (IOException | RuntimeException | Error problem) {
                        IOException closing = closeFailure(problem);
                        if (cleanup == null) cleanup = closing; else cleanup.addSuppressed(closing);
                    }
                }
            } finally { clearDependencyTraces(); entries.clear(); bytes = 0; historicalReads.remove(); }
            if (escaping != null) {
                boolean alreadyCarried = false;
                int causeDepth = 0;
                Throwable cause = escaping;
                while (cause != null && causeDepth++ < 16) {
                    if (cause == firstFailure) { alreadyCarried = true; break; }
                    try { cause = cause.getCause(); }
                    catch (Throwable diagnosticFailure) { break; }
                }
                if (firstFailure != null && !alreadyCarried) escaping.addSuppressed(firstFailure);
                if (cleanup != null) escaping.addSuppressed(cleanup);
                return;
            }
            if (firstFailure != null) {
                IOException failure = new IOException("historical CAS validation failed; caught failure cannot grant a result", firstFailure);
                if (cleanup != null) failure.addSuppressed(cleanup);
                throw failure;
            }
            if (cleanup != null) throw cleanup;
        }
        @Override public void close() throws IOException { finish(null); }
    }
    private static final class PublicationLease implements AutoCloseable {
        private final LedgerFiles.LeasedDocument metadata;
        private final LedgerFiles.LeasedDocument data;
        private final Commit bound;
        private PublicationLease(LedgerFiles.LeasedDocument metadata, LedgerFiles.LeasedDocument data, Commit bound) {
            this.metadata = metadata; this.data = data; this.bound = bound;
        }
        @Override public void close() throws IOException { closePair(data, metadata); }
    }
    private static void closePair(LedgerFiles.LeasedDocument data, LedgerFiles.LeasedDocument metadata) throws IOException {
        IOException failure = null;
        if (data != null) try { data.close(); } catch (IOException | RuntimeException | Error problem) { failure = closeFailure(problem); }
        if (metadata != null) try { metadata.close(); } catch (IOException | RuntimeException | Error problem) {
            IOException closing = closeFailure(problem);
            if (failure == null) failure = closing; else failure.addSuppressed(closing);
        }
        if (failure != null) throw failure;
    }
    private static IOException closeFailure(Throwable problem) {
        return problem instanceof IOException failure ? failure : new IOException("historical native cleanup failed", problem);
    }
    HistoricalReads beginHistoricalReads(ContinuityStorePort.Session session, int maximumEntries,
            long maximumBytes, int maximumHandles, HistoricalReadAuthority authority) throws IOException {
        if (readonlyMode) StorageWriteGuard.requireNoWritesOpen(storage);
        Objects.requireNonNull(session); Objects.requireNonNull(authority);
        if (maximumEntries < 1 || maximumEntries > 4096 || maximumBytes < 1 || maximumBytes > 256L * 1024 * 1024
                || maximumHandles < 4 || maximumHandles > 8192)
            throw new IOException("finite historical CAS read bounds required");
        if (historicalReads.get() != null) {
            IOException failure = new IOException("nested historical CAS read scopes are not permitted");
            recordHistoricalFailure(failure); throw failure;
        }
        authority.require(); session.requireWriter(config.originalWriterLock()); checkRoot();
        HistoricalReads result = new HistoricalReads(session, maximumEntries, maximumBytes, maximumHandles, authority);
        historicalReads.set(result);
        return result;
    }
    private Published readLeasedPublication(PublicationLease lease, ExactRef expected, int maximum) throws IOException {
        LedgerFiles.Document metadata = lease.metadata.read();
        if (!lease.bound.payload().reference().equals(expected)) throw new IOException("artifact commit/ref drift");
        LedgerFiles.Document data = lease.data.read();
        if (data.pin().reference().bytes() > maximum) throw new IOException("leased artifact exceeds its current declared bound");
        requirePin(data.pin(), lease.bound.payload()); checkRoot();
        return new Published(data, metadata, lease.bound.planningOrigin());
    }
    private Published acquirePublication(HistoricalReads reads, ExactRef expected, int maximum) throws IOException {
        LedgerFiles.LeasedDocument metadata = null, data = null;
        boolean retained = false;
        Throwable failure = null;
        try {
            metadata = LedgerFiles.lease(commit(expected.sha256()), COMMIT_LIMIT);
            Commit bound = decode(metadata.original());
            if (!bound.payload().reference().equals(expected)) throw new IOException("artifact commit/ref drift");
            data = LedgerFiles.lease(bound.payload().reference(), maximum);
            PublicationLease lease = new PublicationLease(metadata, data, bound);
            Published actual = readLeasedPublication(lease, expected, maximum);
            long retainedBytes = Math.addExact(data.retainedBytes(), metadata.retainedBytes());
            reads.requireActive();
            if (retainedBytes <= reads.maximumBytes - reads.bytes) {
                reads.entries.put(expected, lease); reads.bytes += retainedBytes; retained = true;
                reads.recordRetained();
            } else {
                reads.unretainedPublications = HistoricalReads.nextCount(reads.unretainedPublications);
            }
            return actual;
        } catch (IOException | RuntimeException | Error problem) { failure = problem; throw problem; }
        finally {
            if (!retained) try { closePair(data, metadata); }
            catch (IOException closing) { if (failure != null) failure.addSuppressed(closing); else throw closing; }
        }
    }

    public ImmutableArtifactStore(Config config, StorageWriteGuard storage) throws IOException {
        this(config, storage, boundary -> { });
    }
    ImmutableArtifactStore(Config config, StorageWriteGuard storage, FaultProbe faults) throws IOException {
        this(config, storage, faults, false);
    }
    private ImmutableArtifactStore(Config config, StorageWriteGuard storage, FaultProbe faults, boolean readonlyMode) throws IOException {
        this.config = Objects.requireNonNull(config); this.storage = Objects.requireNonNull(storage);
        this.faults = Objects.requireNonNull(faults);
        this.readonlyMode = readonlyMode;
        if (readonlyMode) {
            StorageWriteGuard.requireNoWritesOpen(storage);
            lockIdentity = LedgerFiles.identity(config.originalWriterLock());
            rootIdentity = directoryStamp(config.root());
            allocationUnit = 0; // No allocation unit was observed; publication is forbidden.
            sharedAggregateCoversArchive = false;
            return;
        }
        if (StorageWriteGuard.isNoWrites(storage)) throw new IOException("mutable store cannot use the noWrites denial guard");
        // The local CAS cap and the shared package authority must both admit initialization before any mkdir.
        if (config.maximumStoredBytes() < 4096) throw new IOException("archive budget cannot cover its directory guard");
        lockIdentity = LedgerFiles.identity(config.originalWriterLock());
        storage.requireInitialization(config.originalWriterLock(), List.of(config.root()));
        boolean alreadyHeld = writerLockHeldByCurrentThread();
        try (WindowsLedgerLock held = alreadyHeld ? null : WindowsLedgerLock.acquire(config.originalWriterLock())) {
            if (!lockIdentity.equals(LedgerFiles.identity(config.originalWriterLock())))
                throw new IOException("original archive writer lock identity changed before initialization");
            initializeDirectories();
            rootIdentity = directoryStamp(config.root());
            allocationUnit = Files.getFileStore(config.root()).getBlockSize();
            if (allocationUnit < 1 || allocationUnit > 1_048_576)
                throw new IOException("finite observed allocation unit required");
            var enforced = storage.enforcedAggregateMaximumBytes(config.originalWriterLock(), config.root());
            sharedAggregateCoversArchive = enforced.isPresent() && enforced.getAsLong() > 0 && enforced.getAsLong() <= config.maximumStoredBytes();
            reserve(0);
        }
    }
    public static ImmutableArtifactStore readOnlyExisting(Config config, StorageWriteGuard storage) throws IOException {
        return new ImmutableArtifactStore(config, storage, boundary -> { }, true);
    }
    public Path originalWriterLock() { return config.originalWriterLock(); }
    /** Writer and archive must hold this identical required package allocation authority. */
    public StorageWriteGuard storageGuard() { return storage; }

    private void initializeDirectories() throws IOException {
        List<Path> missing = new ArrayList<>(); Path cursor = config.root();
        Path owned = config.originalWriterLock().getParent();
        while (!Files.exists(cursor, LinkOption.NOFOLLOW_LINKS)) {
            if (!cursor.startsWith(owned) || cursor.equals(owned) || missing.size() >= 64)
                throw new IOException("bounded archive initialization escaped the original writer directory");
            missing.add(cursor); cursor = cursor.getParent();
        }
        directoryStamp(cursor);
        if (missing.isEmpty()) return;
        var mutations = new ArrayList<StorageWriteGuard.Mutation>();
        for (int index = missing.size() - 1; index >= 0; index--)
            mutations.add(new StorageWriteGuard.DirectoryCreate(missing.get(index)));
        storage.write(new StorageWriteGuard.WritePlan(config.originalWriterLock(), mutations), () -> {
            for (var mutation : mutations) storage.write(single(mutation), () -> {
                directoryStamp(mutation.target().getParent());
                Files.createDirectory(mutation.target()); directoryStamp(mutation.target()); return null;
            });
            return null;
        });
    }

    private StorageWriteGuard.WritePlan single(StorageWriteGuard.Mutation mutation) {
        return new StorageWriteGuard.WritePlan(config.originalWriterLock(), List.of(mutation));
    }
    /** Actual, revalidated identity; this is not a caller-supplied custody boolean. */
    public record StoreIdentity(Path root, String volumeSerialDecimal, String fileIdDecimal,
            String creationFiletimeDecimal, Path originalWriterLock, FileIdentity originalWriterLockIdentity) {
        public StoreIdentity {
            Objects.requireNonNull(root); Objects.requireNonNull(originalWriterLock); Objects.requireNonNull(originalWriterLockIdentity);
            for (String value : java.util.List.of(volumeSerialDecimal, fileIdDecimal, creationFiletimeDecimal))
                StrictJson.require(value.matches("0|[1-9][0-9]*"), "canonical store native identity required");
        }
    }
    public StoreIdentity identity() throws IOException {
        checkRoot();
        if (!lockIdentity.equals(LedgerFiles.identity(config.originalWriterLock()))) throw new IOException("original archive writer lock identity changed");
        return new StoreIdentity(config.root(), rootIdentity.volume(), rootIdentity.fileId(), rootIdentity.created(),
                config.originalWriterLock(), lockIdentity);
    }
    /** This is custody lookup only; it never acquires a lock or grants writer authority. */
    public boolean writerLockHeldByCurrentThread() {
        try { WindowsLedgerLock.requireHeld(config.originalWriterLock()); return true; }
        catch (IOException absent) { return false; }
    }
    public Pin publish(ExactRef original, int maximumBytes) throws IOException {
        requireWrite(); LedgerFiles.Document source = LedgerFiles.exact(Objects.requireNonNull(original), limit(maximumBytes));
        Pin published = publish(source.bytes(), maximumBytes); LedgerFiles.verify(source.pin()); return published;
    }
    public Pin publish(byte[] original,int maximumBytes)throws IOException {
        return publish(original,maximumBytes,Publication.DURABLE);
    }
    public Pin publishPlanningRead(byte[] original,int maximumBytes)throws IOException {
        return publish(original,maximumBytes,Publication.PLANNING_OBSERVATION);
    }
    private Pin publish(byte[] original, int maximumBytes,Publication publication) throws IOException {
        requireWrite(); Objects.requireNonNull(original); int maximum = limit(maximumBytes);
        if (original.length > maximum) throw new IOException("actual artifact exceeds its declared bound");
        byte[] bytes = original.clone(); String digest = LedgerFiles.sha(bytes);
        Path payload = payload(digest), commit = commit(digest);
        if (exists(commit)) {
            Published existing=readPublication(new ExactRef(payload.toString(),bytes.length,digest),maximum);
            Pin result=matching(bytes,existing.data());
            if(publication==Publication.DURABLE&&existing.planningOrigin())forcePublication(existing);
            return result;
        }
        Path pending = config.root().resolve(digest + ".data.pending");
        Path pendingCommit = config.root().resolve(digest + ".commit.pending");
        long metadataUpper = Math.min(COMMIT_LIMIT, Math.addExact(4096L,
                Math.multiplyExact(6L, payload.toString().getBytes(StandardCharsets.UTF_8).length)));
        long needed = (!exists(payload) && !exists(pending) ? allocatedUpper(bytes.length) : 0)
                + (!exists(pendingCommit) ? allocatedUpper(metadataUpper) : 0);
        reserve(needed);
        var mutations = new ArrayList<StorageWriteGuard.Mutation>();
        if (!exists(payload)) {
            if (!exists(pending)) mutations.add(new StorageWriteGuard.FileCreate(pending, bytes.length));
            mutations.add(new StorageWriteGuard.FileRename(pending, payload, false));
        }
        if (!exists(pendingCommit)) {
            mutations.add(new StorageWriteGuard.FileCreate(pendingCommit, 0));
            mutations.add(new StorageWriteGuard.FileFillExistingEmpty(pendingCommit, metadataUpper));
        }
        mutations.add(new StorageWriteGuard.FileRename(pendingCommit, commit, false));
        // Commit bytes contain their own native FileID. Quote their finite upper before the empty CREATE_NEW,
        // then consume each phase under this one parent reservation; a failed phase stays storage UNKNOWN.
        return storage.write(new StorageWriteGuard.WritePlan(config.originalWriterLock(), mutations),
                () -> publishReserved(bytes, maximum, digest, metadataUpper,publication));
    }
    private Pin publishReserved(byte[] bytes,int maximum,String digest,long metadataUpper,Publication publication)throws IOException {
        requireWrite();
        Path payload=payload(digest),commit=commit(digest);
        Path pending=config.root().resolve(digest+".data.pending"),pendingCommit=config.root().resolve(digest+".commit.pending");
        boolean wroteRaw=false;
        if(!exists(payload)) {
            if(!exists(pending)){writeNew(pending,bytes,publication);wroteRaw=true;}
            LedgerFiles.Document staged=LedgerFiles.exact(new ExactRef(pending.toString(),bytes.length,digest),maximum);
            if(publication==Publication.DURABLE){if(!wroteRaw)forceFile(pending);faults.reached(Boundary.RAW_DURABLE);}
            movePublished(pending,payload,publication);
            if(!Stamp.of(staged.pin().identity()).equals(Stamp.of(LedgerFiles.identity(payload))))throw new IOException("raw artifact identity changed during publication");
        }else if(publication==Publication.DURABLE)forceFile(payload);
        Pin pin=LedgerFiles.exact(new ExactRef(payload.toString(),bytes.length,digest),maximum).pin();
        faults.reached(publication==Publication.DURABLE?Boundary.RAW_PUBLISHED:Boundary.PLANNING_RAW_PUBLISHED);
        boolean wroteCommit=false;
        if(!exists(pendingCommit)) {
            Stamp self=storage.write(single(new StorageWriteGuard.FileCreate(pendingCommit,0)),()->{
                Files.createFile(pendingCommit);return Stamp.of(LedgerFiles.identity(pendingCommit));
            });
            byte[] document=encode(new Commit(pin,self,publication==Publication.PLANNING_OBSERVATION));reserve(allocatedUpper(document.length));
            if(document.length>metadataUpper)throw new IOException("actual commit exceeds its original finite quote");
            storage.write(single(new StorageWriteGuard.FileFillExistingEmpty(pendingCommit,metadataUpper)),()->{writeExistingEmpty(pendingCommit,document,self,publication);return null;});
            wroteCommit=true;
        }
        Commit prepared=decode(LedgerFiles.read(pendingCommit,COMMIT_LIMIT));
        requirePin(prepared.payload(),pin);verifyRaw(prepared.payload(),maximum);
        Publication commitPublication=publication;
        if(publication==Publication.DURABLE) {
            if(!wroteCommit)forceFile(pendingCommit);
            faults.reached(Boundary.COMMIT_DURABLE);
        }else if(!prepared.planningOrigin()) {
            // An interrupted historical strong publication keeps its strong marker and receives a real barrier.
            forceFile(payload);forceFile(pendingCommit);commitPublication=Publication.DURABLE;
            faults.reached(Boundary.COMMIT_DURABLE);
        }
        movePublished(pendingCommit,commit,commitPublication);
        faults.reached(commitPublication==Publication.DURABLE?Boundary.COMMIT_PUBLISHED:Boundary.PLANNING_COMMIT_PUBLISHED);
        Pin result=matching(bytes,readCommitted(pin.reference(),maximum));reserve(0);return result;
    }
    /** No creation, repair, overwrite, acquisition or implicit preserve is allowed here. */
    public Pin referenceOf(byte[] original, int maximumBytes) throws IOException {
        return historicalRead(() -> {
            Objects.requireNonNull(original); int maximum = limit(maximumBytes);
            if (original.length > maximum) throw new IOException("lookup artifact exceeds declared bound");
            String digest = LedgerFiles.sha(original);
            return matching(original, readCommitted(new ExactRef(payload(digest).toString(), original.length, digest), maximum));
        });
    }
    /** Read-only exact CAS lookup by the original producer's digest and byte length. No scan or repair. */
    public Pin referenceOf(String sha256, long bytes, int maximumBytes) throws IOException {
        return historicalRead(() -> {
            requireDigest(sha256); StrictJson.safe(bytes, 0); int maximum = limit(maximumBytes);
            if (bytes > maximum) throw new IOException("lookup artifact exceeds declared bound");
            return readCommitted(new ExactRef(payload(sha256).toString(), bytes, sha256), maximum).pin();
        });
    }
    public byte[] read(Pin expected, int maximumBytes) throws IOException {
        return historicalRead(() -> {
            Objects.requireNonNull(expected); LedgerFiles.Document value = readCommitted(expected.reference(), limit(maximumBytes));
            requirePin(value.pin(), expected); return value.bytes();
        });
    }
    public byte[] read(ExactRef expected, int maximumBytes) throws IOException {
        return historicalRead(() -> {
            return readCommitted(Objects.requireNonNull(expected), limit(maximumBytes)).bytes();
        });
    }
    /** One actual committed read retains its verified Pin and detached bytes for the same-package archive. */
    LedgerFiles.Document readOriginal(ExactRef expected, int maximumBytes) throws IOException {
        return historicalRead(() -> {
            return readCommitted(Objects.requireNonNull(expected), limit(maximumBytes));
        });
    }
    /** Reject foreign paths and invalid bounds before a same-writer caller attempts to capture a Pin.
     * This reads no payload and grants no committed-object or file-identity authority.
     */
    public void requireReference(ExactRef expected, int maximumBytes) throws IOException {
        historicalRead(() -> {
            Objects.requireNonNull(expected); int maximum = limit(maximumBytes); checkRoot();
            if (expected.bytes() > maximum || !Path.of(expected.path()).toAbsolutePath().normalize().equals(payload(expected.sha256())))
                throw new IOException("artifact reference is outside its exact content-addressed root or declared bound");
            return null;
        });
    }
    private LedgerFiles.Document readCommitted(ExactRef expected,int maximum)throws IOException {return readPublication(expected,maximum).data();}
    private Published readPublication(ExactRef expected,int maximum)throws IOException {
        return historicalRead(() -> {
            requireReference(expected,maximum);
            HistoricalReads reads = historicalReads.get();
            if (reads != null) {
                reads.requireActive();
                reads.publicationAttempts = HistoricalReads.nextCount(reads.publicationAttempts);
                PublicationLease held = reads.entries.get(expected);
                if (held != null) {
                    reads.heldPathAttempts = HistoricalReads.nextCount(reads.heldPathAttempts);
                    Published actual = readLeasedPublication(held, expected, maximum);
                    reads.recordDependency(expected, true); return actual;
                }
                // Reserve two transient qualification handles in addition to both new custody handles.
                if (reads.entries.size() < reads.maximumEntries && reads.entries.size() * 2 <= reads.maximumHandles - 4
                        && expected.bytes() <= (reads.maximumBytes - reads.bytes) / 2) {
                    reads.acquisitionAttempts = HistoricalReads.nextCount(reads.acquisitionAttempts);
                    Published actual = acquirePublication(reads, expected, maximum);
                    reads.recordDependency(expected, reads.entries.containsKey(expected)); return actual;
                }
                // Attempt single-pair retirement if admission is blocked by entry or handle limits
                // and the oldest entry can free enough bytes for the new request.
                if (reads.entries.size() >= reads.maximumEntries || reads.entries.size() * 2 > reads.maximumHandles - 4) {
                    if (!reads.entries.isEmpty()) {
                        var oldestKey = reads.entries.keySet().iterator().next();
                        var oldestLease = reads.entries.get(oldestKey);
                        long freedBytes = oldestLease.metadata.retainedBytes() + oldestLease.data.retainedBytes();
                        // Check if freeing the oldest entry allows the new request to fit
                        if (expected.bytes() <= (reads.maximumBytes - (reads.bytes - freedBytes)) / 2) {
                            // Close the lease first; failure poisons the scope and prevents removal
                            oldestLease.close();
                            // Remove from map and adjust accounting only after successful close
                            reads.entries.remove(oldestKey);
                            reads.recordDependency(oldestKey, false); // Retired custody cannot support a new prefix cell.
                            reads.bytes -= freedBytes;
                            // Retry admission with updated state
                            if (reads.entries.size() < reads.maximumEntries && reads.entries.size() * 2 <= reads.maximumHandles - 4
                                    && expected.bytes() <= (reads.maximumBytes - reads.bytes) / 2) {
                                reads.acquisitionAttempts = HistoricalReads.nextCount(reads.acquisitionAttempts);
                                return acquirePublication(reads, expected, maximum);
                            }
                        }
                    }
                }
                reads.recordFallback(expected);
            }
            LedgerFiles.Document metadata=LedgerFiles.read(commit(expected.sha256()),COMMIT_LIMIT);
            Commit bound=decode(metadata);if(!bound.payload().reference().equals(expected))throw new IOException("artifact commit/ref drift");
            Published actual = new Published(verifyRaw(bound.payload(),maximum),metadata,bound.planningOrigin());
            if (reads != null) reads.recordDependency(expected, false);
            return actual;
        });
    }
    private LedgerFiles.Document verifyRaw(Pin pin, int maximum) throws IOException {
        // Same fresh read and validation order as LedgerFiles.exact/read, with one final payload copy.
        Path path = Path.of(pin.reference().path());
        var observed = IdentityBearingFileAttributes.readBoundedWindows(path, maximum);
        BasicFileAttributes after = observed.attributes();
        WindowsFileIdentity key = (WindowsFileIdentity) after.fileKey();
        FileIdentity identity = new FileIdentity(key.volumeSerialDecimal(), key.fileIdDecimal(), key.creationFiletimeDecimal(),
                after.lastModifiedTime().toInstant().toString(), after.size());
        byte[] raw = observed.bytes();
        Pin actual = new Pin(new ExactRef(path.toAbsolutePath().normalize().toString(), raw.length, LedgerFiles.sha(raw)), identity);
        if (actual.reference().bytes() != pin.reference().bytes() || !actual.reference().sha256().equals(pin.reference().sha256())
                || !Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(Path.of(actual.reference().path())))
            throw new IOException("named source bytes/SHA/path changed: path=" + pin.reference().path()
                    + ", expected_bytes=" + pin.reference().bytes() + ", actual_bytes=" + actual.reference().bytes()
                    + ", expected_sha256=" + pin.reference().sha256() + ", actual_sha256=" + actual.reference().sha256());
        LedgerFiles.Document value = new LedgerFiles.Document(new Pin(pin.reference(), actual.identity()), raw);
        requirePin(value.pin(), pin); return value;
    }
    private static Pin matching(byte[] expected, LedgerFiles.Document actual) throws IOException {
        if (!Arrays.equals(expected, actual.bytes())) throw new IOException("same content key has different bytes"); return actual.pin();
    }
    private static void requirePin(Pin actual, Pin expected) throws IOException {
        if (!actual.equals(expected)) throw new IOException("artifact native FileID/content identity changed");
    }
    private void requireWrite() throws IOException {
        if (readonlyMode) {
            IOException failure = new IOException("immutable artifact store is in readonly mode; publication is denied");
            recordHistoricalFailure(failure); throw failure;
        }
        HistoricalReads reads = historicalReads.get();
        if (reads != null) {
            reads.requireActive();
            IOException failure = new IOException("publication cannot mutate an active historical read scope");
            reads.recordFailure(failure); throw failure;
        }
        WindowsLedgerLock.requireHeld(config.originalWriterLock()); checkRoot();
        if (!lockIdentity.equals(LedgerFiles.identity(config.originalWriterLock()))) throw new IOException("original writer lock identity drift");
    }
    private void checkRoot() throws IOException {
        if (readonlyMode) StorageWriteGuard.requireNoWritesOpen(storage);
        if (!rootIdentity.equals(directoryStamp(config.root()))) throw new IOException("artifact root native identity changed");
    }
    private Path payload(String digest) { requireDigest(digest); return config.root().resolve(digest + ".bin"); }
    private Path commit(String digest) { requireDigest(digest); return config.root().resolve(digest + ".commit.json"); }
    private static int limit(int maximum) {
        StrictJson.require(maximum > 0 && maximum <= MAXIMUM_ARTIFACT_BYTES, "finite immutable artifact bound required"); return maximum;
    }
    private static boolean exists(Path path) throws IOException {
        try { LedgerFiles.identity(path); return true; }
        catch (NoSuchFileException absent) { LedgerFiles.requireAbsent(path); return false; }
    }
    private static Stamp directoryStamp(Path root) throws IOException {
        BasicFileAttributes value = IdentityBearingFileAttributes.read(root);
        if (!value.isDirectory() || value.isSymbolicLink() || !(value.fileKey() instanceof WindowsFileIdentity identity))
            throw new IOException("ordinary native identity-bearing archive directory required");
        return Stamp.of(identity);
    }
    private long allocatedUpper(long bytes) { return Math.multiplyExact(Math.floorDiv(Math.addExact(bytes, allocationUnit - 1), allocationUnit), allocationUnit); }
    private void reserve(long additionalNativeBytes) throws IOException {
        if (sharedAggregateCoversArchive) return;
        if (Math.addExact(retainedNativeBytes(), additionalNativeBytes) > config.maximumStoredBytes())
            throw new IOException("actual-length archive budget exhausted; partial originals retained");
    }
    /** Counts every retained final/pending leaf, without reading bodies or assuming old failures are free. */
    public long retainedNativeBytes() throws IOException {
        checkRoot(); long total = 4096; int files = 0;
        try (DirectoryStream<Path> entries = Files.newDirectoryStream(config.root())) {
            for (Path entry : entries) {
                if (++files > MAX_FILES) throw new IOException("finite archive inventory exhausted");
                FileIdentity before = LedgerFiles.identity(entry);
                HANDLE handle = Kernel32.INSTANCE.CreateFile(winPath(entry), 0x80, 3, null, 3, 0x02200000, null);
                if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("archive allocation open Win32=" + Native.getLastError());
                try (Memory info = new Memory(24)) {
                    if (!Api.VALUE.GetFileInformationByHandleEx(handle, 1, info, 24))
                        throw new IOException("archive allocation query Win32=" + Native.getLastError());
                    long allocated = info.getLong(0), logical = info.getLong(8);
                    if (allocated < 0 || logical != before.bytes() || !before.equals(LedgerFiles.identity(entry)))
                        throw new IOException("archive native allocation identity drift");
                    total = Math.addExact(total, allocated);
                } finally { Kernel32.INSTANCE.CloseHandle(handle); }
            }
        }
        checkRoot(); return total;
    }
    private static String winPath(Path path) {
        String value = path.toAbsolutePath().normalize().toString();
        return value.startsWith("\\\\") ? "\\\\?\\UNC\\" + value.substring(2) : "\\\\?\\" + value;
    }
    private void writeNew(Path path, byte[] bytes,Publication publication) throws IOException {
        storage.write(single(new StorageWriteGuard.FileCreate(path, bytes.length)), () -> {
            Files.createFile(path); Stamp stamp = Stamp.of(LedgerFiles.identity(path));
            writeExistingEmpty(path, bytes, stamp,publication); return null;
        });
    }
    private static void writeExistingEmpty(Path path, byte[] bytes, Stamp stamp,Publication publication) throws IOException {
        if (LedgerFiles.identity(path).bytes() != 0) throw new IOException("partial artifact may not be overwritten");
        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.WRITE)) {
            if (!stamp.equals(Stamp.of(LedgerFiles.identity(path)))) throw new IOException("staging native identity changed");
            ByteBuffer buffer = ByteBuffer.wrap(bytes); while (buffer.hasRemaining()) channel.write(buffer); if(publication==Publication.DURABLE)channel.force(true);
        }
        if (!stamp.equals(Stamp.of(LedgerFiles.identity(path)))) throw new IOException("durable staging native identity changed");
        // publishReserved reads this staging file once against the expected payload or commit before its durable boundary.
    }
    private static byte[] encode(Commit commit) {
        ObjectNode row = StrictJson.object(); row.put("schema", commit.planningOrigin() ? PLANNING_SCHEMA : SCHEMA);
        row.set("payload", commit.payload().reference().toJson());
        row.set("payload_identity", identity(commit.payload().identity()));
        row.set("commit_identity", stamp(commit.self()));
        return StrictJson.canonical(row);
    }
    private static Commit decode(LedgerFiles.Document document) throws IOException {
        ObjectNode row = StrictJson.object(StrictJson.parse(document.bytes()), Set.of("schema", "payload", "payload_identity", "commit_identity"));
        String schema = StrictJson.text(row.get("schema"));
        StrictJson.require(schema.equals(SCHEMA) || schema.equals(PLANNING_SCHEMA), "exact immutable commit schema required");
        boolean planningOrigin = schema.equals(PLANNING_SCHEMA);
        Stamp self = stamp(row.get("commit_identity"));
        if (!self.equals(Stamp.of(document.pin().identity()))) throw new IOException("commit replaced under same name/FileID");
        return new Commit(new Pin(ExactRef.fromJson(row.get("payload")), identity(row.get("payload_identity"))), self, planningOrigin);
    }
    private static ObjectNode identity(FileIdentity value) {
        ObjectNode row = stamp(Stamp.of(value)); row.put("modified", value.modifiedInstant()); row.put("bytes", value.bytes()); return row;
    }
    private static FileIdentity identity(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("volume", "file_id", "created", "modified", "bytes"));
        return new FileIdentity(text(row, "volume"), text(row, "file_id"), text(row, "created"), text(row, "modified"),
                StrictJson.integer(row.get("bytes"), 0, MAXIMUM_ARTIFACT_BYTES));
    }
    private static ObjectNode stamp(Stamp value) {
        ObjectNode row = StrictJson.object(); row.put("volume", value.volume()); row.put("file_id", value.fileId()); row.put("created", value.created()); return row;
    }
    private static Stamp stamp(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("volume", "file_id", "created"));
        Stamp result = new Stamp(text(row, "volume"), text(row, "file_id"), text(row, "created"));
        for (String field : java.util.List.of(result.volume(), result.fileId(), result.created())) {
            boolean canonical = !field.isEmpty();
            if (canonical) {
                char first = field.charAt(0);
                canonical = first == '0' ? field.length() == 1 : first >= '1' && first <= '9';
                for (int index = 1; canonical && index < field.length(); index++) {
                    char digit = field.charAt(index);
                    canonical = digit >= '0' && digit <= '9';
                }
            }
            StrictJson.require(canonical, "canonical decimal native FileID required");
        }
        return result;
    }
    private static String text(ObjectNode row, String name) { return StrictJson.text(row.get(name)); }
    private void forceFile(Path path) throws IOException {
        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.WRITE)) {
            channel.force(true);
        }
    }
    public void requireDurable(ExactRef reference,int maximumBytes)throws IOException {
        requireWrite();Published actual=readPublication(Objects.requireNonNull(reference),limit(maximumBytes));
        if(actual.planningOrigin())forcePublication(actual);
    }
    private void forcePublication(Published actual)throws IOException {
        forceFile(Path.of(actual.data().pin().reference().path()));
        forceFile(Path.of(actual.metadata().pin().reference().path()));
        LedgerFiles.verify(actual.data().pin());LedgerFiles.verify(actual.metadata().pin());
    }
    private void movePublished(Path staging,Path target,Publication publication)throws IOException {
        if(publication==Publication.DURABLE)LedgerFiles.moveCreateNew(storage,config.originalWriterLock(),staging,target);
        else LedgerFiles.moveCreateNewNoForce(storage,config.originalWriterLock(),staging,target);
    }
}
