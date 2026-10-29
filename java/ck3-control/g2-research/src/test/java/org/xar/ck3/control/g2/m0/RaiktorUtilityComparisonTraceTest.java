package org.xar.ck3.control.g2.m0;

import org.junit.jupiter.api.Test;

/** Default Surefire discovery; missing original-source bindings fail instead of skipping. */
final class RaiktorUtilityComparisonTraceTest {
    @Test void originalProducerAndFormalPlannerConsumer() throws Exception {
        RaiktorUtilityComparisonTraceOracle.run(
                java.nio.file.Path.of(required("xar.repoRoot", "XAR_REPO_ROOT")),
                required("xar.python", "XAR_ORACLE_PYTHON"), required("xar.machineId", "XAR_MACHINE_ID"));
    }
    private static String required(String property, String environment) {
        String value = System.getProperty(property, System.getenv(environment));
        if (value == null || value.isBlank()) throw new IllegalStateException(property + " or " + environment + " required");
        return value;
    }
}
