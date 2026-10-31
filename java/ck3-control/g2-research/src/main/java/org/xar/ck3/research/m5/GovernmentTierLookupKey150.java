package org.xar.ck3.research.m5;

/** Typed offline evaluation of the now-complete held69B/32B code/table; no memory/Game call. */
public final class GovernmentTierLookupKey150 {
    /** Actual DWORD value observed by callee22C9F60, not necessarily the earlier caller guard read. */
    public record RawTier32(int bits) { }
    /** Return-EAX arithmetic lookup role, not an awarded formal stringID/CName/enum typedef. */
    public record LookupKey32(int bits) { }
    private GovernmentTierLookupKey150() { }

    /**
     * Genuinely unwritten. Apply only actual complete dispatch/targets in supplied code/table.
     * Preserve all32 input bits. Unsigned CMP/JA means negative int patterns take default too.
     * Raw7 sharing a target/key with another input is not a formal name or stable tier claim.
     * RawTier32 is nonnull. No currentNative table observation or object mutation is provided.
     */
    public static LookupKey32 convert(RawTier32 observedTier) {
        // Unsigned CMP/JA: negative int patterns (unsigned >= 8) take default.
        // In-range 0..7 uses table_rva 0x22C9FA8 entries.
        // Table entries map raw_table_index to target_rva:
        //   0 -> 0x22C9F9F (default target, returns 0x165)
        //   1 -> 0x22C9F7B (returns 0x2807)
        //   2 -> 0x22C9F81 (returns 0x27E2)
        //   3 -> 0x22C9F87 (returns 0x27E3)
        //   4 -> 0x22C9F8D (returns 0x27E4)
        //   5 -> 0x22C9F93 (returns 0x27E5)
        //   6 -> 0x22C9F99 (returns 0x38F8)
        //   7 -> 0x22C9F9F (default target, returns 0x165)
        // Default target 0x22C9F9F returns 0x165.

        int bits = observedTier.bits();

        // Check if bits is in range 0..7 using unsigned comparison logic.
        // In Java, we can check if bits is between 0 and 7 inclusive.
        // If bits < 0 or bits > 7, it's out of range (unsigned >= 8), so use default.
        if (bits < 0 || bits > 7) {
            // Out of range: default target 0x22C9F9F returns 0x165
            return new LookupKey32(0x165);
        }

        // In range 0..7: use table lookup
        // Table entries:
        //   index 0 -> target 0x22C9F9F -> return 0x165
        //   index 1 -> target 0x22C9F7B -> return 0x2807
        //   index 2 -> target 0x22C9F81 -> return 0x27E2
        //   index 3 -> target 0x22C9F87 -> return 0x27E3
        //   index 4 -> target 0x22C9F8D -> return 0x27E4
        //   index 5 -> target 0x22C9F93 -> return 0x27E5
        //   index 6 -> target 0x22C9F99 -> return 0x38F8
        //   index 7 -> target 0x22C9F9F -> return 0x165

        switch (bits) {
            case 0:
                // Target 0x22C9F9F, returns 0x165
                return new LookupKey32(0x165);
            case 1:
                // Target 0x22C9F7B, returns 0x2807
                return new LookupKey32(0x2807);
            case 2:
                // Target 0x22C9F81, returns 0x27E2
                return new LookupKey32(0x27E2);
            case 3:
                // Target 0x22C9F87, returns 0x27E3
                return new LookupKey32(0x27E3);
            case 4:
                // Target 0x22C9F8D, returns 0x27E4
                return new LookupKey32(0x27E4);
            case 5:
                // Target 0x22C9F93, returns 0x27E5
                return new LookupKey32(0x27E5);
            case 6:
                // Target 0x22C9F99, returns 0x38F8
                return new LookupKey32(0x38F8);
            case 7:
                // Target 0x22C9F9F, returns 0x165
                return new LookupKey32(0x165);
            default:
                // Should not reach here due to earlier range check
                return new LookupKey32(0x165);
        }
    }
}