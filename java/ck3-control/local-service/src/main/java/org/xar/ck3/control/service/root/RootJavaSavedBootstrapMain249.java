package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Clock;
import java.time.Duration;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SavedGameOwnerLifetime249;
import org.xar.ck3.control.service.OrdinarySessionResource;

/** Same creator owns the real Saved launch, private admission and retained Game lifetime. */
public final class RootJavaSavedBootstrapMain249 {
    private static final int MAX = 1 << 20;
    private RootJavaSavedBootstrapMain249() { }

    public static void main(String... args) throws Exception { System.exit(run(args)); }

    public static int run(String... args) throws Exception {
        if (args.length != 6) throw new IOException("expected Saved owner-plan exact3 and cold business request exact3");
        Clock clock = Clock.systemUTC();
        ExactRef ownerPlanRef = argument(args, 0), requestRef = argument(args, 3);
        byte[] ownerPlanRaw = read(ownerPlanRef), requestRaw = read(requestRef);
        ObjectNode request = StrictJson.object(StrictJson.parse(requestRaw, MAX), Set.of("schema", "machineId",
                "sourceRuntimeConfiguration", "newRuntimeConfiguration", "sourceConfirmation", "checkpointPair", "ownerDirectory"));
        StrictJson.require("xar.java-confirmed-saved-cold-request/v1".equals(StrictJson.text(request.get("schema"))), "cold Saved request schema required");
        String machine = StrictJson.text(request.get("machineId"));
        ExactRef oldConfigRef = ExactRef.fromJson(request.get("sourceRuntimeConfiguration"));
        ExactRef newConfigRef = ExactRef.fromJson(request.get("newRuntimeConfiguration"));
        ExactRef confirmationRef = ExactRef.fromJson(request.get("sourceConfirmation"));
        ExactRef pairRef = ExactRef.fromJson(request.get("checkpointPair"));
        byte[] oldConfigRaw = read(oldConfigRef), newConfigRaw = read(newConfigRef);
        var oldConfig = RootOrdinaryRuntimeConfiguration.read(Path.of(oldConfigRef.path()));
        var newConfig = RootOrdinaryRuntimeConfiguration.read(Path.of(newConfigRef.path()));
        StrictJson.require(Arrays.equals(oldConfigRaw, read(oldConfigRef)) && Arrays.equals(newConfigRaw, read(newConfigRef)), "cold runtime configuration changed while decoded");
        StrictJson.require(machine.equals(oldConfig.machineId()) && machine.equals(newConfig.machineId()), "cold source/new runtime machine differs");
        Path oldRoot = oldConfig.stateDirectory().getParent().toAbsolutePath().normalize();
        Path newRoot = newConfig.stateDirectory().getParent().toAbsolutePath().normalize();
        Path ownerDirectory = Path.of(StrictJson.text(request.get("ownerDirectory")));
        StrictJson.require(!newRoot.startsWith(oldRoot) && !oldRoot.startsWith(newRoot), "distinct independent old/new writer roots required");
        StrictJson.require(ownerDirectory.isAbsolute() && ownerDirectory.normalize().equals(ownerDirectory)
                && !ownerDirectory.startsWith(oldRoot) && Files.notExists(ownerDirectory)
                && Files.isDirectory(ownerDirectory.getParent()), "fresh independent owner directory with existing parent required");
        StrictJson.require(Files.isRegularFile(oldRoot.resolve("continuity/continuity.json"))
                && Files.isRegularFile(oldRoot.resolve("continuity/genesis-anchor.json"))
                && Files.isDirectory(oldRoot.resolve("continuity/ROOT-CONTINUITY-WINDOW-EVENTS")), "existing old canonical source required; no fresh fallback");
        StrictJson.require(newConfig.launchPlanFile().toAbsolutePath().normalize().equals(Path.of(ownerPlanRef.path()).toAbsolutePath().normalize()), "new runtime must consume the exact owner plan");
        var ownerPlan = NativeLaunchPlanCodec.read(Path.of(ownerPlanRef.path()));
        StrictJson.require(Arrays.equals(ownerPlanRaw, read(ownerPlanRef)), "owner plan changed while decoded");
        var pair = CheckpointPairCodec.decode(read(pairRef));
        read(confirmationRef);
        RootOrdinaryRuntimeAssembly.Prepared oldPrepared = null, newPrepared = null;
        RootOrdinaryRuntimeAssembly.Running running = null;
        SavedGameOwnerLifetime249.Retained lifetime = null;
        JavaGameLifecycle.Started originalStarted = null;
        Exception failure = null;
        int result = 1;
        try {
            oldPrepared = RootOrdinaryRuntimeAssembly.prepare(oldConfig, clock);
            var oldCore = oldPrepared.openSavedSourceCore();
            var confirmation = oldCore.writer().locked(same -> {
                var head = same.head();
                StrictJson.require(!head.snapshotNeedsRecovery() && head.indexRepairs().isEmpty(), "old source requires explicit canonical repair");
                var matches = head.documents().stream().filter(pin ->
                        Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(Path.of(confirmationRef.path()).toAbsolutePath().normalize())
                        && pin.reference().bytes() == confirmationRef.bytes() && pin.reference().sha256().equals(confirmationRef.sha256())).toList();
                StrictJson.require(matches.size() == 1, "unique actual canonical confirmation Pin required");
                var captured = same.capturePin(matches.getFirst().reference(), MAX);
                StrictJson.require(captured.equals(matches.getFirst()), "original confirmation identity changed");
                return captured;
            });
            var source = RootJavaSavedBootstrap.qualify(oldCore, new NativeCheckpointFiles(),
                    oldConfig.stateDirectory().resolve("checkpoints/attachments"), oldPrepared.plan().pipeName(), pair, confirmation);
            emit(event(clock, "CONFIRMED_SAVED_SOURCE_QUALIFIED").put("source_head_sequence", source.sourceHead().sequence())
                    .put("confirmation_sequence", source.confirmation().sequence()).put("saved_date_raw", source.savedState().settledDateRaw())
                    .put("saved_cycles", source.savedState().settledCycles()).put("new_saved_day_credit", 0));
            newPrepared = RootOrdinaryRuntimeAssembly.prepareConfirmedSaved(newConfig, clock, source);
            StrictJson.require(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(newPrepared.plan()))
                    .equals(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(ownerPlan))), "actual Prepared plan differs from exact owner plan");
            StrictJson.require(newPrepared.plan().load() instanceof NativeLaunchPlan.SavedGame saved
                    && new ExactRef(saved.save().path(), saved.save().bytes(), saved.save().sha256()).equals(pair.save().reference()), "actual Saved plan must load the confirmed exact SAVE");
            read(ownerPlanRef); read(requestRef); read(oldConfigRef); read(newConfigRef); read(pairRef); read(confirmationRef);
            var creator = newPrepared.lifecycle();
            var launched = creator.launchSaved(newPrepared.plan());
            if (!(launched instanceof JavaGameLifecycle.Started started)) throw new IOException("actual Saved launch was not Started: " + launched);
            originalStarted = started;
            lifetime = SavedGameOwnerLifetime249.retain(creator, started, ownerDirectory);
            running = newPrepared.openConfirmedSaved(started, source, clock.instant().plus(Duration.ofMinutes(10)));
            ObjectNode initial = event(clock, "ORDINARY_WORKER_LOOP_START");
            initial.set("game", started.session().generation().toJson());
            initial.put("next_sequence", Long.toString(running.nextBatchSequence()));
            initial.put("ordinary_batch_started", false); emit(initial);
            var bounds = newConfig.loop();
            var loopConfig = new RootOrdinaryWorkerLoop.Configuration(running.batchPrefix(), bounds.maximumTurns(), bounds.wallTime(),
                    bounds.readinessTimeout(), bounds.pollInterval(), bounds.checkpointEveryEligibleAdvances());
            var control = new RootOrdinaryWorkerLoop.Control() {
                @Override public boolean stopRequested() { return Files.exists(newConfig.stopPath()); }
                @Override public void onBatchCompleted(BatchReport actual, long next) throws IOException { recordBatch(newConfig, clock, actual, next); }
            };
            var terminal = new RootOrdinaryWorkerLoop(loopConfig, control).run(running.core().sessionAccess(), running.nextBatchSequence());
            result = RootOrdinaryWorkerMain.classifyFailureStop(terminal) ? 4 : 0;
            ObjectNode ended = event(clock, "SAVED_DAEMON_BUSINESS_END");
            ended.put("loop_terminal", terminal.stopReason().name()); ended.put("next_sequence", Long.toString(terminal.nextBatchSequence()));
            ended.put("business_exit_code", result); ended.put("game_stop_requested", false);
            terminal.failureDetail().ifPresent(value -> ended.put("loop_detail", value)); emit(ended);
        } catch (Exception actual) {
            failure = actual;
            ObjectNode failed = event(clock, "SAVED_DAEMON_BUSINESS_FAILED");
            failed.put("exception_type", actual.getClass().getName()); failed.put("detail", actual.toString());
            failed.put("game_stop_requested", false);
            try { emit(failed); } catch (IOException output) { actual.addSuppressed(output); }
        } finally {
            // Release only the ended business endpoint; retain the original Game Job until its owner exits.
            if (lifetime != null) {
                boolean endpointReleased = false;
                try { Objects.requireNonNull(originalStarted).session().nativeTransport().close(); endpointReleased = true; }
                catch (Exception release) { failure = merge(failure, release); }
                try {
                    emit(event(clock, "SAVED_DAEMON_ENDPOINT_RELEASE")
                            .put("endpoint_release", endpointReleased ? "RELEASED" : "FAILED")
                            .put("game_stop_requested", false));
                } catch (IOException output) { failure = merge(failure, output); }
                try { lifetime.awaitExit(); }
                catch (Exception awaiting) { failure = merge(failure, awaiting); }
            }
            failure = close(running, failure);
            failure = close(newPrepared, failure);
            failure = close(oldPrepared, failure);
        }
        if (failure != null) throw failure;
        return result;
    }

    private static ExactRef argument(String[] args, int offset) throws IOException {
        long length;
        try { length = Long.parseLong(args[offset + 1]); } catch (NumberFormatException invalid) { throw new IOException("canonical finite length required", invalid); }
        if (length < 1 || length > MAX || !Long.toString(length).equals(args[offset + 1])) throw new IOException("finite exact source length required");
        return new ExactRef(args[offset], length, args[offset + 2]);
    }
    private static byte[] read(ExactRef ref) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > MAX) throw new IOException("bounded cold source reference required");
        Path path = Path.of(ref.path()); BasicFileAttributes before = Files.readAttributes(path, BasicFileAttributes.class);
        if (!before.isRegularFile() || before.size() != ref.bytes()) throw new IOException("exact source size differs");
        byte[] raw; try (var input = Files.newInputStream(path)) { raw = input.readNBytes(MAX + 1); }
        var after = Files.readAttributes(path, BasicFileAttributes.class);
        if (raw.length != ref.bytes() || before.size() != after.size() || !before.lastModifiedTime().equals(after.lastModifiedTime())
                || !Objects.equals(before.fileKey(), after.fileKey()) || !DriverJson.sha256(raw).equals(ref.sha256())) throw new IOException("cold source bytes/hash/identity changed");
        return raw;
    }
    private static void recordBatch(RootOrdinaryRuntimeConfiguration config, Clock clock, BatchReport actual, long next) throws IOException {
        ObjectNode row = OrdinarySessionResource.report(actual);
        row.put("observed_at_utc", clock.instant().toString()); row.put("next_sequence", Long.toString(next));
        byte[] raw = FullJsonTree.encode(row, FullJsonTree.MAXIMUM_BYTES), line = Arrays.copyOf(raw, raw.length + 1);
        line[raw.length] = 10;
        Files.write(config.stateDirectory().resolve("worker-batches.jsonl"), line, StandardOpenOption.CREATE, StandardOpenOption.WRITE, StandardOpenOption.APPEND);
        emit(raw);
    }
    private static ObjectNode event(Clock clock, String status) {
        return StrictJson.object().put("schema", "xar.java-confirmed-saved-daemon-result/v1").put("observed_at_utc", clock.instant().toString()).put("status", status);
    }
    private static void emit(ObjectNode row) throws IOException { emit(StrictJson.canonical(row, MAX)); }
    private static void emit(byte[] raw) throws IOException {
        System.out.write(raw); System.out.write(10); System.out.flush();
        if (System.out.checkError()) throw new IOException("saved daemon output failed");
    }
    private static Exception close(AutoCloseable resource, Exception primary) {
        if (resource != null) try { resource.close(); } catch (Exception cleanup) { return merge(primary, cleanup); }
        return primary;
    }
    private static Exception merge(Exception primary, Exception next) {
        if (primary == null) return next;
        if (primary != next) primary.addSuppressed(next);
        return primary;
    }
}
