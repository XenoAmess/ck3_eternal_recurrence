package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/**
 * Complete original war_contract.normalize_active_wars and objective-state contract.
 * This pure decoder never grants native source/frame qualification; live callers
 * retain their actual Current/Context and archived callers retain original receipts.
 */
public final class NativeActiveWarsCodec {
    private NativeActiveWarsCodec() { }

    /** This particular Province selection uses nonnegative int32 CArmy IDs, not general FullId. */
    public record BesiegingArmySelection(Optional<Integer> nativeArmyId,
            Optional<PublicUnitId> publicUnitId, Optional<Boolean> controllable) {
        public BesiegingArmySelection {
            Objects.requireNonNull(nativeArmyId); Objects.requireNonNull(publicUnitId); Objects.requireNonNull(controllable);
            nativeArmyId.ifPresent(value -> require(value >= 0, "Province selection native Army ID must be nonnegative int32"));
        }
    }

    public record Objective(int provinceId, boolean occupationObservable,
            Optional<Boolean> occupied, Optional<Integer> occupyingCharacterId,
            Optional<Integer> fortLevel, Optional<Integer> garrisonSize, Optional<Integer> besiegingStrength,
            boolean siegeObservable, Optional<ArmyWarOccupationCodec.Siege> activeSiege,
            Field<BesiegingArmySelection> currentBesiegingArmySelection) {
        public Objective {
            require(provinceId > 0, "objective Province ID must be positive int32");
            Objects.requireNonNull(occupied); Objects.requireNonNull(occupyingCharacterId);
            Objects.requireNonNull(fortLevel); Objects.requireNonNull(garrisonSize); Objects.requireNonNull(besiegingStrength);
            Objects.requireNonNull(activeSiege); Objects.requireNonNull(currentBesiegingArmySelection);
            occupyingCharacterId.ifPresent(value -> require(value > 0, "observed occupier must be positive int32"));
            for (Optional<Integer> value : List.of(fortLevel, garrisonSize, besiegingStrength))
                value.ifPresent(number -> require(number >= 0, "objective count must be nonnegative int32"));
            if (!occupationObservable)
                require(occupied.isEmpty() && occupyingCharacterId.isEmpty(), "unknown occupation cannot publish values");
            else {
                require(occupied.isPresent(), "observable occupation requires exact boolean");
                require(occupied.orElseThrow() == occupyingCharacterId.isPresent(),
                        "occupied objective needs an occupier; unoccupied objective cannot publish one");
            }
            require(siegeObservable || activeSiege.isEmpty(), "unknown siege cannot publish an active one");
            activeSiege.ifPresent(value -> require(
                    ArmyWarOccupationCodec.siege(OpportunityJson.toNode(value.normalized())).equals(value),
                    "typed Siege differs from its sole complete normalized tree"));
        }
    }

    /**
     * The original general nonnegative ID contract is arbitrary precision.
     * Objective row identities and public CUnit IDs retain their narrower domains.
     */
    public record War(BigInteger warId, Side playerSide, Optional<BigInteger> primaryOpponentCharacterId,
            Optional<Boolean> playerIsPrimaryWarLeader, Optional<BigInteger> enemyPrimaryDefaultRaiseProvinceId,
            List<BigInteger> targetedTitleIds, List<BigInteger> warObjectiveProvinceIds,
            List<Objective> objectiveProvinceStates, BigInteger playerRelativeWarScore,
            List<NativeArmiesCodec.Army> alliedArmies, List<NativeArmiesCodec.Army> enemyArmies) {
        public War {
            nonnegativeValue(warId, "War ID"); Objects.requireNonNull(playerSide);
            Objects.requireNonNull(primaryOpponentCharacterId); Objects.requireNonNull(playerIsPrimaryWarLeader);
            Objects.requireNonNull(enemyPrimaryDefaultRaiseProvinceId);
            primaryOpponentCharacterId.ifPresent(value -> nonnegativeValue(value, "primary opponent"));
            enemyPrimaryDefaultRaiseProvinceId.ifPresent(value -> nonnegativeValue(value, "default raise Province ID"));
            targetedTitleIds = uniqueIds(targetedTitleIds, "targeted Title IDs");
            warObjectiveProvinceIds = uniqueIds(warObjectiveProvinceIds, "objective Province IDs");
            objectiveProvinceStates = List.copyOf(objectiveProvinceStates);
            Objects.requireNonNull(playerRelativeWarScore);
            alliedArmies = List.copyOf(alliedArmies); enemyArmies = List.copyOf(enemyArmies);
            require(objectiveProvinceStates.isEmpty() || objectiveProvinceStates.stream()
                    .map(value -> BigInteger.valueOf(value.provinceId())).toList().equals(warObjectiveProvinceIds),
                    "nonempty objective states must completely match ordered objective IDs");
        }
    }

