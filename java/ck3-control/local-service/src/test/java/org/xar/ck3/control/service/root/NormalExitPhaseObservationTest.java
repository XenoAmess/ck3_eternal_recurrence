package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.normalexit.NormalExitPhaseObservation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual software transport/chronology/coordinator/archive to structural DATA/codec. This is not native UI, Managed/Core or Game qualification. */
final class NormalExitPhaseObservationTest {
    @TempDir Path temporary;
    @Test void soleProtocolDataEncoderDecoderFeedsTheActualUiProjectorAndAnAckAloneDoesNotConfirmAPhase(){
        var action=NormalExitProtocol.Action.PREPARE_CONFIRMATION;var ack=observation(action,true,false);var after=observation(NormalExitProtocol.Action.QUERY_CONTEXT,true,false);
        var decoded=NormalExitProtocol.decodeObservation(NormalExitProtocol.observationJson(ack),ack.binding(),action);
        assertEquals(Optional.of(NormalExitPhaseObservation.Outcome.CONFIRMATION_VISIBLE),RootNormalExitRuntime.phaseOutcome(action,decoded,after));
        assertTrue(RootNormalExitRuntime.phaseOutcome(action,decoded,decoded).isEmpty());
        var wrongBirth=new NormalExitProtocol.Binding(after.binding().nativeRevision(),after.binding().playerId(),after.binding().gamePid(),after.binding().connectionGeneration(),after.binding().creationFiletime().add(BigInteger.ONE),after.binding().sourceInventorySha256());
        var drift=new NormalExitProtocol.Observation(wrongBirth,after.action(),after.status(),after.pumpEpoch(),after.proof(),after.contextSignatureVerified(),after.confirmationVisible(),false,false,after.contextSignature(),after.reason(),after.targets(),after.dispatches(),after.stageConsumed(),after.exitAutosave());
        assertTrue(RootNormalExitRuntime.phaseOutcome(action,decoded,drift).isEmpty());
        assertTrue(RootNormalExitRuntime.phaseOutcome(NormalExitProtocol.Action.CONFIRM_DESKTOP,decoded,after).isEmpty());
    }
    @Test void actualUiProjectorRequiresTheIndependentObservedAutosaveFalseState(){
        var action=NormalExitProtocol.Action.DISABLE_EXIT_AUTOSAVE;var ack=observation(action,true,false);var after=observation(NormalExitProtocol.Action.QUERY_CONTEXT,true,false);
        assertEquals(Optional.of(NormalExitPhaseObservation.Outcome.AUTOSAVE_DISABLED),RootNormalExitRuntime.phaseOutcome(action,ack,after));
        assertTrue(RootNormalExitRuntime.phaseOutcome(action,ack,observation(NormalExitProtocol.Action.QUERY_CONTEXT,true,true)).isEmpty());
    }
    @Test void realIndependentReadsAndAckCustodySettleThreeFinitePhasesWithoutMaterialCreditAndUnblockTheNextAction()throws Exception{
        var actual=new AtomicReference<ActionWriterIntegrationFixture>();var query=new AtomicReference<ReadContract<RawJson>>();var before=new AtomicReference<PlanningReadResult.Known<RawJson>>();var writes=new AtomicInteger();
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"normal-phase-custody-data",source->{
            var selector=NativeStepDiscriminator.NormalExit.QUERY_CONTEXT;
            ReadContract<RawJson> contract=new ReadContract<>("normal-phase-query-custody/v1",selector.operationKey(),Optional.of(selector.capability()),selector.capability(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                    ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(request,id)->request(request.before(),source,id,selector),receipt->receipt.original().originalResultToken().orElseThrow());query.set(contract);return List.of(contract);
        },request->raw(StrictJson.object().put("software_context_custody_only",true)));
        var scenarios=new ArrayList<ActionWriterIntegrationFixture.SoftwareActionScenario>();
        for(var phase:NormalExitPhaseObservation.Phase.values()){
            ActionPorts.PostconditionPort projection=(command,attempt,dispatch)->{
                var fixture=actual.get();try{var same=fixture.journal.borrowedWriterSession();var archive=fixture.archive.withSession(same);
                    return fixture.collector.current(same,command.before(),command.deadline(),lease->{
                        var after=known(fixture.reads.read(same,query.get(),new PlanningReadRequest(lease.frame().identity(),command.source(),command.sessionId(),query.get().operation(),new OpportunityJson.Obj(Map.of()),command.deadline())));
                        var outcome=phase==NormalExitPhaseObservation.Phase.DISABLE_EXIT_AUTOSAVE?NormalExitPhaseObservation.Outcome.AUTOSAVE_DISABLED:NormalExitPhaseObservation.Outcome.CONFIRMATION_VISIBLE;
                        var value=new NormalExitPhaseObservation(phase,outcome,command.actionId(),ActionCodec.bodySha256(command),attempt.requestId(),archive.referenceOf(dispatch),archive.requestReferenceOf(attempt.preparedRequest()),command.before(),lease.frame().identity(),command.source(),command.sessionId(),before.get().originalReceipt(),before.get().receipt(),after.originalReceipt(),after.receipt());
                        value.validate(command,attempt,dispatch,archive);assertEquals(value,NormalExitPhaseObservation.decode(value.encode(archive),archive));
                        var wrongPhase=value.encode(archive);wrongPhase.put("phase","CONFIRM_DESKTOP");assertThrows(IllegalArgumentException.class,()->NormalExitPhaseObservation.decode(wrongPhase,archive));
                        var missing=value.encode(archive);missing.remove("after_context_ref");assertThrows(IllegalArgumentException.class,()->NormalExitPhaseObservation.decode(missing,archive));
                        var stale=new NormalExitPhaseObservation(phase,outcome,value.actionId(),value.commandBodySha256(),value.originalRequestId(),value.originalDispatchRef(),value.preparedRequestRef(),value.before(),value.after(),value.source(),value.sessionId(),value.afterContextRef(),value.afterContext(),value.beforeContextRef(),value.beforeContext());
                        assertThrows(IllegalArgumentException.class,()->stale.validate(command,attempt,dispatch));
                        return new ActionPorts.NormalExitPhaseObserved(value);
                    });
                }catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
            };
            scenarios.add(new ActionWriterIntegrationFixture.SoftwareActionScenario(phase.selector().operationKey(),phase.selector().capability(),projection,writes::incrementAndGet,
                    Optional.of(()->raw(StrictJson.object().put("software_ack_custody_only",true))),Optional.empty(),false,
                    Optional.of(command->request(command.before(),command.source().sourceRef(),RequestIds.forCommand(command),phase.selector()))));
        }
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual-software-three-phases"),false,reads,scenarios)){
            actual.set(fixture);
            for(var phase:NormalExitPhaseObservation.Phase.values())fixture.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(phase.selector().operationKey(),fixture.observationSource().sourceRef(),(head,receipt,archive)->{
                var settled=assertInstanceOf(ActionState.Settled.class,receipt.state());var typed=assertInstanceOf(ActionState.NormalExitPhaseConfirmed.class,settled.settlement());typed.observation().validate(receipt.command(),settled.attempt(),settled.dispatch(),archive);
            }));
            for(var phase:NormalExitPhaseObservation.Phase.values()){
                var base=fixture.command("phase-"+phase.name());
                before.set(known(fixture.reads.read(query.get(),new PlanningReadRequest(base.before(),base.source(),base.sessionId(),query.get().operation(),new OpportunityJson.Obj(Map.of()),base.deadline()))));
                var expected=new ProposalLifecycle.ExpectedPostcondition(1,base.before(),base.source(),NormalExitPhaseObservation.SCHEMA,List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"),false)));
                var command=new ActionCommand(base.actionId(),base.before(),base.source(),base.sessionId(),phase.selector().operationKey(),base.arguments(),expected,base.claims(),base.deadline());
                var receipt=fixture.coordinator.execute(command);assertTrue(receipt.settled());assertTrue(receipt.applied().isEmpty());assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
                fixture.writer.locked(same->{var archive=fixture.archive.withSession(same);assertEquals(receipt,archive.loadReceipt(archive.receiptReferenceOf(receipt)));return null;});
                assertEquals(receipt,fixture.coordinator.execute(command));
            }
            assertEquals(3,writes.get());assertEquals(3,fixture.nativeActionWrites());assertEquals(6,fixture.scenarioReadWrites());
        }
    }
    private static PlanningReadResult.Known<RawJson> known(PlanningReadResult<RawJson> value){if(!(value instanceof PlanningReadResult.Known<RawJson> result))throw new AssertionError("actual independent software read unavailable");return result;}
    private static NormalExitProtocol.Observation observation(NormalExitProtocol.Action action,boolean modal,boolean shouldSave){
        var binding=new NormalExitProtocol.Binding(BigInteger.ONE,BigInteger.valueOf(73),BigInteger.valueOf(42),BigInteger.valueOf(5),new BigInteger("133700000000000001"),"c".repeat(64));
        var target=new NormalExitProtocol.Target(true,true,true,true,true,true,true,true,BigInteger.ONE);var empty=new NormalExitProtocol.Dispatch(false,false,false,false,false);
        var dispatch=action==NormalExitProtocol.Action.PREPARE_CONFIRMATION?List.of(new NormalExitProtocol.Dispatch(true,true,true,true,true),empty,empty):List.of(empty,empty,empty);
        boolean query=action==NormalExitProtocol.Action.QUERY_CONTEXT,disable=action==NormalExitProtocol.Action.DISABLE_EXIT_AUTOSAVE;
        var autosave=new NormalExitProtocol.Autosave(true,true,true,shouldSave,disable,disable,disable&&!shouldSave);
        var value=new NormalExitProtocol.Observation(binding,action,query?NormalExitProtocol.Status.CONTEXT_OBSERVED:disable?NormalExitProtocol.Status.AUTOSAVE_DISABLED:NormalExitProtocol.Status.CONFIRMATION_OBSERVED,
                BigInteger.ONE,new NormalExitProtocol.Proof(true,true,true,true,true,true,true),!query,modal,false,false,"b".repeat(64),"controlled protocol DATA only",List.of(target,target,target),dispatch,List.of(true,true,false),Optional.of(autosave));
        return NormalExitProtocol.decodeObservation(NormalExitProtocol.observationJson(value),binding,action);
    }
    private static NativeRequest request(ProposalLifecycle.ObservationIdentity before,ExactRef source,String id,NativeStepDiscriminator.NormalExit selector){
        var action=NormalExitProtocol.Action.parse(selector.wire());var binding=new NormalExitProtocol.Binding(before.frame().identity().nativeRevision(),before.frame().identity().player(),BigInteger.valueOf(42),BigInteger.valueOf(5),new BigInteger("133700000000000001"),source.sha256());
        var packet=new NormalExitProtocol.Request(id,action,binding,id,action==NormalExitProtocol.Action.QUERY_CONTEXT?Optional.empty():Optional.of("a".repeat(64)));
        var fields=(ObjectNode)StrictJson.parse(NormalExitProtocol.payload(packet));for(String key:List.of("type","protocol_version","request_id","step","expected_revision"))fields.remove(key);
        return new NativeRequest(selector.nativeStep(),Optional.of(selector.capability()),raw(fields));
    }
    private static RawJson raw(com.fasterxml.jackson.databind.JsonNode value){return new RawJson(StrictJson.canonical(value));}
}
