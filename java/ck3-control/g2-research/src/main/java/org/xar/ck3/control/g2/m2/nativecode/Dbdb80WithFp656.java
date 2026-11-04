package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Complete held [DBDB80,DBDBFA) normal execution; both indirect callees stay explicit. */
public final class Dbdb80WithFp656 {
    private Dbdb80WithFp656() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            Dbdb80Fp656Api.Memory memory, Dbdb80Fp656Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        GovernmentCrtBoundary185Api.Entry entry = input.base().entry();
        long image = entry.imageBaseBits();
        State r = new State(entry, input.base().directionFlagSet(), input.mxcsr());

        // DBDB80..DBDB8F: home saves, three actual pushes and local allocation.
        memory.writeQword(r.rsp + 0x10, r.rbp);
        memory.writeQword(r.rsp + 0x18, r.rsi);
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.rdi);
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.r14);
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.r15);
        r.rsp -= 0x20;

        // DWORD destinations zero-extend; the loop condition remains signed.
        r.rdi = Integer.toUnsignedLong(memory.readDword(r.rcx + 0xC));
        r.rbp = Integer.toUnsignedLong((int) r.r9);
        r.r14 = Integer.toUnsignedLong((int) r.r8);
        r.r15 = r.rdx;
        r.rsi = r.rcx;
        if ((int) r.rdi > 0) {
            // DBDBA6..DBDBAB precede the first positive-loop budget check.
            memory.writeQword(r.rsp + 0x40, r.rbx);
            r.rbx = memory.readQword(r.rcx);
            do {
                input.base().budget().beforeStep(0xDBDBB0L, r.rbx);
                r.rax = memory.readQword(r.rbx);
                r.rdx = 0;
                r.rcx = r.rbx;
                long target = memory.readQword(r.rax);
                QueueFp604Api.Outcome offered = call(image, 0xDBDBB8L, 2,
                        target, r, memory, calls);
                if (offered instanceof QueueFp604Api.Stopped) {
                    return offered;
                }
                r.rdi = Integer.toUnsignedLong((int) r.rdi - 1);
                r.rbx += 0x48;
            } while ((int) r.rdi > 0);
            r.rbx = memory.readQword(r.rsp + 0x40);
        }

        // DBDBC9..DBDBD9: all receiver/base/table/target reads are fresh.
        r.rcx = memory.readQword(r.rsi + 0x10);
        r.r8 = 8;
        r.rdx = memory.readQword(r.rsi);
        r.rax = memory.readQword(r.rcx);
        long target = memory.readQword(r.rax + 0x10);
        QueueFp604Api.Outcome offered = call(image, 0xDBDBD9L, 3,
                target, r, memory, calls);
        if (offered instanceof QueueFp604Api.Stopped) {
            return offered;
        }

        // DBDBDC..DBDBEB: preserve the interleaving of stores and fresh restores.
        memory.writeDword(r.rsi + 8, (int) r.rbp);
        r.rbp = memory.readQword(r.rsp + 0x48);
        memory.writeQword(r.rsi, r.r15);
        memory.writeDword(r.rsi + 0xC, (int) r.r14);
        r.rsi = memory.readQword(r.rsp + 0x50);
        r.rsp += 0x20;
        r.r15 = memory.readQword(r.rsp);
        r.rsp += 8;
        r.r14 = memory.readQword(r.rsp);
        r.rsp += 8;
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8;
        long rip = memory.readQword(r.rsp);
        r.rsp += 8;
        GovernmentCrtBoundary185Api.NormalReturn result =
                new GovernmentCrtBoundary185Api.NormalReturn(
                        r.volatileBits(), rip, r.rsp, r.nonvolatileBits());
        return new QueueFp604Api.Normal(
                new FullCopy437Api.CallResult(result, r.df), r.mxcsr);
    }

    /** One genuine CALL push, full frame guard and complete accepted post-state. */
    private static QueueFp604Api.Outcome call(long image, long site, int length,
            long target, State r, Dbdb80Fp656Api.Memory memory,
            Dbdb80Fp656Api.Calls calls) {
        long rip = image + site + length;
        memory.writeQword(r.rsp - 8, rip);
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                site, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                target, r.rsp, r.volatileBits(), r.nonvolatileBits());
        Dbdb80Fp656Api.CallFrame frame = new Dbdb80Fp656Api.CallFrame(call,
                new GovernmentCrtBoundary185Api.Entry(image, r.rsp - 8,
                        call.volatileBits(), call.nonvolatileBits()),
                r.df, r.mxcsr, length, rip);
        QueueFp604Api.Outcome offered =
                Objects.requireNonNull(calls.invoke(frame), "Null outcome");
        if (offered instanceof QueueFp604Api.Normal normal) {
            frame.checkNormalReturn(normal);
            r.apply(normal.base().normalReturn().volatileBits());
            r.df = normal.base().postDirectionFlagSet();
            r.mxcsr = normal.postMxcsr();
        }
        return offered;
    }

    /** Private mechanical holder for every represented register and current DF/FP. */
    private static final class State {
        private long rax, rcx, rdx, r8, r9, r10, r11;
        private long rbx, rbp, rsi, rdi, r12, r13, r14, r15, rsp;
        private Bits128 x0, x1, x2, x3, x4, x5, x6;
        private boolean df;
        private QueueFp604Api.Mxcsr mxcsr;

        private State(GovernmentCrtBoundary185Api.Entry entry, boolean df,
                QueueFp604Api.Mxcsr mxcsr) {
            rsp = entry.rspBits();
            NonvolatileBits n = entry.nonvolatileBits();
            rbx = n.rbxBits();
            rbp = n.rbpBits();
            rsi = n.rsiBits();
            rdi = n.rdiBits();
            r12 = n.r12Bits();
            r13 = n.r13Bits();
            r14 = n.r14Bits();
            r15 = n.r15Bits();
            x6 = n.xmm6();
            apply(entry.volatileBits());
            this.df = df;
            this.mxcsr = mxcsr;
        }

        private VolatileBits volatileBits() {
            return new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11,
                    x0, x1, x2, x3, x4, x5);
        }

        private NonvolatileBits nonvolatileBits() {
            return new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
        }

        private void apply(VolatileBits v) {
            rax = v.raxBits();
            rcx = v.rcxBits();
            rdx = v.rdxBits();
            r8 = v.r8Bits();
            r9 = v.r9Bits();
            r10 = v.r10Bits();
            r11 = v.r11Bits();
            x0 = v.xmm0();
            x1 = v.xmm1();
            x2 = v.xmm2();
            x3 = v.xmm3();
            x4 = v.xmm4();
            x5 = v.xmm5();
        }
    }
}
