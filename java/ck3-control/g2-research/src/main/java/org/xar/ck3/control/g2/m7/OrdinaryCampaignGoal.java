package org.xar.ck3.control.g2.m7;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** The ordinary campaign's existing semantic intent. No action, writer or restore authority. */
public final class OrdinaryCampaignGoal {
    public static final String GOAL_KEY = "dynasty_continuity";
    private OrdinaryCampaignGoal() { }

    public record Goal(String campaignId, long originCharacterId, long currentCharacterId, Progress progress) {
        public Goal {
            StrictJson.text(campaignId); NativeCharacterId.of(originCharacterId); NativeCharacterId.of(currentCharacterId);
            Objects.requireNonNull(progress);
        }
    }
    public record Progress(long reconciledSuccessions, Optional<Succession> lastSuccession) {
        public Progress { StrictJson.safe(reconciledSuccessions, 0); Objects.requireNonNull(lastSuccession); }
    }
    public record Succession(long predecessorCharacterId, long actualSuccessorCharacterId,
            List<Long> matchedInheritedTitleIds, List<Long> expectedOtherHeirTitleIds,
            List<Long> expectedWithoutHeirTitleIds) {
        public Succession {
            NativeCharacterId.of(predecessorCharacterId); NativeCharacterId.of(actualSuccessorCharacterId);
            matchedInheritedTitleIds = ids(matchedInheritedTitleIds);
            expectedOtherHeirTitleIds = ids(expectedOtherHeirTitleIds);
            expectedWithoutHeirTitleIds = ids(expectedWithoutHeirTitleIds);
        }
    }
    public enum Verdict { MATCHED, MISMATCHED, UNEXPECTED_SUCCESSOR, TITLE_DISTRIBUTION_MISMATCH, UNAVAILABLE, UNKNOWN }
    /** Narrow typed consumption of the original complete M3 reconciliation. */
    public record Reconciliation(Verdict verdict, long predecessorCharacterId, long actualSuccessorCharacterId,
            List<Long> matchedInheritedTitleIds, List<Long> expectedOtherHeirTitleIds,
            List<Long> expectedWithoutHeirTitleIds) {
        public Reconciliation {
            Objects.requireNonNull(verdict); NativeCharacterId.of(predecessorCharacterId); NativeCharacterId.of(actualSuccessorCharacterId);
            matchedInheritedTitleIds = ids(matchedInheritedTitleIds);
            expectedOtherHeirTitleIds = ids(expectedOtherHeirTitleIds);
            expectedWithoutHeirTitleIds = ids(expectedWithoutHeirTitleIds);
        }
    }
    public record Priority(int priority, String action, String reason) {
        public Priority { StrictJson.safe(priority, 0); StrictJson.text(action); StrictJson.text(reason); }
    }
    public record GoalPlan(String policy, String goalKey, String campaignId, long currentCharacterId,
            Progress progress, String focus, List<Priority> priorities) {
        public GoalPlan {
            StrictJson.text(policy); StrictJson.text(goalKey); StrictJson.text(campaignId); NativeCharacterId.of(currentCharacterId);
            Objects.requireNonNull(progress); StrictJson.text(focus); priorities = List.copyOf(priorities);
        }
    }

    public static Goal newGoal(String campaignId, long actorCharacterId) {
        return new Goal(campaignId, actorCharacterId, actorCharacterId, new Progress(0, Optional.empty()));
    }
    public static Goal continueGoal(Goal goal, Reconciliation reconciliation) {
        Objects.requireNonNull(goal); Objects.requireNonNull(reconciliation);
        StrictJson.require(reconciliation.verdict() == Verdict.MATCHED
                && reconciliation.predecessorCharacterId() == goal.currentCharacterId()
                && reconciliation.actualSuccessorCharacterId() != goal.currentCharacterId(),
                "ordinary campaign goal requires the matched predecessor");
        long count = Math.addExact(goal.progress().reconciledSuccessions(), 1);
        var transition = new Succession(reconciliation.predecessorCharacterId(), reconciliation.actualSuccessorCharacterId(),
                reconciliation.matchedInheritedTitleIds(), reconciliation.expectedOtherHeirTitleIds(),
                reconciliation.expectedWithoutHeirTitleIds());
        return new Goal(goal.campaignId(), goal.originCharacterId(), reconciliation.actualSuccessorCharacterId(),
                new Progress(count, Optional.of(transition)));
    }
    public static GoalPlan plan(Goal goal) {
        Objects.requireNonNull(goal);
        return new GoalPlan("ordinary-campaign-goal-v1", GOAL_KEY, goal.campaignId(), goal.currentCharacterId(),
                goal.progress(), "marriage", List.of(
                new Priority(100, "seek_current_ruler_marriage_and_family_continuity",
                        "retain the campaign's family intent with fresh ruler candidates"),
                new Priority(60, "review_current_ruler_succession_and_partition",
                        "reuse the current native heir and estate observations")));
    }
    private static long id(long value) { return StrictJson.safe(value, 1); }
    private static List<Long> ids(List<Long> values) {
        List<Long> result = List.copyOf(values); result.forEach(OrdinaryCampaignGoal::id); return result;
    }
}
