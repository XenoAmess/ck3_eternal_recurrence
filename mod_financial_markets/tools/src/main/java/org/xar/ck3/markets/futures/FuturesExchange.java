package org.xar.ck3.markets.futures;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.markets.core.AccountId;
import org.xar.ck3.markets.core.BeneficiaryId;
import org.xar.ck3.markets.core.CoinId;
import org.xar.ck3.markets.core.FinancialMarket;
import org.xar.ck3.markets.core.LedgerBatch;
import org.xar.ck3.markets.core.TradingFees;
import org.xar.ck3.markets.debt.DebtLedger;
import org.xar.ck3.markets.debt.DebtLedger.CoverPlan;
import org.xar.ck3.markets.debt.DebtLedger.SettlementKey;
import org.xar.ck3.markets.debt.DebtLedger.SettlementKind;
import org.xar.ck3.markets.oracle.PriceOracle;
import org.xar.ck3.markets.oracle.PriceQuote;

/** Deterministic matched derivatives; every cash movement uses the shared spot wallet. */
public final class FuturesExchange {
    public enum Direction { LONG, SHORT;
        public Direction opposite() { return this == LONG ? SHORT : LONG; }
    }
    public enum Kind { DATED, PERPETUAL }
    public enum Status { OPEN, PARTIAL, FILLED, CANCELLED }
    public enum PositionStatus { OPEN, CLOSED, DEFAULTED }
    public record Contract(String id, CoinId coin, Kind kind, long expiryDay) {
        public Contract {
            identity(id); Objects.requireNonNull(coin); Objects.requireNonNull(kind);
            if (expiryDay < 0 || (kind == Kind.PERPETUAL && expiryDay != 0))
                throw new IllegalArgumentException("invalid contract expiry");
        }
    }
    public record OrderView(long id, String contractId, AccountId owner, Direction direction,
                            long originalLots, long remainingLots, long limitCents, int leverage,
                            long closePositionId, long grossCents, long feeCents,
                            AccountId escrow, long heldCents, Status status) { }
    public record PositionView(long id, String contractId, AccountId longAccount, AccountId shortAccount,
                               AccountId longEscrow, AccountId shortEscrow, long lots, long markCents,
                               int longLeverage, int shortLeverage, long lastDay,
                               long longStop, long longTakeProfit, long shortStop, long shortTakeProfit,
                               boolean longExitRequested, boolean shortExitRequested,
                               PositionStatus status) { }
    public record Fill(long sequence, long day, String contractId, long incomingOrder,
                       long restingOrder, long lots, long priceCents, long resultingPosition) { }
    public record Submission(OrderView order, List<Fill> fills) {
        public Submission { fills = List.copyOf(fills); }
    }
    public record DayResult(long day, boolean applied, int marked, int closed, int claims,
                            List<String> suspendedContracts) {
        public DayResult { suspendedContracts = List.copyOf(suspendedContracts); }
    }
    public record Snapshot(long day, long nextOrder, long nextPosition, long nextFill,
                           List<Contract> contracts, List<OrderView> orders,
                           List<PositionView> positions, List<Fill> fills) {
        public Snapshot {
            contracts = List.copyOf(contracts); orders = List.copyOf(orders);
            positions = List.copyOf(positions); fills = List.copyOf(fills);
        }
    }

    private final String id;
    private final FinancialMarket wallet;
    private final DebtLedger debts;
    private final AccountId fund;
    private final PriceOracle oracle;
    private State state = new State();

    public FuturesExchange(String id, FinancialMarket wallet, DebtLedger debts, AccountId fund, PriceOracle oracle) {
        identity(id);
        if (id.length() > 24) throw new IllegalArgumentException("exchange ID too long");
        this.id = id; this.wallet = Objects.requireNonNull(wallet);
        this.debts = Objects.requireNonNull(debts); this.fund = Objects.requireNonNull(fund);
        this.oracle = Objects.requireNonNull(oracle);
        wallet.account(fund);
        if (wallet.isEscrow(fund)) throw new IllegalArgumentException("fund must be an ordinary account");
    }

    public synchronized Contract register(Contract contract) {
        Objects.requireNonNull(contract);
        Contract old = state.contracts.get(contract.id());
        if (old != null) {
            if (!old.equals(contract)) throw new IllegalArgumentException("contract identity conflict");
            return old;
        }
        if (contract.kind() == Kind.DATED && contract.expiryDay() <= state.day)
            throw new IllegalArgumentException("contract has expired");
        State next = new State(state); next.contracts.put(contract.id(), contract); state = next;
        return contract;
    }

