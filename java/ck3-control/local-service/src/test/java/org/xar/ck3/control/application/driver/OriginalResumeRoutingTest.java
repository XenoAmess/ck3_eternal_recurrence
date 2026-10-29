package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.g2.m7.GoalCodec;

/** Sole real canonical DATA producer -> hot/cold/migration routing. No private load or Root admission is manufactured. */
final class OriginalResumeRoutingTest {
    private static final String PIPE="original-resume-routing",SHA="a".repeat(64);
    @Test void pendingMigrationAndManagedRestoreRemainExplicitAndKeepEveryOriginalUnknownRow() {
        Obj base=base();assertTrue(DriverBootstrap.originalResumeNeeds(loaded(base)).isEmpty());
        var missingLife=new java.util.LinkedHashMap<>(base.members());missingLife.remove("succession_lifecycle");
        assertNeeds(loaded(new Obj(missingLife)),DriverBootstrap.OriginalResumeNeed.LIFECYCLE_MIGRATION);
        assertNeeds(loaded(base.with("format_version",number(1)).with("episode_character_id",Nil.INSTANCE).with("episode_run_id",Nil.INSTANCE)),
                DriverBootstrap.OriginalResumeNeed.MODERN_SESSION_BINDING);
        var missingPlural=new java.util.LinkedHashMap<>(base.with("last_checkpoint",checkpoint()).members());missingPlural.remove("rollback_war_failures");
        assertNeeds(loaded(new Obj(missingPlural)),DriverBootstrap.OriginalResumeNeed.ROLLBACK_MIGRATION);
        var receipt=assertInstanceOf(LegacyResumeNormalizer.Loaded.class,LegacyResumeNormalizer.normalize(base,PIPE,LegacyResumeNormalizer.HistoryMaterialization.OMIT));
        assertNeeds(receipt,DriverBootstrap.OriginalResumeNeed.FULL_HISTORY_MATERIALIZATION);
        // Actual Python managed-restoration semantics must not revive abandoned history as same-PID hot.
        // Both changed-process directions stay pending, even though the general four-refusal guards can succeed.
        for(String replacement:List.of("43","null")) {
            Obj transaction=json("{\"status\":\"awaiting_checkpoint_rebind\",\"request_id\":\"restore-actual\",\"source_bridge_pid\":42,"
                    +"\"replacement_bridge_pid\":"+replacement+",\"checkpoint_sha256\":\""+SHA+"\",\"checkpoint_size\":17,"
                    +"\"checkpoint_date_raw\":24000,\"history_index\":1,\"episode_character_id\":7,\"episode_run_id\":\"e\"}");
            var original=loaded(base.with("bridge_pid",number(replacement.equals("43")?43:42)).with("last_checkpoint",checkpoint())
                    .with("command_history",new Arr(List.of(json("{\"index\":1,\"command\":\"save-checkpoint\",\"ok\":true,\"result\":{\"checkpoint\":"
                            +new String(DriverJson.encode(checkpoint()),StandardCharsets.UTF_8)+"}}"),
                            json("{\"index\":2,\"command\":\"unknown-old-step\",\"ok\":false,\"error\":\"UNKNOWN\",\"opaque\":[null,-0.0]}"))))
                    .with("managed_restore_transaction",transaction));
            byte[] before=original.encode();assertNeeds(original,DriverBootstrap.OriginalResumeNeed.MANAGED_RESTORE_RESOLUTION);
            assertArrayEquals(before,original.encode());assertEquals(2,original.commandHistory().size());
            assertEquals(new Text("UNKNOWN"),original.commandHistory().getLast().get("error"));
            assertFalse(original.normalizedPayload().get("managed_restore_transaction")==Nil.INSTANCE);
        }
    }
    private static void assertNeeds(LegacyResumeNormalizer.Loaded actual,DriverBootstrap.OriginalResumeNeed need) {
        assertTrue(DriverBootstrap.originalResumeNeeds(actual).contains(need));
        assertThrows(UnsupportedOperationException.class,()->DriverBootstrap.originalResumeNeeds(actual).add(need));
    }
    private static LegacyResumeNormalizer.Loaded loaded(Obj value){return assertInstanceOf(LegacyResumeNormalizer.Loaded.class,LegacyResumeNormalizer.normalize(value,PIPE));}
    private static Obj base(){return json("{\"format_version\":2,\"pipe_name\":\""+PIPE+"\",\"bridge_pid\":42,\"episode_character_id\":7,\"episode_run_id\":\"e\","
            +"\"command_history\":[],\"last_checkpoint\":null,\"rollback_war_failures\":[]}").with("succession_lifecycle",
            DriverJson.object(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue()),65536));}
    private static Obj checkpoint(){return json("{\"sha256\":\""+SHA+"\",\"size\":17,\"date_raw\":24000,\"history_index\":1}");}
    private static IntegerValue number(long value){return new IntegerValue(java.math.BigInteger.valueOf(value));}
    private static Obj json(String wire){return DriverJson.object(wire.getBytes(StandardCharsets.UTF_8),65536);}

    @Test void signedActorsSurviveActualDriverSerdeAndGoalConsumerWithoutBinding() {
        for(long actor:new long[]{Integer.MIN_VALUE,Integer.MIN_VALUE+2,0,Integer.MAX_VALUE}) {
            var goal=OrdinaryCampaignGoal.newGoal("retained-campaign",actor);
            Obj driver=base().with("episode_character_id",number(actor))
                    .with("campaign_goal",DriverJson.object(GoalCodec.encodeGoal(goal),65536));
            byte[] before=DriverJson.encode(driver);
            var canonical=loaded(DriverJson.object(before,65536));
            assertEquals(java.math.BigInteger.valueOf(actor),canonical.episode().orElseThrow().characterId());
            assertTrue(DriverBootstrap.originalResumeNeeds(canonical).isEmpty());
            assertThrows(UnsupportedOperationException.class,()->DriverBootstrap.originalResumeNeeds(canonical)
                    .add(DriverBootstrap.OriginalResumeNeed.MODERN_SESSION_BINDING));
            var retainedGoal=GoalCodec.decodeGoal(DriverJson.encode(canonical.normalizedPayload().get("campaign_goal")));
            assertEquals(goal,retainedGoal);
            assertEquals(OrdinaryCampaignGoal.plan(goal),GoalCodec.decodePlan(
                    GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(retainedGoal))));
            assertArrayEquals(before,DriverJson.encode(driver),"routing must not mutate original Driver");
        }
    }
    @Test void wideAndSentinelEpisodesStayExactDataAndKeepBindingAndPidRequirements() {
        for(java.math.BigInteger actor:List.of(java.math.BigInteger.valueOf(2147483648L),
                java.math.BigInteger.valueOf(4294967294L),java.math.BigInteger.ONE.shiftLeft(80),
                java.math.BigInteger.valueOf(-1),java.math.BigInteger.valueOf(Integer.MIN_VALUE).subtract(java.math.BigInteger.ONE))) {
            Obj driver=base().with("episode_character_id",new IntegerValue(actor));
            var canonical=loaded(DriverJson.object(DriverJson.encode(driver),65536));
            assertEquals(actor,canonical.episode().orElseThrow().characterId());
            assertNeeds(canonical,DriverBootstrap.OriginalResumeNeed.MODERN_SESSION_BINDING);
        }
        assertNeeds(loaded(base().with("format_version",number(1))),DriverBootstrap.OriginalResumeNeed.MODERN_SESSION_BINDING);
        assertNeeds(loaded(base().with("bridge_pid",new IntegerValue(new java.math.BigInteger("4294967296")))),
                DriverBootstrap.OriginalResumeNeed.MODERN_SESSION_BINDING);
        for(String token:List.of("true","1.0","\"7\"","null")) {
            Obj driver=base().with("episode_character_id",
                    org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertInstanceOf(LegacyResumeNormalizer.Rejected.class,LegacyResumeNormalizer.normalize(driver,PIPE));
        }
    }
}
