package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestRetry4223b94.UnexecutedSourcePath;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentRoot178Api;

/** Source-derived finite port frames, not execution of the whole Root178 subject or Native. */
final class Retry60NormalFullState284Test {
    static final long I=0x180000000L,S=0x900000L,P=0xa00000L,H=0x778800L,T=0x7fff12345678L;
    static final LoopBudget ALLOW=(site,guard)->{};
    static Call direct(long site,long target,long sp,VolatileBits v,NonvolatileBits n) {
        return new Call(site,TargetKind.DIRECT_RVA,target,sp,v,n);
    }
    static VolatileBits heapInput(VolatileBits v,long size) {
        return new VolatileBits(1,H,0,size,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static GovernmentRoot178Api.Calls noOuter() {
        return new GovernmentRoot178Api.Calls() {
            @Override public VolatileBits invoke(OpaqueCall c) { throw new AssertionError(c); }
            @Override public long readGsQword58() { throw new AssertionError("GS"); }
        };
    }

    @Test void rawFullWidthRetryAndBothTerminalFences() {
        var first=v(10,0x55,9,0x66);var nv=n(200);var a=v(30,0,0xdead,81);
        var gate=v(60,0x100000001L,0xbeef,91);var end=v(90,0x100000000L,0x777,101);
        var m=new Memory();m.put(S,0xabcdefL);var expected=new HashMap<>(m.snapshot());
        var seen=new ArrayList<Call>();var steps=new ArrayList<Long>();
        var out=Retry60NormalFullState284.execute(new Entry(I,S,first,nv),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){seen.add(c);return switch(seen.size()){case 1->a;case 2->gate;case 3->end;default->throw new AssertionError(c);};}
        },(site,guard)->{assertEquals(0x4223BAEL,site);assertEquals(9,guard);steps.add(site);});
        assertEquals(List.of(direct(0x4223BAEL,0x42420B8L,S-0x28,first,rbx(nv,9)),
            direct(0x4223BA2L,0x424CFFCL,S-0x28,rcx(a,9),rbx(nv,9)),
            direct(0x4223BAEL,0x42420B8L,S-0x28,rcx(gate,9),rbx(nv,9))),seen);
        assertEquals(2,steps.size());assertEquals(new NormalReturn(end,0xabcdefL,S+8,nv),out);
        assertEquals(List.of(new Write(S-8,8,nv.rbxBits()),new Write(S-0x30,8,I+0x4223BB3L),
            new Write(S-0x30,8,I+0x4223BA7L),new Write(S-0x30,8,I+0x4223BB3L)),m.writes);
        qword(expected,S-8,nv.rbxBits());qword(expected,S-0x30,I+0x4223BB3L);
        assertEquals(expected,m.snapshot());assertEquals(List.of(S-8,S),m.qwordReads);
        for(long size:new long[]{1,-1}) {
            var fm=new Memory();fm.put(S,0x9988);var input=v(11,7,size,9);var calls=new ArrayList<Call>();
            var ex=assertThrows(UnexecutedSourcePath.class,()->Retry60NormalFullState284.execute(new Entry(I,S,input,nv),fm,new Gate47Fixture273.Calls(){
                @Override public VolatileBits invoke(Call c){calls.add(c);return calls.size()==1?a:rax(gate,0x100000000L);}
            },ALLOW));
            assertEquals(size,ex.capturedSizeBits());assertEquals(size==-1?0x4224A58L:0x42207D8L,ex.targetRva());
            assertEquals(size==-1?0x4223BCFL:0x4223BC9L,ex.trapSiteRva());
            assertEquals(2,calls.size());assertEquals(0x4223BA2L,calls.get(1).callSiteRva());
            assertEquals(List.of(new Write(S-8,8,nv.rbxBits()),new Write(S-0x30,8,I+0x4223BB3L),new Write(S-0x30,8,I+0x4223BA7L)),fm.writes);
            assertTrue(fm.qwordReads.isEmpty());
        }
    }

