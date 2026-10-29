package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;

final class GameplayEntryReducerTest {
    @Test void productionReducerBindsOnlyActualFullHistoryAndEntryWithoutResettingUnknownActionsOrWindow() {
        var before=before();var request=request();var after=GameplayEntryAuthority.reduceInitial(before,request);
        assertEquals(before.sequence(),after.sequence());assertEquals(before.origin(),after.origin());
        var expected=before.toJson();expected.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,request.detailsObject().get("full_driver"));
        var entry=request.detailsObject();entry.put("schema","xar.java.first-gameplay-entry-state/v1");expected.set(WriterContracts.GAMEPLAY_ENTRY_FIELD,entry);
        assertTrue(ContinuityJson.same(expected,after.toJson()));assertTrue(after.toJson().get("UNKNOWN").has("historical-request"));
    }
    @Test void missingNullAndExistingBaselineAreDifferentAndCannotBeReinitialized() {
        for(String field:List.of(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,WriterContracts.GAMEPLAY_ENTRY_FIELD)) {
            var nullBody=before().toJson();nullBody.putNull(field);
            assertThrows(IllegalArgumentException.class,()->GameplayEntryAuthority.reduceInitial(ContinuityState.fromJson(nullBody,"fixture-machine"),request()));
        }
        var once=GameplayEntryAuthority.reduceInitial(before(),request());
        assertThrows(IllegalArgumentException.class,()->GameplayEntryAuthority.reduceInitial(once,request()));
    }
    @Test void wrongTypesMissingFieldsAndForeignMachineFailBeforeReducerPublication() {
        var original=request();
        for(String field:List.of("full_driver","driver_facts","entry_basis","start_receipt")) {
            var row=original.detailsObject();row.remove(field);
            assertThrows(IllegalArgumentException.class,()->GameplayEntryAuthority.reduceInitial(before(),new WriterContracts.Request(original.kind(),ContinuityJson.canonical(row),original.evidence())));
        }
        var wrong=original.detailsObject();((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("frame")).put("revision",true);
        assertThrows(IllegalArgumentException.class,()->GameplayEntryAuthority.reduceInitial(before(),new WriterContracts.Request(original.kind(),ContinuityJson.canonical(wrong),original.evidence())));
        var foreign=original.detailsObject();((com.fasterxml.jackson.databind.node.ObjectNode)foreign.get("source")).put("machine_id","another-machine");
        assertThrows(IllegalArgumentException.class,()->GameplayEntryAuthority.reduceInitial(before(),new WriterContracts.Request(original.kind(),ContinuityJson.canonical(foreign),original.evidence())));
    }
    @Test void exactLargeGameBirthAndConnectionRemainCanonicalDecimalStrings() {
        var after=GameplayEntryAuthority.reduceInitial(before(),request());var entry=after.toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD);
        assertTrue(entry.get("game").get("creation_filetime").isTextual());assertEquals("134055108000000017",entry.get("game").get("creation_filetime").textValue());
        assertEquals("18446744073709551615",entry.get("frame").get("connection_generation").textValue());
        var request=request();var number=request.detailsObject();((com.fasterxml.jackson.databind.node.ObjectNode)number.get("game")).put("creation_filetime",134055108000000016L);
        assertThrows(IllegalArgumentException.class,()->GameplayEntryAuthority.reduceInitial(before(),new WriterContracts.Request(request.kind(),ContinuityJson.canonical(number),request.evidence())));
    }
    private static ContinuityState before() {
        var row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id","fixture-machine");row.put("sequence",4);row.put("window_id",1);
        row.put("status","running");row.put("target_days",10);row.put("start_date_raw",53144328);row.put("target_date_raw",53144568);
        row.put("last_settled_date_raw",53144328);row.put("last_settled_cycles",0);row.putObject("UNKNOWN").put("historical-request","do-not-replay");
        row.putNull("pending_cycle");row.put("NEXT","historical-next");row.putObject("java_action_lifecycle_head").put("retained","actual-old-chain");
        return ContinuityState.fromJson(row,"fixture-machine");
    }
    private static WriterContracts.Request request() {
        ExactRef ref=new ExactRef(Path.of("entry-fixture.json").toAbsolutePath().normalize().toString(),2,"a".repeat(64));
        var row=StrictJson.object();row.put("evidence_id","gameplay-entry:start-1");row.put("action_id","start-1");row.put("action_body_sha256","b".repeat(64));
        row.put("auxiliary_sha256","c".repeat(64));row.put("episode_id","java-start-"+"b".repeat(32));row.put("session_id","actual-session");
        var source=row.putObject("source");source.put("machine_id","fixture-machine");for(String field:List.of("implementation","policy","environment"))source.set(field,ref.toJson());
        for(String field:List.of("start_receipt","entry_basis","full_driver","driver_facts"))row.set(field,ref.toJson());
        row.put("driver_version",0);row.put("episode_epoch",0);
        var frame=row.putObject("frame");frame.put("snapshot_id","actual-frame");frame.put("revision",2);frame.put("native_revision",9);frame.put("date_raw",53144328);
        frame.put("player_character_id",73);frame.put("connection_generation","18446744073709551615");
        var game=row.putObject("game");game.put("pid",42);game.put("creation_filetime","134055108000000017");
        return new WriterContracts.Request(WriterContracts.GAMEPLAY_ENTRY_KIND,ContinuityJson.canonical(row),List.of(ref));
    }
}
