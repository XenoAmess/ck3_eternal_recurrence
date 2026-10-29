package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Closed source, upload and native evidence types. JSON integers are checked before construction. */
public final class CoaData {
    private CoaData() { }
    public static final int V1_MAX_BYTES = 128 * 1024, V2_MAX_BYTES = 512 * 1024;
    public static final String GAME_VERSION = "1.19.0.6";
    public static final String ADAPTER_ID = "ck3-1.19.0.6-msvc-x64";
    public static final String EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    public static final String PROBE_STEP = "probe-coat-of-arms-source-v1", EXPORT_STEP = "export-coat-of-arms-source-v1";
    public static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    public static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
    public static BigInteger u64(BigInteger value, boolean positive) {
        Objects.requireNonNull(value); require(value.signum() >= (positive ? 1 : 0) && value.compareTo(U64_MAX) <= 0, "uint64 outside range"); return value;
    }
    public static String text(String value, int maximum) { require(value != null && !value.isEmpty() && value.length() <= maximum, "nonempty bounded text required"); return value; }
    public static String digest(String value) { require(value != null && value.matches("[a-fA-F0-9]{64}"), "SHA256 required"); return value.toLowerCase(java.util.Locale.ROOT); }
    public static String sha256(byte[] value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (NoSuchAlgorithmException unavailable) { throw new IllegalStateException(unavailable); }
    }
    public static String ascii(String value, int maximum) {
        require(value != null && !value.isEmpty() && value.length() <= maximum, "bounded ASCII source required");
        for (int index = 0; index < value.length(); index++) require(value.charAt(index) > 0 && value.charAt(index) < 128, "source requires NUL-free ASCII");
        return value;
    }
    public record EncodedSource(String source, String sourceBase64, String sourceSha256, int sourceBytes) {
        public EncodedSource {
            ascii(source, V2_MAX_BYTES); require(sourceBytes == source.length(), "source byte count mismatch");
            require(sourceSha256.equals(sha256(source.getBytes(StandardCharsets.US_ASCII))), "source hash mismatch");
            require(sourceBase64.equals(Base64.getEncoder().encodeToString(source.getBytes(StandardCharsets.US_ASCII))), "source base64 mismatch");
        }
        public static EncodedSource encode(String input, boolean large) {
            Objects.requireNonNull(input); String source = input.replace("\r\n", "\n").replace('\r', '\n').replace("\n", "\r\n");
            ascii(source, large ? V2_MAX_BYTES : V1_MAX_BYTES); byte[] bytes = source.getBytes(StandardCharsets.US_ASCII);
            return new EncodedSource(source, Base64.getEncoder().encodeToString(bytes), sha256(bytes), bytes.length);
        }
    }
    public sealed interface Binding permits FrontendBinding, SnapshotBinding {
        BigInteger revision(); BigInteger nativeRevision(); long dateRaw(); BigInteger connectionGeneration(); long bridgePid();
    }
    public record FrontendBinding(BigInteger connectionGeneration, long bridgePid) implements Binding {
        public FrontendBinding { u64(connectionGeneration, true); require(bridgePid > 0 && bridgePid <= 0xffffffffL, "positive uint32 bridge PID required"); }
        @Override public BigInteger revision() { return BigInteger.ZERO; }
        @Override public BigInteger nativeRevision() { return BigInteger.ZERO; }
        @Override public long dateRaw() { return 0; }
    }
    public enum SnapshotMode { GAMEPLAY, FRONTEND_SNAPSHOT }
    public record SnapshotBinding(SnapshotMode mode, String snapshotId, BigInteger revision, BigInteger nativeRevision,
            long dateRaw, Optional<String> episodeRunId, BigInteger connectionGeneration, long bridgePid) implements Binding {
        public SnapshotBinding {
            Objects.requireNonNull(mode); text(snapshotId, 4096); u64(revision, true); u64(nativeRevision, true); u64(connectionGeneration, true);
            episodeRunId = Objects.requireNonNull(episodeRunId); episodeRunId.ifPresent(value -> text(value, 4096));
            require((mode == SnapshotMode.GAMEPLAY) == episodeRunId.isPresent(), "only gameplay binding has episode identity");
            require(bridgePid > 0 && bridgePid <= 0xffffffffL, "positive uint32 bridge PID required");
        }
    }
    public enum ProbeStatus { APPLIED, DETECTED, NOT_DETECTED, APPLY_FAILED, UNAVAILABLE }
    public record ProbeResult(ProbeStatus status, boolean detected, boolean designerObserved, boolean clipboardWritten,
            boolean clipboardReadbackMatched, boolean applyRequested, boolean pasteInvoked, boolean applied,
            long candidateIndex, long previewCoatOfArmsHandle, long activeCoatOfArmsIndex,
            Optional<String> reason, EncodedSource source, Binding binding, BigInteger querySequence) {
        public ProbeResult {
            Objects.requireNonNull(status); Objects.requireNonNull(source); Objects.requireNonNull(binding); reason = Objects.requireNonNull(reason); u64(querySequence, true);
            for (long index : new long[]{candidateIndex, previewCoatOfArmsHandle, activeCoatOfArmsIndex}) require(index >= 0 && index <= 0xffffffffL, "uint32 native handle required");
            require(!clipboardReadbackMatched || clipboardWritten, "readback requires write");
            require(!detected || (designerObserved && clipboardWritten && clipboardReadbackMatched), "detection requires designer and exact clipboard readback");
            require(!pasteInvoked || (applyRequested && detected), "paste requires detected apply request");
            require(!applied || pasteInvoked, "applied requires paste");
            require(applyRequested || (!pasteInvoked && !applied), "detect-only operation cannot paste");
            if (status == ProbeStatus.APPLIED || status == ProbeStatus.DETECTED) require(reason.isEmpty(), "success cannot have reason");
            else { require(reason.isPresent(), "failure requires reason"); String explanation = reason.orElseThrow(); text(explanation, 1024);
                require(explanation.getBytes(StandardCharsets.UTF_8).length <= 1024 && explanation.chars().noneMatch(c -> c < 32), "invalid bounded native reason"); }
            switch (status) {
                case APPLIED -> require(detected && applyRequested && pasteInvoked && applied, "applied evidence inconsistent");
                case DETECTED -> require(detected && !applyRequested && !pasteInvoked && !applied, "detected evidence inconsistent");
                case NOT_DETECTED -> require(!detected && !pasteInvoked && !applied && designerObserved && clipboardWritten && clipboardReadbackMatched
                        && reason.orElseThrow().equals("engine_did_not_detect_coat_of_arms"), "not-detected evidence inconsistent");
                case APPLY_FAILED -> require(detected && applyRequested && pasteInvoked && !applied, "apply-failed evidence inconsistent");
                case UNAVAILABLE -> require(!detected && !pasteInvoked && !applied, "unavailable evidence inconsistent");
            }
        }
    }
    public enum ExportStatus { EXPORTED, UNAVAILABLE }
    public record ExportResult(ExportStatus status, boolean designerObserved, boolean copyInvoked, boolean clipboardRead,
            Optional<String> source, Optional<String> sourceSha256, int sourceBytes, Optional<String> reason,
            Binding binding, BigInteger querySequence) {
        public ExportResult {
            Objects.requireNonNull(status); source = Objects.requireNonNull(source); sourceSha256 = Objects.requireNonNull(sourceSha256);
            reason = Objects.requireNonNull(reason); Objects.requireNonNull(binding); u64(querySequence, false);
            if (status == ExportStatus.EXPORTED) {
                String raw = ascii(source.orElseThrow(), V2_MAX_BYTES); require(designerObserved && copyInvoked && clipboardRead && reason.isEmpty(), "export postconditions incomplete");
                require(sourceBytes == raw.length() && sourceSha256.orElseThrow().equals(sha256(raw.getBytes(StandardCharsets.US_ASCII))), "export source identity mismatch");
            } else require(source.isEmpty() && sourceSha256.isEmpty() && sourceBytes == 0 && reason.isPresent() && !reason.orElseThrow().isEmpty(), "unavailable export exposed source or lacks reason");
        }
    }
    public record Widget(String runtimeName, String childPath, int depth, int childCount, BigInteger vtableRva, boolean effectiveVisible, boolean enabled) {
        public Widget {
            Objects.requireNonNull(runtimeName); Objects.requireNonNull(childPath); require(runtimeName.getBytes(StandardCharsets.UTF_8).length <= 127, "widget name too long");
            require(childPath.length() <= 383 && (childPath.isEmpty() || childPath.matches("[0-9]+(?:/[0-9]+)*")), "invalid widget child path");
            require(depth >= 0 && depth <= 64 && depth == (childPath.isEmpty() ? 0 : childPath.split("/").length), "widget depth mismatch");
            require(childCount >= 0 && childCount <= 4096, "widget child count outside range"); u64(vtableRva, false);
        }
    }
    public record Tree(String step, String scopeRootName, boolean available, boolean truncated, List<Widget> widgets, Optional<Integer> directChildCount) {
        public Tree { text(step, 128); Objects.requireNonNull(scopeRootName); widgets = List.copyOf(widgets); require(widgets.size() <= 2048, "tree too large"); directChildCount = Objects.requireNonNull(directChildCount); }
        public boolean has(String path, String name) { return available && widgets.stream().anyMatch(row -> row.childPath().equals(path) && row.runtimeName().equals(name) && row.effectiveVisible() && row.enabled()); }
    }
}
