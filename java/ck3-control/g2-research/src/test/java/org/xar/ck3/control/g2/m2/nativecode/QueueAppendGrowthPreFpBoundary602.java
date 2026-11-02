package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Three owner literal17B bank/order units; no FP conversion or fullgrowth claim. */
public final class QueueAppendGrowthPreFpBoundary602 {
    private QueueAppendGrowthPreFpBoundary602() { }
    private static final RuntimeException MARKER=new IllegalStateException("original-read-order-marker602");
    private record Scenario(String name,VolatileBits input,NonvolatileBits inputN,
            VolatileBits before,NonvolatileBits beforeN,VolatileBits post,NonvolatileBits postN,
            long sp,long address,long value,boolean marker) { }
    private static void need(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static final class Memory implements FullCopy437Api.Memory {
        final Registers r;final Scenario c;int reads;
        Memory(Registers actual,Scenario expected){r=actual;c=expected;}
        public long readQword(long address){
            need(reads==0&&address==c.address(),"onlyfreshallocatorQ");reads++;
            need(r.volatileBits().equals(c.before())&&r.nonvolatileBits().equals(c.beforeN())&&r.rsp==c.sp(),"fullbankafterESI/MOVDbeforeMemory/R8write");
            if(c.marker())throw MARKER;
            return c.value();
        }
        public int readUnsignedByte(long a){throw new AssertionError("unusedBYTE");}
        public void writeByte(long a,int x){throw new AssertionError("unusedBYTE");}
        public int readUnsignedWord(long a){throw new AssertionError("unusedWORD");}
        public void writeWord(long a,int x){throw new AssertionError("unusedWORD");}
        public int readDword(long a){throw new AssertionError("unusedDWORD");}
        public void writeDword(long a,int x){throw new AssertionError("unusedDWORD");}
        public void writeQword(long a,long x){throw new AssertionError("unusedWRITE");}
        public Bits128 read128(long a){throw new AssertionError("unused128");}
        public void write128(long a,Bits128 x){throw new AssertionError("unused128");}
        public int lockedXaddDword(long a,int x){throw new AssertionError("unusedXADD");}
        public void write128NonTemporal(long a,Bits128 x){throw new AssertionError("unusedNT");}
        public FullCopy437Api.Bits256 read256(long a){throw new AssertionError("unused256");}
        public void write256(long a,FullCopy437Api.Bits256 x){throw new AssertionError("unused256");}
        public void write256NonTemporal(long a,FullCopy437Api.Bits256 x){throw new AssertionError("unused256NT");}
        public void sfence(){throw new AssertionError("unusedSFENCE");}
    }
    private static final Scenario[] CASES={
        new Scenario("ordinary",new VolatileBits(0x5L,0x5L,0x1a100L,0xaabbccddeeff1234L,0x9009L,0xa00aL,0xb00bL,new Bits128(0x123456789abcdefL,0xfedcba9876543210L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x3333L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),new VolatileBits(0x5L,0x5L,0x1a100L,0xaabbccddeeff1234L,0x9009L,0xa00aL,0xb00bL,new Bits128(0x5L,0x0L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x6L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),new VolatileBits(0x5L,0x100abcdefL,0x1a100L,0x8L,0x9009L,0xa00aL,0xb00bL,new Bits128(0x5L,0x0L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x6L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),0x19fe0L,0x430010L,0x100abcdefL,false),
        new Scenario("negative_wrap",new VolatileBits(0xffffffffffffffffL,0xffffffffL,0x1a100L,0xaabbccddeeff1234L,0x9009L,0xa00aL,0xb00bL,new Bits128(0x123456789abcdefL,0xfedcba9876543210L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x3333L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),new VolatileBits(0xffffffffffffffffL,0xffffffffL,0x1a100L,0xaabbccddeeff1234L,0x9009L,0xa00aL,0xb00bL,new Bits128(0xffffffffL,0x0L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x0L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),new VolatileBits(0xffffffffffffffffL,0x7abcdef012345678L,0x1a100L,0x8L,0x9009L,0xa00aL,0xb00bL,new Bits128(0xffffffffL,0x0L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x0L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),0x19fe0L,0x430010L,0x7abcdef012345678L,false),
        new Scenario("read_marker_order",new VolatileBits(0xffffffff80000000L,0x80000000L,0x1a100L,0xaabbccddeeff1234L,0x9009L,0xa00aL,0xb00bL,new Bits128(0x123456789abcdefL,0xfedcba9876543210L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x3333L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),new VolatileBits(0xffffffff80000000L,0x80000000L,0x1a100L,0xaabbccddeeff1234L,0x9009L,0xa00aL,0xb00bL,new Bits128(0x80000000L,0x0L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x80000001L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),new VolatileBits(0xffffffff80000000L,0x80000000L,0x1a100L,0xaabbccddeeff1234L,0x9009L,0xa00aL,0xb00bL,new Bits128(0x80000000L,0x0L),new Bits128(0x11L,0x12L),new Bits128(0x21L,0x22L),new Bits128(0x31L,0x32L),new Bits128(0x41L,0x42L),new Bits128(0x51L,0x52L)),new NonvolatileBits(0x430000L,0x2222L,0x80000001L,0x4444L,0x5555L,0x6666L,0x1a100L,0x8888L,new Bits128(0x61L,0x62L)),0x19fe0L,0x430010L,0x0L,true)
    };
    private static void scenario(Scenario c){
        var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(0x140000000L,c.sp(),c.input(),c.inputN()));
        Memory memory=new Memory(r,c);RuntimeException failure=null;
        try{QueueAppendGrowthPreFp602.prepare(r,memory);}catch(RuntimeException ex){failure=ex;}
        need(c.marker()?failure==MARKER:failure==null,"originalmarkeridentity "+c.name());
        need(memory.reads==1&&r.volatileBits().equals(c.post())&&r.nonvolatileBits().equals(c.postN())&&r.rsp==c.sp(),"fullbank/SP actualexit orpriorchangespreserved "+c.name());
    }
    public static int verify(){for(Scenario c:CASES)scenario(c);return CASES.length;}
    public static void main(String[] args){System.out.println(verify());}
}
