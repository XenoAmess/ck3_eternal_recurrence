package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_incident_snapshot_contract.py; original SHA-256 fb795fd95bcc927b6a4d50aa885c284b9e33d99a9d0896306b572843c06effcf. No Python runtime. */
final class CasesINCIDENTOriginalNormalizer {
    private CasesINCIDENTOriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesINCIDENTOriginalNormalizer::dispatch);
        e.put("ZHONGGUO_INCIDENT_KIND_V1",s("zhongguo.incident.subject-self"));
        e.put("ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION",s("1.19.0.6"));
        e.put("ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256",s("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"));
        e.put("ZHONGGUO_INCIDENT_SNAPSHOT_V1_BACKEND_ID",s("ck3-1.19.0.6-native-zhongguo-incident-snapshot-v1"));
        e.put("ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID",s("xar-autoplayer-zhongguo-incident-snapshot-v1"));
        e.put("ZHONGGUO_INCIDENT_SNAPSHOT_V1_ALLOWLIST_ID",s("zg361-incident-terminal-x-y-z-v1"));
        e.put("_PROFILES",call(e,"frozenset",args(new Part[]{p(set(p(s("x")),p(s("y")),p(s("z"))))})));
        e.put("_NONCE_RE",regex(text(s("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\\Z"))));
        e.put("_TYPED_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_PROBE_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("probe_serial")),p(s("result")),p(s("source_kind")),p(s("consequence_kind"))));
        e.put("_RESOURCE_KEYS",set(p(s("subject_personal_gold_q100000")),p(s("manager_treasury_q100000")),p(s("capital_control_q100000"))));
        e.put("_NA_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("reason")),p(s("probe_serial")),p(s("receipt_serial")),p(s("applicable")),p(s("kpi_staged"))));
        e.put("_INCIDENT_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("revision")),p(s("incident_serial")),p(s("source_kind")),p(s("consequence_kind")),p(s("final_score")),p(s("applicable")),p(s("kpi_staged"))));
        e.put("_TERMINAL_KEYS",set(p(s("kind")),p(s("na")),p(s("incident"))));
        e.put("_KPI_VALUE_KEYS",set(p(s("pending")),p(s("consumed")),p(s("owner_character_id")),p(s("subject_character_id")),p(s("origin_cycle")),p(s("due_cycle")),p(s("due_offset")),p(s("case_serial")),p(s("state")),p(s("score")),p(s("incident_serial")),p(s("source_kind")),p(s("consequence_kind")),p(s("receipt_serial")),p(s("consumed_owner_character_id")),p(s("consumed_subject_character_id")),p(s("consumed_origin_cycle")),p(s("consumed_due_cycle")),p(s("consumed_cycle")),p(s("consumed_case_serial")),p(s("consumed_score")),p(s("consumed_incident_serial"))));
        e.put("_KPI_KEYS",binary(Op.OR,e.get("_KPI_VALUE_KEYS"),set(p(s("disposition")))));
        e.put("_READINESS_KEYS",set(p(s("player_subject_binding_ready")),p(s("owner_binding_ready")),p(s("profile_binding_ready")),p(s("probe_ready")),p(s("terminal_ready")),p(s("resource_snapshot_ready")),p(s("kpi_state_ready")),p(s("same_frame_ready")),p(s("ready"))));
        e.put("_PROVENANCE_VALUES",dict(new Item(s("game_version"),e.get("ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION")),new Item(s("executable_sha256"),e.get("ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256")),new Item(s("backend_id"),e.get("ZHONGGUO_INCIDENT_SNAPSHOT_V1_BACKEND_ID")),new Item(s("consumer_id"),e.get("ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID")),new Item(s("allowlist_id"),e.get("ZHONGGUO_INCIDENT_SNAPSHOT_V1_ALLOWLIST_ID")),new Item(s("variable_context_for_scope_rva"),s("0x3329A40")),new Item(s("variable_identifier_table_rva"),s("0x3B971A0")),new Item(s("variable_identifier_lookup_rva"),s("0x3B97020")),new Item(s("variable_identifier_name_rva"),s("0x3B97090")),new Item(s("character_storage_slot_rva"),s("0x570C130")),new Item(s("manager_treasury_source"),s("zg361_ip_probe_manager_treasury"))));
        e.put("_FRAME_KEYS",set(p(s("schema_version")),p(s("status")),p(s("case_kind")),p(s("profile")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("subject_character_id")),p(s("requested_owner_character_id")),p(s("probe")),p(s("resources")),p(s("terminal")),p(s("kpi")),p(s("readiness")),p(s("unavailable_reason")),p(s("provenance"))));
        e.put("_TOP_REASONS",set(p(s("unsupported_build")),p(s("requires_application_main")),p(s("requires_paused")),p(s("map_not_ready")),p(s("incident_not_found")),p(s("incident_inconsistent")),p(s("owner_filter_mismatch")),p(s("not_received_self")),p(s("variable_identifier_unavailable")),p(s("variable_context_unavailable")),p(s("state_changed")),p(s("internal_error"))));
        e.put("_FIELD_REASONS",set(p(s("snapshot_unavailable")),p(s("variable_absent")),p(s("value_type_mismatch")),p(s("value_out_of_range")),p(s("terminal_not_selected")),p(s("not_applicable")),p(s("kpi_not_staged")),p(s("not_yet_consumed"))));
        e.put("_SOURCE_CONSEQUENCE",set(p(seq(true,p(n("1")),p(n("1")))),p(seq(true,p(n("3")),p(n("2")))),p(seq(true,p(n("4")),p(n("2")))),p(seq(true,p(n("5")),p(n("3"))))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_incident_snapshot_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_all_available" -> f_all_available(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED)),List.of(),null),args));
            case "_all_unavailable" -> f_all_unavailable(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("group",REQUIRED)),List.of(),null),args));
            case "_available" -> f_available(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED)),List.of(),null),args));
            case "_exact" -> f_exact(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("keys",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_integer" -> f_integer(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("minimum",REQUIRED),new Param("maximum",REQUIRED)),null),args));
            case "_positive_int32" -> f_positive_int32(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed" -> f_typed(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed_group" -> f_typed_group(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("keys",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_validate_kpi" -> f_validate_kpi(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("kpi",REQUIRED)),List.of(new Param("terminal_kind",REQUIRED),new Param("incident",REQUIRED)),null),args));
            case "_value" -> f_value(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("field",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_incident_snapshot_v1" -> fnormalize_native_zhongguo_incident_snapshot_v1(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            case "validate_incident_profile_v1" -> fvalidate_incident_profile_v1(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(),null),args));
            case "validate_incident_request_nonce_v1" -> fvalidate_incident_request_nonce_v1(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(),null),args));
            case "ZhongguoIncidentQueryV1" -> new D(new LinkedHashMap<>(bind(GLOBALS,CasesINCIDENTOriginalNormalizer::dispatch,new Sig(List.of(new Param("owner_character_id",REQUIRED),new Param("profile",REQUIRED),new Param("request_nonce",REQUIRED)),List.of(),null),args).locals));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_incident_snapshot_contract.py:340..341
    private static V f_all_available(E e){
        return call(e,"all",args(new Part[]{p(generator(e,q1->call(q1,"_available",args(new Part[]{p(q1.get("field"))})),new Clause(new NameTarget("field"),q2->method(q2.get("group"),"values",args(new Part[]{})),List.of())))}));
    }
    // Original zhongguo_incident_snapshot_contract.py:344..345
    private static V f_all_unavailable(E e){
        return call(e,"all",args(new Part[]{p(generator(e,q3->b(!truth(call(q3,"_available",args(new Part[]{p(q3.get("field"))})))),new Clause(new NameTarget("field"),q4->method(q4.get("group"),"values",args(new Part[]{})),List.of())))}));
    }
    // Original zhongguo_incident_snapshot_contract.py:328..329
    private static V f_available(E e){
        return compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q5->s("available")));
    }
    // Original zhongguo_incident_snapshot_contract.py:219..222
    private static V f_exact(E e){
        if(truth(or(e,q6->b(!truth(call(q6,"isinstance",args(new Part[]{p(q6.get("value")),p(q6.get("dict"))})))),q7->compare(q7,call(q7,"set",args(new Part[]{p(q7.get("value"))})),new Comparison(Cmp.NE,q8->q8.get("keys")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_incident_snapshot_contract.py:225..234
    private static V f_integer(E e){
        if(truth(or(e,q9->call(q9,"isinstance",args(new Part[]{p(q9.get("value")),p(q9.get("bool"))})),q10->b(!truth(call(q10,"isinstance",args(new Part[]{p(q10.get("value")),p(q10.get("int"))})))),q11->b(!truth(compare(q11,q11.get("minimum"),new Comparison(Cmp.LE,q12->q12.get("value")),new Comparison(Cmp.LE,q13->q13.get("maximum")))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be an integer in range"))));
        }
        return e.get("value");
    }
    // Original zhongguo_incident_snapshot_contract.py:237..238
    private static V f_positive_int32(E e){
        return call(e,"_integer",args(new Part[]{p(e.get("value")),p(e.get("name"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1")))));
    }
    // Original zhongguo_incident_snapshot_contract.py:304..318
    private static V f_typed(E e){
        assign(e,new NameTarget("field"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_KEYS")),p(e.get("name"))})));
        assign(e,new NameTarget("status"),get(e.get("field"),s("status")));
        assign(e,new NameTarget("raw"),get(e.get("field"),s("value")));
        assign(e,new NameTarget("reason"),get(e.get("field"),s("unavailable_reason")));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q14->s("unavailable"))))) {
            if(truth(or(e,q15->compare(q15,q15.get("raw"),new Comparison(Cmp.IS_NOT,q16->NONE)),q17->compare(q17,q17.get("reason"),new Comparison(Cmp.NOT_IN,q18->q18.get("_FIELD_REASONS")))))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid unavailable value"))));
            }
        } else {
            if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q19->s("available"))))) {
                if(truth(compare(e,e.get("reason"),new Comparison(Cmp.IS_NOT,q20->NONE)))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(" available value has a reason"))));
                }
                call(e,"_integer",args(new Part[]{p(e.get("raw")),p(e.get("name"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
            } else {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid status"))));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_incident_snapshot_contract.py:321..325
    private static V f_typed_group(E e){
        assign(e,new NameTarget("group"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("keys")),p(e.get("name"))})));
        return dictFrom(iter(generator(e,q21->seq(true,p(q21.get("key")),p(call(q21,"_typed",args(new Part[]{p(get(q21.get("group"),q21.get("key"))),p(joined(s(py(q21.get("name"))),s("."),s(py(q21.get("key")))))})))),new Clause(new NameTarget("key"),q22->q22.get("keys"),List.of()))));
    }
    // Original zhongguo_incident_snapshot_contract.py:348..415
    private static V f_validate_kpi(E e){
        assign(e,new NameTarget("disposition"),get(e.get("kpi"),s("disposition")));
        assign(e,new NameTarget("values"),dictFrom(iter(generator(e,q23->seq(true,p(q23.get("key")),p(get(q23.get("kpi"),q23.get("key")))),new Clause(new NameTarget("key"),q24->q24.get("_KPI_VALUE_KEYS"),List.of())))));
        if(!truth(call(e,"all",args(new Part[]{p(generator(e,q25->call(q25,"isinstance",args(new Part[]{p(q25.get("field")),p(q25.get("dict"))})),new Clause(new NameTarget("field"),q26->method(q26.get("values"),"values",args(new Part[]{})),List.of())))}))))throw new AssertionError(py(s("original invariant")));
        assign(e,new NameTarget("typed_values"),e.get("values"));
        if(truth(compare(e,e.get("terminal_kind"),new Comparison(Cmp.EQ,q27->s("na"))))) {
            if(truth(or(e,q28->compare(q28,q28.get("disposition"),new Comparison(Cmp.NE,q29->s("not_staged"))),q30->b(!truth(call(q30,"_all_unavailable",args(new Part[]{p(q30.get("typed_values"))}))))))) {
                throw new Rejected(py(s("N/A must have an exact not-staged KPI tuple")));
            }
            return TRUE;
        }
        if(truth(compare(e,e.get("disposition"),new Comparison(Cmp.EQ,q31->s("unavailable"))))) {
            if(truth(b(!truth(call(e,"_all_unavailable",args(new Part[]{p(e.get("typed_values"))})))))) {
                throw new Rejected(py(s("unavailable KPI disposition leaks values")));
            }
            return FALSE;
        }
        if(truth(or(e,q32->compare(q32,q32.get("disposition"),new Comparison(Cmp.NOT_IN,q33->set(p(s("pending")),p(s("consumed"))))),q34->compare(q34,q34.get("incident"),new Comparison(Cmp.IS,q35->NONE))))) {
            throw new Rejected(py(s("incident KPI disposition is invalid")));
        }
        assign(e,new NameTarget("base"),call(e,"set",args(new Part[]{p(generator(e,q36->q36.get("key"),new Clause(new NameTarget("key"),q37->q37.get("_KPI_VALUE_KEYS"),List.of(q37->and(q37,q38->b(!truth(method(q38.get("key"),"startswith",args(new Part[]{p(s("consumed_"))})))),q39->compare(q39,q39.get("key"),new Comparison(Cmp.NE,q40->s("receipt_serial"))))))))})));
        if(truth(b(!truth(call(e,"all",args(new Part[]{p(generator(e,q41->call(q41,"_available",args(new Part[]{p(get(q41.get("typed_values"),q41.get("key")))})),new Clause(new NameTarget("key"),q42->q42.get("base"),List.of())))})))))) {
            throw new Rejected(py(s("staged KPI base tuple is incomplete")));
        }
        assign(e,new NameTarget("iv"),dictFrom(iter(generator(e,q43->seq(true,p(q43.get("key")),p(call(q43,"_value",args(new Part[]{p(q43.get("field")),p(joined(s("incident."),s(py(q43.get("key")))))})))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("field"))),q44->method(q44.get("incident"),"items",args(new Part[]{})),List.of())))));
        assign(e,new NameTarget("kv"),dictFrom(iter(generator(e,q45->seq(true,p(q45.get("key")),p(call(q45,"_value",args(new Part[]{p(get(q45.get("typed_values"),q45.get("key"))),p(joined(s("kpi."),s(py(q45.get("key")))))})))),new Clause(new NameTarget("key"),q46->q46.get("base"),List.of())))));
        if(truth(or(e,q47->compare(q47,get(q47.get("kv"),s("owner_character_id")),new Comparison(Cmp.NE,q48->get(q48.get("iv"),s("owner_character_id")))),q49->compare(q49,get(q49.get("kv"),s("subject_character_id")),new Comparison(Cmp.NE,q50->get(q50.get("iv"),s("subject_character_id")))),q51->compare(q51,get(q51.get("kv"),s("origin_cycle")),new Comparison(Cmp.NE,q52->get(q52.get("iv"),s("cycle_serial")))),q53->compare(q53,get(q53.get("kv"),s("due_cycle")),new Comparison(Cmp.NE,q54->binary(Op.ADD,get(q54.get("kv"),s("origin_cycle")),n("1")))),q55->compare(q55,get(q55.get("kv"),s("due_offset")),new Comparison(Cmp.NE,q56->n("1"))),q57->compare(q57,get(q57.get("kv"),s("case_serial")),new Comparison(Cmp.NE,q58->get(q58.get("iv"),s("case_serial")))),q59->compare(q59,get(q59.get("kv"),s("state")),new Comparison(Cmp.NE,q60->get(q60.get("iv"),s("state")))),q61->compare(q61,get(q61.get("kv"),s("score")),new Comparison(Cmp.NE,q62->get(q62.get("iv"),s("final_score")))),q63->compare(q63,get(q63.get("kv"),s("incident_serial")),new Comparison(Cmp.NE,q64->get(q64.get("iv"),s("incident_serial")))),q65->compare(q65,get(q65.get("kv"),s("source_kind")),new Comparison(Cmp.NE,q66->get(q66.get("iv"),s("source_kind")))),q67->compare(q67,get(q67.get("kv"),s("consequence_kind")),new Comparison(Cmp.NE,q68->get(q68.get("iv"),s("consequence_kind"))))))) {
            throw new Rejected(py(s("KPI tuple does not join the incident terminal")));
        }
        assign(e,new NameTarget("receipt"),binary(Op.SUB,e.get("_KPI_VALUE_KEYS"),e.get("base")));
        if(truth(compare(e,e.get("disposition"),new Comparison(Cmp.EQ,q69->s("pending"))))) {
            if(truth(or(e,q70->compare(q70,get(q70.get("kv"),s("pending")),new Comparison(Cmp.NE,q71->n("1"))),q72->compare(q72,get(q72.get("kv"),s("consumed")),new Comparison(Cmp.NE,q73->n("0")))))) {
                throw new Rejected(py(s("pending KPI bits are invalid")));
            }
            if(truth(b(!truth(call(e,"all",args(new Part[]{p(generator(e,q74->b(!truth(call(q74,"_available",args(new Part[]{p(get(q74.get("typed_values"),q74.get("key")))})))),new Clause(new NameTarget("key"),q75->q75.get("receipt"),List.of())))})))))) {
                throw new Rejected(py(s("pending KPI leaks a consumed receipt")));
            }
            return TRUE;
        }
        if(truth(or(e,q76->compare(q76,get(q76.get("kv"),s("pending")),new Comparison(Cmp.NE,q77->n("0"))),q78->compare(q78,get(q78.get("kv"),s("consumed")),new Comparison(Cmp.NE,q79->n("1")))))) {
            throw new Rejected(py(s("consumed KPI bits are invalid")));
        }
        if(truth(b(!truth(call(e,"all",args(new Part[]{p(generator(e,q80->call(q80,"_available",args(new Part[]{p(get(q80.get("typed_values"),q80.get("key")))})),new Clause(new NameTarget("key"),q81->q81.get("receipt"),List.of())))})))))) {
            throw new Rejected(py(s("consumed KPI receipt is incomplete")));
        }
        assign(e,new NameTarget("rv"),dictFrom(iter(generator(e,q82->seq(true,p(q82.get("key")),p(call(q82,"_value",args(new Part[]{p(get(q82.get("typed_values"),q82.get("key"))),p(joined(s("kpi."),s(py(q82.get("key")))))})))),new Clause(new NameTarget("key"),q83->q83.get("receipt"),List.of())))));
        if(truth(or(e,q84->compare(q84,get(q84.get("rv"),s("receipt_serial")),new Comparison(Cmp.LT,q85->n("1"))),q86->compare(q86,get(q86.get("rv"),s("consumed_owner_character_id")),new Comparison(Cmp.NE,q87->get(q87.get("kv"),s("owner_character_id")))),q88->compare(q88,get(q88.get("rv"),s("consumed_subject_character_id")),new Comparison(Cmp.NE,q89->get(q89.get("kv"),s("subject_character_id")))),q90->compare(q90,get(q90.get("rv"),s("consumed_origin_cycle")),new Comparison(Cmp.NE,q91->get(q91.get("kv"),s("origin_cycle")))),q92->compare(q92,get(q92.get("rv"),s("consumed_due_cycle")),new Comparison(Cmp.NE,q93->get(q93.get("kv"),s("due_cycle")))),q94->compare(q94,get(q94.get("rv"),s("consumed_cycle")),new Comparison(Cmp.LT,q95->get(q95.get("kv"),s("due_cycle")))),q96->compare(q96,get(q96.get("rv"),s("consumed_case_serial")),new Comparison(Cmp.NE,q97->get(q97.get("kv"),s("case_serial")))),q98->compare(q98,get(q98.get("rv"),s("consumed_score")),new Comparison(Cmp.NE,q99->get(q99.get("kv"),s("score")))),q100->compare(q100,get(q100.get("rv"),s("consumed_incident_serial")),new Comparison(Cmp.NE,q101->get(q101.get("kv"),s("incident_serial"))))))) {
            throw new Rejected(py(s("consumed KPI receipt does not join its tuple")));
        }
        return TRUE;
    }
    // Original zhongguo_incident_snapshot_contract.py:332..337
    private static V f_value(E e){
        if(truth(b(!truth(call(e,"_available",args(new Part[]{p(e.get("field"))})))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be available"))));
        }
        return call(e,"_integer",args(new Part[]{p(get(e.get("field"),s("value"))),p(e.get("name"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("63")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))));
    }
    // Original zhongguo_incident_snapshot_contract.py:418..623
    private static V fnormalize_native_zhongguo_incident_snapshot_v1(E e){
        assign(e,new NameTarget("expected_query"),call(e,"ZhongguoIncidentQueryV1",args(new Part[]{p(call(e,"_positive_int32",args(new Part[]{p(attribute(e.get("expected_query"),"owner_character_id")),p(s("expected owner"))}))),p(call(e,"validate_incident_profile_v1",args(new Part[]{p(attribute(e.get("expected_query"),"profile"))}))),p(call(e,"validate_incident_request_nonce_v1",args(new Part[]{p(attribute(e.get("expected_query"),"request_nonce"))})))})));
        assign(e,new NameTarget("expected_snapshot_revision"),call(e,"_integer",args(new Part[]{p(e.get("expected_snapshot_revision")),p(s("expected_snapshot_revision"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1"))))));
        assign(e,new NameTarget("expected_date_raw"),call(e,"_integer",args(new Part[]{p(e.get("expected_date_raw")),p(s("expected_date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))));
        assign(e,new NameTarget("expected_player_character_id"),call(e,"_positive_int32",args(new Part[]{p(e.get("expected_player_character_id")),p(s("expected_player_character_id"))})));
        assign(e,new NameTarget("frame"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_FRAME_KEYS")),p(s("zhongguo_incident_snapshot"))})));
        if(truth(compare(e,get(e.get("frame"),s("schema_version")),new Comparison(Cmp.NE,q102->n("1"))))) {
            throw new Rejected(py(s("schema_version must be 1")));
        }
        if(truth(compare(e,get(e.get("frame"),s("case_kind")),new Comparison(Cmp.NE,q103->q103.get("ZHONGGUO_INCIDENT_KIND_V1"))))) {
            throw new Rejected(py(s("case kind binding changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("profile")),new Comparison(Cmp.NE,q104->attribute(q104.get("expected_query"),"profile"))))) {
            throw new Rejected(py(s("profile binding changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("request_nonce")),new Comparison(Cmp.NE,q105->attribute(q105.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("nonce binding changed")));
        }
        if(truth(compare(e,call(e,"_integer",args(new Part[]{p(get(e.get("frame"),s("snapshot_revision"))),p(s("snapshot_revision"))},new Kw("minimum",n("1")),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1"))))),new Comparison(Cmp.NE,q106->q106.get("expected_snapshot_revision"))))) {
            throw new Rejected(py(s("snapshot revision binding changed")));
        }
        if(truth(compare(e,call(e,"_integer",args(new Part[]{p(get(e.get("frame"),s("date_raw"))),p(s("date_raw"))},new Kw("minimum",negate(binary(Op.POW,n("2"),n("31")))),new Kw("maximum",binary(Op.SUB,binary(Op.POW,n("2"),n("31")),n("1"))))),new Comparison(Cmp.NE,q107->q107.get("expected_date_raw"))))) {
            throw new Rejected(py(s("date binding changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("paused")),new Comparison(Cmp.IS_NOT,q108->TRUE)))) {
            throw new Rejected(py(s("incident query is not paused")));
        }
        assign(e,new NameTarget("player"),call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("player_character_id"))),p(s("player"))})));
        assign(e,new NameTarget("subject"),call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("subject_character_id"))),p(s("subject"))})));
        assign(e,new NameTarget("owner"),call(e,"_positive_int32",args(new Part[]{p(get(e.get("frame"),s("requested_owner_character_id"))),p(s("owner"))})));
        if(truth(or(e,q109->compare(q109,q109.get("player"),new Comparison(Cmp.NE,q110->q110.get("expected_player_character_id"))),q111->compare(q111,q111.get("subject"),new Comparison(Cmp.NE,q112->q112.get("player")))))) {
            throw new Rejected(py(s("played-character subject binding changed")));
        }
        if(truth(or(e,q113->compare(q113,q113.get("owner"),new Comparison(Cmp.NE,q114->attribute(q114.get("expected_query"),"owner_character_id"))),q115->compare(q115,q115.get("owner"),new Comparison(Cmp.EQ,q116->q116.get("player")))))) {
            throw new Rejected(py(s("owner filter binding changed")));
        }
        assign(e,new NameTarget("probe"),call(e,"_typed_group",args(new Part[]{p(get(e.get("frame"),s("probe"))),p(e.get("_PROBE_KEYS")),p(s("probe"))})));
        assign(e,new NameTarget("resources"),call(e,"_typed_group",args(new Part[]{p(get(e.get("frame"),s("resources"))),p(e.get("_RESOURCE_KEYS")),p(s("resources"))})));
        assign(e,new NameTarget("terminal"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("terminal"))),p(e.get("_TERMINAL_KEYS")),p(s("terminal"))})));
        assign(e,new NameTarget("kpi_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("kpi"))),p(e.get("_KPI_KEYS")),p(s("kpi"))})));
        assign(e,new NameTarget("kpi"),dict(new Item(s("disposition"),get(e.get("kpi_raw"),s("disposition")))));
        method(e.get("kpi"),"update",args(new Part[]{p(dictFrom(iter(generator(e,q117->seq(true,p(q117.get("key")),p(call(q117,"_typed",args(new Part[]{p(get(q117.get("kpi_raw"),q117.get("key"))),p(joined(s("kpi."),s(py(q117.get("key")))))})))),new Clause(new NameTarget("key"),q118->q118.get("_KPI_VALUE_KEYS"),List.of())))))}));
        assign(e,new NameTarget("readiness_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("readiness"))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        assign(e,new NameTarget("readiness"),dict());
        for(V q119:iter(e.get("_READINESS_KEYS"))) {
            assign(e,new NameTarget("key"),q119);
            assign(e,new NameTarget("flag"),get(e.get("readiness_raw"),e.get("key")));
            if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(e.get("flag")),p(e.get("bool"))})))))) {
                throw new Rejected(py(joined(s("readiness."),s(py(e.get("key"))),s(" must be boolean"))));
            }
            put(e.get("readiness"),e.get("key"),e.get("flag"));
        }
        assign(e,new NameTarget("expected_ready"),call(e,"all",args(new Part[]{p(generator(e,q120->get(q120.get("readiness"),q120.get("key")),new Clause(new NameTarget("key"),q121->q121.get("_READINESS_KEYS"),List.of(q121->compare(q121,q121.get("key"),new Comparison(Cmp.NE,q122->s("ready")))))))})));
        if(truth(compare(e,get(e.get("readiness"),s("ready")),new Comparison(Cmp.IS_NOT,q123->q123.get("expected_ready"))))) {
            throw new Rejected(py(s("readiness.ready disagrees with component gates")));
        }
        assign(e,new NameTarget("provenance"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("provenance"))),p(call(e,"set",args(new Part[]{p(e.get("_PROVENANCE_VALUES"))}))),p(s("provenance"))})));
        if(truth(compare(e,e.get("provenance"),new Comparison(Cmp.NE,q124->q124.get("_PROVENANCE_VALUES"))))) {
            throw new Rejected(py(s("provenance does not match the frozen build")));
        }
        assign(e,new NameTarget("status"),get(e.get("frame"),s("status")));
        assign(e,new NameTarget("reason"),get(e.get("frame"),s("unavailable_reason")));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q125->s("unavailable"))))) {
            if(truth(or(e,q126->compare(q126,q126.get("reason"),new Comparison(Cmp.NOT_IN,q127->q127.get("_TOP_REASONS"))),q128->get(q128.get("readiness"),s("ready"))))) {
                throw new Rejected(py(s("unavailable frame has an invalid reason")));
            }
            if(truth(compare(e,e.get("terminal"),new Comparison(Cmp.NE,q129->dict(new Item(s("kind"),s("unavailable")),new Item(s("na"),NONE),new Item(s("incident"),NONE)))))) {
                throw new Rejected(py(s("unavailable frame exposes a terminal")));
            }
            if(truth(or(e,q130->b(!truth(call(q130,"_all_unavailable",args(new Part[]{p(q130.get("probe"))})))),q131->b(!truth(call(q131,"_all_unavailable",args(new Part[]{p(q131.get("resources"))}))))))) {
                throw new Rejected(py(s("unavailable frame leaks probe/resources")));
            }
            if(truth(or(e,q132->compare(q132,get(q132.get("kpi"),s("disposition")),new Comparison(Cmp.NE,q133->s("unavailable"))),q134->b(!truth(call(q134,"_all_unavailable",args(new Part[]{p(dictFrom(iter(generator(q134,q135->seq(true,p(q135.get("key")),p(get(q135.get("kpi"),q135.get("key")))),new Clause(new NameTarget("key"),q136->q136.get("_KPI_VALUE_KEYS"),List.of())))))}))))))) {
                throw new Rejected(py(s("unavailable frame leaks KPI state")));
            }
            return dict(new Expansion(e.get("frame")),new Item(s("probe"),e.get("probe")),new Item(s("resources"),e.get("resources")),new Item(s("kpi"),e.get("kpi")),new Item(s("readiness"),e.get("readiness")));
        }
        if(truth(or(e,q137->compare(q137,q137.get("status"),new Comparison(Cmp.NE,q138->s("available"))),q139->compare(q139,q139.get("reason"),new Comparison(Cmp.IS_NOT,q140->NONE))))) {
            throw new Rejected(py(s("status must be typed available or unavailable")));
        }
        if(truth(b(!truth(call(e,"_all_available",args(new Part[]{p(e.get("probe"))})))))) {
            throw new Rejected(py(s("available frame has an incomplete probe")));
        }
        assign(e,new NameTarget("pv"),dictFrom(iter(generator(e,q141->seq(true,p(q141.get("key")),p(call(q141,"_value",args(new Part[]{p(q141.get("field")),p(joined(s("probe."),s(py(q141.get("key")))))})))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("field"))),q142->method(q142.get("probe"),"items",args(new Part[]{})),List.of())))));
        if(truth(or(e,q143->compare(q143,get(q143.get("pv"),s("owner_character_id")),new Comparison(Cmp.NE,q144->q144.get("owner"))),q145->compare(q145,get(q145.get("pv"),s("subject_character_id")),new Comparison(Cmp.NE,q146->q146.get("player"))),q147->compare(q147,get(q147.get("pv"),s("cycle_serial")),new Comparison(Cmp.LT,q148->n("1"))),q149->compare(q149,get(q149.get("pv"),s("probe_serial")),new Comparison(Cmp.LT,q150->n("1"))),q151->compare(q151,get(q151.get("pv"),s("result")),new Comparison(Cmp.NOT_IN,q152->set(p(n("0")),p(n("1")))))))) {
            throw new Rejected(py(s("probe identity is invalid")));
        }
        if(truth(compare(e,get(e.get("readiness"),s("probe_ready")),new Comparison(Cmp.IS_NOT,q153->TRUE)))) {
            throw new Rejected(py(s("available probe is not marked ready")));
        }
        if(truth(or(e,q154->b(!truth(get(q154.get("readiness"),s("player_subject_binding_ready")))),q155->b(!truth(get(q155.get("readiness"),s("owner_binding_ready"))))))) {
            throw new Rejected(py(s("available frame lacks owner/subject binding")));
        }
        if(truth(or(e,q156->b(!truth(get(q156.get("readiness"),s("profile_binding_ready")))),q157->b(!truth(get(q157.get("readiness"),s("same_frame_ready"))))))) {
            throw new Rejected(py(s("available frame lacks profile/same-frame binding")));
        }
        assign(e,new NameTarget("resource_ready"),call(e,"_all_available",args(new Part[]{p(e.get("resources"))})));
        if(truth(compare(e,get(e.get("readiness"),s("resource_snapshot_ready")),new Comparison(Cmp.IS_NOT,q158->q158.get("resource_ready"))))) {
            throw new Rejected(py(s("resource readiness disagrees with typed resources")));
        }
        assign(e,new NameTarget("kind"),get(e.get("terminal"),s("kind")));
        assign(e,new NameTarget("na"),NONE);
        assign(e,new NameTarget("incident"),NONE);
        if(truth(compare(e,e.get("kind"),new Comparison(Cmp.EQ,q159->s("na"))))) {
            if(truth(compare(e,get(e.get("terminal"),s("incident")),new Comparison(Cmp.IS_NOT,q160->NONE)))) {
                throw new Rejected(py(s("N/A union contains an incident arm")));
            }
            assign(e,new NameTarget("na"),call(e,"_typed_group",args(new Part[]{p(get(e.get("terminal"),s("na"))),p(e.get("_NA_KEYS")),p(s("terminal.na"))})));
            if(truth(b(!truth(call(e,"_all_available",args(new Part[]{p(e.get("na"))})))))) {
                throw new Rejected(py(s("N/A tuple is incomplete")));
            }
            assign(e,new NameTarget("nv"),dictFrom(iter(generator(e,q161->seq(true,p(q161.get("key")),p(call(q161,"_value",args(new Part[]{p(q161.get("field")),p(joined(s("terminal.na."),s(py(q161.get("key")))))})))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("field"))),q162->method(q162.get("na"),"items",args(new Part[]{})),List.of())))));
            if(truth(or(e,q163->compare(q163,get(q163.get("pv"),s("result")),new Comparison(Cmp.NE,q164->n("0"))),q165->compare(q165,get(q165.get("pv"),s("source_kind")),new Comparison(Cmp.NE,q166->n("0"))),q167->compare(q167,get(q167.get("pv"),s("consequence_kind")),new Comparison(Cmp.NE,q168->n("0"))),q169->compare(q169,get(q169.get("nv"),s("owner_character_id")),new Comparison(Cmp.NE,q170->q170.get("owner"))),q171->compare(q171,get(q171.get("nv"),s("subject_character_id")),new Comparison(Cmp.NE,q172->q172.get("player"))),q173->compare(q173,get(q173.get("nv"),s("cycle_serial")),new Comparison(Cmp.NE,q174->get(q174.get("pv"),s("cycle_serial")))),q175->compare(q175,get(q175.get("nv"),s("probe_serial")),new Comparison(Cmp.NE,q176->get(q176.get("pv"),s("probe_serial")))),q177->compare(q177,get(q177.get("nv"),s("reason")),new Comparison(Cmp.NE,q178->n("1"))),q179->compare(q179,get(q179.get("nv"),s("receipt_serial")),new Comparison(Cmp.LT,q180->n("1"))),q181->compare(q181,get(q181.get("nv"),s("applicable")),new Comparison(Cmp.NE,q182->n("0"))),q183->compare(q183,get(q183.get("nv"),s("kpi_staged")),new Comparison(Cmp.NE,q184->n("0")))))) {
                throw new Rejected(py(s("N/A tuple is not an exact positive receipt")));
            }
        } else {
            if(truth(compare(e,e.get("kind"),new Comparison(Cmp.EQ,q185->s("incident"))))) {
                if(truth(compare(e,get(e.get("terminal"),s("na")),new Comparison(Cmp.IS_NOT,q186->NONE)))) {
                    throw new Rejected(py(s("incident union contains an N/A arm")));
                }
                assign(e,new NameTarget("incident"),call(e,"_typed_group",args(new Part[]{p(get(e.get("terminal"),s("incident"))),p(e.get("_INCIDENT_KEYS")),p(s("terminal.incident"))})));
                if(truth(b(!truth(call(e,"_all_available",args(new Part[]{p(e.get("incident"))})))))) {
                    throw new Rejected(py(s("incident terminal tuple is incomplete")));
                }
                assign(e,new NameTarget("iv"),dictFrom(iter(generator(e,q187->seq(true,p(q187.get("key")),p(call(q187,"_value",args(new Part[]{p(q187.get("field")),p(joined(s("terminal.incident."),s(py(q187.get("key")))))})))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("field"))),q188->method(q188.get("incident"),"items",args(new Part[]{})),List.of())))));
                assign(e,new NameTarget("expected_state"),(truth(compare(e,attribute(e.get("expected_query"),"profile"),new Comparison(Cmp.EQ,q189->s("x"))))?n("8"):n("6")));
                if(truth(or(e,q190->compare(q190,get(q190.get("pv"),s("result")),new Comparison(Cmp.NE,q191->n("1"))),q192->compare(q192,seq(true,p(get(q192.get("pv"),s("source_kind"))),p(get(q192.get("pv"),s("consequence_kind")))),new Comparison(Cmp.NOT_IN,q193->q193.get("_SOURCE_CONSEQUENCE"))),q194->compare(q194,get(q194.get("iv"),s("owner_character_id")),new Comparison(Cmp.NE,q195->q195.get("owner"))),q196->compare(q196,get(q196.get("iv"),s("subject_character_id")),new Comparison(Cmp.NE,q197->q197.get("player"))),q198->compare(q198,get(q198.get("iv"),s("cycle_serial")),new Comparison(Cmp.NE,q199->get(q199.get("pv"),s("cycle_serial")))),q200->b(!truth(compare(q200,n("1"),new Comparison(Cmp.LE,q201->get(q201.get("iv"),s("case_serial"))),new Comparison(Cmp.LE,q202->n("999999"))))),q203->compare(q203,get(q203.get("iv"),s("state")),new Comparison(Cmp.NE,q204->q204.get("expected_state"))),q205->compare(q205,get(q205.get("iv"),s("revision")),new Comparison(Cmp.LT,q206->n("1"))),q207->compare(q207,get(q207.get("iv"),s("incident_serial")),new Comparison(Cmp.LT,q208->n("1"))),q209->compare(q209,get(q209.get("iv"),s("source_kind")),new Comparison(Cmp.NE,q210->get(q210.get("pv"),s("source_kind")))),q211->compare(q211,get(q211.get("iv"),s("consequence_kind")),new Comparison(Cmp.NE,q212->get(q212.get("pv"),s("consequence_kind")))),q213->b(!truth(compare(q213,negate(n("4")),new Comparison(Cmp.LE,q214->get(q214.get("iv"),s("final_score"))),new Comparison(Cmp.LE,q215->n("4"))))),q216->compare(q216,get(q216.get("iv"),s("applicable")),new Comparison(Cmp.NE,q217->n("1"))),q218->compare(q218,get(q218.get("iv"),s("kpi_staged")),new Comparison(Cmp.NOT_IN,q219->set(p(n("0")),p(n("1")))))))) {
                    throw new Rejected(py(s("incident terminal does not join its probe")));
                }
            } else {
                throw new Rejected(py(s("available terminal must be exactly na or incident")));
            }
        }
        if(truth(b(!truth(get(e.get("readiness"),s("terminal_ready")))))) {
            throw new Rejected(py(s("available terminal is not marked ready")));
        }
        assign(e,new NameTarget("kpi_ready"),call(e,"_validate_kpi",args(new Part[]{p(e.get("kpi"))},new Kw("terminal_kind",e.get("kind")),new Kw("incident",e.get("incident")))));
        if(truth(compare(e,get(e.get("readiness"),s("kpi_state_ready")),new Comparison(Cmp.IS_NOT,q220->q220.get("kpi_ready"))))) {
            throw new Rejected(py(s("KPI readiness disagrees with the typed tuple")));
        }
        return dict(new Expansion(e.get("frame")),new Item(s("probe"),e.get("probe")),new Item(s("resources"),e.get("resources")),new Item(s("terminal"),dict(new Item(s("kind"),e.get("kind")),new Item(s("na"),e.get("na")),new Item(s("incident"),e.get("incident")))),new Item(s("kpi"),e.get("kpi")),new Item(s("readiness"),e.get("readiness")));
    }
    // Original zhongguo_incident_snapshot_contract.py:256..259
    private static V fvalidate_incident_profile_v1(E e){
        if(truth(or(e,q221->b(!truth(call(q221,"isinstance",args(new Part[]{p(q221.get("value")),p(q221.get("str"))})))),q222->compare(q222,q222.get("value"),new Comparison(Cmp.NOT_IN,q223->q223.get("_PROFILES")))))) {
            throw new Rejected(py(s("profile must be exactly x, y, or z")));
        }
        return e.get("value");
    }
    // Original zhongguo_incident_snapshot_contract.py:250..253
    private static V fvalidate_incident_request_nonce_v1(E e){
        if(truth(or(e,q224->b(!truth(call(q224,"isinstance",args(new Part[]{p(q224.get("value")),p(q224.get("str"))})))),q225->compare(q225,method(q225.get("_NONCE_RE"),"fullmatch",args(new Part[]{p(q225.get("value"))})),new Comparison(Cmp.IS,q226->NONE))))) {
            throw new Rejected(py(s("request_nonce must be 1-64 ASCII token characters")));
        }
        return e.get("value");
    }
}
