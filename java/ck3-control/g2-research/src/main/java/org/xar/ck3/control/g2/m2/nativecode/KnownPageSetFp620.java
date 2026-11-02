package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageFp619;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullPage495Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206;
import org.xar.ck3.research.m1.GovernmentMemoryFillRep207;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;

/**
 * Source-scoped FP carrier for the three Page SET edges (2A3227C, 2A322EE, 2A32325) targeting 4226F10.
 * Reuses mature M1 implementations; no algorithm duplication.
 */
public final class KnownPageSetFp620 {
    private KnownPageSetFp620() { }

    /**
     * Wrapper for a tail call frame carrying the original 185.Tail, direction flag, and pre-call MXCSR state.
     */
    public record TailCall(GovernmentCrtBoundary185Api.Tail original, boolean directionFlagSet, QueueFp604Api.Mxcsr preMxcsr) {
        public TailCall {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);
        }
    }

    /**
     * Functional interface for handling unknown SET tails in the Page context.
     */
    @FunctionalInterface
    public interface TailCalls {
        QueueFp604Api.Outcome tail(TailCall frame);
    }

    /**
     * Private exception used to propagate the Outcome from a tail call back to the invoke handler.
     */
    private static final class TailOutcomeException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Outcome outcome;

        TailOutcomeException(QueueFp604Api.Outcome outcome) {
            this.outcome = outcome;
        }
    }

    /**
     * Binds a KnownPageFp619.Calls handler that routes the specific Page SET edges to the known binder
     * and delegates all other calls to the foreign handler.
     */
    public static KnownPageFp619.Calls bind(
            KnownPageFp619.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            TailCalls unknownSetTails,
            KnownPageFp619.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(unknownSetTails);
        Objects.requireNonNull(foreign);

        return new KnownPageFp619.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(KnownPageFp619.CallFrame fpFrame) {
                Objects.requireNonNull(fpFrame);
                FullPage495Api.CallFrame original495 = fpFrame.original();
                QueueFp604Api.Mxcsr preMxcsr = fpFrame.preMxcsr();

                // Match ONLY original 495 call sites 2A3227C / 2A322EE / 2A32325, kind DIRECT_RVA, target 4226F10
                long site = original495.call().callSiteRva();
                boolean isMatch = (site == 0x2A3227CL || site == 0x2A322EEL || site == 0x2A32325L)
                        && original495.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original495.call().targetBits() == 0x4226F10L;

                if (isMatch) {
                    // Execute mature GovernmentMemoryFill206.execute ONCE with exact child entry, same memory, narrow calls, same budget.

                    // Narrow 185.Calls implementation for the 206 body.
                    GovernmentCrtBoundary185Api.Calls narrowCalls = new GovernmentCrtBoundary185Api.Calls() {
                        @Override
                        public long readGsQword58() {
                            throw new UnsupportedOperationException("GS read not expected in 206");
                        }

                        @Override
                        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                            throw new UnsupportedOperationException("206 has no CALL instructions");
                        }

                        @Override
                        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                            // Select ONLY actual jumpSite 4226F57 / kind DIRECT_RVA / target 4226EF0
                            if (transfer.jumpSiteRva() == 0x4226F57L
                                    && transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                                    && transfer.targetBits() == 0x4226EF0L) {
                                // Execute GovernmentMemoryFillRep207.execute once
                                GovernmentCrtBoundary185Api.NormalReturn nr = GovernmentMemoryFillRep207.execute(
                                        transfer.entry(),
                                        memory,
                                        original495.directionFlagSet(),
                                        budget);
                                return nr;
                            }

                            // Other 206 tails (unknown computed 703B) call unknownSetTails.tail once
                            QueueFp604Api.Outcome outcome = unknownSetTails.tail(new TailCall(
                                    transfer,
                                    original495.directionFlagSet(),
                                    preMxcsr));

                            if (outcome == null) {
                                throw new NullPointerException("Null outcome from unknownSetTails");
                            }

                            // Propagate outcome via exception to bypass legacy NR interface
                            throw new TailOutcomeException(outcome);
                        }
                    };

                    try {
                        // Execute 206
                        GovernmentCrtBoundary185Api.NormalReturn nr = GovernmentMemoryFill206.execute(
                                original495.childEntry(),
                                memory,
                                narrowCalls,
                                budget);

                        // Wrap in Normal with SAME preMxcsr and original direction flag
                        FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(
                                nr,
                                original495.directionFlagSet());

                        // Validate against original 495 frame
                        original495.checkNormalReturn(baseResult);

                        return new QueueFp604Api.Normal(baseResult, preMxcsr);
                    } catch (TailOutcomeException e) {
                        // Return the EXACT offered unknown Tail Outcome
                        QueueFp604Api.Outcome outcome = e.outcome;

                        if (outcome instanceof QueueFp604Api.Normal normal) {
                            // Validate against original 495 frame BEFORE returning
                            original495.checkNormalReturn(normal.base());
                        }

                        return outcome;
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