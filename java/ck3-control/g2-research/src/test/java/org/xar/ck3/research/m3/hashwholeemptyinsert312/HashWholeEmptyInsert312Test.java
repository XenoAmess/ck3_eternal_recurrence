package org.xar.ck3.research.m3.hashwholeemptyinsert312;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.hashwholefp309.HashWholeFp309Api;
import org.xar.ck3.research.m3.hashwholefp310.HashWholeFp310;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/**
 * Two finite owned software cases for actual whole310 with real305 FP continuation.
 * Expected values come from immutable independent ORACLE-LITERALBOOK312, sealed
 * before305/309/310 implementation bodies. Unknown855F00 is explicit foreign DATA.
 */
public final class HashWholeEmptyInsert312Test {
    private static final long IMAGE=0x9000000000000000L, MAP=0x2000L, BUCKETS=0x3000L;
    private static final long DESC=0x6000L, S=0x8008L, OUT_A=0x5000L;
    private static final long ENTRY_RET=0x0123456789abcdefL;
    private static final long FOREIGN_RET=0xfedcba9876543210L, ORIGIN=0x13579bdfL;
    private static final long RAW_R8=0x0123456780000002L;
    private static final long BODY_SP=S-0xa8L, CHILD_SP=S-0xb0L;
    private static final long CALL_SITE=0xc39d27L, CALL_RET=IMAGE+0xc39d2cL;
    private static final NonvolatileBits ENTRY_N=new NonvolatileBits(
            0x1111111111111111L,0x2222222222222222L,0x1122334455667788L,
            0x4444444444444444L,0x5555555555555555L,0x6666666666666666L,
            0x7777777777777777L,0x8888888888888888L,
            new Bits128(0x6162636465666768L,0x7172737475767778L));

    private HashWholeEmptyInsert312Test() { }

    public static void main(String[] args) {
        foreignCountAndFullPostState();
        outputAliasesSavedRbxAndFreshHomes();
        System.out.println("PASS HashWholeEmptyInsert312Test 2 finite empty-bucket cases");
    }

    public static void foreignCountAndFullPostState() { runCase(false); }
    public static void outputAliasesSavedRbxAndFreshHomes() { runCase(true); }

    private static final class Budget implements GovernmentCrtBoundary185Api.LoopBudget {
        int calls;
        @Override public void beforeStep(long site,long address) {
            calls++;
            throw new AssertionError("Unexpected source loop admission at "+Long.toHexString(site));
        }
    }

    private static final class Fixture {
        final boolean alias;
        final long out;
        final BoundedRam ram=new BoundedRam();
        final Budget budget=new Budget();
        final QueueFp604Api.Mxcsr incomingFp,foreignFp;
        final VolatileBits foreignV;
        final HashWholeFp309Api.Input input;
        final Map<Long,Byte> expectedRam;
        int callbackCount;
        Fixture(boolean alias) {
            this.alias=alias;
            out=alias?S+0x10L:OUT_A;
            incomingFp=alias?new QueueFp604Api.Mxcsr(0x20,0x20):new QueueFp604Api.Mxcsr(0,0);
            foreignFp=alias?new QueueFp604Api.Mxcsr(0x20,0x31):new QueueFp604Api.Mxcsr(0x8000,0xc000);
            foreignV=literalVolatile(alias?0xd1L:0xc1L,alias?0x301L:0x201L);
            ram.fill(MAP,32,0xcc);ram.fill(BUCKETS,40,0xcc);ram.fill(DESC,32,0xdd);
            ram.fill(S-0x200L,0x240,0x99);ram.fill(OUT_A,16,0xee);
            ram.poke(MAP+8,8,BUCKETS);ram.poke(MAP+0x18,1,7);
            ram.poke(BUCKETS+4,1,0);ram.poke(S,8,ENTRY_RET);
            ram.poke(MAP+0x14,4,alias?8:4);ram.poke(MAP+0x10,4,alias?3:1);
            ram.poke(MAP+0x1c,4,alias?0x3f800000L:0x3f000000L);
            var v=new VolatileBits(0xa1L,MAP,out,RAW_R8,DESC,0xa6L,0xa7L,
                    bits(0x101),bits(0x103),bits(0x105),bits(0x107),bits(0x109),bits(0x10b));
            var e=new GovernmentCrtBoundary185Api.Entry(IMAGE,S,v,ENTRY_N);
            input=new HashWholeFp309Api.Input(
                    new QueueFp604Api.Input(new FullCopy437Api.Input(e,alias,budget),incomingFp),ORIGIN);
            expectedRam=new HashMap<>(ram.allOwnedBytes());
            literalFinalPatches(this,expectedRam);
        }
    }

