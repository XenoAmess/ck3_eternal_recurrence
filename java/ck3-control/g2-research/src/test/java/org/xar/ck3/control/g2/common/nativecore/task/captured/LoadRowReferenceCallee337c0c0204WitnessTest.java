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
public final class LoadRowReferenceCallee337c0c0204WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }
    static final LoopBudget NO_LOOP=(header,cursor)->{throw new AssertionError("budget");};

    @Test
    void guardRejectDirectAndAllThreeIncomingEdges() {
        long image=0x140000000L, pre=0x70000000L, ret=0xFEDCBA9876543210L;
        VolatileBits base=v(0x1010), in=q(base,base.raxBits(),0x77889900L,
                0xFEDCBA9800000000L,base.r8Bits(),base.r9Bits(),base.r10Bits(),base.r11Bits());
        NonvolatileBits saved=nv(0x2020);
        VolatileBits wanted=q(in,0xFFFFFFFFL,in.rcxBits(),in.rdxBits(),in.r8Bits(),
                in.r9Bits(),in.r10Bits(),in.r11Bits());
        for(int edge=0;edge<4;edge++) {
            Bytes m=new Bytes(); Ports noCalls=new Ports();
            long site=edge==2?0x337C882L:0x337BB8BL;
            long s=edge>=2?pre-8:pre, rip=edge>=2?image+site+5:ret;
            m.putQ(s,rip);
            Entry entry=new Entry(image,s,in,saved);
            NormalReturn wantedReturn=new NormalReturn(wanted,rip,s+8,saved);
            if(edge==0) {
                assertEquals(wantedReturn,LoadRowReferenceCallee337c0c0204.execute(entry,m,noCalls,NO_LOOP));
            } else {
                Calls bound=LoadRowReferenceCallee337c0c0204Calls.bind(image,m,noCalls,NO_LOOP);
                if(edge==1) {
                    assertEquals(wantedReturn,bound.tail(new Tail(0x337C064L,TargetKind.DIRECT_RVA,
                            0x337C0C0L,entry)));
                } else {
                    m.writeQword(pre-8,rip); // Actual parent owns its five-byte CALL return slot.
                    assertEquals(wanted,bound.invoke(new Call(site,TargetKind.DIRECT_RVA,
                            0x337C0C0L,pre,in,saved)));
                }
            }
            List<Op> expected=new ArrayList<>();
            if(edge>=2) expected.add(new Op("wq",pre-8,rip));
            expected.add(new Op("wq",s-8,saved.rsiBits()));
            expected.add(new Op("rq",s-8,saved.rsiBits()));
            expected.add(new Op("rq",s,rip));
            assertEquals(expected,m.ops);
        }
    }

    @Test
    void validOneRowUsesFreshMarkersAndThreeVirtualCallLengths() {
        long image=0x140000000L,s=0x71000000L,w=s-0x58,self=0x40000000L;
        long old=0x42000000L,fresh=0x44000000L,alloc1=0x46000000L,vt1=0x46100000L;
        long alloc2=0x47000000L,vt2=0x47100000L,receiver=old+0x10,releaseVt=0x48000000L;
        long allocFn=0xFEDC000000000008L,releaseFn=0xFEDC000000000020L,freeFn=0xFEDC000000000010L;
        long hash=0x80000001L,newBx=0xA001,newDi=0xA002,new14=0xA003,newBp=0xA004,newSi=0xA005;
        long finalRip=0xEE00112233445566L;
        VolatileBits seed=v(0x1010),in=q(seed,seed.raxBits(),self,0xABCDEF0000000001L,
                seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
        NonvolatileBits saved=nv(0x2020);
        VolatileBits a=v(0x3000),a1=q(a,fresh,a.rcxBits(),a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits());
        VolatileBits b=v(0x4000),a2=q(b,0,b.rcxBits(),b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits());
        VolatileBits c=v(0x5000),a3=q(c,c.raxBits(),c.rcxBits(),0xAABBCCDDEEFF11EFL,
                c.r8Bits(),c.r9Bits(),c.r10Bits(),c.r11Bits());
        VolatileBits a4=v(0x6000),e=v(0x7000),a5=q(e,0,e.rcxBits(),e.rdxBits(),
                e.r8Bits(),e.r9Bits(),e.r10Bits(),e.r11Bits()),a6=v(0x8000);
        NonvolatileBits n1=new NonvolatileBits(2,old,self,1,saved.r12Bits(),saved.r13Bits(),0,saved.r15Bits(),saved.xmm6());
        NonvolatileBits n2=new NonvolatileBits(old+0x48,old,self,1,saved.r12Bits(),saved.r13Bits(),0,saved.r15Bits(),saved.xmm6());
        NonvolatileBits n3=new NonvolatileBits(old+0x98,old,self,0,saved.r12Bits(),saved.r13Bits(),0,saved.r15Bits(),saved.xmm6());
        NonvolatileBits n4=new NonvolatileBits(newBx,old,self,newDi,saved.r12Bits(),saved.r13Bits(),new14,saved.r15Bits(),saved.xmm6());
        NonvolatileBits last=new NonvolatileBits(newBx,newBp,newSi,newDi,saved.r12Bits(),saved.r13Bits(),new14,saved.r15Bits(),saved.xmm6());
        Bytes m=new Bytes(); m.putQ(s,0x1122334455667788L);m.putQ(self+8,old);m.putD(self+0x10,1);
        m.putQ(self+0x20,alloc1);m.putQ(alloc1,vt1);m.putQ(vt1+8,allocFn);
        m.putD(old,(int)hash);m.putB(old+4,1);m.putQ(old+0x48,receiver);
        m.putQ(receiver,releaseVt);m.putQ(releaseVt+0x20,releaseFn);
        m.putQ(alloc2,vt2);m.putQ(vt2+0x10,freeFn);
        List<Call> expected=List.of(
            new Call(0x337C12EL,TargetKind.INDIRECT_ABSOLUTE,allocFn,w,
                    q(in,6,alloc1,480,8,allocFn,in.r10Bits(),in.r11Bits()),n1),
            new Call(0x337C161L,TargetKind.DIRECT_RVA,0x8CEEB0L,w,
                    q(a1,fresh+0xA0,fresh+0xA0,2,a1.r8Bits(),a1.r9Bits(),a1.r10Bits(),a1.r11Bits()),n1),
            new Call(0x337C198L,TargetKind.DIRECT_RVA,0x337C5D0L,w,
                    q(a2,w+0x68,self,w+0x30,hash,old+8,a2.r10Bits(),a2.r11Bits()),n2),
            new Call(0x337C1B2L,TargetKind.INDIRECT_ABSOLUTE,releaseFn,w,
                    q(a3,old+0x10,receiver,0xAABBCCDDEEFF1100L,releaseVt,a3.r9Bits(),a3.r10Bits(),a3.r11Bits()),n2),
            new Call(0x337C1C3L,TargetKind.DIRECT_RVA,0x8CEEB0L,w,a4,n3),
            new Call(0x337C1ECL,TargetKind.INDIRECT_ABSOLUTE,freeFn,w,
                    q(a5,vt2,alloc2,old,8,a5.r9Bits(),a5.r10Bits(),a5.r11Bits()),n4));
        VolatileBits[] replies={a1,a2,a3,a4,a5,a6};
        int[] lengths={3,5,5,4,5,3},seen={0};
        Calls scripted=new Ports() {
            @Override public VolatileBits invoke(Call call) {
                int k=seen[0]++;assertTrue(k<expected.size());assertEquals(expected.get(k),call);
                assertEquals(image+call.callSiteRva()+lengths[k],m.rawQ(w-8));
                if(k==0) m.writeByte(self+0x18,0);
                if(k==2) {
                    assertEquals(w+0x68,m.rawQ(w+0x20));assertEquals(0,m.rawB(w+0x68));
                }
                if(k==4) {
                    m.writeQword(w+0x40,new14);m.writeQword(w+0x48,newDi);
                    m.writeQword(w+0x60,newBx);m.writeQword(self+0x20,alloc2);
                }
                if(k==5) {
                    m.writeQword(w+0x70,newBp);m.writeQword(s-8,newSi);m.writeQword(s,finalRip);
                    m.writeQword(w+0x60,0xBADBADL); // Already restored RBX must not be read again.
                }
                return replies[k];
            }
        };
        List<Op> budget=new ArrayList<>();
        NormalReturn result=LoadRowReferenceCallee337c0c0204.execute(new Entry(image,s,in,saved),m,scripted,
                (header,cursor)->budget.add(new Op("budget",header,cursor)));
        assertEquals(6,seen[0]);assertEquals(new NormalReturn(a6,finalRip,s+8,last),result);
        assertEquals(List.of(new Op("budget",0x337C150L,fresh),
                new Op("budget",0x337C150L,fresh+0x50),new Op("budget",0x337C173L,old+0x48)),budget);
        assertEquals(fresh,m.rawQ(self+8));assertEquals(0,m.rawB(self+0x18));
        assertEquals(0,m.rawD(self+0x10));assertEquals(1,m.rawD(self+0x14));
        assertEquals(0,m.rawB(fresh+4));assertEquals(0,m.rawB(fresh+0x54));
        assertEquals(255,m.rawB(fresh+0xA4));assertEquals(0,m.rawQ(old+0x48));
    }
}
