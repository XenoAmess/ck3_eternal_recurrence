package org.xar.ck3.control.governance.crownauthority;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Pure translation of the authored CA0-to-CA1 and CA1-to-CA2 selector. */
public final class CrownAuthorityPolicy {
    public static final String READ_SCHEMA = "realm-law-crown-action-private-read-v1";
    private static final BigInteger MAX_Q64 = BigInteger.valueOf(Long.MAX_VALUE);
    private static final BigInteger MIN_Q64 = BigInteger.valueOf(Long.MIN_VALUE);

    private CrownAuthorityPolicy() { }

    public enum Currency {
        GOLD("gold"), PRESTIGE("prestige"), PIETY("piety"), INFLUENCE("influence"), MERIT("merit");
        private final String wire;
        Currency(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Currency fromWire(String value) {
            for (Currency currency : values()) {
                if (currency.wire.equals(value)) { return currency; }
            }
            throw new IllegalArgumentException("unsupported Crown currency");
        }
    }

    public enum Status {
        UNAVAILABLE("unavailable"), NO_STOCK_UPGRADE("no_stock_upgrade"),
        NATIVE_BLOCKED("native_blocked"), RESOURCE_WAIT("resource_wait"), READY("ready");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** Native source identity is retained, but is not a future-frame authorization. */
    public record SourceFrame(BigInteger snapshotRevision, BigInteger nativeSnapshotRevision,
            BigInteger proofEpoch, BigInteger dateRaw, BigInteger playerCharacterId,
            String exactCk3Build, String exeSha256, String queriedSnapshotId,
            BigInteger queriedRevision, BigInteger queriedNativeRevision) {
        public SourceFrame {
            positive(snapshotRevision); positive(nativeSnapshotRevision); positive(proofEpoch);
            Objects.requireNonNull(dateRaw); positive(playerCharacterId); positive(queriedRevision);
            positive(queriedNativeRevision); text(exactCk3Build); text(exeSha256);
            if (queriedSnapshotId != null) { text(queriedSnapshotId); }
            require(snapshotRevision.equals(queriedNativeRevision), "queried and observed native frame differ");
            require(exeSha256.matches("[0-9A-Fa-f]{64}"), "exact executable SHA-256 required");
        }
    }

    public record Balance(Currency currency, BigInteger amountRaw) {
        public Balance { Objects.requireNonNull(currency); q64(amountRaw); }
    }

    public record Cost(Currency currency, BigInteger costRaw) {
        public Cost { Objects.requireNonNull(currency); q64(costRaw); nonnegative(costRaw); }
    }

    public record Candidate(String lawKey, boolean active, boolean engineFinalOnly,
            boolean canEnact, String blockedReason, List<Cost> costs) {
        public Candidate {
            text(lawKey); require(lawKey.startsWith("crown_authority_"), "Crown candidate key required");
            Objects.requireNonNull(blockedReason); costs = List.copyOf(costs);
            require(costs.size() <= 6, "bounded native costs required");
        }
    }

    public record HeldTitle(BigInteger titleId, boolean primary, List<BigInteger> successorCharacterIds) {
        public HeldTitle {
            positive(titleId); successorCharacterIds = List.copyOf(successorCharacterIds);
            require(successorCharacterIds.size() <= 32, "bounded successor list required");
            successorCharacterIds.forEach(CrownAuthorityPolicy::positive);
        }
    }

    public record TitleSuccessors(BigInteger primaryTitleId, List<HeldTitle> heldTitles) {
        public TitleSuccessors {
            positive(primaryTitleId); heldTitles = List.copyOf(heldTitles);
            require(!heldTitles.isEmpty() && heldTitles.size() <= 32, "bounded held titles required");
        }
    }

    public record Readback(String schema, boolean available, boolean paused, String groupKey,
            String activeLawKey, List<Candidate> candidates, List<Balance> resources,
            TitleSuccessors titleSuccessors, SourceFrame sourceFrame, boolean readOnly, boolean advertised) {
        public Readback {
            text(schema); text(groupKey); text(activeLawKey);
            candidates = List.copyOf(candidates); resources = List.copyOf(resources);
            Objects.requireNonNull(titleSuccessors); Objects.requireNonNull(sourceFrame);
            require(!candidates.isEmpty() && candidates.size() <= 24, "bounded candidates required");
            require(resources.size() == Currency.values().length, "all five native balances required");
            require(resources.stream().map(Balance::currency).distinct().count() == resources.size(),
                    "native currencies must occur once");
            List<String> active = candidates.stream().filter(Candidate::active).map(Candidate::lawKey).toList();
            require(active.equals(List.of(activeLawKey)), "native active law differs");
            require(readOnly && !advertised, "read-only private source required");
        }
    }

