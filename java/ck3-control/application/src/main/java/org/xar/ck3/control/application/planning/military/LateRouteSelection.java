package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** The original ranked sweep's result, published only by its real leaf before the late fallback leaf. */
public record LateRouteSelection(Optional<Integer> target,String source,Optional<Obj> audit,
        List<Obj> rejections,Optional<Obj> stationaryTransition,List<Integer> candidates,boolean sweepEntered,
        Optional<Obj> defensiveHold,Optional<Obj> nativeRallyBinding,boolean refugeLifecycle,Optional<Obj> campaignRoot) {
    public static final String FIELD="warcore_late_ranked_selection_v1";
    public LateRouteSelection {
        Objects.requireNonNull(target);target.ifPresent(p->require(p>0,"selected Province"));Objects.requireNonNull(source);
        require(SOURCES.contains(source),"exact original late objective source");Objects.requireNonNull(audit);
        rejections=List.copyOf(rejections);Objects.requireNonNull(stationaryTransition);candidates=List.copyOf(candidates);
        candidates.forEach(p->require(p>0,"candidate Province"));Objects.requireNonNull(defensiveHold);
        Objects.requireNonNull(nativeRallyBinding);Objects.requireNonNull(campaignRoot);
    }
    public Obj encode(PlanningRequest request) {
        return obj(f("frame",frame(request)),f("target",target.<Value>map(MilitaryPlanInputs::number).orElse(Nil.INSTANCE)),
                f("source",text(source)),f("audit",json(audit)),f("rejections",objects(rejections)),
                f("stationary_transition",json(stationaryTransition)),f("candidates",numbers(candidates)),f("sweep_entered",new Bool(sweepEntered)),
                f("defensive_hold",json(defensiveHold)),f("native_rally_binding",json(nativeRallyBinding)),
                f("refuge_lifecycle",new Bool(refugeLifecycle)),f("campaign_root",json(campaignRoot)));
    }
    public static LateRouteSelection decode(PlanningRequest request,Value raw) {
        Obj row=OpportunityJson.object(raw,"real earlier late route selection");
        require(row.members().keySet().equals(FIELDS)&&Objects.equals(row.get("frame"),frame(request)),"late ranked selection missing/crossed current frame");
        return new LateRouteSelection(Optional.ofNullable(optionalInt(row.get("target"))),OpportunityJson.text(row.get("source"),"route source"),
                optional(row.get("audit")),rows(row.get("rejections")),optional(row.get("stationary_transition")),
                route(row.get("candidates")).orElseThrow(),OpportunityJson.bool(row.get("sweep_entered"),"sweep entered"),
                optional(row.get("defensive_hold")),optional(row.get("native_rally_binding")),
                OpportunityJson.bool(row.get("refuge_lifecycle"),"refuge lifecycle"),optional(row.get("campaign_root")));
    }
    private static Optional<Obj> optional(Value value) { require(value!=null,"required nullable sweep field");return value==Nil.INSTANCE?Optional.empty():Optional.of(OpportunityJson.object(value,"sweep optional object")); }
    private static Value json(Optional<Obj> value) {return value.<Value>map(v->v).orElse(Nil.INSTANCE);}
    private static final Set<String> SOURCES=Set.of("war_objective_province","enemy_siege_relief","player_held_county_capital",
            "same_realm_vassal_capital","stationary_player_held_capital","stationary_same_realm_vassal_capital","player_capital_regroup");
    private static final Set<String> FIELDS=Set.of("frame","target","source","audit","rejections","stationary_transition","candidates",
            "sweep_entered","defensive_hold","native_rally_binding","refuge_lifecycle","campaign_root");
}
