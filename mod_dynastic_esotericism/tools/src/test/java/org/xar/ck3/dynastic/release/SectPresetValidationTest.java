package org.xar.ck3.dynastic.release;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.zip.ZipFile;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class SectPresetValidationTest {
    private static final String REVISION = "0123456789abcdef0123456789abcdef01234567";
    private static final String REGISTRY = "ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py";
    @TempDir Path temporary;

    @Test
    void actualNineLanguageProducerStagingManifestAndZipPassIndependentExistingAstConsumer() throws Exception {
        Path source = source();
        ReleaseProduct product = ReleaseProduct.official(source, ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION);
        ReleaseBuilder builder = new ReleaseBuilder();
        ReleaseBuilder.BuildResult built = builder.build(product, source.getParent(), temporary.resolve("product"), REVISION, null, null);
        assertEquals(52, ManifestJson.decode(Files.readAllBytes(built.manifest()), product).files().size());
        assertEquals(52, builder.verify(product, built.staging(), built.manifest()).verifiedFiles());
        try (ZipFile archive = new ZipFile(built.archive().toFile(), StandardCharsets.UTF_8)) {
            for (String relative : product.runtimeFiles()) {
                assertArrayEquals(Files.readAllBytes(built.staging().resolve(relative)), archive.getInputStream(archive.getEntry(product.productId() + "/" + relative)).readAllBytes());
            }
        }
        List<ExpectedSect> expected = Arrays.stream(SectPreset.values()).map(preset -> new ExpectedSect(preset.faithId(), preset.riteId(), preset.icon(),
                preset.tenets(), SectPreset.ORDINARY_DOCTRINES, preset.specialDoctrines())).toList();
        Path contract = temporary.resolve("preset-contract.json");
        Files.write(contract, new ObjectMapper().writeValueAsBytes(expected));
        String program = """
                import io,json,struct,sys
                from pathlib import Path
                repository,root,contract=map(Path,sys.argv[1:])
                sys.path.insert(0,str(repository/'ck3_autonomous_player'/'src'))
                from xar_autoplayer.campaign_score_save_reader import melt_tokens
                sys.path.insert(0,str(repository/'tools'/'lyd_i3b_checkpoint_readback'/'reader'/'dependencies'))
                from bounded_save_parser import parse_block,one
                def read(relative):
                    raw=(root/relative).read_text(encoding='utf-8-sig').encode('utf-8')
                    return parse_block('{ '+' '.join(melt_tokens(io.BytesIO(raw)))+' }')
                faiths=read('common/religion/faith_types/des_faiths.txt')
                rites=read('common/religion/rite_types/des_rites.txt')
                coats=read('common/coat_of_arms/coat_of_arms/des_rite_coa.txt')
                doctrines=read('common/religion/doctrine_types/des_doctrines.txt')
                none=one(doctrines,'des_doctrine_none',required=True)
                dynastic=one(doctrines,'des_doctrine_dynastic',required=True)
                assert one(none,'can_pick') is None
                assert one(none,'visible',required=True)=='no'
                assert one(none,'is_shown',required=True)==[{'key':'always','value':'yes'}]
                assert one(dynastic,'visible') is None
                assert one(none,'doctrine_group_type',required=True)==one(dynastic,'doctrine_group_type',required=True)=='des_dynastic_membership'
                group=one(read('common/religion/doctrine_group_types/des_doctrine_groups.txt'),'des_dynastic_membership',required=True)
                assert one(group,'category',required=True)=='main_group'
                assert one(group,'is_available_on_create',required=True)==[{'key':'always','value':'yes'}]
                assert one(dynastic,'icon',required=True)==json.dumps('des_dynastic_membership')
                icons=[(root/'gfx/interface/icons'/folder/'des_dynastic_membership.dds').read_bytes() for folder in ['faith_doctrine_groups','faith_doctrines']]
                assert icons[0]==icons[1]
                for data in icons:
                    assert data[:4]==b'DDS ' and len(data)==128+120*120*4
                    assert [struct.unpack_from('<I',data,offset)[0] for offset in [12,16,20,28,80,84,88,92,96,100,104]]==[120,120,480,0,65,0,32,16711680,65280,255,4278190080]
                gate=one(dynastic,'can_pick',required=True)
                assert {row['key'] for row in gate}=={'exists','scope:actor'}
                assert one(gate,'exists',required=True)=='scope:actor'
                actor=one(gate,'scope:actor',required=True)
                assert actor==[{'key':'is_ai','value':'no'}]
                expected=json.loads(contract.read_bytes())
                assert {row['key'] for row in faiths}=={item['faith'] for item in expected}
                assert {row['key'] for row in rites}=={item['rite'] for item in expected}
                def values(entries,key):
                    rows=one(entries,key,required=True)
                    assert all(row['key'] is None and isinstance(row['value'],str) for row in rows)
                    return [row['value'] for row in rows]
                for item in expected:
                    faith=one(faiths,item['faith'],required=True)
                    rite=one(rites,item['rite'],required=True)
                    assert one(faith,'main_rite',required=True)==item['rite']
                    details=one(faith,'faith_details',required=True)
                    assert one(details,'religion',required=True)=='christianity_religion'
                    assert one(details,'icon',required=True)==one(rite,'icon',required=True)==item['icon']
                    assert one(rite,'faith',required=True)==item['faith']
                    assert one(rite,'name',required=True)==item['rite']
                    tenets=values(rite,'tenets')
                    doctrines=values(rite,'doctrines')
                    assert len(tenets)==3 and set(tenets)==set(item['tenets'])
                    assert len(item['ordinary'])==25
                    assert len(doctrines)==25+len(item['specials'])
                    assert len(doctrines)==len(set(doctrines))
                    assert set(doctrines)==set(item['ordinary']+item['specials'])
                    assert values(faith,'doctrines')==['special_doctrine_is_western_christian_faith']
                    assert (root/'gfx/interface/icons/faith'/(item['icon']+'.dds')).is_file()
                    coat=one(coats,item['rite']+'_coa',required=True)
                    emblem=one(coat,'textured_emblem',required=True)
                    assert one(emblem,'texture',required=True)==json.dumps(item['icon']+'.dds')
                    assert (root/'gfx/coat_of_arms/textured_emblems'/(item['icon']+'.dds')).read_bytes()==(root/'gfx/interface/icons/faith'/(item['icon']+'.dds')).read_bytes()
                print('independent existing lexer/AST accepted both packaged presets; engine semantics not tested')
                """;
        Process process = new ProcessBuilder(System.getProperty("dynastic.python", "python"), "-B", "-X", "utf8", "-c", program, source.getParent().toString(), built.staging().toString(), contract.toString())
                .redirectErrorStream(true).start();
        boolean completed = process.waitFor(30, TimeUnit.SECONDS);
        if (!completed) process.destroyForcibly();
        assertTrue(completed, "independent existing parser timed out");
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertEquals(0, process.exitValue(), output);
        assertTrue(output.contains("accepted both packaged presets"), output);
    }

    @Test
    void packagedDoctrineRequiresRealPlayerChoiceLegalityAndLeavesNoneUnrestricted() throws IOException {
        Fixture fixture = fixture();
        Path doctrine = fixture.product().source().resolve("common/religion/doctrine_types/des_doctrines.txt");
        String original = Files.readString(doctrine);
        String gate = "can_pick = {\n\t\texists = scope:actor\n\t\tscope:actor = { is_ai = no }\n\t}";
        String selectedIcon = "icon = \"des_dynastic_membership\"";
        assertTrue(original.contains(gate));
        assertTrue(original.contains(selectedIcon));
        List<String> invalid = List.of(
                original.replace(gate, ""),
                original.replace(gate, "ai_chance = { value = 0 }"),
                original.replace(gate, "is_shown = { scope:actor = { is_ai = no } }"),
                original.replace("exists = scope:actor", "always = yes"),
                original.replace("is_ai = no", "is_ai = yes"),
                original.replace("is_ai = no", "is_ai = { no }"),
                original.replace("is_ai = no", "always = yes"),
                original.replace(gate, gate + "\n\t" + gate),
                original.replace("visible = no", "visible = yes"),
                original.replace("visible = no", "visible = { no }"),
                original.replace("visible = no", ""),
                original.replace("is_shown = { always = yes }", "is_shown = { always = no }"),
                original.replace("is_shown = { always = yes }", "is_shown = { scope:actor = { is_ai = no } }"),
                original.replace("is_shown = { always = yes }", ""),
                original.replace(selectedIcon, "icon = \"doctrine_pluralism_fundamentalist\""),
                original.replace(selectedIcon, "icon = { des_dynastic_membership }"),
                original.replace(selectedIcon, ""),
                original.replace("doctrine_group_type = des_dynastic_membership", "doctrine_group_type = doctrine_pluralism"),
                original.replace("index = 0", "index = 0\n\tcan_pick = { scope:actor = { is_ai = no } }"));
        for (String changed : invalid) {
            Files.writeString(doctrine, changed, StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        }
        Files.writeString(doctrine, original, StandardCharsets.UTF_8);
        Path group = fixture.product().source().resolve("common/religion/doctrine_group_types/des_doctrine_groups.txt");
        String groupOriginal = Files.readString(group);
        for (String changed : List.of(groupOriginal.replace("always = yes", "always = no"),
                groupOriginal.replace("is_available_on_create = { always = yes }", ""))) {
            Files.writeString(group, changed, StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        }
        Files.writeString(group, groupOriginal, StandardCharsets.UTF_8);
        // Actual static presets retain dynastic doctrines without a selecting actor.
        assertEquals(52, StaticValidation.validate(fixture.product(), fixture.repository()).fileCount());
    }

    @Test
    void realDefinitionsRejectMissingUnknownDuplicateWrongTypeAndWrongDoctrineChoices() throws IOException {
        Fixture fixture = fixture();
        Path faith = fixture.product().source().resolve(SectPreset.FAITH_FILE);
        String faithOriginal = Files.readString(faith);
        List<String> invalidFaiths = List.of(
                faithOriginal.replace("main_rite = des_procreation_rite", "main_rite = des_vivhite_rite"),
                faithOriginal.replace("main_rite = des_procreation_rite", "main_rite = { des_procreation_rite }"),
                faithOriginal.replace("main_rite = des_procreation_rite", ""),
                faithOriginal.replace("main_rite = des_procreation_rite", "main_rite = des_procreation_rite main_rite = des_procreation_rite"),
                faithOriginal.replace("religion = christianity_religion", "religion = catholic"),
                faithOriginal.replace("historical = no", "historical = false"),
                faithOriginal.replace("origin = catholic", "unreviewed = catholic origin = catholic"),
                faithOriginal.replace("icon = des_procreation", "icon = des_vivhite"));
        for (String invalid : invalidFaiths) {
            Files.writeString(faith, invalid, StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        }
        Files.writeString(faith, faithOriginal, StandardCharsets.UTF_8);
        Path rite = fixture.product().source().resolve(SectPreset.RITE_FILE);
        String riteOriginal = Files.readString(rite);
        List<String> invalidRites = List.of(
                riteOriginal.replace("faith = des_procreation_faith", "faith = des_vivhite_faith"),
                riteOriginal.replace("doctrine_gender_equal", ""),
                riteOriginal.replace("doctrine_gender_equal", "doctrine_gender_equal doctrine_gender_equal"),
                riteOriginal.replace("doctrine_gender_equal", "doctrine_gender_equal = yes"),
                riteOriginal.replace("doctrine_gender_equal", "true"),
                riteOriginal.replace("tenet_sacred_childbirth", "tenet_warmonger"),
                riteOriginal.replace("special_doctrine_is_jewish_faith", ""),
                riteOriginal.replace("special_doctrine_jizya", "special_doctrine_unreviewed"),
                riteOriginal.replace("icon = des_procreation", "icon = des_procreation_missing"));
        for (String invalid : invalidRites) {
            Files.writeString(rite, invalid, StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        }
        Files.writeString(rite, riteOriginal, StandardCharsets.UTF_8);
        assertEquals(52, StaticValidation.validate(fixture.product(), fixture.repository()).fileCount());
    }

    @Test
    void stagedConsumerRejectsChangedDoctrineEvenWhenManifestDigestIsUpdated() throws IOException {
        Fixture fixture = fixture();
        ReleaseBuilder builder = new ReleaseBuilder();
        ReleaseBuilder.BuildResult built = builder.build(fixture.product(), fixture.repository(), temporary.resolve("signed-change"), REVISION, null, null);
        Path staged = built.staging().resolve(SectPreset.RITE_FILE);
        Files.writeString(staged, Files.readString(staged).replace("doctrine_gender_equal", "doctrine_gender_male_dominated"), StandardCharsets.UTF_8);
        byte[] changed = Files.readAllBytes(staged);
        ReleaseManifest old = built.payload();
        List<ReleaseManifest.FileEntry> entries = old.files().stream().map(entry -> entry.path().equals(SectPreset.RITE_FILE)
                ? new ReleaseManifest.FileEntry(entry.path(), changed.length, ReleaseBuilder.sha256(changed)) : entry).toList();
        Files.write(built.manifest(), ManifestJson.encode(new ReleaseManifest(old.formatVersion(), old.productId(), old.modVersion(), old.gitTag(), old.gitSha(), old.workshopItemId(), entries)));
        assertThrows(IllegalArgumentException.class, () -> builder.verify(fixture.product(), built.staging(), built.manifest()));
    }

    @Test
    void sectLocalizationHasSeparateExactContractAndCannotAliasAnotherFaith() throws IOException {
        Fixture fixture = fixture();
        Path french = fixture.product().source().resolve(ReleaseProduct.Language.FRENCH.sectRelativePath());
        String original = Files.readString(french);
        String name = original.lines().filter(line -> line.startsWith(" des_procreation_faith:0 ")).findFirst().orElseThrow();
        for (String invalid : List.of(original.replace(name + "\n", ""), original + name + "\n", original + " unreviewed:0 \"x\"\n",
                original.replace(name, " des_procreation_faith:0 \"[ROOT.Char.GetName]\""),
                original.replace("$des_procreation_faith$", "$des_vivhite_faith$"))) {
            Files.writeString(french, invalid, StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        }
        Files.writeString(french, original, StandardCharsets.UTF_8);
        Path chinese = fixture.product().source().resolve(ReleaseProduct.Language.SIMP_CHINESE.sectRelativePath());
        Files.writeString(chinese, Files.readString(chinese).replaceAll("(?m)^ des_procreation_faith:0 .*", " des_procreation_faith:0 \"\""), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
    }

    @Test
    void ddsRequiresRealDimensionsPixelFormatAndCompletePayload() throws IOException {
        String relative = SectPreset.PROCREATION.iconPath();
        byte[] original = Files.readAllBytes(source().resolve(relative));
        StaticValidation.validateBytes(relative, original);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validateBytes(relative, Arrays.copyOf(original, 128)));
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validateBytes(relative, Arrays.copyOf(original, original.length - 1)));
        for (Map.Entry<Integer, Integer> invalid : Map.of(4, 123, 12, 0, 16, -1, 28, 99, 76, 0, 108, 0).entrySet()) {
            byte[] changed = original.clone();
            ByteBuffer.wrap(changed).order(ByteOrder.LITTLE_ENDIAN).putInt(invalid.getKey(), invalid.getValue());
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validateBytes(relative, changed));
        }
        Fixture fixture = fixture();
        Path groupIcon = fixture.product().source().resolve(ReleaseProduct.DYNASTIC_GROUP_ICON);
        Path selectedIcon = fixture.product().source().resolve(ReleaseProduct.DYNASTIC_DOCTRINE_ICON);
        byte[] glyph = Files.readAllBytes(groupIcon);
        byte[] wrongDimensions = glyph.clone();
        ByteBuffer.wrap(wrongDimensions).order(ByteOrder.LITTLE_ENDIAN).putInt(12, 60).putInt(16, 240).putInt(20, 960);
        byte[] missingAlpha = glyph.clone();
        ByteBuffer.wrap(missingAlpha).order(ByteOrder.LITTLE_ENDIAN).putInt(104, 0);
        for (byte[] changed : List.of(wrongDimensions, missingAlpha)) {
            Files.write(groupIcon, changed);
            Files.write(selectedIcon, changed);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        }
        Files.write(groupIcon, glyph);
        Files.write(selectedIcon, glyph);
        byte[] crossedArtwork = glyph.clone();
        crossedArtwork[crossedArtwork.length - 1] ^= 1;
        Files.write(selectedIcon, crossedArtwork);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        Files.delete(selectedIcon);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
    }

    @Test
    void finiteCoatOfArmsDefinitionsRejectCrossedTexturesMissingResourcesAndChangedPixels() throws IOException {
        Fixture fixture = fixture();
        Path coats = fixture.product().source().resolve(SectPreset.COAT_OF_ARMS_FILE);
        String original = Files.readString(coats);
        Files.writeString(coats, original.replace("\"des_procreation.dds\"", "\"des_vivhite.dds\""), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        Files.writeString(coats, original, StandardCharsets.UTF_8);
        Path texture = fixture.product().source().resolve(SectPreset.PROCREATION.coatOfArmsTexturePath());
        byte[] pixels = Files.readAllBytes(texture);
        pixels[pixels.length - 1] ^= 1;
        Files.write(texture, pixels);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        Files.delete(texture);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
    }

    @Test
    void identityLocalizationCannotDriftOrBeMergedIntoTheOriginalFifteenKeyContract() throws IOException {
        Fixture fixture = fixture();
        Path identity = fixture.product().source().resolve(ReleaseProduct.Language.GERMAN.identityRelativePath());
        String original = Files.readString(identity);
        for (String invalid : List.of(original.replace("GetNameNoTooltip", "GetName"), original + " unrelated:0 \"x\"\n",
                original.replace("des_rite_dynasty_name", "des_dynasty_name"))) {
            Files.writeString(identity, invalid, StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
        }
        Files.writeString(identity, original, StandardCharsets.UTF_8);
        Path product = fixture.product().source().resolve(ReleaseProduct.Language.ENGLISH.relativePath());
        Files.writeString(product, Files.readString(product) + " des_rite_dynasty_name:0 \"[des_identity_rite.GetNameNoTooltip]\"\n", StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> StaticValidation.validate(fixture.product(), fixture.repository()));
    }

    private Fixture fixture() throws IOException {
        Path repository = temporary.resolve("repository");
        Path source = repository.resolve(ReleaseProduct.PRODUCT_ID);
        ReleaseProduct product = ReleaseProduct.official(source, ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION);
        for (String relative : product.runtimeFiles()) {
            Path destination = source.resolve(relative);
            Files.createDirectories(destination.getParent());
            Files.copy(source().resolve(relative), destination);
        }
        Path registry = repository.resolve(REGISTRY);
        Files.createDirectories(registry.getParent());
        Files.copy(source().getParent().resolve(REGISTRY), registry);
        return new Fixture(repository, product);
    }

    private static Path source() { return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize(); }
    private record Fixture(Path repository, ReleaseProduct product) { }
    private record ExpectedSect(String faith, String rite, String icon, List<String> tenets, List<String> ordinary, List<String> specials) { }
}
