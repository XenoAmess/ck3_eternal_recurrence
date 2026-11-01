package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api.Memory;
import org.xar.ck3.research.m3.abort220.TerminalAbort4242284;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalTailTarget42421c8213.Memory16;

/** Owned full normal-port frames until a software INT3 boundary; no native nonreturn promise. */
public final class TerminalAbort4242284215 {
    private TerminalAbort4242284215() { }
    public interface Calls60 extends Calls { long readGsQword60(); }

public static GovernmentPrimaryTail155Api.VolatileBits execute(GovernmentCrtBoundary185Api.Entry entry, TerminalTailTarget42421c8213.Memory16 memory, TerminalAbort4242284215.Calls60 calls) {
    Frame f = new Frame(entry, memory, calls);
    f.memory.writeQword(f.e - 8L, f.entry.nonvolatileBits().rbxBits());
    int entryEcx = (int) entry.volatileBits().rcxBits();
    TerminalAbort220Api.Input input = new TerminalAbort220Api.Input(f.image, entryEcx, new TerminalAbort220Api.Scratch(f.e));
    TerminalAbort220Api.Trap trap = TerminalAbort4242284.execute(new MemoryView(f), new BusinessPorts(f), input);
    throw new UnsupportedOperationException("Owned INT3 boundary reached at 42422CD");
  }

private static final class Frame {
    final Entry entry;
    final Memory16 memory;
    final Calls60 calls;
    final long e, image, work;
    final NonvolatileBits active;
    VolatileBits v;
    boolean gsPending;
    long gsAddress;
private Frame(Entry entry, Memory16 memory, Calls60 calls) {
    this.entry = Objects.requireNonNull(entry);
    this.memory = Objects.requireNonNull(memory);
    this.calls = Objects.requireNonNull(calls);
    this.e = entry.rspBits();
    this.image = entry.imageBaseBits();
    this.work = this.e - 0x28L;
    NonvolatileBits incomingNV = entry.nonvolatileBits();
    long rbxVal = Integer.toUnsignedLong((int) entry.volatileBits().rcxBits());
    this.active = new NonvolatileBits(
        rbxVal,
        incomingNV.rbpBits(),
        incomingNV.rsiBits(),
        incomingNV.rdiBits(),
        incomingNV.r12Bits(),
        incomingNV.r13Bits(),
        incomingNV.r14Bits(),
        incomingNV.r15Bits(),
        incomingNV.xmm6()
    );
    this.v = entry.volatileBits();
    this.gsPending = false;
    this.gsAddress = 0L;
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
}

private static final class MemoryView implements TerminalAbort220Api.Memory {
    private final Frame f;
    MemoryView(Frame f) { this.f = f; }
    @Override public long readPointer(long address) { return f.memory.readQword(address); }
    @Override public int readInt32(long address) {
        int raw = f.memory.readDword(address);
        if (f.gsPending && address == f.gsAddress + 0xBC) {
            f.args(f.v.raxBits(), f.v.rcxBits(), Integer.toUnsignedLong(raw) >>> 8, f.v.r8Bits(), f.v.r9Bits());
            f.gsPending = false;
        }
        return raw;
    }
    @Override public void writeInt32(long address, int value) { f.memory.writeDword(address, value); }
    @Override public void writeInt64(long address, long value) { f.memory.writeQword(address, value); }
    @Override public int readUnsigned8(long address) { return f.memory.readUnsignedByte(address); }
    @Override public int readUnsigned16(long address) { return f.memory.readUnsigned16(address); }
    @Override public void write8(long address, int value) { f.memory.writeByte(address, value); }
}

private static final class BusinessPorts implements TerminalAbort220Api.Ports {
    private final Frame f;
    BusinessPorts(Frame f) { this.f = f; }

    @Override public int call42591f8(Memory memory, long siteRva, int entryEcx) {
        // Direct call to 42591F8@424228C (len 5). Does not edit any volatile input before call.
        // The old business logic compares low EAX == 1, but we must preserve full RAX and other V.
        // We invoke the port, which returns the full VolatileBits. We extract low 32 bits for the return value.
        long rax = f.invoke(0x424228CL, TargetKind.DIRECT_RVA, 0x42591F8L, 5);
        return (int) rax;
    }

    @Override public long readGs60(Memory memory, long siteRva) {
        // GS60 callback source 4242296. Explicit new calls.readGsQword60() dynamic.
        // Assign full RAX = returned gsPointer, keep other actual V, set pending GS address.
        long gsPointer = f.calls.readGsQword60();
        f.gsAddress = gsPointer;
        f.gsPending = true;
        // Update RAX in current V, keep others
        f.args(gsPointer, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
        return gsPointer;
    }

    @Override public long call43da798(Memory memory, long siteRva, long actualTarget, long liveRax, int liveEdx) {
        // Indirect absolute call to 43DA798@42422AD (len 6).
        // RAX = passed liveRax, RDX = z32 passed liveEdx, RCX stays ACTUAL previous normal V.RCX.
        // R8/R9/R10/R11/XMM carried.
        long rcx = f.v.rcxBits();
        long rdx = Integer.toUnsignedLong(liveEdx);
        f.args(liveRax, rcx, rdx, f.v.r8Bits(), f.v.r9Bits());
        return f.invoke(0x42422ADL, TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
    }

    @Override public void call43da778(Memory memory, long siteRva, long actualTarget, long rcx, int edx) {
        // Indirect absolute call to 43DA778@42422B8 (len 6).
        // Full RCX = passed rax handle (rcx param), RDX = z32 passed edx, all other V including RAX carried.
        long rax = f.v.raxBits();
        long rdx = Integer.toUnsignedLong(edx);
        f.args(rax, rcx, rdx, f.v.r8Bits(), f.v.r9Bits());
        f.invoke(0x42422B8L, TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
    }

    @Override public void call42422d0(Memory memory, long siteRva, int ecx, long childEntryRsp) {
        // Direct call to 42422D0@42422C0 (len 5).
        // RCX = z32 ecx ONLY, others full V branch-dependent carried.
        // childEntryRsp = E - 30 matches W - 8, Call already encodes preSP W.
        long rcx = Integer.toUnsignedLong(ecx);
        f.args(f.v.raxBits(), rcx, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
        f.invoke(0x42422C0L, TargetKind.DIRECT_RVA, 0x42422D0L, 5);
    }

    @Override public void call43da558(Memory memory, long siteRva, long actualTarget, int ecx) {
        // Indirect absolute call to 43DA558@42422C7 (len 6).
        // RCX = z32 ecx ONLY, all other V from preceding normal 42422D0 result.
        long rcx = Integer.toUnsignedLong(ecx);
        f.args(f.v.raxBits(), rcx, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
        f.invoke(0x42422C7L, TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
    }
}
}
