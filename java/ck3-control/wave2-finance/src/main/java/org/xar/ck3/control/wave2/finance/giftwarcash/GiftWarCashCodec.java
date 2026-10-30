package org.xar.ck3.control.wave2.finance.giftwarcash;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.BudgetFrame;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Candidate;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.CashContext;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Choice;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Decision;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.EmergencyQuote;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.FrameRead;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.GiftObservation;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Market;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Presence;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.QuoteRow;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Read;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Reason;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Request;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Reserve;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Root;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Snapshot;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.SourceFrame;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Spending;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Status;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Treasury;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.War;

/** Bounded UTF-8/token boundary. SDK containers are declared projections, never domain JSON trees. */
public final class GiftWarCashCodec {
    public static final String SCHEMA = "xar.gift-war-cash-input.v1";
    private static final Set<String> FRAME_FIELDS = Set.of("played_character_id", "native_revision", "date_raw",
            "snapshot_id", "revision", "episode_run_id");
    private static final Set<String> BUDGET_FRAME_FIELDS = Set.of("actor_character_id", "native_revision", "date_raw", "snapshot_id");
    private GiftWarCashCodec() { }

    public static Request decode(byte[] bytes) {
        ObjectNode node = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "snapshot", "candidate",
                "root", "spending", "market", "market_source_frame", "mercenary_ledger"));
        StrictJson.require(SCHEMA.equals(text(node.get("schema"))), "unsupported gift wartime cash schema");
        return new Request(snapshot(object(node.get("snapshot"))), read(node, "candidate", GiftWarCashCodec::candidate),
                read(node, "root", GiftWarCashCodec::root), read(node, "spending", GiftWarCashCodec::spending),
                read(node, "market", GiftWarCashCodec::market), read(node, "market_source_frame", GiftWarCashCodec::frameRead),
                read(node, "mercenary_ledger", GiftWarCashCodec::validatedMercenaryPending));
    }

    public static byte[] assess(byte[] bytes) { return encode(GiftWarCashPolicy.assess(decode(bytes))); }

    /** Shared projection only. This does not evaluate a gift or approve another optional spend. */
    public static CashContext decodeCashContext(byte[] bytes) {
        ObjectNode node = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "snapshot", "root",
                "spending", "market", "market_source_frame", "mercenary_ledger"));
        StrictJson.require("xar.native-spending-context.v1".equals(text(node.get("schema"))), "native spending context schema required");
        return new CashContext(snapshot(object(node.get("snapshot"))), read(node, "root", GiftWarCashCodec::root),
                read(node, "spending", GiftWarCashCodec::spending), read(node, "market", GiftWarCashCodec::market),
                read(node, "market_source_frame", GiftWarCashCodec::frameRead),
                read(node, "mercenary_ledger", GiftWarCashCodec::validatedMercenaryPending));
    }

    /** Persistence/wire round-trip validation; this is no substitute for native input qualification. */
    public static Decision decodeDecision(byte[] bytes) {
        JsonNode node = object(StrictJson.parse(bytes));
        Set<String> expected = new HashSet<>(Set.of("schema", "source_frame", "new_gift_spending_allowed",
                "policy_floor_raw", "future_income_or_unreceived_financing_credited_raw",
                "thresholds_are_native_or_user_hard_limits", "status"));
        StrictJson.require("xar.faction-gift-wartime-cash/v1".equals(text(node.get("schema"))), "decision schema required");
        Status status = switch (text(node.get("status"))) {
            case "outside_wartime" -> Status.OUTSIDE_WARTIME;
            case "defer_new_gift" -> Status.DEFER_NEW_GIFT;
            case "war_cash_retained" -> Status.WAR_CASH_RETAINED;
            default -> throw new IllegalArgumentException("unknown gift cash status");
        };
        Reason reason = null;
        if (status != Status.OUTSIDE_WARTIME) {
            expected.add("reason"); String wire = text(node.get("reason"));
            for (Reason candidate : Reason.values()) { if (candidate.wire().equals(wire)) { reason = candidate; } }
            StrictJson.require(reason != null, "known gift cash reason required");
        }
        Treasury treasury = null;
        if (node.has("observed_treasury_raw") || node.has("gift_gold_cost_raw") || node.has("gold_after_gift_raw")) {
            expected.addAll(Set.of("observed_treasury_raw", "gift_gold_cost_raw", "gold_after_gift_raw"));
            treasury = new Treasury(integer(node.get("observed_treasury_raw")), integer(node.get("gift_gold_cost_raw")),
                    integer(node.get("gold_after_gift_raw")));
        }
        Reserve reserve = null;
        if (node.has("required_remaining_gold_raw") || node.has("military_buffer_raw") || node.has("existing_unpaid_commitments_raw")
                || node.has("emergency_quote") || node.has("qualified_quote_count") || node.has("arrival_or_victory_verified")) {
            expected.addAll(Set.of("required_remaining_gold_raw", "military_buffer_raw", "existing_unpaid_commitments_raw",
                    "emergency_quote", "qualified_quote_count", "arrival_or_victory_verified"));
            JsonNode quote = StrictJson.object(node.get("emergency_quote"), Set.of("company_id", "complete_contract_gold_raw"));
            BigInteger count = integer(node.get("qualified_quote_count"));
            StrictJson.require(count.signum() > 0 && count.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "positive bounded quote count");
            reserve = new Reserve(integer(node.get("military_buffer_raw")), integer(node.get("existing_unpaid_commitments_raw")),
                    new EmergencyQuote(integer(quote.get("company_id")), integer(quote.get("complete_contract_gold_raw"))), count.intValueExact());
            StrictJson.require(integer(node.get("required_remaining_gold_raw")).equals(reserve.requiredRaw()), "reserve total mismatch");
            StrictJson.require(!bool(node.get("arrival_or_victory_verified")), "arrival/victory is never verified by this guard");
        }
        StrictJson.object(node, expected);
        JsonNode source = StrictJson.object(node.get("source_frame"), FRAME_FIELDS); FrameRead frame = frameRead(source);
        Decision result = new Decision(new SourceFrame(required(frame.playedCharacterId(), "played_character_id"),
                required(frame.nativeRevision(), "native_revision"), required(frame.dateRaw(), "date_raw"),
                required(frame.snapshotId(), "snapshot_id"), required(frame.revision(), "revision"),
                required(frame.episodeRunId(), "episode_run_id")), status, reason, treasury, reserve);
        StrictJson.require(bool(node.get("new_gift_spending_allowed")) == result.newGiftSpendingAllowed(), "spending status mismatch");
        StrictJson.require(integer(node.get("policy_floor_raw")).equals(GiftWarCashPolicy.MILITARY_FLOOR_RAW), "policy floor mismatch");
        StrictJson.require(integer(node.get("future_income_or_unreceived_financing_credited_raw")).signum() == 0,
                "unreceived finance must not be credited");
        StrictJson.require(!bool(node.get("thresholds_are_native_or_user_hard_limits")), "policy threshold is not a native hard limit");
        return result;
    }

    public static byte[] encode(Decision decision) {
        ObjectNode node = StrictJson.object(); node.put("schema", "xar.faction-gift-wartime-cash/v1");
        node.set("source_frame", encodeFrame(decision.sourceFrame()));
        node.put("new_gift_spending_allowed", decision.newGiftSpendingAllowed());
        node.put("policy_floor_raw", GiftWarCashPolicy.MILITARY_FLOOR_RAW);
        node.put("future_income_or_unreceived_financing_credited_raw", 0);
        node.put("thresholds_are_native_or_user_hard_limits", false);
        node.put("status", switch (decision.status()) {
            case OUTSIDE_WARTIME -> "outside_wartime";
            case DEFER_NEW_GIFT -> "defer_new_gift";
            case WAR_CASH_RETAINED -> "war_cash_retained";
        });
        if (decision.reason() != null) { node.put("reason", decision.reason().wire()); }
        Treasury treasury = decision.treasury();
        if (treasury != null) {
            node.put("observed_treasury_raw", treasury.observedRaw()); node.put("gift_gold_cost_raw", treasury.giftCostRaw());
            node.put("gold_after_gift_raw", treasury.afterGiftRaw());
        }
        Reserve reserve = decision.reserve();
        if (reserve != null) {
            node.put("required_remaining_gold_raw", reserve.requiredRaw()); node.put("military_buffer_raw", reserve.militaryBufferRaw());
            node.put("existing_unpaid_commitments_raw", reserve.existingCommitmentsRaw());
            ObjectNode quote = node.putObject("emergency_quote"); quote.put("company_id", reserve.emergencyQuote().companyId());
            quote.put("complete_contract_gold_raw", reserve.emergencyQuote().completeContractGoldRaw());
            node.put("qualified_quote_count", reserve.qualifiedQuoteCount()); node.put("arrival_or_victory_verified", false);
        }
        return StrictJson.canonical(node, 16_384);
    }

    public static ObjectNode encodeFrame(SourceFrame frame) {
        ObjectNode node = StrictJson.object(); node.put("played_character_id", frame.playedCharacterId());
        node.put("native_revision", frame.nativeRevision()); node.put("date_raw", frame.dateRaw());
        node.put("snapshot_id", frame.snapshotId()); node.put("revision", frame.revision()); node.put("episode_run_id", frame.episodeRunId());
        return node;
    }

    private static Snapshot snapshot(JsonNode node) {
        Read<BigInteger> actor = read(part(node, "played_character"), "character_id", GiftWarCashCodec::integer);
        Read<BigInteger> player = read(node, "played_character_id", GiftWarCashCodec::integer);
        if (!player.known()) { player = actor; }
        SourceFrame frame = new SourceFrame(required(player, "played_character_id"),
                required(read(node, "native_revision", GiftWarCashCodec::integer), "native_revision"),
                required(read(node, "date_raw", GiftWarCashCodec::integer), "date_raw"),
                required(read(node, "snapshot_id", GiftWarCashCodec::text), "snapshot_id"),
                required(read(node, "revision", GiftWarCashCodec::integer), "revision"),
                required(read(node, "episode_run_id", GiftWarCashCodec::text), "episode_run_id"));
        JsonNode wallet = part(node, "played_character_gold");
        return new Snapshot(frame, actor, read(wallet, "raw", GiftWarCashCodec::integer),
                read(wallet, "scale", GiftWarCashCodec::integer), read(node, "active_wars", GiftWarCashCodec::wars));
    }
    private static List<War> wars(JsonNode node) {
        StrictJson.require(node.isArray(), "active_wars array required"); List<War> result = new ArrayList<>();
        for (JsonNode row : node) {
            object(row); List<Read<BigInteger>> provinces = new ArrayList<>(); JsonNode enemies = row.get("enemy_armies");
            if (enemies != null && enemies.isArray()) {
                for (JsonNode army : enemies) {
                    if (army.isObject()) { provinces.add(read(army, "current_province_id", GiftWarCashCodec::integer)); }
                }
            }
            result.add(new War(read(row, "war_id", GiftWarCashCodec::integer), provinces));
        }
        return List.copyOf(result);
    }
    private static Candidate candidate(JsonNode value) {
        JsonNode node = object(value);
        return new Candidate(read(node, "choice", source -> {
            object(source);
            return new Choice(read(source, "player_character_id", GiftWarCashCodec::integer),
                    read(source, "native_snapshot_revision", GiftWarCashCodec::integer),
                    read(source, "date_raw", GiftWarCashCodec::integer), read(source, "gold_cost_raw", GiftWarCashCodec::integer));
        }), read(node, "observation", source -> {
            object(source);
            return new GiftObservation(read(source, "player_character_id", GiftWarCashCodec::privateCharacter),
                    read(source, "native_snapshot_revision", GiftWarCashCodec::integer),
                    read(source, "observed_date_raw", GiftWarCashCodec::integer),
                    read(source, "player_gold_raw", GiftWarCashCodec::integer),
                    read(source, "player_gold_scale", GiftWarCashCodec::integer),
                    read(part(source, "gift_preview"), "gold_cost_raw", GiftWarCashCodec::integer));
        }));
    }
    private static Root root(JsonNode value) {
        JsonNode node = object(value); JsonNode maximum = part(node, "player_max_monthly_gold_maintenance_v1");
        JsonNode rate = part(maximum, "value");
        return new Root(read(node, "status", GiftWarCashCodec::text), read(node, "player_character_id", GiftWarCashCodec::integer),
                read(node, "snapshot_revision", GiftWarCashCodec::integer), read(node, "date_raw", GiftWarCashCodec::integer),
                read(maximum, "status", GiftWarCashCodec::text), read(rate, "raw", GiftWarCashCodec::integer),
                read(rate, "scale", GiftWarCashCodec::integer));
    }
    private static Spending spending(JsonNode value) {
        JsonNode node = object(value); JsonNode budget = part(node, "budget");
        return new Spending(read(node, "status", GiftWarCashCodec::text), read(node, "frame", source -> {
            object(source);
            return new BudgetFrame(read(source, "actor_character_id", GiftWarCashCodec::integer),
                    read(source, "native_revision", GiftWarCashCodec::integer), read(source, "date_raw", GiftWarCashCodec::integer),
                    read(source, "snapshot_id", GiftWarCashCodec::text), exactFields(source, BUDGET_FRAME_FIELDS));
        }), read(part(budget, "reserved_raw"), "gold", GiftWarCashCodec::integer),
                read(budget, "active_war_count", GiftWarCashCodec::integer));
    }
    private static FrameRead frameRead(JsonNode value) {
        JsonNode node = object(value);
        return new FrameRead(read(node, "played_character_id", GiftWarCashCodec::integer),
                read(node, "native_revision", GiftWarCashCodec::integer), read(node, "date_raw", GiftWarCashCodec::integer),
                read(node, "snapshot_id", GiftWarCashCodec::text), read(node, "revision", GiftWarCashCodec::integer),
                read(node, "episode_run_id", GiftWarCashCodec::text), exactFields(node, FRAME_FIELDS));
    }
    private static Market market(JsonNode value) {
        JsonNode node = object(value);
        return new Market(read(node, "available", GiftWarCashCodec::bool), read(node, "actor_character_id", GiftWarCashCodec::integer),
                read(node, "date_raw", GiftWarCashCodec::integer), read(node, "rows", source -> {
                    StrictJson.require(source.isArray(), "market rows array required"); List<QuoteRow> rows = new ArrayList<>();
                    for (JsonNode row : source) { if (row.isObject()) { rows.add(quote(row)); } }
                    return List.copyOf(rows);
                }));
    }
    private static QuoteRow quote(JsonNode node) {
        JsonNode terms = part(node, "final_terms"); JsonNode troops = part(node, "troop_strength");
        JsonNode location = part(node, "location"); JsonNode readiness = part(node, "readiness_v1");
        return new QuoteRow(read(node, "company_id", GiftWarCashCodec::integer), presence(node.get("employer_id")),
                read(terms, "resource_costs_raw", source -> {
                    StrictJson.require(source.isArray(), "resource costs array required"); List<BigInteger> costs = new ArrayList<>();
                    for (JsonNode cost : source) { costs.add(integer(cost)); } return List.copyOf(costs);
                }), read(terms, "resource_scale", GiftWarCashCodec::integer), read(terms, "available", GiftWarCashCodec::bool),
                read(terms, "can_hire", GiftWarCashCodec::bool), read(terms, "can_afford", GiftWarCashCodec::bool),
                read(readiness, "hire_ready", GiftWarCashCodec::bool), read(troops, "available", GiftWarCashCodec::bool),
                read(troops, "current_soldiers", GiftWarCashCodec::integer),
                read(location, "hire_auto_raise_province_id", GiftWarCashCodec::integer),
                read(location, "hire_auto_raise_position_ready", GiftWarCashCodec::bool),
                read(location, "hire_auto_raise_attempted_in_active_war", GiftWarCashCodec::bool));
    }
    private static JsonNode part(JsonNode node, String name) {
        if (node == null || !node.isObject()) { return null; }
        JsonNode value = node.get(name); return value != null && value.isObject() ? value : null;
    }
    private static Presence validatedMercenaryPending(JsonNode value) {
        object(value); StrictJson.require(value.has("pending"), "validated mercenary pending field required");
        JsonNode pending = value.get("pending");
        StrictJson.require(pending.isNull() || pending.isObject(), "pending intent must be object or null");
        return presence(pending);
    }
    private static JsonNode object(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "object projection required"); return node;
    }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "exact JSON integer token required; no bool/float/string");
        return node.bigIntegerValue();
    }
    private static BigInteger privateCharacter(JsonNode node) {
        return NativeCharacterId.fromRawUInt32(integer(node)).asBigInteger();
    }
    private static Boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "actual JSON boolean token required"); return node.booleanValue();
    }
    private static String text(JsonNode node) {
        StrictJson.require(node != null && node.isTextual(), "JSON string required");
        if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); } return node.textValue();
    }
    private static Presence presence(JsonNode node) {
        return node == null ? Presence.MISSING : node.isNull() ? Presence.NULL : Presence.VALUE;
    }
    private static <T> Read<T> read(JsonNode node, String name, Function<JsonNode, T> parse) {
        JsonNode value = node == null ? null : node.get(name);
        return value == null ? Read.missing() : value.isNull() ? Read.nil() : Read.of(parse.apply(value));
    }
    private static <T> T required(Read<T> value, String name) {
        StrictJson.require(value.known(), "M5 observed frame requires " + name); return value.value();
    }
    private static boolean exactFields(JsonNode node, Set<String> expected) {
        Set<String> actual = new HashSet<>(); node.properties().forEach(entry -> actual.add(entry.getKey())); return actual.equals(expected);
    }
}
