package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashCodec;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.CashContext;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.QuoteRow;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Read;
import org.xar.ck3.control.wave3.planning.warpriorityfocus.WarCashFocusProjectionCodec;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;

import static org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.*;

/** The new envelope is strict; original native context uses the shared projected cash contract. */
public final class WartimeConstructionCodec {
    public static final String SCHEMA = "xar.wartime-construction-cash-input.v1";
    public static final int MAX_BYTES = 65_536;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final Set<String> FIELDS = Set.of("schema", "snapshot", "kind", "construction_gold_raw", "root", "spending",
            "market", "market_source_frame", "mercenary_ledger", "procurement_decision");
    private WartimeConstructionCodec() { }
    /** Opaque original-context request, validated by the real focus codec only at its original consumer stage. */
    public static final class FocusRequest {
        private final byte[] context;
        private FocusRequest(byte[] context) { this.context = context.clone(); }
        public WarCashFocusProjectionCodec.Request decodeRequired() { return WarCashFocusProjectionCodec.decode(context); }
    }

    public static Input decode(byte[] bytes) {
        ObjectNode input = StrictJson.object(parse(bytes), FIELDS);
        if (!SCHEMA.equals(text(input.get("schema")))) throw new IllegalArgumentException("wartime construction schema");
        ObjectNode shared = JSON.createObjectNode(); shared.put("schema", "xar.native-spending-context.v1");
        for (String field : List.of("snapshot", "root", "spending", "market", "market_source_frame", "mercenary_ledger"))
            shared.set(field, input.get(field));
        // This parser returns observed context only. It never creates a gift candidate or runs the gift gate.
        CashContext context = GiftWarCashCodec.decodeCashContext(bytes(shared));
        List<QuoteEvidence> quotes = new ArrayList<>();
        MarketShape shape = MarketShape.MISSING;
        JsonNode rows = input.path("market").get("rows");
        if (rows != null && rows.isArray()) {
            shape = rows.isEmpty() ? MarketShape.EMPTY : MarketShape.NONEMPTY;
            List<QuoteRow> parsed = context.market().value().rows().value();
            int index = 0;
            for (JsonNode row : rows) {
                if (!row.isObject()) continue;
                boolean groups = row.path("final_terms").isObject() && row.path("troop_strength").isObject()
                        && row.path("location").isObject() && row.path("readiness_v1").isObject();
                quotes.add(new QuoteEvidence(parsed.get(index++), groups ? GroupShape.ALL_OBJECTS : GroupShape.INCOMPLETE));
            }
        }
        ObjectNode focus = JSON.createObjectNode(); focus.put("schema", "xar.war-cash-focus.request.v1");
        focus.set("snapshot", input.get("snapshot")); focus.set("campaign_root", input.get("root"));
        return new Input(text(input.get("kind")), read(input, "construction_gold_raw", WartimeConstructionCodec::integer), context,
                quotes, shape, read(input, "procurement_decision", WartimeConstructionCodec::procurement),
                new FocusRequest(bytes(focus)));
    }

    private static ProcurementCandidate procurement(JsonNode value) {
        object(value, "procurement_decision");
        JsonNode selected = value.get("selected_candidate");
        if (selected == null || selected.isNull()) return new ProcurementCandidate(false, Read.missing(), Read.missing(), Read.missing(), Read.missing());
        object(selected, "selected_candidate");
        JsonNode rejected = selected.get("rejection_reasons");
        if (rejected != null && !rejected.isNull() && !rejected.isArray()) throw new IllegalArgumentException("rejection reasons array");
        boolean empty = rejected != null && rejected.isArray() && rejected.isEmpty();
        JsonNode finance = selected.get("finance");
        if (finance != null && !finance.isNull()) object(finance, "procurement finance");
        Read<FinanceFrame> frame = read(finance, "source_frame", source -> {
            object(source, "procurement finance frame"); Set<String> fields = new HashSet<>(); source.fieldNames().forEachRemaining(fields::add);
            return new FinanceFrame(read(source, "actor_character_id", WartimeConstructionCodec::integer),
                    read(source, "native_revision", WartimeConstructionCodec::integer), read(source, "date_raw", WartimeConstructionCodec::integer),
                    fields.equals(Set.of("actor_character_id", "native_revision", "date_raw")));
        });
        return new ProcurementCandidate(empty, frame, read(selected, "purpose_war_ids", source -> {
            if (!source.isArray()) throw new IllegalArgumentException("procurement purpose wars array");
            List<BigInteger> result = new ArrayList<>(); for (JsonNode identity : source) result.add(integer(identity)); return List.copyOf(result);
        }), read(selected, "company_id", WartimeConstructionCodec::integer), read(selected, "gold_cost_raw", WartimeConstructionCodec::integer));
    }

