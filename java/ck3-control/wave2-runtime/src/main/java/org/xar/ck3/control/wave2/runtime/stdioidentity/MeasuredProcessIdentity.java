package org.xar.ck3.control.wave2.runtime.stdioidentity;

import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;

/** Actual reader result; intentionally has no public JSON/claim constructor. */
public final class MeasuredProcessIdentity {
    private final ProcessIdentityClaimV1 identity;
    private final String uptimeMillisDecimal;
    private final Instant observedAtUtc;

    MeasuredProcessIdentity(ProcessIdentityClaimV1 identity, String uptimeMillisDecimal, Instant observedAtUtc) {
        this.identity = Objects.requireNonNull(identity);
        new CrossJsDecimalUInt64(uptimeMillisDecimal);
        this.uptimeMillisDecimal = uptimeMillisDecimal;
        this.observedAtUtc = Objects.requireNonNull(observedAtUtc);
    }

    public long pid() { return identity.pid(); }
    public String creationFiletimeDecimal() { return identity.creationFiletimeDecimal(); }
    public Path executable() { return identity.executable(); }
    /** Actual Win32 GetTickCount64 system uptime, never an inferred process age. */
    public String uptimeMillisDecimal() { return uptimeMillisDecimal; }
    public Instant observedAtUtc() { return observedAtUtc; }
    public ProcessIdentityClaimV1 identity() { return identity; }
}
