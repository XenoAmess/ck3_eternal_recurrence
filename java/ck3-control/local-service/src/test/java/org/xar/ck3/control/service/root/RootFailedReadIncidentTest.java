package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Map;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.application.planning.warexit.WarExitReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatFrames;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.EventReadBinding;
import org.xar.ck3.control.application.planning.events.EventIncidentCapturePort;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineScanSource;

/** Actual software native packet/read pipeline -> shared production DATA capture -> cold journal/wire.
 * Existing event17 is reused. No private Current, parent, ManagedGame, Ready or success receipt is invented.
 * The original fixture supplies its own ordinary source; this is not a Natural/whole-Root qualification. */
final class RootFailedReadIncidentTest {
    @TempDir Path temporary;
    private static ObjectNode original;
    @BeforeAll static void originalInputs() throws Exception { original = PendingUiEventOriginalTestInputs.load(); }

    @Test void actualReadFailuresRetainTheirOriginalsWithoutSuccessfulReadOrActionCredit() throws Exception {
        for (String caseName : List.of("negative_ack", "response_lost", "malformed_payload", "capture_failure", "opaque_after", "mandatory_response_lost")) {
            boolean mandatory=caseName.startsWith("mandatory_");String fault=mandatory?caseName.substring("mandatory_".length()):caseName;
            String capability=mandatory?RootMandatoryChoiceRuntime.CAPABILITY:EventWindowRead.CAPABILITY;
            var installed = new AtomicReference<ReadContract<EventPolicies.ReadPublication>>();
            var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario(EventWindowModels.Build.TOURS.sha256().toLowerCase(java.util.Locale.ROOT),
                    "ck3-" + EventWindowModels.Build.TOURS.version() + "-msvc-x64", source -> {
                        var contract = mandatory?RootMandatoryChoiceRuntime.contract(source,request->{ }):EventWindowRead.contract(source, request -> { }); installed.set(contract); return List.of(contract);
                    }, request -> new RawJson(new byte[]{123,125}), Optional.of(EventWindowModels.Build.TOURS.version()),
                    Set.of(capability));
            try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(caseName), false, scenario,
                    originalGuard -> fault.equals("opaque_after") ? unavailableAfterGuard(originalGuard) : originalGuard.guard())) {
                if (Set.of("negative_ack", "capture_failure", "opaque_after").contains(fault)) actual.rejectNextScenarioRead();
                if (fault.equals("response_lost")) actual.loseReadAckOnce();
                // The malformed-payload case receives the actual empty object through NativeWire;
                // a source without OriginalReadDecodeFailure keeps that typed marker false.
                // No Unavailable or opaque attempt object is made by this test.
                existingForeground(actual,mandatory);
                var command = actual.command("existing-event-failed-read");
                Instant deadline = Instant.now().plusSeconds(20);
                var callbacks = new AtomicInteger(); var completed = new AtomicInteger();
                var typedDecode = new AtomicReference<Boolean>(); var denyCapture = new AtomicBoolean();
                actual.writer.locked(same -> actual.collector.current(same, command.before(), deadline, lease -> {
                    var frame = lease.frame(); var contract = installed.get();
                    var request = new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId(),
                            contract.operation(), frame.semantic(), deadline);
                    var archive = actual.archive.withSession(same);
                    var binding = new EpisodeIncidentJournal.Binding(frame.identity(), frame.source(), frame.sessionId());
                    var configured = new EpisodeIncidentJournal.Configuration(
                            Files.createDirectory(actual.root.resolve("m2-incidents")), Files.createDirectory(actual.root.resolve("m2-scans")),
                            Clock.systemUTC(),
                            bytes -> {
                                if (denyCapture.get()) throw new java.io.IOException("actual incident capture I/O denied");
                                if (bytes < 0 || bytes > (1 << 20)) throw new java.io.IOException("finite fixture output");
                            }, Optional.empty());
                    var journal = EpisodeIncidentJournal.initializeObserved(configured, binding,
                            archive.preserveMaterial(RootIncidentRuntime.originalObservationBasis(frame)));
                    var beforeHead = same.head().digest(); int nativeBaseline = actual.nativeReadWrites();
                    var ticket = new AtomicReference<EpisodeIncidentJournal.Ticket>();
                    denyCapture.set(fault.equals("capture_failure"));
                    var planning=new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),deadline,
                            new PlanningObservation(frame.semantic(),List.of(),Set.of(),Set.of(capability),
                                    Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
                    assertEquals(Optional.of(mandatory?EpisodeIncidentJournal.Kind.MANDATORY:EpisodeIncidentJournal.Kind.EVENT),
                            org.xar.ck3.control.application.planning.events.NativeWindowDiagnostic.foregroundKind(frame.semantic()));
                    var unavailableRead=new AtomicReference<PlanningReadResult.Unavailable<?>>();
                    EventIncidentCapturePort captures=new EventIncidentCapturePort() {
                        @Override public void captureBlocked(PlanningRequest source,OpportunityJson.Obj retained){throw new AssertionError("binding must invoke the actual failed READ observer");}
                        @Override public <T> PlanningReadResult<T> read(PlanningReadPort reads,ReadContract<T> exact,PlanningReadRequest requested,PlanningRequest source) {
                            assertSame(actual.reads,reads);assertSame(planning,source);
                            var result = reads.readWithFailureEvidence(same,exact,requested,
                            (borrowed, identical, requestedOriginal, unavailable, attempted, originals) -> {
                                assertEquals(requested,requestedOriginal);
                                assertSame(same, borrowed); assertSame(contract, identical); assertEquals(request, requested);
                                attempted.orElseThrow().requireOriginal(borrowed, identical, requested, unavailable, originals);
                                typedDecode.set(unavailable.decodeFailure().isPresent());
                                callbacks.incrementAndGet();
                                ticket.set(RootIncidentRuntime.captureOrdinaryReadFailureOriginal(journal,borrowed,source,frame,identical,requested,unavailable,attempted,originals));
                                completed.incrementAndGet();
                            });
                            unavailableRead.set(missing(result));
                            return result;
                        }
                    };
                    var route=EventReadBinding.actualReceipt(contract,source->source.observations().snapshot(),
                            (known)->{throw new AssertionError("failed READ cannot publish Known");});
                    var outcome = route.read(actual.reads,planning,contract.operation(),captures);
                    var unavailable = java.util.Objects.requireNonNull(unavailableRead.get());
                    var bindingUnavailable = assertInstanceOf(org.xar.ck3.control.application.planning.events.EventReadBinding.Unavailable.class, outcome);
                    assertSame(unavailable, bindingUnavailable.result());
                    sameFailure(unavailable, bindingUnavailable.result());
                    assertEquals(1, callbacks.get());
                    assertEquals(nativeBaseline + 1, actual.nativeReadWrites()); assertEquals(1, actual.scenarioReadWrites());
                    assertEquals(0, actual.nativeActionWrites()); assertEquals(beforeHead, same.head().digest());
                    denyCapture.set(false);
                    if (fault.equals("capture_failure")) {
                        assertEquals(0, completed.get()); assertNull(ticket.get());
                        assertTrue(unavailable.reason().contains("original failed-read evidence observer unavailable:IOException:actual incident capture I/O denied"));
                        // A genuine failed READ may retain its original after proof while incident DATA capture fails.
                        // That proof does not mean this observer completed or that any window was selected.
                        assertTrue(unavailable.observedFailure().isPresent());
                        var scan = journal.scan(binding);
                        assertEquals(0, scan.incidents()); assertEquals(0, scan.diagnosticOnly()); assertTrue(scan.batch().isEmpty());
                        var reopened = EpisodeIncidentJournal.open(configured, binding, journal.episodeReference());
                        assertTrue(RootIncidentRuntime.retainedOriginalBatches(List.of(reopened)).isEmpty());
                        try (var files = Files.list(configured.incidentRoot())) {
                            assertTrue(files.noneMatch(path -> path.getFileName().toString().endsWith(".before-index.json")
                                    || path.getFileName().toString().endsWith(".review-index.json")));
                        }
                    } else {
                        assertEquals(1, completed.get()); assertNotNull(ticket.get());
                        assertCardAndColdScan(journal, configured, binding, ticket.get(), archive, fault, typedDecode.get());
                    }
                    return null;
                }));
                assertEquals(0, actual.snapshot().ledgerSequence());
            }
        }
    }

    @Test void fixedWindowDefinitionBorrowsOriginalFrameAndSendsTypedQueryWithoutHistoricalGetter() throws Exception {
        for (String operation : List.of("query-war-results-window-v1", "query-war-declared-overview-v1")) {
            String capability="game.command."+operation;
            var installed=new AtomicReference<ReadContract<RawJson>>();
            var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(EventWindowModels.Build.TOURS.sha256().toLowerCase(java.util.Locale.ROOT),
                    "ck3-"+EventWindowModels.Build.TOURS.version()+"-msvc-x64",source->{
                        var contract=new ReadContract<RawJson>("actual-fixed-window-read-"+operation,new OperationKey(operation),
                                Optional.of(capability),capability,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                                ReadContract.WireProfile.EXECUTE_STEP,source,
                                request->new NativeRequest(operation,Optional.of(capability),new RawJson(new byte[]{123,125})),
                                receipt->receipt.original().originalFrame());
                        installed.set(contract);return List.of(contract);
                    },request->new RawJson(new byte[]{123,125}),Optional.of(EventWindowModels.Build.TOURS.version()),Set.of(capability));
            try(var actual=new ActionWriterIntegrationFixture(temporary.resolve(operation),false,scenario)) {
                var historicalReplays=new AtomicInteger();
                actual.collector.bindPlanningEvidence((same,request,lease)->{
                    historicalReplays.incrementAndGet();throw new IOException("historical planning getter is deliberately unavailable");
                });
                var planning=actual.ready().request();actual.rejectNextScenarioRead();
                actual.writer.locked(same->actual.collector.current(same,planning.before(),planning.deadline(),outer->{
                    String head=same.head().digest();int before=actual.nativeReadWrites();
                    return EventRuntimeInstaller.fixedWindowFrame(actual.collector,same,planning,held->{
                        assertSame(outer.frame(),held.frame());assertEquals(planning.source(),held.frame().source());
                        var request=new PlanningReadRequest(planning.before(),planning.source(),planning.sessionId(),
                                new OperationKey(operation),new Obj(Map.of()),planning.deadline());
                        var result=actual.reads.read(same,installed.get(),request);
                        var unavailable=missing(result);
                        var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original().orElseThrow());
                        assertFalse(ack.nativeOk());assertEquals(before+1,actual.nativeReadWrites());
                        assertEquals(1,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());
                        assertEquals(head,same.head().digest());assertEquals(0,historicalReplays.get());
                        return null;
                    });
                }));
            }
        }
    }

    @Test void fixedWindowDefinitionRejectsSourceDriftAndRetainsOriginalIoCause() throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("fixed-window-drift"),false)) {
            var command=actual.command("fixed-window-definition-drift");
            actual.writer.locked(same->actual.collector.current(same,command.before(),command.deadline(),lease->{
                var original=failurePlanning(lease.frame(),command.deadline());
                var foreignSource=new org.xar.ck3.control.g2.common.G2Source(original.source().machineId(),
                        "2026-10-29T00:00:00Z","different-fixed-window-source",original.source().sourceRef());
                var crossed=new PlanningRequest(original.before(),foreignSource,original.sessionId(),original.deadline(),original.observations());
                var callbacks=new AtomicInteger();int reads=actual.nativeReadWrites();
                assertThrows(IllegalArgumentException.class,()->EventRuntimeInstaller.fixedWindowFrame(actual.collector,same,crossed,
                        held->{callbacks.incrementAndGet();return null;}));
                assertEquals(0,callbacks.get());assertEquals(reads,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());
                return null;
            }));
        }
        var original=new IOException("actual fixed-window definition source unavailable");
        var wrapped=EventRuntimeInstaller.fixedWindowFailure(original);
        assertSame(original,wrapped.getCause());
        assertTrue(wrapped.getMessage().contains("IOException:actual fixed-window definition source unavailable"));
    }

    private static final PlanningReadPort NO_TERMINATION_READS=new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            throw new AssertionError("Army family installation cannot submit a detached read");
        }
    };
    @TempDir Path terminationFailures;
    private enum TerminationFault { MALFORMED, NEGATIVE_ACK, RESPONSE_LOST }
    private static <T> PlanningReadResult.Unavailable<T> missing(PlanningReadResult<T> value) {
        if(value instanceof PlanningReadResult.Unavailable<T> failed)return failed;
        throw new AssertionError("failed original READ cannot become Known");
    }
    private static void sameFailure(PlanningReadResult.Unavailable<?> original,PlanningReadResult.Unavailable<?> returned) {
        assertEquals(original.reason(),returned.reason());
        assertEquals(original.original(),returned.original());
        assertEquals(original.decodeFailure(),returned.decodeFailure());
        assertEquals(original.observedFailure(),returned.observedFailure());
        original.original().ifPresent(value->assertSame(value,returned.original().orElseThrow()));
        original.decodeFailure().ifPresent(value->assertSame(value,returned.decodeFailure().orElseThrow()));
        original.observedFailure().ifPresent(value->assertSame(value,returned.observedFailure().orElseThrow()));
    }
    private static PlanningRequest failurePlanning(Complete frame,Instant deadline) {
        return new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),deadline,
                new PlanningObservation(frame.semantic(),List.of(),Set.of(),Set.of(),
                        Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static PlanningReadResult.Unavailable<WarExitReads.Query> routeTerminationFailure(
            ActionWriterIntegrationFixture actual,Session same,Complete frame,Instant deadline,ArmyWarReads wars,
            PlanningReadPort originalReads,WarExitReads.Kind kind,AtomicReference<PlanningReadResult.Unavailable<Obj>> intermediate) {
        var current=failurePlanning(frame,deadline);var key=new WarExitReads.Key(kind,77);
        var call=MilitaryNativeReadDispatcher.termination(WarExitReads.step(key),
                new ArmyCalls.Revision(new ArmyTypes.Present<>(frame.identity().frame().revision()))).orElseThrow();
        var selected=new ArmyWarReads.Selection(call,new ArmyRetreatFrames.Current(frame,deadline),Optional.empty());
        var readers=new WarExitReads((planning,subject,arguments)->RootWarCoreFactory.dispatchExit(planning,subject,arguments,
                (samePlanning,selection)->{
                    assertSame(current,samePlanning);assertEquals(new OperationKey(WarExitReads.step(key)),selection.operation());
                    var result=MilitaryNativeReadDispatcher.termination(wars,originalReads,same,actual.actualReadCatalog(),selected);
                    intermediate.set(missing(result));return result;
                }));
        var result=missing(readers.read(current,key,new Obj(Map.of())));
        sameFailure(intermediate.get(),result);return result;
    }
    private static void retainedFailureRoundtrip(PlanningReadFailure failure,ActionPorts.OutcomeArchive originals) {
        originals.verifyReadFailureOriginals(failure);
        ExactRef ref=PlanningReadFailureCodec.preserve(failure,originals);
        assertEquals(failure,PlanningReadFailureCodec.load(ref,originals));
        assertEquals(failure.original(),originals.load(failure.originalRef()));
        assertEquals(failure.prepared(),originals.loadRequest(failure.preparedRef()));
        for(int fault=0;fault<3;fault++) {
            var row=assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                    StrictJson.parse(originals.loadMaterial(ref).bytes()));
            switch(fault) {
                case 0->row.remove("after");
                case 1->row.put("head_sequence",true);
                case 2->assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                        row.path("request").path("source")).put("machine_id","foreign-failed-read-source");
                default->throw new AssertionError();
            }
            var bad=originals.preserveMaterial(new RawJson(StrictJson.canonical(row)));
            assertThrows(RuntimeException.class,()->PlanningReadFailureCodec.load(bad,originals));
        }
        assertEquals(failure,PlanningReadFailureCodec.load(ref,originals),"rejected mutations cannot repair the original");
    }
    private static final class TerminationDecodeFailure extends IllegalArgumentException implements OriginalReadDecodeFailure {
        private static final long serialVersionUID=1L;
        private final ReadContract<?> installed;private final PlanningReadReceipt original;
        private TerminationDecodeFailure(ReadContract<?> installed,PlanningReadReceipt original) {
            super("controlled original live decoder failure");this.installed=installed;this.original=original;
        }
        @Override public void requireOriginal(ReadContract<?> contract,PlanningReadRequest request,PlanningReadReceipt receipt) {
            StrictJson.require(installed==contract&&original==receipt&&original.request()==request,
                    "typed failure lost its identical live software decoder/request/receipt");
        }
    }
    @Test void actualArmyTerminationFailuresKeepOriginalAfterThroughBothDispatchersAndArchive()throws Exception {
        for(var kind:List.of(WarExitReads.Kind.OPTIONS,WarExitReads.Kind.TERMS))for(var fault:TerminationFault.values()) {
            var wars=new AtomicReference<ArmyWarReads>();
            var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"termination-failure-fields",
                    source->List.of(),request->new RawJson(new byte[]{123,125}),Optional.empty(),Set.of(),
                    source->{var value=new ArmyWarReads(source,source,NO_TERMINATION_READS);wars.set(value);return value.families();});
            try(var actual=new ActionWriterIntegrationFixture(terminationFailures.resolve(kind+"-"+fault),false,scenario)) {
                if(fault==TerminationFault.NEGATIVE_ACK)actual.rejectNextScenarioRead();
                if(fault==TerminationFault.RESPONSE_LOST)actual.loseReadAckOnce();
                var command=actual.command("termination-fields-"+kind+"-"+fault);
                var captured=new AtomicReference<PlanningReadResult.Unavailable<?>>();
                String operation=WarExitReads.step(new WarExitReads.Key(kind,77));
                actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                    @Override public void afterKnown(Session same,ReadContract<?> contract,PlanningReadResult.Known<?> value) {
                        if(contract.operation().value().equals(operation))fail("malformed or failed READ cannot publish Known");
                    }
                    @Override public void afterUnavailable(Session same,ReadContract<?> contract,PlanningReadRequest request,
                            PlanningReadResult.Unavailable<?> value,Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
                        if(!contract.operation().value().equals(operation))return;
                        try{attempted.orElseThrow().requireOriginal(same,contract,request,value,actual.archive.withSession(same));}
                        catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                        captured.set(value);
                    }
                });
                ExactRef source=actual.observationSource().sourceRef();byte[] sourceBytes=Files.readAllBytes(Path.of(source.path()));
                actual.writer.locked(same->{
                    var observedAfter=actual.collector.current(same,command.before(),command.deadline(),lease->{
                    int baseline=actual.nativeReadWrites();String head=same.head().digest();
                    var middle=new AtomicReference<PlanningReadResult.Unavailable<Obj>>();
                    var returned=routeTerminationFailure(actual,same,lease.frame(),command.deadline(),wars.get(),actual.reads,kind,middle);
                    sameFailure(java.util.Objects.requireNonNull(captured.get()),middle.get());
                    sameFailure(captured.get(),returned);
                    assertTrue(returned.decodeFailure().isEmpty(),"current Army decoder does not mint live typed failure custody");
                    var observed=returned.observedFailure().orElseThrow();
                    assertEquals(lease.frame().source(),observed.request().source());assertEquals(source,observed.request().source().sourceRef());
                    if(fault==TerminationFault.RESPONSE_LOST)assertInstanceOf(NativeActionPort.Unknown.class,returned.original().orElseThrow());
                    else assertEquals(fault==TerminationFault.MALFORMED,
                            assertInstanceOf(NativeActionPort.AckReceived.class,returned.original().orElseThrow()).nativeOk());
                    assertEquals(baseline+1,actual.nativeReadWrites());assertEquals(1,actual.scenarioReadWrites());
                    assertEquals(0,actual.nativeActionWrites());assertEquals(head,same.head().digest());return observed;
                    });
                    retainedFailureRoundtrip(observedAfter,actual.archive.withSession(same));
                    assertEquals(1,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());
                    assertEquals(0,same.head().state().sequence());return null;
                });
                assertArrayEquals(sourceBytes,Files.readAllBytes(Path.of(source.path())));
                assertEquals(0,actual.snapshot().ledgerSequence());
            }
        }
    }
    @Test void typedLiveDecoderFailureRemainsOriginalCustodyAcrossBothUnavailableCovariances()throws Exception {
        var installed=new AtomicReference<ReadContract<RawJson>>();
        var thrown=new AtomicReference<TerminationDecodeFailure>();var wars=new AtomicReference<ArmyWarReads>();
        var operation=new OperationKey("query-war-termination-options-77");
        String capability=WarExitReads.capability(WarExitReads.Kind.OPTIONS);
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"termination-typed-failure",source->{
            var contract=new ReadContract<RawJson>("termination-live-software-decoder/v1",operation,Optional.of(capability),
                    "termination-live-software-decoder",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                    ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(operation.value(),capability,new RawJson(new byte[]{123,125})),
                    receipt->{var failure=new TerminationDecodeFailure(installed.get(),receipt);thrown.set(failure);throw failure;},
                    receipt->{throw new IllegalArgumentException("pure replay cannot mint live decoder custody");});
            installed.set(contract);return List.of(contract);
        },request->new RawJson(new byte[]{123,125}),Optional.empty(),Set.of(),source->{
            var value=new ArmyWarReads(source,source,NO_TERMINATION_READS);wars.set(value);return value.families();
        });
        try(var actual=new ActionWriterIntegrationFixture(terminationFailures.resolve("typed-decode"),false,scenario)) {
            var command=actual.command("termination-typed-failure");
            actual.writer.locked(same->{
                var observedAfter=actual.collector.current(same,command.before(),command.deadline(),lease->{
                int baseline=actual.nativeReadWrites();var captured=new AtomicReference<PlanningReadResult.Unavailable<?>>();
                var requestedArmy=new AtomicReference<ReadContract<?>>();
                // Only this controlled software decoder produces a typed marker. Army currently produces none.
                // The covariant port preserves the actual result; it cannot rebind that marker to the Army decoder.
                PlanningReadPort originalFailure=new PlanningReadPort() {
                    @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("same writer required");}
                    @Override public <T> PlanningReadResult<T> read(Session borrowed,ReadContract<T> contract,PlanningReadRequest request) {
                        assertSame(same,borrowed);assertEquals(operation,contract.operation());
                        assertEquals(installed.get().sourceRef(),contract.sourceRef());requestedArmy.set(contract);
                        var result=missing(actual.reads.readWithFailureEvidence(borrowed,installed.get(),request,
                                (locked,exact,current,value,attempted,originals)->{
                                    attempted.orElseThrow().requireOriginal(locked,exact,current,value,originals);captured.set(value);
                                }));
                        return new PlanningReadResult.Unavailable<>(result.reason(),result.original(),result.decodeFailure(),result.observedFailure());
                    }
                };
                var middle=new AtomicReference<PlanningReadResult.Unavailable<Obj>>();
                var returned=routeTerminationFailure(actual,same,lease.frame(),command.deadline(),wars.get(),originalFailure,
                        WarExitReads.Kind.OPTIONS,middle);
                sameFailure(java.util.Objects.requireNonNull(captured.get()),middle.get());sameFailure(captured.get(),returned);
                var marker=thrown.get();assertSame(marker,returned.decodeFailure().orElseThrow());
                marker.requireOriginal(installed.get(),marker.original.request(),marker.original);
                assertThrows(IllegalArgumentException.class,()->marker.requireOriginal(requestedArmy.get(),marker.original.request(),marker.original));
                assertThrows(IllegalArgumentException.class,()->new PlanningReadResult.Unavailable<>("missing original",
                        Optional.empty(),returned.decodeFailure(),Optional.empty()));
                assertThrows(IllegalArgumentException.class,()->new PlanningReadResult.Unavailable<>("foreign original",
                        Optional.empty(),Optional.empty(),returned.observedFailure()));
                assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class,returned.original().orElseThrow()).nativeOk());
                assertThrows(IllegalArgumentException.class,()->installed.get().replay(marker.original));
                assertEquals(baseline+1,actual.nativeReadWrites());assertEquals(1,actual.scenarioReadWrites());
                assertEquals(0,actual.nativeActionWrites());assertEquals(0,same.head().state().sequence());return returned.observedFailure().orElseThrow();
                });
                retainedFailureRoundtrip(observedAfter,actual.archive.withSession(same));
                assertEquals(1,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());
                assertEquals(0,same.head().state().sequence());return null;
            });
        }
    }
    @Test void actualTerminationPreflightFailureCannotAcquireOriginalAfterOrDecoderCustody()throws Exception {
        var wars=new AtomicReference<ArmyWarReads>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"termination-preflight",
                source->List.of(),request->{throw new AssertionError("preflight failure cannot submit a scenario READ");},
                Optional.empty(),Set.of(),source->{
                    var value=new ArmyWarReads(source,source,NO_TERMINATION_READS);wars.set(value);return value.families();
                });
        try(var actual=new ActionWriterIntegrationFixture(terminationFailures.resolve("preflight"),false,scenario)) {
            var command=actual.command("termination-preflight");
            actual.writer.locked(same->actual.collector.current(same,command.before(),command.deadline(),lease->{
                int baseline=actual.nativeReadWrites();var original=new AtomicReference<PlanningReadResult.Unavailable<?>>();
                PlanningReadPort refused=new PlanningReadPort() {
                    @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("same writer required");}
                    @Override public <T> PlanningReadResult<T> read(Session borrowed,ReadContract<T> contract,PlanningReadRequest request) {
                        assertSame(same,borrowed);
                        var foreign=new PlanningReadRequest(request.origin(),request.source(),request.sessionId(),
                                new OperationKey("query-foreign-termination-preflight"),request.arguments(),request.deadline());
                        var result=actual.reads.read(borrowed,contract,foreign);original.set(missing(result));return result;
                    }
                };
                var middle=new AtomicReference<PlanningReadResult.Unavailable<Obj>>();
                var returned=routeTerminationFailure(actual,same,lease.frame(),command.deadline(),wars.get(),refused,
                        WarExitReads.Kind.OPTIONS,middle);
                sameFailure(original.get(),middle.get());sameFailure(original.get(),returned);
                assertTrue(returned.original().isEmpty());assertTrue(returned.decodeFailure().isEmpty());
                assertTrue(returned.observedFailure().isEmpty());assertEquals(baseline,actual.nativeReadWrites());
                assertEquals(0,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());
                assertEquals(0,same.head().state().sequence());return null;
            }));
        }
    }
    private static PlanningReadCoordinator.ReadGuardPort unavailableAfterGuard(
            ActionWriterIntegrationFixture.SoftwareReadGuardContext originalGuard) {
        return new PlanningReadCoordinator.ReadGuardPort() {
            @Override public PlanningReadGuard verify(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,
                    PlanningReadRequest request, ReadContract<?> contract) {
                return originalGuard.guard().verify(head, request, contract);
            }
            @Override public <T> T withOriginalReadSource(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,
                    PlanningReadRequest request, ReadContract<?> contract, java.util.function.Supplier<T> work) {
                return originalGuard.guard().withOriginalReadSource(head, request, contract, work);
            }
            @Override public PlanningReadGuard verifyOriginalCurrent(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,
                    PlanningReadRequest request, ReadContract<?> contract) {
                throw new IllegalStateException("actual software after observation unavailable");
            }
        };
    }

    private static void existingForeground(ActionWriterIntegrationFixture actual,boolean mandatory) throws Exception {
        var seed = actual.command("existing-event-packet-source"); Instant deadline = Instant.now().plusSeconds(20);
        byte[] packet = actual.writer.locked(same -> actual.collector.current(same, seed.before(), deadline, lease -> {
            var full = actual.frameLoader().loadFull(NativeEffectEvidence.basis(lease.frame()), actual.archive.withSession(same));
            var state = assertInstanceOf(ObjectNode.class, StrictJson.parse(full.actual().state().bytes()));
            // Preserve the actual software packet's player/date/world; reuse the existing original event instance/options.
            if(mandatory) {
                state.putNull("active_event");
                state.putObject("top_exclusive_modal_choice_hint").put("status","present").put("source","application_main_pump_observed_modal_receiver")
                        .put("owner_verified",true).put("max_observation_age_ms",2000).put("opaque_root_id","failed-modal-receiver");
            } else state.set("active_event", original.path("event_snapshot").get("active_event").deepCopy());
            state.putNull("pending_character_interaction");
            var next = full.actual().nativeRevision().add(java.math.BigInteger.ONE);
            var envelope = StrictJson.object().put("type", "state_snapshot").put("protocol_version", 1)
                    .put("snapshot_id", "m2-existing-event-" + next).put("revision", next);
            envelope.set("state", state); return NativeWire.packet(StrictJson.canonical(envelope));
        }));
        actual.enqueueSoftwareNativePacket(packet);
    }

    private static void assertCardAndColdScan(EpisodeIncidentJournal journal, EpisodeIncidentJournal.Configuration configured,
            EpisodeIncidentJournal.Binding binding, EpisodeIncidentJournal.Ticket ticket,
            ActionPorts.OutcomeArchive originals, String fault, boolean typedDecode) throws java.io.IOException {
        var body = StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path())));
        assertEquals("xar.unhandled-native-window-diagnostic/v1", body.path("schema").textValue());
        if(ticket.kind()==EpisodeIncidentJournal.Kind.MANDATORY) {
            assertEquals("unknown_mandatory_choice",body.path("kind").textValue());assertFalse(body.has("event_definition_key"));
            assertEquals("failed-modal-receiver",body.path("mandatory_choice_hint").path("opaque_root_id").textValue());
        } else {
            assertTrue(body.path("current_event_instance_id").isIntegralNumber());
            assertEquals(original.path("event_snapshot").path("active_event").path("instance_id").bigIntegerValue(), body.path("current_event_instance_id").bigIntegerValue());
        }
        assertEquals("planning_diagnostic", body.path("stage").textValue()); assertFalse(body.path("dispatch_attempted").booleanValue());
        assertTrue(body.path("selection").isNull()); if(ticket.kind()!=EpisodeIncidentJournal.Kind.MANDATORY)assertTrue(body.path("event_definition_key").isNull()); assertTrue(body.path("context").isNull());
        var failure = body.path("original_plan"); assertEquals("xar.pending-ui-read-failure/v1", failure.path("schema").textValue());
        assertEquals(typedDecode, failure.path("typed_decode_failure_present").booleanValue());
        assertTrue(failure.path("original_parent_action_id").isNull(), "ordinary software source makes no private-parent claim");
        var index = StrictJson.parse(Files.readAllBytes(Path.of(ticket.index().path())));
        assertEquals("xar.episode-incident-before-index/v3", index.path("schema").textValue());
        assertTrue(index.path("action_id").isNull()); assertFalse(index.has("original_read_ref"));
        var refs = index.path("failed_read_originals"); assertEquals("xar.failed-read-originals/v1", refs.path("schema").textValue());
        ExactRef outcome = ExactRef.fromJson(refs.get("original_outcome_ref"));
        ExactRef prepared = ExactRef.fromJson(refs.get("prepared_request_ref"));
        assertEquals(fault.equals("opaque_after"), refs.path("observed_failure_ref").isNull());
        Optional<ExactRef> observed = refs.path("observed_failure_ref").isNull() ? Optional.empty()
                : Optional.of(ExactRef.fromJson(refs.get("observed_failure_ref")));
        var actual = originals.load(outcome); var preparedRequest = originals.loadRequest(prepared);
        if (fault.equals("response_lost")) assertInstanceOf(NativeActionPort.Unknown.class, actual);
        else assertEquals(fault.equals("malformed_payload"), assertInstanceOf(NativeActionPort.AckReceived.class, actual).nativeOk());
        assertTrue(refs.path("dependency_refs").isArray());
        var dependencies = new java.util.ArrayList<ExactRef>();
        for (var ref : refs.path("dependency_refs")) dependencies.add(ExactRef.fromJson(ref));
        assertFalse(dependencies.isEmpty());
        assertTrue(dependencies.contains(originals.materialReferenceOf(preparedRequest.additionalFields())));
        if (observed.isPresent()) {
            var proof = PlanningReadFailureCodec.load(observed.orElseThrow(), originals);
            assertEquals(preparedRequest, proof.prepared());
            assertEquals(binding.before(), proof.request().before()); assertEquals(outcome, proof.originalRef()); assertEquals(prepared, proof.preparedRef());
            assertTrue(dependencies.contains(originals.materialReferenceOf(new RawJson(OpportunityJson.encode(proof.request().arguments())))),
                    "official failed-read codec arguments must survive the same incident scan");
            for (var guard : List.of(proof.before().binding(), proof.after().binding())) {
                assertTrue(dependencies.contains(guard.nativeEvidence())); assertTrue(dependencies.contains(guard.capabilityEvidence()));
                assertTrue(dependencies.containsAll(guard.supportingEvidence()));
            }
        }
        var scan = journal.scan(binding); assertEquals(1, scan.diagnosticOnly()); assertEquals(0, scan.incompleteAfter());
        assertTrue(scan.originals().containsAll(List.of(outcome, prepared)));
        observed.ifPresent(ref -> assertTrue(scan.originals().contains(ref)));
        assertTrue(scan.originals().containsAll(dependencies));
        var request = scan.batch().orElseThrow(); assertEquals(List.of(ticket.before()), request.capturedRefs());
        assertEquals(request, OfflineEventAnalysisWire.decodeBatch(OfflineEventAnalysisWire.encode(request)));
        var manifest = StrictJson.parse(Files.readAllBytes(Path.of(request.manifestRef().path())));
        assertTrue(manifest.path("new_incidents").get(0).path("after").isNull());
        assertTrue(manifest.path("new_incidents").get(0).path("after_sha256").isNull());
        var loaded = OfflineScanSource.load(configured.incidentRoot(), Optional.of(configured.scanRoot()),
                binding.before().machineId(), request.manifestRef(), request.capturedRefs());
        var downstreamOriginals = loaded.externalOriginals().stream().map(OfflineScanSource.ExternalOriginal::source).toList();
        assertTrue(downstreamOriginals.containsAll(List.of(outcome, prepared)));
        observed.ifPresent(ref -> assertTrue(downstreamOriginals.contains(ref)));
        assertTrue(downstreamOriginals.containsAll(dependencies),
                "actual failed-read payload, prepared, guards and optional observed proof must remain recheckable");
        OfflineScanSource.recheck(configured.incidentRoot(), Optional.of(configured.scanRoot()), request.manifestRef(), loaded);
        RootBlockedPendingIncidentTest.assertOfflineUnresolved(journal, configured, binding, request, ticket.incidentId());
        var reopened = EpisodeIncidentJournal.open(configured, binding, journal.episodeReference());
        assertEquals(List.of(request), RootIncidentRuntime.retainedOriginalBatches(List.of(reopened)));
        assertFalse(Files.exists(Path.of(ticket.index().path()).resolveSibling(ticket.incidentId() + ".review-index.json")));
    }
}
