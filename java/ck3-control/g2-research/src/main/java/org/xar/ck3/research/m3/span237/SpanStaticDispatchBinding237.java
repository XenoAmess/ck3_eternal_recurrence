package org.xar.ck3.research.m3.span237;

import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStaticDispatch4267630;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api;

/**
 * Binding for the static dispatch tail target in the span237 context.
 * Implements the contract specified in CONTRACT-FINAL237.txt.
 */
public final class SpanStaticDispatchBinding237 {
    private SpanStaticDispatchBinding237() { }

    public static CallbackSpan228Api.Ports bind(long moduleBase, CallbackSpan228Api.Memory capturedMemory, SpanStaticDispatch237Api.TailPort target, CallbackSpan228Api.Ports fallback) {
        return new CallbackSpan228Api.Ports() {
            @Override
            public void call43dbba8(CallbackSpan228Api.Memory memory, long siteRva, long actualTarget, long liveRax, CallbackSpan228Api.Arguments arguments) {
                // 1. Passive context bypass: If actualTarget != Java wrap64(moduleBase+4267630) OR Arguments is not an EntryArguments record,
                //    immediately originalfallback.call43dbba8 once with every original argument/object unchanged.
                long expectedTarget = moduleBase + 0x4267630L;
                if (actualTarget != expectedTarget || !(arguments instanceof CallbackSpan228Api.EntryArguments)) {
                    fallback.call43dbba8(memory, siteRva, actualTarget, liveRax, arguments);
                    return;
                }

                // 2. Active context admission: memory must be capturedMemory by object identity and site must be 424E1E9.
                if (memory != capturedMemory || siteRva != 0x424E1E9L) {
                    throw new IllegalArgumentException("Wrong memory or site for active call43dbba8");
                }

                // 3. Invoke old mature execute exactly once with entryArguments.rcx() and original full liveRAX.
                //    The TailTarget invokes the supplied real inner TailPort exactly once with original memory/site,
                //    mature callback full targetRAX/knownRCX and the identical received EntryArguments object.
                CallbackSpan228Api.EntryArguments entryArguments = (CallbackSpan228Api.EntryArguments) arguments;
                long knownRcx = entryArguments.rcx();

                RequestStaticDispatch4267630.TailTarget tailTarget = new RequestStaticDispatch4267630.TailTarget() {
                    @Override
                    public int jumpRax(long targetRax, long knownRcx) {
                        // Supplier supplies a true int normal result to the old mature int return.
                        // The record carries knownRDX plus its original RCX; do not reconstruct/copy it.
                        return target.jumpRax(memory, siteRva, targetRax, knownRcx, entryArguments);
                    }
                };

                // Invoke old mature execute once. Exceptions propagate immediately unchanged.
                RequestStaticDispatch4267630.execute(knownRcx, liveRax, tailTarget);
            }
        };
    }
}