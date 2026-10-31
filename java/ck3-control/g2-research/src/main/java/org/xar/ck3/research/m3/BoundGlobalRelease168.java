package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class BoundGlobalRelease168 implements ReleaseApi167.Ports {
    private final ReleaseApi167.Ports outer;
    private final long wrapperTarget;
    private final GlobalReleaseApi168.Ports tailPorts;

    public BoundGlobalRelease168(ReleaseApi167.Ports outer, long wrapperTarget, GlobalReleaseApi168.Ports tailPorts) {
        this.outer = outer;
        this.wrapperTarget = wrapperTarget;
        this.tailPorts = tailPorts;
    }

    @Override
    public long slot38(NativeTaskMemory memory, long target, long receiver, long rows, long alignment, long incomingR9) {
        return outer.slot38(memory, target, receiver, rows, alignment, incomingR9);
    }

    @Override
    public long release10(NativeTaskMemory memory, long target, long receiver, long rows, long alignment, long vptrR9) {
        if (target == wrapperTarget) {
            // Intercept selected release10 code identity.
            // Map actual source-specific registers from 855830 caller context:
            // rcx = receiver (set at 855855: mov rcx,rax where rax was returned by slot38)
            // rdx = rows (set at 855852: mov rdx,rbx where rbx was original rdx)
            // r8 = alignment (set at 85584F: mov r8,rdi where rdi was original r8)
            // r9 = vptrR9 (set at 855858: mov r9,qword ptr [rax] which is the vptr read)
            // incomingRax = receiver (contract states incomingRAX equals returnedReceiver)
            return GlobalReleaseWrapper168.apply(tailPorts, receiver, rows, alignment, vptrR9, receiver);
        }
        return outer.release10(memory, target, receiver, rows, alignment, vptrR9);
    }
}
