package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentTierLookupKey150.LookupKey32;

/** Explicit owned ports for the actual local normal caller segment, never native Game memory. */
public final class GovernmentCaller153Api {
    private GovernmentCaller153Api() { }
    public enum Outcome {
        SKIPPED_SIGNED_GUARD, NORMALIZED_TLS_FLAG, NORMALIZED_COUNTER_LIMIT,
        NORMALIZED_NULL_HELPER, NORMALIZED_DIAGNOSTIC
    }
    /** r12d was copied from an earlier r14d before this segment; it is zero-extended by x86. */
    public record Entry(long imageBaseBits, long governmentBits, int savedTlsOffsetDwordBits,
                        long savedRsiBits, int savedR15dBits) { }
    /** Actual RCX/RDX/R8D/R9D and stack20/28/30 bit roles at CALL ABBAF0. */
    public record DiagnosticCall(long rcxBits, long rdxBits, int r8dBits, int r9dBits,
                                 long stack20Bits, long stack28Bits, long stack30Bits) { }
    public interface Memory {
        int readDword(long addressBits);
        long readQword(long addressBits);
        int readUnsignedByte(long addressBits);
        void writeDword(long addressBits, int valueBits);
        int lockedXaddDword(long addressBits, int addendBits);
    }
    public interface Calls {
        long readGsQword58();
        long call3F4F8E0(LookupKey32 ecxBits);
        long call3F5F970(int ecxBits);
        void callABBAF0(DiagnosticCall arguments);
    }
}
