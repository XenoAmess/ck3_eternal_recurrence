package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/**
 * Full war_contract.normalize_armies boundary, shared by snapshots, war state and planners.
 * Public CUnit, unbounded nonnegative observation values and positive signed32 route
 * provinces are deliberately different domains. Normalization retains array occurrences.
 */
public final class NativeArmiesCodec {
    private NativeArmiesCodec() { }
    public static final int MAX_NATIVE_ROUTE_SOURCE_COUNT = 4096;

    public enum RouteStatus {
        NOT_ATTEMPTED("not_attempted"), COMPLETE_EMPTY("complete_empty"),
        COMPLETE_NONEMPTY("complete_nonempty"), TARGET_ONLY("target_only"),
        INVALID_HEADER("invalid_header"), UNRESOLVED_ENTRY("unresolved_entry");
        private final String wire;
        RouteStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static RouteStatus parse(String value) {
            for (RouteStatus status : values()) if (status.wire.equals(value)) return status;
            throw new IllegalArgumentException("unknown native army route status");
        }
    }
    /** Presence of this record is presence of BOTH original status/count keys. */
    public record RouteEvidence(RouteStatus status, Optional<Integer> sourceCount) {
        public RouteEvidence {
            Objects.requireNonNull(status); Objects.requireNonNull(sourceCount);
            sourceCount.ifPresent(value -> require(value >= 0 && value <= MAX_NATIVE_ROUTE_SOURCE_COUNT,
                    "route source count outside original 0..4096 domain"));
        }
    }
    /** Optional tactical nulls normalize to absence; siege sidecars retain missing/null/value. */
    public record Army(PublicUnitId armyId, BigInteger ownerCharacterId,
            Optional<BigInteger> soldiers, Optional<BigInteger> currentProvinceId,
            Optional<BigInteger> moveTargetProvinceId, boolean moveTargetObservable, boolean controllable,
            Optional<List<Integer>> routeProvinceIds, Optional<RouteEvidence> routeEvidence,
            Optional<Boolean> inCombat, Optional<Boolean> retreating, Optional<String> armyState,
            Optional<BigInteger> armyStateCode, Field<BigInteger> siegeDaysLeft,
            Field<Integer> siegeProvinceHolderCharacterId, Field<Boolean> siegeProvinceInPlayerSubrealm) {
        public Army {
            Objects.requireNonNull(armyId); nonnegative(ownerCharacterId, "owner_character_id");
            soldiers = observed(soldiers, "soldiers"); currentProvinceId = observed(currentProvinceId, "current_province_id");
            moveTargetProvinceId = observed(moveTargetProvinceId, "move_target_province_id");
            Objects.requireNonNull(routeProvinceIds);
            routeProvinceIds = routeProvinceIds.map(values -> {
                List<Integer> copy = List.copyOf(values);
                copy.forEach(value -> require(value > 0, "route province must be positive int32"));
                return copy;
            });
            Objects.requireNonNull(routeEvidence); Objects.requireNonNull(inCombat); Objects.requireNonNull(retreating);
            Objects.requireNonNull(armyState); armyState.ifPresent(value -> require(!value.isEmpty(), "army_state must be nonempty"));
            armyStateCode = observed(armyStateCode, "army_state_code");
            requireField(siegeDaysLeft, value -> nonnegative(value, "siege_days_left"));
            requireField(siegeProvinceHolderCharacterId, value -> {
                require(value > 0, "siege holder requires positive int32"); return value;
            });
            requireField(siegeProvinceInPlayerSubrealm, Objects::requireNonNull);
            require(!(siegeProvinceInPlayerSubrealm instanceof Present<?>)
                    || siegeProvinceHolderCharacterId instanceof Present<?>, "observed siege relation requires holder");
            if (routeEvidence.isPresent()) {
                require(routeProvinceIds.isPresent(), "route status requires original route array");
                validateRoute(routeEvidence.orElseThrow(), routeProvinceIds.orElseThrow(),
                        moveTargetObservable, moveTargetProvinceId);
            }
        }
    }

