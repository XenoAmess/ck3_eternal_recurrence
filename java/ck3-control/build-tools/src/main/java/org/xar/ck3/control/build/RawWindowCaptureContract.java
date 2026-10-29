package org.xar.ck3.control.build;

import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** One finite contract for all eight G2 native-source consumers. No disassembly or Game entry. */
public final class RawWindowCaptureContract {
    public static final String REQUEST_SCHEMA = "xar.native-raw-window-request/v1";
    public static final String ADMISSION_SCHEMA = "xar.native-raw-window-admission/v1";
    public static final String EVENT_SCHEMA = "xar.native-raw-window-journal/v1";
    public static final String BODY_SCHEMA = "xar.native-raw-window-capture/v1";
    public static final String RESULT_SCHEMA = "xar.native-raw-window-result/v1";
    public static final String CLI_FAILURE_SCHEMA = "xar.native-raw-window-cli-failure/v1";
    public static final long SAFE = 9_007_199_254_740_991L;
    public static final int MAX_WINDOWS = 128, MAX_WINDOW_BYTES = 8192, MAX_OUTPUT_BYTES = 1_048_576;
    private RawWindowCaptureContract() { }
    public enum Consumer { M0, M1, M2, M3, M4, M5, M6, M7 }
    public enum Kind { CODE, METADATA, DATA }
    public enum Status { COMPLETE, REJECTED_BEFORE_INPUT, INPUT_IDENTITY_UNAVAILABLE, INPUT_IDENTITY_CHANGED,
        READ_INCOMPLETE, READ_OUTCOME_UNKNOWN, RAW_OUTPUT_FAILED, BODY_OVERSIZE, BODY_OUTPUT_FAILED,
        FALLBACK_WRITE_FAILED, POSTIDENTITY_UNAVAILABLE, SOURCE_CLOSE_FAILED, DEADLINE_EXPIRED,
        LOCATOR_CANDIDATE_LIMIT, LOCATOR_LAYOUT_CHANGED, LOCATOR_CONTENT_CHANGED }
    public enum ProbeStatus { OBSERVED, UNAVAILABLE }
    public enum ReadStatus { COMPLETE, SHORT_READ, NATIVE_ERROR, OUTCOME_UNKNOWN }
    public enum OutputStatus { CREATED_VERIFIED, UNAVAILABLE }
    public enum CloseStatus { NOT_OPENED, CLOSED, FAILED }
    public enum EventKind { STARTED, BEFORE, INTENT, READ_OBSERVED, RAW_OBSERVED, AFTER, FINISHED,
        LOCATOR_INTENT, LOCATOR_READ, LOCATOR_CANDIDATE, LOCATOR_PROGRESS, LOCATOR_BEFORE, LOCATOR_AFTER, LOCATOR_FINISHED }
    public enum CaptureScope { BOUNDED_READ_ONLY_FILE_WINDOWS, M1_EXACT_TEXT_RIPREL_LOCATOR }
    public sealed interface CaptureRequest permits Request, RawWindowLocatorContract.Request {
        String machineId(); Consumer consumer(); String runId(); String inputPath(); FileRef fullHashEvidenceRef();
        String outputRoot(); SharedSourceFiles.DirectoryIdentity outputRootIdentity(); long fileIdentityApiBufferCap();
        int journalMaximumBytes(); int bodyMaximumBytes(); String reviewAtUtc(); CaptureScope scope();
    }
    public sealed interface CaptureOutcome permits Result, RawWindowLocatorContract.Result {
        Status status(); boolean fallbackFinalDurable(); BodySummary body();
    }
    /** The single native port accepts only an explicit bounded range; each request branch narrows its own maximum. */
    public record ReadRange(long fileOffset, int length) {
        public ReadRange { nonnegative(fileOffset); require(length > 0 && length <= MAX_OUTPUT_BYTES
                && fileOffset <= SAFE - length, "finite native input range required"); }
    }

