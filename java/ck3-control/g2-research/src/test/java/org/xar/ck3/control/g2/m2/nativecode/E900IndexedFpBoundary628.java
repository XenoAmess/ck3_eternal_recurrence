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

/** Four source-literal groups: cache, stopped prefix, two Normal calls with exchanges, guards. */
public final class E900IndexedFpBoundary628 {
    private E900IndexedFpBoundary628() { }
    private static final long I=0x140000000L,S=0x890000000000B000L,FACT=I+0x4420C50,FIRST=I+0x4426F28,END=I+0x4426F30,
        TABLE=I+5*8+0x5C5D790,SLOT=I+2*8+0x5C5D6F0,PROVIDER=0x8900000000002000L,BLOCK=0x8900000000003000L,
        RESULT=0x8900000000004000L,ALT=0xF123456789ABCDEFL,D=0x8900000000005000L,T1=0xE123456789ABCDEFL,T2=0xD123456789ABCDEFL,ADDR=0x89000000000030F3L;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=new Mxcsr(0x40,0x40);
    private static final long[] SITES={0x424E4EB,0x424E4F9,0x424E514,0x424E52A,0x424E53B,0x424E574,0x424E5A0};
    private static final long[] RETS={0x424E4F1,0x424E4FF,0x424E519,0x424E52F,0x424E541,0x424E57A,0x424E5A6};
    private static Bits128 x(long b,int k){return new Bits128(b+k,0xD000000000000000L+b+k);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long b){return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,x(b,0),x(b,1),x(b,2),x(b,3),x(b,4),x(b,5));}
    private static NonvolatileBits nv(long bx,long bp,long si,long di,long r12,long r13,long r14,long r15){return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,x(0xA0,6));}
    private static final VolatileBits A=v(0xA0,5,FACT,FIRST,END,0xAA,0xAB,0xA0),BEFORE1=v(0,PROVIDER,0,0x800,END,0,0xAB,0xA0),B=v(BLOCK,0xB1,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0),
        BEFORE2=v(0,BLOCK,FACT,0xB8,0xB9,0,0xBB,0xB0),C=v(RESULT,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0);
    private static final NonvolatileBits N=nv(1,0x33,0x44,0x22,0x55,0x66,0x77,0x88),N1=nv(0,FIRST,2,-1,END,FACT,PROVIDER,5),N2=nv(BLOCK,FIRST,2,-1,END,FACT,I,5);
    private static void check(boolean b){if(!b)throw new AssertionError("628 source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Exchange(long address,long newBits,long oldBits) { }
    private record Budget(long header,long guard) { }
    private record Invoke(GovernmentCrtBoundary185Api.Call original,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret,Outcome out,List<Mem> effects,boolean throwing) { }
    private static final class Script {
        final List<Object> events=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls,exchanges;
        final RuntimeException marker=new IllegalStateException("628 original callback or budget exception");boolean budgetThrows;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{event(new Budget(header,guard));if(budgetThrows)throw marker;};
        final AtomicIndexedMemory229 memory=(AtomicIndexedMemory229)Proxy.newProxyInstance(AtomicIndexedMemory229.class.getClassLoader(),new Class<?>[]{AtomicIndexedMemory229.class},(proxy,method,args)->{
            String name=method.getName();long address=((Long)args[0]).longValue();
            if(name.equals("exchangeQword")){long value=((Long)args[1]).longValue(),old=load(address,8);event(new Exchange(address,value,old));exchanges++;store(address,8,value);return Long.valueOf(old);}
            int width;if(name.equals("readQword")||name.equals("writeQword"))width=8;else if(name.equals("readDword")||name.equals("writeDword"))width=4;else throw new AssertionError("Unexpected628Memory "+name);
            boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,width);event(new Mem(write,width,address,width==4?value&0xFFFFFFFFL:value));
            if(write){store(address,width,value);return null;}if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
        });
        void store(long a,int w,long v){for(int k=0;k<w;k++)ram.put(a+k,Byte.valueOf((byte)(v>>>(8*k))));}
        long load(long a,int w){long v=0;for(int k=0;k<w;k++){Byte z=ram.get(a+k);if(z==null)throw new AssertionError("Unseeded628RAM");v|=(z.byteValue()&255L)<<(8*k);}return v;}
        void event(Object actual){if(cursor>=events.size()||!events.get(cursor++).equals(actual))throw new AssertionError("628 cursor "+(cursor-1)+" actual="+actual);}
        void write(long a,long v){events.add(new Mem(true,8,a,v));}void read(int w,long a,long v){events.add(new Mem(false,w,a,w==4?v&0xFFFFFFFFL:v));}
        void add(int idx,VolatileBits before,NonvolatileBits n,boolean df,Mxcsr fp,Outcome out,List<Mem> effects,boolean throwing){long target=idx==2||idx==3?0x4246A60:idx==6?T2:T1;
            var call=new GovernmentCrtBoundary185Api.Call(SITES[idx],idx==2||idx==3?GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA:GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,S-0x48,before,n);
            events.add(new Invoke(call,new GovernmentCrtBoundary185Api.Entry(I,S-0x50,before,n),df,fp,I+RETS[idx],out,effects,throwing));events.addAll(effects);}
        Outcome invoke(Indexed448Fp628Api.CallFrame f){check(cursor<events.size()&&events.get(cursor) instanceof Invoke);Invoke e=(Invoke)events.get(cursor++);
            check(f.original().equals(e.original())&&f.childEntry().equals(e.child())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==e.ret());calls++;
            for(Mem effect:e.effects()){if(effect.width()==4)memory.writeDword(effect.address(),(int)effect.value());else memory.writeQword(effect.address(),effect.value());}
            if(e.throwing())throw marker;return e.out();}
        void done(){check(cursor==events.size());}
    }
    private static E900Fp627Api.CallFrame frame(){var c=new GovernmentCrtBoundary185Api.Call(0x424E922,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E448,S+8,A,N);
        return new E900Fp627Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S,A,N),true,P0);}
    private static Outcome execute(Script s){return KnownE900IndexedFp628.bind(s.memory,s.budget,s::invoke,new E900Fp627Api.Calls(){
        @Override public Outcome invoke(E900Fp627Api.CallFrame unused){throw new AssertionError("Unexpected628invoke");}
        @Override public Outcome tail(E900Fp627Api.TailFrame unused){throw new AssertionError("Unexpected628tail");}
    }).invoke(frame());}
    private static Script seeded(){Script s=new Script();s.store(S,8,I+0x424E927);s.store(TABLE,8,0);s.store(I+0x542F0B8,8,0);s.store(FIRST,4,2);s.store(SLOT,8,0);s.store(I+2*8+0x44269D0,8,PROVIDER);s.store(I+0x43DA478,8,T1);s.store(I+0x43DA680,8,T2);return s;}
    private static void prologue(Script s){s.write(S+8,1);s.write(S+0x10,0x33);s.write(S+0x18,0x44);s.write(S-8,0x22);s.write(S-0x10,0x55);s.write(S-0x18,0x66);s.write(S-0x20,0x77);s.write(S-0x28,0x88);}
    private static void restore(Script s,long bx){s.read(8,S+8,bx);s.read(8,S+0x10,0x33);s.read(8,S+0x18,0x44);s.read(8,S-0x28,0x88);s.read(8,S-0x20,0x77);s.read(8,S-0x18,0x66);s.read(8,S-0x10,0x55);s.read(8,S-8,0x22);s.read(8,S,I+0x424E927);}
    private static void prefix(Script s){prologue(s);s.read(8,TABLE,0);s.read(8,I+0x542F0B8,0);s.events.add(new Budget(0x424E4BA,FIRST));s.read(4,FIRST,2);s.read(8,SLOT,0);s.read(8,I+2*8+0x44269D0,PROVIDER);s.read(8,I+0x43DA478,T1);s.write(S-0x50,I+0x424E4F1);}
    private static Normal offer(VolatileBits v,int idx,NonvolatileBits n,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,I+RETS[idx],S-0x48,n),df),fp);}
    private static Stopped stopped(){return new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,S-0x50,BEFORE1,N1),0x424E4EB,false,P1),0,0x424E4EB);}
    private static void fastCache(){Script s=seeded();s.store(TABLE,8,ADDR);prologue(s);s.read(8,TABLE,ADDR);s.read(8,I+0x542F0B8,0);restore(s,1);Normal actual=(Normal)execute(s);s.done();
        check(s.calls==0&&s.exchanges==0&&actual.postMxcsr()==P0&&actual.base().postDirectionFlagSet());check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(v(ADDR,ADDR&~255L,ADDR,FIRST,END,0,0xAB,0xA0),I+0x424E927,S+8,N)));}
    private static void stoppedPrefix(){Script s=seeded();prefix(s);Stopped offer=stopped();s.add(0,BEFORE1,N1,true,P0,offer,List.of(new Mem(true,8,D,8)),false);check(execute(s)==offer);s.done();check(s.calls==1&&s.exchanges==0&&s.load(D,8)==8&&s.load(S-0x50,8)==I+0x424E4F1);}
    private static void normalTrace(Script s,boolean alias){prefix(s);s.add(0,BEFORE1,N1,true,P0,offer(B,0,N1,false,P1),List.of(new Mem(true,8,D,9)),false);s.events.add(new Exchange(SLOT,BLOCK,0));s.read(8,I+0x542F0B8,0);s.read(8,I+0x43DA680,T2);s.write(S-0x50,I+0x424E5A6);
        var effects=new ArrayList<Mem>();effects.add(new Mem(true,8,TABLE,ALT));if(alias)effects.add(new Mem(true,8,S+8,0xBAD));s.add(6,BEFORE2,N2,false,P1,offer(C,6,N2,true,P2),effects,false);s.read(8,I+0x542F0B8,0);s.events.add(new Exchange(TABLE,RESULT,ALT));restore(s,alias?0xBAD:1);}
    private static void normalExchange(){Script s=seeded();normalTrace(s,false);Normal actual=(Normal)execute(s);s.done();check(s.calls==2&&s.exchanges==2&&s.load(SLOT,8)==BLOCK&&s.load(TABLE,8)==RESULT&&actual.postMxcsr()==P2&&actual.base().postDirectionFlagSet());
        check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(v(RESULT,0x40,ALT,0,0xC9,0xCA,0xCB,0xC0),I+0x424E927,S+8,N)));}
    private static void rejected(Runnable r){try{r.run();throw new AssertionError("628invalidaccepted");}catch(IllegalArgumentException expected){/* source guard */}}
    private static void pureAndFailures(){for(int k=0;k<SITES.length;k++){long target=k==2||k==3?0x4246A60:T1;var kind=k==2||k==3?GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA:GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE;
        var call=new GovernmentCrtBoundary185Api.Call(SITES[k],kind,target,S-0x48,BEFORE1,N1);var e=new GovernmentCrtBoundary185Api.Entry(I,S-0x50,BEFORE1,N1);var f=new Indexed448Fp628Api.CallFrame(call,e,true,P0);check(f.returnRipBits()==I+RETS[k]);f.checkNormalReturn(offer(B,k,N1,false,P1).base());
        final int j=k;rejected(()->new Indexed448Fp628Api.CallFrame(new GovernmentCrtBoundary185Api.Call(SITES[j]+0x100000000L,kind,target,S-0x48,BEFORE1,N1),e,true,P0));
        rejected(()->new Indexed448Fp628Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,S-0x48,BEFORE1,N1),true,P0));
        rejected(()->f.checkNormalReturn(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(B,I+RETS[j],S-0x48,N),false)));}
        Script alias=seeded();normalTrace(alias,true);rejected(()->execute(alias));alias.done();check(alias.load(S+8,8)==0xBAD&&alias.load(TABLE,8)==RESULT);
        for(int k=0;k<3;k++){Script s=seeded();prefix(s);var bad=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(B,I+0x424E4F1+(k==0?1:0),S-0x48-(k==1?8:0),k==2?N:N1),false),P1);s.add(0,BEFORE1,N1,true,P0,bad,List.of(new Mem(true,8,D,10)),false);rejected(()->execute(s));s.done();check(s.exchanges==0&&s.load(D,8)==10);}
        Script foreign=seeded();prefix(foreign);foreign.add(0,BEFORE1,N1,true,P0,offer(B,0,N1,false,P1),List.of(new Mem(true,8,D,11)),true);try{execute(foreign);throw new AssertionError("628exceptionlost");}catch(RuntimeException e){check(e==foreign.marker);foreign.done();check(foreign.load(D,8)==11);}
        Script budget=seeded();prologue(budget);budget.read(8,TABLE,0);budget.read(8,I+0x542F0B8,0);budget.events.add(new Budget(0x424E4BA,FIRST));budget.budgetThrows=true;try{execute(budget);throw new AssertionError("628budgetexceptionlost");}catch(RuntimeException e){check(e==budget.marker);budget.done();check(budget.calls==0&&budget.exchanges==0);}
    }
    public static int verify(){fastCache();stoppedPrefix();normalExchange();pureAndFailures();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
