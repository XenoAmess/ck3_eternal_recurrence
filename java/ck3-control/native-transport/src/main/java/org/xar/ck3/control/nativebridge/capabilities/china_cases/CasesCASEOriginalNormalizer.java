package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_case_snapshot_contract.py; original SHA-256 ac2530429b0ed193382275eff57ea1b8fa3fb57dac3c9e3612fea21791953e50. No Python runtime. */
final class CasesCASEOriginalNormalizer {
    private CasesCASEOriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesCASEOriginalNormalizer::dispatch);
        e.put("ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION",s("1.19.0.6"));
        e.put("ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256",s("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"));
        e.put("ZHONGGUO_CASE_SNAPSHOT_V1_BACKEND_ID",s("ck3-1.19.0.6-native-zhongguo-case-snapshot-v1"));
        e.put("ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID",s("xar-autoplayer-zhongguo-case-snapshot-v1"));
        e.put("ZHONGGUO_CASE_SNAPSHOT_V1_ALLOWLIST_ID",s("zg361-b1-performance-case-v1"));
        e.put("ZHONGGUO_B1_PERFORMANCE_CASE_KIND",s("zhongguo.b1.performance"));
        e.put("ZHONGGUO_CASE_KINDS_V1",call(e,"frozenset",args(new Part[]{p(set(p(e.get("ZHONGGUO_B1_PERFORMANCE_CASE_KIND"))))})));
        e.put("_NONCE_RE",regex(text(s("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\\Z"))));
        e.put("_STABLE_KEY_RE",regex(text(s("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\\Z"))));
        e.put("_TYPED_FIELD_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_CASE_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("active")),p(s("revision")),p(s("timeline_serial")),p(s("feedback_revision"))));
        e.put("_POLICY_KEYS",set(p(s("policy_id")),p(s("choice"))));
        e.put("_OPERATION_KEYS",set(p(s("operation_id")),p(s("operation_key")),p(s("hook")),p(s("pre_state")),p(s("post_state"))));
        e.put("_RECEIPT_KEYS",set(p(s("status")),p(s("key")),p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("choice"))));
        e.put("_DEADLINE_KEYS",set(p(s("status")),p(s("target_character_id")),p(s("owner_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("expected_state")),p(s("days")),p(s("pending")),p(s("expired")),p(s("open_date_raw")),p(s("due_date_raw")),p(s("on_due_operation"))));
        e.put("_READINESS_KEYS",set(p(s("player_binding_ready")),p(s("case_identity_ready")),p(s("policy_ready")),p(s("operation_ready")),p(s("receipt_ready")),p(s("deadline_identity_ready")),p(s("deadline_due_date_ready")),p(s("same_frame_ready")),p(s("ready"))));
        e.put("_PROVENANCE_VALUES",dict(new Item(s("game_version"),e.get("ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION")),new Item(s("executable_sha256"),e.get("ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256")),new Item(s("backend_id"),e.get("ZHONGGUO_CASE_SNAPSHOT_V1_BACKEND_ID")),new Item(s("consumer_id"),e.get("ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID")),new Item(s("allowlist_id"),e.get("ZHONGGUO_CASE_SNAPSHOT_V1_ALLOWLIST_ID")),new Item(s("variable_context_for_scope_rva"),s("0x3329A40")),new Item(s("variable_identifier_table_rva"),s("0x3B971A0")),new Item(s("variable_identifier_lookup_rva"),s("0x3B97020")),new Item(s("variable_identifier_name_rva"),s("0x3B97090")),new Item(s("character_storage_slot_rva"),s("0x570C130"))));
        e.put("_PROVENANCE_KEYS",call(e,"set",args(new Part[]{p(e.get("_PROVENANCE_VALUES"))})));
        e.put("_FRAME_KEYS",set(p(s("schema_version")),p(s("status")),p(s("case_kind")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("subject_character_id")),p(s("requested_owner_character_id")),p(s("case")),p(s("policy")),p(s("operation")),p(s("receipt")),p(s("deadline")),p(s("readiness")),p(s("unavailable_reason")),p(s("provenance"))));
        e.put("_TOP_LEVEL_UNAVAILABLE_REASONS",set(p(s("unsupported_build")),p(s("requires_application_main")),p(s("requires_paused")),p(s("map_not_ready")),p(s("subject_not_found")),p(s("case_not_found")),p(s("player_binding_mismatch")),p(s("owner_filter_mismatch")),p(s("variable_identifier_unavailable")),p(s("variable_context_unavailable")),p(s("state_changed")),p(s("internal_error"))));
        e.put("_FIELD_UNAVAILABLE_REASONS",set(p(s("case_unavailable")),p(s("variable_absent")),p(s("value_type_mismatch")),p(s("value_out_of_range")),p(s("no_operation_recorded")),p(s("unknown_allowlisted_operation")),p(s("receipt_not_recorded")),p(s("receipt_inconsistent")),p(s("deadline_not_scheduled")),p(s("deadline_inconsistent")),p(s("due_date_not_persisted_by_product")),p(s("not_applicable"))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_case_snapshot_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_all_typed_available" -> f_all_typed_available(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED),new Param("fields",REQUIRED)),List.of(),null),args));
            case "_all_typed_unavailable" -> f_all_typed_unavailable(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED),new Param("fields",REQUIRED)),List.of(),null),args));
            case "_exact_object" -> f_exact_object(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("fields",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_integer" -> f_integer(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("minimum",REQUIRED),new Param("maximum",REQUIRED)),null),args));
            case "_optional_positive_int32" -> f_optional_positive_int32(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_positive_int32" -> f_positive_int32(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed_available" -> f_typed_available(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED)),List.of(),null),args));
            case "_typed_field" -> f_typed_field(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("value_kind",REQUIRED)),null),args));
            case "_typed_group" -> f_typed_group(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("fields",REQUIRED),new Param("kinds",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed_value" -> f_typed_value(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_case_snapshot_v1" -> fnormalize_native_zhongguo_case_snapshot_v1(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            case "validate_request_nonce_v1" -> fvalidate_request_nonce_v1(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(),null),args));
            case "validate_zhongguo_case_kind_v1" -> fvalidate_zhongguo_case_kind_v1(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(),null),args));
            case "ZhongguoCaseQueryV1" -> new D(new LinkedHashMap<>(bind(GLOBALS,CasesCASEOriginalNormalizer::dispatch,new Sig(List.of(new Param("case_kind",REQUIRED),new Param("subject_character_id",REQUIRED),new Param("owner_character_id",REQUIRED),new Param("request_nonce",REQUIRED)),List.of(),null),args).locals));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_case_snapshot_contract.py:368..374
    private static V f_all_typed_available(E e){
        return call(e,"all",args(new Part[]{p(generator(e,q1->and(q1,q3->call(q3,"isinstance",args(new Part[]{p(get(q3.get("group"),q3.get("field"))),p(q3.get("dict"))})),q4->call(q4,"_typed_available",args(new Part[]{p(get(q4.get("group"),q4.get("field")))}))),new Clause(new NameTarget("field"),q2->q2.get("fields"),List.of())))}));
    }
    // Original zhongguo_case_snapshot_contract.py:377..383
    private static V f_all_typed_unavailable(E e){
        return call(e,"all",args(new Part[]{p(generator(e,q5->and(q5,q7->call(q7,"isinstance",args(new Part[]{p(get(q7.get("group"),q7.get("field"))),p(q7.get("dict"))})),q8->b(!truth(call(q8,"_typed_available",args(new Part[]{p(get(q8.get("group"),q8.get("field")))}))))),new Clause(new NameTarget("field"),q6->q6.get("fields"),List.of())))}));
    }
    // Original zhongguo_case_snapshot_contract.py:296..301
    private static V f_exact_object(E e){
        if(truth(or(e,q9->b(!truth(call(q9,"isinstance",args(new Part[]{p(q9.get("value")),p(q9.get("dict"))})))),q10->compare(q10,call(q10,"set",args(new Part[]{p(q10.get("value"))})),new Comparison(Cmp.NE,q11->q11.get("fields")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_case_snapshot_contract.py:304..313
    private static V f_integer(E e){
        if(truth(or(e,q12->call(q12,"isinstance",args(new Part[]{p(q12.get("value")),p(q12.get("bool"))})),q13->b(!truth(call(q13,"isinstance",args(new Part[]{p(q13.get("value")),p(q13.get("int"))})))),q14->b(!truth(compare(q14,q14.get("minimum"),new Comparison(Cmp.LE,q15->q15.get("value")),new Comparison(Cmp.LE,q16->q16.get("maximum")))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be an integer in range"))));
        }
        return e.get("value");
    }
    // Original zhongguo_case_snapshot_contract.py:233..236
    private static V f_optional_positive_int32(E e){
        if(truth(compare(e,e.get("value"),new Comparison(Cmp.IS,q17->NONE)))) {
            return NONE;
        }
        return call(e,"_positive_int32",args(new Part[]{p(e.get("value")),p(e.get("name"))}));
    }
    // Original zhongguo_case_snapshot_contract.py:223..230
    private static V f_positive_int32(E e){
        if(truth(or(e,q18->call(q18,"isinstance",args(new Part[]{p(q18.get("value")),p(q18.get("bool"))})),q19->b(!truth(call(q19,"isinstance",args(new Part[]{p(q19.get("value")),p(q19.get("int"))})))),q20->b(!truth(compare(q20,n("1"),new Comparison(Cmp.LE,q21->q21.get("value")),new Comparison(Cmp.LE,q22->binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be a positive signed int32"))));
        }
        return e.get("value");
    }
    // Original zhongguo_case_snapshot_contract.py:358..359
    private static V f_typed_available(E e){
        return compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q23->s("available")));
    }
    // Original zhongguo_case_snapshot_contract.py:316..342
    private static V f_typed_field(E e){
        assign(e,new NameTarget("field"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_FIELD_KEYS")),p(e.get("name"))})));
        assign(e,new NameTarget("status"),method(e.get("field"),"get",args(new Part[]{p(s("status"))})));
        assign(e,new NameTarget("raw"),method(e.get("field"),"get",args(new Part[]{p(s("value"))})));
        assign(e,new NameTarget("reason"),method(e.get("field"),"get",args(new Part[]{p(s("unavailable_reason"))})));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q24->s("unavailable"))))) {
            if(truth(or(e,q25->compare(q25,q25.get("raw"),new Comparison(Cmp.IS_NOT,q26->NONE)),q27->compare(q27,q27.get("reason"),new Comparison(Cmp.NOT_IN,q28->q28.get("_FIELD_UNAVAILABLE_REASONS")))))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid typed unavailable value"))));
            }
            return call(e,"dict",args(new Part[]{p(e.get("field"))}));
        }
        if(truth(or(e,q29->compare(q29,q29.get("status"),new Comparison(Cmp.NE,q30->s("available"))),q31->compare(q31,q31.get("reason"),new Comparison(Cmp.IS_NOT,q32->NONE))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid availability status"))));
        }
        if(truth(compare(e,e.get("value_kind"),new Comparison(Cmp.EQ,q33->s("int"))))) {
            call(e,"_integer",args(new Part[]{p(e.get("raw")),p(e.get("name"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
        } else {
            if(truth(compare(e,e.get("value_kind"),new Comparison(Cmp.EQ,q34->s("bool"))))) {
                if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(e.get("raw")),p(e.get("bool"))})))))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(".value must be boolean"))));
                }
            } else {
                if(truth(compare(e,e.get("value_kind"),new Comparison(Cmp.EQ,q35->s("string"))))) {
                    if(truth(or(e,q36->b(!truth(call(q36,"isinstance",args(new Part[]{p(q36.get("raw")),p(q36.get("str"))})))),q37->compare(q37,method(q37.get("_STABLE_KEY_RE"),"fullmatch",args(new Part[]{p(q37.get("raw"))})),new Comparison(Cmp.IS,q38->NONE))))) {
                        throw new Rejected(py(joined(s(py(e.get("name"))),s(".value must be a bounded stable key"))));
                    }
                } else {
                    throw new AssertionError(py(e.get("value_kind")));
                }
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_case_snapshot_contract.py:345..355
    private static V f_typed_group(E e){
        assign(e,new NameTarget("group"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("fields")),p(e.get("name"))})));
        return dictFrom(iter(generator(e,q39->seq(true,p(q39.get("field")),p(call(q39,"_typed_field",args(new Part[]{p(get(q39.get("group"),q39.get("field"))),p(joined(s(py(q39.get("name"))),s("."),s(py(q39.get("field")))))},new Kw("value_kind",q39.get("kind")))))),new Clause(new TupleTarget(List.of(new NameTarget("field"),new NameTarget("kind"))),q40->method(q40.get("kinds"),"items",args(new Part[]{})),List.of()))));
    }
    // Original zhongguo_case_snapshot_contract.py:362..365
    private static V f_typed_value(E e){
        if(truth(b(!truth(call(e,"_typed_available",args(new Part[]{p(e.get("field"))})))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be available"))));
        }
        return get(e.get("field"),s("value"));
    }
    // Original zhongguo_case_snapshot_contract.py:400..841
    private static V fnormalize_native_zhongguo_case_snapshot_v1(E e){
        assign(e,new NameTarget("expected_query"),call(e,"ZhongguoCaseQueryV1",args(new Part[]{},new Kw("case_kind",call(e,"validate_zhongguo_case_kind_v1",args(new Part[]{p(attribute(e.get("expected_query"),"case_kind"))}))),new Kw("subject_character_id",call(e,"_positive_int32",args(new Part[]{p(attribute(e.get("expected_query"),"subject_character_id")),p(s("expected_query.subject_character_id"))}))),new Kw("owner_character_id",call(e,"_optional_positive_int32",args(new Part[]{p(attribute(e.get("expected_query"),"owner_character_id")),p(s("expected_query.owner_character_id"))}))),new Kw("request_nonce",call(e,"validate_request_nonce_v1",args(new Part[]{p(attribute(e.get("expected_query"),"request_nonce"))}))))));
        assign(e,new NameTarget("expected_snapshot_revision"),call(e,"_integer",args(new Part[]{p(e.get("expected_snapshot_revision")),p(s("expected_snapshot_revision"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1"))))));
        assign(e,new NameTarget("expected_date_raw"),call(e,"_integer",args(new Part[]{p(e.get("expected_date_raw")),p(s("expected_date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))));
        assign(e,new NameTarget("expected_player_character_id"),call(e,"_positive_int32",args(new Part[]{p(e.get("expected_player_character_id")),p(s("expected_player_character_id"))})));
        assign(e,new NameTarget("frame"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("_FRAME_KEYS")),p(s("zhongguo_case_snapshot"))})));
        if(truth(compare(e,method(e.get("frame"),"get",args(new Part[]{p(s("schema_version"))})),new Comparison(Cmp.NE,q41->n("1"))))) {
            throw new Rejected(py(s("schema_version must be 1")));
        }
        if(truth(compare(e,method(e.get("frame"),"get",args(new Part[]{p(s("case_kind"))})),new Comparison(Cmp.NE,q42->attribute(q42.get("expected_query"),"case_kind"))))) {
            throw new Rejected(py(s("case_kind binding changed")));
        }
        if(truth(compare(e,method(e.get("frame"),"get",args(new Part[]{p(s("request_nonce"))})),new Comparison(Cmp.NE,q43->attribute(q43.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("request_nonce binding changed")));
        }
        assign(e,new NameTarget("revision"),call(e,"_integer",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("snapshot_revision"))}))),p(s("snapshot_revision"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1"))))));
        if(truth(compare(e,e.get("revision"),new Comparison(Cmp.NE,q44->q44.get("expected_snapshot_revision"))))) {
            throw new Rejected(py(s("snapshot revision binding changed")));
        }
        assign(e,new NameTarget("date_raw"),call(e,"_integer",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("date_raw"))}))),p(s("date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))));
        if(truth(compare(e,e.get("date_raw"),new Comparison(Cmp.NE,q45->q45.get("expected_date_raw"))))) {
            throw new Rejected(py(s("date binding changed")));
        }
        if(truth(compare(e,method(e.get("frame"),"get",args(new Part[]{p(s("paused"))})),new Comparison(Cmp.IS_NOT,q46->TRUE)))) {
            throw new Rejected(py(s("native ZhongGuo query is not paused")));
        }
        assign(e,new NameTarget("player"),call(e,"_positive_int32",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("player_character_id"))}))),p(s("player_character_id"))})));
        if(truth(compare(e,e.get("player"),new Comparison(Cmp.NE,q47->q47.get("expected_player_character_id"))))) {
            throw new Rejected(py(s("player identity binding changed")));
        }
        assign(e,new NameTarget("subject"),call(e,"_positive_int32",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("subject_character_id"))}))),p(s("subject_character_id"))})));
        if(truth(compare(e,e.get("subject"),new Comparison(Cmp.NE,q48->attribute(q48.get("expected_query"),"subject_character_id"))))) {
            throw new Rejected(py(s("subject identity binding changed")));
        }
        assign(e,new NameTarget("requested_owner"),call(e,"_optional_positive_int32",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("requested_owner_character_id"))}))),p(s("requested_owner_character_id"))})));
        if(truth(compare(e,e.get("requested_owner"),new Comparison(Cmp.NE,q49->attribute(q49.get("expected_query"),"owner_character_id"))))) {
            throw new Rejected(py(s("owner filter binding changed")));
        }
        assign(e,new NameTarget("case"),call(e,"_typed_group",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("case"))}))),p(e.get("_CASE_KEYS")),p(dict(new Item(s("owner_character_id"),s("int")),new Item(s("subject_character_id"),s("int")),new Item(s("cycle_serial"),s("int")),new Item(s("case_serial"),s("int")),new Item(s("state"),s("int")),new Item(s("active"),s("bool")),new Item(s("revision"),s("int")),new Item(s("timeline_serial"),s("int")),new Item(s("feedback_revision"),s("int")))),p(s("case"))})));
        assign(e,new NameTarget("policy"),call(e,"_typed_group",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("policy"))}))),p(e.get("_POLICY_KEYS")),p(dict(new Item(s("policy_id"),s("string")),new Item(s("choice"),s("int")))),p(s("policy"))})));
        assign(e,new NameTarget("operation"),call(e,"_typed_group",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("operation"))}))),p(e.get("_OPERATION_KEYS")),p(dict(new Item(s("operation_id"),s("int")),new Item(s("operation_key"),s("string")),new Item(s("hook"),s("string")),new Item(s("pre_state"),s("int")),new Item(s("post_state"),s("int")))),p(s("operation"))})));
        assign(e,new NameTarget("receipt_raw"),call(e,"_exact_object",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("receipt"))}))),p(e.get("_RECEIPT_KEYS")),p(s("receipt"))})));
        if(truth(compare(e,method(e.get("receipt_raw"),"get",args(new Part[]{p(s("status"))})),new Comparison(Cmp.NOT_IN,q50->set(p(s("recorded")),p(s("not_recorded")),p(s("unavailable"))))))) {
            throw new Rejected(py(s("receipt.status is invalid")));
        }
        assign(e,new NameTarget("receipt"),dict(new Item(s("status"),get(e.get("receipt_raw"),s("status"))),new Expansion(dictFrom(iter(generator(e,q51->seq(true,p(q51.get("field")),p(call(q51,"_typed_field",args(new Part[]{p(get(q51.get("receipt_raw"),q51.get("field"))),p(joined(s("receipt."),s(py(q51.get("field")))))},new Kw("value_kind",q51.get("kind")))))),new Clause(new TupleTarget(List.of(new NameTarget("field"),new NameTarget("kind"))),q52->method(dict(new Item(s("key"),s("string")),new Item(s("owner_character_id"),s("int")),new Item(s("subject_character_id"),s("int")),new Item(s("cycle_serial"),s("int")),new Item(s("case_serial"),s("int")),new Item(s("state"),s("int")),new Item(s("choice"),s("int"))),"items",args(new Part[]{})),List.of())))))));
        assign(e,new NameTarget("deadline_raw"),call(e,"_exact_object",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("deadline"))}))),p(e.get("_DEADLINE_KEYS")),p(s("deadline"))})));
        if(truth(compare(e,method(e.get("deadline_raw"),"get",args(new Part[]{p(s("status"))})),new Comparison(Cmp.NOT_IN,q53->set(p(s("pending")),p(s("expired")),p(s("not_scheduled")),p(s("unavailable"))))))) {
            throw new Rejected(py(s("deadline.status is invalid")));
        }
        assign(e,new NameTarget("deadline"),dict(new Item(s("status"),get(e.get("deadline_raw"),s("status"))),new Expansion(dictFrom(iter(generator(e,q54->seq(true,p(q54.get("field")),p(call(q54,"_typed_field",args(new Part[]{p(get(q54.get("deadline_raw"),q54.get("field"))),p(joined(s("deadline."),s(py(q54.get("field")))))},new Kw("value_kind",q54.get("kind")))))),new Clause(new TupleTarget(List.of(new NameTarget("field"),new NameTarget("kind"))),q55->method(dict(new Item(s("target_character_id"),s("int")),new Item(s("owner_character_id"),s("int")),new Item(s("cycle_serial"),s("int")),new Item(s("case_serial"),s("int")),new Item(s("expected_state"),s("int")),new Item(s("days"),s("int")),new Item(s("pending"),s("bool")),new Item(s("expired"),s("bool")),new Item(s("open_date_raw"),s("int")),new Item(s("due_date_raw"),s("int")),new Item(s("on_due_operation"),s("string"))),"items",args(new Part[]{})),List.of())))))));
        assign(e,new NameTarget("readiness_raw"),call(e,"_exact_object",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("readiness"))}))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        assign(e,new NameTarget("readiness"),dict());
        for(V q56:iter(e.get("_READINESS_KEYS"))) {
            assign(e,new NameTarget("key"),q56);
            assign(e,new NameTarget("flag"),method(e.get("readiness_raw"),"get",args(new Part[]{p(e.get("key"))})));
            if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(e.get("flag")),p(e.get("bool"))})))))) {
                throw new Rejected(py(joined(s("readiness."),s(py(e.get("key"))),s(" must be boolean"))));
            }
            put(e.get("readiness"),e.get("key"),e.get("flag"));
        }
        assign(e,new NameTarget("expected_ready"),call(e,"all",args(new Part[]{p(generator(e,q57->get(q57.get("readiness"),q57.get("key")),new Clause(new NameTarget("key"),q58->q58.get("_READINESS_KEYS"),List.of(q58->compare(q58,q58.get("key"),new Comparison(Cmp.NE,q59->s("ready")))))))})));
        if(truth(compare(e,get(e.get("readiness"),s("ready")),new Comparison(Cmp.IS_NOT,q60->q60.get("expected_ready"))))) {
            throw new Rejected(py(s("readiness.ready does not equal the component gate")));
        }
        assign(e,new NameTarget("provenance"),call(e,"_exact_object",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("provenance"))}))),p(e.get("_PROVENANCE_KEYS")),p(s("provenance"))})));
        if(truth(call(e,"any",args(new Part[]{p(generator(e,q61->compare(q61,method(q61.get("provenance"),"get",args(new Part[]{p(q61.get("key"))})),new Comparison(Cmp.NE,q63->q63.get("expected"))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("expected"))),q62->method(q62.get("_PROVENANCE_VALUES"),"items",args(new Part[]{})),List.of())))})))) {
            throw new Rejected(py(s("provenance does not match the frozen exact build")));
        }
        assign(e,new NameTarget("status"),method(e.get("frame"),"get",args(new Part[]{p(s("status"))})));
        assign(e,new NameTarget("reason"),method(e.get("frame"),"get",args(new Part[]{p(s("unavailable_reason"))})));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q64->s("available"))))) {
            if(truth(or(e,q65->compare(q65,q65.get("reason"),new Comparison(Cmp.IS_NOT,q66->NONE)),q67->b(!truth(get(q67.get("readiness"),s("player_binding_ready")))),q68->b(!truth(get(q68.get("readiness"),s("case_identity_ready"))))))) {
                throw new Rejected(py(s("available frame lacks a valid case identity")));
            }
        } else {
            if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q69->s("unavailable"))))) {
                if(truth(or(e,q70->compare(q70,q70.get("reason"),new Comparison(Cmp.NOT_IN,q71->q71.get("_TOP_LEVEL_UNAVAILABLE_REASONS"))),q72->get(q72.get("readiness"),s("ready"))))) {
                    throw new Rejected(py(s("unavailable frame has an invalid reason/gate")));
                }
            } else {
                throw new Rejected(py(s("status must be available or unavailable")));
            }
        }
        assign(e,new NameTarget("case_ready"),call(e,"_all_typed_available",args(new Part[]{p(e.get("case")),p(e.get("_CASE_KEYS"))})));
        if(truth(compare(e,get(e.get("readiness"),s("case_identity_ready")),new Comparison(Cmp.IS_NOT,q73->q73.get("case_ready"))))) {
            throw new Rejected(py(s("case identity readiness disagrees with typed fields")));
        }
        if(truth(e.get("case_ready"))) {
            assign(e,new NameTarget("case_owner"),call(e,"_positive_int32",args(new Part[]{p(call(e,"_typed_value",args(new Part[]{p(get(e.get("case"),s("owner_character_id"))),p(s("case.owner_character_id"))}))),p(s("case.owner_character_id"))})));
            assign(e,new NameTarget("case_subject"),call(e,"_positive_int32",args(new Part[]{p(call(e,"_typed_value",args(new Part[]{p(get(e.get("case"),s("subject_character_id"))),p(s("case.subject_character_id"))}))),p(s("case.subject_character_id"))})));
            if(truth(compare(e,e.get("case_subject"),new Comparison(Cmp.NE,q74->q74.get("subject"))))) {
                throw new Rejected(py(s("available case subject does not match the request")));
            }
            if(truth(compare(e,e.get("case_owner"),new Comparison(Cmp.NE,q75->q75.get("player"))))) {
                throw new Rejected(py(s("available case owner does not match the player")));
            }
            if(truth(and(e,q76->compare(q76,q76.get("requested_owner"),new Comparison(Cmp.IS_NOT,q77->NONE)),q78->compare(q78,q78.get("case_owner"),new Comparison(Cmp.NE,q79->q79.get("requested_owner")))))) {
                throw new Rejected(py(s("available case owner does not match the filter")));
            }
            for(V q80:iter(seq(true,p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("revision")),p(s("timeline_serial")),p(s("feedback_revision"))))) {
                assign(e,new NameTarget("field"),q80);
                call(e,"_integer",args(new Part[]{p(call(e,"_typed_value",args(new Part[]{p(get(e.get("case"),e.get("field"))),p(joined(s("case."),s(py(e.get("field")))))}))),p(joined(s("case."),s(py(e.get("field")))))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
            }
        }
        assign(e,new NameTarget("policy_ready"),call(e,"_all_typed_available",args(new Part[]{p(e.get("policy")),p(e.get("_POLICY_KEYS"))})));
        assign(e,new NameTarget("operation_ready"),call(e,"_all_typed_available",args(new Part[]{p(e.get("operation")),p(e.get("_OPERATION_KEYS"))})));
        if(truth(compare(e,get(e.get("readiness"),s("policy_ready")),new Comparison(Cmp.IS_NOT,q81->q81.get("policy_ready"))))) {
            throw new Rejected(py(s("policy readiness disagrees with typed fields")));
        }
        if(truth(compare(e,get(e.get("readiness"),s("operation_ready")),new Comparison(Cmp.IS_NOT,q82->q82.get("operation_ready"))))) {
            throw new Rejected(py(s("operation readiness disagrees with typed fields")));
        }
        if(truth(e.get("policy_ready"))) {
            assign(e,new NameTarget("policy_values"),dictFrom(iter(generator(e,q83->seq(true,p(q83.get("key")),p(call(q83,"_typed_value",args(new Part[]{p(get(q83.get("policy"),q83.get("key"))),p(joined(s("policy."),s(py(q83.get("key")))))})))),new Clause(new NameTarget("key"),q84->q84.get("_POLICY_KEYS"),List.of())))));
            if(truth(compare(e,e.get("policy_values"),new Comparison(Cmp.NE,q85->dict(new Item(s("policy_id"),s("mechanism_039")),new Item(s("choice"),n("1"))))))) {
                throw new Rejected(py(s("policy is outside the B1 v1 semantic allowlist")));
            }
        }
        if(truth(e.get("operation_ready"))) {
            if(truth(b(!truth(e.get("policy_ready"))))) {
                throw new Rejected(py(s("a recorded operation must expose its policy")));
            }
            assign(e,new NameTarget("operation_values"),dictFrom(iter(generator(e,q86->seq(true,p(q86.get("key")),p(call(q86,"_typed_value",args(new Part[]{p(get(q86.get("operation"),q86.get("key"))),p(joined(s("operation."),s(py(q86.get("key")))))})))),new Clause(new NameTarget("key"),q87->q87.get("_OPERATION_KEYS"),List.of())))));
            if(truth(or(e,q88->compare(q88,get(q88.get("operation_values"),s("operation_id")),new Comparison(Cmp.NE,q89->n("39"))),q90->compare(q90,get(q90.get("operation_values"),s("operation_key")),new Comparison(Cmp.NE,q91->s("roster_lock"))),q92->compare(q92,get(q92.get("operation_values"),s("hook")),new Comparison(Cmp.NE,q93->s("roster_lock")))))) {
                throw new Rejected(py(s("operation is outside the B1 v1 semantic allowlist")));
            }
            for(V q94:iter(seq(true,p(s("pre_state")),p(s("post_state"))))) {
                assign(e,new NameTarget("field"),q94);
                call(e,"_integer",args(new Part[]{p(get(e.get("operation_values"),e.get("field"))),p(joined(s("operation."),s(py(e.get("field")))))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
            }
        }
        assign(e,new NameTarget("receipt_fields"),binary(Op.SUB,e.get("_RECEIPT_KEYS"),set(p(s("status")))));
        assign(e,new NameTarget("receipt_available"),call(e,"_all_typed_available",args(new Part[]{p(e.get("receipt")),p(e.get("receipt_fields"))})));
        assign(e,new NameTarget("receipt_unavailable"),call(e,"_all_typed_unavailable",args(new Part[]{p(e.get("receipt")),p(e.get("receipt_fields"))})));
        assign(e,new NameTarget("receipt_status"),get(e.get("receipt"),s("status")));
        assign(e,new NameTarget("receipt_ready"),or(e,q95->and(q95,q96->compare(q96,q96.get("receipt_status"),new Comparison(Cmp.EQ,q97->s("recorded"))),q98->q98.get("receipt_available")),q99->and(q99,q100->compare(q100,q100.get("receipt_status"),new Comparison(Cmp.EQ,q101->s("not_recorded"))),q102->q102.get("receipt_unavailable"))));
        if(truth(and(e,q103->compare(q103,q103.get("receipt_status"),new Comparison(Cmp.EQ,q104->s("unavailable"))),q105->b(!truth(q105.get("receipt_unavailable")))))) {
            throw new Rejected(py(s("unavailable receipt contains invented values")));
        }
        if(truth(compare(e,get(e.get("readiness"),s("receipt_ready")),new Comparison(Cmp.IS_NOT,q106->q106.get("receipt_ready"))))) {
            throw new Rejected(py(s("receipt readiness disagrees with typed fields")));
        }
        if(truth(compare(e,e.get("operation_ready"),new Comparison(Cmp.IS_NOT,q107->compare(q107,q107.get("receipt_status"),new Comparison(Cmp.EQ,q108->s("recorded"))))))) {
            throw new Rejected(py(s("operation and receipt availability disagree")));
        }
        if(truth(compare(e,e.get("receipt_status"),new Comparison(Cmp.EQ,q109->s("recorded"))))) {
            assign(e,new NameTarget("receipt_values"),dictFrom(iter(generator(e,q110->seq(true,p(q110.get("key")),p(call(q110,"_typed_value",args(new Part[]{p(get(q110.get("receipt"),q110.get("key"))),p(joined(s("receipt."),s(py(q110.get("key")))))})))),new Clause(new NameTarget("key"),q111->q111.get("receipt_fields"),List.of())))));
            if(truth(compare(e,get(e.get("receipt_values"),s("key")),new Comparison(Cmp.NE,q112->s("roster_lock"))))) {
                throw new Rejected(py(s("receipt key is outside the B1 v1 allowlist")));
            }
            if(truth(and(e,q113->q113.get("case_ready"),q114->or(q114,q115->compare(q115,get(q115.get("receipt_values"),s("owner_character_id")),new Comparison(Cmp.NE,q116->q116.get("case_owner"))),q117->compare(q117,get(q117.get("receipt_values"),s("subject_character_id")),new Comparison(Cmp.NE,q118->q118.get("case_subject"))),q119->compare(q119,get(q119.get("receipt_values"),s("cycle_serial")),new Comparison(Cmp.NE,q120->call(q120,"_typed_value",args(new Part[]{p(get(q120.get("case"),s("cycle_serial"))),p(s("case.cycle_serial"))})))),q121->compare(q121,get(q121.get("receipt_values"),s("case_serial")),new Comparison(Cmp.NE,q122->call(q122,"_typed_value",args(new Part[]{p(get(q122.get("case"),s("case_serial"))),p(s("case.case_serial"))})))))))) {
                throw new Rejected(py(s("receipt identity does not match the case")));
            }
            for(V q123:iter(seq(true,p(s("owner_character_id")),p(s("subject_character_id"))))) {
                assign(e,new NameTarget("field"),q123);
                call(e,"_positive_int32",args(new Part[]{p(get(e.get("receipt_values"),e.get("field"))),p(joined(s("receipt."),s(py(e.get("field")))))}));
            }
            for(V q124:iter(seq(true,p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("choice"))))) {
                assign(e,new NameTarget("field"),q124);
                call(e,"_integer",args(new Part[]{p(get(e.get("receipt_values"),e.get("field"))),p(joined(s("receipt."),s(py(e.get("field")))))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
            }
            if(truth(compare(e,get(e.get("receipt_values"),s("choice")),new Comparison(Cmp.NE,q125->n("1"))))) {
                throw new Rejected(py(s("receipt choice is outside the B1 v1 allowlist")));
            }
            if(truth(and(e,q126->q126.get("operation_ready"),q127->or(q127,q128->compare(q128,get(q128.get("receipt_values"),s("state")),new Comparison(Cmp.NE,q129->get(q129.get("operation_values"),s("pre_state")))),q130->compare(q130,get(q130.get("operation_values"),s("pre_state")),new Comparison(Cmp.NE,q131->get(q131.get("operation_values"),s("post_state")))),q132->compare(q132,get(q132.get("receipt_values"),s("choice")),new Comparison(Cmp.NE,q133->get(q133.get("policy_values"),s("choice")))))))) {
                throw new Rejected(py(s("receipt does not match the recorded operation")));
            }
        }
        assign(e,new NameTarget("deadline_fields"),binary(Op.SUB,e.get("_DEADLINE_KEYS"),set(p(s("status")))));
        assign(e,new NameTarget("deadline_unavailable"),call(e,"_all_typed_unavailable",args(new Part[]{p(e.get("deadline")),p(e.get("deadline_fields"))})));
        assign(e,new NameTarget("deadline_status"),get(e.get("deadline"),s("status")));
        assign(e,new NameTarget("deadline_identity_ready"),compare(e,e.get("deadline_status"),new Comparison(Cmp.EQ,q134->s("not_scheduled"))));
        if(truth(compare(e,e.get("deadline_status"),new Comparison(Cmp.IN,q135->set(p(s("pending")),p(s("expired"))))))) {
            assign(e,new NameTarget("identity_fields"),binary(Op.SUB,e.get("deadline_fields"),set(p(s("open_date_raw")),p(s("due_date_raw")))));
            assign(e,new NameTarget("deadline_identity_ready"),call(e,"_all_typed_available",args(new Part[]{p(e.get("deadline")),p(e.get("identity_fields"))})));
        } else {
            if(truth(and(e,q136->compare(q136,q136.get("deadline_status"),new Comparison(Cmp.EQ,q137->s("unavailable"))),q138->b(!truth(q138.get("deadline_unavailable")))))) {
                throw new Rejected(py(s("unavailable deadline contains invented values")));
            } else {
                if(truth(and(e,q139->compare(q139,q139.get("deadline_status"),new Comparison(Cmp.EQ,q140->s("not_scheduled"))),q141->b(!truth(q141.get("deadline_unavailable")))))) {
                    throw new Rejected(py(s("unscheduled deadline contains invented values")));
                }
            }
        }
        if(truth(compare(e,get(e.get("readiness"),s("deadline_identity_ready")),new Comparison(Cmp.IS_NOT,q142->q142.get("deadline_identity_ready"))))) {
            throw new Rejected(py(s("deadline identity readiness disagrees with fields")));
        }
        assign(e,new NameTarget("due_date_ready"),FALSE);
        if(truth(compare(e,e.get("deadline_status"),new Comparison(Cmp.IN,q143->set(p(s("pending")),p(s("expired"))))))) {
            assign(e,new NameTarget("due_date_ready"),call(e,"_typed_available",args(new Part[]{p(get(e.get("deadline"),s("due_date_raw")))})));
        } else {
            if(truth(compare(e,e.get("deadline_status"),new Comparison(Cmp.EQ,q144->s("not_scheduled"))))) {
                assign(e,new NameTarget("due_date_ready"),TRUE);
            }
        }
        if(truth(compare(e,get(e.get("readiness"),s("deadline_due_date_ready")),new Comparison(Cmp.IS_NOT,q145->q145.get("due_date_ready"))))) {
            throw new Rejected(py(s("deadline due-date readiness disagrees with fields")));
        }
        if(truth(and(e,q146->compare(q146,q146.get("deadline_status"),new Comparison(Cmp.IN,q147->set(p(s("pending")),p(s("expired"))))),q148->q148.get("deadline_identity_ready")))) {
            assign(e,new NameTarget("deadline_values"),dictFrom(iter(generator(e,q149->seq(true,p(q149.get("key")),p(call(q149,"_typed_value",args(new Part[]{p(get(q149.get("deadline"),q149.get("key"))),p(joined(s("deadline."),s(py(q149.get("key")))))})))),new Clause(new NameTarget("key"),q150->binary(Op.SUB,q150.get("deadline_fields"),set(p(s("open_date_raw")),p(s("due_date_raw")))),List.of())))));
            if(truth(compare(e,get(e.get("deadline_values"),s("on_due_operation")),new Comparison(Cmp.NE,q151->s("resolve_pending_milestone"))))) {
                throw new Rejected(py(s("deadline operation is outside the B1 v1 allowlist")));
            }
            if(truth(compare(e,get(e.get("deadline_values"),s("target_character_id")),new Comparison(Cmp.NE,q152->q152.get("subject"))))) {
                throw new Rejected(py(s("deadline target does not match the subject")));
            }
            if(truth(and(e,q153->q153.get("case_ready"),q154->or(q154,q155->compare(q155,get(q155.get("deadline_values"),s("owner_character_id")),new Comparison(Cmp.NE,q156->q156.get("case_owner"))),q157->compare(q157,get(q157.get("deadline_values"),s("cycle_serial")),new Comparison(Cmp.NE,q158->call(q158,"_typed_value",args(new Part[]{p(get(q158.get("case"),s("cycle_serial"))),p(s("case.cycle_serial"))})))),q159->compare(q159,get(q159.get("deadline_values"),s("case_serial")),new Comparison(Cmp.NE,q160->call(q160,"_typed_value",args(new Part[]{p(get(q160.get("case"),s("case_serial"))),p(s("case.case_serial"))})))))))) {
                throw new Rejected(py(s("deadline identity does not match the case")));
            }
            if(truth(compare(e,get(e.get("deadline_values"),s("pending")),new Comparison(Cmp.IS_NOT,q161->compare(q161,q161.get("deadline_status"),new Comparison(Cmp.EQ,q162->s("pending"))))))) {
                throw new Rejected(py(s("deadline pending flag disagrees with status")));
            }
            if(truth(compare(e,get(e.get("deadline_values"),s("expired")),new Comparison(Cmp.IS_NOT,q163->compare(q163,q163.get("deadline_status"),new Comparison(Cmp.EQ,q164->s("expired"))))))) {
                throw new Rejected(py(s("deadline expired flag disagrees with status")));
            }
            for(V q165:iter(seq(true,p(s("target_character_id")),p(s("owner_character_id"))))) {
                assign(e,new NameTarget("field"),q165);
                call(e,"_positive_int32",args(new Part[]{p(get(e.get("deadline_values"),e.get("field"))),p(joined(s("deadline."),s(py(e.get("field")))))}));
            }
            for(V q166:iter(seq(true,p(s("cycle_serial")),p(s("case_serial")),p(s("expected_state")),p(s("days"))))) {
                assign(e,new NameTarget("field"),q166);
                call(e,"_integer",args(new Part[]{p(get(e.get("deadline_values"),e.get("field"))),p(joined(s("deadline."),s(py(e.get("field")))))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
            }
            assign(e,new NameTarget("open_date_raw"),NONE);
            if(truth(call(e,"_typed_available",args(new Part[]{p(get(e.get("deadline"),s("open_date_raw")))})))) {
                assign(e,new NameTarget("open_date_raw"),call(e,"_integer",args(new Part[]{p(call(e,"_typed_value",args(new Part[]{p(get(e.get("deadline"),s("open_date_raw"))),p(s("deadline.open_date_raw"))}))),p(s("deadline.open_date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))));
            }
            if(truth(e.get("due_date_ready"))) {
                assign(e,new NameTarget("due_date_raw"),call(e,"_integer",args(new Part[]{p(call(e,"_typed_value",args(new Part[]{p(get(e.get("deadline"),s("due_date_raw"))),p(s("deadline.due_date_raw"))}))),p(s("deadline.due_date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))));
                if(truth(and(e,q167->compare(q167,q167.get("open_date_raw"),new Comparison(Cmp.IS_NOT,q168->NONE)),q169->compare(q169,q169.get("due_date_raw"),new Comparison(Cmp.LT,q170->q170.get("open_date_raw")))))) {
                    throw new Rejected(py(s("deadline due date precedes its open date")));
                }
            }
        }
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q171->s("unavailable"))))) {
            if(truth(b(!truth(and(e,q172->call(q172,"_all_typed_unavailable",args(new Part[]{p(q172.get("case")),p(q172.get("_CASE_KEYS"))})),q173->call(q173,"_all_typed_unavailable",args(new Part[]{p(q173.get("policy")),p(q173.get("_POLICY_KEYS"))})),q174->call(q174,"_all_typed_unavailable",args(new Part[]{p(q174.get("operation")),p(q174.get("_OPERATION_KEYS"))})),q175->compare(q175,q175.get("receipt_status"),new Comparison(Cmp.EQ,q176->s("unavailable"))),q177->compare(q177,q177.get("deadline_status"),new Comparison(Cmp.EQ,q178->s("unavailable")))))))) {
                throw new Rejected(py(s("unavailable frame contains invented case data")));
            }
        }
        return dict(new Expansion(e.get("frame")),new Item(s("case"),e.get("case")),new Item(s("policy"),e.get("policy")),new Item(s("operation"),e.get("operation")),new Item(s("receipt"),e.get("receipt")),new Item(s("deadline"),e.get("deadline")),new Item(s("readiness"),e.get("readiness")),new Item(s("provenance"),call(e,"dict",args(new Part[]{p(e.get("provenance"))}))));
    }
    // Original zhongguo_case_snapshot_contract.py:215..220
    private static V fvalidate_request_nonce_v1(E e){
        if(truth(or(e,q179->b(!truth(call(q179,"isinstance",args(new Part[]{p(q179.get("value")),p(q179.get("str"))})))),q180->compare(q180,method(q180.get("_NONCE_RE"),"fullmatch",args(new Part[]{p(q180.get("value"))})),new Comparison(Cmp.IS,q181->NONE))))) {
            throw new Rejected(py(s("request_nonce must be 1-64 ASCII token characters")));
        }
        return e.get("value");
    }
    // Original zhongguo_case_snapshot_contract.py:207..212
    private static V fvalidate_zhongguo_case_kind_v1(E e){
        if(truth(or(e,q182->b(!truth(call(q182,"isinstance",args(new Part[]{p(q182.get("value")),p(q182.get("str"))})))),q183->compare(q183,q183.get("value"),new Comparison(Cmp.NOT_IN,q184->q184.get("ZHONGGUO_CASE_KINDS_V1")))))) {
            throw new Rejected(py(s("case_kind must be an allowlisted ZhongGuo v1 case kind")));
        }
        return e.get("value");
    }
}
