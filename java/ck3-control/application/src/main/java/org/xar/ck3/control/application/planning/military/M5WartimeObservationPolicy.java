package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.finance.warcash.WarcashCodec;
import org.xar.ck3.control.wave2.finance.warcash.WarcashModel;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreatsCodec;

/** Full original plan_m5_wartime_query_only. An observation never replaces the independent war command. */
public final class M5WartimeObservationPolicy implements OrdinaryPolicy {
    private static final List<String> MISSING=List.of("pending_war_cash_raw","immediate_war_action_cost_raw",
            "future_war_cost_upper_raw","future_risk_budget_raw","policy_minimum_gold_reserve_raw","horizon_days","future_bound_assumptions");
    private final ExactRef source;
    private final boolean enabled;
    public M5WartimeObservationPolicy(ExactRef source,boolean enabled){this.source=Objects.requireNonNull(source);this.enabled=enabled;}
    @Override public PlanningStage stage(){return PlanningStage.M5_WARTIME_OBSERVATION;}
    @Override public ExactRef implementationSource(){return source;}
    @Override public Decision evaluate(PlanningRequest request,Draft previous) {
        if(!enabled||!request.observations().warInProgress()||!request.observations().paused()||!request.observations().mapReady()
                ||request.observations().foregroundPresent())return new NotApplicable("original wartime M5 observation scope absent");
        Obj detail;
        try {detail=observe(request.observations().snapshot(),previous.detail(),frame(request));}
        catch(IllegalArgumentException error){detail=put(previous.detail(),"m5_joint_wartime_observation",obj(f("status",text("source_red")),
                f("read_only",new Bool(true)),f("formal_action_ready",new Bool(false)),f("reason",text(error.getMessage()))));}
        detail=put(detail,"m5_nonprimary_war_risk",nonPrimaryRisk(request.observations().snapshot()));
        return new Annotate(new Draft(previous.policy(),previous.phase(),previous.reason(),previous.kind(),previous.command(),
                previous.purpose(),previous.domain(),detail),"same-frame wartime cash and construction observation retains the chosen action");
    }
    public static Obj observe(Obj snapshot,Obj plan,Obj observedFrame) {
        require(yes(snapshot.get("paused"))&&yes(snapshot.get("map_ready")),"M5 wartime observation requires a paused map frame");
        List<Obj> wars=rows(snapshot.get("active_wars"));require(!wars.isEmpty(),"M5 wartime observation requires an active war");
        List<Integer> warIds=new ArrayList<>();for(Obj war:wars){int id=province(war.get("war_id"));require(!warIds.contains(id),"M5 wartime observation lacks exact distinct WarIDs");warIds.add(id);}
        Obj cash=null;String error=null;Value receipt=plan.get("war_cash_resource");
        try {
            if(receipt instanceof Obj raw&&new Text(WarcashModel.AGGREGATE_SCHEMA).equals(raw.get("schema"))) {
                cash=aggregate(snapshot,raw.get("war_receipts"));require(cash.equals(raw),"wartime aggregate differs from its sourced receipts");
            }else if(receipt!=null&&receipt!=Nil.INSTANCE&&warIds.size()==1) {
                Obj raw=OpportunityJson.object(receipt,"war cash receipt");
                if(new Text("incomplete").equals(raw.get("status")))cash=rows(aggregate(snapshot,new Arr(List.of(raw))).get("war_receipts")).getFirst();
                else {
                    WarcashCodec.verifyCompleteSingle(OpportunityJson.toNode(raw),WarcashCodec.decodeObservedFrame(OpportunityJson.toNode(observedFrame)),java.math.BigInteger.valueOf(warIds.getFirst()));
                    cash=raw;
                }
                Obj treasury=OpportunityJson.object(snapshot.get("played_character_gold"),"same-frame treasury");
                require(Objects.equals(cash.get("observed_treasury_raw"),treasury.get("raw")),"wartime cash treasury differs from snapshot");
            }else if(warIds.size()>1||plan.members().containsKey("war_cash_receipts")) {
                Value receipts=plan.members().containsKey("war_cash_receipts")?plan.get("war_cash_receipts"):
                        receipt==null||receipt==Nil.INSTANCE?new Arr(List.of()):new Arr(List.of(receipt));
                cash=aggregate(snapshot,receipts);
            }
        }catch(IllegalArgumentException invalid){error=invalid.getMessage();}
        String status="construction_observation_unavailable";List<String> missing=new ArrayList<>();missing.add("same_frame_native_budgeted_building");missing.addAll(missing(cash));Obj candidate=null;
        if(plan.get("construction_wartime_observation") instanceof Obj construction) {
            Obj expected=obj(f("snapshot_id",observedFrame.get("snapshot_id")),f("revision",observedFrame.get("revision")),
                    f("native_revision",observedFrame.get("native_revision")),f("date_raw",observedFrame.get("date_raw")),
                    f("episode_run_id",observedFrame.get("episode_run_id")),f("actor_character_id",observedFrame.get("played_character_id")));
            Obj treasury=snapshot.get("played_character_gold") instanceof Obj value?value:null;
            if(!expected.equals(construction.get("source_frame"))||treasury==null||!number(100000).equals(treasury.get("scale"))
                    ||!Objects.equals(construction.get("observed_player_gold_raw"),treasury.get("raw"))
                    ||!number(warIds.size()).equals(construction.get("observed_active_war_count")))status="construction_observation_frame_mismatch";
            else if(new Text("source_red").equals(construction.get("status")))status="construction_source_red";
            else if(new Text("observed").equals(construction.get("status"))&&new Text("no_legal_budgeted_building").equals(construction.get("native_source_status"))&&yes(construction.get("positive_income_coverage_complete"))) {status="no_budgeted_building_observed";missing.clear();}
            else if(new Text("observed").equals(construction.get("status"))&&new Text("selected").equals(construction.get("native_source_status"))
                    &&yes(construction.get("native_budgeted_positive_income_candidate"))&&construction.get("candidate") instanceof Obj selected) {
                // This original read-only classification consumes target total income. Net delta remains a distinct native field;
                // the owning construction quote/cash policy independently decides whether any expenditure is allowed.
                candidate=selected;Value cost=candidate.get("stock_gold_cost_raw"),income=candidate.get("authored_monthly_income_hundredths");
                if(cost instanceof IntegerValue c&&c.value().signum()>0&&income instanceof IntegerValue i&&i.value().signum()>0) {
                    status="incomplete_war_cash";missing=new ArrayList<>(missing(cash));if(cash!=null&&new Text("complete").equals(cash.get("status")))status="complete_war_cash_observed";
                    if(error!=null){status="war_cash_resource_invalid";missing.addFirst("valid_same_frame_war_cash_resource");}
                }else {status="construction_candidate_value_unavailable";candidate=null;}
            }else status="construction_observation_incomplete";
        }
        return put(plan,"m5_joint_wartime_observation",obj(f("schema",text("xar.ck3.m5-wartime-joint-observation.v1")),
                f("scope",text("construction_vs_active_war_cash")),f("status",text(status)),f("read_only",new Bool(true)),f("formal_action_ready",new Bool(false)),
                f("frame",observedFrame),f("war_ids",numbers(warIds)),f("candidate",candidate==null?Nil.INSTANCE:candidate),f("missing",strings(missing)),
                f("war_cash_resource",cash==null?Nil.INSTANCE:cash),f("war_cash_error",error==null?Nil.INSTANCE:text(error))));
    }
    /** Independent scope annotation: missing CB/territorial effects never become a safe-war assertion. */
    private static Obj nonPrimaryRisk(Obj snapshot) {
        ParticipatingWarThreats.NonPrimaryRisk risk;
        try {
            risk=ParticipatingWarThreats.nonPrimaryRisk(ParticipatingWarThreatsCodec.observeSnapshot(OpportunityJson.encode(snapshot)));
        } catch(IllegalArgumentException unavailable) {
            risk=new ParticipatingWarThreats.UnavailableNonPrimaryRisk(java.util.Optional.empty(),
                    ParticipatingWarThreats.Reason.PUBLISHED_SNAPSHOT_BOUNDARY_UNAVAILABLE,ParticipatingWarThreats.Presence.INVALID);
        }
        return OpportunityJson.object(OpportunityJson.parse(ParticipatingWarThreatsCodec.encodeNonPrimaryRisk(risk)),"typed non-primary war risk");
    }
    private static List<String> missing(Obj cash) {
        if(cash==null)return MISSING;Value raw=cash.get("missing");
        if(raw instanceof Obj object)return List.copyOf(object.members().keySet());
        return OpportunityJson.array(raw,"cash missing").stream().map(v->OpportunityJson.text(v,"missing field")).toList();
    }
    private static Obj aggregate(Obj snapshot,Value receipts) {
        Obj request=obj(f("schema",text(WarcashCodec.REQUEST_SCHEMA)),f("operation",text("observe_aggregate_active_war_cash_resource_v1")),
                f("arguments",obj(f("snapshot",snapshot),f("receipts",Objects.requireNonNull(receipts)))));
        return OpportunityJson.object(OpportunityJson.parse(WarcashCodec.evaluate(OpportunityJson.encode(request))),"sourced aggregate cash");
    }
}
