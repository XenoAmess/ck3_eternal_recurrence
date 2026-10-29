package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.military.forecast.CombatCore.BackingComponent;
import org.xar.ck3.control.wave2.military.forecast.CombatCore.CommanderRollRequest;
import org.xar.ck3.control.wave2.military.forecast.CombatCore.RegimentKind;

/** Full battle_current_adapter.py: only actual normalized operands, in native order. */
public final class CurrentBattleConditionCodec {
    private CurrentBattleConditionCodec() { }
    public enum Role { ATTACKER, DEFENDER; public String wire() { return name().toLowerCase(java.util.Locale.ROOT); } }
    public enum Phase { MANEUVER, MAIN, PURSUIT, DONE; public String wire() { return name().toLowerCase(java.util.Locale.ROOT); } }
    public record SourceBinding(BigInteger revision, BigInteger dateRaw, int combatId, int provinceId) {
        public SourceBinding { Objects.requireNonNull(revision); Objects.requireNonNull(dateRaw); require(revision.signum() > 0 && revision.bitLength() <= 64, "positive native uint64 revision required"); require(combatId != -1 && provinceId > 0, "current combat/province identity invalid"); dateRaw.longValueExact(); }
    }
    public record Army(int nativeArmyId, int publicUnitId, int ownerCharacterId, int combatBacklinkId) {
        public Army { require(nativeArmyId != -1 && publicUnitId >= 0 && ownerCharacterId > 0 && combatBacklinkId != -1, "actual army identities invalid"); }
        public ObjectNode toJson() { return object().put("native_carmy_id", nativeArmyId).put("public_cunit_id", publicUnitId).put("owner_character_id", ownerCharacterId).put("combat_backlink_id", combatBacklinkId); }
    }
    public record ParticipantHard(int rowIndex, int participantCharacterId, BigInteger hardRaw) {
        public ParticipantHard { require(rowIndex >= 0 && participantCharacterId > 0, "participant ledger identities invalid"); Objects.requireNonNull(hardRaw); }
        public ObjectNode toJson() { return object().put("row_index", rowIndex).put("participant_character_id", participantCharacterId).put("hard_casualties_raw", hardRaw); }
    }
    public record RegimentBacking(BigInteger regimentId, List<BackingComponent> components) {
        public RegimentBacking { Objects.requireNonNull(regimentId); components = List.copyOf(components); }
    }
    public record LevyDamage(int sideIndex, BigInteger damageRaw) { public LevyDamage { require(sideIndex == 0 || sideIndex == 1, "levy side invalid"); Objects.requireNonNull(damageRaw); } }
    public record RollBounds(BigInteger minimum, BigInteger maximum) { public RollBounds { Objects.requireNonNull(minimum); Objects.requireNonNull(maximum); } }
    public record ResumeInputs(SourceBinding source, List<Optional<RollBounds>> boundsBySide) {
        public ResumeInputs { Objects.requireNonNull(source); boundsBySide = List.copyOf(boundsBySide); require(boundsBySide.size() == 2, "two roll-bound sides required"); }
        /** Extract only after BattleControlExtensionCodec.normalizeResume validated the complete leaf. */
        public static ResumeInputs decode(JsonNode normalizedResume) {
            ObjectNode root = object(normalizedResume, "normalized active resume");
            ObjectNode source = object(root.get("source"), "resume source");
            SourceBinding binding = binding(source);
            ObjectNode observed = object(root.get("observed"), "resume observed");
            List<Optional<RollBounds>> bounds = new ArrayList<>();
            for (int side = 0; side < 2; side++) {
                JsonNode row = observed.get("side_" + side + "_selected_commander_next_roll_bounds");
                if (row != null && row.isObject() && is(row.get("status"), "available")) bounds.add(Optional.of(new RollBounds(integer(row.get("effective_min_roll"), "minimum roll"), integer(row.get("effective_max_roll"), "maximum roll"))));
                else bounds.add(Optional.empty());
            }
            return new ResumeInputs(binding, bounds);
        }
    }
    public record ObservedInputs(List<RegimentBacking> backing, Optional<ResumeInputs> resume, List<LevyDamage> levyDamage) {
        public ObservedInputs {
            backing = List.copyOf(backing); Objects.requireNonNull(resume); levyDamage = List.copyOf(levyDamage);
            require(backing.stream().map(RegimentBacking::regimentId).distinct().count() == backing.size(), "duplicate backing RegimentID");
            require(levyDamage.stream().map(LevyDamage::sideIndex).distinct().count() == levyDamage.size(), "duplicate levy side operand");
        }
        public static ObservedInputs empty() { return new ObservedInputs(List.of(), Optional.empty(), List.of()); }
    }
    public record LossSide(int sideIndex, BigInteger outgoingAdvantageFactorRaw, BigInteger ownHardModifierRaw,
            BigInteger opposingHardModifierRaw, Optional<Integer> primaryParticipantCharacterId, Optional<BigInteger> levyDamageRaw) {
        public LossSide { require(sideIndex == 0 || sideIndex == 1, "loss side invalid"); Objects.requireNonNull(outgoingAdvantageFactorRaw); Objects.requireNonNull(ownHardModifierRaw); Objects.requireNonNull(opposingHardModifierRaw); Objects.requireNonNull(primaryParticipantCharacterId); Objects.requireNonNull(levyDamageRaw); }
    }
    public record LossInputs(BigInteger scale, int sourceCombatId, int sourceProvinceId, BigInteger storedAdvantageDamageFactorRaw,
            BigInteger runtimeDamageScalingRaw, BigInteger runtimeMainHardConversionRaw, BigInteger runtimePursuitHardConversionRaw,
            boolean provinceHasHolding, BigInteger winterHardModifierRaw, List<LossSide> sides) {
        public LossInputs { require(SCALE.equals(scale), "loss input scale differs"); sides = List.copyOf(sides); require(sides.size() == 2 && sides.get(0).sideIndex() == 0 && sides.get(1).sideIndex() == 1, "loss side order differs"); }
    }
    public record BattleEntry(CombatCore.Entry state, String bucket, int bucketIndex, int nativeArmyId, int publicUnitId,
            int ownerCharacterId, BigInteger startingRaw, BigInteger effectiveDamageRaw, boolean fightsInMainPhase,
            Optional<BigInteger> hardCasualtiesRaw, Optional<BigInteger> knightCharacterIdRaw,
            Optional<List<BackingComponent>> backingComponents, ObjectNode sourceEntry, Optional<BigInteger> physicalEntryIdentity) {
        public BattleEntry { Objects.requireNonNull(state); require(bucket.equals("levy") || bucket.equals("men_at_arms"), "unknown actual bucket"); require(bucketIndex >= 0, "negative bucket index"); Objects.requireNonNull(hardCasualtiesRaw); Objects.requireNonNull(knightCharacterIdRaw); backingComponents = backingComponents.map(List::copyOf); sourceEntry = sourceEntry.deepCopy(); Objects.requireNonNull(physicalEntryIdentity); }
        @Override public ObjectNode sourceEntry() { return sourceEntry.deepCopy(); }
    }
    public record Side(int sideIndex, Role role, int primaryParticipantCharacterId, int selectedCommanderCharacterId,
            BigInteger currentRollPoints, Optional<CommanderRollRequest> rollRequest, List<BattleEntry> entries, List<Army> orderedArmies,
            BigInteger storedCurrentFightingRaw, BigInteger storedLevyCurrentFightingRaw, BigInteger derivedCurrentFightingRaw,
            BigInteger derivedSoftCasualtiesRaw, BigInteger derivedMainHardRaw, BigInteger nonMainResidualRaw,
            List<ParticipantHard> participantHardLedger, BigInteger participantHardTotalRaw, Optional<LossSide> lossInputs,
            Optional<BigInteger> levyDamageRaw, String levyDamageSource, boolean levyDamageNativeObserved,
            Optional<Integer> levyDamagePrimaryParticipantCharacterId) {
        public Side { require(sideIndex == role.ordinal(), "side/role mismatch"); entries = List.copyOf(entries); orderedArmies = List.copyOf(orderedArmies); participantHardLedger = List.copyOf(participantHardLedger); Objects.requireNonNull(rollRequest); Objects.requireNonNull(lossInputs); Objects.requireNonNull(levyDamageRaw); Objects.requireNonNull(levyDamagePrimaryParticipantCharacterId); }
        public List<CombatCore.Entry> states() { return entries.stream().map(BattleEntry::state).toList(); }
    }
    public record Condition(SourceBinding source, int subjectSideIndex, String sideScope, Phase phase, int phaseRaw, int phaseDay,
            BigInteger baseCombatWidth, BigInteger finalCombatWidth, int rollCadenceCounter, BigInteger baseAdvantageRaw,
            BigInteger resolvedAdvantageRaw, List<Side> sides, Optional<LossInputs> lossInputs,
            Optional<ObjectNode> activeCounterInputs, Optional<ObjectNode> pursuitModifierSides, List<String> missingInputs, ObjectNode sourceSnapshot) {
        public Condition { Objects.requireNonNull(source); require(subjectSideIndex == 0 || subjectSideIndex == 1, "subject side invalid"); require(sideScope.equals("full_side") || sideScope.equals("owner_subset"), "side scope invalid"); require(phase.ordinal() == phaseRaw, "phase and raw disagree"); sides = List.copyOf(sides); require(sides.size() == 2 && sides.get(0).sideIndex() == 0 && sides.get(1).sideIndex() == 1, "native side order required"); Objects.requireNonNull(lossInputs); activeCounterInputs = activeCounterInputs.map(ObjectNode::deepCopy); pursuitModifierSides = pursuitModifierSides.map(ObjectNode::deepCopy); missingInputs = List.copyOf(missingInputs); sourceSnapshot = sourceSnapshot.deepCopy(); }
        @Override public Optional<ObjectNode> activeCounterInputs() { return activeCounterInputs.map(ObjectNode::deepCopy); }
        @Override public Optional<ObjectNode> pursuitModifierSides() { return pursuitModifierSides.map(ObjectNode::deepCopy); }
        @Override public ObjectNode sourceSnapshot() { return sourceSnapshot.deepCopy(); }
    }

