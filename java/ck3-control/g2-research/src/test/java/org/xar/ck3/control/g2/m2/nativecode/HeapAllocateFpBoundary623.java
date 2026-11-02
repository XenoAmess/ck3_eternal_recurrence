package org.xar.ck3.control.g2.m2.nativecode;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Four new groups for actual Retry->jump->allocate composition and failure-cell prefixes. */
public final class HeapAllocateFpBoundary623 {
    private HeapAllocateFpBoundary623() { }
    private static final long I=0x140000000L,E=0x8700000000008000L,D=0x8700000000002000L,
        H=0x8700000000003000L,H2=0x8700000000003100L,ADDR=0x8700000000004000L,
        CELL=0x8700000000005000L,TARGET=0x140123450L,TARGET2=0x140123490L,SIZE=0x172000L;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=new Mxcsr(0x40,0x40),
        P3=new Mxcsr(4,4),P4=new Mxcsr(0x80,0x80);
    private static Bits128 x(long bank,int lane){return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long bank){return new VolatileBits(
        ax,cx,dx,r8,r9,r10,r11,x(bank,0),x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));}
    private static VolatileBits initial(long size){return v(0xA0,size,0xA2,0xA8,0xA9,0xAA,0xAB,0xA0);}
    private static VolatileBits bank(long bank,long ax){return v(ax,bank+1,bank+2,bank+8,bank+9,bank+10,bank+11,bank);}
    private static final NonvolatileBits N=new NonvolatileBits(11,22,33,44,55,66,77,88,x(0xA0,6));
    private static NonvolatileBits callN(long size){return new NonvolatileBits(size,22,33,44,55,66,77,88,x(0xA0,6));}
    private static void check(boolean value){if(!value)throw new AssertionError("623 independent source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Budget(long header,long guard) { }
    private record Invoke(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
        boolean df,Mxcsr fp,long ret,Outcome outcome,List<Mem> effects,boolean throwing) { }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls;
        final RuntimeException marker=new IllegalStateException("623 original foreign callback");
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->event(new Budget(header,guard));
        final KnownPageFp619.Memory memory=(KnownPageFp619.Memory)Proxy.newProxyInstance(KnownPageFp619.Memory.class.getClassLoader(),
            new Class<?>[]{KnownPageFp619.Memory.class},(proxy,method,args)->{
                String name=method.getName();int width;
                if(name.equals("readUnsignedByte")||name.equals("read8")||name.equals("writeByte")||name.equals("write8"))width=1;
                else if(name.equals("readDword")||name.equals("read32")||name.equals("writeDword")||name.equals("write32"))width=4;
                else if(name.equals("readQword")||name.equals("read64")||name.equals("writeQword")||name.equals("write64"))width=8;
                else throw new AssertionError("Unexpected623Memory "+name);
                long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");
                long value=write?((Number)args[1]).longValue():load(address,width);event(new Mem(write,width,address,mask(width,value)));
                if(write){store(address,width,value);return null;}if(width==1)return Integer.valueOf((int)value&255);
                if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long address,int width,long value){for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long address,int width){long value=0;for(int k=0;k<width;k++){Byte p=ram.get(address+k);if(p==null)throw new AssertionError("Unseeded623RAM");value|=(p.byteValue()&255L)<<(8*k);}return value;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))throw new AssertionError("623 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){steps.add(new Mem(false,width,address,mask(width,value)));}
        void write(int width,long address,long value){steps.add(new Mem(true,width,address,mask(width,value)));}
        void add(long site,long target,VolatileBits before,long size,boolean df,Mxcsr fp,Outcome outcome,List<Mem> effects,boolean throwing){
            var kind=site==0x424FDDE?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
            long ret=site==0x424FDBD?0x424FDC2:site==0x424FDC9?0x424FDCE:site==0x424FDDE?0x424FDE4:0x424FDF0;
            var call=new GovernmentCrtBoundary185Api.Call(site,kind,target,E-0x58,before,callN(size));
            steps.add(new Invoke(call,new GovernmentCrtBoundary185Api.Entry(I,E-0x60,before,callN(size)),df,fp,I+ret,outcome,effects,throwing));steps.addAll(effects);}
        void effect(Mem e){check(e.write());if(e.width()==1)memory.writeByte(e.address(),(int)e.value());else if(e.width()==4)memory.writeDword(e.address(),(int)e.value());else memory.writeQword(e.address(),e.value());}
        Outcome invoke(KnownHeapAllocateFp623.AllocateCall actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Invoke);
            Invoke expected=(Invoke)steps.get(cursor++);check(actual.original().equals(expected.call())&&actual.childEntry().equals(expected.child())
                &&actual.directionFlagSet()==expected.df()&&actual.preMxcsr()==expected.fp()&&actual.returnRipBits()==expected.ret());calls++;
            for(Mem effect:expected.effects())effect(effect);if(expected.throwing())throw marker;return expected.outcome();}
        void done(){check(cursor==steps.size());}
    }
    private static KnownPageFp619.CallFrame page(){var call=new GovernmentCrtBoundary185Api.Call(0x2A322DB,
        GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4223B94,E+8,initial(SIZE),N);
        return new KnownPageFp619.CallFrame(new FullPage495Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E,initial(SIZE),N),true,5,I+0x2A322E0),P0);}
    private static KnownPageAllocateFp622.RetryCall direct(long site,long target,long size){var before=initial(size);var n=callN(size);
        var c=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,E-0x28,before,n);
        return new KnownPageAllocateFp622.RetryCall(c,new GovernmentCrtBoundary185Api.Entry(I,E-0x30,before,n),true,P0);}
    private static KnownPageAllocateFp622.RetryCalls bound(Script s){return KnownHeapAllocateFp623.bind(s.memory,s.budget,s::invoke,
        unused->{throw new AssertionError("Unexpected623foreign");});}
    private static Outcome whole(Script s){return KnownPageAllocateFp622.bind(s.memory,s.budget,bound(s),
        unused->{throw new AssertionError("Unexpected623Pageforeign");}).invoke(page());}
    private static Normal offered(VolatileBits after,long ret,long size,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(
        new GovernmentCrtBoundary185Api.NormalReturn(after,I+ret,E-0x58,callN(size)),df),fp);}
    private static Stopped stopped(VolatileBits before,long site,long size,boolean df,Mxcsr fp){return new Stopped(StopReason.MISSING_POST_STATE,
        new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,E-0x60,before,callN(size)),site,df,fp),0,site);}
    private static Script seeded(){Script s=new Script();s.store(E,8,I+0x2A322E0);s.store(I+0x5C5DE30,8,H);s.store(I+0x43DA768,8,TARGET);return s;}
    private static void wholePrefix(Script s){s.write(8,E-8,11);s.steps.add(new Budget(0x4223BAE,SIZE));s.write(8,E-0x30,I+0x4223BB3);s.write(8,E-0x38,SIZE);}
    private static void heapPrefix(Script s,long heap,long target){s.read(8,I+0x5C5DE30,heap);s.read(8,I+0x43DA768,target);s.write(8,E-0x60,I+0x424FDE4);}
    private static VolatileBits firstHeap(){return v(1,H,0,SIZE,0xA9,0xAA,0xAB,0xA0);}
    private static void actualWholeNormal(){Script s=seeded();wholePrefix(s);heapPrefix(s,H,TARGET);
        s.add(0x424FDDE,TARGET,firstHeap(),SIZE,true,P0,offered(bank(0xB0,ADDR),0x424FDE4,SIZE,false,P1),List.of(new Mem(true,1,D,123)),false);
        s.read(8,E-0x38,SIZE);s.read(8,E-0x30,I+0x4223BB3);s.read(8,E-8,11);s.read(8,E,I+0x2A322E0);
        Normal actual=(Normal)whole(s);s.done();check(s.calls==1&&s.load(D,1)==123&&actual.postMxcsr()==P1&&!actual.base().postDirectionFlagSet());
        check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(bank(0xB0,ADDR),I+0x2A322E0,E+8,N)));}
    private static void actualWholeLoopState(){Script s=seeded();wholePrefix(s);heapPrefix(s,H,TARGET);
        s.add(0x424FDDE,TARGET,firstHeap(),SIZE,true,P0,offered(bank(0xB0,0),0x424FDE4,SIZE,false,P1),List.of(new Mem(true,1,D,1)),false);
        s.steps.add(new Budget(0x424FDBD,0));s.write(8,E-0x60,I+0x424FDC2);
        s.add(0x424FDBD,0x424E250,bank(0xB0,0),SIZE,false,P1,offered(bank(0xC0,0x100000001L),0x424FDC2,SIZE,true,P2),List.of(),false);
        s.write(8,E-0x60,I+0x424FDCE);var gate=v(0x100000001L,SIZE,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0);
        s.add(0x424FDC9,0x424CFFC,gate,SIZE,true,P2,offered(bank(0xD0,0x100000001L),0x424FDCE,SIZE,false,P3),
            List.of(new Mem(true,8,I+0x43DA768,TARGET2),new Mem(true,8,I+0x5C5DE30,H2)),false);
        heapPrefix(s,H2,TARGET2);var next=v(0x100000001L,H2,0,SIZE,0xD9,0xDA,0xDB,0xD0);var expected=stopped(next,0x424FDDE,SIZE,true,P4);
        s.add(0x424FDDE,TARGET2,next,SIZE,false,P3,expected,List.of(new Mem(true,1,D+1,77)),false);
        check(whole(s)==expected);s.done();check(s.calls==4&&s.load(D,1)==1&&s.load(D+1,1)==77&&s.load(E-0x38,8)==SIZE&&s.load(E-8,8)==11);}
    private static Script directSeeded(){Script s=new Script();s.store(E-0x30,8,I+0x4223BB3);return s;}
    private static void failPrefix(Script s){s.write(8,E-0x38,-1);s.write(8,E-0x60,I+0x424FDF0);}
    private static void failureNormalAndStopped(){Script s=directSeeded();failPrefix(s);
        s.add(0x424FDEB,0x423B18C,initial(-1),-1,true,P0,offered(bank(0xB0,CELL),0x424FDF0,-1,false,P1),List.of(new Mem(true,1,D,77)),false);
        s.write(4,CELL,12);s.read(8,E-0x38,-1);s.read(8,E-0x30,I+0x4223BB3);
        Normal actual=(Normal)bound(s).invoke(direct(0x4223BAE,0x42420B8,-1));s.done();check(s.calls==1&&s.load(CELL,4)==12&&s.load(D,1)==77
            &&actual.postMxcsr()==P1&&!actual.base().postDirectionFlagSet()&&actual.base().normalReturn().equals(
                new GovernmentCrtBoundary185Api.NormalReturn(bank(0xB0,0),I+0x4223BB3,E-0x28,callN(-1))));
        Script stop=directSeeded();failPrefix(stop);var expected=stopped(initial(-1),0x424FDEB,-1,false,P2);
        stop.add(0x424FDEB,0x423B18C,initial(-1),-1,true,P0,expected,List.of(new Mem(true,1,D,66)),false);
        check(bound(stop).invoke(direct(0x4223BAE,0x42420B8,-1))==expected);stop.done();check(stop.calls==1&&stop.load(D,1)==66);}
    private static void guardsAliasForeignNonmatch(){Script alias=directSeeded();failPrefix(alias);
        alias.add(0x424FDEB,0x423B18C,initial(-1),-1,true,P0,offered(bank(0xB0,E-0x38),0x424FDF0,-1,false,P1),List.of(),false);
        alias.write(4,E-0x38,12);alias.read(8,E-0x38,0xFFFFFFFF0000000CL);alias.read(8,E-0x30,I+0x4223BB3);
        try{bound(alias).invoke(direct(0x4223BAE,0x42420B8,-1));throw new AssertionError("623failurealiasrepaired");}
        catch(IllegalArgumentException expected){alias.done();check(alias.load(E-0x38,8)==0xFFFFFFFF0000000CL);}
        for(int kind=0;kind<3;kind++){Script s=seeded();wholePrefix(s);heapPrefix(s,H,TARGET);
            var bad=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(bank(0xB0,ADDR),
                I+0x424FDE4+(kind==0?1:0),E-0x58-(kind==1?8:0),kind==2?N:callN(SIZE)),false),P1);
            s.add(0x424FDDE,TARGET,firstHeap(),SIZE,true,P0,bad,List.of(new Mem(true,1,D,99)),false);
            try{whole(s);throw new AssertionError("623badinnerNRaccepted");}catch(IllegalArgumentException expected){s.done();check(s.calls==1&&s.load(D,1)==99);}}
        Script foreign=seeded();wholePrefix(foreign);heapPrefix(foreign,H,TARGET);
        foreign.add(0x424FDDE,TARGET,firstHeap(),SIZE,true,P0,offered(bank(0xB0,ADDR),0x424FDE4,SIZE,false,P1),List.of(new Mem(true,1,D,88)),true);
        try{whole(foreign);throw new AssertionError("623foreignexceptionlost");}catch(RuntimeException actual){check(actual==foreign.marker);foreign.done();check(foreign.load(D,1)==88);}
        Script other=new Script();var frame=direct(0x4223BA2,0x424CFFC,SIZE);var expected=stopped(initial(SIZE),0x4223BA2,SIZE,false,P1);
        var result=KnownHeapAllocateFp623.bind(other.memory,other.budget,unused->{throw new AssertionError("623nonmatchcalled");},
            actual->{check(actual==frame);return expected;}).invoke(frame);check(result==expected&&other.calls==0);other.done();}
    public static int verify(){actualWholeNormal();actualWholeLoopState();failureNormalAndStopped();guardsAliasForeignNonmatch();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
