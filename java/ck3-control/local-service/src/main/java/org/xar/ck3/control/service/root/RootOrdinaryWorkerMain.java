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
import org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartTicket;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
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
        if (args.length != 3) throw new IllegalArgumentException("ordinary-worker requires owner.json, business configuration, and fresh|resume");
        String mode = args[2];
        if (!"fresh".equals(mode) && !"resume".equals(mode)) throw new IllegalArgumentException("ordinary-worker mode must be fresh or resume");
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
                    clock.instant().plus(config.operationTimeout()));
            var ack = RootNativeFreshStartup.observeBootstrapCore(attached, clock, clock.instant().plus(config.operationTimeout()));
            var frame = RootNativeFreshStartup.decodeCore(ack.originalResultToken().orElseThrow());
            var mapReady = RootNativeFreshStartup.isMapReady(frame);
            if (mapReady) {
                Optional<CleanRestartTicket> pointer = Files.exists(ticketPath) ? Optional.of(readTicket(ticketPath)) : Optional.empty();
                running = prepared.openSameGameBootstrap(attached, pointer, clock.instant().plus(config.operationTimeout()));
            } else if ("fresh".equals(mode)) {
                opened = prepared.open(attached);
                var dayZero = RootNativeFreshStartup.startFreshRobert(attached, plan, prepared.initialPolicy().kind(),
                        prepared.initialPolicy().lifecycle(), clock, clock.instant().plus(plan.startupTimeout()));
                running = opened.finishFresh(dayZero.startAck(), dayZero.read(), dayZero.produced(), clock.instant().plus(config.operationTimeout()));
            } else {
                var originalTicket = readTicket(ticketPath);
                running = prepared.openCleanRestart(attached, originalTicket, clock.instant().plus(config.operationTimeout()));
            }
            ObjectNode initial = event(clock, "ORDINARY_WORKER_LOOP_START");
            initial.set("game", attached.generation().toJson());
            initial.put("next_sequence", Long.toString(running.nextBatchSequence()));
            initial.put("ordinary_batch_started", false);
            emit(initial);
            var bounds = config.loop();
            var actualLoop = new RootOrdinaryWorkerLoop.Configuration(running.batchPrefix(), bounds.maximumTurns(),
                    bounds.wallTime(), bounds.readinessTimeout(), bounds.pollInterval(), bounds.checkpointEveryEligibleAdvances());
            var control = new RootOrdinaryWorkerLoop.Control() {
                @Override public boolean stopRequested() { return Files.exists(config.stopPath()); }
                @Override public void onBatchCompleted(BatchReport actual, long nextSequence) throws IOException {
                    recordBatch(config, clock, actual, nextSequence);
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
            CleanRestartTicket captured = running.core().sessionAccess().current().captureCleanRestart(
                    running.batchPrefix(), result.nextBatchSequence(), clock.instant().plus(config.operationTimeout()));
            writeTicket(ticketPath, captured);
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

    private static void recordBatch(RootOrdinaryRuntimeConfiguration config, Clock clock,
            BatchReport actual, long nextSequence) throws IOException {
        ObjectNode row = OrdinarySessionResource.report(actual);
        row.put("observed_at_utc", clock.instant().toString());
        row.put("next_sequence", Long.toString(nextSequence));
        byte[] body = StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES);
        byte[] line = java.util.Arrays.copyOf(body, body.length + 1);
        line[body.length] = 10;
        Files.createDirectories(config.stateDirectory());
        Files.write(config.stateDirectory().resolve("worker-batches.jsonl"), line,
                StandardOpenOption.CREATE, StandardOpenOption.WRITE, StandardOpenOption.APPEND);
        emit(row);
    }

    private static ObjectNode event(Clock clock, String status) {
        return StrictJson.object().put("schema", "xar.java-ordinary-worker-result/v1")
                .put("machine_id", WindowsJobProcess.currentMachineId())
                .put("observed_at_utc", clock.instant().toString()).put("status", status);
    }

    private static void emit(ObjectNode row) throws IOException {
        System.out.write(StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES));
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
