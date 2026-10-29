package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Opportunity;

/** New boundary regressions; these tests are not claimed as historical goldens or native qualification. */
final class OrdinaryConstructionBoundaryTest {
    @Test void importedExplicitClearPreservesOriginalMissingVersusEmptyHistory() {
        Obj old = json("{\"schema\":\"xar.ck3.construction_formal_pending_v1\",\"pending\":null,\"applied\":null}");
        var ledger = ConstructionLedgerCodec.decodeLedger(encode(old));
        assertTrue(ledger.pending().isEmpty()); assertTrue(ledger.applied().isEmpty()); assertTrue(ledger.prior().isEmpty());
        assertNull(ledger.original().get("applied_prior"));
        assertEquals(old, parse(encode(ledger.original())));
        Obj empty = old.with("applied_prior", new Arr(List.of()));
        assertNotEquals(old, ConstructionLedgerCodec.decodeLedger(encode(empty)).original());
        assertThrows(IllegalArgumentException.class, () -> ConstructionLedgerCodec.decodeLedger(encode(old.with("applied_prior", Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionLedgerCodec.decodeLedger(bytes("{\"schema\":\"xar.ck3.construction_formal_pending_v1\",\"applied\":null}")));
    }
    @Test void fullPendingTupleRejectsBooleanFloatingAndStringIntegerAliases() {
        Obj intent = pending(); Obj body = body(intent);
        assertEquals(BigInteger.valueOf(11), ConstructionLedgerCodec.decodeLedger(encode(body)).pending().orElseThrow().identity().candidate().building());
        for (Value wrong : List.of(new Bool(true), new DecimalValue("11.0"), new Text("11"))) {
            Obj candidate = object(intent.get("candidate"), "candidate").with("building_type_id", wrong);
            assertThrows(IllegalArgumentException.class, () -> ConstructionLedgerCodec.decodeLedger(encode(body(intent.with("candidate", candidate)))));
        }
        Obj over = object(intent.get("candidate"), "candidate").with("stock_gold_cost_raw", new IntegerValue(BigInteger.valueOf(101)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionLedgerCodec.decodeLedger(encode(body(intent.with("candidate", over)))));
    }
    @Test void freshNativeRequestAndAdvancingProofDoNotMasqueradeAsChangedConstruction() {
        Obj first = quote(); Obj fresh = first.with("native_query_request_id", new Text("actual-fresh-read"))
                .with("proof_epoch", new IntegerValue(BigInteger.valueOf(12)));
        assertTrue(OrdinaryConstructionPolicy.sameQuote(encode(first), encode(fresh)));
        Obj changed = fresh.with("candidate", object(fresh.get("candidate"), "candidate").with("building_type_id", new IntegerValue(BigInteger.valueOf(12))));
        assertFalse(OrdinaryConstructionPolicy.sameQuote(encode(first), encode(changed)));
        Obj unexplainedWorld = fresh.with("world", json("{\"unused\":true}"));
        assertFalse(OrdinaryConstructionPolicy.sameQuote(encode(first), encode(unexplainedWorld)));
        Obj regressed = fresh.with("proof_epoch", new IntegerValue(BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionPolicy.sameQuote(encode(first), encode(regressed)));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionPolicy.sameQuote(encode(first), encode(fresh.with("proof_epoch", new Bool(true)))));
    }
    @Test void onlyOriginalOrdinaryAdvancePrewarAndQualifiedQuietRouteAdmitNewSpend() {
        assertEquals(Opportunity.ORDINARY_ADVANCE, OrdinaryConstructionPolicy.selection(draft("current_life_loop", "life-advance", OrdinaryPolicy.Kind.ORDINARY)).opportunity());
        assertEquals(Opportunity.PREWAR_ARBITRATION, OrdinaryConstructionPolicy.selection(draft("native_entry", "declare-war-2-0--1", OrdinaryPolicy.Kind.ORDINARY)).opportunity());
        String route = "advance-route-contact-horizon-v1-0-to-2-h-2-1-3";
        assertEquals(Opportunity.QUIET_ROUTE_ADVANCE, OrdinaryConstructionPolicy.selection(draft("native_war_route_contact_horizon_progress", route, OrdinaryPolicy.Kind.ORDINARY)).opportunity());
        assertEquals(Opportunity.CONTINUE_SELECTED_WORK, OrdinaryConstructionPolicy.selection(draft("native_march", route, OrdinaryPolicy.Kind.ORDINARY)).opportunity());
        assertEquals(Opportunity.CONTINUE_SELECTED_WORK, OrdinaryConstructionPolicy.selection(draft("current_event", "life-advance", OrdinaryPolicy.Kind.FOREGROUND)).opportunity());
    }
    @Test void missingOptionalConstructionCarriesZeroFundingAndContinuesWar() {
        OrdinaryPolicy.Defer deferred = OrdinaryConstructionPolicy.deferred("actual mercenary market is unavailable");
        assertEquals(new IntegerValue(BigInteger.ZERO), deferred.evidence().get("future_funding_credited_raw"));
        assertEquals(new Bool(true), deferred.evidence().get("continue_ordinary_war"));
        assertEquals(new Bool(false), deferred.evidence().get("business_submission"));
    }
    private static OrdinaryPolicy.Draft draft(String phase, String step, OrdinaryPolicy.Kind kind) {
        return new OrdinaryPolicy.Draft("original-planner", phase, "original reason", kind, Optional.empty(),
                OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), json("{}").with("selected_step", new Text(step)));
    }
    private static Obj pending() {
        return json("{\"action_request_id\":\"actual-request\",\"episode_run_id\":\"episode\",\"actor_character_id\":1,\"pre_native_revision\":2,\"pre_date_raw\":100,\"pre_proof_epoch\":3,\"source_bridge_pid\":42,\"source_bridge_creation_date\":\"legacy-creation-verbatim\",\"candidate\":{\"barony_title_id\":2,\"province_id\":3,\"building_type_id\":11,\"slot_index\":0,\"gold_before_raw\":100,\"stock_gold_cost_raw\":25}}");
    }
    private static Obj body(Obj pending) { return json("{\"schema\":\"xar.ck3.construction_formal_pending_v1\",\"pending\":null,\"applied\":null,\"applied_prior\":[]}").with("pending", pending); }
    private static Obj quote() { return json("{\"status\":\"selected\",\"native_query_request_id\":\"planned-read\",\"proof_epoch\":11,\"source_frame\":{\"actor_character_id\":1},\"candidate\":{\"barony_title_id\":2,\"province_id\":3,\"building_type_id\":11,\"slot_index\":0},\"world\":{}}"); }
    private static Obj json(String value) { return object(parse(bytes(value)), "fixture object"); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
