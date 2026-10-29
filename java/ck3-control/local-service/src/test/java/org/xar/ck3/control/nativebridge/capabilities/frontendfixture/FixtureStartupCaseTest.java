package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class FixtureStartupCaseTest {
    @TempDir Path temporary;
    private JsonNode oracle()throws Exception {
        try(var in=getClass().getResourceAsStream("/frontend-fixture/python-external-case-oracle04.json")){
            assertNotNull(in);return StrictJson.parse(in.readAllBytes(),1<<20);
        }
    }
    @Test void sixActualOriginalHandlersAndAllThirtySixRejectionsShareJavaProducer()throws Exception {
        int cases=0,negative=0;
        for(JsonNode row:oracle().get("cases")) {
            String module=row.get("module").asText();FixtureStartupCase.Handler handler=java.util.Arrays.stream(FixtureStartupCase.Handler.values())
                    .filter(value->value.file.equals(module+".py")).findFirst().orElseThrow();
            byte[] log=row.get("log").asText().getBytes(StandardCharsets.US_ASCII);
            var song=FixtureStartupCase.parseScope(log,"xqol_startup_actor","han_8052",handler.prefix);
            JsonNode original=row.get("result").get("proof");JsonNode expected=handler.steppe?original.get("song"):original;
            assertEquals(expected.get("runtime_character_id").intValue(),song.runtimeCharacterId());
            assertEquals(expected.get("byte_start").longValue(),song.byteStart());assertEquals(expected.get("byte_end").longValue(),song.byteEnd());
            assertEquals(expected.get("raw_scope_block_sha256").asText(),song.blockSha256());
            int actor=handler.steppe?FixtureStartupCase.parseScope(log,"xqol_steppe_startup_actor","194333","ZQD120STEPPEQUAL").runtimeCharacterId():song.runtimeCharacterId();
            FixtureStartupCase.validateIntro(row.get("snapshot"),row.get("event_window"),actor);
            for(JsonNode mutation:row.get("negative")) {
                assertTrue(mutation.get("rejected").booleanValue());String kind=mutation.get("mutation").asText();
                ObjectNode snapshot=row.get("snapshot").deepCopy(),window=row.get("event_window").deepCopy();
                switch(kind) {
                    case "wrongActor"->((ObjectNode)snapshot.get("played_character")).put("character_id",actor+1);
                    case "boolInstance"->((ObjectNode)snapshot.get("active_event")).put("instance_id",true);
                    case "wrongFrame"->((ObjectNode)window.get("current_event_window_context")).put("snapshot_revision",28);
                    case "disabled"->((ObjectNode)window.get("current_event_window_context").get("options").get(0)).put("enabled",false);
                    case "duplicateScope"->{byte[] duplicated=(row.get("log").asText()+row.get("log").asText()).getBytes(StandardCharsets.US_ASCII);
                        assertThrows(Exception.class,()->FixtureStartupCase.parseScope(duplicated,"xqol_startup_actor","han_8052",handler.prefix));negative++;continue;}
                    case "failureScope"->{String prefix=handler.prefix+": TEST FAIL "+(List.of("ZQAUITAIL","ZQAGUARD","ZQREL").contains(handler.prefix)?"actual_song_actor":"actual_song_actor_D0");
                        byte[] failed=(row.get("log").asText()+prefix+"\n").getBytes(StandardCharsets.US_ASCII);
                        assertThrows(Exception.class,()->FixtureStartupCase.parseScope(failed,"xqol_startup_actor","han_8052",handler.prefix));negative++;continue;}
                    default->throw new AssertionError("unreviewed original oracle branch");
                }
                assertThrows(IllegalArgumentException.class,()->FixtureStartupCase.validateIntro(snapshot,window,actor));negative++;
            }
            cases++;
        }
        assertEquals(6,cases);assertEquals(36,negative);
    }
    @Test void completeDecisionCodecPreservesEvidenceAndDecimalRangeRejectsWrongTypes()throws Exception {
        var source=new ExactRef(temporary.resolve("handler.java").toString(),1,"a".repeat(64));
        var log=new ExactRef(temporary.resolve("debug.log").toString(),99,"b".repeat(64));
        var scope=new FixtureStartupHandler.ActorScope(121,"han_8052","actual",1,3,4,9007199254740993L,9007199254741000L,"c".repeat(64));
        var selected=new FixtureStartupHandler.SelectDisplayedOption(1,1,new FixtureStartupHandler.ScopeEvidence(log,List.of(scope),false),source);
        for(var decision:List.of(selected,new FixtureStartupHandler.AutomaticSharedPolicy(source),new FixtureStartupHandler.ObserveOnly(source))) {
            assertEquals(decision,FixtureStartupHandler.decodeDecision(FixtureStartupHandler.encodeDecision(decision)));
        }
        var encoded=DriverJson.toNode(FixtureStartupHandler.encodeDecision(selected));
        assertEquals("9007199254740993",encoded.get("proof").get("scopes").get(0).get("byte_start").textValue());
        assertEquals(List.of(source,log),FixtureStartupHandler.decisionSources(selected));
        ((ObjectNode)encoded).put("event_instance_id",true);
        assertThrows(IllegalArgumentException.class,()->FixtureStartupHandler.decodeDecision(DriverJson.object(StrictJson.canonical(encoded,65536),65536)));
    }
    @Test void actualSourceBoundConfigurationRejectsUnreviewedHandlerAndIncompleteClosure()throws Exception {
        var support=new PreparedFixtureTest();support.temporary=temporary;var files=support.create(false);
        Path implementation=temporary.resolve("FixtureStartupCase.java");Files.writeString(implementation,"reviewed Java body");
        var source=ControlBuild.FileRef.measure(implementation);var sourceRef=new ExactRef(source.path(),source.bytes(),source.sha256());
        var row=StrictJson.object().put("schema",FixtureStartupCase.SCHEMA).put("state_dir",files.prepared().stateDir().toString()).put("handler","ORIGINAL");
        row.set("handler_source",sourceRef.toJson());row.set("original_handler",sourceRef.toJson());row.putArray("original_dependencies");
        Path contract=temporary.resolve("external.json");Files.write(contract,StrictJson.canonical(row,65536));var measured=ControlBuild.FileRef.measure(contract);
        assertThrows(Exception.class,()->FixtureStartupCase.prepare(new ExactRef(measured.path(),measured.bytes(),measured.sha256()),files.prepared()));
        assertTrue(java.util.Arrays.stream(FixtureStartupCase.class.getDeclaredConstructors()).allMatch(value->java.lang.reflect.Modifier.isPrivate(value.getModifiers())));
    }
    @Test void actualPreparedJavaHandlerConsumesAllSixOriginalProducersAndPinsPhysicalSources()throws Exception {
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository,"real original workspace is mandatory; this regression cannot skip its actual source closure");
        Path originals=Path.of(repository).resolve("tools/ck3_mod_acceptance_cases");int cases=0;
        for(JsonNode row:oracle().get("cases")) {
            String module=row.get("module").asText();var handler=java.util.Arrays.stream(FixtureStartupCase.Handler.values()).filter(value->value.file.equals(module+".py")).findFirst().orElseThrow();
            Path cell=Files.createDirectories(temporary.resolve(module));var support=new PreparedFixtureTest();support.temporary=cell;var files=support.create(false);
            // Source DATA is not class-loader qualification. The real Root separately checks actual selected/loaded classes.
            Path implementation=cell.resolve("FixtureStartupCase.java");Files.writeString(implementation,"reviewed source-only software input");
            var config=StrictJson.object().put("schema",FixtureStartupCase.SCHEMA).put("state_dir",files.prepared().stateDir().toString()).put("handler",handler.name());
            config.set("handler_source",exact(implementation).toJson());config.set("original_handler",exact(originals.resolve(handler.file)).toJson());
            var dependencies=config.putArray("original_dependencies");var names=new java.util.ArrayList<>(List.of("xqol_scope.py","ck3_mod_acceptance_prepare.py","__init__.py"));
            switch(handler) {
                case ORIGINAL->names.add("xqol_original_plans.json");
                case UI_TAIL->names.addAll(List.of("xqol_adapter.py","xqol_ui.py","xqol_original_plans.json","xqol_defense_and_ui.json"));
                case ORDINARY_ASYNC->names.addAll(List.of("xqol_ordinary_async.json","xqol_ordinary_async.plan.json","xqol_ordinary_async.rules.json"));
                default->{ }
            }
            for(String name:names)dependencies.add(exact(name.equals("ck3_mod_acceptance_prepare.py")?originals.getParent().resolve(name):originals.resolve(name)).toJson());
            Path contract=cell.resolve("case.json");Files.write(contract,StrictJson.canonical(config,65536));var prepared=FixtureStartupCase.prepare(exact(contract),files.prepared());
            Files.createDirectories(files.profile().resolve("logs"));Files.writeString(files.profile().resolve("logs/debug.log"),row.get("log").asText());
            OpportunityJson.Obj snapshot=DriverJson.object(StrictJson.canonical(row.get("snapshot"),65536),65536),window=DriverJson.object(StrictJson.canonical(row.get("event_window"),65536),65536);
            var decision=prepared.decide(files.prepared(),snapshot,window);assertEquals(1,decision.eventInstanceId());assertEquals(1,decision.optionNumber());
            assertEquals(handler.steppe?2:1,decision.proof().scopes().size());assertFalse(decision.proof().businessPass());
            prepared.verifyOriginal(row.get("log").asText().getBytes(StandardCharsets.US_ASCII),snapshot,window,decision);
            assertEquals(decision,FixtureStartupHandler.decodeDecision(FixtureStartupHandler.encodeDecision(decision)));
            byte[] same=Files.readAllBytes(implementation);Files.move(implementation,cell.resolve("retained-source.java"));Files.write(implementation,same);
            assertThrows(Exception.class,prepared::verifySources,"same-byte physical replacement must not renew source identity");cases++;
        }
        assertEquals(6,cases);
    }
    private ExactRef exact(Path source)throws Exception {var ref=ControlBuild.FileRef.measure(source);return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
}
