package org.xar.ck3.control.service.root;

import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads;
import static org.junit.jupiter.api.Assertions.*;

/** Software-only unavailable DATA: no actual READ, Game, authority, submission or writer. */
final class RootMarriageBeforeReadReasonTest {
    @Test void preservesExactActualReasonAndEmptyOutcomeFlags() {
        String reason="native query unavailable: actual diagnostic supplied by source";
        var unavailable=new PlanningReadResult.Unavailable<FamilyMarriageSendReads.Observation>(reason,Optional.empty());
        var error=assertThrows(IllegalArgumentException.class,()->RootFamilyMarriageSendRuntime.requireKnownMarriageRead(unavailable));
        assertEquals("actual independent marriage before storage/preparation read is unavailable:reason="+reason
                +":original=none:no_decode_failure:no_observed_failure",error.getMessage());
        assertEquals(reason,unavailable.reason());assertTrue(unavailable.original().isEmpty());
    }
    @Test void preservesUnknownAsUnknownDataAndNeverInventsKnown() {
        var outcome=new NativeActionPort.Unknown("software-only-read","actual unknown reason",new byte[]{1},Optional.empty());
        var unavailable=new PlanningReadResult.Unavailable<FamilyMarriageSendReads.Observation>("read outcome remains unknown",Optional.of(outcome));
        var error=assertThrows(IllegalArgumentException.class,()->RootFamilyMarriageSendRuntime.requireKnownMarriageRead(unavailable));
        assertTrue(error.getMessage().contains(":reason=read outcome remains unknown:original=Unknown:"));
        assertSame(outcome,unavailable.original().orElseThrow());assertEquals("actual unknown reason",outcome.reason());
    }
    @Test void boundsReasonWithoutDroppingTypedFlags() {
        var unavailable=new PlanningReadResult.Unavailable<FamilyMarriageSendReads.Observation>("x".repeat(3000),Optional.empty());
        var error=assertThrows(IllegalArgumentException.class,()->RootFamilyMarriageSendRuntime.requireKnownMarriageRead(unavailable));
        assertTrue(error.getMessage().contains(":reason="+"x".repeat(2048)+":original=none:no_decode_failure:no_observed_failure"));
        assertFalse(error.getMessage().contains("x".repeat(2049)));assertEquals(3000,unavailable.reason().length());
    }
}
