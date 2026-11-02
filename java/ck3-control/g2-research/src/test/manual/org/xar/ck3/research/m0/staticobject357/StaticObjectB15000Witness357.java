package org.xar.ck3.research.m0.staticobject357;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m0.lifecycle285.ManagerDestructor28ee610;
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

/** Four new source-derived literal cases; no Game, CRT implementation or native ABI claim. */
public final class StaticObjectB15000Witness357 {
    private static final long IMAGE=0x140000000L,SP=0x730008L,RET=0x123456789ABCDEF0L;
    private static final long GS=0x810000L,TLS=0x920000L,OBJECT=IMAGE+0x5D1EAF0L,GUARD=IMAGE+0x5D1EB08L;
    private static final NonvolatileBits N=new NonvolatileBits(
            0x1010101010101010L,0x2020202020202020L,0x3030303030303030L,0x4040404040404040L,
            0xFEDCBA9876543210L,0x6060606060606060L,0x7070707070707070L,0x8080808080808080L,
            new Bits128(0x9191919191919191L,0xA2A2A2A2A2A2A2A2L));
    private static int checks;
    private StaticObjectB15000Witness357() { }

    public static void main(String[] args) {
        signedGuardAndFullFastReturn();
        callbackConditionalAndFreshFullVolatile();
        exactBindingForwardAndRejects();
        managerConsumerAndFailurePropagation();
        System.out.println("PASS cases=4 checks="+checks+" represented185_only=true Game=false");
    }

    private static void signedGuardAndFullFastReturn() {
        int[][] boundaries={{0,0},{-1,0},{Integer.MIN_VALUE,-1},{Integer.MIN_VALUE,Integer.MIN_VALUE}};
        for(int[] values:boundaries) {
            Mem m=prepared(SP,values[1],values[0]);Ports p=new Ports();VolatileBits incoming=v(0x100L);
            NormalReturn result=StaticObjectB15000FullState.execute(new Entry(IMAGE,SP,incoming,N),m,p);
            equal(replace3(incoming,OBJECT,TLS,16L),result.volatileBits(),"fast full V");
            equal(N,result.nonvolatileBits(),"all full N including R12 high bits");
            number(RET,result.returnRipBits(),"actual RET read");number(SP+8L,result.callerRspBits(),"RET SP");
            number(1,p.gsReads,"one GS read");number(0,p.calls.size(),"no callback");
            equal(List.of(key("Q",GS),key("D",TLS+16L),key("D",GUARD),key("Q",SP)),m.trace,"fast access order");
            for(int i=0;i<16;i++) number(0x9D,m.peekByte(OBJECT+i),"fast object byte unchanged");
        }
    }

