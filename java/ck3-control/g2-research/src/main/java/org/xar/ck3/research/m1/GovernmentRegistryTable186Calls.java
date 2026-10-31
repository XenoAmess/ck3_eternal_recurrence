package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

public final class GovernmentRegistryTable186Calls {
    private GovernmentRegistryTable186Calls() { }

    public static GovernmentPrimaryTail155Api.Calls bind(long imageBase, GovernmentSharedManager167Api.Memory memory, GovernmentPrimaryTail155Api.Calls delegate) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return delegate.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == 0x4223F0CL && call.targetRva() == 0x424DEECL) {
                    long childRsp = call.rspBits() - 8;
                    long expectedReturn = imageBase + 0x4223F11L;

                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                        imageBase,
                        childRsp,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );

                    GovernmentCallee164Api.NormalReturn result = GovernmentRegistryTable186.execute(entry, memory, delegate);

                    if (result.returnRipBits() != expectedReturn) {
                        throw new UnsupportedOperationException("Return RIP mismatch");
                    }
                    if (result.callerRspBits() != call.rspBits()) {
                        throw new UnsupportedOperationException("Caller RSP mismatch");
                    }
                    if (!call.nonvolatileBits().equals(result.nonvolatileBits())) {
                        throw new UnsupportedOperationException("Nonvolatile state not preserved");
                    }

                    return result.volatileBits();
                } else {
                    return delegate.invoke(call);
                }
            }
        };
    }

    public static GovernmentCallee164Api.NormalReturn executeEntry183(GovernmentCallee164Api.Entry entry, GovernmentSharedManager167Api.Memory memory, GovernmentPrimaryTail155Api.Calls delegate) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        GovernmentPrimaryTail155Api.Calls boundCalls = bind(entry.imageBaseBits(), memory, delegate);
        return GovernmentRegistryEntry183.execute(entry, memory, boundCalls);
    }
}
