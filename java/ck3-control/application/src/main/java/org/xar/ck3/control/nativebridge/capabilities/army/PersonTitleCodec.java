package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.PersonCurrentJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;

/** Local Title constituents, first emitted pointer vector, and historically attributed final tail capture. */
final class PersonTitleCodec {
    private PersonTitleCodec() { }
    private static Row header(JsonNode raw,String field){return new Row(raw,field).booleans(false,"ready").strings(true,"reason");}
    private static void noReadyReason(JsonNode n,String field){if(yes(n,"ready"))need(s(n,"reason")==null,field+" ready observation retains unavailable reason");}
    private static JsonNode family(JsonNode raw,String field){
        ObjectNode n=header(raw,field).strings(true,"array_identity").numbers(32,false,true,"count_i32").booleans(true,"known_empty").children("source_pcs",PersonSourceCodec::pc,false).done();
        if(yes(n,"ready"))need(s(n,"reason")==null&&allReady(n.get("source_pcs")),field+" ready family lacks demanded constituent");return n;
    }
    private static JsonNode supplementalSource(JsonNode raw,String field){
        Row r=header(raw,field).numbers(32,true,false,"native_index").strings(true,"definition_identity membership_array_identity match_identity")
            .numbers(32,true,true,"requested_full_id_u32 character_rite_full_id_u32 rite_membership_key_u32 first_match_index")
            .numbers(32,false,true,"definition_gate_224_i32 membership_count_i32").numbers(8,true,true,"object_gate_18_u8").booleans(true,"rite_id_demanded admitted")
            .child("resolution",PersonSourceCodec::resolution).child("rite_resolution",PersonSourceCodec::resolution).child("source_pc",PersonSourceCodec::pc);
        JsonNode values=r.take("membership_full_ids_u32");need(values.isArray(),field+" observed native ID prefix required");var a=r.out.putArray("membership_full_ids_u32");for(JsonNode v:values)a.add(number(v,field+".membership_full_ids_u32",32,true,true));
        ObjectNode n=r.done();need(eq(i(n,"requested_full_id_u32"),i(n.get("resolution"),"requested_full_id_u32")),field+" supplemental lookup ID differs");
        if(yes(n,"ready"))need(s(n,"reason")==null&&yes(n.get("source_pc"),"ready"),field+" supplemental source lacks operand");return n;
    }
    private static JsonNode supplemental(JsonNode raw,String field){
        ObjectNode n=header(raw,field).strings(true,"array_identity").numbers(32,false,true,"count_i32").booleans(true,"known_empty").children("rows",PersonTitleCodec::supplementalSource,true).done();
        if(yes(n,"ready"))need(s(n,"reason")==null&&allReady(n.get("rows")),field+" supplemental family lacks demanded source");return n;
    }
    private static JsonNode localRow(JsonNode raw,String field){
        Row r=header(raw,field).numbers(32,true,false,"native_index").booleans(false,"input_ready supplemental_ready").booleans(true,"native_contribution_eligible")
            .strings(false,"exclusion").strings(true,"template_identity supplemental_array_identity supplemental_reason")
            .numbers(32,true,true,"requested_title_full_id_u32 selected_title_full_id_u32").numbers(8,true,true,"exclusion_byte_130_u8")
            .numbers(32,false,true,"exclusion_dword_12c_i32 template_tier_i32 supplemental_count_i32")
            .child("resolution",PersonSourceCodec::resolution).child("composer",PersonTitleCodec::family).child("primary",PersonTitleCodec::family);
        // Exactly the original optional extension: absent and explicit null remain different.
        if(raw.has("supplemental"))r.child("supplemental",PersonTitleCodec::supplemental);
        ObjectNode n=r.done();need(eq(i(n,"requested_title_full_id_u32"),i(n.get("resolution"),"requested_full_id_u32")),field+" full Title lookup ID differs");
        if(yes(n,"ready"))need(s(n,"reason")==null&&yes(n,"input_ready"),field+" ready row lacks actual input selection");return n;
    }
    static ObjectNode local(JsonNode raw,String field){
        ObjectNode n=base(raw,field,"xar.ck3.person-local-titles-12004-v1").booleans(false,"ready family_input_ready composer_ready primary_ready supplemental_ready full_helper_ready")
            .strings(true,"reason character_identity selected_model_identity destination_pc_identity character_context_1c0_identity header_identity array_identity full_helper_reason")
            .numbers(32,true,true,"character_id").strings(false,"header_selection").numbers(32,false,true,"count_i32").booleans(true,"family_known_zero").children("rows",PersonTitleCodec::localRow,true).done();
        if(yes(n,"ready"))need(s(n,"reason")==null&&yes(n,"family_input_ready")&&yes(n,"composer_ready")&&yes(n,"primary_ready")&&yes(n,"supplemental_ready"),field+" local family lacks demanded inputs");return n;
    }
    private static JsonNode receiver(JsonNode raw,String field){
        ObjectNode n=header(raw,field).strings(false,"selection").strings(true,"input_context_1c0_identity input_link_1b8_identity context_link_1c0_identity context_candidate_28_identity selected_identity")
            .numbers(32,true,true,"candidate_magic_1c_u32 candidate_full_id_18_u32 requested_full_id_u32").child("resolution",PersonSourceCodec::resolution).done();
        if(yes(n,"ready"))need(s(n,"reason")==null&&exists(n,"selected_identity"),field+" receiver lacks actual selected pointer");return n;
    }
    private static JsonNode element(JsonNode raw,String field){
        if(raw.isNull())return nil();ObjectNode n=header(raw,field).booleans(false,"input_ready").strings(true,"identity template_identity").numbers(32,false,true,"template_tier_i32")
            .child("primary",PersonTitleCodec::family).child("composer",PersonTitleCodec::family).child("supplemental",PersonTitleCodec::supplemental).done();
        if(yes(n,"ready"))need(s(n,"reason")==null&&yes(n,"input_ready")&&yes(n.get("primary"),"ready")&&yes(n.get("composer"),"ready")&&yes(n.get("supplemental"),"ready"),field+" emitted element lacks demanded families");return n;
    }
    private static JsonNode candidate(JsonNode raw,String field){
        ObjectNode n=header(raw,field).numbers(32,true,false,"native_index").booleans(true,"id_demanded emitted").numbers(32,true,true,"requested_full_id_u32").numbers(8,true,true,"filter_byte_130_u8")
            .child("resolution",PersonSourceCodec::resolution).child("element",PersonTitleCodec::element).done();
        if(yes(n,"id_demanded"))need(eq(i(n,"requested_full_id_u32"),i(n.get("resolution"),"requested_full_id_u32")),field+" demanded Title ID differs");
        if(yes(n,"ready"))need(s(n,"reason")==null&&exists(n,"emitted"),field+" ready source lacks emission decision");return n;
    }
    private static JsonNode phase(JsonNode raw,String field){
        ObjectNode n=header(raw,field).booleans(true,"admitted").strings(true,"header_identity array_identity title_registry_identity title_fallback_identity").numbers(32,false,true,"count_i32").children("rows",PersonTitleCodec::candidate,true).done();
        if(yes(n,"ready"))need(s(n,"reason")==null&&allReady(n.get("rows")),field+" ready phase lacks demanded source");return n;
    }
    private static JsonNode phaseInputs(JsonNode raw,String field){
        ObjectNode n=header(raw,field).strings(false,"selection").strings(true,"subject_context_1c0_identity context_array_1e0_identity alternate_root_1d0_identity alternate_array_68_identity")
            .numbers(32,false,true,"context_count_1ec_i32 alternate_count_74_i32").numbers(32,true,true,"initial_title_full_id_u32 second_requested_full_id_330_u32")
            .child("initial_title_resolution",PersonSourceCodec::resolution).child("second_resolution",PersonSourceCodec::resolution).done();noReadyReason(n,field);return n;
    }
    static ObjectNode vector(JsonNode raw,String field){
        Row r=base(raw,field,"xar.ck3.person-first-title-vector-12004-v1").booleans(false,"ready source_inputs_ready producer_ready family_input_ready primary_ready composer_ready supplemental_ready full_helper_ready")
            .strings(true,"reason character_identity selected_model_identity destination_pc_identity receiver_context_1c0_identity full_helper_reason")
            .numbers(32,true,true,"character_id receiver_context_1b8_full_id_u32").child("receiver",PersonTitleCodec::receiver)
            .child("phase_a",PersonTitleCodec::phase).child("phase_b_inputs",PersonTitleCodec::phaseInputs).child("phase_b",PersonTitleCodec::phase).booleans(true,"family_known_zero");
        JsonNode values=r.take("emitted_element_identities");if(values.isNull())r.out.putNull("emitted_element_identities");else{need(values.isArray(),field+" emitted pointer sequence required");var a=r.out.putArray("emitted_element_identities");for(JsonNode value:values)a.add(text(value,field+".emitted_element_identities",false,false));}
        ObjectNode n=r.done();if(yes(n,"producer_ready"))need(exists(n,"emitted_element_identities"),field+" ready producer lacks emitted pointers");
        if(yes(n,"ready"))need(s(n,"reason")==null&&yes(n,"source_inputs_ready")&&yes(n,"producer_ready")&&yes(n,"family_input_ready")&&yes(n,"primary_ready")&&yes(n,"composer_ready")&&yes(n,"supplemental_ready"),field+" ready vector lacks demanded input");return n;
    }
    static ObjectNode tail(JsonNode raw,String field){
        ObjectNode n=base(raw,field,"xar.ck3.person-native-title-tail-capture-12004-v1").strings(true,"reason character_identity model_identity source_return_rva inline_destination_identity")
            .numbers(64,true,false,"capture_sequence").numbers(32,false,true,"capture_date_raw").numbers(32,true,true,"character_id").numbers(64,false,false,"weight_q100000").strings(false,"source_stage")
            .child("prepared_pc",PersonSourceCodec::pc).child("model_aggregate_pc",PersonSourceCodec::pc).booleans(false,"configured capture_observed ready historical_capture actual_model_write_performed full_helper_ready").done();
        need("post_composer_pre_final_outer_append".equals(s(n,"source_stage"))&&yes(n,"historical_capture")&&UNIT.equals(i(n,"weight_q100000"))&&!yes(n,"actual_model_write_performed")&&!yes(n,"full_helper_ready"),field+" captured stage scope changed");
        if(yes(n,"capture_observed")){
            need(yes(n,"configured")&&!num(n,"capture_sequence",0)&&exists(n,"character_id")&&exists(n,"character_identity")&&exists(n,"model_identity"),field+" observed capture lacks owner/sequence");
            BigInteger returned=hex(s(n,"source_return_rva"),field),destination=hex(s(n,"inline_destination_identity"),field),model=hex(s(n,"model_identity"),field);
            need(returned.equals(BigInteger.valueOf(0x291ebefL))&&destination.equals(model.add(BigInteger.valueOf(16))),field+" actual final outer caller/destination differ");
        }else need(num(n,"capture_sequence",0)&&!yes(n,"ready"),field+" unobserved record claims readiness/sequence");
        if(yes(n,"ready"))need(yes(n,"capture_observed")&&s(n,"reason")==null&&yes(n.get("prepared_pc"),"ready")&&yes(n.get("prepared_pc"),"admitted"),field+" ready capture lacks native-prepared PC");return n;
    }
    private static BigInteger hex(String text,String field){
        need(text!=null,field+" actual pointer required");String token=text.strip();boolean negative=token.startsWith("-");if(negative||token.startsWith("+"))token=token.substring(1);if(token.startsWith("0x")||token.startsWith("0X"))token=token.substring(2);need(token.matches("[0-9a-fA-F]+"),field+" actual hexadecimal pointer required");BigInteger value=new BigInteger(token,16);return negative?value.negate():value;
    }
}
