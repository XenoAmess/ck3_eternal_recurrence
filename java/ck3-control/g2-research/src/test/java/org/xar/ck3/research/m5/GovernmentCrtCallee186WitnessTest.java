package org.xar.ck3.research.m5;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentCrtCallee186WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentCrtCallee186WitnessTest {
 @Test void fiveIndependentlyAuthoredCalleeWitnesses() {assertEquals(5,GovernmentCrtCallee186WitnessRunner.verifyAll(new GovernmentCrtCallee186WitnessBook()));}
 @Test void twoIndependentlyAuthoredActualCallerWitnesses() {assertEquals(2,GovernmentCrtCallee186WitnessRunner.verifyAll(new GovernmentCrtCaller186WitnessBook()));}
 @Test void unmatchedCallsTailAndGsForwardOriginalObjectsAndBits() {
  Witness w=new GovernmentCrtCallee186WitnessBook().witnesses().get(0);
  List<Call> forwarded=new ArrayList<>();List<Tail> tails=new ArrayList<>();
  VolatileBits returned=w.events().get(0).normalPost();NormalReturn tailReturned=w.expected();
  Calls fallback=new Calls(){
   @Override public VolatileBits invoke(Call c){forwarded.add(c);return returned;}
   @Override public NormalReturn tail(Tail t){tails.add(t);return tailReturned;}
   @Override public long readGsQword58(){return Long.MIN_VALUE;}
  };
  Calls bound=GovernmentCrtCallee186Calls.bind(w.entry().imageBaseBits(),null,fallback);
  Call wrongKind=new Call(0x4223F28L,TargetKind.INDIRECT_ABSOLUTE,0x4223EE8L,19L,w.entry().volatileBits(),w.entry().nonvolatileBits());
  Call wrongSite=new Call(0x4223F29L,TargetKind.DIRECT_RVA,0x4223EE8L,21L,w.entry().volatileBits(),w.entry().nonvolatileBits());
  Call wrongTarget=new Call(0x4223F28L,TargetKind.DIRECT_RVA,0x4223EE9L,23L,w.entry().volatileBits(),w.entry().nonvolatileBits());
  for(Call c:List.of(wrongKind,wrongSite,wrongTarget))assertSame(returned,bound.invoke(c));
  assertSame(wrongKind,forwarded.get(0));assertSame(wrongSite,forwarded.get(1));assertSame(wrongTarget,forwarded.get(2));
  Tail tail=new Tail(101L,TargetKind.DIRECT_RVA,103L,w.entry());assertSame(tailReturned,bound.tail(tail));assertSame(tail,tails.get(0));assertEquals(Long.MIN_VALUE,bound.readGsQword58());
 }
 @Test void freshCorruptedReturnWordIsRejectedByConsumer() {corruptedFrameIsRejected(false);}
 @Test void freshCorruptedSavedRbxIsRejectedByConsumer() {corruptedFrameIsRejected(true);}
 private static void corruptedFrameIsRejected(boolean savedRbx) {
  Witness w=new GovernmentCrtCallee186WitnessBook().witnesses().get(0);Entry e=w.entry();
  Map<Long,Integer> bytes=new HashMap<>(w.memorySeed());var memory=new GovernmentCrtCallee186WitnessRunner.MemoryImpl(bytes);
  memory.writeQword(e.rspBits(),e.imageBaseBits()+0x4223F2DL);
  Calls fallback=new Calls(){
   @Override public VolatileBits invoke(Call c){if(savedRbx)memory.writeQword(e.rspBits()-8L,e.nonvolatileBits().rbxBits()^1L);else memory.writeQword(e.rspBits(),e.imageBaseBits()+0x4223F2EL);return w.events().get(0).normalPost();}
   @Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected tail");}
   @Override public long readGsQword58(){throw new AssertionError("unexpected GS");}
  };
  Calls bound=GovernmentCrtCallee186Calls.bind(e.imageBaseBits(),memory,fallback);
  Call outer=new Call(0x4223F28L,TargetKind.DIRECT_RVA,0x4223EE8L,e.rspBits()+8L,e.volatileBits(),e.nonvolatileBits());
  assertThrows(IllegalStateException.class,()->bound.invoke(outer));
 }
}
