package org.xar.ck3.study.m6.default223;

import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Invocation;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Calls;

public final class DefaultObjectWrappers223 {
    private DefaultObjectWrappers223() { }

    public static long fromSlot08(Invocation entry, long imageBaseRaw64, Calls directCalls) {
        Invocation call = new Invocation(
            0x8571D7,
            imageBaseRaw64 + 0x4223B94,
            entry.raxRaw64(),
            entry.rdxRaw64(),
            entry.rdxRaw64(),
            entry.r8Raw64(),
            entry.r9Raw64()
        );
        return directCalls.call(call);
    }

    public static long fromSlot10(Invocation entry, long imageBaseRaw64, Calls directCalls) {
        if (entry.rdxRaw64() == 0) {
            return entry.raxRaw64();
        }
        Invocation tail = new Invocation(
            0x8571C8,
            imageBaseRaw64 + 0x40EC530,
            entry.raxRaw64(),
            entry.rdxRaw64(),
            entry.rdxRaw64(),
            entry.r8Raw64(),
            entry.r9Raw64()
        );
        return directCalls.tailJump(tail);
    }
}