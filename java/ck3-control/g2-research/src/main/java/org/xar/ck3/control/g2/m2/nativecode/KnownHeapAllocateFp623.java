package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageAllocateFp622;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageFp619;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m4.AllocateJump6FullState283;

/**
 * FP/DF carrier for actual Retry CALL 4223BAE -> normal jump283 -> allocate94 producer282.
 * Reuses both integer/stack algorithms once, with explicit outcomes for four inner CALLs.
 * The failure-cell DWORD write belongs to the existing producer; unknown OS callees remain ports.
 * No actual native, OS allocation, Game or complete upper-chain qualification.
 */
public final class KnownHeapAllocateFp623 {
    private KnownHeapAllocateFp623() { }

    /**
     * Wrapper for actual 5B/6B CALL frames, each pushing eight bytes, carrying the original 185.Call, child entry, direction flag, and pre-call MXCSR state.
     */
    public record AllocateCall(
        GovernmentCrtBoundary185Api.Call original,
        GovernmentCrtBoundary185Api.Entry childEntry,
        boolean directionFlagSet,
        QueueFp604Api.Mxcsr preMxcsr
    ) {
        public AllocateCall {
            Objects.requireNonNull(original);
            Objects.requireNonNull(childEntry);
            Objects.requireNonNull(preMxcsr);

            // Validate exact call site, kind, target, and child entry consistency
            long site = original.callSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = original.kind();
            long target = original.targetBits();
            long imageBase = childEntry.imageBaseBits();
            long returnRip;

            if (site == 0x424FDBDL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E250L) {
                    throw new IllegalArgumentException("Invalid call site 424FDBD");
                }
                returnRip = imageBase + 0x424FDC2L;
            } else if (site == 0x424FDC9L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424CFFCL) {
                    throw new IllegalArgumentException("Invalid call site 424FDC9");
                }
                returnRip = imageBase + 0x424FDCEL;
            } else if (site == 0x424FDDEL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424FDDE");
                }
                returnRip = imageBase + 0x424FDE4L;
            } else if (site == 0x424FDEBL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x423B18CL) {
                    throw new IllegalArgumentException("Invalid call site 424FDEB");
                }
                returnRip = imageBase + 0x424FDF0L;
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
            if (site == 0x424FDBDL) {
                return imageBase + 0x424FDC2L;
            } else if (site == 0x424FDC9L) {
                return imageBase + 0x424FDCEL;
            } else if (site == 0x424FDDEL) {
                return imageBase + 0x424FDE4L;
            } else if (site == 0x424FDEBL) {
                return imageBase + 0x424FDF0L;
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
     * Functional interface for handling 283 inner calls.
     */
    @FunctionalInterface
    public interface AllocateCalls {
        QueueFp604Api.Outcome invoke(AllocateCall frame);
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
     * Binds a KnownPageAllocateFp622.RetryCalls handler that routes the specific Retry edge to the known binder
     * and delegates all other calls to the foreign handler.
     */
    public static KnownPageAllocateFp622.RetryCalls bind(
            KnownPageFp619.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            AllocateCalls inner,
            KnownPageAllocateFp622.RetryCalls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(inner);
        Objects.requireNonNull(foreign);

        return new KnownPageAllocateFp622.RetryCalls() {
            @Override
            public QueueFp604Api.Outcome invoke(KnownPageAllocateFp622.RetryCall fpFrame) {
                Objects.requireNonNull(fpFrame);
                GovernmentCrtBoundary185Api.Call original = fpFrame.original();
                QueueFp604Api.Mxcsr preMxcsr = fpFrame.preMxcsr();

                // Match ONLY original Retry call site 4223BAE / kind DIRECT_RVA / target 42420B8
                if (original.callSiteRva() == 0x4223BAEL
                        && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.targetBits() == 0x42420B8L) {

                    // Isolated local MXCSR holder for EACH invoke, initialized to the SAME preMxcsr object.
                    final QueueFp604Api.Mxcsr[] currentMxcsrHolder = new QueueFp604Api.Mxcsr[1];
                    currentMxcsrHolder[0] = preMxcsr;
                    final boolean[] currentDfHolder = new boolean[1];
                    currentDfHolder[0] = fpFrame.directionFlagSet();

                    // Four explicit FP/DF callbacks for the existing normal94 body282.
                    GovernmentCrtBoundary185Api.Calls narrowCalls = new GovernmentCrtBoundary185Api.Calls() {
                        @Override
                        public long readGsQword58() {
                            throw new UnsupportedOperationException("GS read not expected in 283");
                        }

                        @Override
                        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                            // Construct AllocateCall with EXACT originalCall, new 185.Entry, currentDF/SAME currentFP
                            AllocateCall allocateFrame = new AllocateCall(
                                    call,
                                    new GovernmentCrtBoundary185Api.Entry(
                                            fpFrame.childEntry().imageBaseBits(),
                                            call.rspBits() - 8,
                                            call.volatileBits(),
                                            call.nonvolatileBits()),
                                    currentDfHolder[0],
                                    currentMxcsrHolder[0]);

                            // Call inner.invoke ONCE
                            QueueFp604Api.Outcome outcome = inner.invoke(allocateFrame);

                            if (outcome instanceof QueueFp604Api.Normal normal) {
                                // Validate against the AllocateCall frame BEFORE current state update
                                allocateFrame.checkNormalReturn(normal.base());
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
                            throw new UnsupportedOperationException("Tail not expected in 283");
                        }
                    };

                    try {
                        // Execute AllocateJump6FullState283.execute ONCE with exact child entry, same memory, narrow calls, same budget.
                        GovernmentCrtBoundary185Api.NormalReturn nr = AllocateJump6FullState283.execute(
                                fpFrame.childEntry(),
                                memory,
                                narrowCalls,
                                budget);

                        // Wrap in Normal with SAME currentMxcsr and current direction flag
                        FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(
                                nr,
                                currentDfHolder[0]);

                        // Validate against the original outer 622 Retry frame
                        fpFrame.checkNormalReturn(baseResult);

                        return new QueueFp604Api.Normal(baseResult, currentMxcsrHolder[0]);
                    } catch (StoppedOutcomeException e) {
                        // Return the EXACT offered Stopped object.
                        return e.outcome;
                    }
                }

                // All legal nonmatches go ONCE to foreign.invoke(EXACT SAME 622 frame)
                QueueFp604Api.Outcome outcome = foreign.invoke(fpFrame);
                if (outcome == null) {
                    throw new NullPointerException("Null outcome from foreign");
                }
                return outcome;
            }
        };
    }
}