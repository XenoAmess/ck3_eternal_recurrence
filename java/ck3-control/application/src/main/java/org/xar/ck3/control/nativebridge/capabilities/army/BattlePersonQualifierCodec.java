package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.LinkedHashSet;

/** Actual 28BC0D0 relationship walk, sentinel filtering and per-definition DWORD dedup. */
final class BattlePersonQualifierCodec {
    private BattlePersonQualifierCodec() { }
    private static ObjectNode relation(JsonNode raw,String field) {
        ObjectNode row=shape(raw,field,"native_index","marker_u8","definition_object"),out=object();index(row,out,field,true);
        nums(row,out,field,8,true,"marker_u8");words(row,out,field,"definition_object");return out;
    }
    private static ObjectNode candidate(JsonNode raw,String field) {
        ObjectNode row=shape(raw,field,"native_index","definition_object","relationship_count_raw_i32","relationship_array_present","relationships"),out=object();index(row,out,field,true);
        words(row,out,field,"definition_object");nums(row,out,field,32,false,"relationship_count_raw_i32");bools(row,out,field,"relationship_array_present");
        JsonNode rows=array(row.get("relationships"),field+".relationships",true,BattlePersonQualifierCodec::relation);order(rows,field);out.set("relationships",rows);
        prefix(out.get("relationship_count_raw_i32"),rows,field);return out;
    }
    private static ObjectNode evaluation(JsonNode raw,String field) {
        ObjectNode row=shape(raw,field,"native_index","object","candidate_count_raw_i32","candidate_array_present","candidates","id_u32"),out=object();index(row,out,field,true);
        words(row,out,field,"object");nums(row,out,field,32,false,"candidate_count_raw_i32");nums(row,out,field,32,true,"id_u32");bools(row,out,field,"candidate_array_present");
        JsonNode rows=array(row.get("candidates"),field+".candidates",true,BattlePersonQualifierCodec::candidate);order(rows,field);out.set("candidates",rows);
        prefix(out.get("candidate_count_raw_i32"),rows,field);return out;
    }
    private static ObjectNode definition(JsonNode raw,String field) {
        ObjectNode row=shape(raw,field,"native_index","definition_object","ready","scratch_evaluations","accepted_ids_u32","repeat_count","properties","reason"),out=object();index(row,out,field,true);
        words(row,out,field,"definition_object");out.set("ready",bool(row.get("ready"),field+".ready",false));
        JsonNode rows=array(row.get("scratch_evaluations"),field+".scratch_evaluations",true,BattlePersonQualifierCodec::evaluation);order(rows,field);out.set("scratch_evaluations",rows);
        out.set("accepted_ids_u32",numbers(row.get("accepted_ids_u32"),field+".accepted_ids_u32",32,true,true,false));nums(row,out,field,32,false,"repeat_count");
        out.set("properties",properties(row.get("properties"),field+".properties"));texts(row,out,field,"reason");return out;
    }
    private static int header(JsonNode count,JsonNode present,String field) {
        require(!nil(present)&&!nil(count)&&integer(count).signum()>=0,field,"actual nonnegative count and array pointer required");
        require(zero(count)||present.booleanValue(),field,"positive count has null array");return integer(count).intValueExact();
    }
    private static JsonNode physical(JsonNode rows,int index,String field) {
        require(rows.isArray()&&index<rows.size(),field,"demanded physical prefix row absent");return rows.get(index);
    }
    private static BigInteger pointer(JsonNode value,boolean nonnull,String field) {
        require(!nil(value)&&(!nonnull||positive(value)),field,"demanded native pointer unavailable");return integer(value);
    }
    private static boolean candidateMatches(JsonNode row,BigInteger requested,JsonNode fallback,String field) {
        BigInteger definition=pointer(row.get("definition_object"),false,field);
        if(definition.equals(requested))return true;require(definition.signum()!=0,field,"null candidate definition cannot supply relationships");
        int count=header(row.get("relationship_count_raw_i32"),row.get("relationship_array_present"),field);
        for(int i=0;i<count;i++) {
            JsonNode relation=physical(row.get("relationships"),i,field);require(!nil(relation.get("marker_u8")),field,"relationship marker missing");
            BigInteger effective=pointer(eq(relation.get("marker_u8"),2)?relation.get("definition_object"):fallback,false,field);
            if(effective.equals(requested))return true;
        }
        return false;
    }
    private static boolean evaluationMatches(JsonNode row,BigInteger requested,JsonNode fallback,String field) {
        pointer(row.get("object"),true,field);int count=header(row.get("candidate_count_raw_i32"),row.get("candidate_array_present"),field);
        for(int i=0;i<count;i++)if(candidateMatches(physical(row.get("candidates"),i,field),requested,fallback,field))return true;return false;
    }
    private static ArrayNode ids(ObjectNode leaf,JsonNode definition,String field) {
        BigInteger requested=pointer(definition.get("definition_object"),false,field);JsonNode present=leaf.get("scratch_present");
        require(!nil(present),field,"actual scratch pointer unavailable");ArrayNode result=list();if(!present.booleanValue())return result;
        JsonNode count=leaf.get("scratch_count_raw_i32");require(!nil(count),field,"actual scratch signed count unavailable");if(integer(count).signum()<=0)return result;
        var seen=new LinkedHashSet<BigInteger>();
        for(int i=0;i<integer(count).intValueExact();i++) {
            JsonNode row=physical(definition.get("scratch_evaluations"),i,field);
            if(!evaluationMatches(row,requested,leaf.get("fallback_definition_object"),field))continue;
            require(!nil(row.get("id_u32")),field,"matched scratch evaluation lacks its DWORD ID");BigInteger id=integer(row.get("id_u32"));
            if(!id.equals(U32MAX)&&seen.add(id))result.add(id);
        }
        return result;
    }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;
        ObjectNode out=start(raw,field,"character_id","manager_object","definition_count_raw_i32","definition_array_present","scratch_present","scratch_count_raw_i32","fallback_definition_object","definitions");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));words(raw,out,field,"manager_object","fallback_definition_object");
        nums(raw,out,field,32,false,"definition_count_raw_i32","scratch_count_raw_i32");bools(raw,out,field,"definition_array_present","scratch_present");
        JsonNode rows=array(raw.get("definitions"),field+".definitions",true,BattlePersonQualifierCodec::definition);order(rows,field);out.set("definitions",rows);prefix(out.get("definition_count_raw_i32"),rows,field);
        boolean complete=true;int count;
        try {pointer(out.get("manager_object"),true,field);count=header(out.get("definition_count_raw_i32"),out.get("definition_array_present"),field);}
        catch(IllegalArgumentException unavailable){count=0;complete=false;}
        int retained=rows.isArray()?rows.size():0;if(retained<count)complete=false;
        for(int i=0;i<Math.min(count,retained);i++) {
            JsonNode row=rows.get(i);prefix(out.get("scratch_count_raw_i32"),row.get("scratch_evaluations"),field);
            ArrayNode actual=null;boolean rowReady=false;
            try {actual=ids(out,row,field);rowReady=actual.isEmpty()||propertiesReady(row.get("properties"));}
            catch(IllegalArgumentException unavailable){rowReady=false;}
            require(actual==null?nil(row.get("accepted_ids_u32")):actual.equals(row.get("accepted_ids_u32")),field,"published dedup IDs differ from actual predicates");
            require(actual==null?nil(row.get("repeat_count")):eq(row.get("repeat_count"),actual.size()),field,"published repeat count differs from dedup IDs");
            rowReason(row,rowReady,field);complete&=rowReady;
        }
        require(!is(out.get("status"),"unavailable"),field,"qualifier supports available/partial only");
        require(out.get("ready").booleanValue()==complete,field,"whole-stage readiness differs from actual qualifier walk");return out;
    }
}
