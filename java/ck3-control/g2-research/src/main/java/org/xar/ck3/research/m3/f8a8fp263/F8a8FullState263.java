package org.xar.ck3.research.m3.f8a8fp263;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.f8a8242.F8a8Target424F8A8;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Complete represented205 protocol around the existing storage business, with opaque children. */
public final class F8a8FullState263 {
    private F8a8FullState263() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory, F8a8Fp263Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        GovernmentCrtBoundary185Api.Entry entry = input.base().entry();
        long image = entry.imageBaseBits();
        long originalRsp = entry.rspBits();
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(image, originalRsp,
                entry.volatileBits(), entry.nonvolatileBits()));

        memory.writeQword(originalRsp - 8L, r.rbp);
        r.rsp = originalRsp - 8L;
        r.rbp = r.rsp;
        r.rsp -= 0x50L;

        Invocation invocation = new Invocation(image, memory, calls, r,
            input.base().directionFlagSet(), input.mxcsr());
        try {
            F8a8Target424F8A8.execute(invocation.storage(), invocation.ports(),
                new F8a8Api242.Input(image, entry.volatileBits().rcxBits(),
                    new F8a8Api242.Scratch(originalRsp)));
        } catch (StoppedSignal signal) {
            return signal.outcome;
        }

        r.rsp += 0x50L;
        r.rbp = memory.readQword(r.rsp);
        r.rsp += 8L;
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8L;
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), returnRip,
                r.rsp, r.nonvolatileBits()), invocation.df), invocation.fp);
    }

    private static final class StoppedSignal extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final transient QueueFp604Api.Stopped outcome;

        StoppedSignal(QueueFp604Api.Stopped outcome) {
            super(null, null, false, false);
            this.outcome = outcome;
        }
    }

    private static final class Invocation {
        private final long image;
        private final FullCopy437Api.Memory memory;
        private final F8a8Fp263Api.Calls calls;
        private final GovernmentPrimaryTail155Api.Registers r;
        private boolean df;
        private QueueFp604Api.Mxcsr fp;
        private int pointerReads;

        Invocation(long image, FullCopy437Api.Memory memory, F8a8Fp263Api.Calls calls,
                GovernmentPrimaryTail155Api.Registers r, boolean df, QueueFp604Api.Mxcsr fp) {
            this.image = image;
            this.memory = memory;
            this.calls = calls;
            this.r = r;
            this.df = df;
            this.fp = fp;
        }

        F8a8Api242.Memory storage() {
            return new F8a8Api242.Memory() {
                @Override public long readPointer(long address) {
                    long value = memory.readQword(address);
                    // The pinned business has six MOV RAX,[B-28] reads, then the AND read.
                    // The latter leaves RAX unchanged even when its address aliases the slot.
                    if (++pointerReads <= 6) r.rax = value;
                    return value;
                }
                @Override public int readInt32(long address) { return memory.readDword(address); }
                @Override public void writeInt32(long address, int value) { memory.writeDword(address, value); }
                @Override public void writeInt64(long address, long value) { memory.writeQword(address, value); }
                @Override public void writeInt16(long address, int value) { memory.writeWord(address, value); }
            };
        }

        F8a8Api242.Ports ports() {
            return new F8a8Api242.Ports() {
                @Override public void call424f780(F8a8Api242.Memory m, long site,
                        long rcx, long rdx, long r8, long r9) {
                    call(site, 0x424F780L, rcx, rdx, r8, r9, r.rsp - 8L);
                }
                @Override public void call424f800(F8a8Api242.Memory m, long site,
                        long rcx, long rdx, long r8, long r9) {
                    call(site, 0x424F800L, rcx, rdx, r8, r9, r.rsp - 8L);
                }
                @Override public void call424f780(F8a8Api242.Memory m, long site,
                        long rcx, long rdx, long r8, long r9, long childRsp) {
                    call(site, 0x424F780L, rcx, rdx, r8, r9, childRsp);
                }
                @Override public void call424f800(F8a8Api242.Memory m, long site,
                        long rcx, long rdx, long r8, long r9, long childRsp) {
                    call(site, 0x424F800L, rcx, rdx, r8, r9, childRsp);
                }
            };
        }

        private void call(long site, long target, long rcx, long rdx, long r8,
                long r9, long childRsp) {
            r.rcx = rcx;
            r.rdx = rdx;
            r.r8 = r8;
            r.r9 = r9;
            long preRsp = r.rsp;
            memory.writeQword(preRsp - 8L, image + site + 5L);
            r.rsp = preRsp - 8L;
            GovernmentCrtBoundary185Api.Call original = new GovernmentCrtBoundary185Api.Call(
                site, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target,
                preRsp, r.volatileBits(), r.nonvolatileBits());
            GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                image, childRsp, r.volatileBits(), r.nonvolatileBits());
            F8a8Fp263Api.CallFrame frame = new F8a8Fp263Api.CallFrame(original, child, df, fp);
            QueueFp604Api.Outcome outcome = Objects.requireNonNull(calls.invoke(frame));
            if (outcome instanceof QueueFp604Api.Stopped stopped) {
                throw new StoppedSignal(stopped);
            }
            QueueFp604Api.Normal normal = (QueueFp604Api.Normal) outcome;
            frame.checkNormalReturn(normal);
            r.apply(normal.base().normalReturn().volatileBits());
            r.rsp = normal.base().normalReturn().callerRspBits();
            df = normal.base().postDirectionFlagSet();
            fp = normal.postMxcsr();
        }
    }
}