    private static void callbackConditionalAndFreshFullVolatile() {
        VolatileBits incoming=v(0x100L),header=v(0x200L),footer=v(0x300L);
        Mem once=prepared(SP,1,9);
        Ports p=new Ports(){
            @Override public VolatileBits invoke(Call call) {
                calls.add(call);
                checkCall(call,0xB15033L,0x4223A84L,SP-0x28L,N);
                equal(replace3(incoming,1L,GUARD,16L),call.volatileBits(),"header actual complete input");
                number(IMAGE+0xB15038L,once.peekQ(SP-0x30L),"header continuation");
                once.trace.add("HEADER");once.seedD(GUARD,0);return header;
            }
        };
        NormalReturn first=StaticObjectB15000FullState.execute(new Entry(IMAGE,SP,incoming,N),once,p);
        equal(replaceRax(header,OBJECT),first.volatileBits(),"header returned RCX/RDX/XMM preserved");
        number(1,p.calls.size(),"fresh nonminus1 guard skips footer");
        equal(List.of(key("Q",GS),key("D",TLS+16L),key("D",GUARD),key("WQ",SP-0x30L),
                "HEADER",key("D",GUARD),key("Q",SP)),once.trace,"fresh guard order");
        for(int i=0;i<16;i++) number(0x9D,once.peekByte(OBJECT+i),"header-only object unchanged");

        Mem twice=prepared(SP,Integer.MIN_VALUE,0);
        long changedRet=0x6A6A6A6A5B5B5B5BL;
        Ports both=new Ports(){
            @Override public VolatileBits invoke(Call call) {
                calls.add(call);
                if(calls.size()==1) {
                    checkCall(call,0xB15033L,0x4223A84L,SP-0x28L,N);
                    equal(replace3(incoming,0x80000000L,GUARD,16L),call.volatileBits(),"signed branch and EAX zero extension");
                    number(IMAGE+0xB15038L,twice.peekQ(SP-0x30L),"first actual RIP");
                    twice.trace.add("HEADER");twice.seedD(GUARD,-1);return header;
                }
                number(2,calls.size(),"only two actual calls");
                checkCall(call,0xB15056L,0x4223A24L,SP-0x28L,N);
                equal(replace3(header,header.raxBits(),GUARD,header.rdxBits()),call.volatileBits(),"footer gets fresh header V");
                number(IMAGE+0xB1505BL,twice.peekQ(SP-0x30L),"second actual RIP no extra push");
                for(int i=0;i<16;i++) number(i==0?0:i==12?255:0x9D,twice.peekByte(OBJECT+i),"exact two byte stores before footer");
                twice.trace.add("FOOTER");twice.seedQ(SP,changedRet);return footer;
            }
        };
        NormalReturn second=StaticObjectB15000FullState.execute(new Entry(IMAGE,SP,incoming,N),twice,both);
        equal(replaceRax(footer,OBJECT),second.volatileBits(),"footer all V then final RAX");
        number(changedRet,second.returnRipBits(),"actual final RET observes callback mutation");
        number(SP+8L,second.callerRspBits(),"unchanged fixed SP");
        equal(N,second.nonvolatileBits(),"opaque normal N preservation");
        equal(List.of(key("Q",GS),key("D",TLS+16L),key("D",GUARD),key("WQ",SP-0x30L),"HEADER",
                key("D",GUARD),key("WB",OBJECT),key("WB",OBJECT+12L),key("WQ",SP-0x30L),
                "FOOTER",key("Q",SP)),twice.trace,"two call/write/RET literal order");
    }

    private static void exactBindingForwardAndRejects() {
        VolatileBits incoming=v(0x100L);
        Mem m=prepared(SP,1,0);m.seedQ(SP,IMAGE+0x28EE6B4L);
        Ports fallback=new Ports();Calls bound=ManagerStaticObjectB15000Calls.bind(IMAGE,m,fallback);
        Call selected=new Call(0x28EE6AFL,TargetKind.DIRECT_RVA,0xB15000L,SP+8L,incoming,N);
        VolatileBits result=bound.invoke(selected);
        equal(replace3(incoming,OBJECT,TLS,16L),result,"actual selected callee V");
        number(0,fallback.calls.size(),"no opaque supplier remains");number(1,fallback.gsReads,"GS forwarded");

        Call[] unmatched={
            new Call(0x28EE6AEL,TargetKind.DIRECT_RVA,0xB15000L,3L,incoming,N),
            new Call(0x28EE6AFL,TargetKind.INDIRECT_ABSOLUTE,0xB15000L,3L,incoming,N),
            new Call(0x28EE6AFL,TargetKind.DIRECT_RVA,0xB15001L,3L,incoming,N)};
        VolatileBits forwarded=v(0x900L);
        NormalReturn tailResult=new NormalReturn(forwarded,7L,8L,N);
        Ports pass=new Ports(){
            @Override public VolatileBits invoke(Call call) { calls.add(call);return forwarded; }
            @Override public NormalReturn tail(Tail transfer) { lastTail=transfer;return tailResult; }
        };
        Calls passthrough=ManagerStaticObjectB15000Calls.bind(IMAGE,new Mem(),pass);
        for(Call call:unmatched) {
            same(forwarded,passthrough.invoke(call),"unmatched result identity");
            same(call,pass.calls.get(pass.calls.size()-1),"unmatched argument identity");
        }
        Tail tail=new Tail(9L,TargetKind.DIRECT_RVA,0xB15000L,new Entry(IMAGE,SP,incoming,N));
        same(tailResult,passthrough.tail(tail),"tail result identity");same(tail,pass.lastTail,"tail original identity");
        number(GS,passthrough.readGsQword58(),"GS exact forwarding");

        Mem bad=prepared(SP,1,0);Ports untouched=new Ports();
        expect(IllegalStateException.class,()->ManagerStaticObjectB15000Calls.bind(IMAGE,bad,untouched).invoke(selected));
        number(0,untouched.gsReads,"bad existing slot rejects before GS");
        equal(List.of(key("Q",SP)),bad.trace,"no target effects on bad existing slot");

        Mem altered=prepared(SP,1,9);altered.seedQ(SP,IMAGE+0x28EE6B4L);
        Ports corruptReturn=new Ports(){
            @Override public VolatileBits invoke(Call call) {
                calls.add(call);altered.seedD(GUARD,0);altered.seedQ(SP,RET);return forwarded;
            }
        };
        expect(IllegalStateException.class,()->ManagerStaticObjectB15000Calls.bind(IMAGE,altered,corruptReturn).invoke(selected));
        number(1,corruptReturn.calls.size(),"bad actual RET rejects after target call");
        number(RET,altered.peekQ(SP),"actual callback return-slot mutation retained");
    }

