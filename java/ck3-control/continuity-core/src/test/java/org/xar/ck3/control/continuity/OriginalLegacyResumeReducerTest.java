package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Pure closed event/history tests. None of these descriptor DATA references is a physical ticket. */
final class OriginalLegacyResumeReducerTest {
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186";
    @Test void exactClosedDeltaPreservesEveryUnknownPendingCycleDomainAndWindowFieldAndRoundTrips() {
        var original=before();var delta=delta(original,new OriginalLegacyResume.MissingHistory(),OriginalLegacyResume.Route.SAME_PID);
        assertEquals(delta,OriginalLegacyResume.decode(delta.toJson()));var request=delta.request();
        var next=OriginalLegacyResume.reduce(original,request);var expected=original.toJson();
        expected.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,delta.fullDriver().toJson());expected.set(OriginalLegacyResume.STATE_FIELD,delta.toJson());
        assertTrue(ContinuityJson.same(expected,next.toJson()));assertEquals(original.sequence(),next.sequence());assertEquals(original.settledCycles(),next.settledCycles());
        assertEquals(original.origin(),next.origin());assertEquals(original.toJson().get("UNKNOWN"),next.toJson().get("UNKNOWN"));
        assertFalse(next.toJson().has(WriterContracts.GAMEPLAY_ENTRY_FIELD));OriginalLegacyResume.requireReduction(original,next,request,false);
        var sequenced=next.toJson();sequenced.put("sequence",original.sequence()+1);sequenced.put("last_event_identity",request.identity());
        OriginalLegacyResume.requireReduction(original,ContinuityState.fromJson(sequenced,MACHINE),request,true);
        sequenced.put("last_settled_cycles",original.settledCycles()+1);
        assertThrows(IllegalArgumentException.class,()->OriginalLegacyResume.requireReduction(original,ContinuityState.fromJson(sequenced,MACHINE),request,true));
    }
    @Test void missingNullBoundHistoryAndFreshEntryRemainDifferentAndWrongIntegerBirthEvidenceRefuse() {
        var original=before();var missing=delta(original,new OriginalLegacyResume.MissingHistory(),OriginalLegacyResume.Route.BIND_UNBOUND);
        var nulled=original.toJson();nulled.putNull(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD);var nullState=ContinuityState.fromJson(nulled,MACHINE);
        assertThrows(IllegalArgumentException.class,()->OriginalLegacyResume.reduce(nullState,missing.request()));
        var bound=original.toJson();bound.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,ref(20).toJson());var boundState=ContinuityState.fromJson(bound,MACHINE);
        var matching=delta(boundState,new OriginalLegacyResume.BoundHistory(ref(20)),OriginalLegacyResume.Route.COLD_CHECKPOINT);
        assertDoesNotThrow(()->OriginalLegacyResume.reduce(boundState,matching.request()));
        assertThrows(IllegalArgumentException.class,()->OriginalLegacyResume.reduce(boundState,missing.request()));
        var badActor=matching.toJson();badActor.put("actor_id",true);assertThrows(IllegalArgumentException.class,()->OriginalLegacyResume.decode(badActor));
        var badBirth=matching.toJson();((com.fasterxml.jackson.databind.node.ObjectNode)badBirth.get("game")).put("creation_filetime","01");
        assertThrows(IllegalArgumentException.class,()->OriginalLegacyResume.decode(badBirth));
        var detached=new WriterContracts.Request(OriginalLegacyResume.KIND,matching.request().details(),List.of(ref(1)));
        assertThrows(IllegalArgumentException.class,()->OriginalLegacyResume.checked(boundState,detached));
        var fresh=original.toJson();fresh.putObject(WriterContracts.GAMEPLAY_ENTRY_FIELD).put("already","fresh");var existing=ContinuityState.fromJson(fresh,MACHINE);
        assertThrows(IllegalArgumentException.class,()->OriginalLegacyResume.reduce(existing,delta(existing,new OriginalLegacyResume.MissingHistory(),OriginalLegacyResume.Route.SAME_PID).request()));
    }
    private static ContinuityState before() {
        var state=StrictJson.object();state.put("schema","root.ck3.continuity-window/v1");state.put("machine_id",MACHINE);state.put("sequence",4);
        state.put("window_id",1);state.put("start_date_raw",24000);state.put("target_date_raw",24240);state.put("target_days",10);state.put("status","running");
        state.put("last_settled_cycles",3);state.put("last_settled_date_raw",24072);state.putNull("pending_cycle");state.putNull("pending_checkpoint");
        state.putArray("UNKNOWN").addObject().put("request","unknown-native-write");state.putObject("domain_state").put("opaque","unchanged");
        return ContinuityState.fromJson(state,MACHINE);
    }
    private static OriginalLegacyResume.Delta delta(ContinuityState before,OriginalLegacyResume.BeforeHistory history,OriginalLegacyResume.Route route) {
        return new OriginalLegacyResume.Delta(ref(1),MACHINE,ContinuityJson.digest(before.toJson()),history,route,"original-session","original-pipe",
                new OriginalLegacyResume.Game(42,"134370900000000001"),7,"native-7-original",0,0,ref(2),ref(3),ref(4),ref(5),ref(6),ref(7),ref(8),Optional.empty(),List.of(ref(9)));
    }
    private static ExactRef ref(int index){return new ExactRef("D:/descriptor-data/source-"+index+".json",index+1,"a".repeat(64));}
}
