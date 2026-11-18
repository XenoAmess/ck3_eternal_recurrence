package org.xar.ck3.markets.core;

import org.junit.jupiter.api.Test;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.*;

class FinancialMarketTest {
    private static final AccountId ISSUER = new AccountId("issuer");
    private static final AccountId BUYER = new AccountId("buyer");
    private static final AccountId OTHER = new AccountId("other");
    private static final CoinId COIN = new CoinId("coin-A");
    private static final CoinId SECOND = new CoinId("coin-B");

    @Test
    void issuanceAndCappedMintTransferActualFeesWithoutImportingCash() {
        FinancialMarket market = new FinancialMarket();
        account(market, ISSUER, 100);
        market.issueCoin(COIN, ISSUER, 900, 1_000, 7);
        market.mint(COIN, ISSUER, 100, 3);

        assertEquals(90, market.account(ISSUER).availableCashCents());
        assertEquals(10, market.feeTreasuryCents());
        assertEquals(1_000, market.coin(COIN).issuedCoins());
        assertEquals(1_000, market.account(ISSUER).balance(COIN).availableCoins());
        assertUnchangedOnFailure(market, MarketException.Code.SUPPLY_LIMIT,
                () -> market.mint(COIN, ISSUER, 1, 5));
        assertConserved(market);
    }

    @Test
    void duplicateStableIdentifiersAndUnauthorizedMintFailAtomically() {
        FinancialMarket market = fundedMarket(1_000);
        account(market, OTHER, 100);
        assertUnchangedOnFailure(market, MarketException.Code.ACCOUNT_EXISTS,
                () -> account(market, BUYER, 100));
        assertUnchangedOnFailure(market, MarketException.Code.COIN_EXISTS,
                () -> market.issueCoin(COIN, ISSUER, 1, 10, 0));
        assertUnchangedOnFailure(market, MarketException.Code.NOT_OWNER,
                () -> market.mint(COIN, OTHER, 1, 1));
    }

    @Test
    void issuanceRequiresTheRealUnreservedFeeAndDoesNotLeaveAnEmptyCoin() {
        FinancialMarket market = new FinancialMarket();
        account(market, ISSUER, 4);
        assertUnchangedOnFailure(market, MarketException.Code.INSUFFICIENT_CASH,
                () -> market.issueCoin(COIN, ISSUER, 100, 100, 5));
        assertTrue(market.snapshot().coins().isEmpty());
        assertEquals(0, market.feeTreasuryCents());
    }

    @Test
    void overflowingWalletImportCannotChangeTheWorldCashTotal() {
        FinancialMarket market = new FinancialMarket();
        account(market, ISSUER, Long.MAX_VALUE);
        assertUnchangedOnFailure(market, MarketException.Code.ARITHMETIC_OVERFLOW,
                () -> account(market, BUYER, 1));
        assertEquals(Long.MAX_VALUE, market.snapshot().totalCashCents());
    }

    @Test
    void feesUseCumulativeCeilingAndDoNotOverflowForLargeGrossAmounts() {
        assertEquals(0, TradingFees.cumulativeCents(0));
        assertEquals(1, TradingFees.cumulativeCents(1));
        assertEquals(1, TradingFees.cumulativeCents(333));
        assertEquals(2, TradingFees.cumulativeCents(334));
        assertEquals(3, TradingFees.cumulativeCents(1_000));
        BigInteger gross = BigInteger.valueOf(Long.MAX_VALUE);
        long expected = gross.multiply(BigInteger.valueOf(3)).add(BigInteger.valueOf(999))
                .divide(BigInteger.valueOf(1_000)).longValueExact();
        assertEquals(expected, TradingFees.cumulativeCents(Long.MAX_VALUE));
    }

