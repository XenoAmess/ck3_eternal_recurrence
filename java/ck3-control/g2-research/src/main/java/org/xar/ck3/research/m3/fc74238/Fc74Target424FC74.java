package org.xar.ck3.research.m3.fc74238;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.fc74238.Fc74Api238.Input;
import org.xar.ck3.research.m3.fc74238.Fc74Api238.Ports;

/** The normal204B supplied-storage projection; opaque callees retain their own semantics. */
public final class Fc74Target424FC74 {
    private Fc74Target424FC74() { }

    public static long execute(NativeTaskMemory memory, Ports ports, Input input) {
        long base = input.moduleBase();
        long firstTarget = memory.readPointer(base + 0x43DA738L);
        int savedError = ports.callIat43da738(memory, 0x424FC83L, firstTarget, input.entryEcxBits());
        int index = memory.readInt32(base + 0x542F328L);
        if (index != -1) {
            long existing = ports.call424e900(memory, 0x424FC96L, index);
            if (existing != 0L) {
                return finish(memory, ports, base, savedError, existing == -1L ? 0L : existing);
            }
            index = memory.readInt32(base + 0x542F328L);
        }
        if (ports.call424e948(memory, 0x424FCB9L, index, -1L) == 0) {
            return finish(memory, ports, base, savedError, 0L);
        }
        long block = ports.call424e2ec(memory, 0x424FCCCL, 1L, 0x3C8L);
        index = memory.readInt32(base + 0x542F328L);
        if (block == 0L) {
            ports.call424e948(memory, 0x424FCE1L, index, 0L);
            ports.call424e364(memory, 0x424FCE8L, 0L);
            return finish(memory, ports, base, savedError, 0L);
        }
        if (ports.call424e948(memory, 0x424FCF2L, index, block) == 0) {
            index = memory.readInt32(base + 0x542F328L);
            ports.call424e948(memory, 0x424FD03L, index, 0L);
            ports.call424e364(memory, 0x424FCE8L, block);
            return finish(memory, ports, base, savedError, 0L);
        }
        ports.call424f8a8(memory, 0x424FD10L, block);
        ports.call424e364(memory, 0x424FD17L, 0L);
        return finish(memory, ports, base, savedError, block);
    }

    public static long execute(NativeTaskMemory memory, Ports ports, Input input, long entryRsp) {
        Ports wrapped = new Ports() {
            @Override
            public int callIat43da738(NativeTaskMemory m, long s, long t, int e) { return ports.callIat43da738(m, s, t, e); }
            @Override
            public long call424e900(NativeTaskMemory m, long s, int e) { return ports.call424e900(m, s, e); }
            @Override
            public int call424e948(NativeTaskMemory m, long s, int e, long r) { return ports.call424e948(m, s, e, r); }
            @Override
            public long call424e2ec(NativeTaskMemory m, long s, long r, long d) { return ports.call424e2ec(m, s, r, d); }
            @Override
            public void call424e364(NativeTaskMemory m, long s, long r) { ports.call424e364(m, s, r); }
            @Override
            public void call424f8a8(NativeTaskMemory m, long s, long r) { ports.call424f8a8(m, s, r, entryRsp - 0x30L); }
            @Override
            public void callIat43da420(NativeTaskMemory m, long s, long t, int e) { ports.callIat43da420(m, s, t, e); }
        };
        return execute(memory, wrapped, input);
    }

    private static long finish(NativeTaskMemory memory, Ports ports, long base, int savedError, long selected) {
        long lastTarget = memory.readPointer(base + 0x43DA420L);
        ports.callIat43da420(memory, 0x424FD21L, lastTarget, savedError);
        // At the final block, source RDI and RSI are both the selected value.
        return selected;
    }
}
