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
public final class LoadRowReferenceCallee337c200207GrowthWitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }

    @Test void growthUsesFreshHomesAndSelfPortWhileFatalNeverReturns() {
        for(boolean fatal:new boolean[]{false,true}) {
            long image=0x140000000L,s=0x73000000L,w=s-0x118,bp=s-0x4F;
            long self=0x51000000L,out=0x52000000L,key=0x53000000L,table=0x54000000L;
            long context=0xDD00000000000033L,newBx=0xEE00000000000044L,newRip=0xFF00112233445566L;
            int newHash=0x80000009;
            VolatileBits base=v(0x1000),in=q(base,base.raxBits(),self,out,0xAABBCCDD00000000L,key,base.r10Bits(),base.r11Bits());
            VolatileBits av=v(0x3000),a=q(av,fatal?31:2,av.rcxBits(),av.rdxBits(),av.r8Bits(),av.r9Bits(),av.r10Bits(),av.r11Bits());
            VolatileBits b=v(0x4000),c=v(0x5000);NonvolatileBits n=nv(0x6000);
            NonvolatileBits local=new NonvolatileBits(table,bp,self,out,key,n.r13Bits(),
                    (n.r14Bits()&~255L)|1,n.r15Bits(),n.xmm6());
            Bytes m=new Bytes();m.putQ(s,0x1122334455667788L);m.putQ(self+8,table);
            m.putD(self+0x14,0);m.putB(self+0x18,0);m.putB(table+4,0);m.putQ(s+0x30,0xCC00000000000022L);
            List<Call> expected=new ArrayList<>();
            expected.add(new Call(0x337C55CL,TargetKind.DIRECT_RVA,0x86E160L,w,
                    q(in,0,1,1,in.r8Bits(),key,in.r10Bits(),in.r11Bits()),local));
            if(fatal) {
                expected.add(new Call(0x337C5BDL,TargetKind.DIRECT_RVA,0x86F210L,w,
                        q(a,a.raxBits(),s+8,self,a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),local));
                expected.add(new Call(0x337C5C2L,TargetKind.DIRECT_RVA,0x4232CF4L,w,b,local));
            } else {
                expected.add(new Call(0x337C56BL,TargetKind.DIRECT_RVA,0x337C0C0L,w,
                        q(a,a.raxBits(),self,2,a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),local));
                expected.add(new Call(0x337C593L,TargetKind.DIRECT_RVA,0x337C200L,w,
                        q(b,s+8,self,out,0x80000009L,key,b.r10Bits(),b.r11Bits()),local));
            }
            int[] count={0};VolatileBits[] replies={a,b,c};
            Calls ports=new Ports(){public VolatileBits invoke(Call call){
                int k=count[0]++;assertTrue(k<3);assertEquals(expected.get(k),call);
                assertEquals(image+call.callSiteRva()+5,m.rawQ(w-8));
                if(!fatal&&k==1) {m.writeQword(s+0x30,context);m.writeDword(s+0x18,newHash);}
                if(!fatal&&k==2) {
                    assertEquals(s+8,m.rawQ(w+0x20));assertEquals(context,m.rawQ(w+0x28));
                    assertEquals(0,m.rawB(s+8));m.writeQword(s+0x10,newBx);m.writeQword(s,newRip);
                }
                return replies[k];
            }};
            LoadRowReferenceCallee337b7e0199Api.Float32 fp=new LoadRowReferenceCallee337b7e0199Api.Float32(){
                public int convertSignedDwordToFloatBits(int value){throw new AssertionError("unexpected FP");}
                public int divideScalarFloatBits(int a,int b){throw new AssertionError("unexpected FP");}
                public boolean orderedAbove(int a,int b){throw new AssertionError("unexpected FP");}
            };
            LoopBudget budget=(h,a0)->{throw new AssertionError("unexpected budget");};
            if(fatal) {
                UnsupportedOperationException ex=assertThrows(UnsupportedOperationException.class,
                        ()->LoadRowReferenceCallee337c200207.execute(new Entry(image,s,in,n),m,ports,budget,fp));
                assertEquals("INT3 reached",ex.getMessage());
                assertTrue(m.ops.stream().noneMatch(o->o.kind().equals("rq")&&o.address()==s));
            } else {
                NormalReturn got=LoadRowReferenceCallee337c200207.execute(new Entry(image,s,in,n),m,ports,budget,fp);
                NonvolatileBits restored=new NonvolatileBits(newBx,n.rbpBits(),n.rsiBits(),n.rdiBits(),
                        n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
                assertEquals(new NormalReturn(q(c,out,c.rcxBits(),c.rdxBits(),c.r8Bits(),c.r9Bits(),c.r10Bits(),c.r11Bits()),newRip,s+8,restored),got);
                assertEquals(0x80000009,m.rawD(s+0x18));
            }
            assertEquals(3,count[0]);
        }
    }
}
