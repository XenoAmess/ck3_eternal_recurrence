package org.xar.ck3.study.m6.poststate243;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Snapshot;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.study.m6.poststate240.PostState240Api.FloatingStages;
import org.xar.ck3.study.m6.poststate240.PostState240Api.FpFrame;
import org.xar.ck3.study.m6.poststate240.PostState240Api.IntegerCompleted;
import org.xar.ck3.study.m6.poststate240.PostState240Api.IntegerResult;
import org.xar.ck3.study.m6.poststate240.PostState240Api.StageStopped;
import org.xar.ck3.study.m6.poststate240.PostState240Api.VectorCompleted;
import org.xar.ck3.study.m6.poststate240.PostState240Api.VectorResult;

/**
 * Thin source-site admission for three owner-qualified opaque SSE operations.
 * No host floating arithmetic, MXCSR default, memory access, body translation or CALL/RET.
 */
public final class OpaqueSseOutcomeProvider243 implements FloatingStages {
    private final FloatingStages qualifiedOperations;

    /**
     * The delegate must supply the complete represented operation result and explicit post
     * environment for the offered current Frame. A value-only legacy Floating is insufficient.
     */
    public OpaqueSseOutcomeProvider243(FloatingStages qualifiedOperations) {
        this.qualifiedOperations=Objects.requireNonNull(qualifiedOperations);
    }

    @Override public VectorResult convertSignedDwords(FpFrame frame) {
        requireSite(frame,0x21A5192L,0xB2EF7DL);
        VectorResult offered=Objects.requireNonNull(qualifiedOperations.convertSignedDwords(frame));
        checkVector(frame,offered,false);
        return offered;
    }

    @Override public VectorResult multiplyLowSingle(FpFrame frame,int multiplierRaw32) {
        requireSite(frame,0x21A5195L,0xB2EF83L);
        VectorResult offered=Objects.requireNonNull(qualifiedOperations.multiplyLowSingle(frame,multiplierRaw32));
        checkVector(frame,offered,true);
        return offered;
    }

    @Override public IntegerResult truncateLowSingle(FpFrame frame) {
        requireSite(frame,0x21A519DL,0xB2EF8BL);
        IntegerResult offered=Objects.requireNonNull(qualifiedOperations.truncateLowSingle(frame));
        if(offered instanceof StageStopped stopped) checkStopScope(frame,stopped.actual());
        else {
            IntegerCompleted completed=(IntegerCompleted)offered;
            checkEnvironment(frame,completed.postDirectionFlagSet(),completed.postMxcsr());
        }
        return offered;
    }

    /**
     * Explicit pre-operation stop for a consumer which has only the old value interface.
     * No old value operation is invoked and no post-MXCSR/DF preservation is guessed.
     */
    public static OpaqueSseOutcomeProvider243 missingPostState() {
        return new OpaqueSseOutcomeProvider243(new FloatingStages() {
            @Override public VectorResult convertSignedDwords(FpFrame frame) {
                return beforeOperation(frame,StopReason.MISSING_POST_STATE);
            }
            @Override public VectorResult multiplyLowSingle(FpFrame frame,int multiplierRaw32) {
                return beforeOperation(frame,StopReason.MISSING_POST_STATE);
            }
            @Override public IntegerResult truncateLowSingle(FpFrame frame) {
                return beforeOperation(frame,StopReason.MISSING_POST_STATE);
            }
        });
    }

    /**
     * Reject before this operation changes registers or environment. The Snapshot is the
     * actual current Frame supplied by the consumer, never the outer function's entry.
     * Architectural conditions need a qualified actual stopped outcome instead.
     */
    public static StageStopped beforeOperation(FpFrame frame,StopReason reason) {
        Objects.requireNonNull(frame);Objects.requireNonNull(reason);
        if(reason==StopReason.ARCHITECTURAL_FP_CONDITION)
            throw new IllegalArgumentException("architectural conditions require an actual qualified stop");
        return new StageStopped(new Stopped(reason,frame.before(),0,frame.originCallSiteRva()));
    }

    private static void requireSite(FpFrame frame,long site715,long siteB2) {
        Objects.requireNonNull(frame);
        long site=frame.before().instructionRva();
        if(site!=site715 && site!=siteB2)
            throw new IllegalArgumentException("operation is outside the two held SSE source sites");
    }

    private static void checkVector(FpFrame frame,VectorResult offered,boolean scalarMultiply) {
        if(offered instanceof StageStopped stopped) checkStopScope(frame,stopped.actual());
        else {
            VectorCompleted completed=(VectorCompleted)offered;
            checkEnvironment(frame,completed.postDirectionFlagSet(),completed.postMxcsr());
            if(scalarMultiply) {
                Bits128 prior=frame.before().currentState().volatileBits().xmm0();
                Bits128 after=completed.xmm0Bits();
                if((prior.lowBits()&0xFFFFFFFF00000000L)!=(after.lowBits()&0xFFFFFFFF00000000L)
                        || prior.highBits()!=after.highBits())
                    throw new IllegalArgumentException("legacy MULSS must preserve XMM0 upper 96 bits");
            }
        }
    }

    private static void checkEnvironment(FpFrame frame,boolean postDF,Mxcsr postMxcsr) {
        Objects.requireNonNull(postMxcsr);
        if(postDF!=frame.before().directionFlagSet())
            throw new IllegalArgumentException("these SSE instructions do not modify DF");
        Mxcsr preMxcsr=frame.before().mxcsr();
        int knownControls=preMxcsr.knownMaskBits()&0xFFC0;
        if((postMxcsr.knownMaskBits()&knownControls)!=knownControls
                || ((preMxcsr.valueBits()^postMxcsr.valueBits())&knownControls)!=0)
            throw new IllegalArgumentException("SSE changed or forgot a known MXCSR control bit");
        // No equality/merge is applied to low-six MXCSR status or to unknown mask bits.
        // In particular the known-control mask 0xFFC0 is not a post-status proof.
    }

    private static void checkStopScope(FpFrame frame,Stopped actual) {
        Objects.requireNonNull(actual);
        Snapshot before=frame.before(),after=actual.snapshot();
        if(after.instructionRva()!=before.instructionRva()
                || actual.originCallSiteRva()!=frame.originCallSiteRva()
                || !after.currentState().equals(before.currentState()))
            throw new IllegalArgumentException("opaque SSE stop is not at this actual instruction frame");
        if(actual.reason()!=StopReason.ARCHITECTURAL_FP_CONDITION
                && !after.mxcsr().equals(before.mxcsr()))
            throw new IllegalArgumentException("unexecuted SSE stop changed MXCSR");
        checkEnvironment(frame,after.directionFlagSet(),after.mxcsr());
        // Keep the exact typed Stopped object and all offered register/status bits intact.
        // No current registers are reconstructed from the old outer Entry or from RAX.
    }
}
