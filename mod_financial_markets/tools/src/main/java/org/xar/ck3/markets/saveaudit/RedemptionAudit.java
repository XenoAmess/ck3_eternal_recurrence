package org.xar.ck3.markets.saveaudit;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.*;

/** Source-supported redemption identities and budget attribution; budgets are never cash stock. */
final class RedemptionAudit {
    private RedemptionAudit() { }
    private static final BigInteger HUNDRED = BigInteger.valueOf(100);

    static void required(Story s, List<Issue> issues) {
        if (s.type() == Type.REDEMPTION_WINDOW) {
            numbers(s, issues, NumberField.COIN_ID, NumberField.REDEMPTION_ACCOUNT_ID, NumberField.ISSUER_ACCOUNT_ID,
                    NumberField.PRICE_CENTS, NumberField.INITIAL_CENTS, NumberField.REMAINING_CENTS,
                    NumberField.PAID_CENTS, NumberField.PAID_UNITS, NumberField.RECLAIMED_CENTS,
                    NumberField.CREATED_DAY, NumberField.EXPIRY_DAY, NumberField.STATUS);
            references(s, issues, ReferenceField.COIN, ReferenceField.REDEMPTION_ACCOUNT, ReferenceField.ISSUER_ACCOUNT, ReferenceField.PUBLISHER);
        } else if (s.type() == Type.REDEMPTION_RECEIPT) {
            numbers(s, issues, NumberField.COIN_ID, NumberField.WINDOW_ID, NumberField.PAYER_ACCOUNT_ID, NumberField.PAYEE_ACCOUNT_ID,
                    NumberField.PAID_CENTS, NumberField.PAID_UNITS, NumberField.PRICE_CENTS,
                    NumberField.BUDGET_AFTER_CENTS, NumberField.DAY, NumberField.STATUS);
            references(s, issues, ReferenceField.COIN, ReferenceField.WINDOW, ReferenceField.PAYER_ACCOUNT,
                    ReferenceField.PAYEE_ACCOUNT, ReferenceField.HOLDER, ReferenceField.CONTROLLER);
        }
    }

    static void audit(List<Story> stories, Map<String, Story> all, List<Issue> issues) {
        List<Story> windows = of(stories, Type.REDEMPTION_WINDOW), receipts = of(stories, Type.REDEMPTION_RECEIPT);
        boolean receiptCensus = issues.stream().noneMatch(i -> i.severity() == Severity.INCOMPLETE && i.field().equals("story_cycle"))
                && receipts.stream().allMatch(r -> r.permanentId().isPresent() && have(r, NumberField.PAID_CENTS, NumberField.PAID_UNITS)
                        && r.reference(ReferenceField.WINDOW).isPresent() && r.reference(ReferenceField.COIN).isPresent());
        Map<String, List<Story>> byWindow = new HashMap<>(), byCoin = new HashMap<>(), windowsByCoin = new HashMap<>();
        for (Story w : windows) w.reference(ReferenceField.COIN).ifPresent(r -> windowsByCoin.computeIfAbsent(r.nativeId().value(), ignored -> new ArrayList<>()).add(w));
        for (Story receipt : receipts) {
            target(receipt, ReferenceField.WINDOW, Type.REDEMPTION_WINDOW, all, issues);
            receipt.reference(ReferenceField.WINDOW).ifPresent(r -> byWindow.computeIfAbsent(r.nativeId().value(), ignored -> new ArrayList<>()).add(receipt));
            receipt.reference(ReferenceField.COIN).ifPresent(r -> byCoin.computeIfAbsent(r.nativeId().value(), ignored -> new ArrayList<>()).add(receipt));
            auditReceipt(receipt, all, issues);
        }
        for (Story window : windows) auditWindow(window, byWindow.getOrDefault(window.nativeId().value(), List.of()), receiptCensus, all, issues);
        for (Story coin : of(stories, Type.COIN)) {
            List<Story> coinWindows = windowsByCoin.getOrDefault(coin.nativeId().value(), List.of());
            List<Story> coinReceipts = byCoin.getOrDefault(coin.nativeId().value(), List.of());
            if (!coinWindows.isEmpty() || coin.reference(ReferenceField.REDEMPTION_ACCOUNT).isPresent()
                    || coin.reference(ReferenceField.REDEMPTION_WINDOW).isPresent()) auditCoin(coin, coinWindows, coinReceipts, receiptCensus, all, issues);
            auditChain(coin, coinReceipts, all, issues);
        }
        for (Story a : of(stories, Type.ACCOUNT)) if (a.number(NumberField.REDEMPTION_ONLY).isPresent()) {
            references(a, issues, ReferenceField.LEGAL_ENTITY);
            Story coin = target(a, ReferenceField.LEGAL_ENTITY, Type.COIN, all, issues);
            if (coin != null) {
                account(a, a, coin, true, issues);
                references(coin, issues, ReferenceField.REDEMPTION_ACCOUNT);
                if (coin.reference(ReferenceField.REDEMPTION_ACCOUNT).isPresent() && !sameReference(coin, ReferenceField.REDEMPTION_ACCOUNT, a.nativeId().value()))
                    violation(issues, a, "redemption_only", "Dedicated system account is not the permanent coin's linked redemption account.");
            }
        }
    }

