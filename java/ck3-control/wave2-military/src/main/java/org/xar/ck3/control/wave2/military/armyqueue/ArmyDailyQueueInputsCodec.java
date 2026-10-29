package org.xar.ck3.control.wave2.military.armyqueue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyId;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyMagic;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Available;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ExplicitNull;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Family;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.InitialResolution;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Missing;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Observed;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Readiness;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Unavailable;

/** Exact additive leaf; the surrounding native SDK container is deliberately a projection. */
public final class ArmyDailyQueueInputsCodec {
    public static final String FAMILY_FIELD = "monthly_daily_queue_inputs_v1";
    public static final int MAX_BYTES = 65_536;
    private static final Set<String> FIELDS = Set.of("status", "ready", "unavailable_reason",
            "manager_army_id_list_2a5a8", "initial_army_resolution_rows");
    private static final Set<String> ROW_FIELDS = Set.of("status", "unavailable_reason", "stored_index",
            "raw_army_reference_id", "resolved_army_id", "used_fallback", "army_magic_14_raw",
            "native_army_identity_valid");

    private ArmyDailyQueueInputsCodec() { }

    public static ArmyDailyQueueInputs decode(byte[] bytes) {
        return decodeNullable(StrictJson.parse(bytes, MAX_BYTES));
    }

    /** JSON null is an explicit absent family. A missing Java node is rejected. */
    public static ArmyDailyQueueInputs decodeNullable(JsonNode value) {
        StrictJson.require(value != null && !value.isMissingNode(), "daily queue family must be present");
        if (value.isNull()) { return null; }
        ObjectNode root = StrictJson.object(value, FIELDS);
        Readiness readiness = readiness(root);
        JsonNode ready = root.get("ready");
        StrictJson.require(ready.isBoolean() && ready.booleanValue() == (readiness instanceof Available),
                "daily queue ready disagrees with status");
        Optional<List<ArmyId>> ids = Optional.empty();
        JsonNode idValues = root.get("manager_army_id_list_2a5a8");
        if (!idValues.isNull()) {
            StrictJson.require(idValues.isArray(), "daily queue IDs must be ordered array or null");
            List<ArmyId> parsed = new ArrayList<>();
            for (JsonNode id : idValues) { parsed.add(armyId(id)); }
            ids = Optional.of(parsed);
        }
        Optional<List<InitialResolution>> rows = Optional.empty();
        JsonNode rowValues = root.get("initial_army_resolution_rows");
        if (!rowValues.isNull()) {
            StrictJson.require(rowValues.isArray(), "daily queue resolution rows must be array or null");
            List<InitialResolution> parsed = new ArrayList<>();
            for (JsonNode item : rowValues) {
                ObjectNode row = StrictJson.object(item, ROW_FIELDS);
                parsed.add(new InitialResolution(readiness(row), signed32(row.get("stored_index")),
                        armyId(row.get("raw_army_reference_id")), optionalArmyId(row.get("resolved_army_id")),
                        optionalBoolean(row.get("used_fallback")), optionalMagic(row.get("army_magic_14_raw")),
                        optionalBoolean(row.get("native_army_identity_valid"))));
            }
            rows = Optional.of(parsed);
        }
        return new ArmyDailyQueueInputs(readiness, ids, rows);
    }

    /** Reads only the declared additive family; extra native strength fields are not rejected. */
    public static Family projectFamily(JsonNode armyStrength) {
        StrictJson.require(armyStrength != null && armyStrength.isObject(), "army strength container required");
        JsonNode family = armyStrength.get(FAMILY_FIELD);
        if (family == null) { return new Missing(); }
        if (family.isNull()) { return new ExplicitNull(); }
        return new Observed(decodeNullable(family));
    }

    public static byte[] encode(ArmyDailyQueueInputs value) {
        return StrictJson.canonical(encodeNullable(value), MAX_BYTES);
    }

    public static JsonNode encodeNullable(ArmyDailyQueueInputs value) {
        if (value == null) { return NullNode.getInstance(); }
        ObjectNode root = readinessNode(value.readiness());
        root.put("ready", value.ready());
        if (value.orderedIds().isPresent()) {
            ArrayNode ids = root.putArray("manager_army_id_list_2a5a8");
            value.orderedIds().orElseThrow().forEach(id -> ids.add(id.value()));
        } else { root.putNull("manager_army_id_list_2a5a8"); }
        if (value.initialRows().isPresent()) {
            ArrayNode rows = root.putArray("initial_army_resolution_rows");
            for (InitialResolution valueRow : value.initialRows().orElseThrow()) {
                ObjectNode row = readinessNode(valueRow.readiness());
                row.put("stored_index", valueRow.storedIndex());
                row.put("raw_army_reference_id", valueRow.rawArmyReference().value());
                if (valueRow.resolvedArmy().isPresent()) {
                    row.put("resolved_army_id", valueRow.resolvedArmy().orElseThrow().value());
                } else { row.putNull("resolved_army_id"); }
                optionalBoolean(row, "used_fallback", valueRow.usedFallback());
                if (valueRow.armyMagic().isPresent()) {
                    row.put("army_magic_14_raw", valueRow.armyMagic().orElseThrow().value());
                } else { row.putNull("army_magic_14_raw"); }
                optionalBoolean(row, "native_army_identity_valid", valueRow.nativeIdentityValid());
                rows.add(row);
            }
        } else { root.putNull("initial_army_resolution_rows"); }
        return root;
    }

    private static Readiness readiness(ObjectNode node) {
        JsonNode status = node.get("status");
        StrictJson.require(status.isTextual(), "daily queue status must be string");
        JsonNode reason = node.get("unavailable_reason");
        return switch (status.textValue()) {
            case "available" -> {
                StrictJson.require(reason.isNull(), "available daily queue reason must be null");
                yield new Available();
            }
            case "unavailable" -> {
                StrictJson.require(reason.isTextual() && !reason.textValue().isEmpty(),
                        "unavailable daily queue reason must be nonempty string");
                yield new Unavailable(reason.textValue());
            }
            default -> throw new IllegalArgumentException("daily queue status is malformed");
        };
    }

    private static ObjectNode readinessNode(Readiness readiness) {
        ObjectNode node = StrictJson.object();
        switch (readiness) {
            case Available ignored -> { node.put("status", "available"); node.putNull("unavailable_reason"); }
            case Unavailable absent -> { node.put("status", "unavailable"); node.put("unavailable_reason", absent.reason()); }
        }
        return node;
    }

    private static int signed32(JsonNode value) {
        return Math.toIntExact(StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE));
    }
    private static ArmyId armyId(JsonNode value) { return new ArmyId(signed32(value)); }
    private static Optional<ArmyId> optionalArmyId(JsonNode value) {
        return value.isNull() ? Optional.empty() : Optional.of(armyId(value));
    }
    private static Optional<ArmyMagic> optionalMagic(JsonNode value) {
        return value.isNull() ? Optional.empty()
                : Optional.of(new ArmyMagic(StrictJson.integer(value, 0, 0xffff_ffffL)));
    }
    private static Optional<Boolean> optionalBoolean(JsonNode value) {
        if (value.isNull()) { return Optional.empty(); }
        StrictJson.require(value.isBoolean(), "daily queue predicate must be bool or null");
        return Optional.of(value.booleanValue());
    }
    private static void optionalBoolean(ObjectNode node, String field, Optional<Boolean> value) {
        if (value.isPresent()) { node.put(field, value.orElseThrow().booleanValue()); }
        else { node.putNull(field); }
    }
}
