package org.xar.ck3.control.wave3.planning.scorestate;

import java.math.MathContext;
import java.math.RoundingMode;
import java.util.EnumMap;
import java.util.Optional;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.score.DomainScores;
import org.xar.ck3.control.score.ScoreDecimal;
import org.xar.ck3.control.score.ScoreInterval;

/** Pure state_intervals closure. All scalar steps use Decimal40; interval add/scale use shared Decimal80. */
public final class StateScore {
    private static final MathContext C40 = new MathContext(40, RoundingMode.HALF_EVEN);
    private static final ScoreDecimal ZERO = ScoreDecimal.ZERO;
    private static final ScoreDecimal ONE = ScoreDecimal.integer(1);
    private static final ScoreDecimal HUNDRED = ScoreDecimal.HUNDRED;
    private StateScore() { }

    public static Optional<ScoreDecimal> metric(MetricPacket packet, MetricName name) {
        if (!(packet.row(name) instanceof MetricRow.Fields row)) { return Optional.empty(); }
        if (row.availability() instanceof MetricScalar.Unsupported invalid) {
            StrictJson.require(invalid.kind() != MetricScalar.TokenKind.ARRAY && invalid.kind() != MetricScalar.TokenKind.OBJECT,
                    "unhashable availability token");
        }
        if (!row.availability().textEquals("observed") && !row.availability().textEquals("known_absent")) {
            return Optional.empty();
        }
        StrictJson.require(row.unit().textEquals(name.unit()), "wrong scoring unit: " + name.wire());
        ScoreDecimal value = row.value().decimal();
        StrictJson.require(name == MetricName.GOLD || value.compareTo(ZERO) >= 0, "negative scoring metric");
        if (name == MetricName.CONTROL || name == MetricName.REBELS || name == MetricName.CONTINUATION) {
            StrictJson.require(value.compareTo(ONE) <= 0, "fraction/boolean above one");
        }
        if (name == MetricName.CONTINUATION) {
            StrictJson.require(value.equals(ZERO) || value.equals(ONE), "continuation must be proven zero or one");
        }
        if (name == MetricName.LEGACY || name == MetricName.BACKUP) {
            StrictJson.require(value.value().stripTrailingZeros().scale() <= 0, "discrete metric is fractional");
        }
        return Optional.of(value);
    }

    public static Optional<ScoreInterval> boundedMetric(MetricPacket packet, MetricName name) {
        Optional<ScoreDecimal> known = metric(packet, name);
        if (known.isPresent()) { return Optional.of(ScoreInterval.exact(known.orElseThrow())); }
        MetricRow source = packet.row(name);
        if (source instanceof MetricRow.Missing) { return Optional.empty(); }
        if (!(source instanceof MetricRow.Fields row)) {
            throw new ContractViolationException("bounded metric requires object row, not null or scalar");
        }
        if (!row.availability().textEquals("bounded")) { return Optional.empty(); }
        StrictJson.require(row.unit().textEquals(name.unit()), "bounded scoring unit mismatch");
        ScoreInterval interval = new ScoreInterval(row.lower().decimal(), row.upper().decimal());
        StrictJson.require(name == MetricName.GOLD || interval.lower().compareTo(ZERO) >= 0, "bounded metric below zero");
        if (name == MetricName.CONTROL || name == MetricName.REBELS) {
            StrictJson.require(interval.upper().compareTo(ONE) <= 0, "bounded fraction above one");
        }
        return Optional.of(interval);
    }

    public static ScoreDecimal normalize(ScoreDecimal current, ScoreDecimal baseline, ScoreDecimal scale) {
        StrictJson.require(current.compareTo(ZERO) >= 0 && baseline.compareTo(ZERO) >= 0 && scale.compareTo(ZERO) > 0,
                "invalid normalization inputs");
        return divide(multiply(HUNDRED, current), add(current, max(baseline, scale)));
    }

    public static ScoreInterval relative(Optional<ScoreDecimal> current, Optional<ScoreDecimal> baseline, ScoreDecimal scale) {
        if (current.isEmpty()) { return ScoreInterval.UNKNOWN; }
        ScoreDecimal value = current.orElseThrow();
        if (value.equals(ZERO)) { return ScoreInterval.exact(ZERO); }
        if (baseline.isEmpty()) { return new ScoreInterval(ZERO, normalize(value, ZERO, scale)); }
        return ScoreInterval.exact(normalize(value, baseline.orElseThrow(), scale));
    }

    public static ScoreInterval boundedRelative(Optional<ScoreInterval> current, Optional<ScoreInterval> baseline, ScoreDecimal scale) {
        if (current.isEmpty()) { return ScoreInterval.UNKNOWN; }
        ScoreInterval value = current.orElseThrow();
        if (baseline.isEmpty()) { return new ScoreInterval(ZERO, normalize(value.upper(), ZERO, scale)); }
        ScoreInterval initial = baseline.orElseThrow();
        return new ScoreInterval(normalize(value.lower(), initial.upper(), scale), normalize(value.upper(), initial.lower(), scale));
    }

