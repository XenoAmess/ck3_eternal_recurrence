package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.study.m6.full224.DefaultObject185Wrappers224;

/**
 * Real new224 scope: existing185 REPRESENTED normal state, not full hardwareABI.
 * Actual GovernmentCrtBoundary185Api.Entry supplies image, actual postCALL entrySP, all7V-GPR/XMM0..5 and8N-GPR/XMM6.
 * This carrier adds explicit DF/MXCSR; RFLAGS/XMM7..15/EH/hardware stack faults remain outside its API.
 */
public final class DefaultAllocateWithFp648 {
    private DefaultAllocateWithFp648() { }

    /**
     * Actual 18B8571D0: startSP=s, SUB RSP0x28=>pre=s-0x28; MOV RCX,RDX only;
     * ownedCALL at0x8571D7 writes memory.writeQword(pre-0x8,image+0x8571DC) exactlyonce,
     * then calls.invoke(new185.Call(0x8571D7,DIRECT_RVA,0x4223B94,pre,currentV,currentN)).
     * TargetBits is RVA forDIRECT_RVA, not image+RVA.
     * Call.rsp is PRE-CALL; port owns calleeRET and returns all represented actualV, while normalport preserves providedN.
     * Apply all returnedV. Source then ADD RSP0x28 and RET: freshreadQword at original s, callerSP=s+0x8, preserve all actual representedN.
     * No guessed childreturnV or extra stackpush/pop.
     */
    public static QueueFp604Api.Outcome fromSlot08(DefaultStaticFp648Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory,
            DefaultStaticFp648Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        boolean directionFlagSet = input.directionFlagSet();
        QueueFp604Api.Mxcsr mxcsr = input.mxcsr();
        long image = entry.imageBaseBits();

        // Adapter to bridge old 185 Calls interface to new 648 Calls interface
        final class Adapter implements GovernmentCrtBoundary185Api.Calls {
            private final DefaultStaticFp648Api.Calls newCalls;
            private final long image;
            private final boolean preDF;
            private final QueueFp604Api.Mxcsr preMxcsr;
            private volatile boolean stopped = false;
            private volatile QueueFp604Api.Stopped stoppedOutcome;
            private volatile boolean finalDF;
            private volatile QueueFp604Api.Mxcsr finalMxcsr;

            Adapter(DefaultStaticFp648Api.Calls newCalls, long image, boolean preDF, QueueFp604Api.Mxcsr preMxcsr) {
                this.newCalls = newCalls;
                this.image = image;
                this.preDF = preDF;
                this.preMxcsr = preMxcsr;
                this.finalDF = preDF;
                this.finalMxcsr = preMxcsr;
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (stopped) {
                    throw new IllegalStateException("Execution stopped by foreign outcome");
                }

                // Construct child entry for the call frame
                // Call.rsp is PRE-CALL. Child entry rsp is call.rsp - 8 (after push)
                long childRsp = call.rspBits() - 8L;
                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                        image,
                        childRsp,
                        call.volatileBits(),
                        call.nonvolatileBits()
                );

                // Construct new CallFrame
                // returnRipBits = image + 0x8571DC
                long returnRip = image + 0x8571DCL;
                DefaultStaticFp648Api.CallFrame frame = new DefaultStaticFp648Api.CallFrame(
                        call,
                        childEntry,
                        preDF,
                        preMxcsr,
                        5,
                        returnRip
                );

                // Invoke new calls
                QueueFp604Api.Outcome outcome = newCalls.invoke(frame);

                if (outcome instanceof QueueFp604Api.Stopped) {
                    stopped = true;
                    stoppedOutcome = (QueueFp604Api.Stopped) outcome;
                    throw new StoppedCarrier(stoppedOutcome);
                }

                if (outcome instanceof QueueFp604Api.Normal) {
                    QueueFp604Api.Normal normal = (QueueFp604Api.Normal) outcome;

                    // Validate normal return using frame guard
                    frame.checkNormalReturn(normal);

                    // Update final DF/MXCSR from the validated normal outcome
                    this.finalDF = normal.base().postDirectionFlagSet();
                    this.finalMxcsr = normal.postMxcsr();

                    // Extract volatile bits from the normal return
                    GovernmentCrtBoundary185Api.NormalReturn nr = normal.base().normalReturn();
                    return nr.volatileBits();
                }

                throw new IllegalStateException("Unknown outcome type");
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                throw new UnsupportedOperationException("Tail not expected in fromSlot08");
            }

            @Override
            public long readGsQword58() {
                throw new UnsupportedOperationException("readGsQword58 not expected in fromSlot08");
            }
        }

        Adapter adapter = new Adapter(calls, image, directionFlagSet, mxcsr);

        try {
            // Delegate to old wrapper exactly once
            GovernmentCrtBoundary185Api.NormalReturn oldNR = DefaultObject185Wrappers224.fromSlot08(
                    entry, memory, adapter);

            // Construct the final Normal outcome wrapping old body result with last validated DF/FP
            FullCopy437Api.CallResult callResult = new FullCopy437Api.CallResult(
                    oldNR,
                    adapter.finalDF
            );

            QueueFp604Api.Normal finalNormal = new QueueFp604Api.Normal(
                    callResult,
                    adapter.finalMxcsr
            );

            return finalNormal;

        } catch (StoppedCarrier e) {
            // Return the stopped outcome directly, preserving identity
            return e.getStoppedOutcome();
        }
    }

    private static class StoppedCarrier extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private transient QueueFp604Api.Stopped stoppedOutcome;

        StoppedCarrier(QueueFp604Api.Stopped stoppedOutcome) {
            this.stoppedOutcome = stoppedOutcome;
        }

        QueueFp604Api.Stopped getStoppedOutcome() {
            return stoppedOutcome;
        }
    }
}