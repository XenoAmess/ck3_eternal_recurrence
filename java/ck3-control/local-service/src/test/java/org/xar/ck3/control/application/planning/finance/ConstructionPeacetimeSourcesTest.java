package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly;

/** Software native-envelope -> production finalizer -> actual M5 construction source; no live/private Root qualification. */
final class ConstructionPeacetimeSourcesTest {
    @Test void actualCoveredNativeNoCandidateBecomesTheSameCompleteM5Source() {
        Obj actual = OrdinaryConstructionCollector.finalizePeacetime(input(true));
        var consumed = ConstructionPeacetimeSources.assembly(actual);
        assertEquals(PeacetimeAssembly.ConstructionStatus.NO_LEGAL_BUDGETED_BUILDING, consumed.status());
        assertEquals(actual, consumed.originalQuery());
        assertEquals(n(100), object(consumed.originalQuery().get("world"), "actual world").get("player_gold_raw"));
        assertEquals(n(2), consumed.originalQuery().get("proof_epoch"));
        assertFalse(consumed.originalQuery().members().containsKey("formal_action_ready"));
    }
    @Test void incompleteNativeCoverageAndMaterialOnlySourceCannotBecomeNoCandidate() {
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionCollector.finalizePeacetime(input(false)));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionCollector.finalizePeacetime(input(true).with("material_receipt", new Bool(true))));
        for (String status : List.of("source_red", "read_rejected", "material_source", "evidence_insufficient", "unavailable"))
            assertThrows(IllegalArgumentException.class, () -> ConstructionPeacetimeSources.assembly(obj("status", new Text(status))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionPeacetimeSources.assembly(obj()));
    }
    @Test void rawWrongTypeAndChangedNativeIdentityRemainRejectedBeforeAssembly() {
        Obj input = input(true);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionCollector.finalizePeacetime(input.with("expected_revision", new Bool(true))));
        Obj changed = object(input.get("ending_snapshot"), "actual end").with("episode_run_id", new Text("another-episode"));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionCollector.finalizePeacetime(input.with("ending_snapshot", changed)));
        Obj envelope = object(input.get("native_envelope"), "actual envelope");
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionCollector.finalizePeacetime(input.with("native_envelope", envelope.with("request_id", new Text("other-query")))));
    }
    @Test void processReleaseUsesTheObservedBridgeIdentityWithoutSubstitutingTheGamePid() {
        Obj snapshot = object(input(true).get("starting_snapshot"), "actual snapshot");
        Obj applied = ConstructionCoordinatorPendingTest.original().with("status", new Text("applied")).with("postcondition_verified", new Bool(true))
                .with("completion_status", new Text("in_progress")).with("post_bridge_pid", n(42)).with("post_bridge_creation_date", new Text("actual-fixture-process"))
                .with("post_native_revision", n(2)).with("post_date_raw", n(99));
        Obj full = obj("schema", new Text(ConstructionLedgerCodec.SCHEMA), "pending", Nil.INSTANCE, "applied", applied, "applied_prior", new Arr(List.of()));
        var ledger = ConstructionLedgerCodec.decodeLedger(encode(full));
        var request = request(snapshot);
        var projected = ConstructionPeacetimeSources.project(request, ledger);
        var process = assertInstanceOf(org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.ObservedIdentity.class, projected.release().processObservation());
        assertEquals(BigInteger.valueOf(42), process.identity().pid());
        assertNotEquals(BigInteger.valueOf(request.before().game().pid()), process.identity().pid());
        assertFalse(org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.assess(projected.release().frame(), projected.release().applied(), projected.release().processObservation()).blocksCandidate());
        Obj diagnostic = object(snapshot.get("diagnostics"), "actual process source");
        assertThrows(IllegalArgumentException.class, () -> ConstructionPeacetimeSources.project(request(snapshot.with("diagnostics", diagnostic.with("bridge_pid", new Bool(true)))), ledger));
        var missing = new java.util.LinkedHashMap<String,Value>(diagnostic.members()); missing.remove("bridge_creation_date");
        var unavailable = ConstructionPeacetimeSources.project(request(snapshot.with("diagnostics", new Obj(missing))), ledger);
        assertInstanceOf(org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.IdentityUnavailable.class, unavailable.release().processObservation());
    }
    private static org.xar.ck3.control.application.planning.PlanningRequest request(Obj snapshot) {
        var source = new org.xar.ck3.control.g2.common.G2Source("construction-fixture-machine", "2026-10-24T00:00:00Z", "1.20.0.4",
                new org.xar.ck3.control.contracts.ExactRef("D:/fixture/source.java", 1, "a".repeat(64)));
        var game = new org.xar.ck3.control.contracts.GameGeneration(99, new org.xar.ck3.control.contracts.PythonOnlyUInt64(new BigInteger("133000000000000000")));
        var frame = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(), game,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                        new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.valueOf(3), BigInteger.valueOf(100)),
                        "native:3", BigInteger.valueOf(3), "episode"), 1);
        var observation = new org.xar.ck3.control.application.planning.PlanningObservation(snapshot, List.of(), java.util.Set.of(), java.util.Set.of(),
                java.util.Optional.empty(), List.of(), java.util.Optional.empty(), java.util.Optional.empty(), false);
        return new org.xar.ck3.control.application.planning.PlanningRequest(frame, source, "actual-session", java.time.Instant.parse("2026-10-24T00:00:30Z"), observation);
    }
    private static Obj input(boolean coverage) {
        Obj snapshot = obj("snapshot_id", new Text("native:3"), "revision", n(3), "native_revision", n(3), "date_raw", n(100), "episode_run_id", new Text("episode"),
                "paused", new Bool(true), "map_ready", new Bool(true), "active_event", Nil.INSTANCE, "pending_character_interaction", Nil.INSTANCE,
                "played_character", obj("character_id", n(1), "alive", new Bool(true)), "active_wars", new Arr(List.of()), "player_armies", new Arr(List.of()),
                "diagnostics", obj("bridge_pid", n(42), "bridge_creation_date", new Text("actual-fixture-process"), "hello",
                        obj("expected_ck3_version", new Text("1.20.0.4"), "expected_ck3_sha256", new Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"))));
        Obj world = obj("status", new Text("source_available"), "snapshot_revision", n(3), "date_raw", n(100), "player_character_id", n(1),
                "native_final_legality_evaluated", new Bool(true), "native_cost_evaluated", new Bool(true), "player_gold_raw", n(100),
                "active_constructions", new Arr(List.of()), "completed_buildings_observed", new Bool(true), "completed_buildings", new Arr(List.of()),
                "positive_income_coverage_complete", new Bool(coverage), "legal_samples", new Arr(List.of()));
        Obj probe = obj("advertised", new Bool(false), "snapshot_revision", n(3), "date_raw", n(100), "proof_epoch", n(2), "player_world_building_sources", world);
        Obj envelope = obj("type", new Text("command_result"), "protocol_version", n(1), "request_id", new Text("actual-fixture-query"), "ok", new Bool(true),
                "result", obj("step", new Text("g2_player_construction_view_probe_v1"), "accepted", new Bool(true), "private_probe", probe));
        return obj("schema", new Text("xar.construction-query-observation-input.v1"), "starting_snapshot", snapshot, "ending_snapshot", snapshot,
                "native_envelope", envelope, "expected_revision", n(3), "native_query_request_id", new Text("actual-fixture-query"),
                "material_receipt", new Bool(false), "wartime_observation", new Bool(false));
    }
    private static IntegerValue n(long number) { return new IntegerValue(BigInteger.valueOf(number)); }
}
