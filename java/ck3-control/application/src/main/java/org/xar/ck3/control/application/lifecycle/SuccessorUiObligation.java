package org.xar.ck3.control.application.lifecycle;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Durable DATA only. Private M3 qualification, actual canonical publication and current Root gates remain mandatory. */
public record SuccessorUiObligation(Binding binding,Phase phase,Optional<Observation> observation,
        Optional<CloseAttempt> closeAttempt,Optional<Rebind> rebind,Optional<Finalization> finalization) {
    public static final String SCHEMA="xar.java.successor-ui-obligation/v1";
    public static final String AUXILIARY_KEY="successor_ui_obligation";
    public static final int MAXIMUM_BYTES=262_144;
    public enum Phase { PENDING,OBSERVED,CLOSE_ENTERED,CLOSE_RESULT_RETAINED,FINALIZED }
    public enum UiState { CLEAR,CLOSE_REQUIRED,PLAYER_DECISION_PENDING,UNRESOLVED }
    public record Binding(LifecycleIdentity predecessor,BigInteger successorCharacterId,String successorEpisodeRunId,
            Optional<String> sourceEpochSha256,String causeDigest,String parentActionId,String parentBodySha256,
            ExactRef originalParentCommand,ExactRef preclockDocument,ExactRef qualifiedCause,Instant qualifiedAtUtc) {
        public Binding {
            Objects.requireNonNull(predecessor);NativeCharacterId.of(successorCharacterId);text(successorEpisodeRunId);
            sourceEpochSha256=Objects.requireNonNull(sourceEpochSha256);sourceEpochSha256.ifPresent(SuccessorUiObligation::digest);
            digest(causeDigest);text(parentActionId);digest(parentBodySha256);
            exact(originalParentCommand);exact(preclockDocument);exact(qualifiedCause);Objects.requireNonNull(qualifiedAtUtc);
            require(predecessor.terminalReason()==LifecycleIdentity.TerminalReason.CHANGED
                    &&predecessor.currentPlayer() instanceof LifecycleIdentity.Character current&&current.alive()
                    &&current.characterId().equals(successorCharacterId),"pending cause requires the actual changed living player");
            require(successorCharacterId.bitLength()<=31&&!successorEpisodeRunId.equals(predecessor.subject().episodeRunId()),"actual native successor and distinct new episode required");
            require(!qualifiedAtUtc.isBefore(predecessor.observedAt()),"pending cause observation time regressed");
        }
        public Binding(LifecycleIdentity predecessor,BigInteger successorCharacterId,String successorEpisodeRunId,
                String sourceEpochSha256,String causeDigest,String parentActionId,String parentBodySha256,
                ExactRef originalParentCommand,ExactRef preclockDocument,ExactRef qualifiedCause,Instant qualifiedAtUtc){
            this(predecessor,successorCharacterId,successorEpisodeRunId,Optional.of(sourceEpochSha256),causeDigest,parentActionId,parentBodySha256,originalParentCommand,preclockDocument,qualifiedCause,qualifiedAtUtc);
        }
        public long successorEpisodeEpoch(){return Math.addExact(predecessor.subject().episodeEpoch(),1);}
    }
    public record UiFrame(String machineId,GameGeneration game,String sessionId,BigInteger connectionGeneration,
            Optional<String> sourceEpochSha256,String snapshotId,BigInteger revision,BigInteger nativeRevision,BigInteger dateRaw,
            BigInteger actorCharacterId,String episodeRunId,long episodeEpoch,long driverVersion,ExactRef nativePacket,
            ExactRef semantic,ExactRef originalDriver,Optional<ExactRef> sourceQualification,Instant observedAtUtc) {
        public UiFrame {
            text(machineId);require(!machineId.equals("unknown"),"actual UI machine required");Objects.requireNonNull(game);text(sessionId);uint64(connectionGeneration,true);
            sourceEpochSha256=Objects.requireNonNull(sourceEpochSha256);sourceEpochSha256.ifPresent(SuccessorUiObligation::digest);
            text(snapshotId);uint64(revision,false);uint64(nativeRevision,true);Objects.requireNonNull(dateRaw);require(dateRaw.bitLength()<=31,"signed32 native UI date required");
            NativeCharacterId.of(actorCharacterId);text(episodeRunId);StrictJson.safe(episodeEpoch,0);StrictJson.safe(driverVersion,0);
            exact(nativePacket);exact(semantic);exact(originalDriver);sourceQualification=Objects.requireNonNull(sourceQualification);sourceQualification.ifPresent(SuccessorUiObligation::exact);Objects.requireNonNull(observedAtUtc);
        }
        public UiFrame(String machineId,GameGeneration game,String sessionId,BigInteger connectionGeneration,
                String sourceEpochSha256,String snapshotId,BigInteger revision,BigInteger nativeRevision,BigInteger dateRaw,
                BigInteger actorCharacterId,String episodeRunId,long episodeEpoch,long driverVersion,ExactRef nativePacket,
                ExactRef semantic,ExactRef originalDriver,ExactRef sourceQualification,Instant observedAtUtc){
            this(machineId,game,sessionId,connectionGeneration,Optional.of(sourceEpochSha256),snapshotId,revision,nativeRevision,dateRaw,actorCharacterId,episodeRunId,episodeEpoch,driverVersion,nativePacket,semantic,originalDriver,Optional.of(sourceQualification),observedAtUtc);
        }
    }
    public record Observation(UiFrame frame,UiState state,BigInteger querySequence,BigInteger observationRevision,
            ExactRef timelineRead,ExactRef timelineNativeFrame,Optional<BigInteger> eventInstanceId,Optional<ExactRef> eventRead) {
        public Observation {
            Objects.requireNonNull(frame);Objects.requireNonNull(state);positive(querySequence);positive(observationRevision);exact(timelineRead);exact(timelineNativeFrame);
            eventInstanceId=Objects.requireNonNull(eventInstanceId);eventRead=Objects.requireNonNull(eventRead);eventInstanceId.ifPresent(SuccessorUiObligation::positive);eventRead.ifPresent(SuccessorUiObligation::exact);
            require(eventInstanceId.isEmpty()||eventRead.isPresent(),"event instance requires its actual event read");
            require(state!=UiState.CLEAR||eventInstanceId.isEmpty(),"an actual event cannot become UI clear");
        }
    }
    public record ReadOnlyReconciliation(ExactRef originalUnknownReceipt,ExactRef confirmedReceipt,ExactRef sameOriginalActionProof,
            Optional<ExactRef> materialClearance,Optional<ExactRef> verifiedDateAdvance) {
        public ReadOnlyReconciliation {exact(originalUnknownReceipt);exact(confirmedReceipt);exact(sameOriginalActionProof);
            require(!originalUnknownReceipt.equals(confirmedReceipt),"read-only reconciliation must preserve both original and confirmed receipts");
            materialClearance=Objects.requireNonNull(materialClearance);verifiedDateAdvance=Objects.requireNonNull(verifiedDateAdvance);
            materialClearance.ifPresent(SuccessorUiObligation::exact);verifiedDateAdvance.ifPresent(SuccessorUiObligation::exact);
            require(verifiedDateAdvance.isEmpty()||materialClearance.isPresent(),"reconciled date proof requires actual clearance");}
    }
    public record CloseReceipt(ActionReceipt.Outcome outcome,ExactRef canonicalReceipt,Optional<ExactRef> materialClearance,
            Optional<ExactRef> verifiedDateAdvance,Optional<ReadOnlyReconciliation> reconciliation) {
        public CloseReceipt {
            Objects.requireNonNull(outcome);exact(canonicalReceipt);reconciliation=Objects.requireNonNull(reconciliation);materialClearance=Objects.requireNonNull(materialClearance);verifiedDateAdvance=Objects.requireNonNull(verifiedDateAdvance);
            materialClearance.ifPresent(SuccessorUiObligation::exact);verifiedDateAdvance.ifPresent(SuccessorUiObligation::exact);
            require(outcome==ActionReceipt.Outcome.APPLIED_CONFIRMED||materialClearance.isEmpty()&&verifiedDateAdvance.isEmpty(),"UNKNOWN/ACK cannot claim native clearance or game days");
            require(verifiedDateAdvance.isEmpty()||materialClearance.isPresent(),"date proof requires actual independent clearance");
            if(reconciliation.isPresent())require(outcome==ActionReceipt.Outcome.UNRESOLVED&&reconciliation.orElseThrow().originalUnknownReceipt().equals(canonicalReceipt),"only the identical original UNKNOWN may gain read-only reconciliation");
        }
        public ActionReceipt.Outcome effectiveOutcome(){return reconciliation.isPresent()?ActionReceipt.Outcome.APPLIED_CONFIRMED:outcome;}
        public ExactRef effectiveReceipt(){return reconciliation.map(ReadOnlyReconciliation::confirmedReceipt).orElse(canonicalReceipt);}
        public Optional<ExactRef> effectiveMaterialClearance(){return reconciliation.isPresent()?reconciliation.orElseThrow().materialClearance():materialClearance;}
        public Optional<ExactRef> effectiveDateAdvance(){return reconciliation.isPresent()?reconciliation.orElseThrow().verifiedDateAdvance():verifiedDateAdvance;}
    }
    public record CloseAttempt(String actionId,String commandBodySha256,ExactRef originalCommand,UiFrame before,
            Instant enteredAtUtc,Optional<CloseReceipt> receipt) {
        public CloseAttempt {text(actionId);digest(commandBodySha256);exact(originalCommand);Objects.requireNonNull(before);Objects.requireNonNull(enteredAtUtc);receipt=Objects.requireNonNull(receipt);
            require(!enteredAtUtc.isBefore(before.observedAtUtc()),"Close intent predates its original actual frame");}
    }
    public record Rebind(Optional<UiFrame> retainedObservation,Optional<Binding> retainedPending,UiFrame resumed,ExactRef priorCanonicalObligation,ExactRef actualPrivateRebindProof) {
        public Rebind(UiFrame retained,UiFrame resumed,ExactRef priorCanonicalObligation,ExactRef actualPrivateRebindProof){
            this(Optional.of(retained),Optional.empty(),resumed,priorCanonicalObligation,actualPrivateRebindProof);
        }
        public static Rebind unobserved(Binding original,UiFrame resumed,ExactRef priorCanonicalObligation,ExactRef actualPrivateRebindProof){
            return new Rebind(Optional.empty(),Optional.of(original),resumed,priorCanonicalObligation,actualPrivateRebindProof);
        }
        /** Only the observed variant has an actual retained UI frame. */
        public UiFrame retained(){require(retainedObservation.isPresent(),"unobserved pending binding has no retained UI observation");return retainedObservation.orElseThrow();}
        public Rebind {Objects.requireNonNull(retainedObservation);Objects.requireNonNull(retainedPending);Objects.requireNonNull(resumed);exact(priorCanonicalObligation);exact(actualPrivateRebindProof);
            require(retainedObservation.isPresent()!=retainedPending.isPresent(),"exactly one original retained pending variant is required");
            if(retainedObservation.isPresent()){var retained=retainedObservation.orElseThrow();
            require(retained.machineId().equals(resumed.machineId())&&retained.game().equals(resumed.game())
                    &&sameOptionalEpoch(retained.sourceEpochSha256(),resumed.sourceEpochSha256())&&retained.actorCharacterId().equals(resumed.actorCharacterId())
                    &&retained.episodeRunId().equals(resumed.episodeRunId())&&retained.episodeEpoch()==resumed.episodeEpoch(),"reconnect cannot become a new Game/source/actor/episode");
            require(!retained.sessionId().equals(resumed.sessionId())||!retained.connectionGeneration().equals(resumed.connectionGeneration()),"rebind requires an actual new connection/session");
            physicalMonotonic(retained,resumed);
            }else{var original=retainedPending.orElseThrow();var old=original.predecessor();requireSubject(original,resumed);
                require(!old.sessionId().equals(resumed.sessionId())||!old.connectionGeneration().equals(resumed.connectionGeneration()),"unobserved rebind requires an actual new transport");
                require(resumed.nativeRevision().compareTo(old.frame().nativeRevision())>=0&&resumed.dateRaw().compareTo(old.frame().dateRaw())>=0
                        &&!resumed.observedAtUtc().isBefore(original.qualifiedAtUtc()),"unobserved pending continuation regressed its actual original native/date/time");
            }}
    }
    public record Finalization(String causeDigest,ExactRef finalM3Proof,UiFrame current,Optional<ExactRef> actualCloseReceipt,
            Optional<ExactRef> verifiedDateAdvance,Instant finalizedAtUtc,Optional<ExactRef> continuityBinding) {
        public Finalization(String causeDigest,ExactRef finalM3Proof,UiFrame current,Optional<ExactRef> actualCloseReceipt,
                Optional<ExactRef> verifiedDateAdvance,Instant finalizedAtUtc){this(causeDigest,finalM3Proof,current,actualCloseReceipt,verifiedDateAdvance,finalizedAtUtc,Optional.empty());}
        public Finalization {digest(causeDigest);exact(finalM3Proof);Objects.requireNonNull(current);actualCloseReceipt=Objects.requireNonNull(actualCloseReceipt);verifiedDateAdvance=Objects.requireNonNull(verifiedDateAdvance);
            continuityBinding=Objects.requireNonNull(continuityBinding);continuityBinding.ifPresent(SuccessorUiObligation::exact);
            actualCloseReceipt.ifPresent(SuccessorUiObligation::exact);verifiedDateAdvance.ifPresent(SuccessorUiObligation::exact);Objects.requireNonNull(finalizedAtUtc);
            require(!finalizedAtUtc.isBefore(current.observedAtUtc()),"final M3 time regressed");}
    }
    public SuccessorUiObligation {
        Objects.requireNonNull(binding);Objects.requireNonNull(phase);observation=Objects.requireNonNull(observation);closeAttempt=Objects.requireNonNull(closeAttempt);rebind=Objects.requireNonNull(rebind);finalization=Objects.requireNonNull(finalization);
        require(phase!=Phase.PENDING||rebind.isEmpty()||rebind.orElseThrow().retainedPending().filter(binding::equals).isPresent(),"unobserved rebind must retain its exact canonical original binding");
        rebind.ifPresent(value->{value.retainedObservation().ifPresent(frame->requireSubject(binding,frame));value.retainedPending().ifPresent(original->require(original.equals(binding),"unobserved retained cause binding changed"));requireSubject(binding,value.resumed());});
        require((phase==Phase.PENDING)==observation.isEmpty(),"pending/observed UI phase differs from original observation presence");
        require((phase==Phase.CLOSE_ENTERED||phase==Phase.CLOSE_RESULT_RETAINED)==(closeAttempt.isPresent()&&finalization.isEmpty()),"Close state must retain its once intent");
        require((phase==Phase.FINALIZED)==finalization.isPresent(),"final UI state requires its actual finalization proof");
        if(observation.isPresent()) {
            UiFrame frame=observation.orElseThrow().frame();
            if(rebind.isPresent()&&rebind.orElseThrow().retainedObservation().filter(frame::equals).isPresent())requireSubject(binding,frame);
            else requireFrame(binding,frame,rebind);
        }
        if(closeAttempt.isPresent()) {
            var close=closeAttempt.orElseThrow();
            requireSubject(binding,close.before());
            require(phase!=Phase.CLOSE_ENTERED||close.receipt().isEmpty(),"entered Close cannot already have a result");
            require(phase!=Phase.CLOSE_RESULT_RETAINED||close.receipt().isPresent(),"retained Close result is absent");
        }
        if(finalization.isPresent()) {
            var done=finalization.orElseThrow();var observed=observation.orElseThrow();requireFrame(binding,done.current(),rebind);
            require(done.causeDigest().equals(binding.causeDigest())&&observed.state()==UiState.CLEAR&&done.current().equals(observed.frame()),"final UI proof differs from actual clear observation/cause");
            if(closeAttempt.isPresent()){require(closeAttempt.orElseThrow().receipt().isPresent(),"final Close receipt missing");var close=closeAttempt.orElseThrow().receipt().orElseThrow();require(close.effectiveOutcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    &&close.effectiveMaterialClearance().isPresent()&&close.effectiveDateAdvance().isPresent()
                    &&done.current().dateRaw().compareTo(closeAttempt.orElseThrow().before().dateRaw())>0
                    &&done.actualCloseReceipt().equals(Optional.of(close.effectiveReceipt()))&&done.verifiedDateAdvance().equals(close.effectiveDateAdvance()),"Close finalization lacks its original material/date proofs");}
            else require(done.actualCloseReceipt().isEmpty()&&done.verifiedDateAdvance().isEmpty(),"already-clear route cannot invent a Close or game days");
        }
    }
    public boolean blocksOrdinaryActionsAndSave(){return phase!=Phase.FINALIZED;}
    /** Classification only; actual Root/private canonical intent remains mandatory. */
    public boolean closeCanBeConsidered(){return phase==Phase.OBSERVED&&observation.orElseThrow().state()==UiState.CLOSE_REQUIRED&&closeAttempt.isEmpty()
            &&rebind.map(value->observation.orElseThrow().frame().sessionId().equals(value.resumed().sessionId())
                    &&observation.orElseThrow().frame().connectionGeneration().equals(value.resumed().connectionGeneration())).orElse(true);}
    static void requireFrame(Binding binding,UiFrame frame,Optional<Rebind> rebind) {
        var old=binding.predecessor();String session=rebind.map(v->v.resumed().sessionId()).orElse(old.sessionId());BigInteger connection=rebind.map(v->v.resumed().connectionGeneration()).orElse(old.connectionGeneration());
        require(frame.sessionId().equals(session)&&frame.connectionGeneration().equals(connection),"UI observation lost actual current connection");
        requireSubject(binding,frame);
    }
    static void requireSubject(Binding binding,UiFrame frame) {
        var old=binding.predecessor();
        require(frame.machineId().equals(old.machineId())&&frame.game().equals(old.game())&&sameOptionalEpoch(frame.sourceEpochSha256(),binding.sourceEpochSha256())&&frame.actorCharacterId().equals(binding.successorCharacterId())
                &&frame.episodeRunId().equals(binding.successorEpisodeRunId())&&frame.episodeEpoch()==binding.successorEpisodeEpoch()
                &&frame.driverVersion()>old.subject().driverVersion(),"UI observation is not the actual published same-Game new successor episode");
    }
    static void monotonic(UiFrame old,UiFrame next){require(next.revision().compareTo(old.revision())>=0&&next.nativeRevision().compareTo(old.nativeRevision())>=0
            &&next.dateRaw().compareTo(old.dateRaw())>=0&&next.driverVersion()>=old.driverVersion()&&!next.observedAtUtc().isBefore(old.observedAtUtc()),"UI frame/source progression regressed");}
    static void physicalMonotonic(UiFrame old,UiFrame next){require(next.nativeRevision().compareTo(old.nativeRevision())>=0&&next.dateRaw().compareTo(old.dateRaw())>=0
            &&next.driverVersion()>=old.driverVersion()&&!next.observedAtUtc().isBefore(old.observedAtUtc()),"same physical UI frame/source progression regressed");}
    static void exact(ExactRef value){Objects.requireNonNull(value);require(value.bytes()>0,"actual nonempty UI original source required");}
    static boolean sameOptionalEpoch(Optional<String> left,Optional<String> right){return left.isEmpty()||right.isEmpty()||left.equals(right);}
    static void digest(String value){require(value!=null&&value.matches("[0-9a-f]{64}"),"exact UI SHA256 required");}
    static void text(String value){StrictJson.text(value);require(!value.isBlank(),"nonblank UI identity required");}
    static void positive(BigInteger value){require(value!=null&&value.signum()>0,"positive exact UI integer required");}
    static void uint64(BigInteger value,boolean positive){require(value!=null&&value.signum()>=(positive?1:0)&&value.bitLength()<=64,"exact UI uint64 required");}
}
