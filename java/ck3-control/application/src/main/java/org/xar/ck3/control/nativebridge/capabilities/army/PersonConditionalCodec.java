package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.PersonCurrentJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;

/** Exact .4 self classifier, independent pair opinion, and caller-scoped row weight contracts. */
final class PersonConditionalCodec {
    private PersonConditionalCodec() { }
    private static JsonNode metadata(JsonNode raw,String field) {
        ObjectNode n=new Row(raw,field).numbers(32,true,false,"native_index").booleans(false,"ready").strings(true,"reason definition_identity")
            .numbers(16,true,true,"key_u16").numbers(8,true,true,"flag_ba_u8 flag_b8_u8").done();state(n,"ready","reason",field);
        if(yes(n,"ready")){need(exists(n,"key_u16")&&exists(n,"definition_identity")&&exists(n,"flag_ba_u8"),field+" demanded metadata absent");need(num(n,"flag_ba_u8",0)?exists(n,"flag_b8_u8"):!exists(n,"flag_b8_u8"),field+" BA/B8 source demand differs");}return n;
    }
    private static ObjectNode row(JsonNode raw,String field,boolean nativeEvaluated) {
        Row r=new Row(raw,field).numbers(32,true,false,"native_index").booleans(false,"ready")
            .strings(true,"reason object_identity expression_tree_278_identity expression_scoped_268_identity metadata_registry_identity metadata_table_identity")
            .numbers(32,false,true,"expression_flag_280_i32 expression_count_1d4_i32 keys_count_i32 values_count_i32").child("properties",PersonCurrentJson::pcValues)
            .children("metadata",PersonConditionalCodec::metadata,false);
        for(String k:List.of("raw_value_258_q64","weight_q64"))r.out.set(k,q64(r.take(k),field+"."+k,true));
        ObjectNode n=r.done();state(n,"ready","reason",field);BigInteger weight=i(n,"weight_q64");
        if(!nativeEvaluated&&weight!=null){
            if(num(n,"expression_flag_280_i32",0)){need(UNIT.equals(weight)&&!exists(n,"expression_tree_278_identity")&&!exists(n,"expression_scoped_268_identity")&&!exists(n,"expression_count_1d4_i32")&&!exists(n,"raw_value_258_q64"),field+" default weight consumed skipped expression fields");}
            else need(exists(n,"expression_flag_280_i32")&&"0x0".equals(s(n,"expression_tree_278_identity"))&&"0x0".equals(s(n,"expression_scoped_268_identity"))&&num(n,"expression_count_1d4_i32",0)&&eq(weight,i(n,"raw_value_258_q64")),field+" literal weight lacks three zero guards");
        }
        if(yes(n,"ready")){
            need(exists(n,"object_identity")&&weight!=null,field+" known row lacks physical identity/evaluated scalar");
            JsonNode pc=n.get("properties"),meta=n.get("metadata");
            if(weight.signum()==0)need(pc.isNull()&&meta.isEmpty()&&!exists(n,"keys_count_i32")&&!exists(n,"values_count_i32"),field+" zero weight demanded skipped PC");
            else{
                BigInteger keys=i(n,"keys_count_i32"),values=i(n,"values_count_i32");need(nonnegative(keys)&&values!=null&&values.compareTo(keys)>=0&&!pc.isNull()&&exists(pc,"keys_u16")&&exists(pc,"values_q64")
                    &&eq(keys,BigInteger.valueOf(pc.get("keys_u16").size()))&&eq(values,BigInteger.valueOf(pc.get("values_q64").size()))&&eq(keys,BigInteger.valueOf(meta.size()))&&allReady(meta),field+" known row lacks independent PC counts/metadata");
                for(int index=0;index<meta.size();index++)need(num(meta.get(index),"native_index",index)&&eq(i(meta.get(index),"key_u16"),pc.get("keys_u16").get(index).bigIntegerValue()),field+" metadata physical key order changed");
            }
        }return n;
    }
    private static String voteFor(BigInteger total,BigInteger high,BigInteger low,String field) {
        need(total!=null&&high!=null,field+" total/high threshold demanded");float number=total.intValue();
        if(number>=Float.intBitsToFloat(high.intValue())){need(low==null,field+" low threshold undemanded after high match");return "high";}
        need(low!=null,field+" low threshold demanded");return Float.intBitsToFloat(low.intValue())>=number?"low":"middle";
    }
    private static JsonNode selfVote(JsonNode raw,String field,String character) {
        Row r=new Row(raw,field).numbers(32,true,false,"native_index").booleans(false,"ready").strings(true,"reason registry_identity registry_slots_identity candidate_character_identity selected_character_identity selected_scratch_identity")
            .strings(false,"resolution_selection").numbers(32,true,true,"requested_full_id_u32 registry_count_u32 candidate_full_id_u32 high_threshold_bits_u32 low_threshold_bits_u32")
            .numbers(32,false,true,"base_opinion_i32 additional_opinion_i32 minimum_i32 maximum_i32 clamped_i32");
        JsonNode vote=r.take("vote");r.out.set("vote",text(vote,field+".vote",false,!yes(r.out,"ready")&&vote.isTextual()&&vote.textValue().isEmpty()));
        ObjectNode n=r.done();state(n,"ready","reason",field);
        if(yes(n,"ready")){
            need(eq(s(n,"selected_character_identity"),character)&&exists(n,"selected_scratch_identity")&&num(n,"base_opinion_i32",100)&&num(n,"additional_opinion_i32",0)&&exists(n,"minimum_i32")&&exists(n,"high_threshold_bits_u32"),field+" self-only source operands absent");
            BigInteger minimum=i(n,"minimum_i32"),clamped;if(minimum.compareTo(BigInteger.valueOf(100))>0){clamped=minimum;need(!exists(n,"maximum_i32"),field+" maximum undemanded below minimum");}
            else{need(exists(n,"maximum_i32"),field+" maximum demanded");clamped=i(n,"maximum_i32").min(BigInteger.valueOf(100));}
            need(eq(clamped,i(n,"clamped_i32")),field+" native clamp differs");need(eq(s(n,"vote"),voteFor(clamped,i(n,"high_threshold_bits_u32"),i(n,"low_threshold_bits_u32"),field)),field+" actual float32 vote differs");
        }return n;
    }
    static ObjectNode conditional(JsonNode raw,String field) {
        Row r=base(raw,field,"xar.ck3.person-following-2921a90-conditional-12004-v1")
            .strings(true,"character_identity selected_model_identity selected_object_identity conditional_definition_identity classifier_land_identity classifier_header_identity classifier_array_identity selected_array_identity reason classifier_reason")
            .numbers(32,true,true,"character_id classifier_magic_u32 classifier_full_id_u32 occurrence_count")
            .numbers(32,false,true,"gate_b8c_count_i32 gate_bbc_count_i32 classifier_default_guard_i32 classifier_count_i32 classifier_result_i32 selected_count_i32")
            .booleans(false,"ready classifier_ready").booleans(true,"admitted").strings(false,"classifier_header_selection selected_family");
        r.children("classifier_rows",(v,f)->selfVote(v,f,s(r.out,"character_identity")),true).children("rows",(v,f)->row(v,f,false),true);
        ObjectNode n=r.done();state(n,"ready","reason",field);BigInteger classifier=i(n,"classifier_result_i32");
        if(yes(n,"classifier_ready")){
            need(s(n,"classifier_reason")==null&&validClassifier(classifier),field+" classifier result absent");
            boolean invalid=exists(n,"classifier_magic_u32")&&!num(n,"classifier_magic_u32",0x43686172L)||num(n,"classifier_full_id_u32",0xffffffffL),empty=num(n,"classifier_count_i32",0);
            if(invalid||empty)need(num(n,"classifier_result_i32",1)&&n.get("classifier_rows").isEmpty(),field+" actual classifier early return differs");
            else{exactCount(n,"classifier_count_i32","classifier_rows",field);need(i(n,"classifier_count_i32").signum()>0&&allReady(n.get("classifier_rows")),field+" classifier physical votes unavailable");need(eq(classifier,majority(n.get("classifier_rows"))),field+" physical majority differs");}
            if("static_default_5d21338".equals(s(n,"classifier_header_selection")))need(exists(n,"classifier_default_guard_i32")&&!num(n,"classifier_default_guard_i32",0)&&!num(n,"classifier_default_guard_i32",-1),field+" default header uninitialized");
        }else need(classifier==null,field+" unknown classifier publishes result");
        if(yes(n,"ready")){
            String family=s(n,"selected_family");
            if("not_demanded".equals(family))need(Boolean.FALSE.equals(b(n,"admitted"))||yes(n,"admitted")&&num(n,"gate_b8c_count_i32",0)&&num(n,"gate_bbc_count_i32",0),field+" bypass lacks actual zero counts/admission");
            else if("classifier_other_empty".equals(family))need(yes(n,"classifier_ready")&&num(n,"classifier_result_i32",1),field+" empty branch lacks actual classifier");
            else selectedFamily(n,field,false);
            need(eq(i(n,"occurrence_count"),occurrences(n.get("rows"),false)),field+" append occurrence count differs");
        }else need(!exists(n,"occurrence_count"),field+" incomplete family claims count");return n;
    }
    private static boolean validClassifier(BigInteger n){return n!=null&&n.signum()>=0&&n.compareTo(BigInteger.TWO)<=0;}
    private static BigInteger majority(JsonNode rows){int high=0,low=0;for(JsonNode row:rows){if("high".equals(s(row,"vote")))high++;else if("low".equals(s(row,"vote")))low++;}int middle=rows.size()-high-low;return BigInteger.valueOf(high>low&&high>middle?0:low>high&&low>middle?2:1);}
    private static BigInteger occurrences(JsonNode rows,boolean evaluated){int count=0;for(JsonNode row:rows){JsonNode actual=evaluated?row.get("evaluated_inputs"):row;if(!BigInteger.ZERO.equals(i(actual,"weight_q64")))count++;}return BigInteger.valueOf(count);}
    private static void selectedFamily(JsonNode n,String field,boolean requirePointer){String family=s(n,"selected_family");need(selected(family,"bb0_bbc","b80_b8c")&&yes(n,"classifier_ready")&&(num(n,"classifier_result_i32",0)||num(n,"classifier_result_i32",2))
        &&eq(family,num(n,"classifier_result_i32",0)?"bb0_bbc":"b80_b8c"),field+" selected family/classifier mismatch");exactCount(n,"selected_count_i32","rows",field);need(allReady(n.get("rows"))&&(!requirePointer||exists(n,"selected_array_identity")),field+" selected physical rows incomplete");}
    private static JsonNode opinionRow(JsonNode raw,String field,JsonNode source,JsonNode receiver) {
        Row r=new Row(raw,field).numbers(32,true,false,"source_index").booleans(false,"ready").strings(true,"reason selected_character_identity toward_character_identity")
            .strings(false,"source_selection").numbers(32,true,true,"selected_full_character_id toward_full_character_id high_threshold_bits_u32 low_threshold_bits_u32")
            .numbers(32,false,true,"base_value additional_value total_opinion_i32");JsonNode v=r.take("vote");r.out.set("vote",text(v,field+".vote",false,v.isTextual()&&v.textValue().isEmpty()));
        ObjectNode n=r.done();state(n,"ready","reason",field);String selection=s(n,"source_selection"),character=s(receiver,"character_identity");BigInteger actor=i(receiver,"character_id");
        need(selected(selection,"self_source_inputs","native_pair_postclamp_28bc470","unavailable"),field+" unknown opinion source");
        need(eq(i(n,"source_index"),i(source,"native_index"))&&eq(s(n,"selected_character_identity"),s(source,"selected_character_identity")),field+" physical opinion source identity/index differs");
        need(eq(i(n,"toward_full_character_id"),actor)&&eq(s(n,"toward_character_identity"),character),field+" opinion receiver differs");
        if("native_pair_postclamp_28bc470".equals(selection))need(!exists(n,"base_value")&&!exists(n,"additional_value")&&!eq(s(n,"selected_character_identity"),character)&&!eq(i(n,"selected_full_character_id"),actor),field+" pair total fabricated parts or used receiver self");
        else if("self_source_inputs".equals(selection))need(eq(s(n,"selected_character_identity"),character)&&eq(i(n,"selected_full_character_id"),actor)&&eq(b(n,"ready"),b(source,"ready"))
            &&eq(i(n,"base_value"),i(source,"base_opinion_i32"))&&eq(i(n,"additional_value"),i(source,"additional_opinion_i32"))&&eq(i(n,"total_opinion_i32"),i(source,"clamped_i32"))
            &&eq(i(n,"high_threshold_bits_u32"),i(source,"high_threshold_bits_u32"))&&eq(i(n,"low_threshold_bits_u32"),i(source,"low_threshold_bits_u32")),field+" self vote differs from unchanged source");
        if(!yes(n,"ready")){need("".equals(s(n,"vote")),field+" unread opinion supplied vote");return n;}
        need(!"unavailable".equals(selection)&&exists(n,"selected_full_character_id")&&!num(n,"selected_full_character_id",0)&&!num(n,"selected_full_character_id",0xffffffffL)&&exists(n,"selected_character_identity")&&exists(n,"total_opinion_i32")&&exists(n,"high_threshold_bits_u32"),field+" known opinion lacks actual total/threshold");
        need(eq(s(n,"vote"),voteFor(i(n,"total_opinion_i32"),i(n,"high_threshold_bits_u32"),i(n,"low_threshold_bits_u32"),field)),field+" postclamp float32 vote differs");return n;
    }
    static ObjectNode opinion(JsonNode raw,String field) {
        Row r=base(raw,field,"xar.ck3.person-following-2921a90-opinion-12004-v1").child("source_inputs",PersonConditionalCodec::conditional)
            .numbers(32,true,true,"character_id occurrence_count").booleans(false,"ready classifier_ready").strings(true,"reason classifier_reason selected_array_identity")
            .numbers(32,false,true,"classifier_result_i32 selected_count_i32").strings(false,"selected_family");
        JsonNode source=r.out.get("source_inputs");need(eq(i(r.out,"character_id"),i(source,"character_id")),field+" source inputs changed CharacterID");JsonNode rawOpinions=r.take("opinion_rows");need(rawOpinions.isArray()&&rawOpinions.size()<=source.get("classifier_rows").size(),field+" opinions lack original occurrences");
        var opinions=r.out.putArray("opinion_rows");for(int index=0;index<rawOpinions.size();index++){JsonNode row=opinionRow(rawOpinions.get(index),field+".opinion_rows["+index+"]",source.get("classifier_rows").get(index),source);need(num(row,"source_index",index),field+" opinion occurrence order changed");opinions.add(row);}
        r.children("rows",(v,f)->row(v,f,false),true);ObjectNode n=r.done();state(n,"ready","reason",field);
        boolean unavailable=!yes(source,"admitted")||!exists(source,"character_identity")||!exists(source,"conditional_definition_identity")||"0x0".equals(s(source,"conditional_definition_identity"));
        if(unavailable&&"unavailable".equals(s(n,"selected_family"))){String reason=s(source,"reason")==null?"conditional_admission_unread":s(source,"reason");need(!yes(n,"ready")&&eq(s(n,"reason"),reason)&&!yes(n,"classifier_ready")&&s(n,"classifier_reason")==null&&!exists(n,"classifier_result_i32")&&opinions.isEmpty()&&n.get("rows").isEmpty()&&!exists(n,"selected_array_identity")&&!exists(n,"selected_count_i32")&&!exists(n,"occurrence_count"),field+" preclassifier admission failure differs");return n;}
        if(yes(n,"classifier_ready")||!"not_demanded".equals(s(n,"selected_family")))state(n,"classifier_ready","classifier_reason",field+".classifier");
        if(yes(n,"classifier_ready")){need(validClassifier(i(n,"classifier_result_i32")),field+" classifier absent");if(yes(source,"classifier_ready"))need(eq(i(n,"classifier_result_i32"),i(source,"classifier_result_i32")),field+" preceding known classifier changed");
            BigInteger count=i(source,"classifier_count_i32");if(count!=null&&count.signum()>0)need(eq(count,BigInteger.valueOf(opinions.size()))&&allReady(opinions)&&eq(i(n,"classifier_result_i32"),majority(opinions)),field+" opinion majority/complete source mismatch");else need(yes(source,"classifier_ready")&&opinions.isEmpty(),field+" empty classifier lacks preceding proof");
        }else need(!exists(n,"classifier_result_i32"),field+" unread opinion classifier supplied result");
        prefixCount(n,"selected_count_i32","rows",field);
        if(yes(n,"ready")){String family=s(n,"selected_family");if("not_demanded".equals(family))need(yes(source,"ready")&&eq(s(source,"selected_family"),family)&&opinions.isEmpty()&&n.get("rows").isEmpty(),field+" bypass differs from preceding proof");else if("classifier_other_empty".equals(family))need(yes(n,"classifier_ready")&&num(n,"classifier_result_i32",1)&&n.get("rows").isEmpty(),field+" empty selection lacks classifier");else selectedFamily(n,field,true);need(eq(i(n,"occurrence_count"),occurrences(n.get("rows"),false)),field+" occurrence count differs");}
        else need(!exists(n,"occurrence_count"),field+" incomplete selected family supplied count");return n;
    }
    static void prefixCount(JsonNode n,String count,String rows,String field){BigInteger c=i(n,count);if(c!=null)need(c.signum()<0?n.get(rows).isEmpty():BigInteger.valueOf(n.get(rows).size()).compareTo(c)<=0,field+" observed rows exceed signed count");}
    private static JsonNode scopeRow(JsonNode raw,String field,boolean initialized) {
        Row r=new Row(raw,field).numbers(32,true,false,"native_index").strings(false,"evaluation_selection").numbers(32,true,true,"weight_call_ordinal").booleans(false,"scope_prefix_ready")
            .child("source_inputs",(v,f)->row(v,f,false)).child("evaluated_inputs",(v,f)->v.isNull()?nil():row(v,f,true));
        ObjectNode n=r.done();JsonNode source=n.get("source_inputs"),evaluated=n.get("evaluated_inputs");String selection=s(n,"evaluation_selection");need(selected(selection,"same_sample_source","native_row_2872300","unavailable")&&eq(i(n,"native_index"),i(source,"native_index")),field+" native selection or original index differs");
        if(!evaluated.isNull())need(eq(i(evaluated,"native_index"),i(source,"native_index"))&&(!exists(evaluated,"object_identity")||eq(s(evaluated,"object_identity"),s(source,"object_identity"))),field+" evaluated physical identity changed");
        if(exists(n,"weight_call_ordinal"))need(initialized,field+" native call lacks initialized scope");
        if("same_sample_source".equals(selection))need(!exists(n,"weight_call_ordinal")&&evaluated.equals(source),field+" reused source changed or was called");
        else if("native_row_2872300".equals(selection))need(initialized&&yes(n,"scope_prefix_ready")&&exists(n,"weight_call_ordinal")&&!evaluated.isNull(),field+" native weight scope/call absent");
        else if(!evaluated.isNull())need(!yes(evaluated,"ready")&&!exists(evaluated,"weight_q64"),field+" unavailable native call released weight");return n;
    }
    static ObjectNode scope(JsonNode raw,String field) {
        Row r=base(raw,field,"xar.ck3.person-following-2921a90-scope-weights-12004-v1").numbers(32,true,true,"character_id scope_payload_u32 occurrence_count")
            .strings(true,"selected_object_identity selected_array_identity reason").strings(false,"selected_family").numbers(32,false,true,"classifier_result_i32 selected_count_i32")
            .numbers(16,true,true,"scope_kind_u16").booleans(false,"classifier_ready scope_initialized ready");
        r.children("rows",(v,f)->scopeRow(v,f,yes(r.out,"scope_initialized")),true);ObjectNode n=r.done();
        if(yes(n,"scope_initialized"))need(num(n,"scope_kind_u16",4)&&exists(n,"scope_payload_u32"),field+" initialized native scope lacks kind4/payload");need(!exists(n,"scope_kind_u16")||num(n,"scope_kind_u16",4),field+" scope kind differs");
        int calls=0;for(JsonNode row:n.get("rows"))if(exists(row,"weight_call_ordinal"))need(num(row,"weight_call_ordinal",calls++),field+" native call attempt order changed");state(n,"ready","reason",field);
        if(yes(n,"classifier_ready"))need(validClassifier(i(n,"classifier_result_i32")),field+" classifier result absent");else need(!exists(n,"classifier_result_i32"),field+" unread classifier supplied result");prefixCount(n,"selected_count_i32","rows",field);
        if(yes(n,"ready")){String family=s(n,"selected_family");if(selected(family,"not_demanded","classifier_other_empty"))need(n.get("rows").isEmpty()&&!yes(n,"scope_initialized")&&(!"classifier_other_empty".equals(family)||num(n,"classifier_result_i32",1)),field+" known empty family demanded scope/rows");
            else {need(selected(family,"bb0_bbc","b80_b8c")&&yes(n,"classifier_ready")&&(num(n,"classifier_result_i32",0)||num(n,"classifier_result_i32",2))&&eq(family,num(n,"classifier_result_i32",0)?"bb0_bbc":"b80_b8c"),field+" actual selected classifier differs");exactCount(n,"selected_count_i32","rows",field);for(JsonNode row:n.get("rows"))need(!row.get("evaluated_inputs").isNull()&&yes(row.get("evaluated_inputs"),"ready"),field+" independently observed row unavailable");}
            need(eq(i(n,"occurrence_count"),occurrences(n.get("rows"),true)),field+" downstream occurrence count differs");
        }else need(!exists(n,"occurrence_count"),field+" partial family supplied count");return n;
    }
}