    private static void managerConsumerAndFailurePropagation() {
        long manager=0xB00000L,entrySp=0xA30008L;
        Mem m=prepared(entrySp,1,0);
        m.seedQ(manager+0x88L,0);m.seedQ(manager+0x70L,0);m.seedQ(manager+0x58L,0);
        m.seedQ(manager+0x40L,0);m.seedQ(manager+0x20L,OBJECT);
        VolatileBits incoming=replace3(v(0x100L),0x111L,manager,0x333L);
        Ports fallback=new Ports();
        NormalReturn result=ManagerDestructor28ee610.execute(new Entry(IMAGE,entrySp,incoming,N),m,
                ManagerStaticObjectB15000Calls.bind(IMAGE,m,fallback),
                (header,cursor)->{ throw new AssertionError("no loop in empty child"); });
        equal(replace3(incoming,OBJECT,TLS,16L),result.volatileBits(),"actual manager consumer complete V");
        equal(N,result.nonvolatileBits(),"actual manager N restored");number(RET,result.returnRipBits(),"manager real RET");
        number(entrySp+8L,result.callerRspBits(),"manager actual SP");number(1,fallback.gsReads,"real supplier route reached once");
        number(0,fallback.calls.size(),"all empty child/supplier actual mappings; no unknown call synthesized");
        number(IMAGE+0x4763EE0L,m.peekQ(manager),"original manager vptr effect");
        number(IMAGE+0x28EE6B4L,m.peekQ(entrySp-0x30L),"supplier existing caller slot");

        RuntimeException marker=new IllegalArgumentException("opaque callback failure");
        Mem throwing=prepared(SP,1,9);
        Ports failure=new Ports(){
            @Override public VolatileBits invoke(Call call) { calls.add(call);throw marker; }
        };
        same(marker,expect(RuntimeException.class,()->StaticObjectB15000FullState.execute(
                new Entry(IMAGE,SP,incoming,N),throwing,failure)),"callback exception identity");
        check(!throwing.trace.contains(key("Q",SP)),"no successful RET after failure");
        Mem memoryFault=prepared(SP,1,0);
        RuntimeException nativeFault=new IllegalStateException("owned memory failure");
        memoryFault.failReadDwordAddress=TLS+16L;memoryFault.failure=nativeFault;
        same(nativeFault,expect(RuntimeException.class,()->StaticObjectB15000FullState.execute(
                new Entry(IMAGE,SP,incoming,N),memoryFault,new Ports())),"Memory exception identity");
    }