    private static void auditWindow(Story w, List<Story> receipts, boolean receiptCensus, Map<String, Story> all, List<Issue> issues) {
        Story coin = target(w, ReferenceField.COIN, Type.COIN, all, issues);
        Story escrow = target(w, ReferenceField.REDEMPTION_ACCOUNT, Type.ACCOUNT, all, issues);
        Story issuer = target(w, ReferenceField.ISSUER_ACCOUNT, Type.ACCOUNT, all, issues);
        cached(w, NumberField.COIN_ID, coin, NumberField.COIN_ID, issues);
        cached(w, NumberField.REDEMPTION_ACCOUNT_ID, escrow, NumberField.ACCOUNT_ID, issues);
        cached(w, NumberField.ISSUER_ACCOUNT_ID, issuer, NumberField.ACCOUNT_ID, issues);
        distinct(w, ReferenceField.REDEMPTION_ACCOUNT, ReferenceField.ISSUER_ACCOUNT, "Escrow and issuer must be different permanent accounts.", issues);
        if (coin != null) {
            same(w, ReferenceField.REDEMPTION_ACCOUNT, coin, ReferenceField.REDEMPTION_ACCOUNT, issues);
            same(w, ReferenceField.ISSUER_ACCOUNT, coin, ReferenceField.ISSUER_ACCOUNT, issues);
            if (coin.reference(ReferenceField.MARKET_MAKER_ACCOUNT).isPresent() && w.reference(ReferenceField.REDEMPTION_ACCOUNT).isPresent()
                    && coin.reference(ReferenceField.MARKET_MAKER_ACCOUNT).orElseThrow().nativeId().equals(w.reference(ReferenceField.REDEMPTION_ACCOUNT).orElseThrow().nativeId()))
                violation(issues, w, "redemption_account", "Dedicated escrow cannot be the coin's market-maker account.");
            if (escrow != null) account(w, escrow, coin, true, issues);
            if (issuer != null) account(w, issuer, coin, false, issues);
        }
        sum(w, NumberField.INITIAL_CENTS, List.of(NumberField.PAID_CENTS, NumberField.RECLAIMED_CENTS, NumberField.REMAINING_CENTS), issues);
        priceUnits(w, issues);
        range(w, NumberField.PRICE_CENTS, 1, 1000000, issues);
        range(w, NumberField.INITIAL_CENTS, 1, 100000000, issues);
        if (have(w, NumberField.CREATED_DAY, NumberField.EXPIRY_DAY)) {
            BigInteger duration = n(w, NumberField.EXPIRY_DAY).subtract(n(w, NumberField.CREATED_DAY));
            if (duration.signum() <= 0 || duration.compareTo(BigInteger.valueOf(90)) > 0) violation(issues, w, "expiry_day", "Window duration is outside the immutable published 1..90-day terms.");
        }
        if (w.number(NumberField.STATUS).isPresent() && !List.of(BigInteger.ONE, BigInteger.TWO, BigInteger.valueOf(4)).contains(n(w, NumberField.STATUS)))
            violation(issues, w, "status", "Unsupported redemption window status.");
        if (is(w, NumberField.STATUS, 2) && have(w, NumberField.REMAINING_CENTS, NumberField.PRICE_CENTS)
                && n(w, NumberField.REMAINING_CENTS).compareTo(n(w, NumberField.PRICE_CENTS)) >= 0)
            violation(issues, w, "remaining_cents", "Sold-out window retains at least one lot's budget.");
        if (is(w, NumberField.STATUS, 1) && have(w, NumberField.REMAINING_CENTS, NumberField.PRICE_CENTS)
                && n(w, NumberField.REMAINING_CENTS).compareTo(n(w, NumberField.PRICE_CENTS)) < 0)
            violation(issues, w, "status", "Window with less than one lot's budget must record sold-out status.");
        if (is(w, NumberField.STATUS, 4) && w.number(NumberField.REMAINING_CENTS).filter(v -> v.signum() != 0).isPresent())
            violation(issues, w, "remaining_cents", "Closed reclaimed window retains an unreturned budget.");
        if (receiptCensus) {
            aggregate(w, NumberField.PAID_CENTS, receipts, NumberField.PAID_CENTS, issues);
            aggregate(w, NumberField.PAID_UNITS, receipts, NumberField.PAID_UNITS, issues);
        }
        if (receiptCensus && receipts.stream().allMatch(r -> r.permanentId().isPresent() && have(r, NumberField.PAID_CENTS, NumberField.BUDGET_AFTER_CENTS))
                && w.number(NumberField.INITIAL_CENTS).isPresent()) {
            BigInteger balance = n(w, NumberField.INITIAL_CENTS);
            for (Story r : ordered(receipts)) {
                balance = balance.subtract(n(r, NumberField.PAID_CENTS));
                if (!balance.equals(n(r, NumberField.BUDGET_AFTER_CENTS))) violation(issues, r, "budget_after_cents", "Receipt order does not reproduce the funded window budget after each payment.");
            }
        }
    }

