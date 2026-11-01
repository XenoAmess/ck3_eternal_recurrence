package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api;
import org.xar.ck3.research.m3.span228.CallbackSpan424E1AC;
import org.xar.ck3.control.g2.common.nativecore.task.captured.DispatchMiddle42420f8224;

public final class CallbackSpan424e1ac231 {
    private CallbackSpan424e1ac231() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            DispatchMiddle42420f8224.Memory32 memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        Frame f = new Frame(entry, memory, calls);

        // 1. Physical prologue: save incoming NV to stack slots in source order
        // E = entry.rspBits(). Work = E - 0x28.
        // [E+8] = work + 0x30
        // [E+10] = work + 0x38
        // [E+18] = work + 0x40
        // [E-8] = work + 0x20
        f.memory.writeQword(f.e + 8L, f.entry.nonvolatileBits().rbxBits());
        f.memory.writeQword(f.e + 0x10L, f.entry.nonvolatileBits().rbpBits());
        f.memory.writeQword(f.e + 0x18L, f.entry.nonvolatileBits().rsiBits());
        f.memory.writeQword(f.e - 8L, f.entry.nonvolatileBits().rdiBits());

        // 2. Invoke CallbackSpan424E1AC span228 business logic exactly once
        // Input: moduleBase = image, startAddress = entryV.rcxBits(), endAddress = entryV.rdxBits()
        CallbackSpan228Api.Input input = new CallbackSpan228Api.Input(
            f.image,
            f.v.rcxBits(),
            f.v.rdxBits()
        );

        // Ports implementation
        Ports ports = new Ports(f);
        // Memory adapter implementation
        MemoryAdapter memAdapter = new MemoryAdapter(f);

        CallbackSpan424E1AC.execute(memAdapter, ports, input);

        // 3. Outcome handling (NormalReturn path)
        // Fresh physical reads in source order for epilogue
        long rbx = f.memory.readQword(f.e + 8L);
        long rbp = f.memory.readQword(f.e + 0x10L);
        long rsi = f.memory.readQword(f.e + 0x18L);
        long rdi = f.memory.readQword(f.e - 8L);
        long retRip = f.memory.readQword(f.e);

        // Construct restored NonvolatileBits
        NonvolatileBits restoredNV = new NonvolatileBits(
            rbx,
            rbp,
            rsi,
            rdi,
            f.entry.nonvolatileBits().r12Bits(),
            f.entry.nonvolatileBits().r13Bits(),
            f.entry.nonvolatileBits().r14Bits(),
            f.entry.nonvolatileBits().r15Bits(),
            f.entry.nonvolatileBits().xmm6()
        );

        // Return NormalReturn with current whole V, fresh restored NV, return RIP, callerSP=E+8
        return new NormalReturn(f.v, retRip, f.e + 8L, restoredNV);
    }

    private static final class Frame {
        final Entry entry;
        final DispatchMiddle42420f8224.Memory32 memory;
        final GovernmentCrtBoundary185Api.Calls calls;
        final long e, image, work;
        NonvolatileBits activeNV;
        VolatileBits v;
        long ordinal;
        long currentOrdinal;
        long currentElementAddress;
        long sourceCount;
        boolean isElementRead;

        Frame(Entry entry, DispatchMiddle42420f8224.Memory32 memory, GovernmentCrtBoundary185Api.Calls calls) {
            this.entry = Objects.requireNonNull(entry);
            this.memory = Objects.requireNonNull(memory);
            this.calls = Objects.requireNonNull(calls);
            this.e = entry.rspBits();
            this.image = entry.imageBaseBits();
            this.work = this.e - 0x28L;
            this.v = entry.volatileBits();
            this.ordinal = 0;
            this.currentElementAddress = 0L;
            this.sourceCount = 0L;
            this.isElementRead = false;

            // Compute sourceCount from entry RCX/RDX using unsigned comparison logic
            long start = entry.volatileBits().rcxBits();
            long end = entry.volatileBits().rdxBits();
            if (Long.compareUnsigned(start, end) <= 0) {
                this.sourceCount = (end - start + 7L) >>> 3;
            } else {
                this.sourceCount = 0L;
            }

            // Active NV: RBX=0, RBP=0, RSI=0, RDI=sourceCount, others from entry
            this.activeNV = new NonvolatileBits(
                0L,
                0L,
                0L,
                this.sourceCount,
                entry.nonvolatileBits().r12Bits(),
                entry.nonvolatileBits().r13Bits(),
                entry.nonvolatileBits().r14Bits(),
                entry.nonvolatileBits().r15Bits(),
                entry.nonvolatileBits().xmm6()
            );
        }

        void args(long rax, long rcx, long rdx, long r8, long r9) {
            v = new VolatileBits(rax, rcx, rdx, r8, r9, v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
        }

        long invoke(long site, TargetKind kind, long target, int instructionLength) {
            memory.writeQword(work - 8L, image + site + instructionLength);
            Call call = new Call(site, kind, target, work, v, activeNV);
            VolatileBits returned = calls.invoke(call);
            Objects.requireNonNull(returned);
            v = returned;
            return returned.raxBits();
        }
    }

    private static final class MemoryAdapter implements CallbackSpan228Api.Memory {
        private final Frame f;
        MemoryAdapter(Frame f) { this.f = Objects.requireNonNull(f); }

        public long readPointer(long address) {
            long value = f.memory.readQword(address);
            if (!f.isElementRead) {
                // First readPointer is the element address
                f.currentElementAddress = address;
                f.currentOrdinal = f.ordinal++;
                f.isElementRead = value != 0L;
                // Update RAX with the value read (element value)
                f.args(value, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
            } else {
                // Second readPointer is the IAT target
                f.isElementRead = false;
            }
            return value;
        }

        public int readInt32(long address) {
            return f.memory.readDword(address);
        }

        public void writeInt32(long address, int value) {
            f.memory.writeDword(address, value);
        }

        public void writeInt64(long address, long value) {
            f.memory.writeQword(address, value);
        }

        public int readUnsigned8(long address) {
            return f.memory.readUnsignedByte(address);
        }

        public int readUnsigned16(long address) {
            return f.memory.readUnsigned16(address);
        }

        public void write8(long address, int value) {
            f.memory.writeByte(address, value);
        }

        public void exchangeInt32(long address, int value) {
            f.memory.exchangeDword(address, value);
        }
    }

    private static final class Ports implements CallbackSpan228Api.Ports {
        private final Frame f;
        Ports(Frame f) { this.f = Objects.requireNonNull(f); }

        public void call43dbba8(CallbackSpan228Api.Memory m, long siteRva, long actualTarget,
                        long liveRax, CallbackSpan228Api.Arguments arguments) {
            // Update active NV based on business state
            // RBX = current element address
            // RBP = 0
            // RSI = current element ordinal (advancing all element events)
            // RDI = source count
            f.activeNV = new NonvolatileBits(
                f.currentElementAddress,
                0L,
                f.currentOrdinal,
                f.sourceCount,
                f.entry.nonvolatileBits().r12Bits(),
                f.entry.nonvolatileBits().r13Bits(),
                f.entry.nonvolatileBits().r14Bits(),
                f.entry.nonvolatileBits().r15Bits(),
                f.entry.nonvolatileBits().xmm6()
            );

            // Prepare arguments for the call
            // RAX = liveRax (the element value)
            // RCX/RDX: entry on first callback and actual previous post V thereafter
            f.args(liveRax, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());

            // Invoke the call
            f.invoke(0x424E1E9L, TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);

        }
    }
}