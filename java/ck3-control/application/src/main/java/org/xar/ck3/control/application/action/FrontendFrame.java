package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual frontend wire frames. A menu has no fabricated map, player, episode or semantic revision. */
public sealed interface FrontendFrame permits FrontendFrame.Menu, FrontendFrame.Snapshot {
    BigInteger querySequence();
    BigInteger expectedRevision();
    record Menu(BigInteger querySequence) implements FrontendFrame {
        public Menu { positive(querySequence); }
        @Override public BigInteger expectedRevision() { return BigInteger.ZERO; }
    }
    record Snapshot(String snapshotId, BigInteger revision, BigInteger nativeRevision, long dateRaw,
            BigInteger querySequence) implements FrontendFrame {
        public Snapshot { StrictJson.text(snapshotId); positive(revision); positive(nativeRevision); positive(querySequence); }
        @Override public BigInteger expectedRevision() { return nativeRevision; }
    }
    static void positive(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0,
                "positive exact frontend uint64 required");
    }
}
