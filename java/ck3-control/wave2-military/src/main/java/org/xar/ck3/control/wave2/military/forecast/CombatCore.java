package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;

/** Complete bounded-core primitives from combat_core.py; no Game or transport dependency. */
public final class CombatCore {
    private CombatCore() { }
    public enum RegimentKind { LEVY, MEN_AT_ARMS }
    public record BackingComponent(BigInteger maximumSoldiers, BigInteger currentSoldiers, int kind) { }
    public record ComponentAllocation(List<BackingComponent> components, List<BigInteger> wholeSoldierLosses,
            BigInteger requestedHardRaw, BigInteger unallocatedRaw) {
        public ComponentAllocation { components = List.copyOf(components); wholeSoldierLosses = List.copyOf(wholeSoldierLosses); }
        public BigInteger totalWholeSoldierLoss() { return sum(wholeSoldierLosses); }
    }
    public record Entry(BigInteger regimentId, RegimentKind kind, BigInteger currentRaw, BigInteger softCasualtiesRaw,
            BigInteger toughnessRaw, BigInteger pursuitRaw, BigInteger screenRaw, List<BackingComponent> components) {
        public Entry { Objects.requireNonNull(regimentId); Objects.requireNonNull(kind); Objects.requireNonNull(currentRaw);
            Objects.requireNonNull(softCasualtiesRaw); Objects.requireNonNull(toughnessRaw); Objects.requireNonNull(pursuitRaw);
            Objects.requireNonNull(screenRaw); components = List.copyOf(components); }
        public Entry withPools(BigInteger current, BigInteger soft, List<BackingComponent> backing) {
            return new Entry(regimentId, kind, current, soft, toughnessRaw, pursuitRaw, screenRaw, backing);
        }
    }
    public record MainCasualtyRow(BigInteger regimentId, BigInteger totalRaw, BigInteger hardRaw,
            BigInteger softRaw, BigInteger componentWholeSoldierLoss) { }
    public record MainCasualtyResult(List<Entry> entries, List<MainCasualtyRow> rows, BigInteger conversionRaw,
            BigInteger totalHardRaw, BigInteger totalSoftRaw) {
        public MainCasualtyResult { entries = List.copyOf(entries); rows = List.copyOf(rows); }
    }
    private static BigInteger selected(BackingComponent c) { return c.kind() == 3 && c.currentSoldiers().signum() == 0 ? c.maximumSoldiers() : c.currentSoldiers(); }
    private static BigInteger setter(BackingComponent c) { return c.kind() == 3 && c.currentSoldiers().signum() == 0 ? ZERO : c.currentSoldiers(); }
    public static BigInteger sum(List<BigInteger> values) { BigInteger result = ZERO; for (var v : values) result = result.add(v); return result; }
    public static BigInteger fighting(List<Entry> entries) { BigInteger result = ZERO; for (var e : entries) result = result.add(e.currentRaw()); return result; }
    public static ComponentAllocation allocateHardCasualtiesToComponents(List<BackingComponent> components, BigInteger hardRaw) {
        var mutable = new ArrayList<>(components); var losses = new ArrayList<BigInteger>();
        for (int i = 0; i < components.size(); i++) losses.add(ZERO);
        BigInteger remaining = hardRaw;
        for (int i = 0; i < mutable.size(); i++) {
            var c = mutable.get(i); BigInteger count = selected(c); if (count.signum() == 0) continue;
            BigInteger cap = count.multiply(SCALE);
            BigInteger candidate = fixedDiv(wrap64(count.multiply(hardRaw)), cap).min(cap);
            BigInteger allocated = remaining.min(candidate), whole = div(allocated, SCALE);
            mutable.set(i, new BackingComponent(c.maximumSoldiers(), setter(c).subtract(whole), c.kind()));
            losses.set(i, losses.get(i).add(whole)); remaining = remaining.subtract(allocated);
            if (remaining.signum() <= 0) break;
        }
        if (remaining.signum() >= 0) {
            for (int i = 0; i < mutable.size(); i++) {
                var c = mutable.get(i); BigInteger allocated = remaining.min(selected(c).multiply(SCALE)), whole = div(allocated, SCALE);
                mutable.set(i, new BackingComponent(c.maximumSoldiers(), setter(c).subtract(whole), c.kind()));
                losses.set(i, losses.get(i).add(whole)); remaining = remaining.subtract(allocated);
                if (remaining.signum() <= 0) break;
            }
        }
        return new ComponentAllocation(mutable, losses, hardRaw, remaining);
    }
    public static BigInteger hardCasualtyConversionRaw(BigInteger base, BigInteger defending, BigInteger attacking, BigInteger winter) {
        return mul(base, SCALE.add(defending).add(attacking).add(winter));
    }
    public static MainCasualtyResult applyMainPhaseCasualties(List<Entry> entries, BigInteger incoming, BigInteger defendingTotal) {
        return applyMainPhaseCasualties(entries, incoming, defendingTotal, n(30_000), ZERO, ZERO, ZERO);
    }
    public static MainCasualtyResult applyMainPhaseCasualties(List<Entry> entries, BigInteger incoming, BigInteger defendingTotal,
            BigInteger base, BigInteger defendingModifier, BigInteger enemyModifier, BigInteger winter) {
        BigInteger conversion = hardCasualtyConversionRaw(base, defendingModifier, enemyModifier, winter), hardTotal = ZERO, softTotal = ZERO;
        var updated = new ArrayList<Entry>(); var rows = new ArrayList<MainCasualtyRow>();
        for (var e : entries) {
            BigInteger total = ZERO;
            if (positive(e.currentRaw()) && defendingTotal.signum() != 0) {
                if (e.kind() == RegimentKind.LEVY && e.toughnessRaw().signum() != 0) {
                    total = clamp(mul(e.currentRaw(), fixedDiv(fixedDiv(incoming, defendingTotal), e.toughnessRaw())), ZERO, e.currentRaw());
                } else if (e.kind() == RegimentKind.MEN_AT_ARMS && positive(e.toughnessRaw())) {
                    total = e.currentRaw().min(fixedDiv(fixedDiv(mul(e.currentRaw(), incoming), defendingTotal), e.toughnessRaw()));
                }
            }
            BigInteger hard = mul(total, conversion), soft = total.subtract(hard);
            var allocation = allocateHardCasualtiesToComponents(e.components(), hard);
            updated.add(e.withPools(e.currentRaw().subtract(soft).subtract(hard), e.softCasualtiesRaw().add(soft), allocation.components()));
            rows.add(new MainCasualtyRow(e.regimentId(), total, hard, soft, allocation.totalWholeSoldierLoss()));
            hardTotal = hardTotal.add(hard); softTotal = softTotal.add(soft);
        }
        return new MainCasualtyResult(updated, rows, conversion, hardTotal, softTotal);
    }
    public static List<BigInteger> allocateAttackerHardCredit(List<BigInteger> contributions, BigInteger hard, BigInteger incoming) {
        return contributions.stream().map(v -> incoming.signum() == 0 ? ZERO : fixedDiv(mul(v, hard), incoming)).toList();
    }
    public static BigInteger advantageDamageMultiplierRaw(BigInteger advantage, BigInteger scalingFactor) {
        return SCALE.add(advantage.abs().multiply(scalingFactor).multiply(n(1_000)));
    }
    public static BigInteger outgoingDamageRaw(BigInteger attack, BigInteger multiplier, BigInteger width, BigInteger men, BigInteger scaling) {
        if (men.signum() <= 0) return ZERO;
        BigInteger fraction = SCALE.min(fixedDiv(width.multiply(SCALE), men));
        return mul(mul(mul(multiplier, scaling), fraction), attack);
    }
    public record Width(BigInteger base, BigInteger finalWidth) { }
    public static Width updateCombatWidth(BigInteger side0, BigInteger side1, BigInteger previous, BigInteger terrain, BigInteger ratio, BigInteger minimum) {
        require(side0.signum() >= 0 && side1.signum() >= 0 && previous.signum() >= 0 && terrain.signum() >= 0 && ratio.signum() >= 0 && positive(minimum), "combat width inputs must be nonnegative with positive minimum");
        BigInteger candidate = div(mul(fixedDiv(side0.add(side1), n(200_000)), ratio), SCALE);
        BigInteger base = previous.max(ONE.max(candidate));
        return new Width(base, minimum.max(div(mul(base.multiply(SCALE), terrain), SCALE)));
    }
    public record PursuitInitialPools(BigInteger levySoftRaw, BigInteger menAtArmsSoftRaw) {
        public static PursuitInitialPools fromEntries(List<Entry> entries) {
            BigInteger levy = ZERO, maa = ZERO;
            for (var e : entries) { if (e.kind() == RegimentKind.LEVY) levy = levy.add(e.softCasualtiesRaw()); else maa = maa.add(e.softCasualtiesRaw()); }
            return new PursuitInitialPools(levy, maa);
        }
    }
    public record PursuitDomainBudget(RegimentKind kind, BigInteger currentSoftRaw, BigInteger extraDailyRaw,
            BigInteger floorDailyRaw, BigInteger hardRaw, BigInteger allocationRemainderRaw) { }
    public record HardCredit(BigInteger regimentId, BigInteger hardRaw) { }
    public record PursuitDayResult(List<Entry> entries, List<HardCredit> hardByRegimentRaw, BigInteger totalHardRaw,
            BigInteger toughnessSoftRaw, BigInteger pursuitDamageRaw, BigInteger screenRaw, BigInteger baseRaw,
            BigInteger minimumRaw, BigInteger extraRaw, BigInteger floorComponentRaw, List<PursuitDomainBudget> domains) {
        public PursuitDayResult { entries = List.copyOf(entries); hardByRegimentRaw = List.copyOf(hardByRegimentRaw); domains = List.copyOf(domains); }
    }
    public record ThreeDayPursuitResult(List<Entry> entries, List<PursuitDayResult> days, BigInteger totalHardRaw) {
        public ThreeDayPursuitResult { entries = List.copyOf(entries); days = List.copyOf(days); }
    }
    private record DomainResult(List<Entry> entries, List<BigInteger> hardByIndex, BigInteger hard,
            BigInteger initialRemainder, BigInteger budgetA, BigInteger budgetB) { }
    private static BigInteger proportional(BigInteger budget, BigInteger soft, BigInteger current) { return soft.min(fixedDiv(mul(budget, soft), current)); }
    private static DomainResult applyPursuitDomain(List<Entry> entries, RegimentKind kind, BigInteger a, BigInteger b, BigInteger conversion) {
        BigInteger current = ZERO;
        for (var e : entries) if (e.kind() == kind) current = current.add(e.softCasualtiesRaw());
        var hard = new ArrayList<BigInteger>(); for (int i = 0; i < entries.size(); i++) hard.add(ZERO);
        if (current.signum() <= 0) return new DomainResult(entries, hard, ZERO, ZERO, a, b);
        BigInteger total = a.add(b);
        if (total.compareTo(current) > 0) { a = mul(a, fixedDiv(current, total)); b = current.subtract(a); total = a.add(b); }
        var mutable = new ArrayList<>(entries); BigInteger expected = ZERO;
        for (int i = 0; i < entries.size(); i++) {
            var e = entries.get(i); if (e.kind() != kind || e.softCasualtiesRaw().signum() <= 0) continue;
            BigInteger loss = mul(proportional(a, e.softCasualtiesRaw(), current), conversion).add(mul(proportional(b, e.softCasualtiesRaw(), current), conversion));
            expected = expected.add(proportional(total, e.softCasualtiesRaw(), current));
            var allocation = allocateHardCasualtiesToComponents(e.components(), loss);
            mutable.set(i, e.withPools(e.currentRaw(), e.softCasualtiesRaw().subtract(loss), allocation.components())); hard.set(i, loss);
        }
        BigInteger remainder = total.subtract(expected), initial = remainder;
        if (positive(remainder)) for (int i = 0; i < mutable.size(); i++) {
            if (remainder.signum() <= 0) break;
            var e = mutable.get(i); if (e.kind() != kind || e.softCasualtiesRaw().signum() <= 0) continue;
            BigInteger take = remainder.min(e.softCasualtiesRaw()), loss = mul(take, conversion);
            var allocation = allocateHardCasualtiesToComponents(e.components(), loss);
            mutable.set(i, e.withPools(e.currentRaw(), e.softCasualtiesRaw().subtract(loss), allocation.components()));
            hard.set(i, hard.get(i).add(loss)); remainder = remainder.subtract(take);
        }
        return new DomainResult(List.copyOf(mutable), List.copyOf(hard), sum(hard), initial, a, b);
    }
    private static BigInteger dailyBudget(BigInteger pool, BigInteger component, BigInteger toughness, BigInteger modifier, int days) {
        return fixedDiv(mul(mul(pool, fixedDiv(component, toughness)), modifier), n(days).multiply(SCALE));
    }
    public static PursuitDayResult applyPursuitDay(List<Entry> retreaters, List<Entry> pursuers, PursuitInitialPools pools,
            BigInteger pursuerModifier, BigInteger retreaterModifier) {
        return applyPursuitDay(retreaters, pursuers, pools, pursuerModifier, retreaterModifier, 3, SCALE, n(50_000), n(5_000), n(1_000));
    }
    public static PursuitDayResult applyPursuitDay(List<Entry> retreaters, List<Entry> pursuers, PursuitInitialPools pools,
            BigInteger pursuerModifier, BigInteger retreaterModifier, int days, BigInteger conversion,
            BigInteger pursuitMultiplier, BigInteger baseMultiplier, BigInteger minimumMultiplier) {
        BigInteger toughness = ZERO; for (var e : retreaters) toughness = toughness.add(mul(e.toughnessRaw(), e.softCasualtiesRaw()));
        if (positive(toughness)) toughness = toughness.max(SCALE);
        if (toughness.signum() <= 0) return new PursuitDayResult(retreaters, retreaters.stream().map(e -> new HardCredit(e.regimentId(), ZERO)).toList(), ZERO, toughness, ZERO, ZERO, ZERO, ZERO, ZERO, ZERO, List.of());
        BigInteger pursuitSum = ZERO, screen = ZERO;
        for (var e : pursuers) pursuitSum = pursuitSum.add(mul(e.pursuitRaw(), e.currentRaw()));
        for (var e : retreaters) screen = screen.add(mul(e.screenRaw(), e.softCasualtiesRaw()));
        BigInteger pursuit = mul(pursuitSum, pursuitMultiplier), modifier = ZERO.max(SCALE.add(pursuerModifier).add(retreaterModifier));
        BigInteger base = mul(baseMultiplier, toughness), minimum = mul(minimumMultiplier, toughness);
        BigInteger extra = ZERO.max(pursuit.subtract(screen)), floor = (positive(extra) ? base : base.subtract(screen).add(pursuit)).max(minimum);
        List<Entry> mutable = retreaters; var credits = new ArrayList<BigInteger>(); for (int i = 0; i < retreaters.size(); i++) credits.add(ZERO);
        var domains = new ArrayList<PursuitDomainBudget>();
        for (var kind : RegimentKind.values()) {
            BigInteger pool = kind == RegimentKind.LEVY ? pools.levySoftRaw() : pools.menAtArmsSoftRaw(), current = ZERO;
            for (var e : mutable) if (e.kind() == kind) current = current.add(e.softCasualtiesRaw());
            var result = applyPursuitDomain(mutable, kind, dailyBudget(pool, extra, toughness, modifier, days), dailyBudget(pool, floor, toughness, modifier, days), conversion);
            mutable = result.entries(); for (int i = 0; i < credits.size(); i++) credits.set(i, credits.get(i).add(result.hardByIndex().get(i)));
            domains.add(new PursuitDomainBudget(kind, current, result.budgetA(), result.budgetB(), result.hard(), result.initialRemainder()));
        }
        // Original credit is keyed by RegimentID, even when several armies carry it.
        var byRegiment = new LinkedHashMap<BigInteger, BigInteger>();
        for (int i = 0; i < mutable.size(); i++) byRegiment.merge(mutable.get(i).regimentId(), credits.get(i), BigInteger::add);
        var ordered = new ArrayList<HardCredit>(); for (var entry : mutable) ordered.add(new HardCredit(entry.regimentId(), byRegiment.get(entry.regimentId())));
        return new PursuitDayResult(mutable, ordered, sum(List.copyOf(byRegiment.values())), toughness, pursuit, screen, base, minimum, extra, floor, domains);
    }
    public static ThreeDayPursuitResult applyThreeDayPursuit(List<Entry> retreaters, List<Entry> pursuers,
            PursuitInitialPools initial, BigInteger pursuerModifier, BigInteger retreaterModifier) {
        var pools = initial == null ? PursuitInitialPools.fromEntries(retreaters) : initial;
        List<Entry> current = retreaters; var days = new ArrayList<PursuitDayResult>(); BigInteger total = ZERO;
        for (int i = 0; i < 3; i++) { var day = applyPursuitDay(current, pursuers, pools, pursuerModifier, retreaterModifier); days.add(day); current = day.entries(); total = total.add(day.totalHardRaw()); }
        return new ThreeDayPursuitResult(current, days, total);
    }
    public enum Phase { MANEUVER, MAIN, PURSUIT, DONE }
    public enum RetreatBlockReason { DISALLOWED, MINIMUM_DAYS, PHASE, LANDLESS }
    public record RetreatGateInput(boolean disallowRetreat, boolean allowEarlyRetreat, int elapsedWholeDays,
            Phase phase, boolean landlessBlocked, int minimumDaysBeforeManualRetreat) { }
    public record RetreatGateResult(boolean canRetreat, RetreatBlockReason blockedBy) { }
    public static Integer winnerAtMainTickStart(Integer forced, BigInteger side0, BigInteger side1) {
        require(forced == null || forced == 0 || forced == 1, "forced_side_field must be null, 0, or 1");
        if (forced != null) return forced; if (side0.signum() <= 0) return 1; if (side1.signum() <= 0) return 0; return null;
    }
    public static RetreatGateResult evaluateCanRetreat(RetreatGateInput gate) {
        if (gate.disallowRetreat()) return new RetreatGateResult(false, RetreatBlockReason.DISALLOWED);
        if (!gate.allowEarlyRetreat() && gate.elapsedWholeDays() <= gate.minimumDaysBeforeManualRetreat()) return new RetreatGateResult(false, RetreatBlockReason.MINIMUM_DAYS);
        if (gate.phase().ordinal() >= Phase.PURSUIT.ordinal()) return new RetreatGateResult(false, RetreatBlockReason.PHASE);
        if (gate.landlessBlocked()) return new RetreatGateResult(false, RetreatBlockReason.LANDLESS);
        return new RetreatGateResult(true, null);
    }
    public enum BattleEndBranch { NON_RETREATING_CLEAR, ENTER_PURSUIT, SKIP_PURSUIT }
    public record BattleEndCoreResult(int winnerSide, int loserSide, Phase phase, List<Entry> loserEntries,
            PursuitInitialPools pursuitInitialPools, BattleEndBranch branch, RetreatGateResult retreatGate) {
        public BattleEndCoreResult { loserEntries = List.copyOf(loserEntries); }
    }
    public static BattleEndCoreResult transitionAfterWinnerIsKnown(List<Entry> entries, int winner, RetreatGateInput gateInput, boolean skip) {
        require(winner == 0 || winner == 1, "winner_side must be 0 or 1"); var gate = evaluateCanRetreat(gateInput);
        if (!gate.canRetreat()) {
            var clear = entries.stream().map(e -> e.withPools(ZERO, ZERO, e.components().stream().map(c -> new BackingComponent(c.maximumSoldiers(), ZERO, c.kind())).toList())).toList();
            return new BattleEndCoreResult(winner, 1 - winner, Phase.DONE, clear, null, BattleEndBranch.NON_RETREATING_CLEAR, gate);
        }
        return new BattleEndCoreResult(winner, 1 - winner, skip ? Phase.DONE : Phase.PURSUIT, entries, PursuitInitialPools.fromEntries(entries), skip ? BattleEndBranch.SKIP_PURSUIT : BattleEndBranch.ENTER_PURSUIT, gate);
    }
    public static int forcedWinnerSide(int scopedSide, boolean scopedYes) { require(scopedSide == 0 || scopedSide == 1, "scoped_side must be 0 or 1"); return scopedYes ? scopedSide : 1 - scopedSide; }
    public record ForcedWinnerEffectResult(int forcedSideField, Integer winnerSide, boolean synchronouslyAdvanced) { }
    public static ForcedWinnerEffectResult applyForcedWinnerEffect(Phase phase, Integer currentWinner, int scopedSide, boolean scopedYes) {
        int mapped = forcedWinnerSide(scopedSide, scopedYes); require(currentWinner == null || currentWinner == 0 || currentWinner == 1, "invalid current winner");
        Integer winner = phase == Phase.MANEUVER || phase == Phase.MAIN ? Integer.valueOf(mapped) : currentWinner;
        return new ForcedWinnerEffectResult(mapped, winner, phase != Phase.DONE);
    }
    private static final long MASK32 = 0xffff_ffffL, DRAW_STEP = 0x4ad685b3L, DRAW_BASE = 0x5ea6ba9fL;
    private static long u32(long value) { return value & MASK32; }
    public static long avalanche32(long value) { value = u32(value); value ^= value >>> 8; value = u32(value + 1_759_714_724L); value ^= u32(value << 8); value = u32(value * 458_671_337L); value ^= value >>> 8; value = u32(value * 2_463_534_242L); value ^= value >>> 8; return u32(value); }
    public record DrawState(long counter, long salt) {
        public DrawState { require(counter >= 0 && counter <= MASK32 && salt >= 0 && salt <= MASK32, "draw state must be uint32"); }
        public Draw draw31() { long value = u32(salt - u32(counter * DRAW_STEP)); return new Draw(avalanche32(value) & 0x7fff_ffffL, new DrawState(u32(counter + 1), salt)); }
    }
    public record Draw(long value, DrawState state) { }
    public record EffectChildState(long parentDraw, DrawState nextParent, DrawState child) { }
    public static EffectChildState effectChildState(DrawState parent, long nodeHash) {
        require(nodeHash >= 0 && nodeHash <= MASK32, "node hash must be uint32"); var draw = parent.draw31();
        long mixed = u32(draw.value() + nodeHash * 1_000_033L);
        return new EffectChildState(draw.value(), draw.state(), new DrawState(avalanche32(u32(DRAW_BASE - u32(mixed * DRAW_STEP))), 0));
    }
    public record BattleResultEnvelopeSchedule(boolean normalResultGenerated, boolean terminalNoResolution,
            Long winnerEnvelopeDraw, Long loserEnvelopeDraw, DrawState state) { }
    public static BattleResultEnvelopeSchedule scheduleBattleResultEnvelopes(DrawState state, boolean teardown) {
        if (teardown) return new BattleResultEnvelopeSchedule(false, true, null, null, state);
        var winner = state.draw31(); var loser = winner.state().draw31(); return new BattleResultEnvelopeSchedule(true, false, winner.value(), loser.value(), loser.state());
    }
    public static DrawState phaseScheduleState(long seed) { return new DrawState(avalanche32(u32(DRAW_BASE - u32(seed) * DRAW_STEP)), 0); }
    public static int weightedChoiceIndex(List<BigInteger> weights, BigInteger random31, int fallback) {
        BigInteger total = ZERO; for (var w : weights) if (positive(w)) total = total.add(w); if (total.signum() == 0) return fallback;
        double targetFloat = Math.scalb(random31.abs().doubleValue(), -31) * total.doubleValue();
        BigInteger target = new BigDecimal(targetFloat).toBigInteger(), cumulative = ZERO;
        for (int i = 0; i < weights.size(); i++) { if (!positive(weights.get(i))) continue; cumulative = cumulative.add(weights.get(i)); if (target.compareTo(cumulative) < 0) return i; }
        return fallback;
    }
    public static boolean phaseEventDue(BigInteger characterId, BigInteger day, int cadence) { return u32(characterId.longValue() + u32(day.longValue())) % cadence == 0; }
    public record PhaseEventCandidate(String key, boolean valid, BigInteger intWeight, boolean emptyEffect) { }
    public record PhaseEventSelection(String selectedCandidateKey, String executableEventKey, Long random31, DrawState state, int triggerValidCount) { }
    public static PhaseEventSelection selectPhaseEvent(List<PhaseEventCandidate> candidates, DrawState state) {
        var valid = candidates.stream().filter(PhaseEventCandidate::valid).toList(); if (valid.isEmpty()) return new PhaseEventSelection(null, null, null, state, 0);
        var draw = state.draw31(); int selected = weightedChoiceIndex(valid.stream().map(PhaseEventCandidate::intWeight).toList(), n(draw.value()), -1);
        if (selected < 0) return new PhaseEventSelection(null, null, draw.value(), draw.state(), valid.size()); var candidate = valid.get(selected);
        return new PhaseEventSelection(candidate.key(), candidate.emptyEffect() ? null : candidate.key(), draw.value(), draw.state(), valid.size());
    }
    public record FirePhaseEventSeeds(long base, List<Long> knightEffectSeeds, Long commanderEffectSeed) { public FirePhaseEventSeeds { knightEffectSeeds = List.copyOf(knightEffectSeeds); } }
    public static FirePhaseEventSeeds firePhaseEventSeeds(long globalDraw, int count, boolean commanderExecutes) {
        long base = avalanche32(u32(DRAW_BASE - u32(globalDraw) * DRAW_STEP)); var seeds = new ArrayList<Long>();
        for (int i = 0; i < count; i++) seeds.add(avalanche32(-u32(base + i) * DRAW_STEP) & 0x7fff_ffffL);
        Long commander = commanderExecutes ? avalanche32(u32(u32(base + count) * 0xb5297a4dL)) & 0x7fff_ffffL : null;
        return new FirePhaseEventSeeds(base, seeds, commander);
    }
    public record CommanderRollRequest(boolean drawEnabled, BigInteger effectiveMin, BigInteger effectiveMax, BigInteger previousRoll) { }
    private record SampledRoll(BigInteger value, Long draw, DrawState state) { }
    private static SampledRoll sampleRoll(CommanderRollRequest request, DrawState state) {
        if (!request.drawEnabled()) return new SampledRoll(request.previousRoll(), null, state); var draw = state.draw31();
        BigInteger lower = request.effectiveMin().min(request.effectiveMax()), span = request.effectiveMax().subtract(request.effectiveMin()).abs().add(ONE);
        return new SampledRoll(lower.add(n(draw.value()).mod(span)), draw.value(), draw.state());
    }
    public record MainDayRandomResult(long side0FireDraw, long side1FireDraw, Long side0RollDraw, Long side1RollDraw,
            BigInteger side0Roll, BigInteger side1Roll, int nextRollCadence, DrawState state) { }
    public static MainDayRandomResult scheduleMainDayRandomness(DrawState state, int cadence, CommanderRollRequest side0, CommanderRollRequest side1) {
        var fire0 = state.draw31(); var fire1 = fire0.state().draw31(); state = fire1.state();
        var roll0 = new SampledRoll(side0.previousRoll(), null, state); var roll1 = new SampledRoll(side1.previousRoll(), null, state);
        if (cadence == 0) { roll0 = sampleRoll(side0, state); roll1 = sampleRoll(side1, roll0.state()); state = roll1.state(); }
        return new MainDayRandomResult(fire0.value(), fire1.value(), roll0.draw(), roll1.draw(), roll0.value(), roll1.value(), Math.floorMod(cadence + 1, 3), state);
    }
    public record Manifest(String simulatorBuild, boolean loadedPhaseEffectsExact, boolean battleEndExact,
            boolean retreatAndForcedResultExact, String originalTraceFixtureSha256, List<String> closedNumericDomains) {
        public Manifest { Objects.requireNonNull(simulatorBuild); closedNumericDomains = List.copyOf(closedNumericDomains);
            require(originalTraceFixtureSha256 == null || originalTraceFixtureSha256.matches("[0-9a-fA-F]{64}"), "invalid original trace SHA256"); }
        public boolean fidelityGate() { return loadedPhaseEffectsExact && battleEndExact && retreatAndForcedResultExact && originalTraceFixtureSha256 != null; }
        public List<String> missingRequiredDomains() { var result = new ArrayList<String>();
            if (!loadedPhaseEffectsExact) result.add("loaded_phase_event_effect_transition"); if (!battleEndExact) result.add("battle_end_transition");
            if (!retreatAndForcedResultExact) result.add("manual_ai_retreat_and_forced_result"); if (originalTraceFixtureSha256 == null) result.add("exact_build_original_trace_fixture"); return List.copyOf(result); }
    }
    public static final Manifest BOUNDED_CORE_MANIFEST = new Manifest("ck3-1.19.0.6-bounded-core-v1", false, true, true, null,
            List.of("signed_q100000_fixed_point", "main_damage_to_soft_hard_casualties", "backing_component_allocation", "three_day_pursuit", "commander_roll_and_phase_rng_scheduler", "battle_end_core_and_result_envelope_order", "retreat_skip_pursuit_and_forced_winner"));
    public enum TrialResult { PLAYER_WIN, PLAYER_LOSS, NO_RESOLUTION }
    public record TrialOutcome(TrialResult result, int battleDays, BigInteger playerHardLossRaw, BigInteger enemyHardLossRaw,
            boolean playerStackWipe, boolean commanderOrKnightDeath) {
        public TrialOutcome { Objects.requireNonNull(result); require(battleDays >= 0 && playerHardLossRaw.signum() >= 0 && enemyHardLossRaw.signum() >= 0, "negative trial days or hard losses"); }
    }
    public record TrialRandomStreams(DrawState globalState, DrawState phaseScheduleState) { }
    private static long splitmix64(long value) { value += 0x9e3779b97f4a7c15L; value = (value ^ (value >>> 30)) * 0xbf58476d1ce4e5b9L; value = (value ^ (value >>> 27)) * 0x94d049bb133111ebL; return value ^ (value >>> 31); }
    public static TrialRandomStreams deriveTrialRandomStreams(BigInteger seed, long trialIndex) {
        long first = splitmix64(seed.longValue() + trialIndex * 2), second = splitmix64(seed.longValue() + trialIndex * 2 + 1);
        return new TrialRandomStreams(new DrawState(u32(first), first >>> 32), new DrawState(u32(second), second >>> 32));
    }
    public record Experiment(String inputSha256, BigInteger seedU64, int sampleCount, int horizonDays) {
        public Experiment { require(inputSha256 != null && inputSha256.matches("[0-9a-fA-F]{64}"), "input SHA256 required");
            require(seedU64.signum() >= 0 && seedU64.bitLength() <= 64 && sampleCount > 0 && horizonDays > 0, "invalid experiment seed or budget"); }
    }
    public interface TransitionKernel<T> { Manifest manifest(); TrialOutcome simulateTrial(T initialState, TrialRandomStreams streams, int horizonDays); }
    public record WilsonInterval(double lower, double upper) { }
    public static WilsonInterval wilsonInterval95(int successes, int trials) {
        if (trials <= 0) return null; require(successes >= 0 && successes <= trials, "successes outside trials");
        double z = 1.959963984540054, probability = (double) successes / trials, z2 = z * z, denominator = 1.0 + z2 / trials;
        double center = (probability + z2 / (2.0 * trials)) / denominator;
        double half = z * Math.sqrt(probability * (1.0 - probability) / trials + z2 / (4.0 * trials * trials)) / denominator;
        return new WilsonInterval(Math.max(0.0, center - half), Math.min(1.0, center + half));
    }
    public record DistributionSummary(Double mean, BigInteger p10, BigInteger p50, BigInteger p90) { }
    private static BigInteger nearestRank(List<BigInteger> sorted, double quantile) { return sorted.isEmpty() ? null : sorted.get(Math.max(1, (int) Math.ceil(quantile * sorted.size())) - 1); }
    public static DistributionSummary summarizeDistribution(List<BigInteger> values) {
        var sorted = values.stream().sorted().toList(); return new DistributionSummary(values.isEmpty() ? null : ratio(sum(values), n(values.size())), nearestRank(sorted, .1), nearestRank(sorted, .5), nearestRank(sorted, .9));
    }
    public static double ratio(BigInteger numerator, BigInteger denominator) { return CombatNumbers.binary64Ratio(numerator, denominator); }
    public record Summary(String inputSha256, String simulatorBuild, String sampler, BigInteger seedU64, int sampleCount,
            int playerWins, int playerLosses, int noResolution, Double playerWinProbabilityResolved, WilsonInterval playerWinWilson95,
            DistributionSummary battleDays, DistributionSummary playerHardLossesRaw, DistributionSummary enemyHardLossesRaw,
            double playerStackWipeProbability, double commanderOrKnightDeathProbability, boolean fidelityGate, boolean plannerUsable,
            String modelFidelity, List<String> missingRequiredDomains) {
        public Summary { missingRequiredDomains = List.copyOf(missingRequiredDomains); }
    }
    public static Summary summarizeTrialOutcomes(List<TrialOutcome> outcomes, Experiment experiment, Manifest manifest) {
        require(outcomes.size() == experiment.sampleCount(), "outcome count must equal experiment.sample_count");
        int wins = 0, losses = 0, unresolved = 0, wipes = 0, deaths = 0;
        var days = new ArrayList<BigInteger>(); var playerLoss = new ArrayList<BigInteger>(); var enemyLoss = new ArrayList<BigInteger>();
        for (var o : outcomes) { switch (o.result()) { case PLAYER_WIN -> wins++; case PLAYER_LOSS -> losses++; case NO_RESOLUTION -> unresolved++; }
            if (o.playerStackWipe()) wipes++; if (o.commanderOrKnightDeath()) deaths++; days.add(n(o.battleDays())); playerLoss.add(o.playerHardLossRaw()); enemyLoss.add(o.enemyHardLossRaw()); }
        int resolved = wins + losses; return new Summary(experiment.inputSha256().toLowerCase(java.util.Locale.ROOT), manifest.simulatorBuild(), "splitmix64-derived-independent-draw31-v1", experiment.seedU64(), experiment.sampleCount(), wins, losses, unresolved,
                resolved == 0 ? null : (double) wins / resolved, wilsonInterval95(wins, resolved), summarizeDistribution(days), summarizeDistribution(playerLoss), summarizeDistribution(enemyLoss),
                (double) wipes / experiment.sampleCount(), (double) deaths / experiment.sampleCount(), manifest.fidelityGate(), false,
                manifest.fidelityGate() ? "transition-parity-manifest-claim" : "research-only-bounded-core", manifest.missingRequiredDomains());
    }
    public static <T> Summary runCombatExperiment(T state, Experiment experiment, TransitionKernel<T> kernel) {
        var outcomes = new ArrayList<TrialOutcome>(); for (int i = 0; i < experiment.sampleCount(); i++) outcomes.add(kernel.simulateTrial(state, deriveTrialRandomStreams(experiment.seedU64(), i), experiment.horizonDays()));
        return summarizeTrialOutcomes(outcomes, experiment, kernel.manifest());
    }
}
