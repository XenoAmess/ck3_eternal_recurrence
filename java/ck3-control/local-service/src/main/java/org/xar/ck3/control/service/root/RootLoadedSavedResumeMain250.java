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
import org.xar.ck3.control.platform.GameSupervisorControl;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeGameAttachment;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.RootProcessAttach;
import org.xar.ck3.control.service.OrdinarySessionResource;

public final class RootLoadedSavedResumeMain250 {
    private static final int MAX = 1 << 20;
    private RootLoadedSavedResumeMain250() { }

    public static void main(String... args) {
        try { System.exit(run(args)); }
        catch (Exception failed) { reportFailure(failed); System.exit(1); }
    }

    public static int run(String... args) throws Exception {
        if (args.length != 6) throw new IOException("expected owner descriptor exact3 and resume request exact3");
        Clock clock = Clock.systemUTC();
        ExactRef ownerDescriptorRef = argument(args, 0), requestRef = argument(args, 3);
        byte[] ownerDescriptorRaw = read(ownerDescriptorRef), requestRaw = read(requestRef);
        var requestData=StrictJson.parse(requestRaw,MAX);
        int mode=requestMode(requestData);
        boolean passive=mode==2,preentry=mode==1||passive,originalRecovery=mode==3;
        ObjectNode request=(ObjectNode)requestData;
        String machine = StrictJson.text(request.get("machineId"));
        ExactRef oldConfigRef = ExactRef.fromJson(request.get("sourceRuntimeConfiguration"));
        ExactRef newConfigRef = ExactRef.fromJson(request.get("newRuntimeConfiguration"));
        ExactRef confirmationRef = ExactRef.fromJson(request.get("sourceConfirmation"));
        ExactRef pairRef = ExactRef.fromJson(request.get("checkpointPair"));
        Path ownerDirectory = Path.of(StrictJson.text(request.get("ownerDirectory")));
        byte[] oldConfigRaw = read(oldConfigRef), newConfigRaw = read(newConfigRef);
        var oldConfig = RootOrdinaryRuntimeConfiguration.read(Path.of(oldConfigRef.path()));
        var newConfig = RootOrdinaryRuntimeConfiguration.read(Path.of(newConfigRef.path()));
        StrictJson.require(Arrays.equals(oldConfigRaw, read(oldConfigRef)) && Arrays.equals(newConfigRaw, read(newConfigRef)), "cold runtime configuration changed while decoded");
        StrictJson.require(machine.equals(oldConfig.machineId()) && machine.equals(newConfig.machineId()), "cold source/new runtime machine differs");
        Path oldRoot = oldConfig.stateDirectory().getParent().toAbsolutePath().normalize();
        Path newRoot = newConfig.stateDirectory().getParent().toAbsolutePath().normalize();
        StrictJson.require(!newRoot.startsWith(oldRoot) && !oldRoot.startsWith(newRoot), "distinct independent old/new writer roots required");
        StrictJson.require(ownerDirectory.isAbsolute() && ownerDirectory.normalize().equals(ownerDirectory) && Files.isDirectory(ownerDirectory), "existing owner directory required");
        StrictJson.require(Files.isRegularFile(oldRoot.resolve("continuity/continuity.json")) && Files.isRegularFile(oldRoot.resolve("continuity/genesis-anchor.json")) && Files.isDirectory(oldRoot.resolve("continuity/ROOT-CONTINUITY-WINDOW-EVENTS")), "existing old canonical source required");
        var ownerDescriptor = GameSupervisorControl.readDescriptor(Path.of(ownerDescriptorRef.path()));
        StrictJson.require(Arrays.equals(ownerDescriptorRaw, read(ownerDescriptorRef)), "owner descriptor changed while decoded");
        StrictJson.require(ownerDirectory.equals(Path.of(ownerDescriptorRef.path()).toAbsolutePath().normalize().getParent())
                && machine.equals(ownerDescriptor.machineId()), "resume owner directory or actual machine differs");
        var pair = CheckpointPairCodec.decode(read(pairRef));
        read(confirmationRef);
        RootOrdinaryRuntimeAssembly.Prepared oldSourcePrepared = null, newPrepared = null;
        RootOrdinaryRuntimeAssembly.Running running = null;
        RootProcessAttach.LoadedCustody custody = null;
        ManagedGameSession attached = null;
        Exception failure = null;
        int result = 1;
        try {
            oldSourcePrepared = RootOrdinaryRuntimeAssembly.prepareReadOnlySavedSource(oldConfig, clock);
            var oldCore = oldSourcePrepared.openSavedSourceCore();
            var confirmation = oldCore.writer().locked(same -> {
                var head = same.head();
                StrictJson.require(!head.snapshotNeedsRecovery() && head.indexRepairs().isEmpty(), "old source requires explicit canonical repair");
                var matches = head.documents().stream().filter(pin -> Path.of(pin.reference().path()).toAbsolutePath().normalize().equals(Path.of(confirmationRef.path()).toAbsolutePath().normalize()) && pin.reference().bytes() == confirmationRef.bytes() && pin.reference().sha256().equals(confirmationRef.sha256())).toList();
                StrictJson.require(matches.size() == 1, "unique actual canonical confirmation Pin required");
                var captured = same.capturePin(matches.getFirst().reference(), MAX);
                StrictJson.require(captured.equals(matches.getFirst()), "original confirmation identity changed");
                return captured;
            });
            var source = RootJavaSavedBootstrap.qualify(oldCore, new NativeCheckpointFiles(), oldConfig.stateDirectory().resolve("checkpoints/attachments"), oldSourcePrepared.plan().pipeName(), pair, confirmation);
            emit(event(clock, "SOURCE_QUALIFIED").put("source_head_sequence", source.sourceHead().sequence()).put("confirmation_sequence", source.confirmation().sequence()).put("saved_date_raw", source.savedState().settledDateRaw()).put("saved_cycles", source.savedState().settledCycles()).put("new_saved_day_credit", 0));
            newPrepared = originalRecovery?RootOrdinaryRuntimeAssembly.prepareExistingLoadedSavedRecovery(newConfig,clock,source)
                    :preentry?RootOrdinaryRuntimeAssembly.prepareLoadedSaved(newConfig,clock,source)
                    :RootOrdinaryRuntimeAssembly.prepareRetainedLoadedSaved(newConfig, clock, source);
            StrictJson.require(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(newPrepared.plan())).equals(NativeLaunchPlanCodec.toJson(ownerDescriptor.configuration())), "actual Prepared plan differs from exact owner descriptor");
            read(ownerDescriptorRef); read(requestRef); read(oldConfigRef); read(newConfigRef); read(pairRef); read(confirmationRef);
            attached = NativeGameAttachment.attach(new NativeGameAttachment.Request(newPrepared.plan(), ownerDescriptor.generation(),
                    passive?java.util.List.of():newPrepared.privatePermissions(),
                    passive?1:newConfig.maximumFramesPerOperation(),passive?1:newConfig.maximumSubmissions()),
                    clock.instant().plus(passive?Duration.ofSeconds(30):newConfig.operationTimeout()),
                    passive?Duration.ofSeconds(10):newConfig.operationTimeout());
            emit(event(clock, "ACTUAL_ATTACHMENT").put("attached_pid", attached.identity().pid()).put("attached_session", attached.sessionId()));
            Path evidenceRoot = newPrepared.plan().evidenceRoot().resolve("loaded-saved-" + java.util.UUID.randomUUID());
            custody = RootProcessAttach.retainLoadedSaved(attached, ownerDescriptorRef, pair, evidenceRoot,
                    clock.instant().plus(passive?Duration.ofSeconds(30):Duration.ofMinutes(10)));
            emit(event(clock, "LOADED_CUSTODY_QUALIFIED").put("custody_evidence", custody.evidence().path()));
            if(passive) {
                result=capturePassive(attached,custody,evidenceRoot,clock);
            }else {
            if(originalRecovery)custody.requireCurrent();
            running = originalRecovery?newPrepared.openExistingSameGameRecovery(attached,java.util.Optional.empty(),clock.instant().plus(Duration.ofMinutes(10)))
                    :preentry?newPrepared.openLoadedSaved(attached,source,custody,clock.instant().plus(Duration.ofMinutes(10)))
                    :newPrepared.openRetainedLoadedSaved(attached, source, custody, clock.instant().plus(Duration.ofMinutes(10)));
            if(originalRecovery){custody.requireCurrent();custody.releasePreparation();}
            var adoptedHead = running.core().writer().locked(same -> same.head());
            ObjectNode adopted = event(clock,originalRecovery?"SAVED_ORIGINAL_RECOVERY_ADOPTED":"SAVED_ENTRY_ADOPTED");
            adopted.set("game", attached.generation().toJson());
            adopted.put("actual_head_sequence", adoptedHead.state().sequence()); adopted.put("actual_head_digest", adoptedHead.digest());
            adopted.put("next_sequence", Long.toString(running.nextBatchSequence())); emit(adopted);
            ObjectNode initial = event(clock, "ORDINARY_WORKER_LOOP_START");
            initial.set("game", attached.generation().toJson());
            initial.put("next_sequence", Long.toString(running.nextBatchSequence()));
            initial.put("ordinary_batch_started", false); emit(initial);
            var bounds = newConfig.loop();
            var loopConfig = new RootOrdinaryWorkerLoop.Configuration(running.batchPrefix(), bounds.maximumTurns(), bounds.wallTime(), bounds.readinessTimeout(), bounds.pollInterval(), bounds.checkpointEveryEligibleAdvances());
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
            }
        } catch (Exception actual) {
            failure = actual;
            ObjectNode failed = event(clock, "SAVED_DAEMON_BUSINESS_FAILED");
            failed.put("exception_type", actual.getClass().getName()); failed.put("detail", bounded(actual.toString(), 2048));
            failed.put("game_stop_requested", false);
            try { emit(failed); } catch (IOException output) { actual.addSuppressed(output); }
        } finally {
            if (attached != null) {
                boolean endpointReleased = false;
                try { Objects.requireNonNull(attached).nativeTransport().close(); endpointReleased = true; }
                catch (Exception release) { failure = merge(failure, release); }
                try {
                    emit(event(clock, "SAVED_DAEMON_ENDPOINT_RELEASE")
                            .put("endpoint_release", endpointReleased ? "RELEASED" : "FAILED")
                            .put("game_stop_requested", false));
                } catch (IOException output) { failure = merge(failure, output); }
            }
            failure = close(custody, failure);
            failure = close(running, failure);
            failure = close(attached, failure);
            failure = close(newPrepared, failure);
            failure = close(oldSourcePrepared, failure);
        }
        if (failure != null) throw failure;
        return result;
    }

    /** These schemas select a route; existing source/Core/custody APIs independently enforce its eligibility. */
    static int requestMode(com.fasterxml.jackson.databind.JsonNode value) {
        var request=StrictJson.object(value,Set.of("schema","machineId","sourceRuntimeConfiguration","newRuntimeConfiguration","sourceConfirmation","checkpointPair","ownerDirectory"));
        String schema=StrictJson.text(request.get("schema"));
        if("xar.java-loaded-saved-resume-request/v1".equals(schema))return 0;
        if("xar.java-loaded-saved-preentry-request/v1".equals(schema))return 1;
        if("xar.java-loaded-saved-original-recovery-request/v1".equals(schema))return 3;
        StrictJson.require("xar.java-loaded-saved-passive-observer-request/v1".equals(schema),"resume request schema required");
        return 2;
    }
    static boolean preentryRequest(com.fasterxml.jackson.databind.JsonNode value) {
        int mode=requestMode(value);
        StrictJson.require(mode==0||mode==1,"request grants no initial or retained Saved entry route");
        return mode==1;
    }
    /** One bounded passive receive, never the two-argument observe overload that can issue a fresh query. */
    private static int capturePassive(ManagedGameSession attached,RootProcessAttach.LoadedCustody custody,
            Path evidenceRoot,Clock clock)throws IOException,InterruptedException {
        custody.requireCurrent();attached.verify();
        String reception="AUTOMATIC_SNAPSHOT_RECEIVED",detail="";
        try {attached.nativeTransport().observe(clock.instant().plusSeconds(10));}
        catch(java.io.UncheckedIOException ended){reception="BOUNDED_PASSIVE_RECEIVE_ENDED";detail=bounded(ended.toString(),1024);}
        var diagnostic=attached.nativeTransport().diagnostics();
        Path trace=evidenceRoot.resolve("passive-packets");Files.createDirectory(trace);
        ObjectNode row=event(clock,"PASSIVE_OBSERVER_COMPLETE").put("reception",reception).put("receive_detail",detail)
                .put("received_state",diagnostic.receivedState().name()).put("maximum_receive_seconds",10)
                .put("maximum_receive_frames",1).put("maximum_recorded_packet_bytes",3*65536)
                .put("query_submitted",false).put("Saved_entry_adopted",false).put("game_stop_requested",false);
        retainPassiveNotice(row,trace,"heartbeat",diagnostic.latestHeartbeat());
        retainPassiveNotice(row,trace,"error",diagnostic.latestError());
        retainPassiveNotice(row,trace,"snapshot_diagnostic",diagnostic.latestSnapshotDiagnostic());
        custody.requireCurrent();attached.verify();
        row.put("actual_heartbeat_received",diagnostic.latestHeartbeat().isPresent());
        emit(row);
        return diagnostic.latestHeartbeat().isPresent()?0:2;
    }
    private static void retainPassiveNotice(ObjectNode row,Path trace,String role,
            java.util.Optional<org.xar.ck3.control.nativebridge.NativeGameTransport.ReceivedNotice> actual)throws IOException {
        if(actual.isEmpty()){row.putNull(role);return;}
        byte[] packet=actual.orElseThrow().original().packet().value();
        ExactRef ref=writePassivePacket(trace,role,packet);
        row.set(role,StrictJson.object().put("path",ref.path()).put("bytes",ref.bytes()).put("sha256",ref.sha256())
                .put("observed_at_utc",actual.orElseThrow().observedAt().toString()));
    }
    /** File-only DATA preservation; this mints no Ready, permission, Driver frame or application admission. */
    static ExactRef writePassivePacket(Path trace,String role,byte[] packet)throws IOException {
        if(!Set.of("heartbeat","error","snapshot_diagnostic").contains(role))throw new IOException("bounded passive notice role required");
        if(packet.length<5||packet.length>65536)throw new IOException("passive original packet cap required");
        int length=java.nio.ByteBuffer.wrap(packet,0,4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt();
        if(length!=packet.length-4)throw new IOException("exact original passive packet framing required");
        Path output=trace.resolve(role+".packet");
        Files.write(output,packet,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        return new ExactRef(output.toString(),packet.length,DriverJson.sha256(packet));
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
        if (raw.length != ref.bytes() || before.size() != after.size() || !before.lastModifiedTime().equals(after.lastModifiedTime()) || !Objects.equals(before.fileKey(), after.fileKey()) || !DriverJson.sha256(raw).equals(ref.sha256())) throw new IOException("cold source bytes/hash/identity changed");
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
        return StrictJson.object().put("schema", "xar.java-loaded-saved-resume-result/v1").put("observed_at_utc", clock.instant().toString()).put("status", status);
    }
    private static void emit(ObjectNode row) throws IOException { emit(StrictJson.canonical(row, MAX)); }
    private static void emit(byte[] raw) throws IOException {
        System.out.write(raw); System.out.write(10); System.out.flush();
        if (System.out.checkError()) throw new IOException("saved daemon output failed");
    }
    private static String bounded(String value, int maximum) {
        String text = value == null ? "" : value; return text.substring(0, Math.min(text.length(), maximum));
    }
    private static void reportFailure(Throwable failure) {
        StringBuilder output = new StringBuilder();
        var seen = java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<Throwable, Boolean>());
        Throwable current = failure, inner = failure;
        for (int depth = 0; current != null && depth < 16 && seen.add(current) && output.length() < 14000; depth++) {
            inner = current;
            output.append(depth == 0 ? "" : "Caused by: ").append(current.getClass().getName()).append(": ")
                    .append(bounded(current.getMessage(), 1024)).append('\n');
            var stack = current.getStackTrace();
            for (int frame = 0; frame < Math.min(stack.length, 24) && output.length() < 14000; frame++)
                output.append("  at ").append(stack[frame]).append('\n');
            current = current.getCause();
        }
        output.append("Innermost captured cause: ").append(inner.getClass().getName()).append(": ").append(bounded(inner.getMessage(), 1024));
        System.err.println(bounded(output.toString(), 16384)); System.err.flush();
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