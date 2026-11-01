package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m3.lookup221.ModuleLookup221Api;
import org.xar.ck3.research.m3.lookup221.ModuleLookup42422D0;

/** Owned normal-frame compatibility for the held 91-byte region; no Game execution. */
public final class ModuleLookup42422d0216 {
    private ModuleLookup42422d0216() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls) {
        Frame f = new Frame(entry, memory, calls);

        // PUSH RBX: write incoming RBX to E-8
        memory.writeQword(f.e - 8L, f.entry.nonvolatileBits().rbxBits());

        // Delegate exactly once to existing business logic
        ModuleLookup42422D0 business = new ModuleLookup42422D0();
        ModuleLookup221Api.Memory memView = new MemoryView(f);
        ModuleLookup221Api.Ports ports = new BusinessPorts(f);
        ModuleLookup221Api.Input input = new ModuleLookup221Api.Input(f.image, (int)f.v.rcxBits(), new ModuleLookup221Api.Scratch(f.e));

        business.execute(memView, ports, input);

        // Post-delegation RCX adjustment if no cleanup occurred
        if (!f.cleanupSeen) {
            f.args(f.v.raxBits(), 0L, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
        }

        // Normal physical epilogue: fresh reads
        long savedRbx = memory.readQword(f.e - 8L);
        long returnRip = memory.readQword(f.e);

        // Restore NV: fresh RBX + original remaining 8 fields
        GovernmentPrimaryTail155Api.NonvolatileBits originalNV = f.entry.nonvolatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits restoredNV = new GovernmentPrimaryTail155Api.NonvolatileBits(
            savedRbx,
            originalNV.rbpBits(),
            originalNV.rsiBits(),
            originalNV.rdiBits(),
            originalNV.r12Bits(),
            originalNV.r13Bits(),
            originalNV.r14Bits(),
            originalNV.r15Bits(),
            originalNV.xmm6()
        );

        long callerSP = f.e + 8L;

        return new GovernmentCrtBoundary185Api.NormalReturn(f.v, returnRip, callerSP, restoredNV);
    }

    private static final class Frame {
        private final GovernmentCrtBoundary185Api.Entry entry;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls calls;
        private final long e;
        private final long image;
        private final long work;
        private final GovernmentPrimaryTail155Api.NonvolatileBits active;
        private GovernmentPrimaryTail155Api.VolatileBits v;
        private boolean cleanupSeen;

        Frame(GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls) {
            this.entry = entry;
            this.memory = memory;
            this.calls = calls;
            this.e = entry.rspBits();
            this.image = entry.imageBaseBits();
            this.work = this.e - 0x28L;
            this.v = entry.volatileBits();
            GovernmentPrimaryTail155Api.NonvolatileBits nv = entry.nonvolatileBits();
            int ecx = (int)this.v.rcxBits();
            this.active = new GovernmentPrimaryTail155Api.NonvolatileBits(
                Integer.toUnsignedLong(ecx),
                nv.rbpBits(),
                nv.rsiBits(),
                nv.rdiBits(),
                nv.r12Bits(),
                nv.r13Bits(),
                nv.r14Bits(),
                nv.r15Bits(),
                nv.xmm6()
            );
            this.cleanupSeen = false;
        }

        private void args(long rax, long rcx, long rdx, long r8, long r9) {
            v = new GovernmentPrimaryTail155Api.VolatileBits(rax, rcx, rdx, r8, r9, v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
        }

        private long invoke(long site, GovernmentCrtBoundary185Api.TargetKind kind, long target) {
            memory.writeQword(work - 8, image + site + 6);
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(site, kind, target, work, v, active);
            v = calls.invoke(call);
            return v.raxBits();
        }
    }

    private static final class MemoryView implements ModuleLookup221Api.Memory {
        private final Frame f;

        MemoryView(Frame f) {
            this.f = f;
        }

        @Override
        public long readPointer(long address) {
            return f.memory.readQword(address);
        }

        @Override
        public int readInt32(long address) {
            return f.memory.readDword(address);
        }

        @Override
        public void writeInt32(long address, int value) {
            f.memory.writeDword(address, value);
        }

        @Override
        public void writeInt64(long address, long value) {
            f.memory.writeQword(address, value);
        }
    }

    private static final class BusinessPorts implements ModuleLookup221Api.Ports {
        private final Frame f;
        BusinessPorts(Frame f) { this.f = f; }

        @Override
        public int call43da458(ModuleLookup221Api.Memory memory, long siteRva, long codeTarget, long rcx, long rdx, long r8) {
            f.args(f.v.raxBits(), rcx, rdx, r8, f.v.r9Bits());
            f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, codeTarget);
            return (int) f.v.raxBits();
        }

        @Override
        public long call43da680(ModuleLookup221Api.Memory memory, long siteRva, long codeTarget, long rcx, long rdx) {
            f.args(f.v.raxBits(), rcx, rdx, f.v.r8Bits(), f.v.r9Bits());
            f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, codeTarget);
            return f.v.raxBits();
        }

        @Override
        public void call43dbba8(ModuleLookup221Api.Memory memory, long siteRva, long codeTarget, int ecx, long rax) {
            f.args(rax, Integer.toUnsignedLong(ecx), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
            f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, codeTarget);
        }

        @Override
        public void call43da7c0(ModuleLookup221Api.Memory memory, long siteRva, long codeTarget, long rcx) {
            f.args(f.v.raxBits(), rcx, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
            f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, codeTarget);
            f.cleanupSeen = true;
        }
    }
}
