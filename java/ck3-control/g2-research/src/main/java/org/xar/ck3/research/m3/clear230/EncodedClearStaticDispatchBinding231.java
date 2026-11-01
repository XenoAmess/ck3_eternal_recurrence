package org.xar.ck3.research.m3.clear230;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStaticDispatch4267630;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api.Ports;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api.IndirectArguments;
import org.xar.ck3.research.m3.clear230.StaticDispatch231Api.TailPort;

public final class EncodedClearStaticDispatchBinding231 {
    private EncodedClearStaticDispatchBinding231() { }

    public static Ports bind(long moduleBase, NativeTaskMemory capturedMemory, TailPort target, Ports fallback) {
        return new Ports() {
            @Override
            public void call43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, IndirectArguments arguments) {
                long expectedTarget = moduleBase + 0x4267630L;
                if (actualTarget != expectedTarget) {
                    fallback.call43dbba8(memory, siteRva, actualTarget, liveRax, arguments);
                    return;
                }

                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x424DDE5L) {
                    throw new IllegalArgumentException("Site mismatch");
                }

                long knownRcx = Integer.toUnsignedLong(arguments.ecx());

                RequestStaticDispatch4267630.TailTarget tailTarget = new RequestStaticDispatch4267630.TailTarget() {
                    @Override
                    public int jumpRax(long targetRax, long knownRcx) {
                        return target.jumpRax(memory, siteRva, targetRax, knownRcx, arguments);
                    }
                };

                RequestStaticDispatch4267630.execute(knownRcx, liveRax, tailTarget);
            }

            @Override
            public void call424e364(NativeTaskMemory memory, long siteRva, long rcx) {
                fallback.call424e364(memory, siteRva, rcx);
            }
        };
    }
}