    private static void auditReceipt(Story r, Map<String, Story> all, List<Issue> issues) {
        Story coin = target(r, ReferenceField.COIN, Type.COIN, all, issues);
        Story w = target(r, ReferenceField.WINDOW, Type.REDEMPTION_WINDOW, all, issues);
        Story payer = target(r, ReferenceField.PAYER_ACCOUNT, Type.ACCOUNT, all, issues);
        Story payee = target(r, ReferenceField.PAYEE_ACCOUNT, Type.ACCOUNT, all, issues);
        cached(r, NumberField.COIN_ID, coin, NumberField.COIN_ID, issues);
        cached(r, NumberField.WINDOW_ID, w, NumberField.WINDOW_ID, issues);
        cached(r, NumberField.PAYER_ACCOUNT_ID, payer, NumberField.ACCOUNT_ID, issues);
        cached(r, NumberField.PAYEE_ACCOUNT_ID, payee, NumberField.ACCOUNT_ID, issues);
        distinct(r, ReferenceField.PAYER_ACCOUNT, ReferenceField.PAYEE_ACCOUNT, "Payer and paid party cannot be one account.", issues);
        distinct(r, ReferenceField.HOLDER, ReferenceField.CONTROLLER, "Recorded seller and recorded controller cannot be the same character.", issues);
        if (w != null) {
            same(r, ReferenceField.COIN, w, ReferenceField.COIN, issues);
            same(r, ReferenceField.PAYER_ACCOUNT, w, ReferenceField.REDEMPTION_ACCOUNT, issues);
            equal(r, NumberField.PRICE_CENTS, w, NumberField.PRICE_CENTS, issues);
            if (r.reference(ReferenceField.HOLDER).isPresent() && w.reference(ReferenceField.PUBLISHER).isPresent()
                    && r.reference(ReferenceField.HOLDER).orElseThrow().nativeId().equals(w.reference(ReferenceField.PUBLISHER).orElseThrow().nativeId()))
                violation(issues, r, "holder", "Window publisher cannot redeem through the external seller route.");
            if (have(r, NumberField.DAY) && have(w, NumberField.CREATED_DAY, NumberField.EXPIRY_DAY)
                    && (n(r, NumberField.DAY).compareTo(n(w, NumberField.CREATED_DAY)) < 0 || n(r, NumberField.DAY).compareTo(n(w, NumberField.EXPIRY_DAY)) >= 0))
                violation(issues, r, "day", "Payment is outside its published window's exact day interval.");
        }
        if (payee != null) {
            numbers(payee, issues, NumberField.SYSTEM_ACCOUNT);
            if (payee.number(NumberField.SYSTEM_ACCOUNT).filter(v -> v.signum() != 0).isPresent() || payee.reference(ReferenceField.LEGAL_ENTITY).isPresent())
                violation(issues, r, "payee_account", "Redemption seller must be a private account, not a project/system entity.");
        }
        if (coin != null && payer != null) account(r, payer, coin, true, issues);
        priceUnits(r, issues); range(r, NumberField.PAID_UNITS, 100, 10000, issues);
        range(r, NumberField.PAID_CENTS, 1, 100000000, issues);
        if (r.number(NumberField.STATUS).filter(v -> !v.equals(BigInteger.ONE)).isPresent()) violation(issues, r, "status", "Permanent receipt must record successful actual payment.");
    }

