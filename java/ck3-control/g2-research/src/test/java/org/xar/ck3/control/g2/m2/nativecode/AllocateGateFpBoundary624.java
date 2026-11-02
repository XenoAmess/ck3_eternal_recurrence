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

/** Four new groups for allocator->gate composition, fullRAX/lowEAX and exact state prefixes. */
public final class AllocateGateFpBoundary624 {
    private AllocateGateFpBoundary624() { }
    private static final long I=0x140000000L,E=0x8800000000008000L,D=0x8800000000002000L,
        H=0x8800000000003000L,H2=0x8800000000003100L,ADDR=0x8800000000004000L,
        CELL=0x8800000000005000L,TARGET=0x140123450L,TARGET2=0x140123490L,SIZE=0x172000L;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=new Mxcsr(0x40,0x40),
        P3=new Mxcsr(4,4),P4=new Mxcsr(0x80,0x80);
    private static Bits128 x(long bank,int lane){return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long bank){return new VolatileBits(
        ax,cx,dx,r8,r9,r10,r11,x(bank,0),x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));}
    private static VolatileBits initial(long size){return v(0xA0,size,0xA2,0xA8,0xA9,0xAA,0xAB,0xA0);}
    private static VolatileBits bank(long bank,long ax){return v(ax,bank+1,bank+2,bank+8,bank+9,bank+10,bank+11,bank);}
    private static final NonvolatileBits N=new NonvolatileBits(11,22,33,44,55,66,77,88,x(0xA0,6));
    private static NonvolatileBits callN(long size){return new NonvolatileBits(size,22,33,44,55,66,77,88,x(0xA0,6));}
    private static void check(boolean value){if(!value)throw new AssertionError("624 independent source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Budget(long header,long guard) { }
    private record Invoke(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
        boolean df,Mxcsr fp,long ret,Outcome outcome,List<Mem> effects,boolean throwing) { }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls;
        final RuntimeException marker=new IllegalStateException("624 original foreign callback");
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->event(new Budget(header,guard));
        final KnownPageFp619.Memory memory=(KnownPageFp619.Memory)Proxy.newProxyInstance(KnownPageFp619.Memory.class.getClassLoader(),
            new Class<?>[]{KnownPageFp619.Memory.class},(proxy,method,args)->{
                String name=method.getName();int width;
                if(name.equals("readUnsignedByte")||name.equals("read8")||name.equals("writeByte")||name.equals("write8"))width=1;
                else if(name.equals("readDword")||name.equals("read32")||name.equals("writeDword")||name.equals("write32"))width=4;
                else if(name.equals("readQword")||name.equals("read64")||name.equals("writeQword")||name.equals("write64"))width=8;
                else throw new AssertionError("Unexpected624Memory "+name);
                long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");
                long value=write?((Number)args[1]).longValue():load(address,width);event(new Mem(write,width,address,mask(width,value)));
                if(write){store(address,width,value);return null;}if(width==1)return Integer.valueOf((int)value&255);
                if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long address,int width,long value){for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long address,int width){long value=0;for(int k=0;k<width;k++){Byte p=ram.get(address+k);if(p==null)throw new AssertionError("Unseeded624RAM");value|=(p.byteValue()&255L)<<(8*k);}return value;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))throw new AssertionError("624 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){steps.add(new Mem(false,width,address,mask(width,value)));}
        void write(int width,long address,long value){steps.add(new Mem(true,width,address,mask(width,value)));}
        void add(long site,long target,long pre,VolatileBits before,long size,boolean df,Mxcsr fp,Outcome outcome,List<Mem> effects,boolean throwing){
            boolean indirect=site==0x424FDDE||site==0x424D012;
            var kind=indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
            long ret=site==0x424FDDE?0x424FDE4:site==0x424FDBD?0x424FDC2:site==0x424D005?0x424D00A:0x424D018;
            var call=new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,before,callN(size));
            steps.add(new Invoke(call,new GovernmentCrtBoundary185Api.Entry(I,pre-8,before,callN(size)),df,fp,I+ret,outcome,effects,throwing));steps.addAll(effects);}
        void effect(Mem e){check(e.write());if(e.width()==1)memory.writeByte(e.address(),(int)e.value());else if(e.width()==4)memory.writeDword(e.address(),(int)e.value());else memory.writeQword(e.address(),e.value());}
        Outcome take(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret){
            check(cursor<steps.size()&&steps.get(cursor) instanceof Invoke);Invoke expected=(Invoke)steps.get(cursor++);
            check(call.equals(expected.call())&&child.equals(expected.child())&&df==expected.df()&&fp==expected.fp()&&ret==expected.ret());calls++;
            for(Mem effect:expected.effects())effect(effect);if(expected.throwing())throw marker;return expected.outcome();}
        Outcome invokeGate(KnownAllocateGateFp624.GateCall frame){return take(frame.original(),frame.childEntry(),frame.directionFlagSet(),frame.preMxcsr(),frame.returnRipBits());}
        Outcome invokeAllocate(KnownHeapAllocateFp623.AllocateCall frame){return take(frame.original(),frame.childEntry(),frame.directionFlagSet(),frame.preMxcsr(),frame.returnRipBits());}
        void done(){check(cursor==steps.size());}
    }
    private static final long GTARGET=0x140334450L;
    private static Normal offered(VolatileBits after,long ret,long pre,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(
        new GovernmentCrtBoundary185Api.NormalReturn(after,I+ret,pre,callN(SIZE)),df),fp);}
    private static Stopped stopped(VolatileBits before,long site,long child,boolean df,Mxcsr fp){return new Stopped(StopReason.MISSING_POST_STATE,
        new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,child,before,callN(SIZE)),site,df,fp),0,site);}
    private static KnownPageFp619.CallFrame page(){var c=new GovernmentCrtBoundary185Api.Call(0x2A322DB,
        GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4223B94,E+8,initial(SIZE),N);
        return new KnownPageFp619.CallFrame(new FullPage495Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,E,initial(SIZE),N),true,5,I+0x2A322E0),P0);}
    private static KnownHeapAllocateFp623.AllocateCall direct(long site,long target,boolean indirect){var before=initial(SIZE);
        var c=new GovernmentCrtBoundary185Api.Call(site,indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            target,E-0x58,before,callN(SIZE));
        return new KnownHeapAllocateFp623.AllocateCall(c,new GovernmentCrtBoundary185Api.Entry(I,E-0x60,before,callN(SIZE)),true,P0);}
    private static KnownHeapAllocateFp623.AllocateCall direct(){return direct(0x424FDC9,0x424CFFC,false);}
    private static KnownHeapAllocateFp623.AllocateCalls bound(Script s){return KnownAllocateGateFp624.bind(s.memory,s::invokeGate,s::invokeAllocate);}
    private static Outcome whole(Script s){var inner=KnownHeapAllocateFp623.bind(s.memory,s.budget,bound(s),
        unused->{throw new AssertionError("Unexpected624Retryforeign");});
        return KnownPageAllocateFp622.bind(s.memory,s.budget,inner,unused->{throw new AssertionError("Unexpected624Pageforeign");}).invoke(page());}
    private static Script directSeeded(){Script s=new Script();s.store(E-0x60,8,I+0x424FDCE);s.store(I+0x43DBBA8,8,GTARGET);return s;}
    private static void gatePrefix(Script s){s.write(8,E-0x68,SIZE);s.write(8,E-0x90,I+0x424D00A);}
    private static void gateEpilogue(Script s,long rbx){s.read(8,E-0x68,rbx);s.read(8,E-0x60,I+0x424FDCE);}
    private static void actualNestedLoop(){Script s=new Script();s.store(E,8,I+0x2A322E0);s.store(I+0x5C5DE30,8,H);s.store(I+0x43DA768,8,TARGET);
        s.write(8,E-8,11);s.steps.add(new Budget(0x4223BAE,SIZE));s.write(8,E-0x30,I+0x4223BB3);s.write(8,E-0x38,SIZE);
        s.read(8,I+0x5C5DE30,H);s.read(8,I+0x43DA768,TARGET);s.write(8,E-0x60,I+0x424FDE4);
        var firstHeap=v(1,H,0,SIZE,0xA9,0xAA,0xAB,0xA0);
        s.add(0x424FDDE,TARGET,E-0x58,firstHeap,SIZE,true,P0,offered(bank(0xB0,0),0x424FDE4,E-0x58,false,P1),List.of(new Mem(true,1,D,1)),false);
        s.steps.add(new Budget(0x424FDBD,0));s.write(8,E-0x60,I+0x424FDC2);
        s.add(0x424FDBD,0x424E250,E-0x58,bank(0xB0,0),SIZE,false,P1,offered(bank(0xC0,0x100000001L),0x424FDC2,E-0x58,true,P2),List.of(),false);
        s.write(8,E-0x60,I+0x424FDCE);gatePrefix(s);var before=v(0x100000001L,SIZE,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0);
        s.add(0x424D005,0x424D02C,E-0x88,before,SIZE,true,P2,offered(bank(0xD0,0x100000000L),0x424D00A,E-0x88,false,P3),
            List.of(new Mem(true,8,I+0x43DBBA8,GTARGET)),false);
        s.read(8,I+0x43DBBA8,GTARGET);s.write(8,E-0x90,I+0x424D018);var second=v(0x100000000L,SIZE,0xD2,0xD8,0xD9,0xDA,0xDB,0xD0);
        s.add(0x424D012,GTARGET,E-0x88,second,SIZE,false,P3,offered(bank(0xE0,0x100000001L),0x424D018,E-0x88,true,P4),List.of(new Mem(true,1,D+1,2)),false);
        gateEpilogue(s,SIZE);s.read(8,I+0x5C5DE30,H);s.read(8,I+0x43DA768,TARGET);s.write(8,E-0x60,I+0x424FDE4);
        var next=v(1,H,0,SIZE,0xE9,0xEA,0xEB,0xE0);var expected=stopped(next,0x424FDDE,E-0x60,false,P1);
        s.add(0x424FDDE,TARGET,E-0x58,next,SIZE,true,P4,expected,List.of(new Mem(true,1,D+2,3)),false);
        check(whole(s)==expected);s.done();check(s.calls==5&&s.load(D,1)==1&&s.load(D+1,1)==2&&s.load(D+2,1)==3&&s.load(E-0x68,8)==SIZE&&s.load(E-8,8)==11);}
    private static void firstZeroAndStopped(){Script s=directSeeded();gatePrefix(s);
        s.add(0x424D005,0x424D02C,E-0x88,initial(SIZE),SIZE,true,P0,offered(bank(0xB0,0),0x424D00A,E-0x88,false,P0),List.of(new Mem(true,1,D,7)),false);
        gateEpilogue(s,SIZE);Normal actual=(Normal)bound(s).invoke(direct());s.done();check(s.calls==1&&s.load(D,1)==7&&actual.postMxcsr()==P0
            &&!actual.base().postDirectionFlagSet()&&actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(bank(0xB0,0),I+0x424FDCE,E-0x58,callN(SIZE))));
        Script stop=directSeeded();gatePrefix(stop);var expected=stopped(initial(SIZE),0x424D005,E-0x90,false,P1);
        stop.add(0x424D005,0x424D02C,E-0x88,initial(SIZE),SIZE,true,P0,expected,List.of(new Mem(true,1,D,8)),false);
        check(bound(stop).invoke(direct())==expected);stop.done();check(stop.calls==1&&stop.load(D,1)==8);}
    private static void fullRaxThenLowEax(){Script s=directSeeded();gatePrefix(s);
        s.add(0x424D005,0x424D02C,E-0x88,initial(SIZE),SIZE,true,P0,offered(bank(0xB0,0x100000000L),0x424D00A,E-0x88,false,P1),List.of(),false);
        s.read(8,I+0x43DBBA8,GTARGET);s.write(8,E-0x90,I+0x424D018);var before=v(0x100000000L,SIZE,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0);
        s.add(0x424D012,GTARGET,E-0x88,before,SIZE,false,P1,offered(bank(0xC0,0x100000000L),0x424D018,E-0x88,true,P2),List.of(),false);
        gateEpilogue(s,SIZE);Normal actual=(Normal)bound(s).invoke(direct());s.done();check(s.calls==2&&actual.postMxcsr()==P2&&actual.base().postDirectionFlagSet()
            &&actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(bank(0xC0,0),I+0x424FDCE,E-0x58,callN(SIZE))));}
    private static void guardsAliasForeignNonmatch(){Script alias=directSeeded();gatePrefix(alias);
        alias.add(0x424D005,0x424D02C,E-0x88,initial(SIZE),SIZE,true,P0,offered(bank(0xB0,0),0x424D00A,E-0x88,false,P1),List.of(new Mem(true,8,E-0x68,0xBAD)),false);
        gateEpilogue(alias,0xBAD);try{bound(alias).invoke(direct());throw new AssertionError("624savedRBXaliasrepaired");}
        catch(IllegalArgumentException expected){alias.done();check(alias.load(E-0x68,8)==0xBAD);}
        for(int k=0;k<3;k++){Script s=directSeeded();gatePrefix(s);var bad=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            bank(0xB0,0),I+0x424D00A+(k==0?1:0),E-0x88-(k==1?8:0),k==2?N:callN(SIZE)),false),P1);
            s.add(0x424D005,0x424D02C,E-0x88,initial(SIZE),SIZE,true,P0,bad,List.of(new Mem(true,1,D,9)),false);
            try{bound(s).invoke(direct());throw new AssertionError("624badNRaccepted");}catch(IllegalArgumentException expected){s.done();check(s.load(D,1)==9);}}
        Script foreign=directSeeded();gatePrefix(foreign);
        foreign.add(0x424D005,0x424D02C,E-0x88,initial(SIZE),SIZE,true,P0,offered(bank(0xB0,0),0x424D00A,E-0x88,false,P1),List.of(new Mem(true,1,D,10)),true);
        try{bound(foreign).invoke(direct());throw new AssertionError("624foreignexceptionlost");}catch(RuntimeException actual){check(actual==foreign.marker);foreign.done();check(foreign.load(D,1)==10);}
        Script other=new Script();var frame=direct(0x424FDDE,TARGET,true);var expected=stopped(initial(SIZE),0x424FDDE,E-0x60,false,P1);
        var result=KnownAllocateGateFp624.bind(other.memory,unused->{throw new AssertionError("624nonmatchgate");},actual->{check(actual==frame);return expected;}).invoke(frame);
        check(result==expected&&other.calls==0);other.done();}
    public static int verify(){actualNestedLoop();firstZeroAndStopped();fullRaxThenLowEax();guardsAliasForeignNonmatch();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
