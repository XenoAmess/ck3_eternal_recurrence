package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.presentation.*;
import org.xar.ck3.control.application.presentation.AutoCameraModel.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.presentation.*;
import org.xar.ck3.control.nativebridge.capabilities.gui.LandedProvinceIndex;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Actual ordinary AUTO audience, owned by the installed GUI product. No Session enters its worker. */
public final class RootAutoCamera implements AutoCloseable {
 private final RootRuntimeContext context;private final RootGuiPresentation gui;
 private final AutoCameraPolicy policy=new AutoCameraPolicy();private final LatestCameraFollow worker=new LatestCameraFollow();
 private final AtomicReference<PresentationRequest.Owner> currentOwner=new AtomicReference<>();
 private final Map<String,Pending> pending=new LinkedHashMap<>();private final Map<String,PresentationCapture> outbox=new LinkedHashMap<>();
 private Map<Integer,String> land=Map.of();private LandedProvinceIndex index;private boolean indexTried,active,preUsed,closed;
 private GuardEvidence lastGuard;private ActionCommand lastCommand;private String lastAutomatic;private String diagnostic="not_observed";
 private Optional<RawJson> latestActual=Optional.empty(),lastReceipt=Optional.empty();private DriverSnapshotFacts.Known cachedKnown;
 private record Pending(ActionCommand command,GuardEvidence guard,Frame frame,Decision decision,boolean urgent){}
 RootAutoCamera(RootRuntimeContext context,RootGuiPresentation gui){this.context=context;this.gui=gui;}
 public void begin(){
  cachedKnown=null;
  require(!closed&&!active,"one actual AUTO camera scope");active=true;preUsed=false;
  if(!indexTried){indexTried=true;try{
   Path exe=Path.of(context.game().launchPlan().sources().review().gameExecutable().path());
   require(exe.getFileName().toString().equalsIgnoreCase("ck3.exe")&&exe.getParent().getFileName().toString().equalsIgnoreCase("binaries"),"actual installed executable root required");
   index=LandedProvinceIndex.fromGameDirectory(exe.getParent().getParent());Map<Integer,String> mapped=new LinkedHashMap<>();
   index.provinces().forEach(p->mapped.put(p.province(),p.barony()));land=Map.copyOf(mapped);
  }catch(IOException|RuntimeException unavailable){diagnostic="landed_index_unavailable:"+unavailable.getClass().getSimpleName();}}
 }
 public void end(){active=false;}
 public boolean active(){return active&&!closed;}
 static PresentationIntent intent(ActionCommand command){return RootGuiPresentation.automaticIntent(command);}
 void verifyOwner(ActionCommand command)throws IOException{
  var expected=intent(command).owner();if(closed||!expected.equals(currentOwner.get()))throw new IOException("automatic original owner changed before physical attempt");
 }
 void beforeNative(Session same,ActionCommand command,GuardEvidence guard,List<ActionReceipt> history,PhysicalActionRegistry.Queue queue)throws IOException{
  if(!active()||!(command.origin() instanceof CommandOrigin.Gameplay))return;
  context.writer().requireSession(same);lastGuard=guard;lastCommand=command;
  if(preUsed||!command.operation().value().equals("resume-map")||index==null)return;
  preUsed=true;var archive=context.archive().withSession(same);
  var actual=RootGuardEvidence.loadFrame(guard,archive,context.frameLoader());var frame=AutoCameraModel.copy(actual,gui.ownerFor(actual));
  currentOwner.set(frame.owner());
  var parent=history.stream().filter(r->ActionTransitions.composite(r.state()).filter(c->c.children().stream().anyMatch(child->
    child.actionId().equals(command.actionId())&&child.bodySha256().equals(ActionCodec.bodySha256(command)))).isPresent()).reduce((a,b)->b);
  if(parent.isEmpty()||!frame.paused()||!frame.alive()||!frame.mapReady()||frame.mandatory())return;
  var plan=parent.orElseThrow().command().before().frame();
  require(frame.source().dateRaw()==plan.identity().dateRaw().intValueExact()&&frame.source().actor()==plan.identity().player().intValueExact()
    &&frame.owner().episodeRunId().equals(plan.episodeRunId())&&new BigInteger(frame.source().revision()).compareTo(plan.revision())>=0
    &&new BigInteger(frame.source().nativeRevision()).compareTo(plan.identity().nativeRevision())>=0,"pre-resume frame crossed ordinary planning");
  index.verifySourcesUnchanged();Optional<PresentationIntent.Scope> scope=AutoCameraPolicy.tracking(frame,history,parent.orElseThrow(),land);
  var hotspot=AutoCameraModel.hotspot(frame,land);
  if(scope.isEmpty()&&(hotspot.isEmpty()||!Set.of("battle","moving_player_army","army_destination").contains(hotspot.orElseThrow().reason())))return;
  Decision decision=scope.isPresent()?new Decision(PresentationRequest.Mode.TRACKED_HOTSPOT,"","validated_armed_tactical_scope",scope):
    new Decision(PresentationRequest.Mode.HOTSPOT,hotspot.orElseThrow().title(),hotspot.orElseThrow().reason(),Optional.empty());
  enqueue(same,actual,frame,guard,decision,true,queue);
 }
 void afterTurn(Session same,DriverSnapshotFacts.Known known,Instant deadline){
  if(!active()||index==null||lastGuard==null||lastCommand==null)return;
  try{
   context.writer().requireSession(same);cachedKnown=known;var registry=context.core().physicalActions();registry.collectAutomatic(same);
   if(lastAutomatic!=null){var old=registry.observeAutomatic(same,lastAutomatic);gui.rememberAutomatic(old);}
   if(worker.unresolvedPhysical()){diagnostic="physical_UNKNOWN_no_camera_repost";return;}
   var observation=known.observation();if(observation.isEmpty()){diagnostic="current_cached_semantic_facts_unavailable";return;}
   var actual=context.transport().currentSnapshot(deadline); // Exactly one retained cache read; no Native query.
   var facts=observation.orElseThrow();var archive=context.archive().withSession(same);var original=archive.preserveNativeFrame(actual);
   var joined=new DriverObservationAssembler().assemble(actual,facts,original);if(!(joined instanceof DriverObservationAssembler.Complete complete)){diagnostic="current_cache_identity_or_revision_unavailable";return;}
   var frame=AutoCameraModel.copy(complete,gui.ownerFor(complete));currentOwner.set(frame.owner());
   if(!frame.paused()||!frame.alive()){diagnostic="current_cache_not_living_paused";return;}
   index.verifySourcesUnchanged();var decision=policy.observe(frame,land,context.clock().instant(),Optional.empty());
   if(decision.isPresent())enqueue(same,complete,frame,lastGuard,decision.orElseThrow(),false,cmd->registry.deferAutomatic(same,cmd));
   diagnostic="current_frame_observed";
  }catch(IOException|RuntimeException unavailable){diagnostic="camera_unavailable:"+unavailable.getClass().getSimpleName();}finally{cachedKnown=null;}
 }
 private void enqueue(Session same,DriverObservationAssembler.Complete actual,Frame frame,GuardEvidence basis,Decision decision,boolean urgent,PhysicalActionRegistry.Queue queue)throws IOException{
  if(worker.unresolvedPhysical()||pending.size()>=8){diagnostic="bounded_camera_pending";return;}
  Instant now=context.clock().instant(),deadline=now.plusSeconds(10);require(!actual.observedAt().isAfter(now)&&actual.observedAt().plusSeconds(10).isAfter(now),"current presentation frame expired");
  var archive=context.archive().withSession(same);var guard=gui.automaticGuard(same,actual,basis,deadline,cachedKnown);
  var parent= context.core().actions().withFrozen(same,lease->{var r=lease.snapshot().actions().stream().filter(a->a.command().actionId().equals(lastCommand.actionId())).findFirst().orElseThrow();lease.assertCurrent();return r;});
  ExactRef parentRef=archive.receiptReferenceOf(parent);
  String id="auto-camera-"+UUID.randomUUID().toString().replace("-","");
  var template=new PresentationIntent(id,now,frame.owner(),frame.source(),decision.mode(),decision.title(),decision.tracking(),deadline);
  var args=StrictJson.object();args.set("automatic_intent",template.toJson());args.set("automatic_guard",ActionReceiptCodec.encodeGuard(guard));args.set("parent_receipt",parentRef.toJson());
  var command=gui.automaticCommand(actual,id,args,deadline);
  pending.put(id,new Pending(command,guard,frame,decision,urgent));try{queue.enqueue(command);}
  catch(RuntimeException failure){pending.remove(id);throw failure;}
  diagnostic=urgent?"validated_pre_resume_queued":"current_frame_queued";
 }
 void queued(Session same,ActionCommand command,GuardEvidence guard,PresentationPermit permit)throws IOException{
  context.writer().requireSession(same);var actual=pending.get(command.actionId());require(actual!=null&&actual.command().equals(command)&&actual.guard().equals(guard),"automatic queue has no identical original owner");
  var intent=intent(command);var io=gui.transportFor(intent.owner());boolean urgent=actual.urgent();
  if(worker.schedule(new LatestCameraFollow.Work(intent,request->io.capture(permit,request)),urgent))policy.queued(actual.frame(),actual.decision());
  else outbox.put(intent.requestId(),new PresentationCapture(intent,Optional.empty(),PresentationCapture.Kind.NOT_ATTEMPTED,OriginalOutcome.Phase.BEFORE_ODD,"not admitted by bounded worker",Instant.now(),new byte[0],Optional.empty()));
 }
 List<PhysicalActionRegistry.DeferredResult> collect(Session same)throws IOException{
  context.writer().requireSession(same);for(var raw:worker.drain())outbox.put(raw.intent().requestId(),raw);
  List<PhysicalActionRegistry.DeferredResult> results=new ArrayList<>();
  for(var entry:pending.values()){var raw=outbox.get(intent(entry.command()).requestId());if(raw!=null){var result=gui.archiveAutomatic(same,entry.command(),entry.guard(),raw);results.add(result);
    if(raw.kind()==PresentationCapture.Kind.NOT_POSTED||raw.kind()==PresentationCapture.Kind.UNKNOWN)policy.failed(entry.frame(),entry.decision());}}
  return List.copyOf(results);
 }
 void committed(String id){var p=pending.remove(id);if(p!=null){var raw=outbox.remove(intent(p.command()).requestId());if(raw!=null&&raw.kind()==PresentationCapture.Kind.POSTED)lastAutomatic=id;}}
 boolean issued(ActionCommand command){var p=pending.get(command.actionId());return p!=null&&p.command().equals(command);}
 boolean liveCustody(Session same,ActionCommand command)throws IOException{
  context.writer().requireSession(same);
  if(closed||worker.unresolvedPhysical())return false;
  var p=pending.get(command.actionId());if(p==null||!p.command().equals(command))return false;
  var intent=intent(command);return intent.owner().equals(currentOwner.get());
 }
 void receipt(RawJson raw){lastReceipt=Optional.of(raw);}
 void actual(RawJson raw){latestActual=Optional.of(raw);}
 void failed(ActionCommand command,int date)throws IOException{
  var i=intent(command);var f=RootGuardEvidence.loadFrame(RootGuiPresentation.guard(command),context.archive().withSession(context.borrowedSession()),context.frameLoader());
  var frame=AutoCameraModel.copy(f,i.owner());var h=AutoCameraModel.hotspot(frame,land);
  String target=h.map(v->v.war()+":"+v.army()+":"+v.province()+":"+v.reason()).orElse("");
  policy.failed(frame,new Decision(i.mode(),i.titleKey(),"native_actual_failure",i.tracking(),target),date);
 }
 RawJson status(){var n=StrictJson.object().put("worker_installed",true).put("status",closed?"closed":worker.unresolvedPhysical()?"unknown":"available")
   .put("diagnostic",diagnostic).put("pending",worker.pending()).put("running",worker.running()).put("automatic_retry",false)
   .put("new_game_queries",0).put("camera_postcondition_verified",false).put("continuous_frame_coverage_verified",false).put("same_frame_with_gameplay_claim",false);
  if(latestActual.isPresent())n.set("latest_actual",StrictJson.parse(latestActual.orElseThrow().bytes()));else n.putNull("latest_actual");
  if(lastReceipt.isPresent())n.set("canonical_receipt",StrictJson.parse(lastReceipt.orElseThrow().bytes()));
  var failures=n.putArray("recent_failures");worker.failures().forEach(failures::add);return new RawJson(StrictJson.canonical(n));}
 @Override public void close(){closed=true;active=false;currentOwner.set(null);worker.close();}
}
