package org.xar.ck3.control.wave2.runtime.savedproof;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.SdkDerivedSource32;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Explicit one-read operation. A consumed nonce is never automatically retried. */
public final class SavedCheckpointMeasurementCoordinator {
    private final ManagedSdkMeasurementRunner runner;
    private final SavedProofIdentityReader identities;
    private final Clock clock;
    private final ExactSourceReader sources;
    private SavedCheckpointMeasurement cached;
    private RetainedClosedMeasurement retainedClosedMeasurement;
    private List<ExactRef> cachedSources = List.of();

    public SavedCheckpointMeasurementCoordinator(WindowsJobSdkMeasurementRunner runner,
            WindowsSavedProofIdentityReader identities) {
        this(runner,identities,Clock.systemUTC(),SavedProofFiles::exact);
    }

    /** Package-private deterministic boundaries; no launcher or JSON decoder exposes these seams. */
    SavedCheckpointMeasurementCoordinator(ManagedSdkMeasurementRunner runner, SavedProofIdentityReader identities,
            Clock clock, ExactSourceReader sources) {
        this.runner = Objects.requireNonNull(runner); this.identities = Objects.requireNonNull(identities);
        this.clock = Objects.requireNonNull(clock); this.sources = Objects.requireNonNull(sources);
    }

    @FunctionalInterface
    interface ExactSourceReader {
        byte[] exact(ExactRef reference, int maximumBytes) throws IOException;
    }

    public synchronized boolean hasMeasuredCache() { return cached != null; }

