package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.FixedDynastyHeirProjection12004.*;
import static org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class FixedDynastyHeirProjection12004Test {
    private static final FixedAnchor ANCHOR = ROBERT_20261019_T0;
    private static final Core CORE = new Core(53144328,true,3,0,true,true,31254,true);
    private static final QueryBinding BINDING = binding("query-1");
    @Test void positiveWitnessKeepsFixedD0AndCannotClaimCompleteBackupsOrPointH() {
        var result = project(ANCHOR,captured(observation(true,true,true,true,174),false),BINDING,CORE);
        assertEquals(Status.POSITIVE_WITNESS,result.status()); assertEquals(new Interval(70,100),result.hInterval());
        assertEquals(174,result.fixedDynastyIdRaw()); assertEquals(-2147483647,result.candidateCharacterId());
        assertFalse(result.completeBackupDomain()); assertTrue(StrictJson.parse(encode(result)).get("b").isNull());
        var outside = project(ANCHOR,captured(observation(true,true,true,true,175),false),BINDING,CORE);
        assertEquals(Status.UNKNOWN,outside.status()); assertFalse(outside.candidateSameFixedDynasty());
        assertNull(outside.k()); assertEquals(new Interval(0,100),outside.hInterval());
    }
    @Test void realOriginalPythonMapperMatchesAllReachableTypedOutcomes() throws Exception {
        List<Case> cases = new ArrayList<>();
        cases.add(new Case(ANCHOR,captured(observation(true,true,true,true,174),false),BINDING,CORE));
        cases.add(new Case(ANCHOR,captured(observation(true,true,true,true,175),false),BINDING,CORE));
        cases.add(new Case(ANCHOR,captured(observation(true,true,true,true,174),true),BINDING,CORE));
        cases.add(new Case(ANCHOR,captured(observation(false,true,true,true,174),false),BINDING,CORE));
        cases.add(new Case(ANCHOR,captured(observation(true,false,true,true,174),false),BINDING,CORE));
        cases.add(new Case(ANCHOR,captured(observation(true,true,false,true,174),false),BINDING,CORE));
        cases.add(new Case(ANCHOR,captured(observation(true,true,true,false,174),false),BINDING,CORE));
        cases.add(new Case(ANCHOR,null,BINDING,CORE)); cases.add(new Case(ANCHOR,captured(null,false),BINDING,CORE));
        cases.add(new Case(ANCHOR,captured(observation(true,true,true,true,174),false),null,CORE));
        cases.add(new Case(ANCHOR,captured(observation(true,true,true,true,174),false),binding("other-query"),CORE));
        cases.add(new Case(ANCHOR,captured(observation(true,true,true,true,174),false),BINDING,new Core(53144329,true,3,0,true,true,31254,true)));
        cases.add(new Case(ANCHOR,new Captured(BINDING,observation(true,true,true,true,174),"wrong-source",GETTER_CLOSURE_SHA256),BINDING,CORE));
        FixedAnchor changed = new FixedAnchor(ANCHOR.goalCampaignId(),31254,ANCHOR.baselineEpisodeRunId(),ANCHOR.t0DateRaw(),175,
                ANCHOR.baselineSaveSha256(),ANCHOR.baselineSummarySha256());
        cases.add(new Case(changed,captured(observation(true,true,true,true,174),false),BINDING,CORE));
        ArrayNode input = StrictJson.object().putArray("cases"); for (Case c : cases) input.add(wire(c));
        JsonNode expected = NativePlayerHeirOptional12004Test.originalProjection(input);
        assertEquals(cases.size(),expected.size());
        for (int index=0;index<cases.size();index++) {
            Case c=cases.get(index); assertArrayEquals(StrictJson.canonical(expected.get(index),MAX_BYTES),
                    encode(project(c.anchor(),c.captured(),c.binding(),c.core())),"original projection case "+index);
        }
    }
    private record Case(FixedAnchor anchor,Captured captured,QueryBinding binding,Core core) { }
    private static QueryBinding binding(String query) {
        return new QueryBinding("synthetic-machine","134056180000000001",BigInteger.valueOf(1234),BigInteger.valueOf(2),
                EXE_SHA256,"a".repeat(64),"b".repeat(64),query,"native-31",BigInteger.valueOf(900),BigInteger.valueOf(31),
                BigInteger.valueOf(7),BigInteger.valueOf(53144328),31254,"episode-1",ANCHOR.goalCampaignId(),31254,
                ANCHOR.baselineSaveSha256(),ANCHOR.baselineSummarySha256());
    }
    private static Observation observation(boolean available,boolean present,boolean alive,boolean lineage,int dynasty) {
        return new Observation(available,null,false,true,CORE,CORE,true,present,31254,-2147483647,alive,true,lineage,new Lineage(-2147483646,dynasty),null);
    }
    private static Captured captured(Observation o,boolean fixture) {
        if(o!=null&&fixture)o=new Observation(o.available(),o.unavailableReason(),true,o.originalGetterSourceBound(),o.before(),o.after(),o.getterObserved(),
                o.candidatePresent(),o.actorCharacterId(),o.candidateCharacterId(),o.candidateAlive(),o.identityAndFrameStable(),o.lineageAvailable(),o.candidateLineage(),o.lineageUnavailableReason());
        return new Captured(BINDING,o,SOURCE_KIND,GETTER_CLOSURE_SHA256);
    }
    private static ObjectNode wire(Case c) {
        ObjectNode row=StrictJson.object(),a=row.putObject("anchor");FixedAnchor v=c.anchor();
        a.put("goal_campaign_id",v.goalCampaignId()).put("origin_character_id",v.originCharacterId()).put("baseline_episode_run_id",v.baselineEpisodeRunId())
                .put("t0_date_raw",v.t0DateRaw()).put("founding_dynasty_id_raw",v.foundingDynastyIdRaw()).put("baseline_save_sha256",v.baselineSaveSha256()).put("baseline_summary_sha256",v.baselineSummarySha256());
        if(c.binding()==null)row.putNull("binding");else row.set("binding",wire(c.binding()));
        if(c.captured()==null)row.putNull("captured");else{
            Captured captured=c.captured();ObjectNode cap=row.putObject("captured");cap.set("binding",wire(captured.binding()));
            cap.put("source_kind",captured.sourceKind()).put("getter_source_closure_sha256",captured.getterSourceClosureSha256());
            if(captured.observation()==null)cap.putNull("observation");else cap.set("observation",StrictJson.parse(encodeComponent(new Component(BigInteger.valueOf(31),true,captured.observation())),MAX_BYTES).get("observation"));
        }
        if(c.core()==null)row.putNull("core");else{
            Core core=c.core();row.putObject("core").put("date_raw",core.dateRaw()).put("paused",core.paused()).put("speed",core.speed()).put("local_player_id",core.localPlayerId())
                    .put("map_ready",core.mapReady()).put("has_played_character",core.hasPlayedCharacter()).put("played_character_id",core.playedCharacterId()).put("played_character_alive",core.playedCharacterAlive());
        }return row;
    }
    private static ObjectNode wire(QueryBinding b) {
        return StrictJson.object().put("machine_id",b.machineId()).put("game_birth",b.gameBirth()).put("bridge_pid",b.bridgePid()).put("connection_generation",b.connectionGeneration())
                .put("executable_sha256",b.executableSha256()).put("native_provider_sha256",b.nativeProviderSha256()).put("owner_source_epoch",b.ownerSourceEpoch())
                .put("query_id",b.queryId()).put("snapshot_id",b.snapshotId()).put("revision",b.revision()).put("native_revision",b.nativeRevision()).put("capture_epoch",b.captureEpoch())
                .put("date_raw",b.dateRaw()).put("actor_character_id",b.actorCharacterId()).put("episode_run_id",b.episodeRunId()).put("goal_campaign_id",b.goalCampaignId())
                .put("origin_character_id",b.originCharacterId()).put("baseline_save_sha256",b.baselineSaveSha256()).put("baseline_summary_sha256",b.baselineSummarySha256());
    }
}
