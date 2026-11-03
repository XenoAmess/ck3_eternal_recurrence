package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.ParentFixture642.*;

/** Independent source-literal full322 protocol witnesses; SOURCE-ORACLE642-04 frozen first.
 * No replay of 640, no production algorithm duplication, no Native or physical-FP claim. */
public final class ParentProtocolBoundary642 {
    private ParentProtocolBoundary642() { }
    private static final long I=IMAGE,P=SP,D=0x8000000000001100L,S=0xF000000000002200L;
    private static final long DE=0x30000L,SE=0x40000L,B16=0x50000L,B4=0x60000L;
    private static final long MARK=0x71000L,ALLOC=0x72000L,NEW=0x73000L;
    private static final long ROOT_ALLOC=0x74000L,ROOT_VT=0x75000L,ROOT_TARGET=0x76000L;
    private static final long RANGE_VT=0x77000L,RANGE_TARGET=0x78000L;
    private static final long A16=I+0x54DE260L,A4=I+0x54DE268L,VT=I+0x45648A0L;
    private static final int KIND=0x7FA54321,TAIL=0x91A2B3C4,FLAG=0xE5;
    private static final NonvolatileBits N0=initialN();
    private static final VolatileBits A=bank(0x900,0x901);
    private static final VolatileBits AV=bank(0xA00,ALLOC),CV=bank(0xB00,0xB01);

