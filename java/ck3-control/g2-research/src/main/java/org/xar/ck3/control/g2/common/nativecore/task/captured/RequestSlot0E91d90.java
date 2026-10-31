package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Source E91D90 projection over supplied memory and known opaque argument fields. */
public final class RequestSlot0E91d90 {
    private RequestSlot0E91d90() {}
    public interface Ports { void call856050(long rcx); void call4223f44(long rcx,int edx); }
    public static long invoke(long moduleBase, long receiver, int rawEdx, RequestE92780.Memory memory, Ports ports) {
        long rbx = receiver;
        long rcx = rbx;
        int edx = rawEdx;
        rcx += 0xB0L;
        if (memory.readUnsignedByte(rcx + 0x28L) != 0) {
            ports.call856050(rcx);
        }
        rcx = rbx + 0x70L;
        ports.call856050(rcx);
        long rax = moduleBase + 0x44FC298L;
        rcx = rbx + 0x48L;
        memory.writeInt64(rbx, rax);
        ports.call856050(rcx);
        rcx = rbx + 0x28L;
        ports.call856050(rcx);
        if ((edx & 1) != 0) {
            edx = 0xE0;
            rcx = rbx;
            ports.call4223f44(rcx, edx);
        }
        rax = rbx;
        return rax;
    }
}
