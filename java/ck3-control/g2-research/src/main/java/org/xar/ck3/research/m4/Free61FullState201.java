package org.xar.ck3.research.m4;

import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.AddressFree83Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Normal-return ABI projection of held [424E364,424E3A1); RFLAGS/EH are not represented. */
public final class Free61FullState201 {
    private Free61FullState201() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        if (r.rcx != 0L) {
            long block = r.rcx;
            r.rsp -= 8L;
            memory.writeQword(r.rsp, r.rbx);
            r.rsp -= 0x20L;
            r.r8 = block;
            r.rdx = 0L;
            AddressFree83Consumer.execute(
                    new Lower61Inputs.CallInput(entry.imageBaseBits(), block),
                    new MemoryView(memory), new CallsView(entry.imageBaseBits(), r, memory, calls));
            r.rsp += 0x20L;
            r.rbx = memory.readQword(r.rsp);
            r.rsp += 8L;
        }
        long rip = memory.readQword(r.rsp);
        return new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), rip, r.rsp + 8L, r.nonvolatileBits());
    }

    /** No storage: all effects operate on the original full-state memory. */
    private record MemoryView(GovernmentCrtBoundary185Api.Memory memory) implements Lower61Inputs.Memory {
        @Override public long readPointer(long address) { return memory.readQword(address); }
        @Override public int readInt32(long address) { return memory.readDword(address); }
        @Override public void writeInt32(long address, int value) { memory.writeDword(address, value); }
        @Override public void writeInt64(long address, long value) { memory.writeQword(address, value); }
    }

    private record CallsView(long image, Registers r, GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) implements Lower61Inputs.Calls {
        private void invoke(long site, GovernmentCrtBoundary185Api.TargetKind kind, long target, int length) {
            // The opaque normal-return port owns callee RET; Call.rspBits is the pre-CALL SP.
            memory.writeQword(r.rsp - 8L, image + site + length);
            r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(
                    site, kind, target, r.rsp, r.volatileBits(), r.nonvolatileBits())));
        }

        @Override public int callSlot43DA748(Lower61Inputs.FirstCall known) {
            r.rcx = known.rcxRaw();
            r.rdx = known.rdxRaw();
            r.r8 = known.r8Raw();
            long target = memory.readQword(image + 0x43DA748L);
            invoke(0x424E37AL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target, 6);
            return (int) r.rax;
        }

        @Override public long call423B18C() {
            invoke(0x424E384L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x423B18CL, 5);
            r.rbx = r.rax;
            return r.rax;
        }

        @Override public int callSlot43DA738() {
            long target = memory.readQword(image + 0x43DA738L);
            invoke(0x424E38CL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target, 6);
            return (int) r.rax;
        }

        @Override public int call423B0D4(long knownRcxRaw) {
            r.rcx = knownRcxRaw;
            invoke(0x424E394L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x423B0D4L, 5);
            return (int) r.rax;
        }
    }
}
