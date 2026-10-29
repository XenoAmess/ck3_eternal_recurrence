package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.LifecyclePublicResultCodec;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunStrategySource;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.LifecyclePublicCodec;

/** Actual production reducers and seed reader -> public DATA consumer. No writer/domain/Host authority is exercised. */
final class PublicLifecycleReducerConsumerTest {
    @TempDir Path temporary;
    @Test void actualScoredDeathAndImmutableSeedNextReducerFeedTheSamePublicResultContract() throws Exception {
        var fixture=new PublicLifecycleReducerFixture(temporary);var death=fixture.reduction();
        var deathPayload=new LifecyclePublicCodec.Applied(LifecycleTransitionProof.Kind.DEATH,new RawJson(death.result()),"test-machine",PublicLifecycleReducerFixture.AT);
        var publicDeath=LifecyclePublicCodec.encode(deathPayload);
        var originalDeath=LifecycleJson.parse(LifecyclePublicResultCodec.decode(LifecycleTransitionProof.Kind.DEATH,publicDeath).bytes(),LifecycleProofCodec.MAX_RESULT_BYTES);
        assertEquals("complete",originalDeath.get("settlement_status").textValue());assertTrue(originalDeath.get("score").isNumber());
        assertFalse(originalDeath.get("continue_as_heir_after_death").booleanValue());

        var seed=fixture.files.createNew(temporary.resolve(SeedArtifact.NAME),"actual temporary immutable seed".getBytes(StandardCharsets.UTF_8));
        var metadata=LifecycleJson.row().put("format_version",1).put("name",SeedArtifact.NAME).put("path",seed.reference().path())
                .put("size",seed.reference().bytes()).put("sha256",seed.reference().sha256()).put("date_raw",120).put("character_id",73)
                .put("source_run_id","episode-1").put("source_checkpoint_name","xar_checkpoint.ck3").put("immutable",true);
        var metadataFile=fixture.files.createNew(temporary.resolve("episode-seed.json"),LifecycleJson.bytes(metadata));
        var actualSeed=SeedStore.decode(fixture.files,seed,metadataFile);actualSeed.requireCurrent(fixture.files);
        var strategy=CrossRunStrategySource.decode(OpportunityJson.object(death.auxiliary().get("one_life_strategy"),"actual scored strategy")).state();
        var persisted=OpportunityJson.object(OpportunityJson.parse(CrossRunPlanning.encodeState(strategy)),"canonical persisted strategy DATA");
        // This is a pure reducer source seam. Dynamic's actual writer/canonical-source validator is deliberately not forged here.
        var softwareSource=fixture.files.createNew(temporary.resolve("software-strategy-source.json"),"software source only; not a writer or canonical domain grant".getBytes(StandardCharsets.UTF_8)).reference();
        var auxiliary=death.auxiliary().with("one_life_strategy",persisted).with(DriverPersistentPlanningState.STRATEGY_SOURCE,LifecycleJson.immutable(softwareSource.toJson()));
        var old=fixture.snapshot.facts();var beforeNext=new DriverSnapshotFacts.Known(death.driver(),new DriverSnapshotFacts.Stamp(1,0,old.stamp().game(),"episode-1",LifecycleJson.sha(death.driver().encode())),
                old.originalHistoryBasis(),List.of(),auxiliary,Optional.empty(),Optional.empty());
        var selectedPlan=LifecycleReducer.requireNextRunPlan(beforeNext);
        var next=LifecycleReducer.nextEpisode(beforeNext,actualSeed,124,BigInteger.valueOf(73),BigInteger.valueOf(120),"episode-2",PublicLifecycleReducerFixture.AT);
        var originalNext=LifecycleJson.parse(next.result(),LifecycleProofCodec.MAX_RESULT_BYTES);assertTrue(originalNext.get("cross_run_plan_used").isObject());
        assertEquals(CrossRunPlanning.planJson(selectedPlan),LifecycleJson.immutable(originalNext.get("cross_run_plan_used")));
        var publicNext=LifecyclePublicCodec.encode(new LifecyclePublicCodec.Applied(LifecycleTransitionProof.Kind.NEXT_EPISODE,new RawJson(next.result()),"test-machine",PublicLifecycleReducerFixture.AT));
        var decoded=LifecycleJson.parse(LifecyclePublicResultCodec.decode(LifecycleTransitionProof.Kind.NEXT_EPISODE,publicNext).bytes(),LifecycleProofCodec.MAX_RESULT_BYTES);
        assertEquals(selectedPlan,CrossRunPlanning.parsePlan(OpportunityJson.object(LifecycleJson.immutable(decoded.get("cross_run_plan_used")),"actual reducer used plan")));
        assertEquals("episode-2",decoded.get("episode_run_id").textValue());assertTrue(decoded.get("date_raw").isIntegralNumber());assertTrue(decoded.get("resumed_pid").isIntegralNumber());
        assertEquals(originalNext.get("cross_run_plan_used"),decoded.get("cross_run_plan_used"));
    }
}
