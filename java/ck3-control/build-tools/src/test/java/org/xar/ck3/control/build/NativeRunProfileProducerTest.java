package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.NativeRunProfileManifest.*;

/** Production business bytes and actual temporary file custody; no software fixture issues runtime/Game authority. */
final class NativeRunProfileProducerTest {
    @TempDir Path temporary;
    @Test void missingCurrentSchemaNeverSelectsTheHistoricalConsumerBranch()throws Exception{
        var mapper=ControlBuild.strictMapper();
        for(String wire:List.of("{\"format_version\":2}","{\"format_version\":true}","{\"format_version\":1.0}",
                "{\"format_version\":\"1\"}","{\"producer_tools_build\":null}","{\"producer_runtime\":[]}","{\"profile_assets\":[]}",
                "{\"schema\":null}","{\"schema\":\"unknown-v3\"}"))
            assertThrows(IOException.class,()->requireSupported(mapper.readTree(wire)));
        requireSupported(mapper.readTree("{\"format_version\":1}"));
        requireSupported(mapper.readTree("{\"environment_sha256\":\"historical library fixture\"}"));
    }
    @Test void installedDefaultsActualProducerAppendsExactThreeRulesAndRendersTheOriginalPreset()throws Exception{
        byte[] bytes=defaults();FileRef source=write(temporary.resolve("vanilla.txt"),bytes);
        var contract=NativeRunProfileRules.derive(source,bytes,NativeRunProfileRules.XarMode.XAR_OFF);
        assertEquals(70,contract.declaredVanillaRuleCount());assertEquals(73,contract.profile().size());
        assertEquals(new NativeRunProfileRules.Rule("xar_enabled","xar_off"),contract.profile().get(70));
        String preset=new String(NativeRunProfileRules.renderPresets(contract),StandardCharsets.UTF_8);
        assertTrue(preset.contains("setting={ s0 s1 s2"));assertTrue(preset.endsWith("xar_off xar_inherit_100 xar_score_growth }\n\tironman=no\n}\n"));
        assertEquals(NativeRunProfileRules.sha(NativeRunProfileRules.profileBytes(contract.profile())),contract.profileSha256());
    }
    @Test void realRulesSourceRejectsMissingDefaultDuplicateSettingUnbalancedAndMalformedUtf8()throws Exception{
        for(byte[] bytes:List.of("broken={\n}\n".getBytes(StandardCharsets.UTF_8),
                new String(defaults(),StandardCharsets.UTF_8).replace("s1\n","s0\n").getBytes(StandardCharsets.UTF_8),
                (new String(defaults(),StandardCharsets.UTF_8)+"unfinished={\n").getBytes(StandardCharsets.UTF_8),
                new byte[]{(byte)0xff})){
            FileRef source=write(temporary.resolve("rules-"+NativeRunProfileRules.sha(bytes)+".txt"),bytes);
            assertThrows(IOException.class,()->NativeRunProfileRules.derive(source,bytes,NativeRunProfileRules.XarMode.XAR_ON));
        }
    }
    @Test void actualFiveFileProducerThenNativeReadbackIsRequiredBeforeEnvironmentCanBeEncoded()throws Exception{
        Fixture fixture=fixture();var prepared=NativeRunProfileProducer.derive(fixture.request(),fixture.runtime());
        assertEquals(5,prepared.assets().size());
        assertThrows(IOException.class,()->NativeRunProfileProducer.finish(prepared,List.of(),Clock.systemUTC()));
        var assets=materialize(prepared);
        Manifest actual=NativeRunProfileProducer.finish(prepared,assets,Clock.systemUTC());
        assertEquals(actual,decode(encode(actual)));assertEquals(73,actual.rules().profile().size());
        assertTrue(actual.profileAssets().stream().allMatch(row->row.nativeFile().linkCount()==1));
        assertEquals("mod/xar_autoplayer.mod",actual.loadProfile().enabledMods().getFirst());
        assertEquals(fixture.request().productionRoot(),actual.mod().productionPath());
        assertThrows(IOException.class,()->NativeRunProfileProducer.readVerified(write(temporary.resolve("unqualified-environment.json"),encode(actual))));
    }
    @Test void actualSourceMutationAndOutputReplacementAreRejectedByTheSameProductionCore()throws Exception{
        Fixture fixture=fixture();var prepared=NativeRunProfileProducer.derive(fixture.request(),fixture.runtime());var assets=materialize(prepared);
        Path settings=Path.of(assets.stream().filter(row->row.kind()==AssetKind.SETTINGS).findFirst().orElseThrow().original().path());
        Files.writeString(settings,"changed actual output");
        assertThrows(IOException.class,()->NativeRunProfileProducer.finish(prepared,assets,Clock.systemUTC()));
        Files.writeString(Path.of(fixture.request().vanillaRules().path()),"source drift");
        assertThrows(IOException.class,prepared::verifyOriginals);
    }
    @Test void formalProjectionRejectsExtraOrMissingFile()throws Exception{
        Fixture fixture=fixture();Path production=Path.of(fixture.request().productionRoot());Files.writeString(production.resolve("extra.txt"),"extra");
        assertThrows(IOException.class,()->NativeRunProfileProducer.derive(fixture.request(),fixture.runtime()));
        Files.delete(production.resolve("extra.txt"));Files.delete(production.resolve("descriptor.mod"));
        assertThrows(IOException.class,()->NativeRunProfileProducer.derive(fixture.request(),fixture.runtime()));
    }
    @Test void completeProductionCustodyCodecRejectsNewEntriesAndOriginalManifestSurvivesMutableSettings()throws Exception{
        Fixture fixture=fixture();var prepared=NativeRunProfileProducer.derive(fixture.request(),fixture.runtime());
        var inventory=write(temporary.resolve("production-input.json"),NativeRunProfileProducer.encodeProductionTree(prepared.productionTree()));
        assertEquals(prepared.productionTree(),NativeRunProfileProducer.readProductionTree(inventory));
        assertTrue(prepared.productionTree().retainedAllocatedUpperBytes()>=prepared.productionTree().nativeFileAllocatedBytes());
        var assets=materialize(prepared);Manifest actual=NativeRunProfileProducer.finish(prepared,assets,Clock.systemUTC());
        var original=write(temporary.resolve("environment-original.json"),encode(actual));
        Path settings=Path.of(assets.stream().filter(row->row.kind()==AssetKind.SETTINGS).findFirst().orElseThrow().original().path());
        Files.writeString(settings,"actual postGame mutable settings fixture");
        assertEquals(actual,readOriginal(original));
        assertThrows(IOException.class,()->NativeRunProfileProducer.finish(prepared,assets,Clock.systemUTC()));
        Files.createDirectory(Path.of(fixture.request().productionRoot()).resolve("new-directory"));
        assertThrows(IOException.class,()->NativeRunProfileProducer.readProductionTree(inventory));
    }
    @Test void manifestCodecRejectsWrongMissingUnknownDuplicateAndDigestDrift()throws Exception{
        Fixture fixture=fixture();var prepared=NativeRunProfileProducer.derive(fixture.request(),fixture.runtime());
        String wire=new String(encode(NativeRunProfileProducer.finish(prepared,materialize(prepared),Clock.systemUTC())),StandardCharsets.UTF_8);
        for(String invalid:List.of(wire.replace("\"format_version\":2","\"format_version\":true"),
                wire.replace("\"format_version\":2,",""),wire.replaceFirst("\\{","{\"unknown\":1,"),
                wire.replaceFirst("\\{","{\"format_version\":2,"),wire.replace("fullscreen","windowed"))){
            assertThrows(IOException.class,()->decode(invalid.getBytes(StandardCharsets.UTF_8)));
        }
    }
    @Test void currentPublicPrepareRejectsAnUnqualifiedReceiptBeforeDerivingOrWriting()throws Exception{
        Fixture fixture=fixture();assertThrows(IOException.class,()->NativeRunProfileProducer.prepare(fixture.request(),Clock.systemUTC()));
        assertFalse(Files.exists(fixture.request().profile().resolve("dlc_load.json")));
    }
    private record Fixture(NativeRunProfileProducer.Request request,List<FileRef> runtime){ }
    private Fixture fixture()throws Exception{
        Path state=Files.createDirectories(temporary.resolve("state")),production=Files.createDirectories(state.resolve("profile/mod-content/xar-production"));
        Path game=Files.createDirectories(temporary.resolve("game")),binaries=Files.createDirectories(game.resolve("binaries"));
        Files.createDirectories(game.resolve("game/dlc"));Path launcher=Files.createDirectories(game.resolve("launcher"));
        FileRef exe=write(binaries.resolve("ck3.exe"),"software-only-never-executed".getBytes(StandardCharsets.UTF_8));
        FileRef rules=write(game.resolve("rules.txt"),defaults());
        FileRef identity=write(launcher.resolve("launcher-settings.json"),"{\"rawVersion\":\"fixture\",\"version\":\"fixture\",\"distPlatform\":\"steam\"}".getBytes(StandardCharsets.UTF_8));
        FileRef descriptor=write(production.resolve("descriptor.mod"),"name=\"琉焰卿的永恒轮回\"\nversion=\"1.0.0\"\n".getBytes(StandardCharsets.UTF_8));
        var release=new ReleaseManifest(2,"1.0.0",null,"a".repeat(40),"3784706360",List.of(new ReleaseEntry("descriptor.mod",descriptor.bytes(),descriptor.sha256())));
        FileRef manifest=write(state.resolve("formal.manifest.json"),ControlBuild.strictMapper().writeValueAsBytes(release));
        FileRef unqualified=write(temporary.resolve("not-a-completed-tools-receipt.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var runtime=new ArrayList<FileRef>();for(int index=0;index<6;index++)runtime.add(write(temporary.resolve("runtime"+index+".jar"),("actual fixture file"+index).getBytes(StandardCharsets.UTF_8)));
        var request=new NativeRunProfileProducer.Request(NativeRunProfileProducer.REQUEST_SCHEMA,WindowsJobProcess.currentMachineId(),
                Instant.now().plusSeconds(120).toString(),state.toString(),production.toString(),unqualified,exe,rules,identity,manifest,
                NativeRunProfileRules.XarMode.XAR_OFF,Display.FULLSCREEN);
        return new Fixture(request,List.copyOf(runtime));
    }
    private static List<Asset> materialize(NativeRunProfileProducer.Prepared prepared)throws Exception{
        var actual=new ArrayList<Asset>();
        for(var planned:prepared.assets()){Path path=Path.of(planned.target());Files.createDirectories(path.getParent());
            Files.write(path,planned.bytes(),java.nio.file.StandardOpenOption.CREATE_NEW);var nativeFile=SharedSourceFiles.observe(path);
            actual.add(new Asset(planned.kind(),nativeFile.source(),nativeFile.nativeFile()));}
        return List.copyOf(actual);
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException{Files.write(path,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);return FileRef.measure(path);}
    private static byte[] defaults(){var text=new StringBuilder();for(int i=0;i<70;i++)text.append("r").append(i).append("={\n default=s").append(i).append("\n}\n");return text.toString().getBytes(StandardCharsets.UTF_8);}

    @Test void explicitVanillaKeepsZeroProductRootsDeclaredDlcAndSavedDebugWithoutWeakeningOrdinary()throws Exception{
        var fixture=explicitFixture(0,false,false);var request=explicitRequest(fixture,fixture.request().source(),true);
        var prepared=NativeRunProfileProducer.deriveExplicit(request,fixture.runtime());
        assertEquals(List.of(),prepared.productionRoots());assertEquals(List.of(),prepared.inputCustody().productFiles());
        var environment=NativeRunProfileProducer.finishExplicit(prepared,Clock.systemUTC());
        assertEquals(ProfileKind.SAVED_VANILLA,environment.kind());assertTrue(environment.game().debugMode());
        assertEquals(DlcDeclaration.ABSENT,environment.profile().loadProfile().declaredDlc().declaration());
        assertEquals(environment,decodeEnvironment(encodeEnvironment(environment)));
        assertEquals(environmentJson(environment),ControlBuild.strictMapper().readTree(encodeEnvironment(environment)));
        assertEquals(request,decodeExplicitRequest(encodeExplicitRequest(request)));
        assertEquals(List.of(environment.profile().loadProfile().dlcLoad(),((SavedSource)request.source()).productInventory()),prepared.requiredPreparedFileRefs());
        assertThrows(IllegalArgumentException.class,()->new Game("v","v","steam",request.launcherSettings().path(),request.launcherSettings().sha256(),
                request.gameExecutable().path(),request.gameExecutable().sha256(),request.vanillaRules().path(),request.vanillaRules().sha256(),true));
        assertThrows(IOException.class,()->decode(encodeEnvironment(environment)));
    }
    @Test void multipleSavedModsRetainActualOrderDisabledDlcAndCompletePhysicalInventory()throws Exception{
        var fixture=explicitFixture(2,true,false);
        var prepared=NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime());
        var environment=NativeRunProfileProducer.finishExplicit(prepared,Clock.systemUTC());
        assertEquals(ProfileKind.SAVED_PRODUCT_ONLY,environment.kind());
        assertEquals(List.of("mod/product1.mod","mod/product0.mod"),environment.profile().loadProfile().enabledMods());
        assertEquals(List.of("dlc_b","dlc_a","dlc_b"),environment.profile().loadProfile().declaredDlc().disabledDlcs());
        assertEquals(DlcDeclaration.DECLARED,environment.profile().loadProfile().declaredDlc().declaration());
        assertEquals(2,environment.productionRoots().size());
        assertEquals(fixture.productFiles().size(),environment.profile().custody().productFiles().size());
        assertTrue(environment.profile().custody().retainedAllocatedUpperBytes()>=environment.profile().custody().nativeFileAllocatedBytes());
        assertEquals(environment,decodeEnvironment(encodeEnvironment(environment)));
        assertTrue(environment.profile().custody().productFiles().stream().anyMatch(row->row.source().bytes()==0));
        Files.writeString(Path.of(environment.productionRoots().getFirst()).resolve("new-file.txt"),"actual extra");
        assertThrows(IOException.class,prepared::verifyOriginals);
        assertThrows(IOException.class,()->NativeRunProfileProducer.finishExplicit(prepared,Clock.systemUTC()));
    }
    @Test void savedInventoryRejectsWrongKindOrderMissingExtraDuplicateAndNonIntegralSizes()throws Exception{
        var fixture=explicitFixture(2,true,false);
        for(String variant:List.of("kind","order","missing","extra","duplicate","bool","float","path","schema")){
            var tree=inventoryTree(fixture);
            switch(variant){
                case "kind" -> tree.put("schema","ck3-saved-campaign-vanilla-profile-v1");
                case "order" -> tree.putArray("enabled_mods").add("mod/product0.mod").add("mod/product1.mod");
                case "missing" -> ((com.fasterxml.jackson.databind.node.ArrayNode)tree.get("product_files")).remove(0);
                case "extra" -> tree.put("extra",true);
                case "duplicate" -> ((com.fasterxml.jackson.databind.node.ArrayNode)tree.get("product_files")).add(tree.get("product_files").get(0).deepCopy());
                case "bool" -> ((com.fasterxml.jackson.databind.node.ObjectNode)tree.get("product_files").get(0)).put("bytes",true);
                case "float" -> ((com.fasterxml.jackson.databind.node.ObjectNode)tree.get("product_files").get(0)).put("bytes",1.0);
                case "path" -> tree.put("profile_path",temporary.toString());
                case "schema" -> tree.put("schema","unknown");
                default -> throw new AssertionError(variant);
            }
            var request=withInventory(fixture,tree);
            assertThrows(IOException.class,()->NativeRunProfileProducer.deriveExplicit(request,fixture.runtime()),variant);
        }
        var wrong=explicitRequest(fixture,new SavedSource(SavedKind.VANILLA,((SavedSource)fixture.request().source()).productInventory()),false);
        assertThrows(IOException.class,()->NativeRunProfileProducer.deriveExplicit(wrong,fixture.runtime()));
    }
    @Test void savedColdRegistrarIsRejectedWhileExplicitFixtureKeepsItsSeparateActualSourceDomain()throws Exception{
        var fixture=explicitFixture(2,true,true);
        assertThrows(IOException.class,()->NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime()));
        var request=fixtureRequest(fixture);
        var prepared=NativeRunProfileProducer.deriveExplicit(request,fixture.runtime());
        var environment=NativeRunProfileProducer.finishExplicit(prepared,Clock.systemUTC());
        assertEquals(ProfileKind.FRESH_FRONTEND_FIXTURE,environment.kind());
        assertTrue(environment.profile() instanceof FreshFixtureProfile);assertEquals(2,environment.productionRoots().size());
        assertEquals(environment,decodeEnvironment(encodeEnvironment(environment)));
        assertThrows(IllegalArgumentException.class,()->explicitRequest(fixture,request.source(),true));
        var source=(FixtureSource)request.source();
        var incomplete=new FixtureSource(source.policySource(),source.immutableInputs().stream()
                .filter(row->!row.equals(environment.profile().loadProfile().dlcLoad())).toList(),source.mountedRelativePaths());
        assertThrows(IOException.class,()->NativeRunProfileProducer.deriveExplicit(explicitRequest(fixture,incomplete,false),fixture.runtime()));
        var wrongPaths=new FixtureSource(source.policySource(),source.immutableInputs(),List.of("mod/missing.mod"));
        assertThrows(IOException.class,()->NativeRunProfileProducer.deriveExplicit(explicitRequest(fixture,wrongPaths,false),fixture.runtime()));
        Files.writeString(fixture.request().profile().resolve("mod/unselected.mod"),"new unselected mounted source");
        assertThrows(IOException.class,prepared::verifyOriginals);
    }
    @Test void explicitSourceMutationIsRejectedButImmutableEnvironmentDataSurvivesMutableSettings()throws Exception{
        var fixture=explicitFixture(0,true,false);
        Path settings=fixture.request().profile().resolve("pdx_settings.txt");write(settings,"actual existing settings".getBytes(StandardCharsets.UTF_8));
        var prepared=NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime());
        var environment=NativeRunProfileProducer.finishExplicit(prepared,Clock.systemUTC());
        var original=write(temporary.resolve("explicit-original.json"),encodeEnvironment(environment));
        assertEquals(environment,readEnvironmentOriginal(original));
        assertTrue(prepared.requiredPreparedFileRefs().stream().anyMatch(row->row.path().equals(settings.toString())));
        Files.writeString(settings,"actual changed after Game");
        assertEquals(environment,readEnvironmentOriginal(original));
        assertThrows(IOException.class,prepared::verifyOriginals);
        assertThrows(IOException.class,()->NativeRunProfileProducer.finishExplicit(prepared,Clock.systemUTC()));
        assertThrows(IOException.class,()->NativeRunProfileProducer.readEnvironmentVerified(original));
    }
    @Test void strictExplicitWireRejectsUnknownDomainsMissingFieldsAndScalarCoercions()throws Exception{
        var fixture=explicitFixture(0,false,false);
        var request=explicitRequest(fixture,fixture.request().source(),true);
        String wire=new String(encodeExplicitRequest(request),StandardCharsets.UTF_8);
        for(String invalid:List.of(wire.replace("\"debug_mode\":true","\"debug_mode\":null"),
                wire.replace("\"debug_mode\":true","\"debug_mode\":1"),wire.replace("\"debug_mode\":true","\"debug_mode\":\"true\""),
                wire.replace("\"debug_mode\":true,",""),wire.replace("\"SAVED_NATIVE\"","\"UNDECLARED_DOMAIN\""),
                wire.replace("\"VANILLA\"","0"),wire.replaceFirst("\\{","{\"unknown\":true,"),wire+" {}")){
            assertThrows(IOException.class,()->decodeExplicitRequest(invalid.getBytes(StandardCharsets.UTF_8)));
        }
        var environment=NativeRunProfileProducer.finishExplicit(NativeRunProfileProducer.deriveExplicit(request,fixture.runtime()),Clock.systemUTC());
        String encoded=new String(encodeEnvironment(environment),StandardCharsets.UTF_8);
        for(String invalid:List.of(encoded.replace("\"format_version\":3","\"format_version\":true"),
                encoded.replace("\"format_version\":3","\"format_version\":3.0"),encoded.replace("\"format_version\":3","\"format_version\":\"3\""),
                encoded.replace("\"SAVED_NATIVE\"","\"UNDECLARED_DOMAIN\""),encoded.replaceFirst("\"file_id_decimal\":\"[0-9]+\"","\"file_id_decimal\":1"),encoded.replace("\"debug_mode\":true","\"debug_mode\":false"),
                encoded.replace(EXPLICIT_SCHEMA,"xar.java-native-run-profile-environment/v99"),encoded.replaceFirst("\\{","{\"unknown\":1,"))){
            assertThrows(IOException.class,()->decodeEnvironment(invalid.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(IOException.class,()->decodeEnvironment("[]".getBytes(StandardCharsets.UTF_8)));
    }
    @Test void disabledDlcAbsenceAndDeclaredEmptyAreDifferentAndInvalidDeclarationsAreRejected()throws Exception{
        var fixture=explicitFixture(0,false,false);Path load=fixture.request().profile().resolve("dlc_load.json");
        var absent=NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime());
        assertEquals(DlcDeclaration.ABSENT,absent.profile().loadProfile().declaredDlc().declaration());
        Files.writeString(load,"{\"enabled_mods\":[],\"disabled_dlcs\":[]}");
        var empty=NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime());
        assertEquals(DlcDeclaration.DECLARED,empty.profile().loadProfile().declaredDlc().declaration());
        assertEquals(List.of(),empty.profile().loadProfile().declaredDlc().disabledDlcs());
        for(String value:List.of("null","true","0","[true]")){
            Files.writeString(load,"{\"enabled_mods\":[],\"disabled_dlcs\":"+value+"}");
            assertThrows(IOException.class,()->NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime()));
        }
    }
    @Test void explicitPrepareDoesNotTurnUnqualifiedSoftwareInputsIntoRuntimeOrCreateFiles()throws Exception{
        var fixture=explicitFixture(0,false,false);
        try(var before=Files.list(fixture.request().profile())){assertEquals(1,before.count());}
        assertThrows(IOException.class,()->NativeRunProfileProducer.prepareExplicit(fixture.request(),Clock.systemUTC()));
        assertThrows(IOException.class,()->NativeRunProfileProducer.prepareSaved(fixture.request(),Clock.systemUTC()));
        assertThrows(IOException.class,()->NativeRunProfileProducer.prepareFixture(fixture.request(),Clock.systemUTC()));
        try(var after=Files.list(fixture.request().profile())){assertEquals(1,after.count());}
    }
    private record ExplicitFixture(ExplicitRequest request,List<FileRef> runtime,List<FileRef> productFiles){ }
    private ExplicitFixture explicitFixture(int count,boolean declaredDlc,boolean coldRegistrar)throws Exception{
        Path base=Files.createTempDirectory(temporary,"explicit-"),state=Files.createDirectory(base.resolve("state"));
        Path profile=Files.createDirectory(state.resolve("profile")),game=Files.createDirectory(base.resolve("game"));
        Path binaries=Files.createDirectory(game.resolve("binaries"));Files.createDirectories(game.resolve("game/dlc"));
        Path launcher=Files.createDirectory(game.resolve("launcher"));
        var exe=write(binaries.resolve("ck3.exe"),"software-executable-never-run".getBytes(StandardCharsets.UTF_8));
        var rules=write(game.resolve("rules.txt"),defaults());
        var identity=write(launcher.resolve("launcher-settings.json"),"{\"rawVersion\":\"fixture\",\"version\":\"fixture\",\"distPlatform\":\"steam\"}".getBytes(StandardCharsets.UTF_8));
        var build=write(base.resolve("unqualified-build.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var runtime=new ArrayList<FileRef>();for(int i=0;i<6;i++)runtime.add(write(base.resolve("runtime"+i+".jar"),("actual runtime file "+i).getBytes(StandardCharsets.UTF_8)));
        var mapper=ControlBuild.strictMapper();var load=mapper.createObjectNode();var enabled=load.putArray("enabled_mods");
        var products=new ArrayList<FileRef>();
        for(int index=count-1;index>=0;index--){
            Path root=Files.createDirectories(profile.resolve("mod-content/product"+index));Path outer=profile.resolve("mod/product"+index+".mod");Files.createDirectories(outer.getParent());
            enabled.add("mod/product"+index+".mod");
            products.add(write(outer,("name=\"software product"+index+"\"\npath=\""+root.toString().replace('\\','/')+"\"\n").getBytes(StandardCharsets.UTF_8)));
            products.add(write(root.resolve("descriptor.mod"),("name=\"software product"+index+"\"\n").getBytes(StandardCharsets.UTF_8)));
            products.add(write(root.resolve("script.txt"),(coldRegistrar?"on_game_start_after_lobby = { }":"ordinary saved product").getBytes(StandardCharsets.UTF_8)));
            products.add(write(root.resolve("empty.txt"),new byte[0]));
        }
        if(declaredDlc)load.putArray("disabled_dlcs").add("dlc_b").add("dlc_a").add("dlc_b");
        write(profile.resolve("dlc_load.json"),mapper.writeValueAsBytes(load));
        var inventory=mapper.createObjectNode().put("schema",count==0?"ck3-saved-campaign-vanilla-profile-v1":"ck3-saved-campaign-product-only-profile-v1").put("profile_path",profile.toString());
        inventory.set("enabled_mods",enabled.deepCopy());var rows=inventory.putArray("product_files");
        for(var file:products)rows.addObject().put("path",file.path()).put("bytes",file.bytes()).put("sha256",file.sha256().toUpperCase(java.util.Locale.ROOT));
        var source=write(state.resolve("saved-product-inventory.json"),mapper.writeValueAsBytes(inventory));
        var request=new ExplicitRequest(EXPLICIT_REQUEST_SCHEMA,WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(3600).toString(),state.toString(),base.toString(),
                build,exe,rules,identity,false,new SavedSource(count==0?SavedKind.VANILLA:SavedKind.PRODUCT_ONLY,source));
        return new ExplicitFixture(request,List.copyOf(runtime),List.copyOf(products));
    }
    private static ExplicitRequest explicitRequest(ExplicitFixture fixture,ExplicitSource source,boolean debug){
        var old=fixture.request();return new ExplicitRequest(old.schema(),old.machineId(),old.reviewAtUtc(),old.stateDir(),old.sourceWorkingDirectory(),
                old.qualifiedToolsBuild(),old.gameExecutable(),old.vanillaRules(),old.launcherSettings(),debug,source);
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode inventoryTree(ExplicitFixture fixture)throws Exception{
        return (com.fasterxml.jackson.databind.node.ObjectNode)ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(((SavedSource)fixture.request().source()).productInventory().path())));
    }
    private ExplicitRequest withInventory(ExplicitFixture fixture,com.fasterxml.jackson.databind.node.ObjectNode body)throws Exception{
        Path path=Files.createTempDirectory(temporary,"inventory-").resolve("inventory.json");var source=write(path,ControlBuild.strictMapper().writeValueAsBytes(body));
        return explicitRequest(fixture,new SavedSource(((SavedSource)fixture.request().source()).kind(),source),false);
    }
    private ExplicitRequest fixtureRequest(ExplicitFixture fixture)throws Exception{
        var policy=write(Path.of(fixture.request().stateDir()).resolve("fixture-policy.json"),"{\"software_source_only\":true}".getBytes(StandardCharsets.UTF_8));
        var refs=new ArrayList<FileRef>();refs.add(policy);refs.add(FileRef.measure(fixture.request().profile().resolve("dlc_load.json")));refs.addAll(fixture.productFiles());
        var paths=fixture.productFiles().stream().map(row->fixture.request().profile().relativize(Path.of(row.path())).toString().replace('\\','/')).sorted().toList();
        return explicitRequest(fixture,new FixtureSource(policy,List.copyOf(refs),paths),false);
    }
}
