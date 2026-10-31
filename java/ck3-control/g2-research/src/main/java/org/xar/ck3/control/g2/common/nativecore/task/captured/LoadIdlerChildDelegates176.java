package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadIdlerRootPublication175.Invocation;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadIdlerRootPublication175.Ports;

/** Exact supplied normal memory/tail-call effect trace. Return bits, other registers,
 * unwind metadata, live object identity and natural caller are outside this API. */
public final class LoadIdlerChildDelegates176 {
    private LoadIdlerChildDelegates176() { }
    @FunctionalInterface
    public interface Memory {
        long readPointer(long address);
    }
    public static void forward383e4e0(long self, Memory memory, Ports ports) {
        long child = memory.readPointer(self + 0x10L);
        if (child == 0L) return;
        long vptr = memory.readPointer(child);
        long target = memory.readPointer(vptr + 0x40L);
        ports.invoke(new Invocation(0x383E4ECL, target, child, OptionalLong.empty(), true));
    }
    public static void forward383e500(long self, Memory memory, Ports ports) {
        long child = memory.readPointer(self + 0x10L);
        if (child == 0L) {
            return;
        }
        long vptr = memory.readPointer(child);
        long target = memory.readPointer(vptr + 0x48L);
        ports.invoke(new Invocation(0x383E50CL, target, child, OptionalLong.empty(), true));
    }
}
