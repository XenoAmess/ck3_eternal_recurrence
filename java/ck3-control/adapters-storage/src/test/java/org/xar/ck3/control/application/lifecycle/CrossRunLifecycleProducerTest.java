package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunStrategySource;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual lifecycle producer and shared pure verifier; no second publication or life is produced. */
final class CrossRunLifecycleProducerTest {
    @TempDir Path temporary;
    @Test void soleDeathReducerFeedsNextPlanAndRetainsEveryEarlierLifeExactly()throws Exception {
        var fixture=new LifecycleBusinessFixture(temporary);var previous=CrossRunPlanning.recordEpisode(CrossRunPlanning.empty(),"earlier-life",List.of(),
                object("{\"terminal\":true,\"terminal_reason\":\"player_death\",\"technical_settlement_handoff\":false,\"score\":19}"),LifecycleBusinessFixture.AT.minusSeconds(60));
        var old=fixture.snapshot.facts();var strategy=OpportunityJson.object(OpportunityJson.parse(CrossRunPlanning.encodeState(previous)),"canonical earlier strategy");
        var facts=new DriverSnapshotFacts.Known(old.driver(),old.stamp(),old.originalHistoryBasis(),old.actionRows(),
                old.auxiliary().with("one_life_strategy",strategy),old.loop(),old.observation());
        var observed=new LifecycleObservationPort.Snapshot(fixture.snapshot.actual(),fixture.snapshot.source(),fixture.snapshot.semantic(),facts,fixture.snapshot.originalEvidence());
        var ready=fixture.settlement();
        var actual=LifecycleReducer.death(observed,ready,new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD,false,Optional.empty(),List.of()),LifecycleBusinessFixture.AT);
        var result=OpportunityJson.object(OpportunityJson.parse(actual.result()),"actual sole death reducer output");
        CrossRunPlanning.State state=CrossRunStrategySource.terminal(previous,"episode-1",result,LifecycleBusinessFixture.AT);
        var originalRows=fixture.snapshot.facts().driver().commandHistory().stream().map(row->
                OpportunityJson.object(LifecycleJson.immutable(LifecycleJson.parse(row.originalRow().json(),LifecycleProofCodec.MAX_RESULT_BYTES)),
                        "complete actual original predecessor row")).toList();
        assertEquals(state,CrossRunStrategySource.terminal(previous,"episode-1",originalRows,result,LifecycleBusinessFixture.AT));
        assertEquals(2,state.episodes().size());assertEquals(previous.episodes().getFirst(),state.episodes().getFirst());
        assertEquals(List.of("death-terminal"),state.episodes().getLast().successfulSteps());
        assertEquals(1,state.episodes().stream().filter(episode->episode.runId().equals("episode-1")).count());
        assertEquals(state,CrossRunPlanning.decodeState(CrossRunPlanning.encodeState(state)));
        assertEquals(state,CrossRunStrategySource.decode(actual.auxiliary().get("one_life_strategy") instanceof OpportunityJson.Obj value?value:null).state());
        assertFalse(state.nextRunPlan().continueAsHeirAfterDeath());
        assertThrows(IllegalArgumentException.class,()->CrossRunStrategySource.terminal(CrossRunPlanning.empty(),"episode-1",result,LifecycleBusinessFixture.AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunStrategySource.terminal(previous,"another-life",result,LifecycleBusinessFixture.AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunStrategySource.terminal(previous,"episode-1",result.with("score",OpportunityJson.Nil.INSTANCE),LifecycleBusinessFixture.AT));
        var fabricated=List.of(object("{\"command\":\"enforce-demands-9\",\"ok\":true,\"result\":{\"war_victory\":{\"status\":\"victory_enforced\"}}}"));
        assertThrows(IllegalArgumentException.class,()->CrossRunStrategySource.terminal(previous,"episode-1",fabricated,result,LifecycleBusinessFixture.AT));
    }
    @Test void resultMetadataIsExplicitAndNeverBecomesPersistentFields(){
        var state=CrossRunPlanning.empty();var persisted=OpportunityJson.object(OpportunityJson.parse(CrossRunPlanning.encodeState(state)),"persisted state");
        var view=CrossRunStrategySource.decode(persisted.with("path",new OpportunityJson.Text("D:/original-shared/strategy/one-life-history.json")));
        assertEquals(Optional.of("D:/original-shared/strategy/one-life-history.json"),view.path());assertEquals(state,view.state());assertTrue(view.recordedEpisode().isEmpty());
        assertThrows(IllegalArgumentException.class,()->CrossRunStrategySource.decode(persisted.with("path",OpportunityJson.Nil.INSTANCE)));
        assertThrows(IllegalArgumentException.class,()->CrossRunStrategySource.decode(persisted.with("recorded_episode",OpportunityJson.Nil.INSTANCE)));
        assertThrows(IllegalArgumentException.class,()->CrossRunStrategySource.decode(persisted.with("unknown_state_alias",new OpportunityJson.Text("invalid"))));
    }
    @Test void actualReducerRejectsMissingNullPartialAndMistypedStrategyBeforeRecordingAnyLife()throws Exception {
        var fixture=new LifecycleBusinessFixture(temporary);var old=fixture.snapshot.facts();
        var ready=fixture.settlement();
        var valid=OpportunityJson.object(OpportunityJson.parse(CrossRunPlanning.encodeState(CrossRunPlanning.empty())),"canonical fixture strategy");
        var invalid=List.<OpportunityJson.Value>of(OpportunityJson.Nil.INSTANCE,new OpportunityJson.Bool(true),
                object("{\"episodes\":[]}"),valid.with("format_version",new OpportunityJson.Bool(true)),
                valid.with("episodes",OpportunityJson.Nil.INSTANCE));
        for(var value:invalid){
            var facts=new DriverSnapshotFacts.Known(old.driver(),old.stamp(),old.originalHistoryBasis(),old.actionRows(),
                    old.auxiliary().with("one_life_strategy",value),old.loop(),old.observation());
            var observed=new LifecycleObservationPort.Snapshot(fixture.snapshot.actual(),fixture.snapshot.source(),fixture.snapshot.semantic(),facts,fixture.snapshot.originalEvidence());
            assertThrows(IllegalArgumentException.class,()->LifecycleReducer.death(observed,ready,
                    new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD,false,Optional.empty(),List.of()),LifecycleBusinessFixture.AT));
            assertEquals(1,old.driver().commandHistory().size());
        }
        var absent=new java.util.LinkedHashMap<>(old.auxiliary().members());absent.remove("one_life_strategy");
        var missing=new DriverSnapshotFacts.Known(old.driver(),old.stamp(),old.originalHistoryBasis(),old.actionRows(),
                new OpportunityJson.Obj(absent),old.loop(),old.observation());
        var observed=new LifecycleObservationPort.Snapshot(fixture.snapshot.actual(),fixture.snapshot.source(),fixture.snapshot.semantic(),missing,fixture.snapshot.originalEvidence());
        assertThrows(IllegalArgumentException.class,()->LifecycleReducer.death(observed,ready,
                new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD,false,Optional.empty(),List.of()),LifecycleBusinessFixture.AT));
    }
    private static OpportunityJson.Obj object(String text){return OpportunityJson.object(OpportunityJson.parse(text.getBytes(java.nio.charset.StandardCharsets.UTF_8)),"controlled prior episode");}
}
