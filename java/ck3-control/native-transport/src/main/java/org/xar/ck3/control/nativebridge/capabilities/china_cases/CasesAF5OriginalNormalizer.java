package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_compensation_af5_snapshot_contract.py; original SHA-256 48cff74ba84a0a4f614c8071078c4066fe5af5fdf04f7ac7dda9121728e25744. No Python runtime. */
final class CasesAF5OriginalNormalizer {
    private CasesAF5OriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesAF5OriginalNormalizer::dispatch);
        e.put("QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_CAPABILITY",s("game.command.query-zhongguo-compensation-af5-snapshot-v1"));
        e.put("_TYPED_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_IDENTITY_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("revision"))));
        e.put("_READINESS_KEYS",set(p(s("player_owner_binding_ready")),p(s("portfolio_subject_binding_ready")),p(s("same_case_identity_ready")),p(s("same_frame_ready")),p(s("ready"))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_compensation_af5_snapshot_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_exact" -> f_exact(bind(GLOBALS,CasesAF5OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("keys",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_identity" -> f_identity(bind(GLOBALS,CasesAF5OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("revision",FALSE)),null),args));
            case "_positive" -> f_positive(bind(GLOBALS,CasesAF5OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed" -> f_typed(bind(GLOBALS,CasesAF5OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED),new Param("kind",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_compensation_af5_snapshot_v1" -> fnormalize_native_zhongguo_compensation_af5_snapshot_v1(bind(GLOBALS,CasesAF5OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_compensation_af5_snapshot_contract.py:86..89
    private static V f_exact(E e){
        if(truth(or(e,q1->b(!truth(call(q1,"isinstance",args(new Part[]{p(q1.get("value")),p(q1.get("dict"))})))),q2->compare(q2,call(q2,"set",args(new Part[]{p(q2.get("value"))})),new Comparison(Cmp.NE,q3->q3.get("keys")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_compensation_af5_snapshot_contract.py:110..113
    private static V f_identity(E e){
        assign(e,new NameTarget("keys"),(truth(e.get("revision"))?e.get("_IDENTITY_KEYS"):binary(Op.SUB,e.get("_IDENTITY_KEYS"),set(p(s("revision"))))));
        assign(e,new NameTarget("raw"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("keys")),p(e.get("name"))})));
        return dictFrom(iter(generator(e,q4->seq(true,p(q4.get("key")),p(call(q4,"_typed",args(new Part[]{p(get(q4.get("raw"),q4.get("key"))),p(joined(s(py(q4.get("name"))),s("."),s(py(q4.get("key"))))),p(q4.get("int"))})))),new Clause(new NameTarget("key"),q5->q5.get("raw"),List.of()))));
    }
    // Original zhongguo_compensation_af5_snapshot_contract.py:37..40
    private static V f_positive(E e){
        if(truth(or(e,q6->call(q6,"isinstance",args(new Part[]{p(q6.get("value")),p(q6.get("bool"))})),q7->b(!truth(call(q7,"isinstance",args(new Part[]{p(q7.get("value")),p(q7.get("int"))})))),q8->compare(q8,q8.get("value"),new Comparison(Cmp.LE,q9->n("0")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be a positive integer"))));
        }
        return e.get("value");
    }
    // Original zhongguo_compensation_af5_snapshot_contract.py:92..107
    private static V f_typed(E e){
        assign(e,new NameTarget("field"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_KEYS")),p(e.get("name"))})));
        if(truth(compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q10->s("available"))))) {
            assign(e,new NameTarget("raw"),get(e.get("field"),s("value")));
            if(truth(or(e,q11->compare(q11,get(q11.get("field"),s("unavailable_reason")),new Comparison(Cmp.IS_NOT,q12->NONE)),q13->compare(q13,call(q13,"isinstance",args(new Part[]{p(q13.get("raw")),p(q13.get("bool"))})),new Comparison(Cmp.NE,q14->compare(q14,q14.get("kind"),new Comparison(Cmp.IS,q15->q15.get("bool"))))),q16->b(!truth(call(q16,"isinstance",args(new Part[]{p(q16.get("raw")),p(q16.get("kind"))}))))))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid available value"))));
            }
        } else {
            if(truth(compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q17->s("unavailable"))))) {
                if(truth(or(e,q18->compare(q18,get(q18.get("field"),s("value")),new Comparison(Cmp.IS_NOT,q19->NONE)),q20->b(!truth(call(q20,"isinstance",args(new Part[]{p(get(q20.get("field"),s("unavailable_reason"))),p(q20.get("str"))}))))))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid typed unavailability"))));
                }
            } else {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid status"))));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_compensation_af5_snapshot_contract.py:116..204
    private static V fnormalize_native_zhongguo_compensation_af5_snapshot_v1(E e){
        assign(e,new NameTarget("frame"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(set(p(s("schema_version")),p(s("status")),p(s("capability")),p(s("source_backend_id")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("subject_character_id")),p(s("af5")),p(s("readiness")),p(s("terminal")),p(s("unavailable_reason")))),p(s("af5_frame"))})));
        if(truth(or(e,q21->compare(q21,get(q21.get("frame"),s("schema_version")),new Comparison(Cmp.NE,q22->n("1"))),q23->compare(q23,get(q23.get("frame"),s("capability")),new Comparison(Cmp.NE,q24->q24.get("QUERY_ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_CAPABILITY"))),q25->compare(q25,get(q25.get("frame"),s("source_backend_id")),new Comparison(Cmp.NE,q26->s("ck3-1.19.0.6-native-zhongguo-compensation-af5-snapshot-v1")))))) {
            throw new Rejected(py(s("provider provenance changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("request_nonce")),new Comparison(Cmp.NE,q27->attribute(q27.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("request nonce changed")));
        }
        if(truth(or(e,q28->compare(q28,get(q28.get("frame"),s("snapshot_revision")),new Comparison(Cmp.NE,q29->q29.get("expected_snapshot_revision"))),q30->compare(q30,get(q30.get("frame"),s("date_raw")),new Comparison(Cmp.NE,q31->q31.get("expected_date_raw"))),q32->compare(q32,get(q32.get("frame"),s("paused")),new Comparison(Cmp.IS_NOT,q33->TRUE))))) {
            throw new Rejected(py(s("paused native frame changed")));
        }
        if(truth(or(e,q34->compare(q34,get(q34.get("frame"),s("player_character_id")),new Comparison(Cmp.NE,q35->q35.get("expected_player_character_id"))),q36->compare(q36,attribute(q36.get("expected_query"),"owner_character_id"),new Comparison(Cmp.NE,q37->q37.get("expected_player_character_id")))))) {
            throw new Rejected(py(s("played owner binding changed")));
        }
        call(e,"_positive",args(new Part[]{p(get(e.get("frame"),s("subject_character_id"))),p(s("subject_character_id"))}));
        assign(e,new NameTarget("payload"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("af5"))),p(set(p(s("portfolio")),p(s("case")),p(s("m299")),p(s("m300")))),p(s("af5"))})));
        assign(e,new NameTarget("portfolio"),call(e,"_exact",args(new Part[]{p(get(e.get("payload"),s("portfolio"))),p(set(p(s("domain")),p(s("stage")),p(s("completed_cycle")),p(s("visible_pending")),p(s("result_identity")))),p(s("af5.portfolio"))})));
        assign(e,new NameTarget("normalized_portfolio"),dictFrom(iter(generator(e,q38->seq(true,p(q38.get("key")),p(call(q38,"_typed",args(new Part[]{p(get(q38.get("portfolio"),q38.get("key"))),p(joined(s("af5.portfolio."),s(py(q38.get("key"))))),p(q38.get("int"))})))),new Clause(new NameTarget("key"),q39->seq(true,p(s("domain")),p(s("stage")),p(s("completed_cycle"))),List.of())))));
        put(e.get("normalized_portfolio"),s("visible_pending"),call(e,"_typed",args(new Part[]{p(get(e.get("portfolio"),s("visible_pending"))),p(s("af5.portfolio.visible_pending")),p(e.get("bool"))})));
        put(e.get("normalized_portfolio"),s("result_identity"),call(e,"_identity",args(new Part[]{p(get(e.get("portfolio"),s("result_identity"))),p(s("af5.portfolio.result_identity"))})));
        assign(e,new NameTarget("case"),call(e,"_exact",args(new Part[]{p(get(e.get("payload"),s("case"))),p(set(p(s("identity")),p(s("state")),p(s("active")),p(s("last_operation")),p(s("last_route")),p(s("repurchase_resolved")),p(s("unit_conserved")),p(s("result_case_serial")))),p(s("af5.case"))})));
        assign(e,new NameTarget("normalized_case"),dict(new Item(s("identity"),call(e,"_identity",args(new Part[]{p(get(e.get("case"),s("identity"))),p(s("af5.case.identity"))},new Kw("revision",TRUE))))));
        for(V q40:iter(seq(true,p(s("state")),p(s("last_operation")),p(s("last_route")),p(s("result_case_serial"))))) {
            assign(e,new NameTarget("key"),q40);
            put(e.get("normalized_case"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("case"),e.get("key"))),p(joined(s("af5.case."),s(py(e.get("key"))))),p(e.get("int"))})));
        }
        for(V q41:iter(seq(true,p(s("active")),p(s("repurchase_resolved")),p(s("unit_conserved"))))) {
            assign(e,new NameTarget("key"),q41);
            put(e.get("normalized_case"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("case"),e.get("key"))),p(joined(s("af5.case."),s(py(e.get("key"))))),p(e.get("bool"))})));
        }
        assign(e,new NameTarget("normalized_af5"),dict(new Item(s("portfolio"),e.get("normalized_portfolio")),new Item(s("case"),e.get("normalized_case"))));
        for(V q42:iter(seq(true,p(s("m299")),p(s("m300"))))) {
            assign(e,new NameTarget("receipt_name"),q42);
            assign(e,new NameTarget("receipt"),call(e,"_exact",args(new Part[]{p(get(e.get("payload"),e.get("receipt_name"))),p(set(p(s("identity")),p(s("state")),p(s("active")),p(s("consumed")),p(s("route")))),p(joined(s("af5."),s(py(e.get("receipt_name")))))})));
            assign(e,new NameTarget("normalized_receipt"),dict(new Item(s("identity"),call(e,"_identity",args(new Part[]{p(get(e.get("receipt"),s("identity"))),p(joined(s("af5."),s(py(e.get("receipt_name"))),s(".identity")))})))));
            for(V q43:iter(seq(true,p(s("state")),p(s("route"))))) {
                assign(e,new NameTarget("key"),q43);
                put(e.get("normalized_receipt"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("receipt"),e.get("key"))),p(joined(s("af5."),s(py(e.get("receipt_name"))),s("."),s(py(e.get("key"))))),p(e.get("int"))})));
            }
            for(V q44:iter(seq(true,p(s("active")),p(s("consumed"))))) {
                assign(e,new NameTarget("key"),q44);
                put(e.get("normalized_receipt"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("receipt"),e.get("key"))),p(joined(s("af5."),s(py(e.get("receipt_name"))),s("."),s(py(e.get("key"))))),p(e.get("bool"))})));
            }
            put(e.get("normalized_af5"),e.get("receipt_name"),e.get("normalized_receipt"));
        }
        assign(e,new NameTarget("readiness"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("readiness"))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        if(truth(call(e,"any",args(new Part[]{p(generator(e,q45->b(!truth(call(q45,"isinstance",args(new Part[]{p(q45.get("raw")),p(q45.get("bool"))})))),new Clause(new NameTarget("raw"),q46->method(q46.get("readiness"),"values",args(new Part[]{})),List.of())))})))) {
            throw new Rejected(py(s("readiness values must be boolean")));
        }
        if(truth(compare(e,get(e.get("readiness"),s("ready")),new Comparison(Cmp.IS_NOT,q47->call(q47,"all",args(new Part[]{p(generator(q47,q48->get(q48.get("readiness"),q48.get("key")),new Clause(new NameTarget("key"),q49->binary(Op.SUB,q49.get("_READINESS_KEYS"),set(p(s("ready")))),List.of())))})))))) {
            throw new Rejected(py(s("readiness aggregate disagrees")));
        }
        if(truth(or(e,q50->b(!truth(call(q50,"isinstance",args(new Part[]{p(get(q50.get("frame"),s("terminal"))),p(q50.get("bool"))})))),q51->and(q51,q52->get(q52.get("frame"),s("terminal")),q53->b(!truth(get(q53.get("readiness"),s("ready")))))))) {
            throw new Rejected(py(s("terminal requires an observable AF5 frame")));
        }
        if(truth(compare(e,get(e.get("frame"),s("status")),new Comparison(Cmp.NOT_IN,q54->set(p(s("available")),p(s("unavailable"))))))) {
            throw new Rejected(py(s("invalid provider status")));
        }
        if(truth(and(e,q55->compare(q55,get(q55.get("frame"),s("status")),new Comparison(Cmp.EQ,q56->s("unavailable"))),q57->b(!truth(call(q57,"isinstance",args(new Part[]{p(get(q57.get("frame"),s("unavailable_reason"))),p(q57.get("str"))}))))))) {
            throw new Rejected(py(s("unavailable provider lacks reason")));
        }
        return dict(new Expansion(e.get("frame")),new Item(s("af5"),e.get("normalized_af5")),new Item(s("readiness"),call(e,"dict",args(new Part[]{p(e.get("readiness"))}))));
    }
}
