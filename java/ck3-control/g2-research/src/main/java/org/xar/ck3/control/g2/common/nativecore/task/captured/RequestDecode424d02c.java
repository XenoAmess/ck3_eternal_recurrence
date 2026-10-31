package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Source424D02C supplied QWORD/register projection, no process attachment. */
public final class RequestDecode424d02c {
    private RequestDecode424d02c() { }
    public interface Ports {
        void call4247ffc(long knownRcx);
        void call4248050(long knownRcx, long liveRbx);
    }

public static long execute(long moduleBase, NativeTaskMemory memory, Ports ports) {
    long rbx = 0L;
    long ecx = 0L;
    long rax = 0L;

    ecx = 0L;

    ports.call4247ffc(ecx);

    rbx = memory.readPointer(moduleBase + 0x542f0b8L);

    ecx = (int) rbx;

    ecx = ecx & 0x3FL;

    rbx = rbx ^ memory.readPointer(moduleBase + 0x5c5d568L);

    int shift = (int) ecx;
    if (shift != 0) {
        rbx = (rbx >>> shift) | (rbx << (64 - shift));
    }

    ecx = 0L;

    ports.call4248050(ecx, rbx);

    rax = rbx;

    return rax;
}
}
