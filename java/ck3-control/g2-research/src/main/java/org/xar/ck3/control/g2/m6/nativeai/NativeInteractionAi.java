package org.xar.ck3.control.g2.m6.nativeai;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;

/**
 * Pinned .4 reference semantics for the preparation-complete portion of
 * 1A2B310. Actual target-family enumeration, native filters, context setting,
 * gate/value production and final CanSend/submission remain with their native
 * producers. This reconstruction does not establish any of those facts.
 * Unlike activity hosting, sender utility uses fixed raw /100000 minus 0..99.
 * The caller must supply the exact native ordered target rows after filtering
 * and RNG state AFTER the context-seed draw at 1A2B3A4..1A2B3F3.
 */
public final class NativeInteractionAi {
    private NativeInteractionAi() {}

    public record RandomState(int counter, int salt) {}
    public record Draw(int nonnegative31, RandomState after) {
        public Draw {
            if (nonnegative31 < 0) throw new IllegalArgumentException("31-bit draw required");
            Objects.requireNonNull(after, "after");
        }
    }

    public sealed interface Preparation permits Rejected, Scored {}
    public record Rejected() implements Preparation {}
    public record Scored(long senderWillDoRaw) implements Preparation {}

    public record Target(long fullId, Preparation preparation) {
        public Target {
            if (fullId < 0 || fullId >= 0xFFFF_FFFFL) {
                throw new IllegalArgumentException("full uint32 character ID excluding sentinel required");
            }
            Objects.requireNonNull(preparation, "preparation");
        }
    }

    /**
     * Corresponds to one native 0x78-byte target block after common filters.
     * Chance raw is the signed int64 at block+18; native accepts draw <= raw.
     * A positive max causes native replacement/trimming, not prefix truncation.
     */
    public record PreparedBlock(long chanceRaw, int maxTargets, List<Target> filteredTargets) {
        public PreparedBlock { filteredTargets = List.copyOf(filteredTargets); }
    }

    public enum Disposition { CHANCE_REJECTED, PREPARATION_REJECTED, NOT_BETTER, NEW_MAXIMUM }
    public record Comparison(int blockOrdinal, long targetFullId, int chanceDraw,
            Optional<Integer> marginDraw, Optional<Integer> margin, Disposition disposition) {
        public Comparison {
            if (blockOrdinal < 0 || targetFullId < 0 || targetFullId >= 0xFFFF_FFFFL
                    || chanceDraw < 0 || chanceDraw >= 100000) {
                throw new IllegalArgumentException("invalid native comparison tuple");
            }
            Objects.requireNonNull(marginDraw, "marginDraw");
            Objects.requireNonNull(margin, "margin");
            Objects.requireNonNull(disposition, "disposition");
            boolean scored = disposition == Disposition.NOT_BETTER
                    || disposition == Disposition.NEW_MAXIMUM;
            if (scored != marginDraw.isPresent() || scored != margin.isPresent()
                    || marginDraw.isPresent() && (marginDraw.get() < 0 || marginDraw.get() >= 100)) {
                throw new IllegalArgumentException("score draw branch mismatch");
            }
        }
    }

    public record Result(OptionalLong selectedTarget, int bestMargin,
            List<Comparison> comparisons, RandomState randomAfter) {
        public Result {
            Objects.requireNonNull(selectedTarget, "selectedTarget");
            comparisons = List.copyOf(comparisons);
            Objects.requireNonNull(randomAfter, "randomAfter");
            if (selectedTarget.isPresent() != (bestMargin > 0)) {
                throw new IllegalArgumentException("native best margin starts at zero");
            }
        }
    }

    /** RVA 1A2BC11..1A2BC2F; native unsigned32 actor+month becomes int64 before IDIV. */
    public static boolean phaseDue(long actorFullId, int dateRaw, int rankFrequency) {
        if (actorFullId < 0 || actorFullId >= 0xFFFF_FFFFL) {
            throw new IllegalArgumentException("full uint32 character ID excluding sentinel required");
        }
        if (rankFrequency <= 0) return false;
        long phase = Integer.toUnsignedLong((int) actorFullId + NativeActivityAi.monthOrdinal(dateRaw));
        return phase % rankFrequency == 0;
    }

    /** RVA 1A2B3A4 and repeated native counter/salt hash blocks. */
    public static Draw draw(RandomState state) {
        Objects.requireNonNull(state, "state");
        int value = NativeActivityAi.mix(state.salt() - state.counter() * 0x4AD685B3);
        return new Draw(value & 0x7FFF_FFFF, new RandomState(state.counter() + 1, state.salt()));
    }

    /**
     * RVA 1A2B524..1A2B70F. Preserves native swap-with-last trim semantics,
     * including the unusual modulus maxTargets while the list is still larger.
     * Equal margins retain the earlier selected row; zero never selects.
     */
    public static Result selectPreparedBlocks(List<PreparedBlock> blocks,
            RandomState afterContextSeed) {
        List<PreparedBlock> source = List.copyOf(blocks);
        RandomState random = Objects.requireNonNull(afterContextSeed, "afterContextSeed");
        List<Comparison> comparisons = new ArrayList<>();
        OptionalLong selected = OptionalLong.empty();
        int best = 0;
        for (int blockOrdinal = 0; blockOrdinal < source.size(); blockOrdinal++) {
            PreparedBlock block = source.get(blockOrdinal);
            List<Target> targets = new ArrayList<>(block.filteredTargets());
            while (block.maxTargets() > 0 && targets.size() > block.maxTargets()) {
                Draw trim = draw(random);
                random = trim.after();
                int replace = trim.nonnegative31() % block.maxTargets();
                targets.set(replace, targets.get(targets.size() - 1));
                targets.remove(targets.size() - 1);
            }
            for (Target target : targets) {
                Draw chance = draw(random);
                random = chance.after();
                int chanceValue = chance.nonnegative31() % 100000;
                if (chanceValue > block.chanceRaw()) {
                    comparisons.add(new Comparison(blockOrdinal, target.fullId(), chanceValue,
                            Optional.empty(), Optional.empty(), Disposition.CHANCE_REJECTED));
                    continue;
                }
                if (target.preparation() instanceof Rejected) {
                    comparisons.add(new Comparison(blockOrdinal, target.fullId(), chanceValue,
                            Optional.empty(), Optional.empty(), Disposition.PREPARATION_REJECTED));
                    continue;
                }
                if (!(target.preparation() instanceof Scored scored)) {
                    throw new IllegalArgumentException("unknown sealed preparation");
                }
                Draw penalty = draw(random);
                random = penalty.after();
                int subtract = penalty.nonnegative31() % 100;
                // Signed 64-bit truncation then low32 subtraction is what caller EAX uses.
                int margin = (int) (scored.senderWillDoRaw() / 100000L) - subtract;
                Disposition disposition = Disposition.NOT_BETTER;
                if (margin > best) {
                    best = margin;
                    selected = OptionalLong.of(target.fullId());
                    disposition = Disposition.NEW_MAXIMUM;
                }
                comparisons.add(new Comparison(blockOrdinal, target.fullId(), chanceValue,
                        Optional.of(subtract), Optional.of(margin), disposition));
            }
        }
        return new Result(selected, best, comparisons, random);
    }
}
