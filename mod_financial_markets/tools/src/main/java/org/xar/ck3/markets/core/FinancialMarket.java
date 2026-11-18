package org.xar.ck3.markets.core;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;

import static org.xar.ck3.markets.core.MarketException.Code;

/**
 * Deterministic financial reference core, not a CK3 runtime adapter.
 * Money is integer cents; a price is cents per lot of exactly 100 coins.
 * Each command stages all changes and publishes only after conservation checks.
 */
public final class FinancialMarket {
    public static final long COINS_PER_LOT = 100;

    private State state = new State();

    /** Imports one explicitly supplied world wallet. Trading and issuance never import cash. */
    public synchronized AccountView createAccount(AccountId id, BeneficiaryId beneficiaryId,
                                                   long openingCashCents) {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(beneficiaryId, "beneficiaryId");
        nonnegative(openingCashCents, "opening cash");
        return mutate(next -> {
            if (next.accounts.containsKey(id)) {
                throw failure(Code.ACCOUNT_EXISTS, "account already exists");
            }
            Account account = new Account(id, beneficiaryId, openingCashCents);
            next.accounts.put(id, account);
            next.importedCash = Math.addExact(next.importedCash, openingCashCents);
            return account.view();
        });
    }

    public synchronized CoinView issueCoin(CoinId coinId, AccountId issuerId, long initialSupplyCoins,
                                            long maxSupplyCoins, long feeCents) {
        Objects.requireNonNull(coinId, "coinId");
        Objects.requireNonNull(issuerId, "issuerId");
        positive(initialSupplyCoins, "initial supply");
        positive(maxSupplyCoins, "maximum supply");
        nonnegative(feeCents, "issuance fee");
        if (initialSupplyCoins > maxSupplyCoins) {
            throw failure(Code.SUPPLY_LIMIT, "initial supply exceeds finite cap");
        }
        return mutate(next -> {
            if (next.coins.containsKey(coinId)) {
                throw failure(Code.COIN_EXISTS, "coin ID cannot be reused");
            }
            Account issuer = account(next, issuerId);
            payFee(next, issuer, feeCents);
            CoinView coin = new CoinView(coinId, issuerId, initialSupplyCoins, maxSupplyCoins);
            next.coins.put(coinId, coin);
            issuer.holding(coinId).available = initialSupplyCoins;
            return coin;
        });
    }

    public synchronized CoinView mint(CoinId coinId, AccountId issuerId, long quantityCoins,
                                      long feeCents) {
        Objects.requireNonNull(coinId, "coinId");
        Objects.requireNonNull(issuerId, "issuerId");
        positive(quantityCoins, "mint quantity");
        nonnegative(feeCents, "mint fee");
        return mutate(next -> {
            CoinView previous = coin(next, coinId);
            if (!previous.issuerId().equals(issuerId)) {
                throw failure(Code.NOT_OWNER, "only the registered issuer may mint");
            }
            long issued = Math.addExact(previous.issuedCoins(), quantityCoins);
            if (issued > previous.maxSupplyCoins()) {
                throw failure(Code.SUPPLY_LIMIT, "finite issuance cap exceeded");
            }
            Account issuer = account(next, issuerId);
            payFee(next, issuer, feeCents);
            Holding holding = issuer.holding(coinId);
            holding.available = Math.addExact(holding.available, quantityCoins);
            CoinView updated = new CoinView(coinId, issuerId, issued, previous.maxSupplyCoins());
            next.coins.put(coinId, updated);
            return updated;
        });
    }

    public synchronized void transferCash(AccountId fromId, AccountId toId, long cents) {
        Objects.requireNonNull(fromId, "fromId");
        Objects.requireNonNull(toId, "toId");
        positive(cents, "transfer amount");
        mutate(next -> {
            Account from = account(next, fromId);
            Account to = account(next, toId);
            requireCash(from, cents);
            from.availableCash -= cents;
            to.availableCash = Math.addExact(to.availableCash, cents);
            return null;
        });
    }

