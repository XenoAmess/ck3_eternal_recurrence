package org.xar.ck3.control.wave2.development.constructionscene;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.*;

/** Strict wrappers; snapshot/history/root/cash are explicitly declared extensible SDK projections. */
public final class ConstructionSceneCodec {
    public static final String SCENE_SCHEMA = "xar.construction-scene-input.v1";
    public static final String CASH_SCHEMA = "xar.construction-clan-cash-frame-input.v1";
    public static final int MAX_BYTES = 65_536;
    private ConstructionSceneCodec() { }

    public static SceneInput decodeScene(byte[] raw) {
        return decodeScene(StrictJson.parse(raw, MAX_BYTES));
    }

    public static SceneInput decodeScene(JsonNode node) {
        StrictJson.object(node, Set.of("schema", "snapshot", "history"));
        StrictJson.require(SCENE_SCHEMA.equals(text(node.get("schema"))), "construction scene schema required");
        JsonNode history = node.get("history"); StrictJson.require(history.isArray(), "history must be an array");
        List<HistoryRow> rows = new ArrayList<>();
        for (JsonNode row : history) {
            object(row);
            JsonNode commandValue = row.get("command");
            if (commandValue == null || !commandValue.isTextual()
                    || !ConstructionScenePolicy.ROOT_QUERY_STEP.equals(commandValue.textValue())) {
                rows.add(new HistoryRow(Field.missing(), Field.missing(), Field.missing()));
                continue;
            }
            Field<String> command = Field.of(commandValue.textValue());
            Field<Boolean> ok = read(row, "ok", ConstructionSceneCodec::bool);
            // Unrelated result bodies remain opaque. Only this original public-query producer is consumed.
            Field<Root> root = command.is(ConstructionScenePolicy.ROOT_QUERY_STEP) && ok.is(true)
                    ? read(part(row, "result"), "campaign_root_context", ConstructionSceneCodec::root) : Field.missing();
            rows.add(new HistoryRow(command, ok, root));
        }
        return new SceneInput(snapshot(object(node.get("snapshot"))), rows);
    }

