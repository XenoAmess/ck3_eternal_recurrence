package org.xar.ck3.control.g2.m2.nativecode;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.*;
public final class PendingSlotFullStateWitness424 {
 private PendingSlotFullStateWitness424() { }
 static final long E=0x8100000000009008L,M=0x3300000000L,T=0x8100000000005000L,B=0x8100000000001000L,RET=0xAABBCCDD11223344L;
 static int assertions;
 static void eq(Object e,Object a,String why){assertions++;if(!java.util.Objects.equals(e,a))throw new AssertionError(why+" expected="+e+" actual="+a);}
 static Bits128 x(long n){return new Bits128(n,~n);}
 static VolatileBits v(long seed,long ax,long cx,long dx){return new VolatileBits(ax,cx,dx,seed+8,seed+9,seed+10,seed+11,x(seed+0x10),x(seed+0x20),x(seed+0x30),x(seed+0x40),x(seed+0x50),x(seed+0x60));}
 static NonvolatileBits n(long bx,long bp,long si,long di){return new NonvolatileBits(bx,bp,si,di,0x2005,0x2006,0x2007,0x2008,x(0x2060));}
 static NonvolatileBits n(){return n(0x2001,0x2002,0x2003,0x2004);}
 record Ev(String op,long address,long bits) { }
 static Ev e(String op,long a,long b){return new Ev(op,a,b);}
 static final class Mem implements Memory {
  final Map<Long,Byte> bytes=new HashMap<>();final List<Ev> trace=new ArrayList<>();
  int byteAt(long a){Byte b=bytes.get(a);if(b==null)throw new UnsupportedOperationException("unseeded "+Long.toUnsignedString(a,16));return Byte.toUnsignedInt(b);}
  long peek(long a,int width){long r=0;for(int i=0;i<width;i++)r|=(long)byteAt(a+i)<<(i*8);return r;}
  void seed(long a,long bits,int width){for(int i=0;i<width;i++)bytes.put(a+i,(byte)(bits>>>(8*i)));}
  @Override public int readUnsignedByte(long a){int r=byteAt(a);trace.add(e("R8",a,r));return r;}
  @Override public int readDword(long a){int r=(int)peek(a,4);trace.add(e("R32",a,Integer.toUnsignedLong(r)));return r;}
  @Override public long readQword(long a){long r=peek(a,8);trace.add(e("R64",a,r));return r;}
  @Override public void writeByte(long a,int b){seed(a,b,1);trace.add(e("W8",a,b&255L));}
  @Override public void writeDword(long a,int b){seed(a,Integer.toUnsignedLong(b),4);trace.add(e("W32",a,Integer.toUnsignedLong(b)));}
  @Override public void writeQword(long a,long b){seed(a,b,8);trace.add(e("W64",a,b));}
  @Override public int read8(long a){return readUnsignedByte(a);}
  @Override public int read32(long a){return readDword(a);}
  @Override public long read64(long a){return readQword(a);}
  @Override public void write32(long a,int b){writeDword(a,b);}
  @Override public void write64(long a,long b){writeQword(a,b);}
  @Override public int lockedXaddDword(long a,int b){throw new UnsupportedOperationException("unused atomic");}
  @Override public Bits128 read128(long a){throw new UnsupportedOperationException("unused128");}
  @Override public void write128(long a,Bits128 b){throw new UnsupportedOperationException("unused128");}
  @Override public void writeWord(long a,int b){throw new UnsupportedOperationException("unusedWORD");}
  @Override public void write128NonTemporal(long a,Bits128 b){throw new UnsupportedOperationException("unusedNT");}
  @Override public void sfence(){throw new UnsupportedOperationException("unusedFENCE");}
 }
 record Want(CallFrame frame,CallResult result,Runnable effect) { }
 static CallFrame f(long site,TargetKind kind,long target,long sp,VolatileBits v,NonvolatileBits n,boolean df,int len,long ret){
  return new CallFrame(new Call(site,kind,target,sp,v,n),new Entry(M,sp-8,v,n),df,len,ret);
 }
 static final class Ports implements Calls {
  final Mem mem;final List<Want> wants=new ArrayList<>();int index;
  Ports(Mem m){mem=m;}
  Ports expect(CallFrame f,CallResult r,Runnable effect){wants.add(new Want(f,r,effect));return this;}
  @Override public CallResult invoke(CallFrame actual){
   if(index>=wants.size())throw new AssertionError("unexpected call "+actual);
   Want w=wants.get(index++);eq(w.frame(),actual,"whole expectedCallFrame "+index);
   eq(w.frame().returnRipBits(),mem.peek(w.frame().childEntry().rspBits(),8),"actual caller-owned return push "+index);
   w.effect().run();return w.result();
  }
  @Override public CallResult tail(TailFrame f){throw new AssertionError("unexpectedtail "+f);}
  @Override public long readGsQword58(){throw new AssertionError("unexpectedGS");}
  void done(){eq(wants.size(),index,"exact call count");}
 }
static void book372(){
 Mem mem=new Mem();Ports ports=new Ports(mem);
 mem.seed(E,RET,8);mem.seed(T+0x40,0,1);mem.seed(T+0x24,0,4);mem.seed(T+0x38,0xFFFFFF,4);
 VolatileBits incomingV=v(0x1000L,0x8877665544332211L,T,1);
 NonvolatileBits originalN=n(),callN=n(0,T,1,0x2004);
 VolatileBits reserveV=v(0x1000L,0x8877665544332211L,T+0x18,1);
 VolatileBits reservePost=v(0x3000L,0xAAAABBBBCCCCDDDDL,0x3132333435363738L,0x4142434445464748L);
 VolatileBits setV=new VolatileBits(1,B,0,16,0x3009,0x300A,0x300B,
     x(0x3010),x(0x3020),x(0x3030),x(0x3040),x(0x3050),x(0x3060));
 VolatileBits setPost=v(0x4000L,0xFACEFEED12345678L,0x5152535455565758L,0x6162636465666768L);
 CallFrame reserveFrame=f(0x1ACDFF3L,TargetKind.DIRECT_RVA,0x1ACE4B0L,E-0x28,reserveV,callN,false,5,M+0x1ACDFF8L);
 CallFrame setFrame=f(0x1ACE015L,TargetKind.DIRECT_RVA,0x4226F10L,E-0x28,setV,callN,true,5,M+0x1ACE01AL);
 ports.expect(reserveFrame,new CallResult(new NormalReturn(reservePost,M+0x1ACDFF8L,E-0x28,callN),true),()->mem.writeQword(T+0x18,B));
 ports.expect(setFrame,new CallResult(new NormalReturn(setPost,M+0x1ACE01AL,E-0x28,callN),false),()->mem.writeByte(B+0x20,0x5A));
 VolatileBits finalV=new VolatileBits(0x8100000000001001L,0xFFFFFFFFL,0,0,B,0,0,
     x(0x4010),x(0x4020),x(0x4030),x(0x4040),x(0x4050),x(0x4060));
 CallResult expected=new CallResult(new NormalReturn(finalV,RET,E+8,originalN),false);
 List<Ev> expectedTrace=List.of(
     e("W64",0x8100000000009018L,0x2001L),e("W64",0x8100000000009020L,0x2002L),
     e("W64",0x8100000000009000L,0x2003L),e("R8",0x8100000000005040L,0),
     e("R32",0x8100000000005024L,0),e("W64",0x8100000000009010L,0x2004L),
     e("R32",0x8100000000005024L,0),e("W64",0x8100000000008FD8L,0x3301ACDFF8L),
     e("W64",0x8100000000005018L,0x8100000000001000L),e("R32",0x8100000000005024L,0),
     e("R64",0x8100000000005018L,0x8100000000001000L),e("W64",0x8100000000008FD8L,0x3301ACE01AL),
     e("W8",0x8100000000001020L,0x5A),e("W32",0x8100000000005024L,1),
     e("STEP",0x1ACE030L,0),e("R64",0x8100000000005018L,0x8100000000001000L),
     e("W32",0x8100000000001004L,0xFFFFFF),e("R64",0x8100000000005018L,0x8100000000001000L),
     e("W64",0x8100000000001008L,0),e("R64",0x8100000000005018L,0x8100000000001000L),
     e("W32",0x8100000000001000L,0xFFFFFF),e("STEP",0x1ACE030L,0xFFFFFFFFL),
     e("R32",0x8100000000005038L,0xFFFFFF),e("R64",0x8100000000009010L,0x2004L),
     e("W32",0x8100000000005038L,0),e("R64",0x8100000000009018L,0x2001L),
     e("R64",0x8100000000009020L,0x2002L),e("R64",0x8100000000009000L,0x2003L),
     e("R64",0x8100000000009008L,0xAABBCCDD11223344L));
 Input input=new Input(new Entry(M,E,incomingV,originalN),false,(h,a)->mem.trace.add(e("STEP",h,a)));
 CallResult actual=PendingSlotCapacityFullState1ACDFB0.execute(input,mem,ports);
 eq(expected,actual,"372 whole V/N/XMM/actualRET/SP/postDF");
 eq(expectedTrace,mem.trace,"372 exact source and ownedcallee effects");ports.done();
 eq(1L,mem.peek(T+0x24,4),"372 count");eq(0L,mem.peek(T+0x38,4),"372 head");
 eq(0xFFFFFFL,mem.peek(B,4),"372 slot0 index");eq(0xFFFFFFL,mem.peek(B+4,4),"372 slot0 marker");
 eq(0L,mem.peek(B+8,8),"372 slot0 qword");eq(0x5AL,mem.peek(B+0x20,1),"372 owned opaque SET sideeffect");
}

static void book133(){
    Mem mem = new Mem();
    Ports ports = new Ports(mem);

    mem.seed(0x8100000000009008L, 0xAABBCCDD11223344L, 8);

    long T = 0x8100000000005000L;
    long A = 0x8100000000006000L;
    long A2 = 0x8100000000006100L;
    long VT = 0x8100000000007000L;
    long VT2 = 0x8100000000007100L;
    long B = 0x8100000000001000L;

    mem.seed(T, 0x8100000000003000L, 8);
    mem.seed(T + 8, 0, 4);
    mem.seed(T + 0xC, 0, 4);
    mem.seed(T + 0x10, A, 8);
    mem.seed(A, VT, 8);
    mem.seed(VT + 8, 0x7FFF111122223333L, 8);
    mem.seed(A2, VT2, 8);
    mem.seed(VT2 + 0x10, 0x7FFF444455556666L, 8);

    long imageBase = 0x0000003300000000L;
    long entrySP = 0x8100000000009008L;
    boolean initialDF = false;

    NonvolatileBits origN = n(0x0000000000002001L, 0x0000000000002002L, 0x0000000000002003L, 0x0000000000002004L);

    long s = 0x8877665544332211L;
    VolatileBits inV = new VolatileBits(
        s,
        0x8100000000005000L,
        0x0000000000000001L,
        0x0000000000001008L,
        0x0000000000001009L,
        0x000000000000100AL,
        0x000000000000100BL,
        x(0x0000000000001010L), x(0x0000000000001020L), x(0x0000000000001030L),
        x(0x0000000000001040L), x(0x0000000000001050L), x(0x0000000000001060L)
    );

    VolatileBits f1V = new VolatileBits(
        0x8100000000007000L, 0x8100000000006000L, 0x0000000000000010L,
        0x0000000000000008L, 0x0000000000001009L, 0x000000000000100AL, 0x000000000000100BL,
        x(0x0000000000001010L), x(0x0000000000001020L), x(0x0000000000001030L),
        x(0x0000000000001040L), x(0x0000000000001050L), x(0x0000000000001060L)
    );
    NonvolatileBits f1N = new NonvolatileBits(
        0x8100000000005000L, 0x0000000000002002L, 0x0000000000002003L, 0x0000000000000001L,
        0x0000000000002005L, 0x0000000000002006L, 0x0000000000002007L, 0x0000000000002008L,
        x(0x0000000000002060L)
    );

    CallFrame cf1 = new CallFrame(
        new Call(0x1ACE4E1L, TargetKind.INDIRECT_ABSOLUTE, 0x7FFF111122223333L, 0x8100000000008FE0L, f1V, f1N),
        new Entry(imageBase, 0x8100000000008FD8L, f1V, f1N),
        false, 3, 0x0000003301ACE4E4L
    );

    VolatileBits cb1V = new VolatileBits(
        0x8100000000001000L, 0x7172737475767778L, 0x8182838485868788L,
        0x0000000000005008L, 0x0000000000005009L, 0x000000000000500AL, 0x000000000000500BL,
        x(0x0000000000005010L), x(0x0000000000005020L), x(0x0000000000005030L),
        x(0x0000000000005040L), x(0x0000000000005050L), x(0x0000000000005060L)
    );

    NormalReturn nr1 = new NormalReturn(cb1V, 0x0000003301ACE4E4L, 0x8100000000008FE0L, f1N);
    CallResult cr1 = new CallResult(nr1, true);
    Runnable eff1 = () -> { mem.writeQword(T + 0x10, A2); };

    ports.expect(cf1, cr1, eff1);

    VolatileBits f2V = new VolatileBits(
        0x8100000000007100L, 0x8100000000006100L, 0x8100000000003000L,
        0x0000000000000008L, 0x0000000000005009L, 0x000000000000500AL, 0x000000000000500BL,
        x(0x0000000000005010L), x(0x0000000000005020L), x(0x0000000000005030L),
        x(0x0000000000005040L), x(0x0000000000005050L), x(0x0000000000005060L)
    );
    NonvolatileBits f2N = new NonvolatileBits(
        0x8100000000005000L, 0x8100000000001000L, 0x0000000000000000L, 0x0000000000000001L,
        0x0000000000002005L, 0x0000000000002006L, 0x0000000000002007L, 0x0000000000002008L,
        x(0x0000000000002060L)
    );

    CallFrame cf2 = new CallFrame(
        new Call(0x1ACE514L, TargetKind.INDIRECT_ABSOLUTE, 0x7FFF444455556666L, 0x8100000000008FE0L, f2V, f2N),
        new Entry(imageBase, 0x8100000000008FD8L, f2V, f2N),
        true, 3, 0x0000003301ACE517L
    );

    VolatileBits cb2V = new VolatileBits(
        0xDEADBEEF87654321L, 0x9192939495969798L, 0xA1A2A3A4A5A6A7A8L,
        0x0000000000006008L, 0x0000000000006009L, 0x000000000000600AL, 0x000000000000600BL,
        x(0x0000000000006010L), x(0x0000000000006020L), x(0x0000000000006030L),
        x(0x0000000000006040L), x(0x0000000000006050L), x(0x0000000000006060L)
    );

    NormalReturn nr2 = new NormalReturn(cb2V, 0x0000003301ACE517L, 0x8100000000008FE0L, f2N);
    CallResult cr2 = new CallResult(nr2, false);
    Runnable eff2 = () -> { mem.writeDword(T + 0xC, 7); mem.writeByte(B + 0x20, 0x77); };

    ports.expect(cf2, cr2, eff2);

    Input input = new Input(new Entry(imageBase, entrySP, inV, origN), initialDF, new GovernmentCrtBoundary185Api.LoopBudget() { @Override public void beforeStep(long h, long c) { throw new AssertionError("133 budget"); } });
    CallResult actual = PendingSlotArrayReserveFullState1ACE4B0.execute(input, mem, ports);

    VolatileBits finalV = new VolatileBits(
        0xDEADBEEF87654321L, 0x9192939495969798L, 0xA1A2A3A4A5A6A7A8L,
        0x0000000000006008L, 0x0000000000006009L, 0x000000000000600AL, 0x000000000000600BL,
        x(0x0000000000006010L), x(0x0000000000006020L), x(0x0000000000006030L),
        x(0x0000000000006040L), x(0x0000000000006050L), x(0x0000000000006060L)
    );
    NormalReturn expectedNR = new NormalReturn(finalV, 0xAABBCCDD11223344L, 0x8100000000009010L, origN);
    CallResult expectedCR = new CallResult(expectedNR, false);

    eq(expectedCR, actual, "Final CallResult");

    List<Ev> expectedTrace = List.of(
        e("W64", 0x8100000000009020L, 0x0000000000002001L),
        e("W64", 0x8100000000009000L, 0x0000000000002004L),
        e("R32", 0x8100000000005008L, 0x0000000000000000L),
        e("R64", 0x8100000000005010L, 0x8100000000006000L),
        e("W64", 0x8100000000009010L, 0x0000000000002002L),
        e("W64", 0x8100000000009018L, 0x0000000000002003L),
        e("R64", 0x8100000000006000L, 0x8100000000007000L),
        e("R64", 0x8100000000007008L, 0x7FFF111122223333L),
        e("W64", 0x8100000000008FD8L, 0x0000003301ACE4E4L),
        e("W64", 0x8100000000005010L, 0x8100000000006100L),
        e("R32", 0x810000000000500CL, 0x0000000000000000L),
        e("R64", 0x8100000000005010L, 0x8100000000006100L),
        e("R64", 0x8100000000005000L, 0x8100000000003000L),
        e("R64", 0x8100000000006100L, 0x8100000000007100L),
        e("R64", 0x8100000000007110L, 0x7FFF444455556666L),
        e("W64", 0x8100000000008FD8L, 0x0000003301ACE517L),
        e("W32", 0x810000000000500CL, 0x0000000000000007L),
        e("W8", 0x8100000000001020L, 0x0000000000000077L),
        e("W64", 0x8100000000005000L, 0x8100000000001000L),
        e("R64", 0x8100000000009010L, 0x0000000000002002L),
        e("W32", 0x810000000000500CL, 0x0000000000000000L),
        e("R64", 0x8100000000009018L, 0x0000000000002003L),
        e("W32", 0x8100000000005008L, 0x0000000000000001L),
        e("R64", 0x8100000000009020L, 0x0000000000002001L),
        e("R64", 0x8100000000009000L, 0x0000000000002004L),
        e("R64", 0x8100000000009008L, 0xAABBCCDD11223344L)
    );
    eq(expectedTrace, mem.trace, "Trace");

    ports.done();

    eq(0x8100000000001000L, mem.peek(T, 8), "T");
    eq(1L, mem.peek(T + 8, 4), "T+8");
    eq(0L, mem.peek(T + 0xC, 4), "T+C");
    eq(0x8100000000006100L, mem.peek(T + 0x10, 8), "T+10");
    eq(0x77L, mem.peek(B + 0x20, 1), "B+20");
}

 public static void verify(){book372();book133();}
 public static void main(String[] args){verify();System.out.println("FullState424 scenes=2 explicit="+assertions);}
}
