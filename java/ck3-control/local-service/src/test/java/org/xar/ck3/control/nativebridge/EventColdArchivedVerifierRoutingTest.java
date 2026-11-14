package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software coordinator/Root guard/writer/SDK/archive producer, then a cold
 * catalog passed to the actual generic recorded verifier. Rejected is deliberate:
 * this exercises the new exact EVENT gate, not an Applied EventWitness or actual
 * Root/Game/source authority. Commands are built BEFORE their first submission;
 * no receipt, Guard, ACK, history point or immutable body is modified afterwards.
 * Setup uses its existing software endpoint. Replay must add zero endpoint calls.
 */
final class EventColdArchivedVerifierRoutingTest {
    private static final OperationKey EVENT=new OperationKey("select-event-option-1");
    private static final OperationKey OTHER=new OperationKey("fixture-direct-history-rejection");
    private static final ExactRef FOREIGN=new ExactRef("software-foreign-family-definition",1,"d".repeat(64));
    @TempDir Path directory;

    @Test void coldExactEventFamilyMaterializesOnceAndTheMandatorySameWriterCallbackIsReached()throws Exception{
        try(var produced=produce(directory.resolve("positive"),EVENT,true)){
            var f=produced.fixture;var probe=new Probe();var definition=f.observationSource().sourceRef();
            var family=family("event",EVENT,probe,true,definition,definition,definition,definition);
            var catalog=catalog(List.of(family));assertTrue(catalog.actualArchivedVerifier(EVENT).isEmpty());assertEquals(0,probe.factories.get());
            f.writer.locked(same->{
                var head=same.head();int writes=f.nativeActionWrites(),reads=f.nativeReadWrites();
                probe.expectedHead=head;probe.expected=produced.receipt;
                var verifier=verifier(f,same,catalog);
                assertSame(probe.stop,assertThrows(IllegalStateException.class,()->verifier.verify(head,produced.receipt)));
                assertSame(probe.issuedReplay,catalog.actualArchivedVerifier(EVENT).orElseThrow());assertSame(family,catalog.actualFamily(EVENT).orElseThrow());
                assertEquals(1,probe.factories.get());assertEquals(1,probe.callbacks.get());
                assertSame(probe.stop,assertThrows(IllegalStateException.class,()->verifier.verify(head,produced.receipt)));
                assertEquals(1,probe.factories.get());assertEquals(2,probe.callbacks.get());
                assertEquals(0,probe.preparations.get());assertEquals(0,probe.projectors.get());
                assertEquals(writes,f.nativeActionWrites());assertEquals(reads,f.nativeReadWrites());assertEquals(head.digest(),same.head().digest());return null;
            });
            assertEquals(EVENT,produced.receipt.command().operation());assertEquals(NativeEventPostconditionPort.EVENT_SCHEMA,produced.receipt.command().expected().observerSchema());
            assertInstanceOf(ActionState.Rejected.class,((ActionState.Settled)produced.receipt.state()).settlement());
            assertTrue(produced.receipt.ack().orElseThrow().nativeOk());assertFalse(produced.receipt.eligibleAdvance());assertTrue(produced.receipt.applied().isEmpty());
            assertTrue(f.nativeActionWrites()>0);assertTrue(f.nativeReadWrites()>0); // software setup, never live Native.
        }
    }

    @Test void nonEventSchemaAndNonEventOperationNeverMaterializeAnOtherwiseMatchingFamily()throws Exception{
        for(boolean wrongSchema:List.of(true,false)){
            var operation=wrongSchema?EVENT:OTHER;
            try(var produced=produce(directory.resolve(wrongSchema?"wrong-schema":"wrong-operation"),operation,!wrongSchema)){
                var f=produced.fixture;var probe=new Probe();var source=f.observationSource().sourceRef();
                var catalog=catalog(List.of(family("gate",operation,probe,true,source,source,source,source)));
                f.writer.locked(same->{
                    var head=same.head();int reads=f.nativeReadWrites(),writes=f.nativeActionWrites();
                    var failure=assertThrows(IllegalArgumentException.class,()->verifier(f,same,catalog).verify(head,produced.receipt));
                    assertEquals("settlement has no installed original-evidence domain verifier",failure.getMessage());
                    assertTrue(catalog.actualArchivedVerifier(operation).isEmpty());assertEquals(0,probe.factories.get());assertEquals(0,probe.callbacks.get());
                    assertEquals(reads,f.nativeReadWrites());assertEquals(writes,f.nativeActionWrites());assertEquals(head.digest(),same.head().digest());return null;
                });
            }
        }
    }

