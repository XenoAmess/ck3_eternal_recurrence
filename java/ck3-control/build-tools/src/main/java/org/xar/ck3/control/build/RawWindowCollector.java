package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/**
 * The one bounded producer loop, used by the actual Win32 entry and fault regressions.
 * Every read intent is durable before native input; every returned count/hash is durable
 * before body output. There is no disassembler, compression gate, Game or ledger call.
 */
public final class RawWindowCollector {
    private RawWindowCollector() { }
    /** Mechanical resources only; production does not depend on a test runner. */
    interface Ports extends AutoCloseable {
        String machineId() throws IOException;
        void startJournal(Started started) throws IOException;
        void append(Event event) throws IOException;
        void openInput() throws IOException;
        FileProbe held() throws IOException;
        FileProbe path() throws IOException;
        DirectoryProbe directory() throws IOException;
        ReadResult read(ReadRange window) throws IOException;
        RawArtifact preserveRaw(int index, byte[] actual) throws IOException;
        void publishBody(byte[] complete) throws IOException;
        long fileIdentityApiBufferChargeUpper();
        CloseStatus closeInput();
        @Override void close() throws IOException;
    }

    public static CaptureOutcome capture(Admission admission, FileRef admissionRef) throws IOException {
        Admission original = RawWindowCaptureJson.decode(RawWindowCaptureJson.exactBytes(admissionRef, 65_536), Admission.class, 65_536);
        if (!original.equals(admission)) throw new IOException("admission differs from its exact original bytes");
        CaptureRequest request = RawWindowCaptureJson.decodeRequest(RawWindowCaptureJson.exactBytes(admission.requestRef(), 65_536));
        RawWindowCaptureJson.exactBytes(admission.financialGrantRef(), MAX_OUTPUT_BYTES);
        RawWindowImageProof.Proof proof = RawWindowImageProof.load(request.fullHashEvidenceRef());
        Ports ports = new RawWindowNativeIo(request);
        return switch (request) {
            case Request windows -> execute(admission, admissionRef, windows, proof, ports);
            case RawWindowLocatorContract.Request locator -> executeLocator(admission, admissionRef, locator, proof, ports);
        };
    }

