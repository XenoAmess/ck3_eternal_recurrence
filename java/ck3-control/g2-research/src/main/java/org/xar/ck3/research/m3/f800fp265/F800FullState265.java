package org.xar.ck3.research.m3.f800fp265;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.f800244.F800Api244;
import org.xar.ck3.research.m3.f800244.F800Target424F800;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Complete represented265 protocol around the existing storage business, with opaque children.
 */
public final class F800FullState265 {
    private F800FullState265() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory, F800Fp265Api.Calls calls) {
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

        // Prologue Step 1: W64[E+8]=entryRBX
        memory.writeQword(originalRsp + 8L, r.rbx);

        // Prepare Input for old core
        long rdxAddress = entry.volatileBits().rdxBits();
        long r8Address = entry.volatileBits().r8Bits();
        long r9Address = entry.volatileBits().r9Bits();

        F800Api244.Input coreInput = new F800Api244.Input(rdxAddress, r8Address, r9Address,
            new F800Api244.Scratch(originalRsp));

        Invocation invocation = new Invocation(image, memory, calls, r,
            input.base().directionFlagSet(), input.mxcsr());

        try {
            F800Target424F800.execute(invocation.storage(), invocation.ports(), coreInput);
        } catch (StoppedSignal signal) {
            return signal.outcome;
        }

        // Epilogue
        // "After final accepted Normal: fresh RBX read at currentSP+30; SP+=20; fresh POP RDI; fresh RET; finalSP=E+8."
        // currentSP is r.rsp.
        r.rbx = memory.readQword(r.rsp + 0x30L);
        r.rsp += 0x20L;
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8L;
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
        private final F800Fp265Api.Calls calls;
        private final GovernmentPrimaryTail155Api.Registers r;
        private boolean df;
        private QueueFp604Api.Mxcsr fp;
        private int pointerReads;
        private boolean prologueDone;

        Invocation(long image, FullCopy437Api.Memory memory, F800Fp265Api.Calls calls,
                GovernmentPrimaryTail155Api.Registers r, boolean df, QueueFp604Api.Mxcsr fp) {
            this.image = image;
            this.memory = memory;
            this.calls = calls;
            this.r = r;
            this.df = df;
            this.fp = fp;
            this.pointerReads = 0;
            this.prologueDone = false;
        }

        F8a8Api242.Memory storage() {
            return new F8a8Api242.Memory() {
                @Override public long readPointer(long address) {
                    long value = memory.readQword(address);
                    // Five successful pointer reads observe source destinations RAX/RDX/RCX/RDX/RCX
                    if (pointerReads < 5) {
                        if (pointerReads == 0) r.rax = value;
                        else if (pointerReads == 1) r.rdx = value;
                        else if (pointerReads == 2) r.rcx = value;
                        else if (pointerReads == 3) r.rdx = value;
                        else if (pointerReads == 4) r.rcx = value;
                        pointerReads++;
                    }
                    return value;
                }
                @Override public int readInt32(long address) { return memory.readDword(address); }
                @Override public void writeInt32(long address, int value) { memory.writeDword(address, value); }
                @Override public void writeInt64(long address, long value) {
                    memory.writeQword(address, value);
                    // Hook: successful first write completes pushRDI/sub20/currentRBX=entryR9/currentRDI=entryR8
                    if (!prologueDone && address == r.rsp + 0x20L) {
                        // PUSH RDI at E-8
                        memory.writeQword(r.rsp - 8L, r.rdi);
                        // PUSH consumes8 and SUB consumes0x20: final SP=E-0x28.
                        r.rsp -= 0x28L;
                        // RBX = R9
                        r.rbx = r.r9;
                        // RDI = R8
                        r.rdi = r.r8;
                        prologueDone = true;
                    }
                }
                @Override public void writeInt16(long address, int value) { memory.writeWord(address, value); }
            };
        }

        F800Api244.Ports ports() {
            return new F800Api244.Ports() {
                @Override public void call4247ffc(F8a8Api242.Memory m, long siteRva, int ecxBits) {
                    // First Ports method sets only RCX=z32(ecxBits), retaining all other actual volatile values
                    r.rcx = Integer.toUnsignedLong(ecxBits);
                    performCall(siteRva, 0x4247FFCL);
                }
                @Override public void call424fa90(F8a8Api242.Memory m, long siteRva, long knownRcx, long knownRdx, long liveRax) {
                    // Middle FA90 sets only supplied RCX/RDX/liveRAX
                    r.rcx = knownRcx;
                    r.rdx = knownRdx;
                    r.rax = liveRax;
                    performCall(siteRva, 0x424FA90L);
                }
                @Override public void call4248050(F8a8Api242.Memory m, long siteRva, int ecxBits, long liveRbx) {
                    // Last Ports method sets only RCX=z32(ecxBits), retaining all other actual volatile values
                    r.rcx = Integer.toUnsignedLong(ecxBits);
                    performCall(siteRva, 0x4248050L);
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

                    F800Fp265Api.CallFrame frame = new F800Fp265Api.CallFrame(original, child, df, fp);

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