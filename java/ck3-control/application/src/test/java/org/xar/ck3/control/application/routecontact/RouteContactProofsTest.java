package org.xar.ck3.control.application.routecontact;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy;

/** Executes the original complete same-frame proof collector branches; no Game or transport mock grants live credit. */
final class RouteContactProofsTest {
    static final Owner OWNER = new Owner("xenoamess-full-tower-eb9d2c1186", new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(123456789))),
            "session-1", BigInteger.ONE, 123, "episode-1", 29829, 0);
    static Army army(int id, int province, Integer target, List<Integer> route) {
        return new Army(id, true, province, Optional.ofNullable(target), route, Optional.of(route.isEmpty() ? "regular" : "moving"), Optional.empty(), false, false);
    }
    static Frame frame(int revision, int date, List<Army> own, List<Army> enemies) {
        return new Frame(OWNER, "native-" + revision, BigInteger.valueOf(revision), BigInteger.valueOf(revision), date, true, true, 3, false, true,
                Nil.INSTANCE, Nil.INSTANCE, Nil.INSTANCE, List.of(1), own, enemies);
    }
    static Frame starting() { return frame(1, 100, List.of(army(0, 10, 20, List.of(20))), List.of(army(8, 99, null, List.of()))); }
    static RouteQuery query(Frame frame) {
        return new RouteQuery("query-route-contact-horizon-v1-0-to-20-h-1-8", true, frame.owner(), frame.snapshotId(), frame.revision(), frame.nativeRevision(), frame.dateRaw(),
                0, 20, List.of(8), new RouteWindowPolicy.Route(0, 10, List.of(20), List.of(200)),
                List.of(new RouteWindowPolicy.Route(8, 99, List.of(), List.of())), 10, List.of(99), List.of());
    }
    @Test void slotZeroSubjectAndFullMaximumPublicIdAreLegal() {
        assertEquals(0, RouteContactSteps.parse("advance-route-contact-horizon-v1-0-to-20-h-1-2147483647").subjectId());
        assertThrows(IllegalArgumentException.class, () -> RouteContactSteps.parse("advance-route-contact-horizon-v1-00-to-20-h-1-8"));
    }
    @Test void malformedScopeDoesNotBecomeAnotherNativeOperation() {
        for (String bad : List.of("advance-route-contact-horizon-v1-0-to-20-h-2-8", "advance-route-contact-window-v1-0-to-20-days-1-h-1-8",
                "advance-route-contact-horizon-v1-0-to-20-h-2-8-8", "advance-route-contact-horizon-v1-0-to-20-h-1-0"))
            assertThrows(IllegalArgumentException.class, () -> RouteContactSteps.parse(bad));
    }
    @Test void completeSameFrameProducesContactFreeProof() {
        Frame frame = starting(); assertEquals(ProofKind.CONTACT_FREE, RouteContactProofs.oneDay(frame, List.of(query(frame)), List.of()).values().iterator().next().kind());
    }
    @Test void sameDateDifferentNativeRevisionCannotReuseProof() {
        assertTrue(RouteContactProofs.oneDay(frame(2, 100, starting().ownArmies(), starting().hostileArmies()), List.of(query(starting())), List.of()).isEmpty());
    }
    @Test void sameNativeRevisionDifferentPublicSnapshotCannotReuseProof() {
        Frame old = starting(); Frame next = new Frame(old.owner(), "different", old.revision(), old.nativeRevision(), 100, true, true, 3, false, true,
                Nil.INSTANCE, Nil.INSTANCE, Nil.INSTANCE, old.activeWarIds(), old.ownArmies(), old.hostileArmies());
        assertTrue(RouteContactProofs.oneDay(next, List.of(query(old)), List.of()).isEmpty());
    }
    @Test void latestMalformedOrFailedQueryShadowsOlderSuccessfulQuery() {
        Frame frame = starting(); RouteQuery query = query(frame); var scope = new RouteContactProofs.Scope(0, 20, List.of(8));
        assertTrue(RouteContactProofs.oneDayEntries(frame, List.of(new RouteContactProofs.QueryEntry(scope, Optional.of(query)),
                new RouteContactProofs.QueryEntry(scope, Optional.empty())), List.of()).isEmpty());
    }
    @Test void subjectRemainingRouteMustMatchNativeTimedRouteExactly() {
        Frame frame = frame(1, 100, List.of(army(0, 10, 20, List.of(30, 20))), starting().hostileArmies());
        assertTrue(RouteContactProofs.oneDay(frame, List.of(query(frame)), List.of()).isEmpty());
    }
    @Test void differentHostileSetInvalidatesSameFrameQuery() {
        Frame frame = frame(1, 100, starting().ownArmies(), List.of(army(9, 99, null, List.of())));
        assertTrue(RouteContactProofs.oneDay(frame, List.of(query(frame)), List.of()).isEmpty());
    }
    @Test void nativeRetreatingEnemyRemainsInObservationButIsExcludedFromActiveRouteWatch() {
        Army retreat = new Army(9, false, 90, Optional.empty(), List.of(), Optional.of("retreating"), Optional.of(6), false, true);
        Frame frame = frame(1, 100, starting().ownArmies(), List.of(starting().hostileArmies().getFirst(), retreat));
        assertEquals(List.of(8), frame.hostileIds()); assertEquals(2, frame.hostileArmies().size());
        assertFalse(RouteContactProofs.oneDay(frame, List.of(query(frame)), List.of()).isEmpty());
    }
    @Test void anotherControlledArmyAtHostileProvincePreventsAdvancingWholeGame() {
        Frame frame = frame(1, 100, List.of(starting().ownArmies().getFirst(), army(2, 99, null, List.of())), starting().hostileArmies());
        assertTrue(RouteContactProofs.oneDay(frame, List.of(query(frame)), List.of()).isEmpty());
    }
    @Test void safeStationarySiblingGetsWholeWindowWithoutInventingNativeRouteQuery() {
        Frame frame = frame(1, 100, List.of(starting().ownArmies().getFirst(), army(2, 70, null, List.of())), starting().hostileArmies());
        var days = RouteContactProofs.oneDay(frame, List.of(query(frame)), List.of());
        Proof window = RouteContactProofs.window(frame, days, new RouteContactProofs.Scope(0, 20, List.of(8)), 3, false).orElseThrow();
        assertEquals(List.of(0, 2, 8), window.watchArmyIds()); assertEquals(172, window.targetDateRaw()); assertEquals(2, window.controlledWindows().size());
    }
    @Test void movingSiblingNeedsItsOwnCompleteSameFrameTimelineForMultidayWindow() {
        Frame frame = frame(1, 100, List.of(starting().ownArmies().getFirst(), army(2, 70, 71, List.of(71))), starting().hostileArmies());
        var days = RouteContactProofs.oneDay(frame, List.of(query(frame)), List.of());
        assertFalse(days.isEmpty()); assertTrue(RouteContactProofs.window(frame, days, new RouteContactProofs.Scope(0, 20, List.of(8)), 3, false).isEmpty());
    }
    @Test void shorterWindowRequiresExplicitCampaignCadenceBinding() {
        Frame frame = starting(); var days = RouteContactProofs.oneDay(frame, List.of(query(frame)), List.of()); var scope = new RouteContactProofs.Scope(0, 20, List.of(8));
        assertTrue(RouteContactProofs.window(frame, days, scope, 2, false).isEmpty());
        assertEquals(148, RouteContactProofs.window(frame, days, scope, 2, true).orElseThrow().targetDateRaw());
    }
    static RouteQuery endpointQuery(Frame frame) {
        return new RouteQuery("query-route-contact-horizon-v1-0-to-20-h-1-8", true, frame.owner(), frame.snapshotId(), frame.revision(), frame.nativeRevision(), frame.dateRaw(),
                0, 20, List.of(8), new RouteWindowPolicy.Route(0, 10, List.of(20), List.of(frame.dateRaw() + 100)),
                List.of(new RouteWindowPolicy.Route(8, 99, List.of(10), List.of(frame.dateRaw() + 24))), 10, List.of(99),
                List.of(new RouteWindowPolicy.SameProvince(8, 10, frame.dateRaw() + 24, frame.dateRaw() + 24)));
    }
    @Test void unavoidableClosedEndpointIsProofButDoesNotClaimCombat() {
        Frame frame = starting(); Proof proof = RouteContactProofs.oneDay(frame, List.of(endpointQuery(frame)), List.of()).values().iterator().next();
        assertEquals(ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT, proof.kind()); assertFalse(proof.strictFollowup());
    }
    @Test void retainedEndpointCreatesExactlyOneStrictFollowupAcrossRestoreHistory() {
        Frame frame = starting(); Transition prior = new Transition(TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, false, "episode-1", 0, 10, 76, 100, List.of(8));
        var rows = List.of(new AdvanceHistory(true, 0, "episode-1", 100, Optional.of(prior), false));
        Proof proof = RouteContactProofs.oneDay(frame, List.of(endpointQuery(frame)), rows).values().iterator().next(); assertTrue(proof.strictFollowup());
    }
    @Test void exhaustedStrictFollowupCannotAuthorizeThirdExactDay() {
        Frame frame = starting(); var rows = List.of(new AdvanceHistory(false, 0, "episode-1", 100, Optional.empty(), true));
        assertTrue(RouteContactProofs.oneDay(frame, List.of(endpointQuery(frame)), rows).isEmpty());
    }
    @Test void laterGenericTimelineRowShadowsAnOlderPredictedBoundary() {
        Frame frame = starting(); Transition prior = new Transition(TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, false, "episode-1", 0, 10, 76, 100, List.of(8));
        var rows = List.of(new AdvanceHistory(true, 0, "episode-1", 100, Optional.of(prior), false),
                new TimelineBarrier("life-advance-one-day", "latest timeline is not a route-contact marker"));
        assertFalse(RouteContactProofs.oneDay(frame, List.of(endpointQuery(frame)), rows).values().iterator().next().strictFollowup());
    }
}