    private static Bits128 bits(long low) { return new Bits128(low,low+1L); }
    private static VolatileBits literalVolatile(long first,long xmmFirst) {
        return new VolatileBits(first,first+1,first+2,first+3,first+4,first+5,first+6,
                bits(xmmFirst),bits(xmmFirst+2),bits(xmmFirst+4),
                bits(xmmFirst+6),bits(xmmFirst+8),bits(xmmFirst+10));
    }

    private static void assertOfferedFrame(Fixture f,HashWholeFp309Api.CallFrame frame,
                                          FullCopy437Api.Memory memory) {
        same(memory,f.ram,"same RAM");eq(frame.ownerInput(),f.input,"whole input value");
        same(frame.budget(),f.budget,"budget identity");same(frame.preMxcsr(),f.incomingFp,"exact gate FP identity");
        eq(frame.directionFlagSet(),f.alias,"offered DF");eq(frame.originCallSiteRva(),ORIGIN,"origin");
        eq(frame.instructionLength(),5,"CALL length");eq(frame.returnRipBits(),CALL_RET,"CALL return");
        var call=frame.original();
        eq(call.callSiteRva(),CALL_SITE,"CALL site");
        eq(call.kind(),GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,"CALL kind");
        eq(call.targetBits(),0x855f00L,"CALL target");eq(call.rspBits(),BODY_SP,"preCALL SP");
        var offeredV=new VolatileBits(0L,BUCKETS+8L,DESC,RAW_R8,0L,0xa6L,0xa7L,
                new Bits128(f.alias?0x41000000L:0x40800000L,0L),
                new Bits128(0x3f000000L,0L),bits(0x105),bits(0x107),bits(0x109),bits(0x10b));
        var offeredN=new NonvolatileBits(BUCKETS,S-0x38L,0x1122334455667701L,DESC,
                0x5555555555555555L,0xffffffff80000002L,MAP,f.out,ENTRY_N.xmm6());
        eq(call.volatileBits(),offeredV,"full offered V");eq(call.nonvolatileBits(),offeredN,"full offered N");
        var child=frame.childEntry();
        eq(child.imageBaseBits(),IMAGE,"child image");eq(child.rspBits(),CHILD_SP,"child SP");
        eq(child.volatileBits(),offeredV,"full child V");eq(child.nonvolatileBits(),offeredN,"full child N");
        eq(f.ram.peek(CHILD_SP,8),CALL_RET,"actual owned CALL push");
    }

    /**
     * Mechanical method adopted from complete-source model R1 without executable edits.
     * Owner fixture and expectations were visible and guided; no independent-oracle credit.
     * Only explicit foreign Normal DATA is supplied; no855F00 algorithm is implemented.
     */
    private static HashWholeFp309Api.Result foreignOffer(Fixture f,
            HashWholeFp309Api.CallFrame frame,FullCopy437Api.Memory memory) {
        f.callbackCount++;
        if (f.callbackCount != 1) throw new AssertionError("Unexpected callback count");
        assertOfferedFrame(f, frame, memory);
        f.ram.observation("CALL");
        if (f.alias) {
            memory.writeDword(MAP + 0x10L, 0x7fffffff);
            memory.writeQword(BUCKETS + 8L, 0x8877665544332211L);
            memory.writeQword(S - 8L, 0xe2L);
            memory.writeQword(S - 0x38L, 0xefL);
            memory.writeQword(S, FOREIGN_RET);
        } else {
            memory.writeDword(MAP + 0x10L, 0xffffffff);
            memory.writeQword(BUCKETS + 8L, 0x1122334455667788L);
        }
        var normalReturn = new GovernmentCrtBoundary185Api.NormalReturn(
                f.foreignV, frame.returnRipBits(), frame.original().rspBits(),
                frame.original().nonvolatileBits());
        var callResult = new FullCopy437Api.CallResult(normalReturn, !f.alias);
        var outcome = new QueueFp604Api.Normal(callResult, f.foreignFp);
        f.ram.observation("END");
        return new HashWholeFp309Api.Forwarded(outcome);
    }

