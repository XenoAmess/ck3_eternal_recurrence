package org.xar.ck3.research.m3.span228;

import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api;

/** Actual219 binder: only call424e1ac@424217E/4242191 active; other ports exact fallback. */
public final class CallbackSpanBinding228 {
    private CallbackSpanBinding228() { }

    public static DispatchMiddle219Api.Ports bind(long moduleBase, CallbackSpan228Api.Memory capturedMemory, CallbackSpan228Api.Ports childPorts, DispatchMiddle219Api.Ports fallback) {
        return new DispatchMiddle219Api.Ports() {
            @Override
            public void call43dbba8(DispatchMiddle219Api.Memory memory, long siteRva, long actualTarget, long liveRax, int ecx, int edx, int r8d) {
                fallback.call43dbba8(memory, siteRva, actualTarget, liveRax, ecx, edx, r8d);
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
                if (memory != capturedMemory || (siteRva != 0x424217EL && siteRva != 0x4242191L)) {
                    throw new IllegalArgumentException("Wrong memory or site for active call424e1ac");
                }
                CallbackSpan228Api.Input input = new CallbackSpan228Api.Input(moduleBase, rcx, rdx);
                CallbackSpan424E1AC.execute(capturedMemory, childPorts, input);
            }
        };
    }
}