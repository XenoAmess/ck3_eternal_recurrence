package org.xar.ck3.research.m3.middle235;

import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStaticDispatch4267630;

public final class MiddleStaticDispatchBinding235 {
    private MiddleStaticDispatchBinding235() { }

    public static DispatchMiddle219Api.Ports bind(long moduleBase,
            DispatchMiddle219Api.Memory capturedMemory,
            MiddleStaticDispatch235Api.TailPort target,
            DispatchMiddle219Api.Ports fallback) {

        long expectedTarget = moduleBase + 0x4267630L;

        return new DispatchMiddle219Api.Ports() {
            @Override
            public void call43dbba8(DispatchMiddle219Api.Memory memory, long siteRva, long actualTarget,
                    long liveRax, int ecx, int edx, int r8d) {
                if (actualTarget != expectedTarget) {
                    fallback.call43dbba8(memory, siteRva, actualTarget, liveRax, ecx, edx, r8d);
                    return;
                }

                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory mismatch");
                }
                if (siteRva != 0x4242147L) {
                    throw new IllegalArgumentException("Site mismatch");
                }

                long knownRcx = Integer.toUnsignedLong(ecx);

                RequestStaticDispatch4267630.TailTarget tailTarget = new RequestStaticDispatch4267630.TailTarget() {
                    @Override
                    public int jumpRax(long targetRax, long knownRcx) {
                        return target.jumpRax(memory, siteRva, targetRax, knownRcx, edx, r8d);
                    }
                };

                RequestStaticDispatch4267630.execute(knownRcx, liveRax, tailTarget);
            }

            @Override
            public void call424de88(DispatchMiddle219Api.Memory memory, long siteRva, long rcx) {
                fallback.call424de88(memory, siteRva, rcx);
            }

            @Override
            public void call424de88(DispatchMiddle219Api.Memory memory, long siteRva, long rcx, long calleeEntryRsp) {
                fallback.call424de88(memory, siteRva, rcx, calleeEntryRsp);
            }

            @Override
            public void call424e1ac(DispatchMiddle219Api.Memory memory, long siteRva, long rcx, long rdx) {
                fallback.call424e1ac(memory, siteRva, rcx, rdx);
            }
        };
    }
}