package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.SlotProducerGrowthWithFp618;
import org.xar.ck3.control.g2.m2.nativecode.FullPage495Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Source-scoped FP carrier for the complete 381-byte Page function at RVA 0x2A321F0.
 * Reuses the exact existing producer; no copying or reimplementing its GPR/stack/CALL/RET algorithm.
 * Scoped ONLY to actual complete 381. No claim runtime loading, unknownallocator/freebody/currentNativeMXCSR/CPUOS/Native172samecall16+4/Game/performance.
 */
public final class KnownPageFp619 {
    private KnownPageFp619() { }

    /**
     * Union of memory interfaces required for the full state execution.
     * Ensures all operations address the same shared byte storage.
     */
    public interface Memory extends SlotProducerGrowthWithFp618.Memory, FullPage495Api.Memory {
    }

    /**
     * Call frame wrapper carrying original 495 CallFrame and pre-call MXCSR state.
     */
    public record CallFrame(FullPage495Api.CallFrame original, QueueFp604Api.Mxcsr preMxcsr) {
        public CallFrame {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);
        }
    }

    /**
     * Functional interface for handling calls in the 495 context.
     */
    @FunctionalInterface
    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
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
     * Binds a SlotProducerGrowthWithFp618.Calls handler that routes the specific Page edge to the known binder
     * and delegates all other calls to the foreign handler.
     */
    public static SlotProducerGrowthWithFp618.Calls bind(
            Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Calls pageCalls,
            SlotProducerGrowthWithFp618.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(pageCalls);
        Objects.requireNonNull(foreign);

        return new SlotProducerGrowthWithFp618.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(SlotProducerGrowthWithFp618.CallFrame fpFrame) {
                Objects.requireNonNull(fpFrame);
                FullSlotProducer479Api.CallFrame original479 = fpFrame.original();
                QueueFp604Api.Mxcsr preMxcsr = fpFrame.preMxcsr();

                // Match ONLY original 479 call site 2A327E7 / kind DIRECT_RVA / target 2A321F0
                if (original479.call().callSiteRva() == 0x2A327E7L
                        && original479.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original479.call().targetBits() == 0x2A321F0L) {

                    // Construct 495.Input from EXACT original479.childEntry(), actual original479.directionFlagSet(), SAME bound budget
                    FullPage495Api.Input pageInput = new FullPage495Api.Input(
                            original479.childEntry(),
                            original479.directionFlagSet(),
                            budget);

                    // Isolated local MXCSR holder for EACH invoke, initialized to the SAME preMxcsr object.
                    final QueueFp604Api.Mxcsr[] currentMxcsrHolder = new QueueFp604Api.Mxcsr[1];
                    currentMxcsrHolder[0] = preMxcsr;

                    // Narrow 495.Calls implementation that handles the specific Page edge and delegates others.
                    FullPage495Api.Calls narrowCalls = new FullPage495Api.Calls() {
                        @Override
                        public FullCopy437Api.CallResult invoke(FullPage495Api.CallFrame frame) {
                            Objects.requireNonNull(frame);

                            // All 495 callbacks go ONCE to pageCalls.invoke(new 619.CallFrame(EXACT actual 495 frame, SAME current FP)).
                            CallFrame wrappedFrame = new CallFrame(frame, currentMxcsrHolder[0]);
                            QueueFp604Api.Outcome outcome = pageCalls.invoke(wrappedFrame);

                            if (outcome instanceof QueueFp604Api.Normal normal) {
                                // Validate against the original 495 frame BEFORE current state update
                                frame.checkNormalReturn(normal.base());
                                // Retain SAME postMxcsr
                                currentMxcsrHolder[0] = normal.postMxcsr();
                                // Return SAME normal.base() with actual full NR/postDF
                                return normal.base();
                            } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                                // Abort immediately to execute's outer boundary.
                                throw new StoppedOutcomeException(stopped);
                            } else {
                                throw new NullPointerException("Null outcome from pageCalls");
                            }
                        }
                    };

                    try {
                        // Execute supplied PendingPageReserveFullState2A321F0.execute ONCE.
                        FullCopy437Api.CallResult result = PendingPageReserveFullState2A321F0.execute(
                                pageInput,
                                memory,
                                narrowCalls);

                        // On final old 381 normal return, original 479 frame checkNormalReturn(SAME old result) before wrapping new QueueFP.Normal.
                        original479.checkNormalReturn(result);
                        return new QueueFp604Api.Normal(result, currentMxcsrHolder[0]);
                    } catch (StoppedOutcomeException e) {
                        // Return the EXACT offered Stopped object.
                        return e.outcome;
                    }
                }

                // All nonmatches go ONCE to foreign.invoke(EXACT SAME 618 frame), returning EXACT offered Normal/Stopped Outcome object.
                QueueFp604Api.Outcome outcome = foreign.invoke(fpFrame);
                if (outcome == null) {
                    throw new NullPointerException("Null outcome from foreign");
                }
                return outcome;
            }
        };
    }
}