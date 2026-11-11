package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.util.Optional;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartTicket;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.platform.GameSupervisorControl;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeGameAttachment;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.OrdinarySessionResource;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeAssembly.Opened;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeAssembly.Prepared;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeAssembly.Running;

/** Ordinary business worker. The separate supervisor retains the physical Game Job. */
@QuarkusMain(name = "ordinary-worker")
public final class RootOrdinaryWorkerMain implements QuarkusApplication {
    public static void main(String... args) throws Exception {
        System.exit(new RootOrdinaryWorkerMain().run(args));
    }

    @Override public int run(String... args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("ordinary-worker requires owner.json, business configuration, and fresh|resume|current-map|operator-quarantine");
        String mode = args[2];
        if (!"fresh".equals(mode) && !"resume".equals(mode) && !"current-map".equals(mode) && !"operator-quarantine".equals(mode)) throw new IllegalArgumentException("ordinary-worker mode must be fresh, resume, current-map or operator-quarantine");
        Clock clock = Clock.systemUTC();
        RootOrdinaryRuntimeConfiguration config = RootOrdinaryRuntimeConfiguration.read(Path.of(args[1]));
        var descriptor = GameSupervisorControl.readDescriptor(Path.of(args[0]));
        NativeLaunchPlan plan = descriptor.configuration().accept();
        Path ticketPath = config.stateDirectory().resolve("worker-restart-ticket.json");
        Prepared prepared = null;
        Opened opened = null;
        Running running = null;
        ManagedGameSession attached = null;
        RootOrdinaryWorkerLoop.Result result = null;
        Exception primary = null;
        try {
            prepared = RootOrdinaryRuntimeAssembly.prepare(config, clock);
            attached = NativeGameAttachment.attach(new NativeGameAttachment.Request(plan, descriptor.generation(),
                    prepared.privatePermissions(), config.maximumFramesPerOperation(), config.maximumSubmissions()),
                    clock.instant().plus(config.operationTimeout()), config.operationTimeout());
            var ack = RootNativeFreshStartup.observeBootstrapCore(attached, clock, clock.instant().plus(config.operationTimeout()));
            var frame = RootNativeFreshStartup.decodeCore(ack.originalResultToken().orElseThrow());
            var mapReady = RootNativeFreshStartup.isMapReady(frame);
            if (("current-map".equals(mode) || "operator-quarantine".equals(mode)) && !mapReady)
                throw new IOException("current-map requires an actual ready map; new campaign startup is not permitted");
            if ("operator-quarantine".equals(mode)) {
                running = prepared.openOperatorQuarantineRecovery(attached, clock.instant().plus(config.operationTimeout()));
            } else if ("resume".equals(mode)) {
                Optional<CleanRestartTicket> pointer = Files.exists(ticketPath) ? Optional.of(readTicket(ticketPath)) : Optional.empty();
                running = prepared.openExistingSameGameRecovery(attached, pointer, clock.instant().plus(config.operationTimeout()));
            } else if (mapReady) {
                Optional<CleanRestartTicket> pointer = Files.exists(ticketPath) ? Optional.of(readTicket(ticketPath)) : Optional.empty();
                running = prepared.openSameGameBootstrap(attached, pointer, clock.instant().plus(config.operationTimeout()));
            } else {
                opened = prepared.open(attached);
                var dayZero = RootNativeFreshStartup.startFreshRobert(attached, plan, prepared.initialPolicy().kind(),
                        prepared.initialPolicy().lifecycle(), clock, clock.instant().plus(plan.startupTimeout()));
                running = opened.finishFresh(dayZero.startAck(), dayZero.read(), dayZero.produced(), clock.instant().plus(config.operationTimeout()));
            }
            var schedulingController = running.core().sessionAccess().current().controllerForPublication();
            var importedLifeHint = readLifeBudgetHint(config.stateDirectory().resolve("worker-batches.jsonl"), schedulingController.identity());
            boolean restoredLifeHint = importedLifeHint.filter(schedulingController::restoreLifeBudgetHint).isPresent();
            var schedulingHints = new java.util.concurrent.atomic.AtomicReference<Optional<org.xar.ck3.control.application.action.RawJson>>(
                    restoredLifeHint ? importedLifeHint : Optional.empty());
            ObjectNode initial = event(clock, "ORDINARY_WORKER_LOOP_START");
            initial.put("life_budget_hint_status", restoredLifeHint ? "restored" : "not_available");
            initial.set("game", attached.generation().toJson());
            initial.put("next_sequence", Long.toString(running.nextBatchSequence()));
            initial.put("ordinary_batch_started", false);
            emit(initial);
            var bounds = config.loop();
            var actualLoop = new RootOrdinaryWorkerLoop.Configuration(running.batchPrefix(), bounds.maximumTurns(),
                    bounds.wallTime(), bounds.readinessTimeout(), bounds.pollInterval(), bounds.checkpointEveryEligibleAdvances());
            var warmRunning = running;
            var control = new RootOrdinaryWorkerLoop.Control() {
                @Override public boolean stopRequested() { return Files.exists(config.stopPath()); }
                @Override public void onBatchCompleted(BatchReport actual, long nextSequence) throws IOException {
                    var hint = org.xar.ck3.control.application.session.SessionController.retainLifeBudgetHint(actual, schedulingHints.get());
                    schedulingHints.set(hint);
                    recordBatch(config, clock, actual, nextSequence, hint);
                }
                @Override public boolean captureCleanPlanningWall(BatchReport actual,long nextSequence)
                        throws IOException,InterruptedException {
                    var current=warmRunning.core().sessionAccess().current();
                    var captured=current.captureCleanPlanningWall(warmRunning.batchPrefix(),nextSequence,actual,
                            clock.instant().plus(config.operationTimeout()));
                    if(captured.isEmpty())return false;
                    writeTicket(ticketPath,captured.orElseThrow());
                    ObjectNode warm=event(clock,"CLEAN_UNISSUED_PLANNING_WARM_BATCH");
                    warm.set("game",current.identity().game().toJson());
                    warm.put("batch_id",actual.batchId());warm.put("next_sequence",Long.toString(nextSequence));
                    warm.put("capture_sequence",Long.toString(captured.orElseThrow().sequence()));
                    warm.put("saved_day_credit",0);warm.put("gameplay_credit",false);
                    emit(warm);return true;
                }
            };
            result = new RootOrdinaryWorkerLoop(actualLoop, control).run(running.core().sessionAccess(), running.nextBatchSequence());
            
            boolean isFailureStop = classifyFailureStop(result);
            if (!isFailureStop) {
                var controller = running.core().sessionAccess().current().controllerForPublication();
                isFailureStop = controller.isQuarantined() || controller.isRetired();
            }
            
            if (isFailureStop) {
                ObjectNode failedEvent = event(clock, "WORKER_TERMINAL_FAILURE");
                failedEvent.set("game", attached.generation().toJson());
                failedEvent.put("loop_terminal", result.stopReason().name());
                failedEvent.put("next_sequence", Long.toString(result.nextBatchSequence()));
                result.failureDetail().ifPresent(detail -> failedEvent.put("loop_detail", detail));
                result.lastReport().ifPresent(actual -> {
                    failedEvent.put("last_batch_terminal", actual.terminal().name());
                    failedEvent.put("last_batch_detail", actual.detail());
                });
                failedEvent.put("pause_status", "NOT_ATTEMPTED");
                failedEvent.put("game_stop_requested", false);
                emit(failedEvent);
                return 4;
            }

            // The real capture owns the clean/pending decision and drains actual offline work. Dirty is preserved.
            var currentRunning = running;
            var currentResult = result;
            var captured = captureForStop(currentResult, () -> currentRunning.core().sessionAccess().current().captureCleanRestart(
                    currentRunning.batchPrefix(), currentResult.nextBatchSequence(), clock.instant().plus(config.operationTimeout())));
            if (captured.isEmpty()) {
                ObjectNode deferred = event(clock, "WORKER_RESTART_CAPTURE_DEFERRED");
                deferred.set("game", attached.generation().toJson());
                deferred.put("next_sequence", Long.toString(result.nextBatchSequence()));
                deferred.put("loop_terminal", result.stopReason().name());
                deferred.put("capture_reason", "missing_complete_driver_observation");
                result.lastReport().ifPresent(actual -> {
                    deferred.put("last_batch_terminal", actual.terminal().name());
                    deferred.put("last_batch_detail", actual.detail());
                });
                deferred.put("pause_status", "NOT_ATTEMPTED");
                deferred.put("game_stop_requested", false);
                emit(deferred);
                return 0;
            }
            writeTicket(ticketPath, captured.orElseThrow());
            ObjectNode completed = event(clock, "CLEAN_WORKER_RESTART_CAPTURED");
            completed.set("game", attached.generation().toJson());
            completed.put("ticket_path", ticketPath.toString());
            completed.put("next_sequence", Long.toString(result.nextBatchSequence()));
            completed.put("loop_terminal", result.stopReason().name());
            if (result.stopReason() == RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS) {
                completed.put("no_progress_reason", result.lastReport().filter(report -> report.terminal() == BatchReport.Terminal.WALL_TIMEOUT)
                        .map(report -> "wall_timeout_without_dispatch").orElse("turn_bound_without_progress"));
                var stoppedReport = result.lastReport();
                running.core().sessionAccess().current().controllerForPublication().lastBatchBoundary()
                        .filter(boundary -> stoppedReport.filter(report -> report.batchId().equals(boundary.batchId())).isPresent())
                        .ifPresent(boundary -> {
                            completed.put("actual_observation_count", boundary.observationCount());
                            completed.put("date_progress_observation", boundary.observationCount() < 2 ? "unknown" : "no_change_observed");
                            boundary.firstObservation().ifPresent(observed -> completed.put("first_observed_date_raw", observed.frame().identity().dateRaw().toString()));
                            boundary.lastObservation().ifPresent(observed -> completed.put("last_observed_date_raw", observed.frame().identity().dateRaw().toString()));
                        });
            }
            result.failureDetail().ifPresent(detail -> completed.put("loop_detail", detail));
            result.lastReport().ifPresent(actual -> {
                completed.put("last_batch_terminal", actual.terminal().name());
                completed.put("last_batch_detail", actual.detail());
            });
            completed.put("pause_status", "NOT_ATTEMPTED");
            completed.put("game_stop_requested", false);
            emit(completed);
            return result.stopReason() == RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP ? 0 : 4;
        } catch (Exception failed) {
            primary = failed;
            if (failed instanceof InterruptedException) Thread.currentThread().interrupt();
            ObjectNode diagnostic = event(clock, "WORKER_FAILED");
            diagnostic.put("exception_type", failed.getClass().getName());
            diagnostic.put("detail", failed.toString());
            diagnostic.put("pause_status", "NOT_ATTEMPTED");
            diagnostic.put("game_stop_requested", false);
            if (attached != null) diagnostic.set("game", attached.generation().toJson());
            if (result != null) {
                diagnostic.put("loop_terminal", result.stopReason().name());
                diagnostic.put("next_sequence", Long.toString(result.nextBatchSequence()));
                result.failureDetail().ifPresent(detail -> diagnostic.put("loop_detail", detail));
                result.lastReport().ifPresent(actual -> diagnostic.put("last_batch_terminal", actual.terminal().name()));
            }
            try { emit(diagnostic); }
            catch (IOException outputFailure) { failed.addSuppressed(outputFailure); }
            throw failed;
        } finally {
            closeResources(primary, running, opened, prepared, attached);
        }
    }

