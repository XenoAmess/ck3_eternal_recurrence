package org.xar.ck3.control.g2.m6.nativeai;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/**
 * Pure reference semantics of the pinned 1.20.0.4 activity candidate path.
 * The native builder at RVA 1A74080 consumes a pending Type* set, and the caller at
 * 1A8D530 can submit a command. Neither is a read-only query entry point.
 * This class executes neither native calls nor actions. Its output is a
 * reconstruction from supplied inputs, never proof of live eligibility,
 * complete candidate coverage, command submission, terminal state or benefit.
 * Native source, complete registry and current gate/value observations must
 * be qualified by their actual guarded producer before a live planner uses
 * them. No such producer is introduced by this reference implementation.
 */
public final class NativeActivityAi {
    public static final String EXE_SHA256 =
            "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final String SOURCE_GRAPH = "m6-native-12004-source05";
    private static final BigInteger U64_LIMIT = BigInteger.ONE.shiftLeft(64);
    private static final int[] MONTH_ENDS =
            {31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};

    private NativeActivityAi() {}

    public enum Property {
        IS_SHOWN("is_shown", 0x57B, 0x40),
        CAN_PLAN("can_plan", 0x3D8B, 0x110),
        CAN_START("can_start", 0x363D, 0x1E0),
        CAN_START_SHOWING_FAILURES_ONLY("can_start_showing_failures_only", 0x363E, 0x2B0),
        ON_COMPLETE("on_complete", 0x281F, 0x8E0),
        AI_WILL_DO("ai_will_do", 0x28B2, 0x10B0),
        AI_CHECK_INTERVAL("ai_check_interval", 0x3377, 0x3D60),
        AI_CHECK_INTERVAL_BY_TIER("ai_check_interval_by_tier", 0x3C2A, 0x3D60);

        private final String authoredKey;
        private final int runtimeToken;
        private final int objectOffset;

        Property(String authoredKey, int runtimeToken, int objectOffset) {
            this.authoredKey = authoredKey;
            this.runtimeToken = runtimeToken;
            this.objectOffset = objectOffset;
        }
        public String authoredKey() { return authoredKey; }
        public int runtimeToken() { return runtimeToken; }
        public int objectOffset() { return objectOffset; }
    }

    /** Opaque pointer identity from one native scope; never a portable ID. */
    public record TypePointer(BigInteger value) {
        public TypePointer {
            Objects.requireNonNull(value, "value");
            if (value.signum() <= 0 || value.compareTo(U64_LIMIT) >= 0) {
                throw new IllegalArgumentException("native pointer outside uint64 nonzero domain");
            }
        }

        public String decimal() { return value.toString(); }
    }

    /** Interval values are signed int32, in the exact seven native slots. */
    public record Definition(TypePointer pointer, long nativeId, List<Integer> intervals) {
        public Definition {
            Objects.requireNonNull(pointer, "pointer");
            unsigned32(nativeId);
            intervals = List.copyOf(intervals);
            if (intervals.size() != 7) throw new IllegalArgumentException("seven rank slots required");
        }

        public int interval(int rank) { checkRank(rank); return intervals.get(rank); }
    }

    public record RankIndex(List<List<Definition>> ranks) {
        public RankIndex {
            Objects.requireNonNull(ranks, "ranks");
            ranks = ranks.stream().map(List::copyOf).toList();
            if (ranks.size() != 7 || !ranks.get(0).isEmpty()) {
                throw new IllegalArgumentException("seven native rank vectors; rank zero stays empty");
            }
            for (int rank = 1; rank < 7; rank++) {
                for (Definition definition : ranks.get(rank)) {
                    if (definition.interval(rank) <= 0) {
                        throw new IllegalArgumentException("rank index contains disabled interval");
                    }
                }
            }
        }

        public List<Definition> at(int rank) { checkRank(rank); return ranks.get(rank); }
    }

    /** Logical Type* set at character activity header+28; its bucket has no date/value. */
    public record Invalidations(Set<TypePointer> pending) {
        public Invalidations { pending = Set.copyOf(pending); }
    }