    private PriceQuote quote(Contract contract, long day) {
        PriceQuote quote = Objects.requireNonNull(oracle.quote(contract.coin().value(), day));
        if (!quote.assetId().equals(contract.coin().value()) || quote.day() != day)
            throw new IllegalArgumentException("oracle identity or publication day mismatch");
        return quote;
    }

    public synchronized Submission submit(AccountId owner, String contractId, Direction direction,
                                           long lots, long limitCents, int leverage) {
        return submitInternal(owner, contractId, direction, lots, limitCents, leverage, 0);
    }

    /** A reduction is an order to transfer actual open exposure to an independently funded trader. */
    public synchronized Submission reduce(AccountId owner, long positionId, long lots, long limitCents) {
        Position position = position(state, positionId); Direction holding = side(position, owner);
        if (lots > position.lots) throw new IllegalArgumentException("reduction exceeds position");
        for (Order order : state.orders.values()) {
            if (order.open() && order.closePosition == positionId && order.owner.equals(owner))
                throw new IllegalArgumentException("position already has a reduction order");
        }
        return submitInternal(owner, position.contract, holding.opposite(), lots, limitCents, 1, positionId);
    }

    private Submission submitInternal(AccountId owner, String contractId, Direction direction,
                                      long lots, long limitCents, int leverage, long closePosition) {
        Objects.requireNonNull(owner); Objects.requireNonNull(direction); positive(lots); positive(limitCents);
        allowedLeverage(leverage);
        synchronized (wallet) { synchronized (debts) {
            Contract contract = contract(state, contractId); rejectFund(owner);
            if (wallet.isEscrow(owner)) throw new IllegalArgumentException("escrow cannot trade");
            PriceQuote oracle = quote(contract, state.day);
            if (closePosition == 0) {
                for (var debt : debts.snapshot().debts()) {
                    if (debt.outstandingCents() > 0 && beneficiary(debt.debtor()).equals(beneficiary(owner)))
                        throw new IllegalArgumentException("unresolved debt blocks new leveraged exposure");
                }
                if (!oracle.qualified() || leverage > oracle.maxLeverage())
                    throw new IllegalArgumentException("qualified independent spot oracle required");
                if (contract.kind() == Kind.DATED && contract.expiryDay() <= state.day)
                    throw new IllegalArgumentException("contract has expired");
                if (limitCents < floorRatio(oracle.markCents(), 80, 100)
                        || limitCents > ceilRatio(oracle.markCents(), 120, 100))
                    throw new IllegalArgumentException("order outside oracle risk band");
            }
            State next = new State(state); Work work = new Work(next, "cmd." + next.nextCommand++);
            try {
                maintainBooks(work, Map.of(contractId, oracle));
                long orderId = next.nextOrder++;
                AccountId escrow = escrow("o", orderId, ""); work.create(escrow, owner);
                Order incoming = new Order(orderId, contractId, owner, direction, lots, limitCents,
                        leverage, closePosition, escrow);
                long maxPrice = closePosition == 0 ? Math.max(limitCents,
                        ceilRatio(oracle.markCents(), 120, 100)) : limitCents;
                incoming.reservePrice = maxPrice;
                long gross = Math.multiplyExact(lots, maxPrice);
                long reserve = TradingFees.cumulativeCents(gross);
                if (closePosition == 0) reserve = Math.addExact(reserve, ceilRatio(gross, 1, leverage));
                work.move(owner, escrow, reserve); next.orders.put(orderId, incoming);
                List<Fill> fills = new ArrayList<>();
                while (incoming.remaining > 0) {
                    Order resting = best(next, incoming);
                    if (resting == null) break;
                    if (beneficiary(owner).equals(beneficiary(resting.owner)))
                        throw new IllegalArgumentException("same-beneficiary crossing rejects entire command");
                    fills.add(execute(work, incoming, resting));
                }
                Submission result = new Submission(incoming.view(work.balance(incoming.escrow)), fills);
                work.commit(); return result;
            } catch (RuntimeException exception) { work.abort(); throw exception; }
        } }
    }

