package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owned normal translation of 34F04D0..34F052D; lower calls retain their actual ports. */
public final class LoadRowReferenceStorage34f04d0196 {
    private LoadRowReferenceStorage34f04d0196() { }

    public static NormalReturn execute(Entry entry, Memory memory, Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        long image = entry.imageBaseBits();
        long rsp = entry.rspBits() - 0x28L;
        // GS points at the actual module slot. The DWORD load writes EAX, clearing upper RAX.
        long gs = calls.readGsQword58();
        long module = memory.readQword(gs);
        int epoch = memory.readDword(module + 0x10L);
        VolatileBits before = entry.volatileBits();
        VolatileBits v = first(before, Integer.toUnsignedLong(epoch), module, 0x10L);
        long guard = image + 0x5D75ED8L;
        // CMP DWORD[guard], EAX; JG uses signed 32-bit operands.
        if (memory.readDword(guard) > epoch) {
            v = first(v, v.raxBits(), guard, v.rdxBits());
            v = call(entry, memory, calls, rsp, 0x34F0503L, 0x4223A84L, v);
            // The header port can change guard and every represented volatile bit.
            if (memory.readDword(guard) == -1) {
                v = first(v, v.raxBits(), guard, v.rdxBits());
                memory.writeByte(image + 0x5D75EE4L, 0);
                memory.writeByte(image + 0x5D75F14L, 0xFF);
                v = call(entry, memory, calls, rsp, 0x34F0526L, 0x4223A24L, v);
            }
        }
        v = first(v, image + 0x5D75EE0L, v.rcxBits(), v.rdxBits());
        rsp += 0x28L;
        return new NormalReturn(v, memory.readQword(rsp), rsp + 8L, entry.nonvolatileBits());
    }

    private static VolatileBits first(VolatileBits v, long rax, long rcx, long rdx) {
        return new VolatileBits(rax, rcx, rdx, v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
    }

    private static VolatileBits call(Entry entry, Memory memory, Calls calls, long rsp,
                                    long site, long target, VolatileBits v) {
        memory.writeQword(rsp - 8L, entry.imageBaseBits() + site + 5L);
        return Objects.requireNonNull(calls.invoke(new Call(site, TargetKind.DIRECT_RVA, target,
                rsp, v, entry.nonvolatileBits())));
    }
}
