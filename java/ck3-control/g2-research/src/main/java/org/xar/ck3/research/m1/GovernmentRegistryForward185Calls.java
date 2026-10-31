package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

public final class GovernmentRegistryForward185Calls {
    public static GovernmentPrimaryTail155Api.Calls bind(
            long imageBase,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls delegate) {

        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return delegate.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == 0x4223EFBL && call.targetRva() == 0x424DE78L) {
                    // Frame is already pushed by caller, so rspBits-8 is the child frame RSP
                    long childRsp = call.rspBits() - 8;

                    GovernmentCallee164Api.Entry child = new GovernmentCallee164Api.Entry(
                        imageBase,
                        childRsp,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );

                    GovernmentCallee164Api.NormalReturn result = GovernmentRegistryForward185.execute(child, memory, delegate);

                    if (result.returnRipBits() != imageBase + 0x4223F00L) {
                        throw new IllegalStateException("Invalid return RIP");
                    }
                    if (result.callerRspBits() != call.rspBits()) {
                        throw new IllegalStateException("Invalid caller RSP");
                    }
                    if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new IllegalStateException("Invalid nonvolatile bits");
                    }

                    return result.volatileBits();
                }

                return delegate.invoke(call);
            }
        };
    }
}
