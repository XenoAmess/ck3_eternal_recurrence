package org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup;

import java.util.List;
import java.util.Objects;
import java.util.OptionalLong;

/** Offline typed decoder of owner-verified856050 instruction effects. Never invokes Native or reads memory. */
public final class InlineStorageCleanupPlan {
    public enum Path { INLINE, DIRECT_CALL, ADJUSTED_CALL, REJECTED_HEADER, NEEDS_POINTER, NEEDS_BACK_REFERENCE }
    public enum Target { NONE, RVA_4223F44, RVA_4232A70 }
    public enum ResetTiming { INLINE_NORMAL_PATH, AFTER_NORMAL_CALL_RETURN, NONE_AFTER_TRAP, UNRESOLVED }
    public record Plan(Path path, Target target, OptionalLong rcxBits, OptionalLong rdxBits,
                       OptionalLong r8Bits, OptionalLong backReferenceReadAddress, ResetTiming resetTiming) {
        public Plan {
            Objects.requireNonNull(path, "path");
            Objects.requireNonNull(target, "target");
            Objects.requireNonNull(rcxBits, "rcxBits");
            Objects.requireNonNull(rdxBits, "rdxBits");
            Objects.requireNonNull(r8Bits, "r8Bits");
            Objects.requireNonNull(backReferenceReadAddress, "backReferenceReadAddress");
            Objects.requireNonNull(resetTiming, "resetTiming");
        }
    }
    public record RelativeReset(int offsetFromD, int byteWidth, long valueBits) { }
    private InlineStorageCleanupPlan() { }

    /** Owner locked: D=C+98. These writes occur only on a normal reset path, never actual observations here. */
    public static List<RelativeReset> normalResetValues() {
        return List.of(new RelativeReset(0x10, 8, 0), new RelativeReset(0x18, 8, 15), new RelativeReset(0, 1, 0));
    }

    /**
     * capacityBits is rawQWORD[D+18]; heapPointerBits, if present, is observedQWORD[D];
     * backReferenceBits, if present, is observedQWORD[P-8]. Missing observations are not zero.
     * All long arithmetic below is native modulo2^64, all comparisons unsigned.
     * If K<16: INLINE/NONE, all args/readAddress absent, resetINLINE_NORMAL_PATH; ignore both observations.
     * Otherwise missingP: NEEDS_POINTER/NONE, args/readAddress absent, resetUNRESOLVED.
     * WithP, S=K+1 wrapping. S<4096: DIRECT_CALL/4223F44(RCX=P,RDX=S), R8/readAddress absent,
     * resetAFTER_NORMAL_CALL_RETURN. In particularK=unsignedmax givesS=0, not a rejected header.
     * ForS>=4096, readAddress=P-8 wrapping. MissingH: NEEDS_BACK_REFERENCE/NONE, args absent,
     * preserve readAddress, resetUNRESOLVED. WithH computeDelta=P-H-8 wrapping andZ=S+0x27 wrapping.
     * Delta>31: REJECTED_HEADER/4232A70(RCX=P-H,RDX=Z,R8=H), preserve readAddress,
     * resetNONE_AFTER_TRAP because actualCALL is followed byINT3 even if it returns.
     * ElseADJUSTED_CALL/4223F44(RCX=H,RDX=Z,R8=H), preserve readAddress,
     * resetAFTER_NORMAL_CALL_RETURN. KnownP/H=0 are observations, not missing values. No invented null,
     * overflow, ownership, or capacity validity guards. No formal allocator/type name is established.
     */
    public static Plan plan(long capacityBits, OptionalLong heapPointerBits, OptionalLong backReferenceBits) {
        long K = capacityBits;

        // If K < 16 (unsigned comparison)
        if (Long.compareUnsigned(K, 16) < 0) {
            return new Plan(Path.INLINE, Target.NONE, OptionalLong.empty(), OptionalLong.empty(),
                    OptionalLong.empty(), OptionalLong.empty(), ResetTiming.INLINE_NORMAL_PATH);
        }

        // Otherwise, check if heapPointerBits is missing
        if (heapPointerBits.isEmpty()) {
            return new Plan(Path.NEEDS_POINTER, Target.NONE, OptionalLong.empty(), OptionalLong.empty(),
                    OptionalLong.empty(), OptionalLong.empty(), ResetTiming.UNRESOLVED);
        }

        long P = heapPointerBits.getAsLong();
        // S = K + 1 wrapping
        long S = K + 1;

        // If S < 4096 (unsigned comparison)
        if (Long.compareUnsigned(S, 4096) < 0) {
            return new Plan(Path.DIRECT_CALL, Target.RVA_4223F44, OptionalLong.of(P), OptionalLong.of(S),
                    OptionalLong.empty(), OptionalLong.empty(), ResetTiming.AFTER_NORMAL_CALL_RETURN);
        }

        // For S >= 4096, readAddress = P - 8 wrapping
        long readAddress = P - 8;

        // Check if backReferenceBits is missing
        if (backReferenceBits.isEmpty()) {
            return new Plan(Path.NEEDS_BACK_REFERENCE, Target.NONE, OptionalLong.empty(), OptionalLong.empty(),
                    OptionalLong.empty(), OptionalLong.of(readAddress), ResetTiming.UNRESOLVED);
        }

        long H = backReferenceBits.getAsLong();
        // Delta = P - H - 8 wrapping
        long delta = P - H - 8;
        // Z = S + 0x27 wrapping
        long Z = S + 0x27;

        // If Delta > 31 (unsigned comparison)
        if (Long.compareUnsigned(delta, 31) > 0) {
            return new Plan(Path.REJECTED_HEADER, Target.RVA_4232A70, OptionalLong.of(P - H), OptionalLong.of(Z),
                    OptionalLong.of(H), OptionalLong.of(readAddress), ResetTiming.NONE_AFTER_TRAP);
        } else {
            // Else ADJUSTED_CALL
            return new Plan(Path.ADJUSTED_CALL, Target.RVA_4223F44, OptionalLong.of(H), OptionalLong.of(Z),
                    OptionalLong.of(H), OptionalLong.of(readAddress), ResetTiming.AFTER_NORMAL_CALL_RETURN);
        }
    }
}