package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** Persistent collector software faults plus actual self-created Windows directory custody. No real EXE input is opened. */
final class RawWindowCollectorTest {
    @TempDir Path temporary;
    private static final String MACHINE = "software-fixture-machine";
    private static final String FUTURE = "2099-01-01T00:00:00Z";
    private static final SharedSourceFiles.DirectoryIdentity DIRECTORY = new SharedSourceFiles.DirectoryIdentity("15", "99", "1");
    private static final SharedSourceFiles.NativeFile FILE = new SharedSourceFiles.NativeFile("15", "18446744073709550001", "3", "fffffffffffff9b1", "1", "2", "3", 4096, 4096, 1);
    private enum Fault { NONE, START_WRITE, INTENT_WRITE, RESULT_WRITE, RAW_RESULT_WRITE, BODY_WRITE, RAW_WRITE, POST_HELD, READ_THROW, SHORT_READ, IDENTITY_DRIFT, CLOSE_THROW }
    private record Fixture(Request request, Admission admission, FileRef admissionRef, RawWindowImageProof.Proof proof, FakePorts ports) { }

    @Test void minimumFallbackIsForcedBeforeAnyReadAndPostidentityPrecedesBody() throws Exception {
        Fixture fixture = fixture(Consumer.M6, Fault.NONE, 65_536, false); Result result = run(fixture);
        assertEquals(Status.COMPLETE, result.status()); assertTrue(result.fallbackFinalDurable()); assertTrue(result.body().published());
        assertEquals(1, fixture.ports().reads); assertEquals(2, fixture.ports().heldProbes);
        assertEquals(List.of("START_DURABLE", "OPEN_INPUT", "BEFORE_DURABLE", "INTENT_DURABLE", "READ", "READ_DURABLE",
                "RAW", "RAW_DURABLE", "CLOSE_INPUT", "AFTER_DURABLE", "BODY", "FINISHED_DURABLE"), fixture.ports().order);
        assertEquals(new Amounts(4, 0, 0), result.counts().requestedCharge()); assertEquals(new Amounts(4, 0, 0), result.counts().reportedRead());
        assertFalse(result.counts().physicalIoMeasured()); assertNull(result.counts().totalPhysicalIoBytes());
        for (Event event : fixture.ports().events) {
            var decoded = RawWindowCaptureJson.decodeJournalLine(RawWindowCaptureJson.encode(event));
            assertEquals(kindOf(event), decoded.event()); assertEquals(event, decoded.value());
        }
        assertArrayEquals(fixture.ports().readBytes, fixture.ports().rawBytes);
    }

    @Test void reproduces18cBodyOversizeAfterReadsButRetainsActualCountsHashesAndPostidentity() throws Exception {
        Fixture fixture = fixture(Consumer.M6, Fault.NONE, 1, false); Result result = run(fixture);
        assertEquals(Status.BODY_OVERSIZE, result.status()); assertFalse(result.body().published());
        assertTrue(result.body().encodedBytes() > 1); assertTrue(result.fallbackFinalDurable());
        assertEquals(RawWindowCaptureJson.hash(fixture.ports().readBytes), result.windows().getFirst().sha256());
        assertEquals(4, result.windows().getFirst().reportedBytes()); assertEquals(ProbeStatus.OBSERVED, result.afterHeld().status());
        assertTrue(fixture.ports().events.stream().anyMatch(After.class::isInstance));
        Finished last = (Finished) fixture.ports().events.getLast();
        assertEquals(Status.BODY_OVERSIZE, last.status()); assertEquals(result.body(), last.body());
        assertFalse(fixture.ports().order.contains("BODY"));
    }

