package org.xar.ck3.study.m6.posterror256;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentErrorCell204;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;

/**
 * Whole entry executor for the actual error cell 423B18C.
 * Reuses GovernmentErrorCell204 and KnownAllocateErrorFp625.ErrorCalls.
 * No new algorithm, no state repair, no Game/native proof.
 */
public final class Error32PostState256 implements PostState240Api.EntryExecutor {
    private final KnownAllocateErrorFp625.ErrorCalls childCalls;

    public Error32PostState256(KnownAllocateErrorFp625.ErrorCalls childCalls) {
        this.childCalls = Objects.requireNonNull(childCalls);
    }

    @Override
    public QueueFp604Api.Outcome execute(
            PostState240Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);

        // Mutable state holders for the current invocation
        final boolean[] currentDf = new boolean[1];
        currentDf[0] = input.directionFlagSet();
        final QueueFp604Api.Mxcsr[] currentMxcsr = new QueueFp604Api.Mxcsr[1];
        currentMxcsr[0] = input.mxcsr();

        // Narrow 185.Calls implementation for the 204 body
        GovernmentCrtBoundary185Api.Calls narrowCalls = new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public long readGsQword58() {
                throw new UnsupportedOperationException("GS read not expected in 204");
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                throw new UnsupportedOperationException("Tail not expected in 204");
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                // Construct ErrorCall with EXACT originalCall, new 185.Entry, currentDF/SAME currentFP
                KnownAllocateErrorFp625.ErrorCall errorFrame = new KnownAllocateErrorFp625.ErrorCall(
                        call,
                        new GovernmentCrtBoundary185Api.Entry(
                                input.entry().imageBaseBits(),
                                call.rspBits() - 8,
                                call.volatileBits(),
                                call.nonvolatileBits()),
                        currentDf[0],
                        currentMxcsr[0]);

                // Call childCalls.invoke ONCE
                QueueFp604Api.Outcome outcome = childCalls.invoke(errorFrame);

                if (outcome instanceof QueueFp604Api.Normal normal) {
                    // Validate against the ErrorCall frame BEFORE current state update
                    errorFrame.checkNormalReturn(normal.base());
                    // Retain SAME postMxcsr
                    currentMxcsr[0] = normal.postMxcsr();
                    // Update currentDF from actual postDirectionFlagSet
                    currentDf[0] = normal.base().postDirectionFlagSet();
                    // Return SAME normal.base() with actual full NR/postDF
                    return normal.base().normalReturn().volatileBits();
                } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                    // Abort immediately to execute's outer boundary.
                    throw new StoppedOutcomeException(stopped);
                } else {
                    throw new NullPointerException("Null outcome from childCalls");
                }
            }
        };

        try {
            // Execute GovernmentErrorCell204.execute ONCE with exact child entry, same memory, narrow calls.
            GovernmentCrtBoundary185Api.NormalReturn nr = GovernmentErrorCell204.execute(
                    input.entry(),
                    memory,
                    narrowCalls);

            // Wrap in Normal with SAME currentMxcsr and current direction flag
            FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(
                    nr,
                    currentDf[0]);

            return new QueueFp604Api.Normal(baseResult, currentMxcsr[0]);
        } catch (StoppedOutcomeException e) {
            // Return the EXACT offered Stopped object.
            return e.outcome;
        }
    }

    /**
     * Private exception used to propagate the Stopped outcome from a callback back to execute.
     */
    private static final class StoppedOutcomeException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped outcome;

        StoppedOutcomeException(QueueFp604Api.Stopped outcome) {
            this.outcome = outcome;
        }
    }
}