package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
public final class MapRecord86f210208WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }
    @Test
    void aliasRetIsReadAfterStore() {
        long image = 0x1000000L;
        long S = 0x2000000L;
        long newRip = 0xFEDCBA9876543210L;
        long oldRax = 0xAA00000011111111L;
        long otherR8 = 0xBB00000022222222L;
        long otherR9 = 0xCC00000033333333L;
        long otherR10 = 0xDD00000044444444L;
        long otherR11 = 0xEE00000055555555L;
        long seed = 0x60000000L;
        VolatileBits in = q(v(seed), oldRax, S, newRip, otherR8, otherR9, otherR10, otherR11);
        NonvolatileBits n = nv(seed);
        Bytes m = new Bytes();
        m.putQ(S, 0x1122334455667788L);
        NormalReturn nr = MapRecord86f210208.execute(new Entry(image, S, in, n), m);
        VolatileBits expectedV = q(in, S, in.rcxBits(), in.rdxBits(), in.r8Bits(), in.r9Bits(), in.r10Bits(), in.r11Bits());
        assertEquals(expectedV, nr.volatileBits());
        assertEquals(newRip, nr.returnRipBits());
        assertEquals(S + 8, nr.callerRspBits());
        assertEquals(n, nr.nonvolatileBits());
        assertEquals(List.of(new Op("wq", S, newRip), new Op("rq", S, newRip)), m.ops);
    }

    @Test
    void allThreeActualSitesUseParentsReturnSlot() {
        long image = 0x1000000L;
        long S = 0x2000000L;
        long output = 0x3000000L;
        long map = 0xFEDCBA9876543210L;
        long seed = 0x5000000L;
        for (long site : new long[]{0x337BBD0L, 0x337C8B1L, 0x337C5BDL}) {
            Bytes m = new Bytes();
            Ports fallback = new Ports();
            Calls bound = MapRecord86f210208Calls.bind(image, m, fallback);
            VolatileBits in = q(v(seed), 0xAA00000000000011L, output, map, 0xBB00000000000022L, 0xCC00000000000033L, 0xDD00000000000044L, 0xEE00000000000055L);
            NonvolatileBits n = nv(seed);
            m.writeQword(S - 8, image + site + 5);
            VolatileBits wholeV = q(in, output, output, map, in.r8Bits(), in.r9Bits(), in.r10Bits(), in.r11Bits());
            assertEquals(wholeV, bound.invoke(new Call(site, TargetKind.DIRECT_RVA, 0x86F210L, S, in, n)));
            assertEquals(map, m.rawQ(output));
            assertEquals(List.of(new Op("wq", S - 8, image + site + 5), new Op("wq", output, map), new Op("rq", S - 8, image + site + 5)), m.ops);
        }
    }
}