    @Test void bodyAndRawWriteFailuresRetainTheAlreadyObservedWindowAndDoNotRepeatReads() throws Exception {
        for (Fault fault : List.of(Fault.BODY_WRITE, Fault.RAW_WRITE)) {
            Fixture fixture = fixture(Consumer.M4, fault, 65_536, true); Result result = run(fixture);
            assertEquals(fault == Fault.RAW_WRITE ? Status.RAW_OUTPUT_FAILED : Status.BODY_OUTPUT_FAILED, result.status());
            assertTrue(result.fallbackFinalDurable()); assertEquals(fault == Fault.RAW_WRITE ? 1 : 2, fixture.ports().reads);
            assertEquals(RawWindowCaptureJson.hash(fixture.ports().readBytes), result.windows().getFirst().sha256());
            assertEquals(ProbeStatus.OBSERVED, result.afterHeld().status()); assertEquals(CloseStatus.CLOSED, result.inputClose());
        }
    }

    @Test void fallbackStartAndIntentWriteFailuresPreventNativeInput() throws Exception {
        for (Fault fault : List.of(Fault.START_WRITE, Fault.INTENT_WRITE)) {
            Fixture fixture = fixture(Consumer.M0, fault, 65_536, false); Result result = run(fixture);
            assertEquals(0, fixture.ports().reads); assertEquals(0, result.counts().readAttempts());
            assertEquals(fault == Fault.START_WRITE ? Status.REJECTED_BEFORE_INPUT : Status.FALLBACK_WRITE_FAILED, result.status());
            if (fault == Fault.INTENT_WRITE) assertEquals(new Amounts(4, 0, 0), result.counts().requestedCharge());
        }
    }

    @Test void failedResultJournalPreservesIntentConservativeChargeAndStdoutResultOriginalHash() throws Exception {
        Fixture fixture = fixture(Consumer.M1, Fault.RESULT_WRITE, 65_536, true); Result result = run(fixture);
        assertEquals(Status.FALLBACK_WRITE_FAILED, result.status()); assertFalse(result.fallbackFinalDurable());
        assertEquals(1, fixture.ports().reads); assertTrue(fixture.ports().events.stream().anyMatch(Intent.class::isInstance));
        assertEquals(new Amounts(4, 0, 0), result.counts().reportedRead());
        assertEquals(RawWindowCaptureJson.hash(fixture.ports().readBytes), result.windows().getFirst().sha256());
        assertEquals(ProbeStatus.OBSERVED, result.afterHeld().status());
        assertEquals(ProbeStatus.OBSERVED, result.afterPath().status());
    }

    @Test void unknownAndShortNativeResultsAreDistinctAndNeverRetried() throws Exception {
        Fixture unknown = fixture(Consumer.M5, Fault.READ_THROW, 65_536, true); Result uncertain = run(unknown);
        assertEquals(Status.READ_OUTCOME_UNKNOWN, uncertain.status()); assertEquals(1, unknown.ports().reads);
        assertEquals(1, uncertain.counts().unknownReadOutcomes()); assertEquals(new Amounts(0, 0, 0), uncertain.counts().reportedRead());
        assertEquals(new Amounts(4, 0, 0), uncertain.counts().requestedCharge()); assertNull(uncertain.windows().getFirst().reportedBytes());
        Fixture partial = fixture(Consumer.M3, Fault.SHORT_READ, 65_536, true); Result shortRead = run(partial);
        assertEquals(Status.READ_INCOMPLETE, shortRead.status()); assertEquals(1, partial.ports().reads);
        assertEquals(new Amounts(2, 0, 0), shortRead.counts().reportedRead()); assertEquals(2, partial.ports().rawBytes.length);
        assertTrue(shortRead.fallbackFinalDurable());
    }

    @Test void rawResultJournalFailureRetainsTheActualAlreadyCreatedArtifactInRootResult() throws Exception {
        Fixture fixture = fixture(Consumer.M6, Fault.RAW_RESULT_WRITE, 65_536, true); Result result = run(fixture);
        assertEquals(Status.FALLBACK_WRITE_FAILED, result.status()); assertEquals(1, fixture.ports().reads);
        assertEquals(OutputStatus.CREATED_VERIFIED, result.windows().getFirst().rawArtifact().status());
        assertEquals(RawWindowCaptureJson.hash(fixture.ports().rawBytes), result.windows().getFirst().rawArtifact().sha256());
        assertEquals(ProbeStatus.OBSERVED, result.afterHeld().status()); assertFalse(result.fallbackFinalDurable());
    }

