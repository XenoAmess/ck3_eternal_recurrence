package org.xar.ck3.markets.futures;

import java.util.HashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.core.AccountId;
import org.xar.ck3.markets.core.BeneficiaryId;
import org.xar.ck3.markets.core.CoinId;
import org.xar.ck3.markets.core.FinancialMarket;
import org.xar.ck3.markets.debt.DebtLedger;
import org.xar.ck3.markets.oracle.PriceQuote;
import org.xar.ck3.markets.oracle.Quality;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.markets.futures.FuturesExchange.*;

final class FuturesExchangeTest {
    private static final AccountId A = new AccountId("a");
    private static final AccountId B = new AccountId("b");
    private static final AccountId C = new AccountId("c");
    private static final AccountId FUND = new AccountId("fund");
    private static final CoinId COIN = new CoinId("coin");
    private static final class Fixture {
        final FinancialMarket cash = new FinancialMarket();
        final DebtLedger debt = new DebtLedger();
        final Map<Long, PriceQuote> prices = new HashMap<>();
        final FuturesExchange exchange;
        Fixture(long fundCents, Kind kind, long expiry) {
            cash.createAccount(A, new BeneficiaryId("a"), 100_000);
            cash.createAccount(B, new BeneficiaryId("b"), 100_000);
            cash.createAccount(C, new BeneficiaryId("c"), 100_000);
            cash.createAccount(FUND, new BeneficiaryId("fund"), fundCents);
            price(0, 1_000);
            exchange = new FuturesExchange("test", cash, debt, FUND, (asset, day) -> prices.get(day));
            exchange.register(new Contract("c", COIN, kind, expiry));
        }
        void price(long day, long price) {
            prices.put(day, new PriceQuote(COIN.value(), day, price, price, 10,
                    Quality.SINGLE_VENUE, true, "test", day, "fixture:single-venue"));
        }
        void pending(long day) {
            prices.put(day, new PriceQuote(COIN.value(), day, 1_000, 1_000, 0,
                    Quality.PENDING, false, "missing", 0, "fixture:single-venue"));
        }
        PositionView pair(long lots, int leverage) {
            exchange.submit(B, "c", Direction.SHORT, lots, 1_000, leverage);
            return exchange.submit(A, "c", Direction.LONG, lots, 1_000, leverage).fills().stream()
                    .map(fill -> exchange.snapshot().positions().stream().filter(p -> p.id() == fill.resultingPosition()).findFirst().orElseThrow())
                    .findFirst().orElseThrow();
        }
        long total() { return cash.snapshot().totalCashCents(); }
    }

