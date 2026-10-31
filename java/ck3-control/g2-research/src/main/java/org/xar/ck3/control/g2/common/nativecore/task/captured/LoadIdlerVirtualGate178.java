package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadIdlerRootPublication175.Invocation;

/** Exact supplied normal memory/call effects. External callback returns are supplied
 * bit patterns consumed by the source, not an assertion of a native function ABI.
 * Stack, other registers, native unwinding and live object/caller identity are outside this API. */
public final class LoadIdlerVirtualGate178 {
    private LoadIdlerVirtualGate178() { }
    public interface Memory {
        long readPointer(long address);
        int readUnsigned8(long address);
        void writeInt64(long address, long value);
    }
    public interface Ports {
        long invoke(Invocation call);
    }
    public static void run3976ac0(long moduleBase, Memory memory, Ports ports) {
        long g1 = memory.readPointer(moduleBase + 0x5cb87f8L);
        if (g1 == 0) { return; }
        if (memory.readUnsigned8(g1 + 0x161L) == 0) { return; }
        long obj = memory.readPointer(moduleBase + 0x5c6a688L);
        if (obj == 0) {
            long ecx = 8L;
            long callRes = ports.invoke(new Invocation(0x3976af1L, moduleBase + 0x4223b94L, ecx, java.util.OptionalLong.empty(), false));
            obj = callRes;
            memory.writeInt64(moduleBase + 0x5c6a688L, obj);
            memory.writeInt64(obj, moduleBase + 0x499f998L);
        }
        long vptr = memory.readPointer(obj);
        long target = memory.readPointer(vptr + 0x10L);
        long ret = ports.invoke(new Invocation(0x3976b0dL, target, obj, java.util.OptionalLong.of(vptr), false));
        if (ret == 0) { return; }
        long queryTarget = memory.readPointer(moduleBase + 0x54d5040L);
        long queryRet = ports.invoke(new Invocation(0x3976b1bL, queryTarget, ret, java.util.OptionalLong.empty(), false));
        long alBit = queryRet & 1L;
        long edx = (alBit == 1L) ? 0L : 0x1001L;
        long tailTarget = memory.readPointer(moduleBase + 0x54d50e8L);
        long tailSite = (alBit == 1L) ? 0x3976b33L : 0x3976b48L;
        ports.invoke(new Invocation(tailSite, tailTarget, ret, java.util.OptionalLong.of(edx), true));
    }
}
