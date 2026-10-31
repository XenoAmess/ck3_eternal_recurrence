package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class BoundReleaseSelector167 implements ReleaseApi167.Ports {
    private final ReleaseApi167.Ports outer;
    private final long selectorTarget;

    public BoundReleaseSelector167(ReleaseApi167.Ports outer, long selectorTarget) {
        this.outer = outer;
        this.selectorTarget = selectorTarget;
    }

    public long slot38(NativeTaskMemory memory, long target, long receiver, long rows, long alignment, long incomingR9) {
        if (target == selectorTarget) {
            return AllocatorSelector165.select(memory, receiver);
        }
        return outer.slot38(memory, target, receiver, rows, alignment, incomingR9);
    }

    public long release10(NativeTaskMemory memory, long target, long receiver, long rows, long alignment, long vptrR9) {
        return outer.release10(memory, target, receiver, rows, alignment, vptrR9);
    }
}
