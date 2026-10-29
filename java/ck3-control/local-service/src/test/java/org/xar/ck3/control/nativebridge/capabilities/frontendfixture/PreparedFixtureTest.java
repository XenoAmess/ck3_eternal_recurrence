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
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual immutable-file producer/consumer and original Python business binder comparisons, no Game. */
final class PreparedFixtureTest {
    @TempDir Path temporary;
    record Fileset(PreparedFixture prepared,Path policy,Path profile) { }
    Fileset create(boolean scenario)throws Exception {
        Path state=Files.createDirectories(temporary.resolve(scenario?"scenario":"robert"));Path profile=Files.createDirectories(state.resolve("profile"));
        Files.createDirectories(profile.resolve("mod"));Path preparation=state.resolve("preparation.json");Files.writeString(preparation,"{}");
        Files.writeString(profile.resolve("dlc_load.json"),"{\"enabled_mods\":[\"mod/fixture.mod\"]}");
        Files.writeString(profile.resolve("pdx_settings.txt"),"language=\"english\"");Files.writeString(profile.resolve("mod/fixture.mod"),"name=\"fixture\"\npath=\""+profile.resolve("mod").toString().replace('\\','/')+"\"\n");
        ObjectNode policy=FrontendFixturePolicyTest.policy(scenario);((ObjectNode)policy.get("preparation")).put("path",preparation.toString()).put("sha256",ControlBuild.FileRef.measure(preparation).sha256());
        ObjectNode hashes=(ObjectNode)policy.get("profile_input_sha256");for(String key:List.of("dlc_load.json","pdx_settings.txt","mod/fixture.mod"))hashes.put(key,ControlBuild.FileRef.measure(profile.resolve(key)).sha256());
        Path input=state.resolve("policy.json");Files.write(input,StrictJson.canonical(policy,1<<20));var exact=ControlBuild.FileRef.measure(input);
        return new Fileset(PreparedFixture.prepare(new ExactRef(exact.path(),exact.bytes(),exact.sha256()),state,profile,"native_campaign"),input,profile);
    }
    @Test void realPreparationPinsCompleteMountedInputsAndDoesNotGrantGameplay()throws Exception {
        var files=create(false);files.prepared().verifyBeforeClaim();assertEquals(5,files.prepared().inputClosure().size());
        assertEquals(List.of("policy.json","preparation.json","dlc_load.json","fixture.mod","pdx_settings.txt"),
                files.prepared().inputClosure().stream().map(ref->Path.of(ref.path()).getFileName().toString()).toList());
        assertEquals(files.profile(),files.prepared().profileDirectory());assertEquals(FrontendFixturePolicy.Kind.ROBERT,files.prepared().binding().kind());
        assertEquals("ck3_submit_frontend_fixture_robert_start_v1",files.prepared().policy().publicTool());
        assertTrue(java.util.Arrays.stream(PreparedFixture.class.getDeclaredConstructors()).allMatch(c->java.lang.reflect.Modifier.isPrivate(c.getModifiers())));
    }
    @Test void bothActualPreparedInventoriesReachTheSoleInitialEpisodeProducerAndPersistentConsumers()throws Exception {
        var robert=create(false);var scenario=create(true);
        org.xar.ck3.control.service.root.InitialEpisodeFixturePolicyAssertions.assertPreparedInventoryRoundTrip(robert.prepared(),temporary.resolve("initial-robert"));
        org.xar.ck3.control.service.root.InitialEpisodeFixturePolicyAssertions.assertPreparedInventoryRoundTrip(scenario.prepared(),temporary.resolve("initial-scenario"));
    }
    @Test void actualSameContentFileReplacementCannotReestablishPreparedIdentity()throws Exception {
        var files=create(false);Path input=files.profile().resolve("mod/fixture.mod");byte[] same=Files.readAllBytes(input);
        Files.move(input,temporary.resolve("retained-old.mod"));Files.write(input,same);
        assertThrows(Exception.class,files.prepared()::verifySources);
    }
    @Test void newMountedFileAndChangedConfigRejectActualPreparedConsumer()throws Exception {
        var files=create(false);Files.writeString(files.profile().resolve("mod/new.mod"),"new");
        assertThrows(Exception.class,files.prepared()::verifySources);
    }
    @Test void freshLogsRequiredAtPreparationButActualMenuAndPostStartMayAppendLogs()throws Exception {
        var files=create(true);Files.createDirectories(files.profile().resolve("logs"));Files.writeString(files.profile().resolve("logs/debug.log"),"FIXTURE: qualified\nFIXTURE: switched\n");
        assertDoesNotThrow(files.prepared()::verifyBeforeClaim);assertDoesNotThrow(files.prepared()::verifySources);
        var measured=ControlBuild.FileRef.measure(files.policy());
        assertThrows(Exception.class,()->PreparedFixture.prepare(new ExactRef(measured.path(),measured.bytes(),measured.sha256()),files.prepared().stateDir(),files.profile(),"native_campaign"));
        var observation=FixtureQualificationLogs.observe(files.prepared());assertTrue(observation.qualified(files.prepared().policy()));
        Files.writeString(files.profile().resolve("logs/debug.log"),"FIXTURE: qualified\nFIXTURE: switched\nFIXTURE: FAIL\n");
        assertThrows(IllegalStateException.class,()->FixtureQualificationLogs.observe(files.prepared()).qualified(files.prepared().policy()));
    }
    @Test void actualOriginalPythonBusinessBinderCasesUseSameCurrentStrictConsumer()throws Exception {
        JsonNode oracle;
        try(var input=getClass().getResourceAsStream("/frontend-fixture/python-producer-oracle04.json")){assertNotNull(input);oracle=StrictJson.parse(input.readAllBytes(),1<<20);}
        var submission=FixtureStartSubmission.fromJson(oracle.get("submissions").get(0).get("receipt"));int cases=0;
        for(JsonNode row:oracle.get("business_cases")) {
            var policy=FrontendFixturePolicy.fromJson(row.get("policy"));
            var snapshot=OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row.get("snapshot"),1<<20)),"snapshot");
            var root=OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row.get("root"),1<<20)),"root");
            if(!row.get("error").isNull())assertThrows(IllegalArgumentException.class,()->FixtureBusinessQualification.actor(snapshot,root,policy,submission));
            else {
                var bound=FixtureBusinessQualification.actor(snapshot,root,policy,submission);
                assertEquals(!row.get("binding").isNull(),bound.isPresent());
                if(bound.isPresent()) {
                    assertEquals(row.get("binding").get("actor_character_id").bigIntegerValue(),bound.orElseThrow().actorCharacterId());
                    assertEquals(row.get("binding").get("primary_title_id").bigIntegerValue(),bound.orElseThrow().primaryTitleId());
                    assertEquals(row.get("binding").get("government_key").asText(),bound.orElseThrow().governmentKey());
                }
            }
            cases++;
        }
        assertEquals(4,cases);
    }
    @Test void exactLogLinesCountOnceAndRetainOriginalUnicodeSplitlinesSemantics() {
        byte[] raw="hit hit\r\nhit\u000bhit\u0085miss\u2028hit\n".getBytes(StandardCharsets.UTF_8);
        assertEquals(List.of(new FixtureQualificationLogs.Match("hit",4),new FixtureQualificationLogs.Match("miss",1)),FixtureQualificationLogs.count(raw,List.of("hit","miss")));
    }
}

