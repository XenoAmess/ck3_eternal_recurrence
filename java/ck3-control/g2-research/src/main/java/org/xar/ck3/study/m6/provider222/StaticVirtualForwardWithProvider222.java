package org.xar.ck3.study.m6.provider222;

import org.xar.ck3.study.m6.vtable221.StaticVirtualForward221;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Input;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Invocation;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Memory;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Calls;

public final class StaticVirtualForwardWithProvider222 {
    private StaticVirtualForwardWithProvider222() { }

    public static long fromSlot08(Input input, long imageBaseRaw64, Memory memory, Calls opaqueCalls) {
        Calls wrapper = new Calls() {
            @Override
            public long call(Invocation actual) {
                if ((actual.callsiteRva() == 0x855883 || actual.callsiteRva() == 0x85584C) &&
                    actual.functionRaw64() == imageBaseRaw64 + 0x86E140) {
                    return ObjectProvider86e140.readReturnedObject(actual.rcxRaw64(), memory);
                }
                return opaqueCalls.call(actual);
            }

            @Override
            public long tailJump(Invocation actual) {
                return opaqueCalls.tailJump(actual);
            }
        };
        return StaticVirtualForward221.fromSlot08(input, memory, wrapper);
    }

    public static long fromSlot10(Input input, long imageBaseRaw64, Memory memory, Calls opaqueCalls) {
        Calls wrapper = new Calls() {
            @Override
            public long call(Invocation actual) {
                if ((actual.callsiteRva() == 0x855883 || actual.callsiteRva() == 0x85584C) &&
                    actual.functionRaw64() == imageBaseRaw64 + 0x86E140) {
                    return ObjectProvider86e140.readReturnedObject(actual.rcxRaw64(), memory);
                }
                return opaqueCalls.call(actual);
            }

            @Override
            public long tailJump(Invocation actual) {
                return opaqueCalls.tailJump(actual);
            }
        };
        return StaticVirtualForward221.fromSlot10(input, memory, wrapper);
    }
}