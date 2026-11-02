package org.xar.ck3.research.m0.lifecycle286;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
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

/** Three new composition cases, using only owned strict byte memory and caller-supplied raw state. */
public final class ManagerStaticObjectCompositionWitness {
    private static final long IMAGE=0x140000000L,SP=0x730008L,RET=0x123456789ABCDEF0L;
    private static final long GS=0x810000L,TLS=0x920000L,OBJECT=IMAGE+0x5D1EAF0L,GUARD=IMAGE+0x5D1EB08L;
    private static final NonvolatileBits N=new NonvolatileBits(
            0x1010101010101010L,0x2020202020202020L,0x3030303030303030L,0x4040404040404040L,
            0xFEDCBA9876543210L,0x6060606060606060L,0x7070707070707070L,0x8080808080808080L,
            new Bits128(0x9191919191919191L,0xA2A2A2A2A2A2A2A2L));

    private static final long MANAGER=0xB00000L;
    private static int checks;
    private ManagerStaticObjectCompositionWitness() { }

    public static void main(String[] args) {
        optInCompleteOriginalChain();
        legacyResidualSupplierUnchanged();
        remainingOuterFreeAndFailure();
        System.out.println("PASS cases=3 checks="+checks+" represented185_only=true Game=false");
    }

    private static void optInCompleteOriginalChain() {
        Mem m=managerMemory();Ports residual=new Ports();VolatileBits incoming=incoming(0);
        NormalReturn result=ManagerLifecycle286.executeWithStaticObject357(
                new Entry(IMAGE,SP,incoming,N),m,residual,ManagerStaticObjectCompositionWitness::noLoop);
        equal(replace3(incoming,MANAGER,TLS,16L),result.volatileBits(),"new composition full final V");
        equal(N,result.nonvolatileBits(),"root full N restored");number(RET,result.returnRipBits(),"caller actual root RET");
        number(SP+8L,result.callerRspBits(),"caller actual root SP");
        number(1,residual.gsReads,"new supplier is reached inside captured fallback");
        number(0,residual.calls.size(),"static supplier not delegated to residual");
        number(IMAGE+0x4763EE0L,m.peekQ(MANAGER),"actual manager vptr effect");
        number(IMAGE+0x28EE5E4L,m.peekQ(SP-0x30L),"outer existing destructor continuation");
        number(IMAGE+0x28EE6B4L,m.peekQ(SP-0x60L),"inner existing supplier continuation");
        number(1,m.readDword(TLS+16L),"owned TLS unchanged");
        number(0,m.readDword(GUARD),"owned guard unchanged on fast path");
    }

    private static void legacyResidualSupplierUnchanged() {
        Mem m=managerMemory();VolatileBits supplied=replaceRax(v(0x500L),OBJECT);
        Ports residual=new Ports(){
            @Override public VolatileBits invoke(Call call) {
                calls.add(call);
                number(0x28EE6AFL,call.callSiteRva(),"legacy actual supplier site");
                equal(TargetKind.DIRECT_RVA,call.kind(),"legacy direct RVA");
                number(0xB15000L,call.targetBits(),"legacy opaque target");
                number(SP-0x58L,call.rspBits(),"actual nested pre-call SP");
                number(IMAGE+0x28EE6B4L,m.peekQ(SP-0x60L),"actual preexisting pushed slot");
                number(OBJECT,call.nonvolatileBits().rdiBits(),"captured bucket in current RDI");
                number(MANAGER,call.nonvolatileBits().rbxBits(),"actual manager in current RBX");
                return supplied;
            }
            @Override public long readGsQword58() { throw new AssertionError("legacy must stay residual"); }
        };
        NormalReturn result=ManagerLifecycle286.execute(new Entry(IMAGE,SP,incoming(0),N),
                m,residual,ManagerStaticObjectCompositionWitness::noLoop);
        number(1,residual.calls.size(),"legacy exactly one residual supplier");
        equal(replaceRax(supplied,MANAGER),result.volatileBits(),"legacy opaque V then wrapper RAX");
        equal(N,result.nonvolatileBits(),"legacy root N");number(RET,result.returnRipBits(),"legacy root RET");
        number(SP+8L,result.callerRspBits(),"legacy root SP");
    }

    private static void remainingOuterFreeAndFailure() {
        Mem m=managerMemory();VolatileBits supplied=v(0x600L);
        Ports residual=new Ports(){
            @Override public VolatileBits invoke(Call call) {
                calls.add(call);outerFree(call,m);
                return supplied;
            }
        };
        NormalReturn result=ManagerLifecycle286.executeWithStaticObject357(
                new Entry(IMAGE,SP,incoming(1),N),m,residual,ManagerStaticObjectCompositionWitness::noLoop);
        number(1,residual.calls.size(),"only actual outer free stays residual");
        number(1,residual.gsReads,"supplier reached before outer free");
        equal(replaceRax(supplied,MANAGER),result.volatileBits(),"outer opaque full V then wrapper RAX");
        equal(N,result.nonvolatileBits(),"flags wrapper restores N");
        number(RET,result.returnRipBits(),"flags wrapper root RET");number(SP+8L,result.callerRspBits(),"flags wrapper root SP");
        RuntimeException marker=new IllegalStateException("real residual call failure");
        Mem failing=managerMemory();
        Ports failure=new Ports(){
            @Override public VolatileBits invoke(Call call) {
                calls.add(call);outerFree(call,failing);throw marker;
            }
        };
        same(marker,expect(RuntimeException.class,()->ManagerLifecycle286.executeWithStaticObject357(
                new Entry(IMAGE,SP,incoming(1),N),failing,failure,ManagerStaticObjectCompositionWitness::noLoop)),
                "remaining callback failure identity");
        number(1,failure.calls.size(),"real remaining residual was reached");
        number(1,failure.gsReads,"supplier still precedes callback failure");
    }

    private static void outerFree(Call call,Mem m) {
        number(0x28EE5F1L,call.callSiteRva(),"actual wrapper free site");
        equal(TargetKind.DIRECT_RVA,call.kind(),"actual free target role");
        number(0x4223F44L,call.targetBits(),"outer free remains opaque");
        number(SP-0x28L,call.rspBits(),"outer free pre-call SP");
        number(IMAGE+0x28EE5F6L,m.peekQ(SP-0x30L),"actual outer free continuation");
        number(MANAGER,call.volatileBits().rcxBits(),"actual free RCX");
        number(0xA0L,call.volatileBits().rdxBits(),"actual free RDX size");
        number(OBJECT,call.volatileBits().raxBits(),"actual preceding supplier RAX");
        NonvolatileBits expected=new NonvolatileBits(1L,N.rbpBits(),N.rsiBits(),MANAGER,
                N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
        equal(expected,call.nonvolatileBits(),"exact current wrapper N");
    }
    private static VolatileBits incoming(long flags) { return replace3(v(0x100L),0x111L,MANAGER,flags); }
    private static void noLoop(long header,long cursor) { throw new AssertionError("empty arrays have no loop"); }
    private static Mem managerMemory() {
        Mem m=new Mem();m.seedQ(SP,RET);m.seedQ(GS,TLS);m.seedD(TLS+16L,1);m.seedD(GUARD,0);
        m.seedQ(MANAGER+0x88L,0);m.seedQ(MANAGER+0x70L,0);m.seedQ(MANAGER+0x58L,0);
        m.seedQ(MANAGER+0x40L,0);m.seedQ(MANAGER+0x20L,OBJECT);
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
