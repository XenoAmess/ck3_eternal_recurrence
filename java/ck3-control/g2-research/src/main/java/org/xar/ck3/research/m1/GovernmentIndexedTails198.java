package org.xar.ck3.research.m1;

import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class GovernmentIndexedTails198 {
    private GovernmentIndexedTails198() { }

    public static NormalReturn tail4247ffc(Entry entry, Memory memory, Calls fallback) {
        long base = entry.imageBaseBits();
        long ecx = entry.volatileBits().rcxBits();
        long rax = entry.volatileBits().raxBits();
        long[] outRax = new long[1];
        long[] outRcx = new long[1];
        RequestIndexedTails4247ffc.Ports ports = new RequestIndexedTails4247ffc.Ports() {
            public void jump43da500(long knownRcx, long liveRax) {
                outRax[0] = liveRax;
                outRcx[0] = knownRcx;
            }
            public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                throw new UnsupportedOperationException();
            }
        };
        RequestIndexedTails4247ffc.call4247ffc(base, (int) ecx, ports);
        long target = memory.readQword(base + 0x43DA500L);
        VolatileBits v = entry.volatileBits();
        VolatileBits newV = new VolatileBits(outRax[0], outRcx[0], v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
        Tail t = new Tail(0x424800EL, TargetKind.INDIRECT_ABSOLUTE, target, new Entry(base, entry.rspBits(), newV, entry.nonvolatileBits()));
        return fallback.tail(t);
    }

    public static NormalReturn tail4248050(Entry entry, Memory memory, Calls fallback) {
        long base = entry.imageBaseBits();
        long ecx = entry.volatileBits().rcxBits();
        long rax = entry.volatileBits().raxBits();
        long rbx = entry.nonvolatileBits().rbxBits();
        long[] outRax = new long[1];
        long[] outRcx = new long[1];
        RequestIndexedTails4247ffc.Ports ports = new RequestIndexedTails4247ffc.Ports() {
            public void jump43da500(long knownRcx, long liveRax) {
                throw new UnsupportedOperationException();
            }
            public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                outRax[0] = liveRax;
                outRcx[0] = knownRcx;
            }
        };
        RequestIndexedTails4247ffc.call4248050(base, (int) ecx, rbx, ports);
        long target = memory.readQword(base + 0x43DA4F0L);
        VolatileBits v = entry.volatileBits();
        VolatileBits newV = new VolatileBits(outRax[0], outRcx[0], v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
        Tail t = new Tail(0x4248062L, TargetKind.INDIRECT_ABSOLUTE, target, new Entry(base, entry.rspBits(), newV, entry.nonvolatileBits()));
        return fallback.tail(t);
    }

    public static Calls bind(long imageBase, Memory memory, Calls fallback) {
        return new Calls() {
            public VolatileBits invoke(Call call) {
                if (call.kind() == TargetKind.DIRECT_RVA) {
                    if (call.callSiteRva() == 0x424DB4FL && call.targetBits() == 0x4247FFCL) {
                        Entry childEntry = new Entry(imageBase, call.rspBits() - 8, call.volatileBits(), call.nonvolatileBits());
                        NormalReturn ret = tail4247ffc(childEntry, memory, fallback);
                        if (ret.returnRipBits() != imageBase + 0x424DB54L || ret.callerRspBits() != call.rspBits() || !ret.nonvolatileBits().equals(call.nonvolatileBits())) {
                            throw new AssertionError();
                        }
                        return ret.volatileBits();
                    } else if (call.callSiteRva() == 0x424DB61L && call.targetBits() == 0x4248050L) {
                        Entry childEntry = new Entry(imageBase, call.rspBits() - 8, call.volatileBits(), call.nonvolatileBits());
                        NormalReturn ret = tail4248050(childEntry, memory, fallback);
                        if (ret.returnRipBits() != imageBase + 0x424DB66L || ret.callerRspBits() != call.rspBits() || !ret.nonvolatileBits().equals(call.nonvolatileBits())) {
                            throw new AssertionError();
                        }
                        return ret.volatileBits();
                    }
                }
                return fallback.invoke(call);
            }
            public NormalReturn tail(Tail transfer) {
                return fallback.tail(transfer);
            }
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}