    public synchronized void transferCoins(AccountId fromId, AccountId toId, CoinId coinId,
                                            long quantityCoins) {
        Objects.requireNonNull(fromId, "fromId");
        Objects.requireNonNull(toId, "toId");
        Objects.requireNonNull(coinId, "coinId");
        positive(quantityCoins, "transfer quantity");
        mutate(next -> {
            coin(next, coinId);
            Account from = account(next, fromId);
            Account to = account(next, toId);
            Holding origin = from.holding(coinId);
            if (origin.available < quantityCoins) {
                throw failure(Code.INSUFFICIENT_COINS, "not enough unreserved coins");
            }
            origin.available -= quantityCoins;
            Holding destination = to.holding(coinId);
            destination.available = Math.addExact(destination.available, quantityCoins);
            return null;
        });
    }

    public synchronized SubmissionResult submitLimit(AccountId ownerId, CoinId coinId, Side side,
                                                      long lots, long limitPriceCentsPerLot) {
        Objects.requireNonNull(ownerId, "ownerId");
        Objects.requireNonNull(coinId, "coinId");
        Objects.requireNonNull(side, "side");
        positive(lots, "lots");
        positive(limitPriceCentsPerLot, "limit price");
        return mutate(next -> {
            Account owner = account(next, ownerId);
            coin(next, coinId);
            long quantityCoins = Math.multiplyExact(lots, COINS_PER_LOT);
            long maxGross = Math.multiplyExact(lots, limitPriceCentsPerLot);
            OrderId orderId = new OrderId(next.nextOrder);
            next.nextOrder = Math.incrementExact(next.nextOrder);
            Order incoming = new Order(orderId, next.day, ownerId, coinId, side, lots,
                    limitPriceCentsPerLot);
            if (side == Side.BUY) {
                long reserve = Math.addExact(maxGross, TradingFees.cumulativeCents(maxGross));
                requireCash(owner, reserve);
                owner.availableCash -= reserve;
                owner.reservedCash = Math.addExact(owner.reservedCash, reserve);
                incoming.reservedCash = reserve;
            } else {
                Holding holding = owner.holding(coinId);
                if (holding.available < quantityCoins) {
                    throw failure(Code.INSUFFICIENT_COINS, "sell order must freeze real coins");
                }
                holding.available -= quantityCoins;
                holding.reserved = Math.addExact(holding.reserved, quantityCoins);
            }
            next.orders.put(orderId, incoming);
            List<Trade> executed = new ArrayList<>();
            while (incoming.remainingLots() > 0) {
                Order resting = bestOpposite(next, incoming);
                if (resting == null) {
                    break;
                }
                Account other = account(next, resting.owner);
                if (owner.beneficiary.equals(other.beneficiary)) {
                    throw failure(Code.SELF_TRADE, "same-beneficiary crossing rejects the entire command");
                }
                executed.add(execute(next, incoming, resting));
            }
            return new SubmissionResult(incoming.view(), executed);
        });
    }

    public synchronized OrderView cancel(AccountId ownerId, OrderId orderId) {
        Objects.requireNonNull(ownerId, "ownerId");
        Objects.requireNonNull(orderId, "orderId");
        return mutate(next -> {
            account(next, ownerId);
            Order order = order(next, orderId);
            if (!order.owner.equals(ownerId)) {
                throw failure(Code.NOT_OWNER, "only order owner may cancel");
            }
            if (!order.isOpen()) {
                throw failure(Code.ORDER_NOT_OPEN, "order is already terminal");
            }
            Account owner = account(next, ownerId);
            if (order.side == Side.BUY) {
                owner.reservedCash -= order.reservedCash;
                owner.availableCash = Math.addExact(owner.availableCash, order.reservedCash);
                order.reservedCash = 0;
            } else {
                long quantity = Math.multiplyExact(order.remainingLots(), COINS_PER_LOT);
                Holding holding = owner.holding(order.coin);
                holding.reserved -= quantity;
                holding.available = Math.addExact(holding.available, quantity);
            }
            order.status = OrderStatus.CANCELLED;
            return order.view();
        });
    }

