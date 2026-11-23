package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.save.Clausewitz;

/** Source producer tests only. Engine execution/physical SAVE/claim verification remain NOT_RUN. */
final class ControlledFuturesRiskFixtureTest {
    private static ControlledFuturesRiskFixture.Request request() {
        return new ControlledFuturesRiskFixture.Request(3,ControlledFuturesRiskFixture.CASE_ID,true);
    }
    private static String source(String path) {
        return new String(ControlledFuturesRiskFixture.render(request()).get(path),StandardCharsets.UTF_8);
    }
    private static void walk(Clausewitz.Block block,Consumer<Clausewitz.Entry> visitor) {
        for(var entry:block.entries()) { visitor.accept(entry); if(entry.value() instanceof Clausewitz.Block child)walk(child,visitor); }
    }
    @Test void riskRequestRequiresTheExactExplicitIsolatedSchema() {
        assertThrows(IllegalArgumentException.class,()->new ControlledFuturesRiskFixture.Request(2,ControlledFuturesRiskFixture.CASE_ID,true));
        assertThrows(IllegalArgumentException.class,()->new ControlledFuturesRiskFixture.Request(3,"derivatives",true));
        assertThrows(IllegalArgumentException.class,()->new ControlledFuturesRiskFixture.Request(3,ControlledFuturesRiskFixture.CASE_ID,false));
        assertThrows(NullPointerException.class,()->ControlledFuturesRiskFixture.render(null));
        assertEquals(6,ControlledFuturesRiskFixture.markers().size());
    }
    @Test void realParserAcceptsFiniteAssetsAndOnlyOriginalInputsOrPrivateSnapshotsAreWritten() {
        Set<String> inputs=Set.of("xfm_request_cents","xfm_ui_fund_donation_cents","xfm_selected_coin","xfm_futures_perpetual",
            "xfm_futures_expiry_day","xfm_futures_side","xfm_futures_lots","xfm_futures_leverage","xfm_futures_limit_cents",
            "xfm_futures_selected_position","xfm_futures_stop_cents","xfm_futures_take_profit_cents");
        Set<String> calls=new HashSet<>();List<String> seeds=new ArrayList<>();
        ControlledFuturesRiskFixture.render(request()).forEach((path,bytes)->{
            assertEquals(0xef,Byte.toUnsignedInt(bytes[0]));assertEquals(0xbb,Byte.toUnsignedInt(bytes[1]));assertEquals(0xbf,Byte.toUnsignedInt(bytes[2]));
            String text=new String(bytes,StandardCharsets.UTF_8);assertFalse(text.contains("on_game_start_after_lobby"));
            if(!path.startsWith("common/")||!path.endsWith(".txt"))return;
            var ast=Clausewitz.parse(text);
            if(path.startsWith("common/scripted_effects/"))assertTrue(ast.entries().size()<=20,path);
            walk(ast,e->{
                assertNotEquals("create_story",e.key(),"Only real production APIs allocate financial identities");
                if(e.key().equals("add_gold"))seeds.add(e.value().render());
                if(e.key().startsWith("xfm_")&&e.key().endsWith("_effect"))calls.add(e.key());
                if(Set.of("set_variable","change_variable").contains(e.key())) {
                    String name=((Clausewitz.Block)e.value()).named("name").getFirst().value().render();
                    assertTrue(name.startsWith("xfmr_")||inputs.contains(name),path+": "+name);
                }
            });
        });
        assertEquals(List.of("20000"),seeds);
        assertEquals(Set.of("xfm_finance_ensure_effect","xfm_oracle_index_bootstrap_effect","xfm_oracle_index_daily_effect",
            "xfm_finance_ensure_account_effect","xfm_finance_deposit_effect","xfm_debt_donate_fund_effect",
            "xfm_futures_ensure_market_effect","xfm_futures_submit_effect","xfm_futures_set_stops_effect",
            "xfm_futures_position_daily_effect","xfm_debt_cover_shortfall_effect"),calls);
    }
    @Test void worldInputsAreActualOriginalBasketCountyEffectsAndAllThirtyTwoIdentitiesAreRetained() {
        String world=source("common/scripted_effects/xfmr_world.txt"),book=source("common/scripted_effects/xfmr_book.txt");
        assertTrue(world.contains("variable = xfm_oracle_counties"));
        assertTrue(world.contains("change_county_control = xfmr_control_prepare_delta_value"));
        assertTrue(world.contains("change_prosperity_level = xfmr_prosperity_prepare_delta_value"));
        assertTrue(world.contains("name = xfmr_$PHASE$_county32 value = scope:xfmr_actual_county"));
        assertTrue(world.contains("name = xfmr_$PHASE$_holder32 value = scope:xfmr_actual_county.holder"));
        assertTrue(world.contains("name = xfmr_$PHASE$_war32 value = 1"));
        assertTrue(book.contains("change_county_control = xfmr_control_shock_delta_value"));
        String observe=source("common/scripted_effects/xfmr_observe.txt");
        assertTrue(observe.contains("change_prosperity_level = -25"));
        for(String text:List.of(world,book,observe)) {
            assertFalse(text.contains("name = xfm_mark_cents"));assertFalse(text.contains("name = xfm_oracle_day"));
            assertFalse(text.contains("name = xfm_index_cents"));assertFalse(text.contains("name = xfm_day"));
        }
        assertTrue(source("common/scripted_triggers/xfmr_guards.txt").contains("var:xfm_oracle_war_bps <= 6000"));
    }
    @Test void realActionsAreOneShotAndTheUnfundedGapContractHasNoInventedReplacement() {
        String seed=source("common/scripted_effects/xfmr_seed.txt"),book=source("common/scripted_effects/xfmr_book.txt");
        assertTrue(seed.indexOf("name = xfmr_setup_attempted")<seed.indexOf("xfm_finance_ensure_effect"));
        assertTrue(book.indexOf("name = xfmr_book_attempted")<book.indexOf("xfmr_submit_effect = { ROLE = stop_buy"));
        assertEquals(3,seed.split(java.util.regex.Pattern.quote("xfmr_create_actor_effect = { ROLE"),-1).length-1);
        assertTrue(book.contains("ROLE = gap_buy EXPIRY = 32 SIDE = 1 LOTS = 100 LEV = 5 PRICE = 150"));
        assertTrue(book.contains("ROLE = stop_replacement EXPIRY = 30 SIDE = 1 LOTS = 1 LEV = 1 PRICE = 110"));
        assertTrue(book.contains("ROLE = liquidation_replacement EXPIRY = 31 SIDE = 1 LOTS = 1 LEV = 1 PRICE = 120"));
        assertFalse(book.contains("gap_replacement"));assertTrue(book.contains("xfm_futures_stop_cents value = 135"));
        String observe=source("common/scripted_effects/xfmr_observe.txt");
        assertTrue(observe.indexOf("name = xfmr_second_attempted")<observe.indexOf("change_prosperity_level = -25"));
        assertTrue(observe.indexOf("PHASE = retry_before")<observe.indexOf("xfm_futures_position_daily_effect = yes"));
        assertTrue(observe.indexOf("xfm_futures_position_daily_effect = yes")<observe.indexOf("PHASE = retry_after"));
        assertFalse(observe.contains("xfm_finance_daily_effect = yes"));
    }
    @org.junit.jupiter.api.io.TempDir java.nio.file.Path temporary;
    @Test void actualEmitterRequiresThePackagedRiskComponentAndPreservesOldObserverPrivilege() throws Exception {
        var input=new FollowupContracts.ControlledFuturesRiskRequest(3,ControlledFuturesRiskFixture.CASE_ID,true);
        var repo=java.nio.file.Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent();
        var wire=temporary.resolve("request.json");java.nio.file.Files.write(wire,FixtureEmitter.JSON.writeValueAsBytes(input));
        assertEquals(input,FixtureEmitter.readInput(wire));
        var emission=FixtureEmitter.emit(repo,temporary.resolve("risk"),"controlled-risk-source-test",input);
        var manifest=FixtureEmitter.JSON.readTree(java.nio.file.Files.readAllBytes(java.nio.file.Path.of(emission.manifest().path())));
        assertTrue(manifest.path("receipt").path("fixture_contains_business_effects").booleanValue());
        assertEquals(ControlledFuturesRiskFixture.CASE_ID,manifest.path("case_id").textValue());
        assertEquals(11,manifest.path("producer_source_pins").size(),"six original + actual risk component + four selected production sources");
        assertFalse(emission.gameStarted());assertEquals("NOT_RUN",emission.businessAcceptance());
        for(var names=manifest.path("files").fieldNames();names.hasNext();) {
            String name=names.next();var pin=FixtureEmitter.pin(java.nio.file.Path.of(emission.fixture()).resolve(name));
            assertEquals(pin.sha256(),manifest.path("files").path(name).path("sha256").textValue());
        }
        for(String bad:List.of(
            "{\"schemaVersion\":3,\"caseId\":\"futures-risk-engine-fixture\"}",
            "{\"schemaVersion\":3,\"caseId\":\"futures-risk-engine-fixture\",\"controlledFixtureOnly\":false}",
            "{\"schemaVersion\":3,\"caseId\":\"futures-risk-engine-fixture\",\"controlledFixtureOnly\":true,\"price\":150}")) {
            java.nio.file.Files.writeString(wire,bad);assertThrows(java.io.IOException.class,()->FixtureEmitter.readInput(wire));
        }
        assertFalse(FollowupObservationScripts.renderControlledFunding(new FollowupContracts.ControlledFundingRequest(
            3,"perpetual-funding-engine-fixture",true)).containsKey("common/scripted_effects/xfmr_world.txt"));
        assertFalse(ObservationScripts.render(new AcceptanceContracts.Request(1,"1128")).containsKey("common/scripted_effects/xfmr_seed.txt"));
    }
}
