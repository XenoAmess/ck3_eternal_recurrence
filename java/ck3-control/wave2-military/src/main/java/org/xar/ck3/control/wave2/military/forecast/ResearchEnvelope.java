package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatCore.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatInputs.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;

/** Original research_envelope.py pipeline; its disabled effects remain explicit. */
public final class ResearchEnvelope {
    private ResearchEnvelope() { }

    public static final List<String> DEFAULT_UNMODELED_ADVANTAGE_SOURCES = List.of(
            "supply_state", "debt_tier", "recently_disembarked", "unreformed_faith",
            "dynamic_combat_effects", "dynamic_advantage_helper_0x2307CB0",
            "non_generic_commander_or_owner_contributions");

    private static List<String> concat(List<String> first, List<String> second) {
        var result = new ArrayList<>(first); result.addAll(second); return List.copyOf(result);
    }

    public static final Manifest RESEARCH_ENVELOPE_MANIFEST = new Manifest(
            "ck3-1.19.0.6-phase-events-disabled-envelope-v4", false, true, true, null,
            concat(BOUNDED_CORE_MANIFEST.closedNumericDomains(), List.of(
                    "per_main_tick_dynamic_counter_retention",
                    "next_main_tick_winner_check_side0_first",
                    "generic_commander_plus_stock_static_advantage_research_assumption",
                    "phase_events_disabled_research_assumption",
                    "no_voluntary_or_partial_retreat_research_assumption",
                    "horizon_censored_pursuit_finalizer")));

    public static final Manifest ACTIVE_MAIN_RESUME_MANIFEST = new Manifest(
            "ck3-1.19.0.6-active-main-resume-research-v3", false, true, true, null,
            concat(RESEARCH_ENVELOPE_MANIFEST.closedNumericDomains(), List.of(
                    "observed_main_phase_entry_and_roll_resume",
                    "declared_both_side_route_flags_and_first_stored_armies",
                    "observed_pursuit_side_modifiers_frozen_until_terminal_research_assumption")));

    /** Both selectors may be absent; an absent selector disables its roll draw. */
    public record SelectedCommanders(BigInteger attackerCharacterId, BigInteger defenderCharacterId) {
        public SelectedCommanders {
            if (attackerCharacterId != null) CombatJson.characterId(attackerCharacterId, "selected attacker");
            if (defenderCharacterId != null) CombatJson.characterId(defenderCharacterId, "selected defender");
        }
    }

    /** The original four fixed true assumptions are encoded by this model's type. */
    public record Assumptions(BigInteger attackerCommanderArmyId, BigInteger defenderCommanderArmyId,
            BigInteger precontactZeroRollAdvantageRaw, SelectedCommanders precontactSelectedCommanderCharacterIds,
            List<String> unmodeledAdvantageSources) {
        public Assumptions {
            Objects.requireNonNull(attackerCommanderArmyId); Objects.requireNonNull(defenderCommanderArmyId);
            unmodeledAdvantageSources = List.copyOf(unmodeledAdvantageSources);
            require((precontactZeroRollAdvantageRaw == null) == (precontactSelectedCommanderCharacterIds == null),
                    "native precontact advantage and selector must be paired");
            if (precontactZeroRollAdvantageRaw != null) signed64(precontactZeroRollAdvantageRaw);
        }
        public Assumptions(BigInteger attackerArmy, BigInteger defenderArmy) {
            this(attackerArmy, defenderArmy, null, null, DEFAULT_UNMODELED_ADVANTAGE_SOURCES);
        }
        public Assumptions(BigInteger attackerArmy, BigInteger defenderArmy, BigInteger nativeRaw,
                SelectedCommanders selected) {
            this(attackerArmy, defenderArmy, nativeRaw, selected, DEFAULT_UNMODELED_ADVANTAGE_SOURCES);
        }
    }

    private static void signed64(BigInteger value) {
        require(value != null && value.bitLength() < 64, "observed signed int64 modifier required");
    }