    @Test void unsupportedAmbiguousAndForeignFixedFamilySourcesFailBeforeTheDomainCallback()throws Exception{
        try(var produced=produce(directory.resolve("family-negative"),EVENT,true)){
            var f=produced.fixture;var source=f.observationSource().sourceRef();
            for(int which=0;which<5;which++){
                var probe=new Probe();
                var first=family("first-"+which,EVENT,probe,which!=0,source,
                        which==2?FOREIGN:source,which==3?FOREIGN:source,which==4?FOREIGN:source);
                List<RootExecutableBindings.Family<?>> families=which==1?List.of(first,family("second",EVENT,probe,true,source,source,source,source)):List.of(first);
                var catalog=catalog(families);final int scenario=which;
                f.writer.locked(same->{
                    var head=same.head();int reads=f.nativeReadWrites(),writes=f.nativeActionWrites();
                    assertThrows(IllegalArgumentException.class,()->verifier(f,same,catalog).verify(head,produced.receipt));
                    assertEquals(scenario<2?0:1,probe.factories.get());assertEquals(0,probe.callbacks.get());
                    assertTrue(catalog.actualArchivedVerifier(EVENT).isEmpty());assertTrue(catalog.actionBindings().isEmpty());
                    assertEquals(0,probe.preparations.get());assertEquals(0,probe.projectors.get());
                    assertEquals(reads,f.nativeReadWrites());assertEquals(writes,f.nativeActionWrites());assertEquals(head.digest(),same.head().digest());return null;
                });
            }
        }
    }

