package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** Strategy21418..21561 and war_contract1435..1565; pure closed-window comparisons. */
public final class WarContactWindows {
    private WarContactWindows() {}
    public record Conjunction(List<Obj> covered,List<Obj> missing,List<Obj> unavailable,List<Obj> unavoidable,List<Obj> conflicting) {
        public Conjunction {
            covered=List.copyOf(covered);missing=List.copyOf(missing);unavailable=List.copyOf(unavailable);
            unavoidable=List.copyOf(unavoidable);conflicting=List.copyOf(conflicting);
        }
        public Obj toJson() { return obj(f("covered",objects(covered)),f("missing",objects(missing)),f("unavailable",objects(unavailable)),
                f("unavoidable",objects(unavoidable)),f("conflicting",objects(conflicting))); }
    }
    public static boolean stationaryFree(MilitaryTimeline.Horizon h,int province) {
        require(province>0,"stationary Province");Objects.requireNonNull(h);
        for(var route:h.hostiles()) {
            if(route.currentProvinceId()==province)return false;
            for(int i=0;i<route.provinceIds().size();i++)
                if(route.provinceIds().get(i)==province&&h.horizonStart()<=route.arrivalDates().get(i)
                        &&route.arrivalDates().get(i)<=h.horizonEnd())return false;
        }
        return true;
    }
    public static boolean unavoidableCurrentContact(MilitaryTimeline.Horizon h) {
        if(h.oneDayFree()||h.nativeConflicts().isEmpty())return false;
        var s=h.subject();boolean locked=!s.provinceIds().isEmpty()&&s.arrivalDates().getFirst()>h.horizonEnd();
        boolean stationary=s.provinceIds().isEmpty()&&s.arrivalDates().isEmpty()
                &&h.targetProvinceId()==s.currentProvinceId()&&s.effectiveOriginProvinceId()==s.currentProvinceId();
        return (locked||stationary)&&h.nativeConflicts().stream().allMatch(c->c instanceof MilitaryTimeline.SameProvince p
                &&p.provinceId()==s.currentProvinceId()&&p.start()<=h.horizonEnd());
    }
    public static String advanceStep(MilitaryTimeline.Query q) {
        return q.step().replace("query-route-contact-horizon-v1-","advance-route-contact-horizon-v1-");
    }
    public static String windowStep(MilitaryTimeline.Query q,int days) {
        require(days==2||days==3,"original bounded route window days");
        String suffix=q.step().substring("query-route-contact-horizon-v1-".length());
        int marker=suffix.indexOf("-h-");
        return "advance-route-contact-window-v1-"+suffix.substring(0,marker)+"-days-"+days+suffix.substring(marker);
    }
    public static Conjunction conjunction(PlanningRequest request,WarContactObservation.KnownContact observed,
            MilitaryTimeline.Horizon subject) {
        observed.requireSame(request);var context=observed.context();
        List<Obj> covered=new ArrayList<>(),missing=new ArrayList<>(),unavailable=new ArrayList<>(),unavoidable=new ArrayList<>(),conflicting=new ArrayList<>();
        for(Army army:context.controlledArmies().stream().sorted(Comparator.comparingInt(Army::id)).toList()) {
            if(army.id()==subject.subjectId()||List.of("combat","retreating","gathering").contains(Objects.toString(army.tacticalState(),"")))continue;
            List<Integer> route=army.route().map(r->MilitaryRouteGeometry.remaining(r,army.current()==null?0:army.current())).orElse(null);
            if(army.target()==null&&route!=null&&route.isEmpty())continue;
            if(army.target()==null||army.target()<=0||army.current()==null||army.current()<=0||route==null
                    ||route.isEmpty()||!route.getLast().equals(army.target())) {
                conflicting.add(obj(f("army_id",number(army.id())),f("status",text("active_route_shape_unavailable"))));continue;
            }
            boolean free=stationaryFree(subject,army.current());
            var audit=WarContactObservation.audit(army,context.completeRouteThreatEnemies());
            if(free&&audit.status()==WarContactObservation.AuditStatus.SAFE) {
                covered.add(obj(f("army_id",number(army.id())),f("target_province_id",number(army.target())),
                        f("status",text("derived_current_and_route_safe")),f("proof_subject_army_id",number(subject.subjectId()))));continue;
            }
            var q=new MilitaryTimeline.Query(army.id(),army.current(),army.target(),context.hostileArmyIds(),army.route().orElseThrow());
            Obj evidence=obj(f("army_id",number(army.id())),f("current_province_id",number(army.current())),
                    f("target_province_id",number(army.target())),f("query_step",text(q.step())),
                    f("geometric_audit",audit.detail()),f("derived_current_contact_free",new Bool(free)));
            var lookup=MilitaryTimeline.fresh(request,q);
            if(!(lookup instanceof MilitaryTimeline.Found found)) {
                var attempted=MilitaryTimeline.failure(request,q);
                Obj row=put(evidence,"status",text(attempted.isPresent()?"fresh_subject_query_unavailable":"fresh_subject_query_required"));
                if(lookup instanceof MilitaryTimeline.Malformed malformed) {
                    unavailable.add(merge(row,obj(f("status",text("fresh_subject_query_unavailable")),
                            f("malformed_native_horizon",malformed.original()))));continue;
                }
                if(attempted.isPresent()){row=put(row,"attempt",attempted.orElseThrow());unavailable.add(row);}else missing.add(row);
                continue;
            }
            var h=found.horizon();evidence=put(evidence,"contact_horizon",h.original());
            if(h.oneDayFree())covered.add(put(evidence,"status",text("fresh_subject_contact_free")));
            else if(unavoidableCurrentContact(h))unavoidable.add(merge(evidence,obj(f("status",text("unavoidable_current_province_contact")),
                    f("advance_step",text(advanceStep(q))))));
            else conflicting.add(put(evidence,"status",text("fresh_subject_timed_conflict")));
        }
        return new Conjunction(covered,missing,unavailable,unavoidable,conflicting);
    }
}

