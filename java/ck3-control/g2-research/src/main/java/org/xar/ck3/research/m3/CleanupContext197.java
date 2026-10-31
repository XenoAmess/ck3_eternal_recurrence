package org.xar.ck3.research.m3;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.AddressFree83Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;

public final class CleanupContext197 {
    private CleanupContext197() { }

    public static CleanupContext197Api.Result execute(
            long moduleBase, long storage, CleanupContext197Api.Memory memory, Lower61Inputs.Calls calls) {
        // 1. Read capacity once (QWORD[storage+18])
        long capacityBits = memory.readPointer(storage + 0x18L);

        // 2. Determine if pointer read is required (unsigned capacity >= 16)
        OptionalLong heapPointerBits = OptionalLong.empty();
        if (Long.compareUnsigned(capacityBits, 16) >= 0) {
            heapPointerBits = OptionalLong.of(memory.readPointer(storage));
        }

        // 3. Determine if back-reference read is required (S >= 4096)
        OptionalLong backReferenceBits = OptionalLong.empty();
        if (!heapPointerBits.isEmpty()) {
            long P = heapPointerBits.getAsLong();
            long S = capacityBits + 1; // wrapping
            if (Long.compareUnsigned(S, 4096) >= 0) {
                backReferenceBits = OptionalLong.of(memory.readPointer(P - 8));
            }
        }

        // 4. Use existing planner
        InlineStorageCleanupPlan.Plan plan = InlineStorageCleanupPlan.plan(capacityBits, heapPointerBits, backReferenceBits);

        // 5. Handle REJECTED_HEADER explicitly before any effects
        if (plan.path() == InlineStorageCleanupPlan.Path.REJECTED_HEADER) {
            return new CleanupContext197Api.Result(CleanupContext197Api.Completion.UNSUPPORTED_ERROR_BRANCH, plan);
        }

        // 6. Execute lower chain if DIRECT_CALL or ADJUSTED_CALL
        if (plan.path() == InlineStorageCleanupPlan.Path.DIRECT_CALL || plan.path() == InlineStorageCleanupPlan.Path.ADJUSTED_CALL) {
            long rcxBits = plan.rcxBits().getAsLong();
            Lower61Inputs.CallInput input = new Lower61Inputs.CallInput(moduleBase, rcxBits);
            AddressFree83Consumer.execute(input, memory, calls);
        }

        // 7. Apply normal reset values in order and exact widths
        for (InlineStorageCleanupPlan.RelativeReset reset : InlineStorageCleanupPlan.normalResetValues()) {
            long address = storage + reset.offsetFromD();
            if (reset.byteWidth() == 8) {
                memory.writeInt64(address, reset.valueBits());
            } else if (reset.byteWidth() == 1) {
                memory.writeByte(address, (byte)reset.valueBits());
            }
        }

        return new CleanupContext197Api.Result(CleanupContext197Api.Completion.RETURNED, plan);
    }
}