package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** The actual shared engine and pure matcher, using software ports only. No EXE opens or native qualification. */
final class RawWindowLocatorTest {
    @TempDir Path temporary;
    private static final String MACHINE = "locator-software-machine", FUTURE = "2099-01-01T00:00:00Z";
    private static final SharedSourceFiles.DirectoryIdentity DIRECTORY = new SharedSourceFiles.DirectoryIdentity("15", "99", "1");
    private static final SharedSourceFiles.NativeFile FILE = new SharedSourceFiles.NativeFile("15", "18446744073709550001", "3", "fffffffffffff9b1", "1", "2", "3", 101_040_248, 101_044_224, 1);
    private enum Fault { NONE, START, INTENT, READ_EVENT, UNKNOWN, SHORT, BODY, POST, CLOSE, LAYOUT, CAP }
    private record Fixture(RawWindowLocatorContract.Request request, Admission admission, FileRef admissionRef, RawWindowImageProof.Proof proof, FakePorts ports) { }

    @Test void oneHeldOpenRejectsWholeSegmentContentContradictionWithTwoActualEncodingFixturesAndNoRawFiles() throws Exception {
        Fixture fixture = fixture(Fault.NONE, 256, RawWindowLocatorContract.MAX_BODY_BYTES);
        RawWindowLocatorContract.Result result = run(fixture);
        assertEquals(Status.LOCATOR_CONTENT_CHANGED, result.status()); assertEquals(1, fixture.ports().opens); assertEquals(72, fixture.ports().reads);
        assertEquals(0, fixture.ports().rawCalls); assertEquals(2, result.candidates().size());
        assertEquals(0x9e16ecL, result.candidates().getFirst().rva()); assertEquals("488d0d4dfb2d05", result.candidates().getFirst().encodingHex());
        assertEquals(0x25a9c95L, result.candidates().getLast().rva()); assertEquals("488b0574797103", result.candidates().getLast().encodingHex());
        assertEquals(RawWindowLocatorContract.BudgetClass.DEDICATED_M1_LOCATOR, result.counts().budgetClass());
        assertEquals(RawWindowLocatorContract.TEXT_BYTES, result.counts().reportedLocatorBytes()); assertEquals(1216, result.counts().reportedMetadataBytes());
        assertEquals(result.counts().requestedLocatorBytes(), result.counts().reportedLocatorBytes());
        assertEquals(result.counts().requestedMetadataBytes(), result.counts().reportedMetadataBytes());
        assertEquals(RawWindowLocatorContract.TEXT_BYTES, result.progress().digest().prefixBytes());
        assertNull(result.progress().digest().fullSegmentSha256());
        assertNotEquals(result.expectedSegmentSha256(), result.progress().digest().prefixSha256());
        assertTrue(result.progress().candidateScanComplete()); assertTrue(result.fallbackFinalDurable()); assertTrue(result.body().published());
        assertFalse(result.counts().physicalIoMeasured()); assertNull(result.counts().totalPhysicalIoBytes());
        assertEquals(result, RawWindowCaptureJson.decode(RawWindowCaptureJson.encode((CaptureOutcome) result), RawWindowLocatorContract.Result.class, MAX_OUTPUT_BYTES));
        for (Event event : fixture.ports().events) {
            byte[] encoded = RawWindowCaptureJson.encode(event); assertTrue(encoded.length <= 4095);
            assertEquals(event, RawWindowCaptureJson.decodeJournalLine(encoded).value());
        }
        assertTrue(fixture.ports().events.indexOf(fixture.ports().events.stream().filter(RawWindowLocatorContract.After.class::isInstance).findFirst().orElseThrow())
                < fixture.ports().bodyAtEventCount);
    }

