package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_projects_metrics_postcondition_contract.py; original SHA-256 b2dba9ee76457d0ec72bd87464eec145618e76482bb77d4b6687a03c88a60436. No Python runtime. */
final class CasesPROJECTSOriginalNormalizer {
    private CasesPROJECTSOriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesPROJECTSOriginalNormalizer::dispatch);
        e.put("QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY",s("game.command.query-zhongguo-projects-metrics-postcondition-v1"));
        e.put("_TYPED_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_IDENTITY_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial"))));
        e.put("_PORTFOLIO_KEYS",set(p(s("closed")),p(s("cycle_serial")),p(s("final_owner_character_id")),p(s("final_subject_character_id")),p(s("final_cycle_serial")),p(s("final_case_serial")),p(s("final_state")),p(s("final_conservation_ok")),p(s("pending_player_event")),p(s("provider_observed"))));
        e.put("_READINESS_KEYS",set(p(s("player_subject_binding_ready")),p(s("owner_binding_ready")),p(s("portfolio_observed")),p(s("portfolio_closed")),p(s("source_identity_ready")),p(s("result_identity_ready")),p(s("contribution_ready")),p(s("metrics_ready")),p(s("same_project_case_identity")),p(s("receipt_lineage_ready")),p(s("result_operation_committed")),p(s("same_frame_ready")),p(s("ready"))));
        e.put("_CHECKPOINT_STATES",set(p(s("unavailable")),p(s("cp26_ready_p3_absent")),p(s("p3_initialized_source_not_ready")),p(s("p3_source_ready_result_pending")),p(s("p3_result_committed"))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_projects_metrics_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_exact" -> f_exact(bind(GLOBALS,CasesPROJECTSOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("keys",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_identity" -> f_identity(bind(GLOBALS,CasesPROJECTSOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed" -> f_typed(bind(GLOBALS,CasesPROJECTSOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED),new Param("kind",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_projects_metrics_v1" -> fnormalize_native_zhongguo_projects_metrics_v1(bind(GLOBALS,CasesPROJECTSOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_projects_metrics_postcondition_contract.py:115..118
    private static V f_exact(E e){
        if(truth(or(e,q1->b(!truth(call(q1,"isinstance",args(new Part[]{p(q1.get("value")),p(q1.get("dict"))})))),q2->compare(q2,call(q2,"set",args(new Part[]{p(q2.get("value"))})),new Comparison(Cmp.NE,q3->q3.get("keys")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_projects_metrics_postcondition_contract.py:139..141
    private static V f_identity(E e){
        assign(e,new NameTarget("raw"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_IDENTITY_KEYS")),p(e.get("name"))})));
        return dictFrom(iter(generator(e,q4->seq(true,p(q4.get("key")),p(call(q4,"_typed",args(new Part[]{p(get(q4.get("raw"),q4.get("key"))),p(joined(s(py(q4.get("name"))),s("."),s(py(q4.get("key"))))),p(q4.get("int"))})))),new Clause(new NameTarget("key"),q5->q5.get("raw"),List.of()))));
    }
    // Original zhongguo_projects_metrics_postcondition_contract.py:121..136
    private static V f_typed(E e){
        assign(e,new NameTarget("field"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_KEYS")),p(e.get("name"))})));
        if(truth(compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q6->s("available"))))) {
            assign(e,new NameTarget("raw"),get(e.get("field"),s("value")));
            if(truth(or(e,q7->compare(q7,get(q7.get("field"),s("unavailable_reason")),new Comparison(Cmp.IS_NOT,q8->NONE)),q9->call(q9,"isinstance",args(new Part[]{p(q9.get("raw")),p(q9.get("bool"))})),q10->b(!truth(call(q10,"isinstance",args(new Part[]{p(q10.get("raw")),p(q10.get("kind"))}))))))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid available value"))));
            }
        } else {
            if(truth(compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q11->s("unavailable"))))) {
                if(truth(or(e,q12->compare(q12,get(q12.get("field"),s("value")),new Comparison(Cmp.IS_NOT,q13->NONE)),q14->b(!truth(call(q14,"isinstance",args(new Part[]{p(get(q14.get("field"),s("unavailable_reason"))),p(q14.get("str"))}))))))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid typed unavailability"))));
                }
            } else {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid status"))));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_projects_metrics_postcondition_contract.py:144..307
    private static V fnormalize_native_zhongguo_projects_metrics_v1(E e){
        assign(e,new NameTarget("keys"),set(p(s("schema_version")),p(s("status")),p(s("capability")),p(s("case_kind")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("requested_owner_character_id")),p(s("requested_subject_character_id")),p(s("checkpoint_state")),p(s("credit_project_portfolio")),p(s("source_identity")),p(s("result_identity")),p(s("projects_metrics")),p(s("readiness")),p(s("source_backend_id")),p(s("provenance")),p(s("unavailable_reason"))));
        assign(e,new NameTarget("frame"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("keys")),p(s("projects_metrics_frame"))})));
        if(truth(or(e,q15->compare(q15,get(q15.get("frame"),s("schema_version")),new Comparison(Cmp.NE,q16->n("1"))),q17->compare(q17,get(q17.get("frame"),s("capability")),new Comparison(Cmp.NE,q18->q18.get("QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY"))),q19->compare(q19,get(q19.get("frame"),s("case_kind")),new Comparison(Cmp.NE,q20->s("zhongguo.projects-metrics.project-correlation"))),q21->compare(q21,get(q21.get("frame"),s("source_backend_id")),new Comparison(Cmp.NE,q22->s("native-headless")))))) {
            throw new Rejected(py(s("provider provenance changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("request_nonce")),new Comparison(Cmp.NE,q23->attribute(q23.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("request nonce changed")));
        }
        if(truth(or(e,q24->compare(q24,get(q24.get("frame"),s("snapshot_revision")),new Comparison(Cmp.NE,q25->q25.get("expected_snapshot_revision"))),q26->compare(q26,get(q26.get("frame"),s("date_raw")),new Comparison(Cmp.NE,q27->q27.get("expected_date_raw"))),q28->compare(q28,get(q28.get("frame"),s("paused")),new Comparison(Cmp.IS_NOT,q29->TRUE)),q30->compare(q30,get(q30.get("frame"),s("player_character_id")),new Comparison(Cmp.NE,q31->q31.get("expected_player_character_id"))),q32->compare(q32,get(q32.get("frame"),s("requested_owner_character_id")),new Comparison(Cmp.NE,q33->attribute(q33.get("expected_query"),"owner_character_id"))),q34->compare(q34,get(q34.get("frame"),s("requested_subject_character_id")),new Comparison(Cmp.NE,q35->attribute(q35.get("expected_query"),"subject_character_id"))),q36->compare(q36,attribute(q36.get("expected_query"),"owner_character_id"),new Comparison(Cmp.EQ,q37->attribute(q37.get("expected_query"),"subject_character_id"))),q38->compare(q38,q38.get("expected_player_character_id"),new Comparison(Cmp.NOT_IN,q39->set(p(attribute(q39.get("expected_query"),"owner_character_id")),p(attribute(q39.get("expected_query"),"subject_character_id")))))))) {
            throw new Rejected(py(s("paused owner/subject binding changed")));
        }
        assign(e,new NameTarget("portfolio_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("credit_project_portfolio"))),p(e.get("_PORTFOLIO_KEYS")),p(s("credit_project_portfolio"))})));
        if(truth(compare(e,get(e.get("portfolio_raw"),s("provider_observed")),new Comparison(Cmp.IS_NOT,q40->TRUE)))) {
            throw new Rejected(py(s("credit project portfolio is not provider observed")));
        }
        assign(e,new NameTarget("portfolio"),dictFrom(iter(generator(e,q41->seq(true,p(q41.get("key")),p(call(q41,"_typed",args(new Part[]{p(get(q41.get("portfolio_raw"),q41.get("key"))),p(joined(s("credit_project_portfolio."),s(py(q41.get("key"))))),p(q41.get("int"))})))),new Clause(new NameTarget("key"),q42->binary(Op.SUB,q42.get("_PORTFOLIO_KEYS"),set(p(s("provider_observed")))),List.of())))));
        put(e.get("portfolio"),s("provider_observed"),TRUE);
        assign(e,new NameTarget("source"),call(e,"_identity",args(new Part[]{p(get(e.get("frame"),s("source_identity"))),p(s("source_identity"))})));
        assign(e,new NameTarget("result"),call(e,"_identity",args(new Part[]{p(get(e.get("frame"),s("result_identity"))),p(s("result_identity"))})));
        assign(e,new NameTarget("payload"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("projects_metrics"))),p(set(p(s("source_identity")),p(s("result_identity")),p(s("contribution")),p(s("metrics_result")))),p(s("projects_metrics"))})));
        assign(e,new NameTarget("payload_source"),call(e,"_identity",args(new Part[]{p(get(e.get("payload"),s("source_identity"))),p(s("projects_metrics.source_identity"))})));
        assign(e,new NameTarget("payload_result"),call(e,"_identity",args(new Part[]{p(get(e.get("payload"),s("result_identity"))),p(s("projects_metrics.result_identity"))})));
        if(truth(or(e,q43->compare(q43,q43.get("payload_source"),new Comparison(Cmp.NE,q44->q44.get("source"))),q45->compare(q45,q45.get("payload_result"),new Comparison(Cmp.NE,q46->q46.get("result")))))) {
            throw new Rejected(py(s("outer and payload identities disagree")));
        }
        assign(e,new NameTarget("contribution_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("payload"),s("contribution"))),p(set(p(s("identity")),p(s("receipt_id")),p(s("receipt_revision")),p(s("value")),p(s("provider_observed")))),p(s("contribution"))})));
        if(truth(compare(e,get(e.get("contribution_raw"),s("provider_observed")),new Comparison(Cmp.IS_NOT,q47->TRUE)))) {
            throw new Rejected(py(s("contribution is not provider observed")));
        }
        assign(e,new NameTarget("contribution"),dict(new Item(s("identity"),call(e,"_identity",args(new Part[]{p(get(e.get("contribution_raw"),s("identity"))),p(s("contribution.identity"))}))),new Item(s("receipt_id"),call(e,"_typed",args(new Part[]{p(get(e.get("contribution_raw"),s("receipt_id"))),p(s("contribution.receipt_id")),p(e.get("int"))}))),new Item(s("receipt_revision"),call(e,"_typed",args(new Part[]{p(get(e.get("contribution_raw"),s("receipt_revision"))),p(s("contribution.receipt_revision")),p(e.get("int"))}))),new Item(s("value"),call(e,"_typed",args(new Part[]{p(get(e.get("contribution_raw"),s("value"))),p(s("contribution.value")),p(e.get("int"))}))),new Item(s("provider_observed"),TRUE)));
        assign(e,new NameTarget("metrics_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("payload"),s("metrics_result"))),p(set(p(s("identity")),p(s("source_contribution_receipt_id")),p(s("source_contribution_receipt_revision")),p(s("metrics_revision")),p(s("dictionary_key")),p(s("provider_observed")))),p(s("metrics_result"))})));
        if(truth(compare(e,get(e.get("metrics_raw"),s("provider_observed")),new Comparison(Cmp.IS_NOT,q48->TRUE)))) {
            throw new Rejected(py(s("metrics result is not provider observed")));
        }
        assign(e,new NameTarget("metrics"),dict(new Item(s("identity"),call(e,"_identity",args(new Part[]{p(get(e.get("metrics_raw"),s("identity"))),p(s("metrics_result.identity"))}))),new Item(s("source_contribution_receipt_id"),call(e,"_typed",args(new Part[]{p(get(e.get("metrics_raw"),s("source_contribution_receipt_id"))),p(s("metrics_result.source_contribution_receipt_id")),p(e.get("int"))}))),new Item(s("source_contribution_receipt_revision"),call(e,"_typed",args(new Part[]{p(get(e.get("metrics_raw"),s("source_contribution_receipt_revision"))),p(s("metrics_result.source_contribution_receipt_revision")),p(e.get("int"))}))),new Item(s("metrics_revision"),call(e,"_typed",args(new Part[]{p(get(e.get("metrics_raw"),s("metrics_revision"))),p(s("metrics_result.metrics_revision")),p(e.get("int"))}))),new Item(s("dictionary_key"),call(e,"_typed",args(new Part[]{p(get(e.get("metrics_raw"),s("dictionary_key"))),p(s("metrics_result.dictionary_key")),p(e.get("str"))}))),new Item(s("provider_observed"),TRUE)));
        assign(e,new NameTarget("readiness_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("readiness"))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        if(truth(call(e,"any",args(new Part[]{p(generator(e,q49->b(!truth(call(q49,"isinstance",args(new Part[]{p(q49.get("item")),p(q49.get("bool"))})))),new Clause(new NameTarget("item"),q50->method(q50.get("readiness_raw"),"values",args(new Part[]{})),List.of())))})))) {
            throw new Rejected(py(s("readiness values must be boolean")));
        }
        assign(e,new NameTarget("expected_ready"),call(e,"all",args(new Part[]{p(generator(e,q51->get(q51.get("readiness_raw"),q51.get("key")),new Clause(new NameTarget("key"),q52->binary(Op.SUB,q52.get("_READINESS_KEYS"),set(p(s("ready")))),List.of())))})));
        if(truth(compare(e,get(e.get("readiness_raw"),s("ready")),new Comparison(Cmp.IS_NOT,q53->q53.get("expected_ready"))))) {
            throw new Rejected(py(s("readiness aggregate disagrees")));
        }
        if(truth(compare(e,get(e.get("frame"),s("status")),new Comparison(Cmp.NOT_IN,q54->set(p(s("available")),p(s("unavailable"))))))) {
            throw new Rejected(py(s("invalid provider status")));
        }
        assign(e,new NameTarget("checkpoint_state"),get(e.get("frame"),s("checkpoint_state")));
        if(truth(or(e,q55->b(!truth(call(q55,"isinstance",args(new Part[]{p(q55.get("checkpoint_state")),p(q55.get("str"))})))),q56->compare(q56,q56.get("checkpoint_state"),new Comparison(Cmp.NOT_IN,q57->q57.get("_CHECKPOINT_STATES")))))) {
            throw new Rejected(py(s("invalid projects/metrics checkpoint state")));
        }
        if(truth(compare(e,get(e.get("frame"),s("status")),new Comparison(Cmp.EQ,q58->s("available"))))) {
            if(truth(or(e,q59->compare(q59,get(q59.get("frame"),s("unavailable_reason")),new Comparison(Cmp.IS_NOT,q60->NONE)),q61->compare(q61,q61.get("checkpoint_state"),new Comparison(Cmp.EQ,q62->s("unavailable")))))) {
                throw new Rejected(py(s("available provider has an unavailable reason")));
            }
            assign(e,new NameTarget("source_keys"),seq(true,p(s("owner_binding_ready")),p(s("portfolio_observed")),p(s("source_identity_ready")),p(s("contribution_ready")),p(s("same_frame_ready"))));
            if(truth(b(!truth(call(e,"all",args(new Part[]{p(generator(e,q63->compare(q63,get(q63.get("readiness_raw"),q63.get("key")),new Comparison(Cmp.IS,q65->TRUE)),new Clause(new NameTarget("key"),q64->q64.get("source_keys"),List.of())))})))))) {
                throw new Rejected(py(s("available provider lacks its direct CP26 source")));
            }
            if(truth(and(e,q66->compare(q66,q66.get("checkpoint_state"),new Comparison(Cmp.EQ,q67->s("cp26_ready_p3_absent"))),q68->call(q68,"any",args(new Part[]{p(generator(q68,q69->compare(q69,get(q69.get("readiness_raw"),q69.get("key")),new Comparison(Cmp.IS,q71->TRUE)),new Clause(new NameTarget("key"),q70->seq(true,p(s("result_identity_ready")),p(s("metrics_ready")),p(s("same_project_case_identity")),p(s("receipt_lineage_ready")),p(s("result_operation_committed")),p(s("ready"))),List.of())))}))))) {
                throw new Rejected(py(s("CP26/P3-absent state exposes a P3 result")));
            }
            if(truth(and(e,q72->compare(q72,q72.get("checkpoint_state"),new Comparison(Cmp.EQ,q73->s("p3_result_committed"))),q74->compare(q74,get(q74.get("readiness_raw"),s("ready")),new Comparison(Cmp.IS_NOT,q75->TRUE))))) {
                throw new Rejected(py(s("committed checkpoint is not ready")));
            }
        } else {
            if(truth(or(e,q76->b(!truth(call(q76,"isinstance",args(new Part[]{p(get(q76.get("frame"),s("unavailable_reason"))),p(q76.get("str"))})))),q77->compare(q77,q77.get("checkpoint_state"),new Comparison(Cmp.NE,q78->s("unavailable")))))) {
                throw new Rejected(py(s("unavailable provider lacks reason/state")));
            }
        }
        return dict(new Expansion(e.get("frame")),new Item(s("credit_project_portfolio"),e.get("portfolio")),new Item(s("source_identity"),e.get("source")),new Item(s("result_identity"),e.get("result")),new Item(s("projects_metrics"),dict(new Item(s("source_identity"),e.get("payload_source")),new Item(s("result_identity"),e.get("payload_result")),new Item(s("contribution"),e.get("contribution")),new Item(s("metrics_result"),e.get("metrics")))),new Item(s("readiness"),call(e,"dict",args(new Part[]{p(e.get("readiness_raw"))}))));
    }
}
