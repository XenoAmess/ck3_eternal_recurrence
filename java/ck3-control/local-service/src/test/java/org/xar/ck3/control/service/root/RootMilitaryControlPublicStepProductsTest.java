package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract.*;

import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.gui.*;
import org.xar.ck3.control.nativebridge.publicmethods.gui.*;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;

/** Actual software endpoint, native transport, registered read/preparation/observer, writer and filesystem archive.
 * These tests do not grant a Managed Game or a synthetic Root runtime installation.
 */
final class RootMilitaryControlPublicStepProductsTest {
    @TempDir Path root;
    @Test void reinforcementNativeProducerIndependentReadCanonicalControlAndWholePublicResultRoundTrip()throws Exception {
        for(Control control:List.of(Control.ENABLE_REINFORCEMENT,Control.DISABLE_REINFORCEMENT))run(control,false,false);
    }
    @Test void lostOriginalAckRemainsUnknownAndCannotBePresentedOrSentAgain()throws Exception {
        run(Control.ENABLE_REINFORCEMENT,true,false);
    }
    @Test void alreadyDesiredStillRequiresItsIndependentlyLaterActualTicket()throws Exception {
        run(Control.ENABLE_REINFORCEMENT,false,true);
    }
    private void run(Control control,boolean lost,boolean alreadyDesired)throws Exception {
        var contracts=new AtomicReference<GuiReads>();var actions=new AtomicReference<MilitaryControlActions>();
        var binding=new AtomicReference<Binding>();var before=new AtomicReference<BeforeObservation>();
        int initial=alreadyDesired?(control.desiredEnabled()?1:0):(control.desiredEnabled()?0:1);var state=new AtomicInteger(initial);var ticket=new AtomicInteger(200);
        var read=new ActionWriterIntegrationFixture.SoftwareReadScenario(GuiModels.Build.CROZIER4.sha256(),"military-original-software",source->{
            var actual=new GuiReads(new GuiReads.Sources(source,source,source,source,source,source,source));assertTrue(contracts.compareAndSet(null,actual));return actual.registered();
        },request->{var raw=MilitaryReceiverFixture.census(binding.get(),state.get(),ticket.incrementAndGet());
            before.compareAndSet(null,MilitaryReceiverProof.observeFixedReinforcement(raw,binding.get()));return raw;
        },Optional.of(GuiModels.Build.CROZIER4.version()),Set.of(control.capability()));
        var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(control.operation(),control.capability(),
                (command,attempt,dispatch)->actions.get().observe(command,attempt,dispatch),
                ()->state.set(control.desiredEnabled()?1:0),
                Optional.of(()->MilitaryReceiverFixture.acknowledgement(control,binding.get(),before.get())),Optional.empty(),true,
                Optional.of(command->actions.get().prepare(command)));
        try(var actual=new ActionWriterIntegrationFixture(root.resolve(control.name()+lost+alreadyDesired),lost,read,List.of(action))) {
            var prepared=actual.command("original-fixed-military-"+control.name());
            binding.set(new Binding(new GuiModels.Context(prepared.before(),prepared.source(),prepared.sessionId(),BigInteger.valueOf(5),GuiModels.Build.CROZIER4,prepared.deadline())));
            var producer=new MilitaryControlActions(contracts.get(),actual.reads,()->actual.archive.withSession(actual.writer.borrowedSession()),actual.frameLoader(),Clock.systemUTC());actions.set(producer);
            actual.bindAdditionalArchivedVerifier(new org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.Binding(control.operation(),actual.observationSource().sourceRef(),producer::replay));
            ActionCommand command=actual.writer.locked(same->producer.prepareCommand(control,binding.get(),prepared.actionId()));
            assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
            var nativeRequest=producer.prepare(command);assertEquals(control.operation().value(),nativeRequest.step());
            assertTrue(nativeRequest.preparationEvidence().size()==1);assertFalse(new String(nativeRequest.additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8).contains("_military_before_read"));
            ActionReceipt result=actual.coordinator.execute(command);assertEquals(1,actual.nativeActionWrites());
            actual.writer.locked(same->{
                var archive=actual.archive.withSession(same);var reference=archive.receiptReferenceOf(result);var cold=archive.loadReceipt(reference);assertEquals(result,cold);
                assertEquals(cold,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(cold,archive),archive));
                if(lost) {
                    assertInstanceOf(ActionState.Unknown.class,cold.state());RootMilitaryControlAssertions.requireUnresolvedBlocked(cold);assertThrows(RuntimeException.class,()->RootMilitaryControlStepRuntime.result(cold,archive,producer));
                } else {
                    assertInstanceOf(ActionState.ControlApplied.class,((ActionState.Settled)cold.state()).settlement());RootMilitaryControlAssertions.requireZeroBusiness(cold);
                    producer.replay(same.head(),cold,archive);
                    var full=RootMilitaryControlStepRuntime.result(cold,archive,producer);var body=node(full);
                    assertEquals(alreadyDesired?"verified_already_desired":"verified_desired",body.get("status").textValue());assertTrue(body.get("postcondition_verified").booleanValue());
                    assertEquals(control.operation().value(),body.get("native_ack").get("step").textValue());
                    assertTrue(body.get("before_observation").get("frame").get("native_revision").isTextual());
                    assertNotEquals(body.get("before_observation").get("frame").get("ticket_sequence"),body.get("later_observation").get("frame").get("ticket_sequence"));
                    var envelope=PublicMcpDirectory.CallResult.fromBusinessJson(full);var parsed=DriverJson.toNode(DriverJson.object(envelope.bytes(),RawJson.MAXIMUM_BYTES));
                    assertEquals(body,parsed.get("structuredContent"));assertFalse(body.has("outcome"),"a canonical receipt is not the Driver result");
                    assertEquals(full,raw(body));
                }
                return null;
            });
            var again=actual.coordinator.execute(command);assertEquals(result,again);assertEquals(1,actual.nativeActionWrites(),"same canonical command, including UNKNOWN, cannot dispatch again");
            var reopened=actual.reopenAndReturnExisting(command);assertEquals(result,reopened);assertEquals(1,actual.nativeActionWrites());
            if(lost)RootMilitaryControlAssertions.requireUnresolvedBlocked(reopened);else RootMilitaryControlAssertions.requireZeroBusiness(reopened);
            assertTrue(actual.scenarioReadWrites()>=1);
        }
    }
    @Test void exactSelectorsTypedRequestAndPublicDecimalCountersRejectAliasesAndPreserveLargeValues() {
        for(Control control:Control.values())assertEquals(Optional.of(control),Control.parse(control.operation()));
        for(String wrong:List.of("enable-military-reinforcement","enable-military-reinforcement-v1:extra","pause-map","activate-ingame-military-v1-x"))assertTrue(Control.parse(new OperationKey(wrong)).isEmpty());
        var wire=StrictJson.object().put("native_revision",new BigInteger("18446744073709551615"));wire.putObject("nested").put("ticket_sequence",new BigInteger("9007199254740993"));
        RootMilitaryControlStepRuntime.decimalCounters(wire);assertEquals("18446744073709551615",wire.get("native_revision").textValue());assertEquals("9007199254740993",wire.get("nested").get("ticket_sequence").textValue());
        assertEquals(wire,node(raw(wire)));
    }
}
