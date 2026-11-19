package org.xar.ck3.control.continuity.writer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts;
import static org.junit.jupiter.api.Assertions.*;
class SavedReadsetComponentBudgetTest {
 @Test void independentComponentsRetainFourHandlesPerCasAndOnePerExternal()throws Exception{
  var b=ImmutableArtifactStore.SavedReadsetBudget.componentBounded(2,3,1024);
  b.reserveCas(10);b.reserveCas(20);b.reserveExternal(1);b.reserveExternal(2);b.reserveExternal(0);
  assertEquals(ImmutableArtifactStore.SavedReadsetFailure.ENTRY_BOUND,assertThrows(ImmutableArtifactStore.SavedReadsetUnavailable.class,()->b.reserveCas(1)).reason());
  assertEquals(ImmutableArtifactStore.SavedReadsetFailure.ENTRY_BOUND,assertThrows(ImmutableArtifactStore.SavedReadsetUnavailable.class,()->b.reserveExternal(1)).reason());
 }
 @Test void originalSharedLimitConstructorKeepsTheActualHandleRefusal()throws Exception{
  var b=new ImmutableArtifactStore.SavedReadsetBudget(3,100,7);b.reserveCas(10);b.reserveExternal(1);
  assertEquals(ImmutableArtifactStore.SavedReadsetFailure.HANDLE_BOUND,assertThrows(ImmutableArtifactStore.SavedReadsetUnavailable.class,()->b.reserveExternal(1)).reason());
 }
 @Test void rejectedPayloadDoesNotConsumeAPhantomComponent()throws Exception{
  var b=ImmutableArtifactStore.SavedReadsetBudget.componentBounded(2,2,32);
  assertEquals(ImmutableArtifactStore.SavedReadsetFailure.BYTE_BOUND,assertThrows(ImmutableArtifactStore.SavedReadsetUnavailable.class,()->b.reserveCas(33)).reason());
  b.reserveCas(16);b.reserveCas(16);
  assertEquals(ImmutableArtifactStore.SavedReadsetFailure.BYTE_BOUND,assertThrows(ImmutableArtifactStore.SavedReadsetUnavailable.class,()->b.reserveExternal(1)).reason());b.reserveExternal(0);
 }
 @Test void explicitResourceProfileNeverWidensTheOrdinaryHistoricalGate(){
  var h=new ActionPorts.HistoricalReadLimits(8192,256L*1024*1024,16384);
  var p=new NativeOutcomeArchive.SavedDataReadsetLimits(h,16384,8192,256L*1024*1024);
  assertSame(h,p.historical());assertEquals(73730,p.maximumAggregateHandles());
  assertThrows(IllegalArgumentException.class,()->new ActionPorts.HistoricalReadLimits(8192,256L*1024*1024,16385));
  assertThrows(IllegalArgumentException.class,()->new NativeOutcomeArchive.SavedDataReadsetLimits(h,16385,8192,1));
  assertThrows(IllegalArgumentException.class,()->new NativeOutcomeArchive.SavedDataReadsetLimits(h,1,0,1));
  assertThrows(IllegalArgumentException.class,()->new NativeOutcomeArchive.SavedDataReadsetLimits(h,1,1,256L*1024*1024+1));
 }
}
