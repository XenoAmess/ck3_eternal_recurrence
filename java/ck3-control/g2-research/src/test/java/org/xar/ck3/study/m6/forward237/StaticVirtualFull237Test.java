package org.xar.ck3.study.m6.forward237;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New represented-state software cases only; no Native memory, hardware ABI, flags or FP environment claim. */
public final class StaticVirtualFull237Test {
    private static final long IMAGE=0x140000000L,S=0x9008,OBJECT=0x2000,TABLE=0x3000,RETURNED=0x4000,RETURNED_TABLE=0x5000;
    private static final long FIRST=0x777700001111L,SECOND=0x888800002222L,OUTER=0xAABBCCDD12345678L;
    private static int scenes,checks;
    private StaticVirtualFull237Test() { }
    public static void main(String[] args) {
        run("allocateOpaqueFullStateFreshSaves",StaticVirtualFull237Test::allocateOpaque);
        run("freeOpaqueTwoOwnedCalls",StaticVirtualFull237Test::freeOpaque);
        run("selfStillHasStackFrame",()->self(OBJECT,OBJECT+0x8));
        run("wrappedSelfStillHasStackFrame",()->self(-0x8L,0));
        run("firstFailureRetainsExactPrefix",StaticVirtualFull237Test::firstFailure);
        run("knownProviderDefaultZeroNoLower",StaticVirtualFull237Test::knownFreeZero);
        run("knownProviderTailDefaultRetrySameRam",StaticVirtualFull237Test::knownAllocate);
        run("sameTargetSecondCallRemainsOpaque",StaticVirtualFull237Test::sameTargetSecond);
        System.out.println("PASS scenes="+scenes+" checks="+checks+" represented185Only=true normalWhole7=true guardedPrefix1=true knownProvider224New2=true fullHardwareABI=false Native=false Game=false");
    }
    private static void allocateOpaque() {
        Ram m=ram();Entry e=entry(0x21);VolatileBits first=rax(v(0x900),RETURNED);
        AtomicReference<NormalReturn> exact=new AtomicReference<>();AtomicInteger count=new AtomicInteger();
        Calls ports=new Port() {
            @Override public VolatileBits invoke(Call c) {
                equal(c.callSiteRva(),0x855883L);equal(c.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(c.targetBits(),FIRST);equal(c.rspBits(),S-0x28);
                equal(c.volatileBits(),rax(e.volatileBits(),TABLE));equal(c.nonvolatileBits(),nv(n(),e.volatileBits().r8Bits(),e.volatileBits().rdxBits()));
                equal(m.readQword(S-0x30),IMAGE+0x855886);count.incrementAndGet();
                m.writeQword(S+0x8,0xC001);m.writeQword(S-0x8,0xD002);m.writeQword(S,0xE003);
                m.writeQword(RETURNED,RETURNED_TABLE+0x100);m.writeQword(RETURNED_TABLE+0x108,SECOND);
                return first;
            }
            @Override public NormalReturn tail(Tail t) {
                equal(t.jumpSiteRva(),0x8558A0L);equal(t.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(t.targetBits(),SECOND);equal(t.entry().rspBits(),S);
                equal(t.entry().volatileBits(),args(first,RETURNED,RETURNED,e.volatileBits().rdxBits(),e.volatileBits().r8Bits(),SECOND));
                equal(t.entry().nonvolatileBits(),nv(n(),0xC001,0xD002));
                var out=new NormalReturn(v(0xB00),m.readQword(t.entry().rspBits()),S+0x8,t.entry().nonvolatileBits());exact.set(out);return out;
            }
        };
        var out=StaticVirtualFullState237.fromSlot08(e,m,ports);
        check(out==exact.get());equal(count.get(),1);equal(out.returnRipBits(),0xE003L);equal(out.callerRspBits(),S+0x8);
        equal(m.reads.stream().filter(a->a==S).count(),1L);equal(m.writes.stream().filter(a->a==S-0x30).count(),1L);
        check(m.reads.contains(RETURNED_TABLE+0x108));check(!m.reads.contains(RETURNED_TABLE+0x8));
    }
    private static void freeOpaque() {
        Ram m=ram();Entry e=entry(0x21);VolatileBits first=rax(v(0x1000),RETURNED),second=v(0x2000);AtomicInteger count=new AtomicInteger();
        Calls ports=new Port() {
            @Override public VolatileBits invoke(Call c) {
                equal(c.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(c.rspBits(),S-0x28);
                equal(c.nonvolatileBits(),nv(n(),e.volatileBits().rdxBits(),e.volatileBits().r8Bits()));
                if(count.getAndIncrement()==0) {
                    equal(c.callSiteRva(),0x85584CL);equal(c.targetBits(),FIRST);equal(c.volatileBits(),rax(e.volatileBits(),TABLE));
                    equal(m.readQword(S-0x30),IMAGE+0x85584F);return first;
                }
                equal(c.callSiteRva(),0x85585BL);equal(c.targetBits(),SECOND);equal(m.readQword(S-0x30),IMAGE+0x85585F);
                equal(c.volatileBits(),args(first,RETURNED,RETURNED,e.volatileBits().rdxBits(),e.volatileBits().r8Bits(),RETURNED_TABLE));
                m.writeQword(S+0x8,0xC011);m.writeQword(S-0x8,0xD012);m.writeQword(S,0xE013);return second;
            }
        };
        var out=StaticVirtualFullState237.fromSlot10(e,m,ports);
        equal(count.get(),2);equal(out.volatileBits(),second);equal(out.nonvolatileBits(),nv(n(),0xC011,0xD012));equal(out.returnRipBits(),0xE013L);equal(out.callerRspBits(),S+0x8);
        equal(m.writes.stream().filter(a->a==S-0x30).count(),2L);
    }
    private static void self(long rcx,long rdx) {
        Ram m=new Ram();m.poke(S,OUTER);VolatileBits in=args(v(0x3000),0xBAD,rcx,rdx,0x8000000000000042L,0xDEAD);
        var e=new Entry(IMAGE,S,in,n());var out=StaticVirtualFullState237.fromSlot10(e,m,null);
        equal(out.volatileBits(),rax(in,rcx+0x8));equal(out.nonvolatileBits(),n());equal(out.returnRipBits(),OUTER);equal(out.callerRspBits(),S+0x8);
        equal(m.writes,List.of(S+0x8,S-0x8));equal(m.reads,List.of(S+0x8,S-0x8,S));
    }
    private static void firstFailure() {
        Ram m=ram();RuntimeException original=new IllegalStateException("software237-first");
        Calls ports=new Port(){@Override public VolatileBits invoke(Call c){throw original;}};
        try{StaticVirtualFullState237.fromSlot08(entry(0x21),m,ports);throw new AssertionError("expected original");}catch(RuntimeException failure){check(failure==original);}
        equal(m.peek(S+0x8),n().rbxBits());equal(m.peek(S-0x8),n().rdiBits());equal(m.peek(S-0x30),IMAGE+0x855886);
        check(!m.reads.contains(S+0x8)&&!m.reads.contains(S-0x8)&&!m.reads.contains(S));check(!m.reads.contains(RETURNED));
    }
    private static void knownFreeZero() {
        Ram m=known(0x8571C0,0x8571D0);Entry e=entry(0);
        var out=KnownStaticVirtualFull237.fromSlot10(e,m,null,null);
        equal(out.volatileBits(),args(e.volatileBits(),RETURNED,RETURNED,0,e.volatileBits().r8Bits(),RETURNED_TABLE));
        equal(out.nonvolatileBits(),n());equal(out.returnRipBits(),OUTER);equal(out.callerRspBits(),S+0x8);
        check(m.reads.contains(OBJECT+0x408));equal(m.reads.stream().filter(a->a==S-0x30).count(),2L);
    }
    private static void knownAllocate() {
        Ram m=known(0x8571C0,0x8571D0);Entry e=entry(0x20);VolatileBits returned=v(0x5000);AtomicInteger count=new AtomicInteger(),budget=new AtomicInteger();
        Calls ports=new Port(){@Override public VolatileBits invoke(Call c){
            equal(c.callSiteRva(),0x4223BAEL);equal(c.kind(),TargetKind.DIRECT_RVA);equal(c.targetBits(),0x42420B8L);equal(c.rspBits(),S-0x58);
            equal(c.volatileBits().rcxBits(),0x20L);equal(c.nonvolatileBits().rbxBits(),0x20L);equal(c.nonvolatileBits().r12Bits(),n().r12Bits());
            equal(m.readQword(S-0x60),IMAGE+0x4223BB3);m.writeQword(S,0xE023);count.incrementAndGet();return returned;
        }};
        var out=KnownStaticVirtualFull237.fromSlot08(e,m,ports,(rva,address)->{equal(rva,0x4223BAEL);equal(address,0x20L);budget.incrementAndGet();});
        equal(count.get(),1);equal(budget.get(),1);equal(out.volatileBits(),returned);equal(out.nonvolatileBits(),n());equal(out.returnRipBits(),0xE023L);equal(out.callerRspBits(),S+0x8);
        equal(m.peek(S-0x30),IMAGE+0x8571DC);check(m.reads.contains(OBJECT+0x408));
    }
    private static void sameTargetSecond() {
        Ram m=known(0x86E140,0x8571D0);Entry e=entry(0x21);AtomicInteger calls=new AtomicInteger();VolatileBits returned=v(0x6000);
        Calls ports=new Port(){@Override public VolatileBits invoke(Call c){
            equal(c.callSiteRva(),0x85585BL);equal(c.targetBits(),IMAGE+0x86E140);equal(c.kind(),TargetKind.INDIRECT_ABSOLUTE);
            equal(c.volatileBits().rcxBits(),RETURNED);equal(c.volatileBits().r9Bits(),RETURNED_TABLE);equal(m.readQword(S-0x30),IMAGE+0x85585F);calls.incrementAndGet();return returned;
        }};
        var out=KnownStaticVirtualFull237.fromSlot10(e,m,ports,null);
        equal(calls.get(),1);equal(out.volatileBits(),returned);equal(out.nonvolatileBits(),n());check(!m.reads.contains(RETURNED+0x408));
    }
    private static Ram ram(){Ram m=new Ram();m.poke(S,OUTER);m.poke(OBJECT,TABLE);m.poke(TABLE+0x38,FIRST);m.poke(RETURNED,RETURNED_TABLE);m.poke(RETURNED_TABLE+0x8,SECOND);m.poke(RETURNED_TABLE+0x10,SECOND);return m;}
    private static Ram known(long freeRva,long allocRva){Ram m=ram();m.poke(TABLE+0x38,IMAGE+0x86E140);m.poke(OBJECT+0x408,RETURNED);m.poke(RETURNED_TABLE+0x8,IMAGE+allocRva);m.poke(RETURNED_TABLE+0x10,IMAGE+freeRva);return m;}
    private static Entry entry(long rdx){return new Entry(IMAGE,S,args(v(0x100),0xE001,OBJECT,rdx,0x38,0xE009),n());}
    private static Bits128 x(long tag){return new Bits128(0x8000000000000000L|tag,0xF000000000000000L|tag);}
    private static VolatileBits v(long tag){return new VolatileBits(tag+1,tag+2,tag+3,tag+8,tag+9,tag+10,tag+11,x(tag+0x10),x(tag+0x20),x(tag+0x30),x(tag+0x40),x(tag+0x50),x(tag+0x60));}
    private static VolatileBits rax(VolatileBits v,long rax){return args(v,rax,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits());}
    private static VolatileBits args(VolatileBits v,long rax,long rcx,long rdx,long r8,long r9){return new VolatileBits(rax,rcx,rdx,r8,r9,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static NonvolatileBits n(){return new NonvolatileBits(0xB1,0xB2,0xB3,0xB4,0xF000000100000005L,0xB6,0xB7,0xB8,x(0xB9));}
    private static NonvolatileBits nv(NonvolatileBits n,long rbx,long rdi){return new NonvolatileBits(rbx,n.rbpBits(),n.rsiBits(),rdi,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static class Port implements Calls {
        @Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected CALL "+Long.toHexString(c.callSiteRva()));}
        @Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected TAIL "+Long.toHexString(t.jumpSiteRva()));}
        @Override public long readGsQword58(){throw new AssertionError("unexpected GS");}
    }
    private static final class Ram implements Memory {
        final Map<Long,Integer> bytes=new HashMap<>();final List<Long> reads=new ArrayList<>(),writes=new ArrayList<>();
        void poke(long a,long v){for(int i=0;i<8;i++)bytes.put(a+i,(int)(v>>>(i*8))&0xFF);}
        long peek(long a){long v=0;for(int i=0;i<8;i++){Integer b=bytes.get(a+i);if(b==null)throw new UnsupportedOperationException("unheld RAM "+Long.toHexString(a+i));v|=(long)b<<(i*8);}return v;}
        @Override public long readQword(long a){reads.add(a);return peek(a);}
        @Override public void writeQword(long a,long v){writes.add(a);poke(a,v);}
        @Override public int readDword(long a){int v=0;for(int i=0;i<4;i++)v|=readUnsignedByte(a+i)<<(i*8);return v;}
        @Override public void writeDword(long a,int v){for(int i=0;i<4;i++)writeByte(a+i,v>>>(i*8));}
        @Override public int readUnsignedByte(long a){Integer v=bytes.get(a);if(v==null)throw new UnsupportedOperationException("unheld byte");return v;}
        @Override public void writeByte(long a,int v){bytes.put(a,v&0xFF);}
        @Override public Bits128 read128(long a){return new Bits128(readQword(a),readQword(a+8));}
        @Override public void write128(long a,Bits128 v){writeQword(a,v.lowBits());writeQword(a+8,v.highBits());}
        @Override public int lockedXaddDword(long a,int delta){throw new UnsupportedOperationException("not used by237");}
    }
    private static void run(String name,Runnable body){body.run();scenes++;System.out.println("PASS "+name);}
    private static void check(boolean value){checks++;if(!value)throw new AssertionError("check "+checks);}
    private static void equal(Object actual,Object expected){checks++;if(!java.util.Objects.equals(actual,expected))throw new AssertionError("check "+checks+" actual="+actual+" expected="+expected);}
}