    public static CashInput decodeCash(byte[] raw) {
        JsonNode node = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("schema", "snapshot", "observation"));
        StrictJson.require(CASH_SCHEMA.equals(text(node.get("schema"))), "Clan cash frame schema required");
        JsonNode budget = part(part(node, "observation"), "current_cash_scenarios");
        return new CashInput(snapshot(object(node.get("snapshot"))), read(budget, "source_cash_resources", ConstructionSceneCodec::cashPacket));
    }
    public static byte[] scope(byte[] raw) { return encodeScope(ConstructionScenePolicy.scope(decodeScene(raw))); }
    public static byte[] clanCashReason(byte[] raw) { return encodeCashResult(ConstructionScenePolicy.clanCashFrame(decodeCash(raw))); }

    /** Minimum declared projection, never an original SDK observation or its source proof. */
    public static byte[] encodeScene(SceneInput input) {
        ObjectNode request = StrictJson.object(); request.put("schema", SCENE_SCHEMA);
        Snapshot source = input.snapshot(); ObjectNode snapshot = request.putObject("snapshot");
        write(snapshot, "paused", source.paused(), value -> JsonNodeFactory.instance.booleanNode(value));
        write(snapshot, "active_wars", source.activeWarCount(), count -> {
            StrictJson.require(count <= MAX_BYTES / 2, "bounded projected active war count required");
            ArrayNode wars = JsonNodeFactory.instance.arrayNode(); for (int index = 0; index < count; index++) { wars.addObject(); } return wars;
        });
        if (source.actorId().presence() != Presence.MISSING) {
            write(snapshot.putObject("played_character"), "character_id", source.actorId(), value -> JsonNodeFactory.instance.numberNode(value));
        }
        write(snapshot, "native_revision", source.nativeRevision(), value -> JsonNodeFactory.instance.numberNode(value));
        write(snapshot, "revision", source.publicRevision(), value -> JsonNodeFactory.instance.numberNode(value));
        write(snapshot, "snapshot_id", source.snapshotId(), value -> JsonNodeFactory.instance.textNode(value));
        write(snapshot, "date_raw", source.dateRaw(), value -> JsonNodeFactory.instance.numberNode(value));
        StrictJson.require(input.history().size() <= MAX_BYTES / 2, "bounded projected history required");
        ArrayNode history = request.putArray("history");
        for (HistoryRow row : input.history()) {
            ObjectNode encoded = history.addObject();
            write(encoded, "command", row.command(), value -> JsonNodeFactory.instance.textNode(value));
            write(encoded, "ok", row.ok(), value -> JsonNodeFactory.instance.booleanNode(value));
            if (row.root().presence() != Presence.MISSING) { write(encoded.putObject("result"), "campaign_root_context", row.root(), ConstructionSceneCodec::encodeRoot); }
        }
        return StrictJson.canonical(request, MAX_BYTES);
    }

    private static ObjectNode encodeRoot(Root root) {
        ObjectNode node = StrictJson.object();
        write(node, "status", root.status(), value -> JsonNodeFactory.instance.textNode(value));
        write(node, "snapshot_revision", root.revision(), value -> JsonNodeFactory.instance.numberNode(value));
        write(node, "date_raw", root.dateRaw(), value -> JsonNodeFactory.instance.numberNode(value));
        write(node, "player_character_id", root.actorId(), value -> JsonNodeFactory.instance.numberNode(value));
        write(node, "government", root.government(), government -> {
            ObjectNode value = StrictJson.object(); write(value, "key", government.key(), key -> JsonNodeFactory.instance.textNode(key));
            write(value, "flags", government.flags(), flags -> {
                ArrayNode entries = JsonNodeFactory.instance.arrayNode(); for (String flag : flags) { entries.add(flag); } return entries;
            }); return value;
        });
        write(node, "council", root.council(), council -> {
            ObjectNode value = StrictJson.object(); write(value, "status", council.status(), status -> JsonNodeFactory.instance.textNode(status));
            write(value, "positions", council.positions(), positions -> {
                ArrayNode entries = JsonNodeFactory.instance.arrayNode();
                for (Position position : positions) {
                    ObjectNode item = entries.addObject(); write(item, "position_key", position.key(), key -> JsonNodeFactory.instance.textNode(key));
                    write(item, "incumbent_character_id", position.incumbentId(), identity -> JsonNodeFactory.instance.numberNode(identity));
                    write(item, "task_key", position.taskKey(), key -> JsonNodeFactory.instance.textNode(key));
                    write(item, "frozen", position.frozen(), frozen -> JsonNodeFactory.instance.booleanNode(frozen));
                }
                return entries;
            }); return value;
        }); return node;
    }
    private static <T> void write(ObjectNode node, String key, Field<T> field, Function<T, JsonNode> encoder) {
        if (field.known()) { node.set(key, encoder.apply(field.value())); }
        else if (field.presence() == Presence.NULL) { node.putNull(key); }
    }

    /** Original shared helper wire, including generic observed governments used only by the perk wrapper. */
    public static byte[] encodeRootScope(RootScope value) {
        ObjectNode node = StrictJson.object();
        node.put("status", switch (value.status()) {
            case SCOPE_UNAVAILABLE -> "scope_unavailable";
            case OUTSIDE_SCENE -> "outside_scene";
            case ROOT_QUERY_NEEDED -> "root_query_needed";
            case ADMITTED -> "admitted";
        });
        if (value.status() != RootScopeStatus.SCOPE_UNAVAILABLE) { node.put("at_peace", value.atPeace()); }
        if (value.status() == RootScopeStatus.ADMITTED) {
            node.put("government_key", value.governmentKey()); node.put("snapshot_revision", value.revision()); node.put("player_character_id", value.actorId());
            if (value.collectTaxesActive().known()) { node.put("collect_taxes_active", value.collectTaxesActive().value()); }
            else { node.putNull("collect_taxes_active"); }
        }
        return StrictJson.canonical(node, 4_096);
    }

    public static byte[] encodeScope(Scope value) {
        ObjectNode node = StrictJson.object();
        switch (value) {
            case Unavailable ignored -> node.put("status", "scope_unavailable");
            case OutsideScene outside -> { node.put("status", "outside_scene"); node.put("at_peace", outside.atPeace()); }
            case RootQueryNeeded needed -> { node.put("status", "root_query_needed"); node.put("at_peace", needed.atPeace()); }
            case Admitted admitted -> {
                node.put("status", "admitted"); node.put("at_peace", admitted.atPeace());
                node.put("government_key", admitted.government() == Government.FEUDAL ? "feudal_government" : "clan_government");
                node.put("snapshot_revision", admitted.revision()); node.put("player_character_id", admitted.actorId());
                Field<Boolean> taxes = admitted.collectTaxesActive();
                if (taxes.known()) { node.put("collect_taxes_active", taxes.value()); }
                else if (taxes.presence() == Presence.NULL) { node.putNull("collect_taxes_active"); }
            }
        }
        return StrictJson.canonical(node, 4_096);
    }

    public static Scope decodeScope(byte[] raw) {
        JsonNode node = object(StrictJson.parse(raw, 4_096)); String status = text(node.get("status"));
        return switch (status) {
            case "scope_unavailable" -> { StrictJson.object(node, Set.of("status")); yield new Unavailable(); }
            case "outside_scene" -> {
                StrictJson.object(node, Set.of("status", "at_peace")); yield new OutsideScene(bool(node.get("at_peace")));
            }
            case "root_query_needed" -> {
                StrictJson.object(node, Set.of("status", "at_peace")); yield new RootQueryNeeded(bool(node.get("at_peace")));
            }
            case "admitted" -> {
                Government government = switch (text(node.get("government_key"))) {
                    case "feudal_government" -> Government.FEUDAL;
                    case "clan_government" -> Government.CLAN;
                    default -> throw new IllegalArgumentException("unsupported admitted government");
                };
                StrictJson.object(node, government == Government.FEUDAL
                        ? Set.of("status", "at_peace", "government_key", "snapshot_revision", "player_character_id", "collect_taxes_active")
                        : Set.of("status", "at_peace", "government_key", "snapshot_revision", "player_character_id"));
                yield new Admitted(bool(node.get("at_peace")), government, integer(node.get("snapshot_revision")),
                        integer(node.get("player_character_id")), read(node, "collect_taxes_active", ConstructionSceneCodec::bool));
            }
            default -> throw new IllegalArgumentException("unknown construction scene status");
        };
    }

    public static byte[] encodeCashResult(CashFrameResult result) {
        ObjectNode node = StrictJson.object();
        if (result instanceof CashFrameDeferred deferred) { node.put("reason", deferred.reason().wire()); }
        else { node.putNull("reason"); }
        return StrictJson.canonical(node, 4_096);
    }
    public static CashFrameResult decodeCashResult(byte[] raw) {
        JsonNode node = StrictJson.object(StrictJson.parse(raw, 4_096), Set.of("reason")); JsonNode reason = node.get("reason");
        if (reason.isNull()) { return new CashFrameObserved(); }
        String wire = text(reason);
        for (CashReason value : CashReason.values()) { if (value.wire().equals(wire)) { return new CashFrameDeferred(value); } }
        throw new IllegalArgumentException("unknown Clan cash reason");
    }

    private static Snapshot snapshot(JsonNode node) {
        return new Snapshot(read(node, "paused", ConstructionSceneCodec::bool), read(node, "active_wars", value -> {
            StrictJson.require(value.isArray(), "active_wars must be an array"); return value.size();
        }), read(part(node, "played_character"), "character_id", ConstructionSceneCodec::integer),
                read(node, "native_revision", ConstructionSceneCodec::integer), read(node, "revision", ConstructionSceneCodec::integer),
                read(node, "snapshot_id", ConstructionSceneCodec::text), read(node, "date_raw", ConstructionSceneCodec::integer));
    }
    private static Root root(JsonNode node) {
        object(node);
        return new Root(read(node, "status", ConstructionSceneCodec::text), read(node, "snapshot_revision", ConstructionSceneCodec::integer),
                read(node, "date_raw", ConstructionSceneCodec::integer), read(node, "player_character_id", ConstructionSceneCodec::integer),
                read(node, "government", value -> {
                    object(value); return new GovernmentObservation(read(value, "key", ConstructionSceneCodec::text),
                            read(value, "flags", flags -> {
                                StrictJson.require(flags.isArray(), "government flags must be array"); List<String> result = new ArrayList<>();
                                for (JsonNode flag : flags) { result.add(text(flag)); } return List.copyOf(result);
                            }));
                }), read(node, "council", value -> {
                    object(value); return new Council(read(value, "status", ConstructionSceneCodec::text), read(value, "positions", rows -> {
                        StrictJson.require(rows.isArray(), "council positions must be array"); List<Position> result = new ArrayList<>();
                        for (JsonNode row : rows) {
                            object(row); result.add(new Position(read(row, "position_key", ConstructionSceneCodec::text),
                                    read(row, "incumbent_character_id", ConstructionSceneCodec::integer), read(row, "task_key", ConstructionSceneCodec::text),
                                    read(row, "frozen", ConstructionSceneCodec::bool)));
                        }
                        return List.copyOf(result);
                    }));
                }));
    }
    private static CashPacket cashPacket(JsonNode node) {
        object(node);
        return new CashPacket(read(node, "played_character_id", ConstructionSceneCodec::integer), read(node, "snapshot_revision", ConstructionSceneCodec::integer),
                read(node, "date_raw", ConstructionSceneCodec::integer), read(node, "game_version", ConstructionSceneCodec::text),
                read(node, "read_only", ConstructionSceneCodec::bool), read(node, "readiness", value -> {
                    object(value); return new CashReadiness(read(value, "same_frame_ready", ConstructionSceneCodec::bool),
                            read(value, "current_treasury_ready", ConstructionSceneCodec::bool), read(value, "monthly_gross_income_ready", ConstructionSceneCodec::bool),
                            read(value, "monthly_total_expenses_ready", ConstructionSceneCodec::bool), read(value, "monthly_net_income_ready", ConstructionSceneCodec::bool));
                }), read(node, "monthly_income_semantics", value -> value.isObject()));
    }
    private static JsonNode part(JsonNode node, String name) {
        if (node == null || !node.isObject()) { return null; }
        JsonNode value = node.get(name); return value != null && value.isObject() ? value : null;
    }
    private static JsonNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "SDK object projection required"); return value; }
    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact JSON integer token required; bool/float/string rejected"); return value.bigIntegerValue();
    }
    private static String text(JsonNode value) {
        StrictJson.require(value != null && value.isTextual(), "JSON string token required");
        if (!value.textValue().isEmpty()) { StrictJson.text(value.textValue()); } return value.textValue();
    }
    private static Boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "JSON boolean token required"); return value.booleanValue();
    }
    private static <T> Field<T> read(JsonNode object, String key, Function<JsonNode, T> parser) {
        JsonNode value = object == null ? null : object.get(key);
        return value == null ? Field.missing() : value.isNull() ? Field.nil() : Field.of(parser.apply(value));
    }
}
