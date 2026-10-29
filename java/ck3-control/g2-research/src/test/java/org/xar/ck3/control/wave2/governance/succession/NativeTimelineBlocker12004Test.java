package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;

/** Pure adversarial boundary tests; the separate NativeIT consumes the genuine C++ whole producer. */
final class NativeTimelineBlocker12004Test {
    private static final int ACTOR = 31254, DATE = 53144328;
    private static final BigInteger REVISION = BigInteger.valueOf(31);

    @Test void livingNullIsDifferentFromAnUnavailableQueryAndRoundTrips() {
        Context living = context("none", false, false, false);
        assertEquals(Status.AVAILABLE, living.status()); assertInstanceOf(Unknown.class, living.canContinue());
        assertTrue(living.clearedObserved()); assertFalse(living.supportedCloseObserved());
        assertEquals(living, parseContext(StrictJson.parse(encodeContext(living)), binding().frame()));
        Context unknown = context("none", false, false, true);
        assertEquals(Status.UNAVAILABLE, unknown.status()); assertFalse(unknown.clearedObserved());
        assertEquals(unknown, parseContext(StrictJson.parse(encodeContext(unknown)), binding().frame()));
        assertNotEquals(living, unknown);
        assertEquals(new Scene("{\"b\":2,\"a\":1}", "null", java.util.Optional.empty()),
                new Scene("{\"a\":1,\"b\":2}", "null", java.util.Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> Scene.fromSnapshot(StrictJson.object()));
        assertThrows(IllegalArgumentException.class, () -> new Scene("false", "null", java.util.Optional.empty()));
    }
    @Test void acceptedAvailableWithCanContinueFalseCannotBecomeAClosePermit() {
        Context over = context("game_over_modal", true, true, false);
        assertEquals(Identity.GAME_OVER_MODAL, over.identity()); assertFalse(over.supportedCloseObserved());
        Query initial = query(queryNode("initial", over, 1, 10), binding(), "initial");
        assertEquals(ClearanceState.INITIAL_CLOSE_NOT_OBSERVED, compareClearance(initial,
                close(ackNode("close", 11), binding(), "close"),
                query(queryNode("later", context("none", false, false, false), 2, 12), binding(), "later")).state());
    }
    @Test void exactIntegerBooleanMissingDuplicateAndExtraFieldsAreRejected() {
        ObjectNode clean = queryNode("query", context("death_succession_modal", true, true, false), 1, 10);
        for (String token : new String[]{"true", "1.0", "\"1\""}) {
            ObjectNode bad = copy(clean); ((ObjectNode) bad.get("result")).set("query_sequence", json(token));
            assertThrows(IllegalArgumentException.class, () -> query(bad, binding(), "query"));
            ObjectNode protocol = copy(clean); protocol.set("protocol_version", json(token));
            assertThrows(IllegalArgumentException.class, () -> query(protocol, binding(), "query"));
        }
        ObjectNode unknown = copy(clean); ((ObjectNode) unknown.get("result")).put("continuation_authorized", true);
        assertThrows(IllegalArgumentException.class, () -> query(unknown, binding(), "query"));
        ObjectNode missing = copy(clean); ((ObjectNode) missing.path("result").path("current_timeline_blocker_context")).remove("can_continue");
        assertThrows(IllegalArgumentException.class, () -> query(missing, binding(), "query"));
        String text = new String(bytes(clean), StandardCharsets.UTF_8).replace("\"query_sequence\":1", "\"query_sequence\":1,\"query_sequence\":1");
        byte[] duplicate = text.getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> parseQuery(duplicate, reference(duplicate), binding(), "query"));
        ObjectNode boolVersion = copy(clean); ((ObjectNode) boolVersion.path("result").path("current_timeline_blocker_context")).put("schema_version", true);
        assertThrows(IllegalArgumentException.class, () -> query(boolVersion, binding(), "query"));
    }
    @Test void observedClearanceRequiresFreshPostAckQueryAndBothIndependentPredicates() {
        Query initial = query(queryNode("initial", context("death_succession_modal", true, true, false), 3, 10), binding(), "initial");
        Close close = close(ackNode("close", 11), binding(), "close");
        Query later = query(queryNode("later", context("none", false, false, false), 4, 12), binding(), "later");
        Clearance actual = compareClearance(initial, close, later);
        assertEquals(ClearanceState.CLEARED_OBSERVED, actual.state());
        assertFalse(actual.naturalDeathProven()); assertFalse(actual.savedContinuationProven()); assertFalse(actual.submissionAuthorized());
        assertFalse(close.replayAuthorized());
        Query stale = query(queryNode("stale", context("none", false, false, false), 3, 11), binding(), "stale");
        assertEquals(ClearanceState.POST_QUERY_NOT_NEWER, compareClearance(initial, close, stale).state());
        for (boolean[] predicates : new boolean[][]{{true, false}, {false, true}, {true, true}}) {
            Query stillBlocked = query(queryNode("still", context("none", predicates[0], predicates[1], false), 4, 12), binding(), "still");
            assertEquals(ClearanceState.MODAL_OR_PREDICATES_UNCLEARED, compareClearance(initial, close, stillBlocked).state());
        }
        assertEquals(ClearanceState.OBSERVATION_REGRESSED,
                compareClearance(initial, close(ackNode("old-close", 9), binding(), "old-close"), later).state());
    }
    @Test void sameNumbersAcrossDifferentEpisodesGameBirthsAndPublicFramesAreNotTheSameObservation() {
        Query initial = query(queryNode("initial", context("death_succession_modal", true, true, false), 1, 10), binding(), "initial");
        Close close = close(ackNode("close", 11), binding(), "close");
        BoundFrame normal = binding();
        Session session = normal.session();
        Session other = new Session(session.machineId(), session.sessionId(), new GameIdentity(1234, "134056180000000002"),
                session.episodeRunId(), session.connectionGeneration(), session.executable(), session.executableFileId(), session.executableMtimeNs());
        for (BoundFrame changed : new BoundFrame[]{new BoundFrame(other, normal.frame(), normal.scene()),
                new BoundFrame(new Session(session.machineId(), session.sessionId(), session.game(), "other-episode", session.connectionGeneration(),
                        session.executable(), session.executableFileId(), session.executableMtimeNs()), normal.frame(), normal.scene()),
                new BoundFrame(session, new Frame("regressed-public", BigInteger.valueOf(899), REVISION, DATE, ACTOR, 0), normal.scene()),
                new BoundFrame(session, normal.frame(), new Scene("{\"instance_id\":42}", "null", java.util.Optional.empty()))}) {
            Query later = query(queryNode("later", context("none", false, false, false), 2, 12), changed, "later");
            assertEquals(ClearanceState.FRAME_CHANGED, compareClearance(initial, close, later).state());
        }
        assertEquals("16888498602938861", session.executableFileId());
        assertEquals("134056180000000001", session.game().creationFiletime());
    }
    @Test void closeAndLaterQueryKeepTheirActualFramesWhenPublicAndNativeRevisionsAdvance() {
        BoundFrame first=binding();
        Query initial=query(queryNode("initial",context("death_succession_modal",true,true,false),1,10),first,"initial");
        BoundFrame closeFrame=new BoundFrame(first.session(),new Frame("close-snapshot",BigInteger.valueOf(901),REVISION,DATE,ACTOR,0),first.scene());
        Close close=close(ackNode("close",11),closeFrame,"close");
        BoundFrame laterFrame=new BoundFrame(first.session(),new Frame("later-snapshot",BigInteger.valueOf(902),REVISION.add(BigInteger.ONE),DATE,ACTOR,0),first.scene());
        ObjectNode laterPacket=queryNode("later",context("none",false,false,false),2,12);
        ((ObjectNode)laterPacket.get("result")).put("snapshot_revision",REVISION.add(BigInteger.ONE));
        ((ObjectNode)laterPacket.path("result").path("current_timeline_blocker_context")).put("snapshot_revision",REVISION.add(BigInteger.ONE));
        Query later=query(laterPacket,laterFrame,"later");
        assertEquals(ClearanceState.CLEARED_OBSERVED,compareClearance(initial,close,later).state());
        assertFalse(sameContinuation(laterFrame,closeFrame));
        assertTrue(sameContinuation(first,closeFrame));
    }
    @Test void reclaimRedRetainsTheRealInnerAckAndStillCannotAuthorizeReplayOrClosure() {
        ObjectNode inner = ackNode("close", 11); ObjectNode outer = reclaim(inner);
        Close red = close(outer, binding(), "close");
        assertEquals(CloseState.SUBMISSION_UNKNOWN, red.state()); assertTrue(red.ack().isPresent());
        assertEquals(BigInteger.valueOf(11), red.ack().orElseThrow().actionObservationRevision());
        assertTrue(red.retainedAckValidationFailure().isEmpty()); assertFalse(red.replayAuthorized());
        Query initial = query(queryNode("initial", context("death_succession_modal", true, true, false), 1, 10), binding(), "initial");
        Query later = query(queryNode("later", context("none", false, false, false), 2, 12), binding(), "later");
        assertEquals(ClearanceState.SUBMISSION_UNKNOWN, compareClearance(initial, red, later).state());
        ((ObjectNode) outer.get("death_succession_close_failure_v1")).put("submitted_ack_frame_exact_json", "{\"ok\":true,\"ok\":true}");
        Close malformed = close(outer, binding(), "close");
        assertEquals(CloseState.SUBMISSION_UNKNOWN, malformed.state()); assertTrue(malformed.ack().isEmpty());
        assertTrue(malformed.retainedAckValidationFailure().isPresent()); assertFalse(malformed.replayAuthorized());
    }
    @Test void noAckGenericRedAndStillOpenAckPreserveUnknownAndPending() {
        ObjectNode red = StrictJson.object(); red.put("type", "command_result").put("protocol_version", 1).put("request_id", "close")
                .put("ok", false).put("error", "application-main death-succession modal continue executor failed");
        Close unknown = close(red, binding(), "close"); assertEquals(CloseState.SUBMISSION_UNKNOWN, unknown.state()); assertTrue(unknown.ack().isEmpty());
        Query initial = query(queryNode("initial", context("death_succession_modal", true, true, false), 1, 10), binding(), "initial");
        Query still = query(queryNode("still", context("death_succession_modal", true, true, false), 2, 12), binding(), "still");
        assertEquals(ClearanceState.MODAL_OR_PREDICATES_UNCLEARED, compareClearance(initial, close(ackNode("close", 11), binding(), "close"), still).state());
        ObjectNode wrong = ackNode("close", 11); ((ObjectNode) wrong.get("result")).put("material_result_verified", true);
        assertThrows(IllegalArgumentException.class, () -> close(wrong, binding(), "close"));
    }
    @Test void byteIdentityAndOriginalEnvelopeBindingAreCheckedBeforeValuesBecomeObservations() {
        byte[] original = bytes(queryNode("original", context("none", false, false, false), 1, 10));
        ExactRef reference = reference(original);
        byte[] changed = original.clone(); changed[0] = '[';
        assertThrows(IllegalArgumentException.class, () -> parseQuery(changed, reference, binding(), "original"));
        assertThrows(IllegalArgumentException.class, () -> parseQuery(original, reference, binding(), "another-request"));
        ObjectNode projected = (ObjectNode) StrictJson.parse(original); projected.put("queried_snapshot_id", "sdk-added");
        assertThrows(IllegalArgumentException.class, () -> query(projected, binding(), "original"));
    }

