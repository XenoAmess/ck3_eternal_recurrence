package org.xar.ck3.markets.listing;

/** Reference admission quote in cents. Restricted capital remains owned; it is not exchange income. */
public final class ListingFunding {
    public enum Tier { MICRO, STANDARD }
    public record Allocation(long registrationFeeCents, long listingFeeCents,
                             long prepaidMaintenanceCents, long performanceBondCents,
                             long makerCashCents) {
        public long earnedFeesCents() { return Math.addExact(registrationFeeCents, listingFeeCents); }
        public long restrictedCashCents() {
            return Math.addExact(prepaidMaintenanceCents, Math.addExact(performanceBondCents, makerCashCents));
        }
        public long requiredCashCents() { return Math.addExact(earnedFeesCents(), restrictedCashCents()); }
    }
    public record Funding(long existingCashCents, long actualProceedsCents,
                          long freeProjectCashCents, Allocation allocation) { }
    private ListingFunding() { }

    /** This quote alone does not check rolling financing, outstanding obligations or actual subscription demand. */
    public static Allocation quote(Tier tier, long actualRaisedCents) {
        if (tier == null || actualRaisedCents < 0) throw new IllegalArgumentException("tier and nonnegative real proceeds required");
        if (tier == Tier.MICRO && actualRaisedCents > 5_000) throw new IllegalArgumentException("micro financing exceeds 50 gold");
        long registration = tier == Tier.MICRO ? 100 : 500;
        long listing = Math.addExact(tier == Tier.MICRO ? 100 : 1_000, ceilDivide(actualRaisedCents, 50));
        long maintenance = tier == Tier.MICRO ? 60 : 600;
        long bond = Math.max(tier == Tier.MICRO ? 100 : 1_000, ceilDivide(actualRaisedCents, 20));
        long maker = Math.max(tier == Tier.MICRO ? 200 : 2_000, ceilDivide(actualRaisedCents, 10));
        return new Allocation(registration, listing, maintenance, bond, maker);
    }

    public static Funding fund(Tier tier, long existingCashCents, long actualRaisedCents) {
        if (existingCashCents < 0) throw new IllegalArgumentException("existing cash cannot be negative");
        Allocation allocation = quote(tier, actualRaisedCents);
        long resources = Math.addExact(existingCashCents, actualRaisedCents);
        long free = Math.subtractExact(resources, allocation.requiredCashCents());
        if (free < 0) throw new IllegalArgumentException("insufficient real funding including fees and restricted capital");
        return new Funding(existingCashCents, actualRaisedCents, free, allocation);
    }

    private static long ceilDivide(long numerator, long denominator) {
        return Math.addExact(numerator / denominator, numerator % denominator == 0 ? 0 : 1);
    }
}
