package org.xar.ck3.control.g2.m2.nativecode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.*;
/** Mechanical storage/event/assertion support. No SET target or oracle algorithm. */
public final class PendingSlotCapacityKnownSet412Witness {
 private PendingSlotCapacityKnownSet412Witness() { }
 static final long I=0x140000000L,S=0x70000008L,RET=I+0x1ACE01AL,P=0xABABABABABABABABL;
 static int assertions;
 static void eq(Object e,Object a,String what){assertions++;if(!Objects.equals(e,a))throw new AssertionError(what+" expected="+e+" actual="+a);}
 static void same(Object e,Object a,String what){assertions++;if(e!=a)throw new AssertionError(what+" identity");}
 static Bits128 x(long n){return new Bits128(n,~n);}
 static VolatileBits incoming(long d,long count){return new VolatileBits(0x8877665544332211L,d,0xFEDCBA98765432ABL,count,0x1009L,0x100AL,0x100BL,x(0x1010),x(0x1020),x(0x1030),x(0x1040),x(0x1050),x(0x1060));}
 static NonvolatileBits nv(){return new NonvolatileBits(0x2001,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008,x(0x2060));}
 record Event(String op,long address,long low,long high) { }
 static Event e(String op,long a,long b){return new Event(op,a,b,0);}
 static final class Mem implements Memory {
  final GovernmentSharedComposition168Fixture.MemoryImage raw=new GovernmentSharedComposition168Fixture.MemoryImage();
  final List<Event> trace=new ArrayList<>();
  void seedD(long a,int v){raw.writeDword(a,v);} void seedB(long a,int v){raw.writeByte(a,v);}
  @Override public int readUnsignedByte(long a){int v=raw.readUnsignedByte(a);trace.add(e("R8",a,v));return v;}
  @Override public int readDword(long a){int v=raw.readDword(a);trace.add(e("R32",a,Integer.toUnsignedLong(v)));return v;}
  @Override public long readQword(long a){long v=raw.readQword(a);trace.add(e("R64",a,v));return v;}
  @Override public void writeByte(long a,int v){raw.writeByte(a,v);trace.add(e("W8",a,v&255L));}
  @Override public void writeDword(long a,int v){raw.writeDword(a,v);trace.add(e("W32",a,Integer.toUnsignedLong(v)));}
  @Override public void writeQword(long a,long v){raw.writeQword(a,v);trace.add(e("W64",a,v));}
  @Override public Bits128 read128(long a){Bits128 v=raw.read128(a);trace.add(new Event("R128",a,v.lowBits(),v.highBits()));return v;}
  @Override public void write128(long a,Bits128 v){raw.write128(a,v);trace.add(new Event("W128",a,v.lowBits(),v.highBits()));}
  @Override public void writeWord(long a,int v){raw.writeByte(a,v);raw.writeByte(a+1,v>>>8);trace.add(e("W16",a,v&65535L));}
  @Override public void write128NonTemporal(long a,Bits128 v){raw.write128(a,v);trace.add(new Event("NT128",a,v.lowBits(),v.highBits()));}
  @Override public void sfence(){trace.add(e("FENCE",0,0));}
  @Override public int lockedXaddDword(long a,int v){int old=raw.lockedXaddDword(a,v);trace.add(new Event("XA32",a,Integer.toUnsignedLong(old),Integer.toUnsignedLong(v)));return old;}
  @Override public int read8(long a){return readUnsignedByte(a);}
  @Override public int read32(long a){return readDword(a);}
  @Override public long read64(long a){return readQword(a);}
  @Override public void write32(long a,int v){writeDword(a,v);}
  @Override public void write64(long a,long v){writeQword(a,v);}
 }
 static CallFrame setFrame(Mem m,long d,long count,boolean df){
  VolatileBits v=incoming(d,count);NonvolatileBits n=nv();
  Call c=new Call(0x1ACE015L,TargetKind.DIRECT_RVA,0x4226F10L,S+8,v,n);
  CallFrame f=new CallFrame(c,new Entry(I,S,v,n),df,5,RET);
  m.writeQword(S,RET); // Exactly one caller-owned physical CALL push; no target semantics here.
  return f;
 }
 static final class Ports implements Calls {
  Function<CallFrame,CallResult> onCall=f->{throw new AssertionError("unexpected invoke "+f);};
  Function<TailFrame,CallResult> onTail=f->{throw new AssertionError("unexpected tail "+f);};
  int invokes,tails,gs;
  @Override public CallResult invoke(CallFrame f){invokes++;return onCall.apply(f);}
  @Override public CallResult tail(TailFrame f){tails++;return onTail.apply(f);}
  @Override public long readGsQword58(){gs++;return 0x1122334455667788L;}
 }
 static GovernmentCrtBoundary185Api.LoopBudget noBudget(){return(h,a)->{throw new AssertionError("unexpected budget "+h);};}
 static void small(){
  long d=0x60001003L;Mem m=new Mem();Ports p=new Ports();
  m.seedD(I+0x60900B8L,0x04227077);
  CallFrame f=setFrame(m,d,2,true);
  Calls bound=PendingSlotCapacityKnownSet412.bind(m,noBudget(),p);
  eq(List.of(e("W64",S,RET)),m.trace,"small bind owns no memory effects");
  VolatileBits expectedV=new VolatileBits(0x60001003L,0x60001005L,P,2,0x144227077L,0x100AL,0x60001003L,
      x(0x1010),x(0x1020),x(0x1030),x(0x1040),x(0x1050),x(0x1060));
  CallResult expected=new CallResult(new NormalReturn(expectedV,RET,0x70000010L,nv()),true);
  CallResult actual=bound.invoke(f);
  eq(expected,actual,"small complete V/N/XMM/RIP/SP/DF");
  eq(List.of(e("W64",S,RET),e("R32",I+0x60900B8L,0x04227077L),
      e("W16",0x60001003L,0xABABL),e("R64",S,RET)),m.trace,"small exact source effects");
  eq(0xAB,m.raw.readUnsignedByte(d),"small shared first byte");
  eq(0xAB,m.raw.readUnsignedByte(d+1),"small shared second byte");
  eq(0,p.invokes,"small foreign invoke count");eq(0,p.tails,"small foreign tail count");eq(0,p.gs,"small GS count");
 }
 static void rep(boolean df){
  long d=df?0x60003080L:0x60002080L;Mem m=new Mem();Ports p=new Ports();
  m.seedB(I+0x5C5CBB0L,2);
  GovernmentCrtBoundary185Api.LoopBudget budget=(h,a)->m.trace.add(e("STEP",h,a));
  CallFrame f=setFrame(m,d,129,df);
  Calls bound=PendingSlotCapacityKnownSet412.bind(m,budget,p);
  eq(List.of(e("W64",S,RET)),m.trace,"REP bind adds no push/read");
  VolatileBits expectedV=new VolatileBits(d,0,0xABL,129,P,0x100AL,d,
      new Bits128(P,P),x(0x1020),x(0x1030),x(0x1040),x(0x1050),x(0x1060));
  CallResult expected=new CallResult(new NormalReturn(expectedV,RET,0x70000010L,nv()),df);
  List<Event> events=new ArrayList<>();
  events.add(e("W64",S,RET));events.add(e("R8",I+0x5C5CBB0L,2));events.add(e("W64",S-8,0x2004));
  for(int j=0;j<129;j++){
   long a=df?0x60003080L-j:0x60002080L+j;
   events.add(e("STEP",0x4226EF9L,a));events.add(e("W8",a,0xAB));
  }
  events.add(e("R64",S-8,0x2004));events.add(e("R64",S,RET));
  CallResult actual=bound.invoke(f);
  eq(expected,actual,"REP complete V/N/XMM/RIP/SP/DF "+df);
  eq(events,m.trace,"REP caller push/source PUSH/budget-before-write/fresh POP+RET "+df);
  for(int j=0;j<129;j++)eq(0xAB,m.raw.readUnsignedByte(df?0x60003080L-j:0x60002080L+j),"REP same storage byte "+j);
  eq(0x2004L,m.raw.readQword(S-8),"REP saved RDI same storage");
  eq(RET,m.raw.readQword(S),"REP caller return same storage");
  eq(0,p.invokes,"REP foreign invokes");eq(0,p.tails,"REP foreign tails");eq(0,p.gs,"REP GS");
 }
 static void budgetFailure(){
  Mem m=new Mem();Ports p=new Ports();m.seedB(I+0x5C5CBB0L,2);
  RuntimeException marker=new RuntimeException("owned same-budget rejection");
  GovernmentCrtBoundary185Api.LoopBudget budget=(h,a)->{m.trace.add(e("STEP",h,a));throw marker;};
  CallFrame f=setFrame(m,0x60004080L,129,true);
  Calls bound=PendingSlotCapacityKnownSet412.bind(m,budget,p);
  eq(List.of(e("W64",S,RET)),m.trace,"budget bind effects");
  try{bound.invoke(f);throw new AssertionError("budget rejection was swallowed");}
  catch(RuntimeException actual){same(marker,actual,"same budget marker propagated");}
  eq(List.of(e("W64",S,RET),e("R8",I+0x5C5CBB0L,2),e("W64",S-8,0x2004),
      e("STEP",0x4226EF9L,0x60004080L)),m.trace,"budget rejects before first BYTE and before POP/RET");
  eq(0,p.invokes,"budget foreign invokes");eq(0,p.tails,"budget foreign tails");eq(0,p.gs,"budget GS");
 }
 static void unknownAndGuards(){
  for(int variant=0;variant<4;variant++){
   Mem m=new Mem();Ports p=new Ports();long d=0x60005003L;
   m.seedD(I+0x60900B8L,0xF2227077);m.seedD(d+4,0x55667788);
   CallFrame f=setFrame(m,d,2,true);
   VolatileBits beforeV=new VolatileBits(0x60005003L,0x60005005L,P,2,0x232227077L,0x100AL,0x60005003L,
       x(0x1010),x(0x1020),x(0x1030),x(0x1040),x(0x1050),x(0x1060));
   Tail expectedTail=new Tail(0x422703BL,TargetKind.INDIRECT_ABSOLUTE,0x232227077L,new Entry(I,S,beforeV,nv()));
   VolatileBits opaqueV=GovernmentSharedComposition168Fixture.bits(0x5000L,0xCAFEBABE11223344L,0xCAFEBABE22334455L,0xCAFEBABE33445566L);
   NonvolatileBits offeredN=nv();
   NonvolatileBits returnedN=variant==3?new NonvolatileBits(0x2002,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008,x(0x2060)):offeredN;
   CallResult offered=new CallResult(new NormalReturn(opaqueV,variant==1?RET+1:RET,
       variant==2?0x70000018L:0x70000010L,returnedN),false);
   p.onTail=actual->{eq(expectedTail,actual.transfer(),"unknown full actual beforeframe");
    eq(true,actual.directionFlagSet(),"unknown current DF");m.write32(d,0x11223344);return offered;};
   Calls bound=PendingSlotCapacityKnownSet412.bind(m,noBudget(),p);
   eq(List.of(e("W64",S,RET)),m.trace,"unknown bind effects");
   if(variant==0){
    CallResult actual=bound.invoke(f);same(offered,actual,"whole unknown-tail NR plus changed DF identity");
    eq(offered,actual,"unknown complete opaque poststate");
   }else{
    boolean rejected=false;
    try{bound.invoke(f);}catch(IllegalArgumentException|UnsupportedOperationException expected){rejected=true;}
    eq(true,rejected,"binder rejects actual normal contract field "+variant);
   }
   List<Event> expectedEvents=new ArrayList<>(List.of(e("W64",S,RET),e("R32",I+0x60900B8L,0xF2227077L),e("W32",d,0x11223344L)));
   eq(expectedEvents,m.trace,"unknown source no extra CALL or RET "+variant);
   eq(0,p.invokes,"unknown foreign invokes");eq(1,p.tails,"unknown tail count");eq(0,p.gs,"unknown GS");
   if(variant==0){
    eq(0x44,m.read8(d),"M2read8 aliases callback DWORD storage");
    eq(0x11223344,m.read32(d),"M2read32 aliases callback DWORD storage");
    eq(0x5566778811223344L,m.read64(d),"M2read64 aliases same full backing");
    expectedEvents.add(e("R8",d,0x44));expectedEvents.add(e("R32",d,0x11223344L));expectedEvents.add(e("R64",d,0x5566778811223344L));
    eq(expectedEvents,m.trace,"separate fixture alias checks are explicit after source trace");
   }
  }
 }
 static void forward(){
  Mem m=new Mem();Ports p=new Ports();VolatileBits v=incoming(0x60006000L,10);NonvolatileBits n=nv();
  long foreignRET=I+0x1ACDFF8L;
  Call c=new Call(0x1ACDFF3L,TargetKind.DIRECT_RVA,0x1ACE4B0L,S+8,v,n);
  CallFrame frame=new CallFrame(c,new Entry(I,S,v,n),true,5,foreignRET);
  m.writeQword(S,foreignRET);
  VolatileBits opaqueV=GovernmentSharedComposition168Fixture.bits(0x8000L,0x1234567890ABCDEFL,0x234567890ABCDEFFL,0x34567890ABCDEFF1L);
  NonvolatileBits opaqueN=new NonvolatileBits(0x9001,0x9002,0x9003,0x9004,0x9005,0x9006,0x9007,0x9008,x(0x9060));
  CallResult invokeResult=new CallResult(new NormalReturn(opaqueV,0x1111222233334444L,0x5555666677778888L,opaqueN),false);
  p.onCall=actual->{same(frame,actual,"foreign invoke frame identity");return invokeResult;};
  TailFrame tailFrame=new TailFrame(new Tail(0x123456L,TargetKind.INDIRECT_ABSOLUTE,0x7FFF123456789ABCL,
      new Entry(I,0x71000008L,v,n)),false);
  CallResult tailResult=new CallResult(new NormalReturn(opaqueV,0x9999AAAABBBBCCCCL,0xDDDDEEEEFFFF1111L,opaqueN),true);
  p.onTail=actual->{same(tailFrame,actual,"foreign tail frame identity");return tailResult;};
  Calls bound=PendingSlotCapacityKnownSet412.bind(m,noBudget(),p);
  eq(List.of(e("W64",S,foreignRET)),m.trace,"foreign bind effects");
  same(invokeResult,bound.invoke(frame),"foreign invoke result identity");
  same(tailResult,bound.tail(tailFrame),"foreign tail result identity");
  eq(0x1122334455667788L,bound.readGsQword58(),"foreign GS actual value");
  eq(1,p.invokes,"foreign invoke count");eq(1,p.tails,"foreign tail count");eq(1,p.gs,"foreign GS count");
  eq(List.of(e("W64",S,foreignRET)),m.trace,"foreign channels add no target effects");
 }
 public static void main(String[] args){small();rep(false);rep(true);budgetFailure();unknownAndGuards();forward();System.out.println("SET412 binder scenes=9 guards=3 explicit="+assertions);}
}