    /** Sorted JSON pair rows preserve the old dataclass's tuple/list representation. */
    public record CurrencyAmount(Currency currency, BigInteger amountRaw) {
        public CurrencyAmount { Objects.requireNonNull(currency); Objects.requireNonNull(amountRaw); }
    }

    public record Choice(Status status, String reason, String activeLawKey, String lawKey,
            List<CurrencyAmount> budgetsRaw, List<CurrencyAmount> quotedPostBalancesRaw) {
        public Choice {
            Objects.requireNonNull(status); text(reason);
            budgetsRaw = List.copyOf(budgetsRaw); quotedPostBalancesRaw = List.copyOf(quotedPostBalancesRaw);
            require(status == Status.READY || budgetsRaw.isEmpty() && quotedPostBalancesRaw.isEmpty(),
                    "only ready choices expose usable quote budgets");
        }
    }

    public static Choice choose(Readback readback) { return choose(readback, Map.of()); }

    /** Reserves use arbitrary precision integers, matching Python without narrowing arithmetic. */
    public static Choice choose(Readback readback, Map<Currency, BigInteger> reservesRaw) {
        Objects.requireNonNull(readback); Objects.requireNonNull(reservesRaw);
        Map<Currency, BigInteger> reserves = Map.copyOf(reservesRaw);
        reserves.values().forEach(CrownAuthorityPolicy::nonnegative);
        if (!READ_SCHEMA.equals(readback.schema()) || !readback.available() || !readback.paused()
                || !"crown_authority".equals(readback.groupKey())) {
            return result(Status.UNAVAILABLE, "formal_readback_unavailable", null, null);
        }
        String active = readback.activeLawKey();
        String target = switch (active) {
            case "crown_authority_0" -> "crown_authority_1";
            case "crown_authority_1" -> "crown_authority_2";
            default -> null;
        };
        if (target == null) {
            return result(Status.NO_STOCK_UPGRADE, "no_authored_positive_score", active, null);
        }
        Candidate candidate = readback.candidates().stream().filter(row -> row.lawKey().equals(target))
                .findFirst().orElse(null);
        if (candidate == null) {
            return result(Status.UNAVAILABLE, "target_candidate_unavailable", active, target);
        }
        if (candidate.active() || !candidate.canEnact()) {
            return result(Status.NATIVE_BLOCKED, candidate.blockedReason().isEmpty()
                    ? "native_final_can_enact_false" : candidate.blockedReason(), active, target);
        }
        EnumMap<Currency, BigInteger> balances = new EnumMap<>(Currency.class);
        readback.resources().forEach(row -> balances.put(row.currency(), row.amountRaw()));
        EnumMap<Currency, BigInteger> budgets = new EnumMap<>(Currency.class);
        candidate.costs().forEach(row -> budgets.merge(row.currency(), row.costRaw(), BigInteger::add));
        EnumMap<Currency, BigInteger> post = new EnumMap<>(Currency.class);
        for (Map.Entry<Currency, BigInteger> quote : budgets.entrySet()) {
            BigInteger amount = quote.getValue();
            BigInteger after = balances.get(quote.getKey()).subtract(amount);
            post.put(quote.getKey(), after);
            // A lawful zero cost does not gain an invented balance/reserve veto.
            if (amount.signum() > 0 && after.compareTo(reserves.getOrDefault(quote.getKey(), BigInteger.ZERO)) < 0) {
                return result(Status.RESOURCE_WAIT, "quoted_cost_exceeds_available_policy_balance", active, target);
            }
        }
        return new Choice(Status.READY, "authored_positive_score_and_native_final_permission", active, target,
                pairs(budgets), pairs(post));
    }

    private static List<CurrencyAmount> pairs(Map<Currency, BigInteger> values) {
        List<CurrencyAmount> rows = new ArrayList<>();
        values.forEach((currency, amount) -> rows.add(new CurrencyAmount(currency, amount)));
        rows.sort(Comparator.comparing(row -> row.currency().wire()));
        return List.copyOf(rows);
    }

    private static Choice result(Status status, String reason, String active, String target) {
        return new Choice(status, reason, active, target, List.of(), List.of());
    }

    static void positive(BigInteger value) { require(value != null && value.signum() > 0, "positive integer required"); }
    static void nonnegative(BigInteger value) { require(value != null && value.signum() >= 0, "nonnegative integer required"); }
    static void q64(BigInteger value) {
        require(value != null && value.compareTo(MIN_Q64) >= 0 && value.compareTo(MAX_Q64) <= 0,
                "native signed 64-bit quote required");
    }
    static void text(String value) { require(value != null && !value.isEmpty() && value.length() <= 32768, "bounded text required"); }
    static void require(boolean condition, String reason) {
        if (!condition) { throw new IllegalArgumentException(reason); }
    }
}
