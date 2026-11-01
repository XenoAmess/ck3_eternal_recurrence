package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m3.gs223.GsFlag223Api;
import org.xar.ck3.research.m3.gs223.GsFlag42591F8;

/** Owned normal-frame compatibility for the held 60-byte region; no Game execution. */
public final class GsFlag42591f8217 {
    private GsFlag42591f8217() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory, TerminalAbort4242284215.Calls60 calls) {
        Frame f = new Frame(entry, memory, calls);
        // 1. Physical prologue: save incoming RBX to [E-8]
        f.memory.writeQword(f.e - 8L, f.entry.nonvolatileBits().rbxBits());

        // 2. Invoke existing M3 business algorithm exactly once
        int result = GsFlag42591F8.execute(new MemoryView(f), new BusinessPorts(f), new GsFlag223Api.Scratch(f.e));

        // 3. Apply source MOV EAX, EBX: set RAX to unsigned result, preserve other volatile bits
        f.args(Integer.toUnsignedLong(result), f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());

        // 4. Fresh physical reads in source order for epilogue
        long savedRbx = f.memory.readQword(f.e - 8L);
        long retRip = f.memory.readQword(f.e);

        // 5. Construct restored NonvolatileBits (9 fields: RBX fresh, others from entry)
        GovernmentPrimaryTail155Api.NonvolatileBits incomingNV = f.entry.nonvolatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits restoredNV = new GovernmentPrimaryTail155Api.NonvolatileBits(
            savedRbx,
            incomingNV.rbpBits(),
            incomingNV.rsiBits(),
            incomingNV.rdiBits(),
            incomingNV.r12Bits(),
            incomingNV.r13Bits(),
            incomingNV.r14Bits(),
            incomingNV.r15Bits(),
            incomingNV.xmm6()
        );

        // 6. Return NormalReturn with current whole V, fresh RIP, caller SP (E+8), restored NV
        return new GovernmentCrtBoundary185Api.NormalReturn(f.v, retRip, f.e + 8L, restoredNV);
    }

    private static final class Frame {
        final GovernmentCrtBoundary185Api.Entry entry;
        final GovernmentCrtBoundary185Api.Memory memory;
        final TerminalAbort4242284215.Calls60 calls;
        final long e, image, work;
        final GovernmentPrimaryTail155Api.NonvolatileBits active;
        GovernmentPrimaryTail155Api.VolatileBits v;
        boolean gsPending;
        long gsValue;

        private Frame(GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory, TerminalAbort4242284215.Calls60 calls) {
            this.entry = Objects.requireNonNull(entry);
            this.memory = Objects.requireNonNull(memory);
            this.calls = Objects.requireNonNull(calls);
            this.e = entry.rspBits();
            this.image = entry.imageBaseBits();
            this.work = this.e - 0x28L;
            this.v = entry.volatileBits();
            this.gsPending = false;
            this.gsValue = 0L;

            // Active NV: RBX is 0 (XOR EBX,EBX), others from entry
            GovernmentPrimaryTail155Api.NonvolatileBits incomingNV = entry.nonvolatileBits();
            this.active = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0L,
                incomingNV.rbpBits(),
                incomingNV.rsiBits(),
                incomingNV.rdiBits(),
                incomingNV.r12Bits(),
                incomingNV.r13Bits(),
                incomingNV.r14Bits(),
                incomingNV.r15Bits(),
                incomingNV.xmm6()
            );
        }

        private void args(long rax, long rcx, long rdx, long r8, long r9) {
            v = new VolatileBits(rax, rcx, rdx, r8, r9, v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
        }
        private long invoke(long site) {
            memory.writeQword(work - 8, image + site + 5);
            Call call = new Call(site, TargetKind.DIRECT_RVA, 0x424E620L, work, v, active);
            v = calls.invoke(call);
            return v.raxBits();
        }
    }

    private static final class MemoryView implements NativeTaskMemory {
        private final Frame f;
        MemoryView(Frame f) { this.f = f; }
        @Override public int readInt32(long address) { return f.memory.readDword(address); }
        @Override public void writeInt32(long address, int value) { f.memory.writeDword(address, value); }
        @Override public void writeInt64(long address, long value) { f.memory.writeQword(address, value); }
        @Override public long readPointer(long address) {
            long p = f.memory.readQword(address);
            if (f.gsPending && address == f.gsValue + 0x20L) {
                f.args(f.v.raxBits(), p, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
                f.gsPending = false;
            }
            return p;
        }
    }

    private static final class BusinessPorts implements GsFlag223Api.Ports {
        private final Frame f;
        BusinessPorts(Frame f) { this.f = f; }
        @Override public long readGs60(NativeTaskMemory memory, long siteRva) {
            long gs = f.calls.readGsQword60();
            f.gsValue = gs;
            f.gsPending = true;
            f.args(gs, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
            return gs;
        }
        @Override public void call424e620(NativeTaskMemory memory, long siteRva, long rcx) {
            f.args(f.v.raxBits(), rcx, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
            f.invoke(0x425921BL);
        }
    }
}
