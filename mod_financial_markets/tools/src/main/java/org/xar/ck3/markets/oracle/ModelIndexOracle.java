package org.xar.ck3.markets.oracle;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Disclosed Mod formulas, never represented as independently traded physical commodity prices. */
public final class ModelIndexOracle implements PriceOracle {
    public static final String GRAIN = "index:grain";
    public static final String MILITARY = "index:military";
    public static final String TRADE = "index:trade";
    public static final String SOURCE_ID = "model:xfm-fixed-county-basket-v1";
    private final Set<String> basket;
    private Map<String, Long> prices = Map.of(GRAIN, 0L, MILITARY, 0L, TRADE, 0L);
    private long observationDay = -1;
    private long lastValidDay = -1;
    private boolean sufficient;

    public ModelIndexOracle(List<String> countyIds) {
        Objects.requireNonNull(countyIds, "countyIds");
        Set<String> checked = new HashSet<>();
        if (countyIds.size() > 32) throw new IllegalArgumentException("at most 32 fixed basket counties");
        for (String county : countyIds) {
            if (county == null || county.isBlank() || !checked.add(county)) {
                throw new IllegalArgumentException("nonblank unique basket county IDs required");
            }
        }
        basket = Set.copyOf(checked);
    }

    /** Only existing basket members with actual current holders are supplied by the native producer. */
    public synchronized void observe(long day, List<CountyObservation> observations) {
        Objects.requireNonNull(observations, "observations");
        if (day < 0 || day <= observationDay) throw new IllegalArgumentException("new observation day required");
        int prosperity = 0;
        int control = 0;
        int wars = 0;
        Set<String> seen = new HashSet<>();
        for (CountyObservation county : observations) {
            Objects.requireNonNull(county, "county observation");
            if (!basket.contains(county.countyId()) || !seen.add(county.countyId())) {
                throw new IllegalArgumentException("unknown or duplicate basket county");
            }
            prosperity += county.prosperity();
            control += county.control();
            if (county.holderAtWar()) wars++;
        }
        boolean enough = observations.size() >= 8;
        Map<String, Long> updated = prices;
        if (enough) {
            int count = observations.size();
            long meanProsperity = prosperity / count;
            long meanControl = control / count;
            long warBps = wars * 10_000L / count;
            // Tenths preserve the exact native decimal coefficients before the final floor.
            long grainTenths = 100_000 + warBps * 4 + (100 - meanControl) * 400 - meanProsperity * 500;
            long militaryTenths = 100_000 + warBps * 8 + (100 - meanControl) * 200 + meanProsperity * 200;
            long tradeTenths = 100_000 - warBps * 5 - (100 - meanControl) * 300 + meanProsperity * 800;
            updated = Map.of(GRAIN, bounded(grainTenths), MILITARY, bounded(militaryTenths),
                    TRADE, bounded(tradeTenths));
        }
        prices = updated;
        observationDay = day;
        sufficient = enough;
        if (enough) lastValidDay = day;
    }

    @Override
    public synchronized PriceQuote quote(String assetId, long day) {
        Long price = prices.get(Objects.requireNonNull(assetId, "assetId"));
        if (price == null || day < 0 || day < observationDay) throw new IllegalArgumentException("unknown index or clock regression");
        boolean current = sufficient && observationDay == day;
        return new PriceQuote(assetId, day, price, price, current ? 5 : 0,
                current ? Quality.MODEL_INDEX : Quality.PENDING, current,
                current ? "disclosed_county_model_index" : "missing_current_basket_observations", lastValidDay, SOURCE_ID);
    }

    private static long bounded(long tenths) {
        return Math.max(3_000, Math.min(30_000, Math.floorDiv(tenths, 10)));
    }
}
