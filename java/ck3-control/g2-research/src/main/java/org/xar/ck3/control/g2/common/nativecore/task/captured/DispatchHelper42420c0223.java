package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper218Api;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper42420C0;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import java.util.Objects;

public final class DispatchHelper42420c0223 {
    private DispatchHelper42420c0223() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        long e = entry.rspBits();
        long image = entry.imageBaseBits();
        long work = e - 0x28L;

        // Prologue: save RBX, R9, push RDI
        memory.writeQword(e + 8L, entry.nonvolatileBits().rbxBits());
        memory.writeQword(e + 0x20L, entry.volatileBits().r9Bits());
        memory.writeQword(e - 8L, entry.nonvolatileBits().rdiBits());

        // Active NV: RBX=entryR9, RDI=entryR8, others from entry
        NonvolatileBits activeNV = new NonvolatileBits(
            entry.volatileBits().r9Bits(),
            entry.nonvolatileBits().rbpBits(),
            entry.nonvolatileBits().rsiBits(),
            entry.volatileBits().r8Bits(),
            entry.nonvolatileBits().r12Bits(),
            entry.nonvolatileBits().r13Bits(),
            entry.nonvolatileBits().r14Bits(),
            entry.nonvolatileBits().r15Bits(),
            entry.nonvolatileBits().xmm6()
        );

        // Current V: exact entry V
        VolatileBits v = entry.volatileBits();

        // Input for existing M3 business
        DispatchHelper218Api.Input input = new DispatchHelper218Api.Input(
            v.rdxBits(),
            v.r8Bits(),
            v.r9Bits()
        );

        // Shared Frame
        Frame f = new Frame(memory, calls, image, work, v, activeNV);

        // Execute existing M3 business exactly once
        long finalRax = DispatchHelper42420C0.execute(f, f, input);

        // Epilogue: fresh reads
        long rbx = memory.readQword(e + 8L);
        long rdi = memory.readQword(e - 8L);
        long retRip = memory.readQword(e);

        // Restored NV
        NonvolatileBits restoredNV = new NonvolatileBits(
            rbx,
            entry.nonvolatileBits().rbpBits(),
            entry.nonvolatileBits().rsiBits(),
            rdi,
            entry.nonvolatileBits().r12Bits(),
            entry.nonvolatileBits().r13Bits(),
            entry.nonvolatileBits().r14Bits(),
            entry.nonvolatileBits().r15Bits(),
            entry.nonvolatileBits().xmm6()
        );

        // Final V is the current v after business execution
        return new GovernmentCrtBoundary185Api.NormalReturn(
            f.v,
            retRip,
            e + 8L,
            restoredNV
        );
    }

    private static final class Frame implements NativeTaskMemory, DispatchHelper218Api.Ports {
        private final GovernmentCrtBoundary185Api.Memory mem;
        private final GovernmentCrtBoundary185Api.Calls calls;
        private final long image;
        private final long work;
        private VolatileBits v;
        private final NonvolatileBits activeNV;

        Frame(GovernmentCrtBoundary185Api.Memory mem, GovernmentCrtBoundary185Api.Calls calls, long image, long work, VolatileBits v, NonvolatileBits activeNV) {
            this.mem = mem;
            this.calls = calls;
            this.image = image;
            this.work = work;
            this.v = v;
            this.activeNV = activeNV;
        }

        // NativeTaskMemory methods
        public long readPointer(long address) {
            return mem.readQword(address);
        }

        public int readInt32(long address) {
            int val = mem.readDword(address);
            // Update RCX in current V
            v = new VolatileBits(
                v.raxBits(),
                Integer.toUnsignedLong(val),
                v.rdxBits(),
                v.r8Bits(),
                v.r9Bits(),
                v.r10Bits(),
                v.r11Bits(),
                v.xmm0(),
                v.xmm1(),
                v.xmm2(),
                v.xmm3(),
                v.xmm4(),
                v.xmm5()
            );
            return val;
        }

        public void writeInt32(long address, int value) {
            mem.writeDword(address, value);
        }

        public void writeInt64(long address, long value) {
            mem.writeQword(address, value);
        }

        // DispatchHelper218Api.Ports methods
        public void enter(NativeTaskMemory memory, long siteRva, int ecx) {
            // Site 0x42420D7, Target 0x4247FFC
            long target = 0x4247FFCL;
            long site = 0x42420D7L;

            // Write return address
            mem.writeQword(work - 8L, image + site + 5L);

            // Construct Call
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                target,
                work,
                v,
                activeNV
            );

            // Invoke
            VolatileBits returned = calls.invoke(call);
            Objects.requireNonNull(returned);
            v = returned;
        }

        public void call42420f8(NativeTaskMemory memory, long siteRva, long rcx) {
            // Site 0x42420E0, Target 0x42420F8
            long target = 0x42420F8L;
            long site = 0x42420E0L;

            // Set RCX to passed rcx (saved entry R8)
            v = new VolatileBits(
                v.raxBits(),
                rcx,
                v.rdxBits(),
                v.r8Bits(),
                v.r9Bits(),
                v.r10Bits(),
                v.r11Bits(),
                v.xmm0(),
                v.xmm1(),
                v.xmm2(),
                v.xmm3(),
                v.xmm4(),
                v.xmm5()
            );

            // Write return address
            mem.writeQword(work - 8L, image + site + 5L);

            // Construct Call
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                target,
                work,
                v,
                activeNV
            );

            // Invoke
            VolatileBits returned = calls.invoke(call);
            Objects.requireNonNull(returned);
            v = returned;
        }

        public long leave(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx) {
            // Site 0x42420E8, Target 0x4248050
            long target = 0x4248050L;
            long site = 0x42420E8L;

            // Write return address
            mem.writeQword(work - 8L, image + site + 5L);

            // Construct Call
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                target,
                work,
                v,
                activeNV
            );

            // Invoke
            VolatileBits returned = calls.invoke(call);
            Objects.requireNonNull(returned);
            v = returned;

            return v.raxBits();
        }
    }
}