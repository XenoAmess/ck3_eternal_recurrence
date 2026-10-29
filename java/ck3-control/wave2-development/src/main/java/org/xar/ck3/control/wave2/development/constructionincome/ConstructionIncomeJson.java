package org.xar.ck3.control.wave2.development.constructionincome;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.ConstructionInputValidation;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionIncomeConsumers.PriorObservedDate;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionIncomeConsumers.PriorReceipt;
import org.xar.ck3.control.wave2.development.constructionincome.SameFrameConstructionIncome.Frame;
import org.xar.ck3.control.wave2.development.constructionincome.SameFrameConstructionIncome.HistoryRow;
import org.xar.ck3.control.wave2.development.constructionincome.SameFrameConstructionIncome.Income;
import org.xar.ck3.control.wave2.development.constructionincome.SameFrameConstructionIncome.RootContext;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Evidence;

/** Typed projection of relevant old history rows, leaving unrelated command payloads opaque. */
public final class ConstructionIncomeJson {
    public static final String SCHEMA = "xar.ck3.construction-income-java-request/v1";
    public static final int MAX_BYTES = 1_048_576;
    private ConstructionIncomeJson() { }

    public static byte[] project(byte[] raw) {
        ObjectNode request = object(StrictJson.parse(raw, MAX_BYTES));
        StrictJson.require(SCHEMA.equals(StrictJson.text(request.get("schema"))), "income request schema mismatch");
        String operation = StrictJson.text(request.get("operation"));
        ConstructionIncomeConsumers.StartingSample sample;
        if ("observe".equals(operation)) {
            StrictJson.object(request, Set.of("schema", "operation", "snapshot", "history"));
            sample = ConstructionIncomeConsumers.sampleStarting(frame(request.get("snapshot")), history(request.get("history")));
        } else if ("receipt_income".equals(operation)) {
            StrictJson.object(request, Set.of("schema", "operation", "snapshot", "history", "prior_receipt",
                    "cold_recheck", "completed"));
            sample = ConstructionIncomeConsumers.sampleStarting(frame(request.get("snapshot")), history(request.get("history")));
        } else {
            StrictJson.require("receipt_income_sample".equals(operation), "unknown income operation");
            StrictJson.object(request, Set.of("schema", "operation", "snapshot", "observation", "prior_receipt",
                    "cold_recheck", "completed"));
            JsonNode observation = request.get("observation");
            ConstructionInputValidation.check(() -> StrictJson.require(observation != null && observation.isArray() && observation.size() == 2,
                    "starting income observation must retain its boolean and scalar pair"));
            boolean observed = ConstructionInputValidation.read(() -> bool(observation.get(0)));
            BigInteger observedIncome = ConstructionInputValidation.read(() -> integer(observation.get(1)));
            ConstructionInputValidation.check(() -> StrictJson.require(observed || observedIncome == null,
                    "an absent public root has no observed income"));
            sample = new ConstructionIncomeConsumers.StartingSample(frame(request.get("snapshot")),
                    new SameFrameConstructionIncome.Observation(observed
                            ? SameFrameConstructionIncome.RootObservation.OBSERVED
                            : SameFrameConstructionIncome.RootObservation.NOT_OBSERVED, observedIncome));
        }
        if ("observe".equals(operation)) {
            ArrayNode out = StrictJson.object().arrayNode();
            out.add(sample.observation().rootObservation() == SameFrameConstructionIncome.RootObservation.OBSERVED);
            out.add(sample.observation().incomeRaw());
            return StrictJson.canonical(out);
        }
        ObjectNode prior = object(request.get("prior_receipt"));
        var result = ConstructionIncomeConsumers.receiptIncome(sample,
                new PriorReceipt(text(prior.get("completion_status")), integer(prior.get("observed_player_monthly_gold_income_raw")),
                        new PriorObservedDate(prior.has("income_observed_date_raw"), integer(prior.get("income_observed_date_raw"))),
                        integer(prior.get("post_date_raw"))), bool(request.get("cold_recheck")), bool(request.get("completed")));
        ArrayNode out = StrictJson.object().arrayNode();
        out.add(result.observedIncomeRaw());
        out.add(result.incomeObservedDateRaw());
        return StrictJson.canonical(out);
    }

    public static Frame frame(JsonNode raw) {
        ObjectNode snapshot = object(raw);
        ObjectNode played = nullableObject(snapshot.get("played_character"));
        return new Frame(integer(snapshot.get("native_revision")), integer(snapshot.get("date_raw")),
                played == null ? null : integer(played.get("character_id")));
    }

    public static List<HistoryRow> history(JsonNode raw) {
        StrictJson.require(raw instanceof ArrayNode, "income history array required");
        List<HistoryRow> rows = new ArrayList<>();
        for (JsonNode value : raw) {
            ObjectNode row = object(value);
            JsonNode commandValue = row.get("command");
            // The original observer short-circuits unrelated rows before touching ok/result.
            // Their payload remains opaque, including values outside this operation's root contract.
            if (commandValue == null || !commandValue.isTextual()
                    || !SameFrameConstructionIncome.ROOT_QUERY_STEP.equals(commandValue.textValue())) {
                rows.add(new HistoryRow(null, Evidence.UNKNOWN, null));
                continue;
            }
            String command = commandValue.textValue();
            Evidence ok = evidence(row.get("ok"));
            RootContext root = null;
            if (SameFrameConstructionIncome.ROOT_QUERY_STEP.equals(command) && ok == Evidence.TRUE) {
                ObjectNode result = nullableObject(row.get("result"));
                ObjectNode context = result == null ? null : nullableObject(result.get("campaign_root_context"));
                if (context != null) {
                    ObjectNode money = nullableObject(context.get("player_monthly_gold_income"));
                    root = new RootContext(text(context.get("status")), new Frame(integer(context.get("snapshot_revision")),
                            integer(context.get("date_raw")), integer(context.get("player_character_id"))),
                            money == null ? null : new Income(integer(money.get("raw")), integer(money.get("scale"))));
                }
            }
            rows.add(new HistoryRow(command, ok, root));
        }
        return List.copyOf(rows);
    }

    private static ObjectNode nullableObject(JsonNode value) { return value == null || value.isNull() ? null : object(value); }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "income object required");
        return (ObjectNode) value;
    }
    private static String text(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isTextual(), "income text must be string or null");
        return value.textValue().isEmpty() ? "" : StrictJson.text(value);
    }
    private static BigInteger integer(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isIntegralNumber(), "income exact integer required");
        return value.bigIntegerValue();
    }
    private static Evidence evidence(JsonNode value) {
        if (value == null || value.isNull()) { return Evidence.UNKNOWN; }
        return Evidence.of(bool(value));
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "income exact boolean required");
        return value.booleanValue();
    }
}
