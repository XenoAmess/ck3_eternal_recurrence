package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import java.util.List;
import java.util.ArrayList;
import java.util.Optional;
import java.util.Base64;
import java.io.ByteArrayOutputStream;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.RetainedClosedMeasurement;

/** Actual existing Python consumers call back into the same owning Java measurement session. */
public final class OriginalColdConsumerSession {
    public static final String PYTHON_BOOTSTRAP = "from tools.g2_saved_campaign.current_saved_continuity_v1 import serve_java_closed_partial_cold_consumer_v1; raise SystemExit(serve_java_closed_partial_cold_consumer_v1())";
    public static final int MAX_CALLBACKS_PER_OPERATION = 32;
    private OriginalColdConsumerSession() { }
    @FunctionalInterface public interface ManagedLauncher {
        OriginalWriterTransaction.ManagedProcess start() throws IOException;
    }
    public enum Kind { COLD_INPUTS, LOAD_COLD_INPUTS, SDK_CLOSURE, PREPARED, PREPARE_JUNCTION, PREPARE_OFFLINE, COMPOSE, COMPOSE_BUNDLE, COLD_OWNER, WARM_INPUTS }
    public sealed interface Operation permits ColdInputs, LoadColdInputs, SdkClosure, Prepared, PrepareJunction, PrepareOffline, Compose, ComposeBundle, ColdOwner, WarmInputs {
        Kind kind(); ObjectNode arguments();
    }
    public record ColdInputs() implements Operation {
        @Override public Kind kind() { return Kind.COLD_INPUTS; }
        @Override public ObjectNode arguments() { return StrictJson.object(); }
    }
    public record SdkClosure() implements Operation {
        @Override public Kind kind() { return Kind.SDK_CLOSURE; }
        @Override public ObjectNode arguments() { return StrictJson.object(); }
    }
    public record LoadColdInputs(Path runtimeRoot) implements Operation {
        public LoadColdInputs { absolute(runtimeRoot); }
        @Override public Kind kind() { return Kind.LOAD_COLD_INPUTS; }
        @Override public ObjectNode arguments() { return runtime(runtimeRoot); }
    }
    public record WarmInputs(Path runtimeRoot) implements Operation {
        public WarmInputs { absolute(runtimeRoot); }
        @Override public Kind kind() { return Kind.WARM_INPUTS; }
        @Override public ObjectNode arguments() { return runtime(runtimeRoot); }
    }
    public record Prepared(Path runtimeRoot, String attemptNonce, String taskNonce) implements Operation {
        public Prepared { absolute(runtimeRoot); nonce(attemptNonce); nonce(taskNonce); }
        @Override public Kind kind() { return Kind.PREPARED; }
        @Override public ObjectNode arguments() {
            ObjectNode row = runtime(runtimeRoot); row.put("attempt_nonce",attemptNonce); row.put("task_nonce",taskNonce); return row;
        }
    }
    public record Compose(ExactRef plan) implements Operation {
        public Compose { Objects.requireNonNull(plan); }
        @Override public Kind kind() { return Kind.COMPOSE; }
        @Override public ObjectNode arguments() { ObjectNode row = StrictJson.object(); row.set("plan_ref",plan.toJson()); return row; }
    }
    public record ComposeBundle(ExactRef plan) implements Operation {
        public ComposeBundle { Objects.requireNonNull(plan); }
        @Override public Kind kind() { return Kind.COMPOSE_BUNDLE; }
        @Override public ObjectNode arguments() { ObjectNode row=StrictJson.object();row.set("plan_ref",plan.toJson());return row; }
    }
    /** One explicit filesystem submission; execution requires an actual Root-issued materialization scope. */
    public record PrepareJunction(ExactRef plan, ExactRef quote, Path runtimeRoot) implements Operation {
        public PrepareJunction {
            Objects.requireNonNull(plan); Objects.requireNonNull(quote); absolute(runtimeRoot);
            StrictJson.require(plan.bytes() > 0 && plan.bytes() <= 1_048_576
                    && quote.bytes() > 0 && quote.bytes() <= 1_048_576, "bounded exact junction plan and quote");
        }
        @Override public Kind kind() { return Kind.PREPARE_JUNCTION; }
        @Override public ObjectNode arguments() {
            ObjectNode row=StrictJson.object(); row.set("plan_ref",plan.toJson()); row.set("quote_ref",quote.toJson());
            row.put("approved_runtime_root",runtimeRoot.toString()); return row;
        }
    }
    public record PrepareOffline(ExactRef plan,ExactRef quote,Path runtimeRoot,Path metadataRoot,Path fixtureRoot,
            ExactRef fixture,String attemptNonce,String taskNonce) implements Operation {
        public PrepareOffline { Objects.requireNonNull(plan);Objects.requireNonNull(quote);Objects.requireNonNull(fixture);
            absolute(runtimeRoot);absolute(metadataRoot);absolute(fixtureRoot);nonce(attemptNonce);nonce(taskNonce); }
        @Override public Kind kind() { return Kind.PREPARE_OFFLINE; }
        @Override public ObjectNode arguments() {
            ObjectNode row=StrictJson.object();row.set("plan_ref",plan.toJson());row.set("quote_ref",quote.toJson());
            row.put("approved_runtime_root",runtimeRoot.toString());row.put("approved_metadata_root",metadataRoot.toString());
            row.put("historical_fixture_root",fixtureRoot.toString());row.set("historical_fixture_ref",fixture.toJson());
            row.put("attempt_nonce",attemptNonce);row.put("task_nonce",taskNonce);return row;
        }
    }
    public record ComposedFile(String path,byte[] content) {
        public ComposedFile { absolute(Path.of(path));content=content.clone();StrictJson.require(content.length<=1_048_576,"bounded composed file"); }
        @Override public byte[] content() { return content.clone(); }
    }
    public record ComposedBundle(ExactRef plan,byte[] quote,List<ComposedFile> files) {
        public ComposedBundle {
            Objects.requireNonNull(plan);quote=quote.clone();files=List.copyOf(files);
            StrictJson.require(quote.length>0 && quote.length<=1_048_576 && !files.isEmpty() && files.size()<=192
                    && files.stream().map(ComposedFile::path).distinct().count()==files.size()
                    && files.stream().mapToLong(file->file.content.length).sum()<=8L*1_048_576,"bounded complete original composition");
        }
        @Override public byte[] quote() { return quote.clone(); }
    }
    public record ColdOwner(ExactRef plan, ExactRef quote) implements Operation {
        public ColdOwner { Objects.requireNonNull(plan); Objects.requireNonNull(quote); }
        @Override public Kind kind() { return Kind.COLD_OWNER; }
        @Override public ObjectNode arguments() {
            ObjectNode row = StrictJson.object(); row.set("plan_ref",plan.toJson()); row.set("quote_ref",quote.toJson()); return row;
        }
    }
    public static Operation decodeOperation(JsonNode kindValue, JsonNode argumentsValue) {
        String name = StrictJson.text(kindValue);
        StrictJson.require(Set.of("COLD_INPUTS","LOAD_COLD_INPUTS","SDK_CLOSURE","PREPARED","PREPARE_JUNCTION","PREPARE_OFFLINE","COMPOSE","COMPOSE_BUNDLE","COLD_OWNER","WARM_INPUTS").contains(name),
                "fixed original read-only consumer operation");
        return switch (Kind.valueOf(name)) {
            case COLD_INPUTS -> { StrictJson.object(argumentsValue,Set.of()); yield new ColdInputs(); }
            case SDK_CLOSURE -> { StrictJson.object(argumentsValue,Set.of()); yield new SdkClosure(); }
            case LOAD_COLD_INPUTS -> { var row = StrictJson.object(argumentsValue,Set.of("runtime_root")); yield new LoadColdInputs(path(row,"runtime_root")); }
            case WARM_INPUTS -> { var row = StrictJson.object(argumentsValue,Set.of("runtime_root")); yield new WarmInputs(path(row,"runtime_root")); }
            case PREPARED -> {
                var row = StrictJson.object(argumentsValue,Set.of("runtime_root","attempt_nonce","task_nonce"));
                yield new Prepared(path(row,"runtime_root"),text(row,"attempt_nonce"),text(row,"task_nonce"));
            }
            case COMPOSE -> { var row = StrictJson.object(argumentsValue,Set.of("plan_ref")); yield new Compose(ExactRef.fromJson(row.get("plan_ref"))); }
            case COMPOSE_BUNDLE -> { var row=StrictJson.object(argumentsValue,Set.of("plan_ref"));yield new ComposeBundle(ExactRef.fromJson(row.get("plan_ref"))); }
            case PREPARE_JUNCTION -> {
                var row=StrictJson.object(argumentsValue,Set.of("plan_ref","quote_ref","approved_runtime_root"));
                yield new PrepareJunction(ExactRef.fromJson(row.get("plan_ref")),ExactRef.fromJson(row.get("quote_ref")),
                        path(row,"approved_runtime_root"));
            }
            case PREPARE_OFFLINE -> {
                var row=StrictJson.object(argumentsValue,Set.of("plan_ref","quote_ref","approved_runtime_root","approved_metadata_root",
                        "historical_fixture_root","historical_fixture_ref","attempt_nonce","task_nonce"));
                yield new PrepareOffline(ExactRef.fromJson(row.get("plan_ref")),ExactRef.fromJson(row.get("quote_ref")),
                        path(row,"approved_runtime_root"),path(row,"approved_metadata_root"),path(row,"historical_fixture_root"),
                        ExactRef.fromJson(row.get("historical_fixture_ref")),text(row,"attempt_nonce"),text(row,"task_nonce"));
            }
            case COLD_OWNER -> {
                var row = StrictJson.object(argumentsValue,Set.of("plan_ref","quote_ref"));
                yield new ColdOwner(ExactRef.fromJson(row.get("plan_ref")),ExactRef.fromJson(row.get("quote_ref")));
            }
        };
    }
    public record Consumed(byte[] originalConsumerReceipt, OriginalWriterTransaction.ActualExit processExit,
            Optional<ComposedBundle> composedBundle) {
        public Consumed(byte[] receipt,OriginalWriterTransaction.ActualExit exit) { this(receipt,exit,Optional.empty()); }
        public Consumed { originalConsumerReceipt = originalConsumerReceipt.clone();Objects.requireNonNull(composedBundle); }
        @Override public byte[] originalConsumerReceipt() { return originalConsumerReceipt.clone(); }
        public boolean grantsWarmAttachment() { return false; }
    }

