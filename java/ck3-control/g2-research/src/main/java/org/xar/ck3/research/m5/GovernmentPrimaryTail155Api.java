package org.xar.ck3.research.m5;

import java.util.Objects;

/** Owned exact-bit ports for the complete held [30A3F4D,30A41CE) region. No Game memory. */
public final class GovernmentPrimaryTail155Api {
    private GovernmentPrimaryTail155Api() { }
    public record Bits128(long lowBits, long highBits) { }
    /** All caller-volatile GPR and XMM bits offered to an opaque normal Windows-x64 callee. */
    public record VolatileBits(long raxBits, long rcxBits, long rdxBits,
            long r8Bits, long r9Bits, long r10Bits, long r11Bits,
            Bits128 xmm0, Bits128 xmm1, Bits128 xmm2,
            Bits128 xmm3, Bits128 xmm4, Bits128 xmm5) {
        public VolatileBits {
            Objects.requireNonNull(xmm0); Objects.requireNonNull(xmm1);
            Objects.requireNonNull(xmm2); Objects.requireNonNull(xmm3);
            Objects.requireNonNull(xmm4); Objects.requireNonNull(xmm5);
        }
    }
    /**
     * R12 is zero-extended from savedTlsOffsetDwordBits. R15 low DWORD is read as raw bits.
     * Native-equivalent normal entries retain the held prologue's frame layout/alignment;
     * arbitrary raw entries do not establish a normal native continuation.
     */
    public record Entry(long imageBaseBits, long governmentBits,
            int savedTlsOffsetDwordBits, long savedRsiBits, long savedR15Bits,
            long frameRbpBits, long frameRspBits, long incomingR13Bits,
            long incomingR14Bits, Bits128 incomingXmm6, VolatileBits incomingVolatile) {
        public Entry { Objects.requireNonNull(incomingXmm6); Objects.requireNonNull(incomingVolatile); }
    }
    public record NonvolatileBits(long rbxBits, long rbpBits, long rsiBits, long rdiBits,
            long r12Bits, long r13Bits, long r14Bits, long r15Bits, Bits128 xmm6) {
        public NonvolatileBits { Objects.requireNonNull(xmm6); }
    }
    /** Exact raw register snapshot, not a guessed formal native signature. */
    public record OpaqueCall(long callSiteRva, long targetRva, long rspBits,
            VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public OpaqueCall { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }
    public interface Memory extends GovernmentCaller153Api.Memory {
        void writeQword(long addressBits, long valueBits);
        void writeByte(long addressBits, int lowByteBits);
        /**
         * Exact16-byte snapshot. Padding comes from owned memory, never synthesized zeros.
         * Native MOVAPS/MOVDQA alignment/fault semantics are a normal-entry/port precondition;
         * an implementation claiming those semantics must reject unsupported access there.
         */
        Bits128 read128(long addressBits);
        void write128(long addressBits, Bits128 valueBits);
    }
    public interface Calls {
        long readGsQword58();
        /**
         * Owned callback may alter the shared Memory and returns all represented volatile bits.
         * Normal Windows ABI preservation of supplied nonvolatile state is a port precondition.
         * If its meaning requires unrepresented machine inputs/effects, throw UnsupportedOperationException.
         * In particular8FC920 is NOT silently treated as a zero-argument pure getter.
         */
        VolatileBits invoke(OpaqueCall call);
    }
    public interface LoopBudget {
        /** May throw UnsupportedOperationException; never clamp a signed count or pretend completion. */
        void beforeIteration(long loopHeaderRva, long cursorBits, long fixedEndBits);
    }
    /** Only raw RAX and explicit architectural epilogue reads are reported; no formal return type. */
    public record NormalReturn(long rawRaxBits, long returnRipBits, long callerRspBits,
            NonvolatileBits restoredNonvolatile) {
        public NormalReturn { Objects.requireNonNull(restoredNonvolatile); }
    }
    /** Mechanical local register holder, no target algorithm. */
    public static final class Registers {
        public long rax, rcx, rdx, r8, r9, r10, r11;
        public long rbx, rbp, rsi, rdi, r12, r13, r14, r15, rsp;
        public Bits128 x0, x1, x2, x3, x4, x5, x6;
        public Registers(Entry e) {
            rbp=e.frameRbpBits(); rsp=e.frameRspBits(); rdi=e.governmentBits();
            rsi=e.savedRsiBits(); r12=Integer.toUnsignedLong(e.savedTlsOffsetDwordBits());
            r13=e.incomingR13Bits(); r14=e.incomingR14Bits(); r15=e.savedR15Bits();
            x6=e.incomingXmm6(); apply(e.incomingVolatile());
            // RBX is overwritten by the first tail instruction before any read or call.
        }
        public VolatileBits volatileBits() {
            return new VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,x0,x1,x2,x3,x4,x5);
        }
        public NonvolatileBits nonvolatileBits() {
            return new NonvolatileBits(rbx,rbp,rsi,rdi,r12,r13,r14,r15,x6);
        }
        public void apply(VolatileBits v) {
            Objects.requireNonNull(v); rax=v.raxBits(); rcx=v.rcxBits(); rdx=v.rdxBits();
            r8=v.r8Bits(); r9=v.r9Bits(); r10=v.r10Bits(); r11=v.r11Bits();
            x0=v.xmm0(); x1=v.xmm1(); x2=v.xmm2(); x3=v.xmm3(); x4=v.xmm4(); x5=v.xmm5();
        }
    }
}
