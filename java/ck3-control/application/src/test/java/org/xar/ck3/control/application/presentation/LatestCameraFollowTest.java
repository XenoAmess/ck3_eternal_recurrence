package org.xar.ck3.control.application.presentation;
import static org.junit.jupiter.api.Assertions.*;
import java.nio.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.LockSupport;
import java.util.function.BooleanSupplier;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.presentation.*;
import static org.xar.ck3.control.contracts.presentation.PresentationCapture.Kind.*;
import static org.xar.ck3.control.contracts.presentation.OriginalOutcome.Phase.*;
class LatestCameraFollowTest {
static final Instant AT=Instant.parse("2026-10-27T01:00:00Z");
static PresentationIntent intent(String id){
 var owner=new PresentationRequest.Owner("test-machine","camera",44,"18446744073709551614",
  PresentationRequest.EXECUTABLE_SHA256,"episode","18446744073709551613");
 return new PresentationIntent(id,AT,owner,new PresentationRequest.Frame("snapshot","9","10",42,53138160),
  PresentationRequest.Mode.REALM,"",Optional.empty(),AT.plusSeconds(30));
}
static PresentationCapture capture(PresentationIntent i,PresentationCapture.Kind kind){
 byte[] h=ByteBuffer.allocate(24).order(ByteOrder.LITTLE_ENDIAN).putInt(PresentationRequest.MAGIC)
  .putInt(1).putInt(44).putInt(0).putInt(0).putInt(0).array();
 var p=new PresentationIntent.Prepared(i,AT.plusMillis(1),0,2,0,"9007199254740993","18446744073709551615",Optional.empty(),h);
 return new PresentationCapture(i,Optional.of(p),kind,kind==UNKNOWN?
  EVEN_PUBLICATION_UNCERTAIN:BEFORE_ODD,
  "synthetic IO",AT.plusMillis(2),new byte[0],Optional.empty());
}
static void await(CountDownLatch l)throws InterruptedException{assertTrue(l.await(3,TimeUnit.SECONDS),"worker never started");}
static void eventually(BooleanSupplier condition){
 for(int n=0;n<3000&&!condition.getAsBoolean();n++)LockSupport.parkNanos(1_000_000);assertTrue(condition.getAsBoolean());
}
static LatestCameraFollow.Work plain(String id,AtomicInteger calls){
 return new LatestCameraFollow.Work(intent(id),i->{calls.incrementAndGet();return capture(i,NOT_POSTED);});
}
static LatestCameraFollow.Work block(String id,CountDownLatch started,CountDownLatch release,List<String> calls,AtomicInteger active,AtomicInteger max){
 var original=intent(id);
 return new LatestCameraFollow.Work(original,i->{
  assertSame(original,i);calls.add(id);max.accumulateAndGet(active.incrementAndGet(),Math::max);started.countDown();
  try{release.await();}catch(InterruptedException closing){Thread.currentThread().interrupt();}finally{active.decrementAndGet();}
  return capture(i,NOT_POSTED);
 });
}
static void displaced(PresentationCapture c,String id){
 assertEquals(id,c.intent().requestId());assertEquals(NOT_ATTEMPTED,c.kind());
 assertTrue(c.prepared().isEmpty());assertEquals(BEFORE_ODD,c.phase());
 assertEquals(0,c.afterHeader().length);assertArrayEquals(c.encode(),PresentationCapture.decode(c.encode()).encode());
 assertEquals("18446744073709551614",c.intent().owner().processBirthFiletime());
}
@Test void queueOrderAndReplacementCustody()throws Exception{
 var calls=Collections.synchronizedList(new ArrayList<String>());var active=new AtomicInteger();var max=new AtomicInteger();
 var a=new CountDownLatch(1);var ar=new CountDownLatch(1);var u=new CountDownLatch(1);var ur=new CountDownLatch(1);
 var l=new CountDownLatch(1);var lr=new CountDownLatch(1);var worker=new LatestCameraFollow();
 try{
  assertTrue(worker.schedule(block("running",a,ar,calls,active,max),true));await(a);assertTrue(worker.running());
  assertTrue(worker.schedule(block("old-urgent",u,ur,calls,active,max),true));
  assertTrue(worker.schedule(block("old-latest",l,lr,calls,active,max),false));
  assertTrue(worker.schedule(block("urgent",u,ur,calls,active,max),true));
  assertTrue(worker.schedule(block("latest",l,lr,calls,active,max),false));
  assertEquals(2,worker.pending());assertEquals(List.of("running"),calls);
  var replaced=worker.drain();assertEquals(2,replaced.size());
  displaced(replaced.get(0),"old-urgent");displaced(replaced.get(1),"old-latest");
  ar.countDown();await(u);assertEquals(List.of("running","urgent"),calls);assertEquals(1,l.getCount());
  ur.countDown();await(l);assertEquals(List.of("running","urgent","latest"),calls);
  lr.countDown();eventually(()->!worker.running()&&worker.pending()==0);assertEquals(1,max.get());
  var done=worker.drain();assertEquals(List.of("running","urgent","latest"),done.stream().map(c->c.intent().requestId()).toList());
  done.forEach(c->assertEquals(NOT_POSTED,c.kind()));
 }finally{ar.countDown();ur.countDown();lr.countDown();worker.close();}
}
@Test void unknownKeepsRejectedCustody()throws Exception{
 var calls=new AtomicInteger();var a=new CountDownLatch(1);var release=new CountDownLatch(1);var worker=new LatestCameraFollow();
 try{
  assertTrue(worker.schedule(new LatestCameraFollow.Work(intent("unknown"),i->{
   calls.incrementAndGet();a.countDown();try{release.await();}catch(InterruptedException closing){Thread.currentThread().interrupt();}
   return capture(i,UNKNOWN);
  }),true));await(a);
  assertTrue(worker.schedule(plain("queued-urgent",calls),true));assertTrue(worker.schedule(plain("queued-latest",calls),false));
  release.countDown();eventually(()->worker.unresolvedPhysical()&&!worker.running());
  var original=worker.drain();assertEquals(1,original.size());assertEquals(UNKNOWN,original.getFirst().kind());
  assertArrayEquals(original.getFirst().encode(),PresentationCapture.decode(original.getFirst().encode()).encode());
  for(int n=0;n<24;n++){
   var rejected=plain("rejected-"+n,calls);
   assertFalse(worker.schedule(rejected,n%2==0));assertTrue(worker.drain().isEmpty(),"caller custody");
  }
  assertEquals(1,calls.get());assertEquals(2,worker.pending());assertTrue(worker.failures().size()<=16);
  assertThrows(UnsupportedOperationException.class,()->worker.failures().add("mutation"));
  assertTimeoutPreemptively(Duration.ofSeconds(2),worker::close);
  var queued=worker.drain();assertEquals(2,queued.size());
  displaced(queued.get(0),"queued-urgent");displaced(queued.get(1),"queued-latest");assertEquals(1,calls.get());
 }finally{release.countDown();worker.close();}
}
@Test void saturationKeepsOriginals()throws Exception{
 var calls=Collections.synchronizedList(new ArrayList<String>());var a=new CountDownLatch(1);var release=new CountDownLatch(1);
 var worker=new LatestCameraFollow();var admitted=new LinkedHashSet<String>();var unused=new AtomicInteger();
 try{
  assertTrue(worker.schedule(block("running",a,release,calls,new AtomicInteger(),new AtomicInteger()),true));admitted.add("running");await(a);
  assertTrue(worker.schedule(plain("urgent",unused),true));admitted.add("urgent");
  for(int n=0;n<24;n++){
   String id="latest-"+n;boolean accepted=assertDoesNotThrow(()->worker.schedule(plain(id,unused),false));
   if(accepted)admitted.add(id);assertEquals(2,worker.pending());
  }
  assertTimeoutPreemptively(Duration.ofSeconds(2),worker::close);
  var originals=worker.drain();assertTrue(originals.size()<=12);assertEquals(admitted.size(),originals.size());
  assertEquals(admitted,new LinkedHashSet<>(originals.stream().map(c->c.intent().requestId()).toList()));
  assertEquals(0,worker.pending());assertFalse(worker.running());assertEquals(0,unused.get());
  for(var c:originals)if(!c.intent().requestId().equals("running"))displaced(c,c.intent().requestId());
 }finally{release.countDown();worker.close();}
}
@Test void foreignOrThrownStops(){
 for(boolean foreign:List.of(false,true)){
  var calls=new AtomicInteger();var worker=new LatestCameraFollow();
  try{
   assertTrue(worker.schedule(new LatestCameraFollow.Work(intent("original"),i->{
    calls.incrementAndGet();if(foreign)return capture(intent("foreign"),NOT_POSTED);
    throw new IllegalStateException("uncaptured IO");
   }),true));
   eventually(worker::unresolvedPhysical);assertEquals(1,calls.get());assertTrue(worker.drain().isEmpty());
   assertFalse(worker.failures().isEmpty());assertTrue(worker.failures().size()<=16);
   assertFalse(worker.schedule(plain("retry",calls),true));assertEquals(1,calls.get());
  }finally{worker.close();}
 }
}
 @Test void blockerQueuedOldOrdinaryNewerUrgent()throws Exception{
  var calls=Collections.synchronizedList(new ArrayList<String>());var active=new AtomicInteger();var max=new AtomicInteger();
  var a=new CountDownLatch(1);var ar=new CountDownLatch(1);var u=new CountDownLatch(1);var ur=new CountDownLatch(1);
  var l=new CountDownLatch(1);var lr=new CountDownLatch(1);var worker=new LatestCameraFollow();
  try{
   assertTrue(worker.schedule(block("blocker",a,ar,calls,active,max),true));await(a);assertTrue(worker.running());
   assertTrue(worker.schedule(block("old-ordinary",l,lr,calls,active,max),false));
   assertTrue(worker.schedule(block("newer-urgent",u,ur,calls,active,max),true));
   assertEquals(1,worker.pending());assertEquals(List.of("blocker"),calls);
   var replaced=worker.drain();assertEquals(1,replaced.size());
   displaced(replaced.get(0),"old-ordinary");
   ar.countDown();await(u);assertEquals(List.of("blocker","newer-urgent"),calls);assertEquals(1,l.getCount());
   ur.countDown();eventually(()->!worker.running()&&worker.pending()==0);assertEquals(1,max.get());
   var done=worker.drain();assertEquals(List.of("blocker","newer-urgent"),done.stream().map(c->c.intent().requestId()).toList());
   done.forEach(c->assertEquals(NOT_POSTED,c.kind()));
  }finally{ar.countDown();ur.countDown();lr.countDown();worker.close();}
 }
}
