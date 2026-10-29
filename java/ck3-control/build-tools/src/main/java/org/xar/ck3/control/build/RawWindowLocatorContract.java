package org.xar.ck3.control.build;

import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** Closed M1 raw-encoding locator. A match never establishes an instruction boundary or executed code. */
public final class RawWindowLocatorContract {
    public static final String REQUEST_SCHEMA = "xar.native-exact-locator-request/v1";
    public static final String BODY_SCHEMA = "xar.native-exact-locator-capture/v1";
    public static final String RESULT_SCHEMA = "xar.native-exact-locator-result/v1";
    public static final String IMAGE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final String FULL_HASH_ORIGINAL_SHA256 = "4fe465cf2fe32ba51e1df1d318b0318bb3444aa394e6c37a4083cd082e43cd17";
    /** Independent historical content contradiction guard, never a substitute for current held Win32 identity. */
    public static final String TEXT_SHA256 = "227ca0fa50fee4fe762b0b8b3c62f1d5cc141455041712d0d30b3f9019f81e0d";
    public static final long TEXT_OFFSET = 1024, TEXT_RVA = 4096, TEXT_BYTES = 71_141_888, TEXT_VIRTUAL_BYTES = 71_141_448;
    public static final long MANAGER_RVA = 0x5cc1240L, QUEUE_RVA = 0x5cc1610L;
    public static final int CHUNK_BYTES = 1_048_576, MAX_CANDIDATES = 256, MAX_READS = 72, MAX_BODY_BYTES = 196_608;
    private RawWindowLocatorContract() { }
    public enum Locator { M1_MANAGER_QUEUE_TEXT }
    public enum Frame { DOS_BEFORE, PE_BEFORE, TEXT, DOS_AFTER, PE_AFTER }
    public enum Boundary { UNVALIDATED }
    public enum Operation { LEA, LOAD, STORE, STORE_IMMEDIATE32 }
    public enum Target { MANAGER, QUEUE }
    public enum BudgetClass { DEDICATED_M1_LOCATOR }
    public record Counts(BudgetClass budgetClass, long requestedLocatorBytes, long reportedLocatorBytes,
                         long requestedMetadataBytes, long reportedMetadataBytes, long fileIdentityApiBufferChargeUpper,
                         int readAttempts, int unknownReadOutcomes, boolean physicalIoMeasured, Long totalPhysicalIoBytes) {
        public Counts {
            require(budgetClass == BudgetClass.DEDICATED_M1_LOCATOR, "dedicated locator budget required; never wholeRF CODE");
            nonnegative(requestedLocatorBytes); nonnegative(reportedLocatorBytes); nonnegative(requestedMetadataBytes); nonnegative(reportedMetadataBytes);
            nonnegative(fileIdentityApiBufferChargeUpper);
            require(requestedLocatorBytes <= TEXT_BYTES && reportedLocatorBytes <= requestedLocatorBytes
                    && requestedMetadataBytes <= 1216 && reportedMetadataBytes <= requestedMetadataBytes, "finite independent locator/PE counts required");
            require(readAttempts >= 0 && readAttempts <= MAX_READS && unknownReadOutcomes >= 0 && unknownReadOutcomes <= readAttempts, "actual read outcomes are separate from reserved charges");
            require(!physicalIoMeasured && totalPhysicalIoBytes == null, "physical I/O remains unknown, never pseudo zero");
        }
    }
    public record Segment(long fileOffset, long rva, long bytes, long virtualBytes) {
        public Segment { require(fileOffset == TEXT_OFFSET && rva == TEXT_RVA && bytes == TEXT_BYTES
                && virtualBytes == TEXT_VIRTUAL_BYTES, "only the actual pinned M1 .text raw segment is admitted"); }
    }
    public record Targets(long managerRva, long queueRva) {
        public Targets { require(managerRva == MANAGER_RVA && queueRva == QUEUE_RVA, "exact two M1 targets required"); }
    }
    public record Request(String schema, String machineId, Consumer consumer, String runId, String inputPath,
                          FileRef fullHashEvidenceRef, String outputRoot, SharedSourceFiles.DirectoryIdentity outputRootIdentity,
                          Locator locator, Segment segment, Targets targets, int chunkBytes, int candidateLimit,
                          long fileIdentityApiBufferCap, int journalMaximumBytes, int bodyMaximumBytes, String reviewAtUtc)
            implements CaptureRequest {
        public Request {
            require(REQUEST_SCHEMA.equals(schema), "exact locator request schema required"); machine(machineId);
            require(consumer == Consumer.M1 && locator == Locator.M1_MANAGER_QUEUE_TEXT, "M1 closed locator only");
            identifier(runId); absolute(inputPath); absolute(outputRoot); Objects.requireNonNull(outputRootIdentity);
            Objects.requireNonNull(segment); Objects.requireNonNull(targets); Objects.requireNonNull(fullHashEvidenceRef);
            require(fullHashEvidenceRef.bytes() == 6746 && FULL_HASH_ORIGINAL_SHA256.equals(fullHashEvidenceRef.sha256())
                    && fullHashEvidenceRef.path().length() <= 1024, "actual retained M7 full-hash original required");
            require(chunkBytes == CHUNK_BYTES && candidateLimit > 0 && candidateLimit <= MAX_CANDIDATES, "fixed finite streaming and candidate caps required");
            require(fileIdentityApiBufferCap >= 8192 && fileIdentityApiBufferCap <= 65_536, "finite file-identity API upper required");
            require(journalMaximumBytes >= 65_536 + 2048 * MAX_READS + 1024 * candidateLimit
                    && journalMaximumBytes <= 524_288, "reserve complete bounded chunk/candidate/postidentity journal first");
            require(bodyMaximumBytes > 0 && bodyMaximumBytes <= MAX_BODY_BYTES, "finite locator body maximum required"); Instant.parse(reviewAtUtc);
        }
        @Override public CaptureScope scope() { return CaptureScope.M1_EXACT_TEXT_RIPREL_LOCATOR; }
    }
    /** Only the returned contiguous prefix is hashed. The full-segment field exists solely after complete successful capture. */
    public record Digest(long prefixBytes, String prefixSha256, String fullSegmentSha256) {
        public Digest {
            require(prefixBytes >= 0 && prefixBytes <= TEXT_BYTES, "bounded actual prefix length required"); sha(prefixSha256);
            require(fullSegmentSha256 == null || prefixBytes == TEXT_BYTES && fullSegmentSha256.equals(prefixSha256)
                    && TEXT_SHA256.equals(fullSegmentSha256), "full locator hash needs the whole actual segment and independent content agreement");
        }
    }
    public record ReadActual(int index, Frame frame, long fileOffset, int requestedBytes, ReadStatus status,
                             Integer reportedBytes, String sha256, int win32Error, String headerHex, Digest digest, String error) {
        public ReadActual {
            require(index >= 0 && index < MAX_READS, "finite locator read index required"); Objects.requireNonNull(frame);
            new ReadRange(fileOffset, requestedBytes); Objects.requireNonNull(status); Objects.requireNonNull(digest); diagnostic(error);
            require(status == ReadStatus.OUTCOME_UNKNOWN ? reportedBytes == null && sha256 == null && headerHex == null
                    : reportedBytes != null && reportedBytes >= 0 && reportedBytes <= requestedBytes && sha256 != null,
                    "reported actual bytes/hash or explicit unknown required");
            if (sha256 != null) sha(sha256);
            if (frame == Frame.TEXT) {
                require(headerHex == null && fileOffset >= TEXT_OFFSET && fileOffset + requestedBytes <= TEXT_OFFSET + TEXT_BYTES,
                        "locator text never persists full raw chunks");
            } else {
                boolean dos = frame == Frame.DOS_BEFORE || frame == Frame.DOS_AFTER;
                require(fileOffset == (dos ? 0 : 344) && requestedBytes == (dos ? 64 : 544), "fixed actual header ranges only");
                if (reportedBytes != null) { hex(headerHex, 544); require(headerHex.length() == reportedBytes * 2
                        && RawWindowCaptureJson.hash(HexFormat.of().parseHex(headerHex)).equals(sha256), "actual small header bytes must match their hash"); }
            }
        }
    }
    public record Candidate(long fileOffset, long rva, Operation operation, int assumedLength, int signedDisp32,
                            Target target, long targetRva, String encodingHex, String beforeContextHex, String afterContextHex,
                            boolean shortBeforeContext, boolean shortAfterContext, Boundary boundary) {
        public Candidate {
            Objects.requireNonNull(operation); Objects.requireNonNull(target);
            require(boundary == Boundary.UNVALIDATED, "raw candidate never validates an instruction boundary");
            int length = operation == Operation.STORE_IMMEDIATE32 ? 11 : 7;
            require(assumedLength == length && fileOffset >= TEXT_OFFSET && fileOffset + length <= TEXT_OFFSET + TEXT_BYTES
                    && rva == TEXT_RVA + fileOffset - TEXT_OFFSET, "complete raw encoding within exact segment required");
            require(targetRva == (target == Target.MANAGER ? MANAGER_RVA : QUEUE_RVA)
                    && rva + length + signedDisp32 == targetRva, "signed disp32 must produce one exact target using the full assumed length");
            hex(encodingHex, 11); hex(beforeContextHex, 15); hex(afterContextHex, 15);
            require(encodingHex.length() == 2 * length && shortBeforeContext == (beforeContextHex.length() < 30)
                    && shortAfterContext == (afterContextHex.length() < 30), "actual complete encoding and bounded context required");
            byte[] encoding = HexFormat.of().parseHex(encodingHex); int rex = encoding[0] & 255, opcode = encoding[1] & 255, modrm = encoding[2] & 255;
            require(rex >= 0x48 && rex <= 0x4f && (modrm & 0xc7) == 5, "closed REX.W RIPrelative pattern required");
            require(switch (operation) { case LEA -> opcode == 0x8d; case LOAD -> opcode == 0x8b; case STORE -> opcode == 0x89;
                case STORE_IMMEDIATE32 -> rex == 0x48 && opcode == 0xc7 && modrm == 5; }, "closed actual opcode form required");
            require(littleInt(encoding, 3) == signedDisp32, "candidate displacement must equal its retained original bytes");
        }
    }
    public record Intent(int index, Frame frame, ReadRange range, Counts counts) implements Event {
        public Intent { require(index >= 0 && index < MAX_READS, "bounded locator intent required"); Objects.requireNonNull(frame); Objects.requireNonNull(range); Objects.requireNonNull(counts); }
    }
    public record Before(FileProbe held, FileProbe path, Counts counts) implements Event {
        public Before { Objects.requireNonNull(held); Objects.requireNonNull(path); Objects.requireNonNull(counts); }
    }
    public record After(FileProbe held, FileProbe path, DirectoryProbe directory, CloseStatus inputClose, Counts counts) implements Event {
        public After { Objects.requireNonNull(held); Objects.requireNonNull(path); Objects.requireNonNull(directory); Objects.requireNonNull(inputClose); Objects.requireNonNull(counts); }
    }
    public record Finished(Status status, BodySummary body, Counts counts, String error) implements Event {
        public Finished { Objects.requireNonNull(status); Objects.requireNonNull(body); Objects.requireNonNull(counts); diagnostic(error); }
    }
    public record ReadObserved(ReadActual actual, Counts counts) implements Event {
        public ReadObserved { Objects.requireNonNull(actual); Objects.requireNonNull(counts); }
    }
    public record CandidateObserved(Candidate candidate) implements Event {
        public CandidateObserved { Objects.requireNonNull(candidate); }
    }
    public record Progress(Digest digest, long scannedThroughFileOffset, int candidateCount, boolean candidateScanComplete) implements Event {
        public Progress { Objects.requireNonNull(digest); require(scannedThroughFileOffset >= TEXT_OFFSET
                && scannedThroughFileOffset <= TEXT_OFFSET + TEXT_BYTES && candidateCount >= 0 && candidateCount <= MAX_CANDIDATES,
                "finite actual locator progress required"); require(!candidateScanComplete || scannedThroughFileOffset == TEXT_OFFSET + TEXT_BYTES, "whole scan requires full range"); }
    }
    public record Body(String schema, String machineId, String observedAtUtc, String runId, FileRef requestRef, FileRef fullHashEvidenceRef,
                       String inheritedImageSha256, String expectedSegmentSha256, FileProbe beforeHeld, FileProbe beforePath, FileProbe afterHeld, FileProbe afterPath,
                       DirectoryProbe afterDirectory, CloseStatus inputClose, List<ReadActual> reads, List<Candidate> candidates,
                       Progress progress, Counts counts, Status status) {
        public Body {
            require(BODY_SCHEMA.equals(schema), "exact locator body schema required"); machine(machineId); Instant.parse(observedAtUtc); identifier(runId);
            Objects.requireNonNull(requestRef); Objects.requireNonNull(fullHashEvidenceRef); require(IMAGE_SHA256.equals(inheritedImageSha256), "pinned image SHA only");
            require(TEXT_SHA256.equals(expectedSegmentSha256), "independent historical content constraint required");
            Objects.requireNonNull(beforeHeld); Objects.requireNonNull(beforePath); Objects.requireNonNull(afterHeld); Objects.requireNonNull(afterPath);
            Objects.requireNonNull(afterDirectory); Objects.requireNonNull(inputClose); Objects.requireNonNull(progress); Objects.requireNonNull(counts); Objects.requireNonNull(status);
            reads = actualReads(reads); candidates = actualCandidates(candidates);
            require(status != Status.COMPLETE || progress.candidateScanComplete() && TEXT_SHA256.equals(progress.digest().fullSegmentSha256())
                    && counts.reportedLocatorBytes() == TEXT_BYTES && counts.reportedMetadataBytes() == 1216 && inputClose == CloseStatus.CLOSED
                    && beforeHeld.status() == ProbeStatus.OBSERVED && beforePath.status() == ProbeStatus.OBSERVED
                    && afterHeld.status() == ProbeStatus.OBSERVED && afterPath.status() == ProbeStatus.OBSERVED && afterDirectory.status() == ProbeStatus.OBSERVED,
                    "complete locator body requires actual full stream, content agreement and all real poststates");
        }
    }
    public record Result(String schema, String machineId, String observedAtUtc, String runId, Status status, String fallbackPath,
                         boolean fallbackFinalDurable, Counts counts, String expectedSegmentSha256, FileProbe afterHeld, FileProbe afterPath, DirectoryProbe afterDirectory,
                         CloseStatus inputClose, List<ReadActual> reads, List<Candidate> candidates, Progress progress, BodySummary body, String error)
            implements CaptureOutcome {
        public Result {
            require(RESULT_SCHEMA.equals(schema), "exact locator result schema required"); if (!"unknown".equals(machineId)) machine(machineId);
            Instant.parse(observedAtUtc); identifier(runId); Objects.requireNonNull(status); absolute(fallbackPath); Objects.requireNonNull(counts);
            require(TEXT_SHA256.equals(expectedSegmentSha256), "independent expected text hash required");
            Objects.requireNonNull(afterHeld); Objects.requireNonNull(afterPath); Objects.requireNonNull(afterDirectory); Objects.requireNonNull(inputClose);
            Objects.requireNonNull(progress); Objects.requireNonNull(body); diagnostic(error); reads = actualReads(reads); candidates = actualCandidates(candidates);
            require(status != Status.COMPLETE || fallbackFinalDurable && body.published() && inputClose == CloseStatus.CLOSED
                    && reads.size() == MAX_READS && reads.stream().allMatch(read -> read.status() == ReadStatus.COMPLETE)
                    && progress.candidateScanComplete() && TEXT_SHA256.equals(progress.digest().fullSegmentSha256())
                    && counts.reportedLocatorBytes() == TEXT_BYTES && counts.reportedMetadataBytes() == 1216,
                    "complete locator requires actual whole stream, content agreement, scan and durable outputs");
        }
    }
    static int littleInt(byte[] bytes, int offset) { return (bytes[offset] & 255) | (bytes[offset + 1] & 255) << 8
            | (bytes[offset + 2] & 255) << 16 | bytes[offset + 3] << 24; }
    private static void hex(String value, int maximumBytes) { require(value != null && value.length() <= 2 * maximumBytes
            && value.matches("(?:[0-9a-f]{2})*"), "bounded lowercase original hexadecimal bytes required"); }
    private static List<ReadActual> actualReads(List<ReadActual> values) {
        List<ReadActual> copy = List.copyOf(values); require(copy.size() <= MAX_READS, "bounded actual read list required");
        for (int i = 0; i < copy.size(); i++) require(copy.get(i).index() == i, "contiguous actual reads required"); return copy;
    }
    private static List<Candidate> actualCandidates(List<Candidate> values) {
        List<Candidate> copy = List.copyOf(values); require(copy.size() <= MAX_CANDIDATES, "bounded actual candidates required");
        long previous = -1; for (Candidate candidate : copy) { require(candidate.fileOffset() > previous, "unique monotonically increasing candidate offsets required"); previous = candidate.fileOffset(); } return copy;
    }
}