    /** No settlement or interest is implemented. Repeating a day is a strict no-op. */
    public synchronized DayAdvanceResult advanceToDay(long day) {
        nonnegative(day, "day");
        if (day < state.day) {
            throw failure(Code.DAY_REGRESSION, "cannot move a live market backwards");
        }
        long previous = state.day;
        if (day == previous) {
            return new DayAdvanceResult(previous, day, false);
        }
        return mutate(next -> {
            next.day = day;
            return new DayAdvanceResult(previous, day, true);
        });
    }

    public synchronized long day() {
        return state.day;
    }

    public synchronized long feeTreasuryCents() {
        return state.feeTreasury;
    }

    public synchronized AccountView account(AccountId id) {
        return account(state, Objects.requireNonNull(id, "id")).view();
    }

    public synchronized CoinView coin(CoinId id) {
        return coin(state, Objects.requireNonNull(id, "id"));
    }

    public synchronized OrderView order(OrderId id) {
        return order(state, Objects.requireNonNull(id, "id")).view();
    }

    public synchronized MarketSnapshot snapshot() {
        return state.snapshot();
    }

    private <T> T mutate(Function<State, T> operation) {
        State next = new State(state);
        try {
            T result = operation.apply(next);
            validateConservation(next);
            state = next;
            return result;
        } catch (ArithmeticException exception) {
            throw failure(Code.ARITHMETIC_OVERFLOW, "operation exceeds integer accounting range");
        }
    }

    private static Trade execute(State next, Order incoming, Order resting) {
        Order buy = incoming.side == Side.BUY ? incoming : resting;
        Order sell = incoming.side == Side.SELL ? incoming : resting;
        Account buyer = account(next, buy.owner);
        Account seller = account(next, sell.owner);
        long lots = Math.min(incoming.remainingLots(), resting.remainingLots());
        long price = resting.price;
        long gross = Math.multiplyExact(lots, price);
        long quantity = Math.multiplyExact(lots, COINS_PER_LOT);
        long buyerFee = fill(buy, lots, gross);
        long sellerFee = fill(sell, lots, gross);
        long buyerDebit = Math.addExact(gross, buyerFee);
        buyer.reservedCash = Math.subtractExact(buyer.reservedCash, buyerDebit);
        buy.reservedCash = Math.subtractExact(buy.reservedCash, buyerDebit);
        seller.availableCash = Math.addExact(seller.availableCash, Math.subtractExact(gross, sellerFee));
        next.feeTreasury = Math.addExact(next.feeTreasury, Math.addExact(buyerFee, sellerFee));
        seller.holding(sell.coin).reserved = Math.subtractExact(seller.holding(sell.coin).reserved, quantity);
        buyer.holding(buy.coin).available = Math.addExact(buyer.holding(buy.coin).available, quantity);
        releaseBuyExcess(buyer, buy);
        long tradeId = next.nextTrade;
        next.nextTrade = Math.incrementExact(next.nextTrade);
        Trade trade = new Trade(tradeId, next.day, buy.coin, buy.id, sell.id, buy.owner, sell.owner,
                lots, price, gross, buyerFee, sellerFee);
        next.trades.add(trade);
        return trade;
    }

    private static long fill(Order order, long lots, long gross) {
        order.filled = Math.addExact(order.filled, lots);
        order.gross = Math.addExact(order.gross, gross);
        long cumulativeFee = TradingFees.cumulativeCents(order.gross);
        long deltaFee = Math.subtractExact(cumulativeFee, order.fee);
        order.fee = cumulativeFee;
        order.status = order.remainingLots() == 0 ? OrderStatus.FILLED : OrderStatus.PARTIALLY_FILLED;
        return deltaFee;
    }

