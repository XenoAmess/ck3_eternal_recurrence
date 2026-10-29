package org.xar.ck3.control.g2.m0.integration;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One finite test fixture contract; refs identify retained software fixtures and grant no Game I/O. */
public record M0FixtureConfig(Path repository, Path fixtureRoot, Path outputRoot, ExactRef python,
        ExactRef recommendationOracle, ExactRef originalHttpInput, ExactRef originalHttpExpected,
        ExactRef httpSourceMetadata, ExactRef candidateComposer, ExactRef recommendationAdapter,
        ExactRef formalAdapter, ExactRef clientAdapter, Optional<URI> httpBaseUri) {
    private static final String SCHEMA = "xar.g2-m0-fixture-config/v3";
    private static final int MAX_FILE_BYTES = 8_388_608;
    public M0FixtureConfig {
        Objects.requireNonNull(repository); Objects.requireNonNull(fixtureRoot); Objects.requireNonNull(outputRoot);
        Objects.requireNonNull(python); Objects.requireNonNull(recommendationOracle); Objects.requireNonNull(originalHttpInput);
        Objects.requireNonNull(originalHttpExpected); Objects.requireNonNull(httpSourceMetadata); Objects.requireNonNull(candidateComposer); Objects.requireNonNull(recommendationAdapter);
        Objects.requireNonNull(formalAdapter); Objects.requireNonNull(clientAdapter); Objects.requireNonNull(httpBaseUri);
        for (Path path : new Path[] {repository, fixtureRoot, outputRoot}) absolute(path);
        Path original = Path.of(recommendationOracle.path()); absolute(original);
        if (!original.startsWith(fixtureRoot) || original.equals(fixtureRoot))
            throw new IllegalArgumentException("retained original producer oracle must be a bound software fixture");
        for (ExactRef ref : new ExactRef[] {originalHttpInput, originalHttpExpected, httpSourceMetadata}) {
            Path path = Path.of(ref.path()); absolute(path);
            if (!path.startsWith(fixtureRoot) || path.equals(fixtureRoot)) throw new IllegalArgumentException("software fixture ref escapes the declared fixture root");
        }
        String executable = Path.of(python.path()).getFileName().toString();
        if (!executable.equalsIgnoreCase("python.exe") && !executable.equals("python")) throw new IllegalArgumentException("actual qualified Python interpreter ref required");
    }

    public static M0FixtureConfig fromEnvironment() throws IOException {
        String location = System.getenv("XAR_G2_M0_FIXTURE_CONFIG");
        if (location == null || location.isBlank()) throw new IllegalStateException("actual typed M0 fixture config missing: XAR_G2_M0_FIXTURE_CONFIG");
        ObjectNode value = StrictJson.object(StrictJson.parse(read(Path.of(location), 16_384)), Set.of("schema", "repository", "fixture_root",
                "output_root", "python", "recommendation_oracle", "original_http_input", "original_http_expected", "http_source_metadata", "candidate_composer", "recommendation_adapter", "formal_adapter", "client_adapter", "http_base_uri"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "exact M0 fixture config schema required");
        JsonNode uri = value.get("http_base_uri");
        M0FixtureConfig config = new M0FixtureConfig(path(value, "repository"), path(value, "fixture_root"), path(value, "output_root"),
                ExactRef.fromJson(value.get("python")), ExactRef.fromJson(value.get("recommendation_oracle")),
                ExactRef.fromJson(value.get("original_http_input")), ExactRef.fromJson(value.get("original_http_expected")),
                ExactRef.fromJson(value.get("http_source_metadata")), ExactRef.fromJson(value.get("candidate_composer")), ExactRef.fromJson(value.get("recommendation_adapter")),
                ExactRef.fromJson(value.get("formal_adapter")), ExactRef.fromJson(value.get("client_adapter")), uri.isNull() ? Optional.empty() : Optional.of(URI.create(StrictJson.text(uri))));
        config.verify(); return config;
    }

    public void verify() throws IOException {
        for (Path directory : new Path[] {repository, fixtureRoot, outputRoot}) {
            if (!Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(directory))
                throw new IllegalArgumentException("actual admitted software directory required");
        }
        for (ExactRef ref : new ExactRef[] {python, recommendationOracle, originalHttpInput, originalHttpExpected, httpSourceMetadata, candidateComposer, recommendationAdapter, formalAdapter, clientAdapter}) {
            verifyReference(ref);
        }
    }
    public static void verifyReference(ExactRef ref) throws IOException {
        Path path = Path.of(ref.path()); absolute(path);
        if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(path)
                || ref.bytes() <= 0 || ref.bytes() > MAX_FILE_BYTES || Files.size(path) != ref.bytes())
            throw new IllegalArgumentException("bounded unchanged software reference required");
        byte[] bytes = read(path, MAX_FILE_BYTES);
        if (bytes.length != ref.bytes() || !sha256(bytes).equals(ref.sha256())) throw new IllegalArgumentException("software reference bytes drifted");
    }
    public static String currentTestClasspath() {
        String classpath = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        if (classpath == null || classpath.isBlank()) throw new IllegalStateException("actual current test classpath unavailable");
        if (M0ConsumerRoundTrip.class.getProtectionDomain().getCodeSource() == null)
            throw new IllegalStateException("actual compiled integration CodeSource unavailable");
        try {
            Class<?> domain = Class.forName(M0ConsumerRoundTrip.DOMAIN_MAIN);
            if (domain.getProtectionDomain().getCodeSource() == null) throw new IllegalStateException("actual compiled M0 CodeSource unavailable");
        } catch (ClassNotFoundException error) { throw new IllegalStateException("M0 domain must be compiled in the current reactor", error); }
        return classpath;
    }
    public Path pythonPath() { return Path.of(python.path()); }
    public M0FixtureConfig withHttpBaseUri(URI uri) {
        return new M0FixtureConfig(repository, fixtureRoot, outputRoot, python, recommendationOracle,
                originalHttpInput, originalHttpExpected, httpSourceMetadata, candidateComposer, recommendationAdapter, formalAdapter, clientAdapter, Optional.of(uri));
    }
    public void writeFresh(Path location) throws IOException {
        ObjectNode value = StrictJson.object(); value.put("schema", SCHEMA);
        value.put("repository", repository.toString()); value.put("fixture_root", fixtureRoot.toString());
        value.put("output_root", outputRoot.toString()); value.set("python", python.toJson());
        value.set("recommendation_oracle", recommendationOracle.toJson()); value.set("original_http_input", originalHttpInput.toJson());
        value.set("original_http_expected", originalHttpExpected.toJson()); value.set("http_source_metadata", httpSourceMetadata.toJson());
        value.set("candidate_composer", candidateComposer.toJson());
        value.set("recommendation_adapter", recommendationAdapter.toJson()); value.set("formal_adapter", formalAdapter.toJson());
        value.set("client_adapter", clientAdapter.toJson());
        if (httpBaseUri.isPresent()) value.put("http_base_uri", httpBaseUri.orElseThrow().toString()); else value.putNull("http_base_uri");
        Files.write(location, StrictJson.canonical(value, 16_384), StandardOpenOption.CREATE_NEW);
    }
    private static Path path(ObjectNode value, String key) { return Path.of(StrictJson.text(value.get(key))); }
    private static void absolute(Path path) {
        if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IllegalArgumentException("normalized absolute software path required");
    }
    private static byte[] read(Path path, int maximum) throws IOException {
        try (var stream = Files.newInputStream(path)) {
            byte[] raw = stream.readNBytes(maximum + 1);
            if (raw.length == 0 || raw.length > maximum) throw new IllegalArgumentException("finite actual software input required");
            return raw;
        }
    }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
