package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.*;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusPendingFixture;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusEffects;
import org.xar.ck3.control.nativebridge.capabilities.interactions.GuardianReconciliationQueries;
import org.xar.ck3.control.nativebridge.capabilities.interactions.OrdinaryInteractionCodec;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Build;

/**
 * Real canonical UNKNOWN -> sole Root physical producer -> coordinator's private observation scope ->
 * same installed catalog/query coordinator -> real NativeGameTransport -> immutable archive replay.
 * Packet/source edges are finite software fixtures; this suite never claims a live package, Commander assignment or Game effect.
 */
final class RootReconciliationAuthorityIntegrationTest {
    @TempDir Path temporary;
    private static final OperationKey ACTION=new OperationKey("pause-map");
    private static final OperationKey QUERY=new OperationKey("query-army-commander-candidates-v1-for-army-0");
    private static final String CAP="game.command.query-army-commander-candidates-v1-for-army-N";
    private static final OpportunityJson.Obj ARGS=new OpportunityJson.Obj(Map.of("army_id",new OpportunityJson.IntegerValue(BigInteger.ZERO)));
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static final class DecoderBoundaryReached extends RuntimeException {
        private static final long serialVersionUID=1L;
        DecoderBoundaryReached(){super("actual Root basis/packet reached mandatory original admission; no business success");}
    }
    private final class Harness implements AutoCloseable {
        final ActionWriterIntegrationFixture actual;
        final RootLifecycleAuthority physical;
        final RootReconciliationAuthority reconciliation;
        final RootReconciliationReadGuard readGuard;
        final ReadContract<?> query;
        final AtomicReference<PlanningReadReceipt> issued=new AtomicReference<>();
        final AtomicReference<GuardEvidence> push=new AtomicReference<>();
        final AtomicReference<RootReconciliationAuthority.Lease> escaped=new AtomicReference<>();
        final AtomicInteger scopeCalls=new AtomicInteger();
        final AtomicInteger sourceChecks=new AtomicInteger();
        final AtomicInteger decoderAdmissions=new AtomicInteger();
        final AtomicInteger closeCandidates=new AtomicInteger();
        final AtomicReference<GuardianReconciliationQueries> guardianProfile=new AtomicReference<>();
        final AtomicReference<ReadContract<org.xar.ck3.control.reconciliation.LateOutcome.Status>> statusProfile=new AtomicReference<>();
        final AtomicReference<ReadContract<org.xar.ck3.control.reconciliation.LateOutcome.Status>> ordinaryStatus=new AtomicReference<>();
        final AtomicReference<PlanningReadResult.Known<org.xar.ck3.control.reconciliation.LateOutcome.Status>> statusKnown=new AtomicReference<>();
        final boolean queryEnabled;
        final boolean decoderBoundary;
        final RootReconciliationAuthority.QueryKind kind;
        final OperationKey actualAction;
        ActionCommand command;
        ActionReceipt firstUnknown;
        Harness(Path root,boolean queryEnabled)throws IOException{
            this(root,queryEnabled,RootReconciliationAuthority.QueryKind.COMMANDER_CANDIDATES);
        }
        Harness(Path root,boolean queryEnabled,RootReconciliationAuthority.QueryKind actualKind)throws IOException{
            this(root,queryEnabled,actualKind,false);
        }
        Harness(Path root,boolean queryEnabled,RootReconciliationAuthority.QueryKind actualKind,boolean replaceSource)throws IOException{
            this(root,queryEnabled,actualKind,replaceSource,false);
        }
        Harness(Path root,boolean queryEnabled,RootReconciliationAuthority.QueryKind actualKind,boolean replaceSource,boolean decoderBoundary)throws IOException{
            this.queryEnabled=queryEnabled;
            this.decoderBoundary=decoderBoundary;kind=actualKind;
            actualAction=actualKind==RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE
                    ?new OperationKey(org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.CLOSE_STEP)
                    :!decoderBoundary?ACTION:new OperationKey(actualKind==RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION
                    ?OrdinaryInteractionCodec.INITIATE_STEP:ChildEducationFocus.SUBMIT_STEP);
            var fixtureRef=new AtomicReference<ActionWriterIntegrationFixture>();
            var authorityRef=new AtomicReference<RootReconciliationAuthority>();
            var queryRef=new AtomicReference<ReadContract<?>>();
            var guardRef=new AtomicReference<RootReconciliationReadGuard>();
            var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario(decoderBoundary?Build.CROZIER4.sha256().toLowerCase(java.util.Locale.ROOT):"0".repeat(64),"fixture",source->{
                if(actualKind==RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS){
                    var ordinary=ClockStatusRead.registeredContract(source);
                    ordinaryStatus.set(ordinary);
                    var status=RootUnknownSentinelReadProfile.registeredContract(ordinary);
                    statusProfile.set(status);queryRef.set(status);return List.of(ordinary,status);
                }
                if(actualKind==RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE){
                    // Descriptor DATA only. The real canonical UNKNOWN below lacks genuine private M3/once custody
                    // and must be refused by the production Root binder before any query or observer callback.
                    var operation=new OperationKey(org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.QUERY_STEP);
                    var contract=new ReadContract<RawJson>(RootPendingUiCloseReconciliation.CONTRACT,operation,Optional.empty(),
                            "allow_private_current_timeline_blocker_query",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                            ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.RECONCILIATION_OBSERVATION,source,
                            (request,id)->new NativeRequest(operation.value(),Optional.empty(),raw("{}")),
                            receipt->receipt.original().originalResultToken().orElseThrow(),
                            receipt->receipt.original().originalResultToken().orElseThrow());
                    queryRef.set(contract);return List.of(contract);
                }
                if(actualKind==RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION){
                    var factory=GuardianReconciliationFamilyAdmissionTest.factory(source,source,new GuardianReconciliationQueries.CanonicalAdmission(){
                        @Override public void verifyCurrent(PlanningReadRequest request){requireDecoderCurrent(request,fixtureRef.get(),authorityRef.get());}
                        @Override public void verifyOriginal(PlanningReadReceipt receipt){requireDecoderOriginal(receipt,fixtureRef.get(),authorityRef.get());}
                    });
                    guardianProfile.set(factory);queryRef.set(factory.contract());return List.of(factory.contract());
                }
                if(actualKind==RootReconciliationAuthority.QueryKind.CHILD_EDUCATION_FOCUS_RECEIPT){
                    var ordinary=org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries.contracts(source,
                            (request,pending)->{throw new AssertionError("an unrelated original cannot acquire ordinary focus admission");}).receipt();
                    var focus=org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries.reconciliationReceipt(ordinary,source,
                            new org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries.CanonicalAdmission(){
                                @Override public void verifyCurrent(PlanningReadRequest request,org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.Pending pending){
                                    requireDecoderCurrent(request,fixtureRef.get(),authorityRef.get());
                                }
                                @Override public void verifyOriginal(PlanningReadReceipt receipt,org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.Pending pending){
                                    requireDecoderOriginal(receipt,fixtureRef.get(),authorityRef.get());
                                }
                            });
                    queryRef.set(focus);return List.of(focus);
                }
                var contract=new ReadContract<RawJson>("software-reconciliation-query/v1",QUERY,Optional.of(CAP),CAP,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                        ReadContract.GuardMode.RECONCILIATION_OBSERVATION,source,request->{
                            assertEquals(ARGS,request.arguments());
                            return new NativeRequest(QUERY.value(),Optional.of(CAP),raw("{}"));
                        },receipt->receipt.original().originalResultToken().orElseThrow());
                queryRef.set(contract);return List.of(contract);
            },request->{
                assertEquals(queryRef.get().operation().value(),request.step());
                if(!decoderBoundary)assertEquals(raw("{}"),request.additionalFields());
                return actualKind==RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS
                        ?RootUnknownSentinelReadProfileTest.statusResult():raw("{\"software_read_only_observed\":true}");
            },decoderBoundary?Optional.of(Build.CROZIER4.version()):Optional.empty(),
                    actualKind==RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS?Set.of(ClockStatusRead.STATUS_CAP):Set.of());
            var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(actualAction,"game.command.pause-map",(original,attempt,dispatch)->{
                if(!ActionReconciliationScope.activeFor(original))
                    return new ActionPorts.Pending("original ACK is not independently observed business",List.of(attempt.guard().nativeEvidence()));
                try{
                    var fixture=fixtureRef.get();var authority=authorityRef.get();var same=fixture.journal.borrowedWriterSession();
                    var frame=ActionReconciliationScope.requireFrame(original,attempt);
                    var identity=ActionReconciliationScope.requireIdentity(original,attempt);
                    var observation=ActionReconciliationScope.requireObservationGuard(original,attempt);
                    String head=same.head().digest();int worldWrites=fixture.nativeActionWrites();
                    scopeCalls.incrementAndGet();push.set(observation);
                    assertTrue(authority.hasActiveFor(same,original));
                    authority.currentForCommand(same,original,lease->{
                        escaped.set(lease);assertSame(frame,lease.complete());assertSame(identity,lease.identity());assertSame(observation,lease.observationGuard());
                        assertThrows(IllegalArgumentException.class,()->authority.withPublicWindowSnapshot(same,lease.canonical(),lease.validUntil(),
                                ignored->{throw new AssertionError("an active reconciliation scope cannot become a public-window issuer");}));
                        assertEquals(frame.identity(),authority.verifyArchived(observation,fixture.archive.withSession(same),same,fixture.physicalInputs().originals()).identity());
                        var wrong=new ActionCommand(original.actionId()+"-other",original.before(),original.source(),original.sessionId(),
                                original.operation(),original.arguments(),original.expected(),original.claims(),original.deadline());
                        assertThrows(IllegalArgumentException.class,()->authority.currentForCommand(same,wrong,ignored->null));
                        assertThrows(IllegalArgumentException.class,()->ActionReconciliationScope.requireFrame(wrong));
                        var wrongAttempt=new ActionState.Attempt(attempt.requestId()+"-other",attempt.submittedAt(),attempt.guard(),attempt.preparedRequest());
                        assertThrows(IllegalArgumentException.class,()->ActionReconciliationScope.requireIdentity(original,wrongAttempt));
                        if(queryEnabled){
                            var arguments=decoderBoundary?boundaryArguments(lease.canonical(),identity,frame,lease.validUntil())
                                    :kind==RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS?new OpportunityJson.Obj(Map.of()):ARGS;
                            var request=PlanningReadRequest.newReconciliation(identity,queryRef.get().operation(),arguments,lease.validUntil());
                            PlanningReadResult<?> result;
                            if(kind==RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS){
                                var typed=fixture.reads.read(same,statusProfile.get(),request);
                                if(typed instanceof PlanningReadResult.Known<org.xar.ck3.control.reconciliation.LateOutcome.Status> actualKnown)
                                    statusKnown.set(actualKnown);
                                result=typed;
                            }else result=fixture.reads.read(same,queryRef.get(),request);
                            final PlanningReadReceipt receipt;
                            if(decoderBoundary){
                                assertInstanceOf(PlanningReadResult.Unavailable.class,result,"the boundary callback explicitly refuses business success");
                                assertEquals(1,decoderAdmissions.get(),"the actual producer guard/packet must reach mandatory original admission");
                                receipt=issued.get();assertNotNull(receipt);
                                fixture.archive.withSession(same).preserveRead(receipt); // Immutable actual read, never a Known/domain success.
                            }else{
                                var known=assertInstanceOf(PlanningReadResult.Known.class,result);receipt=known.receipt();issued.set(receipt);
                            }
                            assertInstanceOf(PlanningReadGuard.Reconciliation.class,receipt.before().readiness());
                            assertInstanceOf(PlanningReadGuard.Reconciliation.class,receipt.after().readiness());
                            assertEquals(receipt,fixture.archive.withSession(same).loadRead(fixture.archive.withSession(same).readReferenceOf(receipt)));
                            assertEquals(queryRef.get().operation(),receipt.request().operation());assertEquals(identity.factual(),receipt.request().reconciliationBefore());
                            assertThrows(IllegalStateException.class,receipt.request()::before);
                            for(var binding:List.of(receipt.before().binding(),receipt.after().binding()))
                                assertEquals(frame.identity(),authority.verifyArchived(binding,fixture.archive.withSession(same),same,fixture.physicalInputs().originals()).identity());
                            int queries=fixture.scenarioReadWrites();
                            var changedArguments=kind==RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS
                                    ?new OpportunityJson.Obj(Map.of("foreign",new OpportunityJson.Bool(true))):new OpportunityJson.Obj(Map.of());
                            var changed=PlanningReadRequest.newReconciliation(identity,queryRef.get().operation(),changedArguments,lease.validUntil());
                            assertThrows(IllegalArgumentException.class,()->guardRef.get().verify(same.head(),changed,queryRef.get()));
                            assertEquals(queries,fixture.scenarioReadWrites(),"altered intent arguments must fail before another Native query");
                        }
                        assertEquals(head,same.head().digest(),"no READ history or domain publication is permitted inside the reconciliation callback");
                        assertEquals(worldWrites,fixture.nativeActionWrites());return null;
                    });
                    assertEquals(head,same.head().digest());
                    return new ActionPorts.Pending("actual read-only reconciliation captured; no fixture Game effect is claimed",observation.supportingEvidence());
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            },()->{});
            actual=new ActionWriterIntegrationFixture(root,false,reads,List.of(action));fixtureRef.set(actual);query=queryRef.get();
            var inputs=actual.physicalInputs();
            physical=new RootLifecycleAuthority(actual.writer,actual.archive,inputs.transport(),inputs.driverAssembler(),inputs.observationAssembler(),
                    inputs.source(),(same,session,source,packet,diagnostics,deadline)->{
                        actual.writer.requireSession(same);assertEquals(inputs.source(),source);assertEquals(session,diagnostics.session().orElseThrow());
                        actual.archive.readArtifact(same,packet,WriterContracts.MAX_PIN_BYTES);
                        var pin=same.capturePin(source.sourceRef(),65536);same.verifyPin(pin);
                        // This finite software source never qualifies a Managed package. Its Witness is the
                        // real source file observed now, never a FileID reconstructed from the fixture hash.
                        var live=SharedSourceFiles.observe(Path.of(source.sourceRef().path()));
                        assertEquals(source.sourceRef().bytes(),live.source().bytes());assertEquals(source.sourceRef().sha256(),live.source().sha256());
                        var physical=live.nativeFile();
                        var witness=new NativeSourceFileIdentity.SourceWitness(
                                new ExactRef(live.source().path(),live.source().bytes(),live.source().sha256()),
                                new NativeSourceFileIdentity(physical.volumeSerialDecimal(),physical.fileIdDecimal(),physical.legacyVolumeSerialDecimal(),
                                        physical.legacyFileIdHex(),physical.creationFiletimeDecimal(),physical.lastWriteFiletimeDecimal(),physical.changeFiletimeDecimal(),
                                        physical.logicalBytes(),physical.allocatedBytes(),physical.linkCount()));
                        var normalized=new ExactRef(NativeSourceProofDocument.pathKey(source.sourceRef().path()),source.sourceRef().bytes(),source.sourceRef().sha256());
                        var epoch=StrictJson.object().put("schema","xar.java-root-source-epoch/v1").put("machine_id",source.machineId());
                        var rows=epoch.putArray("inputs");
                        for(String role:List.of("java_runtime","native_source","bridge_dll","injector","game_executable","launcher_settings").stream().sorted().toList())
                            rows.addObject().put("role",role).set("source",normalized.toJson());
                        var epochRef=actual.archive.preserveArtifact(same,StrictJson.canonical(epoch,65536),65536);
                        var epochPin=same.capturePin(epochRef,65536);same.verifyPin(epochPin);
                        var proof=new NativeSourceProofDocument(source.machineId(),session.sessionId(),Instant.now().toString(),
                                NativeSourceProofDocument.Mode.MCP_STDIO,source.sourceRef(),source.sourceRef(),epochRef.sha256(),epochRef,
                                source.sourceRef(),List.of(source.sourceRef()),List.of(witness));
                        byte[] proofBytes=NativeSourceProofCodec.encode(proof);
                        assertEquals(proof,NativeSourceProofCodec.decode(proofBytes));
                        var ref=actual.archive.preserveArtifact(same,proofBytes,16<<20);
                        return new NativeReadinessCollector.SourceQualification(ref,borrowed->{
                            actual.writer.requireSession(borrowed);assertSame(same,borrowed);borrowed.verifyPin(pin);borrowed.verifyPin(epochPin);
                            SharedSourceFiles.assertUnchanged(live);sourceChecks.incrementAndGet();
                        });
                    },Clock.systemUTC(),Duration.ofSeconds(30));
            var pending=new ReconciliationPendingBinding(actual.writer,actual.archive,inputs.originals());
            reconciliation=new RootReconciliationAuthority(actual.writer,actual.archive,physical,pending,inputs.originals(),inputs.frameLoader(),
                    actual.actualReadCatalog(),(original,identity,data,deadline)->{
                        assertEquals(actualAction,original.command().operation());assertEquals(original.command().before(),identity.pending().originalBefore());
                        assertEquals(data.identity(),identity.factual());
                        ReadContract<?> selected=query;
                        if(replaceSource){
                            var ref=query.sourceRef();
                            var foreign=new ExactRef(ref.path(),ref.bytes(),"f".repeat(64));
                            selected=new ReadContract<>(query.contractId(),query.operation(),query.requiredCapability(),query.permissionKey(),
                                    query.permissionMode(),query.wireProfile(),query.guardMode(),foreign,
                                    (request,requestId)->query.prepare(request,requestId),query::decode,query::replay);
                        }
                        if(actualKind==RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE){
                            closeCandidates.incrementAndGet();
                            return List.of(new RootReconciliationAuthority.AllowedRead(selected,new OpportunityJson.Obj(Map.of()),actualKind));
                        }
                        var arguments=decoderBoundary?boundaryArguments(original,identity,data,deadline)
                                :kind==RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS?new OpportunityJson.Obj(Map.of()):ARGS;
                        return queryEnabled?List.of(new RootReconciliationAuthority.AllowedRead(selected,arguments,actualKind)):List.of();
                    },Clock.systemUTC());
            authorityRef.set(reconciliation);
            reconciliation.requireOwner(actual.writer,actual.archive,actual.actualReadCatalog(),physical);
            assertThrows(IllegalArgumentException.class,()->reconciliation.requireOwner(actual.writer,actual.archive,
                    RootReadContractCatalog.staticOnly(List.of()),physical));
            readGuard=new RootReconciliationReadGuard(reconciliation,()->{
                try{return actual.writer.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}
            },actual.archive,inputs.source(),Clock.systemUTC(),"software-reconciliation-query-authority",inputs.originals(),actual.actualReadCatalog());
            guardRef.set(readGuard);actual.bindReconciliationReadGuard(readGuard);
            actual.coordinator.bindReconciliationObservation((same,pendingReceipt,deadline,work)->
                    reconciliation.observe(same,pendingReceipt,deadline,lease->work.apply(lease.complete(),lease.provenance(),lease.identity(),lease.observationGuard())));
        }
        void executeOriginal()throws Exception{executeOriginal(false);}
        void executeOriginal(boolean changedPlayer)throws Exception{
            if(decoderBoundary){
                actual.ready();enqueueBoundarySnapshot();
                var ready=actual.ready();var request=ready.request();
                OpportunityJson.Obj intent;
                if(kind==RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION)
                    intent=new org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent("educate_child_interaction",77,
                            Optional.of(new org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent.Education(78,79,List.of())),Optional.empty()).toJson();
                else intent=new org.xar.ck3.control.application.action.family.ChildEducationFocusIntent(78,
                        org.xar.ck3.control.application.action.family.ChildEducationFocusIntent.FocusKey.EDUCATION_LEARNING,Optional.empty()).toJson();
                var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),
                        "xar.java.family-action-observation/v1",List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(
                                new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("paused"),true)));
                command=new ActionCommand("canonical-unresolved-decoder-boundary",request.before(),request.source(),request.sessionId(),actualAction,intent,expected,
                        new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
            }else if(kind==RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE){
                var base=actual.command("canonical-close-without-private-once-source");
                var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,base.before(),base.source(),
                        "xar.java.pending-successor-modal-close/v1",base.expected().values());
                command=new ActionCommand(base.actionId(),base.before(),base.source(),base.sessionId(),actualAction,base.arguments(),
                        expected,base.claims(),base.deadline());
            }else command=actual.command("canonical-unresolved-software-action");
            firstUnknown=actual.coordinator.execute(command);assertInstanceOf(ActionState.Unknown.class,firstUnknown.state());
            assertEquals(1,actual.nativeActionWrites());assertEquals(0,actual.scenarioReadWrites());assertEquals(0,scopeCalls.get());
            var previous=actual.physicalInputs().transport().latestObservedSnapshot().orElseThrow();
            ObjectNode envelope=StrictJson.object().put("type","state_snapshot").put("protocol_version",1)
                    .put("snapshot_id",decoderBoundary?"native:"+previous.nativeRevision().add(BigInteger.ONE):"actual-post-attempt-snapshot")
                    .put("revision",previous.nativeRevision().add(BigInteger.ONE));
            ObjectNode state=(ObjectNode)StrictJson.parse(previous.state().bytes(),DriverJson.MAX_NATIVE_BYTES);
            if(changedPlayer)state.set("played_character",StrictJson.object().put("character_id",74).put("alive",true));
            envelope.set("state",state);
            actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(envelope,DriverJson.MAX_NATIVE_BYTES)));
        }
        private void enqueueBoundarySnapshot()throws IOException{
            var previous=actual.physicalInputs().transport().latestObservedSnapshot().orElseThrow();
            var state=(ObjectNode)StrictJson.parse(previous.state().bytes(),DriverJson.MAX_NATIVE_BYTES);
            var player=(ObjectNode)state.get("played_character");player.putArray("spouse_ids");player.putNull("betrothed_id");
            state.put("local_player_id",73);
            var revision=previous.nativeRevision().add(BigInteger.ONE);
            var envelope=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:"+revision).put("revision",revision);
            envelope.set("state",state);actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(envelope,DriverJson.MAX_NATIVE_BYTES)));
        }
        private OpportunityJson.Obj boundaryArguments(ActionReceipt original,ReconciliationIdentity identity,DriverObservationAssembler.Complete current,Instant deadline){
            var attempt=ActionTransitions.attempt(original.state()).orElseThrow();
            if(kind==RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION)
                return guardianProfile.get().issue(identity,original.command(),attempt,current,deadline).request().arguments();
            var context=ChildEducationFocusQueries.context(new PlanningReadRequest(original.command().before(),original.command().source(),original.command().sessionId(),
                    new OperationKey(ChildEducationFocus.QUERY_STEP),new OpportunityJson.Obj(Map.of()),deadline));
            var intent=org.xar.ck3.control.application.action.family.ChildEducationFocusIntent.fromJson(original.command().arguments());
            var pending=ChildEducationFocusPendingFixture.fromContext(context,ChildEducationFocusEffects.selection(intent),attempt.requestId());
            return ChildEducationFocusQueries.receiptArguments(new ChildEducationFocusQueries.ReceiptArguments(identity.factual().frame().revision(),pending));
        }
        private void requireDecoderCurrent(PlanningReadRequest request,ActionWriterIntegrationFixture fixture,RootReconciliationAuthority authority){
            assertTrue(decoderBoundary,"unrelated originals cannot reach native profile admission");
            try{var same=fixture.journal.borrowedWriterSession();authority.current(same,request.origin().requireReconciliation(),request.deadline(),lease->{
                if(kind==RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION)
                    GuardianReconciliationQueries.requireOriginalRequest(request,lease.canonical().command(),lease.attempt());
                else ChildEducationFocusQueries.canonicalReceiptArguments(request);
                lease.assertCurrent(same);return null;
            });}catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private void requireDecoderOriginal(PlanningReadReceipt receipt,ActionWriterIntegrationFixture fixture,RootReconciliationAuthority authority){
            assertTrue(decoderBoundary,"unrelated originals cannot reach native profile archive admission");
            try{var same=fixture.journal.borrowedWriterSession();
                for(var guard:List.of(receipt.before().binding(),receipt.after().binding())){
                    assertEquals(1,guard.supportingEvidence().size(),"actual Root representation is one complete source-bound basis");
                    var original=authority.verifyArchived(guard,fixture.archive.withSession(same),same,fixture.physicalInputs().originals());
                    assertEquals(receipt.request().reconciliationBefore(),original.identity());
                }
                issued.set(receipt);decoderAdmissions.incrementAndGet();throw new DecoderBoundaryReached();
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        ActionReceipt reconcile()throws Exception{
            ActionReceipt result=actual.coordinator.reconcile(command.actionId());
            assertInstanceOf(ActionState.Unknown.class,result.state());assertEquals(1,actual.nativeActionWrites());assertEquals(1,scopeCalls.get());
            assertFalse(ActionReconciliationScope.activeFor(command));assertThrows(IllegalArgumentException.class,()->ActionReconciliationScope.requireFrame(command));
            actual.writer.locked(same->{
                assertFalse(reconciliation.hasActiveFor(same,command));
                assertThrows(IllegalArgumentException.class,()->escaped.get().assertCurrent(same));
                assertThrows(IllegalArgumentException.class,()->reconciliation.currentForCommand(same,command,lease->null));
                return null;
            });
            return result;
        }
        @Override public void close()throws IOException{actual.close();}
    }

    @Test void actualUnknownStatusReadUsesTheInstalledClockFactoryCoordinatorArchiveAndMandatoryPublicResultConsumer()throws Exception{
        try(var h=new Harness(temporary.resolve("unknown-status"),true,RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS)){
            h.executeOriginal();h.reconcile();assertEquals(1,h.actual.scenarioReadWrites());assertEquals(1,h.actual.nativeActionWrites());
            var known=h.statusKnown.get();assertNotNull(known,"actual installed query must return its real typed Known result");
            RootUnknownSentinelReadProfileTest.assertActualRead(h.statusProfile.get(),known,h.actual.archive);
            assertEquals(1,h.actual.nativeActionWrites(),"pure Status and cold/public formatting cannot replay UNKNOWN");
        }
    }

    @Test void canonicalUnknownUsesOneRealRootScopeAndTheSameCatalogTransportAndArchiveWithoutReplay()throws Exception{
        try(var h=new Harness(temporary.resolve("query"),true)){
            h.executeOriginal();h.reconcile();assertEquals(1,h.actual.scenarioReadWrites());assertTrue(h.sourceChecks.get()>2);
            int queries=h.actual.scenarioReadWrites(),world=h.actual.nativeActionWrites();
            h.actual.writer.locked(same->{
                var bound=h.actual.archive.withSession(same);var originals=h.actual.physicalInputs().originals();
                assertEquals(h.push.get().origin().requireReconciliation().factual(),h.reconciliation.verifyArchived(h.push.get(),bound,same,originals).identity());
                for(var guard:List.of(h.issued.get().before().binding(),h.issued.get().after().binding()))
                    h.reconciliation.verifyArchived(guard,bound,same,originals);
                return null;
            });
            assertEquals(queries,h.actual.scenarioReadWrites(),"historical replay must perform no Native I/O");
            assertEquals(world,h.actual.nativeActionWrites());
        }
    }

    @Test void canonicalUnknownCannotAcquireWindow2ByRelabelingAnotherInstalledReadonlyFamily()throws Exception{
        try(var h=new Harness(temporary.resolve("window2-family-confusion"),true,RootReconciliationAuthority.QueryKind.WINDOW2)){
            h.executeOriginal();
            var result=h.actual.coordinator.reconcile(h.command.actionId());
            assertInstanceOf(ActionState.Unknown.class,result.state(),"failed admission retains canonical UNKNOWN");
            assertEquals(1,h.actual.nativeActionWrites(),"failed Window2 admission cannot replay the canonical UNKNOWN action");
            assertEquals(0,h.actual.scenarioReadWrites());assertEquals(0,h.scopeCalls.get());
            h.actual.writer.locked(same->{
                assertFalse(h.reconciliation.hasActiveFor(same,h.command));return null;
            });
        }
    }

    @Test void unrelatedCanonicalUnknownCannotBorrowPublicWindowPhysicalOrSemanticAuthority()throws Exception {
        try(var h=new Harness(temporary.resolve("public-window-unrelated-unknown"),false)) {
            h.executeOriginal();
            var transport=h.actual.physicalInputs().transport();var nativeBefore=transport.latestObservedSnapshot();
            int sourceChecks=h.sourceChecks.get(),queries=h.actual.scenarioReadWrites(),actions=h.actual.nativeActionWrites();
            h.actual.writer.locked(same->{
                String head=same.head().digest();
                assertThrows(IllegalArgumentException.class,()->h.reconciliation.withPublicWindowSnapshot(same,h.firstUnknown,
                        Instant.now().plusSeconds(5),ignored->{throw new AssertionError("unrelated UNKNOWN cannot reach the physical callback");}));
                assertThrows(IllegalArgumentException.class,()->h.reconciliation.withPublicWindowSnapshot(same,h.firstUnknown,
                        Instant.EPOCH,ignored->{throw new AssertionError("expired public window input cannot reach the physical callback");}));
                assertEquals(head,same.head().digest());assertFalse(h.reconciliation.hasActiveFor(same,h.command));return null;
            });
            assertEquals(nativeBefore,transport.latestObservedSnapshot(),"refusal must happen before another Native observation");
            assertEquals(sourceChecks,h.sourceChecks.get());assertEquals(queries,h.actual.scenarioReadWrites());assertEquals(actions,h.actual.nativeActionWrites());
        }
    }
    @Test void aReadWithTheSameOperationAndProfileButAnotherSourceCannotReplaceTheActualInstalledCatalogInstance()throws Exception{
        try(var h=new Harness(temporary.resolve("reconciliation-foreign-source"),true,RootReconciliationAuthority.QueryKind.COMMANDER_CANDIDATES,true)){
            h.executeOriginal();
            var result=h.actual.coordinator.reconcile(h.command.actionId());
            assertInstanceOf(ActionState.Unknown.class,result.state());
            assertEquals(1,h.actual.nativeActionWrites());assertEquals(0,h.actual.scenarioReadWrites());assertEquals(0,h.scopeCalls.get());
            h.actual.writer.locked(same->{assertFalse(h.reconciliation.hasActiveFor(same,h.command));return null;});
        }
    }
    @Test void anUnrelatedCanonicalUnknownCannotUseTheActualIndependentChildFocusReceiptProducer()throws Exception{
        try(var h=new Harness(temporary.resolve("focus-unrelated-original"),true,RootReconciliationAuthority.QueryKind.CHILD_EDUCATION_FOCUS_RECEIPT)){
            h.executeOriginal();
            var result=h.actual.coordinator.reconcile(h.command.actionId());
            assertInstanceOf(ActionState.Unknown.class,result.state());
            assertEquals(1,h.actual.nativeActionWrites());assertEquals(0,h.actual.scenarioReadWrites());assertEquals(0,h.scopeCalls.get());
            h.actual.writer.locked(same->{assertFalse(h.reconciliation.hasActiveFor(same,h.command));return null;});
        }
    }
    @Test void anUnrelatedCanonicalUnknownCannotUseTheActualIndependentGuardianQueryProducer()throws Exception{
        try(var h=new Harness(temporary.resolve("guardian-unrelated-original"),true,RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION)){
            h.executeOriginal();
            var result=h.actual.coordinator.reconcile(h.command.actionId());
            assertInstanceOf(ActionState.Unknown.class,result.state());
            assertEquals(1,h.actual.nativeActionWrites());assertEquals(0,h.actual.scenarioReadWrites());assertEquals(0,h.scopeCalls.get());
            h.actual.writer.locked(same->{assertFalse(h.reconciliation.hasActiveFor(same,h.command));return null;});
        }
    }
    @Test void canonicalUnknownCloseWithoutGenuineM3OnceAndPreparationOriginalsCannotReadTimeline()throws Exception{
        try(var h=new Harness(temporary.resolve("close-missing-private-custody"),true,RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE)){
            h.executeOriginal();
            assertTrue(ActionTransitions.attempt(h.firstUnknown.state()).orElseThrow().preparedRequest().preparationEvidence().isEmpty());
            var result=h.actual.coordinator.reconcile(h.command.actionId());
            assertInstanceOf(ActionState.Unknown.class,result.state(),"descriptor DATA cannot manufacture private pending M3/once authority");
            assertEquals(h.firstUnknown.command(),result.command());assertEquals(h.firstUnknown.bodySha256(),result.bodySha256());
            assertEquals(1,h.closeCandidates.get(),"actual original UNKNOWN and fresh Root physical source reached the finite policy");
            assertTrue(h.sourceChecks.get()>0);
            assertEquals(1,h.actual.nativeActionWrites(),"failed Close admission must never repeat the original action");
            assertEquals(0,h.actual.scenarioReadWrites());assertEquals(0,h.scopeCalls.get());
            h.actual.writer.locked(same->{assertFalse(h.reconciliation.hasActiveFor(same,h.command));return null;});
        }
    }
    @Test void pendingCloseDescriptorWithAnotherSourceCannotEnterTheActualInstalledReadCatalog()throws Exception{
        try(var h=new Harness(temporary.resolve("close-foreign-profile-source"),true,RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE,true)){
            h.executeOriginal();var result=h.actual.coordinator.reconcile(h.command.actionId());
            assertInstanceOf(ActionState.Unknown.class,result.state());
            assertEquals(1,h.closeCandidates.get());
            assertEquals(1,h.actual.nativeActionWrites());assertEquals(0,h.actual.scenarioReadWrites());assertEquals(0,h.scopeCalls.get());
            h.actual.writer.locked(same->{assertFalse(h.reconciliation.hasActiveFor(same,h.command));return null;});
        }
    }
    @Test void actualRootSingleBasisAndWireCustodyReachTheFocusOriginalAdmissionWithoutBusinessCredit()throws Exception{
        assertActualDecoderBoundary("focus-root-basis",RootReconciliationAuthority.QueryKind.CHILD_EDUCATION_FOCUS_RECEIPT);
    }
    @Test void actualRootSingleBasisAndWireCustodyReachTheGuardianOriginalAdmissionWithoutBusinessCredit()throws Exception{
        assertActualDecoderBoundary("guardian-root-basis",RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION);
    }
    private void assertActualDecoderBoundary(String name,RootReconciliationAuthority.QueryKind kind)throws Exception{
        try(var h=new Harness(temporary.resolve(name),true,kind,false,true)){
            h.executeOriginal();h.reconcile();
            assertEquals(1,h.decoderAdmissions.get(),"actual Root-produced guards must pass the profile's representation and original packet checks");
            assertEquals(1,h.actual.scenarioReadWrites());int world=h.actual.nativeActionWrites(),queries=h.actual.scenarioReadWrites();
            h.actual.writer.locked(same->{
                var original=h.issued.get();assertNotNull(original);
                for(var guard:List.of(original.before().binding(),original.after().binding()))assertEquals(1,guard.supportingEvidence().size());
                assertThrows(DecoderBoundaryReached.class,()->h.query.replay(original));
                assertEquals(2,h.decoderAdmissions.get(),"archived replay must reach the same mandatory actual Root verifier, then refuse success");
                var guard=original.before().binding();
                assertThrows(IllegalArgumentException.class,()->new GuardEvidence(guard.origin(),guard.source(),guard.sessionId(),guard.connectionGeneration(),
                        guard.operation(),guard.nativeEvidence(),guard.capabilityEvidence(),guard.authorityId(),guard.observedAt(),guard.validUntil(),List.of()));
                var basis=guard.supportingEvidence().getFirst();
                var changed=new GuardEvidence(guard.origin(),guard.source(),guard.sessionId(),guard.connectionGeneration(),guard.operation(),
                        guard.nativeEvidence(),guard.capabilityEvidence(),guard.authorityId(),guard.observedAt(),guard.validUntil(),
                        List.of(new ExactRef(basis.path(),basis.bytes(),"f".repeat(64))));
                assertThrows(UncheckedIOException.class,()->h.query.replay(replaceBefore(original,changed)));
                var bound=h.actual.archive.withSession(same);
                ObjectNode future=(ObjectNode)StrictJson.parse(bound.loadMaterial(basis).bytes(),128<<10);
                future.set("writer_point",StrictJson.object().put("sequence",same.head().state().sequence()+1).put("digest","f".repeat(64)));
                assertThrows(UncheckedIOException.class,()->h.query.replay(replaceBefore(original,replaceBasis(guard,future,bound))));
                assertEquals(2,h.decoderAdmissions.get(),"changed basis/history cannot pass actual original admission");
                return null;
            });
            assertEquals(queries,h.actual.scenarioReadWrites(),"domain replay never issues another native query");
            assertEquals(world,h.actual.nativeActionWrites(),"all decoder refusals retain the same canonical UNKNOWN without replay");
        }
    }
    private static PlanningReadReceipt replaceBefore(PlanningReadReceipt original,GuardEvidence changed){
        var before=new PlanningReadGuard(changed,new PlanningReadGuard.Reconciliation(),original.before().originalBindingSha256());
        return new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),before,original.after(),original.original());
    }

    @Test void pushOnlyUnknownKeepsItsOwnColdQualificationWithoutInventingAQuery()throws Exception{
        try(var h=new Harness(temporary.resolve("push-only"),false)){
            h.executeOriginal();h.reconcile();assertEquals(0,h.actual.scenarioReadWrites());assertNull(h.issued.get());
            h.actual.writer.locked(same->{
                var guard=h.push.get();var bound=h.actual.archive.withSession(same);
                var body=StrictJson.parse(bound.loadMaterial(guard.supportingEvidence().getFirst()).bytes(),128<<10);
                assertEquals("PUSH_OBSERVATION",StrictJson.text(body.get("role")));assertTrue(body.get("read").isNull());
                assertEquals(h.command.operation(),guard.operation());
                assertEquals(guard.origin().requireReconciliation().factual(),
                        h.reconciliation.verifyArchived(guard,bound,same,h.actual.physicalInputs().originals()).identity());
                return null;
            });
            assertEquals(1,h.actual.nativeActionWrites());
        }
    }

    @Test void actualColdQualificationRejectsFutureWriterPointsWrongRolesAndAlteredNativeOriginals()throws Exception{
        try(var h=new Harness(temporary.resolve("tampered"),true)){
            h.executeOriginal();h.reconcile();
            h.actual.writer.locked(same->{
                var guard=h.push.get();var bound=h.actual.archive.withSession(same);var originals=h.actual.physicalInputs().originals();
                ObjectNode actual=(ObjectNode)StrictJson.parse(bound.loadMaterial(guard.supportingEvidence().getFirst()).bytes(),128<<10);
                ObjectNode future=actual.deepCopy();future.set("writer_point",StrictJson.object().put("sequence",same.head().state().sequence()+1).put("digest","f".repeat(64)));
                var futureGuard=replaceBasis(guard,future,bound);
                assertThrows(IOException.class,()->h.reconciliation.verifyArchived(futureGuard,bound,same,originals));
                var anchor=ContinuityState.fromJson(StrictJson.parse(Files.readAllBytes(h.actual.root.resolve("anchor.json")),ContinuityJson.DOCUMENT_MAX_BYTES),h.command.source().machineId());
                ObjectNode beforePending=actual.deepCopy();beforePending.set("writer_point",StrictJson.object().put("sequence",0).put("digest",ContinuityJson.digest(anchor.toJson())));
                assertThrows(IOException.class,()->h.reconciliation.verifyArchived(replaceBasis(guard,beforePending,bound),bound,same,originals));
                ObjectNode wrongRole=actual.deepCopy().put("role","PURE_QUERY");
                assertThrows(IllegalArgumentException.class,()->h.reconciliation.verifyArchived(replaceBasis(guard,wrongRole,bound),bound,same,originals));
                ObjectNode wrongNative=actual.deepCopy();var identity=guard.origin().requireReconciliation();var evidence=identity.evidence();
                var wrongRef=new ExactRef(evidence.actualNativePacket().path(),evidence.actualNativePacket().bytes(),"f".repeat(64));
                var changed=new ReconciliationIdentity(identity.factual(),identity.source(),identity.sessionId(),identity.connectionGeneration(),identity.pending(),
                        new ReconciliationIdentity.Evidence(wrongRef,evidence.actualHello(),evidence.originalHeartbeat(),evidence.observationManifest(),
                                evidence.currentOriginalDriver(),evidence.completeSourceQualification()),identity.observedAt());
                wrongNative.set("identity",ReconciliationIdentityCodec.encode(changed));
                var basis=bound.preserveMaterial(new RawJson(StrictJson.canonical(wrongNative,128<<10)));
                var corrupted=new GuardEvidence(new CommandOrigin.Reconciliation(changed),guard.source(),guard.sessionId(),guard.connectionGeneration(),
                        guard.operation(),wrongRef,guard.capabilityEvidence(),guard.authorityId(),guard.observedAt(),guard.validUntil(),List.of(basis));
                assertThrows(Exception.class,()->h.reconciliation.verifyArchived(corrupted,bound,same,originals));return null;
            });
            assertEquals(1,h.actual.nativeActionWrites());assertEquals(1,h.actual.scenarioReadWrites());
        }
    }
    @Test void changedPlayerReturnsActualQualifiedRawOriginalsWithoutFakeCompleteOrAQuery()throws Exception{
        try(var h=new Harness(temporary.resolve("changed-player"),true)){
            h.executeOriginal(true);var result=h.actual.coordinator.reconcile(h.command.actionId());
            var unknown=assertInstanceOf(ActionState.Unknown.class,result.state());
            assertEquals(0,h.scopeCalls.get());assertNull(h.push.get());assertNull(h.issued.get());
            assertEquals(1,h.actual.nativeActionWrites());assertEquals(0,h.actual.scenarioReadWrites());
            assertTrue(unknown.evidence().size()>=7,"raw-only Pending must preserve actual Native/hello/heartbeat/manifest/Driver/semantic/source originals");
            h.actual.writer.locked(same->{
                for(var ref:unknown.evidence())assertEquals(ref.bytes(),h.actual.archive.readArtifact(same,ref,WriterContracts.MAX_PIN_BYTES).length);
                assertFalse(h.reconciliation.hasActiveFor(same,h.command));return null;
            });
        }
    }
    private static GuardEvidence replaceBasis(GuardEvidence original,ObjectNode row,ActionPorts.OutcomeArchive archive){
        ExactRef basis=archive.preserveMaterial(new RawJson(StrictJson.canonical(row,128<<10)));
        return new GuardEvidence(original.origin(),original.source(),original.sessionId(),original.connectionGeneration(),original.operation(),
                original.nativeEvidence(),original.capabilityEvidence(),original.authorityId(),original.observedAt(),original.validUntil(),List.of(basis));
    }
}