    /** Only the raw-date projection of the independent header+0 cooldown map. */
    public record RawCooldowns(Map<TypePointer, Integer> rawDates) {
        public RawCooldowns { rawDates = Map.copyOf(rawDates); }
    }

    public record ActivityMemory(RawCooldowns cooldowns, Invalidations invalidations) {
        public ActivityMemory {
            Objects.requireNonNull(cooldowns, "cooldowns");
            Objects.requireNonNull(invalidations, "invalidations");
        }
    }

    public enum Mode { HOST, INSPECTION }
    public enum RecomputeReason { CONSUMED_INVALIDATION, INTERVAL_PHASE, INSPECTION_FORCED }

    public record RequiredEvaluation(int ordinal, Definition definition,
            RecomputeReason reason) {
        public RequiredEvaluation {
            if (ordinal < 0) throw new IllegalArgumentException("negative registry ordinal");
            Objects.requireNonNull(definition, "definition");
            Objects.requireNonNull(reason, "reason");
        }
    }

    public record RecomputePlan(int rank, Mode mode, List<Definition> sourceIndex,
            List<RequiredEvaluation> required, Invalidations invalidationsAfterConsumption) {
        public RecomputePlan {
            checkRank(rank);
            Objects.requireNonNull(mode, "mode");
            sourceIndex = List.copyOf(sourceIndex);
            required = List.copyOf(required);
            Objects.requireNonNull(invalidationsAfterConsumption, "invalidationsAfterConsumption");
            int previous = -1;
            for (RequiredEvaluation row : required) {
                if (row.ordinal() <= previous || row.ordinal() >= sourceIndex.size()
                        || !sourceIndex.get(row.ordinal()).equals(row.definition())) {
                    throw new IllegalArgumentException("evaluation must bind the original ordered row");
                }
                previous = row.ordinal();
            }
        }
    }

    public sealed interface Evaluation permits GateRejected, Scored {
        RequiredEvaluation requirement();
    }

    public record GateRejected(RequiredEvaluation requirement) implements Evaluation {
        public GateRejected { Objects.requireNonNull(requirement, "requirement"); }
    }

    /** The signed integer returned from actual Type+10B0 evaluation. */
    public record Scored(RequiredEvaluation requirement, int nativeScore) implements Evaluation {
        public Scored { Objects.requireNonNull(requirement, "requirement"); }
    }

    public record Candidate(RequiredEvaluation requirement, int score) {
        public Candidate { Objects.requireNonNull(requirement, "requirement"); }
    }

    public record Selection(List<Candidate> shuffled, Optional<Candidate> maximum,
            Optional<Integer> roll, int randomCounterAfter, boolean passesScoreRoll) {
        public Selection {
            shuffled = List.copyOf(shuffled);
            Objects.requireNonNull(maximum, "maximum");
            Objects.requireNonNull(roll, "roll");
            if (maximum.isPresent() != roll.isPresent()
                    || maximum.isPresent() != !shuffled.isEmpty()) {
                throw new IllegalArgumentException("winner and roll presence mismatch");
            }
            if (roll.isPresent() && (roll.get() < 1 || roll.get() > 100)) {
                throw new IllegalArgumentException("roll outside native 1..100 domain");
            }
            if (passesScoreRoll != (maximum.isPresent() && roll.get() < maximum.get().score())) {
                throw new IllegalArgumentException("strict native score/roll comparison mismatch");
            }
        }
    }

    /** RVA 3114E70, all three unwind fragments through 3115051. */
    public static RankIndex rebuildIndex(List<Definition> registry) {
        List<Definition> immutable = List.copyOf(registry);
        List<List<Definition>> ranks = new ArrayList<>(7);
        ranks.add(List.of());
        for (int rank = 1; rank < 7; rank++) {
            List<Definition> rows = new ArrayList<>();
            for (Definition definition : immutable) {
                if (definition.interval(rank) > 0) rows.add(definition);
            }
            // Native registry order and duplicate pointers are preserved.
            ranks.add(List.copyOf(rows));
        }
        return new RankIndex(ranks);
    }

