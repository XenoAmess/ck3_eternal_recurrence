package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.gui.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;

/** Actual existing software transport -> sole writer -> archive -> source replay -> public consumer.
 * Software DTOs qualify no loaded native module, CK3 build, or live business capability. */
final class GuiWhiteWriterOriginalsTest {
    @TempDir Path root;
    private static RawJson raw(ObjectNode value){return PublicDataJson.encodeFullMaterial(value);}
    private enum After { CHANGED, NO_EFFECT, STALE_TEXT, OTHER_BUSINESS, OTHER_TEXT, GOLD_CHANGED }
    private static final class Run implements AutoCloseable {
        final ActionWriterIntegrationFixture fixture;
        final GuiReads contracts;
        final GuiActions actions;
        final GuiService.NavigationPorts ports;
        final GuiService service;
        final GuiService.Invocation invocation;
        final OpportunityJson.Obj snapshot;
        final RawJson beforeSource;
        final Request request;
        final AtomicInteger dispatches=new AtomicInteger();
        final AtomicReference<GuiModels.Context> context=new AtomicReference<>();
        final boolean numeric;
        final GuiModels.NumericControl selected;
        final After after;
        Run(Path directory, boolean numeric,GuiModels.NumericControl selected,After after,boolean loseAck)throws Exception {
            this.numeric=numeric;this.selected=selected;this.after=after;
            var readOwner=new AtomicReference<GuiReads>();var actionOwner=new AtomicReference<GuiActions>();
            String step=numeric?"click-white-numeric-control-v1":"click-white-control-v1";
            var readScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(GuiModels.Build.CROZIER3.sha256(),
                    "ck3-1.20.0.3-msvc-x64",source->{
                        var reads=new GuiReads(new GuiReads.Sources(source,source,source,source,source,source,source));
                        assertTrue(readOwner.compareAndSet(null,reads));return reads.registered();
                    },nativeRequest->{
                        assertNotNull(context.get());boolean later=dispatches.get()>0;
                        assertTrue(Set.of("query-white-player-business-variables-v1","query-white-rendered-text-v1").contains(nativeRequest.step()));
                        return raw(nativeRequest.step().equals("query-white-player-business-variables-v1")?business(later):text(later));
                    },Optional.of(GuiModels.Build.CROZIER3.version()),Set.of());
            var actionScenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey(step),"game.command."+step,
                    (command,attempt,outcome)->actionOwner.get().observe(command,attempt,outcome),
                    ()->assertEquals(1,dispatches.incrementAndGet(),"one actual native callback per intent"),
                    Optional.of(()->raw(ack())),Optional.empty(),false,
                    Optional.of(command->actionOwner.get().prepare(command)));
            fixture=new ActionWriterIntegrationFixture(directory,loseAck,readScenario,List.of(actionScenario));
            contracts=readOwner.get();
            actions=new GuiActions(fixture.reads,contracts,()->fixture.archive.withSession(fixture.writer.borrowedSession()));
            assertTrue(actionOwner.compareAndSet(null,actions));
            ports=new GuiService.NavigationPorts(actions,contracts,fixture.reads,List.of());
            fixture.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(new OperationKey(step),contracts.semantic.sourceRef(),ports::replay));
            var actual=fixture.ready().request();snapshot=actual.observations().snapshot();
            var c=new GuiModels.Context(actual.before(),actual.source(),actual.sessionId(),BigInteger.valueOf(5),GuiModels.Build.CROZIER3,actual.deadline());context.set(c);
            invocation=new GuiService.Invocation(c,c.before().frame().revision(),true,true);
            var original=PublicDataJson.encodeFullMaterial(snapshot);
            beforeSource=GuiPublicMetadata.beforeSource(original,PublicDataJson.encodeFullMaterial(OpportunityJson.object(snapshot.get("diagnostics"),"actual diagnostics")));
            var capture=GuiService.captureCapable(fixture.coordinator);
            service=new GuiService(new GuiCapabilities(capture,fixture.reads,contracts),contracts,fixture.reads,capture,
                    ()->fixture.archive.withSession(fixture.writer.borrowedSession()),Optional.empty(),Optional.empty(),Optional.empty());
            ObjectNode args=StrictJson.object().put("expected_revision",invocation.publicRevision()).put("intent_id","one-original-white-intent");
            if(numeric)args.put("control",selected.wire()).put("expected_before_value",6).put("expected_before_price_text","arbitrary-before-price");
            else args.put("control","age_plus_1").put("expected_before_age",30);
            request=GuiCodec.decode((numeric?Method.WHITE_NUMERIC:Method.WHITE_AGE).originalName(),args);
        }
        ActionReply execute()throws Exception{return fixture.writer.locked(same->{
            var actual=(ActionReply)service.invoke(request,invocation);
            return new ActionReply(actual.receipt(),actual.archivedReceipt(),actual.originalReference(),Optional.of(beforeSource),actual.parsedReturnReference());
        });}
        ObjectNode present(ActionReply reply)throws Exception{return fixture.writer.locked(same->{
            var archive=fixture.archive.withSession(same);
            var originals=RootGuiPublicProducts.whiteEvidence(request,reply.receipt(),contracts,archive);
            return PublicDataJson.object(GuiPublicBinder.action(request,reply,new GuiPublicBinder.Before(context.get(),beforeSource),Optional.empty(),Optional.empty(),originals));
        });}
        private ObjectNode binding(){var c=context.get();return StrictJson.object().put("game_pid",c.before().game().pid())
                .put("native_revision",c.before().frame().identity().nativeRevision()).put("connection_generation",c.connectionGeneration())
                .put("played_character_id",c.before().frame().identity().player()).put("date_raw",c.before().frame().identity().dateRaw());}
        ObjectNode business(boolean later){
            var r=binding().put("schema","ck3-native-white-player-business-variables-v1").put("step","query-white-player-business-variables-v1")
                    .put("backend_id","native-headless").put("available",true).put("all_eight_numeric_integers",true).put("fixed_scale",100000)
                    .put("status","observed_business_variables").put("unavailable_reason","").put("application_thread_id",71)
                    .put("application_pump_epoch",new BigInteger("18446744073709551615"))
                    .put("application_tls_context",new BigInteger("9007199254740993")).put("variable_context",4096).put("character_address",8192);
            for(String key:List.of("owner_thread_verified","frame_verified","source_abi_pins_verified","player_scope_verified","stable_two_pass_values"))r.put(key,true);
            for(String key:List.of("rendered_text_available","selected_down_available","scriptvalue_price_available"))r.put(key,false);
            var values=r.putObject("fields");
            GuiModels.Variable target=numeric?GuiModels.Variable.valueOf(selected.name()):GuiModels.Variable.AGE;
            for(var key:GuiModels.Variable.values()){
                int value=key==GuiModels.Variable.FEMALE?0:key==GuiModels.Variable.AGE?30:6;
                if(later&&after!=After.NO_EFFECT&&key==target)value++;
                if(later&&after==After.OTHER_BUSINESS&&key==(target==GuiModels.Variable.MARTIAL?GuiModels.Variable.INTRIGUE:GuiModels.Variable.MARTIAL))value++;
                values.putObject(key.wire()).put("present",true).put("actual_kind",1).put("actual_payload",value*100000L)
                        .put("fixed_raw",value*100000L).put("integer_value",value);
            }
            return r;
        }
        ObjectNode text(boolean later){
            var r=binding().put("schema","ck3-native-white-rendered-text-v1").put("step","query-white-rendered-text-v1")
                    .put("backend_id","native-headless").put("read_only",true).put("available",true).put("rendered_text_available",true)
                    .put("selected_down_available",false).put("widget_count",42).put("text_source","actual_CPdxGuiTextbox_GetText_390").put("unavailable_reason","");
            for(String key:List.of("owner_thread_verified","source_abi_pins_verified","frame_verified","gui_owner_binding_verified","tree_complete","inner_modal_visible","stable_two_pass_text"))r.put(key,true);
            var values=r.putObject("fields");int i=0;GuiModels.TextName target=numeric?GuiModels.TextName.valueOf(selected.name()):GuiModels.TextName.AGE;
            for(var key:GuiModels.TextName.values()){
                String value=key==GuiModels.TextName.AGE?"30":key==GuiModels.TextName.PRICE?(later?"arbitrary-after-price":"arbitrary-before-price"):key==GuiModels.TextName.GOLD?"observed-gold":"6";
                if(later&&after!=After.NO_EFFECT&&after!=After.STALE_TEXT&&key==target)value=key==GuiModels.TextName.AGE?"31":"7";
                if(later&&after==After.OTHER_TEXT&&key==(target==GuiModels.TextName.MARTIAL?GuiModels.TextName.INTRIGUE:GuiModels.TextName.MARTIAL))value="changed unrelated native text";
                if(later&&after==After.GOLD_CHANGED&&key==GuiModels.TextName.GOLD)value="changed gold";
                values.putObject(key.wire()).put("child_path","0/"+(++i)).put("text_utf8",value).put("effective_visible",true).put("enabled",true);
            }
            return r;
        }
        ObjectNode ack(){
            var r=binding().put("schema","ck3-native-white-control-action-v1").put("step",numeric?"click-white-numeric-control-v1":"click-white-control-v1")
                    .put("backend_id","native-headless").put("control",numeric?selected.wire():"age_plus_1").put("available",true)
                    .put("read_only",false).put("selected_down_available",false).put("postcondition_verified",false)
                    .put("native_handled",false).put("unavailable_reason","").put("target_child_path","0/1/3/3/1/5");
            for(String key:List.of("source_abi_pins_verified","receiver_qualified","gui_owner_binding_verified","frame_verified","dispatch_attempted","dispatch_invoked","native_after_read"))r.put(key,true);
            if(numeric)r.put("expected_before_value",6).put("before_price_bound",true);else r.put("expected_before_age",30);
            return r;
        }
        ObjectNode oracleInput(String mode){var input=StrictJson.object().put("mode",mode).put("numeric",numeric)
                .put("control",numeric?selected.wire():"age_plus_1").put("intent","one-original-white-intent");
            input.set("snapshot",OpportunityJson.toNode(snapshot));input.set("before_business",business(false));input.set("after_business",business(true));
            input.set("before_text",text(false));input.set("after_text",text(true));input.set("ack",ack());return input;}
        @Override public void close()throws Exception{fixture.close();}
    }

    @Test void actualAgeAndAllSixNumericCallbacksRetainTwoBeforeTwoAfterAndColdWriterReplay()throws Exception{
        for(int index=-1;index<GuiModels.NumericControl.values().length;index++){
            boolean numeric=index>=0;var selected=numeric?GuiModels.NumericControl.values()[index]:GuiModels.NumericControl.DIPLOMACY;
            try(var run=new Run(root.resolve("writer-"+index),numeric,selected,After.CHANGED,false)){
                ActionReply reply=run.execute();assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,reply.receipt().outcome());
                assertEquals(1,run.dispatches.get());assertEquals(1,run.fixture.nativeActionWrites());assertEquals(4,run.fixture.scenarioReadWrites(),"preparation must reopen the same two before READs");
                run.fixture.writer.locked(same->{
                    var archive=run.fixture.archive.withSession(same);var receipt=reply.receipt();
                    var settled=assertInstanceOf(ActionState.Settled.class,receipt.state());var control=assertInstanceOf(ActionState.ControlApplied.class,settled.settlement());
                    assertEquals(1,control.supportingReads().size());
                    var before=GuiWhiteOriginals.before(receipt.command(),run.contracts,archive);
                    assertEquals(List.of(archive.readReferenceOf(before.business()),archive.readReferenceOf(before.text())),settled.attempt().preparedRequest().preparationEvidence());
                    assertEquals(settled.attempt().preparedRequest(),run.actions.prepare(ActionCodec.decodeCommand(ActionCodec.encodeCommand(receipt.command()))));
                    assertFalse(new String(settled.attempt().preparedRequest().additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8).contains("_gui_before"));
                    byte[] encoded=ActionReceiptCodec.encodeReceipt(receipt,archive);var reopened=ActionReceiptCodec.decodeReceipt(encoded,archive);
                    assertEquals(receipt,reopened);assertArrayEquals(encoded,ActionReceiptCodec.encodeReceipt(reopened,archive));
                    run.ports.replay(same.head(),reopened,archive);
                    GuiWhiteOriginals.requireBeforeSubmission(before,settled.attempt(),receipt.ack().orElseThrow());
                    assertThrows(IllegalArgumentException.class,()->GuiWhiteOriginals.requireBeforeSubmission(new GuiWhiteOriginals.Before(control.read(),control.supportingReads().getFirst()),settled.attempt(),receipt.ack().orElseThrow()));
                    int beforeReads=run.fixture.scenarioReadWrites();
                    var actualHistory=ContinuityActionJournal.receipts(same.head().state(),archive);
                    assertThrows(IllegalArgumentException.class,()->RootGuiPublicProducts.requireWhiteIntentUnclaimed(run.request,run.context.get(),actualHistory));
                    var changed=GuiCodec.encodeRequest(run.request);
                    changed.put(numeric?"expected_before_value":"expected_before_age",numeric?7:31);
                    var changedRequest=GuiCodec.decode(run.request.method().originalName(),changed);
                    assertThrows(IllegalArgumentException.class,()->RootGuiPublicProducts.requireWhiteIntentUnclaimed(changedRequest,run.context.get(),actualHistory));
                    assertEquals(beforeReads,run.fixture.scenarioReadWrites(),"claimed intent is rejected before a second before query");
                    return null;
                });
                var actual=run.present(reply);assertTrue(actual.path("postcondition_verified").booleanValue());assertTrue(actual.path("independent_business_after_verified").booleanValue());
                assertTrue(actual.path("independent_rendered_text_after_verified").booleanValue());assertFalse(actual.path("full_gui_acceptance_credit").booleanValue());
                assertEquals("18446744073709551615",actual.path("later_actual_business").path("application_pump_epoch").textValue());
                assertEquals("9007199254740993",actual.path("before_business").path("application_tls_context").textValue());
                if(numeric){assertEquals("arbitrary-before-price",actual.path("actual_price_before").textValue());assertEquals("arbitrary-after-price",actual.path("actual_price_after").textValue());assertFalse(actual.path("price_formula_verified").booleanValue());}
                var oracle=GuiEightOriginalOracle.invoke(root.resolve("original-"+index),run.oracleInput("white_action"));
                assertEquals(1,oracle.path("dispatches").intValue());assertEquals(4,oracle.path("reads").intValue());
                ObjectNode expected=(ObjectNode)oracle.get("public");
                expected.remove("action_claim_path"); // Original Python local claim is replaced by the actual canonical receipt reference.
                ObjectNode projected=PublicDataJson.object(GuiCodec.encodePublicOriginal(raw(expected)));
                projected.fields().forEachRemaining(field->assertEquals(field.getValue(),actual.get(field.getKey()),field.getKey()));
                assertFalse(actual.has("action_claim_path"));assertFalse(actual.path("legacy_claim_path_available").booleanValue());
                assertTrue(actual.path("canonical_gui_action").path("ack_received").booleanValue());
            }
        }
    }
    @Test void actualBusinessAndTextReadWrappersMatchOriginalProducerAndNeverAppendActions()throws Exception{
        try(var run=new Run(root.resolve("read-only"),true,GuiModels.NumericControl.MARTIAL,After.CHANGED,false)){
            for(Method method:List.of(Method.WHITE_BUSINESS,Method.WHITE_TEXT)){
                byte[] ledger=run.fixture.ledgerBytes();ObjectNode args=StrictJson.object().put("expected_revision",run.invocation.publicRevision());
                Request request=GuiCodec.decode(method.originalName(),args);
                var actual=run.fixture.writer.locked(same->{var original=(ReadReply)run.service.invoke(request,run.invocation);
                    var reply=new ReadReply(original.receipt(),original.originalReference(),Optional.of(run.beforeSource),original.parsedReturnReference());
                    return PublicDataJson.object(GuiPublicBinder.read(request,reply,Optional.of(new GuiPublicBinder.Before(run.context.get(),run.beforeSource))));});
                var input=run.oracleInput("white_read").put("business",method==Method.WHITE_BUSINESS);
                var expected=GuiEightOriginalOracle.invoke(root.resolve(method.name()),input).get("public");
                assertEquals(PublicDataJson.object(GuiCodec.encodePublicOriginal(raw((ObjectNode)expected))),actual);
                assertArrayEquals(ledger,run.fixture.ledgerBytes());assertEquals(0,run.fixture.nativeActionWrites());
            }
        }
    }
    @Test void ackWithoutChangedBusinessOrTextStaysUnknownAndReconcileNeverRedispatches()throws Exception{
        for(After after:List.of(After.NO_EFFECT,After.STALE_TEXT,After.OTHER_BUSINESS,After.OTHER_TEXT,After.GOLD_CHANGED)){
            try(var run=new Run(root.resolve("unknown-"+after),true,GuiModels.NumericControl.MARTIAL,after,false)){
                var reply=run.execute();assertEquals(ActionReceipt.Outcome.UNRESOLVED,reply.receipt().outcome());
                assertInstanceOf(ActionState.Unknown.class,reply.receipt().state());assertEquals(1,run.dispatches.get());
                var out=run.present(reply);assertFalse(out.path("postcondition_verified").asBoolean());assertFalse(out.has("later_actual_business"));
                run.fixture.writer.locked(same->{var collected=run.fixture.coordinator.reconcile(reply.receipt().command().actionId());assertEquals(ActionReceipt.Outcome.UNRESOLVED,collected.outcome());return null;});
                assertEquals(1,run.dispatches.get());assertEquals(1,run.fixture.nativeActionWrites());
            }
        }
    }
    @Test void lostOriginalAckStaysUnknownWithoutAfterCreditOrSecondCallback()throws Exception{
        try(var run=new Run(root.resolve("lost-ack"),false,GuiModels.NumericControl.DIPLOMACY,After.CHANGED,true)){
            var reply=run.execute();assertEquals(ActionReceipt.Outcome.UNRESOLVED,reply.receipt().outcome());assertEquals(1,run.dispatches.get());
            assertEquals(2,run.fixture.scenarioReadWrites(),"no ACK cannot start independent after checks");
            assertFalse(run.present(reply).has("later_actual_business"));
            run.fixture.writer.locked(same->{run.fixture.coordinator.reconcile(reply.receipt().command().actionId());return null;});
            assertEquals(1,run.dispatches.get());assertEquals(1,run.fixture.nativeActionWrites());
        }
    }
    @Test void archivedSupportingTextMissingDamagedSwappedOrDuplicatedIsRejected()throws Exception{
        try(var run=new Run(root.resolve("archive-roles"),true,GuiModels.NumericControl.MARTIAL,After.CHANGED,false)){
            var reply=run.execute();run.fixture.writer.locked(same->{
                var archive=run.fixture.archive.withSession(same);var receipt=reply.receipt();var settled=(ActionState.Settled)receipt.state();var control=(ActionState.ControlApplied)settled.settlement();
                for(var wrong:List.of(new ActionState.ControlApplied(control.read(),List.of(),control.observerSchema(),control.actual()),
                        new ActionState.ControlApplied(control.supportingReads().getFirst(),List.of(control.read()),control.observerSchema(),control.actual()),
                        new ActionState.ControlApplied(control.read(),List.of(control.read()),control.observerSchema(),control.actual()))){
                    var forged=new ActionReceipt(receipt.version(),receipt.sequence(),receipt.command(),receipt.bodySha256(),new ActionState.Settled(settled.attempt(),settled.dispatch(),wrong));
                    assertThrows(IllegalArgumentException.class,()->run.ports.replay(same.head(),forged,archive));
                    assertThrows(IllegalArgumentException.class,()->RootGuiPublicProducts.whiteEvidence(run.request,forged,run.contracts,archive));
                }
                assertEquals(1,run.fixture.nativeActionWrites());return null;
            });
        }
        for(boolean missing:List.of(true,false))try(var run=new Run(root.resolve("archive-file-"+missing),true,GuiModels.NumericControl.MARTIAL,After.CHANGED,false)){
            var reply=run.execute();run.fixture.writer.locked(same->{
                var archive=run.fixture.archive.withSession(same);var control=(ActionState.ControlApplied)((ActionState.Settled)reply.receipt().state()).settlement();
                byte[] encoded=ActionReceiptCodec.encodeReceipt(reply.receipt(),archive);
                Path path=Path.of(archive.readReferenceOf(control.supportingReads().getFirst()).path());
                assertTrue(path.toAbsolutePath().normalize().startsWith(run.fixture.root.toAbsolutePath().normalize()));
                if(missing){Path moved=path.resolveSibling(path.getFileName()+".test-held-original");Files.move(path,moved);
                    try{assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(encoded,archive));}
                    finally{Files.move(moved,path);}
                }else{Files.writeString(path,"{}");assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(encoded,archive));}
                // This intentionally damaged test archive is never requalified or used for another commit.
                return null;
            });
        }
    }
    @Test void missingArchivedBeforeFailsPreparationWithoutAnySetterWrite()throws Exception{
        try(var run=new Run(root.resolve("before-missing"),true,GuiModels.NumericControl.MARTIAL,After.CHANGED,false)){
            run.fixture.writer.locked(same->{
                ActionCommand command=run.service.prepareAction(run.request,run.invocation);
                var prepared=run.actions.prepare(command);assertEquals(2,prepared.preparationEvidence().size());
                assertEquals(2,run.fixture.scenarioReadWrites());
                Path path=Path.of(prepared.preparationEvidence().getLast().path());
                assertTrue(path.toAbsolutePath().normalize().startsWith(run.fixture.root.toAbsolutePath().normalize()));
                Path moved=path.resolveSibling(path.getFileName()+".test-held-original");Files.move(path,moved);
                try{assertThrows(RuntimeException.class,()->run.fixture.coordinator.execute(command));}
                finally{Files.move(moved,path);}
                assertEquals(0,run.fixture.nativeActionWrites());return null;
            });
        }
    }
    @Test void unavailableMissingNullBooleanAndWidthWhiteDataPreserveTheirOriginalDomains()throws Exception{
        try(var run=new Run(root.resolve("strict-dto"),false,GuiModels.NumericControl.DIPLOMACY,After.CHANGED,false)){
            for(String role:List.of("native_revision","connection_generation","application_pump_epoch","application_tls_context","variable_context","character_address")){
                var bad=run.business(false);bad.put(role,true);assertThrows(IllegalArgumentException.class,()->GuiDecoders.whiteBusiness(bad,run.context.get()));
            }
            var negative=run.business(false);((ObjectNode)negative.path("fields").get("ervc_cc_female")).put("actual_payload",-150001).put("fixed_raw",-150001).putNull("integer_value");negative.put("all_eight_numeric_integers",false);
            assertFalse(GuiDecoders.whiteBusiness(negative,run.context.get()).allIntegers());
            for(String field:List.of("fields","stable_two_pass_text","widget_count")){var bad=run.text(false);bad.remove(field);assertThrows(IllegalArgumentException.class,()->GuiDecoders.whiteText(bad,run.context.get()));}
            var bad=run.text(false);((ObjectNode)bad.path("fields").get("ervc_cc_age_value_text")).putNull("text_utf8");assertThrows(IllegalArgumentException.class,()->GuiDecoders.whiteText(bad,run.context.get()));
            assertEquals(0,run.fixture.nativeActionWrites());
        }
    }
}
