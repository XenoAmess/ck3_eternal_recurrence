package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Normal source execution for the exact held 233-byte function; lower callees are opaque. */
public final class ContextConstructorFullState373ACF0 {
    private ContextConstructorFullState373ACF0() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory, ContextConstructor543Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        GovernmentCrtBoundary185Api.Entry e = input.entry();
        long image = e.imageBaseBits();
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, e.rspBits(), e.volatileBits(), e.nonvolatileBits()));
        boolean df = input.directionFlagSet();

        memory.writeQword(r.rsp + 0x10, r.rbx);
        memory.writeQword(r.rsp + 0x18, r.rbp);
        memory.writeQword(r.rsp + 8, r.rcx);
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.rsi);
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.rdi);
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.r14);
        r.rsp -= 0x20;
        r.rsi = r.rdx;
        r.r14 = r.rcx;
        r.rbp = 0;
        memory.writeDword(r.rcx, (int) r.rbp);
        memory.writeQword(r.rcx + 8, r.rbp);
        memory.writeDword(r.rcx + 0x10, -1);
        r.rcx += 0x18;
        df = call(image, 0x373AD20L, 0x8895D0L, r, df, memory, calls);

        r.rcx = r.r14 + 0x100;
        memory.writeQword(r.rcx, r.rbp);
        memory.writeQword(r.rcx + 8, r.rbp);
        r.rdx = image + 0x54DE270L;
        memory.writeQword(r.rcx + 0x10, r.rdx);
        r.rbx = r.r14 + 0x118;
        r.rax = image + 0x448D1F8L;
        memory.writeQword(r.rbx, r.rax);
        r.rax = image + 0x448D268L;
        memory.writeQword(r.rbx + 8, r.rax);
        memory.writeQword(r.rbx + 0x10, r.rbp);
        memory.writeQword(r.rbx + 0x18, r.rbp);
        r.rax = image + 0x54DE278L;
        memory.writeQword(r.rbx + 0x20, r.rax);
        memory.writeDword(r.rbx + 0x28, (int) r.rbp);
        memory.writeQword(r.rbx + 0x30, r.rbp);
        memory.writeQword(r.rbx + 0x38, r.rbp);
        memory.writeQword(r.rbx + 0x40, r.rdx);
        memory.writeDword(r.rbx + 0x48, -1);
        memory.writeWord(r.rbx + 0x4C, (int) r.rbp);
        memory.writeByte(r.rbx + 0x4E, (int) r.rbp);
        r.x0 = memory.read128(r.rsi);
        memory.write128(r.r14, r.x0);
        r.rax = Integer.toUnsignedLong(memory.readDword(r.rsi + 0x10));
        memory.writeDword(r.r14 + 0x10, (int) r.rax);
        r.rdx = r.rsi + 0x100;
        df = call(image, 0x373ADA1L, 0x37282B0L, r, df, memory, calls);
        r.rdx = r.rsi + 0x18;
        r.rcx = r.r14 + 0x18;
        df = call(image, 0x373ADAEL, 0x260E040L, r, df, memory, calls);
        r.rdx = r.rsi + 0x118;
        r.rcx = r.rbx;
        df = call(image, 0x373ADBDL, 0x3727180L, r, df, memory, calls);

        r.rax = r.r14;
        r.rbx = memory.readQword(r.rsp + 0x48);
        r.rbp = memory.readQword(r.rsp + 0x50);
        r.rsp += 0x20;
        r.r14 = memory.readQword(r.rsp);
        r.rsp += 8;
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8;
        r.rsi = memory.readQword(r.rsp);
        r.rsp += 8;
        long rip = memory.readQword(r.rsp);
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), rip, r.rsp + 8, r.nonvolatileBits()), df);
    }

    private static boolean call(long image, long site, long target, Registers r, boolean df,
            FullCopy437Api.Memory memory, ContextConstructor543Api.Calls calls) {
        long rip = image + site + 5;
        memory.writeQword(r.rsp - 8, rip);
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, r.rsp,
                r.volatileBits(), r.nonvolatileBits());
        GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                image, r.rsp - 8, call.volatileBits(), call.nonvolatileBits());
        ContextConstructor543Api.CallFrame frame = new ContextConstructor543Api.CallFrame(
                call, child, df, 5, rip);
        FullCopy437Api.CallResult result = calls.invoke(frame);
        frame.checkNormalReturn(result);
        // The guard proves the complete represented N equals the current registers.
        r.apply(result.normalReturn().volatileBits());
        return result.postDirectionFlagSet();
    }
}