    @Test void rootOwnedPushComposesTailAndHeapWithOneBackingMemory() {
        var role=new RoleMemory284();var m=role.backing;var input=v(100,3,12,4);var nv=n(500);var post=v(700,0x100002000L,0x31,0x32);
        m.put(P-8,I+0x3F5C0FCL);m.put(I+0x5C5DE30L,H);m.put(I+0x43DA768L,T);
        var expected=new HashMap<>(m.snapshot());var seen=new ArrayList<Call>();
        var binder=Retry60NormalFullState284Calls.bindRoot(I,role,noOuter(),new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){seen.add(c);return post;}
        },ALLOW);
        assertSame(m,Retry60NormalFullState284Calls.as185(m));
        assertEquals(post,binder.invoke(new OpaqueCall(0x3F5C0F7L,0x4223B94L,P,input,nv)));
        assertEquals(List.of(new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,T,P-0x60,heapInput(input,12),rbx(nv,12))),seen);
        var writes=List.of(new Write(P-0x10,8,nv.rbxBits()),new Write(P-0x38,8,I+0x4223BB3L),new Write(P-0x40,8,12),new Write(P-0x68,8,I+0x424FDE4L));
        assertEquals(writes,m.writes);for(var w:writes)qword(expected,w.address(),w.bits());
        assertEquals(expected,m.snapshot());
        assertEquals(List.of(I+0x5C5DE30L,I+0x43DA768L,P-0x40,P-0x38,P-0x10,P-8),m.qwordReads);
    }

    @Test void exactGateChildrenPreserveFullStateAndRejectFreshSavedRegisterDamage() {
        for(long site:new long[]{0x4223BA2L,0x424FDC9L}) {
            long ret=site==0x4223BA2L?0x4223BA7L:0x424FDCEL;
            var input=v(1,3,21,4);var nv=n(40);var post=v(90,0,52,53);
            for(boolean damage:new boolean[]{false,true}) {
                var m=new Memory();m.put(P-8,I+ret);var seen=new ArrayList<Call>();
                var lower=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){seen.add(c);if(damage)m.writeQword(P-0x10,0x999);return post;}};
                var children=Retry60NormalFullState284Calls.normalChildren(I,m,lower,ALLOW);
                if(damage)assertThrows(UnsupportedOperationException.class,()->children.invoke(direct(site,0x424CFFCL,P,input,nv)));
                else assertEquals(rax(post,0),children.invoke(direct(site,0x424CFFCL,P,input,nv)));
                assertEquals(List.of(direct(0x424D005L,0x424D02CL,P-0x30,input,rbx(nv,21))),seen);
                assertEquals(List.of(P-0x10,P-8),m.qwordReads);
                assertEquals(new Write(P-0x38,8,I+0x424D00AL),m.writes.get(1));
            }
        }
    }

    @Test void foreignRolesStaySeparateAndRootReturnBudgetExceptionsAreNotSuccess() {
        var input=v(11,2,3,4);var nv=n(50);var role=new RoleMemory284();var m=role.backing;
        var foreign=new OpaqueCall(0x3F5C0F7L,0x4223B95L,P,input,nv);var seenOuter=new ArrayList<OpaqueCall>();
        var outer=new GovernmentRoot178Api.Calls(){@Override public VolatileBits invoke(OpaqueCall c){seenOuter.add(c);return input;}@Override public long readGsQword58(){return 123;}};
        var lowSeen=new ArrayList<Call>();var tail=new Tail(4,TargetKind.INDIRECT_ABSOLUTE,5,new Entry(I,P,input,nv));var nr=new NormalReturn(input,77,P+8,nv);
        var lower=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){lowSeen.add(c);return input;}@Override public NormalReturn tail(Tail t){assertSame(tail,t);return nr;}@Override public long readGsQword58(){return 456;}};
        var children=Retry60NormalFullState284Calls.normalChildren(I,m,lower,ALLOW);
        var indirect=new Call(0x4223BAEL,TargetKind.INDIRECT_ABSOLUTE,0x42420B8L,P,input,nv);
        assertSame(input,children.invoke(indirect));assertSame(indirect,lowSeen.get(0));assertSame(nr,children.tail(tail));assertEquals(456,children.readGsQword58());
        var bind=Retry60NormalFullState284Calls.bindRoot(I,role,outer,lower,ALLOW);
        assertSame(input,bind.invoke(foreign));assertSame(foreign,seenOuter.get(0));assertEquals(123,bind.readGsQword58());assertTrue(m.writes.isEmpty());
        for(long damageOffset:new long[]{-0x10,-8,-0x40,-0x38}) {
            var rm=new RoleMemory284();rm.backing.put(P-8,I+0x3F5C0FCL);rm.backing.put(I+0x5C5DE30L,H);rm.backing.put(I+0x43DA768L,T);
            var rb=Retry60NormalFullState284Calls.bindRoot(I,rm,noOuter(),new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0x424FDDEL,c.callSiteRva());rm.writeQword(P+damageOffset,0x987);return rax(input,9);}},ALLOW);
            assertThrows(UnsupportedOperationException.class,()->rb.invoke(new OpaqueCall(0x3F5C0F7L,0x4223B94L,P,input,nv)));
        }
        var bm=new Memory();bm.put(S,123);var stop=new IllegalArgumentException("budget");
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->Retry60NormalFullState284.execute(new Entry(I,S,input,nv),bm,lower,(site,guard)->{throw stop;})));
        assertEquals(List.of(new Write(S-8,8,nv.rbxBits())),bm.writes);assertTrue(bm.qwordReads.isEmpty());
        var om=new Memory();var opaque=new IllegalStateException("opaque");
        assertSame(opaque,assertThrows(IllegalStateException.class,()->Retry60NormalFullState284.execute(new Entry(I,S,input,nv),om,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(0x4223BAEL,c.callSiteRva());throw opaque;}
        },ALLOW)));
        assertEquals(List.of(new Write(S-8,8,nv.rbxBits()),new Write(S-0x30,8,I+0x4223BB3L)),om.writes);assertTrue(om.qwordReads.isEmpty());
    }
}