    @FunctionalInterface interface RestartCapture {
        CleanRestartTicket capture() throws IOException, InterruptedException;
    }

    /** Only this typed absence during an already benign cooperative stop defers a capture. */
    static Optional<CleanRestartTicket> captureForStop(RootOrdinaryWorkerLoop.Result result, RestartCapture capture)
            throws IOException, InterruptedException {
        try {
            return Optional.of(capture.capture());
        } catch (OrdinaryCycleTransitions.MissingDriverObservation missing) {
            if (result.stopReason() != RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP || classifyFailureStop(result))
                throw missing;
            return Optional.empty();
        }
    }

    static boolean classifyFailureStop(RootOrdinaryWorkerLoop.Result result) {
        if (result.stopReason() == RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP) {
            if (result.failureDetail().isPresent()) return true;
            if (result.lastReport().isPresent()) {
                var terminal = result.lastReport().get().terminal();
                if (terminal == BatchReport.Terminal.CHECKPOINT_DEFERRED) return false;
            }
        }
        return (result.stopReason() != RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP
                && result.stopReason() != RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS)
                || result.failureDetail().isPresent()
                || result.lastReport().filter(actual -> switch (actual.terminal()) {
                    case TURN_BOUND, OPERATOR_STOP, WALL_TIMEOUT, EPISODE_HANDOFF -> false;
                    default -> true;
                }).isPresent();
    }

