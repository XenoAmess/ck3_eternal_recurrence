package org.xar.ck3.control.application.lifecycle;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.util.Objects;
import java.util.List;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import java.util.Optional;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.*;

/** Deterministic DATA reducer. The actual writer must revalidate and commit its sole current predecessor before every effect. */
public final class SuccessorUiObligationReducer {
    private SuccessorUiObligationReducer(){ }
    public static SuccessorUiObligation pending(Binding actualQualifiedCause) {
        return new SuccessorUiObligation(actualQualifiedCause,Phase.PENDING,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
    }
    public record PendingEpisode(DriverStateSnapshot.Complete driver,OpportunityJson.Obj auxiliary,SuccessorUiObligation obligation) {
        public PendingEpisode {Objects.requireNonNull(driver);Objects.requireNonNull(auxiliary);Objects.requireNonNull(obligation);}
    }
    /** Pre-final DATA projection only: preserve the original goal and defer every final continuation credit. */
    public static PendingEpisode pendingEpisode(LifecycleObservationPort.Snapshot actual,Binding binding) {
        Objects.requireNonNull(actual);Objects.requireNonNull(binding);var origin=binding.predecessor();var old=actual.facts().driver();
        require(actual.actual().session().machineId().equals(origin.machineId())&&actual.actual().session().game().equals(origin.game())
                &&actual.actual().session().sessionId().equals(origin.sessionId())&&actual.actual().session().connectionGeneration().equals(origin.connectionGeneration())
                &&actual.facts().stamp().episodeEpoch()==origin.subject().episodeEpoch()&&actual.facts().stamp().driverVersion()==origin.subject().driverVersion()
                &&old.session().actorId().equals(origin.subject().characterId())&&old.session().episodeRunId().equals(origin.subject().episodeRunId())
                &&actual.revision().equals(origin.frame().revision())&&actual.actual().nativeRevision().equals(origin.frame().nativeRevision())
                &&actual.actual().snapshotId().equals(origin.frame().snapshotId())&&actual.dateRaw().equals(origin.frame().dateRaw())
                &&actual.originalEvidence().equals(origin.nativeEvidence())&&actual.paused()&&actual.mapReady(),"pending projection lost its actual qualified terminal predecessor");
        require(LifecycleReducer.lifecycle(old).equals("ordinary_campaign_succession"),"pending UI is only original ordinary campaign succession");
        var semantic=actual.semantic();require(OpportunityJson.text(semantic.get("one_life_terminal_reason"),"terminal reason").equals("played_character_changed"),"changed-player terminal required");
        var player=OpportunityJson.object(semantic.get("played_character"),"actual changed player");
        require(OpportunityJson.bool(player.get("alive"),"alive")&&OpportunityJson.integer(player.get("character_id"),"character_id").equals(binding.successorCharacterId()),"pending successor differs from actual living native player");
        var obligation=pending(binding);var auxiliary=LifecycleReducer.clearEpisodeCaches(actual.facts().auxiliary());
        auxiliary=auxiliary.with("succession_reconciliation",OpportunityJson.Nil.INSTANCE);
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(old.session().pipeName(),old.session().bridgePid(),binding.successorCharacterId(),binding.successorEpisodeRunId()),List.of(),
                new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),old.successionLifecycle(),old.campaignGoal(),
                new DriverStateSnapshot.Value("[]".getBytes(java.nio.charset.StandardCharsets.US_ASCII)));
        return new PendingEpisode(driver,withState(auxiliary,obligation),obligation);
    }
    public static OpportunityJson.Obj withState(OpportunityJson.Obj original,SuccessorUiObligation actual) {
        Objects.requireNonNull(original);Objects.requireNonNull(actual);
        return original.with(SuccessorUiObligation.AUXILIARY_KEY,OpportunityJson.parse(SuccessorUiObligationCodec.encode(actual)))
                .with("episode_binding_state",new OpportunityJson.Text(actual.blocksOrdinaryActionsAndSave()?"successor_ui_pending":"active_natural_successor"));
    }
    public static SuccessorUiObligation observe(SuccessorUiObligation before,Observation actual) {
        Objects.requireNonNull(before);Objects.requireNonNull(actual);require(before.phase()!=Phase.FINALIZED,"completed UI obligation cannot be reopened");
        SuccessorUiObligation.requireFrame(before.binding(),actual.frame(),before.rebind());
        if(before.observation().isPresent()) {
            var old=before.observation().orElseThrow();
            boolean sameConnection=old.frame().sessionId().equals(actual.frame().sessionId())&&old.frame().connectionGeneration().equals(actual.frame().connectionGeneration());
            if(sameConnection){SuccessorUiObligation.monotonic(old.frame(),actual.frame());
                require(actual.querySequence().compareTo(old.querySequence())>0&&actual.observationRevision().compareTo(old.observationRevision())>0,"UI observation repeated/regressed its actual native query");}
            else {require(before.rebind().isPresent()&&before.rebind().orElseThrow().retainedObservation().filter(old.frame()::equals).isPresent(),"UI query has no actual retained connection rebind");
                SuccessorUiObligation.physicalMonotonic(old.frame(),actual.frame());SuccessorUiObligation.monotonic(before.rebind().orElseThrow().resumed(),actual.frame());}
        }
        var phase=before.closeAttempt().isPresent()?before.phase():Phase.OBSERVED;
        return new SuccessorUiObligation(before.binding(),phase,Optional.of(actual),before.closeAttempt(),before.rebind(),Optional.empty());
    }
    /** Must be canonically committed before entering the actual native Close. An exception/ACK/UNKNOWN never resets it. */
    public static SuccessorUiObligation enterClose(SuccessorUiObligation before,CloseAttempt originalIntent) {
        Objects.requireNonNull(before);Objects.requireNonNull(originalIntent);require(before.closeCanBeConsidered(),"UI has no new legal once-only Close candidate");
        require(originalIntent.receipt().isEmpty()&&originalIntent.before().equals(before.observation().orElseThrow().frame()),"Close intent differs from actual current observed frame");
        return new SuccessorUiObligation(before.binding(),Phase.CLOSE_ENTERED,before.observation(),Optional.of(originalIntent),before.rebind(),Optional.empty());
    }
    public static SuccessorUiObligation retainCloseReceipt(SuccessorUiObligation before,CloseReceipt original) {
        Objects.requireNonNull(before);Objects.requireNonNull(original);require(before.phase()==Phase.CLOSE_ENTERED,"Close receipt requires its actual retained once intent");
        var intent=before.closeAttempt().orElseThrow();require(intent.receipt().isEmpty(),"original Close receipt already retained");
        var retained=new CloseAttempt(intent.actionId(),intent.commandBodySha256(),intent.originalCommand(),intent.before(),intent.enteredAtUtc(),Optional.of(original));
        return new SuccessorUiObligation(before.binding(),Phase.CLOSE_RESULT_RETAINED,before.observation(),Optional.of(retained),before.rebind(),Optional.empty());
    }
    /** Add independent postconditions to the identical canonical receipt; never replace UNKNOWN with a claimed result. */
    public static SuccessorUiObligation retainClosePostconditions(SuccessorUiObligation before,CloseReceipt verifiedOriginal) {
        Objects.requireNonNull(before);Objects.requireNonNull(verifiedOriginal);require(before.phase()==Phase.CLOSE_RESULT_RETAINED,"actual Close result unavailable");
        var intent=before.closeAttempt().orElseThrow();var previous=intent.receipt().orElseThrow();
        require(previous.outcome()==org.xar.ck3.control.application.action.ActionReceipt.Outcome.APPLIED_CONFIRMED
                &&verifiedOriginal.outcome()==previous.outcome()&&verifiedOriginal.canonicalReceipt().equals(previous.canonicalReceipt()),"postconditions cannot replace the original UNKNOWN/outcome/receipt");
        previous.materialClearance().ifPresent(value->require(verifiedOriginal.materialClearance().equals(Optional.of(value)),"material clearance original changed"));
        previous.verifiedDateAdvance().ifPresent(value->require(verifiedOriginal.verifiedDateAdvance().equals(Optional.of(value)),"date proof original changed"));
        var retained=new CloseAttempt(intent.actionId(),intent.commandBodySha256(),intent.originalCommand(),intent.before(),intent.enteredAtUtc(),Optional.of(verifiedOriginal));
        return new SuccessorUiObligation(before.binding(),before.phase(),before.observation(),Optional.of(retained),before.rebind(),Optional.empty());
    }
    /** Reconciliation is read-only evidence for the same original action; original UNKNOWN is never erased or retried. */
    public static SuccessorUiObligation retainVerifiedReconciliation(SuccessorUiObligation before,ReadOnlyReconciliation actual) {
        Objects.requireNonNull(before);Objects.requireNonNull(actual);require(before.phase()==Phase.CLOSE_RESULT_RETAINED,"actual retained Close result required");
        var intent=before.closeAttempt().orElseThrow();var original=intent.receipt().orElseThrow();
        require(original.outcome()==org.xar.ck3.control.application.action.ActionReceipt.Outcome.UNRESOLVED
                &&actual.originalUnknownReceipt().equals(original.canonicalReceipt()),"reconciliation changed the original UNKNOWN action");
        original.reconciliation().ifPresent(previous->{require(previous.confirmedReceipt().equals(actual.confirmedReceipt())&&previous.sameOriginalActionProof().equals(actual.sameOriginalActionProof()),"confirmed canonical reconciliation lineage changed");
            previous.materialClearance().ifPresent(value->require(actual.materialClearance().equals(Optional.of(value)),"reconciled material original changed"));
            previous.verifiedDateAdvance().ifPresent(value->require(actual.verifiedDateAdvance().equals(Optional.of(value)),"reconciled date original changed"));});
        var receipt=new CloseReceipt(original.outcome(),original.canonicalReceipt(),original.materialClearance(),original.verifiedDateAdvance(),Optional.of(actual));
        var retained=new CloseAttempt(intent.actionId(),intent.commandBodySha256(),intent.originalCommand(),intent.before(),intent.enteredAtUtc(),Optional.of(receipt));
        return new SuccessorUiObligation(before.binding(),before.phase(),before.observation(),Optional.of(retained),before.rebind(),Optional.empty());
    }
    /** The private Root rebind must prove the retained canonical predecessor and actual same physical Game/new connection. */
    public static SuccessorUiObligation rebind(SuccessorUiObligation before,Rebind actual) {
        Objects.requireNonNull(before);Objects.requireNonNull(actual);require(before.phase()!=Phase.FINALIZED,"finalized metadata cannot issue another pending UI rebind");
        if(before.observation().isEmpty())require(before.phase()==Phase.PENDING&&actual.retainedPending().filter(before.binding()::equals).isPresent(),"unobserved reconnect must retain its exact canonical cause binding");
        else{
            require(actual.retainedObservation().filter(before.observation().orElseThrow().frame()::equals).isPresent(),"reconnect lost its original observed frame");
            if(before.rebind().flatMap(Rebind::retainedObservation).filter(actual.retained()::equals).isPresent())SuccessorUiObligation.requireSubject(before.binding(),actual.retained());
            else SuccessorUiObligation.requireFrame(before.binding(),actual.retained(),before.rebind());
        }
        if(before.rebind().isPresent()){
            var previous=before.rebind().orElseThrow().resumed();var current=actual.resumed();
            require(!previous.sessionId().equals(current.sessionId())||!previous.connectionGeneration().equals(current.connectionGeneration()),"pending rebind cannot repeat its already canonical transport");
            SuccessorUiObligation.physicalMonotonic(previous,current);
        }
        return new SuccessorUiObligation(before.binding(),before.phase(),before.observation(),before.closeAttempt(),Optional.of(actual),Optional.empty());
    }
    /** Pure final DATA projection. The actual Root mutation source must prove genuine private M3 Finalized. */
    public static LifecycleReducer.Reduction finalEpisode(org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known current,
            SuccessorUiObligation before,Finalization actual,org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot currentFrame,
            org.xar.ck3.control.application.action.RawJson actualMatchedEstate,java.time.Instant at) {
        return LifecycleReducer.finalizePendingSuccessor(current,before,finalizeVerified(before,actual),currentFrame,actualMatchedEstate,at);
    }
    /** Only the genuine M3 finalization and actual publication consumer can use this DATA result to lift the Root gate. */
    public static SuccessorUiObligation finalizeVerified(SuccessorUiObligation before,Finalization actual) {
        Objects.requireNonNull(before);Objects.requireNonNull(actual);require(before.phase()!=Phase.FINALIZED,"original UI was already finalized");
        require(before.observation().isPresent()&&before.observation().orElseThrow().state()==UiState.CLEAR,"actual current UI clearance required");
        return new SuccessorUiObligation(before.binding(),Phase.FINALIZED,before.observation(),before.closeAttempt(),before.rebind(),Optional.of(actual));
    }
}