    static BoundFrame binding() {
        Session session = new Session("synthetic-machine", "fixture-session", new GameIdentity(1234, "134056180000000001"), "actual-successor-episode", "2",
                new ExactRef("D:/fixtures/ck3.exe", 101040248, NativePlayerHeirObservation12004.EXE_SHA256), "16888498602938861", "1791307594040564100");
        ObjectNode snapshot = StrictJson.object(); snapshot.putNull("active_event").putNull("pending_character_interaction").putNull("one_life_terminal_reason");
        return new BoundFrame(session, new Frame("native-31", BigInteger.valueOf(900), REVISION, DATE, ACTOR, 0), Scene.fromSnapshot(snapshot));
    }
    private static Context context(String identity, boolean blocks, boolean open, boolean unavailable) {
        ObjectNode c = StrictJson.object(); c.put("schema", "current-timeline-blocker-context-v1").put("schema_version", 1)
                .put("status", unavailable ? "unavailable" : "available").put("snapshot_revision", REVISION).put("date_raw", DATE).put("identity", unavailable ? "none" : identity);
        c.set("blocks_simulation", typed(blocks, unavailable)); c.set("has_open_succession", typed(open, unavailable));
        c.set("can_continue", typed(!identity.equals("game_over_modal"), unavailable || identity.equals("none")));
        c.putObject("evidence_source").put("kind", unavailable ? "" : "exact-build-stock-gui-plus-native-widget-state")
                .put("path", unavailable ? "" : "game/gui/window_succession_event.gui").put("root_name", unavailable ? "" : identity.equals("none") ? "none" : "succession_event_window")
                .put("decisive_widget_name", unavailable ? "" : identity.equals("none") ? "none" : identity.equals("game_over_modal") ? "menu_button" : "close_button");
        if (unavailable) c.put("unavailable_reason", "native source missing"); else c.putNull("unavailable_reason");
        return parseContext(c, binding().frame());
    }
    private static ObjectNode typed(boolean value, boolean unknown) {
        ObjectNode row = StrictJson.object(); row.put("status", unknown ? "unavailable" : "available");
        if (unknown) row.putNull("value").put("unavailable_reason", "no_supported_timeline_surface_visible");
        else row.put("value", value).putNull("unavailable_reason");
        return row;
    }
    private static ObjectNode queryNode(String request, Context context, long sequence, long observed) {
        ObjectNode envelope = envelope(request); ObjectNode result = envelope.putObject("result");
        result.put("step", QUERY_STEP).put("accepted", true).put("status", context.status() == Status.AVAILABLE ? "available" : "unavailable")
                .put("query_sequence", sequence).put("observation_revision", observed).put("snapshot_revision", REVISION)
                .put("private_build", true).put("read_only", true).put("advertised", false).put("backend_id", "native-headless");
        result.set("current_timeline_blocker_context", StrictJson.parse(encodeContext(context))); return envelope;
    }
    private static ObjectNode ackNode(String request, long observed) {
        ObjectNode envelope = envelope(request); ObjectNode ack = envelope.putObject("result");
        ack.put("step", CLOSE_STEP).put("status", "submitted").put("snapshot_revision", REVISION).put("date_raw", DATE).put("played_character_id", ACTOR)
                .put("action_observation_revision", observed).put("close_invocations", 1).put("material_result_verified", false).put("advertised", false).put("backend_id", "native-headless");
        for (String key : new String[]{"accepted", "identity_verified", "can_continue_verified", "paused_by_succession_verified", "has_open_succession_verified", "controller_vtable_verified", "controller_open_verified", "private_build"}) ack.put(key, true);
        return envelope;
    }
    private static ObjectNode envelope(String request) { return StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", request).put("ok", true); }
    private static ObjectNode reclaim(ObjectNode inner) {
        ObjectNode outer = envelope("close"); outer.put("ok", false).put("error", "application-main death-succession modal continue result was not reclaimable");
        outer.putObject("death_succession_close_failure_v1").put("stage", "reclaim").put("status", "submitted_unconfirmed")
                .put("material_result_verified", false).put("business_material_verified", false).put("reclaim_result_enum", 2)
                .put("submitted_ack_frame_exact_json", new String(bytes(inner), StandardCharsets.UTF_8)); return outer;
    }
    private static Query query(ObjectNode value, BoundFrame frame, String request) { byte[] raw = bytes(value); return parseQuery(raw, reference(raw), frame, request); }
    private static Close close(ObjectNode value, BoundFrame frame, String request) { byte[] raw = bytes(value); return parseClose(raw, reference(raw), frame, request); }
    private static ExactRef reference(byte[] raw) { return new ExactRef("D:/fixtures/native-" + G2RetainedNativeSourceProvider.sha256(raw) + ".json", raw.length, G2RetainedNativeSourceProvider.sha256(raw)); }
    private static JsonNode json(String raw) { return StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8)); }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value, MAX_BYTES); }
    private static ObjectNode copy(JsonNode value) { return (ObjectNode) StrictJson.parse(bytes(value), MAX_BYTES); }
}
