package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import static org.xar.ck3.control.wave2.military.forecast.CurrentBattleConditionCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.wave2.military.forecast.CombatCore.CommanderRollRequest;
import org.xar.ck3.control.wave2.military.forecast.CombatCore.DrawState;
import org.xar.ck3.control.wave2.military.forecast.CombatCore.RegimentKind;

/** Full frozen current-condition runner. Events/stats/width/rosters remain frozen. */
public final class FrozenCurrentBattleRunner {
    private FrozenCurrentBattleRunner() { }
    private static final BigInteger DRAW_SPACE = BigInteger.ONE.shiftLeft(31);
    public sealed interface RollDistribution permits RetainedRoll, ModuloRoll { ObjectNode toJson(); }
    public record RetainedRoll(BigInteger points) implements RollDistribution {
        public RetainedRoll { Objects.requireNonNull(points); }
        @Override public ObjectNode toJson() { return object().put("kind", "retained_roll").put("roll_points", points).put("probability_numerator", 1).put("probability_denominator", 1).put("draw_consumed", false); }
    }
    public record ModuloRoll(BigInteger minimum, BigInteger maximum, BigInteger span, BigInteger quotient, BigInteger remainder) implements RollDistribution {
        @Override public ObjectNode toJson() { return object().put("kind", "inclusive_modulo_draw31").put("minimum_points", minimum).put("maximum_points", maximum).put("span", span).put("draw_space", DRAW_SPACE).put("base_preimage_count_per_point", quotient).put("extra_preimage_prefix_length", remainder).put("probability_denominator", DRAW_SPACE).put("draw_consumed", true); }
    }
    public static RollDistribution nextRollDistribution(CommanderRollRequest request, boolean rollDue) {
        Objects.requireNonNull(request);
        if (!rollDue || !request.drawEnabled()) return new RetainedRoll(request.previousRoll());
        BigInteger lower = request.effectiveMin().min(request.effectiveMax()), span = request.effectiveMax().subtract(request.effectiveMin()).abs().add(ONE);
        BigInteger[] division = DRAW_SPACE.divideAndRemainder(span);
        return new ModuloRoll(lower, lower.add(span).subtract(ONE), span, division[0], division[1]);
    }
    public enum RollStatus { NOT_DUE, UNAVAILABLE, AVAILABLE }
    public record RollRow(int sideIndex, int selectedCommander, BigInteger observedPoints, boolean due, Optional<Long> draw,
            RollStatus status, Optional<BigInteger> sampledPoints, Optional<RollDistribution> distribution) {
        public ObjectNode toJson() {
            ObjectNode row = object().put("side_index", sideIndex).put("selected_commander_character_id", selectedCommander).put("observed_roll_points", observedPoints).put("roll_due_at_observed_cadence", due);
            if (draw.isPresent()) row.put("sampled_draw31", draw.orElseThrow()); else row.putNull("sampled_draw31");
            row.put("status", status.name().toLowerCase(java.util.Locale.ROOT)); put(row, "sampled_roll_points", sampledPoints);
            if (distribution.isPresent()) row.set("distribution", distribution.orElseThrow().toJson()); else row.putNull("distribution");
            if (status == RollStatus.UNAVAILABLE) row.put("reason", "selected_commander_next_roll_bounds_not_supplied");
            return row;
        }
    }
    public record Rolls(DrawState input, DrawState output, int cadence, List<RollRow> sides) {
        public Rolls { sides = List.copyOf(sides); }
        public ObjectNode toJson() {
            ObjectNode row = object().put("scope", "caller_owned_roll_diagnostic").put("native_rng_state_observed", false).put("sample_updates_current_loss_factor", false)
                    .put("draw_order", "available_enabled_roll_requests_in_native_side_order").put("phase_event_draws_simulated", false).put("observed_roll_cadence_counter", cadence).putNull("next_roll_cadence_counter");
            row.set("input_draw_state", object().put("counter", input.counter()).put("salt", input.salt())); row.set("output_draw_state", object().put("counter", output.counter()).put("salt", output.salt()));
            ArrayNode rows = row.putArray("sides"); sides.forEach(s -> rows.add(s.toJson())); return row;
        }
    }
    private static Rolls rolls(Condition condition, DrawState input) {
        DrawState state = input; List<RollRow> rows = new ArrayList<>(); boolean due = condition.phase() == Phase.MAIN && condition.rollCadenceCounter() == 0;
        for (Side side : condition.sides()) {
            Optional<Long> draw = Optional.empty(); Optional<BigInteger> points; Optional<RollDistribution> distribution; RollStatus status;
            if (!due) { status = RollStatus.NOT_DUE; points = Optional.of(side.currentRollPoints()); distribution = Optional.of(new RetainedRoll(side.currentRollPoints())); }
            else if (side.rollRequest().isEmpty()) { status = RollStatus.UNAVAILABLE; points = Optional.empty(); distribution = Optional.empty(); }
            else {
                CommanderRollRequest request = side.rollRequest().orElseThrow(); RollDistribution selected = nextRollDistribution(request, true);
                BigInteger value = request.previousRoll();
                if (request.drawEnabled()) { CombatCore.Draw next = state.draw31(); state = next.state(); draw = Optional.of(next.value()); ModuloRoll modulo = (ModuloRoll) selected; value = modulo.minimum().add(BigInteger.valueOf(next.value()).mod(modulo.span())); }
                status = RollStatus.AVAILABLE; points = Optional.of(value); distribution = Optional.of(selected);
            }
            rows.add(new RollRow(side.sideIndex(), side.selectedCommanderCharacterId(), side.currentRollPoints(), due, draw, status, points, distribution));
        }
        return new Rolls(input, state, condition.rollCadenceCounter(), rows);
    }
    public record CounterProjection(Optional<List<List<BigInteger>>> retentions, Optional<String> unavailableReason) {
        public CounterProjection { retentions = retentions.map(rows -> rows.stream().map(List::copyOf).toList()); Objects.requireNonNull(unavailableReason); }
    }
    /** Reuses the complete shared current-frame projector; its filtered attack is deliberately discarded. */
    public static CounterProjection counterRetentions(Condition condition) {
        if (condition.sides().stream().flatMap(s -> s.entries().stream()).noneMatch(e -> e.state().kind() == RegimentKind.MEN_AT_ARMS)) return new CounterProjection(Optional.of(List.of(List.of(), List.of())), Optional.empty());
        if (condition.activeCounterInputs().isEmpty()) return unavailableCounter("active_counter_inputs_not_observed");
        ObjectNode frame = object().put("side_scope", "full_side");
        frame.set("active_counter_inputs_v1", condition.activeCounterInputs().orElseThrow());
        for (Side side : condition.sides()) {
            ObjectNode row = frame.putObject(side.role().wire()); ArrayNode levy = row.putArray("levy_entries"), maa = row.putArray("men_at_arms_entries");
            for (BattleEntry entry : side.entries()) {
                ObjectNode value = object().put("regiment_id", entry.state().regimentId()).put("current_fighting_raw", entry.state().currentRaw()).put("effective_damage_raw", entry.effectiveDamageRaw()).put("fights_in_main_phase", entry.fightsInMainPhase());
                (entry.state().kind() == RegimentKind.LEVY ? levy : maa).add(value);
            }
        }
        try { return new CounterProjection(Optional.of(ActiveCurrentCounterProjector.project(frame).retentions()), Optional.empty()); }
        catch (IllegalArgumentException failure) { return unavailableCounter(failure.getMessage()); }
    }
    private static int classIndex(JsonNode value, int count) { return ActiveCurrentCounterProjector.classIndex(value, count); }
    private static CounterProjection unavailableCounter(String reason) { return new CounterProjection(Optional.empty(), Optional.of(reason)); }

