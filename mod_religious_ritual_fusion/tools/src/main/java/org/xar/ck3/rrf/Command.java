package org.xar.ck3.rrf;

import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.rrf.acceptance.FixtureEmitter;
import org.xar.ck3.rrf.acceptance.CompatibilityModEmitter;
import org.xar.ck3.rrf.qualification.SourceQualificationEmitter;
import org.xar.ck3.rrf.save.SaveInspector;
import org.xar.ck3.rrf.Contracts.Catalog;

/** Quarkus CLI only. CK3 consumes generated scripts and never depends on this process. */
@QuarkusMain
public final class Command implements QuarkusApplication {
    @Override public int run(String... args) {
        try {
            if (args.length == 0) throw new IllegalArgumentException("expected generate, validate, build, verify, fixture or inspect-save");
            if (args[0].equals("fixture")) return FixtureEmitter.run(java.util.Arrays.copyOfRange(args, 1, args.length));
            if (args[0].equals("inspect-save")) return SaveInspector.run(java.util.Arrays.copyOfRange(args, 1, args.length));
            if (args[0].equals("compatibility-mods")) return CompatibilityModEmitter.run(java.util.Arrays.copyOfRange(args, 1, args.length));
            if (args[0].equals("source-qualifications")) return SourceQualificationEmitter.run(java.util.Arrays.copyOfRange(args, 1, args.length));
            Map<String, String> options = options(args);
            Path source = Path.of(options.getOrDefault("--source", "mod_religious_ritual_fusion")).toAbsolutePath().normalize();
            Object result;
            switch (args[0]) {
                case "generate" -> {
                    only(options, Set.of("--source", "--game", "--machine-id", "--catalog"));
                    if (options.containsKey("--catalog") && (options.containsKey("--game") || options.containsKey("--machine-id"))) throw new IllegalArgumentException("catalog snapshot cannot combine with game/machine options");
                    Catalog catalog;
                    if (options.containsKey("--catalog")) catalog = Json.read(Files.readAllBytes(Path.of(options.get("--catalog"))), Catalog.class);
                    else {
                        Path game = options.containsKey("--game") ? Path.of(options.get("--game")) : source.getParent().resolve("Crusader Kings III/game");
                        catalog = new CatalogReader().read(game, required(options, "--machine-id"));
                    }
                    result = new CatalogGenerator().generate(catalog, source);
                }
                case "validate" -> { only(options, Set.of("--source")); result = ContentValidator.validate(source); }
                case "build" -> { only(options, Set.of("--source", "--output", "--revision", "--machine-id", "--workshop-item-id", "--git-tag")); result = new ReleaseBuilder().build(source, Path.of(required(options, "--output")), new Contracts.ReleaseIdentity(required(options, "--workshop-item-id"), required(options, "--git-tag"), required(options, "--revision")), new Contracts.Provenance(Contracts.ProvenanceKind.OBSERVED_MACHINE, required(options, "--machine-id"), java.time.Instant.now().toString())); }
                case "verify" -> { only(options, Set.of("--source", "--output", "--manifest")); result = new ReleaseBuilder().verify(source, Path.of(required(options, "--output")), Path.of(required(options, "--manifest"))); }
                default -> throw new IllegalArgumentException("unknown command: " + args[0]);
            }
            System.out.println(new String(Json.write(result), StandardCharsets.UTF_8)); return 0;
        } catch (IOException | IllegalArgumentException error) {
            System.err.println("RRF FAILED: " + error.getMessage()); return 1;
        }
    }
    private static Map<String, String> options(String[] args) {
        Map<String, String> result = new LinkedHashMap<>();
        for (int i = 1; i < args.length; i += 2) {
            if (i + 1 == args.length || !args[i].startsWith("--") || args[i + 1].isBlank() || result.putIfAbsent(args[i], args[i + 1]) != null) throw new IllegalArgumentException("unknown/duplicate/missing option value: " + args[i]);
        }
        return Map.copyOf(result);
    }
    private static String required(Map<String, String> values, String key) { String value = values.get(key); if (value == null) throw new IllegalArgumentException("required: " + key); return value; }
    private static void only(Map<String, String> values, Set<String> allowed) { if (!allowed.containsAll(values.keySet())) throw new IllegalArgumentException("option is not applicable"); }
}
