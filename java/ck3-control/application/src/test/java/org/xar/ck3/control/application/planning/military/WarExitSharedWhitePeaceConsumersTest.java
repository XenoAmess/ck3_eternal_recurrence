package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.warexit.LegacyWarExitPolicy;
import org.xar.ck3.control.application.planning.warexit.WarExitPolicies;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual shared four-branch producer to the original WarCore consumers; source vectors are not live evidence. */
final class WarExitSharedWhitePeaceConsumersTest {
    @Test void everyOriginalVariantReachesItsOnlyMatchingWarCoreConsumerAfterJsonRoundTrip() {
        for (var variant : OrdinaryWhitePeacePolicy.Variant.values()) {
            Obj original = OrdinaryWhitePeacePolicyTest.obj(OrdinaryWhitePeacePolicyTest.frame(variant));
            Obj input = DriverJson.object(DriverJson.encode(original), DriverJson.MAX_NATIVE_BYTES);
            assertEquals(original, input);
            var produced = assertInstanceOf(OrdinaryWhitePeacePolicy.Ready.class,
                    OrdinaryWhitePeacePolicy.evaluate(input, 23));
            assertEquals(variant, produced.variant());
            assertEquals(variant == OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE,
                    LegacyWarExitPolicy.deJureWhitePeace(input, 23));
            assertEquals(variant == OrdinaryWhitePeacePolicy.Variant.DEFENDER_DE_JURE
                            || variant == OrdinaryWhitePeacePolicy.Variant.DEFENDER_MINOR_RELIGIOUS,
                    LegacyWarExitPolicy.defenderProposal(input, 23));
            assertEquals(variant == OrdinaryWhitePeacePolicy.Variant.CLAIM_CB,
                    WarExitPolicies.claimTermsReady(input, 23));
            assertEquals(variant == OrdinaryWhitePeacePolicy.Variant.CLAIM_CB,
                    WarExitPolicies.claimWhitePeaceCandidate(input, 23));
        }
    }

    @Test void staleOrMissingOriginalBindingCannotSurviveThroughAnotherWarCorePredicate() {
        for (var variant : OrdinaryWhitePeacePolicy.Variant.values()) {
            for (String field : java.util.List.of("queried_snapshot_id", "queried_revision", "queried_native_revision",
                    "queried_connection_generation", "episode_run_id")) {
                ObjectNode frame = OrdinaryWhitePeacePolicyTest.frame(variant);
                OrdinaryWhitePeacePolicyTest.options(frame).remove(field);
                Obj input = OrdinaryWhitePeacePolicyTest.obj(frame);
                assertFalse(OrdinaryWhitePeacePolicy.evaluate(input, 23).ready());
                assertFalse(LegacyWarExitPolicy.deJureWhitePeace(input, 23));
                assertFalse(LegacyWarExitPolicy.defenderProposal(input, 23));
                assertFalse(WarExitPolicies.claimTermsReady(input, 23));
                assertFalse(WarExitPolicies.claimWhitePeaceCandidate(input, 23));
            }
        }
    }
}
