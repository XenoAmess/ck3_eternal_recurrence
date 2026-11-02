package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Exact Base203 allocation site, with its inner Gate47 site reusing the mature body. */
public final class Allocate94FullState282Calls {
    private Allocate94FullState282Calls() { }

    public static Calls bind(long imageBase, Memory memory, Calls fallback, LoopBudget budget) {
        Calls childCalls = new Calls() {
            @Override public VolatileBits invoke(Call call) {
                if (call.kind() == TargetKind.DIRECT_RVA
                        && call.callSiteRva() == 0x424FDC9L && call.targetBits() == 0x424CFFCL) {
                    Entry entry = new Entry(imageBase, call.rspBits() - 8L,
                            call.volatileBits(), call.nonvolatileBits());
                    NormalReturn out = Gate47FullState273.execute(entry, memory, fallback);
                    return checked(imageBase, call, out, 0x424FDCEL);
                }
                return fallback.invoke(call);
            }
            @Override public NormalReturn tail(Tail transfer) { return fallback.tail(transfer); }
            @Override public long readGsQword58() { return fallback.readGsQword58(); }
        };
        return new Calls() {
            @Override public VolatileBits invoke(Call call) {
                if (call.kind() == TargetKind.DIRECT_RVA
                        && call.callSiteRva() == 0x4251F64L && call.targetBits() == 0x424FDA0L) {
                    Entry entry = new Entry(imageBase, call.rspBits() - 8L,
                            call.volatileBits(), call.nonvolatileBits());
                    NormalReturn out = Allocate94FullState282.execute(entry, memory, childCalls, budget);
                    return checked(imageBase, call, out, 0x4251F69L);
                }
                return fallback.invoke(call);
            }
            @Override public NormalReturn tail(Tail transfer) { return fallback.tail(transfer); }
            @Override public long readGsQword58() { return fallback.readGsQword58(); }
        };
    }

    private static VolatileBits checked(long imageBase, Call call, NormalReturn out, long returnRva) {
        if (out.returnRipBits() != imageBase + returnRva || out.callerRspBits() != call.rspBits()
                || !out.nonvolatileBits().equals(call.nonvolatileBits())) {
            throw new UnsupportedOperationException("represented normal continuation mismatch");
        }
        return out.volatileBits();
    }
}
