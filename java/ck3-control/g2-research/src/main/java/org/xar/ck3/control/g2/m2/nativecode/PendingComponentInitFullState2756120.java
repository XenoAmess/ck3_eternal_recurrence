package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;
import java.util.Objects;

public final class PendingComponentInitFullState2756120 {
    private PendingComponentInitFullState2756120() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input, FullCopy437Api.Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        Objects.requireNonNull(entry);

        GovernmentPrimaryTail155Api.VolatileBits vIn = entry.volatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits nIn = entry.nonvolatileBits();

        // Actual incoming RCX is the component address, not RDI.
        long componentAddress = vIn.rcxBits();
        long moduleBase = entry.imageBaseBits();

        // Forwarding adapter for mature Data initializer
        PendingComponentInit2756120.Memory adapter = new PendingComponentInit2756120.Memory() {
            @Override
            public void write8(long address, int value) {
                memory.writeByte(address, value);
            }
            @Override
            public void write32(long address, int value) {
                memory.writeDword(address, value);
            }
            @Override
            public void write64(long address, long value) {
                memory.writeQword(address, value);
            }
        };

        // Execute mature Data initializer exactly once
        long finalRax = PendingComponentInit2756120.initialize(adapter, componentAddress, moduleBase);

        // Derive final state from ASM source
        // RAX: returned by initialize (mov rax,rcx at 275617B)
        long rax = finalRax;

        // RCX: Unchanged (componentAddress)
        long rcx = componentAddress;

        // RDX: Set by lea rdx,[rip+0x2d9019f] at 2756132
        long rdx = moduleBase + 0x54E62D8L;

        // R8: Set by xor r8d,r8d at 2756120 (zero-extended)
        long r8 = 0L;

        // R9, R10, R11: Unchanged from input
        long r9 = vIn.r9Bits();
        long r10 = vIn.r10Bits();
        long r11 = vIn.r11Bits();

        // XMM0..5: Unchanged from input
        GovernmentPrimaryTail155Api.Bits128 x0 = vIn.xmm0();
        GovernmentPrimaryTail155Api.Bits128 x1 = vIn.xmm1();
        GovernmentPrimaryTail155Api.Bits128 x2 = vIn.xmm2();
        GovernmentPrimaryTail155Api.Bits128 x3 = vIn.xmm3();
        GovernmentPrimaryTail155Api.Bits128 x4 = vIn.xmm4();
        GovernmentPrimaryTail155Api.Bits128 x5 = vIn.xmm5();

        // Nonvolatile Bits: All unchanged (source has no N-register writes)
        long rbx = nIn.rbxBits();
        long rbp = nIn.rbpBits();
        long rsi = nIn.rsiBits();
        long rdi = nIn.rdiBits();
        long r12 = nIn.r12Bits();
        long r13 = nIn.r13Bits();
        long r14 = nIn.r14Bits();
        long r15 = nIn.r15Bits();
        GovernmentPrimaryTail155Api.Bits128 x6 = nIn.xmm6();

        // Fresh RET read after all writes
        long returnRipBits = memory.readQword(entry.rspBits());

        // Caller RSP after RET
        long callerRspBits = entry.rspBits() + 8L;

        // Direction Flag: Unchanged by source (xor/mov/lea/ret do not modify DF)
        boolean postDirectionFlagSet = input.directionFlagSet();

        GovernmentPrimaryTail155Api.VolatileBits finalV = new GovernmentPrimaryTail155Api.VolatileBits(
            rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5
        );

        GovernmentPrimaryTail155Api.NonvolatileBits finalN = new GovernmentPrimaryTail155Api.NonvolatileBits(
            rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6
        );

        GovernmentCrtBoundary185Api.NormalReturn normalReturn = new GovernmentCrtBoundary185Api.NormalReturn(
            finalV, returnRipBits, callerRspBits, finalN
        );

        return new FullCopy437Api.CallResult(normalReturn, postDirectionFlagSet);
    }
}