    private static RootExecutableBindings catalog(List<RootExecutableBindings.Family<?>> families){
        return RootExecutableBindings.freeze(List.of(),RootReadContractCatalog.staticOnly(List.of()),List.of(),List.of(),families,16);
    }
    private static RootExecutableBindings.Family<Integer> family(String id,OperationKey operation,Probe probe,boolean supports,
            ExactRef fixed,ExactRef preparer,ExactRef decoder,ExactRef replaySource){
        return new RootExecutableBindings.Family<>(id,Integer.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of("game.command."+operation.value()),
                fixed,fixed,fixed,index->raw("{}"),index->operation,index->{
                    probe.factories.incrementAndGet();
                    var effect=new NativeEffectRegistry.Binding(operation,preparer,
                            command->{probe.preparations.incrementAndGet();throw new AssertionError("archived replay cannot prepare a new action");},
                            (command,attempt,dispatch)->{probe.projectors.incrementAndGet();throw new AssertionError("archived replay cannot project a new result");});
                    var replay=new NativeRecordedEvidenceVerifier.Binding(operation,replaySource,(head,receipt,archive)->{
                        probe.callbacks.incrementAndGet();assertSame(probe.expectedHead,head);assertSame(probe.expected,receipt);
                        assertEquals(receipt,archive.loadReceipt(archive.receiptReferenceOf(receipt)));
                        requireSoftwareRejection(receipt,archive);throw probe.stop;
                    });probe.issuedReplay=replay;
                    return new RootExecutableBindings.IssuedAction(new RootExecutableBindings.ActionBinding(effect,
                            ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of("game.command."+operation.value()),decoder),replay);
                },candidate->supports&&candidate.equals(operation)?Optional.of(1):Optional.empty());
    }
    private static NativeRecordedEvidenceVerifier verifier(ActionWriterIntegrationFixture f,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,RootExecutableBindings catalog){
        return new NativeRecordedEvidenceVerifier(f.archive,()->same,f.physicalInputs().originals(),f.frameLoader(),catalog);
    }
    private static Produced produce(Path path,OperationKey operation,boolean exactEventSchema)throws Exception{
        var held=new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,"game.command."+operation.value(),(command,attempt,dispatch)->{
            var f=held.get();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
            assertTrue(ack.nativeOk());assertEquals(new OpportunityJson.Bool(false),DriverJsonValue(ack.originalResultToken().orElseThrow()).get("accepted"));
            return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"explicit software producer rejection; no EventWitness",f.archive.referenceOf(dispatch)));
        },()->{},()->raw("{\"accepted\":false,\"software_event_routing_fixture\":true}"));
        var f=new ActionWriterIntegrationFixture(path,false,scenario);held.set(f);
        try{
            f.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(operation,f.observationSource().sourceRef(),
                    (head,receipt,archive)->requireSoftwareRejection(receipt,archive)));
            var ready=f.ready();var request=ready.request();
            // Explicit software expected-input only, constructed before submission.
            // The real producer makes a rejection and never claims the instance advanced.
            var expectedSnapshot=request.observations().snapshot().with("active_event",DriverJsonValue(raw("{\"instance_id\":1}")));
            var plan=new OpportunityJson.Obj(Map.of());
            var eventExpected=NativeEventPostconditionPort.expected(request.before(),request.source(),expectedSnapshot,EVENT,plan,Optional.empty()).orElseThrow();
            var expected=exactEventSchema?eventExpected:new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),"paused/v1",
                    List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("paused"),true)));
            var command=new ActionCommand("software-event-cold-route-"+(exactEventSchema?"event":"other"),request.before(),request.source(),f.observationIdentity().sessionId(),operation,plan,expected,
                    new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.now().plusSeconds(25));
            var receipt=f.coordinator.execute(command);assertEquals(command,receipt.command());assertTrue(receipt.settled());
            assertInstanceOf(ActionState.Rejected.class,((ActionState.Settled)receipt.state()).settlement());return new Produced(f,receipt);
        }catch(Exception|Error failed){try{f.close();}catch(IOException close){failed.addSuppressed(close);}throw failed;}
    }
    private static OpportunityJson.Obj DriverJsonValue(RawJson value){return org.xar.ck3.control.application.driver.DriverJson.object(value.bytes(),RawJson.MAXIMUM_BYTES);}
    private static RawJson raw(String value){return new RawJson(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static void requireSoftwareRejection(ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
        var state=assertInstanceOf(ActionState.Settled.class,receipt.state());var rejected=assertInstanceOf(ActionState.Rejected.class,state.settlement());
        var ack=assertInstanceOf(NativeActionPort.AckReceived.class,state.dispatch());assertEquals(state.attempt().requestId(),ack.requestId());assertEquals(ack.requestId(),rejected.requestId());
        assertEquals(ack,archive.load(rejected.originalEvidence()));assertEquals(archive.referenceOf(ack),rejected.originalEvidence());
        assertEquals(new OpportunityJson.Bool(false),DriverJsonValue(ack.originalResultToken().orElseThrow()).get("accepted"));
        ack.custody().orElseThrow().verify(ack,state.attempt().guard());
    }
    private static final class Produced implements AutoCloseable {
        final ActionWriterIntegrationFixture fixture;final ActionReceipt receipt;
        Produced(ActionWriterIntegrationFixture fixture,ActionReceipt receipt){this.fixture=fixture;this.receipt=receipt;}
        @Override public void close()throws IOException{fixture.close();}
    }
    private static final class Probe {
        final AtomicInteger factories=new AtomicInteger(),callbacks=new AtomicInteger(),preparations=new AtomicInteger(),projectors=new AtomicInteger();
        final IllegalStateException stop=new IllegalStateException("mandatory software domain callback reached; no EventWitness or actual Root authority");
        WriterContracts.Head expectedHead;ActionReceipt expected;NativeRecordedEvidenceVerifier.Binding issuedReplay;
    }
}
