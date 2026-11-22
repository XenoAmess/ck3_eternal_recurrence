package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.Clausewitz;

/** Producer/import source qualification. Does not claim engine cash or natural AI execution. */
final class ControlledFundingFixtureTest {
    @TempDir Path temporary;
    private static final String CASE = "perpetual-funding-engine-fixture";
    private static Path repository() { return Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent(); }
    private static FollowupContracts.ControlledFundingRequest input() {
        return new FollowupContracts.ControlledFundingRequest(3, CASE, true);
    }
    private static String source(String path) {
        return new String(FollowupObservationScripts.renderControlledFunding(input()).get(path), StandardCharsets.UTF_8);
    }
    private static void walk(Clausewitz.Block block, Consumer<Clausewitz.Entry> visitor) {
        for (var entry : block.entries()) {
            visitor.accept(entry);
            if (entry.value() instanceof Clausewitz.Block child) walk(child, visitor);
        }
    }

    @Test void explicitControlledRequestUsesActualEmitterAndTruthfulBusinessEffectReceipt() throws Exception {
        Path wire=temporary.resolve("request.json"); Files.write(wire,FixtureEmitter.JSON.writeValueAsBytes(input()));
        assertEquals(input(),FixtureEmitter.readInput(wire));
        var emission=FixtureEmitter.emit(repository(),temporary.resolve("funding"),"synthetic-fixture-machine",FixtureEmitter.readInput(wire));
        var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emission.manifest().path())));
        assertEquals(CASE,manifest.path("case_id").textValue());
        assertTrue(manifest.path("receipt").path("fixture_contains_business_effects").booleanValue());
        assertEquals(6,manifest.path("producer_source_pins").size());
        assertEquals(6,manifest.path("receipt").path("required_markers").size());
        assertFalse(emission.gameStarted()); assertEquals("NOT_RUN",emission.businessAcceptance());
        assertEquals(input(),FixtureEmitter.readInput(Path.of(emission.fixture()).resolve("_xfma_request.json")));
        for(var name=manifest.path("files").fieldNames();name.hasNext();) {
            String relative=name.next(); var actual=FixtureEmitter.pin(Path.of(emission.fixture()).resolve(relative));
            assertEquals(actual.sha256(),manifest.path("files").path(relative).path("sha256").textValue());
        }
    }

    @Test void schemaThreeRejectsImplicitPrivilegeAndCannotTurnAnOldObserverIntoASetup() throws Exception {
        List<String> bad=List.of(
            "{\"schemaVersion\":3,\"caseId\":\"perpetual-funding-engine-fixture\"}",
            "{\"schemaVersion\":3,\"caseId\":\"perpetual-funding-engine-fixture\",\"controlledFixtureOnly\":false}",
            "{\"schemaVersion\":3,\"caseId\":\"derivatives\",\"controlledFixtureOnly\":true}",
            "{\"schemaVersion\":3.0,\"caseId\":\"perpetual-funding-engine-fixture\",\"controlledFixtureOnly\":true}",
            "{\"schemaVersion\":3,\"caseId\":\"perpetual-funding-engine-fixture\",\"controlledFixtureOnly\":1}",
            "{\"schemaVersion\":3,\"caseId\":\"perpetual-funding-engine-fixture\",\"controlledFixtureOnly\":true,\"gold\":1}",
            "{\"schemaVersion\":3,\"caseId\":\"perpetual-funding-engine-fixture\",\"controlledFixtureOnly\":true,\"controlledFixtureOnly\":true}");
        int i=0; for(String text:bad) {
            Path path=temporary.resolve("bad-"+(i++)+".json");Files.writeString(path,text);
            assertThrows(IOException.class,()->FixtureEmitter.readInput(path),text);
        }
        assertThrows(IllegalArgumentException.class,()->new FollowupContracts.ControlledFundingRequest(2,CASE,true));
        var old=FixtureEmitter.emit(repository(),temporary.resolve("legacy"),"synthetic-fixture-machine",new AcceptanceContracts.Request(1,"1128"));
        var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(old.manifest().path())));
        assertFalse(manifest.path("receipt").path("fixture_contains_business_effects").booleanValue());
        assertFalse(ObservationScripts.render(new AcceptanceContracts.Request(1,"1128")).containsKey("common/scripted_effects/xfmf_seed.txt"));
    }

    @Test void allGeneratedScriptsUseTheRealParserAndOnlyDeclaredInputsOrPrivateObservationWrites() {
        Set<String> allowed=Set.of("xfm_request_cents","xfm_selected_coin","xfm_futures_perpetual","xfm_futures_expiry_day",
            "xfm_futures_side","xfm_futures_lots","xfm_futures_leverage","xfm_futures_limit_cents",
            "xfm_futures_selected_position","xfm_futures_reduce_lots");
        Set<String> calls=new HashSet<>(); List<String> gold=new ArrayList<>();
        FollowupObservationScripts.renderControlledFunding(input()).forEach((path,bytes)->{
            assertEquals(0xef,Byte.toUnsignedInt(bytes[0]));assertEquals(0xbb,Byte.toUnsignedInt(bytes[1]));assertEquals(0xbf,Byte.toUnsignedInt(bytes[2]));
            String text=new String(bytes,StandardCharsets.UTF_8);
            assertFalse(text.contains("on_game_start_after_lobby")); assertFalse(text.contains("effect_group"));
            if(!path.endsWith(".txt")||path.startsWith("gui/scripted_widgets/"))return;
            Clausewitz.Block parsed=Clausewitz.parse(text);
            if(path.startsWith("common/scripted_effects/"))assertTrue(parsed.entries().size()<=20);
            walk(parsed,e->{
                if(e.key().startsWith("xfm_")&&e.key().endsWith("_effect"))calls.add(e.key());
                if(e.key().equals("add_gold"))gold.add(e.value().render());
                assertNotEquals("create_story",e.key(),"Business stories must come only from original production effects");
                if(Set.of("set_variable","change_variable").contains(e.key())) {
                    var body=(Clausewitz.Block)e.value();
                    String name=body.entries().stream().filter(x->x.key().equals("name")).findFirst().orElseThrow().value().render();
                    assertTrue(name.startsWith("xfmf_")||allowed.contains(name),path+": "+name);
                }
            });
        });
        assertEquals(Set.of("xfm_finance_ensure_effect","xfm_oracle_index_bootstrap_effect","xfm_oracle_index_daily_effect","xfm_finance_ensure_account_effect",
            "xfm_finance_deposit_effect","xfm_futures_ensure_market_effect","xfm_futures_submit_effect",
            "xfm_futures_position_daily_effect","xfm_futures_reduce_effect"),calls);
        assertEquals(List.of("20000"),gold,"Exactly one bounded seed instruction in the six-role helper");
    }

    @Test void fixtureIsFiniteConsumesActionsBeforeMoneyAndDoesNotOverrideProductionRiskOrPrices() {
        String seed=source("common/scripted_effects/xfmf_seed.txt");
        String book=source("common/scripted_effects/xfmf_book.txt");
        String observe=source("common/scripted_effects/xfmf_observe.txt");
        String close=source("common/scripted_effects/xfmf_close.txt");
        assertTrue(seed.indexOf("name = xfmf_setup_attempted")<seed.indexOf("xfmf_create_actor_effect = { ROLE"));
        assertEquals(6,seed.split("xfmf_create_actor_effect = \\{ ROLE",-1).length-1);
        assertTrue(book.indexOf("name = xfmf_book_attempted")<book.indexOf("var:xfmf_p_long = { xfmf_submit_effect"));
        assertTrue(close.indexOf("name = xfmf_close_attempted")<close.indexOf("xfmf_close_pair_effect = { PAIR"));
        assertTrue(observe.contains("has_variable = xfm_last_funding_day"));
        assertTrue(observe.contains("name = xfmf_$PHASE$_last_funding_day_present value = 0"));
        assertTrue(observe.indexOf("PHASE = retry_before")<observe.indexOf("xfm_futures_position_daily_effect = yes"));
        assertTrue(observe.indexOf("xfm_futures_position_daily_effect = yes")<observe.indexOf("PHASE = retry_after"));
        assertTrue(observe.contains("PHASE = next")); assertTrue(close.contains("xfm_futures_reduce_effect = yes"));
        String guards=source("common/scripted_triggers/xfmf_guards.txt");
        assertTrue(guards.contains("var:xfm_next_futures_position_id = 0"));
        assertTrue(guards.contains("var:xfm_next_futures_order_id = 0"));
        assertTrue(guards.contains("xfm_finance_account_usable_trigger = yes"));
        assertFalse(book.contains("xfm_futures_ai_budget"));
        assertFalse(book.contains("name = xfm_mark_cents")); assertFalse(book.contains("name = xfm_index_cents"));
        assertFalse(observe.contains("name = xfm_day")); assertFalse(observe.contains("name = xfm_last_funding_day"));
    }

    @Test void controlledEmissionUsesActualSharedSavedImportAndHostCopyWithExplicitTestFlag() throws Exception {
        var emission=FixtureEmitter.emit(repository(),temporary.resolve("saved-controlled"),"synthetic-fixture-machine",input());
        Path shared=Path.of(System.getProperty("xfm.shared.source",repository().toString())).toAbsolutePath().normalize();
        Path consumer=repository().resolve("mod_financial_markets/tools/src/test/resources/acceptance/verify_saved_observer_inventory.py");
        Path scratch=temporary.resolve("consumer"),log=temporary.resolve("consumer.log");
        Process process=new ProcessBuilder(System.getProperty("xfm.python","python"),"-B","-X","utf8",consumer.toString(),
            "--repo-root",repository().toString(),"--shared-source",shared.toString(),"--manifest",emission.manifest().path(),
            "--scratch",scratch.toString(),"--controlled-funding-fixture").directory(shared.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        assertTrue(process.waitFor(90,TimeUnit.SECONDS)); assertEquals(0,process.exitValue(),Files.readString(log));
        var result=FixtureEmitter.JSON.readTree(Files.readAllBytes(scratch.resolve("actual-result.json")));
        assertTrue(result.path("saved_inventory_verified").booleanValue());assertTrue(result.path("host_copy_readback_verified").booleanValue());
        assertFalse(result.path("game_started").booleanValue());assertFalse(result.path("business_acceptance_proven").booleanValue());
    }
}
