package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import java.nio.charset.StandardCharsets;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class FamilyResultReducerTest {
    private static final BridgeIdentity BRIDGE = new BridgeIdentity(41, "20261023090000.000000+000");
    private static Obj json(String text) { return decode(text.getBytes(StandardCharsets.UTF_8)); }
    private static Obj pending() { return json("{\"episode_run_id\":\"ep\",\"heir_character_id\":11,\"candidate_character_id\":12,\"source_bridge_pid\":31,\"source_bridge_creation_date\":\"old\",\"pre_native_revision\":7,\"prior_rejected_candidate_ids\":[]}"); }
    private static Obj ledger(Obj pending) { return obj("pending", pending, "resolved", Nil.INSTANCE, "extension", t("retained")); }
    @Test void pendingReadRetainsProposalAndColdUnknown() {
        Obj p = pending(), result = json("{\"status\":\"pending\",\"post_native_revision\":8,\"outbound_pending_state\":null}");
        Obj next = FamilyResultReducer.reduce(Query.FAMILY_RESULT, ledger(p), obj("pending", p, "cold", new Bool(true)), result, BRIDGE, BigInteger.valueOf(100));
        Obj kept = object(next.get("pending")); assertEquals(p.get("candidate_character_id"), kept.get("candidate_character_id"));
        assertTrue(yes(kept.get("cold_absent_relation_unresolved"))); assertEquals(Nil.INSTANCE, next.get("resolved")); assertEquals(t("retained"), next.get("extension"));
    }
    @Test void unavailableCannotClearUnknownProposal() {
        Obj p = pending(); assertThrows(IllegalArgumentException.class, () -> FamilyResultReducer.reduce(Query.FAMILY_RESULT, ledger(p), obj("pending", p),
                json("{\"status\":\"unavailable\",\"post_native_revision\":8}"), BRIDGE, BigInteger.valueOf(100)));
    }
    @Test void refusalCreatesExactRetryHistoryWithoutMaterialCredit() {
        Obj p = pending(); Obj next = FamilyResultReducer.reduce(Query.FAMILY_RESULT, ledger(p), obj("pending", p),
                json("{\"status\":\"refused\",\"material_result\":false,\"post_native_revision\":8}"), BRIDGE, BigInteger.valueOf(100));
        assertEquals(Nil.INSTANCE, next.get("pending")); Obj resolved = object(next.get("resolved"));
        assertEquals(p, resolved.get("source_pending")); assertEquals(List.of(n(12)), array(resolved.get("rejected_candidate_ids"))); assertFalse(yes(resolved.get("material_result")));
    }
    @Test void materialStatusWithoutActualMaterialResultRejected() {
        Obj p = pending(); assertThrows(IllegalArgumentException.class, () -> FamilyResultReducer.reduce(Query.DEFAULT_RESULT, ledger(p), obj("pending", p),
                json("{\"status\":\"marriage\",\"material_result\":false,\"post_native_revision\":8}"), BRIDGE, BigInteger.valueOf(100)));
    }
    @Test void changedPendingPairRejectedBeforeReduction() {
        Obj p = pending(); assertThrows(IllegalArgumentException.class, () -> FamilyResultReducer.reduce(Query.MATRILINEAL_RESULT, ledger(p),
                obj("pending", p.with("candidate_character_id", n(13))), json("{\"status\":\"pending\",\"post_native_revision\":8}"), BRIDGE, BigInteger.valueOf(100)));
    }
    @Test void coldMarriageCannotRegressToBetrothal() {
        Obj p = pending(); Obj prior = obj("status", t("marriage"), "source_pending", p);
        Obj before = obj("pending", Nil.INSTANCE, "resolved", prior);
        assertThrows(IllegalArgumentException.class, () -> FamilyResultReducer.reduce(Query.DEFAULT_RESULT, before, obj("pending", p, "cold", new Bool(true)),
                json("{\"status\":\"betrothal\",\"material_result\":true,\"post_native_revision\":8}"), BRIDGE, BigInteger.valueOf(100)));
    }
    @Test void maturedColdBetrothalInvalidatesPriorAllianceObservation() {
        Obj p = pending(); Obj prior = obj("status", t("betrothal"), "source_pending", p, "alliance_result", obj("status", t("old")));
        Obj next = FamilyResultReducer.reduce(Query.FAMILY_RESULT, obj("pending", Nil.INSTANCE, "resolved", prior), obj("pending", p, "cold", new Bool(true)),
                json("{\"status\":\"marriage\",\"material_result\":true,\"post_native_revision\":8}"), BRIDGE, BigInteger.valueOf(100));
        Obj resolved = object(next.get("resolved")); assertNull(resolved.get("alliance_result")); assertEquals(t("betrothal_to_marriage"), resolved.get("cold_material_transition"));
    }
    @Test void booleanAndFloatingIdsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> positive(new Bool(true)));
        assertThrows(IllegalArgumentException.class, () -> positive(new DecimalValue("12.0")));
    }
}
