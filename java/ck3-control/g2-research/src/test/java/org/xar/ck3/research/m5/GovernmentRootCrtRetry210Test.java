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

/** New whole-caller coupling, explicit owned ports/RAM; no imported routine or Native qualification. */
final class GovernmentRootCrtRetry210Test {
    private static final long I=0x190000000L,S=0xb00008L,GS=0xc00000L,ROOT_TLS=0xc01000L,CRT_TLS=0xc03000L;
    private static final long P=0x100004000L,H=0x77abc0L,HEAP_TARGET=0x7fffabc12345L;
    private static final long ENTER_TARGET=0x7000000100L,EXIT_TARGET=0x7000000200L,RET=0x76543210L,FRESH_RET=0x1122334455667788L;
    private static final int FLOAT_BITS=0x3f900000;
    private static final NonvolatileBits N=new NonvolatileBits(101,102,103,104,105,106,107,108,new Bits128(109,110));

    private static VolatileBits v(long seed,long rax) {
        return new VolatileBits(rax,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,
                new Bits128(seed+10,seed+11),new Bits128(seed+12,seed+13),new Bits128(seed+14,seed+15),
                new Bits128(seed+16,seed+17),new Bits128(seed+18,seed+19),new Bits128(seed+20,seed+21));
    }
    private static VolatileBits regs(VolatileBits a,long rax,long rcx,long rdx,long r8,long r9,Bits128 x0) {
        return new VolatileBits(rax,rcx,rdx,r8,r9,a.r10Bits(),a.r11Bits(),x0,a.xmm1(),a.xmm2(),a.xmm3(),a.xmm4(),a.xmm5());
    }
    private static NonvolatileBits rbx(long value) {
        return new NonvolatileBits(value,N.rbpBits(),N.rsiBits(),N.rdiBits(),N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
    }
    private record Write(long address,int width,long low,long high) { }
    /** Implements only RootMemory, exercising the actual existing as185 forwarding view. */
    private static final class Ram implements GovernmentRoot178Api.Memory {
        final Map<Long,Integer> bytes=new HashMap<>();
        final List<Write> writes=new ArrayList<>();
        List<Integer> guardScript;
        long guardScriptAddress;
        int guardScriptIndex;
        void seed(long address,int width,long low,long high) {
            for(int i=0;i<width;i++)bytes.put(address+i,(int)((i<8?low:high)>>>((i%8)*8))&255);
        }
        @Override public int readUnsignedByte(long address) {
            Integer value=bytes.get(address);if(value==null)throw new AssertionError("unseeded RAM "+Long.toHexString(address));return value;
        }
        @Override public int readDword(long address) {
            if(guardScript!=null && address==guardScriptAddress) {
                assertTrue(guardScriptIndex<guardScript.size(),"unexpected extra guard observation");
                return guardScript.get(guardScriptIndex++);
            }
            int result=0;for(int i=0;i<4;i++)result|=readUnsignedByte(address+i)<<(8*i);return result;
        }
        @Override public long readQword(long address) {long result=0;for(int i=0;i<8;i++)result|=(long)readUnsignedByte(address+i)<<(8*i);return result;}
        @Override public Bits128 read128(long address) {return new Bits128(readQword(address),readQword(address+8));}
        private void write(long address,int width,long low,long high) {writes.add(new Write(address,width,low,high));seed(address,width,low,high);}
        @Override public void writeDword(long address,int value) {write(address,4,Integer.toUnsignedLong(value),0);}
        @Override public void writeQword(long address,long value) {write(address,8,value,0);}
        @Override public void writeByte(long address,int value) {write(address,1,value&255L,0);}
        @Override public void write128(long address,Bits128 value) {write(address,16,value.lowBits(),value.highBits());}
        @Override public int lockedXaddDword(long address,int value) {throw new AssertionError("unexpected atomic");}
    }
    private static final class Fixture {
        final Ram memory=new Ram();
        final List<String> events=new ArrayList<>();
        final int initialGuard,initialRootTls,epoch,fault;
        final IllegalArgumentException exact=new IllegalArgumentException("owned-header-budget");
        final VolatileBits initial=v(10,11),header=v(200,201),heap=v(600,P),other=v(300,301);
        final VolatileBits wrapper=v(400,0x100000000L),footerEnter=v(500,501),footerExit=v(700,701);
        int allocationCalls,outerCalls,crtCalls;
        Fixture(int guard,int rootTls,int epoch,int fault) {
            this.initialGuard=guard;this.initialRootTls=rootTls;this.epoch=epoch;this.fault=fault;
            memory.seed(S,8,RET,0);memory.seed(GS,8,ROOT_TLS,0);memory.seed(GS+3*8,8,CRT_TLS,0);
            memory.seed(ROOT_TLS+16,4,Integer.toUnsignedLong(rootTls),0);memory.seed(CRT_TLS+16,4,0x76543210L,0);
            memory.seed(I+0x5dc11c0L,4,Integer.toUnsignedLong(guard),0);memory.seed(I+0x542f090L,4,Integer.toUnsignedLong(epoch),0);
            memory.seed(I+0x5c5cbc4L,4,3,0);memory.seed(I+0x49f6464L,4,Integer.toUnsignedLong(FLOAT_BITS),0);
            memory.seed(I+0x5c5de30L,8,H,0);memory.seed(I+0x43da768L,8,HEAP_TARGET,0);
            memory.seed(I+0x43da500L,8,ENTER_TARGET,0);memory.seed(I+0x43da4f0L,8,EXIT_TARGET,0);
        }
        final GovernmentRoot178Api.Calls outer=new GovernmentRoot178Api.Calls() {
            @Override public long readGsQword58() {events.add("outerGS");return GS;}
            @Override public VolatileBits invoke(OpaqueCall call) {
                outerCalls++;events.add("outer3714560");
                assertEquals(0x3f5c155L,call.callSiteRva());assertEquals(0x3714560L,call.targetRva());
                assertEquals(S-0x28,call.rspBits());assertEquals(N,call.nonvolatileBits());
                assertEquals(regs(heap,P,I+0x5dc11e8L,16,P,heap.r9Bits(),new Bits128(FLOAT_BITS,0)),call.volatileBits());
                memory.writeQword(S,FRESH_RET);return other;
            }
        };
        final GovernmentCrtBoundary185Api.Calls allocation=new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                allocationCalls++;events.add("allocation-IAT");
                assertEquals(0x424fddeL,call.callSiteRva());assertEquals(GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,call.kind());
                assertEquals(HEAP_TARGET,call.targetBits());assertEquals(S-0x88,call.rspBits());
                assertEquals(I+0x424fde4L,memory.readQword(S-0x90));assertEquals(I+0x4223bb3L,memory.readQword(S-0x60));
                assertEquals(I+0x3f5c0fcL,memory.readQword(S-0x30));assertEquals(H,call.volatileBits().rcxBits());
                assertEquals(0,call.volatileBits().rdxBits());assertEquals(64,call.volatileBits().r8Bits());
                assertEquals(rbx(64),call.nonvolatileBits());return heap;
            }
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail t) {throw new AssertionError(t);}
            @Override public long readGsQword58() {throw new AssertionError("allocation GS not on selected path");}
        };
        final GovernmentCrtBoundary185Api.LoopBudget allocationBudget=(site,value)->{
            events.add("allocation-budget");assertEquals(0x4223baeL,site);assertEquals(64,value);
        };
        final GovernmentCrtBoundary185Api.LoopBudget crtBudget=this::crtStep;
        private void crtStep(long site,long value) {
            events.add("crt-budget-header");assertEquals(0x4223a9aL,site);assertEquals(I+0x5dc11c0L,value);
            if(fault==2)throw exact;
        }
        final GovernmentCrtBoundary185Api.Calls crt=new GovernmentCrtBoundary185Api.Calls() {
            @Override public long readGsQword58() {events.add("crtGS");return GS;}
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                crtCalls++;assertEquals(S-0x58,call.rspBits());
                switch((int)call.callSiteRva()) {
                    case 0x4223a94:
                        events.add("crt-enter-header");assertEquals(GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,call.kind());
                        assertEquals(ENTER_TARGET,call.targetBits());assertEquals(I+0x4223a9aL,memory.readQword(S-0x60));
                        assertEquals(I+0x3f5c0c8L,memory.readQword(S-0x30));assertEquals(N.rbxBits(),memory.readQword(S-0x38));
                        assertEquals(rbx(I+0x5dc11c0L),call.nonvolatileBits());
                        assertEquals(regs(initial,Integer.toUnsignedLong(initialRootTls),I+0x5c5cb18L,16,initial.r8Bits(),initial.r9Bits(),initial.xmm0()),call.volatileBits());
                        return header;
                    case 0x4223f28:
                        events.add("crt3EE8");assertEquals(GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,call.kind());
                        assertEquals(0x4223ee8L,call.targetBits());assertEquals(N,call.nonvolatileBits());
                        assertEquals(I+0x4223f2dL,memory.readQword(S-0x60));
                        assertEquals(regs(other,other.raxBits(),I+0x43d7820L,other.rdxBits(),other.r8Bits(),other.r9Bits(),other.xmm0()),call.volatileBits());
                        return wrapper;
                    case 0x4223a34:
                        events.add("crt-enter-footer");assertEquals(GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,call.kind());
                        assertEquals(ENTER_TARGET,call.targetBits());assertEquals(rbx(I+0x5dc11c0L),call.nonvolatileBits());
                        assertEquals(I+0x4223a3aL,memory.readQword(S-0x60));assertEquals(I+0x3f5c174L,memory.readQword(S-0x30));
                        assertEquals(regs(wrapper,0,I+0x5c5cb18L,wrapper.rdxBits(),wrapper.r8Bits(),wrapper.r9Bits(),wrapper.xmm0()),call.volatileBits());
                        return footerEnter;
                    case 0x4223a74:
                        events.add("crt-exit-footer");assertEquals(GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,call.kind());
                        assertEquals(EXIT_TARGET,call.targetBits());assertEquals(rbx(I+0x5dc11c0L),call.nonvolatileBits());
                        assertEquals(I+0x4223a7aL,memory.readQword(S-0x60));
                        assertEquals(0,memory.readDword(I+0x542f090L));assertEquals(0,memory.readDword(I+0x5dc11c0L));assertEquals(0,memory.readDword(CRT_TLS+16));
                        assertEquals(regs(footerEnter,0,I+0x5c5cb18L,3,CRT_TLS,16,footerEnter.xmm0()),call.volatileBits());
                        return footerExit;
                    default: throw new AssertionError("unexpected CRT call "+call);
                }
            }
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                var entry=transfer.entry();assertEquals(S-0x30,entry.rspBits());assertEquals(N,entry.nonvolatileBits());
                if(transfer.jumpSiteRva()==0x4223ae4L) {
                    events.add("crt-tail-header");assertEquals(GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,transfer.kind());assertEquals(EXIT_TARGET,transfer.targetBits());
                    var expected=initialGuard==0?regs(header,header.raxBits(),I+0x5c5cb18L,header.rdxBits(),header.r8Bits(),header.r9Bits(),header.xmm0()):
                        regs(header,Integer.toUnsignedLong(epoch),I+0x5c5cb18L,CRT_TLS,16,header.r9Bits(),header.xmm0());
                    assertEquals(expected,entry.volatileBits());assertEquals(I+0x3f5c0c8L,memory.readQword(entry.rspBits()));
                    return new GovernmentCrtBoundary185Api.NormalReturn(entry.volatileBits(),fault==0?0x9999L:memory.readQword(entry.rspBits()),entry.rspBits()+8,entry.nonvolatileBits());
                }
                events.add("crt-tail-footer");assertEquals(0x4223a7fL,transfer.jumpSiteRva());
                assertEquals(GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,transfer.kind());assertEquals(0x4223aecL,transfer.targetBits());
                assertEquals(footerExit,entry.volatileBits());assertEquals(I+0x3f5c174L,memory.readQword(entry.rspBits()));
                return new GovernmentCrtBoundary185Api.NormalReturn(entry.volatileBits(),memory.readQword(entry.rspBits()),entry.rspBits()+8,fault==1?rbx(999):entry.nonvolatileBits());
            }
        };
        GovernmentRoot178Api.NormalReturn execute() {
            return GovernmentRootCrtRetry210.execute(new GovernmentRoot178Api.Entry(I,S,initial,N),memory,outer,crt,crtBudget,allocation,allocationBudget);
        }
    }
    private static List<Write> initializationWrites() {
        return List.of(new Write(S-0x30,8,I+0x3f5c0c8L,0),new Write(S-0x38,8,N.rbxBits(),0),new Write(S-0x60,8,I+0x4223a9aL,0),
            new Write(I+0x5dc11c0L,4,0xffffffffL,0),new Write(I+0x5dc11d0L,4,0,0),new Write(I+0x5dc11d8L,8,0,0),new Write(I+0x5dc11e0L,8,0,0),
            new Write(S-0x30,8,I+0x3f5c0fcL,0),new Write(S-0x38,8,N.rbxBits(),0),new Write(S-0x60,8,I+0x4223bb3L,0),
            new Write(S-0x68,8,64,0),new Write(S-0x90,8,I+0x424fde4L,0),new Write(P,8,P,0),new Write(P+8,8,P,0),
            new Write(I+0x5dc11d8L,8,P,0),new Write(I+0x5dc11e8L,8,0,0),new Write(I+0x5dc11f0L,16,0,0),
            new Write(I+0x5dc1200L,8,7,0),new Write(I+0x5dc1208L,8,8,0),new Write(I+0x5dc11d0L,4,FLOAT_BITS,0),
            new Write(S-0x30,8,I+0x3f5c15aL,0),new Write(S,8,FRESH_RET,0),new Write(S-0x30,8,I+0x3f5c167L,0),
            new Write(S-0x60,8,I+0x4223f2dL,0),new Write(S-0x30,8,I+0x3f5c174L,0),new Write(S-0x38,8,N.rbxBits(),0),
            new Write(S-0x60,8,I+0x4223a3aL,0),new Write(I+0x542f090L,4,0,0),new Write(I+0x5dc11c0L,4,0,0),
            new Write(CRT_TLS+16,4,0,0),new Write(S-0x60,8,I+0x4223a7aL,0));
    }
    private static Map<Long,Integer> apply(Map<Long,Integer> initial,List<Write> literal) {
        Map<Long,Integer> expected=new HashMap<>(initial);
        for(Write w:literal)for(int k=0;k<w.width();k++)expected.put(w.address()+k,(int)((k<8?w.low():w.high())>>>((k%8)*8))&255);
        return expected;
    }

    @Test void wholeRootRunsRealHeaderRetryWrapperAndFooterWithEpochWrap() {
        Fixture f=new Fixture(0,-1,-1,-1);Map<Long,Integer> before=new HashMap<>(f.memory.bytes);
        var result=f.execute();
        assertEquals(List.of("outerGS","crt-enter-header","crt-budget-header","crt-tail-header","allocation-budget","allocation-IAT",
            "outer3714560","crt3EE8","crt-enter-footer","crtGS","crt-exit-footer","crt-tail-footer"),f.events);
        assertEquals(1,f.outerCalls);assertEquals(1,f.allocationCalls);assertEquals(4,f.crtCalls);
        assertEquals(new GovernmentRoot178Api.NormalReturn(regs(f.footerExit,I+0x5dc11d0L,f.footerExit.rcxBits(),f.footerExit.rdxBits(),f.footerExit.r8Bits(),f.footerExit.r9Bits(),f.footerExit.xmm0()),FRESH_RET,S+8,N),result);
        assertEquals(initializationWrites(),f.memory.writes);assertEquals(31,f.memory.writes.size());
        assertEquals(apply(before,initializationWrites()),f.memory.bytes);assertEquals(-1,f.memory.readDword(ROOT_TLS+16));
    }

    @Test void initializedRealHeaderUpdatesSelectedTlsAndWholeRootSkipsAllocation() {
        Fixture f=new Fixture(5,0,0x80000003,-1);Map<Long,Integer> before=new HashMap<>(f.memory.bytes);
        var result=f.execute();
        assertEquals(List.of("outerGS","crt-enter-header","crt-budget-header","crtGS","crt-tail-header"),f.events);
        assertEquals(0,f.outerCalls);assertEquals(0,f.allocationCalls);assertEquals(1,f.crtCalls);
        assertEquals(new GovernmentRoot178Api.NormalReturn(regs(f.header,I+0x5dc11d0L,I+0x5c5cb18L,CRT_TLS,16,f.header.r9Bits(),f.header.xmm0()),RET,S+8,N),result);
        List<Write> literal=List.of(new Write(S-0x30,8,I+0x3f5c0c8L,0),new Write(S-0x38,8,N.rbxBits(),0),
            new Write(S-0x60,8,I+0x4223a9aL,0),new Write(CRT_TLS+16,4,0x80000003L,0));
        assertEquals(literal,f.memory.writes);assertEquals(apply(before,literal),f.memory.bytes);
    }

    @Test void wholeCallerKeepsCrtConformanceFailuresAndExactBudgetException() {
        for(int mode=0;mode<3;mode++) {
            Fixture f=new Fixture(0,-1,-1,mode);
            if(mode==2)assertSame(f.exact,assertThrows(IllegalArgumentException.class,f::execute));
            else assertThrows(IllegalStateException.class,f::execute);
            if(mode==1) {
                assertEquals(initializationWrites(),f.memory.writes);assertEquals(1,f.allocationCalls);assertEquals(1,f.outerCalls);
                assertEquals(P,f.memory.readQword(P));assertEquals(0,f.memory.readDword(CRT_TLS+16));
            } else {
                assertEquals(initializationWrites().subList(0,mode==0?4:3),f.memory.writes);
                assertEquals(0,f.allocationCalls);assertEquals(0,f.outerCalls);assertFalse(f.memory.bytes.containsKey(P));
                assertFalse(f.memory.bytes.containsKey(I+0x5dc11d8L));assertEquals(mode==0?-1:0,f.memory.readDword(I+0x5dc11c0L));
            }
        }
    }

    /** New211 port-order boundary: explicit read observations, not a hardware concurrency claim. */
    @Test void headerSecondCmpObservesIndependentMemoryValueBeforeWaitDecision() {
        for(int scenario=0;scenario<2;scenario++) {
            final boolean waits=scenario==0;
            Ram m=new Ram();long guard=I+0x5dc11c0L;
            m.seed(S,8,RET,0);m.seed(guard,4,99,0);m.seed(GS+3*8,8,CRT_TLS,0);
            m.seed(CRT_TLS+16,4,17,0);m.seed(I+0x5c5cbc4L,4,3,0);m.seed(I+0x542f090L,4,0x80000003L,0);
            m.seed(I+0x43da500L,8,ENTER_TARGET,0);m.seed(I+0x43da4f0L,8,EXIT_TARGET,0);
            m.guardScriptAddress=guard;m.guardScript=waits?List.of(1,-1,0,0):List.of(-1,5);
            Map<Long,Integer> before=new HashMap<>(m.bytes);List<String> events=new ArrayList<>();
            VolatileBits entered=v(800,801),waited=v(900,901),initial=v(20,21);
            var ports=new GovernmentCrtBoundary185Api.Calls() {
                @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                    assertEquals(S-0x28,call.rspBits());assertEquals(rbx(guard),call.nonvolatileBits());
                    if(call.callSiteRva()==0x4223a94L) {
                        events.add("enter");assertEquals(GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,call.kind());
                        assertEquals(ENTER_TARGET,call.targetBits());assertEquals(I+0x4223a9aL,m.readQword(S-0x30));return entered;
                    }
                    assertTrue(waits,"initialized second observation must not call wait");events.add("wait");
                    assertEquals(0x4223aa9L,call.callSiteRva());assertEquals(GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,call.kind());
                    assertEquals(0x4223b30L,call.targetBits());assertEquals(100,call.volatileBits().rcxBits());
                    assertEquals(I+0x4223aaeL,m.readQword(S-0x30));return waited;
                }
                @Override public long readGsQword58() {assertFalse(waits,"second observation -1 must take wait, not initialized TLS");events.add("GS");return GS;}
                @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                    events.add("tail");assertEquals(0x4223ae4L,transfer.jumpSiteRva());
                    assertEquals(GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,transfer.kind());assertEquals(EXIT_TARGET,transfer.targetBits());
                    assertEquals(S,transfer.entry().rspBits());assertEquals(N,transfer.entry().nonvolatileBits());
                    return new GovernmentCrtBoundary185Api.NormalReturn(transfer.entry().volatileBits(),m.readQword(S),S+8,transfer.entry().nonvolatileBits());
                }
            };
            var result=GovernmentCrtBoundary185.execute3A84(new GovernmentCrtBoundary185Api.Entry(I,S,
                regs(initial,initial.raxBits(),guard,initial.rdxBits(),initial.r8Bits(),initial.r9Bits(),initial.xmm0()),N),
                org.xar.ck3.research.m4.Retry60NormalFullState284Calls.as185(m),ports,
                (site,value)->{events.add("step");assertEquals(0x4223a9aL,site);assertEquals(guard,value);});
            assertEquals(m.guardScript.size(),m.guardScriptIndex);
            assertEquals(waits?List.of("enter","step","wait","step","tail"):List.of("enter","step","GS","tail"),events);
            VolatileBits expected=waits?regs(waited,waited.raxBits(),I+0x5c5cb18L,waited.rdxBits(),waited.r8Bits(),waited.r9Bits(),waited.xmm0()):
                regs(entered,0x80000003L,I+0x5c5cb18L,CRT_TLS,16,entered.r9Bits(),entered.xmm0());
            assertEquals(new GovernmentCrtBoundary185Api.NormalReturn(expected,RET,S+8,N),result);
            List<Write> literal=waits?List.of(new Write(S-8,8,N.rbxBits(),0),new Write(S-0x30,8,I+0x4223a9aL,0),
                new Write(S-0x30,8,I+0x4223aaeL,0),new Write(guard,4,0xffffffffL,0)):
                List.of(new Write(S-8,8,N.rbxBits(),0),new Write(S-0x30,8,I+0x4223a9aL,0),new Write(CRT_TLS+16,4,0x80000003L,0));
            assertEquals(literal,m.writes);assertEquals(apply(before,literal),m.bytes);
        }
    }
}
