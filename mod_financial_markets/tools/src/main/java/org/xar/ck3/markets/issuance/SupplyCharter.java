package org.xar.ck3.markets.issuance;

/** Lot-denominated supply with independently locked founder allocation. */
public final class SupplyCharter {
    public record Snapshot(long totalLots, long circulationLots, long treasuryLots,
                           long founderLockedLots, long founderReleasedLots, long undisclosedMintLots) { }
    private final long maximumLots;
    private final boolean mintPermitted;
    private final long founderUnlockDay;
    private long totalLots;
    private long treasuryLots;
    private long circulationLots;
    private long founderLockedLots;
    private long founderReleasedLots;
    private long undisclosedMintLots;
    public SupplyCharter(long totalLots, long maximumLots, long founderLockedLots,
                         long founderUnlockDay, boolean mintPermitted) {
        if (totalLots <= 0 || maximumLots < totalLots || founderLockedLots < 0 || founderLockedLots > totalLots || founderUnlockDay < 0)
            throw new IllegalArgumentException("invalid supply charter");
        this.totalLots = totalLots; this.maximumLots = maximumLots; this.founderLockedLots = founderLockedLots;
        this.treasuryLots = totalLots - founderLockedLots; this.founderUnlockDay = founderUnlockDay; this.mintPermitted = mintPermitted;
    }
    public void allot(long lots) {
        positive(lots);
        if (treasuryLots < lots) throw new IllegalArgumentException("insufficient issued treasury inventory");
        treasuryLots -= lots; circulationLots = Math.addExact(circulationLots, lots);
    }
    public long unlock(long day) {
        if (day < 0) throw new IllegalArgumentException("negative day");
        if (day < founderUnlockDay) return 0;
        long released = founderLockedLots;
        founderLockedLots = 0; founderReleasedLots = Math.addExact(founderReleasedLots, released);
        return released;
    }
    public void mint(long lots, boolean disclosed) {
        positive(lots);
        if (!mintPermitted) throw new IllegalStateException("fixed supply charter");
        long next = Math.addExact(totalLots, lots);
        if (next > maximumLots) throw new IllegalArgumentException("charter cap exceeded");
        totalLots = next; treasuryLots = Math.addExact(treasuryLots, lots);
        if (!disclosed) undisclosedMintLots = Math.addExact(undisclosedMintLots, lots);
    }
    public void burnTreasury(long lots) {
        positive(lots);
        if (treasuryLots < lots) throw new IllegalArgumentException("cannot burn other holders' property");
        treasuryLots -= lots; totalLots -= lots;
    }
    public Snapshot snapshot() {
        return new Snapshot(totalLots, circulationLots, treasuryLots, founderLockedLots, founderReleasedLots, undisclosedMintLots);
    }
    private static void positive(long lots) { if (lots <= 0) throw new IllegalArgumentException("positive whole lots required"); }
}
