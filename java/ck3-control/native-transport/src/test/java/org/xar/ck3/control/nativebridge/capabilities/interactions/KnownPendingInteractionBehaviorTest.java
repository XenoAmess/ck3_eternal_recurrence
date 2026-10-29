package org.xar.ck3.control.nativebridge.capabilities.interactions;

import org.xar.ck3.control.contracts.NativeCharacterId;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionFixtures.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Input;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Plan;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

final class KnownPendingInteractionBehaviorTest {
    private static final class SameRegisteredQueryObserved extends RuntimeException { private static final long serialVersionUID=1L; }
    @Test void missingContextUsesExactlyTheInstalledQueryInstanceAndOriginalPreparation() {
        var c=context();ReadContract<PendingContext> actual=PendingInteractionContracts.pending(SOURCE);AtomicInteger calls=new AtomicInteger();
        PlanningReadPort reads=new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                assertSame(actual,contract,"policy must borrow the same registered producer, not mint an equivalent contract");
                assertEquals(PENDING,parse(contract.prepare(request,"same-query").additionalFields()).path("pending_interaction_id").intValue());calls.incrementAndGet();throw new SameRegisteredQueryObserved();
            }
        };
        var operations=new java.util.HashSet<>(steps());operations.add(actual.operation());
        var request=new PlanningRequest(c.before(),c.source(),c.sessionId(),c.deadline(),new PlanningObservation(InteractionArguments.app(snapshot(c)),List.of(),Set.copyOf(operations),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var policy=new KnownPendingInteractionPolicy(SOURCE,r->c,reads,actual,operation->Optional.empty());
        assertThrows(SameRegisteredQueryObserved.class,()->policy.evaluateCore(request,OrdinaryPolicy.Draft.empty()));assertEquals(1,calls.get());
    }
    @Test void realQueryComposerStrictWireHistoryPolicyPlanRoundtripAndNativePreparationShareOneSignedId() {
        var c=context();ObjectNode original=wire(c,"spar_with_knight_interaction"),snapshot=snapshot(c);
        ObjectNode args=InteractionArguments.body(c).put("pending_id",PENDING);
        ReadContract<PendingContext> contract=PendingInteractionContracts.pending(SOURCE);
        var query=contract.prepare(new PlanningReadRequest(c.before(),c.source(),c.sessionId(),contract.operation(),InteractionArguments.app(args),c.deadline()),"query-1");
        assertEquals(PENDING,parse(query.additionalFields()).path("pending_interaction_id").intValue());
        var request=request(c,snapshot,original,steps());
        var captured=KnownPendingInteractionEvidence.pending(request,c).orElseThrow();
        assertEquals(PENDING,captured.value().instance().value());
        var policy=new KnownPendingInteractionPolicy(SOURCE,r->c,noReads(),contract,operation->Optional.empty());
        var chosen=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluateCore(request,OrdinaryPolicy.Draft.empty()));
        ActionCommand command=chosen.draft().command().orElseThrow();
        assertEquals(Action.REJECT.step(),command.operation().value());
        var retained=InteractionArguments.parseApp(chosen.draft().detail());
        Plan plan=KnownPendingInteractionPlanCodec.decode(retained.get("java_policy_plan"));
        assertEquals(plan,KnownPendingInteractionPlanCodec.decode(KnownPendingInteractionPlanCodec.encode(plan)));
        NativeRequest prepared=KnownPendingInteractionEffects.preparation().prepare(command,"reply-1");
        assertEquals(Action.REJECT.step(),prepared.step());
        assertEquals(PENDING,parse(prepared.additionalFields()).path("pending_interaction_id").intValue());
        assertEquals(parse(encode(original)),InteractionArguments.parseApp(captured.originalWrapper()));
    }
    @Test void strictWireRejectsBooleanFloatMissingFieldsSourceDriftAndWrongFullIdentity() {
        var c=context();
        for(int mode=0;mode<5;mode++) {
            ObjectNode raw=wire(c,"spar_with_knight_interaction");
            ObjectNode context=(ObjectNode)raw.get("pending_character_interaction_context");
            switch(mode) {
                case 0 -> context.put("pending_interaction_id",true);
                case 1 -> context.put("pending_interaction_id",(double)PENDING);
                case 2 -> context.remove("deadline");
                case 3 -> ((ObjectNode)context.get("provenance")).put("reply_validator_rva","0x1");
                case 4 -> context.put("pending_interaction_id",-1);
            }
            assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decode(encode(raw),c,c.controls().pending().instance()));
        }
    }
    @Test void pendingRoleAndRoutingIntegerBoundariesRejectAliasesSentinelsAndWrongTokens() {
        var c=context();
        for(String field:List.of("actor_character_id","recipient_character_id","played_character_id")) {
            for(String token:List.of("-1","2147483648","4294967294","-2147483649","true","0.0","\"-2\"","null")) {
                ObjectNode raw=wire(c,"spar_with_knight_interaction");
                ObjectNode nativeContext=(ObjectNode)raw.get("pending_character_interaction_context");
                ObjectNode role=(ObjectNode)nativeContext.get(field.equals("played_character_id")?"routing":"roles");
                var value=org.xar.ck3.control.application.driver.DriverJson.toNode(org.xar.ck3.control.application.driver.DriverJson.object(
                        ("{\"value\":"+token+"}").getBytes(java.nio.charset.StandardCharsets.UTF_8),65536)).get("value");
                role.set(field,value);
                assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decode(encode(raw),c,c.controls().pending().instance()),field+" token="+token);
            }
        }
        ObjectNode absent=wire(c,"spar_with_knight_interaction");
        ((ObjectNode)absent.path("pending_character_interaction_context").get("roles")).remove("recipient_character_id");
        assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decode(encode(absent),c,c.controls().pending().instance()));
    }
    @Test void stalePublicRevisionCannotBeSubstitutedForTheNativeRevision() {
        var c=context();ObjectNode raw=wire(c,"spar_with_knight_interaction");
        assertTrue(KnownPendingInteractionEvidence.pending(request(c,snapshot(c),raw,steps()),c).isPresent());
        raw.put("queried_revision",41);
        assertTrue(KnownPendingInteractionEvidence.pending(request(c,snapshot(c),raw,steps()),c).isEmpty());
    }
    @Test void knownMarriageNeverBecomesUniqueAcceptAndTheStoredPlanCannotForgeAcceptance() {
        var c=context();ObjectNode raw=wire(c,"arrange_marriage_interaction");
        ObjectNode legality=(ObjectNode)raw.path("pending_character_interaction_context").get("legality");
        ((ObjectNode)legality.get("reject")).put("allowed",false).put("reason","not_legal");
        Plan selected=KnownPendingInteractionRules.evaluate(input(c,snapshot(c),raw,false));
        assertEquals(Classification.KNOWN_MARRIAGE,selected.classification());assertTrue(selected.selected().isEmpty());
        ObjectNode stored=KnownPendingInteractionPlanCodec.encode(selected);stored.put("selected_action","accept");stored.putArray("blocked_reasons");
        assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPlanCodec.decode(stored));
    }
    @Test void exactKnownGrantAndPerkRemainDedicatedAndReceivedRansomRequiresPositiveQualifiedCurrentPeaceInput() {
        var c=context();
        assertEquals(Optional.of(Action.REJECT),KnownPendingInteractionRules.evaluate(input(c,snapshot(c),wire(c,"grant_vassal_interaction"),false)).selected());
        assertEquals(Optional.of(Action.ACCEPT),KnownPendingInteractionRules.evaluate(input(c,snapshot(c),wire(c,"perk_alliance_interaction"),false)).selected());
        Plan ransom=KnownPendingInteractionRules.evaluate(input(c,snapshot(c),wire(c,"pay_ransom_interaction"),true));
        assertEquals(Optional.of(Action.ACCEPT),ransom.selected());assertTrue(ransom.ordinaryGoldReady());
        assertEquals(Optional.of(1250000L).map(BigInteger::valueOf),ransom.quotedGoldRaw());
        var bounded=input(c,snapshot(c),wire(c,"pay_ransom_interaction"),true);
        var unknownWar=new Input(bounded.context(),bounded.held(),bounded.activeWars(),Optional.empty(),bounded.prisoners(),bounded.inboundTerms(),bounded.availableSteps());
        assertTrue(KnownPendingInteractionRules.evaluate(unknownWar).blockedReasons().contains("received_ransom_no_war_hostage_input_required"));
        assertTrue(KnownPendingInteractionRules.evaluate(input(c,snapshot(c),wire(c,"pay_ransom_interaction"),false)).selected().isEmpty());
    }
    @Test void blockedMarriageContinuesTheSameCoreWithItsObservedWindowPreservedAndScopeAlwaysCleared() {
        var c=context();ObjectNode raw=wire(c,"arrange_marriage_interaction");
        ((ObjectNode)raw.path("pending_character_interaction_context").path("send_options").path("rows").get(1)).put("selected",true);
        var original=request(c,snapshot(c),raw,steps());AtomicInteger calls=new AtomicInteger();
        var policy=new KnownPendingInteractionPolicy(SOURCE,r->c,noReads(),PendingInteractionContracts.pending(SOURCE),operation->Optional.empty(),(projected,previous)-> {
            calls.incrementAndGet();assertEquals(original.observations().snapshot(),projected.observations().snapshot());
            assertEquals(original.observations().history(),projected.observations().history());
            assertFalse(projected.observations().actionSteps().contains(new OperationKey(Action.ACCEPT.step())));
            var command=new ActionCommand("ordinary-save",projected.before(),projected.source(),projected.sessionId(),new OperationKey("save-checkpoint"),
                    InteractionArguments.app(F.objectNode()),new ExpectedPostcondition(1,projected.before(),projected.source(),"fixture-save/v1",
                    List.of(new ExpectedBoolean(new FieldKey("fixture_saved"),true))),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),projected.deadline());
            return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("one-life-turn-v1","baseline","ordinary core checkpoint",OrdinaryPolicy.Kind.ORDINARY,
                    Optional.of(command),OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.empty(),InteractionArguments.app(F.objectNode().put("phase","baseline"))),"actual core callback");
        });
        var result=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluateCore(original,OrdinaryPolicy.Draft.empty()));
        assertEquals("save-checkpoint",result.draft().command().orElseThrow().operation().value());
        var detail=InteractionArguments.parseApp(result.draft().detail());
        assertFalse(detail.path("notification_continuation").path("observed_notification_cleared").booleanValue());
        assertTrue(detail.path("notification_continuation").path("observed_snapshot_unchanged").booleanValue());
        assertEquals(1,calls.get());
        ObjectNode eventSnapshot=snapshot(c);eventSnapshot.putObject("active_event").put("instance_id",9);
        var blocked=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluateCore(request(c,eventSnapshot,raw,steps()),OrdinaryPolicy.Draft.empty()));
        assertTrue(blocked.draft().command().isEmpty());assertEquals(1,calls.get());
    }
    @Test void submittedAckAloneNeverProvesReplyAndRansomRequiresBothIndependentGoldAndCustody() {
        var c=context();ObjectNode raw=wire(c,"pay_ransom_interaction");
        Plan plan=KnownPendingInteractionRules.evaluate(input(c,snapshot(c),raw,true));
        RawJson ack=encode(F.objectNode().put("step",Action.ACCEPT.step()).put("accepted",true).put("status","submitted"));
        var before=snapshot(c);var afterContext=context(8,42);var after=snapshot(afterContext);after.putNull("pending_character_interaction");
        var unchanged=KnownPendingInteractionPostcondition.verify(new KnownPendingInteractionPostcondition.Input(plan,c.before(),c.before(),
                InteractionArguments.app(before),InteractionArguments.app(before),ack,Optional.empty()));assertFalse(unchanged.verified());
        var missing=KnownPendingInteractionPostcondition.verify(new KnownPendingInteractionPostcondition.Input(plan,c.before(),afterContext.before(),
                InteractionArguments.app(before),InteractionArguments.app(after),ack,Optional.empty()));assertFalse(missing.verified());
        ((ObjectNode)after.get("played_character_gold")).put("raw",1350000);
        var custody=Optional.of(new KnownPendingInteractionPostcondition.PrisonerAfter(afterContext.before(),prisoners(false)));
        var verified=KnownPendingInteractionPostcondition.verify(new KnownPendingInteractionPostcondition.Input(plan,c.before(),afterContext.before(),
                InteractionArguments.app(before),InteractionArguments.app(after),ack,custody));assertTrue(verified.verified());
        assertEquals(Optional.of(BigInteger.valueOf(1250000)),verified.observedGoldIncreaseRaw());
        assertFalse(InteractionArguments.parseApp(verified.compatibleResult()).path("replay_allowed").booleanValue());
        var retained=Optional.of(new KnownPendingInteractionPostcondition.PrisonerAfter(afterContext.before(),prisoners(true)));
        assertFalse(KnownPendingInteractionPostcondition.verify(new KnownPendingInteractionPostcondition.Input(plan,c.before(),afterContext.before(),
                InteractionArguments.app(before),InteractionArguments.app(after),ack,retained)).verified());
    }
    @Test void originalPositiveSenderAndRolePropagationThroughActionCodecAndReceiptRoundtrip() {
        var c=context();ObjectNode raw=wire(c,"spar_with_knight_interaction");
        var request=request(c,snapshot(c),raw,steps());
        var policy=new KnownPendingInteractionPolicy(SOURCE,r->c,noReads(),PendingInteractionContracts.pending(SOURCE),operation->Optional.empty());
        var chosen=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluateCore(request,OrdinaryPolicy.Draft.empty()));
        ActionCommand command=chosen.draft().command().orElseThrow();
        assertEquals(Set.of(c.actor(),BigInteger.valueOf(c.controls().pending().sender().value())),command.claims().characterIds());
        byte[] encoded=ActionCodec.encodeCommand(command);
        ActionCommand decoded=ActionCodec.decodeCommand(encoded);
        assertEquals(command,decoded);
        var unknown=new ActionState.Unknown(Optional.empty(),Optional.empty(),"unknown",List.of());
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),unknown);
        ActionPorts.OutcomeArchive archive=(ActionPorts.OutcomeArchive)java.lang.reflect.Proxy.newProxyInstance(
                ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},
                (proxy,method,arguments)->{throw new AssertionError("empty UNKNOWN must not archive fabricated native originals: "+method.getName());});
        byte[] receiptBytes=ActionReceiptCodec.encodeReceipt(receipt,archive);
        ActionReceipt decodedReceipt=ActionReceiptCodec.decodeReceipt(receiptBytes,archive);
        assertEquals(receipt,decodedReceipt);
    }
    @Test void signedBothOriginalRolesSurviveRawProjectionQueryPolicyClaimsAndUnknownColdPreparation() {
        int[][] pairs={{Integer.MIN_VALUE,-2},{-2,Integer.MIN_VALUE},{0,Integer.MAX_VALUE},{Integer.MAX_VALUE,0},{17,-2}};
        for(int[] pair:pairs) {
            var original=F.objectNode().put("instance_id",PENDING).put("sender_character_id",pair[1]).put("auto_accept_notification",false);
            var actual=NativePendingInteractionConsumerTest.fixture(
                    org.xar.ck3.control.contracts.semantic.NativePendingInteraction.normalize(original),pair[0],null,List.of());
            var c=new RootInteractionContextProjection(InteractionModels.Build.CROZIER4).project(actual,actual.observedAt().plusSeconds(30));
            RootInteractionContextProjection.requireExact(actual,c);
            ObjectNode raw=wire(c,"spar_with_knight_interaction"),arguments=InteractionArguments.body(c).put("pending_id",PENDING);
            ReadContract<PendingContext> contract=PendingInteractionContracts.pending(SOURCE);
            var read=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),contract.operation(),InteractionArguments.app(arguments),c.deadline());
            assertEquals(c,InteractionArguments.context(read));
            assertEquals(PENDING,parse(contract.prepare(read,"signed-query").additionalFields()).path("pending_interaction_id").intValue());
            var observed=KnownPendingInteractionEvidence.pending(request(c,snapshot(c),raw,steps()),c).orElseThrow();
            assertEquals(pair[1],observed.value().roles().actor());assertEquals(pair[0],observed.value().roles().recipient());
            var policy=new KnownPendingInteractionPolicy(SOURCE,r->c,noReads(),contract,operation->Optional.empty());
            var chosen=assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluateCore(request(c,snapshot(c),raw,steps()),OrdinaryPolicy.Draft.empty()));
            ActionCommand command=chosen.draft().command().orElseThrow();
            assertEquals(Action.REJECT.step(),command.operation().value());
            assertEquals(Set.of(BigInteger.valueOf(pair[0]),BigInteger.valueOf(pair[1])),command.claims().characterIds());
            ActionCommand decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));assertEquals(command,decoded);
            var unknown=new ActionReceipt(1,1,decoded,ActionCodec.bodySha256(decoded),
                    new ActionState.Unknown(Optional.empty(),Optional.empty(),"original signed reply remains unknown",List.of()));
            ActionPorts.OutcomeArchive archive=(ActionPorts.OutcomeArchive)java.lang.reflect.Proxy.newProxyInstance(
                    ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},
                    (proxy,method,values)->{throw new AssertionError("UNKNOWN without native originals must not invent archive data: "+method.getName());});
            byte[] bytes=ActionReceiptCodec.encodeReceipt(unknown,archive);
            var cold=ActionReceiptCodec.decodeReceipt(bytes,archive);
            assertEquals(unknown,cold);assertArrayEquals(bytes,ActionReceiptCodec.encodeReceipt(cold,archive));
            assertFalse(cold.settled());assertTrue(cold.ack().isEmpty());assertTrue(cold.applied().isEmpty());
            assertEquals(c,InteractionArguments.context(cold.command()));
            var prepared=KnownPendingInteractionEffects.preparation().prepare(cold.command(),"cold-pure-preparation");
            assertEquals(PENDING,parse(prepared.additionalFields()).path("pending_interaction_id").intValue());
            assertEquals(command.operation().value(),prepared.step());
            ObjectNode wrongSender=raw.deepCopy();((ObjectNode)wrongSender.path("pending_character_interaction_context").get("roles")).put("actor_character_id",pair[1]==0?17:0);
            assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decode(encode(wrongSender),c,c.controls().pending().instance()));
            ObjectNode unsignedAlias=raw.deepCopy();((ObjectNode)unsignedAlias.path("pending_character_interaction_context").get("roles")).put("actor_character_id",Integer.toUnsignedLong(pair[1])+(pair[1]<0?0:4294967296L));
            assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decode(encode(unsignedAlias),c,c.controls().pending().instance()));
        }
    }
    @Test void theExistingExplicitReplyProducerUsesTheSameStrictVersionedPrimitiveWithoutAutomaticPolicyCredit() {
        var c=context();Action requested=Action.ACCEPT;
        var expected=KnownPendingInteractionCommands.expected(c,requested);
        var args=KnownPendingInteractionCommands.arguments(new InteractionModels.ActionContext(c,"operator-reply",expected,
                new Claims(Set.of(),Set.of(),Set.of(),Set.of())),requested);
        var command=new ActionCommand("operator-reply",c.before(),c.source(),c.sessionId(),new OperationKey(requested.step()),
                InteractionArguments.app(args),expected,new Claims(Set.of(),Set.of(),Set.of(),Set.of()),c.deadline());
        var plan=KnownPendingInteractionPlanCodec.decode(args.path("known_pending_plan").get("java_policy_plan"));
        assertEquals(Classification.EXPLICIT_NATIVE_REPLY,plan.classification());assertFalse(plan.classification().dedicated());
        assertFalse(plan.ordinaryGoldReady());
        assertEquals(requested.step(),KnownPendingInteractionEffects.preparation().prepare(command).step());
        ObjectNode historical=KnownPendingInteractionPlanCodec.encode(plan);historical.put("schema","xar.java.known-pending-plan/v1");
        assertThrows(IllegalArgumentException.class,()->KnownPendingInteractionPlanCodec.decode(historical));
    }
}
