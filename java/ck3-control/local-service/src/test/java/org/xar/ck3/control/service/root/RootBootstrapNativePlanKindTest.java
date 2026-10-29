package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;

/** Closed output-contract tests only. No NativePlan, issuer card or Native/Game qualification is manufactured. */
class RootBootstrapNativePlanKindTest {
    @Test void firstNativePlanHasOneFixedFlatTargetWithinTheUnchangedFileCap() {
        var actual=new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.NATIVE_LAUNCH_PLAN,
                "native-launch-plan.json",1234,"1".repeat(64));
        assertEquals(1234,actual.bytes());
        assertThrows(IllegalArgumentException.class,()->new RootBootstrapOutputContract.Output(
                RootBootstrapOutputContract.Kind.NATIVE_LAUNCH_PLAN,"different-plan.json",1234,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new RootBootstrapOutputContract.Output(
                RootBootstrapOutputContract.Kind.NATIVE_LAUNCH_PLAN,"nested/native-launch-plan.json",1234,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new RootBootstrapOutputContract.Output(
                RootBootstrapOutputContract.Kind.NATIVE_LAUNCH_PLAN,"native-launch-plan.json",(1L<<20)+1,"1".repeat(64)));
    }
}