    @Test
    void buyOrderFreezesPrincipalAndWorstCaseCumulativeFee() {
        FinancialMarket market = fundedMarket(1_000);
        OrderView buy = market.submitLimit(BUYER, COIN, Side.BUY, 4, 100).order();
        assertEquals(598, market.account(BUYER).availableCashCents());
        assertEquals(402, market.account(BUYER).reservedCashCents());
        assertEquals(402, buy.reservedCashCents());
        assertEquals(0, market.feeTreasuryCents());
        assertConserved(market);
    }

    @Test
    void restingAsksHavePriceThenTimePriorityAndTradeAtMakerPrice() {
        FinancialMarket market = fundedMarket(100_000);
        account(market, OTHER, 0);
        market.transferCoins(ISSUER, OTHER, COIN, 500);
        OrderView expensive = market.submitLimit(ISSUER, COIN, Side.SELL, 2, 100).order();
        OrderView cheap = market.submitLimit(OTHER, COIN, Side.SELL, 2, 90).order();
        SubmissionResult result = market.submitLimit(BUYER, COIN, Side.BUY, 3, 110);

        assertEquals(2, result.trades().size());
        assertEquals(cheap.id(), result.trades().get(0).sellOrderId());
        assertEquals(2, result.trades().get(0).lots());
        assertEquals(90, result.trades().get(0).priceCentsPerLot());
        assertEquals(expensive.id(), result.trades().get(1).sellOrderId());
        assertEquals(100, result.trades().get(1).priceCentsPerLot());
        assertEquals(OrderStatus.PARTIALLY_FILLED, market.order(expensive.id()).status());
        assertEquals(99_719, market.account(BUYER).availableCashCents());
        assertEquals(300, market.account(BUYER).balance(COIN).availableCoins());
        assertEquals(3, market.feeTreasuryCents());
        assertConserved(market);
    }

    @Test
    void equalPriceAsksUseOriginalOrderSequence() {
        FinancialMarket market = fundedMarket(1_000);
        account(market, OTHER, 0);
        market.transferCoins(ISSUER, OTHER, COIN, 100);
        OrderView first = market.submitLimit(ISSUER, COIN, Side.SELL, 1, 100).order();
        OrderView second = market.submitLimit(OTHER, COIN, Side.SELL, 1, 100).order();
        SubmissionResult result = market.submitLimit(BUYER, COIN, Side.BUY, 1, 100);
        assertEquals(first.id(), result.trades().getFirst().sellOrderId());
        assertEquals(OrderStatus.OPEN, market.order(second.id()).status());
    }

    @Test
    void restingBidsUseHighestPriceThenTimePriority() {
        FinancialMarket market = fundedMarket(1_000);
        account(market, OTHER, 1_000);
        OrderView older = market.submitLimit(BUYER, COIN, Side.BUY, 1, 100).order();
        OrderView better = market.submitLimit(OTHER, COIN, Side.BUY, 1, 110).order();
        OrderView later = market.submitLimit(BUYER, COIN, Side.BUY, 1, 100).order();
        SubmissionResult result = market.submitLimit(ISSUER, COIN, Side.SELL, 2, 80);
        assertEquals(List.of(better.id(), older.id()), result.trades().stream().map(Trade::buyOrderId).toList());
        assertEquals(List.of(110L, 100L), result.trades().stream().map(Trade::priceCentsPerLot).toList());
        assertEquals(OrderStatus.OPEN, market.order(later.id()).status());
        assertConserved(market);
    }