    @Test void actualLeaFixtureSpansFeedsAndRetainsIgnoredPrefixContextWithoutInventingAnInstructionBoundary() {
        ExactRipRelativeLocator matcher = new ExactRipRelativeLocator(); long at = 0x9e16ecL - RawWindowLocatorContract.TEXT_RVA;
        long position = 0;
        while (position < at - 1) { int count = (int) Math.min(RawWindowLocatorContract.CHUNK_BYTES, at - 1 - position);
            assertTrue(matcher.accept(new byte[count], position, false, 256).candidates().isEmpty()); position += count; }
        byte[] prefix = HexFormat.of().parseHex("67488d0d");
        assertTrue(matcher.accept(prefix, position, false, 256).candidates().isEmpty()); position += prefix.length;
        var result = matcher.accept(HexFormat.of().parseHex("4dfb2d05"), position, true, 256);
        assertEquals(1, result.candidates().size()); var candidate = result.candidates().getFirst();
        assertEquals(0x9e16ecL, candidate.rva()); assertEquals(RawWindowLocatorContract.Boundary.UNVALIDATED, candidate.boundary());
        assertTrue(candidate.beforeContextHex().endsWith("67")); assertTrue(candidate.shortAfterContext());
    }

    @Test void immediateStoreUsesElevenByteNextRipAndClosedFormsRejectSibMissingRexNegativeDispAndWrongTargets() {
        byte[] bytes = new byte[256]; put(bytes, 10, 0xc7, RawWindowLocatorContract.QUEUE_RVA, 11);
        // The nextRIP must include imm32; a seven-byte calculation gives the wrong exact target.
        var batch = new ExactRipRelativeLocator().accept(bytes, 0, true, 256);
        assertEquals(1, batch.candidates().size()); assertEquals(11, batch.candidates().getFirst().assumedLength());
        assertEquals(RawWindowLocatorContract.Operation.STORE_IMMEDIATE32, batch.candidates().getFirst().operation());
        byte[] negatives = HexFormat.of().parseHex("488b05ffffffff488b0425000000008b050000000049c7050000000000000000488d0500000000");
        assertTrue(new ExactRipRelativeLocator().accept(negatives, 0, true, 256).candidates().isEmpty());
        byte[] truncated = Arrays.copyOf(bytes, 20); assertTrue(new ExactRipRelativeLocator().accept(truncated, 0, true, 256).candidates().isEmpty());
    }

    @Test void exact256CandidateCapStopsFurtherInputButRetainsActualWholeReadChunkAndPrefixHash() throws Exception {
        Fixture fixture = fixture(Fault.CAP, 256, RawWindowLocatorContract.MAX_BODY_BYTES); var result = run(fixture);
        assertEquals(Status.LOCATOR_CANDIDATE_LIMIT, result.status()); assertEquals(3, fixture.ports().reads);
        assertEquals(256, result.candidates().size()); assertEquals(RawWindowLocatorContract.CHUNK_BYTES, result.counts().reportedLocatorBytes());
        assertEquals(RawWindowLocatorContract.CHUNK_BYTES, result.progress().digest().prefixBytes());
        assertNull(result.progress().digest().fullSegmentSha256()); assertFalse(result.progress().candidateScanComplete());
        assertEquals(ProbeStatus.OBSERVED, result.afterHeld().status()); assertEquals(CloseStatus.CLOSED, result.inputClose());
        assertEquals(0, fixture.ports().rawCalls); assertTrue(result.fallbackFinalDurable());
    }

    @Test void unknownAndShortReadRetainDistinctActualCountersWithoutRetryOrPseudoZero() throws Exception {
        for (Fault fault : List.of(Fault.UNKNOWN, Fault.SHORT)) {
            Fixture fixture = fixture(fault, 256, RawWindowLocatorContract.MAX_BODY_BYTES); var result = run(fixture);
            assertEquals(fault == Fault.UNKNOWN ? Status.READ_OUTCOME_UNKNOWN : Status.READ_INCOMPLETE, result.status());
            assertEquals(3, fixture.ports().reads); assertEquals(RawWindowLocatorContract.CHUNK_BYTES, result.counts().requestedLocatorBytes());
            assertEquals(fault == Fault.UNKNOWN ? 1 : 0, result.counts().unknownReadOutcomes());
            assertEquals(fault == Fault.UNKNOWN ? 0 : 2, result.counts().reportedLocatorBytes());
            assertEquals(fault == Fault.UNKNOWN ? null : Integer.valueOf(2), result.reads().getLast().reportedBytes());
            assertNull(result.progress().digest().fullSegmentSha256()); assertEquals(ProbeStatus.OBSERVED, result.afterPath().status());
        }
    }