    public synchronized OrderView cancel(AccountId owner, long orderId) {
        synchronized (wallet) { synchronized (debts) {
            State next = new State(state); Order order = order(next, orderId);
            if (!order.owner.equals(owner) || !order.open()) throw new IllegalArgumentException("order not cancellable");
            Work work = new Work(next, "cmd." + next.nextCommand++);
            work.move(order.escrow, owner, work.balance(order.escrow)); order.status = Status.CANCELLED;
            OrderView result = order.view(0); work.commit(); return result;
        } }
    }

    public synchronized void addMargin(AccountId owner, long positionId, long cents) {
        changeMargin(owner, positionId, cents, false);
    }
    public synchronized void withdrawMargin(AccountId owner, long positionId, long cents) {
        changeMargin(owner, positionId, cents, true);
    }
    private void changeMargin(AccountId owner, long positionId, long cents, boolean withdrawal) {
        positive(cents);
        synchronized (wallet) { synchronized (debts) {
            State next = new State(state); Position p = position(next, positionId);
            Direction direction = side(p, owner); AccountId escrow = p.escrow(direction);
            Work work = new Work(next, "cmd." + next.nextCommand++);
            if (withdrawal) {
                PriceQuote quote = quote(contract(next, p.contract), next.day);
                if (!quote.qualified() || p.lastDay != next.day)
                    throw new IllegalArgumentException("fresh settled mark required for withdrawal");
                long required = ceilRatio(Math.multiplyExact(p.lots, p.mark), 1, p.leverage(direction));
                if (work.balance(escrow) - cents < required)
                    throw new IllegalArgumentException("withdrawal breaches initial margin");
                work.move(escrow, owner, cents);
            } else work.move(owner, escrow, cents);
            work.commit();
        } }
    }

    public synchronized void setStops(AccountId owner, long positionId, long stop, long takeProfit) {
        if (stop < 0 || takeProfit < 0) throw new IllegalArgumentException("negative trigger");
        State next = new State(state); Position p = position(next, positionId);
        if (side(p, owner) == Direction.LONG) { p.longStop = stop; p.longTake = takeProfit; }
        else { p.shortStop = stop; p.shortTake = takeProfit; }
        state = next;
    }

    /** Marks exactly once per day. Missing oracle suspends expiry, new risk and funding rather than inventing a price. */
    public synchronized DayResult advanceDay(long day) {
        if (day < state.day) throw new IllegalArgumentException("day regression");
        if (day == state.day && state.lastDaily == day) return new DayResult(day, false, 0, 0, 0, List.of());
        synchronized (wallet) { synchronized (debts) {
            State next = new State(state); next.day = day;
            Work work = new Work(next, "day." + day); List<String> suspended = new ArrayList<>();
            int marked = 0; int closed = 0;
            try {
                Map<String, PriceQuote> quotes = new HashMap<>();
                for (Contract contract : next.contracts.values()) {
                    PriceQuote quote = quote(contract, day); quotes.put(contract.id(), quote);
                    if (!quote.qualified()) suspended.add(contract.id());
                }
                maintainBooks(work, quotes);
                for (Position p : next.positions.values()) {
                    if (p.status != PositionStatus.OPEN || p.lastDay >= day) continue;
                    PriceQuote quote = quotes.get(p.contract); if (!quote.qualified()) continue;
                    Contract contract = contract(next, p.contract);
                    if (contract.kind() == Kind.DATED && day >= contract.expiryDay() && !quote.terminationEligible()) {
                        if (!suspended.contains(p.contract)) suspended.add(p.contract);
                        continue;
                    }
                    SettlementKind kind = contract.kind() == Kind.DATED && day >= contract.expiryDay()
                            ? SettlementKind.EXPIRY : SettlementKind.VARIATION;
                    settle(work, p, quote.markCents(), kind); p.lastDay = day; marked++;
                    if (p.status == PositionStatus.DEFAULTED || kind == SettlementKind.EXPIRY) {
                        close(work, p); closed++; continue;
                    }
                    if (contract.kind() == Kind.PERPETUAL) funding(work, p, quote.indexCents());
                    if (p.status == PositionStatus.DEFAULTED) { close(work, p); closed++; continue; }
                    long notional = Math.multiplyExact(p.lots, p.mark);
                    boolean under = work.balance(p.longEscrow) < maintenance(notional, p.longLeverage)
                            || work.balance(p.shortEscrow) < maintenance(notional, p.shortLeverage);
                    if (under) {
                        p.longExit |= work.balance(p.longEscrow) < maintenance(notional, p.longLeverage);
                        p.shortExit |= work.balance(p.shortEscrow) < maintenance(notional, p.shortLeverage);
                    }
                    p.longExit |= triggered(p, Direction.LONG); p.shortExit |= triggered(p, Direction.SHORT);
                }
                // Snapshot avoids invalidating iteration when genuine executions novate positions.
                for (Position p : new ArrayList<>(next.positions.values())) {
                    if (p.status != PositionStatus.OPEN) continue;
                    PriceQuote quote = quotes.get(p.contract); if (!quote.qualified()) continue;
                    if (p.longExit) postExit(work, p, Direction.LONG, quote);
                    if (p.status == PositionStatus.OPEN && p.shortExit) postExit(work, p, Direction.SHORT, quote);
                }
                next.lastDaily = day;
                DayResult result = new DayResult(day, true, marked, closed, work.covers.size(), suspended);
                work.commit(); return result;
            } catch (RuntimeException exception) { work.abort(); throw exception; }
        } }
    }

