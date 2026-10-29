package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Persisted slot compatibility uses the actual shared cache consumer; no Native fixture or receipt is constructed. */
final class DriverBattleControlCacheSlotsTest {
    @Test void existingSavedOwnersWithoutBattleCacheRemainReadableButPartialOrUnsourcedValuesFail() {
        Obj fresh = DriverSemanticReadState.initializeFresh(new Obj(Map.of()));
        DriverSemanticReadState.replaySources(fresh, null); // Empty source tables perform no archive I/O.
        var legacyFields = new LinkedHashMap<>(fresh.members());
        BattleControlSemanticProjection.fields().forEach(legacyFields::remove);
        Obj legacy = new Obj(legacyFields);
        assertDoesNotThrow(() -> DriverSemanticReadState.replaySources(legacy, null));
        assertThrows(IllegalArgumentException.class, () -> DriverSemanticReadState.replaySources(
                legacy.with("battle_control_snapshot_v1_status", Nil.INSTANCE), null));
        assertThrows(IllegalArgumentException.class, () -> DriverSemanticReadState.replaySources(
                fresh.with("battle_control_snapshot_v1_query_sequence", new IntegerValue(BigInteger.ONE)), null));
    }
    @Test void actualColdClearInitializesAllNewSlotsAndRemovesPriorFrameOperands() {
        Obj fresh = DriverSemanticReadState.initializeFresh(new Obj(Map.of()));
        Obj priorFrame = fresh.with("battle_control_snapshot_v1_status", new Text("available"))
                .with("battle_control_snapshot_v1_query_sequence", new IntegerValue(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)))
                .with("active_combat_resume_inputs_v1", new Obj(Map.of("old_frame", new Bool(true))));
        Obj cleared = DriverSemanticReadState.clearForCold(priorFrame);
        for (String field : BattleControlSemanticProjection.fields()) assertEquals(Nil.INSTANCE, cleared.get(field));
        DriverSemanticReadState.replaySources(cleared, null);
        assertEquals(cleared, DriverJson.object(DriverJson.encode(cleared), DriverJson.MAX_NATIVE_BYTES));
    }
}
