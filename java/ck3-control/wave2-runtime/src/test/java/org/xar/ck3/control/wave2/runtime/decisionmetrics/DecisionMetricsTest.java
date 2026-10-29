package org.xar.ck3.control.wave2.runtime.decisionmetrics;

import org.junit.jupiter.api.Test;

/** Persistent reactor route executes the same real-consumer regression as the finite local probe. */
final class DecisionMetricsTest {
    @Test void actualConsumerClockSerializationUnknownAndPersistenceRegressions() throws Exception {
        DecisionMetricsRegression.run();
    }
    @Test void originalSavedQualificationProducerReachesActualSavedMetricConsumer() {
        org.xar.ck3.control.wave2.runtime.savedproof.DecisionSavedMetricsRegression.run();
    }
}
