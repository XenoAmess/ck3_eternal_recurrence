package org.xar.ck3.control.warbudget;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;
import org.junit.jupiter.api.Test;

/** Persistent original59-test route, including every importer's continuation with Java results. */
final class WarBudgetOriginalConsumerDifferentialTest {
    @Test void completeOriginalBudgetConsumerCohortUsesActualJavaResults() throws Exception {
        String repo = required("XAR_ORACLE_REPO"), python = required("XAR_ORACLE_PYTHON");
        String machine = required("XAR_MACHINE_ID");
        String java = ProcessHandle.current().info().command().orElseThrow();
        String classpath = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        assertNotNull(classpath); assertFalse(classpath.isBlank());
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        assertTrue(Files.isDirectory(temporary), "shared owned temporary root required");
        Path scratch = temporary.resolve("war-budget-original-consumer-" + UUID.randomUUID());
        BudgetGoldenExporter.main(new String[] {repo, python, machine, scratch.toString(), java, classpath});
        assertTrue(Files.isDirectory(scratch));
    }
    private static String required(String key) {
        String value = System.getenv(key);
        if (value == null || value.isBlank()) { throw new AssertionError(key + " required; absent original cohort is NOT_RUN"); }
        return value;
    }
}
