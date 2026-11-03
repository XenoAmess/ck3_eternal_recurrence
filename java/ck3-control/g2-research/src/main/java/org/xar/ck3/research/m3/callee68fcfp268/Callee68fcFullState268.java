package org.xar.ck3.research.m3.callee68fcfp268;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.callee246.Callee42568FC246;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

/**
 * Complete represented protocol around the existing storage business, with opaque children.
 * Implements the Callee68fcFullState268.execute contract from PUBLIC-CONTRACT268.txt.
 */
public final class Callee68fcFullState268 {
    private Callee68fcFullState268() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory, Callee68fcFp268Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.base().entry();
        long image = entry.imageBaseBits();
        long originalRsp = entry.rspBits();

        // Initialize registers from the entry
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(image, originalRsp,
                entry.volatileBits(), entry.nonvolatileBits()));

        // Prologue: SUB SP, 0x28
        r.rsp = originalRsp - 0x28L;

        Invocation invocation = new Invocation(image, memory, calls, r,
            input.base().directionFlagSet(), input.mxcsr());

        try {
            // One invocation of existing Callee42568FC246.execute with Input(image, originalRCX)
            Callee42568FC246.execute(invocation.storage(), invocation.ports(),
                new Callee68fcApi246.Input(image, entry.volatileBits().rcxBits()));
        } catch (StoppedSignal signal) {
            return signal.outcome;
        }

        // Epilogue
        // ADD SP, 0x28 then fresh RETread, finalSP=E+8.
        r.rsp += 0x28L;
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8L;

        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), returnRip, r.rsp, r.nonvolatileBits()),
            invocation.df), invocation.fp);
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
        private final Callee68fcFp268Api.Calls calls;
        private final GovernmentPrimaryTail155Api.Registers r;
        private boolean df;
        private QueueFp604Api.Mxcsr fp;

        Invocation(long image, FullCopy437Api.Memory memory, Callee68fcFp268Api.Calls calls,
                GovernmentPrimaryTail155Api.Registers r, boolean df, QueueFp604Api.Mxcsr fp) {
            this.image = image;
            this.memory = memory;
            this.calls = calls;
            this.r = r;
            this.df = df;
            this.fp = fp;
        }

        Callee68fcApi246.Memory storage() {
            return new Callee68fcApi246.Memory() {
                @Override public long readPointer(long address) {
                    return memory.readQword(address);
                }
                @Override public int readInt32(long address) {
                    return memory.readDword(address);
                }
                @Override public void writeInt32(long address, int value) {
                    memory.writeDword(address, value);
                }
                @Override public void writeInt64(long address, long value) {
                    memory.writeQword(address, value);
                }
                @Override public void writeInt16(long address, int value) {
                    memory.writeWord(address, value);
                }
                @Override public void atomicAddInt32(long address, int deltaBits) {
                    // LOCK ADD32 must map to exactly one existing Full437.lockedXaddDword(address,delta) indivisible effect
                    // with old return discarded.
                    memory.lockedXaddDword(address, deltaBits);
                }
            };
        }

        Callee68fcApi246.Ports ports() {
            return new Callee68fcApi246.Ports() {
                @Override public void call42568d4(Callee68fcApi246.Memory m, long siteRva, long knownRcx, long knownRdx,
                        long liveRax, long knownR8, long knownR9) {
                    // At actual port set only those five source-produced GPRs in current full185 registers;
                    // other V/lowXMM and allN remain actual pre-call.
                    r.rcx = knownRcx;
                    r.rdx = knownRdx;
                    r.rax = liveRax;
                    r.r8 = knownR8;
                    r.r9 = knownR9;

                    performCall(siteRva, 0x42568D4L);
                }

                private void performCall(long siteRva, long target) {
                    long preRsp = r.rsp;
                    long retAddr = image + siteRva + 5L; // Direct calls are 5 bytes

                    // Exact owned callpush
                    memory.writeQword(preRsp - 8L, retAddr);
                    r.rsp = preRsp - 8L;

                    // Build child frames from current fullV/N/SP/DF/FP
                    GovernmentCrtBoundary185Api.Call original = new GovernmentCrtBoundary185Api.Call(
                        siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target,
                        preRsp, r.volatileBits(), r.nonvolatileBits());

                    GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                        image, r.rsp, r.volatileBits(), r.nonvolatileBits());

                    Callee68fcFp268Api.CallFrame frame = new Callee68fcFp268Api.CallFrame(original, child, df, fp);

                    QueueFp604Api.Outcome outcome = Objects.requireNonNull(calls.invoke(frame));
                    if (outcome instanceof QueueFp604Api.Stopped stopped) {
                        throw new StoppedSignal(stopped);
                    }

                    QueueFp604Api.Normal normal = (QueueFp604Api.Normal) outcome;

                    // Normal validation before poststate adoption
                    frame.checkNormalReturn(normal);

                    // Checked Normal applies actual postV/DF/FP
                    r.apply(normal.base().normalReturn().volatileBits());
                    r.rsp = normal.base().normalReturn().callerRspBits();
                    df = normal.base().postDirectionFlagSet();
                    fp = normal.postMxcsr();
                }
            };
        }
    }
}