    private static void checkCall(Call call,long site,long target,long sp,NonvolatileBits n) {
        number(site,call.callSiteRva(),"call site");equal(TargetKind.DIRECT_RVA,call.kind(),"direct RVA interpretation");
        number(target,call.targetBits(),"target RVA");number(sp,call.rspBits(),"actual pre-call SP");equal(n,call.nonvolatileBits(),"call N");
    }
    private static Mem prepared(long sp,int epoch,int guard) {
        Mem m=new Mem();m.seedQ(sp,RET);m.seedQ(GS,TLS);m.seedD(TLS+16L,epoch);m.seedD(GUARD,guard);
        for(int i=0;i<16;i++) m.seedByte(OBJECT+i,0x9D);
        return m;
    }
    private static VolatileBits v(long seed) {
        return new VolatileBits(seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,
                new Bits128(seed+8,seed+9),new Bits128(seed+10,seed+11),new Bits128(seed+12,seed+13),
                new Bits128(seed+14,seed+15),new Bits128(seed+16,seed+17),new Bits128(seed+18,seed+19));
    }
    private static VolatileBits replaceRax(VolatileBits v,long rax) { return replace3(v,rax,v.rcxBits(),v.rdxBits()); }
    private static VolatileBits replace3(VolatileBits v,long rax,long rcx,long rdx) {
        return new VolatileBits(rax,rcx,rdx,v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static String key(String operation,long address) { return operation+":"+Long.toUnsignedString(address,16); }
    private static void check(boolean condition,String name) { checks++;if(!condition)throw new AssertionError(name); }
    private static void number(long wanted,long actual,String name) { check(wanted==actual,name+" wanted="+wanted+" actual="+actual); }
    private static void equal(Object wanted,Object actual,String name) { check(wanted.equals(actual),name+" wanted="+wanted+" actual="+actual); }
    private static void same(Object wanted,Object actual,String name) { check(wanted==actual,name); }
    private static RuntimeException expect(Class<? extends RuntimeException> type,Runnable operation) {
        try { operation.run(); } catch(RuntimeException failure) {
            check(type.isInstance(failure),"exception actual type");return failure;
        }
        throw new AssertionError("expected "+type.getName());
    }
    private static class Ports implements Calls {
        final List<Call> calls=new ArrayList<>();
        Tail lastTail;
        int gsReads;
        @Override public long readGsQword58() { gsReads++;return GS; }
        @Override public VolatileBits invoke(Call call) { throw new AssertionError("unexpected opaque call "+call); }
        @Override public NormalReturn tail(Tail transfer) { throw new AssertionError("unexpected tail"); }
    }
    private static final class Mem implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Integer> data=new HashMap<>();
        final List<String> trace=new ArrayList<>();
        long failReadDwordAddress=Long.MIN_VALUE;
        RuntimeException failure;
        void seedByte(long address,int value) { data.put(address,value&255); }
        void seedD(long address,int value) { seed(address,Integer.toUnsignedLong(value),4); }
        void seedQ(long address,long value) { seed(address,value,8); }
        private void seed(long address,long value,int count) {
            for(int i=0;i<count;i++) seedByte(address+i,(int)(value >>> (i*8)));
        }
        int peekByte(long address) {
            Integer value=data.get(address);
            if(value==null)throw new AssertionError("uninitialized "+Long.toHexString(address));
            return value;
        }
        long peekQ(long address) { return raw(address,8); }
        private long raw(long address,int count) {
            long value=0;
            for(int i=0;i<count;i++) value|=(long)peekByte(address+i) << (i*8);
            return value;
        }
        @Override public int readDword(long address) {
            trace.add(key("D",address));
            if(address==failReadDwordAddress && failure!=null)throw failure;
            return (int)raw(address,4);
        }
        @Override public long readQword(long address) { trace.add(key("Q",address));return raw(address,8); }
        @Override public int readUnsignedByte(long address) { trace.add(key("B",address));return peekByte(address); }
        @Override public void writeDword(long address,int value) { trace.add(key("WD",address));seedD(address,value); }
        @Override public void writeQword(long address,long value) { trace.add(key("WQ",address));seedQ(address,value); }
        @Override public void writeByte(long address,int value) { trace.add(key("WB",address));seedByte(address,value); }
        @Override public int lockedXaddDword(long address,int value) { throw new AssertionError("unexpected LOCK"); }
        @Override public Bits128 read128(long address) { throw new AssertionError("unexpected128 read"); }
        @Override public void write128(long address,Bits128 value) { throw new AssertionError("unexpected128 write"); }
    }
}
