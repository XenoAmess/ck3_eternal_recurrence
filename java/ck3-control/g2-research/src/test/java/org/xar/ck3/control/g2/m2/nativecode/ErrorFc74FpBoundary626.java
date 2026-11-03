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

/** Four independent source-literal groups for the FC74 FP/DF carrier. */
public final class ErrorFc74FpBoundary626 {
    private ErrorFc74FpBoundary626() { }
    private static final long I=0x140000000L,S=0x8900000000009000L,PRE=S-0x28,
        ADDR=0x8900000000004000L,D=0x8900000000002000L,T1=0xF123456789ABCDEFL,T2=0xE123456789ABCDEFL,ERR=0x89ABCDEFL;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=new Mxcsr(0x40,0x40),P3=new Mxcsr(4,4);
    private static final long[] SITES={0x424FC83,0x424FC96,0x424FCB9,0x424FCCC,0x424FCE1,0x424FCE8,0x424FCF2,0x424FD03,0x424FD10,0x424FD17,0x424FD21};
    private static final long[] TARGETS={T1,0x424E900,0x424E948,0x424E2EC,0x424E948,0x424E364,0x424E948,0x424E948,0x424F8A8,0x424E364,T2};
    private static final long[] RETURNS={0x424FC89,0x424FC9B,0x424FCBE,0x424FCD1,0x424FCE6,0x424FCED,0x424FCF7,0x424FD08,0x424FD15,0x424FD1C,0x424FD27};
    private static Bits128 x(long b,int k){return new Bits128(b+k,0xD000000000000000L+b+k);}
    private static VolatileBits v(long ax,long cx,long b){return new VolatileBits(ax,cx,b+2,b+8,b+9,b+10,b+11,x(b,0),x(b,1),x(b,2),x(b,3),x(b,4),x(b,5));}
    private static final VolatileBits A=v(0xA0,0xA1,0xA0),B=v(0x1111111189ABCDEFL,0xB1,0xB0),C=v(ADDR,0xC1,0xC0),Z=v(0xF00,0xD1,0xD0);
    private static final NonvolatileBits N=n(0x11,0x22,0x44);
    private static NonvolatileBits n(long bx,long di,long si){return new NonvolatileBits(bx,0x33,si,di,0x55,0x66,0x77,0x88,x(0xA0,6));}
    private static void check(boolean b){if(!b)throw new AssertionError("626 source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Invoke(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret,Outcome outcome,List<Mem> effects,boolean throwing) { }
    private static final class Script {
        final List<Object> events=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls;
        final RuntimeException marker=new IllegalStateException("626 original callback exception");
        final GovernmentCrtBoundary185Api.Memory memory=(GovernmentCrtBoundary185Api.Memory)Proxy.newProxyInstance(GovernmentCrtBoundary185Api.Memory.class.getClassLoader(),
            new Class<?>[]{GovernmentCrtBoundary185Api.Memory.class},(proxy,method,args)->{
                String name=method.getName();int w;if(name.equals("readDword")||name.equals("writeDword"))w=4;
                else if(name.equals("readQword")||name.equals("writeQword"))w=8;else throw new AssertionError("Unexpected626Memory "+name);
                long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,w);
                event(new Mem(write,w,address,w==4?value&0xFFFFFFFFL:value));if(write){store(address,w,value);return null;}
                if(w==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long a,int w,long v){for(int k=0;k<w;k++)ram.put(a+k,Byte.valueOf((byte)(v>>>(8*k))));}
        long load(long a,int w){long v=0;for(int k=0;k<w;k++){Byte p=ram.get(a+k);if(p==null)throw new AssertionError("Unseeded626RAM");v|=(p.byteValue()&255L)<<(8*k);}return v;}
        void event(Object actual){if(cursor>=events.size()||!events.get(cursor++).equals(actual))throw new AssertionError("626 cursor "+(cursor-1)+" actual="+actual);}
        void write(long a,long v){events.add(new Mem(true,8,a,v));}
        void read(int w,long a,long v){events.add(new Mem(false,w,a,w==4?v&0xFFFFFFFFL:v));}
        void add(int idx,VolatileBits before,NonvolatileBits currentN,boolean df,Mxcsr fp,Outcome out,List<Mem> effects,boolean throwing){
            events.add(new Invoke(call(idx,before,currentN),new GovernmentCrtBoundary185Api.Entry(I,S-0x30,before,currentN),df,fp,I+RETURNS[idx],out,effects,throwing));events.addAll(effects);}
        Outcome invoke(Fc74Fp626Api.CallFrame f){check(cursor<events.size()&&events.get(cursor) instanceof Invoke);Invoke expected=(Invoke)events.get(cursor++);
            check(f.original().equals(expected.call())&&f.childEntry().equals(expected.child())&&f.directionFlagSet()==expected.df()&&f.preMxcsr()==expected.fp()&&f.returnRipBits()==expected.ret());calls++;
            for(Mem e:expected.effects()){if(e.width()==4)memory.writeDword(e.address(),(int)e.value());else memory.writeQword(e.address(),e.value());}
            if(expected.throwing())throw marker;return expected.outcome();}
        void done(){check(cursor==events.size());}
    }
    private static GovernmentCrtBoundary185Api.Call call(int idx,VolatileBits v,NonvolatileBits n){return new GovernmentCrtBoundary185Api.Call(SITES[idx],
        idx==0||idx==10?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,TARGETS[idx],PRE,v,n);}
    private static Normal normal(VolatileBits v,int idx,NonvolatileBits n,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(
        new GovernmentCrtBoundary185Api.NormalReturn(v,I+RETURNS[idx],PRE,n),df),fp);}
    private static Stopped stop(VolatileBits v,long site,Mxcsr fp){return new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
        new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,S-0x30,v,n(ERR,0x22,0x44)),site,false,fp),0,site);}
    private static KnownAllocateErrorFp625.ErrorCall outer(){var c=new GovernmentCrtBoundary185Api.Call(0x423B190,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424FC74,S+8,A,N);
        return new KnownAllocateErrorFp625.ErrorCall(c,new GovernmentCrtBoundary185Api.Entry(I,S,A,N),true,P0);}
    private static Outcome execute(Script s){return KnownErrorFc74Fp626.bind(s.memory,s::invoke,unused->{throw new AssertionError("Unexpected626foreign");}).invoke(outer());}
    private static Script seeded(){Script s=new Script();s.store(S,8,I+0x423B195);s.store(I+0x43DA738,8,T1);s.store(I+0x43DA420,8,T2);s.store(I+0x542F328,4,1);return s;}
    private static void first(Script s){s.write(S+8,0x11);s.write(S+0x10,0x44);s.write(S-8,0x22);s.read(8,I+0x43DA738,T1);s.write(S-0x30,I+0x424FC89);
        s.add(0,A,N,true,P0,normal(B,0,N,false,P1),List.of(),false);s.read(4,I+0x542F328,1);s.write(S-0x30,I+0x424FC9B);}
    private static void finish(Script s,List<Mem> effects){s.add(1,v(B.raxBits(),1,0xB0),n(ERR,0x22,0x44),false,P1,normal(C,1,n(ERR,0x22,0x44),true,P2),List.of(),false);
        s.read(8,I+0x43DA420,T2);s.write(S-0x30,I+0x424FD27);s.add(10,v(ADDR,ERR,0xC0),n(ERR,ADDR,ADDR),true,P2,normal(Z,10,n(ERR,ADDR,ADDR),false,P3),effects,false);}
    private static void epilogue(Script s,long bx,long ret){s.read(8,S+8,bx);s.read(8,S+0x10,0x44);s.read(8,S-8,0x22);s.read(8,S,ret);}
    private static void existingNormal(){Script s=seeded();first(s);finish(s,List.of(new Mem(true,4,D,7)));epilogue(s,0x11,I+0x423B195);
        Normal result=(Normal)execute(s);s.done();check(s.calls==3&&result.postMxcsr()==P3&&!result.base().postDirectionFlagSet()&&s.load(D,4)==7);
        check(result.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(v(ADDR,0xD1,0xD0),I+0x423B195,S+8,N)));}
    private static void stoppedPrefix(){Script s=seeded();first(s);Stopped expected=stop(v(B.raxBits(),1,0xB0),0x424FC96,P2);
        s.add(1,v(B.raxBits(),1,0xB0),n(ERR,0x22,0x44),false,P1,expected,List.of(new Mem(true,4,D,8)),false);
        check(execute(s)==expected);s.done();check(s.calls==2&&s.load(D,4)==8&&s.load(S-0x30,8)==I+0x424FC9B);}
    private static void rejected(Runnable r){try{r.run();throw new AssertionError("626 invalid accepted");}catch(IllegalArgumentException expected){/* source guard */}}
    private static void aliasAndFailure(){for(int mode=0;mode<2;mode++){Script s=seeded();first(s);long address=mode==0?S+8:S;
        finish(s,List.of(new Mem(true,8,address,0xBAD)));epilogue(s,mode==0?0xBAD:0x11,mode==0?I+0x423B195:0xBAD);rejected(()->execute(s));s.done();check(s.load(address,8)==0xBAD);}
        for(int mode=0;mode<3;mode++){Script s=seeded();s.write(S+8,0x11);s.write(S+0x10,0x44);s.write(S-8,0x22);s.read(8,I+0x43DA738,T1);s.write(S-0x30,I+0x424FC89);
            Normal bad=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(B,I+0x424FC89+(mode==0?1:0),PRE-(mode==1?8:0),mode==2?n(0xBAD,0x22,0x44):N),false),P1);
            s.add(0,A,N,true,P0,bad,List.of(new Mem(true,4,D,9)),false);rejected(()->execute(s));s.done();check(s.load(D,4)==9);}
        Script s=seeded();s.write(S+8,0x11);s.write(S+0x10,0x44);s.write(S-8,0x22);s.read(8,I+0x43DA738,T1);s.write(S-0x30,I+0x424FC89);
        s.add(0,A,N,true,P0,normal(B,0,N,false,P1),List.of(new Mem(true,4,D,10)),true);
        try{execute(s);throw new AssertionError("626 exception identity lost");}catch(RuntimeException actual){check(actual==s.marker);s.done();check(s.load(D,4)==10);}}
    private static void pureFrames(){for(int i=0;i<SITES.length;i++){var c=call(i,A,n(ERR,ADDR,ADDR));var e=new GovernmentCrtBoundary185Api.Entry(I,S-0x30,A,c.nonvolatileBits());
        var frame=new Fc74Fp626Api.CallFrame(c,e,true,P0);check(frame.original()==c&&frame.childEntry()==e&&frame.preMxcsr()==P0&&frame.returnRipBits()==I+RETURNS[i]);frame.checkNormalReturn(normal(B,i,c.nonvolatileBits(),false,P0).base());
        final int j=i;rejected(()->new Fc74Fp626Api.CallFrame(new GovernmentCrtBoundary185Api.Call(SITES[j]+0x100000000L,c.kind(),c.targetBits(),PRE,A,c.nonvolatileBits()),e,true,P0));
        rejected(()->new Fc74Fp626Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S-0x28,A,c.nonvolatileBits()),true,P0));
        rejected(()->new Fc74Fp626Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S-0x30,B,c.nonvolatileBits()),true,P0));
        rejected(()->new Fc74Fp626Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S-0x30,A,N),true,P0));
        rejected(()->frame.checkNormalReturn(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(B,I+RETURNS[j]+1,PRE,c.nonvolatileBits()),false)));
        if(i!=0&&i!=10)rejected(()->new Fc74Fp626Api.CallFrame(new GovernmentCrtBoundary185Api.Call(SITES[j],c.kind(),TARGETS[j]+1,PRE,A,c.nonvolatileBits()),e,true,P0));
    }
        try{new Fc74Fp626Api.CallFrame(null,new GovernmentCrtBoundary185Api.Entry(I,S-0x30,A,N),true,P0);throw new AssertionError("626null");}catch(NullPointerException expected){/* pure */}
    }
    public static int verify(){existingNormal();stoppedPrefix();aliasAndFailure();pureFrames();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
