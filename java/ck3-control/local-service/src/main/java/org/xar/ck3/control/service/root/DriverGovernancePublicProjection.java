package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;

/** Enumerated public width paths for original private governance values. Native/archive numbers are never rewritten. */
public final class DriverGovernancePublicProjection {
    public enum Shape { COUNCIL,CROWN,FINAL_TERMS,GOVERNMENT }
    private DriverGovernancePublicProjection() { }
    public static RawJson output(RawJson nativeValue,Shape shape) {return project(nativeValue,shape,false);}
    public static RawJson input(RawJson publicValue,Shape shape) {return project(publicValue,shape,true);}
    private static RawJson project(RawJson original,Shape shape,boolean incoming) {
        var node=CouncilCodec.object(StrictJson.parse(original.bytes())).deepCopy();
        wide(node,incoming,"query_sequence","snapshot_revision","native_revision","native_snapshot_revision","proof_epoch","queried_revision","queried_native_revision",
                "pre_public_revision","pre_native_revision","pre_proof_epoch","post_public_revision","post_native_revision","post_proof_epoch");
        if(node.get("source_frame") instanceof ObjectNode source)wide(source,incoming,"revision","native_revision");
        if(shape==Shape.COUNCIL) {
            council(node.get("council_composition_candidates"),incoming);
            if(node.get("council_final_gates") instanceof ObjectNode gates)council(gates.get("council_composition_candidates"),incoming);
            for(String key:List.of("council_assign_councillor_ack","council_assign_councillor_receipt","request"))if(node.get(key) instanceof ObjectNode value)
                wide(value,incoming,"public_revision","native_revision","expected_public_revision","expected_native_revision","pre_public_revision","pre_native_revision","post_public_revision","post_native_revision");
        }
        if(shape==Shape.CROWN) {
            for(JsonNode resource:rows(node,"resources"))signed(CouncilCodec.object(resource),incoming,"amount_raw");
            for(JsonNode candidate:rows(node,"candidates"))for(JsonNode cost:rows(CouncilCodec.object(candidate),"costs"))signed(CouncilCodec.object(cost),incoming,"cost_raw");
            for(JsonNode charge:rows(node,"charges"))signed(CouncilCodec.object(charge),incoming,"cost_raw","pre_balance_raw","post_balance_raw");
        }
        if(shape==Shape.FINAL_TERMS)for(JsonNode group:rows(node,"groups"))for(JsonNode candidate:rows(CouncilCodec.object(group),"candidates")) {
            var row=CouncilCodec.object(candidate);if(row.get("cost_raw") instanceof ArrayNode costs)for(int i=0;i<costs.size();i++)costs.set(i,scalar(costs.get(i),incoming,true));
            if(row.get("succession_profile") instanceof ObjectNode profile)signed(profile,incoming,"primary_heir_minimum_share_raw");
        }
        if(!incoming)safe(node);return new RawJson(StrictJson.canonical(node));
    }
    private static void council(JsonNode value,boolean incoming) {
        if(!(value instanceof ObjectNode payload))return;
        if(payload.get("snapshot") instanceof ObjectNode snapshot)wide(snapshot,incoming,"public_revision","native_revision");
        if(payload.get("position") instanceof ObjectNode position&&position.get("current_task_owner_domain_tax_mult_v1") instanceof ObjectNode tax
                &&tax.get("value") instanceof ObjectNode fixed)signed(fixed,incoming,"raw");
    }
    private static Iterable<JsonNode> rows(ObjectNode node,String field) {
        if(!node.has(field))return List.of();StrictJson.require(node.get(field).isArray(),"validated native array required: "+field);return node.get(field);
    }
    private static void wide(ObjectNode node,boolean incoming,String...fields) {for(String field:fields)if(node.has(field)&&!node.get(field).isNull())node.set(field,scalar(node.get(field),incoming,false));}
    private static void signed(ObjectNode node,boolean incoming,String...fields) {for(String field:fields)if(node.has(field)&&!node.get(field).isNull())node.set(field,scalar(node.get(field),incoming,true));}
    private static JsonNode scalar(JsonNode token,boolean incoming,boolean signed) {
        BigInteger value;
        if(incoming) {
            if(!signed)value=PublicUnsigned64.parse(token,PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);
            else {
                if(token.isTextual()) {StrictJson.require(token.textValue().matches("0|-?[1-9][0-9]{0,18}"),"canonical signed64 public string required");value=new BigInteger(token.textValue());}
                else {StrictJson.require(token.isIntegralNumber()&&token.bigIntegerValue().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"safe numeric signed64 or decimal string required");value=token.bigIntegerValue();}
            }
        } else {StrictJson.require(token.isIntegralNumber(),"native width projection requires its original integer token");value=token.bigIntegerValue();}
        if(signed)StrictJson.require(value.compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&value.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"signed64 public range mismatch");
        else PublicUnsigned64.canonical(value,PublicUnsigned64.Minimum.ZERO);
        return incoming?com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(value):com.fasterxml.jackson.databind.node.TextNode.valueOf(value.toString());
    }
    private static void safe(JsonNode node) {
        if(node.isIntegralNumber())StrictJson.require(node.bigIntegerValue().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"undeclared unsafe governance public numeric field");
        if(node.isContainerNode())for(JsonNode child:node)safe(child);
    }
}