    @Test void failedStartAndTextIntentPerformNoUnrecordedTextReadAndFailedReadEventRetainsTheActualHash() throws Exception {
        for (Fault fault : List.of(Fault.START, Fault.INTENT, Fault.READ_EVENT)) {
            Fixture fixture = fixture(fault, 256, RawWindowLocatorContract.MAX_BODY_BYTES); var result = run(fixture);
            assertNotEquals(Status.COMPLETE, result.status());
            assertEquals(fault == Fault.START ? 0 : fault == Fault.INTENT ? 2 : 3, fixture.ports().reads);
            if (fault == Fault.READ_EVENT) {
                assertEquals(RawWindowLocatorContract.CHUNK_BYTES, result.reads().getLast().reportedBytes());
                assertNotNull(result.reads().getLast().sha256()); assertEquals(ProbeStatus.OBSERVED, result.afterHeld().status());
            }
            assertNull(result.progress().digest().fullSegmentSha256());
        }
    }

    @Test void bodyOversizeAndBodyWriteFailurePreserveAllActualReadsPostidentityAndPrefixWithoutPublishingFullHash() throws Exception {
        for (Fault fault : List.of(Fault.NONE, Fault.BODY)) {
            Fixture fixture = fixture(fault, 256, fault == Fault.NONE ? 1 : RawWindowLocatorContract.MAX_BODY_BYTES); var result = run(fixture);
            assertEquals(fault == Fault.NONE ? Status.BODY_OVERSIZE : Status.BODY_OUTPUT_FAILED, result.status());
            assertEquals(72, fixture.ports().reads); assertEquals(RawWindowLocatorContract.TEXT_BYTES, result.progress().digest().prefixBytes());
            assertFalse(result.body().published()); assertTrue(result.body().encodedBytes() > 1); assertTrue(result.fallbackFinalDurable());
            assertNull(result.progress().digest().fullSegmentSha256()); assertEquals(ProbeStatus.OBSERVED, result.afterHeld().status());
            assertTrue(fixture.ports().events.stream().filter(RawWindowLocatorContract.Progress.class::isInstance)
                    .map(RawWindowLocatorContract.Progress.class::cast).allMatch(progress -> progress.digest().fullSegmentSha256() == null));
        }
    }

    @Test void contentContradictionStillRetainsTruePostAndCloseFaultsWhileLayoutMismatchStopsBeforeText() throws Exception {
        for (Fault fault : List.of(Fault.POST, Fault.CLOSE, Fault.LAYOUT)) {
            Fixture fixture = fixture(fault, 256, RawWindowLocatorContract.MAX_BODY_BYTES); var result = run(fixture);
            assertEquals(fault == Fault.LAYOUT ? Status.LOCATOR_LAYOUT_CHANGED : Status.LOCATOR_CONTENT_CHANGED, result.status());
            assertEquals(fault == Fault.LAYOUT ? 2 : 72, fixture.ports().reads); assertNull(result.progress().digest().fullSegmentSha256());
            assertEquals(fault == Fault.POST ? ProbeStatus.UNAVAILABLE : ProbeStatus.OBSERVED, result.afterHeld().status());
            assertEquals(ProbeStatus.OBSERVED, result.afterDirectory().status()); assertTrue(fixture.ports().events.stream().anyMatch(RawWindowLocatorContract.After.class::isInstance));
            if (fault == Fault.CLOSE) assertEquals(CloseStatus.FAILED, result.inputClose());
        }
    }

