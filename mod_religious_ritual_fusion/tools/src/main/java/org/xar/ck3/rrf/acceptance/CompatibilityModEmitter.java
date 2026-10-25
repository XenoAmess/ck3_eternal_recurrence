package org.xar.ck3.rrf.acceptance;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.rrf.Contracts;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.ReleaseBuilder;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FilePin;

/** Pin independent formal mod projections; never merge their content into a fixture. */
public final class CompatibilityModEmitter {
    private CompatibilityModEmitter() { }

    public record Source(String key, String directory,
                         @JsonProperty("source_manifest") FilePin sourceManifest) {
        public Source {
            if (key == null || !key.matches("[a-z][a-z0-9_]{0,47}") || Set.of("product", "fixture").contains(key))
                throw new IllegalArgumentException("safe canonical compatibility key required");
            if (directory == null || !Path.of(directory).isAbsolute() || sourceManifest == null)
                throw new IllegalArgumentException("absolute compatibility source and exact manifest pin required");
        }
    }
    public record Request(@JsonProperty("schema_version") int schemaVersion,
                          @JsonProperty("machine_id") String machineId, List<Source> mods) {
        public Request {
            if (schemaVersion != 1) throw new IllegalArgumentException("compatibility request version 1 required");
            FixtureContracts.machine(machineId);
            mods = List.copyOf(mods);
            if (mods.size() > 16) throw new IllegalArgumentException("at most 16 independent compatibility mods");
            Contracts.unique(mods.stream().map(Source::key).toList());
            Contracts.unique(mods.stream().map(source -> source.sourceManifest().path()).toList());
        }
    }
    public record CompatibilityMod(String key, String directory,
                                   @JsonProperty("source_manifest") FilePin sourceManifest,
                                   Map<String, FilePin> files) {
        public CompatibilityMod { files = Collections.unmodifiableMap(new LinkedHashMap<>(files)); }
    }
    public record CaseInputs(@JsonProperty("compatibility_mods") List<CompatibilityMod> compatibilityMods) {
        public CaseInputs { compatibilityMods = List.copyOf(compatibilityMods); }
    }
    public record Manifest(String schema, @JsonProperty("machine_id") String machineId,
                           @JsonProperty("observed_at_utc") String observedAtUtc,
                           @JsonProperty("case_inputs") CaseInputs caseInputs,
                           @JsonProperty("game_started") boolean gameStarted,
                           @JsonProperty("business_acceptance") String businessAcceptance) { }

