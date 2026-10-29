package org.xar.ck3.control.g2.m7;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Synthetic original semantic fields; no Native/Root token, process, cycle or saved-day qualification. */
class NativeCalendarObservationTest {
    private static final String MACHINE = "synthetic-m7-calendar";
    private static final G2Source SOURCE = new G2Source(MACHINE, "2026-10-23T17:00:00Z", "1.20.0.4-fixture",
            new ExactRef("fixture-only-no-source-authority", 1, "a".repeat(64)));
    private static final BigInteger ACTOR = new BigInteger("-16777215");
    private static final int RAW = CampaignCalendar.dateToRaw("1068.2.28");

    @Test void existingSharedCalendarRetainsNonGregorianFebruaryAndDistinctRevisions() {
        var frame = identity("134371375868945259", "fixture-episode", ACTOR, 27, 31, RAW);
        assertEquals("original-frame-27", frame.frame().snapshotId());
        var semantic = semantic(frame).with("unrelated_native_metric", new OpportunityJson.DecimalValue("1.0"));
        var projected = NativeCalendarObservation.project(frame, SOURCE, semantic);
        assertEquals("1068.2.28", projected.date()); assertEquals(RAW, projected.dateRaw());
        assertEquals(new OpportunityJson.DecimalValue("1.0"), semantic.get("unrelated_native_metric"));
        assertEquals("1068.3.1", NativeCalendarObservation.project(
                identity("134371375868945259", "fixture-episode", ACTOR, 28, 32, RAW + 24), SOURCE,
                semantic(identity("134371375868945259", "fixture-episode", ACTOR, 28, 32, RAW + 24))).date());
        assertNotEquals(frame.frame().revision(), frame.frame().identity().nativeRevision());
    }

    @Test void consumedOriginalFieldsRejectBooleanFloatMissingAndNullTokens() {
        var frame = identity("134371375868945259", "fixture-episode", ACTOR, 27, 31, RAW);
        for (String key : List.of("revision", "native_revision", "date_raw")) {
            for (OpportunityJson.Value invalid : List.of(new OpportunityJson.Bool(true),
                    new OpportunityJson.DecimalValue("1.0"), OpportunityJson.Nil.INSTANCE)) {
                assertThrows(IllegalArgumentException.class,
                        () -> NativeCalendarObservation.project(frame, SOURCE, semantic(frame).with(key, invalid)));
            }
            var missing = new LinkedHashMap<>(semantic(frame).members()); missing.remove(key);
            assertThrows(IllegalArgumentException.class,
                    () -> NativeCalendarObservation.project(frame, SOURCE, new OpportunityJson.Obj(missing)));
        }
    }

    @Test void completeFrameCannotBeReconstructedFromOnlyDateAndActor() {
        var frame = identity("134371375868945259", "fixture-episode", ACTOR, 27, 31, RAW);
        for (String key : List.of("revision", "native_revision", "date_raw")) {
            BigInteger old = OpportunityJson.integer(semantic(frame).get(key), key);
            assertThrows(IllegalArgumentException.class, () -> NativeCalendarObservation.project(frame, SOURCE,
                    semantic(frame).with(key, new OpportunityJson.IntegerValue(old.add(BigInteger.ONE)))));
        }
        for (String key : List.of("episode_run_id", "snapshot_id")) {
            assertThrows(IllegalArgumentException.class, () -> NativeCalendarObservation.project(frame, SOURCE,
                    semantic(frame).with(key, new OpportunityJson.Text("another-frame"))));
        }
        var low24Only = new OpportunityJson.Obj(java.util.Map.of("character_id", new OpportunityJson.IntegerValue(BigInteger.ONE)));
        assertThrows(IllegalArgumentException.class, () -> NativeCalendarObservation.project(frame, SOURCE,
                semantic(frame).with("played_character", low24Only)));
        var crossed = new G2Source("other-machine", SOURCE.observedAtUtc(), SOURCE.exactBuild(), SOURCE.sourceRef());
        assertThrows(IllegalArgumentException.class, () -> NativeCalendarObservation.project(frame, crossed, semantic(frame)));
    }

