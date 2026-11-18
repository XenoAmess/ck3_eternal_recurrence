package org.xar.ck3.markets.debt;

/** Conservative narrative eligibility. A failed investment alone is never a debt or a terminal event. */
public final class CrisisPolicy {
    public record Context(boolean alive, boolean adult, boolean ai, boolean originalPersonalHolder,
                          boolean accountFrozen, long outstandingCents, long freeCents, long reservedCents,
                          long outsideLiquidCents, long monthlyDisposableIncomeCents, long overdueDays,
                          int stressLevel, int holdingsCount, int openOrdersCount, int openPositionsCount,
                          boolean completeAssetReview, long day, long reliefUntilDay) {
        public Context {
            if (outstandingCents < 0 || freeCents < 0 || reservedCents < 0 || outsideLiquidCents < 0
                    || monthlyDisposableIncomeCents < 0 || overdueDays < 0 || stressLevel < 0 || stressLevel > 3
                    || holdingsCount < 0 || openOrdersCount < 0 || openPositionsCount < 0 || day < 0 || reliefUntilDay < 0)
                throw new IllegalArgumentException("invalid crisis evidence");
        }
    }
    public record State(long beganDay, long nextReviewDay, int reviews, boolean aidOpportunityRecorded,
                        boolean terminalRecorded) {
        public State {
            if (beganDay < 0 || nextReviewDay < beganDay || reviews < 0) throw new IllegalArgumentException("invalid crisis state");
        }
    }
    private CrisisPolicy() { }

    public static boolean seriousDebt(Context context) {
        long threshold = Math.max(1_000, context.monthlyDisposableIncomeCents() > Long.MAX_VALUE / 24
                ? Long.MAX_VALUE : context.monthlyDisposableIncomeCents() * 24);
        return context.alive() && context.adult() && context.ai() && context.originalPersonalHolder()
                && !context.accountFrozen() && context.outstandingCents() > threshold
                && context.overdueDays() >= 30 && context.stressLevel() >= 2
                && context.day() >= context.reliefUntilDay();
    }

    public static boolean eligibleForTerminalReview(Context context, State state) {
        return seriousDebt(context) && !state.terminalRecorded() && state.aidOpportunityRecorded()
                && context.completeAssetReview() && context.freeCents() == 0 && context.reservedCents() == 0
                && context.outsideLiquidCents() == 0 && context.holdingsCount() == 0
                && context.openOrdersCount() == 0 && context.openPositionsCount() == 0
                && context.stressLevel() >= 3 && state.reviews() >= 2
                && context.day() >= state.nextReviewDay() && context.day() - state.beganDay() >= 14;
    }
}
