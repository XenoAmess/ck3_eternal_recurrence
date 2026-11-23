package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.Clausewitz;

/** Authored import/serialization boundaries; actual engine and performance remain untested. */
final class ControlledLoadFixtureTest {
    @TempDir Path temporary;
    private static final String CASE = "synthetic-controlled-load";
    private static Path repository() { return Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent(); }
    private static FollowupContracts.ControlledLoadRequest input() {
        return new FollowupContracts.ControlledLoadRequest(3, CASE, true, List.of(2048,4096));
    }
    @Test void strictSyntheticRequestRoundTripsActualEmissionWithSixJavaPinsOneRuleDataPinAndBusinessEffects() throws Exception {
        Path wire=temporary.resolve("request.json");Files.write(wire,FixtureEmitter.JSON.writeValueAsBytes(input()));
        assertEquals(input(),FixtureEmitter.readInput(wire));
        var emitted=FixtureEmitter.emit(repository(),temporary.resolve("load"),"authored-load-fixture",FixtureEmitter.readInput(wire));
        var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emitted.manifest().path())));
        assertEquals(CASE,manifest.path("case_id").textValue());
        assertTrue(manifest.path("receipt").path("fixture_contains_business_effects").booleanValue());
        assertEquals(7,manifest.path("producer_source_pins").size());
        assertEquals(4,manifest.path("receipt").path("required_markers").size());
        assertEquals(13,manifest.path("files").size());
        assertTrue(manifest.path("files").has("descriptor.mod"));
        assertFalse(emitted.gameStarted());assertEquals("NOT_RUN",emitted.businessAcceptance());
        assertEquals(input(),FixtureEmitter.readInput(Path.of(emitted.fixture()).resolve("_xfma_request.json")));
        for(var names=manifest.path("files").fieldNames();names.hasNext();) {
            String name=names.next();var pin=FixtureEmitter.pin(Path.of(emitted.fixture()).resolve(name));
            assertEquals(pin.sha256(),manifest.path("files").path(name).path("sha256").textValue());
        }
    }
    @Test void emittedRuleVariantPinsOriginalDataAndChangesOnlyTwoDefaults() throws Exception {
        Path source=repository().resolve("mod_financial_markets").resolve(FixtureEmitter.CONTROLLED_LOAD_RULES);
        byte[] before=Files.readAllBytes(source);
        var emitted=FixtureEmitter.emit(repository(),temporary.resolve("rule-variant"),"authored-load-fixture",input());
        var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emitted.manifest().path())));
        var expectedPin=FixtureEmitter.pin(source);
        var dataPin=manifest.path("producer_source_pins").get(6);
        assertEquals(expectedPin.path(),dataPin.path("path").textValue());
        assertEquals(expectedPin.bytes(),dataPin.path("bytes").longValue());
        assertEquals(expectedPin.sha256(),dataPin.path("sha256").textValue());
        assertEquals(6,java.util.stream.StreamSupport.stream(manifest.path("producer_source_pins").spliterator(),false)
            .filter(pin->pin.path("path").textValue().endsWith(".java")).count());
        byte[] variant=Files.readAllBytes(Path.of(emitted.fixture()).resolve(FixtureEmitter.CONTROLLED_LOAD_RULES));
        String text=new String(variant,StandardCharsets.UTF_8);
        var rules=Clausewitz.parse(text);
        assertEquals("xfm_futures_disabled",((Clausewitz.Atom)((Clausewitz.Block)rules.named("xfm_market_futures").getFirst().value()).named("default").getFirst().value()).token());
        assertEquals("xfm_ai_issuance_disabled",((Clausewitz.Atom)((Clausewitz.Block)rules.named("xfm_market_ai_issuance").getFirst().value()).named("default").getFirst().value()).token());
        String restored=text.replace("default = xfm_futures_disabled","default = xfm_futures_enabled")
            .replace("default = xfm_ai_issuance_disabled","default = xfm_ai_issuance_enabled");
        assertArrayEquals(before,restored.getBytes(StandardCharsets.UTF_8),"all other rule bytes, options, BOM and line endings must survive");
        assertArrayEquals(before,Files.readAllBytes(source),"the production source is never rewritten");
    }
    @Test void derivedDefaultsPreserveUtf8BomCrLfAndFailClosedOnSourceDrift() throws Exception {
        String source=Files.readString(repository().resolve("mod_financial_markets").resolve(FixtureEmitter.CONTROLLED_LOAD_RULES),StandardCharsets.UTF_8);
        String crlf=source.replace("\r\n","\n").replace("\n","\r\n");
        byte[] variant=FixtureEmitter.controlledLoadRuleDefaults(crlf.getBytes(StandardCharsets.UTF_8));
        String restored=new String(variant,StandardCharsets.UTF_8)
            .replace("default = xfm_futures_disabled","default = xfm_futures_enabled")
            .replace("default = xfm_ai_issuance_disabled","default = xfm_ai_issuance_enabled");
        assertArrayEquals(crlf.getBytes(StandardCharsets.UTF_8),restored.getBytes(StandardCharsets.UTF_8));
        List<String> invalid=List.of(source.replace("default = xfm_futures_enabled","default = xfm_futures_disabled"),
            source.replace("default = xfm_ai_issuance_enabled","default = xfm_ai_issuance_disabled"),
            source.replace("xfm_market_futures = {","wrong_futures_rule = {"),
            source.replace("xfm_futures_disabled = { }",""),
            source+"\n# duplicate default = xfm_futures_enabled\n");
        for(String text:invalid)assertThrows(IOException.class,()->FixtureEmitter.controlledLoadRuleDefaults(text.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class,()->FixtureEmitter.controlledLoadRuleDefaults(new byte[65537]));
        assertThrows(IOException.class,()->FixtureEmitter.controlledLoadRuleDefaults(new byte[0]));
        assertThrows(IOException.class,()->FixtureEmitter.controlledLoadRuleDefaults(new byte[]{(byte)0xc3,(byte)0x28}));
    }
    @Test void invalidOriginalRuleSourceFailsBeforeAnyFixtureOutputIsCreated() throws Exception {
        Path source=repository(),copy=temporary.resolve("source-copy");
        String javaRoot="mod_financial_markets/tools/src/main/java/org/xar/ck3/markets/acceptance/";
        for(String name:List.of("AcceptanceContracts.java","ObservationScripts.java","FixtureEmitter.java","AcceptanceCommand.java","FollowupContracts.java","FollowupObservationScripts.java")) {
            Path target=copy.resolve(javaRoot+name);Files.createDirectories(target.getParent());Files.copy(source.resolve(javaRoot+name),target);
        }
        Path rules=copy.resolve("mod_financial_markets").resolve(FixtureEmitter.CONTROLLED_LOAD_RULES);Files.createDirectories(rules.getParent());
        Files.writeString(rules,"xfm_market_futures = { default = xfm_futures_disabled }",StandardCharsets.UTF_8);
        Path output=temporary.resolve("rejected-rules");
        assertThrows(IOException.class,()->FixtureEmitter.emit(copy,output,"authored-load-fixture",input()));
        assertFalse(Files.exists(output));assertFalse(Files.exists(Path.of(output+".fixture.json")));
    }
    @Test void naturalSchemaOneTwoAndOtherControlledFixturesRetainSixJavaPinsAndNoRuleOverride() throws Exception {
        var natural=new FollowupContracts.Request(2,FollowupContracts.Profile.DERIVATIVES,1,
            new FollowupContracts.ActorBinding(FollowupContracts.ActorMode.CURRENT_PLAYER,null),
            new FollowupContracts.Targets("1","2",null,null,null,null),null,null);
        List<FollowupContracts.Input> inputs=List.of(new FollowupContracts.LegacyInput(new AcceptanceContracts.Request(1,"1128")),natural,
            new FollowupContracts.ControlledFundingRequest(3,"perpetual-funding-engine-fixture",true),
            new FollowupContracts.ControlledDebtAidNewsRequest(3,"debt-aid-news-engine-fixture",true,new FollowupContracts.ControlledDebtParticipants("1","2","3")));
        int index=0;for(var request:inputs) {
            var emitted=FixtureEmitter.emit(repository(),temporary.resolve("unchanged-"+(index++)),"authored-load-fixture",request);
            var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emitted.manifest().path())));
            assertEquals(6,manifest.path("producer_source_pins").size());
            assertFalse(manifest.path("files").has(FixtureEmitter.CONTROLLED_LOAD_RULES));
            assertFalse(Files.exists(Path.of(emitted.fixture()).resolve(FixtureEmitter.CONTROLLED_LOAD_RULES)));
        }
    }
    @Test void falseOptinWrongTierFractionsUnknownDuplicateAndCrossSubtypeRequestsAreRejected() throws Exception {
        String valid=FixtureEmitter.JSON.writeValueAsString(input());
        List<String> invalid=List.of(valid.replace("true","false"),valid.replace("true","1"),
            valid.replace("2048,4096","4096,2048"),valid.replace("2048,4096","2048,8192"),
            valid.replace("2048,4096","2048.0,4096"),valid.replace("2048,4096","2048,4096,8192"),
            valid.replace("\"schemaVersion\":3","\"schemaVersion\":2"),
            valid.replace(CASE,"ai-capacity"),valid.replace(CASE,"debt-aid-news-engine-fixture"),
            valid.replace("\"loadCoins\":", "\"gold\":1,\"loadCoins\":"),
            valid.replace("\"loadCoins\":[2048,4096]","\"loadCoins\":[2048,4096],\"loadCoins\":[2048,4096]"));
        int index=0;for(String text:invalid){Path bad=temporary.resolve("bad"+(index++)+".json");Files.writeString(bad,text);
            assertThrows(IOException.class,()->FixtureEmitter.readInput(bad),text);}
        assertThrows(IllegalArgumentException.class,()->new FollowupContracts.ControlledLoadRequest(3,CASE,true,List.of(8192)));
        var funding=new FollowupContracts.ControlledFundingRequest(3,"perpetual-funding-engine-fixture",true);
        Path old=temporary.resolve("funding.json");Files.write(old,FixtureEmitter.JSON.writeValueAsBytes(funding));
        assertEquals(funding,FixtureEmitter.readInput(old));
        var debt=new FollowupContracts.ControlledDebtAidNewsRequest(3,"debt-aid-news-engine-fixture",true,
            new FollowupContracts.ControlledDebtParticipants("1","2","3"));
        Files.write(old,FixtureEmitter.JSON.writeValueAsBytes(debt));assertEquals(debt,FixtureEmitter.readInput(old));
    }
    @Test void emittedScriptsParseAndOnlyExplicitGenesisAndSyntheticListingMayMutateBusinessState() {
        var payload=FollowupObservationScripts.renderControlledLoad(input());
        assertEquals(11,payload.size());
        assertTrue(payload.containsKey("descriptor.mod"));
        payload.forEach((path,bytes)->{
            assertArrayEquals(new byte[]{(byte)0xef,(byte)0xbb,(byte)0xbf},java.util.Arrays.copyOf(bytes,3));
            String text=new String(bytes,StandardCharsets.UTF_8);
            assertFalse(text.contains("${"),path);
            if(path.endsWith(".txt")||path.endsWith(".gui"))assertFalse(Clausewitz.parse(text).entries().isEmpty(),path);
            assertFalse(text.contains("xfm_issuer_register_effect"));assertFalse(text.contains("xfm_issuer_receipt_commit_effect"));
            assertFalse(text.contains("xfm_futures_submit_effect"));assertFalse(text.contains("xfm_debt_cover_shortfall_effect"));
        });
        String observer=new String(payload.get("common/scripted_effects/xfmcl_observe.txt"),StandardCharsets.UTF_8);
        var roots=Clausewitz.parse(observer);assertEquals(3,roots.entries().size());
        walk(roots,e->{
            if(e.key().startsWith("var:")||e.key().startsWith("global_var:"))
                assertFalse(e.value() instanceof Clausewitz.Block b && !b.named("value").isEmpty(),
                    "Engine numeric trigger RHS must use a named script_value, not a value/add trigger block: "+e.key());
        });
        var values=Clausewitz.parse(new String(payload.get("common/script_values/xfmcl_observation_values.txt"),StandardCharsets.UTF_8));
        assertEquals(3,values.entries().size());
        for(String name:List.of("xfmcl_owner_next_sample1_value","xfmcl_owner_next_sample2_value","xfmcl_owner_next_financial_value")) {
            var value=values.block(name);assertEquals(2,value.entries().size());
            assertTrue(((Clausewitz.Atom)value.named("value").getFirst().value()).token().startsWith("global_var:xfmcl_fixture_owner.var:"));
            assertEquals("1",((Clausewitz.Atom)value.named("add").getFirst().value()).token());
        }

        walk(roots,e->{if(Set.of("set_variable","change_variable").contains(e.key()))
            assertTrue(((Clausewitz.Atom)((Clausewitz.Block)e.value()).named("name").getFirst().value()).token().startsWith("xfmcl_"));
            assertFalse(Set.of("add_gold","create_story","create_character","set_game_rule").contains(e.key()));});
    }
    private static void walk(Clausewitz.Block block,java.util.function.Consumer<Clausewitz.Entry> consumer){
        for(var entry:block.entries()){consumer.accept(entry);if(entry.value() instanceof Clausewitz.Block child)walk(child,consumer);}}
    @Test void registeredGenericRouteKeepsFourExplicitSavesAndReaderGateBeforeGrowthWithoutChangingNaturalCase() throws Exception {
        var config=FixtureEmitter.JSON.readTree(Files.readAllBytes(repository().resolve("tools/ck3_mod_acceptance_cases/financial_markets_synthetic_controlled_load.json")));
        assertEquals(16,config.path("maximum_natural_days").intValue());
        assertEquals(4,config.path("controlled_fixture_contract").path("physical_save_maximum").intValue());
        assertEquals(32,config.path("controlled_fixture_contract").path("maximum_coins_per_GUI_batch").intValue());
        assertEquals(64,config.path("controlled_fixture_contract").path("initial_hot_books").intValue());
        assertEquals(List.of(0,8,16),java.util.stream.StreamSupport.stream(config.path("gui_phases").spliterator(),false).map(n->n.path("at_day").intValue()).toList());
        assertTrue(config.path("gui_phases").get(0).path("requirements").toString().contains("reader"));
        assertTrue(config.path("gui_phases").get(1).path("requirements").toString().contains("before_grow"));
        assertFalse(config.toString().contains("normal_exit_completes"));
        var registry=FixtureEmitter.JSON.readTree(Files.readAllBytes(repository().resolve("tools/ck3_mod_acceptance_products.json")));
        var cases=registry.path("products").path("financial-markets").path("cases");
        assertEquals(1,java.util.stream.StreamSupport.stream(cases.spliterator(),false).filter(n->CASE.equals(n.path("id").textValue())).count());
        var row=java.util.stream.StreamSupport.stream(cases.spliterator(),false).filter(n->CASE.equals(n.path("id").textValue())).findFirst().orElseThrow();
        assertEquals(180,row.path("normal_close").path("reserve_seconds").intValue());
        assertTrue(row.path("adapter").path("path").textValue().endsWith("generic_product_adapter.py"));
        var natural=FixtureEmitter.JSON.readTree(Files.readAllBytes(repository().resolve("tools/ck3_mod_acceptance_cases/financial_markets_ai_capacity.json")));
        assertEquals(395,natural.path("maximum_natural_days").intValue());
        assertEquals(395,natural.path("gui_phases").get(2).path("at_day").intValue());
        assertTrue(natural.path("gui_phases").get(0).path("requirements").toString().contains("no_fixture_business_seed"));
    }
    @Test void actualSavedImporterAndHostCopyRequireExplicitSyntheticBusinessEffectsFlag() throws Exception {
        var emitted=FixtureEmitter.emit(repository(),temporary.resolve("saved-load"),"authored-load-fixture",input());
        Path shared=Path.of(System.getProperty("xfm.shared.source",repository().toString())).toAbsolutePath().normalize();
        Path consumer=repository().resolve("mod_financial_markets/tools/src/test/resources/acceptance/verify_saved_observer_inventory.py");
        Path scratch=temporary.resolve("consumer"),log=temporary.resolve("consumer.log");
        Process process=new ProcessBuilder(System.getProperty("xfm.python","python"),"-B","-X","utf8",consumer.toString(),
            "--repo-root",repository().toString(),"--shared-source",shared.toString(),"--manifest",emitted.manifest().path(),
            "--scratch",scratch.toString(),"--controlled-load-fixture").directory(shared.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        assertTrue(process.waitFor(90,TimeUnit.SECONDS));assertEquals(0,process.exitValue(),Files.readString(log));
        var result=FixtureEmitter.JSON.readTree(Files.readAllBytes(scratch.resolve("actual-result.json")));
        assertTrue(result.path("saved_inventory_verified").booleanValue());assertTrue(result.path("host_copy_readback_verified").booleanValue());
        assertFalse(result.path("game_started").booleanValue());assertFalse(result.path("business_acceptance_proven").booleanValue());
        Path reject=temporary.resolve("no-optin"),rejectLog=temporary.resolve("reject.log");
        Process noFlag=new ProcessBuilder(System.getProperty("xfm.python","python"),"-B","-X","utf8",consumer.toString(),
            "--repo-root",repository().toString(),"--shared-source",shared.toString(),"--manifest",emitted.manifest().path(),
            "--scratch",reject.toString()).directory(shared.toFile()).redirectErrorStream(true).redirectOutput(rejectLog.toFile()).start();
        assertTrue(noFlag.waitFor(90,TimeUnit.SECONDS));assertNotEquals(0,noFlag.exitValue());
    }
}
