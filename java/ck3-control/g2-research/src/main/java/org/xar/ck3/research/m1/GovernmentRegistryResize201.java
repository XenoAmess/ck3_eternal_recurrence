package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Normal instruction path of the held 149-byte body at RVA 425B804. */
public final class GovernmentRegistryResize201 {
    private GovernmentRegistryResize201() { }

    public static GovernmentCallee164Api.NormalReturn execute(
            GovernmentCallee164Api.Entry entry, GovernmentPrimaryTail155Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        long image = entry.imageBaseBits();
        var r = GovernmentCallee164Api.registers(entry);
        memory.writeQword(r.rsp + 8, r.rbx);
        memory.writeQword(r.rsp + 0x10, r.rbp);
        memory.writeQword(r.rsp + 0x18, r.rsi);
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.rdi);
        r.rsp -= 0x20;
        r.rbp = r.r8;
        r.rbx = r.rdx;
        r.rsi = r.rcx;

        boolean overflow = false;
        if (r.rdx != 0) {
            r.rdx = 0;
            r.rax = r.rdx - 0x20;
            long dividend = r.rax;
            r.rax = Long.divideUnsigned(dividend, r.rbx);
            r.rdx = Long.remainderUnsigned(dividend, r.rbx);
            overflow = Long.compareUnsigned(r.rax, r.r8) < 0;
        }
        if (overflow) {
            invoke(image, memory, calls, r, 0x425B834L, 0x423B18CL);
            memory.writeDword(r.rax, 12);
            r.rax = 0;
        } else {
            if (r.rsi != 0) {
                invoke(image, memory, calls, r, 0x425B848L, 0x4259250L);
                r.rdi = r.rax;
            } else {
                r.rdi = 0;
            }
            r.rbx *= r.rbp;
            r.rcx = r.rsi;
            r.rdx = r.rbx;
            invoke(image, memory, calls, r, 0x425B85EL, 0x4251F4CL);
            r.rsi = r.rax;
            if (r.rax != 0 && Long.compareUnsigned(r.rdi, r.rbx) < 0) {
                r.rbx -= r.rdi;
                r.rcx = r.rax + r.rdi;
                r.r8 = r.rbx;
                r.rdx = 0;
                invoke(image, memory, calls, r, 0x425B87CL, 0x4226F10L);
            }
            r.rax = r.rsi;
        }
        r.rbx = memory.readQword(r.rsp + 0x30);
        r.rbp = memory.readQword(r.rsp + 0x38);
        r.rsi = memory.readQword(r.rsp + 0x40);
        r.rsp += 0x20;
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8;
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8;
        return new GovernmentCallee164Api.NormalReturn(
                r.volatileBits(), r.nonvolatileBits(), returnRip, r.rsp);
    }

    private static void invoke(long image, GovernmentPrimaryTail155Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls calls, GovernmentPrimaryTail155Api.Registers r,
            long site, long target) {
        memory.writeQword(r.rsp - 8, image + site + 5);
        r.apply(calls.invoke(new GovernmentPrimaryTail155Api.OpaqueCall(
                site, target, r.rsp, r.volatileBits(), r.nonvolatileBits())));
    }
}
