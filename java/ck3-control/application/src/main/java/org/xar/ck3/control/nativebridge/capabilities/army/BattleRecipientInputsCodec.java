package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleLeafRecord.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleLeafRecord.Kind.*;

/** Cached/uncached actual native operands plus mandatory exact pure-computation readback. */
final class BattleRecipientInputsCodec {
    private BattleRecipientInputsCodec() { }
    private static JsonNode pointer(JsonNode raw,String field) {
        if(raw!=null&&raw.isTextual()) {
            String value=raw.textValue();require(value.matches("0[xX][0-9a-fA-F]{1,16}"),field,"unsigned64 or hexadecimal pointer required");
            raw=BigIntegerNode.valueOf(new BigInteger(value.substring(2),16));
        }
        return number(raw,field,64,true,true);
    }
    private static ObjectNode ids(JsonNode raw,String field,int bits) {
        String values=bits==32?"values_u32":"values_u64";ObjectNode out=parseRecord(raw,field,f(I32,true,"count"),f(RAW,false,values));
        out.set(values,numbers(out.get(values),field+"."+values,bits,true,true,false));return out;
    }
    private static ObjectNode aggregate(JsonNode raw,String field) {
        ObjectNode out=parseRecord(raw,field,f(I32,true,"count"),f(RAW,false,"keys_u16","values_q64"));
        out.set("keys_u16",numbers(out.get("keys_u16"),field+".keys_u16",16,true,true,false));
        out.set("values_q64",numbers(out.get("values_q64"),field+".values_q64",64,false,true,false));return out;
    }
    private static ObjectNode mapping(JsonNode raw,String field,boolean linked) {
        ObjectNode out=parseRecord(raw,field,f(I32,true,"count","mask"),f(U8,true,"max_probe_u8"),f(RAW,false,"entries"));long[] prior={-1};
        out.set("entries",array(out.get("entries"),field+".entries",true,(value,path)->{
            ObjectNode row=linked?parseRecord(value,path,f(U32,false,"bucket_index"),f(U32,true,"hash_u32"),f(U8,true,"probe_u8"),f(RAW,false,"key_object","value_u64"))
                    :parseRecord(value,path,f(U32,false,"bucket_index"),f(U32,true,"hash_u32","trait_id_u32"),f(U8,true,"probe_u8"),f(I64,true,"value_q64"),f(RAW,false,"key_object"));
            long bucket=n(row,"bucket_index").longValueExact();require(bucket>prior[0],path,"increasing native bucket order required");prior[0]=bucket;
            row.set("key_object",pointer(row.get("key_object"),path+".key_object"));if(linked)row.set("value_u64",pointer(row.get("value_u64"),path+".value_u64"));
            BigInteger probe=n(row,"probe_u8");require(probe==null||probe.signum()!=0&&!probe.equals(BigInteger.valueOf(255)),path,"empty bucket or sentinel cannot be an occupied entry");return row;
        }));
        BigInteger count=n(out,"count");JsonNode entries=out.get("entries");if(count!=null&&!nil(entries))require(BigInteger.valueOf(entries.size()).compareTo(count.max(BigInteger.ZERO))<=0,field,"entries exceed occupied count");return out;
    }
    private static void selection(ObjectNode out,String field) {String selected=s(out,"aggregate_context_selection");require(selected==null||Set.of("owned_model_10","inline_context_5d67b90").contains(selected),field,"unsupported aggregate context selection");}
    static JsonNode absent(JsonNode input,String field) {
        if(nil(input))return NullNode.instance;
        ObjectNode out=parseRecord(input,field,f(TEXT,false,"status"),f(BOOL,false,"ready"),f(I32,false,"character_id"),f(BOOL,true,"carrier_present","associated_used_fallback"),
                f(U32,true,"associated_full_id","associated_resolved_full_id","associated_cache_440"),f(I32,true,"membership_header_guard_raw","aggregate_context_guard_raw"),
                f(I64,true,"member_multiplier_q64","clamp_lower_q64","clamp_upper_q64","calculated_recipient_q64"),f(TEXT,true,"aggregate_context_selection","reason"),
                f(RAW,false,"cached_map_430","cached_map_458","trait_ids","membership_ids","aggregate_properties"));
        out.set("cached_map_430",mapping(out.get("cached_map_430"),field+".cached_map_430",false));out.set("cached_map_458",mapping(out.get("cached_map_458"),field+".cached_map_458",true));
        out.set("trait_ids",ids(out.get("trait_ids"),field+".trait_ids",32));out.set("membership_ids",ids(out.get("membership_ids"),field+".membership_ids",64));out.set("aggregate_properties",aggregate(out.get("aggregate_properties"),field+".aggregate_properties"));selection(out,field);
        BattleRecipientArithmetic.Result calculated=BattleRecipientArithmetic.absent(out);String status=s(out,"status");
        switch(status) {
            case "not_applicable" -> require(Boolean.TRUE.equals(b(out,"ready"))&&Boolean.TRUE.equals(b(out,"carrier_present"))&&nil(out.get("calculated_recipient_q64"))&&zeroReason(out),field,"inconsistent present1C8 skip");
            case "available" -> require(Boolean.TRUE.equals(b(out,"ready"))&&zeroReason(out)&&calculated.calculationReady()&&Objects.equals(n(out,"calculated_recipient_q64"),calculated.valueQ64()),field,"available scalar differs from actual native inputs");
            case "partial" -> require(Boolean.FALSE.equals(b(out,"ready"))&&nil(out.get("calculated_recipient_q64"))&&!zeroReason(out),field,"inconsistent partial observation");
            default -> throw bad(field,"unsupported recipient status");
        }return out;
    }
    private static ObjectNode intrinsicRecord(JsonNode raw,String field) {
        ObjectNode out=parseRecord(raw,field,f(U32,false,"native_index"),f(U8,true,"marker_u8"),f(I32,true,"key_id_i32"),f(I64,true,"value_q64"),f(RAW,false,"key_object"));out.set("key_object",pointer(out.get("key_object"),field+".key_object"));return out;
    }
    private static ObjectNode vector(JsonNode raw,String field,String name,ElementNormalizer normalizer) {
        ObjectNode out=parseRecord(raw,field,f(I32,true,"count"),f(RAW,false,name));out.set(name,ordered(out.get(name),field+"."+name,true,normalizer));BigInteger count=n(out,"count");JsonNode values=out.get(name);
        if(count!=null&&!nil(values))require(BigInteger.valueOf(values.size()).compareTo(count.max(BigInteger.ZERO))<=0,field,"physical rows exceed count");return out;
    }
    private static ObjectNode intrinsicFamily(JsonNode raw,String field) {
        ObjectNode out=parseRecord(raw,field,f(BOOL,false,"ready"),f(RAW,false,"first","second"));
        for(String name:List.of("first","second")) {
            ObjectNode vector=vector(out.get(name),field+"."+name,"records",BattleRecipientInputsCodec::intrinsicRecord);out.set(name,vector);
            if(Boolean.TRUE.equals(b(out,"ready"))) {
                BigInteger count=n(vector,"count");JsonNode records=vector.get("records");require(count!=null&&count.signum()>=0&&!nil(records)&&count.equals(BigInteger.valueOf(records.size())),field,"ready family lacks physical rows");
                for(JsonNode row:records)require(present(row,"marker_u8","value_q64")&&(!eq(row,"marker_u8",2)||present(row,"key_object","key_id_i32")),field,"ready family lacks demanded intrinsic operand");
            }
        }return out;
    }
    private static ObjectNode sourceObject(JsonNode raw,String field) {
        ObjectNode out=parseRecord(raw,field,f(U32,false,"native_index"),f(U32,true,"magic_u32"),f(RAW,false,"object","intrinsic_family"));
        out.set("object",pointer(out.get("object"),field+".object"));out.set("intrinsic_family",intrinsicFamily(out.get("intrinsic_family"),field+".intrinsic_family"));return out;
    }
    private static ObjectNode context(JsonNode raw,String field) {
        ObjectNode out=parseRecord(raw,field,f(U32,false,"native_index"),f(U8,true,"flag_u8"),f(RAW,false,"object"));out.set("object",pointer(out.get("object"),field+".object"));return out;
    }
    private static ObjectNode downstream(JsonNode raw,String field) {
        ObjectNode out=parseRecord(raw,field,f(I32,true,"membership_header_guard_raw","aggregate_context_guard_raw"),f(I64,true,"member_multiplier_q64","clamp_lower_q64","clamp_upper_q64"),f(TEXT,true,"aggregate_context_selection"),f(RAW,false,"trait_ids","membership_ids","aggregate_properties"));
        out.set("trait_ids",ids(out.get("trait_ids"),field+".trait_ids",32));out.set("membership_ids",ids(out.get("membership_ids"),field+".membership_ids",64));out.set("aggregate_properties",aggregate(out.get("aggregate_properties"),field+".aggregate_properties"));selection(out,field);return out;
    }
    static JsonNode uncached(JsonNode input,String field) {
        if(nil(input))return NullNode.instance;
        ObjectNode out=parseRecord(input,field,f(TEXT,false,"status"),f(BOOL,false,"ready"),f(I32,false,"character_id"),f(BOOL,true,"carrier_present","associated_used_fallback"),
                f(U32,true,"associated_full_id","associated_resolved_full_id","associated_cache_440","positive_fallback_magic_u32","negative_fallback_magic_u32"),f(I32,true,"fallback_key_id_i32","cap_i32"),
                f(I64,true,"active_flag4_multiplier_q64","active_other_multiplier_q64","seed_boost_multiplier_q64","calculated_recipient_q64"),f(TEXT,true,"reason"),
                f(RAW,false,"seed_receiver","seed_family","fallback_key_object","active_objects","active_context","removed_objects","positive_fallback_object","negative_fallback_object","downstream_inputs"));
        out.set("seed_family",intrinsicFamily(out.get("seed_family"),field+".seed_family"));
        for(String name:List.of("active_objects","removed_objects"))out.set(name,vector(out.get(name),field+"."+name,"entries",BattleRecipientInputsCodec::sourceObject));
        out.set("active_context",vector(out.get("active_context"),field+".active_context","entries",BattleRecipientInputsCodec::context));out.set("downstream_inputs",downstream(out.get("downstream_inputs"),field+".downstream_inputs"));
        for(String name:List.of("fallback_key_object","positive_fallback_object","negative_fallback_object"))out.set(name,pointer(out.get(name),field+"."+name));
        ObjectNode seed=parseRecord(out.get("seed_receiver"),field+".seed_receiver",f(U32,true,"first_full_id","first_resolved_full_id","second_full_id","second_resolved_full_id"),f(BOOL,true,"first_used_fallback","second_used_fallback"),f(RAW,false,"definition_object"));
        seed.set("definition_object",pointer(seed.get("definition_object"),field+".seed_receiver.definition_object"));out.set("seed_receiver",seed);
        BattleRecipientArithmetic.Result result=BattleRecipientArithmetic.uncached(out);
        switch(s(out,"status")) {
            case "available" -> require(Boolean.TRUE.equals(b(out,"ready"))&&zeroReason(out)&&result.calculationReady()&&Objects.equals(result.valueQ64(),n(out,"calculated_recipient_q64")),field,"available scalar differs from actual native inputs");
            case "not_applicable" -> require(Boolean.TRUE.equals(b(out,"ready"))&&Boolean.FALSE.equals(result.applicable())&&zeroReason(out)&&nil(out.get("calculated_recipient_q64")),field,"inconsistent present/cached skip");
            case "partial" -> require(Boolean.FALSE.equals(b(out,"ready"))&&!zeroReason(out)&&nil(out.get("calculated_recipient_q64")),field,"inconsistent partial observation");
            default -> throw bad(field,"unsupported recipient status");
        }return out;
    }
}