    public static Manifest emit(Request request, Path output) throws IOException {
        Path destination = output.toAbsolutePath().normalize();
        if (Files.exists(destination, LinkOption.NOFOLLOW_LINKS)) throw new IllegalArgumentException("unused compatibility output directory required");
        Path ancestor = destination.getParent();
        while (ancestor != null && !Files.exists(ancestor, LinkOption.NOFOLLOW_LINKS)) ancestor = ancestor.getParent();
        if (ancestor == null || !ancestor.toRealPath().equals(ancestor))
            throw new IllegalArgumentException("compatibility output cannot follow a filesystem link");
        List<Path> roots = new ArrayList<>();
        List<CompatibilityMod> mods = new ArrayList<>();
        for (Source source : request.mods()) {
            Path root = ordinary(Path.of(source.directory()), true);
            if (roots.stream().anyMatch(other -> root.startsWith(other) || other.startsWith(root)))
                throw new IllegalArgumentException("compatibility source directories overlap");
            if (destination.startsWith(root) || root.startsWith(destination))
                throw new IllegalArgumentException("compatibility output must be disjoint from sources");
            roots.add(root);
            if (source.sourceManifest().bytes() > 2 * 1024 * 1024)
                throw new IllegalArgumentException("source manifest exceeds bounded size");
            FilePin manifestPin = checked(source.sourceManifest());
            if (manifestPin.bytes() > 2 * 1024 * 1024 || Path.of(manifestPin.path()).startsWith(root))
                throw new IllegalArgumentException("bounded source manifest must remain outside payload");
            JsonNode manifest = Json.read(Files.readAllBytes(Path.of(manifestPin.path())), JsonNode.class);
            JsonNode entries = manifest.get("files");
            if (entries == null || !entries.isArray() || entries.isEmpty() || entries.size() > 4096)
                throw new IllegalArgumentException("release manifest needs its bounded complete files array");
            Map<String, FilePin> files = new LinkedHashMap<>();
            Set<String> folded = new HashSet<>();
            for (JsonNode entry : entries) {
                Set<String> fields = new HashSet<>(); entry.fieldNames().forEachRemaining(fields::add);
                if (!entry.isObject() || !(fields.equals(Set.of("path", "bytes", "sha256")) || fields.equals(Set.of("path", "size", "sha256"))))
                    throw new IllegalArgumentException("release file requires path, size/bytes and sha256 only");
                JsonNode name = entry.get("path"), digest = entry.get("sha256"), size = entry.has("bytes") ? entry.get("bytes") : entry.get("size");
                if (!name.isTextual() || !digest.isTextual() || !size.isIntegralNumber() || !size.canConvertToLong() || size.longValue() < 0)
                    throw new IllegalArgumentException("strict integral release file size and string path/SHA required");
                String relative = name.textValue();
                safeRelative(relative);
                if (!folded.add(relative.toLowerCase(java.util.Locale.ROOT))) throw new IllegalArgumentException("repeated compatibility path");
                Path path = ordinary(root.resolve(relative), false);
                FilePin pin = checked(new FilePin(path.toString(), size.longValue(), digest.textValue()));
                files.put(relative, pin);
            }
            if (!files.containsKey("descriptor.mod")) throw new IllegalArgumentException("compatibility descriptor.mod missing");
            Set<String> actual = new HashSet<>();
            try (var paths = Files.walk(root)) {
                for (Path path : paths.toList()) {
                    ordinary(path, Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS));
                    if (Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) actual.add(root.relativize(path).toString().replace('\\', '/'));
                }
            }
            if (!actual.equals(files.keySet())) throw new IllegalArgumentException("release manifest differs from actual compatibility file closure");
            mods.add(new CompatibilityMod(source.key(), root.toString(), manifestPin, files));
        }
        Manifest result = new Manifest("ck3-mod-acceptance-compatibility-mods-v1", request.machineId(), Instant.now().toString(),
                new CaseInputs(mods), false, "NOT_ASSESSED");
        Files.createDirectories(destination);
        Files.write(destination.resolve("compatibility-mods.json"), Json.write(result), StandardOpenOption.CREATE_NEW);
        return result;
    }

    public static int run(String[] args) throws IOException {
        if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output"))
            throw new IllegalArgumentException("compatibility-mods --inputs strictRequest.json --output NEWdisjointdir");
        Manifest manifest = emit(Json.read(Files.readAllBytes(Path.of(args[1])), Request.class), Path.of(args[3]));
        System.out.println(new String(Json.write(manifest), StandardCharsets.UTF_8));
        return 0;
    }

    private static Path ordinary(Path path, boolean directory) throws IOException {
        if (!path.isAbsolute() || !path.normalize().equals(path) || Files.isSymbolicLink(path)
                || !path.toRealPath().equals(path) || (directory ? !Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS) : !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)))
            throw new IllegalArgumentException("canonical ordinary compatibility path required: " + path);
        return path;
    }
    private static FilePin checked(FilePin expected) throws IOException {
        Path path = ordinary(Path.of(expected.path()), false);
        byte[] bytes = Files.readAllBytes(path);
        if (bytes.length != expected.bytes() || !ReleaseBuilder.sha256(bytes).equals(expected.sha256()))
            throw new IllegalArgumentException("compatibility source pin changed: " + path);
        return expected;
    }
    private static void safeRelative(String value) {
        if (value.isEmpty() || value.contains("\\") || value.contains(":") || value.startsWith("/")
                || java.util.Arrays.stream(value.split("/", -1)).anyMatch(part -> part.isEmpty() || part.equals(".") || part.equals("..")))
            throw new IllegalArgumentException("canonical relative compatibility file required");
    }
}
