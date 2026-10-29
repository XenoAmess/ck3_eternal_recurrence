package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Environment boundary only; no interpreter, accepted build or game is launched. */
final class CiBootstrapOracleRootTest {
    private record Fixture(Path javaRepository, Path oracleRepository, Path python, Map<String, String> environment) { }

    private static Fixture fixture(Path directory) throws IOException {
        Path javaRepository = Files.createDirectory(directory.resolve("java-checkout")).toRealPath();
        Path oracleRepository = Files.createDirectory(directory.resolve("oracle-checkout")).toRealPath();
        for (Path repository : List.of(javaRepository, oracleRepository)) {
            Path workflows = Files.createDirectories(repository.resolve(".github/workflows"));
            Files.writeString(workflows.resolve("static-ci.yml"), "name: software-only-environment-fixture\n");
        }
        Path python = Files.writeString(directory.resolve("python.exe"), "software identity fixture; never executed").toRealPath();
        var environment = Map.of("XAR_ORACLE_PYTHON", python.toString(),
                "XAR_ORACLE_REPO", oracleRepository.toString(), "XAR_REPO_ROOT", oracleRepository.toString(),
                "JAVA_HOME", javaRepository.toString(), "PYTHONPATH", "original-one;original-two", "UNRELATED", "retained");
        return new Fixture(javaRepository, oracleRepository, python, environment);
    }

    @Test void selectedInterpreterPreservesExplicitOracleRootAcrossDifferentJavaCheckout(@TempDir Path directory) throws Exception {
        Fixture input = fixture(directory);
        Map<String, String> actual = CiBootstrap.OracleEnvironment.bindSelectedInterpreter(input.python(), input.environment());
        var readback = CanonicalOracleEnvironment.require(actual);
        assertEquals(input.oracleRepository().toString(), readback.repositoryRoot());
        assertNotEquals(input.javaRepository().toString(), readback.repositoryRoot());
        assertEquals(input.python().toString(), readback.python());
        assertEquals(input.environment().get("PYTHONPATH"), actual.get("PYTHONPATH"));
        assertEquals(input.environment().get("JAVA_HOME"), actual.get("JAVA_HOME"));
        assertEquals("retained", actual.get("UNRELATED"));
        assertEquals(input.oracleRepository().toString(), input.environment().get("XAR_ORACLE_REPO"));
        assertEquals(input.oracleRepository().toString(), actual.get("XAR_REPO_ROOT"));
    }

    @Test void missingConflictingOrDifferentInterpreterRolesCannotBeRepairedFromJavaRoot(@TempDir Path directory) throws Exception {
        Fixture input = fixture(directory);
        for (String role : List.of("XAR_ORACLE_PYTHON", "XAR_ORACLE_REPO", "XAR_REPO_ROOT")) {
            var missing = new HashMap<>(input.environment());
            missing.remove(role);
            assertThrows(IOException.class, () -> CiBootstrap.OracleEnvironment.bindSelectedInterpreter(input.python(), missing));
        }
        var conflicting = new HashMap<>(input.environment());
        conflicting.put("XAR_REPO_ROOT", input.javaRepository().toString());
        assertThrows(IOException.class, () -> CiBootstrap.OracleEnvironment.bindSelectedInterpreter(input.python(), conflicting));
        Path different = Files.writeString(directory.resolve("different-python.exe"), "other software identity").toRealPath();
        assertThrows(IOException.class, () -> CiBootstrap.OracleEnvironment.bindSelectedInterpreter(different, input.environment()));
        assertEquals(input.python().toString(), input.environment().get("XAR_ORACLE_PYTHON"));
        assertEquals(input.oracleRepository().toString(), input.environment().get("XAR_REPO_ROOT"));
    }

    @Test void sameRepositoryHostedRolesRemainExplicit(@TempDir Path directory) throws Exception {
        Fixture input = fixture(directory);
        var environment = new HashMap<>(input.environment());
        environment.put("XAR_ORACLE_REPO", input.javaRepository().toString());
        environment.put("XAR_REPO_ROOT", input.javaRepository().toString());
        Map<String, String> actual = CiBootstrap.OracleEnvironment.bindSelectedInterpreter(input.python(), environment);
        var readback = CanonicalOracleEnvironment.require(actual);
        assertEquals(input.javaRepository().toString(), readback.repositoryRoot());
        assertEquals(input.python().toString(), readback.python());
        assertEquals("original-one;original-two", actual.get("PYTHONPATH"));
    }
}
