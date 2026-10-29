package org.xar.ck3.control.g2.m7;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;

/** Synthetic producer->strict parser->shared continuity->wire tests; no Native/grant/process fixture. */
final class KernelCheckpointContinuityTest {
    private static final String SHA=M7NativeProjection.EXE_SHA256, EPOCH="d".repeat(64), EPISODE="native-31254-synthetic";
    private static final String BIRTH="133123456789012341";
    private static final long ACTOR=31254;
    private static final ExactRef EXE=new ExactRef("D:/synthetic/ck3.exe",123,SHA);

    @Test void exactOneTickAndUint64MaximumSurviveProducerWireAndComparison() {
        var before=observation(BIRTH,ACTOR);
        var after=observation("133123456789012342",ACTOR);
        var compared=KernelCheckpointContinuity.compare(before,after);
        assertFalse(compared.sameGameIdentity());assertTrue(compared.replacementBirthKnown());
        assertTrue(compared.sameGoal());assertTrue(compared.sameCampaignOrigin());assertTrue(compared.sameRulerEpisode());
        assertFalse(compared.grantsColdAuthority());assertFalse(compared.actionReplayAuthorized());
        var maximum=observation("18446744073709551615",ACTOR);
        assertEquals(maximum,KernelCheckpointContinuity.decodeObservation(KernelCheckpointContinuity.encodeObservation(maximum)));
        var json=KernelCheckpointContinuity.toJson(maximum);
        assertTrue(json.path("game_identity").get("creation_filetime").isTextual());
        assertEquals("18446744073709551615",json.path("game_identity").path("creation_filetime").textValue());
    }