    public synchronized Snapshot snapshot() {
        List<OrderView> orders = state.orders.values().stream().map(o -> o.view(wallet.account(o.escrow).availableCashCents())).toList();
        return new Snapshot(state.day, state.nextOrder, state.nextPosition, state.nextFill,
                new ArrayList<>(state.contracts.values()), orders,
                state.positions.values().stream().map(Position::view).toList(), state.fills);
    }

    private Fill execute(Work work, Order incoming, Order resting) {
        long lots = Math.min(incoming.remaining, resting.remaining); long price = resting.price;
        long gross = Math.multiplyExact(lots, price);
        Order buy = incoming.direction == Direction.LONG ? incoming : resting;
        Order sell = incoming.direction == Direction.SHORT ? incoming : resting;
        // A reduction can only consume its still-owned, unreserved original exposure.
        Position originalLong = buy.closePosition == 0 ? null : position(work.next, buy.closePosition);
        Position originalShort = sell.closePosition == 0 ? null : position(work.next, sell.closePosition);
        if (originalLong != null && (!originalLong.shortAccount.equals(buy.owner) || lots > originalLong.lots))
            throw new IllegalArgumentException("short reduction no longer owned");
        if (originalShort != null && (!originalShort.longAccount.equals(sell.owner) || lots > originalShort.lots))
            throw new IllegalArgumentException("long reduction no longer owned");
        Position fromLong = originalLong == null ? null : extractSlice(work, originalLong, lots);
        Position fromShort = originalShort == null ? null : originalShort == originalLong ? fromLong : extractSlice(work, originalShort, lots);
        long newId = work.next.nextPosition++;
        AccountId longEscrow = escrow("p", newId, "l"); AccountId shortEscrow = escrow("p", newId, "s");
        AccountId longOwner = fromLong == null ? buy.owner : fromLong.longAccount;
        AccountId shortOwner = fromShort == null ? sell.owner : fromShort.shortAccount;
        if (beneficiary(longOwner).equals(beneficiary(shortOwner)))
            throw new IllegalArgumentException("novation creates related opposing exposure");
        work.create(longEscrow, longOwner); work.create(shortEscrow, shortOwner);
        int longLev = fromLong == null ? buy.leverage : fromLong.longLeverage;
        int shortLev = fromShort == null ? sell.leverage : fromShort.shortLeverage;
        if (fromLong != null && fromLong == fromShort) {
            settle(work, fromLong, price, SettlementKind.LIQUIDATION);
            releaseSlice(work, fromLong, lots, null, null); // both actual counterparties close
        } else {
            if (fromLong != null) {
                settle(work, fromLong, price, SettlementKind.LIQUIDATION);
                releaseSlice(work, fromLong, lots, longEscrow, null);
            } else work.move(buy.escrow, longEscrow, ceilRatio(gross, 1, buy.leverage));
            if (fromShort != null) {
                settle(work, fromShort, price, SettlementKind.LIQUIDATION);
                releaseSlice(work, fromShort, lots, null, shortEscrow);
            } else work.move(sell.escrow, shortEscrow, ceilRatio(gross, 1, sell.leverage));
            Position paired = new Position(newId, incoming.contract, longOwner, shortOwner,
                    longEscrow, shortEscrow, lots, price, longLev, shortLev, work.next.day);
            work.next.positions.put(newId, paired);
        }
        fillOrder(work, incoming, lots, gross); fillOrder(work, resting, lots, gross);
        Fill fill = new Fill(work.next.nextFill++, work.next.day, incoming.contract,
                incoming.id, resting.id, lots, price, fromLong != null && fromLong == fromShort ? 0 : newId);
        work.next.fills.add(fill); work.next.lastFuturesPrice.put(incoming.contract, price); return fill;
    }

