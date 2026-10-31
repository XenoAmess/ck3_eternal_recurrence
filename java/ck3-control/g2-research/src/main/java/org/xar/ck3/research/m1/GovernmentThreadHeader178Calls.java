package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

public final class GovernmentThreadHeader178Calls {

    private GovernmentThreadHeader178Calls() { }

    public static GovernmentPrimaryTail155Api.Calls bind(
            long imageBase,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls delegate,
            GovernmentThreadHeader178Api.Ports ports,
            GovernmentThreadHeader178Api.WaitBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(ports);
        Objects.requireNonNull(budget);

        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return delegate.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == 0x3F8A813L && call.targetRva() == 0x4223A84L) {
                    long calleeRsp = call.rspBits() - 8L;
                    long expectedRip = imageBase + call.callSiteRva() + 5L;

                    memory.writeQword(calleeRsp, expectedRip);

                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                            imageBase,
                            calleeRsp,
                            call.volatileBits(),
                            call.nonvolatileBits()
                    );

                    GovernmentCallee164Api.NormalReturn result = GovernmentThreadHeader178.execute(
                            entry,
                            memory,
                            ports,
                            budget
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
            GovernmentThreadHeader178Api.Ports ports,
            GovernmentThreadHeader178Api.WaitBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(ports);
        Objects.requireNonNull(budget);

        GovernmentPrimaryTail155Api.Calls boundCalls = bind(
                entry.imageBaseBits(),
                memory,
                delegate,
                ports,
                budget
        );

        return GovernmentSharedManager167.execute(entry, memory, boundCalls);
    }
}