package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner fixed original81 fullstate cases, no legacyAL/target-derived expected. */
public final class EmbeddedClassifyBoundary594 {
    private EmbeddedClassifyBoundary594() { }
    private static final long I=0x140000000L,E=0x8000L,D=0x10000L,RET=0x8877665544332211L;
    private static final Bits128 X6=new Bits128(0x61,0x62);
    private static final NonvolatileBits N=new NonvolatileBits(0x111,0x222,0x333,0x444,0x555,0x666,0x777,0x888,X6);
    private static void need(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static VolatileBits input(){return new VolatileBits(0x1001,D,0x1003,0x1004,0x1005,0x1006,0x1007,
        new Bits128(0x1010,0x1011),new Bits128(0x1020,0x1021),new Bits128(0x1030,0x1031),new Bits128(0x1040,0x1041),new Bits128(0x1050,0x1051),new Bits128(0x1060,0x1061));}
    private static VolatileBits expected(long[] acd){var v=input();return new VolatileBits(acd[0],acd[1],acd[2],v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static String mem(int w,long a,long x){return "R"+w+"@"+Long.toHexString(a)+"="+Long.toHexString(x);}
    private static final long[][][] INITIAL={
        {{0x4L,0x1001cL,0xffffffffL},{0x8L,0x10010L,0x123456789abcdeefL},{0x4L,0x123456789abcdebbL,0x0L},{0x8L,0x8000L,0x8877665544332211L}},
        {{0x4L,0x1001cL,0x1L},{0x8L,0x10010L,0x110000L},{0x4L,0x11000cL,0xffffffffL},{0x8L,0x10030L,0xabcdef0011223344L},{0x4L,0x1003cL,0x0L},{0x8L,0x8000L,0x8877665544332211L}},
        {{0x4L,0x1001cL,0x0L},{0x8L,0x10030L,0x5555666677778808L},{0x4L,0x1003cL,0x2L},{0x1L,0x555566667777884cL,0x0L},{0x1L,0x5555666677778894L,0x80L},{0x8L,0x8000L,0x8877665544332211L}},
        {{0x4L,0x1001cL,0x0L},{0x8L,0x10030L,0x0L},{0x4L,0x1003cL,0x1L},{0x1L,0x44L,0x1L},{0x8L,0x8000L,0x8877665544332211L}},
        {{0x4L,0x1001cL,0x0L},{0x8L,0x10030L,0x50000L},{0x4L,0x1003cL,0x2L},{0x1L,0x50044L,0x0L},{0x1L,0x5008cL,0x0L},{0x8L,0x8000L,0x8877665544332211L}},
        {{0x4L,0x1001cL,0x0L},{0x8L,0x10030L,0xfffffffffffffff0L},{0x4L,0x1003cL,0xffffffffL},{0x1L,0x34L,0xffL},{0x8L,0x8000L,0x8877665544332211L}},
        {{0x4L,0x1001cL,0x0L},{0x8L,0x10030L,0x60000L},{0x4L,0x1003cL,0x1L}}
    };
    private static final String[][] EVENTS={
        {"R4@1001c=ffffffff","R4@1001c=ffffffff","R8@10010=123456789abcdeef","R4@123456789abcdebb=0","R8@8000=8877665544332211"},
        {"R4@1001c=1","R4@1001c=1","R8@10010=110000","R4@11000c=ffffffff","R8@10030=abcdef0011223344","R4@1003c=0","R8@8000=8877665544332211"},
        {"R4@1001c=0","R8@10030=5555666677778808","R4@1003c=2","B@37275b0:5555666677778808","R1@555566667777884c=0","B@37275b0:5555666677778850","R1@5555666677778894=80","R8@8000=8877665544332211"},
        {"R4@1001c=0","R8@10030=0","R4@1003c=1","B@37275b0:0","R1@44=1","R8@8000=8877665544332211"},
        {"R4@1001c=0","R8@10030=50000","R4@1003c=2","B@37275b0:50000","R1@50044=0","B@37275b0:50048","R1@5008c=0","R8@8000=8877665544332211"},
        {"R4@1001c=0","R8@10030=fffffffffffffff0","R4@1003c=ffffffff","B@37275b0:fffffffffffffff0","R1@34=ff","R8@8000=8877665544332211"},
        {"R4@1001c=0","R8@10030=60000","R4@1003c=1","B@37275b0:60000"}
    };
    private static final long[][] ACD={{0x123456789abcde01L,0x10000L,0xffffffffffffffe0L},{0x0L,0xabcdef0011223344L,0x0L},{0x5555666677778801L,0x5555666677778898L,0x0L},{0x0L,0x48L,0x0L},{0x0L,0x50090L,0x0L},{0xffffffffffffff01L,0xffffffffffffffa8L,0x0L},{}};
    private static final boolean[] DFS={true,false,true,false,true,false,true};
    private static final class Ram implements FullCopy437Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace;int cursor;
        Ram(String...events){trace=List.of(events);}
        void seed(int w,long a,long x){for(int k=0;k<w;k++)bytes.put(a+k,(byte)(x>>>(8*k)));}
        void event(String x){need(cursor<trace.size()&&trace.get(cursor).equals(x),"event"+cursor+" got"+x+" expected"+(cursor<trace.size()?trace.get(cursor):"END"));cursor++;}
        long read(int w,long a){long x=0;for(int k=0;k<w;k++){Byte b=bytes.get(a+k);need(b!=null,"unseeded"+Long.toHexString(a+k));x|=Byte.toUnsignedLong(b)<<(8*k);}event(mem(w,a,x));return x;}
        public int readUnsignedByte(long a){return (int)read(1,a);}
        public int readDword(long a){return (int)read(4,a);}
        public long readQword(long a){return read(8,a);}
        void end(){need(cursor==trace.size(),"all source events consumed");}
        public int readUnsignedWord(long a){throw new AssertionError("unusedWORD");}
        public void writeWord(long a,int x){throw new AssertionError("leaf writes0");}
        public void writeByte(long a,int x){throw new AssertionError("leaf writes0");}
        public void writeDword(long a,int x){throw new AssertionError("leaf writes0");}
        public void writeQword(long a,long x){throw new AssertionError("leaf writes0");}
        public Bits128 read128(long a){throw new AssertionError("unused128");}
        public void write128(long a,Bits128 x){throw new AssertionError("leaf writes0");}
        public int lockedXaddDword(long a,int x){throw new AssertionError("unusedXADD");}
        public void write128NonTemporal(long a,Bits128 x){throw new AssertionError("leaf writes0");}
        public FullCopy437Api.Bits256 read256(long a){throw new AssertionError("unused256");}
        public void write256(long a,FullCopy437Api.Bits256 x){throw new AssertionError("leaf writes0");}
        public void write256NonTemporal(long a,FullCopy437Api.Bits256 x){throw new AssertionError("leaf writes0");}
        public void sfence(){throw new AssertionError("unusedFENCE");}
    }
    private static void one(int index){
        Ram ram=new Ram(EVENTS[index]);for(long[] c:INITIAL[index])ram.seed((int)c[0],c[1],c[2]);Map<Long,Byte> before=new HashMap<>(ram.bytes);
        var marker=new UnsupportedOperationException("original594budget");
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{need(h==0x37275B0,"exact sourceheader");ram.event("B@"+Long.toHexString(h)+":"+Long.toHexString(g));if(index==6)throw marker;};
        FullCopy437Api.CallResult result=null;
        try{
            result=EmbeddedClassifyFullState3727580.execute(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,E,input(),N),DFS[index],budget),ram);
            need(index!=6,"must stop at originalbudget");
        }catch(UnsupportedOperationException ex){need(index==6&&ex==marker,"same originalbudget marker identity");}
        if(index!=6){var wanted=new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(expected(ACD[index]),RET,E+8,N),DFS[index]);need(wanted.equals(result),"fullV/N/allXMM/DF/actualRIP-SP case"+index+" got"+result+" expected"+wanted);}
        ram.end();need(ram.bytes.equals(before),"complete ownedRAM unchanged, no fakeCALLpush/RETwrite");
    }
    public static int verify(){for(int i=0;i<INITIAL.length;i++)one(i);return INITIAL.length;}
    public static void main(String[] args){System.out.println(verify());}
}
