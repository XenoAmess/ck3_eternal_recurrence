package org.xar.ck3.control.finance.feastbudget;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Actor;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.CampaignRoot;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Field;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Inputs;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.IntentState;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Ledgers;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Maintenance;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Money;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Observed;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Presence;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Request;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Result;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Snapshot;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Unavailable;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.War;

/** Strict wrapper; existing SDK containers are explicitly projected, not exact-key constrained. */
public final class FeastBudgetCodec {
    public static final String SCHEMA = "xar.feast-budget-projection.v1";
    private FeastBudgetCodec() { }

    public static Request decode(byte[] raw) {
        ObjectNode request = StrictJson.object(StrictJson.parse(raw),
                Set.of("schema", "snapshot", "inputs", "ledgers", "campaign_root"));
        StrictJson.require(SCHEMA.equals(string(request.get("schema"))), "unsupported feast budget schema");
        JsonNode snapshot = object(request.get("snapshot")); JsonNode inputs = object(request.get("inputs"));
        JsonNode ledgers = StrictJson.object(request.get("ledgers"),
                Set.of("construction", "faction_gift", "first_heir_marriage", "child_marriage"));
        return new Request(new Snapshot(field(snapshot, "paused", FeastBudgetCodec::bool),
                field(snapshot, "map_ready", FeastBudgetCodec::bool),
                field(snapshot, "played_character", node -> new Actor(field(object(node), "character_id", FeastBudgetCodec::integer))),
                field(snapshot, "native_revision", FeastBudgetCodec::integer),
                field(snapshot, "date_raw", FeastBudgetCodec::integer),
                field(snapshot, "snapshot_id", FeastBudgetCodec::string),
                field(snapshot, "revision", FeastBudgetCodec::integer),
                field(snapshot, "active_wars", FeastBudgetCodec::wars), presence(snapshot.get("pending_character_interaction"))),
                new Inputs(field(inputs, "actor_character_id", FeastBudgetCodec::integer),
                        field(inputs, "snapshot_revision", FeastBudgetCodec::integer),
                        field(inputs, "date_raw", FeastBudgetCodec::integer),
                        field(inputs, "post_snapshot_id", FeastBudgetCodec::string),
                        field(inputs, "queried_revision", FeastBudgetCodec::integer)),
                new Ledgers(intent(ledgers.get("construction")), intent(ledgers.get("faction_gift")),
                        intent(ledgers.get("first_heir_marriage")), intent(ledgers.get("child_marriage"))),
                field(request, "campaign_root", FeastBudgetCodec::campaignRoot));
    }

    public static byte[] assess(byte[] raw) { return encode(FeastBudgetPolicy.observe(decode(raw))); }

    public static byte[] encode(Result result) {
        ObjectNode output = StrictJson.object();
        if (result instanceof Unavailable unavailable) {
            output.put("status", "unavailable"); output.put("reason", unavailable.reason().wire());
            output.putNull("budget");
        } else if (result instanceof Observed observed) {
            output.put("status", "observed"); output.put("reason", "exclusive_paused_activity_lane");
            ObjectNode frame = output.putObject("frame");
            frame.put("actor_character_id", observed.frame().actorCharacterId());
            frame.put("native_revision", observed.frame().nativeRevision());
            frame.put("date_raw", observed.frame().dateRaw()); frame.put("snapshot_id", observed.frame().snapshotId());
            ObjectNode budget = output.putObject("budget"); ObjectNode reserved = budget.putObject("reserved_raw");
            for (String resource : List.of("gold", "treasury", "piety", "barter_goods")) { reserved.put(resource, 0); }
            budget.put("peaceful_spend_allowed", true); budget.put("gold_floor_raw", FeastBudgetPolicy.PEACEFUL_GOLD_FLOOR_RAW);
            budget.put("active_war_count", observed.activeWarCount());
            budget.put("war_cash_reserve_raw", observed.warCashReserveRaw());
            if (observed.maximumMonthlyMaintenanceRaw() != null) {
                ObjectNode reservation = output.putObject("financial_reservation");
                reservation.put("policy", FeastBudgetPolicy.MAINTENANCE_POLICY);
                reservation.put("scale", FeastBudgetPolicy.SCALE);
                reservation.put("maximum_monthly_gold_maintenance_raw", observed.maximumMonthlyMaintenanceRaw());
                reservation.put("reservation_months", FeastBudgetPolicy.MAINTENANCE_RESERVATION_MONTHS);
                reservation.put("war_cash_reserve_raw", observed.warCashReserveRaw());
                reservation.put("amount_semantics", "discretionary_spend_financial_allocation");
                reservation.put("native_future_cost_upper_bound", false);
                reservation.put("m5_complete_war_cash_receipt", false);
            }
        } else { throw new IllegalArgumentException("result required"); }
        return StrictJson.canonical(output, 16_384);
    }

