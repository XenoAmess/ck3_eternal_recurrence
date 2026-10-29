package org.xar.ck3.control.wave3.planning.military;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationCodec;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationPlanner;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteAudit.*;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry.*;
import org.xar.ck3.control.wave3.planning.military.OrdinaryMilitaryConsumer.*;

class OrdinaryMilitaryConsumerTest {
    private static final String SHA = "a".repeat(64);
    private static final SourceBoundContactIndex.Current CURRENT = new SourceBoundContactIndex.Current(
            new SourceBoundContactIndex.SourceIdentity("fixture-machine", "1.20.0.4", SHA, SHA, SHA),
            new ProjectedContactPolicy.Snapshot(new ProjectedContactPolicy.Capture("s", BigInteger.valueOf(7), BigInteger.valueOf(11), BigInteger.ONE, "e"), 100),
            new SourceBoundContactIndex.HistoryIdentity("restored-e", BigInteger.ZERO, BigInteger.TEN), SourceBoundContactIndex.Invalidation.NONE);
    private static final HostileScope HOSTILES = new HostileScope(List.of(9), List.of(), true, false);

    @Test void geometricallySafeRouteStillRequiresIndependentNativeHorizonBeforeEndpointContact() {
        var input = input(List.of(3), List.of(List.of(1, 2, 3)), HOSTILES, List.of(), List.of());
        ReadRequired result = assertInstanceOf(ReadRequired.class, OrdinaryMilitaryConsumer.plan(input));
        assertEquals(ReadKind.EXACT_ONE_DAY_ROUTE_CONTACT, result.kind());
        assertEquals("query-route-contact-horizon-v1-4-to-3-h-1-9", result.requiredStep());
        assertFalse(result.actionAuthorized()); assertFalse(result.authorizesCommandReplay());
        roundtrip(result);
    }
    @Test void freeHorizonNeverSubstitutesForProjectedEndpointInput() {
        var input = input(List.of(3), List.of(List.of(1, 2, 3)), HOSTILES, List.of(horizon(3, List.of(1, 2, 3), true)), List.of());
        var result = assertInstanceOf(ReadRequired.class, OrdinaryMilitaryConsumer.plan(input));
        assertEquals(ReadKind.PROJECTED_ENDPOINT_CONTACT, result.kind());
        assertEquals("query-projected-contact-scope-v1-4-to-3-from-2", result.requiredStep());
        assertEquals(Status.SAFE_ONE_DAY_CONTACT_HORIZON, result.audit().status()); roundtrip(result);
    }
    @Test void nativeVetoFallsThroughEveryOriginalRankAndPreservesProjectedGeometry() {
        var input = input(List.of(3, 5, 7), List.of(List.of(1, 3), List.of(1, 5), List.of(1, 7)), HOSTILES,
                List.of(horizon(3, List.of(3), false), horizon(5, List.of(5), false), horizon(7, List.of(7), true)), List.of(contact(7, 1)));
        var result = assertInstanceOf(PlanningContinuation.class, OrdinaryMilitaryConsumer.plan(input));
        assertEquals(2, result.objectiveRank()); assertEquals(2, result.routeRejections().size());
        assertInstanceOf(IndexedContactIngress.NoContact.class, result.endpointContact());
        assertFalse(result.actualArrivalObserved()); assertFalse(result.battleWinProbabilityKnown()); roundtrip(result);
    }
    @Test void failedDestinationBecomesBlockedForLaterDuplicateOccurrenceWithoutDroppingItsRank() {
        var result = assertInstanceOf(PlanningContinuation.class, OrdinaryMilitaryConsumer.plan(input(List.of(3, 3, 5), List.of(List.of(1, 3), List.of(1, 3), List.of(1, 5)), HOSTILES,
                List.of(horizon(3, List.of(3), false), horizon(5, List.of(5), true)), List.of(contact(5, 1)))));
        assertEquals(2, result.objectiveRank()); assertEquals(1, result.routeRejections().size());
        assertTrue(result.previewRejections().stream().anyMatch(value -> value.targetProvinceId() == 3 && value.reason() == RouteReevaluationPlanner.RejectionReason.BLOCKED));
        roundtrip(result);
    }
    @Test void expiredHorizonAndChangedCaptureRequireFreshRead() {
        var old = new SourceBoundContactIndex.Current(CURRENT.source(), new ProjectedContactPolicy.Snapshot(CURRENT.snapshot().capture(), 99), CURRENT.history(), CURRENT.invalidation());
        var stale = new ReturnedHorizon(new Horizon(old, 4, 1, 3, List.of(9), List.of(3), true));
        var result = assertInstanceOf(ReadRequired.class, OrdinaryMilitaryConsumer.plan(input(List.of(3), List.of(List.of(1, 3)), HOSTILES, List.of(stale), List.of(contact(3, 1)))));
        assertEquals(ReadKind.EXACT_ONE_DAY_ROUTE_CONTACT, result.kind());
    }
    @Test void sourceUnknownCannotBecomeKnownFromValidBodyAndFullStrategyBoundarySurvives() {
        var known = input(List.of(3), List.of(List.of(1, 3)), HOSTILES, List.of(horizon(3, List.of(3), true)), List.of(contact(3, 1)));
        var input = new Input(known.route(), new SourceBoundContactIndex.Unknown("no qualified native provider"), known.effectiveContactRows(), known.ownerCharacterId(), known.hostileScope(), known.effectiveHorizonHistory(), known.rollbackMemory());
        var result = assertInstanceOf(Unavailable.class, OrdinaryMilitaryConsumer.plan(input)); assertEquals(Gap.CURRENT_SOURCE_UNAVAILABLE, result.gap()); roundtrip(result);
    }
    @Test void unsafeRouteNoSupportedNativeScopeFallsThroughToExistingRallyBoundary() {
        HostileScope unsupported = new HostileScope(List.of(9), List.of(new Enemy(9, Optional.of(3), Optional.empty(), List.of(), TacticalState.OTHER)), false, false);
        var result = assertInstanceOf(RouteBoundary.class, OrdinaryMilitaryConsumer.plan(input(List.of(3), List.of(List.of(1, 3)), unsupported, List.of(), List.of())));
        assertInstanceOf(RouteReevaluationPlanner.Exhausted.class, result.boundary()); assertEquals(1, result.routeRejections().size()); roundtrip(result);
    }
    @Test void oneDayFreeCannotOverrideOperationalOvermatchWithEnemyCurrentlyOnExactRoute() {
        var hostile = new HostileScope(List.of(9), List.of(new Enemy(9, Optional.of(3), Optional.empty(), List.of(), TacticalState.OTHER)), true, true);
        var result = assertInstanceOf(RouteBoundary.class, OrdinaryMilitaryConsumer.plan(input(List.of(3), List.of(List.of(1, 3)), hostile,
                List.of(horizon(3, List.of(3), true)), List.of(contact(3, 1)))));
        assertEquals(HorizonDecision.FREE_REJECTED_OPERATIONAL_OVERMATCH, result.routeRejections().getFirst().audit().horizonDecision());
        assertFalse(result.actionAuthorized()); roundtrip(result);
    }
    @Test void rollbackMemoryRejectsMatchingRouteButNotOtherEpisode() {
        var base = input(List.of(3), List.of(List.of(1, 3)), new HostileScope(List.of(), List.of(), false, false), List.of(), List.of(contact(3, 1)));
        var blocked = new Input(base.route(), base.origin(), base.effectiveContactRows(), base.ownerCharacterId(), base.hostileScope(), base.effectiveHorizonHistory(), List.of(new Rollback(4, 1, 3, List.of(1, 3), Optional.of("e"))));
        assertInstanceOf(RouteBoundary.class, OrdinaryMilitaryConsumer.plan(blocked));
        var foreign = new Input(base.route(), base.origin(), base.effectiveContactRows(), base.ownerCharacterId(), base.hostileScope(), base.effectiveHorizonHistory(), List.of(new Rollback(4, 1, 3, List.of(1, 3), Optional.of("other"))));
        assertInstanceOf(PlanningContinuation.class, OrdinaryMilitaryConsumer.plan(foreign));
    }
    @Test void mergeBarrierCannotReuseOldHorizonAndCurrentFailureDoesNotHideOlderValidReturn() {
        var good = horizon(3, List.of(3), true);
        assertInstanceOf(MissingHorizon.class, MilitaryRouteAudit.freshHorizon(List.of(good, new MergeBarrier(4, 8)), CURRENT, 4, 1, 3, List.of(9), List.of(3)));
        var failed = new FailedHorizon(4, 3, List.of(9), Optional.of(CURRENT), "native_complete_contact_route_unavailable");
        assertInstanceOf(FoundHorizon.class, MilitaryRouteAudit.freshHorizon(List.of(good, failed), CURRENT, 4, 1, 3, List.of(9), List.of(3)));
        assertInstanceOf(UnavailableHorizon.class, MilitaryRouteAudit.freshHorizon(List.of(failed), CURRENT, 4, 1, 3, List.of(9), List.of(3)));
    }
    @Test void geometricConflictOrderAndReverseEdgeLastOccurrenceMatchExistingAlgorithm() {
        var audit = MilitaryRouteAudit.geometry(List.of(1, 2, 3), 1, 3,
                List.of(new Enemy(9, Optional.of(2), Optional.of(3), List.of(2, 3, 2, 3, 2), TacticalState.OTHER)));
        assertEquals(ConflictKind.ENEMY_CURRENT_ON_ROUTE, audit.conflicts().getFirst().kind());
        assertEquals(ConflictKind.ENEMY_TARGET_ON_ROUTE, audit.conflicts().get(1).kind());
        assertTrue(audit.conflicts().stream().anyMatch(value -> value.kind() == ConflictKind.OPPOSITE_EDGE_INTERSECTION && value.enemyHop().orElseThrow() == 3));
    }
    @Test void malformedRouteIsUnavailableAndRetreatBooleanPrecedesCombatName() {
        var bad = StrictJson.parse(MilitaryRouteGeometryCodec.project(bytes("{\"route_value\":[1,true],\"origin_province_id\":1,\"target_province_id\":3,\"enemies\":[]}")));
        assertEquals("route_not_observable", bad.get("reason").textValue());
        var safe = StrictJson.parse(MilitaryRouteGeometryCodec.project(bytes("{\"route_value\":[1,3],\"origin_province_id\":1,\"target_province_id\":3,\"enemies\":[{\"army_id\":9,\"current_province_id\":3,\"retreating\":true,\"in_combat\":true,\"army_state\":\"embarked\"}]}")));
        assertEquals("safe", safe.get("status").textValue());
        assertThrows(IllegalArgumentException.class, () -> MilitaryRouteGeometryCodec.project(bytes("{\"route_value\":[1,3],\"origin_province_id\":true,\"target_province_id\":3,\"enemies\":[]}")));
    }
    @Test void receiptRejectsWrongFieldsWrongTypeAndForgedAuthority() {
        var result = OrdinaryMilitaryConsumer.plan(input(List.of(3), List.of(List.of(1, 3)), HOSTILES, List.of(), List.of()));
        ObjectNode row = (ObjectNode) StrictJson.parse(OrdinaryMilitaryResultCodec.encode(result)); row.put("action_authorized", true);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryMilitaryResultCodec.decode(StrictJson.canonical(row)));
        row.put("action_authorized", false); row.put("objective_rank", 0.0);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryMilitaryResultCodec.decode(StrictJson.canonical(row)));
        row.put("objective_rank", 0); row.put("extra", "unsupported");
        assertThrows(IllegalArgumentException.class, () -> OrdinaryMilitaryResultCodec.decode(StrictJson.canonical(row)));
    }

    @Test void actualPreviewOpaqueDecimalsSurviveContinuationPersistence() {
        var base = input(List.of(3), List.of(List.of(1, 3)), HOSTILES, List.of(), List.of());
        var lookup = StrictJson.parse(base.route().lookupPacket());
        ((ObjectNode) lookup.get("commands").get(0).get("result").get("route_preview")).put("opaque_native_weight", 1.25);
        var request = new RouteReevaluationCodec.Request(org.xar.ck3.control.wave3.military.routereroute.RoutePreviewConsumerCodec.encodeEnvelope(lookup), base.route().context(), base.route().orderedObjectives(), base.route().availableSteps());
        var result = OrdinaryMilitaryConsumer.plan(new Input(request, base.origin(), base.effectiveContactRows(), base.ownerCharacterId(), base.hostileScope(), base.effectiveHorizonHistory(), base.rollbackMemory()));
        var stored = StrictJson.parse(OrdinaryMilitaryResultCodec.encode(result));
        assertEquals(1.25, stored.get("preview").get("opaque_native_weight").doubleValue()); roundtrip(result);
    }

    @Test void mixedValidEndpointReceiptCannotCrossPreviewTargetOrIncomingEdge() {
        var unsupported = new HostileScope(List.of(), List.of(), false, false);
        var first = OrdinaryMilitaryConsumer.plan(input(List.of(3), List.of(List.of(1, 2, 3)), unsupported, List.of(), List.of(contact(3, 2))));
        var other = OrdinaryMilitaryConsumer.plan(input(List.of(5), List.of(List.of(1, 5)), unsupported, List.of(), List.of(contact(5, 1))));
        ObjectNode encoded = (ObjectNode) StrictJson.parse(OrdinaryMilitaryResultCodec.encode(first));
        encoded.set("endpoint_contact", StrictJson.parse(OrdinaryMilitaryResultCodec.encode(other)).get("endpoint_contact"));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryMilitaryResultCodec.decode(org.xar.ck3.control.wave3.military.routereroute.RoutePreviewConsumerCodec.encodeEnvelope(encoded)));
    }

    @Test void actualCompositionRetainsAttackerEntryAndDefenderConstructorZero() {
        var unsupported = new HostileScope(List.of(), List.of(), false, false);
        for (boolean defender : List.of(false, true)) {
            var scope = new ProjectedContactPolicy.Scope(BigInteger.valueOf(11), 100, 4, 40, 20, 1, 3, 2, List.of(9), List.of(),
                    ProjectedContactPolicy.Transition.CREATE_NEW, null, null, defender ? ProjectedContactPolicy.Side.DEFENDER : ProjectedContactPolicy.Side.ATTACKER,
                    true, defender, 3, defender ? List.of(9) : List.of(4), defender ? List.of(4) : List.of(9));
            var captured = new ProjectedContactPolicy.CapturedRow(new ProjectedContactPolicy.QueryKey(4, 3, 2), CURRENT.snapshot().capture(), scope);
            var result = assertInstanceOf(PlanningContinuation.class, OrdinaryMilitaryConsumer.plan(input(List.of(3), List.of(List.of(1, 2, 3)), unsupported, List.of(), List.of(captured))));
            var encounter = assertInstanceOf(IndexedContactIngress.NewEncounter.class, result.endpointContact());
            assertEquals(3, encounter.selection().projection().incomingAdjacencyKindRaw());
            if (defender) { assertNull(encounter.attackerEntryProvinceId()); assertEquals(0, encounter.constructorAdjacencyKindRaw()); }
            else { assertEquals(2, encounter.attackerEntryProvinceId()); assertNull(encounter.constructorAdjacencyKindRaw()); }
            roundtrip(result);
        }
    }
    @Test void actualCompositionRetainsExistingCombatStoredArrayIndexAndSides() {
        var scope = new ProjectedContactPolicy.Scope(BigInteger.valueOf(11), 100, 4, 40, 20, 1, 3, 2, List.of(9), List.of(20, 10),
                ProjectedContactPolicy.Transition.JOIN_EXISTING, 10, 1, ProjectedContactPolicy.Side.ATTACKER, false, null, 3, List.of(8, 4), List.of(9));
        var captured = new ProjectedContactPolicy.CapturedRow(new ProjectedContactPolicy.QueryKey(4, 3, 2), CURRENT.snapshot().capture(), scope);
        var result = assertInstanceOf(PlanningContinuation.class, OrdinaryMilitaryConsumer.plan(input(List.of(3), List.of(List.of(1, 2, 3)), new HostileScope(List.of(), List.of(), false, false), List.of(), List.of(captured))));
        var resume = assertInstanceOf(IndexedContactIngress.ResumeExisting.class, result.endpointContact());
        assertEquals(10, resume.selectedCombatId()); assertEquals(1, resume.selectedCombatArrayIndex());
        assertEquals(List.of(8, 4), resume.selection().projection().attackerArmyIds()); roundtrip(result);
    }

    private static Input input(List<Integer> targets, List<List<Integer>> routes, HostileScope hostile, List<HorizonEntry> history, List<ProjectedContactPolicy.QueryRow> contact) {
        var lookup = StrictJson.object(); var commands = lookup.putArray("commands");
        for (int i = 0; i < targets.size(); i++) {
            var row = commands.addObject(); row.put("command", "preview-move-army-4-to-" + targets.get(i)); row.put("ok", true); var result = row.putObject("result");
            result.put("queried_snapshot_id", "s"); result.put("queried_revision", 7); result.put("queried_native_revision", 11); result.put("queried_connection_generation", 1); result.put("queried_episode_run_id", "e");
            var preview = result.putObject("route_preview"); preview.put("status", "available"); preview.put("army_id", 4); preview.put("origin_province_id", 1); preview.put("target_province_id", targets.get(i)); preview.put("previewed_date_raw", 100);
            var route = preview.putArray("route_province_ids"); routes.get(i).forEach(route::add);
        }
        var snapshot = lookup.putObject("snapshot"); snapshot.put("snapshot_id", "s"); snapshot.put("revision", 7); snapshot.put("native_revision", 11); snapshot.put("episode_run_id", "e"); snapshot.putObject("diagnostics").put("connection_generation", 1);
        lookup.put("army_id", 4); lookup.put("origin_province_id", 1); lookup.put("target_province_id", targets.getFirst()); lookup.put("date_raw", 100);
        List<RouteReevaluationPlanner.Objective> goals = new ArrayList<>(); for (int target : targets) goals.add(new RouteReevaluationPlanner.Objective(target, RouteReevaluationPlanner.CandidateSource.WAR_OBJECTIVE_PROVINCE, false));
        return new Input(new RouteReevaluationCodec.Request(StrictJson.canonical(lookup), new RouteReevaluationPlanner.Context(false, false, false, false), goals, List.of()), CURRENT, contact, Optional.of(20), hostile, history, List.of());
    }
    private static HorizonEntry horizon(int target, List<Integer> route, boolean free) { return new ReturnedHorizon(new Horizon(CURRENT, 4, 1, target, List.of(9), route, free)); }
    private static ProjectedContactPolicy.QueryRow contact(int target, int incoming) {
        var scope = new ProjectedContactPolicy.Scope(BigInteger.valueOf(11), 100, 4, 40, 20, 1, target, incoming, List.of(), List.of(),
                ProjectedContactPolicy.Transition.NONE, null, null, ProjectedContactPolicy.Side.NONE, false, null, 0, List.of(), List.of());
        return new ProjectedContactPolicy.CapturedRow(new ProjectedContactPolicy.QueryKey(4, target, incoming), CURRENT.snapshot().capture(), scope);
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static void roundtrip(Result result) {
        byte[] original = OrdinaryMilitaryResultCodec.encode(result);
        assertArrayEquals(original, OrdinaryMilitaryResultCodec.encode(OrdinaryMilitaryResultCodec.decode(original)));
    }
}
