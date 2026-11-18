package org.xar.ck3.markets.issuance;

/** Reclassifies existing eligible fees before collecting the net maintenance liability. */
public final class Maintenance {
    public record Charge(long creditUsedCents, long prepaidUsedCents, long arrearsAddedCents,
                         long creditRemainingCents, long prepaidRemainingCents) { }
    private Maintenance() { }
    public static Charge charge(long monthlyFeeCents, long eligibleCreditCents, long prepaidCents) {
        if (monthlyFeeCents < 0 || eligibleCreditCents < 0 || prepaidCents < 0) throw new IllegalArgumentException("negative maintenance input");
        long credit = Math.min(monthlyFeeCents, eligibleCreditCents);
        long due = monthlyFeeCents - credit;
        long prepaid = Math.min(due, prepaidCents);
        return new Charge(credit, prepaid, due - prepaid, eligibleCreditCents - credit, prepaidCents - prepaid);
    }
}