    @Test void closeExceptionStillCapturesActualPathDirectoryAndDurableAfterWithoutBorrowingBefore() throws Exception {
        Fixture fixture = fixture(Consumer.M6, Fault.CLOSE_THROW, 65_536, false); Result result = run(fixture);
        assertEquals(Status.SOURCE_CLOSE_FAILED, result.status()); assertEquals(CloseStatus.FAILED, result.inputClose());
        assertEquals(ProbeStatus.OBSERVED, result.afterHeld().status()); assertEquals(ProbeStatus.OBSERVED, result.afterPath().status());
        assertEquals(ProbeStatus.OBSERVED, result.afterDirectory().status()); assertTrue(result.fallbackFinalDurable());
        assertTrue(fixture.ports().events.stream().anyMatch(After.class::isInstance)); assertEquals(1, fixture.ports().reads);
    }

    @Test void actualPostidentityFailureAndDriftAreRetainedWithoutBorrowingTheBeforeState() throws Exception {
        Fixture missing = fixture(Consumer.M7, Fault.POST_HELD, 65_536, false); Result unavailable = run(missing);
        assertEquals(Status.POSTIDENTITY_UNAVAILABLE, unavailable.status()); assertEquals(ProbeStatus.UNAVAILABLE, unavailable.afterHeld().status());
        assertNull(unavailable.afterHeld().value()); assertTrue(unavailable.fallbackFinalDurable());
        Fixture changed = fixture(Consumer.M2, Fault.IDENTITY_DRIFT, 65_536, false); Result drift = run(changed);
        assertEquals(Status.INPUT_IDENTITY_CHANGED, drift.status());
        assertNotEquals(FILE.changeFiletimeDecimal(), drift.afterHeld().value().changeFiletimeDecimal());
    }

    @Test void allEightConsumerRequestsUseTheOneLoopAndRepeatedOffsetsRemainChargedReads() throws Exception {
        for (Consumer consumer : Consumer.values()) {
            Fixture fixture = fixture(consumer, Fault.NONE, 65_536, true); Result result = run(fixture);
            assertEquals(Status.COMPLETE, result.status()); assertEquals(2, fixture.ports().reads);
            assertEquals(new Amounts(8, 0, 0), result.counts().requestedCharge());
            assertEquals(new Amounts(8, 0, 0), result.counts().reportedRead());
            assertEquals(consumer, fixture.ports().body.consumer());
        }
    }

    @Test void strictRequestAdmissionRoundtripRejectsBoolFloatStringMissingUnknownAndUnderreservedFallback() throws Exception {
        Fixture fixture = fixture(Consumer.M6, Fault.NONE, 65_536, false);
        byte[] valid = RawWindowCaptureJson.encode(fixture.request());
        assertEquals(fixture.request(), RawWindowCaptureJson.decode(valid, Request.class, 65_536));
        assertEquals(fixture.admission(), RawWindowCaptureJson.decode(RawWindowCaptureJson.encode(fixture.admission()), Admission.class, 65_536));
        ObjectNode root = tree(valid); ((ObjectNode) root.withArray("windows").get(0)).put("length", true); rejects(root);
        root = tree(valid); ((ObjectNode) root.withArray("windows").get(0)).put("file_offset", 0.0); rejects(root);
        root = tree(valid); root.put("file_identity_api_buffer_cap", "8192"); rejects(root);
        root = tree(valid); root.remove("body_maximum_bytes"); rejects(root);
        root = tree(valid); root.put("unknown", true); rejects(root);
        root = tree(valid); root.put("journal_maximum_bytes", 8192); rejects(root);
        root = tree(valid); root.putNull("windows"); rejects(root);
        root = tree(valid); root.put("consumer", 6); rejects(root);
        Admission wrongMachine = new Admission(ADMISSION_SCHEMA, "other-machine", fixture.request().consumer(), "/root/budget_fast_lane",
                CaptureScope.BOUNDED_READ_ONLY_FILE_WINDOWS, fixture.admission().requestRef(), fixture.admission().financialGrantRef(), FUTURE);
        Result rejected = RawWindowCollector.execute(wrongMachine, fixture.admissionRef(), fixture.request(), fixture.proof(), fixture.ports());
        assertEquals(Status.REJECTED_BEFORE_INPUT, rejected.status()); assertEquals(MACHINE, rejected.machineId()); assertEquals(0, fixture.ports().reads);
    }

