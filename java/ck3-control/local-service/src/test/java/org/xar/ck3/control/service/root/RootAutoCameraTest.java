package org.xar.ck3.control.service.root;
import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.presentation.LatestCameraFollow;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.application.action.PhysicalActionRegistry.*;
import org.xar.ck3.control.contracts.presentation.PresentationRequest.Owner;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.presentation.*;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
/* Software edges;
Root-only null DATA is unqualified. */ class RootAutoCameraTest { @TempDir Path root;
static final OperationKey OP=RootGuiPresentation.OPERATION;
static final Duration SOFTWARE_FRESHNESS=Duration.ofMillis(15_000);
static final Duration OPERATION_BUDGET=Duration.ofSeconds(60);
static final Duration CAMERA_BUDGET=OPERATION_BUDGET;
static ActionWriterIntegrationFixture fixture(Path path)throws IOException,InterruptedException{ var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"fixture-adapter",r->List.of(),r->{throw new AssertionError("no extra READ");});
var fixture=new ActionWriterIntegrationFixture(path,false,reads,List.of( new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map", (c,a,d)->new ActionPorts.Pending("software result unknown",List.of(a.guard().nativeEvidence())),()->{}), new ActionWriterIntegrationFixture.SoftwareActionScenario(OP,"software.camera.presentation", (c,a,d)->{throw new AssertionError();},()->{throw new AssertionError("wrong pipe");})),SOFTWARE_FRESHNESS);
fixture.preserveInitialObservationData();
fixture.bindGuardObserver((head,command)->{try{republishSoftwareFrame(fixture);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new java.io.UncheckedIOException(new IOException("software Native input interrupted",interrupted));}});
return fixture;
}
static Owner owner(ActionWriterIntegrationFixture f)throws Exception{ var id=f.observationIdentity();return new Owner(id.machineId(),id.sessionId(),id.game().pid(), id.game().creationFiletime().value().toString(),PresentationRequest.EXECUTABLE_SHA256,f.command("owner-data").before().frame().episodeRunId(),"1");
}
static ActionCommand camera(ActionCommand base,String id,Owner owner){return camera(base,id,owner,Instant.now());}
static ActionCommand camera(ActionCommand base,String id,Owner owner,Instant createdAt){ var f=base.before().frame();Instant deadline=createdAt.plus(CAMERA_BUDGET);var template=new PresentationIntent(id,createdAt,owner, new PresentationRequest.Frame(f.snapshotId(),f.revision().toString(),f.identity().nativeRevision().toString(),f.identity().player().intValueExact(),f.identity().dateRaw().intValueExact()), PresentationRequest.Mode.REALM,"",Optional.empty(),deadline);
var n=StrictJson.object();n.set("automatic_intent",template.toJson());n.putNull("automatic_guard");n.putNull("parent_receipt");
return new ActionCommand(id,base.before(),base.source(),base.sessionId(),OP,org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService.arguments(n),base.expected(),base.claims(),deadline);
}
static final class Source implements Producer,AutoCloseable{ final ActionWriterIntegrationFixture f;final NativePresentationMemoryFixture.Scenario memory;final LatestCameraFollow worker=new LatestCameraFollow();
final ContinuityWriter writer;final NativeOutcomeArchive archive;
final Map<String,ActionCommand> issued=new ConcurrentHashMap<>();
final Map<String,GuardEvidence> guards=new ConcurrentHashMap<>();
final Set<String> ordinary=new HashSet<>();
final List<String> calls=Collections.synchronizedList(new ArrayList<>());
volatile boolean closed=false;volatile boolean rejectOwner=false;volatile boolean uncaptured=false;volatile boolean captureBeforeRelease=false;
int guardCalls;
final CountDownLatch started=new CountDownLatch(1),release=new CountDownLatch(1);
Source(ActionWriterIntegrationFixture f,NativePresentationMemoryFixture.Scenario m){this(f,m,f.writer,f.archive,Map.of());}
Source(ActionWriterIntegrationFixture f,NativePresentationMemoryFixture.Scenario m,ContinuityWriter writer,NativeOutcomeArchive archive,Map<String,GuardEvidence> restored){this.f=f;memory=m;this.writer=writer;this.archive=archive;guards.putAll(restored);}
@Override public boolean liveCustody(Session same,ActionCommand c)throws IOException{writer.requireSession(same);return !closed&&!worker.unresolvedPhysical()&&c.equals(issued.get(c.actionId()))&&guards.containsKey(c.actionId())&&memory.owner().equals(automaticIntent(c).owner());}
@Override public void committed(String id){issued.remove(id);}
void authorize(ActionCommand c){issued.put(c.actionId(),c);}
void requireIssued(ActionCommand c){StrictJson.require(c.equals(issued.get(c.actionId())),"unissued");}
@Override public boolean automatic(ActionCommand c){return c.operation().equals(OP)&&c.arguments().get("automatic_intent") instanceof OpportunityJson.Obj;}
@Override public PresentationIntent automaticIntent(ActionCommand c){return RootGuiPresentation.automaticIntent(c);}
@Override public GuardEvidence guard(WriterContracts.Head h,ActionCommand c)throws IOException{guardCalls++;requireIssued(c);if(writer!=f.writer)throw new IllegalStateException("cold-camera-guard-reached");try{var g=f.physicalSoftwareGuard(h,c);guards.put(c.actionId(),g);System.out.println("camera-guard-window "+c.actionId()+" observed_at="+g.observedAt()+" valid_until="+g.validUntil()+" caller_deadline="+c.deadline());return g;}finally{System.out.println("camera-guard-budget "+c.actionId()+" "+f.getGuardObservations(c.actionId()));}}
@Override public void verifyDeferredOwner(ActionCommand c){requireIssued(c);if(rejectOwner)throw new IllegalArgumentException("owner revoked");StrictJson.require(memory.owner().equals(automaticIntent(c).owner()),"owner revoked");}
@Override public void queued(Session same,ActionCommand c,GuardEvidence g,PresentationPermit permit)throws IOException{ writer.requireSession(same);guards.put(c.actionId(),g);assertTrue(worker.schedule(new LatestCameraFollow.Work(automaticIntent(c),i->{ calls.add(c.actionId());var captured=captureBeforeRelease?memory.transport().capture(permit,i):null;started.countDown();try{release.await();}catch(InterruptedException e){Thread.currentThread().interrupt();}
if(uncaptured)throw new IllegalStateException("uncaptured");
return captured==null?memory.transport().capture(permit,i):captured;
}),!ordinary.contains(c.actionId())));
}
@Override public List<DeferredResult> collect(Session same)throws IOException{ writer.requireSession(same);var result=new ArrayList<DeferredResult>();
for(var raw:worker.drain()){var c=issued.values().stream().filter(value->automaticIntent(value).equals(raw.intent())).findFirst().orElseThrow();
result.add(RootGuiPresentation.archiveAutomaticOriginal(c,guards.get(c.actionId()),raw,archive.withSession(same)));}
return List.copyOf(result);
}
@Override public void verifyOptional(Session same,ActionReceipt r)throws IOException{ writer.requireSession(same);assertEquals(r,archive.loadReceipt(archive.receiptReferenceOf(r)));verifyArchived(same.head(),r,archive.withSession(same));
}
@Override public void verifyArchived(WriterContracts.Head h,ActionReceipt r,ActionPorts.OutcomeArchive a){ var g=guards.get(r.command().actionId());StrictJson.require(g!=null,"historical original guard unavailable");assertEquals(g.observed(),r.command().before());
if(r.state() instanceof ActionState.IntentDurable)return;
List<ExactRef> evidence;if(r.state() instanceof PhysicalActionState p)evidence=p.evidence();else{var u=assertInstanceOf(ActionState.Unknown.class,r.state());assertTrue(u.attempt().isEmpty()&&u.dispatch().isEmpty());evidence=u.evidence();}
var raw=PresentationCapture.decode(a.loadMaterial(evidence.getFirst()).bytes());assertEquals(automaticIntent(r.command()),raw.intent());
assertEquals(r.state(),RootGuiPresentation.archiveAutomaticOriginal(r.command(),g,raw,a).state());
}
@Override public PreparedAction prepare(Session s,ActionCommand c,String id){throw new AssertionError();}
@Override public PhysicalOutcome post(PhysicalSubmission p,PreparedAction r,Instant d){throw new AssertionError("deferred only");}
@Override public Observation observe(Session s,ActionCommand c,PhysicalActionState p,Instant d){return new Pending("no result",p.evidence());}
@Override public void close(){closed=true;release.countDown();worker.close();}
}
private record Cold(ContinuityWriter writer,Source source,PhysicalActionRegistry registry,ActionCoordinator coordinator) implements AutoCloseable{ @Override public void close(){source.close();} }
private static Cold openCold(ActionWriterIntegrationFixture f, Source old) throws IOException {
    var root = f.root;
    var machine = f.observationIdentity().machineId();
    var layout = new WriterContracts.Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), reference(root.resolve("anchor.json")), machine);
    var store = new org.xar.ck3.control.continuity.writer.ImmutableArtifactStore(
        new org.xar.ck3.control.continuity.writer.ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 16 * 1024 * 1024),
        f.writer.storageGuard());
    var writer = new ContinuityWriter(layout, List.of(f.physicalInputs().source().sourceRef()),
        new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState previous, WriterContracts.Request request) { throw new AssertionError("cold test must not append"); }
            @Override public ContinuityState reduce(ContinuityState previous, WriterContracts.Request request) { throw new AssertionError("cold test must not append"); }
        }, Clock.systemUTC(),
        new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()),
        f.writer.storageGuard());
    var archive = new NativeOutcomeArchive(store, writer);
    var journal = new ContinuityActionJournal(writer, archive);
    var coordinator = new ActionCoordinator("root-action-software-fixture", journal,
        (head, next) -> { throw new AssertionError("cold test must not acquire a new action guard"); },
        next -> { throw new AssertionError("cold test must not prepare a new native request"); },
        (permit, request, deadline) -> { throw new AssertionError("cold test must never resubmit"); },
        (next, attempt, dispatch) -> { throw new AssertionError("execute must return the retained receipt, not reconcile implicitly"); },
        Clock.systemUTC());
    var source = new Source(f, old.memory, writer, archive, Map.copyOf(old.guards));
    var registry = new PhysicalActionRegistry(List.of(new Binding(OP,TransportKind.PRESENTATION_MMAP,List.of(f.physicalInputs().source().sourceRef()),source)));
    coordinator.bindPhysicalActions(registry);
    return new Cold(writer, source, registry,coordinator);
}

