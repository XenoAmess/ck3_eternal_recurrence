package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.Episode;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Actual pure body producer -> serde -> existing FamilyDomainSource and episode consumers.
 * Synthetic physical/source references are fixture DATA and grant no private lifecycle proof or writer. */
final class FamilyNaturalEpisodeMigrationTest {
    private static final List<Slot> SLOTS = List.of(Slot.FAMILY, Slot.CHILD_MATRILINEAL, Slot.DEFAULT_MARRIAGE);
    private static final SessionIdentity OWNER = owner(123, "same-physical-session", 1);
    private static final Episode BEFORE = new Episode("predecessor-episode", BigInteger.valueOf(101));
    private static final Episode AFTER = new Episode("successor-episode", BigInteger.valueOf(202));

    @Test void sameGameNaturalPublicationPreservesAllThreeFullBodiesAndUnknownOriginalRecordsWithoutReplaying() {
        for (Slot slot : SLOTS) {
            byte[] original = original(slot); var transition = transition(original, BEFORE, AFTER);
            byte[] output = FamilyNaturalEpisodeMigration.derive(slot, original, transition);
            var consumed = FamilyDomainSource.validate(slot, output); JsonNode body = DriverJson.toNode(consumed), prior = StrictJson.parse(original);
            assertTrue(body.get("pending").isNull()); assertTrue(body.get("resolved").isNull());
            assertEquals(prior.get("extension"), body.get("extension")); assertEquals(prior.get("episode_history").get(0), body.get("episode_history").get(0));
            JsonNode archived = body.get("episode_history").get(1);
            assertEquals(prior.get("pending"), archived.get("pending")); assertEquals(prior.get("resolved"), archived.get("resolved"));
            assertEquals("retained_original_unresolved_no_replay", archived.get("pending_status").textValue());
            assertFalse(archived.get("ck3_command_submitted").booleanValue()); assertFalse(archived.get("relation_completion_credit").booleanValue());
            assertEquals(transition, FamilyNaturalEpisodeMigration.Transition.fromJson(body.get(FamilyNaturalEpisodeMigration.FIELD)));
            assertDoesNotThrow(() -> FamilyNextEpisodeMigration.requireCurrent(consumed, request(OWNER, AFTER)));
            assertThrows(IllegalArgumentException.class, () -> FamilyNextEpisodeMigration.requireCurrent(consumed, request(OWNER, BEFORE)));
            assertEquals(consumed, FamilyDomainSource.validate(slot, DriverJson.encode(consumed)));
        }
    }

