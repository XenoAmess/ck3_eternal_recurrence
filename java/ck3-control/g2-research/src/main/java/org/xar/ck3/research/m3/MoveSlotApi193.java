package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;

/** Exact known cleanup boundary for complete80B C3CF10; supplied Memory owns all storage. */
public final class MoveSlotApi193 {
    private MoveSlotApi193() { }
    public interface Ports {
        /** May mutate supplied memory or throw; no result is consumed by C3CF10. */
        void call856050(RequestE92780.Memory memory, long descriptor);
    }
}