    private static VolatileBits bank(long b,long ax) {
        return new VolatileBits(ax,b+2,b+3,b+4,b+5,b+6,b+7,x(b+8),x(b+9),x(b+10),x(b+11),x(b+12),x(b+13));
    }
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,VolatileBits t) {
        return new VolatileBits(ax,cx,dx,r8,r9,t.r10Bits(),t.r11Bits(),t.xmm0(),t.xmm1(),t.xmm2(),t.xmm3(),t.xmm4(),t.xmm5());
    }
    private static NonvolatileBits n(long bx,long bp,long si,long di,long r12,long r14,long r15) {
        return new NonvolatileBits(bx,bp,si,di,r12,N0.r13Bits(),r14,r15,N0.xmm6());
    }
    private static NonvolatileBits cleanupN(int count) {
        return n(count,SE,D,N0.rdiBits(),N0.r12Bits(),N0.r14Bits(),N0.r15Bits());
    }
    private static QueueFp604Api.Normal offered(VolatileBits vv,NonvolatileBits nn,long rip,long rsp,boolean df,QueueFp604Api.Mxcsr fp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(vv,rip,rsp,nn),df),fp);
    }
    private static void normal(QueueFp604Api.Outcome out,VolatileBits vv,NonvolatileBits nn,long rip,long rsp,boolean df,QueueFp604Api.Mxcsr fp,String why) {
        check(out instanceof QueueFp604Api.Normal,why+" Normal");
        var actual=(QueueFp604Api.Normal)out;
        check(actual.base().equals(offered(vv,nn,rip,rsp,df,fp).base()),why+" complete V/N/RIP/SP/DF");
        check(actual.postMxcsr()==fp,why+" exact MXCSR object");
    }
    private static void frame(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
            boolean actualDf,QueueFp604Api.Mxcsr actualFp,int actualLength,long actualRip,
            long site,GovernmentCrtBoundary185Api.TargetKind kind,long target,int length,long pre,long rip,
            VolatileBits vv,NonvolatileBits nn,boolean df,QueueFp604Api.Mxcsr fp,String why) {
        check(call.equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,vv,nn)),why+" complete Call");
        check(child.equals(new GovernmentCrtBoundary185Api.Entry(I,pre-8,vv,nn)),why+" complete child Entry");
        check(actualLength==length&&actualRip==rip&&actualDf==df&&actualFp==fp,why+" length/RIP/DF/MXCSR");
    }
    private static void parentFrame(EmbeddedElementsFp637.CallFrame f,long site,long target,int length,boolean indirect,
            VolatileBits vv,NonvolatileBits nn,boolean df,QueueFp604Api.Mxcsr fp) {
        var o=f.original();
        frame(o.call(),o.childEntry(),o.directionFlagSet(),f.preMxcsr(),o.instructionLength(),o.returnRipBits(),
                site,indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                target,length,P-0x48,I+site+length,vv,nn,df,fp,"parent "+Long.toHexString(site));
    }
    private static void fill(Ram m,long p,int count,int salt) {
        for(int j=0;j<count;j++)m.seed(p+j,1,(salt+j*37)&255);
    }
    private static Ram seed(int count,int cap,int positive16) {
        Ram m=new Ram();
        fill(m,P-0x110,0x160,0x11);fill(m,D,0x20,0x22);fill(m,S,0x20,0x33);
        fill(m,DE,0x90,0x44);fill(m,SE,0x90,0x55);fill(m,ALLOC,0x90,0x66);fill(m,NEW,0x90,0x77);
        fill(m,MARK,0x20,0x88);fill(m,B16,0x30,0x99);fill(m,B4,0x20,0xAA);
        m.seed(P,8,RIP);m.seed(D,8,DE);m.seed(D+8,4,cap);m.seed(D+0xC,4,0);m.seed(D+0x10,8,ROOT_ALLOC);
        m.seed(S,8,SE);m.seed(S+0xC,4,count);
        m.seed(SE+8,4,KIND);m.seed(SE+0x10,8,B16);m.seed(SE+0x1C,4,positive16);
        m.seed(SE+0x28,8,B4);m.seed(SE+0x34,4,0);m.seed(SE+0x40,4,TAIL);m.seed(SE+0x44,1,FLAG);
        m.seed(ROOT_ALLOC,8,ROOT_VT);m.seed(ROOT_VT+8,8,ROOT_TARGET);
        m.seed(A16,8,RANGE_VT);m.seed(RANGE_VT+8,8,RANGE_TARGET);m.seed(I+0x49F64F0L,4,0x3F800000);
        return m;
    }
    private static void sameTraceAndRam(Ram m,List<Event> expected,Map<Long,Byte> initial,String why) {
        check(m.events.equals(expected),why+" complete source-literal event trace: expected="+expected+" actual="+m.events);
        Map<Long,Byte> ram=new HashMap<>(initial);
        for(Event e:expected) {
            int width=switch(e.kind()) {case "W64"->8;case "W32"->4;case "W8"->1;default->0;};
            for(int j=0;j<width;j++)ram.put(e.address()+j,(byte)(e.a()>>>(8*j)));
        }
        check(m.bytes.equals(ram),why+" all owned RAM bytes, untouched padding, callback effects and stack");
    }
    private static void add(List<Event> t,String k,long p,long a) {t.add(e(k,p,a));}
    /** Literal 37282B0..82F5 prefix; no target state is queried to construct it. */
    private static void start(List<Event> t,int count,int cap) {
        add(t,"W64",P+8,N0.rbxBits());add(t,"W64",P+0x10,N0.rbpBits());
        add(t,"W64",P+0x18,N0.rsiBits());add(t,"W64",P+0x20,N0.rdiBits());
        add(t,"W64",P-8,N0.r12Bits());add(t,"W64",P-0x10,N0.r14Bits());add(t,"W64",P-0x18,N0.r15Bits());
        add(t,"R32",S+0xC,count);add(t,"R64",S,SE);add(t,"W64",P-0x50,I+0x37282E6L);
        add(t,"PCALL",0x37282E1,0x889780);add(t,"W32",MARK,0x51525354);
        add(t,"R32",D+0xC,0);add(t,"R32",D+8,cap);
    }
    private static void beginElement(List<Event> t,int count,long dest) {
        add(t,"W32",D+0xC,count);add(t,"R64",D,dest);add(t,"BUDGET",0x37283B0,SE);
        add(t,"W64",P-0x50,I+0x37283BBL);add(t,"CHILD",0x37283B6,0x37297F0);
    }
    /** Fixed single empty-child172 trace. It lists every source read/write; no algorithm loop. */
    private static void emptyChild(List<Event> t,int parentCount,long dest) {
        add(t,"W64",P-0x48,parentCount);add(t,"W64",P-0x40,D);add(t,"W64",P-0x58,dest);
        add(t,"W64",dest,VT);add(t,"R32",SE+8,KIND);add(t,"W32",dest+8,KIND);
        add(t,"W64",dest+0x18,0);add(t,"W64",dest+0x20,0);add(t,"W64",dest+0x10,0);
        add(t,"W64",dest+0x18,0);add(t,"W64",dest+0x20,A16);
        add(t,"R32",SE+0x1C,0);add(t,"R64",SE+0x10,B16);
        add(t,"W64",P-0x80,I+0x372984BL);add(t,"R64",P-0x80,I+0x372984BL);
        add(t,"W64",dest+0x30,0);add(t,"W64",dest+0x38,0);add(t,"W64",dest+0x28,0);
        add(t,"W64",dest+0x30,0);add(t,"W64",dest+0x38,A4);
        add(t,"R64",SE+0x28,B4);add(t,"R32",SE+0x34,0);
        add(t,"W64",P-0x80,I+0x372987CL);add(t,"R64",P-0x80,I+0x372987CL);
        add(t,"R32",SE+0x40,TAIL);add(t,"R64",P-0x40,D);add(t,"W32",dest+0x40,TAIL);
        add(t,"R8",SE+0x44,FLAG);add(t,"R64",P-0x48,parentCount);add(t,"W8",dest+0x44,FLAG);
        add(t,"R64",P-0x58,dest);add(t,"R64",P-0x50,I+0x37283BBL);add(t,"CHILD_NR",0x37283B6,dest);
    }
    private static void parentEpilogue(List<Event> t) {
        add(t,"R64",P+8,N0.rbxBits());add(t,"R64",P+0x10,N0.rbpBits());
        add(t,"R64",P+0x18,N0.rsiBits());add(t,"R64",P+0x20,N0.rdiBits());
        add(t,"R64",P-0x18,N0.r15Bits());add(t,"R64",P-0x10,N0.r14Bits());
        add(t,"R64",P-8,N0.r12Bits());add(t,"R64",P,RIP);
    }
    private static QueueFp604Api.Outcome cleanup(Ram m,EmbeddedElementsFp637.CallFrame f,int count,
            QueueFp604Api.Mxcsr incoming,QueueFp604Api.Mxcsr outgoing,int[] seen) {
        parentFrame(f,0x37282E1,0x889780,5,false,initialV(D,S),cleanupN(count),true,incoming);
        check(++seen[0]==1,"cleanup once");m.events.add(e("PCALL",0x37282E1,0x889780));
        m.writeDword(MARK,0x51525354);
        return offered(A,cleanupN(count),I+0x37282E6L,P-0x48,false,outgoing);
    }
    private static EmbeddedElementsFp637.Calls childWrapper(Ram m,EmbeddedElementsFp637.Calls bound,
            VolatileBits before,NonvolatileBits nn,long dest,VolatileBits after,QueueFp604Api.Mxcsr fp,int[] seen) {
        return f->{
            if(f.original().call().callSiteRva()!=0x37283B6L)return bound.invoke(f);
            parentFrame(f,0x37283B6,0x37297F0,5,false,before,nn,false,fp);
            check(++seen[0]==1,"exactly first selected parent child");m.events.add(e("CHILD",0x37283B6,0x37297F0));
            QueueFp604Api.Outcome result=bound.invoke(f);
            normal(result,after,nn,I+0x37283BBL,P-0x48,false,fp,"real full172 child");
            m.events.add(e("CHILD_NR",0x37283B6,dest));return result;
        };
    }

    /** Full322 count commit and selected172 precede the actual Range16 allocator bad-NR guard. */
    public static void deepAllocatorBadNonvolatilePrefix() {
        Ram m=seed(1,1,1);Map<Long,Byte> initial=new HashMap<>(m.bytes);
        var incoming=QueueFp604Api.Mxcsr.unknown();var fp=QueueFp604Api.Mxcsr.exact(0x1F80);
        GovernmentCrtBoundary185Api.LoopBudget budget=m::step;int[] foreignSeen={0},childSeen={0},rangeSeen={0};
        Range16Fp638Api.Calls range=f->{
            var zero=new Bits128(0,0);
            var vv=new VolatileBits(RANGE_VT,A16,16,8,B16+16,A.r10Bits(),A.r11Bits(),zero,A.xmm1(),A.xmm2(),A.xmm3(),A.xmm4(),A.xmm5());
            var nn=new NonvolatileBits(B16,1,B16+16,DE+0x10,N0.r12Bits(),1,0,1,N0.xmm6());
            frame(f.call(),f.childEntry(),f.directionFlagSet(),f.preMxcsr(),f.instructionLength(),f.returnRipBits(),
                    0x8C7131,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,RANGE_TARGET,3,P-0xC8,I+0x8C7134L,vv,nn,false,fp,"deep real638 allocator");
            check(++rangeSeen[0]==1,"allocator once");m.events.add(e("RCALL",0x8C7131,RANGE_TARGET));
            m.writeDword(MARK+4,0x61626364);
            var bad=new NonvolatileBits(nn.rbxBits(),nn.rbpBits(),nn.rsiBits(),nn.rdiBits(),nn.r12Bits(),2,nn.r14Bits(),nn.r15Bits(),nn.xmm6());
            return offered(bank(0xC00,0xC01),bad,I+0x8C7134L,P-0xC8,true,QueueFp604Api.Mxcsr.unknown());
        };
        Add4Fp639Api.Calls add=f->{throw new AssertionError("no Add4 lower CALL after bad NR");};
        EmbeddedElementsFp637.Calls foreign=f->{
            if(f.original().call().callSiteRva()!=0x37282E1L)throw new AssertionError("unexpected parent foreign");
            return cleanup(m,f,1,incoming,fp,foreignSeen);
        };
        var bound=EmbeddedElementsKnownLower642.bind(m,budget,range,add,foreign);
        var nn=n(1,SE,D,DE,N0.r12Bits(),N0.r14Bits(),N0.r15Bits());
        var wrapped=childWrapper(m,bound,v(0,DE,SE,A.r8Bits(),A.r9Bits(),A),nn,DE,v(DE,DE+0x28,0,B4,B4,A),fp,childSeen);
        boolean rejected=false;
        try {EmbeddedElementsFp637.execute(input(D,S,true,incoming,budget),m,wrapped);}
        catch(IllegalArgumentException failure) {rejected=true;check("Nonvolatile mismatch".equals(failure.getMessage()),"exact original NR guard");}
        check(rejected&&foreignSeen[0]==1&&childSeen[0]==1&&rangeSeen[0]==1,"deep badNR rejected after once-only fullparent/callee prefix");
        List<Event> t=new ArrayList<>();start(t,1,1);beginElement(t,1,DE);
        add(t,"W64",P-0x48,1);add(t,"W64",P-0x40,D);add(t,"W64",P-0x58,DE);
        add(t,"W64",DE,VT);add(t,"R32",SE+8,KIND);add(t,"W32",DE+8,KIND);
        add(t,"W64",DE+0x18,0);add(t,"W64",DE+0x20,0);add(t,"W64",DE+0x10,0);
        add(t,"W64",DE+0x18,0);add(t,"W64",DE+0x20,A16);add(t,"R32",SE+0x1C,1);add(t,"R64",SE+0x10,B16);
        add(t,"W64",P-0x80,I+0x372984BL);
        add(t,"W64",P-0x88,SE);add(t,"W64",P-0x90,0);add(t,"W64",P-0x98,DE);add(t,"W64",P-0xA0,N0.r14Bits());
        add(t,"R32",DE+0x1C,0);add(t,"W64",P-0x78,SE);add(t,"R32",DE+0x18,0);add(t,"W64",P-0xA8,N0.r15Bits());
        add(t,"R64",DE+0x20,A16);add(t,"W64",P-0x70,N0.r12Bits());add(t,"W64",P-0x68,N0.r13Bits());
        add(t,"R32",I+0x49F64F0L,0x3F800000);add(t,"R64",A16,RANGE_VT);add(t,"R64",RANGE_VT+8,RANGE_TARGET);
        add(t,"W64",P-0xD0,I+0x8C7134L);add(t,"RCALL",0x8C7131,RANGE_TARGET);add(t,"W32",MARK+4,0x61626364);
        sameTraceAndRam(m,t,initial,"deep badNR");
    }

    /** New wholeparent two-element path: first complete172 effects precede the second parent budget stop. */
    public static void secondParentBudgetExactException() {
        Ram m=seed(2,2,0);Map<Long,Byte> initial=new HashMap<>(m.bytes);
        var incoming=QueueFp604Api.Mxcsr.unknown();var fp=QueueFp604Api.Mxcsr.exact(0x1F80);
        RuntimeException sentinel=new UnsupportedOperationException("owned second-parent budget sentinel");
        GovernmentCrtBoundary185Api.LoopBudget budget=(pc,cursor)->{
            m.events.add(e("BUDGET",pc,cursor));if(pc==0x37283B0L&&cursor==SE+0x48)throw sentinel;
        };
        int[] foreignSeen={0},childSeen={0};
        Range16Fp638Api.Calls range=f->{throw new AssertionError("real empty Range16 must have no lower CALL");};
        Add4Fp639Api.Calls add=f->{throw new AssertionError("real empty Add4 must have no lower CALL");};
        EmbeddedElementsFp637.Calls foreign=f->{
            if(f.original().call().callSiteRva()!=0x37282E1L)throw new AssertionError("unexpected parent foreign");
            return cleanup(m,f,2,incoming,fp,foreignSeen);
        };
        var bound=EmbeddedElementsKnownLower642.bind(m,budget,range,add,foreign);
        var nn=n(2,SE,D,DE,N0.r12Bits(),N0.r14Bits(),N0.r15Bits());
        var wrapped=childWrapper(m,bound,v(0,DE,SE,A.r8Bits(),A.r9Bits(),A),nn,DE,v(DE,DE+0x28,0,B4,B4,A),fp,childSeen);
        RuntimeException caught=null;
        try {EmbeddedElementsFp637.execute(input(D,S,true,incoming,budget),m,wrapped);}catch(RuntimeException failure){caught=failure;}
        check(caught==sentinel,"same arbitrary exception object crosses 637/642 with no substitute");
        check(foreignSeen[0]==1&&childSeen[0]==1,"only first child and cleanup reached");
        List<Event> t=new ArrayList<>();start(t,2,2);beginElement(t,2,DE);emptyChild(t,2,DE);
        add(t,"BUDGET",0x37283B0,SE+0x48);
        sameTraceAndRam(m,t,initial,"second parent budget");
    }

    /** Full parent allocator and commit offer different bases; only the fresh post-commit root base is used. */
    public static void allocatorCommitFreshBaseNormal() {
        Ram m=seed(1,0,0);Map<Long,Byte> initial=new HashMap<>(m.bytes);
        var incoming=QueueFp604Api.Mxcsr.unknown();var fp=QueueFp604Api.Mxcsr.exact(0x1F80);
        var allocFp=new QueueFp604Api.Mxcsr(0x1000,0x1000);var finalFp=new QueueFp604Api.Mxcsr(0x2000,0x2000);
        GovernmentCrtBoundary185Api.LoopBudget budget=m::step;
        int[] foreignSeen={0},childSeen={0},allocSeen={0},commitSeen={0};
        Range16Fp638Api.Calls range=f->{throw new AssertionError("real empty Range16 must have no lower CALL");};
        Add4Fp639Api.Calls add=f->{throw new AssertionError("real empty Add4 must have no lower CALL");};
        EmbeddedElementsFp637.Calls foreign=f->{
            long site=f.original().call().callSiteRva();
            if(site==0x37282E1L)return cleanup(m,f,1,incoming,fp,foreignSeen);
            if(site==0x3728316L) {
                parentFrame(f,site,ROOT_TARGET,3,true,v(1,ROOT_ALLOC,72,8,ROOT_TARGET,A),cleanupN(1),false,fp);
                check(++allocSeen[0]==1,"parent allocator once");m.events.add(e("PCALL",site,ROOT_TARGET));m.writeDword(MARK+8,0x71727374);
                return offered(AV,cleanupN(1),I+0x3728319L,P-0x48,true,allocFp);
            }
            if(site==0x372836CL) {
                var nn=n(1,SE,D,N0.rdiBits(),ALLOC,0,DE);
                parentFrame(f,site,0xDBDB80,5,false,v(ALLOC,D,ALLOC,0,1,AV),nn,true,allocFp);
                check(++commitSeen[0]==1,"parent commit once");m.events.add(e("PCALL",site,0xDBDB80));
                m.writeQword(D,NEW);m.writeDword(D+8,1);m.writeDword(MARK+12,0x21222324);
                return offered(CV,nn,I+0x3728371L,P-0x48,false,finalFp);
            }
            throw new AssertionError("unexpected parent port "+Long.toHexString(site));
        };
        var bound=EmbeddedElementsKnownLower642.bind(m,budget,range,add,foreign);
        var nn=n(1,SE,D,NEW,ALLOC,0,DE);
        var wrapped=childWrapper(m,bound,v(CV.raxBits(),NEW,SE,CV.r8Bits(),CV.r9Bits(),CV),nn,NEW,v(NEW,NEW+0x28,0,B4,B4,CV),finalFp,childSeen);
        var out=EmbeddedElementsFp637.execute(input(D,S,true,incoming,budget),m,wrapped);
        normal(out,v(D,NEW+0x28,0,B4,B4,CV),N0,RIP,P+8,false,finalFp,"root normal after fresh base");
        check(foreignSeen[0]==1&&allocSeen[0]==1&&commitSeen[0]==1&&childSeen[0]==1,"all actual parent ports once");
        List<Event> t=new ArrayList<>();start(t,1,0);
        add(t,"R64",D+0x10,ROOT_ALLOC);add(t,"R64",ROOT_ALLOC,ROOT_VT);add(t,"R64",ROOT_VT+8,ROOT_TARGET);
        add(t,"W64",P-0x50,I+0x3728319L);add(t,"PCALL",0x3728316,ROOT_TARGET);add(t,"W32",MARK+8,0x71727374);
        add(t,"R32",D+0xC,0);add(t,"R64",D,DE);add(t,"W64",P-0x50,I+0x3728371L);
        add(t,"PCALL",0x372836C,0xDBDB80);add(t,"W64",D,NEW);add(t,"W32",D+8,1);add(t,"W32",MARK+12,0x21222324);
        beginElement(t,1,NEW);emptyChild(t,1,NEW);parentEpilogue(t);
        sameTraceAndRam(m,t,initial,"allocator fresh base normal");
    }
    public static int verify() {
        deepAllocatorBadNonvolatilePrefix();secondParentBudgetExactException();allocatorCommitFreshBaseNormal();return 3;
    }
    public static void main(String[] args) {System.out.println(verify());}
}