    private void maintainBooks(Work work, Map<String, PriceQuote> quotes) {
        for (Order order : work.next.orders.values()) {
            if (!order.open() || !quotes.containsKey(order.contract)) continue;
            if (order.closePosition != 0) {
                Position original = work.next.positions.get(order.closePosition);
                if (original == null || original.status != PositionStatus.OPEN) {
                    work.move(order.escrow, order.owner, work.balance(order.escrow)); order.status = Status.CANCELLED;
                } else if (order.remaining > original.lots) {
                    order.remaining = original.lots;
                    long remainingGross = Math.multiplyExact(order.remaining, order.reservePrice);
                    long fee = TradingFees.cumulativeCents(Math.addExact(order.gross, remainingGross)) - order.fee;
                    work.move(order.escrow, order.owner, work.balance(order.escrow) - fee);
                }
                continue;
            }
            PriceQuote quote = quotes.get(order.contract); Contract contract = contract(work.next, order.contract);
            boolean expired = contract.kind() == Kind.DATED && work.next.day >= contract.expiryDay();
            boolean stale = !quote.qualified() || order.leverage > quote.maxLeverage() || expired;
            if (!stale) stale = order.price < floorRatio(quote.markCents(), 80, 100)
                    || order.price > ceilRatio(quote.markCents(), 120, 100);
            if (stale) {
                work.move(order.escrow, order.owner, work.balance(order.escrow)); order.status = Status.CANCELLED;
            }
        }
    }

    private Position extractSlice(Work work, Position original, long lots) {
        long sliceId = work.next.nextPosition++;
        AccountId longEscrow = escrow("slice", sliceId, "l"); AccountId shortEscrow = escrow("slice", sliceId, "s");
        work.create(longEscrow, original.longAccount); work.create(shortEscrow, original.shortAccount);
        long longPart = floorRatio(work.balance(original.longEscrow), lots, original.lots);
        long shortPart = floorRatio(work.balance(original.shortEscrow), lots, original.lots);
        work.move(original.longEscrow, longEscrow, longPart); work.move(original.shortEscrow, shortEscrow, shortPart);
        Position slice = new Position(sliceId, original.contract, original.longAccount, original.shortAccount,
                longEscrow, shortEscrow, lots, original.mark, original.longLeverage, original.shortLeverage, original.lastDay);
        work.next.positions.put(sliceId, slice);
        original.lots -= lots; if (original.lots == 0) original.status = PositionStatus.CLOSED;
        return slice;
    }

    private void postExit(Work work, Position p, Direction holding, PriceQuote quote) {
        for (Order order : work.next.orders.values())
            if (order.open() && order.closePosition == p.id && order.owner.equals(p.account(holding))) {
                work.move(order.escrow, order.owner, work.balance(order.escrow)); order.status = Status.CANCELLED;
            }
        long upper = ceilRatio(quote.markCents(), 120, 100);
        long fee = TradingFees.cumulativeCents(Math.multiplyExact(p.lots, upper));
        AccountId owner = p.account(holding);
        AccountId source = work.balance(owner) >= fee ? owner : p.escrow(holding);
        if (work.balance(source) < fee) return; // honest illiquidity: retain exit request, no invented proceeds
        long orderId = work.next.nextOrder++; AccountId escrow = escrow("o", orderId, "");
        work.create(escrow, owner); work.move(source, escrow, fee);
        Order exit = new Order(orderId, p.contract, owner, holding.opposite(), p.lots,
                holding == Direction.LONG ? 1 : upper, 1, p.id, escrow);
        exit.reservePrice = upper; work.next.orders.put(orderId, exit);
        while (exit.remaining > 0) {
            Order resting = best(work.next, exit); if (resting == null) break;
            // Automatic orders cancel the offending resting order instead of washing against it.
            if (beneficiary(owner).equals(beneficiary(resting.owner))) {
                work.move(resting.escrow, resting.owner, work.balance(resting.escrow)); resting.status = Status.CANCELLED;
                continue;
            }
            execute(work, exit, resting);
        }
        // A market exit never becomes a resting maker at its extreme protective limit.
        if (exit.open()) {
            work.move(exit.escrow, exit.owner, work.balance(exit.escrow)); exit.status = Status.CANCELLED;
        }
    }

