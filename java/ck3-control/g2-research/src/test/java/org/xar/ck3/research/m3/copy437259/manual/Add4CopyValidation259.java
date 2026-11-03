package org.xar.ck3.research.m3.copy437259.manual;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.copy437259.Add4Copy259;
import org.xar.ck3.control.g2.m2.nativecode.*;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New finite source-derived software witness; foreign ports are explicit DATA offers. */
public final class Add4CopyValidation259 {
    private Add4CopyValidation259() { }
    private static final long IMAGE=0x140000000L, SP=0x70001000L, SRC=0x310000L, DST=0x410000L;
    private static final long OBJ=0x110000L, OLD=0x510000L, NEW=0x610000L, ALLOC=0x120000L, VT=0x130000L;
    private static final long ALLOC_TARGET=0x8122334455667788L, FREE_TARGET=0x9233445566778899L;
    private static final long ROOT_RETURN=IMAGE+0x372987CL;
    private static int checks,scenarios;
    private static void check(boolean value) {checks++;if(!value)throw new AssertionError("259 check "+checks);}
    private static Bits128 b(long tag,int k) {return new Bits128(tag+k,0xD000000000000000L+tag+k);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long tag) {
        return new VolatileBits(ax,cx,dx,r8,tag+9,tag+10,tag+11,b(tag,0),b(tag,1),b(tag,2),b(tag,3),b(tag,4),b(tag,5));
    }
    private static NonvolatileBits n(long tag) {
        return new NonvolatileBits(tag+1,tag+2,tag+3,tag+4,tag+5,tag+6,tag+7,tag+8,b(tag,6));
    }
    private static final NonvolatileBits N=n(0x5000);
    private record Event(String operation,long address,Object value) { }
    private static long narrow(long value,int width) {return width==8?value:value&((1L<<(width*8))-1);}
    private static Event event(String operation,int width,long address,long value) {
        return new Event(operation+width,address,Long.valueOf(narrow(value,width)));
    }
    private static final class Ram {
        final Map<Long,Byte> bytes=new HashMap<>();final List<Event> events=new ArrayList<>();
        long budgets;long failRead=Long.MIN_VALUE;RuntimeException readFailure;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{
            if(++budgets>100)throw new AssertionError("259 finite budget");
        };
        final Add4Fp639Api.Memory memory;
        Ram() {
            memory=(Add4Fp639Api.Memory)Proxy.newProxyInstance(Add4Fp639Api.Memory.class.getClassLoader(),
                new Class<?>[]{Add4Fp639Api.Memory.class},(proxy,method,args)->{
                    String name=method.getName();
                    if(method.getDeclaringClass()==Object.class) {
                        if(name.equals("hashCode"))return Integer.valueOf(System.identityHashCode(proxy));
                        if(name.equals("equals"))return Boolean.valueOf(proxy==args[0]);
                        if(name.equals("toString"))return "259 finite RAM";
                    }
                    if(args==null||args.length==0)throw new AssertionError("259 unsupported zero-arg "+name);
                    long address=((Long)args[0]).longValue();
                    if(name.equals("readQword"))return Long.valueOf(read(address,8));
                    if(name.equals("readDword"))return Integer.valueOf((int)read(address,4));
                    if(name.equals("readUnsignedWord"))return Integer.valueOf((int)read(address,2));
                    if(name.equals("readUnsignedByte"))return Integer.valueOf((int)read(address,1));
                    if(name.equals("writeQword")){write(address,8,((Number)args[1]).longValue());return null;}
                    if(name.equals("writeDword")){write(address,4,((Number)args[1]).longValue());return null;}
                    if(name.equals("writeWord")){write(address,2,((Number)args[1]).longValue());return null;}
                    if(name.equals("writeByte")){write(address,1,((Number)args[1]).longValue());return null;}
                    if(name.equals("read128")) {
                        Bits128 value=new Bits128(load(address,8),load(address+8,8));events.add(new Event("R128",address,value));return value;
                    }
                    if(name.equals("write128")) {
                        Bits128 value=(Bits128)args[1];events.add(new Event("W128",address,value));seed(address,8,value.lowBits());seed(address+8,8,value.highBits());return null;
                    }
                    throw new AssertionError("259 unsupported "+name);
                });
        }
        void seed(long address,int width,long value) {for(int k=0;k<width;k++)bytes.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        void fill(long address,int count,int value) {for(int k=0;k<count;k++)seed(address+k,1,value);}
        long load(long address,int width) {
            long value=0;for(int k=0;k<width;k++) {
                Byte next=bytes.get(address+k);if(next==null)throw new AssertionError("259 unseeded "+Long.toHexString(address+k));
                value|=(next.byteValue()&255L)<<(k*8);
            }return value;
        }
        long read(long address,int width) {
            if(address==failRead)throw readFailure;
            long value=load(address,width);events.add(event("R",width,address,value));return value;
        }
        void write(long address,int width,long value) {events.add(event("W",width,address,value));seed(address,width,value);}
        void smallTarget(int count,long target) {seed(IMAGE+0x6090000L+4L*count,4,target);}
    }
    private static Add4Fp639Api.CallFrame frame(long site,VolatileBits before,NonvolatileBits nv,boolean df,Mxcsr fp) {
        boolean indirect=site==0xADD153L||site==0xADD1B5L;
        int length=indirect?3:5;
        long target=indirect?(site==0xADD153L?ALLOC_TARGET:FREE_TARGET):(site==0xADD219L?0x9D0950L:0x4226860L);
        var call=new GovernmentCrtBoundary185Api.Call(site,indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,SP,before,nv);
        var child=new GovernmentCrtBoundary185Api.Entry(IMAGE,SP-8,before,nv);
        return new Add4Fp639Api.CallFrame(call,child,df,fp,length,IMAGE+site+length);
    }
    private static Normal offer(Add4Fp639Api.CallFrame f,VolatileBits after,boolean df,Mxcsr fp) {
        return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(after,f.returnRipBits(),f.call().rspBits(),f.call().nonvolatileBits()),df),fp);
    }
    private static Stopped stop(FullCopyWithFp613.TailCall f) {
        return new Stopped(StopReason.MISSING_POST_STATE,new Snapshot(f.original().transfer().entry(),f.original().transfer().jumpSiteRva(),f.original().directionFlagSet(),f.preMxcsr()),0,0xADD1F7L);
    }
    private static void directAndFailureProtocol() {
        long[] sites={0xADD16DL,0xADD17CL,0xADD1A0L,0xADD1F7L};int[] counts={4,16,32,0};
        for(int k=0;k<sites.length;k++) {
            scenarios++;Ram ram=new Ram();int count=counts[k];
            VolatileBits before=v(0xABCD000000000001L,DST,SRC,count,0x9000+k*0x100);
            NonvolatileBits nv=n(0xA000+k*0x100);Mxcsr fp=new Mxcsr(0x80,0x80);boolean df=(k&1)==0;
            var f=frame(sites[k],before,nv,df,fp);ram.seed(SP-8,8,f.returnRipBits());ram.fill(SRC,40,0x5A);ram.fill(DST-4,44,0xA5);
            Bits128 first=b(0x12345678,0),second=b(0x88776655,1);
            ram.seed(SRC,8,first.lowBits());ram.seed(SRC+8,8,first.highBits());ram.seed(SRC+16,8,second.lowBits());ram.seed(SRC+24,8,second.highBits());
            if(count==4)ram.smallTarget(4,0x422697A);if(count==0)ram.smallTarget(0,0x422688E);
            Add4Fp639Api.Calls bound=Add4Copy259.bind(ram.memory,ram.budget,t->{throw new AssertionError("259 unexpected tail");},x->{throw new AssertionError("259 selected foreign");});
            Outcome result=bound.invoke(f);check(result instanceof Normal);Normal normal=(Normal)result;
            long cx=count==4?Integer.toUnsignedLong((int)first.lowBits()):DST;
            long r9=count==4?IMAGE+0x422697AL:count==0?IMAGE+0x422688EL:before.r9Bits();
            VolatileBits expected=new VolatileBits(DST,cx,SRC,count,r9,IMAGE,before.r11Bits(),before.xmm0(),
                count>=16?first:before.xmm1(),count==16?first:count==32?second:before.xmm2(),before.xmm3(),before.xmm4(),before.xmm5());
            check(normal.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(expected,f.returnRipBits(),SP,nv)));
            check(normal.base().postDirectionFlagSet()==df&&normal.postMxcsr()==fp&&ram.budgets==0);
            List<Event> expectedEvents;
            if(count==0)expectedEvents=List.of(event("R",4,IMAGE+0x6090000L,0x422688E),event("R",8,SP-8,f.returnRipBits()));
            else if(count==4)expectedEvents=List.of(event("R",4,IMAGE+0x6090010L,0x422697A),event("R",4,SRC,first.lowBits()),event("W",4,DST,first.lowBits()),event("R",8,SP-8,f.returnRipBits()));
            else expectedEvents=List.of(new Event("R128",SRC,first),new Event("R128",SRC+count-16,count==16?first:second),
                new Event("W128",DST,first),new Event("W128",DST+count-16,count==16?first:second),event("R",8,SP-8,f.returnRipBits()));
            check(ram.events.equals(expectedEvents));
            for(int i=-4;i<40;i++)check(ram.load(DST+i,1)==(i>=0&&i<count?ram.load(SRC+i,1):0xA5));
        }
        // A real dynamic small-table target selects the mature REP tail; this is fixture DATA, not a loaded table claim.
        scenarios++;Ram rep=new Ram();Mxcsr repFp=Mxcsr.unknown();var repV=v(0xCAFE,DST+2,SRC+2,3,0xD000);
        var repFrame=frame(0xADD16D,repV,N,true,repFp);rep.seed(SP-8,8,repFrame.returnRipBits());rep.fill(SRC,3,0);rep.seed(SRC,3,0x563412);rep.fill(DST-1,5,0xA5);rep.smallTarget(3,0x4226840);
        Outcome repResult=Add4Copy259.bind(rep.memory,rep.budget,t->{throw new AssertionError("259 known REP escaped");},x->{throw new AssertionError();}).invoke(repFrame);
        check(repResult instanceof Normal);Normal rn=(Normal)repResult;
        var repExpected=new VolatileBits(DST+2,0,SRC+2,3,IMAGE+0x4226840L,IMAGE,repV.r11Bits(),repV.xmm0(),repV.xmm1(),repV.xmm2(),repV.xmm3(),repV.xmm4(),repV.xmm5());
        check(rn.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(repExpected,repFrame.returnRipBits(),SP,N)));
        check(rn.postMxcsr()==repFp&&rn.base().postDirectionFlagSet()&&rep.budgets==3);
        check(rep.load(DST,3)==0x563412&&rep.load(DST-1,1)==0xA5&&rep.load(DST+3,1)==0xA5);
        check(rep.load(SP-16,8)==N.rdiBits()&&rep.load(SP-24,8)==N.rsiBits());
        // Foreign frames retain the same frame/result and do not use any RAM or the budget.
        for(long site:new long[]{0xADD153L,0xADD1B5L,0xADD219L}) {
            scenarios++;Ram ram=new Ram();var f=frame(site,v(1,2,3,4,0xE000),N,false,Mxcsr.unknown());
            Outcome offered=site==0xADD1B5L?new Stopped(StopReason.MISSING_POST_STATE,new Snapshot(f.childEntry(),site,false,f.preMxcsr()),0,site):offer(f,v(5,6,7,8,0xE100),true,new Mxcsr(0x20,0x20));
            int[] calls={0};Outcome actual=Add4Copy259.bind(ram.memory,ram.budget,t->{throw new AssertionError();},same->{check(same==f);calls[0]++;return offered;}).invoke(f);
            check(actual==offered&&calls[0]==1&&ram.events.isEmpty()&&ram.budgets==0);
        }
        // The unknown tail can stop; a valid selected frame never turns it into a Normal.
        scenarios++;Ram stoppedRam=new Ram();stoppedRam.smallTarget(1,0x05556677);var stoppedFrame=frame(0xADD1F7,v(1,DST,SRC,1,0xF000),N,true,new Mxcsr(0x80,0x80));
        Stopped[] stoppedOffer={null};Outcome stopped=Add4Copy259.bind(stoppedRam.memory,stoppedRam.budget,t->{
            check(t.preMxcsr()==stoppedFrame.preMxcsr()&&t.original().directionFlagSet());
            check(t.original().transfer().entry().rspBits()==SP-8);stoppedOffer[0]=stop(t);return stoppedOffer[0];
        },f->{throw new AssertionError();}).invoke(stoppedFrame);
        check(stopped==stoppedOffer[0]&&stoppedRam.events.size()==1); // No RET has been seeded or read.
        for(int fault=0;fault<3;fault++) {
            scenarios++;Ram bad=new Ram();bad.smallTarget(1,0x05556677);var f=frame(0xADD17C,v(1,DST,SRC,1,0xF100),N,false,Mxcsr.unknown());
            final int which=fault;boolean rejected=false;
            try {Add4Copy259.bind(bad.memory,bad.budget,t->{
                var state=t.original().transfer().entry();var nr=new GovernmentCrtBoundary185Api.NormalReturn(state.volatileBits(),f.returnRipBits()+(which==0?1:0),SP+(which==1?8:0),which==2?n(0xFF00):N);
                return new Normal(new FullCopy437Api.CallResult(nr,true),new Mxcsr(0x20,0x20));
            },x->{throw new AssertionError();}).invoke(f);}catch(IllegalArgumentException expected){rejected=true;}
            check(rejected&&bad.events.size()==1);
        }
        scenarios++;Ram throwing=new Ram();RuntimeException sentinel=new IllegalStateException("259 exact callback failure");throwing.smallTarget(4,0x422697A);throwing.failRead=SRC;throwing.readFailure=sentinel;
        var f=frame(0xADD1A0,v(1,DST,SRC,4,0xF200),N,true,Mxcsr.unknown());RuntimeException caught=null;
        try {Add4Copy259.bind(throwing.memory,throwing.budget,t->{throw new AssertionError();},x->{throw new AssertionError();}).invoke(f);}catch(RuntimeException actual){caught=actual;}
        check(caught==sentinel&&throwing.events.size()==1);
        scenarios++;Ram foreignNull=new Ram();boolean nullRejected=false;
        try {Add4Copy259.bind(foreignNull.memory,foreignNull.budget,t->{throw new AssertionError();},x->null).invoke(frame(0xADD219,v(1,2,3,4,8),N,true,Mxcsr.unknown()));}catch(NullPointerException expected){nullRejected=true;}
        check(nullRejected&&foreignNull.events.isEmpty());
    }

    private static void wholeCallerComposition() {
        for(boolean growth:new boolean[]{false,true}) {
            scenarios++;Ram ram=new Ram();ram.seed(SP,8,ROOT_RETURN);ram.seed(OBJ,8,OLD);ram.seed(OBJ+8,4,growth?2:4);ram.seed(OBJ+0xC,4,2);ram.seed(OBJ+0x10,8,ALLOC);
            ram.seed(ALLOC,8,VT);ram.seed(VT+8,8,ALLOC_TARGET);ram.seed(VT+0x10,8,FREE_TARGET);ram.seed(IMAGE+0x49F64F0L,4,0x3FC00000);
            ram.seed(OLD,4,0x11223344);ram.seed(OLD+4,4,0x55667788);ram.seed(OLD+8,4,0xA5A5A5A5L);ram.seed(SRC,4,0x89ABCDEF);
            ram.fill(NEW-4,20,0xA5);ram.smallTarget(4,0x422697A);
            var initial=new VolatileBits(0xABCD000000000001L,OBJ,1,SRC,SRC+4,0xABCD10,0xABCD11,b(0x100,0),b(0x100,1),b(0x100,2),b(0x100,3),b(0x100,4),b(0x100,5));
            Mxcsr entryFp=growth?new Mxcsr(0x1F80,0xFFC0):Mxcsr.unknown();
            Mxcsr allocatedFp=new Mxcsr(0x80,0x80),finalFp=new Mxcsr(0x20,0x20);
            VolatileBits allocated=v(NEW,0xA1,0xA2,0xA8,0xA000),foreignFinal=v(0xDD00000000000001L,0xD1,0xD2,0xD8,0xD000);
            List<Long> sites=new ArrayList<>();int[] foreignCount={0};
            Add4Fp639Api.Calls foreign=frame->{
                foreignCount[0]++;long site=frame.call().callSiteRva();var before=frame.call().volatileBits();
                check(frame.childEntry().rspBits()==frame.call().rspBits()-8&&ram.load(frame.childEntry().rspBits(),8)==frame.returnRipBits());
                if(site==0xADD153L) {
                    check(growth&&before.rcxBits()==ALLOC&&before.rdxBits()==12&&before.r8Bits()==4&&before.raxBits()==VT);
                    check(frame.preMxcsr()==entryFp&&frame.directionFlagSet());
                    return offer(frame,allocated,false,allocatedFp);
                }
                if(site==0xADD1B5L) {
                    check(growth&&before.rcxBits()==ALLOC&&before.rdxBits()==OLD&&before.r8Bits()==4&&before.raxBits()==VT);
                    check(frame.preMxcsr()==allocatedFp&&!frame.directionFlagSet());
                    return offer(frame,foreignFinal,true,finalFp);
                }
                check(!growth&&site==0xADD219L&&before.rcxBits()==OLD+4&&before.rdxBits()==OLD+8&&before.r8Bits()==OLD+12);
                check(before.raxBits()==3&&before.r9Bits()==OLD&&frame.preMxcsr()==entryFp&&frame.directionFlagSet());
                return offer(frame,foreignFinal,false,finalFp);
            };
            Add4Fp639Api.Calls bound=Add4Copy259.bind(ram.memory,ram.budget,t->{throw new AssertionError("259 whole unexpected COPY tail");},foreign);
            Add4Fp639Api.Calls observed=frame->{sites.add(frame.call().callSiteRva());return bound.invoke(frame);};
            var input=new Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,initial,N),true,ram.budget),entryFp);
            Outcome result=Add4FullState639.execute(input,ram.memory,observed,0x3729877L);
            check(result instanceof Normal);Normal actual=(Normal)result;
            VolatileBits finalV=growth?new VolatileBits(3,foreignFinal.rcxBits(),foreignFinal.rdxBits(),foreignFinal.r8Bits(),foreignFinal.r9Bits(),foreignFinal.r10Bits(),foreignFinal.r11Bits(),foreignFinal.xmm0(),foreignFinal.xmm1(),foreignFinal.xmm2(),foreignFinal.xmm3(),foreignFinal.xmm4(),foreignFinal.xmm5()):foreignFinal;
            check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(finalV,ROOT_RETURN,SP+8,N)));
            check(actual.postMxcsr()==finalFp&&actual.base().postDirectionFlagSet()==growth);
            check(ram.load(OBJ,8)==(growth?NEW:OLD)&&ram.load(OBJ+8,4)==(growth?3:4)&&ram.load(OBJ+0xC,4)==3);
            if(growth) {
                check(sites.equals(List.of(0xADD153L,0xADD16DL,0xADD17CL,0xADD1A0L,0xADD1B5L))&&foreignCount[0]==2);
                check(ram.load(NEW,4)==0x11223344&&ram.load(NEW+4,4)==0x89ABCDEFL&&ram.load(NEW+8,4)==0x55667788);
                check(ram.load(NEW-4,4)==0xA5A5A5A5L&&ram.load(NEW+12,4)==0xA5A5A5A5L);
                check(ram.load(OLD+8,4)==0xA5A5A5A5L);
            } else {
                check(sites.equals(List.of(0xADD1F7L,0xADD219L))&&foreignCount[0]==1);
                check(ram.load(OLD,4)==0x11223344&&ram.load(OLD+4,4)==0x55667788&&ram.load(OLD+8,4)==0x89ABCDEFL);
                check(ram.load(NEW,4)==0xA5A5A5A5L);
            }
            check(ram.budgets==0&&ram.load(SP,8)==ROOT_RETURN);
        }
    }
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("No arguments");
        directAndFailureProtocol();wholeCallerComposition();
        System.out.println("PASS groups=2 scenarios="+scenarios+" checks="+checks);
    }
}
