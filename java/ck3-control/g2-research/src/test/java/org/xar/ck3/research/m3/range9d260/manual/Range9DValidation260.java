package org.xar.ck3.research.m3.range9d260.manual;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.range9d260.Range9DFp260Api;
import org.xar.ck3.research.m3.range9d260.Range9DFullState260;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Manual software witness for the complete represented 126-byte protocol. */
public final class Range9DValidation260 {
    private Range9DValidation260() { }
    private static final long IMAGE=0x140000000L, SP=0x70001000L, RETURN=IMAGE+0xADD21EL;
    private static int checks,scenarios;
    private static void check(boolean value) {checks++;if(!value)throw new AssertionError("260 check "+checks);}
    private static Bits128 bits(long tag,int k) {return new Bits128(tag+k,0xE000000000000000L+tag+k);}
    private static VolatileBits offeredV(int ordinal) {
        long tag=0x8100000000000000L+ordinal*0x1000L;
        return new VolatileBits(tag+1,tag+2,tag+3,tag+4,tag+5,tag+6,tag+7,
            bits(tag,0),bits(tag,1),bits(tag,2),bits(tag,3),bits(tag,4),bits(tag,5));
    }
    private static final NonvolatileBits ENTRY_N=new NonvolatileBits(0x1111,0x2222,0x3333,0x4444,0x5555,0x6666,0x7777,0x8888,bits(0x9999,6));
    private record Event(String kind,long address,long value) { }
    private static final class Fixture {
        final long begin,middle,end;
        final Map<Long,Long> ram=new HashMap<>();final List<Event> events=new ArrayList<>();
        final List<Range9DFp260Api.CallFrame> frames=new ArrayList<>();
        final List<Normal> normalOffers=new ArrayList<>();
        final Mxcsr entryFp=Mxcsr.unknown();
        final Mxcsr[] postFp={new Mxcsr(0x80,0x80),new Mxcsr(0x20,0x20),new Mxcsr(0x40,0x40)};
        final boolean[] postDf={false,true,false};
        final VolatileBits entryV;
        final Range9DFp260Api.Memory memory;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{throw new AssertionError("260 body has no loop");};
        int stopAt,throwAt,badAt,badField,aliasAt;
        final RuntimeException failure=new IllegalStateException("260 callback marker");
        Stopped offeredStop;
        Fixture(long begin,long middle,long end) {
            this.begin=begin;this.middle=middle;this.end=end;
            entryV=new VolatileBits(0xAABBCCDDEEFF0011L,begin,middle,end,0xBEEF000000000009L,
                0xBEEF00000000000AL,0xBEEF00000000000BL,bits(0x101,0),bits(0x101,1),bits(0x101,2),bits(0x101,3),bits(0x101,4),bits(0x101,5));
            ram.put(SP,RETURN);
            memory=(Range9DFp260Api.Memory)Proxy.newProxyInstance(Range9DFp260Api.Memory.class.getClassLoader(),
                new Class<?>[]{Range9DFp260Api.Memory.class},(proxy,method,args)->{
                    String name=method.getName();
                    if(method.getDeclaringClass()==Object.class) {
                        if(name.equals("hashCode"))return Integer.valueOf(System.identityHashCode(proxy));
                        if(name.equals("equals"))return Boolean.valueOf(proxy==args[0]);
                        if(name.equals("toString"))return "260 owned finite QWORD RAM";
                    }
                    if(args==null||args.length==0)throw new AssertionError("260 unsupported "+name);
                    long a=((Long)args[0]).longValue();
                    if(name.equals("readQword")) {
                        Long value=ram.get(a);if(value==null)throw new AssertionError("260 unseeded "+Long.toHexString(a));
                        events.add(new Event("R",a,value.longValue()));return value;
                    }
                    if(name.equals("writeQword")) {long value=((Long)args[1]).longValue();events.add(new Event("W",a,value));ram.put(a,value);return null;}
                    throw new AssertionError("260 unsupported "+name);
                });
        }
        Outcome respond(Range9DFp260Api.CallFrame frame) {
            frames.add(frame);int ordinal=frames.size();
            if(throwAt==ordinal)throw failure;
            if(stopAt==ordinal) {
                offeredStop=new Stopped(StopReason.MISSING_POST_STATE,new Snapshot(frame.childEntry(),frame.call().callSiteRva(),frame.directionFlagSet(),frame.preMxcsr()),0,frame.call().callSiteRva());
                return offeredStop;
            }
            if(aliasAt==ordinal) {ram.put(SP+8,0xAAAA111122223333L);ram.put(SP+0x10,0xBBBB444455556666L);ram.put(SP-8,0xCCCC777788889999L);ram.put(SP,RETURN+0x40);}
            long rip=frame.returnRipBits()+(badAt==ordinal&&badField==0?1:0);
            long caller=frame.call().rspBits()+(badAt==ordinal&&badField==1?8:0);
            NonvolatileBits nv=frame.call().nonvolatileBits();
            if(badAt==ordinal&&badField==2)nv=new NonvolatileBits(nv.rbxBits()+1,nv.rbpBits(),nv.rsiBits(),nv.rdiBits(),nv.r12Bits(),nv.r13Bits(),nv.r14Bits(),nv.r15Bits(),nv.xmm6());
            Normal offer=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(offeredV(ordinal),rip,caller,nv),postDf[ordinal-1]),postFp[ordinal-1]);
            normalOffers.add(offer);return offer;
        }
        Outcome run() {
            scenarios++;
            Input input=new Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,entryV,ENTRY_N),true,budget),entryFp);
            return Range9DFullState260.execute(input,memory,this::respond);
        }
    }
    private static VolatileBits expectedV(VolatileBits source,long ax,long cx,long dx) {
        return new VolatileBits(ax,cx,dx,source.r8Bits(),source.r9Bits(),source.r10Bits(),source.r11Bits(),
            source.xmm0(),source.xmm1(),source.xmm2(),source.xmm3(),source.xmm4(),source.xmm5());
    }
    private static NonvolatileBits workingN(Fixture h) {
        return new NonvolatileBits(h.end,ENTRY_N.rbpBits(),h.middle,h.begin,ENTRY_N.r12Bits(),
            ENTRY_N.r13Bits(),ENTRY_N.r14Bits(),ENTRY_N.r15Bits(),ENTRY_N.xmm6());
    }
    private static List<Event> prefix(int calls) {
        List<Event> e=new ArrayList<>(List.of(new Event("W",SP+8,0x1111),
            new Event("W",SP+0x10,0x3333),new Event("W",SP-8,0x4444)));
        long[] returns={IMAGE+0x9D099D,IMAGE+0x9D09A8,IMAGE+0x9D09B3};
        for(int k=0;k<calls;k++)e.add(new Event("W",SP-0x30,returns[k]));
        return e;
    }
    private static void verifyFrames(Fixture h,int count) {
        check(h.frames.size()==count);
        long[] sites={0x9D0998,0x9D09A3,0x9D09AE};
        long[] returns={IMAGE+0x9D099D,IMAGE+0x9D09A8,IMAGE+0x9D09B3};
        for(int k=0;k<count;k++) {
            var f=h.frames.get(k);var c=f.call();
            check(c.callSiteRva()==sites[k]);check(c.targetBits()==0x4220AA4L);
            check(c.kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA);
            check(c.rspBits()==SP-0x28);check(f.childEntry().rspBits()==SP-0x30);
            check(f.childEntry().imageBaseBits()==IMAGE);check(f.instructionLength()==5);
            check(f.returnRipBits()==returns[k]);check(c.nonvolatileBits().equals(workingN(h)));
            check(f.childEntry().nonvolatileBits().equals(c.nonvolatileBits()));
            VolatileBits expected=k==0?h.entryV:expectedV(offeredV(k),offeredV(k).raxBits(),k==1?h.middle:h.begin,h.end);
            check(c.volatileBits().equals(expected));check(f.childEntry().volatileBits().equals(expected));
            check(f.directionFlagSet()==(k==0||k==2));
            check(f.preMxcsr()==(k==0?h.entryFp:h.postFp[k-1]));
        }
    }
    private static Normal requireNormal(Outcome o) {
        check(o instanceof Normal);return (Normal)o;
    }
    private static void normalCalls260() {
        long[][] rows={{0x1000,0x1014,0x1050,0x103c},{0x2000,0x2040,0x2010,0x1fd0}};
        for(long[] row:rows) {
            Fixture h=new Fixture(row[0],row[1],row[2]);Normal n=requireNormal(h.run());
            verifyFrames(h,3);check(h.normalOffers.size()==3);
            var r=n.base().normalReturn();
            check(r.volatileBits().equals(expectedV(offeredV(3),row[3],offeredV(3).rcxBits(),offeredV(3).rdxBits())));
            check(r.nonvolatileBits().equals(ENTRY_N));check(r.callerRspBits()==SP+8);check(r.returnRipBits()==RETURN);
            check(!n.base().postDirectionFlagSet());check(n.postMxcsr()==h.postFp[2]);
            List<Event> e=prefix(3);e.addAll(List.of(new Event("R",SP+0x10,0x3333),new Event("R",SP+8,0x1111),
                new Event("R",SP-8,0x4444),new Event("R",SP,RETURN)));
            check(h.events.equals(e));check(h.ram.get(SP-0x30).longValue()==IMAGE+0x9D09B3);
        }
    }
    private static void earlyAndAlias260() {
        long[][] rows={{0x1000,0x1000,0x1040,0x1040},{0x1000,0x1040,0x1040,0x1000},{0x1000,0x1000,0x1000,0x1000}};
        for(long[] row:rows) {
            Fixture h=new Fixture(row[0],row[1],row[2]);Normal n=requireNormal(h.run());
            check(h.frames.isEmpty());check(h.normalOffers.isEmpty());
            var r=n.base().normalReturn();check(r.volatileBits().equals(expectedV(h.entryV,row[3],row[0],row[1])));
            check(r.nonvolatileBits().equals(ENTRY_N));check(r.returnRipBits()==RETURN);check(r.callerRspBits()==SP+8);
            check(n.base().postDirectionFlagSet());check(n.postMxcsr()==h.entryFp);
            List<Event> e=prefix(0);e.addAll(List.of(new Event("R",SP+8,0x1111),new Event("R",SP+0x10,0x3333),
                new Event("R",SP-8,0x4444),new Event("R",SP,RETURN)));
            check(h.events.equals(e));
        }
        Fixture h=new Fixture(0x1000,0x1014,0x1050);h.aliasAt=3;Normal n=requireNormal(h.run());verifyFrames(h,3);
        var r=n.base().normalReturn();
        check(r.nonvolatileBits().equals(new NonvolatileBits(0xAAAA111122223333L,0x2222,
            0xBBBB444455556666L,0xCCCC777788889999L,0x5555,0x6666,0x7777,0x8888,ENTRY_N.xmm6())));
        check(r.returnRipBits()==RETURN+0x40);check(r.callerRspBits()==SP+8);
        check(r.volatileBits().equals(expectedV(offeredV(3),0x103c,offeredV(3).rcxBits(),offeredV(3).rdxBits())));
        check(n.postMxcsr()==h.postFp[2]);check(!n.base().postDirectionFlagSet());
        List<Event> e=prefix(3);e.addAll(List.of(new Event("R",SP+0x10,0xBBBB444455556666L),
            new Event("R",SP+8,0xAAAA111122223333L),new Event("R",SP-8,0xCCCC777788889999L),new Event("R",SP,RETURN+0x40)));
        check(h.events.equals(e));
    }
    private static void stoppedAt260(int ordinal) {
        Fixture h=new Fixture(0x1000,0x1014,0x1050);h.stopAt=ordinal;Outcome actual=h.run();
        check(actual==h.offeredStop);verifyFrames(h,ordinal);check(h.normalOffers.size()==ordinal-1);
        check(h.events.equals(prefix(ordinal)));var f=h.frames.get(ordinal-1);var s=h.offeredStop;
        check(s.reason()==StopReason.MISSING_POST_STATE);check(s.raisedConditionBits()==0);
        check(s.originCallSiteRva()==f.call().callSiteRva());check(s.snapshot().currentState()==f.childEntry());
        check(s.snapshot().instructionRva()==f.call().callSiteRva());check(s.snapshot().mxcsr()==f.preMxcsr());
        check(s.snapshot().directionFlagSet()==f.directionFlagSet());
        Fixture t=new Fixture(0x1000,0x1014,0x1050);t.throwAt=ordinal;
        try {t.run();throw new AssertionError("missing callback exception");}
        catch(RuntimeException x) {check(x==t.failure);}
        verifyFrames(t,ordinal);check(t.normalOffers.size()==ordinal-1);check(t.events.equals(prefix(ordinal)));
    }
    private static void stoppedFirst260() {stoppedAt260(1);}
    private static void stoppedSecond260() {stoppedAt260(2);}
    private static void stoppedThird260() {stoppedAt260(3);}
    private static void invalidReturns260() {
        for(int ordinal=1;ordinal<=3;ordinal++)for(int field=0;field<3;field++) {
            Fixture h=new Fixture(0x1000,0x1014,0x1050);h.badAt=ordinal;h.badField=field;
            try {h.run();throw new AssertionError("missing normal-return rejection");}
            catch(IllegalArgumentException expected) {check(true);}
            verifyFrames(h,ordinal);check(h.normalOffers.size()==ordinal);check(h.events.equals(prefix(ordinal)));
        }
        Fixture h=new Fixture(0x1000,0x1014,0x1050);scenarios++;
        Input input=new Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,h.entryV,ENTRY_N),true,h.budget),h.entryFp);
        try {Range9DFullState260.execute(input,h.memory,frame->{h.frames.add(frame);return null;});throw new AssertionError("missing null rejection");}
        catch(NullPointerException expected) {check(true);}
        verifyFrames(h,1);check(h.events.equals(prefix(1)));
    }
    public static void main(String[] args) {
        normalCalls260();earlyAndAlias260();
        stoppedFirst260();stoppedSecond260();stoppedThird260();invalidReturns260();
        System.out.println("PASS groups=2 scenarios="+scenarios+" checks="+checks);
    }

}
