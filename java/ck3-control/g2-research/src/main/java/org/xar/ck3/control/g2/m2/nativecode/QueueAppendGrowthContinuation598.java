package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner continuation of actual [8803A2,8803ED), after allocator actual return applied.
 * No prologue, floating-point calculation, epilogue, whole227 or591 binding.
 * Only represented registers, DF and owned Memory effects; general RFLAGS absent. */
public final class QueueAppendGrowthContinuation598 {
    private QueueAppendGrowthContinuation598() { }

    public static boolean resume(long imageBaseBits, Registers r, boolean directionFlagSet,
            QueueAppend597Api.Memory memory, QueueAppend597Api.Calls calls) {
        Objects.requireNonNull(r); Objects.requireNonNull(memory); Objects.requireNonNull(calls);
        if (QueueAppendGrowthStore598.prepare(r, memory)) {
            r.rdx = memory.readQword(r.rbx);
            r.r8 = r.rax << 3;
            r.rcx = r.rdi;
            directionFlagSet = call(imageBaseBits, r, directionFlagSet, memory, calls,
                    0x8803C5L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    0x4226860L, 5, 0x8803CAL);
        }
        r.rcx = memory.readQword(r.rbx + 0x10);
        r.r8 = 8;
        r.rdx = memory.readQword(r.rbx);
        r.rax = memory.readQword(r.rcx);
        long target = memory.readQword(r.rax + 0x10);
        directionFlagSet = call(imageBaseBits, r, directionFlagSet, memory, calls,
                0x8803DAL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                target, 3, 0x8803DDL);
        memory.writeDword(r.rbx + 8, (int)r.rbp);
        r.rbp = memory.readQword(r.rsp + 0x30);
        memory.writeQword(r.rbx, r.rdi);
        memory.writeDword(r.rbx + 0xC, (int)r.rsi);
        return directionFlagSet;
    }

    private static boolean call(long imageBaseBits, Registers r, boolean directionFlagSet,
            QueueAppend597Api.Memory memory, QueueAppend597Api.Calls calls,
            long site, GovernmentCrtBoundary185Api.TargetKind kind, long target,
            int length, long returnRva) {
        long rip = imageBaseBits + returnRva;
        var offered = new GovernmentCrtBoundary185Api.Call(site, kind, target,
                r.rsp, r.volatileBits(), r.nonvolatileBits());
        var child = new GovernmentCrtBoundary185Api.Entry(imageBaseBits,
                r.rsp - 8, offered.volatileBits(), offered.nonvolatileBits());
        var frame = new QueueAppend597Api.CallFrame(offered, child, directionFlagSet, length, rip);
        // Capture target and offered state before the single physical CALL push.
        r.rsp -= 8;
        memory.writeQword(r.rsp, rip);
        FullCopy437Api.CallResult actual = calls.invoke(frame);
        frame.checkNormalReturn(actual);
        r.apply(actual.normalReturn().volatileBits());
        r.rsp = actual.normalReturn().callerRspBits();
        return actual.postDirectionFlagSet();
    }
}