    private static void releaseBuyExcess(Account buyer, Order buy) {
        long remainingGross = Math.multiplyExact(buy.remainingLots(), buy.price);
        long worstFinalGross = Math.addExact(buy.gross, remainingGross);
        long remainingFee = Math.subtractExact(TradingFees.cumulativeCents(worstFinalGross), buy.fee);
        long needed = Math.addExact(remainingGross, remainingFee);
        long release = Math.subtractExact(buy.reservedCash, needed);
        if (release < 0) {
            throw new IllegalStateException("buy reservation underfunded");
        }
        buy.reservedCash = needed;
        buyer.reservedCash -= release;
        buyer.availableCash = Math.addExact(buyer.availableCash, release);
    }

    private static Order bestOpposite(State next, Order incoming) {
        Order best = null;
        for (Order candidate : next.orders.values()) {
            if (!candidate.isOpen() || candidate.side == incoming.side || !candidate.coin.equals(incoming.coin)) {
                continue;
            }
            boolean crossing = incoming.side == Side.BUY
                    ? candidate.price <= incoming.price : candidate.price >= incoming.price;
            if (!crossing) {
                continue;
            }
            if (best == null || better(candidate, best, incoming.side)) {
                best = candidate;
            }
        }
        return best;
    }

    private static boolean better(Order candidate, Order best, Side incomingSide) {
        int priceComparison = Long.compare(candidate.price, best.price);
        if (priceComparison != 0) {
            return incomingSide == Side.BUY ? priceComparison < 0 : priceComparison > 0;
        }
        return candidate.id.value() < best.id.value();
    }

    private static void payFee(State next, Account payer, long cents) {
        requireCash(payer, cents);
        payer.availableCash -= cents;
        next.feeTreasury = Math.addExact(next.feeTreasury, cents);
    }

    private static void requireCash(Account account, long cents) {
        if (account.availableCash < cents) {
            throw failure(Code.INSUFFICIENT_CASH, "not enough unreserved real cash, including fees");
        }
    }

    private static Account account(State state, AccountId id) {
        Account account = state.accounts.get(id);
        if (account == null) {
            throw failure(Code.ACCOUNT_NOT_FOUND, "unknown account: " + id.value());
        }
        return account;
    }

    private static CoinView coin(State state, CoinId id) {
        CoinView coin = state.coins.get(id);
        if (coin == null) {
            throw failure(Code.COIN_NOT_FOUND, "unknown coin: " + id.value());
        }
        return coin;
    }

    private static Order order(State state, OrderId id) {
        Order order = state.orders.get(id);
        if (order == null) {
            throw failure(Code.ORDER_NOT_FOUND, "unknown order: " + id.value());
        }
        return order;
    }

    private static void positive(long value, String label) {
        if (value <= 0) {
            throw failure(Code.INVALID_ARGUMENT, label + " must be positive");
        }
    }

    private static void nonnegative(long value, String label) {
        if (value < 0) {
            throw failure(Code.INVALID_ARGUMENT, label + " cannot be negative");
        }
    }

    private static MarketException failure(Code code, String message) {
        return new MarketException(code, message);
    }

    private static void validateConservation(State next) {
        MarketSnapshot snapshot = next.snapshot();
        if (snapshot.totalCashCents() != next.importedCash) {
            throw new IllegalStateException("cash conservation failed");
        }
        for (Account account : next.accounts.values()) {
            if (account.availableCash < 0 || account.reservedCash < 0) {
                throw new IllegalStateException("negative cash");
            }
            for (Holding holding : account.holdings.values()) {
                if (holding.available < 0 || holding.reserved < 0) {
                    throw new IllegalStateException("negative coins");
                }
            }
        }
        for (CoinView coin : next.coins.values()) {
            if (snapshot.totalCoins(coin.id()) != coin.issuedCoins() || coin.issuedCoins() > coin.maxSupplyCoins()) {
                throw new IllegalStateException("coin conservation failed");
            }
        }
    }