    public static List<Army> normalize(JsonNode raw) { return normalize(raw, "player_armies"); }
    public static List<Army> normalize(JsonNode raw, String name) {
        Objects.requireNonNull(name);
        if (raw == null || raw.isNull()) return List.of();
        require(raw.isArray(), "native " + name + " must be an array");
        List<Army> rows = new ArrayList<>();
        for (int i = 0; i < raw.size(); i++) rows.add(normalizeArmy(raw.get(i), name + "[" + i + "]"));
        return List.copyOf(rows);
    }
    /** Same full decoder for a row already selected by a typed consumer. No partial projection path. */
    public static Army normalizeArmy(JsonNode raw, String name) {
        ObjectNode value = ArmyJson.object(raw); Objects.requireNonNull(name);
        JsonNode soldiers = value.get("soldiers");
        // The original accepted one early fixture spelling only on input; canonical output has soldiers.
        if (soldiers == null || soldiers.isNull()) soldiers = value.get("soldier_count");
        Optional<BigInteger> current = optional(value.get("current_province_id"), NativeArmiesCodec::nonnegativeNode);
        Optional<BigInteger> target = optional(value.get("move_target_province_id"), NativeArmiesCodec::nonnegativeNode);
        Optional<Boolean> explicitObservable = optional(value.get("move_target_observable"), ArmyJson::bool);
        boolean observable = explicitObservable.orElse(value.has("move_target_province_id"));
        Optional<List<Integer>> route = value.has("route_province_ids")
                ? Optional.of(ArmyJson.array(value.get("route_province_ids"), node -> {
                    BigInteger province = nonnegativeNode(node);
                    require(province.signum() > 0 && province.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                            "route province must be positive int32");
                    return province.intValueExact();
                })) : Optional.empty();
        require(value.has("route_read_status") == value.has("route_source_count"),
                "route status/count must appear together");
        Optional<RouteEvidence> evidence = Optional.empty();
        if (value.has("route_read_status")) {
            RouteStatus status = RouteStatus.parse(ArmyJson.text(value.get("route_read_status")));
            Optional<Integer> count = optional(value.get("route_source_count"), node -> {
                BigInteger number = nonnegativeNode(node);
                require(number.compareTo(BigInteger.valueOf(MAX_NATIVE_ROUTE_SOURCE_COUNT)) <= 0,
                        "route source count outside original 0..4096 domain");
                return number.intValueExact();
            });
            evidence = Optional.of(new RouteEvidence(status, count));
        }
        return new Army(ArmyJson.unit(value.get("army_id")), nonnegativeNode(value.get("owner_character_id")),
                optional(soldiers, NativeArmiesCodec::nonnegativeNode), current, target, observable,
                ArmyJson.bool(value.get("controllable")), route, evidence,
                optional(value.get("in_combat"), ArmyJson::bool), optional(value.get("retreating"), ArmyJson::bool),
                optional(value.get("army_state"), ArmyJson::nonempty),
                optional(value.get("army_state_code"), NativeArmiesCodec::nonnegativeNode),
                ArmyJson.field(value, "siege_days_left", NativeArmiesCodec::nonnegativeNode),
                ArmyJson.field(value, "siege_province_holder_character_id", node -> ArmyJson.id(node).value()),
                ArmyJson.field(value, "siege_province_in_player_subrealm", ArmyJson::bool));
    }

