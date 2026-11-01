package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import java.util.ArrayList;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsData578.*;

/** Independent original-ASM literal fixture, no target algorithm or captured target result. */
public final class EmbeddedElementsBook578 {
    private EmbeddedElementsBook578() { }
    public static void main(String[] args) { System.out.println(verify()); }
    public static int verify() {
        EmbeddedElementsHost578.verify(selfScene());
        EmbeddedElementsHost578.verify(growthScene());
        EmbeddedElementsHost578.verify(shrinkScene());
        EmbeddedElementsHost578.verify(shrinkStopScene());
        return 4;
    }
    private static VolatileBits vb(long seed,long... overrides) {
        long[] a={seed,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6};
        if((overrides.length&1)!=0) throw new AssertionError();
        for(int i=0;i<overrides.length;i+=2) a[Math.toIntExact(overrides[i])]=overrides[i+1];
        VolatileBits x=v(seed);
        return new VolatileBits(a[0],a[1],a[2],a[3],a[4],a[5],a[6],x.xmm0(),x.xmm1(),x.xmm2(),x.xmm3(),x.xmm4(),x.xmm5());
    }
    private static NonvolatileBits nb(long a,long b,long c,long d,long e,long f,long g,long h) {
        return new NonvolatileBits(a,b,c,d,e,f,g,h,n(0x900).xmm6());
    }
    private static GovernmentCrtBoundary185Api.Entry entry(boolean self) {
        return new GovernmentCrtBoundary185Api.Entry(0x140000000L,0x8008L,
            vb(0x10L,1,0x1000L,2,self?0x1000L:0x2000L),n(0x900));
    }
    private static void invoke(List<Step> steps,long site,long target,int length,boolean indirect,
            VolatileBits before,NonvolatileBits current,boolean beforeDf,VolatileBits after,
            boolean afterDf,List<Cell> effects) {
        long rip=0x140000000L+site+length;
        steps.add(new Write(8,0x7FB8L,rip));
        GovernmentCrtBoundary185Api.Call call=new GovernmentCrtBoundary185Api.Call(site,
            indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            target,0x7FC0L,before,current);
        EmbeddedElements578Api.CallFrame frame=new EmbeddedElements578Api.CallFrame(call,
            new GovernmentCrtBoundary185Api.Entry(0x140000000L,0x7FB8L,before,current),beforeDf,length,rip);
        FullCopy437Api.CallResult post=new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(after,rip,0x7FC0L,current),afterDf);
        steps.add(new Invoke(frame,post,effects));
        for(Cell c:effects) steps.add(new Write(c.widthBytes(),c.addressBits(),c.valueBits()));
    }
    private static Scene selfScene() {
        List<Step> s=new ArrayList<>();
        s.add(new Write(8,0x8010L,0x900L));
        s.add(new Write(8,0x8018L,0x901L));
        s.add(new Write(8,0x8020L,0x902L));
        s.add(new Write(8,0x8028L,0x903L));
        s.add(new Write(8,0x8000L,0x904L));
        s.add(new Write(8,0x7FF8L,0x906L));
        s.add(new Write(8,0x7FF0L,0x907L));
        s.add(new Read(8,0x8010L,0x900L));
        s.add(new Read(8,0x8018L,0x901L));
        s.add(new Read(8,0x8020L,0x902L));
        s.add(new Read(8,0x8028L,0x903L));
        s.add(new Read(8,0x7FF0L,0x907L));
        s.add(new Read(8,0x7FF8L,0x906L));
        s.add(new Read(8,0x8000L,0x904L));
        s.add(new Read(8,0x8008L,0x1122334455667788L));
        return new Scene("SELF",entry(true),true,List.of(new Cell(8,0x8008L,0x1122334455667788L)),s,new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(vb(0x10L,0,0x1000L,1,0x1000L,2,0x1000L),0x1122334455667788L,0x8010L,nb(0x900L,0x901L,0x902L,0x903L,0x904L,0x905L,0x906L,0x907L)),true),false,List.of(new Cell(8,0x7FF0L,0x907L),new Cell(8,0x7FF8L,0x906L),new Cell(8,0x8000L,0x904L),new Cell(8,0x8008L,0x1122334455667788L),new Cell(8,0x8010L,0x900L),new Cell(8,0x8018L,0x901L),new Cell(8,0x8020L,0x902L),new Cell(8,0x8028L,0x903L)));
    }
    private static Scene growthScene() {
        List<Step> s=new ArrayList<>();
        s.add(new Write(8,0x8010L,0x900L));
        s.add(new Write(8,0x8018L,0x901L));
        s.add(new Write(8,0x8020L,0x902L));
        s.add(new Write(8,0x8028L,0x903L));
        s.add(new Write(8,0x8000L,0x904L));
        s.add(new Write(8,0x7FF8L,0x906L));
        s.add(new Write(8,0x7FF0L,0x907L));
        s.add(new Read(4,0x200CL,0x2L));
        s.add(new Read(8,0x2000L,0x4000L));
        invoke(s,0x37282E1L,0x889780L,5,false,vb(0x10L,1,0x1000L,2,0x2000L),nb(0x2L,0x4000L,0x1000L,0x903L,0x904L,0x905L,0x906L,0x907L),true,vb(0x100L),false,List.of(new Cell(8,0x2000L,0xDEAD0000L),new Cell(4,0x200CL,0x9L)));
        s.add(new Read(4,0x100CL,0x0L));
        s.add(new Read(4,0x1008L,0x0L));
        s.add(new Read(8,0x1010L,0x6000L));
        s.add(new Read(8,0x6000L,0x7000L));
        s.add(new Read(8,0x7008L,0xA000L));
        invoke(s,0x3728316L,0xA000L,3,true,vb(0x100L,0,0x2L,1,0x6000L,2,0x90L,3,0x8L,4,0xA000L),nb(0x2L,0x4000L,0x1000L,0x903L,0x904L,0x905L,0x906L,0x907L),false,vb(0x200L,0,0x5000L),true,List.of(new Cell(4,0x100CL,0x1L),new Cell(8,0x1000L,0x3080L)));
        s.add(new Read(4,0x100CL,0x1L));
        s.add(new Read(8,0x1000L,0x3080L));
        s.add(new Write(8,0x7FE0L,0x5000L));
        s.add(new Write(8,0x7FE8L,0x5000L));
        s.add(new Budget(0x3728335L,0x3080L,false));
        invoke(s,0x372833BL,0x37295B0L,5,false,vb(0x200L,0,0x5000L,1,0x5000L,2,0x3080L),nb(0x2L,0x4000L,0x1000L,0x5000L,0x5000L,0x905L,0x1L,0x3080L),true,vb(0x300L),false,List.of(new Cell(4,0x100CL,0x3L)));
        s.add(new Write(8,0x7FE8L,0x5048L));
        s.add(new Read(4,0x100CL,0x3L));
        invoke(s,0x372836CL,0xDBDB80L,5,false,vb(0x300L,1,0x1000L,2,0x5000L,3,0x3L,4,0x2L),nb(0x2L,0x4000L,0x1000L,0x5048L,0x5000L,0x905L,0x3L,0x30C8L),false,vb(0x400L),true,List.of(new Cell(8,0x1000L,0x5000L)));
        s.add(new Write(4,0x100CL,0x2L));
        s.add(new Read(8,0x1000L,0x5000L));
        s.add(new Budget(0x37283B0L,0x4000L,false));
        invoke(s,0x37283B6L,0x37297F0L,5,false,vb(0x400L,1,0x5000L,2,0x4000L),nb(0x2L,0x4000L,0x1000L,0x5000L,0x5000L,0x905L,0x3L,0x30C8L),true,vb(0x500L),true,List.of());
        s.add(new Budget(0x37283B0L,0x4048L,false));
        invoke(s,0x37283B6L,0x37297F0L,5,false,vb(0x500L,1,0x5048L,2,0x4048L),nb(0x1L,0x4048L,0x1000L,0x5048L,0x5000L,0x905L,0x3L,0x30C8L),true,vb(0x600L),false,List.of(new Cell(8,0x8010L,0x123456789ABCDEF0L),new Cell(8,0x8020L,0xFEDCBA9876543210L),new Cell(8,0x8008L,0x8877665544332211L)));
        s.add(new Read(8,0x8010L,0x123456789ABCDEF0L));
        s.add(new Read(8,0x8018L,0x901L));
        s.add(new Read(8,0x8020L,0xFEDCBA9876543210L));
        s.add(new Read(8,0x8028L,0x903L));
        s.add(new Read(8,0x7FF0L,0x907L));
        s.add(new Read(8,0x7FF8L,0x906L));
        s.add(new Read(8,0x8000L,0x904L));
        s.add(new Read(8,0x8008L,0x8877665544332211L));
        return new Scene("GROW",entry(false),true,List.of(new Cell(8,0x8008L,0x1122334455667788L),new Cell(8,0x2000L,0x4000L),new Cell(4,0x200CL,0x2L),new Cell(8,0x1000L,0x3000L),new Cell(4,0x1008L,0x0L),new Cell(4,0x100CL,0x0L),new Cell(8,0x1010L,0x6000L),new Cell(8,0x6000L,0x7000L),new Cell(8,0x7008L,0xA000L)),s,new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(vb(0x600L,0,0x1000L),0x8877665544332211L,0x8010L,nb(0x123456789ABCDEF0L,0x901L,0xFEDCBA9876543210L,0x903L,0x904L,0x905L,0x906L,0x907L)),false),false,List.of(new Cell(8,0x1000L,0x5000L),new Cell(4,0x1008L,0x0L),new Cell(4,0x100CL,0x2L),new Cell(8,0x1010L,0x6000L),new Cell(8,0x2000L,0xDEAD0000L),new Cell(4,0x200CL,0x9L),new Cell(8,0x6000L,0x7000L),new Cell(8,0x7008L,0xA000L),new Cell(8,0x7FB8L,0x1437283BBL),new Cell(8,0x7FE0L,0x5000L),new Cell(8,0x7FE8L,0x5048L),new Cell(8,0x7FF0L,0x907L),new Cell(8,0x7FF8L,0x906L),new Cell(8,0x8000L,0x904L),new Cell(8,0x8008L,0x8877665544332211L),new Cell(8,0x8010L,0x123456789ABCDEF0L),new Cell(8,0x8018L,0x901L),new Cell(8,0x8020L,0xFEDCBA9876543210L),new Cell(8,0x8028L,0x903L)));
    }
    private static Scene shrinkScene() {
        List<Step> s=new ArrayList<>();
        s.add(new Write(8,0x8010L,0x900L));
        s.add(new Write(8,0x8018L,0x901L));
        s.add(new Write(8,0x8020L,0x902L));
        s.add(new Write(8,0x8028L,0x903L));
        s.add(new Write(8,0x8000L,0x904L));
        s.add(new Write(8,0x7FF8L,0x906L));
        s.add(new Write(8,0x7FF0L,0x907L));
        s.add(new Read(4,0x200CL,0x0L));
        s.add(new Read(8,0x2000L,0x4000L));
        invoke(s,0x37282E1L,0x889780L,5,false,vb(0x10L,1,0x1000L,2,0x2000L),nb(0x0L,0x4000L,0x1000L,0x903L,0x904L,0x905L,0x906L,0x907L),true,vb(0x710L),false,List.of(new Cell(8,0x3000L,0x9000L)));
        s.add(new Read(4,0x100CL,0x1L));
        s.add(new Read(8,0x1000L,0x3000L));
        s.add(new Budget(0x3728390L,0x3000L,false));
        s.add(new Read(8,0x3000L,0x9000L));
        s.add(new Read(8,0x9000L,0xB000L));
        invoke(s,0x3728398L,0xB000L,2,true,vb(0x710L,0,0x9000L,1,0x3000L,2,0x0L),nb(0x0L,0x4000L,0x1000L,0x3000L,0x904L,0x905L,0x3048L,0x907L),false,vb(0x720L),true,List.of(new Cell(8,0x8000L,0xABCDEF0011223344L),new Cell(8,0x8008L,0x8877665544332211L)));
        s.add(new Write(4,0x100CL,0x0L));
        s.add(new Read(8,0x8010L,0x900L));
        s.add(new Read(8,0x8018L,0x901L));
        s.add(new Read(8,0x8020L,0x902L));
        s.add(new Read(8,0x8028L,0x903L));
        s.add(new Read(8,0x7FF0L,0x907L));
        s.add(new Read(8,0x7FF8L,0x906L));
        s.add(new Read(8,0x8000L,0xABCDEF0011223344L));
        s.add(new Read(8,0x8008L,0x8877665544332211L));
        return new Scene("SHRINK",entry(false),true,List.of(new Cell(8,0x8008L,0x1122334455667788L),new Cell(8,0x2000L,0x4000L),new Cell(4,0x200CL,0x0L),new Cell(8,0x1000L,0x3000L),new Cell(4,0x100CL,0x1L),new Cell(8,0x3000L,0x9100L),new Cell(8,0x9000L,0xB000L)),s,new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(vb(0x720L,0,0x1000L),0x8877665544332211L,0x8010L,nb(0x900L,0x901L,0x902L,0x903L,0xABCDEF0011223344L,0x905L,0x906L,0x907L)),true),false,List.of(new Cell(8,0x1000L,0x3000L),new Cell(4,0x100CL,0x0L),new Cell(8,0x2000L,0x4000L),new Cell(4,0x200CL,0x0L),new Cell(8,0x3000L,0x9000L),new Cell(8,0x7FB8L,0x14372839AL),new Cell(8,0x7FF0L,0x907L),new Cell(8,0x7FF8L,0x906L),new Cell(8,0x8000L,0xABCDEF0011223344L),new Cell(8,0x8008L,0x8877665544332211L),new Cell(8,0x8010L,0x900L),new Cell(8,0x8018L,0x901L),new Cell(8,0x8020L,0x902L),new Cell(8,0x8028L,0x903L),new Cell(8,0x9000L,0xB000L)));
    }
    private static Scene shrinkStopScene() {
        List<Step> s=new ArrayList<>();
        s.add(new Write(8,0x8010L,0x900L));
        s.add(new Write(8,0x8018L,0x901L));
        s.add(new Write(8,0x8020L,0x902L));
        s.add(new Write(8,0x8028L,0x903L));
        s.add(new Write(8,0x8000L,0x904L));
        s.add(new Write(8,0x7FF8L,0x906L));
        s.add(new Write(8,0x7FF0L,0x907L));
        s.add(new Read(4,0x200CL,0x0L));
        s.add(new Read(8,0x2000L,0x4000L));
        invoke(s,0x37282E1L,0x889780L,5,false,vb(0x10L,1,0x1000L,2,0x2000L),nb(0x0L,0x4000L,0x1000L,0x903L,0x904L,0x905L,0x906L,0x907L),true,vb(0x710L),false,List.of(new Cell(8,0x3000L,0x9000L)));
        s.add(new Read(4,0x100CL,0x1L));
        s.add(new Read(8,0x1000L,0x3000L));
        s.add(new Budget(0x3728390L,0x3000L,true));
        return new Scene("SHRINK_STOP",entry(false),true,List.of(new Cell(8,0x8008L,0x1122334455667788L),new Cell(8,0x2000L,0x4000L),new Cell(4,0x200CL,0x0L),new Cell(8,0x1000L,0x3000L),new Cell(4,0x100CL,0x1L),new Cell(8,0x3000L,0x9100L),new Cell(8,0x9000L,0xB000L)),s,null,true,List.of(new Cell(8,0x1000L,0x3000L),new Cell(4,0x100CL,0x1L),new Cell(8,0x2000L,0x4000L),new Cell(4,0x200CL,0x0L),new Cell(8,0x3000L,0x9000L),new Cell(8,0x7FB8L,0x1437282E6L),new Cell(8,0x7FF0L,0x907L),new Cell(8,0x7FF8L,0x906L),new Cell(8,0x8000L,0x904L),new Cell(8,0x8008L,0x1122334455667788L),new Cell(8,0x8010L,0x900L),new Cell(8,0x8018L,0x901L),new Cell(8,0x8020L,0x902L),new Cell(8,0x8028L,0x903L),new Cell(8,0x9000L,0xB000L)));
    }
}
