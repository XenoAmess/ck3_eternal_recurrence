package org.xar.ck3.control.wave3.governance.lifecycle;

import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Original consumers' binding-only gates; save bytes, anchors and locks remain their owners'. */
public final class SuccessionLifecycleConsumers {
    private SuccessionLifecycleConsumers() { }
    public static SuccessionLifecycleBinding ordinarySeed(SuccessionLifecycleBinding value) {
        domainRequire(value.profile() == SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF, "ordinary seed requires frozen xar_off/no-pact profile"); return value;
    }
    public static SuccessionLifecycleBinding rogueCheckpoint(SuccessionLifecycleBinding value) {
        domainRequire(value.profile() == SuccessionLifecycleBinding.Profile.ROGUE_ONE_LIFE, "rogue checkpoint requires xar_on/terminal-settlement profile");
        if (value.source().equals("legacy-driver-default")) { domainRequire(value.equals(SuccessionLifecycleBinding.legacyRogue()), "exact legacy rogue binding required"); }
        else { domainRequire(value.source().equals("prepared-environment-manifest") && value.environmentSha256() != null, "prepared rogue environment binding required"); }
        return value;
    }
    public static SuccessionLifecycleBinding equalAnchors(SuccessionLifecycleBinding driver, SuccessionLifecycleBinding checkpoint, SuccessionLifecycleBinding savedHistory) {
        domainRequire(driver != null && driver.equals(checkpoint) && driver.equals(savedHistory), "checkpoint lifecycle anchors are mixed"); return driver;
    }
    private static void domainRequire(boolean admitted, String reason) {
        if (!admitted) { throw new ProjectionDomainRejection(reason); }
    }
}
