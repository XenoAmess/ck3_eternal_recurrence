package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilModels;

/** Explicit public scalar roles. Native receipts, archives and the strict native decoders retain their original numeric domain. */
public final class GovernancePublicWire {
    private static final BigInteger SAFE=BigInteger.valueOf(9_007_199_254_740_991L);
    private GovernancePublicWire() { }

    /** Safe JSON integers remain accepted; full-width values require canonical decimal text. */
    public static BigInteger unsigned64(JsonNode token,boolean positive) {
        StrictJson.require(token!=null,"required public uint64 is missing");BigInteger value;
        if(token.isTextual()) {
            String text=token.textValue();StrictJson.require(text.matches("0|[1-9][0-9]{0,19}"),"canonical public uint64 decimal string required");
            value=new BigInteger(text);
        }else {
            StrictJson.require(token.isIntegralNumber(),"public uint64 must be a safe integer or canonical decimal string");
            value=token.bigIntegerValue();StrictJson.require(value.signum()>=0&&value.compareTo(SAFE)<=0,"unsafe public numeric uint64 requires decimal string");
        }
        CouncilModels.uint64(value,positive);return value;
    }

    static RawJson council(ObjectNode nativeResult) {
        var result=nativeResult.deepCopy();common(result);
        var request=object(result.get("request"));unsigned(request,"public_revision");unsigned(request,"native_revision");
        councilPayload(object(result.get("council_composition_candidates")));
        return encoded(result);
    }
    static RawJson development(ObjectNode nativeResult) {
        var result=nativeResult.deepCopy();common(result);
        var source=object(result.get("source"));unsigned(source,"revision");unsigned(source,"native_revision");
        var binding=object(result.get("binding"));for(String field:List.of("revision","native_revision","expected_revision"))unsigned(binding,field);
        developmentPayload(object(result.get("steward_develop_county_candidates")));
        return encoded(result);
    }
    static RawJson councilExecution(ObjectNode normalizedResult) {
        var result=normalizedResult.deepCopy();common(result);
        councilPayload(object(result.get("council_composition_candidates")));
        return encoded(result);
    }
    static RawJson developmentExecution(ObjectNode normalizedResult) {
        var result=normalizedResult.deepCopy();common(result);developmentPayload(object(result.get("steward_develop_county_candidates")));
        return encoded(result);
    }
    private static void councilPayload(ObjectNode payload) {
        var snapshot=object(payload.get("snapshot"));unsigned(snapshot,"public_revision");unsigned(snapshot,"native_revision");
        var position=object(payload.get("position"));var tax=position.get("current_task_owner_domain_tax_mult_v1");
        if(tax!=null&&!tax.isNull())fixed(object(tax).get("value"));
    }
    private static void developmentPayload(ObjectNode payload) {
        unsigned(payload,"snapshot_revision");
        for(String field:List.of("steward_increase_development_value_raw","current_gold_raw"))if(payload.has(field)&&!payload.get(field).isNull())signed(payload,field);
        var current=payload.get("current_active_task_binding");
        if(current!=null&&!current.isNull()) {
            var progress=object(object(current).get("progress"));fixed(progress.get("current"));fixed(progress.get("maximum"));
        }
        var candidates=payload.get("candidates");StrictJson.require(candidates!=null&&candidates.isArray(),"validated development candidate array required");
        for(JsonNode candidate:candidates) {
            var row=object(candidate);
            if(row.has("monthly_development_rate")) {
                fixed(row.get("monthly_development_rate"));var progress=object(row.get("development_progress"));fixed(progress.get("current"));fixed(progress.get("maximum"));
            }
            for(String field:List.of("development_progress_raw","monthly_development_rate_raw"))if(row.has(field))signed(row,field);
        }
    }
    private static void common(ObjectNode result) {
        for(String field:List.of("query_sequence","snapshot_revision","queried_revision","queried_native_revision"))unsigned(result,field);
    }
    private static void unsigned(ObjectNode row,String field) {
        JsonNode token=row.get(field);StrictJson.require(token!=null&&token.isIntegralNumber(),"validated native uint64 number required at public projection: "+field);
        BigInteger exact=token.bigIntegerValue();CouncilModels.uint64(exact,false);row.put(field,exact.toString());
    }
    private static void fixed(JsonNode value) {if(value!=null&&!value.isNull())signed(object(value),"raw");}
    private static void signed(ObjectNode row,String field) {
        JsonNode token=row.get(field);StrictJson.require(token!=null&&token.isIntegralNumber(),"validated native signed64 number required: "+field);
        BigInteger value=token.bigIntegerValue();StrictJson.require(value.compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&value.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"native signed64 range mismatch");
        row.put(field,value.toString());
    }
    private static ObjectNode object(JsonNode value) {StrictJson.require(value instanceof ObjectNode,"validated public projection object required");return (ObjectNode)value;}
    private static RawJson encoded(ObjectNode result) {requireSafeRemaining(result);return new RawJson(StrictJson.canonical(result));}
    private static void requireSafeRemaining(JsonNode node) {
        if(node.isIntegralNumber())StrictJson.require(node.bigIntegerValue().abs().compareTo(SAFE)<=0,"undeclared public numeric integer exceeds the safe range");
        if(node.isContainerNode())for(JsonNode child:node)requireSafeRemaining(child);
    }
}
