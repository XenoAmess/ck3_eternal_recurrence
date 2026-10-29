package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.NativeActionSteps;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.events.PendingUiEvent;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.semantic.NativePendingInteraction;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Action;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import static org.junit.jupiter.api.Assertions.*;

/** Actual original producers -> installed family contracts/preparation -> owner result/serde.
 * The software frame fixtures grant no live Root/Ready/PendingUI authority. */
final class RootInteractionPublicStepProductsTest {
    private static final String QUERY="query-pending-character-interaction-context-v1";
    private static final int INSTANCE=-2130706399;
    private static final BigInteger PUBLIC=new BigInteger("9007199254740993");
    private static final Instant NOW=Instant.parse("2026-10-24T07:00:00Z"),DEADLINE=NOW.plusSeconds(60);
    private static final Set<String> CAPS=Set.of("game.command."+QUERY,
            "game.command.accept-pending-character-interaction","game.command.reject-pending-character-interaction",
            "game.command.acknowledge-pending-character-interaction");
    private static ObjectNode original;
    @TempDir Path temporary;
    @BeforeAll static void actualOriginalInputs()throws Exception {original=PendingUiEventOriginalTestInputs.load();}

    @Test void exactSelectorsExcludeEventsMarriageOrdinaryAndMalformedNearMatches() {
        assertTrue(RootInteractionPublicStepProducts.query(new OperationKey(QUERY)));
        for(Action action:Action.values())assertTrue(RootInteractionPublicStepProducts.action(new OperationKey(action.step())));
        for(String other:List.of("query-current-event-window-context-v1","select-event-option-1","select-event-option-01",
                "query-arrange-marriage-choices","arrange-marriage-1-2","query-character-interaction-ordinary-v1",
                "initiate-character-interaction-ordinary-v1","query-title-own-laws-v1-k_france","query-title-holder-v1-12",
                "block-pending-character-interaction",QUERY+"-1","accept-pending-character-interaction-1")) {
            assertFalse(RootInteractionPublicStepProducts.query(new OperationKey(other)),other);
            assertFalse(RootInteractionPublicStepProducts.action(new OperationKey(other)),other);
        }
        assertThrows(NullPointerException.class,()->RootInteractionPublicStepProducts.install(null));
    }

