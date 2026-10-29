package org.xar.ck3.control.application.readiness;

import java.io.IOException;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Writes original bytes through the one archive while borrowing the original writer session. */
@FunctionalInterface
public interface ReadinessArchive {
    enum Role {
        NATIVE_PACKET(64 * 1024 * 1024 + 4), SEMANTIC(64 * 1024 * 1024),
        DRIVER_STAMP(16 * 1024), DRIVER(64 * 1024 * 1024),
        HELLO(1024 * 1024), HEARTBEAT(1024 * 1024), SOURCE_PROOF(16 * 1024 * 1024), DIAGNOSTIC(64 * 1024);
        private final int maximumBytes;
        Role(int maximumBytes) { this.maximumBytes = maximumBytes; }
        public int maximumBytes() { return maximumBytes; }
    }
    ExactRef preserve(ContinuityStorePort.Session borrowed, Role role, byte[] actualBytes) throws IOException;
}
