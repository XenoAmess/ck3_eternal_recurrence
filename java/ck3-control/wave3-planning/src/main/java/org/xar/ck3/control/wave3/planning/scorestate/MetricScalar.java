package org.xar.ck3.control.wave3.planning.scorestate;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.score.ScoreDecimal;

/** Missing/null/token kind survive the boundary; decimal conversion is demand-driven. */
public sealed interface MetricScalar {
    record Missing() implements MetricScalar { }
    record NullValue() implements MetricScalar { }
    record Text(String value) implements MetricScalar {
        public Text { Objects.requireNonNull(value); }
    }
    record IntegerValue(BigInteger value) implements MetricScalar {
        public IntegerValue { Objects.requireNonNull(value); }
    }
    enum TokenKind { BOOLEAN, INTEGER, FRACTIONAL, STRING, ARRAY, OBJECT }
    record Unsupported(TokenKind kind) implements MetricScalar {
        public Unsupported { Objects.requireNonNull(kind); }
    }

    default boolean textEquals(String text) { return this instanceof Text field && field.value().equals(text); }
    default ScoreDecimal decimal() {
        return switch (this) {
            case Text text -> ScoreDecimal.parse(text.value());
            case IntegerValue integer -> ScoreDecimal.integer(integer.value());
            default -> throw new ContractViolationException("explicit decimal string/integer required");
        };
    }
}
