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

/** Independent source-literal whole322 growth prefixes through the first actual150.
 * Both lower outcomes are explicit owned offers; no 238/239 FP or Native semantics are inferred.
 * SOURCE-ORACLE644-04 was frozen before this Test source. No 643 body was read. */
public final class ParentConstructProtocolBoundary644 {
    private ParentConstructProtocolBoundary644() { }
    private static final long I=IMAGE,P=SP,D=0x8000000000001100L,S=0xF000000000002200L;
    private static final long OLD=0x30000L,SE=0x40000L,NEW=0x73000L,MARK=0x71000L;
    private static final long ROOT_ALLOC=0x74000L,ROOT_VT=0x75000L,ROOT_TARGET=0x76000L;
    private static final long VT=I+0x45648A0L,A16=I+0x54DE260L,A4=I+0x54DE268L;
    private static final long ALIAS0=0x8877665544332211L,ALIAS1=0x0123456789ABCDEFL,POISON=0xF123456789ABCDEFL;
    private static final int KIND=0x7FA54321,TAIL=0x91A2B3C4,FLAG=0xE5,CHANGED_TAIL=0xD1E2F304,CHANGED_FLAG=0x6B;
    private static final NonvolatileBits N0=initialN();
    private static final VolatileBits A=bank(0x900,0x901),B=bank(0xA00,NEW),C=bank(0xD00,0xD01);