    @Test void exactNativeCapabilityPrecedesIdAndActualActionStepsPrecedeChannelValidation()throws Exception {
        var malformed=StrictJson.object();malformed.putObject("pending_character_interaction").put("instance_id",true)
                .put("sender_character_id",1001).put("auto_accept_notification",false);
        PublicServiceFailure missing=assertThrows(PublicServiceFailure.class,()->RootInteractionPublicStepProducts.queryRequest(
                caller(QUERY,new PublicPlanningCodec.RevisionMissing()),obj(malformed),Set.of(),PUBLIC));
        assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,missing.kind());
        assertThrows(PublicServiceFailure.class,()->RootInteractionPublicStepProducts.queryRequest(
                caller(QUERY,new PublicPlanningCodec.RevisionMissing()),obj(malformed),CAPS,PUBLIC));
        assertThrows(PublicServiceFailure.class,()->RootInteractionPublicStepProducts.actionRequest(
                caller(Action.REJECT.step(),new PublicPlanningCodec.RevisionMissing()),obj(malformed),Set.of(),PUBLIC));
        for(String field:List.of("instance_id","sender_character_id","auto_accept_notification")) {
            ObjectNode missingField=pendingSnapshot(false);((ObjectNode)missingField.get("pending_character_interaction")).remove(field);
            assertThrows(PublicServiceFailure.class,()->query(missingField));
            ObjectNode nullField=pendingSnapshot(false);((ObjectNode)nullField.get("pending_character_interaction")).putNull(field);
            assertThrows(PublicServiceFailure.class,()->query(nullField));
        }
        for(JsonNode wrong:List.of(StrictJson.parse("true".getBytes(StandardCharsets.UTF_8)),com.fasterxml.jackson.databind.node.DecimalNode.valueOf(new java.math.BigDecimal("1.0")),
                StrictJson.parse("\"1\"".getBytes(StandardCharsets.UTF_8)),StrictJson.parse("2147483648".getBytes(StandardCharsets.UTF_8)),StrictJson.parse("-1".getBytes(StandardCharsets.UTF_8)))) {
            var bad=pendingSnapshot(false);((ObjectNode)bad.get("pending_character_interaction")).set("instance_id",wrong);
            assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,assertThrows(PublicServiceFailure.class,()->query(bad)).kind());
        }
        for(int exact:List.of(Integer.MIN_VALUE,0,Integer.MAX_VALUE)) {
            var bounded=pendingSnapshot(false);((ObjectNode)bounded.get("pending_character_interaction")).put("instance_id",exact);
            assertEquals(exact,query(bounded).instance().value());
        }
        for(String absent:List.of("missing","null")) {
            var bad=pendingSnapshot(false);if(absent.equals("missing"))bad.remove("pending_character_interaction");else bad.putNull("pending_character_interaction");
            assertThrows(PublicServiceFailure.class,()->query(bad));
        }
        for(PublicPlanningCodec.Revision revision:List.of(new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.RevisionNull(),new PublicPlanningCodec.RevisionValue(PUBLIC))) {
            for(Action action:Action.values()) {
                var step=caller(action.step(),revision);var snapshot=obj(pendingSnapshot(action==Action.ACKNOWLEDGE));
                var translated=RootInteractionPublicStepProducts.actionRequest(step,snapshot,Set.of(step.step()),PUBLIC);
                assertEquals(action,translated.action());assertEquals(Optional.of(new PendingId(INSTANCE)),translated.requestedInstance());
                var wire=PendingInteractionPublicCodec.encodeRequest(translated);
                assertEquals(translated,translated instanceof PendingInteractionPublicCodec.Reply
                        ?PendingInteractionPublicCodec.decodeReply(new PublicBindings.Value(wire))
                        :PendingInteractionPublicCodec.decodeAcknowledge(new PublicBindings.Value(wire)));
                assertEquals(step,PublicPlanningCodec.decodeExecute(new PublicBindings.Value(PublicPlanningCodec.encodeExecute(step))));
            }
        }
        assertThrows(PublicServiceFailure.class,()->RootInteractionPublicStepProducts.actionRequest(
                caller(Action.ACKNOWLEDGE.step(),new PublicPlanningCodec.RevisionMissing()),obj(pendingSnapshot(false)),Set.of(new OperationKey(Action.ACKNOWLEDGE.step())),PUBLIC));
        assertThrows(PublicServiceFailure.class,()->RootInteractionPublicStepProducts.actionRequest(
                caller(Action.REJECT.step(),new PublicPlanningCodec.RevisionMissing()),obj(pendingSnapshot(true)),Set.of(new OperationKey(Action.REJECT.step())),PUBLIC));
        assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,assertThrows(PublicServiceFailure.class,()->RootInteractionPublicStepProducts.queryRequest(
                caller(QUERY,new PublicPlanningCodec.RevisionValue(PUBLIC.subtract(BigInteger.ONE))),obj(pendingSnapshot(false)),CAPS,PUBLIC)).kind());
        var zero=caller(QUERY,new PublicPlanningCodec.RevisionValue(BigInteger.ZERO));
        assertEquals(zero,PublicPlanningCodec.decodeExecute(new PublicBindings.Value(PublicPlanningCodec.encodeExecute(zero))));
        assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,assertThrows(PublicServiceFailure.class,
                ()->RootInteractionPublicStepProducts.queryRequest(zero,obj(pendingSnapshot(false)),CAPS,PUBLIC)).kind());
        for(String bad:List.of("{\"step\":\""+QUERY+"\",\"expected_revision\":true}","{\"step\":\""+QUERY+"\",\"expected_revision\":1.0}",
                "{\"step\":\""+QUERY+"\",\"expected_revision\":9007199254740993}","{\"step\":\""+QUERY+"\",\"expected_revision\":\"01\"}",
                "{\"step\":\""+QUERY+"\",\"interaction_instance_id\":1}"))
            assertThrows(IllegalArgumentException.class,()->PublicPlanningCodec.decodeExecute(new PublicBindings.Value(new RawJson(bad.getBytes(StandardCharsets.UTF_8)))));
    }

    @Test void actualPendingNativeReadContractAndFullOwnerFormatterRetainOriginalBodyAndMirrors()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("actual-query"),16*1024*1024)) {
            disk.writer.locked(same->{
                var fixture=new PendingUiEventPreparationTest.Inputs(disk,disk.archive.withSession(same),same);
                for(String name:List.of("normal","notification")) {
                    ObjectNode row=originalPending(name);var current=fixture.pending(row);
                    Context context=new RootInteractionContextProjection(Build.WANDERER6).project(current.frame(),DEADLINE);
                    AtomicInteger reads=new AtomicInteger();
                    PlanningReadPort actualReads=new PlanningReadPort(){
                        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                            reads.incrementAndGet();try{return fixture.read(current,contract,request,(ObjectNode)row.get("query").deepCopy());}
                            catch(IOException failure){throw new UncheckedIOException(failure);}
                        }
                    };
                    var facade=facade(disk.pin,actualReads);
                    var caller=caller(QUERY,new PublicPlanningCodec.RevisionValue(PUBLIC));
                    var request=RootInteractionPublicStepProducts.queryRequest(caller,current.frame().semantic(),CAPS,PUBLIC);
                    var typed=typedPending(facade.queryPendingCharacterInteractionContextV1(context,request.instance()));
                    assertEquals(1,reads.get());assertEquals(typed.value(),PendingInteractionContracts.pending(disk.pin).replay(typed.receipt()));
                    var outbound=typed.receipt().original().outbound().orElseThrow();
                    var sent=NativeWire.decodeExecuteRequest(outbound.originalPacket());
                    assertEquals(QUERY,sent.step());assertEquals(Optional.of(BigInteger.valueOf(41)),sent.expectedRevision());
                    assertEquals(INSTANCE,DriverJson.toNode(DriverJson.object(sent.normalizedAdditionalFields().value(),65536)).path("pending_interaction_id").intValue());
                    var result=InteractionDirectPublicCodec.encode(InteractionDirectPublicCodec.pending(typed,context,current.frame()));
                    var publicRow=tree(result);var inner=publicRow.path("pending_character_interaction_context");
                    for(String key:List.of("definition","roles","target","send_options","routing","deadline","auto_accept","legality","terms","readiness","provenance"))
                        assertEquals(inner.get(key),publicRow.get(key),key);
                    assertEquals(PUBLIC.toString(),publicRow.path("binding").path("revision").textValue());
                    assertEquals("41",publicRow.path("binding").path("native_revision").textValue());
                    assertEquals(INSTANCE,publicRow.path("binding").path("pending_interaction_id").intValue());
                    assertEquals(publicRow,tree(new RawJson(DriverJson.encodeNode(publicRow))));
                    assertEquals(typed.receipt(),fixture.archive.loadRead(typed.originalReceipt()));
                }
                return null;
            });
        }
    }

    @Test void actualExplicitCommandNativePacketIndependentAfterAndOwnerResultRoundtripAllThreeActions()throws Exception {
        var oracleCases=StrictJson.object().putArray("cases");var completeJavaMaterials=new ArrayList<RawJson>();
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("actual-replies"),24*1024*1024)) {
            disk.writer.locked(same->{
                var fixture=new PendingUiEventPreparationTest.Inputs(disk,disk.archive.withSession(same),same);
                for(Action action:Action.values()) {
                    var row=originalPending(action==Action.ACKNOWLEDGE?"notification":"normal");
                    var current=fixture.pending(row);var after=fixture.next(current);Context context=new RootInteractionContextProjection(Build.WANDERER6).project(current.frame(),DEADLINE);
                    var request=RootInteractionPublicStepProducts.actionRequest(caller(action.step(),new PublicPlanningCodec.RevisionMissing()),
                            current.frame().semantic(),Set.of(new OperationKey(action.step())),PUBLIC);
                    var facade=facade(disk.pin,noReads());ActionCommand command=prepare(facade,context,request,"execute-"+action.name());
                    assertEquals(action.step(),command.operation().value());assertEquals(KnownPendingInteractionCommands.expected(context,action),command.expected());
                    var nativeRequest=KnownPendingInteractionEffects.preparation().prepare(command);
                    var sent=NativeWire.decodeExecuteRequest(NativeWire.execute("execute-native-"+action.name(),nativeRequest.step(),context.revision(),nativeRequest.additionalFields().bytes()));
                    assertEquals(action.step(),sent.step());assertEquals(INSTANCE,DriverJson.toNode(DriverJson.object(sent.normalizedAdditionalFields().value(),65536)).path("pending_interaction_id").intValue());
                    ActionReceipt receipt=observe(fixture,current,after,command,true);
                    assertTrue(receipt.applied().isPresent());assertFalse(receipt.eligibleAdvance());
                    var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
                    KnownPendingInteractionEffects.archivedVerifiers(disk.pin,loader).stream().filter(binding->binding.operation().equals(command.operation())).findFirst().orElseThrow().verifier().verify(null,receipt,fixture.archive);
                    var evidence=NativeEffectEvidence.load(receipt,fixture.archive,loader);
                    completeJavaMaterials.add(evidence.compatibleResult());
                    var oracleCase=oracleCases.addObject().put("step",action.step()).put("expected_revision",PUBLIC);
                    oracleCase.set("snapshot",DriverJson.toNode(current.frame().semantic()));
                    oracleCase.putArray("capabilities").addAll(CAPS.stream().sorted().map(com.fasterxml.jackson.databind.node.TextNode::valueOf).toList());
                    var result=PendingInteractionPublicCodec.result(receipt,fixture.archive,Optional.of(evidence.compatibleResult()),context.controls().pending(),action);
                    var publicRow=tree(result);assertEquals(PUBLIC.add(BigInteger.ONE).toString(),publicRow.path("revision").textValue());
                    assertEquals(action==Action.ACKNOWLEDGE?"acknowledged":action==Action.ACCEPT?"accepted":"rejected",publicRow.path("interaction_result").path("status").textValue());
                    assertTrue(publicRow.path("action_receipt").path("postcondition_verified").booleanValue());assertTrue(publicRow.path("remaining_pending_character_interaction").isNull());
                    assertEquals(receipt,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,fixture.archive),fixture.archive));
                    assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
                    assertEquals(publicRow,tree(new RawJson(DriverJson.encodeNode(publicRow))));
                    // The same native ACK with an independently later frame that still contains the
                    // original window remains unresolved; the owner never credits ACK as advancement.
                    var stillThere=fixture.later(current,false);ActionReceipt ackOnly=observe(fixture,current,stillThere,command,true);
                    assertFalse(ackOnly.settled());assertTrue(ackOnly.ack().isPresent());
                    var ackWire=tree(PendingInteractionPublicCodec.result(ackOnly,fixture.archive,Optional.empty(),context.controls().pending(),action));
                    assertFalse(ackWire.path("action_receipt").path("postcondition_verified").booleanValue());assertFalse(ackWire.path("replay_allowed").booleanValue());
                    assertTrue(ackWire.path(action==Action.ACKNOWLEDGE?"acknowledged":"accepted").isNull());
                }
                return null;
            });
            JsonNode sourceResults=python(EXECUTE_ORACLE,DriverJson.encodeNode(oracleCases));
            assertEquals(completeJavaMaterials.size(),sourceResults.size());
            for(int index=0;index<sourceResults.size();index++) {
                JsonNode pythonResult=sourceResults.get(index).path("result");assertTrue(pythonResult.isObject(),sourceResults.get(index).toString());
                ObjectNode material=tree(completeJavaMaterials.get(index)),projection=StrictJson.object();
                // Compare every field of the original driver's complete result, not an ACK subset.
                for(var field:pythonResult.properties()) {assertTrue(material.has(field.getKey()),field.getKey());projection.set(field.getKey(),material.get(field.getKey()));}
                assertEquals(obj(pythonResult),obj(projection));
            }
        }
    }

    @Test void actualOriginalExecuteFacadeAndPrimitiveProducerAgreeWithJavaRoutingAndFullResult()throws Exception {
        var cases=StrictJson.object().putArray("cases");
        for(Action action:Action.values()) {
            var row=cases.addObject().put("step",action.step()).put("expected_revision",PUBLIC);
            row.set("snapshot",pendingSnapshot(action==Action.ACKNOWLEDGE));row.putArray("capabilities").addAll(CAPS.stream().sorted().map(com.fasterxml.jackson.databind.node.TextNode::valueOf).toList());
        }
        var query=cases.addObject().put("step",QUERY).putNull("expected_revision");query.set("snapshot",pendingSnapshot(false));query.putArray("capabilities").add("game.command."+QUERY);
        var denied=cases.addObject().put("step",QUERY).putNull("expected_revision");denied.set("snapshot",pendingSnapshot(false));denied.putArray("capabilities");
        var wrong=cases.addObject().put("step",Action.ACKNOWLEDGE.step()).putNull("expected_revision");wrong.set("snapshot",pendingSnapshot(false));wrong.putArray("capabilities").add("game.command."+Action.ACKNOWLEDGE.step());
        var absentBeforeStale=cases.addObject().put("step",QUERY).put("expected_revision",7);absentBeforeStale.set("snapshot",pendingSnapshot(false));absentBeforeStale.putArray("capabilities");
        var malformedBeforeStale=cases.addObject().put("step",QUERY).put("expected_revision",7);var malformedSnapshot=pendingSnapshot(false);
        ((ObjectNode)malformedSnapshot.get("pending_character_interaction")).put("instance_id",true);malformedBeforeStale.set("snapshot",malformedSnapshot);malformedBeforeStale.putArray("capabilities").add("game.command."+QUERY);
        JsonNode produced=python(EXECUTE_ORACLE,DriverJson.encodeNode(cases));assertEquals(cases.size(),produced.size());
        for(int index=0;index<cases.size();index++) {
            var input=cases.get(index);var output=produced.get(index);String step=input.path("step").textValue();
            var snapshot=obj(input.get("snapshot"));Set<String> caps=new java.util.HashSet<>();input.path("capabilities").forEach(cap->caps.add(cap.textValue()));
            Set<OperationKey> actualSteps=NativeActionSteps.candidates(new NativeActionSteps.Input(caps,snapshot,List.of(),Set.of())).stream().map(OperationKey::new).collect(java.util.stream.Collectors.toUnmodifiableSet());
            var caller=caller(step,input.path("expected_revision").isNull()?new PublicPlanningCodec.RevisionNull():new PublicPlanningCodec.RevisionValue(input.path("expected_revision").bigIntegerValue()));
            if(output.has("error")) {
                if(step.equals(QUERY))assertEquals(output.path("error").textValue(),assertThrows(PublicServiceFailure.class,()->RootInteractionPublicStepProducts.queryRequest(caller,snapshot,caps,PUBLIC)).kind().pythonClassName());
                else assertEquals(output.path("error").textValue(),assertThrows(PublicServiceFailure.class,()->RootInteractionPublicStepProducts.actionRequest(caller,snapshot,actualSteps,PUBLIC)).kind().pythonClassName());
                assertEquals(0,output.path("calls").intValue());continue;
            }
            assertEquals(1,output.path("calls").intValue());
            if(step.equals(QUERY)) {
                var request=RootInteractionPublicStepProducts.queryRequest(caller,snapshot,caps,PUBLIC);
                assertEquals(request.instance().value(),output.path("pending_id").intValue());
            }else {
                var request=RootInteractionPublicStepProducts.actionRequest(caller,snapshot,actualSteps,PUBLIC);
                assertEquals(request.action().step(),output.path("step").textValue());
                var material=output.path("result");assertEquals(INSTANCE,material.path("interaction_result").path("instance_id").intValue());
                assertEquals(1001,material.path("interaction_result").path("sender_character_id").intValue());
                assertTrue(material.path("remaining_pending_character_interaction").isNull());assertTrue(material.path("paused").booleanValue());
                assertEquals(PUBLIC.add(BigInteger.ONE),material.path("revision").bigIntegerValue());
                assertEquals(request.action()==Action.ACKNOWLEDGE?"acknowledged":request.action()==Action.ACCEPT?"accepted":"rejected",material.path("interaction_result").path("status").textValue());
                // Exact source helper: ordinary replies have no extra primitive fields; ACK carries
                // its signed native instance. Java's sole receiver binds that instance on all replies.
                if(request.action()==Action.ACKNOWLEDGE)assertEquals(INSTANCE,output.path("primitive_fields").path("pending_interaction_id").intValue());
                else assertTrue(output.path("primitive_fields").isNull());
            }
        }
    }

    @Test void actualUnknownRetainsOriginalAcceptWhenCallerNowRequestsRejectWithoutAnotherPreparation()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("retain-unknown"),16*1024*1024)) {
            disk.writer.locked(same->{
                var fixture=new PendingUiEventPreparationTest.Inputs(disk,disk.archive.withSession(same),same);
                var current=fixture.pending(originalPending("normal"));Context context=new RootInteractionContextProjection(Build.WANDERER6).project(current.frame(),DEADLINE);
                ActionCommand command=prepare(facade(disk.pin,noReads()),context,
                        RootInteractionPublicStepProducts.actionRequest(caller(Action.ACCEPT.step(),new PublicPlanningCodec.RevisionMissing()),current.frame().semantic(),Set.of(new OperationKey(Action.ACCEPT.step())),PUBLIC),"original-accept");
                var later=fixture.later(current,false);ActionReceipt unknown=observe(fixture,current,later,command,false);
                assertFalse(unknown.settled());assertFalse(unknown.ack().isPresent());
                Context actualLater=new RootInteractionContextProjection(Build.WANDERER6).project(later.frame(),DEADLINE);
                var requested=RootInteractionPublicStepProducts.actionRequest(caller(Action.REJECT.step(),new PublicPlanningCodec.RevisionNull()),
                        later.frame().semantic(),Set.of(new OperationKey(Action.REJECT.step())),PUBLIC.add(BigInteger.ONE));
                var retained=KnownInteractionsRuntimeInstaller.retainedPending(List.of(unknown),actualLater).orElseThrow();
                assertEquals(unknown,retained);assertArrayEquals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(retained.command()));
                var response=tree(PendingInteractionPublicCodec.result(retained,fixture.archive,Optional.empty(),actualLater.controls().pending(),requested.action()));
                assertEquals(Action.ACCEPT.step(),response.path("action_receipt").path("original_step").textValue());
                assertEquals(Action.REJECT.step(),response.path("requested_step").textValue());assertTrue(response.path("accepted").isNull());
                assertFalse(response.path("action_receipt").path("native_ack_received").booleanValue());assertFalse(response.path("replay_allowed").booleanValue());
                assertEquals(retained,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(retained,fixture.archive),fixture.archive));
                assertThrows(IllegalArgumentException.class,()->KnownInteractionsRuntimeInstaller.retainedPending(List.of(unknown,unknown),actualLater));
                return null;
            });
        }
    }

    private static PlanningReadResult.Known<PendingContext> typedPending(PlanningReadResult<PendingContext> result) {
        if(result instanceof PlanningReadResult.Known<PendingContext> actual)return actual;
        throw new AssertionError("actual pending native query unexpectedly unavailable: "+result);
    }
    private static InteractionDirectPublicCodec.PendingQuery query(ObjectNode snapshot)throws IOException {
        return RootInteractionPublicStepProducts.queryRequest(caller(QUERY,new PublicPlanningCodec.RevisionMissing()),obj(snapshot),CAPS,PUBLIC);
    }
    private static PublicPlanningCodec.ExecuteRequest caller(String step,PublicPlanningCodec.Revision expected) {
        return new PublicPlanningCodec.ExecuteRequest(new OperationKey(step),expected,new PublicPlanningCodec.FrameMissing());
    }
    private static ObjectNode pendingSnapshot(boolean notification) {
        var row=StrictJson.object().put("snapshot_id","native:41").put("revision",PUBLIC).put("native_revision",41).put("paused",true).putNull("active_event");
        row.putArray("active_wars");row.putArray("player_armies");
        row.putObject("pending_character_interaction").put("instance_id",INSTANCE).put("sender_character_id",1001).put("auto_accept_notification",notification).put("source","native");
        return row;
    }
    private static ObjectNode originalPending(String name) {
        for(JsonNode row:original.path("pending"))if(name.equals(row.path("name").textValue()))return (ObjectNode)row.deepCopy();
        throw new AssertionError("original pending fixture absent: "+name);
    }
    private static OpportunityJson.Obj obj(JsonNode value){return DriverJson.object(DriverJson.encodeNode(value),1<<20);}
    private static RawJson raw(JsonNode value){return new RawJson(DriverJson.encodeNode(value));}
    private static ObjectNode tree(RawJson value){return (ObjectNode)DriverJson.toNode(DriverJson.object(value.bytes(),1<<20));}
    private static PlanningReadPort noReads() {
        return new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("explicit pending reply has no supplementary policy READ");}};
    }
    private static InteractionCapabilities facade(ExactRef source,PlanningReadPort actualReads) {
        var sources=new InteractionCapabilities.Sources(source,source,source,source,source,source,source,source,source,source);
        var definitions=new InteractionCapabilities.Installation(sources,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),new InteractionCapabilities.RootHeirSource(){
            @Override public PlanningReadResult<HeirSubject> read(Context frame){throw new AssertionError("pending operation cannot read the unrelated heir family");}
            @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context frame){throw new AssertionError("pending operation cannot read the unrelated heir family");}
        });
        ActionCoordinatorPort actions=new ActionCoordinatorPort(){
            @Override public ActionReceipt execute(ActionCommand command){throw new AssertionError("only the actual Root coordinator may dispatch after preparation returns");}
            @Override public ActionReceipt reconcile(String id){throw new AssertionError("existing UNKNOWN is retained, never reconciled by this adapter");}
        };
        return new InteractionCapabilities(definitions,actualReads,actions);
    }
    private static ActionCommand prepare(InteractionCapabilities facade,Context actual,PendingInteractionPublicCodec.Request requested,String id) {
        var action=new ActionContext(actual,id,KnownPendingInteractionCommands.expected(actual,requested.action()),
                new Claims(Set.of(),Set.of(),Set.of(actual.actor(),BigInteger.valueOf(actual.controls().pending().sender().value())),Set.of("foreground-window")));
        return requested instanceof PendingInteractionPublicCodec.Reply reply
                ?facade.prepareReplyPendingCharacterInteraction(action,reply.accept(),reply.requestedInstance())
                :facade.prepareAcknowledgePendingCharacterInteraction(action,((PendingInteractionPublicCodec.Acknowledge)requested).instance());
    }

    /** The real observer consumes independently assembled original before/after packets and the sole
     * strict native return. This software domain replay is deliberately separate from Root qualification. */
    private static ActionReceipt observe(PendingUiEventPreparationTest.Inputs fixture,PendingUiEvent.Current current,
            PendingUiEvent.Current after,ActionCommand command,boolean acknowledged)throws IOException {
        var archive=fixture.archive;var nativeRequest=KnownPendingInteractionEffects.preparation().prepare(command);
        var readContract=PendingInteractionContracts.pending(fixture.disk.pin);
        var context=new RootInteractionContextProjection(Build.WANDERER6).project(current.frame(),DEADLINE);
        var request=new PlanningReadRequest(current.frame().identity(),current.frame().source(),current.frame().sessionId(),readContract.operation(),PendingInteractionReadArguments.current(context),DEADLINE);
        var source=originalPending(current.frame().semantic().get("pending_character_interaction") instanceof OpportunityJson.Obj pending
                &&pending.get("auto_accept_notification") instanceof OpportunityJson.Bool value&&value.value()?"notification":"normal");
        var read=fixture.read(current,readContract,request,(ObjectNode)source.get("query").deepCopy());
        var observedKnown=new DriverSnapshotFacts.Known(current.known().driver(),current.known().stamp(),current.known().originalHistoryBasis(),current.known().actionRows(),current.known().auxiliary(),current.known().loop(),Optional.of(current.full().facts()));
        ExactRef semantic=archive.preserveMaterial(new RawJson(DriverJson.encode(current.frame().semantic()))),stamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(current.frame(),observedKnown)));
        var semanticEvidence=new SemanticEvidence(current.frame().identity(),semantic,current.frame().originalEvidence(),stamp,current.originalDriver(),current.frame().observedAt());
        ExactRef hello=read.receipt().before().binding().capabilityEvidence(),capabilities=archive.preserveMaterial(raw(StrictJson.object().put("software_only",true)));
        String authority="explicit-software-execute-pending";
        var originals=new RootGuardEvidence.PhysicalReadOriginals(current.frame(),semanticEvidence,hello,hello,current.qualifiedCause(),capabilities);
        ExactRef basis=RootGuardEvidence.preservePhysicalRead(originals,command.operation(),authority,archive,fixture.same.head());
        var guard=new GuardEvidence(command.before(),command.source(),command.sessionId(),current.frame().connectionGeneration(),command.operation(),current.frame().originalEvidence(),hello,authority,current.frame().observedAt(),DEADLINE,List.of(basis));
        var attempt=new ActionState.Attempt("actual-software-"+command.actionId(),NOW,guard,nativeRequest);
        byte[] outbound=NativeWire.execute(attempt.requestId(),nativeRequest.step(),command.before().frame().identity().nativeRevision(),nativeRequest.additionalFields().bytes());
        NativeActionPort.DispatchOutcome dispatch;
        if(acknowledged) {
            var token=StrictJson.object().put("step",nativeRequest.step()).put("accepted",true).put("status","submitted");
            var returned=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",attempt.requestId()).put("ok",true);returned.set("result",token);
            dispatch=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(raw(token)),raw(returned),NativeWire.packet(DriverJson.encodeNode(returned)),Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(),outbound)));
        }else dispatch=new NativeActionPort.Unknown(attempt.requestId(),"software lost actual return packet",outbound,Optional.empty());
        archive.preserve(dispatch);var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var snapshots=new NativeEffectSnapshots(()->{throw new AssertionError("software original after port must not resolve a live native endpoint");},archive,loader,
                (retained,deadline)->{assertEquals(command,retained);return Optional.of(after.frame());});
        var custody=new PrisonerNativeQueries(fixture.disk.pin,(ordinal,retained,arguments)->{throw new AssertionError("explicit reply must never query an unrelated prisoner ordinal");});
        var effects=new KnownPendingInteractionEffects(snapshots,noReads(),custody.contract(0));
        var projected=effects.observe(command,attempt,dispatch);
        ActionState state=projected.result() instanceof ActionPorts.EffectObserved observed
                ?new ActionState.Settled(attempt,dispatch,new ActionState.Applied(observed.observation()))
                :dispatch instanceof NativeActionPort.AckReceived ack?new ActionState.AckReceived(attempt,ack)
                :new ActionState.Unknown(Optional.of(attempt),Optional.of(dispatch),"original pending outcome unknown",List.of(after.frame().originalEvidence()));
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),state);archive.preserveReceipt(receipt);return receipt;
    }

    private static JsonNode python(String script,byte[] input)throws Exception {
        String executable=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(executable,"required xar.python missing; producer differential must not skip");assertFalse(executable.isBlank());
        assertNotNull(repository,"required xar.repository.root missing; producer differential must not skip");assertFalse(repository.isBlank());
        Path root=Path.of(repository).toRealPath();
        var builder=new ProcessBuilder(executable,"-c",script).directory(root.toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY",root.toString());builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process child=builder.start();var output=java.util.concurrent.CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readNBytes((1<<20)+1);}catch(IOException failure){throw new UncheckedIOException(failure);}});
        try {
            child.getOutputStream().write(input);child.getOutputStream().close();
            assertTrue(child.waitFor(45,TimeUnit.SECONDS),"original execute producer timed out");
            byte[] bytes=output.get(5,TimeUnit.SECONDS);assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=1<<20);
            return StrictJson.parse(bytes,1<<20);
        }finally {if(child.isAlive())child.destroyForcibly();}
    }
    private static final String EXECUTE_ORACLE="""
        import copy,json,sys
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver,_action_steps
        rows=[]
        for case in json.load(sys.stdin):
            snapshot=copy.deepcopy(case['snapshot']);step=case['step'];caps=case['capabilities'];calls=[];primitive=[]
            driver=object.__new__(NativeHeadlessGameplayDriver)
            driver.command_timeout_seconds=0.01
            driver.capabilities=lambda:{'bridge_capabilities':caps,'action_steps':_action_steps(caps,pending_character_interaction=snapshot.get('pending_character_interaction'),paused=snapshot.get('paused'),active_wars=[],player_armies=[])}
            driver.take_snapshot=lambda:copy.deepcopy(snapshot)
            def query(pending_id,*,expected_revision=None):
                calls.append(('query',pending_id,expected_revision))
                return dict(pending_id=pending_id)
            driver.query_pending_character_interaction_context_v1=query
            def execute_primitive(requested,*,expected_revision=None,request_fields=None,required_capability=None):
                if requested not in driver.capabilities()['action_steps']:
                    return NativeHeadlessGameplayDriver._execute_primitive_step(driver,requested,expected_revision=expected_revision,required_capability=required_capability,request_fields=request_fields)
                assert required_capability is None
                assert expected_revision==snapshot['revision']
                primitive.append(copy.deepcopy(request_fields));calls.append(('action',requested,expected_revision))
                return dict(step=requested,accepted=True,status='submitted')
            driver._execute_primitive_step=execute_primitive
            changed=copy.deepcopy(snapshot);changed.update(snapshot_id='native:42',revision=snapshot['revision']+1,native_revision=42,pending_character_interaction=None,paused=True)
            def wait(current,predicate,*,timeout_seconds):
                assert predicate(changed)
                return copy.deepcopy(changed)
            driver._wait_for_snapshot=wait
            try:
                result=driver._execute_step_unrecorded(step,expected_revision=case['expected_revision'])
                row=dict(calls=len(calls),result=result)
                if step.startswith('query-'):row.update(pending_id=result['pending_id'])
                else:row.update(step=result['step'],primitive_fields=primitive[0])
                rows.append(row)
            except Exception as error:rows.append(dict(error=type(error).__name__,calls=len(calls)))
        print(json.dumps(rows,separators=(',',':'),allow_nan=False))
        """;
}