    /** Null and omitted collection input normalize to empty exactly as the original producer contract. */
    public static List<War> normalize(JsonNode value) {
        if (value == null || value.isNull()) return List.of();
        require(value.isArray(), "native active_wars must be an array");
        List<War> result = new ArrayList<>(); int index = 0;
        for (JsonNode row : value) {
            ObjectNode raw = object(row);
            Side side = switch (text(raw.get("player_side"))) {
                case "attacker" -> Side.ATTACKER;
                case "defender" -> Side.DEFENDER;
                default -> throw new IllegalArgumentException("native active_wars player_side malformed");
            };
            List<BigInteger> objectives = idList(raw.get("war_objective_province_ids"));
            result.add(new War(nonnegativeInteger(raw.get("war_id")), side,
                    optional(raw.get("primary_opponent_character_id"), NativeActiveWarsCodec::nonnegativeInteger),
                    optional(raw.get("player_is_primary_war_leader"), ArmyJson::bool),
                    optional(raw.get("enemy_primary_default_raise_province_id"), NativeActiveWarsCodec::nonnegativeInteger),
                    idList(raw.get("targeted_title_ids")), objectives,
                    normalizeObjectives(raw.get("objective_province_states"), objectives),
                    integer(raw.get("player_relative_war_score")),
                    NativeArmiesCodec.normalize(raw.get("allied_armies"), "active_wars[" + index + "].allied_armies"),
                    NativeArmiesCodec.normalize(raw.get("enemy_armies"), "active_wars[" + index + "].enemy_armies")));
            index++;
        }
        return List.copyOf(result);
    }

    /** Bound use of a complete application request, without constructing another native observation. */
    public static List<War> normalize(Context actual, PlanningRequest original) {
        Objects.requireNonNull(actual); Objects.requireNonNull(original);
        require(actual.before().equals(original.before()) && actual.source().equals(original.source())
                && actual.sessionId().equals(original.sessionId()) && actual.deadline().equals(original.deadline()),
                "active War normalizer crossed the actual current source/frame/session/deadline");
        return normalize(OpportunityJson.toNode(original.observations().snapshot()).get("active_wars"));
    }

    public static List<Objective> normalizeObjectives(JsonNode value, List<BigInteger> objectiveIds) {
        Objects.requireNonNull(objectiveIds);
        if (value == null || value.isNull()) return List.of();
        require(value.isArray(), "native objective_province_states must be an array");
        List<Objective> result = new ArrayList<>();
        for (JsonNode row : value) result.add(objective(object(row)));
        require(result.isEmpty() || result.stream().map(row -> BigInteger.valueOf(row.provinceId())).toList().equals(objectiveIds),
                "objective states must completely match war_objective_province_ids in order");
        return List.copyOf(result);
    }

    public static ArrayNode encode(List<War> values) {
        ArrayNode result = JsonNodeFactory.instance.arrayNode();
        for (War value : List.copyOf(values)) result.add(encodeWar(value));
        return result;
    }

    public static ObjectNode encodeWar(War value) {
        Objects.requireNonNull(value); ObjectNode result = empty();
        result.put("war_id", value.warId());
        result.put("player_side", value.playerSide() == Side.ATTACKER ? "attacker" : "defender");
        putBigOptional(result, "primary_opponent_character_id", value.primaryOpponentCharacterId());
        putBooleanOptional(result, "player_is_primary_war_leader", value.playerIsPrimaryWarLeader());
        putBigOptional(result, "enemy_primary_default_raise_province_id", value.enemyPrimaryDefaultRaiseProvinceId());
        putIds(result, "targeted_title_ids", value.targetedTitleIds());
        putIds(result, "war_objective_province_ids", value.warObjectiveProvinceIds());
        ArrayNode objectives = result.putArray("objective_province_states");
        value.objectiveProvinceStates().forEach(row -> objectives.add(encodeObjective(row)));
        result.put("player_relative_war_score", value.playerRelativeWarScore());
        result.set("allied_armies", NativeArmiesCodec.encode(value.alliedArmies()));
        result.set("enemy_armies", NativeArmiesCodec.encode(value.enemyArmies()));
        result.put("source", "native"); return result;
    }

