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
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api.Float32;

public final class LoadRowReferenceSelf337c593210WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static VolatileBits q(VolatileBits b,long a,long c,long d,long r8,long r9,long r10,long r11) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());
    }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }
    static final Float32 NO_FLOAT=new Float32() {
        public int convertSignedDwordToFloatBits(int value) { throw new AssertionError("convert"); }
        public int divideScalarFloatBits(int a,int b) { throw new AssertionError("divide"); }
        public boolean orderedAbove(int a,int b) { throw new AssertionError("compare"); }
    };

    @Test
    void parentGrowthExecutesActualSelfChildProbe210() {
        long image=0x140000000L,s=0x71000000L,w=s-0x118,child=s-0x120;
        long self=0x40000000L,out=0x41000000L,table=0x42000000L,row=0x420002D0L;
        long newTable=0x43000000L,newRow=0x43000320L,keyPointer=0x44000000L,key=0xEEDDCCBBAA998877L;
        long hash=0xAABBCCDD00000009L,oldContext=0xABCDEF0011223344L,newContext=0xFEDCBA9876543210L;
        long rip=0x8877665544332211L;
        VolatileBits seed=v(0x110000001000L);
        VolatileBits in=q(seed,seed.raxBits(),self,out,hash,keyPointer,seed.r10Bits(),seed.r11Bits());
        NonvolatileBits n=nv(0x8899AABBCCDDEE00L);
        NonvolatileBits local=new NonvolatileBits(row,s-0x4F,self,out,keyPointer,n.r13Bits(),
                0x8899AABBCCDDEE01L,n.r15Bits(),n.xmm6());
        VolatileBits aSeed=v(0x330000001000L),a=q(aSeed,4,aSeed.rcxBits(),aSeed.rdxBits(),
                aSeed.r8Bits(),aSeed.r9Bits(),aSeed.r10Bits(),aSeed.r11Bits());
        VolatileBits b=v(0x440000001000L);
        Bytes m=new Bytes();m.putQ(s,rip);m.putQ(s+0x18,0xA1B2C3D455667788L);m.putQ(s+0x30,oldContext);
        m.putQ(self+8,table);m.putD(self+0x14,15);m.putB(self+0x18,0);
        m.putB(row+4,0);m.putQ(keyPointer,key);m.putQ(out+8,0x88776655443322FFL);
        List<Call> expected=List.of(
                new Call(0x337C55CL,TargetKind.DIRECT_RVA,0x86E160L,w,
                        q(in,9,16,1,hash,keyPointer,in.r10Bits(),in.r11Bits()),local),
                new Call(0x337C56BL,TargetKind.DIRECT_RVA,0x337C0C0L,w,
                        q(a,4,self,4,a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),local));
        int[] seen={0},steps={0};
        Calls fallback=new Ports() {
            @Override public VolatileBits invoke(Call call) {
                int k=seen[0]++;assertTrue(k<2);assertEquals(expected.get(k),call);
                assertEquals(image+(k==0?0x337C561L:0x337C570L),m.rawQ(w-8));
                if(k==0) return a;
                m.writeQword(self+8,newTable);m.writeDword(self+0x14,15);m.writeByte(newRow+4,1);
                m.writeQword(newRow+8,key);m.writeDword(s+0x18,0x8000000A);m.writeQword(s+0x30,newContext);
                return b;
            }
        };
        LoopBudget budget=(header,cursor)->{
            assertEquals(0x337C250L,header);assertEquals(newRow,cursor);assertEquals(1,++steps[0]);
            assertEquals(0x8000000A,m.rawD(child+0x18));assertEquals(row,m.rawQ(child+0x10));
            assertEquals(newContext,m.rawQ(child+0x30));assertEquals(s+8,m.rawQ(child+0x28));
        };
        Calls bound=LoadRowReferenceSelf337c593210Calls.bind(image,m,fallback,budget,NO_FLOAT);
        NormalReturn got=LoadRowReferenceCallee337c200207.execute(new Entry(image,s,in,n),m,bound,budget,NO_FLOAT);
        assertEquals(new NormalReturn(q(b,out,15,out,0x8000000AL,keyPointer,b.r10Bits(),b.r11Bits()),rip,s+8,n),got);
        assertEquals(2,seen[0]);assertEquals(1,steps[0]);assertEquals(newRow,m.rawQ(out));
        assertEquals(0x8877665544332200L,m.rawQ(out+8));assertEquals(0xA1B2C3D48000000AL,m.rawQ(s+0x18));
        assertEquals(0,m.rawB(s+8));assertEquals(s+8,m.rawQ(w+0x20));assertEquals(newContext,m.rawQ(w+0x28));
        assertEquals(List.of(new Op("wq",w-8,image+0x337C561L),new Op("wq",w-8,image+0x337C570L),
                new Op("wq",w-8,image+0x337C598L)),m.ops.stream().filter(op->op.kind().equals("wq")&&op.address()==w-8).toList());
        assertEquals(List.of(new Op("rq",w-8,image+0x337C598L)),
                m.ops.stream().filter(op->op.kind().equals("rq")&&op.address()==w-8).toList());
        assertEquals(List.of(new Op("rq",s,rip)),m.ops.stream().filter(op->op.kind().equals("rq")&&op.address()==s).toList());
        assertEquals(List.of(new Op("rq",s+0x30,newContext)),
                m.ops.stream().filter(op->op.kind().equals("rq")&&op.address()==s+0x30).toList());
        assertTrue(m.ops.stream().noneMatch(op->op.kind().equals("rq")&&op.address()==child+0x30));
    }

    @Test
    void foreignIdentityAndException210() {
        long image=0x140000000L,pre=0x72000000L,gs=0xFEDCBA9876543210L;
        Bytes m=new Bytes();VolatileBits in=v(0x110000001000L),reply=v(0x220000002000L);NonvolatileBits n=nv(0x330000003000L);
        List<Call> foreign=List.of(new Call(0x337BBA6L,TargetKind.DIRECT_RVA,0x337C200L,pre,in,n),
                new Call(0x337C593L,TargetKind.DIRECT_RVA,0x337C201L,pre,in,n),
                new Call(0x337C593L,TargetKind.INDIRECT_ABSOLUTE,0x337C200L,pre,in,n));
        Call throwing=new Call(0x337C592L,TargetKind.DIRECT_RVA,0x337C200L,pre,in,n);
        Entry entry=new Entry(image,pre,in,n);Tail transfer=new Tail(0x337C593L,TargetKind.DIRECT_RVA,0x337C200L,entry);
        NormalReturn tailReply=new NormalReturn(reply,0xFFEEDDCCBBAA0099L,pre+8,n);
        RuntimeException marker=new IllegalStateException("foreign callback");
        List<Call> calls=new ArrayList<>();int[] tails={0},gsReads={0},budgets={0};
        Calls fallback=new Ports() {
            @Override public VolatileBits invoke(Call call) { calls.add(call);if(call==throwing) throw marker;return reply; }
            @Override public NormalReturn tail(Tail tail) {
                tails[0]++;assertSame(transfer,tail);assertSame(entry,tail.entry());return tailReply;
            }
            @Override public long readGsQword58() { gsReads[0]++;return gs; }
        };
        Calls bound=LoadRowReferenceSelf337c593210Calls.bind(image,m,fallback,
                (header,cursor)->{budgets[0]++;throw new AssertionError("foreign budget");},NO_FLOAT);
        for(Call call:foreign) { assertSame(reply,bound.invoke(call));assertSame(call,calls.get(calls.size()-1)); }
        assertSame(tailReply,bound.tail(transfer));assertEquals(gs,bound.readGsQword58());
        assertSame(marker,assertThrows(IllegalStateException.class,()->bound.invoke(throwing)));
        assertSame(throwing,calls.get(3));assertEquals(4,calls.size());assertEquals(1,tails[0]);assertEquals(1,gsReads[0]);
        assertEquals(0,budgets[0]);assertEquals(List.of(),m.ops);
    }
}
