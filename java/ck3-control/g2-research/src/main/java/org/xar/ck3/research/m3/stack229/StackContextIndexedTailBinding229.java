package org.xar.ck3.research.m3.stack229;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.stack229.StackContext229Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;

/**
 * Mature-tail binder for 424DB74.
 * Implements StackContext229Api.Ports.
 * Validates exact captured Memory identity and site for active ports.
 * Uses RequestIndexedTails4247ffc actual class exactly once per port.
 * Passive middle call424dd60 delegates original fallback exactly once.
 */
public final class StackContextIndexedTailBinding229 {
    private StackContextIndexedTailBinding229() { }

    public static StackContext229Api.Ports bind(NativeTaskMemory captured, long moduleBase, StackContext229Api.Tails tails, StackContext229Api.Ports fallback) {
        return new StackContext229Api.Ports() {
            @Override
            public void call4247ffc(NativeTaskMemory memory, long siteRva, int ecx) {
                if (memory != captured || siteRva != 0x424DB8BL) {
                    throw new IllegalArgumentException("Wrong memory or site for active call4247ffc");
                }
                RequestIndexedTails4247ffc.call4247ffc(moduleBase, ecx, new RequestIndexedTails4247ffc.Ports() {
                    @Override
                    public void jump43da500(long knownRcx, long liveRax) {
                        tails.jump43da500(captured, knownRcx, liveRax);
                    }

                    @Override
                    public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                        throw new IllegalStateException("Unexpected jump43da4f0 in call4247ffc");
                    }
                });
            }

            @Override
            public long call424dd60(NativeTaskMemory memory, long siteRva, long rcx) {
                return fallback.call424dd60(memory, siteRva, rcx);
            }

            @Override
            public void call4248050(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx) {
                if (memory != captured || siteRva != 0x424DB9DL) {
                    throw new IllegalArgumentException("Wrong memory or site for active call4248050");
                }
                RequestIndexedTails4247ffc.call4248050(moduleBase, ecx, liveRbx, new RequestIndexedTails4247ffc.Ports() {
                    @Override
                    public void jump43da500(long knownRcx, long liveRax) {
                        throw new IllegalStateException("Unexpected jump43da500 in call4248050");
                    }

                    @Override
                    public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                        tails.jump43da4f0(captured, knownRcx, liveRax, liveRbx);
                    }
                });
            }
        };
    }
}