package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.ParentFixture647.Ram;
import org.xar.ck3.control.g2.m2.nativecode.ParentFixture647.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner fallback A, authorized after modelR1 rejection; not model adoption or generationblind.
 * APPEND-A-COUNT1-ORACLE647.json predates this new source. Originalprivateoracle staysfrozen.
 * New whole647 executes actualclear645 then sameinstance172 withpositive16=1/4=1 andrealCOPY0/4/0.
 * Expectedframes/events/fullRAM are source literals. All opaque completeoutcomes are explicitownedoffers. */
public final class ParentClearPositiveElement647 {
    private ParentClearPositiveElement647() { }
    private static final long I=0x140000000L,ROOT=0x70004008L,P=ROOT-0x50,D=0x8000000000001100L,S=0xf000000000002200L;
    private static final long ROOT_D=0x8000000000011000L,ROOT_S=0xf000000000022000L,CHILD_RIP=I+0x37283bb;
    private static final long CLEAR_TABLE=0x9000000000004000L,CLEAR_TARGET=0x800000000000aaaaL,CLEAR_MARK=0x7700;
    private static final long B16=0x4000,B4=0x5000,NEW16=0x9000,NEW4=0xa000,T16=0xb000,T4=0xc000;
    private static final long A16=I+0x54de260,A4=I+0x54de268,H16=D+0x10,H4=D+0x28,L=P-0x78,C=P-0x80;
    private static final long TARGET16A=0x800000000000c001L,TARGET16F=0xf00000000000c002L,TARGET4A=0x800000000000c003L,TARGET4F=0xf00000000000c004L;
    private static final long RIP=I+0x123456,JT=I+0x6090000,PAYLOAD=0x12345678L,MARK=0x7770;
    private static final Bits128 WORD0=new Bits128(0x0102030405060708L,0x1112131415161718L);
    private static final QueueFp604Api.Mxcsr F0=QueueFp604Api.Mxcsr.exact(0x1f80),F1=QueueFp604Api.Mxcsr.exact(0x1fa0),F2=QueueFp604Api.Mxcsr.exact(0x1f81),F3=QueueFp604Api.Mxcsr.exact(0x3f80),F4=new QueueFp604Api.Mxcsr(8,12);
    private static void ev(List<Event> z,String k,long a,long v) {z.add(ParentFixture647.e(k,a,v));}
    private static void wide(List<Event> z,String k,long a,Bits128 x) {z.add(ParentFixture647.e128(k,a,x));}
    private static void same(boolean ok,String why) {if(!ok)throw new AssertionError(why);}
    private static Bits128 x(long n) {return new Bits128(n,~n);}
    private static VolatileBits bank(long b,long ax,long cx,long dx,long r8,long r9) {return new VolatileBits(ax,cx,dx,r8,r9,b+10,b+11,x(b),x(b+1),x(b+2),x(b+3),x(b+4),x(b+5));}
    private static VolatileBits rootV() {return bank(0x1000,0x111,ROOT_D,ROOT_S,0x114,0x115);}
    private static VolatileBits clearOfferV() {return bank(0x1000,0x771,0x772,0x773,0x114,0x115);}
    private static VolatileBits v0() {return bank(0x1000,0,D,S,0x114,0x115);}
    private static VolatileBits offered(int j,long ax) {long b=0x2000+j*0x1000;return bank(b,ax,b+2,b+3,b+4,b+5);}
    private static VolatileBits v(VolatileBits b,long ax,long cx,long dx,long r8,long r9,long r10,Bits128 x0) {return new VolatileBits(ax,cx,dx,r8,r9,r10,b.r11Bits(),x0,b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());}
    private static NonvolatileBits rootN() {return new NonvolatileBits(0x101,0x102,0x103,0x104,0x105,0x106,0x107,0x108,x(0x109));}
    private static NonvolatileBits cleanupN() {var n=rootN();return new NonvolatileBits(1,S,ROOT_D,n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static NonvolatileBits clearN() {var n=rootN();return new NonvolatileBits(D,S,ROOT_D,1,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static NonvolatileBits n0() {var n=rootN();return new NonvolatileBits(1,S,ROOT_D,D,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static NonvolatileBits rangeN(boolean allocated) {var n=n0();return new NonvolatileBits(allocated?B16+16:B16,1,B16+16,H16,allocated?NEW16:n.r12Bits(),1,0,1,n.xmm6());}
    private static NonvolatileBits addN(boolean allocated,long dest) {var n=n0();return new NonvolatileBits(0,1,allocated?dest:0,allocated?0:D,1,B4,H4,4,n.xmm6());}
    private static Ram initial() {
        Ram m=new Ram();for(int i=0;i<0x250;i++)m.seed(ROOT-0x200+i,1,0x5a);m.seed(ROOT,8,RIP);
        for(int i=0;i<0x48;i++){m.seed(D+i,1,0xcc);m.seed(S+i,1,0xcc);}
        for(int i=0;i<0x18;i++){m.seed(ROOT_D+i,1,0xcc);m.seed(ROOT_S+i,1,0xcc);}
        m.seed(ROOT_D,8,D);m.seed(ROOT_D+8,4,1);m.seed(ROOT_D+12,4,1);m.seed(ROOT_S,8,S);m.seed(ROOT_S+12,4,1);
        m.seed(D,8,CLEAR_TABLE);m.seed(CLEAR_TABLE,8,CLEAR_TARGET);
        m.seed(S+8,4,0x76543210);m.seed(S+0x10,8,B16);m.seed(S+0x1c,4,1);m.seed(S+0x28,8,B4);m.seed(S+0x34,4,1);m.seed(S+0x40,4,0x55667788);m.seed(S+0x44,1,0x99);
        for(int i=0;i<32;i++){m.seed(B16-8+i,1,0xdd);m.seed(NEW16-8+i,1,0xcc);}
        for(int i=0;i<20;i++){m.seed(B4-8+i,1,0xdd);m.seed(NEW4-8+i,1,0xcc);}
        m.seed128(B16,WORD0);m.seed(B4,4,PAYLOAD);
        m.seed(A16,8,T16);m.seed(A4,8,T4);m.seed(T16+8,8,TARGET16A);m.seed(T16+16,8,TARGET16F);m.seed(T4+8,8,TARGET4A);m.seed(T4+16,8,TARGET4F);
        m.seed(I+0x49f64f0,4,0x3fc00000);for(int i=0;i<64;i++)m.seed(JT+i,1,0);
        m.seed(JT,4,0x422688e);m.seed(JT+4*4,4,0x422697a);m.seed(MARK,1,0xcc);m.seed(CLEAR_MARK,1,0xcc);return m;
    }
    private static void checkFrame(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,long site,long target,int len,long pre,VolatileBits vv,NonvolatileBits nn,boolean df,QueueFp604Api.Mxcsr fp,boolean actualDf,QueueFp604Api.Mxcsr actualFp,long rip,int actualLen) {
        var kind=len==5?GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA:GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE;
        same(call.equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,vv,nn)),"complete CALL state at "+Long.toHexString(site));
        same(child.equals(new GovernmentCrtBoundary185Api.Entry(I,pre-8,vv,nn)),"complete child state");
        same(actualDf==df&&actualFp==fp&&rip==I+site+len&&actualLen==len,"DF/MXCSR identity/SP/actual return metadata");
    }
    private static QueueFp604Api.Normal normal(long rip,VolatileBits vv,NonvolatileBits nn,boolean df,QueueFp604Api.Mxcsr fp,long error) {return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(vv,rip+error,L,nn),df),fp);}
    private static void compare(Ram m,Ram want,List<Event> expected) {
        for(Event e:expected)switch(e.kind()) {case "W64"->want.seed(e.address(),8,e.a());case "W32"->want.seed(e.address(),4,e.a());case "W8"->want.seed(e.address(),1,e.a());case "W128"->{want.seed(e.address(),8,e.a());want.seed(e.address()+8,8,e.b());}default->{}}
        if(!m.events.equals(expected)){int j=0;while(j<m.events.size()&&j<expected.size()&&m.events.get(j).equals(expected.get(j)))j++;throw new AssertionError("647 ownerA cursor "+j+" actual="+(j<m.events.size()?m.events.get(j):"END")+" expected="+(j<expected.size()?expected.get(j):"END"));}
        same(m.bytes.equals(want.bytes),"entire RAM equality including callstack and committed prefix");
    }
    public static void clearNormalThenPositiveElement() {
        Ram m=initial(),want=initial();int[] rc={0},ac={0},cc={0},pc={0};
        var budget=(GovernmentCrtBoundary185Api.LoopBudget)(site,cursor)->{
            same((site==0x8897a0&&cursor==D)||(site==0x37283b0&&cursor==S)||(site==0x8c7170&&cursor==B16),"only three actual source budget sites/cursors");m.step(site,cursor);
        };
        Range16Fp638Api.Calls range=f->{int j=rc[0]++;same(j<2,"two actualRange allocator/release calls");long site=j==0?0x8c7131:0x8c71d7,target=j==0?TARGET16A:TARGET16F;
            VolatileBits vv=j==0?v(v0(),T16,A16,16,8,B16+16,v0().r10Bits(),new Bits128(0,0)):v(offered(1,NEW16),T16,A16,0,8,0,0,WORD0);
            checkFrame(f.call(),f.childEntry(),site,target,3,L,vv,rangeN(j==1),j==0,trueFP(j),f.directionFlagSet(),f.preMxcsr(),f.returnRipBits(),f.instructionLength());
            ev(m.events,"CALL",site,target);m.writeByte(MARK,j==0?0x11:0x22);
            return normal(f.returnRipBits(),offered(j+1,j==0?NEW16:0x4001),rangeN(j==1),j==1,j==0?F1:F2,0);
        };
        Add4Fp639Api.Calls foreignAdd=f->{int j=ac[0]++;same(j<2,"only explicitAdd allocator/release ports");long site=j==0?0xadd153:0xadd1b5,target=j==0?TARGET4A:TARGET4F;
            var o3=offered(3,NEW4);VolatileBits vv=j==0?v(offered(2,0x4001),T4,A4,4,4,B4+4,offered(2,0x4001).r10Bits(),new Bits128(0,0)):v(o3,T4,A4,0,4,I+0x422688e,I,o3.xmm0());
            checkFrame(f.call(),f.childEntry(),site,target,3,L,vv,addN(j==1,NEW4),true,j==0?F2:F3,f.directionFlagSet(),f.preMxcsr(),f.returnRipBits(),f.instructionLength());
            ev(m.events,"CALL",site,target);
            if(j==0){m.writeByte(MARK,0x33);return normal(f.returnRipBits(),o3,addN(false,NEW4),true,F3,0);}
            m.writeByte(MARK,0x44);m.writeDword(S+0x40,0x80000001);m.writeByte(S+0x44,0x7e);
            return normal(f.returnRipBits(),offered(4,0x6001),addN(true,NEW4),false,F4,0);
        };
        EmbeddedClearFp645Api.Calls clear=f->{int j=cc[0]++;same(j==0,"one realclear virtualdestructor");var o=f.original();
            var vv=v(rootV(),CLEAR_TABLE,D,0,rootV().r8Bits(),rootV().r9Bits(),rootV().r10Bits(),rootV().xmm0());
            checkFrame(o.call(),o.childEntry(),0x8897a8,CLEAR_TARGET,2,ROOT-0x78,vv,clearN(),true,F0,o.directionFlagSet(),f.preMxcsr(),o.returnRipBits(),o.instructionLength());
            ev(m.events,"CLEAR",0x8897a8,CLEAR_TARGET);m.writeByte(CLEAR_MARK,0x11);
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(clearOfferV(),I+0x8897aa,ROOT-0x78,clearN()),true),F0);
        };
        FullCopyWithFp613.TailCalls unknown=f->{throw new AssertionError("unexpectedunknownCOPYtail");};
        Element150Fp643Api.Calls construct=f->{throw new AssertionError("unexpectedparent150");};
        EmbeddedElementsFp637.Calls foreignParent=f->{throw new AssertionError("unexpectedparentgrowth/DBDB80/destructor");};
        same(m.events.isEmpty(),"seeds are mechanical");
        var bound=EmbeddedElementsAllKnown647.bind(m,budget,range,unknown,foreignAdd,construct,clear,foreignParent);
        same(m.events.isEmpty(),"new647 factory addsnoMemory/CALL/RET effects");
        EmbeddedElementsFp637.Calls observed=f->{int j=pc[0]++;same(j<2,"exactclear andknown172 parentcalls");var o=f.original();long site=j==0?0x37282e1:0x37283b6,target=j==0?0x889780:0x37297f0;
            checkFrame(o.call(),o.childEntry(),site,target,5,ROOT-0x48,j==0?rootV():v0(),j==0?cleanupN():n0(),true,F0,o.directionFlagSet(),f.preMxcsr(),o.returnRipBits(),o.instructionLength());
            ev(m.events,"PARENT",site,target);var out=bound.invoke(f);same(out instanceof QueueFp604Api.Normal,"completeactualknowncallee Normal");var normal=(QueueFp604Api.Normal)out;
            if(j==0){same(normal.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(clearOfferV(),I+0x37282e6,ROOT-0x48,cleanupN()))&&normal.base().postDirectionFlagSet()&&normal.postMxcsr()==F0,"complete realclearreturnframe/currentFP");same(m.peek(ROOT_D+12,4)==0,"realclearNormal hasactuallyclearedcount beforeparentfreshread");}
            else {var childV=v(offered(4,0x6001),D,offered(4,0x6001).rcxBits(),offered(4,0x6001).rdxBits(),offered(4,0x6001).r8Bits(),offered(4,0x6001).r9Bits(),offered(4,0x6001).r10Bits(),offered(4,0x6001).xmm0());same(normal.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(childV,CHILD_RIP,P+8,n0()))&&!normal.base().postDirectionFlagSet()&&normal.postMxcsr()==F4,"completepositive1/1actual172returninparentcontext");}
            return out;
        };
        var input=new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,ROOT,rootV(),rootN()),true,budget),F0);
        var out=EmbeddedElementsFp637.execute(input,m,observed);same(out instanceof QueueFp604Api.Normal,"fullrootNormal");var normal=(QueueFp604Api.Normal)out;
        var vv=v(offered(4,0x6001),ROOT_D,offered(4,0x6001).rcxBits(),offered(4,0x6001).rdxBits(),offered(4,0x6001).r8Bits(),offered(4,0x6001).r9Bits(),offered(4,0x6001).r10Bits(),offered(4,0x6001).xmm0());
        same(normal.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(vv,RIP,ROOT+8,rootN()))&&!normal.base().postDirectionFlagSet()&&normal.postMxcsr()==F4,"exactrootV/N/SP/RIP/DF/samecurrentpartialMXCSR");
        same(pc[0]==2&&cc[0]==1&&rc[0]==2&&ac[0]==2,"allactualcallbackcounts / noforeignparentor150");
        compare(m,want,expected());
        same(m.peek(ROOT_D+12,4)==1&&m.peek(ROOT_D+8,4)==1&&m.peek(ROOT_D,8)==D,"parentfinalcount1afterclear0/currentfreshbase");
        same(m.peek(H16,8)==NEW16&&m.peek(H16+8,4)==1&&m.peek(H16+12,4)==1&&m.peek(NEW16,8)==WORD0.lowBits()&&m.peek(NEW16+8,8)==WORD0.highBits(),"positive16oneelement / whole128data/header");
        same(m.peek(H4,8)==NEW4&&m.peek(H4+8,4)==1&&m.peek(H4+12,4)==1&&m.peek(NEW4,4)==PAYLOAD,"positive4oneelement / realCOPY0/4/0data/header");
        same(m.peek(D+0x40,4)==0x80000001L&&m.peek(D+0x44,1)==0x7e,"upperfreshsourcefieldsafterexplicitAddreleaseeffects");
    }
    private static QueueFp604Api.Mxcsr trueFP(int j) {return j==0?F0:F1;}
    private static List<Event> expected() {
        List<Event> z=new ArrayList<>();var n=n0();var r=rootN();long dest=NEW4;
        ev(z,"W64",ROOT+8,r.rbxBits());ev(z,"W64",ROOT+0x10,r.rbpBits());ev(z,"W64",ROOT+0x18,r.rsiBits());ev(z,"W64",ROOT+0x20,r.rdiBits());ev(z,"W64",ROOT-8,r.r12Bits());ev(z,"W64",ROOT-0x10,r.r14Bits());ev(z,"W64",ROOT-0x18,r.r15Bits());
        ev(z,"R32",ROOT_S+12,1);ev(z,"R64",ROOT_S,S);ev(z,"W64",P,I+0x37282e6);ev(z,"PARENT",0x37282e1,0x889780);
        ev(z,"W64",P+0x10,ROOT_D);ev(z,"W64",P-8,r.rdiBits());ev(z,"R32",ROOT_D+12,1);ev(z,"W64",P+8,1);ev(z,"R64",ROOT_D,D);ev(z,"BUDGET",0x8897a0,D);ev(z,"R64",D,CLEAR_TABLE);ev(z,"R64",CLEAR_TABLE,CLEAR_TARGET);ev(z,"W64",P-0x30,I+0x8897aa);ev(z,"CLEAR",0x8897a8,CLEAR_TARGET);ev(z,"W8",CLEAR_MARK,0x11);
        ev(z,"R64",P+8,1);ev(z,"W32",ROOT_D+12,0);ev(z,"R64",P+0x10,ROOT_D);ev(z,"R64",P-8,r.rdiBits());ev(z,"R64",P,I+0x37282e6);
        ev(z,"R32",ROOT_D+12,0);ev(z,"R32",ROOT_D+8,1);ev(z,"W32",ROOT_D+12,1);ev(z,"R64",ROOT_D,D);ev(z,"BUDGET",0x37283b0,S);ev(z,"W64",P,CHILD_RIP);ev(z,"PARENT",0x37283b6,0x37297f0);
        ev(z,"W64",P+8,n.rbxBits());ev(z,"W64",P+16,n.rsiBits());ev(z,"W64",P-8,n.rdiBits());ev(z,"W64",D,I+0x45648a0);ev(z,"R32",S+8,0x76543210);ev(z,"W32",D+8,0x76543210);
        ev(z,"W64",D+0x18,0);ev(z,"W64",D+0x20,0);ev(z,"W64",H16,0);ev(z,"W64",H16+8,0);ev(z,"W64",H16+16,A16);ev(z,"R32",S+0x1c,1);ev(z,"R64",S+0x10,B16);ev(z,"W64",P-0x30,I+0x372984b);
        ev(z,"W64",P-0x38,S);ev(z,"W64",P-0x40,0);ev(z,"W64",P-0x48,D);ev(z,"W64",P-0x50,n.r14Bits());ev(z,"R32",H16+12,0);ev(z,"W64",P-0x28,n.rbpBits());ev(z,"R32",H16+8,0);ev(z,"W64",P-0x58,n.r15Bits());ev(z,"R64",H16+16,A16);
        ev(z,"W64",P-0x20,n.r12Bits());ev(z,"W64",P-0x18,n.r13Bits());ev(z,"R32",I+0x49f64f0,0x3fc00000);ev(z,"R64",A16,T16);ev(z,"R64",T16+8,TARGET16A);ev(z,"W64",C,I+0x8c7134);ev(z,"CALL",0x8c7131,TARGET16A);ev(z,"W8",MARK,0x11);
        ev(z,"R64",H16,0);ev(z,"BUDGET",0x8c7170,B16);wide(z,"R128",B16,WORD0);wide(z,"W128",NEW16,WORD0);
        ev(z,"R64",H16,0);ev(z,"R32",H16+12,0);ev(z,"R64",H16+16,A16);ev(z,"R64",A16,T16);ev(z,"R64",T16+16,TARGET16F);ev(z,"W64",C,I+0x8c71da);ev(z,"CALL",0x8c71d7,TARGET16F);ev(z,"W8",MARK,0x22);
        ev(z,"W64",H16,NEW16);ev(z,"R64",P-0x20,n.r12Bits());ev(z,"W32",H16+8,1);ev(z,"R64",P-0x18,n.r13Bits());ev(z,"W32",H16+12,1);ev(z,"R64",P-0x28,n.rbpBits());ev(z,"R64",P-0x58,n.r15Bits());ev(z,"R64",P-0x50,n.r14Bits());ev(z,"R64",P-0x48,D);ev(z,"R64",P-0x40,0);ev(z,"R64",P-0x38,S);ev(z,"R64",P-0x30,I+0x372984b);
        ev(z,"W64",D+0x30,0);ev(z,"W64",D+0x38,0);ev(z,"W64",H4,0);ev(z,"W64",H4+8,0);ev(z,"W64",H4+16,A4);ev(z,"R64",S+0x28,B4);ev(z,"R32",S+0x34,1);ev(z,"W64",P-0x30,I+0x372987c);
        ev(z,"W64",P-0x38,S);ev(z,"W64",P-0x40,n.r13Bits());ev(z,"W64",P-0x48,n.r14Bits());ev(z,"W64",P-0x50,n.r15Bits());ev(z,"R32",H4+12,0);ev(z,"W64",P-0x58,n.r12Bits());ev(z,"R32",H4+8,0);ev(z,"W32",P-0x28,1);ev(z,"W64",P-0x20,n.rbpBits());ev(z,"W64",P-0x18,0);ev(z,"W64",P-0x10,D);ev(z,"R32",I+0x49f64f0,0x3fc00000);ev(z,"R64",H4+16,A4);ev(z,"R64",A4,T4);ev(z,"R64",T4+8,TARGET4A);ev(z,"W64",C,I+0xadd156);ev(z,"CALL",0xadd153,TARGET4A);ev(z,"W8",MARK,0x33);
        ev(z,"R64",H4,0);ev(z,"W64",C,I+0xadd172);ev(z,"R32",JT,0x422688e);ev(z,"R64",C,I+0xadd172);
        ev(z,"W64",C,I+0xadd181);ev(z,"R32",JT+16,0x422697a);ev(z,"R32",B4,PAYLOAD);ev(z,"W32",dest,PAYLOAD);ev(z,"R64",C,I+0xadd181);
        ev(z,"R64",H4,0);ev(z,"R32",H4+12,0);ev(z,"W64",C,I+0xadd1a5);ev(z,"R32",JT,0x422688e);
        ev(z,"R64",C,I+0xadd1a5);ev(z,"R64",H4+16,A4);ev(z,"R64",H4,0);ev(z,"R64",A4,T4);ev(z,"R64",T4+16,TARGET4F);ev(z,"W64",C,I+0xadd1b8);ev(z,"CALL",0xadd1b5,TARGET4F);ev(z,"W8",MARK,0x44);ev(z,"W32",S+0x40,0x80000001);ev(z,"W8",S+0x44,0x7e);
        ev(z,"R32",P-0x28,1);ev(z,"R64",P-0x10,D);ev(z,"R64",P-0x58,n.r12Bits());ev(z,"W64",H4,dest);ev(z,"R64",P-0x18,0);ev(z,"W32",H4+8,1);ev(z,"R64",P-0x20,n.rbpBits());ev(z,"W32",H4+12,1);ev(z,"R64",P-0x50,n.r15Bits());ev(z,"R64",P-0x48,n.r14Bits());ev(z,"R64",P-0x40,n.r13Bits());ev(z,"R64",P-0x38,S);ev(z,"R64",P-0x30,I+0x372987c);
        ev(z,"R32",S+0x40,0xffffffff80000001L);ev(z,"R64",P+16,n.rsiBits());ev(z,"W32",D+0x40,0xffffffff80000001L);ev(z,"R8",S+0x44,0x7e);ev(z,"R64",P+8,n.rbxBits());ev(z,"W8",D+0x44,0x7e);ev(z,"R64",P-8,n.rdiBits());ev(z,"R64",P,CHILD_RIP);
        ev(z,"R64",ROOT+8,r.rbxBits());ev(z,"R64",ROOT+0x10,r.rbpBits());ev(z,"R64",ROOT+0x18,r.rsiBits());ev(z,"R64",ROOT+0x20,r.rdiBits());ev(z,"R64",ROOT-0x18,r.r15Bits());ev(z,"R64",ROOT-0x10,r.r14Bits());ev(z,"R64",ROOT-8,r.r12Bits());ev(z,"R64",ROOT,RIP);return z;
    }
    public static int verify() {clearNormalThenPositiveElement();return 1;}
    public static void main(String[] args) {System.out.println(verify());}
}
