package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageFp619;
import org.xar.ck3.control.g2.m2.nativecode.FullPage495Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m4.Retry60NormalFullState284;

/**
 * FP carrier for Page allocator CALL 2A322DB to mature normal60 Retry284.
 * Reuses its represented integer/stack algorithm; both inner CALLs offer explicit FP/DF outcomes.
 * Error CALL/INT3 remains legacy UnexecutedSourcePath. No full Page/OS/native/Game proof.
 */
public final class KnownPageAllocateFp622 {
    private KnownPageAllocateFp622() { }

    /**
     * Wrapper for a 5B CALL frame carrying the original 185.Call, child entry, direction flag, and pre-call MXCSR state.
     */
    public record RetryCall(
        GovernmentCrtBoundary185Api.Call original,
        GovernmentCrtBoundary185Api.Entry childEntry,
        boolean directionFlagSet,
        QueueFp604Api.Mxcsr preMxcsr
    ) {
        public RetryCall {
            Objects.requireNonNull(original);
            Objects.requireNonNull(childEntry);
            Objects.requireNonNull(preMxcsr);

            // Validate exact call site, kind, target, and child entry consistency
            long site = original.callSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = original.kind();
            long target = original.targetBits();
            long imageBase = childEntry.imageBaseBits();
            long returnRip;

            if (site == 0x4223BAEL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x42420B8L) {
                    throw new IllegalArgumentException("Invalid call site 4223BAE");
                }
                returnRip = imageBase + 0x4223BB3L;
            } else if (site == 0x4223BA2L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424CFFCL) {
                    throw new IllegalArgumentException("Invalid call site 4223BA2");
                }
                returnRip = imageBase + 0x4223BA7L;
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }

            // Child RSP must be exactly 8 bytes below call RSP (return address push)
            if (childEntry.rspBits() != original.rspBits() - 8) {
                throw new IllegalArgumentException("Child RSP mismatch");
            }

            // Child volatile and nonvolatile bits must match the call's pre-state
            if (!childEntry.volatileBits().equals(original.volatileBits())) {
                throw new IllegalArgumentException("Child V mismatch");
            }
            if (!childEntry.nonvolatileBits().equals(original.nonvolatileBits())) {
                throw new IllegalArgumentException("Child N mismatch");
            }
        }

        public long returnRipBits() {
            long site = original.callSiteRva();
            long imageBase = childEntry.imageBaseBits();
            if (site == 0x4223BAEL) {
                return imageBase + 0x4223BB3L;
            } else if (site == 0x4223BA2L) {
                return imageBase + 0x4223BA7L;
            } else {
                throw new IllegalStateException("Unknown call site");
            }
        }

        public void checkNormalReturn(FullCopy437Api.CallResult result) {
            if (result.normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (result.normalReturn().callerRspBits() != this.original.rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!result.normalReturn().nonvolatileBits().equals(this.original.nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Functional interface for handling 284 inner calls.
     */
    @FunctionalInterface
    public interface RetryCalls {
        QueueFp604Api.Outcome invoke(RetryCall frame);
    }

    /**
     * Private exception used to propagate the Stopped outcome from a callback back to execute.
     * This allows the bridge to intercept the stop and return the Outcome directly without
     * manufacturing a legacy normal return or processing continuation.
     */
    private static final class StoppedOutcomeException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped outcome;

        StoppedOutcomeException(QueueFp604Api.Stopped outcome) {
            this.outcome = outcome;
        }
    }

    /**
     * Binds a KnownPageFp619.Calls handler that routes the specific Page edge to the known binder
     * and delegates all other calls to the foreign handler.
     */
    public static KnownPageFp619.Calls bind(
            KnownPageFp619.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            RetryCalls inner,
            KnownPageFp619.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(inner);
        Objects.requireNonNull(foreign);

        return new KnownPageFp619.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(KnownPageFp619.CallFrame fpFrame) {
                Objects.requireNonNull(fpFrame);
                FullPage495Api.CallFrame original495 = fpFrame.original();
                QueueFp604Api.Mxcsr preMxcsr = fpFrame.preMxcsr();

                // Match ONLY original 495 call site 2A322DB / kind DIRECT_RVA / target 4223B94
                if (original495.call().callSiteRva() == 0x2A322DBL
                        && original495.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original495.call().targetBits() == 0x4223B94L) {

                    // Isolated local MXCSR holder for EACH invoke, initialized to the SAME preMxcsr object.
                    final QueueFp604Api.Mxcsr[] currentMxcsrHolder = new QueueFp604Api.Mxcsr[1];
                    currentMxcsrHolder[0] = preMxcsr;
                    final boolean[] currentDfHolder = new boolean[1];
                    currentDfHolder[0] = original495.directionFlagSet();

                    // Narrow 185.Calls implementation for the 284 body.
                    GovernmentCrtBoundary185Api.Calls narrowCalls = new GovernmentCrtBoundary185Api.Calls() {
                        @Override
                        public long readGsQword58() {
                            throw new UnsupportedOperationException("GS read not expected in 284");
                        }

                        @Override
                        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                            // Construct RetryCall with EXACT originalCall, new 185.Entry, currentDF/SAME currentFP
                            RetryCall retryFrame = new RetryCall(
                                    call,
                                    new GovernmentCrtBoundary185Api.Entry(
                                            original495.childEntry().imageBaseBits(),
                                            call.rspBits() - 8,
                                            call.volatileBits(),
                                            call.nonvolatileBits()),
                                    currentDfHolder[0],
                                    currentMxcsrHolder[0]);

                            // Call inner.invoke ONCE
                            QueueFp604Api.Outcome outcome = inner.invoke(retryFrame);

                            if (outcome instanceof QueueFp604Api.Normal normal) {
                                // Validate against the RetryCall frame BEFORE current state update
                                retryFrame.checkNormalReturn(normal.base());
                                // Retain SAME postMxcsr
                                currentMxcsrHolder[0] = normal.postMxcsr();
                                // Update currentDF from actual postDirectionFlagSet
                                currentDfHolder[0] = normal.base().postDirectionFlagSet();
                                // Return SAME normal.base() with actual full NR/postDF
                                return normal.base().normalReturn().volatileBits();
                            } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                                // Abort immediately to execute's outer boundary.
                                throw new StoppedOutcomeException(stopped);
                            } else {
                                throw new NullPointerException("Null outcome from inner");
                            }
                        }

                        @Override
                        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                            throw new UnsupportedOperationException("Tail not expected in 284");
                        }
                    };

                    try {
                        // Execute Retry60NormalFullState284.execute ONCE with exact child entry, same memory, narrow calls, same budget.
                        GovernmentCrtBoundary185Api.NormalReturn nr = Retry60NormalFullState284.execute(
                                original495.childEntry(),
                                memory,
                                narrowCalls,
                                budget);

                        // Wrap in Normal with SAME currentMxcsr and current direction flag
                        FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(
                                nr,
                                currentDfHolder[0]);

                        // Validate against original 495 frame
                        original495.checkNormalReturn(baseResult);

                        return new QueueFp604Api.Normal(baseResult, currentMxcsrHolder[0]);
                    } catch (StoppedOutcomeException e) {
                        // Return the EXACT offered Stopped object.
                        return e.outcome;
                    }
                }

                // All legal nonmatches go ONCE to foreign.invoke(EXACT SAME 619 frame)
                QueueFp604Api.Outcome outcome = foreign.invoke(fpFrame);
                if (outcome == null) {
                    throw new NullPointerException("Null outcome from foreign");
                }
                return outcome;
            }
        };
    }
}