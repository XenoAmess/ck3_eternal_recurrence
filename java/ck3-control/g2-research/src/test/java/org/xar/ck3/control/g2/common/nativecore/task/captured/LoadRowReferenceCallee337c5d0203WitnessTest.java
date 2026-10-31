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
public final class LoadRowReferenceCallee337c5d0203WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }
    static final LoadRowReferenceCallee337b7e0199Api.Float32 NO_FP = new LoadRowReferenceCallee337b7e0199Api.Float32() {
        public int convertSignedDwordToFloatBits(int n) { throw new AssertionError("convert "+n); }
        public int divideScalarFloatBits(int a,int b) { throw new AssertionError("divide"); }
        public boolean orderedAbove(int a,int b) { throw new AssertionError("compare"); }
    };
    static final LoopBudget NO_LOOP = (header,cursor) -> { throw new AssertionError("budget"); };
    @Test void signedExistingKeyDoesNotReplaceOrTouchConditionalR12Home() {
        long image=0x140000000L,s=0x400000L,self=0x500000L,out=0x600000L,key=0x700000L,table=0x100000000000L,row=table-0x2800000000L,k=0xFACEB00CL,rip=0x777788889999L;
        Bytes m=new Bytes();m.putQ(s,rip);m.putD(self+0x14,-1);m.putQ(self+8,table);m.putB(row+4,1);m.putQ(key,k);m.putQ(row+8,k);
        VolatileBits in=q(v(0x1000),0x1111,self,out,0xAABBCCDD80000000L,key,0x2222,0x3333);NonvolatileBits n=nv(0x8000);
        List<List<Long>> budgets=new ArrayList<>();LoopBudget budget=(h,c)->budgets.add(List.of(h,c));
        NormalReturn nr=LoadRowReferenceCallee337c5d0203.execute(new Entry(image,s,in,n),m,new Ports(),budget,NO_FP);
        VolatileBits want=q(in,out,-1,out,in.r8Bits(),key,0xffffffff80000000L,in.r11Bits());
        assertEquals(new NormalReturn(want,rip,s+8,n),nr);assertEquals(List.of(List.of(0x337C615L,row)),budgets);
        assertEquals(List.of(new Op("wq",s-8,n.rbpBits()),new Op("wq",s-16,n.rbxBits()),new Op("wq",s-24,n.rsiBits()),new Op("wq",s-32,n.rdiBits()),new Op("wq",s-40,n.r13Bits()),new Op("wq",s-48,n.r14Bits()),new Op("wq",s-56,n.r15Bits()),new Op("rd",self+0x14,0xffffffffL),new Op("rq",self+8,table),new Op("rb",row+4,1),new Op("rq",key,k),new Op("rq",row+8,k),new Op("wq",out,row),new Op("wb",out+8,0),new Op("rq",s-56,n.r15Bits()),new Op("rq",s-48,n.r14Bits()),new Op("rq",s-40,n.r13Bits()),new Op("rq",s-32,n.rdiBits()),new Op("rq",s-24,n.rsiBits()),new Op("rq",s-16,n.rbxBits()),new Op("rq",s-8,n.rbpBits()),new Op("rq",s,rip)),m.ops);
        assertEquals(k,m.rawQ(row+8));assertEquals(0,m.rawB(out+8));
    }

    @Test void emptySlotUsesFpPortsAndRestoresFreshConditionalHome() {
        long image=0x140000000L,s=0x500000L,w=s-0xC8,self=0x600000L,out=0x700000L,key=0x800000L,table=0x900000L,row=table+0xA0,k=0xFEED00000000AA55L;
        long fresh12=0xA001L,freshB=0xA002L,fresh14=0xA003L,freshRip=0xA004L;
        Bytes m=new Bytes();m.putQ(s,0xB001);m.putD(self+0x14,7);m.putQ(self+8,table);m.putB(row+4,0);m.putB(self+0x18,5);m.putD(self+0x10,3);m.putD(self+0x1C,0x3f400000);m.putQ(key,k);
        VolatileBits in=q(v(0x1000),0x1111,self,out,0xFACE000000000002L,key,0x2222,0x3333),ret=v(0xC000);NonvolatileBits n=nv(0xD000);
        List<String> fpEvents=new ArrayList<>();int[] cv={0};
        LoadRowReferenceCallee337b7e0199Api.Float32 fp=new LoadRowReferenceCallee337b7e0199Api.Float32(){
            public int convertSignedDwordToFloatBits(int a){fpEvents.add("c:"+a);return ++cv[0]==1?0x40e00000:0x40800000;}
            public int divideScalarFloatBits(int a,int b){fpEvents.add("d:"+Integer.toHexString(a)+":"+Integer.toHexString(b));return 0x3f000000;}
            public boolean orderedAbove(int a,int b){fpEvents.add("a:"+Integer.toHexString(a)+":"+Integer.toHexString(b));return false;}
        };
        List<Call> seen=new ArrayList<>();Calls ports=new Ports(){public VolatileBits invoke(Call c){
            seen.add(c);assertEquals(image+0x337C690,m.rawQ(w-8));
            m.writeQword(s+0x10,fresh12);m.writeQword(s-16,freshB);m.writeQword(s-48,fresh14);m.writeQword(s,freshRip);return ret;
        }};
        NormalReturn nr=LoadRowReferenceCallee337c5d0203.execute(new Entry(image,s,in,n),m,ports,NO_LOOP,fp);
        VolatileBits cvv=new VolatileBits(k,row+0x10,key+8,in.r8Bits(),key,2,in.r11Bits(),new Bits128(0x40e00000,0),new Bits128(0x3f000000,0),in.xmm2(),in.xmm3(),in.xmm4(),in.xmm5());
        NonvolatileBits cnn=new NonvolatileBits(row,s-0x57,self,(n.rdiBits()&~255L)|1,row+8,2,out,key,n.xmm6());
        assertEquals(List.of(new Call(0x337C68BL,TargetKind.DIRECT_RVA,0x87C9B0L,w,cvv,cnn)),seen);
        assertEquals(List.of("c:7","c:4","d:40800000:40e00000","a:3f000000:3f400000"),fpEvents);
        VolatileBits vv=q(ret,out,ret.rcxBits(),ret.rdxBits(),ret.r8Bits(),ret.r9Bits(),ret.r10Bits(),ret.r11Bits());
        NonvolatileBits nn=new NonvolatileBits(freshB,n.rbpBits(),n.rsiBits(),n.rdiBits(),fresh12,n.r13Bits(),fresh14,n.r15Bits(),n.xmm6());
        assertEquals(new NormalReturn(vv,freshRip,s+8,nn),nr);
        assertEquals(4,m.rawD(self+0x10));assertEquals(row,m.rawQ(out));assertEquals(1,m.rawB(out+8));assertEquals(k,m.rawQ(row+8));assertEquals(0,m.rawQ(row+0x48));
        assertEquals(List.of(new Op("wq",s+0x10,n.r12Bits()),new Op("wq",s+0x10,fresh12),new Op("rq",s+0x10,fresh12)),m.ops.stream().filter(o->o.address()==s+0x10).toList());
        assertTrue(m.ops.contains(new Op("wq",row+0x48,0)));assertTrue(m.ops.contains(new Op("wq",w-8,image+0x337C690)));
    }
}
