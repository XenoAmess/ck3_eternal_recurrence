package org.xar.ck3.control.nativebridge.capabilities.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.family.FamilyHistory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePlayedCharacter;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real focus pending producer -> JSON history -> public consumer. DATA grants no canonical or Native authority. */
final class ChildEducationFocusHistoryRecoveryTest {
    private static final String EPISODE = "focus-history-signed-controller";
    private static final String REQUEST = "original-focus-request";
    private static final Selection SELECTION = new Selection(0xFE000001L, Key.EDUCATION_STEWARDSHIP);

    private static Context context(long controller) {
        return new Context(new Frame("native:9", EPISODE, BigInteger.valueOf(9), 100, controller), BigInteger.valueOf(19));
    }
    private static Submitted submitted(Context before) {
        ObjectNode source = StrictJson.object().put("schema", SCHEMA).put("kind", "submit")
                .put("status", "submitted_verification_pending").putNull("unavailable_reason")
                .put("action_request_id", REQUEST).put("accepted", true).put("child_full_id", SELECTION.child())
                .put("requested_focus_key", SELECTION.target().wire());
        source.set("pre_frame", encodeFrame(before.frame()));
        return decodeSubmitted(new RawJson(StrictJson.canonical(source)), before.frame(), SELECTION, REQUEST);
    }
    private static Pending produce(Context before, boolean known) {
        Pending pending = ChildEducationFocusEffects.pendingData(before, SELECTION, REQUEST,
                known ? Optional.of(submitted(before)) : Optional.empty()).orElseThrow();
        assertEquals(pending, decodePending(verifyPending(pending)));
        return pending;
    }
    private static Obj object(Value value) { return OpportunityJson.object(value, "focus history"); }
    private static Obj roundtrip(Obj value) { return object(OpportunityJson.parse(OpportunityJson.encode(value))); }
    private static Obj pendingJson(Pending pending) { return object(OpportunityJson.parse(pending.original().bytes())); }
    private static Obj history(Pending pending, boolean autoTurn) {
        Obj result = pendingJson(pending);
        Obj row = autoTurn
                ? new Obj(Map.of("command", new Text("auto-turn"), "result", new Obj(Map.of("auto_turn",
                        new Obj(Map.of("selected_step", new Text(SUBMIT_STEP), "result", result))))))
                : new Obj(Map.of("command", new Text(SUBMIT_STEP), "result", result));
        return roundtrip(row);
    }
    private static Obj snapshot(int actor) {
        ObjectNode original = StrictJson.object().put("character_id", actor).put("alive", true);
        ObjectNode snapshot = StrictJson.object().put("episode_run_id", EPISODE);
        snapshot.set("played_character", NativePlayedCharacter.normalize(original, BigInteger.valueOf(9), com.fasterxml.jackson.databind.node.IntNode.valueOf(100)));
        return object(OpportunityJson.parse(StrictJson.canonical(snapshot)));
    }
    private static Obj rawSnapshot(Value actor) {
        return new Obj(Map.of("episode_run_id", new Text(EPISODE), "played_character", new Obj(Map.of("character_id", actor))));
    }
    private static Obj receipt(boolean applied, String request) {
        return roundtrip(new Obj(Map.of("command", new Text(RECEIPT_STEP), "result", new Obj(Map.of(
                "status", new Text("observed_applied"), "observed_applied", new Bool(applied),
                "submission", new Obj(Map.of("action_request_id", new Text(request))))))));
    }
    private static void retained(Pending original, Obj recovered) {
        assertEquals(pendingJson(original), recovered, "complete original pending, including source context and nulls, must survive");
        assertEquals(original, decodePending(new RawJson(StrictJson.canonical(OpportunityJson.toNode(recovered)))));
        assertEquals(REQUEST, OpportunityJson.text(recovered.get("action_request_id"), "original action"));
        assertEquals(BigInteger.valueOf(0xFE000001L), OpportunityJson.integer(recovered.get("child_full_id"), "raw child"));
    }

    @Test void realKnownProducerRestoresSignedControllerBoundariesThroughBothHistoryWrappers() {
        int[] actors = {Integer.MIN_VALUE, -33554431, -2, 1, Integer.MAX_VALUE};
        for (int actor : actors) {
            Pending pending = produce(context(Integer.toUnsignedLong(actor)), true);
            Obj snapshot = snapshot(actor);
            for (boolean autoTurn : new boolean[] {false, true}) {
                Obj recovered = FamilyHistory.focusPending(List.of(history(pending, autoTurn)), snapshot).orElseThrow();
                retained(pending, recovered);
                assertEquals(BigInteger.valueOf(actor), OpportunityJson.integer(object(snapshot.get("played_character")).get("character_id"), "signed public actor"));
                assertEquals(new Bool(true), recovered.get("accepted"));
                assertEquals(new Bool(true), recovered.get("native_command_submitted"));
            }
        }
    }

    @Test void unknownProducerRetainsNullAcceptanceAndOriginalRequestAfterHistorySerialization() {
        Pending pending = produce(context(4261412865L), false);
        assertEquals(PendingStatus.ACTION_STATE_UNKNOWN, pending.status());
        for (boolean autoTurn : new boolean[] {false, true}) {
            Obj recovered = FamilyHistory.focusPending(List.of(history(pending, autoTurn)), snapshot(-33554431)).orElseThrow();
            retained(pending, recovered);
            assertEquals(Nil.INSTANCE, recovered.get("accepted"));
            assertEquals(Nil.INSTANCE, recovered.get("native_command_submitted"));
        }
    }

    @Test void anotherControllerOrEpisodeAndZeroCannotBorrowTheRetainedFocusPending() {
        Pending pending = produce(context(4261412865L), true);
        Obj row = history(pending, false);
        assertTrue(FamilyHistory.focusPending(List.of(row), snapshot(-33554430)).isEmpty());
        assertTrue(FamilyHistory.focusPending(List.of(row), snapshot(-33554431).with("episode_run_id", new Text("other-episode"))).isEmpty());
        assertTrue(FamilyHistory.focusPending(List.of(row), snapshot(0)).isEmpty());
        retained(pending, FamilyHistory.focusPending(List.of(row), snapshot(-33554431)).orElseThrow());
    }

    @Test void modernPublicActorRejectsUnsignedAliasesWrongTokensAndAbsentSentinel() {
        Pending pending = produce(context(4261412865L), false);
        List<Obj> history = List.of(history(pending, false));
        for (Value invalid : List.of(new IntegerValue(BigInteger.valueOf(-1)),
                new IntegerValue(BigInteger.valueOf(2147483648L)), new IntegerValue(BigInteger.valueOf(-2147483649L)),
                new IntegerValue(BigInteger.valueOf(4261412865L)), new Bool(true), new DecimalValue("-33554431.0"),
                new Text("-33554431"), Nil.INSTANCE)) {
            assertThrows(IllegalArgumentException.class, () -> FamilyHistory.focusPending(history, roundtrip(rawSnapshot(invalid))));
        }
    }

    @Test void onlyMatchingObservedAppliedTrueHistoryClosesTheOriginalUnknownRequest() {
        Pending pending = produce(context(4261412865L), false);
        Obj row = history(pending, true), snapshot = snapshot(-33554431);
        retained(pending, FamilyHistory.focusPending(List.of(row, receipt(false, REQUEST)), snapshot).orElseThrow());
        retained(pending, FamilyHistory.focusPending(List.of(row, receipt(true, "another-request")), snapshot).orElseThrow());
        assertTrue(FamilyHistory.focusPending(List.of(row, receipt(true, REQUEST)), snapshot).isEmpty());
    }
}
