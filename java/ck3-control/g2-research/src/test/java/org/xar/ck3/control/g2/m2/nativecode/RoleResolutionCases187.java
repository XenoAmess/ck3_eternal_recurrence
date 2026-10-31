package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import static org.xar.ck3.control.g2.m2.nativecode.RoleResolutionScenario187.Op.*;
import org.xar.ck3.control.g2.m2.nativecode.RoleResolutionScenario187.Scene;
import org.xar.ck3.control.g2.m2.nativecode.RoleResolutionScenario187.Step;
import org.xar.ck3.control.g2.m2.nativecode.RoleResolutionScenario187.Op;

/** Owner independent literal book after both complete model candidates were rejected. */
public final class RoleResolutionCases187 {
    private RoleResolutionCases187() { }
    private static Step s(Op op, long address, long value) { return new Step(op,address,value); }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("null-storage-shared-full64",0x1000L,0x2000L,0x10000000L,List.of(
                s(R32,0x22d8L,0xf0000001L),s(W32,0x1250L,0xf0000001L),
                s(R32,0x22e8L,0x80000002L),s(W32,0x1254L,0x80000002L),
                s(R32,0x22dcL,0xffffffffL),s(W32,0x1258L,0xffffffffL),
                s(R64,0x15c67568L,0),s(R64,0x15c67570L,0xfedcba9876543210L)
            ),0xfedcba9876543210L,0xfedcba9876543210L,0xfedcba9876543210L),
            new Scene("unsigned-capacity-highbit-fullids",0x1000L,0x2000L,0x10000000L,List.of(
                s(R32,0x22d8L,0x80000001L),s(W32,0x1250L,0x80000001L),
                s(R32,0x22e8L,0xff000002L),s(W32,0x1254L,0xff000002L),
                s(R32,0x22dcL,0xa5000003L),s(W32,0x1258L,0xa5000003L),
                s(R64,0x15c67568L,0x50000000L),s(R32,0x5000002cL,0x80000000L),
                s(R64,0x15c67570L,0x9999999999999999L),
                s(R64,0x50000020L,0x60000000L),s(R64,0x60000018L,0x1111111122222222L),s(R32,0x111111112222223aL,0x80000001L),
                s(R64,0x50000020L,0x60000000L),s(R64,0x60000028L,0x3333333344444444L),s(R32,0x333333334444445cL,0xff000002L),
                s(R64,0x50000020L,0x60000000L),s(R64,0x60000038L,0x5555555566666666L),s(R32,0x555555556666667eL,0xa5000003L)
            ),0x1111111122222222L,0x3333333344444444L,0x5555555566666666L),
            new Scene("null-version-mismatch-boundary",0x1000L,0x2000L,0x10000000L,List.of(
                s(R32,0x22d8L,0x81000000L),s(W32,0x1250L,0x81000000L),
                s(R32,0x22e8L,0x82000001L),s(W32,0x1254L,0x82000001L),
                s(R32,0x22dcL,0x84000003L),s(W32,0x1258L,0x84000003L),
                s(R64,0x15c67568L,0x50000000L),s(R32,0x5000002cL,3),s(R64,0x15c67570L,0x8877665544332211L),
                s(R64,0x50000020L,0x60000000L),s(R64,0x60000008L,0),
                s(R64,0x50000020L,0x60000000L),s(R64,0x60000018L,0x2222222233333333L),s(R32,0x222222223333334bL,0x83000001L)
            ),0x8877665544332211L,0x8877665544332211L,0x8877665544332211L),
            new Scene("each-role-fresh-slot-pointer",0x1000L,0x2000L,0x10000000L,List.of(
                s(R32,0x22d8L,0xff000001L),s(W32,0x1250L,0xff000001L),
                s(R32,0x22e8L,0xff000001L),s(W32,0x1254L,0xff000001L),
                s(R32,0x22dcL,0xff000001L),s(W32,0x1258L,0xff000001L),
                s(R64,0x15c67568L,0x50000000L),s(R32,0x5000002cL,2),s(R64,0x15c67570L,0x123456789abcdef0L),
                s(R64,0x50000020L,0x60000000L),s(R64,0x60000018L,0x1111111122222222L),s(R32,0x111111112222223aL,0xff000001L),
                s(R64,0x50000020L,0x70000000L),s(R64,0x70000018L,0x3333333344444444L),s(R32,0x333333334444445cL,0xff000001L),
                s(R64,0x50000020L,0x80000000L),s(R64,0x80000018L,0x5555555566666666L),s(R32,0x555555556666667eL,0xff000001L)
            ),0x1111111122222222L,0x3333333344444444L,0x5555555566666666L)
        );
    }
}
