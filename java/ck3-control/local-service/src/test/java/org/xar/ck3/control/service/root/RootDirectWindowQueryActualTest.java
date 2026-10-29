package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.Objects;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.junit.jupiter.api.Assertions.*;

/** Persistent default JUnit entry. A real startup provider supplies existing qualified Roots and native inputs;
 * absent inputs fail explicitly, never skip or construct a replacement Root, ACK, Known or private permit. */
public final class RootDirectWindowQueryActualTest {
    public enum Scenario { RESOLVES_COMPLETED_CLOSE, OWNER_STILL_UNAVAILABLE, ORIGINAL_TECHNICAL_READ_DEFERRED, NEGATIVE_CLOSE_ACK, POSITIVE_CLOSE_WITHOUT_COMPLETED_CALLBACK, UNPAUSED_CURRENT_FRAME, ORIGINAL_CLOSE_OUTCOME_UNKNOWN, RECONNECTED_CURRENT_QUERY, DIFFERENT_ACTOR_OR_EPISODE_CURRENT_QUERY }
    public interface InputsProducer { Inputs open(Scenario actualScenario) throws Exception; }
    public record Inputs(RootInstalledCatalog catalog,ArmyCalls.Frame query,String originalCloseActionId,Instant deadline) {
        public Inputs {Objects.requireNonNull(catalog);Objects.requireNonNull(query);Objects.requireNonNull(originalCloseActionId);Objects.requireNonNull(deadline);}
    }
    private static Inputs actual(Scenario scenario)throws Exception {
        var producers=ServiceLoader.load(InputsProducer.class).stream().toList();
        if(producers.size()!=1)throw new IllegalStateException("MISSING_ACTUAL_ROOT_WINDOW_QUERY_INPUTS_NOT_RUN: "+scenario);
        Inputs result=Objects.requireNonNull(producers.getFirst().get().open(scenario));
        assertEquals(result.query(),ArmyCallCodec.decode(result.query().method(),ArmyCallCodec.encode(result.query())));
        return result;
    }
    private static ObjectNode parseNativeObject(byte[] raw) {
        return assertInstanceOf(ObjectNode.class,
                FullJsonTree.parse(new RawJson(raw).bytes(), RawJson.MAXIMUM_BYTES));
    }
    private static RootApplicationSession root(Inputs input) {
        assertInstanceOf(RootApplicationSession.class,input.catalog().context().actions());
        return (RootApplicationSession)input.catalog().context().actions();
    }
    private static ActionReceipt original(Inputs input)throws Exception {
        var context=input.catalog().context();RootApplicationSession root=root(input);
        return root.withPublicStandaloneRead(input.deadline(),same->{
            context.core().requireCurrentForAccess(same,root);
            return context.core().actions().withFrozen(same,lease->lease.find(input.originalCloseActionId()).orElseThrow());
        });
    }
    private static ArmyWindowService.Reply query(Inputs input) {
        var service=input.catalog().army().products().windows();
        return switch(input.query().method()) {
            case QUERY_WAR_DECLARED_OVERVIEW_V1 -> service.query_war_declared_overview_v1(input.query());
            case QUERY_WAR_RESULTS_WINDOW_V1 -> service.query_war_results_window_v1(input.query());
            default -> throw new IllegalArgumentException("actual fixture must select one original public window QUERY");
        };
    }
    private static void unchangedAttempt(ActionReceipt before,ActionReceipt after) {
        assertEquals(before.command(),after.command());assertEquals(before.bodySha256(),after.bodySha256());
        assertEquals(ActionTransitions.attempt(before.state()),ActionTransitions.attempt(after.state()));
        assertEquals(ActionTransitions.dispatch(before.state()),ActionTransitions.dispatch(after.state()));
    }
    private static NativeDirectFixedWindowObservation.Original retained(Inputs input,ActionReceipt receipt)throws Exception {
        RootApplicationSession root=root(input);var context=input.catalog().context();
        return root.withPublicStandaloneRead(input.deadline(),same->{
            context.core().requireCurrentForAccess(same,root);
            return input.catalog().remainingDomains().armyOrdinary().directWindows().original(receipt);
        });
    }
    @Test void actualPublicQuerySettlesOnlyItsOriginalCompletedClose()throws Exception {
        Inputs input=actual(Scenario.RESOLVES_COMPLETED_CLOSE);ActionReceipt before=original(input);
        assertInstanceOf(ActionState.Unknown.class,before.state());
        ArmyWindowService.Reply reply=query(input);ActionReceipt after=original(input);unchangedAttempt(before,after);
        var settled=assertInstanceOf(ActionState.Settled.class,after.state());
        var complete=assertInstanceOf(ActionState.DirectFixedWindowCompleted.class,settled.settlement());
        assertEquals(NativeDirectFixedWindowObservation.Resolution.LATER_OWNER_QUERY_RESOLVED,complete.completion().resolution());
        var actual=retained(input,after);var owner=actual.ownerQuery().orElseThrow();assertTrue(owner.executionResolved());
        assertInstanceOf(CommandOrigin.Gameplay.class,owner.originalQuery().request().origin());
        assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,owner.originalQuery().before().guardMode());
        assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,owner.originalQuery().after().guardMode());
        assertNotEquals(before.ack().orElseThrow().requestId(),owner.originalQuery().requestId());
        assertEquals(owner.originalQuery().request().operation().value(),ArmyWindowReads.kind(input.query().method()).step(ArmyWindowCodec.Operation.QUERY));
        var encoded=parseNativeObject(ArmyWindowService.encode(reply).bytes());
        assertTrue(encoded.has("prior_close_execution_observation"));assertTrue(encoded.has("close_retry_deferred_for_native_frame"));
        assertFalse(encoded.get("prior_close_execution_observation").get("original_action_replayed").booleanValue());
        assertFalse(encoded.get("prior_close_execution_observation").get("close_action_credit").booleanValue());
        assertFalse(after.visibleGameplay());assertFalse(after.eligibleAdvance());
    }
    @Test void actualUnavailableOwnerQueryRemainsUnknownAndRetainsItsWholeResult()throws Exception {
        Inputs input=actual(Scenario.OWNER_STILL_UNAVAILABLE);ActionReceipt before=original(input);
        ArmyWindowService.Reply reply=query(input);ActionReceipt after=original(input);unchangedAttempt(before,after);
        assertInstanceOf(ActionState.Unknown.class,after.state());assertTrue(after.sequence()>before.sequence());
        var owner=retained(input,after).ownerQuery().orElseThrow();assertFalse(owner.executionResolved());
        assertInstanceOf(CommandOrigin.Gameplay.class,owner.originalQuery().request().origin());
        var restored=ArmyPublicWire.decodeExactSourceBound(ArmyWindowService.encode(reply),reply.context());
        var encoded=org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(restored);
        var original=parseNativeObject(owner.normalizedQuery().bytes());
        original.fieldNames().forEachRemaining(field->assertEquals(original.get(field),encoded.get(field),field));
        assertFalse(encoded.has("prior_close_execution_observation"));
    }
    @Test void actualNegativeTechnicalReadDoesNotBecomeKnownOrResubmitClose()throws Exception {
        Inputs input=actual(Scenario.ORIGINAL_TECHNICAL_READ_DEFERRED);ActionReceipt before=original(input);
        ArmyWindowService.Reply reply=query(input);ActionReceipt after=original(input);
        assertInstanceOf(ArmyWindowService.ReadDeferred.class,reply);
        assertEquals(before,after);assertInstanceOf(ActionState.Unknown.class,after.state());
        assertTrue(ArmyWindowService.encode(reply).bytes().length>2);
    }
    private static void actualReadonlyQueryWithoutCompletion(Scenario scenario,boolean nativeOk)throws Exception {
        Inputs input=actual(scenario);ActionReceipt before=original(input);
        assertInstanceOf(ActionState.Unknown.class,before.state());
        var ack=assertInstanceOf(NativeActionPort.AckReceived.class,ActionTransitions.dispatch(before.state()).orElseThrow());
        assertEquals(nativeOk,ack.nativeOk());
        assertFalse(input.catalog().remainingDomains().armyOrdinary().directWindows().acceptsOwnerQuery(before));
        ArmyWindowService.Reply reply=query(input);ActionReceipt after=original(input);
        assertEquals(before,after,"readonly public QUERY must preserve its exact original UNKNOWN, attempt, ACK and sequence");
        var known=assertInstanceOf(ArmyWindowService.KnownQuery.class,reply);
        assertTrue(known.priorClose().isEmpty());
        assertInstanceOf(CommandOrigin.Gameplay.class,known.original().receipt().request().origin());
        assertNotEquals(ack.requestId(),known.original().receipt().requestId());
        assertEquals(input.query(),known.input());
        var restored=ArmyPublicWire.decodeExactSourceBound(ArmyWindowService.encode(reply),reply.context());
        var encoded=org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(restored);
        var original=known.original().value().normalized();
        original.remove(java.util.List.of("queried_snapshot_id","queried_revision","queried_native_revision"));
        original.fieldNames().forEachRemaining(field->assertEquals(original.get(field),encoded.get(field),field));
        assertFalse(encoded.has("prior_close_execution_observation"));
        assertFalse(encoded.has("close_retry_deferred_for_native_frame"));
    }
    @Test void actualNegativeCloseAcknowledgementStillReturnsTheWholeIndependentQuery()throws Exception {
        actualReadonlyQueryWithoutCompletion(Scenario.NEGATIVE_CLOSE_ACK,false);
    }
    @Test void actualPositiveAcknowledgementWithoutCompletedCallbackRemainsReadonly()throws Exception {
        actualReadonlyQueryWithoutCompletion(Scenario.POSITIVE_CLOSE_WITHOUT_COMPLETED_CALLBACK,true);
    }
    @Test void unpausedPhysicalDataCannotPretendToBeAnOrdinaryPublicQueryGuard()throws Exception {
        Inputs input=actual(Scenario.UNPAUSED_CURRENT_FRAME);ActionReceipt before=original(input);
        var failure=assertThrows(org.xar.ck3.control.service.mcp.PublicServiceFailure.class,()->query(input));
        assertEquals(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());
        assertEquals(before,original(input));
        assertInstanceOf(ActionState.Unknown.class,before.state());assertFalse(before.visibleGameplay());
    }
    @Test void missingOriginalCloseAckAllowsOnlyTheActualReadonlyPublicQuery()throws Exception {
        Inputs input=actual(Scenario.ORIGINAL_CLOSE_OUTCOME_UNKNOWN);ActionReceipt before=original(input);
        var original=assertInstanceOf(ActionState.Unknown.class,before.state());assertTrue(original.attempt().isPresent());
        assertTrue(original.dispatch().isEmpty()||original.dispatch().orElseThrow() instanceof NativeActionPort.Unknown);
        var known=assertInstanceOf(ArmyWindowService.KnownQuery.class,query(input));
        assertEquals(before,original(input));assertTrue(known.priorClose().isEmpty());
        assertInstanceOf(CommandOrigin.Gameplay.class,known.original().receipt().request().origin());
        assertNotEquals(original.attempt().orElseThrow().requestId(),known.original().receipt().requestId());
        var encoded=parseNativeObject(ArmyWindowService.encode(known).bytes());
        assertFalse(encoded.has("prior_close_execution_observation"));
        assertFalse(encoded.has("close_retry_deferred_for_native_frame"));
        assertFalse(before.visibleGameplay());assertFalse(before.eligibleAdvance());
    }
    private static ArmyWindowService.KnownQuery actualCurrentQueryWithoutOriginalResolution(Inputs input)throws Exception {
        ActionReceipt before=original(input);assertInstanceOf(ActionState.Unknown.class,before.state());
        assertTrue(input.catalog().remainingDomains().armyOrdinary().directWindows().acceptsOwnerQuery(before));
        var known=assertInstanceOf(ArmyWindowService.KnownQuery.class,query(input));
        assertEquals(before,original(input));assertTrue(known.priorClose().isEmpty());
        assertInstanceOf(CommandOrigin.Gameplay.class,known.original().receipt().request().origin());
        var encoded=parseNativeObject(ArmyWindowService.encode(known).bytes());
        var normalized=known.original().value().normalized();
        normalized.remove(java.util.List.of("queried_snapshot_id","queried_revision","queried_native_revision"));
        normalized.fieldNames().forEachRemaining(field->assertEquals(normalized.get(field),encoded.get(field),field));
        assertFalse(encoded.has("prior_close_execution_observation"));
        assertFalse(encoded.has("close_retry_deferred_for_native_frame"));
        assertFalse(before.visibleGameplay());assertFalse(before.eligibleAdvance());return known;
    }
    @Test void reconnectedCurrentPublicQueryReturnsWholeResultAndPreservesOldPending()throws Exception {
        Inputs input=actual(Scenario.RECONNECTED_CURRENT_QUERY);ActionReceipt before=original(input);
        var known=actualCurrentQueryWithoutOriginalResolution(input);
        assertNotEquals(ActionTransitions.attempt(before.state()).orElseThrow().guard().connectionGeneration(),
                known.original().receipt().before().binding().connectionGeneration());
    }
    @Test void currentActorOrEpisodeChangeCannotResolveOldCloseOrSuppressItsPublicQuery()throws Exception {
        Inputs input=actual(Scenario.DIFFERENT_ACTOR_OR_EPISODE_CURRENT_QUERY);ActionReceipt before=original(input);
        var known=actualCurrentQueryWithoutOriginalResolution(input);
        var old=before.command().before().frame();var current=known.original().receipt().request().before().frame();
        assertTrue(!old.identity().player().equals(current.identity().player())||!old.episodeRunId().equals(current.episodeRunId()));
    }
}
