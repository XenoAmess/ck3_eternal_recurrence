package org.xar.ck3.control.service.root;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Persistent actual Root writer regressions. Missing original inputs fail explicitly and never count as a skip or pass. */
public final class FixtureCompositeActualTest {
    public enum Scenario { COMPLETE, START_UNKNOWN, START_WITHOUT_FIRST_MAP, QUALIFICATION_PENDING, UNKNOWN_EVENT_LATER_OBSERVED, CONTINUATION_AFTER_ORIGINAL_DEADLINE }
    public interface InputsProducer {Inputs open(Scenario scenario)throws Exception;}
    @FunctionalInterface public interface OriginalContinuation {CompositeContinuationReport resume(ActionReceipt actualCanonicalParent)throws Exception;}
    public record Inputs(RootInstalledCatalog catalog,RootMenuSession menu,ActionCommand parent,Instant deadline,OriginalContinuation originalContinuation){
        public Inputs {Objects.requireNonNull(catalog);Objects.requireNonNull(menu);Objects.requireNonNull(parent);Objects.requireNonNull(deadline);Objects.requireNonNull(originalContinuation);}
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode jsonObject(com.fasterxml.jackson.databind.JsonNode value){if(value instanceof com.fasterxml.jackson.databind.node.ObjectNode object)return object;throw new IllegalArgumentException("JSON object required");}
    private static Inputs actual(Scenario scenario)throws Exception {
        var producers=ServiceLoader.load(InputsProducer.class).stream().toList();
        if(producers.size()!=1)throw new IllegalStateException("MISSING_ACTUAL_ROOT_FIXTURE_COMPOSITE_INPUTS_NOT_RUN: "+scenario);
        var input=Objects.requireNonNull(producers.getFirst().get().open(scenario));var context=input.catalog().context();
        assertSame(context.core().actions(),input.menu().coordinator);assertSame(context.writer(),input.menu().writer);
        assertEquals(context.source(),input.parent().source());FixturePlan.requireParent(input.parent());return input;
    }
    private static ActionJournal.Snapshot snapshot(Inputs input)throws java.io.IOException {
        var context=input.catalog().context();return context.writer().locked(same->context.core().actions().withFrozen(same,lease->lease.snapshot()));
    }
    private static ActionReceipt parent(Inputs input)throws Exception {
        return snapshot(input).actions().stream().filter(value->value.command().actionId().equals(input.parent().actionId())).findFirst().orElseThrow();
    }
    private static List<ActionReceipt> children(Inputs input,ActionReceipt parent)throws Exception {
        var all=snapshot(input).actions();return ActionTransitions.composite(parent.state()).orElseThrow().children().stream().map(child->{
            var actual=all.stream().filter(value->value.command().actionId().equals(child.actionId())).findFirst().orElseThrow();
            assertEquals(child.bodySha256(),actual.bodySha256());return actual;
        }).toList();
    }
    private static List<String> actualAttempts(ActionJournal.Snapshot snapshot){
        return snapshot.actions().stream().flatMap(value->ActionTransitions.attempt(value.state()).stream()).map(ActionState.Attempt::requestId).sorted().toList();
    }
    @Test void upfrontParentOwnsEveryCanonicalChildAndTheRealCommittedEntry()throws Exception {
        var input=actual(Scenario.COMPLETE);var receipt=input.menu().execute(input.parent());
        var settled=assertInstanceOf(ActionState.CompositeSettled.class,receipt.state());
        var complete=assertInstanceOf(ActionState.FixtureBusinessCompleted.class,settled.settlement()).observation();
        var children=children(input,receipt);assertFalse(children.isEmpty());complete.validateParent(input.parent());complete.validateChildren(settled.execution(),children);
        for(int index=0;index<children.size();index++){
            var child=children.get(index);assertTrue(child.settled());assertEquals(ActionIds.child(input.parent().actionId(),index+1,child.command().operation()),child.command().actionId());
            ActionTransitions.attempt(child.state()).ifPresent(attempt->assertFalse(attempt.submittedAt().isBefore(settled.execution().startedAt())));
        }
        var start=complete.evidence().originalStart();assertTrue(children.contains(start));
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,receipt.outcome());
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,start.outcome());
        var first=assertInstanceOf(ActionState.FixtureStarted.class,assertInstanceOf(ActionState.Settled.class,start.state()).settlement()).observation();
        assertNotEquals(first.firstHeartbeat(),first.lastHeartbeat());assertNotEquals(first.independentRead().requestId(),start.ack().orElseThrow().requestId());
        assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
    }
    @Test void unknownStartKeepsItsOriginalAttemptAndCannotCreateFollowingChildren()throws Exception {
        var input=actual(Scenario.START_UNKNOWN);var receipt=input.menu().execute(input.parent());
        assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());var before=snapshot(input);
        var children=children(input,receipt);var kind=FixturePlan.requireParent(input.parent()).kind();
        var start=children.stream().filter(value->value.command().operation().equals(kind.startOperation())).findFirst().orElseThrow();
        assertInstanceOf(ActionState.Unknown.class,start.state());assertEquals(start,children.getLast());
        input.menu().reconcile(input.parent().actionId());var after=snapshot(input);assertEquals(actualAttempts(before),actualAttempts(after));
        var retained=after.actions().stream().filter(value->value.command().actionId().equals(start.command().actionId())).findFirst().orElseThrow();
        assertEquals(ActionTransitions.attempt(start.state()),ActionTransitions.attempt(retained.state()));
        assertEquals(ActionTransitions.dispatch(start.state()),ActionTransitions.dispatch(retained.state()));
    }
    @Test void successfulAckWithoutIndependentFirstMapCannotAuthorizeAnEventChild()throws Exception {
        var input=actual(Scenario.START_WITHOUT_FIRST_MAP);var receipt=input.menu().execute(input.parent());
        assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());var children=children(input,receipt);
        var start=children.getLast();assertEquals(FixturePlan.requireParent(input.parent()).kind().startOperation(),start.command().operation());
        assertTrue(start.ack().orElseThrow().nativeOk());assertFalse(start.settled());
        assertTrue(children.stream().noneMatch(value->value.command().origin() instanceof CommandOrigin.Gameplay));
    }
    @Test void callerConstructedFixtureTokenCannotBorrowTheInstalledPrivateContinuation()throws Exception {
        var input=actual(Scenario.QUALIFICATION_PENDING);input.menu().execute(input.parent());var before=parent(input);
        assertInstanceOf(ActionState.CompositeUnknown.class,before.state());assertTrue(children(input,before).stream().allMatch(ActionReceipt::settled));
        CompositeContinuationToken foreign=new CompositeContinuationToken(){
            public ActionCommand originalParent(){return input.parent();}
            public Instant deadline(){return input.deadline();}
            public Kind kind(){return Kind.FIXTURE_STARTUP;}
        };
        assertThrows(IllegalArgumentException.class,()->input.catalog().context().writer().locked(same->input.menu().coordinator.continueOriginalComposite(same,foreign)));
        assertEquals(before,parent(input));
    }
    @Test void actualFixtureReceiptsRoundTripAndRejectDowngradedOrMissingProofFields()throws Exception {
        var input=actual(Scenario.COMPLETE);var receipt=input.menu().execute(input.parent());
        input.catalog().context().writer().locked(same->{
            var archive=input.catalog().context().archive().withSession(same);
            var actualSnapshot=input.catalog().context().core().actions().withFrozen(same,lease->lease.snapshot());
            for(var value:actualSnapshot.actions()){
                var wire=ActionReceiptCodec.encodeReceipt(value,archive);assertEquals(value,ActionReceiptCodec.decodeReceipt(wire,archive));
                if(value.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.FixtureStarted){
                    var malformed=jsonObject(StrictJson.parse(wire));
                    ((com.fasterxml.jackson.databind.node.ObjectNode)malformed.get("state").get("settlement").get("observation")).remove("independent_read");
                    assertThrows(IllegalArgumentException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(malformed),archive));
                }
            }
            var downgraded=jsonObject(StrictJson.parse(ActionReceiptCodec.encodeReceipt(receipt,archive))).put("schema",ActionReceiptCodec.COMPOSITE_FAILURE_EVIDENCE_SCHEMA);
            assertThrows(IllegalArgumentException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(downgraded),archive));return null;
        });
    }
    @Test void aPublicCursorRecordCannotReopenTheRetiredPrivateHeldScope()throws Exception {
        var input=actual(Scenario.COMPLETE);var receipt=input.menu().execute(input.parent());var execution=ActionTransitions.composite(receipt.state()).orElseThrow();
        new ActionChildPlanningScope.FixtureCursor(receipt,execution,children(input,receipt));
        input.catalog().context().writer().locked(same->{
            assertThrows(java.io.IOException.class,()->ActionChildPlanningScope.fixtureCurrent(same,same.head(),input.parent(),execution.handlerId()));return null;
        });
        input.catalog().context().writer().locked(same->{
            assertThrows(java.io.IOException.class,()->ActionChildPlanningScope.fixtureDeadline(same,same.head(),input.parent(),execution.handlerId()));return null;
        });
    }
    @Test void realPrivateContinuationMayReadUnknownStartButCannotSubmitAnyFollowingChild()throws Exception {
        var input=actual(Scenario.START_UNKNOWN);var receipt=input.menu().execute(input.parent());var before=snapshot(input);
        assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());var report=input.originalContinuation().resume(receipt);
        assertEquals(CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT,report.disposition());assertTrue(report.children().isEmpty());
        var after=snapshot(input);assertEquals(actualAttempts(before),actualAttempts(after));
        assertEquals(before.actions().stream().map(value->value.command().actionId()).sorted().toList(),after.actions().stream().map(value->value.command().actionId()).sorted().toList());
        assertInstanceOf(ActionState.CompositeUnknown.class,report.parent().state());
    }
    @Test void unknownEventResolvesFromItsOriginalFreshAfterReadWithoutAnotherEventSubmission()throws Exception {
        var input=actual(Scenario.UNKNOWN_EVENT_LATER_OBSERVED);var receipt=input.menu().execute(input.parent());var before=snapshot(input);
        assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());var original=children(input,receipt).getLast();
        assertInstanceOf(ActionState.Unknown.class,original.state());assertTrue(original.command().operation().value().startsWith("select-event-option-"));
        var report=input.originalContinuation().resume(receipt);var after=snapshot(input);
        assertEquals(actualAttempts(before),actualAttempts(after));assertTrue(report.children().isEmpty());
        var retained=after.actions().stream().filter(value->value.command().actionId().equals(original.command().actionId())).findFirst().orElseThrow();
        assertTrue(retained.settled());assertEquals(ActionTransitions.attempt(original.state()),ActionTransitions.attempt(retained.state()));
        assertEquals(ActionTransitions.dispatch(original.state()),ActionTransitions.dispatch(retained.state()));
        assertInstanceOf(ActionState.FixtureBusinessCompleted.class,assertInstanceOf(ActionState.CompositeSettled.class,report.parent().state()).settlement());
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,report.parent().outcome());
    }
    @Test void realContinuationReadsUseTheirSourceIssuedCutoffAfterTheOriginalStartDeadline()throws Exception {
        var input=actual(Scenario.CONTINUATION_AFTER_ORIGINAL_DEADLINE);var receipt=input.menu().execute(input.parent());
        assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());var before=snapshot(input);
        var report=input.originalContinuation().resume(receipt);
        assertFalse(input.catalog().context().clock().instant().isBefore(input.parent().deadline()),"actual provider must exercise the expired original cutoff");
        assertEquals(actualAttempts(before),actualAttempts(snapshot(input)));
        assertInstanceOf(ActionState.FixtureBusinessCompleted.class,assertInstanceOf(ActionState.CompositeSettled.class,report.parent().state()).settlement());
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,report.parent().outcome());
    }
}
