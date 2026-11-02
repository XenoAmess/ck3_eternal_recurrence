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

/** Four new allocator FP factory groups; opaque child offers are declared fixture inputs. */
public final class PageAllocateFpBoundary622 {
    private PageAllocateFpBoundary622() { }
    private static final long I=0x140000000L,E=0x8600000000008000L,D=0x8600000000002000L,
        ADDR=0x8600000000004000L,SIZE=0x172000L;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=new Mxcsr(0x40,0x40),P3=new Mxcsr(4,4);
    private static Bits128 x(long bank,int lane){return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long bank){return new VolatileBits(
        ax,cx,dx,r8,r9,r10,r11,x(bank,0),x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));}
    private static final VolatileBits INITIAL=v(0xA0,SIZE,0xA2,0xA8,0xA9,0xAA,0xAB,0xA0);
    private static final NonvolatileBits N=new NonvolatileBits(11,22,33,44,55,66,77,88,x(0xA0,6)),
        CALL_N=new NonvolatileBits(SIZE,22,33,44,55,66,77,88,x(0xA0,6));
    private static VolatileBits b(long ax){return v(ax,0xB1,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0);}
    private static VolatileBits c(){return v(0x100000001L,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0);}
    private static void check(boolean value){if(!value)throw new AssertionError("622 source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Budget(long header,long guard) { }
    private record Invoke(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
        boolean df,Mxcsr fp,long ret,Outcome outcome,List<Mem> effects,boolean throwing) { }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls;
        final RuntimeException marker=new IllegalStateException("622 original foreign callback");
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->event(new Budget(header,guard));
        final KnownPageFp619.Memory memory=(KnownPageFp619.Memory)Proxy.newProxyInstance(KnownPageFp619.Memory.class.getClassLoader(),
            new Class<?>[]{KnownPageFp619.Memory.class},(proxy,method,args)->{
                String name=method.getName();int width;
                if(name.equals("readUnsignedByte")||name.equals("read8")||name.equals("writeByte")||name.equals("write8"))width=1;
                else if(name.equals("readDword")||name.equals("read32")||name.equals("writeDword")||name.equals("write32"))width=4;
                else if(name.equals("readQword")||name.equals("read64")||name.equals("writeQword")||name.equals("write64"))width=8;
                else throw new AssertionError("Unexpected622Memory "+name);
                long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");
                long value=write?((Number)args[1]).longValue():load(address,width);event(new Mem(write,width,address,mask(width,value)));
                if(write){store(address,width,value);return null;}if(width==1)return Integer.valueOf((int)value&255);
                if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long address,int width,long value){for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long address,int width){long value=0;for(int k=0;k<width;k++){Byte p=ram.get(address+k);if(p==null)throw new AssertionError("Unseeded622RAM");value|=(p.byteValue()&255L)<<(8*k);}return value;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))throw new AssertionError("622 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){steps.add(new Mem(false,width,address,mask(width,value)));}
        void write(int width,long address,long value){steps.add(new Mem(true,width,address,mask(width,value)));}
        void add(long site,VolatileBits before,boolean df,Mxcsr fp,Outcome outcome,List<Mem> effects,boolean throwing){
            long target=site==0x4223BAE?0x42420B8:0x424CFFC,ret=site==0x4223BAE?0x4223BB3:0x4223BA7;
            var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,E-0x28,before,CALL_N);
            steps.add(new Invoke(call,new GovernmentCrtBoundary185Api.Entry(I,E-0x30,before,CALL_N),df,fp,I+ret,outcome,effects,throwing));steps.addAll(effects);}
        void effect(Mem e){check(e.write());if(e.width()==1)memory.writeByte(e.address(),(int)e.value());else if(e.width()==4)memory.writeDword(e.address(),(int)e.value());else memory.writeQword(e.address(),e.value());}
        Outcome invoke(KnownPageAllocateFp622.RetryCall actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Invoke);
            Invoke expected=(Invoke)steps.get(cursor++);check(actual.original().equals(expected.call())&&actual.childEntry().equals(expected.child())
                &&actual.directionFlagSet()==expected.df()&&actual.preMxcsr()==expected.fp()&&actual.returnRipBits()==expected.ret());calls++;
            for(Mem effect:expected.effects())effect(effect);if(expected.throwing())throw marker;return expected.outcome();}
        void done(){check(cursor==steps.size());}
    }
    private static KnownPageFp619.CallFrame frame(long site,long target,long ret){var call=new GovernmentCrtBoundary185Api.Call(site,
        GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,E+8,INITIAL,N);
        return new KnownPageFp619.CallFrame(new FullPage495Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E,INITIAL,N),true,5,I+ret),P0);}
    private static KnownPageFp619.CallFrame frame(){return frame(0x2A322DB,0x4223B94,0x2A322E0);}
    private static Script seeded(){Script s=new Script();s.store(E,8,I+0x2A322E0);return s;}
    private static Normal offered(VolatileBits after,long ret,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(
        new GovernmentCrtBoundary185Api.NormalReturn(after,I+ret,E-0x28,CALL_N),df),fp);}
    private static Stopped stopped(VolatileBits before,long site,boolean df,Mxcsr fp){return new Stopped(StopReason.MISSING_POST_STATE,
        new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,E-0x30,before,CALL_N),site,df,fp),0,site);}
    private static Outcome execute(Script s){return KnownPageAllocateFp622.bind(s.memory,s.budget,s::invoke,
        unused->{throw new AssertionError("Unexpected622foreign");}).invoke(frame());}
    private static void firstPrefix(Script s){s.write(8,E-8,11);s.steps.add(new Budget(0x4223BAE,SIZE));s.write(8,E-0x30,I+0x4223BB3);}
    private static void firstNormal(){Script s=seeded();firstPrefix(s);s.add(0x4223BAE,INITIAL,true,P0,offered(b(ADDR),0x4223BB3,false,P1),List.of(new Mem(true,1,D,123)),false);
        s.read(8,E-8,11);s.read(8,E,I+0x2A322E0);var actual=(Normal)execute(s);s.done();check(s.calls==1&&s.load(D,1)==123);
        check(actual.postMxcsr()==P1&&!actual.base().postDirectionFlagSet()&&actual.base().normalReturn().equals(
            new GovernmentCrtBoundary185Api.NormalReturn(b(ADDR),I+0x2A322E0,E+8,N)));}
    private static void firstStopped(){Script s=seeded();firstPrefix(s);var expected=stopped(INITIAL,0x4223BAE,false,P1);
        s.add(0x4223BAE,INITIAL,true,P0,expected,List.of(new Mem(true,1,D,77)),false);check(execute(s)==expected);s.done();check(s.calls==1&&s.load(D,1)==77&&s.load(E-8,8)==11);}
    private static void retryState(){Script s=seeded();firstPrefix(s);s.add(0x4223BAE,INITIAL,true,P0,offered(b(0),0x4223BB3,false,P1),List.of(new Mem(true,1,D,123)),false);
        s.write(8,E-0x30,I+0x4223BA7);var handlerBefore=v(0,SIZE,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0);
        s.add(0x4223BA2,handlerBefore,false,P1,offered(c(),0x4223BA7,true,P2),List.of(),false);
        s.steps.add(new Budget(0x4223BAE,SIZE));s.write(8,E-0x30,I+0x4223BB3);var next=v(0x100000001L,SIZE,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0);
        var expected=stopped(next,0x4223BAE,true,P3);s.add(0x4223BAE,next,true,P2,expected,List.of(new Mem(true,1,D+1,77)),false);
        check(execute(s)==expected);s.done();check(s.calls==3&&s.load(D,1)==123&&s.load(D+1,1)==77&&s.load(E-0x30,8)==I+0x4223BB3&&s.load(E-8,8)==11);}
    private static void guardsAliasForeignNonmatch(){for(int kind=0;kind<3;kind++){Script s=seeded();firstPrefix(s);
        var wrongN=kind==2?N:CALL_N;long rip=I+0x4223BB3+(kind==0?1:0),sp=E-0x28-(kind==1?8:0);
        var bad=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(b(ADDR),rip,sp,wrongN),false),P1);
        s.add(0x4223BAE,INITIAL,true,P0,bad,List.of(new Mem(true,1,D,99)),false);
        try{execute(s);throw new AssertionError("Bad622innerNormalaccepted");}catch(IllegalArgumentException expected){s.done();check(s.calls==1&&s.load(D,1)==99);}}
        Script alias=seeded();firstPrefix(alias);alias.add(0x4223BAE,INITIAL,true,P0,offered(b(ADDR),0x4223BB3,false,P1),List.of(new Mem(true,8,E-8,0xBAD)),false);
        alias.read(8,E-8,0xBAD);alias.read(8,E,I+0x2A322E0);
        try{execute(alias);throw new AssertionError("622freshRBXaliasrepaired");}catch(IllegalArgumentException expected){alias.done();check(alias.calls==1&&alias.load(E-8,8)==0xBAD);}
        Script foreign=seeded();firstPrefix(foreign);foreign.add(0x4223BAE,INITIAL,true,P0,offered(b(ADDR),0x4223BB3,false,P1),List.of(new Mem(true,1,D,88)),true);
        try{execute(foreign);throw new AssertionError("622foreignexceptionlost");}catch(RuntimeException actual){check(actual==foreign.marker);foreign.done();check(foreign.calls==1&&foreign.load(D,1)==88);}
        Script other=new Script();var f=frame(0x2A322A3,0x4223F44,0x2A322A8);
        var expected=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(b(ADDR),I+0x2A322A8,E+8,N),false),P1);
        var result=KnownPageAllocateFp622.bind(other.memory,other.budget,unused->{throw new AssertionError("622nonmatchallocator");},actual->{check(actual==f);return expected;}).invoke(f);
        check(result==expected&&other.calls==0);other.done();}
    public static int verify(){firstNormal();firstStopped();retryState();guardsAliasForeignNonmatch();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