    private static void auditCoin(Story coin, List<Story> windows, List<Story> receipts, boolean receiptCensus, Map<String, Story> all, List<Issue> issues) {
        references(coin, issues, ReferenceField.REDEMPTION_ACCOUNT);
        Story escrow = target(coin, ReferenceField.REDEMPTION_ACCOUNT, Type.ACCOUNT, all, issues);
        if (escrow != null) account(coin, escrow, coin, true, issues);
        if (windows.isEmpty()) {
            // Account allocation may survive an unfunded publication attempt. No zero-window lifetime totals are invented.
            if (escrow != null && escrow.number(NumberField.FREE_CENTS).filter(v -> v.signum() != 0).isPresent()) violation(issues, coin, "redemption_account", "Escrow has cash without a funded permanent window.");
            return;
        }
        references(coin, issues, ReferenceField.REDEMPTION_WINDOW);
        numbers(coin, issues, NumberField.REDEMPTION_LIFETIME_PAID_CENTS, NumberField.REDEMPTION_LIFETIME_UNITS, NumberField.REDEMPTION_NEXT_PUBLISH_DAY);
        range(coin, NumberField.REDEMPTION_LIFETIME_PAID_CENTS, 0, 1000000000000L, issues);
        range(coin, NumberField.REDEMPTION_LIFETIME_UNITS, 0, 1000000000000L, issues);
        Story current = target(coin, ReferenceField.REDEMPTION_WINDOW, Type.REDEMPTION_WINDOW, all, issues);
        if (current != null) {
            if (!sameReference(current, ReferenceField.COIN, coin.nativeId().value())) violation(issues, coin, "redemption_window", "Current window belongs to another coin.");
            if (have(coin, NumberField.REDEMPTION_NEXT_PUBLISH_DAY) && have(current, NumberField.EXPIRY_DAY)
                    && !n(coin, NumberField.REDEMPTION_NEXT_PUBLISH_DAY).equals(n(current, NumberField.EXPIRY_DAY).add(BigInteger.valueOf(7))))
                violation(issues, coin, "redemption_next_publish_day", "Publication cooldown differs from current immutable expiry plus seven financial days.");
            if (escrow != null) equal(current, NumberField.REMAINING_CENTS, escrow, NumberField.FREE_CENTS, issues);
            for (Story old : windows) if (!old.nativeId().equals(current.nativeId())) {
                if (old.number(NumberField.REMAINING_CENTS).filter(v -> v.signum() != 0).isPresent()) violation(issues, old, "remaining_cents", "A superseded window retains budget in a reused escrow account.");
                if (have(old, NumberField.EXPIRY_DAY) && have(current, NumberField.CREATED_DAY)
                        && n(old, NumberField.EXPIRY_DAY).add(BigInteger.valueOf(7)).compareTo(n(current, NumberField.CREATED_DAY)) > 0)
                    violation(issues, old, "expiry_day", "A replacement was published before the old immutable expiry plus seven-day cooldown.");
                if (old.permanentId().isPresent() && current.permanentId().isPresent()
                        && id(old).compareTo(id(current)) >= 0) violation(issues, coin, "redemption_window", "Current pointer does not name the newest permanent window.");
            }
        }
        if (receiptCensus) {
            aggregate(coin, NumberField.REDEMPTION_LIFETIME_PAID_CENTS, receipts, NumberField.PAID_CENTS, issues);
            aggregate(coin, NumberField.REDEMPTION_LIFETIME_UNITS, receipts, NumberField.PAID_UNITS, issues);
        }
    }

