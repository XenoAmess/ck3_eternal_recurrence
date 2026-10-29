package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.OrdinaryPlanner;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePendingInteraction;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Action;
import org.xar.ck3.control.nativebridge.capabilities.interactions.PendingContextCodec;
import org.xar.ck3.control.nativebridge.capabilities.interactions.PendingInteractionContracts;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPolicy;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RootInteractionContextProjection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeComposer;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedInteractionContinuation;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Real original software producers and real Java consumers. No Game, transport send or Root admission is asserted. */
final class UnknownInteractionNativeChainTest {
    private static final Instant NOW=Instant.parse("2026-10-24T02:00:00Z"),DEADLINE=Instant.parse("2030-01-01T00:00:00Z");
    private static final BigInteger PUBLIC=new BigInteger("9007199254740993");
    private static final int INSTANCE=-2130706399;
    private static final List<String> STEPS=List.of("reject-pending-character-interaction","accept-pending-character-interaction",
            "acknowledge-pending-character-interaction","block-pending-character-interaction");
    private record Original(String name,ObjectNode packet,ObjectNode context,ObjectNode query,ObjectNode semantic,ObjectNode expected,
            ObjectNode ordinaryCore,ObjectNode ordinaryPlan,List<String> steps) { }
    private record OrdinaryRun(PlanningResult result,List<OpportunityJson.Obj> captured) { }
    private static List<Original> originals;
    private static Original compiledOriginal;
    @TempDir Path temporary;