    @Test void actualOpposingCashCreatesPositionAndOnlyFeesLeaveWallets() {
        Fixture f = new Fixture(0, Kind.DATED, 30); long total = f.total();
        PositionView p = f.pair(2, 5);
        assertEquals(400, f.cash.account(p.longEscrow()).availableCashCents());
        assertEquals(400, f.cash.account(p.shortEscrow()).availableCashCents());
        assertEquals(12, f.cash.feeTreasuryCents());
        assertEquals(total, f.total());
        assertThrows(IllegalArgumentException.class, () -> f.cash.transferCash(p.longEscrow(), A, 1));
    }
    @Test void priceTimeAndPartialFillsReserveActualCash() {
        Fixture f = new Fixture(0, Kind.DATED, 30);
        var first = f.exchange.submit(B, "c", Direction.SHORT, 1, 990, 2);
        var second = f.exchange.submit(C, "c", Direction.SHORT, 2, 1_000, 3);
        var incoming = f.exchange.submit(A, "c", Direction.LONG, 2, 1_010, 5);
        assertEquals(2, incoming.fills().size());
        assertEquals(first.order().id(), incoming.fills().get(0).restingOrder());
        assertEquals(990, incoming.fills().get(0).priceCents());
        assertEquals(second.order().id(), incoming.fills().get(1).restingOrder());
        assertEquals(1, f.exchange.snapshot().orders().get(1).remainingLots());
        assertEquals(300_000, f.total());
    }
    @Test void laterRelatedCrossingRollsBackEarlierExternalFill() {
        Fixture f = new Fixture(0, Kind.DATED, 30);
        AccountId alias = new AccountId("alias");
        f.cash.createAccount(alias, new BeneficiaryId("a"), 10_000);
        f.exchange.submit(B, "c", Direction.SHORT, 1, 990, 2);
        f.exchange.submit(alias, "c", Direction.SHORT, 1, 1_000, 2);
        var cash = f.cash.snapshot(); var futures = f.exchange.snapshot();
        assertThrows(IllegalArgumentException.class, () -> f.exchange.submit(A, "c", Direction.LONG, 2, 1_000, 2));
        assertEquals(cash, f.cash.snapshot()); assertEquals(futures, f.exchange.snapshot());
    }
    @Test void insufficientCashDoesNotPublishEscrowOrOrder() {
        Fixture f = new Fixture(0, Kind.DATED, 30);
        var cash = f.cash.snapshot(); var futures = f.exchange.snapshot();
        assertThrows(IllegalArgumentException.class, () -> f.exchange.submit(A, "c", Direction.LONG, 1000, 1_000, 1));
        assertEquals(cash, f.cash.snapshot()); assertEquals(futures, f.exchange.snapshot());
    }
    @Test void cancellationRefundsOnlyUnspentRealReservation() {
        Fixture f = new Fixture(0, Kind.DATED, 30);
        long opening = f.cash.account(A).availableCashCents();
        var order = f.exchange.submit(A, "c", Direction.LONG, 2, 1_000, 3);
        assertTrue(f.cash.account(A).availableCashCents() < opening);
        f.exchange.cancel(A, order.order().id());
        assertEquals(opening, f.cash.account(A).availableCashCents());
        assertThrows(IllegalArgumentException.class, () -> f.exchange.cancel(A, order.order().id()));
    }
    @Test void dailyRealizedVariationThenExpiryDoesNotPayEntryProfitTwice() {
        Fixture f = new Fixture(0, Kind.DATED, 2); PositionView p = f.pair(2, 2);
        long a = f.cash.account(A).availableCashCents();
        f.price(1, 1_050); f.exchange.advanceDay(1);
        assertEquals(a + 100, f.cash.account(A).availableCashCents());
        assertEquals(900, f.cash.account(p.shortEscrow()).availableCashCents());
        var before = f.cash.snapshot(); assertFalse(f.exchange.advanceDay(1).applied()); assertEquals(before, f.cash.snapshot());
        f.price(2, 1_080); f.exchange.advanceDay(2);
        assertEquals(a + 160 + 1_000, f.cash.account(A).availableCashCents());
        assertEquals(300_000, f.total());
    }
    @Test void gapDefaultRetainsWinnerClaimAndFundRecourseWithoutMinting() {
        Fixture f = new Fixture(50, Kind.DATED, 30); PositionView p = f.pair(1, 10);
        f.price(1, 1_400); f.exchange.advanceDay(1);
        var debt = f.debt.snapshot().debts().get(0);
        assertEquals(300, debt.originalShortfallCents());
        assertEquals(50, debt.fundRecourseCents());
        assertEquals(250, debt.winnerUnpaidCents());
        assertEquals(0, f.cash.account(FUND).availableCashCents());
        assertEquals(300_050, f.total());
        assertEquals(PositionStatus.DEFAULTED, f.exchange.snapshot().positions().get(0).status());
        assertEquals(0, f.cash.account(p.shortEscrow()).availableCashCents());
    }
    @Test void pendingOraclePreservesPositionsAndCollateralAndDefersExpiry() {
        Fixture f = new Fixture(0, Kind.DATED, 1); f.pair(1, 2); var cash = f.cash.snapshot();
        f.pending(1); var result = f.exchange.advanceDay(1);
        assertEquals(0, result.marked()); assertEquals(cash, f.cash.snapshot());
        assertEquals(PositionStatus.OPEN, f.exchange.snapshot().positions().get(0).status());
        assertThrows(IllegalArgumentException.class, () -> f.exchange.submit(C, "c", Direction.LONG, 1, 1000, 1));
        f.price(2, 1_050); assertEquals(1, f.exchange.advanceDay(2).closed());
    }
    @Test void withdrawalsKeepInitialRatherThanMaintenanceMargin() {
        Fixture f = new Fixture(0, Kind.DATED, 30); PositionView p = f.pair(1, 2);
        f.exchange.addMargin(A, p.id(), 100);
        f.exchange.withdrawMargin(A, p.id(), 100);
        var before = f.cash.snapshot();
        assertThrows(IllegalArgumentException.class, () -> f.exchange.withdrawMargin(A, p.id(), 1));
        assertEquals(before, f.cash.snapshot());
    }
    @Test void genuineReductionNovatesPartialExposureAtActualPrice() {
        Fixture f = new Fixture(0, Kind.DATED, 30); PositionView p = f.pair(2, 2);
        f.exchange.submit(C, "c", Direction.LONG, 1, 1_050, 2);
        var result = f.exchange.reduce(A, p.id(), 1, 1_040);
        assertEquals(1_050, result.fills().get(0).priceCents());
        var replacement = f.exchange.snapshot().positions().stream()
                .filter(v -> v.id() == result.fills().get(0).resultingPosition()).findFirst().orElseThrow();
        assertEquals(C, replacement.longAccount()); assertEquals(B, replacement.shortAccount());
        assertEquals(1, replacement.lots()); assertEquals(1_050, replacement.markCents());
        assertEquals(1, f.exchange.snapshot().positions().get(0).lots());
        assertEquals(1_000, f.exchange.snapshot().positions().get(0).markCents());
        assertEquals(300_000, f.total());
    }
    @Test void stopGapUsesAvailableBidAndCannotInventStopPriceLiquidity() {
        Fixture f = new Fixture(0, Kind.DATED, 30); PositionView p = f.pair(2, 2);
        f.exchange.setStops(A, p.id(), 990, 0);
        f.exchange.submit(C, "c", Direction.LONG, 1, 950, 2);
        f.price(1, 970); f.exchange.advanceDay(1);
        assertTrue(f.exchange.snapshot().fills().stream().anyMatch(v -> v.day() == 1 && v.priceCents() == 950));
        assertTrue(f.exchange.snapshot().orders().stream().anyMatch(v -> v.closePositionId() == p.id() && v.remainingLots() == 1));
        assertTrue(f.exchange.snapshot().orders().stream().filter(v -> v.closePositionId() == p.id()).allMatch(v -> v.status() == Status.CANCELLED));
        assertEquals(300_000, f.total());
    }
    @Test void cappedPerpetualFundingTransfersActualMarginOnce() {
        Fixture f = new Fixture(0, Kind.PERPETUAL, 0); f.pair(100, 2);
        long a = f.cash.account(A).availableCashCents(); long b = f.cash.account(B).availableCashCents();
        f.price(1, 1_000);
        // A genuine premium print requires both independently funded counterparts.
        f.exchange.submit(B, "c", Direction.SHORT, 10, 1_100, 2);
        f.exchange.submit(C, "c", Direction.LONG, 10, 1_100, 2);
        f.exchange.advanceDay(1);
        assertEquals(a, f.cash.account(A).availableCashCents()); // funding paid from reserved margin
        assertTrue(f.cash.account(B).availableCashCents() > b - 6_000);
        assertEquals(300_000, f.total());
        var before = f.cash.snapshot(); f.exchange.advanceDay(1); assertEquals(before, f.cash.snapshot());
    }
    @Test void qualificationControlsTwentyTimesAndModelIndexNeedsNoCoinSupply() {
        Fixture f = new Fixture(0, Kind.DATED, 30);
        assertThrows(IllegalArgumentException.class, () -> f.exchange.submit(A, "c", Direction.LONG, 1, 1000, 20));
        f.prices.put(0L, new PriceQuote(COIN.value(), 0, 1000, 1000, 20, Quality.MULTI_VENUE, true, "three independent venues", 0, "fixture:three-independent-venues"));
        assertEquals(Status.OPEN, f.exchange.submit(A, "c", Direction.LONG, 1, 1000, 20).order().status());
        assertNotNull(f.exchange.register(new Contract("grain", new CoinId("index:grain"), Kind.PERPETUAL, 0)));
    }
    @Test void fundingDefaultClosesAndReleasesOtherCollateralWithoutFundInsurance() {
        Fixture f = new Fixture(1_000, Kind.PERPETUAL, 0); PositionView original = f.pair(100, 10);
        f.exchange.submit(B, "c", Direction.SHORT, 10, 1_100, 2);
        f.exchange.submit(C, "c", Direction.LONG, 10, 1_100, 2);
        f.price(1, 901); f.exchange.advanceDay(1);
        assertEquals(10, f.cash.account(original.longEscrow()).availableCashCents());
        f.exchange.submit(B, "c", Direction.SHORT, 10, 1_000, 2);
        f.exchange.submit(C, "c", Direction.LONG, 10, 1_000, 2);
        f.price(2, 901); f.exchange.advanceDay(2);
        var debt = f.debt.snapshot().debts().get(0);
        assertEquals(DebtLedger.SettlementKind.FUNDING, debt.key().kind());
        assertEquals(80, debt.winnerUnpaidCents());
        assertEquals(0, debt.fundPaidCents());
        assertEquals(1_000, f.cash.account(FUND).availableCashCents());
        assertEquals(0, f.cash.account(original.shortEscrow()).availableCashCents());
        assertEquals(PositionStatus.DEFAULTED, f.exchange.snapshot().positions().get(0).status());
        assertTrue(f.exchange.snapshot().orders().stream()
                .filter(order -> order.closePositionId() == original.id()).noneMatch(order -> order.status() == Status.OPEN));
        assertEquals(301_000, f.total());
    }
    @Test void oracleGapCancelsOldOpeningPriceBeforeItCanOverrunNewCounterpartyMargin() {
        Fixture f = new Fixture(0, Kind.DATED, 30);
        var old = f.exchange.submit(A, "c", Direction.LONG, 1, 1_000, 2);
        assertTrue(f.cash.account(A).availableCashCents() < 100_000);
        f.price(1, 500); f.exchange.advanceDay(1);
        assertEquals(Status.CANCELLED, f.exchange.snapshot().orders().get(0).status());
        assertEquals(100_000, f.cash.account(A).availableCashCents());
        assertEquals(0, f.cash.account(old.order().escrow()).availableCashCents());
        var fresh = f.exchange.submit(B, "c", Direction.SHORT, 1, 500, 2);
        assertTrue(fresh.fills().isEmpty());
        assertEquals(Status.OPEN, fresh.order().status());
        assertEquals(300_000, f.total());
    }
}
