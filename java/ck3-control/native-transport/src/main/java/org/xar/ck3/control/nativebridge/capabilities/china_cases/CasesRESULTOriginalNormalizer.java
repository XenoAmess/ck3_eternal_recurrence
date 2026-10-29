package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_result_case_snapshot_contract.py; original SHA-256 7eb341d0f4094536a92ce20762c6b939d5b68daff19f61da44c8ab636db42ac4. No Python runtime. */
final class CasesRESULTOriginalNormalizer {
    private CasesRESULTOriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesRESULTOriginalNormalizer::dispatch);
        e.put("ZHONGGUO_RESULT_CASE_KIND_V1",s("zhongguo.result.received-self"));
        e.put("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION",s("1.19.0.6"));
        e.put("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256",s("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"));
        e.put("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BACKEND_ID",s("ck3-1.19.0.6-native-zhongguo-result-case-snapshot-v1"));
        e.put("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID",s("xar-autoplayer-zhongguo-result-case-snapshot-v1"));
        e.put("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_ALLOWLIST_ID",s("zg361-result-received-self-v1"));
        e.put("_NONCE_RE",regex(text(s("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\\Z"))));
        e.put("_TYPED_FIELD_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_CASE_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("grade"))));
        e.put("_NOTICE_KEYS",set(p(s("absolute_grade")),p(s("kpi_frozen_q100000")),p(s("rank_frozen")),p(s("cohort_n_frozen"))));
        e.put("_DELIVERY_KEYS",set(p(s("method")),p(s("objection_recorded")),p(s("settlement_posted_serial")),p(s("appeal_open"))));
        e.put("_READINESS_KEYS",set(p(s("player_subject_binding_ready")),p(s("owner_binding_ready")),p(s("case_identity_ready")),p(s("notice_facts_ready")),p(s("delivery_state_ready")),p(s("same_frame_ready")),p(s("ready"))));
        e.put("_PROVENANCE_VALUES",dict(new Item(s("game_version"),e.get("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION")),new Item(s("executable_sha256"),e.get("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256")),new Item(s("backend_id"),e.get("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BACKEND_ID")),new Item(s("consumer_id"),e.get("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID")),new Item(s("allowlist_id"),e.get("ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_ALLOWLIST_ID")),new Item(s("variable_context_for_scope_rva"),s("0x3329A40")),new Item(s("variable_identifier_table_rva"),s("0x3B971A0")),new Item(s("variable_identifier_lookup_rva"),s("0x3B97020")),new Item(s("variable_identifier_name_rva"),s("0x3B97090")),new Item(s("character_storage_slot_rva"),s("0x570C130"))));
        e.put("_PROVENANCE_KEYS",call(e,"set",args(new Part[]{p(e.get("_PROVENANCE_VALUES"))})));
        e.put("_FRAME_KEYS",set(p(s("schema_version")),p(s("status")),p(s("case_kind")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("subject_character_id")),p(s("requested_owner_character_id")),p(s("case")),p(s("notice")),p(s("delivery")),p(s("readiness")),p(s("unavailable_reason")),p(s("provenance"))));
        e.put("_TOP_LEVEL_UNAVAILABLE_REASONS",set(p(s("unsupported_build")),p(s("requires_application_main")),p(s("requires_paused")),p(s("map_not_ready")),p(s("case_not_found")),p(s("case_inconsistent")),p(s("owner_filter_mismatch")),p(s("not_received_self")),p(s("variable_identifier_unavailable")),p(s("variable_context_unavailable")),p(s("state_changed")),p(s("internal_error"))));
        e.put("_FIELD_UNAVAILABLE_REASONS",set(p(s("case_unavailable")),p(s("variable_absent")),p(s("value_type_mismatch")),p(s("value_out_of_range"))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_result_case_snapshot_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_all_available" -> f_all_available(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED),new Param("fields",REQUIRED)),List.of(),null),args));
            case "_all_unavailable" -> f_all_unavailable(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED),new Param("fields",REQUIRED)),List.of(),null),args));
            case "_available" -> f_available(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED)),List.of(),null),args));
            case "_delivery_matrix_ready" -> f_delivery_matrix_ready(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(),List.of(new Param("state",REQUIRED),new Param("grade",REQUIRED),new Param("case_serial",REQUIRED),new Param("method",REQUIRED),new Param("objection",REQUIRED),new Param("settlement",REQUIRED),new Param("appeal",REQUIRED)),null),args));
            case "_exact_object" -> f_exact_object(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("fields",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_integer" -> f_integer(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("minimum",REQUIRED),new Param("maximum",REQUIRED)),null),args));
            case "_positive_int32" -> f_positive_int32(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed_field" -> f_typed_field(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("value_kind",REQUIRED)),null),args));
            case "_typed_group" -> f_typed_group(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("fields",REQUIRED),new Param("kinds",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_value" -> f_value(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_result_case_snapshot_v1" -> fnormalize_native_zhongguo_result_case_snapshot_v1(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            case "validate_result_request_nonce_v1" -> fvalidate_result_request_nonce_v1(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(),null),args));
            case "ZhongguoResultCaseQueryV1" -> new D(new LinkedHashMap<>(bind(GLOBALS,CasesRESULTOriginalNormalizer::dispatch,new Sig(List.of(new Param("owner_character_id",REQUIRED),new Param("request_nonce",REQUIRED)),List.of(),null),args).locals));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_result_case_snapshot_contract.py:291..295
    private static V f_all_available(E e){
        return call(e,"all",args(new Part[]{p(generator(e,q1->and(q1,q3->call(q3,"isinstance",args(new Part[]{p(get(q3.get("group"),q3.get("field"))),p(q3.get("dict"))})),q4->call(q4,"_available",args(new Part[]{p(get(q4.get("group"),q4.get("field")))}))),new Clause(new NameTarget("field"),q2->q2.get("fields"),List.of())))}));
    }
    // Original zhongguo_result_case_snapshot_contract.py:298..302
    private static V f_all_unavailable(E e){
        return call(e,"all",args(new Part[]{p(generator(e,q5->and(q5,q7->call(q7,"isinstance",args(new Part[]{p(get(q7.get("group"),q7.get("field"))),p(q7.get("dict"))})),q8->b(!truth(call(q8,"_available",args(new Part[]{p(get(q8.get("group"),q8.get("field")))}))))),new Clause(new NameTarget("field"),q6->q6.get("fields"),List.of())))}));
    }
    // Original zhongguo_result_case_snapshot_contract.py:281..282
    private static V f_available(E e){
        return compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q9->s("available")));
    }
    // Original zhongguo_result_case_snapshot_contract.py:316..337
    private static V f_delivery_matrix_ready(E e){
        if(truth(compare(e,e.get("grade"),new Comparison(Cmp.NE,q10->n("1"))))) {
            return FALSE;
        }
        return or(e,q11->compare(q11,seq(true,p(q11.get("state")),p(q11.get("method")),p(q11.get("settlement")),p(q11.get("appeal")),p(q11.get("objection"))),new Comparison(Cmp.EQ,q12->seq(true,p(n("1")),p(n("0")),p(n("0")),p(FALSE),p(FALSE)))),q13->compare(q13,seq(true,p(q13.get("state")),p(q13.get("method")),p(q13.get("settlement")),p(q13.get("appeal")),p(q13.get("objection"))),new Comparison(Cmp.EQ,q14->seq(true,p(n("3")),p(n("1")),p(q14.get("case_serial")),p(TRUE),p(FALSE)))),q15->compare(q15,seq(true,p(q15.get("state")),p(q15.get("method")),p(q15.get("settlement")),p(q15.get("appeal")),p(q15.get("objection"))),new Comparison(Cmp.EQ,q16->seq(true,p(n("3")),p(n("2")),p(q16.get("case_serial")),p(TRUE),p(TRUE)))),q17->compare(q17,seq(true,p(q17.get("state")),p(q17.get("method")),p(q17.get("settlement")),p(q17.get("appeal")),p(q17.get("objection"))),new Comparison(Cmp.EQ,q18->seq(true,p(n("2")),p(n("3")),p(n("0")),p(FALSE),p(FALSE)))));
    }
    // Original zhongguo_result_case_snapshot_contract.py:237..242
    private static V f_exact_object(E e){
        if(truth(or(e,q19->b(!truth(call(q19,"isinstance",args(new Part[]{p(q19.get("value")),p(q19.get("dict"))})))),q20->compare(q20,call(q20,"set",args(new Part[]{p(q20.get("value"))})),new Comparison(Cmp.NE,q21->q21.get("fields")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_result_case_snapshot_contract.py:173..182
    private static V f_integer(E e){
        if(truth(or(e,q22->call(q22,"isinstance",args(new Part[]{p(q22.get("value")),p(q22.get("bool"))})),q23->b(!truth(call(q23,"isinstance",args(new Part[]{p(q23.get("value")),p(q23.get("int"))})))),q24->b(!truth(compare(q24,q24.get("minimum"),new Comparison(Cmp.LE,q25->q25.get("value")),new Comparison(Cmp.LE,q26->q26.get("maximum")))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be an integer in range"))));
        }
        return e.get("value");
    }
    // Original zhongguo_result_case_snapshot_contract.py:163..170
    private static V f_positive_int32(E e){
        if(truth(or(e,q27->call(q27,"isinstance",args(new Part[]{p(q27.get("value")),p(q27.get("bool"))})),q28->b(!truth(call(q28,"isinstance",args(new Part[]{p(q28.get("value")),p(q28.get("int"))})))),q29->b(!truth(compare(q29,n("1"),new Comparison(Cmp.LE,q30->q30.get("value")),new Comparison(Cmp.LE,q31->binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be a positive signed int32"))));
        }
        return e.get("value");
    }
    // Original zhongguo_result_case_snapshot_contract.py:245..265
    private static V f_typed_field(E e){
        assign(e,new NameTarget("field"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_FIELD_KEYS")),p(e.get("name"))})));
        assign(e,new NameTarget("status"),method(e.get("field"),"get",args(new Part[]{p(s("status"))})));
        assign(e,new NameTarget("raw"),method(e.get("field"),"get",args(new Part[]{p(s("value"))})));
        assign(e,new NameTarget("reason"),method(e.get("field"),"get",args(new Part[]{p(s("unavailable_reason"))})));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q32->s("unavailable"))))) {
            if(truth(or(e,q33->compare(q33,q33.get("raw"),new Comparison(Cmp.IS_NOT,q34->NONE)),q35->compare(q35,q35.get("reason"),new Comparison(Cmp.NOT_IN,q36->q36.get("_FIELD_UNAVAILABLE_REASONS")))))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid typed unavailable value"))));
            }
            return call(e,"dict",args(new Part[]{p(e.get("field"))}));
        }
        if(truth(or(e,q37->compare(q37,q37.get("status"),new Comparison(Cmp.NE,q38->s("available"))),q39->compare(q39,q39.get("reason"),new Comparison(Cmp.IS_NOT,q40->NONE))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid availability status"))));
        }
        if(truth(compare(e,e.get("value_kind"),new Comparison(Cmp.EQ,q41->s("int"))))) {
            call(e,"_integer",args(new Part[]{p(e.get("raw")),p(e.get("name"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
        } else {
            if(truth(compare(e,e.get("value_kind"),new Comparison(Cmp.EQ,q42->s("bool"))))) {
                if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(e.get("raw")),p(e.get("bool"))})))))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(".value must be boolean"))));
                }
            } else {
                throw new AssertionError(py(e.get("value_kind")));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_result_case_snapshot_contract.py:268..278
    private static V f_typed_group(E e){
        assign(e,new NameTarget("group"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("fields")),p(e.get("name"))})));
        return dictFrom(iter(generator(e,q43->seq(true,p(q43.get("field")),p(call(q43,"_typed_field",args(new Part[]{p(get(q43.get("group"),q43.get("field"))),p(joined(s(py(q43.get("name"))),s("."),s(py(q43.get("field")))))},new Kw("value_kind",q43.get("kind")))))),new Clause(new TupleTarget(List.of(new NameTarget("field"),new NameTarget("kind"))),q44->method(q44.get("kinds"),"items",args(new Part[]{})),List.of()))));
    }
    // Original zhongguo_result_case_snapshot_contract.py:285..288
    private static V f_value(E e){
        if(truth(b(!truth(call(e,"_available",args(new Part[]{p(e.get("field"))})))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be available"))));
        }
        return get(e.get("field"),s("value"));
    }
    // Original zhongguo_result_case_snapshot_contract.py:340..596
    private static V fnormalize_native_zhongguo_result_case_snapshot_v1(E e){
        assign(e,new NameTarget("expected_query"),call(e,"ZhongguoResultCaseQueryV1",args(new Part[]{},new Kw("owner_character_id",call(e,"_positive_int32",args(new Part[]{p(attribute(e.get("expected_query"),"owner_character_id")),p(s("expected_query.owner_character_id"))}))),new Kw("request_nonce",call(e,"validate_result_request_nonce_v1",args(new Part[]{p(attribute(e.get("expected_query"),"request_nonce"))}))))));
        assign(e,new NameTarget("expected_snapshot_revision"),call(e,"_integer",args(new Part[]{p(e.get("expected_snapshot_revision")),p(s("expected_snapshot_revision"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1"))))));
        assign(e,new NameTarget("expected_date_raw"),call(e,"_integer",args(new Part[]{p(e.get("expected_date_raw")),p(s("expected_date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))));
        assign(e,new NameTarget("expected_player_character_id"),call(e,"_positive_int32",args(new Part[]{p(e.get("expected_player_character_id")),p(s("expected_player_character_id"))})));
        assign(e,new NameTarget("frame"),call(e,"_exact_object",args(new Part[]{p(e.get("value")),p(e.get("_FRAME_KEYS")),p(s("zhongguo_result_case_snapshot"))})));
        if(truth(compare(e,method(e.get("frame"),"get",args(new Part[]{p(s("schema_version"))})),new Comparison(Cmp.NE,q45->n("1"))))) {
            throw new Rejected(py(s("schema_version must be 1")));
        }
        if(truth(compare(e,method(e.get("frame"),"get",args(new Part[]{p(s("case_kind"))})),new Comparison(Cmp.NE,q46->q46.get("ZHONGGUO_RESULT_CASE_KIND_V1"))))) {
            throw new Rejected(py(s("case_kind binding changed")));
        }
        if(truth(compare(e,method(e.get("frame"),"get",args(new Part[]{p(s("request_nonce"))})),new Comparison(Cmp.NE,q47->attribute(q47.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("request_nonce binding changed")));
        }
        if(truth(compare(e,call(e,"_integer",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("snapshot_revision"))}))),p(s("snapshot_revision"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1"))))),new Comparison(Cmp.NE,q48->q48.get("expected_snapshot_revision"))))) {
            throw new Rejected(py(s("snapshot revision binding changed")));
        }
        if(truth(compare(e,call(e,"_integer",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("date_raw"))}))),p(s("date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))),new Comparison(Cmp.NE,q49->q49.get("expected_date_raw"))))) {
            throw new Rejected(py(s("date binding changed")));
        }
        if(truth(compare(e,method(e.get("frame"),"get",args(new Part[]{p(s("paused"))})),new Comparison(Cmp.IS_NOT,q50->TRUE)))) {
            throw new Rejected(py(s("result-case query is not paused")));
        }
        assign(e,new NameTarget("player"),call(e,"_positive_int32",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("player_character_id"))}))),p(s("player_character_id"))})));
        if(truth(compare(e,e.get("player"),new Comparison(Cmp.NE,q51->q51.get("expected_player_character_id"))))) {
            throw new Rejected(py(s("player identity binding changed")));
        }
        assign(e,new NameTarget("subject"),call(e,"_positive_int32",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("subject_character_id"))}))),p(s("subject_character_id"))})));
        if(truth(compare(e,e.get("subject"),new Comparison(Cmp.NE,q52->q52.get("player"))))) {
            throw new Rejected(py(s("received-self subject is not the played character")));
        }
        assign(e,new NameTarget("requested_owner"),call(e,"_positive_int32",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("requested_owner_character_id"))}))),p(s("requested_owner_character_id"))})));
        if(truth(compare(e,e.get("requested_owner"),new Comparison(Cmp.NE,q53->attribute(q53.get("expected_query"),"owner_character_id"))))) {
            throw new Rejected(py(s("owner filter binding changed")));
        }
        assign(e,new NameTarget("case"),call(e,"_typed_group",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("case"))}))),p(e.get("_CASE_KEYS")),p(dictFrom(iter(generator(e,q54->seq(true,p(q54.get("field")),p(s("int"))),new Clause(new NameTarget("field"),q55->q55.get("_CASE_KEYS"),List.of()))))),p(s("case"))})));
        assign(e,new NameTarget("notice"),call(e,"_typed_group",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("notice"))}))),p(e.get("_NOTICE_KEYS")),p(dictFrom(iter(generator(e,q56->seq(true,p(q56.get("field")),p(s("int"))),new Clause(new NameTarget("field"),q57->q57.get("_NOTICE_KEYS"),List.of()))))),p(s("notice"))})));
        assign(e,new NameTarget("delivery"),call(e,"_typed_group",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("delivery"))}))),p(e.get("_DELIVERY_KEYS")),p(dict(new Item(s("method"),s("int")),new Item(s("objection_recorded"),s("bool")),new Item(s("settlement_posted_serial"),s("int")),new Item(s("appeal_open"),s("bool")))),p(s("delivery"))})));
        assign(e,new NameTarget("readiness_raw"),call(e,"_exact_object",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("readiness"))}))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        assign(e,new NameTarget("readiness"),dict());
        for(V q58:iter(e.get("_READINESS_KEYS"))) {
            assign(e,new NameTarget("key"),q58);
            assign(e,new NameTarget("flag"),method(e.get("readiness_raw"),"get",args(new Part[]{p(e.get("key"))})));
            if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(e.get("flag")),p(e.get("bool"))})))))) {
                throw new Rejected(py(joined(s("readiness."),s(py(e.get("key"))),s(" must be boolean"))));
            }
            put(e.get("readiness"),e.get("key"),e.get("flag"));
        }
        assign(e,new NameTarget("expected_ready"),call(e,"all",args(new Part[]{p(generator(e,q59->get(q59.get("readiness"),q59.get("key")),new Clause(new NameTarget("key"),q60->q60.get("_READINESS_KEYS"),List.of(q60->compare(q60,q60.get("key"),new Comparison(Cmp.NE,q61->s("ready")))))))})));
        if(truth(compare(e,get(e.get("readiness"),s("ready")),new Comparison(Cmp.IS_NOT,q62->q62.get("expected_ready"))))) {
            throw new Rejected(py(s("readiness.ready does not equal the component gate")));
        }
        assign(e,new NameTarget("provenance"),call(e,"_exact_object",args(new Part[]{p(method(e.get("frame"),"get",args(new Part[]{p(s("provenance"))}))),p(e.get("_PROVENANCE_KEYS")),p(s("provenance"))})));
        if(truth(call(e,"any",args(new Part[]{p(generator(e,q63->compare(q63,method(q63.get("provenance"),"get",args(new Part[]{p(q63.get("key"))})),new Comparison(Cmp.NE,q65->q65.get("expected"))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("expected"))),q64->method(q64.get("_PROVENANCE_VALUES"),"items",args(new Part[]{})),List.of())))})))) {
            throw new Rejected(py(s("provenance does not match the frozen exact build")));
        }
        assign(e,new NameTarget("status"),method(e.get("frame"),"get",args(new Part[]{p(s("status"))})));
        assign(e,new NameTarget("reason"),method(e.get("frame"),"get",args(new Part[]{p(s("unavailable_reason"))})));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q66->s("available"))))) {
            if(truth(or(e,q67->compare(q67,q67.get("reason"),new Comparison(Cmp.IS_NOT,q68->NONE)),q69->b(!truth(call(q69,"all",args(new Part[]{p(generator(q69,q70->get(q70.get("readiness"),q70.get("key")),new Clause(new NameTarget("key"),q71->seq(true,p(s("player_subject_binding_ready")),p(s("owner_binding_ready")),p(s("case_identity_ready"))),List.of())))}))))))) {
                throw new Rejected(py(s("available frame lacks its identity bindings")));
            }
        } else {
            if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q72->s("unavailable"))))) {
                if(truth(or(e,q73->compare(q73,q73.get("reason"),new Comparison(Cmp.NOT_IN,q74->q74.get("_TOP_LEVEL_UNAVAILABLE_REASONS"))),q75->get(q75.get("readiness"),s("ready"))))) {
                    throw new Rejected(py(s("unavailable frame has an invalid reason/gate")));
                }
            } else {
                throw new Rejected(py(s("status must be available or unavailable")));
            }
        }
        assign(e,new NameTarget("case_ready"),call(e,"_all_available",args(new Part[]{p(e.get("case")),p(e.get("_CASE_KEYS"))})));
        if(truth(compare(e,get(e.get("readiness"),s("case_identity_ready")),new Comparison(Cmp.IS_NOT,q76->q76.get("case_ready"))))) {
            throw new Rejected(py(s("case identity readiness disagrees with typed fields")));
        }
        assign(e,new NameTarget("case_values"),dict());
        if(truth(e.get("case_ready"))) {
            assign(e,new NameTarget("case_values"),dictFrom(iter(generator(e,q77->seq(true,p(q77.get("field")),p(call(q77,"_integer",args(new Part[]{p(call(q77,"_value",args(new Part[]{p(get(q77.get("case"),q77.get("field"))),p(joined(s("case."),s(py(q77.get("field")))))}))),p(joined(s("case."),s(py(q77.get("field")))))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1"))))))),new Clause(new NameTarget("field"),q78->q78.get("_CASE_KEYS"),List.of())))));
            if(truth(or(e,q79->compare(q79,call(q79,"_positive_int32",args(new Part[]{p(get(q79.get("case_values"),s("owner_character_id"))),p(s("case.owner_character_id"))})),new Comparison(Cmp.NE,q80->attribute(q80.get("expected_query"),"owner_character_id"))),q81->compare(q81,get(q81.get("case_values"),s("owner_character_id")),new Comparison(Cmp.EQ,q82->q82.get("player"))),q83->compare(q83,call(q83,"_positive_int32",args(new Part[]{p(get(q83.get("case_values"),s("subject_character_id"))),p(s("case.subject_character_id"))})),new Comparison(Cmp.NE,q84->q84.get("player"))),q85->compare(q85,get(q85.get("case_values"),s("cycle_serial")),new Comparison(Cmp.LT,q86->n("1"))),q87->b(!truth(compare(q87,n("1"),new Comparison(Cmp.LE,q88->get(q88.get("case_values"),s("case_serial"))),new Comparison(Cmp.LE,q89->n("999999"))))),q90->b(!truth(compare(q90,n("1"),new Comparison(Cmp.LE,q91->get(q91.get("case_values"),s("state"))),new Comparison(Cmp.LE,q92->n("5"))))),q93->b(!truth(compare(q93,n("1"),new Comparison(Cmp.LE,q94->get(q94.get("case_values"),s("grade"))),new Comparison(Cmp.LE,q95->n("3")))))))) {
                throw new Rejected(py(s("available case identity violates received-self")));
            }
        }
        if(truth(compare(e,get(e.get("readiness"),s("player_subject_binding_ready")),new Comparison(Cmp.IS_NOT,q96->q96.get("case_ready"))))) {
            throw new Rejected(py(s("player-subject readiness disagrees with case")));
        }
        if(truth(compare(e,get(e.get("readiness"),s("owner_binding_ready")),new Comparison(Cmp.IS_NOT,q97->q97.get("case_ready"))))) {
            throw new Rejected(py(s("owner readiness disagrees with case")));
        }
        assign(e,new NameTarget("notice_ready"),call(e,"_all_available",args(new Part[]{p(e.get("notice")),p(e.get("_NOTICE_KEYS"))})));
        if(truth(e.get("notice_ready"))) {
            assign(e,new NameTarget("notice_values"),dictFrom(iter(generator(e,q98->seq(true,p(q98.get("field")),p(call(q98,"_integer",args(new Part[]{p(call(q98,"_value",args(new Part[]{p(get(q98.get("notice"),q98.get("field"))),p(joined(s("notice."),s(py(q98.get("field")))))}))),p(joined(s("notice."),s(py(q98.get("field")))))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1"))))))),new Clause(new NameTarget("field"),q99->q99.get("_NOTICE_KEYS"),List.of())))));
            assign(e,new NameTarget("notice_ready"),and(e,q100->compare(q100,n("1"),new Comparison(Cmp.LE,q101->get(q101.get("notice_values"),s("absolute_grade"))),new Comparison(Cmp.LE,q102->n("3"))),q103->compare(q103,get(q103.get("notice_values"),s("rank_frozen")),new Comparison(Cmp.GE,q104->n("1"))),q105->compare(q105,get(q105.get("notice_values"),s("cohort_n_frozen")),new Comparison(Cmp.GE,q106->n("1"))),q107->compare(q107,get(q107.get("notice_values"),s("rank_frozen")),new Comparison(Cmp.LE,q108->get(q108.get("notice_values"),s("cohort_n_frozen"))))));
        }
        if(truth(compare(e,get(e.get("readiness"),s("notice_facts_ready")),new Comparison(Cmp.IS_NOT,q109->q109.get("notice_ready"))))) {
            throw new Rejected(py(s("notice readiness disagrees with frozen facts")));
        }
        assign(e,new NameTarget("delivery_ready"),call(e,"_all_available",args(new Part[]{p(e.get("delivery")),p(e.get("_DELIVERY_KEYS"))})));
        if(truth(e.get("delivery_ready"))) {
            assign(e,new NameTarget("method"),call(e,"_integer",args(new Part[]{p(call(e,"_value",args(new Part[]{p(get(e.get("delivery"),s("method"))),p(s("delivery.method"))}))),p(s("delivery.method"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1"))))));
            assign(e,new NameTarget("settlement"),call(e,"_integer",args(new Part[]{p(call(e,"_value",args(new Part[]{p(get(e.get("delivery"),s("settlement_posted_serial"))),p(s("delivery.settlement_posted_serial"))}))),p(s("delivery.settlement_posted_serial"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1"))))));
            assign(e,new NameTarget("objection"),call(e,"_value",args(new Part[]{p(get(e.get("delivery"),s("objection_recorded"))),p(s("delivery.objection_recorded"))})));
            assign(e,new NameTarget("appeal"),call(e,"_value",args(new Part[]{p(get(e.get("delivery"),s("appeal_open"))),p(s("delivery.appeal_open"))})));
            if(!truth(and(e,q110->call(q110,"isinstance",args(new Part[]{p(q110.get("objection")),p(q110.get("bool"))})),q111->call(q111,"isinstance",args(new Part[]{p(q111.get("appeal")),p(q111.get("bool"))})))))throw new AssertionError(py(s("original invariant")));
            assign(e,new NameTarget("delivery_ready"),and(e,q112->q112.get("case_ready"),q113->compare(q113,n("0"),new Comparison(Cmp.LE,q114->q114.get("method")),new Comparison(Cmp.LE,q115->n("3"))),q116->compare(q116,n("0"),new Comparison(Cmp.LE,q117->q117.get("settlement")),new Comparison(Cmp.LE,q118->n("999999"))),q119->call(q119,"_delivery_matrix_ready",args(new Part[]{},new Kw("state",get(q119.get("case_values"),s("state"))),new Kw("grade",get(q119.get("case_values"),s("grade"))),new Kw("case_serial",get(q119.get("case_values"),s("case_serial"))),new Kw("method",q119.get("method")),new Kw("objection",q119.get("objection")),new Kw("settlement",q119.get("settlement")),new Kw("appeal",q119.get("appeal"))))));
        }
        if(truth(compare(e,get(e.get("readiness"),s("delivery_state_ready")),new Comparison(Cmp.IS_NOT,q120->q120.get("delivery_ready"))))) {
            throw new Rejected(py(s("delivery readiness disagrees with product state")));
        }
        if(truth(and(e,q121->compare(q121,q121.get("status"),new Comparison(Cmp.EQ,q122->s("unavailable"))),q123->b(!truth(and(q123,q124->call(q124,"_all_unavailable",args(new Part[]{p(q124.get("case")),p(q124.get("_CASE_KEYS"))})),q125->call(q125,"_all_unavailable",args(new Part[]{p(q125.get("notice")),p(q125.get("_NOTICE_KEYS"))})),q126->call(q126,"_all_unavailable",args(new Part[]{p(q126.get("delivery")),p(q126.get("_DELIVERY_KEYS"))})),q127->b(!truth(get(q127.get("readiness"),s("player_subject_binding_ready")))),q128->b(!truth(get(q128.get("readiness"),s("owner_binding_ready")))),q129->b(!truth(get(q129.get("readiness"),s("case_identity_ready")))),q130->b(!truth(get(q130.get("readiness"),s("notice_facts_ready")))),q131->b(!truth(get(q131.get("readiness"),s("delivery_state_ready")))))))))) {
            throw new Rejected(py(s("unavailable result-case leaks semantic fields")));
        }
        return dict(new Expansion(e.get("frame")),new Item(s("case"),e.get("case")),new Item(s("notice"),e.get("notice")),new Item(s("delivery"),e.get("delivery")),new Item(s("readiness"),e.get("readiness")),new Item(s("provenance"),call(e,"dict",args(new Part[]{p(e.get("provenance"))}))));
    }
    // Original zhongguo_result_case_snapshot_contract.py:185..190
    private static V fvalidate_result_request_nonce_v1(E e){
        if(truth(or(e,q132->b(!truth(call(q132,"isinstance",args(new Part[]{p(q132.get("value")),p(q132.get("str"))})))),q133->compare(q133,method(q133.get("_NONCE_RE"),"fullmatch",args(new Part[]{p(q133.get("value"))})),new Comparison(Cmp.IS,q134->NONE))))) {
            throw new Rejected(py(s("request_nonce must be 1-64 ASCII token characters")));
        }
        return e.get("value");
    }
}
