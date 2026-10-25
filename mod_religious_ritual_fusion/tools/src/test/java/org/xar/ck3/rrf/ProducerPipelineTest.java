package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Contracts.Product;

/** Exercises the actual native reader, generator, validation, allowlist staging and independent verifier. */
final class ProducerPipelineTest {
    @TempDir Path directory;

    @Test void realProducerToEveryConsumerAndManifest() throws IOException {
        Path source = createProduct();
        Catalog catalog = catalog();
        Catalog decoded = Json.read(Json.write(catalog), Catalog.class); assertEquals(catalog, decoded);
        CatalogGenerator.Generation generation = new CatalogGenerator().generate(decoded, source);
        assertEquals(6, generation.definitionCount()); assertEquals(1, generation.blockedCount());
        ContentValidator.Validation validation = ContentValidator.validate(source);
        assertEquals(6, validation.definitions());
        String initialize = Files.readString(source.resolve("common/scripted_effects/rrf_catalog_initialize_00.txt"));
        assertTrue(initialize.contains("rrf_candidate_doctrines")); assertTrue(initialize.contains("rite_has_doctrine = doctrine_a"));
        String validate = Files.readString(source.resolve("common/scripted_effects/rrf_catalog_validate_00.txt"));
        assertTrue(validate.contains("scope:actor = { has_dlc_feature = royal_court }"));
        assertTrue(validate.contains("scope:rrf_projection_faith")); assertTrue(validate.contains("is_in_list = selected_doctrines"));
        assertTrue(validate.contains("scope:actor = { is_landed = yes }"));
        assertTrue(validate.contains("add_character_flag = rrf_invalid_selection"));
        assertFalse(validate.contains("remove_character_flag"));
        ReleaseBuilder builder = new ReleaseBuilder();
        Contracts.Provenance provenance = new Contracts.Provenance(Contracts.ProvenanceKind.SYNTHETIC_FIXTURE, "synthetic-fixture-machine", "2026-10-24T00:00:00Z");
        ReleaseBuilder.BuildResult result = builder.build(source, directory.resolve("staging"), releaseIdentity("a"), provenance);
        assertEquals(validation.runtimeFiles(), result.files());
        assertEquals(validation.runtimeFiles(), builder.verify(source, Path.of(result.staging()), Path.of(result.manifest())).files());
        assertFalse(Files.exists(Path.of(result.staging()).resolve("tools")));
        assertFalse(Files.exists(Path.of(result.staging()).resolve("catalog")));
        assertThrows(IllegalArgumentException.class, () -> builder.build(source, directory.resolve("staging"), releaseIdentity("a"), provenance));
        Files.writeString(Path.of(result.staging()).resolve("extra.txt"), "unlisted");
        assertThrows(IllegalArgumentException.class, () -> builder.verify(source, Path.of(result.staging()), Path.of(result.manifest())));
        Files.delete(Path.of(result.staging()).resolve("extra.txt"));
        Files.writeString(Path.of(result.staging()).resolve("common/scripted_effects/rrf_catalog_dispatch_00.txt"), "tampered");
        assertThrows(IllegalArgumentException.class, () -> builder.verify(source, Path.of(result.staging()), Path.of(result.manifest())));
    }

    @Test void deterministicGeneratorAndMalformedSources() throws IOException {
        Catalog catalog = catalog(); CatalogGenerator generator = new CatalogGenerator();
        assertEquals(generator.render(catalog), generator.render(Json.read(Json.write(catalog), Catalog.class)));
        assertTrue(catalog.definitions().stream().filter(d -> d.id().equals("tenet_bad")).findFirst().orElseThrow().blockedReasons().contains("unsupported_prev_context"));
        assertThrows(IllegalArgumentException.class, () -> Clausewitz.parse("a = { x = \"bad"));
        assertThrows(IllegalArgumentException.class, () -> Clausewitz.parse("a = { x = yes"));
        assertThrows(IllegalArgumentException.class, () -> Clausewitz.parse("}"));
        Clausewitz.Block parsed = Clausewitz.parse("\ufeffa={ x=yes # comment\n x=no text=\"a # {} b\\\" c\" list={ a b } }");
        assertEquals(2, parsed.block("a").named("x").size());
        assertEquals(parsed, Clausewitz.parse(parsed.body()));
    }

