package org.xar.ck3.control.wave2.runtime.stdioidentity;

import java.io.IOException;

/** Read-only live kernel measurement port; no spawn, terminate, PID scan or adoption operation. */
@FunctionalInterface
public interface ProcessIdentityReader {
    MeasuredProcessIdentity observe(long pid) throws IOException;
}