    public record ActiveRouteSideState(BigInteger firstStoredPublicCunitId, boolean disallowRetreat,
            boolean allowEarlyRetreat, boolean skipPursuit, boolean landlessBlocked,
            int retreatElapsedWholeDays, BigInteger pursuitEfficiencyModifierRaw, BigInteger retreatLossesModifierRaw) {
        public ActiveRouteSideState {
            CombatJson.publicCunitId(firstStoredPublicCunitId, "route side first stored public CUnit ID");
            require(retreatElapsedWholeDays >= 0, "route side requires native elapsed whole days");
            signed64(pursuitEfficiencyModifierRaw); signed64(retreatLossesModifierRaw);
        }
    }

    public record EffectiveDamage(BigInteger regimentId, BigInteger raw) {
        public EffectiveDamage { Objects.requireNonNull(regimentId); require(raw != null && raw.signum() >= 0,
                "active effective damage must be nonnegative"); }
    }

    /** Declared research continuation input, never synthesized from precontact wire. */
    public record ActiveMainResumeState(Frozen combatInput, BigInteger combatId, String snapshotId, Phase phase,
            int phaseDay, int elapsedWholeDays, int rollCadenceCounter,
            BigInteger side0RollPoints, BigInteger side1RollPoints,
            BigInteger side0NonRollAdvantagePoints, BigInteger side1NonRollAdvantagePoints,
            BigInteger side0CommanderCharacterId, BigInteger side1CommanderCharacterId,
            BigInteger finalCombatWidth, List<Entry> side0Entries, List<Entry> side1Entries,
            List<EffectiveDamage> side0EffectiveDamageRaw, List<EffectiveDamage> side1EffectiveDamageRaw,
            ActiveRouteSideState side0Route, ActiveRouteSideState side1Route) {
        public ActiveMainResumeState {
            Objects.requireNonNull(combatInput);
            side0Entries = List.copyOf(side0Entries); side1Entries = List.copyOf(side1Entries);
            side0EffectiveDamageRaw = List.copyOf(side0EffectiveDamageRaw);
            side1EffectiveDamageRaw = List.copyOf(side1EffectiveDamageRaw);
            require(combatId != null && positive(combatId), "active combat_id must be a positive integer");
            require(combatInput.encounter().participantPolicy().equals("observed_active_combat_resume_fixed_future_participants"),
                    "active resume requires observed participant policy");
            var capture = combatInput.capture();
            require(snapshotId != null && !snapshotId.isEmpty() && snapshotId.equals(capture.snapshotId())
                    && capture.revision() != null && capture.nativeRevision() != null && capture.dateRaw() != null
                    && combatInput.inputObservationReady(), "active resume requires complete same-frame capture");
            require(phase == Phase.MAIN, "only active main-phase resume is supported");
            require(phaseDay >= 0 && elapsedWholeDays >= phaseDay && elapsedWholeDays >= 3
                    && rollCadenceCounter >= 0 && rollCadenceCounter < 3
                    && finalCombatWidth != null && positive(finalCombatWidth), "active phase, cadence, or width is invalid");
            require(side0RollPoints != null && side1RollPoints != null && side0NonRollAdvantagePoints != null
                    && side1NonRollAdvantagePoints != null, "active advantage operands must be integers");
            validateActiveSide(combatInput, combatInput.encounter().attackerSide(),
                    side0Entries, side0EffectiveDamageRaw, side0Route);
            validateActiveSide(combatInput, combatInput.encounter().defenderSide(),
                    side1Entries, side1EffectiveDamageRaw, side1Route);
        }
    }

    private static void validateActiveSide(Frozen input, Coalition side, List<Entry> entries,
            List<EffectiveDamage> damages, ActiveRouteSideState route) {
        var regiments = input.regimentsForSide(side);
        require(!regiments.isEmpty() && regiments.size() == entries.size(), "active entry census is incomplete");
        for (int i = 0; i < regiments.size(); i++) {
            var r = regiments.get(i); var e = entries.get(i);
            require(r.regimentId().equals(e.regimentId()) && r.kind() == e.kind() && e.currentRaw().signum() >= 0
                    && e.softCasualtiesRaw().signum() >= 0 && e.toughnessRaw().signum() >= 0,
                    "active entry identity or state drifted");
        }
        var ids = regiments.stream().filter(Regiment::fightsInMainPhase).map(Regiment::regimentId).toList();
        require(damages.stream().map(EffectiveDamage::regimentId).toList().equals(ids),
                "active effective-damage census drifted");
        var armies = input.armiesForSide(side);
        require(route != null && !armies.isEmpty() && route.firstStoredPublicCunitId().equals(armies.getFirst().publicArmyId()),
                "active route first-army identity drifted");
    }

