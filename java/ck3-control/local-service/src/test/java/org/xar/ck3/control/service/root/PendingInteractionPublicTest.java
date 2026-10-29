package org.xar.ck3.control.service.root;

import org.xar.ck3.control.contracts.NativeCharacterId;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Action;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** Software original channel/instance producer -> same Facade/preparer/postcondition -> strict public consumer. No Game qualification. */
final class PendingInteractionPublicTest {
    @TempDir java.nio.file.Path temporary;
    private static final ExactRef SOURCE=new ExactRef("synthetic-public-pending-source",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z"),DEADLINE=NOW.plusSeconds(30);
    private static final int INSTANCE=-2130706399;
    private static Context context(boolean notification) { return context(notification,707L); }
    private static Context context(boolean notification,long actor) {
        return context(notification,actor,501);
    }
    private static Context context(boolean notification,long actor,int sender) {
        var before=new ObservationIdentity("synthetic-machine",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(41),BigInteger.valueOf(24000)),"synthetic-before",new BigInteger("9007199254740993"),"synthetic-episode"),1);
        return new Context(before,new G2Source(before.machineId(),NOW.toString(),"1.20.0.4@sha256:"+Build.CROZIER4.sha256(),SOURCE),"synthetic-session",BigInteger.ONE,Build.CROZIER4,DEADLINE,
                new ControlFrame(true,true,true,1,707L,actor,"synthetic-episode",false,new PendingSummary(new PendingId(INSTANCE),NativeCharacterId.of(sender),notification),null,List.of()));
    }
    private static Context projectedContext(boolean notification,int actor,int sender) {
        Context seed=context(notification,actor,sender);
        ObjectNode semantic=StrictJson.object().put("paused",true).put("map_ready",true).put("speed",1)
                .put("local_player_id",707).put("episode_character_id",actor).put("episode_run_id",seed.before().frame().episodeRunId());
        semantic.putNull("active_event");
        semantic.set("pending_character_interaction",org.xar.ck3.control.contracts.semantic.NativePendingInteraction.normalize(
                StrictJson.object().put("instance_id",INSTANCE).put("sender_character_id",sender).put("auto_accept_notification",notification)));
        semantic.putObject("played_character").put("character_id",actor).put("alive",true).putNull("betrothed_id").putArray("spouse_ids");
        semantic.putObject("diagnostics").putObject("hello").put("expected_ck3_version",Build.CROZIER4.version()).put("expected_ck3_sha256",Build.CROZIER4.sha256());
        var raw=new org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete(seed.before(),seed.source(),seed.sessionId(),seed.connectionGeneration(),
                DriverJson.object(DriverJson.encodeNode(semantic),65536),SOURCE,NOW,"b".repeat(64));
        Context projected=new RootInteractionContextProjection(Build.CROZIER4).project(raw,DEADLINE);
        RootInteractionContextProjection.requireExact(raw,projected);return projected;
    }
    private static InteractionCapabilities facade() {
        var sources=new InteractionCapabilities.Sources(SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE);
        var definitions=new InteractionCapabilities.Installation(sources,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),new InteractionCapabilities.RootHeirSource(){
            @Override public PlanningReadResult<HeirSubject> read(Context context){throw new AssertionError("no heir query in pending preparation");}
            @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context context){throw new AssertionError("no heir query in pending preparation");}
        });
        PlanningReadPort reads=new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("no read in pure pending preparation");}};
        ActionCoordinatorPort actions=new ActionCoordinatorPort(){@Override public ActionReceipt execute(ActionCommand command){throw new AssertionError("preparation must not submit while Root holds the frame lease");}@Override public ActionReceipt reconcile(String id){throw new AssertionError("unknown public request must not reconcile or replay");}};
        return new InteractionCapabilities(definitions,reads,actions);
    }
    private static ActionCommand command(Context context,Action action) { return command(context,action,"synthetic-pending-"+action.name()); }
    private static ActionCommand command(Context context,Action action,String actionId) {
        var characters=new java.util.HashSet<BigInteger>();characters.add(context.actor());characters.add(context.controls().pending().sender().asBigInteger());
        var input=new ActionContext(context,actionId,KnownPendingInteractionCommands.expected(context,action),new Claims(Set.of(),Set.of(),characters,Set.of("foreground-window")));
        return action==Action.ACKNOWLEDGE?facade().prepareAcknowledgePendingCharacterInteraction(input,new PendingId(INSTANCE)):
                facade().prepareReplyPendingCharacterInteraction(input,action==Action.ACCEPT,Optional.of(new PendingId(INSTANCE)));
    }
    private static ObservationIdentity after(Context before) {
        var frame=before.before().frame();return new ObservationIdentity(before.before().machineId(),before.before().game(),
                new ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(frame.identity().player(),frame.identity().nativeRevision().add(BigInteger.ONE),frame.identity().dateRaw()),"synthetic-after",frame.revision().add(BigInteger.ONE),frame.episodeRunId()),1);
    }
    private static OpportunityJson.Obj snapshot(ObservationIdentity frame,boolean pending,boolean notification) {
        return snapshot(frame,pending,notification,501);
    }
    private static OpportunityJson.Obj snapshot(ObservationIdentity frame,boolean pending,boolean notification,int sender) {
        ObjectNode row=StrictJson.object().put("snapshot_id",frame.frame().snapshotId()).put("episode_run_id",frame.frame().episodeRunId())
                .put("revision",frame.frame().revision()).put("native_revision",frame.frame().identity().nativeRevision()).put("date_raw",frame.frame().identity().dateRaw()).put("paused",true);
        row.putObject("played_character").put("character_id",frame.frame().identity().player());
        if(pending)row.putObject("pending_character_interaction").put("instance_id",INSTANCE).put("sender_character_id",sender).put("auto_accept_notification",notification);else row.putNull("pending_character_interaction");
        return DriverJson.object(DriverJson.encodeNode(row),65536);
    }
    private record Produced(ActionReceipt receipt,RawJson material,PendingSummary pending) { }
    private static Produced applied(Action action) {
        return applied(context(action==Action.ACKNOWLEDGE),action);
    }
    private static Produced applied(Context before,Action action) {
        ActionCommand command=command(before,action);var next=after(before);
        ObjectNode plan=object(DriverJson.toNode(command.arguments()).get("known_pending_plan"));
        var typed=KnownPendingInteractionPlanCodec.decode(plan.get("java_policy_plan"));
        RawJson token=raw("{\"step\":\""+action.step()+"\",\"accepted\":true,\"status\":\"submitted\"}");
        var verified=KnownPendingInteractionPostcondition.verify(new KnownPendingInteractionPostcondition.Input(typed,before.before(),next,
                snapshot(before.before(),true,action==Action.ACKNOWLEDGE,before.controls().pending().sender().value()),snapshot(next,false,action==Action.ACKNOWLEDGE,before.controls().pending().sender().value()),token,Optional.empty()));
        assertTrue(verified.verified(),verified.missing().toString());
        var nativeRequest=KnownPendingInteractionEffects.preparation().prepare(command,"synthetic-native-request");
        assertEquals(INSTANCE,DriverJson.toNode(DriverJson.object(nativeRequest.additionalFields().bytes(),65536)).get("pending_interaction_id").intValue());
        try {
            byte[] packet=org.xar.ck3.control.nativebridge.NativeWire.execute("synthetic-native-request",nativeRequest.step(),before.revision(),nativeRequest.additionalFields().bytes());
            var framed=java.nio.ByteBuffer.wrap(packet).order(java.nio.ByteOrder.LITTLE_ENDIAN);assertEquals(packet.length-4,framed.getInt());byte[] payload=new byte[packet.length-4];framed.get(payload);
            ObjectNode sent=object(DriverJson.toNode(DriverJson.object(payload,65536)));assertEquals(BigInteger.valueOf(41),sent.get("expected_revision").bigIntegerValue());
            assertEquals(INSTANCE,sent.get("pending_interaction_id").intValue());
        }catch(java.io.IOException invalid){throw new AssertionError("actual pending wire serializer rejected the original prepared request",invalid);}
        GuardEvidence guard=new GuardEvidence(before.before(),before.source(),before.sessionId(),BigInteger.ONE,command.operation(),SOURCE,SOURCE,"synthetic-pending-guard",NOW,DEADLINE);
        var attempt=new ActionState.Attempt("synthetic-native-request",NOW,guard,nativeRequest);
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(token),token,new byte[]{1});
        var observation=new ActionState.EffectObservation(next,before.source(),before.sessionId(),KnownPendingInteractionPostcondition.SCHEMA,verified.actual(),
                new ObservationProvenance.Push(next.frame().snapshotId(),next.frame().identity().nativeRevision(),SOURCE),NOW.plusSeconds(1),SOURCE,List.of());
        return new Produced(new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.Applied(observation))),
                new RawJson(DriverJson.encode(verified.compatibleResult())),before.controls().pending());
    }
    @Test void originalFacadePreparerAndIndependentVerifierServeBothReplyChoicesAndDistinctNotificationAck() {
        for(Action action:List.of(Action.ACCEPT,Action.REJECT,Action.ACKNOWLEDGE)) {
            Produced source=applied(action);var archive=new ReceiptArchive(source.receipt());
            RawJson result=PendingInteractionPublicCodec.result(source.receipt(),archive,Optional.of(source.material()),source.pending(),action);
            ObjectNode wire=object(DriverJson.toNode(DriverJson.object(result.bytes(),65536)));
            assertEquals(INSTANCE,wire.get("interaction_instance_id").intValue());assertEquals("9007199254740994",wire.get("revision").textValue());
            assertEquals(action==Action.ACKNOWLEDGE?"acknowledged":action==Action.ACCEPT?"accepted":"rejected",wire.path("interaction_result").path("status").textValue());
            assertTrue(wire.path("action_receipt").path("native_ack_received").booleanValue());assertTrue(wire.path("action_receipt").path("postcondition_verified").booleanValue());
            if(action==Action.ACKNOWLEDGE)assertTrue(wire.get("acknowledged").booleanValue());else assertEquals(action==Action.ACCEPT,wire.get("accepted").booleanValue());
            assertEquals(wire,DriverJson.toNode(DriverJson.object(DriverJson.encodeNode(wire),65536)));
        }
        Context notification=context(true);var ctx=new ActionContext(notification,"bad-channel",KnownPendingInteractionCommands.expected(notification,Action.REJECT),new Claims(Set.of(),Set.of(),Set.of(),Set.of()));
        assertThrows(IllegalArgumentException.class,()->facade().prepareReplyPendingCharacterInteraction(ctx,false,Optional.empty()));
    }
    @Test void strictCodecPreservesSignedIdsMissingNullAndExactDecimalRevisionAndRejectsWrongFieldTypes() {
        for(String document:List.of("{\"accept\":false}","{\"accept\":true,\"interaction_instance_id\":null,\"expected_revision\":null}",
                "{\"accept\":false,\"interaction_instance_id\":-2130706399,\"expected_revision\":\"18446744073709551615\"}")) {
            var decoded=PendingInteractionPublicCodec.decodeReply(new PublicBindings.Value(raw(document)));
            assertEquals(decoded,PendingInteractionPublicCodec.decodeReply(new PublicBindings.Value(PendingInteractionPublicCodec.encodeRequest(decoded))));
        }
        for(String bad:List.of("{}","{\"accept\":1}","{\"accept\":true,\"interaction_instance_id\":true}","{\"accept\":true,\"interaction_instance_id\":-1}",
                "{\"accept\":false,\"interaction_instance_id\":1.0}","{\"accept\":true,\"expected_revision\":9007199254740993}","{\"accept\":false,\"expected_revision\":\"01\"}",
                "{\"accept\":false,\"expected_revision\":\"18446744073709551616\"}","{\"accept\":false,\"option_number\":1}"))
            assertThrows(IllegalArgumentException.class,()->PendingInteractionPublicCodec.decodeReply(new PublicBindings.Value(raw(bad))));
        for(String bad:List.of("{}","{\"interaction_instance_id\":null}","{\"interaction_instance_id\":true}","{\"interaction_instance_id\":-1}"))
            assertThrows(IllegalArgumentException.class,()->PendingInteractionPublicCodec.decodeAcknowledge(new PublicBindings.Value(raw(bad))));
    }
    @Test void nativeAckAloneCannotClaimNotificationAdvancementAndUnknownIsRetainedAcrossNewRequestFrames() {
        Produced source=applied(Action.ACKNOWLEDGE);var settled=(ActionState.Settled)source.receipt().state();
        ActionReceipt ackOnly=new ActionReceipt(1,2,source.receipt().command(),source.receipt().bodySha256(),new ActionState.AckReceived(settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch()));
        ObjectNode wire=object(DriverJson.toNode(DriverJson.object(PendingInteractionPublicCodec.result(ackOnly,new ReceiptArchive(ackOnly),Optional.empty(),source.pending(),Action.ACKNOWLEDGE).bytes(),65536)));
        assertTrue(wire.path("action_receipt").path("native_ack_received").booleanValue());assertFalse(wire.path("action_receipt").path("postcondition_verified").booleanValue());
        assertTrue(wire.get("acknowledged").isNull());
        Context original=context(true);Context later=new Context(after(original),original.source(),original.sessionId(),original.connectionGeneration(),original.build(),original.deadline(),original.controls());
        assertEquals(Optional.of(ackOnly),KnownInteractionsRuntimeInstaller.retainedPending(List.of(ackOnly),later));
        assertEquals(new PendingId(INSTANCE),PendingInteractionPublicCodec.originalInstance(ackOnly.command()));
        var uncertainDispatch=new NativeActionPort.Unknown(settled.attempt().requestId(),"actual software unknown",new byte[]{1},Optional.empty());
        ActionReceipt unknown=new ActionReceipt(1,3,source.receipt().command(),source.receipt().bodySha256(),new ActionState.Unknown(Optional.of(settled.attempt()),Optional.of(uncertainDispatch),"actual software unknown",List.of(SOURCE)));
        assertEquals(Optional.of(unknown),KnownInteractionsRuntimeInstaller.retainedPending(List.of(unknown),later));
        assertThrows(IllegalArgumentException.class,()->KnownInteractionsRuntimeInstaller.retainedPending(List.of(unknown,ackOnly),later));
        ObjectNode unknownWire=object(DriverJson.toNode(DriverJson.object(PendingInteractionPublicCodec.result(unknown,new ReceiptArchive(unknown),Optional.empty(),source.pending(),Action.ACKNOWLEDGE).bytes(),65536)));
        assertFalse(unknownWire.path("action_receipt").path("native_ack_received").booleanValue());assertTrue(unknownWire.get("acknowledged").isNull());assertFalse(unknownWire.get("replay_allowed").booleanValue());
        Produced replySource=applied(Action.ACCEPT);var replySettled=(ActionState.Settled)replySource.receipt().state();
        var replyUnknown=new ActionReceipt(1,4,replySource.receipt().command(),replySource.receipt().bodySha256(),new ActionState.Unknown(Optional.of(replySettled.attempt()),Optional.empty(),"original accept remains unknown",List.of(SOURCE)));
        assertEquals(Optional.of(replyUnknown),KnownInteractionsRuntimeInstaller.retainedPending(List.of(replyUnknown),context(false)));
        ObjectNode changedRequest=object(DriverJson.toNode(DriverJson.object(PendingInteractionPublicCodec.result(replyUnknown,new ReceiptArchive(replyUnknown),Optional.empty(),replySource.pending(),Action.REJECT).bytes(),65536)));
        assertEquals(Action.REJECT.step(),changedRequest.get("requested_step").textValue());assertEquals(Action.ACCEPT.step(),changedRequest.path("action_receipt").path("original_step").textValue());assertTrue(changedRequest.get("accepted").isNull());
        assertThrows(IllegalArgumentException.class,()->PendingInteractionPublicCodec.result(ackOnly,new ReceiptArchive(ackOnly),Optional.of(source.material()),source.pending(),Action.ACKNOWLEDGE));
    }
    @Test void unknownPendingRetainsOnlyItsOriginalActorForLeftReplyAndNotification() {
        for(Action action:List.of(Action.REJECT,Action.ACKNOWLEDGE)) {
            Context original=context(action==Action.ACKNOWLEDGE),successor=context(action==Action.ACKNOWLEDGE,708L);
            ActionCommand predecessorCommand=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command(original,action)));
            ActionReceipt predecessorUnknown=new ActionReceipt(1,1,predecessorCommand,ActionCodec.bodySha256(predecessorCommand),
                    new ActionState.Unknown(Optional.empty(),Optional.empty(),"original predecessor response remains unknown",List.of(SOURCE)));
            assertEquals(original.before().game(),successor.before().game());assertEquals(original.source(),successor.source());
            assertEquals(original.sessionId(),successor.sessionId());assertEquals(original.controls().pending(),successor.controls().pending());
            assertNotEquals(original.actor(),successor.actor());
            assertTrue(KnownInteractionsRuntimeInstaller.retainedPending(List.of(predecessorUnknown),successor).isEmpty(),
                    "a predecessor UNKNOWN cannot claim the successor's current pending instance");
            assertEquals(Optional.of(predecessorUnknown),KnownInteractionsRuntimeInstaller.retainedPending(List.of(predecessorUnknown),original),
                    "the immutable original UNKNOWN still belongs to its actor and must not replay");
            ActionCommand successorCommand=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command(successor,action,"synthetic-successor-"+action.name())));
            assertEquals(successor.actor(),successorCommand.before().frame().identity().player());
            ActionReceipt successorUnknown=new ActionReceipt(1,2,successorCommand,ActionCodec.bodySha256(successorCommand),
                    new ActionState.Unknown(Optional.empty(),Optional.empty(),"original successor response remains unknown",List.of(SOURCE)));
            assertEquals(Optional.of(successorUnknown),KnownInteractionsRuntimeInstaller.retainedPending(List.of(predecessorUnknown,successorUnknown),successor));
            assertThrows(IllegalArgumentException.class,()->KnownInteractionsRuntimeInstaller.retainedPending(List.of(predecessorUnknown,successorUnknown,successorUnknown),successor));
            ObjectNode response=object(DriverJson.toNode(DriverJson.object(PendingInteractionPublicCodec.result(successorUnknown,
                    new ReceiptArchive(successorUnknown),Optional.empty(),successor.controls().pending(),action).bytes(),65536)));
            assertFalse(response.path("replay_allowed").booleanValue());assertFalse(response.path("action_receipt").path("postcondition_verified").booleanValue());
            assertTrue(response.get(action==Action.ACKNOWLEDGE?"acknowledged":"accepted").isNull());
        }
    }
    @Test void signedOriginalBothRolesAndFullPendingSurviveUnknownColdPublicResultWithoutReplay() {
        int[][] pairs={{Integer.MIN_VALUE,-2},{-2,Integer.MIN_VALUE},{0,Integer.MAX_VALUE},{Integer.MAX_VALUE,0}};
        for(int[] pair:pairs)for(Action action:List.of(Action.ACCEPT,Action.REJECT,Action.ACKNOWLEDGE)) {
            Context original=projectedContext(action==Action.ACKNOWLEDGE,pair[0],pair[1]);
            ActionCommand command=command(original,action,"signed-original-"+pair[0]+"-"+action.name());
            var claims=Set.of(BigInteger.valueOf(pair[0]),BigInteger.valueOf(pair[1]));
            assertEquals(claims,command.claims().characterIds());
            ActionCommand decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));assertEquals(command,decoded);
            var nativeRequest=KnownPendingInteractionEffects.preparation().prepare(decoded,"pure-original-preparation");
            assertEquals(INSTANCE,DriverJson.toNode(DriverJson.object(nativeRequest.additionalFields().bytes(),65536)).get("pending_interaction_id").intValue());
            var unknown=new ActionReceipt(1,1,decoded,ActionCodec.bodySha256(decoded),
                    new ActionState.Unknown(Optional.empty(),Optional.empty(),"original signed pending remains unknown",List.of(SOURCE)));
            byte[] bytes=ActionReceiptCodec.encodeReceipt(unknown,new ReceiptArchive(unknown));
            ActionReceipt cold=ActionReceiptCodec.decodeReceipt(bytes,new ReceiptArchive(unknown));
            assertEquals(unknown,cold);assertArrayEquals(bytes,ActionReceiptCodec.encodeReceipt(cold,new ReceiptArchive(cold)));
            assertEquals(claims,cold.command().claims().characterIds());assertEquals(original.actor(),cold.command().before().frame().identity().player());
            assertFalse(cold.settled());assertTrue(cold.applied().isEmpty());assertTrue(cold.ack().isEmpty());
            Context later=new Context(after(original),original.source(),original.sessionId(),original.connectionGeneration(),original.build(),original.deadline(),original.controls());
            assertEquals(Optional.of(cold),KnownInteractionsRuntimeInstaller.retainedPending(List.of(cold),later));
            var retained=new KnownInteractionsRuntimeInstaller.RetainedPending(cold,later.controls().pending(),action);
            ObjectNode result=object(DriverJson.toNode(DriverJson.object(PendingInteractionPublicCodec.result(retained.original(),
                    new ReceiptArchive(cold),Optional.empty(),retained.pending(),retained.requested()).bytes(),65536)));
            assertEquals(INSTANCE,result.get("interaction_instance_id").intValue());assertEquals(pair[1],result.get("sender_character_id").intValue());
            assertEquals(cold.bodySha256(),result.path("action_receipt").path("command_body_sha256").textValue());
            assertEquals(action.step(),result.path("action_receipt").path("original_step").textValue());
            assertEquals("pending_action_state_unknown",result.get("status").textValue());
            assertFalse(result.get("replay_allowed").booleanValue());assertFalse(result.path("action_receipt").path("native_ack_received").booleanValue());
            assertFalse(result.path("action_receipt").path("postcondition_verified").booleanValue());
            assertTrue(result.get(action==Action.ACKNOWLEDGE?"acknowledged":"accepted").isNull());
            Context successor=context(action==Action.ACKNOWLEDGE,pair[0]==0?17:0,pair[1]);
            assertTrue(KnownInteractionsRuntimeInstaller.retainedPending(List.of(cold),successor).isEmpty());
        }
    }
    @Test void signedBothOriginalRolesReachIndependentPendingAdvancementAndOriginalPublicMaterial() {
        int[][] pairs={{Integer.MIN_VALUE,-2},{-2,Integer.MIN_VALUE},{0,Integer.MAX_VALUE},{Integer.MAX_VALUE,0}};
        for(int[] pair:pairs)for(Action action:List.of(Action.ACCEPT,Action.REJECT,Action.ACKNOWLEDGE)) {
            Context c=projectedContext(action==Action.ACKNOWLEDGE,pair[0],pair[1]);Produced source=applied(c,action);
            ObjectNode result=object(DriverJson.toNode(DriverJson.object(PendingInteractionPublicCodec.result(source.receipt(),
                    new ReceiptArchive(source.receipt()),Optional.of(source.material()),source.pending(),action).bytes(),65536)));
            assertEquals(INSTANCE,result.get("interaction_instance_id").intValue());assertEquals(pair[1],result.get("sender_character_id").intValue());
            assertEquals(pair[1],result.path("interaction_result").path("sender_character_id").intValue());
            assertEquals(pair[0],source.receipt().command().before().frame().identity().player().intValueExact());
            assertTrue(result.path("action_receipt").path("postcondition_verified").booleanValue());
            assertFalse(result.path("replay_allowed").booleanValue());
            assertEquals(Set.of(BigInteger.valueOf(pair[0]),BigInteger.valueOf(pair[1])),source.receipt().command().claims().characterIds());
        }
    }
    @Test void signedUnknownOriginalRequestAndClaimsSurviveActualPhysicalArchiveColdLoad()throws Exception {
        Context c=projectedContext(false,Integer.MIN_VALUE,-2);ActionCommand command=command(c,Action.REJECT);
        NativeRequest request=KnownPendingInteractionEffects.preparation().prepare(command,"signed-original-request");
        GuardEvidence guard=new GuardEvidence(c.before(),c.source(),c.sessionId(),c.connectionGeneration(),command.operation(),SOURCE,SOURCE,"synthetic-signed-pending-guard",NOW,DEADLINE);
        var attempt=new ActionState.Attempt("signed-original-request",NOW,guard,request);
        var original=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.of(attempt),Optional.empty(),"original signed request outcome unavailable",List.of(SOURCE)));
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("signed-pending-cold"),8*1024*1024)) {
            ExactRef stored=disk.writer.locked(same->disk.archive.withSession(same).preserveReceipt(original));
            disk.writer.locked(same->{
                var coldArchive=new org.xar.ck3.control.continuity.writer.NativeOutcomeArchive(disk.store,disk.writer).withSession(same);
                ActionReceipt cold=coldArchive.loadReceipt(stored);assertEquals(original,cold);
                assertEquals(Set.of(BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(-2)),cold.command().claims().characterIds());
                var state=assertInstanceOf(ActionState.Unknown.class,cold.state());assertEquals(request,state.attempt().orElseThrow().preparedRequest());
                assertEquals(request,coldArchive.loadRequest(coldArchive.requestReferenceOf(request)));
                assertEquals(Optional.of(cold),KnownInteractionsRuntimeInstaller.retainedPending(List.of(cold),c));
                ObjectNode result=object(DriverJson.toNode(DriverJson.object(PendingInteractionPublicCodec.result(cold,coldArchive,Optional.empty(),c.controls().pending(),Action.REJECT).bytes(),65536)));
                assertEquals(-2,result.get("sender_character_id").intValue());assertEquals(INSTANCE,result.get("interaction_instance_id").intValue());
                assertFalse(result.get("replay_allowed").booleanValue());assertFalse(cold.settled());assertTrue(cold.ack().isEmpty());assertTrue(cold.applied().isEmpty());
                return null;
            });
            assertFalse(disk.guard.hasUnknownWrite());
        }
    }
    @Test void commandCharacterClaimsRequireCanonicalSignedStringsAndKeepOtherClaimDomains() {
        var c=projectedContext(false,Integer.MIN_VALUE,-2);var command=command(c,Action.REJECT);
        ObjectNode encoded=object(DriverJson.toNode(DriverJson.object(ActionCodec.encodeCommand(command),ActionCodec.MAX_COMMAND_BYTES)));
        assertEquals(List.of("-2147483648","-2"),java.util.stream.StreamSupport.stream(encoded.path("claims").get("character_ids").spliterator(),false).map(com.fasterxml.jackson.databind.JsonNode::textValue).toList());
        for(String token:List.of("\"-1\"","\"2147483648\"","\"4294967294\"","\"-2147483649\"","\"-0\"","\"+2\"","\"02\"","\"-02\"","\" -2\"","-2","0.0","true","null","{}")) {
            ObjectNode bad=encoded.deepCopy();ObjectNode claims=(ObjectNode)bad.get("claims");
            var value=DriverJson.toNode(DriverJson.object(("{\"value\":"+token+"}").getBytes(StandardCharsets.UTF_8),65536)).get("value");
            claims.putArray("character_ids").add(value);
            assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(DriverJson.encodeNode(bad)),token);
        }
        ObjectNode duplicate=encoded.deepCopy();((ObjectNode)duplicate.get("claims")).putArray("character_ids").add("-2").add("-2");
        assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(DriverJson.encodeNode(duplicate)));
        ObjectNode missing=encoded.deepCopy();((ObjectNode)missing.get("claims")).remove("character_ids");
        assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(DriverJson.encodeNode(missing)));
        for(String field:List.of("army_ids","ally_character_ids")) {
            ObjectNode bad=encoded.deepCopy();((ObjectNode)bad.get("claims")).putArray(field).add("-2");
            assertThrows(IllegalArgumentException.class,()->ActionCodec.decodeCommand(DriverJson.encodeNode(bad)));
        }
        BigInteger wide=BigInteger.ONE.shiftLeft(40);
        ActionCommand independent=new ActionCommand(command.actionId(),command.origin(),command.source(),command.sessionId(),command.operation(),command.arguments(),command.expectation(),new Claims(Set.of(wide),Set.of(wide),command.claims().characterIds(),command.claims().commitmentKeys()),command.deadline());
        assertEquals(independent,ActionCodec.decodeCommand(ActionCodec.encodeCommand(independent)));
    }
    @Test void originalPythonServiceProducerMatchesBothReplyBranchesAndNotificationAcknowledgement()throws Exception {
        String python=System.getProperty("xar.python"),repositoryProperty=System.getProperty("xar.repository.root");
        assertNotNull(python,"required xar.python property missing; original producer differential cannot skip");assertFalse(python.isBlank());
        assertNotNull(repositoryProperty,"required xar.repository.root property missing; original producer differential cannot skip");assertFalse(repositoryProperty.isBlank());
        String repository=java.nio.file.Path.of(repositoryProperty).toRealPath().toString();
        var cases=StrictJson.object().putArray("cases");var expected=new java.util.ArrayList<ObjectNode>();
        for(Action action:List.of(Action.ACCEPT,Action.REJECT,Action.ACKNOWLEDGE)) {
            Produced source=applied(action);Context before=context(action==Action.ACKNOWLEDGE);
            ObjectNode row=cases.addObject().put("kind",action==Action.ACKNOWLEDGE?"ack":"reply").put("accept",action==Action.ACCEPT).put("instance",INSTANCE);
            row.set("snapshot",DriverJson.toNode(snapshot(before.before(),true,action==Action.ACKNOWLEDGE)));row.set("material",DriverJson.toNode(DriverJson.object(source.material().bytes(),65536)));
            ObjectNode result=object(DriverJson.toNode(DriverJson.object(PendingInteractionPublicCodec.result(source.receipt(),new ReceiptArchive(source.receipt()),Optional.of(source.material()),source.pending(),action).bytes(),65536)));
            // Only the published wide roles change representation. Compare every original result field, including ACK/material flags.
            for(String field:List.of("revision","native_revision"))if(result.has(field))result.put(field,new BigInteger(result.get(field).textValue()));
            expected.add(result);
        }
        String script="""
            import copy,json,sys
            from xar_autoplayer.bridge.service import GameplayBridgeService
            steps=['accept-pending-character-interaction','reject-pending-character-interaction','acknowledge-pending-character-interaction']
            output=[]
            for case in json.load(sys.stdin):
                class Backend:
                    calls=[]
                    def snapshot(self): return copy.deepcopy(case['snapshot'])
                    def capabilities(self): return {'action_steps':steps}
                    def execute_step(self,step,expected_revision=None):
                        assert expected_revision==case['snapshot']['revision']
                        self.calls.append(step)
                        return copy.deepcopy(case['material'])
                backend=Backend()
                if case['kind']=='ack': result=GameplayBridgeService.acknowledge_pending_character_interaction(backend,interaction_instance_id=case['instance'])
                else: result=GameplayBridgeService.reply_pending_character_interaction(backend,accept=case['accept'],interaction_instance_id=case['instance'])
                output.append({'result':result,'calls':len(backend.calls)})
            json.dump(output,sys.stdout,ensure_ascii=False,separators=(',',':'),allow_nan=False)
            """;
        var builder=new ProcessBuilder(python,"-c",script).directory(java.nio.file.Path.of(repository).toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY",repository);builder.environment().put("PYTHONPATH",java.nio.file.Path.of(repository,"ck3_autonomous_player","src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();var result=new java.util.concurrent.CompletableFuture<byte[]>();
        Thread reader=Thread.ofVirtual().start(()->{try {result.complete(process.getInputStream().readNBytes(1024*1024+1));}catch(java.io.IOException failure){result.completeExceptionally(failure);}});
        try {
            process.getOutputStream().write(DriverJson.encodeNode(cases));process.getOutputStream().close();
            assertTrue(process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS),"original Service producer timed out");
            byte[] bytes=result.get(5,java.util.concurrent.TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=1024*1024);
            var rows=StrictJson.parse(bytes);assertEquals(3,rows.size());
            for(int index=0;index<rows.size();index++) {
                assertEquals(1,rows.get(index).get("calls").intValue());ObjectNode original=object(rows.get(index).get("result"));
                ObjectNode actual=expected.get(index);ObjectNode projected=StrictJson.object();
                for(var field:original.properties())projected.set(field.getKey(),actual.get(field.getKey()));
                // Normalize both through the sole full-frame numeric JSON domain before structural comparison.
                assertEquals(DriverJson.toNode(DriverJson.object(DriverJson.encodeNode(original),65536)),DriverJson.toNode(DriverJson.object(DriverJson.encodeNode(projected),65536)));
            }
        }finally {if(process.isAlive())process.destroyForcibly();reader.join(5000);}
    }
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static ObjectNode object(com.fasterxml.jackson.databind.JsonNode value){assertTrue(value.isObject());return (ObjectNode)value;}
    private static final class ReceiptArchive implements ActionPorts.OutcomeArchive {
        private final ActionReceipt receipt;private final ExactRef reference=new ExactRef("synthetic-pending-receipt",1,"b".repeat(64));ReceiptArchive(ActionReceipt receipt){this.receipt=receipt;}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){assertEquals(receipt,value);return reference;}@Override public ActionReceipt loadReceipt(ExactRef value){assertEquals(reference,value);return receipt;}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw new UnsupportedOperationException();}@Override public NativeActionPort.DispatchOutcome load(ExactRef value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw new UnsupportedOperationException();}@Override public NativeRequest loadRequest(ExactRef value){throw new UnsupportedOperationException();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw new UnsupportedOperationException();}@Override public ExactRef requestReferenceOf(NativeRequest value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw new UnsupportedOperationException();}@Override public byte[] loadNativeFrame(ExactRef value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveMaterial(RawJson value){throw new UnsupportedOperationException();}@Override public RawJson loadMaterial(ExactRef value){throw new UnsupportedOperationException();}@Override public ExactRef materialReferenceOf(RawJson value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw new UnsupportedOperationException();}@Override public PlanningReadReceipt loadRead(ExactRef value){throw new UnsupportedOperationException();}@Override public ExactRef readReferenceOf(PlanningReadReceipt value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw new UnsupportedOperationException();}@Override public ActionRecord loadRecord(ExactRef value){throw new UnsupportedOperationException();}@Override public ExactRef recordReferenceOf(ActionRecord value){throw new UnsupportedOperationException();}
    }
}
