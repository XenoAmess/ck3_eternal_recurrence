package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Source4223B94 known RCX/RAX/EAX roles over supplied callbacks,not full native arity. */
public final class RequestRetry4223b94 {
    private RequestRetry4223b94() { }
    public interface Ports {
        long call42420b8(long rcx);
        int call424cffc(long rcx);
    }
    /** Original error CALL+INT3 unexecuted. Size is captured input/RBX,not known error-call RCX. */
    public static final class UnexecutedSourcePath extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final long targetRva;
        private final long trapSiteRva;
        private final long capturedSizeBits;
        public UnexecutedSourcePath(long targetRva, long trapSiteRva, long capturedSizeBits) {
            super("source error helper remains unexecuted");
            this.targetRva = targetRva;
            this.trapSiteRva = trapSiteRva;
            this.capturedSizeBits = capturedSizeBits;
        }
        public long targetRva() { return targetRva; }
        public long trapSiteRva() { return trapSiteRva; }
        public long capturedSizeBits() { return capturedSizeBits; }
    }

public static long execute(long sizeBits, Ports ports) {
    long rbx = sizeBits;
    while (true) {
        long rax = ports.call42420b8(rbx);
        if (rax != 0L) {
            return rax;
        }
        int eax = ports.call424cffc(rbx);
        if (eax != 0) {
            continue;
        }
        if (rbx == -1L) {
            throw new UnexecutedSourcePath(0x4224a58L, 0x4223bcfL, rbx);
        } else {
            throw new UnexecutedSourcePath(0x42207d8L, 0x4223bc9L, rbx);
        }
    }
}

}