    public record Attack(int sideIndex, Optional<BigInteger> levyDamageRaw, String levyDamageSource, Optional<Integer> primaryParticipant,
            boolean nativeLevyObserved, BigInteger storedLevyRaw, Optional<BigInteger> levyAttackRaw, Optional<BigInteger> maaAttackRaw, Optional<BigInteger> effectiveAttackRaw) {
        public ObjectNode toJson() { ObjectNode row = object().put("side_index", sideIndex).put("levy_damage_source", levyDamageSource).put("native_primary_levy_getter_observed_by_runner", nativeLevyObserved).put("stored_levy_current_fighting_raw", storedLevyRaw).put("main_phase_flag_filters_maa_outgoing", false); put(row, "levy_damage_raw", levyDamageRaw); if (primaryParticipant.isPresent()) row.put("levy_damage_primary_participant_character_id", primaryParticipant.orElseThrow()); else row.putNull("levy_damage_primary_participant_character_id"); put(row, "levy_attack_raw", levyAttackRaw); put(row, "all_retained_maa_attack_raw", maaAttackRaw); put(row, "effective_attack_after_counter_raw", effectiveAttackRaw); return row; }
    }
    private static Attack attack(Side side, Condition condition, CounterProjection counter, List<LevyDamage> callerLevy) {
        Optional<BigInteger> damage = Optional.empty(); String source = "not_needed_zero_cached_levy"; boolean nativeObserved = false;
        if (side.storedLevyCurrentFightingRaw().signum() > 0) {
            Optional<BigInteger> caller = levy(callerLevy, side.sideIndex());
            if (side.levyDamageRaw().isPresent() && side.levyDamageNativeObserved()) { damage = side.levyDamageRaw(); source = side.levyDamageSource(); nativeObserved = true; }
            else if (caller.isPresent()) { damage = caller; source = "caller_supplied_primary_levy_damage"; }
            else if (side.levyDamageRaw().isPresent()) { damage = side.levyDamageRaw(); source = side.levyDamageSource(); }
            else { List<BigInteger> values = side.entries().stream().filter(e -> e.state().kind() == RegimentKind.LEVY && e.state().currentRaw().signum() > 0).map(BattleEntry::effectiveDamageRaw).distinct().toList(); if (values.size() == 1) { damage = Optional.of(values.getFirst()); source = "uniform_current_entry_proxy_for_primary_owner_levy_damage"; } else source = "unavailable_primary_owner_levy_damage"; }
        }
        Optional<BigInteger> levyAttack = side.storedLevyCurrentFightingRaw().signum() <= 0 ? Optional.of(ZERO) : damage.map(d -> mul(side.storedLevyCurrentFightingRaw(), d));
        List<BattleEntry> maa = side.entries().stream().filter(e -> e.state().kind() == RegimentKind.MEN_AT_ARMS).toList(); Optional<BigInteger> maaAttack = Optional.of(ZERO);
        if (!maa.isEmpty() && counter.retentions().isEmpty()) maaAttack = Optional.empty();
        else if (!maa.isEmpty()) {
            JsonNode sourceCounter = condition.activeCounterInputs().orElseThrow(); List<JsonNode> operands = elements(sourceCounter.get("sides").get(side.sideIndex()).get("men_at_arms_entries"), "retained MAA operands"); require(maa.size() == operands.size(), "retained MAA operand census changed"); BigInteger sum = ZERO;
            for (int i = 0; i < maa.size(); i++) { BigInteger value = maa.get(i).effectiveDamageRaw(); JsonNode operand = operands.get(i); if (is(operand.get("status"), "available")) value = mul(value, counter.retentions().orElseThrow().get(side.sideIndex()).get(classIndex(operand.get("class_index"), counter.retentions().orElseThrow().get(side.sideIndex()).size()))); sum = sum.add(mul(value, maa.get(i).state().currentRaw())); } maaAttack = Optional.of(sum);
        }
        Optional<BigInteger> total = levyAttack.isPresent() && maaAttack.isPresent() ? Optional.of(levyAttack.orElseThrow().add(maaAttack.orElseThrow())) : Optional.empty();
        return new Attack(side.sideIndex(), damage, source, side.levyDamagePrimaryParticipantCharacterId(), nativeObserved, side.storedLevyCurrentFightingRaw(), levyAttack, maaAttack, total);
    }
    public record ComponentLoss(int index, BigInteger maximum, int kind, BigInteger before, BigInteger after, BigInteger wholeLoss) {
        public ObjectNode toJson() { return object().put("component_index", index).put("maximum_soldiers", maximum).put("kind", kind).put("current_soldiers_before", before).put("current_soldiers_after", after).put("whole_soldier_loss", wholeLoss); }
    }
    public record EntryLoss(BattleEntry before, CombatCore.Entry after, CombatCore.MainCasualtyRow delta, Optional<List<ComponentLoss>> backing) {
        public EntryLoss { backing = backing.map(List::copyOf); }
        public ObjectNode toJson() {
            ObjectNode row = object().put("bucket", before.bucket()).put("bucket_index", before.bucketIndex()).put("regiment_id", before.state().regimentId()).put("native_carmy_id", before.nativeArmyId()).put("public_cunit_id", before.publicUnitId()).put("owner_character_id", before.ownerCharacterId()).put("fights_in_main_phase", before.fightsInMainPhase())
                    .put("current_fighting_raw_before", before.state().currentRaw()).put("current_fighting_raw_after", after.currentRaw()).put("soft_casualties_raw_before", before.state().softCasualtiesRaw()).put("soft_casualties_raw_after", after.softCasualtiesRaw()).put("new_total_casualties_raw", delta.totalRaw()).put("new_soft_casualties_raw", delta.softRaw()).put("new_hard_casualties_raw", delta.hardRaw());
            put(row, "hard_casualties_raw_before", before.hardCasualtiesRaw()); put(row, "hard_casualties_raw_after", before.hardCasualtiesRaw().map(h -> h.add(delta.hardRaw())));
            if (backing.isPresent()) { ArrayNode rows = row.putArray("backing_components"); backing.orElseThrow().forEach(c -> rows.add(c.toJson())); row.put("backing_whole_soldier_loss", delta.componentWholeSoldierLoss()); } else row.putNull("backing_components").putNull("backing_whole_soldier_loss"); return row;
        }
    }
    public record OwnerDelta(int owner, BigInteger hardDelta) { public ObjectNode toJson() { return object().put("owner_character_id", owner).put("hard_casualties_raw_delta", hardDelta); } }
    public record ParticipantDelta(ParticipantHard observed, BigInteger delta) {
        public ObjectNode toJson() { return observed.toJson().put("hard_casualties_raw_before", observed.hardRaw()).put("hard_casualties_raw_delta", delta).put("hard_casualties_raw_after", observed.hardRaw().add(delta)); }
    }
    public sealed interface LossReport permits AvailableLosses, UnavailableLosses { String status(); ObjectNode toJson(); }
    public record UnavailableLosses() implements LossReport {
        @Override public String status() { return "unavailable"; }
        @Override public ObjectNode toJson() { return object().put("status", status()).put("reason", "current_loss_operands_or_opposing_outgoing_unavailable"); }
    }
    public record AvailableLosses(int sideIndex, BigInteger incoming, BigInteger denominator, BigInteger conversion, BigInteger hard, BigInteger soft,
            List<EntryLoss> entries, List<ParticipantHard> observedLedger, List<ParticipantDelta> ledger, List<OwnerDelta> ownerDeltas,
            BigInteger totalBefore, BigInteger totalAfter, List<OwnerDelta> unmatched) implements LossReport {
        public AvailableLosses { entries = List.copyOf(entries); observedLedger = List.copyOf(observedLedger); ledger = List.copyOf(ledger); ownerDeltas = List.copyOf(ownerDeltas); unmatched = List.copyOf(unmatched); }
        @Override public String status() { return "available"; }
        @Override public ObjectNode toJson() {
            ObjectNode row = object().put("status", status()).put("side_index", sideIndex).put("incoming_damage_raw", incoming).put("stored_current_fighting_denominator_raw", denominator).put("main_hard_conversion_raw", conversion).put("new_hard_casualties_raw", hard).put("new_soft_casualties_raw", soft).put("participant_hard_total_raw_before", totalBefore).put("participant_hard_total_raw_after", totalAfter).put("ledger_deltas_are_additional_fighting_deductions", false);
            ArrayNode a = row.putArray("entries"); entries.forEach(e -> a.add(e.toJson())); ArrayNode b = row.putArray("observed_participant_hard_ledger"); observedLedger.forEach(p -> b.add(p.toJson())); ArrayNode c = row.putArray("participant_hard_ledger"); ledger.forEach(p -> c.add(p.toJson())); ArrayNode d = row.putArray("owner_hard_ledger_deltas"); ownerDeltas.forEach(p -> d.add(p.toJson())); ArrayNode e = row.putArray("unmatched_owner_hard_deltas"); unmatched.forEach(p -> e.add(p.toJson())); return row;
        }
    }
    private static AvailableLosses losses(Side side, BigInteger incoming, Condition condition) {
        LossInputs global = condition.lossInputs().orElseThrow(); LossSide operands = global.sides().get(side.sideIndex());
        CombatCore.MainCasualtyResult calculated = CombatCore.applyMainPhaseCasualties(side.states(), incoming, side.storedCurrentFightingRaw(), global.runtimeMainHardConversionRaw(), operands.ownHardModifierRaw(), operands.opposingHardModifierRaw(), global.winterHardModifierRaw());
        List<EntryLoss> rows = new ArrayList<>(); Map<Integer, BigInteger> owners = new LinkedHashMap<>();
        for (int i = 0; i < side.entries().size(); i++) {
            BattleEntry before = side.entries().get(i); CombatCore.Entry after = calculated.entries().get(i); CombatCore.MainCasualtyRow delta = calculated.rows().get(i); Optional<List<ComponentLoss>> backing = Optional.empty();
            if (before.backingComponents().isPresent()) { List<CombatCore.BackingComponent> components = before.backingComponents().orElseThrow(); require(components.size() == after.components().size(), "backing component census changed"); List<ComponentLoss> changes = new ArrayList<>(); for (int c = 0; c < components.size(); c++) { CombatCore.BackingComponent old = components.get(c), next = after.components().get(c); changes.add(new ComponentLoss(c, old.maximumSoldiers(), old.kind(), old.currentSoldiers(), next.currentSoldiers(), old.currentSoldiers().subtract(next.currentSoldiers()))); } backing = Optional.of(changes); }
            rows.add(new EntryLoss(before, after, delta, backing)); owners.merge(before.ownerCharacterId(), delta.hardRaw(), BigInteger::add);
        }
        Map<Integer, BigInteger> remaining = new LinkedHashMap<>(owners); List<ParticipantDelta> ledger = new ArrayList<>();
        for (ParticipantHard observed : side.participantHardLedger()) { BigInteger delta = remaining.remove(observed.participantCharacterId()); ledger.add(new ParticipantDelta(observed, delta == null ? ZERO : delta)); }
        return new AvailableLosses(side.sideIndex(), incoming, side.storedCurrentFightingRaw(), calculated.conversionRaw(), calculated.totalHardRaw(), calculated.totalSoftRaw(), rows, side.participantHardLedger(), ledger, ownerDeltas(owners), side.participantHardTotalRaw(), side.participantHardTotalRaw().add(calculated.totalHardRaw()), ownerDeltas(remaining));
    }
    private static List<OwnerDelta> ownerDeltas(Map<Integer, BigInteger> source) { return source.entrySet().stream().map(e -> new OwnerDelta(e.getKey(), e.getValue())).toList(); }
    public record SideTick(Side side, Attack attack, Optional<BigInteger> outgoing, LossReport losses) {
        public ObjectNode toJson() { ObjectNode row = object().put("side_index", side.sideIndex()).put("role", side.role().wire()); ArrayNode armies = row.putArray("ordered_armies"); side.orderedArmies().forEach(a -> armies.add(a.toJson())); row.set("attack", attack.toJson()); put(row, "outgoing_damage_raw", outgoing); row.set("losses", losses.toJson()); return row; }
    }
    public enum Status { AVAILABLE, PARTIAL, NOT_APPLICABLE }
    public record Seed(BigInteger seedU64, BigInteger trialIndex) { public ObjectNode toJson() { return object().put("seed_u64", seedU64).put("trial_index", trialIndex).put("stream", "splitmix64_derived_independent_global_state"); } }
    public record Result(Condition condition, Rolls rolls, Optional<CounterProjection> counter, List<Optional<BigInteger>> outgoing,
            List<SideTick> sides, Status status, Optional<Seed> callerSeed) {
        public Result { outgoing = List.copyOf(outgoing); sides = List.copyOf(sides); Objects.requireNonNull(counter); Objects.requireNonNull(callerSeed); }
        public BattleRetreatPolicy.FrozenMainTick toRetreatTick() {
            SourceBinding source = condition.source(); BattleRetreatPolicy.TickFrame frame = new BattleRetreatPolicy.TickFrame(source.revision(), source.dateRaw().longValueExact(), source.combatId(), source.provinceId(), condition.subjectSideIndex(), condition.phase().wire(), condition.phaseRaw(), condition.phaseDay());
            List<BattleRetreatPolicy.TickSide> tickSides = sides.stream().map(s -> new BattleRetreatPolicy.TickSide(new BattleRetreatPolicy.Attack(s.attack().storedLevyRaw(), s.attack().nativeLevyObserved()),
                    new BattleRetreatPolicy.Losses(s.losses().status(), s.losses() instanceof AvailableLosses available ? available.ownerDeltas().stream().map(d -> new BattleRetreatPolicy.OwnerDelta(d.owner(), d.hardDelta())).toList() : List.of()))).toList();
            return new BattleRetreatPolicy.FrozenMainTick(frame, tickSides, condition.missingInputs());
        }
        public ObjectNode toJson() {
            ObjectNode row = object().put("scope_kind", "frozen_observed_current_condition_single_main_tick").put("readiness", "static_ready_pending_actual_12003_qualification").put("base_combat_width", condition.baseCombatWidth()).put("final_combat_width", condition.finalCombatWidth()).put("base_advantage_raw", condition.baseAdvantageRaw()).put("resolved_advantage_raw", condition.resolvedAdvantageRaw()).put("complete_transition", false).put("complete_monte_carlo", false).putNull("win_probability").put("actual_next_draw_claimed", false);
            SourceBinding source = condition.source(); row.set("observed_frame", object().put("snapshot_revision", source.revision()).put("observed_date_raw", source.dateRaw()).put("combat_id", source.combatId()).put("province_id", source.provinceId()).put("subject_side_index", condition.subjectSideIndex()).put("phase", condition.phase().wire()).put("phase_raw", condition.phaseRaw()).put("phase_day", condition.phaseDay()));
            row.set("frozen", object().put("events", true).put("stats", true).put("width", true).put("rosters", true)); row.set("rolls", rolls.toJson()); ArrayNode missing = row.putArray("adapter_missing_inputs"); condition.missingInputs().forEach(missing::add);
            row.put("status", status.name().toLowerCase(java.util.Locale.ROOT)); ArrayNode nativeSides = row.putArray("sides"); sides.forEach(s -> nativeSides.add(s.toJson()));
            if (status == Status.NOT_APPLICABLE) row.put("reason", "observed_phase_is_not_main");
            else { CounterProjection projection = counter.orElseThrow(); if (projection.retentions().isPresent()) { ArrayNode retention = row.putArray("counter_retention_raw_by_side"); for (List<BigInteger> values : projection.retentions().orElseThrow()) { ArrayNode side = retention.addArray(); values.forEach(side::add); } } else row.putNull("counter_retention_raw_by_side"); if (projection.unavailableReason().isPresent()) row.put("counter_unavailable_reason", projection.unavailableReason().orElseThrow()); else row.putNull("counter_unavailable_reason"); ArrayNode damage = row.putArray("outgoing_damage_raw_by_side"); outgoing.forEach(v -> { if (v.isPresent()) damage.add(v.orElseThrow()); else damage.addNull(); }); row.put("outgoing_uses_observed_current_loss_factor", true); }
            callerSeed.ifPresent(seed -> row.set("caller_seed", seed.toJson())); return row;
        }
    }
    public static Result run(Condition condition, DrawState drawState) { return run(condition, drawState, List.of()); }
    public static Result run(Condition condition, DrawState drawState, List<LevyDamage> callerLevy) {
        Objects.requireNonNull(condition); Objects.requireNonNull(drawState); callerLevy = List.copyOf(callerLevy); require(callerLevy.stream().map(LevyDamage::sideIndex).distinct().count() == callerLevy.size(), "duplicate caller levy side"); Rolls rolls = rolls(condition, drawState);
        if (condition.phase() != Phase.MAIN) return new Result(condition, rolls, Optional.empty(), List.of(), List.of(), Status.NOT_APPLICABLE, Optional.empty());
        CounterProjection counter = counterRetentions(condition); List<Attack> attacks = new ArrayList<>(); List<Optional<BigInteger>> outgoing = new ArrayList<>();
        for (Side side : condition.sides()) {
            Attack attack = attack(side, condition, counter, callerLevy); attacks.add(attack); Optional<BigInteger> damage = Optional.empty();
            if (condition.lossInputs().isPresent() && attack.effectiveAttackRaw().isPresent()) { LossInputs inputs = condition.lossInputs().orElseThrow(); damage = Optional.of(CombatCore.outgoingDamageRaw(attack.effectiveAttackRaw().orElseThrow(), inputs.sides().get(side.sideIndex()).outgoingAdvantageFactorRaw(), condition.finalCombatWidth(), side.storedCurrentFightingRaw(), inputs.runtimeDamageScalingRaw())); } outgoing.add(damage);
        }
        List<SideTick> sides = new ArrayList<>(); for (int i = 0; i < 2; i++) { Side side = condition.sides().get(i); Optional<BigInteger> incoming = outgoing.get(1 - i); LossReport report = condition.lossInputs().isEmpty() || incoming.isEmpty() ? new UnavailableLosses() : losses(side, incoming.orElseThrow(), condition); sides.add(new SideTick(side, attacks.get(i), outgoing.get(i), report)); }
        Status status = sides.stream().allMatch(s -> s.losses() instanceof AvailableLosses) ? Status.AVAILABLE : Status.PARTIAL;
        return new Result(condition, rolls, Optional.of(counter), outgoing, sides, status, Optional.empty());
    }
    public static Result runSeeded(Condition condition, BigInteger seedU64, BigInteger trialIndex, List<LevyDamage> callerLevy) {
        require(seedU64 != null && seedU64.signum() >= 0 && seedU64.bitLength() <= 64 && trialIndex != null, "exact caller uint64 seed/integer trial required"); Result result = run(condition, CombatCore.deriveTrialRandomStreams(seedU64, trialIndex.longValue()).globalState(), callerLevy);
        return new Result(result.condition(), result.rolls(), result.counter(), result.outgoing(), result.sides(), result.status(), Optional.of(new Seed(seedU64, trialIndex)));
    }
    private static void put(ObjectNode row, String key, Optional<BigInteger> value) { if (value.isPresent()) row.put(key, value.orElseThrow()); else row.putNull(key); }
}