    /** Only explicit input validators become domain rejection; application failures remain unknown. */
    public static void validateInput(StateScoreInput input) {
        EnumMap<MetricName, Optional<ScoreDecimal>> current;
        EnumMap<MetricName, Optional<ScoreDecimal>> baseline;
        try {
            current = values(input.current());
            baseline = values(input.baseline());
            for (MetricName name : new MetricName[] {MetricName.REALM, MetricName.DYNASTY}) {
                boundedMetric(input.current(), name);
                boundedMetric(input.baseline(), name);
            }
            boundedMetric(input.current(), MetricName.CONTROL);
            boundedMetric(input.current(), MetricName.REBELS);
        } catch (ContractViolationException invalidInput) {
            throw new ProjectionDomainRejection(invalidInput.getMessage());
        }
        Optional<ScoreDecimal> expense = current.get(MetricName.EXPENSES);
        Optional<ScoreDecimal> military = current.get(MetricName.MILITARY);
        if (expense.isPresent() && military.isPresent()
                && military.orElseThrow().compareTo(expense.orElseThrow()) > 0) {
            throw new ProjectionDomainRejection("military rate exceeds total expense rate");
        }
        Optional<ScoreDecimal> income = baseline.get(MetricName.INCOME);
        Optional<ScoreDecimal> discretionary = baseline.get(MetricName.DISCRETIONARY);
        expense = baseline.get(MetricName.EXPENSES);
        military = baseline.get(MetricName.MILITARY);
        if (discretionary.isEmpty() && income.isPresent() && expense.isPresent() && military.isPresent()
                && military.orElseThrow().compareTo(expense.orElseThrow()) > 0) {
            throw new ProjectionDomainRejection("baseline military/expense mismatch");
        }
    }