    public static Consumed run(ClosedAdoptionMaterial.CurrentSource current, OriginalWriterTransaction.Committed committed,
            ClosedColdInputsConsumer.CanonicalReceiptSource canonical, RecoveryEvidence basis, RecoveryEvidence qualification,
            ManagedLauncher launcher) throws IOException, InterruptedException {
        // The actual measurement cache and managed process retain their own earlier deadlines.
        try (var authority = ClosedInputsSessionAuthority.open(current,committed,canonical,basis,qualification,Instant.now().plusSeconds(120))) {
            return runOperation(authority,new ColdInputs(),launcher);
        }
    }

    public static Consumed runOperation(ClosedInputsSessionAuthority authority, Operation operation, ManagedLauncher launcher)
            throws IOException, InterruptedException {
        return runOperation(authority,operation,launcher,Optional.empty());
    }
    static Consumed runOperation(ClosedInputsSessionAuthority authority,Operation operation,ManagedLauncher launcher,
            Optional<String> entryInstallationPrefix) throws IOException,InterruptedException {
        StrictJson.require(!(operation instanceof PrepareJunction),
                "PREPARE_JUNCTION requires the concrete retained Root Java path; no Python transport fallback");
        return runTransport(authority,operation,launcher,entryInstallationPrefix);
    }
    private static Consumed runTransport(ClosedInputsSessionAuthority authority,Operation operation,ManagedLauncher launcher,
            Optional<String> entryInstallationPrefix) throws IOException,InterruptedException {
        StrictJson.require(!(operation instanceof ComposeBundle) || entryInstallationPrefix.isPresent(),
                "bundle composition requires actual Root producer settings before process creation");
        authority.qualify(authority.basisRef(),authority.qualificationRef());
        OriginalWriterTransaction.ManagedProcess process = launcher.start();
        try { return exchange(authority,operation,process,entryInstallationPrefix); }
        catch (IOException | InterruptedException | RuntimeException | Error error) {
            OriginalProcessCleanup.suppressing(process,error);
            throw error;
        }
    }
    private static Consumed exchange(ClosedInputsSessionAuthority authority, Operation operation,
            OriginalWriterTransaction.ManagedProcess process,Optional<String> entryInstallationPrefix) throws IOException, InterruptedException {
        String machine = authority.machineId(); ExactRef basis = authority.basisRef(), qualification = authority.qualificationRef();
        ObjectNode request = StrictJson.object(); request.put("schema","xar.java-closed-partial-cold-consumer-request/v1");
        request.put("machine_id",machine); request.set("basis_ref",basis.toJson()); request.set("validation_ref",qualification.toJson());
        request.put("operation",operation.kind().name()); request.set("arguments",operation.arguments());
        if(operation instanceof ComposeBundle) {
            StrictJson.require(entryInstallationPrefix.isPresent(),"actual Root settings must supply the composition installation prefix");
            ((ObjectNode)request.get("arguments")).put("entry_installation_prefix",entryInstallationPrefix.orElseThrow());
        }
        OriginalWriterTransaction.send(process.stdin(),request);
        JsonNode response;
        byte[] responseRaw;
        int callbacks = 0;
        var chunks=new CompositionChunks();
        while (true) {
            responseRaw = OriginalWriterTransaction.readFrame(process.stdout());
            response = StrictJson.parse(responseRaw,OriginalWriterTransaction.MAX_PROTOCOL_BYTES);
            ObjectNode row = SettledQueryClassifier.object(response);
            String schema = text(row,"schema");
            if ("xar.java-closed-composition-chunk/v1".equals(schema)) {
                StrictJson.require(operation instanceof ComposeBundle && responseRaw.length<=65_536,"bundle chunks only on the explicit bounded operation");
                chunks.accept(row,machine,basis,qualification);continue;
            }
            if (!"xar.java-closed-partial-cold-inputs-callback/v1".equals(schema)) { break; }
            StrictJson.require(responseRaw.length <= RecoveryEvidence.MAX_BYTES,"original callback frame remains bounded to 64 KiB");
            ObjectNode callback = StrictJson.object(row,Set.of("schema","machine_id","basis_ref","validation_ref"));
            StrictJson.require(++callbacks <= MAX_CALLBACKS_PER_OPERATION, "finite repeated callbacks in one original consumer operation");
            equal(callback,"machine_id",machine);
            StrictJson.require(ExactRef.fromJson(callback.get("basis_ref")).equals(basis)
                    && ExactRef.fromJson(callback.get("validation_ref")).equals(qualification), "same retained original consumer callback references");
            var verified = authority.qualify(basis,qualification);
            OriginalWriterTransaction.send(process.stdin(),(ObjectNode)StrictJson.parse(verified.wireBytes()));
        }
        StrictJson.require(callbacks > 0,"actual original consumer invoked the owning Java authority");
        ObjectNode result = StrictJson.object(response,Set.of("schema","machine_id","basis_ref","validation_ref","completed_cycles","date_raw",
                "next_sequence","old_ledger_sequence","old_ledger_status","unknown_requests","closed_epoch","new_game_day_credit",
                "new_ordinary_cycle_credit","grants_new_warm_attachment","operation","operation_result"));
        equal(result,"schema","xar.java-closed-partial-cold-consumer-result/v1"); equal(result,"machine_id",machine);
        equal(result,"operation",operation.kind().name());
        StrictJson.require(ExactRef.fromJson(result.get("basis_ref")).equals(basis)
                && ExactRef.fromJson(result.get("validation_ref")).equals(qualification),"actual result retains exact session inputs");
        SettledQueryClassifier.object(result.get("operation_result"));
        ObjectNode published = (ObjectNode)StrictJson.parse(authority.basisBytes());
        for (String field : Set.of("completed_cycles","next_sequence","unknown_requests")) {
            StrictJson.require(result.get(field).equals(published.get(field)), "actual original consumer preserved " + field);
        }
        StrictJson.require(result.get("date_raw").equals(published.get("frame").get("date_raw"))
                && StrictJson.integer(result.get("old_ledger_sequence"),1,StrictJson.MAX_SAFE_INTEGER) == authority.committedSequence(),
                "actual cold frontier and committed writer readback");
        equal(result,"old_ledger_status","repair_required");
        StrictJson.integer(result.get("new_game_day_credit"),0,0); StrictJson.integer(result.get("new_ordinary_cycle_credit"),0,0);
        SettledQueryClassifier.falseValue(result.get("grants_new_warm_attachment"));
        // Recheck the active phase before closing the transport; an ACK alone grants nothing.
        authority.qualify(basis,qualification);
        process.closeOwnedInput(); var exit = process.awaitActualExit();
        StrictJson.require(exit.kernelExitObserved() && exit.exitCode() == 0,"actual original consumer process exit zero");
        // Exit can block and pump callbacks: accept only after the same live phase still qualifies.
        authority.qualify(basis,qualification);
        Optional<ComposedBundle> bundle=operation instanceof ComposeBundle selected
                ?Optional.of(new ComposedBundle(selected.plan(),StrictJson.canonical(result.get("operation_result"),1_048_576),chunks.complete()))
                :Optional.empty();
        return new Consumed(responseRaw,exit,bundle);
    }

