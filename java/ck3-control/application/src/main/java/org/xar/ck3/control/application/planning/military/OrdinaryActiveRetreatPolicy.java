package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal.*;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Normal ordinary stage. Reads and once-only execution are bound by Root to the one coordinator/writer. */
public final class OrdinaryActiveRetreatPolicy implements OrdinaryPolicy {
    public static final String PREVIEW="ordinary-active-retreat-preview-v1",ORDER="ordinary-active-retreat-order-v1",POST="ordinary-active-retreat-observe-v1",FIELD="ordinary_active_retreat_v1";
    private static final Set<String> PHASES=Set.of("native_war_global_battle_control_progress","native_war_global_battle_decision_epoch","native_war_global_battle_terminal_cruise");
    private static final Set<String> REQUIRED_CAPABILITIES=Set.of("game.command.query-battle-control-snapshot-v1-N","game.command.preview-move-army-N-to-N","game.command.move-army-N-to-N");
    public sealed interface DomainRead permits KnownDomain,UnavailableDomain {}
    public record KnownDomain(ObservationIdentity before,State state) implements DomainRead {public KnownDomain {Objects.requireNonNull(before);Objects.requireNonNull(state);}}
    public record UnavailableDomain(String reason) implements DomainRead {public UnavailableDomain {Objects.requireNonNull(reason);}}
    @FunctionalInterface public interface StateReader {DomainRead read(PlanningRequest request);}
    public sealed interface CurrentControl permits ReadyControl,UnavailableControl {}
    public record ReadyControl(ObservationIdentity before,List<Obj> fullFrames) implements CurrentControl {public ReadyControl {Objects.requireNonNull(before);fullFrames=List.copyOf(fullFrames);}}
    public record UnavailableControl(String reason) implements CurrentControl {public UnavailableControl {Objects.requireNonNull(reason);}}
    @FunctionalInterface public interface ControlCollector {CurrentControl collect(PlanningRequest request);}
    public sealed interface ReadResult permits ReadCompleted,ReadUnavailable {}
    public record ReadCompleted(ObservationIdentity before,SourceFrame after,List<ExactRef> originalEvidence) implements ReadResult {
        public ReadCompleted {Objects.requireNonNull(before);Objects.requireNonNull(after);originalEvidence=List.copyOf(originalEvidence);require(!originalEvidence.isEmpty()&&originalEvidence.stream().allMatch(ref->ref.bytes()>0),"actual retained retreat read/domain evidence required");}
    }
    public record ReadUnavailable(String reason) implements ReadResult {public ReadUnavailable {Objects.requireNonNull(reason);}}
    /** Native reads plus the existing writer domain reducer; never an ActionCoordinator operation. */
    public interface RetreatReadPort {
        ReadResult preview(PlanningRequest request,int selectedPublicCunitId,int targetProvinceId);
        ReadResult observe(PlanningRequest request);
    }
    private final ExactRef source;
    private final StateReader stateReader;
    private final ControlCollector controls;
    private final CurrentLossModel currentModel;
    private final RetreatReadPort retreatReads;
    private final MilitaryPlanningDecision.ApplicationAdapter adapter;
    public OrdinaryActiveRetreatPolicy(ExactRef source,StateReader stateReader,ControlCollector controls,CurrentLossModel currentModel,RetreatReadPort retreatReads,MilitaryPlanningDecision.ApplicationAdapter adapter) {
        this.source=Objects.requireNonNull(source);this.stateReader=Objects.requireNonNull(stateReader);this.controls=Objects.requireNonNull(controls);
        this.currentModel=Objects.requireNonNull(currentModel);this.retreatReads=Objects.requireNonNull(retreatReads);this.adapter=Objects.requireNonNull(adapter);
    }
    @Override public PlanningStage stage(){return PlanningStage.ORDINARY_RETREAT;}
    @Override public ExactRef implementationSource(){return source;}
    @Override public Decision evaluate(PlanningRequest request,Draft previous) {
        String selected=optionalText(previous.detail().get("selected_step"));
        if(!WarHistorySteps.isLifeAdvance(selected)||!ActiveRetreatProposal.quiet(request.observations().snapshot()))return new NotApplicable("ordinary retreat keeps concrete orders and mandatory player windows first");
        try{return adapter.adapt(request,previous,review(request,previous));}
        catch(IllegalArgumentException error){return adapter.adapt(request,previous,annotation("current_inputs_unavailable",error.getMessage()));}
    }
    public MilitaryPlanningDecision review(PlanningRequest request,Draft previous) {
        DomainRead read=Objects.requireNonNull(stateReader.read(request));
        if(read instanceof UnavailableDomain unavailable)return annotation("unavailable",unavailable.reason());
        KnownDomain known=(KnownDomain)read;require(known.before().equals(request.before()),"retreat state reader crossed source frame");
        State state=known.state();SourceFrame frame=SourceFrame.read(request.observations().snapshot());
        if(state.pending().isPresent()) {
            Order pending=state.pending().orElseThrow();
            if(!pending.source().episodeRunId().equals(frame.episodeRunId()))return annotation("prior_episode_intent_retained_no_replay","original retreat intent belongs to another episode");
            if(!state.lastAttempt().equals(Optional.of(new Attempt(AttemptKind.OBSERVE,frame))))return refreshed(request,retreatReads.observe(request),"original retreat independently observed and same-writer domain updated; recapture full planning inputs");
            return new MilitaryPlanningDecision.Keep(obj(f(FIELD,obj(f("status",text("original_unresolved_continue_normal_battle")),
                    f("last_post",state.lastPost().<Value>map(v->v).orElse(Nil.INSTANCE)),f("replay_allowed",new Bool(false))))));
        }
        if(!request.observations().bridgeCapabilities().containsAll(REQUIRED_CAPABILITIES)||!PHASES.contains(previous.phase()))return new MilitaryPlanningDecision.Keep(empty());
        CurrentControl captured=Objects.requireNonNull(controls.collect(request));
        if(captured instanceof UnavailableControl)return new MilitaryPlanningDecision.Keep(empty());
        ReadyControl ready=(ReadyControl)captured;require(ready.before().equals(request.before()),"retreat current control collector crossed frame");
        MilitaryPlanningDecision retained=new MilitaryPlanningDecision.Keep(empty());
        for(Obj control:ready.fullFrames()) {
            Budget budget=ActiveRetreatProposal.normalBudget(request.observations().snapshot(),control);
            if(!(budget instanceof BudgetObserved observed))continue;
            Optional<Obj> preview=state.preview().filter(value->frame.json().equals(value.get("source_binding")));
            Proposal proposal=ActiveRetreatProposal.propose(request,control,observed,preview,currentModel);
            int subject=id(control.get("selected_public_cunit_id")),combat=int32(control.get("combat_id"));
            if(state.claimed(new ClaimKey(frame.episodeRunId(),subject,combat)))return annotation("original_claim_retained_no_replay","original episode/subject/full-Combat claim is retained");
            if(proposal instanceof Order order)return job(previous,"order",ORDER,
                    "当帧原生允许撤退且一跳友军路线已核；单次撤退以保留后续防御兵力，追击损失和未来安全仍未知。",frame,
                    obj(f("proposal",ActiveRetreatState.order(order)),f("loss_budget",observed.json())));
            if(proposal instanceof Preview value&&!state.lastAttempt().equals(Optional.of(new Attempt(AttemptKind.PREVIEW,frame))))
                return refreshed(request,retreatReads.preview(request,value.subjectPublicCunitId(),value.targetProvinceId()),"actual retreat control and route preview retained in the same writer; recapture full planning inputs");
            if(proposal instanceof ActiveRetreatProposal.Keep keep)retained=new MilitaryPlanningDecision.Keep(obj(f(FIELD,obj(f("status",text(keep.stage())),f("reason",text(keep.reason())),f("loss_budget",observed.json())))));
        }
        return retained;
    }
    private static MilitaryPlanningDecision refreshed(PlanningRequest request,ReadResult result,String reason) {
        Objects.requireNonNull(result);
        if(result instanceof ReadUnavailable missing)return annotation("native_read_unavailable",missing.reason());
        ReadCompleted completed=(ReadCompleted)result;require(completed.before().equals(request.before())&&completed.after().equals(SourceFrame.read(request.observations().snapshot())),"retreat read/domain update crossed original source frame");
        return new MilitaryPlanningDecision.ApplicationDecision(new Refresh(reason));
    }
    private static MilitaryPlanningDecision annotation(String status,String reason){return new MilitaryPlanningDecision.Keep(obj(f(FIELD,obj(f("status",text(status)),f("reason",text(reason==null?"input unavailable":reason))))));}
    private static MilitaryPlanningDecision job(Draft previous,String kind,String step,String reason,SourceFrame frame,Obj fields) {
        String phase="native_war_active_retreat_"+kind;
        Obj job=merge(obj(f("kind",text(kind)),f("source_frame",frame.json())),fields);
        Obj detail=merge(previous.detail(),obj(f("phase",text(phase)),f("selected_step",text(step)),f("reason",text(reason)),f(FIELD,job)));
        String policy=OpportunityJson.text(detail.get("policy"),"original ordinary policy");
        return new MilitaryPlanningDecision.Select(policy,phase,reason,new OperationKey(step),job,Purpose.WORLD_ACTION,detail);
    }
}