    public record Window(String id, Kind kind, long fileOffset, int length) {
        public Window {
            identifier(id); Objects.requireNonNull(kind); nonnegative(fileOffset);
            require(length > 0 && length <= MAX_WINDOW_BYTES && fileOffset <= SAFE - length,
                    "one finite complete raw window within the safe integer domain required");
        }
    }
    public record Amounts(long code, long metadata, long data) {
        public Amounts { nonnegative(code); nonnegative(metadata); nonnegative(data); }
        public Amounts add(Kind kind, long bytes) {
            nonnegative(bytes);
            return switch (kind) {
                case CODE -> new Amounts(Math.addExact(code, bytes), metadata, data);
                case METADATA -> new Amounts(code, Math.addExact(metadata, bytes), data);
                case DATA -> new Amounts(code, metadata, Math.addExact(data, bytes));
            };
        }
        public boolean contains(Amounts other) { return code >= other.code && metadata >= other.metadata && data >= other.data; }
    }
    /** Requested charge is reserved before native input; actual bytes are only the reported returned bytes. */
    public record Counts(Amounts requestedCharge, Amounts reportedRead, long fileIdentityApiBufferChargeUpper,
                         int readAttempts, int unknownReadOutcomes, boolean physicalIoMeasured, Long totalPhysicalIoBytes) {
        public Counts {
            Objects.requireNonNull(requestedCharge); Objects.requireNonNull(reportedRead);
            nonnegative(fileIdentityApiBufferChargeUpper); require(readAttempts >= 0 && unknownReadOutcomes >= 0
                    && unknownReadOutcomes <= readAttempts, "bounded separate actual/requested counters required");
            require(requestedCharge.contains(reportedRead), "reported bytes cannot exceed reserved reads");
            require(!physicalIoMeasured && totalPhysicalIoBytes == null, "physical I/O including environment/derived/supporting I/O is unmeasured, never zero");
        }
    }
    public record Request(String schema, String machineId, Consumer consumer, String runId, String inputPath,
                          FileRef fullHashEvidenceRef, String outputRoot, SharedSourceFiles.DirectoryIdentity outputRootIdentity,
                          List<Window> windows, Amounts windowCaps, long fileIdentityApiBufferCap,
                          int journalMaximumBytes, int bodyMaximumBytes, String reviewAtUtc) implements CaptureRequest {
        public Request {
            require(REQUEST_SCHEMA.equals(schema), "exact finite capture request schema required");
            machine(machineId); Objects.requireNonNull(consumer); identifier(runId);
            absolute(inputPath); absolute(outputRoot); Objects.requireNonNull(fullHashEvidenceRef);
            require(fullHashEvidenceRef.bytes() > 0 && fullHashEvidenceRef.bytes() <= 65_536 && fullHashEvidenceRef.path().length() <= 1024,
                    "bounded exact historical full-hash evidence required");
            Objects.requireNonNull(outputRootIdentity); windows = List.copyOf(windows); Objects.requireNonNull(windowCaps);
            require(!windows.isEmpty() && windows.size() <= MAX_WINDOWS, "finite nonempty explicit window list required");
            var ids = new HashSet<String>(); Amounts planned = new Amounts(0, 0, 0);
            for (Window window : windows) { require(ids.add(window.id()), "unique raw-window request IDs required"); planned = planned.add(window.kind(), window.length()); }
            require(windowCaps.contains(planned) && windowCaps.code() <= MAX_OUTPUT_BYTES && windowCaps.metadata() <= MAX_OUTPUT_BYTES
                    && windowCaps.data() <= MAX_OUTPUT_BYTES, "whole finite category budget must cover every requested window");
            require(fileIdentityApiBufferCap >= 8192 && fileIdentityApiBufferCap <= 65_536, "explicit finite file-identity/path API buffer upper charge required");
            require(journalMaximumBytes >= 16384 + windows.size() * 2048 && journalMaximumBytes <= MAX_OUTPUT_BYTES,
                    "fallback must be reserved before reads for every bounded intent/result plus real postidentity");
            require(bodyMaximumBytes > 0 && bodyMaximumBytes <= MAX_OUTPUT_BYTES, "finite body output maximum required");
            Instant.parse(reviewAtUtc);
        }
        @Override public CaptureScope scope() { return CaptureScope.BOUNDED_READ_ONLY_FILE_WINDOWS; }
    }
    /** Issuer pins the full request; a historical source-only grant cannot satisfy this execution schema. */
    public record Admission(String schema, String machineId, Consumer consumer, String issuer, CaptureScope scope,
                            FileRef requestRef, FileRef financialGrantRef, String reviewAtUtc) {
        public Admission {
            require(ADMISSION_SCHEMA.equals(schema), "fresh raw-window execution admission required"); machine(machineId);
            Objects.requireNonNull(consumer); require("/root/budget_fast_lane".equals(issuer), "one budget issuer required");
            Objects.requireNonNull(scope);
            require(scope != CaptureScope.M1_EXACT_TEXT_RIPREL_LOCATOR || consumer == Consumer.M1, "exact locator is M1 only");
            Objects.requireNonNull(requestRef); Objects.requireNonNull(financialGrantRef);
            require(requestRef.bytes() > 0 && requestRef.bytes() <= 65_536 && financialGrantRef.bytes() > 0
                    && financialGrantRef.bytes() <= MAX_OUTPUT_BYTES && requestRef.path().length() <= 1024
                    && financialGrantRef.path().length() <= 1024, "bounded exact execution inputs required"); Instant.parse(reviewAtUtc);
        }
    }
    public record FileProbe(ProbeStatus status, SharedSourceFiles.NativeFile value, String finalPath, String error) {
        public FileProbe {
            Objects.requireNonNull(status); diagnostic(error);
            require(status == ProbeStatus.OBSERVED ? value != null && error.isEmpty()
                    : value == null && finalPath == null && !error.isEmpty(), "exact observed/unavailable file branch required");
            if (finalPath != null) require(finalPath.length() <= 1024, "bounded actual final path required");
        }
        public static FileProbe unavailable(String error) { return new FileProbe(ProbeStatus.UNAVAILABLE, null, null, shortError(error)); }
    }
    public record DirectoryProbe(ProbeStatus status, SharedSourceFiles.DirectoryIdentity value, String error) {
        public DirectoryProbe {
            Objects.requireNonNull(status); diagnostic(error);
            require(status == ProbeStatus.OBSERVED ? value != null && error.isEmpty() : value == null && !error.isEmpty(),
                    "exact observed/unavailable directory branch required");
        }
        public static DirectoryProbe unavailable(String error) { return new DirectoryProbe(ProbeStatus.UNAVAILABLE, null, shortError(error)); }
    }
    public record ReadResult(ReadStatus status, byte[] returnedBytes, int win32Error, String error) {
        public ReadResult {
            Objects.requireNonNull(status); diagnostic(error);
            if (status == ReadStatus.OUTCOME_UNKNOWN) require(returnedBytes == null && !error.isEmpty(), "unknown read cannot invent bytes");
            else { Objects.requireNonNull(returnedBytes); require(returnedBytes.length <= MAX_OUTPUT_BYTES, "bounded returned bytes required"); returnedBytes = returnedBytes.clone(); }
        }
        @Override public byte[] returnedBytes() { return returnedBytes == null ? null : returnedBytes.clone(); }
    }
    public record RawArtifact(OutputStatus status, String filename, Long bytes, String sha256, String error) {
        public RawArtifact {
            Objects.requireNonNull(status); diagnostic(error);
            require(status == OutputStatus.CREATED_VERIFIED ? filename != null && bytes != null && bytes >= 0 && sha256 != null && error.isEmpty()
                    : filename == null && bytes == null && sha256 == null && !error.isEmpty(), "exact saved/unavailable raw artifact branch required");
            if (filename != null) require(filename.matches("window-[0-9]{3}\\.raw"), "fixed new raw artifact child required");
            if (sha256 != null) sha(sha256);
        }
        public static RawArtifact unavailable(String error) { return new RawArtifact(OutputStatus.UNAVAILABLE, null, null, null, shortError(error)); }
    }
    public record WindowActual(int index, Window window, ReadStatus status, Integer reportedBytes, String sha256,
                               int win32Error, RawArtifact rawArtifact, String error) {
        public WindowActual {
            require(index >= 0 && index < MAX_WINDOWS, "bounded original read index required"); Objects.requireNonNull(window);
            Objects.requireNonNull(status); Objects.requireNonNull(rawArtifact); diagnostic(error);
            require(status == ReadStatus.OUTCOME_UNKNOWN ? reportedBytes == null && sha256 == null
                    : reportedBytes != null && reportedBytes >= 0 && reportedBytes <= window.length() && sha256 != null,
                    "actual returned count/hash or explicit unknown required"); if (sha256 != null) sha(sha256);
        }
    }
    public record BodySummary(Long encodedBytes, String sha256, boolean published) {
        public BodySummary {
            require((encodedBytes == null) == (sha256 == null), "body size/hash have one presence contract");
            if (encodedBytes != null) { nonnegative(encodedBytes); sha(sha256); }
            require(!published || encodedBytes != null, "published body must have actual complete bytes");
        }
    }
    public sealed interface Event permits Started, Before, Intent, ReadObserved, RawObserved, After, Finished,
            RawWindowLocatorContract.Intent, RawWindowLocatorContract.ReadObserved,
            RawWindowLocatorContract.CandidateObserved, RawWindowLocatorContract.Progress,
            RawWindowLocatorContract.Before, RawWindowLocatorContract.After, RawWindowLocatorContract.Finished { }
    public record Started(String schema, String machineId, Consumer consumer, String runId, String observedAtUtc,
                          FileRef admissionRef, FileRef requestRef, FileRef fullHashEvidenceRef) implements Event {
        public Started { require(EVENT_SCHEMA.equals(schema), "exact journal header required"); machine(machineId); Objects.requireNonNull(consumer);
            identifier(runId); Instant.parse(observedAtUtc); Objects.requireNonNull(admissionRef); Objects.requireNonNull(requestRef); Objects.requireNonNull(fullHashEvidenceRef); }
    }
    public record Before(FileProbe held, FileProbe path, Counts counts) implements Event {
        public Before { Objects.requireNonNull(held); Objects.requireNonNull(path); Objects.requireNonNull(counts); }
    }
    public record Intent(int index, Window window, Counts counts) implements Event {
        public Intent { readIndex(index); Objects.requireNonNull(window); Objects.requireNonNull(counts); }
    }
    public record ReadObserved(int index, ReadStatus status, Integer reportedBytes, String sha256, int win32Error,
                               String error, Counts counts) implements Event {
        public ReadObserved { readIndex(index); Objects.requireNonNull(status); Objects.requireNonNull(counts); diagnostic(error);
            require(status == ReadStatus.OUTCOME_UNKNOWN ? reportedBytes == null && sha256 == null : reportedBytes != null
                    && reportedBytes >= 0 && reportedBytes <= MAX_WINDOW_BYTES && sha256 != null, "reported read or explicit unknown required");
            if (sha256 != null) sha(sha256); }
    }
    public record RawObserved(int index, RawArtifact artifact) implements Event {
        public RawObserved { readIndex(index); Objects.requireNonNull(artifact); }
    }
    public record After(FileProbe held, FileProbe path, DirectoryProbe directory, CloseStatus inputClose, Counts counts) implements Event {
        public After { Objects.requireNonNull(held); Objects.requireNonNull(path); Objects.requireNonNull(directory); Objects.requireNonNull(inputClose); Objects.requireNonNull(counts); }
    }
    public record Finished(Status status, BodySummary body, Counts counts, String error) implements Event {
        public Finished { Objects.requireNonNull(status); Objects.requireNonNull(body); Objects.requireNonNull(counts); diagnostic(error); }
    }
    public static EventKind kindOf(Event value) {
        return switch (value) {
            case Started ignored -> EventKind.STARTED; case Before ignored -> EventKind.BEFORE; case Intent ignored -> EventKind.INTENT;
            case ReadObserved ignored -> EventKind.READ_OBSERVED; case RawObserved ignored -> EventKind.RAW_OBSERVED;
            case After ignored -> EventKind.AFTER; case Finished ignored -> EventKind.FINISHED;
            case RawWindowLocatorContract.Intent ignored -> EventKind.LOCATOR_INTENT;
            case RawWindowLocatorContract.ReadObserved ignored -> EventKind.LOCATOR_READ;
            case RawWindowLocatorContract.CandidateObserved ignored -> EventKind.LOCATOR_CANDIDATE;
            case RawWindowLocatorContract.Progress ignored -> EventKind.LOCATOR_PROGRESS;
            case RawWindowLocatorContract.Before ignored -> EventKind.LOCATOR_BEFORE;
            case RawWindowLocatorContract.After ignored -> EventKind.LOCATOR_AFTER;
            case RawWindowLocatorContract.Finished ignored -> EventKind.LOCATOR_FINISHED;
        };
    }
    public record Body(String schema, String machineId, String observedAtUtc, Consumer consumer, String runId, FileRef requestRef,
                       FileRef fullHashEvidenceRef, String inheritedImageSha256, FileProbe beforeHeld, FileProbe beforePath,
                       FileProbe afterHeld, FileProbe afterPath, DirectoryProbe afterDirectory,
                       List<WindowActual> windows, Counts counts, Status status) {
        public Body {
            require(BODY_SCHEMA.equals(schema), "exact raw capture body schema required");
            machine(machineId); Instant.parse(observedAtUtc); Objects.requireNonNull(consumer); identifier(runId);
            Objects.requireNonNull(requestRef); Objects.requireNonNull(fullHashEvidenceRef); sha(inheritedImageSha256);
            Objects.requireNonNull(beforeHeld); Objects.requireNonNull(beforePath); Objects.requireNonNull(afterHeld);
            Objects.requireNonNull(afterPath); Objects.requireNonNull(afterDirectory); Objects.requireNonNull(counts); Objects.requireNonNull(status);
            windows = actualWindows(windows);
        }
    }
    public record Result(String schema, String machineId, String observedAtUtc, String runId, Status status, String fallbackPath,
                         boolean fallbackFinalDurable, Counts counts, FileProbe afterHeld, FileProbe afterPath,
                         DirectoryProbe afterDirectory, CloseStatus inputClose, List<WindowActual> windows,
                         BodySummary body, String error) implements CaptureOutcome {
        public Result {
            require(RESULT_SCHEMA.equals(schema), "exact finite result schema required");
            if (!"unknown".equals(machineId)) machine(machineId); Instant.parse(observedAtUtc); identifier(runId);
            Objects.requireNonNull(status); absolute(fallbackPath); Objects.requireNonNull(counts);
            Objects.requireNonNull(afterHeld); Objects.requireNonNull(afterPath); Objects.requireNonNull(afterDirectory);
            Objects.requireNonNull(inputClose); Objects.requireNonNull(body); diagnostic(error); windows = actualWindows(windows);
            require(status != Status.COMPLETE || (fallbackFinalDurable && body.published() && inputClose == CloseStatus.CLOSED
                    && !windows.isEmpty() && windows.stream().allMatch(window -> window.status() == ReadStatus.COMPLETE
                    && window.rawArtifact().status() == OutputStatus.CREATED_VERIFIED)), "complete result requires actual complete durable originals and cleanup");
        }
    }
    private static List<WindowActual> actualWindows(List<WindowActual> windows) {
        List<WindowActual> result = List.copyOf(windows); require(result.size() <= MAX_WINDOWS, "bounded returned window list required");
        for (int index = 0; index < result.size(); index++) require(result.get(index).index() == index, "contiguous actual read indexes required"); return result;
    }
    private static void readIndex(int index) { require(index >= 0 && index < MAX_WINDOWS, "bounded original read index required"); }
    static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
    static void nonnegative(long value) { require(value >= 0 && value <= SAFE, "safe nonnegative JSON integer required"); }
    static void sha(String value) { require(value != null && value.matches("[0-9a-f]{64}"), "lowercase SHA-256 required"); }
    static void machine(String value) { require(value != null && value.matches("[a-z0-9][a-z0-9-]{0,127}") && !value.equals("unknown"), "explicit machine required"); }
    static void identifier(String value) { require(value != null && value.matches("[A-Za-z0-9][A-Za-z0-9_.-]{0,47}"), "bounded original identifier required"); }
    static Path absolute(String value) {
        require(value != null && value.length() <= 1024 && value.indexOf('\0') < 0, "bounded explicit absolute path required");
        Path path = Path.of(value); require(path.isAbsolute() && path.normalize().equals(path), "absolute normalized path required"); return path;
    }
    static void diagnostic(String value) { require(value != null && value.length() <= 512, "bounded explicit diagnostic required"); }
    static String shortError(String value) {
        String text = value == null || value.isEmpty() ? "unavailable" : value; int end = Math.min(512, text.length());
        if (end < text.length() && Character.isHighSurrogate(text.charAt(end - 1))) end--; return text.substring(0, end);
    }
}
