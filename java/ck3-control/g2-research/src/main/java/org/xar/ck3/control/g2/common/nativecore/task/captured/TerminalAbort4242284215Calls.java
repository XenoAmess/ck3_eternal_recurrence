package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalTailTarget42421c8213.Memory16;

public final class TerminalAbort4242284215Calls {
    private TerminalAbort4242284215Calls() { }

    public static TerminalAbort4242284215.Calls60 bind(long image, Memory16 memory, TerminalAbort4242284215.Calls60 fallback) {
        return new TerminalAbort4242284215.Calls60() {
            @Override
            public VolatileBits invoke(Call call) {
                if (call.kind() == TargetKind.DIRECT_RVA && call.callSiteRva() == 0x424227EL && call.targetBits() == 0x4242284L) {
                    Entry childEntry = new Entry(
                        image,
                        call.rspBits() - 8,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );
                    return TerminalAbort4242284215.execute(childEntry, memory, fallback);
                }
                return fallback.invoke(call);
            }

            @Override
            public NormalReturn tail(Tail transfer) {
                return fallback.tail(transfer);
            }

            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }

            @Override
            public long readGsQword60() {
                return fallback.readGsQword60();
            }
        };
    }
}