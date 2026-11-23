package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.Clausewitz;

/** Actual request/render/import paths only; no engine, death or delivery qualification. */
final class ControlledCrisis20FixtureTest {
    @TempDir Path temporary;
    private static Path repository() { return Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent(); }
    private static FollowupContracts.ControlledCrisis20Request request() {
        List<FollowupContracts.CrisisSceneRole> scenes=new ArrayList<>();
        for(int i=1;i<=20;i++) scenes.add(new FollowupContracts.CrisisSceneRole(i,Integer.toString(i)));
        return new FollowupContracts.ControlledCrisis20Request(3,"crisis-scenes20-engine-fixture",true,"21","22",scenes,
                new FollowupContracts.CrisisControls("23","24","25","26","27"));
    }
    @Test void exactClosedRequestEmitsItsOwnSourceBoundTenProducerManifestWithoutGameCredit() throws Exception {
        Path input=temporary.resolve("request.json");Files.write(input,FixtureEmitter.JSON.writeValueAsBytes(request()));
        assertEquals(request(),FixtureEmitter.readInput(input));
        var emitted=FixtureEmitter.emit(repository(),temporary.resolve("crisis20"),"authored-crisis20-fixture",FixtureEmitter.readInput(input));
        var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emitted.manifest().path())));
        assertEquals("crisis-scenes20-engine-fixture",manifest.path("case_id").textValue());
        assertTrue(manifest.path("receipt").path("fixture_contains_business_effects").booleanValue());
        assertEquals(10,manifest.path("producer_source_pins").size());assertEquals(3,manifest.path("receipt").path("required_markers").size());
        assertFalse(emitted.gameStarted());assertEquals("NOT_RUN",emitted.businessAcceptance());
        assertEquals(request(),FixtureEmitter.readInput(Path.of(emitted.fixture()).resolve("_xfma_request.json")));
        for(var fields=manifest.path("files").fieldNames();fields.hasNext();) {
            String name=fields.next();var actual=FixtureEmitter.pin(Path.of(emitted.fixture()).resolve(name));
            assertEquals(actual.sha256(),manifest.path("files").path(name).path("sha256").textValue());
        }
        var legacy=new FollowupContracts.ControlledFundingRequest(3,"perpetual-funding-engine-fixture",true);
        var prior=FixtureEmitter.emit(repository(),temporary.resolve("legacy"),"authored-crisis20-fixture",legacy);
        var old=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(prior.manifest().path())));
        assertEquals(6,old.path("producer_source_pins").size(),"Legacy six-producer closure must not be relabelled");
        assertFalse(old.path("files").has("common/scripted_effects/xfmc20_dispatch.txt"));
    }
    @Test void forgedIdentityContextPrivilegeAliasesAndNonIntegralSceneInputsRejectBeforeEmission() throws Exception {
        String good=FixtureEmitter.JSON.writeValueAsString(request());
        List<String> invalid=List.of(good.replace("true","false"),good.replace("true","1"),
                good.replace("\"schemaVersion\":3","\"schemaVersion\":3.0"),
                good.replace("\"sceneId\":1,","\"sceneId\":1.0,"),
                good.replace("\"accountId\":\"1\"","\"accountId\":1"),
                good.replace("\"accountId\":\"1\"","\"accountId\":\"2\""),
                good.replace("\"accountId\":\"1\"","\"accountId\":\"1\",\"isAI\":true"),
                good.replace("\"controls\":{","\"adult\":true,\"controls\":{"),
                good.replace("\"controls\":{","\"forcedTrait\":\"shy\",\"controls\":{"),
                good.replace("crisis-scenes20-engine-fixture","news-crisis"),
                good.replace("\"accountId\":\"1\"","\"accountId\":\"1000000001\""));
        int i=0;for(String text:invalid) {
            Path path=temporary.resolve("invalid-"+(i++)+".json");Files.writeString(path,text);
            assertThrows(java.io.IOException.class,()->FixtureEmitter.readInput(path),text);
        }
    }
    private static void walk(Clausewitz.Block block,java.util.function.Consumer<Clausewitz.Entry> visit) {
        for(var entry:block.entries()) { visit.accept(entry);if(entry.value() instanceof Clausewitz.Block child)walk(child,visit); }
    }
    @Test void generatedBusinessASTContainsOnlyDeclaredSeedsAndCallsProductionNoMoneyDeathOrClockPrimitive() throws Exception {
        var files=FollowupObservationScripts.renderControlledCrisis20(request(),Files.readString(repository().resolve("mod_financial_markets/common/scripted_effects/xfm_crisis_scenes.txt")));
        Set<String> writes=Set.of("xfm_news_scene","xfm_request_debtor","xfm_request_creditor","xfm_request_cents","xfm_request_day","xfm_request_kind","xfm_request_fund_eligible",
                "xfm_overdue_days","xfm_max_overdue_days","xfm_crisis_started_day","xfm_crisis_reviews","xfm_next_crisis_review","xfm_selected_debt","xfm_ui_debt_pay_cents");
        Set<String> calls=new HashSet<>();
        for(var file:files.entrySet()) {
            String path=file.getKey(),text=new String(file.getValue(),StandardCharsets.UTF_8);assertFalse(text.contains("${"));
            assertFalse(path.startsWith("common/on_action/"));
            if(!path.startsWith("common/")||!path.endsWith(".txt"))continue;
            var parsed=Clausewitz.parse(text);if(path.startsWith("common/scripted_effects/"))assertTrue(parsed.entries().size()<=20);
            walk(parsed,e->{
                assertFalse(Set.of("death","send_interface_toast","add_gold","remove_short_term_gold","create_character","effect_group","trigger_event","end_story").contains(e.key()),path+e.key());
                if(e.key().startsWith("xfm_")&&e.key().endsWith("_effect"))calls.add(e.key());
                if(Set.of("set_variable","change_variable","set_global_variable").contains(e.key())) {
                    var b=(Clausewitz.Block)e.value();String name=((Clausewitz.Atom)b.named("name").getFirst().value()).token();
                    assertTrue(name.startsWith("xfmc20_")||writes.contains(name),path+name);
                }
            });
        }
        assertEquals(Set.of("xfm_debt_cover_shortfall_effect","xfm_crisis_begin_effect","xfm_crisis_terminal_effect","xfm_crisis_terminal_with_selector_effect"),calls);
        assertTrue(files.containsKey("common/scripted_effects/xfmc20_selectors.txt"));
        var passive=Clausewitz.parse(new String(files.get("common/story_cycles/xfmc20_retained_observers.txt"),StandardCharsets.UTF_8));
        for(int epoch:List.of(6,7,8)) {
            var row=passive.block("xfma_market_evolution_e"+epoch+"_observer");
            assertEquals(1,row.entries().size());assertEquals("visible",row.entries().getFirst().key());
            assertEquals("no",((Clausewitz.Atom)row.entries().getFirst().value()).token());
        }
    }
    @Test void actualSavedImporterAndHostCopyRequireTheirOwnExplicitControlledFlag() throws Exception {
        var emitted=FixtureEmitter.emit(repository(),temporary.resolve("saved"),"authored-crisis20-fixture",request());
        Path shared=Path.of(System.getProperty("xfm.shared.source",repository().toString()));
        Path consumer=repository().resolve("mod_financial_markets/tools/src/test/resources/acceptance/verify_saved_observer_inventory.py");
        for(boolean allowed:List.of(false,true)) {
            Path scratch=temporary.resolve(allowed?"allowed":"rejected"),log=temporary.resolve(allowed?"allowed.log":"rejected.log");
            List<String> args=new ArrayList<>(List.of(System.getProperty("xfm.python","python"),"-B","-X","utf8",consumer.toString(),"--repo-root",repository().toString(),"--shared-source",shared.toString(),"--manifest",emitted.manifest().path(),"--scratch",scratch.toString()));
            if(allowed)args.add("--controlled-crisis20-fixture");
            Process p=new ProcessBuilder(args).directory(shared.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
            assertTrue(p.waitFor(90,TimeUnit.SECONDS));
            if(allowed) {
                assertEquals(0,p.exitValue(),Files.readString(log));
                var actual=FixtureEmitter.JSON.readTree(Files.readAllBytes(scratch.resolve("actual-result.json")));
                assertTrue(actual.path("saved_inventory_verified").booleanValue());assertTrue(actual.path("host_copy_readback_verified").booleanValue());
                assertFalse(actual.path("game_started").booleanValue());assertFalse(actual.path("business_acceptance_proven").booleanValue());
            } else assertNotEquals(0,p.exitValue());
        }
    }
}
