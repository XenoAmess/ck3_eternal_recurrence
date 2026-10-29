package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure proposal/serde consumers only. This class never fabricates a private Root capture or a published CAS proof. */
final class DriverOperatorRebindProjectionTest {
    @Test void changedActorKeepsEveryHistoricalAndLifecycleSlotWhileInvalidatingActualCharacterCaches() {
        var before=driver();var auxiliary=auxiliary();byte[] original=before.encode();
        var proposed=DriverOperatorRebindProjection.propose(before,auxiliary,new OperatorPlayerSwitch.Request(3,BigInteger.valueOf(99)));
        assertTrue(proposed.rebindPerformed());assertEquals(BigInteger.valueOf(3),proposed.driver().session().actorId());
        assertEquals(before.session().episodeRunId(),proposed.driver().session().episodeRunId());
        assertSame(before.commandHistory(),proposed.driver().commandHistory());
        assertSame(before.lastCheckpoint(),proposed.driver().lastCheckpoint());
        assertSame(before.rollbackWarFailure(),proposed.driver().rollbackWarFailure());
        assertSame(before.managedRestoreTransaction(),proposed.driver().managedRestoreTransaction());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,proposed.driver().successionExpectation());
        assertSame(before.successionLifecycle(),proposed.driver().successionLifecycle());assertSame(before.campaignGoal(),proposed.driver().campaignGoal());
        assertSame(before.rollbackWarFailures(),proposed.driver().rollbackWarFailures());assertArrayEquals(original,before.encode());
        var next=proposed.auxiliary();
        assertEquals(new Text("active_operator_rebind"),next.get("episode_binding_state"));
        assertEquals(new Text("operator_played_character_rebind"),next.get("restore_kind"));
        assertFalse(next.members().containsKey("driver_state_restore_kind"));assertFalse(next.members().containsKey("active_combat_retreat_v1_token"));
        for(String key:List.of("active_combat_retreat_token","campaign_root_context_query","capability_inputs","capability_observed_native_source",
                "independent_battle_speed_readiness","arrange_marriage_query_sequence","succession_reconciliation"))assertSame(Nil.INSTANCE,next.get(key),key);
        assertEquals(new Obj(Map.of()),next.get(DriverSemanticReadState.SOURCES));
        assertEquals(new Obj(Map.of("marriage",Nil.INSTANCE,"campaign_root",Nil.INSTANCE)),next.get("capability_read_sources"));
        assertFalse(next.members().containsKey("capability_retreat_source"));assertFalse(next.members().containsKey(DriverPreclockExpectationProducer.SOURCE_KEY));
        var roundtrip=DriverStateSnapshot.decodeComplete(proposed.driver().encode());
        assertArrayEquals(proposed.driver().encode(),roundtrip.encode());
        assertArrayEquals(before.commandHistory().getFirst().originalRow().json(),roundtrip.commandHistory().getFirst().originalRow().json());
        assertEquals(next,DriverJson.object(DriverJson.encode(next),DriverJson.MAX_NATIVE_BYTES));
        assertEquals(new Text("keep-original-domain-data"),next.get("unrelated_original"));
    }
    @Test void sameActorIsTheExactNoChangeProposalAndDoesNotInvalidateOrCreateAnyPublicationMetadata() {
        var before=driver();var auxiliary=auxiliary();
        var proposed=DriverOperatorRebindProjection.propose(before,auxiliary,new OperatorPlayerSwitch.Request(2,BigInteger.valueOf(99)));
        assertFalse(proposed.rebindPerformed());assertSame(before,proposed.driver());assertSame(auxiliary,proposed.auxiliary());
        assertFalse(auxiliary.members().containsKey(DriverOperatorRebindSource.PUBLICATION_KEY));
    }
    @Test void detachedOrMalformedPublicationMetadataCannotDecodeAsARecordedOperatorSource() {
        for(String row:List.of("{}","{\"schema\":\"xar.java.operator-driver-publication/v1\"}",
                "{\"schema\":\"xar.java.operator-driver-publication/v1\",\"canonical_sequence\":true}",
                "{\"schema\":\"xar.java.operator-driver-publication/v1\",\"transition\":null}"))
            assertThrows(IllegalArgumentException.class,()->DriverOperatorRebindOriginals.decodePublication(new RawJson(row.getBytes(StandardCharsets.UTF_8))));
    }
    private static DriverStateSnapshot.Complete driver() {
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("original-pipe",7,BigInteger.TWO,"same-original-run"),
                List.of(new DriverStateSnapshot.HistoryEntry(1,value("{\"index\":1,\"command\":\"actual-retained\",\"ok\":true,\"result\":{\"opaque\":900719925474099312345}}"))),
                value("{\"checkpoint\":\"unchanged\"}"),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),
                value("{\"old_estate\":true}"),value("{\"lifecycle\":\"ordinary_campaign_succession\",\"status\":\"retained\"}"),
                value("{\"original_goal\":true}"),new DriverStateSnapshot.Missing());
    }
    private static Obj auxiliary() {
        var fields=new java.util.LinkedHashMap<String,OpportunityJson.Value>();
        fields.put("restore_kind",new Text("same_pid_hot"));fields.put("episode_binding_state",new Text("active_resumed"));
        for(String key:List.of("active_combat_retreat_token","campaign_root_context_query","capability_inputs","capability_observed_native_source",
                "independent_battle_speed_readiness","arrange_marriage_query_sequence","succession_reconciliation"))fields.put(key,new Text("old-character-source"));
        fields.put("arrange_marriage_choices",new Arr(List.of(new Text("old-choice"))));
        fields.put(DriverSemanticReadState.SOURCES,new Obj(Map.of("COMBAT_V2",new Obj(Map.of("receipt",new Text("old-receipt"))))));
        fields.put("capability_read_sources",new Obj(Map.of("marriage",new Text("old-marriage"),"campaign_root",new Text("old-root"))));
        fields.put("capability_retreat_source",new Text("old-retreat"));fields.put(DriverPreclockExpectationProducer.SOURCE_KEY,new Text("old-preclock"));
        fields.put("unrelated_original",new Text("keep-original-domain-data"));return new Obj(fields);
    }
    private static DriverStateSnapshot.Value value(String original){return new DriverStateSnapshot.Value(original.getBytes(StandardCharsets.UTF_8));}
}
