package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class CapturedNoDispatchRecoveryReducerTest {
    @Test void ordinaryInterruptionRetainsTheSavedFrontierWhenCurrentDateHasAdvanced() {
        var before=state();var details=details(24_120,7);
        var interrupted=OriginalWindowReducer.reduce(before,"ordinary_batch_interrupted",details);
        assertEquals("repair_required",interrupted.get("status").textValue());
        assertEquals(before.get("last_settled_date_raw"),interrupted.get("last_settled_date_raw"));
        assertEquals(before.get("last_settled_cycles"),interrupted.get("last_settled_cycles"));
        assertEquals(before.get("pending_cycle"),interrupted.get("pending_cycle"));
        assertEquals(before.get("UNKNOWN"),interrupted.get("UNKNOWN"));
        var legacy=OriginalWindowReducer.reduce(before,"repair_required",details);
        assertEquals(24_120,legacy.get("last_settled_date_raw").longValue(),"existing v1 historical replay retains its original meaning");
    }
    @Test void capturedRecoveryChangesOnlyStatusAndCurrentBindingAndRoundTrips() {
        var before=OriginalWindowReducer.reduce(state(),"ordinary_batch_interrupted",details(24_120,7));
        var details=details(24_144,7);var after=OriginalWindowReducer.reduce(before,"captured_no_dispatch_recovery",details);
        var expected=before.deepCopy();expected.put("status","running");expected.set("latest_binding",details.get("frame"));
        assertTrue(ContinuityJson.same(expected,after));
        assertTrue(ContinuityJson.same(after,ContinuityJson.parseObject(ContinuityJson.canonical(after),ContinuityJson.LEDGER_MAX_BYTES)));
        assertEquals(7,after.get("last_settled_cycles").longValue());assertEquals(24_072,after.get("last_settled_date_raw").longValue());
        assertEquals(1,after.get("window_id").longValue());assertEquals(24_000,after.get("start_date_raw").longValue());
    }
    @Test void capturedRecoveryRejectsCreditActorEpisodeAndNativeRevisionChanges() {
        var before=OriginalWindowReducer.reduce(state(),"ordinary_batch_interrupted",details(24_120,7));
        var credit=details(24_144,8);assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(before,"captured_no_dispatch_recovery",credit));
        var actor=details(24_144,7);((ObjectNode)actor.get("frame")).put("actor_character_id",99);
        assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(before,"captured_no_dispatch_recovery",actor));
        var episode=details(24_144,7);((ObjectNode)episode.get("frame")).put("episode_run_id","other");
        assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(before,"captured_no_dispatch_recovery",episode));
        var revision=details(24_144,7);((ObjectNode)revision.get("frame")).put("native_revision",2);
        assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(before,"captured_no_dispatch_recovery",revision));
        var wrongType=details(24_144,7);wrongType.put("completed_cycles",true);
        assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(before,"captured_no_dispatch_recovery",wrongType));
    }
    @Test void ordinaryInterruptionRejectsClaimedSavedCreditAndNeverMutatesThePredecessor() {
        var before=state();var bytes=ContinuityJson.canonical(before);
        assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(before,"ordinary_batch_interrupted",details(24_120,8)));
        assertArrayEquals(bytes,ContinuityJson.canonical(before));
        assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(before,"ordinary_batch_interrupted",details(24_048,7)));
        assertArrayEquals(bytes,ContinuityJson.canonical(before));
    }
    private static ObjectNode state() {
        var state=StrictJson.object();state.put("schema","root.ck3.continuity-window/v1");state.put("machine_id","xenoamess-full-tower-eb9d2c1186");
        state.put("window_id",1);state.put("status","running");state.put("target_days",10_958);state.put("start_date_raw",24_000);
        state.put("target_date_raw",287_000);state.put("last_settled_date_raw",24_072);state.put("last_settled_cycles",7);
        state.set("latest_binding",frame(24_120));state.putNull("pending_cycle");state.putObject("pending_checkpoint").put("retained",true);
        state.putArray("UNKNOWN").addObject().put("request","retained-no-replay");state.putObject("java_ordinary_cycle_state").put("dirty",true);
        return state;
    }
    private static ObjectNode details(long date,long cycles) {
        var details=StrictJson.object();details.put("evidence_id","test-retained-current-frontier");details.put("source","test-java-captured-recovery");
        details.put("machine_id","xenoamess-full-tower-eb9d2c1186");details.put("completed_cycles",cycles);details.put("reason","actual interrupted metadata suffix");
        details.set("frame",frame(date));return details;
    }
    private static ObjectNode frame(long date) {
        var frame=StrictJson.object();frame.put("date_raw",date);frame.put("actor_character_id",42);frame.put("episode_run_id","retained-episode");
        frame.put("snapshot_id","retained-current-snapshot");frame.put("revision",5);frame.put("native_revision",9);return frame;
    }
}
