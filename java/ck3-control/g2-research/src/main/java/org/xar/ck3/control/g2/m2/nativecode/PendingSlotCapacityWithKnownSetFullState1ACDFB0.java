package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.CallResult;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.CallFrame;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.TailFrame;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;
import java.util.Objects;

/**
 * New actual full-mode consumer for PendingSlotCapacity1ACDFB0.
 * Reuses known full 372/133 implementations and the mature KnownSet412 binder.
 * Does not duplicate algorithms or infer default states.
 */
public final class PendingSlotCapacityWithKnownSetFullState1ACDFB0 {
    private PendingSlotCapacityWithKnownSetFullState1ACDFB0() { }

    public static CallResult execute(Input input, Memory memory, Calls fallback) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);

        // Bind the mature KnownSet412 adapter once with the exact same memory and budget.
        // This adapter handles the 206/207 fill semantics and forwards foreign frames.
        Calls knownSetCalls = PendingSlotCapacityKnownSet412.bind(memory, input.budget(), fallback);

        // Create the combined Calls implementation that dispatches the specific reserve call
        // to the new full-state 133 implementation, while delegating everything else to knownSetCalls.
        Calls combinedCalls = new Calls() {
            @Override
            public CallResult invoke(CallFrame frame) {
                // Match only the exact source call site for the reserve function.
                if (frame.call().callSiteRva() == 0x1ACDFF3L &&
                    frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    frame.call().targetBits() == 0x1ACE4B0L) {

                    // Construct the Input for the nested 133 execution using the child entry
                    // and the current direction flag from the frame.
                    Input childInput = new Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Execute the new full-state 133 implementation with the SAME combinedCalls
                    // to ensure nested unknown ports (like virtual allocate/release) are handled
                    // consistently by this consumer or the fallback.
                    CallResult childResult = PendingSlotArrayReserveFullState1ACE4B0.execute(
                        childInput,
                        memory,
                        this
                    );

                    // Validate the child result against the frame expectations.
                    frame.checkNormalReturn(childResult);

                    return childResult;
                }

                // All other invokes (including the 206 fill call at 1ACE015) go to the knownSet adapter.
                return knownSetCalls.invoke(frame);
            }

            @Override
            public CallResult tail(TailFrame frame) {
                // Forward all tails to the knownSet adapter.
                return knownSetCalls.tail(frame);
            }

            @Override
            public long readGsQword58() {
                // Forward GS reads to the knownSet adapter.
                return knownSetCalls.readGsQword58();
            }
        };

        // Execute the new full-state 372 implementation exactly once.
        // It uses the combinedCalls to handle the reserve call and the knownSet adapter for the fill call.
        CallResult result = PendingSlotCapacityFullState1ACDFB0.execute(
            input,
            memory,
            combinedCalls
        );

        return result;
    }
}