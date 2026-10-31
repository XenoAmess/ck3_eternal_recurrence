package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Supplied normal memory/call trace only; no return-register, unwind or process identity. */
public final class LoadIdlerRootPublication175 {
    private LoadIdlerRootPublication175() { }
    public interface Memory extends NativeTaskMemory {
        int readUnsigned8(long address);
    }
    /** Only RCX and source-assigned RDX are projected; other registers and return bits are outside this trace API. */
    public record Invocation(long siteRva, long targetBits, long rcx,
            OptionalLong rdxBits, boolean tail) { }
    public interface Ports {
        void invoke(Invocation call);
    }
    public static void publishC20350(long moduleBase, long self, Memory memory, Ports ports) {
        memory.writeInt64(moduleBase + 0x5C6A520L, self);
        long child = memory.readPointer(self + 8L);
        if (child != 0L) {
            long vptr = memory.readPointer(child);
            long target = memory.readPointer(vptr + 0x28L);
            ports.invoke(new Invocation(0xC2036CL, target, child, OptionalLong.empty(), false));
        }
        child = memory.readPointer(self + 0x10L);
        if (child != 0L) {
            long vptr = memory.readPointer(child);
            long target = memory.readPointer(vptr + 0x28L);
            ports.invoke(new Invocation(0xC2037BL, target, child, OptionalLong.empty(), false));
        }
        if (memory.readUnsigned8(moduleBase + 0x5C6A50DL) == 0
                && memory.readUnsigned8(moduleBase + 0x5430305L) == 0) {
            long receiver = memory.readPointer(self + 0x18L);
            ports.invoke(new Invocation(0xC20399L, moduleBase + 0x39292B0L,
                    receiver, OptionalLong.empty(), true));
        }
    }
    public static void publish383e520(long moduleBase, long self, Memory memory, Ports ports) {
        memory.writeInt64(moduleBase + 0x5C6A520L, self);
        long rbx = self;
        long rcx = memory.readPointer(rbx + 8);
        if (rcx != 0) {
            long rax = memory.readPointer(rcx);
            long target = memory.readPointer(rax + 0x28);
            ports.invoke(new Invocation(0x383E53CL, target, rcx, OptionalLong.empty(), false));
        }
        rcx = memory.readPointer(rbx + 0x10);
        if (rcx != 0) {
            long rax = memory.readPointer(rcx);
            long target = memory.readPointer(rax + 0x28);
            ports.invoke(new Invocation(0x383E550L, target, rcx, OptionalLong.empty(), true));
        }
    }
    public static void release383e130(long moduleBase, long self, Memory memory, Ports ports) {
        memory.writeInt64(self, moduleBase + 0x49458D0L);
        long child = memory.readPointer(self + 8L);
        if (child != 0L) {
            long vptr = memory.readPointer(child);
            long target = memory.readPointer(vptr);
            ports.invoke(new Invocation(0x383E158L, target, child, OptionalLong.of(1L), false));
            memory.writeInt64(self + 8L, 0L);
        }
        child = memory.readPointer(self + 0x10L);
        if (child != 0L) {
            long vptr = memory.readPointer(child);
            long target = memory.readPointer(vptr);
            ports.invoke(new Invocation(0x383E16FL, target, child, OptionalLong.of(1L), false));
            memory.writeInt64(self + 0x10L, 0L);
        }
        long current = memory.readPointer(moduleBase + 0x5C6A520L);
        memory.writeInt64(moduleBase + 0x5C6A520L, current == self ? 0L : current);
        ports.invoke(new Invocation(0x383E18EL, moduleBase + 0x383E8C0L,
                self + 0x30L, OptionalLong.empty(), false));
        memory.writeInt64(self, moduleBase + 0x49459F8L);
    }
}
