package org.xar.ck3.research.m3.f8a8242;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;

/**
 * Binding for the actual 238 consumer to the new F8A8 producer.
 * Captures moduleBase, identical Memory, child Ports, and fallback Ports.
 * Owned call424f8a8 checks identity and site before invoking the producer.
 * All other 238 Ports methods delegate exactly to fallback.
 */
public final class F8a8FromFc74Binding242 {
    private F8a8FromFc74Binding242() { }

    public static Fc74Api238.Ports bind(long moduleBase, F8a8Api242.Memory capturedMemory, F8a8Api242.Ports child, Fc74Api238.Ports fallback) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (child == null) {
            throw new RuntimeException("child");
        }
        if (fallback == null) {
            throw new RuntimeException("fallback");
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
                fallback.call424e364(memory, siteRva, rcxBits);
            }

            @Override
            public void call424f8a8(NativeTaskMemory memory, long siteRva, long rcxBits) {
                fallback.call424f8a8(memory, siteRva, rcxBits);
            }

            @Override
            public void callIat43da420(NativeTaskMemory memory, long siteRva, long actualTarget, int ecxBits) {
                fallback.callIat43da420(memory, siteRva, actualTarget, ecxBits);
            }

            @Override
            public void call424f8a8(NativeTaskMemory memory, long siteRva, long rcxBits, long calleeEntryRsp) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424FD10L) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                F8a8Api242.Input input = new F8a8Api242.Input(
                        moduleBase,
                        rcxBits,
                        new F8a8Api242.Scratch(calleeEntryRsp));
                F8a8Target424F8A8.execute(capturedMemory, child, input);
            }
        };
    }
}