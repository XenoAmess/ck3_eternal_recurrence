package org.xar.ck3.control.wave3.planning.scorestate;

import java.util.Objects;

public record StateScoreInput(MetricPacket current, MetricPacket baseline) {
    public StateScoreInput { Objects.requireNonNull(current); Objects.requireNonNull(baseline); }
}