    static Result execute(Admission admission, FileRef admissionRef, Request request, RawWindowImageProof.Proof proof,
                          Ports ports) throws IOException {
        Objects.requireNonNull(admission); Objects.requireNonNull(admissionRef); Objects.requireNonNull(request);
        Objects.requireNonNull(proof); Objects.requireNonNull(ports);
        if (admissionRef.path().length() > 1024) throw new IOException("bounded exact admission reference required");
        Amounts charged = new Amounts(0, 0, 0), reported = new Amounts(0, 0, 0);
        int attempts = 0, unknown = 0; boolean started = false, finalDurable = false, inputOpened = false;
        Status status = Status.REJECTED_BEFORE_INPUT; String error = "", actualMachine = "unknown";
        FileProbe beforeHeld = FileProbe.unavailable("input not opened"), beforePath = FileProbe.unavailable("input not opened");
        FileProbe afterHeld = FileProbe.unavailable("input not opened"), afterPath = FileProbe.unavailable("input not opened");
        DirectoryProbe afterDirectory = DirectoryProbe.unavailable("postdirectory not observed");
        CloseStatus inputClose = CloseStatus.NOT_OPENED; BodySummary body = new BodySummary(null, null, false);
        List<WindowActual> windows = new ArrayList<>();
        try {
            actualMachine = ports.machineId();
            if (!actualMachine.equals(request.machineId()) || !admission.machineId().equals(request.machineId())
                    || admission.consumer() != request.consumer() || admission.scope() != request.scope() || !Instant.now().isBefore(Instant.parse(admission.reviewAtUtc()))
                    || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))) throw new IOException("fresh same-machine exact request admission required");
            ports.startJournal(new Started(EVENT_SCHEMA, request.machineId(), request.consumer(), request.runId(), Instant.now().toString(),
                    admissionRef, admission.requestRef(), request.fullHashEvidenceRef())); started = true;
            try {
                try { ports.openInput(); inputOpened = true; beforeHeld = ports.held(); beforePath = ports.path(); }
                catch (IOException | RuntimeException failure) { throw new CaptureFailure(Status.INPUT_IDENTITY_UNAVAILABLE, shortError(failure.toString())); }
                ports.append(new Before(beforeHeld, beforePath, counts(charged, reported, ports, attempts, unknown)));
                if (beforeHeld.status() != ProbeStatus.OBSERVED || beforeHeld.finalPath() == null || beforePath.status() != ProbeStatus.OBSERVED)
                    throw new CaptureFailure(Status.INPUT_IDENTITY_UNAVAILABLE, "actual held/path preidentity unavailable");
                try { proof.requireCurrent(request.machineId(), request.inputPath(), beforeHeld.value()); }
                catch (IOException mismatch) { throw new CaptureFailure(Status.INPUT_IDENTITY_CHANGED, shortError(mismatch.toString())); }
                if (!beforeHeld.value().equals(beforePath.value())
                        || !Path.of(RawWindowImageProof.stripExtended(beforeHeld.finalPath())).equals(Path.of(request.inputPath())))
                    throw new CaptureFailure(Status.INPUT_IDENTITY_CHANGED, "held/path/native final spelling differs before input");
                for (int index = 0; index < request.windows().size(); index++) {
                    if (!Instant.now().isBefore(Instant.parse(admission.reviewAtUtc())) || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc())))
                        throw new CaptureFailure(Status.DEADLINE_EXPIRED, "native-input deadline expired before the next finite window");
                    Window window = request.windows().get(index);
                    if (window.fileOffset() > beforeHeld.value().logicalBytes() - window.length())
                        throw new CaptureFailure(Status.READ_INCOMPLETE, "requested original window exceeds actual held image");
                    charged = charged.add(window.kind(), window.length());
                    Counts reserved = counts(charged, reported, ports, attempts, unknown);
                    // If this write fails, ReadFile is never called. A durable intent is a conservative charge, not a read claim.
                    ports.append(new Intent(index, window, reserved));
                    attempts++;
                    ReadResult actual;
                    try { actual = ports.read(new ReadRange(window.fileOffset(), window.length())); }
                    catch (IOException | RuntimeException readError) {
                        actual = new ReadResult(ReadStatus.OUTCOME_UNKNOWN, null, 0, shortError(readError.toString()));
                    }
                    byte[] bytes = actual.returnedBytes();
                    if (bytes != null && bytes.length > window.length()) {
                        actual = new ReadResult(ReadStatus.OUTCOME_UNKNOWN, null, actual.win32Error(), "native adapter exceeded the exact requested bound"); bytes = null;
                    }
                    Integer actualBytes = bytes == null ? null : bytes.length;
                    String hash = bytes == null ? null : RawWindowCaptureJson.hash(bytes);
                    if (bytes == null) unknown++; else reported = reported.add(window.kind(), bytes.length);
                    ReadStatus observedStatus = actual.status();
                    if (observedStatus == ReadStatus.COMPLETE && actualBytes != window.length()) observedStatus = ReadStatus.SHORT_READ;
                    RawArtifact raw = RawArtifact.unavailable("raw output not yet attempted");
                    windows.add(new WindowActual(index, window, observedStatus, actualBytes, hash, actual.win32Error(), raw, actual.error()));
                    ports.append(new ReadObserved(index, observedStatus, actualBytes, hash, actual.win32Error(), actual.error(),
                            counts(charged, reported, ports, attempts, unknown)));
                    if (bytes != null) {
                        try { raw = ports.preserveRaw(index, bytes); }
                        catch (IOException | RuntimeException writeError) { raw = RawArtifact.unavailable(writeError.toString()); }
                        windows.set(windows.size() - 1, new WindowActual(index, window, observedStatus, actualBytes, hash, actual.win32Error(), raw, actual.error()));
                        ports.append(new RawObserved(index, raw));
                    }
                    windows.set(windows.size() - 1, new WindowActual(index, window, observedStatus, actualBytes, hash, actual.win32Error(), raw, actual.error()));
                    if (bytes == null) throw new CaptureFailure(Status.READ_OUTCOME_UNKNOWN, "native read outcome unknown; no retry");
                    if (raw.status() != OutputStatus.CREATED_VERIFIED) throw new CaptureFailure(Status.RAW_OUTPUT_FAILED, raw.error());
                    if (observedStatus != ReadStatus.COMPLETE) throw new CaptureFailure(Status.READ_INCOMPLETE, "short or failed native read retained; no retry");
                }
                status = Status.COMPLETE;
            } catch (CaptureFailure failure) {
                status = failure.status; error = shortError(failure.getMessage());
            } catch (IOException | RuntimeException failure) {
                status = Status.FALLBACK_WRITE_FAILED; error = shortError(failure.toString());
            } finally {
                if (inputOpened) {
                    try { afterHeld = ports.held(); } catch (IOException | RuntimeException failure) { afterHeld = FileProbe.unavailable(failure.toString()); }
                    try { inputClose = ports.closeInput(); }
                    catch (RuntimeException failure) {
                        inputClose = CloseStatus.FAILED; error = shortError(error + "; input close: " + failure);
                        if (status == Status.COMPLETE) status = Status.SOURCE_CLOSE_FAILED;
                    }
                    try { afterPath = ports.path(); } catch (IOException | RuntimeException failure) { afterPath = FileProbe.unavailable(failure.toString()); }
                }
                try { afterDirectory = ports.directory(); } catch (IOException | RuntimeException failure) { afterDirectory = DirectoryProbe.unavailable(failure.toString()); }
                if (status == Status.COMPLETE) {
                    if (afterHeld.status() != ProbeStatus.OBSERVED || afterPath.status() != ProbeStatus.OBSERVED || afterDirectory.status() != ProbeStatus.OBSERVED)
                        status = Status.POSTIDENTITY_UNAVAILABLE;
                    else if (!beforeHeld.value().equals(afterHeld.value()) || !beforeHeld.value().equals(afterPath.value())
                            || !beforeHeld.finalPath().equals(afterHeld.finalPath()) || !request.outputRootIdentity().equals(afterDirectory.value()))
                        status = Status.INPUT_IDENTITY_CHANGED;
                    if (inputClose != CloseStatus.CLOSED) status = Status.SOURCE_CLOSE_FAILED;
                }
                try { ports.append(new After(afterHeld, afterPath, afterDirectory, inputClose, counts(charged, reported, ports, attempts, unknown))); }
                catch (IOException | RuntimeException failure) { status = Status.FALLBACK_WRITE_FAILED; error = shortError(error + "; postidentity journal: " + failure); }
            }
            if (status != Status.FALLBACK_WRITE_FAILED) {
                Body complete = new Body(BODY_SCHEMA, request.machineId(), Instant.now().toString(), request.consumer(), request.runId(), admission.requestRef(),
                        request.fullHashEvidenceRef(), proof.sha256(), beforeHeld, beforePath, afterHeld, afterPath, afterDirectory,
                        windows, counts(charged, reported, ports, attempts, unknown), status);
                try {
                    byte[] encoded = RawWindowCaptureJson.encode(complete);
                    body = new BodySummary((long) encoded.length, RawWindowCaptureJson.hash(encoded), false);
                    if (encoded.length > request.bodyMaximumBytes()) {
                        status = Status.BODY_OVERSIZE; error = "complete body exceeds reserved output; exact size/hash remain in fallback";
                    } else {
                        try { ports.publishBody(encoded); body = new BodySummary((long) encoded.length, RawWindowCaptureJson.hash(encoded), true); }
                        catch (IOException | RuntimeException failure) { status = Status.BODY_OUTPUT_FAILED; error = shortError(failure.toString()); }
                    }
                } catch (IOException | RuntimeException failure) { status = Status.BODY_OUTPUT_FAILED; error = shortError(failure.toString()); }
            }
            try { ports.append(new Finished(status, body, counts(charged, reported, ports, attempts, unknown), error)); finalDurable = true; }
            catch (IOException | RuntimeException failure) { status = Status.FALLBACK_WRITE_FAILED; error = shortError(error + "; terminal journal: " + failure); }
        } catch (IOException | RuntimeException failure) {
            error = shortError(failure.toString()); status = started ? Status.FALLBACK_WRITE_FAILED : Status.REJECTED_BEFORE_INPUT;
        } finally {
            // Cleanup failure is a separate non-success result even if the already forced journal has a complete terminal.
            try { ports.close(); }
            catch (IOException | RuntimeException failure) { status = Status.SOURCE_CLOSE_FAILED; error = shortError(error + "; cleanup: " + failure); }
        }
        return new Result(RESULT_SCHEMA, actualMachine, Instant.now().toString(), request.runId(), status,
                Path.of(request.outputRoot()).resolve("fallback.jsonl").toString(), finalDurable,
                counts(charged, reported, ports, attempts, unknown), afterHeld, afterPath, afterDirectory, inputClose, windows, body, error);
    }
    static RawWindowLocatorContract.Result executeLocator(Admission admission, FileRef admissionRef,
            RawWindowLocatorContract.Request request, RawWindowImageProof.Proof proof, Ports ports) throws IOException {
        LocatorState state = new LocatorState(ports);
        boolean started = false, opened = false, finalDurable = false; String machine = "unknown", error = "";
        Status status = Status.REJECTED_BEFORE_INPUT;
        FileProbe beforeHeld = FileProbe.unavailable("input not opened"), beforePath = FileProbe.unavailable("input not opened");
        FileProbe afterHeld = FileProbe.unavailable("input not opened"), afterPath = FileProbe.unavailable("input not opened");
        DirectoryProbe afterDirectory = DirectoryProbe.unavailable("postdirectory not observed"); CloseStatus inputClose = CloseStatus.NOT_OPENED;
        BodySummary body = new BodySummary(null, null, false);
        try {
            machine = ports.machineId();
            if (!machine.equals(request.machineId()) || !admission.machineId().equals(machine) || admission.consumer() != Consumer.M1
                    || admission.scope() != request.scope() || !RawWindowLocatorContract.IMAGE_SHA256.equals(proof.sha256()))
                throw new IOException("same-machine M1 exact-locator admission and actual historical image required");
            fresh(admission, request);
            ports.startJournal(new Started(EVENT_SCHEMA, machine, Consumer.M1, request.runId(), Instant.now().toString(), admissionRef,
                    admission.requestRef(), request.fullHashEvidenceRef())); started = true;
            try {
                try { ports.openInput(); opened = true; beforeHeld = ports.held(); beforePath = ports.path(); }
                catch (IOException | RuntimeException failure) { throw new CaptureFailure(Status.INPUT_IDENTITY_UNAVAILABLE, shortError(failure.toString())); }
                ports.append(new RawWindowLocatorContract.Before(beforeHeld, beforePath, state.counts()));
                if (beforeHeld.status() != ProbeStatus.OBSERVED || beforeHeld.finalPath() == null || beforePath.status() != ProbeStatus.OBSERVED)
                    throw new CaptureFailure(Status.INPUT_IDENTITY_UNAVAILABLE, "actual held/path identity unavailable");
                try { proof.requireCurrent(machine, request.inputPath(), beforeHeld.value()); }
                catch (IOException mismatch) { throw new CaptureFailure(Status.INPUT_IDENTITY_CHANGED, shortError(mismatch.toString())); }
                if (!beforeHeld.value().equals(beforePath.value()) || beforeHeld.value().logicalBytes() != 101_040_248
                        || !Path.of(RawWindowImageProof.stripExtended(beforeHeld.finalPath())).equals(Path.of(request.inputPath())))
                    throw new CaptureFailure(Status.INPUT_IDENTITY_CHANGED, "locator held/path/final spelling differs");
                byte[] dos = state.read(admission, request, RawWindowLocatorContract.Frame.DOS_BEFORE, 0, 64);
                byte[] pe = state.read(admission, request, RawWindowLocatorContract.Frame.PE_BEFORE, 344, 544);
                requireLocatorHeaders(dos, pe);
                ExactRipRelativeLocator matcher = new ExactRipRelativeLocator();
                for (long offset = 0; offset < RawWindowLocatorContract.TEXT_BYTES;) {
                    int length = (int) Math.min(request.chunkBytes(), RawWindowLocatorContract.TEXT_BYTES - offset);
                    byte[] actual = state.read(admission, request, RawWindowLocatorContract.Frame.TEXT,
                            RawWindowLocatorContract.TEXT_OFFSET + offset, length);
                    ExactRipRelativeLocator.Batch batch = matcher.accept(actual, offset,
                            offset + length == RawWindowLocatorContract.TEXT_BYTES, request.candidateLimit() - state.candidates.size());
                    state.scannedThrough = batch.scannedThroughFileOffset(); state.scanComplete = batch.candidateScanComplete();
                    // Preserve all actually found candidates in the Root result before attempting any candidate-output write.
                    state.candidates.addAll(batch.candidates());
                    for (RawWindowLocatorContract.Candidate candidate : batch.candidates()) ports.append(new RawWindowLocatorContract.CandidateObserved(candidate));
                    if (batch.limitReached()) throw new CaptureFailure(Status.LOCATOR_CANDIDATE_LIMIT, "candidate cap reached; no further input or retry");
                    offset += length;
                }
                byte[] dosAfter = state.read(admission, request, RawWindowLocatorContract.Frame.DOS_AFTER, 0, 64);
                byte[] peAfter = state.read(admission, request, RawWindowLocatorContract.Frame.PE_AFTER, 344, 544);
                requireLocatorHeaders(dosAfter, peAfter);
                if (!Arrays.equals(dos, dosAfter) || !Arrays.equals(pe, peAfter)) throw new CaptureFailure(Status.LOCATOR_LAYOUT_CHANGED, "actual before/after header bytes differ");
                if (!RawWindowLocatorContract.TEXT_SHA256.equals(state.prefixHash)) throw new CaptureFailure(Status.LOCATOR_CONTENT_CHANGED, "actual whole text digest contradicts the independently retained content hash; inherited image SHA cannot conceal it");
                status = Status.COMPLETE;
            } catch (CaptureFailure failure) { status = failure.status; error = shortError(failure.getMessage()); }
            catch (IOException | RuntimeException failure) { status = Status.FALLBACK_WRITE_FAILED; error = shortError(failure.toString()); }
            finally {
                if (opened) {
                    try { afterHeld = ports.held(); } catch (IOException | RuntimeException failure) { afterHeld = FileProbe.unavailable(failure.toString()); }
                    try { inputClose = ports.closeInput(); } catch (RuntimeException failure) { inputClose = CloseStatus.FAILED; error = shortError(error + "; close: " + failure); }
                    try { afterPath = ports.path(); } catch (IOException | RuntimeException failure) { afterPath = FileProbe.unavailable(failure.toString()); }
                }
                try { afterDirectory = ports.directory(); } catch (IOException | RuntimeException failure) { afterDirectory = DirectoryProbe.unavailable(failure.toString()); }
                if (status == Status.COMPLETE) {
                    if (afterHeld.status() != ProbeStatus.OBSERVED || afterPath.status() != ProbeStatus.OBSERVED || afterDirectory.status() != ProbeStatus.OBSERVED)
                        status = Status.POSTIDENTITY_UNAVAILABLE;
                    else if (!beforeHeld.value().equals(afterHeld.value()) || !beforeHeld.value().equals(afterPath.value())
                            || !beforeHeld.finalPath().equals(afterHeld.finalPath()) || !request.outputRootIdentity().equals(afterDirectory.value())) status = Status.INPUT_IDENTITY_CHANGED;
                    if (inputClose != CloseStatus.CLOSED) status = Status.SOURCE_CLOSE_FAILED;
                }
                try { ports.append(new RawWindowLocatorContract.After(afterHeld, afterPath, afterDirectory, inputClose, state.counts())); }
                catch (IOException | RuntimeException failure) { status = Status.FALLBACK_WRITE_FAILED; error = shortError(error + "; actual post journal: " + failure); }
            }
            // Prefix-only progress is durable even if body encoding, capacity or publication fails.
            try { ports.append(state.progress(false)); }
            catch (IOException | RuntimeException failure) { status = Status.FALLBACK_WRITE_FAILED; error = shortError(error + "; prefix progress: " + failure); }
            if (status != Status.FALLBACK_WRITE_FAILED) {
                RawWindowLocatorContract.Progress completeProgress = state.progress(status == Status.COMPLETE);
                var complete = new RawWindowLocatorContract.Body(RawWindowLocatorContract.BODY_SCHEMA, machine, Instant.now().toString(), request.runId(),
                        admission.requestRef(), request.fullHashEvidenceRef(), proof.sha256(), RawWindowLocatorContract.TEXT_SHA256, beforeHeld, beforePath, afterHeld, afterPath, afterDirectory,
                        inputClose, state.reads, state.candidates, completeProgress, state.counts(), status);
                try {
                    byte[] encoded = RawWindowCaptureJson.encode(complete); body = new BodySummary((long) encoded.length, RawWindowCaptureJson.hash(encoded), false);
                    if (encoded.length > request.bodyMaximumBytes()) { status = Status.BODY_OVERSIZE; error = "encoded locator body exceeds reserved maximum; actual prefix/candidates/postidentity retained"; }
                    else {
                        ports.publishBody(encoded); body = new BodySummary((long) encoded.length, RawWindowCaptureJson.hash(encoded), true);
                        if (status == Status.COMPLETE) ports.append(completeProgress);
                    }
                } catch (IOException | RuntimeException failure) { status = Status.BODY_OUTPUT_FAILED; error = shortError(failure.toString()); }
            }
            try { ports.append(new RawWindowLocatorContract.Finished(status, body, state.counts(), error)); finalDurable = true; }
            catch (IOException | RuntimeException failure) { status = Status.FALLBACK_WRITE_FAILED; error = shortError(error + "; final journal: " + failure); }
        } catch (IOException | RuntimeException failure) { status = started ? Status.FALLBACK_WRITE_FAILED : Status.REJECTED_BEFORE_INPUT; error = shortError(failure.toString()); }
        finally { try { ports.close(); } catch (IOException | RuntimeException failure) { status = Status.SOURCE_CLOSE_FAILED; error = shortError(error + "; cleanup: " + failure); } }
        return new RawWindowLocatorContract.Result(RawWindowLocatorContract.RESULT_SCHEMA, machine, Instant.now().toString(), request.runId(), status,
                Path.of(request.outputRoot()).resolve("fallback.jsonl").toString(), finalDurable, state.counts(), RawWindowLocatorContract.TEXT_SHA256, afterHeld, afterPath, afterDirectory,
                inputClose, state.reads, state.candidates, state.progress(status == Status.COMPLETE), body, error);
    }
    private static void fresh(Admission admission, CaptureRequest request) throws CaptureFailure {
        if (!Instant.now().isBefore(Instant.parse(admission.reviewAtUtc())) || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc())))
            throw new CaptureFailure(Status.DEADLINE_EXPIRED, "finite capture deadline expired before next native input");
    }
    private static void requireLocatorHeaders(byte[] dos, byte[] pe) throws CaptureFailure {
        boolean valid = dos.length == 64 && pe.length == 544 && ushort(dos, 0) == 0x5a4d
                && RawWindowLocatorContract.littleInt(dos, 60) == 344 && RawWindowLocatorContract.littleInt(pe, 0) == 0x4550
                && ushort(pe, 4) == 0x8664 && ushort(pe, 6) == 7 && RawWindowLocatorContract.littleInt(pe, 8) == 1_791_204_405
                && ushort(pe, 20) == 240 && ushort(pe, 24) == 0x20b
                && Integer.toUnsignedLong(RawWindowLocatorContract.littleInt(pe, 48)) == 0x40000000L && RawWindowLocatorContract.littleInt(pe, 52) == 1
                && RawWindowLocatorContract.littleInt(pe, 160) == 0x5dc3000 && RawWindowLocatorContract.littleInt(pe, 164) == 2_933_220
                && pe[264] == '.' && pe[265] == 't' && pe[266] == 'e' && pe[267] == 'x' && pe[268] == 't' && pe[269] == 0 && pe[270] == 0 && pe[271] == 0
                && RawWindowLocatorContract.littleInt(pe, 272) == RawWindowLocatorContract.TEXT_VIRTUAL_BYTES
                && RawWindowLocatorContract.littleInt(pe, 276) == RawWindowLocatorContract.TEXT_RVA
                && RawWindowLocatorContract.littleInt(pe, 280) == RawWindowLocatorContract.TEXT_BYTES
                && RawWindowLocatorContract.littleInt(pe, 284) == RawWindowLocatorContract.TEXT_OFFSET;
        if (!valid) throw new CaptureFailure(Status.LOCATOR_LAYOUT_CHANGED, "actual DOS/PE x64/timestamp/imagebase/exception/.text layout differs; no inherited layout fallback");
    }
    private static int ushort(byte[] bytes, int offset) { return (bytes[offset] & 255) | (bytes[offset + 1] & 255) << 8; }
    private static final class LocatorState {
        private final Ports ports; private final MessageDigest digest;
        private long requestedLocator, reportedLocator, requestedMetadata, reportedMetadata;
        private int attempts, unknown; private long prefixBytes, scannedThrough = RawWindowLocatorContract.TEXT_OFFSET;
        private String prefixHash = RawWindowCaptureJson.hash(new byte[0]); private boolean scanComplete;
        private final List<RawWindowLocatorContract.ReadActual> reads = new ArrayList<>();
        private final List<RawWindowLocatorContract.Candidate> candidates = new ArrayList<>();
        private LocatorState(Ports ports) throws IOException {
            this.ports = Objects.requireNonNull(ports);
            try { digest = MessageDigest.getInstance("SHA-256"); digest.clone(); }
            catch (NoSuchAlgorithmException | CloneNotSupportedException unavailable) { throw new IOException("incremental SHA-256 snapshot provider unavailable before native input", unavailable); }
        }
        private RawWindowLocatorContract.Counts counts() { return new RawWindowLocatorContract.Counts(RawWindowLocatorContract.BudgetClass.DEDICATED_M1_LOCATOR,
                requestedLocator, reportedLocator, requestedMetadata, reportedMetadata, ports.fileIdentityApiBufferChargeUpper(), attempts, unknown, false, null); }
        private RawWindowLocatorContract.Progress progress(boolean complete) {
            return new RawWindowLocatorContract.Progress(new RawWindowLocatorContract.Digest(prefixBytes, prefixHash, complete ? prefixHash : null),
                    scannedThrough, candidates.size(), scanComplete);
        }
        private byte[] read(Admission admission, RawWindowLocatorContract.Request request, RawWindowLocatorContract.Frame frame, long offset, int length) throws IOException {
            fresh(admission, request); boolean text = frame == RawWindowLocatorContract.Frame.TEXT;
            if (text) requestedLocator = Math.addExact(requestedLocator, length); else requestedMetadata = Math.addExact(requestedMetadata, length);
            ReadRange range = new ReadRange(offset, length);
            ports.append(new RawWindowLocatorContract.Intent(reads.size(), frame, range, counts())); attempts++;
            ReadResult actual;
            try { actual = ports.read(range); }
            catch (IOException | RuntimeException failure) { actual = new ReadResult(ReadStatus.OUTCOME_UNKNOWN, null, 0, shortError(failure.toString())); }
            byte[] bytes = actual.returnedBytes();
            if (bytes != null && bytes.length > length) { actual = new ReadResult(ReadStatus.OUTCOME_UNKNOWN, null, actual.win32Error(), "adapter returned more than requested"); bytes = null; }
            Integer returned = bytes == null ? null : bytes.length; String hash = bytes == null ? null : RawWindowCaptureJson.hash(bytes);
            if (bytes == null) unknown++; else if (text) reportedLocator = Math.addExact(reportedLocator, bytes.length);
            else reportedMetadata = Math.addExact(reportedMetadata, bytes.length);
            if (frame == RawWindowLocatorContract.Frame.TEXT && bytes != null) {
                digest.update(bytes); prefixBytes += bytes.length;
                try { prefixHash = HexFormat.of().formatHex(((MessageDigest) digest.clone()).digest()); }
                catch (CloneNotSupportedException impossibleAfterPrecheck) { throw new IOException("SHA snapshot provider changed", impossibleAfterPrecheck); }
            }
            ReadStatus observed = actual.status(); if (observed == ReadStatus.COMPLETE && returned != length) observed = ReadStatus.SHORT_READ;
            String header = frame == RawWindowLocatorContract.Frame.TEXT || bytes == null ? null : HexFormat.of().formatHex(bytes);
            var record = new RawWindowLocatorContract.ReadActual(reads.size(), frame, offset, length, observed, returned, hash, actual.win32Error(), header,
                    new RawWindowLocatorContract.Digest(prefixBytes, prefixHash, null), actual.error()); reads.add(record);
            ports.append(new RawWindowLocatorContract.ReadObserved(record, counts()));
            if (bytes == null) throw new CaptureFailure(Status.READ_OUTCOME_UNKNOWN, "locator native read outcome unknown; no retry");
            if (observed != ReadStatus.COMPLETE) throw new CaptureFailure(Status.READ_INCOMPLETE, "locator short/error read retained; no retry"); return bytes;
        }
    }
    private static Counts counts(Amounts charge, Amounts reported, Ports ports, int attempts, int unknown) {
        return new Counts(charge, reported, ports.fileIdentityApiBufferChargeUpper(), attempts, unknown, false, null);
    }
    private static final class CaptureFailure extends IOException {
        private static final long serialVersionUID = 1L;
        private final Status status;
        private CaptureFailure(Status status, String message) { super(message); this.status = status; }
    }
}
