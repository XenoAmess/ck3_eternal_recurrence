package org.xar.ck3.control.wave2.runtime.stdioidentity;

import java.io.IOException;
import java.util.Objects;

/** Explicit failed observation; never substitutes an alive/GREEN flag or cached identity. */
public final class IdentityUnavailableException extends IOException {
    private static final long serialVersionUID = 1L;

    public enum Reason {
        INVALID_PID, NATIVE_UNAVAILABLE, PROCESS_UNAVAILABLE, GENERATION_MISMATCH,
        MACHINE_MISMATCH, SOURCE_UNAVAILABLE, SOURCE_MISMATCH
    }

    private final Reason reason;

    public IdentityUnavailableException(Reason reason, String message) {
        super(message);
        this.reason = Objects.requireNonNull(reason);
    }

    public IdentityUnavailableException(Reason reason, String message, Throwable cause) {
        super(message, cause);
        this.reason = Objects.requireNonNull(reason);
    }

    public Reason reason() { return reason; }
}