    /** Nominal644 Memory over the unchanged mechanical642 RAM; all target layers receive this same object. */
    private static final class Ram implements EmbeddedElementsKnownConstruct644.Memory {
        private final ParentFixture642.Ram owned=new ParentFixture642.Ram();
        final Map<Long,Byte> bytes=owned.bytes;final List<Event> events=owned.events;
        void seed(long p,int width,long value){owned.seed(p,width,value);}
        void step(long pc,long cursor){owned.step(pc,cursor);}
        @Override public int readDword(long p){return owned.readDword(p);}
        @Override public long readQword(long p){return owned.readQword(p);}
        @Override public int readUnsignedByte(long p){return owned.readUnsignedByte(p);}
        @Override public int readUnsignedWord(long p){return owned.readUnsignedWord(p);}
        @Override public Bits128 read128(long p){return owned.read128(p);}
        @Override public FullCopy437Api.Bits256 read256(long p){return owned.read256(p);}
        @Override public void writeDword(long p,int v){owned.writeDword(p,v);}
        @Override public void writeQword(long p,long v){owned.writeQword(p,v);}
        @Override public void writeByte(long p,int v){owned.writeByte(p,v);}
        @Override public void writeWord(long p,int v){owned.writeWord(p,v);}
        @Override public void write128(long p,Bits128 v){owned.write128(p,v);}
        @Override public void write256(long p,FullCopy437Api.Bits256 v){owned.write256(p,v);}
        @Override public int lockedXaddDword(long p,int v){return owned.lockedXaddDword(p,v);}
        @Override public void write128NonTemporal(long p,Bits128 v){owned.write128NonTemporal(p,v);}
        @Override public void write256NonTemporal(long p,FullCopy437Api.Bits256 v){owned.write256NonTemporal(p,v);}
        @Override public void sfence(){owned.sfence();}
    }
    private static VolatileBits bank(long b,long ax) {
        return new VolatileBits(ax,b+2,b+3,b+4,b+5,b+6,b+7,x(b+8),x(b+9),x(b+10),x(b+11),x(b+12),x(b+13));
    }
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,VolatileBits t) {
        return new VolatileBits(ax,cx,dx,r8,r9,t.r10Bits(),t.r11Bits(),t.xmm0(),t.xmm1(),t.xmm2(),t.xmm3(),t.xmm4(),t.xmm5());
    }
    private static NonvolatileBits cleanupN() {
        return new NonvolatileBits(2,SE,D,N0.rdiBits(),N0.r12Bits(),N0.r13Bits(),N0.r14Bits(),N0.r15Bits(),N0.xmm6());
    }
    private static NonvolatileBits parentConstructN() {
        return new NonvolatileBits(2,SE,D,NEW,NEW,N0.r13Bits(),1,OLD,N0.xmm6());
    }
    private static NonvolatileBits lowerN() {
        return new NonvolatileBits(OLD,SE,0,NEW,NEW,N0.r13Bits(),1,OLD,N0.xmm6());
    }
    private static VolatileBits secondV() {return v(A4,NEW+0x28,OLD+0x28,C.r8Bits(),C.r9Bits(),C);}
    private static QueueFp604Api.Normal offered(VolatileBits vv,NonvolatileBits nn,long rip,long rsp,boolean df,QueueFp604Api.Mxcsr fp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(vv,rip,rsp,nn),df),fp);
    }
    private static void frame(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
            boolean actualDf,QueueFp604Api.Mxcsr actualFp,int actualLength,long actualRip,
            long site,long target,int length,boolean indirect,long pre,VolatileBits vv,NonvolatileBits nn,
            boolean df,QueueFp604Api.Mxcsr fp,String why) {
        var kind=indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
        check(call.equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,vv,nn)),why+" complete Call V/N");
        check(child.equals(new GovernmentCrtBoundary185Api.Entry(I,pre-8,vv,nn)),why+" complete child Entry");
        check(actualLength==length&&actualRip==I+site+length&&actualDf==df&&actualFp==fp,why+" length/RIP/DF/MXCSR object");
    }
    private static void parentFrame(EmbeddedElementsFp637.CallFrame f,long site,long target,int len,boolean indirect,
            VolatileBits vv,NonvolatileBits nn,boolean df,QueueFp604Api.Mxcsr fp) {
        var o=f.original();
        frame(o.call(),o.childEntry(),o.directionFlagSet(),f.preMxcsr(),o.instructionLength(),o.returnRipBits(),
                site,target,len,indirect,P-0x48,vv,nn,df,fp,"wholeparent "+Long.toHexString(site));
    }
    private static void lowerFrame(Element150Fp643Api.CallFrame f,long site,long target,VolatileBits vv,
            boolean df,QueueFp604Api.Mxcsr fp) {
        frame(f.call(),f.childEntry(),f.directionFlagSet(),f.preMxcsr(),f.instructionLength(),f.returnRipBits(),
                site,target,5,false,P-0x78,vv,lowerN(),df,fp,"actual150 lower "+Long.toHexString(site));
    }
    private static void fill(Ram m,long p,int count,int salt) {
        for(int j=0;j<count;j++)m.seed(p+j,1,(salt+37*j)&255);
    }
    private static Ram seed() {
        Ram m=new Ram();fill(m,P-0x100,0x150,0x11);fill(m,D,0x20,0x22);fill(m,S,0x20,0x33);
        fill(m,OLD,0x90,0x44);fill(m,SE,0x90,0x55);fill(m,NEW,0x90,0x66);fill(m,MARK,0x20,0x77);
        m.seed(P,8,RIP);m.seed(D,8,OLD);m.seed(D+8,4,1);m.seed(D+0xC,4,1);m.seed(D+0x10,8,ROOT_ALLOC);
        m.seed(S,8,SE);m.seed(S+0xC,4,2);m.seed(OLD+8,4,KIND);m.seed(OLD+0x40,4,TAIL);m.seed(OLD+0x44,1,FLAG);
        m.seed(ROOT_ALLOC,8,ROOT_VT);m.seed(ROOT_VT+8,8,ROOT_TARGET);return m;
    }
    private static void add(List<Event> t,String kind,long p,long a){t.add(e(kind,p,a));}
    /** Complete literal parent path to its first150; not a target-loop reimplementation. */
    private static void parentPrefix(List<Event> t) {
        add(t,"W64",P+8,N0.rbxBits());add(t,"W64",P+0x10,N0.rbpBits());add(t,"W64",P+0x18,N0.rsiBits());add(t,"W64",P+0x20,N0.rdiBits());
        add(t,"W64",P-8,N0.r12Bits());add(t,"W64",P-0x10,N0.r14Bits());add(t,"W64",P-0x18,N0.r15Bits());
        add(t,"R32",S+0xC,2);add(t,"R64",S,SE);add(t,"W64",P-0x50,I+0x37282E6L);
        add(t,"PCALL",0x37282E1,0x889780);add(t,"W32",MARK,0x11223344);
        add(t,"R32",D+0xC,1);add(t,"R32",D+8,1);add(t,"R64",D+0x10,ROOT_ALLOC);add(t,"R64",ROOT_ALLOC,ROOT_VT);add(t,"R64",ROOT_VT+8,ROOT_TARGET);
        add(t,"W64",P-0x50,I+0x3728319L);add(t,"PCALL",0x3728316,ROOT_TARGET);add(t,"W32",MARK+4,0x22334455);
        add(t,"R32",D+0xC,1);add(t,"R64",D,OLD);add(t,"W64",P-0x28,NEW);add(t,"W64",P-0x20,NEW);
        add(t,"BUDGET",0x3728335,OLD);add(t,"W64",P-0x50,I+0x3728340L);add(t,"PCONSTRUCT",0x372833B,0x37295B0);
    }
    /** Both150 CALLs and all intervening alias-overwriting instructions, straightline source literal. */
    private static void constructPrefix(List<Event> t) {
        add(t,"W64",P-0x38,2);add(t,"W64",P-0x30,D);add(t,"W64",P-0x48,NEW);add(t,"W64",P-0x58,NEW);
        add(t,"W64",NEW,VT);add(t,"R32",OLD+8,KIND);add(t,"W32",NEW+8,KIND);add(t,"W64",P-0x40,NEW+0x10);
        add(t,"W64",NEW+0x10,0);add(t,"W64",NEW+0x18,0);add(t,"W64",NEW+0x20,A16);
        add(t,"W64",P-0x80,I+0x3729600L);add(t,"LCALL",0x37295FB,0x21A5050);
        add(t,"W64",NEW+0x28,ALIAS0);add(t,"W64",NEW+0x30,ALIAS1);add(t,"W32",OLD+0x40,CHANGED_TAIL);add(t,"W8",OLD+0x44,CHANGED_FLAG);add(t,"W32",MARK+8,0x33445566);
        add(t,"W64",P-0x40,NEW+0x28);add(t,"W64",NEW+0x28,0);add(t,"W64",NEW+0x30,0);add(t,"W64",NEW+0x38,A4);
        add(t,"W64",P-0x80,I+0x3729625L);add(t,"LCALL",0x3729620,0xB2EEE0);
        add(t,"R64",NEW+0x28,0);add(t,"R64",NEW+0x30,0);add(t,"R64",NEW+0x38,A4);
        add(t,"R32",OLD+0x40,CHANGED_TAIL);add(t,"R8",OLD+0x44,CHANGED_FLAG);add(t,"W32",MARK+12,0x44556677);
    }
    private static void fullTraceAndRam(Ram m,List<Event> expected,Map<Long,Byte> initial,String why) {
        check(m.events.equals(expected),why+" entire source-literal ordered trace: expected="+expected+" actual="+m.events);
        Map<Long,Byte> ram=new HashMap<>(initial);
        for(Event e:expected) {
            int width=switch(e.kind()){case "W64"->8;case "W32"->4;case "W8"->1;default->0;};
            for(int j=0;j<width;j++)ram.put(e.address()+j,(byte)(e.a()>>>(8*j)));
        }
        check(m.bytes.equals(ram),why+" every owned RAM byte, unchanged padding, callback effects and stack");
    }
    /** The lower ports themselves supply all post-state. No callee-preservation default is used. */
    private static void run(boolean stoppedCase) {
        Ram m=seed();Map<Long,Byte> initial=new HashMap<>(m.bytes);
        var incoming=QueueFp604Api.Mxcsr.unknown();var fpA=QueueFp604Api.Mxcsr.exact(0x1F80);
        var fpB=new QueueFp604Api.Mxcsr(0x1000,0x1000);var fpC=new QueueFp604Api.Mxcsr(0x2000,0x2000);
        var stop=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,P-0x80,secondV(),lowerN()),0xB2EEE0,false,fpC),0,0x3729620);
        GovernmentCrtBoundary185Api.LoopBudget budget=m::step;
        int[] cleanup={0},allocation={0},construct={0},lower={0};
        EmbeddedElements578Api.CallFrame[] reachedParent={null};
        EmbeddedElementsFp637.Calls foreign=f->{
            long site=f.original().call().callSiteRva();
            if(site==0x37282E1L) {
                parentFrame(f,site,0x889780,5,false,initialV(D,S),cleanupN(),true,incoming);
                check(++cleanup[0]==1,"cleanup once");m.events.add(e("PCALL",site,0x889780));m.writeDword(MARK,0x11223344);
                return offered(A,cleanupN(),I+0x37282E6L,P-0x48,false,fpA);
            }
            if(site==0x3728316L) {
                parentFrame(f,site,ROOT_TARGET,3,true,v(2,ROOT_ALLOC,144,8,ROOT_TARGET,A),cleanupN(),false,fpA);
                check(++allocation[0]==1,"parent allocation once");m.events.add(e("PCALL",site,ROOT_TARGET));m.writeDword(MARK+4,0x22334455);
                return offered(B,cleanupN(),I+0x3728319L,P-0x48,true,fpB);
            }
            throw new AssertionError("parent must stop before DBDB/count commit/172: "+Long.toHexString(site));
        };
        Element150Fp643Api.Calls lowerCalls=f->{
            long site=f.call().callSiteRva();
            if(site==0x37295FBL) {
                lowerFrame(f,site,0x21A5050,v(A16,NEW+0x10,OLD+0x10,B.r8Bits(),B.r9Bits(),B),true,fpB);
                check(++lower[0]==1,"150 first lower once and first");m.events.add(e("LCALL",site,0x21A5050));
                m.writeQword(NEW+0x28,ALIAS0);m.writeQword(NEW+0x30,ALIAS1);m.writeDword(OLD+0x40,CHANGED_TAIL);m.writeByte(OLD+0x44,CHANGED_FLAG);m.writeDword(MARK+8,0x33445566);
                return offered(C,lowerN(),I+0x3729600L,P-0x78,false,fpC);
            }
            if(site==0x3729620L) {
                lowerFrame(f,site,0xB2EEE0,secondV(),false,fpC);
                check(++lower[0]==2,"150 second lower once and second");m.events.add(e("LCALL",site,0xB2EEE0));
                check(m.readQword(NEW+0x28)==0,"source overwrote first callback alias0");
                check(m.readQword(NEW+0x30)==0,"source overwrote first callback alias1");
                check(m.readQword(NEW+0x38)==A4,"source writes second allocator");
                check(m.readDword(OLD+0x40)==CHANGED_TAIL&&m.readUnsignedByte(OLD+0x44)==CHANGED_FLAG,"sameMemory retains first callback source aliases");
                m.writeDword(MARK+12,0x44556677);
                if(stoppedCase)return stop;
                m.writeQword(P-0x50,POISON);
                // This complete offer passes the ancestor parent578 guard, while violating the actual150 lower frame.
                var bad=offered(bank(0xE00,0xE01),parentConstructN(),I+0x3728340L,P-0x48,true,QueueFp604Api.Mxcsr.unknown());
                check(reachedParent[0]!=null,"actual parent frame already checked against source constants");
                reachedParent[0].checkNormalReturn(bad.base()); // prove an ancestor guard alone cannot reject this offer
                return bad;
            }
            throw new AssertionError("unknown150 lower port");
        };
        var bound=EmbeddedElementsKnownConstruct644.bind(m,budget,
                f->{throw new AssertionError("no172 Range16 entry reached");},
                f->{throw new AssertionError("no COPY tail reached");},
                f->{throw new AssertionError("no172 Add4 entry reached");},lowerCalls,foreign);
        EmbeddedElementsFp637.Calls wrapped=f->{
            if(f.original().call().callSiteRva()!=0x372833BL)return bound.invoke(f);
            parentFrame(f,0x372833B,0x37295B0,5,false,v(NEW,NEW,OLD,B.r8Bits(),B.r9Bits(),B),parentConstructN(),true,fpB);
            check(++construct[0]==1,"first actual parent150 CALL once");reachedParent[0]=f.original();m.events.add(e("PCONSTRUCT",0x372833B,0x37295B0));
            var offered=bound.invoke(f);
            check(stoppedCase&&offered==stop,"actual643/644 returns the same explicit Stopped identity");
            m.events.add(e("PSTOP",0x372833B,0x3729620));return offered;
        };
        boolean rejected=false;
        try {
            var outcome=EmbeddedElementsFp637.execute(input(D,S,true,incoming,budget),m,wrapped);
            check(stoppedCase&&outcome==stop,"whole637 private carrier preserves exact Stopped object");
        } catch(IllegalArgumentException failure) {
            check(!stoppedCase&&"Return RIP mismatch".equals(failure.getMessage()),"original643 badRIP guard before post-state application");rejected=true;
        }
        check(stoppedCase?!rejected:rejected,"expected terminal kind");
        check(cleanup[0]==1&&allocation[0]==1&&construct[0]==1&&lower[0]==2,"complete once-only new wholeparent growth prefix");
        List<Event> expected=new ArrayList<>();parentPrefix(expected);constructPrefix(expected);
        if(stoppedCase)add(expected,"PSTOP",0x372833B,0x3729620);else add(expected,"W64",P-0x50,POISON);
        fullTraceAndRam(m,expected,initial,stoppedCase?"actual150 second-lower Stopped":"actual150 second-lower badRIP");
    }
    public static void secondLowerStoppedAfterAliasOverwrite(){run(true);}
    public static void secondLowerBadRipAfterParentReturnAlias(){run(false);}
    public static int verify(){secondLowerStoppedAfterAliasOverwrite();secondLowerBadRipAfterParentReturnAlias();return 2;}
    public static void main(String[] args){System.out.println(verify());}
}
