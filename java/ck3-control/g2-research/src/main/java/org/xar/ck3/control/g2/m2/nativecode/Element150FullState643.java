package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner translation of all held150 normal instructions. No lower-body or FP preservation guess. */
public final class Element150FullState643 {
    private Element150FullState643() { }

    public static QueueFp604Api.Outcome execute(Element150Fp643Api.Input input,
            Element150Fp643Api.Memory memory, Element150Fp643Api.Calls calls) {
        Objects.requireNonNull(input); Objects.requireNonNull(memory); Objects.requireNonNull(calls);
        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        long image = entry.imageBaseBits();
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        boolean df = input.directionFlagSet();
        QueueFp604Api.Mxcsr fp = input.mxcsr();

        memory.writeQword(r.rsp + 0x18, r.rbx);       // 37295B0
        memory.writeQword(r.rsp + 0x20, r.rsi);       // 37295B5
        memory.writeQword(r.rsp + 8, r.rcx);          // 37295BA
        r.rsp -= 8; memory.writeQword(r.rsp, r.rdi); // 37295BF
        r.rsp -= 0x20;                              // 37295C0
        r.rbx = r.rdx;                              // 37295C4
        r.rdi = r.rcx;                              // 37295C7
        r.rax = image + 0x45648A0L;                 // 37295CA
        memory.writeQword(r.rcx, r.rax);            // 37295D1
        r.rax = Integer.toUnsignedLong(memory.readDword(r.rdx + 8)); // 37295D4
        memory.writeDword(r.rcx + 8, (int) r.rax);   // 37295D7
        r.rcx += 0x10;                              // 37295DA
        memory.writeQword(r.rsp + 0x38, r.rcx);      // 37295DE
        r.rsi = 0;                                  // 37295E3
        memory.writeQword(r.rcx, r.rsi);            // 37295E5
        memory.writeQword(r.rcx + 8, r.rsi);        // 37295E8
        r.rax = image + 0x54DE260L;                 // 37295EC
        memory.writeQword(r.rcx + 0x10, r.rax);     // 37295F3
        r.rdx += 0x10;                              // 37295F7
        QueueFp604Api.Outcome first = call(image, 0x37295FBL, 0x21A5050L,
                r, df, fp, memory, calls);
        if (first instanceof QueueFp604Api.Stopped stopped) return stopped;
        QueueFp604Api.Normal normal = (QueueFp604Api.Normal) first;
        df = normal.base().postDirectionFlagSet(); fp = normal.postMxcsr();
        // 3729600 NOP has no represented effect.
        r.rcx = r.rdi + 0x28;                        // 3729601
        memory.writeQword(r.rsp + 0x38, r.rcx);      // 3729605
        memory.writeQword(r.rcx, r.rsi);            // 372960A
        memory.writeQword(r.rcx + 8, r.rsi);        // 372960D
        r.rax = image + 0x54DE268L;                 // 3729611
        memory.writeQword(r.rcx + 0x10, r.rax);     // 3729618
        r.rdx = r.rbx + 0x28;                        // 372961C
        QueueFp604Api.Outcome second = call(image, 0x3729620L, 0xB2EEE0L,
                r, df, fp, memory, calls);
        if (second instanceof QueueFp604Api.Stopped stopped) return stopped;
        normal = (QueueFp604Api.Normal) second;
        df = normal.base().postDirectionFlagSet(); fp = normal.postMxcsr();
        // 3729625 NOP has no represented effect.
        r.rax = Integer.toUnsignedLong(memory.readDword(r.rbx + 0x40)); // 3729626
        memory.writeDword(r.rdi + 0x40, (int) r.rax); // 3729629
        r.rax = Integer.toUnsignedLong(memory.readUnsignedByte(r.rbx + 0x44)); // 372962C
        memory.writeByte(r.rdi + 0x44, (int) r.rax); // 3729630
        r.rax = r.rdi;                              // 3729633
        r.rbx = memory.readQword(r.rsp + 0x40);     // 3729636
        r.rsi = memory.readQword(r.rsp + 0x48);     // 372963B
        r.rsp += 0x20;                              // 3729640
        r.rdi = memory.readQword(r.rsp); r.rsp += 8; // 3729644
        long rip = memory.readQword(r.rsp); r.rsp += 8; // 3729645
        GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), rip, r.rsp, r.nonvolatileBits());
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(nr, df), fp);
    }

    private static QueueFp604Api.Outcome call(long image, long site, long target, Registers r,
            boolean df, QueueFp604Api.Mxcsr fp, Element150Fp643Api.Memory memory,
            Element150Fp643Api.Calls calls) {
        long pre = r.rsp;
        long rip = image + site + 5;
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, pre,
                r.volatileBits(), r.nonvolatileBits());
        GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                image, pre - 8, call.volatileBits(), call.nonvolatileBits());
        Element150Fp643Api.CallFrame frame = new Element150Fp643Api.CallFrame(
                call, child, df, fp, 5, rip);
        r.rsp = child.rspBits(); memory.writeQword(r.rsp, rip);
        QueueFp604Api.Outcome offered = Objects.requireNonNull(calls.invoke(frame));
        if (offered instanceof QueueFp604Api.Normal normal) {
            frame.checkNormalReturn(normal);
            r.apply(normal.base().normalReturn().volatileBits());
            r.rsp = normal.base().normalReturn().callerRspBits();
        }
        return offered;
    }
}
