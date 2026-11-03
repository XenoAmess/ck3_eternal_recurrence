package org.xar.ck3.research.m3.rangereverse261.manual;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.rangereverse261.RangeReverse261;
import org.xar.ck3.research.m3.range9d260.Range9DFp260Api;
import org.xar.ck3.research.m3.range9d260.Range9DFullState260;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.*;

/** Mechanical finite byte RAM. Target method slots are genuinely unimplemented. */
public final class RangeReverseValidation261 {
    private RangeReverseValidation261() { }
    private static final long IMAGE=0x140000000L,SP=0x72001000L,ARRAY=0x62000000L,RETURN=IMAGE+0xADD21EL;
    private static int checks,scenarios;
    private static void check(boolean b) {checks++;if(!b)throw new AssertionError("261 check "+checks);}
    private static Bits128 bits(long k) {return new Bits128(0x8000000000000000L+k,0xE000000000000000L+k);}
    private static final NonvolatileBits N=new NonvolatileBits(0x1111,0x2222,0x3333,0x4444,0x5555,0x6666,0x7777,0x8888,bits(6));
    private record Event(String op,long address) { }
    private static final class Fixture {
        final int count,split;
        final Map<Long,Byte> bytes=new HashMap<>();final List<Event> events=new ArrayList<>();
        final Mxcsr fp=Mxcsr.unknown();final VolatileBits v;
        final RangeReverse261.Memory memory;final GovernmentCrtBoundary185Api.LoopBudget budget;
        final RuntimeException failure=new IllegalStateException("261 finite port marker");
        int calls,steps,zeros,badRetAt,failBudgetAt;boolean failVzero;
        Fixture(int count,int split,int features) {
            this.count=count;this.split=split;
            v=new VolatileBits(0xAABBCCDDEEFF0011L,ARRAY,ARRAY+split*4L,ARRAY+count*4L,
                0xF000000000000009L,0xF00000000000000AL,0xF00000000000000BL,bits(0),bits(1),bits(2),bits(3),bits(4),bits(5));
            for(int i=0;i<count;i++)rawWrite(ARRAY+i*4L,4,0x50000000L+i);
            rawWrite(SP,8,RETURN);rawWrite(IMAGE+0x542F09CL,4,features);
            budget=(pc,guard)->{steps++;events.add(new Event("B",pc));if(steps==failBudgetAt)throw failure;if(steps>1000)throw new AssertionError("261 bounded budget");};
            memory=(RangeReverse261.Memory)Proxy.newProxyInstance(RangeReverse261.Memory.class.getClassLoader(),
                new Class<?>[]{RangeReverse261.Memory.class},(proxy,method,args)->{
                    String op=method.getName();
                    if(method.getDeclaringClass()==Object.class) {
                        if(op.equals("hashCode"))return Integer.valueOf(System.identityHashCode(proxy));
                        if(op.equals("equals"))return Boolean.valueOf(proxy==args[0]);
                        if(op.equals("toString"))return "261 finite owned byte RAM";
                    }
                    if(op.equals("vzeroUpper")) {zeros++;events.add(new Event("Z",0));if(failVzero)throw failure;return null;}
                    if(args==null||args.length==0)throw new AssertionError("261 unsupported "+op);
                    long a=((Long)args[0]).longValue();
                    if(op.equals("readDword")) {events.add(new Event("RD",a));return Integer.valueOf((int)rawRead(a,4));}
                    if(op.equals("writeDword")) {events.add(new Event("WD",a));rawWrite(a,4,Integer.toUnsignedLong(((Integer)args[1]).intValue()));return null;}
                    if(op.equals("readQword")) {events.add(new Event("RQ",a));long q=rawRead(a,8);return Long.valueOf(a==SP-0x30&&calls==badRetAt?q+1:q);}
                    if(op.equals("writeQword")) {events.add(new Event("WQ",a));rawWrite(a,8,((Long)args[1]).longValue());if(a==SP-0x30)calls++;return null;}
                    if(op.equals("read128")) {events.add(new Event("R128",a));return new Bits128(rawRead(a,8),rawRead(a+8,8));}
                    if(op.equals("write128")) {events.add(new Event("W128",a));Bits128 b=(Bits128)args[1];rawWrite(a,8,b.lowBits());rawWrite(a+8,8,b.highBits());return null;}
                    if(op.equals("read256")) {events.add(new Event("R256",a));return new FullCopy437Api.Bits256(new Bits128(rawRead(a,8),rawRead(a+8,8)),new Bits128(rawRead(a+16,8),rawRead(a+24,8)));}
                    if(op.equals("write256")) {events.add(new Event("W256",a));FullCopy437Api.Bits256 b=(FullCopy437Api.Bits256)args[1];rawWrite(a,8,b.low().lowBits());rawWrite(a+8,8,b.low().highBits());rawWrite(a+16,8,b.high().lowBits());rawWrite(a+24,8,b.high().highBits());return null;}
                    throw new AssertionError("261 unsupported "+op);
                });
        }
        long rawRead(long a,int width) {
            long q=0;for(int k=0;k<width;k++) {Byte b=bytes.get(a+k);if(b==null)throw new AssertionError("261 unseeded "+Long.toHexString(a+k));q|=Byte.toUnsignedLong(b.byteValue())<<(8*k);}return q;
        }
        void rawWrite(long a,int width,long q) {for(int k=0;k<width;k++)bytes.put(a+k,Byte.valueOf((byte)(q>>>(8*k))));}
        int peek(int i) {return (int)rawRead(ARRAY+i*4L,4);}
        long count(String op) {return events.stream().filter(x->x.op().equals(op)).count();}
        Input input() {return new Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,v,N),true,budget),fp);}
        Outcome run() {scenarios++;return RangeReverse261.execute(input(),memory);}
    }
    private static Bits128 lanes(int a,int b,int c,int d) {
        return new Bits128(((0x50000000L+b)<<32)|(0x50000000L+a),((0x50000000L+d)<<32)|(0x50000000L+c));
    }
    private static Normal normal(Outcome outcome) {check(outcome instanceof Normal);return (Normal)outcome;}
    private static void row(Fixture h,int... indices) {
        check(indices.length==h.count);for(int k=0;k<indices.length;k++)check(h.peek(k)==0x50000000+indices[k]);
    }
    private static void fullState(Fixture h,Normal n,long ax,long cx,long dx,long r8,Bits128 x0,Bits128 x1,Bits128 x2,Bits128 x3) {
        var r=n.base().normalReturn();
        check(r.volatileBits().equals(new VolatileBits(ax,cx,dx,r8,h.v.r9Bits(),h.v.r10Bits(),h.v.r11Bits(),x0,x1,x2,x3,h.v.xmm4(),h.v.xmm5())));
        check(r.nonvolatileBits().equals(N));check(r.returnRipBits()==RETURN);check(r.callerRspBits()==SP+8);
        check(n.base().postDirectionFlagSet());check(n.postMxcsr()==h.fp);
        check(h.count("WQ")==6);check(h.count("RQ")==7);check(h.calls==3);
    }
    private static void directBinding261() {
        long[] sites={0x9D0998,0x9D09A3,0x9D09AE};
        for(int k=0;k<3;k++) {
            Fixture h=new Fixture(2,1,0);long ret=IMAGE+sites[k]+5;
            h.memory.writeQword(SP-0x30,ret); // actual preexisting owned CALL push, outside binding
            var directV=new VolatileBits(h.v.raxBits(),ARRAY,ARRAY+8,h.v.r8Bits(),h.v.r9Bits(),h.v.r10Bits(),h.v.r11Bits(),
                h.v.xmm0(),h.v.xmm1(),h.v.xmm2(),h.v.xmm3(),h.v.xmm4(),h.v.xmm5());
            var call=new GovernmentCrtBoundary185Api.Call(sites[k],GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4220AA4L,SP-0x28,directV,N);
            var child=new GovernmentCrtBoundary185Api.Entry(IMAGE,SP-0x30,directV,N);
            Mxcsr fp=k==0?Mxcsr.unknown():new Mxcsr(0x20,0x20);boolean df=k==1;
            var frame=new Range9DFp260Api.CallFrame(call,child,df,fp,5,ret);scenarios++;
            Normal n=normal(RangeReverse261.bind(h.memory,h.budget).invoke(frame));var r=n.base().normalReturn();
            row(h,1,0);check(r.returnRipBits()==ret);check(r.callerRspBits()==SP-0x28);check(r.nonvolatileBits().equals(N));
            check(r.volatileBits().equals(new VolatileBits(0x50000001L,0x50000000L,ARRAY+4,ARRAY+4,h.v.r9Bits(),h.v.r10Bits(),h.v.r11Bits(),h.v.xmm0(),h.v.xmm1(),h.v.xmm2(),h.v.xmm3(),h.v.xmm4(),h.v.xmm5())));
            check(n.base().postDirectionFlagSet()==df);check(n.postMxcsr()==fp);
            check(h.calls==1);check(h.count("WQ")==1);check(h.count("RQ")==1);check(h.count("RD")==2);check(h.count("WD")==2);
            check(h.steps==1);check(h.zeros==0);
            check(h.events.get(0).equals(new Event("WQ",SP-0x30)));check(h.events.get(h.events.size()-1).equals(new Event("RQ",SP-0x30)));
        }
    }
    private static void scalarWhole261() {
        Fixture h=new Fixture(3,1,0);Normal n=normal(h.run());row(h,1,2,0);
        fullState(h,n,ARRAY+8,0x50000000L,ARRAY+4,ARRAY+4,h.v.xmm0(),h.v.xmm1(),h.v.xmm2(),h.v.xmm3());
        check(h.steps==4);check(h.count("RD")==4);check(h.count("WD")==4);check(h.count("R128")==0);check(h.count("R256")==0);check(h.zeros==0);
        Fixture other=new Fixture(5,2,0);Normal z=normal(other.run());row(other,2,3,4,0,1);
        check(z.base().normalReturn().volatileBits().raxBits()==ARRAY+12);check(z.base().normalReturn().nonvolatileBits().equals(N));
        check(z.base().normalReturn().returnRipBits()==RETURN);check(z.base().normalReturn().callerRspBits()==SP+8);check(z.postMxcsr()==other.fp);
        for(int split:new int[]{0,3}) {
            Fixture e=new Fixture(3,split,0x20);Normal early=normal(e.run());row(e,0,1,2);var r=early.base().normalReturn();
            check(r.volatileBits().equals(new VolatileBits(split==0?ARRAY+12:ARRAY,ARRAY,ARRAY+split*4L,ARRAY+12,
                e.v.r9Bits(),e.v.r10Bits(),e.v.r11Bits(),e.v.xmm0(),e.v.xmm1(),e.v.xmm2(),e.v.xmm3(),e.v.xmm4(),e.v.xmm5())));
            check(r.nonvolatileBits().equals(N));check(r.returnRipBits()==RETURN);check(r.callerRspBits()==SP+8);
            check(early.postMxcsr()==e.fp);check(early.base().postDirectionFlagSet());
            check(e.calls==0);check(e.steps==0);check(e.zeros==0);check(e.count("RD")==0);check(e.count("WQ")==3);check(e.count("RQ")==4);
        }
    }
    private static void sseWhole261() {
        Fixture h=new Fixture(16,8,0);Normal n=normal(h.run());row(h,8,9,10,11,12,13,14,15,0,1,2,3,4,5,6,7);
        fullState(h,n,ARRAY+32,0x7ffffffffffffff0L,ARRAY+32,ARRAY+32,lanes(12,13,14,15),lanes(15,14,13,12),lanes(0,1,2,3),h.v.xmm3());
        check(h.steps==4);check(h.count("RD")==1);check(h.count("WD")==0);check(h.count("R128")==8);check(h.count("W128")==8);
        check(h.count("R256")==0);check(h.count("W256")==0);check(h.zeros==0);
        check(h.events.stream().filter(e->e.op().equals("RD")).toList().equals(List.of(new Event("RD",IMAGE+0x542F09CL))));
        List<Event> first=h.events.stream().filter(e->e.op().endsWith("128")).limit(4).toList();
        check(first.equals(List.of(new Event("R128",ARRAY),new Event("R128",ARRAY+16),new Event("W128",ARRAY),new Event("W128",ARRAY+16))));
    }
    private static void avxWhole261() {
        Fixture h=new Fixture(32,16,0x20);Normal n=normal(h.run());
        row(h,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15);
        fullState(h,n,ARRAY+64,0x7fffffffffffffe0L,ARRAY+64,ARRAY+64,h.v.xmm0(),lanes(27,26,25,24),lanes(24,25,26,27),lanes(0,1,2,3));
        check(h.steps==4);check(h.count("RD")==3);check(h.count("WD")==0);check(h.count("R256")==8);check(h.count("W256")==8);
        check(h.count("R128")==0);check(h.count("W128")==0);check(h.zeros==3);check(h.count("Z")==3);
        List<Event> first=h.events.stream().filter(e->e.op().endsWith("256")).limit(4).toList();
        check(first.equals(List.of(new Event("R256",ARRAY),new Event("R256",ARRAY+32),new Event("W256",ARRAY),new Event("W256",ARRAY+32))));
    }
    private static void retFailures261() {
        for(int ordinal=1;ordinal<=3;ordinal++) {
            Fixture h=new Fixture(3,1,0);h.badRetAt=ordinal;
            try {h.run();throw new AssertionError("missing actual RET rejection");}
            catch(IllegalArgumentException expected) {check(true);}
            check(h.calls==ordinal);check(h.count("WQ")==3+ordinal);check(h.count("RQ")==ordinal);
            check(h.events.stream().filter(e->e.op().equals("RQ")).allMatch(e->e.address()==SP-0x30));
            check(h.events.get(h.events.size()-1).equals(new Event("RQ",SP-0x30)));
            check(h.rawRead(SP+8,8)==N.rbxBits());check(h.rawRead(SP+0x10,8)==N.rsiBits());check(h.rawRead(SP-8,8)==N.rdiBits());
            if(ordinal==1) {row(h,0,1,2);check(h.steps==1);check(h.count("WD")==0);}
            if(ordinal==2) {row(h,0,2,1);check(h.steps==2);check(h.count("WD")==2);}
            if(ordinal==3) {row(h,1,2,0);check(h.steps==4);check(h.count("WD")==4);}
        }
    }
    private static void budgetEffectFailures261() {
        Fixture b=new Fixture(3,1,0);b.failBudgetAt=1;
        try {b.run();throw new AssertionError("missing budget exception");}
        catch(RuntimeException e) {check(e==b.failure);}
        row(b,0,1,2);check(b.calls==1);check(b.steps==1);check(b.count("WQ")==4);check(b.count("RQ")==0);check(b.count("WD")==0);check(b.count("RD")==0);check(b.zeros==0);
        Fixture z=new Fixture(32,16,0x20);z.failVzero=true;
        try {z.run();throw new AssertionError("missing explicit upper-lane effect exception");}
        catch(RuntimeException e) {check(e==z.failure);}
        row(z,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31);
        check(z.calls==1);check(z.steps==1);check(z.zeros==1);check(z.count("Z")==1);check(z.count("WQ")==4);check(z.count("RQ")==0);
        check(z.count("R256")==2);check(z.count("W256")==2);check(z.count("RD")==1);check(z.events.get(z.events.size()-1).equals(new Event("Z",0)));
    }
    public static void main(String[] args) {
        directBinding261();scalarWhole261();sseWhole261();avxWhole261();
        retFailures261();budgetEffectFailures261();
        System.out.println("PASS groups=2 scenarios="+scenarios+" checks="+checks);
    }

}
