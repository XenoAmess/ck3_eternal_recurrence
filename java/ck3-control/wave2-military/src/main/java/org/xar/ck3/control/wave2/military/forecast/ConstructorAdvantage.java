package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputs;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputs;

/** Same-query native observations, frozen for bounded future trials, without a parity claim. */
public final class ConstructorAdvantage {
    private ConstructorAdvantage() { }
    public enum Source {
        GENERIC("generic_commander_and_stock_static_approximation"),
        V2_CONSTRUCTOR("same_frame_v2_native_constructor_zero_roll_frozen_future"),
        V3_NATIVE("same_frame_v3_native_zero_roll_frozen_future");
        private final String wire;
        Source(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public static final String V2_CONSTRUCTOR_ADVANTAGE_SOURCE = Source.V2_CONSTRUCTOR.wire();
    public record Selection(BigInteger attackerArmyId, BigInteger defenderArmyId, BigInteger zeroRollRaw,
            ResearchEnvelope.SelectedCommanders selectedCommanders, String modelSha256, Source source) {
        public Selection {
            publicCunitId(attackerArmyId, "selected attacker army"); publicCunitId(defenderArmyId, "selected defender army");
            require(zeroRollRaw != null && zeroRollRaw.bitLength() <= 63, "signed64 native advantage required");
            Objects.requireNonNull(selectedCommanders); Objects.requireNonNull(source);
            require(source != Source.GENERIC && modelSha256 != null && modelSha256.matches("[0-9A-F]{64}"), "native model provenance required");
            require(!attackerArmyId.equals(defenderArmyId), "native leader pair overlaps");
            requireSelectedCharacters(source, selectedCommanders);
        }
        public List<BigInteger> leaderArmyIds() { return List.of(attackerArmyId, defenderArmyId); }
    }
    static void requireSelectedCharacters(Source source, ResearchEnvelope.SelectedCommanders selected) {
        Objects.requireNonNull(source); Objects.requireNonNull(selected);
        for (BigInteger id : new BigInteger[] { selected.attackerCharacterId(), selected.defenderCharacterId() }) {
            if (id == null) continue;
            characterId(id, "selected commander");
            require(source != Source.V3_NATIVE || id.signum() > 0, "v3 selected commander must be positive");
        }
    }
    static BigInteger signedRaw(JsonNode value, String name) {
        BigInteger result = integer(value, name);
        require(result.bitLength() <= 63, name + " must be signed64"); return result;
    }
    private static boolean schema(JsonNode node, int version) {
        return node != null && node.isIntegralNumber() && node.bigIntegerValue().equals(n(version));
    }
    private static boolean sameInteger(JsonNode node, BigInteger expected) {
        return expected == null ? absentOrNull(node) : node != null && node.isIntegralNumber() && expected.equals(node.bigIntegerValue());
    }
    private static List<CombatInputs.Army> armies(CombatInputs.Frozen frozen, CombatInputs.Role role) {
        return frozen.armies().stream().filter(army -> army.encounterRole() == role).toList();
    }
    private static CombatInputs.Army leader(List<CombatInputs.Army> armies, BigInteger selected) {
        require(!armies.isEmpty(), "native side has no army");
        if (selected == null) return armies.getFirst();
        characterId(selected, "native selected commander");
        var candidates = armies.stream().filter(army -> Objects.equals(army.commander().characterId(), selected)).toList();
        require(candidates.size() == 1, "native selected commander army is not unique in same-frame armies");
        return candidates.getFirst();
    }
    public static Optional<Selection> readV2(CombatSimulationInputs payload, CombatInputs.Frozen frozen) { return readV2(Objects.requireNonNull(payload).toJson(), frozen); }
    public static Optional<Selection> readV2(JsonNode payload, CombatInputs.Frozen frozen) {
        Objects.requireNonNull(frozen);
        if (!schema(field(payload, "schema_version"), 2)) return Optional.empty();
        JsonNode base = field(payload, "base_inputs");
        if (base == null || !base.isObject()) return Optional.empty();
        JsonNode context = base.get("contextual_advantage");
        if (context == null || !context.isObject() || !schema(context.get("schema_version"), 2) || !is(context.get("status"), "available")) return Optional.empty();
        var encounter = frozen.encounter(); JsonNode scenario = base.get("scenario");
        require(scenario != null && scenario.isObject()
                && sameInteger(base.get("target_province_id"), encounter.targetProvinceId())
                && sameInteger(context.get("target_province_id"), encounter.targetProvinceId())
                && sameInteger(scenario.get("attacker_entry_province_id"), encounter.attackerEntryProvinceId())
                && ids(scenario.get("attacker_army_ids"), "attacker IDs").equals(encounter.attackerArmyIds())
                && ids(scenario.get("defender_army_ids"), "defender IDs").equals(encounter.defenderArmyIds()), "V2 constructor advantage encounter binding differs");
        require(is(context.get("scope"), "hypothetical_constructor_context")
                && integer(context.get("scale"), "constructor scale").equals(SCALE)
                && yes(context.get("synthetic_helper_total_match")), "V2 constructor advantage helper provenance differs");
        var sides = elements(context.get("sides"), "constructor sides"); require(sides.size() == 2, "V2 constructor side pair malformed");
        BigInteger[] leaders = new BigInteger[2], selected = new BigInteger[2], totals = new BigInteger[2];
        for (int index = 0; index < 2; index++) {
            var side = object(sides.get(index), "constructor side");
            var own = armies(frozen, index == 0 ? CombatInputs.Role.ATTACKER : CombatInputs.Role.DEFENDER);
            var expected = index == 0 ? encounter.attackerArmyIds() : encounter.defenderArmyIds();
            require(integer(side.get("side_index"), "side_index").equals(n(index)) && !own.isEmpty()
                    && own.stream().map(CombatInputs.Army::publicArmyId).toList().equals(expected)
                    && ids(side.get("ordered_public_cunit_ids"), "ordered constructor army IDs").equals(expected), "V2 constructor advantage ordered side differs");
            selected[index] = absentOrNull(side.get("selected_commander_character_id")) ? null : characterId(side.get("selected_commander_character_id"), "selected commander");
            leaders[index] = leader(own, selected[index]).publicArmyId();
            BigInteger commander = signedRaw(side.get("commander_dynamic_raw"), "commander_dynamic_raw"), dynamic = signedRaw(side.get("side_dynamic_raw"), "side_dynamic_raw"), residual = signedRaw(side.get("target_conditionals_residual_raw"), "target_conditionals_residual_raw");
            totals[index] = signedRaw(side.get("side_total_raw"), "side_total_raw");
            require(totals[index].equals(commander.add(dynamic).add(residual)), "V2 constructor advantage side arithmetic differs");
        }
        BigInteger baseRaw = signedRaw(context.get("base_constructor_accumulator_raw"), "base_constructor_accumulator_raw"), total = signedRaw(context.get("synthetic_zero_roll_total_raw"), "synthetic_zero_roll_total_raw");
        require(total.equals(baseRaw.add(totals[0]).subtract(totals[1])), "V2 constructor advantage total arithmetic differs");
        return Optional.of(new Selection(leaders[0], leaders[1], total, new ResearchEnvelope.SelectedCommanders(selected[0], selected[1]), sha256(canonical(context)).toUpperCase(Locale.ROOT), Source.V2_CONSTRUCTOR));
    }
    public static Optional<Selection> readV3(CombatPhaseInputs payload, CombatInputs.Frozen frozen) { return readV3(Objects.requireNonNull(payload).toJson(), frozen); }
    public static Optional<Selection> readV3(JsonNode payload, CombatInputs.Frozen frozen) {
        Objects.requireNonNull(frozen); JsonNode phase = field(payload, "phase_event_inputs");
        if (absentOrNull(phase) && !schema(field(payload, "schema_version"), 3)) return Optional.empty();
        if (phase != null && phase.isObject() && is(phase.get("status"), "unavailable") && absentOrNull(phase.get("advantage_model"))) return Optional.empty();
        require(phase != null && phase.isObject() && schema(field(payload, "schema_version"), 3)
                && is(field(payload, "contract_stage"), "production_exact_132_refs"), "native phase slice has no v3 identity");
        var model = object(phase.get("advantage_model"), "native advantage model"); var resolved = object(model.get("resolved_dynamic"), "native resolved advantage");
        require(is(model.get("status"), "available") && integer(model.get("scale"), "advantage scale").equals(SCALE)
                && is(model.get("scenario_policy"), frozen.encounter().participantPolicy())
                && is(model.get("observation_origin"), "native_exact_build_production")
                && is(resolved.get("status"), "available") && is(resolved.get("helper_status"), "original_helpers_matched")
                && is(resolved.get("roll_policy"), "zero_in_query_sampled_offline")
                && yes(resolved.get("original_total_helper_match")), "native phase advantage provenance unavailable");
        BigInteger base = signedRaw(model.get("base_static_accumulator_raw"), "base static accumulator"), total = signedRaw(resolved.get("resolved_advantage_at_zero_roll_raw"), "resolved zero roll"), original = signedRaw(resolved.get("original_total_helper_raw"), "original total helper");
        var sides = elements(resolved.get("sides"), "native advantage sides"); var sources = elements(model.get("side_inputs"), "native advantage side inputs");
        require(sides.size() == 2 && sources.size() == 2, "native phase advantage side pair malformed");
        BigInteger[] leaders = new BigInteger[2], selected = new BigInteger[2], totals = new BigInteger[2];
        for (int index = 0; index < 2; index++) {
            String role = index == 0 ? "attacker" : "defender"; var side = object(sides.get(index), "native side"); var source = object(sources.get(index), "native side inputs");
            var own = armies(frozen, index == 0 ? CombatInputs.Role.ATTACKER : CombatInputs.Role.DEFENDER);
            var expected = own.stream().map(CombatInputs.Army::publicArmyId).toList();
            require(is(side.get("side"), role) && is(source.get("side"), role) && !own.isEmpty()
                    && ids(source.get("ordered_army_ids"), "native ordered army IDs").equals(expected)
                    && sameInteger(source.get("primary_army_id"), expected.getFirst())
                    && is(side.get("battle_commander_selection"), "native_0x23C8A60"), "native phase side identity differs");
            boolean chosen = bool(side.get("battle_commander_selected"), "battle_commander_selected");
            if (chosen) selected[index] = positiveInteger(side.get("battle_commander_character_id"), "native selected commander");
            else require(absentOrNull(side.get("battle_commander_character_id")), "native absent commander has a character ID");
            leaders[index] = leader(own, selected[index]).publicArmyId();
            BigInteger roll = signedRaw(side.get("roll_raw"), "native roll"), residual = signedRaw(side.get("target_conditionals_residual_raw"), "native residual"), commander = signedRaw(side.get("commander_dynamic_raw"), "native commander"), dynamic = signedRaw(side.get("side_dynamic_raw"), "native side dynamic");
            totals[index] = signedRaw(side.get("side_total_raw"), "native side total");
            require(integer(side.get("roll_points"), "native roll_points").signum() == 0 && roll.signum() == 0 && roll.add(residual).add(commander).add(dynamic).equals(totals[index]), "native phase side helper arithmetic differs");
        }
        require(total.equals(original) && total.equals(base.add(totals[0]).subtract(totals[1]))
                && sameInteger(resolved.get("side_0_dynamic_raw"), totals[0]) && sameInteger(resolved.get("side_1_dynamic_raw"), totals[1]), "native zero-roll advantage arithmetic differs");
        return Optional.of(new Selection(leaders[0], leaders[1], total, new ResearchEnvelope.SelectedCommanders(selected[0], selected[1]), sha256(canonical(model)).toUpperCase(Locale.ROOT), Source.V3_NATIVE));
    }
}
