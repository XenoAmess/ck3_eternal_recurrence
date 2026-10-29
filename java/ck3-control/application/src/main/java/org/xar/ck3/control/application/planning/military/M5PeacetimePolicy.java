package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.application.planning.finance.OrdinaryConstructionPolicy;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryPolicy;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyAdapters;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReadbackJson;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy;
import org.xar.ck3.control.wave2.planning.rootavailability.RootAvailability;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalProposals;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionReleaseCodec;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly;
import org.xar.ck3.control.wave2.planning.jointintake.FamilyProposalPool;

/** Original M5 formal consumer, including due receipts, root queries, actual strict intake and formal route revalidation. */
public final class M5PeacetimePolicy implements OrdinaryPolicy {
    public static final String BUILD=OrdinaryConstructionPolicy.OPERATION.value(), FAMILY="submit-observed-first-heir-marriage-v1-private",
            GIFT="private-submit-faction-gift-member-v1", ROOT="query-campaign-root-context-v1";
    public record Options(boolean enabled,boolean giftEnabled,boolean familyEnabled) {}
    public record Capture(PeacetimeAssembly.Inputs sources,ConstructionEconomyModel.QuoteCashObservation cash,
                          Optional<ConstructionEconomyModel.QueryOutcome> cashOutcome) {
        public Capture {Objects.requireNonNull(sources);Objects.requireNonNull(cash);Objects.requireNonNull(cashOutcome);}
    }
    public record Prior(PeacetimeAssembly.Ledgers ledgers,ConstructionReleaseCodec.Request constructionRelease) {
        public Prior {Objects.requireNonNull(ledgers);Objects.requireNonNull(constructionRelease);}
    }
    /** Actual before/after ledgers and native source reads. No supplied selected candidate or fabricated readiness flag. */
    public interface SourceCollector {
        Prior prior(PlanningRequest request,Draft original);
        Capture capture(PlanningRequest request,Draft original,Prior originalLedgers);
    }
    /** Existing owning consumers run on their genuine input; this is not another native submit path. */
    public record Consumers(OrdinaryPolicy construction,OrdinaryPolicy gift,FamilyOrdinaryPolicy family) {
        public Consumers {Objects.requireNonNull(construction);Objects.requireNonNull(gift);Objects.requireNonNull(family);
            require(construction.stage()==PlanningStage.CONSTRUCTION&&gift.stage()==PlanningStage.FACTION_GIFT&&family.stage()==PlanningStage.FAMILY_AND_EDUCATION,"M5 requires the actual three domain consumers");}
    }
    private final ExactRef source;private final Options options;private final SourceCollector sources;private final Consumers consumers;
    private final MilitaryPlanningDecision.ApplicationAdapter readAdapter;
    public M5PeacetimePolicy(ExactRef source,Options options,SourceCollector sources,Consumers consumers,
            MilitaryPlanningDecision.ApplicationAdapter readAdapter) {
        this.source=Objects.requireNonNull(source);this.options=Objects.requireNonNull(options);this.sources=Objects.requireNonNull(sources);
        this.consumers=Objects.requireNonNull(consumers);this.readAdapter=Objects.requireNonNull(readAdapter);
    }
    @Override public PlanningStage stage(){return PlanningStage.M5_JOINT_PEACETIME;}
    @Override public ExactRef implementationSource(){return source;}
    @Override public Decision evaluate(PlanningRequest request,Draft previous) {
        Decision joint=evaluateJoint(request,previous);Draft observed=changed(joint);
        if(!options.enabled()||!options.familyEnabled()||observed==null||!new Text("life-advance").equals(previous.detail().get("selected_step"))
                ||request.observations().warInProgress()||!OpportunityJson.array(request.observations().snapshot().get("player_armies"),"player armies").isEmpty())return joint;
        Value selected=observed.detail().get("selected_step");if(selected!=Nil.INSTANCE&&!new Text("life-advance").equals(selected))return joint;
        // Original service3032..3117: the independently owned family consumer receives the life baseline.
        Decision family=consumers.family().evaluate(request,draft(previous,put(observed.detail(),"selected_step",text("life-advance"))));
        Draft actual=changed(family);if(actual==null)return family instanceof Keep||family instanceof NotApplicable?joint:family;
        Obj details=actual.detail();String step=optionalText(details.get("selected_step"));
        if("m5_joint_query_only_red".equals(observed.phase())) {
            boolean fixedPair=yes(details.get("current_betrothal_fulfillment"))
                    &&java.util.Set.of(BetrothalProposals.SUBMIT_STEP,"query-observed-first-heir-marriage-result-v1-private").contains(step==null?"":step);
            details=put(details,"m5_joint_red_reason",nullable(observed.detail().get("reason")));
            if(!fixedPair) {
                details=merge(details,obj(f("selected_step",Nil.INSTANCE),f("phase",text(observed.phase())),f("reason",nullable(observed.detail().get("reason")))));
                return new Replace(new Draft(actual.policy(),observed.phase(),observed.reason(),actual.kind(),Optional.empty(),Purpose.READ_ONLY,actual.domain(),details),observed.reason());
            }
        }else if("life-advance".equals(step)) {
            details=merge(details,obj(f("selected_step",nullable(observed.detail().get("selected_step"))),f("phase",text(observed.phase())),f("reason",text(observed.reason()))));
            return new Replace(new Draft(actual.policy(),observed.phase(),observed.reason(),actual.kind(),observed.command(),observed.purpose(),actual.domain(),details),"family unchanged; retain the actual joint collector result");
        }
        return new Replace(draft(actual,details),"existing family consumer returned its real independently revalidated continuation");
    }
    private Decision evaluateJoint(PlanningRequest request,Draft previous) {
        if(!options.enabled()||!new Text("life-advance").equals(previous.detail().get("selected_step")))return new NotApplicable("M5 original formal collector preserves an existing concrete action");
        Obj snapshot=request.observations().snapshot();
        if(request.observations().warInProgress()||!OpportunityJson.array(snapshot.get("player_armies"),"player armies").isEmpty())
            return annotate(previous,put(put(previous.detail(),"m5_joint_status",text(request.observations().warInProgress()?"ineligible_active_war":"ineligible_player_army")),"m5_joint_formal_action_ready",new Bool(false)));
        if(!request.observations().paused()||!request.observations().mapReady())return blocked(previous,"M5 private collector requires one paused map frame");
        try {
            Prior prior=Objects.requireNonNull(sources.prior(request,previous));
            Obj baseline=previous.detail();var ledger=prior.ledgers();Obj pending=objectOrNull(ledger.construction().get("pending"));
            if(pending!=null)return consumers.construction().evaluate(request,previous);
            Optional<ConstructionReceiptReadback.CurrentProcess> process=prior.constructionRelease().processObservation() instanceof ConstructionRelease.ObservedIdentity observed
                    ?Optional.of(new ConstructionReceiptReadback.CurrentProcess(observed.identity().pid(),observed.identity().originalCreationDate())):Optional.empty();
            var priority=ConstructionReceiptReadback.priorityReceipt(ConstructionReadbackJson.ledger(OpportunityJson.toNode(ledger.construction())),
                    new ConstructionReceiptReadback.Snapshot(OpportunityJson.text(snapshot.get("episode_run_id"),"episode"),OpportunityJson.integer(snapshot.get("native_revision"),"native revision"),OpportunityJson.integer(snapshot.get("date_raw"),"date")),process);
            if(priority.isPresent())return consumers.construction().evaluate(request,previous);
            Obj applied=objectOrNull(ledger.construction().get("applied"));if(applied!=null&&Objects.equals(applied.get("episode_run_id"),snapshot.get("episode_run_id")))baseline=put(baseline,"construction_receipt_consumed",applied);
            if(options.giftEnabled()&&objectOrNull(ledger.faction().get("pending"))!=null)return consumers.gift().evaluate(request,draft(previous,baseline));
            Obj familyPending=objectOrNull(ledger.family().get("pending")),resolved=objectOrNull(ledger.family().get("resolved"));
            if(options.familyEnabled()&&(familyPending!=null||resolved!=null&&Objects.equals(resolved.get("episode_run_id"),snapshot.get("episode_run_id")))) {
                Decision family=consumers.family().evaluate(request,draft(previous,baseline));Draft value=changed(family);
                if(value!=null){String step=optionalText(value.detail().get("selected_step"));if("life-advance".equals(step))baseline=value.detail();else if(!FAMILY.equals(step))return family;}
                else if(family instanceof Stop||family instanceof Wait||family instanceof Refresh||family instanceof ReconcileExisting)return family;
            }
            FactionCandidatePolicy.RootStatus root=options.giftEnabled()?rootStatus(snapshot,request.observations().history()):null;
            boolean rootUnavailable=options.giftEnabled()&&root==FactionCandidatePolicy.RootStatus.SAME_FRAME_ROOT_NOT_OBSERVED&&sameFrameRootUnavailable(snapshot,request.observations().history());
            if(options.giftEnabled()&&root==FactionCandidatePolicy.RootStatus.SAME_FRAME_ROOT_NOT_OBSERVED&&!rootUnavailable) {
                if(!advertised(request,ROOT))return rootUnavailable(previous,baseline,"M5 same-frame faction root is absent and its query is unavailable",null);
                Obj plan=plan(baseline,"m5_joint_root_query",ROOT,"observe same-frame feudal faction facts before joint spending",false);
                return readAdapter.adapt(request,previous,new MilitaryPlanningDecision.Select(previous.policy(),"m5_joint_root_query",
                        "observe same-frame feudal faction facts before joint spending",new OperationKey(ROOT),empty(),Purpose.READ_ONLY,plan));
            }
            Capture capture=Objects.requireNonNull(sources.capture(request,draft(previous,baseline),prior));var input=capture.sources();
            require(input.initialSnapshot().equals(snapshot)&&input.before().equals(prior.ledgers())&&input.constructionRelease().equals(prior.constructionRelease()),"M5 source collector crossed the actual semantic snapshot or prior ledger/release input");
            if(capture.cashOutcome().isPresent())baseline=OpportunityJson.object(OpportunityJson.parse(ConstructionEconomyCodec.encodeEnrichedPlan(
                    ConstructionEconomyAdapters.enrichM5Plan(ConstructionEconomyCodec.decodePlan(OpportunityJson.encode(baseline)),capture.cashOutcome().orElseThrow()))),"real current-cash enrichment");
            var actual=new PeacetimeAssembly.Inputs(input.scope(),input.initialSnapshot(),baseline,input.before(),input.after(),input.constructionRelease(),input.construction(),input.faction(),input.family());
            Obj originalSources=PeacetimeAssembly.source(PeacetimeAssembly.compose(actual));
            M5FormalCollection.Collected collection=M5FormalCollection.collect(request.source(),snapshot,originalSources);
            return route(request,previous,baseline,capture.cash(),collection,rootUnavailable);
        }catch(org.xar.ck3.control.application.action.PreSubmissionRevisionMismatchException changed){throw changed;}
        catch(IllegalArgumentException|IllegalStateException|java.io.UncheckedIOException unavailable){return blocked(previous,"M5 private proposal collection RED: "+unavailable.getMessage());}
    }
    private Decision route(PlanningRequest request,Draft previous,Obj baseline,ConstructionEconomyModel.QuoteCashObservation cash,
                           M5FormalCollection.Collected collection,boolean completedRootUnavailable) {
        var selected=collection.dispatch().reservation();Obj receipt=collection.receipt(),sourceDomains=OpportunityJson.object(collection.originalSources().get("domains"),"actual source domains");
        if(selected.isPresent()) {
            var reservation=selected.orElseThrow();String id=collection.dispatch().selectedCandidateId().orElseThrow();require(id.equals(reservation.candidateId()),"M5 reservation and selected identity disagree");
            switch(reservation.domain()) {
                case building -> {
                    Obj building=objectOrNull(sourceDomains.get("building")),query=building==null?null:objectOrNull(building.get("query")),candidate=query==null?null:objectOrNull(query.get("candidate"));
                    if(candidate!=null&&candidate.get("authored_monthly_income_hundredths") instanceof IntegerValue income&&income.value().signum()>0) {
                        Obj originalQuery=query;
                        var projected=ConstructionEconomyAdapters.projectQuote(ConstructionEconomyCodec.decodeQuote(OpportunityJson.encode(query)),cash,false,false);
                        Obj rendered=OpportunityJson.object(OpportunityJson.parse(ConstructionEconomyCodec.encodeQuoteProjection(projected)),"real construction quote cash projection");query=OpportunityJson.object(rendered.get("quote"),"projected quote");
                        if(query.members().containsKey("construction_monthly_budget"))baseline=put(baseline,"construction_monthly_budget",query.get("construction_monthly_budget"));
                        if(projected.deferredReason().isPresent())return annotate(previous,merge(baseline,obj(f("phase",text("m5_joint_construction_cash_budget_deferred")),f("construction_private_query",query),f("reason",text(projected.deferredReason().orElseThrow())),f("m5_joint_query_only",receipt),f("m5_joint_formal_action_ready",new Bool(false)))));
                        return construction(request,previous,baseline,originalQuery,receipt);
                    }
                }
                case marriage -> {
                    Obj family=objectOrNull(sourceDomains.get("marriage"));if(family!=null) {
                        List<Obj> plans=FamilyProposalPool.readSource(family).plans();
                        for(Obj candidate:plans)if(id.equals(M5FormalCollection.familyIdentity(request.observations().snapshot(),candidate))) {
                            String step=optionalText(candidate.get("selected_step"));if(!SetHolder.FAMILY.contains(step==null?"":step))break;
                            Optional<java.math.BigInteger> actualCandidate=FAMILY.equals(step)
                                    ?Optional.of(OpportunityJson.integer(OpportunityJson.object(candidate.get("family_marriage_choice"),"actual selected family choice").get("candidate_character_id"),"actual selected candidate"))
                                    :Optional.empty();
                            return family(request,previous,baseline,collection,id,receipt,actualCandidate);
                        }
                    }
                }
                case diplomacy -> {
                    if(!options.giftEnabled())return annotate(previous,merge(baseline,obj(f("selected_step",text("life-advance")),f("m5_joint_status",text("selected_gift_formal_consumer_disabled")),f("m5_joint_query_only",receipt),f("m5_joint_formal_action_ready",new Bool(false)))));
                    Obj source=objectOrNull(sourceDomains.get("diplomacy")),candidate=source==null?null:objectOrNull(source.get("candidate"));
                    if(candidate!=null) {
                        Decision gift=consumers.gift().evaluate(request,draft(previous,put(baseline,"selected_step",text("life-advance"))));Draft actual=changed(gift);
                        if(actual==null)return blocked(previous,"M5 selected faction gift has no formal submit path");Obj chosen=objectOrNull(actual.detail().get("faction_gift_private_candidate_v1"));
                        if(chosen==null||!new Text("selected").equals(chosen.get("status"))||!Objects.equals(chosen.get("choice"),candidate.get("choice"))||!Objects.equals(chosen.get("observation"),candidate.get("observation")))return blocked(previous,"M5 selected faction gift changed before formal routing");
                        String step=optionalText(actual.detail().get("selected_step"));if(!GIFT.equals(step)&&!"save-checkpoint".equals(step))return blocked(previous,"M5 selected faction gift has no formal submit path");
                        return new Replace(draft(actual,put(put(actual.detail(),"m5_joint_query_only",receipt),"m5_joint_formal_action_ready",new Bool(GIFT.equals(step)))),"actual faction owner revalidated the selected original gift");
                    }
                }
                default -> { /* The original peaceful producer does not provide a typed action for these domains. */ }
            }
        }
        if(collection.dispatch().selectedCandidateId().isEmpty()) {
            if(completedRootUnavailable)return rootUnavailable(previous,baseline,"M5 same-frame root returned unavailable; no independent proposal is ready",receipt);
            return annotate(previous,put(plan(baseline,"m5_joint_empty_proposals","life-advance","no complete same-frame proposal; continue normal life advance",false),"m5_joint_query_only",receipt));
        }
        Obj detail=put(plan(baseline,"m5_joint_query_only_observed",null,"compare complete same-frame proposals without submitting an action",false),"m5_joint_query_only",receipt);
        return new Replace(new Draft(previous.policy(),"m5_joint_query_only_observed","compare complete same-frame proposals without submitting an action",previous.kind(),Optional.empty(),Purpose.READ_ONLY,previous.domain(),detail),"actual observed proposal has no original typed formal route");
    }
    /** The actual construction owner retains funding gates, Native quote identity, tracked plan and the sole command preparer. */
    private Decision construction(PlanningRequest request,Draft previous,Obj baseline,Obj selectedQuery,Obj receipt) {
        Decision decision=consumers.construction().evaluate(request,draft(previous,put(baseline,"selected_step",text("life-advance"))));
        Draft actual=changed(decision);
        if(actual==null) {
            if(decision instanceof Keep||decision instanceof NotApplicable)return blocked(previous,"M5 selected construction has no actual independently revalidated continuation");
            return decision;
        }
        Obj detail=actual.detail();boolean ready=false;
        if(actual.command().isPresent()) {
            ActionCommand command=actual.command().orElseThrow();
            require(command.operation().value().equals(BUILD),"M5 construction owner returned another action family");
            Obj current=OpportunityJson.object(detail.get("construction_private_query"),"actual complete construction quote");
            require(OrdinaryConstructionPolicy.sameQuote(OpportunityJson.encode(selectedQuery),OpportunityJson.encode(current)),
                    "M5 selected complete construction quote changed before its actual owner prepared the command");
            require(Objects.equals(command.arguments().get("candidate"),current.get("candidate")),
                    "M5 actual construction command differs from its sole full selected candidate");
            require(command.before().equals(request.before())&&command.source().equals(request.source())&&command.sessionId().equals(request.sessionId())
                    &&command.deadline().equals(request.deadline()),"M5 actual construction owner crossed the original source/frame/session/deadline");
            ready=true;
        }
        return new Replace(draft(actual,put(put(detail,"m5_joint_query_only",receipt),"m5_joint_formal_action_ready",new Bool(ready))),
                "actual construction owner revalidated the complete selected quote and retained its original command");
    }
    private Decision family(PlanningRequest request,Draft previous,Obj baseline,M5FormalCollection.Collected collection,String selectedId,Obj receipt,Optional<java.math.BigInteger> actualCandidate) {
        Draft familyBaseline=draft(previous,put(baseline,"selected_step",text("life-advance")));
        Decision decision=actualCandidate.isPresent()?consumers.family().evaluateForCandidate(request,familyBaseline,actualCandidate.orElseThrow())
                :consumers.family().evaluate(request,familyBaseline);
        Draft actual=changed(decision);
        if(actual==null) {
            if(decision instanceof Keep||decision instanceof NotApplicable)return blocked(previous,"M5 selected family plan has no actual independently revalidated continuation");
            return decision;
        }
        String step=optionalText(actual.detail().get("selected_step"));
        require(SetHolder.FAMILY.contains(step==null?"":step),"M5 family owner selected another action family");
        require(selectedId.equals(M5FormalCollection.familyIdentity(request.observations().snapshot(),actual.detail())),
                "M5 selected complete family proposal changed before its actual owner prepared the command");
        ActionCommand command=actual.command().orElseThrow(()->new IllegalArgumentException("M5 selected family has no actual prepared command"));
        require(command.before().equals(request.before())&&command.source().equals(request.source())&&command.sessionId().equals(request.sessionId())
                &&command.deadline().equals(request.deadline())&&command.operation().value().equals(step),"M5 actual family owner crossed original source/frame/session/operation");
        return new Replace(draft(actual,put(put(actual.detail(),"m5_joint_query_only",receipt),"m5_joint_formal_action_ready",new Bool(true))),
                "actual family owner revalidated its selected proposal and retained its original command");
    }
    private static FactionCandidatePolicy.RootStatus rootStatus(Obj snapshot,List<Obj> history) {
        Obj actor=OpportunityJson.object(snapshot.get("played_character"),"played actor");Optional<FactionCandidatePolicy.Frame> frame=yes(snapshot.get("paused"))&&yes(snapshot.get("map_ready"))&&yes(actor.get("alive"))
                ?Optional.of(new FactionCandidatePolicy.Frame(OpportunityJson.integer(snapshot.get("native_revision"),"native revision"),OpportunityJson.integer(snapshot.get("date_raw"),"date"),OpportunityJson.integer(actor.get("character_id"),"actor"))):Optional.empty();
        if(frame.isEmpty())return FactionCandidatePolicy.RootStatus.FRAME_UNAVAILABLE;
        for(int i=history.size()-1;i>=0;i--){Obj row=history.get(i),r=objectOrNull(row.get("result")),context=r==null?null:objectOrNull(r.get("campaign_root_context"));
            if(!new Text(ROOT).equals(row.get("command"))||!yes(row.get("ok"))||context==null)continue;
            var result=FactionCandidatePolicy.latestSameFrameRoot(new FactionCandidatePolicy.RootSearch(frame,List.of(new FactionCandidatePolicy.RootHistory(new Text("available").equals(r.get("status")),FactionCandidateCodec.decodeRootProjection(OpportunityJson.encode(context))))));
            if(result.status()!=FactionCandidatePolicy.RootStatus.SAME_FRAME_ROOT_NOT_OBSERVED)return result.status();
        }return FactionCandidatePolicy.RootStatus.SAME_FRAME_ROOT_NOT_OBSERVED;
    }
    private static boolean sameFrameRootUnavailable(Obj snapshot,List<Obj> history) {
        List<RootAvailability.HistoryRow> projected=new ArrayList<>();
        for(Obj row:history) {
            Obj r=objectOrNull(row.get("result")),context=r==null?null:objectOrNull(r.get("campaign_root_context"));
            if(!new Text(ROOT).equals(row.get("command"))||!yes(row.get("ok"))||r==null||context==null
                    ||!new Text(ROOT).equals(r.get("step"))||!yes(r.get("accepted"))||!new Text("unavailable").equals(r.get("status"))
                    ||!new Text("unavailable").equals(context.get("status")))continue;
            if(r.get("snapshot_revision") instanceof IntegerValue rr&&context.get("snapshot_revision") instanceof IntegerValue cr&&context.get("date_raw") instanceof IntegerValue date)
                projected.add(new RootAvailability.CompletedUnavailable(rr.value(),cr.value(),date.value()));
        }
        return RootAvailability.recognize(new RootAvailability.Request(new RootAvailability.Frame(
                OpportunityJson.integer(snapshot.get("native_revision"),"native revision"),OpportunityJson.integer(snapshot.get("date_raw"),"date")),projected)).sameFrameRootReturnedUnavailable();
    }
    private static final class SetHolder {private static final java.util.Set<String> FAMILY=java.util.Set.of(M5PeacetimePolicy.FAMILY,BetrothalProposals.SUBMIT_STEP);}
    private static Obj objectOrNull(Value value){return value instanceof Obj object?object:null;}
    private static Draft changed(Decision d){return d instanceof Replace r?r.draft():d instanceof Annotate a?a.retained():null;}
    private static Draft draft(Draft old,Obj detail){String phase=optionalText(detail.get("phase")),reason=optionalText(detail.get("reason"));return new Draft(old.policy(),phase==null?old.phase():phase,reason==null?old.reason():reason,old.kind(),old.command(),old.purpose(),old.domain(),detail);}
    private static Decision annotate(Draft previous,Obj detail){
        Draft next=draft(previous,detail);String reason="M5 actual producer annotations retained";
        // Root's real reducer allows Annotate to change detail only. A new diagnostic phase/reason is a normal replacement,
        // retaining the exact previously prepared command, source, deadline and resource claims through draft().
        return next.phase().equals(previous.phase())&&next.reason().equals(previous.reason())?new Annotate(next,reason):new Replace(next,reason);
    }
    private static Obj plan(Obj baseline,String phase,String step,String reason,boolean ready){return merge(baseline,obj(f("phase",text(phase)),f("selected_step",step==null?Nil.INSTANCE:text(step)),f("reason",text(reason)),f("m5_joint_formal_action_ready",new Bool(ready))));}
    private static Decision blocked(Draft previous,String reason){Obj detail=plan(previous.detail(),"m5_joint_query_only_red",null,reason,false);return new Replace(new Draft(previous.policy(),"m5_joint_query_only_red",reason,previous.kind(),Optional.empty(),Purpose.READ_ONLY,previous.domain(),detail),reason);}
    private static Decision rootUnavailable(Draft previous,Obj baseline,String reason,Obj collection){Obj detail=merge(plan(baseline,"m5_joint_root_unavailable_independent_family",null,reason,false),obj(f("m5_joint_status",text("same_frame_faction_root_unavailable")),f("m5_joint_red_reason",text(reason))));if(collection!=null)detail=put(detail,"m5_joint_query_only",collection);return new Replace(new Draft(previous.policy(),"m5_joint_root_unavailable_independent_family",reason,previous.kind(),Optional.empty(),Purpose.READ_ONLY,previous.domain(),detail),reason);}
}
