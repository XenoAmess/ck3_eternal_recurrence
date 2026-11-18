package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;

final class FullSnapshotEventOptionControlTest {
    @Test void queryAndSelectedAuthoredIndexShareExactFullClaimWithoutDuplicatingTheIndex() throws Exception {
        var until=Instant.parse("2026-11-18T11:00:00Z");var revision=new BigInteger("9007199254740993");
        var query=FullSnapshotEventOptionControl.query("native:"+revision,revision,until,42);
        var select=FullSnapshotEventOptionControl.select("native:"+revision,revision,until,42,1);
        assertEquals("select-event-option-2",select.step());assertEquals(1,FullSnapshotEventOptionControl.selectedIndex(select.step()));
        assertEquals("game.command.select-event-option-2",select.requiredCapability().orElseThrow());
        assertArrayEquals(query.additionalFields().bytes(),select.additionalFields().bytes());
        var fields=StrictJson.parse(select.additionalFields().bytes());assertEquals(2,fields.size());
        assertEquals(1,fields.path("arguments").size());assertEquals(42,fields.path("arguments").path("event_instance_id").intValue());
        var claim=fields.path("event_option_control");assertEquals(revision,claim.path("native_revision").bigIntegerValue());
        assertEquals(ExactCk3Build.CK3_1210.executableSha256().toUpperCase(java.util.Locale.ROOT),claim.path("executable_sha256").textValue());
        assertEquals(until.toEpochMilli(),claim.path("deadline_unix_ms").longValue());
    }
    @Test void finiteOriginalIdentityAndAuthoredIndexBoundsFailClosed() {
        var until=Instant.parse("2026-11-18T11:00:00Z");
        for(int index:new int[]{-1,512,Integer.MAX_VALUE})assertThrows(IllegalArgumentException.class,()->FullSnapshotEventOptionControl.select("native:1",BigInteger.ONE,until,42,index));
        for(String step:new String[]{"select-event-option-0","select-event-option-01","select-event-option-513","select-event-option-1.0"})assertThrows(IllegalArgumentException.class,()->FullSnapshotEventOptionControl.selectedIndex(step));
        assertEquals(0,FullSnapshotEventOptionControl.selectedIndex("select-event-option-1"));assertEquals(511,FullSnapshotEventOptionControl.selectedIndex("select-event-option-512"));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotEventOptionControl.query("native:2",BigInteger.ONE,until,42));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotEventOptionControl.query("native:1",BigInteger.ONE,Instant.EPOCH,42));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotEventOptionControl.query("native:1",BigInteger.ONE,until,0));
    }
}
