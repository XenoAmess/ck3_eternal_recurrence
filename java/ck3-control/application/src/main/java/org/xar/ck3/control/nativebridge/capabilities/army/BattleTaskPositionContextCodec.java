package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** Actual task/position inputs and already evaluated rows; no ScriptValue or declaration is re-evaluated. */
public final class BattleTaskPositionContextCodec {
    private static final Set<String> KINDS=Set.of("task_owner","position_passive","position_scoped","councillor_task");
    private BattleTaskPositionContextCodec() { }
    public static JsonNode normalize(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("schema_version","status","character_id","raw_task_inputs_ready","branch_vectors_ready","owner_council_present","ordered_owned_tasks",
                "councillor_task_link_present","councillor_task","owned_passive","councillor_position_task","unavailable_reason"));ObjectNode out=object();
        JsonNode version=number(raw.get("schema_version"),field+".schema_version",32,false,false);require(BigInteger.ONE.equals(integer(version)),field+".schema_version","exact integer schema 1 required");out.set("schema_version",version);
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));
        for(String key:List.of("raw_task_inputs_ready","branch_vectors_ready"))out.set(key,bool(raw.get(key),field+"."+key,false));
        for(String key:List.of("owner_council_present","councillor_task_link_present"))out.set(key,bool(raw.get(key),field+"."+key,true));
        out.set("ordered_owned_tasks",array(raw.get("ordered_owned_tasks"),field+".ordered_owned_tasks",true,BattleTaskPositionContextCodec::task));
        JsonNode tasks=out.get("ordered_owned_tasks");if(tasks.isArray())for(int index=0;index<tasks.size();index++)require(integer(tasks.get(index).get("native_index")).equals(BigInteger.valueOf(index)),field+".ordered_owned_tasks","native stored task order differs");
        out.set("councillor_task",nil(raw.get("councillor_task"))?NullNode.instance:task(raw.get("councillor_task"),field+".councillor_task"));
        JsonNode councillor=out.get("councillor_task");
        require(!falseValue(out,"owner_council_present") || tasks.isArray() && tasks.isEmpty(),field,"observed null council requires known empty task input");
        require(!falseValue(out,"councillor_task_link_present") || nil(councillor),field,"absent task link cannot carry task object");
        if(trueValue(out,"raw_task_inputs_ready")) {
            require(booleanValue(out,"owner_council_present")!=null && tasks.isArray() && booleanValue(out,"councillor_task_link_present")!=null
                    && (!trueValue(out,"councillor_task_link_present") || !nil(councillor)),field,"raw task input is marked ready without observed pointers/rows");
            for(JsonNode item:tasks)require(taskMetadataReady((ObjectNode)item,false),field,"raw task metadata is incomplete");
            if(!nil(councillor))require(taskMetadataReady((ObjectNode)councillor,true),field,"councillor task metadata is incomplete");
        }
        out.set("owned_passive",branch(raw.get("owned_passive"),field+".owned_passive","291ded0"));
        out.set("councillor_position_task",branch(raw.get("councillor_position_task"),field+".councillor_position_task","291dce0"));
        boolean vectors=out.get("owned_passive").get("vectors_ready").booleanValue() && out.get("councillor_position_task").get("vectors_ready").booleanValue();
        require(trueValue(out,"branch_vectors_ready")==vectors,field,"branch vector readiness disagrees");
        Status status=Status.decode(raw.get("status"),field+".status");String reason=string(text(raw.get("unavailable_reason"),field+".unavailable_reason",true,false));
        boolean available=status==Status.AVAILABLE;
        require(available==(trueValue(out,"raw_task_inputs_ready") && trueValue(out,"branch_vectors_ready"))
                && (available ? reason==null : reason!=null && !reason.isEmpty()),field,"observation availability/reason disagrees");
        out.put("status",status.wire);if(reason==null)out.putNull("unavailable_reason");else out.put("unavailable_reason",reason);return out;
    }
    private static JsonNode property(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("count","keys_u16","values_q64"));ObjectNode out=object();
        out.set("count",number(raw.get("count"),field+".count",32,false,true));out.set("keys_u16",numbers(raw.get("keys_u16"),field+".keys_u16",16,true,true,false));
        out.set("values_q64",numbers(raw.get("values_q64"),field+".values_q64",64,false,true,false));return out;
    }
    private static boolean propertyReady(JsonNode value) {
        if(nil(value))return false;BigInteger count=integer(value.get("count"));JsonNode keys=value.get("keys_u16"),values=value.get("values_q64");
        return count!=null && count.signum()>=0 && keys.isArray() && values.isArray() && count.equals(BigInteger.valueOf(keys.size())) && count.equals(BigInteger.valueOf(values.size()));
    }
    private static JsonNode context(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("aggregate_properties","weighted_count","weighted_rows"));ObjectNode out=object();
        out.set("aggregate_properties",property(raw.get("aggregate_properties"),field+".aggregate_properties"));out.set("weighted_count",number(raw.get("weighted_count"),field+".weighted_count",32,false,true));
        out.set("weighted_rows",array(raw.get("weighted_rows"),field+".weighted_rows",true,(item,name)-> {
            ObjectNode row=exact(item,name,Set.of("native_index","weight_q64","properties"));ObjectNode result=object();
            result.set("native_index",number(row.get("native_index"),name+".native_index",32,false,false));result.set("weight_q64",number(row.get("weight_q64"),name+".weight_q64",64,false,true));
            result.set("properties",property(row.get("properties"),name+".properties"));return result;
        }));return out;
    }
    private static JsonNode modifier(JsonNode value,String field,boolean evaluated) {
        String propertyKey=evaluated?"properties":"declared_properties";
        var fields=new java.util.HashSet<>(Set.of("contributor_kind","scope_root_character_id_raw","scope_saved_character_id_raw","declaration_scale_q64",propertyKey,"modifier_flags_raw","source_provenance"));
        fields.addAll(evaluated?Set.of("task_native_index","declaration_native_index"):Set.of("native_index"));ObjectNode raw=exact(value,field,fields);ObjectNode out=object();
        JsonNode kind=text(raw.get("contributor_kind"),field+".contributor_kind",false,false);require(KINDS.contains(string(kind)),field+".contributor_kind","unknown contributor kind");out.set("contributor_kind",kind);
        out.set("declaration_scale_q64",number(raw.get("declaration_scale_q64"),field+".declaration_scale_q64",64,false,true));out.set(propertyKey,property(raw.get(propertyKey),field+"."+propertyKey));
        out.set("modifier_flags_raw",number(raw.get("modifier_flags_raw"),field+".modifier_flags_raw",64,true,true));out.set("source_provenance",text(raw.get("source_provenance"),field+".source_provenance",false,false));
        for(String key:List.of("scope_root_character_id_raw","scope_saved_character_id_raw"))out.set(key,number(raw.get(key),field+"."+key,32,false,true));
        for(String key:evaluated?List.of("task_native_index","declaration_native_index"):List.of("native_index"))out.set(key,number(raw.get(key),field+"."+key,32,false,false));return out;
    }
    private static JsonNode task(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("native_index","task_id_raw","resolved_task_id_raw","used_native_default","frozen_raw","incumbent_character_id_raw","owner_character_id_raw","task_type_present",
                "original_position_type_present","native_gate_allowed","terminal_task_type_present","declarations","owner_aggregate_properties_ready","owner_aggregate_properties"));ObjectNode out=object();
        for(String key:List.of("native_index","task_id_raw"))out.set(key,number(raw.get(key),field+"."+key,32,false,false));
        for(String key:List.of("resolved_task_id_raw","incumbent_character_id_raw","owner_character_id_raw"))out.set(key,number(raw.get(key),field+"."+key,32,false,true));
        out.set("frozen_raw",number(raw.get("frozen_raw"),field+".frozen_raw",8,true,true));
        for(String key:List.of("used_native_default","task_type_present","original_position_type_present","native_gate_allowed","terminal_task_type_present"))out.set(key,bool(raw.get(key),field+"."+key,true));
        out.set("declarations",array(raw.get("declarations"),field+".declarations",true,(item,name)->modifier(item,name,false)));
        out.set("owner_aggregate_properties",property(raw.get("owner_aggregate_properties"),field+".owner_aggregate_properties"));
        out.set("owner_aggregate_properties_ready",bool(raw.get("owner_aggregate_properties_ready"),field+".owner_aggregate_properties_ready",false));
        require(!trueValue(out,"owner_aggregate_properties_ready") || propertyReady(out.get("owner_aggregate_properties")),field,"missing owner aggregate marked ready");return out;
    }
    private static boolean taskMetadataReady(ObjectNode task,boolean councillor) {
        for(String key:List.of("resolved_task_id_raw","used_native_default","frozen_raw","incumbent_character_id_raw","owner_character_id_raw","task_type_present","original_position_type_present"))if(nil(task.get(key)))return false;
        return !(councillor && BigInteger.ZERO.equals(integer(task,"frozen_raw")) && trueValue(task,"task_type_present") && nil(task.get("native_gate_allowed")));
    }
    private static JsonNode branch(JsonNode value,String field,String rva) {
        ObjectNode raw=exact(value,field,Set.of("status","complete_no_contribution","vectors_ready","evaluated_rows","prefix_before","prefix_source","aggregate_properties_after","aggregate_source","unavailable_reason"));ObjectNode out=object();
        Status status=Status.decode(raw.get("status"),field+".status");out.put("status",status.wire);out.set("vectors_ready",bool(raw.get("vectors_ready"),field+".vectors_ready",false));
        boolean ready=trueValue(out,"vectors_ready");require(ready==(status==Status.AVAILABLE),field,"vector availability disagrees");
        out.set("evaluated_rows",array(raw.get("evaluated_rows"),field+".evaluated_rows",true,(item,name)->modifier(item,name,true)));JsonNode rows=out.get("evaluated_rows");
        if(ready) { require(rows.isArray(),field,"evaluated rows are unknown");for(JsonNode row:rows)require(propertyReady(row.get("properties")),field,"evaluated properties are unknown"); }
        out.set("complete_no_contribution",bool(raw.get("complete_no_contribution"),field+".complete_no_contribution",true));
        require(!trueValue(out,"complete_no_contribution") || ready && rows.isArray() && rows.isEmpty(),field,"complete none requires known empty evaluated rows");
        String reason=string(text(raw.get("unavailable_reason"),field+".unavailable_reason",true,false));require(ready?reason==null:reason!=null && !reason.isEmpty(),field,"vector availability reason disagrees");
        if(reason==null)out.putNull("unavailable_reason");else out.put("unavailable_reason",reason);
        out.set("prefix_before",context(raw.get("prefix_before"),field+".prefix_before"));out.set("aggregate_properties_after",property(raw.get("aggregate_properties_after"),field+".aggregate_properties_after"));
        for(String key:List.of("prefix","aggregate")) {
            String source=key+"_source",operand=key.equals("prefix")?"prefix_before":"aggregate_properties_after";
            JsonNode normalized=text(raw.get(source),field+"."+source,false,false);
            String expected=nil(out.get(operand))?"unobserved":(key.equals("prefix")?"actual_before_":"actual_after_")+rva;
            require(expected.equals(string(normalized)),field+"."+source,"source does not identify actual native stage");out.set(source,normalized);
        }
        return out;
    }
}
