package org.xar.ck3.control.g2.m2.nativecode;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
/** Owner AVX256 one-step projection [4220AD0,4220AF7); no loop/RET/VZEROUPPER here. */
public final class ReverseAvxStep641 {
    private ReverseAvxStep641() { }
    public static void step(Registers r,FullCopy437Api.Memory memory) {
        Objects.requireNonNull(r);Objects.requireNonNull(memory);
        FullCopy437Api.Bits256 front=Objects.requireNonNull(memory.read256(r.r8));
        FullCopy437Api.Bits256 a=new FullCopy437Api.Bits256(front.high(),front.low());
        r.x1=a.low();r.rdx-=32;
        FullCopy437Api.Bits256 aReversed=new FullCopy437Api.Bits256(reverse(a.low()),reverse(a.high()));r.x3=aReversed.low();
        FullCopy437Api.Bits256 back=Objects.requireNonNull(memory.read256(r.rdx));
        FullCopy437Api.Bits256 z=new FullCopy437Api.Bits256(back.high(),back.low());r.x1=z.low();
        FullCopy437Api.Bits256 zReversed=new FullCopy437Api.Bits256(reverse(z.low()),reverse(z.high()));r.x2=zReversed.low();
        memory.write256(r.r8,zReversed);r.r8+=32;memory.write256(r.rdx,aReversed);
    }
    private static Bits128 reverse(Bits128 x) {
        long low=x.lowBits(),high=x.highBits();
        return new Bits128((high<<32)|(high>>>32),(low<<32)|(low>>>32));
    }
}
