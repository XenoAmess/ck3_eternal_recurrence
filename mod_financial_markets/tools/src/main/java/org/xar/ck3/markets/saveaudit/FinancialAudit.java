package org.xar.ck3.markets.saveaudit;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.*;

/** Snapshot invariants only: no script/source marker or empty fixture can certify funds. */
public final class FinancialAudit {
    private FinancialAudit() { }
    private static final BigInteger HUNDRED = BigInteger.valueOf(100);
    public enum Assessment { VIOLATION, INCOMPLETE, CANDIDATE_INVARIANTS_HOLD }
    public record ExactTotal(boolean known, String cents) {
        public ExactTotal { if (known ? !cents.matches("-?(0|[1-9][0-9]*)") : !cents.isEmpty()) throw new IllegalArgumentException("exact known total or explicit unknown required"); }
    }
    public record Report(Assessment assessment, boolean financialCertified, ExactTotal ledgerCashStockCents,
                         int accountCount, int coinCount, int futuresPositionCount, int debtCount, List<Issue> issues) {
        public Report {
            if (financialCertified) throw new IllegalArgumentException("unqualified external candidate cannot certify live funds");
            issues = List.copyOf(issues);
        }
    }
    public record Difference(String identity, String detail) { }
    public record ColdComparison(boolean comparable, boolean exactSelectedFinancialState,
                                 boolean financialCertified, List<Difference> differences) {
        public ColdComparison {
            if (financialCertified) throw new IllegalArgumentException("cold comparison does not qualify candidate or funds");
            differences = List.copyOf(differences);
        }
    }

    public static Report audit(FinancialSnapshot snapshot) {
        List<Issue> issues = new ArrayList<>(snapshot.issues());
        Map<String, Story> byNative = new HashMap<>(); Set<String> permanent = new HashSet<>();
        for (Story story : snapshot.stories()) {
            if (byNative.putIfAbsent(story.nativeId().value(), story) != null) violation(issues, story, "native_id", "Duplicate native identity.");
            if (story.permanentId().isPresent() && !permanent.add(story.identity())) violation(issues, story, "permanent_id", "Duplicate permanent ID within its namespace.");
            required(story, issues);
            for (var entry : story.numbers().entrySet()) {
                if (!Set.of(NumberField.LAST_DAILY_DAY, NumberField.LAST_SETTLED_DAY, NumberField.LAST_FUNDING_DAY).contains(entry.getKey()) && entry.getValue().signum() < 0)
                    violation(issues, story, entry.getKey().wire(), "Negative financial quantity.");
            }
        }
        for (Story story : snapshot.stories()) {
            for (var entry : story.references().entrySet()) {
                if (entry.getKey().characterReference()) continue;
                Story target = byNative.get(entry.getValue().nativeId().value());
                // Destroyed zero reservations may be absent from old terminal history. Active obligations may not.
                if (target == null && activeObligation(story))
                    incomplete(issues, story, entry.getKey().wire(), "Active financial reference is unresolved in the complete selected story table.");
            }
            if (story.type() == Type.SPOT_POSITION) {
                greaterEqual(story, NumberField.QUANTITY_UNITS, NumberField.RESERVED_UNITS, issues);
                expectReferenceType(story, ReferenceField.ACCOUNT, Type.ACCOUNT, byNative, issues);
                expectReferenceType(story, ReferenceField.COIN, Type.COIN, byNative, issues);
            } else if (story.type() == Type.RESERVATION) {
                expectReferenceType(story, ReferenceField.ACCOUNT, Type.ACCOUNT, byNative, issues);
                if (is(story, NumberField.STATUS, 2) && story.number(NumberField.REMAINING_CENTS).filter(v -> v.signum() != 0).isPresent())
                    violation(issues, story, "remaining_cents", "Spent reservation retains money.");
            } else if (story.type() == Type.COIN) greaterEqual(story, NumberField.MAXIMUM_SUPPLY_UNITS, NumberField.SUPPLY_UNITS, issues);
            else if (story.type() == Type.FUTURES_POSITION) auditFuture(story, byNative, issues);
            else if (story.type() == Type.DEBT) auditDebt(story, byNative, issues);
        }
        auditReservations(snapshot.stories(), issues);
        auditSupply(snapshot.stories(), issues);
        auditSpotSales(snapshot.stories(), issues);
        auditOrderBacking(snapshot.stories(), byNative, issues);
        auditReservationExclusivity(snapshot.stories(), issues);
        auditPermanentHighWater(snapshot.stories(), issues);
        Set<String> settlementKeys = new HashSet<>();
        for (Story debt : of(snapshot.stories(), Type.DEBT)) {
            Optional<Reference> source = debt.reference(ReferenceField.SOURCE);
            Optional<BigInteger> day = debt.number(NumberField.SOURCE_DAY), kind = debt.number(NumberField.SOURCE_KIND);
            if (source.isPresent() && day.isPresent() && kind.isPresent()
                    && !settlementKeys.add(source.get().nativeId().value() + ':' + day.get() + ':' + kind.get()))
                violation(issues, debt, "source/day/kind", "Duplicate clearing identity creates multiple claims.");
        }
        Optional<BigInteger> cash = cash(snapshot.stories());
        Assessment assessment = issues.stream().anyMatch(i -> i.severity() == Severity.VIOLATION) ? Assessment.VIOLATION
                : issues.stream().anyMatch(i -> i.severity() == Severity.INCOMPLETE) ? Assessment.INCOMPLETE
                : Assessment.CANDIDATE_INVARIANTS_HOLD;
        return new Report(assessment, false, new ExactTotal(cash.isPresent(), cash.map(BigInteger::toString).orElse("")), of(snapshot.stories(), Type.ACCOUNT).size(),
                of(snapshot.stories(), Type.COIN).size(), of(snapshot.stories(), Type.FUTURES_POSITION).size(), of(snapshot.stories(), Type.DEBT).size(), issues);
    }

