package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
public final class TerminalTail4242354212WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }

@Test void outgoingTailKeepsWholeWeirdReturnAndException212() {
    // 1. Direct normal: producer must pass exact full Entry to Calls.tail and return whole NR object
    long image = 0x10000000L;
    long sp = 0x20000000L;
    long rax = 0x1111111111111111L;
    long rcx = 0x2222222222222222L;
    long rdx = 0x3333333333333333L;
    long r8 = 0x4444444444444444L;
    long r9 = 0x5555555555555555L;
    long r10 = 0x6666666666666666L;
    long r11 = 0x7777777777777777L;
    VolatileBits incomingV = q(v(0x100L), rax, rcx, rdx, r8, r9, r10, r11);
    // Replace only RDX/R8 per source 12B: LEA EDX,[R8+2] with R8=0 -> EDX=2; XOR R8D,R8D -> R8=0
    VolatileBits expectedOutV = q(incomingV, rax, rcx, 2L, 0L, r9, r10, r11);
    NonvolatileBits incomingNV = nv(0x200L);
    Entry e = new Entry(image, sp, incomingV, incomingNV);
    // Construct expected tail Entry: same image/SP/NV, V with only RDX=2/R8=0
    Entry expectedTailEntry = new Entry(image, sp, expectedOutV, incomingNV);
    Tail expectedTail = new Tail(0x424235BL, TargetKind.DIRECT_RVA, 0x42421C8L, expectedTailEntry);
    // Precreate weird NR with arbitrary different V/NV/RIP/SP (opaque tail contract permits)
    VolatileBits weirdV = v(0x400L);
    NonvolatileBits weirdNV = nv(0x500L);
    NormalReturn weirdNR = new NormalReturn(weirdV, 0x99999999L, 0x88888888L, weirdNV);
    Bytes mem = new Bytes();
    // Anonymous port: verify exact tail record, write to memory to prove no producer RET read, return weirdNR
    Calls port1 = new Calls() {
        public VolatileBits invoke(Call c) { throw new AssertionError("invoke"); }
        public NormalReturn tail(Tail t) {
            assertEquals(expectedTail.jumpSiteRva(), t.jumpSiteRva());
            assertEquals(expectedTail.kind(), t.kind());
            assertEquals(expectedTail.targetBits(), t.targetBits());
            assertEquals(expectedTail, t);
            // Write to memory at physical SP to prove producer does not RET-read
            mem.writeQword(sp, 0xDEADBEEFL);
            return weirdNR;
        }
        public long readGsQword58() { throw new AssertionError("GS"); }
    };
    NormalReturn nr = TerminalTail4242354212.execute(e, mem, port1);
    assertSame(weirdNR, nr);
    assertEquals(List.of(new Op("wq", sp, 0xDEADBEEFL)), mem.ops);

    // 2. Thrown opaque tail: exception identity preserved, no wrapper gate
    IllegalStateException thrown = new IllegalStateException("opaque tail throw");
    Calls port2 = new Calls() {
        public VolatileBits invoke(Call c) { throw new AssertionError("invoke"); }
        public NormalReturn tail(Tail t) { throw thrown; }
        public long readGsQword58() { throw new AssertionError("GS"); }
    };
    Bytes mem2 = new Bytes();
    try {
        TerminalTail4242354212.execute(e, mem2, port2);
        fail("expected throw");
    } catch (IllegalStateException ex) {
        assertSame(thrown, ex);
    }
    // No memory effects from producer on throw path
    assertEquals(0, mem2.ops.size());
}
    @Test
    void actualD44CallAndForeignFrameBoundary212() {
        long image=0x140000000L,pre=0x71000000L,next=image+0x4232D49L,gs=0xFEDCBA9876543210L;
        VolatileBits seed=v(0x110000001000L);
        VolatileBits in=q(seed,0xAA00000000000011L,3,0xBB00000000000022L,
                0xCC00000000000033L,seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
        NonvolatileBits n=nv(0x220000002000L);
        VolatileBits actualV=v(0x330000003000L),foreignV=v(0x440000004000L);
        NormalReturn good=new NormalReturn(actualV,next,pre,n);
        NormalReturn bad=new NormalReturn(actualV,next+1,pre,n);
        Entry childTail=new Entry(image,pre-8,q(in,in.raxBits(),3,2,0,in.r9Bits(),in.r10Bits(),in.r11Bits()),n);
        Tail expectedTail=new Tail(0x424235BL,TargetKind.DIRECT_RVA,0x42421C8L,childTail);
        Entry foreignEntry=new Entry(image,pre+0x100,foreignV,nv(0x550000005000L));
        Tail foreignTail=new Tail(0x424235BL,TargetKind.DIRECT_RVA,0x42421C8L,foreignEntry);
        NormalReturn foreignNR=new NormalReturn(foreignV,0x8877665544332211L,0xFFEEDDCCBBAA0099L,nv(0x660000006000L));
        Bytes m=new Bytes();List<Call> seen=new ArrayList<>();
        boolean[] badMode={false};int[] outgoing={0},foreignTails={0},gsReads={0};
        Calls fallback=new Ports() {
            @Override public VolatileBits invoke(Call call) { seen.add(call);return foreignV; }
            @Override public NormalReturn tail(Tail transfer) {
                if(transfer==foreignTail) {
                    foreignTails[0]++;assertSame(foreignEntry,transfer.entry());return foreignNR;
                }
                outgoing[0]++;assertEquals(expectedTail,transfer);assertEquals(next,m.rawQ(pre-8));
                return badMode[0]?bad:good;
            }
            @Override public long readGsQword58() { gsReads[0]++;return gs; }
        };
        Calls bound=TerminalTail4242354212Calls.bind(image,m,fallback);
        Call matched=new Call(0x4232D44L,TargetKind.DIRECT_RVA,0x4242354L,pre,in,n);
        m.writeQword(pre-8,next);
        assertSame(actualV,bound.invoke(matched));
        assertEquals(List.of(new Op("wq",pre-8,next)),m.ops);
        badMode[0]=true;m.writeQword(pre-8,next);
        RuntimeException rejected=assertThrows(RuntimeException.class,()->bound.invoke(matched));
        assertTrue(rejected instanceof IllegalArgumentException || rejected instanceof IllegalStateException);
        assertEquals(2,outgoing[0]);
        List<Call> foreign=List.of(
                new Call(0x4232D45L,TargetKind.DIRECT_RVA,0x4242354L,pre,in,n),
                new Call(0x4232D44L,TargetKind.DIRECT_RVA,0x4242355L,pre,in,n),
                new Call(0x4232D44L,TargetKind.INDIRECT_ABSOLUTE,0x4242354L,pre,in,n));
        for(Call call:foreign) { assertSame(foreignV,bound.invoke(call));assertSame(call,seen.get(seen.size()-1)); }
        assertEquals(3,seen.size());assertSame(foreignNR,bound.tail(foreignTail));assertEquals(gs,bound.readGsQword58());
        assertEquals(1,foreignTails[0]);assertEquals(1,gsReads[0]);
        assertEquals(List.of(new Op("wq",pre-8,next),new Op("wq",pre-8,next)),m.ops);
    }

}