    /** Strict sequential transport assembly; no file creation, SDK authority or Native grant. */
    static final class CompositionChunks {
        private final List<ComposedFile> files=new ArrayList<>();
        private final ByteArrayOutputStream content=new ByteArrayOutputStream();
        private String path,sha;private long size,total;private int frames;
        void accept(ObjectNode value,String machine,ExactRef basis,ExactRef qualification) {
            ObjectNode row=StrictJson.object(value,Set.of("schema","machine_id","basis_ref","validation_ref","file_index","path","offset","bytes","sha256","data_base64"));
            StrictJson.require("xar.java-closed-composition-chunk/v1".equals(text(row,"schema"))
                    && ++frames<=512 && machine.equals(text(row,"machine_id"))
                    && basis.equals(ExactRef.fromJson(row.get("basis_ref"))) && qualification.equals(ExactRef.fromJson(row.get("validation_ref"))),"same bounded composition stream");
            long index=StrictJson.integer(row.get("file_index"),0,191),offset=StrictJson.integer(row.get("offset"),0,1_048_576);
            long nextSize=StrictJson.integer(row.get("bytes"),0,1_048_576);String nextPath=text(row,"path"),nextSha=text(row,"sha256");
            StrictJson.require(index==files.size() && nextSha.matches("[0-9a-f]{64}"),"sequential original file and SHA");
            absolute(Path.of(nextPath));
            if(path==null) { StrictJson.require(offset==0,"first composition chunk offset");path=nextPath;sha=nextSha;size=nextSize; }
            StrictJson.require(path.equals(nextPath) && sha.equals(nextSha) && size==nextSize && offset==content.size(),"same complete file chunk sequence");
            StrictJson.require(row.get("data_base64").isTextual(),"exact base64 string, including empty content");
            String encoded=row.get("data_base64").textValue();byte[] raw=Base64.getDecoder().decode(encoded);
            StrictJson.require(raw.length<=32_768 && Base64.getEncoder().encodeToString(raw).equals(encoded)
                    && (raw.length>0 || size==0) && offset+raw.length<=size && total+raw.length<=8L*1_048_576,"canonical bounded original file bytes");
            content.writeBytes(raw);total+=raw.length;
            if(content.size()==size) {
                byte[] actual=content.toByteArray();StrictJson.require(RecoveryEvidence.sha256(actual).equals(sha),"complete original composition file hash");
                files.add(new ComposedFile(path,actual));path=null;sha=null;content.reset();
            }
        }
        List<ComposedFile> complete() { StrictJson.require(path==null && !files.isEmpty(),"complete nonempty original composition stream");return List.copyOf(files); }
    }