    /** This is specifically same-paused-state cold reload, not an equality test across trading days. */
    public static ColdComparison compareCold(FinancialSnapshot before, FinancialSnapshot after) {
        List<Difference> changes = new ArrayList<>();
        Report first = audit(before), second = audit(after);
        boolean comparable = before.machineId().equals(after.machineId()) && before.gameVersion().equals(after.gameVersion())
                && before.saveFormat().equals(after.saveFormat()) && before.gameDate().equals(after.gameDate())
                && first.assessment() == Assessment.CANDIDATE_INVARIANTS_HOLD && second.assessment() == Assessment.CANDIDATE_INVARIANTS_HOLD;
        if (!comparable) changes.add(new Difference("save", "Machine/version/format/date mismatch, incomplete projection, or invariant violation; equality is not certified."));
        Map<String, Story> old = identityMap(before.stories()), next = identityMap(after.stories());
        for (var entry : old.entrySet()) {
            Story other = next.get(entry.getKey());
            if (other == null) changes.add(new Difference(entry.getKey(), "Permanent/native financial identity disappeared."));
            else if (!entry.getValue().equals(other)) changes.add(new Difference(entry.getKey(), "Native ID, exact financial integer, legal holder, scope reference, or settlement journal changed."));
        }
        for (String identity : next.keySet()) if (!old.containsKey(identity)) changes.add(new Difference(identity, "New financial identity during same-state cold reload."));
        return new ColdComparison(comparable, comparable && changes.isEmpty(), false, changes);
    }

