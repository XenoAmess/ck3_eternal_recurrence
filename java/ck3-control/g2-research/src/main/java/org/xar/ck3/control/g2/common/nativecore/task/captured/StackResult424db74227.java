package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.stack229.StackContext229Api;
import org.xar.ck3.research.m3.stack229.StackContext424DB74;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class StackResult424db74227 {
    private StackResult424db74227() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        long e = entry.rspBits();
        long image = entry.imageBaseBits();
        long w = e - 0x28L;

        VolatileBits entryV = entry.volatileBits();
        NonvolatileBits entryNV = entry.nonvolatileBits();

        // Physical prologue writes (source order)
        memory.writeQword(e + 8L, entryNV.rbxBits());
        memory.writeQword(e + 0x20L, entryV.r9Bits());
        memory.writeQword(e - 8L, entryNV.rdiBits());

        // Active NV for the body: RBX=entryR9, RDI=entryR8, others from entryNV
        NonvolatileBits activeNV = new NonvolatileBits(
            entryV.r9Bits(), // RBX
            entryNV.rbpBits(),
            entryNV.rsiBits(),
            entryV.r8Bits(), // RDI
            entryNV.r12Bits(),
            entryNV.r13Bits(),
            entryNV.r14Bits(),
            entryNV.r15Bits(),
            entryNV.xmm6()
        );

        // Mutable current V
        VolatileBits[] currentV = new VolatileBits[1];
        currentV[0] = entryV;

        // Native4 View
        NativeTaskMemory nativeView = new Native4View(memory);

        // Ports Implementation
        StackContext229Api.Ports ports = new PortsImpl(image, w, currentV, activeNV, calls, memory);

        // Input for M3 business
        StackContext229Api.Input input = new StackContext229Api.Input(
            entryV.rdxBits(), // RDX address
            entryV.r8Bits(),  // R8 address
            entryV.r9Bits()   // R9 address
        );

        // Run M3 business exactly once
        long oldResult = StackContext424DB74.execute(nativeView, ports, input);

        // Source DBA2: RAX = zeroExtend32(oldResult)
        currentV[0] = new VolatileBits(
            Integer.toUnsignedLong((int) oldResult), // RAX
            currentV[0].rcxBits(),
            currentV[0].rdxBits(),
            currentV[0].r8Bits(),
            currentV[0].r9Bits(),
            currentV[0].r10Bits(),
            currentV[0].r11Bits(),
            currentV[0].xmm0(),
            currentV[0].xmm1(),
            currentV[0].xmm2(),
            currentV[0].xmm3(),
            currentV[0].xmm4(),
            currentV[0].xmm5()
        );

        // Epilogue reads
        long freshRBX = memory.readQword(e + 8L);
        long freshRDI = memory.readQword(e - 8L);
        long actualRetRip = memory.readQword(e);

        // Final NV: fresh RBX, fresh RDI, others from entryNV
        NonvolatileBits finalNV = new NonvolatileBits(
            freshRBX,
            entryNV.rbpBits(),
            entryNV.rsiBits(),
            freshRDI,
            entryNV.r12Bits(),
            entryNV.r13Bits(),
            entryNV.r14Bits(),
            entryNV.r15Bits(),
            entryNV.xmm6()
        );

        return new GovernmentCrtBoundary185Api.NormalReturn(
            currentV[0],
            actualRetRip,
            e + 8L,
            finalNV
        );
    }

    private static final class Native4View implements NativeTaskMemory {
        private final GovernmentCrtBoundary185Api.Memory mem;
        Native4View(GovernmentCrtBoundary185Api.Memory mem) {
            this.mem = Objects.requireNonNull(mem);
        }
        @Override public long readPointer(long address) { return mem.readQword(address); }
        @Override public int readInt32(long address) { return mem.readDword(address); }
        @Override public void writeInt32(long address, int value) { mem.writeDword(address, value); }
        @Override public void writeInt64(long address, long value) { mem.writeQword(address, value); }
    }

    private static final class PortsImpl implements StackContext229Api.Ports {
        private final long image;
        private final long w;
        private final VolatileBits[] currentV;
        private NonvolatileBits activeNV;
        private final GovernmentCrtBoundary185Api.Calls calls;
        private final GovernmentCrtBoundary185Api.Memory mem;

        PortsImpl(long image, long w, VolatileBits[] currentV, NonvolatileBits activeNV, GovernmentCrtBoundary185Api.Calls calls, GovernmentCrtBoundary185Api.Memory mem) {
            this.image = image;
            this.w = w;
            this.currentV = currentV;
            this.activeNV = activeNV;
            this.calls = calls;
            this.mem = mem;
        }

        @Override public void call4247ffc(NativeTaskMemory memory, long siteRva, int ecx) {
            // Site 0x424DB8B, Target 0x4247FFC, Len 5
            // RCX = u32(ecx), others from currentV
            VolatileBits v = currentV[0];
            VolatileBits newV = new VolatileBits(
                v.raxBits(),
                Integer.toUnsignedLong(ecx), // RCX
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
            currentV[0] = newV;

            // Push return address
            mem.writeQword(w - 8L, image + 0x424DB90L);

            // Invoke
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                0x424DB8BL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x4247FFCL,
                w,
                newV,
                activeNV
            );
            VolatileBits reply = calls.invoke(call);
            Objects.requireNonNull(reply);
            currentV[0] = reply;
        }

        @Override public long call424dd60(NativeTaskMemory memory, long siteRva, long rcx) {
            // Site 0x424DB94, Target 0x424DD60, Len 5
            // RCX = passed rcx (saved entryR8), others from currentV (ENTER reply)
            VolatileBits v = currentV[0];
            VolatileBits newV = new VolatileBits(
                v.raxBits(),
                rcx, // RCX
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
            currentV[0] = newV;

            // Push return address
            mem.writeQword(w - 8L, image + 0x424DB99L);

            // Invoke
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                0x424DB94L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x424DD60L,
                w,
                newV,
                activeNV
            );
            VolatileBits reply = calls.invoke(call);
            Objects.requireNonNull(reply);
            currentV[0] = reply;

            // Source DB99: MOV EDI, EAX -> active RDI = u32(midRAX)
            activeNV = new NonvolatileBits(
                activeNV.rbxBits(),
                activeNV.rbpBits(),
                activeNV.rsiBits(),
                Integer.toUnsignedLong((int) reply.raxBits()),
                activeNV.r12Bits(),
                activeNV.r13Bits(),
                activeNV.r14Bits(),
                activeNV.r15Bits(),
                activeNV.xmm6()
            );

            return reply.raxBits();
        }

        @Override public void call4248050(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx) {
            // Site 0x424DB9D, Target 0x4248050, Len 5
            // RCX = u32(ecx), others from currentV (MID reply)
            VolatileBits v = currentV[0];
            VolatileBits newV = new VolatileBits(
                v.raxBits(),
                Integer.toUnsignedLong(ecx), // RCX
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
            currentV[0] = newV;

            // Source DB9B/DB9D context: RBX active is liveRbx (saved entryR9)
            activeNV = new NonvolatileBits(
                liveRbx,
                activeNV.rbpBits(),
                activeNV.rsiBits(),
                activeNV.rdiBits(),
                activeNV.r12Bits(),
                activeNV.r13Bits(),
                activeNV.r14Bits(),
                activeNV.r15Bits(),
                activeNV.xmm6()
            );

            // Push return address
            mem.writeQword(w - 8L, image + 0x424DBA2L);

            // Invoke
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                0x424DB9DL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x4248050L,
                w,
                newV,
                activeNV
            );
            VolatileBits reply = calls.invoke(call);
            Objects.requireNonNull(reply);
            currentV[0] = reply;
        }
    }
}