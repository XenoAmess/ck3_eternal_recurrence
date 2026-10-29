package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.presentation.*;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.nativebridge.capabilities.gui.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.*;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Same Root physical producer. It never constructs a pipe request, ordinary Ready or gameplay credit. */
public final class RootGuiPresentation implements GuiService.PresentationPlane,AutoCloseable {
 public static final OperationKey OPERATION=new OperationKey("gui-camera-presentation-v1");
 public static final String OBSERVER="xar.java.camera-presentation-completion/v1";
 @FunctionalInterface public interface CommandRuntime{RootGuiPresentation require(ActionCommand exact)throws IOException;}
 @FunctionalInterface public interface RequestRuntime{RootGuiPresentation require(PresentationRequest exact)throws IOException;}
 public static PhysicalActionRegistry.Binding binding(List<ExactRef> sources,CommandRuntime commandOwner,RequestRuntime requestOwner,
        CommandRuntime businessOwner,java.util.function.Supplier<List<RootGuiPresentation>> runtimes){
  return new PhysicalActionRegistry.Binding(OPERATION,TransportKind.PRESENTATION_MMAP,sources,new PhysicalActionRegistry.Producer(){
   @Override public boolean automatic(ActionCommand command){try{return commandOwner.require(command).automatic(command);}catch(IOException|IllegalArgumentException unavailable){return false;}}
   @Override public void verifyOptional(Session same,ActionReceipt receipt)throws IOException{
    var runtime=commandOwner.require(receipt.command());runtime.context.writer().requireSession(same);
    var archive=runtime.context.archive().withSession(same);require(receipt.equals(archive.loadReceipt(archive.receiptReferenceOf(receipt))),"optional receipt lost canonical archive");
    runtime.verifyAutomaticArchived(same.head(),receipt,archive);
   }
   @Override public PresentationIntent automaticIntent(ActionCommand command){return RootGuiPresentation.automaticIntent(command);}
   @Override public void verifyDeferredOwner(ActionCommand command)throws IOException{commandOwner.require(command).autoCamera.verifyOwner(command);}
   @Override public boolean liveCustody(Session same,ActionCommand command)throws IOException{try{return commandOwner.require(command).autoCamera.liveCustody(same,command);}catch(IOException|IllegalArgumentException unavailable){return false;}}
   @Override public void beforeNative(Session same,ActionCommand command,GuardEvidence guard,List<ActionReceipt> history,PhysicalActionRegistry.Queue queue)throws IOException{
    try{businessOwner.require(command).autoCamera.beforeNative(same,command,guard,history,queue);}catch(IOException unavailable){/* no installed actual AUTO owner */}
   }
   @Override public void queued(Session same,ActionCommand command,GuardEvidence guard,PresentationPermit permit)throws IOException{commandOwner.require(command).autoCamera.queued(same,command,guard,permit);}
   @Override public List<PhysicalActionRegistry.DeferredResult> collect(Session same)throws IOException{
    var all=new ArrayList<PhysicalActionRegistry.DeferredResult>();for(var runtime:runtimes.get())all.addAll(runtime.autoCamera.collect(same));return List.copyOf(all);
   }
   @Override public void committed(String actionId){for(var runtime:runtimes.get())runtime.autoCamera.committed(actionId);}

   @Override public GuardEvidence guard(WriterContracts.Head head,ActionCommand command)throws IOException{return commandOwner.require(command).guard(head,command);}
   @Override public PreparedAction prepare(Session same,ActionCommand command,String requestId)throws IOException{return commandOwner.require(command).prepare(same,command,requestId);}
   @Override public PhysicalOutcome post(PhysicalSubmission permit,PreparedAction prepared,Instant deadline)throws IOException{
    require(permit instanceof PresentationPermit&&prepared instanceof PreparedAction.MmapRequest,"original mmap request and central private permit required");
    var request=((PreparedAction.MmapRequest)prepared).value();return requestOwner.require(request).post((PresentationPermit)permit,request,deadline);
   }
   @Override public PhysicalActionRegistry.Observation observe(Session same,ActionCommand command,PhysicalActionState original,Instant deadline)throws IOException{return commandOwner.require(command).observe(same,command,original,deadline);}
   @Override public void verifyArchived(WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException{commandOwner.require(receipt.command()).verifyArchived(head,receipt,archive);}
  });
 }
 private final RootRuntimeContext context;private final List<ExactRef> sources;
 private final org.xar.ck3.control.platform.ManagedGameSession.NativePhysicalSourceAccess access;
 private final NativeCameraObserver observer;private NativePresentationTransport transport;
 private final Map<String,PresentationRequest> prepared=new LinkedHashMap<>();
 private final RootAutoCamera autoCamera;
 private Optional<GuiRealmCameraStatus.Submission> submission=Optional.empty();private boolean closed;
 public RootGuiPresentation(RootRuntimeContext context,List<ExactRef> sources)throws IOException{
  this.context=Objects.requireNonNull(context);this.sources=List.copyOf(sources);require(!this.sources.isEmpty(),"actual physical source inventory required");
  context.game().launchPlan().sources().requireLoadedClass(RootGuiPresentation.class);context.game().launchPlan().sources().requireLoadedClass(NativeCameraObserver.class);access=context.game().presentationAccess();access.requireOwner(context.game());
  observer=new NativeCameraObserver(access.actualConfig(),access.actualGuard());autoCamera=new RootAutoCamera(context,this);
 }
 public boolean owns(ActionCommand command){return command.origin() instanceof CommandOrigin.Gameplay&&command.operation().equals(OPERATION)
  &&command.before().game().equals(context.game().generation())&&command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId());}
 public boolean matchesCommand(ActionCommand command){try{requireCommand(command);return true;}catch(IllegalArgumentException malformed){return false;}}
 public synchronized boolean owns(PresentationRequest request){return prepared.values().stream().anyMatch(actual->Arrays.equals(actual.encode(),request.encode()));}
 private ActionPorts.OutcomeArchive archive()throws IOException{return context.archive().withSession(context.borrowedSession());}
 private void requireCommand(ActionCommand command){
  require(owns(command)&&command.expected().observerSchema().equals(OBSERVER),"physical GUI command crossed its actual Root or expected observer");
  if(automatic(command)){verifyAutomaticCommand(command);return;}
  var fields=StrictJson.object(OpportunityJson.toNode(command.arguments()),Set.of("mode"));mode(fields);
  require(command.expected().values().equals(List.of(new ExpectedBoolean(new FieldKey("camera.presentation_complete"),true))),"physical expectation cannot claim business/day/SAVE");
 }
 private static PresentationRequest.Mode mode(ObjectNode fields){var mode=PresentationRequest.Mode.valueOf(StrictJson.text(fields.get("mode")));require(mode==PresentationRequest.Mode.REALM||mode==PresentationRequest.Mode.QUERY,"only original realm/query producer installed");return mode;}
 private PresentationRequest.Owner owner(ActionCommand command)throws IOException{
  requireCommand(command);var hello=context.transport().originalHello();
  require(hello.buildMatch()&&hello.pid()==context.game().generation().pid()&&hello.gameSha256().equalsIgnoreCase(PresentationRequest.EXECUTABLE_SHA256),"actual exact reviewed HELLO required");
  return new PresentationRequest.Owner(context.game().machineId(),context.game().sessionId(),context.game().generation().pid(),context.game().generation().creationFiletime().value().toString(),
   PresentationRequest.EXECUTABLE_SHA256,command.before().frame().episodeRunId(),hello.connectionGeneration().toString());
 }
 private synchronized NativePresentationTransport transport(PresentationRequest.Owner owner)throws IOException{
  if(closed)throw new IOException("actual GUI presentation runtime is closed");access.requireOwner(context.game());
  if(transport==null){PresentationOriginals originals=new PresentationOriginals(){
   @Override public ExactRef preservePresentationArtifact(OriginalArtifact original){try{return archive().preservePresentationArtifact(original);}catch(IOException failure){throw new UncheckedIOException(failure);}}
   @Override public OriginalArtifact loadPresentationArtifact(ArtifactRole role,ExactRef original){try{return archive().loadPresentationArtifact(role,original);}catch(IOException failure){throw new UncheckedIOException(failure);}}
   @Override public ExactRef presentationArtifactReferenceOf(OriginalArtifact original){try{return archive().presentationArtifactReferenceOf(original);}catch(IOException failure){throw new UncheckedIOException(failure);}}
  };transport=NativePresentationTransport.open(access.actualConfig(),owner,access.actualGuard(),originals);}
  return transport;
 }
 private GuardEvidence guard(WriterContracts.Head head,ActionCommand command)throws IOException{
  requireCommand(command);if(automatic(command))return automaticGuardFromCommand(head,command);
  var same=context.borrowedSession();context.writer().requireSession(same);require(same.head().equals(head),"physical guard must retain actual writer Head");
  access.requireOwner(context.game());
  // Each guard revalidates the existing physical frame. A native operation/capability alias is never installed.
  return context.collector().current(same,command.before(),command.deadline(),lease->{
   require(lease.frame().source().equals(context.source())&&lease.frame().sessionId().equals(context.game().sessionId()),"physical guard source/session changed");
   var archive=archive();var capabilities=new RawJson(OpportunityJson.encode(lease.capabilities()));var cap=archive.preserveMaterial(capabilities);
   require(archive.loadMaterial(cap).equals(capabilities),"actual physical capability original changed");
   var basis=RootGuardEvidence.preserve(lease,OPERATION,context.core().authorityId(),cap,archive,head);
   var frame=NativeEffectEvidence.basis(lease.frame());
   return new GuardEvidence(lease.frame().identity(),context.source(),context.game().sessionId(),lease.frame().connectionGeneration(),OPERATION,
    frame.nativeFrame(),lease.originalHello(),context.core().authorityId(),lease.frame().observedAt(),lease.validUntil(),List.of(basis));
  });
 }
 private PreparedAction prepare(Session same,ActionCommand command,String requestId)throws IOException{
  context.writer().requireSession(same);requireCommand(command);require(requestId.equals(RequestIds.forCommand(command)),"physical request identity changed");
  var actualOwner=owner(command);var inspection=transport(actualOwner).inspect(command.deadline());var archive=archive();
  var header=new PresentationOriginals.OriginalArtifact(PresentationOriginals.ArtifactRole.HEADER,inspection.originalHeader());
  var headerRef=archive.preservePresentationArtifact(header);header.requireReference(headerRef);require(archive.loadPresentationArtifact(header.role(),headerRef).equals(header),"inspection original header changed");
  var raw=inspectionBody(command,inspection,headerRef,sources);var proof=archive.preserveMaterial(raw);require(archive.loadMaterial(proof).equals(raw),"actual physical inspection original changed");
  var request=prepareOriginal(command,inspection,List.of(proof,headerRef));verifyPrepared(command,request,archive);
  // Validate the installed status consumer before any once permit or physical mutation.
  statusOwner(request);new GuiCameraCapabilities.Binding(request.requestSequence(),request.frame().actor(),request.frame().dateRaw(),request.owner().episodeRunId());
  synchronized(this){require(prepared.size()<128||prepared.containsKey(requestId),"finite original presentation request custody bound");require(prepared.putIfAbsent(requestId,request)==null,"prepared physical request cannot be replaced");}
  return new PreparedAction.MmapRequest(request);
 }
 /** DATA producer shared with wire/archive regressions; only the central private permit may post it. */
 static PresentationRequest prepareOriginal(ActionCommand command,NativePresentationTransport.Inspection inspection,List<ExactRef> evidence){
  require(command.operation().equals(OPERATION)&&command.expected().observerSchema().equals(OBSERVER),"physical realm/query original command required");
  byte[] rawHeader=inspection.originalHeader();require(rawHeader.length==24,"complete original mapping header required");
  var header=java.nio.ByteBuffer.wrap(rawHeader).order(java.nio.ByteOrder.LITTLE_ENDIAN);
  require(header.getInt()==PresentationRequest.MAGIC&&header.getInt()==1&&Integer.toUnsignedLong(header.getInt())==inspection.owner().processId()&&header.getInt()==0
   &&Integer.toUnsignedLong(header.getInt())==inspection.previousRequestSequence()&&Integer.toUnsignedLong(header.getInt())==inspection.baselineResultSequence(),"original inspection mapping identity/counters differ");
  var mode=mode(StrictJson.object(OpportunityJson.toNode(command.arguments()),Set.of("mode")));var f=command.before().frame();
  require(inspection.owner().machineId().equals(command.source().machineId())&&inspection.owner().sessionId().equals(command.sessionId())
   &&inspection.owner().processId()==command.before().game().pid()&&inspection.owner().processBirthFiletime().equals(command.before().game().creationFiletime().value().toString())
   &&inspection.owner().episodeRunId().equals(f.episodeRunId()),"actual inspection owner crossed command frame");
  return new PresentationRequest(RequestIds.forCommand(command),inspection.observedAt(),inspection.owner(),
   new PresentationRequest.Frame(f.snapshotId(),f.revision().toString(),f.identity().nativeRevision().toString(),f.identity().player().intValueExact(),f.identity().dateRaw().intValueExact()),mode,
   inspection.previousRequestSequence(),PresentationRequest.nextSequence(inspection.previousRequestSequence()),inspection.baselineResultSequence(),
   new BigInteger(inspection.uptimeMillis()).add(BigInteger.valueOf(10000)).toString(),inspection.hwnd(),Float.floatToRawIntBits(mode==PresentationRequest.Mode.REALM?.32f:.15f),"",Optional.empty(),evidence);
 }
 static RawJson inspectionBody(ActionCommand command,NativePresentationTransport.Inspection inspection,ExactRef header,List<ExactRef> sources){
  var n=StrictJson.object().put("schema","xar.java.gui-presentation-inspection/v1").put("command_body_sha256",ActionCodec.bodySha256(command)).put("observed_at",inspection.observedAt().toString())
   .put("previous_request_sequence",inspection.previousRequestSequence()).put("baseline_result_sequence",inspection.baselineResultSequence()).put("uptime_ms",inspection.uptimeMillis()).put("hwnd",inspection.hwnd());
  n.set("owner",inspection.owner().toJson());n.set("original_header",header.toJson());var a=n.putArray("source_inventory");sources.forEach(ref->a.add(ref.toJson()));return new RawJson(StrictJson.canonical(n));
 }
 private void verifyPrepared(ActionCommand command,PresentationRequest request,ActionPorts.OutcomeArchive archive){
  requireCommand(command);require(request.preparationEvidence().size()==2,"two exact inspection originals required");var proof=request.preparationEvidence().getFirst();var raw=archive.loadMaterial(proof);
  require(proof.equals(archive.materialReferenceOf(raw)),"actual preparation material identity changed");
  var n=StrictJson.object(StrictJson.parse(raw.bytes()),Set.of("schema","command_body_sha256","observed_at","previous_request_sequence","baseline_result_sequence","uptime_ms","hwnd","owner","original_header","source_inventory"));
  require(StrictJson.text(n.get("schema")).equals("xar.java.gui-presentation-inspection/v1")&&StrictJson.text(n.get("command_body_sha256")).equals(ActionCodec.bodySha256(command)),"original physical inspection belongs to another command");
  var headerRef=ExactRef.fromJson(n.get("original_header"));require(headerRef.equals(request.preparationEvidence().get(1)),"inspection header role differs");
  var header=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER,headerRef);header.requireReference(headerRef);
  var expectedSources=StrictJson.object().putArray("refs");sources.forEach(ref->expectedSources.add(ref.toJson()));require(expectedSources.equals(n.get("source_inventory")),"actual source inventory changed");
  var inspection=new NativePresentationTransport.Inspection(PresentationRequest.Owner.fromJson(n.get("owner")),Instant.parse(StrictJson.text(n.get("observed_at"))),
   StrictJson.integer(n.get("previous_request_sequence"),BigInteger.ZERO,new BigInteger("4294967295")).longValueExact(),StrictJson.integer(n.get("baseline_result_sequence"),BigInteger.ZERO,new BigInteger("4294967295")).longValueExact(),
   StrictJson.text(n.get("uptime_ms")),StrictJson.text(n.get("hwnd")),header.bytes());
  require(Arrays.equals(prepareOriginal(command,inspection,request.preparationEvidence()).encode(),request.encode()),"archived physical request differs from actual inspection producer");
 }
 private PhysicalOutcome post(PresentationPermit permit,PresentationRequest request,Instant deadline)throws IOException{
  require(owns(request),"physical post request has no actual preparation in this runtime");var outcome=transport(request.owner()).post(permit,request,deadline);
  var archive=archive();var ref=archive.preservePresentationOutcome(outcome);require(archive.loadPresentationOutcome(ref).equals(outcome)&&archive.presentationOutcomeReferenceOf(outcome).equals(ref),"actual physical result custody changed");
  if(!(outcome instanceof OriginalOutcome.NotPosted))synchronized(this){submission=Optional.of(new GuiRealmCameraStatus.Submission(new GuiCameraCapabilities.Binding(request.requestSequence(),request.frame().actor(),request.frame().dateRaw(),request.owner().episodeRunId()),
   statusOwner(request),request.mode()==PresentationRequest.Mode.REALM?GuiRealmCameraStatus.Mode.REALM:GuiRealmCameraStatus.Mode.QUERY,OptionalInt.empty()));}
  return new PhysicalOutcome.MmapOutcome(outcome);
 }
 private static GuiRealmCameraStatus.Owner statusOwner(PresentationRequest request){return new GuiRealmCameraStatus.Owner(request.frame().actor(),request.owner().episodeRunId(),request.owner().processId(),new BigInteger(request.owner().connectionGeneration()));}
 private PhysicalActionRegistry.Observation observe(Session same,ActionCommand command,PhysicalActionState original,Instant deadline)throws IOException{
  context.writer().requireSession(same);if(automatic(command))return observeAutomatic(same,command,original,deadline);
  requireCommand(command);require(original.request() instanceof PreparedAction.MmapRequest,"original mmap request absent");var request=((PreparedAction.MmapRequest)original.request()).value();verifyPrepared(command,request,archive());
  if(original.outcome().isEmpty()||!(original.outcome().orElseThrow() instanceof PhysicalOutcome.MmapOutcome returned)||!(returned.value() instanceof OriginalOutcome.Posted))
   return new PhysicalActionRegistry.Pending("no proved even publication; retain original UNKNOWN without another post",original.evidence());
  var observed=transport(request.owner()).observe(request,deadline);var archive=archive();var ref=archive.preservePresentationObservation(observed);
  require(archive.loadPresentationObservation(ref).equals(observed)&&archive.presentationObservationReferenceOf(observed).equals(ref),"actual presentation observation custody changed");
  var originals=new ArrayList<>(original.evidence());require(originals.size()<16,"bounded original presentation observation history exhausted");originals.add(ref);
  boolean complete=completion(request,originals.stream().map(archive::loadPresentationObservation).toList(),archive);return complete?new PhysicalActionRegistry.Completed(originals):new PhysicalActionRegistry.Pending("original result is not independently complete; no repost",originals);
 }
 /** Requires retained full original result/header/tail, never just an ACK or status string. */
 static boolean completion(PresentationRequest request,PresentationObservation observation,ActionPorts.OutcomeArchive archive){return completion(request,List.of(observation),archive);}
 static boolean completion(PresentationRequest request,List<PresentationObservation> observations,ActionPorts.OutcomeArchive archive){
  require(!observations.isEmpty()&&observations.size()<=16,"bounded independent original observation chain required");
  var original=new GuiRealmCameraStatus.Submission(new GuiCameraCapabilities.Binding(request.requestSequence(),request.frame().actor(),request.frame().dateRaw(),request.owner().episodeRunId()),statusOwner(request),request.mode()==PresentationRequest.Mode.REALM?GuiRealmCameraStatus.Mode.REALM:GuiRealmCameraStatus.Mode.QUERY,OptionalInt.empty());
  Instant previous=request.preparedAt();boolean complete=false;
  for(var observation:observations){
   complete=false;require(Arrays.equals(request.encode(),observation.request().encode()),"completion crossed original request");
   if(!(observation instanceof PresentationObservation.Acknowledged ack))continue;
   var capture=ack.capture();require(!capture.observedAt().isBefore(previous),"actual observation chain regressed");previous=capture.observedAt();
   byte[] header=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER,capture.originalHeader()).bytes();
   byte[] raw=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.RESULT,capture.originalResult()).bytes();byte[] diagnostics=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.DIAGNOSTICS,capture.originalDiagnostics()).bytes();
   ack.verifyOriginal(header,raw,diagnostics);var result=NativeCameraObserver.decodeResult(raw);
   if(result.actor()!=request.frame().actor()||result.dateRaw()<request.frame().dateRaw()||result.dateRaw()>(long)request.frame().dateRaw()+7*24)continue;
   if(request.mode()==PresentationRequest.Mode.QUERY){complete=ack.status()==PresentationObservation.Status.BOUNDS_AVAILABLE;continue;}
   var actual=new NativeCameraObserver.DetailedCapture(new NativeCameraObserver.Capture(request.owner().machineId(),request.owner().processId(),request.owner().sessionId(),capture.resultSequence(),capture.observedAt(),result,raw),diagnostics);
   var projected=GuiRealmCameraStatus.project(true,statusOwner(request),Optional.of(original),Optional.of(actual));
   complete=ack.status()==PresentationObservation.Status.SETTLED&&result.zoomIndex()>=0&&result.cameraPostconditionVerified()&&projected.nativeActual().isPresent();
  }
  return complete;
 }
 private void verifyArchived(WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException{
  if(automatic(receipt.command())){verifyAutomaticArchived(head,receipt,archive);return;}
  requireCommand(receipt.command());
  if(receipt.state() instanceof ActionState.IntentDurable)return;
  require(receipt.state() instanceof PhysicalActionState,"physical producer cannot replay native/business settlement");var state=(PhysicalActionState)receipt.state();
  require(state.request() instanceof PreparedAction.MmapRequest,"physical replay crossed plane");var request=((PreparedAction.MmapRequest)state.request()).value();verifyPrepared(receipt.command(),request,archive);
  RootGuardEvidence.requireHistory(state.guard(),archive,context.borrowedSession());var frame=RootGuardEvidence.loadFrame(state.guard(),archive,context.frameLoader());
  require(frame.identity().equals(receipt.command().before())&&state.guard().authorityId().equals(context.core().authorityId())&&state.guard().operation().equals(OPERATION)
   &&state.guard().source().equals(receipt.command().source())&&state.guard().sessionId().equals(receipt.command().sessionId())
   &&request.owner().connectionGeneration().equals(state.guard().connectionGeneration().toString()),"archived physical guard changed actual owner");
  if(state.outcome().isPresent()){var outcome=((PhysicalOutcome.MmapOutcome)state.outcome().orElseThrow()).value();require(outcome.equals(archive.loadPresentationOutcome(archive.presentationOutcomeReferenceOf(outcome))),"physical original outcome changed");
   if(outcome instanceof OriginalOutcome.Posted posted){var metadata=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.POST_METADATA,posted.originalPostEvidence()).bytes();var evidence=OriginalOutcome.PostEvidence.decode(metadata);
    posted.verifyOriginal(archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.REQUEST,posted.originalRequest()).bytes(),Optional.empty(),metadata,
     archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER,evidence.beforeHeader()).bytes(),archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER,evidence.afterHeader()).bytes());}
  }
  if(state.phase()==PhysicalActionState.Phase.COMPLETED){require(state.outcome().isPresent()&&((PhysicalOutcome.MmapOutcome)state.outcome().orElseThrow()).value() instanceof OriginalOutcome.Posted&&!state.evidence().isEmpty()&&state.evidence().size()<=16,"completion requires original publication and independent after proof");
   require(completion(request,state.evidence().stream().map(archive::loadPresentationObservation).toList(),archive),"archived physical completion is not independently proved");}
 }
 @Override public GuiContract.Reply submit(GuiService.Invocation invocation,boolean queryOnly)throws IOException{
  if(!(context.actions() instanceof RootApplicationSession root))throw new IOException("actual installed Root session required for physical presentation");
  try{return execute(root,invocation,queryOnly);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("original presentation interrupted; UNKNOWN must not replay",interrupted);}
 }
 public GuiContract.Reply execute(RootApplicationSession root,GuiService.Invocation requested,boolean queryOnly)throws IOException,InterruptedException{
  return executePrepared(root,Optional.of(requested),Optional.of(requested.publicRevision()),requested.nativeContext().deadline(),queryOnly);
 }
 public GuiContract.Reply execute(RootApplicationSession root,GuiContract.Request request,Instant deadline)throws IOException,InterruptedException{
  require(request.method()==GuiContract.Method.CENTER_REALM||request.method()==GuiContract.Method.QUERY_BOUNDS,"finite original physical public method required");
  Optional<BigInteger> expected=request.expectedRevision() instanceof org.xar.ck3.control.contracts.PublicUnsigned64.Value value?Optional.of(value.value()):Optional.empty();
  return executePrepared(root,Optional.empty(),expected,deadline,request.method()==GuiContract.Method.QUERY_BOUNDS);
 }
 private GuiContract.Reply executePrepared(RootApplicationSession root,Optional<GuiService.Invocation> requested,Optional<BigInteger> expected,Instant deadline,boolean queryOnly)throws IOException,InterruptedException{
  require(root==context.actions(),"physical public call crossed sole Root");
  return root.executePublicDecision(deadline,(frame,driver,same)->{
   require(frame.semantic().get("paused") instanceof OpportunityJson.Bool paused&&paused.value()&&frame.semantic().get("map_ready") instanceof OpportunityJson.Bool map&&map.value(),"original physical presentation requires paused map-ready source");
   expected.ifPresent(value->require(frame.identity().frame().revision().equals(value),"physical GUI expected public revision differs"));
   requested.ifPresent(value->require(frame.identity().equals(value.nativeContext().before())&&frame.source().equals(value.nativeContext().source())&&frame.sessionId().equals(value.nativeContext().sessionId()),"physical public frame changed before preparation"));
   var existing=context.core().actions().withFrozen(same,lease->{var pending=lease.snapshot().actions().stream().filter(r->owns(r.command())&&!(r.state() instanceof PhysicalActionState p&&p.terminal())&&!(r.state() instanceof ActionState.RejectedBeforeDispatch)).toList();lease.assertCurrent();require(pending.size()<=1,"multiple unresolved original presentation actions");return pending.stream().findFirst();});
   if(existing.isPresent()){var retained=existing.orElseThrow();return new RootApplicationSession.ReconcilePublicAction<GuiContract.Reply>(retained.command().actionId(),archive().receiptReferenceOf(retained));}
   var fields=StrictJson.object().put("mode",queryOnly?"QUERY":"REALM");var postcondition=new ExpectedPostcondition(1,frame.identity(),frame.source(),OBSERVER,List.of(new ExpectedBoolean(new FieldKey("camera.presentation_complete"),true)));
   var command=new ActionCommand("gui-camera-"+UUID.randomUUID().toString().replace("-",""),frame.identity(),frame.source(),frame.sessionId(),OPERATION,GuiService.arguments(fields),postcondition,
    new Claims(Set.of(),Set.of(),Set.of(frame.identity().frame().identity().player()),Set.of("camera:"+frame.sessionId())),deadline);
   return new RootApplicationSession.SubmitPublicAction<GuiContract.Reply>(command);
  },(receipt,archive,same)->project(receipt,archive));
 }
 static GuiContract.Reply project(ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
  var out=StrictJson.object().put("status","UNKNOWN").put("mode",StrictJson.text(OpportunityJson.toNode(receipt.command().arguments()).get("mode")).toLowerCase(Locale.ROOT))
   .put("reason","explicit_realm_camera").put("native_command_pipe_used",false).put("desktop",1).put("camera_postcondition_verified",false).put("same_frame_with_gameplay_claim",false)
   .put("canonical_action_id",receipt.command().actionId()).put("automatic_retry",false).put("game_day_credit",false).put("save_credit",false);
  if(receipt.state() instanceof PhysicalActionState state&&state.request() instanceof PreparedAction.MmapRequest mmap){out.put("request_sequence",mmap.value().requestSequence());if(state.outcome().isPresent()&&((PhysicalOutcome.MmapOutcome)state.outcome().orElseThrow()).value() instanceof OriginalOutcome.Posted)out.put("status","queued_native_presentation");
   out.put("physical_phase",state.phase().name());}
  out.put("canonical_receipt",archive.receiptReferenceOf(receipt).path());return new GuiContract.NativeReply(new RawJson(StrictJson.canonical(out)));
 }
 @Override public synchronized Optional<GuiRealmCameraStatus.Submission> originalSubmission(){return submission;}
 @Override public Optional<NativeCameraObserver> actualObserver(){return Optional.of(observer);}
 @Override public GuiRealmCameraStatus.Owner currentOwner()throws IOException{
  return context.withSession(same->context.adopted().authority().withFrozenFacts(same,frozen->{
   require(frozen.state() instanceof org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known,"actual Driver owner unavailable");var driver=((org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known)frozen.state()).driver().session();var hello=context.transport().originalHello();
   return new GuiRealmCameraStatus.Owner(driver.actorId().intValueExact(),driver.episodeRunId(),context.game().generation().pid(),hello.connectionGeneration());
  }));
 }
 @Override public synchronized void close()throws IOException{if(closed)return;closed=true;autoCamera.close();IOException failure=null;try{observer.close();}catch(IOException e){failure=e;}if(transport!=null)try{transport.close();}catch(IOException e){if(failure==null)failure=e;else failure.addSuppressed(e);}if(failure!=null)throw failure;}

 public RootAutoCamera automaticCamera(){return autoCamera;}
 boolean ownsGame(ActionCommand command){return command.origin() instanceof CommandOrigin.Gameplay&&command.origin().game().equals(context.game().generation())
   &&command.sessionId().equals(context.game().sessionId())&&command.source().equals(context.source());}
 static boolean automaticCandidate(ActionCommand command){return command.operation().equals(OPERATION)&&command.arguments().get("automatic_intent") instanceof OpportunityJson.Obj;}
 boolean automatic(ActionCommand command){return owns(command)&&automaticCandidate(command);}
 static PresentationIntent automaticIntent(ActionCommand command){
  var n=StrictJson.object(OpportunityJson.toNode(command.arguments()),Set.of("automatic_intent","automatic_guard","parent_receipt"));
  var template=PresentationIntent.fromJson(n.get("automatic_intent"));
  require(template.requestId().equals(command.actionId()),"automatic durable template belongs to another action");
  var f=command.before().frame();require(template.frame().snapshotId().equals(f.snapshotId())&&template.frame().revision().equals(f.revision().toString())
   &&template.frame().nativeRevision().equals(f.identity().nativeRevision().toString())&&template.frame().actor()==f.identity().player().intValueExact()
   &&template.frame().dateRaw()==f.identity().dateRaw().intValueExact()&&template.owner().episodeRunId().equals(f.episodeRunId())
   &&template.deadline().equals(command.deadline()),"automatic template changed command frame/deadline");
  return new PresentationIntent(RequestIds.forCommand(command),template.createdAt(),template.owner(),template.frame(),template.mode(),template.titleKey(),template.tracking(),template.deadline());
 }
 static GuardEvidence guard(ActionCommand command){return ActionReceiptCodec.decodeGuard(OpportunityJson.toNode(command.arguments()).get("automatic_guard"));}
 static ExactRef parent(ActionCommand command){return ExactRef.fromJson(OpportunityJson.toNode(command.arguments()).get("parent_receipt"));}

 private void verifyAutomaticCommand(ActionCommand command){
  var intent=automaticIntent(command);var guard=guard(command);
  require(intent.owner().machineId().equals(context.game().machineId())&&intent.owner().sessionId().equals(command.sessionId())
    &&intent.owner().processId()==context.game().generation().pid()&&intent.owner().processBirthFiletime().equals(context.game().generation().creationFiletime().value().toString())
    &&intent.owner().connectionGeneration().equals(guard.connectionGeneration().toString())&&guard.observed().equals(command.before())
    &&guard.operation().equals(OPERATION)&&guard.source().equals(context.source()),"automatic source/owner/frame differs");
  require(command.expected().observerSchema().equals(OBSERVER)&&command.expected().values().equals(List.of(new ExpectedBoolean(new FieldKey("camera.presentation_complete"),true))),"automatic camera cannot claim gameplay");
 }
 PresentationRequest.Owner ownerFor(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame)throws IOException{
  var hello=context.transport().originalHello();require(hello.buildMatch()&&hello.gameSha256().equalsIgnoreCase(PresentationRequest.EXECUTABLE_SHA256)
    &&hello.connectionGeneration().equals(frame.connectionGeneration()),"automatic actual reviewed connection required");
  return new PresentationRequest.Owner(context.game().machineId(),frame.sessionId(),context.game().generation().pid(),
    context.game().generation().creationFiletime().value().toString(),PresentationRequest.EXECUTABLE_SHA256,frame.identity().frame().episodeRunId(),frame.connectionGeneration().toString());
 }
 NativePresentationTransport transportFor(PresentationRequest.Owner owner)throws IOException{return transport(owner);}
 GuardEvidence automaticGuard(Session same,org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,GuardEvidence original,
    Instant deadline,org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known)throws IOException{
  context.writer().requireSession(same);context.game().verify();var archive=archive();RootGuardEvidence.requireHistory(original,archive,same);
  require(original.source().equals(context.source())&&original.origin().game().equals(frame.identity().game()),"automatic source guard crossed actual Game");
  var n=StrictJson.parse(archive.loadMaterial(original.supportingEvidence().getFirst()).bytes());
  var semantic=archive.preserveMaterial(RawJson.fullMaterial(org.xar.ck3.control.application.driver.DriverJson.encode(frame.semantic())));
  var stamp=known==null?ExactRef.fromJson(n.get("driver_stamp")):archive.preserveMaterial(new RawJson(org.xar.ck3.control.application.readiness.NativeDriverStamp.encode(frame,known)));
  var driver=known==null?ExactRef.fromJson(n.get("original_driver")):archive.preserveMaterial(RawJson.fullMaterial(known.driver().encode()));
  var sem=new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(frame.identity(),semantic,frame.originalEvidence(),stamp,driver,frame.observedAt());
  var basis=RootGuardEvidence.preservePhysicalRead(new RootGuardEvidence.PhysicalReadOriginals(frame,sem,ExactRef.fromJson(n.get("hello")),
    ExactRef.fromJson(n.get("heartbeat")),ExactRef.fromJson(n.get("source_qualification")),ExactRef.fromJson(n.get("capabilities"))),OPERATION,context.core().authorityId(),archive,same.head());
  Instant until=frame.observedAt().plusSeconds(10);if(deadline.isBefore(until))until=deadline;
  return new GuardEvidence(frame.identity(),context.source(),frame.sessionId(),frame.connectionGeneration(),OPERATION,frame.originalEvidence(),
    original.capabilityEvidence(),context.core().authorityId(),frame.observedAt(),until,List.of(basis));
 }
 private GuardEvidence automaticGuardFromCommand(WriterContracts.Head head,ActionCommand command)throws IOException{
  verifyAutomaticCommand(command);var g=guard(command);var archive=archive();var same=context.borrowedSession();require(same.head().equals(head),"automatic guard lost original writer");
  RootGuardEvidence.requireHistory(g,archive,same);context.game().verify();
  var original=archive.loadReceipt(parent(command));require(original.command().source().equals(command.source())&&original.command().origin() instanceof CommandOrigin.Gameplay
    &&original.command().before().game().equals(command.before().game())&&original.command().before().frame().episodeRunId().equals(command.before().frame().episodeRunId()),
    "automatic intent has no actual original gameplay parent");
  RootGuardEvidence.loadFrame(g,archive,context.frameLoader());return g;
 }
 ActionCommand automaticCommand(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,String id,ObjectNode args,Instant deadline){
  var expected=new ExpectedPostcondition(1,frame.identity(),frame.source(),OBSERVER,List.of(new ExpectedBoolean(new FieldKey("camera.presentation_complete"),true)));
  return new ActionCommand(id,frame.identity(),frame.source(),frame.sessionId(),OPERATION,GuiService.arguments(args),expected,
    new Claims(Set.of(),Set.of(),Set.of(frame.identity().frame().identity().player()),Set.of("camera:"+frame.sessionId())),deadline);
 }
 private static ExactRef artifact(ActionPorts.OutcomeArchive archive,PresentationOriginals.ArtifactRole role,byte[] bytes){
  var a=new PresentationOriginals.OriginalArtifact(role,bytes);var ref=archive.preservePresentationArtifact(a);a.requireReference(ref);
  require(a.equals(archive.loadPresentationArtifact(role,ref)),"automatic physical archive changed");return ref;
 }
 PhysicalActionRegistry.DeferredResult archiveAutomatic(Session same,ActionCommand command,GuardEvidence guard,PresentationCapture raw)throws IOException{
  context.writer().requireSession(same);return archiveAutomaticOriginal(command,guard,raw,archive());
 }
 static PhysicalActionRegistry.DeferredResult archiveAutomaticOriginal(ActionCommand command,GuardEvidence guard,PresentationCapture raw,ActionPorts.OutcomeArchive archive){require(Arrays.equals(raw.intent().encode(),automaticIntent(command).encode()),"capture changed durable automatic intent");
  var material=new RawJson(raw.encode());var capture=archive.preserveMaterial(material);require(archive.loadMaterial(capture).equals(material),"raw automatic capture changed");
  if(raw.kind()==PresentationCapture.Kind.NOT_ATTEMPTED)return new PhysicalActionRegistry.DeferredResult(command,new ActionState.Unknown(Optional.empty(),Optional.empty(),
    "actual automatic capture proved no physical preparation; original intent is not replayed",List.of(capture)));
  var prepared=raw.prepared().orElseThrow();var before=artifact(archive,PresentationOriginals.ArtifactRole.HEADER,prepared.header());
  var request=prepared.canonical(List.of(capture,before));var requestRef=artifact(archive,PresentationOriginals.ArtifactRole.REQUEST,prepared.requestBytes());
  Optional<ExactRef> tracking=prepared.trackingBytes().map(b->artifact(archive,PresentationOriginals.ArtifactRole.TRACKING_REQUEST,b));
  OriginalOutcome outcome;
  if(raw.kind()==PresentationCapture.Kind.POSTED){
   var after=artifact(archive,PresentationOriginals.ArtifactRole.HEADER,raw.afterHeader());var metadata=new OriginalOutcome.PostEvidence(request.owner(),request.requestId(),raw.observedAt(),
     request.previousRequestSequence(),request.requestSequence(),before,after,requestRef,tracking);
   var ref=artifact(archive,PresentationOriginals.ArtifactRole.POST_METADATA,metadata.encode());var posted=new OriginalOutcome.Posted(request,raw.observedAt(),requestRef,tracking,ref);
   posted.verifyOriginal(prepared.requestBytes(),prepared.trackingBytes(),metadata.encode(),prepared.header(),raw.afterHeader());outcome=posted;
  }else if(raw.kind()==PresentationCapture.Kind.NOT_POSTED)outcome=new OriginalOutcome.NotPosted(request,raw.observedAt(),raw.reason(),List.of(capture,requestRef,before));
  else outcome=new OriginalOutcome.Unknown(request,raw.observedAt(),raw.phase(),raw.reason(),List.of(capture,requestRef,before));
  var ref=archive.preservePresentationOutcome(outcome);require(archive.loadPresentationOutcome(ref).equals(outcome),"automatic outcome archive changed");
  return new PhysicalActionRegistry.DeferredResult(command,new PhysicalActionState(new PreparedAction.MmapRequest(request),prepared.observedAt(),guard,
    raw.kind()==PresentationCapture.Kind.NOT_POSTED?PhysicalActionState.Phase.NOT_POSTED:PhysicalActionState.Phase.UNKNOWN,
    Optional.of(new PhysicalOutcome.MmapOutcome(outcome)),List.of(capture),"actual deferred physical capture; no SUBMITTING event is invented after IO"));
 }
 void rememberAutomatic(ActionReceipt receipt){autoCamera.receipt(projectAutomatic(receipt));}
 private RawJson projectAutomatic(ActionReceipt receipt){
  var n=StrictJson.object().put("canonical_action_id",receipt.command().actionId()).put("canonical_outcome",receipt.outcome().name())
    .put("camera_postcondition_verified",receipt.state() instanceof PhysicalActionState p&&p.phase()==PhysicalActionState.Phase.COMPLETED)
    .put("same_frame_with_gameplay_claim",false).put("continuous_frame_coverage_verified",false);return new RawJson(StrictJson.canonical(n));
 }
 private PhysicalActionRegistry.Observation observeAutomatic(Session same,ActionCommand command,PhysicalActionState state,Instant deadline)throws IOException{
  verifyAutomaticState(command,state,archive());
  var request=((PreparedAction.MmapRequest)state.request()).value();
  if(state.outcome().isEmpty()||!(((PhysicalOutcome.MmapOutcome)state.outcome().orElseThrow()).value() instanceof OriginalOutcome.Posted))
   return new PhysicalActionRegistry.Pending("automatic publication is UNKNOWN; no camera repost",state.evidence());
  var observed=transport(request.owner()).observe(request,deadline);var archive=archive();var ref=archive.preservePresentationObservation(observed);
  if(request.tracking().isPresent()){
   var tracking=archiveTrackingActual(state,transport(request.owner()).sample(request,deadline),archive);
   if(tracking.isPresent())autoCamera.actual(new RawJson(StrictJson.canonical(tracking.orElseThrow().toJson())));
  }
  var evidence=new ArrayList<>(state.evidence());if(evidence.size()>=16)return new PhysicalActionRegistry.Pending("bounded automatic observations retained",evidence);evidence.add(ref);
  if(observed instanceof PresentationObservation.Acknowledged ack&&ack.status()!=PresentationObservation.Status.SUBMITTED&&ack.status()!=PresentationObservation.Status.IDLE
    &&ack.status()!=PresentationObservation.Status.SETTLED&&ack.status()!=PresentationObservation.Status.CANCELLED){
   var result=NativeCameraObserver.decodeResult(archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.RESULT,ack.capture().originalResult()).bytes());
   if(result.actor()==request.frame().actor()&&result.dateRaw()>=request.frame().dateRaw()&&result.dateRaw()<=(long)request.frame().dateRaw()+168){autoCamera.failed(command,result.dateRaw());autoCamera.actual(new RawJson(StrictJson.canonical(ack.toJson())));}
  }
  return automaticComplete(request,evidence,archive)?new PhysicalActionRegistry.Completed(evidence):new PhysicalActionRegistry.Pending("actual automatic result retained; effect not independently complete",evidence);
 }
 static Optional<NativeCameraObserver.TrackingActual> archiveTrackingActual(PhysicalActionState state,PresentationCapture.NativeSample sample,ActionPorts.OutcomeArchive archive){
  var request=((PreparedAction.MmapRequest)state.request()).value();var tracking=NativeCameraObserver.trackingActual(request,sample);
  var first=PresentationCapture.decode(archive.loadMaterial(state.evidence().getFirst()).bytes());
  var actualCapture=new PresentationCapture(first.intent(),first.prepared(),first.kind(),first.phase(),first.reason(),first.observedAt(),first.afterHeader(),Optional.of(sample));
  var raw=RawJson.fullMaterial(actualCapture.encode());var sampleRef=archive.preserveMaterial(raw);require(raw.equals(archive.loadFullMaterial(sampleRef)),"tracking actual archive changed");return tracking;
 }
 private static boolean automaticComplete(PresentationRequest request,List<ExactRef> evidence,ActionPorts.OutcomeArchive archive){
  if(request.mode()==PresentationRequest.Mode.TRACKED_HOTSPOT)return false;
  for(var ref:evidence.subList(1,evidence.size())){var observation=archive.loadPresentationObservation(ref);
   if(observation instanceof PresentationObservation.Acknowledged ack){
    var c=ack.capture();byte[] h=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER,c.originalHeader()).bytes();
    byte[] r=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.RESULT,c.originalResult()).bytes(),d=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.DIAGNOSTICS,c.originalDiagnostics()).bytes();
    ack.verifyOriginal(h,r,d);var actual=NativeCameraObserver.decodeResult(r);
    if(actual.actor()!=request.frame().actor()||actual.dateRaw()<request.frame().dateRaw()||actual.dateRaw()>(long)request.frame().dateRaw()+168)continue;
    if(request.mode()==PresentationRequest.Mode.CANCEL&&ack.status()==PresentationObservation.Status.CANCELLED)return true;
    if(request.mode()==PresentationRequest.Mode.HOTSPOT&&ack.status()==PresentationObservation.Status.SETTLED&&actual.cameraPostconditionVerified())return true;
    if(request.mode()==PresentationRequest.Mode.REALM&&completion(request,List.of(observation),archive))return true;
   }}return false;
 }
 private void verifyAutomaticArchived(WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException{
  var prior=ContinuityActionJournal.lookup(head.state(),receipt.command().actionId(),archive);
  if(prior.isEmpty()){
   boolean issued=receipt.state() instanceof ActionState.IntentDurable&&autoCamera.issued(receipt.command());
   if(!issued)ContinuityActionJournal.requireHistoricalReceipt(context.borrowedSession().head().state(),receipt,archive);
  }else require(prior.orElseThrow().bodySha256().equals(receipt.bodySha256()),"automatic original body changed");
  verifyAutomaticState(receipt.command(),receipt.state(),archive);
 }
 private void verifyAutomaticState(ActionCommand command,ActionState actualState,ActionPorts.OutcomeArchive archive)throws IOException{
  verifyAutomaticCommand(command);
  var g=guard(command);RootGuardEvidence.requireHistory(g,archive,context.borrowedSession());RootGuardEvidence.loadFrame(g,archive,context.frameLoader());
  var parent=archive.loadReceipt(parent(command));require(parent.command().source().equals(command.source())&&parent.command().origin().game().equals(command.origin().game()),"automatic original parent changed");
  if(actualState instanceof ActionState.IntentDurable)return;
  var evidence=actualState instanceof PhysicalActionState p?p.evidence():((ActionState.Unknown)actualState).evidence();
  require(!evidence.isEmpty(),"automatic raw capture is missing");var raw=PresentationCapture.decode(archive.loadMaterial(evidence.getFirst()).bytes());
  require(Arrays.equals(raw.intent().encode(),automaticIntent(command).encode()),"automatic archived capture crossed body");
  if(actualState instanceof ActionState.Unknown unknown){require(unknown.attempt().isEmpty()&&unknown.dispatch().isEmpty()&&raw.kind()==PresentationCapture.Kind.NOT_ATTEMPTED,"automatic no-attempt record changed");return;}
  var state=(PhysicalActionState)actualState;require(state.guard().equals(g)&&state.request() instanceof PreparedAction.MmapRequest,"automatic exact physical guard changed");
  var request=((PreparedAction.MmapRequest)state.request()).value();require(request.preparationEvidence().getFirst().equals(evidence.getFirst())
    &&Arrays.equals(raw.prepared().orElseThrow().canonical(request.preparationEvidence()).encode(),request.encode()),"automatic preparation differs from raw physical capture");
  var outcome=((PhysicalOutcome.MmapOutcome)state.outcome().orElseThrow()).value();require(outcome.equals(archive.loadPresentationOutcome(archive.presentationOutcomeReferenceOf(outcome))),"automatic original outcome changed");
  if(outcome instanceof OriginalOutcome.Posted posted){require(raw.kind()==PresentationCapture.Kind.POSTED,"posted has no actual capture");
   var metadata=archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.POST_METADATA,posted.originalPostEvidence()).bytes();var proof=OriginalOutcome.PostEvidence.decode(metadata);
   posted.verifyOriginal(raw.prepared().orElseThrow().requestBytes(),raw.prepared().orElseThrow().trackingBytes(),metadata,
    archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER,proof.beforeHeader()).bytes(),archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER,proof.afterHeader()).bytes());
  }else require(outcome instanceof OriginalOutcome.NotPosted?raw.kind()==PresentationCapture.Kind.NOT_POSTED:raw.kind()==PresentationCapture.Kind.UNKNOWN,"automatic original return branch changed");
  if(state.phase()==PhysicalActionState.Phase.COMPLETED)require(automaticComplete(request,state.evidence(),archive),"automatic completion lacks independent exact result");
 }
}
