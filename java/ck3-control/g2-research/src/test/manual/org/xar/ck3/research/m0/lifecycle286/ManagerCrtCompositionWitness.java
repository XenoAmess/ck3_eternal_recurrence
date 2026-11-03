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

/** New composed Manager scenes, not an OS/CRT implementation or old isolated-callee rerun. */
public final class ManagerCrtCompositionWitness {
    private static final long I=0x140000000L,S=0x730008L,RET=0x123456789ABCDEF0L;
    private static final long BLOCK=0xB00000L,GS=0x810000L,TLS=0x920000L;
    private static final long STATIC=I+0x5D1EAF0L,GUARD=I+0x5D1EB08L;
    private static final long ENTER=0x710000L,LEAVE=0x720000L,HEAP=0xA00000L,FREE=0x1111222233334444L;
    private static final NonvolatileBits N=new NonvolatileBits(0x101L,0x202L,0x303L,0x404L,
            0xFEDCBA9876543210L,0x606L,0x707L,0x808L,new Bits128(0x919L,0xA2AL));
    private static int checks;
    private ManagerCrtCompositionWitness() { }
    public static void main(String[] args) {
        steadyHeaderInActualManager();
        initializeFooterAndRetainFree();
        legacyRemainsExplicitlyResidual();
        System.out.println("PASS cases=3 checks="+checks+" represented185_only=true Game=false");
    }
    private static void steadyHeaderInActualManager() {
        Mem m=fixture(1,0,5);Ports p=new Ports(m,false);
        List<Long> budget=new ArrayList<>();
        NormalReturn got=ManagerLifecycle286.executeWithStaticCrtAndWrapperFree(entry(0),m,p,
                (site,cursor)->{number(0x4223A9AL,site,"real header budget site");number(GUARD,cursor,"real header guard address");budget.add(site);});
        rootReturn(got);number(1,budget.size(),"one actual header step");
        equal(List.of(0x4223A94L),p.sites,"supplier/header binding removed only B15033 from residual");
        equal(List.of(0x4223AE4L),p.tails,"original header tail stays residual");
        number(1,m.dword(GUARD),"steady guard preserved");number(5,m.dword(TLS+0x10L),"real header updates thread epoch");
        number(5,m.dword(I+0x542F090L),"steady global epoch unchanged");number(2,p.gsReads,"supplier and header actual GS reads");
        number(I+0x5C5CB18L,got.volatileBits().rcxBits(),"actual header tail RCX retained");
        number(TLS,got.volatileBits().rdxBits(),"actual header TLS RDX retained");
        number(0x10L,got.volatileBits().r8Bits(),"actual header R8 retained");
    }
    private static void initializeFooterAndRetainFree() {
        Mem m=fixture(0,-1,10);Ports p=new Ports(m,true);
        List<Long> budget=new ArrayList<>();
        NormalReturn got=ManagerLifecycle286.executeWithStaticCrtAndWrapperFree(entry(1),m,p,
                (site,cursor)->{number(0x4223A9AL,site,"initialization header loop");number(GUARD,cursor,"initialization guard");budget.add(site);});
        rootReturn(got);number(1,budget.size(),"zero guard initialized without wait loop");
        equal(List.of(0x4223A94L,0x4223A34L,0x4223A74L,0x424E37AL),p.sites,"new composed header/footer and retained free actual routes");
        equal(List.of(0x4223AE4L,0x4223A7FL),p.tails,"both actual tails stay opaque");
        number(0,m.raw(STATIC,1),"supplier initializes first byte");number(255,m.raw(STATIC+12L,1),"supplier initializes sentinel byte");
        number(11,m.dword(I+0x542F090L),"real footer increments global epoch");
        number(11,m.dword(GUARD),"real footer publishes guard epoch");number(11,m.dword(TLS+0x10L),"real footer publishes TLS epoch");
        number(2,p.gsReads,"supplier and footer GS reads");number(0,m.dword(S-0x20L),"retained free actual home write");
        equal(with(p.freeAnswer,BLOCK,p.freeAnswer.rcxBits(),p.freeAnswer.rdxBits()),got.volatileBits(),"all actual final volatile bits from free producer/wrapper");
    }
    private static void legacyRemainsExplicitlyResidual() {
        Mem m=fixture(0,-1,10);RuntimeException marker=new IllegalStateException("legacy residual marker");
        List<Call> calls=new ArrayList<>();
        Calls ports=new Calls() {
            @Override public VolatileBits invoke(Call c) {calls.add(c);throw marker;}
            @Override public NormalReturn tail(Tail t) {throw new AssertionError("legacy reached an unexpected tail");}
            @Override public long readGsQword58() {return GS;}
        };
        RuntimeException got;
        try {ManagerLifecycle286.executeWithStaticObjectAndWrapperFree(entry(0),m,ports,
                (site,cursor)->{throw new AssertionError("legacy cannot execute new header algorithm");});throw new AssertionError("missing residual exception");}
        catch(RuntimeException e) {got=e;}
        same(marker,got,"legacy residual exception identity");number(1,calls.size(),"one legacy forwarded CRT call");
        Call call=calls.get(0);number(0xB15033L,call.callSiteRva(),"legacy original caller site");
        equal(TargetKind.DIRECT_RVA,call.kind(),"legacy raw direct kind");number(0x4223A84L,call.targetBits(),"legacy raw target");
        number(S-0x88L,call.rspBits(),"legacy actual preCALL SP");number(I+0xB15038L,m.raw(S-0x90L,8),"legacy actual pushed return");
        number(0,m.dword(GUARD),"legacy never ran real header");number(10,m.dword(I+0x542F090L),"legacy never ran real footer");
    }
    private static Entry entry(long flags) {return new Entry(I,S,with(v(0x200L),0xAAAAL,BLOCK,flags),N);}
    private static Mem fixture(int guard,int tlsEpoch,int globalEpoch) {
        Mem m=new Mem();m.seed(S,RET,8);m.seed(GS,TLS,8);m.seed(TLS+0x10L,Integer.toUnsignedLong(tlsEpoch),4);
        m.seed(GUARD,Integer.toUnsignedLong(guard),4);m.seed(I+0x542F090L,globalEpoch,4);m.seed(I+0x5C5CBC4L,0,4);
        m.seed(I+0x43DA500L,ENTER,8);m.seed(I+0x43DA4F0L,LEAVE,8);
        m.seed(I+0x5C5DE30L,HEAP,8);m.seed(I+0x43DA748L,FREE,8);
        m.seed(BLOCK+0x88L,0,8);m.seed(BLOCK+0x70L,0,8);m.seed(BLOCK+0x58L,0,8);m.seed(BLOCK+0x40L,0,8);m.seed(BLOCK+0x20L,STATIC,8);
        return m;
    }
    private static final class Ports implements Calls {
        final Mem memory;final boolean allowFree;final List<Long> sites=new ArrayList<>(),tails=new ArrayList<>();int gsReads;
        final VolatileBits freeAnswer=with(v(0xD00L),1,0xDDD1L,0xDDD2L);
        Ports(Mem memory,boolean allowFree) {this.memory=memory;this.allowFree=allowFree;}
        @Override public VolatileBits invoke(Call c) {
            sites.add(c.callSiteRva());equal(TargetKind.INDIRECT_ABSOLUTE,c.kind(),"opaque import role");
            if(c.callSiteRva()==0x424E37AL) {
                check(allowFree,"free only in newly composed flag1 scene");number(FREE,c.targetBits(),"fresh free IAT target");
                number(S-0x58L,c.rspBits(),"retained free nested preCALL SP");number(I+0x424E380L,memory.raw(S-0x60L,8),"retained free actual RET");
                number(HEAP,c.volatileBits().rcxBits(),"free heap argument");number(0,c.volatileBits().rdxBits(),"free flags");number(BLOCK,c.volatileBits().r8Bits(),"free object");
                return freeAnswer;
            }
            check(c.callSiteRva()==0x4223A94L||c.callSiteRva()==0x4223A34L||c.callSiteRva()==0x4223A74L,"only declared CRT import sites");
            number(c.callSiteRva()==0x4223A74L?LEAVE:ENTER,c.targetBits(),"actual IAT operand");
            number(S-0xB8L,c.rspBits(),"CRT original preCALL SP");number(I+c.callSiteRva()+6L,memory.raw(S-0xC0L,8),"CRT actual return push");
            number(I+0x5C5CB18L,c.volatileBits().rcxBits(),"mutex argument");return c.volatileBits();
        }
        @Override public NormalReturn tail(Tail t) {
            tails.add(t.jumpSiteRva());number(S-0x90L,t.entry().rspBits(),"tail owns no extra push or RET");
            if(t.jumpSiteRva()==0x4223AE4L) {equal(TargetKind.INDIRECT_ABSOLUTE,t.kind(),"header indirect tail");number(LEAVE,t.targetBits(),"header fresh leave target");}
            else {number(0x4223A7FL,t.jumpSiteRva(),"footer tail site");equal(TargetKind.DIRECT_RVA,t.kind(),"footer direct tail");number(0x4223AECL,t.targetBits(),"footer unknown notify target");}
            return new NormalReturn(t.entry().volatileBits(),memory.readQword(t.entry().rspBits()),t.entry().rspBits()+8L,t.entry().nonvolatileBits());
        }
        @Override public long readGsQword58() {gsReads++;return GS;}
    }
    private static final class Mem implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Integer> bytes=new HashMap<>();
        void seed(long a,long v,int n) {for(int k=0;k<n;k++)bytes.put(a+k,(int)(v>>>(8*k))&255);}
        long raw(long a,int n) {long value=0;for(int k=0;k<n;k++){Integer b=bytes.get(a+k);if(b==null)throw new AssertionError("uninitialized byte "+Long.toUnsignedString(a+k,16));value|=(long)b<<(8*k);}return value;}
        int dword(long a) {return (int)raw(a,4);}
        @Override public long readQword(long a) {return raw(a,8);}
        @Override public int readDword(long a) {return dword(a);}
        @Override public int readUnsignedByte(long a) {return (int)raw(a,1);}
        @Override public void writeQword(long a,long v) {seed(a,v,8);}
        @Override public void writeDword(long a,int v) {seed(a,Integer.toUnsignedLong(v),4);}
        @Override public void writeByte(long a,int v) {seed(a,v,1);}
        @Override public int lockedXaddDword(long a,int v) {throw new AssertionError("unexpected LOCK");}
        @Override public Bits128 read128(long a) {throw new AssertionError("unexpected read128");}
        @Override public void write128(long a,Bits128 v) {throw new AssertionError("unexpected write128");}
    }
    private static void rootReturn(NormalReturn got) {equal(N,got.nonvolatileBits(),"all represented N restored");number(RET,got.returnRipBits(),"root original RET");number(S+8L,got.callerRspBits(),"root caller SP");number(BLOCK,got.volatileBits().raxBits(),"wrapper final object RAX");}
    private static VolatileBits v(long s) {return new VolatileBits(s+1,s+2,s+3,s+4,s+5,s+6,s+7,new Bits128(s+8,s+9),new Bits128(s+10,s+11),new Bits128(s+12,s+13),new Bits128(s+14,s+15),new Bits128(s+16,s+17),new Bits128(s+18,s+19));}
    private static VolatileBits with(VolatileBits v,long a,long c,long d) {return new VolatileBits(a,c,d,v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static void check(boolean b,String s) {checks++;if(!b)throw new AssertionError(s);}
    private static void number(long a,long b,String s) {check(a==b,s+" expected="+a+" actual="+b);}
    private static void equal(Object a,Object b,String s) {check(a.equals(b),s+" expected="+a+" actual="+b);}
    private static void same(Object a,Object b,String s) {check(a==b,s);}
}
