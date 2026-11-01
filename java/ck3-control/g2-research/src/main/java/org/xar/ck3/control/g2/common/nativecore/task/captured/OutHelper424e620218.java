package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.out224.OutHelper224Api;
import org.xar.ck3.research.m3.out224.OutHelper424E620;

/** Owned normal-frame compatibility for the held 78-byte region; no Game execution. */
public final class OutHelper424e620218 {
    private OutHelper424e620218() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls) {
        Frame f = new Frame(entry, memory, calls);
        // 1. Physical prologue: save RBX to [E-8] (source: push rbx)
        memory.writeQword(f.e - 8L, f.entry.nonvolatileBits().rbxBits());

        // 2. Invoke old M3 business logic exactly once
        OutHelper224Api.Input input = new OutHelper224Api.Input(f.image, f.entry.volatileBits().rcxBits());
        long oldResult = OutHelper424E620.execute(new MemoryView(f), new BusinessPorts(f), input);

        // 3. Outcome handling
        if (f.tailResult != null) {
            // Tail path: return the exact captured NormalReturn object from the tail port
            return f.tailResult;
        }

        // Normal path (error or direct return from old core)
        // Apply old scalar result to RAX only, preserving other V

        // Update RAX with oldResult, keep other V
        f.args(oldResult, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());

        // Source physical normal epilogue: fresh READQ[E-8] savedRBX, then READQ[E] RET
        long savedRbx = memory.readQword(f.e - 8L);
        long retRip = memory.readQword(f.e);

        // Construct restored NonvolatileBits: fresh RBX, original remaining 8
        NonvolatileBits incomingNV = entry.nonvolatileBits();
        NonvolatileBits restoredNV = new NonvolatileBits(
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

        // Return NormalReturn with current whole V, fresh restored NV, return RIP, callerSP=E+8
        return new NormalReturn(f.v, retRip, f.e + 8L, restoredNV);
    }

    private static final class Frame {
        final GovernmentCrtBoundary185Api.Entry entry;
        final GovernmentCrtBoundary185Api.Memory memory;
        final GovernmentCrtBoundary185Api.Calls calls;
        final long e, image, work;
        final GovernmentPrimaryTail155Api.NonvolatileBits active;
        GovernmentPrimaryTail155Api.VolatileBits v;
        GovernmentPrimaryTail155Api.NonvolatileBits tailNv;
        GovernmentCrtBoundary185Api.NormalReturn tailResult;

            Frame(GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls) {
                this.entry = Objects.requireNonNull(entry);
                this.memory = Objects.requireNonNull(memory);
                this.calls = Objects.requireNonNull(calls);
                this.e = entry.rspBits();
                this.image = entry.imageBaseBits();
                this.work = this.e - 0x28L;
                this.v = entry.volatileBits();
                this.tailNv = null;
                this.tailResult = null;

                // Active NV: RBX=actual incoming RCX full64, RBP/other NV exact entry
                long rbxVal = entry.volatileBits().rcxBits();
                this.active = new NonvolatileBits(
                    rbxVal,
                    entry.nonvolatileBits().rbpBits(),
                    entry.nonvolatileBits().rsiBits(),
                    entry.nonvolatileBits().rdiBits(),
                    entry.nonvolatileBits().r12Bits(),
                    entry.nonvolatileBits().r13Bits(),
                    entry.nonvolatileBits().r14Bits(),
                    entry.nonvolatileBits().r15Bits(),
                    entry.nonvolatileBits().xmm6()
                );
            }

        private void args(long rax, long rcx, long rdx, long r8, long r9) {
            v = new VolatileBits(rax, rcx, rdx, r8, r9, v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
        }
        private long invoke(long site, TargetKind kind, long target, int length) {
            memory.writeQword(work - 8, image + site + length);
            Call call = new Call(site, kind, target, work, v, active);
            v = calls.invoke(call);
            return v.raxBits();
        }
        private void prepareTail() {
            if (tailNv != null) throw new IllegalStateException("Tail already prepared");
            // Source epilogue projection: RCX=-6, RDX=original saved entry RCX (activeRBX)
            long rcx = 0xfffffffffffffffaL;
            long rdx = entry.volatileBits().rcxBits();
            args(v.raxBits(), rcx, rdx, v.r8Bits(), v.r9Bits());
            // Fresh READQ[E-8] savedRBX BEFORE IAT read
            long savedRbx = memory.readQword(e - 8L);
            // Build stored tail NV: fresh RBX + original other 8
            tailNv = new NonvolatileBits(
                savedRbx,
                active.rbpBits(),
                active.rsiBits(),
                active.rdiBits(),
                active.r12Bits(),
                active.r13Bits(),
                active.r14Bits(),
                active.r15Bits(),
                active.xmm6()
            );
        }
    }

    private static final class MemoryView implements NativeTaskMemory {
        private final Frame f;
        MemoryView(Frame f) { this.f = f; }
        @Override public int readInt32(long address) { return f.memory.readDword(address); }
        @Override public void writeInt32(long address, int value) { f.memory.writeDword(address, value); }
        @Override public long readPointer(long address) {
            if (address == f.image + 0x43dbba8L) {
                f.prepareTail();
            }
            return f.memory.readQword(address);
        }
        @Override public void writeInt64(long address, long value) { f.memory.writeQword(address, value); }
    }

    private static final class BusinessPorts implements OutHelper224Api.Ports {
        private final Frame f;
        BusinessPorts(Frame f) { this.f = f; }
        @Override public long call424e448(NativeTaskMemory memory, long siteRva, int ecx, long rdx, long r8, long r9) {
            f.args(f.v.raxBits(), Integer.toUnsignedLong(ecx), rdx, r8, r9);
            return f.invoke(0x424e643L, TargetKind.DIRECT_RVA, 0x424e448L, 5);
        }
        @Override public long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, long rcx, long rdx) {
            if (f.tailNv == null) throw new IllegalStateException("Tail NV not prepared");
            f.args(liveRax, rcx, rdx, f.v.r8Bits(), f.v.r9Bits());
            Entry tailEntry = new Entry(f.image, f.e, f.v, f.tailNv);
            Tail tail = new Tail(0x424e65cL, TargetKind.INDIRECT_ABSOLUTE, actualTarget, tailEntry);
            NormalReturn nr = f.calls.tail(tail);
            f.tailResult = nr;
            return nr.volatileBits().raxBits();
        }
    }
}
