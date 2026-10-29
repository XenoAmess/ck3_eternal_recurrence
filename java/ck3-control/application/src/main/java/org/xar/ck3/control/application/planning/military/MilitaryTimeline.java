package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteAudit;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** Source-bound full timeline interpretation; H1 stays a distinct one-day predicate. */
public final class MilitaryTimeline {
    private MilitaryTimeline() {}
    public record TimedRoute(int armyId,int currentProvinceId,int effectiveOriginProvinceId,
                             List<Integer> provinceIds,List<Integer> arrivalDates,Obj original) {
        public TimedRoute { provinceIds=List.copyOf(provinceIds);arrivalDates=List.copyOf(arrivalDates);Objects.requireNonNull(original); }
    }
    public sealed interface NativeConflict permits SameProvince,OpposingEdge {}
    public record SameProvince(int hostileId,int provinceId,int start,int end) implements NativeConflict {}
    public record OpposingEdge(int hostileId,int subjectFrom,int subjectTo,int hostileFrom,int hostileTo,
                               int start,int end) implements NativeConflict {}
    public record Horizon(int dateRaw,BigInteger nativeRevision,int subjectId,int targetProvinceId,
                          List<Integer> hostileIds,TimedRoute subject,List<TimedRoute> hostiles,
                          int horizonStart,int horizonEnd,boolean oneDayFree,
                          List<NativeConflict> nativeConflicts,Obj original) {
        public Horizon {
            Objects.requireNonNull(nativeRevision);hostileIds=List.copyOf(hostileIds);Objects.requireNonNull(subject);
            hostiles=List.copyOf(hostiles);nativeConflicts=List.copyOf(nativeConflicts);Objects.requireNonNull(original);
        }
    }
    public sealed interface Lookup permits Found,Missing,Malformed {}
    public record Found(Horizon horizon) implements Lookup { public Found {Objects.requireNonNull(horizon);} }
    public record Missing() implements Lookup {}
    public record Malformed(Obj original,String reason) implements Lookup {
        public Malformed { Objects.requireNonNull(original);StrictJson.text(reason); }
    }
    public record Query(int subjectId,int originProvinceId,int targetProvinceId,
                        List<Integer> hostileIds,List<Integer> routeProvinceIds) {
        public Query {
            require(subjectId>=0&&originProvinceId>0&&targetProvinceId>0,"timeline subject/Province IDs");
            hostileIds=List.copyOf(hostileIds);routeProvinceIds=List.copyOf(routeProvinceIds);
            // Reuse the existing canonical native operation validator.
            MilitaryRouteAudit.horizonStep(subjectId,targetProvinceId,hostileIds);
        }
        public String step() { return MilitaryRouteAudit.horizonStep(subjectId,targetProvinceId,hostileIds); }
    }
    /** Original fresh lookup21331: restore/merge invalidate; first matching current row wins. */
    public static Lookup fresh(PlanningRequest request,Query query) {
        List<Obj> history=afterRestore(request.observations().history());
        List<Integer> expected=MilitaryRouteGeometry.remaining(query.routeProvinceIds(),query.originProvinceId());
        for(int index=history.size()-1;index>=0;index--) {
            Obj row=history.get(index);
            if(mergeBarrier(row,query.subjectId()))return new Missing();
            if(!query.step().equals(command(row))||!yes(row.get("ok")))continue;
            Obj result=result(row);
            if(result==null||!sameLease(request,result)||!(result.get("route_contact_horizon") instanceof Obj h)
                    ||!(h.get("subject_route") instanceof Obj subject))continue;
            try {
                if(!new Text("available").equals(h.get("status"))||id(h.get("subject_army_id"))!=query.subjectId()
                        ||province(h.get("target_province_id"))!=query.targetProvinceId()
                        ||!ids(h.get("hostile_army_ids")).equals(query.hostileIds())
                        ||!OpportunityJson.integer(h.get("date_raw"),"date_raw").equals(request.before().frame().identity().dateRaw())
                        ||!OpportunityJson.integer(h.get("snapshot_revision"),"snapshot_revision").equals(request.before().frame().identity().nativeRevision())
                        ||id(subject.get("army_id"))!=query.subjectId()
                        ||province(subject.get("current_province_id"))!=query.originProvinceId()
                        ||!MilitaryRouteGeometry.remaining(route(subject.get("route_province_ids")).orElseThrow(),
                            query.originProvinceId()).equals(expected)
                        ||!(h.get("one_day_contact_free") instanceof Bool))continue;
            } catch(IllegalArgumentException|java.util.NoSuchElementException invalid) {continue;}
            try { return new Found(decode(h,request,query)); }
            catch(IllegalArgumentException invalid) { return new Malformed(h,invalid.getMessage()==null?"native timeline schema invalid":invalid.getMessage()); }
        }
        return new Missing();
    }
    private static final Set<String> HORIZON_FIELDS=Set.of("status","date_raw","snapshot_revision","subject_army_id",
            "target_province_id","hostile_army_ids","subject_route","hostile_routes","horizon_start_date_raw",
            "horizon_end_date_raw","one_day_contact_free","conflicts");
    private static final Set<String> ROUTE_FIELDS=Set.of("timeline_observable","army_id","current_province_id",
            "effective_origin_province_id","route_province_ids","arrival_date_raws");
    public static Horizon decode(Obj value,PlanningRequest request,Query query) {
        require(value.members().keySet().equals(HORIZON_FIELDS),"exact native route-contact horizon fields");
        require(new Text("available").equals(value.get("status")),"native horizon not available");
        int date=int32(value.get("date_raw"));
        BigInteger revision=OpportunityJson.integer(value.get("snapshot_revision"),"native snapshot revision");
        require(revision.signum()>0&&revision.compareTo(StrictJson.UINT64_MAX)<=0,"positive native uint64 revision");
        require(date==int32(number(request.before().frame().identity().dateRaw()))
                &&revision.equals(request.before().frame().identity().nativeRevision())
                &&id(value.get("subject_army_id"))==query.subjectId()
                &&province(value.get("target_province_id"))==query.targetProvinceId()
                &&ids(value.get("hostile_army_ids")).equals(query.hostileIds()),"native horizon scope differs");
        TimedRoute subject=timed(OpportunityJson.object(value.get("subject_route"),"subject route"),query.subjectId(),date);
        require(subject.provinceIds().isEmpty()?subject.currentProvinceId()==query.targetProvinceId():
                subject.provinceIds().getLast()==query.targetProvinceId(),"native subject route misses requested target");
        List<Obj> hostileRows=rows(value.get("hostile_routes"));
        require(hostileRows.size()==query.hostileIds().size(),"complete ordered native hostile scope required");
        List<TimedRoute> hostiles=new ArrayList<>();
        for(int i=0;i<hostileRows.size();i++)hostiles.add(timed(hostileRows.get(i),query.hostileIds().get(i),date));
        int start=int32(value.get("horizon_start_date_raw"));
        int end=int32(value.get("horizon_end_date_raw"));
        require(start==date&&(long)end==(long)date+24,"native H1 must be exactly one day");
        boolean free=OpportunityJson.bool(value.get("one_day_contact_free"),"one_day_contact_free");
        List<NativeConflict> conflicts=new ArrayList<>();
        for(Obj conflict:rows(value.get("conflicts"))) {
            String kind=OpportunityJson.text(conflict.get("kind"),"conflict kind");
            int hostile=id(conflict.get("hostile_army_id"));
            require(query.hostileIds().contains(hostile),"native conflict outside requested hostile scope");
            int a=int32(conflict.get("overlap_start_date_raw"));
            int b=int32(conflict.get("overlap_end_date_raw"));
            require(start<=a&&a<=b&&b<=end,"native conflict outside H1");
            if(kind.equals("same_province")) {
                require(conflict.members().keySet().equals(Set.of("kind","hostile_army_id","province_id",
                        "overlap_start_date_raw","overlap_end_date_raw")),"native same-Province conflict schema");
                conflicts.add(new SameProvince(hostile,province(conflict.get("province_id")),a,b));
            } else {
                require(kind.equals("opposing_edge")&&conflict.members().keySet().equals(Set.of("kind","hostile_army_id",
                        "subject_from_province_id","subject_to_province_id","hostile_from_province_id","hostile_to_province_id",
                        "overlap_start_date_raw","overlap_end_date_raw")),"native opposing-edge conflict schema");
                conflicts.add(new OpposingEdge(hostile,province(conflict.get("subject_from_province_id")),
                        province(conflict.get("subject_to_province_id")),province(conflict.get("hostile_from_province_id")),
                        province(conflict.get("hostile_to_province_id")),a,b));
            }
        }
        require(free==conflicts.isEmpty(),"native H1 predicate differs from its conflicts");
        return new Horizon(date,revision,query.subjectId(),query.targetProvinceId(),query.hostileIds(),subject,
                hostiles,start,end,free,conflicts,value);
    }
    private static TimedRoute timed(Obj value,int expectedArmy,int date) {
        require(value.members().keySet().equals(ROUTE_FIELDS)&&yes(value.get("timeline_observable")),"complete native timed route schema");
        int army=id(value.get("army_id")),current=province(value.get("current_province_id"));
        int effective=province(value.get("effective_origin_province_id"));
        List<Integer> route=route(value.get("route_province_ids")).orElseThrow();
        List<Integer> arrivals=new ArrayList<>();
        for(Value raw:OpportunityJson.array(value.get("arrival_date_raws"),"native arrivals"))
            arrivals.add(int32(raw));
        require(army==expectedArmy&&route.size()==arrivals.size(),"native timed route identity/length differs");
        require(route.isEmpty()?effective==current:effective==current||effective==route.getFirst(),"native effective origin differs");
        int last=date;
        for(int arrival:arrivals) {require(arrival>=last,"native arrival dates are unordered or before frame");last=arrival;}
        return new TimedRoute(army,current,effective,route,arrivals,value);
    }
    /** Known/unknown query failures remain distinct; a returned older valid proof is selected first by fresh(). */
    public static Optional<Obj> failure(PlanningRequest request,Query query) {
        List<Obj> history=afterRestore(request.observations().history());
        for(int i=history.size()-1;i>=0;i--) {
            Obj row=history.get(i);String step=command(row);
            if(query.step().equals(step)) {
                if(no(row.get("ok"))&&new Text("_NativeCommandRejectedError: native gameplay step failed: state_changed").equals(row.get("error")))
                    return Optional.empty();
                Obj result=result(row);Obj h=result!=null&&result.get("route_contact_horizon") instanceof Obj nativeH?nativeH:null;
                if(no(row.get("ok"))&&result==null) {
                    String suffix="; typed_query_failure_v1={\"executor_enter\":true,\"executor_exception\":{\"code\":0,\"image\":\"none\",\"rva\":null},\"executor_finish\":true,\"executor_typed_result\":false,\"final_equal\":null,\"final_read\":null,\"frame_stable\":true,\"query_type\":\"route\",\"stage\":\"typed_result\",\"typed_result\":false,\"wait_completed\":true,\"wait_result\":\"completed\"}";
                    for(String reason:List.of("CK3 could not build a complete contact route","CK3 route arrival timeline is unavailable"))
                        if(new Text("_NativeCommandRejectedError: native gameplay step failed: "+reason+suffix).equals(row.get("error")))
                            return Optional.empty();
                }
                // Exact current fields that disagree mean an expired readonly result, not a current veto.
                if(result!=null) {
                    var snapshot=request.observations().snapshot();
                    Obj diagnostics=snapshot.get("diagnostics") instanceof Obj d?d:empty();
                    Obj expected=obj(f("queried_snapshot_id",snapshot.get("snapshot_id")),f("queried_revision",snapshot.get("revision")),
                            f("queried_native_revision",snapshot.get("native_revision")),f("queried_connection_generation",nullable(diagnostics.get("connection_generation"))),
                            f("queried_episode_run_id",snapshot.get("episode_run_id")));
                    for(var field:expected.members().entrySet())
                        if(result.members().containsKey(field.getKey())&&!Objects.equals(result.get(field.getKey()),field.getValue()))
                            return Optional.empty();
                    if(h!=null&&((h.members().containsKey("date_raw")&&!Objects.equals(h.get("date_raw"),snapshot.get("date_raw")))
                            ||(h.members().containsKey("snapshot_revision")&&!Objects.equals(h.get("snapshot_revision"),snapshot.get("native_revision")))))
                        return Optional.empty();
                }
                Obj snapshot=request.observations().snapshot();
                Obj diagnostics=snapshot.get("diagnostics") instanceof Obj d?d:empty();
                Obj actor=snapshot.get("played_character") instanceof Obj a?a:empty();
                Obj evidence=result!=null&&result.get("readonly_unavailable_evidence") instanceof Obj e?e:empty();
                Obj readback=evidence.get("same_frame_readback") instanceof Obj r?r:empty();
                boolean exactUnavailable=result!=null&&no(row.get("ok"))
                        &&new Text("xar.route-contact-readonly-unavailable.v1").equals(result.get("schema"))
                        &&new Text(query.step()).equals(result.get("step"))&&new Text("unavailable").equals(result.get("status"))
                        &&no(result.get("accepted"))&&result.get("route_contact_horizon")==Nil.INSTANCE
                        &&new Text("native_complete_contact_route_unavailable").equals(result.get("unavailable_reason"))
                        &&sameLease(request,result)&&result.get("queried_date_raw") instanceof IntegerValue
                        &&Objects.equals(result.get("queried_date_raw"),snapshot.get("date_raw"))
                        &&result.get("queried_actor_character_id") instanceof IntegerValue&&actor.get("character_id") instanceof IntegerValue
                        &&Objects.equals(result.get("queried_actor_character_id"),actor.get("character_id"))
                        &&result.get("queried_bridge_pid") instanceof IntegerValue&&diagnostics.get("bridge_pid") instanceof IntegerValue
                        &&Objects.equals(result.get("queried_bridge_pid"),diagnostics.get("bridge_pid"))
                        &&readback.get("starting_frame") instanceof Obj&&Objects.equals(readback.get("starting_frame"),readback.get("ending_frame"));
                boolean exact=result!=null&&sameLease(request,result)&&result.get("queried_revision") instanceof IntegerValue
                        &&result.get("queried_native_revision") instanceof IntegerValue
                        &&result.get("queried_connection_generation") instanceof IntegerValue
                        &&diagnostics.get("connection_generation") instanceof IntegerValue
                        &&snapshot.get("episode_run_id") instanceof Text episode&&!episode.value().isEmpty()
                        &&(h!=null&&Objects.equals(h.get("date_raw"),snapshot.get("date_raw"))
                            &&Objects.equals(h.get("snapshot_revision"),snapshot.get("native_revision"))||exactUnavailable);
                return Optional.of(obj(f("history_index",nullable(row.get("index"))),f("ok",nullable(row.get("ok"))),
                        f("error",nullable(row.get("error"))),f("scope_status",text(exact?"current_frame":"unknown_frame")),
                        f("status",result==null?Nil.INSTANCE:nullable(result.get("status")))));
            }
            if(isMutationFence(step))return Optional.empty();
        }
        return Optional.empty();
    }
    /** Original exact parsers: malformed prefixes are not historical world transitions. */
    public static boolean isMutationFence(String step) {
        return WarHistorySteps.isLifeAdvance(step)||WarHistorySteps.parseMove(step).isPresent()
                ||WarHistorySteps.isMerge(step)||WarHistorySteps.isSplit(step);
    }
    public record Exposure(boolean available,boolean veto,Obj detail) {
        public Exposure {Objects.requireNonNull(detail);require(available||!veto,"unavailable origin observation is not a native veto");}
    }
    /** Original war_route_origin_exposure_v1: closed-window known entry before the first subject arrival. */
    public static Exposure origin(Horizon h,int origin) {
        if(h.subject().currentProvinceId()!=origin||h.subject().provinceIds().isEmpty()
                ||h.subject().arrivalDates().getFirst()<=h.dateRaw())
            return new Exposure(false,false,obj(f("status",text("unavailable")),f("veto",new Bool(false)),
                    f("reason",text("subject_first_arrival_not_observable"))));
        int first=h.subject().arrivalDates().getFirst();List<Obj> exposures=new ArrayList<>();
        for(TimedRoute hostile:h.hostiles())for(int i=0;i<hostile.provinceIds().size();i++) {
            int arrival=hostile.arrivalDates().get(i);
            if(hostile.provinceIds().get(i)==origin&&h.dateRaw()<=arrival&&arrival<=first) {
                exposures.add(obj(f("hostile_army_id",number(hostile.armyId())),f("province_id",number(origin)),
                        f("hostile_arrival_date_raw",number(arrival)),f("subject_first_arrival_date_raw",number(first)),
                        f("origin_exposure_hours",number((long)first-arrival))));break;
            }
        }
        boolean veto=!exposures.isEmpty();
        return new Exposure(true,veto,obj(f("schema",text("xar.ck3.pre-move-origin-exposure/v1")),
                f("status",text("available")),f("veto",new Bool(veto)),f("reason",text(veto?
                    "hostile_enters_origin_before_subject_first_arrival":"no_observed_origin_entry_before_subject_first_arrival")),
                f("subject_army_id",number(h.subjectId())),f("origin_province_id",number(origin)),f("target_province_id",number(h.targetProvinceId())),
                f("first_arrival_date_raw",number(first)),f("native_timeline_exposures",objects(exposures)),
                f("complete_hostile_army_ids",numbers(h.hostileIds())),f("source_native_revision",number(h.nativeRevision())),
                f("source_date_raw",number(h.dateRaw())),f("first_day_contact_free",new Bool(h.oneDayFree())),
                f("movement_abortability",text("not_observed; native halt can reject a committed leg")),
                f("full_route_safety_or_battle_win_proven",new Bool(false))));
    }
    private record Visit(int province,int start,int end) {}
    private record Edge(int from,int to,int start,int end) {}
    private record Windows(List<Visit> visits,List<Edge> edges) {}
    private static Windows windows(TimedRoute route,int start,int end) {
        List<Integer> places=new ArrayList<>();places.add(route.currentProvinceId());places.addAll(route.provinceIds());
        List<Integer> dates=new ArrayList<>();dates.add(start);dates.addAll(route.arrivalDates());
        List<Visit> visits=new ArrayList<>();List<Edge> edges=new ArrayList<>();
        for(int i=0;i<places.size();i++) {
            int date=dates.get(i),next=i+1<dates.size()?dates.get(i+1):end;
            if(date<=end)visits.add(new Visit(places.get(i),date,Math.min(next,end)));
            if(i>0&&dates.get(i-1)<=end)edges.add(new Edge(places.get(i-1),places.get(i),dates.get(i-1),Math.min(date,end)));
        }
        return new Windows(List.copyOf(visits),List.copyOf(edges));
    }
    /** Original conservative full-current-order overlap calculation; it never extends H1's native guarantee. */
    public static Obj lockedRoute(Horizon h) {
        require(!h.subject().arrivalDates().isEmpty(),"moving subject has no final arrival");
        int end=h.subject().arrivalDates().getLast();Windows own=windows(h.subject(),h.dateRaw(),end);
        List<Obj> conflicts=new ArrayList<>();
        for(TimedRoute hostile:h.hostiles()) {
            Windows enemy=windows(hostile,h.dateRaw(),end);
            for(Visit a:own.visits())for(Visit b:enemy.visits())
                if(a.province()==b.province()&&Math.max(a.start(),b.start())<=Math.min(a.end(),b.end()))
                    conflicts.add(obj(f("kind",text("projected_locked_province_overlap")),f("hostile_army_id",number(hostile.armyId())),
                            f("province_id",number(a.province())),f("overlap_start_date_raw",number(Math.max(a.start(),b.start()))),
                            f("overlap_end_date_raw",number(Math.min(a.end(),b.end())))));
            for(Edge a:own.edges())for(Edge b:enemy.edges())
                if(a.from()==b.to()&&a.to()==b.from()&&Math.max(a.start(),b.start())<=Math.min(a.end(),b.end()))
                    conflicts.add(obj(f("kind",text("projected_locked_opposing_edge")),f("hostile_army_id",number(hostile.armyId())),
                            f("from_province_id",number(a.from())),f("to_province_id",number(a.to())),
                            f("overlap_start_date_raw",number(Math.max(a.start(),b.start()))),
                            f("overlap_end_date_raw",number(Math.min(a.end(),b.end())))));
        }
        return obj(f("schema",text("xar.ck3.rendezvous-locked-route-exposure/v1")),f("status",text("available")),
                f("veto",new Bool(!conflicts.isEmpty())),f("known_route_conflicts",objects(conflicts)),
                f("evaluated_until_date_raw",number(end)),f("native_h1_end_date_raw",number(h.horizonEnd())),
                f("source",text("conservative inference from full Native current-order route/arrival arrays")),
                f("future_orders_or_safe_arrival_proven",new Bool(false)));
    }
}

