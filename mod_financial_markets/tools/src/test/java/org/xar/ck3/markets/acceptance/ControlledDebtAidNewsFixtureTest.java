package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.Clausewitz;

/** Source/strict import only; money is executed separately in the existing full-book AST VM. */
final class ControlledDebtAidNewsFixtureTest {
    @TempDir Path temporary;
    private static final String CASE = "debt-aid-news-engine-fixture";
    private static Path repository() { return Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent(); }
    private static FollowupContracts.ControlledDebtAidNewsRequest input() {
        return new FollowupContracts.ControlledDebtAidNewsRequest(3, CASE, true,
                new FollowupContracts.ControlledDebtParticipants("1", "2", "3"));
    }
    private static void walk(Clausewitz.Block block, Consumer<Clausewitz.Entry> visitor) {
        for (var entry : block.entries()) {
            visitor.accept(entry);
            if (entry.value() instanceof Clausewitz.Block child) walk(child, visitor);
        }
    }
    @Test void exactNewControlledRequestHasItsOwnActualManifestAndOriginalSixProducerPins() throws Exception {
        Path wire=temporary.resolve("request.json"); Files.write(wire,FixtureEmitter.JSON.writeValueAsBytes(input()));
        assertEquals(input(),FixtureEmitter.readInput(wire));
        var emitted=FixtureEmitter.emit(repository(),temporary.resolve("debt"),"authored-debt-fixture",FixtureEmitter.readInput(wire));
        var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emitted.manifest().path())));
        assertEquals(CASE,manifest.path("case_id").textValue());
        assertTrue(manifest.path("receipt").path("fixture_contains_business_effects").booleanValue());
        assertEquals(6,manifest.path("producer_source_pins").size());
        assertEquals(2,manifest.path("receipt").path("required_markers").size());
        assertFalse(emitted.gameStarted()); assertEquals("NOT_RUN",emitted.businessAcceptance());
        assertEquals(input(),FixtureEmitter.readInput(Path.of(emitted.fixture()).resolve("_xfma_request.json")));
        for(var files=manifest.path("files").fieldNames();files.hasNext();) {
            String name=files.next(); var pin=FixtureEmitter.pin(Path.of(emitted.fixture()).resolve(name));
            assertEquals(pin.sha256(),manifest.path("files").path(name).path("sha256").textValue());
        }
    }
    @Test void privilegeAndParticipantsStayClosedTypedDistinctAndCannotRelabelNaturalOrFundingCases() throws Exception {
        String valid=FixtureEmitter.JSON.writeValueAsString(input());
        List<String> bad=List.of(valid.replace("true","false"),valid.replace("true","1"),
            valid.replace("\"schemaVersion\":3","\"schemaVersion\":2"),
            valid.replace("\"schemaVersion\":3","\"schemaVersion\":3.0"),
            valid.replace(CASE,"news-crisis"), valid.replace(CASE,"perpetual-funding-engine-fixture"),
            valid.replace("\"debtorAccountId\":\"1\"","\"debtorAccountId\":1"),
            valid.replace("\"debtorAccountId\":\"1\"","\"debtorAccountId\":\"01\""),
            valid.replace("\"debtorAccountId\":\"1\"","\"debtorAccountId\":\"1000000001\""),
            valid.replace("\"debtorAccountId\":\"1\"","\"debtorAccountId\":\"2\""),
            valid.replace("\"debtorAccountId\":\"1\"","\"debtorAccountId\":\"1\",\"debtorAccountId\":\"1\""),
            valid.replace("\"participants\":{","\"gold\":1,\"participants\":{"));
        int index=0; for(String body:bad) {
            Path path=temporary.resolve("bad-"+(index++)+".json");Files.writeString(path,body);
            assertThrows(IOException.class,()->FixtureEmitter.readInput(path),body);
        }
        var original=new FollowupContracts.ControlledFundingRequest(3,"perpetual-funding-engine-fixture",true);
        Path funding=temporary.resolve("funding.json");Files.write(funding,FixtureEmitter.JSON.writeValueAsBytes(original));
        assertEquals(original,FixtureEmitter.readInput(funding));
        assertThrows(IllegalArgumentException.class,()->new FollowupContracts.Request(2,FollowupContracts.Profile.NEWS_CRISIS,1,
            new FollowupContracts.ActorBinding(FollowupContracts.ActorMode.CURRENT_PLAYER,null),
            new FollowupContracts.Targets("3",null,null,null,null,null),null,null));
    }
    @Test void parsedPayloadHasOnlyTwoExplicitApiLiabilityCallsAndNoTerminalMoneyOrClockSetter() {
        Set<String> allowed=Set.of("xfm_request_debtor","xfm_request_creditor","xfm_request_cents","xfm_request_day",
            "xfm_request_kind","xfm_request_fund_eligible","xfm_selected_debt");
        Set<String> calls=new HashSet<>();
        var scripts=FollowupObservationScripts.renderControlledDebtAidNews(input());
        scripts.forEach((path,bytes)->{
            assertArrayEquals(new byte[]{(byte)0xef,(byte)0xbb,(byte)0xbf},java.util.Arrays.copyOf(bytes,3));
            String text=new String(bytes,StandardCharsets.UTF_8); assertFalse(text.contains("${"));
            if(!path.endsWith(".txt")||path.startsWith("gui/"))return;
            var parsed=Clausewitz.parse(text);
            if(path.startsWith("common/scripted_effects/"))assertTrue(parsed.entries().size()<=20);
            walk(parsed,e->{
                assertFalse(Set.of("death","add_gold","remove_short_term_gold","create_character","add_stress",
                    "effect_group","on_game_start_after_lobby","trigger_event","send_interface_toast").contains(e.key()),path+":"+e.key());
                assertFalse(e.key().contains("terminal")||e.key().startsWith("xfm_crisis_"));
                if(e.key().equals("create_story"))assertEquals("xfmd_claim_source",((Clausewitz.Block)e.value()).named("type").getFirst().value().render());
                if(e.key().startsWith("xfm_")&&e.key().endsWith("_effect"))calls.add(e.key());
                if(Set.of("set_variable","change_variable","set_global_variable").contains(e.key())) {
                    var body=(Clausewitz.Block)e.value();
                    String name=body.named("name").getFirst().value().render();
                    assertTrue(name.startsWith("xfmd_")||allowed.contains(name),path+":"+name);
                }
            });
        });
        assertEquals(Set.of("xfm_debt_cover_shortfall_effect","xfm_debt_repay_effect","xfm_debt_restructure_selected_effect"),calls);
        assertFalse(scripts.keySet().stream().anyMatch(p->p.startsWith("common/on_action/")));
        assertTrue(scripts.containsKey("gui/scripted_widgets/xfmd_widget.txt"));
        assertTrue(scripts.containsKey("gui/xfmd_widget.gui"));
        var schema2=new FollowupContracts.Request(2,FollowupContracts.Profile.DERIVATIVES,1,
            new FollowupContracts.ActorBinding(FollowupContracts.ActorMode.CURRENT_PLAYER,null),
            new FollowupContracts.Targets("3",null,null,null,null,null,"1"),null,null);
        assertFalse(FollowupObservationScripts.render(schema2).keySet().stream().anyMatch(p->p.contains("xfmd_")));
    }
    @Test void actualSavedImporterAndHostCopyRequireTheExplicitDebtControlledFlag() throws Exception {
        var emitted=FixtureEmitter.emit(repository(),temporary.resolve("saved-debt"),"authored-debt-fixture",input());
        Path descriptorPath=Path.of(emitted.fixture()).resolve("descriptor.mod");
        var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emitted.manifest().path())));
        assertTrue(manifest.path("files").has("descriptor.mod"),"Shared importer needs a complete descriptor inventory");
        assertArrayEquals(FollowupObservationScripts.renderControlledDebtAidNews(input()).get("descriptor.mod"),Files.readAllBytes(descriptorPath));
        var descriptor=Clausewitz.parse(Files.readString(descriptorPath,StandardCharsets.UTF_8));
        assertEquals(Set.of("name","version","supported_version"),descriptor.entries().stream().map(Clausewitz.Entry::key).collect(java.util.stream.Collectors.toSet()));
        assertEquals(3,descriptor.entries().size());
        assertEquals(FixtureEmitter.JSON.writeValueAsString("1"),descriptor.named("version").getFirst().value().render());
        assertEquals(FixtureEmitter.JSON.writeValueAsString("1.21.*"),descriptor.named("supported_version").getFirst().value().render());
        Path shared=Path.of(System.getProperty("xfm.shared.source",repository().toString())).toAbsolutePath().normalize();
        Path consumer=repository().resolve("mod_financial_markets/tools/src/test/resources/acceptance/verify_saved_observer_inventory.py");
        Path scratch=temporary.resolve("consumer"), log=temporary.resolve("consumer.log");
        Process process=new ProcessBuilder(System.getProperty("xfm.python","python"),"-B","-X","utf8",consumer.toString(),
            "--repo-root",repository().toString(),"--shared-source",shared.toString(),"--manifest",emitted.manifest().path(),
            "--scratch",scratch.toString(),"--controlled-debt-aid-fixture").directory(shared.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        assertTrue(process.waitFor(90,TimeUnit.SECONDS));assertEquals(0,process.exitValue(),Files.readString(log));
        var result=FixtureEmitter.JSON.readTree(Files.readAllBytes(scratch.resolve("actual-result.json")));
        assertTrue(result.path("saved_inventory_verified").booleanValue());assertTrue(result.path("host_copy_readback_verified").booleanValue());
        assertFalse(result.path("game_started").booleanValue());assertFalse(result.path("business_acceptance_proven").booleanValue());
        Path rejected=temporary.resolve("without-flag"), rejectLog=temporary.resolve("without-flag.log");
        Process noFlag=new ProcessBuilder(System.getProperty("xfm.python","python"),"-B","-X","utf8",consumer.toString(),
            "--repo-root",repository().toString(),"--shared-source",shared.toString(),"--manifest",emitted.manifest().path(),
            "--scratch",rejected.toString()).directory(shared.toFile()).redirectErrorStream(true).redirectOutput(rejectLog.toFile()).start();
        assertTrue(noFlag.waitFor(90,TimeUnit.SECONDS));assertNotEquals(0,noFlag.exitValue());
    }
}
