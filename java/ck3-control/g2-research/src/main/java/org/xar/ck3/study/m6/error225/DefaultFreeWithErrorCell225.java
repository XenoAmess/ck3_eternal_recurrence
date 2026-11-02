package org.xar.ck3.study.m6.error225;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.full224.DefaultObject185Known224;
import org.xar.ck3.research.m5.GovernmentErrorCell204Calls;

/**
 * Thin genuine consumer composition of mature DefaultObject185Known224 and GovernmentErrorCell204Calls.
 * Reuses actual fromSlot10 logic with bound error-cell calls; no algorithm reimplementation.
 */
public final class DefaultFreeWithErrorCell225 {
    private DefaultFreeWithErrorCell225() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls lower) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        // lower is not eagerly validated here to preserve zeroRDX lazy boundary contract.
        // If lower is null and RDX is non-zero, DefaultObject185Known224.fromSlot10 will handle it.

        GovernmentCrtBoundary185Api.Calls boundCalls = GovernmentErrorCell204Calls.bind(
                entry.imageBaseBits(), memory, lower);

        return DefaultObject185Known224.fromSlot10(entry, memory, boundCalls, null);
    }
}