package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.Map;
import java.util.TreeMap;

/** Explicit interpreter, compatibility repository and canonical workflow repository roles. */
public final class CanonicalOracleEnvironment {
    private CanonicalOracleEnvironment() { }

    public record Inputs(String python, String repositoryRoot) {
        public Inputs {
            absolute(python); absolute(repositoryRoot);
        }
    }

    /** Live validation. Both repository roles must independently name the same real source root. */
    public static Inputs require(Map<String, String> environment) throws IOException {
        Path python = plainFile(required(environment, "XAR_ORACLE_PYTHON"));
        Path oracle = plainDirectory(required(environment, "XAR_ORACLE_REPO"));
        Path canonical = plainDirectory(required(environment, "XAR_REPO_ROOT"));
        if (!oracle.equals(canonical))
            throw new IOException("XAR_ORACLE_REPO and XAR_REPO_ROOT must bind the same actual repository");
        Path workflow = oracle.resolve(".github/workflows/static-ci.yml");
        if (!Files.isRegularFile(workflow, LinkOption.NOFOLLOW_LINKS) || Files.size(workflow) < 1
                || !workflow.toRealPath().equals(workflow))
            throw new IOException("Actual canonical workflow source is unavailable");
        return new Inputs(python.toString(), oracle.toString());
    }

    /** A producer deliberately sets all three roles; no missing role is inferred by a reader. */
    public static Map<String, String> bind(Path repository, Path python, Map<String, String> inherited) throws IOException {
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(inherited);
        environment.put("XAR_ORACLE_PYTHON", python.toString());
        environment.put("XAR_ORACLE_REPO", repository.toString());
        environment.put("XAR_REPO_ROOT", repository.toString());
        require(environment);
        return Map.copyOf(environment);
    }

    private static String required(Map<String, String> environment, String name) throws IOException {
        String value = environment.get(name);
        if (value == null || value.isBlank()) throw new IOException("NOT EXECUTED: explicit " + name + " required");
        return value;
    }
    private static Path plainFile(String value) throws IOException {
        Path path = absolute(value);
        if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.size(path) < 1
                || !path.toRealPath().equals(path)) throw new IOException("Plain actual interpreter required: " + path);
        return path;
    }
    private static Path plainDirectory(String value) throws IOException {
        Path path = absolute(value);
        if (!Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS) || !path.toRealPath().equals(path))
            throw new IOException("Plain actual repository required: " + path);
        return path;
    }
    private static Path absolute(String value) {
        if (value == null || value.isBlank() || value.length() > 4096
                || value.codePoints().anyMatch(point -> point < 32 || point == 127))
            throw new IllegalArgumentException("Bounded plain absolute source path required");
        Path path = Path.of(value);
        if (!path.isAbsolute() || !path.equals(path.normalize()))
            throw new IllegalArgumentException("Canonical absolute source path required");
        return path;
    }
}
