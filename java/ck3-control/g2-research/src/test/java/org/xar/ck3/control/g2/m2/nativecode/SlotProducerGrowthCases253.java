package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import static org.xar.ck3.control.g2.m2.nativecode.SlotProducerGrowthFixture253.*;
/** Owner source-derived literal:470 GROW->372->133 then PAGEfalse, not target-generated. */
public final class SlotProducerGrowthCases253 {
    private SlotProducerGrowthCases253() { }
    private static Step m(Kind k,long at,long value) { return new Step(k,at,value,0,0,0); }
    private static Step c(Kind k,long target,long value,long a,long b,long x) { return new Step(k,target,value,a,b,x); }
    public static List<Scene> scenes() {
        long t=0x1008L;
        return List.of(new Scene("actual470-grow-array-then-pagefalse",
            new PendingSlotProducer2A32770.Input(0x1000L,0,0,0,0,0,0x100000000L),
            0x1234567887654321L,List.of(
                m(Kind.R8,t+0x40,0), m(Kind.R8,t+0x41,0),
                m(Kind.R32,t+0x38,0xFFFFFF), m(Kind.R32,t+0x24,1),
                m(Kind.R8,t+0x40,0), m(Kind.R32,t+0x24,1), m(Kind.R32,t+0x24,1),
                m(Kind.R32,t+0x20,1), m(Kind.R64,t+0x28,0x4000),
                m(Kind.R64,0x4000,0x5000), m(Kind.R64,0x5008,0x6000),
                c(Kind.ALLOC,0x6000,0x3000,0x4000,32,8),
                m(Kind.R32,t+0x24,1), m(Kind.R64,t+0x18,0x2000),
                c(Kind.COPY,0,0,0x3000,0x2000,16), m(Kind.R32,t+0x24,1),
                m(Kind.R64,t+0x28,0x4000), m(Kind.R64,t+0x18,0x2000),
                m(Kind.R64,0x4000,0x5000), m(Kind.R64,0x5010,0x7000),
                c(Kind.RELEASE,0x7000,0,0x4000,0x2000,8),
                m(Kind.W64,t+0x18,0x3000), m(Kind.W32,t+0x24,1), m(Kind.W32,t+0x20,2),
                m(Kind.R32,t+0x24,1), m(Kind.R64,t+0x18,0x3000),
                c(Kind.SET,0,0,0x3010,0,16), m(Kind.W32,t+0x24,2),
                m(Kind.R64,t+0x18,0x3000), m(Kind.W32,0x3014,0xFFFFFF),
                m(Kind.R64,t+0x18,0x3000), m(Kind.W64,0x3018,0),
                m(Kind.R64,t+0x18,0x3000), m(Kind.W32,0x3010,0xFFFFFF),
                m(Kind.R32,t+0x38,0xFFFFFF), m(Kind.W32,t+0x38,1),
                m(Kind.R32,t+0x38,1), c(Kind.PAGE,0,0,t,2,0),
                m(Kind.R64,0x105D1EC70L,0x1234567887654321L)
            )));
    }
}
