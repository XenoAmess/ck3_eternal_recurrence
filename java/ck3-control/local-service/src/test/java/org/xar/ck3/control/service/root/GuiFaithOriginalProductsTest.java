package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.*;
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

/** Original .4 Python producer and actual framed READ/ACTION consumers; never a live .3/.4/.6 grant. */
final class GuiFaithOriginalProductsTest {
    @TempDir Path root;
    private static RawJson raw(ObjectNode value){return PublicDataJson.encodeFullMaterial(value);}
    private static final class Run implements AutoCloseable {
        final ActionWriterIntegrationFixture fixture;final GuiReads contracts;final GuiActions actions;
        final GuiService service;final GuiService.Invocation invocation;final OpportunityJson.Obj snapshot;
        final GuiPublicBinder.Before before;final AtomicReference<ObjectNode> readPacket=new AtomicReference<>(),actionPacket=new AtomicReference<>();
        Run(Path path)throws Exception{
            var owner=new AtomicReference<GuiReads>();var actionOwner=new AtomicReference<GuiActions>();
            var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(GuiModels.Build.CROZIER4.sha256(),"ck3-1.20.0.4-msvc-x64",source->{
                var actual=new GuiReads(new GuiReads.Sources(source,source,source,source,source,source,source));assertTrue(owner.compareAndSet(null,actual));return actual.registered();
            },request->{assertEquals("query-ingame-ui-window-v1",request.step());return raw(Objects.requireNonNull(readPacket.get(),"actual original query producer unbound"));},Optional.of(GuiModels.Build.CROZIER4.version()),Set.of());
            var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("navigate-ingame-ui-v1"),"game.command.navigate-ingame-ui-v1",
                (command,attempt,dispatch)->actionOwner.get().observe(command,attempt,dispatch),()->{},
                Optional.of(()->raw(Objects.requireNonNull(actionPacket.get()))),Optional.empty(),false,Optional.of(command->actionOwner.get().prepare(command)));
            fixture=new ActionWriterIntegrationFixture(path,false,scenario,List.of(action));contracts=owner.get();
            actions=new GuiActions(fixture.reads,contracts,()->fixture.archive.withSession(fixture.writer.borrowedSession()));actionOwner.set(actions);
            var ports=new GuiService.NavigationPorts(actions,contracts,fixture.reads,List.of());
            fixture.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(new OperationKey("navigate-ingame-ui-v1"),contracts.semantic.sourceRef(),ports::replay));
            var actual=fixture.ready().request();snapshot=actual.observations().snapshot();
            var context=new GuiModels.Context(actual.before(),actual.source(),actual.sessionId(),BigInteger.valueOf(5),GuiModels.Build.CROZIER4,actual.deadline());
            invocation=new GuiService.Invocation(context,context.before().frame().revision(),true,true);
            before=new GuiPublicBinder.Before(context,GuiPublicMetadata.beforeSource(PublicDataJson.encodeFullMaterial(snapshot),
                PublicDataJson.encodeFullMaterial(OpportunityJson.object(snapshot.get("diagnostics"),"actual Driver diagnostics"))));
            var capture=GuiService.captureCapable(fixture.coordinator);service=new GuiService(new GuiCapabilities(capture,fixture.reads,contracts),contracts,fixture.reads,capture,
                ()->fixture.archive.withSession(fixture.writer.borrowedSession()),Optional.empty(),Optional.empty(),Optional.empty());
        }
        ObjectNode original(Path directory,String operation,String kind,BigInteger subject,ObjectNode options,boolean absent,boolean badCache)throws Exception{
            var data=StrictJson.object().put("mode","faith").put("operation",operation).put("kind",kind).put("subject",subject).put("absent",absent).put("bad_cache",badCache);
            data.set("snapshot",OpportunityJson.toNode(snapshot));data.set("options",options);return GuiEightOriginalOracle.invoke(directory,data);
        }
        ReadReply read(Request request)throws Exception{return fixture.writer.locked(same->{
            var actual=(ReadReply)service.invoke(request,invocation);
            return new ReadReply(actual.receipt(),actual.originalReference(),Optional.of(before.source()),actual.parsedReturnReference());
        });}
        @Override public void close()throws Exception{fixture.close();}
    }
    @Test void presentQueryAndBothOriginalAliasesUseActualReadonlyContractAndCompleteOriginalPublicWrapper()throws Exception{
        try(var run=new Run(root.resolve("three-original-reads"))){
            for(Method method:List.of(Method.PRESENT,Method.QUERY_PRESENT,Method.QUERY_PRESENT_TOOLTIP)){
                ObjectNode args=StrictJson.object().put("window_kind","faith").put("expected_revision",run.invocation.publicRevision());
                ObjectNode options=StrictJson.object().put("presentation_tab","");BigInteger subject=BigInteger.ZERO;
                if(method==Method.PRESENT)args.put("operation","query").put("subject_id",0);
                if(method==Method.QUERY_PRESENT_TOOLTIP){
                    options.remove("presentation_tab");subject=new BigInteger("4294967294");args.put("subject_id",subject).put("presentation_target","faith_core_tenet")
                        .put("presentation_index",0).put("presentation_receipt","0123456789abcdef0123456789abcdef");
                    options.put("presentation_target","faith_core_tenet").put("presentation_index",0).put("presentation_receipt","0123456789abcdef0123456789abcdef");
                }
                var original=run.original(root.resolve(method.name()),"query","faith",subject,options,false,false);
                assertTrue(original.path("accepted").booleanValue());run.readPacket.set((ObjectNode)original.get("native"));
                Request request=GuiCodec.decode(method.originalName(),args);assertFalse(request.submitsAction());
                assertEquals(request,GuiCodec.decode(method.originalName(),GuiCodec.encodeRequest(request)));
                byte[] ledger=run.fixture.ledgerBytes();int reads=run.fixture.scenarioReadWrites();
                var reply=run.read(request);run.fixture.writer.locked(same->{NativeRecordedEvidenceVerifier.requireRead(reply.receipt(),run.fixture.archive.withSession(same));return null;});
                var body=PublicDataJson.object(GuiPublicBinder.read(request,reply,Optional.of(run.before)));
                assertEquals(PublicDataJson.object(GuiCodec.encodePublicOriginal(raw((ObjectNode)original.get("public")))),body);
                assertEquals(reads+1,run.fixture.scenarioReadWrites());assertEquals(0,run.fixture.nativeActionWrites());assertArrayEquals(ledger,run.fixture.ledgerBytes());
                assertTrue(body.has("queried_snapshot_id"));assertEquals("5",body.path("queried_connection_generation").textValue());
                assertEquals(run.invocation.nativeContext().before().frame().episodeRunId(),body.path("episode_run_id").textValue());
                assertEquals(method==Method.QUERY_PRESENT_TOOLTIP,body.path("verification_pending").booleanValue());
                assertThrows(IllegalArgumentException.class,()->run.fixture.writer.locked(same->run.service.prepareAction(request,run.invocation)));
            }
        }
    }
    @Test void originalOpenFaithAckFlagsSurviveActualIndependentReadAndCanonicalSettlement()throws Exception{
        try(var run=new Run(root.resolve("open-faith"))){
            var original=run.original(root.resolve("original-open"),"open_faith","faith",BigInteger.ZERO,StrictJson.object(),false,false);
            assertTrue(original.path("accepted").booleanValue());run.actionPacket.set((ObjectNode)original.get("native"));
            var read=run.original(root.resolve("original-later"),"query","faith",BigInteger.ZERO,StrictJson.object().put("presentation_tab",""),false,false);
            ObjectNode nativeRead=(ObjectNode)read.get("native");nativeRead.remove("presentation_ui");
            nativeRead.put("pump_epoch",run.actionPacket.get().get("pump_epoch").bigIntegerValue().add(BigInteger.ONE));run.readPacket.set(nativeRead);
            Request request=GuiCodec.decode(Method.OPEN_FAITH.originalName(),StrictJson.object().put("faith_id",0).put("expected_revision",run.invocation.publicRevision()));
            var reply=run.fixture.writer.locked(same->{var actual=(ActionReply)run.service.invoke(request,run.invocation);
                return new ActionReply(actual.receipt(),actual.archivedReceipt(),actual.originalReference(),Optional.of(run.before.source()),actual.parsedReturnReference());});
            assertEquals(1,run.fixture.nativeActionWrites());assertEquals(1,run.fixture.scenarioReadWrites());
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,reply.receipt().outcome());
            var body=PublicDataJson.object(GuiPublicBinder.action(request,reply,run.before,Optional.empty(),Optional.empty(),Optional.empty()));
            ObjectNode expected=PublicDataJson.object(GuiCodec.encodePublicOriginal(raw((ObjectNode)original.get("public"))));
            expected.fields().forEachRemaining(field->assertEquals(field.getValue(),body.get(field.getKey()),field.getKey()));
            assertTrue(body.path("verification_pending").booleanValue());assertEquals("acknowledged_verification_pending",body.path("status").textValue());
            assertEquals("applied_confirmed",body.path("canonical_gui_action").path("outcome").textValue());
        }
    }
    @Test void originalAbsentWindowAndMalformedTooltipCacheDoNotInventVisibilityOrCredit()throws Exception{
        try(var run=new Run(root.resolve("presentation-boundaries"))){
            var options=StrictJson.object().put("presentation_tab","");
            var absent=run.original(root.resolve("original-absent"),"query","faith",BigInteger.ZERO,options,true,false);
            assertTrue(absent.path("accepted").booleanValue());var nativeAbsent=(ObjectNode)absent.get("native");
            GuiPresentationResult.validate(nativeAbsent,run.invocation.nativeContext(),"query",GuiModels.WindowKind.FAITH,new GuiModels.Subject(0),options);
            assertFalse(nativeAbsent.path("presentation_ui").path("source_bound").booleanValue());
            ObjectNode selectors=options.deepCopy().put("presentation_target","faith_core_tenet").put("presentation_index",0).put("presentation_receipt","0123456789abcdef0123456789abcdef");
            var bad=run.original(root.resolve("original-bad-cache"),"query","faith",BigInteger.valueOf(50),selectors,false,true);
            assertFalse(bad.path("accepted").booleanValue());
            assertThrows(IllegalArgumentException.class,()->GuiPresentationResult.validate((ObjectNode)bad.get("native"),run.invocation.nativeContext(),"query",GuiModels.WindowKind.FAITH,new GuiModels.Subject(50),selectors));
            for(String field:List.of("action_owner_epoch","observation_owner_epoch","cache_texts","targets")){
                var changed=nativeAbsent.deepCopy();((ObjectNode)changed.get("presentation_ui")).remove(field);
                assertThrows(IllegalArgumentException.class,()->GuiPresentationResult.validate(changed,run.invocation.nativeContext(),"query",GuiModels.WindowKind.FAITH,new GuiModels.Subject(0),options));
            }
            var wrong=nativeAbsent.deepCopy();((ObjectNode)wrong.get("presentation_ui")).put("source_bound",true);
            assertThrows(IllegalArgumentException.class,()->GuiPresentationResult.validate(wrong,run.invocation.nativeContext(),"query",GuiModels.WindowKind.FAITH,new GuiModels.Subject(0),options));
            assertEquals(0,run.fixture.nativeActionWrites());
        }
    }
    @Test void existingUmbrellaClericalAndGlobalStackQueriesKeepTheirDistinctOriginalSelectors()throws Exception{
        try(var run=new Run(root.resolve("clerical-global-queries"))){
            for(String target:List.of("clerical_puppet","external_clerical_puppet","global_stack")){
                boolean global=target.equals("global_stack");String kind=global?"tooltips":"clerical_interaction";
                BigInteger subject=global?BigInteger.ZERO:new BigInteger("2148676694");
                ObjectNode options=StrictJson.object();if(!global)options.put("presentation_target",target);
                ObjectNode args=StrictJson.object().put("window_kind",kind).put("subject_id",subject).put("expected_revision",run.invocation.publicRevision());
                if(!global)args.put("presentation_target",target);
                var original=run.original(root.resolve("original-"+target),"query",kind,subject,options,false,false);
                assertTrue(original.path("accepted").booleanValue(),original.toString());run.readPacket.set((ObjectNode)original.get("native"));
                Request request=GuiCodec.decode(Method.QUERY_PRESENT.originalName(),args);var reply=run.read(request);
                var nativeFields=(ObjectNode)OpportunityJson.toNode(reply.receipt().request().arguments());
                assertFalse(nativeFields.has("presentation_tab"));assertFalse(nativeFields.has("presentation_index"));
                var actual=PublicDataJson.object(GuiPublicBinder.read(request,reply,Optional.of(run.before)));
                assertEquals(PublicDataJson.object(GuiCodec.encodePublicOriginal(raw((ObjectNode)original.get("public")))),actual);
                if(global){assertFalse(actual.path("tree").path("root_available").booleanValue());assertEquals(0,actual.path("tree").path("widgets").size());}
                else assertFalse(actual.path("presentation_ui").path("clerical_preview").path("command_submitted").booleanValue());
            }
            int reads=run.fixture.scenarioReadWrites();
            ObjectNode forbidden=StrictJson.object().put("operation","query").put("window_kind","tooltips").put("subject_id",0)
                .put("presentation_tab","").put("expected_revision",run.invocation.publicRevision());
            Request invalid=GuiCodec.decode(Method.PRESENT.originalName(),forbidden);
            assertThrows(RuntimeException.class,()->run.read(invalid));assertEquals(reads,run.fixture.scenarioReadWrites());
            ObjectNode noReceipt=StrictJson.object().put("operation","open_clerical_preview").put("window_kind","clerical_interaction")
                .put("subject_id",2148676694L).put("presentation_target","clerical_puppet").put("expected_revision",run.invocation.publicRevision());
            Request invalidAction=GuiCodec.decode(Method.PRESENT.originalName(),noReceipt);
            assertThrows(IllegalArgumentException.class,()->run.fixture.writer.locked(same->run.service.invoke(invalidAction,run.invocation)));
            assertEquals(0,run.fixture.nativeActionWrites());
        }
    }
    @Test void allEightPublicNamesRetainTypedArgumentsAndRejectBooleanOrUnknownSelector() {
        for(String name:List.of("ck3_open_faith_window_v1","ck3_present_faith_power_ui_v1","ck3_query_faith_power_ui_v1","ck3_query_faith_power_tooltip_v1",
                "ck3_click_white_control_v1","ck3_click_white_numeric_control_v1","ck3_query_white_player_business_variables_v1","ck3_query_white_rendered_text_v1"))
            assertTrue(GuiFaithWhitePublicFormatter.supports(Method.exact(name)));
        var numeric=StrictJson.object().put("control","martial_plus_1").put("expected_before_value",6).put("expected_before_price_text","actual price").put("intent_id","once");
        var request=GuiCodec.decode(Method.WHITE_NUMERIC.originalName(),numeric);assertEquals(request,GuiCodec.decode(request.method().originalName(),GuiCodec.encodeRequest(request)));
        numeric.put("expected_before_value",true);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.WHITE_NUMERIC.originalName(),numeric));
        var faith=StrictJson.object().put("faith_id",true);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.OPEN_FAITH.originalName(),faith));
        var unknown=StrictJson.object().put("operation","query").put("window_kind","faith").put("subject_id",0).put("presentation_target","not_original");
        assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.PRESENT.originalName(),unknown));
    }
}
