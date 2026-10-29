package org.xar.ck3.control.wave2.military.monthlycaller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel;
import org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel;

/** Finite caller stores from original budgets, preserving ordered raw IDs and shared physical counter aliases. */
public final class ArmyMonthlyCaller {
    private ArmyMonthlyCaller(){}
    public enum Availability { AVAILABLE,UNAVAILABLE }
    public enum Status { AVAILABLE,PARTIAL,UNAVAILABLE }
    public record CounterRow(Availability status,String unavailableReason,int storedIndex,int warReferenceId,
            Integer resolvedWarId,Boolean usedFallback,Integer nativeSelectedSide,Integer nativeCounter30Raw) {
        public CounterRow {Objects.requireNonNull(status);require((status==Availability.AVAILABLE)?unavailableReason==null:unavailableReason!=null&&!unavailableReason.isEmpty(),"caller row readiness/reason");
            require(nativeSelectedSide==null||Set.of(-1,0,1).contains(nativeSelectedSide),"caller side");
            require(status!=Availability.AVAILABLE||resolvedWarId!=null&&usedFallback!=null&&nativeSelectedSide!=null&&(nativeSelectedSide==-1||nativeCounter30Raw!=null),"caller available row incomplete");
            require(!Integer.valueOf(-1).equals(nativeSelectedSide)||nativeCounter30Raw==null,"no-side counter must be null");}
    }
    public record Input(Availability status,boolean ready,String unavailableReason,Integer armyByte22Raw,
            Long currentDateStorageRaw64,Integer unitActorCharacterId,List<CounterRow> warCounterRows,List<Integer> managerArmyIdList2a5a8) {
        public Input {Objects.requireNonNull(status);warCounterRows=copy(warCounterRows);managerArmyIdList2a5a8=copy(managerArmyIdList2a5a8);
            require(ready==(status==Availability.AVAILABLE),"caller readiness");require(ready?unavailableReason==null:unavailableReason!=null&&!unavailableReason.isEmpty(),"caller reason");
            require(armyByte22Raw==null||armyByte22Raw>=0&&armyByte22Raw<=255,"caller byte");
            if(warCounterRows!=null)for(int i=0;i<warCounterRows.size();i++)require(warCounterRows.get(i).storedIndex()==i,"caller stored order");
            require(!ready||armyByte22Raw!=null&&currentDateStorageRaw64!=null&&unitActorCharacterId!=null&&warCounterRows!=null&&managerArmyIdList2a5a8!=null&&warCounterRows.stream().allMatch(r->r.status()==Availability.AVAILABLE),"caller available family incomplete");}
    }
    public record CounterWrite(int storedIndex,int warReferenceId,Integer resolvedWarId,boolean usedFallback,int selectedSide,
            int observedCounter,int before,int increment,int after){}
    public record Skipped(int storedIndex,int warReferenceId){}
    public record Cell(boolean fallback,Integer resolvedWarId,int selectedSide,int initial,int after,int writeOccurrences){}
    private record CellKey(boolean fallback,Integer warId,int side){}
    public record Result(Status status,boolean ready,Integer byteBefore,Integer byteAfter,boolean byteReady,Long dateBefore,
            Long dateAfter,boolean dateReady,Integer counterIncrement,boolean counterReady,List<CounterWrite> writes,List<Skipped> skipped,
            List<Cell> cells,Integer totalBudget,Integer finalCurrent,boolean appendDecisionReady,Boolean appendRequired,
            List<Integer> idsBefore,List<Integer> idsAfter,boolean idsReady,List<String> missing) {
        public Result {writes=List.copyOf(writes);skipped=List.copyOf(skipped);cells=copy(cells);idsBefore=copy(idsBefore);idsAfter=copy(idsAfter);missing=List.copyOf(missing);}
    }
    public static Input decodeInputs(JsonNode node) {
        if(node==null||node.isNull())return null;
        ObjectNode n=StrictJson.object(node,Set.of("status","ready","unavailable_reason","army_byte_22_raw","current_date_storage_raw64","unit_actor_character_id","war_counter_rows","manager_army_id_list_2a5a8"));
        List<CounterRow> rows=null;JsonNode raw=n.get("war_counter_rows");
        if(!raw.isNull()){require(raw.isArray(),"caller rows array/null");rows=new ArrayList<>();for(JsonNode value:raw){
            ObjectNode r=StrictJson.object(value,Set.of("status","unavailable_reason","stored_index","war_reference_id","resolved_war_id","used_fallback","native_selected_side","native_counter_30_raw"));
            rows.add(new CounterRow(availability(r.get("status")),text(r.get("unavailable_reason")),required32(r.get("stored_index")),required32(r.get("war_reference_id")),n32(r.get("resolved_war_id")),bool(r.get("used_fallback")),n32(r.get("native_selected_side")),n32(r.get("native_counter_30_raw"))));}}
        return new Input(availability(n.get("status")),requiredBool(n.get("ready")),text(n.get("unavailable_reason")),n32(n.get("army_byte_22_raw")),n64(n.get("current_date_storage_raw64")),n32(n.get("unit_actor_character_id")),rows,ids(n.get("manager_army_id_list_2a5a8")));
    }
    public static JsonNode encodeInputs(Input input) {
        if(input==null)return com.fasterxml.jackson.databind.node.NullNode.getInstance();
        ObjectNode n=StrictJson.object();n.put("status",wire(input.status()));n.put("ready",input.ready());put(n,"unavailable_reason",input.unavailableReason());put(n,"army_byte_22_raw",input.armyByte22Raw());put64(n,"current_date_storage_raw64",input.currentDateStorageRaw64());put(n,"unit_actor_character_id",input.unitActorCharacterId());
        n.putNull("war_counter_rows");if(input.warCounterRows()!=null){ArrayNode a=n.putArray("war_counter_rows");for(var r:input.warCounterRows()){ObjectNode x=a.addObject();x.put("status",wire(r.status()));put(x,"unavailable_reason",r.unavailableReason());x.put("stored_index",r.storedIndex());x.put("war_reference_id",r.warReferenceId());put(x,"resolved_war_id",r.resolvedWarId());put(x,"used_fallback",r.usedFallback());put(x,"native_selected_side",r.nativeSelectedSide());put(x,"native_counter_30_raw",r.nativeCounter30Raw());}}
        putIds(n,"manager_army_id_list_2a5a8",input.managerArmyIdList2a5a8());return n;
    }
    public static Result project(JsonNode army,MonthlyLossModel.Result budgets,LossSequenceModel.Result sequence) {
        require(army!=null&&army.isObject(),"caller army row required");
        boolean available=new com.fasterxml.jackson.databind.node.TextNode("available").equals(army.get("status"));
        Input input=decodeInputs(army.get("monthly_caller_effect_inputs_v1"));
        Long previous=army.get("army_update_clock_v1") instanceof ObjectNode clock?n64(clock.get("last_supply_update_date_storage_raw64")):null;
        return project(available,n32(army.get("native_carmy_id")),input,previous,budgets,sequence);
    }
    public static Result project(boolean available,Integer nativeArmy,Input input,Long previous,MonthlyLossModel.Result budgets,LossSequenceModel.Result sequence) {
        if(!available)return new Result(Status.UNAVAILABLE,false,null,null,false,null,null,false,null,false,List.of(),List.of(),null,null,null,false,null,null,null,false,List.of("available_same_query_army_strength"));
        List<String> missing=new ArrayList<>();Integer beforeByte=input==null?null:input.armyByte22Raw();
        Boolean admitted=budgets.supplyUpdaterAdmitted();Long date=admitted==null?null:admitted?input==null?null:input.currentDateStorageRaw64():previous;
        if(date==null)missing.add(admitted==null?"supply_updater_admission":admitted?"current_date_storage_raw64":"last_supply_update_date_storage_raw64");
        Integer supply=budgets.supplyComponent().soldiers(),siege=budgets.siegeBudgetSoldiers(),raid=budgets.raidBudgetSoldiers(),increment=null,total=null,finalCurrent=null;
        boolean counterReady=false,appendDecision=false,idsReady=false;Boolean append=null;List<CounterWrite> writes=new ArrayList<>();List<Skipped> skipped=new ArrayList<>();List<Cell> cells=null;
        if(supply!=null&&siege!=null){
            increment=supply+siege;
            if(increment<=0){counterReady=true;cells=List.of();}
            else if(input==null||input.warCounterRows()==null)missing.add("war_counter_rows");
            else {
                Map<CellKey,Cell> values=new LinkedHashMap<>();boolean complete=true;
                for(var row:input.warCounterRows()){
                    if(row.status()!=Availability.AVAILABLE){missing.add("war_counter_rows["+row.storedIndex()+"].available_operands");complete=false;break;}
                    if(Integer.valueOf(-1).equals(row.nativeSelectedSide())){skipped.add(new Skipped(row.storedIndex(),row.warReferenceId()));continue;}
                    if(row.nativeSelectedSide()==null||!Set.of(0,1).contains(row.nativeSelectedSide())||row.usedFallback()==null||row.nativeCounter30Raw()==null||!row.usedFallback()&&row.resolvedWarId()==null){missing.add("war_counter_rows["+row.storedIndex()+"].selected_counter_cell");complete=false;break;}
                    var key=new CellKey(row.usedFallback(),row.usedFallback()?null:row.resolvedWarId(),row.nativeSelectedSide());
                    Cell old=values.get(key);int before=old==null?row.nativeCounter30Raw():old.after(),after=before+increment;
                    values.put(key,new Cell(key.fallback(),key.warId(),key.side(),old==null?row.nativeCounter30Raw():old.initial(),after,old==null?1:old.writeOccurrences()+1));
                    writes.add(new CounterWrite(row.storedIndex(),row.warReferenceId(),row.resolvedWarId(),row.usedFallback(),row.nativeSelectedSide(),row.nativeCounter30Raw(),before,increment,after));
                }
                if(complete){counterReady=true;cells=List.copyOf(values.values());}
            }
        }else{if(supply==null)missing.add("supply_budget_soldiers");if(siege==null)missing.add("siege_budget_soldiers");}
        if(supply!=null&&siege!=null&&raid!=null){total=siege+raid+supply;if(total<=0){appendDecision=true;append=false;}
            else if(sequence!=null&&sequence.ready()&&sequence.finalCurrentSoldiers()!=null){finalCurrent=sequence.finalCurrentSoldiers();appendDecision=true;append=finalCurrent<=0;}
            else missing.add("derived_loss_subsystem_final_current_soldiers");
        }else{if(supply==null)missing.add("supply_budget_soldiers");if(siege==null)missing.add("siege_budget_soldiers");if(raid==null)missing.add("raid_budget_soldiers");}
        List<Integer> before=input==null?null:input.managerArmyIdList2a5a8(),after=null;
        if(appendDecision){if(before==null)missing.add("manager_army_id_list_2a5a8");else if(Boolean.TRUE.equals(append)){if(nativeArmy==null)missing.add("native_carmy_id");else{after=new ArrayList<>(before);after.add(nativeArmy);idsReady=true;}}else{after=before;idsReady=true;}}
        boolean ready=date!=null&&counterReady&&idsReady;
        return new Result(ready?Status.AVAILABLE:Status.PARTIAL,ready,beforeByte,1,true,previous,date,date!=null,increment,counterReady,writes,skipped,cells,total,finalCurrent,appendDecision,append,before,after,idsReady,new ArrayList<>(new java.util.LinkedHashSet<>(missing)));
    }
    public static ObjectNode encode(Result v){
        ObjectNode n=StrictJson.object();n.put("projection_kind","conditional_finite_monthly_caller_effects");n.put("source_contract_game_version","1.20.0.3");n.put("input_basis","same_query_original_budgets_observed_counter_cells_and_derived_loss_subsystem");n.put("status",wire(v.status()));n.put("conditional_caller_effects_ready",v.ready());
        n.put("actual_effects",false);n.put("actual_loss",false);n.putNull("actual_post_state");n.putNull("actual_caller_passed_date_raw64");n.put("full_monthly_applied_loss_ready",false);
        put(n,"army_byte_22_before",v.byteBefore());put(n,"conditional_byte_22_after",v.byteAfter());n.put("conditional_byte_22_ready",v.byteReady());put64(n,"supply_update_date_before_raw64",v.dateBefore());put64(n,"conditional_supply_update_date_raw64",v.dateAfter());n.put("conditional_supply_update_date_ready",v.dateReady());
        n.put("conditional_date_input_basis","current_frame_date_storage_as_explicit_entry_argument");n.put("native_date_pointer_origin","GameState+8");n.put("native_date_pointer_origin_source_closed",true);
        put(n,"war_counter_increment_soldiers",v.counterIncrement());n.put("war_counter_ready",v.counterReady());ArrayNode writes=n.putArray("war_counter_writes");
        for(var w:v.writes()){ObjectNode r=writes.addObject();r.put("stored_index",w.storedIndex());r.put("war_reference_id",w.warReferenceId());put(r,"resolved_war_id",w.resolvedWarId());r.put("used_fallback",w.usedFallback());r.put("native_selected_side",w.selectedSide());r.put("same_query_counter_30_raw",w.observedCounter());r.put("conditional_counter_before_raw",w.before());r.put("original_budget_increment_soldiers",w.increment());r.put("conditional_counter_after_raw",w.after());}
        ArrayNode skipped=n.putArray("war_counter_skipped_occurrences");for(var s:v.skipped()){ObjectNode r=skipped.addObject();r.put("stored_index",s.storedIndex());r.put("war_reference_id",s.warReferenceId());r.put("reason","native_actor_membership_neither_side");}
        n.putNull("conditional_war_counter_cells_after");if(v.cells()!=null){ArrayNode a=n.putArray("conditional_war_counter_cells_after");for(var c:v.cells()){ObjectNode r=a.addObject();r.put("cell_kind",c.fallback()?"fallback":"resolved_war");put(r,"resolved_war_id",c.resolvedWarId());r.put("native_selected_side",c.selectedSide());r.put("initial_counter_30_raw",c.initial());r.put("conditional_counter_30_raw",c.after());r.put("write_occurrences",c.writeOccurrences());}}
        put(n,"tail_original_budget_total_soldiers",v.totalBudget());put(n,"tail_conditional_post_loss_current_soldiers",v.finalCurrent());n.put("id_append_decision_ready",v.appendDecisionReady());put(n,"conditional_id_append_required",v.appendRequired());
        putIds(n,"manager_army_id_list_2a5a8_before",v.idsBefore());putIds(n,"conditional_manager_army_id_list_2a5a8_after",v.idsAfter());n.put("conditional_manager_army_id_list_ready",v.idsReady());n.put("id_collection_operation","ordered_raw_DWORD_append_without_deduplication");n.put("id_collection_growth_basis","conditional_on_ordinary_successful_native_allocation_if_needed");
        ArrayNode missing=n.putArray("missing_inputs");v.missing().forEach(missing::add);return n;
    }
    private static Availability availability(JsonNode v){return Availability.valueOf(StrictJson.text(v).toUpperCase(java.util.Locale.ROOT));}
    private static int required32(JsonNode v){return(int)StrictJson.integer(v,Integer.MIN_VALUE,Integer.MAX_VALUE);}
    private static Integer n32(JsonNode v){return v==null||v.isNull()?null:required32(v);}
    private static Long n64(JsonNode v){return v==null||v.isNull()?null:StrictJson.integer(v,Long.MIN_VALUE,Long.MAX_VALUE);}
    private static String text(JsonNode v){return v==null||v.isNull()?null:StrictJson.text(v);}
    private static boolean requiredBool(JsonNode v){require(v!=null&&v.isBoolean(),"caller Boolean required");return v.booleanValue();}
    private static Boolean bool(JsonNode v){return v==null||v.isNull()?null:requiredBool(v);}
    private static List<Integer> ids(JsonNode v){if(v==null||v.isNull())return null;require(v.isArray(),"caller ordered IDs required");List<Integer> out=new ArrayList<>();for(JsonNode x:v)out.add(required32(x));return List.copyOf(out);}
    private static <T> List<T> copy(List<T> v){return v==null?null:List.copyOf(v);}
    private static void put(ObjectNode n,String k,Integer v){if(v==null)n.putNull(k);else n.put(k,v.intValue());}
    private static void put(ObjectNode n,String k,Boolean v){if(v==null)n.putNull(k);else n.put(k,v.booleanValue());}
    private static void put(ObjectNode n,String k,String v){if(v==null)n.putNull(k);else n.put(k,v);}
    private static void put64(ObjectNode n,String k,Long v){if(v==null)n.putNull(k);else n.put(k,v.longValue());}
    private static void putIds(ObjectNode n,String k,List<Integer> v){n.putNull(k);if(v!=null){ArrayNode a=n.putArray(k);v.forEach(a::add);}}
    private static String wire(Enum<?> value){return value.name().toLowerCase(java.util.Locale.ROOT);}
    private static void require(boolean v,String message){StrictJson.require(v,message);}
}
