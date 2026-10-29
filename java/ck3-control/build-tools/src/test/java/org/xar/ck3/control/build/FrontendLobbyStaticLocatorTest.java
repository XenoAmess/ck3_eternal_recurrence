package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.FrontendLobbyStaticLocator.*;
import org.xar.ck3.control.build.RawWindowCaptureContract.ReadRange;
import org.xar.ck3.control.build.RawWindowCaptureContract.ReadResult;
import org.xar.ck3.control.build.RawWindowCaptureContract.ReadStatus;
import org.xar.ck3.control.build.RawWindowCaptureContract.CloseStatus;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Fixed software-only qualification; real shared native backend, never the CK3 image. */
public final class FrontendLobbyStaticLocatorTest {
    @TempDir Path temporary;
    private static final Section RDATA = new Section(".rdata", 8192, 2048, 1024);
    private static final Section CODE = new Section(".text", 4096, 4096, 1024);
    private static Budget budget() { return new Budget(131072, 8192, 0, 32768, 64, 65536, 32768); }
    private Path directory(String name) throws IOException { return Files.createDirectory(temporary.resolve(name)); }

    @Test void crossChunkNamesAndRipReferencesAreCountedExactlyOnce() {
        byte[] names = names(); Scanner scanner = new Scanner(RDATA, CODE, IMAGE_BASE);
        chunks(names, false, scanner, 64);
        byte[] code = new byte[1024];
        int[] starts = {62, 126, 190};
        for (int i = 0; i < 3; i++) rip(code, starts[i], scanner.names.get(i).get(0).rva(), 0x8d);
        chunks(code, true, scanner, 64);
        assertEquals(Status.COMPLETE_UNVALIDATED, scanner.status());
        for (NameResult value : scanner.results(false)) { assertEquals(1, value.anchorCount()); assertEquals(1, value.xrefCount()); }
    }
    @Test void negativeRipAndAbsoluteCandidatesPreserveActualBytes() {
        Section highCode = new Section(".text", 32768, 4096, 1024);
        Scanner scanner = new Scanner(RDATA, highCode, IMAGE_BASE); scanner.anchors(names(), 0, 0);
        long anchor = scanner.names.get(0).get(0).rva(); byte[] code = new byte[1024];
        code[62] = 0x48; code[63] = (byte) 0x8b; code[64] = 5; i32(code, 65, (int) (anchor - highCode.rva() - 62 - 7));
        code[126] = 0x49; code[127] = (byte) 0xb8; i64(code, 128, IMAGE_BASE + anchor);
        chunks(code, true, scanner, 64);
        var refs = scanner.results(false).get(0).candidates(); assertEquals(2, refs.size());
        assertEquals(Encoding.RIP_LOAD, refs.get(0).encoding()); assertEquals(Encoding.MOVABS_IMMEDIATE, refs.get(1).encoding());
        assertEquals("49b8", refs.get(1).bytesHex().substring(0, 4));
        assertEquals(anchor, refs.get(1).anchorRva());
    }
    @Test void exactTrailingNulAndMissingNameCannotBecomeComplete() {
        byte[] raw = names(); raw[61] = 'X'; Scanner scanner = new Scanner(RDATA, CODE, IMAGE_BASE);
        chunks(raw, false, scanner, 64);
        assertEquals(1, scanner.anchorCounts[0]);
        raw[62 + Name.GetSelectedPlayable.name().length()] = 88;
        Scanner missing = new Scanner(RDATA, CODE, IMAGE_BASE); chunks(raw, false, missing, 64);
        assertEquals(0, missing.anchorCounts[0]); assertEquals(Status.MISSING_ANCHOR, missing.status());
        Scanner empty = new Scanner(RDATA, CODE, IMAGE_BASE); chunks(new byte[1024], false, empty, 64);
        assertEquals(Status.MISSING_ANCHOR, empty.status());
    }
    @Test void anchorAndXrefOverflowKeepActualCountsAndRejectCompleteness() {
        byte[] raw = new byte[1024]; byte[] name = (Name.GetSelectedPlayable.name() + "\0").getBytes(StandardCharsets.US_ASCII);
        for (int i = 0; i < 9; i++) System.arraycopy(name, 0, raw, 1 + i * 48, name.length);
        Scanner scanner = new Scanner(RDATA, CODE, IMAGE_BASE); chunks(raw, false, scanner, 64);
        assertEquals(9, scanner.anchorCounts[0]); assertEquals(8, scanner.names.get(0).size());
        assertEquals(Status.AMBIGUOUS_OVER_LIMIT, scanner.status());
        Scanner many = new Scanner(RDATA, CODE, IMAGE_BASE); many.anchors(names(), 0, 0); byte[] code = new byte[1024];
        for (int i = 0; i < 65; i++) rip(code, i * 10, many.names.get(0).get(0).rva(), 0x8d);
        chunks(code, true, many, 64); assertEquals(65, many.xrefCounts[0]); assertEquals(64, many.refs.get(0).size());
        assertEquals(Status.AMBIGUOUS_OVER_LIMIT, many.status());
    }
    @Test void actualSharedReadonlyBackendScansFixtureAndPublishesBoundedOriginal() throws Exception {
        byte[] bytes = fixture(); Path file = temporary.resolve("actual-small-pe.bin"); Files.write(file, bytes); Path output = directory("actual-scan");
        Body body = softwareFixture(file, output, RDATA, CODE, IMAGE_BASE, budget());
        assertEquals(Origin.SOFTWARE_FIXTURE, body.origin()); assertEquals(Status.COMPLETE_UNVALIDATED, body.status());
        assertEquals("UNVALIDATED_CANDIDATES_ONLY", body.qualification()); assertNull(body.reusedFullHash());
        assertEquals("CLOSED", body.inputClose()); assertEquals(body.beforeIdentity(), body.afterIdentity());
        assertEquals(2240, body.counts().metadataReported()); assertEquals(1024, body.counts().codeReported());
        assertFalse(body.counts().physicalIoMeasured()); assertEquals(36, body.counts().readCalls());
        assertEquals(RawWindowCaptureJson.hash(Arrays.copyOfRange(bytes, 2048, 3072)), body.sections().get(0).sha256());
        assertEquals(RawWindowCaptureJson.hash(Arrays.copyOfRange(bytes, 4096, 5120)), body.sections().get(1).sha256());
        byte[] published = Files.readAllBytes(output.resolve("capture.json")); assertArrayEquals(encode(body), published); assertTrue(published.length <= 32768);
        Body decoded = RawWindowCaptureJson.decode(published, Body.class, 32768); assertEquals(body, decoded);
        assertThrows(IOException.class, () -> softwareFixture(file, output, RDATA, CODE, IMAGE_BASE, budget()));
        try (var files = Files.list(output)) { assertEquals(List.of("capture.json", "fallback.jsonl"), files.map(p -> p.getFileName().toString()).sorted().toList()); }
        List<String> journal = Files.readAllLines(output.resolve("fallback.jsonl")); long intents = 0, observations = 0;
        for (String line : journal) { var event = RawWindowCaptureJson.tree(line.getBytes(StandardCharsets.UTF_8));
            if ("READ_INTENT".equals(event.get("phase").textValue())) intents++;
            if ("READ_OBSERVED".equals(event.get("phase").textValue())) observations++;
        }
        assertEquals(36, intents); assertEquals(intents, observations);
        Section largeCode = new Section(".text", CODE.rva(), CODE.offset(), 4096);
        byte[] worst = Arrays.copyOf(bytes, 8192); header(worst, 344 + 264, largeCode);
        byte[] instructions = new byte[4096]; int[] anchors = {62, 190, 318};
        for (int group = 0; group < 3; group++) for (int i = 0; i < 64; i++)
            rip(instructions, (group * 64 + i) * 10, RDATA.rva() + anchors[group], 0x8d);
        System.arraycopy(instructions, 0, worst, 4096, instructions.length);
        Path worstFile = temporary.resolve("maximum-candidates.bin"); Files.write(worstFile, worst);
        Budget largerJournal = new Budget(131072, 8192, 0, 32768, 64, 131072, 32768);
        Body maximum = softwareFixture(worstFile, directory("maximum-candidates"), RDATA, largeCode, IMAGE_BASE, largerJournal);
        assertEquals(Status.COMPLETE_UNVALIDATED, maximum.status()); assertTrue(encode(maximum).length <= 32768);
        for (NameResult name : maximum.names()) { assertEquals(64, name.xrefCount()); assertEquals(64, name.candidates().size()); }
        Body bounded = softwareFixture(worstFile, directory("bounded-body"), RDATA, largeCode, IMAGE_BASE,
                new Budget(131072, 8192, 0, 32768, 64, 131072, 4096));
        assertEquals(Status.BODY_LIMIT, bounded.status()); assertTrue(bounded.candidatesOmittedForBodyLimit());
        for (NameResult name : bounded.names()) { assertEquals(64, name.xrefCount()); assertTrue(name.candidates().isEmpty()); }
    }
    @Test void wrongFreshPeIsPublishedAsFailedWithoutScanningSections() throws Exception {
        byte[] bytes = fixture(); bytes[344 + 4] = 0; Path file = temporary.resolve("wrong-pe.bin"); Files.write(file, bytes);
        Body body = softwareFixture(file, directory("wrong-pe"), RDATA, CODE, IMAGE_BASE, budget());
        assertEquals(Status.FAILED, body.status()); assertEquals(2, body.counts().readCalls()); assertTrue(body.sections().isEmpty());
        assertTrue(body.failure().contains("PE32+"));
    }
    @Test void sourceRequestTypesAndFullScanBudgetAreRejectedBeforeRead() throws Exception {
        var ref = new ControlBuild.FileRef(temporary.resolve("source17.json").toString(), 6746, "0".repeat(64));
        var identity = SharedSourceFiles.nativeDirectory(temporary);
        assertThrows(IllegalArgumentException.class, () -> new Request(SCHEMA, WindowsJobProcess.currentMachineId(), "one", INPUT,
                ref, temporary.toString(), identity, budget(), Instant.now().plusSeconds(60).toString()));
        assertThrows(IllegalArgumentException.class, () -> new Budget(131072, 8192, 1, 32768, 64, 65536, 32768));
        com.fasterxml.jackson.databind.node.ObjectNode wrongType = ControlBuild.strictMapper().valueToTree(budget()); wrongType.put("metadata_maximum", true);
        assertThrows(IOException.class, () -> RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(wrongType), Budget.class, 65536));
        Path file = temporary.resolve("budget-fixture.bin"); Files.write(file, fixture()); Path output = directory("budget-fail");
        assertThrows(IOException.class, () -> softwareFixture(file, output, RDATA, CODE, IMAGE_BASE,
                new Budget(1216, 8192, 0, 32768, 64, 65536, 32768)));
        try (var children = Files.list(output)) { assertEquals(0, children.count()); }
    }
    @Test void actualSharedBackendReportsShortReadAndNeverPadsOrRetries() throws Exception {
        Path input = temporary.resolve("short-native.bin"); Files.write(input, new byte[] {1, 2, 3, 4}); Path output = directory("short-native");
        try (RawWindowNativeIo io = RawWindowNativeIo.namedFrontend(new RawWindowNativeIo.NamedInput(input.toString(), output.toString(),
                SharedSourceFiles.nativeDirectory(output), 32768, 65536, 32768))) {
            io.startMetadataJournal("{\"software\":true}".getBytes(StandardCharsets.UTF_8)); io.openInput();
            ReadResult result = io.read(new ReadRange(2, 8)); assertEquals(ReadStatus.SHORT_READ, result.status());
            assertArrayEquals(new byte[] {3, 4}, result.returnedBytes()); assertEquals(CloseStatus.CLOSED, io.closeInput());
        }
    }
    @Test void actualSharedBackendPoisonedJournalPreventsFurtherRead() throws Exception {
        Path input = temporary.resolve("poison-native.bin"); Files.write(input, new byte[64]); Path output = directory("poison-native");
        try (RawWindowNativeIo io = RawWindowNativeIo.namedFrontend(new RawWindowNativeIo.NamedInput(input.toString(), output.toString(),
                SharedSourceFiles.nativeDirectory(output), 32768, 65536, 32768))) {
            io.startMetadataJournal("{\"software\":true}".getBytes(StandardCharsets.UTF_8)); io.openInput();
            assertThrows(IOException.class, () -> io.appendMetadata("{\"bad\":true}\n".getBytes(StandardCharsets.UTF_8)));
            assertThrows(IOException.class, () -> io.read(new ReadRange(0, 8))); assertEquals(CloseStatus.CLOSED, io.closeInput());
        }
    }
    @Test void wrongPeGeometryAndSourceCoercionAreStrict() throws Exception {
        byte[] all = fixture(); byte[] dos = Arrays.copyOf(all, 64), pe = Arrays.copyOfRange(all, 344, 888);
        assertDoesNotThrow(() -> requirePe(dos, pe, RDATA, CODE, IMAGE_BASE, all.length, Origin.SOFTWARE_FIXTURE));
        i32(pe, 304 + 20, 999999); assertThrows(IOException.class, () -> requirePe(dos, pe, RDATA, CODE, IMAGE_BASE, all.length, Origin.SOFTWARE_FIXTURE));
        com.fasterxml.jackson.databind.node.ObjectNode wrongType = ControlBuild.strictMapper().valueToTree(budget()); wrongType.put("metadata_maximum", 1.0);
        assertThrows(IOException.class, () -> RawWindowCaptureJson.decode(ControlBuild.strictMapper().writeValueAsBytes(wrongType), Budget.class, 65536));
        assertThrows(IOException.class, () -> RawWindowCaptureJson.decode("{\"schema\":\"x\",\"schema\":\"y\"}".getBytes(StandardCharsets.UTF_8), Request.class, 65536));
    }
    /** Exact fixed selection; no discover/skip path, no invocation of the real image CLI. Caller supplies the new software envelope root. */
    public static void main(String[] args) throws Exception {
        if (args.length != 1 || !Path.of(args[0]).isAbsolute()) throw new IllegalArgumentException("new software qualification output root required");
        Path root = Path.of(args[0]); Files.createDirectory(root);
        List<String> passed = new ArrayList<>();
        String[] names = {"crossChunkNamesAndRipReferencesAreCountedExactlyOnce", "negativeRipAndAbsoluteCandidatesPreserveActualBytes",
                "exactTrailingNulAndMissingNameCannotBecomeComplete", "anchorAndXrefOverflowKeepActualCountsAndRejectCompleteness",
                "actualSharedReadonlyBackendScansFixtureAndPublishesBoundedOriginal", "wrongFreshPeIsPublishedAsFailedWithoutScanningSections",
                "sourceRequestTypesAndFullScanBudgetAreRejectedBeforeRead", "actualSharedBackendReportsShortReadAndNeverPadsOrRetries",
                "actualSharedBackendPoisonedJournalPreventsFurtherRead", "wrongPeGeometryAndSourceCoercionAreStrict"};
        for (String name : names) {
            FrontendLobbyStaticLocatorTest test = new FrontendLobbyStaticLocatorTest(); test.temporary = Files.createDirectory(root.resolve(name));
            try { FrontendLobbyStaticLocatorTest.class.getDeclaredMethod(name).invoke(test); passed.add(name); }
            catch (java.lang.reflect.InvocationTargetException failure) { throw new AssertionError("fixed software method failed: " + name, failure.getCause()); }
        }
        var receipt = ControlBuild.strictMapper().createObjectNode(); receipt.put("schema", "xar.frontend-lobby-locator-software/v1");
        receipt.put("machine_id", WindowsJobProcess.currentMachineId()); receipt.put("observed_at_utc", Instant.now().toString()); receipt.put("status", "PASS");
        receipt.put("found", names.length); receipt.put("started", names.length); receipt.put("succeeded", passed.size()); receipt.put("skipped", 0); receipt.put("failed", 0);
        receipt.put("real_image_read", false); receipt.set("methods", ControlBuild.strictMapper().valueToTree(passed));
        receipt.put("producer_class_sha256", classHash(FrontendLobbyStaticLocator.class)); receipt.put("test_class_sha256", classHash(FrontendLobbyStaticLocatorTest.class));
        System.out.println(ControlBuild.strictMapper().writeValueAsString(receipt));
    }
    private static String classHash(Class<?> type) throws IOException {
        try (var input = type.getResourceAsStream(type.getSimpleName() + ".class")) {
            if (input == null) throw new IOException("actual compiled software class absent"); return RawWindowCaptureJson.hash(input.readAllBytes());
        }
    }
    private static byte[] names() {
        byte[] names = new byte[1024]; int[] starts = {62, 190, 318};
        for (Name name : Name.values()) { byte[] needle = (name.name() + "\0").getBytes(StandardCharsets.US_ASCII);
            System.arraycopy(needle, 0, names, starts[name.ordinal()], needle.length); }
        return names;
    }
    private static void chunks(byte[] source, boolean code, Scanner scanner, int chunk) {
        byte[] carry = new byte[0];
        for (int start = 0; start < source.length; start += chunk) {
            int length = Math.min(chunk, source.length - start); byte[] both = new byte[carry.length + length];
            System.arraycopy(carry, 0, both, 0, carry.length); System.arraycopy(source, start, both, carry.length, length);
            if (code) scanner.references(both, start - carry.length, start); else scanner.anchors(both, start - carry.length, start);
            carry = Arrays.copyOfRange(both, Math.max(0, both.length - 64), both.length);
        }
    }
    private static byte[] fixture() {
        byte[] raw = new byte[5120]; raw[0] = 0x4d; raw[1] = 0x5a; i32(raw, 60, 344);
        int pe = 344; i32(raw, pe, 0x4550); i16(raw, pe + 4, 0x8664); i16(raw, pe + 6, 7);
        i16(raw, pe + 20, 240); i16(raw, pe + 24, 0x20b); i64(raw, pe + 48, IMAGE_BASE);
        header(raw, pe + 264, CODE); header(raw, pe + 304, RDATA); System.arraycopy(names(), 0, raw, 2048, 1024);
        byte[] code = new byte[1024]; int[] offsets = {62, 190, 318};
        for (Name name : Name.values()) rip(code, 62 + name.ordinal() * 128, RDATA.rva() + offsets[name.ordinal()], 0x8d);
        System.arraycopy(code, 0, raw, 4096, 1024); return raw;
    }
    private static void header(byte[] raw, int at, Section value) {
        byte[] name = value.name().getBytes(StandardCharsets.US_ASCII); System.arraycopy(name, 0, raw, at, name.length);
        i32(raw, at + 8, value.bytes()); i32(raw, at + 12, (int) value.rva()); i32(raw, at + 16, value.bytes()); i32(raw, at + 20, (int) value.offset());
    }
    private static void rip(byte[] bytes, int at, long target, int opcode) { bytes[at] = 0x48; bytes[at + 1] = (byte) opcode; bytes[at + 2] = 5; i32(bytes, at + 3, (int) (target - CODE.rva() - at - 7)); }
    private static void i16(byte[] b, int at, int n) { b[at] = (byte) n; b[at + 1] = (byte) (n >>> 8); }
    private static void i32(byte[] b, int at, int n) { for (int i = 0; i < 4; i++) b[at + i] = (byte) (n >>> (8 * i)); }
    private static void i64(byte[] b, int at, long n) { for (int i = 0; i < 8; i++) b[at + i] = (byte) (n >>> (8 * i)); }
}
