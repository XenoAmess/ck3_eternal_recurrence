package org.xar.ck3.research.m4;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import org.xar.ck3.research.m1.GovernmentResizeBase203;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Source-derived owner literals; owner reviewed production. No Game/OS/native oracle. */
final class Gate47FullState273Test {
    private static final long I=0x140000000L, S=0x10000L, RET=0x778899aabbccdd00L;

    @Test void widthBranchesPreserveCompleteStateAndByteMap() {
        long[][] cases={{0,0,0},{0x100000000L,0x7654321000000000L,0},
                {0x100000000L,0x7654321080000000L,1},{-1,-1,1}};
        for(long[] row:cases) {
            Memory m=new Memory();m.put(S,RET);m.put(I+0x43DBBA8L,0x9988776655443322L);
            Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());
            VolatileBits in=v(100,0x1234,0x8877,0x6655), p1=v(200,row[0],0x2222,0x3333), p2=v(300,row[1],0x4444,0x5555);
            NonvolatileBits nv=n(900), offered=rbx(nv,in.rcxBits());
            List<Call> seen=new ArrayList<>();
            List<Write> writes=new ArrayList<>();
            writes.add(new Write(S-8,8,nv.rbxBits()));writes.add(new Write(S-0x30,8,I+0x424D00AL));
            qword(expected,S-8,nv.rbxBits());qword(expected,S-0x30,I+0x424D00AL);
            Calls calls=new Calls(){@Override public VolatileBits invoke(Call c){
                seen.add(c);
                if(seen.size()==1){
                    assertEquals(new Call(0x424D005L,TargetKind.DIRECT_RVA,0x424D02CL,S-0x28,in,offered),c);
                    assertEquals(expected,m.snapshot());return p1;
                }
                assertEquals(new Call(0x424D012L,TargetKind.INDIRECT_ABSOLUTE,0x9988776655443322L,S-0x28,rcx(p1,in.rcxBits()),offered),c);
                return p2;
            }};
            NormalReturn out=Gate47FullState273.execute(new Entry(I,S,in,nv),m,calls);
            if(row[0]!=0){writes.add(new Write(S-0x30,8,I+0x424D018L));qword(expected,S-0x30,I+0x424D018L);}
            assertEquals(new NormalReturn(rax(row[0]==0?p1:p2,row[2]),RET,S+8,nv),out);
            assertEquals(row[0]==0?1:2,seen.size());assertEquals(writes,m.writes);assertEquals(expected,m.snapshot());
            assertEquals(row[0]==0?List.of(S-8,S):List.of(I+0x43DBBA8L,S-8,S),m.qwordReads);
        }
    }

    @Test void freshAliasedImportStackReadsAndOpaqueException() {
        long s=I+0x43DBBA8L+0x30, slot=s-0x30, saved=0x1122334455667788L, ret=0x1020304050607080L;
        Memory m=new Memory();m.put(s,RET);
        Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());
        VolatileBits in=v(1,17,19,23),p1=v(100,0x100000000L,29,31),p2=v(200,0x123400000001L,37,41);
        NonvolatileBits nv=n(300),offered=rbx(nv,19);
        List<Call> seen=new ArrayList<>();
        Calls calls=new Calls(){@Override public VolatileBits invoke(Call c){
            seen.add(c);
            if(seen.size()==1){
                assertEquals(new Call(0x424D005L,TargetKind.DIRECT_RVA,0x424D02CL,s-0x28,in,offered),c);
                m.writeDword(s-8,0x55667788);m.writeDword(s-4,0x11223344);
                m.writeQword(s,ret);return p1;
            }
            assertEquals(new Call(0x424D012L,TargetKind.INDIRECT_ABSOLUTE,I+0x424D00AL,s-0x28,rcx(p1,19),offered),c);
            return p2;
        }};
        NormalReturn out=Gate47FullState273.execute(new Entry(I,s,in,nv),m,calls);
        qword(expected,s-8,saved);qword(expected,s,ret);qword(expected,slot,I+0x424D018L);
        assertEquals(new NormalReturn(rax(p2,1),ret,s+8,rbx(nv,saved)),out);
        assertEquals(expected,m.snapshot());assertEquals(List.of(slot,s-8,s),m.qwordReads);
        assertEquals(List.of(new Write(s-8,8,nv.rbxBits()),new Write(slot,8,I+0x424D00AL),
                new Write(s-8,4,0x55667788L),new Write(s-4,4,0x11223344L),new Write(s,8,ret),
                new Write(slot,8,I+0x424D018L)),m.writes);

        Memory failed=new Memory();failed.put(S,RET);Map<Long,Byte> failedMap=new LinkedHashMap<>(failed.snapshot());
        UnsupportedOperationException sentinel=new UnsupportedOperationException("opaque stop");
        Calls abort=new Calls(){@Override public VolatileBits invoke(Call c){throw sentinel;}};
        assertSame(sentinel,assertThrows(UnsupportedOperationException.class,()->Gate47FullState273.execute(new Entry(I,S,in,nv),failed,abort)));
        qword(failedMap,S-8,nv.rbxBits());qword(failedMap,S-0x30,I+0x424D00AL);
        assertEquals(failedMap,failed.snapshot());assertEquals(List.of(),failed.qwordReads);
        assertEquals(List.of(new Write(S-8,8,nv.rbxBits()),new Write(S-0x30,8,I+0x424D00AL)),failed.writes);
    }

    @Test void exactBinderFramesGuardsAndForeignForwarding() {
        VolatileBits in=v(10,13,17,19),post=v(20,0,23,29);NonvolatileBits nv=n(40);
        long pre=0x9000L,s=pre-8;
        for(int fault=0;fault<3;fault++) {
            int which=fault;Memory m=new Memory();m.put(s,I+0x4251FA6L);
            Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());List<Call> seen=new ArrayList<>();
            Calls fallback=new Calls(){@Override public VolatileBits invoke(Call c){
                seen.add(c);assertEquals(new Call(0x424D005L,TargetKind.DIRECT_RVA,0x424D02CL,s-0x28,in,rbx(nv,17)),c);
                if(which==1)m.writeQword(s,0xdead);if(which==2)m.writeQword(s-8,0xbeef);return post;
            }};
            var bound=Gate47FullState273Calls.bind(I,m,fallback);
            Call original=new Call(0x4251FA1L,TargetKind.DIRECT_RVA,0x424CFFCL,pre,in,nv);
            if(fault==0)assertEquals(rax(post,0),bound.invoke(original));
            else assertThrows(UnsupportedOperationException.class,()->bound.invoke(original));
            qword(expected,s-8,fault==2?0xbeef:nv.rbxBits());qword(expected,s-0x30,I+0x424D00AL);
            if(fault==1)qword(expected,s,0xdead);
            assertEquals(expected,m.snapshot());assertEquals(1,seen.size());
            assertEquals(2+(fault==0?0:1),m.writes.size()); // no second CALL push by binder
        }
        Memory unused=new Memory();List<Object> forwarded=new ArrayList<>();NormalReturn answer=new NormalReturn(post,RET,pre,nv);
        Calls fallback=new Calls(){
            @Override public VolatileBits invoke(Call c){forwarded.add(c);return post;}
            @Override public NormalReturn tail(Tail t){forwarded.add(t);return answer;}
            @Override public long readGsQword58(){forwarded.add("GS");return 0x10293847;}
        };
        var bound=Gate47FullState273Calls.bind(I,unused,fallback);
        List<Call> foreign=List.of(new Call(0x4251FA0L,TargetKind.DIRECT_RVA,0x424CFFCL,pre,in,nv),
                new Call(0x4251FA1L,TargetKind.DIRECT_RVA,0x424CFFDL,pre,in,nv),
                new Call(0x4251FA1L,TargetKind.INDIRECT_ABSOLUTE,0x424CFFCL,pre,in,nv));
        for(Call c:foreign)assertSame(post,bound.invoke(c));
        Tail tail=new Tail(7,TargetKind.DIRECT_RVA,9,new Entry(I,S,in,nv));
        assertSame(answer,bound.tail(tail));assertEquals(0x10293847,bound.readGsQword58());
        for(int k=0;k<3;k++)assertSame(foreign.get(k),forwarded.get(k));assertSame(tail,forwarded.get(3));
        assertEquals(List.of(),unused.writes);assertEquals(Map.of(),unused.snapshot());
    }

    @Test void actualBase203ReachesGateAndReturnsCompleteState() {
        long e=0x20000,pre=e-0x28,child=pre-8,inner=child-0x28,size=0x40,ptr=0x11223344,heap=0x88776655;
        Memory m=new Memory();m.put(e,RET);m.put(I+0x5C5DE30L,heap);m.put(I+0x43DA388L,0x123456789abcL);m.put(I+0x43DBBA8L,0x778899aabbccL);
        Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());
        VolatileBits in=v(100,7,ptr,size),heapFail=v(200,0,23,29),policy=v(300,1,31,37),
                gateFirst=v(400,0x100000000L,41,43),gateSecond=v(500,0x7000000000000001L,47,53),heapSuccess=v(600,0x99990000L,59,61);
        NonvolatileBits nv=n(700),bodyN=rdi(rbx(nv,size),ptr);
        List<Call> expectedCalls=List.of(
                new Call(0x4251FB9L,TargetKind.INDIRECT_ABSOLUTE,0x123456789abcL,pre,heapArgs(in,heap,ptr,size),bodyN),
                new Call(0x4251F95L,TargetKind.DIRECT_RVA,0x424E250L,pre,heapFail,bodyN),
                new Call(0x424D005L,TargetKind.DIRECT_RVA,0x424D02CL,inner,rcx(policy,size),bodyN),
                new Call(0x424D012L,TargetKind.INDIRECT_ABSOLUTE,0x778899aabbccL,inner,rcx(gateFirst,size),bodyN),
                new Call(0x4251FB9L,TargetKind.INDIRECT_ABSOLUTE,0x123456789abcL,pre,heapArgs(rax(gateSecond,1),heap,ptr,size),bodyN));
        List<VolatileBits> replies=List.of(heapFail,policy,gateFirst,gateSecond,heapSuccess);List<Call> seen=new ArrayList<>();
        Calls fallback=new Calls(){@Override public VolatileBits invoke(Call c){int k=seen.size();seen.add(c);assertEquals(expectedCalls.get(k),c);return replies.get(k);}};
        List<Long> budget=new ArrayList<>();
        var out=GovernmentResizeBase203.execute(new Entry(I,e,in,nv),m,Gate47FullState273Calls.bind(I,m,fallback),
                (site,guard)->{budget.add(site);assertEquals(0,guard);if(budget.size()>1)throw new AssertionError("unexpected retry");});
        List<Write> writes=List.of(new Write(e+8,8,nv.rbxBits()),new Write(e-8,8,nv.rdiBits()),
                new Write(pre-8,8,I+0x4251FBFL),new Write(pre-8,8,I+0x4251F9AL),new Write(pre-8,8,I+0x4251FA6L),
                new Write(child-8,8,size),new Write(inner-8,8,I+0x424D00AL),new Write(inner-8,8,I+0x424D018L),new Write(pre-8,8,I+0x4251FBFL));
        for(Write w:writes)qword(expected,w.address(),w.bits());
        assertEquals(new NormalReturn(heapSuccess,RET,e+8,nv),out);assertEquals(expectedCalls,seen);assertEquals(List.of(0x4251F95L),budget);
        assertEquals(writes,m.writes);assertEquals(expected,m.snapshot());
        assertEquals(List.of(I+0x5C5DE30L,I+0x43DA388L,I+0x43DBBA8L,child-8,child,I+0x5C5DE30L,I+0x43DA388L,e+8,e-8,e),m.qwordReads);
    }

    private static VolatileBits heapArgs(VolatileBits a,long heap,long ptr,long size){
        return new VolatileBits(a.raxBits(),heap,0,ptr,size,a.r10Bits(),a.r11Bits(),a.xmm0(),a.xmm1(),a.xmm2(),a.xmm3(),a.xmm4(),a.xmm5());
    }
}
