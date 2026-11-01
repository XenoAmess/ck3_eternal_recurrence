package org.xar.ck3.research.m3.fc74free251;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.AddressFree83Consumer;

public final class Fc74FreeBinding251 {
    private Fc74FreeBinding251() { }

    public static Fc74Api238.Ports bind(
            long moduleBase,
            Lower61Inputs.Memory capturedMemory,
            Lower61Inputs.Calls calls,
            Fc74Api238.Ports fallback) {
        if (capturedMemory == null) {
            throw new NullPointerException("capturedMemory");
        }
        if (calls == null) {
            throw new NullPointerException("calls");
        }
        if (fallback == null) {
            throw new NullPointerException("fallback");
        }

        return new Fc74Api238.Ports() {
            @Override
            public int callIat43da738(NativeTaskMemory memory, long siteRva, long actualTarget, int entryEcxBits) {
                return fallback.callIat43da738(memory, siteRva, actualTarget, entryEcxBits);
            }

            @Override
            public long call424e900(NativeTaskMemory memory, long siteRva, int ecxBits) {
                return fallback.call424e900(memory, siteRva, ecxBits);
            }

            @Override
            public int call424e948(NativeTaskMemory memory, long siteRva, int ecxBits, long rdxBits) {
                return fallback.call424e948(memory, siteRva, ecxBits, rdxBits);
            }

            @Override
            public long call424e2ec(NativeTaskMemory memory, long siteRva, long rcxBits, long rdxBits) {
                return fallback.call424e2ec(memory, siteRva, rcxBits, rdxBits);
            }

            @Override
            public void call424e364(NativeTaskMemory memory, long siteRva, long rcxBits) {
                if (memory == capturedMemory && (siteRva == 0x424FCE8L || siteRva == 0x424FD17L)) {
                    AddressFree83Consumer.execute(
                        new Lower61Inputs.CallInput(moduleBase, rcxBits),
                        capturedMemory,
                        calls
                    );
                } else {
                    fallback.call424e364(memory, siteRva, rcxBits);
                }
            }

            @Override
            public void call424f8a8(NativeTaskMemory memory, long siteRva, long rcxBits) {
                fallback.call424f8a8(memory, siteRva, rcxBits);
            }

            @Override
            public void call424f8a8(NativeTaskMemory memory, long siteRva, long rcxBits, long calleeEntryRsp) {
                fallback.call424f8a8(memory, siteRva, rcxBits, calleeEntryRsp);
            }

            @Override
            public void callIat43da420(NativeTaskMemory memory, long siteRva, long actualTarget, int ecxBits) {
                fallback.callIat43da420(memory, siteRva, actualTarget, ecxBits);
            }
        };
    }
}