    public static DomainScores evaluate(StateScoreInput input) {
        EnumMap<MetricName, Optional<ScoreDecimal>> current = values(input.current());
        EnumMap<MetricName, Optional<ScoreDecimal>> baseline = values(input.baseline());
        ScoreInterval land = boundedRelative(boundedMetric(input.current(), MetricName.REALM),
                boundedMetric(input.baseline(), MetricName.REALM), ONE);
        Optional<ScoreDecimal> g = current.get(MetricName.INCOME), e = current.get(MetricName.EXPENSES);
        Optional<ScoreDecimal> m = current.get(MetricName.MILITARY);
        Optional<ScoreDecimal> civil = Optional.empty();
        if (e.isPresent() && m.isPresent()) {
            StrictJson.require(m.orElseThrow().compareTo(e.orElseThrow()) <= 0, "military rate exceeds total expense rate");
            civil = Optional.of(subtract(e.orElseThrow(), m.orElseThrow()));
        }
        Optional<ScoreDecimal> bg = baseline.get(MetricName.INCOME), bu = baseline.get(MetricName.DISCRETIONARY);
        Optional<ScoreDecimal> be = baseline.get(MetricName.EXPENSES), bm = baseline.get(MetricName.MILITARY);
        if (bu.isEmpty() && bg.isPresent() && be.isPresent() && bm.isPresent()) {
            StrictJson.require(bm.orElseThrow().compareTo(be.orElseThrow()) <= 0, "baseline military/expense mismatch");
            bu = Optional.of(max(ZERO, subtract(bg.orElseThrow(), subtract(be.orElseThrow(), bm.orElseThrow()))));
        }
        Optional<ScoreDecimal> gold = current.get(MetricName.GOLD), due = current.get(MetricName.DUE);
        ScoreInterval economy = ScoreInterval.UNKNOWN;
        if (g.isPresent() && e.isPresent() && civil.isPresent() && gold.isPresent() && due.isPresent()
                && bg.isPresent() && bu.isPresent()) {
            ScoreDecimal income = g.orElseThrow(), cash = gold.orElseThrow(), commitment = due.orElseThrow();
            ScoreDecimal u = max(ZERO, subtract(income, civil.orElseThrow())), net = subtract(income, e.orElseThrow());
            ScoreDecimal wealth = subtract(cash, commitment), debt = add(max(negate(cash), ZERO), commitment);
            ScoreDecimal q12 = multiply(ScoreDecimal.integer(12), max(max(income, bg.orElseThrow()), ONE));
            ScoreDecimal flow = normalize(u, bu.orElseThrow(), ONE);
            ScoreDecimal buffer = multiply(HUNDRED, min(ONE, max(ZERO, divide(wealth, q12))));
            ScoreDecimal solvency = divide(HUNDRED, add(ONE, divide(debt, q12)));
            ScoreDecimal money = add(add(multiply(decimal(".55"), flow), multiply(decimal(".30"), buffer)),
                    multiply(decimal(".15"), solvency));
            if (net.compareTo(ZERO) < 0 && wealth.compareTo(ZERO) <= 0) { money = min(money, ScoreDecimal.integer(25)); }
            economy = ScoreInterval.exact(money);
        } else if (gold.isPresent() && gold.orElseThrow().compareTo(ZERO) <= 0 && g.isPresent() && e.isPresent()
                && g.orElseThrow().compareTo(e.orElseThrow()) < 0) {
            economy = new ScoreInterval(ZERO, ScoreDecimal.integer(25));
        }
        ScoreInterval power = relative(current.get(MetricName.POWER), baseline.get(MetricName.POWER), HUNDRED);
        Optional<ScoreDecimal> full = current.get(MetricName.RAISED);
        ScoreInterval factor = new ScoreInterval(decimal(".65"), ONE);
        if (g.isPresent() && civil.isPresent() && full.isPresent()) {
            ScoreDecimal total = add(civil.orElseThrow(), full.orElseThrow());
            ScoreDecimal afford = total.equals(ZERO) ? ONE : min(ONE, divide(g.orElseThrow(), total));
            factor = ScoreInterval.exact(add(decimal(".65"), multiply(decimal(".35"), afford)));
        }
        ScoreInterval military = new ScoreInterval(multiply(power.lower(), factor.lower()), multiply(power.upper(), factor.upper()));
        Optional<ScoreInterval> control = boundedMetric(input.current(), MetricName.CONTROL);
        Optional<ScoreInterval> rebels = boundedMetric(input.current(), MetricName.REBELS);
        ScoreInterval controlScore = control.isEmpty() ? new ScoreInterval(ZERO, ScoreDecimal.integer(60))
                : control.orElseThrow().scale(ScoreDecimal.integer(60));
        ScoreInterval rebelScore = rebels.isEmpty() ? new ScoreInterval(ZERO, ScoreDecimal.integer(40))
                : new ScoreInterval(multiply(ScoreDecimal.integer(40), subtract(ONE, rebels.orElseThrow().upper())),
                        multiply(ScoreDecimal.integer(40), subtract(ONE, rebels.orElseThrow().lower())));
        ScoreInterval stability = controlScore.add(rebelScore);
        ScoreInterval dynasty = boundedRelative(boundedMetric(input.current(), MetricName.DYNASTY),
                boundedMetric(input.baseline(), MetricName.DYNASTY), ONE).scale(decimal(".8")).add(
                relative(current.get(MetricName.LEGACY), baseline.get(MetricName.LEGACY), ONE).scale(decimal(".2")));
        Optional<ScoreDecimal> legal = current.get(MetricName.CONTINUATION), backup = current.get(MetricName.BACKUP);
        ScoreDecimal top = backup.isEmpty() ? HUNDRED : add(ScoreDecimal.integer(70),
                multiply(ScoreDecimal.integer(15), min(backup.orElseThrow(), ScoreDecimal.integer(2))));
        ScoreInterval heirs;
        if (legal.isPresent() && legal.orElseThrow().equals(ZERO)) { heirs = ScoreInterval.exact(ZERO); }
        else if (legal.isPresent() && legal.orElseThrow().equals(ONE)) {
            heirs = backup.isEmpty() ? new ScoreInterval(ScoreDecimal.integer(70), top) : ScoreInterval.exact(top);
        } else { heirs = new ScoreInterval(ZERO, top); }
        return new DomainScores(land, economy, military, stability, dynasty, heirs);
    }

    private static EnumMap<MetricName, Optional<ScoreDecimal>> values(MetricPacket packet) {
        EnumMap<MetricName, Optional<ScoreDecimal>> result = new EnumMap<>(MetricName.class);
        for (MetricName name : MetricName.values()) { result.put(name, metric(packet, name)); }
        return result;
    }
    private static ScoreDecimal decimal(String value) { return ScoreDecimal.parse(value); }
    private static ScoreDecimal add(ScoreDecimal left, ScoreDecimal right) { return left.add(right, C40); }
    private static ScoreDecimal multiply(ScoreDecimal left, ScoreDecimal right) { return left.multiply(right, C40); }
    private static ScoreDecimal divide(ScoreDecimal left, ScoreDecimal right) { return left.divide(right, C40); }
    private static ScoreDecimal subtract(ScoreDecimal left, ScoreDecimal right) {
        // Exact sign inversion first; one rounded subtraction, including signed zero.
        ScoreDecimal opposite = new ScoreDecimal(right.value().negate(), right.value().signum() == 0 && !right.negativeZero());
        return add(left, opposite);
    }
    private static ScoreDecimal negate(ScoreDecimal value) {
        // Python unary minus applies context and normalizes a zero result to positive zero.
        return new ScoreDecimal(value.value().negate(C40), false);
    }
    private static ScoreDecimal min(ScoreDecimal left, ScoreDecimal right) { return left.compareTo(right) <= 0 ? left : right; }
    private static ScoreDecimal max(ScoreDecimal left, ScoreDecimal right) { return left.compareTo(right) >= 0 ? left : right; }
}
