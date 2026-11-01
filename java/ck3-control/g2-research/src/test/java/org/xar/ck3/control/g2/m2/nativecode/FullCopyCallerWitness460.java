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

/** Owner-frozen ASM oracle and mechanical byte storage with finite verification. */
public final class FullCopyCallerWitness460 {
 private FullCopyCallerWitness460() { }
 private static final long M=0x0000003300000000L;
 private static final long E=0x8100000000009008L;
 private static final long RET=0xAABBCCDD11223344L;
 private static final long T=0x8100000000005000L;
 private static final long B=0x8100000000001200L;
 private static final long D=0x8100000000001400L;
 private static final long A=0x8100000000006000L;
 private static final long A2=0x8100000000006100L;
 private static final long VT=0x8100000000007000L;
 private static final long VT2=0x8100000000007100L;
 private static final long ALLOC=0x7FFF111122223333L;
 private static final long RELEASE=0x7FFF444455556666L;
 private static final long S=0x8100000000008FE0L;
 private static final long C=0x8100000000008FD8L;
 private static final VolatileBits V0=new VolatileBits(0x8877665544332211L,0x8100000000005000L,0x0000000000000002L,0x0000000000001008L,0x0000000000001009L,0x000000000000100AL,0x000000000000100BL,new Bits128(0x0000000000001010L,0xFFFFFFFFFFFFEFEFL),new Bits128(0x0000000000001020L,0xFFFFFFFFFFFFEFDFL),new Bits128(0x0000000000001030L,0xFFFFFFFFFFFFEFCFL),new Bits128(0x0000000000001040L,0xFFFFFFFFFFFFEFBFL),new Bits128(0x0000000000001050L,0xFFFFFFFFFFFFEFAFL),new Bits128(0x0000000000001060L,0xFFFFFFFFFFFFEF9FL));
 private static final VolatileBits VA=new VolatileBits(0x8100000000007000L,0x8100000000006000L,0x0000000000000020L,0x0000000000000008L,0x0000000000001009L,0x000000000000100AL,0x000000000000100BL,new Bits128(0x0000000000001010L,0xFFFFFFFFFFFFEFEFL),new Bits128(0x0000000000001020L,0xFFFFFFFFFFFFEFDFL),new Bits128(0x0000000000001030L,0xFFFFFFFFFFFFEFCFL),new Bits128(0x0000000000001040L,0xFFFFFFFFFFFFEFBFL),new Bits128(0x0000000000001050L,0xFFFFFFFFFFFFEFAFL),new Bits128(0x0000000000001060L,0xFFFFFFFFFFFFEF9FL));
 private static final VolatileBits VR=new VolatileBits(0x8100000000007100L,0x8100000000006100L,0x8100000000001400L,0x0000000000000008L,0x0000000000005009L,0x0000003300000000L,0x000000000000500BL,new Bits128(0x0000000000005010L,0xFFFFFFFFFFFFAFEFL),new Bits128(0x8786858483828180L,0x8F8E8D8C8B8A8988L),new Bits128(0x8786858483828180L,0x8F8E8D8C8B8A8988L),new Bits128(0x0000000000005040L,0xFFFFFFFFFFFFAFBFL),new Bits128(0x0000000000005050L,0xFFFFFFFFFFFFAFAFL),new Bits128(0x0000000000005060L,0xFFFFFFFFFFFFAF9FL));
 private static final VolatileBits POA=new VolatileBits(0x8100000000001200L,0x7172737475767778L,0x8182838485868788L,0x0000000000005008L,0x0000000000005009L,0x000000000000500AL,0x000000000000500BL,new Bits128(0x0000000000005010L,0xFFFFFFFFFFFFAFEFL),new Bits128(0x0000000000005020L,0xFFFFFFFFFFFFAFDFL),new Bits128(0x0000000000005030L,0xFFFFFFFFFFFFAFCFL),new Bits128(0x0000000000005040L,0xFFFFFFFFFFFFAFBFL),new Bits128(0x0000000000005050L,0xFFFFFFFFFFFFAFAFL),new Bits128(0x0000000000005060L,0xFFFFFFFFFFFFAF9FL));
 private static final VolatileBits POR=new VolatileBits(0xDEADBEEF87654321L,0x9192939495969798L,0xA1A2A3A4A5A6A7A8L,0x0000000000006008L,0x0000000000006009L,0x000000000000600AL,0x000000000000600BL,new Bits128(0x0000000000006010L,0xFFFFFFFFFFFF9FEFL),new Bits128(0x0000000000006020L,0xFFFFFFFFFFFF9FDFL),new Bits128(0x0000000000006030L,0xFFFFFFFFFFFF9FCFL),new Bits128(0x0000000000006040L,0xFFFFFFFFFFFF9FBFL),new Bits128(0x0000000000006050L,0xFFFFFFFFFFFF9FAFL),new Bits128(0x0000000000006060L,0xFFFFFFFFFFFF9F9FL));
 private static final NonvolatileBits N0=new NonvolatileBits(0x0000000000002001L,0x0000000000002002L,0x0000000000002003L,0x0000000000002004L,0x0000000000002005L,0x0000000000002006L,0x0000000000002007L,0x0000000000002008L,new Bits128(0x0000000000002060L,0xFFFFFFFFFFFFDF9FL));
 private static final NonvolatileBits NA=new NonvolatileBits(0x8100000000005000L,0x0000000000002002L,0x0000000000002003L,0x0000000000000002L,0x0000000000002005L,0x0000000000002006L,0x0000000000002007L,0x0000000000002008L,new Bits128(0x0000000000002060L,0xFFFFFFFFFFFFDF9FL));
 private static final NonvolatileBits NC=new NonvolatileBits(0x8100000000005000L,0x8100000000001200L,0x0000000000000001L,0x0000000000000002L,0x0000000000002005L,0x0000000000002006L,0x0000000000002007L,0x0000000000002008L,new Bits128(0x0000000000002060L,0xFFFFFFFFFFFFDF9FL));
 private static final PendingSlotCapacityFullState412Api.CallFrame ALLOC_FRAME=new PendingSlotCapacityFullState412Api.CallFrame(new GovernmentCrtBoundary185Api.Call(0x0000000001ACE4E1L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x7FFF111122223333L,S,VA,NA),new GovernmentCrtBoundary185Api.Entry(M,C,VA,NA),false,3,0x0000003301ACE4E4L);
 private static final PendingSlotCapacityFullState412Api.CallFrame RELEASE_FRAME=new PendingSlotCapacityFullState412Api.CallFrame(new GovernmentCrtBoundary185Api.Call(0x0000000001ACE514L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x7FFF444455556666L,S,VR,NC),new GovernmentCrtBoundary185Api.Entry(M,C,VR,NC),true,3,0x0000003301ACE517L);
 private static final PendingSlotCapacityFullState412Api.CallResult ALLOC_RETURN=new PendingSlotCapacityFullState412Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(POA,0x0000003301ACE4E4L,0x8100000000008FE0L,NA),true);
 private static final PendingSlotCapacityFullState412Api.CallResult RELEASE_RETURN=new PendingSlotCapacityFullState412Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(POR,0x0000003301ACE517L,0x8100000000008FE0L,NC),false);
 private static final PendingSlotCapacityFullState412Api.CallResult NORMAL=new PendingSlotCapacityFullState412Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(POR,0xAABBCCDD11223344L,0x8100000000009010L,N0),false);
 private record Ev(String op,int width,long address,String hex) { }
 private static List<Ev> expectedTrace(){return List.of(
  new Ev("W",8,0x8100000000009020L,"0120000000000000"),
  new Ev("W",8,0x8100000000009000L,"0420000000000000"),
  new Ev("R",4,0x8100000000005008L,"00000000"),
  new Ev("R",8,0x8100000000005010L,"0060000000000081"),
  new Ev("W",8,0x8100000000009010L,"0220000000000000"),
  new Ev("W",8,0x8100000000009018L,"0320000000000000"),
  new Ev("R",8,0x8100000000006000L,"0070000000000081"),
  new Ev("R",8,0x8100000000007008L,"333322221111ff7f"),
  new Ev("W",8,0x8100000000008FD8L,"e4e4ac0133000000"),
  new Ev("W",8,0x8100000000005010L,"0061000000000081"),
  new Ev("R",4,0x810000000000500CL,"01000000"),
  new Ev("R",8,0x8100000000005000L,"0014000000000081"),
  new Ev("W",8,0x8100000000008FD8L,"01e5ac0133000000"),
  new Ev("R",16,0x8100000000001400L,"808182838485868788898a8b8c8d8e8f"),
  new Ev("R",16,0x8100000000001400L,"808182838485868788898a8b8c8d8e8f"),
  new Ev("W",16,0x8100000000001200L,"808182838485868788898a8b8c8d8e8f"),
  new Ev("W",16,0x8100000000001200L,"808182838485868788898a8b8c8d8e8f"),
  new Ev("R",8,0x8100000000008FD8L,"01e5ac0133000000"),
  new Ev("R",4,0x810000000000500CL,"01000000"),
  new Ev("R",8,0x8100000000005010L,"0061000000000081"),
  new Ev("R",8,0x8100000000005000L,"0014000000000081"),
  new Ev("R",8,0x8100000000006100L,"0071000000000081"),
  new Ev("R",8,0x8100000000007110L,"666655554444ff7f"),
  new Ev("W",8,0x8100000000008FD8L,"17e5ac0133000000"),
  new Ev("W",4,0x810000000000500CL,"07000000"),
  new Ev("W",1,0x8100000000001220L,"77"),
  new Ev("W",8,0x8100000000005000L,"0012000000000081"),
  new Ev("R",8,0x8100000000009010L,"0220000000000000"),
  new Ev("W",4,0x810000000000500CL,"01000000"),
  new Ev("R",8,0x8100000000009018L,"0320000000000000"),
  new Ev("W",4,0x8100000000005008L,"02000000"),
  new Ev("R",8,0x8100000000009020L,"0120000000000000"),
  new Ev("R",8,0x8100000000009000L,"0420000000000000"),
  new Ev("R",8,0x8100000000009008L,"44332211ddccbbaa"));}
 private static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);}
 private static byte[] little(long bits,int width){byte[] b=new byte[width];for(int i=0;i<width;i++)b[i]=(byte)(bits>>>(8*i));return b;}
 private static long scalar(byte[] b,int offset,int width){long value=0;for(int i=0;i<width;i++)value|=(long)(b[offset+i]&255)<<(8*i);return value;}
 private static final class Mem implements PendingSlotCapacityKnownCopyFullState456.Memory {
  final Map<Long,Byte> cells=new HashMap<>();final List<Ev> events=new ArrayList<>();
  void raw(long a,byte[] b){for(int i=0;i<b.length;i++)cells.put(a+i,b[i]);}
  void seed(long a,long value,int width){raw(a,little(value,width));}
  byte[] peek(long a,int width){byte[] b=new byte[width];for(int i=0;i<width;i++){Byte v=cells.get(a+i);if(v==null)throw new AssertionError("unseeded "+Long.toUnsignedString(a+i,16));b[i]=v;}return b;}
  long peek64(long a){return scalar(peek(a,8),0,8);}
  int peek32(long a){return (int)scalar(peek(a,4),0,4);}
  String peekHex(long a,int width){return HexFormat.of().formatHex(peek(a,width));}
  byte[] read(long a,int width){byte[] b=peek(a,width);events.add(new Ev("R",width,a,HexFormat.of().formatHex(b)));return b;}
  void write(long a,byte[] b){raw(a,b);events.add(new Ev("W",b.length,a,HexFormat.of().formatHex(b)));}
  @Override public int readUnsignedByte(long a){return (int)scalar(read(a,1),0,1);}
  @Override public int read8(long a){return readUnsignedByte(a);}
  @Override public int readDword(long a){return (int)scalar(read(a,4),0,4);}
  @Override public int read32(long a){return readDword(a);}
  @Override public long readQword(long a){return scalar(read(a,8),0,8);}
  @Override public long read64(long a){return readQword(a);}
  @Override public void writeDword(long a,int v){write(a,little(v,4));}
  @Override public void write32(long a,int v){writeDword(a,v);}
  @Override public void writeQword(long a,long v){write(a,little(v,8));}
  @Override public void write64(long a,long v){writeQword(a,v);}
  @Override public void writeByte(long a,int v){write(a,new byte[]{(byte)v});}
  @Override public Bits128 read128(long a){byte[] b=read(a,16);return new Bits128(scalar(b,0,8),scalar(b,8,8));}
  @Override public void write128(long a,Bits128 v){byte[] b=new byte[16];System.arraycopy(little(v.lowBits(),8),0,b,0,8);System.arraycopy(little(v.highBits(),8),0,b,8,8);write(a,b);}
  private static UnsupportedOperationException unused(){return new UnsupportedOperationException("unexpected unused effect");}
  @Override public int lockedXaddDword(long a,int v){throw unused();}
  @Override public void writeWord(long a,int v){throw unused();}
  @Override public void write128NonTemporal(long a,Bits128 v){throw unused();}
  @Override public void sfence(){throw unused();}
  @Override public int readUnsignedWord(long a){throw unused();}
  @Override public FullCopy437Api.Bits256 read256(long a){throw unused();}
  @Override public void write256(long a,FullCopy437Api.Bits256 v){throw unused();}
  @Override public void write256NonTemporal(long a,FullCopy437Api.Bits256 v){throw unused();}
 }
 private static Mem seeded(){Mem m=new Mem();m.seed(E,RET,8);m.seed(T,D,8);m.seed(T+8,0,4);m.seed(T+0xC,1,4);m.seed(T+0x10,A,8);m.seed(A,VT,8);m.seed(VT+8,ALLOC,8);m.seed(A2,VT2,8);m.seed(VT2+0x10,RELEASE,8);byte[] old=new byte[16];for(int i=0;i<16;i++)old[i]=(byte)(0x80+i);m.raw(D,old);return m;}
 public static int verify() {
    Mem m = seeded();
    List<Ev> expectedTrace = FullCopyCallerWitness460.expectedTrace();
    PendingSlotCapacityFullState412Api.CallFrame expectedAlloc = ALLOC_FRAME;
    PendingSlotCapacityFullState412Api.CallFrame expectedRelease = RELEASE_FRAME;
    PendingSlotCapacityFullState412Api.CallResult expectedAllocReturn = ALLOC_RETURN;
    PendingSlotCapacityFullState412Api.CallResult expectedReleaseReturn = RELEASE_RETURN;
    PendingSlotCapacityFullState412Api.CallResult expectedNormal = NORMAL;
    int[] index = new int[1];
    GovernmentCrtBoundary185Api.LoopBudget budget = new GovernmentCrtBoundary185Api.LoopBudget() {
        public void beforeStep(long loopHeaderRva, long guardAddressBits) {
            throw new UnsupportedOperationException("unexpected loop hook");
        }
    };
    PendingSlotCapacityFullState412Api.Calls opaqueCalls = new PendingSlotCapacityFullState412Api.Calls() {
        public PendingSlotCapacityFullState412Api.CallResult invoke(PendingSlotCapacityFullState412Api.CallFrame frame) {
            if (index[0] == 0) {
                if (!frame.equals(expectedAlloc)) throw new AssertionError("alloc frame mismatch");
                if (m.peek64(frame.childEntry().rspBits()) != expectedAlloc.returnRipBits()) throw new AssertionError("alloc ret mismatch");
                index[0]++;
                m.writeQword(T + 0x10, A2);
                return expectedAllocReturn;
            } else if (index[0] == 1) {
                if (!frame.equals(expectedRelease)) throw new AssertionError("release frame mismatch");
                if (m.peek64(frame.childEntry().rspBits()) != expectedRelease.returnRipBits()) throw new AssertionError("release ret mismatch");
                index[0]++;
                m.writeDword(T + 0xC, 7);
                m.writeByte(B + 0x20, 0x77);
                return expectedReleaseReturn;
            } else {
                throw new AssertionError("unexpected invoke");
            }
        }
        public PendingSlotCapacityFullState412Api.CallResult tail(PendingSlotCapacityFullState412Api.TailFrame frame) {
            throw new UnsupportedOperationException("unexpected tail");
        }
        public long readGsQword58() {
            throw new UnsupportedOperationException("unexpected gs");
        }
    };
    PendingSlotCapacityFullState412Api.Calls bound = PendingSlotCapacityKnownCopyFullState456.bind(m, budget, opaqueCalls);
    if (!m.events.isEmpty()) throw new AssertionError("bind effects");
    PendingSlotCapacityFullState412Api.Input input = new PendingSlotCapacityFullState412Api.Input(new GovernmentCrtBoundary185Api.Entry(M, E, V0, N0), false, budget);
    PendingSlotCapacityFullState412Api.CallResult actual = PendingSlotArrayReserveFullState1ACE4B0.execute(input, m, bound);
    if (!actual.equals(expectedNormal)) throw new AssertionError("normal mismatch");
    if (index[0] != 2) throw new AssertionError("callback count mismatch");
    if (!m.events.equals(expectedTrace)) throw new AssertionError("trace mismatch");
    if (m.peek64(T) != B) throw new AssertionError("array mismatch");
    if (m.peek32(T + 8) != 2) throw new AssertionError("capacity mismatch");
    if (m.peek32(T + 0xC) != 1) throw new AssertionError("count mismatch");
    if (m.peek64(T + 0x10) != A2) throw new AssertionError("allocator mismatch");
    if (!m.peekHex(B, 16).equals("808182838485868788898a8b8c8d8e8f")) throw new AssertionError("newB payload mismatch");
    if (!m.peekHex(D, 16).equals("808182838485868788898a8b8c8d8e8f")) throw new AssertionError("oldD payload mismatch");
    if (!m.peekHex(B + 0x20, 1).equals("77")) throw new AssertionError("outside byte mismatch");
    return 1;
}
 public static void main(String[] args) {
    System.out.println(FullCopyCallerWitness460.verify());
}
}