    private static void auditChain(Story coin, List<Story> receipts, Map<String, Story> all, List<Issue> issues) {
        if (receipts.isEmpty()) {
            if (coin.reference(ReferenceField.REDEMPTION_LAST_RECEIPT).isPresent()) incomplete(issues, coin, "redemption_last_receipt", "Last receipt pointer has no surviving matching receipts.");
            return;
        }
        references(coin, issues, ReferenceField.REDEMPTION_LAST_RECEIPT);
        if (receipts.stream().anyMatch(r -> r.permanentId().isEmpty())) return;
        Story previous = null;
        for (Story r : ordered(receipts)) {
            if (previous == null) {
                if (r.reference(ReferenceField.PREVIOUS_RECEIPT).isPresent()) {
                    Story predecessor = target(r, ReferenceField.PREVIOUS_RECEIPT, Type.REDEMPTION_RECEIPT, all, issues);
                    if (predecessor != null) violation(issues, r, "previous_receipt", "First surviving receipt has an invalid predecessor, cycle, or foreign-coin chain.");
                }
            } else {
                references(r, issues, ReferenceField.PREVIOUS_RECEIPT);
                if (r.reference(ReferenceField.PREVIOUS_RECEIPT).isPresent() && !sameReference(r, ReferenceField.PREVIOUS_RECEIPT, previous.nativeId().value()))
                    violation(issues, r, "previous_receipt", "Per-coin predecessor differs from the prior globally ordered permanent receipt.");
                if (have(previous, NumberField.DAY) && have(r, NumberField.DAY) && n(previous, NumberField.DAY).compareTo(n(r, NumberField.DAY)) > 0)
                    violation(issues, r, "day", "Permanent receipt order goes backwards in financial day.");
            }
            previous = r;
        }
        if (previous != null && coin.reference(ReferenceField.REDEMPTION_LAST_RECEIPT).isPresent()
                && !sameReference(coin, ReferenceField.REDEMPTION_LAST_RECEIPT, previous.nativeId().value()))
            violation(issues, coin, "redemption_last_receipt", "Last pointer differs from the highest-ID receipt for the coin.");
    }

