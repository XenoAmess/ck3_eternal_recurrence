package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestRetry4223b94.UnexecutedSourcePath;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;

/** Independent held-normal-path literals. D7 meaning and Native exception behavior remain unknown. */
final class Wrapper19NormalFullState285Test {
    static final long I=0x180000000L,S=0xb00000L,P=0xc00000L,H=0x889900L,T=0x7fff12340000L;
    static final LoopBudget ALLOW=(site,guard)->{};
    static final class InitialMemory extends RoleMemory284 implements GovernmentInitialFrame162Api.Memory { }
    static GovernmentInitialFrame162Api.Calls noOuter() {
        return new GovernmentInitialFrame162Api.Calls(){
            @Override public VolatileBits invoke(OpaqueCall c){throw new AssertionError(c);}
            @Override public long readGsQword58(){throw new AssertionError("GS");}
        };
    }
    static VolatileBits heapInput(VolatileBits v,long size) {
        return new VolatileBits(1,H,0,size,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }

    @Test void initialOwnsOnePreviouslyUnmappedPushAndComposesAllNormalChildren() {
        var role=new InitialMemory();var m=role.backing;var input=v(200,9,13,11);var nv=n(700);var post=v(900,0x100008000L,0x13,0x14);
        m.put(I+0x5C5DE30L,H);m.put(I+0x43DA768L,T);var expected=new HashMap<>(m.snapshot());
        assertFalse(expected.containsKey(P-8));var seen=new ArrayList<Call>();
        var binder=Wrapper19Initial162Calls285.bind(I,role,noOuter(),new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){seen.add(c);return post;}
        },ALLOW);
        assertEquals(post,binder.invoke(new OpaqueCall(0x30A304FL,0x42242CCL,P,input,nv)));
        assertEquals(List.of(new Call(0x424FDDEL,TargetKind.INDIRECT_ABSOLUTE,T,P-0x90,heapInput(input,13),rbx(nv,13))),seen);
        var writes=List.of(new Write(P-8,8,I+0x30A3054L),new Write(P-0x38,8,I+0x42242D5L),
            new Write(P-0x40,8,nv.rbxBits()),new Write(P-0x68,8,I+0x4223BB3L),
            new Write(P-0x70,8,13),new Write(P-0x98,8,I+0x424FDE4L));
        assertEquals(writes,m.writes);for(var w:writes)qword(expected,w.address(),w.bits());
        assertEquals(expected,m.snapshot());
        assertEquals(List.of(I+0x5C5DE30L,I+0x43DA768L,P-0x70,P-0x68,P-0x40,P-0x38,P-8),m.qwordReads);
    }

    @Test void terminalExceptionAndActualChildReturnDamageNeverTakeDisconnectedZeroFragment() {
        var input=v(10,8,17,9);var nv=n(200);var m=new Memory();m.put(S,0xaaaa);var seen=new ArrayList<Call>();
        var ex=assertThrows(UnexecutedSourcePath.class,()->Wrapper19NormalFullState285.execute(new Entry(I,S,input,nv),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){seen.add(c);return v(30,seen.size()==1?0:0x100000000L,31,32);}
        },ALLOW));
        assertEquals(0x42207D8L,ex.targetRva());assertEquals(0x4223BC9L,ex.trapSiteRva());assertEquals(17,ex.capturedSizeBits());
        assertEquals(List.of(0x4223BAEL,0x4223BA2L),seen.stream().map(Call::callSiteRva).toList());
        assertEquals(S-0x58,seen.get(0).rspBits());assertEquals(17,seen.get(1).volatileBits().rcxBits());
        assertEquals(List.of(new Write(S-0x30,8,I+0x42242D5L),new Write(S-0x38,8,nv.rbxBits()),
                new Write(S-0x60,8,I+0x4223BB3L),new Write(S-0x60,8,I+0x4223BA7L)),m.writes);
        assertTrue(m.qwordReads.isEmpty());
        for(boolean damageN:new boolean[]{false,true}) {
            var damaged=new Memory();damaged.put(S,0xbbbb);var post=v(60,0x1234,61,62);
            assertThrows(UnsupportedOperationException.class,()->Wrapper19NormalFullState285.execute(new Entry(I,S,input,nv),damaged,new Gate47Fixture273.Calls(){
                @Override public VolatileBits invoke(Call c){damaged.writeQword(damageN?S-0x38:S-0x30,0x9988);return post;}
            },ALLOW));
            assertEquals(List.of(S-0x38,S-0x30),damaged.qwordReads);
            assertEquals(new Write(S-0x30,8,I+0x42242D5L),damaged.writes.get(0));
        }
    }

    @Test void initialForeignProtocolIsUntouchedAndFreshOuterReturnIsQualified() {
        var input=v(30,1,5,2);var nv=n(300);var role=new InitialMemory();var seen=new ArrayList<OpaqueCall>();
        var outer=new GovernmentInitialFrame162Api.Calls(){@Override public VolatileBits invoke(OpaqueCall c){seen.add(c);return input;}@Override public long readGsQword58(){return 987;}};
        var lower=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError(c);}};
        var binder=Wrapper19Initial162Calls285.bind(I,role,outer,lower,ALLOW);
        for(var foreign:List.of(new OpaqueCall(0x30A3050L,0x42242CCL,P,input,nv),new OpaqueCall(0x30A304FL,0x42242CDL,P,input,nv))) {
            assertSame(input,binder.invoke(foreign));assertSame(foreign,seen.get(seen.size()-1));
        }
        assertEquals(987,binder.readGsQword58());assertTrue(role.backing.writes.isEmpty());assertTrue(role.backing.qwordReads.isEmpty());
        var damaged=new InitialMemory();damaged.backing.put(I+0x5C5DE30L,H);damaged.backing.put(I+0x43DA768L,T);
        var broken=Wrapper19Initial162Calls285.bind(I,damaged,noOuter(),new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){damaged.writeQword(P-8,0x7654);return v(50,0x7777,51,52);}
        },ALLOW);
        assertThrows(UnsupportedOperationException.class,()->broken.invoke(new OpaqueCall(0x30A304FL,0x42242CCL,P,input,nv)));
        assertEquals(P-8,damaged.backing.qwordReads.get(damaged.backing.qwordReads.size()-1).longValue());
        assertEquals(new Write(P-8,8,I+0x30A3054L),damaged.backing.writes.get(0));
    }
}
