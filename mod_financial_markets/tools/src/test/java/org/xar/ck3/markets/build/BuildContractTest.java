package org.xar.ck3.markets.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class BuildContractTest {
    @TempDir Path temporary;
    private static final String REVISION = "0123456789012345678901234567890123456789";
    private static final List<String> FILES = List.of("descriptor.mod", "common/scripted_effects/xfm_test.txt",
            "localization/simp_chinese/xfm_l_simp_chinese.yml", "localization/english/xfm_l_english.yml");

    @Test void candidateCopiesOnlyRuntimeAndPinsActualBytes() throws Exception {
        Path source = fixture();
        Files.createDirectories(source.resolve("tools"));
        Files.writeString(source.resolve("tools/not-for-players.txt"), "excluded");
        Path output = temporary.resolve("candidate");
        var result = SnapshotBuilder.build(source, output, REVISION);
        assertEquals(4, result.files().size());
        assertFalse(Files.exists(output.resolve("content/tools")));
        for (var file : result.files()) {
            byte[] bytes = Files.readAllBytes(output.resolve("content").resolve(file.path()));
            assertEquals(file.bytes(), bytes.length);
            assertEquals(file.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        }
        assertTrue(result.qualification().contains("NO_ENGINE_OR_RELEASE_CREDIT"));
        assertThrows(IOException.class, () -> SnapshotBuilder.build(source, output, REVISION));
    }

    @Test void rejectsMissingBomUndefinedEffectAndUnlistedRuntime() throws Exception {
        Path source = fixture();
        Files.writeString(source.resolve(FILES.get(1)), "xfm_test_effect = { }", StandardCharsets.UTF_8);
        assertTrue(assertThrows(IOException.class, () -> ContentValidator.validate(source)).getMessage().contains("BOM"));
        bom(source.resolve(FILES.get(1)), "xfm_test_effect = { xfm_missing_effect = yes }");
        assertTrue(assertThrows(IOException.class, () -> ContentValidator.validate(source)).getMessage().contains("undefined"));
        bom(source.resolve(FILES.get(1)), "xfm_test_effect = { }");
        bom(source.resolve("common/scripted_effects/rogue.txt"), "xfm_rogue_effect = { }");
        assertTrue(assertThrows(IOException.class, () -> ContentValidator.validate(source)).getMessage().contains("unlisted"));
    }

    @Test void rejectsBrokenStructureLocalizationAndUnsafeManifest() throws Exception {
        Path source = fixture();
        bom(source.resolve(FILES.get(1)), "xfm_test_effect = { # braces inside comments are ignored: }\n x = \"{\" }");
        assertEquals(1, ContentValidator.validate(source).effects());
        bom(source.resolve(FILES.get(1)), "xfm_test_effect = { x = \"unterminated }");
        assertThrows(IOException.class, () -> ContentValidator.validate(source));
        bom(source.resolve(FILES.get(1)), "xfm_test_effect = { }");
        bom(source.resolve(FILES.get(3)), "l_english:\n xfm_other:0 \"Other\"\n");
        assertThrows(IOException.class, () -> ContentValidator.validate(source));
        writeManifest(source, List.of("../outside.txt"));
        assertThrows(IOException.class, () -> ContentValidator.validate(source));
    }

    @Test void rejectsOverlappingOutputAndMalformedRevisionBeforeCreatingOutput() throws Exception {
        Path source = fixture();
        assertThrows(IOException.class, () -> SnapshotBuilder.build(source, source.resolve("out"), REVISION));
        Path output = temporary.resolve("bad-revision");
        assertThrows(IOException.class, () -> SnapshotBuilder.build(source, output, "dirty"));
        assertFalse(Files.exists(output));
    }

    @Test void actualProductHasConsistentSourceContract() throws Exception {
        var report = ContentValidator.validate(Path.of(System.getProperty("xfm.source")));
        assertTrue(report.effects() > 0);
        assertTrue(report.localizationKeys() > 0);
        assertEquals("STATIC_ONLY_NOT_ENGINE_OR_BUSINESS_PASS", report.boundary());
    }

    private Path fixture() throws IOException {
        Path source = Files.createDirectory(temporary.resolve("source"));
        bom(source.resolve(FILES.get(0)), "name=\"Test\"\nversion=\"0.0.0\"\n");
        bom(source.resolve(FILES.get(1)), "xfm_test_effect = { }\n");
        bom(source.resolve(FILES.get(2)), "l_simp_chinese:\n xfm_test:0 \"测试\"\n");
        bom(source.resolve(FILES.get(3)), "l_english:\n xfm_test:0 \"Test\"\n");
        writeManifest(source, FILES);
        return source;
    }
    private static void writeManifest(Path root, List<String> files) throws IOException {
        new ObjectMapper().writeValue(root.resolve("runtime-files.json").toFile(), new ContentValidator.Manifest("xfm.runtime-files.v1", files));
    }
    private static void bom(Path file, String content) throws IOException {
        Files.createDirectories(file.getParent());
        Files.writeString(file, "\ufeff" + content, StandardCharsets.UTF_8);
    }
}
