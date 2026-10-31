package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.QueueCompositionData355.Op;
import org.xar.ck3.control.g2.m2.nativecode.QueueCompositionData355.Scene;
import org.xar.ck3.control.g2.m2.nativecode.QueueCompositionData355.Step;
/** OwnerNONBLIND48literal: actual103+81+227; two modelBooks rejected. */
public final class QueueCompositionCases355 {
    private QueueCompositionCases355() { }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("known81-false-known227-nongrowth",0x1100000000L,0x3300000000L,0x7FF000000000L, List.of(
                new Step(Op.R8,List.of(0x110000004EL,0x0L),0x0L),
                new Step(Op.R32,List.of(0x110000001CL,0x0L),0x0L),
                new Step(Op.R64,List.of(0x1100000030L,0x5500000000L),0x0L),
                new Step(Op.R32,List.of(0x110000003CL,0x0L),0x0L),
                new Step(Op.R32,List.of(0x1100000048L,0x0L),0x0L),
                new Step(Op.R32,List.of(0x3305C9FF68L,0x0L),0x0L),
                new Step(Op.CAS,List.of(0x3305C9FF68L,0x0L,0x1L),0x0L),
                new Step(Op.W64,List.of(0x7FF000000000L,0x1100000000L),0x0L),
                new Step(Op.R32,List.of(0x3305468A74L,0x0L),0x0L),
                new Step(Op.R32,List.of(0x3305468A70L,0x1L),0x0L),
                new Step(Op.R64,List.of(0x3305468A68L,0xCC00000000L),0x0L),
                new Step(Op.R64,List.of(0x7FF000000000L,0x1100000000L),0x0L),
                new Step(Op.W64,List.of(0xCC00000000L,0x1100000000L),0x0L),
                new Step(Op.R32,List.of(0x3305468A74L,0x0L),0x0L),
                new Step(Op.W32,List.of(0x3305468A74L,0x1L),0x0L),
                new Step(Op.R32,List.of(0x3305468A74L,0x1L),0x0L),
                new Step(Op.R64,List.of(0x3305468A68L,0xCC00000000L),0x0L),
                new Step(Op.W8,List.of(0x110000004EL,0x1L),0x0L),
                new Step(Op.W32,List.of(0x3305C9FF68L,0x0L),0x0L)
            )),
            new Scene("known81-false-known227-growth",0x1100000000L,0x3300000000L,0x7FF000000000L, List.of(
                new Step(Op.R8,List.of(0x110000004EL,0x0L),0x0L),
                new Step(Op.R32,List.of(0x110000001CL,0x0L),0x0L),
                new Step(Op.R64,List.of(0x1100000030L,0x5500000000L),0x0L),
                new Step(Op.R32,List.of(0x110000003CL,0x0L),0x0L),
                new Step(Op.R32,List.of(0x1100000048L,0x0L),0x0L),
                new Step(Op.R32,List.of(0x3305C9FF68L,0x0L),0x0L),
                new Step(Op.CAS,List.of(0x3305C9FF68L,0x0L,0x1L),0x0L),
                new Step(Op.W64,List.of(0x7FF000000000L,0x1100000000L),0x0L),
                new Step(Op.R32,List.of(0x3305468A74L,0x0L),0x0L),
                new Step(Op.R32,List.of(0x3305468A70L,0x0L),0x0L),
                new Step(Op.R64,List.of(0x3305468A78L,0x8800000000L),0x0L),
                new Step(Op.R32,List.of(0x33049F64F0L,0x3FC00000L),0x0L),
                new Step(Op.R64,List.of(0x8800000000L,0x9900000000L),0x0L),
                new Step(Op.R64,List.of(0x9900000008L,0xAB00000000L),0x0L),
                new Step(Op.ALLOC,List.of(0xAB00000000L,0x8800000000L,0x8L,0x8L),0xBB00000000L),
                new Step(Op.R32,List.of(0x3305468A74L,0x0L),0x0L),
                new Step(Op.R64,List.of(0x7FF000000000L,0x1100000000L),0x0L),
                new Step(Op.W64,List.of(0xBB00000000L,0x1100000000L),0x0L),
                new Step(Op.R32,List.of(0x3305468A74L,0x0L),0x0L),
                new Step(Op.R64,List.of(0x3305468A78L,0x8800000000L),0x0L),
                new Step(Op.R64,List.of(0x3305468A68L,0x0L),0x0L),
                new Step(Op.R64,List.of(0x8800000000L,0x9900000000L),0x0L),
                new Step(Op.R64,List.of(0x9900000010L,0xAC00000000L),0x0L),
                new Step(Op.FREE,List.of(0xAC00000000L,0x8800000000L,0x0L,0x8L),0x0L),
                new Step(Op.W32,List.of(0x3305468A70L,0x1L),0x0L),
                new Step(Op.W64,List.of(0x3305468A68L,0xBB00000000L),0x0L),
                new Step(Op.W32,List.of(0x3305468A74L,0x1L),0x0L),
                new Step(Op.W8,List.of(0x110000004EL,0x1L),0x0L),
                new Step(Op.W32,List.of(0x3305C9FF68L,0x0L),0x0L)
            ))
        );
    }
}
