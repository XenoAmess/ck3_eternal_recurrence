package org.xar.ck3.control.wave3.runtime.processcustody;

import java.io.IOException;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;

/** Query-only handle lifetime port. Observations must never reopen the PID. */
@FunctionalInterface
public interface RetainedProcessApi {
    Handle open(long pid) throws IOException;

    interface Handle extends AutoCloseable {
        ProcessIdentityClaimV1 identity();
        long waitZero() throws IOException;
        long exitCode() throws IOException;
        @Override void close() throws IOException;
    }
}
