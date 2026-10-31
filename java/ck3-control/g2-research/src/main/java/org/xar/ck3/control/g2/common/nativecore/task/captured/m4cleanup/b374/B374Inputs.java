package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374;

import java.util.List;
import java.util.Map;

/**
 * Typed effect-only API for the complete normal path of RF 0x42566FC..0x4256872 (374 bytes).
 * This class defines the inputs, memory model, and opaque call observations required to
 * faithfully represent the physical execution flow without implementing the algorithm.
 */
public final class B374Inputs {

    /**
     * Represents the initial state of the function call.
     * @param moduleBaseRaw The base address of the module for resolving RIP-relative offsets.
     * @param objectRaw The value of RCX at function entry (0x42566FC), which is used as the primary object pointer.
     */
    public record CallInput(long moduleBaseRaw, long objectRaw) { }

    /**
     * Shared mutable memory interface.
     * All reads and writes must reflect the current state of the simulated memory, ensuring that
     * later loads in the execution path see fresh values potentially mutated by opaque calls.
     */
    public interface Memory extends org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory { }

    /**
     * Interface for observing opaque calls.
     * Each method corresponds to a specific call site in the native code.
     * The parameter 'knownRcxRaw' represents the value of RCX at the moment of the call,
     * which is the only register observation exposed by this effects-only port, not a complete native argument list.
     *
     * Note: The final tail call (jmp 0x424e364) is distinguished from normal calls to preserve
     * the control flow semantics (tail call vs. return after call).
     */
    public interface Calls {
        // Normal calls to 0x424e364
        void call424E364(long knownRcxRaw);

        // Normal call to 0x42552d0
        void call42552D0(long knownRcxRaw);

        // Normal call to 0x4255910
        void call4255910(long knownRcxRaw);

        // Normal call to 0x425689c
        void call425689C(long knownRcxRaw);

        // Final tail call to 0x424e364 (distinguished from normal calls)
        void tail424E364(long knownRcxRaw);
    }

    /**
     * Static ABI and execution notes.
     *
     * 1. Entry State:
     *    - RCX contains the object pointer (objectRaw).
     *    - RAX and RDX are NOT used by this 374-byte block as inputs; they are overwritten or ignored.
     *    - The caller discards the raw return value.
     *
     * 2. Memory Model:
     *    - Memory is shared and mutable across ALL opaque calls.
     *    - Subsequent loads (e.g., [rbx + 0x100], [rdi - 0x10]) must read from the current state of Memory,
     *      which may have been modified by previous opaque calls (e.g., call424E364).
     *    - No fake-zeroing of missing memory; reads return actual simulated values.
     *
     * 3. RIP-Relative References:
     *    - All image references are calculated as moduleBaseRaw + actual_RIP_target_RVA.
     *    - Example: 0x425671f uses [rip + 0x11d8afa] -> moduleBaseRaw + 0x542f220 (next RVA 0x4256726 plus displacement).
     *    - Example: 0x4256807 uses [rip + 0x11d8c8a] -> moduleBaseRaw + 0x542f498 (next RVA 0x425680e plus displacement).
     *    - These are addresses, not assumed contents.
     *
     * 4. Opaque Call Observations:
     *    - Only RCX is observed at call edges. Other registers (RAX, RBX, RSI, RDI, RBP) are internal
     *      to the 374-byte block and their values at call sites are not part of the external ABI contract
     *      for this study component, except as they influence internal control flow.
     *    - The 'knownRcxRaw' parameter captures the RCX value at the call site.
     *
     * 5. Control Flow:
     *    - The block contains multiple conditional branches and loops.
     *    - The final instruction is a JMP to 0x424e364, treated as a tail call (tail424E364).
     *    - Normal CALLs to 0x424e364 are distinct from the tail call.
     *
     * 6. Unknowns:
     *    - The internal algorithms of the opaque callees (0x424e364, 0x42552d0, 0x4255910, 0x425689c) are not inferred.
     *    - The specific side effects of these calls on memory are opaque but must be reflected in subsequent reads.
     *    - No names or inline algorithms are assigned to the callees.
     */
    public static final String abi_notes = """
        Entry: RCX=objectRaw. RAX/RDX unused as inputs.
        Memory: Shared, mutable. Fresh reads after opaque calls.
        RIP: moduleBaseRaw + RVA.
        Calls: Observed by RCX only. Tail call distinguished.
        """;
}