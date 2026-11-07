package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.io.CleanupMode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.wave2.finance.giftpending.*;

/** Actual public temporary writer/guard/read/coordinator/native-packet SOFTWARE chain. No Game, Root admission or SAVE. */
final class ConstructionFullProduction113Test {
    @TempDir(cleanup=CleanupMode.NEVER) Path directory;
    private static final String SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private enum Mode { APPLIED, REJECTED, UNKNOWN }
    private record Body(FinanceStatePort.ReaderBinding reader,DomainBodies.Registration registration,byte[] raw) { }
    private static final class Context {
        final AtomicReference<ActionWriterIntegrationFixture> fixture=new AtomicReference<>();
        final AtomicReference<FinanceReadContracts> definitions=new AtomicReference<>();
        final AtomicReference<ConstructionDomainLifecycle.Prepared> domain=new AtomicReference<>();
        final AtomicReference<OrdinaryConstructionPolicy> policy=new AtomicReference<>();
        final AtomicReference<PlanningRequest> planned=new AtomicReference<>();
        final AtomicReference<ExactRef> source=new AtomicReference<>();
        final AtomicInteger revision=new AtomicInteger(2),proof=new AtomicInteger(10);
        final List<Body> bodies=new ArrayList<>();
    }
    @Test void fullFuturePlanRunsActualIntentEffectColdVerifierAndFullMaterialPublication()throws Exception {exercise(Mode.APPLIED);}
    @Test void rejectedSoftwareCommandStillRequiresFullOriginalBeforeClearingPending()throws Exception {exercise(Mode.REJECTED);}
    @Test void unknownSoftwareCommandStillRequiresFullOriginalAndNeverResubmits()throws Exception {exercise(Mode.UNKNOWN);}

