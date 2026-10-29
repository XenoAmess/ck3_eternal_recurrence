package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;

/** Ordered physical list predicate. Nonempty scoped triggers remain unknown exactly as the source consumer. */
final class BattlePersonListPredicateCodec {
    private BattlePersonListPredicateCodec() { }
    private static JsonNode scope(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;
        ObjectNode row=shape(raw,field,"root_scope_kind_u32","root_character_full_id_u32","named_scope_kind_u32","named_selected_full_id_u32","named_binding_key_i32","trigger_object","trigger_vtable","trigger_evaluator_function"),out=object();
        nums(row,out,field,32,true,"root_scope_kind_u32","root_character_full_id_u32","named_scope_kind_u32","named_selected_full_id_u32");
        nums(row,out,field,32,false,"named_binding_key_i32");words(row,out,field,"trigger_object","trigger_vtable","trigger_evaluator_function");
        require(nil(out.get("root_scope_kind_u32"))||eq(out.get("root_scope_kind_u32"),4),field,"unsupported root scope kind");
        require(nil(out.get("named_scope_kind_u32"))||eq(out.get("named_scope_kind_u32"),31),field,"unsupported named scope kind");return out;
    }
    private static ObjectNode row(JsonNode raw,String field) {
        ObjectNode in=shape(raw,field,"native_index","key_u32","ready","resolution_selection","selected_object","selected_full_id_u32","used_fallback","predicate_receiver","magic_u32","condition_count_raw_i32","predicate_result","pc_selection","scope_inputs","properties","reason"),out=object();
        index(in,out,field,true);out.set("ready",bool(in.get("ready"),field+".ready",false));
        nums(in,out,field,32,true,"key_u32","selected_full_id_u32","magic_u32");nums(in,out,field,32,false,"condition_count_raw_i32");
        words(in,out,field,"selected_object","predicate_receiver");bools(in,out,field,"used_fallback","predicate_result");texts(in,out,field,"resolution_selection","pc_selection","reason");
        out.set("scope_inputs",scope(in.get("scope_inputs"),field+".scope_inputs"));out.set("properties",properties(in.get("properties"),field+".properties"));
        String selection=string(out.get("resolution_selection")),pc=string(out.get("pc_selection"));
        require(selection==null||selection.equals("registry_full_id")||selection.equals("native_fallback"),field,"unsupported full-ID resolution selection");
        require(pc==null||pc.equals("selected_d8"),field,"PC selection lacks source-closed predicate");return out;
    }
    private record RowResult(boolean ready,boolean skipped,Boolean predicate,String pc) { }
    private static RowResult actual(JsonNode row) {
        if(nil(row.get("key_u32")))return new RowResult(false,false,null,null);
        if(integer(row.get("key_u32")).equals(U32MAX))return new RowResult(true,true,null,null);
        boolean valid=positive(row.get("selected_object"));String selection=string(row.get("resolution_selection"));
        if("registry_full_id".equals(selection))valid&=Boolean.FALSE.equals(booleanValue(row.get("used_fallback")))&&row.get("selected_full_id_u32").equals(row.get("key_u32"));
        else if("native_fallback".equals(selection))valid&=Boolean.TRUE.equals(booleanValue(row.get("used_fallback")));else valid=false;
        valid&=positive(row.get("predicate_receiver"))&&!nil(row.get("magic_u32"));Boolean admitted=null;
        if(valid) {
            if(!eq(row.get("magic_u32"),0x4744624fL)||zero(row.get("condition_count_raw_i32")))admitted=true;
            else valid=false;
        }
        if(Boolean.TRUE.equals(admitted)&&!propertiesReady(row.get("properties")))valid=false;
        return new RowResult(valid,false,admitted,Boolean.TRUE.equals(admitted)?"selected_d8":null);
    }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;
        ObjectNode out=start(raw,field,"character_id","scratch_present","header_selection","default_header_guard_raw","source_array_present","source_count_raw","rows");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));
        bools(raw,out,field,"scratch_present","source_array_present");texts(raw,out,field,"header_selection");nums(raw,out,field,32,false,"default_header_guard_raw","source_count_raw");
        JsonNode rows=array(raw.get("rows"),field+".rows",true,BattlePersonListPredicateCodec::row);order(rows,field);out.set("rows",rows);prefix(out.get("source_count_raw"),rows,field);
        String selection=string(out.get("header_selection"));boolean header=false;
        if("held_scratch_458".equals(selection))header=Boolean.TRUE.equals(booleanValue(out.get("scratch_present")));
        else if("static_default_54e7180".equals(selection))header=Boolean.FALSE.equals(booleanValue(out.get("scratch_present")))&&!nil(out.get("default_header_guard_raw"))&&!zero(out.get("default_header_guard_raw"))&&!eq(out.get("default_header_guard_raw"),-1);
        BigInteger count=integer(out.get("source_count_raw"));header&=count!=null&&count.signum()>=0&&!nil(out.get("source_array_present"))&&(count==null||count.signum()==0||Boolean.TRUE.equals(booleanValue(out.get("source_array_present"))));
        boolean complete=header;
        if(header) {
            int retained=rows.isArray()?rows.size():0;if(count.compareTo(BigInteger.valueOf(retained))>0)complete=false;
            for(JsonNode row:rows) {
                RowResult result=actual(row);rowReason(row,result.ready(),field);
                same(row.get("predicate_result"),result.predicate(),field,"published predicate differs from actual source operands");
                same(row.get("pc_selection"),result.pc(),field,"published PC selection differs from actual predicate");
                require(!result.skipped()||(nil(row.get("properties"))&&nil(row.get("scope_inputs"))),field,"sentinel row contains undemanded properties/scope");
                require(result.predicate()!=null||nil(row.get("properties")),field,"unknown predicate cannot publish a selected PC");complete&=result.ready();
            }
        }
        require(!is(out.get("status"),"unavailable"),field,"list predicate supports available/partial only");
        require(out.get("ready").booleanValue()==complete,field,"whole-stage readiness differs from actual ordered source predicates");return out;
    }
}