    private static void runCase(boolean alias) {
        Fixture f=new Fixture(alias);
        var result=HashWholeFp310.execute(f.input,f.ram,(frame,memory)->foreignOffer(f,frame,memory));
        if(!(result instanceof HashWholeFp309Api.Forwarded forwarded)
                ||!(forwarded.actual() instanceof QueueFp604Api.Normal normal))
            throw new AssertionError("Whole empty-bucket case must reach real RET Normal");
        var nr=normal.base().normalReturn();
        var fv=f.foreignV;
        var expectedV=new VolatileBits(f.out,fv.rcxBits(),fv.rdxBits(),fv.r8Bits(),fv.r9Bits(),
                fv.r10Bits(),fv.r11Bits(),fv.xmm0(),fv.xmm1(),fv.xmm2(),fv.xmm3(),fv.xmm4(),fv.xmm5());
        var expectedN=alias?new NonvolatileBits(BUCKETS,0xe2L,ENTRY_N.rsiBits(),ENTRY_N.rdiBits(),
                ENTRY_N.r12Bits(),ENTRY_N.r13Bits(),ENTRY_N.r14Bits(),0xefL,ENTRY_N.xmm6()):ENTRY_N;
        eq(nr.volatileBits(),expectedV,"final full V");eq(nr.nonvolatileBits(),expectedN,"final fresh full N");
        eq(nr.returnRipBits(),alias?FOREIGN_RET:ENTRY_RET,"fresh RET");
        eq(nr.callerRspBits(),S+8L,"final SP");eq(normal.base().postDirectionFlagSet(),!alias,"foreign DF");
        same(normal.postMxcsr(),f.foreignFp,"foreign partial MXCSR object");
        eq(f.callbackCount,1,"only explicit855F00");eq(f.budget.calls,0,"no budget admission");
        eq(f.ram.eventSnapshot(),literalEvents(f),"exact widths addresses values and order");
        eq(f.ram.allOwnedBytes(),f.expectedRam,"all owned bytes padding and sentinels");
    }

    private static void literalFinalPatches(Fixture f,Map<Long,Byte> expected) {
        patch(expected,S+0x10L,8,0x1111111111111111L);
        patch(expected,S-8L,8,0x2222222222222222L);
        patch(expected,S-0x10L,8,0x1122334455667788L);
        patch(expected,S-0x18L,8,0x4444444444444444L);
        patch(expected,S-0x20L,8,0x5555555555555555L);
        patch(expected,S-0x28L,8,0x6666666666666666L);
        patch(expected,S-0x30L,8,0x7777777777777777L);
        patch(expected,S-0x38L,8,0x8888888888888888L);
        patch(expected,BUCKETS,4,0x80000002L);patch(expected,BUCKETS+4,1,1L);
        patch(expected,CHILD_SP,8,CALL_RET);
        patch(expected,BUCKETS+8,8,f.alias?0x8877665544332211L:0x1122334455667788L);
        if(f.alias) {
            patch(expected,S-8L,8,0xe2L);patch(expected,S-0x38L,8,0xefL);patch(expected,S,8,FOREIGN_RET);
        }
        patch(expected,MAP+0x10L,4,f.alias?0x80000000L:0L);
        patch(expected,f.out,8,BUCKETS);patch(expected,f.out+8L,1,1L);
    }

