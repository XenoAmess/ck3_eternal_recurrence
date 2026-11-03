package org.xar.ck3.study.m6.forward237;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/**
 * Real new237 scope: full represented normal frames for exact 855870 (51B) and 855830 (58B).
 * Follows COMPLETE supplied ASM literally, not old221 scalar port replay.
 * Uses actual existing 185/164 declarations.
 */
public final class StaticVirtualFullState237 {
    private StaticVirtualFullState237() { }

    /**
     * Actual 855870 (51B) body.
     * Prologue: save RBX, push RDI, SUB RSP 0x20.
     * Allocate: RAX=[RCX], RBX=R8, RDI=RDX, CALL [RAX+0x38].
     * Epilogue: restore RBX, ADD RSP 0x20, POP RDI.
     * Tail: JMP R9 (INDIRECT_ABSOLUTE).
     */
    public static NormalReturn fromSlot08(Entry entry, Memory memory, Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        long image = entry.imageBaseBits();
        long s = entry.rspBits();
        VolatileBits currentV = entry.volatileBits();
        NonvolatileBits currentN = entry.nonvolatileBits();

        // Prologue: MOV [RSP+0x8], RBX; PUSH RDI; SUB RSP, 0x20
        // entrySP is s. After PUSH RDI, SP is s-8. After SUB 0x20, SP is s-0x28.
        long pre = s - 0x28L;

        // Mechanical initialization using 164 registers helper
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, pre, currentV, currentN));

        // Save original RBX at [entrySP+0x8] (which is [pre+0x30])
        // The 164 helper initializes r.rbx from nonvolatileBits, but the ASM says "mov QWORD PTR [rsp+0x8], rbx" at the very start.
        // However, the contract says "Both bodies first write originalRBX at [entrySP+0x8]".
        // In the 164 Entry, frameRspBits is the SP *after* the CALL pushed the return address (i.e., the callee's entry SP).
        // The ASM 855870 starts with `mov QWORD PTR [rsp+0x8], rbx`. This is the prologue saving RBX.
        // The 164 helper `registers(Entry e)` sets `rbx` from `e.nonvolatileBits().rbxBits()`. It does NOT perform the memory write.
        // We must perform the memory write explicitly as per the contract: "write originalRBX at [entrySP+0x8]".
        // entrySP is `s`. So write to `s + 0x8`.
        memory.writeQword(s + 0x8L, r.rbx);

        // Push original RDI at [entrySP-0x8] (which is [s-0x8])
        // The ASM says `push rdi`. This decrements SP by 8 and writes RDI.
        // The 164 helper sets `rdi` from `e.governmentBits()` (which is `n.rdiBits()`).
        // We must perform the memory write explicitly.
        memory.writeQword(s - 0x8L, r.rdi);

        // Allocate: RAX=[RCX], RBX=entryR8, RDI=entryRDX
        // The 164 helper already set r.rax, r.rbx, r.rdi from the Entry's volatile/nonvolatile bits.
        // But the ASM says:
        // 85587a: mov rax, QWORD PTR [rcx]
        // 85587d: mov rbx, r8
        // 855880: mov rdi, rdx
        // The 164 helper initializes registers from the Entry. The Entry's VolatileBits contains the incoming RAX, RCX, etc.
        // The Entry's NonvolatileBits contains the incoming RBX, RDI, etc.
        // The contract says "Allocate51: RAX=[RCX], RBX=entryR8, RDI=entryRDX".
        // This implies we must update the registers based on the memory read and the incoming values.
        // r.rcx is the incoming RCX.
        r.rax = memory.readQword(r.rcx);
        r.rbx = r.r8; // entryR8 is in VolatileBits
        r.rdi = r.rdx; // entryRDX is in VolatileBits

        // First indirect CALL 0x855883 to [RAX+0x38]
        // Target is [RAX+0x38]. This is an INDIRECT_ABSOLUTE call? No, the contract says "first indirectCALL0x855883 to [RAX+0x38]".
        // The ASM `ff 50 38` is `call QWORD PTR [rax+0x38]`. This is an indirect call.
        // The target bits are the value at [RAX+0x38].
        long targetBits = memory.readQword(r.rax + 0x38L);

        // Child RET is image + 0x855886
        long childRet = image + 0x855886L;

        // Write child RET to memory at pre-0x8
        // The contract says "producer writes childRET once at preSP-0x8".
        // preSP is `pre`. So write to `pre - 0x8`.
        memory.writeQword(pre - 0x8L, childRet);

        // Invoke the owned call
        // Call.rspBits is PRE-owned-pushSP. The CALL instruction pushes the return address.
        // The current SP is `pre`. The CALL will push to `pre-8` and set SP to `pre-8`.
        // The `Call` record expects `rspBits` to be the SP *before* the push.
        Call call = new Call(0x855883L, TargetKind.INDIRECT_ABSOLUTE, targetBits, pre, r.volatileBits(), r.nonvolatileBits());
        VolatileBits returnedV = calls.invoke(call);

        // Apply all returnedV
        r.apply(returnedV);

        // Post-call register updates from ASM:
        // 855886: mov r8, rbx
        // 855889: mov rdx, rdi
        // 85588c: mov rcx, QWORD PTR [rax]
        // 85588f: mov r9, QWORD PTR [rcx+0x8]
        // 855893: mov rcx, rax
        r.r8 = r.rbx;
        r.rdx = r.rdi;
        r.rcx = memory.readQword(r.rax);
        r.r9 = memory.readQword(r.rcx + 0x8L);
        r.rcx = r.rax;

        // Epilogue:
        // 855896: mov rbx, QWORD PTR [rsp+0x30]
        // 85589b: add rsp, 0x20
        // 85589f: pop rdi
        // Current SP is `pre` (since we haven't changed it in the code, but the CALL pushed/popped? No, the CALL is opaque, it returns with SP restored to `pre`?
        // The contract says "port owns calleeRET and returns all represented V... Source then ADD RSP0x28 and RET".
        // Wait, the ASM for 855870 has `add rsp, 0x20` and `pop rdi`.
        // The `pre` was `s - 0x28`.
        // `add rsp, 0x20` makes SP `s - 0x8`.
        // `pop rdi` makes SP `s`.
        // The `mov rbx, [rsp+0x30]` happens at SP=`pre`. `pre+0x30` is `s-0x28+0x30` = `s+0x8`. This matches the saved RBX location.
        r.rbx = memory.readQword(pre + 0x30L);
        r.rdi = memory.readQword(s - 0x8L);

        // Restore SP
        r.rsp = s;

        // Tail at 0x8558A0 to actual R9 is INDIRECT_ABSOLUTE
        // The ASM `rex.WB jmp r9` is a tail jump.
        // The target is the value in R9.
        // The entry for the tail is the current state (image, s, V, N).
        Tail tail = new Tail(0x8558A0L, TargetKind.INDIRECT_ABSOLUTE, r.r9, new Entry(image, s, r.volatileBits(), r.nonvolatileBits()));

        // Return exact port NR unchanged
        return calls.tail(tail);
    }

    /**
     * Actual 855830 (58B) body.
     * Prologue: save RBX, push RDI, SUB RSP 0x20.
     * Free58: RAX=RCX+0x8, RDI=R8, RBX=RDX.
     * If RDX==RAX, jump epilogue.
     * Else: RAX=[RCX], CALL [RAX+0x38].
     * Post-call: R8=RDI, RDX=RBX, RCX=RAX, R9=[RAX].
     * Second CALL [R9+0x10].
     * Epilogue: restore RBX, ADD RSP 0x20, POP RDI, RET.
     */
    public static NormalReturn fromSlot10(Entry entry, Memory memory, Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);

        long image = entry.imageBaseBits();
        long s = entry.rspBits();
        VolatileBits currentV = entry.volatileBits();
        NonvolatileBits currentN = entry.nonvolatileBits();

        // Prologue: MOV [RSP+0x8], RBX; PUSH RDI; SUB RSP, 0x20
        long pre = s - 0x28L;

        // Mechanical initialization using 164 registers helper
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, pre, currentV, currentN));

        // Save original RBX at [entrySP+0x8]
        memory.writeQword(s + 0x8L, r.rbx);

        // Push original RDI at [entrySP-0x8]
        memory.writeQword(s - 0x8L, r.rdi);

        // Free58: RAX=entryRCX+0x8 (wrap64), RDI=entryR8, RBX=entryRDX
        r.rax = r.rcx + 0x8L;
        r.rdi = r.r8;
        r.rbx = r.rdx;

        // If RDX==RAX jump epilogue with no object read/callback
        // The ASM says `cmp rdx, rax; je 0x85585f`.
        // 0x85585f is the epilogue start.
        if (r.rdx == r.rax) {
            // Jump to epilogue
            // Epilogue:
            // 85585f: mov rbx, QWORD PTR [rsp+0x30]
            // 855864: add rsp, 0x20
            // 855868: pop rdi
            // 855869: ret
            r.rbx = memory.readQword(pre + 0x30L);
        r.rdi = memory.readQword(s - 0x8L);
            r.rsp = s;

            // RET: fresh readQword at original s
            long rip = memory.readQword(s);
            long callerSP = s + 0x8L;

            return new NormalReturn(r.volatileBits(), rip, callerSP, r.nonvolatileBits());
        }

        // Otherwise RAX=[RCX], first indirectCALL0x85584C->[RAX+0x38]
        r.rax = memory.readQword(r.rcx);

        long targetBits = memory.readQword(r.rax + 0x38L);
        long childRet = image + 0x85584FL;

        // Write child RET to memory at pre-0x8
        memory.writeQword(pre - 0x8L, childRet);

        // Invoke the owned call
        Call call = new Call(0x85584CL, TargetKind.INDIRECT_ABSOLUTE, targetBits, pre, r.volatileBits(), r.nonvolatileBits());
        VolatileBits returnedV = calls.invoke(call);

        // Apply all returnedV
        r.apply(returnedV);

        // Post-call register updates from ASM:
        // 85584f: mov r8, rdi
        // 855852: mov rdx, rbx
        // 855855: mov rcx, rax
        // 855858: mov r9, QWORD PTR [rax]
        r.r8 = r.rdi;
        r.rdx = r.rbx;
        r.rcx = r.rax;
        r.r9 = memory.readQword(r.rax);

        // Second indirectCALL0x85585B->[R9+0x10] is FOUR bytes
        // The ASM `41 ff 51 10` is `call QWORD PTR [r9+0x10]`.
        long targetBits2 = memory.readQword(r.r9 + 0x10L);
        long childRet2 = image + 0x85585FL;

        // Write child RET to memory at pre-0x8
        // The SP is still `pre` (the first CALL returned with SP restored to `pre`).
        memory.writeQword(pre - 0x8L, childRet2);

        // Invoke the owned call
        Call call2 = new Call(0x85585BL, TargetKind.INDIRECT_ABSOLUTE, targetBits2, pre, r.volatileBits(), r.nonvolatileBits());
        VolatileBits returnedV2 = calls.invoke(call2);

        // Apply entire second returnedV
        r.apply(returnedV2);

        // Epilogue:
        // 85585f: mov rbx, QWORD PTR [rsp+0x30]
        // 855864: add rsp, 0x20
        // 855868: pop rdi
        // 855869: ret
        r.rbx = memory.readQword(pre + 0x30L);
        r.rdi = memory.readQword(s - 0x8L);
        r.rsp = s;

        // RET: fresh readQword at original s
        long rip = memory.readQword(s);
        long callerSP = s + 0x8L;

        return new NormalReturn(r.volatileBits(), rip, callerSP, r.nonvolatileBits());
    }
}