    private static void auditFuture(Story story, Map<String, Story> byNative, List<Issue> issues) {
        expectReferenceType(story, ReferenceField.CONTRACT, Type.FUTURES_CONTRACT, byNative, issues);
        Story contract = resolve(story, ReferenceField.CONTRACT, byNative);
        if (contract != null && story.number(NumberField.CONTRACT_ID).isPresent() && contract.number(NumberField.CONTRACT_ID).isPresent()
                && !story.number(NumberField.CONTRACT_ID).equals(contract.number(NumberField.CONTRACT_ID)))
            violation(issues, story, "contract_id", "Cached contract ID disagrees with its permanent contract.");
        if (is(story, NumberField.STATUS, 0) && story.number(NumberField.LOTS).filter(v -> v.signum() > 0).isPresent()) {
            Story longAccount = resolve(story, ReferenceField.LONG_ACCOUNT, byNative), shortAccount = resolve(story, ReferenceField.SHORT_ACCOUNT, byNative);
            if (longAccount != null && shortAccount != null && longAccount.nativeId().equals(shortAccount.nativeId()))
                violation(issues, story, "long/short", "Both obligations point to one account.");
            verifyPositionReservation(story, ReferenceField.LONG_ACCOUNT, ReferenceField.LONG_RESERVATION, byNative, issues);
            verifyPositionReservation(story, ReferenceField.SHORT_ACCOUNT, ReferenceField.SHORT_RESERVATION, byNative, issues);
            for (NumberField leverage : List.of(NumberField.LONG_LEVERAGE, NumberField.SHORT_LEVERAGE))
                story.number(leverage).filter(v -> !Set.of(BigInteger.ONE, BigInteger.TWO, BigInteger.valueOf(3), BigInteger.valueOf(5), BigInteger.TEN, BigInteger.valueOf(20)).contains(v))
                        .ifPresent(v -> violation(issues, story, leverage.wire(), "Unsupported leverage."));
        }
        if (is(story, NumberField.PENDING_PAYMENT, 1)) {
            requireNumbers(story, issues, NumberField.PENDING_AMOUNT, NumberField.PENDING_PAID, NumberField.PENDING_DAY, NumberField.PENDING_KIND, NumberField.PENDING_NEW_MARK);
            requireReferences(story, issues, ReferenceField.PENDING_DEBTOR, ReferenceField.PENDING_CREDITOR);
            greaterEqual(story, NumberField.PENDING_AMOUNT, NumberField.PENDING_PAID, issues);
        }
    }
    private static void verifyPositionReservation(Story position, ReferenceField accountField, ReferenceField reservationField,
                                                  Map<String, Story> byNative, List<Issue> issues) {
        expectReferenceType(position, accountField, Type.ACCOUNT, byNative, issues);
        expectReferenceType(position, reservationField, Type.RESERVATION, byNative, issues);
        Story reservation = resolve(position, reservationField, byNative);
        if (reservation != null && position.reference(accountField).isPresent() && reservation.reference(ReferenceField.ACCOUNT).isPresent()
                && !position.reference(accountField).orElseThrow().nativeId().equals(reservation.reference(ReferenceField.ACCOUNT).orElseThrow().nativeId()))
            violation(issues, position, reservationField.wire(), "Margin reservation belongs to a different account.");
    }
    private static void auditDebt(Story story, Map<String, Story> byNative, List<Issue> issues) {
        expectReferenceType(story, ReferenceField.DEBTOR_ACCOUNT, Type.ACCOUNT, byNative, issues);
        expectReferenceType(story, ReferenceField.CREDITOR_ACCOUNT, Type.ACCOUNT, byNative, issues);
        expectReferenceType(story, ReferenceField.SOURCE, Type.FUTURES_POSITION, byNative, issues);
        equalSum(story, NumberField.OUTSTANDING_CENTS, List.of(NumberField.WINNER_UNPAID_CENTS, NumberField.FUND_RECOURSE_CENTS), issues);
        equalSum(story, NumberField.ORIGINAL_CENTS, List.of(NumberField.OUTSTANDING_CENTS, NumberField.REPAID_CENTS, NumberField.WRITTEN_OFF_CENTS), issues);
        greaterEqual(story, NumberField.FUND_PAID_CENTS, NumberField.FUND_RECOURSE_CENTS, issues);
        if (story.number(NumberField.FUND_PAID_CENTS).filter(v -> v.signum() > 0).isPresent()) {
            requireReferences(story, issues, ReferenceField.FUND_ACCOUNT);
            expectReferenceType(story, ReferenceField.FUND_ACCOUNT, Type.ACCOUNT, byNative, issues);
        }
        if (is(story, NumberField.SOURCE_KIND, 2) && story.number(NumberField.FUND_PAID_CENTS).filter(v -> v.signum() != 0).isPresent())
            violation(issues, story, "fund_paid_cents", "Funding claim incorrectly insured.");
    }
    private static void auditReservations(List<Story> stories, List<Issue> issues) {
        boolean complete = of(stories, Type.RESERVATION).stream().allMatch(s -> s.number(NumberField.REMAINING_CENTS).isPresent() && s.reference(ReferenceField.ACCOUNT).isPresent());
        if (!complete) return;
        Map<String, BigInteger> totals = new HashMap<>();
        for (Story reservation : of(stories, Type.RESERVATION)) totals.merge(reservation.reference(ReferenceField.ACCOUNT).orElseThrow().nativeId().value(), reservation.number(NumberField.REMAINING_CENTS).orElseThrow(), BigInteger::add);
        for (Story account : of(stories, Type.ACCOUNT)) account.number(NumberField.RESERVED_CENTS).ifPresent(v -> {
            // Zero here is an empty exact sum, never a replacement for a missing serialized balance.
            if (!v.equals(totals.getOrDefault(account.nativeId().value(), BigInteger.ZERO))) violation(issues, account, "reserved_cents", "Account reserve differs from the sum of all surviving reservations.");
        });
    }
    private static void auditSupply(List<Story> stories, List<Issue> issues) {
        List<Story> positions = of(stories, Type.SPOT_POSITION);
        if (positions.stream().anyMatch(s -> s.number(NumberField.QUANTITY_UNITS).isEmpty() || s.reference(ReferenceField.COIN).isEmpty())) return;
        Map<String, BigInteger> supply = new HashMap<>(); Set<String> accountCoin = new HashSet<>();
        for (Story position : positions) {
            String coin = position.reference(ReferenceField.COIN).orElseThrow().nativeId().value();
            supply.merge(coin, position.number(NumberField.QUANTITY_UNITS).orElseThrow(), BigInteger::add);
            if (position.reference(ReferenceField.ACCOUNT).isPresent() && !accountCoin.add(position.reference(ReferenceField.ACCOUNT).orElseThrow().nativeId().value() + ':' + coin))
                violation(issues, position, "account/coin", "Duplicate spot holding for the same persistent account and coin.");
        }
        for (Story coin : of(stories, Type.COIN)) coin.number(NumberField.SUPPLY_UNITS).ifPresent(v -> {
            if (!v.equals(supply.getOrDefault(coin.nativeId().value(), BigInteger.ZERO))) violation(issues, coin, "supply_units", "Issued supply differs from the sum of all account holdings, including issuer/maker inventory.");
        });
    }
    private static void auditSpotSales(List<Story> stories, List<Issue> issues) {
        Map<String, BigInteger> sold = new HashMap<>();
        for (Story order : of(stories, Type.SPOT_ORDER)) {
            if (!is(order, NumberField.STATUS, 1) || !is(order, NumberField.SIDE, 2)) continue;
            if (order.reference(ReferenceField.SELL_POSITION).isEmpty() || order.number(NumberField.REMAINING_LOTS).isEmpty()) return;
            sold.merge(order.reference(ReferenceField.SELL_POSITION).orElseThrow().nativeId().value(), order.number(NumberField.REMAINING_LOTS).orElseThrow().multiply(HUNDRED), BigInteger::add);
        }
        for (Story position : of(stories, Type.SPOT_POSITION)) position.number(NumberField.RESERVED_UNITS).ifPresent(v -> {
            if (!v.equals(sold.getOrDefault(position.nativeId().value(), BigInteger.ZERO))) violation(issues, position, "reserved_units", "Coin freeze differs from active funded sell order lots times 100.");
        });
    }
    private static void auditOrderBacking(List<Story> stories, Map<String, Story> all, List<Issue> issues) {
        for (Story order : stories) {
            boolean spot = order.type() == Type.SPOT_ORDER;
            if (!spot && order.type() != Type.FUTURES_ORDER || !activeObligation(order)) continue;
            if (is(order, NumberField.SIDE, 1) || !spot) {
                requireReferences(order, issues, ReferenceField.RESERVATION);
                expectReferenceType(order, ReferenceField.RESERVATION, Type.RESERVATION, all, issues);
                Story reservation = resolve(order, ReferenceField.RESERVATION, all);
                if (reservation != null && order.reference(ReferenceField.ACCOUNT).isPresent() && reservation.reference(ReferenceField.ACCOUNT).isPresent()
                        && !order.reference(ReferenceField.ACCOUNT).orElseThrow().nativeId().equals(reservation.reference(ReferenceField.ACCOUNT).orElseThrow().nativeId()))
                    violation(issues, order, "reservation", "Order cash reservation belongs to another account.");
                if (spot && reservation != null && order.number(NumberField.REMAINING_LOTS).isPresent()
                        && order.number(NumberField.LIMIT_CENTS).isPresent() && order.number(NumberField.FILLED_NOTIONAL_CENTS).isPresent()
                        && order.number(NumberField.FEE_PAID_CENTS).isPresent() && reservation.number(NumberField.REMAINING_CENTS).isPresent()) {
                    BigInteger principal = order.number(NumberField.REMAINING_LOTS).orElseThrow().multiply(order.number(NumberField.LIMIT_CENTS).orElseThrow());
                    BigInteger fee = fee(principal.add(order.number(NumberField.FILLED_NOTIONAL_CENTS).orElseThrow())).subtract(order.number(NumberField.FEE_PAID_CENTS).orElseThrow());
                    if (fee.signum() < 0 || reservation.number(NumberField.REMAINING_CENTS).orElseThrow().compareTo(principal.add(fee)) < 0)
                        violation(issues, order, "reservation", "Buy order lacks limit principal plus remaining cumulative original-order fee.");
                }
            } else if (is(order, NumberField.SIDE, 2)) requireReferences(order, issues, ReferenceField.SELL_POSITION);
            NumberField gross = spot ? NumberField.FILLED_NOTIONAL_CENTS : NumberField.FILLED_GROSS_CENTS;
            if (order.number(gross).filter(v -> v.signum() > 0).isPresent() && order.number(NumberField.FEE_PAID_CENTS).isPresent()
                    && !fee(order.number(gross).orElseThrow()).equals(order.number(NumberField.FEE_PAID_CENTS).orElseThrow()))
                violation(issues, order, "fee_paid_cents", "Fee differs from 0.3% cumulative original-order gross, rounded up, minimum one cent.");
        }
    }
    private static BigInteger fee(BigInteger gross) { return gross.multiply(BigInteger.valueOf(3)).add(BigInteger.valueOf(999)).divide(BigInteger.valueOf(1000)).max(BigInteger.ONE); }
    private static void auditReservationExclusivity(List<Story> stories, List<Issue> issues) {
        Map<String, String> users = new HashMap<>();
        for (Story story : stories) {
            if (!activeObligation(story)) continue;
            List<ReferenceField> fields = switch (story.type()) {
                case SPOT_ORDER, FUTURES_ORDER -> List.of(ReferenceField.RESERVATION);
                case FUTURES_POSITION -> List.of(ReferenceField.LONG_RESERVATION, ReferenceField.SHORT_RESERVATION);
                default -> List.of();
            };
            for (ReferenceField field : fields) story.reference(field).ifPresent(reference -> {
                String previous = users.putIfAbsent(reference.nativeId().value(), story.identity() + ':' + field);
                if (previous != null) violation(issues, story, field.wire(), "Cash reservation already assigned to " + previous + '.');
            });
        }
    }
    private static void auditPermanentHighWater(List<Story> stories, List<Issue> issues) {
        List<Story> exchanges = of(stories, Type.EXCHANGE);
        if (exchanges.size() != 1) return;
        Map<Type, NumberField> counters = Map.of(Type.ACCOUNT, NumberField.NEXT_ACCOUNT_ID, Type.RESERVATION, NumberField.NEXT_RESERVATION_ID,
                Type.COIN, NumberField.NEXT_COIN_ID, Type.SPOT_ORDER, NumberField.NEXT_ORDER_ID, Type.FUTURES_ORDER, NumberField.NEXT_FUTURES_ORDER_ID,
                Type.FUTURES_CONTRACT, NumberField.NEXT_FUTURES_CONTRACT_ID, Type.FUTURES_POSITION, NumberField.NEXT_FUTURES_POSITION_ID, Type.DEBT, NumberField.DEBT_COUNTER);
        Story exchange = exchanges.getFirst();
        for (var entry : counters.entrySet()) {
            List<Story> members = of(stories, entry.getKey());
            if (members.isEmpty()) continue;
            Optional<BigInteger> high = exchange.number(entry.getValue());
            if (high.isEmpty()) { incomplete(issues, exchange, entry.getValue().wire(), "High-water counter missing for existing persistent identities."); continue; }
            for (Story member : members) if (member.permanentId().isPresent() && new BigInteger(member.permanentId().orElseThrow().value()).compareTo(high.get()) > 0)
                violation(issues, member, "permanent_id", "Permanent ID exceeds exchange high-water counter.");
        }
    }
    private static Optional<BigInteger> cash(List<Story> stories) {
        if (of(stories, Type.EXCHANGE).size() != 1 || of(stories, Type.ACCOUNT).isEmpty()) return Optional.empty();
        Story exchange = of(stories, Type.EXCHANGE).getFirst();
        if (exchange.number(NumberField.FEE_CENTS).isEmpty()) return Optional.empty();
        BigInteger cash = exchange.number(NumberField.FEE_CENTS).orElseThrow();
        for (Story account : of(stories, Type.ACCOUNT)) {
            if (account.number(NumberField.FREE_CENTS).isEmpty() || account.number(NumberField.RESERVED_CENTS).isEmpty()) return Optional.empty();
            cash = cash.add(account.number(NumberField.FREE_CENTS).orElseThrow()).add(account.number(NumberField.RESERVED_CENTS).orElseThrow());
        }
        return Optional.of(cash);
    }

