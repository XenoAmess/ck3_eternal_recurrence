package org.xar.ck3.control.g2.m0.integration;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;
import org.junit.jupiter.api.Test;

/** Default Surefire bridge. Missing actual source/runtime inputs is a hard RED, never a passing skip. */
final class M0ConsumerRoundTripTest {
    @Test void compiledJavaDecisionReachesOriginalConsumerCohortAndPersistedJson() throws Exception {
        M0FixtureConfig config = M0FixtureConfig.fromEnvironment();
        Path root = freshDirectory(config, "original-consumers");
        M0ConsumerRoundTrip.main(new String[] {
                config.repository().toString(), config.pythonPath().toString(),
                Path.of(System.getProperty("java.home"), "bin",
                        System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java").toString(),
                M0FixtureConfig.currentTestClasspath(), root.resolve("actual.json").toString(),
                config.recommendationOracle().sha256(), root.resolve("test-scratch").toString(),
        });
        M0LegacyComposerProbe.main(new String[] {
                config.repository().toString(), config.pythonPath().toString(),
                Path.of(System.getProperty("java.home"), "bin",
                        System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java").toString(),
                M0FixtureConfig.currentTestClasspath(), config.candidateComposer().path(),
                config.recommendationAdapter().path(), root.resolve("legacy-composer").toString(),
        });
        config.verify();
    }

    @Test void commonRequestAndResponsePreserveOriginalOracleAndRejectCrossedFrames() throws Exception {
        M0FixtureConfig config = M0FixtureConfig.fromEnvironment();
        Path root = freshDirectory(config, "common-wire");
        M0CommonRoundTrip.main(new String[] {
                config.originalHttpInput().path(), config.originalHttpExpected().path(),
                config.httpSourceMetadata().path(), root.resolve("g2-http").toString(),
                "m0-common-" + UUID.randomUUID(),
        });
        config.verify();
    }

    private static Path freshDirectory(M0FixtureConfig config, String label) throws Exception {
        Path admitted = config.outputRoot();
        if (!Files.isDirectory(admitted)) throw new IllegalStateException("actual admitted M0 integration output root required");
        return Files.createDirectory(admitted.resolve(label + "-" + UUID.randomUUID()));
    }
}
