package org.xar.ck3.research.m0.lifecycle286;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m0.lifecycle284.DeletingWrappers284;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New binding scenes only. Strict owned bytes; no Game, native allocator or hardware-race claim. */
public final class DeletingWrapperFreeWitness {
    private static final long I=0x140000000L,SP=0x730008L,RET=0x123456789ABCDEF0L;
    private static final long BLOCK=0xB00000L,HEAP=0xA00000L,TARGET=0x1111222233334444L;
    private static final long GS=0x810000L,TLS=0x920000L,STATIC=I+0x5D1EAF0L;
    private static final NonvolatileBits N=new NonvolatileBits(0x101L,0x202L,0x303L,0x404L,
            0xFEDCBA9876543210L,0x606L,0x707L,0x808L,new Bits128(0x919L,0xA2AL));
    private static int checks;
    private DeletingWrapperFreeWitness() { }
    public static void main(String[] args) {
        exactNullEntriesUseFreshHome();
        actualPlayerWrapper();
        actualManagerOptIn();
        residualIdentity();
        preAndPostBoundaries();
        System.out.println("PASS cases=5 checks="+checks+" represented185_only=true Game=false");
    }
    private static void exactNullEntriesUseFreshHome() {
        for(long site:new long[]{0x23DA6A1L,0x28EE5F1L}) {
            Mem m=new Mem();long pre=SP-8L,child=pre-8L,expected=I+site+5L;
            m.seedQ(child,expected);m.scriptDwordAddress=child+0x10L;m.scriptDwordValue=0xF1234567;
            Ports p=new Ports();VolatileBits input=with(v(0x100L),0xDEADL,0L,0xFFFFL);
            Call call=new Call(site,TargetKind.DIRECT_RVA,0x4223F44L,pre,input,N);
            VolatileBits got=DeletingWrapperFreeCalls.bind(I,m,p).invoke(call);
            equal(with(input,0xF1234567L,0L,0xFFFFL),got,"fresh unsigned EAX with all other V intact");
            equal(List.of("Q:"+hex(child),"WD:"+hex(child+0x10L),"D:"+hex(child+0x10L),"Q:"+hex(child)),
                    m.trace,"only original RET check, actual home write/read and actual RET; no push");
            number(expected,m.peekQ(child),"existing actual continuation intact");
            number(0,m.peekD(child+0x10L),"actual home DWORD write is zero before scripted fresh read");
            number(0,p.calls.size(),"null block has no imported call");
            number(0,p.gsReads,"null block has no GS read");
        }
    }
    private static void actualPlayerWrapper() {
        Mem m=heapMemory();m.seedQ(SP,RET);VolatileBits after=v(0x900L);
        Ports p=new Ports(){
            @Override public VolatileBits invoke(Call call) {
                calls.add(call);
                if(call.callSiteRva()==0x23DA68FL) {
                    number(0x23D9E40L,call.targetBits(),"actual opaque player destructor");
                    number(SP-0x28L,call.rspBits(),"wrapper destructor preSP");
                    number(I+0x23DA694L,m.peekQ(SP-0x30L),"existing destructor pushed RET");
                    return v(0x500L);
                }
                heapCall(call,m,SP-0x58L,BLOCK);
                number(1L,call.nonvolatileBits().rbxBits(),"wrapper flag preserved through mature body");
                number(BLOCK,call.nonvolatileBits().rdiBits(),"wrapper object preserved through mature body");
                number(I+0x23DA6A6L,m.peekQ(SP-0x30L),"free uses wrapper's existing continuation");
                return with(after,1L,after.rcxBits(),after.rdxBits());
            }
        };
        NormalReturn got=DeletingWrappers284.executePlayerInfo(
                new Entry(I,SP,with(v(0x100L),0xAAAAL,BLOCK,1L),N),m,
                DeletingWrapperFreeCalls.bind(I,m,p));
        equal(with(after,BLOCK,after.rcxBits(),after.rdxBits()),got.volatileBits(),"actual wrapper final V");
        rootReturn(got);number(2,p.calls.size(),"only opaque destructor plus mature heap port");
        number(0,m.peekD(SP-0x20L),"actual child home DWORD address");
    }
    private static void actualManagerOptIn() {
        Mem m=heapMemory();m.seedQ(SP,RET);m.seedQ(GS,TLS);m.seedD(TLS+0x10L,1);
        m.seedD(I+0x5D1EB08L,0);m.seedQ(BLOCK+0x88L,0);m.seedQ(BLOCK+0x70L,0);
        m.seedQ(BLOCK+0x58L,0);m.seedQ(BLOCK+0x40L,0);m.seedQ(BLOCK+0x20L,STATIC);
        VolatileBits after=v(0xA00L);
        Ports p=new Ports(){
            @Override public VolatileBits invoke(Call call) {
                calls.add(call);heapCall(call,m,SP-0x58L,BLOCK);
                number(I+0x28EE5F6L,m.peekQ(SP-0x30L),"manager actual free continuation");
                return with(after,1L,after.rcxBits(),after.rdxBits());
            }
        };
        NormalReturn got=ManagerLifecycle286.executeWithStaticObjectAndWrapperFree(
                new Entry(I,SP,with(v(0x200L),0xAAAA,BLOCK,1),N),m,p,
                (header,cursor)->{throw new AssertionError("empty manager array cannot iterate");});
        rootReturn(got);equal(with(after,BLOCK,after.rcxBits(),after.rdxBits()),got.volatileBits(),"manager final full V");
        number(1,p.calls.size(),"only mature heap port residual, no static/destructor/free delegate");
        number(1,p.gsReads,"qualified static supplier is actually reached");
        number(I+0x4763EE0L,m.peekQ(BLOCK),"actual manager destructor writes vtable");
        number(0,m.peekD(SP-0x20L),"manager free reaches mature home write");
    }
    private static void residualIdentity() {
        Mem m=new Mem();VolatileBits answer=v(0xB00L);NormalReturn tailAnswer=new NormalReturn(answer,5,6,N);
        final Tail[] seen={null};
        Ports p=new Ports(){
            @Override public VolatileBits invoke(Call call){calls.add(call);return answer;}
            @Override public NormalReturn tail(Tail t){seen[0]=t;return tailAnswer;}
        };
        Calls bound=DeletingWrapperFreeCalls.bind(I,m,p);
        Call[] residual={new Call(0x23DA6A2,TargetKind.DIRECT_RVA,0x4223F44,SP,v(1),N),
            new Call(0x23DA6A1,TargetKind.INDIRECT_ABSOLUTE,0x4223F44,SP,v(2),N),
            new Call(0x28EE5F1,TargetKind.DIRECT_RVA,I+0x4223F44L,SP,v(3),N)};
        for(Call call:residual){same(answer,bound.invoke(call),"residual V identity");same(call,p.calls.get(p.calls.size()-1),"original Call identity");}
        Entry entry=new Entry(I,SP,v(4),N);Tail transfer=new Tail(7,TargetKind.DIRECT_RVA,8,entry);
        same(tailAnswer,bound.tail(transfer),"tail NR identity");same(transfer,seen[0],"tail transfer identity");
        same(entry,seen[0].entry(),"tail entry identity");number(GS,bound.readGsQword58(),"GS raw bits");
        number(0,m.trace.size(),"unmatched paths never touch memory");
        RuntimeException marker=new IllegalStateException("opaque marker");
        Calls failing=DeletingWrapperFreeCalls.bind(I,m,new Ports(){@Override public VolatileBits invoke(Call c){throw marker;}});
        same(marker,expect(IllegalStateException.class,()->failing.invoke(residual[0])),"opaque failure identity");
    }
    private static void preAndPostBoundaries() {
        long site=0x23DA6A1L,pre=SP-8L,child=pre-8L,expected=I+site+5L;
        Call call=new Call(site,TargetKind.DIRECT_RVA,0x4223F44L,pre,with(v(5),0,BLOCK,0),N);
        Mem bad=new Mem();bad.seedQ(child,expected+1L);
        expect(IllegalStateException.class,()->DeletingWrapperFreeCalls.bind(I,bad,new Ports()).invoke(call));
        equal(List.of("Q:"+hex(child)),bad.trace,"bad preexisting RET refuses before every child effect");
        for(boolean corruptN:new boolean[]{false,true}) {
            Mem m=heapMemory();m.seedQ(child,expected);
            Ports p=new Ports(){@Override public VolatileBits invoke(Call actual){
                calls.add(actual);heapCall(actual,m,child-0x28L,BLOCK);
                if(corruptN)m.writeQword(child-8L,N.rbxBits()+1L);else m.writeQword(child,expected+1L);
                return with(v(0xC00),1,2,3);
            }};
            expect(IllegalStateException.class,()->DeletingWrapperFreeCalls.bind(I,m,p).invoke(call));
            number(1,p.calls.size(),"postboundary check follows one real mature port");
            check(m.trace.contains("WD:"+hex(child+0x10L)),"postboundary failure is after actual mature body");
        }
    }
    private static Mem heapMemory(){Mem m=new Mem();m.seedQ(I+0x5C5DE30L,HEAP);m.seedQ(I+0x43DA748L,TARGET);return m;}
    private static void heapCall(Call c,Mem m,long pre,long block){
        number(0x424E37AL,c.callSiteRva(),"mature actual first IAT site");
        equal(TargetKind.INDIRECT_ABSOLUTE,c.kind(),"IAT absolute role");number(TARGET,c.targetBits(),"fresh IAT target");
        number(pre,c.rspBits(),"exact nested preCALL SP, no extra push");
        number(I+0x424E380L,m.peekQ(pre-8L),"actual mature CALL RET");
        number(HEAP,c.volatileBits().rcxBits(),"heap RCX");number(0,c.volatileBits().rdxBits(),"heap flags");number(block,c.volatileBits().r8Bits(),"heap R8 block");
    }
    private static void rootReturn(NormalReturn r){equal(N,r.nonvolatileBits(),"all represented N restored");number(RET,r.returnRipBits(),"actual root RET");number(SP+8L,r.callerRspBits(),"actual root SP");}
    private static VolatileBits v(long s){return new VolatileBits(s+1,s+2,s+3,s+4,s+5,s+6,s+7,
        new Bits128(s+8,s+9),new Bits128(s+10,s+11),new Bits128(s+12,s+13),
        new Bits128(s+14,s+15),new Bits128(s+16,s+17),new Bits128(s+18,s+19));}
    private static VolatileBits with(VolatileBits v,long a,long c,long d){return new VolatileBits(a,c,d,v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static String hex(long x){return Long.toUnsignedString(x,16);}
    private static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
    private static void number(long a,long b,String s){check(a==b,s+" expected="+a+" actual="+b);}
    private static void equal(Object a,Object b,String s){check(a.equals(b),s+" expected="+a+" actual="+b);}
    private static void same(Object a,Object b,String s){check(a==b,s);}
    private static RuntimeException expect(Class<? extends RuntimeException> type,Runnable work){try{work.run();}catch(RuntimeException e){check(type.isInstance(e),"exact failure type");return e;}throw new AssertionError("missing "+type);}
    private static class Ports implements Calls {
        final List<Call> calls=new ArrayList<>();int gsReads;
        @Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected opaque CALL "+c);}
        @Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected tail");}
        @Override public long readGsQword58(){gsReads++;return GS;}
    }
    private static final class Mem implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Integer> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();
        long scriptDwordAddress=Long.MIN_VALUE;int scriptDwordValue;
        void seed(long a,long v,int n){for(int k=0;k<n;k++)bytes.put(a+k,(int)(v>>>(8*k))&255);}
        void seedQ(long a,long v){seed(a,v,8);}void seedD(long a,int v){seed(a,Integer.toUnsignedLong(v),4);}
        long raw(long a,int n){long v=0;for(int k=0;k<n;k++){Integer b=bytes.get(a+k);if(b==null)throw new AssertionError("uninitialized "+hex(a+k));v|=(long)b<<(8*k);}return v;}
        long peekQ(long a){return raw(a,8);}int peekD(long a){return(int)raw(a,4);}
        @Override public long readQword(long a){trace.add("Q:"+hex(a));return raw(a,8);}
        @Override public int readDword(long a){trace.add("D:"+hex(a));return a==scriptDwordAddress?scriptDwordValue:(int)raw(a,4);}
        @Override public int readUnsignedByte(long a){trace.add("B:"+hex(a));return(int)raw(a,1);}
        @Override public void writeQword(long a,long v){trace.add("WQ:"+hex(a));seedQ(a,v);}
        @Override public void writeDword(long a,int v){trace.add("WD:"+hex(a));seedD(a,v);}
        @Override public void writeByte(long a,int v){trace.add("WB:"+hex(a));seed(a,v,1);}
        @Override public int lockedXaddDword(long a,int v){throw new AssertionError("unexpected LOCK");}
        @Override public Bits128 read128(long a){throw new AssertionError("unexpected read128");}
        @Override public void write128(long a,Bits128 v){throw new AssertionError("unexpected write128");}
    }
}
