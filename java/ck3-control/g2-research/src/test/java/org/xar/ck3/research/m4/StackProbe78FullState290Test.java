package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;

/** Held78B literals; owner reviewed production, not an independent model oracle or hardware test. */
final class StackProbe78FullState290Test {
    static final long I=0x180000000L,RIP=0x7fff01020304L;
    static VolatileBits scratch(VolatileBits v,long r10,long r11) {
        return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),r10,r11,
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static final class ProbeMemory extends RoleMemory284 implements GovernmentInitialFrame162Api.Memory { }

    @Test void noTouchUnsignedComparisonAndHighAddressThreePagesKeepAllOtherBits() {
        for(long s:new long[]{0x9000L,0x8000000000001000L}) {
            var m=new Memory();m.put(s,RIP);var input=v(100,0x100,0x4567,0x89);var nv=n(300);var expected=new HashMap<>(m.snapshot());
            var out=StackProbe78FullState290.execute(new Entry(I,s,input,nv),m,()->0x8000L,(site,page)->{throw new AssertionError("no page expected");});
            assertEquals(new NormalReturn(input,RIP,s+8,nv),out);
            assertEquals(List.of(new Write(s-16,8,input.r10Bits()),new Write(s-8,8,input.r11Bits())),m.writes);
            qword(expected,s-16,input.r10Bits());qword(expected,s-8,input.r11Bits());assertEquals(expected,m.snapshot());
            assertEquals(List.of(s-16,s-8,s),m.qwordReads);
        }
        long s=0x1_0002_0ff8L;var input=v(400,0x3000,0x5566,0x7788);var nv=n(600);var m=new Memory();m.put(s,RIP);
        for(long page:new long[]{0x1_0002_0000L,0x1_0001_f000L,0x1_0001_e000L})m.put(page,0x1122334455667788L);
        var expected=new HashMap<>(m.snapshot());var pages=new ArrayList<Long>();
        var out=StackProbe78FullState290.execute(new Entry(I,s,input,nv),m,()->0x1_0002_1000L,(site,page)->{assertEquals(0x42247E0L,site);pages.add(page);});
        assertEquals(List.of(0x1_0002_0000L,0x1_0001_f000L,0x1_0001_e000L),pages);
        assertEquals(new NormalReturn(input,RIP,s+8,nv),out);
        assertEquals(List.of(new Write(s-16,8,input.r10Bits()),new Write(s-8,8,input.r11Bits()),
                new Write(0x1_0002_0000L,1,0),new Write(0x1_0001_f000L,1,0),new Write(0x1_0001_e000L,1,0)),m.writes);
        qword(expected,s-16,input.r10Bits());qword(expected,s-8,input.r11Bits());for(long p:pages)expected.put(p,(byte)0);
        assertEquals(expected,m.snapshot());assertEquals(List.of(s-16,s-8,s),m.qwordReads);
    }

    @Test void unsignedBorrowTargetsZeroAndGsAliasIsRestoredFromActualSavedSlots() {
        long s=0x18;var input=v(100,-1L,0x45,0x67);var nv=n(300);var m=new Memory();m.put(s,RIP);m.put(0,0x8877665544332211L);
        var pages=new ArrayList<Long>();var out=StackProbe78FullState290.execute(new Entry(I,s,input,nv),m,()->0x1000L,(site,page)->pages.add(page));
        assertEquals(List.of(0L),pages);assertEquals(new NormalReturn(input,RIP,s+8,nv),out);
        assertEquals(List.of(new Write(8,8,input.r10Bits()),new Write(16,8,input.r11Bits()),new Write(0,1,0)),m.writes);
        assertEquals((byte)0,m.data.get(0L).byteValue());assertEquals((byte)0x22,m.data.get(1L).byteValue());
        long a=0xa000;var am=new Memory();am.put(a,RIP);var av=v(500,0,0x123,0x456);var an=n(700);
        var expected=new HashMap<>(am.snapshot());
        var alias=StackProbe78FullState290.execute(new Entry(I,a,av,an),am,()->{
            assertEquals(List.of(new Write(a-16,8,av.r10Bits()),new Write(a-8,8,av.r11Bits())),am.writes);
            am.writeQword(a-16,0x1111222233334444L);am.writeQword(a-8,0x5555666677778888L);am.writeQword(a,0x123456789L);return a+8;
        },(site,page)->{throw new AssertionError("alias no page");});
        assertEquals(new NormalReturn(scratch(av,0x1111222233334444L,0x5555666677778888L),0x123456789L,a+8,an),alias);
        qword(expected,a-16,0x1111222233334444L);qword(expected,a-8,0x5555666677778888L);qword(expected,a,0x123456789L);
        assertEquals(expected,am.snapshot());assertEquals(List.of(a-16,a-8,a),am.qwordReads);
    }

