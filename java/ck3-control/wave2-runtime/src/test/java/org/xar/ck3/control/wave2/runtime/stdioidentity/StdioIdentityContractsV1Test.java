package org.xar.ck3.control.wave2.runtime.stdioidentity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.clockreader.Win32ClockProcessProbe;
import org.xar.ck3.control.wave2.runtime.stdioidentity.IdentityUnavailableException.Reason;
import org.xar.ck3.control.wave2.runtime.stdioidentity.LegacyProcessIdentityCodecV1.RoleIdentity;
import org.xar.ck3.control.wave2.runtime.stdioidentity.SourceBoundStdioIdentityVerifier.Snapshot;
import org.xar.ck3.control.wave2.runtime.stdioidentity.StdioIdentityPlanV1.SourcePinV1;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class StdioIdentityContractsV1Test {
    @TempDir Path temporary;
    private static final String MACHINE = "synthetic-no-native-proof";
    private static final Instant UTC = Instant.parse("2026-10-22T14:00:00Z");

    @TestFactory
    Stream<DynamicTest> actualLegacyProducerGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals("55e4409b2b0920085d432cd4a7ef9eef316a49762856db33e07d802128c274cc",
                golden.path("producer").path("sha256").textValue());
        assertEquals(40, golden.path("cases").size());
        return StreamSupport.stream(golden.path("cases").spliterator(), false).map(sample ->
                DynamicTest.dynamicTest(sample.path("id").textValue(), () -> {
                    // Preserve 1.0 as an actual float token; do not re-emit a normalized JSON tree.
                    byte[] raw = sample.path("raw_input_json").textValue().getBytes(StandardCharsets.UTF_8);
                    if (!sample.path("accepted").booleanValue()) {
                        assertThrows(ContractViolationException.class, () -> LegacyProcessIdentityCodecV1.decode(raw));
                    } else {
                        RoleIdentity identity = LegacyProcessIdentityCodecV1.decode(raw);
                        JsonNode original = sample.path("output");
                        assertEquals(original.path("role").textValue(), identity.role());
                        assertEquals(original.path("pid").longValue(), identity.identity().pid());
                        assertEquals(original.path("creation_filetime").bigIntegerValue().toString(),
                                identity.identity().creationFiletimeDecimal());
                        assertEquals(sample.path("normalized_executable").textValue(),
                                identity.identity().executable().toString().replace('/', '\\').toLowerCase(Locale.ROOT));
                        byte[] encoded = LegacyProcessIdentityCodecV1.encode(identity);
                        assertEquals(identity, LegacyProcessIdentityCodecV1.decode(encoded));
                        assertTrue(StrictJson.parse(encoded).get("creation_filetime").isIntegralNumber());
                    }
                    assertEquals(sample.path("injected_open_count").intValue(),
                            sample.path("injected_close_count").intValue(), "legacy injected resource closure");
                }));
    }

    @Test
    void legacyFieldContractRejectsCoercionsAndStructuralDrift() {
        String raw = legacyJson();
        for (String wrong : List.of("true", "1.0", "\"1\"", "null", "0", "18446744073709551616")) {
            assertThrows(ContractViolationException.class, () -> LegacyProcessIdentityCodecV1.decode(bytes(
                    raw.replace("134371502550367280", wrong))));
        }
        assertThrows(ContractViolationException.class, () -> LegacyProcessIdentityCodecV1.decode(bytes(
                raw.replace("\"pid\":17", "\"pid\":17.0"))));
        assertThrows(ContractViolationException.class, () -> LegacyProcessIdentityCodecV1.decode(bytes(
                raw.replace("\"pid\":17", "\"pid\":17,\"pid\":17"))));
        assertThrows(ContractViolationException.class, () -> LegacyProcessIdentityCodecV1.decode(bytes(
                raw.replace("\"role\":\"MCPApp\",", ""))));
        assertThrows(ContractViolationException.class, () -> LegacyProcessIdentityCodecV1.decode(bytes(
                raw.replace("\"role\":\"MCPApp\"", "\"role\":\"MCPApp\",\"alive\":true"))));
    }

    @Test
    void explicitNewPlanUsesDecimalStringsAndRoundTrips() {
        StdioIdentityPlanV1 plan = plan(new SourcePinV1(temporary.resolve("entry.py"), 0, "a".repeat(64)));
        byte[] raw = StdioIdentityCodecV1.encode(plan);
        assertEquals(plan, StdioIdentityCodecV1.decode(raw));
        assertArrayEquals(raw, StdioIdentityCodecV1.encode(StdioIdentityCodecV1.decode(raw)));
        String json = new String(raw, StandardCharsets.UTF_8);
        for (String replacement : List.of("true", "1.0", "134371502550367280", "null")) {
            assertThrows(ContractViolationException.class, () -> StdioIdentityCodecV1.decode(bytes(json.replace(
                    "\"creation_filetime_decimal\":\"134371502550367280\"",
                    "\"creation_filetime_decimal\":" + replacement))));
        }
        for (String replacement : List.of("true", "1.0", "\"17\"", "null", "4294967296")) {
            assertThrows(ContractViolationException.class, () -> StdioIdentityCodecV1.decode(bytes(json.replace(
                    "\"pid\":17", "\"pid\":" + replacement))));
        }
        assertThrows(ContractViolationException.class, () -> StdioIdentityCodecV1.decode(bytes(json.replace(
                StdioIdentityPlanV1.SCHEMA, "xar.owned-stdio-identity-plan/v2"))));
        assertThrows(ContractViolationException.class, () -> StdioIdentityCodecV1.decode(bytes(json.replace(
                "\"schema\":", "\"schema\":\"duplicate\",\"schema\":"))));
        for (String field : List.of("schema", "machine_id", "game", "queue", "app", "entry_sources")) {
            ObjectNode missing = (ObjectNode) StrictJson.parse(raw);
            missing.remove(field);
            assertThrows(ContractViolationException.class,
                    () -> StdioIdentityCodecV1.decode(StrictJson.canonical(missing)));
        }
        ObjectNode unknown = (ObjectNode) StrictJson.parse(raw);
        unknown.put("qualified", true);
        assertThrows(ContractViolationException.class,
                () -> StdioIdentityCodecV1.decode(StrictJson.canonical(unknown)));
        assertThrows(ContractViolationException.class, () -> StdioIdentityCodecV1.decode(bytes(json.replace(
                "\"bytes\":0", "\"bytes\":0.0"))));
        assertThrows(ContractViolationException.class, () -> StdioIdentityCodecV1.decode(bytes(json.replace(
                "\"bytes\":0", "\"bytes\":false"))));
        assertThrows(ContractViolationException.class,
                () -> StdioIdentityCodecV1.decode(new byte[StrictJson.INPUT_MAX_BYTES + 1]));
        assertThrows(ContractViolationException.class,
                () -> StdioIdentityCodecV1.decode(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test
    void sourceAndGenerationModelsAreBoundedAndImmutable() {
        SourcePinV1 pin = new SourcePinV1(temporary.resolve("entry.py"), 0, "a".repeat(64));
        List<SourcePinV1> mutable = new ArrayList<>(List.of(pin));
        StdioIdentityPlanV1 plan = new StdioIdentityPlanV1(MACHINE, claim(17), claim(21), claim(25), mutable);
        mutable.clear();
        assertEquals(List.of(pin), plan.entrySources());
        assertThrows(UnsupportedOperationException.class, () -> plan.entrySources().clear());
        assertThrows(ContractViolationException.class, () -> new StdioIdentityPlanV1(MACHINE,
                claim(17), claim(17), claim(25), List.of(pin)));
        assertThrows(ContractViolationException.class, () -> new StdioIdentityPlanV1(MACHINE,
                claim(17), claim(21), claim(25), List.of(pin, pin)));
        assertThrows(ContractViolationException.class, () -> new SourcePinV1(pin.path(), 1_048_577, pin.sha256()));
        assertThrows(ContractViolationException.class,
                () -> new ProcessIdentityClaimV1(17, "0134371502550367280", temporary.resolve("java.exe")));
        assertThrows(ContractViolationException.class,
                () -> new ProcessIdentityClaimV1(17, "18446744073709551616", temporary.resolve("java.exe")));
        ProcessIdentityClaimV1 maximum = new ProcessIdentityClaimV1(0xffff_ffffL,
                "18446744073709551615", temporary.resolve("java.exe"));
        assertEquals("18446744073709551615", maximum.creationFiletimeDecimal());
    }

    @Test
    void everyVerificationMeasuresAllThreeProcessesAndSourcesAgain() throws Exception {
        byte[] body = bytes("frozen original entry\n");
        Path source = temporary.resolve("entry.py"); Files.write(source, body);
        StdioIdentityPlanV1 plan = plan(new SourcePinV1(source, body.length, sha(body)));
        AtomicInteger observations = new AtomicInteger();
        SourceBoundStdioIdentityVerifier verifier = verifier(pid -> {
            observations.incrementAndGet(); return measured(claim(pid));
        });
        Snapshot before = verifier.requireCurrent(plan);
        assertEquals(3, observations.get());
        Snapshot after = verifier.requireUnchanged(before);
        assertEquals(6, observations.get());
        assertEquals(plan.game(), after.game().identity());
        assertThrows(UnsupportedOperationException.class, () -> after.sources().clear());
        assertNotNull(after.sources().getFirst().createdAtUtc());
        Files.write(source, bytes("changed original entry\n"));
        IdentityUnavailableException error = assertThrows(IdentityUnavailableException.class,
                () -> verifier.requireUnchanged(before));
        assertEquals(Reason.SOURCE_MISMATCH, error.reason());
        assertEquals(9, observations.get());
    }

    @Test
    void mismatchedBirthImageMachineOrUnavailableReadCannotUseCachedSuccess() throws Exception {
        Path source = temporary.resolve("empty.py"); Files.write(source, new byte[0]);
        StdioIdentityPlanV1 plan = plan(new SourcePinV1(source, 0, sha(new byte[0])));
        AtomicInteger calls = new AtomicInteger();
        SourceBoundStdioIdentityVerifier machineMismatch = new SourceBoundStdioIdentityVerifier(pid -> {
            calls.incrementAndGet(); return measured(claim(pid));
        }, () -> "different-machine");
        assertEquals(Reason.MACHINE_MISMATCH, assertThrows(IdentityUnavailableException.class,
                () -> machineMismatch.requireCurrent(plan)).reason());
        assertEquals(0, calls.get());
        SourceBoundStdioIdentityVerifier birthMismatch = verifier(pid -> measured(new ProcessIdentityClaimV1(
                pid, "134371502550367281", temporary.resolve("java.exe"))));
        assertEquals(Reason.GENERATION_MISMATCH, assertThrows(IdentityUnavailableException.class,
                () -> birthMismatch.requireCurrent(plan)).reason());
        SourceBoundStdioIdentityVerifier imageMismatch = verifier(pid -> measured(new ProcessIdentityClaimV1(
                pid, "134371502550367280", temporary.resolve("other.exe"))));
        assertEquals(Reason.GENERATION_MISMATCH, assertThrows(IdentityUnavailableException.class,
                () -> imageMismatch.requireCurrent(plan)).reason());
        IOException original = new IOException("original native read failed");
        assertSame(original, assertThrows(IOException.class, () -> verifier(pid -> { throw original; }).requireCurrent(plan)));
        SourceBoundStdioIdentityVerifier initiallyGood = verifier(pid -> measured(claim(pid)));
        Snapshot before = initiallyGood.requireCurrent(plan);
        Files.delete(source);
        assertEquals(Reason.SOURCE_UNAVAILABLE, assertThrows(IdentityUnavailableException.class,
                () -> initiallyGood.requireUnchanged(before)).reason());
    }

    @Test
    void nativeAdapterActuallyMeasuresCurrentWindowsProcess() throws Exception {
        // A missing Windows/JNA environment is a test failure, not a skipped native PASS.
        long current = ProcessHandle.current().pid();
        MeasuredProcessIdentity first = new Win32ProcessIdentityReader().observe(current);
        MeasuredProcessIdentity second = new Win32ProcessIdentityReader().observe(current);
        assertEquals(current, first.pid());
        assertTrue(first.identity().sameGeneration(second.identity()));
        assertTrue(new BigInteger(first.creationFiletimeDecimal()).compareTo(BigInteger.valueOf(9_007_199_254_740_991L)) > 0);
        assertTrue(new BigInteger(second.uptimeMillisDecimal()).compareTo(new BigInteger(first.uptimeMillisDecimal())) >= 0);
        assertTrue(Files.isSameFile(first.executable(), Path.of(ProcessHandle.current().info().command().orElseThrow())));
        // Exercise the actual production consumer, retaining the >53-bit birth as a decimal string.
        var consumed = new Win32ClockProcessProbe(new Win32ProcessIdentityReader()).observe(current);
        assertEquals(first.pid(), consumed.identity().pid());
        assertEquals(first.creationFiletimeDecimal(), consumed.identity().creationFiletime().decimal());
        assertTrue(Files.isSameFile(first.executable(), consumed.executable()));
        assertTrue(new BigInteger(consumed.win32UptimeMillis().decimal())
                .compareTo(new BigInteger(second.uptimeMillisDecimal())) >= 0);
        assertEquals(Reason.INVALID_PID, assertThrows(IdentityUnavailableException.class,
                () -> new Win32ProcessIdentityReader().observe(0)).reason());
    }

    private StdioIdentityPlanV1 plan(SourcePinV1 source) {
        return new StdioIdentityPlanV1(MACHINE, claim(17), claim(21), claim(25), List.of(source));
    }

    private ProcessIdentityClaimV1 claim(long pid) {
        return new ProcessIdentityClaimV1(pid, "134371502550367280", temporary.resolve("java.exe"));
    }

    private static MeasuredProcessIdentity measured(ProcessIdentityClaimV1 claim) {
        return new MeasuredProcessIdentity(claim, "12345678901234567", UTC);
    }

    private static SourceBoundStdioIdentityVerifier verifier(ProcessIdentityReader reader) {
        return new SourceBoundStdioIdentityVerifier(reader, () -> MACHINE);
    }

    private static String legacyJson() {
        return "{\"role\":\"MCPApp\",\"pid\":17,\"creation_filetime\":134371502550367280,"
                + "\"executable\":\"C:/Python/python.exe\"}";
    }

    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }

    private static String sha(byte[] raw) throws NoSuchAlgorithmException {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = StdioIdentityContractsV1Test.class.getResourceAsStream(
                "/stdioidentity/legacy-producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("actual legacy producer golden is required"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
}
