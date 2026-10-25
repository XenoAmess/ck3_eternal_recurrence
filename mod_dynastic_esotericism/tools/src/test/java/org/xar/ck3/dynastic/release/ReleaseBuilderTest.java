package org.xar.ck3.dynastic.release;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipFile;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class ReleaseBuilderTest {
    private static final String REVISION = "0123456789abcdef0123456789abcdef01234567";
    private static final String UINT64_MAX = "18446744073709551615";
    private static final String REGISTRY = "ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py";
    private static final ObjectMapper JSON = new ObjectMapper();
    @TempDir Path temporary;

    @Test
    void producerToManifestConsumerAndZipRoundTripUsesExactBytes() throws IOException {
        Fixture fixture = fixture();
        ReleaseBuilder builder = new ReleaseBuilder();
        ReleaseBuilder.BuildResult first = builder.build(fixture.product(), fixture.repository(), temporary.resolve("first"), REVISION, "test-v0.1.0", UINT64_MAX);
        ReleaseManifest decoded = ManifestJson.decode(Files.readAllBytes(first.manifest()), fixture.product());
        assertEquals(first.payload(), decoded);
        assertEquals(UINT64_MAX, decoded.workshopItemId());
        assertEquals(2, builder.verify(fixture.product(), first.staging(), first.manifest()).verifiedFiles());
        try (ZipFile archive = new ZipFile(first.archive().toFile(), StandardCharsets.UTF_8)) {
            assertEquals(2, archive.size());
            for (ReleaseManifest.FileEntry file : decoded.files()) {
                assertArrayEquals(Files.readAllBytes(first.staging().resolve(file.path())),
                        archive.getInputStream(archive.getEntry("mod_test/" + file.path())).readAllBytes());
            }
        }
        String descriptor = Files.readString(first.staging().resolve("descriptor.mod"));
        assertTrue(descriptor.contains("\"Balance \""));
        assertTrue(descriptor.indexOf("\"Balance \"") < descriptor.indexOf("\"Religion\""));
        assertTrue(descriptor.indexOf("\"Religion\"") < descriptor.indexOf("\"1.20 'Crozier'\""));
        assertFalse(descriptor.contains("\"1.19\""));
        ReleaseBuilder.BuildResult second = builder.build(fixture.product(), fixture.repository(), temporary.resolve("second"), REVISION, "test-v0.1.0", UINT64_MAX);
        assertArrayEquals(Files.readAllBytes(first.manifest()), Files.readAllBytes(second.manifest()));
        assertArrayEquals(Files.readAllBytes(first.archive()), Files.readAllBytes(second.archive()));
        assertThrows(IllegalArgumentException.class, () -> builder.build(fixture.product(), fixture.repository(), first.staging(), REVISION, null, null));
    }

    @Test
    void strictManifestRejectsUnknownMissingNullAndWrongJsonTypes() throws IOException {
        Fixture fixture = fixture();
        ReleaseBuilder.BuildResult built = new ReleaseBuilder().build(fixture.product(), fixture.repository(), temporary.resolve("built"), REVISION, null, null);
        byte[] valid = Files.readAllBytes(built.manifest());
        ObjectNode original = (ObjectNode) JSON.readTree(valid);
        for (String field : List.of("format_version", "product_id", "mod_version", "git_tag", "git_sha", "workshop_item_id", "files")) {
            ObjectNode missing = original.deepCopy();
            missing.remove(field);
            reject(missing, fixture.product());
        }
        ObjectNode unknown = original.deepCopy();
        unknown.put("legacy_id", "ignored");
        reject(unknown, fixture.product());
        for (String wrongFormat : List.of("true", "1.0", "\"1\"", "null")) {
            ObjectNode invalid = original.deepCopy();
            invalid.set("format_version", JSON.readTree(wrongFormat));
            reject(invalid, fixture.product());
        }
        for (String wrongItem : List.of("18446744073709551615", "true", "\"01\"", "\"18446744073709551616\"", "\"\"")) {
            ObjectNode invalid = original.deepCopy();
            invalid.set("workshop_item_id", JSON.readTree(wrongItem));
            reject(invalid, fixture.product());
        }
        for (String wrongSize : List.of("true", "1.0", "\"1\"", "-1", "9007199254740992", "null")) {
            ObjectNode invalid = original.deepCopy();
            ((ObjectNode) invalid.get("files").get(0)).set("size", JSON.readTree(wrongSize));
            reject(invalid, fixture.product());
        }
        ObjectNode filesNull = original.deepCopy();
        filesNull.putNull("files");
        reject(filesNull, fixture.product());
        ObjectNode filesEmpty = original.deepCopy();
        filesEmpty.set("files", JSON.createArrayNode());
        reject(filesEmpty, fixture.product());
        ObjectNode missingEntryField = original.deepCopy();
        ((ObjectNode) missingEntryField.get("files").get(0)).remove("sha256");
        reject(missingEntryField, fixture.product());
        ObjectNode unknownEntryField = original.deepCopy();
        ((ObjectNode) unknownEntryField.get("files").get(0)).put("digest", "ignored");
        reject(unknownEntryField, fixture.product());
        ObjectNode duplicatePath = original.deepCopy();
        ((ArrayNode) duplicatePath.get("files")).add(duplicatePath.get("files").get(0).deepCopy());
        reject(duplicatePath, fixture.product());
        assertThrows(IOException.class, () -> ManifestJson.decode((new String(valid, StandardCharsets.UTF_8) + "{}").getBytes(StandardCharsets.UTF_8), fixture.product()));
    }

    @Test
    void verifiesActualContentAndRejectsTestFilesInRuntime() throws IOException {
        Fixture fixture = fixture();
        ReleaseBuilder builder = new ReleaseBuilder();
        ReleaseBuilder.BuildResult built = builder.build(fixture.product(), fixture.repository(), temporary.resolve("built"), REVISION, null, null);
        Path script = built.staging().resolve("common/scripted_effects/test.txt");
        byte[] original = Files.readAllBytes(script);
        Files.writeString(script, "\ufeffdifferent = { }\n", StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> builder.verify(fixture.product(), built.staging(), built.manifest()));
        Files.write(script, original);
        Path extra = built.staging().resolve("docs/test-only.txt");
        Files.createDirectories(extra.getParent());
        Files.writeString(extra, "source-only");
        assertThrows(IllegalArgumentException.class, () -> builder.verify(fixture.product(), built.staging(), built.manifest()));
        Path sourceExtra = fixture.product().source().resolve("test_event.txt");
        Files.writeString(sourceExtra, "\ufefftest = { }\n");
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
    }

    @Test
    void rejectsMissingFileBadBomMalformedBracesAndUnknownCompatibility() throws IOException {
        Fixture fixture = fixture();
        Path script = fixture.product().source().resolve("common/scripted_effects/test.txt");
        for (String invalid : List.of("test = { }\n", "\ufefftest = {\n", "\ufefftest = { key = \"unclosed }\n")) {
            Files.writeString(script, invalid, StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        }
        Files.writeString(script, "\ufefftest = { quoted = \"}#\" # }\n }\n", StandardCharsets.UTF_8);
        assertEquals(2, StaticValidation.validate(fixture.product(), fixture.repository()).fileCount());
        Path descriptor = fixture.product().source().resolve("descriptor.mod");
        Files.writeString(descriptor, Files.readString(descriptor).replace("1.20.*", "1.21.*"));
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        Files.delete(script);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
    }

    @Test
    void actualProductSourceBuildsAndReadsBackThroughTheSameConsumer() throws IOException {
        Path source = Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize();
        ReleaseProduct product = ReleaseProduct.official(source);
        ReleaseBuilder builder = new ReleaseBuilder();
        assertEquals(31, StaticValidation.validate(product, source.getParent()).fileCount());
        ReleaseBuilder.CheckResult checked = builder.check(product, source.getParent(), temporary.resolve("real-product"), REVISION, null);
        assertEquals(31, checked.fileCount());
        Map<String, Path> files = StaticValidation.inventory(temporary.resolve("real-product/one"), false);
        assertEquals(Set.copyOf(product.runtimeFiles()), files.keySet());
        assertTrue(files.keySet().stream().noneMatch(ReleaseProduct::sourceOnly));
    }

    private void reject(JsonNode node, ReleaseProduct product) throws IOException {
        byte[] bytes = JSON.writeValueAsBytes(node);
        assertThrows(Exception.class, () -> ManifestJson.decode(bytes, product));
    }

    private Fixture fixture() throws IOException {
        Path repository = temporary.resolve("repository");
        Path source = repository.resolve("mod_test");
        Path script = source.resolve("common/scripted_effects/test.txt");
        Files.createDirectories(script.getParent());
        Files.writeString(script, "\ufefftest_effect = { value = 1 }\n", StandardCharsets.UTF_8);
        Files.writeString(source.resolve("descriptor.mod"), "version=\"0.1.0\"\ntags={ \"Balance \" \"1.19\" \"Religion\" }\nsupported_version=\"1.20.*\"\n", StandardCharsets.UTF_8);
        Path registry = repository.resolve(REGISTRY);
        Files.createDirectories(registry.getParent());
        Files.writeString(registry, "CK3_WORKSHOP_VERSION_TAGS = {\"1.20\": \"1.20 'Crozier'\"}\n", StandardCharsets.UTF_8);
        return new Fixture(repository, new ReleaseProduct("mod_test", source, "test-v", List.of("descriptor.mod", "common/scripted_effects/test.txt")));
    }

    private record Fixture(Path repository, ReleaseProduct product) { }
}
