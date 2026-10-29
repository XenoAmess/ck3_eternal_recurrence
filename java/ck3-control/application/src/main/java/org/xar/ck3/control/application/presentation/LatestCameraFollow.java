package org.xar.ck3.control.application.presentation;

import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.contracts.presentation.*;

/** One actual worker: one urgent slot plus the latest ordinary request, with bounded raw capture custody. */
public final class LatestCameraFollow implements AutoCloseable {
 @FunctionalInterface public interface Post { PresentationCapture capture(PresentationIntent intent); }
 public record Work(PresentationIntent intent,Post post){public Work{Objects.requireNonNull(intent);Objects.requireNonNull(post);}}
 private final Thread worker;private Work urgent,latest;private boolean running,closed,uncertain;
 private final ArrayDeque<PresentationCapture> completed=new ArrayDeque<>();private final ArrayDeque<String> failures=new ArrayDeque<>();
 public LatestCameraFollow(){worker=new Thread(this::loop,"ck3-auto-camera-presentation");worker.setDaemon(true);worker.start();}
 /** False leaves custody with the caller. Every admitted original reserves one of twelve terminal slots. */
 public synchronized boolean schedule(Work work,boolean priority){
  Objects.requireNonNull(work);int custody=completed.size()+(running?1:0)+(urgent==null?0:1)+(latest==null?0:1);
  if(closed||uncertain||custody>=12)return false;
  if(priority){if(urgent!=null)retain(unattempted(urgent,"urgent intent superseded before physical attempt"));if(latest!=null)retain(unattempted(latest,"latest intent superseded by urgent"));latest=null;urgent=work;}
  else{if(latest!=null)retain(unattempted(latest,"latest intent superseded before physical attempt"));latest=work;}
  notifyAll();return true;
 }
 private static PresentationCapture unattempted(Work w,String reason){return new PresentationCapture(w.intent(),Optional.empty(),PresentationCapture.Kind.NOT_ATTEMPTED,
  OriginalOutcome.Phase.BEFORE_ODD,reason,Instant.now(),new byte[0],Optional.empty());}
 private void loop(){
  for(;;){Work work;
   synchronized(this){try{while(!closed&&(urgent==null&&latest==null||completed.size()>=8||uncertain))wait();
     if(closed)return;
     if(urgent!=null){work=urgent;urgent=null;}else{wait(250);if(closed)return;if(urgent!=null){work=urgent;urgent=null;}else{work=latest;latest=null;}}
     if(work==null)continue;running=true;
    }catch(InterruptedException stop){if(closed)return;continue;}}
   PresentationCapture result;
   try{result=Objects.requireNonNull(work.post().capture(work.intent()));if(!java.util.Arrays.equals(result.intent().encode(),work.intent().encode()))throw new IllegalStateException("capture changed original intent");}
   catch(RuntimeException failure){synchronized(this){running=false;uncertain=true;failures.addLast("uncaptured physical outcome:"+failure.getClass().getName());while(failures.size()>16)failures.removeFirst();notifyAll();}continue;}
   synchronized(this){running=false;if(result.kind()==PresentationCapture.Kind.UNKNOWN)uncertain=true;retain(result);notifyAll();}
  }
 }
 private void retain(PresentationCapture capture){
  // At most one running + two queued + eight completed. The owner drains before admitting more intents.
  if(completed.size()>=12)throw new IllegalStateException("camera raw capture custody exhausted");completed.addLast(capture);
  if(capture.kind()!=PresentationCapture.Kind.POSTED){failures.addLast(capture.reason());while(failures.size()>16)failures.removeFirst();}
 }
 public synchronized List<PresentationCapture> drain(){var out=List.copyOf(completed);completed.clear();notifyAll();return out;}
 public synchronized List<String> failures(){return List.copyOf(failures);}
 public synchronized boolean unresolvedPhysical(){return uncertain;}
 public synchronized boolean running(){return running;}
 public synchronized int pending(){return (urgent==null?0:1)+(latest==null?0:1);}
 @Override public void close(){
  synchronized(this){if(closed)return;closed=true;if(urgent!=null)retain(unattempted(urgent,"original camera runtime closed before attempt"));
   if(latest!=null)retain(unattempted(latest,"original camera runtime closed before attempt"));urgent=null;latest=null;notifyAll();}
  worker.interrupt();try{worker.join(1000);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();}
 }
}
