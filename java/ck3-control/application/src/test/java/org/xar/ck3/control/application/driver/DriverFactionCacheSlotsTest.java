package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Persisted compatibility of the real semantic-state consumer; no original receipt or live owner is fabricated. */
final class DriverFactionCacheSlotsTest {
    @Test void preFactionOwnersRetainMissingVersusExplicitUnavailableAcrossJsonAndColdClear() {
        Obj fresh=DriverSemanticReadState.initializeFresh(new Obj(Map.of()));
        assertEquals(Nil.INSTANCE,fresh.get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
        var fields=new LinkedHashMap<>(fresh.members());fields.remove(DriverSemanticReadState.FACTION_ALERTS_FIELD);
        Obj legacy=roundTrip(new Obj(fields));
        assertFalse(legacy.members().containsKey(DriverSemanticReadState.FACTION_ALERTS_FIELD));
        assertDoesNotThrow(()->DriverSemanticReadState.replaySources(legacy,null));
        Obj cleared=roundTrip(DriverSemanticReadState.clearForCold(legacy));
        assertTrue(cleared.members().containsKey(DriverSemanticReadState.FACTION_ALERTS_FIELD));
        assertEquals(Nil.INSTANCE,cleared.get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
        assertDoesNotThrow(()->DriverSemanticReadState.replaySources(cleared,null));
    }

    @Test void populatedUnsourcedFactionSlotsCannotBecomePersistedCurrentInputs() {
        Obj fresh=DriverSemanticReadState.initializeFresh(new Obj(Map.of()));
        for(Value unsourced:java.util.List.<Value>of(new Obj(Map.of()),new Bool(false),new Text("unavailable"),new Arr(java.util.List.of()))) {
            Obj persisted=roundTrip(fresh.with(DriverSemanticReadState.FACTION_ALERTS_FIELD,unsourced));
            assertThrows(IllegalArgumentException.class,()->DriverSemanticReadState.replaySources(persisted,null));
            Obj cold=roundTrip(DriverSemanticReadState.clearForCold(persisted));
            assertEquals(Nil.INSTANCE,cold.get(DriverSemanticReadState.FACTION_ALERTS_FIELD));
            assertDoesNotThrow(()->DriverSemanticReadState.replaySources(cold,null));
        }
    }

    @Test void malformedFactionSourceFailsBeforeAnyArchiveCanLendItAnOriginal() {
        Obj fresh=DriverSemanticReadState.initializeFresh(new Obj(Map.of()));
        Obj sources=new Obj(Map.of("FACTION_ALERTS",new Obj(Map.of("receipt",new Bool(true)))));
        Obj persisted=roundTrip(fresh.with(DriverSemanticReadState.SOURCES,sources));
        assertThrows(IllegalArgumentException.class,()->DriverSemanticReadState.replaySources(persisted,null));
    }

    private static Obj roundTrip(Obj value) {
        return DriverJson.object(DriverJson.encode(value),DriverJson.MAX_NATIVE_BYTES);
    }
}
