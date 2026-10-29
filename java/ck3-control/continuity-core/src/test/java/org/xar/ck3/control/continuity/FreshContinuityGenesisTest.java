package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Closed DATA/serde/reducer contracts only; no private Entry authority or physical Game is constructed. */
final class FreshContinuityGenesisTest {
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186";
    private static ContinuityState initial()throws java.security.NoSuchAlgorithmException {
        var plan=new FreshContinuityGenesis.Plan(MACHINE,1,OriginalWindowReducer.TARGET_DAYS);
        byte[] request=FreshContinuityGenesis.encode(plan);
        // ExactRef is DATA here. The physical initializer test separately observes the real original request.
        String digest=java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(request));
        return FreshContinuityGenesis.initial(plan,new ExactRef("D:/software-fixture/genesis-request.json",request.length,digest));
    }
    @Test void explicitFreshStateHasNoObservedOriginAndRoundtripPreservesMissingNullAndUnknown()throws Exception {
        var state=initial();var row=state.toJson();
        row.putNull("pending_cycle");row.putArray("unknown_actions").add("retained-original-unknown");row.put("NEXT",7);
        var reopened=ContinuityState.fromJson(row,MACHINE);
        assertEquals(ContinuityState.Status.AWAITING_INITIAL_ENTRY,reopened.status());
        assertTrue(reopened.initializedOrigin().isEmpty());assertEquals(0,reopened.settledCycles());
        assertThrows(IllegalArgumentException.class,reopened::origin);assertThrows(IllegalArgumentException.class,reopened::settledDateRaw);
        assertTrue(reopened.pendingCycle() instanceof ContinuityState.NullValue);
        assertArrayEquals(ContinuityJson.canonical(row),reopened.canonicalBytes());
        assertEquals("retained-original-unknown",reopened.toJson().get("unknown_actions").get(0).textValue());
        assertFalse(reopened.toJson().has("game_binding"));
    }
    @Test void ordinaryRepairAttachAndCreditCannotCreateAnObservedOriginBeforeRealEntry()throws Exception {
        var state=initial();
        for(String kind:List.of("repair_required","attach_verified","settled_batch","automatic_recovery")) {
            var details=StrictJson.object();details.put("evidence_id","not-an-entry");details.put("source","software-contract-only");
            assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(state,
                    new WriterContracts.Request(kind,ContinuityJson.canonical(details),List.of())));
        }
        var invalid=state.toJson();invalid.put("last_settled_date_raw",0);
        assertThrows(IllegalArgumentException.class,()->ContinuityState.fromJson(invalid,MACHINE));
        var inventedGame=state.toJson();inventedGame.putObject("game_binding").put("pid",1).put("creation_filetime","1");
        assertThrows(IllegalArgumentException.class,()->ContinuityState.fromJson(inventedGame,MACHINE));
    }
}