    private static Army armyByPublicId(Frozen input, BigInteger id) {
        return input.armies().stream().filter(a -> a.publicArmyId().equals(id)).findFirst()
                .orElseThrow(() -> new CombatInputException("commander army " + id + " is outside encounter"));
    }

    private static BigInteger staticDefenderAdvantage(Frozen input) {
        int terrain = switch (input.encounter().terrainKey()) {
            case "hills", "terraced_hills", "wetlands" -> 5;
            case "mountains", "desert_mountains" -> 12;
            case "jungle" -> 6; case "forest" -> 3; case "taiga" -> 4; default -> 0;
        };
        int crossing = switch (input.encounter().crossingKind()) {
            case NONE -> 0; case RIVER -> 10; case LARGE_RIVER -> 20; case STRAIT -> 30;
        };
        return n(terrain + crossing + (input.encounter().holdingDefender() ? 1 : 0));
    }

    private static BigInteger outgoingAttackRaw(List<Army> armies, List<Entry> entries,
            List<BigInteger> retention, List<EffectiveDamage> effectiveDamage) {
        var regiments = armies.stream().flatMap(a -> a.regiments().stream()).toList();
        require(regiments.size() == entries.size(), "entry/input census drifted");
        var currentDamage = new LinkedHashMap<BigInteger, BigInteger>();
        if (effectiveDamage != null) for (var row : effectiveDamage) currentDamage.put(row.regimentId(), row.raw());
        BigInteger total = ZERO;
        for (int i = 0; i < regiments.size(); i++) {
            var r = regiments.get(i); var e = entries.get(i);
            if (e.currentRaw().signum() <= 0 || !r.fightsInMainPhase()) continue;
            BigInteger damage = effectiveDamage == null ? r.stats().damageRaw() : currentDamage.get(r.regimentId());
            require(damage != null, "current effective-damage census drifted");
            if (r.counter() != null) damage = mul(damage, retention.get(index(r.counter().classIndex(), retention.size())));
            total = total.add(mul(damage, e.currentRaw()));
        }
        return total;
    }