    @Test void priorFullHashBindingUsesFullWidthNativeIdentityAndRejectsChangedMachineTimeOrLegacyId() throws Exception {
        Fixture fixture = fixture(Consumer.M6, Fault.NONE, 65_536, false);
        fixture.proof().requireCurrent(MACHINE, fixture.request().inputPath(), FILE);
        assertThrows(IOException.class, () -> fixture.proof().requireCurrent("other-machine", fixture.request().inputPath(), FILE));
        SharedSourceFiles.NativeFile wrongLegacy = new SharedSourceFiles.NativeFile(FILE.volumeSerialDecimal(), FILE.fileIdDecimal(), FILE.legacyVolumeSerialDecimal(),
                "0000000000000001", FILE.creationFiletimeDecimal(), FILE.lastWriteFiletimeDecimal(), FILE.changeFiletimeDecimal(), FILE.logicalBytes(), FILE.allocatedBytes(), FILE.linkCount());
        assertThrows(IOException.class, () -> fixture.proof().requireCurrent(MACHINE, fixture.request().inputPath(), wrongLegacy));
        var changed = drifted(); assertThrows(IOException.class, () -> fixture.proof().requireCurrent(MACHINE, fixture.request().inputPath(), changed));
    }


    /** Real Windows filesystem custody on a self-created directory; input EXE is never opened. */
    @Test void retainedOutputDirectoryDeniesRenameAndDeleteAccessUntilActualPortClose() throws Exception {
        assertTrue(System.getProperty("os.name").startsWith("Windows"),"MISSING actual Windows filesystem environment");
        Path root=java.nio.file.Files.createDirectory(temporary.resolve("custody-root"));
        Path renamed=temporary.resolve("custody-renamed"),unopened=temporary.resolve("NOT-OPENED.exe");
        String machine=WindowsJobProcess.currentMachineId();
        var identity=SharedSourceFiles.nativeDirectory(root);
        FileRef proof=ref("software-proof-not-read.json");
        var request=new Request(REQUEST_SCHEMA,machine,Consumer.M7,"software-native-custody",unopened.toString(),
            proof,root.toString(),identity,List.of(new Window("not-read",Kind.METADATA,0,1)),
            new Amounts(0,1,0),8192,18432,32768,FUTURE);
        try(var ports=new RawWindowNativeIo(request)) {
            ports.startJournal(new Started(EVENT_SCHEMA,machine,Consumer.M7,request.runId(),java.time.Instant.now().toString(),
                ref("software-admission-not-read.json"),ref("software-request-not-read.json"),proof));
            assertEquals(identity,ports.directory().value());
            com.sun.jna.platform.win32.WinNT.HANDLE deleting=com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(
                SharedSourceFiles.nativePath(root),0x00010000,7,null,3,0x02200000,null);
            int error=com.sun.jna.Native.getLastError();
            boolean invalid=deleting==null||com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(deleting);
            if(!invalid)assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(deleting),"unexpected DELETE handle close");
            assertTrue(invalid,"retained output directory must deny a DELETE-access handle");
            assertEquals(32,error,"actual sharing violation required");
            assertThrows(IOException.class,()->java.nio.file.Files.move(root,renamed));
            assertTrue(java.nio.file.Files.isDirectory(root));assertFalse(java.nio.file.Files.exists(renamed));
            assertEquals(identity,SharedSourceFiles.nativeDirectory(root));
        }
        com.sun.jna.platform.win32.WinNT.HANDLE deleting=com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(
            SharedSourceFiles.nativePath(root),0x00010000,7,null,3,0x02200000,null);
        assertNotNull(deleting);assertNotEquals(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE,deleting,
            "after actual port close the same directory must admit DELETE access");
        assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(deleting));
        java.nio.file.Files.move(root,renamed);assertFalse(java.nio.file.Files.exists(root));
        assertEquals(identity,SharedSourceFiles.nativeDirectory(renamed));
        assertFalse(java.nio.file.Files.exists(unopened),"custody regression must not create or open an EXE input");
    }

    private Result run(Fixture fixture) throws IOException {
        return RawWindowCollector.execute(fixture.admission(), fixture.admissionRef(), fixture.request(), fixture.proof(), fixture.ports());
    }
    private Fixture fixture(Consumer consumer, Fault fault, int bodyLimit, boolean two) {
        String input = temporary.resolve("software-image.exe").toString(), output = temporary.resolve("output").toString();
        FileRef proofRef = ref("fullhash-original.json"), requestRef = ref("request.json"), admissionRef = ref("admission.json");
        List<Window> windows = two ? List.of(new Window("one", Kind.CODE, 12, 4), new Window("two", Kind.CODE, 12, 4))
                : List.of(new Window("one", Kind.CODE, 12, 4));
        Request request = new Request(REQUEST_SCHEMA, MACHINE, consumer, "software-fault-case", input, proofRef, output, DIRECTORY,
                windows, new Amounts(two ? 8 : 4, 0, 0), 8192, 65_536, bodyLimit, FUTURE);
        Admission admission = new Admission(ADMISSION_SCHEMA, MACHINE, consumer, "/root/budget_fast_lane", CaptureScope.BOUNDED_READ_ONLY_FILE_WINDOWS, requestRef, ref("grant.json"), FUTURE);
        var nativeIdentity = new RawWindowImageProof.LegacyIdentity(new java.math.BigInteger(FILE.legacyFileIdHex(), 16).toString(), FILE.fileIdDecimal(),
                FILE.volumeSerialDecimal(), FILE.logicalBytes(), FILE.creationFiletimeDecimal(), FILE.lastWriteFiletimeDecimal(), FILE.changeFiletimeDecimal(), 32, FILE.linkCount());
        var proof = new RawWindowImageProof.Proof(MACHINE, input, "a".repeat(64), nativeIdentity, proofRef);
        return new Fixture(request, admission, admissionRef, proof, new FakePorts(request, fault));
    }
    private FileRef ref(String name) { return new FileRef(temporary.resolve(name).toString(), 1, "a".repeat(64)); }
    private static ObjectNode tree(byte[] raw) throws IOException { return (ObjectNode) RawWindowCaptureJson.tree(raw); }
    private static void rejects(ObjectNode root) { assertThrows(Exception.class, () -> RawWindowCaptureJson.decode(root.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8), Request.class, 65_536)); }
    private static SharedSourceFiles.NativeFile drifted() {
        return new SharedSourceFiles.NativeFile(FILE.volumeSerialDecimal(), FILE.fileIdDecimal(), FILE.legacyVolumeSerialDecimal(), FILE.legacyFileIdHex(),
                FILE.creationFiletimeDecimal(), FILE.lastWriteFiletimeDecimal(), "4", FILE.logicalBytes(), FILE.allocatedBytes(), FILE.linkCount());
    }
    private static final class FakePorts implements RawWindowCollector.Ports {
        private final Request request; private final Fault fault;
        private final List<Event> events = new ArrayList<>(); private final List<String> order = new ArrayList<>();
        private final byte[] readBytes = {1, 2, 3, 4}; private byte[] rawBytes; private int reads, heldProbes;
        private boolean poisoned; private Body body;
        private FakePorts(Request request, Fault fault) { this.request = request; this.fault = fault; }
        @Override public String machineId() { return MACHINE; }
        @Override public void startJournal(Started start) throws IOException {
            if (fault == Fault.START_WRITE) throw new IOException("injected CREATE_NEW failure"); events.add(start); order.add("START_DURABLE");
        }
        @Override public void append(Event event) throws IOException {
            if (poisoned || (fault == Fault.INTENT_WRITE && event instanceof Intent) || (fault == Fault.RESULT_WRITE && event instanceof ReadObserved)
                    || (fault == Fault.RAW_RESULT_WRITE && event instanceof RawObserved)) {
                poisoned = true; throw new IOException("injected fallback write failure");
            }
            events.add(event);
            order.add(event instanceof Before ? "BEFORE_DURABLE" : event instanceof Intent ? "INTENT_DURABLE" : event instanceof ReadObserved ? "READ_DURABLE"
                    : event instanceof RawObserved ? "RAW_DURABLE" : event instanceof After ? "AFTER_DURABLE" : "FINISHED_DURABLE");
        }
        @Override public void openInput() { assertTrue(order.contains("START_DURABLE")); order.add("OPEN_INPUT"); }
        @Override public FileProbe held() throws IOException {
            heldProbes++; if (fault == Fault.POST_HELD && heldProbes == 2) throw new IOException("actual postidentity unavailable");
            return new FileProbe(ProbeStatus.OBSERVED, fault == Fault.IDENTITY_DRIFT && heldProbes == 2 ? drifted() : FILE, request.inputPath(), "");
        }
        @Override public FileProbe path() { return new FileProbe(ProbeStatus.OBSERVED, FILE, null, ""); }
        @Override public DirectoryProbe directory() { return new DirectoryProbe(ProbeStatus.OBSERVED, DIRECTORY, ""); }
        @Override public ReadResult read(ReadRange window) throws IOException {
            assertEquals("INTENT_DURABLE", order.getLast()); reads++; order.add("READ");
            if (fault == Fault.READ_THROW) throw new IOException("injected unknown native outcome");
            return new ReadResult(fault == Fault.SHORT_READ ? ReadStatus.SHORT_READ : ReadStatus.COMPLETE,
                    fault == Fault.SHORT_READ ? new byte[] {1, 2} : readBytes, 0, "");
        }
        @Override public RawArtifact preserveRaw(int index, byte[] raw) throws IOException {
            order.add("RAW"); if (fault == Fault.RAW_WRITE) throw new IOException("injected raw-file write failure");
            rawBytes = raw.clone(); return new RawArtifact(OutputStatus.CREATED_VERIFIED, String.format(java.util.Locale.ROOT, "window-%03d.raw", index),
                    (long) raw.length, RawWindowCaptureJson.hash(raw), "");
        }
        @Override public void publishBody(byte[] complete) throws IOException {
            assertTrue(order.contains("AFTER_DURABLE")); order.add("BODY");
            if (fault == Fault.BODY_WRITE) throw new IOException("injected complete body CREATE_NEW/write failure");
            body = RawWindowCaptureJson.decode(complete, Body.class, MAX_OUTPUT_BYTES);
        }
        @Override public long fileIdentityApiBufferChargeUpper() { return 512; }
        @Override public CloseStatus closeInput() {
            order.add("CLOSE_INPUT"); if (fault == Fault.CLOSE_THROW) throw new IllegalStateException("injected native close runtime failure"); return CloseStatus.CLOSED;
        }
        @Override public void close() { }
    }
}