    @Test void kernelIdentityRejectsNumberRoundoffAliasesAndMissingFields() {
        var original=KernelCheckpointContinuity.toJson(observation(BIRTH,ACTOR));
        for(String bad:new String[]{"0133123456789012341","+133123456789012341","1e17","0","18446744073709551616"}) {
            var row=original.deepCopy();((ObjectNode)row.get("game_identity")).put("creation_filetime",bad);
            assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(row)));
        }
        var numeric=original.deepCopy();((ObjectNode)numeric.get("game_identity")).put("creation_filetime",new BigInteger(BIRTH));
        assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(numeric)));
        var bool=original.deepCopy();((ObjectNode)bool.get("game_identity")).put("pid",true);
        assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(bool)));
        var floating=original.deepCopy();((ObjectNode)floating.get("game_identity")).put("pid",100.0);
        assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(floating)));
        var missing=original.deepCopy();((ObjectNode)missing.get("game_identity")).remove("creation_filetime");
        assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(missing)));
    }

    @Test void originalLegacyBirthBoundaryAndIntentComparisonRemainUnchanged() {
        var first=new CheckpointContinuity.GameIdentity(100,"20261023123045.123456+480","D:/synthetic/ck3.exe");
        var second=new CheckpointContinuity.GameIdentity(100,"2026-10-23T04:30:45.1234560Z","d:\\synthetic\\ck3.exe");
        assertTrue(CheckpointContinuity.sameGameIdentity(first,second));
        assertThrows(IllegalArgumentException.class,()->new CheckpointContinuity.GameIdentity(100,"2026-10-23T04:30:45.1234561Z","D:/synthetic/ck3.exe"));
        var goal=OrdinaryCampaignGoal.newGoal("synthetic-campaign",ACTOR);
        var a=new CheckpointContinuity.Observation("synthetic-machine",EPOCH,first,"native:1",2,1,EPISODE,ACTOR,53144328,goal,null,null);
        var b=new CheckpointContinuity.Observation("synthetic-machine",EPOCH,second,"native:1",2,1,EPISODE,ACTOR,53144328,goal,null,null);
        assertTrue(CheckpointContinuity.compare(a,b).sameGameIdentity());
        assertTrue(CheckpointContinuity.compare(a,b).sameGoal());
        assertFalse(CheckpointContinuity.compare(a,b).governmentObservationComparable());
    }

    @Test void machineAndExeDriftNeverBecomeSameGameOrGovernmentQualification() {
        var before=observation(BIRTH,ACTOR);
        var after=new KernelCheckpointContinuity.Observation("unknown",EPOCH,before.game(),EXE,"native:1",2,1,EPISODE,
                ACTOR,53144328,before.goal(),null,null);
        assertFalse(KernelCheckpointContinuity.compare(before,after).sameGameIdentity());
        var changed=new KernelCheckpointContinuity.Observation(before.machineId(),EPOCH,before.game(),
                new ExactRef(EXE.path(),EXE.bytes(),"f".repeat(64)),"native:1",2,1,EPISODE,ACTOR,53144328,before.goal(),null,null);
        assertFalse(KernelCheckpointContinuity.compare(before,changed).sameGameIdentity());
        assertFalse(KernelCheckpointContinuity.compare(before,changed).governmentObservationComparable());
    }

    @Test void optionalEmptyMetadataSurvivesEncodeDecodeAndRemainsStrictWhenPresent() {
        var absent=optionalObservation(BIRTH,ACTOR);
        assertEquals(absent,KernelCheckpointContinuity.decodeObservation(KernelCheckpointContinuity.encodeObservation(absent)));
        var json=KernelCheckpointContinuity.toJson(absent);
        assertTrue(json.get("source_epoch").isNull());
        assertTrue(json.path("game_identity").get("executable_ref").isNull());
        var missing=json.deepCopy();missing.remove("source_epoch");
        ((ObjectNode)missing.get("game_identity")).remove("executable_ref");
        assertEquals(absent,KernelCheckpointContinuity.decodeObservation(raw(missing)));
        assertTrue(KernelCheckpointContinuity.compare(absent,observation(BIRTH,ACTOR)).sameGameIdentity());
        var compared=KernelCheckpointContinuity.compare(absent,optionalObservation("133123456789012342",ACTOR));
        assertFalse(compared.sameGameIdentity());assertTrue(compared.replacementBirthKnown());
        assertTrue(compared.sameGoal());assertFalse(compared.grantsColdAuthority());assertFalse(compared.actionReplayAuthorized());
        for(String token:new String[]{"true","1.0","\"bad-epoch\"","{}"}) {
            var bad=json.deepCopy();bad.set("source_epoch",StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(bad)));
        }
        for(String token:new String[]{"true","1.0","\"bad-exe\""}) {
            var bad=json.deepCopy();((ObjectNode)bad.get("game_identity")).set("executable_ref",StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(bad)));
        }
        var extra=json.deepCopy();
        ((ObjectNode)extra.get("game_identity")).set("executable_ref",EXE.toJson().put("extra",true));
        assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(extra)));
    }

    @Test void sharedOriginalBodyProducerConsumesGoalAndKeepsUnrelatedDecimalMetrics() throws Exception {
        var actual=M7NativeProjection.project(raw(ownerRow(ACTOR)),binding(ACTOR));
        assertEquals(observation(BIRTH,ACTOR),actual);
        assertEquals(OrdinaryCampaignGoal.plan(actual.goal()),OrdinaryCampaignGoal.plan(
                KernelCheckpointContinuity.decodeObservation(KernelCheckpointContinuity.encodeObservation(actual)).goal()));
        assertNull(actual.governmentKey());assertNull(actual.adapterFamily());
    }

    @Test void completeHighGenerationActorIdentityIsNotReducedToItsStorageIndex() throws Exception {
        long high=-2147483647L;
        var projected=M7NativeProjection.project(raw(ownerRow(high)),binding(high));
        assertEquals(high,projected.actorCharacterId());assertEquals(high,projected.goal().currentCharacterId());
        assertNotEquals(1,projected.actorCharacterId());
        assertEquals(projected,KernelCheckpointContinuity.decodeObservation(KernelCheckpointContinuity.encodeObservation(projected)));
        var index=M7NativeProjection.project(raw(ownerRow(1)),binding(1));
        assertFalse(KernelCheckpointContinuity.compare(projected,index).sameRulerEpisode());
    }

    @Test void sharedParserRejectsWrongActorEpisodeFrameBuildAndIntegerTypes() {
        for(String field:new String[]{"actor","episode","snapshot","build","generation","paused","goal"}) {
            var row=ownerRow(ACTOR);var snapshot=snapshot(row);
            switch(field) {
                case "actor"->((ObjectNode)snapshot.get("played_character")).put("character_id",ACTOR+1);
                case "episode"->snapshot.put("episode_run_id","other-episode");
                case "snapshot"->snapshot.put("snapshot_id","native:2");
                case "build"->((ObjectNode)snapshot.path("diagnostics").get("hello")).put("expected_ck3_sha256","f".repeat(64));
                case "generation"->((ObjectNode)snapshot.get("diagnostics")).put("connection_generation",1.0);
                case "paused"->snapshot.put("paused",1);
                case "goal"->((ObjectNode)snapshot.get("campaign_goal")).put("current_character_id",ACTOR+1);
                default->throw new AssertionError(field);
            }
            assertThrows(IllegalArgumentException.class,()->M7NativeProjection.project(raw(row),binding(ACTOR)),field);
        }
    }

    @Test void fullUint64OriginalRevisionFeedsKernelConsumerWithoutNumericNarrowing() throws Exception {
        var row=ownerRow(ACTOR);var original=snapshot(row);BigInteger maximum=StrictJson.UINT64_MAX;
        original.put("snapshot_id","native:"+maximum).put("revision",maximum).put("native_revision",maximum);
        var projected=M7NativeProjection.project(raw(row),binding(ACTOR));
        assertEquals(maximum,projected.revision());assertEquals(maximum,projected.nativeRevision());
        assertEquals(projected,KernelCheckpointContinuity.decodeObservation(KernelCheckpointContinuity.encodeObservation(projected)));
        var consumed=M7KernelPlanConsumer.consume(M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN,projected,"query",java.util.Optional.empty());
        assertEquals(consumed,M7KernelPlanConsumer.decode(M7KernelPlanConsumer.encode(consumed)));
        for(String field:new String[]{"revision","native_revision"}) {
            for(String token:new String[]{"true","1.0","\"1\"","null","-1","18446744073709551616"}) {
                byte[] altered=integerToken(row,field,maximum.toString(),token);
                assertThrows(IllegalArgumentException.class,()->M7NativeProjection.project(altered,binding(ACTOR)),field+" token "+token);
            }
        }
    }

    @Test void fullLifecycleAndNullableGovernmentSemanticsSurvivePersistence() throws Exception {
        var row=ownerRow(ACTOR);((ObjectNode)snapshot(row).get("succession_lifecycle")).remove("source");
        assertThrows(IllegalArgumentException.class,()->M7NativeProjection.project(raw(row),binding(ACTOR)));
        var encoded=KernelCheckpointContinuity.toJson(observation(BIRTH,ACTOR));
        assertTrue(encoded.get("government_key").isNull());encoded.remove("government_key");
        assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(encoded)));
        var goalMismatch=ownerRow(ACTOR);snapshot(goalMismatch).remove("campaign_goal");
        assertThrows(IllegalArgumentException.class,()->M7NativeProjection.project(raw(goalMismatch),binding(ACTOR)));
    }

    @Test void signedActorsSurviveOriginalProjectionKernelAndPlanPersistence() throws Exception {
        for(long actor:new long[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}) {
            var value=M7NativeProjection.project(raw(ownerRow(actor)),binding(actor));
            assertEquals(actor,value.actorCharacterId());assertEquals(actor,value.goal().originCharacterId());
            assertEquals(value,KernelCheckpointContinuity.decodeObservation(KernelCheckpointContinuity.encodeObservation(value)));
            var consumed=M7KernelPlanConsumer.consume(M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN,
                    value,"query",java.util.Optional.empty());
            assertEquals(consumed,M7KernelPlanConsumer.decode(M7KernelPlanConsumer.encode(consumed)));
            assertFalse(consumed.gameActionsSubmitted());assertFalse(consumed.coldAuthorityGranted());
            assertFalse(consumed.replayAuthorized());assertEquals(0,consumed.savedDayCredit());
        }
    }

    @Test void actorBoundariesRejectUnsignedAliasesSentinelAndLiteralWrongTypes() {
        var original=ownerRow(1);
        var encoded=KernelCheckpointContinuity.toJson(observation(BIRTH,1));
        for(String token:new String[]{"-1","-2147483649","2147483648","2147483649","4294967295",
                "true","1.0","\"1\"","null"}) {
            byte[] nativeRow=integerToken(original,"character_id","1",token);
            var nativeError=assertThrows(IllegalArgumentException.class,()->M7NativeProjection.project(nativeRow,binding(1)),token);
            byte[] kernelRow=integerToken(encoded,"actor_character_id","1",token);
            var kernelError=assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(kernelRow),token);
            String reason=token.equals("-1")?"absent-character sentinel"
                    :token.matches("-?[0-9]+")?"integer outside contract range":"exact JSON integer required";
            assertTrue(nativeError.getMessage().contains(reason),nativeError.getMessage());
            assertTrue(kernelError.getMessage().contains(reason),kernelError.getMessage());
        }
        for(long actor:new long[]{-1,(long)Integer.MIN_VALUE-1,(long)Integer.MAX_VALUE+1,4294967295L})
            assertThrows(IllegalArgumentException.class,()->binding(actor));
        ((ObjectNode)snapshot(original).get("played_character")).remove("character_id");
        assertThrows(IllegalArgumentException.class,()->M7NativeProjection.project(raw(original),binding(1)));
        encoded.remove("actor_character_id");
        assertThrows(IllegalArgumentException.class,()->KernelCheckpointContinuity.decodeObservation(raw(encoded)));
    }

    private static byte[] integerToken(ObjectNode row,String field,String current,String token) {
        String text=new String(raw(row),StandardCharsets.UTF_8),needle="\""+field+"\":"+current;
        assertTrue(text.indexOf(needle)>=0&&text.indexOf(needle)==text.lastIndexOf(needle),"one actual integer field required");
        return text.replace(needle,"\""+field+"\":"+token).getBytes(StandardCharsets.UTF_8);
    }

    private static KernelCheckpointContinuity.Observation observation(String birth,long actor) {
        return new KernelCheckpointContinuity.Observation("synthetic-machine",EPOCH,new GameIdentity(100,birth),EXE,
                "native:1",2,1,EPISODE,actor,53144328,OrdinaryCampaignGoal.newGoal("synthetic-campaign",actor),null,null);
    }
    private static KernelCheckpointContinuity.Observation optionalObservation(String birth,long actor) {
        return new KernelCheckpointContinuity.Observation("synthetic-machine",java.util.Optional.<String>empty(),new GameIdentity(100,birth),java.util.Optional.<ExactRef>empty(),
                "native:1",2,1,EPISODE,actor,53144328,OrdinaryCampaignGoal.newGoal("synthetic-campaign",actor),null,null);
    }
    private static M7NativeProjection.Binding binding(long actor) {
        return new M7NativeProjection.Binding("synthetic-machine",EPOCH,new GameIdentity(100,BIRTH),EXE,EPISODE,actor,
                "synthetic-pipe","1",ProjectionJson.object(StrictJson.canonical(lifecycle()),M7NativeProjection.MAX_BYTES));
    }
    private static ObjectNode lifecycle() {
        var life=StrictJson.object();life.put("schema","xar.ck3.succession-lifecycle-binding/v1");
        life.put("lifecycle","ordinary_campaign_succession");life.put("xar_enabled","xar_off");
        life.put("pact_contract","absent_by_fresh_campaign_xar_off_contract");life.put("source","synthetic-frozen-environment");
        life.put("environment_sha256","a".repeat(64));return life;
    }
    private static ObjectNode ownerRow(long actor) {
        var row=StrictJson.object();var result=row.putObject("result");result.put("is_error",false);
        var s=result.putObject("structured_content");s.put("map_ready",true);s.put("paused",true);s.put("snapshot_id","native:1");
        s.put("revision",2);s.put("native_revision",1);s.put("date_raw",53144328);s.put("episode_run_id",EPISODE);
        s.putObject("played_character").put("character_id",actor);s.put("unrelated_decimal_metric",1.25);
        s.set("campaign_goal",GoalCodec.goalJson(OrdinaryCampaignGoal.newGoal("synthetic-campaign",actor)));
        s.set("succession_lifecycle",lifecycle());var d=s.putObject("diagnostics");d.put("connected",true);
        d.put("pipe_name","synthetic-pipe");d.put("bridge_pid",100);d.put("connection_generation",1);
        var h=d.putObject("hello");h.put("pid",100);h.put("connection_generation",1);h.put("ck3_build_match",true);
        h.put("expected_ck3_version",M7NativeProjection.GAME_VERSION);h.put("expected_ck3_sha256",SHA);return row;
    }
    private static ObjectNode snapshot(ObjectNode row) { return (ObjectNode)row.path("result").get("structured_content"); }
    private static byte[] raw(ObjectNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
}
