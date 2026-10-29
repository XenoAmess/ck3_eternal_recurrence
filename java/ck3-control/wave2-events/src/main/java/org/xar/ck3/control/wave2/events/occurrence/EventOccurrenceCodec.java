package org.xar.ck3.control.wave2.events.occurrence;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.CommandResult;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.CommandRow;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.EventContext;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.EventSelection;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.HistoryItem;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.IgnoredItem;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.Request;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.Result;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.TypedCharacter;

/** Typed projection of extensible original command-history containers. */
public final class EventOccurrenceCodec {
    public static final String SCHEMA = "xar.ck3.event-occurrence-input/v1";
    private EventOccurrenceCodec() { }
    public static Request decode(byte[] raw) {
        return decodeParsed(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES));
    }
    /** Shared retained source already parsed by RetainedJson; every field/slot is converted, never re-encoded/re-parsed. */
    public static Request decodeRetained(org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue retained) {
        java.util.Objects.requireNonNull(retained);
        return decodeParsed(json(retained, new java.util.IdentityHashMap<>()));
    }
    private static Request decodeParsed(JsonNode parsed) {
        ObjectNode root = StrictJson.object(parsed,
            Set.of("schema", "event_definition_key", "played_character_id", "commands"));
        StrictJson.require(SCHEMA.equals(text(root, "schema")), "occurrence input schema");
        JsonNode commands = root.get("commands");
        Optional<List<HistoryItem>> history;
        if (commands.isNull()) history = Optional.empty();
        else {
            StrictJson.require(commands.isArray(), "command history array or explicit null");
            List<HistoryItem> rows = new ArrayList<>();
            for (JsonNode node : commands) {
                if (!node.isObject()) rows.add(new IgnoredItem());
                else rows.add(new CommandRow(text(node, "command"), bool(node, "ok"), result(objectOrNull(node.get("result")))));
            }
            history = Optional.of(rows);
        }
        return new Request(StrictJson.text(root.get("event_definition_key")), requiredInteger(root, "played_character_id"), history);
    }
    public static byte[] encode(Result result) {
        ObjectNode root = StrictJson.object().put("status", result.status() == EventOccurrence.Status.AVAILABLE ? "available" : "unavailable")
            .put("count", result.count()).put("reason", result.reason() == null ? null : result.reason().wire());
        return StrictJson.canonical(root);
    }
    public static byte[] encode(Request request) {
        ObjectNode root = StrictJson.object().put("schema", SCHEMA).put("event_definition_key", request.eventDefinitionKey())
            .put("played_character_id", request.playedCharacterId());
        if (request.commands().isEmpty()) root.putNull("commands");
        else {
            ArrayNode commands = root.putArray("commands");
            for (HistoryItem item : request.commands().orElseThrow()) {
                if (item instanceof IgnoredItem) commands.addNull();
                else if (item instanceof CommandRow row) {
                    ObjectNode encoded = commands.addObject().put("command", row.command()).put("ok", row.ok());
                    if (row.result() == null) encoded.putNull("result"); else encoded.set("result", resultNode(row.result()));
                }
            }
        }
        return StrictJson.canonical(root, StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static CommandResult result(JsonNode node) {
        if (node == null) return null;
        return new CommandResult(text(node, "step"), bool(node, "accepted"), context(objectOrNull(node.get("current_event_window_context"))),
            integer(node, "current_event_instance_id"), integer(node, "queried_native_revision"), integer(node, "snapshot_revision"),
            integer(node, "date_raw"), integer(node, "queried_revision"), text(node, "queried_snapshot_id"),
            selection(objectOrNull(node.get("event_selection"))));
    }
    private static EventContext context(JsonNode node) {
        if (node == null) return null;
        return new EventContext(text(node, "status"), integer(node, "current_event_instance_id"), integer(node, "snapshot_revision"),
            integer(node, "date_raw"), text(node, "event_definition_key"), character(objectOrNull(node.get("root_scope"))));
    }
    private static TypedCharacter character(JsonNode node) {
        if (node == null) return null;
        JsonNode identity = objectOrNull(node.get("typed_identity"));
        return new TypedCharacter(text(node, "status"), text(node, "type_key"), text(identity, "status"),
            text(identity, "kind"), integer(identity, "character_id"));
    }
    private static EventSelection selection(JsonNode node) {
        if (node == null) return null;
        return new EventSelection(text(node, "status"), bool(node, "postcondition_verified"), integer(node, "selected_option_number"),
            integer(node, "selected_native_option_index"), integer(node, "new_event_instance_id"), integer(node, "old_event_instance_id"),
            text(node, "starting_snapshot_id"), integer(node, "starting_revision"));
    }
    private static ObjectNode resultNode(CommandResult result) {
        ObjectNode node = StrictJson.object().put("step", result.step()).put("accepted", result.accepted())
            .put("current_event_instance_id", result.currentEventInstanceId()).put("queried_native_revision", result.queriedNativeRevision())
            .put("snapshot_revision", result.snapshotRevision()).put("date_raw", result.dateRaw()).put("queried_revision", result.queriedRevision())
            .put("queried_snapshot_id", result.queriedSnapshotId());
        EventContext context = result.context();
        if (context == null) node.putNull("current_event_window_context");
        else {
            ObjectNode frame = node.putObject("current_event_window_context").put("status", context.status())
                .put("current_event_instance_id", context.currentEventInstanceId()).put("snapshot_revision", context.snapshotRevision())
                .put("date_raw", context.dateRaw()).put("event_definition_key", context.eventDefinitionKey());
            TypedCharacter actor = context.rootScope();
            if (actor == null) frame.putNull("root_scope");
            else frame.putObject("root_scope").put("status", actor.status()).put("type_key", actor.typeKey())
                .putObject("typed_identity").put("status", actor.identityStatus()).put("kind", actor.identityKind()).put("character_id", actor.characterId());
        }
        EventSelection selected = result.eventSelection();
        if (selected == null) node.putNull("event_selection");
        else node.putObject("event_selection").put("status", selected.status()).put("postcondition_verified", selected.postconditionVerified())
            .put("selected_option_number", selected.selectedOptionNumber()).put("selected_native_option_index", selected.selectedNativeOptionIndex())
            .put("new_event_instance_id", selected.newEventInstanceId()).put("old_event_instance_id", selected.oldEventInstanceId())
            .put("starting_snapshot_id", selected.startingSnapshotId()).put("starting_revision", selected.startingRevision());
        return node;
    }
    /** Representation bridge only. The shared parser and original domain decoder remain the sole implementations. */
    private static JsonNode json(org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.Value value,
            java.util.IdentityHashMap<org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.Value,JsonNode> seen) {
        JsonNode known = seen.get(value); if (known != null) return known;
        var factory = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance;
        JsonNode result = switch (value) {
            case org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.NullValue ignored -> factory.nullNode();
            case org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.BooleanValue bool -> factory.booleanNode(bool.value());
            case org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.StringValue text -> factory.textNode(text.value());
            case org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.IntegerValue integer -> factory.numberNode(integer.value());
            case org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.FloatingValue floating -> factory.numberNode(floating.value());
            case org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ArrayValue array -> {
                ArrayNode node = factory.arrayNode(); seen.put(value, node);
                for (var item : array.values()) node.add(json(item, seen)); yield node;
            }
            case org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue object -> {
                ObjectNode node = factory.objectNode(); seen.put(value, node);
                for (var field : object.fields().entrySet()) node.set(field.getKey(), json(field.getValue(), seen)); yield node;
            }
        };
        seen.put(value, result); return result;
    }
    private static JsonNode objectOrNull(JsonNode value) {
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isObject(), "object or null required");
        return value;
    }
    private static String text(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isTextual(), "string token required: " + field);
        if (!value.textValue().isEmpty()) StrictJson.text(value.textValue());
        return value.textValue();
    }
    private static BigInteger integer(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isIntegralNumber(), "integer token required, no bool/float/string: " + field);
        return value.bigIntegerValue();
    }
    private static BigInteger requiredInteger(JsonNode node, String field) {
        BigInteger value = integer(node, field);
        StrictJson.require(value != null, "required integer: " + field);
        return value;
    }
    private static Boolean bool(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isBoolean(), "boolean token required: " + field);
        return value.booleanValue();
    }
}
