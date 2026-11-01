package org.xar.ck3.research.m3.dispatch218;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper218Api;

public final class DispatchIndexedTailBinding218 {
    private DispatchIndexedTailBinding218() { }

    public static DispatchHelper218Api.Ports bind(NativeTaskMemory captured, long moduleBase, DispatchHelper218Api.ResultTails tails, DispatchHelper218Api.Ports fallback) {
        return new DispatchHelper218Api.Ports() {
            @Override
            public void enter(NativeTaskMemory memory, long siteRva, int ecx) {
                if (memory != captured) {
                    throw new IllegalArgumentException("Memory identity mismatch in enter");
                }
                if (siteRva != 0x42420D7L) {
                    throw new IllegalArgumentException("Wrong site in enter");
                }

                RequestIndexedTails4247ffc.Ports oldPorts = new RequestIndexedTails4247ffc.Ports() {
                    @Override
                    public void jump43da500(long knownRcx, long liveRax) {
                        tails.jump43da500(memory, knownRcx, liveRax);
                    }
                    @Override
                    public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                        throw new IllegalStateException("Wrong old jump kind in enter");
                    }
                };

                RequestIndexedTails4247ffc.call4247ffc(moduleBase, ecx, oldPorts);
            }

            @Override
            public void call42420f8(NativeTaskMemory memory, long siteRva, long rcx) {
                fallback.call42420f8(memory, siteRva, rcx);
            }

            @Override
            public long leave(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx) {
                if (memory != captured) {
                    throw new IllegalArgumentException("Memory identity mismatch in leave");
                }
                if (siteRva != 0x42420E8L) {
                    throw new IllegalArgumentException("Wrong site in leave");
                }

                Long[] holder = new Long[1];

                RequestIndexedTails4247ffc.Ports oldPorts = new RequestIndexedTails4247ffc.Ports() {
                    @Override
                    public void jump43da500(long knownRcx, long liveRax) {
                        throw new IllegalStateException("Wrong old jump kind in leave");
                    }
                    @Override
                    public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                        holder[0] = tails.jump43da4f0(memory, knownRcx, liveRax, liveRbx);
                    }
                };

                RequestIndexedTails4247ffc.call4248050(moduleBase, ecx, liveRbx, oldPorts);

                if (holder[0] == null) {
                    throw new IllegalStateException("Missing normal capture in leave");
                }

                return holder[0];
            }
        };
    }
}