    private static final class State {
        private long day;
        private long nextOrder = 1;
        private long nextTrade = 1;
        private long importedCash;
        private long feeTreasury;
        private final LinkedHashMap<AccountId, Account> accounts = new LinkedHashMap<>();
        private final LinkedHashMap<CoinId, CoinView> coins = new LinkedHashMap<>();
        private final LinkedHashMap<OrderId, Order> orders = new LinkedHashMap<>();
        private final ArrayList<Trade> trades = new ArrayList<>();

        private State() {
        }

        private State(State source) {
            day = source.day;
            nextOrder = source.nextOrder;
            nextTrade = source.nextTrade;
            importedCash = source.importedCash;
            feeTreasury = source.feeTreasury;
            source.accounts.forEach((id, account) -> accounts.put(id, new Account(account)));
            coins.putAll(source.coins);
            source.orders.forEach((id, order) -> orders.put(id, new Order(order)));
            trades.addAll(source.trades);
        }

        private MarketSnapshot snapshot() {
            return new MarketSnapshot(day, nextOrder, nextTrade, importedCash, feeTreasury,
                    accounts.values().stream().map(Account::view).toList(), List.copyOf(coins.values()),
                    orders.values().stream().map(Order::view).toList(), trades);
        }
    }

    private static final class Account {
        private final AccountId id;
        private final BeneficiaryId beneficiary;
        private long availableCash;
        private long reservedCash;
        private final LinkedHashMap<CoinId, Holding> holdings = new LinkedHashMap<>();

        private Account(AccountId id, BeneficiaryId beneficiary, long openingCash) {
            this.id = id;
            this.beneficiary = beneficiary;
            availableCash = openingCash;
        }

        private Account(Account source) {
            id = source.id;
            beneficiary = source.beneficiary;
            availableCash = source.availableCash;
            reservedCash = source.reservedCash;
            source.holdings.forEach((coin, holding) -> holdings.put(coin, new Holding(holding)));
        }

        private Holding holding(CoinId coin) {
            return holdings.computeIfAbsent(coin, ignored -> new Holding());
        }

        private AccountView view() {
            Map<CoinId, CoinBalance> balances = new LinkedHashMap<>();
            holdings.forEach((coin, holding) -> balances.put(coin, new CoinBalance(holding.available, holding.reserved)));
            return new AccountView(id, beneficiary, availableCash, reservedCash, balances);
        }
    }

    private static final class Holding {
        private long available;
        private long reserved;

        private Holding() {
        }

        private Holding(Holding source) {
            available = source.available;
            reserved = source.reserved;
        }
    }

    private static final class Order {
        private final OrderId id;
        private final long day;
        private final AccountId owner;
        private final CoinId coin;
        private final Side side;
        private final long lots;
        private final long price;
        private long filled;
        private long gross;
        private long fee;
        private long reservedCash;
        private OrderStatus status = OrderStatus.OPEN;

        private Order(OrderId id, long day, AccountId owner, CoinId coin, Side side, long lots, long price) {
            this.id = id;
            this.day = day;
            this.owner = owner;
            this.coin = coin;
            this.side = side;
            this.lots = lots;
            this.price = price;
        }

        private Order(Order source) {
            this(source.id, source.day, source.owner, source.coin, source.side, source.lots, source.price);
            filled = source.filled;
            gross = source.gross;
            fee = source.fee;
            reservedCash = source.reservedCash;
            status = source.status;
        }

        private long remainingLots() {
            return lots - filled;
        }

        private boolean isOpen() {
            return status == OrderStatus.OPEN || status == OrderStatus.PARTIALLY_FILLED;
        }

        private OrderView view() {
            return new OrderView(id, day, owner, coin, side, lots, filled, price, gross, fee, reservedCash, status);
        }
    }
}
