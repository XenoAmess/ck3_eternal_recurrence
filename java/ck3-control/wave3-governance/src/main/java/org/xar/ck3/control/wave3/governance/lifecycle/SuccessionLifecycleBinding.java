package org.xar.ck3.control.wave3.governance.lifecycle;

import java.util.Objects;

/** The complete supported lifecycle profiles, without runtime or recovery authority. */
public record SuccessionLifecycleBinding(Profile profile, String source, String environmentSha256) {
    public static final String SCHEMA = "xar.ck3.succession-lifecycle-binding/v1";
    public enum Profile {
        ROGUE_ONE_LIFE("rogue_one_life", "xar_on", "terminal_settlement_required"),
        ORDINARY_FROZEN_OFF("ordinary_campaign_succession", "xar_off", "absent_by_fresh_campaign_xar_off_contract"),
        ORDINARY_VERIFIED_MOD_ABSENCE("ordinary_campaign_succession", null, "absent_by_verified_xar_mod_not_loaded"),
        /** Configured vanilla DATA, without a verified mod-absence or native-cause assertion. */
        ORDINARY_VANILLA_CONFIGURATION("ordinary_campaign_succession", null, "not_applicable_to_vanilla_configuration"),
        UNKNOWN("unknown", null, "unknown");
        private final String lifecycle;
        private final String xarEnabled;
        private final String pactContract;
        Profile(String lifecycle, String xarEnabled, String pactContract) {
            this.lifecycle = lifecycle; this.xarEnabled = xarEnabled; this.pactContract = pactContract;
        }
        public String lifecycle() { return lifecycle; }
        public String xarEnabled() { return xarEnabled; }
        public String pactContract() { return pactContract; }
        public boolean ordinary() { return this == ORDINARY_FROZEN_OFF || this == ORDINARY_VERIFIED_MOD_ABSENCE || this == ORDINARY_VANILLA_CONFIGURATION; }
    }
    public SuccessionLifecycleBinding {
        Objects.requireNonNull(profile);
        require(source != null && !source.isEmpty(), "lifecycle source required");
        require(environmentSha256 == null || environmentSha256.matches("[0-9a-f]{64}"), "lowercase SHA-256 required");
        require(!profile.ordinary() || profile == Profile.ORDINARY_VANILLA_CONFIGURATION || environmentSha256 != null, "ordinary succession requires frozen environment binding");
        require(profile != Profile.ORDINARY_VERIFIED_MOD_ABSENCE || source.equals("absent_by_verified_xar_mod_not_loaded"), "verified absence source mismatch");
        require(profile != Profile.ORDINARY_VANILLA_CONFIGURATION || source.equals("ordinary_vanilla_configuration") && environmentSha256 == null, "vanilla configuration requires its exact source and no environment assertion");
    }
    public static SuccessionLifecycleBinding legacyRogue() { return new SuccessionLifecycleBinding(Profile.ROGUE_ONE_LIFE, "legacy-driver-default", null); }
    public static SuccessionLifecycleBinding unknown() { return new SuccessionLifecycleBinding(Profile.UNKNOWN, "unbound", null); }
    static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
