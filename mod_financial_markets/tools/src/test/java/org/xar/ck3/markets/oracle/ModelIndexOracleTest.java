package org.xar.ck3.markets.oracle;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Map;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;

final class ModelIndexOracleTest {
    @Test void actualWarAndDisruptionMoveThreeModelsDifferently() {
        ModelIndexOracle oracle = oracle();
        oracle.observe(0, counties(50, 100, false));
        assertEquals(7_500, oracle.quote(ModelIndexOracle.GRAIN, 0).indexCents());
        assertEquals(11_000, oracle.quote(ModelIndexOracle.MILITARY, 0).indexCents());
        assertEquals(14_000, oracle.quote(ModelIndexOracle.TRADE, 0).indexCents());
        oracle.observe(1, counties(50, 80, true));
        assertEquals(12_300, oracle.quote(ModelIndexOracle.GRAIN, 1).indexCents());
        assertEquals(19_400, oracle.quote(ModelIndexOracle.MILITARY, 1).indexCents());
        assertEquals(8_400, oracle.quote(ModelIndexOracle.TRADE, 1).indexCents());
        assertEquals(Quality.MODEL_INDEX, oracle.quote(ModelIndexOracle.GRAIN, 1).quality());
        assertEquals(5, oracle.quote(ModelIndexOracle.GRAIN, 1).maxLeverage());
    }

    @Test void modelNeedsEightRealMembersAndCurrentObservations() {
        ModelIndexOracle oracle = oracle();
        oracle.observe(0, counties(50, 100, false));
        assertEquals(Quality.PENDING, oracle.quote(ModelIndexOracle.GRAIN, 1).quality());
        oracle.observe(1, counties(50, 100, false).subList(0, 7));
        PriceQuote pending = oracle.quote(ModelIndexOracle.GRAIN, 1);
        assertEquals(7_500, pending.indexCents());
        assertEquals(0, pending.maxLeverage());
        assertEquals(0, pending.lastObservationDay());
        assertFalse(pending.terminationEligible());
    }

    @Test void membershipAndDuplicateObservationsAreValidatedBeforePublication() {
        ModelIndexOracle oracle = oracle();
        oracle.observe(0, counties(50, 100, false));
        CountyObservation first = new CountyObservation("c0", 100, 100, true);
        assertThrows(IllegalArgumentException.class, () -> oracle.observe(1, List.of(first, first)));
        assertThrows(IllegalArgumentException.class, () -> oracle.observe(1,
                List.of(new CountyObservation("unknown", 0, 0, false))));
        assertEquals(Quality.MODEL_INDEX, oracle.quote(ModelIndexOracle.GRAIN, 0).quality());
    }

    @Test void explicitRouteCannotSubstituteAnotherAssetOrAStalePublication() {
        ModelIndexOracle oracle = oracle();
        oracle.observe(0, counties(50, 100, false));
        CompositePriceOracle routes = new CompositePriceOracle(Map.of(ModelIndexOracle.GRAIN, oracle));
        assertEquals(Quality.MODEL_INDEX, routes.quote(ModelIndexOracle.GRAIN, 0).quality());
        assertThrows(IllegalArgumentException.class, () -> routes.quote("unknown", 0));
        PriceOracle wrong = (asset, day) -> oracle.quote(ModelIndexOracle.MILITARY, day);
        assertThrows(IllegalStateException.class, () -> new CompositePriceOracle(Map.of("wrong", wrong)).quote("wrong", 0));
    }

    @Test void pendingQuotesCannotAuthorizeTerminationAndSingleVenueCannotClaimTwenty() {
        assertThrows(IllegalArgumentException.class, () -> new PriceQuote("x", 0, 100, 100,
                1, Quality.PENDING, false, "pending", -1, "fixture:pending"));
        assertThrows(IllegalArgumentException.class, () -> new PriceQuote("x", 0, 100, 100,
                20, Quality.SINGLE_VENUE, true, "fake", 0, "fixture:single"));
        assertThrows(IllegalArgumentException.class, () -> new PriceQuote("x", 0, 0, 0,
                5, Quality.MODEL_INDEX, true, "zero", 0, "fixture:model"));
    }

    @Test void explicitNewFaceMatchesBoundedModelAndLegacyConstructorKeepsOldUnits() {
        List<String> basket = IntStream.range(0, 8).mapToObj(i -> "c" + i).toList();
        ModelIndexOracle legacy = new ModelIndexOracle(basket), small = new ModelIndexOracle(basket, ModelIndexOracle.NEW_INDEX_QUOTE_DIVISOR);
        assertEquals(1, legacy.quoteDivisor()); assertEquals(100, small.quoteDivisor());
        assertEquals(0, small.quote(ModelIndexOracle.GRAIN, 0).markCents());
        for (int day = 0; day < 3; day++) {
            List<CountyObservation> observations = counties(day == 0 ? 0 : 100, day == 2 ? 0 : 100, day == 2);
            legacy.observe(day, observations); small.observe(day, observations);
            for (String asset : List.of(ModelIndexOracle.GRAIN, ModelIndexOracle.MILITARY, ModelIndexOracle.TRADE)) {
                assertEquals(legacy.quote(asset, day).indexCents() / 100, small.quote(asset, day).indexCents());
                assertEquals(small.quote(asset, day).indexCents(), small.quote(asset, day).markCents());
                assertEquals(5, small.quote(asset, day).maxLeverage());
            }
        }
        long prior = small.quote(ModelIndexOracle.GRAIN, 2).markCents();
        small.observe(3, counties(0, 100, false).subList(0, 7));
        assertEquals(prior, small.quote(ModelIndexOracle.GRAIN, 3).markCents());
        assertEquals(0, small.quote(ModelIndexOracle.GRAIN, 3).maxLeverage());
        assertEquals(2, small.quote(ModelIndexOracle.GRAIN, 3).lastObservationDay());
        assertThrows(IllegalArgumentException.class, () -> new ModelIndexOracle(basket, 0));
        assertThrows(IllegalArgumentException.class, () -> new ModelIndexOracle(basket, 10));
    }

    private static ModelIndexOracle oracle() {
        return new ModelIndexOracle(IntStream.range(0, 8).mapToObj(i -> "c" + i).toList());
    }

    private static List<CountyObservation> counties(int prosperity, int control, boolean war) {
        return IntStream.range(0, 8).mapToObj(i -> new CountyObservation("c" + i, prosperity, control, war)).toList();
    }
}
