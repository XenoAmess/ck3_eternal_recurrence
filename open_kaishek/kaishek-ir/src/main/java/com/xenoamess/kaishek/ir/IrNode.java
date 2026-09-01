package com.xenoamess.kaishek.ir;

import com.xenoamess.kaishek.profile.*;

/** Common strict-IR node contract consumed by validators and runtime. */
public interface IrNode {
    String opcodeId();
    String profileVersion();
    OpcodeKind kind();
    ScopeType requiredScope();
    SourceSpan sourceSpan();
    RandomnessClass randomness();
    UnsupportedReason unsupportedReason();
    /** An unsupported randomness class is never executable without a reason. */
    default boolean executable() {
        return unsupportedReason() == null && randomness() != RandomnessClass.UNSUPPORTED;
    }
}
