package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.g2.m7.GoalCodec;

/** Real policy codec and fresh driver domain using software originals; guarded publication has its own bootstrap test. */
final class InitialEpisodeProducerTest {
    @TempDir Path temporary;
    @Test void actualFrozenPolicyToFreshDriverPreservesAllThirteenFieldsAndRoundTrips()throws Exception {
        InitialEpisodePolicy policy=policy("ordinary_campaign_succession","xar_off","absent_by_fresh_campaign_xar_off_contract");
        var produced=InitialDriverState.create(frame("73"),"actual-pipe","java-start-"+"a".repeat(32),policy);
        var driver=produced.driver();var wire=driver.encode();assertArrayEquals(wire,DriverStateSnapshot.decodeComplete(wire).encode());
        var body=ContinuityJson.parseObject(wire,65536);assertEquals(13,body.size());assertEquals(2,body.get("format_version").intValue());
        assertTrue(driver.commandHistory().isEmpty());assertInstanceOf(DriverStateSnapshot.NullValue.class,driver.lastCheckpoint());
        var goalSlot=assertInstanceOf(DriverStateSnapshot.Value.class,driver.campaignGoal());
        var goal=GoalCodec.decodeGoal(goalSlot.json());
        assertEquals(driver.session().episodeRunId(),goal.campaignId());
        assertEquals(73,goal.originCharacterId());assertEquals(73,goal.currentCharacterId());
        assertEquals(0,goal.progress().reconciledSuccessions());assertTrue(goal.progress().lastSuccession().isEmpty());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,driver.successionExpectation());
        assertTrue(body.get("rollback_war_failure").isNull());assertTrue(body.get("rollback_war_failures").isArray());assertTrue(body.get("rollback_war_failures").isEmpty());
        assertEquals("ordinary_campaign_succession",body.get("succession_lifecycle").get("lifecycle").textValue());
        assertEquals(BigInteger.valueOf(73),driver.session().actorId());
    }
    @Test void rogueFreshEpisodeKeepsTheActualNullCampaignGoal()throws Exception {
        InitialEpisodePolicy policy=policy("rogue_one_life","xar_on","terminal_settlement_required");
        var produced=InitialDriverState.create(frame("73"),"actual-pipe","rogue-first-episode",policy);
        assertInstanceOf(DriverStateSnapshot.NullValue.class,produced.driver().campaignGoal());
        var reopened=DriverStateSnapshot.decodeComplete(produced.driver().encode());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,reopened.campaignGoal());
        assertArrayEquals(produced.driver().encode(),reopened.encode());
    }
    @Test void freshActorRejectsInvalidTypesAndSentinelButAcceptsSignedInt32Boundaries()throws Exception {
        var policy=policy("ordinary_campaign_succession","xar_off","absent_by_fresh_campaign_xar_off_contract");
        for(String wrong:new String[]{"true","73.0","-1","null","\"73\"","-2147483649","2147483648"}) {
            assertThrows(IllegalArgumentException.class,()->InitialDriverState.create(frame(wrong),"actual-pipe","episode",policy));
        }
        for(String valid:new String[]{"0","2147483647","-2147483648","-2147483646"}) {
            var produced=InitialDriverState.create(frame(valid),"actual-pipe","episode",policy);
            var reopened=DriverStateSnapshot.decodeComplete(produced.driver().encode());
            assertEquals(new BigInteger(valid),reopened.session().actorId());
            assertArrayEquals(produced.driver().encode(),reopened.encode());
            var goal=GoalCodec.decodeGoal(assertInstanceOf(DriverStateSnapshot.Value.class,reopened.campaignGoal()).json());
            assertEquals(Integer.parseInt(valid),goal.originCharacterId());
            assertEquals(Integer.parseInt(valid),goal.currentCharacterId());
            assertEquals(goal,GoalCodec.decodeGoal(GoalCodec.encodeGoal(goal)));
        }
    }
    @Test void unknownLifecycleAndMissingFrozenEnvironmentCannotInitializeAPlayableEpisode()throws Exception {
        assertThrows(IllegalArgumentException.class,()->policy("unknown",null,"unknown"));
        var policy=policy("ordinary_campaign_succession","xar_off","absent_by_fresh_campaign_xar_off_contract");
        Files.writeString(Path.of(policy.environment().path()),"{}");
        assertThrows(java.io.IOException.class,policy::verify);
    }
    @Test void actualPolicyIdentityMutationCannotBeReclassifiedAsASecondEmptyNewLife()throws Exception {
        var policy=policy("rogue_one_life","xar_on","terminal_settlement_required");
        Files.writeString(Path.of(policy.source().path()),"{}");
        assertThrows(java.io.IOException.class,policy::verify);
    }
    @Test void frozenRulesCannotBeOverriddenByAClaimedModeOrFreshPact()throws Exception {
        Path environment=temporary.resolve("actual-on.json");
        Files.writeString(environment,"{\"environment_sha256\":\""+"e".repeat(64)+"\",\"rules\":{\"profile\":[{\"rule\":\"xar_enabled\",\"setting\":\"xar_on\"}]}}");
        var env=ControlBuild.FileRef.measure(environment);
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.encode(env,
                InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT));
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.encode(env,
                InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE,InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT));
    }
    @Test void actualAbsenceRequiresOriginalFilesReviewAndTheSameGameBirth()throws Exception {
        var manifest=absenceManifest("actual-profile");
        Path log=Path.of(StrictJson.text(manifest.get("verified_mod_absence").get("startup_log_original_path")));
        Path environment=temporary.resolve("actual-absence.json");Files.write(environment,ContinuityJson.canonical(manifest));
        var policy=writePolicyFixture(temporary.resolve("absence-policy.json"),ControlBuild.FileRef.measure(environment),
                InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT);
        policy.verifyGame(new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134055108000000017"))));
        assertThrows(IllegalArgumentException.class,()->policy.verifyGame(new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134055108000000018")))));
        Files.writeString(log,"changed");assertThrows(java.io.IOException.class,policy::verify);
    }
    @Test void absenceFiletimeCanonicalStringsRoundTripAtUint64Boundaries()throws Exception {
        for(String raw:new String[]{"1","18446744073709551615"}) {
            var manifest=absenceManifest("boundary-profile-"+raw);
            ContinuityJson.object(manifest.get("verified_mod_absence")).put("game_creation_filetime",raw);
            var policy=absencePolicy(manifest,"boundary-"+raw);
            var actual=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger(raw)));
            policy.verifyGame(actual);
            var reopened=InitialEpisodePolicy.readExact(policy.source(),ControlBuild.FileRef.measure(Path.of(policy.environment().path())));
            reopened.verifyGame(actual);
            assertArrayEquals(policy.lifecycle().bytes(),reopened.lifecycle().bytes());
            BigInteger wrong=raw.equals("1")?BigInteger.TWO:BigInteger.ONE;
            assertThrows(ContractViolationException.class,()->reopened.verifyGame(new GameGeneration(42,new PythonOnlyUInt64(wrong))));
        }
    }
    @Test void absenceFiletimeRejectsLegacyNumbersAndMalformedFieldsWithoutWideningJson()throws Exception {
        var manifest=absenceManifest("invalid-profile");
        String[] wrong={"\"0\"","\"01\"","\"+1\"","\"-1\"","\"1.0\"","\"1e3\"","\" 1\"","\"1 \"","\"\"",
                "\"18446744073709551616\"","\"999999999999999999999\"","1","9007199254740991","134055108000000017",
                "1.0","true","null","[]","{}"};
        for(int index=0;index<wrong.length;index++) {
            var changed=manifest.deepCopy();
            ContinuityJson.object(changed.get("verified_mod_absence")).set("game_creation_filetime",
                    StrictJson.parse(wrong[index].getBytes(StandardCharsets.UTF_8)));
            String name="invalid-"+index;
            assertThrows(ContractViolationException.class,()->absencePolicy(changed,name),wrong[index]);
        }
        var missing=manifest.deepCopy();
        ContinuityJson.object(missing.get("verified_mod_absence")).remove("game_creation_filetime");
        assertThrows(ContractViolationException.class,()->absencePolicy(missing,"missing"));
        var safe=StrictJson.object();safe.put("n",StrictJson.MAX_SAFE_INTEGER);
        assertEquals(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER),
                ContinuityJson.parseObject(ContinuityJson.canonical(safe),65536).get("n").bigIntegerValue());
        safe.put("n",BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER).add(BigInteger.ONE));
        assertThrows(ContractViolationException.class,()->ContinuityJson.canonical(safe));
    }
    private com.fasterxml.jackson.databind.node.ObjectNode absenceManifest(String profileName)throws Exception {
        Path profile=temporary.resolve(profileName);Files.createDirectories(profile.resolve("logs"));
        Path mods=profile.resolve("dlc_load.json");Files.writeString(mods,"{\"enabled_mods\":[]}");
        Path log=profile.resolve("logs/startup-original.log");Files.writeString(log,"original startup fixture bytes");
        var modRef=ControlBuild.FileRef.measure(mods);var logRef=ControlBuild.FileRef.measure(log);
        var manifest=StrictJson.object();manifest.put("environment_sha256","e".repeat(64));manifest.put("profile_dir",profile.toString());
        manifest.putObject("rules").putArray("profile");var load=manifest.putObject("load_profile");load.putArray("enabled_mods");load.put("dlc_load_sha256",modRef.sha256());
        var evidence=manifest.putObject("verified_mod_absence");evidence.put("schema","xar.verified-xar-mod-absence/v1");
        evidence.put("status","ACTUAL_PROFILE_AND_STARTUP_LOG_VERIFIED");evidence.put("reviewer","/root");
        for(String key:new String[]{"enabled_mods_known","loaded_mods_known","startup_log_reviewed"})evidence.put(key,true);
        evidence.putArray("enabled_mods");evidence.putArray("loaded_mods");evidence.put("environment_sha256","e".repeat(64));
        evidence.put("game_pid",42);evidence.put("game_creation_filetime","134055108000000017");evidence.put("profile_dir",profile.toString());
        evidence.set("profile_enabled_mods",new ExactRef(modRef.path(),modRef.bytes(),modRef.sha256()).toJson());
        evidence.set("startup_log_snapshot",new ExactRef(logRef.path(),logRef.bytes(),logRef.sha256()).toJson());evidence.put("startup_log_original_path",log.toString());
        return manifest;
    }
    private InitialEpisodePolicy absencePolicy(com.fasterxml.jackson.databind.node.ObjectNode manifest,String name)throws Exception {
        Path environment=temporary.resolve(name+"-absence.json");
        Files.write(environment,ContinuityJson.canonical(manifest));
        return writePolicyFixture(temporary.resolve(name+"-policy.json"),ControlBuild.FileRef.measure(environment),
                InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT);
    }
    private InitialEpisodePolicy policy(String lifecycle,String enabled,String pact)throws Exception {
        var kind=switch(lifecycle) {
            case "rogue_one_life" -> InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE;
            case "ordinary_campaign_succession" -> InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION;
            default -> throw new IllegalArgumentException("explicit actual lifecycle required");
        };
        Path environment=temporary.resolve("environment-"+lifecycle+".json");
        var manifest=StrictJson.object();manifest.put("environment_sha256","e".repeat(64));
        var setting=manifest.putObject("rules").putArray("profile").addObject();setting.put("rule","xar_enabled");setting.put("setting",enabled);
        Files.write(environment,ContinuityJson.canonical(manifest));
        var env=ControlBuild.FileRef.measure(environment);
        Path path=temporary.resolve("policy-"+lifecycle+".json");
        return writePolicyFixture(path,env,kind,kind==InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE
                ? InitialEpisodePolicy.FreshPact.ROGUE_REQUIRED:InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT);
    }
    private static InitialEpisodePolicy writePolicyFixture(Path target,ControlBuild.FileRef environment,
            InitialEpisodePolicy.Lifecycle lifecycle,InitialEpisodePolicy.FreshPact fresh)throws java.io.IOException {
        byte[] bytes=InitialEpisodePolicy.encode(environment,lifecycle,fresh);
        Files.write(target,bytes,StandardOpenOption.CREATE_NEW);
        var source=ControlBuild.FileRef.measure(target);
        return InitialEpisodePolicy.readExact(new ExactRef(source.path(),source.bytes(),source.sha256()),environment);
    }
    private static NativeObservationPort.ObservedFrame frame(String actor) {
        byte[] state=("{\"date_raw\":53144328,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":"+actor+",\"alive\":true}}").getBytes(StandardCharsets.UTF_8);
        String envelope="{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"actual-first-frame\",\"revision\":9,\"state\":"+new String(state,StandardCharsets.UTF_8)+"}";
        byte[] raw=envelope.getBytes(StandardCharsets.UTF_8),packet=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134055108000000017")));
        var session=new NativeObservationPort.TransportSession("fixture-machine",game,BigInteger.ONE,"first-session");
        return new NativeObservationPort.ObservedFrame(session,"actual-first-frame",BigInteger.valueOf(9),new RawJson(state),packet,Instant.now());
    }
}
