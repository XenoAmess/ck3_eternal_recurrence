package org.xar.ck3.research.m3.clear230;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.AddressFree83Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api;

public final class EncodedClearFreeBinding230 {
    private EncodedClearFreeBinding230() { }

    public static EncodedClear230Api.Ports bind(long moduleBase, Lower61Inputs.Memory capturedMemory, Lower61Inputs.Calls calls, EncodedClear230Api.Ports fallback) {
        return new EncodedClear230Api.Ports() {
            @Override
            public void call43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, EncodedClear230Api.IndirectArguments arguments) {
                fallback.call43dbba8(memory, siteRva, actualTarget, liveRax, arguments);
            }

            @Override
            public void call424e364(NativeTaskMemory memory, long siteRva, long rcx) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x424DE32L) {
                    throw new IllegalArgumentException("Site mismatch");
                }
                AddressFree83Consumer.execute(new Lower61Inputs.CallInput(moduleBase, rcx), capturedMemory, calls);
            }
        };
    }
}