package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunStrategySource;
import org.xar.ck3.control.application.planning.campaign.CrossRunFirstCheckpointReader;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

public final class LifecycleReducerTest {
    @TempDir Path temporary;
    @Test void actualNativeUnderflowSignedZeroSurvivesDeathWholeCrossRunSerdeAndOpaqueUnknownHistory()throws Exception {
        var nativeSettlement=DeathSettlementTest.ready(false,10,10);
        nativeSettlement.set("final_score",LifecycleJson.row().put("raw",BigInteger.valueOf(-1)).put("scale",BigInteger.ONE.shiftLeft(2000)));
        var f=new LifecycleBusinessFixture(temporary,nativeSettlement);var reduced=f.reduction();
        var result=LifecycleJson.parse(reduced.result(),LifecycleProofCodec.MAX_RESULT_BYTES);
        long negativeZero=Double.doubleToRawLongBits(-0.0);
        assertEquals(negativeZero,Double.doubleToRawLongBits(result.get("score").doubleValue()));
        assertEquals(negativeZero,Double.doubleToRawLongBits(result.get("one_life_settlement").get("final_score").doubleValue()));
        var state=CrossRunStrategySource.decode(OpportunityJson.object(reduced.auxiliary().get("one_life_strategy"),"actual recorded strategy")).state();
        assertEquals(new OpportunityJson.DecimalValue("-0.0"),state.episodes().getLast().score());
        byte[] encoded=CrossRunPlanning.encodeState(state);
        assertTrue(new String(encoded,StandardCharsets.UTF_8).contains("\"score\":-0.0"));
        assertEquals(state,CrossRunPlanning.decodeState(encoded));
        var original=f.snapshot.facts().driver().commandHistory().getFirst().originalRow().json();
        assertTrue(new String(original,StandardCharsets.UTF_8).contains("\"opaque_decimal\":-0.0"));
        assertArrayEquals(original,reduced.driver().commandHistory().getFirst().originalRow().json());
        var replayed=DriverStateSnapshot.decodeComplete(reduced.driver().encode());
        assertArrayEquals(original,replayed.commandHistory().getFirst().originalRow().json());
        LifecycleReducer.requireScoredTerminal(replayed);
    }
    @Test void actualNormalizedSettlementLargerThanOld64KiBBoundaryReachesDeathAndRetainedFullDriver()throws Exception {
        var nativeSettlement=DeathSettlementTest.ready(false,10,10);
        var actualCounter=new BigInteger("9".repeat(70000));nativeSettlement.put("contract_progress",actualCounter);
        var f=new LifecycleBusinessFixture(temporary,nativeSettlement);
        assertTrue(f.settlement().normalized().length>65536);
        var reduced=f.reduction();var result=LifecycleJson.parse(reduced.result(),LifecycleProofCodec.MAX_RESULT_BYTES);
        assertEquals(actualCounter,result.get("one_life_settlement").get("contract_progress").bigIntegerValue());
        assertEquals(f.settlement().typed(),DeathSettlement.fromNormalized(result.get("one_life_settlement")).orElseThrow().typed());
        var replayed=DriverStateSnapshot.decodeComplete(reduced.driver().encode());
        LifecycleReducer.requireScoredTerminal(replayed);
        assertArrayEquals(reduced.driver().encode(),replayed.encode());
        assertArrayEquals(f.snapshot.facts().driver().commandHistory().getFirst().originalRow().json(),
                replayed.commandHistory().getFirst().originalRow().json());
    }
    @Test void actualNativeRatioRoundedToOneRetainsNormalizedFloatingLaneThroughDeathAndCrossRunSerialization()throws Exception {
        var nativeSettlement=DeathSettlementTest.ready(false,10,10);
        nativeSettlement.set("final_score",LifecycleJson.row().put("raw",new BigInteger("9007199254740993"))
                .put("scale",new BigInteger("9007199254740992")));
        var f=new LifecycleBusinessFixture(temporary,nativeSettlement);
        assertEquals(1L,f.snapshot.facts().observation().orElseThrow().observationVersion());
        assertEquals(f.snapshot.actual().snapshotId(),f.snapshot.facts().observation().orElseThrow().snapshotId());
        assertEquals(f.snapshot.actual().session(),f.snapshot.facts().observation().orElseThrow().transport());
        assertEquals(org.xar.ck3.control.application.driver.DriverJson.sha256(f.snapshot.actual().state().bytes()),
                f.snapshot.facts().observation().orElseThrow().nativeStateSha256());
        assertTrue(OpportunityJson.object(f.snapshot.semantic().get("one_life_settlement"),"actual raw v1 settlement").get("final_score") instanceof OpportunityJson.Obj);
        var reduced=f.reduction();var result=LifecycleJson.parse(reduced.result(),LifecycleProofCodec.MAX_RESULT_BYTES);
        assertTrue(result.get("score").isFloatingPointNumber());assertEquals(1.0,result.get("score").doubleValue());
        assertTrue(result.get("one_life_settlement").get("final_score").isFloatingPointNumber());
        assertTrue(result.get("cross_run_strategy").get("episodes").get(0).get("score").isFloatingPointNumber());
        var normalized=DeathSettlement.fromNormalized(result.get("one_life_settlement")).orElseThrow();
        assertTrue(normalized.scoreJson().isFloatingPointNumber());
        assertEquals(result.get("score").doubleValue(),normalized.scoreJson().doubleValue());
        assertEquals(normalized.typed(),DeathSettlement.fromNormalized(normalized.normalizedJson()).orElseThrow().typed());
    }
    @Test void actualDeathReducerRetainsLargeUnknownHistoryAndCanonicalCrossLifeStrategyThenScoresOnce() throws Exception {
        var f=new LifecycleBusinessFixture(temporary);var reduced=f.reduction();
        assertArrayEquals(f.snapshot.facts().driver().commandHistory().getFirst().originalRow().json(),reduced.driver().commandHistory().getFirst().originalRow().json());
        assertEquals(2,reduced.driver().commandHistory().size());assertTrue(reduced.driver().encode().length>128*1024);
        LifecycleReducer.requireScoredTerminal(reduced.driver());
        var result=LifecycleJson.parse(reduced.result(),LifecycleProofCodec.MAX_RESULT_BYTES);
        assertEquals("complete",result.get("settlement_status").textValue());assertFalse(result.get("continue_as_heir_after_death").booleanValue());
        assertEquals(1,result.get("cross_run_strategy").get("episodes").size());
        assertEquals(150000,LifecycleJson.parse(reduced.driver().commandHistory().getFirst().originalRow().json(),LifecycleProofCodec.MAX_RESULT_BYTES).get("result").get("retained_original").textValue().length());
        assertFalse(result.get("cross_run_strategy").has("retained_original"));
        assertSame(f.snapshot.facts().driver().campaignGoal(),reduced.driver().campaignGoal());
    }
    @Test void actualImmutableSeedReaderAndScoredTerminalProduceNewEpisodeWithCacheInvalidation() throws Exception {
        var f=new LifecycleBusinessFixture(temporary);var death=f.reduction();
        var seed=f.files.createNew(temporary.resolve(SeedArtifact.NAME),"actual temporary immutable seed".getBytes(StandardCharsets.UTF_8));
        var meta=LifecycleJson.row();meta.put("format_version",1);meta.put("name",SeedArtifact.NAME);meta.put("path",seed.reference().path());
        meta.put("size",seed.reference().bytes());meta.put("sha256",seed.reference().sha256());meta.put("date_raw",120);meta.put("character_id",73);
        meta.put("source_run_id","episode-1");meta.put("source_checkpoint_name","xar_checkpoint.ck3");meta.put("immutable",true);
        var metadata=f.files.createNew(temporary.resolve("episode-seed.json"),LifecycleJson.bytes(meta));var actual=SeedStore.decode(f.files,seed,metadata);actual.requireCurrent(f.files);
        var old=f.snapshot.facts();var strategy=CrossRunStrategySource.decode(OpportunityJson.object(death.auxiliary().get("one_life_strategy"),"actual scored strategy")).state();
        var canonical=OpportunityJson.object(OpportunityJson.parse(CrossRunPlanning.encodeState(strategy)),"canonical strategy state");
        // Pure reducer DATA seam only. The real LifecycleComposites caller separately validates dynamic16's current canonical source under its writer.
        var source=f.files.createNew(temporary.resolve("software-strategy-source.json"),"software original source reference; no authority".getBytes(StandardCharsets.UTF_8)).reference();
        var auxiliary=death.auxiliary().with("one_life_strategy",canonical).with(DriverPersistentPlanningState.STRATEGY_SOURCE,
                LifecycleJson.immutable(source.toJson())).with("driver_preclock_expectation_source",LifecycleJson.immutable(source.toJson()));
        var dead=new DriverSnapshotFacts.Known(death.driver(),new DriverSnapshotFacts.Stamp(1,0,old.stamp().game(),"episode-1",LifecycleJson.sha(death.driver().encode())),
                old.originalHistoryBasis(),List.of(),auxiliary,Optional.empty(),Optional.empty());
        var next=LifecycleReducer.nextEpisode(dead,actual,124,BigInteger.valueOf(73),BigInteger.valueOf(120),"episode-2",LifecycleBusinessFixture.AT);
        assertEquals("episode-2",next.driver().session().episodeRunId());assertEquals(124,next.driver().session().bridgePid());assertTrue(next.driver().commandHistory().isEmpty());
        assertEquals(new OpportunityJson.Text("new_episode"),next.auxiliary().get("restore_kind"));assertEquals(new OpportunityJson.Arr(List.of()),next.auxiliary().get("arrange_marriage_choices"));
        assertEquals(OpportunityJson.Nil.INSTANCE,next.auxiliary().get("active_combat_retreat_token"));
        assertFalse(next.auxiliary().members().containsKey("driver_preclock_expectation_source"));
        assertEquals(LifecycleJson.immutable(source.toJson()),dead.auxiliary().get("driver_preclock_expectation_source"));
        var result=LifecycleJson.parse(next.result(),LifecycleProofCodec.MAX_RESULT_BYTES);
        assertTrue(result.get("cross_run_plan_used").isObject());
        assertEquals(CrossRunPlanning.planJson(strategy.nextRunPlan()),LifecycleJson.immutable(result.get("cross_run_plan_used")));
        assertEquals(strategy.nextRunPlan(),CrossRunPlanning.parsePlan(OpportunityJson.object(LifecycleJson.immutable(result.get("cross_run_plan_used")),"actual used plan")));
        assertEquals(CrossRunPlanning.planJson(strategy.nextRunPlan()),LifecycleJson.immutable(LifecycleJson.parse(LifecycleJson.bytes(result),LifecycleProofCodec.MAX_RESULT_BYTES).get("cross_run_plan_used")));
        // The real FIRST reader's pure comparison consumes these actual producer bytes. This is DATA, not a private FIRST permit.
        assertEquals(strategy.nextRunPlan(),CrossRunFirstCheckpointReader.requireNextPlan(death.driver(),next.result(),strategy));
        assertEquals(strategy.nextRunPlan(),CrossRunFirstCheckpointReader.requireNextPlan(death.driver(),LifecycleJson.bytes(result),strategy));
        var booleanPlan=result.deepCopy();booleanPlan.put("cross_run_plan_used",true);
        assertThrows(IllegalArgumentException.class,()->CrossRunFirstCheckpointReader.requireNextPlan(death.driver(),LifecycleJson.bytes(booleanPlan),strategy));
        var missingPlan=result.deepCopy();missingPlan.remove("cross_run_plan_used");
        assertThrows(IllegalArgumentException.class,()->CrossRunFirstCheckpointReader.requireNextPlan(death.driver(),LifecycleJson.bytes(missingPlan),strategy));
        var wrongLife=result.deepCopy();wrongLife.put("source_run_id","another-scored-life");
        assertThrows(IllegalArgumentException.class,()->CrossRunFirstCheckpointReader.requireNextPlan(death.driver(),LifecycleJson.bytes(wrongLife),strategy));
        assertThrows(IllegalArgumentException.class,()->CrossRunFirstCheckpointReader.requireNextPlan(death.driver(),next.result(),CrossRunPlanning.empty()));
        var missingSource=new DriverSnapshotFacts.Known(dead.driver(),dead.stamp(),dead.originalHistoryBasis(),List.of(),death.auxiliary(),Optional.empty(),Optional.empty());
        assertThrows(IllegalArgumentException.class,()->LifecycleReducer.requireNextRunPlan(missingSource));
        var wrongPlan=canonical.with("next_run_plan",CrossRunPlanning.planJson(CrossRunPlanning.empty().nextRunPlan()).with("policy",new OpportunityJson.Text("wrong-policy")));
        var changed=new DriverSnapshotFacts.Known(dead.driver(),dead.stamp(),dead.originalHistoryBasis(),List.of(),auxiliary.with("one_life_strategy",wrongPlan),Optional.empty(),Optional.empty());
        assertThrows(IllegalArgumentException.class,()->LifecycleReducer.requireNextRunPlan(changed));
        assertThrows(IllegalArgumentException.class,()->LifecycleReducer.nextEpisode(dead,actual,123,BigInteger.valueOf(73),BigInteger.valueOf(120),"episode-2",LifecycleBusinessFixture.AT));
        assertThrows(IllegalArgumentException.class,()->LifecycleReducer.nextEpisode(old,actual,124,BigInteger.valueOf(73),BigInteger.valueOf(120),"episode-2",LifecycleBusinessFixture.AT));
    }
}
