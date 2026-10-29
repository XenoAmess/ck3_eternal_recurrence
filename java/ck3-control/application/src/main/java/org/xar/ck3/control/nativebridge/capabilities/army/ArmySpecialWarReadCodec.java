package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmySpecialWarReads.*;

/** Single parser for live/cold originals and complete public EXECUTE projection. Raw archive numbers stay numeric. */
public final class ArmySpecialWarReadCodec {
    private ArmySpecialWarReadCodec(){}
    public static Observation decode(Selection selection,PlanningReadReceipt receipt) {
        var result=ArmyNativeReadEvidence.result(selection.context(),receipt);
        // Full Native packet/outbound/custody verification is mandatory in the identical installed Reads port.
        // This application parser has no dependency on native-transport and cannot mint a ReadPermit or Known.
        return decodeToken(selection,new RawJson(bytes(result)));
    }
    public static Observation decodeToken(Selection selection,RawJson originalResult) {
        Kind kind=kind(selection.operation());ObjectNode result=parse(originalResult.bytes());
        equal(result.get("step"),selection.operation().value());yes(result.get("accepted"));equal(result.get("backend_id"),"native-headless");
        BigInteger sequence=u64(result.get("query_sequence")),revision=u64(result.get("snapshot_revision"));
        StrictJson.require(revision.equals(selection.context().nativeRevision()),"special READ native revision differs from original paused frame");
        Optional<RawJson> proof=switch(kind){
            case H2743->Optional.of(new RawJson(bytes(h2743(selection,result))));
            case PRISONERS->Optional.of(new RawJson(bytes(prisoners(selection,result))));
            case BOUND_LOSS->{boundLoss(selection,result);yield Optional.empty();}
        };
        return new Observation(selection,kind,selection.operation(),sequence,revision,originalResult,proof);
    }
    /** Recomputes from original numeric native JSON; never trusts a caller-supplied proof or observation label. */
    public static RawJson fullDriverResult(Observation actual) {
        Observation replay=decodeToken(actual.selection(),actual.nativeResult());
        StrictJson.require(replay.equals(actual),"special READ projection differs from original complete decoder");
        var result=parse(actual.nativeResult().bytes());actual.proof().ifPresent(p->result.set(actual.kind()==Kind.H2743?"h2743_preaction_existing_truce_proof":"war_prisoner_release_pairs_proof",parse(p.bytes())));
        decimal(result,"query_sequence");decimal(result,"snapshot_revision");
        if(actual.kind()==Kind.H2743){decimal(object(result.get("h2743_preaction_existing_truce")),"snapshot_revision");decimal(object(result.get("h2743_preaction_existing_truce_proof")),"snapshot_revision");}
        if(actual.kind()==Kind.BOUND_LOSS){var body=object(result.get("raiktor_war_bound_loss_cleanup"));for(String field:List.of("active_frame","postwar_frame")){var f=object(body.get(field));decimal(f,"snapshot_revision");decimal(f,"native_revision");}decimal(object(body.get("soldiers")),"observed_current_soldiers");for(var r:body.get("regiments"))decimal((ObjectNode)r,"current_soldiers");}
        safe(result);return new RawJson(StrictJson.canonical(result));
    }
    private static ObjectNode h2743(Selection s,ObjectNode result) {
        closed(result,"step","accepted","query_sequence","snapshot_revision","h2743_preaction_existing_truce","backend_id");
        var v=closed(result.get("h2743_preaction_existing_truce"),"schema","backend_id","war_id","owner_character_id","toward_character_id","episode_id_claim","episode_authenticated_here","checkpoint_sha256_claim","checkpoint_bytes_authenticated_here","status","snapshot_revision","date_raw","same_frame_stable","preaction_existing_expiry_observable","preaction_existing_expiry_date_raw","post_surrender_actual_expiry_date_raw","script_candidate_days","effect_projection_complete","material_complete","recommended_outcome","action_literal","unavailable_reason");
        equal(v.get("schema"),"xar.ck3.h2743_preaction_existing_truce.v1");equal(v.get("backend_id"),"ck3-1.19.0.6-native-h2743-existing-truce-v1");
        number(v,"war_id",16777231);number(v,"owner_character_id",30097);number(v,"toward_character_id",29829);number(v,"date_raw",53217264);
        equal(v.get("episode_id_claim"),EPISODE);equal(v.get("checkpoint_sha256_claim"),CHECKPOINT);
        for(String key:List.of("episode_authenticated_here","checkpoint_bytes_authenticated_here","effect_projection_complete","material_complete"))no(v.get(key));
        for(String key:List.of("post_surrender_actual_expiry_date_raw","script_candidate_days","recommended_outcome","action_literal"))nil(v.get(key));
        StrictJson.require(u64(v.get("snapshot_revision")).equals(s.context().nativeRevision()),"H2743 payload revision differs");
        String status=text(v.get("status"));switch(status){
            case "existing_truce"->{yes(v.get("same_frame_stable"));yes(v.get("preaction_existing_expiry_observable"));StrictJson.require(i32(v.get("preaction_existing_expiry_date_raw"))>53217264,"H2743 expiry is not after current date");nil(v.get("unavailable_reason"));}
            case "no_existing_truce"->{yes(v.get("same_frame_stable"));no(v.get("preaction_existing_expiry_observable"));nil(v.get("preaction_existing_expiry_date_raw"));equal(v.get("unavailable_reason"),"no_existing_truce");}
            case "unavailable"->{no(v.get("same_frame_stable"));no(v.get("preaction_existing_expiry_observable"));nil(v.get("preaction_existing_expiry_date_raw"));StrictJson.text(text(v.get("unavailable_reason")));}
            default->throw new IllegalArgumentException("unknown H2743 status");}
        return v;
    }
    private static ObjectNode prisoners(Selection s,ObjectNode result) {
        // The original Python accepts producer extension fields; preserve them, while requiring all original mandatory facts.
        equal(result.get("status"),"available");yes(result.get("read_only"));var v=object(result.get("war_prisoner_release_pairs_v1"));
        number(v,"war_id",warId(s));equal(v.get("date_raw"),s.context().dateRaw());nonnegative(v.get("active_casus_belli_database_index"));nonempty(v.get("active_casus_belli_key"));
        int attacker=positiveId(v.get("primary_attacker_character_id")),defender=positiveId(v.get("primary_defender_character_id"));
        Set<Integer> attackers=ids(v.get("attacker_participant_ids")),defenders=ids(v.get("defender_participant_ids"));
        var ac=array(v.get("attacker_release_candidate_ids"),ArmySpecialWarReadCodec::positiveId);var dc=array(v.get("defender_release_candidate_ids"),ArmySpecialWarReadCodec::positiveId);
        StrictJson.require(new HashSet<>(ac).size()==ac.size()&&new HashSet<>(dc).size()==dc.size()&&!ac.isEmpty()&&!dc.isEmpty()&&ac.size()<=4&&dc.size()<=4
            &&ac.getFirst()==attacker&&dc.getFirst()==defender&&attackers.contains(attacker)&&defenders.contains(defender)&&java.util.Collections.disjoint(attackers,defenders),"incomplete native participant/successor scan");
        yes(v.get("same_frame_stable"));yes(v.get("full_participant_scan"));yes(v.get("primary_and_first_three_successors_scanned"));
        var pairs=v.get("release_pairs");StrictJson.require(pairs!=null&&pairs.isArray(),"release pairs absent");Set<String> seen=new HashSet<>();
        for(var pair:pairs){var row=object(pair);int jailer=positiveId(row.get("jailer_character_id")),prisoner=positiveId(row.get("prisoner_character_id"));
            StrictJson.require(seen.add(jailer+":"+prisoner)&&((attackers.contains(jailer)&&dc.contains(prisoner))||(defenders.contains(jailer)&&ac.contains(prisoner))),"release pair contradicts full scan");text(row.get("reason"));}
        return v;
    }
    private static void boundLoss(Selection s,ObjectNode result) {
        closed(result,"step","accepted","query_sequence","snapshot_revision","raiktor_war_bound_loss_cleanup","backend_id");
        var v=closed(result.get("raiktor_war_bound_loss_cleanup"),"schema_version","backend_id","status","failure","active_frame","postwar_frame","owner_character_id","war_id","source_attribution","soldiers","cleanup","regiments","readiness");
        number(v,"schema_version",1);equal(v.get("backend_id"),"ck3-1.19.0.6-native-raiktor-war-bound-regiment-v1");equal(v.get("status"),"generic_war_bound_visible_source_unattributed");nil(v.get("failure"));
        int war=fullId(v.get("war_id")),owner=fullId(v.get("owner_character_id"));StrictJson.require(war==warId(s)&&BigInteger.valueOf(owner).equals(s.context().playerId()),"cleanup war/player differs");
        var a=closed(v.get("active_frame"),"snapshot_revision","native_revision","date_raw","paused","war_id","active_casus_belli_database_index","active_casus_belli_key","primary_attacker_character_id","primary_defender_character_id");
        yes(a.get("paused"));number(a,"war_id",war);number(a,"primary_attacker_character_id",owner);fullId(a.get("primary_defender_character_id"));nonnegative(a.get("active_casus_belli_database_index"));equal(a.get("active_casus_belli_key"),"raiktor_claim_cb");
        StrictJson.require(u64(a.get("snapshot_revision")).equals(u64(a.get("native_revision"))),"native active baseline revisions differ");i32(a.get("date_raw"));
        var p=closed(v.get("postwar_frame"),"snapshot_revision","native_revision","date_raw","paused","frozen_war_id","frozen_war_absent_from_active_wars");
        yes(p.get("paused"));yes(p.get("frozen_war_absent_from_active_wars"));number(p,"frozen_war_id",war);
        StrictJson.require(u64(p.get("snapshot_revision")).equals(s.context().nativeRevision())&&u64(p.get("native_revision")).equals(s.context().nativeRevision())&&BigInteger.valueOf(i32(p.get("date_raw"))).equals(s.context().dateRaw()),"cleanup post frame differs from actual original");
        var wars=org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(s.original().observations().snapshot()).get("active_wars");StrictJson.require(wars!=null&&wars.isArray(),"actual postwar roster absent");for(var current:wars)StrictJson.require(!current.path("war_id").isIntegralNumber()||!current.path("war_id").bigIntegerValue().equals(BigInteger.valueOf(war)),"frozen war remains active");
        var source=closed(v.get("source_attribution"),"mode","authored_candidate_name","authored_spawn_army_count","authored_soldiers_per_army","authored_total_soldiers");
        equal(source.get("mode"),"authored_candidate_only");equal(source.get("authored_candidate_name"),"norman_highwaymen");number(source,"authored_spawn_army_count",6);number(source,"authored_soldiers_per_army",500);number(source,"authored_total_soldiers",3000);
        var soldiers=closed(v.get("soldiers"),"current_soldiers_observable","observed_current_soldiers","pre_soldiers_observable","observed_pre_soldiers","proven_soldier_loss_observable","proven_soldiers_lost");
        yes(soldiers.get("current_soldiers_observable"));no(soldiers.get("pre_soldiers_observable"));no(soldiers.get("proven_soldier_loss_observable"));nil(soldiers.get("observed_pre_soldiers"));nil(soldiers.get("proven_soldiers_lost"));long total=nonnegative64(soldiers.get("observed_current_soldiers"));
        var cleanup=closed(v.get("cleanup"),"observable","status");yes(cleanup.get("observable"));String cleanupStatus=state(cleanup.get("status"));
        var regiments=v.get("regiments");StrictJson.require(regiments!=null&&regiments.isArray()&&!regiments.isEmpty(),"cleanup regiments absent");
        Set<Integer> persistentIds=new HashSet<>(),currentIds=new HashSet<>();long computed=0;boolean anyAlive=false;
        for(var raw:regiments){var r=closed(raw,"persistent_regiment_id","bound_war_id","war_keep_on_attacker_victory","current_soldiers","postwar_persistent_state","composition_rows");
            StrictJson.require(persistentIds.add(fullId(r.get("persistent_regiment_id"))),"duplicate persistent regiment generation");number(r,"bound_war_id",war);no(r.get("war_keep_on_attacker_victory"));
            long regimentTotal=nonnegative64(r.get("current_soldiers"));String persistent=state(r.get("postwar_persistent_state"));anyAlive|=persistent.equals("still_alive");
            var rows=r.get("composition_rows");StrictJson.require(rows!=null&&rows.isArray()&&rows.size()==7,"seven composition rows required");long sum=0;int ordinal=0;
            for(var rowRaw:rows){var row=closed(rowRaw,"composition_ordinal","current_army_regiment_id","raised_carmy_id","current_soldiers","current_army_regiment_state","raised_carmy_state","frozen_carmy_roster_evidence");number(row,"composition_ordinal",ordinal++);
                if(row.get("current_army_regiment_id").isNull()){nil(row.get("raised_carmy_id"));nil(row.get("current_soldiers"));equal(row.get("current_army_regiment_state"),"not_present");equal(row.get("raised_carmy_state"),"not_present");equal(row.get("frozen_carmy_roster_evidence"),"not_present");continue;}
                StrictJson.require(currentIds.add(fullId(row.get("current_army_regiment_id"))),"duplicate current regiment generation");fullId(row.get("raised_carmy_id"));sum=Math.addExact(sum,nonnegative(row.get("current_soldiers")));
                String current=state(row.get("current_army_regiment_state")),army=state(row.get("raised_carmy_state")),roster=text(row.get("frozen_carmy_roster_evidence"));
                StrictJson.require(army.equals("destroyed")?roster.equals("frozen_army_destroyed"):Set.of("detached","still_attached").contains(roster),"cleanup roster evidence disagrees with army state");
                StrictJson.require(!current.equals("destroyed")||!roster.equals("still_attached"),"destroyed regiment cannot remain attached");anyAlive|=current.equals("still_alive");}
            StrictJson.require(sum==regimentTotal,"regiment soldier sum differs");computed=Math.addExact(computed,regimentTotal);}
        StrictJson.require(computed==total&&cleanupStatus.equals(anyAlive?"still_alive":"destroyed"),"cleanup total/status differs from exact rows");
        var ready=closed(v.get("readiness"),"exact_raiktor_war_context_ready","generic_war_bound_identity_ready","current_soldiers_ready","postwar_cleanup_ready","source_specific_attribution_ready","pre_soldiers_ready","proven_soldier_loss_ready","independently_visible_value_ready","raiktor_source_specific_domain_ready");
        for(String key:List.of("exact_raiktor_war_context_ready","generic_war_bound_identity_ready","current_soldiers_ready","postwar_cleanup_ready","independently_visible_value_ready"))yes(ready.get(key));
        for(String key:List.of("source_specific_attribution_ready","pre_soldiers_ready","proven_soldier_loss_ready","raiktor_source_specific_domain_ready"))no(ready.get(key));
    }
    private static String state(JsonNode n){String state=text(n);StrictJson.require(Set.of("destroyed","still_alive").contains(state),"unknown exact cleanup state");return state;}
    private static BigInteger u64(JsonNode n){return StrictJson.integer(n,BigInteger.ONE,StrictJson.UINT64_MAX);}
    private static int positiveId(JsonNode n){int id=i32(n);StrictJson.require(id>0,"positive full native ID required");return id;}
    private static int fullId(JsonNode n){int id=i32(n);StrictJson.require(id!=-1,"invalid full native ID sentinel");return id;}
    private static Set<Integer> ids(JsonNode n){var ids=array(n,ArmySpecialWarReadCodec::positiveId);Set<Integer> result=new HashSet<>(ids);StrictJson.require(result.size()==ids.size(),"duplicate full native participant ID");return Set.copyOf(result);}
    private static long nonnegative64(JsonNode n){return StrictJson.integer(n,BigInteger.ZERO,BigInteger.valueOf(Long.MAX_VALUE)).longValueExact();}
    private static void nil(JsonNode n){StrictJson.require(n!=null&&n.isNull(),"explicit unavailable null required");}
    private static void number(ObjectNode n,String field,long expected){StrictJson.require(integer(n.get(field)).equals(BigInteger.valueOf(expected)),"native field differs: "+field);}
    private static void decimal(ObjectNode n,String field){n.put(field,integer(n.get(field)).toString());}
    private static void safe(JsonNode n){if(n.isIntegralNumber())StrictJson.require(n.bigIntegerValue().abs().compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,"undeclared unsafe public integer");if(n.isContainerNode())for(var child:n)safe(child);}
}
