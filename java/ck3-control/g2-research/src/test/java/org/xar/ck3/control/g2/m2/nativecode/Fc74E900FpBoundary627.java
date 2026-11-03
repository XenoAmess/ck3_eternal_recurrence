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

/** Four source-literal groups for the actual E900 call and tail FP/DF carrier. */
public final class Fc74E900FpBoundary627 {
    private Fc74E900FpBoundary627() { }
    private static final long I=0x140000000L,S=0x890000000000A000L,IDX=0xF1234567L,D=0x8900000000002000L,
        T1=0xF123456789ABCDEFL,T2=0xE123456789ABCDEFL;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=new Mxcsr(0x40,0x40);
    private static Bits128 x(long b,int k){return new Bits128(b+k,0xD000000000000000L+b+k);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long b){return new VolatileBits(ax,cx,dx,r8,r9,b+10,b+11,x(b,0),x(b,1),x(b,2),x(b,3),x(b,4),x(b,5));}
    private static VolatileBits bank(long b,long ax,long cx){return v(ax,cx,b+2,b+8,b+9,b);}
    private static final VolatileBits A=bank(0xA0,0xA0,0xFFFF0000F1234567L),C=bank(0xC0,0xC0,0xC1);
    private static NonvolatileBits n(long bx){return new NonvolatileBits(bx,0x33,0x44,0x22,0x55,0x66,0x77,0x88,x(0xA0,6));}
    private static final NonvolatileBits N=n(0x11);
    private static void check(boolean b){if(!b)throw new AssertionError("627 source literal mismatch");}
    private record Mem(boolean write,long address,long value) { }
    private record Invoke(GovernmentCrtBoundary185Api.Call original,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,Outcome outcome,List<Mem> effects,boolean throwing) { }
    private record Tail(GovernmentCrtBoundary185Api.Tail original,boolean df,Mxcsr fp,Outcome outcome,List<Mem> effects,boolean throwing) { }
    private static final class Script {
        final List<Object> events=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls,tails;
        final Fc74Fp626Api.CallFrame caller=outer();final RuntimeException marker=new IllegalStateException("627 original callback exception");
        final GovernmentCrtBoundary185Api.Memory memory=(GovernmentCrtBoundary185Api.Memory)Proxy.newProxyInstance(GovernmentCrtBoundary185Api.Memory.class.getClassLoader(),new Class<?>[]{GovernmentCrtBoundary185Api.Memory.class},(proxy,method,args)->{
            String name=method.getName();if(!name.equals("readQword")&&!name.equals("writeQword"))throw new AssertionError("Unexpected627Memory "+name);
            long address=((Long)args[0]).longValue();boolean write=name.equals("writeQword");long value=write?((Long)args[1]).longValue():load(address);event(new Mem(write,address,value));if(write){store(address,value);return null;}return Long.valueOf(value);
        });
        final E900Fp627Api.Calls inner=new E900Fp627Api.Calls(){
            @Override public Outcome invoke(E900Fp627Api.CallFrame f){check(cursor<events.size()&&events.get(cursor) instanceof Invoke);Invoke e=(Invoke)events.get(cursor++);
                check(f.original().equals(e.original())&&f.childEntry().equals(e.child())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==I+0x424E927);calls++;
                for(Mem effect:e.effects())effect(effect);if(e.throwing())throw marker;return e.outcome();}
            @Override public Outcome tail(E900Fp627Api.TailFrame f){check(cursor<events.size()&&events.get(cursor) instanceof Tail);Tail e=(Tail)events.get(cursor++);
                check(f.original().equals(e.original())&&f.caller()==caller&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==I+0x424FC9B);tails++;
                for(Mem effect:e.effects())effect(effect);if(e.throwing())throw marker;return e.outcome();}
        };
        void store(long a,long v){for(int k=0;k<8;k++)ram.put(a+k,Byte.valueOf((byte)(v>>>(8*k))));}
        long load(long a){long v=0;for(int k=0;k<8;k++){Byte b=ram.get(a+k);if(b==null)throw new AssertionError("Unseeded627RAM");v|=(b.byteValue()&255L)<<(8*k);}return v;}
        void event(Object actual){if(cursor>=events.size()||!events.get(cursor++).equals(actual))throw new AssertionError("627 cursor "+(cursor-1)+" actual="+actual);}
        void write(long a,long v){events.add(new Mem(true,a,v));}void read(long a,long v){events.add(new Mem(false,a,v));}
        void effect(Mem m){check(m.write());memory.writeQword(m.address(),m.value());}
        void done(){check(cursor==events.size());}
    }
    private static Fc74Fp626Api.CallFrame outer(){var c=new GovernmentCrtBoundary185Api.Call(0x424FC96,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E900,S+8,A,N);
        return new Fc74Fp626Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S,A,N),true,P0);}
    private static VolatileBits callV(){return v(0xA0,5,I+0x4420C50,I+0x4426F28,I+0x4426F30,0xA0);}
    private static GovernmentCrtBoundary185Api.Call lower(){return new GovernmentCrtBoundary185Api.Call(0x424E922,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E448,S-0x28,callV(),n(IDX));}
    private static GovernmentCrtBoundary185Api.Entry child(){return new GovernmentCrtBoundary185Api.Entry(I,S-0x30,callV(),n(IDX));}
    private static Normal callNormal(long ax){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(bank(0xB0,ax,0xB1),I+0x424E927,S-0x28,n(IDX)),false),P1);}
    private static Normal tailNormal(NonvolatileBits n,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(C,I+0x424FC9B,S+8,n),df),fp);}
    private static Stopped stopped(){return new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,S,C,N),0x424E93F,false,P2),0,0x424E93F);}
    private static Script seeded(){Script s=new Script();s.store(I+0x43DBBA8,T1);s.store(I+0x43DA460,T2);return s;}
    private static void prefix(Script s){s.write(S-8,0x11);s.write(S-0x30,I+0x424E927);}
    private static void offerCall(Script s,Outcome out,List<Mem> effects,boolean throwing){s.events.add(new Invoke(lower(),child(),true,P0,out,effects,throwing));s.events.addAll(effects);}
    private static void offerTail(Script s,boolean nonzero,long bx,Outcome out,List<Mem> effects,boolean throwing){long ax=nonzero?0x100000000L:0;
        var e=new GovernmentCrtBoundary185Api.Entry(I,S,bank(0xB0,ax,IDX),n(bx));var t=new GovernmentCrtBoundary185Api.Tail(nonzero?0x424E933:0x424E93F,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,nonzero?T1:T2,e);
        s.events.add(new Tail(t,false,P1,out,effects,throwing));s.events.addAll(effects);}
    private static Outcome execute(Script s){return KnownFc74E900Fp627.bind(s.memory,s.inner,unused->{throw new AssertionError("Unexpected627foreign");}).invoke(s.caller);}
    private static void fullRaxNormalTail(){Script s=seeded();prefix(s);offerCall(s,callNormal(0x100000000L),List.of(),false);s.read(S-8,0x11);s.read(I+0x43DBBA8,T1);Normal offer=tailNormal(N,true,P0);
        offerTail(s,true,0x11,offer,List.of(new Mem(true,D,7)),false);Normal actual=(Normal)execute(s);s.done();check(s.calls==1&&s.tails==1&&actual.base().normalReturn()==offer.base().normalReturn()&&actual.postMxcsr()==P0&&actual.base().postDirectionFlagSet()&&s.load(D)==7);}
    private static void zeroTailStopped(){Script s=seeded();prefix(s);offerCall(s,callNormal(0),List.of(),false);s.read(S-8,0x11);s.read(I+0x43DA460,T2);Stopped offer=stopped();offerTail(s,false,0x11,offer,List.of(new Mem(true,D,8)),false);
        check(execute(s)==offer);s.done();check(s.calls==1&&s.tails==1&&s.load(D)==8);}
    private static void rejected(Runnable r){try{r.run();throw new AssertionError("627invalidaccepted");}catch(IllegalArgumentException expected){/* source guard */}}
    private static void stoppedAliasFailures(){Script s=seeded();prefix(s);Stopped offer=stopped();offerCall(s,offer,List.of(new Mem(true,D,9)),false);check(execute(s)==offer);s.done();check(s.tails==0&&s.load(D)==9);
        Script alias=seeded();prefix(alias);offerCall(alias,callNormal(0x100000000L),List.of(new Mem(true,S-8,0xBAD)),false);alias.read(S-8,0xBAD);alias.read(I+0x43DBBA8,T1);
        offerTail(alias,true,0xBAD,tailNormal(n(0xBAD),true,P2),List.of(new Mem(true,D,10)),false);rejected(()->execute(alias));alias.done();check(alias.tails==1&&alias.load(D)==10);
        for(int mode=0;mode<3;mode++){Script a=seeded();prefix(a);Normal bad=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(C,I+0x424E927+(mode==0?1:0),S-0x28-(mode==1?8:0),mode==2?N:n(IDX)),false),P1);offerCall(a,bad,List.of(),false);rejected(()->execute(a));a.done();}
        Script foreign=seeded();prefix(foreign);offerCall(foreign,callNormal(0),List.of(new Mem(true,D,11)),true);try{execute(foreign);throw new AssertionError("627foreignlost");}catch(RuntimeException a){check(a==foreign.marker);foreign.done();check(foreign.load(D)==11);}}
    private static void pureAndForeign(){var c=lower();var e=child();var frame=new E900Fp627Api.CallFrame(c,e,true,P0);check(frame.returnRipBits()==I+0x424E927);frame.checkNormalReturn(callNormal(0).base());
        rejected(()->new E900Fp627Api.CallFrame(new GovernmentCrtBoundary185Api.Call(0x1424E922L,c.kind(),c.targetBits(),c.rspBits(),c.volatileBits(),c.nonvolatileBits()),e,true,P0));
        rejected(()->new E900Fp627Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S-0x28,callV(),n(IDX)),true,P0));
        for(long site:new long[]{0x424E933L,0x424E93FL}){var t=new GovernmentCrtBoundary185Api.Tail(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,T1,new GovernmentCrtBoundary185Api.Entry(I,S,C,n(0xBAD)));
            var f=new E900Fp627Api.TailFrame(t,outer(),false,P1);check(f.original()==t&&f.returnRipBits()==I+0x424FC9B);f.checkNormalReturn(tailNormal(n(0xBAD),true,P2).base());
            rejected(()->new E900Fp627Api.TailFrame(new GovernmentCrtBoundary185Api.Tail(site,c.kind(),T1,t.entry()),outer(),false,P1));
            rejected(()->new E900Fp627Api.TailFrame(new GovernmentCrtBoundary185Api.Tail(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,T1,new GovernmentCrtBoundary185Api.Entry(I,S-8,C,n(0xBAD))),outer(),false,P1));}
        Script s=seeded();var other=new Fc74Fp626Api.CallFrame(new GovernmentCrtBoundary185Api.Call(0x424FC83,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,T2,S+8,A,N),new GovernmentCrtBoundary185Api.Entry(I,S,A,N),true,P0);Stopped result=stopped();
        Outcome actual=KnownFc74E900Fp627.bind(s.memory,s.inner,f->{check(f==other);return result;}).invoke(other);check(actual==result&&s.calls==0&&s.tails==0);s.done();}
    public static int verify(){fullRaxNormalTail();zeroTailStopped();stoppedAliasFailures();pureAndForeign();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
