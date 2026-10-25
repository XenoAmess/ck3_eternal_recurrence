package org.xar.ck3.dynastic;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.dynastic.acceptance.FixtureEmitter;
import org.xar.ck3.dynastic.acceptance.SharedRuntimeComposer;
import org.xar.ck3.dynastic.artwork.SectArtworkImporter;
import org.xar.ck3.dynastic.release.ReleaseBuilder;
import org.xar.ck3.dynastic.release.ReleaseProduct;
import org.xar.ck3.dynastic.release.StaticValidation;

/** Local development command host. No Java file is shipped in the CK3 runtime package. */
@QuarkusMain
public final class ReleaseCommand implements QuarkusApplication {
    private static final Set<String> OPTIONS = Set.of("--source", "--repo-root", "--output", "--manifest", "--workshop-item-id", "--git-tag");
    private static final ObjectMapper JSON = new ObjectMapper();

    @Override
    public int run(String... args) {
        try {
            if (args.length == 0) throw new IllegalArgumentException("expected validate, build, verify, check, fixture, runtime or artwork");
            if (args[0].equals("artwork")) {
                if (args.length != 3) throw new IllegalArgumentException("expected artwork <uploaded-zip> <mod-source>");
                System.out.println(JSON.writerWithDefaultPrettyPrinter().writeValueAsString(
                        SectArtworkImporter.importArchive(Path.of(args[1]), Path.of(args[2]))));
                return 0;
            }
            if (args[0].equals("fixture")) return FixtureEmitter.run(Arrays.copyOfRange(args, 1, args.length));
            if (args[0].equals("runtime")) return SharedRuntimeComposer.run(Arrays.copyOfRange(args, 1, args.length));
            ParsedOptions parsed = parse(Arrays.copyOfRange(args, 1, args.length));
            Map<String, String> options = parsed.values();
            Path source = Path.of(options.getOrDefault("--source", "mod_dynastic_esotericism")).toAbsolutePath().normalize();
            Path repository = Path.of(options.getOrDefault("--repo-root", source.getParent().toString())).toAbsolutePath().normalize();
            ReleaseProduct product = ReleaseProduct.official(source, parsed.localizationMode());
            ReleaseBuilder builder = new ReleaseBuilder();
            Object result;
            switch (args[0]) {
                case "validate" -> {
                    only(options, Set.of("--source", "--repo-root"));
                    result = StaticValidation.validate(product, repository);
                }
                case "verify" -> {
                    only(options, Set.of("--source", "--output", "--manifest", "--repo-root"));
                    result = builder.verify(product, Path.of(required(options, "--output")), Path.of(required(options, "--manifest")));
                }
                case "build" -> {
                    only(options, Set.of("--source", "--repo-root", "--output", "--workshop-item-id", "--git-tag"));
                    ReleaseBuilder.BuildResult built = builder.build(product, repository, Path.of(required(options, "--output")),
                            revision(repository), options.get("--git-tag"), options.get("--workshop-item-id"));
                    result = new BuildReport(built.staging().toString(), built.manifest().toString(), built.archive().toString(),
                            built.payload().files().size(), built.payload().gitSha(), built.payload().gitTag());
                }
                case "check" -> {
                    only(options, Set.of("--source", "--repo-root", "--output", "--workshop-item-id"));
                    result = builder.check(product, repository, Path.of(required(options, "--output")), revision(repository), options.get("--workshop-item-id"));
                }
                default -> throw new IllegalArgumentException("unknown command: " + args[0]);
            }
            System.out.println(JSON.writerWithDefaultPrettyPrinter().writeValueAsString(result));
            return 0;
        } catch (IOException | IllegalArgumentException | InterruptedException error) {
            if (error instanceof InterruptedException) Thread.currentThread().interrupt();
            System.err.println("DES RELEASE FAILED: " + error.getMessage());
            return 1;
        }
    }

    public record BuildReport(String staging, String manifest, String archive, int fileCount, String gitSha, String gitTag) { }

    private record ParsedOptions(Map<String, String> values, ReleaseProduct.LocalizationMode localizationMode) { }

    private static ParsedOptions parse(String[] args) {
        Map<String, String> result = new HashMap<>();
        ReleaseProduct.LocalizationMode mode = ReleaseProduct.LocalizationMode.DEVELOPMENT;
        for (int index = 0; index < args.length;) {
            if (args[index].equals("--release-localization")) {
                if (mode == ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION) throw new IllegalArgumentException("duplicate --release-localization");
                mode = ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION;
                index++;
                continue;
            }
            if (index + 1 >= args.length || !OPTIONS.contains(args[index]) || args[index + 1].isEmpty()
                    || result.putIfAbsent(args[index], args[index + 1]) != null) {
                throw new IllegalArgumentException("unknown, duplicate or empty option: " + args[index]);
            }
            index += 2;
        }
        return new ParsedOptions(Map.copyOf(result), mode);
    }

    private static String required(Map<String, String> options, String key) {
        String result = options.get(key);
        if (result == null) throw new IllegalArgumentException("required option: " + key);
        return result;
    }

    private static void only(Map<String, String> options, Set<String> allowed) {
        if (!allowed.containsAll(options.keySet())) throw new IllegalArgumentException("option is not applicable to this command");
    }

    private static String revision(Path repository) throws IOException, InterruptedException {
        Process process = new ProcessBuilder("git", "-C", repository.toString(), "rev-parse", "HEAD").redirectErrorStream(true).start();
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8).strip();
        if (process.waitFor() != 0 || !ReleaseProduct.REVISION.matcher(output).matches()) throw new IllegalArgumentException("cannot read source Git revision: " + output);
        return output;
    }
}
