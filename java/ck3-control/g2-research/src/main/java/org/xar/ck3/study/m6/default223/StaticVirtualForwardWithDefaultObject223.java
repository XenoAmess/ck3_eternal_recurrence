package org.xar.ck3.study.m6.default223;

import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Input;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Invocation;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Memory;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Calls;
import org.xar.ck3.study.m6.provider222.StaticVirtualForwardWithProvider222;

public final class StaticVirtualForwardWithDefaultObject223 {
    private StaticVirtualForwardWithDefaultObject223() { }

    public static long fromSlot08(Input input, long imageBaseRaw64, Memory memory, Calls opaqueCalls) {
        Calls wrapper = new Calls() {
            @Override
            public long call(Invocation actual) {
                return opaqueCalls.call(actual);
            }

            @Override
            public long tailJump(Invocation actual) {
                if (actual.callsiteRva() == 0x8558A0 && actual.functionRaw64() == imageBaseRaw64 + 0x8571D0) {
                    return DefaultObjectWrappers223.fromSlot08(actual, imageBaseRaw64, opaqueCalls);
                }
                return opaqueCalls.tailJump(actual);
            }
        };
        return StaticVirtualForwardWithProvider222.fromSlot08(input, imageBaseRaw64, memory, wrapper);
    }

    public static long fromSlot10(Input input, long imageBaseRaw64, Memory memory, Calls opaqueCalls) {
        Calls wrapper = new Calls() {
            @Override
            public long call(Invocation actual) {
                if (actual.callsiteRva() == 0x85585B && actual.functionRaw64() == imageBaseRaw64 + 0x8571C0) {
                    return DefaultObjectWrappers223.fromSlot10(actual, imageBaseRaw64, opaqueCalls);
                }
                return opaqueCalls.call(actual);
            }

            @Override
            public long tailJump(Invocation actual) {
                return opaqueCalls.tailJump(actual);
            }
        };
        return StaticVirtualForwardWithProvider222.fromSlot10(input, imageBaseRaw64, memory, wrapper);
    }
}