package org.xar.ck3.control.wave3.planning.scorestate;

import java.util.Objects;

/** Old SDK rows are declared projections; extensions are ignored, never aliases. */
public sealed interface MetricRow {
    record Missing() implements MetricRow { }
    record NullValue() implements MetricRow { }
    record NonObject(MetricScalar.TokenKind kind) implements MetricRow {
        public NonObject { Objects.requireNonNull(kind); }
    }
    record Fields(MetricScalar availability, MetricScalar unit, MetricScalar value,
                  MetricScalar lower, MetricScalar upper) implements MetricRow {
        public Fields {
            Objects.requireNonNull(availability); Objects.requireNonNull(unit); Objects.requireNonNull(value);
            Objects.requireNonNull(lower); Objects.requireNonNull(upper);
        }
    }
}
