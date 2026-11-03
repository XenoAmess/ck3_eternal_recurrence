package org.xar.ck3.study.m6.full238;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

/** New owned proposal for exact 715-byte normal body; no FP environment or hardware ABI assertion. */
public final class TransferFull238Api {
    private TransferFull238Api() { }
    @FunctionalInterface public interface Budget {
        void before(long instructionRva, long cursorBits, long endBits);
    }
    /** Exact represented SSE effects supplied by an owner-qualified environment, otherwise throw. */
    public interface Floating {
        Bits128 convertSignedDwords(Bits128 input);
        Bits128 multiplyLowSingle(Bits128 input, int multiplierRaw32);
        int truncateLowSingle(Bits128 input);
    }
    @FunctionalInterface public interface Self {
        NormalReturn execute(Entry entry);
    }
    /** Shared mutable represented register state only; algorithms belong to the requested blocks. */
    public static final class Frame {
        public final long image, entrySP;
        public final Registers r;
        public final Memory memory;
        public final Calls calls;
        public final Floating floating;
        public final Budget budget;
        public final Self self;
        public Frame(Entry entry, Memory memory, Calls calls, Floating floating, Budget budget, Self self) {
            Objects.requireNonNull(entry);
            image=entry.imageBaseBits(); entrySP=entry.rspBits();
            r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(image,entrySP,entry.volatileBits(),entry.nonvolatileBits()));
            this.memory=Objects.requireNonNull(memory); this.calls=calls; this.floating=floating;
            this.budget=Objects.requireNonNull(budget); this.self=Objects.requireNonNull(self);
        }
        /** Call.rspBits is before the one owned CALL push. Opaque normal ports preserve supplied N. */
        public void indirect(long siteRva, long targetBits) {
            memory.writeQword(r.rsp-0x8L,image+siteRva+0x3L);
            r.apply(calls.invoke(new Call(siteRva,TargetKind.INDIRECT_ABSOLUTE,targetBits,r.rsp,r.volatileBits(),r.nonvolatileBits())));
        }
        /** A known recursive body returns all represented state; do not guess it from RAX. */
        public void recursive(long siteRva) {
            budget.before(siteRva,r.rsp,0L);
            long pre=r.rsp;
            memory.writeQword(pre-0x8L,image+siteRva+0x5L);
            NormalReturn returned=self.execute(new Entry(image,pre-0x8L,r.volatileBits(),r.nonvolatileBits()));
            if(returned.returnRipBits()!=image+siteRva+0x5L || returned.callerRspBits()!=pre)
                throw new UnsupportedOperationException("recursive body did not return to this source continuation");
            r.apply(returned.volatileBits());
            var n=returned.nonvolatileBits();
            r.rbx=n.rbxBits();r.rbp=n.rbpBits();r.rsi=n.rsiBits();r.rdi=n.rdiBits();
            r.r12=n.r12Bits();r.r13=n.r13Bits();r.r14=n.r14Bits();r.r15=n.r15Bits();r.x6=n.xmm6();
            r.rsp=returned.callerRspBits();
        }
    }
}
