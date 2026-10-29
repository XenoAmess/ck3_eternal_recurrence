package org.xar.ck3.control.g2.m0;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;

/** Persistent full-reactor regression: missing original producer inputs fail instead of skipping. */
final class RaiktorExitObservationCodecTest {
    @Test void originalProducerDifferentialAndJsonRoundtrip() throws Exception {
        WarExitCodecOracle.run(Path.of(required("xar.repoRoot", "XAR_REPO_ROOT")),
                required("xar.python", "XAR_ORACLE_PYTHON"), required("xar.machineId", "XAR_MACHINE_ID"));
    }
    private static String required(String property, String variable) {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) value = System.getenv(variable);
        if (value == null || value.isBlank()) throw new IllegalStateException("required original producer binding: " + variable);
        return value;
    }
}
