package org.xar.ck3.research.m3.stack227;

import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;
import org.xar.ck3.research.m3.stack227.StackContext227Api;

/**
 * Active leaf binding for 424DE88@4242162.
 * Implements DispatchMiddle219Api.Ports.
 * Old call424de88 delegates to fallback (no E).
 * New call424de88 validates identity/site, then calls StackContext424DE88.execute once.
 * IAT and E1AC ports are passive exact delegates.
 */
public final class StackContextFromMiddleBinding227 {
    private StackContextFromMiddleBinding227() { }

    public static DispatchMiddle219Api.Ports bind(DispatchMiddle219Api.Memory captured, StackContext227Api.Ports child, DispatchMiddle219Api.Ports fallback) {
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
                if (memory != captured || siteRva != 0x4242162L) {
                    throw new IllegalArgumentException("Wrong memory or site for active call424de88");
                }
                StackContext227Api.Context context = new StackContext227Api.Context(calleeEntryRsp, rcx);
                StackContext424DE88.execute(captured, child, context);
            }

            @Override
            public void call424e1ac(DispatchMiddle219Api.Memory memory, long siteRva, long rcx, long rdx) {
                fallback.call424e1ac(memory, siteRva, rcx, rdx);
            }
        };
    }
}