package org.xar.ck3.study.m6.full238;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate240.FrameCallHooks240;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;

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
        private PostState240Api.FrameBindings postState;

        /** New typed-entry path only; the Context must share this exact register holder. */
        private void installPostState(PostState240Api.FrameBindings actual) {
            Objects.requireNonNull(actual);
            if (postState != null || !actual.context().boundTo(image,r))
                throw new IllegalArgumentException("Post-state context binding mismatch");
            postState=actual;
        }
        public PostState240Api.Context postStateContext() {
            return Objects.requireNonNull(postState).context();
        }
        public void beforeInstruction(long actualRva) {
            if(postState!=null) postState.context().beforeInstruction(actualRva);
        }
        /** Source direct helper retains its old path unless this typed path owns the CALL. */
        public boolean directIfPostState(long actualSiteRva,long targetRva) {
            if(postState==null) return false;
            postState.context().beforeInstruction(actualSiteRva);
            Objects.requireNonNull(postState.callHooks()).direct(actualSiteRva,targetRva);
            return true;
        }
        public void convertSignedDwords(long actualRva) {
            if(postState==null) { r.x0=floating.convertSignedDwords(r.x0); return; }
            var before=postState.context().fpFrame(actualRva);
            var result=Objects.requireNonNull(postState.floatingStages()).convertSignedDwords(before);
            postState.context().acceptVector(before,result);
        }
        public void multiplyLowSingle(long actualRva,int actualMultiplierRaw32) {
            if(postState==null) { r.x0=floating.multiplyLowSingle(r.x0,actualMultiplierRaw32); return; }
            var before=postState.context().fpFrame(actualRva);
            var result=Objects.requireNonNull(postState.floatingStages()).multiplyLowSingle(before,actualMultiplierRaw32);
            postState.context().acceptVector(before,result);
        }
        public void truncateLowSingle(long actualRva) {
            if(postState==null) { r.rax=Integer.toUnsignedLong(floating.truncateLowSingle(r.x0)); return; }
            var before=postState.context().fpFrame(actualRva);
            var result=Objects.requireNonNull(postState.floatingStages()).truncateLowSingle(before);
            postState.context().acceptInteger(before,result);
        }
        public Frame(Entry entry, Memory memory, Calls calls, Floating floating, Budget budget, Self self) {
            Objects.requireNonNull(entry);
            image=entry.imageBaseBits(); entrySP=entry.rspBits();
            r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(image,entrySP,entry.volatileBits(),entry.nonvolatileBits()));
            this.memory=Objects.requireNonNull(memory); this.calls=calls; this.floating=floating;
            this.budget=Objects.requireNonNull(budget); this.self=Objects.requireNonNull(self);
        }
        /** Explicit whole-Outcome mode; no legacy NR-to-Outcome preservation adapter is installed. */
        public Frame(PostState240Api.Input input, Memory memory,
                PostState240Api.FloatingStages floatingStages, Budget budget,
                CallOutcome242Api.OutcomePort opaqueEffects,
                PostState240Api.KnownEntryRegistry knownEntries, long ownerEntryRva) {
            this(Objects.requireNonNull(input).entry(),memory,null,null,budget,
                    child -> { throw new UnsupportedOperationException("Typed recursive CALL must use its explicit registry"); });
            Objects.requireNonNull(floatingStages);
            Objects.requireNonNull(opaqueEffects);
            Objects.requireNonNull(knownEntries);
            PostState240Api.Context context=new PostState240Api.Context(image,r,
                    input.directionFlagSet(),input.mxcsr(),ownerEntryRva,input.originCallSiteRva());
            CallOutcome242Api.Ports ports=new CallOutcome242Api.Ports(opaqueEffects,
                    FrameCallHooks240.knownEntries(memory,knownEntries.whole715(),
                            knownEntries.wholeMove4(),knownEntries.wholeSwap4()));
            installPostState(new PostState240Api.FrameBindings(context,floatingStages,
                    new FrameCallHooks240(ownerEntryRva,context,memory,ports)));
        }
        /** Call.rspBits is before the one owned CALL push. Opaque normal ports preserve supplied N. */
        public void indirect(long siteRva, long targetBits) {
            if(postState!=null) {
                postState.context().beforeInstruction(siteRva);
                Objects.requireNonNull(postState.callHooks()).indirect(siteRva,targetBits);
                return;
            }
            memory.writeQword(r.rsp-0x8L,image+siteRva+0x3L);
            r.apply(calls.invoke(new Call(siteRva,TargetKind.INDIRECT_ABSOLUTE,targetBits,r.rsp,r.volatileBits(),r.nonvolatileBits())));
        }
        /** A known recursive body returns all represented state; do not guess it from RAX. */
        public void recursive(long siteRva) {
            budget.before(siteRva,r.rsp,0L);
            if(postState!=null) {
                postState.context().beforeInstruction(siteRva);
                Objects.requireNonNull(postState.callHooks()).recursive(siteRva);
                return;
            }
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