    private static void patch(Map<Long,Byte> bytes,long address,int width,long value) {
        for(int i=0;i<width;i++) {
            if(!bytes.containsKey(address+i))throw new AssertionError("Expected patch outside owned RAM");
            bytes.put(address+i,(byte)(value>>>(8*i)));
        }
    }

    private record MemoryOp(String kind,long address,Object value) { }
    private static MemoryOp op(String kind,long address,long value) { return new MemoryOp(kind,address,value); }
    private static MemoryOp mark(String kind) { return new MemoryOp(kind,CALL_SITE,null); }
    private static List<MemoryOp> literalEvents(Fixture f) {
        List<MemoryOp> e=new ArrayList<>(List.of(
            op("W64",S+0x10L,0x1111111111111111L),op("W64",S-8L,0x2222222222222222L),
            op("W64",S-0x10L,0x1122334455667788L),op("W64",S-0x18L,0x4444444444444444L),
            op("W64",S-0x20L,0x5555555555555555L),op("W64",S-0x28L,0x6666666666666666L),
            op("W64",S-0x30L,0x7777777777777777L),op("W64",S-0x38L,0x8888888888888888L),
            op("R32",MAP+0x14L,f.alias?8L:4L),op("R64",MAP+8L,BUCKETS),
            op("R8",BUCKETS+4L,0L),op("R8",MAP+0x18L,7L),op("R32",MAP+0x10L,f.alias?3L:1L),
            op("R32",MAP+0x1cL,f.alias?0x3f800000L:0x3f000000L),op("R8",BUCKETS+4L,0L),
            op("W32",BUCKETS,0x80000002L),op("W8",BUCKETS+4L,1L),op("W64",CHILD_SP,CALL_RET),
            mark("CALL"),op("W32",MAP+0x10L,f.alias?0x7fffffffL:0xffffffffL),
            op("W64",BUCKETS+8L,f.alias?0x8877665544332211L:0x1122334455667788L)));
        if(f.alias) {
            e.add(op("W64",S-8L,0xe2L));e.add(op("W64",S-0x38L,0xefL));e.add(op("W64",S,FOREIGN_RET));
        }
        e.addAll(List.of(mark("END"),op("R32",MAP+0x10L,f.alias?0x7fffffffL:0xffffffffL),
            op("W32",MAP+0x10L,f.alias?0x80000000L:0L),op("W64",f.out,BUCKETS),op("W8",f.out+8L,1L),
            op("R64",S+0x10L,f.alias?BUCKETS:0x1111111111111111L),
            op("R64",S-0x38L,f.alias?0xefL:0x8888888888888888L),op("R64",S-0x30L,0x7777777777777777L),
            op("R64",S-0x28L,0x6666666666666666L),op("R64",S-0x20L,0x5555555555555555L),
            op("R64",S-0x18L,0x4444444444444444L),op("R64",S-0x10L,0x1122334455667788L),
            op("R64",S-8L,f.alias?0xe2L:0x2222222222222222L),op("R64",S,f.alias?FOREIGN_RET:ENTRY_RET)));
        return List.copyOf(e);
    }

    private static void same(Object actual,Object expected,String what) {
        if(actual!=expected)throw new AssertionError(what+" identity");
    }
    private static void eq(Object actual,Object expected,String what) {
        if(!Objects.equals(actual,expected))throw new AssertionError(what+": expected "+expected+", actual "+actual);
    }