    /** Caller must first use the complete native control normalizer; all consumed token types are rechecked here. */
    public static Condition adapt(JsonNode normalizedControl) { return adapt(normalizedControl, ObservedInputs.empty()); }
    public static Condition adapt(JsonNode normalizedControl, ObservedInputs supplied) {
        Objects.requireNonNull(supplied); ObjectNode source = object(normalizedControl, "normalized control").deepCopy();
        require(is(source.get("status"), "available"), "available normalized battle-control leaf required");
        SourceBinding binding = binding(source); Optional<LossInputs> loss = loss(source.get("current_loss_inputs_v1"), binding);
        List<String> missing = new ArrayList<>(); if (loss.isEmpty()) missing.add("current_loss_inputs_v1");
        Optional<ObjectNode> counter = optionalObject(source.get("active_counter_inputs_v1"), "active counter");
        if (counter.isEmpty() || !is(counter.orElseThrow().get("status"), "available")) missing.add("active_counter_inputs_v1");
        Optional<ResumeInputs> resume = supplied.resume();
        if (resume.isPresent() && !resume.orElseThrow().source().equals(binding)) { resume = Optional.empty(); missing.add("active_resume_inputs_same_frame"); }
        List<Side> sides = new ArrayList<>();
        for (int index = 0; index < 2; index++) {
            Role role = Role.values()[index]; ObjectNode side = object(source.get(role.wire()), "native side");
            List<BattleEntry> entries = new ArrayList<>();
            for (String bucket : List.of("levy", "men_at_arms")) for (JsonNode raw : elements(side.get(bucket + "_entries"), "native bucket")) {
                ObjectNode row = object(raw, "actual entry"); BigInteger regiment = integer(row.get("regiment_id"), "regiment_id");
                Optional<List<BackingComponent>> backing = supplied.backing().stream().filter(r -> r.regimentId().equals(regiment)).map(RegimentBacking::components).findFirst();
                if (backing.isEmpty()) missing.add("backing_components." + regiment);
                CombatCore.Entry state = new CombatCore.Entry(regiment, bucket.equals("levy") ? RegimentKind.LEVY : RegimentKind.MEN_AT_ARMS,
                        integer(row.get("current_fighting_raw"), "current fighting"), integer(row.get("soft_casualties_raw"), "soft casualties"),
                        integer(row.get("effective_toughness_raw"), "toughness"), integer(row.get("effective_pursuit_raw"), "pursuit"), integer(row.get("effective_screen_raw"), "screen"), backing.orElse(List.of()));
                require(row.has("hard_casualties_raw"), "entry hard account must be present, nullable");
                entries.add(new BattleEntry(state, bucket, intValue(row.get("bucket_index"), "bucket index"), fullId(row.get("native_carmy_id")), publicCunitId(row.get("public_cunit_id"), "public CUnit").intValueExact(),
                        positiveId(row.get("owner_character_id")), integer(row.get("starting_raw"), "starting raw"), integer(row.get("effective_damage_raw"), "damage"), bool(row.get("fights_in_main_phase"), "main eligibility"),
                        optionalInteger(row.get("hard_casualties_raw")), optionalInteger(row.get("knight_character_id_raw")), backing, row, optionalInteger(row.get("physical_entry_identity"))));
            }
            int commander = intValue(side.get("selected_commander_character_id"), "selected commander");
            require(commander == -1 || commander > 0, "actual selected commander must be -1 or positive CharacterID");
            BigInteger previous = integer(side.get("current_roll_points"), "current roll"); Optional<CommanderRollRequest> roll = Optional.empty();
            if (commander == -1) roll = Optional.of(new CommanderRollRequest(false, ZERO, ZERO, previous));
            else if (resume.isPresent() && resume.orElseThrow().boundsBySide().get(index).isPresent()) { RollBounds b = resume.orElseThrow().boundsBySide().get(index).orElseThrow(); roll = Optional.of(new CommanderRollRequest(true, b.minimum(), b.maximum(), previous)); }
            if (roll.isEmpty()) missing.add("selected_commander_next_roll_bounds." + index);
            Optional<LossSide> sideLoss = loss.isPresent() ? Optional.of(loss.orElseThrow().sides().get(index)) : Optional.empty();
            Optional<BigInteger> nativeLevy = sideLoss.flatMap(LossSide::levyDamageRaw), callerLevy = levy(supplied.levyDamage(), index);
            Optional<BigInteger> chosen = nativeLevy.isPresent() ? nativeLevy : callerLevy;
            String levySource = nativeLevy.isPresent() ? "current_loss_inputs_v1.sides[" + index + "].levy_damage_raw" : callerLevy.isPresent() ? "caller_observed_primary_participant_operand" : "unavailable";
            Optional<Integer> actor = nativeLevy.isPresent() || callerLevy.isEmpty() ? sideLoss.flatMap(LossSide::primaryParticipantCharacterId) : Optional.of(positiveId(side.get("primary_participant_character_id")));
            List<Army> armies = new ArrayList<>(); for (JsonNode a : elements(side.get("ordered_armies"), "ordered armies")) armies.add(new Army(fullId(a.get("native_carmy_id")), publicCunitId(a.get("public_cunit_id"), "public CUnit").intValueExact(), positiveId(a.get("owner_character_id")), fullId(a.get("combat_backlink_id"))));
            List<ParticipantHard> ledger = new ArrayList<>(); for (JsonNode r : elements(side.get("participant_hard_ledger"), "participant hard ledger")) ledger.add(new ParticipantHard(intValue(r.get("row_index"), "ledger row index"), positiveId(r.get("participant_character_id")), integer(r.get("hard_casualties_raw"), "participant hard")));
            require(is(side.get("role"), role.wire()) && intValue(side.get("side_index"), "side index") == index, "actual side role/order disagrees");
            sides.add(new Side(index, role, positiveId(side.get("primary_participant_character_id")), commander, previous, roll, entries, armies,
                    integer(side.get("stored_current_fighting_raw"), "stored current"), integer(side.get("stored_levy_current_fighting_raw"), "stored levy"), integer(side.get("derived_current_fighting_raw"), "derived current"),
                    integer(side.get("derived_soft_casualties_raw"), "derived soft"), integer(side.get("derived_main_fighting_entry_hard_casualties_raw"), "derived main hard"), integer(side.get("non_main_start_minus_current_minus_soft_raw"), "nonmain residual"),
                    ledger, integer(side.get("participant_hard_total_raw"), "hard total"), sideLoss, chosen, levySource, nativeLevy.isPresent(), actor));
        }
        int phaseRaw = intValue(source.get("phase_raw"), "phase_raw"); require(phaseRaw >= 0 && phaseRaw <= 3, "unknown actual phase"); Phase phase = Phase.values()[phaseRaw]; require(is(source.get("phase"), phase.wire()), "actual phase raw/name differs");
        return new Condition(binding, intValue(source.get("side_index"), "subject side"), text(source.get("side_scope"), "side scope"), phase, phaseRaw, intValue(source.get("phase_day"), "phase day"),
                integer(source.get("base_combat_width"), "base width"), integer(source.get("final_combat_width"), "final width"), intValue(source.get("roll_cadence_counter"), "roll cadence"), integer(source.get("base_advantage_raw"), "base advantage"), integer(source.get("resolved_advantage_raw"), "resolved advantage"),
                sides, loss, counter, optionalObject(source.get("pursuit_modifier_sides"), "pursuit modifiers"), missing, source);
    }
    static Optional<BigInteger> levy(List<LevyDamage> rows, int side) { return rows.stream().filter(r -> r.sideIndex() == side).map(LevyDamage::damageRaw).findFirst(); }
    private static Optional<LossInputs> loss(JsonNode value, SourceBinding source) {
        if (absentOrNull(value)) return Optional.empty(); ObjectNode row = object(value, "current loss inputs");
        int combat = fullId(row.get("source_combat_id")), province = positiveId(row.get("source_target_province_id")); require(combat == source.combatId() && province == source.provinceId(), "loss input source differs");
        List<LossSide> sides = new ArrayList<>(); for (JsonNode s : elements(row.get("sides"), "loss sides")) sides.add(new LossSide(intValue(s.get("side_index"), "loss side index"), integer(s.get("outgoing_advantage_factor_raw"), "outgoing advantage"), integer(s.get("own_hard_conversion_modifier_raw"), "own hard modifier"), integer(s.get("opposing_hard_conversion_modifier_raw"), "opposing hard modifier"), optionalInteger(s.get("primary_participant_character_id")).map(BigInteger::intValueExact), optionalInteger(s.get("levy_damage_raw"))));
        return Optional.of(new LossInputs(integer(row.get("scale"), "loss scale"), combat, province, integer(row.get("stored_advantage_damage_factor_raw"), "stored advantage factor"), integer(row.get("runtime_damage_scaling_raw"), "damage scaling"), integer(row.get("runtime_main_hard_conversion_raw"), "main conversion"), integer(row.get("runtime_pursuit_hard_conversion_raw"), "pursuit conversion"), bool(row.get("province_has_holding"), "province holding"), integer(row.get("province_winter_hard_conversion_modifier_raw"), "winter modifier"), sides));
    }
    private static SourceBinding binding(JsonNode row) { return new SourceBinding(integer(row.get("snapshot_revision"), "snapshot revision"), integer(row.get("observed_date_raw"), "observed date"), fullId(row.get("combat_id")), positiveId(row.get("province_id"))); }
    private static Optional<BigInteger> optionalInteger(JsonNode value) { return absentOrNull(value) ? Optional.empty() : Optional.of(integer(value, "optional integer")); }
    private static Optional<ObjectNode> optionalObject(JsonNode value, String name) { return absentOrNull(value) ? Optional.empty() : Optional.of(object(value, name).deepCopy()); }
    private static int positiveId(JsonNode node) { int id = intValue(node, "positive identity"); require(id > 0, "positive identity required"); return id; }
    private static int fullId(JsonNode node) { int id = intValue(node, "full component identity"); require(id != -1, "missing full component identity"); return id; }
}
