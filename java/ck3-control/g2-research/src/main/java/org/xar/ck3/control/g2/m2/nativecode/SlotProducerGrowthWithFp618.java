package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullSlotProducer479Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.SlotReserveWithFp615;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.KnownSetFp617;
import org.xar.ck3.control.g2.m2.nativecode.KnownRepFpTail614;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotProducerFullState2A32770;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Scoped FP carrier for the complete 470B slot producer 2A32770.
 * Reuses mature implementations for nested reserve/SET/COPY/REP paths.
 * No new algorithm, no Game/native proof, no state repair.
 */
public final class SlotProducerGrowthWithFp618 {
    private SlotProducerGrowthWithFp618() { }

    /**
     * Input wrapper carrying base 479 Input and explicit MXCSR.
     */
    public record Input(FullSlotProducer479Api.Input base, QueueFp604Api.Mxcsr preMxcsr) {
        public Input {
            Objects.requireNonNull(base);
            Objects.requireNonNull(preMxcsr);
        }
    }

    /**
     * Union of memory interfaces required for the full state execution.
     */
    public interface Memory extends FullSlotProducer479Api.Memory, SlotReserveWithFp615.Memory {
    }

    /**
     * Call frame wrapper carrying original 479 CallFrame and pre-call MXCSR state.
     */
    public record CallFrame(FullSlotProducer479Api.CallFrame original, QueueFp604Api.Mxcsr preMxcsr) {
        public CallFrame {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);
        }
    }

    /**
     * Functional interface for handling calls in the 479 context.
     */
    @FunctionalInterface
    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
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

    /**
     * Executes the 479 logic with FP awareness.
     * @param input The FP input containing the base FullSlotProducer479Api.Input and MXCSR state.
     * @param memory The owned memory view.
     * @param otherProducerCalls The handler for non-reserve calls (page/context/init).
     * @param reserveOtherCalls The handler for non-SET calls in the reserve context.
     * @param unknownCopyTails The handler for unknown COPY tails.
     * @param unknownSetTails The handler for unknown SET tails.
     * @return The Outcome (Normal or Stopped) resulting from the execution.
     */
    public static QueueFp604Api.Outcome execute(
            Input input,
            Memory memory,
            Calls otherProducerCalls,
            SlotReserveWithFp615.Calls reserveOtherCalls,
            FullCopyWithFp613.TailCalls unknownCopyTails,
            KnownSetFp617.TailCalls unknownSetTails) {

        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(otherProducerCalls);
        Objects.requireNonNull(reserveOtherCalls);
        Objects.requireNonNull(unknownCopyTails);
        Objects.requireNonNull(unknownSetTails);

        // Isolated local MXCSR holder for EACH execute, initialized to the SAME input.preMxcsr object.
        final QueueFp604Api.Mxcsr[] currentMxcsrHolder = new QueueFp604Api.Mxcsr[1];
        currentMxcsrHolder[0] = input.preMxcsr();

        // Narrow 479.Calls implementation that handles the specific reserve call and delegates others.
        FullSlotProducer479Api.Calls narrowCalls = new FullSlotProducer479Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(FullSlotProducer479Api.CallFrame frame) {
                Objects.requireNonNull(frame);

                // Match ONLY original 479 call site 2A327CE / kind DIRECT_RVA / target 1ACDFB0
                if (frame.call().callSiteRva() == 0x2A327CEL
                        && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && frame.call().targetBits() == 0x1ACDFB0L) {

                    // Construct 412.Input from EXACT frame.childEntry(), actual frame.directionFlagSet(), ORIGINAL input.base().budget()
                    PendingSlotCapacityFullState412Api.Input nested412Input = new PendingSlotCapacityFullState412Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            input.base().budget());

                    // Construct 615.Input with nested412Input and SAME currentMxcsr
                    SlotReserveWithFp615.Input nested615Input = new SlotReserveWithFp615.Input(
                            nested412Input,
                            currentMxcsrHolder[0]);

                    // Bind KnownSetFp617 with SAME Memory, SAME budget, unknownSetTails, reserveOtherCalls
                    SlotReserveWithFp615.Calls knownSetCalls = KnownSetFp617.bind(
                            memory,
                            input.base().budget(),
                            unknownSetTails,
                            reserveOtherCalls);

                    // Bind KnownRepFpTail614 with SAME Memory, SAME budget, unknownCopyTails
                    FullCopyWithFp613.TailCalls knownRepTails = KnownRepFpTail614.bind(
                            memory,
                            input.base().budget(),
                            unknownCopyTails);

                    // Execute SlotCapacityWithFp616.execute ONCE
                    QueueFp604Api.Outcome outcome = SlotCapacityWithFp616.execute(
                            nested615Input,
                            memory,
                            knownSetCalls,
                            knownRepTails);

                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        // Validate against the original 479 frame BEFORE holder mutation
                        frame.checkNormalReturn(normal.base());

                        // Store its SAME postMxcsr object as localcurrentstate.
                        currentMxcsrHolder[0] = normal.postMxcsr();

                        // Return EXACT SAME normal.base object
                        return normal.base();
                    } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                        // Abort immediately to execute's outer boundary.
                        throw new StoppedOutcomeException(stopped);
                    } else {
                        throw new NullPointerException("Null outcome from nested reserve");
                    }
                }

                // All other actual 479 calls go once to otherProducerCalls.invoke(new 618.CallFrame(EXACT SAME 479frame, SAME currentMxcsr)).
                CallFrame wrappedFrame = new CallFrame(frame, currentMxcsrHolder[0]);
                QueueFp604Api.Outcome outcome = otherProducerCalls.invoke(wrappedFrame);

                if (outcome instanceof QueueFp604Api.Normal normal) {
                    // Validate against the original 479 frame BEFORE holder mutation
                    frame.checkNormalReturn(normal.base());

                    // Store its SAME postMxcsr object as localcurrentstate.
                    currentMxcsrHolder[0] = normal.postMxcsr();

                    // Return EXACT SAME normal.base object
                    return normal.base();
                } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                    // Abort immediately to execute's outer boundary.
                    throw new StoppedOutcomeException(stopped);
                } else {
                    throw new NullPointerException("Null outcome from otherProducerCalls");
                }
            }
        };

        try {
            // Execute exact supplied PendingSlotProducerFullState2A32770.execute(input.base(), SAME memory, invocation-local 479.Calls) ONCE.
            FullCopy437Api.CallResult result = PendingSlotProducerFullState2A32770.execute(
                    input.base(),
                    memory,
                    narrowCalls);

            // On final oldproducer normal return wrap SAME old full 437 CallResult with SAME current postMxcsr.
            return new QueueFp604Api.Normal(result, currentMxcsrHolder[0]);
        } catch (StoppedOutcomeException e) {
            // Return the EXACT offered Stopped object.
            return e.outcome;
        }
    }
}