    public static final class PhaseEventsDisabledResearchKernel implements TransitionKernel<Frozen> {
        private final Assumptions assumptions;
        public PhaseEventsDisabledResearchKernel(Assumptions assumptions) { this.assumptions = Objects.requireNonNull(assumptions); }
        @Override public Manifest manifest() { return RESEARCH_ENVELOPE_MANIFEST; }
        @Override public TrialOutcome simulateTrial(Frozen initial, TrialRandomStreams streams, int horizonDays) {
            return simulate(initial, streams, horizonDays, null);
        }
        public TrialOutcome simulateResumedTrial(ActiveMainResumeState resume, TrialRandomStreams streams, int horizonDays) {
            Objects.requireNonNull(resume); return simulate(resume.combatInput(), streams, horizonDays, resume);
        }
        private TrialOutcome simulate(Frozen initial, TrialRandomStreams streams, int horizon, ActiveMainResumeState resume) {
            require(horizon > 0, "horizon_days must be positive");
            Army attackerCommander = armyByPublicId(initial, assumptions.attackerCommanderArmyId());
            Army defenderCommander = armyByPublicId(initial, assumptions.defenderCommanderArmyId());
            require(attackerCommander.encounterRole() == Role.ATTACKER, "selected attacker commander army is not attacker");
            require(defenderCommander.encounterRole() == Role.DEFENDER, "selected defender commander army is not defender");
            if (resume != null) require(Objects.equals(attackerCommander.commander().characterId(), resume.side0CommanderCharacterId())
                    && Objects.equals(defenderCommander.commander().characterId(), resume.side1CommanderCharacterId()),
                    "active selected commander identity drifted");
            Coalition attackerSide = initial.encounter().attackerSide(), defenderSide = initial.encounter().defenderSide();
            var attackerArmies = initial.armiesForSide(attackerSide); var defenderArmies = initial.armiesForSide(defenderSide);
            List<Entry> attackerEntries = resume == null ? initial.initialEntriesForSide(attackerSide) : resume.side0Entries();
            List<Entry> defenderEntries = resume == null ? initial.initialEntriesForSide(defenderSide) : resume.side1Entries();
            var selected = assumptions.precontactSelectedCommanderCharacterIds();
            if (selected != null) require(
                    (selected.attackerCharacterId() == null || selected.attackerCharacterId().equals(attackerCommander.commander().characterId()))
                    && (selected.defenderCharacterId() == null || selected.defenderCharacterId().equals(defenderCommander.commander().characterId())),
                    "native selected commander drifted from bound army");
            boolean attackerHasCommander = selected == null ? attackerCommander.commander().characterId() != null : selected.attackerCharacterId() != null;
            boolean defenderHasCommander = selected == null ? defenderCommander.commander().characterId() != null : selected.defenderCharacterId() != null;
            BigInteger attackerGeneric = Objects.requireNonNullElse(attackerCommander.commander().genericAdvantagePoints(), ZERO);
            BigInteger defenderGeneric = Objects.requireNonNullElse(defenderCommander.commander().genericAdvantagePoints(), ZERO);
            BigInteger defenderStatic = staticDefenderAdvantage(initial);
            BigInteger attackerRoll = resume == null ? ZERO : resume.side0RollPoints();
            BigInteger defenderRoll = resume == null ? ZERO : resume.side1RollPoints();
            int cadence = resume == null ? 0 : resume.rollCadenceCounter();
            var global = streams.globalState();
            BigInteger attackerHard = ZERO, defenderHard = ZERO;
            int maneuverDays = resume == null ? 3 : resume.elapsedWholeDays(), mainDays = 0;
            Integer winner = null;
            while ((resume == null ? (long) maneuverDays + mainDays : mainDays) < horizon) {
                mainDays++;
                BigInteger attackerTotal = fighting(attackerEntries), defenderTotal = fighting(defenderEntries);
                winner = winnerAtMainTickStart(null, attackerTotal, defenderTotal);
                if (winner != null) break;
                var randomDay = scheduleMainDayRandomness(global, cadence,
                        new CommanderRollRequest(attackerHasCommander, attackerCommander.commander().effectiveMinRoll(),
                                attackerCommander.commander().effectiveMaxRoll(), attackerRoll),
                        new CommanderRollRequest(defenderHasCommander, defenderCommander.commander().effectiveMinRoll(),
                                defenderCommander.commander().effectiveMaxRoll(), defenderRoll));
                global = randomDay.state(); cadence = randomDay.nextRollCadence();
                attackerRoll = randomDay.side0Roll(); defenderRoll = randomDay.side1Roll();
                BigInteger resolved;
                if (resume != null) resolved = resume.side0NonRollAdvantagePoints().add(attackerRoll)
                        .subtract(resume.side1NonRollAdvantagePoints()).subtract(defenderRoll).multiply(SCALE);
                else if (assumptions.precontactZeroRollAdvantageRaw() != null)
                    resolved = assumptions.precontactZeroRollAdvantageRaw().add(attackerRoll.subtract(defenderRoll).multiply(SCALE));
                else resolved = attackerGeneric.add(attackerRoll).subtract(defenderGeneric).subtract(defenderRoll)
                        .subtract(defenderStatic).multiply(SCALE);
                BigInteger attackerAdvantage = positive(resolved) ? SCALE.add(mul(resolved, n(5_000))) : SCALE;
                BigInteger defenderAdvantage = negative(resolved) ? SCALE.add(mul(resolved.negate(), n(5_000))) : SCALE;
                var attackerRetention = initial.dynamicCounterRetentionByClassRaw(attackerSide, attackerEntries, defenderEntries);
                var defenderRetention = initial.dynamicCounterRetentionByClassRaw(defenderSide, defenderEntries, attackerEntries);
                BigInteger attackerAttack = outgoingAttackRaw(attackerArmies, attackerEntries, attackerRetention,
                        resume == null ? null : resume.side0EffectiveDamageRaw());
                BigInteger defenderAttack = outgoingAttackRaw(defenderArmies, defenderEntries, defenderRetention,
                        resume == null ? null : resume.side1EffectiveDamageRaw());
                BigInteger width = resume == null ? initial.encounter().finalWidth() : resume.finalCombatWidth();
                BigInteger attackerDamage = outgoingDamageRaw(attackerAttack, attackerAdvantage, width, attackerTotal, n(3_000));
                BigInteger defenderDamage = outgoingDamageRaw(defenderAttack, defenderAdvantage, width, defenderTotal, n(3_000));
                var attackerResult = applyMainPhaseCasualties(attackerEntries, defenderDamage, attackerTotal);
                var defenderResult = applyMainPhaseCasualties(defenderEntries, attackerDamage, defenderTotal);
                attackerEntries = attackerResult.entries(); defenderEntries = defenderResult.entries();
                attackerHard = attackerHard.add(attackerResult.totalHardRaw()); defenderHard = defenderHard.add(defenderResult.totalHardRaw());
            }
            int battleDays = Math.addExact(maneuverDays, mainDays);
            if (winner == null) return outcome(TrialResult.NO_RESOLUTION,
                    resume == null ? Math.min(battleDays, horizon) : mainDays, attackerSide, attackerHard, defenderHard, false);
            List<Entry> loserEntries = winner == 0 ? defenderEntries : attackerEntries;
            List<Entry> winnerEntries = winner == 0 ? attackerEntries : defenderEntries;
            ActiveRouteSideState loserRoute = resume == null ? null : winner == 0 ? resume.side1Route() : resume.side0Route();
            var end = transitionAfterWinnerIsKnown(loserEntries, winner,
                    new RetreatGateInput(loserRoute != null && loserRoute.disallowRetreat(),
                            loserRoute != null && loserRoute.allowEarlyRetreat(),
                            loserRoute == null ? battleDays : Math.addExact(loserRoute.retreatElapsedWholeDays(), mainDays),
                            Phase.MAIN, loserRoute != null && loserRoute.landlessBlocked(), 14),
                    loserRoute != null && loserRoute.skipPursuit());
            BigInteger pursuitHard = ZERO;
            if (end.phase() == Phase.PURSUIT) {
                ActiveRouteSideState winnerRoute = resume == null ? null : winner == 0 ? resume.side0Route() : resume.side1Route();
                BigInteger pursuerModifier = winnerRoute == null ? ZERO : winnerRoute.pursuitEfficiencyModifierRaw();
                BigInteger loserModifier = loserRoute == null ? ZERO : loserRoute.retreatLossesModifierRaw();
                int remaining = horizon - (resume == null ? battleDays : mainDays);
                if (remaining < 4) {
                    var current = end.loserEntries();
                    for (int i = 0; i < Math.min(3, remaining); i++) {
                        var day = applyPursuitDay(current, winnerEntries, end.pursuitInitialPools(), pursuerModifier, loserModifier);
                        pursuitHard = pursuitHard.add(day.totalHardRaw()); current = day.entries();
                    }
                    if (winner == 0) defenderHard = defenderHard.add(pursuitHard); else attackerHard = attackerHard.add(pursuitHard);
                    return outcome(TrialResult.NO_RESOLUTION, horizon, attackerSide, attackerHard, defenderHard, false);
                }
                pursuitHard = applyThreeDayPursuit(end.loserEntries(), winnerEntries, end.pursuitInitialPools(),
                        pursuerModifier, loserModifier).totalHardRaw();
                battleDays = Math.addExact(battleDays, 4);
            }
            Coalition winningSide;
            if (winner == 0) { defenderHard = defenderHard.add(pursuitHard); winningSide = attackerSide; }
            else { attackerHard = attackerHard.add(pursuitHard); winningSide = defenderSide; }
            scheduleBattleResultEnvelopes(global, false);
            boolean playerWon = winningSide == Coalition.PLAYER_OR_ALLIED;
            return outcome(playerWon ? TrialResult.PLAYER_WIN : TrialResult.PLAYER_LOSS,
                    resume == null ? battleDays : battleDays - resume.elapsedWholeDays(), attackerSide, attackerHard, defenderHard,
                    !playerWon && end.branch() == BattleEndBranch.NON_RETREATING_CLEAR);
        }
    }