private static ExactRef reference(Path path) throws IOException {
    byte[] original = Files.readAllBytes(path);
    return new ExactRef(path.toAbsolutePath().normalize().toString(), original.length, ActionCodec.sha256(original));
}
static void done(Source source)throws Exception{ for(int n=0;n<3000&&(source.worker.running()||source.worker.pending()!=0);n++)Thread.sleep(1);assertFalse(source.worker.running());assertEquals(0,source.worker.pending());
}
static void republishSoftwareFrame(ActionWriterIntegrationFixture f)throws IOException,InterruptedException{
 var transport=f.physicalInputs().transport();var old=transport.currentSnapshot(Instant.now().plusSeconds(5));
 byte[] original=old.originalPacket();f.enqueueSoftwareNativePacket(original);
 Instant deadline=Instant.now().plusSeconds(5);boolean received=false;
 for(int n=0;n<3&&!received;n++){
  var frame=transport.observe(deadline);received=frame.observedAt().isAfter(old.observedAt())&&Arrays.equals(frame.originalPacket(),original);
 }
 assertTrue(received,"actual software Native source did not publish its original packet again");
}
 @Test void expiredCameraCannotReachPhysicalPost()throws Exception{
  try(var f=fixture(root.resolve("expired"));var m=NativePresentationMemoryFixture.create(owner(f),f.archive);var source=new Source(f,m)){
   var registry=new PhysicalActionRegistry(List.of(new Binding(OP,TransportKind.PRESENTATION_MMAP,List.of(f.physicalInputs().source().sourceRef()),source)));
   f.bindPhysicalActions(registry);f.driverAuthority().bindPresentationSource(registry);
   var expired=camera(f.command("expiry-base"),"expired-camera",m.owner(),Instant.now().minus(CAMERA_BUDGET).minusSeconds(15));source.authorize(expired);
   byte[] ledger=f.ledgerBytes();
   assertThrows(IllegalArgumentException.class,()->f.writer.locked(same->registry.deferAutomatic(same,expired)));
   assertEquals(0,m.actualWriteAttempts());assertTrue(source.calls.isEmpty());assertArrayEquals(ledger,f.ledgerBytes());
  }
 }
 @Test void coldOrphanAndUnknownNeverRepost()throws Exception{
  for(boolean uncaptured:List.of(true,false)){
   try(var f=fixture(root.resolve(uncaptured?"cold-orphan":"cold-unknown"));var m=NativePresentationMemoryFixture.create(owner(f),f.archive)){
    var base=f.command("cold-base");var old=camera(base,"old-camera",m.owner());var next=camera(base,"new-camera",m.owner());
    var source=new Source(f,m);ActionReceipt retained;
    try(source){
     var registry=new PhysicalActionRegistry(List.of(new Binding(OP,TransportKind.PRESENTATION_MMAP,List.of(f.physicalInputs().source().sourceRef()),source)));
     f.bindPhysicalActions(registry);f.driverAuthority().bindPresentationSource(registry);
     source.authorize(old);source.uncaptured=uncaptured;if(!uncaptured)m.failAfterPhysicalOdd();
     f.writer.locked(same->{registry.deferAutomatic(same,old);return null;});assertTrue(source.started.await(3,TimeUnit.SECONDS));
     source.release.countDown();done(source);assertTrue(source.worker.unresolvedPhysical());
     f.writer.locked(same->{registry.collectAutomatic(same);return null;});
     retained=f.snapshot().actions().stream().filter(r->r.command().equals(old)).findFirst().orElseThrow();
     if(uncaptured)assertInstanceOf(ActionState.IntentDurable.class,retained.state());
     else{
      var physical=assertInstanceOf(PhysicalActionState.class,retained.state());
      assertInstanceOf(OriginalOutcome.Unknown.class,assertInstanceOf(PhysicalOutcome.MmapOutcome.class,physical.outcome().orElseThrow()).value());
     }
    }
    byte[] ledger=f.ledgerBytes();int writes=m.actualWriteAttempts();
    try(var fresh=openCold(f,source)){
     assertTrue(fresh.source().issued.isEmpty());
     assertEquals(retained,fresh.writer().locked(same->fresh.registry().deferAutomatic(same,old)));
     fresh.source().authorize(next);
     assertThrows(IllegalArgumentException.class,()->fresh.writer().locked(same->fresh.registry().deferAutomatic(same,next)));
     assertEquals(0,fresh.source().guardCalls);assertTrue(fresh.source().calls.isEmpty());
     var ordinaryReached=assertThrows(AssertionError.class,()->fresh.coordinator().execute(base));
     assertEquals("cold test must not acquire a new action guard",ordinaryReached.getMessage());
     assertArrayEquals(ledger,f.ledgerBytes());assertEquals(writes,m.actualWriteAttempts());
    }
   }
  }
 }
 @Test void coldKnownPublicationCanReachFreshGuard()throws Exception{
  for(boolean posted:List.of(true,false)){
   try(var f=fixture(root.resolve(posted?"cold-posted":"cold-not-posted"));var m=NativePresentationMemoryFixture.create(owner(f),f.archive)){
    var base=f.command("known-base");var old=camera(base,"known-old",m.owner());var next=camera(base,"known-next",m.owner());
    var source=new Source(f,m);
    try(source){
     var registry=new PhysicalActionRegistry(List.of(new Binding(OP,TransportKind.PRESENTATION_MMAP,List.of(f.physicalInputs().source().sourceRef()),source)));
     f.bindPhysicalActions(registry);f.driverAuthority().bindPresentationSource(registry);
     source.authorize(old);source.rejectOwner=!posted;
     f.writer.locked(same->{registry.deferAutomatic(same,old);return null;});assertTrue(source.started.await(3,TimeUnit.SECONDS));
     source.release.countDown();done(source);f.writer.locked(same->{registry.collectAutomatic(same);return null;});
     var retained=f.snapshot().actions().stream().filter(r->r.command().equals(old)).findFirst().orElseThrow();
     var physical=assertInstanceOf(PhysicalActionState.class,retained.state());
     var outcome=assertInstanceOf(PhysicalOutcome.MmapOutcome.class,physical.outcome().orElseThrow()).value();
     if(posted){assertInstanceOf(OriginalOutcome.Posted.class,outcome);assertEquals(PhysicalActionState.Phase.UNKNOWN,physical.phase());}
     else assertInstanceOf(OriginalOutcome.NotPosted.class,outcome);
    }
    byte[] ledger=f.ledgerBytes();int writes=m.actualWriteAttempts();
    try(var fresh=openCold(f,source)){
     fresh.source().authorize(next);
     var denied=assertThrows(IllegalStateException.class,()->fresh.writer().locked(same->fresh.registry().deferAutomatic(same,next)));
     assertEquals("cold-camera-guard-reached",denied.getMessage());assertEquals(1,fresh.source().guardCalls);
     assertTrue(fresh.source().calls.isEmpty());assertArrayEquals(ledger,f.ledgerBytes());assertEquals(writes,m.actualWriteAttempts());
     var retained=f.snapshot().actions().stream().filter(r->r.command().equals(old)).findFirst().orElseThrow();
     var physical=assertInstanceOf(PhysicalActionState.class,retained.state());
     Files.write(Path.of(physical.evidence().getFirst().path()),new byte[]{0});
     fresh.source().guardCalls=0;
     assertThrows(RuntimeException.class,()->fresh.writer().locked(same->fresh.registry().deferAutomatic(same,next)));
     assertEquals(0,fresh.source().guardCalls);assertArrayEquals(ledger,f.ledgerBytes());assertEquals(writes,m.actualWriteAttempts());
    }
   }
  }
 }
 @Test void liveCoalescingArchivesDisplacedOrdinary()throws Exception{
  try(var f=fixture(root.resolve("coalescing"));var m=NativePresentationMemoryFixture.create(owner(f),f.archive);var s=new Source(f,m)){
   var registry=new PhysicalActionRegistry(List.of(new Binding(OP,TransportKind.PRESENTATION_MMAP,List.of(f.physicalInputs().source().sourceRef()),s)));
   f.bindPhysicalActions(registry);f.driverAuthority().bindPresentationSource(registry);
   var base=f.command("running");var c1=camera(base,"running",m.owner());s.authorize(c1);
   f.writer.locked(same->{registry.deferAutomatic(same,c1);return null;});assertTrue(s.started.await(3,TimeUnit.SECONDS));
   var c2=camera(base,"ordinary2",m.owner());s.authorize(c2);s.ordinary.add(c2.actionId());
   f.writer.locked(same->{registry.deferAutomatic(same,c2);return null;});
   var c3=camera(base,"urgent3",m.owner());s.authorize(c3);
   f.writer.locked(same->{registry.deferAutomatic(same,c3);return null;});
   assertEquals(1,s.worker.pending());
   f.writer.locked(same->{registry.collectAutomatic(same);return null;});
   var state2=assertInstanceOf(ActionState.Unknown.class,f.snapshot().actions().stream().filter(r->r.command().equals(c2)).findFirst().orElseThrow().state());
   assertEquals(Optional.empty(),state2.attempt());assertEquals(Optional.empty(),state2.dispatch());
   assertEquals(PresentationCapture.Kind.NOT_ATTEMPTED,PresentationCapture.decode(f.archive.loadMaterial(state2.evidence().getFirst()).bytes()).kind());
   s.release.countDown();done(s);
   f.writer.locked(same->{registry.collectAutomatic(same);return null;});
   assertEquals(List.of(c1.actionId(),c3.actionId()),s.calls);
   assertFalse(s.calls.contains(c2.actionId()));
   republishSoftwareFrame(f);var next=camera(f.command("after-displaced-base"),"after-displaced",m.owner());
   byte[] ledger=f.ledgerBytes();int writes=m.actualWriteAttempts();
   try(var fresh=openCold(f,s)){
    fresh.source().authorize(next);
    var reached=assertThrows(IllegalStateException.class,()->fresh.writer().locked(same->fresh.registry().deferAutomatic(same,next)));
    assertEquals("cold-camera-guard-reached",reached.getMessage());assertEquals(1,fresh.source().guardCalls);
    assertArrayEquals(ledger,f.ledgerBytes());assertEquals(writes,m.actualWriteAttempts());
   }
  }
 }
 @Test void actualAutoTrackingSampleReachesOriginalArchiveConsumer()throws Exception{
  try(var f=fixture(root.resolve("tracking"));var m=NativePresentationMemoryFixture.create(owner(f),f.archive);var s=new Source(f,m)){
   var registry=new PhysicalActionRegistry(List.of(new Binding(OP,TransportKind.PRESENTATION_MMAP,List.of(f.physicalInputs().source().sourceRef()),s)));
   f.bindPhysicalActions(registry);f.driverAuthority().bindPresentationSource(registry);
   var base=f.command("tracking-base");var c=camera(base,"tracking",m.owner());
   var fields=org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService.argumentFields(c);
   var ti=PresentationIntent.fromJson(fields.get("automatic_intent"));int date=ti.frame().dateRaw();
   var scope=new PresentationIntent.Scope("9007199254740993",7,date,date+24,List.of(new PresentationRequest.Province(9,"b_test")));
   fields.set("automatic_intent",new PresentationIntent(ti.requestId(),ti.createdAt(),ti.owner(),ti.frame(),PresentationRequest.Mode.TRACKED_HOTSPOT,"",Optional.of(scope),ti.deadline()).toJson());
   var command=new ActionCommand(c.actionId(),c.before(),c.source(),c.sessionId(),c.operation(),org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService.arguments(fields),c.expected(),c.claims(),c.deadline());
   s.authorize(command);m.publishTrackingCapability(false);
   f.writer.locked(same->{registry.deferAutomatic(same,command);return null;});assertTrue(s.started.await(3,TimeUnit.SECONDS));s.release.countDown();done(s);
   f.writer.locked(same->{registry.collectAutomatic(same);return null;});
   var state=assertInstanceOf(PhysicalActionState.class,f.snapshot().actions().getLast().state());
   assertInstanceOf(OriginalOutcome.Posted.class,((PhysicalOutcome.MmapOutcome)state.outcome().orElseThrow()).value());
   var request=((PreparedAction.MmapRequest)state.request()).value();m.publishTrackingResult(request,false);
   int writes=m.actualWriteAttempts();long sequence=f.sequence();
   f.writer.locked(same->{
    var archive=f.archive.withSession(same);var sample=m.transport().sample(request,command.deadline());
    var actual=RootGuiPresentation.archiveTrackingActual(state,sample,archive).orElseThrow();
    assertTrue(actual.active());assertEquals(date+1,actual.dateRaw());assertEquals("9007199254740993",actual.scopeGeneration());
    assertFalse(actual.toJson().get("camera_postcondition_verified").booleanValue());
    var first=PresentationCapture.decode(archive.loadMaterial(state.evidence().getFirst()).bytes());
    var captured=new PresentationCapture(first.intent(),first.prepared(),first.kind(),first.phase(),first.reason(),first.observedAt(),first.afterHeader(),Optional.of(sample));
    var material=RawJson.fullMaterial(captured.encode());assertEquals(material,archive.loadFullMaterial(archive.materialReferenceOf(material)));
    return null;
   });
   assertEquals(writes,m.actualWriteAttempts());assertEquals(sequence,f.sequence());assertEquals(0,f.nativeActionWrites());
  }
 }
