package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** Strict current native source census. Normalization observes operands; it never executes a native write. */
public final class BattleContextSourceCodec {
    private static final List<String> SPANS=List.of("selected_lifestyle_span","selected_dynasty_span","selected_house_span","selected_house_extra_span");
    private static final Set<String> EXTERNAL=Set.of("later_direct_291c3fb_44c","helper_291f0a0","later_helpers_291f550_291f940","tail_direct_291c5b7_291cc49",
            "tail_prefix_2753860_2922530","middle_helpers_291f260_291fb10","trait_stage_291d460","absent_recipient_inputs","helper_2922070",
            "conference_24b1d00","uncached_recipient_inputs","provider_bucket_291c5b2","qualifier_28bc0d0","list_predicate_2530dd0",
            "gated_temporary_tail_291c7a7","after_gated_tail_326a8e0_2920310","provider192_and2920850","following_2920b50","following_2bca620",
            "following_government_land_312a950","following_2921350","following_2921020","following_diac_2920d60");
    private BattleContextSourceCodec() { }
    public static JsonNode normalize(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        Set<String> optional=new HashSet<>(EXTERNAL);optional.addAll(Set.of("branch_291d7e0","pre_291e210_1640","post_291d7e0_sources"));
        ObjectNode raw=exact(value,field,Set.of("status","ready","character_id","branch_291e210","reason"),optional);
        ObjectNode result=object();availabilityFields(result,availability(raw,field),"reason");
        result.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));
        result.set("branch_291e210",branchA(raw.get("branch_291e210"),field+".branch_291e210"));
        if(raw.has("branch_291d7e0"))result.set("branch_291d7e0",branchB(raw.get("branch_291d7e0"),field+".branch_291d7e0"));
        if(raw.has("pre_291e210_1640")) {
            JsonNode pre=pre(raw.get("pre_291e210_1640"),field+".pre_291e210_1640");sameActor(pre,integer(result,"character_id"),field+".pre_291e210_1640");result.set("pre_291e210_1640",pre);
        }
        if(raw.has("post_291d7e0_sources")) {
            JsonNode post=post(raw.get("post_291d7e0_sources"),field+".post_291d7e0_sources");sameActor(post,integer(result,"character_id"),field+".post_291d7e0_sources");result.set("post_291d7e0_sources",post);
        }
        for(String key:EXTERNAL)if(raw.has(key)) {
            JsonNode section=BattlePersonExternalCodec.normalize(BattlePersonExternalCodec.Leaf.fromWire(key),raw.get(key),field+"."+key);
            sameActor(section,integer(result,"character_id"),field+"."+key);result.set(key,section);
        }
        return result;
    }
    private static JsonNode resolution(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("status","requested_full_id","selected_full_id","reason"));ObjectNode out=object();
        out.set("status",text(raw.get("status"),field+".status",false,true));out.set("reason",text(raw.get("reason"),field+".reason",true,true));
        for(String key:List.of("requested_full_id","selected_full_id"))out.set(key,number(raw.get(key),field+"."+key,32,true,true));return out;
    }
    private static JsonNode span(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("selected_source","count","rows","reason"));ObjectNode out=object();
        out.set("selected_source",text(raw.get("selected_source"),field+".selected_source",false,true));
        out.set("count",number(raw.get("count"),field+".count",32,false,true));out.set("reason",text(raw.get("reason"),field+".reason",true,true));
        out.set("rows",ordered(raw.get("rows"),field+".rows","native_index",(item,name)-> {
            ObjectNode row=exact(item,name,Set.of("native_index","definition_identity","weight_q64"));ObjectNode result=object();
            result.set("native_index",number(row.get("native_index"),name+".native_index",32,false,false));
            result.set("definition_identity",text(row.get("definition_identity"),name+".definition_identity",true,true));
            result.set("weight_q64",number(row.get("weight_q64"),name+".weight_q64",64,false,true));return result;
        }));return out;
    }
    private static JsonNode branchA(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        Set<String> fields=new HashSet<>(SPANS);fields.addAll(Set.of("status","ready","component_present","first_relation_resolution","second_relation_resolution","house_resolution","house_extra_enabled","definition_blocks","reason"));
        ObjectNode raw=exact(value,field,fields);ObjectNode out=object();availabilityFields(out,availability(raw,field),"reason");
        for(String key:List.of("component_present","house_extra_enabled"))out.set(key,bool(raw.get(key),field+"."+key,true));
        for(String key:List.of("first_relation_resolution","second_relation_resolution","house_resolution"))out.set(key,resolution(raw.get(key),field+"."+key));
        for(String key:SPANS)out.set(key,span(raw.get(key),field+"."+key));
        var seen=new HashSet<String>();out.set("definition_blocks",array(raw.get("definition_blocks"),field+".definition_blocks",false,(item,name)-> {
            ObjectNode row=exact(item,name,Set.of("definition_identity","properties"));ObjectNode result=object();
            JsonNode identity=text(row.get("definition_identity"),name+".definition_identity",false,true);
            require(seen.add(string(identity)),name,"definition identity is not distinct");result.set("definition_identity",identity);
            result.set("properties",properties(row.get("properties"),name+".properties"));return result;
        }));
        require(!trueValue(out,"ready") || aReady(out),field,"available branch lacks consumed native operands");return out;
    }
    private static boolean aReady(ObjectNode branch) {
        if(booleanValue(branch,"house_extra_enabled")==null || booleanValue(branch,"component_present")==null)return false;
        for(String key:SPANS) {
            JsonNode span=branch.get(key);if(nil(span) || integer(span.get("count"))==null)return false;
            int count=integer(span.get("count")).intValueExact();if(count<=0)continue;
            JsonNode rows=span.get("rows");if(!rows.isArray() || rows.size()<count)return false;
            for(int index=0;index<count;index++) {
                JsonNode row=rows.get(index),identity=row.get("definition_identity");
                if(nil(identity) || nil(row.get("weight_q64")))return false;
                JsonNode found=NullNode.instance;
                for(JsonNode definition:branch.get("definition_blocks"))if(string(identity).equals(string(definition.get("definition_identity")))) { found=definition.get("properties");break; }
                if(!propertiesReady(found))return false;
            }
        }
        return true;
    }
    private static JsonNode pre(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("status","ready","character_id","army_selection","army_key_f4_raw","army_field_120_raw","army_field_124_raw","second_selection","second_field_174_raw","admitted","property_block","unavailable_reason"));
        ObjectNode out=object();availabilityFields(out,availability(raw,field,"unavailable_reason"),"unavailable_reason");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));
        out.set("admitted",bool(raw.get("admitted"),field+".admitted",true));out.set("property_block",properties(raw.get("property_block"),field+".property_block"));
        for(String key:List.of("army_selection","second_selection")) {
            JsonNode selected=text(raw.get(key),field+"."+key,true,true);String selection=string(selected);
            require(selection==null || Set.of("registry_full_id","native_fallback").contains(selection),field+"."+key,"unknown native selection");out.set(key,selected);
        }
        for(String key:List.of("army_key_f4_raw","army_field_120_raw","army_field_124_raw","second_field_174_raw"))out.set(key,number(raw.get(key),field+"."+key,32,false,true));
        BigInteger first=integer(out,"army_field_120_raw"),second=integer(out,"second_field_174_raw");
        Boolean actual=BigInteger.valueOf(-1).equals(first) ? Boolean.FALSE : first!=null && second!=null ? first.equals(second) : null;
        require(Objects.equals(booleanValue(out,"admitted"),actual),field,"admitted disagrees with exact DWORD predicate");
        if(BigInteger.valueOf(-1).equals(first))for(String key:List.of("army_field_124_raw","second_selection","second_field_174_raw"))require(nil(out.get(key)),field,"early false branch contains undemanded second operands");
        require(Boolean.TRUE.equals(actual) || nil(out.get("property_block")),field,"provider block requires true admission");
        boolean complete=!nil(out.get("army_selection")) && actual!=null && (BigInteger.valueOf(-1).equals(first) || !nil(out.get("second_selection")))
                && (!Boolean.TRUE.equals(actual) || propertiesReady(out.get("property_block")));
        require(trueValue(out,"ready")==complete,field,"availability disagrees with consumed native operands");return out;
    }
    private static JsonNode conditionalA(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("native_index","key_identity","key_object_id","key_object_magic","property_block","admitted","reason"),Set.of("property_source","property_source_native_index"));
        ObjectNode out=conditionalCommon(raw,field);out.set("key_identity",text(raw.get("key_identity"),field+".key_identity",true,true));
        for(String key:List.of("key_object_id","key_object_magic"))out.set(key,number(raw.get(key),field+"."+key,32,true,true));
        out.setAll(BattleContextAdmissionsV86Codec.normalizeAdmissionExtension(raw,field,BattleContextAdmissionsV86Codec.Kind.A));return out;
    }
    private static JsonNode conditionalB(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("native_index","key_i32","property_block","admitted","reason"),Set.of("admission_source","admission_nested_native_index"));
        ObjectNode out=conditionalCommon(raw,field);out.set("key_i32",number(raw.get("key_i32"),field+".key_i32",32,false,true));
        out.setAll(BattleContextAdmissionsV86Codec.normalizeAdmissionExtension(raw,field,BattleContextAdmissionsV86Codec.Kind.B));return out;
    }
    private static JsonNode conditionalC(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("native_index","source_key_u32","masked_index_u32","resolver_count_i32","selected_native_fallback","invert_u8","property_block",
                "resolved_condition_identity","condition_source","condition_length","condition_capacity","condition_bytes","first_signed_byte","classifier_mode_i32","classifier_result_i32",
                "condition_token_id","admitted","token_origin","lookup_status","reason"),Set.of("locale_classification"));
        ObjectNode out=conditionalCommon(raw,field);
        for(String key:List.of("source_key_u32","masked_index_u32"))out.set(key,number(raw.get(key),field+"."+key,32,true,true));
        for(String key:List.of("resolver_count_i32","condition_length","first_signed_byte","classifier_mode_i32","classifier_result_i32","condition_token_id"))out.set(key,number(raw.get(key),field+"."+key,32,false,true));
        out.set("selected_native_fallback",bool(raw.get("selected_native_fallback"),field+".selected_native_fallback",true));
        out.set("invert_u8",number(raw.get("invert_u8"),field+".invert_u8",8,true,true));out.set("condition_capacity",number(raw.get("condition_capacity"),field+".condition_capacity",64,true,true));
        out.set("condition_bytes",numbers(raw.get("condition_bytes"),field+".condition_bytes",8,true,true,false));
        out.set("resolved_condition_identity",text(raw.get("resolved_condition_identity"),field+".resolved_condition_identity",true,true));
        for(String key:List.of("condition_source","token_origin","lookup_status"))out.set(key,text(raw.get(key),field+"."+key,false,false));
        out.setAll(BattleContextAdmissionsV86Codec.normalizeAdmissionExtension(raw,field,BattleContextAdmissionsV86Codec.Kind.C));return out;
    }
    private static ObjectNode conditionalCommon(ObjectNode raw,String field) {
        ObjectNode out=object();out.set("native_index",number(raw.get("native_index"),field+".native_index",32,false,false));
        out.set("property_block",properties(raw.get("property_block"),field+".property_block"));out.set("admitted",bool(raw.get("admitted"),field+".admitted",true));
        out.set("reason",text(raw.get("reason"),field+".reason",true,true));return out;
    }
    private static JsonNode sourceRow(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("native_index","source_identity","base_properties","auxiliary_410_provenance","auxiliary_retained_identity","auxiliary_retained_present","auxiliary_tag_u32",
                "conditional_a_count","conditional_b_count","conditional_c_count","conditional_a_rows","conditional_b_rows","conditional_c_rows","reason"));
        ObjectNode out=object();out.set("native_index",number(raw.get("native_index"),field+".native_index",32,false,false));
        for(String key:List.of("source_identity","auxiliary_retained_identity","reason"))out.set(key,text(raw.get(key),field+"."+key,true,true));
        out.set("base_properties",properties(raw.get("base_properties"),field+".base_properties"));out.set("auxiliary_410_provenance",text(raw.get("auxiliary_410_provenance"),field+".auxiliary_410_provenance",false,false));
        out.set("auxiliary_retained_present",bool(raw.get("auxiliary_retained_present"),field+".auxiliary_retained_present",true));out.set("auxiliary_tag_u32",number(raw.get("auxiliary_tag_u32"),field+".auxiliary_tag_u32",32,true,true));
        for(String kind:List.of("a","b","c")) {
            String count="conditional_"+kind+"_count",rows="conditional_"+kind+"_rows";out.set(count,number(raw.get(count),field+"."+count,32,false,true));
            ElementNormalizer normalizer=switch(kind) { case "a"->BattleContextSourceCodec::conditionalA;case "b"->BattleContextSourceCodec::conditionalB;default->BattleContextSourceCodec::conditionalC; };
            out.set(rows,ordered(raw.get(rows),field+"."+rows,"native_index",normalizer));
        }
        return out;
    }
    private static JsonNode branchB(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("status","ready","base_inputs_ready","component_present","selected_source","source_count","source_rows","conditional_a_fallback_properties",
                "government_token_count","government_token_ids_i32","government_source","condition_registry_guard","condition_fallback_guard","token_manager_present","reason"),BattleContextAdmissionsV86Codec.SELECTOR_FIELDS);
        ObjectNode out=object();availabilityFields(out,availability(raw,field),"reason");out.set("base_inputs_ready",bool(raw.get("base_inputs_ready"),field+".base_inputs_ready",false));
        for(String key:List.of("component_present","token_manager_present"))out.set(key,bool(raw.get(key),field+"."+key,true));
        for(String key:List.of("selected_source","government_source"))out.set(key,text(raw.get(key),field+"."+key,false,false));
        for(String key:List.of("source_count","government_token_count","condition_registry_guard","condition_fallback_guard"))out.set(key,number(raw.get(key),field+"."+key,32,false,true));
        out.set("source_rows",ordered(raw.get("source_rows"),field+".source_rows","native_index",BattleContextSourceCodec::sourceRow));
        out.set("conditional_a_fallback_properties",properties(raw.get("conditional_a_fallback_properties"),field+".conditional_a_fallback_properties"));
        out.set("government_token_ids_i32",numbers(raw.get("government_token_ids_i32"),field+".government_token_ids_i32",32,false,true,false));
        require(trueValue(out,"base_inputs_ready")==bBaseReady(out),field,"base-copy availability disagrees with independently observed arrays");
        require(trueValue(out,"ready")==bConsumedReady(out),field,"conditional availability disagrees with observed admission inputs");
        out.setAll(BattleContextAdmissionsV86Codec.normalizeSelectorFields(raw,field));return out;
    }
    private static boolean bBaseReady(ObjectNode branch) {
        BigInteger count=integer(branch,"source_count");if(booleanValue(branch,"component_present")==null || count==null)return false;
        int length=count.intValueExact();if(length<=0)return true;JsonNode rows=branch.get("source_rows");if(!rows.isArray() || rows.size()<length)return false;
        for(int index=0;index<length;index++) {
            JsonNode row=rows.get(index),block=row.get("base_properties");if(nil(row.get("source_identity")) || nil(block))return false;
            for(String key:List.of("keys","values")) {
                BigInteger nativeCount=integer(block.get(key+"_count"));JsonNode values=block.get(key.equals("keys")?"keys_u16":"values_q64");
                if(nativeCount==null || nativeCount.signum()<0 || !values.isArray() || nativeCount.compareTo(BigInteger.valueOf(values.size()))>0)return false;
            }
        }
        return true;
    }
    private static boolean bConsumedReady(ObjectNode branch) {
        if(!trueValue(branch,"base_inputs_ready"))return false;int count=integer(branch,"source_count").intValueExact();if(count<=0)return true;
        for(int source=0;source<count;source++)for(String kind:List.of("a","b","c")) {
            JsonNode row=branch.get("source_rows").get(source);BigInteger amount=integer(row.get("conditional_"+kind+"_count"));JsonNode rows=row.get("conditional_"+kind+"_rows");
            if(amount==null || !rows.isArray())return false;int length=amount.intValueExact();if(length<=0)continue;if(rows.size()<length)return false;
            for(int index=0;index<length;index++) {
                JsonNode admission=rows.get(index);Boolean admitted=booleanValue(admission.get("admitted"));if(admitted==null)return false;
                if(kind.equals("c")) {
                    BigInteger government=integer(branch,"government_token_count");JsonNode tokens=branch.get("government_token_ids_i32");
                    if(nil(admission.get("condition_token_id")) || nil(admission.get("invert_u8")) || government==null || !tokens.isArray()
                            || tokens.size()<Math.max(0,government.intValueExact()))return false;
                }
                if(admitted && !propertiesReady(admission.get("property_block")))return false;
            }
        }
        return true;
    }
    private static JsonNode post(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("status","ready","character_id","guarded630","carrier40","ordered_d8","unavailable_reason"));ObjectNode out=object();
        availabilityFields(out,availability(raw,field,"unavailable_reason"),"unavailable_reason");out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));
        out.set("guarded630",postGuarded(raw.get("guarded630"),field+".guarded630"));out.set("carrier40",postCarrier(raw.get("carrier40"),field+".carrier40"));
        out.set("ordered_d8",postOrdered(raw.get("ordered_d8"),field+".ordered_d8"));
        require(trueValue(out,"ready")==List.of("guarded630","carrier40","ordered_d8").stream().allMatch(key->out.get(key).get("ready").booleanValue()),field,"availability disagrees with independent current source leaves");return out;
    }
    private static JsonNode postGuarded(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("status","ready","carrier_1b0_present","carrier280_present","selection","selected_field38_raw","character68_signed","threshold_signed","admitted","property_block","unavailable_reason"));
        ObjectNode out=object();availabilityFields(out,availability(raw,field,"unavailable_reason"),"unavailable_reason");
        for(String key:List.of("carrier_1b0_present","carrier280_present","admitted"))out.set(key,bool(raw.get(key),field+"."+key,true));
        out.set("selection",text(raw.get("selection"),field+".selection",true,true));out.set("property_block",properties(raw.get("property_block"),field+".property_block"));
        for(String key:List.of("selected_field38_raw","threshold_signed"))out.set(key,number(raw.get(key),field+"."+key,32,false,true));
        out.set("character68_signed",number(raw.get("character68_signed"),field+".character68_signed",16,false,true));
        Boolean carrier=booleanValue(out,"carrier_1b0_present"),nested=booleanValue(out,"carrier280_present");
        String expected=Boolean.FALSE.equals(carrier) || Boolean.TRUE.equals(carrier) && Boolean.FALSE.equals(nested) ? "native_fallback5D1E308"
                : Boolean.TRUE.equals(carrier) && Boolean.TRUE.equals(nested) ? "carrier280_qword8" : null;
        require(Objects.equals(string(out.get("selection")),expected),field,"selection disagrees with current pointer guards");
        BigInteger magic=integer(out,"selected_field38_raw"),signed=integer(out,"character68_signed"),threshold=integer(out,"threshold_signed");
        Boolean admitted=magic==null ? null : !magic.equals(BigInteger.valueOf(0x4744624FL)) ? Boolean.FALSE : signed!=null && threshold!=null ? signed.compareTo(threshold)>=0 : null;
        require(Objects.equals(booleanValue(out,"admitted"),admitted),field,"admitted disagrees with native magic/signed comparison");
        if(magic!=null && !magic.equals(BigInteger.valueOf(0x4744624FL)))require(signed==null && threshold==null,field,"wrong magic contains undemanded signed operands");
        require(Boolean.TRUE.equals(admitted) || nil(out.get("property_block")),field,"property block requires true admission");
        boolean consumed=expected!=null && admitted!=null && (!admitted || propertiesReady(out.get("property_block")));
        require(trueValue(out,"ready")==consumed,field,"availability disagrees with demanded operands");return out;
    }
    private static JsonNode postCarrier(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("status","ready","carrier_1b0_present","carrier288_present","admitted","property_block","unavailable_reason"));ObjectNode out=object();
        availabilityFields(out,availability(raw,field,"unavailable_reason"),"unavailable_reason");
        for(String key:List.of("carrier_1b0_present","carrier288_present","admitted"))out.set(key,bool(raw.get(key),field+"."+key,true));out.set("property_block",properties(raw.get("property_block"),field+".property_block"));
        Boolean carrier=booleanValue(out,"carrier_1b0_present"),nested=booleanValue(out,"carrier288_present");Boolean admitted=Boolean.FALSE.equals(carrier)?Boolean.FALSE:Boolean.TRUE.equals(carrier)?nested:null;
        require(Objects.equals(booleanValue(out,"admitted"),admitted),field,"admitted disagrees with native pointer guards");
        require(!Boolean.FALSE.equals(carrier) || nested==null,field,"null carrier contains undemanded +288 operand");
        require(Boolean.TRUE.equals(admitted) || nil(out.get("property_block")),field,"property block requires true admission");
        require(trueValue(out,"ready")==(admitted!=null && (!admitted || propertiesReady(out.get("property_block")))),field,"availability disagrees with demanded operands");return out;
    }
    private static JsonNode postOrdered(JsonNode value,String field) {
        ObjectNode raw=exact(value,field,Set.of("status","ready","carrier_1c0_present","header_selection","source_array_present","source_count_raw","occurrences","unavailable_reason"));ObjectNode out=object();
        availabilityFields(out,availability(raw,field,"unavailable_reason"),"unavailable_reason");
        for(String key:List.of("carrier_1c0_present","source_array_present"))out.set(key,bool(raw.get(key),field+"."+key,true));
        out.set("header_selection",text(raw.get("header_selection"),field+".header_selection",true,true));out.set("source_count_raw",number(raw.get("source_count_raw"),field+".source_count_raw",32,false,true));
        Boolean carrier=booleanValue(out,"carrier_1c0_present");String expected=carrier==null?null:carrier?"carrier_1c0_plus200":"inline_static54E7270";
        require(Objects.equals(string(out.get("header_selection")),expected),field,"header selection disagrees with current carrier");
        out.set("occurrences",ordered(raw.get("occurrences"),field+".occurrences","source_index",(item,name)-> {
            ObjectNode row=exact(item,name,Set.of("source_index","source_identity","property_block","unavailable_reason"));ObjectNode result=object();
            result.set("source_index",number(row.get("source_index"),name+".source_index",32,false,false));result.set("source_identity",text(row.get("source_identity"),name+".source_identity",true,true));
            result.set("property_block",properties(row.get("property_block"),name+".property_block"));result.set("unavailable_reason",text(row.get("unavailable_reason"),name+".unavailable_reason",true,true));return result;
        }));
        BigInteger count=integer(out,"source_count_raw");JsonNode rows=out.get("occurrences");
        boolean consumed=carrier!=null && booleanValue(out,"source_array_present")!=null && count!=null && count.signum()>=0 && rows.isArray()
                && count.equals(BigInteger.valueOf(rows.size())) && (count.signum()==0 || trueValue(out,"source_array_present"));
        if(consumed)for(JsonNode row:rows)if(nil(row.get("source_identity")) || !propertiesReady(row.get("property_block"))) { consumed=false;break; }
        require(trueValue(out,"ready")==consumed,field,"availability disagrees with stored source occurrences");return out;
    }
    private static JsonNode ordered(JsonNode value,String field,String key,ElementNormalizer normalizer) {
        JsonNode result=array(value,field,true,normalizer);
        if(!nil(result))for(int index=0;index<result.size();index++)require(integer(result.get(index).get(key)).equals(BigInteger.valueOf(index)),field+"["+index+"]."+key,"native stored row order differs");return result;
    }
}
