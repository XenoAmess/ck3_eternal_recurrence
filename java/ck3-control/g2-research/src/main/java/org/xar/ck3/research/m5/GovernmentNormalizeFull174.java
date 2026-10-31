package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Calls;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Entry;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Memory;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner implementation after both model candidates truncated. Frozen dispatch DATA belongs to this held body. */
public final class GovernmentNormalizeFull174 {
    private GovernmentNormalizeFull174() { }
    private static final int[] FIVE_TARGETS={0x30a2d39,0x30a2d0f,0x30a2d16,0x30a2d1d,0x30a2d24,0x30a2d2b,0x30a2d32,0x30a2d39};
    private static final int[] OTHER_TARGETS={0x30a2e1f,0x30a2df5,0x30a2dfc,0x30a2e03,0x30a2e0a,0x30a2e11,0x30a2e18,0x30a2e1f};
    private static final int[] KEYS={0x165,0x2807,0x27e2,0x27e3,0x27e4,0x27e5,0x38f8,0x165};

    public static NormalReturn execute(Entry entry, Memory memory, Calls calls) {
        Objects.requireNonNull(memory); Objects.requireNonNull(calls);
        Registers r=new Registers(entry);
        memory.writeQword(r.sp+8,r.bx);
        memory.writeQword(r.sp+0x10,r.si);
        r.sp-=8; memory.writeQword(r.sp,r.di); r.sp-=0x40;
        boolean five=memory.readUnsignedByte(r.c+0x4d6)==5;
        r.si=r.d;
        int incoming=(int)r.r8;
        if (five ? incoming!=1 && incoming!=7 : incoming==7) {
            r.bx=memory.readQword(r.sp+0x50);
            r.a=Integer.toUnsignedLong(incoming);
            return finish(r,memory,true);
        }

        r.bx=r.c+0x18;
        if (Integer.compareUnsigned(incoming,7)<=0) {
            r.c=r.base;
            r.a=(long)incoming;
            r.a=Integer.toUnsignedLong((five?FIVE_TARGETS:OTHER_TARGETS)[incoming]);
            r.a+=r.c;
            r.c=Integer.toUnsignedLong(KEYS[incoming]);
        } else {
            r.c=0x165;
        }
        r.call(five?0x30a2d3eL:0x30a2e24L,0x3f4f8e0L,memory,calls);
        r.c=calls.readGsQword58();
        r.di=r.a;
        r.r8=0x158;
        r.d=memory.readQword(r.c);
        if (memory.readUnsignedByte(r.r8+r.d)==0) {
            r.c=Integer.toUnsignedLong(memory.readDword(r.base+0x5c6a9dcL));
            if ((int)r.c<100000) {
                r.c=0x10000;
                r.call(five?0x30a2d73L:0x30a2e59L,0x3f5f970L,memory,calls);
                if (r.a!=0) {
                    memory.writeQword(r.sp+0x38,r.bx);
                    r.c=r.base+(five?0x48b7b80L:0x48b7bd0L);
                    memory.writeQword(r.sp+0x30,r.si);
                    r.d=r.base+0x48b7a48L;
                    memory.writeQword(r.sp+0x28,r.di);
                    r.r8=five?0x11e:0x12c;
                    memory.writeQword(r.sp+0x20,r.c);
                    r.c=r.a;
                    r.call(five?0x30a2da8L:0x30a2e8eL,0x2850890L,memory,calls);
                    r.a=1;
                    r.a=Integer.toUnsignedLong(memory.lockedXaddDword(r.base+0x5c6a9dcL,(int)r.a));
                }
            }
        }
        r.a=five?3:7;
        return finish(r,memory,false);
    }

    private static NormalReturn finish(Registers r,Memory memory,boolean rbxAlreadyRestored) {
        if (!rbxAlreadyRestored) r.bx=memory.readQword(r.sp+0x50);
        r.si=memory.readQword(r.sp+0x58);
        r.sp+=0x40;
        r.di=memory.readQword(r.sp); r.sp+=8;
        long returnRip=memory.readQword(r.sp); r.sp+=8;
        return new NormalReturn(r.v(),returnRip,r.sp,r.n());
    }

    private static final class Registers {
        final long base;
        long a,c,d,r8,r9,r10,r11,bx,bp,si,di,r12,r13,r14,r15,sp;
        Bits128 x0,x1,x2,x3,x4,x5,x6;
        Registers(Entry entry) {
            Objects.requireNonNull(entry); base=entry.imageBaseBits(); sp=entry.rspBits();
            NonvolatileBits n=entry.nonvolatileBits();
            bx=n.rbxBits();bp=n.rbpBits();si=n.rsiBits();di=n.rdiBits();
            r12=n.r12Bits();r13=n.r13Bits();r14=n.r14Bits();r15=n.r15Bits();x6=n.xmm6();
            apply(entry.volatileBits());
        }
        VolatileBits v() { return new VolatileBits(a,c,d,r8,r9,r10,r11,x0,x1,x2,x3,x4,x5); }
        NonvolatileBits n() { return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,x6); }
        void apply(VolatileBits value) {
            Objects.requireNonNull(value);a=value.raxBits();c=value.rcxBits();d=value.rdxBits();
            r8=value.r8Bits();r9=value.r9Bits();r10=value.r10Bits();r11=value.r11Bits();
            x0=value.xmm0();x1=value.xmm1();x2=value.xmm2();x3=value.xmm3();x4=value.xmm4();x5=value.xmm5();
        }
        void call(long site,long target,Memory memory,Calls calls) {
            memory.writeQword(sp-8,base+site+5);
            apply(calls.invoke(new OpaqueCall(site,target,sp,v(),n())));
        }
    }
}
