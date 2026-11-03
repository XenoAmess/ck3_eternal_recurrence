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

/** Two NEW whole322 -> actual93 positive-clear prefixes. Independent SOURCE-ORACLE645-04
 * was frozen first. New645 wrapper body and other-owner direct645 Test were not read. */
public final class ParentClearBoundary645 {
    private ParentClearBoundary645() { }
    private static final long I=IMAGE,P=SP,D=0x8000000000001100L,S=0xF000000000002200L;
    private static final long OLD=0x30000L,SE=0x40000L,STALE_VT=0x80000L,FRESH_VT=0x81000L;
    private static final long STALE_TARGET=0x82000L,FRESH_TARGET=0x83000L,MARK=0x84000L;
    private static final long POISON=0xF123456789ABCDEFL;
    private static final NonvolatileBits N0=initialN();
    private static final VolatileBits V0=initialV(D,S);
    /** Same outer memory object supplies both the full parent and actual645 clear contracts. */
    private interface Memory extends FullCopy437Api.Memory,EmbeddedElementsFp637.Memory { }
    private static final class Ram implements Memory {
        private final ParentFixture642.Ram owned=new ParentFixture642.Ram();
        final Map<Long,Byte> bytes=owned.bytes;final List<Event> events=owned.events;
        void seed(long p,int width,long value){owned.seed(p,width,value);}
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
    private static NonvolatileBits parentN() {
        return new NonvolatileBits(2,SE,D,N0.rdiBits(),N0.r12Bits(),N0.r13Bits(),N0.r14Bits(),N0.r15Bits(),N0.xmm6());
    }
    private static NonvolatileBits destructorN() {
        return new NonvolatileBits(OLD,SE,D,1,N0.r12Bits(),N0.r13Bits(),N0.r14Bits(),N0.r15Bits(),N0.xmm6());
    }
    private static VolatileBits destructorV() {
        return new VolatileBits(FRESH_VT,OLD,0,V0.r8Bits(),V0.r9Bits(),V0.r10Bits(),V0.r11Bits(),V0.xmm0(),V0.xmm1(),V0.xmm2(),V0.xmm3(),V0.xmm4(),V0.xmm5());
    }
    private static VolatileBits offeredV() {
        return new VolatileBits(0xE01,0xE02,0xE03,0xE04,0xE05,0xE06,0xE07,x(0xE08),x(0xE09),x(0xE0A),x(0xE0B),x(0xE0C),x(0xE0D));
    }
    private static void frame(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
            boolean actualDf,QueueFp604Api.Mxcsr actualFp,int actualLength,long actualRip,
            long site,long target,int length,boolean indirect,long pre,VolatileBits vv,NonvolatileBits nn,
            QueueFp604Api.Mxcsr fp,String why) {
        var kind=indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
        check(call.equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,vv,nn)),why+" complete Call V/N");
        check(child.equals(new GovernmentCrtBoundary185Api.Entry(I,pre-8,vv,nn)),why+" complete child Entry");
        check(actualLength==length&&actualRip==I+site+length&&actualDf&&actualFp==fp,why+" instruction length/returnRIP/DF/current MXCSR object");
    }
    private static void fill(Ram m,long p,int width,int salt) {
        for(int j=0;j<width;j++)m.seed(p+j,1,(salt+37*j)&255);
    }
    private static Ram seed() {
        Ram m=new Ram();fill(m,P-0x100,0x150,0x11);fill(m,D,0x20,0x22);fill(m,S,0x20,0x33);
        fill(m,OLD,0x90,0x44);fill(m,SE,0x90,0x55);fill(m,MARK,0x20,0x66);
        m.seed(P,8,RIP);m.seed(D,8,OLD);m.seed(D+8,4,1);m.seed(D+0xC,4,1);
        m.seed(S,8,SE);m.seed(S+0xC,4,2);m.seed(OLD,8,STALE_VT);
        m.seed(STALE_VT,8,STALE_TARGET);m.seed(FRESH_VT,8,0xDEADFADEL);return m;
    }
    private static void add(List<Event> t,String kind,long p,long a){t.add(e(kind,p,a));}
    /** Literal322 prefix and the first actual93 virtual CALL, with owned budget alias effects. */
    private static List<Event> prefix() {
        List<Event> t=new ArrayList<>();
        add(t,"W64",P+8,N0.rbxBits());add(t,"W64",P+0x10,N0.rbpBits());
        add(t,"W64",P+0x18,N0.rsiBits());add(t,"W64",P+0x20,N0.rdiBits());
        add(t,"W64",P-8,N0.r12Bits());add(t,"W64",P-0x10,N0.r14Bits());add(t,"W64",P-0x18,N0.r15Bits());
        add(t,"R32",S+0xC,2);add(t,"R64",S,SE);add(t,"W64",P-0x50,I+0x37282E6L);
        add(t,"PCLEAR",0x37282E1,0x889780);
        add(t,"W64",P-0x40,D);add(t,"W64",P-0x58,N0.rdiBits());add(t,"R32",D+0xC,1);
        add(t,"W64",P-0x48,2);add(t,"R64",D,OLD);add(t,"BUDGET",0x8897A0,OLD);
        add(t,"W64",OLD,FRESH_VT);add(t,"W64",FRESH_VT,FRESH_TARGET);
        add(t,"R64",OLD,FRESH_VT);add(t,"R64",FRESH_VT,FRESH_TARGET);add(t,"W64",P-0x80,I+0x8897AAL);
        add(t,"DESTRUCTOR",0x8897A8,FRESH_TARGET);add(t,"W32",MARK,0x778899AA);return t;
    }
    private static void fullTraceAndRam(Ram m,List<Event> expected,Map<Long,Byte> initial,String why) {
        check(m.events.equals(expected),why+" complete ordered parent/93/budget/callback trace: expected="+expected+" actual="+m.events);
        Map<Long,Byte> ram=new HashMap<>(initial);
        for(Event e:expected) {
            int width=switch(e.kind()){case "W64"->8;case "W32"->4;default->0;};
            for(int j=0;j<width;j++)ram.put(e.address()+j,(byte)(e.a()>>>(8*j)));
        }
        check(m.bytes.equals(ram),why+" all owned RAM/untouched padding/stack/partial callback effects");
    }
    private static void run(boolean stoppedCase) {
        Ram m=seed();Map<Long,Byte> initial=new HashMap<>(m.bytes);
        var fp=new QueueFp604Api.Mxcsr(0x4000,0x4000);
        var stop=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,P-0x80,destructorV(),destructorN()),0xA01000,true,fp),0,0x8897A8);
        int[] parentSeen={0},budgetSeen={0},destructorSeen={0};
        EmbeddedElements578Api.CallFrame[] reachedParent={null};
        GovernmentCrtBoundary185Api.LoopBudget budget=(pc,cursor)->{
            check(pc==0x8897A0L&&cursor==OLD&&++budgetSeen[0]==1,"exactly one actual93 loop budget before first loop read");
            m.events.add(e("BUDGET",pc,cursor));m.writeQword(OLD,FRESH_VT);m.writeQword(FRESH_VT,FRESH_TARGET);
        };
        EmbeddedClearFp645Api.Calls destructor=f->{
            var o=f.original();
            frame(o.call(),o.childEntry(),o.directionFlagSet(),f.preMxcsr(),o.instructionLength(),o.returnRipBits(),
                    0x8897A8,FRESH_TARGET,2,true,P-0x78,destructorV(),destructorN(),fp,"actual93 indirect destructor");
            check(++destructorSeen[0]==1,"one indirect destructor only");m.events.add(e("DESTRUCTOR",0x8897A8,FRESH_TARGET));m.writeDword(MARK,0x778899AA);
            if(stoppedCase)return stop;
            m.writeQword(P-0x50,POISON);
            // Ancestor-parent-valid full offer, deliberately invalid for this actual destructor frame.
            var bad=new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                    offeredV(),I+0x37282E6L,P-0x48,parentN()),false),QueueFp604Api.Mxcsr.unknown());
            check(reachedParent[0]!=null,"source-checked parent frame reached first");
            reachedParent[0].checkNormalReturn(bad.base()); // an outer parent guard alone cannot reject this offer
            return bad;
        };
        EmbeddedElementsFp637.Calls forbidden=f->{throw new AssertionError("no parent allocator/150/172/fallback may be reached");};
        var bound=EmbeddedClearWithFp645.bindClear(m,budget,destructor,forbidden);
        EmbeddedElementsFp637.Calls wrapped=f->{
            var o=f.original();
            frame(o.call(),o.childEntry(),o.directionFlagSet(),f.preMxcsr(),o.instructionLength(),o.returnRipBits(),
                    0x37282E1,0x889780,5,false,P-0x48,V0,parentN(),fp,"parent actual cleanup");
            check(++parentSeen[0]==1,"only parent actual cleanup reached");reachedParent[0]=o;m.events.add(e("PCLEAR",0x37282E1,0x889780));
            var result=bound.invoke(f);
            check(stoppedCase&&result==stop,"645 loop carrier and bindClear preserve same Stopped");
            m.events.add(e("PCLEAR_STOP",0x37282E1,0x8897A8));return result;
        };
        boolean rejected=false;
        try {
            var result=EmbeddedElementsFp637.execute(input(D,S,true,fp,budget),m,wrapped);
            check(stoppedCase&&result==stop,"outer637 parent carrier returns exact same explicit Stopped");
        } catch(IllegalArgumentException failure) {
            check(!stoppedCase&&"Return RIP mismatch".equals(failure.getMessage()),"actual destructor badNR rejected before application/clear or parent continuation");rejected=true;
        }
        check(stoppedCase?!rejected:rejected,"expected terminal kind");
        check(parentSeen[0]==1&&budgetSeen[0]==1&&destructorSeen[0]==1,"complete once-only new parent-clear prefix");
        List<Event> expected=prefix();
        if(stoppedCase)add(expected,"PCLEAR_STOP",0x37282E1,0x8897A8);else add(expected,"W64",P-0x50,POISON);
        fullTraceAndRam(m,expected,initial,stoppedCase?"parent clear sameStopped":"parent clear badAncestorNR");
    }
    public static void parentCleanupStoppedAtFreshDestructor(){run(true);}
    public static void parentCleanupBadAncestorReturn(){run(false);}
    public static int verify(){parentCleanupStoppedAtFreshDestructor();parentCleanupBadAncestorReturn();return 2;}
    public static void main(String[] args){System.out.println(verify());}
}
