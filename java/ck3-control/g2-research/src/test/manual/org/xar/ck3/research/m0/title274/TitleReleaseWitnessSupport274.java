package org.xar.ck3.research.m0.title274;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Generic owned DATA/bit constructors only; no target algorithm or expected matrix. */
public final class TitleReleaseWitnessSupport274 {
    private TitleReleaseWitnessSupport274() { }
    public static int checks;
    public static void eq(long expected,long actual,String message) {
        checks++; if(expected!=actual)throw new AssertionError(message+": expected="+Long.toHexString(expected)+" actual="+Long.toHexString(actual));
    }
    public static void eq(Object expected,Object actual,String message) {
        checks++; if(!Objects.equals(expected,actual))throw new AssertionError(message+": expected="+expected+" actual="+actual);
    }
    public static void same(Object expected,Object actual,String message) {
        checks++; if(expected!=actual)throw new AssertionError(message+": object identity differs");
    }
    public static VolatileBits v(long a,long c,long d,long r8,long r9,long r10,long r11) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,new Bits128(0x101L,0x102L),new Bits128(0x201L,0x202L),
                new Bits128(0x301L,0x302L),new Bits128(0x401L,0x402L),new Bits128(0x501L,0x502L),new Bits128(0x601L,0x602L));
    }
    public static NonvolatileBits n() {
        return new NonvolatileBits(0x1111222233334444L,0x5555666677778888L,0x9999AAAABBBBCCCCL,
                0xDDDDEEEEFFFF0001L,0x123456789ABCDEFFL,0xFEDCBA9876543210L,0x3141592653589793L,
                0x2718281828459045L,new Bits128(0xABCDEF0123456789L,0x9876543210ABCDEFL));
    }
    public static class RejectCalls implements GovernmentCrtBoundary185Api.Calls {
        @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {throw new AssertionError("unexpected invoke "+call);}
        @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail tail) {throw new AssertionError("unexpected tail "+tail);}
        @Override public long readGsQword58() {throw new AssertionError("unexpected GS read");}
    }
    public static final class Image implements GovernmentCrtBoundary185Api.Memory {
        public final List<String> events=new ArrayList<>();
        private final Map<Long,Integer> bytes=new HashMap<>();
        private static String h(long a){return Long.toUnsignedString(a,16);}
        private long peek(long address,int width) {
            long value=0L;
            for(int i=0;i<width;i++) {
                Integer b=bytes.get(address+i);
                if(b==null)throw new AssertionError("unmapped byte "+h(address+i));
                value|=(long)b<<(8*i);
            }
            return value;
        }
        private void put(long address,long value,int width) {
            for(int i=0;i<width;i++)bytes.put(address+i,(int)(value>>>(8*i))&0xFF);
        }
        public void seedQ(long address,long value){put(address,value,8);}
        public void seedD(long address,int value){put(address,Integer.toUnsignedLong(value),4);}
        public long peekQ(long address){return peek(address,8);}
        public int peekD(long address){return (int)peek(address,4);}
        @Override public long readQword(long address){events.add("rq@"+h(address));return peek(address,8);}
        @Override public int readDword(long address){events.add("rd@"+h(address));return (int)peek(address,4);}
        @Override public int readUnsignedByte(long address){events.add("rb@"+h(address));return (int)peek(address,1);}
        @Override public void writeQword(long address,long value){events.add("wq@"+h(address)+"="+h(value));put(address,value,8);}
        @Override public void writeDword(long address,int value){events.add("wd@"+h(address)+"="+Integer.toUnsignedString(value,16));put(address,Integer.toUnsignedLong(value),4);}
        @Override public void writeByte(long address,int value){events.add("wb@"+h(address)+"="+Integer.toUnsignedString(value&0xFF,16));put(address,value,1);}
        @Override public Bits128 read128(long address){events.add("r128@"+h(address));return new Bits128(peek(address,8),peek(address+8L,8));}
        @Override public void write128(long address,Bits128 value){events.add("w128@"+h(address));put(address,value.lowBits(),8);put(address+8L,value.highBits(),8);}
        @Override public int lockedXaddDword(long address,int addend){throw new AssertionError("unexpected xadd");}
    }
}
