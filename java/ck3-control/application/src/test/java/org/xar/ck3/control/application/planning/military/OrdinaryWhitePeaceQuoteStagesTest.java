package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

/** Before issuing dependent terms, the real original options must pass the sole policy's first-phase gates. */
final class OrdinaryWhitePeaceQuoteStagesTest {
    @Test void onlyFreshEligibleClaimOptionsRequestTheSecondTermsQuote() {
        for (var variant : OrdinaryWhitePeacePolicy.Variant.values()) {
            var frame = OrdinaryWhitePeacePolicyTest.frame(variant);
            assertEquals(variant == OrdinaryWhitePeacePolicy.Variant.CLAIM_CB,
                    OrdinaryWhitePeacePolicy.needsClaimTerms(OrdinaryWhitePeacePolicyTest.obj(frame), 23));
        }
        var claim = OrdinaryWhitePeacePolicyTest.frame(OrdinaryWhitePeacePolicy.Variant.CLAIM_CB);
        claim.putArray("war_termination_terms");
        assertTrue(OrdinaryWhitePeacePolicy.needsClaimTerms(OrdinaryWhitePeacePolicyTest.obj(claim), 23));
        assertFalse(OrdinaryWhitePeacePolicy.evaluate(OrdinaryWhitePeacePolicyTest.obj(claim), 23).ready());
        for (String key : java.util.List.of("queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_connection_generation", "episode_run_id")) {
            var stale = claim.deepCopy(); OrdinaryWhitePeacePolicyTest.options(stale).remove(key);
            assertFalse(OrdinaryWhitePeacePolicy.needsClaimTerms(OrdinaryWhitePeacePolicyTest.obj(stale), 23), key);
        }
        var refused = claim.deepCopy(); ((ObjectNode) OrdinaryWhitePeacePolicyTest.white(refused).get("recipient_response")).put("would_accept_now", false);
        assertFalse(OrdinaryWhitePeacePolicy.needsClaimTerms(OrdinaryWhitePeacePolicyTest.obj(refused), 23));
    }
    @Test void historicalClassificationNeverGrantsFreshTermsOrReady() {
        var stale = OrdinaryWhitePeacePolicyTest.frame(OrdinaryWhitePeacePolicy.Variant.CLAIM_CB);
        var war = org.xar.ck3.control.planning.opportunity.OpportunityJson.object(OrdinaryWhitePeacePolicyTest.obj(stale).get("active_wars") instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr wars ? wars.items().getFirst() : null, "actual war");
        OrdinaryWhitePeacePolicyTest.options(stale).put("queried_revision", 1);
        var options = OrdinaryWhitePeacePolicyTest.obj(OrdinaryWhitePeacePolicyTest.options(stale));
        assertTrue(OrdinaryWhitePeacePolicy.historicalOptionsRequireRefresh(war, options));
        assertFalse(OrdinaryWhitePeacePolicy.needsClaimTerms(OrdinaryWhitePeacePolicyTest.obj(stale), 23));
        assertFalse(OrdinaryWhitePeacePolicy.evaluate(OrdinaryWhitePeacePolicyTest.obj(stale), 23).ready());
    }
}
