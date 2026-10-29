package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original Service argument/frame contract; software DATA never grants H2743 read authority. */
final class PublicPlanningCodecTest {
    static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    static PublicBindings.Arguments args(String value) { return PublicBindings.present(raw(value)); }
    static String frame(String revision) {
        String snapshotRevision = revision.startsWith("\"") ? revision.substring(1, revision.length()-1) : revision;
        return "{\"snapshot_id\":\"native:" + snapshotRevision + "\",\"revision\":" + revision + ",\"native_revision\":" + revision
                + ",\"date_raw\":53217264,\"actor_character_id\":29829,\"episode_run_id\":\"native-29829-2bc2d599f7f9\",\"war_id\":16777231,\"connection_generation\":1}";
    }
    static String special(String revision) {
        return "{\"step\":\"" + PublicPlanningCodec.H2743_STEP + "\",\"expected_revision\":" + revision + ",\"expected_h2743_frame\":" + frame(revision) + "}";
    }
    static String snapshot(String revision) {
        return "{\"snapshot_id\":\"native:" + revision + "\",\"revision\":" + revision + ",\"native_revision\":" + revision
                + ",\"date_raw\":53217264,\"episode_run_id\":\"native-29829-2bc2d599f7f9\",\"paused\":true,\"map_ready\":true,"
                + "\"played_character\":{\"character_id\":29829,\"alive\":true},\"diagnostics\":{\"connection_generation\":1},"
                + "\"player_armies\":[],\"active_wars\":[{\"war_id\":16777231,\"player_side\":\"defender\",\"player_is_primary_war_leader\":true,\"primary_opponent_character_id\":30097,\"targeted_title_ids\":[2128]}]}";
    }
    static PlanningRequest original(String snapshot, BigInteger revision) {
        var game = new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100)));
        var before = new ObservationIdentity("software-planning-codec", game, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829), revision, BigInteger.valueOf(53217264)),
                "native:" + revision, revision, "native-29829-2bc2d599f7f9"), 1);
        var source = new G2Source(before.machineId(), "2026-10-24T00:00:00Z", "software-only", new ExactRef("software-source", 1, "a".repeat(64)));
        var observations = new PlanningObservation((OpportunityJson.Obj) OpportunityJson.parse(snapshot.getBytes(StandardCharsets.UTF_8)),
                List.of(), Set.of(new OperationKey("pause-map")), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, source, "original-software-session", Instant.parse("2026-10-24T00:01:00Z"), observations);
    }
    @Test void planHasOnlyItsOriginalEmptyArgumentObjectAndNoNullAlias() {
        assertEquals(new PublicPlanningCodec.PlanRequest(), PublicPlanningCodec.decodePlan(new PublicBindings.Missing()));
        assertEquals(new PublicPlanningCodec.PlanRequest(), PublicPlanningCodec.decodePlan(args("{}")));
        for (String bad : List.of("null", "[]", "{\"nonwar_only\":false}", "{\"revision\":1}"))
            assertThrows(IllegalArgumentException.class, () -> PublicPlanningCodec.decodePlan(args(bad)), bad);
    }
    @Test void optionalOriginalRevisionAndFramePreserveAllThreePresenceStates() {
        for (String input : List.of("{\"step\":\"pause-map\"}", "{\"step\":\"pause-map\",\"expected_revision\":null}",
                "{\"step\":\"pause-map\",\"expected_revision\":1,\"expected_h2743_frame\":null}")) {
            var decoded = PublicPlanningCodec.decodeExecute(args(input));
            var encoded = PublicPlanningCodec.encodeExecute(decoded);
            assertEquals(decoded, PublicPlanningCodec.decodeExecute(PublicBindings.present(encoded)));
            if (decoded.expectedRevision() instanceof PublicPlanningCodec.RevisionValue value)
                assertEquals(value.value().toString(), StrictJson.parse(encoded.bytes()).path("expected_revision").textValue());
            else assertEquals(StrictJson.parse(input.getBytes(StandardCharsets.UTF_8)), StrictJson.parse(encoded.bytes()));
        }
        assertInstanceOf(PublicPlanningCodec.RevisionMissing.class, PublicPlanningCodec.decodeExecute(args("{\"step\":\"pause-map\"}")).expectedRevision());
        assertInstanceOf(PublicPlanningCodec.RevisionNull.class, PublicPlanningCodec.decodeExecute(args("{\"step\":\"pause-map\",\"expected_revision\":null}")).expectedRevision());
    }
    @Test void wrongFieldsTypesDuplicatesAndNonIntegerRevisionsFailBeforeAConsumer() {
        for (String value : List.of("true", "1.0", "\"01\"", "\"+1\"", "\"1.0\"", "-1", "9007199254740992", "18446744073709551616", "[]"))
            assertThrows(IllegalArgumentException.class, () -> PublicPlanningCodec.decodeExecute(args("{\"step\":\"pause-map\",\"expected_revision\":" + value + "}")), value);
        for (String input : List.of("{}", "[]", "null", "{\"step\":true}", "{\"step\":\"pause-map\",\"revision\":1}",
                "{\"step\":\"pause-map\",\"step\":\"resume-map\"}"))
            assertThrows(IllegalArgumentException.class, () -> PublicPlanningCodec.decodeExecute(args(input)), input);
    }
    @Test void fullUnsignedRevisionSurvivesOriginalInputSerdeAndActualFrameConsumer() {
        String max = StrictJson.UINT64_MAX.toString(); var request = PublicPlanningCodec.decodeExecute(args(special("\"" + max + "\"")));
        assertEquals(request, PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicPlanningCodec.encodeExecute(request))));
        request.requireCurrent(original(snapshot(max), StrictJson.UINT64_MAX));
        assertThrows(IllegalArgumentException.class, () -> PublicPlanningCodec.decodeExecute(args(special(max))));
        for (String value : List.of("0", "-1", "true", "1.0", "18446744073709551616"))
            assertThrows(IllegalArgumentException.class, () -> request.requireCurrent(original(snapshot(value), StrictJson.UINT64_MAX)), value);
        assertThrows(IllegalArgumentException.class, () -> request.requireCurrent(original(snapshot(max), BigInteger.ONE)));
    }
    @Test void originalGenericZeroRevisionIsAcceptedAsInputThenRejectedAgainstTheActualPositiveFrame() {
        var decoded = PublicPlanningCodec.decodeExecute(args("{\"step\":\"pause-map\",\"expected_revision\":0}"));
        assertEquals(new PublicPlanningCodec.RevisionValue(BigInteger.ZERO), decoded.expectedRevision());
        assertEquals(decoded, PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicPlanningCodec.encodeExecute(decoded))));
        assertThrows(IllegalArgumentException.class, () -> decoded.requireCurrent(original(snapshot("1"), BigInteger.ONE)));
    }
    @Test void h2743PreflightKeepsTheOriginalTypedBeforeFrameFailure() {
        for (String input : List.of("{\"step\":\"" + PublicPlanningCodec.H2743_STEP + "\"}",
                special("1").replace("\"expected_revision\":1", "\"expected_revision\":null"),
                special("1").replace(PublicPlanningCodec.H2743_STEP, "pause-map"),
                special("1").replace("\"expected_revision\":1", "\"expected_revision\":true"),
                special("1").replace("\"expected_revision\":1", "\"expected_revision\":1.0"))) {
            var failure=assertThrows(PublicServiceFailure.class,()->PublicPlanningCodec.decodeExecute(args(input)),input);
            assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());
            assertEquals("H2743 read-only query requires an explicit before-frame claim",failure.getMessage());
        }
    }
    @Test void malformedH2743FrameStillCannotReachAConsumer() {
        for(String input:List.of(special("1").replace("\"war_id\":16777231","\"war_id\":false"),
                special("1").replace("\"connection_generation\":1","\"connection_generation\":1.0"),
                special("1").replace("\"snapshot_id\"","\"frame_id\"")))
            assertThrows(IllegalArgumentException.class,()->PublicPlanningCodec.decodeExecute(args(input)),input);
    }
    @Test void actualH2743ConsumerRequiresOriginalPartiesTitleAndPausedEpisode() {
        var caller = PublicPlanningCodec.decodeExecute(args(special("1")));
        caller.requireCurrent(original(snapshot("1"), BigInteger.ONE));
        for (String bad : List.of(snapshot("1").replace("\"paused\":true", "\"paused\":false"), snapshot("1").replace("\"map_ready\":true", "\"map_ready\":false"),
                snapshot("1").replace("\"alive\":true", "\"alive\":false"), snapshot("1").replace("\"primary_opponent_character_id\":30097", "\"primary_opponent_character_id\":30098"),
                snapshot("1").replace("\"targeted_title_ids\":[2128]", "\"targeted_title_ids\":[2129]"), snapshot("1").replace("\"date_raw\":53217264", "\"date_raw\":53217265"),
                snapshot("1").replace("\"war_id\":16777231", "\"war_id\":true")))
            assertThrows(IllegalArgumentException.class, () -> caller.requireCurrent(original(bad, BigInteger.ONE)), bad);
    }
}
