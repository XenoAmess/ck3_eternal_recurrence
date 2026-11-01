package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class Gate47FullState273Calls {
    private Gate47FullState273Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long imageBase,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public VolatileBits invoke(Call call) {
                if (call.kind() == TargetKind.DIRECT_RVA
                        && call.callSiteRva() == 0x4251FA1L
                        && call.targetBits() == 0x424CFFCL) {
                    Entry childEntry = new Entry(imageBase, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
                    NormalReturn result = Gate47FullState273.execute(childEntry, memory, fallback);
                    if (result.returnRipBits() != imageBase + 0x4251FA6L
                            || result.callerRspBits() != call.rspBits()
                            || !result.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new UnsupportedOperationException("Normal continuation mismatch");
                    }
                    return result.volatileBits();
                }
                return fallback.invoke(call);
            }

            @Override
            public NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                return fallback.tail(transfer);
            }

            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}