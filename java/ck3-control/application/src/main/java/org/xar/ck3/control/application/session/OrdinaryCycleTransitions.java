package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionEffects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineObservation;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.RestoreBinding;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.RestoreSeedSupplement;
import org.xar.ck3.control.application.readiness.ReadinessArchive;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleProofMaterialJson;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Actual canonical AUTO receipt + fresh archived SEM. The original writer alone publishes state. */
public final class OrdinaryCycleTransitions implements WriterContracts.TransitionAuthority {
    public static final String CYCLE_KIND = WriterContracts.ORDINARY_CYCLE_KIND;
    public static final String BATCH_KIND = WriterContracts.ORDINARY_BATCH_KIND;
    public static final String NEXT_BASELINE_KIND = WriterContracts.ORDINARY_NEXT_BASELINE_KIND;
    private static final String NEXT_ORIGIN_SCHEMA = "xar.java-ordinary-next-window-origin/v1";
    public static final String STATE_FIELD = WriterContracts.ORDINARY_CYCLE_FIELD;
    private static final String STATE_SCHEMA = "xar.java-ordinary-cycle-state/v2";
    private static final String RECORD_SCHEMA = "xar.java-ordinary-cycle-record/v1";
    private static final String RESTORE_SOURCE = "java-ordinary-source-bound-restore/v1";
    private static final String IMPORTED_RESTORE_SOURCE = WriterContracts.ORDINARY_IMPORTED_CYCLE_RESTORE_SOURCE;
    private static final int MAX_RECORDS = 100_000;
    private static final String SAVED_MATERIAL_SOURCE = "java-ordinary-session/v2";
    private final ActionPorts.OutcomeArchive archive;
    private final SemanticVerifier semanticVerifier;
    private final CheckpointVerifier checkpointVerifier;
    private final OriginalWindowReducer.Policy policy;
    private final SessionAuthority sessionAuthority;
    private volatile NativeEffectEvidence.FrameLoader terminalFrames;
    private volatile OperatorAuthority operatorAuthority;
    @FunctionalInterface public interface OperatorRetirementVerifier {
        void verify(ContinuityStorePort.Session same,WriterContracts.Head head,ActionReceipt retired)throws IOException;
    }
    private volatile OperatorRetirementVerifier operatorRetirementVerifier;
    public synchronized void bindOperatorRetirementVerifier(OperatorRetirementVerifier actual) {
        StrictJson.require(operatorRetirementVerifier==null,"actual operator retirement verifier installs once");operatorRetirementVerifier=Objects.requireNonNull(actual);
    }
    private static final String OPERATOR_ORIGIN_SCHEMA="xar.java-ordinary-operator-origin/v1";
    private static final String TRANSPORT_ORIGIN_SCHEMA="xar.java-ordinary-transport-origin/v1";
    private volatile SameGameTransportContinuity.Port transportRebindPort;
    private record SettledObservation(SessionIdentity owner, String cycleStateDigest, ObservationIdentity frame) { }
    private volatile SettledObservation settledObservation;
    private record TransportContext(SameGameTransportContinuity.Scope scope,SameGameTransportContinuity.Evidence evidence) { }
    private final ThreadLocal<TransportContext> transportContext=new ThreadLocal<>();
    private record SavedSettledContext(ContinuityStorePort.Session same, ContinuityBatchJournal.SavedSettledHistory role, ContinuityBatchJournal.SettledSameGameData data) { }
    private final ThreadLocal<SavedSettledContext> savedSettledContext = new ThreadLocal<>();
    /** The actual Root installs its sole NS/M3 adapter, never a caller-provided DATA proof. */
    public synchronized void bindTransportRebindPort(SameGameTransportContinuity.Port actual) {
        StrictJson.require(transportRebindPort==null,"actual same-Game transport port is installed once");
        transportRebindPort=Objects.requireNonNull(actual);
    }
    @FunctionalInterface public interface OperatorAuthority {
        void requireCurrent(ContinuityStorePort.Session same,SessionIdentity owner,ActionReceipt actual,SemanticEvidence semantic)throws IOException;
    }
    /** Installed by the actual Root constructor, never supplied by an action caller. */
    public synchronized void bindOperatorAuthority(OperatorAuthority actual){
        StrictJson.require(operatorAuthority==null,"actual operator cycle authority is installed once");operatorAuthority=Objects.requireNonNull(actual);
    }
    private final ThreadLocal<ContinuityStorePort.Session> active = new ThreadLocal<>();
    private final ThreadLocal<RestoreBinding> restoring = new ThreadLocal<>();
    private final ThreadLocal<CommittedImportedRebind> committedImportedRebinding = new ThreadLocal<>();
    private volatile CommittedImportedRebindAuthority committedImportedRebindAuthority;
    private volatile CommittedImportedSettledReadAuthority committedImportedSettledReadAuthority;
    private volatile CommittedImportedSavedMaterialReader committedImportedSavedMaterialReader;

    /** Root reopens only the original immutable manifest and retained SAVE originals on the held Writer. */
    @FunctionalInterface public interface CommittedImportedSavedMaterialReader {
        org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore.SavedMaterial read(ContinuityStorePort.Session same,
                org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence evidence) throws IOException;
    }
    public synchronized void bindCommittedImportedSavedMaterialReader(CommittedImportedSavedMaterialReader actual) {
        StrictJson.require(committedImportedSavedMaterialReader == null, "settled imported SAVE material reader installs once");
        committedImportedSavedMaterialReader = Objects.requireNonNull(actual);
    }
    org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore.SavedMaterial readCommittedImportedSavedMaterial(
            ContinuityStorePort.Session same, org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence evidence) throws IOException {
        StrictJson.require(active.get() == same, "settled imported SAVE material requires the actual locked Writer");
        var reader = committedImportedSavedMaterialReader;
        if (reader == null) throw new IOException("settled imported SAVE requires its installed retained material reader");
        return Objects.requireNonNull(reader.read(same, evidence));
    }

    /** Installed Root supplies the exact independently read Native Full, verified under its current receiver custody. */
    @FunctionalInterface public interface CommittedImportedSettledReadAuthority {
        ObservedFrame requireCurrent(ContinuityStorePort.Session same, ContinuityBatchJournal.SettledSameGameData data,
                SemanticEvidence fresh) throws IOException;
    }
    public synchronized void bindCommittedImportedSettledReadAuthority(CommittedImportedSettledReadAuthority actual) {
        StrictJson.require(committedImportedSettledReadAuthority == null, "settled imported current READ authority installs once");
        committedImportedSettledReadAuthority = Objects.requireNonNull(actual);
    }


    /** Root's actual newly adopted Driver and independent current paused, living, map-ready SEM. */
    @FunctionalInterface public interface CommittedImportedRebindAuthority {
        void requireCurrent(ContinuityStorePort.Session same,ContinuityBatchJournal.ImportedRestoreRebindReadback attachment,
                SemanticEvidence fresh)throws IOException;
    }
    public synchronized void bindCommittedImportedRebindAuthority(CommittedImportedRebindAuthority actual) {
        StrictJson.require(committedImportedRebindAuthority==null,"actual committed imported REBIND authority installs once");
        committedImportedRebindAuthority=Objects.requireNonNull(actual);
    }
    private record CommittedImportedRebind(ContinuityBatchJournal.ImportedRestoreRebindReadback attachment,
            SemanticEvidence fresh,WriterContracts.Pin seedPin,RawJson tombstone,String predecessorDigest,String requestIdentity,VerifiedSemantic verified) { }

    private record EpisodeContext(LifecycleEpisodeInputs inputs,LifecycleEpisodeInputs.Binding binding) { }
    private final ThreadLocal<EpisodeContext> episode = new ThreadLocal<>();
    private record NextBaselineContext(LifecycleEpisodeInputs inputs,LifecycleEpisodeInputs.NextBaselineBinding binding) { }
    private final ThreadLocal<NextBaselineContext> nextBaseline = new ThreadLocal<>();

    /** Evidence identity describes an archive read; it is never invented as a native request ID. */
    public record VerifiedSemantic(ObservationIdentity frame, Instant observedAt, String semanticEvidenceId, String materialDigest) {
        public VerifiedSemantic {
            Objects.requireNonNull(frame); Objects.requireNonNull(observedAt); StrictJson.text(semanticEvidenceId);
            WriterContracts.requireDigest(materialDigest);
        }
    }
    @FunctionalInterface public interface SemanticVerifier {
        VerifiedSemantic verify(ContinuityStorePort.Session actualLockedSession, SessionIdentity session, SemanticEvidence semantic) throws IOException;
    }
    /** Original capture DATA only; constructing this result grants no SAVE or writer authority. */
    public record CheckpointCaptureResult(String digest, Optional<org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence> material) {
        public CheckpointCaptureResult { WriterContracts.requireDigest(digest); Objects.requireNonNull(material); }
    }
    @FunctionalInterface public interface CheckpointVerifier {
        String verify(ContinuityStorePort.Session actualLockedSession, SessionIdentity session, CheckpointPair pair, CompletedCycleProof proof) throws IOException;
        /** Legacy producers retain their complete verification with explicit absence of captured material. */
        default CheckpointCaptureResult verifyMaterialCapture(ContinuityStorePort.Session actualLockedSession,
                SessionIdentity session, CheckpointPair pair, CompletedCycleProof proof) throws IOException {
            return new CheckpointCaptureResult(verify(actualLockedSession, session, pair, proof), Optional.empty());
        }
    }
    /** Root passes its sole ContinuityWriter::requireSession, including actual writer-object ownership. */
    @FunctionalInterface public interface SessionAuthority {
        void require(ContinuityStorePort.Session actualLockedSession) throws IOException;
    }
    @FunctionalInterface interface LockedWork<T> { T run() throws IOException; }
    public OrdinaryCycleTransitions(ActionPorts.OutcomeArchive archive, SemanticVerifier semanticVerifier,
            CheckpointVerifier checkpointVerifier, OriginalWindowReducer.Policy policy, SessionAuthority sessionAuthority) {
        this.archive = Objects.requireNonNull(archive); this.semanticVerifier = Objects.requireNonNull(semanticVerifier);
        this.checkpointVerifier = Objects.requireNonNull(checkpointVerifier); this.policy = Objects.requireNonNull(policy);
        this.sessionAuthority = Objects.requireNonNull(sessionAuthority);
    }
    /** Root binds its one actual native/Driver evidence loader before installing this cycle authority. */
    public synchronized void bindTerminalFrameLoader(NativeEffectEvidence.FrameLoader actualLoader) {
        Objects.requireNonNull(actualLoader);
        StrictJson.require(terminalFrames == null, "the actual cycle terminal frame loader is installed once");
        terminalFrames = actualLoader;
    }