    private void exercise(Mode mode)throws Exception {
        var c=new Context();var scenario=scenario(c);
        ActionPorts.PostconditionPort observer=(command,attempt,dispatch)->{
            var actual=c.fixture.get();var p=actual.physicalInputs();
            var held=new HeldDriverObservationPort(p.transport(),p.driverAssembler(),actual.archive::preserveNativeFrame,p.observationAssembler(),16);
            var snapshots=new NativeEffectSnapshots(held,actual.archive.withSession(actual.journal.borrowedWriterSession()),actual.frameLoader());
            return new NativeConstructionEffects(snapshots,actual.reads,c.definitions.get().contract(FinanceReadContracts.Query.CONSTRUCTION)).observe(command,attempt,dispatch).result();
        };
        var construction=new ActionWriterIntegrationFixture.SoftwareActionScenario(OrdinaryConstructionPolicy.OPERATION,
                "game.command."+OrdinaryConstructionPolicy.OPERATION.value(),observer,()->{
                    c.revision.set(3);c.fixture.get().enqueueSoftwareNativePacket(snapshot(3,77_000_000));
                },Optional.empty(),Optional.empty(),true);
        var unused=new ArrayList<ActionWriterIntegrationFixture.SoftwareActionScenario>();unused.add(construction);
        for(var operation:List.of(OrdinaryFinancePolicies.GIFT,OrdinaryFinancePolicies.MERCENARY))unused.add(new ActionWriterIntegrationFixture.SoftwareActionScenario(
                operation,"game.command."+operation.value(),(command,attempt,dispatch)->{throw new AssertionError("no finance action in construction-only software test");},
                ()->{throw new AssertionError("no finance dispatch in construction-only software test");}));
        try(var f=new ActionWriterIntegrationFixture(directory.resolve(mode.name()),false,scenario,unused,List.of(),source->registrations(c,source),64L*1024*1024)) {
            c.fixture.set(f);f.configureSoftwareFreshRead179("success",true);
            var domain=c.domain.get();var definitions=c.definitions.get();
            domain.bindCore(f.writer,f.archive,f.frameLoader(),definitions);domain.bindOriginals(c.source.get(),new SoftwareFresh(c.source.get()));
            var cold=ConstructionOriginalSource.archivedBinding(NativeConstructionEffects.archivedVerifier(OrdinaryConstructionPolicy.OPERATION,
                    c.source.get(),f.frameLoader(),definitions.contract(FinanceReadContracts.Query.CONSTRUCTION)),f.writer::borrowedSession);
            f.bindAdditionalArchivedVerifier(cold);
            var histories=new DriverActionHistoryPublisher(f.driverAuthority(),f.journal,f.archive,
                    new ConstructionHistoryMaterials(f,cold,c.source.get()),List.of(c.source.get()));
            f.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND,histories);
            f.bindAdditionalBeforeIntent((same,command)->{
                c.policy.get().revalidateConstruction(same,command,c.planned.get());
                try {domain.prepareIntent(same,command);}catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            var beforeWriteRefusal=new IllegalStateException("explicit software pre-write guard failure");
            var rejectionGuards=new AtomicInteger();
            if(mode==Mode.REJECTED)f.bindGuardObserver((head,original)->{
                if(rejectionGuards.incrementAndGet()==2){
                    try {
                        var durable=ContinuityActionJournal.lookup(head.state(),original.actionId(),f.archive.withSession(f.writer.borrowedSession())).orElseThrow();
                        assertInstanceOf(ActionState.IntentDurable.class,durable.state());
                    }catch(IOException failure){throw new UncheckedIOException(failure);}
                    // The unchanged coordinator creates and archives its genuine BEFORE_WRITE/zero-byte proof.
                    throw beforeWriteRefusal;
                }
            });
            if(mode==Mode.UNKNOWN)f.loseActionAckOnce();
            f.enqueueSoftwareNativePacket(snapshot(2,100_000_000));var initial=f.ready();var published=initial.request().observations();
            assertTrue(published.actionSteps().contains(OrdinaryConstructionPolicy.OPERATION));
            AtomicReference<ActionCommand> selected=new AtomicReference<>();
            f.writer.locked(same->{
                initialize(f,same,initial.request().before());
                domain.publishOriginal(same,ConstructionDomainLifecycle.Kind.FRESH,obj("body",empty()),List.of(c.source.get()));
                for(var body:c.bodies){var scoped=f.archive.withSession(same);var original=scoped.preserveMaterial(new RawJson(body.raw()));
                    var request=new DomainBodies.ImportRequest(body.registration().slot(),body.registration().contractSchema(),original,body.raw(),body.registration().producerSources(),"p113-software:"+body.registration().slot());
                    same.commitImport(same.previewImport(request));}
                var actualBindings=f.actualBindings();var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();archived.add(cold);
                for(var operation:List.of(OrdinaryFinancePolicies.GIFT,OrdinaryFinancePolicies.MERCENARY))archived.add(new NativeRecordedEvidenceVerifier.Binding(
                        operation,c.source.get(),(head,receipt,archive)->{throw new AssertionError("unexecuted finance software binding");}));
                // Retain the identical actually registered action objects and read contracts; no detached action issuer is added.
                var completeBindings=RootExecutableBindings.freeze(actualBindings.actionBindings(),RootReadContractCatalog.staticOnly(actualBindings.readContracts()),
                        actualBindings.compositeBindings(),archived,List.of(),64);
                var request=f.collector.current(same,initial.request().before(),Instant.now().plusSeconds(120),lease->{
                    var frame=lease.frame();Instant deadline=Instant.now().plusSeconds(120);
                    return new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),deadline,new PlanningObservation(frame.semantic(),published.history(),published.actionSteps(),
                            published.bridgeCapabilities(),published.battleSpeedReadiness(),published.actionFacts(),published.campaignGoal(),published.crossRunPlan(),published.initialLifestyleFocusRequired()));
                });
                // Planning/archive work follows the closed capture; every query/ending/state callback captures its real frame separately.
                    var bindings=new ArrayList<CanonicalFinanceStateSource.Binding>();var registration=domain.registration();
                    bindings.add(new CanonicalFinanceStateSource.Binding(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION,c.source.get(),domain::financePending),
                            registration.slot(),registration.contractSchema(),registration.maximumBodyBytes(),registration.producerSources()));
                    for(var body:c.bodies)bindings.add(new CanonicalFinanceStateSource.Binding(body.reader(),body.registration().slot(),body.registration().contractSchema(),body.registration().maximumBodyBytes(),body.registration().producerSources()));
                    var originalState=new CanonicalFinanceStateSource(f.root.resolve("ROOT-CONTINUITY-WINDOW.lock"),f.writer,new ActionSnapshotReader(f.journal),
                            (held,expected)->f.collector.current(held,expected.before(),expected.deadline(),current->current.frame().identity()),held->Optional.empty(),bindings);
                    var state=new FinanceStatePort(originalState,originalState.owningReaders());
                    var funding=new CanonicalFundingPending(new ActionSnapshotReader(f.journal),f.root.resolve("ROOT-CONTINUITY-WINDOW.lock"),state,originalState.owningReaders(),
                            ()->completeBindings,f.archive::withSession,request.before().game(),request.source(),request.sessionId());
                    var finance=new OrdinaryFinanceCollector(definitions,observing(f.reads),state,()->{try{return f.writer.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}});
                    var collector=new OrdinaryConstructionCollector(finance,new OrdinaryConstructionCollector.EndingSnapshot(){
                        public Obj readCurrent(PlanningRequest original){try{return readCurrent(f.writer.borrowedSession(),original);}catch(IOException failure){throw new UncheckedIOException(failure);}}
                        public Obj readCurrent(Session held,PlanningRequest original){try{return f.collector.current(held,original.before(),original.deadline(),current->current.frame().semantic());}catch(IOException failure){throw new UncheckedIOException(failure);}}
                    },new OrdinaryConstructionCollector.FinancingPending(){
                        public CanonicalFundingPending.Result readUnderOriginalWriterLock(PlanningRequest original){try{return funding.read(f.writer.borrowedSession(),original);}catch(IOException failure){throw new UncheckedIOException(failure);}}
                        public CanonicalFundingPending.Result readUnderOriginalWriterLock(Session held,PlanningRequest original){
                            try{return funding.read(held,original);}catch(IOException failure){throw new UncheckedIOException(failure);}
                        }
                    });
                    var policy=new OrdinaryConstructionPolicy(c.source.get(),collector,(original,args)->Optional.of(NativeConstructionEffects.expected(original.before(),original.source(),args)),
                            (original,draft,ledger,receipt,reason)->{throw new AssertionError("initial clear software body has no material followup");},
                            new ConstructionOriginalSource(f.archive,f.writer::borrowedSession));
                    c.planned.set(request);c.policy.set(policy);
                    var draft=new OrdinaryPolicy.Draft("software-original-life","current_life_loop","explicit software ordinary input",OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),
                            OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),obj("selected_step",new Text("life-advance")));
                    var decision=policy.evaluate(request,draft);
                    var replacement=assertInstanceOf(OrdinaryPolicy.Replace.class,decision,()->"actual construction producer: "+decision);
                    var command=replacement.draft().command().orElseThrow();selected.set(command);
                    assertEquals(request.before(),command.before());assertEquals(request.source(),command.source());assertEquals(request.deadline(),command.deadline());
                    Obj manifest=object(command.arguments().get("ordinary_cash_request"),"future full manifest");assertEquals(new Text(ConstructionOriginalSource.SCHEMA),manifest.get("schema"));
                    var opened=ConstructionOriginalSource.resolveCommand(same,f.archive,command);assertTrue(opened.observed().original().length>4_194_304);
                    assertEquals(ConstructionFundingEvidence.command(command),CanonicalFundingPending.decodeEvidence(CanonicalFundingPending.encodeEvidence(ConstructionFundingEvidence.command(command))));
                    // Preserve the true current producer for the later MATERIAL path, not a fake Complete or exported snapshot.
                    productionCollector.set(collector);return null;
            });
            var command=selected.get();byte[] canonical=ActionCodec.encodeCommand(command);int beforeWrites=f.nativeActionWrites();
            final ActionReceipt receipt;
            if(mode==Mode.REJECTED){
                assertSame(beforeWriteRefusal,assertThrows(IllegalStateException.class,()->f.coordinator.execute(command)));
                assertEquals(2,rejectionGuards.get());
                receipt=f.journal.locked(actual->actual.find(command.actionId()).orElseThrow());
            }else receipt=f.coordinator.execute(command);
            final int expectedWrites=beforeWrites+(mode==Mode.REJECTED?0:1);
            assertEquals(expectedWrites,f.nativeActionWrites());
            f.writer.locked(same->{
                if(mode==Mode.APPLIED){
                    assertTrue(receipt.applied().isPresent(),()->"software construction outcome "+receipt.state());
                    var uncovered=f.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
                    assertTrue(uncovered.actionRows().stream().noneMatch(row->row.actionId().equals(receipt.command().actionId())));
                    int reads=f.nativeReadWrites();
                    var publication=assertInstanceOf(DriverActionHistoryPublisher.Published.class,histories.completed(same,receipt));
                    assertTrue(publication.legacyRow().isPresent());
                    var covered=f.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
                    var coverage=covered.actionRows().stream().filter(row->row.actionId().equals(receipt.command().actionId())).findFirst().orElseThrow();
                    assertEquals(receipt.bodySha256(),coverage.bodySha256());assertEquals(receipt.sequence(),coverage.durableSequence());
                    assertEquals(uncovered.stamp().driverVersion()+1,covered.stamp().driverVersion());
                    String publishedHead=same.head().digest();
                    assertEquals(new DriverActionHistoryPublisher.Unchanged(DriverActionHistoryPublisher.Reason.ALREADY_COVERED),histories.completed(same,receipt));
                    assertEquals(publishedHead,same.head().digest());
                    assertEquals(reads,f.nativeReadWrites());assertEquals(expectedWrites,f.nativeActionWrites());
                }
                var pending=domain.read(same);assertTrue(pending.pending().isPresent());
                byte[] before=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.CONSTRUCTION)).canonicalBody();
                Obj manifest=object(command.arguments().get("ordinary_cash_request"),"manifest");ExactRef ref=reference(manifest.get("input_ref"));
                Path file=Path.of(ref.path()),held=file.resolveSibling(file.getFileName()+".held");Files.move(file,held);
                try {
                    assertThrows(RuntimeException.class,()->domain.synchronizeOutcome(same,receipt));
                    assertArrayEquals(before,assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.CONSTRUCTION)).canonicalBody());
                    if(mode==Mode.APPLIED)assertThrows(RuntimeException.class,()->cold.verifier().verify(same.head(),receipt,f.archive.withSession(same)));
                } finally {Files.move(held,file);}
                if(mode==Mode.APPLIED){
                    assertTrue(receipt.applied().isPresent(),()->"software construction outcome "+receipt.state());
                    cold.verifier().verify(same.head(),receipt,new NativeOutcomeArchive(f.archive.artifactStore(),f.writer).withSession(same));
                } else if(mode==Mode.REJECTED){
                    var rejected=assertInstanceOf(ActionState.RejectedBeforeDispatch.class,receipt.state());
                    assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.dispatch().proof().stage());
                    assertEquals(0,rejected.dispatch().proof().requestBytesWritten());assertTrue(receipt.applied().isEmpty());
                    var originals=f.archive.withSession(same);var proof=originals.referenceOf(rejected.dispatch());
                    assertEquals(rejected.dispatch(),originals.load(proof));
                }else assertInstanceOf(ActionState.Unknown.class,receipt.state());
                domain.synchronizeOutcome(same,receipt);
                var after=domain.read(same);assertEquals(mode==Mode.UNKNOWN,after.pending().isPresent());
                if(mode==Mode.UNKNOWN)assertEquals(new Text("action_state_unknown"),after.pending().orElseThrow().original().get("status"));
                if(mode==Mode.APPLIED){
                    assertTrue(after.applied().isPresent());
                    var materialRequest=f.collector.currentOwned(same,f.observationIdentity(),command.deadline(),lease->{
                        var frame=lease.frame();var old=c.planned.get().observations();return new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),command.deadline(),
                                new PlanningObservation(frame.semantic(),old.history(),old.actionSteps(),old.bridgeCapabilities(),old.battleSpeedReadiness(),old.actionFacts(),old.campaignGoal(),old.crossRunPlan(),old.initialLifestyleFocusRequired()));
                    });
                    var material=assertInstanceOf(OrdinaryConstructionCollector.MaterialAvailable.class,productionCollector.get().material(same,materialRequest));
                    assertTrue(DriverJson.encode(material.queryInput()).length>4_194_304);
                    domain.publishMaterial(same,after,ConstructionMaterialReducer.RefreshKind.COLD_MATERIAL,after.applied().orElseThrow().identity().actionRequestId(),material);
                    var body=domain.read(same).original();var full=ConstructionFullMaterialSource.fromBody(body).orElseThrow();
                    assertEquals(ConstructionMaterialReducer.InputVersion.FULL_V3,full.load(same,f.archive).version());
                    assertTrue(body.members().containsKey(ConstructionFullMaterialSource.BODY_FIELD));assertFalse(body.members().containsKey(ConstructionMaterialSource.BODY_FIELD));
                }
                assertArrayEquals(canonical,ActionCodec.encodeCommand(receipt.command()));assertEquals(expectedWrites,f.nativeActionWrites());return null;
            });
        }
    }
    private final AtomicReference<OrdinaryConstructionCollector> productionCollector=new AtomicReference<>();

    /** Software installed material source; the unchanged publisher alone creates canonical history/coverage. */
    private static final class ConstructionHistoryMaterials implements DriverActionHistoryPublisher.MaterialSource {
        private final ActionWriterIntegrationFixture owner;private final NativeRecordedEvidenceVerifier.Binding cold;private final ExactRef source;
        ConstructionHistoryMaterials(ActionWriterIntegrationFixture owner,NativeRecordedEvidenceVerifier.Binding cold,ExactRef source){this.owner=owner;this.cold=cold;this.source=source;}
        @Override public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){
            assertSame(owner.driverAuthority(),authority);assertSame(owner.journal,journal);assertSame(owner.archive,archive);
        }
        @Override public List<ExactRef> sources(){return List.of(source);}
        @Override public DriverActionHistoryCodec.OriginalMaterial capture(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            return original(same,actual,originals);
        }
        @Override public void requireOriginal(Session same,ActionReceipt actual,DriverActionHistoryCodec.OriginalMaterial captured,ActionPorts.OutcomeArchive originals)throws IOException {
            assertEquals(original(same,actual,originals),captured);
        }
        private DriverActionHistoryCodec.Legacy original(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            owner.writer.requireSession(same);assertEquals(OrdinaryConstructionPolicy.OPERATION,actual.command().operation());
            assertTrue(actual.applied().isPresent());cold.verifier().verify(same.head(),actual,originals);
            var original=NativeEffectEvidence.load(actual,originals,owner.frameLoader());
            var evidence=new LinkedHashSet<DriverActionHistoryCodec.Evidence>();
            ActionEffects.observation(actual).ifPresent(value->{evidence.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,value.originalEvidence()));
                value.supportingEvidence().forEach(ref->evidence.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,ref)));});
            for(var frame:List.of(original.frames().before(),original.frames().after())){
                evidence.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,frame.originalEvidence()));
                evidence.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,NativeEffectEvidence.basis(frame).driverFacts()));
            }
            original.independentReads().forEach(read->evidence.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.READ,originals.readReferenceOf(read))));
            original.supportingMaterials().forEach(ref->evidence.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,ref)));
            var result=originals.materialReferenceOf(original.compatibleResult());
            assertArrayEquals(original.compatibleResult().bytes(),originals.loadMaterial(result).bytes());
            evidence.add(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,result));
            return new DriverActionHistoryCodec.Legacy(DriverActionHistoryCodec.Recording.RETURNED,Optional.of(result),Optional.empty(),List.copyOf(evidence),sources());
        }
    }

    /** Observe the existing real READ result only; never issue an extra query, retry or fabricated receipt. */
    private static PlanningReadPort observing(PlanningReadPort actual) {
        return new PlanningReadPort() {
            @Override public PlanningReadPort planningReads() { return observing(actual.planningReads()); }
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                return observed(contract,actual.read(contract,request));
            }
            @Override public <T> PlanningReadResult<T> read(Session same,ReadContract<T> contract,PlanningReadRequest request) {
                return observed(contract,actual.read(same,contract,request));
            }
            private <T> PlanningReadResult<T> observed(ReadContract<T> contract,PlanningReadResult<T> result) {
                if(result instanceof PlanningReadResult.Unavailable<?> missing) {
                    System.out.println("P113 exact existing READ unavailable operation="+contract.operation().value()+" reason="+missing.reason());
                    missing.observedFailure().ifPresent(original->System.out.println("P113 failed READ original="+original.originalRef()+" prepared="+original.preparedRef()+" sequence="+original.headSequence()));
                    if(missing.decodeFailure().orElse(null) instanceof Throwable failure)failure.printStackTrace(System.err);
                }
                return result;
            }
        };
    }
    private static final class SoftwareFresh implements ConstructionDomainLifecycle.OriginalBodyProducer {
        private final ExactRef source;SoftwareFresh(ExactRef source){this.source=source;}
        public ConstructionDomainLifecycle.OriginalBody replay(Session same,org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ConstructionDomainLifecycle.Kind kind,Obj input,Optional<ConstructionLedgerCodec.Ledger> previous){
            assertEquals(ConstructionDomainLifecycle.Kind.FRESH,kind);assertTrue(previous.isEmpty());assertEquals(empty(),input.get("body"));return new ConstructionDomainLifecycle.OriginalBody(object(input.get("body"),"exact software original empty body"),List.of(source));
        }
    }
    private static List<DomainBodies.Registration> registrations(Context c,ExactRef source){
        c.source.set(source);var domain=ConstructionDomainLifecycle.prepare(List.of(source),source);c.domain.set(domain);var registrations=new ArrayList<DomainBodies.Registration>();registrations.add(domain.registration());
        for(var owner:List.of(FinanceStatePort.Domain.FACTION_GIFT,FinanceStatePort.Domain.MERCENARY,FinanceStatePort.Domain.FEAST,FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,FinanceStatePort.Domain.CHILD_MARRIAGE,FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE)){
            var slot=switch(owner){case FACTION_GIFT->DomainBodies.Slot.FACTION;case MERCENARY->DomainBodies.Slot.MERCENARY;case FEAST->DomainBodies.Slot.FEAST;case FIRST_HEIR_MARRIAGE->DomainBodies.Slot.FAMILY;case CHILD_MARRIAGE->DomainBodies.Slot.CHILD_MATRILINEAL;case CHILD_DEFAULT_MARRIAGE->DomainBodies.Slot.DEFAULT_MARRIAGE;default->throw new AssertionError(owner);};
            String schema=owner==FinanceStatePort.Domain.MERCENARY?MercenaryProcurement.SCHEMA:owner==FinanceStatePort.Domain.FACTION_GIFT?GiftPendingModel.SCHEMA:"fixture.owned-submission/v1";
            byte[] raw=owner==FinanceStatePort.Domain.MERCENARY?MercenaryProcurement.encode(MercenaryProcurement.emptyFreshEpisode()):owner==FinanceStatePort.Domain.FACTION_GIFT?GiftPendingCodec.encodeLedger(GiftPendingModel.Ledger.empty()):encode(obj("schema",new Text(schema),"pending",Nil.INSTANCE));
            var reader=owner==FinanceStatePort.Domain.FACTION_GIFT?FinanceStatePort.giftReader(source):new FinanceStatePort.ReaderBinding(owner,source,document->{
                if(owner==FinanceStatePort.Domain.MERCENARY)return MercenaryProcurement.decode(document.bytes()).pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR;
                Obj body=DriverJson.object(document.bytes(),65_536);assertEquals(new Text(schema),body.get("schema"));assertEquals(Nil.INSTANCE,body.get("pending"));return FinanceStatePort.Pending.CLEAR;
            });
            var registration=new DomainBodies.Registration(slot,schema,org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES,List.of(source),(head,previous,request,actual)->{
                assertTrue(previous.isEmpty());assertArrayEquals(raw,actual);assertArrayEquals(org.xar.ck3.control.continuity.writer.WriterContracts.canonical(raw),request.producerInput());reader.reader().decode(new FinanceStatePort.Document(owner,request.originalBody(),actual));return ActionCodec.sha256(actual);
            });c.bodies.add(new Body(reader,registration,raw));registrations.add(registration);
        }return List.copyOf(registrations);
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(Context c){
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(SHA.toLowerCase(Locale.ROOT),"ck3-1.20.0.4-msvc-x64",source->{
            var definitions=new FinanceReadContracts(query->{String cap="game.command."+query.operation().value();return new FinanceReadContracts.Registration(source,new FinanceReadContracts.Permission(
                    Optional.of(cap),cap,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,query==FinanceReadContracts.Query.CASH?ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY:ReadContract.WireProfile.EXECUTE_STEP));});c.definitions.set(definitions);
            return List.of(definitions.contract(FinanceReadContracts.Query.ROOT),definitions.contract(FinanceReadContracts.Query.MERCENARIES),definitions.contract(FinanceReadContracts.Query.CASH),definitions.contract(FinanceReadContracts.Query.CONSTRUCTION));
        },request->{try{return new RawJson(StrictJson.canonical(result(c,request.step())));}catch(Exception failure){throw new IllegalArgumentException("explicit software read result",failure);}},Optional.of("1.20.0.4"),Set.of(org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.CAPABILITY));
    }
    private static ObjectNode result(Context c,String step)throws Exception {
        int revision=c.revision.get();var result=StrictJson.object().put("step",step).put("accepted",true).put("snapshot_revision",revision).put("query_sequence",c.proof.incrementAndGet());
        if(step.equals(FinanceReadContracts.Query.ROOT.operation().value())){
            ObjectNode root=(ObjectNode)StrictJson.parse(resource("/finance/faction-generation-native90/authored-root.json"));remap(root,BigInteger.valueOf(12345),BigInteger.valueOf(73));
            root.put("snapshot_revision",revision).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW);root.putNull("player_heir_candidate_v1");
            root.putObject("player_monthly_gold_income").put("raw",584686).put("scale",100000);
            root.putObject("player_max_monthly_gold_maintenance_v1").put("status","available").putNull("unavailable_reason").putObject("value").put("raw",451200).put("scale",100000);
            result.put("status","available").put("backend_id","native-headless");result.set("campaign_root_context",root);return result;
        }
        if(step.equals(FinanceReadContracts.Query.MERCENARIES.operation().value())){
            ObjectNode market=result.putObject("player_mercenary_context").put("schema","ck3_12004_player_mercenary_context_v1").put("game_version","1.20.0.4").put("executable_sha256",SHA)
                    .put("actor_character_id",73).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("capture_epoch",c.proof.get()).put("read_only",true).put("native_hire_mode",1).put("available",true);
            market.putNull("unavailable_reason");market.putArray("rows");return result;
        }
        if(step.equals(FinanceReadContracts.Query.CASH.operation().value())){
            Class<?> data=Class.forName("org.xar.ck3.control.wave3.development.wartimesequencing.ConstructionFullOriginal113SdkTest");var method=data.getDeclaredMethod("packet",JsonNode.class);method.setAccessible(true);
            ObjectNode cash=(ObjectNode)method.invoke(null,cashSnapshot(revision));cash.putObject("current_treasury").put("raw",revision==2?100000000:77000000).put("scale",100000);
            cash.put("queried_snapshot_id","native:"+revision).put("queried_revision",revision).put("queried_native_revision",revision);result.set("war_cash_current_resources",cash);return result;
        }
        assertEquals(FinanceReadContracts.Query.CONSTRUCTION.operation().value(),step);
        ObjectNode probe=result.putObject("private_probe").put("advertised",false).put("snapshot_revision",revision).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("proof_epoch",c.proof.incrementAndGet());
        ObjectNode world=probe.putObject("player_world_building_sources").put("status","source_available").put("snapshot_revision",revision).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW)
                .put("player_character_id",73).put("native_final_legality_evaluated",true).put("native_cost_evaluated",true).put("player_gold_raw",revision==2?100000000:77000000);
        ObjectNode active=world.putArray("active_constructions").addObject().put("barony_title_id",2103).put("province_id",2635).put("active",revision>2);
        if(revision>2)active.put("building_type_id",11).put("slot_index",0).put("initiator_character_id",73);
        world.put("completed_buildings_observed",true).put("positive_income_coverage_complete",true);world.putArray("completed_buildings");
        var samples=world.putArray("legal_samples");if(revision==2){var sample=samples.addObject().put("barony_title_id",2103).put("province_id",2635).put("building_type_id",11).put("slot_index",0).put("building_key","farm_estates_01").put("native_cost_observed",true);
            var costs=sample.putArray("cost_raw_native");costs.add(23000000);for(int i=1;i<10;i++)costs.add(0);}
        return result;
    }
    private static byte[] snapshot(int revision,long gold)throws IOException {
        ObjectNode state=cashSnapshot(revision);
        // The native edge supplies only its own diagnostics; the real assembler appends its complete held HELLO packet.
        ObjectNode diagnostics=(ObjectNode)state.get("diagnostics");diagnostics.remove("hello");
        diagnostics.put("bridge_creation_date","explicit-software-construction-birth");
        state.put("speed",3).put("one_life_terminal",false).putNull("one_life_terminal_reason");state.put("episode_identity_pending",false);
        state.putObject("played_character_gold").put("raw",gold).put("scale",100000);state.putNull("active_event");state.putNull("pending_character_interaction");
        state.put("opaque_unconsumed_extension","x".repeat(3_400_000));
        ObjectNode packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:"+revision).put("revision",revision);packet.set("state",state);
        return org.xar.ck3.control.nativebridge.NativeWire.packet(FullJsonTree.encode(packet,16*1024*1024));
    }
    private static ObjectNode cashSnapshot(int revision){
        ObjectNode snapshot=StrictJson.object().put("snapshot_id","native:"+revision).put("revision",revision).put("native_revision",revision).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW)
                .put("episode_run_id","fixture-episode-1").put("paused",true).put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",73).put("alive",true);snapshot.putArray("active_wars");snapshot.putArray("player_armies");
        snapshot.putObject("diagnostics").put("bridge_pid",42).put("connection_generation",5).putObject("hello").put("expected_ck3_version","1.20.0.4").put("expected_ck3_sha256",SHA);return snapshot;
    }
    private static void initialize(ActionWriterIntegrationFixture fixture,Session same,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity initial)throws IOException {
        fixture.collector.current(same,initial,Instant.now().plusSeconds(30),lease->{
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=fixture.archive.withSession(same).preserveMaterial(new RawJson("{\"actual_software_start_policy\":true}".getBytes(StandardCharsets.UTF_8)));
            var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
            fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
        });
    }
    private static Obj empty(){return obj("schema",new Text(ConstructionLedgerCodec.SCHEMA),"pending",Nil.INSTANCE,"applied",Nil.INSTANCE,"applied_prior",new Arr(List.of()));}
    private static ExactRef reference(Value value){return ExactRef.fromJson(StrictJson.parse(DriverJson.encode(value)));}
    private static byte[] resource(String name)throws IOException {try(var stream=ConstructionFullProduction113Test.class.getResourceAsStream(name)){if(stream==null)throw new IOException("required unchanged DATA missing: "+name);return stream.readAllBytes();}}
    private static void remap(JsonNode node,BigInteger old,BigInteger actor){
        Set<String> fields=Set.of("player_character_id","top_liege_character_id","immediate_liege_character_id","first_heir_character_id","owner_character_id","incumbent_character_id","character_id");
        if(node.isObject()){var object=(ObjectNode)node;var keys=new ArrayList<String>();object.fieldNames().forEachRemaining(keys::add);for(String key:keys){JsonNode value=object.get(key);if(fields.contains(key)&&value.isIntegralNumber()&&value.bigIntegerValue().equals(old))object.put(key,actor);
            else if(Set.of("primary_title_succession_character_ids","direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids").contains(key)&&value.isArray()){
                var array=(com.fasterxml.jackson.databind.node.ArrayNode)value;for(int i=0;i<array.size();i++)if(array.get(i).isIntegralNumber()&&array.get(i).bigIntegerValue().equals(old))array.set(i,com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(actor));
            }else remap(value,old,actor);}}
        else if(node.isArray())for(JsonNode value:node)remap(value,old,actor);
    }
}
