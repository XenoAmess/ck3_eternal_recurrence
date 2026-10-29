package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.TreeMap;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** Original20652..20831 endpoint observations/epochs, derived from actual history; no native timer estimate. */
public final class WarContactEpochs {
    private final WarContactHistory history;
    public WarContactEpochs(WarContactHistory history){this.history=Objects.requireNonNull(history);}
    private record Key(int war,int army) {}
    private record Endpoint(Key key,int date,Integer current,int target,List<Integer> route) {
        private Endpoint {route=List.copyOf(route);}
        Obj toJson(){return obj(f("war_id",number(key.war())),f("enemy_army_id",number(key.army())),f("date_raw",number(date)),
                f("current_province_id",current==null?Nil.INSTANCE:number(current)),f("move_target_province_id",number(target)),
                f("next_hop_province_id",number(route.getFirst())),f("endpoint_province_id",number(route.getLast())),
                f("route_province_ids",numbers(route)),f("intent_state",text("moving")));}
    }
    private static final class Epoch {
        Endpoint endpoint;final int sequence,first;int last,samples=1;Integer closed;String reason;
        Epoch(Endpoint endpoint,int sequence){this.endpoint=endpoint;this.sequence=sequence;this.first=endpoint.date();this.last=endpoint.date();}
        Obj toJson() {
            long days=Math.max(0,((long)last-first)/24);
            List<Integer> milestones=List.of(7,14).stream().filter(d->days>=d).toList();
            return merge(endpoint.toJson(),obj(f("epoch_sequence",number(sequence)),f("first_observed_date_raw",number(first)),
                    f("last_observed_date_raw",number(last)),f("observed_span_days",number(days)),f("sample_count",number(samples)),
                    f("milestones_crossed_days",numbers(milestones)),f("active",new Bool(closed==null)),
                    f("closed_date_raw",closed==null?Nil.INSTANCE:number(closed)),f("closed_reason",reason==null?Nil.INSTANCE:text(reason))));
        }
    }
    public List<Obj> observe(PlanningRequest request) {
        TreeMap<Integer,List<Obj>> frames=new TreeMap<>();
        for(Obj row:afterRestore(request.observations().history())) {
            if(!yes(row.get("ok"))||!history.lifeStep(command(row)))continue;
            Obj r=result(row);if(r==null)continue;
            for(String name:List.of("war_progress_before","war_progress_after"))if(r.get(name) instanceof Obj frame) {
                Integer date=optionalInt(frame.get("date_raw"));
                if(date!=null&&frame.get("wars") instanceof Arr)frames.put(date,MilitaryPlanInputs.rows(frame.get("wars")));
            }
        }
        Obj snapshot=request.observations().snapshot();Integer now=optionalInt(snapshot.get("date_raw"));
        if(now!=null&&snapshot.get("active_wars") instanceof Arr)frames.put(now,MilitaryPlanInputs.rows(snapshot.get("active_wars")));
        List<Epoch> all=new ArrayList<>();Map<Key,Epoch> opened=new LinkedHashMap<>();Map<Key,Integer> sequences=new LinkedHashMap<>();
        for(var frame:frames.entrySet()) {
            Map<Key,Endpoint> observed=new LinkedHashMap<>();
            for(Obj war:frame.getValue()) {
                Integer warId=optionalInt(war.get("war_id"));if(warId==null||warId<=0||!(war.get("enemy_armies") instanceof Arr))continue;
                for(Obj raw:MilitaryPlanInputs.rows(war.get("enemy_armies")))endpoint(raw,warId,frame.getKey()).ifPresent(e->observed.put(e.key(),e));
            }
            for(Key key:List.copyOf(opened.keySet()))if(!observed.containsKey(key))close(opened,key,frame.getKey(),"observation_gap_or_intent_closed");
            for(var row:observed.entrySet()) {
                Key key=row.getKey();Endpoint next=row.getValue();Epoch prior=opened.get(key);
                boolean same=prior!=null&&prior.endpoint.target()==next.target()
                        &&prior.endpoint.route().getLast().equals(next.route().getLast())&&naturalSuffix(prior.endpoint,next);
                if(!same) {
                    close(opened,key,frame.getKey(),"intent_changed");
                    int sequence=sequences.getOrDefault(key,0)+1;sequences.put(key,sequence);
                    Epoch epoch=new Epoch(next,sequence);all.add(epoch);opened.put(key,epoch);
                } else {prior.endpoint=next;prior.last=next.date();prior.samples++;}
            }
        }
        return all.stream().sorted(Comparator.comparingInt((Epoch e)->e.endpoint.key().war())
                .thenComparingInt(e->e.endpoint.key().army()).thenComparingInt(e->e.sequence)).map(Epoch::toJson).toList();
    }
    private static void close(Map<Key,Epoch> opened,Key key,int date,String reason) {
        Epoch epoch=opened.remove(key);if(epoch!=null){epoch.closed=date;epoch.reason=reason;}
    }
    private static Optional<Endpoint> endpoint(Obj raw,int war,int date) {
        Army army=army(raw);if(List.of("combat","retreating").contains(Objects.toString(army.tacticalState(),""))
                ||army.target()==null||army.target()<=0||army.route().isEmpty())return Optional.empty();
        var route=MilitaryRouteGeometry.remaining(army.route().orElseThrow(),army.current()==null?0:army.current());
        if(route.isEmpty()||!route.getLast().equals(army.target()))return Optional.empty();
        return Optional.of(new Endpoint(new Key(war,army.id()),date,army.current(),army.target(),route));
    }
    private static boolean naturalSuffix(Endpoint previous,Endpoint current) {
        var p=previous.route();var c=current.route();
        if(c.isEmpty()||c.size()>p.size()||!p.subList(p.size()-c.size(),p.size()).equals(c))return false;
        int consumed=p.size()-c.size();
        return consumed==0?Objects.equals(previous.current(),current.current()):Objects.equals(current.current(),p.get(consumed-1));
    }
}

