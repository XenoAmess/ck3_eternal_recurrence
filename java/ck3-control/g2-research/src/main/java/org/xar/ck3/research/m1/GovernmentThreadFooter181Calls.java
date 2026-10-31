package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m1.GovernmentThreadFooter181;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api;

public final class GovernmentThreadFooter181Calls {

    private GovernmentThreadFooter181Calls() { }

    public static GovernmentPrimaryTail155Api.Calls bind(
            long imageBase,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls delegate,
            GovernmentThreadHeader178Api.Ports ports) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(ports);

        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return delegate.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                // Route ONLY actual old manager callsite 3F8A8A2, target 4223A24
                if (call.callSiteRva() == 0x3F8A8A2L && call.targetRva() == 0x4223A24L) {
                    long calleeRsp = call.rspBits() - 8L;
                    long expectedRip = imageBase + 0x3F8A8A7L;

                    // Write EXACTLY ONCE at call.rspBits()-8 the image+3F8A8A7 continuation
                    memory.writeQword(calleeRsp, expectedRip);

                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                            imageBase,
                            calleeRsp,
                            call.volatileBits(),
                            call.nonvolatileBits()
                    );

                    GovernmentCallee164Api.NormalReturn result = GovernmentThreadFooter181.execute(
                            entry,
                            memory,
                            ports
                    );

                    if (result.returnRipBits() != expectedRip) {
                        throw new UnsupportedOperationException("Invalid return RIP");
                    }
                    if (result.callerRspBits() != call.rspBits()) {
                        throw new UnsupportedOperationException("Invalid caller RSP");
                    }
                    if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new UnsupportedOperationException("Invalid nonvolatile preservation");
                    }

                    return result.volatileBits();
                } else {
                    return delegate.invoke(call);
                }
            }
        };
    }

    public static GovernmentCallee164Api.NormalReturn executeManager(
            GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls delegate,
            GovernmentThreadHeader178Api.Ports ports) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(ports);

        GovernmentPrimaryTail155Api.Calls boundCalls = bind(
                entry.imageBaseBits(),
                memory,
                delegate,
                ports
        );

        return GovernmentSharedManager167.execute(entry, memory, boundCalls);
    }
}
