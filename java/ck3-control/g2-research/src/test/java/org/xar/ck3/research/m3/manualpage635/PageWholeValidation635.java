package org.xar.ck3.research.m3.manualpage635;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.*;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New complete Page entry DATA witness; no production changes or native execution. */
public final class PageWholeValidation635 {
    private PageWholeValidation635() { }
    private static final long IMAGE=0x140000000L, PRE_SP=0x70001000L, ENTRY_SP=PRE_SP-8,
        PAGE_BODY=ENTRY_SP-0x48, INSTANCE=0x110000L, TABLE=0x120000L,
        PAGE=0x200000000L, OLD_PAGE=0x300000000L, HEAP=0x123456789ABCDEFL,
        HEAP_TARGET=0xFEDCBA9876543210L, RETURN=IMAGE+0x2A327ECL;
    private static final int SIZE=0x172000;
    private static final Mxcsr ENTRY_FP=Mxcsr.unknown(), RESERVE_FP=new Mxcsr(0x80,0x80), ALLOCATE_FP=new Mxcsr(0x20,0x20);
    private static Bits128 bits(long a,int k) {return new Bits128(a+k,0xD000000000000000L+a+k);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long tag) {
        return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,bits(tag,0),bits(tag,1),bits(tag,2),bits(tag,3),bits(tag,4),bits(tag,5));
    }
    private static final VolatileBits INITIAL=v(0x81000000000000AAL,INSTANCE,1025,0x88,0x99,0xAA,0xBB,0x100),
        RESERVE_V=v(0x9100000000000001L,0x92,0x93,0x98,0x99,0x9A,0x9B,0x200),
        ALLOCATE_V=v(PAGE,0xA1,0xA2,0xA8,0xA9,0xAABBCCDDEEFF0011L,0xAB,0x300);
    private static final NonvolatileBits INITIAL_N=new NonvolatileBits(0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,bits(0x400,6));
    private static int checks, scenarios;
    private static void check(boolean good) {checks++;if(!good)throw new AssertionError("635 check "+checks);}
    private enum Mode { NORMAL, STOP, BAD_RETURN }
    private record Read(int width,long address,long bits) { }
    private static final class Fixture {
        final Mode mode;final byte[] page=new byte[SIZE];final Map<Long,Byte> small=new HashMap<>();
        final List<Read> controlReads=new ArrayList<>();final List<Long> pageSites=new ArrayList<>();
        final List<KnownPageFp619.CallFrame> pageFrames=new ArrayList<>();
        final Map<Long,Long> budgetCalls=new HashMap<>();
        long page128Writes,pageByteWrites,pageDwordWrites,tableZeroWrites,unexpected,allocateCalls;
        KnownHeapAllocateFp623.AllocateCall heapFrame;Stopped offeredStop;
        final KnownPageIndexedFp633.Memory memory;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{
            long n=budgetCalls.merge(header,1L,Long::sum);if(n>40000)throw new AssertionError("635 bounded loop");
        };
        Fixture(Mode mode) {
            this.mode=mode;Arrays.fill(page,(byte)0xA5);
            memory=(KnownPageIndexedFp633.Memory)Proxy.newProxyInstance(KnownPageIndexedFp633.Memory.class.getClassLoader(),new Class<?>[]{KnownPageIndexedFp633.Memory.class},(proxy,method,args)->{
                String name=method.getName();
                if(method.getDeclaringClass()==Object.class) {
                    if(name.equals("hashCode"))return Integer.valueOf(System.identityHashCode(proxy));
                    if(name.equals("equals"))return Boolean.valueOf(proxy==args[0]);
                    if(name.equals("toString"))return "635 owned DATA";
                }
                long a=((Long)args[0]).longValue();
                if(name.equals("readQword")||name.equals("readPointer")||name.equals("read64"))return Long.valueOf(read(a,8));
                if(name.equals("readDword")||name.equals("readInt32")||name.equals("read32"))return Integer.valueOf((int)read(a,4));
                if(name.equals("readUnsignedByte")||name.equals("readUnsigned8")||name.equals("read8"))return Integer.valueOf((int)read(a,1));
                if(name.equals("readUnsignedWord")||name.equals("readUnsigned16"))return Integer.valueOf((int)read(a,2));
                if(name.equals("writeQword")||name.equals("writeInt64")){write(a,8,((Number)args[1]).longValue());return null;}
                if(name.equals("writeDword")||name.equals("writeInt32")){write(a,4,((Number)args[1]).longValue());return null;}
                if(name.equals("writeByte")||name.equals("write8")){write(a,1,((Number)args[1]).longValue());return null;}
                if(name.equals("writeWord")||name.equals("write16")){write(a,2,((Number)args[1]).longValue());return null;}
                if(name.equals("write128")){
                    Bits128 value=(Bits128)args[1];if(inPage(a,16))page128Writes++;
                    store(a,8,value.lowBits());store(a+8,8,value.highBits());return null;
                }
                unexpected++;throw new AssertionError("635 unsupported operation "+name);
            });
            store(ENTRY_SP,8,RETURN);store(INSTANCE,8,TABLE);store(INSTANCE+0xC,4,1);store(INSTANCE+0x40,1,0);
            store(TABLE,8,OLD_PAGE);store(TABLE+8,8,0xBAD0000000000001L);
            store(PAGE-16,8,0x5A5A5A5A5A5A5A5AL);store(PAGE-8,8,0x5A5A5A5A5A5A5A5AL);
            store(PAGE+SIZE,8,0x5A5A5A5A5A5A5A5AL);store(PAGE+SIZE+8,8,0x5A5A5A5A5A5A5A5AL);
            store(IMAGE+0x60900B0+8*4,4,0x422707C);store(IMAGE+0x5C5CBB0,1,0);store(IMAGE+0x542F0A8,8,Long.MAX_VALUE);
            store(IMAGE+0x5C5DE30,8,HEAP);store(IMAGE+0x43DA768,8,HEAP_TARGET);
        }
        boolean inPage(long a,int w) {long off=a-PAGE;return off>=0&&off<=SIZE-w;}
        long load(long a,int w) {
            long value=0;for(int i=0;i<w;i++) {
                long at=a+i;Byte b=inPage(at,1)?Byte.valueOf(page[(int)(at-PAGE)]):small.get(at);
                if(b==null)throw new AssertionError("635 unseeded "+Long.toHexString(at));
                value|=(b.byteValue()&255L)<<(8*i);
            }return value;
        }
        void store(long a,int w,long value) {
            for(int i=0;i<w;i++){long at=a+i;byte b=(byte)(value>>>(8*i));if(inPage(at,1))page[(int)(at-PAGE)]=b;else small.put(at,Byte.valueOf(b));}
        }
        long read(long a,int w) {
            long value=load(a,w);
            if(a==IMAGE+0x60900B0+8*4||a==IMAGE+0x5C5CBB0||a==IMAGE+0x542F0A8||a==IMAGE+0x5C5DE30||a==IMAGE+0x43DA768)controlReads.add(new Read(w,a,value));
            return value;
        }
        void write(long a,int w,long value) {
            if(inPage(a,w)){if(w==1)pageByteWrites++;if(w==4)pageDwordWrites++;}
            if(a==TABLE+8&&w==8&&value==0)tableZeroWrites++;
            store(a,w,value);
        }
        Normal external(VolatileBits after,GovernmentCrtBoundary185Api.Call call,long ret,boolean df,Mxcsr fp) {
            return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(after,ret,call.rspBits(),call.nonvolatileBits()),df),fp);
        }
        Outcome pageForeign(KnownPageFp619.CallFrame frame) {
            if(frame.original().call().callSiteRva()!=0x2A32258L)throw new AssertionError("635 unexpected Page foreign");
            return external(RESERVE_V,frame.original().call(),frame.original().returnRipBits(),false,RESERVE_FP);
        }
        Outcome allocateForeign(KnownHeapAllocateFp623.AllocateCall frame) {
            allocateCalls++;heapFrame=frame;
            if(frame.original().callSiteRva()!=0x424FDDEL||frame.original().kind()!=GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE||frame.original().targetBits()!=HEAP_TARGET)throw new AssertionError("635 unexpected allocation edge");
            if(mode==Mode.STOP) {
                offeredStop=new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(frame.childEntry(),0x424FDDE,frame.directionFlagSet(),frame.preMxcsr()),0,0x424FDDE);
                return offeredStop;
            }
            return external(ALLOCATE_V,frame.original(),frame.returnRipBits()+(mode==Mode.BAD_RETURN?1:0),true,ALLOCATE_FP);
        }
        Outcome run() {
            E900Fp627Api.Calls e900Foreign=new E900Fp627Api.Calls(){
                @Override public Outcome invoke(E900Fp627Api.CallFrame f){throw new AssertionError("635 E900 foreign");}
                @Override public Outcome tail(E900Fp627Api.TailFrame f){throw new AssertionError("635 E900 tail");}
            };
            KnownPageFp619.Calls allocate=KnownPageIndexedFp633.bind(memory,budget,
                f->{throw new AssertionError("635 Indexed foreign");},e900Foreign,
                f->{throw new AssertionError("635 FC74 foreign");},f->{throw new AssertionError("635 Error foreign");},
                this::allocateForeign,f->{throw new AssertionError("635 Retry foreign");},this::pageForeign);
            KnownPageFp619.Calls withSet=KnownPageSetFp620.bind(memory,budget,f->{throw new AssertionError("635 unknown SET tail");},allocate);
            KnownPageFp619.Calls observed=f->{pageSites.add(f.original().call().callSiteRva());pageFrames.add(f);return withSet.invoke(f);};
            SlotProducerGrowthWithFp618.Calls root=KnownPageFp619.bind(memory,budget,observed,f->{throw new AssertionError("635 foreign root");});
            var call=new GovernmentCrtBoundary185Api.Call(0x2A327E7,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x2A321F0,PRE_SP,INITIAL,INITIAL_N);
            var child=new GovernmentCrtBoundary185Api.Entry(IMAGE,ENTRY_SP,INITIAL,INITIAL_N);
            var frame=new FullSlotProducer479Api.CallFrame(call,child,true,5,RETURN);
            scenarios++;return root.invoke(new SlotProducerGrowthWithFp618.CallFrame(frame,ENTRY_FP));
        }
    }

    private static void wholePageNormal() {
        Fixture f=new Fixture(Mode.NORMAL);Outcome outcome=f.run();check(outcome instanceof Normal);
        Normal actual=(Normal)outcome;GovernmentCrtBoundary185Api.NormalReturn nr=actual.base().normalReturn();
        VolatileBits expected=new VolatileBits(PAGE+0x172001L,0,0,0,0,ALLOCATE_V.r10Bits(),PAGE,
                new Bits128(0,0),ALLOCATE_V.xmm1(),ALLOCATE_V.xmm2(),ALLOCATE_V.xmm3(),ALLOCATE_V.xmm4(),ALLOCATE_V.xmm5());
        check(nr.equals(new GovernmentCrtBoundary185Api.NormalReturn(expected,RETURN,PRE_SP,INITIAL_N)));
        check(actual.base().postDirectionFlagSet());check(actual.postMxcsr()==ALLOCATE_FP);
        check(f.pageSites.equals(List.of(0x2A32258L,0x2A3227CL,0x2A322DBL,0x2A322EEL,0x2A32325L)));
        check(f.pageFrames.size()==5&&f.allocateCalls==1&&f.unexpected==0&&f.offeredStop==null);
        for(KnownPageFp619.CallFrame frame:f.pageFrames) {
            check(frame.original().call().rspBits()==PAGE_BODY);
            check(frame.original().childEntry().rspBits()==PAGE_BODY-8);
            check(frame.original().childEntry().imageBaseBits()==IMAGE);
        }
        check(f.load(PAGE_BODY-8,8)==IMAGE+0x2A3232AL);
        check(f.pageFrames.get(0).preMxcsr()==ENTRY_FP&&f.pageFrames.get(0).original().directionFlagSet());
        check(f.pageFrames.get(1).preMxcsr()==RESERVE_FP&&!f.pageFrames.get(1).original().directionFlagSet());
        check(f.pageFrames.get(2).preMxcsr()==RESERVE_FP&&!f.pageFrames.get(2).original().directionFlagSet());
        check(f.pageFrames.get(3).preMxcsr()==ALLOCATE_FP&&f.pageFrames.get(3).original().directionFlagSet());
        check(f.pageFrames.get(4).preMxcsr()==ALLOCATE_FP&&f.pageFrames.get(4).original().directionFlagSet());
        check(f.pageFrames.get(1).original().call().volatileBits().rcxBits()==TABLE+8);
        check(f.pageFrames.get(1).original().call().volatileBits().rdxBits()==0);
        check(f.pageFrames.get(1).original().call().volatileBits().r8Bits()==8);
        for(int k=3;k<5;k++) {
            VolatileBits before=f.pageFrames.get(k).original().call().volatileBits();
            check(before.rcxBits()==PAGE&&before.rdxBits()==0&&before.r8Bits()==SIZE);
        }
        check(f.heapFrame!=null&&f.heapFrame.preMxcsr()==RESERVE_FP&&!f.heapFrame.directionFlagSet());
        check(f.heapFrame.original().callSiteRva()==0x424FDDEL&&f.heapFrame.original().kind()==GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE);
        check(f.heapFrame.original().targetBits()==HEAP_TARGET);
        check(f.heapFrame.childEntry().rspBits()==PAGE_BODY-0x68);
        check(f.heapFrame.original().rspBits()==PAGE_BODY-0x60);
        check(f.heapFrame.returnRipBits()==IMAGE+0x424FDE4L);
        VolatileBits heapV=f.heapFrame.original().volatileBits();
        VolatileBits expectedHeap=new VolatileBits(1,HEAP,0,SIZE,IMAGE+0x422707CL,RESERVE_V.r10Bits(),TABLE+8,
                RESERVE_V.xmm0(),RESERVE_V.xmm1(),RESERVE_V.xmm2(),RESERVE_V.xmm3(),RESERVE_V.xmm4(),RESERVE_V.xmm5());
        check(heapV.equals(expectedHeap));
        check(f.heapFrame.original().nonvolatileBits().equals(new NonvolatileBits(SIZE,1,8,1,INITIAL_N.r12Bits(),INITIAL_N.r13Bits(),INSTANCE,INITIAL_N.r15Bits(),INITIAL_N.xmm6())));
        check(f.load(TABLE,8)==OLD_PAGE&&f.load(TABLE+8,8)==PAGE&&f.load(INSTANCE+0xC,4)==2);
        boolean pageGood=true;
        for(int offset=0;offset<SIZE;offset++) {
            int d=offset-0x10;boolean header=d>=0&&d/0x5C8<1024&&d%0x5C8<4;
            if((f.page[offset]&255)!=(header?255:0)){pageGood=false;break;}
        }
        check(pageGood);
        check(f.page128Writes==189440&&f.pageDwordWrites==1024&&f.pageByteWrites==0&&f.tableZeroWrites==1);
        check(f.controlReads.equals(List.of(new Read(4,IMAGE+0x60900B0+32,0x422707C),
                new Read(8,IMAGE+0x5C5DE30,HEAP),new Read(8,IMAGE+0x43DA768,HEAP_TARGET),
                new Read(1,IMAGE+0x5C5CBB0,0),new Read(8,IMAGE+0x542F0A8,Long.MAX_VALUE),
                new Read(1,IMAGE+0x5C5CBB0,0),new Read(8,IMAGE+0x542F0A8,Long.MAX_VALUE))));
        check(f.budgetCalls.equals(Map.of(0x2A322D0L,1L,0x4223BAEL,1L,0x4226F80L,23678L,0x4226FC0L,14L,0x2A32333L,1024L)));
        check(f.load(PAGE-16,8)==0x5A5A5A5A5A5A5A5AL&&f.load(PAGE-8,8)==0x5A5A5A5A5A5A5A5AL);
        check(f.load(PAGE+SIZE,8)==0x5A5A5A5A5A5A5A5AL&&f.load(PAGE+SIZE+8,8)==0x5A5A5A5A5A5A5A5AL);
        check(f.load(ENTRY_SP,8)==RETURN&&f.load(ENTRY_SP-8,8)==INITIAL_N.r14Bits());
    }
    private static void wholePageStopsAndRejects() {
        for(Mode mode:List.of(Mode.STOP,Mode.BAD_RETURN)) {
            Fixture f=new Fixture(mode);
            if(mode==Mode.STOP) {
                Outcome actual=f.run();check(actual==f.offeredStop&&actual instanceof Stopped);
                Stopped stopped=(Stopped)actual;
                check(stopped.reason()==QueueFp604Api.StopReason.MISSING_POST_STATE);
                check(stopped.raisedConditionBits()==0&&stopped.originCallSiteRva()==0x424FDDEL);
                check(stopped.snapshot().instructionRva()==0x424FDDEL&&!stopped.snapshot().directionFlagSet());
                check(stopped.snapshot().mxcsr()==RESERVE_FP);
                check(stopped.snapshot().currentState().equals(f.heapFrame.childEntry()));
            } else {
                boolean rejected=false;
                try {f.run();}catch(IllegalArgumentException expected) {rejected=true;}
                check(rejected&&f.offeredStop==null);
            }
            check(f.pageSites.equals(List.of(0x2A32258L,0x2A3227CL,0x2A322DBL)));
            check(f.pageFrames.size()==3&&f.allocateCalls==1&&f.unexpected==0);
            check(f.pageFrames.get(0).preMxcsr()==ENTRY_FP&&f.pageFrames.get(0).original().directionFlagSet());
            check(f.pageFrames.get(1).preMxcsr()==RESERVE_FP&&!f.pageFrames.get(1).original().directionFlagSet());
            check(f.pageFrames.get(2).preMxcsr()==RESERVE_FP&&!f.pageFrames.get(2).original().directionFlagSet());
            check(f.heapFrame.preMxcsr()==RESERVE_FP&&!f.heapFrame.directionFlagSet());
            check(f.heapFrame.original().callSiteRva()==0x424FDDEL&&f.heapFrame.original().targetBits()==HEAP_TARGET);
            check(f.heapFrame.original().kind()==GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE);
            check(f.heapFrame.childEntry().rspBits()==PAGE_BODY-0x68&&f.heapFrame.original().rspBits()==PAGE_BODY-0x60);
            check(f.heapFrame.childEntry().imageBaseBits()==IMAGE&&f.heapFrame.returnRipBits()==IMAGE+0x424FDE4L);
            check(f.heapFrame.original().volatileBits().rcxBits()==HEAP&&f.heapFrame.original().volatileBits().rdxBits()==0&&f.heapFrame.original().volatileBits().r8Bits()==SIZE);
            check(f.load(TABLE,8)==OLD_PAGE&&f.load(TABLE+8,8)==0&&f.load(INSTANCE+0xC,4)==2);
            boolean pageUnchanged=true;for(byte value:f.page)if((value&255)!=0xA5){pageUnchanged=false;break;}check(pageUnchanged);
            check(f.page128Writes==0&&f.pageDwordWrites==0&&f.pageByteWrites==0&&f.tableZeroWrites==1);
            check(f.controlReads.equals(List.of(new Read(4,IMAGE+0x60900B0+32,0x422707C),new Read(8,IMAGE+0x5C5DE30,HEAP),new Read(8,IMAGE+0x43DA768,HEAP_TARGET))));
            check(f.budgetCalls.equals(Map.of(0x2A322D0L,1L,0x4223BAEL,1L)));
            check(f.load(ENTRY_SP,8)==RETURN&&f.load(ENTRY_SP-8,8)==INITIAL_N.r14Bits());
            check(f.load(PAGE_BODY-8,8)==IMAGE+0x2A322E0L);
            check(f.load(PAGE_BODY-0x38,8)==IMAGE+0x4223BB3L&&f.load(PAGE_BODY-0x68,8)==IMAGE+0x424FDE4L);
            check(f.load(PAGE-16,8)==0x5A5A5A5A5A5A5A5AL&&f.load(PAGE-8,8)==0x5A5A5A5A5A5A5A5AL);
            check(f.load(PAGE+SIZE,8)==0x5A5A5A5A5A5A5A5AL&&f.load(PAGE+SIZE+8,8)==0x5A5A5A5A5A5A5A5AL);
        }
    }

    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("No arguments");
        wholePageNormal();wholePageStopsAndRejects();
        System.out.println("PASS groups=2 scenarios="+scenarios+" checks="+checks);
    }
}