    private static void required(Story s, List<Issue> issues) {
        switch (s.type()) {
            case EXCHANGE -> requireNumbers(s, issues, NumberField.DAY, NumberField.FEE_CENTS);
            case ACCOUNT -> { requireNumbers(s, issues, NumberField.FREE_CENTS, NumberField.RESERVED_CENTS); requireReferences(s, issues, ReferenceField.HOLDER); }
            case RESERVATION -> { requireNumbers(s, issues, NumberField.REMAINING_CENTS, NumberField.STATUS); requireReferences(s, issues, ReferenceField.ACCOUNT); }
            case COIN -> requireNumbers(s, issues, NumberField.SUPPLY_UNITS, NumberField.MAXIMUM_SUPPLY_UNITS);
            case SPOT_POSITION -> { requireNumbers(s, issues, NumberField.QUANTITY_UNITS, NumberField.RESERVED_UNITS); requireReferences(s, issues, ReferenceField.ACCOUNT, ReferenceField.COIN); }
            case SPOT_ORDER -> { requireNumbers(s, issues, NumberField.STATUS, NumberField.SIDE, NumberField.REMAINING_LOTS, NumberField.LIMIT_CENTS, NumberField.FEE_PAID_CENTS, NumberField.FILLED_NOTIONAL_CENTS); requireReferences(s, issues, ReferenceField.ACCOUNT, ReferenceField.COIN); }
            case FUTURES_CONTRACT -> { requireNumbers(s, issues, NumberField.CREATED_DAY, NumberField.PERPETUAL, NumberField.EXPIRY_DAY, NumberField.STATUS); requireReferences(s, issues, ReferenceField.COIN); }
            case FUTURES_ORDER -> { requireNumbers(s, issues, NumberField.STATUS, NumberField.SIDE, NumberField.REMAINING_LOTS, NumberField.LIMIT_CENTS, NumberField.FEE_PAID_CENTS, NumberField.FILLED_GROSS_CENTS); requireReferences(s, issues, ReferenceField.ACCOUNT, ReferenceField.CONTRACT); }
            case FUTURES_POSITION -> {
                requireNumbers(s, issues, NumberField.CONTRACT_ID, NumberField.CREATED_DAY, NumberField.LOTS, NumberField.MARK_CENTS, NumberField.STATUS, NumberField.LAST_SETTLED_DAY);
                requireReferences(s, issues, ReferenceField.CONTRACT, ReferenceField.COIN);
                if (is(s, NumberField.STATUS, 0)) { requireReferences(s, issues, ReferenceField.LONG_ACCOUNT, ReferenceField.SHORT_ACCOUNT, ReferenceField.LONG_RESERVATION, ReferenceField.SHORT_RESERVATION); requireNumbers(s, issues, NumberField.LONG_LEVERAGE, NumberField.SHORT_LEVERAGE); }
            }
            case DEBT -> {
                requireNumbers(s, issues, NumberField.SOURCE_DAY, NumberField.SOURCE_KIND, NumberField.ORIGINAL_CENTS, NumberField.OUTSTANDING_CENTS, NumberField.WINNER_UNPAID_CENTS, NumberField.FUND_PAID_CENTS, NumberField.FUND_RECOURSE_CENTS, NumberField.REPAID_CENTS, NumberField.WRITTEN_OFF_CENTS, NumberField.STATE);
                requireReferences(s, issues, ReferenceField.DEBTOR_ACCOUNT, ReferenceField.CREDITOR_ACCOUNT, ReferenceField.SOURCE);
            }
            case INDEX -> { }
        }
    }
    private static boolean activeObligation(Story s) {
        return switch (s.type()) {
            case ACCOUNT, COIN, SPOT_POSITION, DEBT, EXCHANGE, FUTURES_CONTRACT -> true;
            case RESERVATION -> s.number(NumberField.REMAINING_CENTS).filter(v -> v.signum() > 0).isPresent();
            case SPOT_ORDER -> is(s, NumberField.STATUS, 1);
            case FUTURES_ORDER -> is(s, NumberField.STATUS, 0) || is(s, NumberField.STATUS, 1);
            case FUTURES_POSITION -> is(s, NumberField.STATUS, 0) && s.number(NumberField.LOTS).filter(v -> v.signum() > 0).isPresent();
            case INDEX -> false;
        };
    }
    private static void requireNumbers(Story s, List<Issue> issues, NumberField... fields) { for (NumberField field : fields) if (s.number(field).isEmpty()) incomplete(issues, s, field.wire(), "Required explicit integer is absent or unrecognized; zero not inferred."); }
    private static void requireReferences(Story s, List<Issue> issues, ReferenceField... fields) { for (ReferenceField field : fields) if (s.reference(field).isEmpty()) incomplete(issues, s, field.wire(), "Required explicit scope reference is absent or unrecognized."); }
    private static boolean is(Story s, NumberField field, int value) { return s.number(field).filter(v -> v.equals(BigInteger.valueOf(value))).isPresent(); }
    private static List<Story> of(List<Story> all, Type type) { return all.stream().filter(s -> s.type() == type).toList(); }
    private static Map<String, Story> identityMap(List<Story> stories) { Map<String, Story> result = new HashMap<>(); for (Story s : stories) if (result.putIfAbsent(s.identity(), s) != null) throw new IllegalArgumentException("Duplicate identity cannot be cold-compared."); return result; }
    private static Story resolve(Story s, ReferenceField field, Map<String, Story> all) { return s.reference(field).map(r -> all.get(r.nativeId().value())).orElse(null); }
    private static void expectReferenceType(Story s, ReferenceField field, Type expected, Map<String, Story> all, List<Issue> issues) { Story target = resolve(s, field, all); if (target != null && target.type() != expected) violation(issues, s, field.wire(), "Scope resolves to wrong financial story type."); }
    private static void greaterEqual(Story s, NumberField left, NumberField right, List<Issue> issues) { if (s.number(left).isPresent() && s.number(right).isPresent() && s.number(left).orElseThrow().compareTo(s.number(right).orElseThrow()) < 0) violation(issues, s, left.wire(), "Less than " + right.wire() + '.'); }
    private static void equalSum(Story s, NumberField total, List<NumberField> parts, List<Issue> issues) { if (s.number(total).isEmpty() || parts.stream().anyMatch(f -> s.number(f).isEmpty())) return; BigInteger sum = parts.stream().map(f -> s.number(f).orElseThrow()).reduce(BigInteger.ZERO, BigInteger::add); if (!s.number(total).orElseThrow().equals(sum)) violation(issues, s, total.wire(), "Does not equal exact component sum."); }
    private static void incomplete(List<Issue> issues, Story s, String field, String detail) { issues.add(new Issue(Severity.INCOMPLETE, s.identity(), field, detail)); }
    private static void violation(List<Issue> issues, Story s, String field, String detail) { issues.add(new Issue(Severity.VIOLATION, s.identity(), field, detail)); }
}