    /** Exact native signed int32 date arithmetic and pinned 365-byte month table. */
    public static int monthOrdinal(int dateRaw) {
        int days = (dateRaw - 0x29C55C0) / 24;
        int year = days / 365;
        int day = days - year * 365;
        if (day < 0) day += 365;
        int month = 0;
        while (day >= MONTH_ENDS[month]) month++;
        return year * 12 + month;
    }

    /**
     * Plans required fresh gate/score evaluations. A pending Type* invalidation
     * is consumed from the separate set and bypasses interval phase.
     * Unlike the native helper, this only changes a returned immutable copy.
     */
    public static RecomputePlan plan(RankIndex index, int rank, Invalidations before,
            long actorFullId, int dateRaw, Mode mode) {
        Objects.requireNonNull(index, "index");
        Objects.requireNonNull(before, "before");
        Objects.requireNonNull(mode, "mode");
        unsigned32(actorFullId);
        if (actorFullId == 0xFFFF_FFFFL) throw new IllegalArgumentException("actor sentinel");
        List<Definition> rows = index.at(rank);
        Set<TypePointer> invalidations = new HashSet<>(before.pending());
        List<RequiredEvaluation> required = new ArrayList<>();
        int actorMonth = (int) actorFullId * 0x1115 + monthOrdinal(dateRaw) * 0x16D3;
        for (int ordinal = 0; ordinal < rows.size(); ordinal++) {
            Definition definition = rows.get(ordinal);
            boolean removed = invalidations.remove(definition.pointer());
            if (removed) {
                required.add(new RequiredEvaluation(ordinal, definition,
                        RecomputeReason.CONSUMED_INVALIDATION));
            } else {
                int phase = (int) definition.nativeId() * 0x1C73 + actorMonth;
                if (phase % definition.interval(rank) == 0) {
                    required.add(new RequiredEvaluation(ordinal, definition,
                            RecomputeReason.INTERVAL_PHASE));
                } else if (mode == Mode.INSPECTION) {
                    required.add(new RequiredEvaluation(ordinal, definition,
                            RecomputeReason.INSPECTION_FORCED));
                }
            }
        }
        return new RecomputePlan(rank, mode, rows, required, new Invalidations(invalidations));
    }

    /**
     * RVA 2BBD830 uses the separate header+0 map, not the pending set. Only the
     * first raw-date DWORD of each native eight-byte Date is projected here.
     */
    public static boolean cooldownBlocked(RawCooldowns cooldowns, TypePointer type, int dateRaw) {
        Objects.requireNonNull(cooldowns, "cooldowns");
        Objects.requireNonNull(type, "type");
        Integer deadline = cooldowns.rawDates().get(type);
        return deadline != null && dateRaw < deadline;
    }

    /**
     * Raw-date projection of 23F620E..23F635D: Activity+3EC plus 24 times the
     * signed returned duration. The other four packed Date bytes are not
     * fabricated. This pure projection writes neither native memory nor Game.
     */
    public static RawCooldowns projectCooldownWrite(RawCooldowns before, TypePointer type,
            int activityRawDate, int returnedDurationDays) {
        Objects.requireNonNull(before, "before");
        Objects.requireNonNull(type, "type");
        Map<TypePointer, Integer> result = new HashMap<>(before.rawDates());
        result.put(type, activityRawDate + returnedDurationDays * 24);
        return new RawCooldowns(result);
    }

    /**
     * Pure projection of ai_attempt_to_host_activity's TWO mutations:
     * 2CABDEA removes the type's cooldown; 2CABE94 inserts it into the pending
     * set. Native execution first requires a real AI state at actor+1B0+278.
     * This reference function cannot qualify that state or authorize the effect.
     * Normal candidate plan() never calls this or removes a cooldown.
     */
    public static ActivityMemory projectForcedReevaluation(ActivityMemory before, TypePointer type) {
        Objects.requireNonNull(before, "before");
        Objects.requireNonNull(type, "type");
        Map<TypePointer, Integer> cooldowns = new HashMap<>(before.cooldowns().rawDates());
        cooldowns.remove(type);
        Set<TypePointer> pending = new HashSet<>(before.invalidations().pending());
        pending.add(type);
        return new ActivityMemory(new RawCooldowns(cooldowns), new Invalidations(pending));
    }

