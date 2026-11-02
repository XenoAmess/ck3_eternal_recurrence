package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** New bounded pure Council witnesses. No cadence, source authority, Native, Game or HTTP is exercised. */
final class CouncilPure324Test {
    private static final CouncilSelection.Position ROLE = CouncilSelection.Position.STEWARD;
    private static Obj obj() { return new Obj(Map.of()); }
    private static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static CouncilSelection.Candidate candidate(String id, int skill, int ordinal, boolean blocked) {
        return new CouncilSelection.Candidate(new BigInteger(id), BigInteger.valueOf(ordinal), skill,
                blocked ? List.of("native_blocker") : List.of(), obj().with("marker", new Text(id + ":" + ordinal)));
    }
    private static CouncilSelection.Query query(boolean available, List<CouncilSelection.Candidate> candidates, Integer incumbent) {
        return new CouncilSelection.Query(ROLE, available, incumbent == null ? Optional.empty() : Optional.of(BigInteger.valueOf(50)),
                Optional.ofNullable(incumbent), candidates, obj().with("unknown", new Text("retained")));
    }
    private static ProposalLifecycle.ObservationIdentity observed() {
        return new ProposalLifecycle.ObservationIdentity("council324-software",
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(100), BigInteger.valueOf(5), BigInteger.valueOf(53144328)),
                        "snapshot-3", BigInteger.valueOf(3), "episode-1"), 1);
    }
    private static Obj outer(String status) {
        return obj().with("status", new Text(status)).with("queried_snapshot_id", new Text("snapshot-3"))
                .with("queried_revision", n(3)).with("queried_native_revision", n(5))
                .with("source_frame", obj().with("snapshot_id", new Text("snapshot-3")).with("revision", n(3))
                        .with("native_revision", n(5)).with("date_raw", n(53144328)).with("player_character_id", n(100)).with("paused", new Bool(true)));
    }
    private static Obj payload(boolean privateFrame) {
        var snapshot = obj().with("snapshot_id", new Text(privateFrame ? "native:5" : "snapshot-3"))
                .with("public_revision", n(privateFrame ? 5 : 3)).with("native_revision", n(5))
                .with("date_raw", n(53144328)).with("paused", new Bool(true));
        var position = obj().with("position_key", new Text(ROLE.key())).with("incumbent_character_id", Nil.INSTANCE)
                .with("incumbent_main_skill", Nil.INSTANCE).with("vacant", new Bool(true)).with("action_route", new Text("assign"));
        var candidate = obj().with("character_id", n(17)).with("native_collection_ordinal", n(7)).with("eligible", new Bool(true))
                .with("eligibility_reason", new Text("native_candidate_provider_accepted"))
                .with("main_skill", obj().with("key", new Text(ROLE.skill())).with("value", n(20))).with("action_route", new Text("assign"));
        Obj ready = obj();
        for (String key : List.of("identity_ready", "candidate_collection_ready", "incumbent_ready", "incumbent_main_skill_ready",
                "candidate_legality_ready", "main_skill_ready", "action_route_ready", "same_frame_ready", "ready")) ready = ready.with(key, new Bool(true));
        return obj().with("snapshot", snapshot).with("owner_character_id", n(100)).with("position", position)
                .with("candidate_collection_complete", new Bool(true)).with("candidates", new Arr(List.of(candidate))).with("readiness", ready);
    }
    private static Obj privateAvailable() {
        var gate = obj().with("character_id", n(17)).with("native_collection_ordinal", n(7)).with("final_gate_available", new Bool(true))
                .with("candidate_already_councillor", new Bool(false)).with("candidate_is_guest", new Bool(false))
                .with("pending_character_interaction", new Bool(false)).with("incumbent_fireability_evaluated", new Bool(false))
                .with("incumbent_can_be_fired", new Bool(false));
        return outer("available").with("council_composition_candidates", payload(true))
                .with("council_final_gates", obj().with("status", new Text("available")).with("candidate_count", n(1)).with("rows", new Arr(List.of(gate))))
                .with("unknown_business_fact", new Text("preserve"));
    }
    @Test void unavailableKeepsExactOriginalAndReason() {
        var q = query(false, List.of(candidate("1", Integer.MAX_VALUE, 0, false)), null);
        var out = CouncilSelection.choose(q);
        assertEquals(CouncilSelection.Outcome.QUERY_UNAVAILABLE, out.outcome()); assertTrue(out.selected().isEmpty());
        assertSame(q, out.original()); assertEquals("private_query_unavailable", out.reason());
    }
    @Test void emptyAndBlockedKeepNoEligibleCandidate() {
        for (var candidates : List.of(List.<CouncilSelection.Candidate>of(), List.of(candidate("1", 999, 0, true)))) {
            var out = CouncilSelection.choose(query(true, candidates, null));
            assertEquals(CouncilSelection.Outcome.NO_CHANGE, out.outcome()); assertTrue(out.selected().isEmpty());
            assertEquals("no_eligible_candidates", out.reason());
        }
    }
    @Test void highestSkillThenLowestFullBigIntegerIdWins() {
        var lowId = candidate("4294967297", 25, 99, false);
        var highId = candidate("18446744073709551615", 25, 0, false);
        var blocked = candidate("1", 1000, 1, true);
        var out = CouncilSelection.choose(query(true, List.of(highId, blocked, candidate("0", 24, 0, false), lowId), null));
        assertSame(lowId, out.selected().orElseThrow()); assertEquals(CouncilSelection.Outcome.ASSIGN_REQUIRED, out.outcome());
        assertEquals("native_final_gate_and_observed_skill", out.reason());
    }
    @Test void equalComparatorValuesRetainFirstObjectNotOrdinalOrder() {
        var first = candidate("17", 20, 99, false); var second = candidate("17", 20, 0, false);
        assertSame(first, CouncilSelection.choose(query(true, List.of(first, second), null)).selected().orElseThrow());
        assertSame(second, CouncilSelection.choose(query(true, List.of(second, first), null)).selected().orElseThrow());
    }
    @Test void signedExtremesAndIncumbentStrictImprovementStayExact() {
        var low = candidate("1", Integer.MIN_VALUE, 0, false); var high = candidate("2", Integer.MAX_VALUE, 1, false);
        assertSame(high, CouncilSelection.choose(query(true, List.of(low, high), null)).selected().orElseThrow());
        var tied = CouncilSelection.choose(query(true, List.of(high), Integer.MAX_VALUE));
        assertEquals(CouncilSelection.Outcome.NO_CHANGE, tied.outcome()); assertSame(high, tied.selected().orElseThrow());
        assertEquals("incumbent_not_outperformed", tied.reason());
        assertEquals(CouncilSelection.Outcome.REPLACE_REQUIRED,
                CouncilSelection.choose(query(true, List.of(high), Integer.MAX_VALUE - 1)).outcome());
    }
    @Test void unavailableStillRequiresCompleteExactOuterFrame() {
        var original = outer("unavailable");
        assertFalse(CouncilSelection.decodeObserved(observed(), ROLE, original).available());
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decodeObserved(observed(), ROLE, original.with("queried_revision", n(99))));
        var frame = object(original.get("source_frame"), "frame");
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decodeObserved(observed(), ROLE,
                original.with("source_frame", frame.with("paused", new Bool(false)))));
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decodeObserved(observed(), ROLE,
                original.with("source_frame", frame.with("extra", new Bool(true)))));
    }
    @Test void availablePrivateStillChecksGatesAndRetainsUnknownFacts() {
        var original = privateAvailable(); var decoded = CouncilSelection.decodeObserved(observed(), ROLE, original);
        assertSame(original, decoded.original()); assertEquals(BigInteger.valueOf(17), CouncilSelection.choose(decoded).selected().orElseThrow().characterId());
        assertEquals(new Text("preserve"), decoded.original().get("unknown_business_fact"));
        var gates = object(original.get("council_final_gates"), "gates"); var rows = array(gates.get("rows"), "rows");
        var wrong = object(rows.getFirst(), "gate").with("native_collection_ordinal", n(8));
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decodeObserved(observed(), ROLE,
                original.with("council_final_gates", gates.with("rows", new Arr(List.of(wrong))))));
        var bad = original.with("queried_revision", n(99)).with("council_composition_candidates", obj());
        assertTrue(assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decodeObserved(observed(), ROLE, bad))
                .getMessage().contains("private Council outer query binding drift"));
    }
    @Test void publicCompositionRetainsOwnFrameWithoutPrivateEnvelope() {
        var original = payload(false); var decoded = CouncilSelection.decodeCompositionObserved(observed(), original);
        assertTrue(decoded.available()); assertSame(original, decoded.original()); assertTrue(decoded.incumbent().isEmpty());
        assertEquals(BigInteger.valueOf(17), CouncilSelection.choose(decoded).selected().orElseThrow().characterId());
    }
}