    public synchronized SavedCheckpointMeasurement measureOnce(SavedProofReadTicket ticket)
            throws IOException, InterruptedException {
        return measure(ticket,false);
    }
    public synchronized ColdRestoreMeasurement measureColdRestoreOnce(SavedProofReadTicket ticket) throws IOException, InterruptedException {
        measure(ticket,true); return java.util.Objects.requireNonNull(coldRestoreCached);
    }
    private ColdRestoreMeasurement coldRestoreCached;
    public synchronized ColdRestoreMeasurement requireCurrentColdRestoreCached() throws IOException {
        StrictJson.require(coldRestoreCached != null,"actual same-JVM cold restore SDK measurement required");
        StrictJson.require(requireCurrentCached() == coldRestoreCached.checkpoint(),"same retained actual post-HELLO cache");
        return coldRestoreCached;
    }
    private SavedCheckpointMeasurement measure(SavedProofReadTicket ticket, boolean coldRestore) throws IOException, InterruptedException {
        Objects.requireNonNull(ticket);
        StrictJson.require(cached == null, "coordinator already measured; consume its unchanged cache");
        requireCurrent(ticket);
        StrictJson.require(Files.isDirectory(ticket.outputRoot(), LinkOption.NOFOLLOW_LINKS)
                && !Files.isSymbolicLink(ticket.outputRoot()), "existing owned finite output root");
        byte[] releaseBytes = sources.exact(ticket.release().reference(), 65_536);
        StrictJson.require(java.util.Arrays.equals(releaseBytes, ticket.release().bytes())
                && SavedProofReadTicket.parse(ticket.release()).equals(ticket), "ticket is the exact independently issued release");
        Map<String, ExactRef> pins = sourcePins(ticket,sources);
        requireIdentities(ticket); requireCurrent(ticket);
        Path claim = ticket.outputRoot().resolve("sdk-" + ticket.nonce() + ".consumed.json");
        ObjectNode claimed = StrictJson.object(); claimed.put("schema", "xar.sdk-measurement-nonce-consumed/v1");
        claimed.put("machine_id", ticket.machineId()); claimed.put("observed_at_utc", clock.instant().toString());
        claimed.put("nonce", ticket.nonce()); claimed.set("release_ref", ticket.release().reference().toJson());
        claimed.put("worker_source_sha256", FixedSdkTransport.sourceSha256());
        SavedProofFiles.publish(claim, StrictJson.canonical(claimed));
        RecoveryEvidence inventory = SavedProofFiles.publish(ticket.outputRoot().resolve("sdk-" + ticket.nonce() + ".source-inventory.json"),
                FixedSdkTransport.sourceInventory(ticket,pins));
        Path request = ticket.outputRoot().resolve("sdk-" + ticket.nonce() + ".request.json");
        Files.write(request, FixedSdkTransport.request(ticket,coldRestore,inventory.reference()), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        ManagedSdkMeasurementRunner.Outcome outcome = runner.run(ticket, request);
        publishTerminal(ticket, outcome, clock.instant());
        StrictJson.require(outcome.command().passed()
                && outcome.command().accounting().memoryLimitBytes() == ticket.jobMemoryBytes(), "actual SDK managed exit/Job terminal state");
        byte[] stdout = SavedProofFiles.read(outcome.stdout(), 65_536);
        ColdRestoreDriverLineage lineage = null;
        byte[] common = stdout;
        if (coldRestore) {
            JsonNode parsed = StrictJson.parse(stdout); StrictJson.require(parsed.isObject(),"actual cold restore transport object");
            ObjectNode full = (ObjectNode)parsed;
            StrictJson.require("xar.original-sdk-current-save-transport/v2".equals(StrictJson.text(full.get("schema"))),"actual post-HELLO worker result version");
            lineage = ColdRestoreDriverLineage.decode(StrictJson.object(full.get("cold_restore_lineage"),Set.of("schema","format_version","bridge_pid","episode_character_id","episode_run_id","succession_lifecycle")));
            ObjectNode normalized = full.deepCopy(); normalized.remove("cold_restore_lineage");
            normalized.put("schema","xar.original-sdk-current-save-transport/v1"); common = StrictJson.canonical(normalized);
        }
        Observation observation = decode(ticket, common, pins);
        requireCurrentScope(ticket.machineId(),observation.observed(),ticket.reviewAt()); requireIdentities(ticket);
        sourcePins(ticket,sources);
        for (ExactRef source : observation.importedSources()) { sources.exact(source, 2_097_152); }
        requireIdentities(ticket); requireCurrentScope(ticket.machineId(),observation.observed(),ticket.reviewAt());
        RecoveryEvidence transport = new RecoveryEvidence(new ExactRef(outcome.stdout().toString(), stdout.length, RecoveryEvidence.sha256(stdout)), stdout);
        byte[] receiptBytes = qualification(ticket, observation);
        RecoveryEvidence receipt = SavedProofFiles.publish(ticket.outputRoot().resolve("sdk-" + ticket.nonce() + ".canonical-qualification.json"), receiptBytes);
        requireIdentities(ticket); requireCurrentScope(ticket.machineId(),observation.observed(),ticket.reviewAt());
        cachedSources = observation.importedSources();
        cached = new SavedCheckpointMeasurement(ticket, receipt, transport, observation.driver(), ticket.driverIdentity(),
            RecoveryEvidence.sha256(StrictJson.canonical(observation.originalSdkAnchor())), FixedSdkTransport.sourceSha256(), observation.observed());
        if (coldRestore) { coldRestoreCached = new ColdRestoreMeasurement(cached,java.util.Objects.requireNonNull(lineage)); }
        return cached;
    }

    /** No Driver/SAVE body access: fresh native attributes plus exact source metadata only. */
    public synchronized SavedCheckpointMeasurement requireCurrentCached() throws IOException {
        StrictJson.require(cached != null, "actual original SDK measurement is unavailable");
        requireCurrentCacheScope(); requireCachedIdentities();
        sources.exact(cached.sdkFreeze(), 1_048_576);
        for (ExactRef source : cachedSources) { sources.exact(source, 2_097_152); }
        sources.exact(cached.canonicalCheckpointProof(), 65_536);
        requireCachedIdentities(); requireCurrentCacheScope();
        return cached;
    }


    /**
     * Explicitly retain the measured closed facts while the original Driver is still current.
     * The caller must first finish the original writer/cold qualification. This method alone
     * does not prove that qualification and never grants a new source tuple or warm attachment.
     */
    public synchronized RetainedClosedMeasurement retainClosedMeasurement() throws IOException {
        StrictJson.require(retainedClosedMeasurement == null,
                "closed measurement context is retained once; reuse it without renewal");
        SavedCheckpointMeasurement original = requireCurrentCached();
        var historical = new RetainedClosedMeasurement.HistoricalInputs(original.machineId(),
                original.observedAtUtc(), original.reviewAtUtc(), clock.instant(), original.nonce(),
                original.releaseRef(), original.canonicalReceipt(), original.validatorSource(),
                original.sdkFreeze(), original.checkpointDigest(), original.workerSourceSha256(),
                original.driver(), original.driverIdentity(), original.save(), original.saveIdentity(),
                cachedSources);
        retainedClosedMeasurement = RetainedClosedMeasurement.retainFor(this,historical);
        return retainedClosedMeasurement;
    }

    /** Called only by the exact retained object; this path deliberately makes no current Driver claim. */
    synchronized RetainedClosedMeasurement.HistoricalInputs requireRetainedHistoricalInputs(
            RetainedClosedMeasurement requested) throws IOException {
        StrictJson.require(requested != null && requested == retainedClosedMeasurement && cached != null,
                "exact historical context retained by the original live coordinator required");
        var historical = requested.retainedInputs(this);
        RetainedClosedMeasurement.requireMetadata(historical,new RetainedClosedMeasurement.MetadataReader() {
            @Override public FileStatIdentity statSave(Path path) throws IOException { return identities.stat(path); }
            @Override public void requireExact(ExactRef reference, int maximumBytes) throws IOException {
                SavedProofFiles.exact(reference,maximumBytes);
            }
        },clock,WindowsJobProcess.currentMachineId(),FixedSdkTransport.sourceSha256());
        return historical;
    }

    private void requireCurrent(SavedProofReadTicket ticket) {
        requireCurrentScope(ticket.machineId(),ticket.observedAt(),ticket.reviewAt());
    }
    private void requireCurrentScope(String machineId, Instant observedAt, Instant reviewAt) {
        Instant now = clock.instant();
        StrictJson.require(!now.isBefore(observedAt) && now.isBefore(reviewAt)
                && machineId.equals(WindowsJobProcess.currentMachineId()), "current independently authorized measurement scope");
    }
    private void requireCurrentCacheScope() {
        requireCurrentScope(cached.machineId(),cached.observedAtUtc(),cached.reviewAtUtc());
        StrictJson.require(cached.workerSourceSha256().equals(FixedSdkTransport.sourceSha256()), "current unchanged SDK cache scope");
    }
    private void requireCachedIdentities() throws IOException {
        StrictJson.require(identities.stat(Path.of(cached.driver().path())).equals(cached.driverIdentity())
                && identities.stat(Path.of(cached.save().path())).equals(cached.saveIdentity()), "current Driver/SAVE attributes match the measured cache");
    }
    private void requireIdentities(SavedProofReadTicket ticket) throws IOException {
        StrictJson.require(identities.stat(ticket.driverPath()).equals(ticket.driverIdentity())
                && identities.stat(Path.of(ticket.save().path())).equals(ticket.saveIdentity()), "fresh exact Driver/SAVE attributes");
    }

    public static Map<String, ExactRef> sourcePins(SavedProofReadTicket ticket) throws IOException {
        return sourcePins(ticket,SavedProofFiles::exact);
    }
    private static Map<String, ExactRef> sourcePins(SavedProofReadTicket ticket, ExactSourceReader sources) throws IOException {
        Map<String,ExactRef> pins = sourceInventoryPins(ticket.machineId(),ticket.sdkRoot(),ticket.sdkFreeze(),sources);
        StrictJson.require(ticket.validatorSource().equals(pins.get("xar_autoplayer/cold_checkpoint_validator.py")), "validator source exactly from frozen inventory");
        sources.exact(ticket.validatorSource(), 65_536);
        return pins;
    }
    /** Data-only source projection. This does not measure persistence or grant a Root/Native session. */
    public static Map<String,ExactRef> sourceInventoryPins(String machineId, Path sdkRoot, ExactRef sdkFreeze) throws IOException {
        return sourceInventoryPins(machineId,sdkRoot,sdkFreeze,SavedProofFiles::exact);
    }
    private static Map<String,ExactRef> sourceInventoryPins(String machineId, Path sdkRoot, ExactRef sdkFreeze,
            ExactSourceReader sources) throws IOException {
        JsonNode inventory = StrictJson.parse(sources.exact(sdkFreeze, 1_048_576), 1_048_576);
        if (inventory.isObject() && inventory.hasNonNull("schema")
                && SdkDerivedSource32.SCHEMA.equals(StrictJson.text(inventory.get("schema")))) {
            var reference = new ControlBuild.FileRef(sdkFreeze.path(),sdkFreeze.bytes(),sdkFreeze.sha256());
            var verified = SdkDerivedSource32.verify(reference);
            StrictJson.require(machineId.equals(verified.machineId()) && sdkRoot.equals(Path.of(verified.sdkRoot()))
                    && !verified.runtimeAdmitted(),"explicit actual Java-verified derived SDK source scope");
            var lineage = SdkDerivedSource32.read(reference);
            Map<String,ExactRef> derived = new HashMap<>();
            for (var row : lineage.currentInventory()) {
                Path path = sdkRoot.resolve(row.relativePath()).normalize();
                StrictJson.require(path.startsWith(sdkRoot),"typed derived SDK inventory child");
                var exact = new ExactRef(path.toString(),row.content().bytes(),row.content().sha256());
                StrictJson.require(derived.putIfAbsent(row.relativePath(),exact) == null,"unique typed derived SDK source");
            }
            // Recheck the exact source lineage after consuming its typed projection.
            reference.verify(); verified.assemblyActualRef().verify();
            return Map.copyOf(derived);
        }
        StrictJson.require(inventory.isObject() && machineId.equals(StrictJson.text(inventory.get("machine_id")))
                && sdkRoot.equals(Path.of(StrictJson.text(inventory.get("source_root"))))
                && inventory.get("files") != null && inventory.get("files").isArray(), "actual source inventory root/machine");
        Map<String, ExactRef> pins = new HashMap<>();
        for (JsonNode item : inventory.get("files")) {
            ObjectNode row = StrictJson.object(item, Set.of("bytes", "git_blob_sha1", "git_mode", "relative", "sha256"));
            StrictJson.require(StrictJson.text(row.get("git_blob_sha1")).matches("[0-9a-f]{40}")
                    && StrictJson.text(row.get("git_mode")).matches("100644|100755"), "actual regular Git source inventory item");
            String relative = StrictJson.text(row.get("relative")); Path child = Path.of(relative);
            StrictJson.require(!child.isAbsolute() && !relative.contains("\\") && !relative.contains(":")
                    && child.normalize().equals(child) && !relative.startsWith("../") && !relative.equals(".."), "inventory relative child");
            ExactRef ref = new ExactRef(sdkRoot.resolve(child).toString(),
                StrictJson.integer(row.get("bytes"), 0, StrictJson.MAX_SAFE_INTEGER), StrictJson.text(row.get("sha256")));
            StrictJson.require(pins.putIfAbsent(relative, ref) == null, "unique source inventory item");
        }
        return Map.copyOf(pins);
    }

    record Observation(ExactRef driver, ObjectNode checkpoint, ObjectNode originalSdkAnchor, Instant observed, List<ExactRef> importedSources) {
        Observation { checkpoint = checkpoint.deepCopy(); originalSdkAnchor = originalSdkAnchor.deepCopy(); importedSources = List.copyOf(importedSources); }
        @Override public ObjectNode checkpoint() { return checkpoint.deepCopy(); }
        @Override public ObjectNode originalSdkAnchor() { return originalSdkAnchor.deepCopy(); }
    }
    static Observation decode(SavedProofReadTicket ticket, byte[] raw, Map<String, ExactRef> pins) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "status", "machine_id", "nonce", "observed_at_utc",
            "worker_source_sha256", "sdk_freeze_ref", "validator_ref", "driver_ref", "driver_identity_before", "driver_identity_after",
            "save_ref", "save_identity_before", "save_identity_after", "checkpoint", "anchor", "pipe_name", "counts", "imported_sources",
            "Driver_SAVE_body_rewritten", "Game_RPC_calls"));
        StrictJson.require("xar.original-sdk-current-save-transport/v1".equals(StrictJson.text(row.get("schema")))
                && "ORIGINAL_SDK_CALL_COMPLETED".equals(StrictJson.text(row.get("status")))
                && ticket.machineId().equals(StrictJson.text(row.get("machine_id")))
                && ticket.nonce().equals(StrictJson.text(row.get("nonce")))
                && FixedSdkTransport.sourceSha256().equals(StrictJson.text(row.get("worker_source_sha256")))
                && ticket.sdkFreeze().equals(ExactRef.fromJson(row.get("sdk_freeze_ref")))
                && ticket.validatorSource().equals(ExactRef.fromJson(row.get("validator_ref")))
                && ticket.save().equals(ExactRef.fromJson(row.get("save_ref")))
                && ticket.pipeName().equals(StrictJson.text(row.get("pipe_name"))), "actual request/source binding");
        Instant observed = Instant.parse(StrictJson.utc(StrictJson.text(row.get("observed_at_utc"))));
        StrictJson.require(!observed.isBefore(ticket.observedAt()) && observed.isBefore(ticket.reviewAt()), "actual SDK time within release");
        for (String key : List.of("driver_identity_before", "driver_identity_after")) {
            StrictJson.require(ticket.driverIdentity().equals(FileStatIdentity.fromJson(row.get(key), FileStatIdentity.SCHEMA)), "stable exact Driver identity");
        }
        for (String key : List.of("save_identity_before", "save_identity_after")) {
            StrictJson.require(ticket.saveIdentity().equals(FileStatIdentity.fromJson(row.get(key), FileStatIdentity.SCHEMA)), "stable exact SAVE identity");
        }
        ExactRef driver = ExactRef.fromJson(row.get("driver_ref"));
        StrictJson.require(ticket.driverPath().equals(Path.of(driver.path()))
                && ticket.driverIdentity().bytes().equals(BigInteger.valueOf(driver.bytes())), "measured whole Driver ref");
        ObjectNode counts = StrictJson.object(row.get("counts"), Set.of("driver_physical_body_reads", "driver_physical_read_bytes", "original_validator_calls", "save_sha256_calls"));
        for (String key : List.of("driver_physical_body_reads", "original_validator_calls", "save_sha256_calls")) { StrictJson.integer(counts.get(key), 1, 1); }
        StrictJson.integer(counts.get("driver_physical_read_bytes"), driver.bytes(), driver.bytes());
        StrictJson.integer(row.get("Game_RPC_calls"), 0, 0);
        StrictJson.require(row.get("Driver_SAVE_body_rewritten").isBoolean() && !row.get("Driver_SAVE_body_rewritten").booleanValue(), "no body mutation");
        ObjectNode checkpoint = validateCheckpointBinding(ticket.save(), row.get("checkpoint"), row.get("anchor"));
        ObjectNode anchor = (ObjectNode) row.get("anchor");
        StrictJson.require(row.get("imported_sources").isArray() && !row.get("imported_sources").isEmpty(), "complete actual imported SDK source pins");
        List<ExactRef> imported = new ArrayList<>(); Set<String> seen = new java.util.HashSet<>();
        for (JsonNode item : row.get("imported_sources")) {
            ObjectNode source = StrictJson.object(item, Set.of("relative", "bytes", "sha256"));
            String relative = StrictJson.text(source.get("relative")); ExactRef expected = pins.get(relative);
            StrictJson.require(expected != null && seen.add(relative)
                && expected.bytes() == StrictJson.integer(source.get("bytes"), 0, 2_097_152)
                && expected.sha256().equals(StrictJson.text(source.get("sha256"))), "actual import belongs to frozen source inventory");
            imported.add(expected);
        }
        StrictJson.require(seen.contains("xar_autoplayer/cold_checkpoint_validator.py") && seen.contains("xar_autoplayer/native_session.py"), "actual validator and SAVE hasher source observations");
        return new Observation(driver, checkpoint, anchor, observed, imported);
    }

    static ObjectNode validateCheckpointBinding(ExactRef save, JsonNode rawCheckpoint, JsonNode normalizedAnchor) {
        StrictJson.require(rawCheckpoint instanceof ObjectNode, "raw Native checkpoint object");
        ObjectNode checkpoint = (ObjectNode) rawCheckpoint;
        ObjectNode anchor = StrictJson.object(normalizedAnchor, Set.of("name", "load_save_name", "path", "size", "sha256", "saved_date_raw", "history_index", "succession_lifecycle"));
        StrictJson.text(anchor.get("name")); StrictJson.text(anchor.get("load_save_name"));
        long savedDate = StrictJson.integer(anchor.get("saved_date_raw"), 0, StrictJson.MAX_SAFE_INTEGER);
        long historyIndex = StrictJson.integer(anchor.get("history_index"), 1, StrictJson.MAX_SAFE_INTEGER);
        StrictJson.require(checkpoint.has("sha256") && checkpoint.has("size") && checkpoint.has("date_raw") && checkpoint.has("history_index"), "complete measured checkpoint anchor fields");
        StrictJson.require(save.path().equals(StrictJson.text(anchor.get("path")))
                && save.sha256().equals(StrictJson.text(anchor.get("sha256")))
                && StrictJson.integer(anchor.get("size"), save.bytes(), save.bytes()) == save.bytes()
                && save.sha256().equals(StrictJson.text(checkpoint.get("sha256")))
                && StrictJson.integer(checkpoint.get("size"), save.bytes(), save.bytes()) == save.bytes()
                && StrictJson.integer(checkpoint.get("date_raw"), savedDate, savedDate) == savedDate
                && StrictJson.integer(checkpoint.get("history_index"), historyIndex, historyIndex) == historyIndex,
                "original SDK canonical SAVE anchor");
        return checkpoint.deepCopy();
    }

    static byte[] qualification(SavedProofReadTicket ticket, Observation observation) {
        ObjectNode row = StrictJson.object();
        row.put("schema", "xar.current-saved-recovery-checkpoint-qualification/v1");
        row.put("status", "ORIGINAL_SDK_SAVED_CHECKPOINT_QUALIFIED");
        row.put("machine_id", ticket.machineId()); row.put("observed_at_utc", observation.observed().toString());
        row.set("validator_source_ref", ticket.validatorSource().toJson()); row.set("driver_ref", observation.driver().toJson());
        row.set("driver_identity_before", ticket.driverIdentity().toJson()); row.set("driver_identity_after", ticket.driverIdentity().toJson());
        row.set("save_ref", ticket.save().toJson()); row.set("save_identity_before", ticket.saveIdentity().toJson()); row.set("save_identity_after", ticket.saveIdentity().toJson());
        row.set("checkpoint", observation.checkpoint()); row.put("pipe_name", ticket.pipeName());
        row.put("driver_physical_body_reads", 1); row.put("driver_payload_reader_calls", 1);
        row.put("driver_physical_read_scope", "entire_operation_including_caller_reference_measurement");
        row.put("driver_payload_reader_scope", "pinned_reader_or_caller_premeasured_RAM");
        row.put("original_validator_calls", 1); row.put("save_sha256_calls", 1);
        row.put("driver_body_rewritten", false); row.put("ledger_write_already_performed", false); row.put("game_or_RPC_calls", 0);
        return StrictJson.canonical(row);
    }

    static void publishTerminal(SavedProofReadTicket ticket, ManagedSdkMeasurementRunner.Outcome outcome, Instant observed) throws IOException {
        WindowsJobProcess.CommandResult command = outcome.command();
        ObjectNode value = StrictJson.object(); value.put("schema", "xar.original-sdk-managed-terminal/v1");
        value.put("machine_id", ticket.machineId()); value.put("observed_at_utc", observed.toString());
        value.put("nonce", ticket.nonce()); value.put("worker_source_sha256", FixedSdkTransport.sourceSha256());
        value.set("release_ref", ticket.release().reference().toJson()); value.put("exit_code", command.exitCode());
        value.put("elapsed_seconds_decimal", Double.toString(command.elapsedSeconds())); value.put("pid", command.identity().pid());
        value.put("creation_filetime", command.identity().creationFiletimeDecimal()); value.put("executable", command.identity().executable());
        value.put("job_active", command.accounting().activeProcesses()); value.put("job_peak_bytes", command.accounting().peakJobMemoryBytes());
        value.put("job_memory_limit_bytes", command.accounting().memoryLimitBytes()); value.put("job_limit_flags", command.accounting().limitFlags());
        value.put("passed", command.passed()); value.put("stop_reason", command.stopReason());
        value.set("stdout_log", logObservation(outcome.stdout()));
        value.set("stderr_log", logObservation(outcome.stderr()));
        SavedProofFiles.publish(ticket.outputRoot().resolve("sdk-" + ticket.nonce() + ".terminal.json"), StrictJson.canonical(value));
    }

    /** A log failure never hides the independently observed Job terminal state. */
    static ObjectNode logObservation(Path path) {
        ObjectNode value = StrictJson.object(); value.put("path", path.toString());
        value.putNull("bytes"); value.putNull("sha256"); value.putNull("error");
        try {
            BasicFileAttributes attributes = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            StrictJson.require(attributes.isRegularFile() && !attributes.isSymbolicLink(), "ordinary non-reparse managed log");
            value.put("bytes", attributes.size());
            if (attributes.size() > 65_536) { value.put("status", "OVER_CAP_NOT_READ"); }
            else {
                byte[] bytes = SavedProofFiles.read(path, 65_536);
                value.put("bytes", bytes.length); value.put("sha256", RecoveryEvidence.sha256(bytes));
                value.put("status", "EXACT_BOUNDED");
            }
        } catch (IOException | ContractViolationException error) {
            value.put("status", "UNAVAILABLE_NOT_READ"); value.putNull("bytes"); value.putNull("sha256");
            String message = error.getClass().getSimpleName() + ": " + error.getMessage();
            value.put("error", message.substring(0, Math.min(message.length(), 2048)));
        }
        return value;
    }
}