    @Test void strictJsonRejectsWrongMissingNullCoercionsAndUnsafeRuntime() throws IOException {
        byte[] valid = Json.write(new Product(1, "test", "0.1.0", List.of("descriptor.mod")));
        String text = new String(valid, StandardCharsets.UTF_8);
        assertEquals("test", Json.read(valid, Product.class).productId());
        for (String invalid : List.of(text.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : true"),
                text.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : 1.0"),
                text.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : \"1\""),
                text.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : null"),
                text.replace("\"productId\" : \"test\",", ""),
                text.replace("\"productId\" : \"test\"", "\"productId\" : null"),
                text.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : 1, \"schemaVersion\" : 1"),
                text.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : 1, \"unknown\" : 2"))) {
            assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Product.class), invalid);
        }
        assertThrows(IllegalArgumentException.class, () -> new Product(1, "test", "0.1.0", List.of("descriptor.mod", "../escape")));
        assertThrows(IllegalArgumentException.class, () -> new Product(1, "test", "0.1.0", List.of("descriptor.mod", "tools/fixture.txt")));
        assertThrows(IllegalArgumentException.class, () -> new Product(1, "test", "0.1.0", List.of("descriptor.mod", "descriptor.mod")));
        String provenance = "{\"kind\":0,\"machineId\":\"fixture\",\"observedAt\":\"2026-10-24T00:00:00Z\"}";
        assertThrows(IOException.class, () -> Json.read(provenance.getBytes(StandardCharsets.UTF_8), Contracts.Provenance.class));
    }

    @Test void sourceClosureRejectsDriftMissingBomRemoteIdAndMissingReferences() throws IOException {
        Path source = createProduct(); new CatalogGenerator().generate(catalog(), source);
        Path generated = source.resolve("common/scripted_effects/rrf_catalog_validate_00.txt");
        String original = Files.readString(generated);
        Files.writeString(generated, original + "\n# drift"); assertThrows(IllegalArgumentException.class, () -> ContentValidator.validate(source));
        Files.writeString(generated, original);
        Path consumer = source.resolve("common/scripted_effects/rrf_sample_effects.txt");
        Files.writeString(consumer, "rrf_sample_effect = { }"); assertThrows(IllegalArgumentException.class, () -> ContentValidator.validate(source));
        Files.writeString(consumer, "\ufeffrrf_sample_effect = { rrf_missing_effect = yes }"); assertThrows(IllegalArgumentException.class, () -> ContentValidator.validate(source));
        Files.writeString(consumer, "\ufeffrrf_sample_effect = { rrf_catalog_validate_effect = yes }");
        Files.writeString(source.resolve("descriptor.mod"), "version=\"0.1.0\" remote_file_id=\"123\""); assertThrows(IllegalArgumentException.class, () -> ContentValidator.validate(source));
    }

    @Test void prereleaseVersionAndDeclaredForeignLanguageUseRealBuilderAndTokenConsumer() throws IOException {
        Path source = createProduct();
        String tokens = "@piety_icon! [GetPlayer.GetName]\\n";
        for (String language : List.of("english", "simp_chinese", "french")) {
            write(source, "localization/" + language + "/rrf_l_" + language + ".yml", "\ufeffl_" + language + ":\n rrf_label:0 \"" + tokens + "Text\"\n rrf_hidden:0 \"\"\n");
        }
        Product previous = Json.read(Files.readAllBytes(source.resolve("tools/product.json")), Product.class);
        List<String> files = new java.util.ArrayList<>(previous.runtimeFiles()); files.add("localization/french/rrf_l_french.yml");
        Product product = new Product(1, previous.productId(), "0.1.0-alpha", files);
        Files.write(source.resolve("tools/product.json"), Json.write(product));
        Files.writeString(source.resolve("descriptor.mod"), Files.readString(source.resolve("descriptor.mod")).replace("0.1.0", product.version()));
        new CatalogGenerator().generate(catalog(), source);
        ReleaseBuilder builder = new ReleaseBuilder();
        Contracts.Provenance provenance = new Contracts.Provenance(Contracts.ProvenanceKind.SYNTHETIC_FIXTURE, "synthetic-release-machine", "2026-10-25T00:00:00Z");
        ReleaseBuilder.BuildResult built = builder.build(source, directory.resolve("alpha-staging"), releaseIdentity("d"), provenance);
        assertEquals(product.version(), Json.read(Files.readAllBytes(Path.of(built.manifest())), Contracts.Manifest.class).version());
        assertEquals(product.version(), builder.verify(source, Path.of(built.staging()), Path.of(built.manifest())).version());
        Path french = source.resolve("localization/french/rrf_l_french.yml"); String original = Files.readString(french);
        Files.writeString(french, original.replace("[GetPlayer.GetName]", "[GetPlayer.GetFaith.GetName]"));
        assertThrows(IllegalArgumentException.class, () -> ContentValidator.validate(source));
        Files.writeString(french, original.replace("rrf_hidden", "rrf_unknown"));
        assertThrows(IllegalArgumentException.class, () -> ContentValidator.validate(source));
        for (String invalid : List.of("0.1.0 Alpha", "0.1.0-", "0.1", "0.1.0-alpha..1")) {
            assertThrows(IllegalArgumentException.class, () -> new Product(1, previous.productId(), invalid, files));
            assertThrows(IllegalArgumentException.class, () -> new Contracts.Manifest(2, "3826756673", "synthetic-v0.1.0", "d".repeat(40), previous.productId(), invalid, provenance, List.of()));
        }
    }

    private static Contracts.ReleaseIdentity releaseIdentity(String digit) { return new Contracts.ReleaseIdentity("3826756673", "synthetic-v0.1.0", digit.repeat(40)); }

    private Catalog catalog() throws IOException {
        Path game = directory.resolve("game");
        write(game, "common/scripted_triggers/fixture.txt", "fixture_ok_trigger = { scope:actor = { is_landed = yes } }");
        write(game, "common/religion/doctrine_group_types/fixture.txt", "marriage = { category=main_group is_available_on_create={ religion_tag = christianity_religion } }");
        write(game, "common/religion/doctrine_types/fixture.txt", "doctrine_a={doctrine_group_type=marriage} doctrine_b={doctrine_group_type=marriage can_pick={ root = { fixture_ok_trigger = yes } }}");
        write(game, "common/religion/tenet_types/fixture.txt", "tenet_a={requires_dlc_flag=royal_court is_shown={always=yes} can_pick={scope:actor={is_landed=yes} NOT={tenet:tenet_b={is_in_list=selected_doctrines}}}} tenet_b={} tenet_c={} tenet_bad={can_pick={prev={always=yes}}}");
        return new CatalogReader().read(game, "test-fixture-machine");
    }
    private Path createProduct() throws IOException {
        Path source = directory.resolve("source");
        write(source, "descriptor.mod", "name=\"Fixture\" version=\"0.1.0\" supported_version=\"1.20.*\"");
        write(source, "common/scripted_effects/rrf_sample_effects.txt", "\ufeffrrf_sample_effect = { rrf_catalog_validate_effect = yes }");
        write(source, "localization/english/rrf_l_english.yml", "\ufeffl_english:\n rrf_label:0 \"Fixture\"\n");
        write(source, "localization/simp_chinese/rrf_l_simp_chinese.yml", "\ufeffl_simp_chinese:\n rrf_label:0 \"夹具\"\n");
        write(source, "docs/private.md", "not a runtime payload");
        Product product = new Product(1, "fixture", "0.1.0", List.of("descriptor.mod", "common/scripted_effects/rrf_sample_effects.txt", "localization/english/rrf_l_english.yml", "localization/simp_chinese/rrf_l_simp_chinese.yml"));
        Path config = source.resolve("tools/product.json"); Files.createDirectories(config.getParent()); Files.write(config, Json.write(product));
        return source;
    }
    private static void write(Path root, String relative, String content) throws IOException { Path target = root.resolve(relative); Files.createDirectories(target.getParent()); Files.writeString(target, content, StandardCharsets.UTF_8); }
}
