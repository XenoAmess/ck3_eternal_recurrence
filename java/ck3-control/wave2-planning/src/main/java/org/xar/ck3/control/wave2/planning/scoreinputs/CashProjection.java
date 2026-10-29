package org.xar.ck3.control.wave2.planning.scoreinputs;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.planning.campaigncadence.MonthlyObservation.Metric;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.Expense;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.FixedPoint;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.NormalizedCurrentCash;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.Read;

/** Complete pure _cash_metrics mapping after the one shared actual cash decoder. */
public record CashProjection(Map<Metric, Rate> metrics, Source source) {
    private static final Set<Metric> METRICS = Set.of(Metric.GROSS_INCOME, Metric.TOTAL_EXPENSES,
            Metric.MILITARY_CURRENT, Metric.MILITARY_ALL_RAISED);

    public enum Origin {
        GROSS(Metric.GROSS_INCOME, "player_monthly_gross_income", "player_monthly_gross_income", "played_character_personal_gold"),
        TOTAL(Metric.TOTAL_EXPENSES, "player_monthly_total_expenses", "player_monthly_total_expenses", "played_character_personal_gold"),
        CURRENT(Metric.MILITARY_CURRENT, "current", "military_expenses.current.gold_raw", "actor_owned_military_once_across_all_wars"),
        RAISED(Metric.MILITARY_ALL_RAISED, "all_raised", "military_expenses.all_raised.gold_raw", "actor_owned_military_once_across_all_wars");
        private final Metric metric;
        private final String key;
        private final String locator;
        private final String scope;
        Origin(Metric metric, String key, String locator, String scope) {
            this.metric = metric; this.key = key; this.locator = locator; this.scope = scope;
        }
        public Metric metric() { return metric; }
        public String key() { return key; }
        public String locator() { return locator; }
        public String scope() { return scope; }
    }
    public sealed interface Rate permits Observed, Unknown {
        Origin origin();
        ObjectNode toJson();
    }
    public record Observed(Origin origin, BigInteger raw) implements Rate {
        public Observed {
            require(origin != null && raw != null && raw.signum() >= 0
                    && raw.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "observed compatible nonnegative int64 rate required");
        }
        public String valueText() {
            return new BigDecimal(raw).divide(BigDecimal.valueOf(100_000), new MathContext(28, RoundingMode.HALF_EVEN)).toPlainString();
        }
        @Override public ObjectNode toJson() {
            ObjectNode object = StrictJson.object(); object.put("value", valueText()); object.put("unit", "gold/month");
            object.put("availability", "observed"); object.put("source_ref", "existing_cash_v2");
            object.put("locator", origin.locator()); object.put("scope", origin.scope());
            return object;
        }
    }
    public enum UnknownReason { COMPONENT_UNAVAILABLE, MILITARY_EXCEEDS_TOTAL }
    public record Unknown(Origin origin, UnknownReason reason) implements Rate {
        public Unknown {
            require(origin != null && reason != null && (reason != UnknownReason.MILITARY_EXCEEDS_TOTAL || origin == Origin.CURRENT),
                    "explicit unknown component branch required");
        }
        @Override public ObjectNode toJson() {
            String wire = reason == UnknownReason.MILITARY_EXCEEDS_TOTAL
                    ? "cash_military_exceeds_compatible_total_expenses" : "cash_v2_component_unavailable:" + origin.key();
            return new UnknownScoreMetric(origin.metric(), wire).toJson();
        }
    }
    public record Source(ObjectNode monthlyIncomeSemantics, String gameVersion, String executableSha256) {
        public Source {
            require(monthlyIncomeSemantics != null, "original normalized monthly semantics required");
            StrictJson.text(gameVersion); StrictJson.text(executableSha256);
            monthlyIncomeSemantics = monthlyIncomeSemantics.deepCopy();
        }
        @Override public ObjectNode monthlyIncomeSemantics() { return monthlyIncomeSemantics.deepCopy(); }
        public ObjectNode toJson() {
            ObjectNode object = StrictJson.object(); object.set("monthly_income_semantics", monthlyIncomeSemantics.deepCopy());
            object.put("game_version", gameVersion); object.put("executable_sha256", executableSha256); return object;
        }
    }