    public static byte[] encode(Decision decision) {
        ObjectNode result = JSON.createObjectNode(); result.put("schema", "xar.wartime-construction-cash.v1");
        result.put("construction_kind", decision.kindWire()); result.set("source_frame", GiftWarCashCodec.encodeFrame(decision.frame()));
        result.put("new_spend_allowed", decision.newSpendAllowed()); number(result, "construction_gold_raw", decision.quotedCost());
        result.put("thresholds_are_user_hard_limits", false); result.put("thresholds_are_native_rules", false);
        result.put("future_income_credited_raw", 0); result.put("loan_or_refund_credited_raw", 0);
        result.put("does_not_open_or_refresh_mercenary_procurement_epoch", true); result.put("status", decision.status().wire());
        decision.reason().ifPresent(reason -> result.put("reason", reason.wire()));
        decision.marketEmpty().ifPresent(empty -> result.put("market_observation", empty ? "complete_empty" : "complete_collection_with_rows"));
        decision.comparisons().ifPresent(rows -> {
            var array = result.putArray("mercenary_quote_comparisons"); for (Comparison row : rows) array.add(comparison(row));
        });
        decision.reserve().ifPresent(reserve -> {
            result.put("observed_treasury_raw", reserve.treasury()); result.put("gold_after_construction_raw", reserve.afterConstruction());
            result.put("required_remaining_gold_raw", reserve.required()); result.put("maximum_monthly_military_raw", reserve.maximumMaintenance());
            result.put("maintenance_policy_months", WartimeConstructionCash.MAXIMUM_MAINTENANCE_MONTHS);
            result.put("fixed_buffer_policy_gold_raw", WartimeConstructionCash.FIXED_BUFFER); result.put("military_buffer_raw", reserve.militaryBuffer());
            result.put("existing_unpaid_commitments_raw", reserve.commitments()); result.set("emergency_company_quote", comparison(reserve.selected()));
            result.put("emergency_quote_reserve_policy", reserve.basis().wire());
            if (reserve.focusedWar().isPresent()) result.put("focused_war_id", reserve.focusedWar().orElseThrow()); else result.putNull("focused_war_id");
            if (reserve.observedDeficit().isPresent()) result.put("observed_focused_headcount_deficit", reserve.observedDeficit().orElseThrow()); else result.putNull("observed_focused_headcount_deficit");
            result.putNull("arrival_eta_days"); result.putNull("battle_win_probability"); result.put("quoted_company_arrival_or_combat_usefulness_verified", false);
            result.put("paid_contracts_already_reflected_in_current_wallet_not_deducted_twice", true);
        });
        return bytes(result);
    }
    private static ObjectNode comparison(Comparison row) {
        ObjectNode result = JSON.createObjectNode(); number(result, "company_id", row.companyId()); result.put("usable", row.usable());
        if (row.completeGroups()) {
            if (row.contractGold().isPresent()) result.put("contract_gold_raw", row.contractGold().orElseThrow()); else result.putNull("contract_gold_raw");
            number(result, "current_soldiers", row.soldiers());
        }
        result.put("reason", row.reason().wire()); return result;
    }
    private static JsonNode parse(byte[] raw) {
        if (raw == null || raw.length == 0 || raw.length > MAX_BYTES) throw new IllegalArgumentException("wartime construction byte budget");
        try {
            String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode result = JSON.readTree(value); if (result == null) throw new IllegalArgumentException("empty JSON"); return result;
        } catch (IOException failure) { throw new IllegalArgumentException("invalid wartime construction JSON", failure); }
    }
    private static byte[] bytes(JsonNode value) {
        try {
            byte[] result = JSON.writeValueAsBytes(value); if (result.length > MAX_BYTES) throw new IllegalArgumentException("wartime construction output budget"); return result;
        } catch (IOException failure) { throw new IllegalStateException("wartime construction encoding", failure); }
    }
    private static BigInteger integer(JsonNode value) {
        if (value == null || !value.isIntegralNumber()) throw new IllegalArgumentException("integer token required, no bool/float/string");
        return value.bigIntegerValue();
    }
    private static String text(JsonNode value) {
        if (value == null || !value.isTextual()) throw new IllegalArgumentException("string token required");
        String result = value.textValue(); if (!result.isEmpty()) StrictJson.text(result); return result;
    }
    private static void object(JsonNode value, String field) {
        if (value == null || !value.isObject()) throw new IllegalArgumentException(field + " object required");
    }
    private static <T> Read<T> read(JsonNode source, String field, Function<JsonNode, T> parser) {
        JsonNode value = source == null ? null : source.get(field);
        return value == null ? Read.missing() : value.isNull() ? Read.nil() : Read.of(parser.apply(value));
    }
    private static void number(ObjectNode target, String field, Read<BigInteger> value) {
        if (value.known()) target.put(field, value.value()); else target.putNull(field);
    }
}
