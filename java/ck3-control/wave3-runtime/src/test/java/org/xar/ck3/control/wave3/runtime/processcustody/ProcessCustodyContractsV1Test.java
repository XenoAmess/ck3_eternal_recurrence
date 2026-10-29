package org.xar.ck3.control.wave3.runtime.processcustody;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.TreeMap;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ErrorStage;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.KernelSignal;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ObservationError;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Actual producer/consumer differential vectors, plus ownership and strict ingress failures. */
final class ProcessCustodyContractsV1Test {
    private static final String BIRTH = "134371502550367280";
    @TempDir Path temporary;

    @TestFactory
    Stream<DynamicTest> actualRetainedGenerationProducer() throws IOException {
        JsonNode root = golden();
        assertEquals(26, root.path("cases").size());
        assertEquals(22, root.path("original_complete_fake_suite").path("tests_run").intValue());
        assertEquals("55e4409b2b0920085d432cd4a7ef9eef316a49762856db33e07d802128c274cc",
                root.path("sources").get(0).path("sha256").textValue());
        return stream(root.path("cases")).map(sample -> DynamicTest.dynamicTest(
                sample.path("id").textValue(), () -> {
                    FakeApi api = new FakeApi();
                    FakeHandle handle = api.handles.get(17L);
                    RetainedProcessGenerationV1 generation = RetainedProcessGenerationV1.capture(
                            ProcessExpectationV1.exact(handle.identity), api);
                    JsonNode config = sample.path("configuration");
                    handle.configure(config);
                    if (config.path("mutate_identity").asBoolean()) {
                        handle.identity = new ProcessIdentityClaimV1(17, "134371502550367380",
                                Path.of("C:/replacement/python.exe"));
                    }
                    boolean closeFailed = false;
                    if (config.path("closed").asBoolean()) {
                        try { generation.close(); } catch (IOException error) { closeFailed = true; }
                    }
                    ProcessObservationV1 actual = generation.observe();
                    ProcessObservationV1 archived = LegacyProcessObservationCodecV1.decode(
                            StrictJson.canonical(sample.path("observation")));
                    assertObservation(archived, actual);
                    assertEquals(archived, LegacyProcessObservationCodecV1.decode(
                            LegacyProcessObservationCodecV1.encode(archived)));
                    if (sample.path("require_live").booleanValue()) {
                        assertEquals(KernelSignal.UNSIGNALED, generation.requireLive().signal());
                    } else {
                        assertThrows(ProcessCustodyUnavailableException.class, generation::requireLive);
                    }
                    try { generation.close(); generation.close(); }
                    catch (IOException error) { closeFailed = true; }
                    assertEquals(!sample.path("close_error").isNull(), closeFailed);
                    assertEquals(1, api.attempts.size(), "observing must never reopen a PID");
                    assertEquals(1, handle.identities, "generation identity is measured once");
                    assertCalls(sample.path("calls"), handle);
                }));
    }

