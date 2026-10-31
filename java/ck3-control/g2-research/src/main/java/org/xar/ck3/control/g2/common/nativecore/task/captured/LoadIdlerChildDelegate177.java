package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadIdlerRootPublication175.Invocation;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadIdlerRootPublication175.Ports;

/** Exact supplied 17B normal effect trace only; no register-return, RF/EH or live caller assertion. */
public final class LoadIdlerChildDelegate177 {
    private LoadIdlerChildDelegate177() { }
    @FunctionalInterface
    public interface Memory { long readPointer(long address); }
    public static void forward383e4c0(long self, Memory memory, Ports ports) {
        long child = memory.readPointer(self + 0x10);
        if (child == 0) return;
        long vptr = memory.readPointer(child);
        long target = memory.readPointer(vptr + 0x38);
        ports.invoke(new Invocation(0x383e4ccL, target, child, OptionalLong.empty(), true));
    }
}
