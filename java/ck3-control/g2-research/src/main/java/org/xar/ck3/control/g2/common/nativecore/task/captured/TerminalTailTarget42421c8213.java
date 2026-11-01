package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;

/** Exact owned normal-frame variant; delegates the existing217 business algorithm once. */
public final class TerminalTailTarget42421c8213 {
    private TerminalTailTarget42421c8213() { }
    public interface Memory16 extends Memory { int readUnsigned16(long addressBits); }

public static NormalReturn execute(Entry entry, Memory16 memory, Calls calls) {
    Frame f = new Frame(entry, memory, calls);
    // 1. Physical prologue: save RBX to [E+8]
    memory.writeQword(f.e + 8L, f.entry.nonvolatileBits().rbxBits());
    // 2. Invoke old217 business logic exactly once
    TerminalTailTarget217Api.Input input = new TerminalTailTarget217Api.Input(
        f.image,
        (int)f.entry.volatileBits().rcxBits(),
        (int)f.entry.volatileBits().rdxBits(),
        (int)f.entry.volatileBits().r8Bits(),
        new TerminalTailTarget217Api.Scratch(f.e)
    );
    TerminalTailTarget217Api.Outcome outcome = TerminalTailTarget217.execute(
        new MemoryView(f),
        new BusinessPorts(f),
        input
    );
    // 3. Outcome handling
    if (outcome instanceof TerminalTailTarget217Api.NormalReturn) {
        // Fresh physical reads in source order
        long rbx = memory.readQword(f.e + 8L);
        long rbp = memory.readQword(f.e - 8L);
        long retRip = memory.readQword(f.e);

        // Construct restored NonvolatileBits
        NonvolatileBits restoredNV = new NonvolatileBits(
            rbx,
            rbp,
            f.entry.nonvolatileBits().rsiBits(),
            f.entry.nonvolatileBits().rdiBits(),
            f.entry.nonvolatileBits().r12Bits(),
            f.entry.nonvolatileBits().r13Bits(),
            f.entry.nonvolatileBits().r14Bits(),
            f.entry.nonvolatileBits().r15Bits(),
            f.entry.nonvolatileBits().xmm6()
        );

        // Return NormalReturn with current whole V, fresh restored NV, return RIP, callerSP=E+8
        return new NormalReturn(f.v, retRip, f.e + 8L, restoredNV);
    } else {
        // Trap.INT3_4242283
        throw new UnsupportedOperationException("Software INT3 boundary at 4242283");
    }
}

private static final class Frame {
    final Entry entry;
    final Memory16 memory;
    final Calls calls;
    final long e, image, work;
    final NonvolatileBits active;
    VolatileBits v;
    int homeWrites;
Frame(Entry entry, Memory16 memory, Calls calls) {
    this.entry = Objects.requireNonNull(entry);
    this.memory = Objects.requireNonNull(memory);
    this.calls = Objects.requireNonNull(calls);
    this.e = entry.rspBits();
    this.image = entry.imageBaseBits();
    this.work = this.e - 0x58L;
    this.v = entry.volatileBits();
    this.homeWrites = 0;

    // Active NV: RBX=z32incomingECX, RBP=E-8, others from entry
    long rbx = Integer.toUnsignedLong((int)this.v.rcxBits());
    long rbp = this.e - 8L;
    this.active = new NonvolatileBits(
        rbx,
        rbp,
        entry.nonvolatileBits().rsiBits(),
        entry.nonvolatileBits().rdiBits(),
        entry.nonvolatileBits().r12Bits(),
        entry.nonvolatileBits().r13Bits(),
        entry.nonvolatileBits().r14Bits(),
        entry.nonvolatileBits().r15Bits(),
        entry.nonvolatileBits().xmm6()
    );
}
void args(long rax,long rcx,long rdx,long r8,long r9) {
    v = new VolatileBits(rax, rcx, rdx, r8, r9, v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
}
long invoke(long site,TargetKind kind,long target,int instructionLength) {
    memory.writeQword(work - 8, image + site + instructionLength);
    VolatileBits returned = calls.invoke(new Call(site, kind, target, work, v, active));
    Objects.requireNonNull(returned);
    v = returned;
    return returned.raxBits();
}
}

private static final class MemoryView implements TerminalTailTarget217Api.Memory {
    private final Frame f;
    MemoryView(Frame f) { this.f = Objects.requireNonNull(f); }
    public long readPointer(long a) { return f.memory.readQword(a); }
    public int readInt32(long a) { return f.memory.readDword(a); }
    public void writeInt32(long a, int value) {
        f.memory.writeDword(a, value);
        f.homeWrites++;
        if (f.homeWrites == 2) {
            f.memory.writeQword(f.e - 8, f.entry.nonvolatileBits().rbpBits());
        }
    }
    public void writeInt64(long a, long value) { f.memory.writeQword(a, value); }
    public int readUnsigned8(long a) { return f.memory.readUnsignedByte(a); }
    public int readUnsigned16(long a) { return f.memory.readUnsigned16(a); }
    public void write8(long a, int value) { f.memory.writeByte(a, value); }
}

private static final class BusinessPorts implements TerminalTailTarget217Api.Ports {
    final Frame f;
    BusinessPorts(Frame f) { this.f = f; }
    public long call43da620(TerminalTailTarget217Api.Memory m, long site, long target, int ecx) {
        f.args(f.v.raxBits(), Integer.toUnsignedLong(ecx), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
        return f.invoke(site, TargetKind.INDIRECT_ABSOLUTE, target, 6);
    }
    public void call42422d0(TerminalTailTarget217Api.Memory m, long site, int ecx) {
        f.args(0x20B, Integer.toUnsignedLong(ecx), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
        f.invoke(site, TargetKind.DIRECT_RVA, 0x42422D0L, 5);
    }
    public long call42420c0(TerminalTailTarget217Api.Memory m, long site, long rcx, long rdx, long r8, long r9) {
        f.args(2, rcx, rdx, r8, r9);
        return f.invoke(site, TargetKind.DIRECT_RVA, 0x42420C0L, 5);
    }
    public void call4242284(TerminalTailTarget217Api.Memory m, long site, int ecx) {
        f.args(f.v.raxBits(), Integer.toUnsignedLong(ecx), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
        f.invoke(site, TargetKind.DIRECT_RVA, 0x4242284L, 5);
    }
}
}
