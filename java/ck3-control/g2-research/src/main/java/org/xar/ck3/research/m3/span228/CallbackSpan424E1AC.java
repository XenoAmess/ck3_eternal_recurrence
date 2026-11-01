package org.xar.ck3.research.m3.span228;

import org.xar.ck3.research.m3.span228.CallbackSpan228Api.Memory;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api.Input;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api.Ports;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api.Arguments;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api.EntryArguments;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api.AfterOpaqueReturn;

public final class CallbackSpan424E1AC {
    private CallbackSpan424E1AC() { }

    public static void execute(Memory memory, Ports ports, Input input) {
        long base = input.moduleBase();
        long start = input.startAddress();
        long end = input.endAddress();

        // Compute count: ((end - start + 7) >>> 3) with unsigned comparison check
        // If unsigned start > end, count is 0
        long diff = end - start;
        long count = 0;
        if (Long.compareUnsigned(start, end) <= 0) {
            count = (diff + 7L) >>> 3;
        }

        if (count == 0) {
            return;
        }

        long cursor = start;
        Arguments currentArgs = new EntryArguments(start, end);
        boolean firstCallDone = false;

        for (long i = 0; i < count; i++) {
            // Fresh read pointer at cursor
            long observedElement = memory.readPointer(cursor);

            if (observedElement != 0) {
                // Fresh read IAT target
                long actualTarget = memory.readPointer(base + 0x43DBBA8L);

                // Invoke port
                ports.call43dbba8(memory, 0x424E1E9L, actualTarget, observedElement, currentArgs);

                // After first successful opaque return, subsequent calls use UNKNOWN
                if (!firstCallDone) {
                    firstCallDone = true;
                    currentArgs = AfterOpaqueReturn.UNKNOWN;
                }
            }

            // Advance cursor by 8
            cursor += 8L;
        }
    }
}