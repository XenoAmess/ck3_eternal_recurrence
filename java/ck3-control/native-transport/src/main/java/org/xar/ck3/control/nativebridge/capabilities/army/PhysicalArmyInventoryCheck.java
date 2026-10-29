package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Existing diagnostic-only native mailbox proof. Its historical episode/build scope is intentionally retained. */
public final class PhysicalArmyInventoryCheck {
    private PhysicalArmyInventoryCheck() {}
    private static final Set<String> KEYS=Set.of("source_build","status","date_raw","war_id","subject_army_id","native_revision","query_sequence","mailbox_pump_epoch","mailbox_thread_id","mailbox_date_raw","mailbox_paused","same_source_across_route","storage_capacity","slots_scanned","empty_slots","canonical_units","invalid_id_slots","noncanonical_slots","unresolved_slots","player_army_ids","allied_army_ids","hostile_army_ids","contact_hostile_army_ids","retreating_hostile_army_ids","units");
    private static final Set<String> UNIT=Set.of("army_id","owner_character_id","current_province_id","route_province_ids","route_read_status","route_source_count","army_state_code","in_combat","retreating","controllable","war_side");
    public record Check(boolean valid,String reason,List<Integer> physicalHostiles,List<Integer> contactHostiles) {
        public Check {physicalHostiles=List.copyOf(physicalHostiles);contactHostiles=List.copyOf(contactHostiles);}
        public Obj json(){return new Obj(java.util.Map.of("valid",new Bool(valid),"reason",new Text(reason),"date_or_action_authorized",new Bool(false)));}
    }
    private static Check red(String reason){return new Check(false,reason,List.of(),List.of());}
    public static Check mailbox(Obj original,Obj before,Obj after,Obj horizon,BigInteger sequence,int subject,List<Integer> requested) {
        if(!original.members().keySet().equals(KEYS))return red("mailbox_receipt_missing_or_extra_fields");
        List<Obj> units;
        try{units=rows(original.get("units"));if(units.stream().anyMatch(row->!row.members().keySet().equals(UNIT)))return red("mailbox_unit_rows_malformed");}
        catch(IllegalArgumentException invalid){return red("mailbox_unit_rows_malformed");}
        if(!yes(before,"map_ready")||!yes(after,"map_ready")||!yes(before,"paused")||!yes(after,"paused")
                ||!positive(original.get("mailbox_pump_epoch"))||!positive(original.get("mailbox_thread_id"))||!yes(original,"mailbox_paused")||!yes(original,"same_source_across_route")
                ||!sameInt(original.get("mailbox_date_raw"),before.get("date_raw"))||!new IntegerValue(sequence).equals(original.get("query_sequence"))
                ||!sameInt(original.get("native_revision"),before.get("native_revision")))return red("mailbox_source_or_frame_mismatch");
        for(String field:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id","played_character","active_wars","player_armies","map_ready","paused","episode_character_id","active_event","pending_character_interaction","route_contact_horizon_supported"))
            if(!before.members().containsKey(field)||!after.members().containsKey(field)||!before.get(field).equals(after.get(field)))return red("public_frame_changed");
        Set<String> capabilities=new HashSet<>(before.members().keySet());capabilities.addAll(after.members().keySet());
        for(String field:capabilities)if(field.endsWith("_supported")||field.equals("capabilities"))if(!before.members().containsKey(field)||!after.members().containsKey(field)||!before.get(field).equals(after.get(field)))return red("capability_frame_changed");
        if(!(before.get("played_character") instanceof Obj actorValue)||!positive(actorValue.get("character_id")))return red("played_character_missing");
        var actor=OpportunityJson.object(before.get("played_character"),"actor");
        if(new Text("native-29829-2bc2d599f7f9").equals(before.get("episode_run_id"))&&!integer(29829).equals(actor.get("character_id")))return red("h3937_actor_binding_mismatch");
        if(!actor.get("character_id").equals(before.get("episode_character_id")))return red("episode_actor_binding_mismatch");
        List<Obj> players;
        try{players=rows(before.get("player_armies"));}catch(IllegalArgumentException invalid){return red("played_character_subject_mismatch");}
        var subjectRows=players.stream().filter(row->integer(subject).equals(row.get("army_id"))).toList();
        if(subjectRows.size()!=1||!actor.get("character_id").equals(subjectRows.getFirst().get("owner_character_id"))||!yes(subjectRows.getFirst(),"controllable"))return red("played_character_subject_mismatch");
        if(!(before.get("diagnostics") instanceof Obj)||!(after.get("diagnostics") instanceof Obj))return red("connection_generation_missing");
        Obj first=OpportunityJson.object(before.get("diagnostics"),"diagnostics"),last=OpportunityJson.object(after.get("diagnostics"),"diagnostics");
        if(!positive(first.get("connection_generation"))||!sameInt(first.get("connection_generation"),last.get("connection_generation")))return red("connection_generation_mismatch");
        if(!(before.get("snapshot_id") instanceof Text snapshot)||snapshot.value().isEmpty()||!(before.get("episode_run_id") instanceof Text episode)||episode.value().isEmpty()||!positive(before.get("revision"))||!positive(before.get("native_revision")))return red("public_frame_token_missing");
        if(!new Text("native-29829-2bc2d599f7f9").equals(before.get("episode_run_id"))||subject!=83886367)return red("h3937_episode_or_subject_mismatch");
        List<Obj> wars;try{wars=rows(before.get("active_wars"));}catch(IllegalArgumentException invalid){return red("war_scope_ambiguous");}
        if(wars.size()!=1)return red("war_scope_ambiguous");Obj war=wars.getFirst();if(!positive(war.get("war_id")))return red("war_id_missing");if(!integer(16777231).equals(war.get("war_id")))return red("h3937_war_mismatch");
        try {
            List<Integer> publishedPlayer=roster(players),publishedAllied=roster(rows(war.get("allied_armies"))),publishedEnemy=roster(rows(war.get("enemy_armies")));
            List<Integer> contactResult=ids(horizon.get("hostile_army_ids"));
            return shape(original,before,war,subject,units,publishedPlayer,publishedAllied,publishedEnemy,requested,contactResult);
        }catch(IllegalArgumentException invalid){return red("published_army_roster_malformed");}
    }
    private static Check shape(Obj receipt,Obj before,Obj war,int subject,List<Obj> units,List<Integer> publishedPlayer,List<Integer> publishedAllied,List<Integer> publishedEnemy,List<Integer> requested,List<Integer> contactResult) {
        if(!new Text("complete").equals(receipt.get("status")))return red("inventory_unavailable_or_partial");if(!new Text("CK3 1.19.0.6").equals(receipt.get("source_build")))return red("source_build_mismatch");
        for(String field:List.of("date_raw","native_revision"))if(!sameInt(receipt.get(field),before.get(field)))return red(field+"_mismatch");
        if(!sameInt(receipt.get("war_id"),war.get("war_id")))return red("war_id_mismatch");if(!integer(subject).equals(receipt.get("subject_army_id")))return red("subject_army_id_mismatch");
        for(String field:List.of("storage_capacity","slots_scanned","empty_slots","canonical_units","invalid_id_slots","noncanonical_slots","unresolved_slots"))if(!nonnegative(receipt.get(field)))return red("scan_counts_invalid");
        BigInteger capacity=number(receipt.get("storage_capacity"));if(capacity.signum()<=0||capacity.compareTo(BigInteger.valueOf(1000000))>0||!capacity.equals(number(receipt.get("slots_scanned")))
                ||!capacity.equals(number(receipt.get("empty_slots")).add(number(receipt.get("canonical_units"))).add(number(receipt.get("invalid_id_slots"))).add(number(receipt.get("noncanonical_slots"))))
                ||number(receipt.get("invalid_id_slots")).signum()!=0||number(receipt.get("noncanonical_slots")).signum()!=0||number(receipt.get("unresolved_slots")).signum()!=0)return red("scan_incomplete_or_unresolved");
        if(!BigInteger.valueOf(units.size()).equals(number(receipt.get("canonical_units"))))return red("unit_rows_incomplete");
        Set<Integer> seen=new HashSet<>();List<Integer> players=new ArrayList<>(),allies=new ArrayList<>(),physical=new ArrayList<>(),contact=new ArrayList<>(),retreating=new ArrayList<>();boolean subjectFound=false;
        for(Obj row:units) {
            // Public CUnit zero is legal; all private owner/Province IDs remain positive.
            int id;try{id=publicId(row.get("army_id"));}catch(IllegalArgumentException invalid){return red("unit_id_invalid_or_duplicate");}if(!seen.add(id))return red("unit_id_invalid_or_duplicate");
            if(!(row.get("war_side") instanceof Text sideValue)||!Set.of("allied","hostile","neutral").contains(sideValue.value()))return red("war_side_unclassified");
            String side=((Text)row.get("war_side")).value();if(!positive(row.get("owner_character_id"))||!positive(row.get("current_province_id")))return red("owner_or_province_unresolved");
            if(!(row.get("retreating") instanceof Bool))return red("retreat_state_unresolved");if(!(row.get("controllable") instanceof Bool))return red("control_state_unresolved");
            if(!positive(row.get("army_state_code"))||number(row.get("army_state_code")).compareTo(BigInteger.valueOf(9))>0)return red("army_state_unresolved");if(!(row.get("in_combat") instanceof Bool))return red("combat_state_unresolved");
            if(!side.equals("neutral")&&(yes(row,"in_combat")||integer(6).equals(row.get("army_state_code"))&&!yes(row,"retreating")))return red("army_state_risk_unproven");
            if(id==subject)subjectFound=side.equals("allied")&&completeRoute(row)&&yes(row,"controllable");if(yes(row,"controllable"))players.add(id);if(side.equals("allied"))allies.add(id);
            if(side.equals("hostile")){physical.add(id);if(!completeRoute(row))return red("hostile_route_incomplete");if(yes(row,"retreating"))retreating.add(id);else contact.add(id);}
        }
        if(!subjectFound)return red("subject_unresolved");
        List<Integer> observedPlayer,observedAllied;try{observedPlayer=ids(receipt.get("player_army_ids"));observedAllied=ids(receipt.get("allied_army_ids"));}catch(IllegalArgumentException invalid){return red("friendly_set_noncanonical");}
        if(!observedPlayer.equals(sorted(players))||!observedPlayer.equals(publishedPlayer))return red("player_army_set_mismatch");if(!observedAllied.equals(sorted(allies))||!observedAllied.equals(publishedAllied))return red("allied_army_set_mismatch");
        List<Integer> hostile,desired,excluded;try{hostile=ids(receipt.get("hostile_army_ids"));desired=ids(receipt.get("contact_hostile_army_ids"));excluded=ids(receipt.get("retreating_hostile_army_ids"));}catch(IllegalArgumentException invalid){return red("hostile_set_noncanonical");}
        if(!hostile.equals(sorted(physical))||!hostile.equals(publishedEnemy))return red("physical_published_set_mismatch");if(hostile.isEmpty())return red("hostile_set_empty");
        if(!excluded.equals(sorted(retreating))||!excluded.isEmpty())return red("retreating_hostile_risk_unproven");if(!desired.equals(sorted(contact))||!desired.equals(requested)||!desired.equals(contactResult))return red("contact_set_mismatch");
        return new Check(true,"shape_valid_only",hostile,desired);
    }
    private static boolean completeRoute(Obj row){try{List<Integer> route=OpportunityJson.array(row.get("route_province_ids"),"route").stream().map(value->{if(!positive(value))throw new IllegalArgumentException("private Province");return number(value).intValueExact();}).toList();
        if(!nonnegative(row.get("route_source_count"))||!number(row.get("route_source_count")).equals(BigInteger.valueOf(route.size())))return false;
        return route.isEmpty()?new Text("complete_empty").equals(row.get("route_read_status")):new Text("complete_nonempty").equals(row.get("route_read_status"));}catch(IllegalArgumentException|ArithmeticException invalid){return false;}}
    private static List<Obj> rows(Value value){return OpportunityJson.array(value,"rows").stream().map(item->OpportunityJson.object(item,"row")).toList();}
    private static List<Integer> roster(List<Obj> rows){List<Integer> result=sorted(rows.stream().map(row->publicId(row.get("army_id"))).toList());if(new HashSet<>(result).size()!=result.size())throw new IllegalArgumentException("duplicate public army");return result;}
    private static List<Integer> ids(Value value){List<Integer> result=OpportunityJson.array(value,"IDs").stream().map(PhysicalArmyInventoryCheck::publicId).toList();if(!result.equals(sorted(new ArrayList<>(new HashSet<>(result)))))throw new IllegalArgumentException("noncanonical public army set");return result;}
    private static List<Integer> sorted(List<Integer> values){return values.stream().sorted().toList();}
    private static int publicId(Value value){BigInteger n=number(value);if(n.signum()<0||n.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))>0)throw new IllegalArgumentException("public CUnit int32");return n.intValueExact();}
    private static IntegerValue integer(int n){return new IntegerValue(BigInteger.valueOf(n));}
    private static BigInteger number(Value value){return OpportunityJson.integer(value,"integer");}
    private static boolean positive(Value value){return value instanceof IntegerValue n&&n.value().signum()>0;}
    private static boolean nonnegative(Value value){return value instanceof IntegerValue n&&n.value().signum()>=0;}
    private static boolean sameInt(Value first,Value second){return first instanceof IntegerValue&&second instanceof IntegerValue&&first.equals(second);}
    private static boolean yes(Obj row,String field){return new Bool(true).equals(row.get(field));}
}