    @Test void strictRequestUnionRejectsWrongModeTargetsConsumerScopeCoercionAndMalformedRanges() throws Exception {
        Fixture fixture = fixture(Fault.NONE, 256, RawWindowLocatorContract.MAX_BODY_BYTES); byte[] encoded = RawWindowCaptureJson.encode(fixture.request());
        assertEquals(fixture.request(), RawWindowCaptureJson.decodeRequest(encoded));
        ObjectNode root = (ObjectNode) RawWindowCaptureJson.tree(encoded); root.put("consumer", "M2"); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); root.put("chunk_bytes", 8192); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); root.put("candidate_limit", 257); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); root.put("candidate_limit", true); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); root.put("candidate_limit", 256.0); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); root.put("schema", "unknown"); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); root.putNull("output_root_identity"); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); ((ObjectNode) root.get("targets")).put("queue_rva", 123); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); ((ObjectNode) root.get("segment")).put("file_offset", 1025); rejects(root);
        root = (ObjectNode) RawWindowCaptureJson.tree(encoded); root.put("extra", 1); rejects(root);
        Admission wrong = new Admission(ADMISSION_SCHEMA, MACHINE, Consumer.M1, "/root/budget_fast_lane", CaptureScope.BOUNDED_READ_ONLY_FILE_WINDOWS,
                fixture.admission().requestRef(), fixture.admission().financialGrantRef(), FUTURE);
        var result = RawWindowCollector.executeLocator(wrong, fixture.admissionRef(), fixture.request(), fixture.proof(), fixture.ports());
        assertEquals(Status.REJECTED_BEFORE_INPUT, result.status()); assertEquals(0, fixture.ports().reads);
    }
    private static void rejects(ObjectNode node) { assertThrows(Exception.class, () -> RawWindowCaptureJson.decodeRequest(node.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
    private RawWindowLocatorContract.Result run(Fixture fixture) throws IOException {
        return RawWindowCollector.executeLocator(fixture.admission(), fixture.admissionRef(), fixture.request(), fixture.proof(), fixture.ports());
    }
    private Fixture fixture(Fault fault, int limit, int bodyMaximum) {
        FileRef full = new FileRef(temporary.resolve("actual-original.json").toString(), 6746, RawWindowLocatorContract.FULL_HASH_ORIGINAL_SHA256);
        var request = new RawWindowLocatorContract.Request(RawWindowLocatorContract.REQUEST_SCHEMA, MACHINE, Consumer.M1, "locator-software-case",
                temporary.resolve("software-image.exe").toString(), full, temporary.resolve("output").toString(), DIRECTORY,
                RawWindowLocatorContract.Locator.M1_MANAGER_QUEUE_TEXT, new RawWindowLocatorContract.Segment(1024, 4096, 71_141_888, 71_141_448),
                new RawWindowLocatorContract.Targets(RawWindowLocatorContract.MANAGER_RVA, RawWindowLocatorContract.QUEUE_RVA),
                RawWindowLocatorContract.CHUNK_BYTES, limit, 8192, 524_288, bodyMaximum, FUTURE);
        FileRef requestRef = ref("request.json"), admissionRef = ref("admission.json");
        Admission admission = new Admission(ADMISSION_SCHEMA, MACHINE, Consumer.M1, "/root/budget_fast_lane", CaptureScope.M1_EXACT_TEXT_RIPREL_LOCATOR, requestRef, ref("financial.json"), FUTURE);
        var legacy = new RawWindowImageProof.LegacyIdentity(new java.math.BigInteger(FILE.legacyFileIdHex(), 16).toString(), FILE.fileIdDecimal(), FILE.volumeSerialDecimal(),
                FILE.logicalBytes(), FILE.creationFiletimeDecimal(), FILE.lastWriteFiletimeDecimal(), FILE.changeFiletimeDecimal(), 32, FILE.linkCount());
        var proof = new RawWindowImageProof.Proof(MACHINE, request.inputPath(), RawWindowLocatorContract.IMAGE_SHA256, legacy, full);
        FakePorts ports = new FakePorts(fault); ports.inputPath = request.inputPath();
        return new Fixture(request, admission, admissionRef, proof, ports);
    }
    private FileRef ref(String name) { return new FileRef(temporary.resolve(name).toString(), 1, "a".repeat(64)); }
    private static void put(byte[] output, int at, int opcode, long target, int length) {
        output[at] = 0x48; output[at + 1] = (byte) opcode; output[at + 2] = 5;
        ByteBuffer.wrap(output).order(ByteOrder.LITTLE_ENDIAN).putInt(at + 3, Math.toIntExact(target - (RawWindowLocatorContract.TEXT_RVA + at + length)));
    }
    private static byte[] dos() { byte[] bytes = new byte[64]; ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).putShort(0, (short) 0x5a4d).putInt(60, 344); return bytes; }
    private static byte[] pe() {
        byte[] bytes = new byte[544]; ByteBuffer buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        buffer.putInt(0, 0x4550).putShort(4, (short) 0x8664).putShort(6, (short) 7).putInt(8, 1_791_204_405).putShort(20, (short) 240)
                .putShort(24, (short) 0x20b).putLong(48, 0x140000000L).putInt(160, 0x5dc3000).putInt(164, 2_933_220);
        System.arraycopy(new byte[]{'.', 't', 'e', 'x', 't'}, 0, bytes, 264, 5);
        buffer.putInt(272, 71_141_448).putInt(276, 4096).putInt(280, 71_141_888).putInt(284, 1024); return bytes;
    }
    private static final class FakePorts implements RawWindowCollector.Ports {
        private final Fault fault; private final List<Event> events = new ArrayList<>();
        private int reads, opens, heldCalls, rawCalls, bodyAtEventCount; private boolean poisoned;
        private FakePorts(Fault fault) { this.fault = fault; }
        @Override public String machineId() { return MACHINE; }
        @Override public void startJournal(Started start) throws IOException { if (fault == Fault.START) throw new IOException("injected start failure"); events.add(start); }
        @Override public void append(Event event) throws IOException {
            if (poisoned || fault == Fault.INTENT && event instanceof RawWindowLocatorContract.Intent intent && intent.frame() == RawWindowLocatorContract.Frame.TEXT
                    || fault == Fault.READ_EVENT && event instanceof RawWindowLocatorContract.ReadObserved observed && observed.actual().frame() == RawWindowLocatorContract.Frame.TEXT) {
                poisoned = true; throw new IOException("injected durable event failure"); }
            events.add(event);
        }
        @Override public void openInput() { opens++; }
        @Override public FileProbe held() { heldCalls++; return fault == Fault.POST && heldCalls == 2 ? FileProbe.unavailable("actual post probe failed") : new FileProbe(ProbeStatus.OBSERVED, FILE, temporarySpelling(), ""); }
        private String temporarySpelling() { return inputPath; }
        private String inputPath;
        @Override public FileProbe path() { return new FileProbe(ProbeStatus.OBSERVED, FILE, null, ""); }
        @Override public DirectoryProbe directory() { return new DirectoryProbe(ProbeStatus.OBSERVED, DIRECTORY, ""); }
        @Override public ReadResult read(ReadRange range) throws IOException {
            reads++;
            if (range.fileOffset() == 0) return new ReadResult(ReadStatus.COMPLETE, dos(), 0, "");
            if (range.fileOffset() == 344) { byte[] bytes = pe(); if (fault == Fault.LAYOUT) bytes[276]++; return new ReadResult(ReadStatus.COMPLETE, bytes, 0, ""); }
            if (fault == Fault.UNKNOWN) throw new IOException("actual native result unavailable");
            if (fault == Fault.SHORT) return new ReadResult(ReadStatus.SHORT_READ, new byte[]{1, 2}, 0, "short actual result");
            byte[] bytes = new byte[range.length()]; long relative = range.fileOffset() - RawWindowLocatorContract.TEXT_OFFSET;
            inject(bytes, relative, 0x9e16ecL - RawWindowLocatorContract.TEXT_RVA, "488d0d4dfb2d05");
            inject(bytes, relative, 0x25a9c95L - RawWindowLocatorContract.TEXT_RVA, "488b0574797103");
            if (fault == Fault.CAP) for (int i = 0; i < 256; i++) put(bytes, 100 + i * 48, 0x8d, RawWindowLocatorContract.MANAGER_RVA, 7);
            return new ReadResult(ReadStatus.COMPLETE, bytes, 0, "");
        }
        private static void inject(byte[] target, long relative, long instruction, String original) {
            byte[] bytes = HexFormat.of().parseHex(original);
            for (int i = 0; i < bytes.length; i++) { long at = instruction + i - relative; if (at >= 0 && at < target.length) target[(int) at] = bytes[i]; }
        }
        @Override public RawArtifact preserveRaw(int index, byte[] actual) { rawCalls++; throw new AssertionError("locator must not create raw window files"); }
        @Override public void publishBody(byte[] encoded) throws IOException { bodyAtEventCount = events.size(); if (fault == Fault.BODY) throw new IOException("actual body output failure");
            RawWindowCaptureJson.decode(encoded, RawWindowLocatorContract.Body.class, RawWindowLocatorContract.MAX_BODY_BYTES); }
        @Override public long fileIdentityApiBufferChargeUpper() { return 512; }
        @Override public CloseStatus closeInput() { if (fault == Fault.CLOSE) throw new IllegalStateException("actual close failed"); return CloseStatus.CLOSED; }
        @Override public void close() { }
    }
}
