package org.xar.ck3.research.m3.fa90fp267;

import java.util.Objects;
import java.util.OptionalLong;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.fa90245.Fa90Target424FA90;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

/**
 * Complete represented protocol around the existing storage business, with opaque children.
 * Implements the Fa90FullState267.execute contract from PUBLIC-CONTRACT267.txt.
 */
public final class Fa90FullState267 {
    private Fa90FullState267() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory, Fa90Fp267Api.Calls calls) {
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

        // Prologue: W64[E+8]=entryRBX
        memory.writeQword(originalRsp + 8L, r.rbx);
        memory.writeQword(originalRsp - 8L, r.rdi);
        r.rsp = originalRsp - 0x28L;
        r.rdi = entry.volatileBits().rcxBits();
        r.rbx = entry.volatileBits().rdxBits();

        // Prepare Input for old core
        long entryRcx = entry.volatileBits().rcxBits();
        long entryRdx = entry.volatileBits().rdxBits();
        long entryRax = entry.volatileBits().raxBits();

        Fa90Api245.Input coreInput = new Fa90Api245.Input(image, entryRcx, entryRdx, entryRax);

        Invocation invocation = new Invocation(image, memory, calls, r,
            input.base().directionFlagSet(), input.mxcsr());

        try {
            Fa90Target424FA90.execute(invocation.storage(), invocation.ports(), coreInput);
        } catch (StoppedSignal signal) {
            return signal.outcome;
        }

        // Epilogue
        // "Final successful path fresh RBX=[currentSP+30], SP+=20, fresh POP RDI, fresh RET; finalSP=E+8."
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
        private final Fa90Fp267Api.Calls calls;
        private final GovernmentPrimaryTail155Api.Registers r;
        private boolean df;
        private QueueFp604Api.Mxcsr fp;
        private int pointerReads;

        Invocation(long image, FullCopy437Api.Memory memory, Fa90Fp267Api.Calls calls,
                GovernmentPrimaryTail155Api.Registers r, boolean df, QueueFp604Api.Mxcsr fp) {
            this.image = image;
            this.memory = memory;
            this.calls = calls;
            this.r = r;
            this.df = df;
            this.fp = fp;
            this.pointerReads = 0;
        }

        F8a8Api242.Memory storage() {
            return new F8a8Api242.Memory() {
                @Override public long readPointer(long address) {
                    long value = memory.readQword(address);
                    // Only the first two reads (entryRCX+0x90) update RCX.
                    // The third read (global) is CMP memory and does not assign a GPR.
                    if (pointerReads < 2) {
                        r.rcx = value;
                    } else if (pointerReads == 2 && r.rcx != value) {
                        r.rax = image + 0x542F330L;
                    }
                    pointerReads++;
                    return value;
                }
                @Override public int readInt32(long address) { return memory.readDword(address); }
                @Override public void writeInt32(long address, int value) { memory.writeDword(address, value); }
                @Override public void writeInt64(long address, long value) {
                    memory.writeQword(address, value);
                }
                @Override public void writeInt16(long address, int value) { memory.writeWord(address, value); }
            };
        }

        Fa90Api245.Ports ports() {
            return new Fa90Api245.Ports() {
                @Override public void call42568fc(F8a8Api242.Memory m, long siteRva, long knownRcx, long knownRdx, long liveRax) {
                    // First call has all three source-known register values.
                    // "First sets RCX=firstCurrent, preserves actual entry RDX/RAX."
                    // The old business passes `firstCurrent` as `knownRcx`.
                    r.rcx = knownRcx;
                    // RDX and RAX are preserved from entry (or previous state).
                    // The contract says "preserves actual entry RDX/RAX". Since this is the first call, they are entry values.
                    // But we must ensure they are set in the register state for the call frame.
                    // The registers `r` already have `rdx` and `rax` from the entry initialization.
                    // We just need to set `rcx`.
                    performCall(siteRva, 0x42568FCL);
                }
                @Override public void call42566fc(F8a8Api242.Memory m, long siteRva, long knownRcx, long liveRax) {
                    // RDX is unknown after the first opaque call; RAX is the reached LEA address.
                    // "Second sets source-known RCX and LEA RAX, keeps actual postfirst RDX/other V."
                    r.rcx = knownRcx;
                    r.rax = liveRax;
                    // RDX is kept as is (postfirst).
                    performCall(siteRva, 0x42566FCL);
                }
                @Override public void call4256670(F8a8Api242.Memory m, long siteRva, long knownRcx,
                        OptionalLong knownRdx, OptionalLong knownRax) {
                    // Empty denotes unknown, never zero; both OptionalLong arguments are nonnull.
                    // "Third sets RCX=entryRDX, applies known Optional values only when present; empty never means zero."
                    r.rcx = knownRcx;
                    if (knownRdx.isPresent()) {
                        r.rdx = knownRdx.getAsLong();
                    }
                    if (knownRax.isPresent()) {
                        r.rax = knownRax.getAsLong();
                    }
                    performCall(siteRva, 0x4256670L);
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

                    Fa90Fp267Api.CallFrame frame = new Fa90Fp267Api.CallFrame(original, child, df, fp);

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
