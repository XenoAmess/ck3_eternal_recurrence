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
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner literals frozen from94/122B before candidates; owner later reviewed production. */
final class Allocate94FullState282Test {
    private static final long I=0x140000000L,S=0x10000,RET=0x1122334455667788L;
    private static final long H=I+0x5C5DE30L,T=I+0x43DA768L;

    @Test void zeroBoundaryAndOverflowWithAliasedErrorDword() {
        for(long size:new long[]{0,0xFFFFFFFFFFFFFFE0L}){
            Memory m=new Memory();m.put(S,RET);m.put(H,0x7788);m.put(T,0xaabbccddL);
            Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());
            VolatileBits in=v(100,0x1234567800000000L,size,9),post=v(200,0x9988776600000000L,17,19);
            NonvolatileBits nv=n(0x5566778800000000L);long adjusted=size==0?1:size;
            List<Call> seen=new ArrayList<>();
            Gate47Fixture273.Calls ports=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
                seen.add(c);assertEquals(new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,0xaabbccddL,S-0x28,heapV(rax(in,1),0x7788,adjusted),rbx(nv,adjusted)),c);return post;
            }};
            NormalReturn out=Allocate94FullState282.execute(new Entry(I,S,in,nv),m,ports,(a,b)->fail("unexpected retry"));
            List<Write> writes=List.of(new Write(S-8,8,nv.rbxBits()),new Write(S-0x30,8,I+0x424FDE4L));
            apply(expected,writes);assertEquals(new NormalReturn(post,RET,S+8,nv),out);
            assertEquals(writes,m.writes);assertEquals(expected,m.snapshot());assertEquals(1,seen.size());assertEquals(List.of(H,T,S-8,S),m.qwordReads);
        }
        Memory m=new Memory();m.put(S,RET);Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());
        long size=0xFFFFFFFFFFFFFFE1L;VolatileBits in=v(300,0xdeadbeef00112233L,size,31),post=v(400,S,37,41);NonvolatileBits nv=n(500);
        List<Call> seen=new ArrayList<>();
        Gate47Fixture273.Calls ports=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            seen.add(c);assertEquals(new Call(0x424FDEBL,TargetKind.DIRECT_RVA,0x423B18CL,S-0x28,in,rbx(nv,size)),c);return post;
        }};
        NormalReturn out=Allocate94FullState282.execute(new Entry(I,S,in,nv),m,ports,(a,b)->fail("overflow cannot retry"));
        List<Write> writes=List.of(new Write(S-8,8,nv.rbxBits()),new Write(S-0x30,8,I+0x424FDF0L),new Write(S,4,12));
        apply(expected,writes);assertEquals(new NormalReturn(rax(post,0),0x112233440000000cL,S+8,nv),out);
        assertEquals(writes,m.writes);assertEquals(expected,m.snapshot());assertEquals(List.of(S-8,S),m.qwordReads);assertEquals(1,seen.size());
    }

    @Test void policyGateLow32AndRetryFreshGlobalImport() {
        for(int mode=0;mode<3;mode++){
            int branch=mode;long size=0x40,cell=0x30000;
            Memory m=new Memory();m.put(S,RET);m.put(H,0x1111);m.put(T,0x2222);m.put(cell,0xabcdef0012345678L);
            Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());VolatileBits in=v(100,7,size,9),heapFail=v(200,0,13,17),
                    policy=v(300,mode==0?0xaaaa000000000000L:0xaaaa000000000001L,19,23),
                    gate=v(400,mode==1?0xbbbb000000000000L:0xbbbb000000000001L,29,31),
                    err=v(500,cell,37,41),ok=v(600,0xdead123400000000L,43,47);
            NonvolatileBits nv=n(700),body=rbx(nv,size);
            List<Call> wanted=new ArrayList<>();wanted.add(new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,0x2222,S-0x28,heapV(rax(in,1),0x1111,size),body));
            wanted.add(new Call(0x424FDBDL,TargetKind.DIRECT_RVA,0x424E250L,S-0x28,heapFail,body));
            if(mode!=0)wanted.add(new Call(0x424FDC9L,TargetKind.DIRECT_RVA,0x424CFFCL,S-0x28,rcx(policy,size),body));
            wanted.add(mode==2?new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,0x4444,S-0x28,heapV(gate,0x3333,size),body):
                    new Call(0x424FDEBL,TargetKind.DIRECT_RVA,0x423B18CL,S-0x28,mode==0?policy:gate,body));
            List<Call> seen=new ArrayList<>();List<Long> budget=new ArrayList<>();
            Gate47Fixture273.Calls ports=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
                int k=seen.size();seen.add(c);assertEquals(wanted.get(k),c);
                if(k==0)return heapFail;if(k==1)return policy;
                if(branch!=0&&k==2){if(branch==2){m.writeQword(H,0x3333);m.writeQword(T,0x4444);}return gate;}
                return branch==2?ok:err;
            }};
            NormalReturn out=Allocate94FullState282.execute(new Entry(I,S,in,nv),m,ports,(site,guard)->{budget.add(site);assertEquals(0x424FDBDL,site);assertEquals(0,guard);assertEquals(1,budget.size());});
            List<Write> writes=new ArrayList<>();writes.add(new Write(S-8,8,nv.rbxBits()));writes.add(new Write(S-0x30,8,I+0x424FDE4L));writes.add(new Write(S-0x30,8,I+0x424FDC2L));
            if(mode!=0)writes.add(new Write(S-0x30,8,I+0x424FDCEL));
            if(mode==2){writes.add(new Write(H,8,0x3333));writes.add(new Write(T,8,0x4444));writes.add(new Write(S-0x30,8,I+0x424FDE4L));}
            else{writes.add(new Write(S-0x30,8,I+0x424FDF0L));writes.add(new Write(cell,4,12));}
            apply(expected,writes);assertEquals(new NormalReturn(mode==2?ok:rax(err,0),RET,S+8,nv),out);
            assertEquals(wanted,seen);assertEquals(writes,m.writes);assertEquals(expected,m.snapshot());
            assertEquals(mode==2?List.of(H,T,H,T,S-8,S):List.of(H,T,S-8,S),m.qwordReads);
        }
    }

    @Test void opaqueAndBudgetFailuresDoNotSynthesizeEpilogue() {
        for(boolean abortBudget:new boolean[]{false,true}){
            Memory m=new Memory();m.put(S,RET);m.put(H,0x11);m.put(T,0x22);Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());
            VolatileBits in=v(100,7,0x40,13),post=v(200,0,17,19);NonvolatileBits nv=n(300);
            UnsupportedOperationException sentinel=new UnsupportedOperationException(abortBudget?"finite budget":"opaque port");
            Gate47Fixture273.Calls ports=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
                assertEquals(new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,0x22,S-0x28,heapV(rax(in,1),0x11,0x40),rbx(nv,0x40)),c);
                if(!abortBudget)throw sentinel;return post;
            }};
            assertSame(sentinel,assertThrows(UnsupportedOperationException.class,()->Allocate94FullState282.execute(new Entry(I,S,in,nv),m,ports,(site,guard)->{
                assertTrue(abortBudget);assertEquals(0x424FDBDL,site);assertEquals(0,guard);throw sentinel;
            })));
            List<Write> writes=List.of(new Write(S-8,8,nv.rbxBits()),new Write(S-0x30,8,I+0x424FDE4L));apply(expected,writes);
            assertEquals(writes,m.writes);assertEquals(expected,m.snapshot());assertEquals(List.of(H,T),m.qwordReads);
        }
    }

    @Test void actualBase203NullPathReusesInnerGateAndReturnsAllState() {
        long e=0x20000,basePre=e-0x28,allocationS=basePre-8,allocationPre=allocationS-0x28,gateS=allocationPre-8,gatePre=gateS-0x28,size=0x40;
        Memory m=new Memory();m.put(e,RET);m.put(H,0x1111);m.put(T,0x2222);m.put(I+0x43DBBA8L,0x5555);Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());
        VolatileBits in=v(100,0x12340000,0,size),heapFail=v(200,0,13,17),policy=v(300,1,19,23),
                gateFirst=v(400,0x100000000L,29,31),gateSecond=v(500,0xabcd000000000001L,37,41),heapOK=v(600,0x99990000L,43,47);
        NonvolatileBits nv=n(700),body=rdi(rbx(nv,size),0);
        List<Call> wanted=List.of(new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,0x2222,allocationPre,heapV(rax(rcx(in,size),1),0x1111,size),body),
                new Call(0x424FDBDL,TargetKind.DIRECT_RVA,0x424E250L,allocationPre,heapFail,body),
                new Call(0x424D005L,TargetKind.DIRECT_RVA,0x424D02CL,gatePre,rcx(policy,size),body),
                new Call(0x424D012L,TargetKind.INDIRECT_ABSOLUTE,0x5555,gatePre,rcx(gateFirst,size),body),
                new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,0x4444,allocationPre,heapV(rax(gateSecond,1),0x3333,size),body));
        List<VolatileBits> replies=List.of(heapFail,policy,gateFirst,gateSecond,heapOK);List<Call> seen=new ArrayList<>();List<Long> budget=new ArrayList<>();
        Gate47Fixture273.Calls fallback=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            int k=seen.size();seen.add(c);assertEquals(wanted.get(k),c);if(k==3){m.writeQword(H,0x3333);m.writeQword(T,0x4444);}return replies.get(k);
        }};
        var bounded=(GovernmentCrtBoundary185Api.LoopBudget)(site,guard)->{budget.add(site);assertEquals(0x424FDBDL,site);assertEquals(0,guard);assertEquals(1,budget.size());};
        NormalReturn out=GovernmentResizeBase203.execute(new Entry(I,e,in,nv),m,Allocate94FullState282Calls.bind(I,m,fallback,bounded),bounded);
        List<Write> writes=List.of(new Write(e+8,8,nv.rbxBits()),new Write(e-8,8,nv.rdiBits()),new Write(basePre-8,8,I+0x4251F69L),
                new Write(allocationS-8,8,size),new Write(allocationPre-8,8,I+0x424FDE4L),new Write(allocationPre-8,8,I+0x424FDC2L),new Write(allocationPre-8,8,I+0x424FDCEL),
                new Write(gateS-8,8,size),new Write(gatePre-8,8,I+0x424D00AL),new Write(gatePre-8,8,I+0x424D018L),new Write(H,8,0x3333),new Write(T,8,0x4444),new Write(allocationPre-8,8,I+0x424FDE4L));
        apply(expected,writes);assertEquals(new NormalReturn(heapOK,RET,e+8,nv),out);assertEquals(wanted,seen);assertEquals(List.of(0x424FDBDL),budget);
        assertEquals(writes,m.writes);assertEquals(expected,m.snapshot());
        assertEquals(List.of(H,T,I+0x43DBBA8L,gateS-8,gateS,H,T,allocationS-8,allocationS,e+8,e-8,e),m.qwordReads);
    }

    @Test void exactConsumerGuardAndForeignForwarding() {
        long pre=0x9000,s=pre-8;VolatileBits in=v(100,7,0x40,13),post=v(200,0x98760000,17,19);NonvolatileBits nv=n(300);
        for(int fault=0;fault<3;fault++){
            int which=fault;Memory m=new Memory();m.put(s,I+0x4251F69L);m.put(H,0x11);m.put(T,0x22);Map<Long,Byte> expected=new LinkedHashMap<>(m.snapshot());
            Gate47Fixture273.Calls fallback=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
                assertEquals(new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,0x22,s-0x28,heapV(rax(in,1),0x11,0x40),rbx(nv,0x40)),c);
                if(which==1)m.writeQword(s,0xdead);if(which==2)m.writeQword(s-8,0xbeef);return post;
            }};
            Calls bind=Allocate94FullState282Calls.bind(I,m,fallback,(a,b)->fail("unexpected retry"));Call call=new Call(0x4251F64L,TargetKind.DIRECT_RVA,0x424FDA0L,pre,in,nv);
            if(fault==0)assertEquals(post,bind.invoke(call));else assertThrows(UnsupportedOperationException.class,()->bind.invoke(call));
            qword(expected,s-8,fault==2?0xbeef:nv.rbxBits());qword(expected,s-0x30,I+0x424FDE4L);if(fault==1)qword(expected,s,0xdead);
            assertEquals(expected,m.snapshot());assertEquals(fault==0?2:3,m.writes.size());
        }
        Memory unused=new Memory();List<Object> seen=new ArrayList<>();NormalReturn answer=new NormalReturn(post,RET,pre,nv);
        Gate47Fixture273.Calls fallback=new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){seen.add(c);return post;}
            @Override public NormalReturn tail(Tail t){seen.add(t);return answer;}
            @Override public long readGsQword58(){seen.add("GS");return 0x7788;}
        };
        Calls bind=Allocate94FullState282Calls.bind(I,unused,fallback,(a,b)->fail("unexpected budget"));
        List<Call> foreign=List.of(new Call(0x4251F63L,TargetKind.DIRECT_RVA,0x424FDA0L,pre,in,nv),new Call(0x4251F64L,TargetKind.DIRECT_RVA,0x424FDA1L,pre,in,nv),
                new Call(0x4251F64L,TargetKind.INDIRECT_ABSOLUTE,0x424FDA0L,pre,in,nv),new Call(0x424FDC9L,TargetKind.DIRECT_RVA,0x424CFFCL,pre,in,nv));
        for(Call c:foreign)assertSame(post,bind.invoke(c));Tail tail=new Tail(7,TargetKind.DIRECT_RVA,9,new Entry(I,S,in,nv));assertSame(answer,bind.tail(tail));assertEquals(0x7788,bind.readGsQword58());
        for(int k=0;k<4;k++)assertSame(foreign.get(k),seen.get(k));assertSame(tail,seen.get(4));assertEquals(Map.of(),unused.snapshot());assertEquals(List.of(),unused.writes);
    }

    private static VolatileBits heapV(VolatileBits a,long heap,long bytes){return new VolatileBits(a.raxBits(),heap,0,bytes,a.r9Bits(),a.r10Bits(),a.r11Bits(),a.xmm0(),a.xmm1(),a.xmm2(),a.xmm3(),a.xmm4(),a.xmm5());}
    private static void apply(Map<Long,Byte> map,List<Write> writes){for(Write w:writes){if(w.bytes()==8)qword(map,w.address(),w.bits());else if(w.bytes()==4)dword(map,w.address(),(int)w.bits());else throw new AssertionError("unsupported expected write");}}
}