    public static RecoveryEvidence serveRootSession(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, WindowsFileWriterSession.Settings settings,
            Path sessionDirectory, Instant earliestDeadline) throws IOException, InterruptedException {
        return RootConsumerSession.serve(source,committed,canonical,basis,qualification,settings,sessionDirectory,earliestDeadline);
    }
    public static RecoveryEvidence serveRootSession(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, WindowsFileWriterSession.Settings settings,
            Path sessionDirectory, Instant earliestDeadline, RetainedClosedMeasurement retained) throws IOException, InterruptedException {
        return serveRootSession(source,committed,canonical,basis,qualification,settings,sessionDirectory,earliestDeadline,retained,
                java.util.Optional.empty(),java.util.Optional.empty());
    }
    static RecoveryEvidence serveRootSession(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed, ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis, RecoveryEvidence qualification, WindowsFileWriterSession.Settings settings,
            Path sessionDirectory, Instant earliestDeadline, RetainedClosedMeasurement retained,
            java.util.Optional<OriginalWriterTransaction.RetainedSession> writerSession,
            java.util.Optional<NativeOwnerResumeSession.Workflow> workflow) throws IOException, InterruptedException {
        return serveRootSession(source,committed,canonical,basis,qualification,settings,sessionDirectory,earliestDeadline,retained,
                writerSession,workflow,java.util.Optional.empty());
    }
    static RecoveryEvidence serveRootSession(ClosedAdoptionMaterial.CurrentSource source,
            OriginalWriterTransaction.Committed committed,ClosedColdInputsConsumer.CanonicalReceiptSource canonical,
            RecoveryEvidence basis,RecoveryEvidence qualification,WindowsFileWriterSession.Settings settings,
            Path sessionDirectory,Instant earliestDeadline,RetainedClosedMeasurement retained,
            java.util.Optional<OriginalWriterTransaction.RetainedSession> writerSession,
            java.util.Optional<NativeOwnerResumeSession.Workflow> workflow,
            java.util.Optional<RootColdResumeSession.Workflow> coldWorkflow) throws IOException,InterruptedException {
        Objects.requireNonNull(retained);
        try (retained) {
            retained.requireHistoricalInputs();
            return RootConsumerSession.serve(source,committed,canonical,basis,qualification,settings,sessionDirectory,earliestDeadline,
                    java.util.Optional.of(retained),writerSession,workflow,coldWorkflow);
        }
    }
    private static ObjectNode runtime(Path path) { ObjectNode row = StrictJson.object(); row.put("runtime_root",path.toString()); return row; }
    private static void absolute(Path path) {
        Objects.requireNonNull(path); StrictJson.require(path.isAbsolute() && path.normalize().equals(path),"absolute normalized consumer runtime");
    }
    private static void nonce(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{32}"),"exact consumer nonce"); }
    private static Path path(ObjectNode row, String name) { return Path.of(text(row,name)); }
    private static String text(ObjectNode row, String key) { return StrictJson.text(row.get(key)); }
    private static void equal(ObjectNode row, String key, String expected) { SettledQueryClassifier.equal(row,key,expected); }
}
