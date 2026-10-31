package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real selected Finish producer. It never submits or writes pending state; Root alone executes its decision. */
public final class SwaySelectedFinish {
    public record Request(BigInteger expectedRevision,long targetCharacterId,long schemeInstanceId,int schemeInstanceGeneration) {
        public Request {
            SwayNativeWire.u64(expectedRevision,1); SwayNativeWire.actionCharacter(targetCharacterId);
            SwayNativeWire.instance(schemeInstanceId,schemeInstanceGeneration);
        }
    }
    public sealed interface Decision permits NewStop,ExistingStop,Retained { }
    public record NewStop(ActionCommand command,List<ExactRef> evidence) implements Decision {
        public NewStop { Objects.requireNonNull(command); evidence=List.copyOf(evidence); require(command.operation().value().equals(SwayNativeWire.STOP)&&evidence.size()==3,"selected Stop needs its three original guarded reads"); }
    }
    public record ExistingStop(String actionId,ExactRef canonicalReceipt) implements Decision {
        public ExistingStop { SwayNativeWire.action(actionId,true); Objects.requireNonNull(canonicalReceipt); }
    }
    public enum Reason { NO_ORIGINAL_EPISODE, START_PENDING_RECOVERY, CURRENT_SOURCE_UNAVAILABLE, RETAIN_EXISTING_SWAY, ORIGINAL_STOP_RECEIPT_UNAVAILABLE, ORIGINAL_REDUCER_DECLINED }
    public record Retained(Reason reason,String detail,List<ExactRef> evidence) implements Decision {
        public Retained { Objects.requireNonNull(reason); Objects.requireNonNull(detail); require(!detail.isBlank(),"explicit Finish disposition required"); evidence=List.copyOf(evidence); }
    }
    private final SwayCanonicalDomain domain;
    private final ActionPorts.OutcomeArchive archive;
    private final PlanningReadPort reads;
    private final SwayActionLifecycle.RegisteredReads definitions;
    private final Supplier<String> actionIds;
    public SwaySelectedFinish(SwayCanonicalDomain domain,ActionPorts.OutcomeArchive archive,PlanningReadPort reads,
            SwayActionLifecycle.RegisteredReads definitions,Supplier<String> actionIds) {
        this.domain=Objects.requireNonNull(domain);this.archive=Objects.requireNonNull(archive);this.reads=Objects.requireNonNull(reads);
        this.definitions=Objects.requireNonNull(definitions);this.actionIds=Objects.requireNonNull(actionIds);
    }
    /** Caller must retain the actual currentOwned frame/Driver freeze and original borrowed writer through all three reads. */
    public Decision prepare(ContinuityStorePort.Session session,SwayActionLifecycle.View current,Request request)throws IOException {
        Objects.requireNonNull(session);Objects.requireNonNull(current);Objects.requireNonNull(request);
        require(current.before().frame().revision().equals(request.expectedRevision()),"selected Sway Finish expected public revision is stale");
        var originals=archive.withSession(session);var loaded=domain.load(session);var ledger=loaded.ledger();
        if(ledger.pending().isPresent())return retained(Reason.START_PENDING_RECOVERY,"original Start remains pending; Finish creates no new action",List.of());
        if(ledger.resolved().isEmpty())return retained(Reason.NO_ORIGINAL_EPISODE,"selected Finish requires its actual original resolved episode",List.of());
        var episode=ledger.resolved().orElseThrow();var identity=episode.identity();
        require(identity.targetCharacterId()==request.targetCharacterId()&&identity.schemeInstanceId()==request.schemeInstanceId()
                &&identity.schemeInstanceGeneration()==request.schemeInstanceGeneration(),"selected Finish differs from original target/full instance");
        require(identity.actorCharacterId()==current.before().frame().identity().player().longValueExact()
                &&ledger.machineId().equals(current.before().machineId())&&ledger.episodeRunId().equals(current.before().frame().episodeRunId()),"selected Finish crossed original actor/episode");
        if(!episode.lifecycle().origin().game().equals(current.before().game()))return retained(Reason.CURRENT_SOURCE_UNAVAILABLE,"original episode needs its actual source-bound restoration before current-Game Finish",List.of());
        if(episode.stop().isPresent()) {
            String originalId=episode.stop().orElseThrow().actionId();var actual=ContinuityActionJournal.lookup(session.head().state(),originalId,originals);
            if(actual.isEmpty())return retained(Reason.ORIGINAL_STOP_RECEIPT_UNAVAILABLE,"original Stop intent is retained without a canonical action receipt; never resubmit it",List.of());
            var receipt=actual.orElseThrow();var command=receipt.command();
            require(command.operation().value().equals(SwayNativeWire.STOP)&&command.before().game().equals(current.before().game())
                    &&command.source().equals(current.source())&&command.sessionId().equals(current.sessionId()),"retained Stop canonical source/session differs");
            var fields=SwayNativeBindings.args(command.arguments(),Set.of("schema","original_action_id","target_character_id","scheme_instance_id","scheme_instance_generation","original_target_read","completion_read","opinion_read"));
            SwayNativeWire.equals(fields,"schema",SwayNativeBindings.STOP_ARGUMENTS);
            SwayNativeWire.equals(fields,"original_action_id",identity.actionId());
            require(NativeCharacterId.fromJson(fields.get("target_character_id")).value()==identity.targetCharacterId()
                    &&SwayNativeWire.integer(fields,"scheme_instance_id",0,0xffff_fffeL)==identity.schemeInstanceId()
                    &&SwayNativeWire.integer(fields,"scheme_instance_generation",0,255)==identity.schemeInstanceGeneration(),"retained Stop command changed original full identity");
            return new ExistingStop(originalId,originals.receiptReferenceOf(receipt));
        }
        var refs=new ArrayList<ExactRef>();var targetResult=read(session,definitions.target(identity.targetCharacterId()),current,arguments(identity.targetCharacterId(),Optional.empty()));
        if(!(targetResult instanceof PlanningReadResult.Known<SwayNativeWire.TargetRead> target))return retained(Reason.CURRENT_SOURCE_UNAVAILABLE,"actual current target quote unavailable",refs);
        refs.add(originals.readReferenceOf(target.receipt()));
        var completionResult=read(session,definitions.plane(SwayObservationReads.Kind.COMPLETION,identity),current,arguments(identity.targetCharacterId(),Optional.of(identity.schemeInstanceId())));
        if(!(completionResult instanceof PlanningReadResult.Known<SwayObservationReads.Plane> completion))return retained(Reason.CURRENT_SOURCE_UNAVAILABLE,"actual original full-instance completion read unavailable",refs);
        refs.add(originals.readReferenceOf(completion.receipt()));
        var opinionResult=read(session,definitions.plane(SwayObservationReads.Kind.OPINION,identity),current,arguments(identity.targetCharacterId(),Optional.empty()));
        if(!(opinionResult instanceof PlanningReadResult.Known<SwayObservationReads.Plane> opinion))return retained(Reason.CURRENT_SOURCE_UNAVAILABLE,"actual independent named benefit read unavailable",refs);
        refs.add(originals.readReferenceOf(opinion.receipt()));
        for(var original:List.of(target.receipt(),completion.receipt(),opinion.receipt())) {
            NativeRecordedEvidenceVerifier.requireRead(original,originals);
            require(original.request().before().equals(current.before())&&original.request().source().equals(current.source())
                    &&original.request().sessionId().equals(current.sessionId()),"Finish source reads do not share the actual current frame/source/session");
        }
        var observed=SwayLifecycle.observe(episode.lifecycle(),SwayFormalCodec.m6Episode(episode),
                new M6TerminalSourceComposition.Inputs(Optional.of(completion.value().normalized()),Optional.empty(),Optional.empty(),Optional.of(opinion.value().normalized())),current.before());
        var staged=SwayFormalState.reduce(ledger,new SwayFormalState.LifecycleObserved(observed));
        if(!SwayLifecycle.mayFinish(observed,current.before(),target.value().targetOpinion()))return retained(Reason.RETAIN_EXISTING_SWAY,"exact active original and current positive named benefit do not yet admit Finish",refs);
        try { SwayFormalState.requireStopEligible(staged,target.value()); }
        catch(IllegalArgumentException declined) {return retained(Reason.ORIGINAL_REDUCER_DECLINED,declined.getMessage()==null?"original source reducer declined new Stop":declined.getMessage(),refs);}
        // ID is allocated only after actual eligibility; pending/reconciliation paths never allocate another ID.
        String actionId=Objects.requireNonNull(actionIds.get());SwayNativeWire.action(actionId,true);
        var row=StrictJson.object();row.put("schema",SwayNativeBindings.STOP_ARGUMENTS);row.put("original_action_id",identity.actionId());
        row.put("target_character_id",identity.targetCharacterId());row.put("scheme_instance_id",identity.schemeInstanceId());row.put("scheme_instance_generation",identity.schemeInstanceGeneration());
        row.set("original_target_read",refs.get(0).toJson());row.set("completion_read",refs.get(1).toJson());row.set("opinion_read",refs.get(2).toJson());
        var expected=new ExpectedPostcondition(1,current.before(),current.source(),SwayActionLifecycle.STOP_OBSERVER,SwayActionLifecycle.values(episode,actionId,true));
        var claims=new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(BigInteger.valueOf(identity.actorCharacterId()),BigInteger.valueOf(identity.targetCharacterId())),Set.of("sway:"+identity.schemeInstanceId()));
        var command=new ActionCommand(actionId,current.before(),current.source(),current.sessionId(),new OperationKey(SwayNativeWire.STOP),
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"selected Sway Finish arguments"),expected,claims,current.deadline());
        return new NewStop(command,refs);
    }
    private static Retained retained(Reason reason,String detail,List<ExactRef> refs){return new Retained(reason,detail,refs);}
    private <T> PlanningReadResult<T> read(ContinuityStorePort.Session session,ReadContract<T> contract,SwayActionLifecycle.View current,OpportunityJson.Obj arguments) {
        return reads.read(session,contract,new PlanningReadRequest(current.before(),current.source(),current.sessionId(),contract.operation(),arguments,current.deadline()));
    }
    private static OpportunityJson.Obj arguments(long target,Optional<Long> instance) {
        ObjectNode row=StrictJson.object();row.put("target_character_id",target);instance.ifPresent(value->row.put("scheme_instance_id",value.longValue()));
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"selected Finish native read arguments");
    }
}
