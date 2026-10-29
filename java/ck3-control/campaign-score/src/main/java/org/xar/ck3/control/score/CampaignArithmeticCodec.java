package org.xar.ck3.control.score;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** One typed byte entry for the existing arithmetic leaves; no native or date qualification. */
public final class CampaignArithmeticCodec {
    public static final String SCHEMA = "g2.campaign-score-arithmetic/v1";

    /**
     * The actual Python caller profile: prec28, HALF_EVEN, Emin=-999999,
     * Emax=999999, capitals=1, clamp=0 and only InvalidOperation,
     * DivisionByZero/Overflow traps. Sticky flags do not affect arithmetic.
     * Interval add/scale/display inherit HALF_EVEN at precision80; score_360
     * explicitly installs precision40/HALF_EVEN. No ambient context is accepted
     * silently. Other Python Decimal profiles require their own proven contract.
     */
    public enum ArithmeticProfile {
        PYTHON_DECIMAL_DEFAULT_28_HALF_EVEN("python-decimal-default-28-half-even/v1");
        private final String wire;
        ArithmeticProfile(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static ArithmeticProfile parse(JsonNode value) {
            String text = StrictJson.text(value);
            for (ArithmeticProfile profile : values()) { if (profile.wire.equals(text)) { return profile; } }
            throw new ContractViolationException("unsupported original decimal arithmetic profile");
        }
    }
    public enum Operation {
        AGGREGATE("aggregate"), SCORE_360("score360"), DISPLAY("display"), ROUNDTRIP("roundtrip"), SCALE("scale"), ADD("add");
        private final String wire;
        Operation(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Operation parse(JsonNode value) {
            String text = StrictJson.text(value);
            for (Operation operation : values()) { if (operation.wire.equals(text)) { return operation; } }
            throw new ContractViolationException("unknown campaign arithmetic operation");
        }
    }
    public sealed interface Input permits AggregateInput, HistoryInput, DisplayInput, IntervalInput, ScaleInput, AddInput { }
    public record AggregateInput(DomainScores scores) implements Input {
        public AggregateInput { Objects.requireNonNull(scores); }
    }
    public record HistoryInput(MonthlyHistory history) implements Input {
        public HistoryInput { Objects.requireNonNull(history); }
    }
    public record DisplayInput(ScoreDecimal lower, ScoreDecimal upper, int places) implements Input {
        public DisplayInput {
            Objects.requireNonNull(lower); Objects.requireNonNull(upper);
            StrictJson.require(places >= 0 && places <= 80, "display places outside leaf contract");
        }
    }
    public record IntervalInput(ScoreInterval interval) implements Input {
        public IntervalInput { Objects.requireNonNull(interval); }
    }
    public record ScaleInput(ScoreInterval interval, ScoreDecimal weight) implements Input {
        public ScaleInput { Objects.requireNonNull(interval); Objects.requireNonNull(weight); }
    }
    public record AddInput(ScoreInterval left, ScoreInterval right) implements Input {
        public AddInput { Objects.requireNonNull(left); Objects.requireNonNull(right); }
    }
    public record Request(ArithmeticProfile profile, Operation operation, Input input) {
        public Request {
            Objects.requireNonNull(profile); Objects.requireNonNull(operation); Objects.requireNonNull(input);
            boolean matching = switch (operation) {
                case AGGREGATE -> input instanceof AggregateInput;
                case SCORE_360 -> input instanceof HistoryInput;
                case DISPLAY -> input instanceof DisplayInput;
                case ROUNDTRIP -> input instanceof IntervalInput;
                case SCALE -> input instanceof ScaleInput;
                case ADD -> input instanceof AddInput;
            };
            StrictJson.require(matching, "arithmetic operation/input type mismatch");
        }
    }
    public sealed interface Result permits IntervalResult, DisplayResult { }
    public record IntervalResult(ScoreInterval interval) implements Result {
        public IntervalResult { Objects.requireNonNull(interval); }
    }
    public record DisplayResult(String text) implements Result {
        public DisplayResult { Objects.requireNonNull(text); }
    }

    private CampaignArithmeticCodec() { }

