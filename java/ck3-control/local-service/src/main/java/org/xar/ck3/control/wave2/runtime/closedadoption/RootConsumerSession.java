package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;
import org.xar.ck3.control.wave2.runtime.savedproof.RetainedClosedMeasurement;

/** Finite continuation of the existing Root file session, restricted to original read-only consumers. */
final class RootConsumerSession {
    static final int MAX_OPERATIONS = RootConsumerProtocol.MAX_OPERATIONS;
    private RootConsumerSession() { }
    static RecoveryEvidence serve(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, WindowsFileWriterSession.Settings settings,
            Path directory, Instant requestedDeadline) throws IOException, InterruptedException {
        return serve(source,committed,canonical,basis,qualification,settings,directory,requestedDeadline,Optional.empty());
    }
    static RecoveryEvidence serve(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, WindowsFileWriterSession.Settings settings,
            Path directory, Instant requestedDeadline, Optional<RetainedClosedMeasurement> historical) throws IOException, InterruptedException {
        return serve(source,committed,canonical,basis,qualification,settings,directory,requestedDeadline,historical,Optional.empty(),Optional.empty());
    }
    static RecoveryEvidence serve(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, WindowsFileWriterSession.Settings settings,
            Path directory, Instant requestedDeadline, Optional<RetainedClosedMeasurement> historical,
            Optional<OriginalWriterTransaction.RetainedSession> writerSession) throws IOException, InterruptedException {
        return serve(source,committed,canonical,basis,qualification,settings,directory,requestedDeadline,historical,writerSession,Optional.empty());
    }
    static RecoveryEvidence serve(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, WindowsFileWriterSession.Settings settings,
            Path directory, Instant requestedDeadline, Optional<RetainedClosedMeasurement> historical,
            Optional<OriginalWriterTransaction.RetainedSession> writerSession,
            Optional<NativeOwnerResumeSession.Workflow> nativeWorkflow) throws IOException, InterruptedException {
        return serve(source,committed,canonical,basis,qualification,settings,directory,requestedDeadline,historical,writerSession,nativeWorkflow,Optional.empty());
    }
    static RecoveryEvidence serve(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed,ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis,RecoveryEvidence qualification,WindowsFileWriterSession.Settings settings,
            Path directory,Instant requestedDeadline,Optional<RetainedClosedMeasurement> historical,
            Optional<OriginalWriterTransaction.RetainedSession> writerSession,Optional<NativeOwnerResumeSession.Workflow> nativeWorkflow,
            Optional<RootColdResumeSession.Workflow> coldWorkflow) throws IOException,InterruptedException {
        Instant deadline = requestedDeadline.isBefore(settings.leaseDeadline()) ? requestedDeadline : settings.leaseDeadline();
        StrictJson.require(Instant.now().isBefore(deadline),"Root consumer session uses the original earlier finite deadline");
        Path root = settings.outputRoot().toRealPath();
        StrictJson.require(directory.isAbsolute() && directory.normalize().equals(directory)
                && directory.getParent().toRealPath().equals(root) && !Files.exists(directory,LinkOption.NOFOLLOW_LINKS),
                "fresh Root consumer session directory immediately inside the existing owned output root");
        settings.capacityGuard().run();
        Files.createDirectory(directory);
        String nonce = UUID.randomUUID().toString().replace("-","");
        String machine = StrictJson.text(StrictJson.parse(basis.bytes()).get("machine_id"));
        var binding = new RootConsumerProtocol.Binding(machine,nonce);
        List<ExactRef> operationReceipts = new ArrayList<>();
        Path terminal = directory.resolve("session-result.json");
        try (var authority = ClosedInputsSessionAuthority.open(source,committed,canonical,basis,qualification,deadline,historical,writerSession)) {
            StrictJson.require(authority.machineId().equals(machine),"actual retained authority machine");
            var callbackEndpoint = ClosedInputsFileEndpoint.create(authority,settings,nonce,directory,deadline);
            var operationSettings = operationSettings(settings,deadline,callbackEndpoint);
            ObjectNode ready = base(machine,nonce,deadline,basis.reference(),qualification.reference(),"READY");
            ready.set("callback_endpoint_ref",callbackEndpoint.descriptorRef().toJson());
            ready.put("maximum_operations",MAX_OPERATIONS);
            ready.put("maximum_callbacks_per_operation",OriginalColdConsumerSession.MAX_CALLBACKS_PER_OPERATION);
            var kinds = ready.putArray("operations");
            for (var kind : OriginalColdConsumerSession.Kind.values()) { kinds.add(kind.name()); }
            kinds.add("BEGIN_RESTORE_READS");
            if (nativeWorkflow.isPresent()) { kinds.add("OPEN_NATIVE_OWNER"); }
            if (coldWorkflow.isPresent()) { kinds.add("OPEN_COLD_SESSION"); }
            publish(directory.resolve("session-ready.json"),ready);
            String status = "OPERATION_LIMIT_REACHED";
            ExactRef materializedPlan=null,materializedQuote=null;Path materializedRuntime=null;
            for (int sequence = 1; sequence <= MAX_OPERATIONS; sequence++) {
                Path command = directory.resolve(RootConsumerProtocol.requestFileName(sequence));
                Path close = directory.resolve("close.json");
                while (!Files.exists(command,LinkOption.NOFOLLOW_LINKS) && !Files.exists(close,LinkOption.NOFOLLOW_LINKS)
                        && Instant.now().isBefore(deadline)) {
                    settings.capacityGuard().run();
                    callbackEndpoint.poll();
                    Thread.sleep(100);
                }
                if (!Instant.now().isBefore(deadline)) { status = "DEADLINE_EXPIRED"; break; }
                if (Files.exists(close,LinkOption.NOFOLLOW_LINKS)) {
                    RootConsumerProtocol.decodeClose(readSmall(close),binding);
                    status = "CLOSED"; break;
                }
                var commandValue = RootConsumerProtocol.decodeCommand(readSmall(command),binding,sequence);
                if (commandValue.request() instanceof RootConsumerProtocol.OpenColdSession open) {
                    ObjectNode result=base(machine,nonce,deadline,basis.reference(),qualification.reference(),"COLD_WORKFLOW_UNAVAILABLE");
                    result.put("sequence",sequence); result.put("operation","OPEN_COLD_SESSION"); result.put("prepared_sequence",open.preparedSequence());
                    try {
                        if (coldWorkflow.isPresent()) {
                            RootColdResumeSession cold=RootColdResumeSession.open(authority,open.preparedSequence(),directory);
                            coldWorkflow.orElseThrow().run(cold);
                            result.put("status","COLD_WORKFLOW_RETURNED"); result.put("resource_phase",cold.phase().name());
                            result.put("qualification_scope","LIMITED_COLD_STAGES_ONLY_NATIVE_AND_BUSINESS_ACCEPTANCE_SEPARATE");
                        } else { result.put("reason","ACTUAL_ROOT_COLD_WORKFLOW_NOT_SUPPLIED"); }
                    } catch(IOException|InterruptedException|RuntimeException failure) {
                        result.put("status","COLD_WORKFLOW_FAILED_OR_UNKNOWN_NO_REPLAY"); result.put("error",boundedError(failure)); result.put("replay_allowed",false);
                        operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),result).reference());
                        throw failure;
                    }
                    operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),result).reference()); continue;
                }
                if (commandValue.request() instanceof RootConsumerProtocol.OpenNativeOwner open) {
                    ObjectNode opened = base(machine,nonce,deadline,basis.reference(),qualification.reference(),"COLD_OWNER_UNAVAILABLE");
                    opened.put("sequence",sequence); opened.put("operation","OPEN_NATIVE_OWNER");
                    opened.put("prepared_sequence",open.preparedSequence());
                    opened.put("grants_new_warm_attachment",false);
                    if (nativeWorkflow.isEmpty()) {
                        opened.put("reason","ROOT_NATIVE_WORKFLOW_NOT_SUPPLIED");
                    } else {
                        var workflow = nativeWorkflow.orElseThrow();
                        var actualInputs = authority.nativeRestoreInputs(open.preparedSequence());
                        var start = NativeOwnerResumeSession.startOwner(authority,open.preparedSequence(),workflow.specification(actualInputs));
                        if (start instanceof NativeOwnerResumeSession.Started started) {
                            NativeOwnerResumeSession session = started.session();
                            try {
                                var actualOwnerIdentity = session.ownedStdio().identity();
                                workflow.started(session);
                                opened.put("status","COLD_OWNER_WORKFLOW_RETURNED");
                                opened.put("owner_pid",actualOwnerIdentity.pid());
                                opened.put("owner_creation_filetime",actualOwnerIdentity.creationFiletimeDecimal());
                                opened.put("owner_resource_phase",session.phase().name());
                                session.cleanupFailure().ifPresent(value -> opened.put("owner_cleanup_unavailable",value));
                                opened.put("qualification_scope","LIMITED_COLD_OWNER_ONLY_SAVED_LOAD_AND_PRE_CAP_ACCEPTANCE_SEPARATE");
                            } catch (IOException | InterruptedException | RuntimeException failure) {
                                opened.put("status","COLD_OWNER_WORKFLOW_UNKNOWN_NO_REPLAY");
                                opened.put("error",boundedError(failure)); opened.put("replay_allowed",false);
                                operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),opened).reference());
                                throw failure;
                            }
                        } else if (start instanceof NativeOwnerResumeSession.Unavailable unavailable) {
                            opened.put("reason",unavailable.reason().name()); opened.put("detail",unavailable.detail());
                        } else {
                            var unknown = (NativeOwnerResumeSession.Unknown)start;
                            opened.put("status","COLD_OWNER_SUBMISSION_UNKNOWN_NO_REPLAY");
                            opened.put("reason",unknown.reason().name()); opened.put("detail",unknown.detail()); opened.put("replay_allowed",false);
                            operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),opened).reference());
                            throw new IOException("original cold owner submission unknown; no replay");
                        }
                    }
                    operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),opened).reference());
                    continue;
                }
                if (commandValue.request() instanceof RootConsumerProtocol.BeginRestoreReads begin) {
                    int preparedSequence = begin.preparedSequence();
                    authority.beginRestoreReads(preparedSequence);
                    ObjectNode phase = base(machine,nonce,deadline,basis.reference(),qualification.reference(),"RESTORE_INPUT_VIEW_REGISTERED");
                    phase.put("sequence",sequence); phase.put("operation","BEGIN_RESTORE_READS"); phase.put("prepared_sequence",preparedSequence);
                    phase.put("qualification_scope",authority.qualificationScope()); phase.put("current_driver_qualified",false);
                    phase.putArray("actual_original_processes");
                    operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),phase).reference());
                    continue;
                }
                var operation = ((RootConsumerProtocol.Consumer)commandValue.request()).operation();
                settings.capacityGuard().run();
                List<WindowsFileWriterSession> launched = new ArrayList<>();
                ObjectNode result = base(machine,nonce,deadline,basis.reference(),qualification.reference(),"VERIFIED_ORIGINAL_CONSUMER");
                result.put("sequence",sequence); result.put("operation",operation.kind().name());
                try {
                    if(operation instanceof OriginalColdConsumerSession.PrepareOffline prepare) {
                        authority.requireCompletedJunction(prepare);
                        StrictJson.require(prepare.plan().equals(materializedPlan) && prepare.quote().equals(materializedQuote)
                                && prepare.runtimeRoot().equals(materializedRuntime),"offline producer uses the actual same-session Java materialization");
                        StrictJson.require(prepare.metadataRoot().equals(root.resolve("preparation-metadata"))
                                && prepare.fixtureRoot().equals(root.resolve("preparation-historical-fixture")),
                                "offline producer write roots come from the actual Root-owned output, not command authority");
                    }
                    if(operation instanceof OriginalColdConsumerSession.PrepareJunction junction) {
                        CampaignScoreJunction.Prepared actual=authority.prepareJunction(junction);
                        actual.requireCurrent();
                        Path javaPath=directory.resolve(String.format(java.util.Locale.ROOT,"%04d.java-junction.json",sequence));
                        ExactRef reference=publishFrame(javaPath,actual.bytes());
                        actual.requireCurrent();
                        result.put("status",CampaignScoreJunction.ROOT_RESULT_STATUS);
                        result.set("java_junction_ref",reference.toJson());
                        result.set("junction_writer_handoff",authority.junctionHandoffEvidence());
                        result.put("qualification_scope",authority.qualificationScope());
                        result.putArray("actual_original_processes");
                        settings.capacityGuard().run();
                        operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),result).reference());
                        continue;
                    }
                    var consumed = OriginalColdConsumerSession.runOperation(authority,operation,() -> {
                        var mode=operation instanceof OriginalColdConsumerSession.ComposeBundle
                                ?WindowsFileWriterSession.Mode.ROOT_COMPOSE_BUNDLE:WindowsFileWriterSession.Mode.ROOT_OPERATION;
                        var session = WindowsFileWriterSession.start(operationSettings,mode);
                        launched.add(session); return session;
                    },operation instanceof OriginalColdConsumerSession.ComposeBundle
                            ?Optional.of(WindowsFileWriterSession.entryInstallationPrefix(operationSettings)):Optional.empty());
                    if(consumed.composedBundle().isPresent()) {
                        var workflow=coldWorkflow.orElseThrow(()->new IOException("concrete Root Java materializer is required"));
                        var scope=workflow.materialize(consumed.composedBundle().orElseThrow());
                        authority.recordMaterialized(consumed,scope);
                        ExactRef quote=scope.quoteRef();
                        var bundle=consumed.composedBundle().orElseThrow();
                        materializedPlan=bundle.plan();materializedQuote=quote;
                        materializedRuntime=Path.of(StrictJson.text(StrictJson.parse(bundle.quote()).get("runtime_root")));
                        result.set("materialized_quote_ref",quote.toJson());
                    }
                    if (operation instanceof OriginalColdConsumerSession.Prepared prepared) { authority.recordPrepared(sequence,prepared,consumed); }
                    result.put("qualification_scope",authority.qualificationScope());
                    Path originalPath = directory.resolve(String.format(java.util.Locale.ROOT,"%04d.original-consumer.json",sequence));
                    result.set("original_consumer_ref",publishFrame(originalPath,consumed.originalConsumerReceipt()).toJson());
                    recordJobs(result,launched,true);
                    settings.capacityGuard().run();
                    operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),result).reference());
                } catch (IOException | InterruptedException | RuntimeException error) {
                    String failureStatus=operation instanceof OriginalColdConsumerSession.PrepareJunction
                            ?"JAVA_JUNCTION_FAILED_OR_UNKNOWN_NO_REPLAY":"REJECTED_OR_UNAVAILABLE";
                    result.put("status",failureStatus); result.put("error",boundedError(error));
                    if(operation instanceof OriginalColdConsumerSession.PrepareJunction) result.put("replay_allowed",false);
                    recordJobs(result,launched,false);
                    operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),result).reference());
                    ObjectNode failed = terminal(machine,nonce,deadline,basis,qualification,failureStatus,operationReceipts,authority.callbackCount());
                    failed.set("callback_endpoint_ref",callbackEndpoint.descriptorRef().toJson());
                    failed.put("qualified_file_callbacks",callbackEndpoint.processedCount());
                    failed.put("failed_sequence",sequence); failed.put("error",boundedError(error)); publish(terminal,failed);
                    if (error instanceof InterruptedException interrupted) { throw interrupted; }
                    throw new IOException("original consumer failed; retained Java session closed; terminal="+terminal,error);
                }
            }
            ObjectNode result = terminal(machine,nonce,deadline,basis,qualification,status,operationReceipts,authority.callbackCount());
            result.put("qualification_scope",authority.qualificationScope());
            result.set("callback_endpoint_ref",callbackEndpoint.descriptorRef().toJson());
            result.put("qualified_file_callbacks",callbackEndpoint.processedCount());
            return publish(terminal,result);
        } catch (IOException | InterruptedException | RuntimeException failure) {
            if (!Files.exists(terminal,LinkOption.NOFOLLOW_LINKS)) {
                ObjectNode result = terminal(machine,nonce,deadline,basis,qualification,
                        "REJECTED_OR_UNAVAILABLE",operationReceipts,0);
                result.put("error",boundedError(failure));
                try { publish(terminal,result); } catch (IOException | RuntimeException reporting) { failure.addSuppressed(reporting); }
            }
            throw failure;
        }
    }
    /** Pump the same live authority while an original consumer blocks on stdout or process exit. */
    static WindowsFileWriterSession.Settings operationSettings(WindowsFileWriterSession.Settings settings,
            Instant deadline, ClosedInputsFileEndpoint callbackEndpoint) {
        StrictJson.require(!deadline.isAfter(settings.leaseDeadline()),"active consumer guard cannot extend its original lease");
        return new WindowsFileWriterSession.Settings(settings.python(),settings.repo(),settings.outputRoot(),
                settings.memoryLimitBytes(),settings.timeout(),deadline,settings.environment(),settings.mechanicalSource(),settings.coldOwnerSource(),() -> {
                    settings.capacityGuard().run();
                    try { callbackEndpoint.poll(); }
                    catch (IOException error) { throw new java.io.UncheckedIOException(error); }
                },settings.sdkLineageBinding());
    }
    private static ObjectNode terminal(String machine, String nonce, Instant deadline, RecoveryEvidence basis,
            RecoveryEvidence qualification, String status, List<ExactRef> receipts, long validations) {
        ObjectNode row = base(machine,nonce,deadline,basis.reference(),qualification.reference(),status);
        row.put("schema","xar.java-closed-partial-root-consumer-session-result/v1");
        row.put("authority_closed",true); row.put("qualification_calls",validations); row.put("operation_count",receipts.size());
        var entries = row.putArray("operation_receipts"); for (ExactRef receipt : receipts) { entries.add(receipt.toJson()); }
        return row;
    }
    private static ObjectNode base(String machine, String nonce, Instant deadline, ExactRef basis, ExactRef qualification, String status) {
        ObjectNode row = StrictJson.object(); row.put("schema","xar.java-closed-partial-root-consumer-session/v1");
        row.put("machine_id",machine); row.put("observed_at_utc",Instant.now().toString()); row.put("session_nonce",nonce);
        row.put("deadline_utc",deadline.toString()); row.put("status",status); row.set("basis_ref",basis.toJson()); row.set("validation_ref",qualification.toJson());
        row.put("qualification_scope",ClosedColdInputsConsumer.SCOPE); row.put("new_game_day_credit",0); row.put("new_ordinary_cycle_credit",0);
        row.put("original_actions_replayed",false); row.put("grants_new_warm_attachment",false); return row;
    }
    private static void recordJobs(ObjectNode result, List<WindowsFileWriterSession> launched, boolean requireSuccess) {
        var jobs = result.putArray("actual_original_processes");
        for (var session : launched) {
            var actual = session.actualCommandResult();
            StrictJson.require(!requireSuccess || actual.isPresent(),"actual original consumer terminal must be retained");
            ObjectNode row = jobs.addObject(); row.put("terminal_path",session.terminalPath().toString());
            row.put("stdout_path",session.stdoutPath().toString());
            if (actual.isEmpty()) { row.put("status","ACTUAL_TERMINAL_UNAVAILABLE"); continue; }
            var value = actual.orElseThrow(); row.put("status",value.passed() ? "PASSED" : "FAILED");
            row.put("pid",value.identity().pid()); row.put("creation_filetime",value.identity().creationFiletimeDecimal()); row.put("exit_code",value.exitCode());
            row.put("active_processes",value.accounting().activeProcesses()); row.put("peak_job_memory_bytes",value.accounting().peakJobMemoryBytes());
            StrictJson.require(!requireSuccess || value.passed(),"original consumer actual native Job passed and active zero");
        }
        StrictJson.require(!requireSuccess || launched.size() == 1,"one actual original consumer Job per fixed operation");
    }
    private static byte[] readSmall(Path path) throws IOException {
        var identities = new WindowsSavedProofIdentityReader(); var before = identities.stat(path);
        StrictJson.require(before.bytes().signum() > 0 && before.bytes().longValueExact() <= RecoveryEvidence.MAX_BYTES,"complete bounded Root consumer metadata");
        byte[] raw;
        try (var input = Files.newInputStream(path)) { raw = input.readNBytes(RecoveryEvidence.MAX_BYTES+1); }
        StrictJson.require(raw.length == before.bytes().longValueExact() && before.equals(identities.stat(path)),"stable native Root command identity");
        return raw;
    }
    private static RecoveryEvidence publish(Path path, ObjectNode value) throws IOException {
        byte[] raw = ClosedAdoptionJson.encode(value);
        Files.write(path,raw,StandardOpenOption.CREATE_NEW);
        return new RecoveryEvidence(new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)),raw);
    }
    private static ExactRef publishFrame(Path path, byte[] raw) throws IOException {
        StrictJson.require(raw.length > 0 && raw.length <= OriginalWriterTransaction.MAX_PROTOCOL_BYTES,"bounded complete original consumer response");
        StrictJson.parse(raw,OriginalWriterTransaction.MAX_PROTOCOL_BYTES);
        Files.write(path,raw,StandardOpenOption.CREATE_NEW);
        return new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw));
    }
    private static String boundedError(Throwable error) {
        String value = error.getClass().getSimpleName()+": "+error.getMessage(); return value.substring(0,Math.min(value.length(),2048));
    }
}
