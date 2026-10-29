package org.xar.ck3.control.wave2.finance.holyloan;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.Available;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.Decision;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.Definition;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ExpectedFrame;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.Observation;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ObservedDecision;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.Unavailable;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.UnknownDecision;

/** Strict token entrance; native SDK objects are declared projections with permitted extensions. */
public final class HolyLoanCodec {
    public static final String NATIVE_SCHEMA = "ck3_12004_holy_order_loan_decision_costs_v1";
    public static final String SCHEMA = "xar.holy-order-loan-decision-observation.v1";
    public static final String VERSION = "1.20.0.4";
    public static final String SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Set<String> OUTPUT_FIELDS = Set.of("schema", "available", "unavailable_reason", "source",
            "raw_scale", "resource_slot_count", "borrow_decision", "repay_decision", "principal_quote_raw",
            "existing_debt_principal_raw", "repayment_total_outlay_raw", "complete_loan_terms", "submission_qualified",
            "received_funds_verified", "funding_credit_raw", "selected_action");
    private HolyLoanCodec() { }

    public static Observation project(byte[] nativeBytes, ExpectedFrame expected) {
        JsonNode node = object(StrictJson.parse(nativeBytes));
        require(NATIVE_SCHEMA.equals(text(node.get("schema"))), "unexpected loan decision schema");
        require(VERSION.equals(text(node.get("game_version"))) && SHA256.equalsIgnoreCase(text(node.get("executable_sha256"))),
                "loan decision source is not the exact .4 build");
        require(integer(node.get("played_character_id"), 1, Integer.MAX_VALUE) == expected.playedCharacterId()
                && integer(node.get("date_raw"), 0, Integer.MAX_VALUE) == expected.dateRaw()
                && StrictJson.integer(node.get("capture_epoch"), BigInteger.ONE, HolyLoanModel.UINT64_MAX).equals(expected.captureEpoch()),
                "loan decision differs from owner actor/date/capture epoch");
        require(is(node, "read_only", true) && "decision_gates_and_costs_only".equals(text(node.get("scope")))
                && integer(node.get("raw_scale"), 100000, 100000) == 100000
                && integer(node.get("resource_slot_count"), 10, 10) == 10, "loan decision scope/resource layout differs");
        require(is(node, "complete_loan_terms", false) && nil(node.get("principal_quote_raw")) && nil(node.get("typed_debt"))
                && integer(node.get("funding_credit_raw"), 0, 0) == 0 && is(node, "submit_planned", false),
                "decision-cost source cannot assert principal, debt, action or received money");
        boolean available = bool(node.get("available"));
        String reason = available ? null : text(node.get("unavailable_reason"));
        require(!available || nil(node.get("unavailable_reason")), "available source carries unavailable reason");
        return new Observation(expected, available ? new Available() : new Unavailable(reason),
                decision(node.get("borrow_decision"), Definition.BORROW, available, false),
                decision(node.get("repay_decision"), Definition.REPAY, available, false));
    }

    public static ExpectedFrame decodeExpectedFrame(byte[] bytes) {
        JsonNode node = StrictJson.object(StrictJson.parse(bytes), Set.of("played_character_id", "date_raw", "capture_epoch"));
        return new ExpectedFrame((int) integer(node.get("played_character_id"), 1, Integer.MAX_VALUE),
                (int) integer(node.get("date_raw"), 0, Integer.MAX_VALUE),
                StrictJson.integer(node.get("capture_epoch"), BigInteger.ONE, HolyLoanModel.UINT64_MAX));
    }

    /** Strict persistence validation; a decoded observation still grants no native action qualification. */
    public static Observation decodeObservation(byte[] bytes) {
        JsonNode node = StrictJson.object(StrictJson.parse(bytes), OUTPUT_FIELDS);
        require(SCHEMA.equals(text(node.get("schema"))), "projected loan schema differs");
        JsonNode source = StrictJson.object(node.get("source"), Set.of("game_version", "executable_sha256",
                "played_character_id", "date_raw", "capture_epoch"));
        require(VERSION.equals(text(source.get("game_version"))) && SHA256.equals(text(source.get("executable_sha256"))),
                "projected source build differs");
        ExpectedFrame frame = new ExpectedFrame((int) integer(source.get("played_character_id"), 1, Integer.MAX_VALUE),
                (int) integer(source.get("date_raw"), 0, Integer.MAX_VALUE),
                StrictJson.integer(source.get("capture_epoch"), BigInteger.ONE, HolyLoanModel.UINT64_MAX));
        require(integer(node.get("raw_scale"), 100000, 100000) == 100000
                && integer(node.get("resource_slot_count"), 10, 10) == 10, "projected resource layout differs");
        for (String name : List.of("principal_quote_raw", "existing_debt_principal_raw", "repayment_total_outlay_raw", "selected_action")) {
            require(node.has(name) && node.get(name).isNull(), "unobserved value must remain explicit null: " + name);
        }
        for (String name : List.of("complete_loan_terms", "submission_qualified", "received_funds_verified")) {
            require(is(node, name, false), "loan projection cannot assert " + name);
        }
        require(integer(node.get("funding_credit_raw"), 0, 0) == 0, "unreceived funding cannot be credited");
        boolean available = bool(node.get("available"));
        String reason = available ? null : text(node.get("unavailable_reason"));
        require(!available || node.get("unavailable_reason").isNull(), "projected availability reason differs");
        return new Observation(frame, available ? new Available() : new Unavailable(reason),
                decision(node.get("borrow_decision"), Definition.BORROW, available, true),
                decision(node.get("repay_decision"), Definition.REPAY, available, true));
    }