    private static TrialOutcome outcome(TrialResult result, int days, Coalition attackerSide,
            BigInteger attackerHard, BigInteger defenderHard, boolean wipe) {
        boolean playerAttacker = attackerSide == Coalition.PLAYER_OR_ALLIED;
        return new TrialOutcome(result, days, playerAttacker ? attackerHard : defenderHard,
                playerAttacker ? defenderHard : attackerHard, wipe, false);
    }

    public static final class ActiveMainResumeResearchKernel implements TransitionKernel<ActiveMainResumeState> {
        private final PhaseEventsDisabledResearchKernel base;
        public ActiveMainResumeResearchKernel(Assumptions assumptions) { base = new PhaseEventsDisabledResearchKernel(assumptions); }
        @Override public Manifest manifest() { return ACTIVE_MAIN_RESUME_MANIFEST; }
        @Override public TrialOutcome simulateTrial(ActiveMainResumeState initial, TrialRandomStreams streams, int horizonDays) {
            return base.simulateResumedTrial(initial, streams, horizonDays);
        }
    }

    public static Summary run(Frozen input, Experiment experiment, Assumptions assumptions) {
        return run(input, experiment, assumptions, 1, 2);
    }

    /** Parallel chunks preserve original trial-index ordering and never create services. */
    public static Summary run(Frozen input, Experiment experiment, Assumptions assumptions, int maxWorkers, int chunksPerWorker) {
        int requested = maxWorkers == 0 ? Math.min(24, Runtime.getRuntime().availableProcessors()) : maxWorkers;
        int workers = Math.max(1, Math.min(requested, experiment.sampleCount()));
        long chunkCount = Math.min(experiment.sampleCount(), Math.max((long) workers, (long) workers * chunksPerWorker));
        int chunkSize = Math.toIntExact(((long) experiment.sampleCount() + chunkCount - 1) / chunkCount);
        var work = new ArrayList<Callable<List<TrialOutcome>>>();
        for (int first = 0; first < experiment.sampleCount();) {
            int start = first, stop = (int) Math.min(experiment.sampleCount(), (long) start + chunkSize);
            work.add(() -> {
                var kernel = new PhaseEventsDisabledResearchKernel(assumptions);
                var result = new ArrayList<TrialOutcome>();
                for (int trial = start; trial < stop; trial++)
                    result.add(kernel.simulateTrial(input, deriveTrialRandomStreams(experiment.seedU64(), trial), experiment.horizonDays()));
                return List.copyOf(result);
            });
            first = stop;
        }
        var outcomes = new ArrayList<TrialOutcome>();
        try {
            if (workers == 1) for (var chunk : work) outcomes.addAll(chunk.call());
            else try (var pool = Executors.newFixedThreadPool(workers)) {
                for (var result : pool.invokeAll(work)) outcomes.addAll(result.get());
            }
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt(); throw new CombatInputException("combat experiment interrupted", error);
        } catch (ExecutionException error) {
            if (error.getCause() instanceof RuntimeException runtime) throw runtime;
            throw new CombatInputException("combat experiment worker failed", error.getCause());
        } catch (RuntimeException error) { throw error;
        } catch (Exception error) { throw new CombatInputException("combat experiment failed", error); }
        return summarizeTrialOutcomes(outcomes, experiment, RESEARCH_ENVELOPE_MANIFEST);
    }
}