    private static CleanRestartTicket readTicket(Path path) throws IOException {
        byte[] bytes;
        try (var stream = Files.newInputStream(path)) {
            bytes = stream.readNBytes(StrictJson.EXPLICIT_MAX_BYTES + 1);
        }
        if (bytes.length > StrictJson.EXPLICIT_MAX_BYTES) throw new IOException("Worker restart ticket exceeds its JSON byte bound: " + path);
        try {
            return CleanRestartTicket.decode(bytes);
        } catch (IllegalArgumentException invalid) {
            throw new IOException("Invalid worker restart ticket: " + path, invalid);
        }
    }

    /** Only replaces the small pointer after actual canonical capture; never removes the previous pointer first. */
    private static void writeTicket(Path path, CleanRestartTicket ticket) throws IOException {
        Path target = path.toAbsolutePath().normalize();
        Path parent = target.getParent();
        Files.createDirectories(parent);
        byte[] bytes = ticket.encode();
        Path pending = Files.createTempFile(parent, "worker-restart-", ".pending");
        IOException original = null;
        boolean moved = false;
        try {
            try (var channel = FileChannel.open(pending, StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING)) {
                ByteBuffer buffer = ByteBuffer.wrap(bytes);
                while (buffer.hasRemaining()) channel.write(buffer);
                channel.force(true);
            }
            Files.move(pending, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            moved = true;
        } catch (IOException failed) {
            original = failed;
            throw failed;
        } finally {
            if (!moved) {
                try { Files.deleteIfExists(pending); }
                catch (IOException cleanup) {
                    if (original != null) original.addSuppressed(cleanup);
                    else throw cleanup;
                }
            }
        }
    }

    /** Bounded optional telemetry snapshot. No original, ticket, Driver or Game is opened here. */
    static Optional<org.xar.ck3.control.application.action.RawJson> readLifeBudgetHint(Path path,
            org.xar.ck3.control.application.session.SessionPorts.SessionIdentity owner) {
        final int maximum = 1_048_576;
        try (var channel = FileChannel.open(path, StandardOpenOption.READ)) {
            long end = channel.size(), start = Math.max(0, end - maximum);
            var data = ByteBuffer.allocate((int) (end - start)); channel.position(start);
            while (data.hasRemaining()) { int count = channel.read(data); if (count <= 0) break; }
            byte[] bytes = data.array(); int size = data.position(), first = 0;
            if (start > 0) { while (first < size && bytes[first] != 10) first++; first++; }
            int last = size - 1; while (last >= first && bytes[last] != 10) last--;
            for (int records = 0; last >= first && records < 64; records++) {
                int previous = last - 1; while (previous >= first && bytes[previous] != 10) previous--;
                int beginning = previous + 1;
                if (last > beginning) {
                    try {
                        var parsed = FullJsonTree.parse(java.util.Arrays.copyOfRange(bytes, beginning, last), maximum);
                        if (parsed instanceof ObjectNode row) {
                            var hint = lifeBudgetHintFromReport(row, owner);
                            if (hint.isPresent()) return hint;
                        }
                    } catch (IllegalArgumentException unavailable) { /* A partial/bad optional line grants no metric. */ }
                }
                last = previous;
            }
        } catch (IOException | IllegalArgumentException unavailable) { /* Missing or unreadable optional history preserves the old fallback. */ }
        return Optional.empty();
    }

    static Optional<org.xar.ck3.control.application.action.RawJson> lifeBudgetHintFromReport(ObjectNode row,
            org.xar.ck3.control.application.session.SessionPorts.SessionIdentity owner) {
        try {
            if (!"xar.ordinary-session-batch-result/v1".equals(StrictJson.text(row.get("schema")))
                    || !owner.machineId().equals(StrictJson.text(row.get("machine_id")))
                    || owner.game().pid() != StrictJson.integer(row.get("game_pid"), 1, 4_294_967_295L)
                    || !owner.game().creationFiletime().value().toString().equals(StrictJson.text(row.get("game_creation_filetime")))
                    || !owner.sessionId().equals(StrictJson.text(row.get("session_id")))) return Optional.empty();
            var pair = org.xar.ck3.control.application.checkpoint.CheckpointPairCodec.decode(FullJsonTree.encode(row.get("last_saved_pair"), 65_536));
            ObjectNode hint;
            if (row.hasNonNull("life_budget_hint")) {
                var fields = java.util.Set.of("schema", "owner", "subject", "saved_life_tail_nanos", "reserve_floor_nanos");
                hint = StrictJson.object(row.get("life_budget_hint"), fields, fields);
                if (!"xar.life-budget-hint/v1".equals(StrictJson.text(hint.get("schema")))
                        || !owner.equals(OrdinaryCycleTransitions.sessionFromJson(hint.get("owner")))) return Optional.empty();
                long tail = lifeHintNanos(hint.get("saved_life_tail_nanos")), floor = lifeHintNanos(hint.get("reserve_floor_nanos"));
                if (tail == 0 && floor == 0) return Optional.empty();
            } else {
                if (!"WALL_TIMEOUT".equals(StrictJson.text(row.get("terminal"))) || !row.get("dirty_since_save").isBoolean()
                        || row.get("dirty_since_save").booleanValue()) return Optional.empty();
                for (String name : java.util.List.of("attempted_turns", "original_action_reconciliation_count", "zero_dispatch_revision_replan_count",
                        "lifecycle_turn_count", "reported_action_tail_count", "committed_saved_days", "eligible_advances_since_save"))
                    if (StrictJson.integer(row.get(name), 0, StrictJson.MAX_SAFE_INTEGER) != 0) return Optional.empty();
                for (String name : java.util.List.of("last_actions", "last_original_action_reconciliations", "last_lifecycle_turns", "last_read_publication_reconciliations"))
                    if (row.get(name) == null || !row.get(name).isArray() || !row.get(name).isEmpty()) return Optional.empty();
                String detail = StrictJson.text(row.get("detail"));
                String prefix = "PRE_INTENT_LIFE_BUDGET_DEFERRED: remaining_nanos=", middle = "; reserve_nanos=",
                        suffix = "; no action INTENT submitted; next batch must freshly observe and plan";
                int split = detail.indexOf(middle, prefix.length());
                if (detail.length() > 1024 || !detail.startsWith(prefix) || !detail.endsWith(suffix) || split < 0) return Optional.empty();
                String remainingText = detail.substring(prefix.length(), split);
                if (!remainingText.matches("0|-?[1-9][0-9]{0,18}")) return Optional.empty();
                long remaining = Long.parseLong(remainingText);
                long reserve = lifeHintNanos(StrictJson.object().put("value", detail.substring(split + middle.length(), detail.length() - suffix.length())).get("value"));
                if (reserve <= 0 || remaining >= reserve) return Optional.empty();
                var plan = StrictJson.object(row.get("last_plan"), java.util.Set.of("before", "visits", "final_plan"));
                var command = org.xar.ck3.control.application.action.ActionCodec.decodeCommand(FullJsonTree.encode(plan.get("final_plan").get("command"), 1_048_576));
                var subject = org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(plan.get("before"));
                if (!(command.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay)
                        || !org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(command.operation().value())
                        || !command.before().equals(subject) || !command.sessionId().equals(owner.sessionId())) return Optional.empty();
                hint = StrictJson.object(); hint.put("schema", "xar.life-budget-hint/v1"); hint.set("owner", OrdinaryCycleTransitions.sessionToJson(owner));
                hint.set("subject", org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(subject));
                hint.put("saved_life_tail_nanos", "0"); hint.put("reserve_floor_nanos", Long.toString(reserve));
            }
            var subject = org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(hint.get("subject"));
            var anchor = pair.frame();
            if (!subject.machineId().equals(owner.machineId()) || !subject.game().equals(owner.game())
                    || !anchor.machineId().equals(owner.machineId()) || !anchor.game().equals(owner.game())
                    || !subject.frame().episodeRunId().equals(anchor.frame().episodeRunId())
                    || !subject.frame().identity().player().equals(anchor.frame().identity().player())
                    || subject.frame().identity().dateRaw().compareTo(anchor.frame().identity().dateRaw()) > 0) return Optional.empty();
            return Optional.of(new org.xar.ck3.control.application.action.RawJson(StrictJson.canonical(hint, 16_384)));
        } catch (IllegalArgumentException | NullPointerException | java.time.DateTimeException unavailable) { return Optional.empty(); }
    }

    private static long lifeHintNanos(com.fasterxml.jackson.databind.JsonNode value) {
        String text = StrictJson.text(value); StrictJson.require(text.matches("0|[1-9][0-9]{0,18}"), "canonical scheduling nanoseconds required");
        long nanos = Long.parseLong(text); StrictJson.require(nanos <= java.time.Duration.ofDays(1).toNanos(), "bounded scheduling telemetry required"); return nanos;
    }

    private static void recordBatch(RootOrdinaryRuntimeConfiguration config, Clock clock,
            BatchReport actual, long nextSequence, Optional<org.xar.ck3.control.application.action.RawJson> lifeHint) throws IOException {
        ObjectNode row = OrdinarySessionResource.report(actual);
        lifeHint.ifPresent(hint -> row.set("life_budget_hint", StrictJson.parse(hint.bytes(), 16_384)));
        row.put("observed_at_utc", clock.instant().toString());
        row.put("next_sequence", Long.toString(nextSequence));
        byte[] body = FullJsonTree.encode(row, FullJsonTree.MAXIMUM_BYTES);
        byte[] line = java.util.Arrays.copyOf(body, body.length + 1);
        line[body.length] = 10;
        Files.createDirectories(config.stateDirectory());
        Files.write(config.stateDirectory().resolve("worker-batches.jsonl"), line,
                StandardOpenOption.CREATE, StandardOpenOption.WRITE, StandardOpenOption.APPEND);
        emit(body);
    }

    private static ObjectNode event(Clock clock, String status) {
        return StrictJson.object().put("schema", "xar.java-ordinary-worker-result/v1")
                .put("machine_id", WindowsJobProcess.currentMachineId())
                .put("observed_at_utc", clock.instant().toString()).put("status", status);
    }

    private static void emit(ObjectNode row) throws IOException {
        emit(StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES));
    }

    private static void emit(byte[] body) throws IOException {
        System.out.write(body);
        System.out.write(10);
        System.out.flush();
        if (System.out.checkError()) throw new IOException("Ordinary worker result stdout failed");
    }

    /** All sessions supplied here came from NativeGameAttachment; closing them releases only pipe/observer custody. */
    private static void closeResources(Exception primary, Running running, Opened opened,
            Prepared prepared, ManagedGameSession attached) throws IOException {
        IOException failure = null;
        failure = closeOne(running, failure);
        failure = closeOne(opened, failure);
        failure = closeOne(prepared, failure);
        failure = closeOne(attached, failure);
        if (failure != null) {
            if (primary != null) {
                if (primary != failure) primary.addSuppressed(failure);
            }
            else throw failure;
        }
    }

    private static IOException closeOne(AutoCloseable resource, IOException previous) {
        if (resource == null) return previous;
        try { resource.close(); }
        catch (Exception failed) {
            IOException actual = failed instanceof IOException io ? io
                    : new IOException("Ordinary worker resource close failed: " + resource.getClass().getName(), failed);
            if (previous == null) return actual;
            if (previous != actual) previous.addSuppressed(actual);
        }
        return previous;
    }
}