    @BeforeAll static void captureOriginalPythonProducer() throws Exception {
        String python=System.getProperty("xar.python"),repositoryProperty=System.getProperty("xar.repository.root");
        assertNotNull(python,"required xar.python missing; original producer differential cannot skip");assertFalse(python.isBlank());
        assertNotNull(repositoryProperty,"required xar.repository.root missing; original producer differential cannot skip");assertFalse(repositoryProperty.isBlank());
        String repository=Path.of(repositoryProperty).toRealPath().toString();
        String script="""
            import copy, importlib.util, json, os
            from pathlib import Path
            from xar_autoplayer.bridge.native_driver import _semantic_snapshot_from_frame
            from xar_autoplayer.pending_interaction_fallback import plan_pending_interaction_left_reply_v1
            from xar_autoplayer import strategy
            root=Path(os.environ['XAR_SOURCE_REPOSITORY'])
            spec=importlib.util.spec_from_file_location('original_pending_fixture',root/'ck3_autonomous_player/tests/unit/test_pending_character_interaction_context_v1_bridge.py')
            fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
            steps=['reject-pending-character-interaction','accept-pending-character-interaction','acknowledge-pending-character-interaction','block-pending-character-interaction']
            rows=[]
            for name in ('normal','notification','disabled','no_native','ransom_blocked','blocked_marriage','known_accept','compiled-source'):
                notification=name=='notification'
                packet=fixture._semantic_snapshot()
                state=packet['state'];state['local_player_id']=2001;state['one_life_terminal_reason']=None
                state['played_character'].update(spouse_ids=[],betrothed_id=None,primary_spouse_id=None)
                state['pending_character_interaction']['auto_accept_notification']=notification
                context=fixture._frame(notification=notification)
                if name=='compiled-source':
                    context['definition'].update(canonical_key='request_clerical_chastity_interaction',deterministic_key_hash=1409884230)
                elif name=='ransom_blocked':
                    context['definition']['canonical_key']='pay_ransom_interaction'
                elif name=='blocked_marriage':
                    context['definition'].update(canonical_key='arrange_marriage_interaction',deterministic_key_hash=1298930137)
                    context['terms']['special_data_present']=True
                    context['terms']['special_war_binding'].update(reason='special_interaction_subtype_opaque')
                    context['readiness']['not_ready_reasons'][0]='special_interaction_subtype_opaque'
                elif name=='known_accept':
                    context['definition']['canonical_key']='spar_with_knight_interaction'
                    for action in ('reject','block'):context['legality'][action].update(allowed=False,reason='native_reply_not_allowed')
                if name=='disabled':context['legality']['reject'].update(allowed=False,reason='reject_not_legal')
                actualsteps=[step for step in steps if not(name=='no_native' and step.startswith('reject-'))]
                semantic=_semantic_snapshot_from_frame(packet)
                semantic.update(native_revision=41,revision=9007199254740993,episode_character_id=2001,episode_run_id='episode-real-1')
                semantic['diagnostics']={'bridge_pid':42,'connection_generation':5,'hello':{'expected_ck3_version':context['build']['version'],'expected_ck3_sha256':context['build']['exe_sha256']}}
                expected=plan_pending_interaction_left_reply_v1(snapshot=semantic,context=context,original_plan=None,action_steps=actualsteps,registry_state_dir=None)
                query=fixture._native_result(frame=context)
                recorded=copy.deepcopy(query)
                recorded.update(queried_snapshot_id=semantic['snapshot_id'],queried_revision=semantic['revision'],queried_native_revision=semantic['native_revision'])
                history=[dict(command=recorded['step'],ok=True,result=recorded)]
                core=strategy._choose_one_life_turn_core(history,snapshot=semantic,action_steps=actualsteps,bridge_capabilities=())
                ordinary=strategy.choose_one_life_turn(history,snapshot=semantic,action_steps=actualsteps,bridge_capabilities=())
                rows.append(dict(name=name,packet=packet,context=context,query=query,semantic=semantic,expected=expected,ordinary_core=core,ordinary_plan=ordinary,steps=actualsteps))
            print(json.dumps(rows,separators=(',',':'),ensure_ascii=False))
            """;
        ProcessBuilder builder=new ProcessBuilder(python,"-c",script).directory(Path.of(repository).toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY",repository);builder.environment().put("PYTHONPATH",Path.of(repository,"ck3_autonomous_player","src").toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process child=builder.start();
        // Drain concurrently; timeout and nonzero exit are failures, never skips.
        var output=java.util.concurrent.CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readAllBytes();}catch(IOException e){throw new UncheckedIOException(e);}});
        boolean finished=child.waitFor(45,TimeUnit.SECONDS);if(!finished)child.destroyForcibly();assertTrue(finished,"original Python producer timed out");
        byte[] bytes=output.get(5,TimeUnit.SECONDS);assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));
        JsonNode rows=StrictJson.parse(bytes,StrictJson.EXPLICIT_MAX_BYTES);assertTrue(rows.isArray());assertEquals(8,rows.size());List<Original> typed=new ArrayList<>();
        for(JsonNode row:rows){List<String> steps=new ArrayList<>();row.path("steps").forEach(v->{assertTrue(v.isTextual());steps.add(v.textValue());});
            typed.add(new Original(row.path("name").textValue(),object(row.get("packet")),object(row.get("context")),object(row.get("query")),object(row.get("semantic")),object(row.get("expected")),
                    object(row.get("ordinary_core")),object(row.get("ordinary_plan")),List.copyOf(steps)));}
        compiledOriginal=typed.stream().filter(row->row.name().equals("compiled-source")).findFirst().orElseThrow();
        originals=typed.stream().filter(row->!row.name().equals("compiled-source")).toList();assertEquals(7,originals.size());
    }

    @Test void actualOriginalProducerMatchesSharedSemanticContextAndLegacyPlanWithOneDeclaredVersionedDelta() throws Exception {
        for(Original original:originals){Fixture fixture=new Fixture(original,true);var before=fixture.before;
            JsonNode semantic=DriverJson.toNode(before.semantic());
            same(original.semantic().get("pending_character_interaction"),semantic.get("pending_character_interaction"));
            same(NativePendingInteraction.normalize(original.packet().path("state").path("pending_character_interaction")),semantic.get("pending_character_interaction"));
            Context actual=new RootInteractionContextProjection(Build.WANDERER6).project(before,DEADLINE);
            var nativeContext=PendingContextCodec.decode(raw(original.query()),actual,new PendingId(INSTANCE));
            assertEquals(INSTANCE,nativeContext.instance().value());
            ObjectNode current=fixture.plan();ObjectNode legacy=current.deepCopy();
            ObjectNode gui=object(legacy.path("unhandled_interaction_fallback").get("gui_binding"));
            assertTrue(gui.remove("current_presentation").isObject());same(original.expected(),legacy);
            ObjectNode presentation=object(current.path("unhandled_interaction_fallback").path("gui_binding").get("current_presentation"));
            assertEquals(original.name().equals("notification")?1:2,presentation.path("buttons").size());
            assertFalse(presentation.path("full_widget_visibility_observed").booleanValue());assertTrue(presentation.path("supplemental_block").path("shown").isNull());
            var decoded=CurrentInteractionPresentation.validateCapture(current.get("unhandled_interaction_fallback"),nullableText(current.get("selected_step")),true);
            assertTrue(decoded.isPresent());
            same(current,StrictJson.parse(StrictJson.canonical(current,65536)));
        }
    }

    @Test void realRejectAndNotificationAckReachDurableBeforeNativeWireIndependentAfterArchiveAndPublicConsumer() throws Exception {
        for(String name:List.of("normal","notification"))for(boolean receivedAck:List.of(true,false)){
            Fixture fixture=new Fixture(original(name),true);Produced produced=fixture.execute(receivedAck);
            assertTrue(produced.receipt().applied().isPresent());assertFalse(produced.receipt().eligibleAdvance());
            var original=produced.material().orElseThrow();JsonNode body=StrictJson.parse(original.compatibleResult().bytes());
            assertEquals(name.equals("notification")?"acknowledged":"rejected",body.path("interaction_result").path("status").textValue());
            assertEquals(INSTANCE,body.path("interaction_result").path("instance_id").intValue());assertEquals(1001,body.path("interaction_result").path("sender_character_id").intValue());
            assertTrue(body.path("remaining_pending_character_interaction").isNull());assertTrue(body.path("paused").booleanValue());
            assertEquals(PUBLIC.add(BigInteger.ONE),body.path("revision").bigIntegerValue());
            assertEquals("xar.java-native-event-result/v3",body.path("event_result_projection_schema").textValue());
            JsonNode wire=fixture.publicResult(produced);assertEquals(PUBLIC.add(BigInteger.ONE).toString(),wire.path("revision").textValue());
            assertEquals(receivedAck,wire.path("action_receipt").path("native_ack_received").booleanValue());
            assertTrue(wire.path("action_receipt").path("postcondition_verified").booleanValue());assertFalse(wire.path("replay_allowed").booleanValue());
            if(name.equals("notification"))assertTrue(wire.path("acknowledged").booleanValue());else assertFalse(wire.path("accepted").booleanValue());
            JsonNode after=fixture.incidentBody(".after.json");
            assertEquals(receivedAck,after.path("command_acknowledged").booleanValue());
            assertEquals(receivedAck,after.path("original_pending_advanced_verified").booleanValue());
            assertEquals(receivedAck,after.path("original_pending_advanced_in_response").booleanValue());
            assertEquals("sdk-response-only",after.path("postcondition_scope").textValue());assertFalse(after.path("durable_completion_granted").booleanValue());
            JsonNode index=fixture.incidentBody(".after-index.json");assertTrue(index.path("independent_postcondition_verified").booleanValue());
            assertEquals(0,fixture.journal.scan(fixture.journal.origin()).incompleteAfter());
            same(wire,DriverJson.toNode(DriverJson.object(DriverJson.encodeNode(wire),65536)));
        }
    }

    @Test void ackOnlyAndUnknownWithOriginalWindowStillPresentPersistNegativeEvidenceWithoutAfterOrReplay() throws Exception {
        for(String name:List.of("normal","notification"))for(boolean receivedAck:List.of(true,false)){
            Fixture fixture=new Fixture(original(name),false);Produced produced=fixture.execute(receivedAck);
            assertTrue(produced.receipt().applied().isEmpty());assertTrue(produced.material().isEmpty());assertFalse(produced.receipt().settled());
            JsonNode wire=fixture.publicResult(produced);
            assertEquals(receivedAck,wire.path("action_receipt").path("native_ack_received").booleanValue());
            assertFalse(wire.path("action_receipt").path("postcondition_verified").booleanValue());assertFalse(wire.path("replay_allowed").booleanValue());
            assertTrue(wire.path(name.equals("notification")?"acknowledged":"accepted").isNull());
            JsonNode negative=fixture.incidentBody(".unsettled.json");
            assertEquals(receivedAck?"ACK_RECEIVED":"UNKNOWN",negative.path("dispatch_kind").textValue());
            assertEquals(INSTANCE,negative.path("original_instance_id").intValue());assertTrue(negative.path("original_instance_present").booleanValue());
            assertFalse(negative.path("independent_postcondition_verified").booleanValue());assertFalse(negative.path("replay_allowed").booleanValue());
            ExactRef dispatch=ExactRef.fromJson(negative.get("original_dispatch_ref"));assertNotNull(fixture.archive.load(dispatch));
            for(String field:List.of("before_frame","before_driver_facts","after_frame","after_driver_facts"))
                assertArrayEquals(Files.readAllBytes(Path.of(ExactRef.fromJson(negative.get(field)).path())),fixture.archive.read(ExactRef.fromJson(negative.get(field))));
            try(var paths=Files.list(fixture.journal.configuration().incidentRoot())){assertTrue(paths.noneMatch(p->p.getFileName().toString().endsWith(".after-index.json")||p.getFileName().toString().endsWith(".after.json")));}
            assertEquals(1,fixture.journal.scan(fixture.journal.origin()).incompleteAfter());
            EpisodeIncidentJournal reopened=EpisodeIncidentJournal.openOriginal(fixture.journal.configuration(),fixture.journal.episodeReference());
            assertEquals(1,reopened.scan(reopened.origin()).incompleteAfter());
        }
    }

    @Test void disabledOrAbsentNativeLeftChannelIsDurablyCapturedWithoutAcceptanceSubstitution() throws Exception {
        for(String name:List.of("disabled","no_native")){
            Fixture fixture=new Fixture(original(name),false);ObjectNode plan=fixture.plan();assertTrue(plan.path("selected_step").isNull());
            ObjectNode capture=object(plan.get("unhandled_interaction_fallback"));
            assertEquals("reject",capture.path("selection").path("action").textValue());
            assertEquals(name.equals("disabled")?false:true,capture.path("selection").path("native_legal").booleanValue());
            assertEquals(name.equals("no_native")?false:true,capture.path("selection").path("action_reachable").booleanValue());
            var ticket=fixture.journal.captureBlocked(fixture.planningRequest(),DriverJson.object(StrictJson.canonical(plan,65536),65536),fixture.before.originalEvidence());
            JsonNode stored=StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path())));
            assertEquals("planning_diagnostic",stored.path("stage").textValue());assertFalse(stored.path("dispatch_attempted").booleanValue());
            assertTrue(stored.path("gui_binding").path("current_presentation").path("buttons").isArray());
            assertEquals(1,fixture.journal.scan(fixture.journal.origin()).diagnosticOnly());
            plan.put("selected_step","reject-pending-character-interaction");
            assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(fixture.command(plan)));
            plan.put("selected_step","accept-pending-character-interaction");
            assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(fixture.command(plan)));
        }
    }

    @Test void wrongInstanceFrameButtonsTypesAndSourceFailBeforeARequestCanBePrepared() throws Exception {
        Fixture fixture=new Fixture(original("normal"),true);
        List<java.util.function.Consumer<ObjectNode>> mutations=List.of(
                plan->capture(plan).put("pending_interaction_id",17),
                plan->object(capture(plan).get("binding")).put("revision",PUBLIC.add(BigInteger.ONE)),
                plan->object(capture(plan).get("binding")).put("connection_generation",6),
                plan->object(capture(plan).get("binding")).put("bridge_pid",43),
                plan->object(capture(plan).get("binding")).put("actor_character_id",1001),
                plan->object(capture(plan).get("context")).put("snapshot_revision",42),
                plan->object(capture(plan).get("context")).put("pending_interaction_id",true),
                plan->object(capture(plan).get("gui_binding")).put("sha256","a".repeat(64)),
                plan->object(capture(plan).get("selection")).put("button","accept_button"),
                plan->object(capture(plan).get("selection")).put("rendered_index",1),
                plan->object(capture(plan).get("selection")).put("native_legal",1),
                plan->object(capture(plan).path("gui_binding").path("current_presentation").path("buttons").get(0)).put("shown",false),
                plan->object(capture(plan).path("gui_binding").get("current_presentation")).remove("native_pending"),
                plan->object(capture(plan).path("gui_binding").path("current_presentation").get("native_pending")).put("sender_character_id",true));
        for(var mutate:mutations){ObjectNode plan=fixture.plan();mutate.accept(plan);
            assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(fixture.command(plan)));}
        ObjectNode legacy=fixture.plan();object(capture(legacy).get("gui_binding")).remove("current_presentation");
        ObjectNode planned=StrictJson.object().put("snapshot_id",fixture.before.identity().frame().snapshotId()).put("revision",PUBLIC);planned.set("plan",legacy);
        byte[] bytes=StrictJson.canonical(planned,65536);
        assertInstanceOf(InteractionBeforeEvidence.Prepared.class,InteractionBeforeComposer.compose(bytes,InteractionBeforeComposer.digest(bytes),
                new InteractionBeforeEvidence.Identity("a".repeat(32),NOW.toString(),"test-machine"),new InteractionBeforeEvidence.GuiSourcePin(InteractionFallback.GUI_SOURCE,InteractionFallback.GUI_SHA256)));
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(fixture.command(legacy)));
        Files.writeString(fixture.stock.resolve(InteractionFallback.GUI_SOURCE),"different GUI source",StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(TrustedEventSourceContext.UnavailableException.class,fixture::plan);
    }
    @Test void publicFallbackConsumerRejectsWrongProofInstanceRemainingFrameAndTypesWithoutRewritingTheOriginal() throws Exception {
        Fixture fixture=new Fixture(original("normal"),true);Produced produced=fixture.execute(true);
        RawJson material=produced.material().orElseThrow().compatibleResult();byte[] originalBytes=material.bytes();
        List<java.util.function.Consumer<ObjectNode>> mutations=List.of(
                root->root.put("revision",PUBLIC),
                root->root.put("revision",true),
                root->root.put("snapshot_id","wrong-original-after"),
                root->root.remove("event_result_projection_schema"),
                root->object(root.get("pending_character_interaction_selection")).put("ending_snapshot_id","wrong-after"),
                root->object(root.get("pending_character_interaction_selection")).put("postcondition_verified",1),
                root->object(root.get("interaction_result")).put("instance_id",INSTANCE+1),
                root->object(root.get("interaction_result")).put("sender_character_id",true),
                root->root.remove("remaining_pending_character_interaction"),
                root->root.set("remaining_pending_character_interaction",original("normal").semantic().get("pending_character_interaction")));
        for(var mutate:mutations){ObjectNode changed=object(StrictJson.parse(originalBytes));mutate.accept(changed);
            assertThrows(IllegalArgumentException.class,()->PendingInteractionPublicCodec.result(produced.receipt(),fixture.archive,Optional.of(raw(changed)),
                    new PendingSummary(new PendingId(INSTANCE),org.xar.ck3.control.contracts.NativeCharacterId.of(1001),false),Action.REJECT));}
        assertArrayEquals(originalBytes,material.bytes());assertFalse(StrictJson.parse(originalBytes).has("postcondition_verified"));
        JsonNode wire=fixture.publicResult(produced);assertTrue(wire.path("postcondition_verified").booleanValue());
        assertArrayEquals(originalBytes,material.bytes());
    }
    @Test void completePythonOrdinaryReturnMatchesActualJavaPendingPoliciesAndOriginalPlanGuards() throws Exception {
        for(Original original:originals) {
            Fixture fixture=new Fixture(original,true);OrdinaryRun actual=fixture.ordinary(fixture.before,List.of());
            String selected=nullableText(original.ordinaryPlan().get("selected_step"));
            if(selected==null)assertInstanceOf(PlanningResult.ReadOnlyWait.class,actual.result(),original.name());
            else assertEquals(selected,assertInstanceOf(PlanningResult.ActionSelected.class,actual.result()).command().operation().value(),original.name());
            OpportunityJson.Obj effective=actual.captured().isEmpty()?actual.result().trace().finalPlan().orElseThrow().detail():actual.captured().getLast();
            ObjectNode plan=object(DriverJson.toNode(effective));
            assertEquals(original.ordinaryPlan().path("phase").textValue(),plan.path("phase").textValue(),original.name());
            if(original.ordinaryPlan().has("unhandled_interaction_fallback")) {
                ObjectNode expected=capture(original.ordinaryPlan()),observed=capture(plan);
                for(String field:List.of("pending_interaction_id","binding","context","selection","reply_options","registry_known","offline_followup_required"))
                    same(expected.get(field),observed.get(field));
                assertTrue(observed.path("gui_binding").path("current_presentation").isObject());
                if(original.name().equals("ransom_blocked")) {
                    assertEquals("known_received_ransom",original.ordinaryCore().path("decision").path("classification").textValue());
                    assertTrue(original.ordinaryCore().path("selected_step").isNull());
                    assertTrue(observed.path("original_plan").path("known_policy_handled").booleanValue());
                    assertTrue(observed.path("selection").path("native_legal").booleanValue());
                }
            } else assertFalse(plan.has("unhandled_interaction_fallback"),original.name());
            if(original.name().equals("blocked_marriage"))assertTrue(SourceReviewedInteractionContinuation.originalPlan(
                    RetainedJson.parse(DriverJson.encode(effective))).blockedMarriageReply());
            if(original.name().equals("known_accept"))assertEquals("accept-pending-character-interaction",selected);
        }
    }

    @Test void blockedKnownReplyWithInvalidOptionalRegistryReachesOneNativePacketAfterOrUnknownAndFreshOrdinaryRound() throws Exception {
        for(boolean advance:List.of(true,false))for(boolean ack:List.of(true,false)) {
            Fixture fixture=new Fixture(original("ransom_blocked"),advance);
            Path entry=fixture.state.resolve("evidence/interaction-source-registry").resolve("0".repeat(64)+".json");
            Files.createDirectories(entry.getParent());Files.write(entry,new byte[65_537],StandardOpenOption.CREATE_NEW);
            var actual=fixture.ordinary(fixture.before,List.of());
            ActionCommand command=assertInstanceOf(PlanningResult.ActionSelected.class,actual.result()).command();
            assertEquals("reject-pending-character-interaction",command.operation().value());
            ObjectNode capture=object(DriverJson.toNode(command.arguments().get("unhandled_interaction_fallback")));
            assertFalse(capture.path("registry_known").booleanValue());assertTrue(capture.path("offline_followup_required").booleanValue());
            Produced produced=fixture.execute(command,ack);assertEquals(1,fixture.nativeRequests.get());
            assertEquals(advance,produced.receipt().applied().isPresent());assertEquals(advance,produced.receipt().settled());
            JsonNode result=fixture.publicResult(produced);assertFalse(result.path("replay_allowed").booleanValue());
            assertEquals(ack,result.path("action_receipt").path("native_ack_received").booleanValue());
            if(advance) {
                var after=produced.material().orElseThrow().frames().after();
                assertSame(OpportunityJson.Nil.INSTANCE,after.semantic().get("pending_character_interaction"));
                assertInstanceOf(PlanningResult.ReadOnlyWait.class,fixture.ordinary(after,List.of()).result());
                assertEquals(1,fixture.nativeRequests.get(),"fresh ordinary planning cannot repeat the old native reply");
            } else {
                assertTrue(produced.material().isEmpty());
                var negative=fixture.incidentBody(".unsettled.json");
                assertTrue(negative.path("original_instance_present").booleanValue());
                assertEquals(ack?"ACK_RECEIVED":"UNKNOWN",negative.path("dispatch_kind").textValue());
                assertFalse(negative.path("replay_allowed").booleanValue());
            }
        }
    }

    @Test void sharedOriginalPlanConsumesSelectedExistingAndExactMarriageGuardsWithoutAReply() throws Exception {
        Fixture fixture=new Fixture(original("normal"),true);
        ObjectNode selected=StrictJson.object().put("phase","pending_known_selected").put("selected_step","accept-pending-character-interaction");
        ObjectNode existing=StrictJson.object().put("phase","pending_previous").putNull("selected_step");
        existing.putObject("unhandled_interaction_fallback");
        ObjectNode invalidMarriage=StrictJson.object().put("phase","pending_character_interaction_degraded_blocked").putNull("selected_step");
        ObjectNode decision=invalidMarriage.putObject("decision").put("classification","evidence_invalid").put("interaction_key","arrange_marriage_interaction");
        decision.putArray("marriage_contract_gaps").add("actual_roles_missing");decision.putObject("definition_classification").put("definition_key","arrange_marriage_interaction");
        for(ObjectNode previous:List.of(selected,existing,invalidMarriage)) {
            var input=new SourceReviewedInteractionContinuation.Input(Optional.of(RetainedJson.object(RetainedJson.parse(DriverJson.encode(fixture.before.semantic())))),
                    Optional.of(RetainedJson.object(RetainedJson.parse(StrictJson.canonical(fixture.original.context())))),
                    RetainedJson.parse(StrictJson.canonical(previous)),fixture.original.steps(),true);
            assertTrue(SourceReviewedInteractionContinuation.plan(input,fixture.trusted).isEmpty());
        }
        assertTrue(SourceReviewedInteractionContinuation.originalPlan(RetainedJson.parse(StrictJson.canonical(invalidMarriage))).blockedMarriageReply());
        decision.putArray("marriage_contract_gaps");
        assertFalse(SourceReviewedInteractionContinuation.originalPlan(RetainedJson.parse(StrictJson.canonical(invalidMarriage))).blockedMarriageReply());
    }

    @Test void optionalCompiledReviewFailuresRetainTheActualPythonLeftChoiceThroughOnePacketAfterOrUnknown() throws Exception {
        assertNotNull(compiledOriginal);
        assertEquals("pending_character_interaction_reviewed_left_reply",compiledOriginal.ordinaryPlan().path("phase").textValue());
        assertEquals("reject-pending-character-interaction",compiledOriginal.ordinaryPlan().path("selected_step").textValue());
        ObjectNode originalCapture=capture(compiledOriginal.ordinaryPlan());assertTrue(originalCapture.path("registry_known").booleanValue());
        for(String sourceState:List.of("missing","directory","hash-mismatch"))for(boolean advance:List.of(true,false))for(boolean ack:List.of(true,false)) {
            Fixture fixture=new Fixture(compiledOriginal,advance);
            Path optional=fixture.stock.resolve("common/character_interactions/clerical_chastity_interaction.txt");
            if(!sourceState.equals("missing"))Files.createDirectories(optional.getParent());
            if(sourceState.equals("directory"))Files.createDirectory(optional);
            if(sourceState.equals("hash-mismatch"))Files.writeString(optional,"unreviewed optional definition",StandardOpenOption.CREATE_NEW);
            else {
                var unavailable=assertThrows(TrustedEventSourceContext.UnavailableException.class,()->fixture.trusted.readInteractionSource(optional,2_097_152));
                assertEquals(TrustedEventSourceContext.FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE,unavailable.failureKind());
            }
            var actual=fixture.ordinary(fixture.before,List.of());
            ActionCommand command=assertInstanceOf(PlanningResult.ActionSelected.class,actual.result()).command();
            assertEquals(compiledOriginal.ordinaryPlan().path("selected_step").textValue(),command.operation().value());
            ObjectNode actualPlan=object(DriverJson.toNode(command.arguments())),captured=capture(actualPlan);
            assertEquals("pending_character_interaction_left_fallback",actualPlan.path("phase").textValue());
            for(String field:List.of("schema","kind","policy","pending_interaction_id","interaction_definition_key","binding","context","reply_options","selection",
                    "presented_choice_policy","semantic_optimal","native_ai_equivalent"))same(originalCapture.get(field),captured.get(field));
            assertFalse(captured.path("registry_known").booleanValue());assertTrue(captured.path("reviewed_rule").isNull());
            assertTrue(captured.path("offline_followup_required").booleanValue());
            assertEquals("unknown",captured.path("offline_registry_audit").path("status").textValue());
            assertEquals("no_match",captured.path("offline_registry_audit").path("reason").textValue());
            Produced produced=fixture.execute(command,ack);assertEquals(1,fixture.nativeRequests.get());
            assertEquals(advance,produced.receipt().applied().isPresent());JsonNode result=fixture.publicResult(produced);
            assertEquals(ack,result.path("action_receipt").path("native_ack_received").booleanValue());assertFalse(result.path("replay_allowed").booleanValue());
            if(advance) {
                var after=produced.material().orElseThrow().frames().after();
                assertSame(OpportunityJson.Nil.INSTANCE,after.semantic().get("pending_character_interaction"));
                assertInstanceOf(PlanningResult.ReadOnlyWait.class,fixture.ordinary(after,List.of()).result());
            } else {
                assertFalse(produced.receipt().settled());assertTrue(produced.material().isEmpty());
                JsonNode negative=fixture.incidentBody(".unsettled.json");assertTrue(negative.path("original_instance_present").booleanValue());
                assertEquals(ack?"ACK_RECEIVED":"UNKNOWN",negative.path("dispatch_kind").textValue());assertFalse(negative.path("replay_allowed").booleanValue());
            }
            assertEquals(1,fixture.nativeRequests.get(),"optional source knowledge cannot authorize a second native submission");
        }
    }

    @Test void optionalCompiledReviewFailureCannotSoftenTheOriginalGuiOrRequiredRootIdentity() throws Exception {
        for(boolean rootDrift:List.of(false,true)) {
            Fixture fixture=new Fixture(compiledOriginal,true);
            if(rootDrift) {
                Files.move(fixture.stock,fixture.directory.resolve("original-stock"));
                Files.createDirectory(fixture.stock);
            } else Files.writeString(fixture.stock.resolve(InteractionFallback.GUI_SOURCE),"changed GUI",StandardOpenOption.APPEND);
            var unavailable=assertThrows(TrustedEventSourceContext.UnavailableException.class,()->fixture.ordinary(fixture.before,List.of()));
            assertEquals(TrustedEventSourceContext.FailureKind.REQUIRED_SOURCE_UNAVAILABLE,unavailable.failureKind());
            assertEquals(0,fixture.nativeRequests.get());
        }
    }

    @Test void delayedOriginalWindowClosureIsReadWithoutAnotherReplyPacket() throws Exception {
        assertAll("original delayed pending windows",()->delayedReply("normal"),()->delayedReply("notification"),
                ()->delayedReply("normal",java.util.OptionalInt.of(0)));
    }
    private void delayedReply(String name) throws Exception {
        delayedReply(name,java.util.OptionalInt.empty());
    }
    private void delayedReply(String name,java.util.OptionalInt replacement) throws Exception {
        Fixture fixture=new Fixture(original(name),true,2);
        fixture.replacementPendingId=replacement;
        Produced actual=fixture.execute(true);
        assertEquals(1,fixture.nativeRequests.get(),"the original reply packet must be prepared once");
        assertTrue(actual.receipt().applied().isPresent(),"an early unchanged window must not hide the later independent closure: "+name);
        var later=actual.material().orElseThrow().frames().after();
        assertEquals(BigInteger.valueOf(43),later.identity().frame().identity().nativeRevision());
        if(replacement.isEmpty())assertSame(OpportunityJson.Nil.INSTANCE,later.semantic().get("pending_character_interaction"));
        else {
            var remaining=assertInstanceOf(OpportunityJson.Obj.class,later.semantic().get("pending_character_interaction"));
            assertEquals(BigInteger.valueOf(replacement.getAsInt()),OpportunityJson.integer(remaining.get("instance_id"),"actual replacement pending instance"));
        }
        JsonNode wire=fixture.publicResult(actual);
        assertEquals(PUBLIC.add(BigInteger.TWO).toString(),wire.path("revision").textValue());
        assertTrue(wire.path("action_receipt").path("postcondition_verified").booleanValue());
        assertFalse(wire.path("replay_allowed").booleanValue());
        if(name.equals("notification"))assertTrue(wire.path("acknowledged").booleanValue());else assertFalse(wire.path("accepted").booleanValue());
    }
    @Test void pendingReadFailureKeepsLastActualWindowAndInterruptFlag() throws Exception {
        for(ReadFailure failure:List.of(ReadFailure.UNAVAILABLE,ReadFailure.INTERRUPTED)) {
            Fixture fixture=new Fixture(original("normal"),false);
            fixture.subsequentReadFailure=failure;
            try {
                var pair=fixture.readOnlyPair(java.time.Duration.ofSeconds(5));
                assertEquals(BigInteger.valueOf(42),pair.after().identity().frame().identity().nativeRevision());
                var remaining=assertInstanceOf(OpportunityJson.Obj.class,pair.after().semantic().get("pending_character_interaction"));
                assertEquals(BigInteger.valueOf(INSTANCE),OpportunityJson.integer(remaining.get("instance_id"),"actual original pending instance"));
                assertEquals(failure==ReadFailure.INTERRUPTED,Thread.currentThread().isInterrupted());
                assertEquals(3,fixture.nativeObservations.get(),"before, unchanged after, then the real failing read only");
                assertEquals(0,fixture.nativeRequests.get(),"read-only observation owns no Native submission");
            } finally { Thread.interrupted(); }
        }
    }
    @Test void pendingReadDeadlineKeepsOriginalWindowAndNeverSubstitutesAnAbsentInstance() throws Exception {
        Fixture fixture=new Fixture(original("normal"),false);
        fixture.repeatUnchangedAfter=true;
        Instant deadline=Instant.now().plusSeconds(2);
        var pair=fixture.readOnlyPair(deadline);
        assertFalse(Instant.now().isBefore(deadline),"an unchanged original window must consume its bounded observation window");
        assertEquals(BigInteger.valueOf(42),pair.after().identity().frame().identity().nativeRevision());
        assertTrue(fixture.nativeObservations.get()>=3,"a cached first after frame cannot end the bounded wait early");
        var remaining=assertInstanceOf(OpportunityJson.Obj.class,pair.after().semantic().get("pending_character_interaction"));
        assertEquals(BigInteger.valueOf(INSTANCE),OpportunityJson.integer(remaining.get("instance_id"),"actual original pending instance"));
        assertFalse(Thread.currentThread().isInterrupted());
        assertEquals(0,fixture.nativeRequests.get());
    }
    @Test void pendingReadCannotTurnConnectionDriftIntoAWaitTimeout() throws Exception {
        Fixture fixture=new Fixture(original("normal"),false);
        fixture.subsequentReadFailure=ReadFailure.CONNECTION_DRIFT;
        assertThrows(IllegalArgumentException.class,()->fixture.readOnlyPair(java.time.Duration.ofSeconds(5)));
        assertEquals(0,fixture.nativeRequests.get());
    }
    private enum ReadFailure { NONE,UNAVAILABLE,INTERRUPTED,CONNECTION_DRIFT }
    private static ObjectNode capture(ObjectNode plan){return object(plan.get("unhandled_interaction_fallback"));}

    private final class Fixture {
        private final Original original;
        private final boolean advance;
        private final Path directory,stock,state;
        private final DiskArchive archive;
        private final G2Source source;
        private final HeldDriverObservationPort held;
        private final DriverObservationAssembler.Complete before;
        private final TrustedEventSourceContext trusted;
        private final EpisodeIncidentJournal journal;
        private final AtomicInteger nativeRequests=new AtomicInteger();
        private final AtomicInteger nativeObservations=new AtomicInteger();
        private ReadFailure subsequentReadFailure=ReadFailure.NONE;
        private boolean repeatUnchangedAfter;
        private java.util.OptionalInt replacementPendingId=java.util.OptionalInt.empty();
        private Fixture(Original original,boolean advance) throws Exception {this(original,advance,1);}
        private Fixture(Original original,boolean advance,int advanceAtObservation) throws Exception {
            this.original=original;this.advance=advance;repeatUnchangedAfter=!advance;directory=Files.createTempDirectory(temporary,"native-chain-");
            archive=new DiskArchive(Files.createDirectory(directory.resolve("archive")));
            stock=Files.createDirectory(directory.resolve("stock"));state=Files.createDirectory(directory.resolve("state"));
            byte[] gui;
            try(var stream=UnknownInteractionNativeChainTest.class.getResourceAsStream("/unknownnotification/interaction_notification_window.gui")){
                assertNotNull(stream,"exact original GUI fixture missing");gui=stream.readAllBytes();}
            assertEquals(InteractionFallback.GUI_SHA256,DriverJson.sha256(gui));
            Path guiPath=stock.resolve(InteractionFallback.GUI_SOURCE);Files.createDirectories(guiPath.getParent());Files.write(guiPath,gui,StandardOpenOption.CREATE_NEW);
            trusted=TrustedEventSourceContext.openEvidence(new EventSourceReadContext("test-machine",state,stock));
            Path origin=directory.resolve("software-source.json");Files.write(origin,"explicit software fixture, no Game qualification".getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
            source=new G2Source("test-machine",NOW.toString(),"1.19.0.6@sha256:"+Build.WANDERER6.sha256(),EpisodeIncidentJournal.measure(origin));
            held=new HeldDriverObservationPort(deadline->{
                int observation=nativeObservations.getAndIncrement();
                if(observation>=2&&subsequentReadFailure==ReadFailure.UNAVAILABLE)
                    throw new UncheckedIOException(new IOException("actual fixture read unavailable after the unchanged window"));
                if(observation>=2&&subsequentReadFailure==ReadFailure.INTERRUPTED)
                    throw new InterruptedException("actual fixture read interrupted after the unchanged window");
                var actual=frame(repeatUnchangedAfter?Math.min(observation,1):observation,advanceAtObservation);
                if(observation>=2&&subsequentReadFailure==ReadFailure.CONNECTION_DRIFT)
                    return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",NativeEventPublicMaterialProducerTest.game(),BigInteger.valueOf(6),"held-session"),
                            actual.snapshotId(),actual.nativeRevision(),actual.state(),actual.originalPacket(),actual.observedAt());
                return actual;
            },actual->new DriverObservationFacts.Known(facts(actual)),
                    archive::preserveNativeFrame,new DriverObservationAssembler(),8);
            before=held.observe(DEADLINE);
            Path incidents=Files.createDirectory(directory.resolve("incidents")),scans=Files.createDirectory(directory.resolve("scans"));
            var configuration=new EpisodeIncidentJournal.Configuration(incidents,scans,Clock.fixed(NOW,ZoneOffset.UTC),pending->{assertTrue(pending>0);},Optional.of(trusted));
            journal=EpisodeIncidentJournal.initializeObserved(configuration,new EpisodeIncidentJournal.Binding(before.identity(),source,before.sessionId()),before.originalEvidence());
        }
        private NativeObservationPort.ObservedFrame frame(int observation,int advanceAtObservation) {
            ObjectNode packet=original.packet().deepCopy();long revision=41L+observation;
            packet.put("snapshot_id","native:"+revision).put("revision",revision);
            if(observation>=advanceAtObservation&&advance) {
                if(replacementPendingId.isPresent())object(packet.path("state").get("pending_character_interaction")).put("instance_id",replacementPendingId.getAsInt());
                else object(packet.get("state")).putNull("pending_character_interaction");
            }
            byte[] body=StrictJson.canonical(packet);byte[] framed=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
            return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",NativeEventPublicMaterialProducerTest.game(),BigInteger.valueOf(5),"held-session"),
                    "native:"+revision,BigInteger.valueOf(revision),raw(packet.get("state")),framed,NOW.plusSeconds(observation));
        }
        private DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual) {
            byte[] originalDriver=NativeEventPublicMaterialProducerTest.WIRE.replace(":73",":2001").getBytes(StandardCharsets.UTF_8);
            ExactRef imported=archive.preserveMaterial(new RawJson(originalDriver));
            DriverSnapshotFacts.Known known=DriverFactsRepository.imported(imported,originalDriver,3,7,NativeEventPublicMaterialProducerTest.game(),new OpportunityJson.Obj(Map.of()));
            RawJson full=new RawJson(known.driver().encode());ExactRef fullRef=archive.preserveMaterial(full);
            ObjectNode extras=StrictJson.object();extras.set("diagnostics",original.semantic().get("diagnostics"));
            RawJson manifest=DriverObservationEvidenceReader.encode(known,actual,PUBLIC.add(actual.nativeRevision().subtract(BigInteger.valueOf(41))),3,source,
                    DriverJson.object(StrictJson.canonical(extras),65536),fullRef);
            ExactRef reference=archive.preserveMaterial(manifest);
            return DriverObservationEvidenceReader.decode(reference,manifest,full,actual);
        }
        private ObjectNode plan() {
            var input=new SourceReviewedInteractionContinuation.Input(Optional.of(RetainedJson.object(RetainedJson.parse(DriverJson.encode(before.semantic())))),
                    Optional.of(RetainedJson.object(RetainedJson.parse(StrictJson.canonical(original.context())))),RetainedJson.NULL,original.steps(),false);
            return object(StrictJson.parse(SourceReviewedInteractionContinuation.encode(SourceReviewedInteractionContinuation.plan(input,trusted))));
        }
        private ActionCommand command(ObjectNode plan) {
            String step=plan.path("selected_step").textValue();assertNotNull(step);
            var expected=new ExpectedPostcondition(1,before.identity(),source,NativeEventPostconditionPort.PENDING_SCHEMA,List.of(
                    new ExpectedInteger(new FieldKey("old_instance_id"),BigInteger.valueOf(INSTANCE)),new ExpectedBoolean(new FieldKey("old_instance_advanced"),true),
                    new ExpectedInteger(new FieldKey("actor_id"),BigInteger.valueOf(2001)),new ExpectedText(new FieldKey("connection_generation_decimal"),"5")));
            return new ActionCommand("software-left-reply-"+original.name(),before.identity(),source,before.sessionId(),new OperationKey(step),
                    DriverJson.object(StrictJson.canonical(plan,65536),65536),expected,new Claims(Set.of(),Set.of(),Set.of(),Set.of("foreground-window")),DEADLINE);
        }
        private PlanningRequest planningRequest() {
            Set<OperationKey> actions=original.steps().stream().map(OperationKey::new).collect(java.util.stream.Collectors.toUnmodifiableSet());
            return new PlanningRequest(before.identity(),source,before.sessionId(),DEADLINE,
                    new PlanningObservation(before.semantic(),List.of(),actions,Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        }
        private OrdinaryRun ordinary(DriverObservationAssembler.Complete frame,List<ExternalFact> facts) {
            var steps=original.steps().stream().map(OperationKey::new).collect(java.util.stream.Collectors.toUnmodifiableSet());
            List<OpportunityJson.Obj> history=new ArrayList<>();
            if(frame.semantic().get("pending_character_interaction") instanceof OpportunityJson.Obj) {
                ObjectNode query=original.query().deepCopy();
                query.put("queried_snapshot_id",frame.identity().frame().snapshotId()).put("queried_revision",frame.identity().frame().revision())
                        .put("queried_native_revision",frame.identity().frame().identity().nativeRevision());
                ObjectNode row=StrictJson.object().put("command",PendingContextCodec.STEP).put("ok",true);row.set("result",query);
                history.add(DriverJson.object(StrictJson.canonical(row),65536));
            }
            var request=new PlanningRequest(frame.identity(),source,frame.sessionId(),DEADLINE,
                    new PlanningObservation(frame.semantic(),history,steps,Set.of(),Optional.empty(),facts,Optional.empty(),Optional.empty(),false));
            var captured=new ArrayList<OpportunityJson.Obj>();
            org.xar.ck3.control.application.planning.events.EventIncidentCapturePort captures=(actual,plan)-> {
                captured.add(plan);journal.captureBlocked(actual,plan,frame.originalEvidence());
            };
            var known=new KnownPendingInteractionPolicy(source.sourceRef(),
                    actual->new RootInteractionContextProjection(Build.WANDERER6).project(frame,actual.deadline()),
                    NO_READS,PendingInteractionContracts.pending(source.sourceRef()),operation->Optional.empty());
            known.bindIncidentCapture(captures);
            var continuation=EventPolicies.policies(source.sourceRef(),Optional.of(trusted),
                    (actual,operation,plan,material)->NativeEventPostconditionPort.expected(actual.before(),actual.source(),
                            actual.observations().snapshot(),operation,plan,material),
                    NO_READS,List.of(),(actual,raw)->Optional.empty(),captures,
                    (actual,operation,args,plan,purpose,domain)->{throw new AssertionError("pending continuation uses its real native expectation");})
                    .stream().filter(policy->policy.stage()==PlanningStage.EVENT_AND_INTERACTION_CONTINUATION).findFirst().orElseThrow();
            var realm=new RealmLifecycle(source.sourceRef());var policies=new ArrayList<OrdinaryPolicy>();
            for(PlanningStage stage:PlanningStage.values()) {
                if(stage==PlanningStage.EVENT_AND_INTERACTION_CONTINUATION)policies.add(continuation);
                else if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION)policies.add(realm);
                else policies.add(new OrdinaryPolicy() {
                    @Override public PlanningStage stage(){return stage;}
                    @Override public ExactRef implementationSource(){return source.sourceRef();}
                    @Override public Decision evaluate(PlanningRequest actual,Draft previous){
                        return stage==PlanningStage.ORDINARY_CORE?known.evaluateCore(actual,previous):new Keep("unrelated stage outside this software pending slice");
                    }
                });
            }
            return new OrdinaryRun(new OrdinaryPlanner(policies,Clock.fixed(NOW,ZoneOffset.UTC),realm).plan(request),List.copyOf(captured));
        }
        private NativeEffectSnapshots.Pair readOnlyPair(java.time.Duration window) {
            return readOnlyPair(Instant.now().plus(window));
        }
        private NativeEffectSnapshots.Pair readOnlyPair(Instant deadline) {
            ActionCommand originalCommand=command(plan());
            ActionCommand command=new ActionCommand(originalCommand.actionId(),originalCommand.before(),originalCommand.source(),originalCommand.sessionId(),
                    originalCommand.operation(),originalCommand.arguments(),originalCommand.expected(),originalCommand.claims(),deadline);
            NativeRequest prepared=EventActionPreparation.prepare(command);
            var guard=new GuardEvidence(before.identity(),source,before.sessionId(),before.connectionGeneration(),command.operation(),before.originalEvidence(),before.originalEvidence(),
                    "explicit-software-read-only-pending",NOW,DEADLINE);
            var attempt=new ActionState.Attempt("software-read-only-pending",NOW,guard,prepared);
            return new NativeEffectSnapshots(held,archive).read(command,attempt);
        }
        private Produced execute(boolean receivedAck) throws Exception { return execute(command(plan()),receivedAck); }
        private Produced execute(ActionCommand command,boolean receivedAck) throws Exception {
            var ticket=journal.before(command).orElseThrow();
            JsonNode beforeBody=StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path())));
            assertFalse(beforeBody.path("dispatch_attempted").booleanValue());assertEquals(INSTANCE,beforeBody.path("pending_interaction_id").intValue());
            assertTrue(beforeBody.path("gui_binding").path("current_presentation").isObject());
            NativeRequest prepared=EventActionPreparation.prepare(command);
            nativeRequests.incrementAndGet();
            byte[] outbound=NativeWire.execute("software-native-request",prepared.step(),before.identity().frame().identity().nativeRevision(),prepared.additionalFields().bytes());
            var bytes=ByteBuffer.wrap(outbound).order(ByteOrder.LITTLE_ENDIAN);assertEquals(outbound.length-4,bytes.getInt());byte[] payload=new byte[bytes.remaining()];bytes.get(payload);
            JsonNode sent=StrictJson.parse(payload);assertEquals(BigInteger.valueOf(41),sent.path("expected_revision").bigIntegerValue());
            assertEquals(INSTANCE,sent.path("pending_interaction_id").intValue());assertFalse(sent.has("option_number"));assertFalse(sent.has("native_option_index"));
            var guard=new GuardEvidence(before.identity(),source,before.sessionId(),before.connectionGeneration(),command.operation(),before.originalEvidence(),before.originalEvidence(),
                    "explicit-software-native-chain",NOW,DEADLINE);
            var attempt=new ActionState.Attempt("software-native-request",NOW,guard,prepared);
            RawJson token=raw(StrictJson.object().put("step",command.operation().value()).put("accepted",true).put("status","submitted"));
            NativeActionPort.DispatchOutcome dispatch;
            if(receivedAck){ObjectNode ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",attempt.requestId()).put("ok",true);ack.set("result",StrictJson.parse(token.bytes()));
                byte[] ackBody=StrictJson.canonical(ack);byte[] packet=ByteBuffer.allocate(ackBody.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(ackBody.length).put(ackBody).array();
                var acknowledged=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
                assertEquals(attempt.requestId(),acknowledged.requestId());assertTrue(acknowledged.nativeOk());
                var actualToken=acknowledged.result().token().map(value->new RawJson(value.value()));
                assertEquals(Optional.of(token),actualToken);assertArrayEquals(packet,acknowledged.packet().value());
                dispatch=new NativeActionPort.AckReceived(acknowledged.requestId(),acknowledged.nativeOk(),actualToken,
                        new RawJson(acknowledged.payload().value()),acknowledged.packet().value(),Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(),outbound)));
            }else dispatch=new NativeActionPort.Unknown(attempt.requestId(),"software lost ACK",outbound,Optional.empty());
            archive.preserve(dispatch);
            var queries=new NativeEventEffects.MaterialQueries(Optional.empty(),Optional.empty());
            NativeEventEffects.ObservedAfter callback=new NativeEventEffects.ObservedAfter(){
                @Override public void record(ActionCommand original,ActionState.Attempt actualAttempt,NativeEffectSnapshots.Pair frames,NativeEffectRegistry.Projected result){journal.observedAfter(original,actualAttempt,frames,result);}
                @Override public void recordUnsettled(ActionCommand original,ActionState.Attempt actualAttempt,NativeEventEffects.UnsettledObservation actual){
                    try{journal.observedUnsettled(original,actualAttempt,actual,archive.referenceOf(actual.dispatch()));}catch(IOException failure){throw new UncheckedIOException(failure);}}
            };
            NativeEffectRegistry.Projected projected=new NativeEventEffects(new NativeEffectSnapshots(held,archive),NO_READS,queries,callback).observe(command,attempt,dispatch);
            ActionState state;
            Optional<NativeEffectEvidence.Original> material;
            if(projected.result() instanceof ActionPorts.EffectObserved observed){
                state=new ActionState.Settled(attempt,dispatch,new ActionState.Applied(observed.observation()));
            }else if(dispatch instanceof NativeActionPort.AckReceived ack)state=new ActionState.AckReceived(attempt,ack);
            else state=new ActionState.Unknown(Optional.of(attempt),Optional.of(dispatch),"original result remains unknown",List.of(before.originalEvidence()));
            ActionReceipt receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),state);archive.preserveReceipt(receipt);
            assertEquals(receipt,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,archive),archive));
            if(receipt.applied().isPresent()){
                var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
                NativeEventEffects.archivedVerifier(command.operation(),source.sourceRef(),loader,queries).verifier().verify(null,receipt,archive);
                material=Optional.of(NativeEffectEvidence.load(receipt,archive,loader));
            }else material=Optional.empty();
            return new Produced(receipt,material);
        }
        private JsonNode publicResult(Produced produced) {
            boolean notification=original.name().equals("notification");
            RawJson result=PendingInteractionPublicCodec.result(produced.receipt(),archive,produced.material().map(NativeEffectEvidence.Original::compatibleResult),
                    new PendingSummary(new PendingId(INSTANCE),org.xar.ck3.control.contracts.NativeCharacterId.of(1001),notification),notification?Action.ACKNOWLEDGE:Action.REJECT);
            return DriverJson.toNode(DriverJson.object(result.bytes(),65536));
        }
        private JsonNode incidentBody(String suffix) throws IOException {
            try(var paths=Files.list(journal.configuration().incidentRoot())){List<Path> found=paths.filter(p->p.getFileName().toString().endsWith(suffix)).toList();
                assertEquals(1,found.size());return StrictJson.parse(Files.readAllBytes(found.getFirst()));}
        }
    }
    private static final PlanningReadPort NO_READS=new PlanningReadPort(){
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("pending advancement has no event material read");}
    };

    /** Disk bytes are immutable and checked on every read; object caches are this software fixture's typed codec lookup. */
    private static final class DiskArchive implements ActionPorts.OutcomeArchive {
        private final Path root;
        private final Map<ExactRef,ActionReceipt> receipts=new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> dispatches=new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests=new HashMap<>();
        private DiskArchive(Path root){this.root=root;}
        private ExactRef store(String kind,byte[] raw){
            try{Path file=root.resolve(kind+"-"+DriverJson.sha256(raw)+".bin");
                if(Files.exists(file))assertArrayEquals(raw,Files.readAllBytes(file));else Files.write(file,raw,StandardOpenOption.CREATE_NEW);
                return new ExactRef(file.toString(),raw.length,DriverJson.sha256(raw));
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private byte[] read(ExactRef reference){
            assertEquals(root,Path.of(reference.path()).getParent());
            try{byte[] raw=Files.readAllBytes(Path.of(reference.path()));assertEquals(reference.bytes(),raw.length);assertEquals(reference.sha256(),DriverJson.sha256(raw));return raw;}
            catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        @Override public ExactRef preserveMaterial(RawJson raw){return store("material",raw.bytes());}
        @Override public RawJson loadMaterial(ExactRef reference){return new RawJson(read(reference));}
        @Override public RawJson loadFullMaterial(ExactRef reference){
            assertEquals(root.resolve("material-"+reference.sha256()+".bin"),Path.of(reference.path()));
            assertTrue(reference.bytes()>0&&reference.bytes()<=RawJson.MAXIMUM_BYTES);
            try(var input=Files.newInputStream(Path.of(reference.path()))){
                byte[] raw=input.readNBytes(Math.toIntExact(reference.bytes())+1);
                assertEquals(reference.bytes(),raw.length);assertEquals(reference.sha256(),DriverJson.sha256(raw));
                return RawJson.fullMaterial(raw);
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        @Override public ExactRef materialReferenceOf(RawJson raw){ExactRef ref=store("material",raw.bytes());assertArrayEquals(raw.bytes(),read(ref));return ref;}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame raw){return store("native",raw.originalPacket());}
        @Override public byte[] loadNativeFrame(ExactRef reference){return read(reference);}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome raw){
            byte[] bytes=raw instanceof NativeActionPort.Unknown unknown?unknown.originalRequestPacket():assertInstanceOf(NativeActionPort.AckReceived.class,raw).originalPacket();
            ExactRef ref=store("dispatch",bytes);dispatches.putIfAbsent(ref,raw);assertEquals(raw,dispatches.get(ref));return ref;
        }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef reference){read(reference);return java.util.Objects.requireNonNull(dispatches.get(reference));}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome raw){return preserve(raw);}
        @Override public ExactRef preserveRequest(NativeRequest raw){
            ObjectNode body=StrictJson.object().put("step",raw.step()).put("capability",raw.requiredCapability().orElse(""));body.set("additional",StrictJson.parse(raw.additionalFields().bytes()));
            ExactRef ref=store("request",StrictJson.canonical(body));requests.putIfAbsent(ref,raw);assertEquals(raw,requests.get(ref));return ref;
        }
        @Override public NativeRequest loadRequest(ExactRef reference){read(reference);return java.util.Objects.requireNonNull(requests.get(reference));}
        @Override public ExactRef requestReferenceOf(NativeRequest raw){return preserveRequest(raw);}
        @Override public ExactRef preserveReceipt(ActionReceipt raw){ExactRef ref=store("receipt",ActionReceiptCodec.encodeReceipt(raw,this));receipts.putIfAbsent(ref,raw);return ref;}
        @Override public ActionReceipt loadReceipt(ExactRef reference){read(reference);return java.util.Objects.requireNonNull(receipts.get(reference));}
        @Override public ExactRef receiptReferenceOf(ActionReceipt raw){ExactRef ref=store("receipt",ActionReceiptCodec.encodeReceipt(raw,this));assertEquals(raw,receipts.get(ref));return ref;}
        @Override public ExactRef preserveRead(PlanningReadReceipt raw){throw new UnsupportedOperationException("no event material read in pending fixture");}
        @Override public PlanningReadReceipt loadRead(ExactRef reference){throw new UnsupportedOperationException("no event material read in pending fixture");}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt raw){throw new UnsupportedOperationException("no event material read in pending fixture");}
        @Override public ExactRef preserveRecord(ActionRecord raw){throw new UnsupportedOperationException("no canonical writer in software fixture");}
        @Override public ActionRecord loadRecord(ExactRef reference){throw new UnsupportedOperationException("no canonical writer in software fixture");}
        @Override public ExactRef recordReferenceOf(ActionRecord raw){throw new UnsupportedOperationException("no canonical writer in software fixture");}
    }

    private static Original original(String name){return originals.stream().filter(v->v.name().equals(name)).findFirst().orElseThrow();}
    private static String nullableText(JsonNode value){return value==null||value.isNull()?null:value.textValue();}
    private static ObjectNode object(JsonNode value){assertInstanceOf(ObjectNode.class,value);return (ObjectNode)value;}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value,65536));}
    private static void same(JsonNode first,JsonNode second){assertEquals(RetainedJson.parse(StrictJson.canonical(first,65536)),RetainedJson.parse(StrictJson.canonical(second,65536)));}
    private record Produced(ActionReceipt receipt,Optional<NativeEffectEvidence.Original> material) { }
}
