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

/** Two new whole error32/fullFC74-entry groups; selected lower Indexed cache path, not upper positive WORD path. */
public final class AllocateIndexedFpBoundary632 {
    private AllocateIndexedFpBoundary632() { }
    private static final long I=0x140000000L,R=0x890000000000F000L,F=R-0x30L,S=F-0x30L,H=S-0x30L,
        ADDR=0x8900000000002003L,D=0x8900000000003000L,GETERR=0x12345678L,TGET=0xA123456789ABCDEFL,TSET=0xB123456789ABCDEFL,TAIL=0xC123456789ABCDEFL,
        FACT=I+0x4420C50,FIRST=I+0x4426F28,END=I+0x4426F30,TABLE=I+5*8+0x5C5D790;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x20,0x20),P2=Mxcsr.unknown(),P3=new Mxcsr(0x40,0x40);
    private static Bits128 x(long b,int k){return new Bits128(b+k,0xD000000000000000L+b+k);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long b){return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,x(b,0),x(b,1),x(b,2),x(b,3),x(b,4),x(b,5));}
    private static NonvolatileBits nv(long bx,long bp,long si,long di,long r12,long r13,long r14,long r15){return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,x(0xA0,6));}
    private static final VolatileBits A=v(0xA0,0xA1,0xA2,0xA8,0xA9,0xAA,0xAB,0xA0),B=v(0xFFFF000012345678L,0xB1,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0),
        FC_BEFORE=v(0xFFFF000012345678L,5,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0),TAIL_BEFORE=v(ADDR,5,ADDR,FIRST,END,0,0xBB,0xB0),
        TAIL_AFTER=v(ADDR,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),SET_BEFORE=v(ADDR,GETERR,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),SET_AFTER=v(0xD0,0xD1,0xD2,0xD8,0xD9,0xDA,0xDB,0xD0),
        FINAL=v(ADDR+0x20,0xD1,0xD2,0xD8,0xD9,0xDA,0xDB,0xD0);
    private static final NonvolatileBits N=nv(0x11,0x33,0x44,0x22,0x55,0x66,0x77,0x88),NFC=nv(GETERR,0x33,0x44,0x22,0x55,0x66,0x77,0x88),NSET=nv(GETERR,0x33,ADDR,ADDR,0x55,0x66,0x77,0x88);
    private static void check(boolean b){if(!b)throw new AssertionError("632 source-literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Foreign(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret,Outcome out,List<Mem> effects) { }
    private record TailEvent(GovernmentCrtBoundary185Api.Tail tail,boolean df,Mxcsr fp,Outcome out) { }
    private static final class Script {
        final Map<Long,Byte> ram=new HashMap<>();final List<Object> events=new ArrayList<>();int cursor,fcCalls,tails;
        final KnownAllocateIndexedFp632.Memory memory=(KnownAllocateIndexedFp632.Memory)Proxy.newProxyInstance(KnownAllocateIndexedFp632.Memory.class.getClassLoader(),new Class<?>[]{KnownAllocateIndexedFp632.Memory.class},(proxy,method,args)->{
            String name=method.getName();int width;if(name.equals("readQword")||name.equals("writeQword"))width=8;else if(name.equals("readDword")||name.equals("writeDword"))width=4;else throw new AssertionError("632 unexpected operation "+name);
            long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,width);
            event(new Mem(write,width,address,width==4?value&0xFFFFFFFFL:value));if(write){store(address,width,value);return null;}if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
        });
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{throw new AssertionError("632 unexpected loop budget on cache path");};
        void store(long a,int w,long v){for(int k=0;k<w;k++)ram.put(a+k,Byte.valueOf((byte)(v>>>(8*k))));}
        long load(long a,int w){long v=0;for(int k=0;k<w;k++){Byte z=ram.get(a+k);if(z==null)throw new AssertionError("632 unseeded RAM");v|=(z.byteValue()&255L)<<(8*k);}return v;}
        void event(Object actual){if(cursor>=events.size()||!events.get(cursor++).equals(actual))throw new AssertionError("632 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){events.add(new Mem(false,width,address,width==4?value&0xFFFFFFFFL:value));}
        void write(long address,long value){events.add(new Mem(true,8,address,value));}
        void done(){check(cursor==events.size());}
        Outcome fc(Fc74Fp626Api.CallFrame f){check(cursor<events.size()&&events.get(cursor) instanceof Foreign);Foreign e=(Foreign)events.get(cursor++);
            check(f.original().equals(e.call())&&f.childEntry().equals(e.child())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==e.ret());fcCalls++;
            for(Mem m:e.effects())memory.writeQword(m.address(),m.value());return e.out();}
        Outcome tail(E900Fp627Api.TailFrame f){check(cursor<events.size()&&events.get(cursor) instanceof TailEvent);TailEvent e=(TailEvent)events.get(cursor++);
            check(f.original().equals(e.tail())&&f.caller().equals(fcFrame())&&f.directionFlagSet()==e.df()&&f.preMxcsr()==e.fp()&&f.returnRipBits()==I+0x424FC9B);tails++;return e.out();}
    }
    private static KnownHeapAllocateFp623.AllocateCall outer(){var c=new GovernmentCrtBoundary185Api.Call(0x424FDEB,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x423B18C,R+8,A,N);return new KnownHeapAllocateFp623.AllocateCall(c,new GovernmentCrtBoundary185Api.Entry(I,R,A,N),true,P0);}
    private static Fc74Fp626Api.CallFrame fcFrame(){var c=new GovernmentCrtBoundary185Api.Call(0x424FC96,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E900,F-0x28,FC_BEFORE,NFC);return new Fc74Fp626Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S,FC_BEFORE,NFC),false,P1);}
    private static Outcome execute(Script s){E900Fp627Api.Calls e900=new E900Fp627Api.Calls(){
        @Override public Outcome invoke(E900Fp627Api.CallFrame unused){throw new AssertionError("632 unexpected E900 foreignCALL");}
        @Override public Outcome tail(E900Fp627Api.TailFrame f){return s.tail(f);}};
        return KnownAllocateIndexedFp632.bind(s.memory,s.budget,unused->{throw new AssertionError("632 unexpected Indexed foreignCALL");},e900,s::fc,unused->{throw new AssertionError("632 unexpected Error foreign");},unused->{throw new AssertionError("632 unexpected Allocate foreign");}).invoke(outer());}
    private static Normal normal(VolatileBits v,long ret,long sp,NonvolatileBits n,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,I+ret,sp,n),df),fp);}
    private static Script seeded(){Script s=new Script();s.store(R,8,I+0x424FDF0);s.store(I+0x43DA738,8,TGET);s.store(I+0x43DA420,8,TSET);s.store(I+0x542F328,4,5);s.store(TABLE,8,ADDR);s.store(I+0x542F0B8,8,0);s.store(I+0x43DBBA8,8,TAIL);return s;}
    private static void addFc(Script s,long site,long target,VolatileBits before,NonvolatileBits n,boolean df,Mxcsr fp,Outcome out,List<Mem> effects){var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,F-0x28,before,n);s.events.add(new Foreign(call,new GovernmentCrtBoundary185Api.Entry(I,F-0x30,before,n),df,fp,I+site+6,out,effects));s.events.addAll(effects);}
    private static void prefix(Script s){s.write(F,I+0x423B195);s.write(F+8,0x11);s.write(F+0x10,0x44);s.write(F-8,0x22);
        s.read(8,I+0x43DA738,TGET);s.write(F-0x30,I+0x424FC89);addFc(s,0x424FC83,TGET,A,N,true,P0,normal(B,0x424FC89,F-0x28,N,false,P1),List.of());
        s.read(4,I+0x542F328,5);s.write(S,I+0x424FC9B);s.write(S-8,GETERR);s.write(H,I+0x424E927);s.write(H+8,5);s.write(H+0x10,0x33);s.write(H+0x18,0x44);s.write(H-8,0x22);s.write(H-0x10,0x55);s.write(H-0x18,0x66);s.write(H-0x20,0x77);s.write(H-0x28,0x88);
        s.read(8,TABLE,ADDR);s.read(8,I+0x542F0B8,0);s.read(8,H+8,5);s.read(8,H+0x10,0x33);s.read(8,H+0x18,0x44);s.read(8,H-0x28,0x88);s.read(8,H-0x20,0x77);s.read(8,H-0x18,0x66);s.read(8,H-0x10,0x55);s.read(8,H-8,0x22);s.read(8,H,I+0x424E927);s.read(8,S-8,GETERR);s.read(8,I+0x43DBBA8,TAIL);}
    private static void addTail(Script s,Outcome out){s.events.add(new TailEvent(new GovernmentCrtBoundary185Api.Tail(0x424E933,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,TAIL,new GovernmentCrtBoundary185Api.Entry(I,S,TAIL_BEFORE,NFC)),false,P1,out));}
    private static void suffix(Script s,boolean alias){s.read(8,I+0x43DA420,TSET);s.write(F-0x30,I+0x424FD27);var effects=alias?List.of(new Mem(true,8,R,0xBAD)):List.<Mem>of();
        addFc(s,0x424FD21,TSET,SET_BEFORE,NSET,true,P2,normal(SET_AFTER,0x424FD27,F-0x28,NSET,false,P3),effects);
        s.read(8,F+8,0x11);s.read(8,F+0x10,0x44);s.read(8,F-8,0x22);s.read(8,F,I+0x423B195);s.read(8,R,alias?0xBAD:I+0x424FDF0);}
    private static void wholeNormal(){Script s=seeded();prefix(s);addTail(s,normal(TAIL_AFTER,0x424FC9B,F-0x28,NFC,true,P2));suffix(s,false);Normal actual=(Normal)execute(s);s.done();
        check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(FINAL,I+0x424FDF0,R+8,N))&&!actual.base().postDirectionFlagSet()&&actual.postMxcsr()==P3);check(s.fcCalls==2&&s.tails==1&&s.load(TABLE,8)==ADDR&&s.load(R,8)==I+0x424FDF0);}
    private static void wholeFailures(){Script stop=seeded();prefix(stop);Stopped out=new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,S,TAIL_BEFORE,NFC),0x424E933,false,P1),0,0x424E933);addTail(stop,out);check(execute(stop)==out);stop.done();check(stop.fcCalls==1&&stop.tails==1);
        Script bad=seeded();prefix(bad);addTail(bad,normal(TAIL_AFTER,0x424FC9B,F-0x28,NFC,true,P2));suffix(bad,true);try{execute(bad);throw new AssertionError("632 repaired bad outerRET");}catch(IllegalArgumentException expected){bad.done();check(bad.fcCalls==2&&bad.tails==1&&bad.load(R,8)==0xBAD);}}
    public static int verify(){wholeNormal();wholeFailures();return 2;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
