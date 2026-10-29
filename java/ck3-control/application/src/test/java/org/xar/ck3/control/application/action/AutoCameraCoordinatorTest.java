package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.*;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.presentation.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.*;

/** Actual coordinator/once-consumption boundary on explicit RAM ports; no private Session or Native qualification. */
class AutoCameraCoordinatorTest {
 @Test void preworkReallyStartsInsideLongNativeActionAndUnknownBusinessIsNeverReplayed()throws Exception{
  var journal=new Journal();var pre=new AtomicInteger();var posts=new AtomicInteger();
  var started=new CountDownLatch(1);var finish=new CountDownLatch(1);
  try(var worker=new LatestCameraFollow()){
   var binding=binding((same,command,guard,history,queue)->{
    pre.incrementAndGet();assertEquals("resume-map",command.operation().value());
    assertTrue(history.stream().anyMatch(r->r.command().equals(command)&&r.state() instanceof ActionState.Submitting));
    worker.schedule(new LatestCameraFollow.Work(intent(),i->{
     posts.incrementAndGet();started.countDown();try{assertTrue(finish.await(2,TimeUnit.SECONDS));}catch(InterruptedException e){Thread.currentThread().interrupt();}
     return unattempted(i);
    }),true);
   });
   var coordinator=coordinator(journal,new PhysicalActionRegistry(List.of(binding)),(permit,request,deadline)->{
    permit.consumeOnce();try{assertTrue(started.await(2,TimeUnit.SECONDS),"worker must run while business call is still in progress");}
    catch(InterruptedException e){Thread.currentThread().interrupt();fail(e);}
    assertEquals(1,posts.get());assertEquals(1,pre.get());finish.countDown();
    return new NativeActionPort.Unknown(permit.requestId(),"actual software wire outcome unknown",new byte[0],Optional.empty());
   });
   var command=DecisionDisplayTest.command("long-original","resume-map");var first=coordinator.execute(command);
   assertEquals(ActionReceipt.Outcome.UNRESOLVED,first.outcome());var attempt=ActionTransitions.attempt(first.state()).orElseThrow();
   assertEquals(RequestIds.forCommand(command),attempt.requestId());assertSame(first,coordinator.execute(command));
   assertEquals(1,posts.get());assertEquals(1,pre.get());
   assertThrows(IllegalArgumentException.class,()->coordinator.execute(DecisionDisplayTest.command("another-business","pause-map")));
   assertEquals(1,posts.get());assertEquals(attempt,ActionTransitions.attempt(journal.rows.get(command.actionId()).state()).orElseThrow());
  }finally{finish.countDown();}
 }
 @Test void nativeRejectionBeforePermitConsumptionNeverSchedulesPrework(){
  var journal=new Journal();var pre=new AtomicInteger();
  var coordinator=coordinator(journal,new PhysicalActionRegistry(List.of(binding((same,command,guard,history,queue)->pre.incrementAndGet()))),
   (permit,request,deadline)->new NativeActionPort.RejectedBeforeDispatch(permit.requestId(),
    new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,0,"actual software native guard rejected before write",Optional.empty())));
  var receipt=coordinator.execute(DecisionDisplayTest.command("native-guard-fails","resume-map"));
  assertEquals(ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH,receipt.outcome());assertEquals(0,pre.get());
 }
 @Test void optionalObserverFailureDoesNotReplaceOrRetryOriginalNativeUnknown(){
  var journal=new Journal();var calls=new AtomicInteger();
  var coordinator=coordinator(journal,new PhysicalActionRegistry(List.of(binding((same,command,guard,history,queue)->{throw new java.io.IOException("camera unavailable");}))),
   (permit,request,deadline)->{permit.consumeOnce();calls.incrementAndGet();return new NativeActionPort.Unknown(permit.requestId(),"original wire unknown",new byte[0],Optional.empty());});
  var command=DecisionDisplayTest.command("optional-failure","resume-map");var first=coordinator.execute(command);
  assertEquals(1,calls.get());assertEquals(ActionReceipt.Outcome.UNRESOLVED,first.outcome());assertSame(first,coordinator.execute(command));assertEquals(1,calls.get());
 }
 @Test void immutableDataAndChangedIdentityCannotRegrantOriginalPhysicalPermit()throws Exception{
  var original=intent();var checks=new AtomicInteger();
  java.util.function.Function<PresentationIntent,PresentationIntent.Prepared> prepared=i->{
   byte[] h=java.nio.ByteBuffer.allocate(24).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(PresentationRequest.MAGIC).putInt(1)
    .putInt((int)i.owner().processId()).putInt(0).putInt(0).putInt(0).array();
   return new PresentationIntent.Prepared(i,i.createdAt().plusMillis(1),0,2,0,"10000","4096",Optional.empty(),h);
  };
  var permit=new PresentationPermit(original,()->checks.incrementAndGet());
  permit.consume(prepared.apply(original),original.deadline());assertEquals(1,checks.get());
  var replay=PresentationIntent.fromJson(original.toJson());
  assertThrows(java.io.IOException.class,()->permit.consume(prepared.apply(replay),replay.deadline()));assertEquals(1,checks.get());
  assertEquals(0,PresentationPermit.class.getConstructors().length);
  assertFalse(java.io.Serializable.class.isAssignableFrom(PresentationPermit.class));
  var o=original.owner();var f=original.frame();
  var owners=List.of(new PresentationRequest.Owner(o.machineId(),o.sessionId(),o.processId(),"2",o.executableSha256(),o.episodeRunId(),o.connectionGeneration()),
   new PresentationRequest.Owner(o.machineId(),o.sessionId(),o.processId(),o.processBirthFiletime(),o.executableSha256(),"next-episode",o.connectionGeneration()));
  var changed=new ArrayList<PresentationIntent>();
  for(var owner:owners)changed.add(new PresentationIntent(original.requestId(),original.createdAt(),owner,f,original.mode(),original.titleKey(),original.tracking(),original.deadline()));
  for(var frame:List.of(new PresentationRequest.Frame(f.snapshotId(),"2",f.nativeRevision(),f.actor(),f.dateRaw()),
   new PresentationRequest.Frame(f.snapshotId(),f.revision(),"2",f.actor(),f.dateRaw())))
   changed.add(new PresentationIntent(original.requestId(),original.createdAt(),o,frame,original.mode(),original.titleKey(),original.tracking(),original.deadline()));
  for(var foreign:changed){
   var once=new PresentationPermit(original,()->checks.incrementAndGet());
   assertThrows(java.io.IOException.class,()->once.consume(prepared.apply(foreign),original.deadline()));
   assertThrows(java.io.IOException.class,()->once.consume(prepared.apply(original),original.deadline()));
  }
  assertEquals(1,checks.get());
 }
 @FunctionalInterface interface Before{void apply(ContinuityStorePort.Session same,ActionCommand command,GuardEvidence guard,List<ActionReceipt> history,PhysicalActionRegistry.Queue queue)throws java.io.IOException;}
 static PhysicalActionRegistry.Binding binding(Before before){
  return new PhysicalActionRegistry.Binding(new OperationKey("test-camera"),TransportKind.PRESENTATION_MMAP,
   List.of(DecisionDisplayTest.command("source","pause-map").source().sourceRef()),new PhysicalActionRegistry.Producer(){
    @Override public void beforeNative(ContinuityStorePort.Session same,ActionCommand c,GuardEvidence g,List<ActionReceipt> history,PhysicalActionRegistry.Queue queue)throws java.io.IOException{before.apply(same,c,g,history,queue);}
    @Override public GuardEvidence guard(WriterContracts.Head head,ActionCommand c){throw new AssertionError("no physical request in this software boundary test");}
    @Override public PreparedAction prepare(ContinuityStorePort.Session same,ActionCommand c,String id){throw new AssertionError();}
    @Override public PhysicalOutcome post(PhysicalSubmission p,PreparedAction r,java.time.Instant d){throw new AssertionError();}
    @Override public PhysicalActionRegistry.Observation observe(ContinuityStorePort.Session same,ActionCommand c,PhysicalActionState s,java.time.Instant d){throw new AssertionError();}
    @Override public void verifyArchived(WriterContracts.Head h,ActionReceipt r,ActionPorts.OutcomeArchive a){throw new AssertionError();}
   });
 }
 static ActionCoordinator coordinator(Journal journal,PhysicalActionRegistry registry,NativeActionPort nativePort){
  ActionPorts.PreparationPort preparation=new ActionPorts.PreparationPort(){
   @Override public void requireOutsideReadOnlyScope(ContinuityStorePort.Session same,ActionCommand c){}
   @Override public NativeRequest prepare(ActionCommand c){return new NativeRequest(c.operation().value(),"game.command."+c.operation().value(),new RawJson(new byte[]{'{','}'}));}
   @Override public NativeRequest prepare(ContinuityStorePort.Session same,ActionCommand c,String id){return prepare(c);}
  };
  var result=new ActionCoordinator("display-test-authority",journal,(head,c)->new GuardEvidence(c.before(),c.source(),c.sessionId(),BigInteger.ONE,
   c.operation(),c.source().sourceRef(),c.source().sourceRef(),"display-test-authority",DecisionDisplayTest.NOW,c.deadline()),preparation,nativePort,
   (c,a,d)->new ActionPorts.Pending("independent software state unavailable",List.of()),Clock.fixed(DecisionDisplayTest.NOW,ZoneOffset.UTC));
  result.bindPhysicalActions(registry);return result;
 }
 static PresentationIntent intent(){
  var now=java.time.Instant.now();return new PresentationIntent("software-io",now,new PresentationRequest.Owner("camera-software","session",42,"1",PresentationRequest.EXECUTABLE_SHA256,"episode","1"),
   new PresentationRequest.Frame("snapshot","1","1",73,1000),PresentationRequest.Mode.HOTSPOT,"b_test",Optional.empty(),now.plusSeconds(10));
 }
 static PresentationCapture unattempted(PresentationIntent i){return new PresentationCapture(i,Optional.empty(),PresentationCapture.Kind.NOT_ATTEMPTED,OriginalOutcome.Phase.BEFORE_ODD,"software IO did not post",java.time.Instant.now(),new byte[0],Optional.empty());}
 static final class Journal implements ActionJournal{
  final LinkedHashMap<String,ActionReceipt> rows=new LinkedHashMap<>();long sequence;
  final WriterContracts.Head head=new WriterContracts.Head(ContinuityState.fromJson(StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id","display-software-vector")
   .put("sequence",0).put("window_id",1).put("status","running").put("start_date_raw",24000).put("target_date_raw",286992).put("target_days",10958)
   .put("last_settled_cycles",0).put("last_settled_date_raw",24000).put("binding_lineage_count",0),"display-software-vector"),List.of(),List.of(),List.of(),false);
  @Override public <T>T locked(Function<LockedJournal,T> work){return work.apply(new LockedJournal(){
   @Override public ContinuityStorePort.Session writerSession(){return null;}
   @Override public WriterContracts.Head head(){return head;}
   @Override public Optional<ActionReceipt> find(String id){return Optional.ofNullable(rows.get(id));}
   @Override public List<ActionReceipt> unresolved(){return rows.values().stream().filter(r->!r.settled()).toList();}
   @Override public Snapshot snapshot(){return new Snapshot(sequence,head.digest(),List.copyOf(rows.values()),new MissingHistoryBasis());}
   @Override public ActionReceipt append(ActionCommand c,String digest,ActionState s){ActionTransitions.validate(find(c.actionId()),c,digest,s);var r=new ActionReceipt(1,++sequence,c,digest,s);rows.put(c.actionId(),r);return r;}
  });}
 }
}
