package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalAbort4242284215.Calls60;
import org.xar.ck3.control.g2.common.nativecore.task.captured.DispatchMiddle42420f8224;
import org.xar.ck3.control.g2.common.nativecore.task.captured.CallbackSpan424e1ac231Calls;
import org.xar.ck3.control.g2.common.nativecore.task.captured.CallbackSpanStaticDispatch232Calls;

public final class DispatchMiddleSpanComposition233 {
    private DispatchMiddleSpanComposition233() { }

    public static NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            DispatchMiddle42420f8224.Memory32 memory,
            Calls60 originalFallback) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(originalFallback);

        long image = entry.imageBaseBits();

        // 1. Create inner 232 Calls60 binding originalFallback
        Calls60 inner232 = CallbackSpanStaticDispatch232Calls.bind(image, originalFallback);

        // 2. Create outer 231 Calls60 binding memory and inner232
        Calls60 outer231 = CallbackSpan424e1ac231Calls.bind(image, memory, inner232);

        // 3. Execute existing 224 business logic once with outer231
        return DispatchMiddle42420f8224.execute(entry, memory, outer231);
    }
}