    @Test void unalignedLimitBudgetAndGsFailuresPreserveOnlyActualPriorEffects() {
        long s=0x6000;var input=v(100,0x5000,7,8);var nv=n(300);var m=new Memory();m.put(s,RIP);var seen=new ArrayList<Long>();
        var stop=new IllegalArgumentException("finite source work");
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->StackProbe78FullState290.execute(new Entry(I,s,input,nv),m,()->0x5001L,(site,page)->{
            assertEquals(0x42247E0L,site);seen.add(page);if(seen.size()==3)throw stop;
        })));
        assertEquals(List.of(0x4001L,0x3001L,0x2001L),seen);
        assertEquals(List.of(new Write(s-16,8,input.r10Bits()),new Write(s-8,8,input.r11Bits()),new Write(0x4001,1,0),new Write(0x3001,1,0)),m.writes);
        assertTrue(m.qwordReads.isEmpty());
        var gm=new Memory();var error=new UnsupportedOperationException("GS10 unavailable");
        assertSame(error,assertThrows(UnsupportedOperationException.class,()->StackProbe78FullState290.execute(new Entry(I,s,input,nv),gm,()->{throw error;},(site,page)->{throw new AssertionError("no GS value");})));
        assertEquals(List.of(new Write(s-16,8,input.r10Bits()),new Write(s-8,8,input.r11Bits())),gm.writes);assertTrue(gm.qwordReads.isEmpty());
    }

    @Test void initialCallbackOwnsOneUnmappedPushAndKeepsForeignGs58Separate() {
        long p=0x90008;var role=new ProbeMemory();var m=role.backing;var input=v(100,0x12f8,0x123456,0xabc);var nv=n(300);
        m.put(0x8f000,0x1122334455667788L);m.put(0x8e000,0x8877665544332211L);var expected=new HashMap<>(m.snapshot());assertFalse(expected.containsKey(p-8));
        var foreignSeen=new ArrayList<OpaqueCall>();int[] gs10={0};
        var outer=new GovernmentInitialFrame162Api.Calls(){@Override public VolatileBits invoke(OpaqueCall c){foreignSeen.add(c);return input;}@Override public long readGsQword58(){return 0x58;}};
        var binder=StackProbe78Initial162Calls290.bind(I,role,outer,()->{gs10[0]++;return 0x90000;},(site,page)->{});
        assertEquals(input,binder.invoke(new OpaqueCall(0x30A2F2AL,0x42247B0L,p,input,nv)));
        var writes=List.of(new Write(p-8,8,I+0x30A2F2FL),new Write(p-24,8,input.r10Bits()),new Write(p-16,8,input.r11Bits()),new Write(0x8f000,1,0),new Write(0x8e000,1,0));
        assertEquals(writes,m.writes);qword(expected,p-8,I+0x30A2F2FL);qword(expected,p-24,input.r10Bits());qword(expected,p-16,input.r11Bits());expected.put(0x8f000L,(byte)0);expected.put(0x8e000L,(byte)0);
        assertEquals(expected,m.snapshot());assertEquals(List.of(p-24,p-16,p-8),m.qwordReads);assertEquals(1,gs10[0]);assertTrue(foreignSeen.isEmpty());
        var before=m.snapshot();int written=m.writes.size(),read=m.qwordReads.size();
        for(var foreign:List.of(new OpaqueCall(0x30A2F2BL,0x42247B0L,p,input,nv),new OpaqueCall(0x30A2F2AL,0x42247B1L,p,input,nv))){assertSame(input,binder.invoke(foreign));assertSame(foreign,foreignSeen.get(foreignSeen.size()-1));}
        assertEquals(0x58,binder.readGsQword58());assertEquals(1,gs10[0]);assertEquals(before,m.snapshot());assertEquals(written,m.writes.size());assertEquals(read,m.qwordReads.size());
        var bad=new ProbeMemory();var badBind=StackProbe78Initial162Calls290.bind(I,bad,outer,()->{bad.writeQword(p-8,0x9876);return 0;},(site,page)->{throw new AssertionError("no page");});
        assertThrows(UnsupportedOperationException.class,()->badBind.invoke(new OpaqueCall(0x30A2F2AL,0x42247B0L,p,input,nv)));
        assertEquals(List.of(p-24,p-16,p-8),bad.backing.qwordReads);
    }
}
