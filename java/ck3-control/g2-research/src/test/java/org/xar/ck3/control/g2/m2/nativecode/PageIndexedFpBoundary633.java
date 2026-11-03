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

/** Two new Page-callport/Retry60/jump6/whole94 groups entering known error32/fullFC74; selected cache lower path. */
public final class PageIndexedFpBoundary633 {
    private PageIndexedFpBoundary633() { }
    private static final long I=0x140000000L,P=0x8900000000010000L,K=P-0x30L,R=K-0x30L,F=R-0x30L,S=F-0x30L,H=S-0x30L,SIZE=0x172000L,
        HEAP1=0x8900000000004000L,HEAP2=0x8900000000004100L,BLOCK2=0x8900000000005000L,THEAP1=0xD123456789ABCDEFL,THEAP2=0xE123456789ABCDEFL,
        ADDR=0x8900000000002003L,D=0x8900000000003000L,GETERR=0x12345678L,TGET=0xA123456789ABCDEFL,TSET=0xB123456789ABCDEFL,TAIL=0xC123456789ABCDEFL,
        FACT=I+0x4420C50,FIRST=I+0x4426F28,END=I+0x4426F30,TABLE=I+5*8+0x5C5D790;
    private static final Mxcsr PIN=Mxcsr.unknown(),PH=new Mxcsr(8,8),PG=new Mxcsr(4,4),P6=new Mxcsr(0x80,0x80),P0=Mxcsr.unknown(),P1=new Mxcsr(0x20,0x20),P2=Mxcsr.unknown(),P3=new Mxcsr(0x40,0x40);
    private static Bits128 x(long b,int k){return new Bits128(b+k,0xD000000000000000L+b+k);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long b){return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,x(b,0),x(b,1),x(b,2),x(b,3),x(b,4),x(b,5));}
    private static NonvolatileBits nv(long bx,long bp,long si,long di,long r12,long r13,long r14,long r15){return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,x(0xA0,6));}
    private static final VolatileBits INIT=v(0x90,SIZE,0x92,0x98,0x99,0x9A,0x9B,0x90),HEAP_BEFORE=v(1,HEAP1,0,SIZE,0x99,0x9A,0x9B,0x90),
        HEAP_ZERO=v(0,0x91,0x92,0x98,0x99,0x9A,0x9B,0x90),A=v(0,0xA1,0xA2,0xA8,0xA9,0xAA,0xAB,0xA0),B=v(0xFFFF000012345678L,0xB1,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0),
        FC_BEFORE=v(0xFFFF000012345678L,5,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0),TAIL_BEFORE=v(ADDR,5,ADDR,FIRST,END,0,0xBB,0xB0),
        TAIL_AFTER=v(ADDR,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),SET_BEFORE=v(ADDR,GETERR,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),SET_AFTER=v(0xD0,0xD1,0xD2,0xD8,0xD9,0xDA,0xDB,0xD0),
        GATE_BEFORE=v(0,SIZE,0xD2,0xD8,0xD9,0xDA,0xDB,0xD0),GATE_AFTER=v(1,0xE1,0xE2,0xE8,0xE9,0xEA,0xEB,0xE0),
        HEAP2_BEFORE=v(1,HEAP2,0,SIZE,0xE9,0xEA,0xEB,0xE0),FINAL=v(BLOCK2,0xF1,0xF2,0xF8,0xF9,0xFA,0xFB,0xF0);
    private static final NonvolatileBits N0=nv(0x11,0x33,0x44,0x22,0x55,0x66,0x77,0x88),N=nv(SIZE,0x33,0x44,0x22,0x55,0x66,0x77,0x88),NFC=nv(GETERR,0x33,0x44,0x22,0x55,0x66,0x77,0x88),NSET=nv(GETERR,0x33,ADDR,ADDR,0x55,0x66,0x77,0x88);
    private static void check(boolean b){if(!b)throw new AssertionError("633 source-literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Budget(long header,long guard) { }
    private record AllocateEvent(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret,Outcome out,List<Mem> effects) { }
    private record RetryEvent(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret,Outcome out,List<Mem> effects) { }
    private record Foreign(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret,Outcome out,List<Mem> effects) { }
    private record TailEvent(GovernmentCrtBoundary185Api.Tail tail,boolean df,Mxcsr fp,Outcome out) { }
    private static final class Script {
        final Map<Long,Byte> ram=new HashMap<>();final List<Object> events=new ArrayList<>();int cursor,fcCalls,tails,allocateCalls,retryCalls,budgets;
        final KnownPageIndexedFp633.Memory memory=(KnownPageIndexedFp633.Memory)Proxy.newProxyInstance(KnownPageIndexedFp633.Memory.class.getClassLoader(),new Class<?>[]{KnownPageIndexedFp633.Memory.class},(proxy,method,args)->{
            String name=method.getName();int width;if(name.equals("readQword")||name.equals("writeQword"))width=8;else if(name.equals("readDword")||name.equals("writeDword"))width=4;else throw new AssertionError("633 unexpected operation "+name);
            long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,width);
            event(new Mem(write,width,address,width==4?value&0xFFFFFFFFL:value));if(write){store(address,width,value);return null;}if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
        });
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{event(new Budget(header,guard));budgets++;};
        void store(long a,int w,long v){for(int k=0;k<w;k++)ram.put(a+k,Byte.valueOf((byte)(v>>>(8*k))));}
        long load(long a,int w){long v=0;for(int k=0;k<w;k++){Byte z=ram.get(a+k);if(z==null)throw new AssertionError("633 unseeded RAM");v|=(z.byteValue()&255L)<<(8*k);}return v;}
        void event(Object actual){if(cursor>=events.size()||!events.get(cursor++).equals(actual))throw new AssertionError("633 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){events.add(new Mem(false,width,address,width==4?value&0xFFFFFFFFL:value));}
        void write(long address,long value){events.add(new Mem(true,8,address,value));}
        void done(){check(cursor==events.size());}
        Outcome fc(Fc74Fp626Api.CallFrame f){check(cursor<events.size()&&events.get(cursor) instanceof Foreign);Foreign e=(Foreign)events.get(cursor++);
            check(f.original().equals(e.call())&&f.childEntry().equals(e.child())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==e.ret());fcCalls++;
            for(Mem m:e.effects())memory.writeQword(m.address(),m.value());return e.out();}
        Outcome allocate(KnownHeapAllocateFp623.AllocateCall f){check(cursor<events.size()&&events.get(cursor) instanceof AllocateEvent);AllocateEvent e=(AllocateEvent)events.get(cursor++);
            check(f.original().equals(e.call())&&f.childEntry().equals(e.child())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==e.ret());allocateCalls++;
            for(Mem m:e.effects())memory.writeQword(m.address(),m.value());return e.out();}
        Outcome retry(KnownPageAllocateFp622.RetryCall f){check(cursor<events.size()&&events.get(cursor) instanceof RetryEvent);RetryEvent e=(RetryEvent)events.get(cursor++);
            check(f.original().equals(e.call())&&f.childEntry().equals(e.child())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==e.ret());retryCalls++;
            for(Mem m:e.effects())memory.writeQword(m.address(),m.value());return e.out();}
        Outcome tail(E900Fp627Api.TailFrame f){check(cursor<events.size()&&events.get(cursor) instanceof TailEvent);TailEvent e=(TailEvent)events.get(cursor++);
            check(f.original().equals(e.tail())&&f.caller().equals(fcFrame())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==I+0x424FC9B);tails++;return e.out();}
    }
    private static KnownPageFp619.CallFrame outer(){var c=new GovernmentCrtBoundary185Api.Call(0x2A322DB,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4223B94,P+8,INIT,N0);return new KnownPageFp619.CallFrame(new FullPage495Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,P,INIT,N0),true,5,I+0x2A322E0),PIN);}
    private static Fc74Fp626Api.CallFrame fcFrame(){var c=new GovernmentCrtBoundary185Api.Call(0x424FC96,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E900,F-0x28,FC_BEFORE,NFC);return new Fc74Fp626Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S,FC_BEFORE,NFC),false,P1);}
    private static Outcome execute(Script s){E900Fp627Api.Calls e900=new E900Fp627Api.Calls(){
        @Override public Outcome invoke(E900Fp627Api.CallFrame unused){throw new AssertionError("633 unexpected E900 foreignCALL");}
        @Override public Outcome tail(E900Fp627Api.TailFrame f){return s.tail(f);}};
        return KnownPageIndexedFp633.bind(s.memory,s.budget,unused->{throw new AssertionError("633 unexpected Indexed foreignCALL");},e900,s::fc,unused->{throw new AssertionError("633 unexpected Error foreign");},s::allocate,s::retry,unused->{throw new AssertionError("633 unexpected Page foreign");}).invoke(outer());}
    private static Normal normal(VolatileBits v,long ret,long sp,NonvolatileBits n,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,I+ret,sp,n),df),fp);}
    private static Script seeded(){Script s=new Script();s.store(P,8,I+0x2A322E0);s.store(I+0x5C5DE30,8,HEAP1);s.store(I+0x43DA768,8,THEAP1);s.store(I+0x43DA738,8,TGET);s.store(I+0x43DA420,8,TSET);s.store(I+0x542F328,4,5);s.store(TABLE,8,ADDR);s.store(I+0x542F0B8,8,0);s.store(I+0x43DBBA8,8,TAIL);return s;}
    private static void addFc(Script s,long site,long target,VolatileBits before,NonvolatileBits n,boolean df,Mxcsr fp,Outcome out,List<Mem> effects){var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,F-0x28,before,n);s.events.add(new Foreign(call,new GovernmentCrtBoundary185Api.Entry(I,F-0x30,before,n),df,fp,I+site+6,out,effects));s.events.addAll(effects);}
    private static void prefix(Script s){s.write(F,I+0x423B195);s.write(F+8,SIZE);s.write(F+0x10,0x44);s.write(F-8,0x22);
        s.read(8,I+0x43DA738,TGET);s.write(F-0x30,I+0x424FC89);addFc(s,0x424FC83,TGET,A,N,true,P0,normal(B,0x424FC89,F-0x28,N,false,P1),List.of());
        s.read(4,I+0x542F328,5);s.write(S,I+0x424FC9B);s.write(S-8,GETERR);s.write(H,I+0x424E927);s.write(H+8,5);s.write(H+0x10,0x33);s.write(H+0x18,0x44);s.write(H-8,0x22);s.write(H-0x10,0x55);s.write(H-0x18,0x66);s.write(H-0x20,0x77);s.write(H-0x28,0x88);
        s.read(8,TABLE,ADDR);s.read(8,I+0x542F0B8,0);s.read(8,H+8,5);s.read(8,H+0x10,0x33);s.read(8,H+0x18,0x44);s.read(8,H-0x28,0x88);s.read(8,H-0x20,0x77);s.read(8,H-0x18,0x66);s.read(8,H-0x10,0x55);s.read(8,H-8,0x22);s.read(8,H,I+0x424E927);s.read(8,S-8,GETERR);s.read(8,I+0x43DBBA8,TAIL);}
    private static void addTail(Script s,Outcome out){s.events.add(new TailEvent(new GovernmentCrtBoundary185Api.Tail(0x424E933,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,TAIL,new GovernmentCrtBoundary185Api.Entry(I,S,TAIL_BEFORE,NFC)),false,P1,out));}
    private static void suffix(Script s,boolean alias){s.read(8,I+0x43DA420,TSET);s.write(F-0x30,I+0x424FD27);var effects=alias?List.of(new Mem(true,8,P,0xBAD)):List.<Mem>of();
        addFc(s,0x424FD21,TSET,SET_BEFORE,NSET,true,P2,normal(SET_AFTER,0x424FD27,F-0x28,NSET,false,P3),effects);
        s.read(8,F+8,SIZE);s.read(8,F+0x10,0x44);s.read(8,F-8,0x22);s.read(8,F,I+0x423B195);s.read(8,R,I+0x424FDF0);}
    private static void addAllocate(Script s,long site,long target,VolatileBits before,boolean df,Mxcsr fp,Normal out){var kind=site==0x424FDDE?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;long ret=site==0x424FDDE?0x424FDE4:0x424FDC2;
        var call=new GovernmentCrtBoundary185Api.Call(site,kind,target,K-0x28,before,N);s.events.add(new AllocateEvent(call,new GovernmentCrtBoundary185Api.Entry(I,R,before,N),df,fp,I+ret,out,List.of()));}
    private static void upstreamPrefix(Script s){s.write(P-8,0x11);s.events.add(new Budget(0x4223BAE,SIZE));s.write(K,I+0x4223BB3);s.write(K-8,SIZE);s.read(8,I+0x5C5DE30,HEAP1);s.read(8,I+0x43DA768,THEAP1);s.write(R,I+0x424FDE4);
        addAllocate(s,0x424FDDE,THEAP1,HEAP_BEFORE,true,PIN,normal(HEAP_ZERO,0x424FDE4,K-0x28,N,false,PH));s.events.add(new Budget(0x424FDBD,0));s.write(R,I+0x424FDC2);
        addAllocate(s,0x424FDBD,0x424E250,HEAP_ZERO,false,PH,normal(A,0x424FDC2,K-0x28,N,true,P0));s.write(R,I+0x424FDF0);prefix(s);}
    private static void retryAndSuccess(Script s,boolean alias){s.events.add(new Mem(true,4,ADDR+0x20,12));s.read(8,K-8,SIZE);s.read(8,K,I+0x4223BB3);s.write(K,I+0x4223BA7);
        var call=new GovernmentCrtBoundary185Api.Call(0x4223BA2,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424CFFC,P-0x28,GATE_BEFORE,N);
        var effects=List.of(new Mem(true,8,I+0x5C5DE30,HEAP2),new Mem(true,8,I+0x43DA768,THEAP2));s.events.add(new RetryEvent(call,new GovernmentCrtBoundary185Api.Entry(I,K,GATE_BEFORE,N),false,P3,I+0x4223BA7,normal(GATE_AFTER,0x4223BA7,P-0x28,N,true,PG),effects));s.events.addAll(effects);
        s.events.add(new Budget(0x4223BAE,SIZE));s.write(K,I+0x4223BB3);s.write(K-8,SIZE);s.read(8,I+0x5C5DE30,HEAP2);s.read(8,I+0x43DA768,THEAP2);s.write(R,I+0x424FDE4);
        addAllocate(s,0x424FDDE,THEAP2,HEAP2_BEFORE,true,PG,normal(FINAL,0x424FDE4,K-0x28,N,false,P6));s.read(8,K-8,SIZE);s.read(8,K,I+0x4223BB3);s.read(8,P-8,0x11);s.read(8,P,alias?0xBAD:I+0x2A322E0);}
    private static void wholeNormal(){Script s=seeded();upstreamPrefix(s);addTail(s,normal(TAIL_AFTER,0x424FC9B,F-0x28,NFC,true,P2));suffix(s,false);retryAndSuccess(s,false);Normal actual=(Normal)execute(s);s.done();
        check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(FINAL,I+0x2A322E0,P+8,N0))&&!actual.base().postDirectionFlagSet()&&actual.postMxcsr()==P6);
        check(s.fcCalls==2&&s.tails==1&&s.allocateCalls==3&&s.retryCalls==1&&s.budgets==3&&s.load(ADDR+0x20,4)==12&&s.load(I+0x5C5DE30,8)==HEAP2&&s.load(I+0x43DA768,8)==THEAP2);}
    private static void wholeFailures(){Script stop=seeded();upstreamPrefix(stop);Stopped out=new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,S,TAIL_BEFORE,NFC),0x424E933,false,P1),0,0x424E933);addTail(stop,out);check(execute(stop)==out);stop.done();check(stop.fcCalls==1&&stop.tails==1&&stop.allocateCalls==2&&stop.retryCalls==0&&stop.budgets==2);
        Script bad=seeded();upstreamPrefix(bad);addTail(bad,normal(TAIL_AFTER,0x424FC9B,F-0x28,NFC,true,P2));suffix(bad,true);retryAndSuccess(bad,true);try{execute(bad);throw new AssertionError("633 repaired bad outerRET");}catch(IllegalArgumentException expected){bad.done();check(bad.fcCalls==2&&bad.tails==1&&bad.allocateCalls==3&&bad.retryCalls==1&&bad.budgets==3&&bad.load(P,8)==0xBAD&&bad.load(ADDR+0x20,4)==12);}}
    public static int verify(){wholeNormal();wholeFailures();return 2;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
