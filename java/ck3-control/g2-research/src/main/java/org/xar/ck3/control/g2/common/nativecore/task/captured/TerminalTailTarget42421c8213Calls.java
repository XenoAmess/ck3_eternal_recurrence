package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class TerminalTailTarget42421c8213Calls {
    private TerminalTailTarget42421c8213Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            TerminalTailTarget42421c8213.Memory16 memory,
            GovernmentCrtBoundary185Api.Calls fallback) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public VolatileBits invoke(Call call) {
                return fallback.invoke(call);
            }

            @Override
            public NormalReturn tail(Tail transfer) {
                if (transfer.jumpSiteRva() == 0x424235BL
                        && transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && transfer.targetBits() == 0x42421C8L) {
                    return TerminalTailTarget42421c8213.execute(transfer.entry(), memory, fallback);
                }
                return fallback.tail(transfer);
            }

            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}