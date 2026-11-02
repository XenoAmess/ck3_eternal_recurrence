package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.SlotReserveWithFp615;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState1ACDFB0;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Parent composition for the complete 372-byte PendingSlotCapacityFullState1ACDFB0.
 * Reuses SlotReserveWithFp615 for the nested 133-byte reserve call and delegates other calls to opaque ports.
 */
public final class SlotCapacityWithFp616 {
    private SlotCapacityWithFp616() { }

    public static QueueFp604Api.Outcome execute(
            SlotReserveWithFp615.Input input,
            SlotReserveWithFp615.Memory memory,
            SlotReserveWithFp615.Calls otherCalls,
            FullCopyWithFp613.TailCalls copyTails) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(otherCalls);
        Objects.requireNonNull(copyTails);

        final QueueFp604Api.Mxcsr[] currentMxcsrHolder = new QueueFp604Api.Mxcsr[1];
        currentMxcsrHolder[0] = input.mxcsr();

        PendingSlotCapacityFullState412Api.Calls narrowCalls = new PendingSlotCapacityFullState412Api.Calls() {
            @Override
            public PendingSlotCapacityFullState412Api.CallResult invoke(PendingSlotCapacityFullState412Api.CallFrame frame) {
                Objects.requireNonNull(frame);

                if (frame.call().callSiteRva() == 0x1ACDFF3L
                        && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && frame.call().targetBits() == 0x1ACE4B0L) {

                    SlotReserveWithFp615.Input nestedInput = new SlotReserveWithFp615.Input(
                            new PendingSlotCapacityFullState412Api.Input(
                                    frame.childEntry(),
                                    frame.directionFlagSet(),
                                    input.base().budget()),
                            currentMxcsrHolder[0]);

                    QueueFp604Api.Outcome outcome = SlotReserveWithFp615.execute(
                            nestedInput, memory, otherCalls, copyTails);

                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        currentMxcsrHolder[0] = normal.postMxcsr();
                        return new PendingSlotCapacityFullState412Api.CallResult(
                                normal.base().normalReturn(),
                                normal.base().postDirectionFlagSet());
                    } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                        throw new StoppedOutcomeException(stopped);
                    } else {
                        throw new NullPointerException("Null outcome from nested reserve");
                    }
                }

                SlotReserveWithFp615.CallFrame wrappedFrame = new SlotReserveWithFp615.CallFrame(
                        frame, currentMxcsrHolder[0]);
                QueueFp604Api.Outcome outcome = otherCalls.invoke(wrappedFrame);

                if (outcome instanceof QueueFp604Api.Normal normal) {
                    currentMxcsrHolder[0] = normal.postMxcsr();
                    return new PendingSlotCapacityFullState412Api.CallResult(
                            normal.base().normalReturn(),
                            normal.base().postDirectionFlagSet());
                } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                    throw new StoppedOutcomeException(stopped);
                } else {
                    throw new NullPointerException("Null outcome from otherCalls");
                }
            }

            @Override
            public PendingSlotCapacityFullState412Api.CallResult tail(PendingSlotCapacityFullState412Api.TailFrame frame) {
                throw new UnsupportedOperationException("Tail not expected in complete 372");
            }

            @Override
            public long readGsQword58() {
                throw new UnsupportedOperationException("GS read not expected in complete 372");
            }
        };

        try {
            PendingSlotCapacityFullState412Api.CallResult result = PendingSlotCapacityFullState1ACDFB0.execute(
                    input.base(), memory, narrowCalls);

            FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(
                    result.normalReturn(),
                    result.postDirectionFlagSet());
            return new QueueFp604Api.Normal(baseResult, currentMxcsrHolder[0]);
        } catch (StoppedOutcomeException e) {
            return e.outcome;
        }
    }

    private static final class StoppedOutcomeException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped outcome;

        StoppedOutcomeException(QueueFp604Api.Stopped outcome) {
            this.outcome = outcome;
        }
    }
}