package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;

public final class DriverRollbackFailurePublicationTest {
    private record Fixture(DriverStateSnapshot.Complete abandoned,DriverStateSnapshot.Complete restored) { }
    private Fixture fixture() {
        var checkpoint=StrictJson.object();checkpoint.put("sha256","a".repeat(64));checkpoint.put("size",20);checkpoint.put("date_raw",240);checkpoint.put("history_index",1);
        var original=StrictJson.object();original.put("format_version",2);original.put("pipe_name","test-pipe");original.put("bridge_pid",123);
        original.put("episode_character_id",29829);original.put("episode_run_id","episode-1");original.set("last_checkpoint",checkpoint);
        original.putNull("rollback_war_failure");original.putArray("rollback_war_failures");original.putNull("managed_restore_transaction");
        original.putNull("succession_expectation");original.putNull("succession_lifecycle");original.putObject("campaign_goal").put("purpose","retained actual campaign");
        var history=original.putArray("command_history");var save=history.addObject();save.put("index",1);save.put("command","save-checkpoint");save.put("ok",true);save.putObject("result").set("checkpoint",checkpoint.deepCopy());
        var huge=history.addObject();huge.put("index",2);huge.put("command","query-large-history");huge.put("ok",false);
        huge.putObject("result").put("status","unknown").put("retained_original","x".repeat(150000));
        var restored=original.deepCopy();restored.put("bridge_pid",124);var retained=restored.putArray("command_history");retained.add(save.deepCopy());
        var restart=retained.addObject();restart.put("index",2);restart.put("command","restore-checkpoint");restart.put("ok",true);
        var result=restart.putObject("result");result.put("step","restore-checkpoint");result.put("accepted",true);result.put("status","restored");
        result.put("backend_id","native-headless");result.put("source","native-session-lifecycle-queue");result.put("restored_date_raw",240);result.put("map_ready",true);
        result.set("checkpoint",checkpoint.deepCopy());var lifecycle=result.putObject("lifecycle");lifecycle.put("previous_pid",123);lifecycle.put("pid",124);
        return new Fixture(DriverStateSnapshot.decodeComplete(StrictJson.canonical(original,DriverJson.MAX_NATIVE_BYTES)),
                DriverStateSnapshot.decodeComplete(StrictJson.canonical(restored,DriverJson.MAX_NATIVE_BYTES)));
    }
    private static org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj snapshot(int pid,int date) {
        String raw="{\"episode_run_id\":\"episode-1\",\"paused\":true,\"map_ready\":true,\"date_raw\":"+date
                +",\"played_character\":{\"character_id\":29829,\"alive\":true},\"diagnostics\":{\"bridge_pid\":"+pid+"},\"active_wars\":[],\"player_armies\":[]}";
        return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);
    }
    @Test void fullOriginalHistoryBeyondSmallJsonLimitIsConsumedAndOtherSlotsRemainExact() {
        var f=fixture();var after=DriverRollbackFailurePublication.project(f.restored,f.abandoned,snapshot(124,240),Optional.empty(),8);
        assertEquals(f.restored.commandHistory(),after.commandHistory());assertSame(f.restored.campaignGoal(),after.campaignGoal());
        assertSame(f.restored.successionLifecycle(),after.successionLifecycle());assertSame(f.restored.managedRestoreTransaction(),after.managedRestoreTransaction());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,after.rollbackWarFailure());
        assertEquals("[]",new String(((DriverStateSnapshot.Value)after.rollbackWarFailures()).json(),StandardCharsets.UTF_8));
    }
    @Test void staleProcessOrDateCannotPublishRollbackAdvisory() {
        var f=fixture();assertThrows(IllegalArgumentException.class,()->DriverRollbackFailurePublication.project(f.restored,f.abandoned,snapshot(123,240),Optional.empty(),8));
        assertThrows(IllegalArgumentException.class,()->DriverRollbackFailurePublication.project(f.restored,f.abandoned,snapshot(124,264),Optional.empty(),8));
        assertThrows(IllegalArgumentException.class,()->DriverRollbackFailurePublication.project(f.restored,f.abandoned,snapshot(124,240),Optional.of(snapshot(124,240)),8));
    }
}