    public static Request decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "profile", "operation", "input"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "campaign arithmetic schema differs");
        ArithmeticProfile profile = ArithmeticProfile.parse(row.get("profile"));
        Operation operation = Operation.parse(row.get("operation"));
        JsonNode input = row.get("input");
        Input parsed = switch (operation) {
            case AGGREGATE -> new AggregateInput(CampaignScoreCodec.domainScores(input));
            case SCORE_360 -> new HistoryInput(CampaignScoreCodec.history(input));
            case ROUNDTRIP -> new IntervalInput(CampaignScoreCodec.interval(input));
            case SCALE -> {
                ObjectNode scale = StrictJson.object(input, Set.of("interval", "weight"));
                yield new ScaleInput(CampaignScoreCodec.interval(scale.get("interval")), CampaignScoreCodec.decimal(scale.get("weight")));
            }
            case ADD -> {
                ObjectNode add = StrictJson.object(input, Set.of("left", "right"));
                yield new AddInput(CampaignScoreCodec.interval(add.get("left")), CampaignScoreCodec.interval(add.get("right")));
            }
            case DISPLAY -> {
                ObjectNode display = StrictJson.object(input, Set.of("lower", "upper", "places"));
                yield new DisplayInput(CampaignScoreCodec.decimal(display.get("lower")),
                        CampaignScoreCodec.decimal(display.get("upper")),
                        Math.toIntExact(StrictJson.integer(display.get("places"), 0, 80)));
            }
        };
        return new Request(profile, operation, parsed);
    }

    public static Result evaluate(Request request) {
        Objects.requireNonNull(request);
        return switch (request.input()) {
            case AggregateInput aggregate -> new IntervalResult(CampaignScoreCore.aggregateState(aggregate.scores()));
            case HistoryInput history -> new IntervalResult(CampaignScoreCore.score360(history.history()));
            case DisplayInput display -> new DisplayResult(CampaignScoreCore.intervalText(display.lower(), display.upper(), display.places()));
            case IntervalInput interval -> new IntervalResult(interval.interval());
            case ScaleInput scale -> new IntervalResult(scale.interval().scale(scale.weight()));
            case AddInput add -> new IntervalResult(add.left().add(add.right()));
        };
    }

    public static byte[] encode(Result result) {
        return switch (Objects.requireNonNull(result)) {
            case IntervalResult interval -> CampaignScoreCodec.encodeInterval(interval.interval());
            case DisplayResult display -> StrictJson.canonical(new TextNode(display.text()));
        };
    }
    public static byte[] evaluate(byte[] raw) { return encode(evaluate(decode(raw))); }

    /** Recreate the strict request using the original exported decimal-string ABI. */
    public static byte[] encodeRequest(Request request) {
        Objects.requireNonNull(request);
        ObjectNode row = StrictJson.object().put("schema", SCHEMA).put("profile", request.profile().wire())
                .put("operation", request.operation().wire());
        JsonNode input = switch (request.input()) {
            case IntervalInput interval -> CampaignScoreCodec.json(interval.interval());
            case ScaleInput scale -> {
                ObjectNode body = StrictJson.object(); body.set("interval", CampaignScoreCodec.json(scale.interval()));
                body.put("weight", scale.weight().lexical()); yield body;
            }
            case AddInput add -> {
                ObjectNode body = StrictJson.object(); body.set("left", CampaignScoreCodec.json(add.left()));
                body.set("right", CampaignScoreCodec.json(add.right())); yield body;
            }
            case DisplayInput display -> StrictJson.object().put("lower", display.lower().lexical())
                    .put("upper", display.upper().lexical()).put("places", display.places());
            case AggregateInput aggregate -> CampaignScoreCodec.json(aggregate.scores());
            case HistoryInput history -> {
                ObjectNode body = StrictJson.object();
                var samples = body.putArray("samples");
                history.history().samples().forEach(sample -> samples.add(CampaignScoreCodec.json(sample)));
                body.set("endpoint", CampaignScoreCodec.json(history.history().endpoint())); yield body;
            }
        };
        row.set("input", input); return StrictJson.canonical(row);
    }
}
