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
import org.xar.ck3.study.m6.indexed229.AtomicIndexedMemory229;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;

/** Four new same-call whole-composition groups over actual70B plus470B; opaque lower outcomes remain explicit. */
public final class Fc74IndexedFpBoundary629 {
    private Fc74IndexedFpBoundary629() { }
    private static final long I=0x140000000L,S=0x890000000000C000L,E=S-0x30L,FACT=I+0x4420C50,FIRST=I+0x4426F28,END=I+0x4426F30,
        TABLE=I+5*8+0x5C5D790,SLOT=I+2*8+0x5C5D6F0,PROVIDER=0x8900000000002000L,BLOCK=0x8900000000003000L,
        RESULT=0x8900000000004000L,ALT=0xF123456789ABCDEFL,D=0x8900000000005000L,T1=0xE123456789ABCDEFL,T2=0xD123456789ABCDEFL,ADDR=0x89000000000030F3L;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=new Mxcsr(0x40,0x40),P3=new Mxcsr(8,8);
    private static final long IDX=0xF1234567L,TAIL=0xC123456789ABCDEFL;
    private static final long[] SITES={0x424E4EB,0x424E4F9,0x424E514,0x424E52A,0x424E53B,0x424E574,0x424E5A0};
    private static final long[] RETS={0x424E4F1,0x424E4FF,0x424E519,0x424E52F,0x424E541,0x424E57A,0x424E5A6};
    private static Bits128 x(long b,int k){return new Bits128(b+k,0xD000000000000000L+b+k);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long b){return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,x(b,0),x(b,1),x(b,2),x(b,3),x(b,4),x(b,5));}
    private static NonvolatileBits nv(long bx,long bp,long si,long di,long r12,long r13,long r14,long r15){return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,x(0xA0,6));}
    private static final VolatileBits A=v(0xA0,0xFFFF0000F1234567L,0xA2,0xA8,0xA9,0xAA,0xAB,0xA0),BEFORE1=v(0,PROVIDER,0,0x800,END,0,0xAB,0xA0),B=v(BLOCK,0xB1,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0),
        BEFORE2=v(0,BLOCK,FACT,0xB8,0xB9,0,0xBB,0xB0),C=v(RESULT,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),Q=v(0xD0,0xD1,0xD2,0xD8,0xD9,0xDA,0xDB,0xD0);
    private static final NonvolatileBits N=nv(0x11,0x33,0x44,0x22,0x55,0x66,0x77,0x88),NLOOK=nv(IDX,0x33,0x44,0x22,0x55,0x66,0x77,0x88),N1=nv(0,FIRST,2,-1,END,FACT,PROVIDER,5),N2=nv(BLOCK,FIRST,2,-1,END,FACT,I,5);
    private static void check(boolean b){if(!b)throw new AssertionError("629 source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Exchange(long address,long newBits,long oldBits) { }
    private record Budget(long header,long guard) { }
    private record Invoke(GovernmentCrtBoundary185Api.Call original,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret,Outcome out,List<Mem> effects,boolean throwing) { }
    private record TailEvent(GovernmentCrtBoundary185Api.Tail original,boolean df,Mxcsr fp,Outcome out,List<Mem> effects) { }
    private static final class Script {
        final List<Object> events=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls,exchanges,tailcalls;
        final Fc74Fp626Api.CallFrame caller=frame();
        final RuntimeException marker=new IllegalStateException("629 original callback or budget exception");boolean budgetThrows;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{event(new Budget(header,guard));if(budgetThrows)throw marker;};
        final AtomicIndexedMemory229 memory=(AtomicIndexedMemory229)Proxy.newProxyInstance(AtomicIndexedMemory229.class.getClassLoader(),new Class<?>[]{AtomicIndexedMemory229.class},(proxy,method,args)->{
            String name=method.getName();long address=((Long)args[0]).longValue();
            if(name.equals("exchangeQword")){long value=((Long)args[1]).longValue(),old=load(address,8);event(new Exchange(address,value,old));exchanges++;store(address,8,value);return Long.valueOf(old);}
            int width;if(name.equals("readQword")||name.equals("writeQword"))width=8;else if(name.equals("readDword")||name.equals("writeDword"))width=4;else throw new AssertionError("Unexpected629Memory "+name);
            boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,width);event(new Mem(write,width,address,width==4?value&0xFFFFFFFFL:value));
            if(write){store(address,width,value);return null;}if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
        });
        void store(long a,int w,long v){for(int k=0;k<w;k++)ram.put(a+k,Byte.valueOf((byte)(v>>>(8*k))));}
        long load(long a,int w){long v=0;for(int k=0;k<w;k++){Byte z=ram.get(a+k);if(z==null)throw new AssertionError("Unseeded629RAM");v|=(z.byteValue()&255L)<<(8*k);}return v;}
        void event(Object actual){if(cursor>=events.size()||!events.get(cursor++).equals(actual))throw new AssertionError("629 cursor "+(cursor-1)+" actual="+actual);}
        void write(long a,long v){events.add(new Mem(true,8,a,v));}void read(int w,long a,long v){events.add(new Mem(false,w,a,w==4?v&0xFFFFFFFFL:v));}
        void add(int idx,VolatileBits before,NonvolatileBits n,boolean df,Mxcsr fp,Outcome out,List<Mem> effects,boolean throwing){long target=idx==2||idx==3?0x4246A60:idx==6?T2:T1;
            var call=new GovernmentCrtBoundary185Api.Call(SITES[idx],idx==2||idx==3?GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA:GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,E-0x48,before,n);
            events.add(new Invoke(call,new GovernmentCrtBoundary185Api.Entry(I,E-0x50,before,n),df,fp,I+RETS[idx],out,effects,throwing));events.addAll(effects);}
        Outcome invoke(Indexed448Fp628Api.CallFrame f){check(cursor<events.size()&&events.get(cursor) instanceof Invoke);Invoke e=(Invoke)events.get(cursor++);
            check(f.original().equals(e.original())&&f.childEntry().equals(e.child())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==e.ret());calls++;
            for(Mem effect:e.effects()){if(effect.width()==4)memory.writeDword(effect.address(),(int)effect.value());else memory.writeQword(effect.address(),effect.value());}
            if(e.throwing())throw marker;return e.out();}
        Outcome tail(E900Fp627Api.TailFrame f){check(cursor<events.size()&&events.get(cursor) instanceof TailEvent);TailEvent e=(TailEvent)events.get(cursor++);
            check(f.original().equals(e.original())&&f.caller()==caller&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==I+0x424FC9B);tailcalls++;
            for(Mem m:e.effects())memory.writeQword(m.address(),m.value());return e.out();}
        void done(){check(cursor==events.size());}
    }
    private static Fc74Fp626Api.CallFrame frame(){var c=new GovernmentCrtBoundary185Api.Call(0x424FC96,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E900,S+8,A,N);
        return new Fc74Fp626Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S,A,N),true,P0);}
    private static E900Fp627Api.Calls lower(Script s){return new E900Fp627Api.Calls(){
        @Override public Outcome invoke(E900Fp627Api.CallFrame unused){throw new AssertionError("Unexpected629E900foreigninvoke");}
        @Override public Outcome tail(E900Fp627Api.TailFrame f){return s.tail(f);}};}
    private static Outcome execute(Script s){return KnownFc74IndexedFp629.bind(s.memory,s.budget,s::invoke,lower(s),unused->{throw new AssertionError("Unexpected629outerforeign");}).invoke(s.caller);}
    private static Script seeded(){Script s=new Script();s.store(TABLE,8,0);s.store(I+0x542F0B8,8,0);s.store(FIRST,4,2);s.store(SLOT,8,0);s.store(I+2*8+0x44269D0,8,PROVIDER);s.store(I+0x43DA478,8,T1);s.store(I+0x43DA680,8,T2);s.store(I+0x43DBBA8,8,TAIL);return s;}
    private static void prologue(Script s){s.write(S-8,0x11);s.write(E,I+0x424E927);s.write(E+8,IDX);s.write(E+0x10,0x33);s.write(E+0x18,0x44);s.write(E-8,0x22);s.write(E-0x10,0x55);s.write(E-0x18,0x66);s.write(E-0x20,0x77);s.write(E-0x28,0x88);}
    private static void restore(Script s){s.read(8,E+8,IDX);s.read(8,E+0x10,0x33);s.read(8,E+0x18,0x44);s.read(8,E-0x28,0x88);s.read(8,E-0x20,0x77);s.read(8,E-0x18,0x66);s.read(8,E-0x10,0x55);s.read(8,E-8,0x22);s.read(8,E,I+0x424E927);s.read(8,S-8,0x11);s.read(8,I+0x43DBBA8,TAIL);}
    private static void prefix(Script s){prologue(s);s.read(8,TABLE,0);s.read(8,I+0x542F0B8,0);s.events.add(new Budget(0x424E4BA,FIRST));s.read(4,FIRST,2);s.read(8,SLOT,0);s.read(8,I+2*8+0x44269D0,PROVIDER);s.read(8,I+0x43DA478,T1);s.write(E-0x50,I+0x424E4F1);}
    private static Normal offer(VolatileBits v,int idx,NonvolatileBits n,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,I+RETS[idx],E-0x48,n),df),fp);}
    private static Stopped stopped(long pc,GovernmentCrtBoundary185Api.Entry e){return new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(e,pc,false,P3),0,pc);}
    private static void addTail(Script s,VolatileBits v,boolean df,Mxcsr fp,Outcome out,List<Mem> effects){s.events.add(new TailEvent(new GovernmentCrtBoundary185Api.Tail(0x424E933,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,TAIL,new GovernmentCrtBoundary185Api.Entry(I,S,v,N)),df,fp,out,effects));s.events.addAll(effects);}
    private static VolatileBits fastTail(){return v(ADDR,IDX,ADDR,FIRST,END,0,0xAB,0xA0);}
    private static void cachedPrefix(Script s){s.store(TABLE,8,ADDR);prologue(s);s.read(8,TABLE,ADDR);s.read(8,I+0x542F0B8,0);restore(s);}
    private static Normal tailNormal(NonvolatileBits n){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(Q,I+0x424FC9B,S+8,n),false),P3);}
    private static void cacheWhole(){Script s=seeded();cachedPrefix(s);Normal offered=tailNormal(N);addTail(s,fastTail(),true,P0,offered,List.of(new Mem(true,8,D,7)));Normal actual=(Normal)execute(s);s.done();check(s.calls==0&&s.exchanges==0&&s.tailcalls==1&&s.load(D,8)==7);check(actual.base().normalReturn()==offered.base().normalReturn()&&actual.postMxcsr()==P3&&!actual.base().postDirectionFlagSet());}
    private static void stoppedWhole(){Script s=seeded();prefix(s);Stopped offered=stopped(0x424E4EB,new GovernmentCrtBoundary185Api.Entry(I,E-0x50,BEFORE1,N1));s.add(0,BEFORE1,N1,true,P0,offered,List.of(new Mem(true,8,D,8)),false);check(execute(s)==offered);s.done();check(s.calls==1&&s.exchanges==0&&s.tailcalls==0&&s.load(D,8)==8);}
    private static void normalWholePrefix(Script s){prefix(s);s.add(0,BEFORE1,N1,true,P0,offer(B,0,N1,false,P1),List.of(new Mem(true,8,D,9)),false);s.events.add(new Exchange(SLOT,BLOCK,0));s.read(8,I+0x542F0B8,0);s.read(8,I+0x43DA680,T2);s.write(E-0x50,I+0x424E5A6);s.add(6,BEFORE2,N2,false,P1,offer(C,6,N2,true,P2),List.of(new Mem(true,8,TABLE,ALT)),false);s.read(8,I+0x542F0B8,0);s.events.add(new Exchange(TABLE,RESULT,ALT));restore(s);}
    private static void deepNormalTailStop(){Script s=seeded();normalWholePrefix(s);VolatileBits before=v(RESULT,IDX,ALT,0,0xC9,0xCA,0xCB,0xC0);Stopped offered=stopped(0x424E933,new GovernmentCrtBoundary185Api.Entry(I,S,before,N));addTail(s,before,true,P2,offered,List.of(new Mem(true,8,D,12)));check(execute(s)==offered);s.done();check(s.calls==2&&s.exchanges==2&&s.tailcalls==1&&s.load(TABLE,8)==RESULT&&s.load(SLOT,8)==BLOCK&&s.load(D,8)==12);}
    private static void rejectedNull(Runnable f){try{f.run();throw new AssertionError("629nullaccepted");}catch(NullPointerException expected){/* pure creation contract */}}
    private static void pureFactoryAndBadTail(){Script s=seeded();var inner=(Indexed448Fp628Api.Calls)s::invoke;var e900=lower(s);Fc74Fp626Api.Calls other=unused->{throw new AssertionError("Unused629other");};
        rejectedNull(()->KnownFc74IndexedFp629.bind(null,s.budget,inner,e900,other));rejectedNull(()->KnownFc74IndexedFp629.bind(s.memory,null,inner,e900,other));rejectedNull(()->KnownFc74IndexedFp629.bind(s.memory,s.budget,null,e900,other));rejectedNull(()->KnownFc74IndexedFp629.bind(s.memory,s.budget,inner,null,other));rejectedNull(()->KnownFc74IndexedFp629.bind(s.memory,s.budget,inner,e900,null));s.done();
        var c=new GovernmentCrtBoundary185Api.Call(0x424FC83,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,T1,S+8,A,N);var frame=new Fc74Fp626Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S,A,N),true,P0);Stopped out=stopped(0x424FC83,frame.childEntry());int[] seen={0};var linked=KnownFc74IndexedFp629.bind(s.memory,s.budget,inner,e900,f->{check(f==frame);seen[0]++;return out;});check(linked.invoke(frame)==out&&seen[0]==1);s.done();
        Script bad=seeded();cachedPrefix(bad);addTail(bad,fastTail(),true,P0,tailNormal(NLOOK),List.of(new Mem(true,8,D,13)));try{execute(bad);throw new AssertionError("629badTailaccepted");}catch(IllegalArgumentException expected){bad.done();check(bad.tailcalls==1&&bad.load(D,8)==13);}
    }
    public static int verify(){cacheWhole();stoppedWhole();deepNormalTailStop();pureFactoryAndBadTail();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
