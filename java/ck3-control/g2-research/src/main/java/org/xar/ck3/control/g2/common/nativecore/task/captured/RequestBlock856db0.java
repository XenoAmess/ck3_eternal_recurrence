package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Source856DB0 supplied-storage projection. External4223B94 remains an explicit raw callback. */
public final class RequestBlock856db0 {
    private RequestBlock856db0() { }
    public interface Ports {
        long call4223b94(long rcx);
    }
    /** Original error CALL+INT3 remains unexecuted; only source-known RCX is recorded. */
    public static final class UnexecutedSourcePath extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final long targetRva;
        private final long trapSiteRva;
        private final long knownRcx;
        public UnexecutedSourcePath(long targetRva, long trapSiteRva, long knownRcx) {
            super("source error helper remains unexecuted");
            this.targetRva = targetRva;
            this.trapSiteRva = trapSiteRva;
            this.knownRcx = knownRcx;
        }
        public long targetRva() { return targetRva; }
        public long trapSiteRva() { return trapSiteRva; }
        public long knownRcx() { return knownRcx; }
    }

public static long execute(long sizeBits, RequestE92780.Memory memory, Ports ports) {
    if (Long.compareUnsigned(sizeBits, 0x1000L) < 0) {
        if (sizeBits == 0L) {
            return 0L;
        }
        return ports.call4223b94(sizeBits);
    }
    long adjusted = sizeBits + 0x27L;
    if (Long.compareUnsigned(adjusted, sizeBits) <= 0) {
        throw new UnexecutedSourcePath(0x852340L, 0x856E01L, sizeBits);
    }
    long returnedRaw = ports.call4223b94(adjusted);
    if (returnedRaw == 0L) {
        throw new UnexecutedSourcePath(0x4232A70L, 0x856E07L, 0L);
    }
    long rax = (returnedRaw + 0x27L) & ~31L;
    memory.writeInt64(rax - 8L, returnedRaw);
    return rax;
}

}
