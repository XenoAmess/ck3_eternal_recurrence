package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovementCodec;
import org.xar.ck3.control.wave2.military.zerostockclock.ArmyUpdateClock;
import org.xar.ck3.control.wave2.military.zerostockclock.ArmyUpdateClockCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;

/** Concrete normalizers, including the existing complete current-edge/timeline and clock Java implementations. */
public final class ArmyStrengthsNativeFields {
    private ArmyStrengthsNativeFields() { }
    public enum ResolutionBranch { UNAVAILABLE, REFERENCE_ABSENT, STORAGE_UNAVAILABLE, INDEX_OUT_OF_RANGE, ENTRY_EMPTY, FULL_ID_MISMATCH, RESOLVED }
    public record Resolution(Status status, boolean ready, ResolutionBranch branch, Field<Integer> rawReference,
            Field<Integer> referenceIndex, Field<Integer> storageCapacity, Field<Integer> entryFullId) {
        public Resolution { Objects.requireNonNull(status); Objects.requireNonNull(branch); require(status != Status.PARTIAL && ready == (status == Status.AVAILABLE), "native resolution readiness mismatch"); Objects.requireNonNull(rawReference); Objects.requireNonNull(referenceIndex); Objects.requireNonNull(storageCapacity); Objects.requireNonNull(entryFullId); }
    }
    public record LossInputs(Status status, Field<String> reason, Field<Integer> raidAssociationId, Field<Integer> wholeSoldiers,
            Field<Integer> definitionLeZeroSoldiers, Field<Integer> supplyEligibleSoldiers, Field<Integer> definitionLeZeroSupplyEligibleSoldiers,
            Field<Integer> currentSupplyLossBudget, Field<Integer> siegeLossBudget, Field<Integer> raidLossBudget,
            Field<Long> siegeRateRaw, Field<Long> raidRateRaw, Field<Boolean> siegeActive, Field<Boolean> raidActive) {
        public LossInputs {
            Objects.requireNonNull(status); Objects.requireNonNull(reason);
            List<Field<?>> fields = List.of(raidAssociationId, wholeSoldiers, definitionLeZeroSoldiers, supplyEligibleSoldiers, definitionLeZeroSupplyEligibleSoldiers,
                    currentSupplyLossBudget, siegeLossBudget, raidLossBudget, siegeRateRaw, raidRateRaw, siegeActive, raidActive);
            require(status == Status.AVAILABLE ? reason instanceof NullValue<?> && fields.stream().allMatch(value -> value instanceof Present<?>)
                    : status == Status.UNAVAILABLE && reason instanceof Present<?> && fields.stream().allMatch(value -> value instanceof NullValue<?>), "loss application input availability must cover every observed scalar");
        }
    }
    public record Sources(ExactRef nativeFields, ExactRef currentMovement, ExactRef armyUpdateClock) {
        public Sources { Objects.requireNonNull(nativeFields); Objects.requireNonNull(currentMovement); Objects.requireNonNull(armyUpdateClock); }
    }
    public static void install(ArmyStrengthsFamilies.Registry registry, Sources sources) {
        registry.register(ArmyStrengthsFamilies.Key.NATIVE_ARMY_RESOLUTION_V1, Resolution.class,
                (input, row) -> new Present<>(resolution(required(input))), field -> new RawJson(bytes(resolutionJson(ArmyStrengthsCodec.present(field)))), sources.nativeFields());
        registry.register(ArmyStrengthsFamilies.Key.LOSS_APPLICATION_INPUTS_V1, LossInputs.class,
                (input, row) -> new Present<>(lossInputs(required(input))), field -> new RawJson(bytes(lossJson(ArmyStrengthsCodec.present(field)))),
                field -> ArmyStrengthsPublicNumbers.encode(new RawJson(bytes(lossJson(ArmyStrengthsCodec.present(field)))), List.of(
                        new ArmyStrengthsPublicNumbers.Rule("/siege_rate_raw", ArmyStrengthsPublicNumbers.Domain.SIGNED_64),
                        new ArmyStrengthsPublicNumbers.Rule("/raid_rate_raw", ArmyStrengthsPublicNumbers.Domain.SIGNED_64))), sources.nativeFields());
        registry.register(ArmyStrengthsFamilies.Key.CURRENT_MOVEMENT_PROGRESS, CurrentMovement.class, (input, row) -> {
            Optional<CurrentMovement> value = CurrentMovementCodec.normalize(nullableInput(input));
            return value.<Field<CurrentMovement>>map(Present::new).orElseGet(NullValue::new);
        }, field -> new RawJson(CurrentMovementCodec.encode(field instanceof Present<CurrentMovement> p ? Optional.of(p.value()) : Optional.empty())), sources.currentMovement());
        registry.register(ArmyStrengthsFamilies.Key.ARMY_UPDATE_CLOCK_V1, ArmyUpdateClock.class, (input, row) -> {
            ArmyUpdateClock value = ArmyUpdateClockCodec.decode(nullableInput(input)); return value == null ? new NullValue<>() : new Present<>(value);
        }, field -> new RawJson(bytes(ArmyUpdateClockCodec.encode(field instanceof Present<ArmyUpdateClock> p ? p.value() : null))), sources.armyUpdateClock());
    }
    private static ObjectNode required(Field<RawJson> input) { require(input instanceof Present<?>, "this native Army family requires an object, not missing or null"); return parse(ArmyStrengthsCodec.present(input).bytes()); }
    private static com.fasterxml.jackson.databind.JsonNode nullableInput(Field<RawJson> input) { return input instanceof Present<RawJson> p ? ArmyStrengthsCodec.parseValue(p.value()) : com.fasterxml.jackson.databind.node.NullNode.getInstance(); }
    public static Resolution resolution(ObjectNode row) {
        closed(row, "status", "ready", "branch", "raw_reference", "reference_index", "storage_capacity", "entry_full_id");
        return new Resolution(ArmyStrengthsCodec.enumText(get(row, "status"), Status.class), bool(get(row, "ready")), ArmyStrengthsCodec.enumText(get(row, "branch"), ResolutionBranch.class),
                nullable(row, "raw_reference", ArmyJson::i32), nullable(row, "reference_index", ArmyJson::i32), nullable(row, "storage_capacity", ArmyJson::i32), nullable(row, "entry_full_id", ArmyJson::i32));
    }
    public static ObjectNode resolutionJson(Resolution value) {
        ObjectNode row = empty().put("status", ArmyStrengthsCodec.wire(value.status())).put("ready", value.ready()).put("branch", ArmyStrengthsCodec.wire(value.branch()));
        ArmyStrengthsCodec.put(row, "raw_reference", value.rawReference(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "reference_index", value.referenceIndex(), n -> empty().numberNode(n));
        ArmyStrengthsCodec.put(row, "storage_capacity", value.storageCapacity(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "entry_full_id", value.entryFullId(), n -> empty().numberNode(n)); return row;
    }
    public static LossInputs lossInputs(ObjectNode row) {
        closed(row, "status", "unavailable_reason", "fraction_scale", "soldier_scale", "raid_association_id", "whole_soldiers", "definition_le_zero_soldiers", "supply_eligible_soldiers", "definition_le_zero_supply_eligible_soldiers", "current_supply_loss_budget", "siege_loss_budget", "raid_loss_budget", "siege_rate_raw", "raid_rate_raw", "siege_active", "raid_active");
        equal(get(row, "fraction_scale"), BigInteger.valueOf(SCALE)); equal(get(row, "soldier_scale"), BigInteger.ONE);
        return new LossInputs(ArmyStrengthsCodec.enumText(get(row, "status"), Status.class), nullable(row, "unavailable_reason", ArmyJson::nonempty), nullable(row, "raid_association_id", ArmyJson::i32),
                nullable(row, "whole_soldiers", ArmyJson::i32), nullable(row, "definition_le_zero_soldiers", ArmyJson::i32), nullable(row, "supply_eligible_soldiers", ArmyJson::i32), nullable(row, "definition_le_zero_supply_eligible_soldiers", ArmyJson::i32),
                nullable(row, "current_supply_loss_budget", ArmyJson::i32), nullable(row, "siege_loss_budget", ArmyJson::i32), nullable(row, "raid_loss_budget", ArmyJson::i32), nullable(row, "siege_rate_raw", ArmyJson::i64), nullable(row, "raid_rate_raw", ArmyJson::i64), nullable(row, "siege_active", ArmyJson::bool), nullable(row, "raid_active", ArmyJson::bool));
    }
    public static ObjectNode lossJson(LossInputs value) {
        ObjectNode row = empty().put("status", ArmyStrengthsCodec.wire(value.status())).put("fraction_scale", SCALE).put("soldier_scale", 1);
        ArmyStrengthsCodec.put(row, "unavailable_reason", value.reason(), n -> empty().textNode(n));
        ArmyStrengthsCodec.put(row, "raid_association_id", value.raidAssociationId(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "whole_soldiers", value.wholeSoldiers(), n -> empty().numberNode(n));
        ArmyStrengthsCodec.put(row, "definition_le_zero_soldiers", value.definitionLeZeroSoldiers(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "supply_eligible_soldiers", value.supplyEligibleSoldiers(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "definition_le_zero_supply_eligible_soldiers", value.definitionLeZeroSupplyEligibleSoldiers(), n -> empty().numberNode(n));
        ArmyStrengthsCodec.put(row, "current_supply_loss_budget", value.currentSupplyLossBudget(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "siege_loss_budget", value.siegeLossBudget(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "raid_loss_budget", value.raidLossBudget(), n -> empty().numberNode(n));
        ArmyStrengthsCodec.put(row, "siege_rate_raw", value.siegeRateRaw(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "raid_rate_raw", value.raidRateRaw(), n -> empty().numberNode(n)); ArmyStrengthsCodec.put(row, "siege_active", value.siegeActive(), n -> empty().booleanNode(n)); ArmyStrengthsCodec.put(row, "raid_active", value.raidActive(), n -> empty().booleanNode(n)); return row;
    }
}
