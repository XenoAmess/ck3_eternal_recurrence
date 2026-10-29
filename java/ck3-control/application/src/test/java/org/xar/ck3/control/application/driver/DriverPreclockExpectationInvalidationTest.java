package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

/** Invalidation of serialized DATA only. No private Root capture or current expectation authority is manufactured. */
final class DriverPreclockExpectationInvalidationTest {
    @Test void actualCapabilityStateEpisodeClearRemovesTheOldPreclockSourceAndPreservesItsInput() {
        var fixture=DriverCapabilityStateProducerTest.fresh();var known=DriverCapabilityStateProducerTest.published(fixture);
        Obj original=known.auxiliary().with(DriverPreclockExpectationProducer.SOURCE_KEY,
                DriverObservationEvidenceReader.reference(fixture.initial().source()));
        Obj cleared=original.with("arrange_marriage_choices",new Arr(List.of())).with("arrange_marriage_query_sequence",Nil.INSTANCE)
                .with("active_combat_retreat_token",Nil.INSTANCE);
        Obj next=DriverCapabilityStateProducer.afterEpisodeCacheClear(cleared);
        assertFalse(next.members().containsKey(DriverPreclockExpectationProducer.SOURCE_KEY));
        assertTrue(cleared.members().containsKey(DriverPreclockExpectationProducer.SOURCE_KEY));
        assertEquals(original.get("capability_configuration"),next.get("capability_configuration"));
        assertEquals(original.get("capability_session_paths"),next.get("capability_session_paths"));
        assertEquals(next,DriverJson.object(DriverJson.encode(next),DriverJson.MAX_NATIVE_BYTES));
    }
    @Test void oldMetadataWithoutCapabilityCapsuleStillRequiresAnActualCacheClearAndNeverLeaksToTheNewEpisode() {
        Obj original=new Obj(Map.of(DriverPreclockExpectationProducer.SOURCE_KEY,new Obj(Map.of("serialized_old_data",new Bool(true))),
                "arrange_marriage_choices",new Arr(List.of()),"arrange_marriage_query_sequence",Nil.INSTANCE,
                "active_combat_retreat_token",Nil.INSTANCE,"retained_original",new Text("unchanged")));
        Obj next=DriverCapabilityStateProducer.afterEpisodeCacheClear(original);
        assertFalse(next.members().containsKey(DriverPreclockExpectationProducer.SOURCE_KEY));
        assertEquals(new Text("unchanged"),next.get("retained_original"));assertTrue(original.members().containsKey(DriverPreclockExpectationProducer.SOURCE_KEY));
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.afterEpisodeCacheClear(
                original.with("arrange_marriage_query_sequence",new IntegerValue(java.math.BigInteger.ONE))));
    }
}
