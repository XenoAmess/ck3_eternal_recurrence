package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.TreeSet;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original21566..21647,22027..22360. Halt ACK and independent suffix observation remain distinct. */
final class WarContactHalts {
    private WarContactHalts() {}
    private static Obj child(Obj obj,String name){return obj!=null&&obj.get(name) instanceof Obj o?o:null;}
    private static boolean eq(Obj o,String key,Value v){return o!=null&&Objects.equals(o.get(key),v);}
    private static String halt(Army army){return "halt-army-"+army.id();}
    private static boolean has(PlanningRequest request,String step){return request.observations().actionSteps().contains(new org.xar.ck3.control.application.action.OperationKey(step));}
    static Optional<Obj> pending(PlanningRequest request,Army army) {
        Obj s=request.observations().snapshot();Integer date=optionalInt(s.get("date_raw"));
        List<Obj> history=afterRestore(request.observations().history());
        String step=halt(army),movePrefix="move-army-"+army.id()+"-to-";
        for(int i=history.size()-1;i>=0;i--) {
            Obj row=history.get(i);String command=command(row);
            if(command!=null&&command.startsWith(movePrefix))return Optional.empty();
            if(!step.equals(command))continue;
            Obj r=result(row),action=child(r,"war_action");
            if(eq(r,"business_submission_may_have_applied",new Bool(true))&&!eq(r,"accepted",new Bool(true)))
                return Optional.of(obj(f("step",text(step)),f("army_id",number(army.id())),f("history_index",nullable(row.get("index"))),
                        f("unknown_submission",new Bool(true)),f("suffix_cancellation_observed",new Bool(false)),f("postcondition_verified",new Bool(false))));
            Integer submitted=action==null?null:optionalInt(action.get("submitted_date_raw"));
            if(!yes(row.get("ok"))||!eq(r,"accepted",new Bool(true))||!eq(r,"step",text(step))
                    ||!eq(action,"status",text("halt_submitted"))||!eq(action,"army_id",number(army.id()))
                    ||submitted==null||date==null||submitted>date||!eq(action,"postcondition_verified",new Bool(false)))return Optional.empty();
            Obj diag=child(s,"diagnostics"),player=child(s,"played_character");
            var old=route(action.get("original_route_province_ids"));
            BigInteger oldRevision=optionalInteger(action.get("submitted_native_revision")),nowRevision=optionalInteger(s.get("native_revision"));
            BigInteger oldGeneration=optionalInteger(action.get("submitted_connection_generation")),generation=diag==null?null:optionalInteger(diag.get("connection_generation"));
            Obj hello=child(diag,"hello");Integer pid=diag==null?null:optionalInt(diag.get("bridge_pid"));
            boolean sameConnection=oldGeneration!=null&&generation!=null&&(oldGeneration.equals(generation)
                    ||oldGeneration.compareTo(generation)<0&&submitted.equals(date)&&pid!=null&&pid>0&&eq(hello,"pid",number(pid)));
            boolean suffix=player!=null&&yes(s.get("paused"))&&yes(s.get("map_ready"))&&army.controllable()
                    &&Objects.equals(army.raw().get("owner_character_id"),action.get("owner_character_id"))
                    &&Objects.equals(action.get("owner_character_id"),player.get("character_id"))
                    &&Objects.equals(army.raw().get("current_province_id"),action.get("original_current_province_id"))
                    &&Boolean.FALSE.equals(army.inCombat())&&Boolean.FALSE.equals(army.retreating())
                    &&List.of("moving","embarked").contains(Objects.toString(army.tacticalState(),""))
                    &&"complete_nonempty".equals(army.routeReadStatus())&&old.filter(r0->r0.size()>1).isPresent()
                    &&old.orElseThrow().getLast().equals(optionalInt(action.get("original_move_target_province_id")))
                    &&!old.orElseThrow().getFirst().equals(old.orElseThrow().getLast())
                    &&army.route().filter(r0->r0.equals(old.orElseThrow().subList(0,1))).isPresent()
                    &&Objects.equals(army.target(),old.orElseThrow().getFirst())&&oldRevision!=null&&nowRevision!=null&&nowRevision.compareTo(oldRevision)>0
                    &&sameConnection&&action.get("submitted_episode_run_id") instanceof Text e&&!e.value().isEmpty()
                    &&e.equals(s.get("episode_run_id"));
            if(!suffix&&!submitted.equals(date))return Optional.empty();
            return Optional.of(obj(f("step",text(step)),f("army_id",number(army.id())),f("submitted_date_raw",number(submitted)),
                    f("history_index",nullable(row.get("index"))),f("suffix_cancellation_observed",new Bool(suffix)),
                    f("current_edge_retained",new Bool(suffix)),f("contact_free_proven",new Bool(false)),f("postcondition_verified",new Bool(false))));
        }
        return Optional.empty();
    }
    private static boolean base(PlanningRequest request,Army army) {
        Obj s=request.observations().snapshot(),player=child(s,"played_character"),hint=child(s,"top_exclusive_modal_choice_hint");
        return yes(s.get("paused"))&&yes(s.get("map_ready"))&&s.get("active_event")==Nil.INSTANCE
                &&s.get("pending_character_interaction")==Nil.INSTANCE&&!eq(hint,"status",text("present"))
                &&player!=null&&yes(player.get("alive"))&&army.controllable()
                &&Objects.equals(army.raw().get("owner_character_id"),player.get("character_id"))
                &&Boolean.FALSE.equals(army.inCombat())&&Boolean.FALSE.equals(army.retreating())
                &&"complete_nonempty".equals(army.routeReadStatus())&&army.route().filter(r->!r.isEmpty()&&r.getLast().equals(army.target())).isPresent();
    }
    static Optional<Obj> unavailableWatch(PlanningRequest request,Army army,MilitaryTimeline.Query query,
            Optional<Obj> pending,Obj attempt,Arr summaries) {
        if(!base(request,army)||!new Text("current_frame").equals(attempt.get("scope_status"))
                ||!new Text("unavailable").equals(attempt.get("status"))||!no(attempt.get("ok")))return Optional.empty();
        List<Obj> rows=afterRestore(request.observations().history());Obj nativeEvidence=null;
        for(int i=rows.size()-1;i>=0;i--)if(query.step().equals(command(rows.get(i)))){nativeEvidence=child(result(rows.get(i)),"readonly_unavailable_evidence");break;}
        Obj raw=child(nativeEvidence,"native_command_result");
        if(raw==null||!no(raw.get("ok"))||!eq(raw,"error",text("CK3 route arrival timeline is unavailable")))return Optional.empty();
        String state=army.tacticalState(),step=halt(army);boolean oneDay=has(request,"life-advance-one-day");
        Obj s=request.observations().snapshot();
        Obj watch=obj(f("army_id",number(army.id())),f("current_province_id",army.current()==null?Nil.INSTANCE:number(army.current())),
                f("target_province_id",number(query.targetProvinceId())),f("route_province_ids",numbers(army.route().orElseThrow())),
                f("query_step",text(query.step())),f("native_request_id",nullable(nativeEvidence.get("native_request_id"))),
                f("native_error",raw.get("error")),f("source_date_raw",s.get("date_raw")),f("source_native_revision",s.get("native_revision")),
                f("contact_free_proven",new Bool(false)),f("contact_status",text("unknown")),
                f("movement_resubmitted",new Bool(false)),f("war_or_material_credit",new Bool(false)));
        if("embarked".equals(state)&&Integer.valueOf(4).equals(army.stateCode())&&pending.isEmpty()&&oneDay)
            return Optional.of(plan("native_war_embarked_route_timeline_unavailable_one_day_watch","life-advance-one-day",
                    "the exact arrival reader is unavailable for the current committed sea route; observe one existing native-stopped day and re-read army/combat state; contact remains unknown",
                    obj(f("route_timeline_unavailable_watch",watch),f("contact_query_attempt",attempt)),summaries));
        if(!"moving".equals(state)||!Integer.valueOf(7).equals(army.stateCode()))return Optional.empty();
        TreeSet<Integer> completeHostiles=new TreeSet<>();
        for(Obj war:wars(request)) {
            require(war.get("enemy_armies") instanceof Arr,"land watch requires complete enemy roster");
            for(Obj enemy:MilitaryPlanInputs.rows(war.get("enemy_armies")))if(!yes(enemy.get("retreating")))completeHostiles.add(id(enemy.get("army_id")));
        }
        if(!List.copyOf(completeHostiles).equals(query.hostileIds()))return Optional.empty();
        if(pending.isEmpty()) {
            var rejected=validatorDeferred(request,army);
            if(rejected.isPresent()&&oneDay)return Optional.of(plan("native_war_land_halt_validator_rejected_one_day_watch","life-advance-one-day",
                    "Native rejected Halt before queue submission and a fresh readback still shows the same committed land route; observe one exact day of contact risk, then replan without crediting a stop or victory",
                    obj(f("route_timeline_unavailable_watch",merge(watch,obj(f("halt_rejection",rejected.orElseThrow()),
                            f("halt_accepted",new Bool(false)),f("offensive_combat_permission",new Bool(false))))),f("contact_query_attempt",attempt)),summaries));
            for(Obj row:rows)if(step.equals(command(row))) {
                Obj r=result(row),e=child(r,"halt_rejection_evidence"),frame=child(e,"observed_frame");
                if(no(row.get("ok"))||eq(r,"schema",text("xar.halt-army-validator-deferred/v1"))
                        &&frame!=null&&Objects.equals(frame.get("date_raw"),s.get("date_raw")))return Optional.empty();
            }
            if(!has(request,step)||army.route().orElseThrow().size()<2)return Optional.empty();
            return Optional.of(plan("native_war_land_route_timeline_unavailable_halt_submit",step,
                    "the exact full-hostile timeline failed for a committed land route; submit native Halt to cancel the future tail before any time advance",
                    obj(f("halt_intent",obj(f("army_id",number(army.id())),f("current_province_id",army.current()==null?Nil.INSTANCE:number(army.current())),
                            f("original_move_target_province_id",number(query.targetProvinceId())),f("original_route_province_ids",numbers(army.route().orElseThrow())),
                            f("postcondition_required",text("fresh_route_empty_or_verified_retained_first_edge")),f("contact_free_proven",new Bool(false)))),
                            f("contact_query_attempt",attempt)),summaries));
        }
        Obj p=pending.orElseThrow();
        if(oneDay&&eq(p,"army_id",number(army.id()))&&yes(p.get("suffix_cancellation_observed"))&&yes(p.get("current_edge_retained"))
                &&no(p.get("postcondition_verified"))&&army.route().orElseThrow().size()==1)
            return Optional.of(plan("native_war_land_retained_route_timeline_unavailable_one_day_watch","life-advance-one-day",
                    "native Halt independently canceled the future tail but CK3 retained the first land edge; observe one exact native-stopped day, then re-read contact and battle state; contact remains unknown",
                    obj(f("route_timeline_unavailable_watch",merge(watch,obj(f("halt_submission",p),f("offensive_combat_permission",new Bool(false))))),
                            f("contact_query_attempt",attempt)),summaries));
        return Optional.empty();
    }
    private static Optional<Obj> validatorDeferred(PlanningRequest request,Army army) {
        Obj s=request.observations().snapshot(),diag=child(s,"diagnostics"),actor=child(s,"played_character");
        if(diag==null||actor==null)return Optional.empty();
        Obj frame=obj(f("snapshot_id",s.get("snapshot_id")),f("revision",s.get("revision")),f("native_revision",s.get("native_revision")),
                f("date_raw",s.get("date_raw")),f("actor_character_id",actor.get("character_id")),f("episode_run_id",s.get("episode_run_id")),
                f("bridge_pid",nullable(diag.get("bridge_pid"))),f("connection_generation",nullable(diag.get("connection_generation"))));
        for(String key:List.of("revision","native_revision","date_raw","actor_character_id","bridge_pid","connection_generation"))
            if(optionalInteger(frame.get(key))==null)return Optional.empty();
        if(optionalInteger(frame.get("bridge_pid")).signum()<=0)return Optional.empty();
        List<Obj> rows=afterRestore(request.observations().history());
        for(int i=rows.size()-1;i>=0;i--) {
            Obj row=rows.get(i);String step=halt(army);if(!step.equals(command(row)))continue;
            Obj r=result(row),action=child(r,"war_action"),e=child(r,"halt_rejection_evidence"),nr=child(e,"native_request"),response=child(e,"native_command_result");
            Value rid=e==null?null:e.get("native_request_id");
            if(!yes(row.get("ok"))||!eq(r,"schema",text("xar.halt-army-validator-deferred/v1"))||!eq(r,"step",text(step))
                    ||!eq(r,"accepted",new Bool(false))||!eq(r,"status",text("deferred"))||!eq(r,"business_submission",new Bool(false))
                    ||!eq(r,"replay_allowed",new Bool(false))||!eq(action,"status",text("halt_validator_rejected_current_route_retained"))
                    ||!eq(action,"army_id",number(army.id()))||!eq(action,"reason",text("native_halt_validator_rejected"))
                    ||!eq(action,"contact_free_proven",new Bool(false))||!eq(action,"current_province_id",army.raw().get("current_province_id"))
                    ||!eq(action,"move_target_province_id",army.raw().get("move_target_province_id"))
                    ||!eq(action,"route_province_ids",army.raw().get("route_province_ids"))||!eq(e,"observed_frame",frame)
                    ||!(rid instanceof Text t)||t.value().isEmpty()||!eq(nr,"request_id",rid)||!eq(nr,"step",text(step))
                    ||!eq(nr,"type",text("execute_step"))||!eq(response,"request_id",rid)||!eq(response,"type",text("command_result"))
                    ||!Objects.equals(response.get("protocol_version"),nr.get("protocol_version"))||!eq(response,"ok",new Bool(false))
                    ||!eq(response,"error",text("CK3 halt-army command validation failed")))return Optional.empty();
            return Optional.of(obj(f("history_index",nullable(row.get("index"))),f("native_request_id",rid),
                    f("native_error",response.get("error")),f("observed_frame",frame)));
        }
        return Optional.empty();
    }
    static Optional<Obj> unsafeHalt(PlanningRequest request,Army army,Obj audit,MilitaryTimeline.Horizon horizon,Arr summaries) {
        Obj s=request.observations().snapshot();
        if(!base(request,army)||!has(request,halt(army))
                ||!List.of("moving","embarked").contains(Objects.toString(army.tacticalState(),""))||horizon.oneDayFree()
                ||horizon.subjectId()!=army.id()||!Objects.equals(army.target(),horizon.targetProvinceId())
                ||!eq(audit,"contact_policy",text("blocked_without_qualified_combat_permission")))return Optional.empty();
        return Optional.of(plan("native_war_unsafe_route_halt_submit",halt(army),
                "the fresh full-hostile horizon shows committed contact without qualified combat permission; submit the native halt before any time advance",
                obj(f("halt_intent",obj(f("army_id",number(army.id())),f("current_province_id",army.current()==null?Nil.INSTANCE:number(army.current())),
                        f("unsafe_move_target_province_id",number(horizon.targetProvinceId())),
                        f("postcondition_required",text("fresh_route_empty_and_move_target_none")))),f("route_audit",audit)),summaries));
    }
    static Obj plan(String phase,String step,String reason,Obj detail,Arr summaries) {
        return merge(detail,obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",text(step)),
                f("reason",text(reason)),f("active_wars",summaries)));
    }
}

