package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Shared actual lifecycle producer -> production preclock mode gate DATA only, never a live capture token. */
final class RootPreclockLifecycleModeTest {
    private static OpportunityJson.Obj semantic(SuccessionLifecycleBinding value) {
        return new OpportunityJson.Obj(Map.of("succession_lifecycle",DriverJson.object(SuccessionLifecycleCodec.encode(value),SuccessionLifecycleCodec.MAX_BYTES)));
    }
    @Test void originalTypedOrdinaryAndRogueProfilesChooseOnlyTheOrdinaryPublisher() {
        assertTrue(RootNaturalSuccessionOriginals.ordinaryPreclockExpectation(semantic(new SuccessionLifecycleBinding(
                SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF,"actual-frozen-environment","a".repeat(64)))));
        assertTrue(RootNaturalSuccessionOriginals.ordinaryPreclockExpectation(semantic(new SuccessionLifecycleBinding(
                SuccessionLifecycleBinding.Profile.ORDINARY_VERIFIED_MOD_ABSENCE,"absent_by_verified_xar_mod_not_loaded","b".repeat(64)))));
        assertFalse(RootNaturalSuccessionOriginals.ordinaryPreclockExpectation(semantic(new SuccessionLifecycleBinding(
                SuccessionLifecycleBinding.Profile.ROGUE_ONE_LIFE,"actual-one-life-runtime",null))));
    }
    @Test void MissingWrongAndUnknownLifecycleCannotBecomeADefaultMode() {
        assertThrows(IllegalArgumentException.class,()->RootNaturalSuccessionOriginals.ordinaryPreclockExpectation(new OpportunityJson.Obj(Map.of())));
        assertThrows(IllegalArgumentException.class,()->RootNaturalSuccessionOriginals.ordinaryPreclockExpectation(new OpportunityJson.Obj(Map.of(
                "succession_lifecycle",new OpportunityJson.Text("ordinary_campaign_succession")))));
        assertThrows(IllegalArgumentException.class,()->RootNaturalSuccessionOriginals.ordinaryPreclockExpectation(semantic(SuccessionLifecycleBinding.unknown())));
    }
}
