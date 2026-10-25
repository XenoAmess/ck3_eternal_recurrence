package org.xar.ck3.dynastic.release;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.zip.ZipFile;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.dynastic.ReleaseCommand;

final class ReleaseLocalizationTest {
    private static final String REVISION = "0123456789abcdef0123456789abcdef01234567";
    private static final String REGISTRY = "ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py";
    @TempDir Path temporary;

    @Test
    void developmentProjectionHasEighteenAndDoesNotGateKnownSevenLanguages() throws IOException {
        Fixture fixture = fixture();
        Path french = fixture.source().resolve(ReleaseProduct.Language.FRENCH.relativePath());
        Files.writeString(french, "deliberately invalid test-only foreign source");
        ReleaseProduct development = ReleaseProduct.official(fixture.source());
        assertEquals(18, StaticValidation.validate(development, fixture.repository()).fileCount());
        ReleaseBuilder.BuildResult built = new ReleaseBuilder().build(development, fixture.repository(), temporary.resolve("development"), REVISION, null, null);
        assertEquals(18, built.payload().files().size());
        assertTrue(Files.notExists(built.staging().resolve(ReleaseProduct.Language.FRENCH.relativePath())));
        Path unexpected = fixture.source().resolve("localization/french/unreviewed.yml");
        Files.writeString(unexpected, "extra");
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(development, fixture.repository()));
    }

    @Test
    void explicitCliAndRealReleaseProducerConsumerZipAndSharedPythonContractsRoundTrip() throws Exception {
        Fixture fixture = fixture();
        ReleaseProduct release = ReleaseProduct.official(fixture.source(), ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION);
        assertEquals(25, StaticValidation.validate(release, fixture.repository()).fileCount());
        assertEquals(0, new ReleaseCommand().run("validate", "--release-localization", "--source", fixture.source().toString(), "--repo-root", fixture.repository().toString()));
        assertEquals(1, new ReleaseCommand().run("validate", "--release-localization", "--release-localization"));
        assertEquals(1, new ReleaseCommand().run("validate", "--release-localization", "false"));
        ReleaseBuilder builder = new ReleaseBuilder();
        ReleaseBuilder.BuildResult built = builder.build(release, fixture.repository(), temporary.resolve("release"), REVISION, "dynastic-esotericism-v0.1.0", null);
        assertEquals(25, builder.verify(release, built.staging(), built.manifest()).verifiedFiles());
        assertEquals(25, ManifestJson.decode(Files.readAllBytes(built.manifest()), release).files().size());
        assertThrows(IllegalArgumentException.class, () -> builder.verify(ReleaseProduct.official(fixture.source()), built.staging(), built.manifest()));
        assertEquals(0, new ReleaseCommand().run("verify", "--source", fixture.source().toString(), "--repo-root", fixture.repository().toString(),
                "--output", built.staging().toString(), "--manifest", built.manifest().toString(), "--release-localization"));
        try (ZipFile archive = new ZipFile(built.archive().toFile(), StandardCharsets.UTF_8)) {
            assertEquals(25, archive.size());
            for (ReleaseManifest.FileEntry file : built.payload().files()) {
                assertArrayEquals(Files.readAllBytes(built.staging().resolve(file.path())),
                        archive.getInputStream(archive.getEntry(ReleaseProduct.PRODUCT_ID + "/" + file.path())).readAllBytes());
            }
        }
        String consumer = "import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
                + "from independent_mod_release import ProductSpec,verify_manifest; "
                + "from translate_localization_minimax import parse_ck3_localization,assert_protected_tokens; "
                + "source=Path(sys.argv[2]); staging=Path(sys.argv[3]); manifest=Path(sys.argv[4]); "
                + "paths=json.loads(Path(sys.argv[5]).read_bytes()); spec=ProductSpec('mod_dynastic_esotericism',source,paths,None,'dynastic-esotericism-v'); "
                + "assert verify_manifest(spec,staging,manifest)==25; "
                + "base=parse_ck3_localization(staging/'localization/english/des_l_english.yml'); "
                + "[assert_protected_tokens(base,parse_ck3_localization(staging/p),('\u2212100',)) for p in paths if p.endswith('.yml')]; "
                + "print('legacy manifest 25/25 and shared parser/token contract 9/9')";
        Path expectedInventory = temporary.resolve("expected-runtime.json");
        Files.write(expectedInventory, new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(release.runtimeFiles()));
        Process process = new ProcessBuilder("python", "-B", "-X", "utf8", "-c", consumer,
                actualSource().getParent().resolve("tools").toString(), fixture.source().toString(), built.staging().toString(), built.manifest().toString(),
                expectedInventory.toString()).redirectErrorStream(true).start();
        assertTrue(process.waitFor(30, TimeUnit.SECONDS), "shared existing Python consumers timed out");
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertEquals(0, process.exitValue(), output);
        assertTrue(output.contains("legacy manifest 25/25"));
    }

    @Test
    void releaseRejectsMissingVersionsKeysMalformedEscapesAndTokenDriftButAllowsForeignEmptyText() throws IOException {
        Fixture fixture = fixture();
        ReleaseProduct release = ReleaseProduct.official(fixture.source(), ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION);
        Path english = fixture.source().resolve(ReleaseProduct.Language.ENGLISH.relativePath());
        String original = Files.readString(english);
        Files.writeString(english, original.replace(":0 \"", ": \""));
        IllegalArgumentException missingVersion = assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(release, fixture.repository()));
        assertTrue(missingVersion.getMessage().contains(":0"));
        Files.writeString(english, original);
        Path french = fixture.source().resolve(ReleaseProduct.Language.FRENCH.relativePath());
        String valid = Files.readString(french);
        String nameLine = valid.lines().filter(line -> line.startsWith(" des_dynastic_membership_name:")).findFirst().orElseThrow();
        Map<String, String> invalid = Map.ofEntries(
                Map.entry("bom", valid.substring(1)),
                Map.entry("header", valid.replace("l_french:", "l_german:")),
                Map.entry("version", valid.replace(":0 \"", ":1 \"")),
                Map.entry("duplicate", valid + nameLine + "\n"),
                Map.entry("missing", valid.replace(nameLine + "\n", "")),
                Map.entry("extra", valid + " unreviewed_key:0 \"extra\"\n"),
                Map.entry("unescaped quote", valid.replace(nameLine, " des_dynastic_membership_name:0 \"bad \"quote\"\"")),
                Map.entry("dangling escape", valid.replace(nameLine, " des_dynastic_membership_name:0 \"bad\\\"")),
                Map.entry("added token", valid.replace(nameLine, " des_dynastic_membership_name:0 \"[ROOT.Char.GetName]\"")),
                Map.entry("protected number", valid.replace("\u2212100", "-100")));
        for (Map.Entry<String, String> entry : invalid.entrySet()) {
            Files.writeString(french, entry.getValue());
            assertThrows(Exception.class, () -> StaticValidation.validate(release, fixture.repository()), entry.getKey());
        }
        Files.writeString(french, valid.replace(nameLine, " des_dynastic_membership_name:0 \"\""));
        assertEquals(25, StaticValidation.validate(release, fixture.repository()).fileCount());
        Path chinese = fixture.source().resolve(ReleaseProduct.Language.SIMP_CHINESE.relativePath());
        String chineseOriginal = Files.readString(chinese);
        Files.writeString(chinese, chineseOriginal.replaceAll("(?m)^ des_dynastic_membership_name:0 .*", " des_dynastic_membership_name:0 \"\""));
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(release, fixture.repository()));
    }

    @Test
    void sharedProtectedScopesIconsEscapesAndIcuBlocksCannotChangeAndVerifyRechecksFormat() throws IOException {
        Fixture fixture = fixture();
        String tokenValue = "$LOC$ [ROOT.Char.GetName] @icon! #Ptext#! \\n \\\"quote\\\" ${name} {{name}} {count} %2$s <b>x</b> https://example.invalid/path {n, plural, one {A} other {B}}";
        for (ReleaseProduct.Language language : ReleaseProduct.Language.values()) {
            Path path = fixture.source().resolve(language.relativePath());
            String value = Files.readString(path).replaceAll("(?m)^ des_dynastic_membership_name:0 .*", java.util.regex.Matcher.quoteReplacement(" des_dynastic_membership_name:0 \"" + tokenValue + "\""));
            Files.writeString(path, value);
        }
        ReleaseProduct release = ReleaseProduct.official(fixture.source(), ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION);
        assertEquals(25, StaticValidation.validate(release, fixture.repository()).fileCount());
        Path french = fixture.source().resolve(ReleaseProduct.Language.FRENCH.relativePath());
        String valid = Files.readString(french);
        for (String changed : List.of(valid.replace("ROOT.Char", "OTHER.Char"), valid.replace("@icon!", "@different!"),
                valid.replace("\\n", ""), valid.replace("\\\"quote\\\"", "quote"), valid.replace("plural,", "select,"))) {
            Files.writeString(french, changed);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(release, fixture.repository()));
        }
        Files.writeString(french, valid);
        ReleaseBuilder builder = new ReleaseBuilder();
        ReleaseBuilder.BuildResult built = builder.build(release, fixture.repository(), temporary.resolve("verified"), REVISION, null, null);
        Path staged = built.staging().resolve(ReleaseProduct.Language.FRENCH.relativePath());
        Files.writeString(staged, valid.replace("l_french:", "l_german:"));
        byte[] changed = Files.readAllBytes(staged);
        ReleaseManifest old = built.payload();
        List<ReleaseManifest.FileEntry> entries = old.files().stream().map(entry -> entry.path().equals(ReleaseProduct.Language.FRENCH.relativePath())
                ? new ReleaseManifest.FileEntry(entry.path(), changed.length, ReleaseBuilder.sha256(changed)) : entry).toList();
        Files.write(built.manifest(), ManifestJson.encode(new ReleaseManifest(old.formatVersion(), old.productId(), old.modVersion(), old.gitTag(), old.gitSha(), old.workshopItemId(), entries)));
        assertThrows(IllegalArgumentException.class, () -> builder.verify(release, built.staging(), built.manifest()));
    }

    private Fixture fixture() throws IOException {
        Path repository = temporary.resolve("repository");
        Path source = repository.resolve("mod_dynastic_esotericism");
        for (String relative : ReleaseProduct.official(actualSource()).runtimeFiles()) {
            Path destination = source.resolve(relative);
            Files.createDirectories(destination.getParent());
            Files.copy(actualSource().resolve(relative), destination);
        }
        Path registry = repository.resolve(REGISTRY);
        Files.createDirectories(registry.getParent());
        Files.copy(actualSource().getParent().resolve(REGISTRY), registry);
        String english = Files.readString(source.resolve(ReleaseProduct.Language.ENGLISH.relativePath())).replace("\r\n", "\n").replaceAll("(?m)^ ([^:\\s]+): ", " $1:0 ");
        for (ReleaseProduct.Language language : ReleaseProduct.Language.values()) {
            Path path = source.resolve(language.relativePath());
            Files.createDirectories(path.getParent());
            String value = language == ReleaseProduct.Language.SIMP_CHINESE
                    ? Files.readString(path).replace("\r\n", "\n").replaceAll("(?m)^ ([^:\\s]+): ", " $1:0 ")
                    : english.replace("l_english:", language.header());
            Files.writeString(path, value, StandardCharsets.UTF_8);
        }
        return new Fixture(repository, source);
    }

    private static Path actualSource() { return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize(); }
    private record Fixture(Path repository, Path source) { }
}
