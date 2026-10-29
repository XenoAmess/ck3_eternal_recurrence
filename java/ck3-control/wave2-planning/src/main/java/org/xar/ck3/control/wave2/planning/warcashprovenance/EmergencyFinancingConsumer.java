package org.xar.ck3.control.wave2.planning.warcashprovenance;

import java.util.Objects;
import static org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment.Assessment;

/** Ordinary planner seam: consumes current inputs once, keeps the existing war action, performs no Game I/O. */
public final class EmergencyFinancingConsumer {
    private EmergencyFinancingConsumer() { }
    @FunctionalInterface public interface CurrentInputs {
        EmergencyFinancingAssessmentCodec.Request readCurrent();
    }
    public static Assessment observe(CurrentInputs inputs) {
        return EmergencyFinancingAssessmentCodec.assess(Objects.requireNonNull(inputs.readCurrent()));
    }
}
