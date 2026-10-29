package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.finance.WarPaymentExtrasCodec;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.development.constructioneconomy.*;
import static org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.*;
import static org.xar.ck3.control.service.root.CashObservationPublicCodec.*;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Full original domain normalizers plus the existing economic classifier. No ACK is a financial effect. */
public final class CashObservationCodec {
    private CashObservationCodec() { }
    public static ObjectNode arguments(Request input) {
        ObjectNode n=StrictJson.object().put("expected_revision",input.expectedRevision());
        if(input instanceof Current c){put(n,"payment_sampling",c.sampling(),c.sampling().value().map(Sampling::wire));put(n,"payment_window_contract",c.window(),c.window().value().map(Window::wire));}
        else if(input instanceof Construction c)n.put("reserve_gold_raw",c.reserve()).put("existing_commitment_gold_raw",c.commitments()).put("horizon_months",c.horizonMonths());
        else {var t=(Termination)input;n.put("war_id",t.warId()).put("outcome",t.outcome().wire());}return n;
    }
    private static void put(ObjectNode n,String key,Nullable<?> presence,Optional<String> value){if(presence.presence()==Presence.NULL)n.putNull(key);else value.ifPresent(v->n.put(key,v));}
    static Response normalize(CashObservationReads.Selection selected,PlanningReadReceipt receipt) {
        var envelope=PublicDataJson.object(receipt.original().originalFrame());
        byte[] rawFrame=receipt.original().originalFrame().bytes();byte[] packet=receipt.original().originalPacket();
        require(packet.length==rawFrame.length+4&&java.nio.ByteBuffer.wrap(packet,0,4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt()==rawFrame.length
                &&Arrays.equals(Arrays.copyOfRange(packet,4,packet.length),rawFrame),"cash original packet/frame disagree");
        require(envelope.path("type").asText().equals("command_result")&&integer(envelope.get("protocol_version")).equals(BigInteger.ONE)
                &&envelope.path("request_id").asText().equals(receipt.requestId())&&truth(envelope.get("ok")),"cash original native envelope differs");
        ObjectNode result=object(envelope.get("result"));
        require(selected.operation().value().equals(text(result.get("step")))&&truth(result.get("accepted"))&&truth(result.get("private_build"))
                &&truth(result.get("read_only"))&&!truth(result.get("advertised")),"cash private native envelope malformed");
        RawJson snapshot=new RawJson(DriverJson.encode(selected.current().semantic()));ObjectNode observed;
        if(selected.input() instanceof Termination t)observed=termination(object(result.get("war_cash_termination_send_costs")),PublicDataJson.object(snapshot),t);
        else {
            var normalized=RawCashCodec.normalize(PublicDataJson.encode(object(result.get("war_cash_current_resources"))).bytes(),snapshot.bytes());
            observed=PublicDataJson.object(new RawJson(normalized.toJson()));metadata(observed,selected);
            Optional<WarPaymentExtrasCodec.Mode> mode=selected.input() instanceof Current c?c.sampling().value().map(x->WarPaymentExtrasCodec.Mode.valueOf(x.name())):Optional.empty();
            var extras=PublicDataJson.object(WarPaymentExtrasCodec.normalize(PublicDataJson.encode(result),snapshot,selected.current().source().machineId(),mode));
            final ObjectNode currentObserved=observed;
            extras.properties().forEach(e->currentObserved.set(e.getKey(),e.getValue()));
            if(selected.input() instanceof Construction c)observed=construction(observed,selected.actualAppliedMaterial().orElseThrow(),c);
        }
        if(selected.input() instanceof Termination)metadata(observed,selected);
        return new Response(PublicDataJson.encode(observed));
    }
    private static void metadata(ObjectNode n,CashObservationReads.Selection s){n.put("queried_snapshot_id",s.current().identity().frame().snapshotId())
            .put("queried_revision",s.current().identity().frame().revision()).put("queried_native_revision",s.current().identity().frame().identity().nativeRevision());}
    static ObjectNode termination(ObjectNode value,ObjectNode snapshot,Termination input) {
        String version=text(value.get("game_version")),sha=text(value.get("executable_sha256"));
        var hello=object(object(snapshot.get("diagnostics")).get("hello"));
        require(version.equals(text(hello.get("expected_ck3_version")))&&sha.equalsIgnoreCase(text(hello.get("expected_ck3_sha256"))),"termination costs belong to another exact native build");
        require(RawCashBuilds.matches(version,sha),"termination quote has unknown native build");
        require("xar.ck3.war-cash-termination-send-costs.v1".equals(text(value.get("schema")))&&truth(value.get("read_only"))&&!truth(value.get("advertised"))&&!truth(value.get("formal_action_ready")),"termination quote source flags malformed");
        require(integer(value.get("played_character_id")).equals(integer(object(snapshot.get("played_character")).get("character_id")))
                &&integer(value.get("snapshot_revision")).equals(integer(snapshot.get("native_revision")))&&integer(value.get("date_raw")).equals(integer(snapshot.get("date_raw"))),"termination quote crossed current actor/frame");
        require(integer(value.get("war_id")).equals(BigInteger.valueOf(input.warId()))&&input.outcome().wire().equals(text(value.get("outcome")))
                &&Set.of("available","unavailable").contains(text(value.get("status"))),"termination costs bound to another choice");
        ObjectNode send=object(value.get("generic_send_costs")),ready=object(value.get("readiness"));
        require(integer(send.get("raw_scale")).equals(BigInteger.valueOf(100000))&&text(send.get("payer_role")).equals("actor")
                &&text(send.get("application_timing")).equals("on_send")&&text(send.get("payment_state")).equals("not_yet_applied")
                &&!truth(ready.get("total_immediate_gold_cost_ready"))&&nil(value.get("special_outcome_gold_cost_raw"))&&nil(value.get("total_immediate_gold_cost_raw")),"generic fees cannot become complete applied costs");
        if(text(value.get("status")).equals("available")){var vector=send.get("resource_raw_native");require(vector!=null&&vector.isArray()&&vector.size()==10,"exact resource10 vector required");
            for(JsonNode item:vector)signed64(item);require(integer(send.get("gold_raw")).equals(integer(vector.get(0)))&&truth(ready.get("generic_send_costs_ready")),"termination vector/gold/readiness mismatch");}
        return value.deepCopy();
    }
    static ObjectNode construction(ObjectNode normalizedCash,RawJson actualMaterial,Construction input) {
        ObjectNode mathCash=withoutPayment(normalizedCash);
        var cash=ConstructionEconomyCodec.decodeCash(PublicDataJson.encode(mathCash).bytes());
        var policy=new BudgetPolicy(BigInteger.ZERO,input.reserve(),input.commitments(),input.horizonMonths());
        var projected=ConstructionEconomy.projectBudget(cash,policy);
        var budget=new Budget(projected.cash(),projected.policy(),projected.current(),projected.allRaised(),true);
        var withPost=PublicDataJson.object(actualMaterial).deepCopy();withPost.set("post_cash_v2",normalizedCash.deepCopy());
        var mathReceipt=withPost.deepCopy();mathReceipt.set("post_cash_v2",mathCash);
        if(mathReceipt.get("pre_cash_v2") instanceof ObjectNode pre)mathReceipt.set("pre_cash_v2",withoutPayment(pre));
        var receipt=ConstructionEconomyCodec.decodeReceipt(PublicDataJson.encode(mathReceipt).bytes());
        var outcome=ConstructionEconomy.classify(new OutcomeRequest(receipt,cash.frame().gameVersion(),Optional.empty(),Optional.empty()));
        var result=PublicDataJson.object(new RawJson(ConstructionEconomyCodec.encodeQueryOutcome(new QueryOutcome(budget,new CompletedFields(receipt,outcome)))));
        // Payment evidence is independently validated and does not enter cash arithmetic; retain it in the original public containers.
        object(result.get("current_cash_scenarios")).set("source_cash_resources",normalizedCash.deepCopy());result.set("material_receipt",withPost);
        return result;
    }
    private static ObjectNode withoutPayment(ObjectNode cash){var result=cash.deepCopy();result.remove(List.of("war_payment_observations_v1","war_payment_control_v1"));return result;}
    private static final Set<String> UNSIGNED=Set.of("revision","native_revision","snapshot_revision","queried_revision","queried_native_revision","connection_generation","capture_epoch","ticket_sequence","pump_epoch",
        "rng_wrapper","rng_state","tls_initialized_flag_address","tls_context","jomini_state","game_state","character_identity","context_identity","capture_sequence","execution_epoch","character","context_identity_before","context_identity_after");
    private static final Set<String> MONEY=Set.of("raw","gold_raw","treasury_raw","amount_raw","principal_quote_raw","existing_debt_principal_raw","funding_credit_raw","generic_interaction_cost_raw","total_declaration_cost_raw",
        "special_outcome_gold_cost_raw","total_immediate_gold_cost_raw","construction_gold_cost_raw","reserve_gold_raw","existing_commitment_gold_raw","net_monthly_gold_raw","cash_after_construction_and_commitments_raw","projected_ending_gold_raw",
        "burn_reservation_raw","minimum_projected_gold_raw","maximum_one_off_spend_raw","new_construction_spend_projected_raw","before_raw","after_raw","delta_raw","verified_construction_gold_debit_raw","personal_gold_residual_after_verified_debit_raw",
        "pre_player_monthly_gold_income_raw","observed_player_monthly_gold_income_raw","native_province_monthly_income_raw","stock_gold_cost_raw","gold_before_raw","post_player_gold_raw","value_2c0","value_2c8","value_28","value_30");
    private static final Set<String> VECTORS=Set.of("resource_raw_native","resource_costs_raw");
    public static RawJson publicWire(RawJson normalized) {ObjectNode value=PublicDataJson.object(normalized).deepCopy();project(value,false);return PublicDataJson.encode(value);}
    public static RawJson nativeWire(RawJson encoded) {ObjectNode value=PublicDataJson.object(encoded).deepCopy();project(value,true);RawJson result=PublicDataJson.encode(value);require(publicWire(result).equals(encoded),"noncanonical public cash representation");return result;}
    private static void project(JsonNode node,boolean restoring) {
        if(node instanceof ObjectNode object){ObjectNode extras=StrictJson.object();
            for(String key:List.of("war_payment_observations_v1","war_payment_control_v1"))if(object.has(key))extras.set(key,object.remove(key));
            var names=new java.util.ArrayList<String>();object.fieldNames().forEachRemaining(names::add);
            for(String key:names){JsonNode value=object.get(key);if(value.isNull())continue;
                if(UNSIGNED.contains(key)){if(restoring)object.put(key,PublicUnsigned64.parse(value,PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.DECIMAL_ONLY));else object.put(key,PublicUnsigned64.canonical(integer(value),PublicUnsigned64.Minimum.ZERO));}
                else if(MONEY.contains(key)){if(restoring)object.put(key,moneyDecimal(value));else object.put(key,integer(value).toString());}
                else if(VECTORS.contains(key)){require(value.isArray(),"money vector required");var array=(com.fasterxml.jackson.databind.node.ArrayNode)value;for(int i=0;i<array.size();i++){if(restoring)array.set(i,StrictJson.object().numberNode(moneyDecimal(array.get(i))));else array.set(i,StrictJson.object().textNode(integer(array.get(i)).toString()));}}
                else if(value.isIntegralNumber())require(value.bigIntegerValue().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"unclassified unsafe public cash integer: "+key);
                else project(value,restoring);
            }
            if(!extras.isEmpty())PublicDataJson.object(restoring?WarPaymentExtrasCodec.nativeWire(PublicDataJson.encode(extras)):WarPaymentExtrasCodec.publicWire(PublicDataJson.encode(extras)))
                    .properties().forEach(e->object.set(e.getKey(),e.getValue()));
        }else if(node.isArray())for(JsonNode value:node){if(value.isIntegralNumber())require(value.bigIntegerValue().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"unclassified unsafe public cash array integer");else project(value,restoring);}
    }
    private static BigInteger moneyDecimal(JsonNode value){require(value!=null&&value.isTextual()&&value.textValue().matches("0|-?[1-9][0-9]{0,127}"),"canonical exact signed cash decimal required");return new BigInteger(value.textValue());}
    static ObjectNode object(JsonNode n){require(n instanceof ObjectNode,"cash object missing/wrong type");return (ObjectNode)n;}
    static String text(JsonNode n){require(n!=null&&n.isTextual(),"cash text missing/wrong type");return n.textValue();}
    static BigInteger integer(JsonNode n){require(n!=null&&n.isIntegralNumber(),"cash integer required; bool/float invalid");return n.bigIntegerValue();}
    static boolean truth(JsonNode n){require(n!=null&&n.isBoolean(),"cash bool missing/wrong type");return n.booleanValue();}
    static boolean nil(JsonNode n){return n==null||n.isNull();}
    static void signed64(JsonNode n){BigInteger v=integer(n);require(v.bitLength()<=63,"signed native resource64 out of range");}
    private static final class RawCashBuilds {
        private static final java.util.Map<String,String> EXACT=java.util.Map.of(
            "1.19.0.6","2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            "1.20.0.2","AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
            "1.20.0.3","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
            "1.20.0.4","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        static boolean matches(String version,String sha){return EXACT.containsKey(version)&&EXACT.get(version).equalsIgnoreCase(sha);}
    }
}
