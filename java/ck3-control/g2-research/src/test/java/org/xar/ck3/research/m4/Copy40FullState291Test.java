package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Source literals, not an actual Rotate/Native invocation. Existing byte-storage algorithm is reused. */
final class Copy40FullState291Test {
    static final long I=0x180000000L,S=0x90000L,RIP=0x7fff00112233L;
    record Touch(String op,long address) { }
    static final class Traced implements GovernmentCrtBoundary185Api.Memory {
        final Gate47Fixture273.Memory m=new Gate47Fixture273.Memory();
        final List<Touch> events=new ArrayList<>();
        @Override public int readUnsignedByte(long p){events.add(new Touch("R1",p));return m.readUnsignedByte(p);}
        @Override public int readDword(long p){events.add(new Touch("R4",p));return m.readDword(p);}
        @Override public long readQword(long p){events.add(new Touch("R8",p));return m.readQword(p);}
        @Override public Bits128 read128(long p){events.add(new Touch("R16",p));return m.read128(p);}
        @Override public void writeByte(long p,int x){events.add(new Touch("W1",p));m.writeByte(p,x);}
        @Override public void writeDword(long p,int x){events.add(new Touch("W4",p));m.writeDword(p,x);}
        @Override public void writeQword(long p,long x){events.add(new Touch("W8",p));m.writeQword(p,x);}
        @Override public void write128(long p,Bits128 x){events.add(new Touch("W16",p));m.write128(p,x);}
        @Override public int lockedXaddDword(long p,int x){throw new AssertionError("unused atomic");}
    }
    static VolatileBits input(long seed,long rax,long source,long end,long destination) {
        var v=v(seed,rax,source,end);
        return new VolatileBits(rax,source,end,destination,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static VolatileBits post(VolatileBits v,long source,long destination,Bits128 x0,Bits128 x1) {
        return new VolatileBits(destination,source,v.rdxBits(),destination,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                x0,x1,v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static List<Touch> row(long source,long destination) {
        return List.of(new Touch("R16",source),new Touch("W16",destination),new Touch("R16",source+16),
                new Touch("W16",destination+16),new Touch("R8",source+32),new Touch("W8",destination+32));
    }

    @Test void emptyAndTwoUnalignedRowsPreserveFullPayloadAndRepresentedState() {
        var empty=new Traced();empty.m.put(S,RIP);var nv=n(700);var in=input(100,-1,0x123,0x123,0x8000000000002222L);
        var out=Copy40FullState291.execute(new Entry(I,S,in,nv),empty,(site,guard)->{throw new AssertionError("empty budget");});
        assertEquals(new NormalReturn(post(in,0x123,0x8000000000002222L,in.xmm0(),in.xmm1()),RIP,S+8,nv),out);
        assertEquals(List.of(new Touch("R8",S)),empty.events);assertTrue(empty.m.writes.isEmpty());
        long source=0x2003,dest=0x4005;var m=new Traced();m.m.put(S,RIP);
        for(int i=0;i<10;i++)m.m.put(source+8L*i,0x1100000000000000L+i);
        m.m.put(dest-8,0x9876);m.m.put(dest+80,0x5432);var expected=new HashMap<>(m.m.snapshot());
        var vin=input(200,0x1234,source,source+80,dest);var headers=new ArrayList<Long>();
        var copied=Copy40FullState291.execute(new Entry(I,S,vin,nv),m,(site,guard)->{assertEquals(0xF0ABA0L,site);headers.add(guard);});
        assertEquals(List.of(source,source+40),headers);
        assertEquals(new NormalReturn(post(vin,source+80,dest+80,new Bits128(0x1100000000000009L,0),new Bits128(0x1100000000000007L,0x1100000000000008L)),RIP,S+8,nv),copied);
        for(int i=0;i<10;i++)qword(expected,dest+8L*i,0x1100000000000000L+i);
        assertEquals(expected,m.m.snapshot());var trace=new ArrayList<>(row(source,dest));trace.addAll(row(source+40,dest+40));trace.add(new Touch("R8",S));assertEquals(trace,m.events);
        assertEquals(10,m.m.writes.size());for(int i=0;i<10;i++)assertEquals(new Write(dest+8L*i,8,0x1100000000000000L+i),m.m.writes.get(i));
    }

    @Test void overlappingDestinationConsumesFreshInterleavedReadsNotMemmoveSnapshot() {
        long p=0x2000,A=0x1111111111111111L,B=0x2222222222222222L,C=0x3333333333333333L,D=0x4444444444444444L,E=0x5555555555555555L;
        var m=new Traced();m.m.put(S,RIP);long[] before={A,B,C,D,E};for(int i=0;i<before.length;i++)m.m.put(p+8L*i,before[i]);
        var expected=new HashMap<>(m.m.snapshot());long[] after={A,A,B,B,D,D};for(int i=0;i<after.length;i++)qword(expected,p+8L*i,after[i]);
        var in=input(300,0x999,p,p+40,p+8);var nv=n(800);
        var out=Copy40FullState291.execute(new Entry(I,S,in,nv),m,(site,guard)->{assertEquals(p,guard);});
        assertEquals(new NormalReturn(post(in,p+40,p+48,new Bits128(D,0),new Bits128(B,D)),RIP,S+8,nv),out);
        assertEquals(expected,m.m.snapshot());var events=new ArrayList<>(row(p,p+8));events.add(new Touch("R8",S));assertEquals(events,m.events);
        assertEquals(List.of(new Write(p+8,8,A),new Write(p+16,8,B),new Write(p+24,8,B),new Write(p+32,8,D),new Write(p+40,8,D)),m.m.writes);
        assertEquals(List.of(p,p+8,p+16,p+24,p+32,S),m.m.qwordReads);
    }

    @Test void destinationMayChangeFreshReturnSlotAndIdentityCopyStillChangesXmm() {
        long source=0x2000;var nv=n(600);
        for(boolean self:new boolean[]{false,true}) {
            long dest=self?source:S;var m=new Traced();m.m.put(S,RIP);for(int i=0;i<5;i++)m.m.put(source+8L*i,0x100L+i);
            var expected=new HashMap<>(m.m.snapshot());for(int i=0;i<5;i++)qword(expected,dest+8L*i,0x100L+i);
            var in=input(200,0x987,source,source+40,dest);
            var out=Copy40FullState291.execute(new Entry(I,S,in,nv),m,(site,guard)->{});
            assertEquals(new NormalReturn(post(in,source+40,dest+40,new Bits128(0x104,0),new Bits128(0x102,0x103)),self?RIP:0x100,S+8,nv),out);
            assertEquals(expected,m.m.snapshot());assertEquals(5,m.m.writes.size());
            var events=new ArrayList<>(row(source,dest));events.add(new Touch("R8",S));assertEquals(events,m.events);
        }
    }

    @Test void malformedEndpointBudgetAndMissingSecondLoadPreserveExactWritePrefixes() {
        long source=0x2000,dest=0x4000;var nv=n(600);var in=input(200,7,source,source+41,dest);var m=new Traced();m.m.put(S,RIP);
        for(int i=0;i<5;i++)m.m.put(source+8L*i,0x200L+i);var expected=new HashMap<>(m.m.snapshot());for(int i=0;i<5;i++)qword(expected,dest+8L*i,0x200L+i);
        var headers=new ArrayList<Long>();var stop=new IllegalArgumentException("bounded rows");
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->Copy40FullState291.execute(new Entry(I,S,in,nv),m,(site,guard)->{headers.add(guard);if(headers.size()==2)throw stop;})));
        assertEquals(List.of(source,source+40),headers);assertEquals(row(source,dest),m.events);assertEquals(expected,m.m.snapshot());assertEquals(5,m.m.writes.size());
        var missing=new Traced();missing.m.put(S,RIP);missing.m.put(source,0x123);missing.m.put(source+8,0x456);var prefix=new HashMap<>(missing.m.snapshot());qword(prefix,dest,0x123);qword(prefix,dest+8,0x456);
        assertThrows(UnsupportedOperationException.class,()->Copy40FullState291.execute(new Entry(I,S,input(10,1,source,source+40,dest),nv),missing,(site,guard)->{}));
        assertEquals(List.of(new Touch("R16",source),new Touch("W16",dest),new Touch("R16",source+16)),missing.events);
        assertEquals(List.of(new Write(dest,8,0x123),new Write(dest+8,8,0x456)),missing.m.writes);assertEquals(prefix,missing.m.snapshot());
    }
}
