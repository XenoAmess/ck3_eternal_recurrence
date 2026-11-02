package org.xar.ck3.study.m6.vtable221;

import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Input;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Invocation;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Memory;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Calls;

public final class StaticVirtualForward221 {
    private StaticVirtualForward221() { }

    public static long fromSlot08(Input input, Memory memory, Calls calls) {
        long rcx = input.rcxRaw64();
        long rdx = input.rdxRaw64();
        long r8 = input.r8Raw64();
        long r9 = input.r9Raw64();

        long originalVtable = memory.read64(rcx);
        long functionRaw64 = memory.read64(originalVtable + 0x38);

        Invocation firstCall = new Invocation(
            0x855883,
            functionRaw64,
            originalVtable,
            rcx,
            rdx,
            r8,
            r9
        );
        long returnedObject = calls.call(firstCall);

        long returnedVtable = memory.read64(returnedObject);
        long tailFunctionTarget = memory.read64(returnedVtable + 0x8);

        Invocation tailJump = new Invocation(
            0x8558A0,
            tailFunctionTarget,
            returnedObject,
            returnedObject,
            rdx,
            r8,
            tailFunctionTarget
        );
        return calls.tailJump(tailJump);
    }

    public static long fromSlot10(Input input, Memory memory, Calls calls) {
        long rcx = input.rcxRaw64();
        long rdx = input.rdxRaw64();
        long r8 = input.r8Raw64();
        long r9 = input.r9Raw64();

        long computedRax = rcx + 0x8;
        if (computedRax == rdx) {
            return computedRax;
        }

        long originalVtable = memory.read64(rcx);
        long functionRaw64 = memory.read64(originalVtable + 0x38);

        Invocation firstCall = new Invocation(
            0x85584C,
            functionRaw64,
            originalVtable,
            rcx,
            rdx,
            r8,
            r9
        );
        long returnedObject = calls.call(firstCall);

        long returnedVtable = memory.read64(returnedObject);
        long secondFunctionTarget = memory.read64(returnedVtable + 0x10);

        Invocation secondCall = new Invocation(
            0x85585B,
            secondFunctionTarget,
            returnedObject,
            returnedObject,
            rdx,
            r8,
            returnedVtable
        );
        return calls.call(secondCall);
    }
}