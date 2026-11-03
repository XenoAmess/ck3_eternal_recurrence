package org.xar.ck3.control.g2.m2.nativecode;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalTailTarget42421c8213.Memory16;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;

/** Four finite callee-carrier groups, not a new whole Indexed448 execution or hardware FP test. */
public final class WordCompareFpBoundary630 {
    private WordCompareFpBoundary630() { }
    private static final long I=0x140000000L,S=0x890000000000D000L,L=0x8900000000001003L,R=0x8900000000002005L,D=0x8900000000003007L;
    private static final Mxcsr UNKNOWN=Mxcsr.unknown(),PARTIAL=new Mxcsr(0x20,0x20);
    private static Bits128 x(int k){return new Bits128(0xA000000000000000L+k,0xB000000000000000L+k);}
    private static final NonvolatileBits N=new NonvolatileBits(0x11,0x33,0x44,0x22,0x55,0x66,0x77,0x88,x(6));
    private static VolatileBits v(long ax,long cx,long dx,long count){return new VolatileBits(ax,cx,dx,count,0x99,0xAA,0xBB,x(0),x(1),x(2),x(3),x(4),x(5));}
    private static void check(boolean value){if(!value)throw new AssertionError("630 source-literal contract mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Alias(int width,long address,long value) { }
    private static final class Script {
        final Map<Long,Byte> ram=new HashMap<>();final List<Object> events=new ArrayList<>();int cursor,words,qwords;
        int mutateAfterWord=-1,throwAfterWord=-1;List<Alias> aliases=List.of();
        final RuntimeException marker=new IllegalStateException("630 original Memory/callback exception");
        final Memory16 memory=(Memory16)Proxy.newProxyInstance(Memory16.class.getClassLoader(),new Class<?>[]{Memory16.class},(proxy,method,args)->{
            String name=method.getName();
            if(method.getDeclaringClass()==Object.class){if(name.equals("toString"))return "630 supplied Memory";if(name.equals("hashCode"))return Integer.valueOf(System.identityHashCode(proxy));if(name.equals("equals"))return Boolean.valueOf(proxy==args[0]);throw new AssertionError(name);}
            long address=((Long)args[0]).longValue();
            if(name.equals("writeQword")){long value=((Long)args[1]).longValue();event(new Mem(true,8,address,value));store(address,8,value);return null;}
            int width;if(name.equals("readUnsigned16"))width=2;else if(name.equals("readQword"))width=8;else throw new AssertionError("630 unexpected/widened Memory operation "+name);
            long value=load(address,width);event(new Mem(false,width,address,value));
            if(width==2){words++;if(words==mutateAfterWord){for(Alias alias:aliases){event(alias);store(alias.address(),alias.width(),alias.value());}}if(words==throwAfterWord)throw marker;return Integer.valueOf((int)value);}
            qwords++;return Long.valueOf(value);
        });
        void store(long address,int width,long value){for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long address,int width){long result=0;for(int k=0;k<width;k++){Byte item=ram.get(address+k);if(item==null)throw new AssertionError("630 unseeded RAM");result|=(item.byteValue()&255L)<<(8*k);}return result;}
        void event(Object actual){if(cursor>=events.size()||!events.get(cursor++).equals(actual))throw new AssertionError("630 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){events.add(new Mem(false,width,address,value));}
        void done(){check(cursor==events.size());}
    }
    private static Indexed448Fp628Api.CallFrame frame(long site,long count,boolean df,Mxcsr fp){var bits=v(0xA0,L,R,count);var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4246A60,S+8,bits,N);return new Indexed448Fp628Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,S,bits,N),df,fp);}
    private static Script seeded(long site){Script s=new Script();s.store(S,8,I+site+5);return s;}
    private static Normal invoke(Script s,Indexed448Fp628Api.CallFrame frame){return (Normal)WordCompareFp630.bind(s.memory,unused->{throw new AssertionError("630 unexpected foreign branch");}).invoke(frame);}
    private static void expectedNormal(Normal actual,Indexed448Fp628Api.CallFrame frame,VolatileBits expected){check(actual.postMxcsr()==frame.preMxcsr()&&actual.base().postDirectionFlagSet()==frame.directionFlagSet());check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(expected,frame.returnRipBits(),S+8,N)));}
    private static void zeroCount(){long site=0x424E514;Script s=seeded(site);s.read(8,S,I+site+5);var frame=frame(site,0,true,UNKNOWN);Normal result=invoke(s,frame);s.done();check(s.words==0&&s.qwords==1);expectedNormal(result,frame,v(0,L,R,0));}
    private static void oneCountNegative(){long site=0x424E52A;Script s=seeded(site);s.store(L,2,0x8000);s.store(R,2,0xFFFF);s.read(2,L,0x8000);s.read(2,R,0xFFFF);s.read(8,S,I+site+5);var frame=frame(site,1,false,PARTIAL);Normal result=invoke(s,frame);s.done();check(s.words==2&&s.qwords==1);expectedNormal(result,frame,v(0xFFFF8001L,0xFFFF,R,0));}
    private static void fullCountFreshAlias(){long site=0x424E514;Script s=seeded(site);s.store(L,2,2);s.store(R,2,3);s.mutateAfterWord=2;s.aliases=List.of(new Alias(2,L,0x1234),new Alias(2,R,0x2345));s.read(2,L,2);s.read(2,R,3);s.events.addAll(s.aliases);s.read(2,L,0x1234);s.read(2,R,0x2345);s.read(8,S,I+site+5);var frame=frame(site,0x100000001L,true,PARTIAL);Normal result=invoke(s,frame);s.done();check(s.words==4&&s.qwords==1);expectedNormal(result,frame,v(0xFFFFEEEFL,0x2345,R,0x100000000L));}
    private static Stopped stop(Indexed448Fp628Api.CallFrame frame){return new Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(frame.childEntry(),frame.original().callSiteRva(),frame.directionFlagSet(),frame.preMxcsr()),0,frame.original().callSiteRva());}
    private static Indexed448Fp628Api.CallFrame foreignFrame(long site){VolatileBits bits=v(0xA0,L,R,1);var c=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0xF123456789ABCDEFL,S+8,bits,N);return new Indexed448Fp628Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(I,S,bits,N),true,UNKNOWN);}
    private static void rejectsNull(Runnable action){try{action.run();throw new AssertionError("630 null accepted");}catch(NullPointerException expected){/* factory/foreign contract */}}
    private static void forwardingAndFailures(){
        Script empty=new Script();rejectsNull(()->WordCompareFp630.bind(null,frame->stop(frame)));rejectsNull(()->WordCompareFp630.bind(empty.memory,null));empty.done();
        for(long site:new long[]{0x424E4EB,0x424E4F9,0x424E53B,0x424E574,0x424E5A0}){Script s=new Script();var frame=foreignFrame(site);Stopped offered=stop(frame);int[] count={0};Outcome actual=WordCompareFp630.bind(s.memory,f->{check(f==frame);count[0]++;return offered;}).invoke(frame);check(actual==offered&&count[0]==1);s.done();}
        Script nil=new Script();var f=foreignFrame(0x424E4EB);int[] count={0};nil.events.add(new Mem(true,8,D,99));var nullable=WordCompareFp630.bind(nil.memory,frame->{check(frame==f);count[0]++;nil.memory.writeQword(D,99);return null;});rejectsNull(()->nullable.invoke(f));nil.done();check(count[0]==1&&nil.load(D,8)==99);
        Script thrown=seeded(0x424E52A);thrown.store(L,2,0x8000);thrown.store(R,2,0xFFFF);thrown.read(2,L,0x8000);thrown.read(2,R,0xFFFF);thrown.throwAfterWord=2;try{invoke(thrown,frame(0x424E52A,1,false,PARTIAL));throw new AssertionError("630 Memory exception lost");}catch(RuntimeException e){check(e==thrown.marker);thrown.done();check(thrown.words==2&&thrown.qwords==0);}
        Script bad=seeded(0x424E514);bad.store(L,2,0x8000);bad.store(R,2,0xFFFF);bad.mutateAfterWord=2;bad.aliases=List.of(new Alias(8,S,0xBAD));bad.read(2,L,0x8000);bad.read(2,R,0xFFFF);bad.events.addAll(bad.aliases);bad.read(8,S,0xBAD);try{invoke(bad,frame(0x424E514,1,true,UNKNOWN));throw new AssertionError("630 bad fresh RET accepted");}catch(IllegalArgumentException expected){bad.done();check(bad.words==2&&bad.qwords==1&&bad.load(S,8)==0xBAD);}
    }
    public static int verify(){zeroCount();oneCountNegative();fullCountFreshAlias();forwardingAndFailures();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
