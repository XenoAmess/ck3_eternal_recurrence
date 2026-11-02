package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownHeapAllocateFp623;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageFp619;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m4.Gate47FullState273;

/**
 * FP/DF carrier for actual allocation CALL 424FDC9 -> normal gate47 producer273.
 * Reuses the existing integer/stack algorithm once, with explicit outcomes for two inner CALLs.
 * No full Page/OS/native/Game proof.
 */
public final class KnownAllocateGateFp624 {
    private KnownAllocateGateFp624() { }

    /**
     * Wrapper for actual 47-body CALL frames, each pushing eight bytes, carrying the original 185.Call,
     * child entry, direction flag, and pre-call MXCSR state.
     */
    public record GateCall(
        GovernmentCrtBoundary185Api.Call original,
        GovernmentCrtBoundary185Api.Entry childEntry,
        boolean directionFlagSet,
        QueueFp604Api.Mxcsr preMxcsr
    ) {
        public GateCall {
            Objects.requireNonNull(original);
            Objects.requireNonNull(childEntry);
            Objects.requireNonNull(preMxcsr);

            // Validate exact call site, kind, target, and child entry consistency
            long site = original.callSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = original.kind();
            long target = original.targetBits();
            long imageBase = childEntry.imageBaseBits();
            long returnRip;

            if (site == 0x424D005L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424D02CL) {
                    throw new IllegalArgumentException("Invalid call site 424D005");
                }
                returnRip = imageBase + 0x424D00AL;
            } else if (site == 0x424D012L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424D012");
                }
                returnRip = imageBase + 0x424D018L;
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
            if (site == 0x424D005L) {
                return imageBase + 0x424D00AL;
            } else if (site == 0x424D012L) {
                return imageBase + 0x424D018L;
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
     * Functional interface for handling 273 inner calls.
     */
    @FunctionalInterface
    public interface GateCalls {
        QueueFp604Api.Outcome invoke(GateCall frame);
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
     * Binds a KnownHeapAllocateFp623.AllocateCalls handler that routes the specific Gate edge to the known binder
     * and delegates all other calls to the foreign handler.
     */
    public static KnownHeapAllocateFp623.AllocateCalls bind(
            KnownPageFp619.Memory memory,
            GateCalls inner,
            KnownHeapAllocateFp623.AllocateCalls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(inner);
        Objects.requireNonNull(foreign);

        return new KnownHeapAllocateFp623.AllocateCalls() {
            @Override
            public QueueFp604Api.Outcome invoke(KnownHeapAllocateFp623.AllocateCall fpFrame) {
                Objects.requireNonNull(fpFrame);
                GovernmentCrtBoundary185Api.Call original = fpFrame.original();
                QueueFp604Api.Mxcsr preMxcsr = fpFrame.preMxcsr();

                // Match ONLY original 623 call site 424FDC9 / kind DIRECT_RVA / target 424CFFC
                if (original.callSiteRva() == 0x424FDC9L
                        && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.targetBits() == 0x424CFFCL) {

                    // Isolated local MXCSR holder for EACH invoke, initialized to the SAME preMxcsr object.
                    final QueueFp604Api.Mxcsr[] currentMxcsrHolder = new QueueFp604Api.Mxcsr[1];
                    currentMxcsrHolder[0] = preMxcsr;
                    final boolean[] currentDfHolder = new boolean[1];
                    currentDfHolder[0] = fpFrame.directionFlagSet();

                    // Narrow 185.Calls implementation for the 273 body.
                    GovernmentCrtBoundary185Api.Calls narrowCalls = new GovernmentCrtBoundary185Api.Calls() {
                        @Override
                        public long readGsQword58() {
                            throw new UnsupportedOperationException("GS read not expected in 273");
                        }

                        @Override
                        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                            // Construct GateCall with EXACT originalCall, new 185.Entry, currentDF/SAME currentFP
                            GateCall gateFrame = new GateCall(
                                    call,
                                    new GovernmentCrtBoundary185Api.Entry(
                                            fpFrame.childEntry().imageBaseBits(),
                                            call.rspBits() - 8,
                                            call.volatileBits(),
                                            call.nonvolatileBits()),
                                    currentDfHolder[0],
                                    currentMxcsrHolder[0]);

                            // Call inner.invoke ONCE
                            QueueFp604Api.Outcome outcome = inner.invoke(gateFrame);

                            if (outcome instanceof QueueFp604Api.Normal normal) {
                                // Validate against the GateCall frame BEFORE current state update
                                gateFrame.checkNormalReturn(normal.base());
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
                            throw new UnsupportedOperationException("Tail not expected in 273");
                        }
                    };

                    try {
                        // Execute Gate47FullState273.execute ONCE with exact child entry, same memory, narrow calls.
                        GovernmentCrtBoundary185Api.NormalReturn nr = Gate47FullState273.execute(
                                fpFrame.childEntry(),
                                memory,
                                narrowCalls);

                        // Wrap in Normal with SAME currentMxcsr and current direction flag
                        FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(
                                nr,
                                currentDfHolder[0]);

                        // Validate against the original outer 623 AllocateCall frame
                        fpFrame.checkNormalReturn(baseResult);

                        return new QueueFp604Api.Normal(baseResult, currentMxcsrHolder[0]);
                    } catch (StoppedOutcomeException e) {
                        // Return the EXACT offered Stopped object.
                        return e.outcome;
                    }
                }

                // All legal nonmatches go ONCE to foreign.invoke(EXACT SAME 623 frame)
                QueueFp604Api.Outcome outcome = foreign.invoke(fpFrame);
                if (outcome == null) {
                    throw new NullPointerException("Null outcome from foreign");
                }
                return outcome;
            }
        };
    }
}