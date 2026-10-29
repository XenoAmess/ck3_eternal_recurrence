package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_b2_pip_snapshot_contract.py; original SHA-256 e6ca1c8f711f24f25ac128d93e3336e92c945261443bbbd1b107247f8da19b77. No Python runtime. */
final class CasesPIPOriginalNormalizer {
    private CasesPIPOriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesPIPOriginalNormalizer::dispatch);
        e.put("ZHONGGUO_B2_PIP_CASE_KIND_V1",s("zhongguo.b2.pip"));
        e.put("ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION",s("1.19.0.6"));
        e.put("ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256",s("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"));
        e.put("ZHONGGUO_B2_PIP_SNAPSHOT_V1_BACKEND_ID",s("ck3-1.19.0.6-native-zhongguo-b2-pip-snapshot-v1"));
        e.put("ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID",s("xar-autoplayer-zhongguo-b2-pip-snapshot-v1"));
        e.put("ZHONGGUO_B2_PIP_SNAPSHOT_V1_ALLOWLIST_ID",s("zg361-b2-pip-received-self-v1"));
        e.put("_NONCE_RE",regex(text(s("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\\Z"))));
        e.put("_TYPED_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_GROUP_SPECS",dict(new Item(s("gate"),dict(new Item(s("owner_character_id"),s("int")),new Item(s("subject_character_id"),s("int")),new Item(s("cycle_serial"),s("int")),new Item(s("case_serial"),s("int")),new Item(s("threshold"),s("int")),new Item(s("negative_component_count"),s("int")),new Item(s("evidence_complete"),s("bool")),new Item(s("status"),s("int")),new Item(s("result_case_serial"),s("int")),new Item(s("result_grade"),s("int")),new Item(s("absolute_grade"),s("int")),new Item(s("kpi_frozen_q100000"),s("int")),new Item(s("governance_q100000"),s("int")),new Item(s("capability_q100000"),s("int")),new Item(s("growth_q100000"),s("int")),new Item(s("superior_q100000"),s("int")),new Item(s("values_q100000"),s("int")),new Item(s("collaboration_q100000"),s("int")),new Item(s("jingcha_q100000"),s("int")),new Item(s("organization_q100000"),s("int")))),new Item(s("pip"),dict(new Item(s("owner_character_id"),s("int")),new Item(s("subject_character_id"),s("int")),new Item(s("cycle_serial"),s("int")),new Item(s("case_serial"),s("int")),new Item(s("state"),s("int")),new Item(s("task_kind"),s("int")),new Item(s("task_controllable"),s("bool")),new Item(s("policy_route"),s("int")))),new Item(s("response"),dict(new Item(s("subject_response"),s("int")),new Item(s("response_case_serial"),s("int")),new Item(s("response_author_character_id"),s("int")),new Item(s("acknowledgement_receipt_serial"),s("int")),new Item(s("goal_revision_used"),s("bool")),new Item(s("refusal_receipt_serial"),s("int")))),new Item(s("support"),dict(new Item(s("capacity_reserved"),s("bool")),new Item(s("owner_capacity_used"),s("int")),new Item(s("support_absent"),s("bool")),new Item(s("hours"),s("int")),new Item(s("attention_units"),s("int")),new Item(s("mentor_character_id"),s("int")),new Item(s("budget_owner_character_id"),s("int")),new Item(s("treasury_budget_allocated"),s("int")),new Item(s("treasury_budget_spent"),s("int")),new Item(s("support_receipt_serial"),s("int")),new Item(s("released"),s("bool")),new Item(s("withheld"),s("bool")),new Item(s("atomic_shortfall"),s("bool")))),new Item(s("budget_ledger"),dict(new Item(s("result_case_serial"),s("int")),new Item(s("treasury_penalty_paid"),s("int")),new Item(s("personal_gold_penalty_paid"),s("int")),new Item(s("support_treasury_allocated"),s("int")),new Item(s("support_treasury_spent"),s("int")))),new Item(s("d180_ticket"),dict(new Item(s("owner_character_id"),s("int")),new Item(s("subject_character_id"),s("int")),new Item(s("cycle_serial"),s("int")),new Item(s("case_serial"),s("int")),new Item(s("expected_state"),s("int")),new Item(s("due_date_raw"),s("int")))),new Item(s("d365_ticket"),dict(new Item(s("owner_character_id"),s("int")),new Item(s("subject_character_id"),s("int")),new Item(s("cycle_serial"),s("int")),new Item(s("case_serial"),s("int")),new Item(s("expected_state"),s("int")),new Item(s("due_date_raw"),s("int")))),new Item(s("midpoint"),dict(new Item(s("receipt_serial"),s("int")),new Item(s("resource_delivery_valid"),s("bool")),new Item(s("progress_status"),s("int")),new Item(s("progress_red_code"),s("int")),new Item(s("state"),s("int")))),new Item(s("outcome"),dict(new Item(s("code"),s("int")),new Item(s("settlement_receipt_serial"),s("int")),new Item(s("result_cycle_serial"),s("int")),new Item(s("result_case_serial"),s("int")),new Item(s("result_grade"),s("int")),new Item(s("stability_days_observed"),s("int")),new Item(s("independent_review_status"),s("int")),new Item(s("independent_review_red_code"),s("int")),new Item(s("graduation_receipt_serial"),s("int")),new Item(s("failure_receipt_serial"),s("int")),new Item(s("no_support_liability"),s("bool")))),new Item(s("next_cycle_evidence"),dict(new Item(s("status"),s("int")),new Item(s("owner_character_id"),s("int")),new Item(s("subject_character_id"),s("int")),new Item(s("source_cycle_serial"),s("int")),new Item(s("source_case_serial"),s("int")),new Item(s("due_cycle_serial"),s("int")),new Item(s("delta"),s("int")),new Item(s("consumed_cycle_serial"),s("int")),new Item(s("consumed_case_serial"),s("int"))))));
        e.put("_READINESS_KEYS",set(p(s("player_subject_binding_ready")),p(s("owner_binding_ready")),p(s("gate_ready")),p(s("gate_evidence_ready")),p(s("pip_identity_ready")),p(s("response_ready")),p(s("support_ready")),p(s("budget_ledger_ready")),p(s("midpoint_ready")),p(s("outcome_ready")),p(s("next_cycle_evidence_ready")),p(s("d180_ticket_observation_ready")),p(s("d365_ticket_observation_ready")),p(s("modifier_observation_ready")),p(s("same_frame_ready")),p(s("ready"))));
        e.put("_PROVENANCE_VALUES",dict(new Item(s("game_version"),e.get("ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION")),new Item(s("executable_sha256"),e.get("ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256")),new Item(s("backend_id"),e.get("ZHONGGUO_B2_PIP_SNAPSHOT_V1_BACKEND_ID")),new Item(s("consumer_id"),e.get("ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID")),new Item(s("allowlist_id"),e.get("ZHONGGUO_B2_PIP_SNAPSHOT_V1_ALLOWLIST_ID")),new Item(s("variable_context_for_scope_rva"),s("0x3329A40")),new Item(s("variable_identifier_table_rva"),s("0x3B971A0")),new Item(s("variable_identifier_lookup_rva"),s("0x3B97020")),new Item(s("variable_identifier_name_rva"),s("0x3B97090")),new Item(s("character_storage_slot_rva"),s("0x570C130"))));
        e.put("_FRAME_KEYS",set(p(s("schema_version")),p(s("status")),p(s("case_kind")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("subject_character_id")),p(s("requested_owner_character_id")),spread(e.get("_GROUP_SPECS")),p(s("pip_modifier_present")),p(s("readiness")),p(s("unavailable_reason")),p(s("provenance"))));
        e.put("_TOP_REASONS",set(p(s("unsupported_build")),p(s("requires_application_main")),p(s("requires_paused")),p(s("map_not_ready")),p(s("case_not_found")),p(s("case_inconsistent")),p(s("owner_filter_mismatch")),p(s("not_received_self")),p(s("variable_identifier_unavailable")),p(s("variable_context_unavailable")),p(s("state_changed")),p(s("internal_error"))));
        e.put("_FIELD_REASONS",set(p(s("case_unavailable")),p(s("variable_absent")),p(s("value_type_mismatch")),p(s("value_out_of_range")),p(s("case_binding_mismatch")),p(s("product_not_persisted")),p(s("native_observation_unavailable")),p(s("not_applicable"))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_b2_pip_snapshot_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_all_available" -> f_all_available(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED),new Param("keys",NONE)),List.of(),null),args));
            case "_available" -> f_available(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED)),List.of(),null),args));
            case "_exact" -> f_exact(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("keys",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_field_equals" -> f_field_equals(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED),new Param("expected",REQUIRED)),List.of(),null),args));
            case "_group" -> f_group(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_integer" -> f_integer(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED),new Param("minimum",REQUIRED),new Param("maximum",REQUIRED)),List.of(),null),args));
            case "_integer_field_in_range" -> f_integer_field_in_range(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED),new Param("minimum",REQUIRED),new Param("maximum",REQUIRED)),List.of(),null),args));
            case "_positive_int32" -> f_positive_int32(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed" -> f_typed(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED),new Param("kind",REQUIRED)),List.of(),null),args));
            case "_unavailable_for" -> f_unavailable_for(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED),new Param("reason",REQUIRED)),List.of(),null),args));
            case "_value" -> f_value(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_b2_pip_snapshot_v1" -> fnormalize_native_zhongguo_b2_pip_snapshot_v1(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            case "validate_b2_pip_request_nonce_v1" -> fvalidate_b2_pip_request_nonce_v1(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(),null),args));
            case "ZhongguoB2PipQueryV1" -> new D(new LinkedHashMap<>(bind(GLOBALS,CasesPIPOriginalNormalizer::dispatch,new Sig(List.of(new Param("owner_character_id",REQUIRED),new Param("request_nonce",REQUIRED)),List.of(),null),args).locals));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:373..375
    private static V f_all_available(E e){
        assign(e,new NameTarget("selected"),(truth(compare(e,e.get("keys"),new Comparison(Cmp.IS_NOT,q1->NONE)))?e.get("keys"):call(e,"set",args(new Part[]{p(e.get("group"))}))));
        return call(e,"all",args(new Part[]{p(generator(e,q2->call(q2,"_available",args(new Part[]{p(get(q2.get("group"),q2.get("key")))})),new Clause(new NameTarget("key"),q3->q3.get("selected"),List.of())))}));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:347..348
    private static V f_available(E e){
        return compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q4->s("available")));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:264..267
    private static V f_exact(E e){
        if(truth(or(e,q5->b(!truth(call(q5,"isinstance",args(new Part[]{p(q5.get("value")),p(q5.get("dict"))})))),q6->compare(q6,call(q6,"set",args(new Part[]{p(q6.get("value"))})),new Comparison(Cmp.NE,q7->q7.get("keys")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:390..391
    private static V f_field_equals(E e){
        return and(e,q8->call(q8,"_available",args(new Part[]{p(q8.get("field"))})),q9->compare(q9,get(q9.get("field"),s("value")),new Comparison(Cmp.EQ,q10->q10.get("expected"))));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:364..370
    private static V f_group(E e){
        assign(e,new NameTarget("spec"),get(e.get("_GROUP_SPECS"),e.get("name")));
        assign(e,new NameTarget("raw"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(call(e,"set",args(new Part[]{p(e.get("spec"))}))),p(e.get("name"))})));
        return dictFrom(iter(generator(e,q11->seq(true,p(q11.get("key")),p(call(q11,"_typed",args(new Part[]{p(get(q11.get("raw"),q11.get("key"))),p(joined(s(py(q11.get("name"))),s("."),s(py(q11.get("key"))))),p(q11.get("kind"))})))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("kind"))),q12->method(q12.get("spec"),"items",args(new Part[]{})),List.of()))));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:270..277
    private static V f_integer(E e){
        if(truth(or(e,q13->call(q13,"isinstance",args(new Part[]{p(q13.get("value")),p(q13.get("bool"))})),q14->b(!truth(call(q14,"isinstance",args(new Part[]{p(q14.get("value")),p(q14.get("int"))})))),q15->b(!truth(compare(q15,q15.get("minimum"),new Comparison(Cmp.LE,q16->q16.get("value")),new Comparison(Cmp.LE,q17->q17.get("maximum")))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be an integer in range"))));
        }
        return e.get("value");
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:378..387
    private static V f_integer_field_in_range(E e){
        assign(e,new NameTarget("value"),get(e.get("field"),s("value")));
        return and(e,q18->call(q18,"_available",args(new Part[]{p(q18.get("field"))})),q19->call(q19,"isinstance",args(new Part[]{p(q19.get("value")),p(q19.get("int"))})),q20->b(!truth(call(q20,"isinstance",args(new Part[]{p(q20.get("value")),p(q20.get("bool"))})))),q21->compare(q21,q21.get("minimum"),new Comparison(Cmp.LE,q22->q22.get("value")),new Comparison(Cmp.LE,q23->q23.get("maximum"))));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:280..281
    private static V f_positive_int32(E e){
        return call(e,"_integer",args(new Part[]{p(e.get("value")),p(e.get("name")),p(n("1")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1")))}));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:329..344
    private static V f_typed(E e){
        assign(e,new NameTarget("field"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_KEYS")),p(e.get("name"))})));
        assign(e,new NameTarget("status"),get(e.get("field"),s("status")));
        assign(e,new NameTarget("raw"),get(e.get("field"),s("value")));
        assign(e,new NameTarget("reason"),get(e.get("field"),s("unavailable_reason")));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q24->s("unavailable"))))) {
            if(truth(or(e,q25->compare(q25,q25.get("raw"),new Comparison(Cmp.IS_NOT,q26->NONE)),q27->compare(q27,q27.get("reason"),new Comparison(Cmp.NOT_IN,q28->q28.get("_FIELD_REASONS")))))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid typed unavailability"))));
            }
        } else {
            if(truth(and(e,q29->compare(q29,q29.get("status"),new Comparison(Cmp.EQ,q30->s("available"))),q31->compare(q31,q31.get("reason"),new Comparison(Cmp.IS,q32->NONE))))) {
                if(truth(compare(e,e.get("kind"),new Comparison(Cmp.EQ,q33->s("int"))))) {
                    call(e,"_integer",args(new Part[]{p(e.get("raw")),p(e.get("name")),p(negate(binary(Op.POW,n("2"),n("63")))),p(binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))}));
                } else {
                    if(truth(and(e,q34->compare(q34,q34.get("kind"),new Comparison(Cmp.EQ,q35->s("bool"))),q36->b(!truth(call(q36,"isinstance",args(new Part[]{p(q36.get("raw")),p(q36.get("bool"))}))))))) {
                        throw new Rejected(py(joined(s(py(e.get("name"))),s(".value must be boolean"))));
                    }
                }
            } else {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid typed availability"))));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:351..355
    private static V f_unavailable_for(E e){
        return and(e,q37->compare(q37,get(q37.get("field"),s("status")),new Comparison(Cmp.EQ,q38->s("unavailable"))),q39->compare(q39,get(q39.get("field"),s("unavailable_reason")),new Comparison(Cmp.EQ,q40->q40.get("reason"))));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:358..361
    private static V f_value(E e){
        if(truth(b(!truth(call(e,"_available",args(new Part[]{p(e.get("field"))})))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be available"))));
        }
        return get(e.get("field"),s("value"));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:404..954
    private static V fnormalize_native_zhongguo_b2_pip_snapshot_v1(E e){
        assign(e,new NameTarget("expected_query"),call(e,"ZhongguoB2PipQueryV1",args(new Part[]{p(call(e,"_positive_int32",args(new Part[]{p(attribute(e.get("expected_query"),"owner_character_id")),p(s("expected owner"))}))),p(call(e,"validate_b2_pip_request_nonce_v1",args(new Part[]{p(attribute(e.get("expected_query"),"request_nonce"))})))})));
        assign(e,new NameTarget("expected_snapshot_revision"),call(e,"_integer",args(new Part[]{p(e.get("expected_snapshot_revision")),p(s("expected_snapshot_revision")),p(n("1")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1")))})));
        assign(e,new NameTarget("expected_date_raw"),call(e,"_integer",args(new Part[]{p(e.get("expected_date_raw")),p(s("expected_date_raw")),p(negate(binary(Op.POW,n("2"),n("31")))),p(binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1")))})));
        assign(e,new NameTarget("expected_player_character_id"),call(e,"_positive_int32",args(new Part[]{p(e.get("expected_player_character_id")),p(s("expected_player_character_id"))})));
        assign(e,new NameTarget("frame"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_FRAME_KEYS")),p(s("zhongguo_b2_pip_snapshot"))})));
        if(truth(compare(e,get(e.get("frame"),s("schema_version")),new Comparison(Cmp.NE,q41->n("1"))))) {
            throw new Rejected(py(s("schema_version must be 1")));
        }
        if(truth(compare(e,get(e.get("frame"),s("case_kind")),new Comparison(Cmp.NE,q42->q42.get("ZHONGGUO_B2_PIP_CASE_KIND_V1"))))) {
            throw new Rejected(py(s("case_kind binding changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("request_nonce")),new Comparison(Cmp.NE,q43->attribute(q43.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("request_nonce binding changed")));
        }
        if(truth(compare(e,call(e,"_integer",args(new Part[]{p(get(e.get("frame"),s("snapshot_revision"))),p(s("snapshot_revision")),p(n("1")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1")))})),new Comparison(Cmp.NE,q44->q44.get("expected_snapshot_revision"))))) {
            throw new Rejected(py(s("snapshot revision binding changed")));
        }
        if(truth(compare(e,call(e,"_integer",args(new Part[]{p(get(e.get("frame"),s("date_raw"))),p(s("date_raw")),p(negate(binary(Op.POW,n("2"),n("31")))),p(binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1")))})),new Comparison(Cmp.NE,q45->q45.get("expected_date_raw"))))) {
            throw new Rejected(py(s("date binding changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("paused")),new Comparison(Cmp.IS_NOT,q46->TRUE)))) {
            throw new Rejected(py(s("B2 PIP query is not paused")));
        }
        assign(e,new NameTarget("player"),call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("player_character_id"))),p(s("player_character_id"))})));
        assign(e,new NameTarget("subject"),call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("subject_character_id"))),p(s("subject_character_id"))})));
        if(truth(or(e,q47->compare(q47,q47.get("player"),new Comparison(Cmp.NE,q48->q48.get("expected_player_character_id"))),q49->compare(q49,q49.get("subject"),new Comparison(Cmp.NE,q50->q50.get("player")))))) {
            throw new Rejected(py(s("received-self subject binding changed")));
        }
        if(truth(compare(e,call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("requested_owner_character_id"))),p(s("requested owner"))})),new Comparison(Cmp.NE,q51->attribute(q51.get("expected_query"),"owner_character_id"))))) {
            throw new Rejected(py(s("owner filter binding changed")));
        }
        assign(e,new NameTarget("groups"),dictFrom(iter(generator(e,q52->seq(true,p(q52.get("name")),p(call(q52,"_group",args(new Part[]{p(get(q52.get("frame"),q52.get("name"))),p(q52.get("name"))})))),new Clause(new NameTarget("name"),q53->q53.get("_GROUP_SPECS"),List.of())))));
        for(V q54:iter(seq(true,p(seq(true,p(s("gate")),p(s("owner_character_id")))),p(seq(true,p(s("gate")),p(s("subject_character_id")))),p(seq(true,p(s("pip")),p(s("owner_character_id")))),p(seq(true,p(s("pip")),p(s("subject_character_id")))),p(seq(true,p(s("response")),p(s("response_author_character_id")))),p(seq(true,p(s("support")),p(s("mentor_character_id")))),p(seq(true,p(s("support")),p(s("budget_owner_character_id")))),p(seq(true,p(s("next_cycle_evidence")),p(s("owner_character_id")))),p(seq(true,p(s("next_cycle_evidence")),p(s("subject_character_id"))))))) {
            assign(e,new TupleTarget(List.of(new NameTarget("group_name"),new NameTarget("field_name"))),q54);
            assign(e,new NameTarget("character_field"),get(get(e.get("groups"),e.get("group_name")),e.get("field_name")));
            if(truth(and(e,q55->call(q55,"_available",args(new Part[]{p(q55.get("character_field"))})),q56->b(!truth(call(q56,"_integer_field_in_range",args(new Part[]{p(q56.get("character_field")),p(n("1")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1")))}))))))) {
                throw new Rejected(py(joined(s(py(e.get("group_name"))),s("."),s(py(e.get("field_name"))),s(" is not a valid character"))));
            }
        }
        assign(e,new NameTarget("modifier"),call(e,"_typed",args(new Part[]{p(get(e.get("frame"),s("pip_modifier_present"))),p(s("pip_modifier_present")),p(s("bool"))})));
        assign(e,new NameTarget("readiness_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("readiness"))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        assign(e,new NameTarget("readiness"),dict());
        for(V q57:iter(e.get("_READINESS_KEYS"))) {
            assign(e,new NameTarget("key"),q57);
            if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(get(e.get("readiness_raw"),e.get("key"))),p(e.get("bool"))})))))) {
                throw new Rejected(py(joined(s("readiness."),s(py(e.get("key"))),s(" must be boolean"))));
            }
            put(e.get("readiness"),e.get("key"),get(e.get("readiness_raw"),e.get("key")));
        }
        assign(e,new NameTarget("expected_ready"),call(e,"all",args(new Part[]{p(generator(e,q58->get(q58.get("readiness"),q58.get("key")),new Clause(new NameTarget("key"),q59->seq(true,p(s("player_subject_binding_ready")),p(s("owner_binding_ready")),p(s("gate_ready")),p(s("same_frame_ready"))),List.of())))})));
        if(truth(compare(e,get(e.get("readiness"),s("ready")),new Comparison(Cmp.IS_NOT,q60->q60.get("expected_ready"))))) {
            throw new Rejected(py(s("readiness.ready disagrees with the identity gate")));
        }
        assign(e,new NameTarget("provenance"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("provenance"))),p(call(e,"set",args(new Part[]{p(e.get("_PROVENANCE_VALUES"))}))),p(s("provenance"))})));
        if(truth(call(e,"any",args(new Part[]{p(generator(e,q61->compare(q61,get(q61.get("provenance"),q61.get("key")),new Comparison(Cmp.NE,q63->q63.get("expected"))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("expected"))),q62->method(q62.get("_PROVENANCE_VALUES"),"items",args(new Part[]{})),List.of())))})))) {
            throw new Rejected(py(s("provenance does not match the frozen exact build")));
        }
        assign(e,new NameTarget("status"),get(e.get("frame"),s("status")));
        assign(e,new NameTarget("reason"),get(e.get("frame"),s("unavailable_reason")));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q64->s("unavailable"))))) {
            if(truth(or(e,q65->compare(q65,q65.get("reason"),new Comparison(Cmp.NOT_IN,q66->q66.get("_TOP_REASONS"))),q67->get(q67.get("readiness"),s("ready"))))) {
                throw new Rejected(py(s("unavailable frame has an invalid reason/gate")));
            }
            assign(e,new NameTarget("expected_same_frame"),compare(e,e.get("reason"),new Comparison(Cmp.IN,q68->set(p(s("case_not_found")),p(s("case_inconsistent")),p(s("owner_filter_mismatch")),p(s("not_received_self"))))));
            if(truth(or(e,q69->compare(q69,get(q69.get("readiness"),s("same_frame_ready")),new Comparison(Cmp.IS_NOT,q70->q70.get("expected_same_frame"))),q71->call(q71,"any",args(new Part[]{p(generator(q71,q72->get(q72.get("readiness"),q72.get("key")),new Clause(new NameTarget("key"),q73->binary(Op.SUB,q73.get("_READINESS_KEYS"),set(p(s("same_frame_ready")))),List.of())))}))))) {
                throw new Rejected(py(s("unavailable frame fabricates component readiness")));
            }
            for(V q74:iter(method(e.get("groups"),"items",args(new Part[]{})))) {
                assign(e,new TupleTarget(List.of(new NameTarget("name"),new NameTarget("group"))),q74);
                if(truth(call(e,"any",args(new Part[]{p(generator(e,q75->or(q75,q77->compare(q77,get(q77.get("field"),s("status")),new Comparison(Cmp.NE,q78->s("unavailable"))),q79->compare(q79,get(q79.get("field"),s("unavailable_reason")),new Comparison(Cmp.NE,q80->s("case_unavailable")))),new Clause(new NameTarget("field"),q76->method(q76.get("group"),"values",args(new Part[]{})),List.of())))})))) {
                    throw new Rejected(py(joined(s("unavailable frame leaks "),s(py(e.get("name"))))));
                }
            }
            if(truth(compare(e,get(e.get("modifier"),s("unavailable_reason")),new Comparison(Cmp.NE,q81->s("case_unavailable"))))) {
                throw new Rejected(py(s("unavailable frame leaks modifier state")));
            }
        } else {
            if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q82->s("available"))))) {
                if(truth(compare(e,e.get("reason"),new Comparison(Cmp.IS_NOT,q83->NONE)))) {
                    throw new Rejected(py(s("available frame has an unavailable reason")));
                }
                assign(e,new NameTarget("gate"),get(e.get("groups"),s("gate")));
                assign(e,new NameTarget("gate_core"),set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("threshold")),p(s("negative_component_count")),p(s("evidence_complete")),p(s("status"))));
                assign(e,new NameTarget("gate_ready"),call(e,"_all_available",args(new Part[]{p(e.get("gate")),p(e.get("gate_core"))})));
                if(truth(e.get("gate_ready"))) {
                    assign(e,new NameTarget("gate_complete"),call(e,"_value",args(new Part[]{p(get(e.get("gate"),s("evidence_complete"))),p(s("gate.evidence_complete"))})));
                    assign(e,new NameTarget("gate_status"),call(e,"_integer",args(new Part[]{p(call(e,"_value",args(new Part[]{p(get(e.get("gate"),s("status"))),p(s("gate.status"))}))),p(s("gate.status")),p(n("0")),p(n("3"))})));
                    assign(e,new NameTarget("gate_ready"),and(e,q84->compare(q84,call(q84,"_positive_int32",args(new Part[]{p(call(q84,"_value",args(new Part[]{p(get(q84.get("gate"),s("owner_character_id"))),p(s("gate.owner"))}))),p(s("gate.owner"))})),new Comparison(Cmp.EQ,q85->attribute(q85.get("expected_query"),"owner_character_id"))),q86->compare(q86,call(q86,"_positive_int32",args(new Part[]{p(call(q86,"_value",args(new Part[]{p(get(q86.get("gate"),s("subject_character_id"))),p(s("gate.subject"))}))),p(s("gate.subject"))})),new Comparison(Cmp.EQ,q87->q87.get("player"))),q88->compare(q88,call(q88,"_integer",args(new Part[]{p(call(q88,"_value",args(new Part[]{p(get(q88.get("gate"),s("cycle_serial"))),p(s("gate.cycle"))}))),p(s("gate.cycle")),p(n("1")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))})),new Comparison(Cmp.GE,q89->n("1"))),q90->compare(q90,n("1"),new Comparison(Cmp.LE,q91->call(q91,"_integer",args(new Part[]{p(call(q91,"_value",args(new Part[]{p(get(q91.get("gate"),s("case_serial"))),p(s("gate.case"))}))),p(s("gate.case")),p(n("1")),p(n("999999"))}))),new Comparison(Cmp.LE,q92->n("999999"))),q93->compare(q93,call(q93,"_value",args(new Part[]{p(get(q93.get("gate"),s("threshold"))),p(s("gate.threshold"))})),new Comparison(Cmp.EQ,q94->n("3"))),q95->compare(q95,n("0"),new Comparison(Cmp.LE,q96->call(q96,"_integer",args(new Part[]{p(call(q96,"_value",args(new Part[]{p(get(q96.get("gate"),s("negative_component_count"))),p(s("gate.count"))}))),p(s("gate.count")),p(n("0")),p(n("10"))}))),new Comparison(Cmp.LE,q97->n("10"))),q98->compare(q98,n("0"),new Comparison(Cmp.LE,q99->q99.get("gate_status")),new Comparison(Cmp.LE,q100->n("3"))),q101->or(q101,q102->and(q102,q103->compare(q103,q103.get("gate_complete"),new Comparison(Cmp.IS,q104->TRUE)),q105->compare(q105,q105.get("gate_status"),new Comparison(Cmp.NE,q106->n("0")))),q107->and(q107,q108->compare(q108,q108.get("gate_complete"),new Comparison(Cmp.IS,q109->FALSE)),q110->compare(q110,q110.get("gate_status"),new Comparison(Cmp.EQ,q111->n("0")))))));
                }
                if(truth(compare(e,get(e.get("readiness"),s("gate_ready")),new Comparison(Cmp.IS_NOT,q112->q112.get("gate_ready"))))) {
                    throw new Rejected(py(s("gate readiness disagrees with frozen gate")));
                }
                assign(e,new NameTarget("pip"),get(e.get("groups"),s("pip")));
                assign(e,new NameTarget("any_pip"),call(e,"any",args(new Part[]{p(generator(e,q113->b(!truth(call(q113,"_unavailable_for",args(new Part[]{p(q113.get("field")),p(s("variable_absent"))})))),new Clause(new NameTarget("field"),q114->method(q114.get("pip"),"values",args(new Part[]{})),List.of())))})));
                assign(e,new NameTarget("pip_ready"),and(e,q115->q115.get("gate_ready"),q116->call(q116,"_all_available",args(new Part[]{p(q116.get("pip"))}))));
                if(truth(e.get("pip_ready"))) {
                    assign(e,new NameTarget("pip_ready"),and(e,q117->compare(q117,call(q117,"_value",args(new Part[]{p(get(q117.get("pip"),s("owner_character_id"))),p(s("pip.owner"))})),new Comparison(Cmp.EQ,q118->attribute(q118.get("expected_query"),"owner_character_id"))),q119->compare(q119,call(q119,"_value",args(new Part[]{p(get(q119.get("pip"),s("subject_character_id"))),p(s("pip.subject"))})),new Comparison(Cmp.EQ,q120->q120.get("player"))),q121->compare(q121,n("1"),new Comparison(Cmp.LE,q122->call(q122,"_integer",args(new Part[]{p(call(q122,"_value",args(new Part[]{p(get(q122.get("pip"),s("cycle_serial"))),p(s("pip.cycle"))}))),p(s("pip.cycle")),p(n("1")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("2")))})))),q123->compare(q123,n("1"),new Comparison(Cmp.LE,q124->call(q124,"_integer",args(new Part[]{p(call(q124,"_value",args(new Part[]{p(get(q124.get("pip"),s("case_serial"))),p(s("pip.case"))}))),p(s("pip.case")),p(n("1")),p(n("999999"))}))),new Comparison(Cmp.LE,q125->n("999999"))),q126->call(q126,"_field_equals",args(new Part[]{p(get(q126.get("pip"),s("cycle_serial"))),p(get(get(q126.get("gate"),s("cycle_serial")),s("value")))})),q127->call(q127,"_field_equals",args(new Part[]{p(get(q127.get("pip"),s("case_serial"))),p(get(get(q127.get("gate"),s("case_serial")),s("value")))})),q128->compare(q128,n("1"),new Comparison(Cmp.LE,q129->call(q129,"_integer",args(new Part[]{p(call(q129,"_value",args(new Part[]{p(get(q129.get("pip"),s("state"))),p(s("pip.state"))}))),p(s("pip.state")),p(n("1")),p(n("5"))}))),new Comparison(Cmp.LE,q130->n("5"))),q131->compare(q131,n("1"),new Comparison(Cmp.LE,q132->call(q132,"_integer",args(new Part[]{p(call(q132,"_value",args(new Part[]{p(get(q132.get("pip"),s("task_kind"))),p(s("pip.task_kind"))}))),p(s("pip.task_kind")),p(n("1")),p(n("3"))}))),new Comparison(Cmp.LE,q133->n("3"))),q134->compare(q134,n("1"),new Comparison(Cmp.LE,q135->call(q135,"_integer",args(new Part[]{p(call(q135,"_value",args(new Part[]{p(get(q135.get("pip"),s("policy_route"))),p(s("pip.policy_route"))}))),p(s("pip.policy_route")),p(n("1")),p(n("2"))}))),new Comparison(Cmp.LE,q136->n("2")))));
                }
                if(truth(compare(e,get(e.get("readiness"),s("pip_identity_ready")),new Comparison(Cmp.IS_NOT,q137->q137.get("pip_ready"))))) {
                    throw new Rejected(py(s("PIP identity readiness disagrees with fields")));
                }
                if(truth(and(e,q138->q138.get("any_pip"),q139->b(!truth(q139.get("pip_ready")))))) {
                    throw new Rejected(py(s("available frame contains an inconsistent PIP")));
                }
                assign(e,new NameTarget("player_binding_ready"),and(e,q140->call(q140,"_field_equals",args(new Part[]{p(get(q140.get("gate"),s("subject_character_id"))),p(q140.get("player"))})),q141->or(q141,q142->b(!truth(q142.get("any_pip"))),q143->call(q143,"_field_equals",args(new Part[]{p(get(q143.get("pip"),s("subject_character_id"))),p(q143.get("player"))})))));
                assign(e,new NameTarget("owner_binding_ready"),and(e,q144->call(q144,"_field_equals",args(new Part[]{p(get(q144.get("gate"),s("owner_character_id"))),p(attribute(q144.get("expected_query"),"owner_character_id"))})),q145->or(q145,q146->b(!truth(q146.get("any_pip"))),q147->call(q147,"_field_equals",args(new Part[]{p(get(q147.get("pip"),s("owner_character_id"))),p(attribute(q147.get("expected_query"),"owner_character_id"))})))));
                if(truth(or(e,q148->compare(q148,get(q148.get("readiness"),s("player_subject_binding_ready")),new Comparison(Cmp.IS_NOT,q149->q149.get("player_binding_ready"))),q150->compare(q150,get(q150.get("readiness"),s("owner_binding_ready")),new Comparison(Cmp.IS_NOT,q151->q151.get("owner_binding_ready"))),q152->b(!truth(q152.get("player_binding_ready"))),q153->b(!truth(q153.get("owner_binding_ready"))),q154->compare(q154,get(q154.get("readiness"),s("same_frame_ready")),new Comparison(Cmp.IS_NOT,q155->TRUE))))) {
                    throw new Rejected(py(s("available frame lacks its same-frame subject/owner binding")));
                }
                assign(e,new NameTarget("evidence_names"),seq(true,p(s("governance_q100000")),p(s("capability_q100000")),p(s("growth_q100000")),p(s("superior_q100000")),p(s("values_q100000")),p(s("collaboration_q100000")),p(s("jingcha_q100000")),p(s("organization_q100000"))));
                assign(e,new NameTarget("gate_evidence_ready"),and(e,q156->q156.get("gate_ready"),q157->call(q157,"_all_available",args(new Part[]{p(q157.get("gate")),p(set(p(s("result_case_serial")),p(s("result_grade")),p(s("absolute_grade")),p(s("kpi_frozen_q100000")),spread(q157.get("evidence_names"))))}))));
                if(truth(e.get("gate_evidence_ready"))) {
                    assign(e,new NameTarget("negative_count"),call(e,"int",args(new Part[]{p(compare(e,call(e,"_value",args(new Part[]{p(get(e.get("gate"),s("absolute_grade"))),p(s("gate.absolute_grade"))})),new Comparison(Cmp.EQ,q158->n("1"))))})));
                    assign(e,new NameTarget("negative_count"),binary(Op.ADD,e.get("negative_count"),call(e,"int",args(new Part[]{p(compare(e,call(e,"_value",args(new Part[]{p(get(e.get("gate"),s("kpi_frozen_q100000"))),p(s("gate.kpi"))})),new Comparison(Cmp.LT,q159->n("0"))))}))));
                    assign(e,new NameTarget("negative_count"),binary(Op.ADD,e.get("negative_count"),call(e,"sum",args(new Part[]{p(generator(e,q160->call(q160,"int",args(new Part[]{p(compare(q160,call(q160,"_value",args(new Part[]{p(get(q160.get("gate"),q160.get("name"))),p(joined(s("gate."),s(py(q160.get("name")))))})),new Comparison(Cmp.LT,q162->n("0"))))})),new Clause(new NameTarget("name"),q161->q161.get("evidence_names"),List.of())))}))));
                    assign(e,new NameTarget("gate_evidence_ready"),and(e,q163->compare(q163,call(q163,"_value",args(new Part[]{p(get(q163.get("gate"),s("evidence_complete"))),p(s("gate.evidence_complete"))})),new Comparison(Cmp.IS,q164->TRUE)),q165->call(q165,"_field_equals",args(new Part[]{p(get(q165.get("gate"),s("result_case_serial"))),p(get(get(q165.get("gate"),s("case_serial")),s("value")))})),q166->call(q166,"_integer_field_in_range",args(new Part[]{p(get(q166.get("gate"),s("result_grade"))),p(n("1")),p(n("3"))})),q167->call(q167,"_integer_field_in_range",args(new Part[]{p(get(q167.get("gate"),s("absolute_grade"))),p(n("1")),p(n("3"))})),q168->call(q168,"_field_equals",args(new Part[]{p(get(q168.get("gate"),s("negative_component_count"))),p(q168.get("negative_count"))}))));
                }
                if(truth(compare(e,get(e.get("readiness"),s("gate_evidence_ready")),new Comparison(Cmp.IS_NOT,q169->q169.get("gate_evidence_ready"))))) {
                    throw new Rejected(py(s("gate evidence readiness disagrees with frozen evidence")));
                }
                assign(e,new NameTarget("response"),get(e.get("groups"),s("response")));
                assign(e,new NameTarget("response_ready"),FALSE);
                if(truth(e.get("pip_ready"))) {
                    assign(e,new NameTarget("pip_case"),get(get(e.get("pip"),s("case_serial")),s("value")));
                    assign(e,new NameTarget("pip_state"),get(get(e.get("pip"),s("state")),s("value")));
                    assign(e,new NameTarget("response_code"),get(get(e.get("response"),s("subject_response")),s("value")));
                    assign(e,new NameTarget("pending"),and(e,q170->compare(q170,q170.get("pip_state"),new Comparison(Cmp.EQ,q171->n("1"))),q172->compare(q172,q172.get("response_code"),new Comparison(Cmp.EQ,q173->n("0"))),q174->call(q174,"_field_equals",args(new Part[]{p(get(q174.get("response"),s("response_case_serial"))),p(n("0"))})),q175->call(q175,"_unavailable_for",args(new Part[]{p(get(q175.get("response"),s("response_author_character_id"))),p(s("variable_absent"))})),q176->call(q176,"_field_equals",args(new Part[]{p(get(q176.get("response"),s("refusal_receipt_serial"))),p(n("0"))}))));
                    assign(e,new NameTarget("accepted"),and(e,q177->compare(q177,q177.get("pip_state"),new Comparison(Cmp.IN,q178->seq(true,p(n("2")),p(n("3")),p(n("4"))))),q179->compare(q179,q179.get("response_code"),new Comparison(Cmp.IN,q180->seq(true,p(n("1")),p(n("2"))))),q181->call(q181,"_field_equals",args(new Part[]{p(get(q181.get("response"),s("response_case_serial"))),p(q181.get("pip_case"))})),q182->call(q182,"_field_equals",args(new Part[]{p(get(q182.get("response"),s("response_author_character_id"))),p(q182.get("player"))})),q183->call(q183,"_field_equals",args(new Part[]{p(get(q183.get("response"),s("refusal_receipt_serial"))),p(n("0"))}))));
                    assign(e,new NameTarget("refused"),and(e,q184->compare(q184,q184.get("pip_state"),new Comparison(Cmp.EQ,q185->n("5"))),q186->compare(q186,q186.get("response_code"),new Comparison(Cmp.EQ,q187->n("3"))),q188->call(q188,"_field_equals",args(new Part[]{p(get(q188.get("response"),s("response_case_serial"))),p(q188.get("pip_case"))})),q189->call(q189,"_field_equals",args(new Part[]{p(get(q189.get("response"),s("response_author_character_id"))),p(q189.get("player"))})),q190->call(q190,"_field_equals",args(new Part[]{p(get(q190.get("response"),s("refusal_receipt_serial"))),p(q190.get("pip_case"))}))));
                    assign(e,new NameTarget("response_ready"),and(e,q191->call(q191,"_field_equals",args(new Part[]{p(get(q191.get("response"),s("acknowledgement_receipt_serial"))),p(q191.get("pip_case"))})),q192->call(q192,"_available",args(new Part[]{p(get(q192.get("response"),s("goal_revision_used")))})),q193->or(q193,q194->q194.get("pending"),q195->q195.get("accepted"),q196->q196.get("refused"))));
                }
                if(truth(compare(e,get(e.get("readiness"),s("response_ready")),new Comparison(Cmp.IS_NOT,q197->q197.get("response_ready"))))) {
                    throw new Rejected(py(s("response readiness disagrees with PIP receipt")));
                }
                assign(e,new NameTarget("support"),get(e.get("groups"),s("support")));
                assign(e,new NameTarget("support_ready"),FALSE);
                if(truth(e.get("pip_ready"))) {
                    assign(e,new NameTarget("reserved"),get(get(e.get("support"),s("capacity_reserved")),s("value")));
                    assign(e,new NameTarget("absent"),get(get(e.get("support"),s("support_absent")),s("value")));
                    assign(e,new NameTarget("core_support"),and(e,q198->call(q198,"_available",args(new Part[]{p(get(q198.get("support"),s("capacity_reserved")))})),q199->call(q199,"_available",args(new Part[]{p(get(q199.get("support"),s("support_absent")))})),q200->call(q200,"_integer_field_in_range",args(new Part[]{p(get(q200.get("support"),s("hours"))),p(n("0")),p(n("12"))})),q201->call(q201,"_integer_field_in_range",args(new Part[]{p(get(q201.get("support"),s("attention_units"))),p(n("0")),p(n("1"))})),q202->call(q202,"_integer_field_in_range",args(new Part[]{p(get(q202.get("support"),s("treasury_budget_allocated"))),p(n("0")),p(n("25"))})),q203->call(q203,"_integer_field_in_range",args(new Part[]{p(get(q203.get("support"),s("treasury_budget_spent"))),p(n("0")),p(n("25"))})),q204->call(q204,"_field_equals",args(new Part[]{p(get(q204.get("support"),s("support_receipt_serial"))),p(get(get(q204.get("pip"),s("case_serial")),s("value")))}))));
                    assign(e,new NameTarget("reserved_package"),and(e,q205->compare(q205,get(get(q205.get("pip"),s("state")),s("value")),new Comparison(Cmp.EQ,q206->n("2"))),q207->compare(q207,q207.get("reserved"),new Comparison(Cmp.IS,q208->TRUE)),q209->compare(q209,q209.get("absent"),new Comparison(Cmp.IS,q210->FALSE)),q211->call(q211,"_field_equals",args(new Part[]{p(get(q211.get("support"),s("hours"))),p(n("12"))})),q212->call(q212,"_field_equals",args(new Part[]{p(get(q212.get("support"),s("attention_units"))),p(n("1"))})),q213->call(q213,"_integer_field_in_range",args(new Part[]{p(get(q213.get("support"),s("mentor_character_id"))),p(n("1")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1")))})),q214->call(q214,"_field_equals",args(new Part[]{p(get(q214.get("support"),s("budget_owner_character_id"))),p(attribute(q214.get("expected_query"),"owner_character_id"))})),q215->call(q215,"_field_equals",args(new Part[]{p(get(q215.get("support"),s("treasury_budget_allocated"))),p(n("25"))})),q216->call(q216,"_field_equals",args(new Part[]{p(get(q216.get("support"),s("treasury_budget_spent"))),p(n("25"))})),q217->call(q217,"_integer_field_in_range",args(new Part[]{p(get(q217.get("support"),s("owner_capacity_used"))),p(n("1")),p(n("2"))})),q218->or(q218,q219->call(q219,"_unavailable_for",args(new Part[]{p(get(q219.get("support"),s("released"))),p(s("variable_absent"))})),q220->call(q220,"_field_equals",args(new Part[]{p(get(q220.get("support"),s("released"))),p(FALSE)}))),q221->or(q221,q222->call(q222,"_unavailable_for",args(new Part[]{p(get(q222.get("support"),s("withheld"))),p(s("variable_absent"))})),q223->call(q223,"_field_equals",args(new Part[]{p(get(q223.get("support"),s("withheld"))),p(FALSE)}))),q224->or(q224,q225->call(q225,"_unavailable_for",args(new Part[]{p(get(q225.get("support"),s("atomic_shortfall"))),p(s("variable_absent"))})),q226->call(q226,"_field_equals",args(new Part[]{p(get(q226.get("support"),s("atomic_shortfall"))),p(FALSE)})))));
                    assign(e,new NameTarget("absent_package"),and(e,q227->compare(q227,get(get(q227.get("pip"),s("state")),s("value")),new Comparison(Cmp.EQ,q228->n("2"))),q229->compare(q229,q229.get("reserved"),new Comparison(Cmp.IS,q230->FALSE)),q231->compare(q231,q231.get("absent"),new Comparison(Cmp.IS,q232->TRUE)),q233->call(q233,"_field_equals",args(new Part[]{p(get(q233.get("support"),s("hours"))),p(n("0"))})),q234->call(q234,"_field_equals",args(new Part[]{p(get(q234.get("support"),s("attention_units"))),p(n("0"))})),q235->call(q235,"_field_equals",args(new Part[]{p(get(q235.get("support"),s("treasury_budget_allocated"))),p(n("0"))})),q236->call(q236,"_field_equals",args(new Part[]{p(get(q236.get("support"),s("treasury_budget_spent"))),p(n("0"))})),q237->or(q237,q238->call(q238,"_unavailable_for",args(new Part[]{p(get(q238.get("support"),s("released"))),p(s("variable_absent"))})),q239->call(q239,"_field_equals",args(new Part[]{p(get(q239.get("support"),s("released"))),p(FALSE)}))),q240->or(q240,q241->and(q241,q242->compare(q242,get(get(q242.get("pip"),s("policy_route")),s("value")),new Comparison(Cmp.EQ,q243->n("1"))),q244->or(q244,q245->call(q245,"_unavailable_for",args(new Part[]{p(get(q245.get("support"),s("withheld"))),p(s("variable_absent"))})),q246->call(q246,"_field_equals",args(new Part[]{p(get(q246.get("support"),s("withheld"))),p(FALSE)}))),q247->call(q247,"_field_equals",args(new Part[]{p(get(q247.get("support"),s("atomic_shortfall"))),p(TRUE)}))),q248->and(q248,q249->compare(q249,get(get(q249.get("pip"),s("policy_route")),s("value")),new Comparison(Cmp.EQ,q250->n("2"))),q251->call(q251,"_field_equals",args(new Part[]{p(get(q251.get("support"),s("withheld"))),p(TRUE)})),q252->or(q252,q253->call(q253,"_unavailable_for",args(new Part[]{p(get(q253.get("support"),s("atomic_shortfall"))),p(s("variable_absent"))})),q254->call(q254,"_field_equals",args(new Part[]{p(get(q254.get("support"),s("atomic_shortfall"))),p(FALSE)})))))));
                    assign(e,new NameTarget("support_ready"),and(e,q255->q255.get("core_support"),q256->or(q256,q257->q257.get("reserved_package"),q258->q258.get("absent_package"))));
                }
                if(truth(compare(e,get(e.get("readiness"),s("support_ready")),new Comparison(Cmp.IS_NOT,q259->q259.get("support_ready"))))) {
                    throw new Rejected(py(s("support readiness disagrees with package ledger")));
                }
                assign(e,new NameTarget("ledger"),get(e.get("groups"),s("budget_ledger")));
                assign(e,new NameTarget("budget_ledger_ready"),and(e,q260->q260.get("pip_ready"),q261->call(q261,"_field_equals",args(new Part[]{p(get(q261.get("ledger"),s("result_case_serial"))),p(get(get(q261.get("pip"),s("case_serial")),s("value")))})),q262->call(q262,"_integer_field_in_range",args(new Part[]{p(get(q262.get("ledger"),s("treasury_penalty_paid"))),p(n("0")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))})),q263->call(q263,"_integer_field_in_range",args(new Part[]{p(get(q263.get("ledger"),s("personal_gold_penalty_paid"))),p(n("0")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))})),q264->call(q264,"_integer_field_in_range",args(new Part[]{p(get(q264.get("ledger"),s("support_treasury_allocated"))),p(n("0")),p(n("25"))})),q265->call(q265,"_integer_field_in_range",args(new Part[]{p(get(q265.get("ledger"),s("support_treasury_spent"))),p(n("0")),p(n("25"))}))));
                if(truth(compare(e,get(e.get("readiness"),s("budget_ledger_ready")),new Comparison(Cmp.IS_NOT,q266->q266.get("budget_ledger_ready"))))) {
                    throw new Rejected(py(s("budget readiness disagrees with penalty ledger")));
                }
                for(V q267:iter(seq(true,p(s("d180_ticket")),p(s("d365_ticket"))))) {
                    assign(e,new NameTarget("ticket_name"),q267);
                    assign(e,new NameTarget("ticket"),get(e.get("groups"),e.get("ticket_name")));
                    for(V q268:iter(method(e.get("ticket"),"items",args(new Part[]{})))) {
                        assign(e,new TupleTarget(List.of(new NameTarget("key"),new NameTarget("field"))),q268);
                        assign(e,new NameTarget("expected_reason"),(truth(compare(e,e.get("key"),new Comparison(Cmp.EQ,q269->s("due_date_raw"))))?s("product_not_persisted"):s("native_observation_unavailable")));
                        if(truth(or(e,q270->compare(q270,get(q270.get("field"),s("status")),new Comparison(Cmp.NE,q271->s("unavailable"))),q272->compare(q272,get(q272.get("field"),s("unavailable_reason")),new Comparison(Cmp.NE,q273->q273.get("expected_reason")))))) {
                            throw new Rejected(py(joined(s(py(e.get("ticket_name"))),s("."),s(py(e.get("key"))),s(" must remain typed unavailable"))));
                        }
                    }
                }
                if(truth(or(e,q274->get(q274.get("readiness"),s("d180_ticket_observation_ready")),q275->get(q275.get("readiness"),s("d365_ticket_observation_ready")),q276->get(q276.get("readiness"),s("modifier_observation_ready")),q277->compare(q277,get(q277.get("modifier"),s("status")),new Comparison(Cmp.NE,q278->s("unavailable"))),q279->compare(q279,get(q279.get("modifier"),s("unavailable_reason")),new Comparison(Cmp.NE,q280->s("native_observation_unavailable")))))) {
                    throw new Rejected(py(s("unimplemented ticket/modifier observation was fabricated")));
                }
                assign(e,new NameTarget("midpoint"),get(e.get("groups"),s("midpoint")));
                assign(e,new NameTarget("midpoint_ready"),and(e,q281->q281.get("pip_ready"),q282->call(q282,"_field_equals",args(new Part[]{p(get(q282.get("midpoint"),s("receipt_serial"))),p(get(get(q282.get("pip"),s("case_serial")),s("value")))})),q283->call(q283,"_available",args(new Part[]{p(get(q283.get("midpoint"),s("resource_delivery_valid")))})),q284->call(q284,"_field_equals",args(new Part[]{p(get(q284.get("midpoint"),s("progress_status"))),p(n("0"))})),q285->call(q285,"_field_equals",args(new Part[]{p(get(q285.get("midpoint"),s("progress_red_code"))),p(n("1"))})),q286->call(q286,"_field_equals",args(new Part[]{p(get(q286.get("midpoint"),s("state"))),p(n("2"))}))));
                if(truth(compare(e,get(e.get("readiness"),s("midpoint_ready")),new Comparison(Cmp.IS_NOT,q287->q287.get("midpoint_ready"))))) {
                    throw new Rejected(py(s("midpoint readiness disagrees with receipt")));
                }
                assign(e,new NameTarget("outcome"),get(e.get("groups"),s("outcome")));
                assign(e,new NameTarget("outcome_ready"),FALSE);
                if(truth(and(e,q288->q288.get("pip_ready"),q289->compare(q289,get(get(q289.get("pip"),s("state")),s("value")),new Comparison(Cmp.IN,q290->seq(true,p(n("3")),p(n("4")))))))) {
                    assign(e,new NameTarget("pip_case"),get(get(e.get("pip"),s("case_serial")),s("value")));
                    assign(e,new NameTarget("graduated"),and(e,q291->compare(q291,get(get(q291.get("pip"),s("state")),s("value")),new Comparison(Cmp.EQ,q292->n("3"))),q293->call(q293,"_field_equals",args(new Part[]{p(get(q293.get("outcome"),s("code"))),p(n("1"))})),q294->call(q294,"_field_equals",args(new Part[]{p(get(q294.get("outcome"),s("graduation_receipt_serial"))),p(q294.get("pip_case"))})),q295->or(q295,q296->call(q296,"_field_equals",args(new Part[]{p(get(q296.get("outcome"),s("failure_receipt_serial"))),p(n("0"))})),q297->call(q297,"_unavailable_for",args(new Part[]{p(get(q297.get("outcome"),s("failure_receipt_serial"))),p(s("variable_absent"))})))));
                    assign(e,new NameTarget("failed"),and(e,q298->compare(q298,get(get(q298.get("pip"),s("state")),s("value")),new Comparison(Cmp.EQ,q299->n("4"))),q300->call(q300,"_field_equals",args(new Part[]{p(get(q300.get("outcome"),s("code"))),p(n("2"))})),q301->call(q301,"_field_equals",args(new Part[]{p(get(q301.get("outcome"),s("failure_receipt_serial"))),p(q301.get("pip_case"))})),q302->or(q302,q303->call(q303,"_field_equals",args(new Part[]{p(get(q303.get("outcome"),s("graduation_receipt_serial"))),p(n("0"))})),q304->call(q304,"_unavailable_for",args(new Part[]{p(get(q304.get("outcome"),s("graduation_receipt_serial"))),p(s("variable_absent"))})))));
                    assign(e,new NameTarget("outcome_ready"),and(e,q305->call(q305,"_field_equals",args(new Part[]{p(get(q305.get("outcome"),s("settlement_receipt_serial"))),p(q305.get("pip_case"))})),q306->call(q306,"_integer_field_in_range",args(new Part[]{p(get(q306.get("outcome"),s("result_cycle_serial"))),p(n("1")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))})),q307->call(q307,"_integer_field_in_range",args(new Part[]{p(get(q307.get("outcome"),s("result_case_serial"))),p(n("1")),p(n("999999"))})),q308->call(q308,"_integer_field_in_range",args(new Part[]{p(get(q308.get("outcome"),s("result_grade"))),p(n("1")),p(n("3"))})),q309->call(q309,"_field_equals",args(new Part[]{p(get(q309.get("outcome"),s("stability_days_observed"))),p(n("365"))})),q310->call(q310,"_field_equals",args(new Part[]{p(get(q310.get("outcome"),s("independent_review_status"))),p(n("0"))})),q311->call(q311,"_field_equals",args(new Part[]{p(get(q311.get("outcome"),s("independent_review_red_code"))),p(n("2"))})),q312->or(q312,q313->q313.get("graduated"),q314->q314.get("failed"))));
                }
                if(truth(compare(e,get(e.get("readiness"),s("outcome_ready")),new Comparison(Cmp.IS_NOT,q315->q315.get("outcome_ready"))))) {
                    throw new Rejected(py(s("outcome readiness disagrees with settlement")));
                }
                assign(e,new NameTarget("evidence"),get(e.get("groups"),s("next_cycle_evidence")));
                assign(e,new NameTarget("next_cycle_evidence_ready"),FALSE);
                if(truth(and(e,q316->q316.get("pip_ready"),q317->call(q317,"_integer_field_in_range",args(new Part[]{p(get(q317.get("evidence"),s("status"))),p(n("1")),p(n("2"))}))))) {
                    assign(e,new NameTarget("pip_cycle"),get(get(e.get("pip"),s("cycle_serial")),s("value")));
                    assign(e,new NameTarget("pip_case"),get(get(e.get("pip"),s("case_serial")),s("value")));
                    assign(e,new NameTarget("base"),and(e,q318->call(q318,"_field_equals",args(new Part[]{p(get(q318.get("evidence"),s("owner_character_id"))),p(attribute(q318.get("expected_query"),"owner_character_id"))})),q319->call(q319,"_field_equals",args(new Part[]{p(get(q319.get("evidence"),s("subject_character_id"))),p(q319.get("player"))})),q320->call(q320,"_field_equals",args(new Part[]{p(get(q320.get("evidence"),s("source_cycle_serial"))),p(q320.get("pip_cycle"))})),q321->call(q321,"_field_equals",args(new Part[]{p(get(q321.get("evidence"),s("source_case_serial"))),p(q321.get("pip_case"))})),q322->call(q322,"_field_equals",args(new Part[]{p(get(q322.get("evidence"),s("due_cycle_serial"))),p(binary(Op.ADD,q322.get("pip_cycle"),n("1")))})),q323->compare(q323,get(get(q323.get("evidence"),s("delta")),s("value")),new Comparison(Cmp.IN,q324->seq(true,p(n("10")),p(negate(n("10"))),p(negate(n("15")))))),q325->call(q325,"_available",args(new Part[]{p(get(q325.get("evidence"),s("delta")))}))));
                    assign(e,new NameTarget("pending_evidence"),and(e,q326->compare(q326,get(get(q326.get("evidence"),s("status")),s("value")),new Comparison(Cmp.EQ,q327->n("1"))),q328->call(q328,"_unavailable_for",args(new Part[]{p(get(q328.get("evidence"),s("consumed_cycle_serial"))),p(s("variable_absent"))})),q329->call(q329,"_unavailable_for",args(new Part[]{p(get(q329.get("evidence"),s("consumed_case_serial"))),p(s("variable_absent"))}))));
                    assign(e,new NameTarget("consumed_evidence"),and(e,q330->compare(q330,get(get(q330.get("evidence"),s("status")),s("value")),new Comparison(Cmp.EQ,q331->n("2"))),q332->call(q332,"_integer_field_in_range",args(new Part[]{p(get(q332.get("evidence"),s("consumed_cycle_serial"))),p(get(get(q332.get("evidence"),s("due_cycle_serial")),s("value"))),p(binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))})),q333->call(q333,"_field_equals",args(new Part[]{p(get(q333.get("evidence"),s("consumed_case_serial"))),p(q333.get("pip_case"))}))));
                    assign(e,new NameTarget("next_cycle_evidence_ready"),and(e,q334->q334.get("base"),q335->or(q335,q336->q336.get("pending_evidence"),q337->q337.get("consumed_evidence"))));
                }
                if(truth(compare(e,get(e.get("readiness"),s("next_cycle_evidence_ready")),new Comparison(Cmp.IS_NOT,q338->q338.get("next_cycle_evidence_ready"))))) {
                    throw new Rejected(py(s("next-cycle evidence readiness disagrees with receipt")));
                }
            } else {
                throw new Rejected(py(s("status must be available or unavailable")));
            }
        }
        return dict(new Expansion(e.get("frame")),new Expansion(e.get("groups")),new Item(s("pip_modifier_present"),e.get("modifier")),new Item(s("readiness"),e.get("readiness")),new Item(s("provenance"),call(e,"dict",args(new Part[]{p(e.get("provenance"))}))));
    }
    // Original zhongguo_b2_pip_snapshot_contract.py:284..287
    private static V fvalidate_b2_pip_request_nonce_v1(E e){
        if(truth(or(e,q339->b(!truth(call(q339,"isinstance",args(new Part[]{p(q339.get("value")),p(q339.get("str"))})))),q340->compare(q340,method(q340.get("_NONCE_RE"),"fullmatch",args(new Part[]{p(q340.get("value"))})),new Comparison(Cmp.IS,q341->NONE))))) {
            throw new Rejected(py(s("request_nonce must be 1-64 ASCII token characters")));
        }
        return e.get("value");
    }
}