    private static void account(Story context, Story account, Story coin, boolean escrow, List<Issue> issues) {
        numbers(account, issues, NumberField.SYSTEM_ACCOUNT);
        references(account, issues, ReferenceField.LEGAL_ENTITY);
        if (account.number(NumberField.SYSTEM_ACCOUNT).filter(v -> !v.equals(BigInteger.ONE)).isPresent()) violation(issues, context, "system_account", "Redemption source account must be a system entity account.");
        if (account.reference(ReferenceField.LEGAL_ENTITY).isPresent() && !sameReference(account, ReferenceField.LEGAL_ENTITY, coin.nativeId().value())) violation(issues, context, "legal_entity", "System account belongs to another permanent coin.");
        if (escrow) {
            numbers(account, issues, NumberField.REDEMPTION_ONLY, NumberField.FREE_CENTS, NumberField.RESERVED_CENTS);
            if (account.number(NumberField.REDEMPTION_ONLY).filter(v -> !v.equals(BigInteger.ONE)).isPresent()) violation(issues, context, "redemption_only", "Escrow lacks its exclusive redemption purpose.");
            if (account.number(NumberField.RESERVED_CENTS).filter(v -> v.signum() != 0).isPresent()) violation(issues, context, "reserved_cents", "Dedicated redemption cash cannot also back reservations.");
        } else if (account.number(NumberField.REDEMPTION_ONLY).isPresent()) violation(issues, context, "issuer_account", "Issuer funding source cannot be the dedicated redemption account.");
    }
    private static void priceUnits(Story s, List<Issue> issues) {
        if (!have(s, NumberField.PAID_CENTS, NumberField.PAID_UNITS, NumberField.PRICE_CENTS)) return;
        BigInteger[] lots = n(s, NumberField.PAID_UNITS).divideAndRemainder(HUNDRED);
        if (lots[1].signum() != 0 || !lots[0].multiply(n(s, NumberField.PRICE_CENTS)).equals(n(s, NumberField.PAID_CENTS))) violation(issues, s, "paid_units/paid_cents", "Paid units are not whole 100-coin lots at the immutable window price.");
    }
    private static void aggregate(Story total, NumberField field, List<Story> members, NumberField part, List<Issue> issues) {
        if (total.number(field).isEmpty() || members.stream().anyMatch(r -> r.number(part).isEmpty())) return;
        BigInteger sum = members.stream().map(r -> n(r, part)).reduce(BigInteger.ZERO, BigInteger::add);
        if (!n(total, field).equals(sum)) violation(issues, total, field.wire(), "Cumulative payment differs from the exact surviving permanent receipt sum.");
    }
    private static void sum(Story s, NumberField total, List<NumberField> parts, List<Issue> issues) {
        if (s.number(total).isPresent() && parts.stream().allMatch(p -> s.number(p).isPresent())
                && !n(s, total).equals(parts.stream().map(p -> n(s, p)).reduce(BigInteger.ZERO, BigInteger::add))) violation(issues, s, total.wire(), "Posted budget must equal paid plus reclaimed plus remaining, without treating a budget as another wallet.");
    }
    private static void range(Story s, NumberField field, long low, long high, List<Issue> issues) {
        s.number(field).filter(v -> v.compareTo(BigInteger.valueOf(low)) < 0 || v.compareTo(BigInteger.valueOf(high)) > 0)
                .ifPresent(v -> violation(issues, s, field.wire(), "Value is outside its exact source-supported range."));
    }
    private static void equal(Story a, NumberField x, Story b, NumberField y, List<Issue> issues) {
        if (a.number(x).isPresent() && b.number(y).isPresent() && !a.number(x).equals(b.number(y))) violation(issues, a, x.wire(), "Exact value disagrees with " + b.identity() + '.' + y.wire());
    }
    private static void cached(Story s, NumberField cached, Story target, NumberField permanent, List<Issue> issues) { if (target != null) equal(s, cached, target, permanent, issues); }
    private static void same(Story a, ReferenceField x, Story b, ReferenceField y, List<Issue> issues) {
        references(b, issues, y);
        if (a.reference(x).isPresent() && b.reference(y).isPresent() && !a.reference(x).orElseThrow().nativeId().equals(b.reference(y).orElseThrow().nativeId())) violation(issues, a, x.wire(), "Reference disagrees with immutable linked financial identity.");
    }
    private static void distinct(Story s, ReferenceField a, ReferenceField b, String detail, List<Issue> issues) { if (s.reference(a).isPresent() && s.reference(b).isPresent() && s.reference(a).orElseThrow().nativeId().equals(s.reference(b).orElseThrow().nativeId())) violation(issues, s, a.wire(), detail); }
    private static Story target(Story s, ReferenceField field, Type type, Map<String, Story> all, List<Issue> issues) {
        Optional<Reference> ref = s.reference(field); if (ref.isEmpty()) return null;
        Story result = all.get(ref.orElseThrow().nativeId().value());
        if (result == null) { incomplete(issues, s, field.wire(), "Persistent redemption reference is unresolved in the complete financial census."); return null; }
        if (result.type() != type) { violation(issues, s, field.wire(), "Redemption reference resolves to the wrong story type."); return null; }
        return result;
    }
    private static boolean sameReference(Story s, ReferenceField f, String id) { return s.reference(f).map(r -> r.nativeId().value().equals(id)).orElse(false); }
    private static BigInteger id(Story s) { return new BigInteger(s.permanentId().orElseThrow().value()); }
    private static List<Story> ordered(List<Story> stories) { return stories.stream().sorted(Comparator.comparing(RedemptionAudit::id)).toList(); }
    private static BigInteger n(Story s, NumberField f) { return s.number(f).orElseThrow(); }
    private static boolean is(Story s, NumberField f, int value) { return s.number(f).map(v -> v.equals(BigInteger.valueOf(value))).orElse(false); }
    private static boolean have(Story s, NumberField... fields) { for (NumberField f : fields) if (s.number(f).isEmpty()) return false; return true; }
    private static List<Story> of(List<Story> all, Type type) { return all.stream().filter(s -> s.type() == type).toList(); }
    private static void numbers(Story s, List<Issue> issues, NumberField... fields) { for (NumberField f : fields) if (s.number(f).isEmpty()) incomplete(issues, s, f.wire(), "Required explicit redemption integer missing or unrecognized; zero is not inferred."); }
    private static void references(Story s, List<Issue> issues, ReferenceField... fields) { for (ReferenceField f : fields) if (s.reference(f).isEmpty()) incomplete(issues, s, f.wire(), "Required explicit redemption scope reference missing or unrecognized."); }
    private static void incomplete(List<Issue> issues, Story s, String field, String detail) { issues.add(new Issue(Severity.INCOMPLETE, s.identity(), field, detail)); }
    private static void violation(List<Issue> issues, Story s, String field, String detail) { issues.add(new Issue(Severity.VIOLATION, s.identity(), field, detail)); }
}
