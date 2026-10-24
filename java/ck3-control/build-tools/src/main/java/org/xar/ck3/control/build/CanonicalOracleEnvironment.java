package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;

/** Packaged facade for the sole engine owned by the standalone bootstrap source. */
public final class CanonicalOracleEnvironment {
    private CanonicalOracleEnvironment() { }

    public record Inputs(String python, String repositoryRoot) {
        public Inputs {
            new CiBootstrap.OracleEnvironment.Inputs(python, repositoryRoot);
        }
    }

    public static Inputs require(Map<String, String> environment) throws IOException {
        var inputs = CiBootstrap.OracleEnvironment.require(environment);
        return new Inputs(inputs.python(), inputs.repositoryRoot());
    }

    public static Map<String, String> bind(Path repository, Path python, Map<String, String> inherited) throws IOException {
        return CiBootstrap.OracleEnvironment.bind(repository, python, inherited);
    }
}
