package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.nio.file.Files;
import java.io.IOException;
import java.io.ByteArrayInputStream;
import java.util.LinkedHashMap;
import java.util.Base64;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;
import org.xar.ck3.control.service.OfflineEventAnalysisHost;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryEvidenceLookup;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.NativeActionSteps;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software NativeWire/read/ordinary-selection/coordinator/archive path.
 * Synthetic receiver and option data never qualify a loaded Game or gameplay material. */
final class RootMandatoryChoiceRuntimeTest {
    @TempDir Path temporary;
    @Test void ordinaryQueryUsesActualMailboxTokenAndIndependentAfterThenReplaysOriginalArchive()throws Exception {
        run("advanced",true);
    }
    @Test void ackWithReceiverStillPresentRemainsUnknownAndCannotSubmitAgain()throws Exception {
        run("ack-only",false);
    }
    @Test void disabledFirstDisplayDoesNotSelectTheLaterEnabledNativeToken()throws Exception { run("disabled-first",false); }
    private void run(String name,boolean advanced)throws Exception {
        var owned=new AtomicReference<ActionWriterIntegrationFixture>();
        var installed=new AtomicReference<ReadContract<EventPolicies.ReadPublication>>();
        var journal=new AtomicReference<EpisodeIncidentJournal>();
        var knowledge=new AtomicReference<RootMandatoryChoiceRuntime.Knowledge>();
        var generation=new java.util.concurrent.atomic.AtomicInteger();
        var readScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(EventWindowModels.Build.TOURS.sha256(),
                "ck3-"+EventWindowModels.Build.TOURS.version()+"-msvc-x64",source->{
                    var query=RootMandatoryChoiceRuntime.contract(source,request->{ });installed.set(query);return List.of(query);
                },request->queryResult(request,name.equals("disabled-first")?-1:generation.incrementAndGet()),Optional.of(EventWindowModels.Build.TOURS.version()),Set.of(RootMandatoryChoiceRuntime.CAPABILITY));
        var actionScenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey(RootMandatoryChoiceRuntime.SELECT),
                RootMandatoryChoiceRuntime.CAPABILITY,(command,attempt,dispatch)->{
                    var actual=owned.get();var input=actual.physicalInputs();
                    var held=new HeldDriverObservationPort(input.transport(),input.driverAssembler(),actual.archive::preserveNativeFrame,input.observationAssembler(),16);
                    return RootMandatoryChoiceRuntime.observe(command,attempt,dispatch,new NativeEffectSnapshots(held,actual.archive,actual.frameLoader()),actual.archive,
                            (original,submitted,pair,projected)->journal.get().observedAfter(original,submitted,pair,projected)).result();
                },()->publishHint(owned.get(),advanced?"absent":"present",advanced?null:"receiver-1"),
                Optional.of(()->selectionResult(advanced)),Optional.empty(),false,
                Optional.of(new ActionPorts.PreparationPort(){
                    @Override public NativeRequest prepare(ActionCommand command){return RootMandatoryChoiceRuntime.prepareRequest(command,owned.get().archive);}
                }));
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve(name),false,readScenario,List.of(actionScenario))) {
            owned.set(actual);
            Path offline=Files.createDirectories(temporary.resolve(name+"-offline"));
            EventSourceReadContext configured=offlineSources(offline,actual.observationSource().machineId());
            Path manifest=configured.stateRoot().resolve("offline-grants.json");
            Path backend=offline.resolve("xar_ck3_bridge.dll");Files.writeString(backend,"synthetic software Native backend source");
            ExactRef backendRef=EpisodeIncidentJournal.measure(backend);
            EventSourceReadContext dynamic=new EventSourceReadContext(configured.machineId(),configured.stateRoot(),configured.stockGameRoot(),()->{
                try{return ProjectionEvidenceCodec.decode(EvidenceGrantManifestPublisher.readStable(manifest,ProjectionEvidenceCodec.MAX_BYTES));}
                catch(java.nio.file.NoSuchFileException absent){return List.of();}
                catch(IOException failed){throw new java.io.UncheckedIOException(failed);}
            });
            knowledge.set(new RootMandatoryChoiceRuntime.Knowledge(dynamic,backendRef));
            Path incidents=Files.createDirectories(offline.resolve("incidents")),scans=Files.createDirectories(offline.resolve("scans"));
            var journalConfiguration=new EpisodeIncidentJournal.Configuration(incidents,scans,java.time.Clock.systemUTC(),bytes->{},Optional.empty());
            actual.bindAdditionalBeforeIntent((same,command)->{
                try { journal.get().before(command).orElseThrow(); }
                catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
            });
            actual.bindAdditionalArchivedVerifier(RootMandatoryChoiceRuntime.archived(actual.observationSource().sourceRef(),actual.frameLoader()));
            actual.ready();publishHint(actual,"present","receiver-1");var seed=actual.command("ordinary-modal-seed");
            var selected=new AtomicReference<ActionCommand>();
            actual.writer.locked(same->actual.collector.current(same,seed.before(),Instant.now().plusSeconds(20),lease->{
                var frame=lease.frame();var caps=Set.of(RootMandatoryChoiceRuntime.CAPABILITY);
                var origin=new EpisodeIncidentJournal.Binding(frame.identity(),frame.source(),frame.sessionId());
                var basis=actual.archive.withSession(same).preserveMaterial(RootIncidentRuntime.originalObservationBasis(frame));
                journal.set(EpisodeIncidentJournal.initializeObserved(journalConfiguration,origin,basis));
                var steps=NativeActionSteps.candidates(new NativeActionSteps.Input(caps,frame.semantic(),List.of(),Set.of())).stream().map(OperationKey::new).collect(java.util.stream.Collectors.toUnmodifiableSet());
                assertTrue(steps.contains(new OperationKey(RootMandatoryChoiceRuntime.SELECT)));
                var observations=new PlanningObservation(frame.semantic(),List.of(),steps,caps,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
                var request=new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),Instant.now().plusSeconds(20),observations);
                var binding=EventReadBinding.actualReceipt(installed.get(),current->current.observations().snapshot(),PlanningReadResult.Known::value);
                var policy=EventPolicies.policies(frame.source().sourceRef(),Optional.empty(),(a,b,c,d)->Optional.empty(),actual.reads,List.of(binding),
                        (a,b)->Optional.of(b),(current,plan)->{RootIncidentRuntime.captureBlockedOriginal(journal.get(),current,plan,frame,actual.archive.withSession(same));},
                        (current,operation,args,plan,purpose,domain)->RootMandatoryChoiceRuntime.prepare(current,plan,actual.archive.withSession(same),knowledge.get()))
                        .stream().filter(value->value.stage()==PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS).findFirst().orElseThrow();
                var decision=policy.evaluate(request,OrdinaryPolicy.Draft.empty());
                if(name.equals("disabled-first")) {
                    assertEquals("first_displayed_native_choice_disabled",assertInstanceOf(OrdinaryPolicy.Wait.class,decision).reason());return null;
                }
                var replacement=assertInstanceOf(OrdinaryPolicy.Replace.class,decision);
                var command=replacement.draft().command().orElseThrow();selected.set(command);
                assertEquals(RootMandatoryChoiceRuntime.SELECT,command.operation().value());
                assertNotNull(command.arguments().get("mandatory_choice_original_read"));
                assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
                var nativeRequest=RootMandatoryChoiceRuntime.prepareRequest(command,actual.archive.withSession(same));
                assertEquals("opaque-token-1",StrictJson.parse(nativeRequest.additionalFields().bytes()).path("mandatory_choice_selection").path("action_token").textValue());
                var capture=OpportunityJson.object(command.arguments().get("unknown_mandatory_choice_v1"),"capture");
                var choice=OpportunityJson.object(capture.get("selection"),"choice").with("action_token",new OpportunityJson.Text("forged-token"));
                var changed=command.arguments().with("unknown_mandatory_choice_v1",capture.with("selection",choice));
                var forged=new ActionCommand(command.actionId(),command.before(),command.source(),command.sessionId(),command.operation(),changed,command.expected(),command.claims(),command.deadline());
                assertThrows(IllegalArgumentException.class,()->RootMandatoryChoiceRuntime.prepareRequest(forged,actual.archive.withSession(same)));
                return null;
            }));
            assertEquals(1,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());
            if(name.equals("disabled-first")) {
                assertNull(selected.get());var blocked=journal.get().scan(journal.get().origin());
                assertEquals(1,blocked.diagnosticOnly());assertEquals(0,blocked.incompleteAfter());
                var batch=blocked.batch().orElseThrow();var body=StrictJson.parse(Files.readAllBytes(Path.of(batch.capturedRefs().getFirst().path())));
                assertEquals("unknown_mandatory_choice",body.path("kind").textValue());assertTrue(body.path("selection").isNull());
                assertFalse(body.has("event_definition_key"));assertFalse(body.path("dispatch_attempted").booleanValue());
                assertEquals("receiver-1",body.path("mandatory_choice_hint").path("opaque_root_id").textValue());
                var choices=body.path("retained_history").get(0).path("result").path("mandatory_choice").path("choices");
                assertEquals(2,choices.size());assertEquals("choice-1",choices.get(1).path("choice_id").textValue());
                assertFalse(choices.get(1).path("enabled").booleanValue());
                assertEquals(1,choices.get(1).path("bounds").path("left").intValue());
                var beforeIndex=StrictJson.parse(Files.readAllBytes(Path.of(batch.capturedRefs().getFirst().path().replace(".before.json",".before-index.json"))));
                assertEquals("MANDATORY",beforeIndex.path("kind").textValue());assertTrue(beforeIndex.path("action_id").isNull());
                assertTrue(blocked.originals().contains(ExactRef.fromJson(beforeIndex.get("original_read_ref"))));
                var host=new OfflineEventAnalysisHost(Optional.of(knowledge.get().sources()),new OfflineEventAnalysisHost.Settings(true,false,Optional.of(manifest),
                        Optional.of(incidents),Optional.of(Files.createDirectories(offline.resolve("blocked-knowledge"))),Optional.of(scans)),Optional.of(journal.get()::acknowledge));
                var report=StrictJson.parse(host.batch(batch)).path("report");
                assertEquals(0,report.path("entries").size());assertEquals(1,report.path("unresolved").size());
                assertEquals("diagnostic_only",report.path("unresolved").get(0).path("status").textValue());
                var cold=EpisodeIncidentJournal.openOriginal(journalConfiguration,journal.get().episodeReference());
                assertEquals(List.of(batch),RootIncidentRuntime.retainedOriginalBatches(List.of(cold)));
                assertEquals(0,actual.nativeActionWrites());assertEquals(0,actual.snapshot().ledgerSequence());return;
            }
            ActionReceipt receipt=actual.coordinator.execute(selected.get());
            assertEquals(1,actual.nativeActionWrites());
            if(advanced) {
                var settled=assertInstanceOf(ActionState.Settled.class,receipt.state());
                var applied=assertInstanceOf(ActionState.Applied.class,settled.settlement());
                assertFalse(applied.observation().supportingEvidence().isEmpty());
                actual.writer.locked(same->{
                    var archive=actual.archive.withSession(same);
                    RootMandatoryChoiceRuntime.archived(actual.observationSource().sourceRef(),actual.frameLoader()).verifier().verify(same.head(),receipt,archive);
                    var original=NativeEffectEvidence.load(receipt,archive,actual.frameLoader());
                    assertEquals(1,original.independentReads().size());
                    assertFalse(StrictJson.parse(original.compatibleResult().bytes()).path("material_effects_verified").booleanValue());
                    return null;
                });
                verifyOfflineRoundTrip(actual,journal.get(),knowledge.get(),installed.get(),manifest,offline);
            } else {
                assertFalse(receipt.settled());assertEquals(receipt,actual.coordinator.execute(selected.get()));
                assertEquals(1,actual.nativeActionWrites(),"the same unresolved mandatory token must not be replayed");
                var unresolved=journal.get().scan(journal.get().origin());assertEquals(1,unresolved.incompleteAfter());
                assertFalse(Files.exists(configured.stateRoot().resolve("evidence/unknown-mandatory-choice-reviews/root-known-ui-recovery")));
            }
        }
    }

    private void verifyOfflineRoundTrip(ActionWriterIntegrationFixture actual,EpisodeIncidentJournal journal,RootMandatoryChoiceRuntime.Knowledge knowledge,
            ReadContract<EventPolicies.ReadPublication> query,Path manifest,Path offline)throws Exception {
        var host=new OfflineEventAnalysisHost(Optional.of(knowledge.sources()),new OfflineEventAnalysisHost.Settings(true,false,Optional.of(manifest),
                Optional.of(journal.configuration().incidentRoot()),Optional.of(Files.createDirectories(offline.resolve("knowledge"))),
                Optional.of(journal.configuration().scanRoot())),Optional.of(journal::acknowledge));
        var retained=RootIncidentRuntime.retainedOriginalBatches(List.of(EpisodeIncidentJournal.openOriginal(journal.configuration(),journal.episodeReference())));
        assertEquals(1,retained.size(),"ordinary batch-end source must retain this actual mandatory pair");
        var first=StrictJson.parse(host.batch(retained.getFirst()));assertEquals(1,first.path("report").path("unresolved").size(),
                "a removed receiver without actual later date progress cannot publish known recovery");
        publishProgress(actual);
        var ready=actual.ready();
        BatchRequest batch=actual.writer.locked(same->actual.collector.current(same,ready.request().before(),Instant.now().plusSeconds(20),lease->{
            var frame=lease.frame();var basis=actual.archive.withSession(same).preserveMaterial(RootIncidentRuntime.originalObservationBasis(frame));
            return journal.scan(new EpisodeIncidentJournal.Binding(frame.identity(),frame.source(),frame.sessionId()),Optional.of(basis)).batch().orElseThrow();
        }));
        verifyWorkerCompletion(host,batch,knowledge.sources(),manifest,offline);
        var response=StrictJson.parse(host.batch(batch));var report=response.path("report");
        assertEquals(1,report.path("entries").size(),()->report.toString());assertEquals(0,report.path("unresolved").size());
        assertEquals("unknown_mandatory_choice",report.path("entries").get(0).path("kind").textValue());
        assertFalse(report.path("entries").get(0).path("business_effect_known").booleanValue());
        assertFalse(report.path("entries").get(0).path("semantic_optimal").booleanValue());
        assertEquals(0,response.path("Game_MCP_OBS_calls").intValue());assertEquals(0,response.path("timeline_writer_calls").intValue());
        assertTrue(RootIncidentRuntime.retainedOriginalBatches(List.of(EpisodeIncidentJournal.openOriginal(journal.configuration(),journal.episodeReference()))).isEmpty(),
                "real offline completion ACK removes this exact source-reviewed pair from the original journal");
        assertEquals(report,StrictJson.parse(host.batch(batch)).path("report"),"same captured cohort replays the exact immutable review");
        publishHint(actual,"present","receiver-2");var next=actual.ready();
        ActionCommand nextCommand=actual.writer.locked(same->actual.collector.current(same,next.request().before(),Instant.now().plusSeconds(20),lease->{
            var frame=lease.frame();var caps=Set.of(RootMandatoryChoiceRuntime.CAPABILITY);
            var steps=NativeActionSteps.candidates(new NativeActionSteps.Input(caps,frame.semantic(),List.of(),Set.of())).stream().map(OperationKey::new).collect(java.util.stream.Collectors.toUnmodifiableSet());
            var observations=new PlanningObservation(frame.semantic(),List.of(),steps,caps,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
            var planning=new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),Instant.now().plusSeconds(20),observations);
            var policy=EventPolicies.policies(frame.source().sourceRef(),Optional.empty(),(a,b,c,d)->Optional.empty(),actual.reads,
                    List.of(EventReadBinding.actualReceipt(query,current->current.observations().snapshot(),PlanningReadResult.Known::value)),(a,b)->Optional.of(b),
                    (a,b)->{throw new AssertionError("next native modal should continue with its new actual token");},
                    (current,operation,args,plan,purpose,domain)->RootMandatoryChoiceRuntime.prepare(current,plan,actual.archive.withSession(same),knowledge))
                    .stream().filter(value->value.stage()==PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS).findFirst().orElseThrow();
            return assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluate(planning,OrdinaryPolicy.Draft.empty())).draft().command().orElseThrow();
        }));
        var fact=OpportunityJson.object(nextCommand.arguments().get("known_ui_recovery_source"),"actual next-round Root source fact");
        assertEquals(new OpportunityJson.Text("observed-UI"),fact.get("known_recovery_source"));
        assertEquals(new OpportunityJson.Bool(false),fact.get("business_effect_known"));
        var sent=actual.writer.locked(same->RootMandatoryChoiceRuntime.prepareRequest(nextCommand,actual.archive.withSession(same)));
        assertEquals("opaque-token-2",StrictJson.parse(sent.additionalFields().bytes()).path("mandatory_choice_selection").path("action_token").textValue(),
                "knowledge must never reuse the historical instance/action token");
        assertEquals(1,actual.nativeActionWrites(),"offline analysis and next-round recognition do not submit an action");
        ObjectNode changed=(ObjectNode)StrictJson.parse(OpportunityJson.encode(nextCommand.arguments()));
        var window=changed.path("unknown_mandatory_choice_v1").path("native_window");
        ExactRef before=ExactRef.fromJson(StrictJson.parse(Files.readAllBytes(Path.of(report.path("entries").get(0).path("published").path("path").textValue()))).get("before_ref"));
        Files.writeString(Path.of(before.path())," ",java.nio.file.StandardOpenOption.APPEND);
        assertTrue(new UiRecoveryEvidenceLookup(knowledge.sources()).lookupRoot(window,BigInteger.valueOf(nextCommand.before().game().pid()),knowledge.backend()).isEmpty(),
                "changed historical source SHA cannot retain known status or overwrite its immutable fact");
    }
    private static void verifyWorkerCompletion(OfflineEventAnalysisHost host,BatchRequest batch,EventSourceReadContext sources,Path manifest,Path offline)throws Exception {
        var files=new org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles();
        var io=new org.xar.ck3.control.contracts.offline.OfflineAnalysisFiles.Port() {
            private void bound(Path path){assertTrue(path.startsWith(offline));}
            @Override public void directories(Path path)throws IOException{bound(path);Files.createDirectories(path);}
            @Override public ExactRef createNew(Path path,byte[] raw)throws IOException{bound(path);return files.createNew(path,raw).reference();}
            @Override public ExactRef replace(Path path,byte[] raw)throws IOException{bound(path);return files.replace(path,raw).reference();}
            @Override public void beforeLock(Path path){bound(path);}
            @Override public void beforeLink(Path path,long bytes){bound(path);assertTrue(bytes>0);}
        };
        var scope=host.batchScope().orElseThrow();
        var binding=new org.xar.ck3.control.service.OfflineAnalysisWorker.Binding(sources.machineId(),sources.stateRoot(),sources.stockGameRoot(),
                scope.incidentRoot(),scope.scanRoot().orElseThrow(),scope.knowledgeRoot(),manifest);
        var settings=new org.xar.ck3.control.service.OfflineAnalysisWorker.Settings(offline.resolve("offline-worker"),2,8);
        org.xar.ck3.control.application.session.SessionPorts.AnalysisCompletion completed;
        try(var worker=new org.xar.ck3.control.service.OfflineAnalysisWorker(settings,files,io)) {
            var port=worker.bind(host,binding,io);
            completed=port.enqueue(batch).completion().toCompletableFuture().get(30,java.util.concurrent.TimeUnit.SECONDS);
            assertEquals(batch.batchId(),completed.batchId());
            assertEquals(completed,port.enqueue(batch).completion().toCompletableFuture().get(30,java.util.concurrent.TimeUnit.SECONDS));
            Path canonical=sources.stateRoot().resolve("evidence/unknown-mandatory-choice-reviews/root-known-ui-recovery");
            assertTrue(completed.persistedReviews().stream().anyMatch(ref->Path.of(ref.path()).startsWith(canonical)),
                    "actual worker completion must retain the mandatory producer's canonical fact");
            assertNotEquals(manifest,Path.of(completed.publishedKnowledge().path()));
            worker.close();worker.drainCompletion().toCompletableFuture().get(30,java.util.concurrent.TimeUnit.SECONDS);
        }
        try(var restored=new org.xar.ck3.control.service.OfflineAnalysisWorker(settings,files,io)) {
            assertEquals(completed,restored.bind(host,binding,io).enqueue(batch).completion().toCompletableFuture().get(30,java.util.concurrent.TimeUnit.SECONDS),
                    "durable worker replay must validate every original mandatory output and immutable knowledge snapshot");
            restored.close();restored.drainCompletion().toCompletableFuture().get(30,java.util.concurrent.TimeUnit.SECONDS);
        }
        try(var entries=Files.list(settings.workRoot())) {
            assertFalse(entries.anyMatch(path->path.getFileName().toString().endsWith(".failure.json")));
        }
    }
    private static void publishProgress(ActionWriterIntegrationFixture actual)throws IOException {
        var original=actual.physicalInputs().transport().latestObservedSnapshot().orElseThrow();
        ObjectNode state=(ObjectNode)StrictJson.parse(original.state().bytes());
        state.put("date_raw",state.path("date_raw").bigIntegerValue().add(BigInteger.valueOf(org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.TICKS_PER_DAY)));
        BigInteger next=original.nativeRevision().add(BigInteger.ONE);
        ObjectNode packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","mandatory-progress-"+next).put("revision",next);
        packet.set("state",state);actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(packet)));
    }
    /** Real immutable source corpus; original TrustedEventSourceContext guards remain enabled. */
    private static EventSourceReadContext offlineSources(Path output,String machine)throws IOException {
        return RootBlockedPendingIncidentTest.offlineSources(output,machine);
    }

    private static RawJson queryResult(NativeRequest request,int generation) {
        boolean disabled=generation<0;generation=Math.abs(generation);
        ObjectNode fields=(ObjectNode)StrictJson.parse(request.additionalFields().bytes());
        ObjectNode frame=(ObjectNode)fields.get("mandatory_choice_frame_binding");
        ObjectNode result=StrictJson.object().put("step",RootMandatoryChoiceRuntime.QUERY).put("accepted",true).put("status","available").put("owner_verified",true).put("unavailable_reason","");
        for(String key:List.of("snapshot_id","revision","native_revision"))result.set("queried_"+key,frame.get(key));
        ObjectNode window=result.putObject("mandatory_choice").put("schema","xar.native-mandatory-choice-window/v1").put("query_id","query-native-"+generation)
                .put("window_id","synthetic-modal").put("window_instance_id","receiver-"+generation).put("window_type","unknown_modal")
                .put("exclusive_modal",true).put("blocks_input",true).put("choices_complete",true);
        window.set("frame_binding",frame.deepCopy());
        var choice=window.putArray("choices").addObject().put("choice_id","choice-1").put("visible",true).put("enabled",true).put("is_choice",true)
                .put("action_token","opaque-token-"+generation).put("role","option").put("rendered_index",0).put("native_index",0);
        choice.putObject("bounds").put("top",1).put("left",1).put("width",100).put("height",20);
        var source=window.putObject("source_identity").put("game_exe_sha256",EventWindowModels.Build.TOURS.sha256())
                .putNull("backend_sha256").put("native_adapter_id","synthetic-source-adapter").put("root_runtime_name","SyntheticMandatory")
                .put("root_type","synthetic-native-gui").put("root_vtable_module_rva","ck3.exe+0x1000");
        var catalogue=source.putArray("choice_catalogue").addObject().put("choice_id","choice-1").put("runtime_name","SyntheticOption")
                .put("widget_vtable_module_rva","ck3.exe+0x2000").put("role","option");
        catalogue.putArray("callback_identities").addObject().put("vtable_module_rva","ck3.exe+0x3000").put("function_module_rva","ck3.exe+0x4000");
        if(disabled) {
            choice.put("enabled",false);
            var later=choice.deepCopy().put("enabled",true).put("choice_id","choice-2").put("action_token","later-enabled");
            ((ObjectNode)later.get("bounds")).put("left",200);
            ((com.fasterxml.jackson.databind.node.ArrayNode)window.get("choices")).removeAll().add(later).add(choice);
        }
        return new RawJson(StrictJson.canonical(result));
    }
    private static RawJson selectionResult(boolean advanced) {
        var result=StrictJson.object().put("step",RootMandatoryChoiceRuntime.SELECT).put("accepted",true).put("status","verification_pending")
                .put("owner_verified",true).put("selected_choice_id","choice-1").put("dispatch_attempted",true).put("dispatch_invoked",true)
                .put("native_handled",true).put("verification_pending",true).put("dispatch_stage","callback_returned").put("dispatch_exception_code",0);
        result.putObject("mandatory_choice_postcondition").put("verified",true).put("old_window_id","synthetic-modal").put("old_instance","receiver-1")
                .put("selected_choice_id","choice-1").put("old_window_no_longer_blocking",advanced).put("source","fresh_native_modal_receiver_vector_no_old_widget_dereference");
        return new RawJson(StrictJson.canonical(result));
    }
    private static void publishHint(ActionWriterIntegrationFixture actual,String status,String root)throws java.io.IOException {
        var original=actual.physicalInputs().transport().latestObservedSnapshot().orElseThrow();
        ObjectNode state=(ObjectNode)StrictJson.parse(original.state().bytes());
        ObjectNode hint=state.putObject("top_exclusive_modal_choice_hint").put("status",status)
                .put("source","application_main_pump_observed_modal_receiver").put("owner_verified",true).put("max_observation_age_ms",2000);
        if(root==null)hint.putNull("opaque_root_id");else hint.put("opaque_root_id",root);
        BigInteger next=original.nativeRevision().add(BigInteger.ONE);
        ObjectNode packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","mandatory-software-"+next).put("revision",next);
        packet.set("state",state);actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(packet)));
    }
}
