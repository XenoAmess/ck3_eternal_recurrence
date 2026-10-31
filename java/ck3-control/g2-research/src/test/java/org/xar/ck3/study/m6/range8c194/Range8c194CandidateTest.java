package org.xar.ck3.study.m6.range8c194;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.study.m6.element172.Element172Inputs;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.element190.RawMemory190.Access;

public final class Range8c194CandidateTest {
    static final long H=0x8000000000002000L,OLD=0xf000000000003000L,SECOND=0xf000000000004000L;
    static final long NEW=0x8000000000005000L,SRC=0xe000000000006000L,A=0xc000000000007000L,V=0xc000000000008000L;
    static final long A2=0xc000000000009000L,V2=0xc00000000000a000L,U=0xd00000000000b000L;
    static final long T8=0xf100000000001001L,T16=0xf100000000001002L,T162=0xf100000000001003L;
    static final Range8c194Inputs.Word16 O0=new Range8c194Inputs.Word16(0xa100000000000011L,0xa200000000001122L);
    static final Range8c194Inputs.Word16 O1=new Range8c194Inputs.Word16(0xa100000000000033L,0xa200000000003344L);
    static final Range8c194Inputs.Word16 B0=new Range8c194Inputs.Word16(0xb100000000000055L,0xb200000000005566L);
    static final Range8c194Inputs.Word16 B1=new Range8c194Inputs.Word16(0xb100000000000077L,0xb200000000007788L);
    static final Range8c194Inputs.Word16 S0=new Range8c194Inputs.Word16(0xc100000000000099L,0xc2000000000099aaL);
    static final Range8c194Inputs.Word16 S1=new Range8c194Inputs.Word16(0xc1000000000000bbL,0xc20000000000bbccL);
    record Block(String operation,long address,Range8c194Inputs.Word16 value) { }
    record Port(String kind,List<Long> arguments) { }
    static final class Memory extends RawMemory190 implements Range8c194Inputs.Memory {
        final List<Object> events=new ArrayList<>();
        Runnable afterFirstBlockWrite=()->{};
        private boolean first=true;
        @Override protected void observed(Access access) { events.add(access); }
        Range8c194Inputs.Word16 peek16(long address) { return new Range8c194Inputs.Word16(peek64(address),peek64(address+8)); }
        void put16(long address,Range8c194Inputs.Word16 word) { put64(address,word.lowRaw64());put64(address+8,word.highRaw64()); }
        @Override public Range8c194Inputs.Word16 read16(long address) { var word=peek16(address);events.add(new Block("read16",address,word));return word; }
        @Override public void write16(long address,Range8c194Inputs.Word16 word) {
            events.add(new Block("write16",address,word));put16(address,word);
            if(first) { first=false;afterFirstBlockWrite.run(); }
        }
    }
    static class Calls implements Element172WithKnownRange194.Calls {
        final List<Port> events=new ArrayList<>();
        Runnable allocate=()->{},release=()->{},copy4=()->{};
        long result=NEW;
        @Override public long virtual8(long target,long receiver,long bytes,long align,long end) {
            events.add(new Port("virtual8",List.of(target,receiver,bytes,align,end)));allocate.run();return result;
        }
        @Override public void virtual16(long target,long receiver,long old,long align,long r9) {
            events.add(new Port("virtual16",List.of(target,receiver,old,align,r9)));release.run();
        }
        @Override public void direct8f8550(long rcx,long rdx,long r8,long r9) { events.add(new Port("direct8f8550",List.of(rcx,rdx,r8,r9))); }
        @Override public void copy4_add0d0(long header,long zero,long begin,long end) { events.add(new Port("copy4",List.of(header,zero,begin,end)));copy4.run(); }
    }
    private static int cases,checks;
    private static void eq(Object expected,Object actual) { ++checks;if(!expected.equals(actual))throw new IllegalStateException("expected="+expected+" actual="+actual); }
    private static void header(Memory memory,long base,int capacity,int size,long allocator) {
        memory.put64(H,base);memory.put32(H+8,capacity);memory.put32(H+0xc,size);memory.put64(H+0x10,allocator);
    }
    private static void allocator(Memory memory,long receiver,long table,long allocateTarget,long releaseTarget) {
        memory.put64(receiver,table);memory.put64(table+8,allocateTarget);memory.put64(table+0x10,releaseTarget);
    }
    private static void empty() {
        var memory=new Memory();var calls=new Calls();Range8c194Candidate.apply(new Range8c194Inputs.Input(0,0,SRC,SRC),memory,calls);
        eq(List.of(),memory.events);eq(List.of(),calls.events);++cases;
    }
    private static void withinFresh() {
        var memory=new Memory();var calls=new Calls();header(memory,OLD,3,1,A);memory.put16(OLD,O0);memory.put16(SRC,S0);
        memory.afterFirstBlockWrite=()->{memory.put64(H,SECOND);memory.put32(H+0xc,2);};
        Range8c194Candidate.apply(new Range8c194Inputs.Input(H,0,SRC,SRC+16),memory,calls);
        eq(O0,memory.peek16(OLD));eq(S0,memory.peek16(OLD+16));eq(SECOND,memory.peek64(H));eq(3,memory.peek32(H+0xc));
        eq(List.of(new Port("direct8f8550",List.of(SECOND,SECOND+32,SECOND+48,SECOND))),calls.events);
        eq(List.of(new Access("r32",H+0xc,4,1),new Access("r32",H+8,4,3),new Access("r64",H,8,OLD),
                new Block("read16",SRC,S0),new Block("write16",OLD+16,S0),new Access("r32",H+0xc,4,2),
                new Access("r64",H,8,SECOND),new Access("w32",H+0xc,4,3)),memory.events);++cases;
    }
    private static void growthFresh() {
        var memory=new Memory();var calls=new Calls();header(memory,OLD,2,2,A);allocator(memory,A,V,T8,T16);allocator(memory,A2,V2,T8,T162);
        memory.put16(OLD,O0);memory.put16(OLD+16,O1);memory.put16(SECOND,B0);memory.put16(SECOND+16,B1);memory.put16(SRC,S0);memory.put16(SRC+16,S1);
        calls.allocate=()->{memory.put64(H,SECOND);memory.put64(H+0x10,A2);memory.put32(H+8,99);};
        calls.release=()->{memory.put64(H,0xdeadL);memory.put32(H+8,-1);memory.put32(H+0xc,-1);};
        Range8c194Candidate.apply(new Range8c194Inputs.Input(H,1,SRC,SRC+32),memory,calls);
        eq(List.of(new Port("virtual8",List.of(T8,A,64L,8L,SRC+32)),new Port("virtual16",List.of(T162,A2,SECOND,8L,SECOND))),calls.events);
        eq(List.of(B0,S0,S1,B1),List.of(memory.peek16(NEW),memory.peek16(NEW+16),memory.peek16(NEW+32),memory.peek16(NEW+48)));
        eq(NEW,memory.peek64(H));eq(4,memory.peek32(H+8));eq(4,memory.peek32(H+0xc));eq(A2,memory.peek64(H+0x10));eq(O0,memory.peek16(OLD));eq(O1,memory.peek16(OLD+16));++cases;
    }
    private static void floatSentinel(int size,int capacity,long expectedBytes) {
        var memory=new Memory();var calls=new Calls();header(memory,OLD,capacity,size,A);allocator(memory,A,V,T8,T16);
        RuntimeException sentinel=new RuntimeException("allocation boundary");calls.allocate=()->{throw sentinel;};
        try { Range8c194Candidate.apply(new Range8c194Inputs.Input(H,0,SRC,SRC+16),memory,calls);throw new IllegalStateException("missing allocation sentinel"); }
        catch(RuntimeException failure) { eq(sentinel,failure); }
        eq(List.of(new Port("virtual8",List.of(T8,A,expectedBytes,8L,SRC+16))),calls.events);
        eq(OLD,memory.peek64(H));eq(size,memory.peek32(H+0xc));++cases;
    }
    private static void actualUpper() {
        var memory=new Memory();var calls=new Calls();long image=0x7fffffffff000000L,receiver=image+0x54de260L;
        memory.fill(H,0x80,0xcc);memory.fill(U,0x80,0xcc);memory.put32(U+8,5);memory.put64(U+0x10,SRC);memory.put32(U+0x1c,1);
        memory.put64(U+0x28,SECOND);memory.put32(U+0x34,0);memory.put32(U+0x40,1);memory.put8(U+0x44,2);memory.put16(SRC,S0);
        for(int n=0;n<4;++n)memory.put8(H+0x45+n,0xc5+n);allocator(memory,receiver,V,T8,T16);
        calls.copy4=()->{memory.put32(U+0x40,Integer.MIN_VALUE);memory.put8(U+0x44,0xe1);};
        long result=Element172WithKnownRange194.assign(new Element172Inputs.Input(H,U,image),memory,calls);
        eq(H,result);eq(List.of(new Port("virtual8",List.of(T8,receiver,16L,8L,SRC+16)),new Port("virtual16",List.of(T16,receiver,0L,8L,0L)),
                new Port("copy4",List.of(H+0x28,0L,SECOND,SECOND))),calls.events);
        eq(S0,memory.peek16(NEW));eq(NEW,memory.peek64(H+0x10));eq(1,memory.peek32(H+0x18));eq(1,memory.peek32(H+0x1c));eq(receiver,memory.peek64(H+0x20));
        eq(5,memory.peek32(H+8));eq(Integer.MIN_VALUE,memory.peek32(H+0x40));eq(0xe1,memory.peek8(H+0x44));
        eq(List.of(0xc5,0xc6,0xc7,0xc8),List.of(memory.peek8(H+0x45),memory.peek8(H+0x46),memory.peek8(H+0x47),memory.peek8(H+0x48)));++cases;
    }
    public static void main(String[] arguments) {
        empty();withinFresh();growthFresh();floatSentinel(-2,Integer.MIN_VALUE,0x0000000ffffffff0L);
        floatSentinel(0x55555555,0x55555555,0x0000000555555560L);actualUpper();
        System.out.println("RANGE8C194_DATA_CASES="+cases+" CHECKS="+checks);
    }
}
