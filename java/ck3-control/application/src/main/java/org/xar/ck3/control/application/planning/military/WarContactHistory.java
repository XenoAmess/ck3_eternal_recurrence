package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original surviving-history move/restore/UNKNOWN rules. Reads only caller-owned actual rows. */
public final class WarContactHistory {
    private final java.util.function.Predicate<String> lifeSteps;
    public WarContactHistory(java.util.function.Predicate<String> actualLifeStepClassifier) {
        this.lifeSteps=Objects.requireNonNull(actualLifeStepClassifier);
    }
    private static final Pattern MOVE=Pattern.compile("move-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)");
    public sealed interface Lookup permits Found,Absent,Incomplete {}
    public record Found(ObservationIdentity before,G2Source source,Obj evidence) implements Lookup {
        public Found {Objects.requireNonNull(before);Objects.requireNonNull(source);Objects.requireNonNull(evidence);}
        public void requireSame(PlanningRequest request){require(before.equals(request.before())&&source.equals(request.source()),"history result source/frame differs");}
    }
    public record Absent() implements Lookup {}
    public record Incomplete(List<String> missing) implements Lookup {
        public Incomplete {missing=List.copyOf(missing);require(!missing.isEmpty(),"history gap required");}
    }
    private record Move(int army,int target) {}
    private record Accepted(int position,Obj row) {}
    private static Move move(String value) {
        if(value==null)return null;var m=MOVE.matcher(value);if(!m.matches())return null;
        return new Move(Integer.parseInt(m.group(1)),Integer.parseInt(m.group(2)));
    }
    private static Obj rawResult(Obj row){return row.get("result") instanceof Obj r?r:null;}
    private static Obj child(Obj row,String key){return row!=null&&row.get(key) instanceof Obj v?v:null;}
    private static boolean eq(Obj row,String key,Value value){return row!=null&&Objects.equals(row.get(key),value);}
    public boolean lifeStep(String step) { return step!=null&&lifeSteps.test(step); }
    @FunctionalInterface private interface Read {Optional<Obj> observe();}
    private static Lookup read(PlanningRequest request,Read read) {
        try{return read.observe().<Lookup>map(v->new Found(request.before(),request.source(),v)).orElseGet(Absent::new);}
        catch(IllegalArgumentException|java.util.NoSuchElementException e){return new Incomplete(List.of(Objects.toString(e.getMessage(),"history observation malformed")));}
    }
    public Lookup activeMoveIntent(PlanningRequest request,int army,int target) {
        require(army>=0&&target>0,"actual move identity required");
        return read(request,()->acceptedIntent(request,army,target,false));
    }
    public Lookup arrival(PlanningRequest request,int army,int target) {
        require(army>=0&&target>0,"actual arrival identity required");
        return read(request,()->acceptedIntent(request,army,target,true).or(()->observedIntent(request,army,target,true)));
    }
    public Lookup deferredBackoff(PlanningRequest request,int army,int target) {
        return read(request,()->backoff(request,army,target));
    }
    public Lookup acceptedArrival(PlanningRequest request,int army,int target) { return read(request,()->acceptedIntent(request,army,target,true)); }
    public Lookup observedErrorArrival(PlanningRequest request,int army,int target) { return read(request,()->observedIntent(request,army,target,true)); }
    private static Optional<Accepted> latestAccepted(List<Obj> rows,int army) {
        List<Integer> restores=new ArrayList<>();
        for(int i=rows.size()-1;i>=0;i--) {
            Obj row=rows.get(i);if(mergeBarrier(row,army))return Optional.empty();
            if("restore-checkpoint".equals(command(row))&&yes(row.get("ok"))){restores.add(i);continue;}
            Move parsed=move(command(row));if(parsed==null||parsed.army()!=army)continue;
            if(!yes(row.get("ok")))return Optional.empty();
            int boundary=i;
            for(int j=restores.size()-1;j>=0;j--) {
                int restored=restores.get(j);
                if(!persistedThroughRestore(rows,boundary,restored))return Optional.empty();boundary=restored;
            }
            return Optional.of(new Accepted(i,row));
        }
        return Optional.empty();
    }
    /** Original23372..23455: saved checkpoint between boundaries or exact adjacent official restore reuse. */
    public static boolean persistedThroughRestore(List<Obj> actualRows,int movePosition,int restorePosition) {
        List<Obj> rows=List.copyOf(actualRows);
        require(movePosition>=0&&restorePosition>movePosition&&restorePosition<rows.size(),"actual history positions");
        Obj restored=rawResult(rows.get(restorePosition)),checkpoint=child(restored,"checkpoint");
        if(!eq(restored,"status",text("restored"))||!eq(restored,"source",text("native-session-cold-start"))||checkpoint==null)return false;
        Integer index=optionalInt(checkpoint.get("history_index")),date=optionalInt(checkpoint.get("date_raw"));
        String sha=optionalText(checkpoint.get("sha256"));
        if(index==null||date==null||sha==null||sha.isEmpty())return false;
        if(restorePosition==movePosition+1&&"restore-checkpoint".equals(command(rows.get(movePosition)))) {
            Obj previous=rows.get(movePosition),r=rawResult(previous),old=child(r,"checkpoint");
            if(!yes(previous.get("ok"))||!eq(r,"status",text("restored"))||!eq(r,"source",text("native-session-cold-start"))||old==null)return false;
            for(String field:List.of("history_index","date_raw","sha256","size","name","episode_character_id","episode_run_id"))
                if(old.get(field)==null||old.get(field)==Nil.INSTANCE||checkpoint.get(field)==null||checkpoint.get(field)==Nil.INSTANCE
                        ||!old.get(field).equals(checkpoint.get(field)))return false;
            return true;
        }
        for(int i=restorePosition-1;i>movePosition;i--) {
            Obj row=rows.get(i);if(!"save-checkpoint".equals(command(row))||!yes(row.get("ok")))continue;
            Obj saved=child(rawResult(row),"checkpoint");
            if(saved!=null&&Objects.equals(optionalInt(saved.get("history_index")),index)
                    &&Objects.equals(optionalInt(saved.get("date_raw")),date)&&eq(saved,"sha256",text(sha)))return true;
        }
        return false;
    }
    private Optional<Obj> acceptedIntent(PlanningRequest request,int id,int target,boolean arrived) {
        List<Obj> rows=request.observations().history();var latest=latestAccepted(rows,id);
        if(latest.isEmpty())return arrived?Optional.empty():observedIntent(request,id,target,false);
        var accepted=latest.orElseThrow();Move m=move(command(accepted.row()));
        if(m==null||m.army()!=id||m.target()!=target)return Optional.empty();
        Obj r=rawResult(accepted.row()),action=child(r,"war_action");
        String status=action==null?null:optionalText(action.get("status"));
        if(action==null||!List.of("move_submitted","moving").contains(Objects.toString(status,""))||eq(r,"accepted",new Bool(false)))return Optional.empty();
        for(var field:List.of(f("army_id",number(id)),f("target_province_id",number(target))))
            if(action.get(field.key())!=null&&action.get(field.key())!=Nil.INSTANCE&&!action.get(field.key()).equals(field.value()))return Optional.empty();
        var army=topArmy(request,id);if(army.isEmpty())return Optional.empty();Army a=army.orElseThrow();
        if(arrived) {
            if(!sieging(a.raw(),target))return Optional.empty();
        } else {
            if(Objects.equals(a.current(),target))return Optional.empty();
            boolean observable=yes(a.raw().get("move_target_observable"));
            boolean knownIdle=no(a.raw().get("move_target_observable"))
                    &&List.of("regular","sieging","gathering","raiding","bartering").contains(Objects.toString(a.tacticalState(),""));
            if(a.target()==null&&(observable||knownIdle)||a.target()!=null&&a.target()!=target)return Optional.empty();
        }
        int elapsed=elapsedDays(rows,accepted.position(),action,request.observations().snapshot());
        if(elapsed>=90&&(!arrived||!siegeContinuity(rows,accepted.position(),id,target,
                optionalInt(action.get("submitted_date_raw")),optionalInt(request.observations().snapshot().get("date_raw")))))return Optional.empty();
        return Optional.of(obj(f("status",text(arrived?"arrived":"active")),f("army_id",number(id)),f("target_province_id",number(target)),
                f("elapsed_days",number(elapsed)),f("timeout_days",number(90))));
    }
    private static Optional<Army> topArmy(PlanningRequest request,int id) {
        require(request.observations().snapshot().get("player_armies") instanceof Arr,"actual top-level player_armies required");
        return MilitaryPlanInputs.rows(request.observations().snapshot().get("player_armies")).stream().map(MilitaryPlanInputs::army).filter(a->a.id()==id).findFirst();
    }
    private int elapsedDays(List<Obj> rows,int position,Obj action,Obj snapshot) {
        Integer submitted=optionalInt(action.get("submitted_date_raw")),current=optionalInt(snapshot.get("date_raw"));
        if(submitted!=null&&current!=null&&current>=submitted)return Math.toIntExact(((long)current-submitted)/24);
        long days=0;
        for(Obj row:rows.subList(position+1,rows.size())) {
            if(!yes(row.get("ok"))||!lifeStep(command(row)))continue;
            Obj r=rawResult(row);if(r==null)continue;
            Integer elapsed=optionalInt(r.get("elapsed_days"));
            if(elapsed!=null&&elapsed>=0){days+=elapsed;continue;}
            Integer start=optionalInt(r.get("starting_date_raw")),end=optionalInt(r.get("ending_date_raw"));
            if(start!=null&&end!=null&&end>=start)days+=((long)end-start)/24;
        }
        return Math.toIntExact(days);
    }
    private static Optional<Obj> progressArmy(Obj summary,int army) {
        if(summary==null||!(summary.get("wars") instanceof Arr))return Optional.empty();List<Obj> matches=new ArrayList<>();
        for(Obj war:MilitaryPlanInputs.rows(summary.get("wars")))if(war.get("player_armies") instanceof Arr)
            for(Obj a:MilitaryPlanInputs.rows(war.get("player_armies")))if(Objects.equals(optionalInt(a.get("army_id")),army))matches.add(a);
        if(matches.isEmpty()||matches.stream().anyMatch(v->!v.equals(matches.getFirst())))return Optional.empty();return Optional.of(matches.getFirst());
    }
    private static boolean sieging(Obj raw,int target) {
        Army a=army(raw);return "sieging".equals(a.tacticalState())&&Objects.equals(a.current(),target)
                &&a.moveTargetPresent()&&a.target()==null&&a.route().filter(List::isEmpty).isPresent()
                &&Boolean.FALSE.equals(a.inCombat())&&Boolean.FALSE.equals(a.retreating());
    }
    private static boolean combat(Obj raw,int target) {
        Army a=army(raw);return "combat".equals(a.tacticalState())&&Objects.equals(a.current(),target)
                &&a.target()==null&&a.route().filter(List::isEmpty).isPresent()
                &&Boolean.TRUE.equals(a.inCombat())&&Boolean.FALSE.equals(a.retreating());
    }
    private static boolean moving(Obj raw,int target) {
        Army a=army(raw);return List.of("moving","embarked").contains(Objects.toString(a.tacticalState(),""))
                &&Objects.equals(a.target(),target)&&a.route().filter(v->!v.isEmpty()&&v.getLast()==target).isPresent()
                &&Boolean.FALSE.equals(a.inCombat())&&Boolean.FALSE.equals(a.retreating());
    }
    private boolean siegeContinuity(List<Obj> rows,int position,int army,int target,Integer submitted,Integer current) {
        if(submitted==null||current==null)return false;int expected=submitted;String state="moving";
        for(Obj row:rows.subList(position+1,rows.size())) {
            if(!yes(row.get("ok")))continue;Obj r=result(row),before=child(r,"war_progress_before"),after=child(r,"war_progress_after");
            if(before==null||after==null){if(lifeStep(command(row)))return false;continue;}
            Integer start=optionalInt(before.get("date_raw")),end=optionalInt(after.get("date_raw"));
            if(!Objects.equals(start,expected)||end==null||end<=expected)return false;
            var b=progressArmy(before,army);var a=progressArmy(after,army);if(b.isEmpty()||a.isEmpty())return false;
            if(state.equals("sieging")) {if(!sieging(b.orElseThrow(),target)||!sieging(a.orElseThrow(),target))return false;}
            else if(state.equals("combat")) {
                if(!combat(b.orElseThrow(),target))return false;
                if(sieging(a.orElseThrow(),target))state="sieging";else if(!combat(a.orElseThrow(),target))return false;
            } else {
                if(!moving(b.orElseThrow(),target))return false;
                if(sieging(a.orElseThrow(),target))state="sieging";else if(combat(a.orElseThrow(),target))state="combat";
                else if(!moving(a.orElseThrow(),target))return false;
            }
            expected=end;
        }
        return state.equals("sieging")&&expected==current;
    }
    private static Optional<Obj> backoff(PlanningRequest request,int id,int target) {
        List<Obj> rows=afterRestore(request.observations().history());int first=0;List<Integer> dates=new ArrayList<>();
        for(int i=rows.size()-1;i>=0;i--)if(mergeBarrier(rows.get(i),id)){first=i+1;break;}
        String step="move-army-"+id+"-to-"+target;
        for(Obj row:rows.subList(first,rows.size())) {
            if(!step.equals(command(row))||!yes(row.get("ok")))continue;Obj action=child(rawResult(row),"war_action");
            if(action==null)continue;String status=optionalText(action.get("status"));
            if(List.of("move_submitted","moving","arrived").contains(Objects.toString(status,"")))dates.clear();
            else if("move_deferred".equals(status)) {Integer date=optionalInt(action.get("submitted_date_raw"));if(date!=null)dates.add(date);}
        }
        if(dates.isEmpty())return Optional.empty();
        int required=new int[]{7,14,30}[Math.min(dates.size()-1,2)];Integer now=optionalInt(request.observations().snapshot().get("date_raw"));
        long elapsed=now==null?0:Math.max(0,((long)now-dates.getLast())/24);
        return Optional.of(obj(f("attempt",number(dates.size())),f("elapsed_days",number(elapsed)),f("required_days",number(required)),f("retry_due",new Bool(elapsed>=required))));
    }
    private static Optional<Obj> observedIntent(PlanningRequest request,int id,int target,boolean arrived) {
        Obj s=request.observations().snapshot(),actor=child(s,"played_character"),diag=child(s,"diagnostics");
        var candidateArmy=topArmy(request,id);if(candidateArmy.isEmpty()||actor==null||diag==null)return Optional.empty();
        Army a=candidateArmy.orElseThrow();
        if(!yes(s.get("paused"))||!yes(s.get("map_ready"))||!yes(actor.get("alive"))||!a.controllable()
                ||!Objects.equals(a.raw().get("owner_character_id"),actor.get("character_id"))
                ||!Boolean.FALSE.equals(a.inCombat())||!Boolean.FALSE.equals(a.retreating())
                ||optionalInt(diag.get("bridge_pid"))==null||optionalInt(diag.get("bridge_pid"))<=0)return Optional.empty();
        if(arrived) {
            if(!Objects.equals(a.current(),target)||a.target()!=null||a.route().filter(List::isEmpty).isEmpty())return Optional.empty();
        } else if(Objects.equals(a.current(),target)||!yes(a.raw().get("move_target_observable"))||!Objects.equals(a.target(),target)
                ||!"complete_nonempty".equals(a.routeReadStatus())||a.route().filter(v->!v.isEmpty()&&v.getLast()==target).isEmpty())return Optional.empty();
        Obj evidence=null;List<Obj> rows=afterRestore(request.observations().history());String expected="move-army-"+id+"-to-"+target;
        for(int i=rows.size()-1;i>=0;i--) {
            Obj row=rows.get(i);String step=command(row);
            if("reconcile-observed-move-intent".equals(step)) {
                Obj e=rawResult(row);
                if(no(row.get("ok"))&&eq(e,"schema",text("xar.reconciled-observed-move-intent.v1"))&&eq(e,"original_step",text(expected))) {
                    Obj original=null;
                    for(int j=i-1;j>=0;j--){Move parsed=move(command(rows.get(j)));if(parsed!=null&&parsed.army()==id){original=rows.get(j);break;}}
                    if(original!=null&&Objects.equals(original.get("index"),e.get("original_failed_history_index"))&&expected.equals(command(original))
                            &&no(original.get("ok"))&&optionalText(original.get("error"))!=null
                            &&optionalText(original.get("error")).contains("CK3 move-army state is unavailable"))evidence=e;
                }break;
            }
            Move parsed=move(step);if(parsed==null||parsed.army()!=id)continue;Obj e=result(row);
            if(parsed.target()==target&&no(row.get("ok"))&&eq(e,"step",text(step))&&eq(e,"status",text("observed_after_native_error")))evidence=e;
            break;
        }
        if(evidence==null||!eq(evidence,"native_ack_verified",new Bool(false))
                ||!eq(evidence,"business_submission_may_have_applied",new Bool(true))
                ||!eq(evidence,"native_error",text("CK3 move-army state is unavailable"))||!eq(evidence,"accepted",new Bool(false)))return Optional.empty();
        Obj source=child(evidence,"source_frame"),observed=child(evidence,"observed_frame");
        if(source==null||observed==null)return Optional.empty();
        BigInteger sn=optionalInteger(source.get("native_revision")),on=optionalInteger(observed.get("native_revision")),cn=optionalInteger(s.get("native_revision"));
        BigInteger sr=optionalInteger(source.get("revision")),or=optionalInteger(observed.get("revision"));
        Integer date=optionalInt(s.get("date_raw")),sd=optionalInt(source.get("date_raw"));
        if(sn==null||sn.signum()<=0||on==null||on.compareTo(sn)<=0||cn==null||cn.compareTo(on)<0
                ||!eq(s,"snapshot_id",text("native:"+cn))||!eq(source,"snapshot_id",text("native:"+sn))||!eq(observed,"snapshot_id",text("native:"+on))
                ||sr==null||or==null||or.compareTo(sr)<=0||date==null||sd==null||!Objects.equals(source.get("date_raw"),observed.get("date_raw"))
                ||sd>date||((long)date-sd)/24>=90)return Optional.empty();
        if(!Objects.equals(source.get("actor_character_id"),actor.get("character_id"))||!Objects.equals(observed.get("actor_character_id"),actor.get("character_id"))
                ||optionalInteger(actor.get("character_id"))==null||optionalInteger(actor.get("character_id")).signum()<=0
                ||!Objects.equals(source.get("episode_run_id"),s.get("episode_run_id"))||!Objects.equals(observed.get("episode_run_id"),s.get("episode_run_id"))
                ||!Objects.equals(source.get("bridge_pid"),diag.get("bridge_pid"))||!Objects.equals(observed.get("bridge_pid"),diag.get("bridge_pid")))return Optional.empty();
        var observedRoute=route(evidence.get("observed_army_route"));
        var startingRoute=route(evidence.get("starting_army_route"));
        if(observedRoute.isEmpty()||startingRoute.isEmpty()||observedRoute.orElseThrow().isEmpty()
                ||observedRoute.orElseThrow().getLast()!=target||observedRoute.equals(startingRoute))return Optional.empty();
        if(!arrived) {
            List<Integer> r=observedRoute.orElseThrow(),currentRoute=a.route().orElseThrow();
            if(currentRoute.size()>r.size()||!r.subList(r.size()-currentRoute.size(),r.size()).equals(currentRoute))return Optional.empty();
        }
        if(eq(evidence,"status",text("observed_after_native_error"))) {
            Obj action=child(evidence,"war_action"),raw=child(evidence,"native_error_evidence"),nr=child(raw,"native_request"),response=child(raw,"native_command_result");
            Value rid=raw==null?null:raw.get("native_request_id");
            if(!(rid instanceof Text t)||t.value().isEmpty()||!eq(action,"status",text("route_intent_observed"))
                    ||!eq(action,"postcondition_verified",new Bool(true))||!eq(action,"original_native_ack_verified",new Bool(false))
                    ||!eq(action,"army_id",number(id))||!eq(action,"target_province_id",number(target))
                    ||!Objects.equals(action.get("submitted_date_raw"),source.get("date_raw"))
                    ||!eq(nr,"type",text("execute_step"))||!eq(nr,"protocol_version",number(1))||!eq(nr,"request_id",rid)||!eq(nr,"step",text(expected))
                    ||!eq(nr,"expected_revision",number(sn))||!eq(response,"type",text("command_result"))
                    ||!eq(response,"protocol_version",number(1))||!eq(response,"request_id",rid)
                    ||!eq(response,"ok",new Bool(false))||!eq(response,"error",evidence.get("native_error")))return Optional.empty();
        } else if(eq(evidence,"schema",text("xar.reconciled-observed-move-intent.v1"))) {
            if(!eq(evidence,"status",text("observed_route_intent"))||!eq(evidence,"recovery_kind",text("original_move_observed_route_intent"))
                    ||!(evidence.get("original_native_request_id") instanceof Text t)||t.value().isEmpty())return Optional.empty();
            for(String name:List.of("recovery_audit_sha256","original_response_sha256"))
                if(!(evidence.get(name) instanceof Text h)||!h.value().matches("[0-9a-f]{64}"))return Optional.empty();
            for(String name:List.of("new_move_submissions","failed_pending_business_credit","date_credit"))
                if(!eq(evidence,name,number(0)))return Optional.empty();
        } else return Optional.empty();
        return Optional.of(obj(f("status",text(arrived?"arrived":"active")),f("army_id",number(id)),f("target_province_id",number(target)),
                f("elapsed_days",number(((long)date-sd)/24)),f("timeout_days",number(90)),
                f("evidence_kind",text("independently_observed_route_after_native_error")),
                f("native_ack_verified",new Bool(false)),f("business_submission_may_have_applied",new Bool(true))));
    }
}

