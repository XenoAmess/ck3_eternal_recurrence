package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialAdmissionVerifier;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialEpochProducer;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialRpcEvidence;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialSources;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.recovery.RecoveryPrerequisiteVerifier;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Actual original writer and original cold consumer; only the SDK authority seam is explicitly synthetic. */
class ClosedAdoptionTransactionTest {
    static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static Path repo() {
        String explicit = System.getProperty("xar.repo");
        if (explicit == null || explicit.isBlank()) { explicit = System.getenv("XAR_REPO_ROOT"); }
        Path current = Path.of(explicit == null || explicit.isBlank() ? System.getProperty("user.dir") : explicit).toAbsolutePath();
        for (int count = 0; count < 6 && current != null; count++, current = current.getParent()) {
            if (Files.isRegularFile(current.resolve("java/ck3-control/admission-contracts/src/test/resources/closedpartial/original-sources.json"))) { return current; }
        }
        throw new IllegalStateException("UNAVAILABLE: original source fixture checkout is required; set xar.repo or XAR_REPO_ROOT");
    }
    private static byte[] resource(String name) throws IOException {
        try (InputStream input = ClosedAdoptionTransactionTest.class.getResourceAsStream("/closedadoption/" + name)) {
            assertNotNull(input, "required original golden: " + name); byte[] raw = input.readNBytes(65_537);
            assertTrue(raw.length <= 65_536); return raw;
        }
    }
    private static RecoveryEvidence evidence(String path, byte[] raw) {
        return new RecoveryEvidence(new ExactRef(path, raw.length, RecoveryEvidence.sha256(raw)), raw);
    }
    private static RecoveryEvidence direct(JsonNode row) throws IOException {
        ExactRef ref = ExactRef.fromJson(row.get("ref")); byte[] raw;
        if (row.has("resource")) { raw = resource(row.get("resource").textValue()); }
        else { raw = bounded(Path.of(ref.path()), RecoveryEvidence.MAX_BYTES); }
        return new RecoveryEvidence(ref, raw);
    }
    private static byte[] bounded(Path path, int maximum) throws IOException {
        assertTrue(Files.isRegularFile(path), "UNAVAILABLE: actual original environment source missing: " + path);
        try (InputStream input = Files.newInputStream(path)) {
            byte[] raw = input.readNBytes(maximum + 1); assertTrue(raw.length <= maximum, "bounded complete original fixture"); return raw;
        }
    }
    private static RecoveryEvidence prior(JsonNode row) throws IOException {
        Path source = repo().resolve("java/ck3-control/admission-contracts/src/test/resources/closedpartial").resolve(row.get("resource").textValue());
        return new RecoveryEvidence(ExactRef.fromJson(row.get("ref")), bounded(source, RecoveryEvidence.MAX_BYTES));
    }
    private static ClosedPartialRpcEvidence rpc(JsonNode row) throws IOException {
        ExactRef ref = ExactRef.fromJson(row.get("ref")); return new ClosedPartialRpcEvidence(ref, bounded(Path.of(ref.path()), ClosedPartialRpcEvidence.MAX_BYTES));
    }
    static final class SourceCache implements ClosedAdoptionSources.SourceVerifier {
        private final Map<ExactRef, FileStatIdentity> checked = new HashMap<>();
        private final WindowsSavedProofIdentityReader nativeMetadata = new WindowsSavedProofIdentityReader();
        @Override public void verify(ExactRef source) {
            try {
                Path path = Path.of(source.path()); FileStatIdentity current = nativeMetadata.stat(path);
                if (!checked.containsKey(source)) {
                    assertTrue(source.bytes() <= ClosedPartialRpcEvidence.MAX_BYTES, "test source guard excludes Driver/SAVE bodies");
                    byte[] raw = bounded(path, ClosedPartialRpcEvidence.MAX_BYTES);
                    assertEquals(source.bytes(), raw.length); assertEquals(source.sha256(), RecoveryEvidence.sha256(raw)); checked.put(source, current);
                }
                assertEquals(checked.get(source), current, "current source identity changed");
            } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        }
    }
    record Fixture(Path root, ClosedAdoptionMaterial material, RecoveryEvidence canonical,
            OriginalWriterTransaction.Target target, SourceCache sourceCache) { }
    static Fixture fixture() throws IOException {
        assertEquals(MACHINE, WindowsJobProcess.currentMachineId(), "actual source-machine fixture scope");
        Path scratch = Path.of(System.getProperty("xar.scratch", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch")).toAbsolutePath();
        Files.createDirectories(scratch); Path root = Files.createTempDirectory(scratch, "closedadoption-");
        ObjectNode manifest = (ObjectNode) StrictJson.parse(resource("original-business-sources.json"));
        ExactRef priorManifest = ExactRef.fromJson(manifest.get("prior_fixture_manifest").get("ref"));
        byte[] priorRaw = bounded(Path.of(priorManifest.path()), RecoveryEvidence.MAX_BYTES);
        assertEquals(priorManifest.sha256(), RecoveryEvidence.sha256(priorRaw));
        JsonNode old = StrictJson.parse(priorRaw), inputRows = old.get("inputs"), sources = old.get("sources");
        RecoveryEvidence basis = prior(inputRows.get("basis")); ObjectNode basisValue = (ObjectNode) StrictJson.parse(basis.bytes());
        byte[] snapshotRaw = prior(inputRows.get("head")).bytes(); Path snapshot = root.resolve("immutable-head240.json"); Files.write(snapshot, snapshotRaw);
        Path driver = root.resolve("fixture-driver.json"); byte[] driverRaw = "{}".getBytes(StandardCharsets.UTF_8); Files.write(driver, driverRaw);
        var identities = new WindowsSavedProofIdentityReader();
        ExactRef driverRef = new ExactRef(driver.toString(), driverRaw.length, RecoveryEvidence.sha256(driverRaw));
        ClosedFailureRecoveryInput input = new ClosedFailureRecoveryInput(MACHINE, "2026-10-22T14:30:00Z", evidence(snapshot.toString(), snapshotRaw), basis,
                prior(inputRows.get("qualification")), prior(inputRows.get("fullRequest")), prior(inputRows.get("failedFull")),
                prior(inputRows.get("autoRequest")), prior(inputRows.get("failedAuto")), prior(inputRows.get("state")), prior(inputRows.get("governance")),
                prior(inputRows.get("next")), driverRef, identities.stat(driver), ExactRef.fromJson(basisValue.get("refs").get("save")),
                FileStatIdentity.fromJson(basisValue.get("save_identity"), FileStatIdentity.SCHEMA));
        List<ClosedPartialSources.Task> tasks = new ArrayList<>();
        for (JsonNode row : old.get("tasks")) { tasks.add(new ClosedPartialSources.Task(ClosedPartialSources.TaskRole.valueOf(row.get("role").textValue()),
                prior(row.get("spec")), prior(row.get("closed")), prior(row.get("unregistered")))); }
        List<ClosedPartialSources.Cycle> cycles = new ArrayList<>();
        for (JsonNode row : old.get("cycles")) { cycles.add(new ClosedPartialSources.Cycle(rpc(row.get("auto")), rpc(row.get("metrics")))); }
        ClosedPartialSources closed = new ClosedPartialSources(prior(sources.get("sdk")), prior(sources.get("game")), prior(sources.get("supervisor")),
                prior(sources.get("recording")), prior(sources.get("capture")), prior(sources.get("screen")), tasks, cycles);
        JsonNode businessRows = manifest.get("sources"); List<ClosedAdoptionSources.CycleSources> entries = new ArrayList<>();
        for (JsonNode row : manifest.get("cycles")) {
            entries.add(new ClosedAdoptionSources.CycleSources(direct(row.get("event")), direct(row.get("ordinaryCredit")), direct(row.get("autoAfter")),
                    direct(row.get("metricsAfter")), direct(row.get("beforePlan")), row.get("readonlySaveSkip").isNull() ? Optional.empty() : Optional.of(direct(row.get("readonlySaveSkip")))));
        }
        ClosedAdoptionSources business = new ClosedAdoptionSources(direct(businessRows.get("seed")), direct(businessRows.get("governance")),
                direct(businessRows.get("bound")), direct(businessRows.get("semantic")), direct(businessRows.get("capabilities")),
                direct(businessRows.get("classifierPin")), ExactRef.fromJson(businessRows.get("classifierSource").get("ref")),
                ExactRef.fromJson(businessRows.get("queueSource").get("ref")), direct(businessRows.get("captureProbe")), direct(businessRows.get("captureCleanup")), entries);
        ClosedPartialEpochProducer.Produced produced = ClosedPartialEpochProducer.compose(input, closed);
        RecoveryEvidence epoch = publish(root.resolve("closed-epoch.json"), produced.epochBytes()), prefix = publish(root.resolve("settled-prefix.json"), produced.prefixBytes());
        ObjectNode sdkFixture = StrictJson.object(); sdkFixture.put("machine_id", MACHINE); sdkFixture.put("pipe_name", "fixture-only-NOT-ACTUAL-SDK");
        RecoveryEvidence canonical = publish(root.resolve("NOT-ACTUAL-SDK-qualification.json"), StrictJson.canonical(sdkFixture));
        ClosedPartialAdmissionVerifier.OriginalSdkVerifier synthetic = (value, digest, e, p, actualSources) -> new RecoveryPrerequisiteVerifier.Verified(
                digest, e.reference(), p.reference(), canonical.reference(), ExactRef.fromJson(basisValue.get("refs").get("checkpoint_validator")),
                RecoveryEvidence.sha256(StrictJson.canonical(basisValue.get("checkpoint"))), value.currentDriver(), value.currentDriverIdentity(),
                value.currentSave(), value.currentSaveIdentity(), actualSources.settledCycles().size(), 11558);
        SourceCache cache = new SourceCache(); ClosedAdoptionMaterial material = new ClosedAdoptionMaterial(input, closed, epoch, prefix, business, cache, synthetic);
        Path canonicalPath = root.resolve("fixture-canonical/ROOT-CONTINUITY-WINDOW.json"); Files.createDirectories(canonicalPath.getParent());
        Files.write(canonicalPath, snapshotRaw); Path eventDirectory = canonicalPath.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS"); Files.createDirectories(eventDirectory);
        Files.write(eventDirectory.resolve("00000240.json"), direct(businessRows.get("lastCommittedEvent")).bytes());
        return new Fixture(root, material, canonical, new OriginalWriterTransaction.Target(canonicalPath,
                ExactRef.fromJson(businessRows.get("writerSource").get("ref"))), cache);
    }
    static RecoveryEvidence publish(Path path, byte[] raw) throws IOException { Files.write(path, raw); return evidence(path.toString(), raw); }
    private static WindowsFileWriterSession session(Fixture fixture, WindowsFileWriterSession.Mode mode) throws IOException {
        return WindowsFileWriterSession.start(settings(fixture),mode);
    }
    static WindowsFileWriterSession.Settings settings(Fixture fixture) throws IOException {
        Path python = Path.of(System.getProperty("xar.python", System.getenv().getOrDefault("XAR_ORACLE_PYTHON",
                repo().resolve("tools/.venv/Scripts/python.exe").toString())));
        Map<String, String> environment = new HashMap<>(System.getenv()); environment.put("PYTHONDONTWRITEBYTECODE", "1");
        return new WindowsFileWriterSession.Settings(python, repo(), fixture.root(),
                512L * 1024 * 1024, java.time.Duration.ofSeconds(30), java.time.Instant.now().plusSeconds(45), environment,
                moduleRef("current_saved_continuity_v1.py"),moduleRef("root_current_saved_campaign_cold_owner_v1.py"), () -> {
                    try { assertTrue(Files.getFileStore(fixture.root()).getUsableSpace() > 1_048_576); }
                    catch (IOException error) { throw new java.io.UncheckedIOException(error); }
                });
    }
    private static ExactRef moduleRef(String name) throws IOException {
        Path source=repo().resolve("tools/g2_saved_campaign").resolve(name); byte[] raw=bounded(source,2*1024*1024);
        return new ExactRef(source.toString(),raw.length,RecoveryEvidence.sha256(raw));
    }
    private static ObjectNode protocolEnvelopeWithSize(int bytes) {
        ObjectNode value = StrictJson.object();
        // Eight two-character keys contribute 65 syntax bytes; every individual value retains its 32K cap.
        for (int index = 0; index < 8; index++) {
            int count = index < 7 ? 32_768 : bytes - 65 - 7 * 32_768;
            value.put("x"+index,"a".repeat(count));
        }
        return value;
    }
    /** JSON trailing whitespace keeps the real request unchanged while exercising each full legal wire frame. */
    private static OriginalWriterTransaction.ManagedProcess paddedWriter(WindowsFileWriterSession actual, boolean overflow) {
        return new OriginalWriterTransaction.ManagedProcess() {
            private boolean closed;
            private final OutputStream padded = new OutputStream() {
                private final ByteArrayOutputStream line = new ByteArrayOutputStream();
                @Override public void write(int value) throws IOException {
                    if (value != '\n') { line.write(value); return; }
                    assertTrue(line.size() <= OriginalWriterTransaction.MAX_PROTOCOL_BYTES);
                    actual.stdin().write(line.toByteArray());
                    byte[] spaces = new byte[OriginalWriterTransaction.MAX_PROTOCOL_BYTES - line.size()];
                    java.util.Arrays.fill(spaces,(byte)' '); actual.stdin().write(spaces); actual.stdin().write('\n');
                    actual.stdin().flush(); line.reset();
                }
            };
            @Override public InputStream stdout() { return actual.stdout(); }
            @Override public OutputStream stdin() { return padded; }
            @Override public OriginalWriterTransaction.ActualExit awaitActualExit() throws IOException, InterruptedException { return actual.awaitActualExit(); }
            @Override public void closeOwnedInput() throws IOException {
                if (!closed) {
                    closed = true;
                    if (overflow) { actual.stdin().write('\n'); actual.stdin().flush(); }
                    actual.closeOwnedInput();
                }
            }
        };
    }
    private static Path writerRequest(Fixture fixture) throws IOException {
        try (var paths = Files.list(fixture.root())) {
            List<Path> requests = paths.filter(path -> path.getFileName().toString().startsWith("closed-partial-writer-")
                    && path.getFileName().toString().endsWith(".request.jsonl")).toList();
            assertEquals(1,requests.size()); return requests.get(0);
        }
    }
    static OriginalWriterTransaction.Target productionFixture(Fixture fixture) throws IOException {
        Path root = Files.createTempDirectory(fixture.root().getParent(),"closed-production-fixture-");
        Path canonical = root.resolve("ROOT-CONTINUITY-WINDOW.json"); Files.write(canonical,fixture.material().input().predecessor().bytes());
        Path events = root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"); Files.createDirectory(events);
        Files.write(events.resolve("00000240.json"),bounded(fixture.target().canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS").resolve("00000240.json"),RecoveryEvidence.MAX_BYTES));
        return new OriginalWriterTransaction.Target(canonical,fixture.target().originalWriter());
    }
    private static ClosedAdoptionApplication.Completed sharedStage(Fixture fixture, OriginalWriterTransaction.Target target,
            ClosedAdoptionMaterial.CurrentSource writerCurrent, String prefix, ClosedAdoptionApplication.CommitObserver observer) throws Exception {
        return ClosedAdoptionApplication.runOriginal(target,writerCurrent,fixture::material,fixture::canonical,
                raw -> publish(fixture.root().resolve(prefix+"-basis.json"),raw),
                raw -> publish(fixture.root().resolve(prefix+"-qualification.json"),raw),settings(fixture),observer);
    }

    @Test void explicitRootReviewUsesTheSharedTemporaryAndProductionWriterColdConsumerPath() throws Exception {
        Fixture fixture = fixture(); OriginalWriterTransaction.Target production = productionFixture(fixture);
        ClosedAdoptionApplication.Completed temporary = sharedStage(fixture,fixture.target(),fixture::material,"temporary",value -> { });
        ObjectNode result = StrictJson.object(); result.put("schema","synthetic-temporary-result-NOT-ACTUAL-SDK");
        result.set("temporary_head_ref",temporary.writer().head().evidence().reference().toJson());
        RecoveryEvidence temporaryResult = publish(fixture.root().resolve("synthetic-temporary-result.json"),StrictJson.canonical(result));
        var nativeMetadata = new WindowsSavedProofIdentityReader(); byte[] rawHead = fixture.material().input().predecessor().bytes();
        ExactRef actualHead = new ExactRef(production.canonicalPath().toString(),rawHead.length,RecoveryEvidence.sha256(rawHead));
        var now = java.time.Instant.now();
        var plan = new ClosedAdoptionReview.Plan(MACHINE,fixture.canonical().reference(),"0".repeat(32),production,actualHead,
                nativeMetadata.stat(production.canonicalPath()),now.plusSeconds(30));
        var challenge = ClosedAdoptionReview.createChallenge(plan,temporaryResult.reference(),MACHINE,fixture.canonical().reference(),
                "0".repeat(32),now.plusSeconds(40),now.plusSeconds(40),now);
        var approval = new ClosedAdoptionReview.Approval(challenge,ClosedAdoptionReview.Decision.APPROVE,now);
        assertEquals(ClosedAdoptionReview.Decision.APPROVE,ClosedAdoptionReview.validateApproval(challenge,
                ClosedAdoptionReview.Approval.decode(StrictJson.canonical(approval.toJson())),now));
        AtomicInteger lockChecks = new AtomicInteger();
        ClosedAdoptionMaterial.CurrentSource guarded = () -> {
            lockChecks.incrementAndGet();
            try { assertEquals(plan.predecessorIdentity(),nativeMetadata.stat(production.canonicalPath())); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
            return fixture.material();
        };
        AtomicReference<OriginalWriterTransaction.Committed> observed = new AtomicReference<>();
        ClosedAdoptionApplication.Completed completed = sharedStage(fixture,production,guarded,"production",observed::set);
        assertEquals(2,lockChecks.get()); assertSame(completed.writer(),observed.get());
        assertEquals(production.canonicalPath().toString(),StrictJson.parse(completed.basis().bytes()).get("refs").get("ledger").get("path").textValue());
        assertEquals(production.canonicalPath().toString(),StrictJson.parse(completed.qualification().bytes()).get("committed_head_ref").get("path").textValue());
        assertEquals(fixture.target().canonicalPath().toString(),StrictJson.parse(temporary.basis().bytes()).get("refs").get("ledger").get("path").textValue());
        assertEquals(2,completed.actualJobs().size()); assertTrue(completed.actualJobs().stream().allMatch(WindowsJobProcess.CommandResult::passed));
        assertFalse(completed.grantsWarmAttachment()); assertEquals(11559,StrictJson.parse(completed.consumer().originalConsumerReceipt()).get("next_sequence").longValue());
    }
    @Test void sharedExecutionReportsTheActualCommittedWriterBeforeALaterPublicationFailure() throws Exception {
        Fixture fixture = fixture(); OriginalWriterTransaction.Target production = productionFixture(fixture);
        AtomicReference<OriginalWriterTransaction.Committed> observed = new AtomicReference<>();
        IOException error = assertThrows(IOException.class,() -> ClosedAdoptionApplication.runOriginal(production,fixture::material,fixture::material,
                fixture::canonical,raw -> { throw new IOException("synthetic post-commit publication refusal"); },
                raw -> publish(fixture.root().resolve("must-not-publish.json"),raw),settings(fixture),observed::set));
        assertEquals("synthetic post-commit publication refusal",error.getMessage()); assertNotNull(observed.get());
        assertEquals(241,StrictJson.parse(bounded(production.canonicalPath(),RecoveryEvidence.MAX_BYTES)).get("sequence").longValue());
        assertEquals(0,observed.get().processExit().exitCode()); assertFalse(Files.exists(fixture.root().resolve("must-not-publish.json")));
        try (var files = Files.list(fixture.root())) { assertFalse(files.anyMatch(path -> path.getFileName().toString().startsWith("closed-partial-cold_consumer-"))); }
    }

    @Test void actualWriterFileSessionAcceptsTwoMaximumLinesIncludingBothNewlines() throws Exception {
        Fixture fixture = fixture(); AtomicReference<WindowsFileWriterSession> launched = new AtomicReference<>();
        OriginalWriterTransaction.Committed committed = OriginalWriterTransaction.execute(fixture.target(),fixture::material,
                target -> { var process = session(fixture,WindowsFileWriterSession.Mode.WRITER); launched.set(process); return paddedWriter(process,false); });
        WindowsFileWriterSession actual = launched.get(); assertNotNull(actual);
        assertEquals(241,committed.head().value().get("sequence").longValue());
        assertEquals(WindowsFileWriterSession.MAX_WRITER_STREAM_BYTES,Files.size(writerRequest(fixture)));
        assertEquals(0,actual.actualCommandResult().orElseThrow().exitCode());
        assertEquals(0,actual.actualCommandResult().orElseThrow().accounting().activeProcesses());
    }
    @Test void actualWriterFileSessionRejectsOneByteWholeStreamOverflowAndRetainsTerminal() throws Exception {
        Fixture fixture = fixture(); AtomicReference<WindowsFileWriterSession> launched = new AtomicReference<>();
        IOException error = assertThrows(IOException.class,() -> OriginalWriterTransaction.execute(fixture.target(),fixture::material,
                target -> { var process = session(fixture,WindowsFileWriterSession.Mode.WRITER); launched.set(process); return paddedWriter(process,true); }));
        WindowsFileWriterSession actual = launched.get(); assertNotNull(actual);
        assertTrue(error.getMessage().contains("transport guard failed"));
        assertEquals(WindowsFileWriterSession.MAX_WRITER_STREAM_BYTES+1,Files.size(writerRequest(fixture)));
        assertTrue(Files.isRegularFile(actual.terminalPath()));
        assertEquals(0,actual.actualCommandResult().orElseThrow().accounting().activeProcesses());
    }

    @Test void actualOriginalWriterLockReadbackIdempotenceAndActualOriginalColdConsumer() throws Exception {
        Fixture fixture = fixture(); byte[] pending = fixture.material().input().rawState().bytes();
        AtomicInteger phases = new AtomicInteger(); ClosedAdoptionMaterial.CurrentSource current = () -> { phases.incrementAndGet(); return fixture.material(); };
        OriginalWriterTransaction.Committed first = OriginalWriterTransaction.execute(fixture.target(), current,
                target -> session(fixture, WindowsFileWriterSession.Mode.WRITER));
        assertFalse(first.idempotentReplay()); assertEquals(2, phases.get());
        assertEquals(241, first.head().value().get("sequence").longValue()); assertEquals("repair_required", first.head().value().get("status").textValue());
        assertEquals(5182, first.head().value().get("last_settled_cycles").longValue());
        OriginalWriterTransaction.Committed repeat = OriginalWriterTransaction.execute(fixture.target(), current,
                target -> session(fixture, WindowsFileWriterSession.Mode.WRITER));
        assertTrue(repeat.idempotentReplay()); assertEquals(first.event().evidence(), repeat.event().evidence());
        ClosedColdInputsConsumer.Prepared prepared = ClosedColdInputsConsumer.prepare(current, repeat, fixture::canonical);
        RecoveryEvidence basis = publish(fixture.root().resolve("current-basis.json"), prepared.basisBytes());
        RecoveryEvidence qualification = publish(fixture.root().resolve("current-qualification.json"), prepared.qualificationBytes(basis.reference()));
        OriginalColdConsumerSession.Consumed consumed = OriginalColdConsumerSession.run(current, repeat, fixture::canonical, basis, qualification,
                () -> session(fixture, WindowsFileWriterSession.Mode.COLD_CONSUMER));
        JsonNode result = StrictJson.parse(consumed.originalConsumerReceipt()); assertEquals(5182, result.get("completed_cycles").longValue());
        assertEquals(11559, result.get("next_sequence").longValue()); assertFalse(consumed.grantsWarmAttachment());
        assertEquals(0, consumed.processExit().exitCode()); assertArrayEquals(pending, fixture.material().input().rawState().bytes());
        assertEquals(5190, StrictJson.parse(pending).get("pending_cycle").get("global_turn").longValue());
        assertTrue(java.util.stream.StreamSupport.stream(result.get("unknown_requests").spliterator(), false)
                .anyMatch(row -> row.get("sequence").longValue() == 11558 && !row.get("replayed").booleanValue()));
    }
    @Test void missingActualSdkProofStopsBeforeAnyWriterLaunch() throws Exception {
        Fixture fixture = fixture(); var old = fixture.material();
        ClosedAdoptionMaterial unavailable = new ClosedAdoptionMaterial(old.input(), old.sources(), old.publishedEpoch(), old.publishedPrefix(), old.business(),
                old.sourceVerifier(), ClosedPartialAdmissionVerifier.unavailableOriginalSdk()); AtomicInteger launches = new AtomicInteger();
        assertThrows(ContractViolationException.class, () -> OriginalWriterTransaction.execute(fixture.target(), () -> unavailable, target -> {
            launches.incrementAndGet(); return session(fixture, WindowsFileWriterSession.Mode.WRITER);
        }));
        assertEquals(0, launches.get()); assertFalse(Files.exists(fixture.target().canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS").resolve("00000241.json")));
    }
    @Test void actualLockedPredecessorDriftCannotCommit() throws Exception {
        Fixture fixture = fixture(); ObjectNode changed = (ObjectNode) StrictJson.parse(fixture.material().input().predecessor().bytes());
        changed.put("fixture_unexpected_change", true); Files.write(fixture.target().canonicalPath(), StrictJson.canonical(changed));
        assertThrows(ContractViolationException.class, () -> OriginalWriterTransaction.execute(fixture.target(), fixture::material,
                target -> session(fixture, WindowsFileWriterSession.Mode.WRITER)));
        assertFalse(Files.exists(fixture.target().canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS").resolve("00000241.json")));
    }
    @Test void queryPrefixNamesAndBooleanNativeIdsCannotBypassTheTypedClassifier() throws Exception {
        Fixture fixture = fixture(); ObjectNode auto = (ObjectNode) fixture.material().sources().settledCycles().get(3).auto().object().get("result").get("structured_content");
        SavedFrame frame = SavedFrame.fromJson(StrictJson.parse(fixture.material().business().coldBound().bytes()).get("opening_frame"));
        ObjectNode unsupported = auto.deepCopy(); unsupported.put("selected_step", "query-any-arbitrary-action");
        assertThrows(ContractViolationException.class, () -> SettledQueryClassifier.classify(unsupported, frame));
        ObjectNode invalid = auto.deepCopy(); ((ObjectNode) invalid.get("result").get("war_termination_options")).put("war_id", true);
        assertThrows(ContractViolationException.class, () -> SettledQueryClassifier.classify(invalid, frame));
        ObjectNode opaque = StrictJson.object(); opaque.set("historical_extension", StrictJson.parse("6.0".getBytes(StandardCharsets.UTF_8)));
        assertTrue(StrictJson.parse(ClosedAdoptionJson.encode(opaque)).get("historical_extension").isFloatingPointNumber());
    }
    @Test void actualHeadEnvelopeUsesItsOwnBoundAndRejectsOneByteOverflow() throws Exception {
        Fixture fixture = fixture(); JsonNode head = StrictJson.parse(fixture.material().input().predecessor().bytes());
        ObjectNode envelope = StrictJson.object();
        for (String field : List.of("expected_predecessor", "expected_reduced", "expected_committed")) { envelope.set(field, head); }
        ByteArrayOutputStream output = new ByteArrayOutputStream(); OriginalWriterTransaction.send(output, envelope);
        assertTrue(output.size() > 112_269 && output.size() <= OriginalWriterTransaction.MAX_PROTOCOL_BYTES + 1);
        assertEquals(envelope, OriginalWriterTransaction.read(new ByteArrayInputStream(output.toByteArray())));
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionJson.encode(envelope));
        ObjectNode exact = protocolEnvelopeWithSize(OriginalWriterTransaction.MAX_PROTOCOL_BYTES);
        output.reset(); OriginalWriterTransaction.send(output, exact);
        assertEquals(OriginalWriterTransaction.MAX_PROTOCOL_BYTES + 1, output.size());
        assertEquals(exact, OriginalWriterTransaction.read(new ByteArrayInputStream(output.toByteArray())));
        ObjectNode over = protocolEnvelopeWithSize(OriginalWriterTransaction.MAX_PROTOCOL_BYTES+1);
        assertThrows(ContractViolationException.class, () -> OriginalWriterTransaction.send(new ByteArrayOutputStream(), over));
        ByteArrayOutputStream overflowWire = new ByteArrayOutputStream();
        overflowWire.write(StrictJson.canonical(over,StrictJson.EXPLICIT_MAX_BYTES)); overflowWire.write('\n');
        byte[] oversized = overflowWire.toByteArray();
        assertThrows(IOException.class, () -> OriginalWriterTransaction.read(new ByteArrayInputStream(oversized)));
    }
    @Test void temporaryInvocationRejectsBooleanLimitsAndUnexpectedAuthorityFields() throws Exception {
        Fixture fixture = fixture(); ObjectNode row = StrictJson.object();
        row.put("schema","xar.closed-partial-temporary-invocation/v1"); row.put("machine_id",MACHINE);
        row.set("adoption_request_ref",fixture.canonical().reference().toJson()); row.set("sdk_read_ticket_ref",fixture.canonical().reference().toJson());
        row.put("repo",repo().toString()); row.put("python_executable",repo().resolve("tools/.venv/Scripts/python.exe").toString());
        row.put("output_root",fixture.root().toString()); row.put("memory_limit_bytes",512L*1024*1024); row.put("timeout_seconds",60);
        row.put("lease_deadline_utc","2026-10-22T15:30:00Z"); row.put("minimum_free_bytes",1_048_576); row.put("maximum_output_bytes",8*1024*1024);
        row.set("mechanical_source_ref",moduleRef("current_saved_continuity_v1.py").toJson());
        row.set("cold_owner_source_ref",moduleRef("root_current_saved_campaign_cold_owner_v1.py").toJson());
        var parsed = ClosedAdoptionMain.Invocation.decode(StrictJson.canonical(row)); assertEquals(MACHINE,parsed.machine());
        ObjectNode invalid = row.deepCopy(); invalid.put("memory_limit_bytes",true);
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionMain.Invocation.decode(StrictJson.canonical(invalid)));
        row.put("SDK_proof_verified",true);
        assertThrows(ContractViolationException.class, () -> ClosedAdoptionMain.Invocation.decode(StrictJson.canonical(row)));
    }
}
