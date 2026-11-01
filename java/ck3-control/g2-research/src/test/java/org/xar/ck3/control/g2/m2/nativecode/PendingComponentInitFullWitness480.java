package org.xar.ck3.control.g2.m2.nativecode;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
/** Owner-frozen original ASM literals and mechanical storage; new verification methods encoded by local model, independently reviewed. */
public final class PendingComponentInitFullWitness480 {
 private PendingComponentInitFullWitness480() { }
 private static final long M=0x0000003300000000L;
 private static final long C=0x8100000000004000L;
 private static final long SP0=0x8100000000009008L;
 private static final long SP1=0x81000000000041E0L;
 private static final long RET=0xAABBCCDD11223344L;
 private static final VolatileBits V0=new VolatileBits(0x8877665544332211L,0x8100000000004000L,0xF1E2D3C4B5A69788L,0xDEADBEEF12345678L,0x1122334455667788L,0x8877665544332211L,0x7FFEEDDCCBBAA009L,new Bits128(0x0000000000001010L,0xFFFFFFFFFFFFEFEFL),new Bits128(0x0000000000001020L,0xFFFFFFFFFFFFEFDFL),new Bits128(0x0000000000001030L,0xFFFFFFFFFFFFEFCFL),new Bits128(0x0000000000001040L,0xFFFFFFFFFFFFEFBFL),new Bits128(0x0000000000001050L,0xFFFFFFFFFFFFEFAFL),new Bits128(0x0000000000001060L,0xFFFFFFFFFFFFEF9FL));
 private static final VolatileBits VF=new VolatileBits(0x8100000000004000L,0x8100000000004000L,0x00000033054E62D8L,0x0000000000000000L,0x1122334455667788L,0x8877665544332211L,0x7FFEEDDCCBBAA009L,new Bits128(0x0000000000001010L,0xFFFFFFFFFFFFEFEFL),new Bits128(0x0000000000001020L,0xFFFFFFFFFFFFEFDFL),new Bits128(0x0000000000001030L,0xFFFFFFFFFFFFEFCFL),new Bits128(0x0000000000001040L,0xFFFFFFFFFFFFEFBFL),new Bits128(0x0000000000001050L,0xFFFFFFFFFFFFEFAFL),new Bits128(0x0000000000001060L,0xFFFFFFFFFFFFEF9FL));
 private static final NonvolatileBits N0=new NonvolatileBits(0x0000000000002001L,0x0000000000002002L,0x0000000000002003L,0x0000000000002004L,0x0000000000002005L,0x0000000000002006L,0x0000000000002007L,0x0000000000002008L,new Bits128(0x0000000000002060L,0xFFFFFFFFFFFFDF9FL));
 private static final FullCopy437Api.CallResult NORMAL0=new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(VF,0xAABBCCDD11223344L,0x8100000000009010L,N0),false);
 private static final FullCopy437Api.CallResult NORMAL1=new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(VF,0x8100000000004000L,0x81000000000041E8L,N0),true);
 private static final String EXPECTED_IMAGE="00000000000000000d1a2734414e5b6800000000000000000f000000000000000000000000000000adbac7d4e1eefb0800000000000000000f0000000000000000000000000000004d5a6774818e9ba800000000000000000f0000000000000000000000000000000000000000000000d8624e0533000000000000000000000025323f4c5966738000000000000000000f000000000000000000000000000000c5d2dfecf906132000000000000000000f00000000000000000000000000000065727f8c99a6b3c000000000000000000f0000000000000000000000000000000000000000000000d8624e053300000000000000000000003d4a5764717e8b9800000000000000000f000000000000000000000000000000ddeaf704111e2b3800000000000000000f0000000000000000000000000000007d8a97a4b1becbd800000000000000000f0000000000000000000000000000000000000000000000d8624e0533000000000000000000000055626f7c8996a3b000000000000000000f000000000000000000000000000000f5020f1c2936435000000000000000000f00000000000000000000000000000095a2afbcc9d6e3f000000000000000000f0000000000000000000000000000000000000000000000d8624e05330000000040000000000081784000000000008100000000000000003d4a5764717e8b9800000000000000000f000000000000000000000000000000ddeaf704111e2b3800000000000000000f0000000000000000000000000000007d8a97a4b1becbd800000000000000000f00000000000000ffffffffffffffffffffffff005e6b780000000001c6d3e0edfa0714212e3b48";
 private record Ev(String op,int width,long address,String hex) { }
 private static List<Ev> expectedTrace(boolean alias){List<Ev> r=new ArrayList<>(List.of(
  new Ev("W",8,0x8100000000004018L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004000L,"0000000000000000"),
  new Ev("W",8,0x8100000000004078L,"0000000000000000"),
  new Ev("W",8,0x8100000000004088L,"0000000000000000"),
  new Ev("W",8,0x8100000000004090L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004098L,"0000000000000000"),
  new Ev("W",8,0x81000000000040A8L,"0000000000000000"),
  new Ev("W",8,0x81000000000040B0L,"0f00000000000000"),
  new Ev("W",8,0x81000000000040B8L,"0000000000000000"),
  new Ev("W",8,0x81000000000040C8L,"0000000000000000"),
  new Ev("W",8,0x81000000000040D0L,"0f00000000000000"),
  new Ev("W",8,0x81000000000040D8L,"0000000000000000"),
  new Ev("W",8,0x81000000000040E0L,"0000000000000000"),
  new Ev("W",8,0x81000000000040E8L,"d8624e0533000000"),
  new Ev("W",8,0x81000000000041E8L,"7840000000000081"),
  new Ev("W",8,0x8100000000004010L,"0000000000000000"),
  new Ev("W",8,0x8100000000004020L,"0000000000000000"),
  new Ev("W",8,0x8100000000004030L,"0000000000000000"),
  new Ev("W",8,0x8100000000004038L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004040L,"0000000000000000"),
  new Ev("W",8,0x8100000000004050L,"0000000000000000"),
  new Ev("W",8,0x8100000000004058L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004060L,"0000000000000000"),
  new Ev("W",8,0x8100000000004068L,"0000000000000000"),
  new Ev("W",8,0x8100000000004070L,"d8624e0533000000"),
  new Ev("W",8,0x81000000000040F0L,"0000000000000000"),
  new Ev("W",8,0x8100000000004100L,"0000000000000000"),
  new Ev("W",8,0x8100000000004108L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004110L,"0000000000000000"),
  new Ev("W",8,0x8100000000004120L,"0000000000000000"),
  new Ev("W",8,0x8100000000004128L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004130L,"0000000000000000"),
  new Ev("W",8,0x8100000000004140L,"0000000000000000"),
  new Ev("W",8,0x8100000000004148L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004150L,"0000000000000000"),
  new Ev("W",8,0x8100000000004158L,"0000000000000000"),
  new Ev("W",8,0x8100000000004160L,"d8624e0533000000"),
  new Ev("W",8,0x8100000000004168L,"0000000000000000"),
  new Ev("W",8,0x8100000000004178L,"0000000000000000"),
  new Ev("W",8,0x8100000000004180L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004188L,"0000000000000000"),
  new Ev("W",8,0x8100000000004198L,"0000000000000000"),
  new Ev("W",8,0x81000000000041A0L,"0f00000000000000"),
  new Ev("W",8,0x81000000000041A8L,"0000000000000000"),
  new Ev("W",8,0x81000000000041B8L,"0000000000000000"),
  new Ev("W",8,0x81000000000041C0L,"0f00000000000000"),
  new Ev("W",8,0x81000000000041C8L,"0000000000000000"),
  new Ev("W",8,0x81000000000041D0L,"0000000000000000"),
  new Ev("W",8,0x81000000000041D8L,"d8624e0533000000"),
  new Ev("W",8,0x81000000000041E0L,"0040000000000081"),
  new Ev("W",8,0x81000000000041F0L,"0000000000000000"),
  new Ev("W",8,0x8100000000004200L,"0000000000000000"),
  new Ev("W",8,0x8100000000004208L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004210L,"0000000000000000"),
  new Ev("W",8,0x8100000000004220L,"0000000000000000"),
  new Ev("W",8,0x8100000000004228L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004230L,"0000000000000000"),
  new Ev("W",8,0x8100000000004240L,"0000000000000000"),
  new Ev("W",8,0x8100000000004248L,"0f00000000000000"),
  new Ev("W",8,0x8100000000004250L,"ffffffffffffffff"),
  new Ev("W",4,0x8100000000004258L,"ffffffff"),
  new Ev("W",1,0x810000000000425CL,"00"),
  new Ev("W",4,0x8100000000004260L,"00000000"),
  new Ev("W",1,0x8100000000004264L,"01")));
 r.add(alias?new Ev("R",8,SP1,"0040000000000081"):new Ev("R",8,SP0,"44332211ddccbbaa"));return List.copyOf(r);}
 private static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);}
 private static byte[] little(long value,int width){byte[] b=new byte[width];for(int i=0;i<width;i++)b[i]=(byte)(value>>>(8*i));return b;}
 private static long scalar(byte[] b){long value=0;for(int i=0;i<b.length;i++)value|=(long)(b[i]&255)<<(i*8);return value;}
 private static final class Mem implements FullCopy437Api.Memory {
  final Map<Long,Byte> cells=new HashMap<>();final List<Ev> events=new ArrayList<>();
  void raw(long a,byte[] b){for(int i=0;i<b.length;i++)cells.put(a+i,b[i]);}
  void seed(long a,long value,int width){raw(a,little(value,width));}
  byte[] peek(long a,int width){byte[] b=new byte[width];for(int i=0;i<width;i++){Byte v=cells.get(a+i);if(v==null)throw new AssertionError("unseeded "+Long.toUnsignedString(a+i,16));b[i]=v;}return b;}
  long peek64(long a){return scalar(peek(a,8));}
  String peekHex(long a,int width){return HexFormat.of().formatHex(peek(a,width));}
  void write(long a,long v,int width){byte[] b=little(v,width);raw(a,b);events.add(new Ev("W",width,a,HexFormat.of().formatHex(b)));}
  @Override public long readQword(long a){byte[] b=peek(a,8);events.add(new Ev("R",8,a,HexFormat.of().formatHex(b)));return scalar(b);}
  @Override public void writeByte(long a,int v){write(a,v,1);}
  @Override public void writeDword(long a,int v){write(a,Integer.toUnsignedLong(v),4);}
  @Override public void writeQword(long a,long v){write(a,v,8);}
  private static UnsupportedOperationException unused(){return new UnsupportedOperationException("unexpected source effect");}
  @Override public int readUnsignedByte(long a){throw unused();}
  @Override public int readUnsignedWord(long a){throw unused();}
  @Override public int readDword(long a){throw unused();}
  @Override public int lockedXaddDword(long a,int v){throw unused();}
  @Override public Bits128 read128(long a){throw unused();}
  @Override public void write128(long a,Bits128 v){throw unused();}
  @Override public void writeWord(long a,int v){throw unused();}
  @Override public void write128NonTemporal(long a,Bits128 v){throw unused();}
  @Override public void sfence(){throw unused();}
  @Override public FullCopy437Api.Bits256 read256(long a){throw unused();}
  @Override public void write256(long a,FullCopy437Api.Bits256 v){throw unused();}
  @Override public void write256NonTemporal(long a,FullCopy437Api.Bits256 v){throw unused();}
 }
 private static Mem seeded(long sp){Mem m=new Mem();byte[] initial=new byte[0x270];for(int i=0;i<initial.length;i++)initial[i]=(byte)((i*13+0xA5)&255);m.raw(C,initial);m.seed(sp,RET,8);return m;}
 public static int verify() {
    int count = 0;
    for (int i = 0; i < 2; i++) {
        boolean alias = (i == 1);
        long sp = alias ? SP1 : SP0;
        boolean df = alias;
        FullCopy437Api.CallResult expectedNormal = alias ? NORMAL1 : NORMAL0;
        List<Ev> expectedTrace = expectedTrace(alias);
        Mem m = seeded(sp);
        GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(M, sp, V0, N0);
        FullCopy437Api.Input input = new FullCopy437Api.Input(entry, df, new GovernmentCrtBoundary185Api.LoopBudget() {
            @Override public void beforeStep(long loopHeaderRva, long guardAddressBits) {
                throw new UnsupportedOperationException("Budget not used");
            }
        });
        FullCopy437Api.CallResult actual = PendingComponentInitFullState2756120.execute(input, m);
        check(actual.equals(expectedNormal), "Normal mismatch case " + i);
        check(m.events.equals(expectedTrace), "Trace mismatch case " + i);
        check(m.events.size() == 65, "Event count mismatch case " + i);
        check(m.peekHex(C, 0x270).equals(EXPECTED_IMAGE), "Image mismatch case " + i);
        long freshRet = m.peek64(sp);
        long expectedRet = alias ? C : RET;
        check(freshRet == expectedRet, "Fresh RET mismatch case " + i);
        count++;
    }
    return count;
}
 public static void main(String[] args) {
    System.out.println(verify());
}
}
