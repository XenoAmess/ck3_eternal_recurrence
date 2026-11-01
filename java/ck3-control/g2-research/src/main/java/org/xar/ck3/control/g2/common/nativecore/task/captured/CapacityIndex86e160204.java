package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m3.CapacityIndex179;

public final class CapacityIndex86e160204 {
    private CapacityIndex86e160204() {}

    public static GovernmentCrtBoundary185Api.NormalReturn execute(GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory) {
        long rsp = entry.rspBits();
        long callerRsp = rsp + 8;

        long rax = entry.volatileBits().raxBits();
        long rcx = entry.volatileBits().rcxBits();
        long rdx = entry.volatileBits().rdxBits();
        long r8 = entry.volatileBits().r8Bits();
        long r9 = entry.volatileBits().r9Bits();
        long r10 = entry.volatileBits().r10Bits();
        long r11 = entry.volatileBits().r11Bits();
        var x0 = entry.volatileBits().xmm0();
        var x1 = entry.volatileBits().xmm1();
        var x2 = entry.volatileBits().xmm2();
        var x3 = entry.volatileBits().xmm3();
        var x4 = entry.volatileBits().xmm4();
        var x5 = entry.volatileBits().xmm5();

        int count = (int)rcx;
        int bias = (int)rdx;
        int sel = CapacityIndex179.select(count, bias);
        rax = Integer.toUnsignedLong(sel);

        r9 = Integer.toUnsignedLong((int)rdx);

        if (count > 1) {
            int c1 = count - 1;
            int msb = 31 - Integer.numberOfLeadingZeros(c1);
            int edx = 31 - msb;
            int r8v = 1 + msb;
            int ecx = r8v + bias;
            rdx = Integer.toUnsignedLong(edx);
            r8 = Integer.toUnsignedLong(r8v);
            rcx = Integer.toUnsignedLong(ecx);
        } else {
            r8 = 0;
            rcx = Integer.toUnsignedLong((int)(r8 + rdx));
        }

        GovernmentPrimaryTail155Api.VolatileBits v = new GovernmentPrimaryTail155Api.VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
        long rip = memory.readQword(rsp);
        return new GovernmentCrtBoundary185Api.NormalReturn(v, rip, callerRsp, entry.nonvolatileBits());
    }
}