    private static final class BoundedRam implements FullCopy437Api.Memory {
        private static final int MAX_BYTES=4096, MAX_EVENTS=512;
        private final Map<Long,Byte> owned=new HashMap<>();
        private final List<MemoryOp> events=new ArrayList<>();
        void fill(long first,int length,int value) {
            if(length<0||length>MAX_BYTES)throw new IllegalArgumentException("Invalid finite RAM region");
            for(int i=0;i<length;i++) {
                long address=first+i;
                if(!owned.containsKey(address)&&owned.size()==MAX_BYTES)throw new IllegalArgumentException("RAM bound");
                owned.put(address,(byte)value);
            }
        }
        private void checkInitialized(long address,int length) {
            if(length<1||length>32)throw new IllegalArgumentException("Unsupported width");
            for(int i=0;i<length;i++)if(!owned.containsKey(address+i))
                throw new AssertionError("Uninitialized owned RAM at "+Long.toUnsignedString(address+i,16));
        }
        long peek(long address,int width) {
            if(width<1||width>8)throw new IllegalArgumentException("Scalar width");
            checkInitialized(address,width);long value=0;
            for(int i=0;i<width;i++)value|=(long)Byte.toUnsignedInt(owned.get(address+i))<<(8*i);
            return value;
        }
        void poke(long address,int width,long value) {
            if(width<1||width>8)throw new IllegalArgumentException("Scalar width");
            checkInitialized(address,width);
            for(int i=0;i<width;i++)owned.put(address+i,(byte)(value>>>(8*i)));
        }
        private void record(String kind,long address,Object value) {
            if(events.size()==MAX_EVENTS)throw new AssertionError("Finite event bound");
            events.add(new MemoryOp(kind,address,value));
        }
        void observation(String kind) {
            if(!kind.equals("CALL")&&!kind.equals("END"))throw new IllegalArgumentException("Observation marker");
            record(kind,CALL_SITE,null);
        }
        private long read(String kind,long address,int width) {
            long value=peek(address,width);record(kind,address,value);return value;
        }
        private void write(String kind,long address,int width,long value) {
            poke(address,width,value);record(kind,address,width==8?value:value&((1L<<(width*8))-1L));
        }
        @Override public int readUnsignedByte(long a){return (int)read("R8",a,1);}
        @Override public int readUnsignedWord(long a){return (int)read("R16",a,2);}
        @Override public int readDword(long a){return (int)read("R32",a,4);}
        @Override public long readQword(long a){return read("R64",a,8);}
        @Override public void writeByte(long a,int v){write("W8",a,1,Integer.toUnsignedLong(v));}
        @Override public void writeWord(long a,int v){write("W16",a,2,Integer.toUnsignedLong(v));}
        @Override public void writeDword(long a,int v){write("W32",a,4,Integer.toUnsignedLong(v));}
        @Override public void writeQword(long a,long v){write("W64",a,8,v);}
        private Bits128 peek128(long a){checkInitialized(a,16);return new Bits128(peek(a,8),peek(a+8,8));}
        @Override public Bits128 read128(long a){var v=peek128(a);record("R128",a,v);return v;}
        private void put128(long a,Bits128 v){Objects.requireNonNull(v);checkInitialized(a,16);poke(a,8,v.lowBits());poke(a+8,8,v.highBits());}
        @Override public void write128(long a,Bits128 v){put128(a,v);record("W128",a,v);}
        @Override public void write128NonTemporal(long a,Bits128 v){put128(a,v);record("WN128",a,v);}
        @Override public FullCopy437Api.Bits256 read256(long a) {
            checkInitialized(a,32);var v=new FullCopy437Api.Bits256(peek128(a),peek128(a+16));record("R256",a,v);return v;
        }
        private void put256(long a,FullCopy437Api.Bits256 v){Objects.requireNonNull(v);checkInitialized(a,32);put128(a,v.low());put128(a+16,v.high());}
        @Override public void write256(long a,FullCopy437Api.Bits256 v){put256(a,v);record("W256",a,v);}
        @Override public void write256NonTemporal(long a,FullCopy437Api.Bits256 v){put256(a,v);record("WN256",a,v);}
        @Override public int lockedXaddDword(long a,int addend){throw new AssertionError("No atomic instruction in these two cases");}
        @Override public void sfence(){record("SFENCE",0L,null);}
        List<MemoryOp> eventSnapshot(){return List.copyOf(events);}
        Map<Long,Byte> allOwnedBytes(){return Map.copyOf(owned);}
    }
}
