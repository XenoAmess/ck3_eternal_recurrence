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

/** Two new whole-composition groups across actual70/470/44B; opaque IAT offers stay explicit. */
public final class Fc74IndexedWordFpBoundary631 {
    private Fc74IndexedWordFpBoundary631() { }
    private static final long I=0x140000000L,S=0x890000000000E000L,E=S-0x30L,FACT=I+0x4420C50,FIRST=I+0x4426F28,END=I+0x4426F30,
        TABLE=I+5*8+0x5C5D790,SLOT=I+2*8+0x5C5D6F0,PROVIDER=0x8900000000002000L,BLOCK=0x8900000000003000L,
        RESULT=0x8900000000004000L,ALT=0xF123456789ABCDEFL,D=0x8900000000005000L,T1=0xE123456789ABCDEFL,T2=0xD123456789ABCDEFL,
        GETERR=0xA123456789ABCDEFL,LIT1=I+0x44226A0,LIT2=I+0x4426EC8,IDX=0xF1234567L,TAIL=0xC123456789ABCDEFL;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=Mxcsr.unknown(),P3=new Mxcsr(8,8),P4=new Mxcsr(0x40,0x40),P5=new Mxcsr(0x20,0x20);
    private static final long[] SITES={0x424E4EB,0x424E4F9,0x424E514,0x424E52A,0x424E53B,0x424E574,0x424E5A0};
    private static final long[] RETS={0x424E4F1,0x424E4FF,0x424E519,0x424E52F,0x424E541,0x424E57A,0x424E5A6};
    private static Bits128 x(long b,int k){return new Bits128(b+k,0xD000000000000000L+b+k);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long b){return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,x(b,0),x(b,1),x(b,2),x(b,3),x(b,4),x(b,5));}
    private static NonvolatileBits nv(long bx,long bp,long si,long di,long r12,long r13,long r14,long r15){return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,x(0xA0,6));}
    private static final VolatileBits A=v(0xA0,0xFFFF0000F1234567L,0xA2,0xA8,0xA9,0xAA,0xAB,0xA0),BEFORE1=v(0,PROVIDER,0,0x800,END,0,0xAB,0xA0),
        FIRST_OUT=v(0,0xB1,0xB2,0xB8,0xB9,0xBA,0xBB,0xB0),ERROR_OUT=v(0x1234000000000057L,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),
        BEFORE_ALLOC=v(0xFFFFFFFFL,PROVIDER,0,0,0xC9,0xCA,0xCB,0xC0),THIRD_OUT=v(BLOCK,0xD1,0xD2,0xD8,0xD9,0xDA,0xDB,0xD0),
        BEFORE_RESOLVE=v(0,BLOCK,FACT,0xD8,0xD9,0,0xDB,0xD0),RESOLVE_OUT=v(RESULT,0xE1,0xE2,0xE8,0xE9,0xEA,0xEB,0xE0),
        FINAL=v(0xF0,0xF1,0xF2,0xF8,0xF9,0xFA,0xFB,0xF0);
    private static final NonvolatileBits N=nv(0x11,0x33,0x44,0x22,0x55,0x66,0x77,0x88),N1=nv(0,FIRST,2,-1,END,FACT,PROVIDER,5),N2=nv(BLOCK,FIRST,2,-1,END,FACT,I,5),N3=nv(7,FIRST,2,-1,END,FACT,PROVIDER,5);
    private static void check(boolean b){if(!b)throw new AssertionError("631 source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Alias(int width,long address,long value) { }
    private record Exchange(long address,long newBits,long oldBits) { }
    private record Budget(long header,long guard) { }
    private record Invoke(GovernmentCrtBoundary185Api.Call original,GovernmentCrtBoundary185Api.Entry child,boolean df,Mxcsr fp,long ret,Outcome out,List<Mem> effects,boolean throwing) { }
    private record TailEvent(GovernmentCrtBoundary185Api.Tail original,boolean df,Mxcsr fp,Outcome out,List<Mem> effects) { }
    private static final class Script {
        final List<Object> events=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls,exchanges,tailcalls,words;int throwAfterWord=-1,aliasAfterWord=-1;List<Alias> aliases=List.of();
        final Fc74Fp626Api.CallFrame caller=frame();
        final RuntimeException marker=new IllegalStateException("631 original callback or budget exception");boolean budgetThrows;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{event(new Budget(header,guard));if(budgetThrows)throw marker;};
        final KnownFc74IndexedWordFp631.Memory memory=(KnownFc74IndexedWordFp631.Memory)Proxy.newProxyInstance(KnownFc74IndexedWordFp631.Memory.class.getClassLoader(),new Class<?>[]{KnownFc74IndexedWordFp631.Memory.class},(proxy,method,args)->{
            String name=method.getName();long address=((Long)args[0]).longValue();
            if(name.equals("exchangeQword")){long value=((Long)args[1]).longValue(),old=load(address,8);event(new Exchange(address,value,old));exchanges++;store(address,8,value);return Long.valueOf(old);}
            int width;if(name.equals("readUnsigned16"))width=2;else if(name.equals("readQword")||name.equals("writeQword"))width=8;else if(name.equals("readDword")||name.equals("writeDword"))width=4;else throw new AssertionError("Unexpected631Memory "+name);
            boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,width);event(new Mem(write,width,address,width==4?value&0xFFFFFFFFL:value));
            if(write){store(address,width,value);return null;}if(width==2){words++;if(words==aliasAfterWord){for(Alias a:aliases){event(a);store(a.address(),a.width(),a.value());}}if(words==throwAfterWord)throw marker;return Integer.valueOf((int)value);}if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
        });
        void store(long a,int w,long v){for(int k=0;k<w;k++)ram.put(a+k,Byte.valueOf((byte)(v>>>(8*k))));}
        long load(long a,int w){long v=0;for(int k=0;k<w;k++){Byte z=ram.get(a+k);if(z==null)throw new AssertionError("Unseeded631RAM");v|=(z.byteValue()&255L)<<(8*k);}return v;}
        void event(Object actual){if(cursor>=events.size()||!events.get(cursor++).equals(actual))throw new AssertionError("631 cursor "+(cursor-1)+" actual="+actual);}
        void write(long a,long v){events.add(new Mem(true,8,a,v));}void read(int w,long a,long v){events.add(new Mem(false,w,a,w==4?v&0xFFFFFFFFL:v));}
        void add(int idx,VolatileBits before,NonvolatileBits n,boolean df,Mxcsr fp,Outcome out,List<Mem> effects,boolean throwing){long target=idx==2||idx==3?0x4246A60:idx==6?T2:idx==1?GETERR:T1;
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
        @Override public Outcome invoke(E900Fp627Api.CallFrame unused){throw new AssertionError("Unexpected631E900foreigninvoke");}
        @Override public Outcome tail(E900Fp627Api.TailFrame f){return s.tail(f);}};}
    private static Outcome execute(Script s){return KnownFc74IndexedWordFp631.bind(s.memory,s.budget,s::invoke,lower(s),unused->{throw new AssertionError("Unexpected631outerforeign");}).invoke(s.caller);}
    private static Script seeded(){Script s=new Script();s.store(TABLE,8,0);s.store(I+0x542F0B8,8,0);s.store(FIRST,4,2);s.store(SLOT,8,0);s.store(I+2*8+0x44269D0,8,PROVIDER);s.store(I+0x43DA478,8,T1);s.store(I+0x43DA680,8,T2);s.store(I+0x43DA738,8,GETERR);s.store(LIT1,2,2);s.store(LIT2,2,2);s.store(I+0x43DBBA8,8,TAIL);return s;}
    private static void prologue(Script s){s.write(S-8,0x11);s.write(E,I+0x424E927);s.write(E+8,IDX);s.write(E+0x10,0x33);s.write(E+0x18,0x44);s.write(E-8,0x22);s.write(E-0x10,0x55);s.write(E-0x18,0x66);s.write(E-0x20,0x77);s.write(E-0x28,0x88);}
    private static void restore(Script s){s.read(8,E+8,IDX);s.read(8,E+0x10,0x33);s.read(8,E+0x18,0x44);s.read(8,E-0x28,0x88);s.read(8,E-0x20,0x77);s.read(8,E-0x18,0x66);s.read(8,E-0x10,0x55);s.read(8,E-8,0x22);s.read(8,E,I+0x424E927);s.read(8,S-8,0x11);s.read(8,I+0x43DBBA8,TAIL);}
    private static void prefix(Script s){prologue(s);s.read(8,TABLE,0);s.read(8,I+0x542F0B8,0);s.events.add(new Budget(0x424E4BA,FIRST));s.read(4,FIRST,2);s.read(8,SLOT,0);s.read(8,I+2*8+0x44269D0,PROVIDER);s.read(8,I+0x43DA478,T1);s.write(E-0x50,I+0x424E4F1);}
    private static Normal offer(VolatileBits v,int idx,NonvolatileBits n,boolean df,Mxcsr fp){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,I+RETS[idx],E-0x48,n),df),fp);}
    private static Stopped stopped(long pc,GovernmentCrtBoundary185Api.Entry e){return new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(e,pc,false,P3),0,pc);}
    private static void addTail(Script s,VolatileBits v,boolean df,Mxcsr fp,Outcome out,List<Mem> effects){s.events.add(new TailEvent(new GovernmentCrtBoundary185Api.Tail(0x424E933,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,TAIL,new GovernmentCrtBoundary185Api.Entry(I,S,v,N)),df,fp,out,effects));s.events.addAll(effects);}
    private static void firstTwo(Script s){prefix(s);s.add(0,BEFORE1,N1,true,P0,offer(FIRST_OUT,0,N1,false,P1),List.of(new Mem(true,8,PROVIDER,1)),false);
        s.read(8,I+0x43DA738,GETERR);s.write(E-0x50,I+0x424E4FF);s.add(1,FIRST_OUT,N1,false,P1,offer(ERROR_OUT,1,N1,true,P2),List.of(),false);}
    private static void wordReads(Script s,long literal,long ret){s.write(E-0x50,I+ret);s.read(2,PROVIDER,1);s.read(2,literal,2);s.read(2,PROVIDER,1);s.read(2,literal,2);s.read(8,E-0x50,I+ret);}
    private static void completeKnownWords(){Script s=seeded();firstTwo(s);wordReads(s,LIT1,0x424E519);wordReads(s,LIT2,0x424E52F);
        s.read(8,I+0x43DA478,T1);s.write(E-0x50,I+0x424E541);s.add(4,BEFORE_ALLOC,N3,true,P2,offer(THIRD_OUT,4,N3,false,P3),List.of(),false);
        s.events.add(new Exchange(SLOT,BLOCK,0));s.read(8,I+0x542F0B8,0);s.read(8,I+0x43DA680,T2);s.write(E-0x50,I+0x424E5A6);
        s.add(6,BEFORE_RESOLVE,N2,false,P3,offer(RESOLVE_OUT,6,N2,true,P4),List.of(new Mem(true,8,TABLE,ALT)),false);
        s.read(8,I+0x542F0B8,0);s.events.add(new Exchange(TABLE,RESULT,ALT));restore(s);
        var before=v(RESULT,IDX,ALT,0,0xE9,0xEA,0xEB,0xE0);Normal offered=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(FINAL,I+0x424FC9B,S+8,N),false),P5);
        addTail(s,before,true,P4,offered,List.of(new Mem(true,8,D,17)));Normal actual=(Normal)execute(s);s.done();
        check(actual.base().normalReturn()==offered.base().normalReturn()&&actual.postMxcsr()==P5&&!actual.base().postDirectionFlagSet());
        check(s.calls==4&&s.words==8&&s.exchanges==2&&s.tailcalls==1&&s.load(TABLE,8)==RESULT&&s.load(SLOT,8)==BLOCK&&s.load(PROVIDER,8)==1&&s.load(D,8)==17&&s.load(E-0x50,8)==I+0x424E5A6);
        check(s.load(S-8,8)==0x11&&s.load(E,8)==I+0x424E927&&s.load(E+8,8)==IDX&&s.load(E+0x10,8)==0x33&&s.load(E+0x18,8)==0x44&&s.load(E-8,8)==0x22&&s.load(E-0x10,8)==0x55&&s.load(E-0x18,8)==0x66&&s.load(E-0x20,8)==0x77&&s.load(E-0x28,8)==0x88);
    }
    private static void failuresThroughUpper(){
        Script thrown=seeded();firstTwo(thrown);thrown.write(E-0x50,I+0x424E519);thrown.read(2,PROVIDER,1);thrown.read(2,LIT1,2);thrown.throwAfterWord=2;
        try{execute(thrown);throw new AssertionError("631 exception lost");}catch(RuntimeException e){check(e==thrown.marker);thrown.done();check(thrown.calls==2&&thrown.words==2&&thrown.exchanges==0&&thrown.tailcalls==0);}
        Script bad=seeded();firstTwo(bad);bad.write(E-0x50,I+0x424E519);bad.read(2,PROVIDER,1);bad.read(2,LIT1,2);bad.read(2,PROVIDER,1);bad.read(2,LIT1,2);
        bad.aliasAfterWord=4;bad.aliases=List.of(new Alias(8,E-0x50,0xBAD));bad.events.addAll(bad.aliases);bad.read(8,E-0x50,0xBAD);
        try{execute(bad);throw new AssertionError("631 bad fresh RET accepted");}catch(IllegalArgumentException expected){bad.done();check(bad.calls==2&&bad.words==4&&bad.exchanges==0&&bad.tailcalls==0&&bad.load(E-0x50,8)==0xBAD);}
    }
    public static int verify(){completeKnownWords();failuresThroughUpper();return 2;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
