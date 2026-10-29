package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRelationJson.*;

/** Source-owned public number roles. Only a complete validated original may be projected; no recursive integer guessing. */
public final class FamilyCurrentRelationPublic {
    public static final String SCHEMA="xar.current-first-heir-relationship-public/12004/v2";
    private static final BigInteger JS_MAX=new BigInteger("9007199254740991");
    private enum Role { U64,S64 }
    private static final Map<String,Role> ROLES=roles();
    private FamilyCurrentRelationPublic() { }
    public static OpportunityJson.Obj encode(FamilyCurrentRelation.Observation actual){
        Objects.requireNonNull(actual);ObjectNode body=object(walk(nativeObject(actual.original()),"",true,0));need(!body.has("public_numeric_schema"),"original relationship has an undeclared public encoding marker");body.put("public_numeric_schema",SCHEMA);return retain(body);
    }
    /** Explicit original capture profile; the ordinary Driver's automatic material annotations are not its legacy family result. */
    public static OpportunityJson.Obj captureFamily(FamilyCurrentRelation.Observation actual){
        ObjectNode out=nativeObject(Objects.requireNonNull(actual).original()).deepCopy();
        out.remove(List.of("guardian_factory_materials_v2",FamilyRelationEducationProvider.LEAF,FamilyRelationEducationProvider.SOURCE_LEAF,
                FamilyRelationGuardianMaterials.CHILD_MATERIALS,"current_child_relation_materials_source_v1"));return retain(out);
    }
    /** Original pure guardian decision with declared native64 roles, never recursive integer inference. */
    public static OpportunityJson.Obj guardianDecision(FamilyCurrentRelation.Observation actual){
        Objects.requireNonNull(actual);var binding=actual.root().binding();Long heir=binding.observedFirstHeir().isPresent()?binding.observedFirstHeir().orElseThrow():null;
        var decision=FamilyRelationGuardianMaterials.decision(actual.materials(),actual.descendants(),binding.context().revision(),heir);
        return retain(walk(nativeObject(decision),"/capture_decision",true,0));
    }
    /** Decode is integrity comparison against the actual same archived read, never a new public DTO qualification. */
    public static OpportunityJson.Obj decode(OpportunityJson.Obj publicBody,FamilyCurrentRelation.Observation actualArchived){
        Objects.requireNonNull(actualArchived);ObjectNode body=nativeObject(Objects.requireNonNull(publicBody));eq(body,"public_numeric_schema",SCHEMA);body.remove("public_numeric_schema");OpportunityJson.Obj restored=retain(walk(body,"",false,0));need(restored.equals(actualArchived.original()),"public current relation changed the complete archived original");return actualArchived.original();
    }
    public static OpportunityJson.Obj arguments(PlanningReadReceipt actual,FamilyCurrentRelation.Observation actualArchived){
        requireContract(actual,actualArchived);return retain(walk(nativeObject(actual.request().arguments()),"/arguments",true,0));
    }
    public static OpportunityJson.Obj decodeArguments(OpportunityJson.Obj publicArguments,PlanningReadReceipt actual,FamilyCurrentRelation.Observation actualArchived){
        requireContract(actual,actualArchived);OpportunityJson.Obj restored=retain(walk(nativeObject(Objects.requireNonNull(publicArguments)),"/arguments",false,0));need(restored.equals(actual.request().arguments()),"public relation arguments changed actual canonical input");return actual.request().arguments();
    }
    private static void requireContract(PlanningReadReceipt receipt,FamilyCurrentRelation.Observation actual){Objects.requireNonNull(receipt);Objects.requireNonNull(actual);need(receipt.contractId().equals(FamilyCurrentRelationQueries.CONTRACT_ID)&&receipt.request().operation().value().equals(FamilyCurrentRelation.STEP)&&InteractionArguments.context(receipt.request()).equals(actual.root().binding().context()),"public argument roles require the exact current relation contract and complete context");JsonNode args=nativeObject(receipt.request().arguments());need(field(args,"root_binding").equals(FamilyRootBinding.encode(actual.root())),"public relation arguments changed their actual original ROOT binding");}
    private static JsonNode walk(JsonNode value,String path,boolean encode,int depth){
        need(depth<=32,"public relation depth exceeds its original material bound");Role role=ROLES.get(path);
        if(role!=null){
            if(value.isNull())return value;BigInteger number;
            if(encode){need(value.isIntegralNumber(),"validated native64 role is not an integer: "+path);number=value.bigIntegerValue();}
            else {need(value.isTextual()&&value.textValue().length()<=20&&value.textValue().matches("-?(0|[1-9][0-9]*)")&&!value.textValue().equals("-0"),"canonical public native64 decimal string required: "+path);number=new BigInteger(value.textValue());}
            range(number,role==Role.U64?BigInteger.ZERO:I64_MIN,role==Role.U64?U64:I64_MAX);return encode?F.textNode(number.toString()):F.numberNode(number);
        }
        if(value.isObject()){ObjectNode out=F.objectNode();value.properties().forEach(field->out.set(field.getKey(),walk(field.getValue(),path+"/"+field.getKey(),encode,depth+1)));return out;}
        if(value.isArray()){var out=F.arrayNode();for(JsonNode item:value)out.add(walk(item,path+"/*",encode,depth+1));return out;}
        if(value.isIntegralNumber())need(value.bigIntegerValue().abs().compareTo(JS_MAX)<=0,"unknown unsafe integer has no declared current-relation public role: "+path);
        need(!value.isFloatingPointNumber(),"current-relation native public values cannot be floating tokens");return value.deepCopy();
    }
    private static void add(Map<String,Role> map,String prefix,Role role,String...fields){for(String field:fields)need(map.put(prefix+"/"+field,role)==null,"duplicate public numeric role");}
    private static Map<String,Role> roles(){
        Map<String,Role> out=new LinkedHashMap<>();
        add(out,"",Role.U64,"native_revision","root_query_sequence");add(out,"/source_frame/native_frame",Role.U64,"native_revision","connection_generation");for(String phase:List.of("public_before","public_after"))add(out,"/source_frame/"+phase,Role.U64,"revision");
        for(String source:List.of(FamilyRelationEducationProvider.SOURCE_LEAF,"current_child_relation_materials_source_v1"))add(out,"/"+source,Role.U64,"connection_generation","native_revision");
        String descendants="/"+FamilyRelationDescendants.LEAF;add(out,descendants,Role.U64,"native_revision");add(out,descendants+"/child_inputs",Role.U64,"native_revision");add(out,descendants+"/child_inputs/typed_windows",Role.U64,"native_revision");add(out,descendants+"/child_inputs/typed_windows/rows/*",Role.U64,"object_vtable_rva","object_col_rva","object_type_descriptor_rva");add(out,descendants+"/child_inputs/rows/*/court_owner_source",Role.U64,"native_revision","child_address","court_owner_address","getter_return_address","fallback_address");
        guardian(out,"/guardian_factory_materials_v2/observation");education(out,"/"+FamilyRelationEducationProvider.LEAF);childMaterials(out,"/"+FamilyRelationGuardianMaterials.CHILD_MATERIALS);
        educationDecision(out,"/family_generation_education_decision_inputs_v1");educationDecision(out,"/capture_decision");childMaterials(out,"/capture_decision/"+FamilyRelationGuardianMaterials.CHILD_MATERIALS);reproductive(out,"/"+FamilyRelationReproductive.LEAF);
        add(out,"/betrothal_actionability",Role.S64,"recipient_ai_accept_raw");for(String field:List.of("gold_raw","prestige_raw","piety_raw","renown_raw","influence_raw","herd_raw","treasury_raw","treasury_or_gold_raw","merit_raw","barter_goods_raw"))add(out,"/betrothal_actionability/generic_costs",Role.S64,field);
        add(out,"/arguments",Role.U64,"expected_native_revision");add(out,"/arguments/root_binding",Role.U64,"root_query_sequence");add(out,"/arguments/group_context",Role.U64,"connection_generation");return Map.copyOf(out);
    }
    private static void guardian(Map<String,Role> out,String p){
        add(out,p,Role.U64,"native_revision","module_base","image_size","pump_epoch");add(out,p+"/factories/*",Role.U64,"factory_address","vtable_address","opaque_descriptor_address");add(out,p+"/factories/*/factory_create_inputs_v1/field_18_qword",Role.U64,"raw_value");add(out,p+"/factories/*/virtual_slots/*",Role.U64,"address","rva");add(out,p+"/factories/*/rtti",Role.U64,"col_address","type_descriptor_address");add(out,p+"/current_family_relation_v1",Role.U64,"root_address","target_address","root_death_data_raw","target_death_data_raw");add(out,p+"/current_family_relation_v1/rows/*",Role.U64,"descriptor_raw","peer_address");childMaterials(out,p+"/"+FamilyRelationGuardianMaterials.CHILD_MATERIALS);education(out,p+"/"+FamilyRelationEducationProvider.LEAF);
    }
    private static void education(Map<String,Role> out,String p){add(out,p,Role.U64,"native_revision");}
    private static void childMaterials(Map<String,Role> out,String p){add(out,p+"/rows/*",Role.U64,"child_address");add(out,p+"/rows/*/peers",Role.U64,"extension_address","data_address");add(out,p+"/rows/*/peers/rows/*",Role.U64,"material_address","character_address","lookup_address");add(out,p+"/rows/*/guardian_named_material",Role.U64,"matched_peer_character_address");}
    private static void educationDecision(Map<String,Role> out,String p){add(out,p+"/frame",Role.U64,"native_revision");add(out,p+"/children/frame",Role.U64,"native_revision");add(out,p+"/children/rows/*/court_owner_source",Role.U64,"native_revision","child_address","court_owner_address","getter_return_address","fallback_address");}
    private static void reproductive(Map<String,Role> out,String p){
        add(out,p,Role.U64,"native_revision");String row=p+"/rows/*";add(out,row+"/native_fertility",Role.S64,"effective_raw");add(out,row+"/native_conception_extended_gate",Role.U64,"extended_288_raw_u64");add(out,row+"/native_conception_candidate_pending",Role.U64,"target_pointer_raw_u64");add(out,row+"/native_conception_first_value",Role.S64,"seed_after_children_raw","age_product_raw","first_output_raw");add(out,row+"/native_conception_second_value",Role.S64,"prefinal_raw","second_output_raw");
        String pair=p+"/conception_pair_inputs/pairs/*";add(out,pair+"/conditional_base_stage",Role.S64,"base_raw");for(String container:List.of("loaded_numeric_inputs","independent_numeric_inputs"))add(out,pair+"/"+container,Role.S64,"base_average_floor","linked_pair_addend","linked_pair_title_state_addend","both_title_state_absent_multiplier","first_relation_multiplier","second_relation_multiplier","alternate_relation_multiplier");add(out,pair+"/native_child_limit",Role.S64,"decrement_threshold_raw");add(out,pair+"/native_offspring_count/rows/*",Role.U64,"character_1d0_raw_u64");add(out,pair+"/native_second_title_state",Role.U64,"second_1c0_raw_u64");add(out,pair+"/native_secondary_family_membership",Role.U64,"list_span_bytes");add(out,pair+"/conditional_pair_provider",Role.S64,"first_output_raw");add(out,pair+"/conditional_pair_provider",Role.U64,"reached_stages_mask_u64");add(out,pair+"/conditional_short_circuit",Role.S64,"first_output_raw");for(String role:List.of("first","second"))add(out,pair+"/conditional_short_circuit/"+role,Role.S64,"rounded_modifier");add(out,pair+"/native_last_child_date",Role.S64,"selected_date_storage_raw64","adjusted_date_storage_raw64");natural(out,pair+"/natural_conception_observations_v1");naturalProjection(out,pair+"/natural_conception_observation");
    }
    private static void clock(Map<String,Role> out,String p){add(out,p,Role.U64,"clock_identity","sequence");}
    private static void key(Map<String,Role> out,String p){add(out,p,Role.U64,"clock_identity","parent_scope_id","process_clock","first_character","second_character","sample_receiver");}
    private static void natural(Map<String,Role> out,String p){
        add(out,p,Role.U64,"image_base","clock_identity","oldest_available_sequence","latest_sequence","overwritten_events","unattributed_identity_events","event_count");String event=p+"/events/*";add(out,event,Role.U64,"journal_sequence","caller_return_pc","caller_return_rva","first_character","second_character","sample_receiver");clock(out,event+"/before_event");clock(out,event+"/completed_event");for(String role:List.of("first_before","second_before","first_after","second_after"))add(out,event+"/"+role,Role.U64,"character","extended_pointer","pending_3f0_raw");
        String provider=event+"/provider";add(out,provider,Role.U64,"journal_sequence","caller_return_pc","caller_return_rva","output_pointer","first_character","second_character","fifth_argument","native_return_bits");add(out,provider,Role.S64,"output_before","output_after");key(out,provider+"/parent");clock(out,provider+"/before_event");clock(out,provider+"/returned_event");String sample=event+"/sample";add(out,sample,Role.U64,"oldest_available_sequence","latest_sequence","overwritten_events","event_count");String child=sample+"/events/*";add(out,child,Role.U64,"journal_sequence","caller_return_rva","receiver");add(out,child,Role.S64,"original_lower","original_upper","returned_rax_signed64","threshold_at_sample_signed64");key(out,child+"/parent");clock(out,child+"/before_event");clock(out,child+"/returned_event");
    }
    private static void guards(Map<String,Role> out,String p){add(out,p,Role.U64,"clock_identity","oldest_available_sequence","latest_sequence","overwritten_events","unattributed_identity_events");}
    private static void naturalProjection(Map<String,Role> out,String p){guards(out,p+"/journal_guards");guards(out,p+"/incoming_caller_source_binding/journal_guards");String row=p+"/records/*";add(out,row,Role.U64,"journal_sequence","caller_return_pc","caller_return_rva");key(out,row+"/original_parent_key");add(out,row+"/sample_comparison",Role.S64,"threshold_at_sample_signed64","returned_sample_signed64");add(out,row+"/provider_first_qword",Role.S64,"first_qword_raw","copied_output_before","copied_output_after");}
}
