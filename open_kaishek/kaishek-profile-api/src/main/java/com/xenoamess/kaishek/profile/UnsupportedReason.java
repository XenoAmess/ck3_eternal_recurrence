package com.xenoamess.kaishek.profile;

/** Explicit fail-closed reasons; UNKNOWN must never become a silent no-op. */
public enum UnsupportedReason {
    UNKNOWN_OPCODE,
    UNSUPPORTED_PROFILE,
    UNSUPPORTED_VERSION,
    UNSUPPORTED_NATIVE_OPERATION,
    MISSING_SCHEMA,
    INVALID_INPUT,
    INVALID_SCOPE,
    MISSING_SCOPE,
    UNRESOLVED_REFERENCE,
    UNCONFIRMED_SCHEDULER,
    UNCONFIRMED_RANDOMNESS,
    FEATURE_DISABLED,
    STATE_UNAVAILABLE,
    STALE_STATE,
    NOT_CERTIFIED
}
