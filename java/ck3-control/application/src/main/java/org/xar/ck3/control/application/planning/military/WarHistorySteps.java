package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Pattern;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.contracts.StrictJson;

/** Original strategy history reducers. Failed native calls stay failed; route evidence grants no ACK credit. */
public final class WarHistorySteps {
    private WarHistorySteps() {}
    private static final BigInteger UNIT_MAX=BigInteger.valueOf(Integer.MAX_VALUE);
    private static final Pattern MOVE=Pattern.compile("move-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)"),
            PREVIEW=Pattern.compile("preview-move-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)"),
            MERGE=Pattern.compile("merge-armies-(0|[1-9][0-9]*)-with-(0|[1-9][0-9]*)");
    public record Move(int armyId,int targetProvinceId) {
        public Move { StrictJson.require(armyId>=0&&targetProvinceId>0,"public CUnit and positive Province required"); }
    }
    public record AcceptedMove(int position,Obj row) { public AcceptedMove {Objects.requireNonNull(row);} }
    public static Optional<Move> parseMove(String step) {return pair(step,MOVE);}
    public static Optional<Move> parsePreview(String step) {return pair(step,PREVIEW);}
    private static Optional<Move> pair(String step,Pattern pattern) {
        if(step==null)return Optional.empty();var m=pattern.matcher(step);if(!m.matches())return Optional.empty();
        Integer a=decimal(m.group(1),false,UNIT_MAX),p=decimal(m.group(2),true,UNIT_MAX);
        return a==null||p==null?Optional.empty():Optional.of(new Move(a,p));
    }
    public static boolean isMerge(String step) {
        if(step==null)return false;var m=MERGE.matcher(step);if(!m.matches())return false;
        Integer a=decimal(m.group(1),false,UNIT_MAX),b=decimal(m.group(2),false,UNIT_MAX);return a!=null&&b!=null&&!a.equals(b);
    }
    public static boolean isSplit(String step) {
        String p="split-army-half-";return step!=null&&step.startsWith(p)&&canonicalUnit(step.substring(p.length()));
    }
    public static boolean mergeBarrier(Obj row,int army) {
        String step=command(row);if(!yes(row.get("ok"))||!isMerge(step))return false;var m=MERGE.matcher(step);m.matches();
        return new BigInteger(m.group(1)).intValueExact()==army||new BigInteger(m.group(2)).intValueExact()==army;
    }
    /** Sole clock/history command classifier; native operation parsers enforce every token and range. */
    public static boolean isLifeAdvance(String step) {
        return DriverSurvivingHistory.isLifeAdvanceStep(step);
    }