    /** Encodes the typed projection, preserving consumed missing/null semantics. Extra SDK fields are omitted. */
    public static byte[] encodeRequest(Request request) {
        ObjectNode output = StrictJson.object(); output.put("schema", SCHEMA);
        Snapshot value = request.snapshot(); ObjectNode snapshot = output.putObject("snapshot");
        put(snapshot, "paused", value.paused(), (node, entry) -> node.put("paused", entry));
        put(snapshot, "map_ready", value.mapReady(), (node, entry) -> node.put("map_ready", entry));
        put(snapshot, "played_character", value.playedCharacter(), (node, entry) ->
                putInteger(node.putObject("played_character"), "character_id", entry.characterId()));
        putInteger(snapshot, "native_revision", value.nativeRevision()); putInteger(snapshot, "date_raw", value.dateRaw());
        putText(snapshot, "snapshot_id", value.snapshotId()); putInteger(snapshot, "revision", value.revision());
        put(snapshot, "active_wars", value.activeWars(), (node, entries) -> {
            ArrayNode array = node.putArray("active_wars");
            for (War war : entries) { putInteger(array.addObject(), "war_id", war.warId()); }
        });
        if (value.pendingInteraction() == Presence.NULL) { snapshot.putNull("pending_character_interaction"); }
        else if (value.pendingInteraction() == Presence.VALUE) { snapshot.putObject("pending_character_interaction"); }
        Inputs source = request.inputs(); ObjectNode inputs = output.putObject("inputs");
        putInteger(inputs, "actor_character_id", source.actorCharacterId());
        putInteger(inputs, "snapshot_revision", source.snapshotRevision()); putInteger(inputs, "date_raw", source.dateRaw());
        putText(inputs, "post_snapshot_id", source.postSnapshotId()); putInteger(inputs, "queried_revision", source.queriedRevision());
        ObjectNode ledgers = output.putObject("ledgers");
        putIntent(ledgers, "construction", request.ledgers().construction());
        putIntent(ledgers, "faction_gift", request.ledgers().factionGift());
        putIntent(ledgers, "first_heir_marriage", request.ledgers().firstHeirMarriage());
        putIntent(ledgers, "child_marriage", request.ledgers().childMarriage());
        put(output, "campaign_root", request.campaignRoot(), (node, root) -> {
            ObjectNode target = node.putObject("campaign_root");
            putInteger(target, "player_character_id", root.playerCharacterId());
            putInteger(target, "snapshot_revision", root.snapshotRevision()); putInteger(target, "date_raw", root.dateRaw());
            put(target, "player_max_monthly_gold_maintenance_v1", root.maximumMaintenance(), (container, rate) -> {
                ObjectNode maintenance = container.putObject("player_max_monthly_gold_maintenance_v1");
                putText(maintenance, "status", rate.status());
                put(maintenance, "value", rate.value(), (holder, money) -> {
                    ObjectNode amount = holder.putObject("value");
                    putInteger(amount, "raw", money.raw()); putInteger(amount, "scale", money.scale());
                });
            });
        });
        return StrictJson.canonical(output);
    }

    private static CampaignRoot campaignRoot(JsonNode source) {
        JsonNode node = object(source);
        return new CampaignRoot(field(node, "player_character_id", FeastBudgetCodec::integer),
                field(node, "snapshot_revision", FeastBudgetCodec::integer), field(node, "date_raw", FeastBudgetCodec::integer),
                field(node, "player_max_monthly_gold_maintenance_v1", entry -> new Maintenance(
                        field(object(entry), "status", FeastBudgetCodec::string),
                        field(entry, "value", money -> new Money(field(object(money), "raw", FeastBudgetCodec::integer),
                                field(money, "scale", FeastBudgetCodec::integer))))));
    }
    private static List<War> wars(JsonNode value) {
        StrictJson.require(value.isArray(), "active_wars must be an array"); List<War> result = new ArrayList<>();
        for (JsonNode war : value) { result.add(new War(field(object(war), "war_id", FeastBudgetCodec::integer))); }
        return List.copyOf(result);
    }
    private static IntentState intent(JsonNode value) {
        object(value); StrictJson.require(value.has("pending"), "validated ledger pending field required");
        StrictJson.require(value.get("pending").isNull() || value.get("pending").isObject(),
                "validated pending intent must be an object or null");
        return value.get("pending").isNull() ? IntentState.CLEAR : IntentState.PENDING;
    }
    private static void putIntent(ObjectNode ledgers, String name, IntentState state) {
        ObjectNode ledger = ledgers.putObject(name);
        if (state == IntentState.CLEAR) { ledger.putNull("pending"); } else { ledger.putObject("pending"); }
    }
    private static JsonNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "object projection required"); return value;
    }
    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value.isIntegralNumber(), "exact integer token required; boolean/float/string rejected");
        return value.bigIntegerValue();
    }
    private static Boolean bool(JsonNode value) {
        StrictJson.require(value.isBoolean(), "actual boolean token required"); return value.booleanValue();
    }
    private static String string(JsonNode value) {
        StrictJson.require(value.isTextual(), "string token required");
        if (!value.textValue().isEmpty()) { StrictJson.text(value.textValue()); }
        return value.textValue();
    }
    private static Presence presence(JsonNode value) {
        return value == null ? Presence.MISSING : value.isNull() ? Presence.NULL : Presence.VALUE;
    }
    private static <T> Field<T> field(JsonNode node, String key, Function<JsonNode, T> parse) {
        JsonNode value = node.get(key);
        return value == null ? Field.missing() : value.isNull() ? Field.nil() : Field.of(parse.apply(value));
    }
    @FunctionalInterface private interface PutValue<T> { void put(ObjectNode node, T value); }
    private static <T> void put(ObjectNode node, String key, Field<T> value, PutValue<T> writer) {
        if (value.presence() == Presence.NULL) { node.putNull(key); }
        else if (value.known()) { writer.put(node, value.value()); }
    }
    private static void putInteger(ObjectNode node, String key, Field<BigInteger> value) {
        put(node, key, value, (holder, entry) -> holder.put(key, entry));
    }
    private static void putText(ObjectNode node, String key, Field<String> value) {
        put(node, key, value, (holder, entry) -> holder.put(key, entry));
    }
}
