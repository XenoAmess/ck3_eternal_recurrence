package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.effects.NativeConstructionEffects.*;

final class NativeConstructionEffectsTest {
    private static final BigInteger DATE = BigInteger.valueOf(53144328), REV = BigInteger.valueOf(81);
    private static final Tuple TUPLE = new Tuple(4, 5, 6, 0);
    private static final Candidate CANDIDATE = new Candidate(TUPLE, BigInteger.valueOf(1000), BigInteger.valueOf(100), BigInteger.valueOf(7));
    private static World world(List<Active> active, List<Tuple> completed, long gold) {
        return new World(BigInteger.valueOf(8), REV, DATE, 9, BigInteger.valueOf(gold), active, completed, true);
    }
    @Test void materialRequiresExactRequestedTupleAndActorNotAnotherSelection() {
        assertEquals(Material.ACTIVE, verify(CANDIDATE, 9, DATE, REV, DATE, world(List.of(new Active(TUPLE, 9, true)), List.of(), 900)));
        assertEquals(Material.UNOBSERVED, verify(CANDIDATE, 9, DATE, REV, DATE, world(List.of(new Active(new Tuple(4,5,7,0),9,true)), List.of(), 900)));
        assertEquals(Material.UNOBSERVED, verify(CANDIDATE, 9, DATE, REV, DATE, world(List.of(new Active(TUPLE,10,true)), List.of(), 900)));
    }
    @Test void sameDateWalletAndIndependentProofRemainNecessary() {
        assertThrows(IllegalArgumentException.class, () -> verify(CANDIDATE, 9, DATE, REV, DATE, world(List.of(new Active(TUPLE,9,true)), List.of(), 1000)));
        var stale = new World(BigInteger.valueOf(7), REV, DATE, 9, BigInteger.valueOf(900), List.of(new Active(TUPLE,9,true)), List.of(), true);
        assertThrows(IllegalArgumentException.class, () -> verify(CANDIDATE, 9, DATE, REV, DATE, stale));
    }
    @Test void completedMaterialDoesNotSilentlyHideAnActiveConflict() {
        assertEquals(Material.COMPLETED, verify(CANDIDATE,9,DATE,REV,DATE,world(List.of(),List.of(TUPLE),900)));
        assertThrows(IllegalArgumentException.class, () -> verify(CANDIDATE,9,DATE,REV,DATE,world(List.of(new Active(TUPLE,9,true)),List.of(TUPLE),900)));
    }
    @Test void quotedCandidateRejectsBooleanFloatAndMissingFieldsAfterJsonRoundTrip() {
        String valid = "{\"candidate\":{\"barony_title_id\":4,\"province_id\":5,\"building_type_id\":6,\"slot_index\":0,\"gold_before_raw\":1000,\"stock_gold_cost_raw\":100},\"pre_proof_epoch\":7}";
        assertEquals(CANDIDATE, decode(valid));
        for (String wrong : List.of(valid.replace("\"province_id\":5", "\"province_id\":true"), valid.replace("\"slot_index\":0", "\"slot_index\":0.0"), valid.replace(",\"pre_proof_epoch\":7", "")))
            assertThrows(IllegalArgumentException.class, () -> decode(wrong));
        var parsed = OpportunityJson.parse(valid.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertEquals(CANDIDATE, Candidate.decode((OpportunityJson.Obj) OpportunityJson.parse(OpportunityJson.encode(parsed))));
    }
    private static Candidate decode(String value) { return Candidate.decode((OpportunityJson.Obj) OpportunityJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
}
