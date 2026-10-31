package org.xar.ck3.research.m3.map191;
import java.util.List;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Input;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Scratch;
import org.xar.ck3.research.m3.map191.MapInsertWitness191Api.*;
import static org.xar.ck3.research.m3.map191.MapInsertWitness191Api.Kind.*;

public final class MapInsertWitnessBook191 {
    private MapInsertWitnessBook191() { }
    public static List<Scene> scenes() { return List.of(equal(), empty(), displaced()); }
    private static Scene equal() {
        long m=0x1100001000L,b=0x2200002000L,s=b+0x50L,o=0x3300003000L,d=0x4400004000L;
        long kd=0x8123456700006000L,bd=0x9234567800007000L;
        long kc=0x8000000100000010L,bc=0x8000000200000010L;
        return new Scene("occupied_unsigned_heap_equal_lowAL_true",
            new Input(0x6600000000L,m,o,0x80000002,d,new Scratch(0x5500005000L)),
            List.of(c(m+0x14L,4,3),c(m+8L,8,b),c(s+4L,1,1),c(d+0x18L,8,kc),
                c(s+0x20L,8,bc),c(s+8L,8,bd),c(d,8,kd)),
            List.of(a(R32,m+0x14L,3),a(R64,m+8L,b),a(R8,s+4L,1),a(R64,d+0x18L,kc),
                a(R64,s+0x20L,bc),a(R64,s+8L,bd),a(R64,d,kd),
                p(EQUAL,0xC3B9CAL,List.of(kd,bd),0x101L,List.of()),
                a(W64,o,s),a(W8,o+8L,0)),o,List.of(c(o,8,s),c(o+8L,1,0)));
    }
    private static Scene empty() {
        long m=0x1200001000L,b=0x2300002000L,s=b+0x28L,o=0x3400003000L,d=0x4500004000L;
        long l=0x0123456789ABCDEFL,h=0xFEDCBA9876543210L,n=0x100000013L,q=0x200000022L;
        return new Scene("empty_actual_move32_and_source_reset",
            new Input(0x6700000000L,m,o,0x80000001,d,new Scratch(0x5600005000L)),
            List.of(c(m+0x14L,4,7),c(m+8L,8,b),c(s+4L,1,0),c(m+0x18L,1,4),
                c(m+0x10L,4,2),c(m+0x1CL,4,0x3F800000L),v(d,l,h),v(d+0x10L,n,q)),
            List.of(a(R32,m+0x14L,7),a(R64,m+8L,b),a(R8,s+4L,0),a(R8,m+0x18L,4),
                a(R32,m+0x10L,2),a(R32,m+0x1CL,0x3F800000L),a(R8,s+4L,0),
                a(W32,s,0x80000001L),a(W8,s+4L,1),a(W64,s+8L,0),
                a(W64,s+0x18L,0),a(W64,s+0x20L,0),
                t(R128,d,l,h),t(W128,s+8L,l,h),t(R128,d+0x10L,n,q),t(W128,s+0x18L,n,q),
                a(W64,d+0x10L,0),a(W64,d+0x18L,15),a(W8,d,0),
                a(R32,m+0x10L,2),a(W32,m+0x10L,3),a(W64,o,s),a(W8,o+8L,1)),o,
            List.of(c(o,8,s),c(o+8L,1,1),c(m+0x10L,4,3),c(s,4,0x80000001L),c(s+4L,1,1),
                v(s+8L,l,h),v(s+0x18L,n,q),v(d,0x0123456789ABCD00L,h),v(d+0x10L,0,15)));
    }
    private static Scene displaced() {
        long m=0x1300001000L,b=0x2400002000L,s=b+0x28L,z=b+0x50L,o=0x3500003000L,d=0x4600004000L;
        long l=0x1111222233334444L,h=0x5555666677778888L,n=0x100000011L,q=0x200000022L;
        long al=0x9999AAAABBBBCCCCL,ah=0xDDDDEEEEFFFF0001L,an=0x300000003L,aq=0x400000040L;
        return new Scene("collision_short_move_then_opaque_slot_fresh_count",
            new Input(0x6800000000L,m,o,0x80000000,d,new Scratch(0x5700005000L)),
            List.of(c(m+0x14L,4,3),c(m+8L,8,b),c(b+4L,1,1),c(d+0x18L,8,15),
                c(b+0x20L,8,15),c(s+4L,1,1),c(m+0x18L,1,6),c(m+0x10L,4,1),
                c(m+0x1CL,4,0x3F800000L),c(s,4,0xF1234567L),c(z+4L,1,0),
                v(s+8L,l,h),v(s+0x18L,n,q)),
            List.of(a(R32,m+0x14L,3),a(R64,m+8L,b),a(R8,b+4L,1),a(R64,d+0x18L,15),
                a(R64,b+0x20L,15),p(EQUAL,0xC3B9CAL,List.of(d,b+8L),0x100L,List.of()),
                a(R8,s+4L,1),a(R32,m+0x14L,3),a(R8,m+0x18L,6),a(R32,m+0x10L,1),
                a(R32,m+0x1CL,0x3F800000L),a(R8,s+4L,1),a(R32,s,0xF1234567L),a(R8,z+4L,0),
                a(W32,z,0xF1234567L),a(W8,z+4L,2),a(W64,z+8L,0),
                a(W64,z+0x18L,0),a(W64,z+0x20L,0),
                t(R128,s+8L,l,h),t(W128,z+8L,l,h),t(R128,s+0x18L,n,q),t(W128,z+0x18L,n,q),
                a(W64,s+0x18L,0),a(W64,s+0x20L,15),a(W8,s+8L,0),
                p(INSERT_SLOT,0xC3BAB8L,List.of(s,2L,-2147483648L,d),0,
                    List.of(c(m+0x10L,4,0xFFFFFFFFL),c(s,4,0x80000000L),c(s+4L,1,2),
                        v(s+8L,al,ah),v(s+0x18L,an,aq))),
                a(R32,m+0x10L,0xFFFFFFFFL),a(W32,m+0x10L,0),a(W64,o,s),a(W8,o+8L,1)),o,
            List.of(c(o,8,s),c(o+8L,1,1),c(m+0x10L,4,0),c(s,4,0x80000000L),c(s+4L,1,2),
                v(s+8L,al,ah),v(s+0x18L,an,aq),c(z,4,0xF1234567L),c(z+4L,1,2),
                v(z+8L,l,h),v(z+0x18L,n,q)));
    }
    private static Cell c(long a,int w,long l) { return new Cell(a,w,l,0); }
    private static Cell v(long a,long l,long h) { return new Cell(a,16,l,h); }
    private static Step a(Kind k,long a,long l) { return new Step(k,a,l,0,List.of(),0,List.of()); }
    private static Step t(Kind k,long a,long l,long h) { return new Step(k,a,l,h,List.of(),0,List.of()); }
    private static Step p(Kind k,long s,List<Long> args,long r,List<Cell> effects) {
        return new Step(k,s,0,0,args,r,effects);
    }
}
