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

public final class LoadRowReferenceCallee337c200207ColdWitnessTest {
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
    void existingKeyUsesDwordAndThenCdqe207() {
        long image=0x140000000L,s=0x71000000L,self=0x40000000L,out=0x42000000L;
        long table=0x4000000000L,row=0x18000002D0L,keyPointer=0x43000000L;
        long key=0xEEDDCCBBAA998877L,hash=0xFEDCBA9880000009L;
        long originalRip=0x1122334455667788L,freshRip=0xFFEEDDCCBBAA0099L;
        VolatileBits seed=v(0x100000001000L);
        VolatileBits in=q(seed,seed.raxBits(),self,out,hash,keyPointer,seed.r10Bits(),seed.r11Bits());
        NonvolatileBits n=nv(0x8899AABBCCDDEE00L);
        Bytes m=new Bytes();m.putQ(s,originalRip);m.putQ(s+0x18,0xAABBCCDDEEFF0011L);
        m.putQ(self+8,table);m.putD(self+0x14,0x8000000F);
        m.putB(row+4,1);m.putQ(row+8,key);m.putQ(keyPointer,key);
        m.putQ(out+8,0x88776655443322FFL);
        int[] steps={0};
        LoopBudget budget=(header,cursor)->{
            assertEquals(0x337C250L,header);assertEquals(row,cursor);assertEquals(1,++steps[0]);
            assertEquals(new Op("rq",keyPointer,key),m.ops.get(m.ops.size()-1));
            m.writeQword(s,freshRip);
        };
        NormalReturn got=LoadRowReferenceCallee337c200207.execute(new Entry(image,s,in,n),m,new Ports(),budget,NO_FLOAT);
        VolatileBits wanted=q(in,out,0x8000000FL,out,hash,keyPointer,in.r10Bits(),in.r11Bits());
        assertEquals(new NormalReturn(wanted,freshRip,s+8,n),got);assertEquals(1,steps[0]);
        assertEquals(row,m.rawQ(out));assertEquals(0x8877665544332200L,m.rawQ(out+8));
        assertEquals(n.rbxBits(),m.rawQ(s+0x10));assertEquals(0xAABBCCDD80000009L,m.rawQ(s+0x18));
        assertEquals(List.of(
            new Op("wq",s+0x10,n.rbxBits()),new Op("wd",s+0x18,0x80000009L),
            new Op("wq",s-8,n.rbpBits()),new Op("wq",s-0x10,n.rsiBits()),
            new Op("wq",s-0x18,n.rdiBits()),new Op("wq",s-0x20,n.r12Bits()),
            new Op("wq",s-0x28,n.r13Bits()),new Op("wq",s-0x30,n.r14Bits()),
            new Op("wq",s-0x38,n.r15Bits()),new Op("rd",self+0x14,0x8000000FL),
            new Op("rq",self+8,table),new Op("rb",row+4,1),new Op("rq",keyPointer,key),
            new Op("wq",s,freshRip),new Op("rq",row+8,key),
            new Op("wq",out,row),new Op("wb",out+8,0),new Op("rq",s+0x10,n.rbxBits()),
            new Op("rq",s-0x38,n.r15Bits()),new Op("rq",s-0x30,n.r14Bits()),
            new Op("rq",s-0x28,n.r13Bits()),new Op("rq",s-0x20,n.r12Bits()),
            new Op("rq",s-0x18,n.rdiBits()),new Op("rq",s-0x10,n.rsiBits()),
            new Op("rq",s-8,n.rbpBits()),new Op("rq",s,freshRip)),m.ops);
    }