    public static byte[] encode(Observation observation) {
        ObjectNode node = StrictJson.object(); node.put("schema", SCHEMA);
        boolean available = observation.availability() instanceof Available;
        node.put("available", available);
        if (observation.availability() instanceof Unavailable unavailable) { node.put("unavailable_reason", unavailable.reason()); }
        else { node.putNull("unavailable_reason"); }
        ObjectNode source = node.putObject("source"); source.put("game_version", VERSION); source.put("executable_sha256", SHA256);
        source.put("played_character_id", observation.source().playedCharacterId()); source.put("date_raw", observation.source().dateRaw());
        source.put("capture_epoch", observation.source().captureEpoch()); node.put("raw_scale", 100000); node.put("resource_slot_count", 10);
        node.set("borrow_decision", encodeDecision(observation.borrowDecision())); node.set("repay_decision", encodeDecision(observation.repayDecision()));
        node.putNull("principal_quote_raw"); node.putNull("existing_debt_principal_raw"); node.putNull("repayment_total_outlay_raw");
        node.put("complete_loan_terms", false); node.put("submission_qualified", false); node.put("received_funds_verified", false);
        node.put("funding_credit_raw", 0); node.putNull("selected_action"); return StrictJson.canonical(node, 16384);
    }

    private static Decision decision(JsonNode value, Definition definition, boolean available, boolean projected) {
        JsonNode node = object(value);
        if (projected) { StrictJson.object(node, Set.of("decision_id", "is_shown", "can_take", "affordable",
                "native_gates_allow_decision", "declared_costs_raw_by_native_index")); }
        require(definition.wire().equals(text(node.get("decision_id"))), "loan decision definition identity differs");
        String costsKey = projected ? "declared_costs_raw_by_native_index" : "costs_raw_by_native_index";
        if (!available) {
            for (String key : List.of("is_shown", "can_take", "affordable", costsKey)) {
                require(nil(node.get(key)), "unavailable loan source carries observed gates/costs");
            }
            if (projected) { require(node.get("native_gates_allow_decision").isNull(), "unknown decision cannot have final gate"); }
            return new UnknownDecision(definition);
        }
        boolean shown = bool(node.get("is_shown")), canTake = bool(node.get("can_take")), affordable = bool(node.get("affordable"));
        JsonNode costs = node.get(costsKey); require(costs != null && costs.isArray() && costs.size() == 10, "ten native slots required");
        List<Long> raw = new ArrayList<>(); for (JsonNode cost : costs) { raw.add(integer(cost, Long.MIN_VALUE, Long.MAX_VALUE)); }
        ObservedDecision result = new ObservedDecision(definition, shown, canTake, affordable, raw);
        if (projected) { require(bool(node.get("native_gates_allow_decision")) == result.nativeGatesAllowDecision(), "final native gate differs"); }
        return result;
    }
    private static ObjectNode encodeDecision(Decision decision) {
        ObjectNode node = StrictJson.object(); node.put("decision_id", decision.definition().wire());
        if (decision instanceof ObservedDecision observed) {
            node.put("is_shown", observed.shown()); node.put("can_take", observed.canTake()); node.put("affordable", observed.affordable());
            node.put("native_gates_allow_decision", observed.nativeGatesAllowDecision());
            var costs = node.putArray("declared_costs_raw_by_native_index"); observed.declaredCostsRaw().forEach(costs::add);
        } else {
            for (String key : List.of("is_shown", "can_take", "affordable", "native_gates_allow_decision", "declared_costs_raw_by_native_index")) {
                node.putNull(key);
            }
        }
        return node;
    }
    private static JsonNode object(JsonNode node) { require(node != null && node.isObject(), "loan object required"); return node; }
    private static String text(JsonNode node) { return StrictJson.text(node); }
    private static long integer(JsonNode node, long minimum, long maximum) { return StrictJson.integer(node, minimum, maximum); }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "actual boolean token required"); return node.booleanValue(); }
    private static boolean is(JsonNode node, String key, boolean expected) { JsonNode value = node.get(key); return value != null && value.isBoolean() && value.booleanValue() == expected; }
    private static boolean nil(JsonNode value) { return value == null || value.isNull(); }
    private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}