    private void releaseSlice(Work work, Position p, long lots, AccountId retainLong, AccountId retainShort) {
        long longPart = floorRatio(work.balance(p.longEscrow), lots, p.lots);
        long shortPart = floorRatio(work.balance(p.shortEscrow), lots, p.lots);
        work.move(p.longEscrow, retainLong == null ? p.longAccount : retainLong, longPart);
        work.move(p.shortEscrow, retainShort == null ? p.shortAccount : retainShort, shortPart);
        p.lots -= lots; if (p.lots == 0 && p.status != PositionStatus.DEFAULTED) p.status = PositionStatus.CLOSED;
    }
    private void fillOrder(Work work, Order order, long lots, long gross) {
        order.remaining -= lots; order.gross = Math.addExact(order.gross, gross);
        long totalFee = TradingFees.cumulativeCents(order.gross);
        long deltaFee = totalFee - order.fee; order.fee = totalFee; work.fee(order.escrow, deltaFee);
        order.status = order.remaining == 0 ? Status.FILLED : Status.PARTIAL;
        long remainingGross = Math.multiplyExact(order.remaining, order.reservePrice);
        long required = TradingFees.cumulativeCents(Math.addExact(order.gross, remainingGross)) - order.fee;
        if (order.closePosition == 0) required = Math.addExact(required, ceilRatio(remainingGross, 1, order.leverage));
        long release = work.balance(order.escrow) - required;
        if (release < 0) throw new IllegalArgumentException("order margin or fee reservation exhausted");
        work.move(order.escrow, order.owner, release);
    }
    private void settle(Work work, Position p, long price, SettlementKind kind) {
        long delta = Math.multiplyExact(Math.subtractExact(price, p.mark), p.lots);
        if (delta != 0) pay(work, p, delta > 0 ? Direction.SHORT : Direction.LONG,
                Math.absExact(delta), kind);
        p.mark = price;
    }
    private void funding(Work work, Position p, long index) {
        // Completed-day real volume, rather than the last microscopic print, sets the premium.
        long volume = 0; long lots = 0;
        for (Fill fill : work.next.fills) {
            if (!fill.contractId().equals(p.contract) || fill.day() != work.next.day - 1) continue;
            volume = Math.addExact(volume, Math.multiplyExact(fill.lots(), fill.priceCents()));
            lots = Math.addExact(lots, fill.lots());
        }
        if (volume < 10_000 || lots < 10) return;
        long future = volume / lots;
        long premiumBps = Math.multiplyExact(Math.subtractExact(future, index), 10_000) / index;
        long rate = Math.max(-10, Math.min(10, premiumBps)); // at most 0.10% daily
        long amount = floorRatio(Math.multiplyExact(p.lots, index), Math.abs(rate), 10_000);
        if (amount > 0) pay(work, p, rate > 0 ? Direction.LONG : Direction.SHORT, amount, SettlementKind.FUNDING);
    }
    private void pay(Work work, Position p, Direction loser, long amount, SettlementKind kind) {
        AccountId from = p.escrow(loser); AccountId debtor = p.account(loser);
        AccountId winner = p.account(loser.opposite());
        long paid = Math.min(amount, work.balance(from)); work.move(from, winner, paid);
        long shortfall = amount - paid;
        if (shortfall > 0) {
            CoverPlan plan = debts.prepareCover(new SettlementKey(id + ".p." + p.id, work.next.day, kind),
                    debtor, winner, fund, shortfall, wallet.account(fund).availableCashCents());
            work.covers.add(plan);
            for (var payment : plan.transfers()) work.move(payment.from(), payment.to(), payment.cents());
            p.status = PositionStatus.DEFAULTED;
        }
    }
    private void close(Work work, Position p) {
        work.move(p.longEscrow, p.longAccount, work.balance(p.longEscrow));
        work.move(p.shortEscrow, p.shortAccount, work.balance(p.shortEscrow));
        if (p.status != PositionStatus.DEFAULTED) p.status = PositionStatus.CLOSED;
        for (Order order : work.next.orders.values()) {
            if (order.closePosition == p.id && order.open()) {
                work.move(order.escrow, order.owner, work.balance(order.escrow)); order.status = Status.CANCELLED;
            }
        }
    }
    private static boolean triggered(Position p, Direction side) {
        if (side == Direction.LONG) return (p.longStop > 0 && p.mark <= p.longStop)
                || (p.longTake > 0 && p.mark >= p.longTake);
        return (p.shortStop > 0 && p.mark >= p.shortStop) || (p.shortTake > 0 && p.mark <= p.shortTake);
    }
    private BeneficiaryId beneficiary(AccountId account) { return wallet.account(account).beneficiaryId(); }
    private void rejectFund(AccountId owner) {
        if (beneficiary(owner).equals(beneficiary(fund)))
            throw new IllegalArgumentException("default fund or its controller cannot speculate");
    }
    private AccountId escrow(String kind, long number, String suffix) {
        return new AccountId("xfm.escrow." + id + "." + kind + number + suffix);
    }
    private static long maintenance(long notional, int leverage) {
        return ceilRatio(notional, 60, Math.multiplyExact(leverage, 100));
    }
    private static long ceilRatio(long value, long numerator, long denominator) {
        long multiplied = Math.multiplyExact(value, numerator);
        return multiplied / denominator + (multiplied % denominator == 0 ? 0 : 1);
    }
    private static long floorRatio(long value, long numerator, long denominator) {
        return Math.multiplyExact(value, numerator) / denominator;
    }
    private static void positive(long value) { if (value <= 0) throw new IllegalArgumentException("positive value required"); }
    private static void identity(String value) {
        if (value == null || !value.matches("[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}"))
            throw new IllegalArgumentException("invalid stable identity");
    }
    private static void allowedLeverage(int leverage) {
        if (leverage != 1 && leverage != 2 && leverage != 3 && leverage != 5 && leverage != 10 && leverage != 20)
            throw new IllegalArgumentException("unsupported leverage");
    }
    private static Contract contract(State state, String id) {
        Contract value = state.contracts.get(id); if (value == null) throw new IllegalArgumentException("unknown contract"); return value;
    }
    private static Position position(State state, long id) {
        Position value = state.positions.get(id);
        if (value == null || value.status != PositionStatus.OPEN) throw new IllegalArgumentException("position is not open"); return value;
    }
    private static Order order(State state, long id) {
        Order value = state.orders.get(id); if (value == null) throw new IllegalArgumentException("unknown order"); return value;
    }
    private static Direction side(Position position, AccountId owner) {
        if (position.longAccount.equals(owner)) return Direction.LONG;
        if (position.shortAccount.equals(owner)) return Direction.SHORT;
        throw new IllegalArgumentException("not position owner");
    }
    private static Order best(State state, Order incoming) {
        Order best = null;
        for (Order order : state.orders.values()) {
            if (!order.open() || order == incoming || !order.contract.equals(incoming.contract)
                    || order.direction == incoming.direction) continue;
            if (incoming.direction == Direction.LONG ? order.price > incoming.price : order.price < incoming.price) continue;
            if (best == null || (incoming.direction == Direction.LONG ? order.price < best.price : order.price > best.price)
                    || (order.price == best.price && order.id < best.id)) best = order;
        }
        return best;
    }

