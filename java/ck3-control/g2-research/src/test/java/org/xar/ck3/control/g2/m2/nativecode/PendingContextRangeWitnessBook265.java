package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextRangeWitness265Api.*;

/** Owner nonblind source-derived DATA after two model books failed; no target-produced expectations. */
public final class PendingContextRangeWitnessBook265 {
    private PendingContextRangeWitnessBook265() { }
    private static Cell c(long at,int width,long value) { return new Cell(at,width,value); }
    private static Step m(Kind kind,long at,long value) {
        return new Step(kind,at,value,List.of(),0,List.of());
    }
    private static Step k(Kind kind,long returned,List<Long> args,Cell... effects) {
        return new Step(kind,0,0,args,returned,List.of(effects));
    }
    public static List<Scene> scenes() { return List.of(empty(),noGrowth(),overflowGrowth()); }
    private static Scene empty() {
        return new Scene("equal range no memory",
            new PendingContextRangeInsertBCB7C0.Input(0x1200000000L,-1,0x1300000000L,0x1300000000L,0),
            List.of(),List.of(),List.of());
    }
    private static Scene noGrowth() {
        long r=0x100000000L,beg=0x300000000L,old=0x400000000L,fresh=0x500000000L;
        return new Scene("no growth fresh count and buffer",
            new PendingContextRangeInsertBCB7C0.Input(r,1,beg,beg+2,0x200000000L),
            List.of(c(r,8,old),c(r+8,4,8),c(r+0xC,4,3)),
            List.of(
                m(Kind.R32,r+0xC,3),m(Kind.R32,r+8,8),m(Kind.R64,r,old),
                k(Kind.COPY,0,List.of(old+3,beg,2L),c(r+0xC,4,4),c(r,8,fresh)),
                m(Kind.R32,r+0xC,4),m(Kind.R64,r,fresh),m(Kind.W32,r+0xC,6),
                k(Kind.FINALIZE,0,List.of(fresh+1,fresh+4,fresh+6))
            ),List.of(c(r,8,fresh),c(r+8,4,8),c(r+0xC,4,6)));
    }
    private static Scene overflowGrowth() {
        long r=0x600000000L,mod=0x700000000L,beg=0x800000000L;
        long old=0x900000000L,next=0xA00000000L,fresh=0xB00000000L;
        long a=0xC00000000L,vt=0xD00000000L,alloc=0xE00000000L;
        long a2=0xF00000000L,vt2=0x1000000000L,release=0x1100000000L;
        return new Scene("growth CVTT positive overflow MIN then signed CMOV",
            new PendingContextRangeInsertBCB7C0.Input(r,2,beg,beg+1,mod),
            List.of(c(r,8,old),c(r+8,4,0x60000000),c(r+0xC,4,0x60000000),c(r+0x10,8,a),
                c(mod+0x49F64F0L,4,0x3FC00000),c(a,8,vt),c(vt+8,8,alloc),c(a2,8,vt2),c(vt2+0x10,8,release)),
            List.of(
                m(Kind.R32,r+0xC,0x60000000),m(Kind.R32,r+8,0x60000000),
                m(Kind.R64,r+0x10,a),m(Kind.R32,mod+0x49F64F0L,0x3FC00000),
                m(Kind.R64,a,vt),m(Kind.R64,vt+8,alloc),
                k(Kind.ALLOCATE,next,List.of(alloc,a,0x60000001L,1L)),
                m(Kind.R64,r,old),
                k(Kind.COPY,0,List.of(next,old,2L),c(r,8,fresh),c(r+0xC,4,7),c(r+0x10,8,a2)),
                k(Kind.COPY,0,List.of(next+2,beg,1L)),
                m(Kind.R64,r,fresh),m(Kind.R32,r+0xC,7),
                k(Kind.COPY,0,List.of(next+3,fresh+2,5L)),
                m(Kind.R64,r+0x10,a2),m(Kind.R64,r,fresh),
                m(Kind.R64,a2,vt2),m(Kind.R64,vt2+0x10,release),
                k(Kind.RELEASE,0,List.of(release,a2,fresh,1L),c(r,8,old),c(r+0xC,4,99)),
                m(Kind.W64,r,next),m(Kind.W32,r+8,0x60000001),m(Kind.W32,r+0xC,0x60000001)
            ),List.of(c(r,8,next),c(r+8,4,0x60000001),c(r+0xC,4,0x60000001),c(r+0x10,8,a2)));
    }
}
