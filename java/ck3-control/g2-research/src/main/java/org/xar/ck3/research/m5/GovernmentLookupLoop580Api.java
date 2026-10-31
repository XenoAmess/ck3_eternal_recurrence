package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owned normal-state boundary for580B, excluding32C3..32D5. No CPU/allocator/Game behavior is invented. */
public final class GovernmentLookupLoop580Api {
    private GovernmentLookupLoop580Api() { }
    /** Raw32 owned observation, not a default/decoded mode or a claim of live CPU availability. */
    public record Mxcsr32(int bits) { }
    public record Entry(GovernmentCompaction160Api.Entry raw, Mxcsr32 mxcsr) {
        public Entry { Objects.requireNonNull(raw);Objects.requireNonNull(mxcsr); }
    }
    /** Normal nextRva33B8 or33C2, full represented GPR/XMM0..6 plus observed FP environment. */
    public record Join(long nextRva, GovernmentCompaction160Api.Entry raw, Mxcsr32 mxcsr) {
        public Join { Objects.requireNonNull(raw);Objects.requireNonNull(mxcsr); }
    }
    public sealed interface Target permits StaticRva, IndirectVa { }
    public record StaticRva(long targetRva) implements Target { }
    /** Value actually read from the call target's owned memory operand, never an RVA. */
    public record IndirectVa(long addressBits) implements Target { }
    public record CallFrame(long callSiteRva,Target target,long frameRspBits,
            VolatileBits volatileBits,NonvolatileBits nonvolatileBits,Mxcsr32 mxcsr) {
        public CallFrame { Objects.requireNonNull(target);Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits);Objects.requireNonNull(mxcsr); }
    }
    public record CallPost(VolatileBits volatileBits,Mxcsr32 mxcsr) {
        public CallPost { Objects.requireNonNull(volatileBits);Objects.requireNonNull(mxcsr); }
    }
    public interface Memory extends GovernmentPrimaryTail155Api.Memory { }
    public interface Calls {
        long readGsQword58();
        /**
         * Exact owned normal call effect; may mutate shared Memory, then supplies ALL volatile bits and MXCSR.
         * Represented nonvolatile GPR/XMM6 preservation is an explicit ABI precondition, not a discovered
         * callee identity/signature. If actual effects/inputs do not fit, throw UnsupportedOperationException.
         * No implicit copying of incoming MXCSR or volatile outputs; nativeEH/unwind is not represented.
         */
        CallPost invoke(CallFrame call);
    }
    public record VectorPost(Bits128 vectorBits,Mxcsr32 mxcsr) {
        public VectorPost { Objects.requireNonNull(vectorBits);Objects.requireNonNull(mxcsr); }
    }
    public record EaxPost(int eaxBits,Mxcsr32 mxcsr) {
        public EaxPost { Objects.requireNonNull(mxcsr); }
    }
    /**
     * Each port denotes ONE exact held instruction's owned normal observation/semantics, not Java float.
     * Supply full raw vector output and MXCSR observation; unsupported rounding, invalid/unmasked faults,
     * denormal/precision effects or other unrepresented behavior must throw, never invent a normal result.
     * Initial MXCSR and literal DWORDs come only from owned Entry/Memory, never a guessed current value.
     * Port implementation is responsible for genuine ISA semantics/observation if claiming them; software
     * witnesses of protocol plumbing do not independently prove Native FP results, masks or exception paths.
     */
    public interface Cpu {
        VectorPost movssMemoryXmm6(long siteRva,int memoryDwordBits,Bits128 beforeXmm6,Mxcsr32 before);
        VectorPost movdXmm0(long siteRva,int ecxBits,Bits128 beforeXmm0,Mxcsr32 before);
        VectorPost cvtdq2psXmm0(long siteRva,Bits128 xmm0,Mxcsr32 before);
        VectorPost mulssXmm0(long siteRva,Bits128 xmm0,Bits128 xmm6,Mxcsr32 before);
        EaxPost cvttss2siEax(long siteRva,Bits128 xmm0,Mxcsr32 before);
    }
    public interface LoopBudget {
        /** Actual31A0 visit; third input is endSLOT ADDRESS, not a permanently frozen end value.
         * Budget may reject finite unsupported work; do not add a phantom native memory read for it. */
        void beforeIteration(long headerRva,long cursorBits,long endSlotAddressBits);
    }
    /** Mechanical raw snapshot helper only; retains incoming RBX/full R12. */
    public static Registers registers(Entry entry) { return GovernmentCompaction160Api.registers(entry.raw()); }
    public static Join join(Entry entry,Registers r,Mxcsr32 mxcsr,long nextRva) {
        return new Join(nextRva,new GovernmentCompaction160Api.Entry(
                entry.raw().imageBaseBits(),r.rsp,r.volatileBits(),r.nonvolatileBits()),mxcsr);
    }
}