    private final class Work {
        private final State next;
        private final String batchId;
        private final List<LedgerBatch.CreateEscrow> creates = new ArrayList<>();
        private final List<LedgerBatch.Transfer> transfers = new ArrayList<>();
        private final List<LedgerBatch.Fee> fees = new ArrayList<>();
        private final List<CoverPlan> covers = new ArrayList<>();
        private final Map<AccountId, Long> balances = new HashMap<>();
        Work(State next, String operation) { this.next = next; batchId = id + "." + operation; }
        long balance(AccountId account) { return balances.computeIfAbsent(account, key -> wallet.account(key).availableCashCents()); }
        void create(AccountId escrow, AccountId owner) {
            creates.add(new LedgerBatch.CreateEscrow(escrow, owner)); balances.put(escrow, 0L);
        }
        void move(AccountId from, AccountId to, long cents) {
            if (cents == 0) return;
            if (from.equals(to)) return;
            if (cents < 0 || balance(from) < cents) throw new IllegalArgumentException("insufficient real margin or wallet cash");
            long target = Math.addExact(balance(to), cents); balances.put(from, balance(from) - cents); balances.put(to, target);
            transfers.add(new LedgerBatch.Transfer(from, to, cents));
        }
        void fee(AccountId from, long cents) {
            if (cents == 0) return;
            if (cents < 0 || balance(from) < cents) throw new IllegalArgumentException("unfunded fee");
            balances.put(from, balance(from) - cents); fees.add(new LedgerBatch.Fee(from, cents));
        }
        void commit() {
            // Batch and all externally visible results have already been constructed before this point.
            LedgerBatch batch = new LedgerBatch(batchId, creates, transfers, fees);
            wallet.applyBatch(batch);
            for (CoverPlan plan : covers) debts.commitCover(plan);
            state = next;
        }
        void abort() { for (CoverPlan plan : covers) debts.abortCover(plan); }
    }
    private static final class State {
        long day; long lastDaily = -1; long nextOrder = 1; long nextPosition = 1; long nextFill = 1; long nextCommand = 1;
        final Map<String, Contract> contracts = new LinkedHashMap<>();
        final Map<Long, Order> orders = new LinkedHashMap<>();
        final Map<Long, Position> positions = new LinkedHashMap<>();
        final Map<String, Long> lastFuturesPrice = new LinkedHashMap<>();
        final List<Fill> fills = new ArrayList<>();
        State() { }
        State(State old) {
            day = old.day; lastDaily = old.lastDaily; nextOrder = old.nextOrder; nextPosition = old.nextPosition;
            nextFill = old.nextFill; nextCommand = old.nextCommand; contracts.putAll(old.contracts);
            old.orders.forEach((key, value) -> orders.put(key, new Order(value)));
            old.positions.forEach((key, value) -> positions.put(key, new Position(value)));
            lastFuturesPrice.putAll(old.lastFuturesPrice); fills.addAll(old.fills);
        }
    }
    private static final class Order {
        final long id; final String contract; final AccountId owner; final Direction direction;
        final long lots; final long price; final int leverage; final long closePosition; final AccountId escrow;
        long remaining; long gross; long fee; long reservePrice; Status status = Status.OPEN;
        Order(long id, String contract, AccountId owner, Direction direction, long lots, long price,
              int leverage, long closePosition, AccountId escrow) {
            this.id = id; this.contract = contract; this.owner = owner; this.direction = direction;
            this.lots = lots; this.price = price; this.leverage = leverage; this.closePosition = closePosition;
            this.escrow = escrow; remaining = lots;
        }
        Order(Order old) {
            this(old.id, old.contract, old.owner, old.direction, old.lots, old.price, old.leverage, old.closePosition, old.escrow);
            remaining = old.remaining; gross = old.gross; fee = old.fee; reservePrice = old.reservePrice; status = old.status;
        }
        boolean open() { return status == Status.OPEN || status == Status.PARTIAL; }
        OrderView view(long held) { return new OrderView(id, contract, owner, direction, lots, remaining,
                price, leverage, closePosition, gross, fee, escrow, held, status); }
    }
    private static final class Position {
        final long id; final String contract; final AccountId longAccount; final AccountId shortAccount;
        final AccountId longEscrow; final AccountId shortEscrow; final int longLeverage; final int shortLeverage;
        long lots; long mark; long lastDay; long longStop; long longTake; long shortStop; long shortTake;
        boolean longExit; boolean shortExit; PositionStatus status = PositionStatus.OPEN;
        Position(long id, String contract, AccountId longAccount, AccountId shortAccount,
                 AccountId longEscrow, AccountId shortEscrow, long lots, long mark,
                 int longLeverage, int shortLeverage, long day) {
            this.id = id; this.contract = contract; this.longAccount = longAccount; this.shortAccount = shortAccount;
            this.longEscrow = longEscrow; this.shortEscrow = shortEscrow; this.lots = lots; this.mark = mark;
            this.longLeverage = longLeverage; this.shortLeverage = shortLeverage; lastDay = day;
        }
        Position(Position old) {
            this(old.id, old.contract, old.longAccount, old.shortAccount, old.longEscrow, old.shortEscrow,
                    old.lots, old.mark, old.longLeverage, old.shortLeverage, old.lastDay);
            longStop = old.longStop; longTake = old.longTake; shortStop = old.shortStop; shortTake = old.shortTake;
            longExit = old.longExit; shortExit = old.shortExit; status = old.status;
        }
        AccountId account(Direction side) { return side == Direction.LONG ? longAccount : shortAccount; }
        AccountId escrow(Direction side) { return side == Direction.LONG ? longEscrow : shortEscrow; }
        int leverage(Direction side) { return side == Direction.LONG ? longLeverage : shortLeverage; }
        PositionView view() { return new PositionView(id, contract, longAccount, shortAccount, longEscrow, shortEscrow,
                lots, mark, longLeverage, shortLeverage, lastDay, longStop, longTake, shortStop, shortTake,
                longExit, shortExit, status); }
    }
}
