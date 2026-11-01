package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.CallResult;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.CallFrame;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.TailFrame;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

/**
 * Thin composition consumer: installs mature KnownSet412 (206/207) and KnownCopy456 (4226860)
 * on the same strong Memory and budget, then executes full372 with combined Calls.
 * Dispatches only the reserve call site to full133; all other frames delegate to binders.
 */
public final class PendingSlotCapacityWithKnownMemoryFullState470 {
    private PendingSlotCapacityWithKnownMemoryFullState470() { }

    public static CallResult execute(Input input, PendingSlotCapacityKnownCopyFullState456.Memory memory, Calls fallback) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);

        // Bind mature KnownSet412 (handles 206/207 fill semantics)
        Calls knownSetCalls = PendingSlotCapacityKnownSet412.bind(memory, input.budget(), fallback);

        // Bind mature KnownCopy456 (handles 4226860 copy semantics)
        Calls knownCopyCalls = PendingSlotCapacityKnownCopyFullState456.bind(memory, input.budget(), knownSetCalls);

        // Combined Calls: dispatch reserve to full133, everything else to knownCopyCalls
        Calls combinedCalls = new Calls() {
            @Override
            public CallResult invoke(CallFrame frame) {
                if (frame.call().callSiteRva() == 0x1ACDFF3L &&
                    frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    frame.call().targetBits() == 0x1ACE4B0L) {

                    Input childInput = new Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    CallResult childResult = PendingSlotArrayReserveFullState1ACE4B0.execute(
                        childInput,
                        memory,
                        this
                    );

                    frame.checkNormalReturn(childResult);
                    return childResult;
                }

                return knownCopyCalls.invoke(frame);
            }

            @Override
            public CallResult tail(TailFrame frame) {
                return knownCopyCalls.tail(frame);
            }

            @Override
            public long readGsQword58() {
                return knownCopyCalls.readGsQword58();
            }
        };

        // Execute full372 exactly once with combined Calls
        CallResult result = PendingSlotCapacityFullState1ACDFB0.execute(
            input,
            memory,
            combinedCalls
        );

        return result;
    }
}