    @Test
    void emptyRowUsesSixthDescriptorAndFreshEpilogue207() {
        long image=0x140000000L,s=0x72000000L,w=s-0x118,self=0x45000000L,out=0x46000000L;
        long table=0x47000000L,row=0x470002D0L,keyPointer=0x48000000L;
        long key=0xABCDEF0011223344L,hash=0xFFEEDDCC00000009L;
        long oldDescriptor=0x49000000L,descriptor=0x4A000000L,receiver=0x4B000000L,vptr=0x4C000000L;
        long target=0xFEDC112233445566L,decoyFifth=0x4D000000L,finalRip=0xFFEEDDCCBBAA0099L;
        VolatileBits seed=v(0x110000001000L);
        VolatileBits in=q(seed,seed.raxBits(),self,out,hash,keyPointer,seed.r10Bits(),seed.r11Bits());
        NonvolatileBits n=nv(0x8899AABBCCDDEE00L);
        NonvolatileBits restored=new NonvolatileBits(0xFA01000000000001L,0xFA02000000000002L,
                0xFA03000000000003L,0xFA04000000000004L,0xFA05000000000005L,
                0xFA06000000000006L,0xFA07000000000007L,0xFA08000000000008L,n.xmm6());
        VolatileBits reply=v(0x330000001000L);
        Bytes m=new Bytes();m.putQ(s,0x1122334455667788L);m.putQ(s+0x18,0xAABBCCDDEEFF0011L);
        m.putQ(s+0x28,decoyFifth);m.putQ(s+0x30,oldDescriptor);
        m.putQ(oldDescriptor+0x38,0);m.putQ(descriptor+0x38,receiver);m.putQ(receiver,vptr);m.putQ(vptr,target);
        m.putQ(self+8,table);m.putD(self+0x14,15);m.putD(self+0x10,0);
        m.putB(self+0x18,1);m.putD(self+0x1C,0x3F000000);
        m.putQ(row,0xA1B2C300DEADBEEFL);m.putQ(row+8,0x5566778899AABBCCL);m.putQ(keyPointer,key);
        m.putQ(out+8,0x88776655443322FFL);
        int[] fpStep={0},seen={0};
        Float32 fp=new Float32() {
            public int convertSignedDwordToFloatBits(int value) {
                int k=fpStep[0]++;assertTrue(k<2);assertEquals(k==0?1:15,value);
                return k==0?0x3F800000:0x41700000;
            }
            public int divideScalarFloatBits(int a,int b) {
                assertEquals(2,fpStep[0]++);assertEquals(0x3F800000,a);assertEquals(0x41700000,b);
                return 0x3D888889;
            }
            public boolean orderedAbove(int a,int b) {
                assertEquals(3,fpStep[0]++);assertEquals(0x3D888889,a);assertEquals(0x3F000000,b);
                m.writeQword(s+0x30,descriptor);return false;
            }
        };
        VolatileBits callV=new VolatileBits(vptr,receiver,row+0x10,hash,keyPointer,in.r10Bits(),in.r11Bits(),
                new Bits128(0x41700000L,0),new Bits128(0x3D888889L,0),in.xmm2(),in.xmm3(),in.xmm4(),in.xmm5());
        NonvolatileBits callN=new NonvolatileBits(row,s-0x4F,self,out,0,row+0x10,
                0x8899AABBCCDDEE01L,n.r15Bits(),n.xmm6());
        Calls ports=new Ports() {
            @Override public VolatileBits invoke(Call call) {
                assertEquals(1,++seen[0]);assertEquals(4,fpStep[0]);
                assertEquals(new Call(0x337C2CAL,TargetKind.INDIRECT_ABSOLUTE,target,w,callV,callN),call);
                assertEquals(List.of(new Op("rq",vptr,target),new Op("wq",w-8,image+0x337C2CCL)),
                        m.ops.subList(m.ops.size()-2,m.ops.size()));
                assertEquals(row+0x10,m.rawQ(s+8));assertEquals(0,m.rawQ(row+0x48));
                m.writeDword(self+0x10,41);m.writeQword(s+0x10,restored.rbxBits());
                m.writeQword(s-8,restored.rbpBits());m.writeQword(s-0x10,restored.rsiBits());
                m.writeQword(s-0x18,restored.rdiBits());m.writeQword(s-0x20,restored.r12Bits());
                m.writeQword(s-0x28,restored.r13Bits());m.writeQword(s-0x30,restored.r14Bits());
                m.writeQword(s-0x38,restored.r15Bits());m.writeQword(s,finalRip);return reply;
            }
        };
        NormalReturn got=LoadRowReferenceCallee337c200207.execute(new Entry(image,s,in,n),m,ports,
                (header,cursor)->{throw new AssertionError("empty budget");},fp);
        assertEquals(new NormalReturn(q(reply,out,reply.rcxBits(),reply.rdxBits(),reply.r8Bits(),
                reply.r9Bits(),reply.r10Bits(),reply.r11Bits()),finalRip,s+8,restored),got);
        assertEquals(4,fpStep[0]);assertEquals(1,seen[0]);
        assertEquals(42,m.rawD(self+0x10));assertEquals(row,m.rawQ(out));
        assertEquals(0x8877665544332201L,m.rawQ(out+8));assertEquals(0xA1B2C30100000009L,m.rawQ(row));
        assertEquals(key,m.rawQ(row+8));assertEquals(reply.raxBits(),m.rawQ(row+0x48));
        assertEquals(0xAABBCCDD00000009L,m.rawQ(s+0x18));assertEquals(decoyFifth,m.rawQ(s+0x28));
        assertEquals(List.of(
            new Op("rd",self+0x14,15),new Op("rq",self+8,table),new Op("rb",row+4,0),
            new Op("rb",self+0x18,1),new Op("rd",self+0x10,0),new Op("rd",self+0x1C,0x3F000000L),
            new Op("rb",row+4,0),new Op("rq",keyPointer,key),new Op("rq",s+0x30,descriptor),
            new Op("rq",descriptor+0x38,receiver),new Op("rq",receiver,vptr),new Op("rq",vptr,target),
            new Op("rd",self+0x10,41),new Op("rq",s+0x10,restored.rbxBits()),
            new Op("rq",s-0x38,restored.r15Bits()),new Op("rq",s-0x30,restored.r14Bits()),
            new Op("rq",s-0x28,restored.r13Bits()),new Op("rq",s-0x20,restored.r12Bits()),
            new Op("rq",s-0x18,restored.rdiBits()),new Op("rq",s-0x10,restored.rsiBits()),
            new Op("rq",s-8,restored.rbpBits()),new Op("rq",s,finalRip)),
                m.ops.stream().filter(op->op.kind().startsWith("r")).toList());
    }
}
