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
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;
import org.xar.ck3.control.wave2.runtime.savedproof.RetainedClosedMeasurement;

/** Finite continuation of the existing Root file session, restricted to original read-only consumers. */
final class RootConsumerSession {
    static final int MAX_OPERATIONS = 16;
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
        List<ExactRef> operationReceipts = new ArrayList<>();
        Path terminal = directory.resolve("session-result.json");
        try (var authority = ClosedInputsSessionAuthority.open(source,committed,canonical,basis,qualification,deadline,historical)) {
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
            publish(directory.resolve("session-ready.json"),ready);
            String status = "OPERATION_LIMIT_REACHED";
            for (int sequence = 1; sequence <= MAX_OPERATIONS; sequence++) {
                Path command = directory.resolve(String.format(java.util.Locale.ROOT,"%04d.request.json",sequence));
                Path close = directory.resolve("close.json");
                while (!Files.exists(command,LinkOption.NOFOLLOW_LINKS) && !Files.exists(close,LinkOption.NOFOLLOW_LINKS)
                        && Instant.now().isBefore(deadline)) {
                    settings.capacityGuard().run();
                    callbackEndpoint.poll();
                    Thread.sleep(100);
                }
                if (!Instant.now().isBefore(deadline)) { status = "DEADLINE_EXPIRED"; break; }
                if (Files.exists(close,LinkOption.NOFOLLOW_LINKS)) {
                    ObjectNode value = StrictJson.object(StrictJson.parse(readSmall(close)),Set.of("schema","machine_id","session_nonce"));
                    require(value,"schema","xar.java-closed-partial-root-consumer-close/v1");
                    require(value,"machine_id",machine); require(value,"session_nonce",nonce);
                    status = "CLOSED"; break;
                }
                ObjectNode commandValue = StrictJson.object(StrictJson.parse(readSmall(command)),Set.of("schema","machine_id","session_nonce","sequence","operation","arguments"));
                require(commandValue,"schema","xar.java-closed-partial-root-consumer-command/v1");
                require(commandValue,"machine_id",machine); require(commandValue,"session_nonce",nonce);
                StrictJson.integer(commandValue.get("sequence"),sequence,sequence);
                if ("BEGIN_RESTORE_READS".equals(StrictJson.text(commandValue.get("operation")))) {
                    var arguments = StrictJson.object(commandValue.get("arguments"),Set.of("prepared_sequence"));
                    int preparedSequence = (int)StrictJson.integer(arguments.get("prepared_sequence"),1,MAX_OPERATIONS);
                    authority.beginRestoreReads(preparedSequence);
                    ObjectNode phase = base(machine,nonce,deadline,basis.reference(),qualification.reference(),"RESTORE_INPUT_VIEW_REGISTERED");
                    phase.put("sequence",sequence); phase.put("operation","BEGIN_RESTORE_READS"); phase.put("prepared_sequence",preparedSequence);
                    phase.put("qualification_scope",authority.qualificationScope()); phase.put("current_driver_qualified",false);
                    phase.putArray("actual_original_processes");
                    operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),phase).reference());
                    continue;
                }
                var operation = OriginalColdConsumerSession.decodeOperation(commandValue.get("operation"),commandValue.get("arguments"));
                settings.capacityGuard().run();
                List<WindowsFileWriterSession> launched = new ArrayList<>();
                ObjectNode result = base(machine,nonce,deadline,basis.reference(),qualification.reference(),"VERIFIED_ORIGINAL_CONSUMER");
                result.put("sequence",sequence); result.put("operation",operation.kind().name());
                try {
                    var consumed = OriginalColdConsumerSession.runOperation(authority,operation,() -> {
                        var session = WindowsFileWriterSession.start(operationSettings,WindowsFileWriterSession.Mode.ROOT_OPERATION);
                        launched.add(session); return session;
                    });
                    if (operation instanceof OriginalColdConsumerSession.Prepared prepared) { authority.recordPrepared(sequence,prepared,consumed); }
                    result.put("qualification_scope",authority.qualificationScope());
                    Path originalPath = directory.resolve(String.format(java.util.Locale.ROOT,"%04d.original-consumer.json",sequence));
                    result.set("original_consumer_ref",publishFrame(originalPath,consumed.originalConsumerReceipt()).toJson());
                    recordJobs(result,launched,true);
                    settings.capacityGuard().run();
                    operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),result).reference());
                } catch (IOException | InterruptedException | RuntimeException error) {
                    result.put("status","REJECTED_OR_UNAVAILABLE"); result.put("error",boundedError(error));
                    recordJobs(result,launched,false);
                    operationReceipts.add(publish(directory.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),result).reference());
                    ObjectNode failed = terminal(machine,nonce,deadline,basis,qualification,"REJECTED_OR_UNAVAILABLE",operationReceipts,authority.callbackCount());
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
                });
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
    private static void require(ObjectNode row, String key, String expected) { SettledQueryClassifier.equal(row,key,expected); }
    private static String boundedError(Throwable error) {
        String value = error.getClass().getSimpleName()+": "+error.getMessage(); return value.substring(0,Math.min(value.length(),2048));
    }
}
