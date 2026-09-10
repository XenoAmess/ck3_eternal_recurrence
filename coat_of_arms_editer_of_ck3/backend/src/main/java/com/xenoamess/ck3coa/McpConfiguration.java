package com.xenoamess.ck3coa;

import io.smallrye.config.ConfigMapping;
import io.smallrye.config.WithDefault;
import java.time.Duration;
import java.util.Optional;

@ConfigMapping(prefix = "coat-of-arms.mcp")
public interface McpConfiguration {
    @WithDefault("py")
    String pythonCommand();

    Optional<String> pythonPath();

    @WithDefault("native-headless")
    String driver();

    Optional<String> stateDirectory();

    Optional<String> gameDirectory();

    Optional<String> userDirectory();

    Optional<String> pipeName();

    @WithDefault("15S")
    Duration requestTimeout();
}
