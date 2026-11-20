package org.xar.ck3.control.nativebridge;

import org.xar.ck3.control.contracts.ExactRef;

/**
 * Independent Native114 artifact DATA. Matching bytes never enable a profile,
 * prove an actual runtime speed count or authorize a speed effect.
 *
 * The transport requires an explicit binding to its original Managed owner.
 * The default Managed path continues to select corrected112 only.
 */
final class Native114SourceProfile {
    private static final long BRIDGE_BYTES = 12382720L;
    private static final String BRIDGE_SHA256 =
            "42cecc8a69bc5f6142e10b8d5bb044fab9a63d26bcfd3a01a6de25501f4a604a";

    private Native114SourceProfile() { }

    static boolean matchesBridge(ExactRef bridge) {
        return bridge != null && bridge.bytes() == BRIDGE_BYTES
                && BRIDGE_SHA256.equalsIgnoreCase(bridge.sha256());
    }
}
