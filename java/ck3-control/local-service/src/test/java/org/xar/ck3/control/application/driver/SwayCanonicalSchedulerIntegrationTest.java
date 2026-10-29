package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.sway.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.vanilla.schemesway.*;

/** Software native producer + real full Driver assembler + actual immutable store/writer/event replay.
 * The physical Game/session and guarded wire are synthetic. This is never a live-Game qualification. */
final class SwayCanonicalSchedulerIntegrationTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z"), DEADLINE = Instant.parse("2030-01-01T00:00:00Z");
    private static final String MACHINE = "test-machine", ROOT_ID = "software-campaign-root/v1";
    private static final long ACTOR = 50331649L, TARGET = 50331650L;
    private static final OperationKey SOFTWARE_FOLLOWING = new OperationKey("software-following-gameplay");
    @TempDir Path root;
    @Test void actualInstalledJournalFamiliesPreserveNonzeroUint64CursorThroughNativeArchiveAndPublicConsumers() throws Exception {
        Fixture fixture=new Fixture(root);fixture.journal.locked(locked->{
            try {
                var same=locked.writerSession();var archive=fixture.archive.withSession(same);var frame=fixture.frame(archive);
                var definitions=new SwayRootReads(new SwayRootReads.Sources(fixture.source,fixture.source,fixture.source));
                var catalog=new RootReadContractCatalog(List.of(),definitions.families());definitions.attach(catalog);
                var subject=new org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject(ACTOR,TARGET,0x0100_000bL,1);
                var identity=new org.xar.ck3.control.g2.m6.G2M6Contracts.Identity("software-real-origin-in-fixture",ACTOR,TARGET,subject.schemeInstanceId(),1);
                var cursor=new BigInteger("9007199254740992");String head=same.head().digest();
                for(var kind:List.of(SwayObservationReads.Kind.EXECUTION,SwayObservationReads.Kind.TERMINATION)) {
                    var query=new SwayObservationReads.JournalQuery(kind,subject,cursor);var definition=definitions.journal(query);
                    assertSame(definition,definitions.journal(query));assertTrue(catalog.containsIdentity(definition));
                    var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),definition.operation(),SwayObservationReads.arguments(query),DEADLINE);
                    var nativeRequest=definition.prepare(request,"software-journal-read");
                    var outgoing=org.xar.ck3.control.nativebridge.NativeWire.decodeExecuteRequest(org.xar.ck3.control.nativebridge.NativeWire.execute("software-journal-read",nativeRequest.step(),frame.identity().frame().identity().nativeRevision(),nativeRequest.additionalFields().bytes()));
                    var fields=StrictJson.parse(outgoing.normalizedAdditionalFields().value());assertEquals(cursor,fields.get("after_sequence").bigIntegerValue());assertTrue(fields.get("after_sequence").isIntegralNumber());
                    var packet=journalPlane(kind,frame,subject,cursor);var original=journalReceipt(fixture,archive,frame,definition,request,packet);
                    archive.preserve(original.original());var ref=archive.preserveRead(original);var cold=archive.loadRead(ref);assertEquals(ref,archive.readReferenceOf(cold));
                    assertArrayEquals(original.original().originalFrame().bytes(),cold.original().originalFrame().bytes());
                    var value=definition.decode(cold);assertEquals(cursor,value.afterSequence());assertEquals(subject,value.subject());
                    var publicValue=StrictJson.parse(SwayPublicCodec.publicNormalized(value).bytes());assertEquals(cursor.toString(),publicValue.get("after_sequence").textValue());
                    assertEquals(cursor.add(BigInteger.ONE).toString(),publicValue.at("/records/0/sequence").textValue());
                    assertFalse(publicValue.has("action_id"));assertFalse(publicValue.at("/records/0").has("action_id"));
                    var ordinary=SwayObservationReads.decode(cold,kind,identity);assertArrayEquals(value.normalized().bytes(),ordinary.normalized().bytes());assertEquals(Optional.of(cursor),ordinary.afterSequence());
                    var requestRoundTrip=SwayPublicCodec.decodeJournal(kind,SwayPublicCodec.encodeJournalRequest(new SwayPublicCodec.JournalRequest(kind,frame.identity().frame().revision(),TARGET,subject.schemeInstanceId(),cursor)));
                    assertEquals(cursor,requestRoundTrip.afterSequence());
                    for(String defect:List.of("cursor","at-cursor","row-identity","missing-row-field","actor","legacy-build","alias","float-sequence")) {
                        var invalid=journalPlane(kind,frame,subject,cursor);var body=(ObjectNode)invalid.at("/result/"+(kind==SwayObservationReads.Kind.EXECUTION?"sway_completion_execution":"sway_completion_termination"));var row=(ObjectNode)body.at("/records/0");
                        switch(defect) {
                            case "cursor"->body.put("after_sequence",cursor.subtract(BigInteger.ONE));
                            case "at-cursor"->row.put("sequence",cursor);
                            case "row-identity"->row.put("scheme_instance_generation",2);
                            case "missing-row-field"->row.remove("target_character_id");
                            case "actor"->body.put("actor_character_id",ACTOR+7);
                            case "legacy-build"->((ObjectNode)invalid.get("result")).put("build_version","1.20.0.2");
                            case "alias"->body.put("last_sequence",cursor);
                            case "float-sequence"->row.put("sequence",2.0);
                            default->throw new AssertionError(defect);
                        }
                        var rejected=journalReceipt(fixture,archive,frame,definition,request,invalid);assertThrows(IllegalArgumentException.class,()->definition.decode(rejected),kind+":"+defect);
                    }
                    var ordinaryQuery=new SwayObservationReads.Query(kind,identity,Optional.of(cursor));var ordinaryContract=definitions.observation(ordinaryQuery);
                    var ordinaryRequest=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),ordinaryContract.operation(),SwayObservationReads.arguments(ordinaryQuery),DEADLINE);
                    var originalOrdinary=journalReceipt(fixture,archive,frame,ordinaryContract,ordinaryRequest,packet);assertEquals(Optional.of(cursor),ordinaryContract.decode(originalOrdinary).afterSequence());
                    var zeroPacket=journalPlane(kind,frame,subject,BigInteger.ZERO);var oldArgs=StrictJson.object();oldArgs.put("target_character_id",TARGET);oldArgs.put("scheme_instance_id",subject.schemeInstanceId());
                    var oldRequest=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),ordinaryContract.operation(),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(oldArgs)),"historical explicit cursor0 arguments"),DEADLINE);
                    var oldGuard=fixture.guard(frame,ordinaryContract.operation(),archive);var guarded=new PlanningReadGuard(oldGuard,true,true,true,frame.fullBindingSha256());
                    var old=new PlanningReadReceipt(oldRequest,"sway-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"-actual4:"+identity.actionId(),"software-journal-read",guarded,guarded,acknowledgement(zeroPacket));
                    assertEquals(Optional.of(BigInteger.ZERO),SwayObservationReads.decode(old,kind,identity).afterSequence());
                    assertThrows(IllegalArgumentException.class,()->SwayObservationReads.decode(new PlanningReadReceipt(oldRequest,ordinaryContract.contractId(),old.requestId(),guarded,guarded,old.original()),kind,identity),"v2 cannot silently inherit missing v1 cursor");
                }
                assertEquals(head,same.head().digest(),"journal archive and public formatting cannot submit or advance any action");return true;
            }catch(Exception failure){throw new RuntimeException(failure);}
        });
    }
    private static PlanningReadReceipt journalReceipt(Fixture fixture,ActionPorts.OutcomeArchive archive,DriverObservationAssembler.Complete frame,
            ReadContract<?> definition,PlanningReadRequest request,ObjectNode packet)throws java.io.IOException {
        var guard=fixture.guard(frame,definition.operation(),archive);var readGuard=new PlanningReadGuard(guard,true,true,true,frame.fullBindingSha256());
        return new PlanningReadReceipt(request,definition.contractId(),"software-journal-read",readGuard,readGuard,acknowledgement(packet));
    }
    /** Explicit current-build software packet, never an edited historical capture or native/Game qualification. */
    private static ObjectNode journalPlane(SwayObservationReads.Kind kind,DriverObservationAssembler.Complete frame,
            org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject subject,BigInteger cursor) {
        boolean execution=kind==SwayObservationReads.Kind.EXECUTION;var packet=StrictJson.object();packet.put("type","command_result");packet.put("protocol_version",1);packet.put("request_id","software-journal-read");packet.put("ok",true);
        var result=packet.putObject("result");result.put("step",kind.step());result.put("accepted",true);result.put("status","available");result.put("private_build",true);result.put("read_only",true);result.put("advertised",false);result.put("backend_id","native-headless");
        result.put("snapshot_revision",frame.identity().frame().identity().nativeRevision());result.put("date_raw",frame.identity().frame().identity().dateRaw());result.put("build_version",SwayNativeWire.BUILD);result.put("executable_sha256",SwayNativeWire.EXE);
        var body=result.putObject(execution?"sway_completion_execution":"sway_completion_termination");body.put("schema",execution?"xar.ck3.sway-completion-execution.v1":"xar.ck3.sway-completion-termination.v1");
        body.put("available",true);body.put("unavailable_reason","");body.put("read_only",true);body.put("observer_attached",true);body.put("actor_character_id",subject.actorCharacterId());body.put("target_character_id",subject.targetCharacterId());body.put("scheme_instance_id",subject.schemeInstanceId());
        body.put("after_sequence",cursor);body.put("earliest_sequence",cursor.add(BigInteger.ONE));body.put("latest_sequence",cursor.add(BigInteger.ONE));body.put("retention_gap",false);body.put("material_effect_observed",false);
        if(execution)body.put("native_terminal_state_observed",false);else body.put("session_records_only",true);
        var row=body.putArray("records").addObject();row.put("sequence",cursor.add(BigInteger.ONE));row.put("date_raw",frame.identity().frame().identity().dateRaw());row.put("actor_character_id",subject.actorCharacterId());row.put("target_character_id",subject.targetCharacterId());row.put("scheme_instance_id",subject.schemeInstanceId());row.put("scheme_instance_generation",subject.schemeInstanceGeneration());row.put("material_effect_observed",false);
        if(execution) {
            row.put("source_branch","hidden_phase_success_source");row.put("stock_event","sway_outcome.0001");row.put("phase_result","success");row.put("executing_input_observed",true);row.put("exact_scope_join_ready",true);row.put("message_enqueue_observed",false);row.put("native_terminal_state_observed",false);
        }else {
            row.put("source_class","end_scheme_command_execute");row.put("input_root_scope_kind",4);row.put("executing_source_observed",true);row.put("pre_status",0);row.put("pre_owner",subject.actorCharacterId());row.put("post_read_succeeded",true);row.put("post_instance_present",true);row.put("post_storage_slot_reused",false);row.put("post_exact_instance_join_ready",true);row.put("post_status_observed",true);row.put("post_status",1);row.put("post_owner",subject.actorCharacterId());row.put("native_terminal_state_observed",true);row.put("native_terminal_transition_observed",true);row.putNull("specific_invalidation_reason");
        }
        return packet;
    }
    @Test void actualZeroChildPublicationReplaysBeforeSharedSchedulerReceiptClassificationAndColdRoundtrip() throws Exception {
        Fixture fixture = new Fixture(root);
        fixture.journal.locked(locked -> {
            try {
                var session = locked.writerSession(); var archive = fixture.archive.withSession(session); var frame = fixture.frame(archive);
                var rootRead = fixture.rootRead(frame, archive); var rootRef = archive.preserveRead(rootRead);
                ExactRef original = write(root.resolve("state/active-scheme-sway-formal-private-v1.json"), bytes("{\"schema\":\"xar.ck3.active-scheme-sway-formal-private.v1\",\"pending\":null,\"resolved\":null}"));
                fixture.domain.importOriginal(session, original, archive.preserveMaterial(new RawJson(Files.readAllBytes(Path.of(original.path())))), rootRef, Optional.empty());
                var request = new PlanningRequest(frame.identity(), frame.source(), frame.sessionId(), DEADLINE,
                        new PlanningObservation(frame.semantic(), List.of(), Set.of(OrdinarySwayPolicy.OPERATION), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
                var inputs = SwaySessionInputs.project(fixture.domain.load(session).ledger(), request.before());
                var policy = new OrdinarySwayPolicy(fixture.source, ignored -> OrdinarySwayPolicy.project(request.before(), OrdinarySwayReadSource.originalResult(rootRead), new OrdinarySwayService.Capabilities(true,true,true), () -> Optional.of(inputs)), SwayOrdinaryComposite::expected);
                var prior = new ActionCommand("software-earlier-life", request.before(), request.source(), request.sessionId(), new OperationKey("life-advance"), new OpportunityJson.Obj(Map.of()),
                        new ProposalLifecycle.ExpectedPostcondition(1, request.before(), request.source(), "software-prior/v1", List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("software.prior"),true))), new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()), DEADLINE);
                var draft = new OrdinaryPolicy.Draft("software-prior", "life-advance", "explicit software earlier selection", OrdinaryPolicy.Kind.ORDINARY, Optional.of(prior), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new OpportunityJson.Obj(Map.of()));
                var parent = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, draft)).draft().command().orElseThrow();
                assertEquals(OrdinarySwaySchedule.Job.COMPLETE_NO_RELATION, OrdinarySwayPolicy.restoreStaged(parent).decision().job().orElseThrow());
                var guard = fixture.guard(frame, parent.operation(), archive); fixture.currentGuard.set(guard);
                locked.append(parent, ActionCodec.bodySha256(parent), new ActionState.IntentDurable());
                var retained = new CompositeExecution(SwayOrdinaryComposite.HANDLER, NOW, guard, List.of()); locked.append(parent, ActionCodec.bodySha256(parent), new ActionState.CompositeRunning(retained));
                var before = fixture.domain.load(session); ExactRef stage = archive.preserveMaterial(new RawJson(SwaySchedulerReplay.encodeStage(new SwaySchedulerReplay.Stage(parent, before.original().reference().payload(), rootRef))));
                fixture.domain.commit(session, new SwayFormalState.StageRecorded(stage), new SwayTransitionCodec.Proofs(List.of(rootRef), Optional.empty(), Optional.empty(), List.of(stage)));
                final SwayCanonicalDomain.Publication[] saved = new SwayCanonicalDomain.Publication[1]; final ExactRef[] originalRun = new ExactRef[1];
                var result = new OrdinarySwayService().execute(OrdinarySwayPolicy.restoreStaged(parent), new OrdinarySwayService.ExecutionPort() {
                    @Override public Optional<OrdinarySwayService.Inputs> loadInputs() { return Optional.of(inputs); }
                    @Override public OrdinarySwayService.FormalResult queryAndConsume(OrdinarySwaySchedule.Frame ignored,long target) { throw new AssertionError("known empty frontier cannot submit Start"); }
                    @Override public OrdinarySwayService.LifecycleResult observeLifecycle(OrdinarySwaySchedule.Frame ignored) { throw new AssertionError("known empty frontier cannot invent lifecycle"); }
                    @Override public Optional<String> saveScheduler(OrdinarySwaySchedule.State state) {
                        var local = new OrdinarySwayService.LocalResult(OrdinarySwayService.LocalStatus.KNOWN_EMPTY_RELATION_FRONTIER, Optional.empty());
                        var run = new SwaySchedulerReplay.Run(stage,local,List.of(),Optional.empty()); originalRun[0] = archive.preserveMaterial(new RawJson(SwaySchedulerReplay.encodeRun(run)));
                        try { saved[0] = fixture.domain.commitPublication(session,new SwayFormalState.SchedulerSaved(state,originalRun[0]),new SwayTransitionCodec.Proofs(List.of(),Optional.empty(),Optional.empty(),List.of(stage,originalRun[0]))); }
                        catch(java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); } return Optional.empty();
                    }
                    @Override public OrdinarySwayService.OrdinaryContinuation executeFreshOrdinary() { var value = org.xar.ck3.control.contracts.projection.ProjectionJson.object(bytes("{\"status\":\"root_fresh_fullplan_required\"}"),256); return new OrdinarySwayService.OrdinaryContinuation(value,value); }
                });
                assertInstanceOf(OrdinarySwayService.Continued.class,result);
                var proof = new SwaySchedulerCompletion(parent.actionId(),ActionCodec.bodySha256(parent),originalRun[0],saved[0].witness(),NativeEffectEvidence.basis(frame),List.of(rootRef),List.of(),Optional.empty(),Optional.empty(),SwaySchedulerCompletion.Continuation.FRESH_FULL_PLAN_REQUIRED,new SwaySchedulerCompletion.NoNewBusiness());
                fixture.domain.verifySchedulerCompleted(session,parent,retained,proof);
                var publication = fixture.domain.savedScheduler(session,parent).orElseThrow(); assertEquals(originalRun[0],publication.originalRun()); assertEquals(saved[0].witness(),publication.witness());
                var observed = new ActionPorts.SwaySchedulerObserved(proof); var receipt = locked.append(parent,ActionCodec.bodySha256(parent),new ActionState.CompositeSettled(retained,new ActionState.SwaySchedulerCompleted(observed.proof())));
                assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,receipt.outcome()); assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
                byte[] wire = ActionReceiptCodec.encodeReceipt(receipt,archive); var cold = ActionReceiptCodec.decodeReceipt(wire,archive); assertArrayEquals(wire,ActionReceiptCodec.encodeReceipt(cold,archive)); assertFalse(cold.visibleGameplay()); assertFalse(cold.eligibleAdvance());
                fixture.domain.verifySchedulerCompleted(session,parent,retained,((ActionState.SwaySchedulerCompleted)((ActionState.CompositeSettled)cold.state()).settlement()).proof());
                var changed = new SwaySchedulerCompletion(parent.actionId(),ActionCodec.bodySha256(parent),originalRun[0],saved[0].witness(),NativeEffectEvidence.basis(frame),List.of(rootRef),List.of(),Optional.empty(),Optional.empty(),SwaySchedulerCompletion.Continuation.FRESH_FULL_PLAN_REQUIRED,new SwaySchedulerCompletion.NewStartConfirmed("sway-fake","a".repeat(64)));
                assertThrows(IllegalArgumentException.class,()->fixture.domain.verifySchedulerCompleted(session,parent,retained,changed));
                ObjectNode corrupt = (ObjectNode)StrictJson.parse(proof.encode(),SwaySchedulerCompletionCodec.MAX_BYTES); corrupt.put("unexpected_alias",false); assertThrows(IllegalArgumentException.class,()->SwaySchedulerCompletionCodec.decodeRecorded(StrictJson.canonical(corrupt,SwaySchedulerCompletionCodec.MAX_BYTES)));
                var wrong = new SwayCanonicalDomain.PublicationWitness(saved[0].witness().event(),saved[0].witness().predecessor(),saved[0].witness().result(),saved[0].witness().producerInput(),saved[0].witness().sequence(),saved[0].witness().eventIdentity(),"f".repeat(64));
                var wrongProof = new SwaySchedulerCompletion(parent.actionId(),ActionCodec.bodySha256(parent),originalRun[0],wrong,NativeEffectEvidence.basis(frame),List.of(rootRef),List.of(),Optional.empty(),Optional.empty(),SwaySchedulerCompletion.Continuation.FRESH_FULL_PLAN_REQUIRED,new SwaySchedulerCompletion.NoNewBusiness());
                assertThrows(IllegalArgumentException.class,()->fixture.domain.verifySchedulerCompleted(session,parent,retained,wrongProof)); return null;
            } catch(Exception failure) { throw new RuntimeException(failure); }
        });
    }

    @Test void actualStartRunsOneCoordinatorPendingHookNativeReceiptIndependentRowAndSchedulerBeforeVisibleParent() throws Exception {
        actualStart(false);
    }
    @Test void actualStartSettlesOneVisibleCycleThroughTheRealSemanticVerifierWithoutSavedDayCredit() throws Exception {
        actualStart(true);
    }
    @Test void actualSelectedFinishBuildsStopFromThreeIndependentReadsThenUnknownOnlyReconcilesOriginal() throws Exception {
        actualStart(true,true);
    }
    @Test void ordinaryGenerationZeroEarlyBaselineAndFirstNamedGainSurviveFailedEndReaderThenConsumeNaturalTerminal() throws Exception {
        actualStart(true,false,true,false);
    }
    @Test void failedEarlyNamedBaselineKeepsConfirmedStartAndNeverReplaysItsNativeWrite() throws Exception {
        actualStart(true,false,false,true);
    }
    @Test void actualEmptyExecutorArchivesFreshFullPlannerSelectionThenSettlesParentWithoutDispatchingContinuation() throws Exception {
        Fixture fixture = new Fixture(root); var captures = new java.util.concurrent.atomic.AtomicInteger(); var dispatches = new java.util.concurrent.atomic.AtomicInteger();
        fixture.journal.locked(locked -> {
            try {
                var session = locked.writerSession(); var archive = fixture.archive.withSession(session); var before = fixture.frame(archive,9); var after = fixture.frame(archive,10);
                var rootDefinition = new ReadContract<OpportunityJson.Obj>(ROOT_ID,OrdinarySwayReadSource.ROOT,Optional.empty(),"software-root-private",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,fixture.source,
                        request -> new NativeRequest(request.operation().value(),Optional.empty(),new RawJson(bytes("{}"))),OrdinarySwayReadSource::originalResult);
                var nativeReads = new SwayRootReads(new SwayRootReads.Sources(fixture.source,fixture.source,fixture.source));
                var readCatalog = new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(rootDefinition,fixture.source)),nativeReads.families()); nativeReads.attach(readCatalog);
                PlanningReadPort readPort = new PlanningReadPort() {
                    @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> definition,PlanningReadRequest request) { assertSame(session,same); return read(definition,request); }
                    @Override public <T> PlanningReadResult<T> read(ReadContract<T> definition,PlanningReadRequest request) {
                        try {
                            assertEquals(OrdinarySwayReadSource.ROOT,definition.operation(),"known empty relation frontier uses no native target query");
                            var frame = request.before().equals(before.identity()) ? before : after; var original = fixture.rootRead(frame,archive);
                            var ref = archive.preserveRead(original); return new PlanningReadResult.Known<>(definition.decode(original),original,ref);
                        } catch (Exception failure) { throw new RuntimeException(failure); }
                    }
                };
                var registered = new SwayActionLifecycle.RegisteredReads() {
                    @Override public ReadContract<SwayNativeWire.TargetRead> target(long target) { return nativeReads.target(target); }
                    @Override public ReadContract<SwayNativeWire.AppliedReceipt> receipt(long target,String action,BigInteger epoch) { return nativeReads.receipt(target,action,epoch); }
                    @Override public ReadContract<SwayObservationReads.Plane> plane(SwayObservationReads.Kind kind,org.xar.ck3.control.g2.m6.G2M6Contracts.Identity identity) { return nativeReads.plane(kind,identity); }
                };
                var originalRoot = fixture.rootRead(before,archive); var rootRef = archive.preserveRead(originalRoot);
                ExactRef original = write(root.resolve("state/active-scheme-sway-formal-private-v1.json"),bytes("{\"schema\":\"xar.ck3.active-scheme-sway-formal-private.v1\",\"pending\":null,\"resolved\":null}"));
                fixture.domain.importOriginal(session,original,archive.preserveMaterial(new RawJson(Files.readAllBytes(Path.of(original.path())))),rootRef,Optional.empty());
                java.util.function.Function<DriverObservationAssembler.Complete,PlanningRequest> request = frame -> new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),DEADLINE,
                        new PlanningObservation(frame.semantic(),List.of(),Set.of(OrdinarySwayPolicy.OPERATION,new OperationKey("life-advance")),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
                var lifecycle = new SwayActionLifecycle(fixture.domain,fixture.archive,readPort,registered,fixture::same,
                        command -> { throw new AssertionError("known empty frontier cannot create native action lifecycle"); },new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
                var nativeActions = new SwayRootActions(lifecycle,new SwayRootActions.Sources(fixture.source,fixture.source,fixture.source)); var inventory = new AtomicReference<RootExecutableBindings>();
                var executor = new SwayOrdinaryExecutor(fixture.domain,fixture.archive,readPort,rootDefinition,registered,nativeActions,inventory::get,fixture::same,
                        parent -> { var frame = captures.getAndIncrement()==0 ? before : after; return new SwayOrdinaryExecutor.Fresh(request.apply(frame),NativeEffectEvidence.basis(frame)); },
                        parent -> { throw new AssertionError("live completion does not use cold authority"); },
                        deadline -> { throw new java.io.IOException("software fixture cannot mint RestoreBinding"); },()->softwareFullPlanner(fixture.source));
                var composite = new SwayOrdinaryComposite(executor,fixture.domain,fixture::same); var binding = new RootExecutableBindings.CompositeBinding(composite,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),fixture.source,fixture.source);
                var bindings = RootExecutableBindings.freeze(List.of(nativeActions.selectedStop()),readCatalog,List.of(binding),List.of(nativeActions.selectedStopReplay(),composite.recorded(fixture.source)),List.of(nativeActions.startFamily()),32); inventory.set(bindings);
                fixture.guardFactory.set(command -> fixture.guard(before,command.operation(),archive));
                var coordinator = new ActionCoordinator("software-sway",fixture.journal,(head,command)->fixture.guard(before,command.operation(),archive),bindings,
                        (permit,nativeRequest,deadline)-> { dispatches.incrementAndGet(); throw new AssertionError("parent must settle before Root independently replans continuation"); },bindings.effects(),Clock.fixed(NOW,ZoneOffset.UTC),bindings.composites());
                var initial = request.apply(before); var policy = new OrdinarySwayPolicy(fixture.source,ignored -> OrdinarySwayPolicy.project(before.identity(),OrdinarySwayReadSource.originalResult(originalRoot),new OrdinarySwayService.Capabilities(true,true,true),()->Optional.of(SwaySessionInputs.project(load(fixture.domain,session),before.identity()))),SwayOrdinaryComposite::expected);
                var parent = assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluate(initial,softwareDraft(initial,"software-prior"))).draft().command().orElseThrow();
                var receipt = coordinator.execute(session,parent); assertTrue(receipt.settled()); assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance()); assertEquals(0,dispatches.get());
                var settled = assertInstanceOf(ActionState.CompositeSettled.class,receipt.state()); assertTrue(settled.execution().children().isEmpty());
                var proof = assertInstanceOf(ActionState.SwaySchedulerCompleted.class,settled.settlement()).proof(); assertEquals(SwaySchedulerCompletion.Continuation.FRESH_FULL_PLAN_REQUIRED,proof.continuation());
                var retained = proof.exactContinuation().orElseThrow(); assertEquals(after.identity(),retained.before()); assertEquals("life-advance",retained.operation().value());
                var originals = proof.fullPlanOriginals().orElseThrow(); assertArrayEquals(PlanningWire.encodeRequest(request.apply(after)),archive.loadMaterial(originals.request()).bytes());
                var result = assertInstanceOf(PlanningResult.ActionSelected.class,PlanningWire.decodeResult(archive.loadMaterial(originals.result()).bytes())); assertEquals(retained,result.command());
                assertTrue(ContinuityActionJournal.lookup(session.head().state(),retained.actionId(),archive).isEmpty(),"archived planner selection has no durable action intent or submit authority");
                fixture.domain.verifySchedulerCompleted(session,parent,settled.execution(),proof);
                byte[] wire = ActionReceiptCodec.encodeReceipt(receipt,archive); var cold = ActionReceiptCodec.decodeReceipt(wire,archive); assertArrayEquals(wire,ActionReceiptCodec.encodeReceipt(cold,archive));
                assertArrayEquals(wire,ActionReceiptCodec.encodeReceipt(coordinator.execute(session,parent),archive)); assertEquals(0,dispatches.get());
                return true;
            } catch(Exception failure) { throw new RuntimeException(failure); }
        });
    }
    /** Explicit software stage producers exercise the actual planner; they are never a production installation. */
    private static OrdinaryPlanner softwareFullPlanner(ExactRef source) {
        var realm = new org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle(source);
        var policies = new java.util.ArrayList<OrdinaryPolicy>();
        for (var stage : PlanningStage.values()) {
            if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION) { policies.add(realm); continue; }
            policies.add(new OrdinaryPolicy() {
                @Override public PlanningStage stage() { return stage; }
                @Override public ExactRef implementationSource() { return source; }
                @Override public Decision evaluate(PlanningRequest request,Draft previous) {
                    if(stage==PlanningStage.ORDINARY_SWAY) throw new AssertionError("actual planAfterOptional must suppress completed Sway once");
                    return stage==PlanningStage.ORDINARY_CORE ? new Replace(softwareDraft(request,"software-fresh-life"),"explicit software selection") : new Keep("explicit independent software stage");
                }
            });
        }
        return new OrdinaryPlanner(policies,Clock.fixed(NOW,ZoneOffset.UTC),realm);
    }
    private static OrdinaryPolicy.Draft softwareDraft(PlanningRequest request,String id) {
        var command = new ActionCommand(id,request.before(),request.source(),request.sessionId(),new OperationKey("life-advance"),new OpportunityJson.Obj(Map.of()),
                new ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),"software-prior/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("software.prior"),true))),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
        return new OrdinaryPolicy.Draft("software-prior","life-advance","explicit software selection",OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),new OpportunityJson.Obj(Map.of()));
    }
    private void actualStart(boolean initiallySettled) throws Exception {
        actualStart(initiallySettled,false);
    }
    private void actualStart(boolean initiallySettled,boolean finishAfterStart) throws Exception {
        actualStart(initiallySettled,finishAfterStart,false,false);
    }
    private void actualStart(boolean initiallySettled,boolean finishAfterStart,boolean observeFailure,boolean failEarlyBaseline) throws Exception {
        Fixture fixture = new Fixture(root, initiallySettled); var submitted = new java.util.concurrent.atomic.AtomicBoolean(); var writes = new java.util.concurrent.atomic.AtomicInteger(); var readSequence = new java.util.concurrent.atomic.AtomicInteger(); var nativeActionId = new AtomicReference<String>();
        var finishing=new java.util.concurrent.atomic.AtomicBoolean();var stopWrites=new java.util.concurrent.atomic.AtomicInteger();var allocatedStopIds=new java.util.concurrent.atomic.AtomicInteger();
        var followingCold = new AtomicReference<byte[]>();
        ActionReceipt completed = fixture.journal.locked(locked -> {
            try {
                var session = locked.writerSession(); var archive = fixture.archive.withSession(session); var before = fixture.frame(archive,9); var after = fixture.frame(archive,10);
                var currentFrame = new AtomicReference<>(before); var observationPhase = new java.util.concurrent.atomic.AtomicInteger();
                var frames = new java.util.HashMap<ProposalLifecycle.ObservationIdentity,DriverObservationAssembler.Complete>(); frames.put(before.identity(),before); frames.put(after.identity(),after);
                var rootDefinition = new ReadContract<OpportunityJson.Obj>(ROOT_ID,OrdinarySwayReadSource.ROOT,Optional.empty(),"software-root-private",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,fixture.source,
                        request -> new NativeRequest(request.operation().value(),Optional.empty(),new RawJson(bytes("{}"))),OrdinarySwayReadSource::originalResult);
                var nativeReads = new SwayRootReads(new SwayRootReads.Sources(fixture.source,fixture.source,fixture.source));
                var readCatalog = new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(rootDefinition,fixture.source)),nativeReads.families()); nativeReads.attach(readCatalog);
                PlanningReadPort readPort = new PlanningReadPort() {
                    @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> definition,PlanningReadRequest request) { assertSame(session,same); return read(definition,request); }
                    @Override public <T> PlanningReadResult<T> read(ReadContract<T> definition,PlanningReadRequest request) {
                        if(failEarlyBaseline && definition.operation().value().equals(SwayObservationReads.Kind.OPINION.step())) throw new OrdinarySwayService.Unavailable("synthetic early baseline read failed");
                        if(observeFailure && observationPhase.get()>0 && definition.operation().value().equals(SwayObservationReads.Kind.TERMINATION.step())) throw new OrdinarySwayService.Unavailable("synthetic retained end reader unavailable");
                        try {
                            var frame = java.util.Objects.requireNonNull(frames.get(request.before())); assertEquals(frame.identity(),request.before());
                            PlanningReadReceipt receipt;
                            if(definition.operation().equals(OrdinarySwayReadSource.ROOT)) receipt = fixture.rootRead(frame,archive,true);
                            else {
                                String role = definition.operation().value().startsWith(SwayNativeWire.RECEIPT) ? "receipt" : "query";
                                boolean plane=definition.operation().equals(new OperationKey(SwayObservationReads.Kind.COMPLETION.step()))||definition.operation().equals(new OperationKey(SwayObservationReads.Kind.OPINION.step()));
                                boolean journal=definition.operation().equals(new OperationKey(SwayObservationReads.Kind.EXECUTION.step()))||definition.operation().equals(new OperationKey(SwayObservationReads.Kind.TERMINATION.step()));
                                ObjectNode packet;
                                if(journal) {
                                    var kind=definition.operation().value().equals(SwayObservationReads.Kind.EXECUTION.step())?SwayObservationReads.Kind.EXECUTION:SwayObservationReads.Kind.TERMINATION;
                                    var args=StrictJson.parse(OpportunityJson.encode(request.arguments()));var subject=new org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject(ACTOR,TARGET,1,0);
                                    packet=journalPlane(kind,frame,subject,new BigInteger(args.get("after_sequence").textValue()));
                                }else packet=plane?finishPlane(definition.operation(),frame):wire(role);
                                if(plane && (observeFailure || failEarlyBaseline)) {
                                    if(definition.operation().value().equals(SwayObservationReads.Kind.OPINION.step())) {
                                        var named=(ObjectNode)packet.at("/result/sway_outcome_opinion/scheme_sway_opinion"); named.put("observed",true);
                                        if(observationPhase.get()==0)named.put("present",false).putNull("value");else named.put("present",true).put("value",25);
                                    } else if(observationPhase.get()==2) {
                                        var body=(ObjectNode)packet.at("/result/sway_completion");body.put("native_owner_raw",0xffff_ffffL);body.put("owner_matches_actor",false);body.put("owner_cleared",true);
                                        body.put("native_status_raw",1);body.put("native_status_key","terminated_unattributed");body.put("native_terminal_state_observed",true);body.put("native_success_chance_observed",false);body.putNull("native_success_chance_raw");
                                    }
                                }
                                String requestId = "software-sway-read-"+readSequence.incrementAndGet(); packet.put("request_id",requestId);
                                if(!plane&&!journal) {
                                ObjectNode body = (ObjectNode)packet.at("/result/"+(role.equals("receipt") ? "active_scheme_sway_formal" : "active_scheme_sway"));
                                if(role.equals("receipt")) body.put("action_id",nativeActionId.get());
                                else {
                                    body.put("snapshot_revision",frame.identity().frame().identity().nativeRevision());
                                    if(submitted.get()) { body.put("capture_epoch",43); body.put("active_scheme_count",1); body.put("matching_sway_active",true); body.put("native_complete_can_send",false); body.put("native_legal_now",false);
                                        body.putArray("active_sway_instances").addObject().put("scheme_instance_id",1).put("scheme_instance_generation",0).put("target_character_id",TARGET).put("progress",1).put("progress_goal",355).put("is_exposed",false).put("is_frozen",false); }
                                    if(finishing.get())body.put("target_opinion_of_actor",60);
                                }
                                }
                                var guard = fixture.guard(frame,definition.operation(),archive); var readGuard = new PlanningReadGuard(guard,true,true,true,frame.fullBindingSha256());
                                var ack = acknowledgement(packet); archive.preserve(ack); receipt = new PlanningReadReceipt(request,definition.contractId(),requestId,readGuard,readGuard,ack);
                            }
                            var ref = archive.preserveRead(receipt); return new PlanningReadResult.Known<>(definition.decode(receipt),receipt,ref);
                        } catch(Exception failure) { throw new RuntimeException(failure); }
                    }
                };
                var registered = new SwayActionLifecycle.RegisteredReads() {
                    @Override public ReadContract<SwayNativeWire.TargetRead> target(long target) { return nativeReads.target(target); }
                    @Override public ReadContract<SwayNativeWire.AppliedReceipt> receipt(long target,String action,BigInteger epoch) { return nativeReads.receipt(target,action,epoch); }
                    @Override public ReadContract<SwayObservationReads.Plane> plane(SwayObservationReads.Kind kind,org.xar.ck3.control.g2.m6.G2M6Contracts.Identity identity) { return nativeReads.plane(kind,identity); }
                };
                var originalRoot = fixture.rootRead(before,archive,true); var originalRootRef = archive.preserveRead(originalRoot);
                ExactRef original = write(root.resolve("state/active-scheme-sway-formal-private-v1.json"),bytes("{\"schema\":\"xar.ck3.active-scheme-sway-formal-private.v1\",\"pending\":null,\"resolved\":null}"));
                fixture.domain.importOriginal(session,original,archive.preserveMaterial(new RawJson(Files.readAllBytes(Path.of(original.path())))),originalRootRef,Optional.empty());
                java.util.function.Function<DriverObservationAssembler.Complete,PlanningRequest> request = frame -> new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),DEADLINE,
                        new PlanningObservation(frame.semantic(),List.of(),Set.of(OrdinarySwayPolicy.OPERATION),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
                var lifecycle = new SwayActionLifecycle(fixture.domain,fixture.archive,readPort,registered,fixture::same,
                        command -> {var frame=currentFrame.get();return new SwayActionLifecycle.View(frame.identity(),frame.source(),frame.sessionId(),DEADLINE);},new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
                var nativeActions = new SwayRootActions(lifecycle,new SwayRootActions.Sources(fixture.source,fixture.source,fixture.source)); var inventory = new AtomicReference<RootExecutableBindings>();
                var executor = new SwayOrdinaryExecutor(fixture.domain,fixture.archive,readPort,rootDefinition,registered,nativeActions,inventory::get,fixture::same,
                        parent -> { var frame = currentFrame.get(); return new SwayOrdinaryExecutor.Fresh(request.apply(frame),NativeEffectEvidence.basis(frame)); },
                        parent -> { throw new AssertionError("new Start does not use cold observation authority"); },
                        deadline -> { throw new java.io.IOException("software fixture cannot mint RestoreBinding"); },
                        () -> { if(observeFailure)return softwareFullPlanner(fixture.source);throw new AssertionError("verified new Start must not invoke ordinary fallback"); });
                var composite = new SwayOrdinaryComposite(executor,fixture.domain,fixture::same); var binding = new RootExecutableBindings.CompositeBinding(composite,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),fixture.source,fixture.source);
                var followingBinding = new RootExecutableBindings.ActionBinding(new NativeEffectRegistry.Binding(SOFTWARE_FOLLOWING,fixture.source,
                        command -> new NativeRequest(SOFTWARE_FOLLOWING.value(),Optional.empty(),new RawJson(bytes("{}"))),
                        (command,attempt,dispatch) -> {
                            var previous = java.util.Objects.requireNonNull(frames.get(command.before())); var observed = currentFrame.get();
                            var pair = new NativeEffectSnapshots.Pair(previous,observed);
                            var material = NativeEffectEvidence.preserve(command,attempt,pair,List.of(),new RawJson(bytes("{\"status\":\"postcondition\"}")),archive);
                            var effect = new ActionState.EffectObservation(observed.identity(),observed.source(),observed.sessionId(),"software-following/v1",
                                    List.of(new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("software.observed_date"),observed.identity().frame().identity().dateRaw())),
                                    "software-independent-following-read",observed.observedAt(),observed.originalEvidence(),List.of(material));
                            return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(effect),Optional.empty());
                        }),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),fixture.source);
                var followingReplay = new NativeRecordedEvidenceVerifier.Binding(SOFTWARE_FOLLOWING,fixture.source,
                        (head,proposed,originals) -> verifySoftwareFollowing(proposed,originals));
                var bindings = RootExecutableBindings.freeze(List.of(nativeActions.selectedStop(),followingBinding),readCatalog,List.of(binding),List.of(nativeActions.selectedStopReplay(),composite.recorded(fixture.source),followingReplay),List.of(nativeActions.startFamily()),32); inventory.set(bindings);
                fixture.guardFactory.set(command -> fixture.guard(java.util.Objects.requireNonNull(frames.get(command.before())),command.operation(),archive));
                NativeActionPort nativePort = (permit,nativeRequest,deadline) -> {
                    permit.consumeOnce();
                    if(nativeRequest.step().equals(SOFTWARE_FOLLOWING.value())) {
                        var next=fixture.frame(archive,14,53220000+2*720+48);frames.put(next.identity(),next);currentFrame.set(next);
                        var packet=StrictJson.object();packet.put("protocol_version",1);packet.put("type","command_result");packet.put("request_id",permit.requestId());packet.put("ok",true);packet.putObject("result").put("step",SOFTWARE_FOLLOWING.value()).put("accepted",true);
                        try { return acknowledgement(packet); }
                        catch(java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
                    }
                    if(nativeRequest.step().equals(SwayNativeWire.STOP)) {
                        assertEquals(1,stopWrites.incrementAndGet());
                        try {return new NativeActionPort.Unknown(permit.requestId(),"declared software Stop lost its result after the single write",
                                org.xar.ck3.control.nativebridge.NativeWire.execute(permit.requestId(),nativeRequest.step(),permit.expectedRevision(),nativeRequest.additionalFields().bytes()),Optional.empty());}
                        catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
                    }
                    assertEquals(1,writes.incrementAndGet()); assertEquals(SwayNativeWire.START+TARGET,nativeRequest.step()); nativeActionId.set(permit.actionId()); submitted.set(true); currentFrame.set(after);
                    try { var packet = wire("submit"); packet.put("request_id",permit.requestId()); ((ObjectNode)packet.at("/result/active_scheme_sway_formal")).put("action_id",permit.actionId()); return acknowledgement(packet); }
                    catch(Exception failure) { throw new RuntimeException(failure); }
                };
                var coordinator = new ActionCoordinator("software-sway",fixture.journal,(head,command)->fixture.guard(java.util.Objects.requireNonNull(frames.get(command.before())),command.operation(),archive),bindings,nativePort,bindings.effects(),Clock.fixed(NOW,ZoneOffset.UTC),bindings.composites(),
                        (same,command)-> { if(command.operation().value().startsWith(SwayNativeWire.START)||command.operation().value().equals(SwayNativeWire.STOP)) lifecycle.pendingProducer().prepare(same,command); });
                var originalRequest = request.apply(before); var policy = new OrdinarySwayPolicy(fixture.source,ignored -> OrdinarySwayPolicy.project(before.identity(),OrdinarySwayReadSource.originalResult(originalRoot),new OrdinarySwayService.Capabilities(true,true,true),()->Optional.of(SwaySessionInputs.project(load(fixture.domain,session),before.identity()))),SwayOrdinaryComposite::expected);
                var prior = new ActionCommand("software-earlier-life",before.identity(),before.source(),before.sessionId(),new OperationKey("life-advance"),new OpportunityJson.Obj(Map.of()),
                        new ProposalLifecycle.ExpectedPostcondition(1,before.identity(),before.source(),"software-prior/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("software.prior"),true))),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
                var draft = new OrdinaryPolicy.Draft("software-prior","life-advance","explicit software selection",OrdinaryPolicy.Kind.ORDINARY,Optional.of(prior),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),new OpportunityJson.Obj(Map.of()));
                var parent = assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluate(originalRequest,draft)).draft().command().orElseThrow(); assertEquals(OrdinarySwaySchedule.Job.QUERY_SELECTED_TARGET,OrdinarySwayPolicy.restoreStaged(parent).decision().job().orElseThrow());
                var receipt = coordinator.execute(session,parent); assertTrue(receipt.settled()); assertEquals(1,writes.get()); assertTrue(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
                var state = assertInstanceOf(ActionState.CompositeSettled.class,receipt.state()); var proof = assertInstanceOf(ActionState.SwaySchedulerCompleted.class,state.settlement()).proof(); assertEquals(SwaySchedulerCompletion.Continuation.NOT_NEEDED,proof.continuation()); assertTrue(proof.newlyAppliedBusiness().isPresent()); assertEquals(1,state.execution().children().size());
                var child = ContinuityActionJournal.lookup(session.head().state(),nativeActionId.get(),archive).orElseThrow(); assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,child.outcome()); SwayActionLifecycle.verifyArchived(new DriverFrameEvidenceLoader(new DriverObservationAssembler()),session.head().state(),child,archive);
                fixture.domain.verifySchedulerCompleted(session,parent,state.execution(),proof); assertTrue(fixture.domain.load(session).ledger().pending().isEmpty()); assertEquals(nativeActionId.get(),fixture.domain.load(session).ledger().resolved().orElseThrow().identity().actionId());
                byte[] encoded = ActionReceiptCodec.encodeReceipt(receipt,archive); var cold = ActionReceiptCodec.decodeReceipt(encoded,archive); assertArrayEquals(encoded,ActionReceiptCodec.encodeReceipt(cold,archive)); assertTrue(cold.visibleGameplay()); assertFalse(cold.eligibleAdvance()); assertArrayEquals(encoded,ActionReceiptCodec.encodeReceipt(coordinator.execute(session,parent),archive)); assertEquals(1,writes.get(),"known parent must not dispatch Start again");
                var firstRun=SwaySchedulerReplay.decodeRun(archive.loadMaterial(proof.originalRun()).bytes());
                var firstResult=assertInstanceOf(OrdinarySwayService.FormalResult.class,firstRun.result());
                var firstEvidence=StrictJson.parse(firstResult.evidence().bytes());
                assertEquals(failEarlyBaseline?"query_failed":"observed",firstEvidence.at("/ordinary_sway_post_start_observation/status").textValue());
                assertFalse(firstEvidence.at("/ordinary_sway_post_start_observation/submit_attempted").booleanValue());
                assertEquals(0,firstEvidence.at("/ordinary_sway_post_start_observation/new_game_days").intValue());
                var early=fixture.domain.load(session).ledger().resolved().orElseThrow();assertEquals(0,early.identity().schemeInstanceGeneration());
                if(failEarlyBaseline) {assertTrue(early.lifecycle().material().isEmpty());assertTrue(firstEvidence.at("/ordinary_sway_post_start_observation/error").textValue().contains("synthetic early baseline read failed"));}
                else assertTrue(early.lifecycle().material().isPresent(),"actual confirmed Start must capture named baseline before ordinary time advances");
                if(observeFailure) {
                    assertEquals(Optional.of(BigInteger.ZERO),early.lifecycle().material().orElseThrow().sway().points());assertTrue(early.lifecycle().firstGain().isEmpty());
                    var baseline=early.lifecycle().material().orElseThrow();
                    for(int phase=1;phase<=2;phase++) {
                        observationPhase.set(phase);var observedFrame=fixture.frame(archive,10+phase,53220000+phase*720);frames.put(observedFrame.identity(),observedFrame);currentFrame.set(observedFrame);
                        var observedRoot=fixture.rootRead(observedFrame,archive,true);archive.preserveRead(observedRoot);var observedRequest=request.apply(observedFrame);
                        var ordinaryPolicy=new OrdinarySwayPolicy(fixture.source,ignored->OrdinarySwayPolicy.project(observedFrame.identity(),OrdinarySwayReadSource.originalResult(observedRoot),new OrdinarySwayService.Capabilities(true,true,true),()->Optional.of(SwaySessionInputs.project(load(fixture.domain,session),observedFrame.identity()))),SwayOrdinaryComposite::expected);
                        var observationParent=assertInstanceOf(OrdinaryPolicy.Replace.class,ordinaryPolicy.evaluate(observedRequest,softwareDraft(observedRequest,"software-next-life-"+phase))).draft().command().orElseThrow();
                        assertEquals(OrdinarySwaySchedule.Job.OBSERVE_APPLIED,OrdinarySwayPolicy.restoreStaged(observationParent).decision().job().orElseThrow());
                        var observationReceipt=coordinator.execute(session,observationParent);assertTrue(observationReceipt.settled());assertFalse(observationReceipt.visibleGameplay());assertFalse(observationReceipt.eligibleAdvance());assertEquals(1,writes.get());assertEquals(0,stopWrites.get());
                        var observationSettled=assertInstanceOf(ActionState.CompositeSettled.class,observationReceipt.state());var observationProof=assertInstanceOf(ActionState.SwaySchedulerCompleted.class,observationSettled.settlement()).proof();
                        var run=SwaySchedulerReplay.decodeRun(archive.loadMaterial(observationProof.originalRun()).bytes());var unavailable=assertInstanceOf(OrdinarySwayService.LocalResult.class,run.result());
                        assertEquals(OrdinarySwayService.LocalStatus.UNAVAILABLE,unavailable.status());assertTrue(unavailable.error().orElseThrow().contains("synthetic retained end reader unavailable"));assertEquals(2,run.reads().size(),"successful completion/opinion originals survive the later failed reader");
                        fixture.domain.verifySchedulerCompleted(session,observationParent,observationSettled.execution(),observationProof);
                        var episode=fixture.domain.load(session).ledger().resolved().orElseThrow();assertTrue(episode.stop().isEmpty());var gain=episode.lifecycle().firstGain().orElseThrow();
                        assertEquals(baseline.source(),gain.baseline());assertEquals(BigInteger.valueOf(25),gain.observed().sway().points().orElseThrow());assertFalse(gain.observed().consumption().nextTurnConsumed());
                        assertEquals(phase==2,episode.lifecycle().terminal().isPresent());
                        byte[] ledgerBytes=SwayFormalCodec.encode(fixture.domain.load(session).ledger());assertArrayEquals(ledgerBytes,SwayFormalCodec.encode(SwayFormalCodec.decode(ledgerBytes)));
                        assertArrayEquals(ActionReceiptCodec.encodeReceipt(observationReceipt,archive),ActionReceiptCodec.encodeReceipt(coordinator.execute(session,observationParent),archive),"known failed optional parent never replays or reacquires native results");
                    }
                    var following=fixture.frame(archive,13,53220000+2*720+24);frames.put(following.identity(),following);currentFrame.set(following);
                    var followingRead=fixture.rootRead(following,archive,true);var followingRef=archive.preserveRead(followingRead);
                    var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());var oldChild=ContinuityActionJournal.lookup(session.head().state(),nativeActionId.get(),archive).orElseThrow();
                    var legacyInput=new SwayTransitionCodec.Input(fixture.domain.load(session).original().reference().payload(),new SwayFormalState.Following(following.identity()),new SwayTransitionCodec.Proofs(List.of(followingRef),Optional.empty(),Optional.empty()));
                    byte[] legacyBytes=SwayTransitionCodec.encode(legacyInput);assertArrayEquals(legacyBytes,SwayTransitionCodec.encode(SwayTransitionCodec.decode(legacyBytes,fixture.domain.load(session).ledger())));
                    assertThrows(IllegalArgumentException.class,()->fixture.domain.commit(session,new SwayFormalState.Following(following.identity()),legacyInput.proofs()),"historical v2 remains readable but cannot publish new source-only Following");
                    String unchangedHead=session.head().digest();
                    var stale=SwayFollowingConsumption.consume(session,fixture.domain,fixture.archive,game(),loader,oldChild,
                            (same,actual) -> SwayActionLifecycle.verifyArchived(loader,same.head().state(),actual,archive),
                            command -> new SwayOrdinaryExecutor.FinalRead(NativeEffectEvidence.basis(following),followingRef));
                    assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,stale);assertEquals(unchangedHead,session.head().digest(),"an earlier confirmed Start plus a later read cannot consume subsequent gain or terminal");
                    var unconsumed=fixture.domain.load(session).ledger();assertFalse(unconsumed.resolved().orElseThrow().lifecycle().firstGain().orElseThrow().observed().consumption().nextTurnConsumed());
                    assertFalse(unconsumed.resolved().orElseThrow().lifecycle().terminal().orElseThrow().consumption().nextTurnConsumed());
                    var gainSource=unconsumed.resolved().orElseThrow().lifecycle().firstGain().orElseThrow().observed().source();
                    var selective=SwayFormalState.reduce(unconsumed,new SwayFormalState.FollowingGameplay(gainSource,following.identity(),archive.receiptReferenceOf(oldChild)));
                    assertTrue(selective.resolved().orElseThrow().lifecycle().firstGain().orElseThrow().observed().consumption().nextTurnConsumed());
                    assertFalse(selective.resolved().orElseThrow().lifecycle().terminal().orElseThrow().consumption().nextTurnConsumed(),"each later source remains unconsumed independently of the gain source");
                    var expectedDate=BigInteger.valueOf(53220000+2*720+48);
                    var followingCommand=new ActionCommand("software-confirmed-following",following.identity(),following.source(),following.sessionId(),SOFTWARE_FOLLOWING,new OpportunityJson.Obj(Map.of()),
                            new ProposalLifecycle.ExpectedPostcondition(1,following.identity(),following.source(),"software-following/v1",List.of(new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("software.observed_date"),expectedDate))),
                            new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
                    var actualFollowing=coordinator.execute(session,followingCommand);assertTrue(actualFollowing.settled());assertTrue(actualFollowing.visibleGameplay());assertFalse(actualFollowing.eligibleAdvance());
                    var post=currentFrame.get();var postRef=archive.preserveRead(fixture.rootRead(post,archive,true));
                    SwayFollowingConsumption.ActualResultVerifier verifier=(same,actual) -> verifySoftwareFollowing(actual,archive);
                    SwayOrdinaryExecutor.IndependentFinal finalRead=command -> new SwayOrdinaryExecutor.FinalRead(NativeEffectEvidence.basis(post),postRef);
                    String beforeConsumption=session.head().digest();
                    assertThrows(IllegalArgumentException.class,()->SwayFollowingConsumption.consume(session,fixture.domain,fixture.archive,game(),loader,actualFollowing,verifier,
                            command -> new SwayOrdinaryExecutor.FinalRead(NativeEffectEvidence.basis(following),followingRef)),"a guarded read before the confirmed actual poststate cannot grant consumption");
                    var pendingData=new ActionReceipt(actualFollowing.version(),actualFollowing.sequence(),actualFollowing.command(),actualFollowing.bodySha256(),new ActionState.Unknown(Optional.empty(),Optional.empty(),"software unknown-data negative",List.of()));
                    assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,SwayFollowingConsumption.consume(session,fixture.domain,fixture.archive,game(),loader,pendingData,
                            (same,actual) -> {throw new AssertionError("UNKNOWN cannot enter Following verification");},command -> {throw new AssertionError("UNKNOWN cannot read or replay");}));
                    assertEquals(beforeConsumption,session.head().digest());
                    var published=assertInstanceOf(OrdinaryPlanCompletion.Published.class,SwayFollowingConsumption.consume(session,fixture.domain,fixture.archive,game(),loader,actualFollowing,verifier,finalRead));
                    var consumed=fixture.domain.load(session).ledger();var lifecycleState=consumed.resolved().orElseThrow().lifecycle();
                    assertTrue(lifecycleState.firstGain().orElseThrow().observed().consumption().nextTurnConsumed());assertTrue(lifecycleState.terminal().orElseThrow().consumption().nextTurnConsumed());
                    assertEquals(org.xar.ck3.control.g2.m6.SwayLifecycle.TerminalKind.CURRENT_STATUS,lifecycleState.terminal().orElseThrow().kind());assertFalse(lifecycleState.terminal().orElseThrow().terminalCauseObserved());
                    String consumedHead=session.head().digest();assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,SwayFollowingConsumption.consume(session,fixture.domain,fixture.archive,game(),loader,actualFollowing,verifier,finalRead));assertEquals(consumedHead,session.head().digest());
                    var event=StrictJson.parse(Files.readAllBytes(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS").resolve(String.format(java.util.Locale.ROOT,"%08d.json",published.actual().head().sequence()))));
                    var producerInput=ExactRef.fromJson(event.at("/details/source/producer_input"));byte[] transition=archive.loadMaterial(producerInput).bytes();
                    var input=SwayTransitionCodec.decode(transition,unconsumed);var actualChange=assertInstanceOf(SwayFormalState.FollowingGameplay.class,input.change());
                    assertEquals(following.identity(),actualChange.actionBefore());assertEquals(post.identity(),actualChange.after());assertEquals(archive.receiptReferenceOf(actualFollowing),actualChange.receipt());
                    assertEquals(List.of(actualChange.receipt()),input.proofs().materials());assertEquals(List.of(postRef),input.proofs().reads());
                    assertArrayEquals(transition,SwayTransitionCodec.encode(input));
                    for(String defect:List.of("receipt","wrong-schema","float-revision","unexpected-field")) {
                        var invalid=(ObjectNode)StrictJson.parse(transition);var change=(ObjectNode)invalid.get("change");
                        switch(defect) {case "receipt" -> change.remove("receipt");case "wrong-schema" -> invalid.put("schema",SwayTransitionCodec.SCHEMA);case "float-revision" -> ((ObjectNode)change.get("action_before").get("frame")).put("revision",13.0);case "unexpected-field" -> change.put("alias",true);default -> throw new AssertionError(defect);}
                        assertThrows(IllegalArgumentException.class,()->SwayTransitionCodec.decode(StrictJson.canonical(invalid),consumed),defect);
                    }
                    assertThrows(IllegalArgumentException.class,()->fixture.domain.commit(session,new SwayFormalState.FollowingGameplay(following.identity(),post.identity(),archive.receiptReferenceOf(oldChild)),new SwayTransitionCodec.Proofs(List.of(postRef),Optional.empty(),Optional.empty(),List.of(archive.receiptReferenceOf(oldChild)))));
                    assertEquals(consumedHead,session.head().digest());
                    var coldLedger=SwayFormalCodec.decode(SwayFormalCodec.encode(consumed));assertEquals(lifecycleState,coldLedger.resolved().orElseThrow().lifecycle());assertTrue(coldLedger.resolved().orElseThrow().stop().isEmpty());assertEquals(1,writes.get());assertEquals(0,stopWrites.get());followingCold.set(SwayFormalCodec.encode(consumed));
                }
                if(finishAfterStart) {
                    finishing.set(true);var finish=new SwaySelectedFinish(fixture.domain,fixture.archive,readPort,registered,()->{allocatedStopIds.incrementAndGet();return "stop-sway-software-original";});
                    var finishRequest=new SwaySelectedFinish.Request(after.identity().frame().revision(),TARGET,1,0);var view=new SwayActionLifecycle.View(after.identity(),after.source(),after.sessionId(),DEADLINE);
                    String originalHead=session.head().digest();var selected=assertInstanceOf(SwaySelectedFinish.NewStop.class,finish.prepare(session,view,finishRequest));
                    assertEquals(originalHead,session.head().digest(),"producer only prepares; sole pending hook must publish under coordinator");assertEquals(3,selected.evidence().size());assertEquals(1,allocatedStopIds.get());
                    assertArrayEquals(ActionCodec.encodeCommand(selected.command()),ActionCodec.encodeCommand(ActionCodec.decodeCommand(ActionCodec.encodeCommand(selected.command()))));
                    var stopped=coordinator.execute(session,selected.command());assertFalse(stopped.settled());assertEquals(1,stopWrites.get());
                    assertEquals("stop-sway-software-original",fixture.domain.load(session).ledger().resolved().orElseThrow().stop().orElseThrow().actionId());
                    var retained=assertInstanceOf(SwaySelectedFinish.ExistingStop.class,finish.prepare(session,view,finishRequest));assertEquals(stopped.command().actionId(),retained.actionId());
                    assertEquals(archive.receiptReferenceOf(stopped),retained.canonicalReceipt());var observed=coordinator.reconcile(session,retained.actionId());assertFalse(observed.settled());
                    assertEquals(1,stopWrites.get(),"UNKNOWN only observes original Stop and never resubmits");assertEquals(1,allocatedStopIds.get());
                    assertThrows(IllegalArgumentException.class,()->finish.prepare(session,view,new SwaySelectedFinish.Request(view.before().frame().revision(),TARGET,2,0)));
                    var journals=new SwaySelectedJournal(fixture.domain,fixture.archive,readPort,nativeReads);var cursor=new BigInteger("9007199254740992");
                    for(var kind:List.of(SwayObservationReads.Kind.EXECUTION,SwayObservationReads.Kind.TERMINATION)) {
                        int beforeReads=readSequence.get();var batch=journals.read(session,view,new SwayObservationReads.JournalQuery(kind,fixture.domain.load(session).ledger().resolved().orElseThrow().identity().nativeSubject(),cursor));
                        assertEquals(2,readSequence.get()-beforeReads,"Service must independently query the opposite source plane");assertEquals(cursor,batch.primary().afterSequence());assertEquals(BigInteger.ZERO,batch.independentPeer().afterSequence());
                        assertTrue(batch.originalComposition().isPresent());var result=StrictJson.parse(SwayPublicCodec.publicNormalized(batch).bytes());
                        assertTrue(result.has("sway_terminal_sources_12004"));assertFalse(result.get("sway_end_cause_observed_12004").booleanValue());
                        var pair=result.at("/sway_terminal_sources_12004/cause_input_pair");String selectedKey=kind==SwayObservationReads.Kind.EXECUTION?"execution_read":"termination_read";String peerKey=kind==SwayObservationReads.Kind.EXECUTION?"termination_read":"execution_read";
                        assertEquals(cursor.toString(),pair.get(selectedKey).get("after_sequence").textValue());assertEquals("0",pair.get(peerKey).get("after_sequence").textValue());
                        var afterJournal=fixture.domain.load(session).ledger();assertEquals(stopped.command().actionId(),afterJournal.resolved().orElseThrow().stop().orElseThrow().actionId());
                        assertArrayEquals(SwayFormalCodec.encode(afterJournal),SwayFormalCodec.encode(SwayFormalCodec.decode(SwayFormalCodec.encode(afterJournal))));
                    }
                    assertEquals(1,stopWrites.get());assertEquals(1,allocatedStopIds.get());
                }
                return receipt;
            } catch(Exception failure) { throw new RuntimeException(failure); }
        });
        // The actual journal reopens and replays v4 through the same domain registration.
        if(observeFailure) fixture.journal.locked(locked -> {
            try { assertArrayEquals(followingCold.get(),SwayFormalCodec.encode(fixture.domain.load(locked.writerSession()).ledger())); return true; }
            catch(java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
        });
        // The actual journal opens the sole writer scope. Do not call it from an already held scope.
        if(finishAfterStart || observeFailure || failEarlyBaseline)return;
        if (initiallySettled) settleActualCycle(fixture, completed);
        else rejectLegacyCycleFrontier(fixture, completed);
    }
    private static void verifySoftwareFollowing(ActionReceipt receipt,ActionPorts.OutcomeArchive originals) {
        assertEquals(SOFTWARE_FOLLOWING,receipt.command().operation());
        var source=NativeEffectEvidence.load(receipt,originals,new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        var after=source.frames().after();assertTrue(after.identity().frame().identity().dateRaw().compareTo(source.frames().before().identity().frame().identity().dateRaw())>0);
        var effect=receipt.applied().orElseThrow().observation();assertEquals("software-following/v1",effect.observerSchema());
        assertEquals(List.of(new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("software.observed_date"),after.identity().frame().identity().dateRaw())),effect.actual());
    }
    /** Explicit software native packet derived from retained actual4 schema, never a relabeled old-build native qualification. */
    private static ObjectNode finishPlane(OperationKey operation,DriverObservationAssembler.Complete frame)throws Exception {
        String resource="/sway/actual-retained-nonempty-ledger.json";byte[] original;
        try(var stream=SwayCanonicalSchedulerIntegrationTest.class.getResourceAsStream(resource)) {assertNotNull(stream,"actual historical full original is mandatory");original=stream.readAllBytes();}
        assertEquals("6f1da9ee2c0e00839497a650cbcfaba527807342e85cce29d8a357344f55aad9",ActionCodec.sha256(original));
        var old=StrictJson.parse(original,SwayFormalCodec.MAX);var packet=StrictJson.object();packet.put("protocol_version",1);packet.put("type","command_result");packet.put("request_id","software-finish-read");packet.put("ok",true);
        var result=packet.putObject("result");result.put("step",operation.value());result.put("accepted",true);result.put("status","available");result.put("private_build",true);result.put("read_only",true);result.put("advertised",false);result.put("backend_id","native-headless");
        if(operation.value().equals(SwayObservationReads.Kind.COMPLETION.step())) {
            var body=((ObjectNode)old.at("/resolved/latest_instance_observation/native_observation")).deepCopy();
            for(String field:List.of("exact_ck3_build","exe_sha256","queried_snapshot_id","queried_revision","queried_native_revision","backend_id","status"))body.remove(field);
            body.put("snapshot_revision",frame.identity().frame().identity().nativeRevision());body.put("date_raw",frame.identity().frame().identity().dateRaw());body.put("actor_character_id",ACTOR);body.put("target_character_id",TARGET);body.put("scheme_instance_id",1);body.put("scheme_instance_generation",0);body.put("native_owner_raw",ACTOR);result.set("sway_completion",body);
        } else {
            var body=result.putObject("sway_outcome_opinion");body.put("schema","xar.ck3.sway-outcome-opinion-v1");body.put("build",SwayNativeWire.BUILD);body.put("available",true);body.put("unavailable_reason","");
            body.put("snapshot_revision",frame.identity().frame().identity().nativeRevision());body.put("date_raw",frame.identity().frame().identity().dateRaw());body.put("actor_character_id",ACTOR);body.put("target_character_id",TARGET);body.put("target_opinion_of_actor",60);
            body.set("scheme_sway_opinion",old.at("/resolved/material_intervention/scheme_sway_opinion").deepCopy());body.set("sway_blocker_opinion",old.at("/resolved/material_intervention/sway_blocker_opinion").deepCopy());body.put("instance_terminal_outcome_observed",false);body.put("cancel_outcome_observed",false);
        }
        return packet;
    }
    private static SwayFormalState.Ledger load(SwayCanonicalDomain domain,ContinuityStorePort.Session session) { try { return domain.load(session).ledger(); } catch(java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); } }
    private static void rejectLegacyCycleFrontier(Fixture fixture,ActionReceipt receipt) throws Exception {
        var calls = new java.util.concurrent.atomic.AtomicInteger(); var entered = new java.util.concurrent.atomic.AtomicInteger();
        var cycles = new org.xar.ck3.control.application.session.OrdinaryCycleTransitions(fixture.archive,
                (same,owner,semantic)-> { calls.incrementAndGet(); throw new java.io.IOException("no qualified Root SemanticVerifier fixture; never mint success"); },
                (same,owner,pair,proof)-> { throw new java.io.IOException("no qualified SAVE fixture"); },new org.xar.ck3.control.continuity.OriginalWindowReducer.Policy(10958),same -> { fixture.writer.requireSession(same); entered.incrementAndGet(); });
        cycles.bindTerminalFrameLoader(new DriverFrameEvidenceLoader(new DriverObservationAssembler())); fixture.cycleAuthority.set(cycles); var journal = new org.xar.ck3.control.application.session.ContinuityBatchJournal(fixture.writer,cycles);
        var command = receipt.command(); var owner = new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(command.before().machineId(),command.before().game(),command.sessionId());
        String before = fixture.writer.locked(same -> same.head().digest());
        assertThrows(Exception.class,()->journal.retainCycle(owner,receipt)); assertTrue(entered.get()>0,"actual shared Cycle authority must enter its original writer scope");
        assertEquals(before,fixture.writer.locked(same -> same.head().digest()),"legacy pending/binding rejection must not grant cycle or day credit"); assertEquals(0,calls.get());
    }
    private static void settleActualCycle(Fixture fixture,ActionReceipt receipt) throws Exception {
        var verifier = new org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier(fixture.archive::readArtifact);
        var cycles = new org.xar.ck3.control.application.session.OrdinaryCycleTransitions(fixture.archive,verifier,
                (same,owner,pair,proof)-> { throw new java.io.IOException("software fixture has no paired SAVE authority"); },
                new org.xar.ck3.control.continuity.OriginalWindowReducer.Policy(10958),fixture.writer::requireSession);
        cycles.bindTerminalFrameLoader(new DriverFrameEvidenceLoader(new DriverObservationAssembler())); fixture.cycleAuthority.set(cycles);
        var journal = new org.xar.ck3.control.application.session.ContinuityBatchJournal(fixture.writer,cycles);
        var command = receipt.command(); var owner = new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(command.before().machineId(),command.before().game(),command.sessionId());
        var fresh = fixture.writer.locked(same -> { fixture.frame(fixture.archive.withSession(same),11); return fixture.semantics.get(11); });
        journal.retainCycle(owner,receipt); String retained = fixture.writer.locked(same -> same.head().digest());
        assertThrows(Exception.class,()->journal.settleCycle(owner,receipt,fixture.semantics.get(10)),"terminal frame is not a fresh post-terminal SEM");
        assertEquals(retained,fixture.writer.locked(same -> same.head().digest()));
        var proof = journal.settleCycle(owner,receipt,fresh); assertEquals(2,proof.completedCycles());
        var cold = org.xar.ck3.control.application.session.OrdinaryCycleTransitions.proofFromJson(org.xar.ck3.control.application.session.OrdinaryCycleTransitions.proofToJson(proof));
        assertEquals(proof,cold); assertEquals(proof,journal.cycleProof(owner,fresh).orElseThrow());
        String settled = fixture.writer.locked(same -> same.head().digest());
        journal.retainCycle(owner,receipt); assertEquals(proof,journal.settleCycle(owner,receipt,fresh));
        assertEquals(settled,fixture.writer.locked(same -> same.head().digest()),"cold/known completion cannot count an original receipt twice");
        fixture.writer.locked(same -> {
            assertEquals(1,same.head().state().settledCycles(),"ordinary completion alone cannot publish a saved frontier");
            assertEquals(53220000,same.head().state().settledDateRaw());
            assertFalse(same.head().state().toJson().has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
            assertEquals("VISIBLE_GAMEPLAY",StrictJson.text(StrictJson.parse(fixture.archive.withSession(same).loadMaterial(
                    ExactRef.fromJson(same.head().state().toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).get("head"))).bytes()).get("classification")));
            return true;
        });
        assertFalse(receipt.eligibleAdvance()); assertTrue(fixture.cycleValidations.get()>0);
    }
    private static ObjectNode wire(String role) throws Exception {
        String repository = System.getProperty("xar.repository.root"); assertNotNull(repository,"actual shared native serializer originals are mandatory");
        Path source = Path.of(repository).resolve("ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_sway_"+role+"_wire.json"); byte[] bytes = Files.readAllBytes(source);
        String digest = switch(role) { case "query" -> "8051e4ed15f12f5ff1466187ae0c61f05fc91284c4f0821b8e30dea9a0098bed"; case "submit" -> "0e906ab96b262a266d77677952327a28ce9107fa9069ab32fd8df724970ddefd"; case "receipt" -> "9731c34de32b17abf59ce44549a10a73231cff199944571419e73dd9a8fa552f"; default -> throw new IllegalArgumentException(role); };
        assertEquals(digest,ActionCodec.sha256(bytes)); return (ObjectNode)StrictJson.parse(bytes,SwayFormalCodec.MAX);
    }
    private static NativeActionPort.AckReceived acknowledgement(ObjectNode packet) throws java.io.IOException {
        byte[] bytes = StrictJson.canonical(packet,SwayFormalCodec.MAX); String requestId = StrictJson.text(packet.get("request_id")); return new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson(StrictJson.canonical(packet.get("result"),SwayFormalCodec.MAX))),new RawJson(bytes),org.xar.ck3.control.nativebridge.NativeWire.packet(bytes));
    }

    private static final class Fixture {
        final ExactRef source; final ContinuityWriter writer; final NativeOutcomeArchive archive; final ContinuityActionJournal journal; final SwayCanonicalDomain domain;
        final AtomicReference<GuardEvidence> currentGuard = new AtomicReference<>();
        final AtomicReference<java.util.function.Function<ActionCommand,GuardEvidence>> guardFactory = new AtomicReference<>();
        final AtomicReference<org.xar.ck3.control.application.session.OrdinaryCycleTransitions> cycleAuthority = new AtomicReference<>();
        final java.util.concurrent.atomic.AtomicInteger cycleValidations = new java.util.concurrent.atomic.AtomicInteger();
        final Map<Integer,org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence> semantics = new java.util.HashMap<>();
        Fixture(Path root) throws Exception { this(root,false); }
        Fixture(Path root,boolean initiallySettled) throws Exception {
            Files.createDirectories(root.resolve("state")); Files.createDirectories(root.resolve("artifacts")); Files.createDirectories(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);
            source = write(root.resolve("software-reviewed-source.java"),bytes("explicit software source fixture; not a live permission"));
            ExactRef anchor = write(root.resolve("anchor.json"),ContinuityJson.canonical(initiallySettled ? settledSoftwareState() : state())); Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"),Files.readAllBytes(Path.of(anchor.path())));
            var layout = new WriterContracts.Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor,MACHINE);
            var storage = org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport.create(layout);
            var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"),layout.lock(),64L*1024*1024),storage);
            var domainRef = new AtomicReference<SwayCanonicalDomain>(); var actionRef = new AtomicReference<WriterContracts.TransitionAuthority>();
            var registration = new DomainBodies.Registration(DomainBodies.Slot.SWAY,SwayFormalState.SCHEMA,SwayFormalCodec.MAX,List.of(source),(head,previous,request,body)->domainRef.get().registration().verifier().verify(head,previous,request,body));
            writer = new ContinuityWriter(layout,List.of(source),new WriterContracts.TransitionAuthority() {
                @Override public String revalidate(ContinuityState head,WriterContracts.Request request) { throw new IllegalStateException("actual original head required"); }
                @Override public String revalidate(WriterContracts.Head head,WriterContracts.Request request) throws java.io.IOException { if(cycleAuthority.get()!=null && cycleAuthority.get().kinds().contains(request.kind())) { cycleValidations.incrementAndGet(); return cycleAuthority.get().revalidate(head,request); } return actionRef.get().revalidate(head,request); }
                @Override public ContinuityState reduce(ContinuityState head,WriterContracts.Request request) throws java.io.IOException { if(cycleAuthority.get()!=null && cycleAuthority.get().kinds().contains(request.kind())) return cycleAuthority.get().reduce(head,request); return actionRef.get().reduce(head,request); }
            },Clock.fixed(NOW,ZoneOffset.UTC),new ContinuityWriter.Extensions(List.of(registration),Optional.of(artifacts),Optional.empty()),storage);
            assertSame(storage,writer.storageGuard());assertSame(storage,artifacts.storageGuard());
            archive = new NativeOutcomeArchive(artifacts,writer); var loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
            domain = new SwayCanonicalDomain(layout.lock(),root.resolve("state/active-scheme-sway-formal-private-v1.json"),archive,List.of(source),new SwaySchedulerReplay(loader,new OrdinarySwayService.Capabilities(true,true,true),ROOT_ID),loader); domainRef.set(domain);
            actionRef.set(new ActionContinuityAuthority("software-sway",archive,(head,command)->guardFactory.get() == null ? currentGuard.get() : guardFactory.get().apply(command),(head,proposed)->{
                if(proposed.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Applied) {
                    if(proposed.command().operation().equals(SOFTWARE_FOLLOWING)) verifySoftwareFollowing(proposed,archive.withSession(same()));
                    else SwayActionLifecycle.verifyArchived(loader,head.state(),proposed,archive.withSession(same()));
                }
                if(proposed.state() instanceof ActionState.CompositeSettled settled) {
                    StrictJson.require(settled.settlement() instanceof ActionState.SwaySchedulerCompleted,"only actual Sway scheduler fixture settlement");
                    try { domain.verifySchedulerCompleted(writer.borrowedSession(),proposed.command(),settled.execution(),((ActionState.SwaySchedulerCompleted)settled.settlement()).proof()); }
                    catch(java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
                }
            },Clock.fixed(NOW,ZoneOffset.UTC))); journal = new ContinuityActionJournal(writer,archive);
        }
        DriverObservationAssembler.Complete frame(ActionPorts.OutcomeArchive originals) { return frame(originals,9); }
        ContinuityStorePort.Session same() { try { return writer.borrowedSession(); } catch(java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); } }
        DriverObservationAssembler.Complete frame(ActionPorts.OutcomeArchive originals,int revision) { return frame(originals,revision,53220000); }
        DriverObservationAssembler.Complete frame(ActionPorts.OutcomeArchive originals,int revision,int dateRaw) {
            String state = "{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":53220000,\"played_character\":{\"character_id\":50331649,\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"active_wars\":[],\"player_armies\":[]}";
            state=state.replace("53220000",Integer.toString(dateRaw));
            byte[] body = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-"+revision+"\",\"revision\":"+revision+",\"state\":"+state+"}"); byte[] packet = ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
            var nativeFrame = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE,game(),BigInteger.valueOf(5),"held-session"),"snapshot-"+revision,BigInteger.valueOf(revision),new RawJson(bytes(state)),packet,NOW.plusSeconds(revision-9));
            var known = known(); var full = new RawJson(known.driver().encode()); var fullRef = originals.preserveMaterial(full); var sourceValue = new G2Source(MACHINE,NOW.toString(),SwayNativeWire.BUILD,source);
            var manifest = DriverObservationEvidenceReader.encode(known,nativeFrame,BigInteger.valueOf(revision+1L),1,sourceValue,new OpportunityJson.Obj(Map.of()),fullRef); var ref = originals.preserveMaterial(manifest); var facts = DriverObservationEvidenceReader.decode(ref,manifest,full,nativeFrame);
            var completed = assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(nativeFrame,facts,originals.preserveNativeFrame(nativeFrame)));
            var held = new DriverSnapshotFacts.Known(known.driver(),known.stamp(),known.originalHistoryBasis(),known.actionRows(),known.auxiliary(),known.loop(),Optional.of(facts));
            var semantic = originals.preserveMaterial(new RawJson(DriverJson.encode(completed.semantic())));
            var stamp = originals.preserveMaterial(new RawJson(org.xar.ck3.control.application.readiness.NativeDriverStamp.encode(completed,held)));
            semantics.put(revision,new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(completed.identity(),semantic,completed.originalEvidence(),stamp,fullRef,completed.observedAt()));
            return completed;
        }
        GuardEvidence guard(DriverObservationAssembler.Complete frame,OperationKey operation,ActionPorts.OutcomeArchive originals) {
            var basis = NativeEffectEvidence.basis(frame); var semantic = originals.preserveMaterial(new RawJson(DriverJson.encode(frame.semantic()))); var empty = originals.preserveMaterial(new RawJson(bytes("{}")));
            var row = StrictJson.object(); row.put("schema",RootGuardEvidence.SCHEMA); row.put("operation",operation.value()); row.put("authority_id","software-sway"); row.set("native_frame",basis.nativeFrame().toJson()); row.set("driver_facts",basis.driverFacts().toJson()); row.set("semantic",semantic.toJson());
            for(String field:List.of("driver_stamp","original_driver","capabilities","hello","heartbeat","source_qualification")) row.set(field,empty.toJson());
            var ref = originals.preserveMaterial(new RawJson(StrictJson.canonical(row))); return new GuardEvidence(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),operation,frame.originalEvidence(),empty,"software-sway",frame.observedAt(),DEADLINE,List.of(ref));
        }
        PlanningReadReceipt rootRead(DriverObservationAssembler.Complete frame,ActionPorts.OutcomeArchive originals) throws java.io.IOException { return rootRead(frame,originals,false); }
        PlanningReadReceipt rootRead(DriverObservationAssembler.Complete frame,ActionPorts.OutcomeArchive originals,boolean relation) throws java.io.IOException {
            var op = OrdinarySwayReadSource.ROOT; var guard = guard(frame,op,originals); var binding = new PlanningReadGuard(guard,true,true,true,frame.fullBindingSha256()); var result = StrictJson.object(); result.put("step",op.value()); result.put("accepted",true);
            var context = result.putObject("campaign_root_context"); context.put("status","available"); context.put("player_character_id",ACTOR); context.put("player_character_alive",true); context.put("snapshot_revision",frame.identity().frame().identity().nativeRevision()); context.put("date_raw",frame.identity().frame().identity().dateRaw()); if(relation) context.putArray("direct_landed_vassal_character_ids").add(TARGET); else context.putArray("direct_landed_vassal_character_ids");
            String requestId = "software-root-read-"+frame.identity().frame().identity().nativeRevision(); var packet = StrictJson.object(); packet.put("protocol_version",1); packet.put("type","command_result"); packet.put("request_id",requestId); packet.put("ok",true); packet.set("result",result);
            byte[] bytes = StrictJson.canonical(packet); var ack = new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(bytes),org.xar.ck3.control.nativebridge.NativeWire.packet(bytes)); originals.preserve(ack);
            return new PlanningReadReceipt(new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),op,new OpportunityJson.Obj(Map.of()),DEADLINE),ROOT_ID,requestId,binding,binding,ack);
        }
    }
    private static ExactRef write(Path path,byte[] bytes) throws java.io.IOException { Files.createDirectories(path.getParent()); Files.write(path,bytes); return new ExactRef(path.toAbsolutePath().toString(),bytes.length,ActionCodec.sha256(bytes)); }
    private static byte[] bytes(String value) { return value.getBytes(java.nio.charset.StandardCharsets.UTF_8); }
    private static org.xar.ck3.control.contracts.GameGeneration game() { return new org.xar.ck3.control.contracts.GameGeneration(42,new org.xar.ck3.control.contracts.PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    private static DriverSnapshotFacts.Known known() {
        byte[] wire = bytes("""
            {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":50331649,"episode_run_id":"episode-real-1",
             "last_checkpoint":null,"command_history":[
              {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
              {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
             "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
             "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
             "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":50331649}},
             "rollback_war_failures":[{"reason":"original advisory"}]}
            """);
        return DriverFactsRepository.imported(new ExactRef("software:driver-original",wire.length,ActionCodec.sha256(wire)),wire,3,7,game(),new OpportunityJson.Obj(Map.of()));
    }
    private static ObjectNode state() {
        var row = StrictJson.object(); row.put("schema","root.ck3.continuity-window/v1"); row.put("machine_id",MACHINE); row.put("sequence",0); row.put("window_id",1); row.put("status","running"); row.put("target_days",10958); row.put("target_years",30); row.put("calendar_year_days",365.25); row.put("start_date_raw",1000); row.put("target_date_raw",263992); row.put("last_settled_date_raw",1000); row.put("last_settled_cycles",1); row.put("manual_repair_count",0); row.put("automatic_recovery_count",0); row.put("binding_lineage_count",0); row.putObject("game_binding").put("pid",42).put("creation_date","2026-10-23T01:00:00Z"); row.putNull("latest_binding"); row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1); row.put("NEXT",2); return row;
    }
    /** A distinct explicit software outset, produced before the writer exists. Never repairs or clears an old pending head. */
    private static ObjectNode settledSoftwareState() {
        var details = StrictJson.object(); details.put("machine_id",MACHINE); details.put("evidence_id","software-initial-blocking-source"); details.put("source","software-only-baseline-not-game-qualification");
        details.putObject("game").put("pid",42).put("creation_date","2026-10-23T01:00:00Z"); details.put("completed_cycles",1); details.put("reason","explicit independent software outset");
        details.putObject("frame").put("date_raw",53220000).put("actor_character_id",ACTOR).put("episode_run_id","episode-real-1").put("snapshot_id","snapshot-9").put("revision",10).put("native_revision",9);
        var reducer = new org.xar.ck3.control.continuity.OriginalWindowReducer.Policy(10958);
        var prepared = org.xar.ck3.control.continuity.OriginalWindowReducer.reduce(null,"repair_required",details,reducer);
        details.put("evidence_id","software-initial-attach-source");
        return org.xar.ck3.control.continuity.OriginalWindowReducer.reduce(prepared,"attach_verified",details,reducer);
    }
}
