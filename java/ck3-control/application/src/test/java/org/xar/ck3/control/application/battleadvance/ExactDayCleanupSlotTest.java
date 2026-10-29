package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.advance.AdvanceClock;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Shared actual cleanup slot guard, including its original native JSON representation. */
final class ExactDayCleanupSlotTest {
    @Test void matchingGenerationCannotAuthorizeAnotherSlotAfterSerializationRoundTrip() {
        var original=BattleAdvanceFixture.armed();
        for(String field:List.of("speed","army_count")) {
            var changed=SentinelObservation.toJson(original);
            changed.put(field,field.equals("speed")?4:2);
            var actual=SentinelObservation.decode(changed);
            assertEquals(original.generation(),actual.generation());
            assertThrows(IllegalArgumentException.class,()->AdvanceClock.requireSameSlot(original,actual));
        }
    }
    @Test void sameSlotAllowsDifferentObservedPhaseWithoutGrantingStopOrReplayCredit() {
        var original=BattleAdvanceFixture.armed();
        assertDoesNotThrow(()->AdvanceClock.requireSameSlot(original,SentinelObservation.decode(SentinelObservation.toJson(BattleAdvanceFixture.idle()))));
        assertDoesNotThrow(()->AdvanceClock.requireSameSlot(original,SentinelObservation.decode(SentinelObservation.toJson(BattleAdvanceFixture.stopped()))));
    }
}
