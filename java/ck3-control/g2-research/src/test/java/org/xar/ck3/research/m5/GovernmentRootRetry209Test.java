package org.xar.ck3.research.m5;

import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New Root178 caller integration. Explicit owned RAM/opaque ports; no Native/full ABI claim. */
final class GovernmentRootRetry209Test {
    private static final long I=0x180000000L,S=0x900008L,TLS=0x880000L,TLS_ROW=0x881000L;
    private static final long P=0x100002000L,H=0x778800L,TARGET=0x7fff12345678L,RET=0x22334455L,FRESH_RET=0x8899aabbL;
    private static final int FLOAT_BITS=0x7fa12345;
    private static final NonvolatileBits N=new NonvolatileBits(101,102,103,104,105,106,107,108,new Bits128(109,110));
    private static VolatileBits v(long seed,long rax) {
        return new VolatileBits(rax,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,
                new Bits128(seed+10,seed+11),new Bits128(seed+12,seed+13),new Bits128(seed+14,seed+15),
                new Bits128(seed+16,seed+17),new Bits128(seed+18,seed+19),new Bits128(seed+20,seed+21));
    }
    private static VolatileBits regs(VolatileBits a,long rax,long rcx,long rdx,long r8,Bits128 x0) {
        return new VolatileBits(rax,rcx,rdx,r8,a.r9Bits(),a.r10Bits(),a.r11Bits(),x0,a.xmm1(),a.xmm2(),a.xmm3(),a.xmm4(),a.xmm5());
    }
    private record Write(long address,int width,long low,long high) { }
    private static final class Ram implements GovernmentRoot178Api.Memory {
        final Map<Long,Integer> bytes=new HashMap<>();
        final List<Write> writes=new ArrayList<>();
        void seed(long address,int width,long low,long high) {
            for(int i=0;i<width;i++) bytes.put(address+i,(int)((i<8?low:high)>>>((i%8)*8))&255);
        }
        @Override public int readUnsignedByte(long address) {
            Integer value=bytes.get(address);if(value==null)throw new AssertionError("unseeded RAM "+Long.toHexString(address));return value;
        }
        @Override public int readDword(long address) {int out=0;for(int i=0;i<4;i++)out|=readUnsignedByte(address+i)<<(8*i);return out;}
        @Override public long readQword(long address) {long out=0;for(int i=0;i<8;i++)out|=(long)readUnsignedByte(address+i)<<(8*i);return out;}
        @Override public Bits128 read128(long address) {return new Bits128(readQword(address),readQword(address+8));}
        private void write(long address,int width,long low,long high) {writes.add(new Write(address,width,low,high));seed(address,width,low,high);}
        @Override public void writeDword(long address,int value) {write(address,4,Integer.toUnsignedLong(value),0);}
        @Override public void writeQword(long address,long value) {write(address,8,value,0);}
        @Override public void writeByte(long address,int value) {write(address,1,value&255L,0);}
        @Override public void write128(long address,Bits128 value) {write(address,16,value.lowBits(),value.highBits());}
        @Override public int lockedXaddDword(long address,int value) {throw new AssertionError("unexpected atomic");}
    }
    private static Ram ram(int guard,int tls) {
        Ram m=new Ram();m.seed(S,8,RET,0);m.seed(TLS,8,TLS_ROW,0);m.seed(TLS_ROW+16,4,Integer.toUnsignedLong(tls),0);
        m.seed(I+0x5dc11c0L,4,Integer.toUnsignedLong(guard),0);m.seed(I+0x49f6464L,4,Integer.toUnsignedLong(FLOAT_BITS),0);
        m.seed(I+0x5c5de30L,8,H,0);m.seed(I+0x43da768L,8,TARGET,0);return m;
    }
    private static final class Outer implements GovernmentRoot178Api.Calls {
        final Ram memory;final List<OpaqueCall> calls=new ArrayList<>();int gs;
        final VolatileBits first=v(200,201),third=v(300,301),fourth=v(400,401),last=v(500,501);
        Outer(Ram memory) {this.memory=memory;}
        @Override public long readGsQword58() {gs++;return TLS;}
        @Override public VolatileBits invoke(OpaqueCall call) {
            calls.add(call);
            return switch((int)call.callSiteRva()) {
                case 0x3f5c0c3 -> {memory.writeDword(I+0x5dc11c0L,-1);yield first;}
                case 0x3f5c155 -> third;
                case 0x3f5c162 -> fourth;
                case 0x3f5c16f -> {memory.writeQword(S,FRESH_RET);yield last;}
                default -> throw new AssertionError("unmatched outer "+call);
            };
        }
    }
    private abstract static class Lower implements GovernmentCrtBoundary185Api.Calls {
        @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail tail) {throw new AssertionError(tail);}
        @Override public long readGsQword58() {throw new AssertionError("lower GS must remain distinct");}
    }
    private static GovernmentRoot178Api.Entry entry() {return new GovernmentRoot178Api.Entry(I,S,v(10,11),N);}

    @Test void rootInitializationReallyExecutesRetryAndHeapChildrenOnSameRam() {
        Ram m=ram(2,0);Map<Long,Integer> expected=new HashMap<>(m.bytes);Outer outer=new Outer(m);
        VolatileBits heap=v(600,P);List<GovernmentCrtBoundary185Api.Call> lowerCalls=new ArrayList<>();List<Long> steps=new ArrayList<>();
        var out=GovernmentRootRetry209.execute(entry(),m,outer,new Lower(){
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                lowerCalls.add(call);
                assertEquals(0x424fddeL,call.callSiteRva());assertEquals(GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,call.kind());
                assertEquals(TARGET,call.targetBits());assertEquals(S-0x88,call.rspBits());
                assertEquals(I+0x424fde4L,m.readQword(S-0x90));assertEquals(I+0x4223bb3L,m.readQword(S-0x60));
                assertEquals(I+0x3f5c0fcL,m.readQword(S-0x30));
                assertEquals(64,call.volatileBits().r8Bits());assertEquals(H,call.volatileBits().rcxBits());assertEquals(0,call.volatileBits().rdxBits());
                assertEquals(64,call.nonvolatileBits().rbxBits());return heap;
            }
        },(site,guard)->{assertEquals(0x4223baeL,site);assertEquals(64,guard);steps.add(site);});
        assertEquals(1,outer.gs);assertEquals(1,lowerCalls.size());assertEquals(1,steps.size());
        assertEquals(List.of(0x3f5c0c3L,0x3f5c155L,0x3f5c162L,0x3f5c16fL),outer.calls.stream().map(OpaqueCall::callSiteRva).toList());
        assertTrue(outer.calls.stream().allMatch(c->c.rspBits()==S-0x28 && c.nonvolatileBits().equals(N)));
        assertEquals(new GovernmentRoot178Api.NormalReturn(regs(outer.last,I+0x5dc11d0L,outer.last.rcxBits(),outer.last.rdxBits(),outer.last.r8Bits(),outer.last.xmm0()),FRESH_RET,S+8,N),out);
        assertEquals(new OpaqueCall(0x3f5c155L,0x3714560L,S-0x28,
                regs(heap,P,I+0x5dc11e8L,16,P,new Bits128(Integer.toUnsignedLong(FLOAT_BITS),0)),N),outer.calls.get(1));
        List<Write> literal=List.of(new Write(S-0x30,8,I+0x3f5c0c8L,0),new Write(I+0x5dc11c0L,4,0xffffffffL,0),
            new Write(I+0x5dc11d0L,4,0,0),new Write(I+0x5dc11d8L,8,0,0),new Write(I+0x5dc11e0L,8,0,0),
            new Write(S-0x30,8,I+0x3f5c0fcL,0),new Write(S-0x38,8,N.rbxBits(),0),
            new Write(S-0x60,8,I+0x4223bb3L,0),new Write(S-0x68,8,64,0),new Write(S-0x90,8,I+0x424fde4L,0),
            new Write(P,8,P,0),new Write(P+8,8,P,0),new Write(I+0x5dc11d8L,8,P,0),new Write(I+0x5dc11e8L,8,0,0),
            new Write(I+0x5dc11f0L,16,0,0),new Write(I+0x5dc1200L,8,7,0),new Write(I+0x5dc1208L,8,8,0),
            new Write(I+0x5dc11d0L,4,Integer.toUnsignedLong(FLOAT_BITS),0),new Write(S-0x30,8,I+0x3f5c15aL,0),
            new Write(S-0x30,8,I+0x3f5c167L,0),new Write(S-0x30,8,I+0x3f5c174L,0),new Write(S,8,FRESH_RET,0));
        assertEquals(literal,m.writes);
        for(Write w:literal)for(int k=0;k<w.width();k++)expected.put(w.address()+k,(int)((k<8?w.low():w.high())>>>((k%8)*8))&255);
        assertEquals(expected,m.bytes);
    }

    @Test void newWholeCallerEarlyPathPreservesRootStateWithoutTouchingRetryPorts() {
        Ram m=ram(-1,Integer.MAX_VALUE);Map<Long,Integer> before=new HashMap<>(m.bytes);Outer outer=new Outer(m);
        var out=GovernmentRootRetry209.execute(entry(),m,outer,new Lower(){@Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call c){throw new AssertionError(c);}},
                (site,guard)->{throw new AssertionError("unexpected budget");});
        VolatileBits initial=entry().volatileBits();
        assertEquals(new GovernmentRoot178Api.NormalReturn(regs(initial,I+0x5dc11d0L,TLS_ROW,16,initial.r8Bits(),initial.xmm0()),RET,S+8,N),out);
        assertEquals(1,outer.gs);assertTrue(outer.calls.isEmpty());assertTrue(m.writes.isEmpty());assertEquals(before,m.bytes);
    }

    @Test void wholeCallerPropagatesBudgetLowerAndFreshReturnSlotFailures() {
        for(int mode=0;mode<3;mode++) {
            final int fault=mode;Ram m=ram(2,0);Outer outer=new Outer(m);var exact=new IllegalArgumentException("owned-stop-"+mode);
            var lower=new Lower(){@Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call){
                if(fault==1)throw exact;
                if(fault==2)m.writeQword(S-0x30,0x77778888L);
                return v(600,P);
            }};
            if(mode<2)assertSame(exact,assertThrows(IllegalArgumentException.class,()->GovernmentRootRetry209.execute(entry(),m,outer,lower,
                    (site,guard)->{if(fault==0)throw exact;})));
            else assertThrows(UnsupportedOperationException.class,()->GovernmentRootRetry209.execute(entry(),m,outer,lower,(site,guard)->{}));
            assertEquals(1,outer.gs);assertEquals(List.of(0x3f5c0c3L),outer.calls.stream().map(OpaqueCall::callSiteRva).toList());
            assertEquals(0,m.readQword(I+0x5dc11d8L));assertFalse(m.bytes.containsKey(P));
        }
    }
}