    /** Distinct operator retirement recovery. It never describes the old action as no-dispatch or no-effect. */
    static final String OPERATOR_QUARANTINE_RECOVERY_OPERATION="OPERATOR_QUARANTINE_RECOVERY";
    static final String OPERATOR_QUARANTINE_RECOVERY_FIELD="java_operator_quarantine_recovery";
    static final String OPERATOR_LIFE_INTERRUPTION_OPERATION="OPERATOR_LIFE_INTERRUPTION_RECOVERY";
    static final String OPERATOR_LIFE_INTERRUPTION_FIELD="java_operator_life_interruption_recovery";
    private record OperatorQuarantineContext(ContinuityBatchJournal.OperatorQuarantineRecovery admission,SemanticEvidence semantic,byte[] details) { }
    private final ThreadLocal<OperatorQuarantineContext> operatorQuarantineContext=new ThreadLocal<>();
    WriterContracts.Receipt commitOperatorQuarantineRecovery(ContinuityStorePort.Session same,
            ContinuityBatchJournal.OperatorQuarantineRecovery admission,SemanticEvidence semantic)throws IOException {
        StrictJson.require(active.get()==same&&operatorQuarantineContext.get()==null,"operator recovery requires its unique original journal scope");
        admission.requireCurrent(same);Objects.requireNonNull(semantic);
        ObjectNode row=StrictJson.object();row.put("evidence_id","operator-quarantine-recovery:"+admission.terminalReceipt().command().actionId()+":"+admission.sequence());
        row.put("source",admission.reservedTailInterruption()?"java-operator-life-interruption-recovery/v2":admission.lifeInterruption()?"java-operator-life-interruption-recovery/v1":"java-operator-quarantine-recovery/v1");row.set("session",sessionToJson(admission.owner()));
        row.put("operation",admission.lifeInterruption()?OPERATOR_LIFE_INTERRUPTION_OPERATION:OPERATOR_QUARANTINE_RECOVERY_OPERATION);row.put("predecessor_head_digest",admission.digest());
        row.set("receipt_ref",admission.receiptReference().toJson());row.set("operator_observation",admission.observationReference().toJson());
        row.set("controller_ref",admission.controllerReference().toJson());row.set("retained_driver",admission.retainedDriver().toJson());
        row.put("batch_id",admission.consumedBatchId());row.put("next_sequence",admission.nextBatchSequence());
        var batches=row.putArray("consumed_batches");admission.consumedBatchIds().forEach(batches::add);
        row.set("semantic",semanticToJson(semantic));
        if(admission.reservedTailInterruption()) {row.put("completion_issued_at",admission.completionIssuedAt().toString());row.put("completion_deadline",admission.completionDeadline().toString());}
        byte[] bytes=ContinuityJson.canonical(row);var refs=new ArrayList<ExactRef>(admission.history());refs.addAll(semantic.references());
        var request=new WriterContracts.Request(CYCLE_KIND,bytes,refs.stream().distinct().toList());
        operatorQuarantineContext.set(new OperatorQuarantineContext(admission,semantic,bytes));
        try {var prepared=same.preview(request);var receipt=same.commit(prepared);same.requireCommitted(prepared,receipt);admission.committed(prepared,receipt);return receipt;}
        finally {operatorQuarantineContext.remove();}
    }
    private String revalidateOperatorQuarantineRecovery(ContinuityStorePort.Session same,WriterContracts.Head head,ObjectNode details)throws IOException {
        var context=operatorQuarantineContext.get();StrictJson.require(context!=null,"operator recovery requires its actual private journal admission");
        var admission=context.admission();admission.requireCurrent(same);strictOperatorQuarantineRecovery(details);
        StrictJson.require(java.util.Arrays.equals(context.details(),ContinuityJson.canonical(details))
                &&head.digest().equals(admission.digest()),"operator recovery changed its exact private producer/predecessor");
        admission.requireCanonicalTerminal(same);requireOwner(head.state(),admission.owner());
        if(admission.lifeInterruption())requireOperatorLifeFrontier(head.state(),admission.owner());else requireOperatorQuarantineFrontier(head.state());
        var checked=verify(same,admission.owner(),context.semantic());
        if(admission.lifeInterruption())requireObservedBindingNotRegressed(head.state(),checked.frame());else requireSettledBinding(head.state(),checked.frame());
        var observation=org.xar.ck3.control.application.action.CompositeOperatorQuarantineObservation.load(admission.terminalReceipt(),archive.withSession(same));
        var request=org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest.decode(archive.withSession(same).loadMaterial(observation.requestMaterial()).bytes());
        if(admission.reservedTailInterruption()) {
            StrictJson.require(request.reservedTailInterruption()&&!admission.completionIssuedAt().isBefore(observation.observedAt())
                    &&!checked.observedAt().isBefore(admission.completionIssuedAt())&&checked.observedAt().isBefore(admission.completionDeadline())
                    &&admission.completionCurrent(),"reserved recovery SEM is outside this actual completion observation window");
        } else StrictJson.require(!request.reservedTailInterruption()&&!checked.observedAt().isBefore(request.issuedAt())&&checked.observedAt().isBefore(request.observationDeadline()),
                "operator recovery SEM is outside its distinct decision observation window");
        var proof=StrictJson.object();proof.put("predecessor",head.digest());proof.put("operator_observation",admission.observationReference().sha256());
        proof.put("semantic",checked.materialDigest());proof.put("controller",admission.controllerReference().sha256());return ContinuityJson.digest(proof);
    }
    private ContinuityState reduceOperatorQuarantineRecovery(ContinuityState predecessor,ObjectNode details) {
        strictOperatorQuarantineRecovery(details);var owner=sessionFromJson(details.get("session"));requireOwner(predecessor,owner);
        boolean life=OPERATOR_LIFE_INTERRUPTION_OPERATION.equals(text(details,"operation"));
        if(life)requireOperatorLifeFrontier(predecessor,owner);else requireOperatorQuarantineFrontier(predecessor);
        StrictJson.require(ContinuityJson.digest(predecessor.toJson()).equals(text(details,"predecessor_head_digest")),"operator recovery predecessor changed");
        var semantic=semanticFromJson(details.get("semantic"));if(life)requireObservedBindingNotRegressed(predecessor,semantic.frame());else requireSettledBinding(predecessor,semantic.frame());
        var original=StrictJson.object();original.put("evidence_id",text(details,"evidence_id"));original.set("source",details.get("source"));original.put("machine_id",predecessor.machineId());
        original.put("completed_cycles",life?StrictJson.integer(predecessor.toJson().get(STATE_FIELD).get("completed_cycles"),1,StrictJson.MAX_SAFE_INTEGER):predecessor.settledCycles());original.set("frame",originalFrame(semantic.frame()));
        original.set("session",details.get("session"));original.set("batch_id",details.get("batch_id"));original.set("next_sequence",details.get("next_sequence"));
        original.set("operator_observation",details.get("operator_observation"));
                var next=OriginalWindowReducer.reduce(predecessor.toJson(),life?("java-operator-life-interruption-recovery/v2".equals(text(details,"source"))?"operator_life_reserved_tail_recovery":"operator_life_interruption_recovery"):"operator_quarantine_recovery",original,policy);
        next.set(life?OPERATOR_LIFE_INTERRUPTION_FIELD:OPERATOR_QUARANTINE_RECOVERY_FIELD,details.deepCopy());
        if(life)StrictJson.require(java.util.Objects.equals(next.get(STATE_FIELD),predecessor.toJson().get(STATE_FIELD))
                &&java.util.Objects.equals(next.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),predecessor.toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)),"Life retirement cannot change completed cycle or saved pair credit");
        StrictJson.require(number(next,"last_settled_cycles")==predecessor.settledCycles()&&number(next,"last_settled_date_raw")==predecessor.settledDateRaw(),
                "operator recovery cannot grant or rewind saved/cycle progress");
        return ContinuityState.fromJson(next,predecessor.machineId());
    }
    private static void strictOperatorQuarantineRecovery(ObjectNode row) {
        boolean reserved="java-operator-life-interruption-recovery/v2".equals(text(row,"source"));
        var keys=new java.util.HashSet<String>(Set.of("evidence_id","source","session","operation","predecessor_head_digest","receipt_ref","operator_observation","controller_ref","retained_driver","batch_id","next_sequence","consumed_batches","semantic"));
        if(reserved){keys.add("completion_issued_at");keys.add("completion_deadline");}
        StrictJson.object(row,keys);
        boolean life=OPERATOR_LIFE_INTERRUPTION_OPERATION.equals(text(row,"operation"));
        if(reserved) {
            var issued=java.time.Instant.parse(text(row,"completion_issued_at"));var until=java.time.Instant.parse(text(row,"completion_deadline"));
            var semantic=semanticFromJson(row.get("semantic"));
            StrictJson.require(life&&issued.isBefore(until)&&!until.isAfter(issued.plus(java.time.Duration.ofMinutes(10)))
                    &&!semantic.observedAt().isBefore(issued)&&semantic.observedAt().isBefore(until),"strict reserved completion window required");
        }
        StrictJson.require(life?(reserved||"java-operator-life-interruption-recovery/v1".equals(text(row,"source")))&&number(row,"next_sequence")>=2:
                OPERATOR_QUARANTINE_RECOVERY_OPERATION.equals(text(row,"operation"))&&"java-operator-quarantine-recovery/v1".equals(text(row,"source"))&&number(row,"next_sequence")==1,
                "explicit operator recovery operation/source/batch sequence required");
        JsonNode consumed=row.get("consumed_batches");StrictJson.require(consumed.isArray()&&!consumed.isEmpty(),"operator recovery must retain consumed batch identities");
        if(life) {
            var identities=new java.util.HashSet<String>();for(JsonNode value:consumed)StrictJson.require(identities.add(StrictJson.text(value)),"duplicate consumed operator batch identity");
            StrictJson.require(identities.contains(text(row,"batch_id")),"operator interruption must preserve the original consumed batch; Set iteration order is not batch order");
        } else StrictJson.require(consumed.size()==1&&StrictJson.text(consumed.get(0)).equals(text(row,"batch_id")),"initial operator recovery retains its one original batch");
    }
    /** Pure DATA boundary only; no writer, readiness or native permission is issued. */
    public static void requireOperatorLifeFrontier(ContinuityState state,SessionIdentity owner) {
        requireOwner(state,owner);var whole=state.toJson();var cycle=whole.get(STATE_FIELD);
        StrictJson.require(state.status()==ContinuityState.Status.REPAIR_REQUIRED&&cycle!=null&&cycle.isObject()
                &&sessionFromJson(cycle.get("session")).equals(owner)&&StrictJson.integer(cycle.get("completed_cycles"),1,StrictJson.MAX_SAFE_INTEGER)>=1
                &&cycle.hasNonNull("head")&&cycle.has("pending_receipt")&&cycle.get("pending_receipt").isNull()
                &&whole.hasNonNull(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),"Life interruption requires its real nonzero completed/saved frontier with no pending cycle");
        var boundary=StrictJson.object(whole.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD),Set.of("evidence_id","session","batch_id","boundary"));
        StrictJson.require("BATCH_INTERRUPTED".equals(text(boundary,"boundary"))&&sessionFromJson(boundary.get("session")).equals(owner),"Life operator recovery must consume its exact interrupted batch owner");
        for(String field:List.of("pending_cycle","pending_checkpoint","current_cycle_pending")){var pending=whole.get(field);StrictJson.require(pending==null||pending.isNull(),"Life operator recovery cannot clear pending obligations: "+field);}
    }
    private static void requireOperatorQuarantineFrontier(ContinuityState state) {
        StrictJson.require(state.status()==ContinuityState.Status.REPAIR_REQUIRED&&state.settledCycles()==0,"operator recovery only resumes the unchanged interrupted initial frontier");
        var row=state.toJson();
        for(String field:List.of(WriterContracts.ORDINARY_CYCLE_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,"pending_cycle","pending_checkpoint","current_cycle_pending")) {
            JsonNode value=row.get(field);StrictJson.require(value==null||value.isNull(),"operator recovery cannot discard an existing cycle/SAVE/pending field: "+field);
        }
    }
    private static final String INITIAL_NO_DISPATCH_OPERATION="INITIAL_NO_DISPATCH_RECOVERY";
    private static final String CAPTURED_NO_DISPATCH_OPERATION="CAPTURED_NO_DISPATCH_RECOVERY";
    private record InitialRecoveryContext(ContinuityBatchJournal.InitialNoDispatchRecovery admission,SemanticEvidence semantic) { }
    private final ThreadLocal<InitialRecoveryContext> initialRecoveryContext=new ThreadLocal<>();
    WriterContracts.Receipt commitInitialNoDispatchRecovery(ContinuityStorePort.Session same,
            ContinuityBatchJournal.InitialNoDispatchRecovery admission,SemanticEvidence semantic)throws IOException {
        StrictJson.require(active.get()==same&&initialRecoveryContext.get()==null,"initial recovery requires the unique original journal scope");
        admission.requireCurrent(same);Objects.requireNonNull(semantic);
        ObjectNode row=StrictJson.object();row.put("evidence_id","initial-no-dispatch:"+admission.digest());
        row.put("source",admission.fromCapturedRestart()?"java-captured-no-dispatch-recovery/v1":"java-initial-no-dispatch-recovery/v1");row.set("session",sessionToJson(admission.owner()));
        row.put("operation",admission.fromCapturedRestart()?CAPTURED_NO_DISPATCH_OPERATION:INITIAL_NO_DISPATCH_OPERATION);row.put("predecessor_head_digest",admission.digest());
        row.put("batch_id",admission.consumedBatchId());row.put("next_sequence",admission.nextBatchSequence());row.set("semantic",semanticToJson(semantic));
        var refs=new ArrayList<ExactRef>(admission.history());refs.addAll(semantic.references());
        var request=new WriterContracts.Request(CYCLE_KIND,ContinuityJson.canonical(row),refs.stream().distinct().toList());
        initialRecoveryContext.set(new InitialRecoveryContext(admission,semantic));
        try {var prepared=same.preview(request);var receipt=same.commit(prepared);same.requireCommitted(prepared,receipt);return receipt;}
        finally {initialRecoveryContext.remove();}
    }
    private String revalidateInitialNoDispatchRecovery(ContinuityStorePort.Session same,WriterContracts.Head head,ObjectNode details)throws IOException {
        var context=initialRecoveryContext.get();StrictJson.require(context!=null,"initial recovery needs its actual private journal producer");
        var admission=context.admission();admission.requireCurrent(same);strictInitialNoDispatch(details);
        StrictJson.require(head.digest().equals(admission.digest())&&text(details,"predecessor_head_digest").equals(admission.digest())
                &&sessionFromJson(details.get("session")).equals(admission.owner())&&text(details,"batch_id").equals(admission.consumedBatchId())
                &&number(details,"next_sequence")==admission.nextBatchSequence()
                &&ContinuityJson.same(details.get("semantic"),semanticToJson(context.semantic())),"initial recovery producer/head/input changed");
        var state=head.state();requireOwner(state,admission.owner());
        StrictJson.require(state.status()==ContinuityState.Status.REPAIR_REQUIRED&&(admission.fromCapturedRestart()||state.settledCycles()==0),
                "only the retained interrupted initial frontier can recover");
        StrictJson.require(text(details,"operation").equals(admission.fromCapturedRestart()?CAPTURED_NO_DISPATCH_OPERATION:INITIAL_NO_DISPATCH_OPERATION),
                "captured recovery requires its actual private captured admission");
        if(!admission.fromCapturedRestart())StrictJson.require(ContinuityActionJournal.receipts(state,archive.withSession(same)).isEmpty(),"initial recovery cannot discard canonical actions");
        var checked=verify(same,admission.owner(),context.semantic());
        if(admission.fromCapturedRestart())admission.requireCapturedCurrentFrame(checked.frame());else requireSettledBinding(state,checked.frame());
        var proof=StrictJson.object();proof.put("predecessor",head.digest());proof.put("semantic",checked.materialDigest());proof.put("batch",admission.consumedBatchId());
        return ContinuityJson.digest(proof);
    }
    private ContinuityState reduceInitialNoDispatchRecovery(ContinuityState predecessor,ObjectNode details) {
        strictInitialNoDispatch(details);requireOwner(predecessor,sessionFromJson(details.get("session")));
        boolean captured=CAPTURED_NO_DISPATCH_OPERATION.equals(text(details,"operation"));
        StrictJson.require(predecessor.status()==ContinuityState.Status.REPAIR_REQUIRED&&(captured||predecessor.settledCycles()==0)
                &&ContinuityJson.digest(predecessor.toJson()).equals(text(details,"predecessor_head_digest")),"initial recovery predecessor changed");
        var semantic=semanticFromJson(details.get("semantic"));if(!captured)requireSettledBinding(predecessor,semantic.frame());
        var original=StrictJson.object();original.put("evidence_id",text(details,"evidence_id"));original.set("source",details.get("source"));
        original.put("machine_id",predecessor.machineId());original.put("completed_cycles",predecessor.settledCycles());original.set("frame",originalFrame(semantic.frame()));
        var next=OriginalWindowReducer.reduce(predecessor.toJson(),captured?"captured_no_dispatch_recovery":"initial_no_dispatch_recovery",original,policy);
        StrictJson.require(number(next,"last_settled_cycles")==predecessor.settledCycles()
                &&number(next,"last_settled_date_raw")==predecessor.settledDateRaw(),"initial no-dispatch recovery cannot grant game credit");
        return ContinuityState.fromJson(next,predecessor.machineId());
    }
    /** Replays a previously committed zero-dispatch recovery; it grants no current write permit. */
    void requireInitialNoDispatchHistoryEdge(WriterContracts.HistoricalTransition edge,SessionIdentity owner,String batch,long next) {
        var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES);strictInitialNoDispatch(details);
        StrictJson.require(edge.kind().equals(CYCLE_KIND)&&sessionFromJson(details.get("session")).equals(owner)
                &&text(details,"batch_id").equals(batch)&&number(details,"next_sequence")==next,
                "historical initial recovery crossed its actual failed batch prefix");
        var replay=reduceInitialNoDispatchRecovery(edge.before(),details).toJson();
        replay.put("sequence",edge.sequence());replay.put("last_event_identity",edge.eventIdentity());
        StrictJson.require(ContinuityJson.same(replay,edge.after().toJson()),"historical initial recovery differs from its actual reducer edge");
    }
    private static void strictInitialNoDispatch(ObjectNode row) {
        StrictJson.object(row,Set.of("evidence_id","source","session","operation","predecessor_head_digest","batch_id","next_sequence","semantic"));
        StrictJson.require(Set.of(INITIAL_NO_DISPATCH_OPERATION,CAPTURED_NO_DISPATCH_OPERATION).contains(text(row,"operation"))&&number(row,"next_sequence")>=1,
                "initial no-dispatch recovery operation/frontier differs");
    }

    private static final String SAVED_READ_ONLY_RECOVERY_OPERATION="SAVED_READ_ONLY_RECOVERY";
    private record SavedReadOnlyRecoveryContext(ContinuityBatchJournal.SavedReadOnlyRecovery admission,SemanticEvidence semantic) { }
    private final ThreadLocal<SavedReadOnlyRecoveryContext> savedReadOnlyRecoveryContext=new ThreadLocal<>();
    WriterContracts.Receipt commitSavedReadOnlyRecovery(ContinuityStorePort.Session same,
            ContinuityBatchJournal.SavedReadOnlyRecovery admission,SemanticEvidence semantic)throws IOException {
        StrictJson.require(active.get()==same&&savedReadOnlyRecoveryContext.get()==null,"Saved recovery requires the actual unique Journal scope");
        Objects.requireNonNull(semantic);admission.requireCurrent(same);
        ObjectNode row=StrictJson.object();row.put("evidence_id","saved-read-only:"+admission.digest());
        row.put("source","java-saved-read-only-recovery/v1");row.set("session",sessionToJson(admission.owner()));
        row.put("operation",SAVED_READ_ONLY_RECOVERY_OPERATION);row.put("predecessor_head_digest",admission.digest());
        row.put("batch_id",admission.batch());row.set("semantic",semanticToJson(semantic));row.set("driver_ref",admission.driver().toJson());
        var refs=new ArrayList<ExactRef>(admission.history());refs.addAll(semantic.references());refs.add(admission.driver());
        var request=new WriterContracts.Request(CYCLE_KIND,ContinuityJson.canonical(row),refs.stream().distinct().toList());
        savedReadOnlyRecoveryContext.set(new SavedReadOnlyRecoveryContext(admission,semantic));
        try {var prepared=same.preview(request);var receipt=same.commit(prepared);same.requireCommitted(prepared,receipt);return receipt;}
        finally {savedReadOnlyRecoveryContext.remove();}
    }
    private String revalidateSavedReadOnlyRecovery(ContinuityStorePort.Session same,WriterContracts.Head head,ObjectNode details)throws IOException {
        strictSavedReadOnlyRecovery(details);var context=savedReadOnlyRecoveryContext.get();
        StrictJson.require(context!=null,"Saved recovery needs its actual private Journal source context");
        var actual=context.admission();actual.requireCurrent(same);
        StrictJson.require(head.digest().equals(actual.digest())&&text(details,"predecessor_head_digest").equals(actual.digest())
                &&sessionFromJson(details.get("session")).equals(actual.owner())&&text(details,"batch_id").equals(actual.batch())
                &&ContinuityJson.same(details.get("semantic"),semanticToJson(context.semantic()))
                &&ExactRef.fromJson(details.get("driver_ref")).equals(actual.driver())
                &&context.semantic().originalDriver().equals(actual.driver()),"Saved recovery changed its exact producer/head/current Driver/SEM");
        var checked=verify(same,actual.owner(),context.semantic());
        // The pure reducer also applies the exact same-subject/date/revision/zero-credit Saved guards.
        reduceSavedReadOnlyRecovery(head.state(),details);
        var proof=StrictJson.object();proof.put("head",head.digest());proof.put("semantic",checked.materialDigest());proof.put("batch",actual.batch());
        return ContinuityJson.digest(proof);
    }
    private ContinuityState reduceSavedReadOnlyRecovery(ContinuityState predecessor,ObjectNode details) {
        strictSavedReadOnlyRecovery(details);var owner=sessionFromJson(details.get("session"));requireOwner(predecessor,owner);
        StrictJson.require(ContinuityJson.digest(predecessor.toJson()).equals(text(details,"predecessor_head_digest")),"Saved recovery predecessor changed");
        var original=StrictJson.object();original.put("evidence_id",text(details,"evidence_id"));original.set("source",details.get("source"));
        original.put("machine_id",owner.machineId());original.set("session",details.get("session"));original.put("batch_id",text(details,"batch_id"));
        original.put("completed_cycles",predecessor.settledCycles());original.set("frame",originalFrame(semanticFromJson(details.get("semantic")).frame()));
        original.set("driver_ref",details.get("driver_ref"));original.set("predecessor_head_digest",details.get("predecessor_head_digest"));
        var next=OriginalWindowReducer.reduce(predecessor.toJson(),"saved_read_only_recovery",original,policy);
        var expected=predecessor.toJson();expected.put("status","running");expected.set("latest_binding",original.get("frame"));
        StrictJson.require(ContinuityJson.same(expected,next),"Saved read-only recovery may change only status and actual latest binding");
        return ContinuityState.fromJson(next,predecessor.machineId());
    }
    private static void strictSavedReadOnlyRecovery(ObjectNode row) {
        StrictJson.object(row,Set.of("evidence_id","source","session","operation","predecessor_head_digest","batch_id","semantic","driver_ref"));
        StrictJson.require(SAVED_READ_ONLY_RECOVERY_OPERATION.equals(text(row,"operation"))
                &&"java-saved-read-only-recovery/v1".equals(text(row,"source")),"Saved recovery operation/source differs");
        WriterContracts.requireDigest(text(row,"predecessor_head_digest"));StrictJson.text(row.get("evidence_id"));StrictJson.text(row.get("batch_id"));
        sessionFromJson(row.get("session"));semanticFromJson(row.get("semantic"));ExactRef.fromJson(row.get("driver_ref"));
    }

    private static final String SETTLED_SAME_GAME_OPERATION = "SETTLED_SAME_GAME_RECOVERY";
    private final ThreadLocal<WriterContracts.HistoricalTransition> openReadOnlyRecovery = new ThreadLocal<>();

    /** Consume one actual unfinished read-only batch; its original STARTED fact remains canonical. */
    WriterContracts.Receipt commitSettledSameGameRecovery(ContinuityStorePort.Session same,
            ContinuityBatchJournal.SettledSameGameData data, SemanticEvidence semantic,
            WriterContracts.HistoricalTransition anchor) throws IOException {
        StrictJson.require(active.get() == same && openReadOnlyRecovery.get() == null,
                "unfinished batch recovery requires the original idle recovery writer scope");
        Objects.requireNonNull(anchor);
        openReadOnlyRecovery.set(anchor);
        try { return commitSettledSameGameRecovery(same, data, semantic); }
        finally { openReadOnlyRecovery.remove(); }
    }

    /** Consume this journal's fully verified saved and settled history without replaying an action. */
    Optional<WriterContracts.Receipt> recoverSettledSavedGame(ContinuityStorePort.Session same,
            ContinuityBatchJournal.SettledSameGameData data, SemanticEvidence semantic,
            ContinuityBatchJournal.SavedSettledHistory role) throws IOException {
        StrictJson.require(active.get() == same && savedSettledContext.get() == null,
                "saved settled recovery requires the unique original journal scope");
        Objects.requireNonNull(role); Objects.requireNonNull(data); Objects.requireNonNull(semantic);
        role.requireCurrent(same, data);
        savedSettledContext.set(new SavedSettledContext(same, role, data));
        try {
            var head=same.head();
            var owner=data.controller().owner();
            var branch=state(head.state(),owner);
            boolean open=isOpenReadOnlyBatch(head.state());
            if ((open||isFullySavedBatchBoundary(head.state(),owner,branch))
                    && ContinuityJson.same(head.state().toJson().get("latest_binding"),originalFrame(semantic.frame()))) {
                // A fresh paused read can have the identical frame. The writer would have no state change to commit.
                var fresh=verify(same,owner,semantic);
                var retained=data.latestCycleSemantic();
                requireObservedContinuation(data.latestObservedFrame(),fresh.frame());
                requireSettledRecoveryFrontier(head.state(),owner,branch);
                if(open)requireOpenReadOnlyRecovery(same,head.state(),owner,branch);
                StrictJson.require(fresh.observedAt().isAfter(retained.observedAt())
                        && fresh.observedAt().isAfter(data.controller().savedPair().orElseThrow().observedAt())
                        && load(branch.head().orElseThrow()).semantic().equals(retained)
                        && semantic.originalDriver().sha256().equals(data.retainedFullDriver().sha256())
                        && head.digest().equals(same.head().digest()),
                        "unchanged saved frontier requires an independent later SEM with its actual Driver");
                settledObservation=new SettledObservation(owner,ContinuityJson.digest(branch.toJson()),fresh.frame());
                return Optional.empty();
            }
            return Optional.of(commitSettledSameGameRecovery(same, data, semantic));
        } finally {
            savedSettledContext.remove();
        }
    }

    /** Recover an already completed dirty cycle; no action or cycle is executed again. */
    WriterContracts.Receipt commitSettledSameGameRecovery(ContinuityStorePort.Session same,
            ContinuityBatchJournal.SettledSameGameData data, SemanticEvidence semantic) throws IOException {
        StrictJson.require(active.get() == same, "settled recovery requires the original journal writer scope");
        Objects.requireNonNull(data); Objects.requireNonNull(semantic);
        requireObservedContinuation(data.latestObservedFrame(), semantic.frame());
        var head = same.head();
        StrictJson.require(head.state().sequence() == data.canonicalSequence()
                && head.digest().equals(data.canonicalHeadDigest()), "settled recovery predecessor changed");
        var owner = data.controller().owner();
        var branch = state(head.state(), owner);
        requireSettledRecoveryFrontier(head.state(), owner, branch);
        if (isOpenReadOnlyBatch(head.state()))
            requireOpenReadOnlyRecovery(same, head.state(), owner, branch);
        StrictJson.require(branch.head().isPresent()
                && load(branch.head().orElseThrow()).semantic().equals(data.latestCycleSemantic()),
                "settled recovery changed its actual completed cycle");
        var canonicalActions = ContinuityActionJournal.receipts(head.state(), archive.withSession(same));
        StrictJson.require(new HashSet<>(canonicalActions).equals(new HashSet<>(data.settledActions())),
                "settled recovery changed its retained original action set");
        var boundary = head.state().toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        StrictJson.require(StrictJson.text(boundary.get("batch_id")).equals(data.controller().batchPrefix()
                + "-" + (data.controller().nextBatchSequence() - 1)), "settled recovery changed its actual consumed batch sequence");
        ObjectNode row = StrictJson.object();
        row.put("evidence_id", "settled-same-game:" + head.digest());
        row.put("source", "java-settled-same-game-recovery/v1");
        row.set("session", sessionToJson(owner));
        row.put("operation", SETTLED_SAME_GAME_OPERATION);
        row.put("predecessor_head_digest", head.digest());
        row.put("batch_id", StrictJson.text(boundary.get("batch_id")));
        row.put("next_sequence", data.controller().nextBatchSequence());
        row.set("cycle_record_ref", branch.head().orElseThrow().toJson());
        row.set("semantic", semanticToJson(semantic));
        var refs = new ArrayList<ExactRef>(data.history());
        refs.addAll(semantic.references());
        refs.add(branch.head().orElseThrow());
        canonicalActions.forEach(action -> refs.add(archive.receiptReferenceOf(action)));
        var request = new WriterContracts.Request(CYCLE_KIND, ContinuityJson.canonical(row), refs.stream().distinct().toList());
        var prepared = same.preview(request);
        var receipt = same.commit(prepared);
        same.requireCommitted(prepared, receipt);
        return receipt;
    }

    /** Adopt the retained recovery after a later business process restart; no ledger event is repeated. */
    void requireSettledSameGameReady(ContinuityStorePort.Session same,
            ContinuityBatchJournal.SettledSameGameData data, SemanticEvidence fresh,
            WriterContracts.HistoricalTransition recovery) throws IOException {
        StrictJson.require(active.get() == same, "settled adoption requires the original journal writer scope");
        Objects.requireNonNull(data); Objects.requireNonNull(fresh); Objects.requireNonNull(recovery);
        var head = same.head();
        var owner = data.controller().owner();
        StrictJson.require(head.state().status() == ContinuityState.Status.RUNNING
                && head.state().sequence() == data.canonicalSequence()
                && head.digest().equals(data.canonicalHeadDigest()), "settled adoption frontier changed");
        requireSettledSameGameHistoryEdge(recovery, owner);
        same.requireHistoricalState(recovery.sequence(), ContinuityJson.digest(recovery.after().toJson()));
        var branch = state(head.state(), owner);
        requireOwner(head.state(), owner); requireFrontier(head.state(), branch); requireLegacyPendingClear(head.state(), branch);
        StrictJson.require(branch.pending().isEmpty() && branch.head().isPresent()
                && load(branch.head().orElseThrow()).semantic().equals(data.latestCycleSemantic()),
                "settled adoption changed its already completed cycle");
        validateChain(branch);
        var actions = ContinuityActionJournal.receipts(head.state(), archive.withSession(same));
        StrictJson.require(actions.stream().allMatch(ActionReceipt::settled)
                && new HashSet<>(actions).equals(new HashSet<>(data.settledActions()))
                && new HashSet<>(actions).equals(new HashSet<>(ContinuityActionJournal.receipts(
                        recovery.after(), archive.withSession(same)))),
                "settled adoption changed its retained original actions");
        var details = ContinuityJson.parseObject(recovery.details(), ContinuityJson.LEDGER_MAX_BYTES);
        long recoveredNext = number(details, "next_sequence");
        String recoveredBatch = text(details, "batch_id");
        StrictJson.require(branch.toJson().equals(state(recovery.after(), owner).toJson())
                && recoveredBatch.equals(data.controller().batchPrefix() + "-" + (recoveredNext - 1))
                && data.controller().usedBatches().contains(recoveredBatch)
                && recoveredNext <= data.controller().nextBatchSequence(),
                "settled adoption changed its recovered batch or cycle frontier");
        var retained = semanticFromJson(details.get("semantic"));
        var checked = verify(same, owner, fresh);
        requireObservedContinuation(retained.frame(), checked.frame());
        requireObservedContinuation(data.latestObservedFrame(), checked.frame());
        StrictJson.require(!checked.observedAt().isBefore(retained.observedAt()), "settled adoption SEM predates its committed recovery");
        requireObservedBindingNotRegressed(head.state(), checked.frame());
        data.retainedFacts().observation().ifPresent(observation -> StrictJson.require(
                observation.observationVersion() == checked.frame().observationVersion()
                        && checked.frame().frame().identity().nativeRevision().compareTo(observation.nativeRevision()) >= 0,
                "settled adoption regressed its retained Driver observation"));
        settledObservation = new SettledObservation(owner, ContinuityJson.digest(branch.toJson()), checked.frame());
    }

    /** Adopts the exact completed cycle of an imported save using a new same-date observation. */
    void requireImportedCycleSettlementReady(ContinuityStorePort.Session same,
            ContinuityBatchJournal.SettledSameGameData data,SemanticEvidence fresh,ActionReceipt original)throws IOException {
        StrictJson.require(active.get()==same,"imported Saved adoption requires the original held writer scope");
        var head=same.head();var owner=data.controller().owner();var branch=state(head.state(),owner);
        StrictJson.require(data.startingPoint() instanceof ContinuityBatchJournal.SameGameEntry.ImportedSaved
                &&head.state().sequence()==data.canonicalSequence()&&head.digest().equals(data.canonicalHeadDigest())
                &&data.source().equals(original.command().source())&&branch.pending().isEmpty(),
                "imported Saved restart lost its exact completed frontier");
        requireFrontier(head.state(),branch);requireLegacyPendingClear(head.state(),branch);validateChain(branch);
        var record=load(branch.head().orElseThrow());var retained=data.latestCycleSemantic();
        StrictJson.require(record.receipt().equals(archive.receiptReferenceOf(original))&&record.semantic().equals(retained)
                &&ContinuityActionJournal.receipts(head.state(),archive).equals(data.settledActions()),
                "imported Saved restart changed its already completed cycle or canonical actions");
        requireImportedCycleSemantic(same,owner,original,fresh);
        requireObservedContinuation(retained.frame(),fresh.frame());
        requireObservedBindingNotRegressed(head.state(),fresh.frame());
        StrictJson.require(fresh.observedAt().isAfter(retained.observedAt())
                &&fresh.frame().frame().identity().dateRaw().equals(retained.frame().frame().identity().dateRaw())
                &&fresh.originalDriver().sha256().equals(data.retainedFullDriver().sha256())
                &&head.digest().equals(same.head().digest()),
                "imported Saved restart requires a fresh same-date SEM with the original Driver and head");
        settledObservation=new SettledObservation(owner,ContinuityJson.digest(branch.toJson()),fresh.frame());
    }

    /** Installs only the observation of the new receiver on the already completed successor branch. */
    void requireCommittedImportedSettledReady(ContinuityStorePort.Session same, ContinuityBatchJournal.SettledSameGameData data,
            CommittedImportedSettledFrontier.Data frontier, SemanticEvidence fresh) throws IOException {
        StrictJson.require(active.get() == same, "settled imported successor requires the original held writer");
        var head = same.head();
        var owner = frontier.owner();
        var branch = state(head.state(), owner);
        var saved = frontier.savedPair();
        StrictJson.require(head.state().status() == ContinuityState.Status.RUNNING && data.controller().owner().equals(owner)
                && head.digest().equals(data.canonicalHeadDigest()) && head.state().sequence() == data.canonicalSequence()
                && branch.pending().isEmpty() && branch.head().isPresent() && data.controller().savedPair().filter(saved::equals).isPresent()
                && head.state().settledDateRaw() == saved.frame().frame().identity().dateRaw().longValueExact(),
                "settled imported successor changed its original cycle, SAVE or held head");
        requireFrontier(head.state(), branch);
        requireLegacyPendingClear(head.state(), branch);
        validateChain(branch);
        var record = load(branch.head().orElseThrow());
        var bound = archive.withSession(same);
        var settled = bound.loadReceipt(record.receipt());
        StrictJson.require(frontier.successorActions().contains(settled) && data.source().equals(settled.command().source())
                && record.semantic().equals(data.latestCycleSemantic()) && record.semantic().equals(frontier.latestCycle()),
                "settled imported successor changed its canonical completed action or SEM");
        var authority = committedImportedSettledReadAuthority;
        if (authority == null) throw new IOException("settled imported successor requires its installed independent Native READ");
        var read = authority.requireCurrent(same, data, fresh);
        var transport = ContinuityBatchJournal.retainedSemanticObservation(fresh, owner, bound).transport();
        var nativePacket = fresh.originalNativePacket();
        byte[] originalPacket = read.originalPacket();
        StrictJson.require(transport.equals(read.session())
                && transport.connectionGeneration().compareTo(data.previousTransport().connectionGeneration()) > 0
                && read.snapshotId().equals(fresh.frame().frame().snapshotId())
                && read.nativeRevision().equals(fresh.frame().frame().identity().nativeRevision())
                && read.observedAt().equals(fresh.observedAt())
                && originalPacket.length == nativePacket.bytes() && ActionCodec.sha256(originalPacket).equals(nativePacket.sha256()),
                "settled imported successor requires the exact independent Full from its newer connection");
        requireImportedCycleSemantic(same, owner, settled, fresh);
        ContinuityBatchJournal.requireSettledObservedContinuation(data.latestObservedFrame(), fresh.frame());
        requireObservedBindingNotRegressed(head.state(), fresh.frame());
        StrictJson.require(fresh.observedAt().isAfter(record.semantic().observedAt())
                && fresh.frame().frame().identity().dateRaw().equals(data.latestObservedFrame().frame().identity().dateRaw())
                && fresh.originalDriver().sha256().equals(data.retainedFullDriver().sha256())
                && fresh.originalDriver().bytes() == data.retainedFullDriver().bytes() && head.digest().equals(same.head().digest()),
                "settled imported successor requires its new same-date SEM and exact retained Driver");
        settledObservation = new SettledObservation(owner, ContinuityJson.digest(branch.toJson()), fresh.frame());
    }

    void requireImportedCycleSemantic(ContinuityStorePort.Session same,SessionIdentity owner,ActionReceipt original,
            SemanticEvidence semantic)throws IOException {
        verifyImportedCycleSemantic(same,owner,original,semantic);
    }

    private VerifiedSemantic verifyImportedCycleSemantic(ContinuityStorePort.Session same, SessionIdentity owner,
            ActionReceipt original, SemanticEvidence semantic) throws IOException {
        var verified=verify(same,owner,semantic);freshAfter(original,verified);
        var originalSemantic=archive.loadFullMaterial(semantic.semantic());
        var body=DriverJson.object(originalSemantic.bytes(),DriverJson.MAX_NATIVE_BYTES);
        var manifestRef=DriverObservationEvidenceReader.reference(body.get("java_driver_facts_evidence"));
        var manifest=archive.loadFullMaterial(manifestRef);
        StrictJson.require(G2Wire.source(StrictJson.parse(manifest.bytes()).get("source")).equals(original.command().source()),
                "imported Saved restart SEM changed the actual original action source");
        return verified;
    }

    private String revalidateSettledSameGameRecovery(ContinuityStorePort.Session same,
            WriterContracts.Head head, ObjectNode details) throws IOException {
        strictSettledSameGameRecovery(details);
        var owner = sessionFromJson(details.get("session"));
        var branch = state(head.state(), owner);
        requireSettledRecoveryFrontier(head.state(), owner, branch);
        if (isOpenReadOnlyBatch(head.state()))
            requireOpenReadOnlyRecovery(same, head.state(), owner, branch);
        StrictJson.require(head.digest().equals(text(details, "predecessor_head_digest"))
                && branch.head().filter(ExactRef.fromJson(details.get("cycle_record_ref"))::equals).isPresent()
                && text(details, "batch_id").equals(StrictJson.text(head.state().toJson()
                        .get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).get("batch_id"))),
                "settled recovery changed its retained canonical frontier");
        var fresh = semanticFromJson(details.get("semantic"));
        var checked = verify(same, owner, fresh);
        var retained = load(branch.head().orElseThrow()).semantic();
        requireObservedContinuation(retained.frame(), checked.frame());
        StrictJson.require(!checked.observedAt().isBefore(retained.observedAt()),
                "settled recovery SEM predates the completed cycle");
        var proof = StrictJson.object();
        proof.put("predecessor", head.digest());
        proof.put("semantic", checked.materialDigest());
        proof.set("cycle_record_ref", details.get("cycle_record_ref"));
        return ContinuityJson.digest(proof);
    }

    private void requireSettledRecoveryFrontier(ContinuityState head, SessionIdentity owner, CycleState branch) throws IOException {
        requireOwner(head, owner); requireFrontier(head, branch); requireLegacyPendingClear(head, branch);
        StrictJson.require((head.status() == ContinuityState.Status.REPAIR_REQUIRED
                || isOpenReadOnlyBatch(head) || isDeferredReadOnlyBatch(head)
                || isCompletedInterruptedSavedBatch(head, owner, branch)
                || isCompletedFinishedSavedBatch(head, owner, branch)
                || isFullySavedBatchBoundary(head, owner, branch))
                && branch.pending().isEmpty() && branch.head().isPresent(),
                "settled recovery requires a completed interrupted cycle");
        Set<ExactRef> completedReceipts = validatedBranchReceipts(branch);
        var actions = ContinuityActionJournal.receipts(head, archive);
        StrictJson.require(!actions.isEmpty() && actions.stream().allMatch(ActionReceipt::settled),
                "settled recovery cannot discard an UNKNOWN or pending original");
        for (var action : actions) {
            StrictJson.require(action.command().sessionId().equals(owner.sessionId())
                    && action.command().origin().game().equals(owner.game())
                    && action.command().origin().machineId().equals(owner.machineId()),
                    "settled recovery crossed an original action owner");
        }
        var context = savedSettledContext.get();
        StrictJson.require(!(isDeferredReadOnlyBatch(head) || isCompletedInterruptedSavedBatch(head, owner, branch)
                || isCompletedFinishedSavedBatch(head, owner, branch)
                || isFullySavedBatchBoundary(head, owner, branch)) || context != null,
                "deferred or completed interrupted recovery requires this journal's fully verified saved history role");
        Set<ExactRef> confirmedSaveReceipts = Set.of();
        if (context != null) {
            StrictJson.require(active.get() == context.same(), "saved settled history lost its actual writer scope");
            context.role().requireCurrent(context.same(), context.data());
            StrictJson.require(head.sequence() == context.data().canonicalSequence()
                    && ContinuityJson.digest(head.toJson()).equals(context.data().canonicalHeadDigest()),
                    "saved settled history crossed its checked frontier");
            confirmedSaveReceipts = context.role().confirmedSaveReceipts();
        }
        boolean revalidateCompletedChain = false;
        for (var action : ContinuityBatchJournal.ordinaryCycleRoots(actions)) {
            if (action.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED && action.visibleGameplay()) {
                var receiptRef = archive.receiptReferenceOf(action);
                if (!confirmedSaveReceipts.contains(receiptRef)) {
                    revalidateCompletedChain = true;
                    StrictJson.require(completedReceipts.contains(receiptRef),
                            "settled recovery cannot discard a visible action without its completed cycle");
                }
            }
        }
        // Requalify the complete chain after all actual Archive/role callbacks before admission.
        if (revalidateCompletedChain) validateChain(branch);
    }

    private static boolean isOpenReadOnlyBatch(ContinuityState state) {
        if (state.status() != ContinuityState.Status.RUNNING) return false;
        var boundary = state.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        return boundary != null && boundary.isObject()
                && JournalKind.BATCH_STARTED.name().equals(StrictJson.text(boundary.get("boundary")));
    }

    private static boolean isDeferredReadOnlyBatch(ContinuityState state) {
        if (state.status() != ContinuityState.Status.RUNNING) return false;
        var boundary = state.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        return boundary != null && boundary.isObject()
                && JournalKind.BATCH_DEFERRED.name().equals(StrictJson.text(boundary.get("boundary")));
    }

    /** Pure dirty completed-frontier DATA; live admission additionally requires the actual saved Journal role. */
    private static boolean isCompletedInterruptedSavedBatch(ContinuityState current, SessionIdentity owner, CycleState branch) {
        if (current.status() != ContinuityState.Status.RUNNING || branch.pending().isPresent() || branch.head().isEmpty()) return false;
        var whole = current.toJson();
        var boundary = whole.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        var savedValue = whole.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD);
        if (boundary == null || !boundary.isObject() || savedValue == null || !savedValue.isObject()
                || !JournalKind.BATCH_INTERRUPTED.name().equals(StrictJson.text(boundary.get("boundary")))
                || !sessionFromJson(boundary.get("session")).equals(owner)) return false;
        StrictJson.text(boundary.get("batch_id"));
        var saved = StrictJson.object(savedValue, Set.of("pair", "state"));
        if (saved.get("pair") == null || !saved.get("pair").isObject()) return false;
        var baseline = parseState(saved.get("state"));
        return branch.session().equals(owner) && baseline.session().equals(owner)
                && baseline.pending().isEmpty() && baseline.head().isPresent()
                && baseline.completedCycles() == current.settledCycles()
                && branch.completedCycles() > baseline.completedCycles()
                && branch.basisCycles() == baseline.basisCycles()
                && branch.retainedLegacyPendingDigest().equals(baseline.retainedLegacyPendingDigest())
                && branch.originFrame().equals(baseline.originFrame()) && branch.episodeOrigin().equals(baseline.episodeOrigin());
    }

    /** Finished dirty-cycle DATA only; live admission still requires the actual saved Journal role. */
    private static boolean isCompletedFinishedSavedBatch(ContinuityState current, SessionIdentity owner, CycleState branch) {
        if (current.status() != ContinuityState.Status.RUNNING || branch.pending().isPresent() || branch.head().isEmpty()) return false;
        var whole = current.toJson();
        var boundary = whole.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        var savedValue = whole.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD);
        if (boundary == null || !boundary.isObject() || savedValue == null || !savedValue.isObject()
                || !JournalKind.BATCH_FINISHED.name().equals(StrictJson.text(boundary.get("boundary")))
                || !sessionFromJson(boundary.get("session")).equals(owner)) return false;
        StrictJson.text(boundary.get("batch_id"));
        var saved = StrictJson.object(savedValue, Set.of("pair", "state"));
        if (saved.get("pair") == null || !saved.get("pair").isObject()) return false;
        var baseline = parseState(saved.get("state"));
        return branch.session().equals(owner) && baseline.session().equals(owner)
                && baseline.pending().isEmpty() && baseline.head().isPresent()
                && baseline.completedCycles() == current.settledCycles()
                && branch.completedCycles() > baseline.completedCycles()
                && branch.basisCycles() == baseline.basisCycles()
                && branch.retainedLegacyPendingDigest().equals(baseline.retainedLegacyPendingDigest())
                && branch.originFrame().equals(baseline.originFrame()) && branch.episodeOrigin().equals(baseline.episodeOrigin());
    }

    /** Pure fully saved boundary DATA; live admission still requires the actual saved Journal role. */
    private static boolean isFullySavedBatchBoundary(ContinuityState current, SessionIdentity owner, CycleState branch) {
        if (current.status() != ContinuityState.Status.RUNNING || branch.pending().isPresent() || branch.head().isEmpty()) return false;
        var whole = current.toJson();
        var boundary = whole.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        var savedValue = whole.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD);
        if (boundary == null || !boundary.isObject() || savedValue == null || !savedValue.isObject()
                || !Set.of(JournalKind.SAVE_CONFIRMED.name(), JournalKind.BATCH_FINISHED.name())
                        .contains(StrictJson.text(boundary.get("boundary")))
                || !sessionFromJson(boundary.get("session")).equals(owner)) return false;
        StrictJson.text(boundary.get("batch_id"));
        var saved = StrictJson.object(savedValue, Set.of("pair", "state"));
        if (saved.get("pair") == null || !saved.get("pair").isObject()) return false;
        var baseline = parseState(saved.get("state"));
        return branch.session().equals(owner) && baseline.session().equals(owner)
                && branch.completedCycles() == current.settledCycles()
                && branch.toJson().equals(baseline.toJson());
    }

    private void requireOpenReadOnlyRecovery(ContinuityStorePort.Session same, ContinuityState current,
            SessionIdentity owner, CycleState branch) throws IOException {
        if(savedSettledContext.get()!=null) {
            requireSavedOpenReadOnlyRecovery(same,current,owner,branch);
            return;
        }
        var anchor = openReadOnlyRecovery.get();
        StrictJson.require(anchor != null && isOpenReadOnlyBatch(current),
                "unfinished batch requires this actual recovery producer and its retained canonical anchor");
        requireSettledSameGameHistoryEdge(anchor, owner);
        same.requireHistoricalState(anchor.sequence(), ContinuityJson.digest(anchor.after().toJson()));
        StrictJson.require(branch.toJson().equals(state(anchor.after(), owner).toJson())
                && new HashSet<>(ContinuityActionJournal.receipts(current, archive.withSession(same)))
                        .equals(new HashSet<>(ContinuityActionJournal.receipts(anchor.after(), archive.withSession(same))))
                && current.settledCycles() == anchor.after().settledCycles()
                && current.settledDateRaw() == anchor.after().settledDateRaw()
                && Objects.equals(current.toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),
                        anchor.after().toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)),
                "unfinished read-only batch changed original actions, completed cycles or saved credit");
    }

    /** Only the actual saved-reader context may combine its current canonical anchor with an open batch. */
    private void requireSavedOpenReadOnlyRecovery(ContinuityStorePort.Session same,ContinuityState current,
            SessionIdentity owner,CycleState branch) throws IOException {
        var context=savedSettledContext.get();
        StrictJson.require(context!=null&&context.same()==same&&active.get()==same&&isOpenReadOnlyBatch(current),
                "saved open recovery lost its actual producer/writer/batch");
        var data=context.data();context.role().requireCurrent(same,data);
        StrictJson.require(data.controller().owner().equals(owner)&&data.controller().savedPair().isPresent()
                &&!context.role().confirmedSaveReceipts().isEmpty()
                &&data.canonicalSequence()==current.sequence()
                &&data.canonicalHeadDigest().equals(ContinuityJson.digest(current.toJson()))
                &&same.head().state().sequence()==current.sequence()
                &&same.head().digest().equals(data.canonicalHeadDigest()),
                "saved open recovery changed its actual current full-history anchor");
        var boundary=StrictJson.object(current.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD),
                Set.of("evidence_id","session","batch_id","boundary"));
        String batch=text(boundary,"batch_id");
        StrictJson.require(JournalKind.BATCH_STARTED.name().equals(text(boundary,"boundary"))
                &&sessionFromJson(boundary.get("session")).equals(owner)
                &&text(boundary,"evidence_id").equals(batch+":"+JournalKind.BATCH_STARTED.name())
                &&batch.equals(data.controller().batchPrefix()+"-"+(data.controller().nextBatchSequence()-1))
                &&data.controller().usedBatches().contains(batch)
                &&branch.session().equals(owner)&&branch.pending().isEmpty()&&branch.head().isPresent(),
                "saved open recovery changed its real retained batch/owner/completed-cycle frontier");
        var bound=archive.withSession(same);var actions=ContinuityActionJournal.receipts(current,bound);
        StrictJson.require(!actions.isEmpty()&&actions.stream().allMatch(ActionReceipt::settled)
                &&actions.size()==data.settledActions().size()
                &&new HashSet<>(actions).equals(new HashSet<>(data.settledActions())),
                "saved open recovery changed its complete actual canonical action set");
        var latest=actions.stream().max(java.util.Comparator.comparingLong(ActionReceipt::sequence)).orElseThrow();
        var anchored=bound.loadRecord(ContinuityActionJournal.recordHead(current).orElseThrow()).receipt();
        if(context.role().confirmedSaveReceipts().contains(bound.receiptReferenceOf(latest))) {
            var saved=StrictJson.object(current.toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),Set.of("pair","state"));
            var pair=CheckpointPairCodec.decode(ContinuityJson.canonical(saved.get("pair")));
            StrictJson.require(anchored.equals(latest)&&latest.sequence()<=current.sequence()
                    &&latest.command().source().equals(data.source())&&latest.bodySha256().equals(ActionCodec.bodySha256(latest.command()))
                    &&"save-checkpoint".equals(latest.command().operation().value())
                    &&latest.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&pair.saveActionId().equals(latest.command().actionId())
                    &&data.controller().savedPair().filter(pair::equals).isPresent()
                    &&branch.completedCycles()==current.settledCycles()&&branch.toJson().equals(parseState(saved.get("state")).toJson()),
                    "saved open recovery changed its verified SAVE, owner or unchanged completed cycle");
            ContinuityActionJournal.requireHistoricalReceipt(current,latest,bound);
            context.role().requireCurrent(same,data);
            return;
        }
        if(latest.state() instanceof ActionState.CompositeOperatorQuarantined retired) {
            StrictJson.require(anchored.equals(latest)&&latest.sequence()<=current.sequence()&&latest.command().source().equals(data.source())
                    &&latest.bodySha256().equals(ActionCodec.bodySha256(latest.command()))
                    &&org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(latest.command().operation().value())
                    &&org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER.equals(retired.execution().handlerId())
                    &&latest.outcome()==ActionReceipt.Outcome.OPERATOR_ABANDONED_UNKNOWN_EFFECT&&!latest.visibleGameplay()&&!latest.eligibleAdvance(),
                    "operator continuation requires its exact canonical retired Life original with unknown effects");
            var recovery=ContinuityJson.object(current.toJson().get(OPERATOR_LIFE_INTERRUPTION_FIELD));strictOperatorQuarantineRecovery(recovery);
            StrictJson.require(OPERATOR_LIFE_INTERRUPTION_OPERATION.equals(text(recovery,"operation"))
                    &&sessionFromJson(recovery.get("session")).equals(owner)
                    &&ExactRef.fromJson(recovery.get("receipt_ref")).equals(bound.receiptReferenceOf(latest))
                    &&number(recovery,"next_sequence")<=data.controller().nextBatchSequence()-1,
                    "operator continuation lost its already committed same-decision recovery or consumed batch");
            var verifier=operatorRetirementVerifier;StrictJson.require(verifier!=null,"operator continuation needs the actual installed retirement verifier");
            verifier.verify(same,same.head(),latest);ContinuityActionJournal.requireHistoricalReceipt(current,latest,bound);
            context.role().requireCurrent(same,data);StrictJson.require(same.head().digest().equals(data.canonicalHeadDigest()),"operator continuation changed its original saved/open-batch head");
            return; // This administrative continuation does not call the old Sway no-gameplay path or grant a cycle.
        }
        StrictJson.require(anchored.equals(latest)&&latest.sequence()<=current.sequence()
                &&latest.command().source().equals(data.source())
                &&latest.bodySha256().equals(ActionCodec.bodySha256(latest.command()))
                &&latest.state() instanceof ActionState.CompositeSettled,
                "saved open recovery requires its exact latest source-owned canonical original");
        var settled=(ActionState.CompositeSettled)latest.state();
        if(settled.settlement() instanceof ActionState.SwaySchedulerCompleted) {
            var canonical=canonicalReceipt(current,bound.receiptReferenceOf(latest),owner);
            StrictJson.require(canonical.equals(latest)&&matchesRecordedSwayReadContinuation(same,same.head(),branch,canonical),
                    "saved open recovery requires its actual no-new-business Sway original ROOT read");
        } else {
            StrictJson.require(settled.settlement() instanceof ActionState.CompositeNoGameplayWrite,
                    "saved open recovery requires its exact latest source-owned no-gameplay canonical original");
        org.xar.ck3.control.application.planning.sway.SwayOrdinaryComposite.requireNoGameplayWriteData(latest.command(),settled.execution());
        ((ActionState.CompositeNoGameplayWrite)settled.settlement()).observation().validate(latest.command(),settled.execution());
        }
        ContinuityActionJournal.requireHistoricalReceipt(current,latest,bound);
        // Role/current-head equality covers all original fields, including saved credit and the closed cycle.
        // The reducer below separately proves that neither credit nor that cycle changes during this admin recovery.
        context.role().requireCurrent(same,data);
        StrictJson.require(same.head().digest().equals(data.canonicalHeadDigest()),"saved open recovery changed during original validation");
    }
    private ContinuityState reduceSettledSameGameRecovery(ContinuityState predecessor, ObjectNode details) {
        strictSettledSameGameRecovery(details);
        var owner = sessionFromJson(details.get("session"));
        var branch = state(predecessor, owner);
        StrictJson.require((predecessor.status() == ContinuityState.Status.REPAIR_REQUIRED
                || isOpenReadOnlyBatch(predecessor) || isDeferredReadOnlyBatch(predecessor)
                || isCompletedInterruptedSavedBatch(predecessor, owner, branch)
                || isCompletedFinishedSavedBatch(predecessor, owner, branch)
                || isFullySavedBatchBoundary(predecessor, owner, branch))
                && ContinuityJson.digest(predecessor.toJson()).equals(text(details, "predecessor_head_digest"))
                && branch.pending().isEmpty()
                && branch.head().filter(ExactRef.fromJson(details.get("cycle_record_ref"))::equals).isPresent(),
                "settled recovery predecessor or completed cycle changed");
        var fresh = semanticFromJson(details.get("semantic"));
        requireObservedContinuation(load(branch.head().orElseThrow()).semantic().frame(), fresh.frame());
        var recovery = StrictJson.object();
        recovery.put("evidence_id", text(details, "evidence_id"));
        // The original reducer already has this no-credit completed-cycle recovery.
        recovery.put("source", "java-reconciled-original-cycle/v1");
        recovery.put("machine_id", owner.machineId());
        recovery.set("session", details.get("session"));
        recovery.put("batch_id", text(details, "batch_id"));
        recovery.put("completed_cycles", predecessor.settledCycles());
        recovery.set("cycle_record_ref", details.get("cycle_record_ref"));
        recovery.set("frame", originalFrame(fresh.frame()));
        final ObjectNode next;
        if (isOpenReadOnlyBatch(predecessor) || isDeferredReadOnlyBatch(predecessor)
                || isCompletedInterruptedSavedBatch(predecessor, owner, branch)
                || isCompletedFinishedSavedBatch(predecessor, owner, branch)
                || isFullySavedBatchBoundary(predecessor, owner, branch)) {
            var boundary = StrictJson.object(predecessor.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD),
                    Set.of("evidence_id", "session", "batch_id", "boundary"));
            StrictJson.require(sessionFromJson(boundary.get("session")).equals(owner)
                    && text(boundary, "batch_id").equals(text(details, "batch_id")),
                    "read-only batch recovery crossed its actual retained batch");
            requireObservedBindingNotRegressed(predecessor, fresh.frame());
            next = predecessor.toJson();
            next.set("latest_binding", originalFrame(fresh.frame()));
        } else next = OriginalWindowReducer.reduce(predecessor.toJson(), "reconciled_original_cycle", recovery, policy);
        StrictJson.require(number(next, "last_settled_cycles") == predecessor.settledCycles()
                && number(next, "last_settled_date_raw") == predecessor.settledDateRaw()
                && next.get(STATE_FIELD).equals(predecessor.toJson().get(STATE_FIELD)),
                "settled same-game recovery cannot change saved credit or the completed cycle");
        return ContinuityState.fromJson(next, predecessor.machineId());
    }

    /** The retained committed recovery is replayed as DATA, without completing its cycle again. */
    void requireSettledSameGameHistoryEdge(WriterContracts.HistoricalTransition edge, SessionIdentity owner) {
        var details = ContinuityJson.parseObject(edge.details(), ContinuityJson.LEDGER_MAX_BYTES);
        strictSettledSameGameRecovery(details);
        StrictJson.require(edge.kind().equals(CYCLE_KIND) && sessionFromJson(details.get("session")).equals(owner),
                "historical settled recovery crossed its actual session");
        var replay = reduceSettledSameGameRecovery(edge.before(), details).toJson();
        replay.put("sequence", edge.sequence()); replay.put("last_event_identity", edge.eventIdentity());
        StrictJson.require(ContinuityJson.same(replay, edge.after().toJson()),
                "historical settled recovery differs from its actual reducer edge");
    }

    private static void strictSettledSameGameRecovery(ObjectNode row) {
        var fields = Set.of("evidence_id", "source", "session", "operation", "predecessor_head_digest",
                "batch_id", "next_sequence", "cycle_record_ref", "semantic");
        StrictJson.object(row, fields, fields);
        text(row, "evidence_id"); text(row, "batch_id");
        StrictJson.require(SETTLED_SAME_GAME_OPERATION.equals(text(row, "operation"))
                && "java-settled-same-game-recovery/v1".equals(text(row, "source"))
                && number(row, "next_sequence") >= 1, "settled same-game recovery fields differ");
        WriterContracts.requireDigest(text(row, "predecessor_head_digest"));
        ExactRef.fromJson(row.get("cycle_record_ref"));
        sessionFromJson(row.get("session")); semanticFromJson(row.get("semantic"));
    }

    private static void requireObservedContinuation(ObservationIdentity retained, ObservationIdentity fresh) {
        requireSameOwner(retained, fresh);
        StrictJson.require(retained.observationVersion() == fresh.observationVersion()
                && fresh.frame().identity().nativeRevision().compareTo(retained.frame().identity().nativeRevision()) >= 0
                && fresh.frame().identity().dateRaw().compareTo(retained.frame().identity().dateRaw()) >= 0,
                "fresh same-game observation regressed its retained native revision or date");
    }

    private record RestartCapture(ExactRef manifest, ControllerRestartState controller) { }
    private final ThreadLocal<RestartCapture> restartCapture=new ThreadLocal<>();
    org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive restartArchive(ContinuityStorePort.Session same){
        StrictJson.require(active.get()==same,"restart originals require the original authority scope");return archive.withSession(same);
    }
    CommittedImportedSettledFrontier.Data readCommittedImportedSettledFrontier(ContinuityStorePort.Session same,
            CommittedImportedRebindOriginal.Historical history)throws IOException {
        return CommittedImportedSettledFrontier.read(same,history,this,archive);
    }
    CommittedImportedDriverHistory.Data readCommittedImportedDriverHistory(ContinuityStorePort.Session same,
            CommittedImportedSettledFrontier.Data frontier)throws IOException {
        return CommittedImportedDriverHistory.read(same,frontier,archive);
    }
    public Set<String> kinds() { return Set.of(CYCLE_KIND, BATCH_KIND, NEXT_BASELINE_KIND); }
    <T> T withLocked(ContinuityStorePort.Session session, LockedWork<T> work) throws IOException {
        Objects.requireNonNull(session); Objects.requireNonNull(work);
        StrictJson.require(active.get() == null, "cycle authority cannot borrow a nested or replacement writer session");
        sessionAuthority.require(session);
        session.head(); active.set(session);
        try { return archive.inSession(session, ignored -> {
            try { return work.run(); } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
        }); } catch (java.io.UncheckedIOException failure) { throw failure.getCause(); }
        finally { active.remove(); }
    }
    private ContinuityStorePort.Session locked(WriterContracts.Head expected) throws IOException {
        var session = active.get(); StrictJson.require(session != null, "actual live writer-lock session is required");
        sessionAuthority.require(session);
        StrictJson.require(session.head().digest().equals(expected.digest()), "cycle authority received a different actual writer head");
        return session;
    }
    @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request request) {
        throw new IllegalStateException("cycle qualification requires the actual held writer session and Head");
    }
    @Override public String revalidate(WriterContracts.Head actualHead, WriterContracts.Request request) throws IOException {
        var session = locked(actualHead); ObjectNode details = request.detailsObject();
        SessionIdentity owner = sessionFromJson(details.get("session")); requireOwner(actualHead.state(), owner);
        ObjectNode proof = StrictJson.object(); proof.put("head_digest", actualHead.digest()); proof.put("request", request.identity());
        if (request.kind().equals(NEXT_BASELINE_KIND)) return revalidateNextBaseline(session,actualHead,details);
        if (request.kind().equals(CYCLE_KIND)) {
            if (Set.of(OPERATOR_QUARANTINE_RECOVERY_OPERATION,OPERATOR_LIFE_INTERRUPTION_OPERATION).contains(text(details,"operation"))) return revalidateOperatorQuarantineRecovery(session,actualHead,details);
            if (SAVED_READ_ONLY_RECOVERY_OPERATION.equals(text(details,"operation"))) return revalidateSavedReadOnlyRecovery(session,actualHead,details);
            if (SETTLED_SAME_GAME_OPERATION.equals(text(details, "operation"))) return revalidateSettledSameGameRecovery(session, actualHead, details);
            if (Set.of(INITIAL_NO_DISPATCH_OPERATION,CAPTURED_NO_DISPATCH_OPERATION).contains(text(details,"operation"))) return revalidateInitialNoDispatchRecovery(session,actualHead,details);
            if (text(details,"operation").equals("TRANSPORT_REBIND")) return revalidateTransport(session,actualHead,details);
            if (text(details, "operation").equals("OPERATOR_REBIND")) return revalidateOperator(session,actualHead,details);
            if (EXTERNAL_SAVE_REBIND.equals(text(details, "operation"))) return revalidateExternalSave(session, actualHead, details);
            if (text(details, "operation").equals("REBIND")) return revalidateRebind(session,actualHead,details,request.identity());
            if (text(details, "operation").equals("EPISODE_REBIND")) return revalidateEpisode(session,actualHead,details);
            strictCycle(details); String operation = text(details, "operation");
            ExactRef receiptRef = ExactRef.fromJson(details.get("receipt_ref"));
            ActionReceipt receipt = canonicalReceipt(actualHead.state(), receiptRef, owner);
            CycleState state = state(actualHead.state(), owner); requireLegacyPendingClear(actualHead.state(), state);
            requireFrontier(actualHead.state(), state);
            StrictJson.require(!hasUnresolvedOtherAction(actualHead.state(), receipt), "another original action remains UNKNOWN or pending");
            if (operation.equals("RETAIN")) {
                StrictJson.require(details.get("semantic").isNull() && details.get("cycle_record_ref").isNull() && details.get("cycle_record").isNull(), "RETAIN cannot claim a completed SEM");
                StrictJson.require(state.pending().isEmpty() || state.pending().orElseThrow().equals(receiptRef), "another AUTO already awaits its fresh SEM");
                StrictJson.require(find(state, receiptRef).isEmpty(), "a canonical AUTO already completed in this cycle branch cannot be counted again");
                if (!matchesSettledActionContinuation(state, receipt)
                        && !matchesRecordedKnownCompletion(session, actualHead, state, receipt)
                        && !matchesRecordedSwayReadContinuation(session, actualHead, state, receipt))
                    requireCurrentFrame(actualHead.state(), state, receipt.command().before());
            } else {
                StrictJson.require(operation.equals("SETTLE"), "unknown ordinary cycle operation");
                validateChain(state);
                SemanticEvidence semantic = semanticFromJson(details.get("semantic"));
                VerifiedSemantic verified = verify(session, owner, semantic); freshAfter(receipt, verified);
                CycleRecord record = CycleRecord.fromJson(details.get("cycle_record"));
                ExactRef recordRef = ExactRef.fromJson(details.get("cycle_record_ref"));
                StrictJson.require(archive.loadMaterial(recordRef).equals(new RawJson(ContinuityJson.canonical(record.toJson()))), "cycle record differs from its actual immutable archive");
                requireRecord(state, receiptRef, receipt, semantic, record);
                proof.put("semantic_digest", verified.materialDigest()); proof.put("semantic_evidence_id", verified.semanticEvidenceId());
            }
        } else {
            StrictJson.require(request.kind().equals(BATCH_KIND), "cycle authority refuses an unregistered event kind");
            strictBatch(details); JournalKind kind = JournalKind.valueOf(text(details, "boundary"));
            if (kind == JournalKind.WORKER_RESTART_CAPTURE) {
                StrictJson.require(details.get("checkpoint_pair").isNull()&&details.get("completed_cycle_proof").isNull(),"restart metadata grants no SAVE or cycle credit");
                var captured=restartCapture.get();
                StrictJson.require(captured!=null&&captured.manifest().equals(ExactRef.fromJson(details.get("restart_manifest"))),
                        "only the idle original Controller can publish restart state");
                var manifest=CleanBatchRestart.decode(archive.loadMaterial(captured.manifest()).bytes());
                var controller=ControllerRestartState.decode(archive.loadMaterial(manifest.controller()).bytes());
                StrictJson.require(java.util.Arrays.equals(controller.encode(),captured.controller().encode())&&controller.owner().equals(owner)
                        &&!controller.quarantined()&&!controller.localUnresolved(),"restart state differs from the captured resolved Controller");
                requireRestartClean(session,owner);
                proof.put("restart_manifest",captured.manifest().sha256());
            } else if (kind == JournalKind.SAVE_CONFIRMED) {
                CheckpointPair pair = CheckpointPairCodec.decode(ContinuityJson.canonical(details.get("checkpoint_pair")));
                CompletedCycleProof completed = proofFromJson(details.get("completed_cycle_proof"));
                var checked = verifySaveCapture(session, actualHead, owner, pair, completed);
                StrictJson.require(savedMaterialEvidence(details, owner, pair).equals(checked.material()),
                        "SAVE canonical material differs from the actual current capture");
                proof.put("checkpoint_digest", checked.digest());
            } else {
                StrictJson.require(details.get("checkpoint_pair").isNull() && details.get("completed_cycle_proof").isNull(), "batch metadata cannot claim a checkpoint or new completed cycles");
            }
        }
        return ContinuityJson.digest(proof);
    }
    @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request request) {
        ObjectNode details = request.detailsObject(); SessionIdentity owner = sessionFromJson(details.get("session"));
        requireOwner(predecessor, owner); ObjectNode next = predecessor.toJson();
        if (request.kind().equals(NEXT_BASELINE_KIND)) return reduceNextBaseline(predecessor,details);
        if (request.kind().equals(CYCLE_KIND)) {
            if (Set.of(OPERATOR_QUARANTINE_RECOVERY_OPERATION,OPERATOR_LIFE_INTERRUPTION_OPERATION).contains(text(details,"operation"))) return reduceOperatorQuarantineRecovery(predecessor,details);
            if (SAVED_READ_ONLY_RECOVERY_OPERATION.equals(text(details,"operation"))) return reduceSavedReadOnlyRecovery(predecessor,details);
            if (SETTLED_SAME_GAME_OPERATION.equals(text(details, "operation"))) return reduceSettledSameGameRecovery(predecessor, details);
            if (Set.of(INITIAL_NO_DISPATCH_OPERATION,CAPTURED_NO_DISPATCH_OPERATION).contains(text(details,"operation"))) return reduceInitialNoDispatchRecovery(predecessor,details);
            if (text(details,"operation").equals("TRANSPORT_REBIND")) return reduceTransport(predecessor,details);
            if (text(details, "operation").equals("OPERATOR_REBIND")) return reduceOperator(predecessor,details);
            if (EXTERNAL_SAVE_REBIND.equals(text(details, "operation"))) return reduceExternalSave(predecessor, details);
            if (text(details, "operation").equals("REBIND")) return reduceRebind(predecessor, details);
            if (text(details, "operation").equals("EPISODE_REBIND")) return reduceEpisode(predecessor,details);
            strictCycle(details); CycleState before = state(predecessor, owner); ExactRef receipt = ExactRef.fromJson(details.get("receipt_ref"));
            if (text(details, "operation").equals("RETAIN")) {
                next.set(STATE_FIELD, before.withPending(Optional.of(receipt)).toJson());
            } else {
                StrictJson.require(text(details, "operation").equals("SETTLE"), "ordinary cycle operation");
                CycleRecord record = CycleRecord.fromJson(details.get("cycle_record"));
                StrictJson.require(before.pending().filter(receipt::equals).isPresent() && record.previous().equals(before.head())
                        && record.receipt().equals(receipt) && record.session().equals(owner), "actual pending cycle/record predecessor changed");
                long expected = Math.addExact(before.completedCycles(), record.classification() == Classification.CONTROL_ONLY ? 0 : 1);
                StrictJson.require(record.completedCycles() == expected, "completed cycle count must come from actual receipt classification");
                next.set(STATE_FIELD, new CycleState(owner, before.basisCycles(), expected,
                        Optional.of(ExactRef.fromJson(details.get("cycle_record_ref"))), Optional.empty(), before.retainedLegacyPendingDigest(),before.originFrame(),before.episodeOrigin()).toJson());
                if(predecessor.status()==ContinuityState.Status.REPAIR_REQUIRED) {
                    // Actual SETTLE has revalidated the canonical receipt, archived record and fresh SEM under this writer lock.
                    ObjectNode recovery=StrictJson.object();recovery.put("evidence_id",text(details,"evidence_id"));
                    recovery.put("source","java-reconciled-original-cycle/v1");recovery.put("machine_id",owner.machineId());
                    recovery.set("session",sessionToJson(owner));
                    recovery.set("batch_id",predecessor.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).get("batch_id"));
                    recovery.put("completed_cycles",predecessor.settledCycles());recovery.set("cycle_record_ref",details.get("cycle_record_ref"));
                    recovery.set("frame",originalFrame(semanticFromJson(details.get("semantic")).frame()));
                    next=OriginalWindowReducer.reduce(next,"reconciled_original_cycle",recovery,policy);
                }
            }
        } else {
            StrictJson.require(request.kind().equals(BATCH_KIND), "unregistered batch event"); strictBatch(details);
            JournalKind boundary = JournalKind.valueOf(text(details, "boundary"));
            if (boundary == JournalKind.SAVE_CONFIRMED) {
                next = reduceConfirmedSave(predecessor, owner, details);
            } else if (boundary == JournalKind.BATCH_INTERRUPTED) {
                ObjectNode original = StrictJson.object(); original.put("evidence_id", text(details, "evidence_id")); original.set("source", details.get("source"));
                original.put("machine_id", owner.machineId()); original.put("completed_cycles", predecessor.settledCycles());
                original.set("frame", predecessor.toJson().get("latest_binding")); original.put("reason", "ordinary Java batch interrupted; original unsettled actions remain retained without replay");
                next = OriginalWindowReducer.reduce(predecessor.toJson(),
                        "java-ordinary-batch-interruption/v2".equals(text(details,"source"))?"ordinary_batch_interrupted":"repair_required", original, policy);
            }
            recordBatchBoundary(next, details, owner, boundary);
        }
        return ContinuityState.fromJson(next, predecessor.machineId());
    }

    /** Pure replay of one canonical ordinary batch boundary with no gameplay or SAVE effects. */
    static ContinuityState replayCommittedBatchMetadata(ContinuityState predecessor, SessionIdentity owner, String batch,
            JournalKind boundary, WriterContracts.HistoricalTransition actual) {
        StrictJson.require(Set.of(JournalKind.BATCH_STARTED, JournalKind.BATCH_FINISHED, JournalKind.BATCH_DEFERRED).contains(boundary),
                "only empty ordinary batch metadata can follow the imported REBIND");
        requireOwner(predecessor, owner);
        var input = new JournalInput(owner, batch, boundary, Optional.empty(), Optional.empty(), Optional.empty(), List.of());
        var request = batchRequest(input, Optional.empty());
        StrictJson.require(request.kind().equals(actual.kind()) && request.identity().equals(actual.eventIdentity())
                && java.util.Arrays.equals(request.details(), actual.details()),
                "committed imported batch metadata differs from the exact ordinary producer");
        var next = predecessor.toJson();
        recordBatchBoundary(next, request.detailsObject(), owner, boundary);
        return ContinuityState.fromJson(next, predecessor.machineId());
    }

    private static void recordBatchBoundary(ObjectNode next, ObjectNode details, SessionIdentity owner, JournalKind boundary) {
        ObjectNode boundaryState = StrictJson.object(); boundaryState.put("evidence_id", text(details, "evidence_id"));
        boundaryState.set("session", sessionToJson(owner)); boundaryState.put("batch_id", text(details, "batch_id")); boundaryState.put("boundary", boundary.name());
        if (boundary == JournalKind.WORKER_RESTART_CAPTURE) boundaryState.set("restart_manifest", details.get("restart_manifest"));
        next.set(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD, boundaryState);
    }

    Optional<CompletedCycleProof> retainedCycleProof(ContinuityStorePort.Session session, SessionIdentity owner) throws IOException {
        var head = session.head(); requireOwner(head.state(), owner);
        requireRetainedProofRole(session, head.state(), owner);
        CycleState retained = state(head.state(), owner);
        requireLegacyPendingClear(head.state(), retained); requireFrontier(head.state(), retained); validateChain(retained);
        if (retained.pending().isPresent() || retained.head().isEmpty()) return Optional.empty();
        var semantic = load(retained.head().orElseThrow()).semantic();
        VerifiedSemantic checked = verify(session, owner, semantic);
        requireCurrentFrame(head.state(), retained, checked.frame());
        StrictJson.require(head.digest().equals(session.head().digest()), "retained proof read changed its original writer head");
        return Optional.of(new CompletedCycleProof(retained.completedCycles(), semantic, ContinuityJson.digest(retained.toJson())));
    }
    /** Reading the existing completed branch grants no ordinary action or restart authority. */
    private void requireRetainedProofRole(ContinuityStorePort.Session session, ContinuityState head, SessionIdentity owner) throws IOException {
        if (head.status() != ContinuityState.Status.REPAIR_REQUIRED) { requireActive(head); return; }
        StrictJson.require(active.get() == session, "retained SAVE proof requires the identical locked writer Session");
        sessionAuthority.require(session); requireOwner(head, owner);
        ObjectNode whole = head.toJson();
        ObjectNode boundary = StrictJson.object(whole.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD),
                Set.of("evidence_id", "session", "batch_id", "boundary"));
        ObjectNode interruption = StrictJson.object(whole.get("interruption"),
                Set.of("reason", "source", "evidence_id", "last_settled_frame", "completed_cycles"));
        StrictJson.require(text(boundary, "boundary").equals(JournalKind.BATCH_INTERRUPTED.name())
                && sessionFromJson(boundary.get("session")).equals(owner)
                && text(interruption, "source").equals("java-ordinary-batch-interruption/v2")
                && text(interruption, "evidence_id").equals(text(boundary, "evidence_id"))
                && number(whole, "interrupted_window_id") == head.origin().windowId()
                && number(interruption, "completed_cycles") == head.settledCycles(),
                "retained SAVE proof requires this actual ordinary interrupted window");
        var record = archive.loadRecord(ContinuityActionJournal.recordHead(head)
                .orElseThrow(() -> new IOException("retained SAVE proof has no canonical action head")));
        ActionReceipt save = record.receipt(); ActionCommand command = save.command();
        StrictJson.require(save.settled() && save.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                && command.origin() instanceof CommandOrigin.Gameplay
                && command.expectation() instanceof org.xar.ck3.control.application.action.CommandExpectation.Gameplay
                && command.protocolIdentity() instanceof org.xar.ck3.control.application.action.ProtocolRequestIdentity.BodyDerived
                && command.operation().value().equals("save-checkpoint")
                && command.sessionId().equals(owner.sessionId())
                && command.origin().machineId().equals(owner.machineId()) && command.origin().game().equals(owner.game())
                && command.expected().observerSchema().equals(org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory.OBSERVER_SCHEMA)
                && command.arguments().members().isEmpty()
                && command.claims().armyIds().isEmpty() && command.claims().allyCharacterIds().isEmpty()
                && command.claims().characterIds().isEmpty() && command.claims().commitmentKeys().isEmpty()
                && save.bodySha256().equals(ActionCodec.bodySha256(command))
                && ContinuityActionJournal.lookup(head, command.actionId(), archive).filter(save::equals).isPresent(),
                "retained proof requires the current canonical independently APPLIED original SAVE");
        var expected = List.of(
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("date_raw"), command.before().frame().identity().dateRaw()),
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("played_character_id"), command.before().frame().identity().player()),
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("checkpoint_pair_verified"), true));
        StrictJson.require(command.expected().values().equals(expected), "retained proof SAVE postcondition differs from its actual factory");
        var attempt = ActionTransitions.attempt(save.state()).orElseThrow(() -> new IOException("retained SAVE proof lacks its original attempt"));
        var dispatch = ActionTransitions.dispatch(save.state()).orElseThrow(() -> new IOException("retained SAVE proof lacks its original ACK"));
        StrictJson.require(dispatch instanceof org.xar.ck3.control.application.action.NativeActionPort.AckReceived ack
                && ack.nativeOk() && ack.requestId().equals(attempt.requestId()), "retained SAVE proof lacks its positive original ACK");
        var guard = attempt.guard();
        StrictJson.require(command.origin().acceptsGuard(guard.origin()) && guard.source().equals(command.source())
                && guard.sessionId().equals(command.sessionId()) && guard.operation().equals(command.operation())
                && guard.observed().equals(command.before()), "retained SAVE proof changed its original attempt guard");
        for (ActionReceipt action : ContinuityActionJournal.receipts(head, archive))
            StrictJson.require(action.settled(), "retained SAVE proof cannot conceal another unresolved original");
        CycleState cycle = state(head, owner); requireLegacyPendingClear(head, cycle); requireFrontier(head, cycle); validateChain(cycle);
        StrictJson.require(cycle.pending().isEmpty() && cycle.head().isPresent(), "retained SAVE proof needs its completed original cycle branch");
        requireSavedContinuation(load(cycle.head().orElseThrow()).semantic().frame(), command.before());
    }
    /** Deterministic SAVE DATA reduction; also checks the exact old reducer eligibility before capture. */
    private ObjectNode reduceConfirmedSave(ContinuityState predecessor, SessionIdentity owner, ObjectNode details) {
        ObjectNode next;
        var completed = proofFromJson(details.get("completed_cycle_proof")); requireProof(state(predecessor, owner), completed);
        var pair = CheckpointPairCodec.decode(ContinuityJson.canonical(details.get("checkpoint_pair"))); requireSavedContinuation(completed.frame(), pair.frame());
        if (predecessor.status() == ContinuityState.Status.REPAIR_REQUIRED) {
            ObjectNode original = StrictJson.object(); original.put("evidence_id", text(details, "evidence_id")); original.put("source", "java-reconciled-original-save/v1");
            original.put("machine_id", owner.machineId()); original.put("date_raw", pair.frame().frame().identity().dateRaw().longValueExact());
            original.put("completed_cycles", completed.completedCycles()); original.set("frame", originalFrame(pair.frame()));
            original.set("session", sessionToJson(owner)); original.put("batch_id", text(ContinuityJson.object(predecessor.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)), "batch_id"));
            original.set("cycle_record_ref", state(predecessor, owner).head().orElseThrow().toJson());
            next = OriginalWindowReducer.reduce(predecessor.toJson(), "reconciled_original_save", original, policy);
        } else {
            ObjectNode original = StrictJson.object(); original.put("evidence_id", text(details, "evidence_id")); original.set("source", details.get("source"));
            original.put("machine_id", owner.machineId()); original.put("date_raw", pair.frame().frame().identity().dateRaw().longValueExact());
            original.put("completed_cycles", completed.completedCycles()); original.set("frame", originalFrame(pair.frame()));
            next = OriginalWindowReducer.reduce(predecessor.toJson(), "settled_batch", original, policy);
        }
        // Preserve the exact saved cycle branch for a later source-bound restore authority.
        ObjectNode saved = StrictJson.object(); saved.set("pair", StrictJson.parse(CheckpointPairCodec.encode(pair)));
        saved.set("state", state(predecessor, owner).toJson()); next.set(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD, saved);
        var material = savedMaterialEvidence(details, owner, pair);
        if (material.isPresent()) {
            requireMaterialHead(predecessor, material.orElseThrow());
            next.set(org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence.FIELD,
                    details.get(org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence.FIELD).deepCopy());
        } else next.remove(org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence.FIELD);
        return next;
    }
    private static void requireMaterialHead(ContinuityState predecessor,
            org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence material) {
        StrictJson.require(material.originalHeadSequence() <= predecessor.sequence(), "SAVE material source head lies after its actual predecessor");
        if (material.originalHeadSequence() == predecessor.sequence())
            StrictJson.require(material.originalHeadDigest().equals(ContinuityJson.digest(predecessor.toJson())),
                    "SAVE material changed its exact original predecessor head");
    }
    /** Strict versioned DATA only: no private issuer, physical qualification or current authority is created. */
    static Optional<org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence> savedMaterialEvidence(
            ObjectNode details, SessionIdentity owner, CheckpointPair pair) {
        strictBatch(details);
        StrictJson.require(JournalKind.SAVE_CONFIRMED.name().equals(text(details, "boundary")), "saved material needs the exact SAVE boundary");
        if (!SAVED_MATERIAL_SOURCE.equals(text(details, "source"))) return Optional.empty();
        var material = org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence.decode(
                details.get(org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence.FIELD));
        material.requireSavedBranch(pair, owner); return Optional.of(material);
    }
    /** Full current SAVE admission is repeated for preparation, preview and commit; nothing is replay-cached. */
    private CheckpointCaptureResult verifySaveCapture(ContinuityStorePort.Session same, WriterContracts.Head head,
            SessionIdentity owner, CheckpointPair pair, CompletedCycleProof completed) throws IOException {
        StrictJson.require(locked(head) == same, "SAVE capture requires its actual original writer Session");
        requireOwner(head.state(), owner);
        CycleState state = state(head.state(), owner); requireLegacyPendingClear(head.state(), state);
        requireFrontier(head.state(), state); validateChain(state); requireProof(state, completed);
        StrictJson.require(ContinuityActionJournal.receipts(head.state(), archive).stream().noneMatch(receipt -> !receipt.settled()
                        && receipt.command().sessionId().equals(owner.sessionId()) && receipt.command().origin().game().equals(owner.game())),
                "SAVE capture cannot discard an unresolved original action in its actual owner scope");
        VerifiedSemantic semantic = verify(same, owner, completed.semantic()); requireProofFrame(head.state(), state, semantic);
        requireSavedContinuation(completed.frame(), pair.frame());
        var checked = checkpointVerifier.verifyMaterialCapture(same, owner, pair, completed);
        if (checked.material().isPresent()) {
            var material = checked.material().orElseThrow(); material.requireSavedBranch(pair, owner);
            requireMaterialHead(head.state(), material);
        }
        StrictJson.require(head.digest().equals(same.head().digest()), "SAVE capture changed its actual writer head");
        return checked;
    }

    Optional<CompletedCycleProof> cycleProof(ContinuityStorePort.Session session, SessionIdentity owner, SemanticEvidence semantic) throws IOException {
        return cycleProof(session,owner,semantic,() -> verify(session,owner,semantic));
    }

    Optional<CompletedCycleProof> importedTerminalCycleProof(ContinuityStorePort.Session session, SessionIdentity owner,
            ActionReceipt receipt, SemanticEvidence semantic) throws IOException {
        StrictJson.require(active.get() == session, "imported terminal cycle requires its actual locked replay");
        return cycleProof(session,owner,semantic,() -> verifyImportedCycleSemantic(session,owner,receipt,semantic));
    }

    private Optional<CompletedCycleProof> cycleProof(ContinuityStorePort.Session session, SessionIdentity owner,
            SemanticEvidence semantic, LockedWork<VerifiedSemantic> verification) throws IOException {
        var head = session.head(); requireOwner(head.state(), owner); requireActive(head.state());
        CycleState state = state(head.state(), owner); requireLegacyPendingClear(head.state(), state);
        requireFrontier(head.state(), state); validateChain(state); if (state.pending().isPresent()) return Optional.empty();
        VerifiedSemantic checked = verification.run();
        requireProofFrame(head.state(), state, checked);
        return Optional.of(new CompletedCycleProof(state.completedCycles(), semantic, ContinuityJson.digest(state.toJson())));
    }
    /** Read-only calendar evidence for the original unissued Opening. */
    public sealed interface OpeningDateEvidence permits ImportedOpeningAdvance, SavedOpeningAdvance {
        SemanticEvidence semantic();
        List<ExactRef> evidence();
    }

    public record ImportedOpeningAdvance(ExactRef cycleRecord, ExactRef lifeReceipt, SemanticEvidence semantic,
            List<ExactRef> restoredOpeningEvidence) implements OpeningDateEvidence {
        public ImportedOpeningAdvance(ExactRef cycleRecord, ExactRef lifeReceipt, SemanticEvidence semantic) {
            this(cycleRecord, lifeReceipt, semantic, List.of());
        }
        public ImportedOpeningAdvance {
            Objects.requireNonNull(cycleRecord); Objects.requireNonNull(lifeReceipt); Objects.requireNonNull(semantic);
            restoredOpeningEvidence = List.copyOf(restoredOpeningEvidence);
        }
        public List<ExactRef> evidence() {
            var refs = new ArrayList<>(List.of(cycleRecord, lifeReceipt));
            refs.addAll(semantic.references());
            refs.addAll(restoredOpeningEvidence);
            return List.copyOf(refs);
        }
    }

    public record SavedOpeningAdvance(ExactRef confirmation, ExactRef saveReceipt, ExactRef savedCycleRecord, SemanticEvidence savedSemantic,
            Optional<ImportedOpeningAdvance> laterAdvance) implements OpeningDateEvidence {
        public SavedOpeningAdvance {
            Objects.requireNonNull(confirmation); Objects.requireNonNull(saveReceipt); Objects.requireNonNull(savedCycleRecord);
            Objects.requireNonNull(savedSemantic); Objects.requireNonNull(laterAdvance);
        }
        @Override public SemanticEvidence semantic() {
            return laterAdvance.map(ImportedOpeningAdvance::semantic).orElse(savedSemantic);
        }
        @Override public List<ExactRef> evidence() {
            var refs = new ArrayList<>(List.of(confirmation, saveReceipt, savedCycleRecord));
            refs.addAll(savedSemantic.references());
            laterAdvance.ifPresent(advance -> refs.addAll(advance.evidence()));
            return List.copyOf(refs);
        }
    }

    /** Settled Life cycles and date-neutral controls can explain the current date of an unissued imported opening. */
    public Optional<ImportedOpeningAdvance> importedOpeningAdvance(ContinuityStorePort.Session same, SessionIdentity owner,
            ObservationIdentity originalOpening, G2Source source, ObservationIdentity current) throws IOException {
        if (active.get() == null)
            return withLocked(same, () -> importedOpeningAdvance(same, owner, originalOpening, source, current));
        return openingDateEvidence(same, owner, originalOpening, source, current, Optional.empty())
                .map(ImportedOpeningAdvance.class::cast);
    }

    Optional<OpeningDateEvidence> openingDateEvidence(ContinuityStorePort.Session same, SessionIdentity owner,
            ObservationIdentity originalOpening, G2Source source, ObservationIdentity current,
            Optional<ContinuityBatchJournal.OpeningSaveAnchor> saved) throws IOException {
        Objects.requireNonNull(originalOpening); Objects.requireNonNull(source); Objects.requireNonNull(current);
        StrictJson.require(active.get() == same, "opening date projection requires its original writer Session");
        sessionAuthority.require(same);
        var head = same.head();
        var retained = head.state();
        var whole = retained.toJson();
        if (retained.status() != ContinuityState.Status.RUNNING || !whole.hasNonNull(SavedContinuityBootstrap.FIELD)
                || !whole.hasNonNull(STATE_FIELD) || whole.hasNonNull(WriterContracts.GAMEPLAY_ENTRY_FIELD)
                || whole.hasNonNull(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD) != saved.isPresent()) return Optional.empty();

        var imported = SavedContinuityBootstrap.request(ContinuityJson.object(whole.get(SavedContinuityBootstrap.FIELD))).detailsObject();
        boolean restored = whole.has(WriterContracts.ORDINARY_IMPORTED_CYCLE_ORIGIN_FIELD);
        if (!restored && (!owner.equals(sessionFromJson(imported.get("session")))
                || !originalOpening.equals(ProposalLifecycleCodec.decodeObservation(imported.get("opening")))
                || !ContinuityJson.same(imported.get("source"), ProposalLifecycleCodec.source(source)))) return Optional.empty();
        if (!ContinuityJson.same(whole.get("game_binding"), owner.game().toJson())
                || !ContinuityJson.same(whole.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD), imported.get("full_driver"))
                || (restored && !owner.equals(sessionFromJson(whole.get(STATE_FIELD).get("session"))))) return Optional.empty();
        requireOwner(retained, owner);
        requireSameOwner(originalOpening, current);
        long importedCycles = number(imported, "saved_completed_cycles");
        long anchorCycles = importedCycles;
        long anchorDate = number(imported, "saved_date_raw");
        var anchor = saved.orElse(null);
        if (anchor != null) {
            requireObservedContinuation(originalOpening, anchor.pair().frame());
            requireObservedBindingNotRegressed(retained, current);
            var canonicalRevision = StrictJson.integer(whole.get("latest_binding").get("revision"), BigInteger.ZERO, StrictJson.UINT64_MAX);
            StrictJson.require(current.frame().revision().compareTo(canonicalRevision) >= 0,
                    "Opening projection regressed its canonical public revision");
            anchorCycles = anchor.pairCycles();
            anchorDate = anchor.pair().frame().frame().identity().dateRaw().longValueExact();
        }
        if (retained.settledCycles() != anchorCycles || retained.settledDateRaw() != anchorDate) return Optional.empty();
        CycleState cycle = state(retained, owner);
        long advances = cycle.completedCycles() - anchorCycles;
        if (cycle.pending().isPresent() || cycle.head().isEmpty() || cycle.originFrame().isPresent() != restored
                || cycle.episodeOrigin().isPresent() || cycle.basisCycles() != importedCycles
                || advances < 0 || advances > MAX_RECORDS || (anchor == null && advances == 0)) return Optional.empty();
        List<ExactRef> restoredEvidence = List.of();
        if (restored) {
            var selected = restoredImportedOpeningEvidence(retained, whole, imported, cycle, originalOpening, source);
            if (selected.isEmpty()) return Optional.empty();
            restoredEvidence = selected.orElseThrow();
        }
        requireLegacyPendingClear(retained, cycle);
        ExactRef recordRef = cycle.head().orElseThrow();
        CycleRecord record = load(recordRef);
        if (!record.semantic().frame().frame().identity().dateRaw().equals(current.frame().identity().dateRaw()))
            return Optional.empty();
        var actionHead = ContinuityActionJournal.recordHead(retained);
        if (actionHead.isEmpty()) return Optional.empty();
        ActionReceipt receipt = archive.loadRecord(actionHead.orElseThrow()).receipt();
        if (anchor != null && recordRef.equals(anchor.cycleRecord())) {
            if (advances != 0 || !receipt.equals(anchor.receipt())) return Optional.empty();
            requireOpeningSaveContinuation(anchor, current);
            return Optional.of(savedOpeningEvidence(anchor, null));
        }
        long followingSequence = retained.sequence() + 1;
        ObservationIdentity following = current;
        ImportedOpeningAdvance latestLife = null;
        long remaining = advances;
        for (int visited = 0; visited < MAX_RECORDS; visited++) {
            boolean advance = record.classification() == Classification.ELIGIBLE_ADVANCE;
            boolean controlOnly = record.classification() == Classification.CONTROL_ONLY;
            if (!record.session().equals(owner) || record.completedCycles() != anchorCycles + remaining
                    || (anchor != null && receipt.sequence() <= anchor.sequence())
                    || (!advance && !controlOnly)
                    || (advance && (remaining == 0 || !LifeAdvanceComposite.accepts(receipt.command().operation().value())))
                    || !receipt.command().source().equals(source) || receipt.sequence() >= followingSequence
                    || !matchesCycleRecordReceipt(record, receipt, owner)) return Optional.empty();
            var before = receipt.command().before();
            var terminal = terminal(receipt);
            var after = terminal.frame();
            int dateChange = after.frame().identity().dateRaw().compareTo(before.frame().identity().dateRaw());
            if ((advance ? dateChange <= 0 : dateChange != 0)
                    || !after.frame().identity().dateRaw().equals(following.frame().identity().dateRaw()))
                return Optional.empty();
            requireSavedContinuation(after, record.semantic().frame());
            requireSavedContinuation(record.semantic().frame(), following);
            freshAfter(receipt, terminal, record.semantic().frame(), record.semantic().observedAt());
            if (advance) {
                remaining--;
                if (latestLife == null) latestLife = new ImportedOpeningAdvance(recordRef, record.receipt(), record.semantic(), restoredEvidence);
            }
            if (record.previous().isEmpty()) {
                if (anchor != null || !advance || remaining != 0
                        || !before.frame().identity().dateRaw().equals(originalOpening.frame().identity().dateRaw()))
                    return Optional.empty();
                requireSavedContinuation(originalOpening, before);
                StrictJson.require(head.digest().equals(same.head().digest()), "opening date evidence changed the actual writer head");
                return Optional.of(latestLife);
            }
            following = before;
            followingSequence = receipt.sequence();
            recordRef = record.previous().orElseThrow();
            if (anchor != null && recordRef.equals(anchor.cycleRecord())) {
                if (remaining != 0) return Optional.empty();
                requireOpeningSaveContinuation(anchor, following);
                StrictJson.require(head.digest().equals(same.head().digest()), "opening date evidence changed the actual writer head");
                return Optional.of(savedOpeningEvidence(anchor, latestLife));
            }
            record = load(recordRef);
            receipt = archive.loadReceipt(record.receipt());
        }
        return Optional.empty();
    }

    private static void requireOpeningSaveContinuation(ContinuityBatchJournal.OpeningSaveAnchor anchor,
            ObservationIdentity following) {
        var saved = anchor.receipt().applied().orElseThrow().observation().after();
        requireSavedContinuation(saved, following);
        StrictJson.require(following.frame().revision().compareTo(saved.frame().revision()) >= 0,
                "opening date projection regressed the actual SAVE public revision");
    }

    private Optional<List<ExactRef>> restoredImportedOpeningEvidence(ContinuityState retained, ObjectNode whole,
            ObjectNode imported, CycleState cycle, ObservationIdentity originalOpening, G2Source source) {
        if (cycle.originFrame().filter(originalOpening::equals).isEmpty()) return Optional.empty();
        var body = DomainBodies.reference(retained, DomainBodies.Slot.OPENING_GATE);
        if (body.isEmpty()) return Optional.empty();
        var openingRef = body.orElseThrow().payload();
        var opening = GovernanceOpeningDocument.decode(archive.loadMaterial(openingRef).bytes());
        if (!opening.observed().equals(originalOpening) || !opening.source().equals(source)
                || !opening.sessionId().equals(cycle.session().sessionId())
                || opening.stage() != OpeningStage.AWAIT_SUBMIT || opening.preparedCommand().isPresent()
                || opening.actionReceipt().isPresent() || opening.checkpoint().isPresent())
            return Optional.empty();

        var originRef = ExactRef.fromJson(whole.get(WriterContracts.ORDINARY_IMPORTED_CYCLE_ORIGIN_FIELD));
        var origin = StrictJson.object(ContinuityJson.parseObject(archive.loadMaterial(originRef).bytes(),
                ContinuityJson.DOCUMENT_MAX_BYTES), Set.of("schema", "attachment_identity", "restored_session", "restore_pair",
                        "retained_legacy_pending_digest", STATE_FIELD, WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,
                        WriterContracts.ORDINARY_CYCLE_REBIND_FIELD, "original_action_head"));
        if (!text(origin, "schema").equals("xar.java-ordinary-cycle-restore-tombstone/v2")
                || !cycle.session().equals(sessionFromJson(origin.get("restored_session")))) return Optional.empty();
        var attachment = ContinuityJson.object(whole.get("last_current_saved_cold"));
        var sources = SavedAttachmentSourceStore.Sources.decode(attachment.get(SavedAttachmentSourceStore.SOURCES_DETAIL));
        var v5 = sources.importedOrigin().orElseThrow();
        var pair = CheckpointPairCodec.decode(ContinuityJson.canonical(origin.get("restore_pair")));
        var oldCycle = StrictJson.object(origin.get(STATE_FIELD), Set.of("present", "value"));
        var actor = originalOpening.frame();
        var physical = pair.frame().frame();
        boolean exact = oldCycle.get("present").isBoolean() && oldCycle.get("present").booleanValue()
                && v5.owner().equals(sessionFromJson(oldCycle.get("value").get("session")))
                && v5.owner().equals(sessionFromJson(imported.get("session")))
                && !cycle.session().game().equals(v5.owner().game()) && !cycle.session().game().equals(pair.frame().game())
                && sources.physicalSaveWitness().filter(pair.save()::equals).isPresent()
                && ContinuityJson.same(origin.get("restore_pair"), attachment.get(SavedAttachmentAuthority.PAIR_DETAIL))
                && ContinuityJson.same(origin.get("restore_pair"), imported.get("checkpoint_pair"))
                && opening.originals().contains(v5.targetEntry().reference())
                && actor.episodeRunId().equals(physical.episodeRunId())
                && actor.identity().player().equals(physical.identity().player())
                && actor.identity().dateRaw().equals(physical.identity().dateRaw());
        return exact ? Optional.of(List.of(openingRef, originRef, v5.targetEntry().reference())) : Optional.empty();
    }

    private static SavedOpeningAdvance savedOpeningEvidence(ContinuityBatchJournal.OpeningSaveAnchor anchor,
            ImportedOpeningAdvance latestLife) {
        return new SavedOpeningAdvance(anchor.confirmation(), anchor.receiptRef(), anchor.cycleRecord(), anchor.semantic(), Optional.ofNullable(latestLife));
    }

    SemanticEvidence openingSavedCycleSemantic(ExactRef record) {
        return load(record).semantic();
    }

    /** Qualify only current ordinary submission; this value cannot serve as a SAVE/cycle proof. */
    public void validateOrdinarySubmission(ContinuityStorePort.Session session, SessionIdentity owner, SemanticEvidence semantic) throws IOException {
        Objects.requireNonNull(session); Objects.requireNonNull(owner); Objects.requireNonNull(semantic);
        if (active.get() == null) {
            withLocked(session, () -> { validateOrdinarySubmission(session, owner, semantic); return true; });
            return;
        }
        StrictJson.require(active.get() == session, "ordinary submission cannot replace its original writer Session");
        sessionAuthority.require(session);
        var head = session.head(); requireOwner(head.state(), owner); requireActive(head.state());
        CycleState state = state(head.state(), owner); requireLegacyPendingClear(head.state(), state);
        requireFrontier(head.state(), state);
        archive.inHistoricalReadScope(session, new org.xar.ck3.control.application.action.ActionPorts.HistoricalReadLimits(
                4096, 256L * 1024 * 1024, 8192), ignored -> { validateChain(state); return true; });
        StrictJson.require(state.pending().isEmpty(), "ordinary submission cannot discard an unfinished cycle");
        var canonical = ContinuityActionJournal.receipts(head.state(), archive);
        StrictJson.require(ContinuityActionJournal.blockingUnresolved(session, head, archive, owner, canonical).isEmpty(),
                "ordinary submission cannot discard an unresolved original action");
        var verified = verify(session, owner, semantic); var frame = verified.frame();
        requireObservedBindingNotRegressed(head.state(), frame);
        StrictJson.require(frame.frame().revision().compareTo(StrictJson.integer(head.state().toJson().get("latest_binding").get("revision"),
                BigInteger.ZERO, StrictJson.UINT64_MAX)) >= 0, "ordinary submission regressed its canonical public revision");
        if (state.head().isPresent()) {
            var retained = load(state.head().orElseThrow()).semantic();
            requireObservedContinuation(retained.frame(), frame);
            StrictJson.require(frame.frame().revision().compareTo(retained.frame().frame().revision()) >= 0
                    && !verified.observedAt().isBefore(retained.observedAt()),
                    "ordinary submission regressed its retained cycle public revision or observation time");
        } else if (state.originFrame().isPresent()) {
            var retained = state.originFrame().orElseThrow();
            requireObservedContinuation(retained, frame);
            StrictJson.require(frame.frame().revision().compareTo(retained.frame().revision()) >= 0,
                    "ordinary submission regressed its origin public revision");
        } else requireSettledBinding(head.state(), frame);
        StrictJson.require(head.digest().equals(session.head().digest()), "ordinary submission changed its actual writer head");
    }

    /** Rechecks the completed proof or its exact surviving saved branch. */
    public String verifyCompletedCycleProof(ContinuityStorePort.Session session, SessionIdentity owner, CompletedCycleProof proof) throws IOException {
        return verifyCompletedCycleProof(session, owner, proof, false);
    }

    /** A new SAVE capture requires the current completed cycle and a nonregressed Native proof. */
    public String verifyCurrentCompletedCycleProof(ContinuityStorePort.Session session, SessionIdentity owner,
            CompletedCycleProof proof) throws IOException {
        return verifyCompletedCycleProof(session, owner, proof, true);
    }

    private String verifyCompletedCycleProof(ContinuityStorePort.Session session, SessionIdentity owner,
            CompletedCycleProof proof, boolean currentCapture) throws IOException {
        Objects.requireNonNull(session); Objects.requireNonNull(owner); Objects.requireNonNull(proof);
        if (active.get() == null) return withLocked(session, () -> verifyCompletedCycleProof(session, owner, proof, currentCapture));
        StrictJson.require(active.get() == session, "cycle proof verifier cannot borrow a replacement writer session");
        sessionAuthority.require(session);
        var head = session.head(); requireOwner(head.state(), owner); ObjectNode whole = head.state().toJson();
        CycleState current = whole.has(STATE_FIELD) ? parseState(whole.get(STATE_FIELD))
                : new CycleState(owner, head.state().settledCycles(), head.state().settledCycles(), Optional.empty(), Optional.empty(), Optional.empty(),Optional.empty(),Optional.empty());
        CycleState selected = current; boolean savedBranch = false;
        if (whole.has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)) {
            ObjectNode saved = StrictJson.object(whole.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD), Set.of("pair", "state"));
            CycleState survived = parseState(saved.get("state"));
            if (survived.session().equals(owner) && ContinuityJson.digest(survived.toJson()).equals(proof.cycleStateDigest())) {
                CheckpointPair pair = CheckpointPairCodec.decode(ContinuityJson.canonical(saved.get("pair")));
                if (currentCapture) {
                    if (head.state().status() != ContinuityState.Status.REPAIR_REQUIRED)
                        requireSavedContinuation(pair.frame(), proof.frame());
                } else {
                    selected = survived; savedBranch = true;
                    requireSavedContinuation(proof.frame(), pair.frame());
                    StrictJson.require(selected.completedCycles() == head.state().settledCycles(), "saved cycle proof is not the current surviving saved frontier");
                }
            }
        }
        if (!savedBranch) requireRetainedProofRole(session, head.state(), owner);
        StrictJson.require(selected.session().equals(owner), "cycle proof crossed its actual session owner");
        requireProof(selected, proof); requireFrontier(head.state(), selected); validateChain(selected);
        VerifiedSemantic verified = verify(session, owner, proof.semantic());
        if (!savedBranch) { requireLegacyPendingClear(head.state(), selected); requireProofFrame(head.state(), selected, verified); }
        else requireSavedProofFrame(head.state(),selected,verified);
        StrictJson.require(head.digest().equals(session.head().digest()), "writer changed during completed-cycle proof verification");
        // The checked head is fresh on every call; the result binds stable material across current -> saved.
        return proofMaterialDigest(owner,proof,verified);
    }
    /** Immutable retained SAVE sources are checked against the actual canonical historical head, never promoted to current credit. */
    public String verifyHistoricalCompletedCycleProof(ContinuityStorePort.Session session,SessionIdentity owner,
            CompletedCycleProof proof,ContinuityState capturedOriginalHead) throws IOException {
        Objects.requireNonNull(session);Objects.requireNonNull(owner);Objects.requireNonNull(proof);Objects.requireNonNull(capturedOriginalHead);
        if(active.get()==null)return withLocked(session,()->verifyHistoricalCompletedCycleProof(session,owner,proof,capturedOriginalHead));
        StrictJson.require(active.get()==session,"historical cycle verification cannot replace its original writer Session");
        sessionAuthority.require(session);String current=session.head().digest();
        ContinuityState original=session.requireHistoricalState(capturedOriginalHead.sequence(),ContinuityJson.digest(capturedOriginalHead.toJson()));
        StrictJson.require(original.toJson().equals(capturedOriginalHead.toJson()),"retained cycle source differs from the actual canonical historical state");
        requireOwner(original,owner);requireRetainedProofRole(session,original,owner);CycleState source=state(original,owner);
        requireLegacyPendingClear(original,source);requireProof(source,proof);requireFrontier(original,source);validateChain(source);
        VerifiedSemantic verified=verify(session,owner,proof.semantic());requireProofFrame(original,source,verified);
        StrictJson.require(current.equals(session.head().digest()),"canonical writer changed during immutable historical cycle verification");
        return proofMaterialDigest(owner,proof,verified);
    }
    private static String proofMaterialDigest(SessionIdentity owner,CompletedCycleProof proof,VerifiedSemantic verified) {
        ObjectNode checked=StrictJson.object();checked.put("cycle_state_digest",proof.cycleStateDigest());
        checked.put("semantic_digest",verified.materialDigest());checked.set("session",sessionToJson(owner));return ContinuityJson.digest(checked);
    }
    void retain(ContinuityStorePort.Session session, SessionIdentity owner, ActionReceipt receipt) throws IOException {
        var head = session.head(); ExactRef receiptRef = archive.receiptReferenceOf(receipt); canonicalReceipt(head.state(), receiptRef, owner);
        CycleState state = state(head.state(), owner); requireFrontier(head.state(), state);
        if (find(state, receiptRef).isPresent()) return; // A read-only reconciliation never counts an old cycle twice.
        if (state.pending().filter(receiptRef::equals).isPresent()) return; // Recovery resumes the original RETAIN without another writer event.
        var request = cycleRequest(owner, "RETAIN", receiptRef, Optional.empty(), Optional.empty(), Optional.empty());
        session.commit(session.preview(request));
    }
    /** Select observation DATA only; a completed original still passes the unchanged settle/proof validation. */
    boolean requiresFreshAfterCycle(ContinuityStorePort.Session session,SessionIdentity owner,ActionReceipt receipt)throws IOException {
        StrictJson.require(active.get()==session,"cycle observation must use its actual locked writer Session");
        sessionAuthority.require(session);
        var head=session.head();requireOwner(head.state(),owner);
        ExactRef ref=archive.receiptReferenceOf(receipt);
        StrictJson.require(canonicalReceipt(head.state(),ref,owner).equals(receipt),"cycle observation changed its canonical original receipt");
        CycleState current=state(head.state(),owner);requireLegacyPendingClear(head.state(),current);requireFrontier(head.state(),current);
        boolean completed=find(current,ref).isPresent(); // find validates the entire immutable chain, including its origins.
        if(completed)StrictJson.require(current.pending().isEmpty(),"a completed original cannot conceal another pending cycle");
        else StrictJson.require(current.pending().filter(ref::equals).isPresent(),"after-SEM requires the exact actual retained pending original");
        StrictJson.require(head.digest().equals(session.head().digest()),"cycle observation selection changed its actual writer head");
        return !completed;
    }
    CompletedCycleProof settle(ContinuityStorePort.Session session, SessionIdentity owner, ActionReceipt receipt, SemanticEvidence semantic) throws IOException {
        var head = session.head(); ExactRef receiptRef = archive.receiptReferenceOf(receipt); canonicalReceipt(head.state(), receiptRef, owner);
        CycleState state = state(head.state(), owner); requireFrontier(head.state(), state);
        if (find(state, receiptRef).isPresent()) return cycleProof(session, owner, semantic).orElseThrow(() -> new IOException("another real AUTO awaits SEM"));
        VerifiedSemantic checked = verify(session, owner, semantic); freshAfter(receipt, checked);
        Classification classification = classify(receipt);
        long cycles = Math.addExact(state.completedCycles(), classification == Classification.CONTROL_ONLY ? 0 : 1);
        CycleRecord record = new CycleRecord(owner, receiptRef, semantic, state.head(), cycles, classification);
        RawJson material = new RawJson(ContinuityJson.canonical(record.toJson())); ExactRef recordRef = archive.preserveMaterial(material);
        var request = cycleRequest(owner, "SETTLE", receiptRef, Optional.of(semantic), Optional.of(recordRef), Optional.of(record));
        session.commit(session.preview(request));
        return cycleProof(session, owner, semantic).orElseThrow(() -> new IOException("cycle commit did not clear its actual pending receipt"));
    }
    WriterContracts.Request batchRequest(JournalInput input) { return batchRequest(input, Optional.empty()); }
    /** Actual journal SAVE path: admit and capture before freezing canonical request DATA. */
    WriterContracts.Request batchRequest(ContinuityStorePort.Session same, JournalInput input) throws IOException {
        Objects.requireNonNull(input);
        if (input.kind() != JournalKind.SAVE_CONFIRMED) return batchRequest(input);
        StrictJson.require(active.get() == same, "SAVE request preparation requires its original current authority scope");
        sessionAuthority.require(same);
        var head = same.head(); requireOwner(head.state(), input.session());
        ObjectNode details = batchDetails(input); strictBatch(details);
        StrictJson.require(input.pair().isPresent() && input.completedCycleProof().isPresent(), "SAVE capture requires actual pair and completed proof");
        // This dry pure reduction enforces RUNNING/COMPLETE or the exact reconciled-repair role before any capture.
        reduceConfirmedSave(head.state(), input.session(), details);
        var captured = verifySaveCapture(same, head, input.session(), input.pair().orElseThrow(), input.completedCycleProof().orElseThrow());
        StrictJson.require(head.digest().equals(same.head().digest()), "SAVE request capture changed its original predecessor");
        return batchRequest(input, captured.material());
    }
    private static ObjectNode batchDetails(JournalInput input) {
        StrictJson.require(input.kind()!=JournalKind.WORKER_RESTART_CAPTURE,"restart capture requires the private original Controller producer");
        ObjectNode details = StrictJson.object(); details.put("evidence_id", input.batchId() + ":" + input.kind()
                + input.pair().map(pair -> ":" + pair.saveActionId()).orElse(""));
        details.put("source", input.kind()==JournalKind.BATCH_INTERRUPTED?"java-ordinary-batch-interruption/v2":"java-ordinary-session/v1"); details.set("session", sessionToJson(input.session()));
        details.put("batch_id", input.batchId()); details.put("boundary", input.kind().name());
        details.set("checkpoint_pair", input.pair().map(pair -> StrictJson.parse(CheckpointPairCodec.encode(pair))).orElseGet(() -> com.fasterxml.jackson.databind.node.NullNode.instance));
        if (input.completedCycleProof().isPresent()) details.set("completed_cycle_proof", proofToJson(input.completedCycleProof().orElseThrow()));
        else details.putNull("completed_cycle_proof");
        return details;
    }
    private static WriterContracts.Request batchRequest(JournalInput input,
            Optional<org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence> material) {
        ObjectNode details = batchDetails(input);
        material.ifPresent(value -> {
            StrictJson.require(input.kind() == JournalKind.SAVE_CONFIRMED, "only SAVE can carry original material DATA");
            value.requireSavedBranch(input.pair().orElseThrow(), input.session());
            details.put("source", SAVED_MATERIAL_SOURCE);
            details.set(org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence.FIELD, value.toJson());
        });
        List<ExactRef> evidence = new ArrayList<>(input.evidence());
        if (input.kind() == JournalKind.SAVE_CONFIRMED) {
            StrictJson.require(input.pair().isPresent() && input.completedCycleProof().isPresent(),
                    "confirmed SAVE requires its actual physical pair and completed-cycle proof");
            var pair = input.pair().orElseThrow();
            // The complete FileWitness remains in checkpoint_pair, and verify() independently
            // reopens/revalidates this physical SAVE. It is not a small immutable native packet.
            evidence.removeIf(ref -> ref.equals(pair.save().reference()));
        }
        material.ifPresent(value -> evidence.add(value.material().reference()));
        input.completedCycleProof().ifPresent(proof -> evidence.addAll(proof.semantic().references()));
        return new WriterContracts.Request(BATCH_KIND, ContinuityJson.canonical(details), evidence.stream().distinct().toList());
    }
    void requireCapturedRestartFrame(ContinuityStorePort.Session same,ContinuityState captured,
            ControllerRestartState controller,CleanBatchRestart manifest)throws IOException {
        StrictJson.require(active.get()==same,"captured frontier requires the actual held writer scope");
        var cycle=state(captured,controller.owner());
        long date=cycle.head().isPresent()?load(cycle.head().orElseThrow()).semantic().frame().frame().identity().dateRaw().longValueExact()
                :cycle.originFrame().isPresent()?cycle.originFrame().orElseThrow().frame().identity().dateRaw().longValueExact()
                :number(StrictJson.object(captured.toJson().get("latest_binding"),Set.of("date_raw","actor_character_id","episode_run_id","snapshot_id","revision","native_revision")),"date_raw");
        StrictJson.require(manifest.dateRaw()==date&&date>=captured.settledDateRaw(),"captured restart current date differs from its actual historical cycle frontier");
        for(var receipt:ContinuityActionJournal.receipts(captured,archive.withSession(same)))
            StrictJson.require(receipt.settled(),"captured recovery cannot discard an UNKNOWN original action");
    }
    /** A missing current observation can defer a cooperative stop capture; it is not a ticket. */
    public static final class MissingDriverObservation extends IOException {
        private static final long serialVersionUID = 1L;
        public MissingDriverObservation() { super("restart requires the actual latest complete Driver observation"); }
    }

    ContinuityBatchJournal.CleanRestartTicket captureRestart(ContinuityStorePort.Session same,
            ControllerRestartState controller,org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known)throws IOException {
        StrictJson.require(active.get()==same&&restartCapture.get()==null,"one actual writer restart capture required");
        requireRestartClean(same,controller.owner());
        var observation=known.observation().orElseThrow(MissingDriverObservation::new);
        StrictJson.require(observation.transport().machineId().equals(controller.owner().machineId())
                &&observation.transport().game().equals(controller.owner().game())&&observation.transport().sessionId().equals(controller.owner().sessionId()),
                "restart observation crossed the actual owned Game/session");
        // Preserve all durable facts. Old receive custody is deliberately excluded from the new producer's current observation.
        var durable=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known(known.driver(),known.stamp(),known.originalHistoryBasis(),
                known.actionRows(),known.auxiliary(),known.loop(),Optional.empty());
        ExactRef full=archive.preserveMaterial(RawJson.fullMaterial(known.driver().encode()));
        ExactRef facts=archive.preserveMaterial(org.xar.ck3.control.application.driver.DriverSnapshotFacts.encodeKnownOriginal(durable));
        ExactRef state=archive.preserveMaterial(new RawJson(controller.encode()));
        var predecessor=same.head().state();var currentCycle=state(predecessor,controller.owner());
        long dateRaw=currentCycle.head().isPresent()?load(currentCycle.head().orElseThrow()).semantic().frame().frame().identity().dateRaw().longValueExact()
                :currentCycle.originFrame().isPresent()?currentCycle.originFrame().orElseThrow().frame().identity().dateRaw().longValueExact()
                :number(StrictJson.object(predecessor.toJson().get("latest_binding"),Set.of("date_raw","actor_character_id","episode_run_id","snapshot_id","revision","native_revision")),"date_raw");
        var manifest=new CleanBatchRestart(state,facts,full,observation.transport(),observation.publicRevision(),observation.nativeRevision(),observation.observationVersion(),dateRaw,observation.source());
        ExactRef manifestRef=archive.preserveMaterial(new RawJson(manifest.encode()));
        ObjectNode details=StrictJson.object();details.put("evidence_id",controller.batchPrefix()+":restart:"+controller.nextBatchSequence()+":"+ContinuityJson.digest(predecessor.toJson()));
        details.put("source","java-ordinary-session/v1");details.set("session",sessionToJson(controller.owner()));
        details.put("batch_id",controller.batchPrefix()+":restart:"+controller.nextBatchSequence());details.put("boundary",JournalKind.WORKER_RESTART_CAPTURE.name());
        details.putNull("checkpoint_pair");details.putNull("completed_cycle_proof");details.set("restart_manifest",manifestRef.toJson());
        List<ExactRef> evidence=new ArrayList<>(List.of(state,facts,full,manifestRef,known.originalHistoryBasis()));
        known.loop().ifPresent(loop->evidence.add(loop.originalFacts()));
        known.actionRows().forEach(row->{if(row.coverageSource() instanceof org.xar.ck3.control.application.driver.DriverSnapshotFacts.LegacyHistoryRow legacy)evidence.add(legacy.originalRow());
            else evidence.add(((org.xar.ck3.control.application.driver.DriverSnapshotFacts.CanonicalOnly)row.coverageSource()).originalSource());});
        restartCapture.set(new RestartCapture(manifestRef,controller));
        try {
            var receipt=same.commit(same.preview(new WriterContracts.Request(BATCH_KIND,ContinuityJson.canonical(details),evidence.stream().distinct().toList())));
            return new ContinuityBatchJournal.CleanRestartTicket(same.persistedHead(),receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson()),manifestRef);
        } finally {restartCapture.remove();}
    }
    void requireRestartClean(ContinuityStorePort.Session same,SessionIdentity owner)throws IOException {
        StrictJson.require(active.get()==same,"restart check requires the original writer scope");
        var head=same.head();requireOwner(head.state(),owner);requireActive(head.state());
        var cycle=state(head.state(),owner);requireLegacyPendingClear(head.state(),cycle);validateChain(cycle);requireFrontier(head.state(),cycle);
        StrictJson.require(cycle.pending().isEmpty(),"unfinished ordinary cycle cannot restart");
        ObjectNode whole=head.state().toJson();
        for(String key:List.of("pending_cycle","pending_checkpoint"))StrictJson.require(!whole.has(key)||whole.get(key).isNull(),"original pending cycle/SAVE cannot restart");
        var raw = ContinuityActionJournal.receipts(head.state(), archive);
        StrictJson.require(ContinuityActionJournal.blockingUnresolved(same, head, archive, owner, raw).isEmpty(),
                "unresolved original action remains retained without replay");
    }
    /** Pure old-branch preflight before a new operator native attempt. Actual Root source qualification remains mandatory. */
    public void requireOperatorBefore(ContinuityStorePort.Session same,SessionIdentity owner,
            DriverStateSnapshot.Complete actualBeforeDriver,BigInteger actualDateRaw)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(owner);Objects.requireNonNull(actualBeforeDriver);Objects.requireNonNull(actualDateRaw);
        StrictJson.require(actualDateRaw.signum()>=0&&actualDateRaw.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,"actual safe original date required");
        withLocked(same,()->{
            var head=same.head();requireOwner(head.state(),owner);requireActive(head.state());
            var before=state(head.state(),owner);validateChain(before);requireLegacyPendingClear(head.state(),before);
            StrictJson.require(before.pending().isEmpty(),"operator cannot discard the original unfinished cycle");requireFrontier(head.state(),before);
            ObjectNode whole=head.state().toJson();
            for(String key:List.of("pending_cycle","pending_checkpoint"))StrictJson.require(!whole.has(key)||whole.get(key).isNull(),"operator cannot replace an original pending cycle or SAVE");
            for(ActionReceipt row:ContinuityActionJournal.receipts(head.state(),archive)) {
                var command=row.command();
                if(command.origin().machineId().equals(owner.machineId())&&command.origin().game().equals(owner.game())&&command.sessionId().equals(owner.sessionId()))
                    StrictJson.require(row.settled(),"operator cannot erase another original unresolved action");
            }
            var original=actualBeforeDriver.session();ObjectNode opening=StrictJson.object();
            opening.put("actor_character_id",original.actorId());opening.put("episode_run_id",original.episodeRunId());opening.put("date_raw",actualDateRaw);
            requireOperatorAnchor(before,original.actorId(),original.episodeRunId(),actualDateRaw,opening);
            StrictJson.require(same.head().digest().equals(head.digest()),"pure operator preflight changed its original writer head");
            return true;
        });
    }
    record TransportEvidence(ContinuityState head,ExactRef origin,SameGameTransportContinuity.Evidence evidence,
            CompletedCycleProof proof,Optional<WriterContracts.Receipt> committed,
            boolean checkpointRequired,Optional<CheckpointPair> savedFrontier) { }
    void requireHistoricalTransportEvidence(ContinuityStorePort.Session same,TransportEvidence actual)throws IOException {
        sessionAuthority.require(same);StrictJson.require(active.get()==same,"transport history requires the identical borrowed Cycle scope");
        var historical=same.requireHistoricalState(actual.head().sequence(),ContinuityJson.digest(actual.head().toJson()));
        StrictJson.require(historical.toJson().equals(actual.head().toJson()),"transport admission lost its actual qualified whole state");
        verifyHistoricalCompletedCycleProof(same,actual.evidence().afterOwner(),actual.proof(),historical);
        CycleState branch=state(historical,actual.evidence().afterOwner());
        StrictJson.require(branch.episodeOrigin().filter(actual.origin()::equals).isPresent(),"transport admission lost its exact canonical origin");
        ObjectNode origin=ContinuityJson.parseObject(archive.loadMaterial(actual.origin()).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
        StrictJson.require(actual.evidence().toJson(archive).equals(origin.get("transport_evidence")),
                "transport admission changed its retained NS source evidence");
    }
    /** Actual installed NS/M3 prepared custody encloses canonical preview and commit after its physical loan closes. */
    TransportEvidence rebindTransport(ContinuityStorePort.Session same,SessionIdentity afterOwner,
            ActionCommand exactParent,Instant deadline)throws IOException,InterruptedException {
        sessionAuthority.require(same);Objects.requireNonNull(afterOwner);Objects.requireNonNull(exactParent);Objects.requireNonNull(deadline);
        SameGameTransportContinuity.Port installed=transportRebindPort;
        if(installed==null)throw new IOException("actual installed same-Game transport custody is unavailable");
        CycleState prior=retainedStateForTransport(same.head().state(),exactParent);
        SessionIdentity beforeOwner=prior.session();
        SessionIdentity expectedBefore=beforeOwner;
        return installed.withCurrent(same,expectedBefore,afterOwner,exactParent,deadline,scope->withLocked(same,()->{
            Objects.requireNonNull(scope);var evidence=Objects.requireNonNull(scope.evidence());
            StrictJson.require(evidence.beforeOwner().equals(expectedBefore)&&evidence.afterOwner().equals(afterOwner)
                    &&sameTransportParent(evidence.canonicalParent().command(),exactParent),"actual transport scope changed requested owners or original parent");
            scope.requireCurrent(same);requireTransportCurrent(same,same.head(),evidence);
            CycleState before=retainedStateForTransport(same.head().state(),exactParent);validateChain(before);
            Optional<WriterContracts.Receipt> committed=Optional.empty();ExactRef origin;
            if(before.session().equals(afterOwner)&&before.episodeOrigin().isPresent()
                    &&sameTransportOrigin(before.episodeOrigin().orElseThrow(),evidence)) {
                origin=before.episodeOrigin().orElseThrow();
            }else {
                StrictJson.require(before.session().equals(evidence.beforeOwner()),"transport scope does not own the actual retained Cycle");
                WriterContracts.Head head=same.head();ObjectNode original=transportOrigin(head,before,evidence);
                origin=archive.preserveMaterial(new RawJson(ContinuityJson.canonical(original)));
                ObjectNode row=StrictJson.object();row.put("evidence_id","transport-cycle:"+origin.sha256());
                row.put("source","java-private-same-game-transport/v1");row.put("operation","TRANSPORT_REBIND");
                row.set("session",sessionToJson(afterOwner));row.set("before_session",sessionToJson(before.session()));
                row.put("predecessor_head_digest",head.digest());row.set("transport_evidence",evidence.toJson(archive));
                row.set("previous_state_ref",origin.toJson());row.set("new_cycle_state",transportState(before,evidence,origin).toJson());
                var refs=new ArrayList<>(evidence.references(archive));refs.add(origin);
                StrictJson.require(transportContext.get()==null,"nested actual transport rebind scope is forbidden");
                transportContext.set(new TransportContext(scope,evidence));
                try {
                    var request=new WriterContracts.Request(CYCLE_KIND,ContinuityJson.canonical(row),refs.stream().distinct().toList());
                    var result=same.commit(same.preview(request));committed=Optional.of(result);
                    scope.requireCommitted(same,result);
                }finally{transportContext.remove();}
            }
            var proof=cycleProof(same,afterOwner,evidence.semantic()).orElseThrow(()->new IOException("actual transport Cycle remains unfinished"));
            var frontier=savedCycleFrontier(same,afterOwner,state(same.head().state(),afterOwner),proof.frame());
            ObjectNode retained=ContinuityJson.parseObject(archive.loadMaterial(origin).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
            var originalEvidence=SameGameTransportContinuity.fromJson((ObjectNode)retained.get("transport_evidence"),archive);
            return new TransportEvidence(same.head().state(),origin,originalEvidence,proof,committed,frontier.checkpointRequired(),frontier.pair());
        }));
    }
    private static boolean sameTransportParent(ActionCommand left,ActionCommand right) {
        return java.util.Arrays.equals(ActionCodec.encodeCommand(left),ActionCodec.encodeCommand(right));
    }
    private boolean sameTransportOrigin(ExactRef reference,SameGameTransportContinuity.Evidence expected) {
        ObjectNode origin=ContinuityJson.parseObject(archive.loadMaterial(reference).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
        if(!TRANSPORT_ORIGIN_SCHEMA.equals(text(origin,"schema")))return false;
        var old=SameGameTransportContinuity.fromJson((ObjectNode)origin.get("transport_evidence"),archive);
        return old.purpose()==expected.purpose()&&old.afterOwner().equals(expected.afterOwner())
                &&old.canonicalMetadata().equals(expected.canonicalMetadata())&&old.canonicalSequence()==expected.canonicalSequence()
                &&old.canonicalEventIdentity().equals(expected.canonicalEventIdentity())&&old.canonicalHeadDigest().equals(expected.canonicalHeadDigest())
                &&sameTransportParent(old.canonicalParent().command(),expected.canonicalParent().command());
    }
    private static CycleState retainedStateForTransport(ContinuityState head,ActionCommand parent) {
        ObjectNode whole=head.toJson();if(whole.has(STATE_FIELD))return parseState(whole.get(STATE_FIELD));
        return retainedState(head,new SessionIdentity(parent.origin().machineId(),parent.origin().game(),parent.sessionId()));
    }
    private void requireTransportCurrent(ContinuityStorePort.Session same,WriterContracts.Head head,
            SameGameTransportContinuity.Evidence evidence)throws IOException {
        requireOwner(head.state(),evidence.afterOwner());requireActive(head.state());
        ActionReceipt parent=evidence.canonicalParent();ActionCommand command=parent.command();
        StrictJson.require(command.origin() instanceof CommandOrigin.LifecycleTerminal
                &&LifecycleComposites.parentKind(command.operation()).filter(kind->kind==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR).isPresent(),
                "transport continuation requires the actual original CONTINUE parent");
        StrictJson.require(ContinuityActionJournal.lookup(head.state(),command.actionId(),archive).filter(parent::equals).isPresent()
                &&archive.loadReceipt(archive.receiptReferenceOf(parent)).equals(parent),"transport scope lost its actual canonical parent receipt");
        if(evidence.purpose()==SameGameTransportContinuity.Purpose.PENDING_REBIND)
            StrictJson.require(!parent.settled(),"pending transport custody cannot replace settled final metadata");
        else {
            ActionState.Settlement settlement=parent.state() instanceof ActionState.Settled value?value.settlement()
                    :parent.state() instanceof ActionState.CompositeSettled value?value.settlement():null;
            StrictJson.require(parent.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    &&settlement instanceof ActionState.LifecycleApplied applied
                    &&applied.proof().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,
                    "finalized transport metadata requires its actual committed CONTINUE parent");
        }
        var composite=ActionTransitions.composite(parent.state());
        for(ActionReceipt row:ContinuityActionJournal.receipts(head.state(),archive)) {
            if(row.settled()||!row.command().origin().game().equals(evidence.afterOwner().game())
                    ||!row.command().origin().machineId().equals(evidence.afterOwner().machineId()))continue;
            boolean original=row.command().actionId().equals(command.actionId())&&sameTransportParent(row.command(),command);
            boolean child=composite.isPresent()&&composite.orElseThrow().children().stream().anyMatch(item->
                    item.actionId().equals(row.command().actionId())&&item.bodySha256().equals(row.bodySha256()));
            StrictJson.require(original||child,"transport continuation cannot erase another original unresolved action");
        }
        CycleState prior=retainedStateForTransport(head.state(),command);validateChain(prior);requireFrontier(head.state(),prior);
        StrictJson.require(prior.pending().isEmpty(),"transport continuation cannot discard an unfinished ordinary Cycle");
        requireLegacyPendingClear(head.state(),prior);
        SameGameTransportContinuity.Port installed=transportRebindPort;if(installed==null)throw new IOException("actual transport history reader is unavailable");
        installed.requireRecorded(same,evidence);verify(same,evidence.afterOwner(),evidence.semantic());
        StrictJson.require(same.head().digest().equals(head.digest()),"transport source changed the actual held writer head");
    }
    private ObjectNode transportOrigin(WriterContracts.Head head,CycleState before,SameGameTransportContinuity.Evidence evidence) {
        ObjectNode row=StrictJson.object();row.put("schema",TRANSPORT_ORIGIN_SCHEMA);
        row.set("after_session",sessionToJson(evidence.afterOwner()));row.set("previous_cycle_state",before.toJson());
        row.set("semantic",semanticToJson(evidence.semantic()));row.set("transport_evidence",evidence.toJson(archive));
        row.put("before_head_sequence",head.state().sequence());row.put("before_head_digest",head.digest());return row;
    }
    private static CycleState transportState(CycleState before,SameGameTransportContinuity.Evidence evidence,ExactRef origin) {
        return new CycleState(evidence.afterOwner(),before.completedCycles(),before.completedCycles(),Optional.empty(),Optional.empty(),
                before.retainedLegacyPendingDigest(),Optional.of(evidence.semantic().frame()),Optional.of(origin));
    }
    private String revalidateTransport(ContinuityStorePort.Session same,WriterContracts.Head head,ObjectNode row)throws IOException {
        strictTransport(row);TransportContext context=transportContext.get();StrictJson.require(context!=null,"actual installed transport scope is required");
        var evidence=context.evidence();context.scope().requireCurrent(same);requireTransportCurrent(same,head,evidence);
        StrictJson.require(evidence.toJson(archive).equals(row.get("transport_evidence"))
                &&head.digest().equals(text(row,"predecessor_head_digest"))
                &&sessionFromJson(row.get("session")).equals(evidence.afterOwner())
                &&sessionFromJson(row.get("before_session")).equals(evidence.beforeOwner()),"transport preview changed its actual scope, owners or head");
        CycleState before=state(head.state(),evidence.beforeOwner());ExactRef origin=ExactRef.fromJson(row.get("previous_state_ref"));
        StrictJson.require(text(row,"evidence_id").equals("transport-cycle:"+origin.sha256())
                &&archive.loadMaterial(origin).equals(new RawJson(ContinuityJson.canonical(transportOrigin(head,before,evidence))))
                &&transportState(before,evidence,origin).toJson().equals(row.get("new_cycle_state")),"transport tombstone changed its retained real Cycle");
        return ContinuityJson.digest(row);
    }
    private ContinuityState reduceTransport(ContinuityState before,ObjectNode row) {
        strictTransport(row);var evidence=SameGameTransportContinuity.fromJson((ObjectNode)row.get("transport_evidence"),archive);
        CycleState old=state(before,sessionFromJson(row.get("before_session")));
        CycleState next=parseState(row.get("new_cycle_state"));ExactRef origin=ExactRef.fromJson(row.get("previous_state_ref"));
        StrictJson.require(old.session().equals(evidence.beforeOwner())&&next.session().equals(evidence.afterOwner())
                &&sessionFromJson(row.get("session")).equals(evidence.afterOwner())
                &&sessionFromJson(row.get("before_session")).equals(evidence.beforeOwner())
                &&text(row,"predecessor_head_digest").equals(ContinuityJson.digest(before.toJson()))
                &&text(row,"evidence_id").equals("transport-cycle:"+origin.sha256())
                &&next.toJson().equals(transportState(old,evidence,origin).toJson())&&old.pending().isEmpty(),
                "transport reducer must preserve the exact old branch and grant zero cycle credit");
        ObjectNode result=before.toJson();result.set(STATE_FIELD,next.toJson());result.set(WriterContracts.ORDINARY_CYCLE_REBIND_FIELD,origin.toJson());
        return ContinuityState.fromJson(result,before.machineId());
    }
    private static void strictTransport(ObjectNode row) {
        StrictJson.object(row,Set.of("evidence_id","source","operation","session","before_session","predecessor_head_digest",
                "transport_evidence","previous_state_ref","new_cycle_state"));
        StrictJson.require("TRANSPORT_REBIND".equals(text(row,"operation"))
                &&"java-private-same-game-transport/v1".equals(text(row,"source")),"known actual transport event required");
    }
    private void requireRecordedTransportOrigin(ObjectNode row,CycleState branch,CycleState before) {
        StrictJson.object(row,Set.of("schema","after_session","previous_cycle_state","semantic","transport_evidence","before_head_sequence","before_head_digest"));
        var evidence=SameGameTransportContinuity.fromJson((ObjectNode)row.get("transport_evidence"),archive);
        StrictJson.require(TRANSPORT_ORIGIN_SCHEMA.equals(text(row,"schema"))&&before.session().equals(evidence.beforeOwner())
                &&branch.session().equals(evidence.afterOwner())&&before.completedCycles()==branch.basisCycles()
                &&branch.originFrame().filter(evidence.semantic().frame()::equals).isPresent(),
                "recorded transport origin changed owner, original semantic frame or zero-credit basis");
        ContinuityStorePort.Session same=active.get();StrictJson.require(same!=null,"recorded transport history requires the actual writer scope");
        SameGameTransportContinuity.Port installed=transportRebindPort;
        if(installed==null)throw new IllegalStateException("actual installed NS transport historical reader is unavailable");
        try {
            installed.requireRecorded(same,evidence);
            ContinuityState original=same.requireHistoricalState(number(row,"before_head_sequence"),text(row,"before_head_digest"));
            StrictJson.require(retainedStateForTransport(original,evidence.canonicalParent().command()).toJson().equals(before.toJson()),
                    "transport tombstone differs from the exact actual predecessor whole state");
        }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
    private boolean transportParentMatches(ObjectNode origin,ActionReceipt parent,String publication) {
        var evidence=SameGameTransportContinuity.fromJson((ObjectNode)origin.get("transport_evidence"),archive);
        if(!sameTransportParent(evidence.canonicalParent().command(),parent.command()))return false;
        ActionState.Settlement settlement=parent.state() instanceof ActionState.Settled value?value.settlement()
                :parent.state() instanceof ActionState.CompositeSettled value?value.settlement():null;
        StrictJson.require(parent.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&settlement instanceof ActionState.LifecycleApplied,
                "transport episode admission requires the actual final confirmed original parent");
        var proof=((ActionState.LifecycleApplied)settlement).proof();proof.validateParent(parent.command());
        StrictJson.require(proof.kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,
                "transport history cannot replace another lifecycle operation");
        JsonNode encoded=LifecycleProofMaterialJson.proof(proof.encode());
        StrictJson.require(publication.equals(StrictJson.text(encoded.get("committed_event_identity"))),
                "transport episode history changed its actual final lifecycle publication");return true;
    }
    /** Same Game/run/epoch identity change; it neither submits native work nor completes an ordinary cycle. */
    void rebindOperator(ContinuityStorePort.Session same,SessionIdentity owner,ActionReceipt actual,SemanticEvidence semantic)throws IOException {
        var head=same.head();requireOperatorCurrent(same,head,owner,actual,semantic);
        var completion=requireOperatorEvidence(owner,actual,semantic);
        if(!completion.rebindPerformed())return;
        CycleState before=state(head.state(),owner);validateChain(before);
        ExactRef receipt=archive.receiptReferenceOf(actual);
        if(before.episodeOrigin().isPresent()) {
            ObjectNode retained=ContinuityJson.parseObject(archive.loadMaterial(before.episodeOrigin().orElseThrow()).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
            if(OPERATOR_ORIGIN_SCHEMA.equals(text(retained,"schema"))&&receipt.equals(ExactRef.fromJson(retained.get("operator_receipt_ref")))) {
                StrictJson.require(before.originFrame().filter(semantic.frame()::equals).isPresent(),"same operator changed its original cycle binding");return;
            }
        }
        requireOperatorPredecessor(head.state(),before,actual);
        ObjectNode origin=operatorOrigin(head,before,owner,receipt,semantic);ExactRef retained=archive.preserveMaterial(new RawJson(ContinuityJson.canonical(origin)));
        ObjectNode row=StrictJson.object();row.put("evidence_id","operator-cycle:"+actual.command().actionId());row.put("source","java-private-operator-cycle/v1");
        row.put("operation","OPERATOR_REBIND");row.set("session",sessionToJson(owner));row.set("operator_receipt_ref",receipt.toJson());
        row.put("predecessor_head_digest",head.digest());row.set("semantic",semanticToJson(semantic));row.set("previous_state_ref",retained.toJson());
        row.set("new_cycle_state",operatorState(before,semantic,retained).toJson());
        List<ExactRef> refs=new ArrayList<>(semantic.references());refs.addAll(completion.references());refs.add(receipt);refs.add(retained);
        same.commit(same.preview(new WriterContracts.Request(CYCLE_KIND,ContinuityJson.canonical(row),refs.stream().distinct().toList())));
    }
    private void requireOperatorCurrent(ContinuityStorePort.Session same,WriterContracts.Head head,SessionIdentity owner,ActionReceipt actual,SemanticEvidence semantic)throws IOException {
        requireOperatorEvidence(owner,actual,semantic);requireActive(head.state());
        OperatorAuthority installed=operatorAuthority;if(installed==null)throw new IOException("actual installed operator cycle source unavailable");
        StrictJson.require(ContinuityActionJournal.lookup(head.state(),actual.command().actionId(),archive).filter(actual::equals).isPresent()
                &&archive.loadReceipt(archive.receiptReferenceOf(actual)).equals(actual)&&!hasUnresolvedOtherAction(head.state(),actual),"operator requires its actual canonical settled receipt with no other unresolved action");
        ObjectNode whole=head.state().toJson();
        for(String key:List.of("pending_cycle","pending_checkpoint"))StrictJson.require(!whole.has(key)||whole.get(key).isNull(),"operator cannot erase an original pending cycle or SAVE");
        installed.requireCurrent(same,owner,actual,semantic);verify(same,owner,semantic);
        requireOperatorWindow(head.state(),actual);StrictJson.require(same.head().digest().equals(head.digest()),"operator source changed the original writer head during revalidation");
    }
    private void requireOperatorWindow(ContinuityState head,ActionReceipt actual) {
        var completion=((ActionState.OperatorRebound)((ActionState.Settled)actual.state()).settlement()).observation();
        if(EpisodeWindow.state(head).isPresent())EpisodeWindow.requireActive(head);
        var lineage=EpisodeWindow.operatorLineage(head);
        if(!completion.rebindPerformed())return;
        StrictJson.require(lineage.stream().anyMatch(value->value.actionId().equals(actual.command().actionId())
                &&value.bodySha256().equals(actual.bodySha256())&&value.requestId().equals(completion.requestId())
                &&value.before().actorId()==completion.priorActor()&&value.after().actorId()==completion.request().characterId()
                &&value.after().game().equals(completion.transport().game())&&value.after().sessionId().equals(completion.transport().sessionId())
                &&value.after().episodeRunId().equals(completion.episodeRunId())&&value.after().epoch()==completion.episodeEpoch()
                &&value.beforeDriverVersion()==completion.beforeDriverVersion()&&value.afterDriverVersion()==completion.afterDriverVersion()
                &&value.originals().beforeDriver().equals(completion.originals().beforeDriver())&&value.originals().afterDriver().equals(completion.originals().afterDriver())),
                "actual canonical opening has no exact original operator lineage");
    }
    private void requireOperatorPredecessor(ContinuityState whole,CycleState before,ActionReceipt actual) {
        StrictJson.require(before.pending().isEmpty(),"operator cannot discard an unfinished ordinary cycle");requireFrontier(whole,before);
        var completion=((ActionState.OperatorRebound)((ActionState.Settled)actual.state()).settlement()).observation();
        requireOperatorAnchor(before,BigInteger.valueOf(completion.priorActor()),completion.episodeRunId(),BigInteger.valueOf(completion.dateRaw()),operatorOpeningFrame(actual));
    }
    private void requireOperatorAnchor(CycleState before,BigInteger actor,String run,BigInteger date,ObjectNode opening) {
        ObjectNode frame=before.head().map(this::load).map(value->originalFrame(value.semantic().frame()))
                .orElseGet(()->before.originFrame().map(OrdinaryCycleTransitions::originalFrame).orElse(opening));
        StrictJson.require(org.xar.ck3.control.contracts.NativeCharacterId.fromJson(frame.get("actor_character_id")).asBigInteger().equals(actor)
                &&text(frame,"episode_run_id").equals(run)&&BigInteger.valueOf(number(frame,"date_raw")).compareTo(date)<=0,
                "operator original subject differs from the retained cycle frontier");
    }
    private static ObjectNode operatorOpeningFrame(ActionReceipt actual) {
        if(actual.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay)return originalFrame(actual.command().before());
        var original=actual.command().lifecycleBefore();ObjectNode row=StrictJson.object();
        row.put("actor_character_id",original.subject().characterId());row.put("episode_run_id",original.subject().episodeRunId());
        row.put("date_raw",original.frame().dateRaw());return row;
    }
    private ObjectNode operatorOrigin(WriterContracts.Head head,CycleState before,SessionIdentity owner,ExactRef receipt,SemanticEvidence semantic) {
        ObjectNode row=StrictJson.object();row.put("schema",OPERATOR_ORIGIN_SCHEMA);row.set("previous_cycle_state",before.toJson());
        row.set("after_session",sessionToJson(owner));row.set("operator_receipt_ref",receipt.toJson());row.set("semantic",semanticToJson(semantic));
        row.put("predecessor_sequence",head.state().sequence());row.put("predecessor_head_digest",head.digest());
        ObjectNode actual=head.state().toJson();for(String field:List.of(STATE_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD)) {
            ObjectNode slot=row.putObject(field);slot.put("present",actual.has(field));if(actual.has(field))slot.set("value",actual.get(field));
        }return row;
    }
    private static CycleState operatorState(CycleState before,SemanticEvidence semantic,ExactRef retained) {
        return new CycleState(before.session(),before.completedCycles(),before.completedCycles(),Optional.empty(),Optional.empty(),
                before.retainedLegacyPendingDigest(),Optional.of(semantic.frame()),Optional.of(retained));
    }
    private String revalidateOperator(ContinuityStorePort.Session same,WriterContracts.Head head,ObjectNode row)throws IOException {
        strictOperator(row);SessionIdentity owner=sessionFromJson(row.get("session"));
        ExactRef receiptRef=ExactRef.fromJson(row.get("operator_receipt_ref"));ActionReceipt actual=archive.loadReceipt(receiptRef);
        SemanticEvidence semantic=semanticFromJson(row.get("semantic"));requireOperatorCurrent(same,head,owner,actual,semantic);
        StrictJson.require(archive.receiptReferenceOf(actual).equals(receiptRef)&&text(row,"predecessor_head_digest").equals(head.digest())
                &&requireOperatorEvidence(owner,actual,semantic).rebindPerformed(),"operator event crossed its original receipt/head or no-op classification");
        CycleState before=state(head.state(),owner);validateChain(before);requireOperatorPredecessor(head.state(),before,actual);
        ExactRef retained=ExactRef.fromJson(row.get("previous_state_ref"));
        StrictJson.require(archive.loadMaterial(retained).equals(new RawJson(ContinuityJson.canonical(operatorOrigin(head,before,owner,receiptRef,semantic))))
                &&ContinuityJson.same(operatorState(before,semantic,retained).toJson(),row.get("new_cycle_state")),"operator cycle origin changed the actual retained branch");
        return ContinuityJson.digest(row);
    }
    private static ContinuityState reduceOperator(ContinuityState predecessor,ObjectNode row) {
        strictOperator(row);StrictJson.require(text(row,"operation").equals("OPERATOR_REBIND")&&text(row,"source").equals("java-private-operator-cycle/v1")
                &&text(row,"predecessor_head_digest").equals(ContinuityJson.digest(predecessor.toJson())),"operator reducer requires its exact original source/head");
        CycleState before=state(predecessor,sessionFromJson(row.get("session")));SemanticEvidence semantic=semanticFromJson(row.get("semantic"));
        StrictJson.require(before.pending().isEmpty(),"operator reducer cannot erase a pending cycle");
        CycleState exact=operatorState(before,semantic,ExactRef.fromJson(row.get("previous_state_ref")));
        StrictJson.require(ContinuityJson.same(exact.toJson(),row.get("new_cycle_state")),"operator reducer must preserve counters, source owner and original pending tombstone");
        ObjectNode result=predecessor.toJson();result.set(STATE_FIELD,exact.toJson());result.set(WriterContracts.ORDINARY_CYCLE_REBIND_FIELD,row.get("previous_state_ref"));
        return ContinuityState.fromJson(result,predecessor.machineId());
    }
    private static void strictOperator(ObjectNode row){StrictJson.object(row,Set.of("evidence_id","source","operation","session","operator_receipt_ref","predecessor_head_digest","semantic","previous_state_ref","new_cycle_state"));}
    private static final String EXTERNAL_SAVE_REBIND = "REBIND_EXTERNAL_SAVE";
    private record ExternalSaveRebind(ExternalSaveOrigin origin, SemanticEvidence semantic, ExactRef original) { }
    private final ThreadLocal<ExternalSaveRebind> externalSaveRebinding = new ThreadLocal<>();
    private volatile ExternalSaveAuthority externalSaveAuthority;

    /** Root verifies the actual held successor, manually loaded file and current Driver source. */
    @FunctionalInterface
    public interface ExternalSaveAuthority {
        void requireCurrent(ContinuityStorePort.Session same, ExternalSaveOrigin origin, SemanticEvidence semantic)
                throws IOException;
    }

    public synchronized void bindExternalSaveAuthority(ExternalSaveAuthority actual) {
        StrictJson.require(externalSaveAuthority == null, "external save authority is installed once by the actual Root");
        externalSaveAuthority = Objects.requireNonNull(actual);
    }

    WriterContracts.Receipt rebindExternalSave(ContinuityStorePort.Session same, ExternalSaveOrigin prepared,
            SemanticEvidence semantic) throws IOException {
        StrictJson.require(active.get() == same && externalSaveRebinding.get() == null,
                "external save observation requires the original borrowed writer and its private producer");
        var origin = prepared;
        origin.requireSemantic(semantic.frame());
        var head = same.head();
        origin.requireOriginal(head.state());
        var previous = state(head.state(), origin.departed());
        validateChain(previous);
        requireLegacyPendingClear(head.state(), previous);
        var original = archive.preserveMaterial(new RawJson(ContinuityJson.canonical(origin.toJson())));
        var details = StrictJson.object().put("evidence_id", "external-save:" + original.sha256())
                .put("source", ExternalSaveOrigin.SOURCE).put("operation", EXTERNAL_SAVE_REBIND);
        details.set("session", sessionToJson(origin.successor()));
        details.set("origin", origin.toJson());
        details.set("origin_ref", original.toJson());
        details.set("semantic", semanticToJson(semantic));
        var refs = new ArrayList<>(semantic.references());
        refs.add(original);
        refs.add(origin.loadedFile().reference());
        var request = new WriterContracts.Request(CYCLE_KIND, ContinuityJson.canonical(details), refs.stream().distinct().toList());
        externalSaveRebinding.set(new ExternalSaveRebind(origin, semantic, original));
        try {
            var preview = same.preview(request);
            var receipt = same.commit(preview);
            same.requireCommitted(preview, receipt);
            return receipt;
        } finally {
            externalSaveRebinding.remove();
        }
    }

    private String revalidateExternalSave(ContinuityStorePort.Session same, WriterContracts.Head head, ObjectNode details)
            throws IOException {
        var actual = externalSaveRebinding.get();
        StrictJson.require(actual != null && externalSaveAuthority != null,
                "external save rebind requires the private Root producer");
        requireExternalSaveDetails(details);
        var origin = actual.origin();
        origin.requireOriginal(head.state());
        StrictJson.require(sessionFromJson(details.get("session")).equals(origin.successor())
                && ContinuityJson.same(details.get("origin"), origin.toJson())
                && ContinuityJson.same(details.get("semantic"), semanticToJson(actual.semantic()))
                && ExactRef.fromJson(details.get("origin_ref")).equals(actual.original())
                && archive.loadMaterial(actual.original()).equals(new RawJson(ContinuityJson.canonical(origin.toJson())))
                && text(details, "evidence_id").equals("external-save:" + actual.original().sha256()),
                "external save observation changed its writer, current semantic or archived origin");
        externalSaveAuthority.requireCurrent(same, origin, actual.semantic());
        var originals = archive.withSession(same);
        var history = ContinuityActionJournal.receipts(head.state(), originals);
        var unresolved = history.stream().filter(action -> !action.settled()).toList();
        var retained = ContinuityActionJournal.externalSaveRetiredResume(same, origin, originals, history);
        StrictJson.require(unresolved.size() == 1 && retained.filter(unresolved.getFirst()::equals).isPresent(),
                "external save rebind requires the original retired positive-ACK RESUME as its sole unresolved receipt");
        var verified = verify(same, origin.successor(), actual.semantic());
        origin.requireSemantic(verified.frame());
        return verified.materialDigest();
    }

    private ContinuityState reduceExternalSave(ContinuityState predecessor, ObjectNode details) {
        requireExternalSaveDetails(details);
        var origin = ExternalSaveOrigin.fromJson(details.get("origin"));
        var owner = sessionFromJson(details.get("session"));
        var reference = ExactRef.fromJson(details.get("origin_ref"));
        var frame = semanticFromJson(details.get("semantic")).frame();
        origin.requireOriginal(predecessor);
        origin.requireSemantic(frame);
        StrictJson.require(origin.successor().equals(owner), "external save observation differs from its current successor");
        var previous = state(predecessor, origin.departed());
        StrictJson.require(previous.pending().isEmpty() && previous.completedCycles() >= predecessor.settledCycles(),
                "external save rebind cannot grant cycles or discard pending ordinary work");
        var restored = new CycleState(owner, previous.completedCycles(), previous.completedCycles(), Optional.empty(),
                Optional.empty(), Optional.of(legacyPendingDigest(predecessor)), Optional.of(frame), Optional.of(reference));
        var transition = StrictJson.object().put("evidence_id", text(details, "evidence_id"))
                .put("source", ExternalSaveOrigin.SOURCE);
        transition.set("successor_game", owner.game().toJson());
        transition.set("frame", originalFrame(frame));
        var next = OriginalWindowReducer.reduce(predecessor.toJson(), ExternalSaveOrigin.TRANSITION, transition, policy);
        next.set(STATE_FIELD, restored.toJson());
        next.set(WriterContracts.ORDINARY_EXTERNAL_SAVE_ORIGIN_FIELD, reference.toJson());
        return ContinuityState.fromJson(next, predecessor.machineId());
    }

    private static void requireExternalSaveDetails(ObjectNode details) {
        StrictJson.object(details, Set.of("evidence_id", "source", "operation", "session", "origin", "origin_ref", "semantic"));
        StrictJson.require(ExternalSaveOrigin.SOURCE.equals(text(details, "source"))
                && EXTERNAL_SAVE_REBIND.equals(text(details, "operation")), "external save rebind contract differs");
    }

    /** Historical canonical data only. Live Root authority is never invoked while replaying an old branch. */
    private void requireRecordedOperatorOrigin(ObjectNode row,CycleState branch,CycleState before) {
        StrictJson.object(row,Set.of("schema","previous_cycle_state","after_session","operator_receipt_ref","semantic","predecessor_sequence","predecessor_head_digest",
                STATE_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD));
        StrictJson.require(branch.basisCycles()==before.completedCycles()&&branch.session().equals(before.session()),"operator history changed its original cycle count or session");
        ExactRef ref=ExactRef.fromJson(row.get("operator_receipt_ref"));ActionReceipt actual=archive.loadReceipt(ref);SemanticEvidence semantic=semanticFromJson(row.get("semantic"));
        requireOperatorEvidence(branch.session(),actual,semantic);
        var same=active.get();StrictJson.require(same!=null,"historical operator lineage requires the original held writer");
        try {
            ContinuityState old=same.requireHistoricalState(number(row,"predecessor_sequence"),text(row,"predecessor_head_digest"));
            StrictJson.require(archive.receiptReferenceOf(actual).equals(ref)
                    &&ContinuityActionJournal.lookup(old,actual.command().actionId(),archive).filter(actual::equals).isPresent()
                    &&state(old,before.session()).toJson().equals(before.toJson()),"operator historical branch lost its canonical original receipt or predecessor");
            requireOperatorWindow(old,actual);requireOperatorPredecessor(old,before,actual);
            ObjectNode whole=old.toJson();for(String field:List.of(STATE_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD)) {
                ObjectNode slot=StrictJson.object(row.get(field),whole.has(field)?Set.of("present","value"):Set.of("present"));
                StrictJson.require(slot.get("present").isBoolean()&&slot.get("present").booleanValue()==whole.has(field)
                        &&(!whole.has(field)||whole.get(field).equals(slot.get("value"))),"operator history changed an original saved/cycle/rebind field");
            }
        }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
    WriterContracts.Receipt rebind(ContinuityStorePort.Session session, RestoreBinding binding) throws IOException {
        StrictJson.require(restoring.get()==null&&committedImportedRebinding.get()==null,"one actual restore binding per cycle transaction");
        restoring.set(Objects.requireNonNull(binding));
        try {
            var head = session.head();
            var imported = importedRestoreSources(binding);
            CycleState successor = restoredState(head.state(), binding, imported);
            RawJson tombstone = new RawJson(ContinuityJson.canonical(restoreTombstone(head.state(),binding.attachment().eventIdentity(),
                    binding.session(),binding.pair(),imported.isPresent())));
            ExactRef retained = archive.preserveMaterial(tombstone);
            ObjectNode details = restoreRebindDetails(binding.attachment().eventIdentity(),ContinuityJson.digest(binding.attachment().head().toJson()),
                    binding.session(),binding.pair(),binding.semantic(),successor,retained,imported.isPresent());
            List<ExactRef> evidence = new ArrayList<>(binding.semantic().references());
            evidence.add(retained);
            if (imported.isPresent()) {
                evidence.add(binding.pair().nativeAckRef());
                evidence.addAll(imported.orElseThrow().references());
                evidence.add(ContinuityActionJournal.recordHead(head.state()).orElseThrow());
            } else {
                evidence.add(binding.pair().save().reference());
            }
            evidence.add(binding.pair().driver().reference());
            var request = new WriterContracts.Request(CYCLE_KIND, ContinuityJson.canonical(details), evidence.stream().distinct().toList());
            return session.commit(session.preview(request));
        } finally { restoring.remove(); }
    }
    private static ObjectNode restoreRebindDetails(String attachmentIdentity,String attachmentDigest,SessionIdentity owner,
            CheckpointPair pair,SemanticEvidence semantic,CycleState successor,ExactRef retained,boolean imported) {
        var details=StrictJson.object().put("evidence_id","restore-cycle:"+attachmentIdentity)
                .put("source",imported?IMPORTED_RESTORE_SOURCE:RESTORE_SOURCE).put("operation","REBIND")
                .put("attachment_identity",attachmentIdentity).put("attachment_head_digest",attachmentDigest);
        details.set("session",sessionToJson(owner));details.set("restore_pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
        details.set("semantic",semanticToJson(semantic));details.set("previous_state_ref",retained.toJson());
        details.set("new_cycle_state",successor.toJson());return details;
    }
    WriterContracts.Receipt rebindCommittedImported(ContinuityStorePort.Session same,String predecessorDigest,
            ContinuityBatchJournal.ImportedRestoreRebindReadback original,SemanticEvidence fresh)throws IOException {
        StrictJson.require(active.get()==same&&restoring.get()==null&&committedImportedRebinding.get()==null,
                "one actual committed imported REBIND per borrowed writer scope required");
        var authority=committedImportedRebindAuthority;
        if(authority==null)throw new IOException("Actual successor Driver and SEM authority is not installed for committed imported REBIND");
        if(fresh==null)throw new IOException("An independently refreshed successor SEM is required for committed imported REBIND");
        var head=same.head();requireCommittedRebindPredecessor(head,original,predecessorDigest);
        var successor=original.recoveryBasis().successor();var pair=original.savedPair();
        var relevant=requireImportedCyclePredecessor(head.state(),successor,pair,fresh);
        var opening=ContinuityJson.object(head.state().toJson().get("latest_binding"));
        var historicalRevision=new BigInteger(StrictJson.text(opening.get("native_revision")));
        if(fresh.frame().frame().snapshotId().equals(StrictJson.text(opening.get("snapshot_id")))
                ||fresh.originalNativePacket().equals(original.recoveryBasis().secondNative().reference())
                ||fresh.frame().frame().identity().nativeRevision().compareTo(historicalRevision)<=0)
            throw new IOException("Committed imported REBIND requires a fresh successor Native publication after the historical opening");
        var seedPin=requireCommittedDriverSeed(same,original,fresh);
        requireImportedRestoreRetirement(original.attachment().before(),original.importedOrigin().owner(),pair);
        validateChain(parseState(head.state().toJson().get(STATE_FIELD)));
        authority.requireCurrent(same,original,fresh);
        var verified=verify(same,successor,fresh);
        requireCommittedRebindPredecessor(same.head(),original,head.digest());

        var cycle=restoredCycle(head.state(),successor,fresh);
        var edge=original.attachment();var tombstone=new RawJson(ContinuityJson.canonical(
                restoreTombstone(head.state(),edge.eventIdentity(),successor,pair,true)));
        var retained=archive.preserveMaterial(tombstone);
        var details=restoreRebindDetails(edge.eventIdentity(),ContinuityJson.digest(edge.after().toJson()),successor,pair,fresh,cycle,retained,true);
        var refs=new ArrayList<>(fresh.references());
        refs.addAll(List.of(retained,pair.driver().reference(),pair.nativeAckRef(),original.departedActionHead(),edge.eventPin().reference(),seedPin.reference()));
        refs.addAll(relevant.references());
        var request=new WriterContracts.Request(CYCLE_KIND,ContinuityJson.canonical(details),refs.stream().distinct().toList());
        committedImportedRebinding.set(new CommittedImportedRebind(original,fresh,seedPin,tombstone,head.digest(),request.identity(),verified));
        try {
            var prepared=same.preview(request);
            var result=same.commit(prepared);
            same.requireCommitted(prepared,result);
            return result;
        } finally {committedImportedRebinding.remove();}
    }

    private static void requireCommittedRebindPredecessor(WriterContracts.Head head,
            ContinuityBatchJournal.ImportedRestoreRebindReadback original,String expectedDigest)throws IOException {
        var edge=original.attachment();var state=head.state();var whole=state.toJson();
        if(head.snapshotNeedsRecovery()||!head.indexRepairs().isEmpty()||state.sequence()<edge.sequence()
                ||!head.digest().equals(expectedDigest)
                ||!head.documents().contains(edge.eventPin())
                ||!original.departedCycle().equals(new RawJson(ContinuityJson.canonical(whole.get(STATE_FIELD))))
                ||ContinuityActionJournal.recordHead(state).filter(original.departedActionHead()::equals).isEmpty())
            throw new IOException("Committed imported REBIND requires the qualified attachment suffix and unchanged departed cycle/action head");
    }

    private WriterContracts.Pin requireCommittedDriverSeed(ContinuityStorePort.Session same,
            ContinuityBatchJournal.ImportedRestoreRebindReadback original,SemanticEvidence fresh)throws IOException {
        var edge=original.attachment();var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.DOCUMENT_MAX_BYTES);
        var seedRow=details.get(RestoreSeedSupplement.DETAIL_FIELD);
        if(seedRow==null)throw new IOException("Committed attachment has no original pinned final Driver seed");
        try {
            var pin=WriterContracts.Pin.fromJson(seedRow);
            var seed=RestoreSeedSupplement.decode(same.readPinned(pin,RestoreSeedSupplement.MAXIMUM_BYTES));
            var delta=ContinuityJson.object(details.get("driver_snapshot"));
            var stamp=ContinuityJson.parseObject(archive.loadMaterial(fresh.driverStamp()).bytes(),ReadinessArchive.Role.DRIVER_STAMP.maximumBytes());
            if(!seed.requestId().equals(original.recoveryBasis().requestId())
                    ||!seed.successor().equals(original.recoveryBasis().successor())
                    ||!seed.fullDriver().equals(ExactRef.fromJson(details.get("restored_full_driver")))
                    ||!seed.fullDriver().equals(fresh.originalDriver())||!seed.fullDriver().sha256().equals(text(delta,"after_sha256"))
                    ||!seed.originalHistoryBasis().equals(ExactRef.fromJson(edge.before().toJson().get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)))
                    ||seed.driverVersion()!=Math.addExact(number(delta,"expected_version"),1)||seed.episodeEpoch()!=number(delta,"next_epoch")
                    ||seed.driverVersion()!=number(stamp,"driver_version")||seed.episodeEpoch()!=number(stamp,"episode_epoch")
                    ||!seed.fullDriver().sha256().equals(text(stamp,"driver_sha256")))
                throw new IOException("Current successor Driver and SEM differ from the original committed final seed");
            return pin;
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid committed Driver seed or current successor stamp DATA",invalid);}
    }

    WriterContracts.Receipt rebindEpisode(ContinuityStorePort.Session session,LifecycleEpisodeInputs inputs,LifecycleEpisodeInputs.Binding binding) throws IOException {
        StrictJson.require(episode.get()==null,"one actual lifecycle episode input per cycle transaction");
        inputs.requireCurrent(session,binding);episode.set(new EpisodeContext(inputs,binding));
        try {
            var head=session.head();CycleState before=state(head.state(),binding.beforeOwner());validateChain(before);requireEpisodePredecessor(head.state(),before,binding);
            ObjectNode tombstone=episodeTombstone(head.state(),before,binding);ExactRef retained=archive.preserveMaterial(new RawJson(ContinuityJson.canonical(tombstone)));
            CycleState next=episodeState(head.state(),before,binding,retained);
            ObjectNode row=StrictJson.object();row.put("evidence_id","episode-cycle:"+binding.parent().command().actionId());row.put("source","java-private-lifecycle-episode/v1");
            row.put("operation","EPISODE_REBIND");row.set("session",sessionToJson(binding.afterOwner()));row.set("before_session",sessionToJson(binding.beforeOwner()));
            row.set("parent_receipt_ref",archive.receiptReferenceOf(binding.parent()).toJson());row.put("lifecycle_commit_digest",binding.commitDigest());
            row.put("predecessor_head_digest",head.digest());row.set("semantic",semanticToJson(binding.semantic()));row.set("previous_state_ref",retained.toJson());row.set("new_cycle_state",next.toJson());
            List<ExactRef> refs=new ArrayList<>(binding.semantic().references());refs.add(retained);refs.add(archive.receiptReferenceOf(binding.parent()));
            return session.commit(session.preview(new WriterContracts.Request(CYCLE_KIND,ContinuityJson.canonical(row),refs.stream().distinct().toList())));
        }finally{episode.remove();}
    }
    /** A real current private publication may readopt its already recorded branch without another rebind. */
    boolean hasEpisodeAdmission(ContinuityStorePort.Session same,LifecycleEpisodeInputs inputs,LifecycleEpisodeInputs.Binding binding)throws IOException {
        inputs.requireCurrent(same,binding);CycleState current=state(same.head().state(),binding.afterOwner());validateChain(current);
        if(current.episodeOrigin().isEmpty())return false;
        ObjectNode origin=ContinuityJson.parseObject(archive.loadMaterial(current.episodeOrigin().orElseThrow()).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
        if(!"xar.java-ordinary-episode-origin/v1".equals(text(origin,"schema")))return false;
        if(!ExactRef.fromJson(origin.get("parent_receipt_ref")).equals(archive.receiptReferenceOf(binding.parent())))return false;
        StrictJson.require(text(origin,"lifecycle_commit_digest").equals(binding.commitDigest())
                &&ExactRef.fromJson(origin.get("predecessor_driver_ref")).equals(binding.predecessorDriverReference()),"recorded episode publication or causal predecessor differs");
        StrictJson.require(current.pending().isEmpty(),"an unfinished cycle cannot be discarded by readoption");
        requireLegacyPendingClear(same.head().state(),current);requireFrontier(same.head().state(),current);
        return true;
    }
    record EpisodeEvidence(ContinuityState head,ExactRef origin,CompletedCycleProof proof) { }
    EpisodeEvidence episodeEvidence(ContinuityStorePort.Session same,SessionIdentity owner,ActionReceipt parent,String publication,SemanticEvidence semantic)throws IOException {
        ContinuityState head=same.head().state();CycleState current=state(head,owner);validateChain(current);
        ExactRef origin=current.episodeOrigin().orElseThrow(()->new IOException("actual episode origin is unavailable"));
        ObjectNode body=ContinuityJson.parseObject(archive.loadMaterial(origin).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
        StrictJson.require("xar.java-ordinary-episode-origin/v1".equals(text(body,"schema"))
                &&ExactRef.fromJson(body.get("parent_receipt_ref")).equals(archive.receiptReferenceOf(parent))
                &&text(body,"lifecycle_commit_digest").equals(publication),"actual canonical episode branch differs from the original parent/publication");
        var proof=cycleProof(same,owner,semantic).orElseThrow(()->new IOException("admitted episode still has an unfinished cycle"));
        return new EpisodeEvidence(head,origin,proof);
    }
    void requireHistoricalEpisodeEvidence(ContinuityStorePort.Session same,SessionIdentity owner,ActionReceipt parent,String publication,
            ContinuityState historical,ExactRef origin,CompletedCycleProof proof)throws IOException {
        verifyHistoricalCompletedCycleProof(same,owner,proof,historical);CycleState branch=state(historical,owner);
        StrictJson.require(branch.episodeOrigin().filter(origin::equals).isPresent(),"historical adoption lost its actual episode origin");
        ObjectNode body=ContinuityJson.parseObject(archive.loadMaterial(origin).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
        if(TRANSPORT_ORIGIN_SCHEMA.equals(text(body,"schema"))) {
            StrictJson.require(transportParentMatches(body,parent,publication),"transport historical adoption changed its original parent");return;
        }
        StrictJson.require("xar.java-ordinary-episode-origin/v1".equals(text(body,"schema"))
                &&ExactRef.fromJson(body.get("parent_receipt_ref")).equals(archive.receiptReferenceOf(parent))
                &&text(body,"lifecycle_commit_digest").equals(publication),"historical adoption changed the original parent/publication");
    }
    record HistoricalEpisodeEvidence(ExactRef origin,ObservationIdentity frame,String cycleDigest,
            WriterContracts.HistoricalTransition admission,boolean checkpointRequired,Optional<CheckpointPair> savedFrontier,
            Optional<SameGameTransportContinuity.Evidence> transportEvidence) { }
    /** Real adoption ancestry plus the current validated branch; historical DATA alone cannot mint this evidence. */
    Optional<HistoricalEpisodeEvidence> historicalEpisodeEvidence(ContinuityStorePort.Session same,SessionIdentity owner,
            org.xar.ck3.control.application.lifecycle.LifecycleHistoricalPublication.Recorded recorded)throws IOException {
        return historicalEpisodeEvidence(same,owner,recorded,false);
    }
    Optional<HistoricalEpisodeEvidence> transportedHistoricalEpisodeEvidence(ContinuityStorePort.Session same,SessionIdentity owner,
            org.xar.ck3.control.application.lifecycle.LifecycleHistoricalPublication.Recorded recorded,ExactRef actualTransportOrigin)throws IOException {
        CycleState current=state(same.head().state(),owner);validateChain(current);
        StrictJson.require(current.episodeOrigin().filter(actualTransportOrigin::equals).isPresent(),
                "transported current admission requires the exact actual private current Cycle rebind origin");
        return historicalEpisodeEvidence(same,owner,recorded,true);
    }
    private Optional<HistoricalEpisodeEvidence> historicalEpisodeEvidence(ContinuityStorePort.Session same,SessionIdentity owner,
            org.xar.ck3.control.application.lifecycle.LifecycleHistoricalPublication.Recorded recorded,boolean allowTransport)throws IOException {
        recorded.requireCurrent(same);requireOwner(same.head().state(),owner);requireActive(same.head().state());
        CycleState current=state(same.head().state(),owner);validateChain(current);requireFrontier(same.head().state(),current);
        StrictJson.require(current.pending().isEmpty(),"an unresolved current cycle cannot be cleared by historical adoption");
        requireLegacyPendingClear(same.head().state(),current);
        if(current.episodeOrigin().isEmpty())return Optional.empty();
        ExactRef origin=current.episodeOrigin().orElseThrow();
        ObjectNode body=ContinuityJson.parseObject(archive.loadMaterial(origin).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
        boolean transported=TRANSPORT_ORIGIN_SCHEMA.equals(text(body,"schema"));
        if(transported&&!allowTransport)return Optional.empty();
        if(allowTransport&&!transported)return Optional.empty();
        if(!transported&&!"xar.java-ordinary-episode-origin/v1".equals(text(body,"schema")))return Optional.empty();
        ExactRef parent=archive.receiptReferenceOf(recorded.parent());
        if(transported) {
            if(!transportParentMatches(body,recorded.parent(),recorded.publication().eventIdentity()))return Optional.empty();
        }else {
            if(!ExactRef.fromJson(body.get("parent_receipt_ref")).equals(parent))return Optional.empty();
            StrictJson.require(text(body,"lifecycle_commit_digest").equals(recorded.publication().eventIdentity())
                &&ExactRef.fromJson(body.get("predecessor_driver_ref")).equals(recorded.predecessorDriverReference()),
                "actual admitted origin differs from its original publication or causal predecessor");
        }
        StrictJson.require(ContinuityActionJournal.receipts(same.head().state(),archive).stream().noneMatch(receipt->!receipt.settled()
                &&receipt.command().origin().machineId().equals(owner.machineId())&&receipt.command().origin().game().equals(owner.game())
                &&receipt.command().sessionId().equals(owner.sessionId())),"another actual action remains unresolved in this admitted session");
        WriterContracts.HistoricalTransition admission=null;
        for(var pin:same.head().documents()) {
            if(!java.nio.file.Path.of(pin.reference().path()).getFileName().toString().matches("[0-9]{8}\\.json"))continue;
            var edge=same.readHistoricalTransition(pin);if(!edge.kind().equals(CYCLE_KIND))continue;
            ObjectNode row=ContinuityJson.parseObject(edge.details(),ContinuityJson.DOCUMENT_MAX_BYTES);
            String expectedOperation=transported?"TRANSPORT_REBIND":"EPISODE_REBIND";
            if(!row.has("operation")||!row.get("operation").isTextual()||!expectedOperation.equals(row.get("operation").textValue()))continue;
            if(!ExactRef.fromJson(row.get("previous_state_ref")).equals(origin))continue;
            if(transported) {
                strictTransport(row);var evidence=SameGameTransportContinuity.fromJson((ObjectNode)row.get("transport_evidence"),archive);
                StrictJson.require(sameTransportParent(evidence.canonicalParent().command(),recorded.parent().command()),
                        "canonical transport admission changed the original parent");
            }else {
                strictEpisode(row);
                StrictJson.require(ExactRef.fromJson(row.get("parent_receipt_ref")).equals(parent)
                        &&text(row,"lifecycle_commit_digest").equals(recorded.publication().eventIdentity()),"canonical adoption changed its parent/publication");
            }
            ObjectNode replay=(transported?reduceTransport(edge.before(),row):reduceEpisode(edge.before(),row)).toJson();replay.put("sequence",edge.sequence());replay.put("last_event_identity",edge.eventIdentity());
            StrictJson.require(ContinuityJson.same(replay,edge.after().toJson()),"sole cycle reducer cannot reproduce the canonical adoption event");
            same.requireHistoricalState(edge.sequence(),ContinuityJson.digest(edge.after().toJson()));admission=edge;break;
        }
        if(admission==null)throw new IOException("actual canonical episode adoption event/pin is absent");
        ObservationIdentity frame=current.head().map(this::load).map(value->value.semantic().frame()).orElseGet(()->current.originFrame().orElseThrow());
        ObservationIdentity initial=semanticFromJson(body.get("semantic")).frame();requireSameOwner(initial,frame);
        var saved=savedCycleFrontier(same,owner,current,frame);
        Optional<SameGameTransportContinuity.Evidence> transport=transported
                ?Optional.of(SameGameTransportContinuity.fromJson((ObjectNode)body.get("transport_evidence"),archive)):Optional.empty();
        return Optional.of(new HistoricalEpisodeEvidence(origin,frame,ContinuityJson.digest(current.toJson()),admission,saved.checkpointRequired(),saved.pair(),transport));
    }
    record SavedFrontierEvidence(boolean checkpointRequired,Optional<CheckpointPair> pair) { }
    SavedFrontierEvidence savedFrontierEvidence(ContinuityStorePort.Session same,SessionIdentity owner,CompletedCycleProof proof)throws IOException {
        var actual=cycleProof(same,owner,proof.semantic()).orElseThrow(()->new IOException("current saved frontier has an unfinished cycle"));
        StrictJson.require(actual.equals(proof),"saved-frontier DATA requires the actual current complete cycle proof");
        CycleState current=state(same.head().state(),owner);requireProof(current,proof);
        return savedCycleFrontier(same,owner,current,proof.frame());
    }
    private SavedFrontierEvidence savedCycleFrontier(ContinuityStorePort.Session same,SessionIdentity owner,CycleState current,ObservationIdentity frame) throws IOException {
        Optional<CheckpointPair> savedFrontier=Optional.empty();boolean needsSave=true;ObjectNode whole=same.head().state().toJson();
        if(whole.has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)) {
            ObjectNode saved=StrictJson.object(whole.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),Set.of("pair","state"));
            CycleState savedState=parseState(saved.get("state"));CheckpointPair pair=CheckpointPairCodec.decode(ContinuityJson.canonical(saved.get("pair")));
            if(savedState.session().equals(owner)) {
                validateChain(savedState);savedFrontier=Optional.of(pair);needsSave=!savedState.toJson().equals(current.toJson());
                if(!needsSave){
                    var anchor=current.head().map(this::load).map(value->value.semantic().frame()).orElseGet(()->current.originFrame().orElse(pair.frame()));
                    requireSavedContinuation(anchor,pair.frame()); // READ may advance the public revision after this actual SAVE.
                }
            }else if(hasTransportAncestorOwner(current,savedState.session())) {
                validateChain(savedState);savedFrontier=Optional.of(pair);
                // Preserve the actual old SAVE as DATA. A transport owner change cannot adopt its files or prove a clean current frontier.
            }
        }
        if(!needsSave&&savedFrontier.isPresent()) {
            var receipts=ContinuityActionJournal.receipts(same.head().state(),archive);CheckpointPair canonicalSaved=savedFrontier.orElseThrow();
            var saved=receipts.stream().filter(receipt->receipt.command().actionId().equals(canonicalSaved.saveActionId())).findFirst();
            if(saved.isEmpty()||saved.orElseThrow().outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)needsSave=true;
            else {
                long savedSequence=saved.orElseThrow().sequence();
                needsSave=receipts.stream().anyMatch(receipt->receipt.visibleGameplay()&&receipt.sequence()>savedSequence
                        &&receipt.command().origin().machineId().equals(owner.machineId())&&receipt.command().origin().game().equals(owner.game())
                        &&receipt.command().sessionId().equals(owner.sessionId()));
            }
        }
        return new SavedFrontierEvidence(needsSave,savedFrontier);
    }
    private boolean hasTransportAncestorOwner(CycleState current,SessionIdentity savedOwner) {
        CycleState cursor=current;boolean transport=false;Set<ExactRef> seen=new HashSet<>();
        while(cursor.episodeOrigin().isPresent()) {
            ExactRef reference=cursor.episodeOrigin().orElseThrow();
            StrictJson.require(seen.add(reference)&&seen.size()<=1024,"transport saved-frontier ancestry is cyclic or exceeds its finite bound");
            ObjectNode original=ContinuityJson.parseObject(archive.loadMaterial(reference).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
            transport|=TRANSPORT_ORIGIN_SCHEMA.equals(text(original,"schema"));
            cursor=parseState(original.get("previous_cycle_state"));
            if(transport&&cursor.session().equals(savedOwner))return true;
        }
        return false;
    }
    private String revalidateEpisode(ContinuityStorePort.Session session,WriterContracts.Head head,ObjectNode row) throws IOException {
        strictEpisode(row);EpisodeContext context=episode.get();StrictJson.require(context!=null,"actual private episode input is required");
        var binding=context.binding();context.inputs().requireCurrent(session,binding);
        StrictJson.require(text(row,"predecessor_head_digest").equals(head.digest())&&head.digest().equals(binding.writerHeadDigest())
                &&sessionFromJson(row.get("session")).equals(binding.afterOwner())&&sessionFromJson(row.get("before_session")).equals(binding.beforeOwner())
                &&text(row,"lifecycle_commit_digest").equals(binding.commitDigest())&&semanticFromJson(row.get("semantic")).equals(binding.semantic())
                &&ExactRef.fromJson(row.get("parent_receipt_ref")).equals(archive.receiptReferenceOf(binding.parent())),"episode input or canonical parent changed");
        CycleState before=state(head.state(),binding.beforeOwner());validateChain(before);requireEpisodePredecessor(head.state(),before,binding);ExactRef retained=ExactRef.fromJson(row.get("previous_state_ref"));
        StrictJson.require(archive.loadMaterial(retained).equals(new RawJson(ContinuityJson.canonical(episodeTombstone(head.state(),before,binding))))
                &&episodeState(head.state(),before,binding,retained).toJson().equals(row.get("new_cycle_state")),"episode origin differs from actual retained old branch");
        return ContinuityJson.digest(row);
    }
    private static ContinuityState reduceEpisode(ContinuityState predecessor,ObjectNode row) {
        strictEpisode(row);CycleState before=state(predecessor,sessionFromJson(row.get("before_session"))),next=parseState(row.get("new_cycle_state"));
        StrictJson.require(next.session().equals(sessionFromJson(row.get("session")))&&next.head().isEmpty()&&next.pending().isEmpty()
                &&next.basisCycles()==before.completedCycles()&&next.completedCycles()==before.completedCycles()
                &&next.retainedLegacyPendingDigest().equals(before.retainedLegacyPendingDigest())
                &&next.originFrame().filter(semanticFromJson(row.get("semantic")).frame()::equals).isPresent()
                &&next.episodeOrigin().filter(ExactRef.fromJson(row.get("previous_state_ref"))::equals).isPresent(),"episode rebind must inherit exact confirmed cycles with zero new credit");
        ObjectNode result=predecessor.toJson();result.set(STATE_FIELD,next.toJson());result.set(WriterContracts.ORDINARY_CYCLE_REBIND_FIELD,row.get("previous_state_ref"));
        // The saved frontier and latest_binding stay under actual paired SAVE authority.
        return ContinuityState.fromJson(result,predecessor.machineId());
    }
    private static CycleState episodeState(ContinuityState predecessor,CycleState before,LifecycleEpisodeInputs.Binding binding,ExactRef origin) {
        StrictJson.require(binding.savedDayCredit()==0&&binding.completedCycleCredit()==0
                &&binding.parent().outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                &&(binding.proof() instanceof LifecycleTransitionProof.ContinueSuccessor||binding.proof() instanceof LifecycleTransitionProof.NextEpisode),"private committed episode proof with zero credit required");
        return new CycleState(binding.afterOwner(),before.completedCycles(),before.completedCycles(),Optional.empty(),Optional.empty(),
                before.retainedLegacyPendingDigest(),Optional.of(binding.semantic().frame()),Optional.of(origin));
    }
    private void requireEpisodePredecessor(ContinuityState predecessor,CycleState before,LifecycleEpisodeInputs.Binding binding) {
        requireLegacyPendingClear(predecessor,before);
        StrictJson.require(before.pending().isEmpty(),"an actual retained ordinary cycle cannot be discarded by episode handoff");
        var old=binding.predecessorDriver().session();
        ObjectNode frame=before.head().map(this::load).map(value->originalFrame(value.semantic().frame()))
                .orElseGet(()->before.originFrame().map(OrdinaryCycleTransitions::originalFrame)
                        .orElseGet(()->StrictJson.object(predecessor.toJson().get("latest_binding"),Set.of("date_raw","actor_character_id","episode_run_id","snapshot_id","revision","native_revision"))));
        StrictJson.require(number(frame,"actor_character_id")==old.actorId().longValueExact()
                &&text(frame,"episode_run_id").equals(old.episodeRunId()),"episode predecessor differs from the actually retained old Driver subject and cycle branch");
    }
    private ObjectNode episodeTombstone(ContinuityState predecessor,CycleState before,LifecycleEpisodeInputs.Binding binding) {
        ObjectNode row=StrictJson.object();row.put("schema","xar.java-ordinary-episode-origin/v1");row.set("previous_cycle_state",before.toJson());
        row.set("after_session",sessionToJson(binding.afterOwner()));row.set("semantic",semanticToJson(binding.semantic()));row.put("lifecycle_commit_digest",binding.commitDigest());
        row.set("parent_receipt_ref",archive.receiptReferenceOf(binding.parent()).toJson());
        row.set("predecessor_driver_ref",binding.predecessorDriverReference().toJson());
        ObjectNode source=predecessor.toJson();for(String key:WriterContracts.PRESERVED_RUNTIME_FIELDS){ObjectNode slot=row.putObject(key);slot.put("present",source.has(key));if(source.has(key))slot.set("value",source.get(key));}
        return row;
    }
    /** Consume the actual first SAVE/BASELINE exactly once. This operation never submits SAVE. */
    WriterContracts.Receipt rebindNextBaseline(ContinuityStorePort.Session session,LifecycleEpisodeInputs inputs,
            LifecycleEpisodeInputs.NextBaselineBinding binding) throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(binding);
        StrictJson.require(nextBaseline.get()==null,"one original post-BASELINE input per cycle transaction");
        inputs.requireCurrentBaseline(session,binding);nextBaseline.set(new NextBaselineContext(inputs,binding));
        try {
            var head=session.head();EpisodeWindow.CommittedBaseline baseline=binding.baseline();
            requireUnconsumedBaseline(session,head.state(),baseline);
            ObjectNode origin=nextWindowOrigin(session,head.state(),binding);
            ExactRef retained=archive.preserveMaterial(new RawJson(ContinuityJson.canonical(origin)));
            CycleState next=newWindowState(head.state(),binding.afterOwner(),binding.semantic(),retained);
            ObjectNode row=StrictJson.object();row.put("evidence_id","next-baseline-cycle:"+baseline.eventIdentity());
            row.put("source","java-private-first-save-baseline/v1");row.set("session",sessionToJson(binding.afterOwner()));
            row.set("before_session",sessionToJson(binding.beforeOwner()));row.set("baseline",baseline.toJson());
            row.put("predecessor_head_digest",head.digest());row.set("semantic",semanticToJson(binding.semantic()));
            row.set("previous_state_ref",retained.toJson());row.set("new_cycle_state",next.toJson());
            List<ExactRef> refs=new ArrayList<>(binding.semantic().references());refs.add(retained);refs.add(baseline.eventRef());
            refs.add(baseline.baseline().begin().eventRef());refs.add(baseline.baseline().pairRef());refs.add(baseline.baseline().canonicalSaveReceiptRef());
            return session.commit(session.preview(new WriterContracts.Request(NEXT_BASELINE_KIND,ContinuityJson.canonical(row),refs.stream().distinct().toList())));
        }finally{nextBaseline.remove();}
    }
    private String revalidateNextBaseline(ContinuityStorePort.Session session,WriterContracts.Head head,ObjectNode row) throws IOException {
        strictNextBaseline(row);NextBaselineContext context=nextBaseline.get();
        StrictJson.require(context!=null,"actual private first-SAVE/BASELINE input is required");
        var binding=context.binding();context.inputs().requireCurrentBaseline(session,binding);
        StrictJson.require(text(row,"predecessor_head_digest").equals(head.digest())
                &&sessionFromJson(row.get("session")).equals(binding.afterOwner())
                &&sessionFromJson(row.get("before_session")).equals(binding.beforeOwner())
                &&EpisodeWindow.CommittedBaseline.fromJson(row.get("baseline")).equals(binding.baseline())
                &&semanticFromJson(row.get("semantic")).equals(binding.semantic()),"actual first-SAVE/BASELINE input changed before cycle admission");
        requireUnconsumedBaseline(session,head.state(),binding.baseline());
        ExactRef retained=ExactRef.fromJson(row.get("previous_state_ref"));
        StrictJson.require(archive.loadMaterial(retained).equals(new RawJson(ContinuityJson.canonical(nextWindowOrigin(session,head.state(),binding))))
                &&newWindowState(head.state(),binding.afterOwner(),binding.semantic(),retained).toJson().equals(row.get("new_cycle_state")),
                "next-window origin or new cycle branch differs from the actual original BASELINE");
        return ContinuityJson.digest(row);
    }
    private static ContinuityState reduceNextBaseline(ContinuityState predecessor,ObjectNode row) {
        strictNextBaseline(row);EpisodeWindow.CommittedBaseline committed=EpisodeWindow.CommittedBaseline.fromJson(row.get("baseline"));
        EpisodeWindow.State window=EpisodeWindow.requireActive(predecessor);
        StrictJson.require(window.baseline().filter(committed.baseline()::equals).isPresent()
                &&predecessor.settledCycles()==0&&predecessor.settledDateRaw()==window.begin().after().dateRaw(),
                "new cycle requires this exact real first-SAVE ACTIVE baseline with no completed cycle");
        SessionIdentity owner=sessionFromJson(row.get("session"));SemanticEvidence semantic=semanticFromJson(row.get("semantic"));
        requireWindowSubject(committed,owner,semantic.frame());
        CycleState next=parseState(row.get("new_cycle_state"));ExactRef retained=ExactRef.fromJson(row.get("previous_state_ref"));
        StrictJson.require(next.toJson().equals(newWindowState(predecessor,owner,semantic,retained).toJson()),
                "first-SAVE branch cannot inherit old credits, pending head or a different source");
        ObjectNode result=predecessor.toJson();result.set(STATE_FIELD,next.toJson());
        result.remove(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD);result.set(WriterContracts.ORDINARY_CYCLE_REBIND_FIELD,retained.toJson());
        result.set("latest_binding",originalFrame(semantic.frame()));
        return ContinuityState.fromJson(result,predecessor.machineId());
    }
    private static CycleState newWindowState(ContinuityState predecessor,SessionIdentity owner,SemanticEvidence semantic,ExactRef retained) {
        StrictJson.require(predecessor.settledCycles()==0,"a first BASELINE cannot reuse an already completed cycle");
        return new CycleState(owner,0,0,Optional.empty(),Optional.empty(),Optional.of(legacyPendingDigest(predecessor)),
                Optional.of(semantic.frame()),Optional.of(retained));
    }
    private void requireUnconsumedBaseline(ContinuityStorePort.Session session,ContinuityState current,
            EpisodeWindow.CommittedBaseline committed) throws IOException {
        session.requireEpisodeWindowActive(committed);
        ContinuityState original=session.requireHistoricalState(committed.sequence(),committed.headDigest());
        StrictJson.require(EpisodeWindow.requireActive(original).baseline().filter(committed.baseline()::equals).isPresent()
                &&original.settledCycles()==0&&current.settledCycles()==0,"actual canonical first BASELINE is required");
        ObjectNode expected=original.toJson(),actual=current.toJson();
        for(String field:List.of(STATE_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD)) {
            StrictJson.require(expected.has(field)==actual.has(field)&&(!expected.has(field)||expected.get(field).equals(actual.get(field))),
                    "new-window Cycle was already initialized or its original predecessor branch changed");
        }
    }
    private ObjectNode nextWindowOrigin(ContinuityStorePort.Session session,ContinuityState current,
            LifecycleEpisodeInputs.NextBaselineBinding binding) throws IOException {
        EpisodeWindow.CommittedBaseline baseline=binding.baseline();
        var begin=baseline.baseline().begin();ContinuityState old=session.requireHistoricalState(begin.sequence(),begin.headDigest());
        CycleState before=retainedState(old,binding.beforeOwner());validateChain(before);
        requireWindowSubject(baseline,binding.afterOwner(),binding.semantic().frame());
        CheckpointPair pair=binding.firstCheckpoint().pair();
        StrictJson.require(pair.equals(CheckpointPairCodec.decode(archive.loadMaterial(baseline.baseline().pairRef()).bytes()))
                &&pair.saveActionId().equals(baseline.baseline().saveActionId()),"next cycle changed the one actual physical first SAVE pair");
        requireSavedContinuation(pair.frame(),binding.semantic().frame());
        ObjectNode row=StrictJson.object();row.put("schema",NEXT_ORIGIN_SCHEMA);row.set("baseline",baseline.toJson());
        row.set("before_session",sessionToJson(binding.beforeOwner()));row.set("after_session",sessionToJson(binding.afterOwner()));
        row.set("previous_cycle_state",before.toJson());row.set("semantic",semanticToJson(binding.semantic()));
        row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
        ObjectNode source=current.toJson();for(String field:List.of(STATE_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD)) {
            ObjectNode slot=row.putObject(field);slot.put("present",source.has(field));if(source.has(field))slot.set("value",source.get(field));
        }
        return row;
    }
    private static void requireWindowSubject(EpisodeWindow.CommittedBaseline committed,SessionIdentity owner,ObservationIdentity frame) {
        var actual=committed.baseline().savedIdentity();
        StrictJson.require(actual.machineId().equals(owner.machineId())&&actual.game().equals(owner.game())&&actual.sessionId().equals(owner.sessionId())
                &&frame.machineId().equals(owner.machineId())&&frame.game().equals(owner.game())
                &&frame.frame().episodeRunId().equals(actual.episodeRunId())&&frame.frame().identity().player().longValueExact()==actual.actorId()
                &&frame.frame().identity().dateRaw().longValueExact()==actual.dateRaw(),"new cycle differs from its actual first-SAVE window owner/actor/date");
    }
    private static void strictNextBaseline(ObjectNode row) {
        StrictJson.object(row,Set.of("evidence_id","source","session","before_session","baseline","predecessor_head_digest","semantic","previous_state_ref","new_cycle_state"));
        WriterContracts.requireDigest(text(row,"predecessor_head_digest"));
        StrictJson.require(text(row,"source").equals("java-private-first-save-baseline/v1"),"exact first-SAVE cycle source required");
    }
    private String revalidateRebind(ContinuityStorePort.Session session,WriterContracts.Head head,ObjectNode details,String identity)throws IOException {
        strictRebind(details);
        var committed=committedImportedRebinding.get();
        if(committed!=null)return revalidateCommittedImportedRebind(session,head,details,identity,committed);
        RestoreBinding binding = restoring.get();
        StrictJson.require(binding != null && binding.session().equals(sessionFromJson(details.get("session")))
                && text(details, "attachment_identity").equals(binding.attachment().eventIdentity())
                && text(details, "attachment_head_digest").equals(ContinuityJson.digest(binding.attachment().head().toJson()))
                && CheckpointPairCodec.decode(ContinuityJson.canonical(details.get("restore_pair"))).equals(binding.pair())
                && semanticFromJson(details.get("semantic")).equals(binding.semantic()), "private actual restore admission/source/head changed before cycle rebind");
        var imported = importedRestoreSources(binding);
        StrictJson.require(text(details, "source").equals(imported.isPresent() ? IMPORTED_RESTORE_SOURCE : RESTORE_SOURCE),
                "cycle rebind changed its actual restore source version");
        session.requireDomainImportContinuation(binding.attachment().head().sequence(),ContinuityJson.digest(binding.attachment().head().toJson()));
        StrictJson.require(restoredState(head.state(), binding, imported).toJson().equals(details.get("new_cycle_state")), "cycle rebind changed surviving saved branch or granted cycles");
        RawJson retained = archive.loadMaterial(ExactRef.fromJson(details.get("previous_state_ref")));
        StrictJson.require(retained.equals(new RawJson(ContinuityJson.canonical(restoreTombstone(head.state(),binding.attachment().eventIdentity(),
                binding.session(),binding.pair(),imported.isPresent())))), "old cycle/pending tombstone is not the actual immutable archived predecessor");
        VerifiedSemantic verified = verify(session, binding.session(), binding.semantic());
        ObjectNode proof = StrictJson.object(); proof.put("head", head.digest()); proof.put("attachment", binding.attachment().eventIdentity()); proof.put("semantic", verified.materialDigest()); return ContinuityJson.digest(proof);
    }
    private String revalidateCommittedImportedRebind(ContinuityStorePort.Session same,WriterContracts.Head head,ObjectNode details,
            String identity,CommittedImportedRebind committing)throws IOException {
        var original=committing.attachment();
        requireCommittedRebindPredecessor(head,original,committing.predecessorDigest());
        var authority=committedImportedRebindAuthority;
        if(authority==null||!committing.requestIdentity().equals(identity))
            throw new IOException("Committed imported REBIND differs from its actual private writer preparation");
        same.verifyPin(committing.seedPin());
        authority.requireCurrent(same,original,committing.fresh());
        requireCommittedRebindPredecessor(same.head(),original,committing.predecessorDigest());
        var retained=archive.loadMaterial(ExactRef.fromJson(details.get("previous_state_ref")));
        if(!retained.equals(committing.tombstone()))throw new IOException("Committed imported REBIND changed the original cycle and pending tombstone");
        var proof=StrictJson.object().put("head",head.digest()).put("attachment",original.attachment().eventIdentity())
                .put("semantic",committing.verified().materialDigest());
        return ContinuityJson.digest(proof);
    }
    /** Replays already recorded imported REBIND data without the live restore authority. */
    static ContinuityState replayImportedRebind(ContinuityState predecessor, ObjectNode details, byte[] retainedTombstone) {
        strictRebind(details);
        var owner = sessionFromJson(details.get("session"));
        requireOwner(predecessor, owner);
        StrictJson.require("REBIND".equals(text(details, "operation")) && IMPORTED_RESTORE_SOURCE.equals(text(details, "source")),
                "exact imported REBIND source required");
        var pair = CheckpointPairCodec.decode(ContinuityJson.canonical(details.get("restore_pair")));
        var tombstone = restoreTombstone(predecessor, text(details, "attachment_identity"), owner, pair, true);
        StrictJson.require(java.util.Arrays.equals(ContinuityJson.canonical(tombstone), retainedTombstone),
                "committed imported REBIND tombstone differs from its exact predecessor");
        return reduceRebind(predecessor, details);
    }

    private static ContinuityState reduceRebind(ContinuityState predecessor, ObjectNode details) {
        strictRebind(details); CycleState restored = parseState(details.get("new_cycle_state"));
        StrictJson.require(restored.session().equals(sessionFromJson(details.get("session"))) && restored.head().isEmpty() && restored.pending().isEmpty()
                && restored.basisCycles() == predecessor.settledCycles() && restored.completedCycles() == predecessor.settledCycles()
                && restored.retainedLegacyPendingDigest().filter(legacyPendingDigest(predecessor)::equals).isPresent(), "restore cycle rebind must preserve saved frontier and exact original pending tombstones");
        boolean imported = text(details, "source").equals(IMPORTED_RESTORE_SOURCE);
        if (imported) {
            var pair = CheckpointPairCodec.decode(ContinuityJson.canonical(details.get("restore_pair")));
            var semantic = semanticFromJson(details.get("semantic"));
            requireImportedCyclePredecessor(predecessor, restored.session(), pair, semantic);
            StrictJson.require(restored.originFrame().filter(semantic.frame()::equals).isPresent() && restored.episodeOrigin().isEmpty(),
                    "imported cycle rebind must start from the exact restored observation");
        }
        ObjectNode next = predecessor.toJson(); next.set(STATE_FIELD, restored.toJson()); next.set(WriterContracts.ORDINARY_CYCLE_REBIND_FIELD, details.get("previous_state_ref"));
        if (imported) {
            next.set(WriterContracts.ORDINARY_IMPORTED_CYCLE_ORIGIN_FIELD, details.get("previous_state_ref"));
        }
        // Only the private admitted final SEM has the public Driver revision absent from raw restore opening.
        next.set("latest_binding", originalFrame(semanticFromJson(details.get("semantic")).frame()));
        return ContinuityState.fromJson(next, predecessor.machineId());
    }
    private CycleState restoredState(ContinuityState predecessor, RestoreBinding binding,
            Optional<SavedAttachmentSourceStore.Sources> imported) {
        StrictJson.require(binding.newSavedDayCredit() == 0 && binding.session().machineId().equals(predecessor.machineId())
                && binding.attachment().head().settledCycles() == predecessor.settledCycles()
                && binding.attachment().head().settledDateRaw() == predecessor.settledDateRaw(), "actual restore cannot grant day/cycle credit");
        ObjectNode whole = predecessor.toJson();
        if (imported.isPresent()) {
            var actual = requireImportedCyclePredecessor(predecessor, binding.session(), binding.pair(), binding.semantic());
            StrictJson.require(imported.orElseThrow().equals(actual), "imported cycle rebind changed its actual attachment sources");
            validateChain(parseState(whole.get(STATE_FIELD)));
        } else if (whole.has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)) {
            ObjectNode saved = StrictJson.object(whole.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD), Set.of("pair", "state"));
            StrictJson.require(CheckpointPairCodec.decode(ContinuityJson.canonical(saved.get("pair"))).equals(binding.pair()), "surviving Java cycle branch belongs to a different physical SAVE");
            CycleState survived = parseState(saved.get("state"));
            StrictJson.require(survived.pending().isEmpty() && survived.completedCycles() == predecessor.settledCycles(), "saved cycle branch/counter is not the restored frontier");
            requireFrontier(predecessor, survived); validateChain(survived);
        } else StrictJson.require(!whole.has(STATE_FIELD), "a Java cycle branch without its exact saved cycle snapshot cannot be guessed during restore");
        return restoredCycle(predecessor,binding.session(),binding.semantic());
    }
    private static CycleState restoredCycle(ContinuityState predecessor,SessionIdentity owner,SemanticEvidence semantic) {
        return new CycleState(owner,predecessor.settledCycles(),predecessor.settledCycles(),Optional.empty(),Optional.empty(),
                Optional.of(legacyPendingDigest(predecessor)),Optional.of(semantic.frame()),Optional.empty());
    }
    private Optional<SavedAttachmentSourceStore.Sources> importedRestoreSources(RestoreBinding binding) {
        if (!(binding.savedMaterial() instanceof SavedAttachmentSourceStore.SavedMaterial material) || material.importedOrigin().isEmpty()) {
            return Optional.empty();
        }
        var original = binding.originalAttachment();
        var sources = SavedAttachmentSourceStore.Sources.decode(original.request().detailsObject().get(SavedAttachmentSourceStore.SOURCES_DETAIL));
        var owner = material.importedOrigin().orElseThrow().owner();
        StrictJson.require(sources.importedOrigin().equals(material.importedOrigin()) && sources.material().equals(material.witness())
                        && sources.physicalSaveWitness().filter(binding.pair().save()::equals).isPresent()
                        && ContinuityBatchJournal.importedSavedInterruptedFrontier(original.predecessor().state(), owner),
                "imported cycle rebind needs the actual interrupted target and original v5 physical SAVE witness");
        requireImportedRestoreRetirement(original.predecessor().state(),owner,binding.pair());
        return Optional.of(sources);
    }
    private void requireImportedRestoreRetirement(ContinuityState previous,SessionIdentity owner,CheckpointPair pair) {
        var record = archive.loadRecord(ContinuityActionJournal.recordHead(previous).orElseThrow());
        var terminal = record.receipt();
        StrictJson.require(terminal.sequence() == previous.sequence()
                        && terminal.state() instanceof ActionState.CompositeOperatorQuarantined
                        && terminal.command().origin().game().equals(owner.game()) && terminal.command().sessionId().equals(owner.sessionId()),
                "imported cycle rebind requires the actual exited target operator terminal");
        var observation = CompositeOperatorQuarantineObservation.load(terminal, archive);
        var request = CompositeOperatorQuarantineRequest.decode(archive.loadMaterial(observation.requestMaterial()).bytes());
        StrictJson.require(request.exitedLife().filter(exit -> exit.ownerSessionId().equals(owner.sessionId())
                                && exit.savedPairSha256().equals(ActionCodec.sha256(CheckpointPairCodec.encode(pair)))).isPresent()
                        && request.parentActionId().equals(terminal.command().actionId())
                        && record.previous().filter(observation.originalActionHead()::equals).isPresent()
                        && Math.addExact(request.expectedHeadSequence(), 1) == terminal.sequence(),
                "imported cycle rebind changed its actual exited target decision");
    }
    private static SavedAttachmentSourceStore.Sources requireImportedCyclePredecessor(ContinuityState predecessor,
            SessionIdentity restored, CheckpointPair pair, SemanticEvidence semantic) {
        var whole = predecessor.toJson();
        var attachment = ContinuityJson.object(whole.get("last_current_saved_cold"));
        var sources = SavedAttachmentSourceStore.Sources.decode(attachment.get(SavedAttachmentSourceStore.SOURCES_DETAIL));
        var imported = sources.importedOrigin().orElseThrow();
        var previous = parseState(whole.get(STATE_FIELD));
        var loaded = ContinuityJson.object(whole.get("latest_binding"));
        var frame = semantic.frame();
        StrictJson.require(!whole.has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)
                        && !whole.has(WriterContracts.ORDINARY_IMPORTED_CYCLE_ORIGIN_FIELD)
                        && sources.physicalSaveWitness().filter(pair.save()::equals).isPresent()
                        && pair.equals(CheckpointPairCodec.decode(ContinuityJson.canonical(attachment.get(SavedAttachmentAuthority.PAIR_DETAIL))))
                        && previous.session().equals(imported.owner()) && previous.basisCycles() == predecessor.settledCycles()
                        && previous.completedCycles() > predecessor.settledCycles() && previous.pending().isEmpty() && previous.head().isPresent()
                        && !restored.equals(imported.owner()) && !restored.game().equals(imported.owner().game())
                        && !restored.game().equals(pair.frame().game()) && frame.game().equals(restored.game())
                        && restored.machineId().equals(frame.machineId()) && restored.machineId().equals(imported.owner().machineId())
                        && ContinuityJson.same(whole.get("game_binding"), restored.game().toJson())
                        && restored.sessionId().equals(StrictJson.text(loaded.get("session_id")))
                        && frame.frame().episodeRunId().equals(pair.frame().frame().episodeRunId())
                        && frame.frame().identity().player().equals(pair.frame().frame().identity().player())
                        && frame.frame().identity().dateRaw().equals(pair.frame().frame().identity().dateRaw())
                        && frame.frame().identity().dateRaw().longValueExact() == predecessor.settledDateRaw(),
                "imported cycle rebind must preserve the physical SAVE frontier and the exact old target cycle");
        return sources;
    }
    private static ObjectNode restoreTombstone(ContinuityState predecessor,String attachmentIdentity,
            SessionIdentity owner,CheckpointPair pair,boolean imported) {
        ObjectNode before = predecessor.toJson(); ObjectNode row = StrictJson.object();
        row.put("schema", imported ? "xar.java-ordinary-cycle-restore-tombstone/v2" : "xar.java-ordinary-cycle-restore-tombstone/v1");
        row.put("attachment_identity", attachmentIdentity); row.set("restored_session", sessionToJson(owner));
        row.set("restore_pair", StrictJson.parse(CheckpointPairCodec.encode(pair))); row.put("retained_legacy_pending_digest", legacyPendingDigest(predecessor));
        for (String key : List.of(STATE_FIELD, WriterContracts.ORDINARY_SAVED_CYCLE_FIELD, WriterContracts.ORDINARY_CYCLE_REBIND_FIELD)) {
            ObjectNode slot = row.putObject(key); slot.put("present", before.has(key)); if (before.has(key)) slot.set("value", before.get(key));
        }
        if (imported) {
            row.set("original_action_head", ContinuityActionJournal.recordHead(predecessor).orElseThrow().toJson());
        }
        return row;
    }
    private WriterContracts.Request cycleRequest(SessionIdentity owner, String operation, ExactRef receipt,
            Optional<SemanticEvidence> semantic, Optional<ExactRef> recordRef, Optional<CycleRecord> record) {
        ObjectNode details = StrictJson.object(); details.put("evidence_id", operation + ":" + receipt.sha256()
                + semantic.map(value -> ":" + value.semantic().sha256()).orElse("")); details.put("source", "java-ordinary-auto-sem/v1");
        details.set("session", sessionToJson(owner)); details.put("operation", operation); details.set("receipt_ref", receipt.toJson());
        if (semantic.isPresent()) details.set("semantic", semanticToJson(semantic.orElseThrow())); else details.putNull("semantic");
        if (recordRef.isPresent()) details.set("cycle_record_ref", recordRef.orElseThrow().toJson()); else details.putNull("cycle_record_ref");
        if (record.isPresent()) details.set("cycle_record", record.orElseThrow().toJson()); else details.putNull("cycle_record");
        List<ExactRef> refs = new ArrayList<>(List.of(receipt)); semantic.ifPresent(value -> refs.addAll(value.references()));
        recordRef.ifPresent(refs::add); record.flatMap(CycleRecord::previous).ifPresent(refs::add);
        return new WriterContracts.Request(CYCLE_KIND, ContinuityJson.canonical(details), refs.stream().distinct().toList());
    }
    private VerifiedSemantic verify(ContinuityStorePort.Session session, SessionIdentity owner, SemanticEvidence semantic) throws IOException {
        VerifiedSemantic verified = semanticVerifier.verify(session, owner, semantic);
        StrictJson.require(verified.frame().equals(semantic.frame()) && verified.observedAt().equals(semantic.observedAt()), "verified archived SEM differs from the requested exact frame/time");
        StrictJson.require(owner.machineId().equals(verified.frame().machineId()) && owner.game().equals(verified.frame().game()), "SEM changed owned Game or machine"); return verified;
    }
    private ActionReceipt canonicalReceipt(ContinuityState head, ExactRef ref, SessionIdentity owner) {
        ActionReceipt receipt = archive.loadReceipt(ref);
        StrictJson.require(receipt.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay,"ordinary cycle accepts an actual gameplay origin only");
        StrictJson.require(archive.receiptReferenceOf(receipt).equals(ref)
                && ContinuityActionJournal.lookup(head, receipt.command().actionId(), archive).filter(receipt::equals).isPresent(), "AUTO receipt is not reachable from the actual canonical action head");
        StrictJson.require(receipt.command().sessionId().equals(owner.sessionId()) && receipt.command().before().machineId().equals(owner.machineId())
                && receipt.command().before().game().equals(owner.game()) && receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED,
                "only the owned independently confirmed AUTO receipt can complete a cycle");
        if (head.status() == ContinuityState.Status.REPAIR_REQUIRED) requireReconciledOriginalRepair(head,receipt,owner);
        else requireActive(head);
        classify(receipt); return receipt;
    }
    /** Only the current original UNKNOWN, now canonically confirmed, may enter RETAIN/SETTLE while repair is retained. */
    private void requireReconciledOriginalRepair(ContinuityState head,ActionReceipt receipt,SessionIdentity owner) {
        ObjectNode whole=head.toJson();
        ObjectNode boundary=StrictJson.object(whole.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD),
                Set.of("evidence_id","session","batch_id","boundary"));
        ObjectNode interruption=StrictJson.object(whole.get("interruption"),
                Set.of("reason","source","evidence_id","last_settled_frame","completed_cycles"));
        StrictJson.require(head.status()==ContinuityState.Status.REPAIR_REQUIRED
                &&text(boundary,"boundary").equals(JournalKind.BATCH_INTERRUPTED.name())
                &&sessionFromJson(boundary.get("session")).equals(owner)
                &&text(interruption,"source").equals("java-ordinary-batch-interruption/v2")
                &&text(interruption,"evidence_id").equals(text(boundary,"evidence_id"))
                &&number(whole,"interrupted_window_id")==head.origin().windowId()
                &&number(interruption,"completed_cycles")==head.settledCycles()
                &&!hasUnresolvedOtherAction(head,receipt),
                "only this ordinary interrupted batch with resolved originals may recover a cycle");
        if(requirePublishedAppliedLifeRepair(head,receipt,owner))return;
        Optional<ExactRef> cursor=ContinuityActionJournal.recordHead(head);
        Set<ExactRef> seen=new HashSet<>();long maximum=head.sequence();boolean originalUnknown=false;
        while(cursor.isPresent()) {
            ExactRef ref=cursor.orElseThrow();
            StrictJson.require(seen.add(ref)&&seen.size()<=MAX_RECORDS,"reconciled original history is cyclic or exceeds its bound");
            var record=archive.loadRecord(ref);var prior=record.receipt();
            StrictJson.require(prior.sequence()<=maximum,"reconciled original action history moved backwards");
            maximum=prior.sequence()-1;
            if(prior.command().actionId().equals(receipt.command().actionId())) {
                StrictJson.require(prior.command().equals(receipt.command())&&prior.bodySha256().equals(receipt.bodySha256()),
                        "reconciliation changed the original action body");
                if(prior.sequence()<receipt.sequence()&&(prior.state() instanceof ActionState.Unknown
                        ||prior.state() instanceof ActionState.CompositeUnknown)) {originalUnknown=true;break;}
            }
            cursor=record.previous();
        }
        StrictJson.require(originalUnknown,"repair recovery requires this same canonical original UNKNOWN before its confirmed reconciliation");
    }
    /** Pre-RETAIN unretained Life and post-RETAIN exact pending Life are distinct real states, neither invents UNKNOWN. */
    private boolean requirePublishedAppliedLifeRepair(ContinuityState head,ActionReceipt receipt,SessionIdentity owner) {
        var same=active.get();StrictJson.require(same!=null,"Life repair material consumption requires the actual locked writer");
        var originals=archive.withSession(same);var actions=ContinuityActionJournal.receipts(head,originals);
        var actual=ContinuityBatchJournal.readOnlyUnretainedAppliedLifeRoot(head,owner,actions,originals)
                .or(()->ContinuityBatchJournal.readOnlyPendingCompletedLifeCycle(head,owner,actions,originals));
        if(actual.filter(receipt::equals).isEmpty())return false;
        var publication=org.xar.ck3.control.application.driver.DriverActionHistoryState.decode(
                ContinuityJson.object(head.toJson().get(WriterContracts.DRIVER_ACTION_HISTORY_FIELD)),receipt);
        StrictJson.require(publication.command().equals(receipt.command())&&publication.bodySha256().equals(receipt.bodySha256())
                &&publication.actionSequence()==receipt.sequence(),"repair Life RETAIN/SETTLE must consume its actual already published same-source material");
        try {
            sessionAuthority.require(same);var locked=same.head();String expected=ContinuityJson.digest(head.toJson());
            if(locked.state().sequence()==head.sequence())StrictJson.require(locked.digest().equals(expected),"Life repair changed its actual current predecessor");
            else {
                StrictJson.require(head.sequence()<locked.state().sequence(),"Life repair cannot consume a future predecessor");
                var historical=same.requireHistoricalCanonicalState(head.sequence(),expected);
                StrictJson.require(ContinuityJson.same(historical.toJson(),head.toJson()),"Life repair historical predecessor is not its exact original canonical state");
            }
            org.xar.ck3.control.application.driver.DriverActionHistoryState.requireOriginals(same,List.of(publication),List.of(receipt),originals);
            StrictJson.require(same.head().digest().equals(locked.digest()),"published Life repair material changed the actual locked writer head");
        }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
        return true;
    }
    private boolean hasUnresolvedOtherAction(ContinuityState head, ActionReceipt receipt) {
        return ContinuityActionJournal.receipts(head, archive).stream().anyMatch(item -> !item.settled()
                && item.command().sessionId().equals(receipt.command().sessionId()) && item.command().origin().game().equals(receipt.command().origin().game())
                && !item.command().actionId().equals(receipt.command().actionId()));
    }
    private enum Classification { CONTROL_ONLY, VISIBLE_GAMEPLAY, ELIGIBLE_ADVANCE }
    private Classification classify(ActionReceipt receipt) {
        terminal(receipt);
        if (receipt.eligibleAdvance()) return Classification.ELIGIBLE_ADVANCE;
        return receipt.visibleGameplay() ? Classification.VISIBLE_GAMEPLAY : Classification.CONTROL_ONLY;
    }
    private record Terminal(ObservationIdentity frame, Instant observedAt) { }
    private Terminal terminal(ActionReceipt receipt) {
        var semantic = ActionEffects.observation(receipt);
        if (semantic.isPresent()) return new Terminal(semantic.orElseThrow().after(), semantic.orElseThrow().observedAt());
        if (receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied control)
            return new Terminal(control.read().after().binding().observed(), control.read().after().binding().observedAt());
        if (receipt.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.SwaySchedulerCompleted scheduler) {
            var proof = scheduler.proof(); proof.validateParent(receipt.command());
            NativeEffectEvidence.FrameLoader actualLoader = terminalFrames;
            StrictJson.require(actualLoader != null, "Sway cycle completion requires the actual Root terminal frame loader");
            var actual = actualLoader.load(proof.finalFrame(), archive);
            StrictJson.require(actual.sessionId().equals(receipt.command().sessionId())
                    && actual.source().equals(receipt.command().source())
                    && actual.originalEvidence().equals(proof.finalFrame().nativeFrame()),
                    "Sway cycle terminal frame differs from its actual parent source/session and original native packet");
            requireSameOwner(receipt.command().before(), actual.identity());
            return new Terminal(actual.identity(), actual.observedAt());
        }
        throw new IllegalArgumentException("an ACK, frontend transition or unsupported settlement is not an ordinary completed AUTO");
    }
    private void freshAfter(ActionReceipt receipt, VerifiedSemantic semantic) {
        freshAfter(receipt, semantic.frame(), semantic.observedAt());
    }
    private void freshAfter(ActionReceipt receipt, ObservationIdentity frame, Instant observedAt) {
        freshAfter(receipt, terminal(receipt), frame, observedAt);
    }
    private static void freshAfter(ActionReceipt receipt, Terminal terminal, ObservationIdentity frame, Instant observedAt) {
        requireSameOwner(receipt.command().before(), frame);
        requireSameOwner(terminal.frame(), frame);
        StrictJson.require(observedAt.isAfter(terminal.observedAt()), "the cycle SEM must be collected after the actual terminal observation");
        StrictJson.require(frame.frame().identity().nativeRevision().compareTo(terminal.frame().frame().identity().nativeRevision()) >= 0
                && frame.frame().identity().dateRaw().compareTo(terminal.frame().frame().identity().dateRaw()) >= 0,
                "fresh SEM regressed native revision or game date");
        // A zero-day modal/control observation may retain nativeRevision; it receives no gameplay/day credit.
        if (!receipt.visibleGameplay()) StrictJson.require(!receipt.eligibleAdvance(), "control-only cycle cannot claim an eligible advance");
    }
    private void requireRecord(CycleState state, ExactRef receiptRef, ActionReceipt receipt, SemanticEvidence semantic, CycleRecord record) {
        StrictJson.require(state.pending().filter(receiptRef::equals).isPresent() && record.receipt().equals(receiptRef)
                && record.previous().equals(state.head()) && record.session().equals(state.session()) && record.semantic().equals(semantic)
                && record.classification() == classify(receipt), "cycle record changed its exact pending AUTO, source, SEM or classification");
        StrictJson.require(record.completedCycles() == Math.addExact(state.completedCycles(), record.classification() == Classification.CONTROL_ONLY ? 0 : 1), "cycle counter differs from actual receipt classification");
    }
    private static void requireProof(CycleState state, CompletedCycleProof proof) {
        StrictJson.require(state.pending().isEmpty() && proof.completedCycles() == state.completedCycles()
                && proof.cycleStateDigest().equals(ContinuityJson.digest(state.toJson())), "SAVE proof differs from the actual settled cycle state");
    }
    private boolean matchesCycleRecordReceipt(CycleRecord record, ActionReceipt receipt, SessionIdentity owner) {
        return receipt.command().origin() instanceof CommandOrigin.Gameplay
                && archive.receiptReferenceOf(receipt).equals(record.receipt())
                && receipt.command().sessionId().equals(owner.sessionId())
                && receipt.command().before().machineId().equals(owner.machineId())
                && receipt.command().before().game().equals(owner.game())
                && receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED && classify(receipt) == record.classification();
    }
    private Optional<CycleRecord> find(CycleState state, ExactRef receipt) {
        return walk(state, Optional.of(Objects.requireNonNull(receipt)));
    }
    private void validateChain(CycleState state) { walk(state, Optional.empty()); }
    /** Validate the entire immutable branch even when the requested receipt was found at its head. */
    private Optional<CycleRecord> walk(CycleState state, Optional<ExactRef> wanted) {
        return walk(state,wanted,new HashSet<>(),new HashSet<>());
    }
    private Set<ExactRef> validatedBranchReceipts(CycleState state) {
        Set<ExactRef> receipts = new HashSet<>();
        walk(state, Optional.empty(), new HashSet<>(), new HashSet<>(), receipts);
        return Set.copyOf(receipts);
    }
    private Optional<CycleRecord> walk(CycleState state,Optional<ExactRef> wanted,Set<ExactRef> origins,Set<ExactRef> allRecords) {
        return walk(state, wanted, origins, allRecords, null);
    }
    private Optional<CycleRecord> walk(CycleState state,Optional<ExactRef> wanted,Set<ExactRef> origins,Set<ExactRef> allRecords,
            Set<ExactRef> branchReceipts) {
        Optional<ExactRef> cursor = state.head(); Set<ExactRef> seen = new HashSet<>(); Set<String> actionIds = new HashSet<>();
        Optional<CycleRecord> found = Optional.empty(); long expected = state.completedCycles();
        while (cursor.isPresent()) {
            var ref = cursor.orElseThrow(); StrictJson.require(seen.add(ref) && seen.size() <= MAX_RECORDS, "cycle archive chain is cyclic or exceeds its finite read budget");
            StrictJson.require(allRecords.add(ref)&&allRecords.size()<=MAX_RECORDS,"combined episode cycle archive repeats or exceeds its finite read budget");
            var record = load(ref); StrictJson.require(record.session().equals(state.session()) && record.completedCycles() == expected,
                    "cycle record source/counter differs from the exact branch head or predecessor");
            ActionReceipt receipt = archive.loadReceipt(record.receipt());
            StrictJson.require(matchesCycleRecordReceipt(record, receipt, state.session()),
                    "cycle record differs from its original owned canonical AUTO classification");
            StrictJson.require(actionIds.add(receipt.command().actionId()), "the same canonical AUTO receipt occurs twice in the cycle branch");
            freshAfter(receipt, record.semantic().frame(), record.semantic().observedAt());
            if (wanted.filter(record.receipt()::equals).isPresent()) found = Optional.of(record);
            expected = Math.subtractExact(expected, record.classification() == Classification.CONTROL_ONLY ? 0 : 1);
            StrictJson.require(expected >= state.basisCycles(), "cycle record grants credit below its retained branch basis");
            cursor = record.previous();
            if (branchReceipts != null) branchReceipts.add(record.receipt());
        }
        StrictJson.require(expected == state.basisCycles(), "cycle record chain does not terminate at its exact retained basis");
        if(state.episodeOrigin().isPresent()) {
            ExactRef ref=state.episodeOrigin().orElseThrow();StrictJson.require(origins.add(ref)&&origins.size()<=1024,"episode origin chain is cyclic or exceeds its finite bound");
            ObjectNode origin=ContinuityJson.parseObject(archive.loadMaterial(ref).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
            if (ExternalSaveOrigin.SCHEMA.equals(text(origin, "schema"))) {
                var external = ExternalSaveOrigin.fromJson(origin);
                var same = active.get();
                StrictJson.require(same != null && external.successor().equals(state.session()),
                        "external save cycle history needs its current owner and original writer");
                external.requireSemantic(state.originFrame().orElseThrow());
                try {
                    var previous = state(external.requireOriginal(same), external.departed());
                    StrictJson.require(previous.completedCycles() == state.basisCycles(),
                            "external save cycle origin changed the original completed cycle count");
                    walk(previous, Optional.empty(), origins, allRecords);
                    return found;
                } catch (IOException failure) {
                    throw new java.io.UncheckedIOException(failure);
                }
            }
            StrictJson.require(sessionFromJson(origin.get("after_session")).equals(state.session())
                    &&state.originFrame().filter(semanticFromJson(origin.get("semantic")).frame()::equals).isPresent(),"episode/window origin source differs");
            CycleState before=parseState(origin.get("previous_cycle_state"));
            if(TRANSPORT_ORIGIN_SCHEMA.equals(text(origin,"schema")))requireRecordedTransportOrigin(origin,state,before);
            else if(OPERATOR_ORIGIN_SCHEMA.equals(text(origin,"schema")))requireRecordedOperatorOrigin(origin,state,before);
            else if(NEXT_ORIGIN_SCHEMA.equals(text(origin,"schema")))requireRecordedNextWindowOrigin(origin,state,before);
            else {
                StrictJson.require(text(origin,"schema").equals("xar.java-ordinary-episode-origin/v1"),"known exact cycle origin version required");
                requireRecordedEpisodeOrigin(origin,state);
                StrictJson.require(before.completedCycles()==state.basisCycles(),"episode origin changed inherited confirmed cycle count");
            }
            walk(before,Optional.empty(),origins,allRecords);
        }
        return found;
    }
    /** Historical proof of a new window preserves its old branch without inheriting its cycle count. */
    private void requireRecordedNextWindowOrigin(ObjectNode row,CycleState branch,CycleState before) {
        StrictJson.object(row,Set.of("schema","baseline","before_session","after_session","previous_cycle_state","semantic","pair",
                STATE_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD));
        EpisodeWindow.CommittedBaseline baseline=EpisodeWindow.CommittedBaseline.fromJson(row.get("baseline"));
        SessionIdentity previous=sessionFromJson(row.get("before_session"));
        StrictJson.require(branch.basisCycles()==0&&before.session().equals(previous),"new window cannot carry old cycle credit or change its predecessor");
        requireWindowSubject(baseline,branch.session(),branch.originFrame().orElseThrow());
        CheckpointPair pair=CheckpointPairCodec.decode(ContinuityJson.canonical(row.get("pair")));
        StrictJson.require(pair.saveActionId().equals(baseline.baseline().saveActionId())
                &&pair.equals(CheckpointPairCodec.decode(archive.loadMaterial(baseline.baseline().pairRef()).bytes())),"retained first SAVE pair changed");
        requireSavedContinuation(pair.frame(),branch.originFrame().orElseThrow());
        var session=active.get();StrictJson.require(session!=null,"new-window history requires the actual original writer Session");
        try {
            session.requireHistoricalEpisodeWindowBaseline(baseline);
            ContinuityState historical=session.requireHistoricalState(baseline.sequence(),baseline.headDigest());
            StrictJson.require(EpisodeWindow.requireActive(historical).baseline().filter(baseline.baseline()::equals).isPresent()
                    &&historical.settledCycles()==0,"retained new-window origin has no actual canonical first BASELINE");
            var begin=baseline.baseline().begin();ContinuityState old=session.requireHistoricalState(begin.sequence(),begin.headDigest());
            StrictJson.require(retainedState(old,previous).toJson().equals(before.toJson()),"retained previous cycle differs from the actual original BEGIN head");
            ObjectNode actual=historical.toJson();
            for(String field:List.of(STATE_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD)) {
                ObjectNode slot=StrictJson.object(row.get(field),actual.has(field)?Set.of("present","value"):Set.of("present"));
                StrictJson.require(slot.get("present").isBoolean()&&slot.get("present").booleanValue()==actual.has(field)
                        &&(!actual.has(field)||actual.get(field).equals(slot.get("value"))),"retained old Cycle field differs from canonical BASELINE");
            }
        }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
    /** Historical verification retains recorded facts only; it cannot mint a new live episode admission. */
    private void requireRecordedEpisodeOrigin(ObjectNode origin,CycleState state) {
        String committed=text(origin,"lifecycle_commit_digest");WriterContracts.requireDigest(committed);
        ExactRef ref=ExactRef.fromJson(origin.get("parent_receipt_ref"));ActionReceipt parent=archive.loadReceipt(ref);
        StrictJson.require(archive.receiptReferenceOf(parent).equals(ref)&&parent.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,"episode origin lost its original confirmed parent receipt");
        ActionState.Settlement settled=parent.state() instanceof ActionState.CompositeSettled value?value.settlement()
                :parent.state() instanceof ActionState.Settled value?value.settlement():null;
        StrictJson.require(settled instanceof ActionState.LifecycleApplied,"episode origin parent is not a recorded lifecycle outcome");
        LifecycleTransitionProof proof=((ActionState.LifecycleApplied)settled).proof();proof.validateParent(parent.command());
        StrictJson.require(proof.kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR||proof.kind()==LifecycleTransitionProof.Kind.NEXT_EPISODE,"episode origin has no supported episode branch");
        JsonNode encoded=LifecycleProofMaterialJson.proof(proof.encode());
        StrictJson.require(committed.equals(StrictJson.text(encoded.get("committed_event_identity"))),"episode origin changed its actual lifecycle commit");
        JsonNode result=LifecycleProofMaterialJson.result(proof.encodedResult());
        var after=state.originFrame().orElseThrow();var old=DriverStateSnapshot.decodeComplete(archive.loadFullMaterial(ExactRef.fromJson(origin.get("predecessor_driver_ref"))).bytes()).session();
        StrictJson.require(StrictJson.text(result.get("source_run_id")).equals(old.episodeRunId())
                &&StrictJson.text(result.get("episode_run_id")).equals(after.frame().episodeRunId())
                &&!old.episodeRunId().equals(after.frame().episodeRunId()),"episode origin result changed its actual old or new episode");
        String actor=proof.kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR?"actual_successor_character_id":"episode_character_id";
        StrictJson.require(org.xar.ck3.control.contracts.NativeCharacterId.fromJson(result.get(actor)).value()==after.frame().identity().player().longValueExact(),"episode origin result changed its actual new actor");
        if(proof.kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR)StrictJson.require(
                org.xar.ck3.control.contracts.NativeCharacterId.fromJson(result.get("predecessor_character_id")).value()==old.actorId().longValueExact()
                &&!old.actorId().equals(after.frame().identity().player()),"episode origin lost the actual distinct predecessor Driver subject");
    }
    private CycleRecord load(ExactRef ref) { return CycleRecord.fromJson(ContinuityJson.parseObject(archive.loadMaterial(ref).bytes(), ContinuityJson.DOCUMENT_MAX_BYTES)); }
    private void requireCurrentFrame(ContinuityState predecessor, CycleState state, ObservationIdentity frame) {
        requireFrontier(predecessor, state);
        if(usesSavedControlBridge(predecessor,state,frame))return;
        if (state.head().isPresent()) {
            var retained = load(state.head().orElseThrow()).semantic().frame();
            if (matchesObservedBinding(predecessor, retained, frame)) return;
            if (matchesSettledObservedBinding(state, frame)) return;
            if (matchesPublishedReadBinding(predecessor, state.session(), retained, frame)) return;
            requireSameIdentity(retained, frame);
        }
        else if(state.originFrame().isPresent()) {
            var retained = state.originFrame().orElseThrow();
            if (matchesObservedBinding(predecessor, retained, frame)) return;
            requireSameIdentity(retained, frame);
        }
        else requireSettledBinding(predecessor, frame);
    }

    /** Canonical same-game recovery can retain a newer observed frontier without another completed cycle. */
    private static boolean matchesObservedBinding(ContinuityState actual, ObservationIdentity retained, ObservationIdentity frame) {
        var binding = actual.toJson().get("latest_binding");
        if (binding == null || binding.isNull()) return false;
        var row = StrictJson.object(binding, Set.of("date_raw", "actor_character_id", "episode_run_id",
                "snapshot_id", "revision", "native_revision"));
        var nativeRevision = row.get("native_revision");
        if (nativeRevision.isNull()) return false;
        var revision = StrictJson.integer(nativeRevision, BigInteger.ZERO, StrictJson.UINT64_MAX);
        var identity = frame.frame().identity();
        boolean matches = number(row, "date_raw") == identity.dateRaw().longValueExact()
                && number(row, "actor_character_id") == identity.player().longValueExact()
                && text(row, "episode_run_id").equals(frame.frame().episodeRunId())
                && revision.equals(identity.nativeRevision());
        if (!matches) return false;
        requireObservedContinuation(retained, frame);
        return true;
    }

    private static void requireObservedBindingNotRegressed(ContinuityState actual, ObservationIdentity frame) {
        var binding = StrictJson.object(actual.toJson().get("latest_binding"), Set.of("date_raw", "actor_character_id",
                "episode_run_id", "snapshot_id", "revision", "native_revision"));
        var identity = frame.frame().identity();
        StrictJson.require(number(binding, "actor_character_id") == identity.player().longValueExact()
                && text(binding, "episode_run_id").equals(frame.frame().episodeRunId())
                && identity.dateRaw().compareTo(BigInteger.valueOf(number(binding, "date_raw"))) >= 0
                && identity.nativeRevision().compareTo(StrictJson.integer(binding.get("native_revision"),
                        BigInteger.ZERO, StrictJson.UINT64_MAX)) >= 0,
                "settled adoption regressed or changed its canonical observed binding");
    }

    private SettledObservation settledObservation(CycleState branch) {
        var adopted = settledObservation;
        return adopted != null && adopted.owner().equals(branch.session())
                && adopted.cycleStateDigest().equals(ContinuityJson.digest(branch.toJson())) ? adopted : null;
    }

    private boolean matchesSettledObservedBinding(CycleState branch, ObservationIdentity frame) {
        var adopted = settledObservation(branch);
        return adopted != null && sameIdentity(adopted.frame(), frame)
                && frame.frame().revision().compareTo(adopted.frame().frame().revision()) >= 0;
    }

    /** The caller has already resolved this exact APPLIED original through canonicalReceipt. */
    private boolean matchesSettledActionContinuation(CycleState branch, ActionReceipt original) {
        var adopted = settledObservation(branch);
        if (adopted == null) return false;
        var before = original.command().before();
        requireObservedContinuation(adopted.frame(), before);
        StrictJson.require(before.frame().revision().compareTo(adopted.frame().frame().revision()) >= 0,
                "canonical action regressed its adopted observation's public revision");
        return true;
    }

    /** Retain only the exact already-applied known reply; this grants no current action or SAVE proof. */
    private boolean matchesRecordedKnownCompletion(ContinuityStorePort.Session same, WriterContracts.Head head,
            CycleState branch, ActionReceipt receipt) throws IOException {
        if(head.state().status()==ContinuityState.Status.REPAIR_REQUIRED
                &&receipt.state() instanceof ActionState.CompositeSettled life
                &&life.settlement() instanceof ActionState.Applied
                &&org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(receipt.command().operation().value())
                &&org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER.equals(life.execution().handlerId())) {
            if(!requirePublishedAppliedLifeRepair(head.state(),receipt,branch.session()))return false;
            var before=receipt.command().before();requireObservedBindingNotRegressed(head.state(),before);
            var retained=load(branch.head().orElseThrow()).semantic();requireObservedContinuation(retained.frame(),before);
            StrictJson.require(before.frame().revision().compareTo(StrictJson.integer(head.state().toJson().get("latest_binding").get("revision"),BigInteger.ZERO,StrictJson.UINT64_MAX))>=0
                    &&before.frame().revision().compareTo(retained.frame().frame().revision())>=0
                    &&!life.execution().guard().observedAt().isBefore(retained.observedAt()),
                    "confirmed Life material must preserve the actual original guard and retained cycle observation");
            StrictJson.require(head.digest().equals(same.head().digest()),"confirmed Life material RETAIN changed the actual writer head");return true;
        }
        if(!(receipt.state() instanceof ActionState.Settled))return false;
        var originals = archive.withSession(same);
        var known = ContinuityBatchJournal.readOnlyPendingKnownCompletionRoot(head.state(), branch.session(),
                ContinuityActionJournal.receipts(head.state(), originals), originals);
        if (known.filter(receipt::equals).isEmpty()) return false;
        var before = receipt.command().before();
        requireObservedBindingNotRegressed(head.state(), before);
        StrictJson.require(before.frame().revision().compareTo(StrictJson.integer(
                head.state().toJson().get("latest_binding").get("revision"), BigInteger.ZERO, StrictJson.UINT64_MAX)) >= 0,
                "confirmed reply regressed its canonical public revision");
        var retained = load(branch.head().orElseThrow()).semantic();
        requireObservedContinuation(retained.frame(), before);
        StrictJson.require(before.frame().revision().compareTo(retained.frame().frame().revision()) >= 0
                && !((ActionState.Settled) receipt.state()).attempt().guard().observedAt().isBefore(retained.observedAt()),
                "confirmed reply predates or regresses its retained cycle observation");
        StrictJson.require(head.digest().equals(same.head().digest()), "confirmed reply retention changed its actual writer head");
        return true;
    }

    /** Only RETAIN of this canonical scheduler terminal may recover its original pre-action READ. */
    private boolean matchesRecordedSwayReadContinuation(ContinuityStorePort.Session same, WriterContracts.Head head,
            CycleState branch, ActionReceipt receipt) throws IOException {
        if (!(receipt.state() instanceof ActionState.CompositeSettled settled)
                || !(settled.settlement() instanceof ActionState.SwaySchedulerCompleted completed)
                || !(completed.proof().business() instanceof org.xar.ck3.control.application.planning.sway.SwaySchedulerCompletion.NoNewBusiness)
                || branch.head().isEmpty()) return false;
        StrictJson.require(settled.execution().children().isEmpty() && completed.proof().childReceiptRefs().isEmpty()
                && !receipt.visibleGameplay() && !receipt.eligibleAdvance(),
                "Sway no-new-business retention changed its canonical child custody or effect classification");
        var originals = archive.withSession(same);
        var command = receipt.command(); var before = command.before(); var completion = completed.proof();
        completion.validateParent(command);
        StrictJson.require(head.digest().equals(same.head().digest()), "Sway READ retention requires its exact actual writer head");
        var run = org.xar.ck3.control.application.planning.sway.SwaySchedulerReplay.decodeRun(originals.loadMaterial(completion.originalRun()).bytes());
        var stage = org.xar.ck3.control.application.planning.sway.SwaySchedulerReplay.decodeStage(originals.loadMaterial(run.stage()).bytes());
        StrictJson.require(stage.command().equals(command) && run.child().isEmpty(),
                "Sway READ retention crossed its complete original stage/parent or child custody");
        var read = originals.loadRead(stage.rootRead());
        var terminal = terminal(receipt);
        NativeEffectEvidence.FrameLoader actualLoader = terminalFrames;
        StrictJson.require(actualLoader != null, "Sway READ retention requires the actual Root frame loader");
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(read, originals);
        org.xar.ck3.control.application.planning.sway.SwaySharedRoot.requirePublicCapture(read);
        StrictJson.require(stage.rootRead().equals(originals.readReferenceOf(read))
                && read.request().operation().equals(org.xar.ck3.control.application.planning.sway.OrdinarySwayReadSource.ROOT)
                && read.request().origin() instanceof CommandOrigin.Gameplay
                && read.request().before().equals(before) && read.request().source().equals(command.source())
                && read.request().sessionId().equals(command.sessionId()) && read.request().deadline().equals(command.deadline())
                && read.before().paused() && read.after().paused() && read.before().mapReady() && read.after().mapReady()
                && read.before().playerAlive() && read.after().playerAlive(),
                "Sway original ROOT read changed its exact source, parent frame, deadline or guarded map");
        var retained = load(branch.head().orElseThrow()).semantic();
        for (var guard : List.of(read.before().binding(), read.after().binding())) {
            var rebuilt = org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(guard, originals, actualLoader);
            org.xar.ck3.control.application.effects.RootGuardEvidence.requireHistory(guard, originals, same);
            StrictJson.require(guard.origin().equals(command.origin()) && guard.source().equals(command.source())
                    && guard.sessionId().equals(command.sessionId()) && sameIdentity(rebuilt.identity(), before)
                    && rebuilt.identity().frame().revision().equals(before.frame().revision())
                    && !guard.observedAt().isBefore(retained.observedAt()) && !guard.observedAt().isAfter(terminal.observedAt()),
                    "Sway original ROOT guard crossed its actual frame, owner or retained/terminal time");
        }
        StrictJson.require(completion.finalReads().size() == 1, "Sway retention requires its one actual final ROOT read");
        var finalRef = completion.finalReads().getFirst(); var finalRead = originals.loadRead(finalRef);
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(finalRead, originals);
        org.xar.ck3.control.application.planning.sway.SwaySharedRoot.requirePublicCapture(finalRead);
        StrictJson.require(finalRef.equals(originals.readReferenceOf(finalRead)) && finalRead.contractId().equals(read.contractId())
                && finalRead.request().operation().equals(read.request().operation()) && finalRead.request().before().equals(terminal.frame())
                && finalRead.request().source().equals(command.source()) && finalRead.request().sessionId().equals(command.sessionId())
                && sameIdentity(finalRead.after().binding().observed(), terminal.frame())
                && finalRead.before().paused() && finalRead.after().paused() && finalRead.before().mapReady() && finalRead.after().mapReady()
                && finalRead.before().playerAlive() && finalRead.after().playerAlive(),
                "Sway retention final ROOT read differs from its canonical actual terminal frame");
        for (var guard : List.of(finalRead.before().binding(), finalRead.after().binding())) {
            var rebuilt = org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(guard, originals, actualLoader);
            org.xar.ck3.control.application.effects.RootGuardEvidence.requireHistory(guard, originals, same);
            StrictJson.require(rebuilt.identity().equals(terminal.frame()) && guard.source().equals(command.source())
                    && guard.sessionId().equals(command.sessionId()) && !guard.observedAt().isBefore(read.after().binding().observedAt()),
                    "Sway final ROOT guard crossed its exact terminal frame, source or original READ time");
        }
        requireObservedBindingNotRegressed(head.state(), before);
        requireObservedContinuation(retained.frame(), before); requireObservedContinuation(before, terminal.frame());
        StrictJson.require(before.frame().identity().dateRaw().equals(retained.frame().frame().identity().dateRaw())
                && terminal.frame().frame().identity().dateRaw().equals(before.frame().identity().dateRaw())
                && before.frame().revision().compareTo(retained.frame().frame().revision()) >= 0
                && terminal.frame().frame().revision().compareTo(before.frame().revision()) >= 0
                && before.frame().revision().compareTo(StrictJson.integer(head.state().toJson().get("latest_binding").get("revision"), BigInteger.ZERO, StrictJson.UINT64_MAX)) >= 0,
                "Sway original READ continuation changed its retained date or regressed native/public revision");
        StrictJson.require(head.digest().equals(same.head().digest()), "Sway original READ retention changed its actual writer head");
        return true;
    }

    /** A canonical READ retains its actual observation while leaving saved/cycle bindings untouched. */
    private boolean matchesPublishedReadBinding(ContinuityState actual, SessionIdentity owner,
            ObservationIdentity retained, ObservationIdentity frame) {
        var publication = actual.toJson().get(WriterContracts.DRIVER_READ_HISTORY_FIELD);
        if (publication == null || publication.isNull()) return false;
        var row = StrictJson.object(publication, Set.of("schema", "evidence_id", "token", "source", "predecessor_head_sha256",
                "read_head_sha256", "read_head_sequence", "before_version", "after_version", "episode_epoch",
                "before_driver", "after_driver", "read_rows"));
        var reads = row.get("read_rows");
        StrictJson.require(reads.isArray() && !reads.isEmpty() && reads.size() <= 128, "finite canonical READ rows required");
        for (int index = reads.size() - 1; index >= 0; index--) {
            var item = reads.get(index);
            if (item.has("row_kind") && !Set.of(
                    org.xar.ck3.control.application.driver.DriverReadHistoryPublisher.SUMMARY_ROW_KIND,
                    org.xar.ck3.control.application.driver.DriverReadHistoryPublisher.EXECUTE_ROW_KIND)
                    .contains(StrictJson.text(item.get("row_kind")))) continue;
            var reference = item.get("read");
            if (reference == null || reference.isNull()) continue;
            var readRef = ExactRef.fromJson(reference);
            var read = archive.loadRead(readRef);
            var observed = read.after().binding().observed();
            if (!sameIdentity(observed, frame)) continue;
            StrictJson.require(readRef.equals(archive.readReferenceOf(read))
                    && read.request().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                    && read.request().sessionId().equals(owner.sessionId())
                    && read.request().before().machineId().equals(owner.machineId())
                    && read.request().before().game().equals(owner.game())
                    && read.before().paused() && read.after().paused() && read.before().mapReady() && read.after().mapReady()
                    && read.before().playerAlive() && read.after().playerAlive()
                    && frame.frame().revision().compareTo(observed.frame().revision()) >= 0,
                    "canonical READ continuation crossed its actual owner, guarded map or public revision");
            requireObservedContinuation(retained, observed);
            requireObservedContinuation(read.request().before(), observed);
            return true;
        }
        return false;
    }
    private void requireSavedProofFrame(ContinuityState actual,CycleState saved,VerifiedSemantic verified) {
        if(usesSavedControlBridge(actual,saved,verified.frame()))return;
        if(saved.head().isPresent() || saved.originFrame().isPresent()) requireProofFrame(actual,saved,verified);
        // An initial saved branch has no ordinary receipt; its actual paired SAVE was verified above.
    }
    /** Only the exact canonical last-SAVED state may use its actual pair's post-SAVE native frame, with zero new cycle credit. */
    private boolean usesSavedControlBridge(ContinuityState actual,CycleState candidate,ObservationIdentity frame) {
        ObjectNode whole=actual.toJson();if(!whole.has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD))return false;
        ObjectNode saved=StrictJson.object(whole.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),Set.of("pair","state"));
        CycleState canonical=parseState(saved.get("state"));
        if(!canonical.session().equals(candidate.session())||canonical.completedCycles()!=actual.settledCycles()
                ||!ContinuityJson.digest(canonical.toJson()).equals(ContinuityJson.digest(candidate.toJson())))return false;
        ObservationIdentity pair=CheckpointPairCodec.decode(ContinuityJson.canonical(saved.get("pair"))).frame();
        return sameIdentity(pair,frame)&&frame.frame().revision().compareTo(pair.frame().revision())>=0;
    }
    private record CycleState(SessionIdentity session, long basisCycles, long completedCycles, Optional<ExactRef> head, Optional<ExactRef> pending, Optional<String> retainedLegacyPendingDigest,Optional<ObservationIdentity> originFrame,Optional<ExactRef> episodeOrigin) {
        private CycleState {
            Objects.requireNonNull(session); StrictJson.safe(basisCycles, 0); StrictJson.safe(completedCycles, basisCycles); Objects.requireNonNull(head); Objects.requireNonNull(pending);
            Objects.requireNonNull(retainedLegacyPendingDigest); retainedLegacyPendingDigest.ifPresent(WriterContracts::requireDigest);
            Objects.requireNonNull(originFrame);Objects.requireNonNull(episodeOrigin);StrictJson.require(episodeOrigin.isEmpty()||originFrame.isPresent(),"episode origin requires its actual complete new frame");
        }
        CycleState withPending(Optional<ExactRef> value) { return new CycleState(session, basisCycles, completedCycles, head, value, retainedLegacyPendingDigest,originFrame,episodeOrigin); }
        ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("schema", STATE_SCHEMA); row.set("session", sessionToJson(session)); row.put("basis_cycles", basisCycles); row.put("completed_cycles", completedCycles);
            if (head.isPresent()) row.set("head", head.orElseThrow().toJson()); else row.putNull("head");
            if (pending.isPresent()) row.set("pending_receipt", pending.orElseThrow().toJson()); else row.putNull("pending_receipt");
            if (retainedLegacyPendingDigest.isPresent()) row.put("retained_legacy_pending_digest", retainedLegacyPendingDigest.orElseThrow()); else row.putNull("retained_legacy_pending_digest");
            if(originFrame.isPresent())row.set("origin_frame",ProposalLifecycleCodec.observation(originFrame.orElseThrow()));else row.putNull("origin_frame");
            if(episodeOrigin.isPresent())row.set("episode_origin",episodeOrigin.orElseThrow().toJson());else row.putNull("episode_origin");return row;
        }
    }
    private static CycleState state(ContinuityState predecessor, SessionIdentity owner) {
        if(EpisodeWindow.state(predecessor).isPresent()) {
            EpisodeWindow.requireActive(predecessor);
            StrictJson.require(predecessor.toJson().has(STATE_FIELD),"actual first-SAVE BASELINE needs its private next-cycle initialization");
            CycleState branch=retainedState(predecessor,owner);
            StrictJson.require(branch.originFrame().isPresent(),"old cycle branch cannot authorize the new ACTIVE Game without a source-bound restore/episode/window origin");
            return branch;
        }
        return retainedState(predecessor,owner);
    }
    /** Canonical historical BEGIN preserves its predecessor fields even while awaiting its first SAVE. */
    private static CycleState retainedState(ContinuityState predecessor,SessionIdentity owner) {
        ObjectNode whole=predecessor.toJson();
        if(!whole.has(STATE_FIELD))return new CycleState(owner,predecessor.settledCycles(),predecessor.settledCycles(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
        CycleState parsed=parseState(whole.get(STATE_FIELD));
        StrictJson.require(parsed.session().equals(owner),"a different Game/session needs its actual private restore or episode cycle rebind");return parsed;
    }
    private static CycleState parseState(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "session", "basis_cycles", "completed_cycles", "head", "pending_receipt", "retained_legacy_pending_digest","origin_frame","episode_origin"));
        StrictJson.require(text(row, "schema").equals(STATE_SCHEMA), "ordinary cycle state version");
        return new CycleState(sessionFromJson(row.get("session")), number(row, "basis_cycles"), number(row, "completed_cycles"), optionalRef(row.get("head")), optionalRef(row.get("pending_receipt")),
                row.get("retained_legacy_pending_digest").isNull() ? Optional.empty() : Optional.of(text(row, "retained_legacy_pending_digest")),
                row.get("origin_frame").isNull()?Optional.empty():Optional.of(ProposalLifecycleCodec.decodeObservation(row.get("origin_frame"))),optionalRef(row.get("episode_origin")));
    }
    private record CycleRecord(SessionIdentity session, ExactRef receipt, SemanticEvidence semantic, Optional<ExactRef> previous, long completedCycles, Classification classification) {
        private CycleRecord { Objects.requireNonNull(session); Objects.requireNonNull(receipt); Objects.requireNonNull(semantic); Objects.requireNonNull(previous); StrictJson.safe(completedCycles, 0); Objects.requireNonNull(classification); }
        ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("schema", RECORD_SCHEMA); row.set("session", sessionToJson(session)); row.set("receipt_ref", receipt.toJson()); row.set("semantic", semanticToJson(semantic));
            if (previous.isPresent()) row.set("previous", previous.orElseThrow().toJson()); else row.putNull("previous"); row.put("completed_cycles", completedCycles); row.put("classification", classification.name()); return row;
        }
        static CycleRecord fromJson(JsonNode value) {
            ObjectNode row = StrictJson.object(value, Set.of("schema", "session", "receipt_ref", "semantic", "previous", "completed_cycles", "classification"));
            StrictJson.require(text(row, "schema").equals(RECORD_SCHEMA), "cycle record version");
            return new CycleRecord(sessionFromJson(row.get("session")), ExactRef.fromJson(row.get("receipt_ref")), semanticFromJson(row.get("semantic")), optionalRef(row.get("previous")), number(row, "completed_cycles"), Classification.valueOf(text(row, "classification")));
        }
    }
    private static void requireLegacyPendingClear(ContinuityState state, CycleState cycle) {
        ObjectNode row = state.toJson();
        boolean pending = List.of("pending_cycle", "pending_checkpoint").stream().anyMatch(key -> row.has(key) && !row.get(key).isNull());
        if (pending) StrictJson.require(cycle.retainedLegacyPendingDigest().filter(legacyPendingDigest(state)::equals).isPresent(),
                "original pending remains unresolved; only its exact source-bound restored tombstone may coexist with a new Game cycle");
    }
    private static String legacyPendingDigest(ContinuityState state) {
        ObjectNode row = StrictJson.object(); ObjectNode source = state.toJson();
        for (String key : List.of("pending_cycle", "pending_checkpoint")) {
            ObjectNode slot = row.putObject(key); slot.put("present", source.has(key)); if (source.has(key)) slot.set("value", source.get(key));
        }
        return ContinuityJson.digest(row);
    }
    private static void requireOwner(ContinuityState state, SessionIdentity owner) { StrictJson.require(state.machineId().equals(owner.machineId()), "ordinary cycle machine differs from the canonical writer"); }
    private static void requireFrontier(ContinuityState predecessor, CycleState state) {
        StrictJson.require((state.basisCycles() <= predecessor.settledCycles()||state.episodeOrigin().isPresent()) && state.completedCycles() >= predecessor.settledCycles(),
                "ordinary cycle branch cannot replace or move behind the actual saved cycle frontier");
    }
    private static void requireActive(ContinuityState state) { StrictJson.require(state.status() == ContinuityState.Status.RUNNING || state.status() == ContinuityState.Status.COMPLETE, "actual continuity manual repair remains unresolved"); }
    private static void requireSettledBinding(ContinuityState state, ObservationIdentity frame) {
        ObjectNode row = StrictJson.object(state.toJson().get("latest_binding"), Set.of("date_raw", "actor_character_id", "episode_run_id", "snapshot_id", "revision", "native_revision"));
        StrictJson.require(number(row, "date_raw") == frame.frame().identity().dateRaw().longValueExact()
                && number(row, "actor_character_id") == frame.frame().identity().player().longValueExact()
                && row.get("native_revision") != null && row.get("native_revision").isIntegralNumber()
                && row.get("native_revision").bigIntegerValue().compareTo(frame.frame().identity().nativeRevision()) <= 0
                && text(row, "episode_run_id").equals(frame.frame().episodeRunId()), "initial SEM differs from the actual last-settled canonical binding");
    }
    public static void requireSameIdentity(ObservationIdentity left, ObservationIdentity right) { requireSameOwner(left, right); StrictJson.require(left.frame().identity().equals(right.frame().identity()), "native player/revision/date identity differs"); }
    /** A real SAVE may publish a newer native/public revision while preserving this one actor/episode/date.
     * Same-date verified proof DATA grants no current action or read-publication authority. */
    private void requireProofFrame(ContinuityState actual, CycleState state, VerifiedSemantic verified) {
        requireFrontier(actual, state);
        var frame = verified.frame();
        if (usesSavedControlBridge(actual, state, frame)) return;
        if (state.head().isPresent()) {
            var retained = load(state.head().orElseThrow()).semantic();
            requireSavedContinuation(retained.frame(), frame);
            StrictJson.require(!verified.observedAt().isBefore(retained.observedAt()), "proof SEM predates its retained cycle semantic");
        } else if (state.originFrame().isPresent()) {
            var retained = state.originFrame().orElseThrow();
            requireSavedContinuation(retained, frame);
        } else {
            requireSettledBinding(actual, frame);
        }
    }

    private static void requireSavedContinuation(ObservationIdentity before,ObservationIdentity saved) {
        requireSameOwner(before,saved);
        StrictJson.require(before.observationVersion()==saved.observationVersion()
                &&before.frame().identity().dateRaw().equals(saved.frame().identity().dateRaw())
                &&saved.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision())>=0,
                "actual SAVE changed actor/episode/date or regressed its native/public revision");
    }
    private static boolean sameIdentity(ObservationIdentity left,ObservationIdentity right) {
        return left.machineId().equals(right.machineId())&&left.game().equals(right.game())
                &&left.observationVersion()==right.observationVersion()
                &&left.frame().episodeRunId().equals(right.frame().episodeRunId())
                &&left.frame().identity().equals(right.frame().identity());
    }
    private static void requireSameOwner(ObservationIdentity left, ObservationIdentity right) {
        StrictJson.require(left.machineId().equals(right.machineId()) && left.game().equals(right.game())
                && left.frame().episodeRunId().equals(right.frame().episodeRunId()) && left.frame().identity().player().equals(right.frame().identity().player()), "Game/player/episode changed without its actual binding authority");
    }
    private static void strictCycle(ObjectNode row) { StrictJson.object(row, Set.of("evidence_id", "source", "session", "operation", "receipt_ref", "semantic", "cycle_record_ref", "cycle_record")); }
    private static void strictRebind(ObjectNode row) {
        StrictJson.object(row, Set.of("evidence_id", "source", "session", "operation", "attachment_identity", "attachment_head_digest", "restore_pair", "semantic", "previous_state_ref", "new_cycle_state"));
        StrictJson.require(Set.of(RESTORE_SOURCE, IMPORTED_RESTORE_SOURCE).contains(text(row, "source")), "known restore cycle rebind source required");
    }
    private static void strictEpisode(ObjectNode row){StrictJson.object(row,Set.of("evidence_id","source","operation","session","before_session","parent_receipt_ref","lifecycle_commit_digest","predecessor_head_digest","semantic","previous_state_ref","new_cycle_state"));}
    private static void strictBatch(ObjectNode row) {
        Set<String> fields=JournalKind.WORKER_RESTART_CAPTURE.name().equals(text(row,"boundary"))
                ?Set.of("evidence_id","source","session","batch_id","boundary","checkpoint_pair","completed_cycle_proof","restart_manifest")
                :Set.of("evidence_id","source","session","batch_id","boundary","checkpoint_pair","completed_cycle_proof");
        if (SAVED_MATERIAL_SOURCE.equals(text(row, "source"))) {
            StrictJson.require(JournalKind.SAVE_CONFIRMED.name().equals(text(row, "boundary")), "material DATA source is restricted to SAVE");
            var withMaterial = new HashSet<>(fields);
            withMaterial.add(org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialEvidence.FIELD);
            fields = withMaterial;
        }
        StrictJson.object(row,fields,fields);
        if (JournalKind.SAVE_CONFIRMED.name().equals(text(row, "boundary")))
            StrictJson.require(Set.of("java-ordinary-session/v1", "java-reconciled-original-save/v1", SAVED_MATERIAL_SOURCE)
                    .contains(text(row, "source")), "known exact SAVE details source required");
    }
    public static ObjectNode semanticToJson(SemanticEvidence value) {
        ObjectNode row = StrictJson.object(); row.set("frame", ProposalLifecycleCodec.observation(value.frame())); row.set("semantic", value.semantic().toJson());
        row.set("original_native_packet", value.originalNativePacket().toJson()); row.set("driver_stamp", value.driverStamp().toJson()); row.set("original_driver", value.originalDriver().toJson()); row.put("observed_at", value.observedAt().toString()); return row;
    }
    public static SemanticEvidence semanticFromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("frame", "semantic", "original_native_packet", "driver_stamp", "original_driver", "observed_at"));
        return new SemanticEvidence(ProposalLifecycleCodec.decodeObservation(row.get("frame")), ExactRef.fromJson(row.get("semantic")), ExactRef.fromJson(row.get("original_native_packet")), ExactRef.fromJson(row.get("driver_stamp")), ExactRef.fromJson(row.get("original_driver")), Instant.parse(StrictJson.utc(text(row, "observed_at"))));
    }
    public static ObjectNode sessionToJson(SessionIdentity value) {
        ObjectNode row = StrictJson.object(); row.put("machine_id", value.machineId()); row.set("game", value.game().toJson()); row.put("session_id", value.sessionId()); return row;
    }
    public static SessionIdentity sessionFromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("machine_id", "game", "session_id"));
        return new SessionIdentity(text(row, "machine_id"), GameGeneration.fromJson(row.get("game")), text(row, "session_id"));
    }
    public static ObjectNode proofToJson(CompletedCycleProof proof) {
        ObjectNode row = StrictJson.object(); row.put("completed_cycles", proof.completedCycles()); row.set("semantic", semanticToJson(proof.semantic())); row.put("cycle_state_digest", proof.cycleStateDigest()); return row;
    }
    public static CompletedCycleProof proofFromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("completed_cycles", "semantic", "cycle_state_digest")); return new CompletedCycleProof(number(row, "completed_cycles"), semanticFromJson(row.get("semantic")), text(row, "cycle_state_digest"));
    }
    private static Optional<ExactRef> optionalRef(JsonNode value) { StrictJson.require(value != null, "missing is not an explicit nullable cycle reference"); return value.isNull() ? Optional.empty() : Optional.of(ExactRef.fromJson(value)); }
    private static long number(ObjectNode row, String field) { return StrictJson.integer(row.get(field), 0, StrictJson.MAX_SAFE_INTEGER); }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static ObjectNode originalFrame(ObservationIdentity value) {
        ObjectNode row = StrictJson.object(); row.put("date_raw", value.frame().identity().dateRaw()); row.put("actor_character_id", value.frame().identity().player()); row.put("episode_run_id", value.frame().episodeRunId()); row.put("snapshot_id", value.frame().snapshotId()); row.put("revision", value.frame().revision()); row.put("native_revision", value.frame().identity().nativeRevision()); return row;
    }
}