@Test void pendingAndUnknownAreOptionalButNeverRepost()throws Exception{ for(boolean pending:List.of(true,false)){ try(var f=fixture(root.resolve(pending?"pending":"unknown"));var m=NativePresentationMemoryFixture.create(owner(f),f.archive);var s=new Source(f,m)){ var registry=new PhysicalActionRegistry(List.of(new Binding(OP,TransportKind.PRESENTATION_MMAP,List.of(f.physicalInputs().source().sourceRef()),s)));
f.bindPhysicalActions(registry);f.driverAuthority().bindPresentationSource(registry);
var basis=f.command("camera-basis");var another=f.command("another-business");var camera=camera(basis,"automatic",m.owner());var forged=camera(basis,"forged",m.owner());s.authorize(camera);s.captureBeforeRelease=true;m.failAfterPhysicalOdd();
f.writer.locked(same->{registry.deferAutomatic(same,camera);return null;});assertTrue(s.started.await(3,TimeUnit.SECONDS));
if(!pending){s.release.countDown();done(s);f.writer.locked(same->{registry.collectAutomatic(same);return null;});}
republishSoftwareFrame(f);
var business=f.command("ordinary",OPERATION_BUDGET);ActionReceipt original;try{original=f.coordinator.execute(business);}finally{System.out.println("ordinary-guard-budget "+f.getGuardObservations("ordinary"));}assertEquals(ActionReceipt.Outcome.UNRESOLVED,original.outcome());
s.release.countDown();done(s);f.writer.locked(same->{registry.collectAutomatic(same);return null;});
var retained=f.snapshot().actions().stream().filter(r->r.command().equals(camera)).findFirst().orElseThrow();
assertEquals(PhysicalActionState.Phase.UNKNOWN,assertInstanceOf(PhysicalActionState.class,retained.state()).phase());
assertEquals(1,m.actualSuccessfulOddClaims());int writes=m.actualWriteAttempts();byte[] ledger=f.ledgerBytes();
assertEquals(retained,f.reopenAndReturnExisting(camera));assertArrayEquals(ledger,f.ledgerBytes());
f.writer.locked(same->{assertEquals(retained,registry.deferAutomatic(same,camera));registry.collectAutomatic(same);return null;});
assertEquals(writes,m.actualWriteAttempts());assertEquals(1,f.nativeActionWrites());
assertThrows(IllegalArgumentException.class,()->f.writer.locked(same->{registry.deferAutomatic(same,forged);return null;}));
assertThrows(IllegalArgumentException.class,()->f.coordinator.execute(another));
}
}
}
}
