package org.xar.ck3.research.m3.allocator241;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.allocator241.Allocator241Api;

public final class AllocatorFromFc74Binding241 {
    private AllocatorFromFc74Binding241() { }

    public static Fc74Api238.Ports bind(long moduleBase, NativeTaskMemory capturedMemory, Allocator241Api.Ports child, Fc74Api238.Ports fallback) {
        if (capturedMemory == null || child == null || fallback == null) {
            throw new RuntimeException();
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
                if (memory != capturedMemory) {
                    throw new RuntimeException();
                }
                if (siteRva != 0x424FCCC) {
                    throw new RuntimeException();
                }
                return AllocatorReuse424E2EC241.execute(memory, child, new Allocator241Api.Input(moduleBase, rcxBits, rdxBits));
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