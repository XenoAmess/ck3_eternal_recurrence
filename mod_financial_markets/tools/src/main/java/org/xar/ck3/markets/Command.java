package org.xar.ck3.markets;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import java.io.IOException;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.markets.build.ContentValidator;
import org.xar.ck3.markets.build.SnapshotBuilder;

@QuarkusMain
public final class Command implements QuarkusApplication {
    @Override public int run(String... args) {
        try {
            if (args.length == 0) throw new IllegalArgumentException("expected validate or build");
            Map<String, String> options = new HashMap<>();
            for (int i = 1; i < args.length; i += 2) {
                if (i + 1 >= args.length || !args[i].startsWith("--") || options.putIfAbsent(args[i], args[i + 1]) != null) throw new IllegalArgumentException("invalid/duplicate option");
            }
            Set<String> allowed = switch (args[0]) {
                case "validate" -> Set.of("--source");
                case "build" -> Set.of("--source", "--output", "--revision");
                default -> throw new IllegalArgumentException("unknown command: " + args[0]);
            };
            if (!allowed.containsAll(options.keySet())) throw new IllegalArgumentException("unknown option");
            Path source = Path.of(required(options, "--source"));
            Object result = args[0].equals("validate") ? ContentValidator.validate(source)
                    : SnapshotBuilder.build(source, Path.of(required(options, "--output")), required(options, "--revision"));
            System.out.println(new ObjectMapper().writerWithDefaultPrettyPrinter().writeValueAsString(result));
            return 0;
        } catch (IOException | IllegalArgumentException | IllegalStateException error) {
            System.err.println("XFM FAILED: " + error.getMessage());
            return 1;
        }
    }
    private static String required(Map<String, String> options, String name) {
        String value = options.get(name);
        if (value == null || value.isBlank()) throw new IllegalArgumentException("required " + name);
        return value;
    }
}
