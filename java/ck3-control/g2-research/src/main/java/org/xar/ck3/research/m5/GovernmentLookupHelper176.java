package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.Calls;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.Entry;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.Memory;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner full body after two rejected model rounds; unknown3F5C090 remains an explicit normal port. */
public final class GovernmentLookupHelper176 {
    private GovernmentLookupHelper176() { }

    public static NormalReturn execute(Entry entry,Memory memory,Calls calls,LoopBudget budget) {
        Objects.requireNonNull(memory);Objects.requireNonNull(calls);Objects.requireNonNull(budget);
        Registers r=new Registers(entry);
        memory.writeDword(r.sp+8,(int)r.c);
        r.sp-=8;memory.writeQword(r.sp,r.bx);r.sp-=0x20;
        r.bx=Integer.toUnsignedLong((int)r.c);
        memory.writeQword(r.sp-8,r.base+0x3f5f980L);
        r.apply(calls.invoke(new OpaqueCall(0x3f5f97bL,0x3f5c090L,r.sp,r.v(),r.n())));
        r.d=memory.readUnsignedByte(r.sp+0x31);
        r.r9=r.a;
        r.c=memory.readUnsignedByte(r.sp+0x32);
        r.r10=0x100000001b3L;
        r.a=0xcbf29ce484222325L;
        r.r8=r.bx&255;
        r.r8^=r.a;
        r.a=memory.readUnsignedByte(r.sp+0x33);
        r.r8*=r.r10;
        r.r8^=r.d;
        r.d=memory.readQword(r.r9+8);
        r.r8*=r.r10;
        r.r8^=r.c;
        r.c=memory.readQword(r.r9+0x30);
        r.r8*=r.r10;
        r.r8^=r.a;
        r.r8*=r.r10;
        r.c&=r.r8;r.c<<=4;
        r.c+=memory.readQword(r.r9+0x18);
        r.a=memory.readQword(r.c+8);
        if (r.a==r.d) {
            r.a=0;
            return finish(r,memory);
        }
        r.c=memory.readQword(r.c);
        boolean found=(int)r.bx==memory.readDword(r.a+0x10);
        while (!found) {
            budget.beforeStep(0x3f5f9f0L,r.a,r.c);
            if (r.a==r.c) {
                r.a=0;
                return finish(r,memory);
            }
            r.a=memory.readQword(r.a+8);
            found=(int)r.bx==memory.readDword(r.a+0x10);
        }
        if (r.a==0) r.a=r.d;
        if (r.a==r.d) r.a=0;
        else r.a+=0x18;
        return finish(r,memory);
    }

    private static NormalReturn finish(Registers r,Memory memory) {
        r.sp+=0x20;r.bx=memory.readQword(r.sp);r.sp+=8;
        long returnRip=memory.readQword(r.sp);r.sp+=8;
        return new NormalReturn(r.v(),returnRip,r.sp,r.n());
    }

    private static final class Registers {
        final long base;
        long a,c,d,r8,r9,r10,r11,bx,bp,si,di,r12,r13,r14,r15,sp;
        Bits128 x0,x1,x2,x3,x4,x5,x6;
        Registers(Entry entry) {
            Objects.requireNonNull(entry);base=entry.imageBaseBits();sp=entry.rspBits();
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
    }
}
