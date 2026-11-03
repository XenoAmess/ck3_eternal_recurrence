package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.copy437259.Add4Copy259;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner new full322-parent literal fixtures, frozen after SOURCE-LITERAL-ORACLE642.json.
 * Real637/640/636/638/639 and M3 COPY259/613/614 execute in two new parent contexts.
 * No old verify/case is invoked; expected trace and all RAM derive from held source, never a target run.
 * Allocator/release/cleanup/unknown-tail post states are explicit owned offers, not native evidence. */
public final class ParentRamBoundary642 {
    private ParentRamBoundary642() { }
    private static final long I=0x140000000L,R=0x70001008L,P=R-0x50,D=0x8000000000001100L,S=0xf000000000002200L;
    private static final long ROOT_D=0x8000000000011000L,ROOT_S=0xf000000000022000L,CHILD_RIP=I+0x37283bb;
    private static final long B16=0x4000,B4=0x5000,NEW16=0x9000,NEW4=0xa000,T16=0xb000,T4=0xc000;
    private static final long A16=I+0x54de260,A4=I+0x54de268,H16=D+0x10,H4=D+0x28,L=P-0x78,C=P-0x80;
    private static final long TARGET16A=0x800000000000c001L,TARGET16F=0xf00000000000c002L,TARGET4A=0x800000000000c003L,TARGET4F=0xf00000000000c004L;
    private static final long RIP=I+0x123456,JT=I+0x6090000,UNKNOWN=0x12345678L,PAYLOAD=0x1122334455667788L,MARK=0x7770;
    private static final Bits128 WORD0=new Bits128(0x0102030405060708L,0x1112131415161718L),WORD1=new Bits128(0x2122232425262728L,0x3132333435363738L);
    private static final QueueFp604Api.Mxcsr F0=QueueFp604Api.Mxcsr.exact(0x1f80),F1=QueueFp604Api.Mxcsr.exact(0x1fa0),F2=QueueFp604Api.Mxcsr.exact(0x1f81),F3=QueueFp604Api.Mxcsr.exact(0x3f80),F4=new QueueFp604Api.Mxcsr(8,12);
    private record Event(String k,long a,long v,long hi) { }
    private static void ev(List<Event> z,String k,long a,long v) {z.add(new Event(k,a,v,0));}
    private static void wide(List<Event> z,String k,long a,Bits128 x) {z.add(new Event(k,a,x.lowBits(),x.highBits()));}
    private static void same(boolean ok,String why) {if(!ok)throw new AssertionError(why);}
    private static Bits128 x(long n) {return new Bits128(n,~n);}
    private static VolatileBits bank(long b,long ax,long cx,long dx,long r8,long r9) {return new VolatileBits(ax,cx,dx,r8,r9,b+10,b+11,x(b),x(b+1),x(b+2),x(b+3),x(b+4),x(b+5));}
    private static VolatileBits rootV() {return bank(0x1000,0x111,ROOT_D,ROOT_S,0x114,0x115);}
    private static VolatileBits cleanupV() {return bank(0x1000,0x771,0x772,0x773,0x114,0x115);}
    private static VolatileBits v0() {return bank(0x1000,0,D,S,0x114,0x115);}
    private static VolatileBits offered(int j,long ax) {long b=0x2000+j*0x1000;return bank(b,ax,b+2,b+3,b+4,b+5);}
    private static VolatileBits v(VolatileBits b,long ax,long cx,long dx,long r8,long r9,long r10,Bits128 x0) {return new VolatileBits(ax,cx,dx,r8,r9,r10,b.r11Bits(),x0,b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());}
    private static NonvolatileBits rootN() {return new NonvolatileBits(0x101,0x102,0x103,0x104,0x105,0x106,0x107,0x108,x(0x109));}
    private static NonvolatileBits cleanupN() {var n=rootN();return new NonvolatileBits(1,S,ROOT_D,n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static NonvolatileBits n0() {var n=rootN();return new NonvolatileBits(1,S,ROOT_D,D,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static NonvolatileBits rangeN(boolean allocated) {var n=n0();return new NonvolatileBits(allocated?B16+32:B16,2,B16+32,H16,allocated?NEW16:n.r12Bits(),2,0,2,n.xmm6());}
    private static NonvolatileBits addN(boolean allocated,long dest) {var n=n0();return new NonvolatileBits(0,3,allocated?dest:0,allocated?0:D,3,B4,H4,12,n.xmm6());}
    private static final class Ram implements EmbeddedElementsKnownLower642.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<Event> events=new ArrayList<>();
        void seed(long p,int w,long value) {for(int j=0;j<w;j++)bytes.put(p+j,(byte)(value>>>(8*j)));}
        long peek(long p,int w) {long value=0;for(int j=0;j<w;j++)value|=(bytes.getOrDefault(p+j,(byte)0)&255L)<<(8*j);return value;}
        @Override public int readDword(long p) {int a=(int)peek(p,4);ev(events,"R32",p,a);return a;}
        @Override public long readQword(long p) {long a=peek(p,8);ev(events,"R64",p,a);return a;}
        @Override public int readUnsignedByte(long p) {int a=(int)peek(p,1);ev(events,"R8",p,a);return a;}
        @Override public void writeDword(long p,int a) {ev(events,"W32",p,a);seed(p,4,a);}
        @Override public void writeQword(long p,long a) {ev(events,"W64",p,a);seed(p,8,a);}
        @Override public void writeByte(long p,int a) {ev(events,"W8",p,a&255);seed(p,1,a);}
        @Override public Bits128 read128(long p) {Bits128 a=new Bits128(peek(p,8),peek(p+8,8));wide(events,"R128",p,a);return a;}
        @Override public void write128(long p,Bits128 a) {wide(events,"W128",p,a);seed(p,8,a.lowBits());seed(p+8,8,a.highBits());}
        @Override public int lockedXaddDword(long p,int a) {throw new AssertionError("unexpected atomic");}
        @Override public void writeWord(long p,int a) {throw new AssertionError("unexpected word");}
        @Override public int readUnsignedWord(long p) {throw new AssertionError("unexpected word read");}
        @Override public void write128NonTemporal(long p,Bits128 a) {throw new AssertionError("unexpected NT128");}
        @Override public FullCopy437Api.Bits256 read256(long p) {throw new AssertionError("unexpected R256");}
        @Override public void write256(long p,FullCopy437Api.Bits256 a) {throw new AssertionError("unexpected W256");}
        @Override public void write256NonTemporal(long p,FullCopy437Api.Bits256 a) {throw new AssertionError("unexpected NT256");}
        @Override public void sfence() {throw new AssertionError("unexpected fence");}
    }
    private static Ram initial(int mode) {
        Ram m=new Ram();m.seed(R,8,RIP);for(int i=0;i<0x48;i++)m.seed(D+i,1,0xcc);
        m.seed(ROOT_D,8,D);m.seed(ROOT_D+8,4,1);m.seed(ROOT_D+12,4,0);
        m.seed(ROOT_S,8,S);m.seed(ROOT_S+12,4,1);
        m.seed(S+8,4,0x76543210);m.seed(S+0x10,8,B16);m.seed(S+0x1c,4,2);m.seed(S+0x28,8,B4);m.seed(S+0x34,4,3);m.seed(S+0x40,4,0x55667788);m.seed(S+0x44,1,0x99);
        m.seed(B16,8,WORD0.lowBits());m.seed(B16+8,8,WORD0.highBits());m.seed(B16+16,8,WORD1.lowBits());m.seed(B16+24,8,WORD1.highBits());m.seed(B4,8,PAYLOAD);m.seed(B4+8,4,UNKNOWN);
        m.seed(A16,8,T16);m.seed(A4,8,T4);m.seed(T16+8,8,TARGET16A);m.seed(T16+16,8,TARGET16F);m.seed(T4+8,8,TARGET4A);m.seed(T4+16,8,TARGET4F);
        m.seed(I+0x49f64f0,4,0x3fc00000);m.seed(JT,4,0x422688e);m.seed(JT+12*4,4,0x4226943);m.seed(MARK,1,0xcc);
        same(mode==0||mode==1,"only two new parent contexts");return m;
    }
    private static void checkFrame(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,long site,long target,int len,long pre,VolatileBits vv,NonvolatileBits nn,boolean df,QueueFp604Api.Mxcsr fp,boolean actualDf,QueueFp604Api.Mxcsr actualFp,long rip,int actualLen) {
        var kind=len==3?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
        same(call.equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,vv,nn)),"complete CALL state at "+Long.toHexString(site));
        same(child.equals(new GovernmentCrtBoundary185Api.Entry(I,pre-8,vv,nn)),"complete child state");
        same(actualDf==df&&actualFp==fp&&rip==I+site+len&&actualLen==len,"DF/MXCSR identity/SP/actual return metadata");
    }
    private static QueueFp604Api.Normal normal(long rip,VolatileBits vv,NonvolatileBits nn,boolean df,QueueFp604Api.Mxcsr fp,long error) {return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(vv,rip+error,L,nn),df),fp);}
    private static void compare(Ram m,Ram want,List<Event> expected) {
        for(Event e:expected)switch(e.k()) {case "W64"->want.seed(e.a(),8,e.v());case "W32"->want.seed(e.a(),4,e.v());case "W8"->want.seed(e.a(),1,e.v());case "W128"->{want.seed(e.a(),8,e.v());want.seed(e.a()+8,8,e.hi());}default->{}}
        if(!m.events.equals(expected)){int j=0;while(j<m.events.size()&&j<expected.size()&&m.events.get(j).equals(expected.get(j)))j++;throw new AssertionError("642 new parent cursor "+j+" actual="+(j<m.events.size()?m.events.get(j):"END")+" expected="+(j<expected.size()?expected.get(j):"END"));}
        same(m.bytes.equals(want.bytes),"entire RAM equality including callstack and committed prefix");
    }
    private static void fixture(int mode) {
        long dest=mode==1?JT-8:NEW4;Ram m=initial(mode),want=initial(mode);int[] rc={0},ac={0},pc={0},fc={0},tail={0};QueueFp604Api.Stopped[] stopped={null};QueueFp604Api.Outcome[] parent172={null},addStopped={null};
        var budget=(GovernmentCrtBoundary185Api.LoopBudget)(stepPc,cursor)->{same(stepPc==0x8c7170||stepPc==0x37283b0,"only actual parent/Range insertion budgets");ev(m.events,"BUDGET",stepPc,cursor);};
        Range16Fp638Api.Calls range=f->{int j=rc[0]++;same(j<2,"two Range calls");long site=j==0?0x8c7131:0x8c71d7,target=j==0?TARGET16A:TARGET16F;
            VolatileBits vv=j==0?v(v0(),T16,A16,32,8,B16+32,v0().r10Bits(),new Bits128(0,0)):v(offered(1,NEW16),T16,A16,0,8,0,0,WORD1);
            checkFrame(f.call(),f.childEntry(),site,target,3,L,vv,rangeN(j==1),j==0,trueFP(j),f.directionFlagSet(),f.preMxcsr(),f.returnRipBits(),f.instructionLength());
            ev(m.events,"CALL",site,target);m.writeByte(MARK,j==0?0x11:0x22);
            return normal(f.returnRipBits(),offered(j+1,j==0?NEW16:0x4001),f.call().nonvolatileBits(),j==1,j==0?F1:F2,0);
        };
        Add4Fp639Api.Calls foreign=f->{long site=f.call().callSiteRva();same(site==0xadd153||site==0xadd1b5,"only explicit allocator/release ports");
            if(site==0xadd153){m.writeByte(MARK,0x33);return normal(f.returnRipBits(),offered(3,dest),f.call().nonvolatileBits(),true,F3,0);}
            m.writeByte(MARK,0x44);m.writeDword(S+0x40,0x80000001);m.writeByte(S+0x44,0x7e);return normal(f.returnRipBits(),offered(4,0x6001),f.call().nonvolatileBits(),false,F4,0);
        };
        FullCopyWithFp613.TailCalls unknown=f->{tail[0]++;var t=f.original().transfer();
            VolatileBits vv=v(offered(3,dest),dest+12,dest+12,0,0,I+UNKNOWN,I,new Bits128(offered(3,dest).xmm0().lowBits(),offered(3,dest).xmm0().highBits()));
            same(mode==1&&tail[0]==1&&t.jumpSiteRva()==0x422688b&&t.kind()==GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE&&t.targetBits()==I+UNKNOWN,"actual zeroCOPY fresh unknown table tail");
            same(t.entry().equals(new GovernmentCrtBoundary185Api.Entry(I,C,vv,addN(true,dest)))&&f.preMxcsr()==F3&&f.original().directionFlagSet(),"full unknown tail state/DF/FP");
            ev(m.events,"TAIL",0x422688b,I+UNKNOWN);m.writeByte(MARK,0x55);stopped[0]=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(t.entry(),0x422688b,true,F3),0,0xadd1a0);return stopped[0];
        };
        Add4Fp639Api.Calls copy=Add4Copy259.bind(m,budget,unknown,foreign);
        Add4Fp639Api.Calls add=f->{int j=ac[0]++;same(j<5,"five Add calls including zero COPY");long[] sites={0xadd153,0xadd16d,0xadd17c,0xadd1a0,0xadd1b5};long site=sites[j],target=j==0?TARGET4A:j==4?TARGET4F:0x4226860;
            var o3=offered(3,dest);VolatileBits vv;
            if(j==0)vv=v(offered(2,0x4001),T4,A4,12,4,B4+12,offered(2,0x4001).r10Bits(),new Bits128(0,0));
            else if(j==1)vv=v(o3,dest,dest,0,0,o3.r9Bits(),o3.r10Bits(),o3.xmm0());
            else if(j==2)vv=v(o3,dest,dest,B4,12,I+0x422688e,I,o3.xmm0());
            else if(j==3)vv=v(o3,3,dest+12,0,0,I+0x4226943,I,o3.xmm0());
            else vv=v(o3,T4,A4,0,4,I+0x422688e,I,o3.xmm0());
            checkFrame(f.call(),f.childEntry(),site,target,j==0||j==4?3:5,L,vv,addN(j!=0,dest),true,j==0?F2:F3,f.directionFlagSet(),f.preMxcsr(),f.returnRipBits(),f.instructionLength());
            ev(m.events,"CALL",site,target);var offered=copy.invoke(f);
            if(offered instanceof QueueFp604Api.Stopped){same(offered==stopped[0],"COPY/Add wrapper exact deep Stopped identity");addStopped[0]=offered;}
            return offered;
        };
        EmbeddedElementsFp637.Calls foreignParent=f->{
            fc[0]++;same(f.original().call().callSiteRva()==0x37282e1,"sole explicit parent cleanup port");
            m.writeByte(MARK,0x66);
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(cleanupV(),I+0x37282e6,R-0x48,cleanupN()),true),F0);
        };
        same(m.events.isEmpty(),"owned seed creates no runtime events");
        var bound=EmbeddedElementsKnownLower642.bind(m,budget,range,add,foreignParent);
        same(m.events.isEmpty(),"factory has no RAM/CALL/push/RET effects");
        EmbeddedElementsFp637.Calls observed=f->{
            int j=pc[0]++;same(j<2,"exact two whole parent calls");var original=f.original();
            long site=j==0?0x37282e1:0x37283b6,target=j==0?0x889780:0x37297f0;
            checkFrame(original.call(),original.childEntry(),site,target,5,R-0x48,j==0?rootV():v0(),j==0?cleanupN():n0(),true,F0,original.directionFlagSet(),f.preMxcsr(),original.returnRipBits(),original.instructionLength());
            ev(m.events,"PARENT",site,target);var offered=bound.invoke(f);
            if(j==1){
                parent172[0]=offered;
                if(mode==1)same(offered==stopped[0]&&offered==addStopped[0],"deep Stopped same object at selected parent call");
                else {
                    same(offered instanceof QueueFp604Api.Normal,"real172 whole Normal reaches parent");
                    var child=(QueueFp604Api.Normal)offered;var childV=v(offered(4,0x6001),D,offered(4,0x6001).rcxBits(),offered(4,0x6001).rdxBits(),offered(4,0x6001).r8Bits(),offered(4,0x6001).r9Bits(),offered(4,0x6001).r10Bits(),offered(4,0x6001).xmm0());
                    same(child.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(childV,CHILD_RIP,P+8,n0()))&&!child.base().postDirectionFlagSet()&&child.postMxcsr()==F4,"complete child172 return in new parent context");
                }
            }
            return offered;
        };
        var input=new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,R,rootV(),rootN()),true,budget),F0);
        var out=EmbeddedElementsFp637.execute(input,m,observed);
        same(pc[0]==2&&fc[0]==1&&parent172[0]!=null,"parent exact selected/foreign routing");
        if(mode==0){same(rc[0]==2&&ac[0]==5&&tail[0]==0&&out instanceof QueueFp604Api.Normal,"new whole parent bothpositive/COPY0,12,0");var normal=(QueueFp604Api.Normal)out;var vv=v(offered(4,0x6001),ROOT_D,offered(4,0x6001).rcxBits(),offered(4,0x6001).rdxBits(),offered(4,0x6001).r8Bits(),offered(4,0x6001).r9Bits(),offered(4,0x6001).r10Bits(),offered(4,0x6001).xmm0());same(normal.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(vv,RIP,R+8,rootN()))&&!normal.base().postDirectionFlagSet()&&normal.postMxcsr()==F4,"whole parent final V/N/SP/RIP/DF/same partialMXCSR");}
        if(mode==1)same(out==stopped[0]&&out==parent172[0]&&out==addStopped[0]&&rc[0]==2&&ac[0]==4&&tail[0]==1,"deep Stopped same identity through whole parent/no continuation");
        List<Event> z=expected(mode,dest);compare(m,want,z);
        same(m.peek(ROOT_D,8)==D&&m.peek(ROOT_D+8,4)==1&&m.peek(ROOT_D+12,4)==1,"parent pointer/capacity and pre-child count commit remain");
        same(m.peek(H16,8)==NEW16&&m.peek(H16+8,4)==2&&m.peek(H16+12,4)==2&&m.peek(NEW16,8)==WORD0.lowBits()&&m.peek(NEW16+24,8)==WORD1.highBits(),"first positive16 complete and preserved");
        if(mode==0)same(m.peek(H4,8)==dest&&m.peek(H4+8,4)==3&&m.peek(H4+12,4)==3&&m.peek(dest,8)==PAYLOAD&&m.peek(dest+8,4)==UNKNOWN,"positive4 actual data/commit");
        if(mode==1)same(m.peek(JT,4)==UNKNOWN&&m.peek(H4,8)==0&&m.peek(H4+8,8)==0&&m.peek(D+0x40,4)==0xccccccccL,"table alias effects survive; Add/upper commits absent");
    }
    private static QueueFp604Api.Mxcsr trueFP(int j) {return j==0?F0:F1;}
    private static List<Event> expected(int mode,long dest) {
        List<Event> z=new ArrayList<>();var n=n0();var root=rootN();
        ev(z,"W64",R+8,root.rbxBits());ev(z,"W64",R+0x10,root.rbpBits());ev(z,"W64",R+0x18,root.rsiBits());ev(z,"W64",R+0x20,root.rdiBits());
        ev(z,"W64",R-8,root.r12Bits());ev(z,"W64",R-0x10,root.r14Bits());ev(z,"W64",R-0x18,root.r15Bits());
        ev(z,"R32",ROOT_S+12,1);ev(z,"R64",ROOT_S,S);ev(z,"W64",P,I+0x37282e6);ev(z,"PARENT",0x37282e1,0x889780);ev(z,"W8",MARK,0x66);
        ev(z,"R32",ROOT_D+12,0);ev(z,"R32",ROOT_D+8,1);ev(z,"W32",ROOT_D+12,1);ev(z,"R64",ROOT_D,D);ev(z,"BUDGET",0x37283b0,S);ev(z,"W64",P,CHILD_RIP);ev(z,"PARENT",0x37283b6,0x37297f0);
        ev(z,"W64",P+8,n.rbxBits());ev(z,"W64",P+16,n.rsiBits());ev(z,"W64",P-8,n.rdiBits());ev(z,"W64",D,I+0x45648a0);ev(z,"R32",S+8,0x76543210);ev(z,"W32",D+8,0x76543210);
        ev(z,"W64",D+0x18,0);ev(z,"W64",D+0x20,0);ev(z,"W64",H16,0);ev(z,"W64",H16+8,0);ev(z,"W64",H16+16,A16);ev(z,"R32",S+0x1c,2);ev(z,"R64",S+0x10,B16);ev(z,"W64",P-0x30,I+0x372984b);
        ev(z,"W64",P-0x38,S);ev(z,"W64",P-0x40,0);ev(z,"W64",P-0x48,D);ev(z,"W64",P-0x50,n.r14Bits());ev(z,"R32",H16+12,0);ev(z,"W64",P-0x28,n.rbpBits());ev(z,"R32",H16+8,0);ev(z,"W64",P-0x58,n.r15Bits());ev(z,"R64",H16+16,A16);
        ev(z,"W64",P-0x20,n.r12Bits());ev(z,"W64",P-0x18,n.r13Bits());ev(z,"R32",I+0x49f64f0,0x3fc00000);ev(z,"R64",A16,T16);ev(z,"R64",T16+8,TARGET16A);ev(z,"W64",C,I+0x8c7134);ev(z,"CALL",0x8c7131,TARGET16A);ev(z,"W8",MARK,0x11);
        ev(z,"R64",H16,0);ev(z,"BUDGET",0x8c7170,B16);wide(z,"R128",B16,WORD0);wide(z,"W128",NEW16,WORD0);ev(z,"BUDGET",0x8c7170,B16+16);wide(z,"R128",B16+16,WORD1);wide(z,"W128",NEW16+16,WORD1);
        ev(z,"R64",H16,0);ev(z,"R32",H16+12,0);ev(z,"R64",H16+16,A16);ev(z,"R64",A16,T16);ev(z,"R64",T16+16,TARGET16F);ev(z,"W64",C,I+0x8c71da);ev(z,"CALL",0x8c71d7,TARGET16F);ev(z,"W8",MARK,0x22);
        ev(z,"W64",H16,NEW16);ev(z,"R64",P-0x20,n.r12Bits());ev(z,"W32",H16+8,2);ev(z,"R64",P-0x18,n.r13Bits());ev(z,"W32",H16+12,2);ev(z,"R64",P-0x28,n.rbpBits());ev(z,"R64",P-0x58,n.r15Bits());ev(z,"R64",P-0x50,n.r14Bits());ev(z,"R64",P-0x48,D);ev(z,"R64",P-0x40,0);ev(z,"R64",P-0x38,S);ev(z,"R64",P-0x30,I+0x372984b);
        ev(z,"W64",D+0x30,0);ev(z,"W64",D+0x38,0);ev(z,"W64",H4,0);ev(z,"W64",H4+8,0);ev(z,"W64",H4+16,A4);ev(z,"R64",S+0x28,B4);ev(z,"R32",S+0x34,3);ev(z,"W64",P-0x30,I+0x372987c);
        ev(z,"W64",P-0x38,S);ev(z,"W64",P-0x40,n.r13Bits());ev(z,"W64",P-0x48,n.r14Bits());ev(z,"W64",P-0x50,n.r15Bits());ev(z,"R32",H4+12,0);ev(z,"W64",P-0x58,n.r12Bits());ev(z,"R32",H4+8,0);ev(z,"W32",P-0x28,3);ev(z,"W64",P-0x20,n.rbpBits());ev(z,"W64",P-0x18,0);ev(z,"W64",P-0x10,D);ev(z,"R32",I+0x49f64f0,0x3fc00000);ev(z,"R64",H4+16,A4);ev(z,"R64",A4,T4);ev(z,"R64",T4+8,TARGET4A);ev(z,"W64",C,I+0xadd156);ev(z,"CALL",0xadd153,TARGET4A);ev(z,"W8",MARK,0x33);
        ev(z,"R64",H4,0);ev(z,"W64",C,I+0xadd172);ev(z,"CALL",0xadd16d,0x4226860);ev(z,"R32",JT,0x422688e);ev(z,"R64",C,I+0xadd172);
        ev(z,"W64",C,I+0xadd181);ev(z,"CALL",0xadd17c,0x4226860);ev(z,"R32",JT+48,0x4226943);ev(z,"R64",B4,PAYLOAD);ev(z,"R32",B4+8,UNKNOWN);ev(z,"W64",dest,PAYLOAD);ev(z,"W32",dest+8,UNKNOWN);ev(z,"R64",C,I+0xadd181);
        ev(z,"R64",H4,0);ev(z,"R32",H4+12,0);ev(z,"W64",C,I+0xadd1a5);ev(z,"CALL",0xadd1a0,0x4226860);ev(z,"R32",JT,mode==1?UNKNOWN:0x422688e);
        if(mode==1){ev(z,"TAIL",0x422688b,I+UNKNOWN);ev(z,"W8",MARK,0x55);return z;}
        ev(z,"R64",C,I+0xadd1a5);ev(z,"R64",H4+16,A4);ev(z,"R64",H4,0);ev(z,"R64",A4,T4);ev(z,"R64",T4+16,TARGET4F);ev(z,"W64",C,I+0xadd1b8);ev(z,"CALL",0xadd1b5,TARGET4F);ev(z,"W8",MARK,0x44);ev(z,"W32",S+0x40,0x80000001);ev(z,"W8",S+0x44,0x7e);
        ev(z,"R32",P-0x28,3);ev(z,"R64",P-0x10,D);ev(z,"R64",P-0x58,n.r12Bits());ev(z,"W64",H4,dest);ev(z,"R64",P-0x18,0);ev(z,"W32",H4+8,3);ev(z,"R64",P-0x20,n.rbpBits());ev(z,"W32",H4+12,3);ev(z,"R64",P-0x50,n.r15Bits());ev(z,"R64",P-0x48,n.r14Bits());ev(z,"R64",P-0x40,n.r13Bits());ev(z,"R64",P-0x38,S);ev(z,"R64",P-0x30,I+0x372987c);
        ev(z,"R32",S+0x40,0xffffffff80000001L);ev(z,"R64",P+16,n.rsiBits());ev(z,"W32",D+0x40,0xffffffff80000001L);ev(z,"R8",S+0x44,0x7e);ev(z,"R64",P+8,n.rbxBits());ev(z,"W8",D+0x44,0x7e);ev(z,"R64",P-8,n.rdiBits());ev(z,"R64",P,CHILD_RIP);
        ev(z,"R64",R+8,root.rbxBits());ev(z,"R64",R+0x10,root.rbpBits());ev(z,"R64",R+0x18,root.rsiBits());ev(z,"R64",R+0x20,root.rdiBits());
        ev(z,"R64",R-0x18,root.r15Bits());ev(z,"R64",R-0x10,root.r14Bits());ev(z,"R64",R-8,root.r12Bits());ev(z,"R64",R,RIP);return z;
    }
    public static void normalParentPositive16And4() {fixture(0);}
    public static void aliasParentDeepStopped() {fixture(1);}
    public static int verify2() {normalParentPositive16And4();aliasParentDeepStopped();return 2;}
    public static int verify() {return verify2();}
    public static void main(String[] args) {System.out.println(verify2());}
}
