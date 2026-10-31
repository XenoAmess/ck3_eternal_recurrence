package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public final class AddressFree83ConsumerTest {
 private static final long BASE=0x100000000L, BLOCK=0x200000001L, HEAP=0x300000001L, DEST=0x400000001L;
 private static Lower61Fixture fixture(int result) {
  var f=new Lower61Fixture(); f.qwords.put(BASE+0x5C5DE30L,HEAP); f.firstEax=result;
  f.destination=DEST; f.dwords.put(DEST,17); return f;
 }
 @Test void nullBlockPerformsNoReadOrCall() {
  assertDoesNotThrow(()->AddressFree83Consumer.execute(new Lower61Inputs.CallInput(BASE,0L),null,null));
 }
 @Test void firstNonzeroResultUsesRealHeapAndBlockWithoutFailureAccess() {
  var f=fixture(Integer.MIN_VALUE);
  AddressFree83Consumer.execute(new Lower61Inputs.CallInput(BASE,BLOCK),f,f);
  assertEquals(List.of(new Lower61Fixture.Read64(BASE+0x5C5DE30L,HEAP),new Lower61Fixture.First(new Lower61Inputs.FirstCall(HEAP,0L,BLOCK))),f.events);
  assertEquals(17,f.dwords.get(DEST)); assertTrue(f.writes32.isEmpty());
 }
 @Test void failedReleaseWritesActualAddressAfterUnsignedMapperWithoutDestinationRead() {
  var f=fixture(0); f.errorEax=-1; f.mappedEax=0x80000001;
  AddressFree83Consumer.execute(new Lower61Inputs.CallInput(BASE,BLOCK),f,f);
  assertEquals(List.of(new Lower61Fixture.Read64(BASE+0x5C5DE30L,HEAP),new Lower61Fixture.First(new Lower61Inputs.FirstCall(HEAP,0L,BLOCK)),Lower61Fixture.Opaque.POINTER,Lower61Fixture.Opaque.ERROR,new Lower61Fixture.MapEax(0xFFFFFFFFL),new Lower61Fixture.Write32(DEST,0x80000001)),f.events);
  assertEquals(0x80000001,f.dwords.get(DEST)); assertEquals(1,f.writes32.size());
 }
 @Test void mapperExceptionPropagatesWithoutWriteback() {
  var sentinel=new IllegalStateException("controlled mapper stop");
  var f=new Lower61Fixture(){@Override public int call423B0D4(long rcx){super.call423B0D4(rcx);throw sentinel;}};
  f.qwords.put(BASE+0x5C5DE30L,HEAP); f.firstEax=0; f.destination=DEST; f.errorEax=-1; f.dwords.put(DEST,17);
  assertSame(sentinel,assertThrows(IllegalStateException.class,()->AddressFree83Consumer.execute(new Lower61Inputs.CallInput(BASE,BLOCK),f,f)));
  assertEquals(List.of(new Lower61Fixture.Read64(BASE+0x5C5DE30L,HEAP),new Lower61Fixture.First(new Lower61Inputs.FirstCall(HEAP,0L,BLOCK)),Lower61Fixture.Opaque.POINTER,Lower61Fixture.Opaque.ERROR,new Lower61Fixture.MapEax(0xFFFFFFFFL)),f.events);
  assertEquals(17,f.dwords.get(DEST)); assertTrue(f.writes32.isEmpty());
 }
}
