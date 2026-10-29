package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_ai_owned_case_snapshot_contract.py; original SHA-256 58eb3a6341d43c5b3932f786fa16c58e5d9b92227f846057070cdb69ff0efc75. No Python runtime. */
final class CasesAIOWNEDOriginalNormalizer {
    private CasesAIOWNEDOriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesAIOWNEDOriginalNormalizer::dispatch);
        e.put("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CASE_KIND",s("zhongguo.b1.performance"));
        e.put("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION",s("1.19.0.6"));
        e.put("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256",s("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"));
        e.put("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BACKEND_ID",s("ck3-1.19.0.6-native-zhongguo-ai-owned-case-snapshot-v1"));
        e.put("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID",s("xar-autoplayer-zhongguo-ai-owned-case-snapshot-v1"));
        e.put("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_ALLOWLIST_ID",s("zg361-b1-ai-owned-case-v1"));
        e.put("ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1",s("authorized_ai_background"));
        e.put("_NONCE_RE",regex(text(s("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\\Z"))));
        e.put("_STABLE_KEY_RE",regex(text(s("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\\Z"))));
        e.put("_TYPED_FIELD_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_ELIGIBILITY_KEYS",set(p(s("owner_character_id")),p(s("owner_alive")),p(s("owner_is_ai")),p(s("primary_title_id")),p(s("primary_title_tier_raw")),p(s("primary_title_tier_key")),p(s("government_key")),p(s("subject_immediate_liege_character_id")),p(s("subject_is_direct_subject")),p(s("authorized"))));
        e.put("_CASE_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("active")),p(s("revision")),p(s("timeline_serial")),p(s("feedback_revision"))));
        e.put("_STAGE_KEYS",set(p(s("state")),p(s("key")),p(s("active"))));
        e.put("_ROUTE_KEYS",set(p(s("kind")),p(s("visible_event_allowed")),p(s("owner_is_ai")),p(s("manager_eligible")),p(s("direct_subject_eligible"))));
        e.put("_POLICY_KEYS",set(p(s("policy_id")),p(s("choice"))));
        e.put("_OPERATION_KEYS",set(p(s("operation_id")),p(s("operation_key")),p(s("hook")),p(s("pre_state")),p(s("post_state"))));
        e.put("_RECEIPT_KEYS",set(p(s("status")),p(s("key")),p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("choice"))));
        e.put("_READINESS_KEYS",set(p(s("owner_eligibility_ready")),p(s("case_identity_ready")),p(s("stage_ready")),p(s("route_ready")),p(s("receipt_ready")),p(s("same_frame_ready")),p(s("ready"))));
        e.put("_FIELD_UNAVAILABLE_REASONS",set(p(s("case_unavailable")),p(s("variable_absent")),p(s("value_type_mismatch")),p(s("value_out_of_range")),p(s("stage_inconsistent")),p(s("no_operation_recorded")),p(s("unknown_allowlisted_operation")),p(s("receipt_not_recorded")),p(s("receipt_inconsistent")),p(s("not_applicable"))));
        e.put("_TOP_LEVEL_UNAVAILABLE_REASONS",set(p(s("unsupported_build")),p(s("requires_application_main")),p(s("requires_paused")),p(s("map_not_ready")),p(s("owner_is_played_character")),p(s("owner_eligibility_unavailable")),p(s("owner_not_alive")),p(s("owner_not_ai")),p(s("owner_not_celestial")),p(s("owner_not_landed_duke_plus")),p(s("subject_not_direct_subject")),p(s("case_not_found")),p(s("owner_filter_mismatch")),p(s("variable_identifier_unavailable")),p(s("variable_context_unavailable")),p(s("state_changed")),p(s("internal_error")),p(s("subject_not_found"))));
        e.put("_PROVENANCE_VALUES",dict(new Item(s("game_version"),e.get("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION")),new Item(s("executable_sha256"),e.get("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256")),new Item(s("backend_id"),e.get("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BACKEND_ID")),new Item(s("consumer_id"),e.get("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID")),new Item(s("allowlist_id"),e.get("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_ALLOWLIST_ID")),new Item(s("variable_context_for_scope_rva"),s("0x3329A40")),new Item(s("character_storage_slot_rva"),s("0x570C130")),new Item(s("primary_title_rva"),s("0x25F3350")),new Item(s("immediate_liege_rva"),s("0x2613480")),new Item(s("government_rva"),s("0x26165B0")),new Item(s("is_human_player_rva"),s("0x28BCEB0"))));
        e.put("_FRAME_KEYS",set(p(s("schema_version")),p(s("status")),p(s("case_kind")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("requested_owner_character_id")),p(s("subject_character_id")),p(s("owner_eligibility")),p(s("case")),p(s("stage")),p(s("route")),p(s("policy")),p(s("operation")),p(s("receipt")),p(s("readiness")),p(s("unavailable_reason")),p(s("provenance"))));
        e.put("_TITLE_TIER_KEYS",dict(new Item(n("3"),s("duchy")),new Item(n("4"),s("kingdom")),new Item(n("5"),s("empire")),new Item(n("6"),s("hegemony"))));
        e.put("_STAGE_KEYS_BY_STATE",dict(new Item(n("1"),s("targets_open")),new Item(n("2"),s("midcycle_open")),new Item(n("3"),s("evidence_open")),new Item(n("4"),s("facts_frozen")),new Item(n("5"),s("shadow_open")),new Item(n("6"),s("quota_ready")),new Item(n("7"),s("calibration_open")),new Item(n("8"),s("published"))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_ai_owned_case_snapshot_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_all_available" -> f_all_available(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED),new Param("fields",REQUIRED)),List.of(),null),args));
            case "_all_unavailable_with_reason" -> f_all_unavailable_with_reason(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED),new Param("fields",REQUIRED),new Param("reason",REQUIRED)),List.of(),null),args));
            case "_available" -> f_available(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED)),List.of(),null),args));
            case "_exact_object" -> f_exact_object(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("fields",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_integer" -> f_integer(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("minimum",REQUIRED),new Param("maximum",REQUIRED)),null),args));
            case "_positive_int32" -> f_positive_int32(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed_field" -> f_typed_field(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("value_kind",REQUIRED)),null),args));
            case "_typed_group" -> f_typed_group(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("fields",REQUIRED),new Param("kinds",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_validated_query" -> f_validated_query(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(),null),args));
            case "_value" -> f_value(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_ai_owned_case_snapshot_v1" -> fnormalize_native_zhongguo_ai_owned_case_snapshot_v1(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            case "validate_ai_owned_case_request_nonce_v1" -> fvalidate_ai_owned_case_request_nonce_v1(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(),null),args));
            case "ZhongguoAiOwnedCaseQueryV1" -> new D(new LinkedHashMap<>(bind(GLOBALS,CasesAIOWNEDOriginalNormalizer::dispatch,new Sig(List.of(new Param("owner_character_id",REQUIRED),new Param("subject_character_id",REQUIRED),new Param("request_nonce",REQUIRED)),List.of(),null),args).locals));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:402..405
    private static V f_all_available(E e){
        return call(e,"all",args(new Part[]{p(generator(e,q1->call(q1,"_available",args(new Part[]{p(get(q1.get("group"),q1.get("key")))})),new Clause(new NameTarget("key"),q2->q2.get("fields"),List.of())))}));
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:408..415
    private static V f_all_unavailable_with_reason(E e){
        return call(e,"all",args(new Part[]{p(generator(e,q3->and(q3,q5->b(!truth(call(q5,"_available",args(new Part[]{p(get(q5.get("group"),q5.get("key")))})))),q6->compare(q6,get(get(q6.get("group"),q6.get("key")),s("unavailable_reason")),new Comparison(Cmp.EQ,q7->q7.get("reason")))),new Clause(new NameTarget("key"),q4->q4.get("fields"),List.of())))}));
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:392..393
    private static V f_available(E e){
        return compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q8->s("available")));
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:340..345
    private static V f_exact_object(E e){
        if(truth(or(e,q9->b(!truth(call(q9,"isinstance",args(new Part[]{p(q9.get("value")),p(q9.get("dict"))})))),q10->compare(q10,call(q10,"set",args(new Part[]{p(q10.get("value"))})),new Comparison(Cmp.NE,q11->q11.get("fields")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:251..260
    private static V f_integer(E e){
        if(truth(or(e,q12->call(q12,"isinstance",args(new Part[]{p(q12.get("value")),p(q12.get("bool"))})),q13->b(!truth(call(q13,"isinstance",args(new Part[]{p(q13.get("value")),p(q13.get("int"))})))),q14->b(!truth(compare(q14,q14.get("minimum"),new Comparison(Cmp.LE,q15->q15.get("value")),new Comparison(Cmp.LE,q16->q16.get("maximum")))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be an integer in range"))));
        }
        return e.get("value");
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:241..248
    private static V f_positive_int32(E e){
        if(truth(or(e,q17->call(q17,"isinstance",args(new Part[]{p(q17.get("value")),p(q17.get("bool"))})),q18->b(!truth(call(q18,"isinstance",args(new Part[]{p(q18.get("value")),p(q18.get("int"))})))),q19->b(!truth(compare(q19,n("1"),new Comparison(Cmp.LE,q20->q20.get("value")),new Comparison(Cmp.LE,q21->binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be a positive signed int32"))));
        }
        return e.get("value");
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:348..376
    private static V f_typed_field(E e){
        assign(e,new NameTarget("field"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_FIELD_KEYS")),p(e.get("name"))})));
        assign(e,new NameTarget("status"),get(e.get("field"),s("status")));
        assign(e,new NameTarget("raw"),get(e.get("field"),s("value")));
        assign(e,new NameTarget("reason"),get(e.get("field"),s("unavailable_reason")));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q22->s("available"))))) {
            if(truth(compare(e,e.get("reason"),new Comparison(Cmp.IS_NOT,q23->NONE)))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" available field has a reason"))));
            }
            if(truth(compare(e,e.get("value_kind"),new Comparison(Cmp.IS,q24->q24.get("int"))))) {
                call(e,"_integer",args(new Part[]{p(e.get("raw")),p(e.get("name"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
            } else {
                if(truth(compare(e,e.get("value_kind"),new Comparison(Cmp.IS,q25->q25.get("bool"))))) {
                    if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(e.get("raw")),p(e.get("bool"))})))))) {
                        throw new Rejected(py(joined(s(py(e.get("name"))),s(".value must be boolean"))));
                    }
                } else {
                    if(truth(compare(e,e.get("value_kind"),new Comparison(Cmp.IS,q26->q26.get("str"))))) {
                        if(truth(or(e,q27->b(!truth(call(q27,"isinstance",args(new Part[]{p(q27.get("raw")),p(q27.get("str"))})))),q28->compare(q28,method(q28.get("_STABLE_KEY_RE"),"fullmatch",args(new Part[]{p(q28.get("raw"))})),new Comparison(Cmp.IS,q29->NONE))))) {
                            throw new Rejected(py(joined(s(py(e.get("name"))),s(".value must be a bounded stable key"))));
                        }
                    } else {
                        throw new AssertionError(py(e.get("value_kind")));
                    }
                }
            }
        } else {
            if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q30->s("unavailable"))))) {
                if(truth(or(e,q31->compare(q31,q31.get("raw"),new Comparison(Cmp.IS_NOT,q32->NONE)),q33->compare(q33,q33.get("reason"),new Comparison(Cmp.NOT_IN,q34->q34.get("_FIELD_UNAVAILABLE_REASONS")))))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(" has a malformed unavailable field"))));
                }
            } else {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an unknown typed status"))));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:379..389
    private static V f_typed_group(E e){
        assign(e,new NameTarget("group"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("fields")),p(e.get("name"))})));
        return dictFrom(iter(generator(e,q35->seq(true,p(q35.get("key")),p(call(q35,"_typed_field",args(new Part[]{p(get(q35.get("group"),q35.get("key"))),p(joined(s(py(q35.get("name"))),s("."),s(py(q35.get("key")))))},new Kw("value_kind",q35.get("kind")))))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("kind"))),q36->method(q36.get("kinds"),"items",args(new Part[]{})),List.of()))));
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:271..288
    private static V f_validated_query(E e){
        assign(e,new NameTarget("owner"),call(e,"_positive_int32",args(new Part[]{p(attribute(e.get("value"),"owner_character_id")),p(s("owner_character_id"))})));
        assign(e,new NameTarget("subject"),call(e,"_positive_int32",args(new Part[]{p(attribute(e.get("value"),"subject_character_id")),p(s("subject_character_id"))})));
        if(truth(compare(e,e.get("owner"),new Comparison(Cmp.EQ,q37->q37.get("subject"))))) {
            throw new Rejected(py(s("owner_character_id and subject_character_id differ")));
        }
        return call(e,"ZhongguoAiOwnedCaseQueryV1",args(new Part[]{},new Kw("owner_character_id",e.get("owner")),new Kw("subject_character_id",e.get("subject")),new Kw("request_nonce",call(e,"validate_ai_owned_case_request_nonce_v1",args(new Part[]{p(attribute(e.get("value"),"request_nonce"))})))));
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:396..399
    private static V f_value(E e){
        if(truth(b(!truth(call(e,"_available",args(new Part[]{p(e.get("field"))})))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be available"))));
        }
        return get(e.get("field"),s("value"));
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:432..865
    private static V fnormalize_native_zhongguo_ai_owned_case_snapshot_v1(E e){
        assign(e,new NameTarget("expected_query"),call(e,"_validated_query",args(new Part[]{p(e.get("expected_query"))})));
        assign(e,new NameTarget("expected_snapshot_revision"),call(e,"_integer",args(new Part[]{p(e.get("expected_snapshot_revision")),p(s("expected_snapshot_revision"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1"))))));
        assign(e,new NameTarget("expected_date_raw"),call(e,"_integer",args(new Part[]{p(e.get("expected_date_raw")),p(s("expected_date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))));
        assign(e,new NameTarget("expected_player_character_id"),call(e,"_positive_int32",args(new Part[]{p(e.get("expected_player_character_id")),p(s("expected_player_character_id"))})));
        assign(e,new NameTarget("frame"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("_FRAME_KEYS")),p(s("zhongguo_ai_owned_case_snapshot"))})));
        if(truth(compare(e,get(e.get("frame"),s("schema_version")),new Comparison(Cmp.NE,q38->n("1"))))) {
            throw new Rejected(py(s("schema_version must be 1")));
        }
        if(truth(compare(e,get(e.get("frame"),s("case_kind")),new Comparison(Cmp.NE,q39->q39.get("ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CASE_KIND"))))) {
            throw new Rejected(py(s("case_kind is outside the fixed B1 product")));
        }
        if(truth(compare(e,get(e.get("frame"),s("request_nonce")),new Comparison(Cmp.NE,q40->attribute(q40.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("request nonce binding changed")));
        }
        assign(e,new NameTarget("revision"),call(e,"_integer",args(new Part[]{p(get(e.get("frame"),s("snapshot_revision"))),p(s("snapshot_revision"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1"))))));
        if(truth(compare(e,e.get("revision"),new Comparison(Cmp.NE,q41->q41.get("expected_snapshot_revision"))))) {
            throw new Rejected(py(s("snapshot revision binding changed")));
        }
        assign(e,new NameTarget("date_raw"),call(e,"_integer",args(new Part[]{p(get(e.get("frame"),s("date_raw"))),p(s("date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))));
        if(truth(or(e,q42->compare(q42,q42.get("date_raw"),new Comparison(Cmp.NE,q43->q43.get("expected_date_raw"))),q44->compare(q44,get(q44.get("frame"),s("paused")),new Comparison(Cmp.IS_NOT,q45->TRUE))))) {
            throw new Rejected(py(s("snapshot is not the expected paused frame")));
        }
        assign(e,new NameTarget("player"),call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("player_character_id"))),p(s("player_character_id"))})));
        if(truth(compare(e,e.get("player"),new Comparison(Cmp.NE,q46->q46.get("expected_player_character_id"))))) {
            throw new Rejected(py(s("played character binding changed")));
        }
        assign(e,new NameTarget("owner"),call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("requested_owner_character_id"))),p(s("requested_owner_character_id"))})));
        assign(e,new NameTarget("subject"),call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("subject_character_id"))),p(s("subject_character_id"))})));
        if(truth(compare(e,e.get("owner"),new Comparison(Cmp.NE,q47->attribute(q47.get("expected_query"),"owner_character_id"))))) {
            throw new Rejected(py(s("owner request binding changed")));
        }
        if(truth(compare(e,e.get("subject"),new Comparison(Cmp.NE,q48->attribute(q48.get("expected_query"),"subject_character_id"))))) {
            throw new Rejected(py(s("subject request binding changed")));
        }
        assign(e,new NameTarget("eligibility"),call(e,"_typed_group",args(new Part[]{p(get(e.get("frame"),s("owner_eligibility"))),p(e.get("_ELIGIBILITY_KEYS")),p(dict(new Item(s("owner_character_id"),e.get("int")),new Item(s("owner_alive"),e.get("bool")),new Item(s("owner_is_ai"),e.get("bool")),new Item(s("primary_title_id"),e.get("int")),new Item(s("primary_title_tier_raw"),e.get("int")),new Item(s("primary_title_tier_key"),e.get("str")),new Item(s("government_key"),e.get("str")),new Item(s("subject_immediate_liege_character_id"),e.get("int")),new Item(s("subject_is_direct_subject"),e.get("bool")),new Item(s("authorized"),e.get("bool")))),p(s("owner_eligibility"))})));
        assign(e,new NameTarget("case"),call(e,"_typed_group",args(new Part[]{p(get(e.get("frame"),s("case"))),p(e.get("_CASE_KEYS")),p(dict(new Item(s("owner_character_id"),e.get("int")),new Item(s("subject_character_id"),e.get("int")),new Item(s("cycle_serial"),e.get("int")),new Item(s("case_serial"),e.get("int")),new Item(s("state"),e.get("int")),new Item(s("active"),e.get("bool")),new Item(s("revision"),e.get("int")),new Item(s("timeline_serial"),e.get("int")),new Item(s("feedback_revision"),e.get("int")))),p(s("case"))})));
        assign(e,new NameTarget("stage"),call(e,"_typed_group",args(new Part[]{p(get(e.get("frame"),s("stage"))),p(e.get("_STAGE_KEYS")),p(dict(new Item(s("state"),e.get("int")),new Item(s("key"),e.get("str")),new Item(s("active"),e.get("bool")))),p(s("stage"))})));
        assign(e,new NameTarget("route"),call(e,"_typed_group",args(new Part[]{p(get(e.get("frame"),s("route"))),p(e.get("_ROUTE_KEYS")),p(dict(new Item(s("kind"),e.get("str")),new Item(s("visible_event_allowed"),e.get("bool")),new Item(s("owner_is_ai"),e.get("bool")),new Item(s("manager_eligible"),e.get("bool")),new Item(s("direct_subject_eligible"),e.get("bool")))),p(s("route"))})));
        assign(e,new NameTarget("policy"),call(e,"_typed_group",args(new Part[]{p(get(e.get("frame"),s("policy"))),p(e.get("_POLICY_KEYS")),p(dict(new Item(s("policy_id"),e.get("str")),new Item(s("choice"),e.get("int")))),p(s("policy"))})));
        assign(e,new NameTarget("operation"),call(e,"_typed_group",args(new Part[]{p(get(e.get("frame"),s("operation"))),p(e.get("_OPERATION_KEYS")),p(dict(new Item(s("operation_id"),e.get("int")),new Item(s("operation_key"),e.get("str")),new Item(s("hook"),e.get("str")),new Item(s("pre_state"),e.get("int")),new Item(s("post_state"),e.get("int")))),p(s("operation"))})));
        assign(e,new NameTarget("receipt_raw"),call(e,"_exact_object",args(new Part[]{p(get(e.get("frame"),s("receipt"))),p(e.get("_RECEIPT_KEYS")),p(s("receipt"))})));
        assign(e,new NameTarget("receipt_status"),get(e.get("receipt_raw"),s("status")));
        if(truth(compare(e,e.get("receipt_status"),new Comparison(Cmp.NOT_IN,q49->set(p(s("recorded")),p(s("not_recorded")),p(s("unavailable"))))))) {
            throw new Rejected(py(s("receipt.status is invalid")));
        }
        assign(e,new NameTarget("receipt"),dict(new Item(s("status"),e.get("receipt_status")),new Expansion(dictFrom(iter(generator(e,q50->seq(true,p(q50.get("key")),p(call(q50,"_typed_field",args(new Part[]{p(get(q50.get("receipt_raw"),q50.get("key"))),p(joined(s("receipt."),s(py(q50.get("key")))))},new Kw("value_kind",q50.get("kind")))))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("kind"))),q51->method(dict(new Item(s("key"),q51.get("str")),new Item(s("owner_character_id"),q51.get("int")),new Item(s("subject_character_id"),q51.get("int")),new Item(s("cycle_serial"),q51.get("int")),new Item(s("case_serial"),q51.get("int")),new Item(s("state"),q51.get("int")),new Item(s("choice"),q51.get("int"))),"items",args(new Part[]{})),List.of())))))));
        assign(e,new NameTarget("readiness_raw"),call(e,"_exact_object",args(new Part[]{p(get(e.get("frame"),s("readiness"))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        if(truth(call(e,"any",args(new Part[]{p(generator(e,q52->b(!truth(call(q52,"isinstance",args(new Part[]{p(get(q52.get("readiness_raw"),q52.get("key"))),p(q52.get("bool"))})))),new Clause(new NameTarget("key"),q53->q53.get("_READINESS_KEYS"),List.of())))})))) {
            throw new Rejected(py(s("readiness must contain booleans")));
        }
        assign(e,new NameTarget("readiness"),dictFrom(iter(generator(e,q54->seq(true,p(q54.get("key")),p(call(q54,"bool",args(new Part[]{p(get(q54.get("readiness_raw"),q54.get("key")))})))),new Clause(new NameTarget("key"),q55->q55.get("_READINESS_KEYS"),List.of())))));
        assign(e,new NameTarget("component_ready"),call(e,"all",args(new Part[]{p(generator(e,q56->get(q56.get("readiness"),q56.get("key")),new Clause(new NameTarget("key"),q57->q57.get("_READINESS_KEYS"),List.of(q57->compare(q57,q57.get("key"),new Comparison(Cmp.NE,q58->s("ready")))))))})));
        if(truth(compare(e,get(e.get("readiness"),s("ready")),new Comparison(Cmp.IS_NOT,q59->q59.get("component_ready"))))) {
            throw new Rejected(py(s("readiness.ready disagrees with its component gate")));
        }
        assign(e,new NameTarget("provenance"),call(e,"_exact_object",args(new Part[]{p(get(e.get("frame"),s("provenance"))),p(call(e,"set",args(new Part[]{p(e.get("_PROVENANCE_VALUES"))}))),p(s("provenance"))})));
        if(truth(compare(e,e.get("provenance"),new Comparison(Cmp.NE,q60->q60.get("_PROVENANCE_VALUES"))))) {
            throw new Rejected(py(s("provenance does not match the frozen exact ABI")));
        }
        assign(e,new NameTarget("status"),get(e.get("frame"),s("status")));
        assign(e,new NameTarget("unavailable_reason"),get(e.get("frame"),s("unavailable_reason")));
        assign(e,new NameTarget("semantic_groups"),seq(true,p(seq(true,p(e.get("eligibility")),p(e.get("_ELIGIBILITY_KEYS")))),p(seq(true,p(e.get("case")),p(e.get("_CASE_KEYS")))),p(seq(true,p(e.get("stage")),p(e.get("_STAGE_KEYS")))),p(seq(true,p(e.get("route")),p(e.get("_ROUTE_KEYS")))),p(seq(true,p(e.get("policy")),p(e.get("_POLICY_KEYS")))),p(seq(true,p(e.get("operation")),p(e.get("_OPERATION_KEYS")))),p(seq(true,p(e.get("receipt")),p(binary(Op.SUB,e.get("_RECEIPT_KEYS"),set(p(s("status")))))))));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q61->s("unavailable"))))) {
            if(truth(compare(e,e.get("unavailable_reason"),new Comparison(Cmp.NOT_IN,q62->q62.get("_TOP_LEVEL_UNAVAILABLE_REASONS"))))) {
                throw new Rejected(py(s("unavailable frame has an unknown reason")));
            }
            if(truth(or(e,q63->compare(q63,q63.get("receipt_status"),new Comparison(Cmp.NE,q64->s("unavailable"))),q65->call(q65,"any",args(new Part[]{p(generator(q65,q66->b(!truth(call(q66,"_all_unavailable_with_reason",args(new Part[]{p(q66.get("group")),p(q66.get("fields")),p(s("case_unavailable"))})))),new Clause(new TupleTarget(List.of(new NameTarget("group"),new NameTarget("fields"))),q67->q67.get("semantic_groups"),List.of())))}))))) {
                throw new Rejected(py(s("unavailable frame leaks case semantics")));
            }
            assign(e,new NameTarget("expected_same_frame"),compare(e,e.get("unavailable_reason"),new Comparison(Cmp.IN,q68->set(p(s("case_not_found")),p(s("owner_filter_mismatch"))))));
            assign(e,new NameTarget("expected_readiness"),dictFrom(iter(generator(e,q69->seq(true,p(q69.get("key")),p(FALSE)),new Clause(new NameTarget("key"),q70->q70.get("_READINESS_KEYS"),List.of())))));
            put(e.get("expected_readiness"),s("same_frame_ready"),e.get("expected_same_frame"));
            if(truth(compare(e,e.get("readiness"),new Comparison(Cmp.NE,q71->q71.get("expected_readiness"))))) {
                throw new Rejected(py(s("unavailable readiness disagrees with native flow")));
            }
            return dict(new Expansion(e.get("frame")),new Item(s("owner_eligibility"),e.get("eligibility")),new Item(s("case"),e.get("case")),new Item(s("stage"),e.get("stage")),new Item(s("route"),e.get("route")),new Item(s("policy"),e.get("policy")),new Item(s("operation"),e.get("operation")),new Item(s("receipt"),e.get("receipt")),new Item(s("readiness"),e.get("readiness")),new Item(s("provenance"),call(e,"dict",args(new Part[]{p(e.get("provenance"))}))));
        }
        if(truth(or(e,q72->compare(q72,q72.get("status"),new Comparison(Cmp.NE,q73->s("available"))),q74->compare(q74,q74.get("unavailable_reason"),new Comparison(Cmp.IS_NOT,q75->NONE))))) {
            throw new Rejected(py(s("available frame has a malformed status")));
        }
        if(truth(compare(e,e.get("owner"),new Comparison(Cmp.EQ,q76->q76.get("player"))))) {
            throw new Rejected(py(s("an available AI-owned case cannot be player-owned")));
        }
        assign(e,new NameTarget("eligibility_ready"),call(e,"_all_available",args(new Part[]{p(e.get("eligibility")),p(e.get("_ELIGIBILITY_KEYS"))})));
        if(truth(e.get("eligibility_ready"))) {
            assign(e,new NameTarget("eligibility_values"),dictFrom(iter(generator(e,q77->seq(true,p(q77.get("key")),p(call(q77,"_value",args(new Part[]{p(get(q77.get("eligibility"),q77.get("key"))),p(joined(s("owner_eligibility."),s(py(q77.get("key")))))})))),new Clause(new NameTarget("key"),q78->q78.get("_ELIGIBILITY_KEYS"),List.of())))));
            assign(e,new NameTarget("title_tier"),get(e.get("eligibility_values"),s("primary_title_tier_raw")));
            assign(e,new NameTarget("eligibility_ready"),and(e,q79->compare(q79,get(q79.get("eligibility_values"),s("owner_character_id")),new Comparison(Cmp.EQ,q80->q80.get("owner"))),q81->compare(q81,get(q81.get("eligibility_values"),s("owner_alive")),new Comparison(Cmp.IS,q82->TRUE)),q83->compare(q83,get(q83.get("eligibility_values"),s("owner_is_ai")),new Comparison(Cmp.IS,q84->TRUE)),q85->call(q85,"isinstance",args(new Part[]{p(get(q85.get("eligibility_values"),s("primary_title_id"))),p(q85.get("int"))})),q86->b(!truth(call(q86,"isinstance",args(new Part[]{p(get(q86.get("eligibility_values"),s("primary_title_id"))),p(q86.get("bool"))})))),q87->compare(q87,get(q87.get("eligibility_values"),s("primary_title_id")),new Comparison(Cmp.GT,q88->n("0"))),q89->compare(q89,q89.get("title_tier"),new Comparison(Cmp.IN,q90->q90.get("_TITLE_TIER_KEYS"))),q91->compare(q91,get(q91.get("eligibility_values"),s("primary_title_tier_key")),new Comparison(Cmp.EQ,q92->method(q92.get("_TITLE_TIER_KEYS"),"get",args(new Part[]{p(q92.get("title_tier"))})))),q93->compare(q93,get(q93.get("eligibility_values"),s("government_key")),new Comparison(Cmp.EQ,q94->s("celestial_government"))),q95->compare(q95,get(q95.get("eligibility_values"),s("subject_immediate_liege_character_id")),new Comparison(Cmp.EQ,q96->q96.get("owner"))),q97->compare(q97,get(q97.get("eligibility_values"),s("subject_is_direct_subject")),new Comparison(Cmp.IS,q98->TRUE)),q99->compare(q99,get(q99.get("eligibility_values"),s("authorized")),new Comparison(Cmp.IS,q100->TRUE))));
        }
        if(truth(b(!truth(e.get("eligibility_ready"))))) {
            throw new Rejected(py(s("available frame lacks authorized AI-owner evidence")));
        }
        assign(e,new NameTarget("case_ready"),call(e,"_all_available",args(new Part[]{p(e.get("case")),p(e.get("_CASE_KEYS"))})));
        if(truth(e.get("case_ready"))) {
            assign(e,new NameTarget("case_values"),dictFrom(iter(generator(e,q101->seq(true,p(q101.get("key")),p(call(q101,"_value",args(new Part[]{p(get(q101.get("case"),q101.get("key"))),p(joined(s("case."),s(py(q101.get("key")))))})))),new Clause(new NameTarget("key"),q102->q102.get("_CASE_KEYS"),List.of())))));
            assign(e,new NameTarget("case_ready"),and(e,q103->compare(q103,get(q103.get("case_values"),s("owner_character_id")),new Comparison(Cmp.EQ,q104->q104.get("owner"))),q105->compare(q105,get(q105.get("case_values"),s("subject_character_id")),new Comparison(Cmp.EQ,q106->q106.get("subject"))),q107->compare(q107,get(q107.get("case_values"),s("cycle_serial")),new Comparison(Cmp.GT,q108->n("0"))),q109->compare(q109,get(q109.get("case_values"),s("case_serial")),new Comparison(Cmp.GT,q110->n("0"))),q111->compare(q111,get(q111.get("case_values"),s("revision")),new Comparison(Cmp.GT,q112->n("0"))),q113->compare(q113,get(q113.get("case_values"),s("timeline_serial")),new Comparison(Cmp.GT,q114->n("0"))),q115->compare(q115,get(q115.get("case_values"),s("feedback_revision")),new Comparison(Cmp.GT,q116->n("0")))));
        }
        if(truth(b(!truth(e.get("case_ready"))))) {
            throw new Rejected(py(s("available frame lacks its exact case identity")));
        }
        assign(e,new NameTarget("stage_state"),call(e,"_value",args(new Part[]{p(get(e.get("stage"),s("state"))),p(s("stage.state"))})));
        assign(e,new NameTarget("stage_active"),call(e,"_value",args(new Part[]{p(get(e.get("stage"),s("active"))),p(s("stage.active"))})));
        if(truth(or(e,q117->compare(q117,q117.get("stage_state"),new Comparison(Cmp.NE,q118->get(q118.get("case_values"),s("state")))),q119->compare(q119,q119.get("stage_active"),new Comparison(Cmp.IS_NOT,q120->get(q120.get("case_values"),s("active"))))))) {
            throw new Rejected(py(s("stage projection does not match the case")));
        }
        assign(e,new NameTarget("expected_stage_key"),method(e.get("_STAGE_KEYS_BY_STATE"),"get",args(new Part[]{p(e.get("stage_state"))})));
        assign(e,new NameTarget("stage_consistent"),and(e,q121->compare(q121,q121.get("expected_stage_key"),new Comparison(Cmp.IS_NOT,q122->NONE)),q123->or(q123,q124->and(q124,q125->compare(q125,q125.get("stage_state"),new Comparison(Cmp.LT,q126->n("8"))),q127->compare(q127,q127.get("stage_active"),new Comparison(Cmp.IS,q128->TRUE))),q129->and(q129,q130->compare(q130,q130.get("stage_state"),new Comparison(Cmp.EQ,q131->n("8"))),q132->compare(q132,q132.get("stage_active"),new Comparison(Cmp.IS,q133->FALSE))))));
        if(truth(e.get("stage_consistent"))) {
            if(truth(or(e,q134->b(!truth(call(q134,"_available",args(new Part[]{p(get(q134.get("stage"),s("key")))})))),q135->compare(q135,call(q135,"_value",args(new Part[]{p(get(q135.get("stage"),s("key"))),p(s("stage.key"))})),new Comparison(Cmp.NE,q136->q136.get("expected_stage_key")))))) {
                throw new Rejected(py(s("stage key does not match the case state")));
            }
        } else {
            if(truth(or(e,q137->call(q137,"_available",args(new Part[]{p(get(q137.get("stage"),s("key")))})),q138->compare(q138,get(get(q138.get("stage"),s("key")),s("unavailable_reason")),new Comparison(Cmp.NE,q139->s("stage_inconsistent")))))) {
                throw new Rejected(py(s("inconsistent stage is not typed as unavailable")));
            }
        }
        assign(e,new NameTarget("expected_route"),dict(new Item(s("kind"),e.get("ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1")),new Item(s("visible_event_allowed"),FALSE),new Item(s("owner_is_ai"),TRUE),new Item(s("manager_eligible"),TRUE),new Item(s("direct_subject_eligible"),TRUE)));
        if(truth(or(e,q140->b(!truth(call(q140,"_all_available",args(new Part[]{p(q140.get("route")),p(q140.get("_ROUTE_KEYS"))})))),q141->call(q141,"any",args(new Part[]{p(generator(q141,q142->compare(q142,call(q142,"_value",args(new Part[]{p(get(q142.get("route"),q142.get("key"))),p(joined(s("route."),s(py(q142.get("key")))))})),new Comparison(Cmp.NE,q144->q144.get("expected"))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("expected"))),q143->method(q143.get("expected_route"),"items",args(new Part[]{})),List.of())))}))))) {
            throw new Rejected(py(s("route is not the authorized AI-background route")));
        }
        assign(e,new NameTarget("operation_id"),(truth(call(e,"_available",args(new Part[]{p(get(e.get("operation"),s("operation_id")))})))?call(e,"_value",args(new Part[]{p(get(e.get("operation"),s("operation_id"))),p(s("operation.operation_id"))})):NONE));
        assign(e,new NameTarget("policy_choice"),(truth(call(e,"_available",args(new Part[]{p(get(e.get("policy"),s("choice")))})))?call(e,"_value",args(new Part[]{p(get(e.get("policy"),s("choice"))),p(s("policy.choice"))})):NONE));
        assign(e,new NameTarget("semantic_operation"),and(e,q145->compare(q145,q145.get("operation_id"),new Comparison(Cmp.EQ,q146->n("39"))),q147->compare(q147,q147.get("policy_choice"),new Comparison(Cmp.EQ,q148->n("1")))));
        assign(e,new NameTarget("no_operation"),compare(e,e.get("operation_id"),new Comparison(Cmp.EQ,q149->n("0"))));
        if(truth(e.get("semantic_operation"))) {
            if(truth(or(e,q150->b(!truth(call(q150,"_available",args(new Part[]{p(get(q150.get("policy"),s("policy_id")))})))),q151->compare(q151,call(q151,"_value",args(new Part[]{p(get(q151.get("policy"),s("policy_id"))),p(s("policy.policy_id"))})),new Comparison(Cmp.NE,q152->s("mechanism_039"))),q153->b(!truth(call(q153,"_available",args(new Part[]{p(get(q153.get("operation"),s("operation_key")))})))),q154->compare(q154,call(q154,"_value",args(new Part[]{p(get(q154.get("operation"),s("operation_key"))),p(s("operation.operation_key"))})),new Comparison(Cmp.NE,q155->s("roster_lock"))),q156->b(!truth(call(q156,"_available",args(new Part[]{p(get(q156.get("operation"),s("hook")))})))),q157->compare(q157,call(q157,"_value",args(new Part[]{p(get(q157.get("operation"),s("hook"))),p(s("operation.hook"))})),new Comparison(Cmp.NE,q158->s("roster_lock")))))) {
                throw new Rejected(py(s("operation is outside the B1 semantic allowlist")));
            }
        } else {
            assign(e,new NameTarget("semantic_reason"),(truth(e.get("no_operation"))?s("no_operation_recorded"):s("unknown_allowlisted_operation")));
            for(V q159:iter(seq(true,p(seq(true,p(get(e.get("policy"),s("policy_id"))),p(s("policy.policy_id")))),p(seq(true,p(get(e.get("operation"),s("operation_key"))),p(s("operation.operation_key")))),p(seq(true,p(get(e.get("operation"),s("hook"))),p(s("operation.hook"))))))) {
                assign(e,new TupleTarget(List.of(new NameTarget("field"),new NameTarget("name"))),q159);
                if(truth(or(e,q160->call(q160,"_available",args(new Part[]{p(q160.get("field"))})),q161->compare(q161,get(q161.get("field"),s("unavailable_reason")),new Comparison(Cmp.NE,q162->q162.get("semantic_reason")))))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid negative projection"))));
                }
            }
        }
        assign(e,new NameTarget("receipt_fields"),binary(Op.SUB,e.get("_RECEIPT_KEYS"),set(p(s("status")))));
        assign(e,new NameTarget("receipt_ready"),FALSE);
        if(truth(compare(e,e.get("receipt_status"),new Comparison(Cmp.EQ,q163->s("recorded"))))) {
            if(truth(or(e,q164->b(!truth(q164.get("semantic_operation"))),q165->b(!truth(call(q165,"_all_available",args(new Part[]{p(q165.get("receipt")),p(q165.get("receipt_fields"))}))))))) {
                throw new Rejected(py(s("recorded receipt lacks its allowlisted operation")));
            }
            assign(e,new NameTarget("receipt_values"),dictFrom(iter(generator(e,q166->seq(true,p(q166.get("key")),p(call(q166,"_value",args(new Part[]{p(get(q166.get("receipt"),q166.get("key"))),p(joined(s("receipt."),s(py(q166.get("key")))))})))),new Clause(new NameTarget("key"),q167->q167.get("receipt_fields"),List.of())))));
            assign(e,new NameTarget("expected_receipt_identity"),dict(new Item(s("key"),s("roster_lock")),new Item(s("owner_character_id"),e.get("owner")),new Item(s("subject_character_id"),e.get("subject")),new Item(s("cycle_serial"),get(e.get("case_values"),s("cycle_serial"))),new Item(s("case_serial"),get(e.get("case_values"),s("case_serial"))),new Item(s("choice"),n("1"))));
            if(truth(or(e,q168->call(q168,"any",args(new Part[]{p(generator(q168,q169->compare(q169,get(q169.get("receipt_values"),q169.get("key")),new Comparison(Cmp.NE,q171->q171.get("expected"))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("expected"))),q170->method(q170.get("expected_receipt_identity"),"items",args(new Part[]{})),List.of())))})),q172->compare(q172,get(q172.get("receipt_values"),s("state")),new Comparison(Cmp.LE,q173->n("0")))))) {
                throw new Rejected(py(s("receipt identity does not match the case")));
            }
            if(truth(or(e,q174->b(!truth(call(q174,"_available",args(new Part[]{p(get(q174.get("operation"),s("pre_state")))})))),q175->b(!truth(call(q175,"_available",args(new Part[]{p(get(q175.get("operation"),s("post_state")))})))),q176->compare(q176,call(q176,"_value",args(new Part[]{p(get(q176.get("operation"),s("pre_state"))),p(s("operation.pre_state"))})),new Comparison(Cmp.NE,q177->get(q177.get("receipt_values"),s("state")))),q178->compare(q178,call(q178,"_value",args(new Part[]{p(get(q178.get("operation"),s("post_state"))),p(s("operation.post_state"))})),new Comparison(Cmp.NE,q179->get(q179.get("receipt_values"),s("state"))))))) {
                throw new Rejected(py(s("receipt does not match the operation state")));
            }
            assign(e,new NameTarget("receipt_ready"),TRUE);
        } else {
            if(truth(compare(e,e.get("receipt_status"),new Comparison(Cmp.EQ,q180->s("not_recorded"))))) {
                if(truth(or(e,q181->b(!truth(q181.get("no_operation"))),q182->b(!truth(call(q182,"_all_unavailable_with_reason",args(new Part[]{p(q182.get("receipt")),p(q182.get("receipt_fields")),p(s("receipt_not_recorded"))}))))))) {
                    throw new Rejected(py(s("not-recorded receipt has invented semantics")));
                }
                for(V q183:iter(seq(true,p(get(e.get("operation"),s("pre_state"))),p(get(e.get("operation"),s("post_state")))))) {
                    assign(e,new NameTarget("field"),q183);
                    if(truth(or(e,q184->call(q184,"_available",args(new Part[]{p(q184.get("field"))})),q185->compare(q185,get(q185.get("field"),s("unavailable_reason")),new Comparison(Cmp.NE,q186->s("receipt_not_recorded")))))) {
                        throw new Rejected(py(s("not-recorded operation invented state")));
                    }
                }
                assign(e,new NameTarget("receipt_ready"),TRUE);
            } else {
                if(truth(e.get("no_operation"))) {
                    throw new Rejected(py(s("operation zero must have a not-recorded receipt")));
                }
                if(truth(b(!truth(call(e,"_all_unavailable_with_reason",args(new Part[]{p(e.get("receipt")),p(e.get("receipt_fields")),p(s("receipt_inconsistent"))})))))) {
                    throw new Rejected(py(s("unavailable receipt leaks inconsistent values")));
                }
                for(V q187:iter(seq(true,p(get(e.get("operation"),s("pre_state"))),p(get(e.get("operation"),s("post_state")))))) {
                    assign(e,new NameTarget("field"),q187);
                    if(truth(or(e,q188->call(q188,"_available",args(new Part[]{p(q188.get("field"))})),q189->compare(q189,get(q189.get("field"),s("unavailable_reason")),new Comparison(Cmp.NE,q190->s("receipt_inconsistent")))))) {
                        throw new Rejected(py(s("inconsistent operation state is malformed")));
                    }
                }
            }
        }
        assign(e,new NameTarget("computed_readiness"),dict(new Item(s("owner_eligibility_ready"),e.get("eligibility_ready")),new Item(s("case_identity_ready"),e.get("case_ready")),new Item(s("stage_ready"),e.get("stage_consistent")),new Item(s("route_ready"),TRUE),new Item(s("receipt_ready"),e.get("receipt_ready")),new Item(s("same_frame_ready"),TRUE),new Item(s("ready"),and(e,q191->q191.get("eligibility_ready"),q192->q192.get("case_ready"),q193->q193.get("stage_consistent"),q194->q194.get("receipt_ready")))));
        if(truth(compare(e,e.get("readiness"),new Comparison(Cmp.NE,q195->q195.get("computed_readiness"))))) {
            throw new Rejected(py(s("readiness disagrees with native semantic facts")));
        }
        return dict(new Expansion(e.get("frame")),new Item(s("owner_eligibility"),e.get("eligibility")),new Item(s("case"),e.get("case")),new Item(s("stage"),e.get("stage")),new Item(s("route"),e.get("route")),new Item(s("policy"),e.get("policy")),new Item(s("operation"),e.get("operation")),new Item(s("receipt"),e.get("receipt")),new Item(s("readiness"),e.get("readiness")),new Item(s("provenance"),call(e,"dict",args(new Part[]{p(e.get("provenance"))}))));
    }
    // Original zhongguo_ai_owned_case_snapshot_contract.py:263..268
    private static V fvalidate_ai_owned_case_request_nonce_v1(E e){
        if(truth(or(e,q196->b(!truth(call(q196,"isinstance",args(new Part[]{p(q196.get("value")),p(q196.get("str"))})))),q197->compare(q197,method(q197.get("_NONCE_RE"),"fullmatch",args(new Part[]{p(q197.get("value"))})),new Comparison(Cmp.IS,q198->NONE))))) {
            throw new Rejected(py(s("request_nonce must be 1-64 ASCII token characters")));
        }
        return e.get("value");
    }
}
