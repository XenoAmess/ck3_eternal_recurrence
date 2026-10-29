package org.xar.ck3.control.wave3.governance.capture;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

/** Current reference-source metadata only; this never creates oracle results or native observations. */
public final class ReferenceSourceClosureCapture {
    public static final String SCHEMA = "xar.education-service-source-pins/v2";
    public static final int MAX_COMPRESSED = 131072;
    public static final int MAX_EXPANDED = 1048576;
    public enum Role { PRODUCTION, REFERENCE, INTERPRETER_BOOTSTRAP }
    public record SourceRef(String path, long bytes, String sha256, Role role) {
        public SourceRef {
            if (path == null || !Path.of(path).isAbsolute() || bytes < 0 || bytes > (8L << 20)
                    || sha256 == null || !sha256.matches("[0-9a-f]{64}") || role == null) {
                throw new IllegalArgumentException("Exact typed source reference required");
            }
        }
    }
    public record Closure(String schema, String machineId, String repository, String observedAtUtc,
            List<SourceRef> files) {
        public Closure {
            if (!SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
                    || repository == null || !Path.of(repository).isAbsolute()) {
                throw new IllegalArgumentException("Versioned reference closure identity required");
            }
            Instant.parse(observedAtUtc);
            files = List.copyOf(files);
            if (files.isEmpty() || files.size() > 4096
                    || files.stream().map(SourceRef::path).distinct().count() != files.size()) {
                throw new IllegalArgumentException("Finite distinct source closure required");
            }
        }
    }
    private static final String PRODUCTION = "ck3_autonomous_player/src/xar_autoplayer";
    private static final String BOOTSTRAP = "tools/.venv/Lib/site-packages/win32/lib/pywin32_bootstrap.py";
    private static final List<String> REFERENCES = List.of(
            "ck3_autonomous_player/tests/unit/test_family_guardian_negative_cadence_v1.py",
            "ck3_autonomous_player/tests/unit/test_service_family_guardian_negative_cadence_v1.py",
            "ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json",
            "ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py",
            "ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py",
            "tools/ck3_live_run_id.py");
    private static final ObjectMapper JSON = JsonMapper.builder()
            .enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
            .enable(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES)
            .disable(MapperFeature.ALLOW_COERCION_OF_SCALARS)
            .propertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE).build();
    private ReferenceSourceClosureCapture() { }

    public static Closure observe(Path repository, String machineId) throws IOException {
        Path root = canonicalDirectory(repository);
        List<SourceRef> refs = new ArrayList<>();
        for (Path file : productionInventory(root)) refs.add(measure(file, Role.PRODUCTION));
        for (String relative : REFERENCES) refs.add(measure(root.resolve(relative), Role.REFERENCE));
        refs.add(measure(root.resolve(BOOTSTRAP), Role.INTERPRETER_BOOTSTRAP));
        refs.sort(Comparator.comparing(SourceRef::path));
        return new Closure(SCHEMA, machineId, root.toString(), Instant.now().toString(), refs);
    }

    public static SourceRef writeNew(Path repository, String machineId, Path output) throws IOException {
        Closure closure = observe(repository, machineId);
        byte[] expanded = JSON.writeValueAsBytes(closure);
        require(expanded.length <= MAX_EXPANDED, "Expanded closure exceeds bound");
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(buffer)) { gzip.write(expanded); }
        byte[] compressed = buffer.toByteArray();
        require(compressed.length <= MAX_COMPRESSED, "Compressed closure exceeds bound");
        Path target = output.toAbsolutePath().normalize();
        require(output.equals(target) && target.getParent() != null
                && target.getParent().toRealPath().equals(target.getParent())
                && !target.startsWith(Path.of(closure.repository()))
                && !Files.exists(target, LinkOption.NOFOLLOW_LINKS), "New external metadata output required");
        Files.write(target, compressed, StandardOpenOption.CREATE_NEW);
        SourceRef result = measure(target, Role.REFERENCE);
        require(verify(repository, target, result.sha256()).equals(closure), "Observed closure changed before publication");
        return result;
    }

    public static Closure verify(Path repository, Path compressedPath, String expectedSha256) throws IOException {
        Path root = canonicalDirectory(repository);
        byte[] compressed = readBounded(compressedPath, MAX_COMPRESSED);
        require(digest(compressed).equals(expectedSha256), "Exact reference closure bytes changed");
        byte[] expanded;
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            expanded = gzip.readNBytes(MAX_EXPANDED + 1);
            require(expanded.length <= MAX_EXPANDED && gzip.read() == -1, "Expanded reference closure exceeds bound");
        }
        JsonNode tree = JSON.readTree(expanded);
        require(tree != null && tree.isObject() && tree.path("files").isArray(), "Structured reference closure required");
        for (JsonNode row : tree.path("files")) {
            require(row.isObject() && row.size() == 4 && row.path("bytes").isIntegralNumber()
                    && row.path("bytes").canConvertToLong(), "Source size must be an integer token");
        }
        Closure closure = JSON.treeToValue(tree, Closure.class);
        require(root.toString().equals(closure.repository()), "Reference repository differs");
        Set<Path> actualProduction = new HashSet<>();
        Set<Path> actualReferences = new HashSet<>();
        Set<Path> actualBootstrap = new HashSet<>();
        for (SourceRef ref : closure.files()) {
            Path file = Path.of(ref.path());
            require(file.equals(file.toAbsolutePath().normalize()) && file.startsWith(root)
                    && !Files.isSymbolicLink(file) && file.toRealPath().equals(file), "Canonical repository source required");
            require(measure(file, ref.role()).equals(ref), "Current reference source drift: " + file);
            switch (ref.role()) {
                case PRODUCTION -> require(actualProduction.add(file), "Duplicate production source");
                case REFERENCE -> require(actualReferences.add(file), "Duplicate reference source");
                case INTERPRETER_BOOTSTRAP -> require(actualBootstrap.add(file), "Duplicate bootstrap source");
            }
        }
        Set<Path> expectedReferences = new HashSet<>();
        for (String relative : REFERENCES) expectedReferences.add(root.resolve(relative));
        require(actualProduction.equals(productionInventory(root)), "Complete production source inventory changed");
        require(actualReferences.equals(expectedReferences), "Explicit oracle reference inventory differs");
        require(actualBootstrap.equals(Set.of(root.resolve(BOOTSTRAP))), "Exact interpreter bootstrap source required");
        return closure;
    }

    private static Set<Path> productionInventory(Path root) throws IOException {
        Path production = canonicalDirectory(root.resolve(PRODUCTION));
        Set<Path> result = new HashSet<>();
        try (var walk = Files.walk(production)) {
            for (Path file : walk.toList()) {
                require(!Files.isSymbolicLink(file), "Production source links rejected");
                if (Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS) && file.toString().endsWith(".py")) {
                    require(file.toRealPath().equals(file) && result.add(file), "Canonical unique production source required");
                    require(result.size() <= 4089, "Production source inventory exceeds bound");
                }
            }
        }
        require(!result.isEmpty(), "Complete production source inventory required");
        return Set.copyOf(result);
    }
    private static Path canonicalDirectory(Path value) throws IOException {
        Path path = value.toAbsolutePath().normalize();
        require(value.equals(path) && Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)
                && path.toRealPath().equals(path), "Canonical existing repository directory required");
        return path;
    }
    private static SourceRef measure(Path path, Role role) throws IOException {
        require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(path), "Regular exact source required: " + path);
        byte[] bytes = readBounded(path, 8 << 20);
        return new SourceRef(path.toString(), bytes.length, digest(bytes), role);
    }
    private static byte[] readBounded(Path path, int maximum) throws IOException {
        require(Files.size(path) <= maximum, "Source metadata/input exceeds bound");
        try (var input = Files.newInputStream(path)) {
            byte[] bytes = input.readNBytes(maximum + 1);
            require(bytes.length <= maximum, "Source metadata/input grew beyond bound");
            return bytes;
        }
    }
    private static String digest(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static void require(boolean condition, String message) throws IOException {
        if (!condition) throw new IOException(message);
    }
    public static void main(String[] args) throws IOException {
        if (args.length != 4) throw new IllegalArgumentException("repository existing-python new-metadata-output verified-machine-id");
        Path root = Path.of(args[0]).toRealPath();
        require(Path.of(args[1]).toRealPath().equals(root.resolve("tools/.venv/Scripts/python.exe")), "Exact repository interpreter required");
        SourceRef result = writeNew(root, args[3], Path.of(args[2]));
        System.out.println(JSON.writeValueAsString(result));
    }
}