    @Test void wholeDayPositiveYearProfileRefusesHourOrOverflowInsteadOfTruncating() {
        for (BigInteger invalid : List.of(BigInteger.valueOf(RAW + 1L), BigInteger.valueOf(43_800_000L),
                BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE))) {
            var base = identity("134371375868945259", "fixture-episode", ACTOR, 27, 31, RAW);
            var changed = new ObservationIdentity(MACHINE, base.game(), new JointBudgetSelector.ProposalFrame(
                    new JointBudgetSelector.Frame(ACTOR, BigInteger.valueOf(27), invalid), "original-frame-27",
                    BigInteger.valueOf(31), "fixture-episode"), 1);
            assertThrows(IllegalArgumentException.class, () -> NativeCalendarObservation.project(changed, SOURCE, semantic(changed)));
        }
    }

    @Test void persistenceUsesExactBirthAndRejectsChangedCalendarOrNumericBirth() {
        var frame = identity(StrictJson.UINT64_MAX.toString(), "fixture-episode", ACTOR, 27, 31, RAW);
        var projected = NativeCalendarObservation.project(frame, SOURCE, semantic(frame));
        byte[] bytes = NativeCalendarObservation.encode(projected);
        assertEquals(projected, NativeCalendarObservation.decode(bytes));
        ObjectNode body = (ObjectNode) StrictJson.parse(bytes);
        assertTrue(body.path("identity").path("game").path("creation_filetime").isTextual());
        assertEquals(StrictJson.UINT64_MAX.toString(), body.path("identity").path("game").path("creation_filetime").textValue());
        ObjectNode wrongDate = body.deepCopy(); wrongDate.put("date", "1068.2.29");
        assertThrows(IllegalArgumentException.class, () -> NativeCalendarObservation.decode(StrictJson.canonical(wrongDate)));
        ObjectNode wrongBirth = body.deepCopy(); ((ObjectNode) wrongBirth.path("identity").path("game")).put("creation_filetime", StrictJson.UINT64_MAX);
        assertThrows(IllegalArgumentException.class, () -> NativeCalendarObservation.decode(StrictJson.canonical(wrongBirth)));
    }

    @Test void sameDateDoesNotCollapseOneTickBirthOrNewEpisodeAndIssuesNoCycleCounter() {
        var first = identity("134371375868945259", "fixture-episode", ACTOR, 27, 31, RAW);
        var tick = identity("134371375868945260", "fixture-episode", ACTOR, 27, 31, RAW);
        var episode = identity("134371375868945259", "successor-episode", ACTOR, 27, 31, RAW);
        assertNotEquals(NativeCalendarObservation.project(first, SOURCE, semantic(first)),
                NativeCalendarObservation.project(tick, SOURCE, semantic(tick)));
        assertNotEquals(NativeCalendarObservation.project(first, SOURCE, semantic(first)),
                NativeCalendarObservation.project(episode, SOURCE, semantic(episode)));
        ObjectNode encoded = (ObjectNode) StrictJson.parse(NativeCalendarObservation.encode(
                NativeCalendarObservation.project(first, SOURCE, semantic(first))));
        assertFalse(encoded.has("completed_cycles")); assertFalse(encoded.has("saved_days"));
    }


     @Test void signedNativeActorDomainSurvivesCalendarPersistenceWithoutUnsignedAliases() {
         for (int actor : List.of(Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE)) {
             var frame = identity("134371375868945259", "fixture-episode", BigInteger.valueOf(actor), 27, 31, RAW);
             var projected = NativeCalendarObservation.project(frame, SOURCE, semantic(frame));
             assertEquals(BigInteger.valueOf(actor), projected.identity().frame().identity().player());
             assertEquals(projected, NativeCalendarObservation.decode(NativeCalendarObservation.encode(projected)));
         }
         for (String actor : List.of("-1", "2147483648", "4294967295", "-2147483649")) {
             assertThrows(IllegalArgumentException.class, () -> {
                 var frame = identity("134371375868945259", "fixture-episode", new BigInteger(actor), 27, 31, RAW);
                 NativeCalendarObservation.project(frame, SOURCE, semantic(frame));
             });
         }
     }
 
    private static ObservationIdentity identity(String birth, String episode, BigInteger actor, int nativeRevision,
            int publicRevision, int raw) {
        return new ObservationIdentity(MACHINE, new GameGeneration(17, new PythonOnlyUInt64(new BigInteger(birth))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor, BigInteger.valueOf(nativeRevision),
                        BigInteger.valueOf(raw)), "original-frame-" + nativeRevision, BigInteger.valueOf(publicRevision), episode), 1);
    }
    private static OpportunityJson.Obj semantic(ObservationIdentity value) {
        var frame = value.frame(); var nativeFrame = frame.identity();
        return new OpportunityJson.Obj(java.util.Map.of("snapshot_id", new OpportunityJson.Text(frame.snapshotId()),
                "episode_run_id", new OpportunityJson.Text(frame.episodeRunId()),
                "revision", new OpportunityJson.IntegerValue(frame.revision()),
                "native_revision", new OpportunityJson.IntegerValue(nativeFrame.nativeRevision()),
                "date_raw", new OpportunityJson.IntegerValue(nativeFrame.dateRaw()),
                "played_character", new OpportunityJson.Obj(java.util.Map.of("character_id", new OpportunityJson.IntegerValue(nativeFrame.player())))));
    }
}
