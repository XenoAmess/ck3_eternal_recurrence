package org.xar.ck3.research.m3.f780fp264;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.f780243.F780Api243;
import org.xar.ck3.research.m3.f780243.F780Target424F780;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Complete represented264 protocol around the existing storage business, with opaque children.
 * Implements the new public API contract for F780FullState264.
 */
public final class F780FullState264 {
    private F780FullState264() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory, F780Fp264Api.Calls calls) {
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

        // Prologue: WQword[E+8]=entryRBX only.
        // The old core owns the first R9-home write (WQword[E+20]=entryR9) via its adapter.
        memory.writeQword(originalRsp + 8L, r.rbx);

        // Prepare the adapter for the old core execution
        Invocation invocation = new Invocation(image, memory, calls, r,
            input.base().directionFlagSet(), input.mxcsr());

        try {
            // Execute the existing old core exactly once
            // Input for F780Target424F780: rdxAddress, r8Address, r9Address, Scratch
            // rdxAddress is the value of RDX at entry
            // r8Address is the value of R8 at entry
            // r9Address is the value of R9 at entry
            // Scratch contains the entryRsp (originalRsp)

            F780Api243.Input coreInput = new F780Api243.Input(
                r.rdx,
                r.r8,
                r.r9,
                new F780Api243.Scratch(originalRsp)
            );

            F780Target424F780.execute(invocation.storage(), invocation.ports(), coreInput);
        } catch (StoppedSignal signal) {
            return signal.outcome;
        }

        // Epilogue: Restore RBX, adjust SP, POP RDI, RET
        // Source:
        // 000000014424F7B4  48 8b 5c 24 30                   mov rbx, qword ptr [rsp + 0x30]
        // 000000014424F7B9  48 83 c4 20                      add rsp, 0x20
        // 000000014424F7BD  5f                               pop rdi
        // 000000014424F7BE  c3                               ret

        // Current RSP is originalRsp - 0x28.
        // [rsp + 0x30] is (originalRsp - 0x28) + 0x30 = originalRsp + 8. This is where we saved RBX.
        r.rbx = memory.readQword(r.rsp + 0x30L);

        // Add 0x20 to RSP
        r.rsp += 0x20L;

        // POP RDI: Read from [RSP], then RSP += 8
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8L;

        // RET: Read return address from [RSP], then RSP += 8
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
        private final F780Fp264Api.Calls calls;
        private final GovernmentPrimaryTail155Api.Registers r;
        private boolean df;
        private QueueFp604Api.Mxcsr fp;
        private int pointerReads;

        Invocation(long image, FullCopy437Api.Memory memory, F780Fp264Api.Calls calls,
                GovernmentPrimaryTail155Api.Registers r, boolean df, QueueFp604Api.Mxcsr fp) {
            this.image = image;
            this.memory = memory;
            this.calls = calls;
            this.r = r;
            this.df = df;
            this.fp = fp;
            this.pointerReads = 0;
        }

        F780Api243.Memory storage() {
            return new F780Api243.Memory() {
                @Override public long readPointer(long address) {
                    long value = memory.readQword(address);
                    // The pinned business has three pointer MOVs: RAX, RCX, RAX.
                    // We map the first three successful pointer reads to RAX/RCX/RAX as per contract.
                    // Actually, the contract says: "readPointer successful ordinal1/2/3 observes RAX/RCX/RAX".
                    // This implies we need to track the ordinal of readPointer calls.
                    if (++pointerReads <= 3) {
                        if (pointerReads == 1) r.rax = value;
                        else if (pointerReads == 2) r.rcx = value;
                        else if (pointerReads == 3) r.rax = value;
                    }
                    return value;
                }
                @Override public int readInt32(long address) {
                    return memory.readDword(address);
                }
                @Override public void writeInt32(long address, int value) {
                    memory.writeDword(address, value);
                }
                @Override public void writeInt64(long address, long value) {
                    // This is the hook for the first write (R9 home).
                    // The contract says: "Invocation-local old F780Api243.Memory.writeInt64 delegates the original old-core home write exactly once, then pushes originalRDI to E-8, sets SP=E-28 and RBX/RDI from originalR9/R8 before returning to first read."
                    // The old core calls writeInt64(entryRsp + 0x20L, r9Address) first.
                    // We intercept this to perform the prologue steps.
                    memory.writeQword(address, value);
                    if (address == r.rsp + 0x20L && value == r.r9) {
                         // Perform the remaining prolog steps
                         memory.writeQword(r.rsp - 8L, r.rdi); // PUSH entryRDI at[E-8]
                         r.rsp = r.rsp - 0x28L; // SP=E-28
                         r.rbx = r.r9; // RBX=entryR9
                         r.rdi = r.r8; // RDI=entryR8
                    }
                }
                @Override public void writeInt16(long address, int value) {
                    memory.writeWord(address, value);
                }
                @Override public void atomicIncrementInt32(long address) {
                    // Contract: Full437.lockedXaddDword(address,1) may supply the one indivisible increment effect
                    memory.lockedXaddDword(address, 1);
                }
            };
        }

        F780Api243.Ports ports() {
            return new F780Api243.Ports() {
                @Override public void call4247ffc(F780Api243.Memory m, long site, int ecx) {
                    // Source: call 0x144247ffc at 424F797
                    // This is an opaque call. We must capture state, push return address, invoke, apply results.
                    // The contract says: "Opaque callbacks access underlying Full437.Memory, not the private old-Memory adapter."
                    // And "Capture live registers/stack at actual CALL, push only that owned CALL RET, apply actual postV/DF/FP."

                    // The site is 0x424F797L. The target is 0x4247FFCL.
                    // Instruction length is 5 (E8 ...).
                    // Return RIP = image + site + 5 = image + 0x424F79CL.

                    r.rcx = Integer.toUnsignedLong(ecx);
                    long preRsp = r.rsp;
                    long retAddr = image + site + 5L;

                    // Push return address
                    memory.writeQword(preRsp - 8L, retAddr);
                    r.rsp = preRsp - 8L;

                    // Create Call frame
                    GovernmentCrtBoundary185Api.Call original = new GovernmentCrtBoundary185Api.Call(
                        site, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4247FFCL,
                        preRsp, r.volatileBits(), r.nonvolatileBits());

                    GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                        image, r.rsp, r.volatileBits(), r.nonvolatileBits());

                    F780Fp264Api.CallFrame frame = new F780Fp264Api.CallFrame(original, child, df, fp);

                    QueueFp604Api.Outcome outcome = Objects.requireNonNull(calls.invoke(frame));

                    if (outcome instanceof QueueFp604Api.Stopped stopped) {
                        throw new StoppedSignal(stopped);
                    }

                    QueueFp604Api.Normal normal = (QueueFp604Api.Normal) outcome;
                    frame.checkNormalReturn(normal);

                    // Apply post-state
                    r.apply(normal.base().normalReturn().volatileBits());
                    r.rsp = normal.base().normalReturn().callerRspBits();
                    df = normal.base().postDirectionFlagSet();
                    fp = normal.postMxcsr();
                }

                @Override public void call4248050(F780Api243.Memory m, long site, int ecx, long liveRbx) {
                    // Source: call 0x144248050 at 424F7AF
                    // Site is 0x424F7AFL. Target is 0x4248050L.
                    // Instruction length is 5.
                    // Return RIP = image + site + 5 = image + 0x424F7B4L.

                    r.rcx = Integer.toUnsignedLong(ecx);
                    long preRsp = r.rsp;
                    long retAddr = image + site + 5L;

                    // Push return address
                    memory.writeQword(preRsp - 8L, retAddr);
                    r.rsp = preRsp - 8L;

                    // Create Call frame
                    GovernmentCrtBoundary185Api.Call original = new GovernmentCrtBoundary185Api.Call(
                        site, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4248050L,
                        preRsp, r.volatileBits(), r.nonvolatileBits());

                    GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                        image, r.rsp, r.volatileBits(), r.nonvolatileBits());

                    F780Fp264Api.CallFrame frame = new F780Fp264Api.CallFrame(original, child, df, fp);

                    QueueFp604Api.Outcome outcome = Objects.requireNonNull(calls.invoke(frame));

                    if (outcome instanceof QueueFp604Api.Stopped stopped) {
                        throw new StoppedSignal(stopped);
                    }

                    QueueFp604Api.Normal normal = (QueueFp604Api.Normal) outcome;
                    frame.checkNormalReturn(normal);

                    // Apply post-state
                    r.apply(normal.base().normalReturn().volatileBits());
                    r.rsp = normal.base().normalReturn().callerRspBits();
                    df = normal.base().postDirectionFlagSet();
                    fp = normal.postMxcsr();
                }
            };
        }
    }
}