    @TestFactory
    Stream<DynamicTest> actualSdkPairConsumer() throws IOException {
        JsonNode root = golden();
        assertEquals(6, root.path("sdk_pair_consumers").size());
        return stream(root.path("sdk_pair_consumers")).map(sample -> DynamicTest.dynamicTest(
                sample.path("id").textValue(), () -> {
                    String id = sample.path("id").textValue();
                    byte[] raw = bytes(sample.path("published_pair_json").textValue());
                    PublishedSdkPairClaimV1 pair = PublishedSdkPairCodecV1.decode(raw);
                    assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)),
                            pair.originalSha256());
                    FakeApi api = new FakeApi();
                    if (id.equals("queue-exit-259")) { api.handles.get(17L).wait = 0; }
                    if (id.equals("application-exit-1")) {
                        api.handles.get(21L).wait = 0; api.handles.get(21L).exit = 1;
                    }
                    if (id.equals("wait-unavailable")) { api.handles.get(21L).failWait = true; }
                    if (id.equals("second-capture-failure")) { api.failPid = 21; }
                    SdkPairObserverV1 observer = new SdkPairObserverV1(pair, api);
                    int incidents = 0;
                    for (int index = 0; index < 3; index++) {
                        if (id.equals("late-application-exit") && index == 1) {
                            api.handles.get(21L).wait = 0; api.handles.get(21L).exit = 1;
                        }
                        JsonNode old = sample.path("snapshots").get(index);
                        SdkPairObserverV1.Report actual = observer.observe();
                        assertEquals(old.path("capture_error").booleanValue(), actual.captureFailure().isPresent());
                        if (actual.firstIncident()) { incidents++; }
                        assertEquals(old.path("incident_count").intValue(), incidents);
                        assertEquals(old.path("observations").size(), actual.observations().size());
                        for (int row = 0; row < actual.observations().size(); row++) {
                            assertEquals(pair.processes().get(row).role(), actual.observations().get(row).role());
                            assertObservation(LegacyProcessObservationCodecV1.decode(StrictJson.canonical(
                                    old.path("observations").get(row))), actual.observations().get(row).observation());
                        }
                        List<Long> expectedAttempts = stream(old.path("capture_attempts")).map(JsonNode::longValue).toList();
                        assertEquals(expectedAttempts, api.attempts);
                    }
                    observer.close(); observer.close();
                    assertCalls(sample.path("calls").path("17"), api.handles.get(17L));
                    assertCalls(sample.path("calls").path("21"), api.handles.get(21L));
                    assertEquals(SdkPairObserverV1.Phase.CLOSED, observer.observe().phase());
                    assertTrue(observer.observe().observations().isEmpty());
                }));
    }

    @Test
    void archiveRequiresExactFieldsAndNullableStates() {
        String raw = observationJson();
        ProcessObservationV1 parsed = LegacyProcessObservationCodecV1.decode(bytes(raw));
        assertEquals(parsed, LegacyProcessObservationCodecV1.decode(LegacyProcessObservationCodecV1.encode(parsed)));
        for (String field : List.of("pid", "creation_filetime", "executable", "kernel_exit_observed",
                "wait_result", "exit_code", "observation_error")) {
            ObjectNode missing = (ObjectNode) StrictJson.parse(bytes(raw));
            missing.remove(field);
            assertThrows(ContractViolationException.class,
                    () -> LegacyProcessObservationCodecV1.decode(StrictJson.canonical(missing)));
        }
        for (String wrong : List.of("true", "17.0", "\"17\"", "null", "0", "4294967296")) {
            assertThrows(ContractViolationException.class, () -> LegacyProcessObservationCodecV1.decode(
                    bytes(raw.replace("\"pid\":17", "\"pid\":" + wrong))));
        }
        for (String wrong : List.of("true", "134371502550367280.0", "\"" + BIRTH + "\"", "null",
                "0", "18446744073709551616")) {
            assertThrows(ContractViolationException.class, () -> LegacyProcessObservationCodecV1.decode(
                    bytes(raw.replace("\"creation_filetime\":" + BIRTH, "\"creation_filetime\":" + wrong))));
        }
        for (String wrong : List.of("true", "258.0", "\"258\"", "null", "0", "9223372036854775808")) {
            assertThrows(ContractViolationException.class, () -> LegacyProcessObservationCodecV1.decode(
                    bytes(raw.replace("\"wait_result\":258", "\"wait_result\":" + wrong))));
        }
        for (String wrong : List.of("true", "259.0", "\"259\"", "null", "-1", "4294967296")) {
            assertThrows(ContractViolationException.class, () -> LegacyProcessObservationCodecV1.decode(
                    bytes(raw.replace("\"exit_code\":259", "\"exit_code\":" + wrong))));
        }
        for (String wrong : List.of("0", "\"false\"", "null", "true")) {
            assertThrows(ContractViolationException.class, () -> LegacyProcessObservationCodecV1.decode(
                    bytes(raw.replace("\"kernel_exit_observed\":false", "\"kernel_exit_observed\":" + wrong))));
        }
        assertThrows(ContractViolationException.class, () -> LegacyProcessObservationCodecV1.decode(bytes(
                raw.replace("\"pid\":17", "\"pid\":17,\"pid\":17"))));
        assertThrows(ContractViolationException.class, () -> LegacyProcessObservationCodecV1.decode(bytes(
                raw.replace("\"pid\":17", "\"pid\":17,\"alive\":true"))));
        assertThrows(ContractViolationException.class,
                () -> LegacyProcessObservationCodecV1.decode(new byte[65_537]));
        assertThrows(ContractViolationException.class,
                () -> LegacyProcessObservationCodecV1.decode(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test
    void archivedUnknownAndPartialFailureRemainIndependent() {
        ProcessIdentityClaimV1 identity = claim(17);
        for (ErrorStage stage : ErrorStage.values()) {
            OptionalLong wait = stage == ErrorStage.EXIT_CODE ? OptionalLong.of(0) : OptionalLong.empty();
            KernelSignal signal = stage == ErrorStage.EXIT_CODE ? KernelSignal.SIGNALED : KernelSignal.UNKNOWN;
            ProcessObservationV1 value = new ProcessObservationV1(identity, wait, signal, OptionalLong.empty(),
                    Optional.of(new ObservationError(stage, "IOException", "")));
            assertEquals(value, LegacyProcessObservationCodecV1.decode(LegacyProcessObservationCodecV1.encode(value)));
        }
        assertThrows(ContractViolationException.class, () -> new ProcessObservationV1(identity,
                OptionalLong.of(0), KernelSignal.UNKNOWN, OptionalLong.empty(), Optional.of(
                        new ObservationError(ErrorStage.WAIT, "IOException", "unknown"))));
        assertThrows(ContractViolationException.class, () -> new ProcessObservationV1(identity,
                OptionalLong.of(258), KernelSignal.UNSIGNALED, OptionalLong.of(259), Optional.of(
                        new ObservationError(ErrorStage.EXIT_CODE, "IOException", "failed"))));
    }

    @Test
    void publishedPairProjectsOnlyKnownRowsAndRetainsOriginalBytesDigest() throws Exception {
        String raw = pairJson();
        PublishedSdkPairClaimV1 pair = PublishedSdkPairCodecV1.decode(bytes(raw));
        assertEquals(2, pair.processes().size());
        assertEquals(BIRTH, pair.processes().get(0).identity().creationFiletimeDecimal());
        PublishedSdkPairClaimV1 spaced = PublishedSdkPairCodecV1.decode(bytes(" " + raw));
        assertEquals(pair.processes(), spaced.processes());
        assertFalse(pair.originalSha256().equals(spaced.originalSha256()), "digest binds original bytes");
        for (String wrong : List.of("true", "17.0", "\"17\"", "null", "0", "4294967296")) {
            assertThrows(ContractViolationException.class, () -> PublishedSdkPairCodecV1.decode(bytes(
                    raw.replace("\"pid\":17", "\"pid\":" + wrong))));
        }
        for (String wrong : List.of("true", "134371502550367280.0", "\"" + BIRTH + "\"", "null", "0")) {
            assertThrows(ContractViolationException.class, () -> PublishedSdkPairCodecV1.decode(bytes(
                    raw.replace("\"creation_filetime\":" + BIRTH, "\"creation_filetime\":" + wrong))));
        }
        assertThrows(ContractViolationException.class, () -> PublishedSdkPairCodecV1.decode(bytes(
                raw.replace("SDK_PAIR_HANDLES_RETAINED", "PREPARED"))));
        assertThrows(ContractViolationException.class, () -> PublishedSdkPairCodecV1.decode(bytes(
                raw.replace("sdk_application", "sdk_queue"))));
        assertThrows(ContractViolationException.class, () -> PublishedSdkPairCodecV1.decode(bytes(
                raw.replace("sdk_application", "app"))));
        assertThrows(ContractViolationException.class, () -> PublishedSdkPairCodecV1.decode(bytes(
                raw.replace("\"pid\":17", "\"pid\":17,\"pid\":17"))));
        assertThrows(ContractViolationException.class, () -> PublishedSdkPairCodecV1.decode(bytes(
                raw.replace("\"role\":\"sdk_queue\",", ""))));
        assertThrows(UnsupportedOperationException.class, () -> pair.processes().clear());
    }

    @Test
    void captureFailureClosesOnlyAcquiredHandleAndPreservesPrimaryFailure() {
        FakeApi mismatch = new FakeApi();
        mismatch.handles.get(17L).identity = claim(21);
        assertThrows(IOException.class, () -> RetainedProcessGenerationV1.capture(
                ProcessExpectationV1.exact(claim(17)), mismatch));
        assertEquals(1, mismatch.handles.get(17L).closes);
        IOException primary = new IOException("original open failure");
        assertSame(primary, assertThrows(IOException.class, () -> RetainedProcessGenerationV1.capture(
                ProcessExpectationV1.measuredPid(17), pid -> { throw primary; })));
        FakeApi failedIdentity = new FakeApi();
        RuntimeException original = new IllegalStateException("original identity failure");
        FakeHandle acquired = failedIdentity.handles.get(17L);
        acquired.identityError = original; acquired.failClose = true;
        assertSame(original, assertThrows(IllegalStateException.class, () -> RetainedProcessGenerationV1.capture(
                ProcessExpectationV1.measuredPid(17), failedIdentity)));
        assertEquals(1, original.getSuppressed().length);
        assertEquals(1, acquired.closes);
    }

    @Test
    void kernelSignalControlsLivenessIndependentlyFromExitCode259() throws Exception {
        FakeApi api = new FakeApi();
        RetainedProcessGenerationV1 generation = RetainedProcessGenerationV1.capture(
                ProcessExpectationV1.measuredPid(17), api);
        FakeHandle handle = api.handles.get(17L);
        handle.exit = 0;
        assertEquals(KernelSignal.UNSIGNALED, generation.requireLive().signal());
        handle.wait = 0; handle.exit = 259;
        ProcessCustodyUnavailableException exited = assertThrows(ProcessCustodyUnavailableException.class,
                generation::requireLive);
        assertEquals(KernelSignal.SIGNALED, exited.observation().signal());
        assertEquals(OptionalLong.of(259), exited.observation().exitCode());
        handle.failExit = true;
        ProcessObservationV1 partial = generation.observe();
        assertEquals(KernelSignal.SIGNALED, partial.signal());
        assertEquals(ErrorStage.EXIT_CODE, partial.error().orElseThrow().stage());
        generation.close();
    }

    @Test
    void closeFailureIsAttemptedOnceAndCannotBecomeLiveAgain() throws Exception {
        FakeApi api = new FakeApi();
        FakeHandle handle = api.handles.get(17L);
        RetainedProcessGenerationV1 generation = RetainedProcessGenerationV1.capture(
                ProcessExpectationV1.measuredPid(17), api);
        handle.failClose = true;
        assertThrows(IOException.class, generation::close);
        generation.close();
        assertEquals(1, handle.closes);
        assertEquals(ErrorStage.CLOSED, generation.observe().error().orElseThrow().stage());
        assertThrows(ProcessCustodyUnavailableException.class, generation::requireLive);
        assertEquals(0, handle.waits);
        assertEquals(List.of(17L), api.attempts);
    }

    @Test
    void pairCloseAttemptsBothHandlesAndKeepsOriginalFailure() throws Exception {
        FakeApi api = new FakeApi();
        SdkPairObserverV1 observer = new SdkPairObserverV1(PublishedSdkPairCodecV1.decode(bytes(pairJson())), api);
        observer.observe();
        api.handles.get(17L).failClose = true; api.handles.get(21L).failClose = true;
        IOException failure = assertThrows(IOException.class, observer::close);
        assertEquals(1, failure.getSuppressed().length);
        observer.close();
        assertEquals(1, api.handles.get(17L).closes);
        assertEquals(1, api.handles.get(21L).closes);
        assertEquals(SdkPairObserverV1.Phase.CLOSED, observer.observe().phase());
        assertTrue(observer.observe().observations().isEmpty());
    }

    @Test
    void uncheckedCloseFailureStillReleasesEveryCapturedHandleAndIsNeverRetried() throws Exception {
        for (Throwable original : List.of(new IllegalStateException("first native close failed"),
                new AssertionError("first native close linkage failure"))) {
            FakeApi api = new FakeApi();
            SdkPairObserverV1 observer = new SdkPairObserverV1(PublishedSdkPairCodecV1.decode(bytes(pairJson())), api);
            observer.observe();
            IOException later = new IOException("second native close failed");
            api.handles.get(17L).closeError = original;
            api.handles.get(21L).closeError = later;
            assertSame(original, assertThrows(original.getClass(), observer::close));
            assertEquals(1, original.getSuppressed().length);
            assertSame(later, original.getSuppressed()[0]);
            observer.close();
            assertEquals(1, api.handles.get(17L).closes);
            assertEquals(1, api.handles.get(21L).closes);
            assertEquals(SdkPairObserverV1.Phase.CLOSED, observer.observe().phase());
            assertTrue(observer.observe().observations().isEmpty());
            assertEquals(List.of(17L, 21L), api.attempts);
        }
    }

    @Test
    void sharedNativeAdapterActuallyRetainsCurrentGenerationUntilClose() throws Exception {
        // Missing shared API/Windows/JNA is a failure, never a skipped native PASS.
        RetainedProcessGenerationV1 generation = RetainedProcessGenerationV1.system(
                ProcessExpectationV1.measuredPid(ProcessHandle.current().pid()));
        ProcessObservationV1 first = generation.requireLive();
        assertEquals(ProcessHandle.current().pid(), first.identity().pid());
        assertTrue(first.identity().executable().isAbsolute());
        assertTrue(first.identity().sameGeneration(generation.requireLive().identity()));
        generation.close(); generation.close();
        ProcessObservationV1 closed = generation.observe();
        assertEquals(KernelSignal.UNKNOWN, closed.signal());
        assertEquals(ErrorStage.CLOSED, closed.error().orElseThrow().stage());
        assertTrue(closed.waitResult().isEmpty());
        assertTrue(closed.exitCode().isEmpty());
    }

    @Test
    void systemConsumerKeepsActualExitedJobGenerationWithExit259AfterOriginalOwnerCloses() throws Exception {
        Path releaseGate = temporary.resolve("exit259.release");
        Path java = Path.of(System.getProperty("java.home"), "bin/java.exe");
        String classpath = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());
        String scratch = System.getProperty("java.io.tmpdir");
        environment.put("JAVA_TOOL_OPTIONS", "-Xms16m -Xmx64m -XX:MaxMetaspaceSize=64m"
                + " -XX:ReservedCodeCacheSize=32m -Djava.io.tmpdir=" + scratch + " -Djna.tmpdir=" + scratch);
        WindowsJobProcess.CommandSpec spec = new WindowsJobProcess.CommandSpec(java,
                List.of("-Xms16m", "-Xmx64m", "-cp", classpath, NativeChild.class.getName(), releaseGate.toString()),
                temporary.toAbsolutePath(), environment, temporary.resolve("child.stdout").toAbsolutePath(),
                temporary.resolve("child.stderr").toAbsolutePath(), 256L * 1024 * 1024);
        RetainedProcessGenerationV1 retained = null;
        ProcessIdentityClaimV1 original;
        try {
            try (WindowsJobProcess owner = WindowsJobProcess.start(spec)) {
                var actual = owner.identity();
                original = new ProcessIdentityClaimV1(actual.pid(), actual.creationFiletimeDecimal(),
                        Path.of(actual.executable()));
                retained = RetainedProcessGenerationV1.system(ProcessExpectationV1.exact(original));
                assertTrue(original.sameGeneration(retained.identity()));
                assertFalse(Files.exists(releaseGate));
                ProcessObservationV1 beforeRelease = retained.requireLive();
                assertEquals(KernelSignal.UNSIGNALED, beforeRelease.signal());
                assertEquals(OptionalLong.of(258), beforeRelease.waitResult());
                assertEquals(OptionalLong.of(259), beforeRelease.exitCode());
                Files.createFile(releaseGate);
                WindowsJobProcess.CommandResult terminal = owner.await(
                        Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
                assertEquals(259, terminal.exitCode());
                assertEquals(0, terminal.accounting().activeProcesses());
                assertTrue(terminal.accounting().peakJobMemoryBytes() <= terminal.accounting().memoryLimitBytes());
            }
            ProcessObservationV1 actual = retained.observe();
            assertTrue(original.sameGeneration(actual.identity()));
            assertEquals(KernelSignal.SIGNALED, actual.signal());
            assertEquals(OptionalLong.of(0), actual.waitResult());
            assertEquals(OptionalLong.of(259), actual.exitCode());
            assertTrue(actual.error().isEmpty());
            assertThrows(ProcessCustodyUnavailableException.class, retained::requireLive);
        } finally {
            if (retained != null) retained.close();
        }
    }

    public static final class NativeChild {
        private NativeChild() { }
        public static void main(String[] args) throws InterruptedException {
            if (args.length != 1) throw new IllegalArgumentException("One explicit release gate required");
            Path releaseGate = Path.of(args[0]);
            long deadline = System.nanoTime() + Duration.ofSeconds(20).toNanos();
            while (!Files.isRegularFile(releaseGate)) {
                if (System.nanoTime() - deadline >= 0) throw new IllegalStateException("Release gate never opened");
                Thread.sleep(10);
            }
            System.exit(259);
        }
    }

    private static final class FakeApi implements RetainedProcessApi {
        private final Map<Long, FakeHandle> handles = new LinkedHashMap<>();
        private final List<Long> attempts = new ArrayList<>();
        private long failPid = -1;
        private FakeApi() { handles.put(17L, new FakeHandle(claim(17))); handles.put(21L, new FakeHandle(claim(21))); }
        @Override public Handle open(long pid) throws IOException {
            attempts.add(pid);
            if (pid == failPid) { throw new IOException("injected second capture failure"); }
            FakeHandle handle = handles.get(pid);
            if (handle == null) { throw new IOException("unregistered synthetic process"); }
            handle.opens++;
            return handle;
        }
    }

    private static final class FakeHandle implements RetainedProcessApi.Handle {
        private ProcessIdentityClaimV1 identity;
        private long wait = 258;
        private long exit = 259;
        private boolean failWait, failExit, failClose, wrongWaitType, wrongExitType;
        private RuntimeException identityError;
        private Throwable closeError;
        private int opens, identities, waits, exits, closes;
        private FakeHandle(ProcessIdentityClaimV1 identity) { this.identity = identity; }
        private void configure(JsonNode config) {
            if (config.has("wait")) {
                wrongWaitType = !config.get("wait").isIntegralNumber();
                if (!wrongWaitType) { wait = config.get("wait").longValue(); }
            }
            if (config.has("exit")) {
                wrongExitType = !config.get("exit").isIntegralNumber();
                if (!wrongExitType) { exit = config.get("exit").longValue(); }
            }
            failWait = config.path("fail_wait").asBoolean();
            failExit = config.path("fail_exit").asBoolean();
            failClose = config.path("fail_close").asBoolean();
        }
        @Override public ProcessIdentityClaimV1 identity() {
            identities++;
            if (identityError != null) { throw identityError; }
            return identity;
        }
        @Override public long waitZero() throws IOException {
            waits++;
            if (failWait || wrongWaitType) { throw new IOException("injected invalid wait result"); }
            return wait;
        }
        @Override public long exitCode() throws IOException {
            exits++;
            if (failExit || wrongExitType) { throw new IOException("injected invalid exit result"); }
            return exit;
        }
        @Override public void close() throws IOException {
            closes++;
            if (closeError instanceof IOException error) { throw error; }
            if (closeError instanceof RuntimeException error) { throw error; }
            if (closeError instanceof Error error) { throw error; }
            if (failClose) { throw new IOException("injected close failure"); }
        }
    }

    private static void assertObservation(ProcessObservationV1 expected, ProcessObservationV1 actual) {
        assertTrue(expected.identity().sameGeneration(actual.identity()));
        assertEquals(expected.signal(), actual.signal());
        assertEquals(expected.waitResult(), actual.waitResult());
        assertEquals(expected.exitCode(), actual.exitCode());
        assertEquals(expected.error().map(ObservationError::stage), actual.error().map(ObservationError::stage));
        // Python OSError/ProcessCustodyError and Java IOException have different runtime names/messages.
    }

    private static void assertCalls(JsonNode expected, FakeHandle actual) {
        assertEquals(expected.path("open").intValue(), actual.opens);
        assertEquals(expected.path("wait").intValue(), actual.waits);
        assertEquals(expected.path("exit").intValue(), actual.exits);
        assertEquals(expected.path("close").intValue(), actual.closes);
    }

    private static ProcessIdentityClaimV1 claim(long pid) {
        return new ProcessIdentityClaimV1(pid, Long.toString(Long.parseLong(BIRTH) + pid - 17),
                Path.of("C:/Python/python.exe"));
    }

    private static String observationJson() {
        return "{\"pid\":17,\"creation_filetime\":" + BIRTH + ",\"executable\":\"C:/Python/python.exe\","
                + "\"kernel_exit_observed\":false,\"wait_result\":258,\"exit_code\":259,\"observation_error\":null}";
    }

    private static String pairJson() {
        return "{\"status\":\"SDK_PAIR_HANDLES_RETAINED\",\"extension\":true,\"processes\":["
                + "{\"role\":\"sdk_queue\",\"pid\":17,\"creation_filetime\":" + BIRTH
                + ",\"executable\":\"C:/Python/python.exe\",\"extra\":{}},"
                + "{\"role\":\"sdk_application\",\"pid\":21,\"creation_filetime\":134371502550367284,"
                + "\"executable\":\"C:/Python/python.exe\"}]}";
    }

    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static Stream<JsonNode> stream(JsonNode node) { return StreamSupport.stream(node.spliterator(), false); }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = ProcessCustodyContractsV1Test.class.getResourceAsStream(
                "/processcustody/original-producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("actual producer and consumer golden is required"); }
            return StrictJson.parse(stream.readAllBytes(), 98_304);
        }
    }
}
