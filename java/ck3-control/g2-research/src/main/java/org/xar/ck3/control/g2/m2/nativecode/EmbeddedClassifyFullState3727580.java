package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Complete held81 normal represented source; legacyAL-only helper is not called. */
public final class EmbeddedClassifyFullState3727580 {
    private EmbeddedClassifyFullState3727580() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);
        var e=input.entry();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
            e.imageBaseBits(),e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        boolean positive=false;
        if(memory.readDword(r.rcx+0x1C)!=0) {
            positive=EmbeddedClassifyFirstVector594.firstVectorNonnegative(r,memory);
        }
        if(!positive) {
            r.rax=memory.readQword(r.rcx+0x30);
            r.rcx=memory.readDword(r.rcx+0x3C);
            r.rdx=r.rcx+r.rcx*8;
            r.rcx=r.rax+r.rdx*8;
            while(r.rax!=r.rcx) {
                // Sourceheader software bound before its first Memory operation.
                input.budget().beforeStep(0x37275B0L,r.rax);
                if((memory.readUnsignedByte(r.rax+0x44)&0xFF)!=0)break;
                r.rax+=0x48;
            }
            r.rdx=0;
            if(r.rax==r.rcx)r.rax=0;
            positive=r.rax!=0;
        }
        if(positive)r.rax=(r.rax&~0xFFL)|1L;
        long rip=memory.readQword(r.rsp);
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),rip,r.rsp+8,r.nonvolatileBits()),input.directionFlagSet());
    }
}
