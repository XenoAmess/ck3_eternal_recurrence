package org.xar.ck3.markets.acceptance;

import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import java.io.IOException;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** Optional named Quarkus entry; the existing default validate/build command is unchanged. */
@QuarkusMain(name = "acceptance")
public final class AcceptanceCommand implements QuarkusApplication {
    @Override public int run(String... args) {
        try {
            if (args.length != 9 || !args[0].equals("emit")) throw new IllegalArgumentException("expected emit --repo-root --output --machine-id --inputs");
            Map<String, String> options = new LinkedHashMap<>();
            Set<String> allowed = Set.of("--repo-root", "--output", "--machine-id", "--inputs");
            for (int i = 1; i < args.length; i += 2) {
                if (!allowed.contains(args[i]) || args[i + 1].isBlank() || options.putIfAbsent(args[i], args[i + 1]) != null)
                    throw new IllegalArgumentException("invalid or duplicate fixture option");
            }
            if (!options.keySet().equals(allowed)) throw new IllegalArgumentException("all four fixture options required");
            var result = FixtureEmitter.emit(Path.of(options.get("--repo-root")), Path.of(options.get("--output")),
                    options.get("--machine-id"), FixtureEmitter.readInput(Path.of(options.get("--inputs"))));
            System.out.println(FixtureEmitter.JSON.writerWithDefaultPrettyPrinter().writeValueAsString(result));
            return 0;
        } catch (IOException | IllegalArgumentException error) {
            System.err.println("XFM FIXTURE FAILED: " + error.getMessage());
            return 1;
        }
    }
}
