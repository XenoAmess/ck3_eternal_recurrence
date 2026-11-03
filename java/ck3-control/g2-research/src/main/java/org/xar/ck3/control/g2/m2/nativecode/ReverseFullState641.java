package org.xar.ck3.control.g2.m2.nativecode;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
/** Owner orchestration of held194 normal source and represented185 low-XMM state.
 * Upper YMM/RFLAGS/hardware/OS are outside this projection; VZEROUPPER is an explicit effect. */
public final class ReverseFullState641 {
    private ReverseFullState641() { }
    public static QueueFp604Api.Normal execute(QueueFp604Api.Input input,Reverse641Api.Memory memory) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);
        var e=input.base().entry();long image=e.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(image,e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        var budget=input.base().budget();
        r.rax=r.rdx;r.r8=r.rcx;r.rax-=r.rcx;
        if(Long.compareUnsigned(r.rax,0x40L)>=0) {
            int features=memory.readDword(image+0x542f09cL);
            if((features&0x20)!=0) {
                r.rax>>>=1;r.rcx=0x7fffffffffffffe0L;r.rax&=r.rcx;r.rax+=r.r8;
                do {budget.beforeStep(0x4220ad0L,r.r8);ReverseAvxStep641.step(r,memory);}while(r.r8!=r.rax);
                memory.vzeroUpper();
            }
        }
        r.rax=r.rdx;r.rax-=r.r8;
        if(Long.compareUnsigned(r.rax,0x20L)>=0) {
            r.rax>>>=1;r.rcx=0x7ffffffffffffff0L;r.rax&=r.rcx;r.rax+=r.r8;
            do {budget.beforeStep(0x4220b1eL,r.r8);ReverseSseStep641.step(r,memory);}while(r.r8!=r.rax);
        }
        return ReverseScalarTail641.finish(r,memory,budget,input.base().directionFlagSet(),input.mxcsr());
    }
}
