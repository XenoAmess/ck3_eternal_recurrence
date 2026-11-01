package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.CallResult;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.PendingSlotKnownPageData531.*;

public final class PendingSlotKnownPageBook531 {
    private PendingSlotKnownPageBook531() { }

    public static Scene scene() {
        long M = 0x3300000000L;
        long E = 0x810000000000D008L;
        long R = 0x8100000000004000L;
        long T = R + 8;
        long S = 0x8100000000010000L;
        long P3 = 0x810000000000A100L;
        long P3b = 0x810000000000A180L;
        long P4 = 0x810000000000A200L;
        long P5 = 0x810000000000A300L;
        long P6 = 0x810000000000A400L;
        long RET = 0xAABBCCDD11223344L;
        long RB = E - 0x58L;
        long PE = E - 0x60L;
        long PB = E - 0xA8L;
        long PJ = E - 0xB0L;

        List<Cell> initialMemory = List.of(
            c(8, E, RET),
            c(8, E + 0x28, P5),
            c(8, E + 0x30, P6),
            c(4, P3, 0x01234567L),
            c(1, P4, 1),
            c(1, P5, 0),
            c(4, P6, 0),
            c(1, T + 0x40, 0),
            c(1, T + 0x41, 0),
            c(4, T + 0x38, 0xFFFFFFL),
            c(4, T + 0x24, 1),
            c(4, S + 0x2E8, 0xFFFFFFFFL),
            c(8, M + 0x5D1EC70L, 0xDEADBEEF01234567L)
        );

        VolatileBits growV = new VolatileBits(
            2L, T, 2L, P3, P4, 0x100AL, 0x100BL,
            x(0x1010), x(0x1020), x(0x1030), x(0x1040), x(0x1050), x(0x1060)
        );
        NonvolatileBits growN = n(T, 0x2002L, 0x2003L, 0x2004L, S, P4, 0x2007L, 0x2008L);
        FullSlotProducer479Api.CallFrame growFrame = rf(0x2A327CEL, 0x1ACDFB0L, RB, growV, growN, false);
        CallResult growResult = result(v(0x3000L, 0x9999888877776601L, 0x3132333435363738L, 0x4142434445464748L), growN, M + 0x2A327D3L, RB, true);
        List<Write> growEffects = List.of(
            w(4, T + 0x38, 0xFFFFFEL),
            w(8, E + 0x18, P3b),
            w(4, P3b, 0x89ABCDEFL),
            w(1, T + 0x40, 0)
        );

        VolatileBits loggerV = v(0x3000L, M + 0x5D1DAD9L, M + 0x45B64C8L, 0xFFFFFFL);
        NonvolatileBits loggerN = n(T, 0x2002L, 0x2003L, 0xFFFFFEL, S, P4, T, 0xFFFFFEL);
        FullPage495Api.CallFrame loggerFrame = pf(0x2A3221AL, 0x3F7AA40L, PB, loggerV, loggerN, true);
        CallResult loggerResult = result(v(0xF000L, 0x11223344556677FFL, 0x2233445566778899L, 0x33445566778899AAL), loggerN, M + 0x2A3221FL, PB, true);
        List<Write> loggerEffects = List.of(w(4, T + 0xC, 0x55667788L));

        List<Step> steps = List.of(
            w(8, E + 0x10, 0x2001L),
            w(8, E + 0x18, P3),
            w(8, E - 0x08, 0x2002L),
            w(8, E - 0x10, 0x2003L),
            w(8, E - 0x18, 0x2004L),
            w(8, E - 0x20, 0x2005L),
            w(8, E - 0x28, 0x2006L),
            w(8, E - 0x30, 0x2007L),
            w(8, E - 0x38, 0x2008L),
            r(1, T + 0x40, 0),
            r(1, T + 0x41, 0),
            r(4, T + 0x38, 0xFFFFFFL),
            r(4, T + 0x24, 1),
            w(8, PE, M + 0x2A327D3L),
            new RootInvoke(growFrame, growResult, growEffects),
            w(4, T + 0x38, 0xFFFFFEL),
            w(8, E + 0x18, P3b),
            w(4, P3b, 0x89ABCDEFL),
            w(1, T + 0x40, 0),
            r(4, T + 0x38, 0xFFFFFEL),
            w(8, PE, M + 0x2A327ECL),
            w(8, PE - 0x08, 0x2007L),
            r(1, T + 0x40, 0),
            w(8, PB + 0x20, M + 0x5D1DAD9L),
            w(8, PJ, M + 0x2A3221FL),
            new PageInvoke(loggerFrame, loggerResult, loggerEffects),
            w(4, T + 0xC, 0x55667788L),
            r(8, PE - 0x08, 0x2007L),
            r(8, PE, M + 0x2A327ECL),
            r(8, M + 0x5D1EC70L, 0xDEADBEEF01234567L),
            r(8, E + 0x10, 0x2001L),
            r(8, E - 0x38, 0x2008L),
            r(8, E - 0x30, 0x2007L),
            r(8, E - 0x28, 0x2006L),
            r(8, E - 0x20, 0x2005L),
            r(8, E - 0x18, 0x2004L),
            r(8, E - 0x10, 0x2003L),
            r(8, E - 0x08, 0x2002L),
            r(8, E, RET)
        );

        VolatileBits finalV = v(0xF000L, 0xDEADBEEF01234567L, 0x2233445566778899L, 0x33445566778899AAL);
        NonvolatileBits finalN = n0();
        CallResult expectedResult = result(finalV, finalN, RET, E + 8, true);

        List<Cell> finalMemory = List.of(
            c(8, E + 0x10, 0x2001L),
            c(8, E + 0x18, P3b),
            c(8, E - 0x08, 0x2002L),
            c(8, E - 0x10, 0x2003L),
            c(8, E - 0x18, 0x2004L),
            c(8, E - 0x20, 0x2005L),
            c(8, E - 0x28, 0x2006L),
            c(8, E - 0x30, 0x2007L),
            c(8, E - 0x38, 0x2008L),
            c(4, T + 0x38, 0xFFFFFEL),
            c(4, P3b, 0x89ABCDEFL),
            c(1, T + 0x40, 0),
            c(8, PE, M + 0x2A327ECL),
            c(8, PE - 0x08, 0x2007L),
            c(8, PB + 0x20, M + 0x5D1DAD9L),
            c(8, PJ, M + 0x2A3221FL),
            c(4, T + 0xC, 0x55667788L),
            c(8, E, RET),
            c(8, M + 0x5D1EC70L, 0xDEADBEEF01234567L)
        );

        return new Scene(
            "KNOWN_PAGE",
            new GovernmentCrtBoundary185Api.Entry(M, E, v0(), n0()),
            false,
            initialMemory,
            steps,
            expectedResult,
            finalMemory
        );
    }

    public static List<Scene> scenes() {
        return List.of(scene());
    }

    public static int verify() {
        List<Scene> scenes = scenes();
        for (Scene scene : scenes) {
            PendingSlotKnownPageHost531.verify(scene);
        }
        return scenes.size();
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }
}