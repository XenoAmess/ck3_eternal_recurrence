package org.xar.ck3.research.m3.out234;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStaticDispatch4267630;
import org.xar.ck3.research.m3.out224.OutHelper224Api;
import org.xar.ck3.research.m3.out234.OutStaticDispatch234Api;

public final class OutStaticDispatchBinding234 {
    private OutStaticDispatchBinding234() { }

    public static OutHelper224Api.Ports bind(long moduleBase, NativeTaskMemory capturedMemory, OutStaticDispatch234Api.TailPort target, OutHelper224Api.Ports fallback) {
        final long expectedTarget = moduleBase + 0x4267630L;

        return new OutHelper224Api.Ports() {
            @Override
            public long call424e448(NativeTaskMemory memory, long siteRva, int ecx, long rdx, long r8, long r9) {
                return fallback.call424e448(memory, siteRva, ecx, rdx, r8, r9);
            }

            @Override
            public long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, long rcx, long rdx) {
                if (actualTarget != expectedTarget) {
                    return fallback.tail43dbba8(memory, siteRva, actualTarget, liveRax, rcx, rdx);
                }

                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x424E65CL) {
                    throw new IllegalArgumentException("Site RVA mismatch");
                }

                final long[] resultHolder = new long[1];
                final boolean[] executed = new boolean[1];

                RequestStaticDispatch4267630.TailTarget intAdapter = new RequestStaticDispatch4267630.TailTarget() {
                    @Override
                    public int jumpRax(long targetRax, long knownRcx) {
                        if (executed[0]) {
                            throw new IllegalStateException("TailPort already executed");
                        }
                        executed[0] = true;
                        long realResult = target.jumpRax(memory, siteRva, targetRax, knownRcx, rdx);
                        resultHolder[0] = realResult;
                        return (int) realResult;
                    }
                };

                RequestStaticDispatch4267630.execute(rcx, liveRax, intAdapter);

                if (!executed[0]) {
                    throw new IllegalStateException("TailPort not executed");
                }

                return resultHolder[0];
            }
        };
    }
}