    public CashProjection {
        require(metrics != null && metrics.keySet().equals(METRICS) && source != null, "exact four-rate projection required");
        for (Map.Entry<Metric, Rate> entry : metrics.entrySet()) {
            require(entry.getValue() != null && entry.getKey() == entry.getValue().origin().metric(), "rate origin differs from metric");
        }
        metrics = Map.copyOf(metrics);
    }

    /** The same defensive snapshot bytes feed normalization and projection; no re-labeling a retained DTO. */
    public static CashProjection fromPacket(byte[] currentPacket, byte[] snapshotBytes) {
        require(currentPacket != null && snapshotBytes != null, "original packet and snapshot bytes required");
        byte[] packet = currentPacket.clone(); byte[] snapshotCopy = snapshotBytes.clone();
        NormalizedCurrentCash cash;
        try { cash = RawCashCodec.normalize(packet, snapshotCopy); }
        catch (ContractViolationException rejectedInput) {
            throw new ProjectionDomainRejection(rejectedInput.getMessage());
        }
        JsonNode parsed = StrictJson.parse(snapshotCopy);
        requireInput(parsed instanceof ObjectNode, "ordinary snapshot object required");
        return fromNormalized(cash, (ObjectNode) parsed);
    }

    private static CashProjection fromNormalized(NormalizedCurrentCash cash, ObjectNode snapshot) {
        RawCashCodec.Metrics values = cash.metrics();
        requireInput(values.trueNetSemantics(), "cash_v2_monthly_semantics_missing");
        requireInput(actualTrue(values.readiness().sameFrameReady()), "cash_same_frame_unavailable");
        requireInput(values.queriedSnapshotId().known() && snapshot.get("snapshot_id") != null && snapshot.get("snapshot_id").isTextual()
                && values.queriedSnapshotId().value().equals(snapshot.get("snapshot_id").textValue()), "cash_query_binding_changed:queried_snapshot_id");
        requireInput(sameInteger(values.queriedRevision(), snapshot.get("revision")), "cash_query_binding_changed:queried_revision");
        requireInput(sameInteger(values.queriedNativeRevision(), snapshot.get("native_revision")), "cash_query_binding_changed:queried_native_revision");
        List<BigInteger> actualWars = new ArrayList<>();
        requireInput(snapshot.get("active_wars") instanceof ArrayNode, "cash_player_war_scope_changed");
        for (JsonNode row : snapshot.get("active_wars")) {
            requireInput(row instanceof ObjectNode && row.get("war_id") != null && row.get("war_id").isIntegralNumber(), "cash_player_war_scope_changed");
            actualWars.add(row.get("war_id").bigIntegerValue());
        }
        actualWars.sort(BigInteger::compareTo);
        List<BigInteger> cashWars = new ArrayList<>(cash.activeWarIds()); cashWars.sort(BigInteger::compareTo);
        requireInput(cashWars.equals(actualWars), "cash_player_war_scope_changed");
        ObjectNode wire = (ObjectNode) StrictJson.parse(cash.toJson());
        JsonNode wallet = snapshot.get("played_character_gold"), treasury = wire.get("current_treasury");
        requireInput(!(wallet instanceof ObjectNode) || !(treasury instanceof ObjectNode) || sameDomain(wallet, treasury),
                "cash_and_ordinary_wallet_disagree");
        EnumMap<Metric, Rate> projected = new EnumMap<>(Metric.class);
        projected.put(Metric.GROSS_INCOME, fixed(Origin.GROSS, values.monthlyGrossIncome(), values.readiness().monthlyGrossIncomeReady()));
        projected.put(Metric.TOTAL_EXPENSES, fixed(Origin.TOTAL, values.monthlyTotalExpenses(), values.readiness().monthlyTotalExpensesReady()));
        projected.put(Metric.MILITARY_CURRENT, military(Origin.CURRENT, values.currentMilitaryExpenses(), values.readiness().currentMilitaryExpensesReady()));
        projected.put(Metric.MILITARY_ALL_RAISED, military(Origin.RAISED, values.allRaisedMilitaryExpenses(), values.readiness().allRaisedMilitaryExpensesReady()));
        if (projected.get(Metric.TOTAL_EXPENSES) instanceof Observed total
                && projected.get(Metric.MILITARY_CURRENT) instanceof Observed current && current.raw().compareTo(total.raw()) > 0) {
            projected.put(Metric.MILITARY_CURRENT, new Unknown(Origin.CURRENT, UnknownReason.MILITARY_EXCEEDS_TOTAL));
        }
        requireInput(wire.get("monthly_income_semantics") instanceof ObjectNode, "cash_v2_monthly_semantics_missing");
        return new CashProjection(projected, new Source((ObjectNode) wire.get("monthly_income_semantics"),
                StrictJson.text(wire.get("game_version")), StrictJson.text(wire.get("executable_sha256"))));
    }