    @Test
    void buyerPartialFeesAccumulatePerOriginalOrderInsteadOfPerFill() {
        FinancialMarket market = fundedMarket(1_000);
        OrderView buy = market.submitLimit(BUYER, COIN, Side.BUY, 3, 113).order();
        List<Long> buyerFees = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            Trade trade = market.submitLimit(ISSUER, COIN, Side.SELL, 1, 113).trades().getFirst();
            buyerFees.add(trade.buyerFeeCents());
        }
        assertEquals(List.of(1L, 0L, 1L), buyerFees);
        assertEquals(2, market.order(buy.id()).feePaidCents());
        assertEquals(339, market.order(buy.id()).filledGrossCents());
        assertEquals(659, market.account(BUYER).availableCashCents());
        assertEquals(5, market.feeTreasuryCents());
        assertConserved(market);
    }

    @Test
    void sellerPartialFeesAccumulatePerOriginalOrder() {
        FinancialMarket market = fundedMarket(1_000);
        OrderView sell = market.submitLimit(ISSUER, COIN, Side.SELL, 3, 113).order();
        List<Long> sellerFees = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            Trade trade = market.submitLimit(BUYER, COIN, Side.BUY, 1, 113).trades().getFirst();
            sellerFees.add(trade.sellerFeeCents());
        }
        assertEquals(List.of(1L, 0L, 1L), sellerFees);
        assertEquals(2, market.order(sell.id()).feePaidCents());
        assertEquals(337, market.account(ISSUER).availableCashCents());
        assertEquals(5, market.feeTreasuryCents());
        assertConserved(market);
    }

    @Test
    void feeHistorySurvivesIncomingOrderBecomingResting() {
        FinancialMarket market = fundedMarket(1_000);
        market.submitLimit(ISSUER, COIN, Side.SELL, 1, 113);
        OrderView buy = market.submitLimit(BUYER, COIN, Side.BUY, 3, 113).order();
        assertEquals(1, buy.feePaidCents());
        market.submitLimit(ISSUER, COIN, Side.SELL, 1, 113);
        market.submitLimit(ISSUER, COIN, Side.SELL, 1, 113);
        assertEquals(2, market.order(buy.id()).feePaidCents());
        assertEquals(OrderStatus.FILLED, market.order(buy.id()).status());
        assertConserved(market);
    }

    @Test
    void priceImprovementReleasesOnlyExcessAndCancelReturnsUnspentReservation() {
        FinancialMarket market = fundedMarket(1_000);
        market.submitLimit(ISSUER, COIN, Side.SELL, 1, 100);
        OrderView buy = market.submitLimit(BUYER, COIN, Side.BUY, 4, 200).order();
        assertEquals(602, buy.reservedCashCents());
        assertEquals(297, market.account(BUYER).availableCashCents());
        market.cancel(BUYER, buy.id());
        assertEquals(899, market.account(BUYER).availableCashCents());
        assertEquals(0, market.account(BUYER).reservedCashCents());
        assertEquals(1, market.order(buy.id()).feePaidCents());
        assertEquals(2, market.feeTreasuryCents());
        assertConserved(market);
    }

    @Test
    void cancelUnfilledOrdersReturnsAllCashAndCoinsWithoutTradingFees() {
        FinancialMarket market = fundedMarket(1_000);
        OrderView buy = market.submitLimit(BUYER, COIN, Side.BUY, 1, 50).order();
        OrderView sell = market.submitLimit(ISSUER, COIN, Side.SELL, 2, 100).order();
        market.cancel(BUYER, buy.id());
        market.cancel(ISSUER, sell.id());
        assertEquals(1_000, market.account(BUYER).availableCashCents());
        assertEquals(new CoinBalance(1_000, 0), market.account(ISSUER).balance(COIN));
        assertEquals(0, market.feeTreasuryCents());
        assertConserved(market);
    }

    @Test
    void buyerCannotReservePrincipalWithoutItsFeeOrReuseAlreadyFrozenCash() {
        FinancialMarket market = fundedMarket(200);
        market.submitLimit(BUYER, COIN, Side.BUY, 1, 100);
        assertUnchangedOnFailure(market, MarketException.Code.INSUFFICIENT_CASH,
                () -> market.submitLimit(BUYER, COIN, Side.BUY, 1, 99));
        assertEquals(99, market.account(BUYER).availableCashCents());
        FinancialMarket exactPrincipalOnly = fundedMarket(100);
        assertUnchangedOnFailure(exactPrincipalOnly, MarketException.Code.INSUFFICIENT_CASH,
                () -> exactPrincipalOnly.submitLimit(BUYER, COIN, Side.BUY, 1, 100));
    }

    @Test
    void nakedSellingAndReusingFrozenCoinsAreRejected() {
        FinancialMarket market = fundedMarket(1_000);
        assertUnchangedOnFailure(market, MarketException.Code.INSUFFICIENT_COINS,
                () -> market.submitLimit(BUYER, COIN, Side.SELL, 1, 100));
        market.submitLimit(ISSUER, COIN, Side.SELL, 10, 100);
        assertUnchangedOnFailure(market, MarketException.Code.INSUFFICIENT_COINS,
                () -> market.submitLimit(ISSUER, COIN, Side.SELL, 1, 100));
        assertUnchangedOnFailure(market, MarketException.Code.INSUFFICIENT_COINS,
                () -> market.transferCoins(ISSUER, BUYER, COIN, 1));
    }

    @Test
    void sameBeneficiarySelfTradeRollsBackEvenEarlierExternalFillsInTheCommand() {
        FinancialMarket market = new FinancialMarket();
        market.createAccount(BUYER, new BeneficiaryId("shared-owner"), 1_000);
        market.createAccount(OTHER, new BeneficiaryId("shared-owner"), 0);
        account(market, ISSUER, 0);
        market.issueCoin(COIN, ISSUER, 1_000, 1_000, 0);
        market.transferCoins(ISSUER, OTHER, COIN, 100);
        market.submitLimit(ISSUER, COIN, Side.SELL, 1, 90);
        market.submitLimit(OTHER, COIN, Side.SELL, 1, 100);

        assertUnchangedOnFailure(market, MarketException.Code.SELF_TRADE,
                () -> market.submitLimit(BUYER, COIN, Side.BUY, 2, 100));
        assertTrue(market.snapshot().trades().isEmpty());
        assertEquals(0, market.feeTreasuryCents());
        assertConserved(market);
    }

    @Test
    void nonCrossingOrdersByOneBeneficiaryRemainPermitted() {
        FinancialMarket market = fundedMarket(1_000);
        market.transferCoins(ISSUER, BUYER, COIN, 100);
        market.submitLimit(BUYER, COIN, Side.SELL, 1, 200);
        SubmissionResult result = market.submitLimit(BUYER, COIN, Side.BUY, 1, 100);
        assertEquals(OrderStatus.OPEN, result.order().status());
        assertTrue(result.trades().isEmpty());
        assertConserved(market);
    }

    @Test
    void onlyOwnerCanCancelAndTerminalCancellationCannotReturnCashAgain() {
        FinancialMarket market = fundedMarket(1_000);
        OrderView buy = market.submitLimit(BUYER, COIN, Side.BUY, 1, 100).order();
        assertUnchangedOnFailure(market, MarketException.Code.NOT_OWNER,
                () -> market.cancel(ISSUER, buy.id()));
        market.cancel(BUYER, buy.id());
        assertUnchangedOnFailure(market, MarketException.Code.ORDER_NOT_OPEN,
                () -> market.cancel(BUYER, buy.id()));
    }

    @Test
    void coinMarketsAndTheirFrozenInventoriesDoNotCross() {
        FinancialMarket market = fundedMarket(1_000);
        market.issueCoin(SECOND, ISSUER, 500, 500, 0);
        OrderView sellA = market.submitLimit(ISSUER, COIN, Side.SELL, 1, 100).order();
        OrderView buyB = market.submitLimit(BUYER, SECOND, Side.BUY, 1, 100).order();
        assertEquals(OrderStatus.OPEN, market.order(sellA.id()).status());
        assertEquals(OrderStatus.OPEN, market.order(buyB.id()).status());
        assertTrue(market.snapshot().trades().isEmpty());
        market.submitLimit(ISSUER, SECOND, Side.SELL, 1, 100);
        assertEquals(0, market.account(BUYER).balance(COIN).totalCoins());
        assertEquals(100, market.account(BUYER).balance(SECOND).totalCoins());
        assertEquals(OrderStatus.OPEN, market.order(sellA.id()).status());
        assertConserved(market);
    }

    @Test
    void ordersOnDifferentCoinsStillShareOneRealWalletReservation() {
        FinancialMarket market = fundedMarket(200);
        market.issueCoin(SECOND, ISSUER, 500, 500, 0);
        market.submitLimit(BUYER, COIN, Side.BUY, 1, 100);
        assertEquals(99, market.account(BUYER).availableCashCents());
        assertUnchangedOnFailure(market, MarketException.Code.INSUFFICIENT_CASH,
                () -> market.submitLimit(BUYER, SECOND, Side.BUY, 1, 99));
        assertEquals(101, market.account(BUYER).reservedCashCents());
        assertConserved(market);
    }

    @Test
    void cancellingPartiallyFilledSellerReturnsOnlyItsUnfilledCoins() {
        FinancialMarket market = fundedMarket(1_000);
        OrderView sell = market.submitLimit(ISSUER, COIN, Side.SELL, 3, 113).order();
        market.submitLimit(BUYER, COIN, Side.BUY, 1, 113);
        market.cancel(ISSUER, sell.id());
        assertEquals(new CoinBalance(900, 0), market.account(ISSUER).balance(COIN));
        assertEquals(100, market.account(BUYER).balance(COIN).availableCoins());
        assertEquals(112, market.account(ISSUER).availableCashCents());
        assertEquals(1, market.order(sell.id()).feePaidCents());
        assertConserved(market);
    }

    @Test
    void sameDayAllowsSeveralTradesWhileRepeatedDayAdvanceDoesNothing() {
        FinancialMarket market = fundedMarket(1_000);
        assertTrue(market.advanceToDay(7).advanced());
        market.submitLimit(ISSUER, COIN, Side.SELL, 1, 100);
        market.submitLimit(BUYER, COIN, Side.BUY, 1, 100);
        market.submitLimit(ISSUER, COIN, Side.SELL, 1, 100);
        market.submitLimit(BUYER, COIN, Side.BUY, 1, 100);
        MarketSnapshot beforeRepeat = market.snapshot();
        assertFalse(market.advanceToDay(7).advanced());
        assertEquals(beforeRepeat, market.snapshot());
        assertEquals(2, market.snapshot().trades().size());
        assertTrue(market.snapshot().trades().stream().allMatch(trade -> trade.day() == 7));
        assertUnchangedOnFailure(market, MarketException.Code.DAY_REGRESSION,
                () -> market.advanceToDay(6));
    }

    @Test
    void invalidAndOverflowingOrdersLeaveAllStateAndSequencesUnchanged() {
        FinancialMarket market = fundedMarket(1_000);
        assertUnchangedOnFailure(market, MarketException.Code.INVALID_ARGUMENT,
                () -> market.submitLimit(BUYER, COIN, Side.BUY, 0, 100));
        assertUnchangedOnFailure(market, MarketException.Code.INVALID_ARGUMENT,
                () -> market.submitLimit(BUYER, COIN, Side.BUY, 1, -1));
        assertUnchangedOnFailure(market, MarketException.Code.ARITHMETIC_OVERFLOW,
                () -> market.submitLimit(BUYER, COIN, Side.BUY, Long.MAX_VALUE, 100));
        assertUnchangedOnFailure(market, MarketException.Code.COIN_NOT_FOUND,
                () -> market.submitLimit(BUYER, SECOND, Side.BUY, 1, 100));
        assertEquals(1, market.snapshot().nextOrderSequence());
    }

    @Test
    void snapshotsDoNotExposeMutableEngineState() {
        FinancialMarket market = fundedMarket(1_000);
        MarketSnapshot snapshot = market.snapshot();
        assertThrows(UnsupportedOperationException.class, () -> snapshot.accounts().clear());
        assertThrows(UnsupportedOperationException.class,
                () -> market.account(ISSUER).holdings().clear());
        market.transferCash(BUYER, ISSUER, 10);
        assertEquals(0, snapshot.accounts().getFirst().availableCashCents());
        assertEquals(1_000, snapshot.totalCashCents());
        assertConserved(market);
    }

    @Test
    void deterministicRandomCommandsPreserveCashCoinsAndFailureAtomicity() {
        FinancialMarket market = new FinancialMarket();
        List<AccountId> actors = new ArrayList<>();
        for (int i = 0; i < 6; i++) {
            AccountId id = new AccountId("actor-" + i);
            actors.add(id);
            account(market, id, 100_000);
        }
        market.issueCoin(COIN, actors.get(0), 12_000, 12_000, 17);
        market.issueCoin(SECOND, actors.get(0), 12_000, 12_000, 19);
        for (int i = 1; i < actors.size(); i++) {
            market.transferCoins(actors.get(0), actors.get(i), COIN, 2_000);
            market.transferCoins(actors.get(0), actors.get(i), SECOND, 2_000);
        }
        Random random = new Random(0x5EED_2026L);
        for (int step = 0; step < 600; step++) {
            MarketSnapshot before = market.snapshot();
            try {
                AccountId actor = actors.get(random.nextInt(actors.size()));
                if (random.nextInt(5) == 0 && !before.orders().isEmpty()) {
                    OrderView order = before.orders().get(random.nextInt(before.orders().size()));
                    market.cancel(actor, order.id());
                } else {
                    market.submitLimit(actor, random.nextBoolean() ? COIN : SECOND,
                            random.nextBoolean() ? Side.BUY : Side.SELL,
                            1 + random.nextInt(4), 1 + random.nextInt(200));
                }
            } catch (MarketException exception) {
                assertEquals(before, market.snapshot(), "rejected step " + step);
            }
            assertConserved(market);
            assertEquals(600_000, market.snapshot().totalCashCents());
            assertEquals(12_000, market.snapshot().totalCoins(COIN));
            assertEquals(12_000, market.snapshot().totalCoins(SECOND));
        }
        assertFalse(market.snapshot().trades().isEmpty());
    }

    private static FinancialMarket fundedMarket(long buyerCash) {
        FinancialMarket market = new FinancialMarket();
        account(market, ISSUER, 0);
        account(market, BUYER, buyerCash);
        market.issueCoin(COIN, ISSUER, 1_000, 2_000, 0);
        return market;
    }

    private static void account(FinancialMarket market, AccountId id, long cents) {
        market.createAccount(id, new BeneficiaryId("beneficiary-" + id.value()), cents);
    }

    private static void assertUnchangedOnFailure(FinancialMarket market, MarketException.Code expected,
                                                Runnable command) {
        MarketSnapshot before = market.snapshot();
        MarketException exception = assertThrows(MarketException.class, command::run);
        assertEquals(expected, exception.code());
        assertEquals(before, market.snapshot());
    }

    private static void assertConserved(FinancialMarket market) {
        MarketSnapshot snapshot = market.snapshot();
        assertEquals(snapshot.importedCashCents(), snapshot.totalCashCents());
        assertTrue(snapshot.feeTreasuryCents() >= 0);
        for (AccountView account : snapshot.accounts()) {
            assertTrue(account.availableCashCents() >= 0);
            assertTrue(account.reservedCashCents() >= 0);
            for (CoinBalance balance : account.holdings().values()) {
                assertTrue(balance.availableCoins() >= 0);
                assertTrue(balance.reservedCoins() >= 0);
            }
        }
        for (CoinView coin : snapshot.coins()) {
            assertEquals(coin.issuedCoins(), snapshot.totalCoins(coin.id()));
            assertTrue(coin.issuedCoins() <= coin.maxSupplyCoins());
        }
    }
}
