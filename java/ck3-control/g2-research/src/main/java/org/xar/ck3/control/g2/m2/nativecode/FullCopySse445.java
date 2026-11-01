package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Actual SSE forward component; only the owned GPR/N/low128/DF projection is represented. */
public final class FullCopySse445 {
    private FullCopySse445() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,FullCopy437Api.Calls calls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        var entry=input.entry();var initial=entry.volatileBits();
        long rax=initial.raxBits(),rcx=initial.rcxBits(),rdx=initial.rdxBits(),r8=initial.r8Bits();
        long r9=initial.r9Bits(),r10=initial.r10Bits(),r11=initial.r11Bits();
        Bits128 x0=initial.xmm0(),x1=initial.xmm1(),x2=initial.xmm2(),x3=initial.xmm3();
        Bits128 x4=initial.xmm4(),x5=initial.xmm5();

        if(Long.compareUnsigned(r8,0x800L)>0) {
            int flag=memory.readUnsignedByte(entry.imageBaseBits()+0x5C5CBB0L);
            if((flag&~0xff)!=0)throw new IllegalArgumentException("actual unsigned BYTE required");
            if((flag&2)!=0)return FullCopyRep4226840.execute(input,memory);
        }
        x0=Objects.requireNonNull(memory.read128(rdx));
        x5=Objects.requireNonNull(memory.read128(rdx+r8-0x10L));
        if(Long.compareUnsigned(r8,0x80L)>0) {
            r9=(rcx&0xfL)-0x10L;
            rcx-=r9;rdx-=r9;r8+=r9;
            if(Long.compareUnsigned(r8,0x80L)>0) {
                do {
                    input.budget().beforeStep(0x4226CF0L,rcx);
                    x1=Objects.requireNonNull(memory.read128(rdx));
                    x2=Objects.requireNonNull(memory.read128(rdx+0x10L));
                    x3=Objects.requireNonNull(memory.read128(rdx+0x20L));
                    x4=Objects.requireNonNull(memory.read128(rdx+0x30L));
                    memory.write128(rcx,x1);memory.write128(rcx+0x10L,x2);
                    memory.write128(rcx+0x20L,x3);memory.write128(rcx+0x30L,x4);
                    x1=Objects.requireNonNull(memory.read128(rdx+0x40L));
                    x2=Objects.requireNonNull(memory.read128(rdx+0x50L));
                    x3=Objects.requireNonNull(memory.read128(rdx+0x60L));
                    x4=Objects.requireNonNull(memory.read128(rdx+0x70L));
                    memory.write128(rcx+0x40L,x1);memory.write128(rcx+0x50L,x2);
                    memory.write128(rcx+0x60L,x3);memory.write128(rcx+0x70L,x4);
                    rcx+=0x80L;rdx+=0x80L;r8-=0x80L;
                }while(Long.compareUnsigned(r8,0x80L)>=0);
            }
        }

        r9=(r8+0xfL)&~0xfL;
        r11=r9>>>4;
        r11=Integer.toUnsignedLong(memory.readDword(r10+0x6090088L+(r11<<2)))+r10;
        long targetRva=r11-entry.imageBaseBits();
        int first;
        if(targetRva==0x4226D79L)first=0;
        else if(targetRva==0x4226D87L)first=1;
        else if(targetRva==0x4226D95L)first=2;
        else if(targetRva==0x4226DA3L)first=3;
        else if(targetRva==0x4226DB1L)first=4;
        else if(targetRva==0x4226DBFL)first=5;
        else if(targetRva==0x4226DCDL)first=6;
        else if(targetRva==0x4226DDBL)first=7;
        else if(targetRva==0x4226DE2L)first=8;
        else {
            var current=bits(rax,rcx,rdx,r8,r9,r10,r11,x0,x1,x2,x3,x4,x5);
            var tail=new GovernmentCrtBoundary185Api.Tail(0x4226D76L,
                    GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,r11,
                    new GovernmentCrtBoundary185Api.Entry(entry.imageBaseBits(),entry.rspBits(),current,entry.nonvolatileBits()));
            return calls.tail(new FullCopy437Api.TailFrame(tail,input.directionFlagSet()));
        }
        // Seven fixed fallthrough instruction pairs, beginning only at an exact family label.
        for(int step=first;step<7;step++) {
            long offset=-0x80L+step*0x10L;
            x1=Objects.requireNonNull(memory.read128(rdx+r9+offset));
            memory.write128(rcx+r9+offset,x1);
        }
        if(first<8)memory.write128(rcx+r8-0x10L,x5);
        memory.write128(rax,x0);
        long returned=memory.readQword(entry.rspBits());
        var normal=new GovernmentCrtBoundary185Api.NormalReturn(
                bits(rax,rcx,rdx,r8,r9,r10,r11,x0,x1,x2,x3,x4,x5),returned,
                entry.rspBits()+8,entry.nonvolatileBits());
        return new FullCopy437Api.CallResult(normal,input.directionFlagSet());
    }

    private static VolatileBits bits(long rax,long rcx,long rdx,long r8,long r9,long r10,long r11,
            Bits128 x0,Bits128 x1,Bits128 x2,Bits128 x3,Bits128 x4,Bits128 x5) {
        return new VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,x0,x1,x2,x3,x4,x5);
    }
}