    /** The original Python tuple uses the agreed JSON list domain. */
    public ArrayNode toJson() {
        ObjectNode rates = StrictJson.object();
        for (Origin origin : Origin.values()) { rates.set(origin.metric().wire(), metrics.get(origin.metric()).toJson()); }
        ArrayNode result = JsonNodeFactory.instance.arrayNode(); result.add(rates); result.add(source.toJson()); return result;
    }

    private static Rate fixed(Origin origin, Read<FixedPoint> fixed, Read<Boolean> readiness) {
        if (!actualTrue(readiness) || !fixed.known() || fixed.value().raw().signum() < 0) {
            return new Unknown(origin, UnknownReason.COMPONENT_UNAVAILABLE);
        }
        return new Observed(origin, fixed.value().raw());
    }
    private static Rate military(Origin origin, Expense expense, Read<Boolean> readiness) {
        if (!actualTrue(readiness) || !expense.available() || !expense.resourceKind().known()
                || !expense.resourceKind().value().equals("actor_military_" + origin.key() + "_maintenance")
                || !expense.rawScale().known() || !expense.goldRaw().known() || expense.goldRaw().value().signum() < 0) {
            return new Unknown(origin, UnknownReason.COMPONENT_UNAVAILABLE);
        }
        return new Observed(origin, expense.goldRaw().value());
    }
    private static void requireInput(boolean condition, String publicReason) {
        if (!condition) { throw new ProjectionDomainRejection(publicReason); }
    }

    private static boolean actualTrue(Read<Boolean> flag) { return flag.known() && Boolean.TRUE.equals(flag.value()); }
    private static boolean sameInteger(Read<BigInteger> expected, JsonNode actual) {
        return expected.known() && actual != null && actual.isIntegralNumber() && expected.value().equals(actual.bigIntegerValue());
    }
    private static boolean sameDomain(JsonNode left, JsonNode right) {
        if (left == null || right == null) { return left == right; }
        if (left.isIntegralNumber() && right.isIntegralNumber()) { return left.bigIntegerValue().equals(right.bigIntegerValue()); }
        if (left.isFloatingPointNumber() && right.isFloatingPointNumber()) { return left.decimalValue().compareTo(right.decimalValue()) == 0; }
        if (left.isObject() && right.isObject()) {
            if (!left.properties().stream().map(Map.Entry::getKey).collect(java.util.stream.Collectors.toSet())
                    .equals(right.properties().stream().map(Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()))) { return false; }
            return left.properties().stream().allMatch(entry -> sameDomain(entry.getValue(), right.get(entry.getKey())));
        }
        if (left.isArray() && right.isArray()) {
            if (left.size() != right.size()) { return false; }
            for (int index = 0; index < left.size(); index++) { if (!sameDomain(left.get(index), right.get(index))) { return false; } }
            return true;
        }
        return left.equals(right);
    }
}
