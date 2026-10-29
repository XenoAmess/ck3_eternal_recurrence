package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import java.io.ByteArrayOutputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.function.LongSupplier;
import java.util.function.Supplier;

/** Monotonic, bounded source assembly. Every conflict destroys the session; commit consumes before native submission. */
public final class CoaUploads {
    public static final int MAX_CHUNK = 48 * 1024, MAX_CHUNKS = 32, MAX_SESSIONS = 2, MAX_RESERVED = 768 * 1024;
    private static final long TTL_NANOS = 60_000_000_000L;
    public record Intent(BigInteger expectedRevision, boolean apply, String expectedGameVersion, String expectedExecutableSha256) {
        public Intent { u64(expectedRevision, false); text(expectedGameVersion, 32); expectedExecutableSha256 = digest(expectedExecutableSha256); }
        public void requireSupportedBuild() { require(expectedGameVersion.equals(GAME_VERSION) && expectedExecutableSha256.equalsIgnoreCase(EXE_SHA256), "unsupported exact CoA build"); }
    }
    public record Begin(int totalBytes, String sourceSha256, int chunkCount, String chunkEncoding, Intent intent) {
        public Begin { require(totalBytes > 0 && totalBytes <= V2_MAX_BYTES, "total_bytes outside range"); sourceSha256 = digest(sourceSha256);
            require(chunkCount > 0 && chunkCount <= MAX_CHUNKS && chunkCount * MAX_CHUNK >= totalBytes, "chunk count cannot carry payload");
            require("base64".equals(chunkEncoding), "chunk_encoding must be base64"); Objects.requireNonNull(intent); }
    }
    public record SessionKey(String uploadId, BigInteger generation) {
        public SessionKey { require(uploadId != null && uploadId.matches("[0-9a-f]{32}"), "invalid upload ID"); u64(generation, true); }
    }
    public record Commit(SessionKey key, int chunkCount, String sourceSha256, Intent intent) {
        public Commit { Objects.requireNonNull(key); require(chunkCount > 0 && chunkCount <= MAX_CHUNKS, "chunk count outside range"); sourceSha256 = digest(sourceSha256); Objects.requireNonNull(intent); }
    }
    /** Deeper chunk validation deliberately occurs inside append, after locating the session, so malformed input invalidates it. */
    public record Append(Commit commit, int chunkIndex, String chunkEncoding, int chunkBytes, String chunkSha256, String chunkBase64) {
        public Append { Objects.requireNonNull(commit); }
    }
    public enum Status { RECEIVING, READY, COMMITTED, ABORTED }
    public record Receipt(Status status, SessionKey key, int totalBytes, String sourceSha256, int chunkCount,
            int receivedChunks, int receivedBytes, Intent intent, Binding binding) {
        public Receipt { Objects.requireNonNull(status); Objects.requireNonNull(key); Objects.requireNonNull(intent); Objects.requireNonNull(binding); }
        public String schema() { return "coat-of-arms-source-upload-v2"; }
        public int schemaVersion() { return 2; }
        public String chunkEncoding() { return "base64"; }
        public int maxChunkBytes() { return MAX_CHUNK; }
        public int timeoutSeconds() { return 60; }
    }
    public record Finalized(EncodedSource source, Receipt upload, Binding binding) { public Finalized { Objects.requireNonNull(source); Objects.requireNonNull(upload); Objects.requireNonNull(binding); } }
    private static final class Upload {
        final Begin begin; final Binding binding; final SessionKey key; final long created; final List<byte[]> chunks = new ArrayList<>(); int buffered;
        Upload(Begin begin, Binding binding, SessionKey key, long created) { this.begin = begin; this.binding = binding; this.key = key; this.created = created; }
        Receipt receipt(Status status) { return new Receipt(status, key, begin.totalBytes(), begin.sourceSha256(), begin.chunkCount(), chunks.size(), buffered, begin.intent(), binding); }
    }
    private final List<Upload> uploads = new ArrayList<>(); private final LongSupplier clock; private final Supplier<String> tokenFactory;
    private BigInteger generation = BigInteger.ZERO;
    public CoaUploads() { this(System::nanoTime, () -> { byte[] bytes = new byte[16]; new SecureRandom().nextBytes(bytes); return HexFormat.of().formatHex(bytes); }); }
    public CoaUploads(LongSupplier clock, Supplier<String> tokenFactory) { this.clock = Objects.requireNonNull(clock); this.tokenFactory = Objects.requireNonNull(tokenFactory); }
    public synchronized Receipt begin(Begin request, Binding binding) {
        Objects.requireNonNull(request); Objects.requireNonNull(binding); request.intent().requireSupportedBuild();
        require(request.intent().expectedRevision().equals(binding.revision()), "upload expected revision differs from exact binding");
        long now = clock.getAsLong(); expire(now); require(uploads.size() < MAX_SESSIONS, "upload session budget exhausted");
        require(uploads.stream().mapToInt(item -> item.begin.totalBytes()).sum() + request.totalBytes() <= MAX_RESERVED, "upload byte budget exhausted");
        generation = u64(generation.add(BigInteger.ONE), true); SessionKey key = new SessionKey(tokenFactory.get(), generation);
        require(uploads.stream().noneMatch(item -> item.key.uploadId().equals(key.uploadId())), "duplicate upload token");
        Upload upload = new Upload(request, binding, key, now); uploads.add(upload); return upload.receipt(Status.RECEIVING);
    }
    public synchronized Receipt append(Append request) {
        Objects.requireNonNull(request); expire(clock.getAsLong()); Upload upload = find(request.commit().key());
        try {
            match(upload, request.commit()); require(request.chunkIndex() == upload.chunks.size() && request.chunkIndex() < upload.begin.chunkCount(), "chunk is duplicate or out of order");
            require("base64".equals(request.chunkEncoding()), "chunk_encoding must be base64");
            int length = request.chunkBytes(); require(length > 0 && length <= MAX_CHUNK, "chunk_bytes outside range");
            String encoded = text(request.chunkBase64(), 4 * ((length + 2) / 3)); byte[] decoded;
            try { decoded = Base64.getDecoder().decode(encoded); } catch (IllegalArgumentException invalid) { throw new IllegalArgumentException("chunk_base64 is not canonical", invalid); }
            require(Base64.getEncoder().encodeToString(decoded).equals(encoded), "chunk_base64 is not canonical");
            require(decoded.length == length && sha256(decoded).equals(digest(request.chunkSha256())), "chunk length or SHA256 mismatch");
            for (byte value : decoded) require(value > 0, "chunks require NUL-free ASCII wire bytes");
            require(upload.buffered + length <= upload.begin.totalBytes(), "chunks exceed declared total_bytes");
            upload.chunks.add(decoded); upload.buffered += length; return upload.receipt(upload.chunks.size() == upload.begin.chunkCount() ? Status.READY : Status.RECEIVING);
        } catch (RuntimeException failure) { uploads.remove(upload); throw failure; }
    }
    public synchronized Finalized finalizeUpload(Commit request) {
        expire(clock.getAsLong()); Upload upload = find(request.key()); uploads.remove(upload); match(upload, request);
        require(upload.chunks.size() == upload.begin.chunkCount() && upload.buffered == upload.begin.totalBytes(), "upload is incomplete");
        ByteArrayOutputStream output = new ByteArrayOutputStream(upload.buffered); upload.chunks.forEach(output::writeBytes); byte[] bytes = output.toByteArray();
        require(sha256(bytes).equals(upload.begin.sourceSha256()), "assembled source SHA256 mismatch");
        String source = new String(bytes, StandardCharsets.US_ASCII); EncodedSource encoded = EncodedSource.encode(source, true);
        require(encoded.source().equals(source), "large source must already use canonical CRLF wire bytes");
        return new Finalized(encoded, upload.receipt(Status.COMMITTED), upload.binding);
    }
    public synchronized Receipt abort(SessionKey key) {
        expire(clock.getAsLong()); Upload upload = find(key); uploads.remove(upload);
        require(upload.key.generation().equals(key.generation()), "upload generation changed"); return upload.receipt(Status.ABORTED);
    }
    private void expire(long now) { uploads.removeIf(upload -> now - upload.created >= TTL_NANOS); }
    private Upload find(SessionKey key) { return uploads.stream().filter(upload -> upload.key.uploadId().equals(key.uploadId())).findFirst().orElseThrow(() -> new IllegalArgumentException("upload unavailable or expired")); }
    private static void match(Upload upload, Commit request) {
        require(upload.key.generation().equals(request.key().generation()), "upload generation changed");
        require(upload.begin.chunkCount() == request.chunkCount() && upload.begin.sourceSha256().equals(request.sourceSha256()), "upload chunk count or source hash changed");
        require(upload.begin.intent().equals(request.intent()), "upload revision/apply/build intent changed");
    }
}
