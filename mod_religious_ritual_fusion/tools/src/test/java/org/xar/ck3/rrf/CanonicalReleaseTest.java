package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Contracts.Manifest;
import org.xar.ck3.rrf.Contracts.Product;
import org.xar.ck3.rrf.Contracts.Provenance;
import org.xar.ck3.rrf.Contracts.ProvenanceKind;
import org.xar.ck3.rrf.Contracts.ReleaseIdentity;

/** Actual Java release producer into the unchanged canonical shared cache consumers. */
final class CanonicalReleaseTest {
    @TempDir Path directory;
    private static final String ITEM = "3826756673";
    private static final String TAG = "synthetic-release-v0.1.0-alpha";

    @Test void actualProducerPassesCanonicalManifestAndExactCacheConsumers() throws IOException, InterruptedException {
        Path source = source();
        ReleaseBuilder.BuildResult built = new ReleaseBuilder().build(source, directory.resolve("staging"),
                new ReleaseIdentity(ITEM, TAG, "e".repeat(40)), synthetic());
        byte[] bytes = Files.readAllBytes(Path.of(built.manifest()));
        Manifest manifest = Json.read(bytes, Manifest.class);
        assertEquals(manifest, Json.read(Json.write(manifest), Manifest.class));
        assertEquals(2, manifest.formatVersion()); assertEquals(ITEM, manifest.workshopItemId());
        assertEquals(TAG, manifest.gitTag()); assertEquals("e".repeat(40), manifest.gitSha());
        assertEquals(75, manifest.files().size());
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Path localPython = repository.resolve("tools/.venv/Scripts/python.exe");
        String python = Files.isRegularFile(localPython) ? localPython.toString() : "python";
        String script = """
                import json, pathlib, runpy, sys
                sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / 'tools'))
                adapter = runpy.run_path(str(pathlib.Path(sys.argv[1]) / 'tools/ck3_mod_acceptance_cases/workshop_cache_adapter.py'))
                from verify_zhongguo_workshop_cache import _verify_cache
                manifest = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
                adapter['validate_manifest'](manifest, sys.argv[4])
                records, descriptor = _verify_cache(pathlib.Path(sys.argv[3]), manifest, 'canonical')
                assert len(records) == 75 and descriptor['policy'] == 'canonical'
                try:
                    adapter['validate_manifest'](manifest, '1')
                except ValueError:
                    pass
                else:
                    raise AssertionError('wrong canonical Workshop item accepted')
                next(row for row in manifest['files'] if row['path'] == 'thumbnail.png')['sha256'] = '0' * 64
                try:
                    _verify_cache(pathlib.Path(sys.argv[3]), manifest, 'canonical')
                except (ValueError, RuntimeError):
                    pass
                else:
                    raise AssertionError('changed formal hash accepted')
                print('CANONICAL_PRODUCER_CONSUMER_PASS files=75')
                """;
        String output = execute(List.of(python, "-B", "-X", "utf8", "-c", script, repository.toString(), built.manifest(), built.staging(), ITEM));
        assertTrue(output.contains("CANONICAL_PRODUCER_CONSUMER_PASS files=75"), output);
    }

    @Test void canonicalJsonRejectsCoercionsMissingFieldsLegacyAliasesAndInvalidIdentity() throws IOException {
        Manifest valid = new Manifest(2, ITEM, TAG, "e".repeat(40), "fixture", "0.1.0-alpha", synthetic(),
                List.of(new Contracts.FileEntry("descriptor.mod", 0, "0".repeat(64))));
        String text = new String(Json.write(valid), StandardCharsets.UTF_8);
        for (String wrong : List.of("true", "2.0", "\"2\"", "null", "1", "3")) {
            assertThrows(IOException.class, () -> Json.read(text.replace("\"format_version\" : 2", "\"format_version\" : " + wrong).getBytes(StandardCharsets.UTF_8), Manifest.class));
        }
        for (String wrong : List.of("3826756673", "true", "3826756673.0", "null", "\"\"", "\"03826756673\"", "\"0\"")) {
            assertThrows(IOException.class, () -> Json.read(text.replace("\"workshop_item_id\" : \"" + ITEM + "\"", "\"workshop_item_id\" : " + wrong).getBytes(StandardCharsets.UTF_8), Manifest.class));
        }
        for (String field : List.of("format_version", "workshop_item_id", "git_tag", "git_sha")) {
            assertThrows(IOException.class, () -> Json.read(text.replaceAll("(?m)^  \\\"" + field + "\\\" : .*\\n", "").getBytes(StandardCharsets.UTF_8), Manifest.class));
        }
        assertThrows(IOException.class, () -> Json.read(text.replace("format_version", "schemaVersion").getBytes(StandardCharsets.UTF_8), Manifest.class));
        assertThrows(IOException.class, () -> Json.read(text.replace(TAG, "").getBytes(StandardCharsets.UTF_8), Manifest.class));
        assertThrows(IOException.class, () -> Json.read(text.replace("e".repeat(40), "short").getBytes(StandardCharsets.UTF_8), Manifest.class));
        assertThrows(IllegalArgumentException.class, () -> new Manifest(2, ITEM, TAG, "e".repeat(40), "fixture", "0.1.0-alpha", synthetic(), List.of()));
        assertEquals(1, new Command().run("build", "--output", directory.resolve("missing-identity").toString(), "--revision", "e".repeat(40), "--machine-id", "synthetic-fixture"));
        assertFalse(Files.exists(directory.resolve("missing-identity")));
    }