    public static ObjectNode encodeArmy(Army value) {
        Objects.requireNonNull(value); ObjectNode result = ArmyJson.empty();
        result.put("army_id", value.armyId().value()); result.put("owner_character_id", value.ownerCharacterId());
        // Write nullable canonical integers without any Number/string coercion.
        integer(result, "soldiers", value.soldiers()); integer(result, "current_province_id", value.currentProvinceId());
        integer(result, "move_target_province_id", value.moveTargetProvinceId());
        result.put("move_target_observable", value.moveTargetObservable()); result.put("controllable", value.controllable());
        result.put("source", "native");
        value.routeProvinceIds().ifPresent(route -> {
            ArrayNode rows = result.putArray("route_province_ids"); route.forEach(number -> rows.add(number.intValue()));
        });
        value.routeEvidence().ifPresent(evidence -> {
            result.put("route_read_status", evidence.status().wire());
            if (evidence.sourceCount().isPresent()) result.put("route_source_count", evidence.sourceCount().orElseThrow());
            else result.putNull("route_source_count");
        });
        value.inCombat().ifPresent(flag -> result.put("in_combat", flag));
        value.retreating().ifPresent(flag -> result.put("retreating", flag));
        value.armyState().ifPresent(state -> result.put("army_state", state));
        value.armyStateCode().ifPresent(code -> result.put("army_state_code", code));
        putField(result, "siege_days_left", value.siegeDaysLeft(), number -> result.numberNode(number));
        putField(result, "siege_province_holder_character_id", value.siegeProvinceHolderCharacterId(), number -> result.numberNode(number));
        putField(result, "siege_province_in_player_subrealm", value.siegeProvinceInPlayerSubrealm(), flag -> result.booleanNode(flag));
        return result;
    }
    public static ArrayNode encode(List<Army> values) {
        Objects.requireNonNull(values); ArrayNode result = ArmyJson.empty().arrayNode();
        values.forEach(value -> result.add(encodeArmy(value))); return result;
    }
    private static void validateRoute(RouteEvidence evidence, List<Integer> route, boolean observable, Optional<BigInteger> target) {
        Integer count = evidence.sourceCount().orElse(null);
        boolean valid = switch (evidence.status()) {
            case COMPLETE_EMPTY -> Integer.valueOf(0).equals(count) && route.isEmpty() && !observable && target.isEmpty();
            case COMPLETE_NONEMPTY -> count != null && count > 0 && route.size() == count && observable
                    && target.isPresent() && target.orElseThrow().equals(BigInteger.valueOf(route.get(route.size() - 1)));
            case TARGET_ONLY -> count != null && count > 0 && route.isEmpty() && observable && target.isPresent();
            case UNRESOLVED_ENTRY -> count != null && count > 0 && route.isEmpty() && !observable && target.isEmpty();
            case NOT_ATTEMPTED, INVALID_HEADER -> count == null && route.isEmpty() && !observable && target.isEmpty();
        };
        require(valid, "route status/count disagrees with observed fields");
    }
    private static BigInteger nonnegativeNode(JsonNode value) { return nonnegative(ArmyJson.integer(value), "army observation"); }
    private static BigInteger nonnegative(BigInteger value, String name) {
        Objects.requireNonNull(value); require(value.signum() >= 0, name + " must be nonnegative"); return value;
    }
    private static Optional<BigInteger> observed(Optional<BigInteger> value, String name) {
        Objects.requireNonNull(value); value.ifPresent(number -> nonnegative(number, name)); return value;
    }
    private static <T> Optional<T> optional(JsonNode node, Function<JsonNode, T> decoder) {
        return node == null || node.isNull() ? Optional.empty() : Optional.of(decoder.apply(node));
    }
    private static <T> void requireField(Field<T> field, Function<T, T> validator) {
        Objects.requireNonNull(field); if (field instanceof Present<T> present) validator.apply(present.value());
    }
    private static void integer(ObjectNode result, String key, Optional<BigInteger> value) {
        if (value.isPresent()) result.put(key, value.orElseThrow()); else result.putNull(key);
    }
    private static <T> void putField(ObjectNode result, String key, Field<T> field, Function<T, JsonNode> encoder) {
        if (field instanceof Present<T> present) result.set(key, encoder.apply(present.value()));
        else if (field instanceof NullValue<?>) result.putNull(key);
    }
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}