    @Test void naturalTransitionSerdeRejectsMissingNullForeignFieldsBooleanIdsAndSameActorEpisode() {
        byte[] original = original(Slot.FAMILY); var transition = transition(original, BEFORE, AFTER);
        assertEquals(transition, FamilyNaturalEpisodeMigration.Transition.fromJson(StrictJson.parse(StrictJson.canonical(transition.toJson()))));
        for (String field : List.of("owner", "before_episode", "after_episode", "lifecycle_material", "previous_body")) {
            ObjectNode missing = transition.toJson(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.Transition.fromJson(missing));
            ObjectNode nullable = transition.toJson(); nullable.putNull(field);
            assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.Transition.fromJson(nullable));
        }
        ObjectNode extra = transition.toJson(); extra.put("alias", true);
        assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.Transition.fromJson(extra));
        ObjectNode bool = transition.toJson(); object(bool.get("after_episode")).put("played_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.Transition.fromJson(bool));
        assertThrows(IllegalArgumentException.class, () -> transition(original, BEFORE, new Episode(BEFORE.runId(), AFTER.player())));
        assertThrows(IllegalArgumentException.class, () -> transition(original, BEFORE, new Episode(AFTER.runId(), BEFORE.player())));
    }

    @Test void originalPinAndExactCurrentBodyAreRequiredForPartialThreeSlotResume() {
        for (Slot slot : SLOTS) {
            byte[] original = original(slot); var transition = transition(original, BEFORE, AFTER);
            byte[] expected = FamilyNaturalEpisodeMigration.derive(slot, original, transition);
            assertDoesNotThrow(() -> FamilyNaturalEpisodeMigration.requireCompatibleCurrent(slot, original, original, transition));
            assertDoesNotThrow(() -> FamilyNaturalEpisodeMigration.requireCompatibleCurrent(slot, original, expected, transition));
            ObjectNode changed = object(StrictJson.parse(expected)); changed.put("later_business_change", true);
            byte[] mutated = StrictJson.canonical(changed);
            assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.requireCompatibleCurrent(slot, original, mutated, transition));
            var foreign = new FamilyNaturalEpisodeMigration.Transition(OWNER, BEFORE, AFTER, reference("another-lifecycle", new byte[]{9}), reference("original", original));
            assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.requireCompatibleCurrent(slot, original, expected, foreign));
            ObjectNode wrong = object(StrictJson.parse(original)); object(wrong.get("pending")).put("episode_run_id", "unrelated");
            byte[] bad = StrictJson.canonical(wrong);
            assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.derive(slot, bad, transition(bad, BEFORE, AFTER)));
            wrong = object(StrictJson.parse(original)); wrong.remove("pending"); byte[] absent = StrictJson.canonical(wrong);
            assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.derive(slot, absent, transition(absent, BEFORE, AFTER)));
            wrong = object(StrictJson.parse(original)); wrong.putNull("episode_history"); byte[] nullHistory = StrictJson.canonical(wrong);
            assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.derive(slot, nullHistory, transition(nullHistory, BEFORE, AFTER)));
        }
    }

    @Test void naturalAfterNextArchivesTheOldMarkerAndRepeatedNaturalSuccessionKeepsAllHistory() {
        for (Slot slot : SLOTS) {
            byte[] original = original(slot); var intermediate = new Episode("intermediate-episode", BigInteger.valueOf(151));
            var previousOwner = owner(99, "previous-physical-session", 2);
            var next = new FamilyNextEpisodeMigration.Transition(previousOwner, OWNER, BEFORE, intermediate,
                    reference("baseline", new byte[]{3}), reference("original", original));
            byte[] initialized = FamilyNextEpisodeMigration.derive(slot, original, next);
            var natural = transition(initialized, intermediate, AFTER);
            byte[] output = FamilyNaturalEpisodeMigration.derive(slot, initialized, natural); JsonNode body = StrictJson.parse(output);
            assertFalse(body.has(FamilyNextEpisodeMigration.FIELD)); assertEquals(3, body.get("episode_history").size());
            assertArrayEquals(StrictJson.canonical(next.toJson()),
                    StrictJson.canonical(body.get("episode_history").get(2).get("previous_next_episode_binding")));
            var later = new Episode("third-episode", BigInteger.valueOf(303));
            byte[] third = FamilyNaturalEpisodeMigration.derive(slot, output, transition(output, AFTER, later));
            assertEquals(4, StrictJson.parse(third).get("episode_history").size());
            assertDoesNotThrow(() -> FamilyNextEpisodeMigration.requireCurrent(FamilyDomainSource.validate(slot, third), request(OWNER, later)));
            assertThrows(IllegalArgumentException.class, () -> FamilyNaturalEpisodeMigration.derive(slot, output, transition(output, BEFORE, later)));
        }
    }

    @Test void laterPhysicalNextConsumesNaturalBindingButNeverAcceptsAStaleOrConflictingOwnerMarker() {
        byte[] original = original(Slot.DEFAULT_MARRIAGE); var natural = transition(original, BEFORE, AFTER);
        byte[] output = FamilyNaturalEpisodeMigration.derive(Slot.DEFAULT_MARRIAGE, original, natural);
        var nextOwner = owner(456, "next-physical-session", 3); var nextEpisode = new Episode("physical-next-episode", BigInteger.valueOf(404));
        var next = new FamilyNextEpisodeMigration.Transition(OWNER, nextOwner, AFTER, nextEpisode,
                reference("next-baseline", new byte[]{4}), reference("natural-output", output));
        byte[] nextBody = FamilyNextEpisodeMigration.derive(Slot.DEFAULT_MARRIAGE, output, next);
        JsonNode decoded = StrictJson.parse(nextBody); assertFalse(decoded.has(FamilyNaturalEpisodeMigration.FIELD));
        assertArrayEquals(StrictJson.canonical(natural.toJson()),
                StrictJson.canonical(decoded.get("episode_history").get(2).get("previous_natural_episode_binding")));
        var consumed = FamilyDomainSource.validate(Slot.DEFAULT_MARRIAGE, nextBody);
        assertDoesNotThrow(() -> FamilyNextEpisodeMigration.requireCurrent(consumed, request(nextOwner, nextEpisode)));
        assertThrows(IllegalArgumentException.class, () -> FamilyNextEpisodeMigration.requireCurrent(FamilyDomainSource.validate(Slot.DEFAULT_MARRIAGE, output), request(nextOwner, AFTER)));
        ObjectNode conflicting = object(StrictJson.parse(output)); conflicting.set(FamilyNextEpisodeMigration.FIELD, next.toJson());
        var invalid = FamilyDomainSource.validate(Slot.DEFAULT_MARRIAGE, StrictJson.canonical(conflicting));
        assertThrows(IllegalArgumentException.class, () -> FamilyNextEpisodeMigration.requireCurrent(invalid, request(OWNER, AFTER)));
    }

    @Test void signedNaturalMarkersContinueThroughNextAndOrdinaryRestoreWithoutReplayingUnknownHistory() {
        for(Slot slot:SLOTS)for(long actor:List.of((long)Integer.MIN_VALUE,-2L,0L,(long)Integer.MAX_VALUE)) {
            byte[] original=original(slot);var after=new Episode("signed-successor-"+actor,BigInteger.valueOf(actor));
            var natural=transition(original,BEFORE,after);byte[] output=FamilyNaturalEpisodeMigration.derive(slot,original,natural);
            var consumed=FamilyDomainSource.validate(slot,output);JsonNode body=DriverJson.toNode(consumed),prior=StrictJson.parse(original);
            assertEquals(natural,FamilyNaturalEpisodeMigration.Transition.fromJson(StrictJson.parse(StrictJson.canonical(natural.toJson()))));
            JsonNode archived=body.get("episode_history").get(1);
            assertEquals(prior.get("pending"),archived.get("pending"));assertEquals(prior.get("resolved"),archived.get("resolved"));
            assertEquals("retained_original_unresolved_no_replay",archived.get("pending_status").textValue());
            assertFalse(archived.get("ck3_command_submitted").booleanValue());assertFalse(archived.get("relation_completion_credit").booleanValue());
            assertTrue(body.get("pending").isNull());assertTrue(body.get("resolved").isNull());
            assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCurrent(consumed,request(OWNER,after)));
            assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(consumed,request(OWNER,BEFORE)));
            var nextOwner=owner(456,"signed-next-session",3);var nextEpisode=new Episode("signed-next-"+actor,BigInteger.valueOf(-303));
            var next=new FamilyNextEpisodeMigration.Transition(OWNER,nextOwner,after,nextEpisode,
                    reference("signed-next-baseline",new byte[]{4}),reference("signed-natural-output",output));
            byte[] nextBody=FamilyNextEpisodeMigration.derive(slot,output,next);
            assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCurrent(FamilyDomainSource.validate(slot,nextBody),request(nextOwner,nextEpisode)));
            var restoredOwner=owner(789,"signed-restored-session",4);
            var restore=new FamilyOrdinaryRestoreMigration.Transition(nextOwner,nextOwner,restoredOwner,nextEpisode,
                    reference("saved-material",new byte[]{5}),reference("restoration-basis",new byte[]{6}),
                    reference("saved-body",nextBody),reference("previous-body",nextBody));
            byte[] restored=FamilyOrdinaryRestoreMigration.derive(slot,nextBody,nextBody,restore);
            JsonNode restoredBody=StrictJson.parse(restored),previous=StrictJson.parse(nextBody);
            for(String field:List.of("pending","resolved","episode_history"))assertEquals(previous.get(field),restoredBody.get(field));
            var restoredDocument=FamilyDomainSource.validate(slot,restored);
            assertDoesNotThrow(()->FamilyOrdinaryRestoreMigration.requireCurrent(restoredDocument,request(restoredOwner,nextEpisode)));
            assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCurrent(restoredDocument,request(restoredOwner,nextEpisode)));
            assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(restoredDocument,request(nextOwner,nextEpisode)));
            assertEquals(restore,FamilyOrdinaryRestoreMigration.Transition.fromJson(restoredBody.get(FamilyOrdinaryRestoreMigration.HISTORY).get(0).get("transition")));
        }
    }

    @Test void preservedPlayerDataRetainsUnsignedHistoryWhileCurrentPlayersRequireStrictNativeIdentity() {
        BigInteger legacy=new BigInteger("4294967294"),signed=BigInteger.valueOf(-2);
        assertEquals(legacy,FamilyNextEpisodeMigration.preservedPlayer(StrictJson.object().put("id",legacy).get("id")));
        assertEquals(legacy,new Episode("legacy-data",legacy).player());
        assertEquals(signed,FamilyNextEpisodeMigration.preservedPlayer(signed));assertNotEquals(legacy,signed);
        assertEquals(signed,FamilyNextEpisodeMigration.currentPlayer(StrictJson.object().put("id",-2).get("id")));
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.currentPlayer(StrictJson.object().put("id",legacy).get("id")));
        var transition=transition(original(Slot.DEFAULT_MARRIAGE),BEFORE,new Episode("legacy-data",legacy));
        assertEquals(legacy,FamilyNaturalEpisodeMigration.Transition.fromJson(StrictJson.parse(StrictJson.canonical(transition.toJson()))).after().player());
        for(String token:List.of("true","1.0","\"-2\"","null","-1","-2147483649","4294967295")) {
            JsonNode value=StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.preservedPlayer(value),token);
            assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.currentPlayer(value),token);
        }
    }


    private static FamilyNaturalEpisodeMigration.Transition transition(byte[] original, Episode before, Episode after) {
        return new FamilyNaturalEpisodeMigration.Transition(OWNER, before, after, reference("actual-lifecycle-fixture", new byte[]{1}), reference("original", original));
    }
    private static byte[] original(Slot slot) {
        ObjectNode value = StrictJson.object().put("schema", FamilyDomainSource.schema(slot));
        for (String field : List.of("pending", "resolved")) value.putObject(field).put("episode_run_id", BEFORE.runId())
                .put("played_character_id", BEFORE.player()).put("heir_character_id", 11).put("candidate_character_id", 12)
                .put("source_bridge_pid", 77).put("source_bridge_creation_date", "fixture-bridge").put("pre_native_revision", 1)
                .put("unknown_original_extension", "retained");
        value.putObject("extension").put("keep", false).putArray("values").addNull().add(7);
        value.putArray("episode_history").addObject().put("source", "retained-prior-history");
        return StrictJson.canonical(value);
    }
    private static ObjectNode object(JsonNode value) { if (!(value instanceof ObjectNode object)) throw new IllegalArgumentException("fixture JSON object required"); return object; }
    private static ExactRef reference(String name, byte[] bytes) { return new ExactRef("D:/synthetic-family-natural/" + name, bytes.length, ActionCodec.sha256(bytes)); }
    private static SessionIdentity owner(long pid, String session, long birth) { return new SessionIdentity("fixture-family-natural-machine", new GameGeneration(pid, new PythonOnlyUInt64(BigInteger.valueOf(birth))), session); }
    private static PlanningRequest request(SessionIdentity owner, Episode episode) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(episode.player(), BigInteger.ONE, BigInteger.ONE), "fixture", BigInteger.ONE, episode.runId());
        var identity = new ObservationIdentity(owner.machineId(), owner.game(), frame, 1);
        ObjectNode snapshot = StrictJson.object().put("snapshot_id", frame.snapshotId()).put("revision", frame.revision())
                .put("native_revision", frame.identity().nativeRevision()).put("date_raw", frame.identity().dateRaw())
                .put("episode_run_id", episode.runId()).put("paused", true).put("map_ready", true);
        snapshot.putObject("played_character").put("character_id", episode.player());
        snapshot.putArray("active_wars"); snapshot.putArray("player_armies");
        return new PlanningRequest(identity, new G2Source(owner.machineId(), "2026-10-25T00:00:00Z", "fixture-build", reference("source", new byte[]{1})), owner.sessionId(),
                Instant.parse("2099-01-01T00:00:00Z"), new PlanningObservation(DriverJson.object(StrictJson.canonical(snapshot), DriverJson.MAX_NATIVE_BYTES),
                List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
}