    @Test void observedReleaseRequiresActualMatchingGitTagAndHeadAndVerifierRechecksTag() throws IOException, InterruptedException {
        Path source = source();
        git(source, "init", "--quiet"); git(source, "add", "--all");
        git(source, "-c", "user.name=Synthetic fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "Synthetic producer fixture");
        String revision = git(source, "rev-parse", "HEAD").strip(); git(source, "tag", TAG);
        ReleaseBuilder builder = new ReleaseBuilder();
        Provenance observedBranch = new Provenance(ProvenanceKind.OBSERVED_MACHINE, "synthetic-git-branch-fixture", "2026-10-25T00:00:00Z");
        assertThrows(IllegalArgumentException.class, () -> builder.build(source, directory.resolve("wrong-sha"), new ReleaseIdentity(ITEM, TAG, "0".repeat(40)), observedBranch));
        assertFalse(Files.exists(directory.resolve("wrong-sha")));
        assertThrows(IllegalArgumentException.class, () -> builder.build(source, directory.resolve("missing-tag"), new ReleaseIdentity(ITEM, "absent-tag", revision), observedBranch));
        ReleaseIdentity identity = new ReleaseIdentity(ITEM, TAG, revision);
        ReleaseBuilder.BuildResult built = builder.build(source, directory.resolve("tagged-staging"), identity, observedBranch);
        assertEquals(revision, builder.verify(source, Path.of(built.staging()), Path.of(built.manifest())).gitSha());
        Files.writeString(source.resolve("docs-note.txt"), "synthetic next commit"); git(source, "add", "docs-note.txt");
        git(source, "-c", "user.name=Synthetic fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "Synthetic successor");
        assertThrows(IllegalArgumentException.class, () -> builder.build(source, directory.resolve("old-head"), identity, observedBranch));
        git(source, "tag", "--force", TAG);
        assertThrows(IllegalArgumentException.class, () -> builder.verify(source, Path.of(built.staging()), Path.of(built.manifest())));
    }

    private Path source() throws IOException {
        Path actual = Path.of(System.getProperty("rrf.source")); Path source = directory.resolve("source");
        Product product = Json.read(Files.readAllBytes(actual.resolve("tools/product.json")), Product.class);
        for (String relative : product.runtimeFiles()) {
            Path target = source.resolve(relative); Files.createDirectories(target.getParent()); Files.copy(actual.resolve(relative), target);
        }
        Files.createDirectories(source.resolve("tools")); Files.write(source.resolve("tools/product.json"), Json.write(product));
        Catalog catalog = Json.read(Files.readAllBytes(actual.resolve("catalog/generated-catalog.json")), Catalog.class);
        new CatalogGenerator().generate(catalog, source); return source;
    }
    private static Provenance synthetic() { return new Provenance(ProvenanceKind.SYNTHETIC_FIXTURE, "synthetic-canonical-release-machine", "2026-10-25T00:00:00Z"); }
    private static String git(Path source, String... args) throws IOException, InterruptedException {
        List<String> command = new ArrayList<>(List.of("git", "-C", source.toString())); command.addAll(List.of(args)); return execute(command);
    }
    private static String execute(List<String> command) throws IOException, InterruptedException {
        Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
        assertTrue(process.waitFor(30, TimeUnit.SECONDS), "bounded consumer timed out");
        String output = new String(process.getInputStream().readNBytes(65_537), StandardCharsets.UTF_8);
        assertTrue(output.length() <= 65_536, "bounded consumer output exceeded"); assertEquals(0, process.exitValue(), output); return output;
    }
}
