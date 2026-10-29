package org.xar.ck3.control.application.routecontact;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;

final class RouteContactPostconditionsTest {
    static final Frame BEFORE = RouteContactProofsTest.starting();
    static Proof proof(boolean strict) {
        Transition prior = new Transition(TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, false, "episode-1", 0, 10, 76, 100, List.of(8));
        return new Proof(ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT, RouteContactProofsTest.endpointQuery(BEFORE), strict,
                strict ? Optional.of(prior) : Optional.empty(), 1, List.of(), Map.of());
    }
    static Frame after(List<Army> own, List<Army> enemies) { return RouteContactProofsTest.frame(2, 124, own, enemies); }
    @Test void closedEndpointPredictionNeverClaimsActualContact() {
        Frame after = after(BEFORE.ownArmies(), BEFORE.hostileArmies());
        assertTrue(RouteContactPostconditions.observed(BEFORE, after, proof(false)).isEmpty());
        Transition predicted = RouteContactPostconditions.predictedEndpoint(BEFORE, after, proof(false)).orElseThrow();
        assertEquals(TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, predicted.kind()); assertFalse(predicted.contactObserved());
    }
    @Test void strictFollowupCannotUseAnotherPredictedEndpoint() {
        Frame after = after(BEFORE.ownArmies(), BEFORE.hostileArmies());
        assertTrue(RouteContactPostconditions.predictedEndpoint(BEFORE, after, proof(true)).isEmpty());
    }
    @Test void actualHostileProvinceEntryIsAStateTransitionButDoesNotClaimCombat() {
        Frame after = after(BEFORE.ownArmies(), List.of(RouteContactProofsTest.army(8, 10, null, List.of())));
        Transition transition = RouteContactPostconditions.observed(BEFORE, after, proof(false)).orElseThrow();
        assertEquals(TransitionKind.HOSTILE_ENTERED_CONTACT_PROVINCE, transition.kind()); assertFalse(transition.contactObserved());
        assertTrue(RouteContactPostconditions.observed(BEFORE, after, proof(true)).isEmpty());
    }
    @Test void observedCombatSatisfiesStrongFollowup() {
        Army combat = new Army(0, true, 10, Optional.of(20), List.of(20), Optional.of("combat"), Optional.of(2), true, false);
        Transition transition = RouteContactPostconditions.observed(BEFORE, after(List.of(combat), BEFORE.hostileArmies()), proof(true)).orElseThrow();
        assertEquals(TransitionKind.ACTIVE_COMBAT_OBSERVED, transition.kind()); assertTrue(transition.contactObserved());
    }
    @Test void observedRetreatSatisfiesStrongFollowup() {
        Army retreat = new Army(0, true, 10, Optional.of(20), List.of(20), Optional.of("retreating"), Optional.of(6), false, true);
        assertEquals(TransitionKind.RETREAT_OBSERVED, RouteContactPostconditions.observed(BEFORE, after(List.of(retreat), BEFORE.hostileArmies()), proof(true)).orElseThrow().kind());
    }
    @Test void overshotClockCannotSatisfyEvenStrongCombatPostcondition() {
        Frame late = RouteContactProofsTest.frame(2, 148, BEFORE.ownArmies(), BEFORE.hostileArmies());
        assertTrue(RouteContactPostconditions.observed(BEFORE, late, proof(false)).isEmpty());
        assertTrue(RouteContactPostconditions.predictedEndpoint(BEFORE, late, proof(false)).isEmpty());
    }
    @Test void refreshRequiresBothNativeAndPublicRevisionsToIncrease() {
        Frame prior = after(BEFORE.ownArmies(), BEFORE.hostileArmies());
        Frame bad = new Frame(prior.owner(), "native-3", BigInteger.valueOf(3), prior.nativeRevision(), 124, true, true, 3, false, true,
                Nil.INSTANCE, Nil.INSTANCE, Nil.INSTANCE, prior.activeWarIds(), prior.ownArmies(), prior.hostileArmies());
        assertFalse(RouteContactPostconditions.samePausedRefreshOwner(prior, bad));
        assertTrue(RouteContactPostconditions.samePausedRefreshOwner(prior, RouteContactProofsTest.frame(3, 124, prior.ownArmies(), prior.hostileArmies())));
    }
    @Test void refreshCannotSilentlyAdvanceAnotherDay() {
        Frame prior = after(BEFORE.ownArmies(), BEFORE.hostileArmies());
        assertFalse(RouteContactPostconditions.samePausedRefreshOwner(prior, RouteContactProofsTest.frame(3, 148, prior.ownArmies(), prior.hostileArmies())));
    }
}
