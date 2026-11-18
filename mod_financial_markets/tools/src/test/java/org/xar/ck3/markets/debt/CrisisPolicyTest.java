package org.xar.ck3.markets.debt;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.debt.CrisisPolicy.*;

final class CrisisPolicyTest {
    private Context context(boolean alive, boolean adult, boolean ai, boolean personal, long debt,
                            long free, long reserved, long outside, int holdings, boolean complete, long relief) {
        return new Context(alive, adult, ai, personal, false, debt, free, reserved, outside,
                100, 40, 3, holdings, 0, 0, complete, 60, relief);
    }
    private final State mature = new State(30, 59, 3, true, false);

    @Test void adultAiMustHaveRealSevereDebtMatureCrisisAndRecordedHelp() {
        var serious = context(true, true, true, true, 3_000, 0, 0, 0, 0, true, 0);
        assertTrue(CrisisPolicy.eligibleForTerminalReview(serious, mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(serious, new State(55, 59, 3, true, false)));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(serious, new State(30, 59, 3, false, false)));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(serious, new State(30, 59, 3, true, true)));
    }

    @Test void humansChildrenDeadAndInheritedEstateHoldersAreProtected() {
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, false, true, 3_000, 0, 0, 0, 0, true, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, false, true, true, 3_000, 0, 0, 0, 0, true, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(false, true, true, true, 3_000, 0, 0, 0, 0, true, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, true, false, 3_000, 0, 0, 0, 0, true, 0), mature));
    }

    @Test void paidDebtAidHiddenAssetsAndIncompleteReviewCancelTerminalEligibility() {
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, true, true, 0, 0, 0, 0, 0, true, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, true, true, 3_000, 1, 0, 0, 0, true, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, true, true, 3_000, 0, 1, 0, 0, true, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, true, true, 3_000, 0, 0, 1, 0, true, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, true, true, 3_000, 0, 0, 0, 1, true, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, true, true, 3_000, 0, 0, 0, 0, false, 0), mature));
        assertFalse(CrisisPolicy.eligibleForTerminalReview(context(true, true, true, true, 3_000, 0, 0, 0, 0, true, 90), mature));
    }
}
