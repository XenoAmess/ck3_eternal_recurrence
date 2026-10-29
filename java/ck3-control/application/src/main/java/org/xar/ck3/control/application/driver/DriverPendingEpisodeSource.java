package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.List;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer.PendingEpisode;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Root installs its actual private M3-qualified pending source. DATA captures cannot install themselves or grant readiness. */
public interface DriverPendingEpisodeSource {
    String DOMAIN_SCHEMA="xar.java.natural-clock-originals/v2";
    String PUBLICATION_KEY="driver_pending_episode_source";
    String MUTATION_KEY="driver_pending_episode_mutation_source";
    /** True NEW/NATURAL episode reset only; cold pending recovery still needs its actual canonical domain/private issuer. */
    static org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj clearEpisodeData(
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj original) {
        var values=new java.util.LinkedHashMap<>(original.members());values.remove(SuccessorUiObligation.AUXILIARY_KEY);
        values.remove(PUBLICATION_KEY);values.remove(MUTATION_KEY);
        return new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(values);
    }
    List<ExactRef> sources();
    Capture current(ContinuityStorePort.Session same,DriverStateAssembler expected) throws IOException;
    /** Checks the identical live private issuer/token, genuine M3 cause and exact original committed projection before CAS. */
    void requireCurrent(ContinuityStorePort.Session same,DriverStateAssembler expected,Capture identical) throws IOException;
    /** Checks that identical issuer and canonical pending child after its actual CAS, without requiring the obsolete old subject to be current. */
    void requirePublished(ContinuityStorePort.Session same,DriverStateAssembler expected,Capture identical,
            DriverSnapshotFacts.Known actualPublished) throws IOException;
    Mutation currentMutation(ContinuityStorePort.Session same,DriverStateAssembler expected) throws IOException;
    void requireMutation(ContinuityStorePort.Session same,DriverStateAssembler expected,Mutation identical) throws IOException;
    void requirePublishedMutation(ContinuityStorePort.Session same,DriverStateAssembler expected,Mutation identical,
            DriverSnapshotFacts.Known actualPublished) throws IOException;
    /** The actual installed UI source must recognize its genuine current publication, original parent and exact once-only new-subject child. */
    void requireChild(ContinuityStorePort.Session same,DriverStateAssembler expected,
            DriverStateAssembler.PendingEpisodePublication actualPublication,ActionCommand originalParent,ActionCommand actualChild) throws IOException;
    interface InitialData {
        DriverSnapshotFacts.Known actualKnown();
        LifecycleObservationPort.Snapshot terminalSnapshot();
        PendingEpisode pendingEpisode();
        ExactRef canonicalDomainRef();
        DriverPendingEpisodeProjection canonicalProjection();
        ExactRef projectionOriginal();
        ExactRef originalParentKnown();
        ExactRef originalBeforeNative();
    }
    interface Capture extends InitialData {
        DomainBodies.PreparedImport originalPrepared();
        WriterContracts.Receipt actualReceipt();
    }
    /** Actual historical edge, never an invented copy of the warm prepared CAS. */
    interface RecordedCapture extends InitialData {
        DomainBodies.RecordedImport recordedImport();
        ExactRef originalSource();
    }
    enum MutationPhase { OBSERVE,CLOSE_ENTER,RETAIN_RESULT,RETAIN_POSTCONDITIONS,RECONCILE,REBIND,FINALIZE }
    sealed interface Change permits Observe,EnterClose,RetainResult,RetainPostconditions,Reconcile,Rebind,Finalize {
        MutationPhase phase();
    }
    record Observe(SuccessorUiObligation.Observation value) implements Change {
        @Override public MutationPhase phase(){return MutationPhase.OBSERVE;}
    }
    record EnterClose(SuccessorUiObligation.CloseAttempt value) implements Change {
        @Override public MutationPhase phase(){return MutationPhase.CLOSE_ENTER;}
    }
    record RetainResult(SuccessorUiObligation.CloseReceipt value) implements Change {
        @Override public MutationPhase phase(){return MutationPhase.RETAIN_RESULT;}
    }
    record RetainPostconditions(SuccessorUiObligation.CloseReceipt value) implements Change {
        @Override public MutationPhase phase(){return MutationPhase.RETAIN_POSTCONDITIONS;}
    }
    record Reconcile(SuccessorUiObligation.ReadOnlyReconciliation value) implements Change {
        @Override public MutationPhase phase(){return MutationPhase.RECONCILE;}
    }
    record Rebind(SuccessorUiObligation.Rebind value) implements Change {
        @Override public MutationPhase phase(){return MutationPhase.REBIND;}
    }
    /** These values are DATA until the installed issuer revalidates its genuine private M3 Finalized object and canonical source. */
    record Finalize(SuccessorUiObligation.Finalization value,SuccessorUiObligation.Observation currentObservation,DriverObservationAssembler.FullSnapshot currentFrame,
            RawJson matchedEstate,java.time.Instant observedAtUtc) implements Change {
        @Override public MutationPhase phase(){return MutationPhase.FINALIZE;}
    }
    interface MutationData {
        DriverSnapshotFacts.Known actualKnown();
        SuccessorUiObligation beforeObligation();
        Change change();
        SuccessorUiObligation afterObligation();
        DriverPendingEpisodeMutations.Prepared preparedProjection();
        ExactRef canonicalDomainRef();
        ExactRef originalBeforeNative();
        java.time.Instant actualObservedAtUtc();
    }
    interface Mutation extends MutationData {
        DomainBodies.PreparedImport originalPrepared();
        WriterContracts.Receipt actualReceipt();
    }
    interface RecordedMutation extends MutationData {
        DomainBodies.RecordedImport recordedImport();
        ExactRef originalSource();
    }
    /** Persisted source DATA has one field contract, shared by the real producer and cold consumer. */
    sealed interface RecoveryMetadata permits InitialMetadata,MutationMetadata {
        String machineId();java.time.Instant observedAtUtc();ExactRef beforeKnown();ExactRef beforeNative();ExactRef canonicalDomain();
        long canonicalHeadSequence();String canonicalHeadSha256();String eventIdentity();List<ExactRef> producerSources();
        default RawJson encode(){return encodeRecoveryMetadata(this);}
    }
    record InitialMetadata(String machineId,java.time.Instant observedAtUtc,ExactRef beforeKnown,ExactRef beforeNative,ExactRef parentKnown,
            ExactRef canonicalDomain,long canonicalHeadSequence,String canonicalHeadSha256,String eventIdentity,
            ExactRef projection,List<ExactRef> producerSources) implements RecoveryMetadata {
        public InitialMetadata {producerSources=List.copyOf(producerSources);requireMetadata(machineId,observedAtUtc,beforeKnown,canonicalDomain,canonicalHeadSequence,canonicalHeadSha256,eventIdentity,producerSources);for(var ref:List.of(beforeNative,parentKnown,projection))requireRecoveryRef(ref);}
    }
    record MutationMetadata(String machineId,java.time.Instant observedAtUtc,ExactRef beforeKnown,ExactRef beforeNative,ExactRef canonicalDomain,
            long canonicalHeadSequence,String canonicalHeadSha256,String eventIdentity,MutationPhase phase,
            ExactRef beforeObligation,ExactRef afterObligation,List<ExactRef> producerSources) implements RecoveryMetadata {
        public MutationMetadata {producerSources=List.copyOf(producerSources);requireMetadata(machineId,observedAtUtc,beforeKnown,canonicalDomain,canonicalHeadSequence,canonicalHeadSha256,eventIdentity,producerSources);java.util.Objects.requireNonNull(phase);for(var ref:List.of(beforeNative,beforeObligation,afterObligation))requireRecoveryRef(ref);}
    }
    private static void requireMetadata(String machine,java.time.Instant observed,ExactRef before,ExactRef domain,long sequence,String digest,String identity,List<ExactRef> sources) {
        org.xar.ck3.control.contracts.StrictJson.text(machine);java.util.Objects.requireNonNull(observed);org.xar.ck3.control.contracts.StrictJson.utc(observed.toString());
        requireRecoveryRef(before);requireRecoveryRef(domain);org.xar.ck3.control.contracts.StrictJson.safe(sequence,1);
        org.xar.ck3.control.contracts.StrictJson.require(digest!=null&&digest.matches("[0-9a-f]{64}"),"actual canonical import digest required");
        org.xar.ck3.control.contracts.StrictJson.text(identity);org.xar.ck3.control.contracts.StrictJson.require(!sources.isEmpty()&&sources.size()<=64&&sources.stream().distinct().count()==sources.size(),"finite exact producer closure required");
        sources.forEach(DriverPendingEpisodeSource::requireRecoveryRef);
    }
    private static void requireRecoveryRef(ExactRef ref) {org.xar.ck3.control.contracts.StrictJson.require(java.util.Objects.requireNonNull(ref).bytes()>0&&ref.bytes()<=67_108_864,"nonempty bounded retained recovery original required");}
    private static RawJson encodeRecoveryMetadata(RecoveryMetadata value) {
        var row=org.xar.ck3.control.contracts.StrictJson.object().put("schema",value instanceof InitialMetadata?"xar.java.pending-episode-driver-source/v2":"xar.java.pending-episode-driver-mutation/v2")
                .put("machine_id",value.machineId()).put("observed_at_utc",value.observedAtUtc().toString())
                .put("canonical_head_sequence",value.canonicalHeadSequence()).put("canonical_head_sha256",value.canonicalHeadSha256()).put("event_identity",value.eventIdentity());
        row.set("before_known",value.beforeKnown().toJson());row.set("before_native",value.beforeNative().toJson());row.set("canonical_domain",value.canonicalDomain().toJson());
        var sources=row.putArray("producer_sources");value.producerSources().forEach(ref->sources.add(ref.toJson()));
        if(value instanceof InitialMetadata initial){row.set("parent_known",initial.parentKnown().toJson());row.set("projection",initial.projection().toJson());}
        else {var mutation=(MutationMetadata)value;row.put("phase",mutation.phase().name());row.set("before_obligation",mutation.beforeObligation().toJson());row.set("after_obligation",mutation.afterObligation().toJson());}
        return new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(row,1_048_576));
    }
    /** Legacy v1 lacks the exact original Known/head and is deliberately not upgraded. */
    static RecoveryMetadata decodeRecoveryMetadata(RawJson original) {
        var row=org.xar.ck3.control.contracts.StrictJson.parse(original.bytes(),1_048_576);
        String schema=org.xar.ck3.control.contracts.StrictJson.text(row.get("schema"));
        boolean initial=schema.equals("xar.java.pending-episode-driver-source/v2");
        org.xar.ck3.control.contracts.StrictJson.require(initial||schema.equals("xar.java.pending-episode-driver-mutation/v2"),"pending source v2 required; legacy cold originals are missing");
        var fields=new java.util.HashSet<>(java.util.Set.of("schema","machine_id","observed_at_utc","before_known","before_native","canonical_domain","canonical_head_sequence","canonical_head_sha256","event_identity","producer_sources"));
        if(initial)fields.addAll(java.util.Set.of("parent_known","projection"));else fields.addAll(java.util.Set.of("phase","before_obligation","after_obligation"));
        org.xar.ck3.control.contracts.StrictJson.object(row,fields);var rawSources=row.get("producer_sources");
        org.xar.ck3.control.contracts.StrictJson.require(rawSources.isArray()&&rawSources.size()<=64,"finite producer sources required");
        var sources=new java.util.ArrayList<ExactRef>();rawSources.forEach(ref->sources.add(ExactRef.fromJson(ref)));
        String machine=org.xar.ck3.control.contracts.StrictJson.text(row.get("machine_id"));var observed=java.time.Instant.parse(org.xar.ck3.control.contracts.StrictJson.utc(org.xar.ck3.control.contracts.StrictJson.text(row.get("observed_at_utc"))));
        var before=ExactRef.fromJson(row.get("before_known"));var domain=ExactRef.fromJson(row.get("canonical_domain"));long sequence=org.xar.ck3.control.contracts.StrictJson.integer(row.get("canonical_head_sequence"),1,org.xar.ck3.control.contracts.StrictJson.MAX_SAFE_INTEGER);
        String digest=org.xar.ck3.control.contracts.StrictJson.text(row.get("canonical_head_sha256")),identity=org.xar.ck3.control.contracts.StrictJson.text(row.get("event_identity"));
        var nativeOriginal=ExactRef.fromJson(row.get("before_native"));
        return initial?new InitialMetadata(machine,observed,before,nativeOriginal,ExactRef.fromJson(row.get("parent_known")),domain,sequence,digest,identity,ExactRef.fromJson(row.get("projection")),sources):
                new MutationMetadata(machine,observed,before,nativeOriginal,domain,sequence,digest,identity,MutationPhase.valueOf(org.xar.ck3.control.contracts.StrictJson.text(row.get("phase"))),ExactRef.fromJson(row.get("before_obligation")),ExactRef.fromJson(row.get("after_obligation")),sources);
    }
    /** Separate installed capability: an ordinary Capture never reconstructs a cold private issuer. */
    interface Recovering extends DriverPendingEpisodeSource {
        Recovery currentRecovery(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException;
        /** Revalidates the identical private Root/M3 historical scope, every canonical import and the actual current Known. */
        void requireRecovery(ContinuityStorePort.Session same,DriverStateAssembler expected,Recovery identical)throws IOException;
        /** The genuine assembler proof is passed back only after the complete read-only replay; no second Driver CAS is allowed. */
        void requireRecovered(ContinuityStorePort.Session same,DriverStateAssembler expected,Recovery identical,
                DriverStateAssembler.PendingEpisodePublication genuine,DriverSnapshotFacts.Known actualCurrent)throws IOException;
    }
    interface Recovery {
        RecordedCapture initialCapture();
        /** Ordered actual canonical transitions after the original pending adoption, including each real ACTION publication. */
        List<RecoveryStep> transitions();
        DriverSnapshotFacts.Known actualCurrent();
    }
    sealed interface RecoveryStep permits RecoveryMutation,RecoveryAction { }
    record RecoveryMutation(RecordedMutation actual) implements RecoveryStep {
        public RecoveryMutation {java.util.Objects.requireNonNull(actual);}
    }
    record RecoveryAction(org.xar.ck3.control.application.action.ActionReceipt actual,
            DriverSnapshotFacts.Known actualAfter) implements RecoveryStep {
        public RecoveryAction {java.util.Objects.requireNonNull(actual);java.util.Objects.requireNonNull(actualAfter);}
    }
    /** Replay output is DATA. Only the identical installed assembler/source can issue a private recovered publication. */
    record ReplayedRecovery(DriverSnapshotFacts.Known originalBefore,DriverSnapshotFacts.Known actualAfter,
            DomainBodies.RecordedImport latestImport,WriterContracts.Receipt latestReceipt,ExactRef canonicalDomain,
            ExactRef originalSource,ExactRef actualDriverOriginal) { }
    /** Read-only reuse of the sole pending and ACTION producers; this method performs no observation, writer commit or CAS. */
    static ReplayedRecovery replayRecovery(ContinuityStorePort.Session same,Recovery actual,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive originals,List<ExactRef> sources)throws IOException {
        java.util.Objects.requireNonNull(actual);sources=List.copyOf(sources);
        var capture=java.util.Objects.requireNonNull(actual.initialCapture());
        var initial=DriverPendingEpisodeProducer.replayInitial(same,capture,originals,sources);
        var current=initial.after();var prepared=capture.recordedImport();var receipt=prepared.receipt();
        var domain=capture.canonicalDomainRef();var source=initial.originalSource();
        var steps=List.copyOf(actual.transitions());
        org.xar.ck3.control.contracts.StrictJson.require(steps.size()<=65_536,"bounded canonical pending recovery history required");
        for(var step:steps) {
            if(step instanceof RecoveryMutation item) {
                var mutation=item.actual();requireSameRecoveryState(current,mutation.actualKnown());
                var next=DriverPendingEpisodeProducer.replayMutation(same,mutation,originals,sources);
                current=next.after();prepared=mutation.recordedImport();receipt=prepared.receipt();
                domain=mutation.canonicalDomainRef();source=next.originalSource();
            } else {
                var item=(RecoveryAction)step;current=replayRecoveryAction(same,capture,item,current,originals);
            }
        }
        requireSameRecoveryState(current,actual.actualCurrent());
        var driver=RawJson.fullMaterial(current.driver().encode());var driverRef=originals.materialReferenceOf(driver);
        org.xar.ck3.control.contracts.StrictJson.require(originals.loadFullMaterial(driverRef).equals(driver),"recovered current Driver lacks its exact retained original");
        return new ReplayedRecovery(initial.before(),actual.actualCurrent(),prepared,receipt,domain,source,driverRef);
    }
    private static DriverSnapshotFacts.Known replayRecoveryAction(ContinuityStorePort.Session same,InitialData initial,
            RecoveryAction step,DriverSnapshotFacts.Known before,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive originals)throws IOException {
        var action=step.actual();var after=step.actualAfter();
        var committed=DriverActionHistoryState.findCommittedCoverage(same,action,originals)
                .orElseThrow(()->new IOException("pending recovery ACTION has no actual canonical publication"));
        var published=committed.publication();
        var origin=action.command().origin();var binding=initial.pendingEpisode().obligation().binding();
        var parent=org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(same.head().state(),binding.parentActionId(),originals)
                .orElseThrow(()->new IOException("actual original pending composite is missing from its canonical action chain"));
        org.xar.ck3.control.contracts.StrictJson.require(parent.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal
                &&parent.command().operation().value().equals("continue-as-reconciled-successor")
                &&parent.bodySha256().equals(binding.parentBodySha256()),"recovery ACTION lost its original qualified Continue parent");
        var parentExecution=recoveryComposite(parent.state());
        boolean reserved=parentExecution.children().stream().anyMatch(child->child.actionId().equals(action.command().actionId())
                &&child.bodySha256().equals(action.bodySha256()));
        boolean nestedChild=false;
        if(!reserved)for(var outer:parentExecution.children()) {
            var life=org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(same.head().state(),outer.actionId(),originals)
                    .orElseThrow(()->new IOException("retained pending child reservation has no canonical command"));
            if(!life.command().operation().value().equals("life-advance"))continue;
            org.xar.ck3.control.contracts.StrictJson.require(life.bodySha256().equals(outer.bodySha256())
                    &&life.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay,
                    "retained date reservation changed its actual command/origin");
            var nested=recoveryComposite(life.state());
            org.xar.ck3.control.contracts.StrictJson.require(nested.children().size()<=3,"retained date ACTION ancestry exceeds the real bounded Life algorithm");
            if(nested.children().stream().anyMatch(child->child.actionId().equals(action.command().actionId())&&child.bodySha256().equals(action.bodySha256()))) {
                org.xar.ck3.control.contracts.StrictJson.require(action.command().source().equals(life.command().source())
                        &&action.command().sessionId().equals(life.command().sessionId())
                        &&!action.command().deadline().isAfter(life.command().deadline()),"retained date primitive crossed its actual parent source/session/deadline");
                org.xar.ck3.control.contracts.StrictJson.require(org.xar.ck3.control.application.advance.AdvancePrimitives.supports(action.command().operation()),"retained date reservation contains an unrelated action");
                reserved=true;nestedChild=true;break;
            }
        }
        if(!nestedChild) {
            String operation=action.command().operation().value();
            if(!operation.equals("continue-death-succession-modal-v1")&&!operation.equals("life-advance")) {
                org.xar.ck3.control.contracts.StrictJson.require(action.command().arguments().members().containsKey("pending_ui_event_source"),"retained original Continue contains an unrelated ACTION");
                org.xar.ck3.control.contracts.StrictJson.require(org.xar.ck3.control.application.effects.NativeEventEffects.supports(action.command().operation()),"retained event ACTION is outside the installed finite event family");
            }
        }
        org.xar.ck3.control.contracts.StrictJson.require(action.settled()
                &&reserved
                &&origin instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                &&action.command().before().game().equals(before.stamp().game())
                &&action.command().before().frame().episodeRunId().equals(binding.successorEpisodeRunId())
                &&action.command().before().frame().identity().player().equals(binding.successorCharacterId())
                &&action.command().source().equals(initial.terminalSnapshot().source())
                &&action.command().sessionId().equals(binding.predecessor().sessionId())
                &&published.command().equals(action.command())&&published.actionSequence()==action.sequence()
                &&published.beforeVersion()==before.stamp().driverVersion()
                &&published.afterVersion()==Math.addExact(before.stamp().driverVersion(),1)
                &&published.episodeEpoch()==before.stamp().episodeEpoch()
                &&java.util.Arrays.equals(originals.loadFullMaterial(published.beforeDriver()).bytes(),before.driver().encode())
                &&java.util.Arrays.equals(originals.loadFullMaterial(published.afterDriver()).bytes(),after.driver().encode()),
                "recovered ACTION is not the exact original new-subject full Driver transition");
        org.xar.ck3.control.contracts.StrictJson.require(after.stamp().driverVersion()==published.afterVersion()
                &&after.stamp().episodeEpoch()==before.stamp().episodeEpoch()&&after.stamp().game().equals(before.stamp().game())
                &&after.stamp().episodeRunId().equals(before.stamp().episodeRunId())
                &&after.driver().session().actorId().equals(before.driver().session().actorId())
                &&after.originalHistoryBasis().equals(before.originalHistoryBasis())&&after.auxiliary().equals(before.auxiliary())
                &&after.actionRows().size()==before.actionRows().size()+1&&after.actionRows().containsAll(before.actionRows()),
                "pending ACTION changed its canonical episode, obligation, history basis or other action coverage");
        var additions=after.actionRows().stream().filter(row->!before.actionRows().contains(row)).toList();
        org.xar.ck3.control.contracts.StrictJson.require(additions.size()==1,"exactly one actual ACTION coverage is required");
        var row=additions.getFirst();
        org.xar.ck3.control.contracts.StrictJson.require(row.actionId().equals(action.command().actionId())
                &&row.bodySha256().equals(action.bodySha256())&&row.durableSequence()==action.sequence(),"recovered ACTION coverage changed its exact receipt");
        if(published.legacyRow().isPresent()) {
            org.xar.ck3.control.contracts.StrictJson.require(row.coverageSource() instanceof DriverSnapshotFacts.LegacyHistoryRow
                    &&((DriverSnapshotFacts.LegacyHistoryRow)row.coverageSource()).originalRow().equals(published.legacyRow().orElseThrow())
                    &&((DriverSnapshotFacts.LegacyHistoryRow)row.coverageSource()).historyIndex()==after.driver().commandHistory().size(),
                    "recovered ACTION lost its actual compatible history row/index");
        } else org.xar.ck3.control.contracts.StrictJson.require(row.coverageSource() instanceof DriverSnapshotFacts.CanonicalOnly
                &&((DriverSnapshotFacts.CanonicalOnly)row.coverageSource()).originalSource().equals(published.originalSource()),
                "recovered canonical-only ACTION invented a compatible history row");
        return after;
    }
    private static org.xar.ck3.control.application.action.CompositeExecution recoveryComposite(
            org.xar.ck3.control.application.action.ActionState state) {
        if(state instanceof org.xar.ck3.control.application.action.ActionState.CompositeRunning running)return running.execution();
        if(state instanceof org.xar.ck3.control.application.action.ActionState.CompositeUnknown unknown)return unknown.execution();
        if(state instanceof org.xar.ck3.control.application.action.ActionState.CompositeSettled settled)return settled.execution();
        throw new IllegalArgumentException("actual retained composite reservation is required");
    }
    /** Ephemeral observation/loop DATA comes from the actual current owner, not from a historical permission. */
    private static void requireSameRecoveryState(DriverSnapshotFacts.Known expected,DriverSnapshotFacts.Known actual) {
        org.xar.ck3.control.contracts.StrictJson.require(expected.stamp().equals(actual.stamp())
                &&java.util.Arrays.equals(expected.driver().encode(),actual.driver().encode())
                &&expected.originalHistoryBasis().equals(actual.originalHistoryBasis())
                &&expected.actionRows().equals(actual.actionRows())&&expected.auxiliary().equals(actual.auxiliary()),
                "pending recovery is not the complete exact canonical Driver/history/obligation chain");
    }
}