    /** RVA 1A74321 and 1A743F6. Rejects missing, extra, reordered or alien evaluations. */
    public static List<Candidate> filter(RecomputePlan plan, List<Evaluation> evaluations,
            int activityScoreThreshold) {
        Objects.requireNonNull(plan, "plan");
        List<Evaluation> rows = List.copyOf(evaluations);
        if (rows.size() != plan.required().size()) {
            throw new IllegalArgumentException("complete planned evaluation set required");
        }
        List<Candidate> candidates = new ArrayList<>();
        for (int i = 0; i < rows.size(); i++) {
            Evaluation evaluation = rows.get(i);
            if (!evaluation.requirement().equals(plan.required().get(i))) {
                throw new IllegalArgumentException("evaluation source row mismatch");
            }
            int score;
            if (evaluation instanceof GateRejected) {
                if (plan.mode() == Mode.HOST) continue;
                score = -1000;
            } else if (evaluation instanceof Scored scored) {
                score = scored.nativeScore();
            } else {
                throw new IllegalArgumentException("unknown sealed evaluation");
            }
            if (score >= activityScoreThreshold || plan.mode() == Mode.INSPECTION) {
                candidates.add(new Candidate(evaluation.requirement(), score));
            }
        }
        return List.copyOf(candidates);
    }

    /**
     * RVA 1A8D5AB..1A8D768: native bit-exact hash, shuffle, strict signed maximum,
     * then roll < score. The remaining native planning/validation is separate.
     */
    public static Selection select(List<Candidate> candidates, int callerSeed) {
        List<Candidate> rows = new ArrayList<>(List.copyOf(candidates));
        int counter = mix(0x5EA6BA9F - callerSeed * 0x4AD685B3);
        for (int last = rows.size() - 1; last > 0; last--) {
            int sample = mix(-counter * 0x4AD685B3) & 0x7FFF_FFFF;
            counter++;
            Collections.swap(rows, last, sample % (last + 1));
        }
        if (rows.isEmpty()) {
            return new Selection(rows, Optional.empty(), Optional.empty(), counter, false);
        }
        Candidate maximum = rows.get(0);
        for (int i = 1; i < rows.size(); i++) {
            if (maximum.score() < rows.get(i).score()) maximum = rows.get(i);
        }
        int roll = (mix(counter * 0xB5297A4D) & 0x7FFF_FFFF) % 100 + 1;
        counter++;
        return new Selection(rows, Optional.of(maximum), Optional.of(roll), counter,
                roll < maximum.score());
    }

    /** Native FNV1a over all eight little-endian pointer bytes. */
    public static int typeKeyHash(TypePointer pointer) {
        Objects.requireNonNull(pointer, "pointer");
        int hash = 0x811C9DC5;
        BigInteger value = pointer.value();
        for (int i = 0; i < 8; i++) {
            hash = (hash ^ (value.shiftRight(i * 8).intValue() & 0xFF)) * 0x01000193;
        }
        return hash;
    }

    static int mix(int value) {
        int x = (value ^ value >>> 8) + 0x68E31DA4;
        x = (x ^ x << 8) * 0x1B56C4E9;
        x = (x ^ x >>> 8) * 0x92D68CA2;
        return x ^ x >>> 8;
    }

    private static void checkRank(int rank) {
        if (rank < 0 || rank >= 7) throw new IllegalArgumentException("rank outside 0..6");
    }

    private static void unsigned32(long value) {
        if (value < 0 || value > 0xFFFF_FFFFL) throw new IllegalArgumentException("uint32 required");
    }
}