    public static ObjectNode encodeObjective(Objective value) {
        Objects.requireNonNull(value); ObjectNode result = empty();
        result.put("province_id", value.provinceId()); result.put("occupation_observable", value.occupationObservable());
        putBooleanOptional(result, "is_occupied", value.occupied()); putIntOptional(result, "occupying_character_id", value.occupyingCharacterId());
        putIntOptional(result, "fort_level", value.fortLevel()); putIntOptional(result, "garrison_size", value.garrisonSize());
        putIntOptional(result, "besieging_strength", value.besiegingStrength()); result.put("siege_observable", value.siegeObservable());
        if (value.activeSiege().isPresent())
            result.set("active_siege", OpportunityJson.toNode(value.activeSiege().orElseThrow().normalized()));
        else result.putNull("active_siege");
        switch (value.currentBesiegingArmySelection()) {
            case Missing<BesiegingArmySelection> ignored -> { }
            case NullValue<BesiegingArmySelection> ignored -> result.putNull("current_besieging_army_selection");
            case Present<BesiegingArmySelection> present -> {
                BesiegingArmySelection selection = present.value(); ObjectNode row = empty();
                putIntOptional(row, "native_carmy_id", selection.nativeArmyId());
                if (selection.publicUnitId().isPresent()) row.put("public_unit_id", selection.publicUnitId().orElseThrow().value());
                else row.putNull("public_unit_id");
                putBooleanOptional(row, "controllable", selection.controllable());
                result.set("current_besieging_army_selection", row);
            }
        }
        return result;
    }

    private static Objective objective(ObjectNode raw) {
        boolean occupation = bool(raw.get("occupation_observable")), siege = bool(raw.get("siege_observable"));
        JsonNode originalSiege = raw.get("active_siege");
        return new Objective(id(raw.get("province_id")).value(), occupation,
                optional(raw.get("is_occupied"), ArmyJson::bool),
                optional(raw.get("occupying_character_id"), node -> id(node).value()),
                optional(raw.get("fort_level"), ArmyJson::nonnegative),
                optional(raw.get("garrison_size"), ArmyJson::nonnegative),
                optional(raw.get("besieging_strength"), ArmyJson::nonnegative), siege,
                optional(originalSiege, ArmyWarOccupationCodec::siege),
                field(raw, "current_besieging_army_selection", NativeActiveWarsCodec::selection));
    }

    private static BesiegingArmySelection selection(JsonNode value) {
        ObjectNode raw = object(value);
        return new BesiegingArmySelection(optional(raw.get("native_carmy_id"), ArmyJson::nonnegative),
                optional(raw.get("public_unit_id"), ArmyJson::unit),
                optional(raw.get("controllable"), ArmyJson::bool));
    }

    private static BigInteger nonnegativeInteger(JsonNode value) {
        BigInteger result = integer(value); nonnegativeValue(result, "native ID"); return result;
    }
    private static void nonnegativeValue(BigInteger value, String name) {
        require(Objects.requireNonNull(value).signum() >= 0, name + " must be a nonnegative integer");
    }
    private static List<BigInteger> idList(JsonNode value) {
        if (value == null || value.isNull()) return List.of();
        require(value.isArray(), "native ID collection must be an array");
        LinkedHashSet<BigInteger> result = new LinkedHashSet<>();
        for (JsonNode id : value) result.add(nonnegativeInteger(id));
        return List.copyOf(result);
    }
    private static List<BigInteger> uniqueIds(List<BigInteger> value, String name) {
        List<BigInteger> result = List.copyOf(value); result.forEach(id -> nonnegativeValue(id, name));
        require(new LinkedHashSet<>(result).size() == result.size(), name + " must already be normalized without duplicates");
        return result;
    }
    private static <T> Optional<T> optional(JsonNode raw, java.util.function.Function<JsonNode,T> decode) {
        return raw == null || raw.isNull() ? Optional.empty() : Optional.of(decode.apply(raw));
    }
    private static void putIds(ObjectNode target, String name, List<BigInteger> values) {
        ArrayNode result = target.putArray(name); values.forEach(result::add);
    }
    private static void putBigOptional(ObjectNode target, String name, Optional<BigInteger> value) {
        if (value.isEmpty()) target.putNull(name); else target.put(name, value.orElseThrow());
    }
    private static void putIntOptional(ObjectNode target, String name, Optional<Integer> value) {
        if (value.isEmpty()) target.putNull(name); else target.put(name, value.orElseThrow().intValue());
    }
    private static void putBooleanOptional(ObjectNode target, String name, Optional<Boolean> value) {
        if (value.isEmpty()) target.putNull(name); else target.put(name, value.orElseThrow().booleanValue());
    }
}
