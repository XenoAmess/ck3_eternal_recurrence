package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;

/** Finite exact input table with the same native birth/hash observations used by SharedOwnedCommand. */
public final class BoundedSourceInputGuard {
    public static final String SCHEMA = "xar.bounded-source-input-manifest/v1";
    public static final int MAX_FILES = 1024;
    public static final long MAX_LOGICAL_BYTES = 64L << 20;
    public static final int MAX_MANIFEST_BYTES = 256 << 10;
    private BoundedSourceInputGuard() { }

    public record Manifest(String schema, String machineId, String taskOwner, String observedAtUtc,
            String reviewAtUtc, List<FileRef> files) {
        public Manifest {
            if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{0,127}")
                    || "unknown".equals(machineId) || taskOwner == null || !taskOwner.matches("/root(?:/[a-z0-9_]+)*")
                    || observedAtUtc == null || reviewAtUtc == null || files == null || files.isEmpty()
                    || files.size() > MAX_FILES) throw new IllegalArgumentException("Finite versioned same-machine input manifest required");
            Instant observed = Instant.parse(observedAtUtc), review = Instant.parse(reviewAtUtc);
            if (!observed.toString().equals(observedAtUtc) || !review.toString().equals(reviewAtUtc)
                    || !review.isAfter(observed)) throw new IllegalArgumentException("Canonical finite UTC observation/review required");
            files = canonicalInputs(files);
            long total = 0;
            for (FileRef file : files) total = Math.addExact(total, file.bytes());
            if (total > MAX_LOGICAL_BYTES) throw new IllegalArgumentException("Input table exceeds finite logical byte bound");
        }
    }

    /** DATA only. Successful closure is observed by the owning process, not minted by this record. */
    public record Receipt(String schema, String machineId, String taskOwner, FileRef manifestRef,
            int files, long logicalBytes, String postcheck, List<Witness> observations) {
        public Receipt { observations = List.copyOf(observations); }
    }

    /** In-memory preparation inputs only: no caller-supplied observed timestamp or machine identity. */
    public record PreparationRequest(Path target, String taskOwner, Instant reviewAt, List<FileRef> files) {
        public PreparationRequest {
            Objects.requireNonNull(target); Objects.requireNonNull(reviewAt); Objects.requireNonNull(files);
            if (!target.isAbsolute() || !target.normalize().equals(target) || taskOwner == null
                    || !taskOwner.matches("/root(?:/[a-z0-9_]+)*") || files.isEmpty())
                throw new IllegalArgumentException("Canonical target, actual owner and finite exact inputs required");
            files = canonicalInputs(files);
            for (FileRef input : files) if (Path.of(input.path()).equals(target))
                throw new IllegalArgumentException("Prepared manifest cannot list itself");
        }
    }

    /** A closed preparation observation; later protected operations must open their own actual Lease. */
    public record PreparedManifest(FileRef manifestRef, Receipt readback) {
        public PreparedManifest {
            Objects.requireNonNull(manifestRef); Objects.requireNonNull(readback);
            if (!manifestRef.equals(readback.manifestRef()) || !"MATCH".equals(readback.postcheck()))
                throw new IllegalArgumentException("Matching complete preparation readback required");
        }
    }

    /** Failed created candidates remain available to the owner; preparation never replaces or removes them. */
    public static final class PreparationRejectedException extends IOException {
        private static final long serialVersionUID = 1L;
        private final String retainedCandidatePath;
        private final long retainedCandidateBytes;
        private final String retainedCandidateSha256;
        private PreparationRejectedException(FileRef retainedCandidate, Exception cause) {
            super("Prepared input manifest rejected; retain original candidate: " + retainedCandidate.path(), cause);
            this.retainedCandidatePath = retainedCandidate.path();
            this.retainedCandidateBytes = retainedCandidate.bytes();
            this.retainedCandidateSha256 = retainedCandidate.sha256();
        }
        public FileRef retainedCandidate() {
            return new FileRef(retainedCandidatePath, retainedCandidateBytes, retainedCandidateSha256);
        }
    }

    /** Same Manifest contract and serializer as the actual guard; no alternate wire schema or parser. */
    public static byte[] encodeManifest(Manifest manifest) throws IOException {
        Objects.requireNonNull(manifest);
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(manifest);
        if (bytes.length > MAX_MANIFEST_BYTES) throw new IOException("Prepared manifest exceeds finite wire bound");
        return bytes;
    }

    /** Prepare once, then read the exact created body through the existing decoder and complete native guard. */
    public static PreparedManifest prepare(PreparationRequest request, Clock clock) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(clock);
        Instant observed = clock.instant();
        requirePreparationWindow(observed, request.reviewAt(), observed);
        Manifest manifest = new Manifest(SCHEMA, WindowsJobProcess.currentMachineId(), request.taskOwner(),
                observed.toString(), request.reviewAt().toString(), request.files());
        Path parent = request.target().getParent();
        if (parent == null || !Files.isDirectory(parent, LinkOption.NOFOLLOW_LINKS) || !parent.toRealPath().equals(parent))
            throw new IOException("Existing canonical ordinary manifest parent required");
        byte[] bytes = encodeManifest(manifest);
        for (FileRef input : manifest.files()) {
            requirePreparationWindow(observed, request.reviewAt(), clock.instant()); input.verify();
        }
        requirePreparationWindow(observed, request.reviewAt(), clock.instant());
        try (var output = FileChannel.open(request.target(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            var buffer = ByteBuffer.wrap(bytes); while (buffer.hasRemaining()) output.write(buffer); output.force(true);
        }
        FileRef retained = FileRef.measure(request.target());
        try {
            byte[] read;
            try (var input = Files.newInputStream(request.target())) { read = input.readNBytes(MAX_MANIFEST_BYTES + 1); }
            if (!manifest.equals(decodeManifest(retained, read)) || !java.util.Arrays.equals(bytes, read))
                throw new IOException("Created manifest differs from its typed preparation inputs");
            requirePreparationWindow(observed, request.reviewAt(), clock.instant());
            Lease lease = open(retained, request.taskOwner());
            try (lease) { lease.requireExactInputs(manifest.files()); lease.requireCurrent(); }
            Receipt receipt = lease.receipt(); retained.verify();
            requirePreparationWindow(observed, request.reviewAt(), clock.instant());
            return new PreparedManifest(retained, receipt);
        } catch (IOException | RuntimeException failure) { throw new PreparationRejectedException(retained, failure); }
    }

    /** A bounded exact pure3 FileRef list is configuration, never a caller-selected machine or observation. */
    public static PreparedManifest prepareFromTable(FileRef inputTable, Path target, String owner,
            String canonicalReviewAtUtc, Clock clock) throws IOException {
        Instant review = canonicalReview(canonicalReviewAtUtc);
        Objects.requireNonNull(inputTable);
        if (inputTable.bytes() < 2 || inputTable.bytes() > MAX_MANIFEST_BYTES)
            throw new IOException("Finite pinned input table required");
        Path tablePath = Path.of(inputTable.path());
        if (!Files.isRegularFile(tablePath, LinkOption.NOFOLLOW_LINKS) || !tablePath.toRealPath().equals(tablePath)
                || Files.size(tablePath) != inputTable.bytes()) throw new IOException("Exact ordinary bounded input table required");
        byte[] bytes;
        try (var input = Files.newInputStream(tablePath)) {
            bytes = input.readNBytes(Math.toIntExact(inputTable.bytes()) + 1);
        }
        verifyReadBytes(inputTable, bytes, MAX_MANIFEST_BYTES);
        if (Files.size(tablePath) != inputTable.bytes()) throw new IOException("Input table length changed after its bounded read");
        inputTable.verify();
        List<FileRef> files = ControlBuild.strictMapper().readerForListOf(FileRef.class).readValue(bytes);
        final PreparationRequest request;
        try { request = new PreparationRequest(target, owner, review, files); }
        catch (IllegalArgumentException | NullPointerException failure) { throw new IOException("Strict bounded preparation input table required", failure); }
        return prepare(request, clock);
    }

    /** CLI: target owner canonicalReview inputTablePath inputTableBytes inputTableSha256. */
    public static void main(String[] args) throws IOException {
        PreparedManifest prepared = prepareArguments(args, Clock.systemUTC());
        // Receipt already has the existing versioned wire and string UTC/native identities; Request is never serialized.
        System.out.write(ControlBuild.strictMapper().writeValueAsBytes(prepared.readback())); System.out.write('\n');
    }

    static PreparedManifest prepareArguments(String[] args, Clock clock) throws IOException {
        if (args == null || args.length != 6) throw new IOException("Expected target owner review table-path table-bytes table-sha256");
        final long bytes;
        try {
            if (args[4] == null || !args[4].matches("0|[1-9][0-9]{0,18}")) throw new NumberFormatException("canonical integer required");
            bytes = Long.parseLong(args[4]);
        } catch (NumberFormatException failure) { throw new IOException("Canonical bounded table byte count required", failure); }
        final FileRef table; final Path target;
        try { table = new FileRef(args[3], bytes, args[5]); target = Path.of(args[0]); }
        catch (IllegalArgumentException | NullPointerException failure) { throw new IOException("Exact CLI table reference and target required", failure); }
        return prepareFromTable(table, target, args[1], args[2], clock);
    }

    private static Instant canonicalReview(String value) throws IOException {
        try {
            Instant review = Instant.parse(value);
            if (!review.toString().equals(value)) throw new IOException("Canonical UTC review string required");
            return review;
        } catch (java.time.DateTimeException | NullPointerException failure) {
            throw new IOException("Canonical UTC review string required", failure);
        }
    }

    private static void requirePreparationWindow(Instant observed, Instant review, Instant now) throws IOException {
        if (!review.isAfter(observed) || now.isBefore(observed) || !now.isBefore(review))
            throw new IOException("Preparation clock outside the finite observed/review interval");
    }

    public static List<FileRef> canonicalInputs(List<FileRef> inputs) {
        Objects.requireNonNull(inputs);
        if (inputs.size() > MAX_FILES) throw new IllegalArgumentException("Finite exact input count required");
        var unique = new LinkedHashMap<String, FileRef>();
        for (FileRef input : inputs) {
            Objects.requireNonNull(input);
            Path path = Path.of(input.path());
            if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IllegalArgumentException("Normalized absolute input path required");
            var canonical = new FileRef(path.toString(), input.bytes(), input.sha256());
            if (unique.putIfAbsent(path.toString().toLowerCase(Locale.ROOT), canonical) != null)
                throw new IllegalArgumentException("Duplicate input path in bounded manifest");
        }
        return unique.values().stream().sorted(Comparator.comparing(FileRef::path)).toList();
    }

    /** Acquire before the protected operation; close performs the complete final native/hash check. */
    public static Lease open(FileRef manifestRef, String expectedOwner) throws IOException {
        Objects.requireNonNull(manifestRef); Objects.requireNonNull(expectedOwner);
        if (manifestRef.bytes() > MAX_MANIFEST_BYTES) throw new IOException("Input manifest exceeds finite wire bound");
        manifestRef.verify();
        Witness manifestWitness = SharedSourceFiles.observe(Path.of(manifestRef.path()));
        if (manifestWitness.source().bytes() != manifestRef.bytes()
                || !manifestWitness.source().sha256().equals(manifestRef.sha256()))
            throw new IOException("Input manifest differs from its original pin");
        byte[] bytes;
        try (var input = Files.newInputStream(Path.of(manifestRef.path()))) {
            bytes = input.readNBytes(Math.toIntExact(manifestRef.bytes()) + 1);
        }
        if (bytes.length > MAX_MANIFEST_BYTES) throw new IOException("Input manifest grew beyond wire bound");
        Manifest manifest = decodeManifest(manifestRef, bytes);
        SharedSourceFiles.assertUnchanged(manifestWitness);
        if (!manifest.machineId().equals(WindowsJobProcess.currentMachineId()) || !manifest.taskOwner().equals(expectedOwner)
                || !Instant.now().isBefore(Instant.parse(manifest.reviewAtUtc()))
                || Instant.now().isBefore(Instant.parse(manifest.observedAtUtc()))) throw new IOException("Input manifest machine/owner/review differs");
        List<Witness> before = new ArrayList<>(); before.add(manifestWitness);
        for (FileRef file : manifest.files()) {
            if (Path.of(file.path()).equals(Path.of(manifestRef.path()))) throw new IOException("Manifest cannot list itself");
            file.verify(); Witness witness = SharedSourceFiles.observe(Path.of(file.path()));
            if (witness.source().bytes() != file.bytes() || !witness.source().sha256().equals(file.sha256()))
                throw new IOException("Input changed while acquiring its native witness");
            before.add(witness);
        }
        Lease lease = new Lease(manifestRef, manifest, before);
        lease.requireCurrent();
        return lease;
    }

    /** Bind the exact bytes actually parsed, including a transient read body between equal file observations. */
    static Manifest decodeManifest(FileRef exact, byte[] bytes) throws IOException {
        verifyReadBytes(exact, bytes, MAX_MANIFEST_BYTES);
        return ControlBuild.strictMapper().readValue(bytes, Manifest.class);
    }

    /** Bind a finite actual read body before any typed metadata decoder consumes it. */
    public static void verifyReadBytes(FileRef exact, byte[] bytes, int maximumBytes) throws IOException {
        Objects.requireNonNull(exact); Objects.requireNonNull(bytes);
        if (maximumBytes < 1 || maximumBytes > MAX_LOGICAL_BYTES) throw new IllegalArgumentException("Finite exact-read byte maximum required");
        final byte[] digest;
        try { digest = java.security.MessageDigest.getInstance("SHA-256").digest(bytes); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
        if (bytes.length > maximumBytes || bytes.length != exact.bytes()
                || !java.util.HexFormat.of().formatHex(digest).equals(exact.sha256()))
            throw new IOException("Actual parsed input-manifest bytes differ from the exact pin");
    }

    public static final class Lease implements AutoCloseable {
        private final FileRef manifestRef;
        private final Manifest manifest;
        private final List<Witness> before;
        private boolean closed, verified;
        private Lease(FileRef manifestRef, Manifest manifest, List<Witness> before) {
            this.manifestRef = manifestRef; this.manifest = manifest; this.before = List.copyOf(before);
        }
        /** The caller derives this complete closure from its original source map/receipt, not its own result. */
        public synchronized void requireExactInputs(List<FileRef> expected) throws IOException {
            if (closed) throw new IOException("Bounded input observation already closed");
            List<FileRef> unique = new ArrayList<>();
            var byPath = new LinkedHashMap<String, FileRef>();
            for (FileRef file : expected) {
                Path path = Path.of(file.path()).toAbsolutePath().normalize();
                var value = new FileRef(path.toString(), file.bytes(), file.sha256());
                var old = byPath.putIfAbsent(path.toString().toLowerCase(Locale.ROOT), value);
                if (old != null && !old.equals(value)) throw new IOException("Conflicting required source pins");
            }
            unique.addAll(byPath.values());
            if (!canonicalInputs(unique).equals(manifest.files())) throw new IOException("Bounded manifest omitted, added or crossed original inputs");
        }
        public synchronized void requireCurrent() throws IOException {
            if (closed || !Instant.now().isBefore(Instant.parse(manifest.reviewAtUtc()))) throw new IOException("Bounded input observation closed or expired");
            for (Witness witness : before) SharedSourceFiles.assertUnchanged(witness);
        }
        @Override public synchronized void close() throws IOException {
            if (closed) return;
            try { requireCurrent(); verified = true; }
            finally { closed = true; }
        }
        /** Exact finite serialization upper bound only; this cannot mint a successful observation. */
        public synchronized long maximumReceiptBytes() throws IOException {
            if (closed) throw new IOException("Reserve metadata before closing the input observation");
            return ControlBuild.strictMapper().writeValueAsBytes(receiptData("PENDING_VERIFICATION")).length;
        }
        private Receipt receiptData(String postcheck) {
            long total = 0; for (FileRef file : manifest.files()) total = Math.addExact(total, file.bytes());
            return new Receipt("xar.bounded-source-input-readback/v1", manifest.machineId(), manifest.taskOwner(),
                    manifestRef, manifest.files().size(), total, postcheck, before);
        }
        public synchronized Receipt receipt() throws IOException {
            if (!closed || !verified) throw new IOException("A successful complete final observation is required");
            return receiptData("MATCH");
        }
    }
}
