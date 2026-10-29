package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection;

/** Decoded cache DTO tests do not construct a Root session, reviewed stage or raw admission ticket. */
class RootColdResumeSessionTest {
    private static WindowsJobProcess.ProcessIdentity game() {
        return new WindowsJobProcess.ProcessIdentity(123,"134000000000000001","D:/synthetic/ck3.exe");
    }
    private static NativeColdAdoptionProjection unboundData() {
        var value=StrictJson.object();value.put("schema","xar.native.owner-cold-adoption.v1");value.put("binding_state","unbound");
        for(String name:java.util.List.of("session_bridge_pid","restore_kind","rejection","pending")){value.putNull(name);}
        return NativeColdAdoptionProjection.fromJson(value);
    }
    @Test void rawDataKeepsPublicAndNativeRevisionSeparateAndNeverInventsAnEpisode() {
        var frame=new RootColdResumeSession.RawColdFrame("native:19",20,19,53279400,40526,true,true,game(),
                "synthetic-pipe","18446744073709551615","a".repeat(64),7,unboundData());
        var value=StrictJson.parse(StrictJson.canonical(frame.toJson()));
        assertEquals(20,value.get("public_revision").intValue()); assertEquals(19,value.get("native_revision").intValue());
        assertEquals("134000000000000001",value.get("actual_game").get("creation_filetime_decimal").textValue());
        assertEquals("18446744073709551615",value.get("connection_generation").textValue());
        assertEquals("xar.native.owner-cold-adoption.v1",value.get("owner_cold_adoption").get("schema").textValue());
        assertTrue(value.get("owner_cold_adoption").get("pending").isNull());
        assertNull(value.get("episode_run_id")); assertNull(value.get("native_admitted"));
    }
    @Test void wrongRawSnapshotRevisionSequenceHashAndUnsafeCountersFailBeforeAnyTicketExists() {
        assertThrows(RuntimeException.class,()->new RootColdResumeSession.RawColdFrame("native:20",20,19,1,1,true,true,game(),"p","1","a".repeat(64),1,unboundData()));
        assertThrows(RuntimeException.class,()->new RootColdResumeSession.RawColdFrame("native:19",20,19,1,1,true,true,game(),"p","1","bad",1,unboundData()));
        assertThrows(RuntimeException.class,()->new RootColdResumeSession.RawColdFrame("native:19",20,19,1,1,true,true,game(),"p","1","a".repeat(64),0,unboundData()));
        assertThrows(RuntimeException.class,()->new RootColdResumeSession.RawColdFrame("native:19",StrictJson.MAX_SAFE_INTEGER+1,19,1,1,true,true,game(),"p","1","a".repeat(64),1,unboundData()));
        assertThrows(RuntimeException.class,()->new RootColdResumeSession.RawColdFrame("native:19",20,19,1,1,true,true,game(),"p","1","a".repeat(64),1,null));
        for(String generation:java.util.List.of("0","01","-1","18446744073709551616")) {
            assertThrows(RuntimeException.class,()->new RootColdResumeSession.RawColdFrame("native:19",20,19,1,1,true,true,game(),"p",generation,"a".repeat(64),1,unboundData()));
        }
    }
    @Test void completedCapProjectionRoundtripsStringIdentitiesWithoutGrantingAPoststateTicket() {
        var actual=new RootColdResumeSession.CapabilitiesCompletion("c".repeat(64),8,game(),game(),"synthetic-pipe","18446744073709551615");
        var value=StrictJson.parse(StrictJson.canonical(actual.toJson()));
        assertEquals("18446744073709551615",value.get("connection_generation").textValue());
        assertEquals("134000000000000001",value.get("actual_owner").get("creation_filetime_decimal").textValue());
        assertEquals(8,value.get("arrival_sequence").intValue());assertNull(value.get("native_admitted"));
    }
    @Test void malformedCompletedCapIdentityAndUnsafeArrivalFailBeforeQualification() {
        for(String generation:java.util.List.of("01","0","18446744073709551616")) {
            assertThrows(RuntimeException.class,()->new RootColdResumeSession.CapabilitiesCompletion("c".repeat(64),8,game(),game(),"p",generation));
        }
        assertThrows(RuntimeException.class,()->new RootColdResumeSession.CapabilitiesCompletion("bad",8,game(),game(),"p","1"));
        assertThrows(RuntimeException.class,()->new RootColdResumeSession.CapabilitiesCompletion("c".repeat(64),StrictJson.MAX_SAFE_INTEGER+1,game(),game(),"p","1"));
    }
}
