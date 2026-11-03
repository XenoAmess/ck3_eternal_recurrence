package org.xar.ck3.study.m6.poststate242;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Held715/B2 CALL frames with explicit post-state Outcomes; no child algorithm or FP emulation. */
public final class CallOutcome242Api {
    private CallOutcome242Api() { }

    public enum NormalRule {
        /** Ordinary opaque normal port must preserve its supplied whole N. */
        OPAQUE_PRESERVES_N,
        /** Known source body returns actual whole N, including fresh saved-slot aliases. */
        KNOWN_ACTUAL_N
    }

    /** Direct target is an RVA. Indirect target is resolved by genuine source before this boundary. */
    public record SourceSite(long ownerEntryRva,long callSiteRva,
            GovernmentCrtBoundary185Api.TargetKind kind,int instructionLength,
            long directTargetRva,NormalRule normalRule) {
        public SourceSite {
            Objects.requireNonNull(kind);Objects.requireNonNull(normalRule);
            if(kind==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && instructionLength!=5)
                throw new IllegalArgumentException("Held direct CALL must be five bytes");
            if(kind==GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE && instructionLength!=3)
                throw new IllegalArgumentException("Held indirect CALL must be three bytes");
        }
    }

    /** call.RSP is the actual caller preSP; childEntry.RSP is after the single owned push. */
    public record CallFrame(long ownerEntryRva,long imageBaseBits,
            GovernmentCrtBoundary185Api.Call call,
            GovernmentCrtBoundary185Api.Entry childEntry,
            boolean preDirectionFlagSet,QueueFp604Api.Mxcsr preMxcsr,
            int instructionLength,long returnRipBits,NormalRule normalRule) {
        public CallFrame {
            Objects.requireNonNull(call);Objects.requireNonNull(childEntry);
            Objects.requireNonNull(preMxcsr);Objects.requireNonNull(normalRule);
            SourceSite source=CallOutcome242Sites.require(ownerEntryRva,call.callSiteRva());
            if(childEntry.imageBaseBits()!=imageBaseBits)
                throw new IllegalArgumentException("Child image mismatch");
            if(childEntry.rspBits()!=call.rspBits()-8L)
                throw new IllegalArgumentException("Child RSP is not actual post-push preSP-8");
            if(!childEntry.volatileBits().equals(call.volatileBits()))
                throw new IllegalArgumentException("Child whole V mismatch");
            if(!childEntry.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Child whole N mismatch");
            if(call.kind()!=source.kind() || instructionLength!=source.instructionLength())
                throw new IllegalArgumentException("Held source CALL kind/length mismatch");
            if(normalRule!=source.normalRule())
                throw new IllegalArgumentException("Held source normal-return rule mismatch");
            if(call.kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits()!=source.directTargetRva())
                throw new IllegalArgumentException("Held source direct target RVA mismatch");
            if(returnRipBits!=imageBaseBits+call.callSiteRva()+instructionLength)
                throw new IllegalArgumentException("Actual source continuation RIP mismatch");
        }

        /** Validate before applying any Normal; post DF and MXCSR are neither coerced nor discarded. */
        public void checkNormalReturn(QueueFp604Api.Normal actual) {
            Objects.requireNonNull(actual);
            GovernmentCrtBoundary185Api.NormalReturn nr=actual.base().normalReturn();
            if(nr.returnRipBits()!=returnRipBits)
                throw new IllegalArgumentException("Normal return RIP mismatch");
            if(nr.callerRspBits()!=call.rspBits())
                throw new IllegalArgumentException("Normal caller RSP mismatch");
            if(normalRule==NormalRule.OPAQUE_PRESERVES_N
                    && !nr.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Opaque normal port did not preserve whole N");
            // KNOWN_ACTUAL_N deliberately accepts actual NR.N, not a fabricated copy of pre.N.
        }
    }

    @FunctionalInterface
    public interface OutcomePort {
        /** Same RAM is supplied by provider construction. Unknown semantics require an explicit truthful stop. */
        QueueFp604Api.Outcome invoke(CallFrame actualFrame);
    }

    /** No legacy scalar-return adapter or implicit post-state preservation is installed. */
    public record Ports(OutcomePort opaque,OutcomePort known) {
        public Ports { Objects.requireNonNull(opaque);Objects.requireNonNull(known); }
    }
}