    public enum ProgressPhase {
        BEFORE("war_progress_before"), AFTER("war_progress_after");
        private final String field;
        ProgressPhase(String field) { this.field=field; }
        public String field() { return field; }
    }
    public enum ArmyRole {
        PLAYER("player_armies"), ENEMY("enemy_armies"), ALLIED("allied_armies");
        private final String field;
        ArmyRole(String field) { this.field=field; }
        public String field() { return field; }
    }
    public record ProgressSlice(Optional<BigInteger> dateRaw, Optional<Obj> war) {
        public ProgressSlice { Objects.requireNonNull(dateRaw); Objects.requireNonNull(war); }
    }
    /** Exact original progress summary selection. A missing war and a missing date remain independent. */
    public static ProgressSlice progressSlice(Optional<Obj> result, ProgressPhase phase, int warId) {
        Objects.requireNonNull(result); Objects.requireNonNull(phase);
        StrictJson.require(warId>0,"positive WarID required");
        Obj summary=result.map(value -> child(value,phase.field())).orElse(null);
        return new ProgressSlice(Optional.ofNullable(integer(summary,"date_raw")),
                Optional.ofNullable(summary==null?null:find(summary.get("wars"),"war_id",warId)));
    }
    public static Optional<Obj> progressArmy(Optional<Obj> war, ArmyRole role, int armyId) {
        Objects.requireNonNull(war); Objects.requireNonNull(role);
        StrictJson.require(armyId>=0,"public CUnit including zero required");
        return war.map(value -> find(value.get(role.field()),"army_id",armyId));
    }
    public static Optional<Obj> progressObjective(Optional<Obj> war, int provinceId) {
        Objects.requireNonNull(war); StrictJson.require(provinceId>0,"positive ProvinceID required");
        return war.map(value -> find(value.get("objective_province_states"),"province_id",provinceId));
    }
    public static Optional<Obj> progressActiveSiege(Optional<Obj> state, int siegeId) {
        Objects.requireNonNull(state); StrictJson.require(siegeId>=0,"public SiegeID including zero required");
        return state.map(value -> child(value,"active_siege"))
                .filter(value -> equalNumber(value.get("siege_id"),siegeId)&&yes(value.get("player_army_besieging")));
    }
    public static List<BigInteger> progressSiegeObjectives(Obj war) {
        Objects.requireNonNull(war); List<BigInteger> result=new ArrayList<>();
        if(war.get("war_objective_province_ids") instanceof Arr array)
            for(Value value:array.items())if(value instanceof IntegerValue number)result.add(number.value());
        BigInteger fallback=integer(war,"enemy_primary_default_raise_province_id");
        if(fallback!=null&&!result.contains(fallback))result.add(fallback);
        return List.copyOf(result);
    }
    public static Optional<String> armyTacticalState(Optional<Obj> army) {
        Objects.requireNonNull(army); return army.flatMap(value -> Optional.ofNullable(tactical(value)));
    }
    private static boolean canonicalUnit(String s){return s!=null&&s.matches("0|[1-9][0-9]*")&&decimal(s,false,UNIT_MAX)!=null;}
    private static Integer decimal(String s,boolean positive,BigInteger max){BigInteger n=bounded(s,positive,max);return n==null?null:n.intValueExact();}
    private static BigInteger bounded(String s,boolean positive,BigInteger max){if(s==null||!s.matches("[0-9]+"))return null;BigInteger n=new BigInteger(s);return n.compareTo(positive?BigInteger.ONE:BigInteger.ZERO)<0||n.compareTo(max)>0?null:n;}
    private static BigInteger integer(Value v){return v instanceof IntegerValue n?n.value():null;}
    private static BigInteger integer(Obj o,String k){return o==null?null:integer(o.get(k));}
    private static boolean equalNumber(Value v,long n){return BigInteger.valueOf(n).equals(integer(v));}
    private static boolean positive(Value v){return integer(v)!=null&&integer(v).signum()>0;}
    private static Obj child(Obj o,String k){return o!=null&&o.get(k) instanceof Obj c?c:null;}
    private static List<Obj> objectsOrEmpty(Value v){if(!(v instanceof Arr a))return List.of();return a.items().stream().filter(Obj.class::isInstance).map(Obj.class::cast).toList();}
    private static String string(Value v){return v instanceof Text t?t.value():null;}
    private static boolean named(Obj o,String key,String value){return o!=null&&new Text(value).equals(o.get(key));}
    private static boolean nullish(Value v){return v==null||v==Nil.INSTANCE;}
    private static boolean positiveRoute(Value v){return v instanceof Arr a&&a.items().stream().allMatch(WarHistorySteps::positive);}
    private static Obj find(Value rows,String key,int id){return objectsOrEmpty(rows).stream().filter(r->equalNumber(r.get(key),id)).findFirst().orElse(null);}
    private static String tactical(Obj a){if(a==null)return null;if(yes(a.get("retreating")))return "retreating";if(yes(a.get("in_combat")))return "combat";if(a.get("army_state") instanceof Text t)return t.value().toLowerCase(java.util.Locale.ROOT);BigInteger c=integer(a,"army_state_code");if(BigInteger.TWO.equals(c))return "combat";if(BigInteger.valueOf(3).equals(c))return "sieging";if(BigInteger.valueOf(6).equals(c))return "retreating";return BigInteger.valueOf(7).equals(c)?"moving":null;}
    /** Preserve the source's no-credit elapsed fallback when old move receipts omit dates. */
    public static BigInteger moveIntentElapsedDays(List<Obj> history,int position,Obj action,Obj snapshot) {
        BigInteger submitted=integer(action,"submitted_date_raw"),now=integer(snapshot,"date_raw");
        if(submitted!=null&&now!=null&&now.compareTo(submitted)>=0)return now.subtract(submitted).divide(BigInteger.valueOf(24));
        BigInteger elapsed=BigInteger.ZERO;
        for(Obj row:history.subList(position+1,history.size()))if(isLifeAdvance(command(row))&&yes(row.get("ok"))) {
            Obj r=child(row,"result");if(r==null)continue;BigInteger days=integer(r,"elapsed_days");
            if(days!=null&&days.signum()>=0){elapsed=elapsed.add(days);continue;}
            BigInteger start=integer(r,"starting_date_raw"),end=integer(r,"ending_date_raw");
            if(start!=null&&end!=null&&end.compareTo(start)>=0)elapsed=elapsed.add(end.subtract(start).divide(BigInteger.valueOf(24)));
        }return elapsed;
    }
    public static Optional<Obj> deferredMoveBackoff(List<Obj> history,Obj snapshot,String step) {
        List<Obj> scoped=afterRestore(history);Optional<Move> parsed=parseMove(step);
        if(parsed.isPresent())for(int i=scoped.size()-1;i>=0;i--)if(mergeBarrier(scoped.get(i),parsed.orElseThrow().armyId())){scoped=scoped.subList(i+1,scoped.size());break;}
        List<BigInteger> dates=new ArrayList<>();
        for(Obj row:scoped)if(Objects.equals(command(row),step)&&yes(row.get("ok"))) {
            Obj action=child(child(row,"result"),"war_action");String status=action==null?null:string(action.get("status"));
            if(status!=null&&Set.of("move_submitted","moving","arrived").contains(status))dates.clear();
            else if("move_deferred".equals(status)&&integer(action,"submitted_date_raw")!=null)dates.add(integer(action,"submitted_date_raw"));
        }
        if(dates.isEmpty())return Optional.empty();int required=new int[]{7,14,30}[Math.min(dates.size()-1,2)];BigInteger now=integer(snapshot,"date_raw");
        BigInteger elapsed=now==null?BigInteger.ZERO:now.subtract(dates.getLast()).divide(BigInteger.valueOf(24)).max(BigInteger.ZERO);
        return Optional.of(obj(f("attempt",number(dates.size())),f("elapsed_days",number(elapsed)),f("required_days",number(required)),f("retry_due",new Bool(elapsed.compareTo(BigInteger.valueOf(required))>=0))));
    }
    public static Optional<AcceptedMove> latestAcceptedMove(List<Obj> history,int army) {
        List<Integer> restores=new ArrayList<>();
        for(int i=history.size()-1;i>=0;i--){Obj row=history.get(i);if(mergeBarrier(row,army))return Optional.empty();String step=command(row);
            if("restore-checkpoint".equals(step)&&yes(row.get("ok"))){restores.add(i);continue;}
            var move=parseMove(step);if(move.isEmpty()||move.orElseThrow().armyId()!=army)continue;if(!yes(row.get("ok")))return Optional.empty();int boundary=i;
            for(int r=restores.size()-1;r>=0;r--){int restore=restores.get(r);if(!persistedThroughRestore(history,boundary,restore))return Optional.empty();boundary=restore;}
            return Optional.of(new AcceptedMove(i,row));
        }return Optional.empty();
    }
    private static boolean persistedThroughRestore(List<Obj> history,int move,int restore) {
        Obj result=child(history.get(restore),"result"),checkpoint=child(result,"checkpoint");
        if(!named(result,"status","restored")||!named(result,"source","native-session-cold-start")||checkpoint==null||integer(checkpoint,"history_index")==null||integer(checkpoint,"date_raw")==null||!(checkpoint.get("sha256") instanceof Text sha)||sha.value().isEmpty())return false;
        if(restore==move+1&&"restore-checkpoint".equals(command(history.get(move)))) {
            Obj previous=child(history.get(move),"result"),prior=child(previous,"checkpoint");if(!yes(history.get(move).get("ok"))||!named(previous,"status","restored")||!named(previous,"source","native-session-cold-start")||prior==null)return false;
            for(String field:List.of("history_index","date_raw","sha256","size","name","episode_character_id","episode_run_id"))if(nullish(prior.get(field))||nullish(checkpoint.get(field))||!Objects.equals(prior.get(field),checkpoint.get(field)))return false;return true;
        }
        for(int i=restore-1;i>move;i--){Obj row=history.get(i),save=child(child(row,"result"),"checkpoint");if(!"save-checkpoint".equals(command(row))||!yes(row.get("ok"))||save==null)continue;
            if(integer(save,"history_index")!=null&&Objects.equals(save.get("history_index"),checkpoint.get("history_index"))&&integer(save,"date_raw")!=null&&Objects.equals(save.get("date_raw"),checkpoint.get("date_raw"))&&Objects.equals(save.get("sha256"),checkpoint.get("sha256")))return true;
        }return false;
    }
    public static Optional<Obj> activeNativeMoveIntent(List<Obj> history,Obj snapshot,int army,int target) {
        var latest=latestAcceptedMove(history,army);if(latest.isEmpty())return observedNativeMoveIntent(history,snapshot,army,target,false);
        var found=latest.orElseThrow();if(!parseMove(command(found.row())).equals(Optional.of(new Move(army,target))))return Optional.empty();
        Obj result=child(found.row(),"result"),action=child(result,"war_action");
        if(action==null||!Set.of("move_submitted","moving").contains(string(action.get("status"))==null?"":string(action.get("status")))||no(result.get("accepted"))||!optionalIdentity(action,"army_id",army)||!optionalIdentity(action,"target_province_id",target))return Optional.empty();
        Obj current=find(snapshot.get("player_armies"),"army_id",army);if(current==null||equalNumber(current.get("current_province_id"),target))return Optional.empty();
        Value observed=current.get("move_target_province_id");String state=tactical(current);
        if(nullish(observed)&&(yes(current.get("move_target_observable"))||no(current.get("move_target_observable"))&&Set.of("regular","sieging","gathering","raiding","bartering").contains(state==null?"":state)))return Optional.empty();
        if(integer(observed)!=null&&!equalNumber(observed,target))return Optional.empty();BigInteger elapsed=moveIntentElapsedDays(history,found.position(),action,snapshot);
        return elapsed.compareTo(BigInteger.valueOf(90))>=0?Optional.empty():Optional.of(intent("active",army,target,elapsed));
    }
    private static boolean optionalIdentity(Obj o,String k,int expected){return nullish(o.get(k))||equalNumber(o.get(k),expected);}
    private static Obj intent(String status,int army,int target,BigInteger days){return obj(f("status",text(status)),f("army_id",number(army)),f("target_province_id",number(target)),f("elapsed_days",number(days)),f("timeout_days",number(90)));}
    public static Optional<Obj> observedNativeMoveIntent(List<Obj> history,Obj snapshot,int army,int target,boolean arrived) {
        if(!yes(snapshot.get("paused"))||!yes(snapshot.get("map_ready")))return Optional.empty();Obj current=find(snapshot.get("player_armies"),"army_id",army),actor=child(snapshot,"played_character"),diag=child(snapshot,"diagnostics");
        if(current==null||actor==null||diag==null||!yes(actor.get("alive"))||!Objects.equals(current.get("owner_character_id"),actor.get("character_id"))||!yes(current.get("controllable"))||!no(current.get("in_combat"))||!no(current.get("retreating"))||!positive(diag.get("bridge_pid")))return Optional.empty();
        Value route=current.get("route_province_ids");
        if(arrived){if(!equalNumber(current.get("current_province_id"),target)||!nullish(current.get("move_target_province_id"))||!new Arr(List.of()).equals(route))return Optional.empty();}
        else if(equalNumber(current.get("current_province_id"),target)||!yes(current.get("move_target_observable"))||!equalNumber(current.get("move_target_province_id"),target)||!named(current,"route_read_status","complete_nonempty")||!positiveRoute(route)||((Arr)route).items().isEmpty()||!equalNumber(((Arr)route).items().getLast(),target))return Optional.empty();
        List<Obj> scoped=afterRestore(history);Obj evidence=null;String exact="move-army-"+army+"-to-"+target;
        for(int i=scoped.size()-1;i>=0;i--){Obj row=scoped.get(i);String step=command(row);
            if("reconcile-observed-move-intent".equals(step)) {
                Obj candidate=child(row,"result");
                if(no(row.get("ok"))&&named(candidate,"schema","xar.reconciled-observed-move-intent.v1")&&named(candidate,"original_step",exact)) {
                    Obj original=null;for(int j=i-1;j>=0;j--){var move=parseMove(command(scoped.get(j)));if(move.isPresent()&&move.orElseThrow().armyId()==army){original=scoped.get(j);break;}}
                    if(original!=null&&Objects.equals(original.get("index"),candidate.get("original_failed_history_index"))&&exact.equals(command(original))&&no(original.get("ok"))&&original.get("error") instanceof Text error&&error.value().contains("CK3 move-army state is unavailable"))evidence=candidate;
                }break;
            }
            var move=parseMove(step);if(move.isEmpty()||move.orElseThrow().armyId()!=army)continue;Obj candidate=result(row);
            if(move.orElseThrow().targetProvinceId()==target&&no(row.get("ok"))&&named(candidate,"step",step)&&named(candidate,"status","observed_after_native_error"))evidence=candidate;break;
        }
        if(evidence==null||!no(evidence.get("native_ack_verified"))||!yes(evidence.get("business_submission_may_have_applied"))||!named(evidence,"native_error","CK3 move-army state is unavailable")||!no(evidence.get("accepted")))return Optional.empty();
        Obj source=child(evidence,"source_frame"),observed=child(evidence,"observed_frame");if(source==null||observed==null)return Optional.empty();
        BigInteger sn=integer(source,"native_revision"),on=integer(observed,"native_revision"),cn=integer(snapshot,"native_revision"),sd=integer(source,"date_raw"),cd=integer(snapshot,"date_raw"),sr=integer(source,"revision"),or=integer(observed,"revision");
        if(sn==null||sn.signum()<=0||on==null||on.compareTo(sn)<=0||cn==null||cn.compareTo(on)<0||!named(snapshot,"snapshot_id","native:"+cn)||!named(source,"snapshot_id","native:"+sn)||!named(observed,"snapshot_id","native:"+on)||sr==null||or==null||or.compareTo(sr)<=0||sd==null||cd==null||!Objects.equals(source.get("date_raw"),observed.get("date_raw"))||sd.compareTo(cd)>0||cd.subtract(sd).divide(BigInteger.valueOf(24)).compareTo(BigInteger.valueOf(90))>=0||!positive(actor.get("character_id"))||!Objects.equals(source.get("actor_character_id"),actor.get("character_id"))||!Objects.equals(observed.get("actor_character_id"),actor.get("character_id"))||!(snapshot.get("episode_run_id") instanceof Text episode)||episode.value().isEmpty()||!Objects.equals(source.get("episode_run_id"),snapshot.get("episode_run_id"))||!Objects.equals(observed.get("episode_run_id"),snapshot.get("episode_run_id"))||!Objects.equals(source.get("bridge_pid"),diag.get("bridge_pid"))||!Objects.equals(observed.get("bridge_pid"),diag.get("bridge_pid")))return Optional.empty();
        Value observedRoute=evidence.get("observed_army_route"),startingRoute=evidence.get("starting_army_route");
        if(!positiveRoute(observedRoute)||((Arr)observedRoute).items().isEmpty()||!equalNumber(((Arr)observedRoute).items().getLast(),target)||!positiveRoute(startingRoute)||startingRoute.equals(observedRoute))return Optional.empty();
        if(!arrived){var old=((Arr)observedRoute).items();var now=((Arr)route).items();if(now.size()>old.size()||!old.subList(old.size()-now.size(),old.size()).equals(now))return Optional.empty();}
        if(named(evidence,"status","observed_after_native_error")) {
            Obj action=child(evidence,"war_action"),raw=child(evidence,"native_error_evidence"),request=child(raw,"native_request"),response=child(raw,"native_command_result");String rid=raw==null?null:string(raw.get("native_request_id"));
            if(!named(action,"status","route_intent_observed")||!yes(action.get("postcondition_verified"))||!no(action.get("original_native_ack_verified"))||!equalNumber(action.get("army_id"),army)||!equalNumber(action.get("target_province_id"),target)||!Objects.equals(action.get("submitted_date_raw"),source.get("date_raw"))||rid==null||rid.isEmpty()||!named(request,"type","execute_step")||!equalNumber(request.get("protocol_version"),1)||!named(request,"request_id",rid)||!named(request,"step",exact)||!Objects.equals(request.get("expected_revision"),source.get("native_revision"))||!named(response,"type","command_result")||!equalNumber(response.get("protocol_version"),1)||!named(response,"request_id",rid)||!no(response.get("ok"))||!Objects.equals(response.get("error"),evidence.get("native_error")))return Optional.empty();
        }else if(named(evidence,"schema","xar.reconciled-observed-move-intent.v1")) {
            String rid=string(evidence.get("original_native_request_id")),audit=string(evidence.get("recovery_audit_sha256")),sha=string(evidence.get("original_response_sha256"));
            if(!named(evidence,"status","observed_route_intent")||!named(evidence,"recovery_kind","original_move_observed_route_intent")||rid==null||rid.isEmpty()||audit==null||!audit.matches("[0-9a-f]{64}")||sha==null||!sha.matches("[0-9a-f]{64}")||!equalNumber(evidence.get("new_move_submissions"),0)||!equalNumber(evidence.get("failed_pending_business_credit"),0)||!equalNumber(evidence.get("date_credit"),0))return Optional.empty();
        }else return Optional.empty();
        return Optional.of(merge(intent(arrived?"arrived":"active",army,target,cd.subtract(sd).divide(BigInteger.valueOf(24))),obj(f("evidence_kind",text("independently_observed_route_after_native_error")),f("native_ack_verified",new Bool(false)),f("business_submission_may_have_applied",new Bool(true)))));
    }
    public static Optional<Obj> acceptedNativeMoveArrival(List<Obj> history,Obj snapshot,int army,int target) {
        var latest=latestAcceptedMove(history,army);if(latest.isEmpty())return Optional.empty();var found=latest.orElseThrow();if(!parseMove(command(found.row())).equals(Optional.of(new Move(army,target))))return Optional.empty();Obj r=child(found.row(),"result"),a=child(r,"war_action");
        if(a==null||!Set.of("move_submitted","moving").contains(string(a.get("status"))==null?"":string(a.get("status")))||no(r.get("accepted"))||!optionalIdentity(a,"army_id",army)||!optionalIdentity(a,"target_province_id",target)||!sieging(find(snapshot.get("player_armies"),"army_id",army),target))return Optional.empty();
        BigInteger days=moveIntentElapsedDays(history,found.position(),a,snapshot);if(days.compareTo(BigInteger.valueOf(90))>=0&&!siegeContinuity(history,found.position(),army,target,integer(a,"submitted_date_raw"),integer(snapshot,"date_raw")))return Optional.empty();return Optional.of(intent("arrived",army,target,days));
    }
    private static boolean siegeContinuity(List<Obj> history,int position,int army,int target,BigInteger submitted,BigInteger current) {
        if(submitted==null||current==null)return false;BigInteger expected=submitted;String state="moving";
        for(Obj row:history.subList(position+1,history.size()))if(yes(row.get("ok"))) {
            Obj r=result(row),before=child(r,"war_progress_before"),after=child(r,"war_progress_after");if(before==null||after==null){if(isLifeAdvance(command(row)))return false;continue;}
            BigInteger bd=integer(before,"date_raw"),ad=integer(after,"date_raw");if(!expected.equals(bd)||ad==null||ad.compareTo(bd)<=0)return false;
            Obj b=progressSummaryArmy(before,army),a=progressSummaryArmy(after,army);if(b==null||a==null)return false;
            if(state.equals("sieging")){if(!sieging(b,target)||!sieging(a,target))return false;}
            else if(state.equals("combat")){if(!combat(b,target))return false;if(sieging(a,target))state="sieging";else if(!combat(a,target))return false;}
            else {if(!moving(b,target))return false;if(sieging(a,target))state="sieging";else if(combat(a,target))state="combat";else if(!moving(a,target))return false;}expected=ad;
        }return state.equals("sieging")&&expected.equals(current);
    }
    private static Obj progressSummaryArmy(Obj summary,int army){List<Obj> found=new ArrayList<>();for(Obj war:objectsOrEmpty(summary.get("wars")))for(Obj a:objectsOrEmpty(war.get("player_armies")))if(equalNumber(a.get("army_id"),army))found.add(a);return !found.isEmpty()&&found.stream().allMatch(found.getFirst()::equals)?found.getFirst():null;}
    private static boolean sieging(Obj a,int target){return a!=null&&"sieging".equals(tactical(a))&&equalNumber(a.get("current_province_id"),target)&&nullish(a.get("move_target_province_id"))&&new Arr(List.of()).equals(a.get("route_province_ids"))&&no(a.get("in_combat"))&&no(a.get("retreating"));}
    private static boolean combat(Obj a,int target){return a!=null&&"combat".equals(tactical(a))&&equalNumber(a.get("current_province_id"),target)&&nullish(a.get("move_target_province_id"))&&new Arr(List.of()).equals(a.get("route_province_ids"))&&yes(a.get("in_combat"))&&no(a.get("retreating"));}
    private static boolean moving(Obj a,int target){return a!=null&&Set.of("moving","embarked").contains(tactical(a)==null?"":tactical(a))&&equalNumber(a.get("move_target_province_id"),target)&&a.get("route_province_ids") instanceof Arr route&&!route.items().isEmpty()&&equalNumber(route.items().getLast(),target)&&no(a.get("in_combat"))&&no(a.get("retreating"));}
    public static Optional<Obj> capitalRegroupIntent(List<Obj> history,Obj snapshot,int army,int war) {
        List<Obj> scoped=afterRestore(history);Obj row=null;Move move=null;int position=-1;
        for(int i=scoped.size()-1;i>=0;i--){Obj candidate=scoped.get(i);if(mergeBarrier(candidate,army))return Optional.empty();var parsed=parseMove(command(candidate));if(parsed.isPresent()&&parsed.orElseThrow().armyId()==army){row=candidate;move=parsed.orElseThrow();position=i;break;}}
        if(row==null||!yes(row.get("ok")))return Optional.empty();int target=move.targetProvinceId();Obj result=result(row),action=child(result,"war_action");BigInteger submitted=integer(action,"submitted_date_raw");
        if(action==null||!Set.of("move_submitted","moving","arrived").contains(string(action.get("status"))==null?"":string(action.get("status")))||no(result.get("accepted"))||!optionalIdentity(action,"army_id",army)||!optionalIdentity(action,"target_province_id",target)||submitted==null)return Optional.empty();
        Obj actor=child(snapshot,"played_character"),root=null;Integer origin=null;
        for(int i=position-1;i>=0;i--){Obj previous=scoped.get(i);if(!yes(previous.get("ok")))continue;Obj r=result(previous);
            if(root==null&&"query-campaign-root-context-v1".equals(command(previous))){Obj candidate=child(r,"campaign_root_context"),ready=child(candidate,"readiness");if(named(candidate,"status","available")&&submitted.equals(integer(candidate,"date_raw"))&&Objects.equals(candidate.get("player_character_id"),actor==null?null:actor.get("character_id"))&&equalNumber(candidate.get("capital_province_id"),target)&&ready!=null&&yes(ready.get("ready")))root=candidate;}
            if(origin==null&&parsePreview(command(previous)).equals(Optional.of(new Move(army,target)))){Obj p=child(r,"route_preview");if(named(p,"status","available")&&submitted.equals(integer(p,"previewed_date_raw")))origin=optionalInt(p.get("origin_province_id"));}
        }
        Obj bound=find(snapshot.get("active_wars"),"war_id",war),current=find(snapshot.get("player_armies"),"army_id",army);
        if(root==null||origin==null||bound==null||!named(bound,"player_side","attacker")||!yes(bound.get("player_is_primary_war_leader"))||!new Arr(List.of(number(origin))).equals(bound.get("war_objective_province_ids"))||current==null||!equalNumber(current.get("current_province_id"),target)||!nullish(current.get("move_target_province_id"))||!new Arr(List.of()).equals(current.get("route_province_ids"))||Set.of("combat","retreating").contains(tactical(current)==null?"":tactical(current)))return Optional.empty();
        BigInteger arrival=named(action,"status","arrived")?submitted:null;
        if(arrival==null)for(Obj later:scoped.subList(position+1,scoped.size()))if(isLifeAdvance(command(later))&&yes(later.get("ok"))){Obj after=child(child(later,"result"),"war_progress_after"),w=after==null?null:find(after.get("wars"),"war_id",war),a=w==null?null:find(w.get("player_armies"),"army_id",army);if(integer(after,"date_raw")!=null&&a!=null&&equalNumber(a.get("current_province_id"),target)&&nullish(a.get("move_target_province_id"))&&new Arr(List.of()).equals(a.get("route_province_ids"))){arrival=integer(after,"date_raw");break;}}
        BigInteger now=integer(snapshot,"date_raw");if(now==null)return Optional.empty();if(arrival==null)arrival=now;if(now.compareTo(arrival)<0)return Optional.empty();BigInteger days=now.subtract(arrival).divide(BigInteger.valueOf(24));if(days.compareTo(BigInteger.ONE)>=0)return Optional.empty();
        return Optional.of(obj(f("status",text("holding")),f("army_id",number(army)),f("war_id",number(war)),f("capital_province_id",number(target)),f("arrival_date_raw",number(arrival)),f("elapsed_days",number(days)),f("minimum_days",number(1))));
    }
    public static Optional<Obj> pendingUnsafeRouteHalt(List<Obj> history,Obj snapshot,int army) {
        String step="halt-army-"+army;BigInteger now=integer(snapshot,"date_raw");List<Obj> scoped=afterRestore(history);
        for(int i=scoped.size()-1;i>=0;i--){Obj row=scoped.get(i);String command=command(row);var move=parseMove(command);if(move.isPresent()&&move.orElseThrow().armyId()==army)return Optional.empty();if(!step.equals(command))continue;
            Obj r=result(row),action=child(r,"war_action");BigInteger submitted=integer(action,"submitted_date_raw");
            if(!yes(row.get("ok"))||r==null||!yes(r.get("accepted"))||!named(r,"step",step)||!named(action,"status","halt_submitted")||!equalNumber(action.get("army_id"),army)||submitted==null||now==null||submitted.compareTo(now)>0||!no(action.get("postcondition_verified")))return Optional.empty();
            Obj current=find(snapshot.get("player_armies"),"army_id",army),actor=child(snapshot,"played_character"),diag=child(snapshot,"diagnostics");Value original=action.get("original_route_province_ids");BigInteger nativeNow=integer(snapshot,"native_revision"),nativeThen=integer(action,"submitted_native_revision"),genNow=integer(diag,"connection_generation"),genThen=integer(action,"submitted_connection_generation");
            boolean suffix=current!=null&&actor!=null&&yes(snapshot.get("paused"))&&yes(snapshot.get("map_ready"))&&yes(current.get("controllable"))&&Objects.equals(current.get("owner_character_id"),action.get("owner_character_id"))&&Objects.equals(current.get("owner_character_id"),actor.get("character_id"))&&Objects.equals(current.get("current_province_id"),action.get("original_current_province_id"))&&no(current.get("in_combat"))&&no(current.get("retreating"))&&Set.of("moving","embarked").contains(tactical(current)==null?"":tactical(current))&&named(current,"route_read_status","complete_nonempty")&&positiveRoute(original)&&((Arr)original).items().size()>1;
            if(suffix){var route=((Arr)original).items();Obj hello=child(diag,"hello");suffix=Objects.equals(route.getLast(),action.get("original_move_target_province_id"))&&!route.getFirst().equals(route.getLast())&&new Arr(route.subList(0,1)).equals(current.get("route_province_ids"))&&Objects.equals(current.get("move_target_province_id"),route.getFirst())&&nativeNow!=null&&nativeThen!=null&&nativeNow.compareTo(nativeThen)>0&&genNow!=null&&genThen!=null&&(genThen.equals(genNow)||genThen.compareTo(genNow)<0&&submitted.equals(now)&&diag!=null&&positive(diag.get("bridge_pid"))&&hello!=null&&Objects.equals(hello.get("pid"),diag.get("bridge_pid")))&&action.get("submitted_episode_run_id") instanceof Text episode&&!episode.value().isEmpty()&&Objects.equals(action.get("submitted_episode_run_id"),snapshot.get("episode_run_id"));}
            if(!suffix&&!submitted.equals(now))return Optional.empty();return Optional.of(obj(f("step",text(step)),f("army_id",number(army)),f("submitted_date_raw",number(submitted)),f("history_index",nullable(row.get("index"))),f("suffix_cancellation_observed",new Bool(suffix)),f("current_edge_retained",new Bool(suffix)),f("contact_free_proven",new Bool(false)),f("postcondition_verified",new Bool(false))));
        }return Optional.empty();
    }
    /** Exact query -> raise -> surviving restore/progress chain; a raise ACK alone is insufficient. */
    public static Optional<Obj> nativeRallyHoldBinding(List<Obj> history,Obj snapshot,int war,int army,int province) {
        Obj actor=child(snapshot,"played_character"),current=find(snapshot.get("player_armies"),"army_id",army);BigInteger now=integer(snapshot,"date_raw"),owner=integer(actor,"character_id");Value episode=snapshot.get("episode_run_id");
        if(war<=0||army<0||province<=0||now==null||owner==null||!nullish(episode)&&!(episode instanceof Text)||current==null||!owner.equals(integer(current,"owner_character_id"))||!equalNumber(current.get("current_province_id"),province))return Optional.empty();
        int raisedAt=-1,queriedAt=-1;Obj raisedRow=null,queriedRow=null;
        for(int i=history.size()-1;i>=0;i--)if("raise-troops-default".equals(command(history.get(i)))){raisedAt=i;raisedRow=history.get(i);break;}
        if(raisedRow==null||!yes(raisedRow.get("ok")))return Optional.empty();BigInteger raisedIndex=integer(raisedRow,"index");Obj raised=result(raisedRow),action=child(raised,"war_action");
        List<Obj> raisedArmies=raised==null?List.of():objectsOrEmpty(raised.get("player_armies"));Obj subject=raisedArmies.size()==1?raisedArmies.getFirst():null;
        if(raisedIndex==null||raised==null||!yes(raised.get("accepted"))||!named(raised,"status","submitted")||!named(action,"status","raised")||!new Arr(List.of(number(army))).equals(action.get("raised_army_ids"))||subject==null||!equalNumber(subject.get("army_id"),army)||!owner.equals(integer(subject,"owner_character_id"))||!equalNumber(subject.get("current_province_id"),province)||!yes(subject.get("controllable"))||!"gathering".equals(tactical(subject))||!no(subject.get("in_combat"))||!no(subject.get("retreating"))||!subject.members().containsKey("move_target_province_id")||!nullish(subject.get("move_target_province_id"))||!new Arr(List.of()).equals(subject.get("route_province_ids")))return Optional.empty();
        String queryStep="query-war-termination-options-"+war;
        for(int i=raisedAt-1;i>=0;i--)if(queryStep.equals(command(history.get(i)))){queriedAt=i;queriedRow=history.get(i);break;}
        if(queriedRow==null||!yes(queriedRow.get("ok")))return Optional.empty();BigInteger queriedIndex=integer(queriedRow,"index");Obj queried=result(queriedRow),options=child(queried,"war_termination_options"),context=child(queried,"termination_query_context");
        List<Obj> signatures=context==null?List.of():objectsOrEmpty(context.get("active_war_signature"));Obj signature=signatures.size()==1?signatures.getFirst():null;BigInteger date=integer(context,"queried_date_raw");
        if(queriedIndex==null||queried==null||!yes(queried.get("accepted"))||!named(queried,"status","available")||!Objects.equals(queried.get("queried_episode_run_id"),episode)||options==null||!equalNumber(options.get("war_id"),war)||!named(options,"player_side","defender")||!yes(options.get("player_is_primary_war_leader"))||context==null||!Objects.equals(context.get("queried_episode_run_id"),episode)||!owner.equals(integer(context,"queried_character_id"))||date==null||date.compareTo(now)>0||signature==null||!equalNumber(signature.get("war_id"),war)||!named(signature,"player_side","defender")||!yes(signature.get("player_is_primary_war_leader")))return Optional.empty();
        for(Obj row:history.subList(queriedAt+1,raisedAt))if("restore-checkpoint".equals(command(row))&&!rallyRestore(row,queriedIndex,owner,episode))return Optional.empty();
        List<Value> restored=new ArrayList<>();
        for(Obj row:history.subList(raisedAt+1,history.size())) {
            String step=command(row);if("restore-checkpoint".equals(step)){if(integer(row,"index")==null||!rallyRestore(row,raisedIndex,owner,episode))return Optional.empty();restored.add(row.get("index"));continue;}
            var move=parseMove(step);boolean split=step!=null&&step.equals("split-army-half-"+army),merged=isMerge(step)&&mergeMentions(step,army);
            if("raise-troops-default".equals(step)||move.isPresent()&&move.orElseThrow().armyId()==army||split||merged||("disband-army-"+army).equals(step)||"war-disband-armies".equals(step)||typedAssault(step,"start-assault-")||typedAssault(step,"stop-assault-"))return Optional.empty();
            if(!isLifeAdvance(step))continue;if(!yes(row.get("ok")))return Optional.empty();Obj r=result(row),before=child(r,"war_progress_before"),after=child(r,"war_progress_after");BigInteger bd=integer(before,"date_raw"),ad=integer(after,"date_raw");
            Obj bw=before==null?null:find(before.get("wars"),"war_id",war),aw=after==null?null:find(after.get("wars"),"war_id",war),ba=bw==null?null:find(bw.get("player_armies"),"army_id",army),aa=aw==null?null:find(aw.get("player_armies"),"army_id",army);
            if(bd==null||ad==null||ad.compareTo(bd)<0||!stableRally(ba,army,province)||!stableRally(aa,army,province))return Optional.empty();
        }
        return Optional.of(obj(f("status",text("ready")),f("war_id",number(war)),f("army_id",number(army)),f("owner_character_id",number(owner)),f("rally_province_id",number(province)),f("raise_history_index",number(raisedIndex)),f("raise_snapshot_id",nullable(raised.get("snapshot_id"))),f("raise_revision",nullable(raised.get("revision"))),f("war_query_history_index",number(queriedIndex)),f("war_query_date_raw",number(date)),f("crossed_restore_history_indices",new Arr(restored))));
    }
    private static boolean rallyRestore(Obj row,BigInteger minimum,BigInteger owner,Value episode){Obj r=result(row),c=child(r,"checkpoint");BigInteger index=integer(c,"history_index");return yes(row.get("ok"))&&named(r,"status","restored")&&index!=null&&index.compareTo(minimum)>=0&&owner.equals(integer(c,"episode_character_id"))&&Objects.equals(c.get("episode_run_id"),episode);}
    private static boolean stableRally(Obj a,int army,int province){return a!=null&&equalNumber(a.get("army_id"),army)&&equalNumber(a.get("current_province_id"),province)&&Set.of("gathering","regular").contains(tactical(a)==null?"":tactical(a))&&no(a.get("in_combat"))&&no(a.get("retreating"))&&a.members().containsKey("move_target_province_id")&&nullish(a.get("move_target_province_id"))&&new Arr(List.of()).equals(a.get("route_province_ids"));}
    private static boolean mergeMentions(String step,int army){var m=MERGE.matcher(step);return m.matches()&&(new BigInteger(m.group(1)).intValueExact()==army||new BigInteger(m.group(2)).intValueExact()==army);}
    private static boolean typedAssault(String step,String prefix){return step!=null&&step.startsWith(prefix)&&bounded(step.substring(prefix.length()),true,UNIT_MAX)!=null;}
}
