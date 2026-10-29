package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.CharBuffer;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedProofReadTicket;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialAdmissionVerifier;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryReducer;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.recovery.RecoveryPrerequisiteVerifier;
import org.xar.ck3.control.recovery.RecoveryPreview;

/** One managed Java host drives the existing original writer; no separate JVM or native connection. */
public final class OriginalWriterTransaction {
    /** A transport envelope contains several independently bounded original metadata documents. */
    static final int MAX_PROTOCOL_BYTES = 262_144;
    public static final String PYTHON_BOOTSTRAP = "from tools.g2_saved_campaign.current_saved_continuity_v1 import serve_java_closed_partial_writer_v1; raise SystemExit(serve_java_closed_partial_writer_v1())";
    private OriginalWriterTransaction() { }
    public record Target(Path canonicalPath, ExactRef originalWriter) {
        public Target { Objects.requireNonNull(canonicalPath); Objects.requireNonNull(originalWriter);
            StrictJson.require(canonicalPath.isAbsolute(), "explicit Root-selected original canonical target"); }
    }
    /** Supplied by the sole Root process owner with its existing Win32 Job/finite deadline. */
    public interface ManagedProcess {
        InputStream stdout(); OutputStream stdin();
        ActualExit awaitActualExit() throws IOException, InterruptedException;
        void closeOwnedInput() throws IOException;
    }
    @FunctionalInterface public interface ManagedLauncher {
        /** Starts the fixed Python bootstrap in the original Root Job only after Java preflight passed. */
        ManagedProcess start(Target target) throws IOException;
    }
    /** Read-only additional scope check at the real original writer lock, never an action or continuation grant. */
    @FunctionalInterface public interface LockedRecheck {
        void verify(Target target) throws IOException;
    }
    public record ActualExit(long pid, String creationFiletime, int exitCode, boolean kernelExitObserved) {
        public ActualExit { StrictJson.safe(pid, 1);
            new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(creationFiletime); }
    }
    public record Document(RecoveryEvidence evidence, FileStatIdentity identity) {
        public Document { Objects.requireNonNull(evidence); Objects.requireNonNull(identity);
            StrictJson.require(identity.bytes().longValueExact() == evidence.reference().bytes(), "actual readback stat size"); }
        static Document decode(JsonNode value) {
            ObjectNode row = StrictJson.object(value, Set.of("ref", "identity", "raw_utf8"));
            ExactRef reference = ExactRef.fromJson(row.get("ref"));
            RecoveryEvidence evidence = new RecoveryEvidence(reference, documentUtf8(row.get("raw_utf8")));
            return new Document(evidence, FileStatIdentity.fromJson(row.get("identity"), FileStatIdentity.SCHEMA));
        }
        private static byte[] documentUtf8(JsonNode value) {
            StrictJson.require(value != null && value.isTextual(), "raw readback UTF-8 text required");
            String text = value.textValue();
            StrictJson.require(!text.isEmpty() && text.length() <= RecoveryEvidence.MAX_BYTES, "bounded raw readback document required");
            try {
                var encoded = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).encode(CharBuffer.wrap(text));
                StrictJson.require(encoded.remaining() <= RecoveryEvidence.MAX_BYTES, "bounded raw readback UTF-8 document required");
                byte[] raw = new byte[encoded.remaining()]; encoded.get(raw); return raw;
            } catch (CharacterCodingException error) {
                throw new ContractViolationException("well-formed Unicode readback required",error);
            }
        }
        public ObjectNode value() { return object(StrictJson.parse(evidence.bytes())); }
    }
    public record Committed(Target target, Document head, Document event, Document index, ActualExit processExit,
            String inputDigest, String businessDigest, boolean idempotentReplay) {
        public Committed { Objects.requireNonNull(target); Objects.requireNonNull(head); Objects.requireNonNull(event); Objects.requireNonNull(index);
            Objects.requireNonNull(processExit); StrictJson.text(inputDigest); StrictJson.text(businessDigest); }
        public boolean gameActionsReplayed() { return false; }
    }
    public record Evaluation(ClosedAdoptionMaterial material, RecoveryPreview.Candidate candidate, String businessDigest,
            RecoveryPrerequisiteVerifier.Verified prerequisites) { }

    /** Not reconstructible from Committed/JSON. Only the actual production Job path creates it. */
    static final class RetainedExecution {
        private final Committed committed;
        private final RetainedSession session;
        private final WindowsFileWriterSession process;
        private RetainedExecution(Committed committed, RetainedSession session, WindowsFileWriterSession process) {
            this.committed = committed; this.session = session; this.process = process;
        }
        Committed committed() { return committed; }
        RetainedSession session() { return session; }
        WindowsFileWriterSession process() { return process; }
    }
    static RetainedExecution executeRetained(Target target, ClosedAdoptionMaterial.CurrentSource writerCurrent,
            ClosedAdoptionMaterial.CurrentSource handoffCurrent, Runnable rootScope, SavedProofReadTicket ticket,
            WindowsFileWriterSession.Settings settings)
            throws IOException, InterruptedException {
        java.util.concurrent.atomic.AtomicReference<WindowsFileWriterSession> actual = new java.util.concurrent.atomic.AtomicReference<>();
        Committed committed = execute(target,writerCurrent,selected -> {
            var process = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.WRITER);
            actual.set(process); return process;
        });
        var process = actual.get();
        StrictJson.require(process != null && process.actualCommandResult().orElseThrow().passed(),
                "retained writer session requires the actual original writer Job zero and no active processes");
        return new RetainedExecution(committed,new RetainedSession(committed,handoffCurrent,rootScope,ticket,settings,evaluate(handoffCurrent.current())),process);
    }

    public static final class ColdStageNotSubmitted extends IOException {
        private static final long serialVersionUID=1L;
        private final RootColdStageReview.Stage stage;
        private ColdStageNotSubmitted(RootColdStageReview.Stage stage,Throwable cause) {
            super("Original handoff terminal Job zero and actual cold stage has not entered submission: "+stage,cause);this.stage=stage;
        }
        public RootColdStageReview.Stage stage() { return stage; }
    }
    /** One live Root production continuation; no public factory, deserializer or boolean grant. */
    public static final class RetainedSession {
        private final Thread owner = Thread.currentThread();
        private final Committed committed;
        private final ClosedAdoptionMaterial.CurrentSource current;
        private final Runnable rootScope;
        private final SavedProofReadTicket ticket;
        private final WindowsFileWriterSession.Settings settings;
        private final Evaluation closedEvaluation;
        private boolean attempted;
        private boolean sourceQualificationAttempted;
        private final java.util.Set<RootColdStageReview.Stage> stageAttempts = java.util.EnumSet.noneOf(RootColdStageReview.Stage.class);
        private RetainedSession(Committed committed, ClosedAdoptionMaterial.CurrentSource current, Runnable rootScope, SavedProofReadTicket ticket,
                WindowsFileWriterSession.Settings settings, Evaluation closedEvaluation) {
            this.closedEvaluation = Objects.requireNonNull(closedEvaluation);
            this.committed = committed; this.current = Objects.requireNonNull(current);
            this.rootScope = Objects.requireNonNull(rootScope); this.ticket = Objects.requireNonNull(ticket); this.settings = settings;
        }
        void requireRetainedScope() {
            StrictJson.require(Thread.currentThread() == owner && java.time.Instant.now().isBefore(settings.leaseDeadline()),
                    "same live Root writer continuation within its original finite lease");
            rootScope.run();
        }
        private Evaluation requireCurrent() {
            requireRetainedScope();
            Evaluation fresh = evaluate(current.current());
            StrictJson.require(fresh.candidate().inputDigest().equals(committed.inputDigest())
                    && fresh.businessDigest().equals(committed.businessDigest())
                    && StrictJson.parse(fresh.candidate().committedState()).equals(committed.head().value()),
                    "fresh actual reducer/SDK/source qualification still binds the original committed result");
            return fresh;
        }
        void requireCommitted(Committed expected) {
            StrictJson.require(Thread.currentThread() == owner && committed == expected,
                    "same non-reconstructed actual original writer completion");
        }
        NativeProgramSources nativeProgramSources(java.nio.file.Path runtime, ExactRef plan, ExactRef quote,
                ExactRef basis, ExactRef qualification) throws IOException {
            requireRetainedScope();
            return NativeProgramSources.fromActualPrepared(ticket,runtime,plan,quote,basis,qualification);
        }
        <T> T withNativeOwnerReadLock(ClosedInputsSessionAuthority authority, int preparedSequence,
                WindowsJobProcess.OwnedStdioSpec spec, NativeOwnerResumeSession.OwnerCreation<T> creation)
                throws IOException, InterruptedException {
            Objects.requireNonNull(creation); Objects.requireNonNull(spec);
            StrictJson.require(!attempted && !spec.deadline().isAfter(authority.deadline())
                    && !spec.deadline().isAfter(settings.leaseDeadline())
                    && spec.command().executable().equals(settings.python()), "one finite original writer handoff using its actual approved interpreter");
            attempted = true;
            return withHandoff(authority,preparedSequence,java.util.Optional.of(spec),java.util.Optional.empty(),creation);
        }
        <T> T withColdStageOwnerReadLock(ClosedInputsSessionAuthority authority,int sequence,RootColdStageReview.Reviewed reviewed,
                WindowsJobProcess.OwnedStdioSpec spec,NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException,InterruptedException {
            requireRetainedScope();
            StrictJson.require(reviewed.stage()==RootColdStageReview.Stage.MCP_OWNER && spec.command().executable().equals(settings.python())
                    && !spec.deadline().isAfter(authority.deadline()) && !spec.deadline().isAfter(settings.leaseDeadline())
                    && stageAttempts.add(reviewed.stage()),"same finite approved interpreter and once real MCP stage");
            return withHandoff(authority,sequence,java.util.Optional.of(spec),java.util.Optional.of(reviewed),creation);
        }
        <T> T withColdStageReadLock(ClosedInputsSessionAuthority authority, int preparedSequence,
                RootColdStageReview.Reviewed reviewed, NativeOwnerResumeSession.OwnerCreation<T> creation)
                throws IOException, InterruptedException {
            Objects.requireNonNull(reviewed); Objects.requireNonNull(creation); requireRetainedScope();
            StrictJson.require(java.util.Set.of(RootColdStageReview.Stage.SAVED_GAME_CREATE,RootColdStageReview.Stage.MOD_ABSENCE_ROOT_REVIEW,
                    RootColdStageReview.Stage.INJECT).contains(reviewed.stage()),"only Game/Mod/Inject use generic cold-stage path; MCP requires approved OwnedSpec and raw/postCAP require actual fresh SDK contexts");
            StrictJson.require(!reviewed.command().deadline().isAfter(authority.deadline())
                    && !reviewed.command().deadline().isAfter(settings.leaseDeadline()) && stageAttempts.add(reviewed.stage()),
                    "one independently reviewed finite submission for this exact cold stage; UNKNOWN never replays");
            return withHandoff(authority,preparedSequence,java.util.Optional.empty(),java.util.Optional.of(reviewed),creation);
        }
        java.util.List<org.xar.ck3.control.build.ControlBuild.FileRef> qualifyProgramSources(
                ClosedInputsSessionAuthority authority, int preparedSequence) throws IOException, InterruptedException {
            requireRetainedScope(); StrictJson.require(!sourceQualificationAttempted,"one original locked source qualification");
            sourceQualificationAttempted = true;
            return withHandoff(authority,preparedSequence,java.util.Optional.empty(),java.util.Optional.empty(),
                    () -> authority.approvedNativeProgramSourcesUnderLock(preparedSequence));
        }
        SavedProofReadTicket originalReadTicket() { requireRetainedScope(); return ticket; }
        org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator newColdRestoreMeasurementCoordinator() {
            requireRetainedScope();
            return new org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator(
                    new org.xar.ck3.control.wave2.runtime.savedproof.WindowsJobSdkMeasurementRunner(settings.capacityGuard()),
                    new org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader());
        }
        <T> T withColdRawReadLock(ClosedInputsSessionAuthority authority,int sequence,ColdRawRestoreQualification actual,
                NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException,InterruptedException {
            requireRetainedScope(); StrictJson.require(stageAttempts.add(RootColdStageReview.Stage.RAW_PREFLIGHT),"one actual post-HELLO original lock admission; UNKNOWN never replays");
            return withHandoff(authority,sequence,java.util.Optional.empty(),java.util.Optional.empty(),java.util.Optional.of(actual),creation);
        }
        <T> T withColdCapabilitiesReadLock(ClosedInputsSessionAuthority authority,int sequence,ColdRawRestoreQualification actual,
                NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException,InterruptedException {
            requireRetainedScope();StrictJson.require(stageAttempts.add(RootColdStageReview.Stage.CAPABILITIES_POSTSTATE),"one actual independent post-CAP original writer-lock qualification");
            return withHandoff(authority,sequence,java.util.Optional.empty(),java.util.Optional.empty(),java.util.Optional.of(actual),creation);
        }
        CampaignScoreJunction.Prepared withPreparationReadLock(ClosedInputsSessionAuthority authority,
                OriginalColdConsumerSession.PrepareJunction operation,RootNativeMapMaterializer.JunctionScope scope) throws IOException,InterruptedException {
            requireRetainedScope();authority.requireJunctionInputs(scope);
            return withHandoff(authority,0,java.util.Optional.empty(),java.util.Optional.empty(),java.util.Optional.empty(),
                    java.util.Optional.of(scope),()->scope.prepareJavaInsideOriginalLock(authority,operation));
        }
        private <T> T withHandoff(ClosedInputsSessionAuthority authority, int preparedSequence,
                java.util.Optional<WindowsJobProcess.OwnedStdioSpec> ownerSpec,
                java.util.Optional<RootColdStageReview.Reviewed> stage,
                NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException, InterruptedException {
            return withHandoff(authority,preparedSequence,ownerSpec,stage,java.util.Optional.empty(),creation);
        }
        private <T> T withHandoff(ClosedInputsSessionAuthority authority,int preparedSequence,
                java.util.Optional<WindowsJobProcess.OwnedStdioSpec> ownerSpec,
                java.util.Optional<RootColdStageReview.Reviewed> stage,java.util.Optional<ColdRawRestoreQualification> raw,
                NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException,InterruptedException {
            return withHandoff(authority,preparedSequence,ownerSpec,stage,raw,java.util.Optional.empty(),creation);
        }
        private <T> T withHandoff(ClosedInputsSessionAuthority authority,int preparedSequence,
                java.util.Optional<WindowsJobProcess.OwnedStdioSpec> ownerSpec,
                java.util.Optional<RootColdStageReview.Reviewed> stage,java.util.Optional<ColdRawRestoreQualification> raw,
                java.util.Optional<RootNativeMapMaterializer.JunctionScope> preparation,
                NativeOwnerResumeSession.OwnerCreation<T> creation) throws IOException,InterruptedException {
            if(preparation.isPresent()) {
                StrictJson.require(ownerSpec.isEmpty() && stage.isEmpty() && raw.isEmpty(),"preparation cannot borrow Native/Prepared authority");
                authority.requireJunctionInputs(preparation.orElseThrow());
            } else { authority.requireNativeOwnerInputs(preparedSequence); }
            Evaluation fresh;
            if (raw.isPresent()) { raw.orElseThrow().requireCurrent(); fresh=closedEvaluation; }
            else { fresh=requireCurrent(); }
            WindowsFileWriterSession process = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.WRITER);
            try {
                String nonce = UUID.randomUUID().toString().replace("-","");
                String machine = fresh.material().input().machineId();
                var request = StrictJson.object(); request.put("schema","xar.java-original-writer-handoff-request/v1");
                request.put("machine_id",machine); request.put("canonical_path",committed.target().canonicalPath().toString());
                request.set("writer_source_ref",committed.target().originalWriter().toJson());
                request.set("expected_committed",committed.head().value()); request.put("source_key",fresh.candidate().sourceKey());
                request.put("input_digest",committed.inputDigest()); request.put("session_nonce",nonce); send(process.stdin(),request);
                var locked = StrictJson.object(read(process.stdout()),Set.of("schema","machine_id","writer_source_ref",
                        "canonical_path","input_digest","session_nonce","readback"));
                equal(locked,"schema","xar.java-original-writer-handoff-locked/v1"); equal(locked,"machine_id",machine);
                equal(locked,"session_nonce",nonce); equal(locked,"input_digest",committed.inputDigest());
                StrictJson.require(ExactRef.fromJson(locked.get("writer_source_ref")).equals(committed.target().originalWriter())
                        && Path.of(text(locked,"canonical_path")).equals(committed.target().canonicalPath()), "same original writer handoff target/source");
                var outputs = StrictJson.object(locked.get("readback"),Set.of("head","event","index"));
                Document head = Document.decode(outputs.get("head")), event = Document.decode(outputs.get("event")), index = Document.decode(outputs.get("index"));
                Evaluation insideLock;
                if (raw.isPresent()) { raw.orElseThrow().requireCurrent(); insideLock=closedEvaluation; }
                else { insideLock=requireCurrent(); }
                validateReadback(committed.target(),insideLock,head,event,index);
                sameOriginalDocument(head,committed.head()); sameOriginalDocument(event,committed.event()); sameOriginalDocument(index,committed.index());
                if(preparation.isEmpty()) { authority.approvedNativeProgramSourcesUnderLock(preparedSequence); }
                if (ownerSpec.isPresent() || stage.isPresent() || raw.isPresent()) {
                    authority.requireNativeRestoreSourcePurposeUnderLock(preparedSequence);
                }
                if (ownerSpec.isPresent()) {
                    var spec = ownerSpec.orElseThrow();
                    // Reject unapproved paths before any program-source read; never hash caller-selected persistence.
                    authority.verifyNativeProgramSources(preparedSequence,spec);
                    var verifier = insideLock.material().sourceVerifier(); var executable = spec.executableRef();
                    verifier.verify(new ExactRef(executable.path(),executable.bytes(),executable.sha256()));
                    for (var source : spec.programSourceRefs()) { verifier.verify(new ExactRef(source.path(),source.bytes(),source.sha256())); }
                }
                if(preparation.isPresent()) {
                    authority.requireJunctionInputs(preparation.orElseThrow());
                    preparation.orElseThrow().consumeInsideOriginalLock(authority);
                } else { authority.requireNativeOwnerInputs(preparedSequence); }
                if (stage.isPresent()) {
                    var actual = stage.orElseThrow(); actual.requireCurrent(); actual.consumeImmediatelyBeforeSubmission();
                }
                if (raw.isPresent()) { raw.orElseThrow().consumeReviewInsideLock(); }
                // This is an execution callback, not a caller-supplied qualification predicate.
                T ownerResult = creation.create();
                if(preparation.isPresent()) {
                    // Fresh real reducer/SDK/source proof still binds the same committed head while its original lock is held.
                    requireCurrent();authority.requireJunctionInputs(preparation.orElseThrow());
                    preparation.orElseThrow().requireJavaPhysicalCurrent(authority);
                }
                var release = StrictJson.object(); release.put("schema","xar.java-original-writer-handoff-release/v1");
                release.put("machine_id",machine); release.put("session_nonce",nonce); release.put("input_digest",committed.inputDigest());
                release.put("release",true); send(process.stdin(),release);
                var released = StrictJson.object(read(process.stdout()),Set.of("schema","machine_id","session_nonce","input_digest",
                        "original_actions_replayed","ledger_modified","raw_pending_modified"));
                equal(released,"schema","xar.java-original-writer-handoff-released/v1"); equal(released,"machine_id",machine);
                equal(released,"session_nonce",nonce); equal(released,"input_digest",committed.inputDigest());
                for (String field : Set.of("original_actions_replayed","ledger_modified","raw_pending_modified")) {
                    SettledQueryClassifier.falseValue(released.get(field));
                }
                process.closeOwnedInput(); ActualExit exit = process.awaitActualExit();
                StrictJson.require(exit.kernelExitObserved() && exit.exitCode() == 0
                        && process.actualCommandResult().orElseThrow().passed(),
                        "handoff actual process exit zero and Job zero before any Native hello or capabilities");
                if(preparation.isPresent()) { preparation.orElseThrow().recordHandoff(authority,process); }
                return ownerResult;
            } catch (IOException | InterruptedException | RuntimeException | Error error) {
                OriginalProcessCleanup.suppressing(process,error);
                if(stage.isPresent() && raw.isEmpty() && !(error instanceof InterruptedException) && !(error instanceof Error)
                        && error.getSuppressed().length==0 && process.actualCommandResult().isPresent()
                        && process.actualCommandResult().orElseThrow().accounting().activeProcesses()==0
                        && !authority.coldStageSubmitted(stage.orElseThrow().stage())) {
                    var known=stage.orElseThrow().stage();stageAttempts.remove(known);throw new ColdStageNotSubmitted(known,error);
                }
                throw error;
            }
        }
        private static void sameOriginalDocument(Document actual, Document original) {
            StrictJson.require(actual.evidence().reference().equals(original.evidence().reference())
                    && actual.identity().equals(original.identity())
                    && java.util.Arrays.equals(actual.evidence().bytes(),original.evidence().bytes()),
                    "handoff preserves exact original committed bytes and native file identity");
        }
    }
    public static Evaluation evaluate(ClosedAdoptionMaterial material) {
        String business = ClosedPartialBusinessAuthority.verify(material.input(), material.sources(), material.business(), material.sourceVerifier());
        ClosedPartialAdmissionVerifier provider = new ClosedPartialAdmissionVerifier(material.sources(), material.publishedEpoch(),
                material.publishedPrefix(), material.originalSdk());
        String digest = ClosedFailureRecoveryReducer.inputDigest(material.input());
        RecoveryPrerequisiteVerifier.Check checked = provider.verify(material.input(), digest);
        if (checked instanceof RecoveryPrerequisiteVerifier.Unavailable missing) { throw new ContractViolationException("UNAVAILABLE: " + missing.reason()); }
        if (checked instanceof RecoveryPrerequisiteVerifier.Rejected rejected) { throw new ContractViolationException(rejected.reason()); }
        if (!(checked instanceof RecoveryPrerequisiteVerifier.Verified proof)) { throw new IllegalStateException("proof branch"); }
        RecoveryPreview result = ClosedFailureRecoveryReducer.preview(material.input(), (sameInput, sameDigest) -> {
            StrictJson.require(sameInput.equals(material.input()) && sameDigest.equals(digest), "scoped current Java prerequisite proof");
            return proof;
        });
        if (result instanceof RecoveryPreview.Unavailable missing) { throw new ContractViolationException("UNAVAILABLE: " + missing.reason()); }
        if (result instanceof RecoveryPreview.Rejected rejected) { throw new ContractViolationException(rejected.reason()); }
        if (!(result instanceof RecoveryPreview.Candidate candidate)) { throw new IllegalStateException("recovery branch"); }
        return new Evaluation(material, candidate, business, proof);
    }

    public static Committed execute(Target target, ClosedAdoptionMaterial.CurrentSource current, ManagedLauncher launcher)
            throws IOException, InterruptedException {
        return execute(target,current,launcher,ignored -> { });
    }
    public static Committed execute(Target target, ClosedAdoptionMaterial.CurrentSource current, ManagedLauncher launcher,
            LockedRecheck lockedRecheck) throws IOException, InterruptedException {
        Objects.requireNonNull(lockedRecheck);
        Evaluation preflight = evaluate(current.current()); ManagedProcess process = launcher.start(target);
        try { return run(target, current, process, preflight,lockedRecheck); }
        catch (IOException | InterruptedException | RuntimeException | Error error) {
            OriginalProcessCleanup.suppressing(process,error);
            throw error;
        }
    }
    private static Committed run(Target target, ClosedAdoptionMaterial.CurrentSource current, ManagedProcess process, Evaluation preflight,
            LockedRecheck lockedRecheck)
            throws IOException, InterruptedException {
        RecoveryPreview.Candidate candidate = preflight.candidate();
        ObjectNode start = StrictJson.object(); start.put("schema", "xar.java-original-closed-partial-writer-request/v1");
        start.put("machine_id", preflight.material().input().machineId()); start.put("canonical_path", target.canonicalPath().toString());
        start.set("writer_source_ref", target.originalWriter().toJson()); start.put("kind", "repair_required");
        start.set("details", StrictJson.parse(candidate.details()));
        start.set("expected_predecessor", StrictJson.parse(preflight.material().input().predecessor().bytes()));
        start.set("expected_reduced", StrictJson.parse(candidate.reducedState())); start.set("expected_committed", StrictJson.parse(candidate.committedState()));
        start.put("input_digest", candidate.inputDigest()); send(process.stdin(), start);
        ObjectNode locked = StrictJson.object(read(process.stdout()), Set.of("schema", "machine_id", "writer_source_ref", "canonical_path",
                "previous", "kind", "details", "input_digest"));
        equal(locked, "schema", "xar.java-original-writer-locked/v1"); equal(locked, "machine_id", preflight.material().input().machineId());
        equal(locked, "input_digest", candidate.inputDigest()); equal(locked, "kind", "repair_required");
        StrictJson.require(ExactRef.fromJson(locked.get("writer_source_ref")).equals(target.originalWriter())
                && Path.of(text(locked, "canonical_path")).equals(target.canonicalPath())
                && locked.get("details").equals(StrictJson.parse(candidate.details())), "original locked target/source/details");
        Evaluation again = evaluate(current.current());
        StrictJson.require(again.businessDigest().equals(preflight.businessDigest())
                && java.util.Arrays.equals(again.candidate().details(), candidate.details())
                && java.util.Arrays.equals(again.candidate().committedState(), candidate.committedState()),
                "same actual source and SDK cache qualification under the original writer lock");
        JsonNode previous = locked.get("previous");
        boolean repeated = previous.equals(StrictJson.parse(candidate.committedState()));
        StrictJson.require(repeated || previous.equals(StrictJson.parse(preflight.material().input().predecessor().bytes())),
                "actual canonical predecessor changed after preflight");
        lockedRecheck.verify(target);
        ObjectNode decision = StrictJson.object(); decision.put("schema", "xar.java-original-writer-locked-decision/v1"); decision.put("approved", true);
        decision.set("expected_predecessor", previous); decision.set("expected_reduced", StrictJson.parse(candidate.reducedState()));
        decision.set("expected_committed", StrictJson.parse(candidate.committedState())); decision.put("input_digest", candidate.inputDigest());
        send(process.stdin(), decision);
        ObjectNode completed = StrictJson.object(read(process.stdout()), Set.of("schema", "machine_id", "writer_source_ref", "input_digest",
                "lock_callbacks", "readback", "original_actions_replayed", "raw_pending_modified"));
        equal(completed, "schema", "xar.java-original-closed-partial-writer-readback/v1");
        equal(completed, "machine_id", preflight.material().input().machineId()); equal(completed, "input_digest", candidate.inputDigest());
        StrictJson.require(ExactRef.fromJson(completed.get("writer_source_ref")).equals(target.originalWriter()), "original actual readback writer program");
        StrictJson.integer(completed.get("lock_callbacks"), 1, 1);
        SettledQueryClassifier.falseValue(completed.get("original_actions_replayed")); SettledQueryClassifier.falseValue(completed.get("raw_pending_modified"));
        ObjectNode outputs = StrictJson.object(completed.get("readback"), Set.of("head", "event", "index"));
        Document head = Document.decode(outputs.get("head")), event = Document.decode(outputs.get("event")), index = Document.decode(outputs.get("index"));
        validateReadback(target, preflight, head, event, index);
        process.closeOwnedInput(); ActualExit exit = process.awaitActualExit();
        StrictJson.require(exit.kernelExitObserved() && exit.exitCode() == 0, "original writer actual process exit zero, not transport ACK");
        return new Committed(target, head, event, index, exit, candidate.inputDigest(), preflight.businessDigest(), repeated);
    }
    static void validateReadback(Target target, Evaluation evaluated, Document head, Document event, Document index) {
        RecoveryPreview.Candidate plan = evaluated.candidate();
        StrictJson.require(Path.of(head.evidence().reference().path()).equals(target.canonicalPath())
                && head.value().equals(StrictJson.parse(plan.committedState())), "actual canonical readback equals Java and original reducer");
        ObjectNode actualEvent = event.value(), actualIndex = index.value();
        StrictJson.integer(actualEvent.get("sequence"), plan.expectedSequence() + 1, plan.expectedSequence() + 1);
        equal(actualEvent, "kind", "repair_required"); equal(actualEvent, "identity", plan.eventIdentity());
        equal(actualEvent, "previous_sha256", plan.predecessorDigest());
        StrictJson.require(actualEvent.get("details").equals(StrictJson.parse(plan.details()))
                && actualEvent.get("after").equals(head.value()), "actual immutable original event after/details");
        StrictJson.integer(actualIndex.get("sequence"), plan.expectedSequence() + 1, plan.expectedSequence() + 1); equal(actualIndex, "identity", plan.eventIdentity());
        Path events = target.canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
        StrictJson.require(Path.of(event.evidence().reference().path()).equals(events.resolve(String.format(java.util.Locale.ROOT, "%08d.json", plan.expectedSequence() + 1)))
                && Path.of(index.evidence().reference().path()).equals(events.resolve("source-" + plan.sourceKey() + ".json")), "original event/source index exact paths");
    }
    static void send(OutputStream output, ObjectNode value) throws IOException { output.write(ClosedAdoptionJson.encode(value, MAX_PROTOCOL_BYTES)); output.write('\n'); output.flush(); }
    static JsonNode read(InputStream input) throws IOException {
        return StrictJson.parse(readFrame(input),MAX_PROTOCOL_BYTES);
    }
    /** Complete original UTF-8 frame body, excluding its transport newline; never a tree re-encoding. */
    static byte[] readFrame(InputStream input) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        for (int count = 0; count <= MAX_PROTOCOL_BYTES; count++) {
            int value = input.read(); if (value < 0) { throw new IOException("original writer exited before complete protocol line"); }
            if (value == '\n') { byte[] raw = bytes.toByteArray(); StrictJson.parse(raw,MAX_PROTOCOL_BYTES); return raw; } bytes.write(value);
        }
        throw new IOException("original writer protocol line exceeds finite 256 KiB transport bound");
    }
    private static ObjectNode object(JsonNode node) { return SettledQueryClassifier.object(node); }
    private static String text(ObjectNode row, String field) { return SettledQueryClassifier.text(row, field); }
    private static void equal(ObjectNode row, String field, String expected) { SettledQueryClassifier.equal(row, field, expected); }
}
