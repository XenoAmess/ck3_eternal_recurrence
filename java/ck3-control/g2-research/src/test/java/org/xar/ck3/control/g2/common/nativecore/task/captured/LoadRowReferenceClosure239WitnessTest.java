package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
public final class LoadRowReferenceClosure239WitnessTest {
 static Bits128 x(long b) {return new Bits128(b,b+1L);}
 static VolatileBits v(long b) {return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60));}
 static NonvolatileBits n(long b) {return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80));}
 static VolatileBits q(VolatileBits b,long a,long c,long d,long r8,long r9,long r10,long r11) {return new VolatileBits(a,c,d,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());}
 static final class Ports implements Calls {
  java.util.function.Function<Call,VolatileBits> invoke=c->{throw new AssertionError(c);};
  java.util.function.Function<Tail,NormalReturn> tail=t->{throw new AssertionError(t);};
  java.util.function.LongSupplier gs=()->{throw new AssertionError("GS58");};
  public VolatileBits invoke(Call c) {return invoke.apply(c);}
  public NormalReturn tail(Tail t) {return tail.apply(t);}
  public long readGsQword58() {return gs.getAsLong();}
 }

 static final LoadRowReferenceCallee337b7e0199Api.Float32 NO_FP=new LoadRowReferenceCallee337b7e0199Api.Float32() {
  public int convertSignedDwordToFloatBits(int bits) {throw new AssertionError("CVTDQ2PS");}
  public int divideScalarFloatBits(int left,int right) {throw new AssertionError("DIVSS");}
  public boolean orderedAbove(int left,int right) {throw new AssertionError("COMISS");}
 };
 @Test void naturalCapacityThreeRebuildsThenReentersThroughActualGraph() {
  long image=0x8800000100000000L,pre=0x7000000000200000L;
  long self=0x8200000000010000L,old=0x8300000000020000L,callerRows=0x8400000000030000L;
  long allocator=0x8500000000040000L,vptr=0x8600000000050000L,rows=0x8700000000060000L;
  long allocateTarget=0xF100000000004001L,freeTarget=0xF200000000004002L,key=0xDADA001122334455L;
  long descriptor=callerRows+0x08,out=pre+0x30,e=pre-8,w=e-0xC8,bp=e-0x57,cw=w-0x60,ce=w-8;
  Bytes m=new Bytes(); Ports fallback=new Ports();
  // Literal source-admissible C0@C198 context: active RSI=self, RBX=row+48, RBP=old table,
  // EDI=one remaining row, R14=0; R9=row+8, RDX=preSP+30, RAX=preSP+68, R8D=hash0.
  NonvolatileBits incomingN=new NonvolatileBits(callerRows+0x48,callerRows,self,1,
    0xA120000000000005L,0xA130000000000006L,0,0xA150000000000008L,x(0xB600000000000080L));
  VolatileBits seed=v(0x9100000000000100L);
  VolatileBits incoming=q(seed,pre+0x68,self,out,0,descriptor,0x9110000000000010L,0x9110000000000011L);
  m.putD(callerRows,0);m.putB(callerRows+4,1);m.putQ(descriptor,key);
  m.putQ(pre+0x20,pre+0x68);m.putB(pre+0x68,0);
  m.putQ(self+8,old);m.putD(self+0x10,0);m.putD(self+0x14,0);m.putB(self+0x18,0);m.putQ(self+0x20,allocator);
  m.putB(old+4,0);m.putQ(allocator,vptr);m.putQ(vptr+8,allocateTarget);m.putQ(vptr+0x10,freeTarget);

  VolatileBits a=v(0xA100000000000100L),b=v(0xB100000000000100L),c=v(0xC100000000000100L);
  VolatileBits allocation=q(a,rows,a.rcxBits(),a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits());
  VolatileBits first=q(b,old,b.rcxBits(),b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits());
  VolatileBits second=q(c,0xC222000000000022L,c.rcxBits(),c.rdxBits(),c.r8Bits(),c.r9Bits(),c.r10Bits(),c.r11Bits());
  VolatileBits released=v(0xD100000000000100L);
  NonvolatileBits allocatingN=new NonvolatileBits(8,old,self,0,incomingN.r12Bits(),0,0,descriptor,incomingN.xmm6());
  NonvolatileBits releasingN=new NonvolatileBits(old,old,self,1,incomingN.r12Bits(),0,out,descriptor,incomingN.xmm6());
  // These are explicit software-port inputs. They do not model a natural allocator or execute 8CEE.
  List<Call> expectedCalls=List.of(
    new Call(0x337C12EL,TargetKind.INDIRECT_ABSOLUTE,allocateTarget,cw,
      q(incoming,14,allocator,1120,8,allocateTarget,0,incoming.r11Bits()),allocatingN),
    new Call(0x337C161L,TargetKind.DIRECT_RVA,0x8CEEB0L,cw,
      q(allocation,rows+0x410,rows+0x410,13,allocation.r8Bits(),allocation.r9Bits(),allocation.r10Bits(),allocation.r11Bits()),allocatingN),
    new Call(0x337C1C3L,TargetKind.DIRECT_RVA,0x8CEEB0L,cw,first,allocatingN),
    new Call(0x337C1ECL,TargetKind.INDIRECT_ABSOLUTE,freeTarget,cw,
      q(second,vptr,allocator,old,8,second.r9Bits(),second.r10Bits(),second.r11Bits()),releasingN));
  assertEquals(4,expectedCalls.size());
  int[] calls={0};
  fallback.invoke=actual->{
   int i=calls[0]++;assertTrue(i<expectedCalls.size(),"unexpected opaque call");assertEquals(expectedCalls.get(i),actual);
   return switch(i) {
    case 0 -> allocation;
    case 1 -> first;
    case 2 -> second;
    case 3 -> {
     // Controlled last virtual callback makes the actual later child C5 probe match one literal key.
     m.putB(rows+4,1);m.putQ(rows+8,key);yield released;
    }
    default -> throw new AssertionError("extra opaque call");
   };
  };
  List<Op> expectedBudget=List.of(
    new Op("budget",0x337C150L,rows),new Op("budget",0x337C150L,rows+0x50),
    new Op("budget",0x337C150L,rows+0xA0),new Op("budget",0x337C150L,rows+0xF0),
    new Op("budget",0x337C150L,rows+0x140),new Op("budget",0x337C150L,rows+0x190),
    new Op("budget",0x337C150L,rows+0x1E0),new Op("budget",0x337C150L,rows+0x230),
    new Op("budget",0x337C150L,rows+0x280),new Op("budget",0x337C150L,rows+0x2D0),
    new Op("budget",0x337C150L,rows+0x320),new Op("budget",0x337C150L,rows+0x370),
    new Op("budget",0x337C150L,rows+0x3C0),new Op("budget",0x337C615L,rows));
  assertEquals(14,expectedBudget.size());
  List<Op> budgets=new ArrayList<>();
  LoopBudget budget=(pc,address)->{assertTrue(budgets.size()<expectedBudget.size(),"unexpected loop step");budgets.add(new Op("budget",pc,address));};
  List<Op> expected=List.of(
    new Op("wq",e,image+0x337C19DL),
    // Outer C5 seven pushes, initial probe and forced growth. Real Capacity204 reads its own RET slot.
    new Op("wq",e-8,callerRows),new Op("wq",e-0x10,callerRows+0x48),new Op("wq",e-0x18,self),
    new Op("wq",e-0x20,1),new Op("wq",e-0x28,incomingN.r13Bits()),new Op("wq",e-0x30,0),
    new Op("wq",e-0x38,incomingN.r15Bits()),new Op("rd",self+0x14,0),new Op("rq",self+8,old),
    new Op("rb",old+4,0),new Op("rb",self+0x18,0),
    new Op("wq",w-8,image+0x337C878L),new Op("rq",w-8,image+0x337C878L),
    new Op("wq",w-8,image+0x337C887L),
    // C0 slow frame. Natural Capacity returns EAX3; C0 derives mask7, distance5 and 13 rows.
    new Op("wq",w-0x10,self),new Op("wq",cw+0x60,old),new Op("wq",cw+0x70,bp),
    new Op("rq",self+8,old),new Op("wb",self+0x18,5),new Op("rq",self+0x20,allocator),
    new Op("wq",cw+0x48,1),new Op("rd",self+0x10,0),new Op("wq",cw+0x40,out),
    new Op("wd",self+0x14,7),new Op("wd",self+0x10,0),new Op("rq",allocator,vptr),
    new Op("rq",vptr+8,allocateTarget),new Op("wq",cw-8,image+0x337C131L),
    new Op("rb",self+0x18,5),new Op("wq",self+8,rows),
    new Op("wb",rows+4,0),new Op("wb",rows+0x54,0),new Op("wb",rows+0xA4,0),
    new Op("wb",rows+0xF4,0),new Op("wb",rows+0x144,0),new Op("wb",rows+0x194,0),
    new Op("wb",rows+0x1E4,0),new Op("wb",rows+0x234,0),new Op("wb",rows+0x284,0),
    new Op("wb",rows+0x2D4,0),new Op("wb",rows+0x324,0),new Op("wb",rows+0x374,0),
    new Op("wb",rows+0x3C4,0),new Op("wb",rows+0x414,0xFF),
    new Op("wq",cw-8,image+0x337C166L),new Op("wq",cw-8,image+0x337C1C8L),
    new Op("rq",cw+0x40,out),new Op("rq",cw+0x48,1),new Op("rq",cw+0x60,old),
    new Op("rq",self+0x20,allocator),new Op("rq",allocator,vptr),new Op("rq",vptr+0x10,freeTarget),
    new Op("wq",cw-8,image+0x337C1EFL),new Op("rq",cw+0x70,bp),
    new Op("rq",cw+0x50,self),new Op("rq",cw+0x58,image+0x337C887L),
    // Source writes the sixth-argument home then physically calls the real C5 child.
    new Op("wb",e+0x18,0),new Op("wq",w+0x20,e+0x18),new Op("wq",w-8,image+0x337C8A5L),
    new Op("wq",ce-8,bp),new Op("wq",ce-0x10,old),new Op("wq",ce-0x18,self),
    new Op("wq",ce-0x20,1),new Op("wq",ce-0x28,0),new Op("wq",ce-0x30,out),new Op("wq",ce-0x38,descriptor),
    new Op("rd",self+0x14,7),new Op("rq",self+8,rows),new Op("rb",rows+4,1),
    new Op("rq",descriptor,key),new Op("rq",rows+8,key),new Op("wq",out,rows),new Op("wb",out+8,0),
    new Op("rq",ce-0x38,descriptor),new Op("rq",ce-0x30,out),new Op("rq",ce-0x28,0),
    new Op("rq",ce-0x20,1),new Op("rq",ce-0x18,self),new Op("rq",ce-0x10,old),
    new Op("rq",ce-8,bp),new Op("rq",ce,image+0x337C8A5L),
    new Op("rq",e-0x38,incomingN.r15Bits()),new Op("rq",e-0x30,0),new Op("rq",e-0x28,incomingN.r13Bits()),
    new Op("rq",e-0x20,1),new Op("rq",e-0x18,self),new Op("rq",e-0x10,callerRows+0x48),
    new Op("rq",e-8,callerRows),new Op("rq",e,image+0x337C19DL));
  assertEquals(90,expected.size());assertEquals(List.of(),m.ops);
  Calls graph=LoadRowReferenceClosure239Calls.bind(image,m,fallback,budget,NO_FP);
  assertEquals(List.of(),m.ops);
  m.writeQword(e,image+0x337C19DL); // actual parent owns this one physical CALL push
  VolatileBits result=graph.invoke(new Call(0x337C198L,TargetKind.DIRECT_RVA,0x337C5D0L,pre,incoming,incomingN));
  assertEquals(q(released,out,7,out,0,descriptor,0,released.r11Bits()),result);
  assertEquals(4,calls[0]);assertEquals(expectedBudget,budgets);assertEquals(expected,m.ops);
 }
}
