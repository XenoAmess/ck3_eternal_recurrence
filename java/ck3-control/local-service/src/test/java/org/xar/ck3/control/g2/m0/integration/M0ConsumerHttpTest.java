package org.xar.ck3.control.g2.m0.integration;

import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.G2Wire;

/** Adopt into local-service tests; exercises original consumers against the already-running Quarkus host. */
@QuarkusTest
final class M0ConsumerHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @Test void originalConsumerCohortUsesActualSharedClientAndJsonCheckpointRepresentation() throws Exception {
        M0FixtureConfig config = M0FixtureConfig.fromEnvironment().withHttpBaseUri(
                URI.create("http://127.0.0.1:" + endpoint.getPort()));
        Path root = Files.createDirectory(config.outputRoot().resolve("http-consumers-" + UUID.randomUUID()));
        Path javaExecutable = Path.of(System.getProperty("java.home"), "bin",
                System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        Path actualTransportConfig = root.resolve("actual-http-fixture.json");
        config.writeFresh(actualTransportConfig);
        M0ConsumerRoundTrip.run(new String[] {
                config.repository().toString(), config.pythonPath().toString(), javaExecutable.toString(),
                M0FixtureConfig.currentTestClasspath(), root.resolve("actual.json").toString(),
                config.recommendationOracle().sha256(), root.resolve("test-scratch").toString(),
        }, M0HttpStdioAdapter.class.getName(), actualTransportConfig);
        config.verify();
    }
}
