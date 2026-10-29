package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.LifecycleIdentityCodec;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.LifecyclePublicResultCodec;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.action.LifecycleOriginFactory;
import org.xar.ck3.control.application.lifecycle.DeathSettlement;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.lifecycle.LifecycleReducer;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure software tests call the real shared reducer, then both public serialization directions. */
final class LifecyclePublicResultCodecTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final BigInteger FULL64 = new BigInteger("18446744073709551615");
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(FULL64));

    @Test void actualDeathProducerRetainsFullRevisionAndOrdinaryCountersAcrossPublicRoundtrip() {
        var actual = LifecycleReducer.death(snapshot(false, FULL64), null,
                new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD, false,
                        Optional.empty(), List.of()), NOW);
        var original = new RawJson(actual.result());
        var encoded = LifecyclePublicResultCodec.encode(Kind.DEATH, original);
        var wire = object(encoded);
        assertEquals(FULL64.toString(), wire.path("revision").textValue());
        assertTrue(wire.path("episode_character_id").isIntegralNumber());
        assertTrue(wire.path("date_raw").isIntegralNumber());
        assertTrue(wire.path("heir_gameplay_actions").isIntegralNumber());
        assertTrue(wire.path("score").isNull());
        assertEquals(object(original), object(LifecyclePublicResultCodec.decode(Kind.DEATH, encoded)));
        assertTrue(object(original).path("revision").isIntegralNumber());
        assertTrue(actual.driver().commandHistory().getLast().originalRow().json().length > 0);
    }

    @Test void actualMatchedSuccessorProducerConvertsOnlyFiveRevisionRolesAndKeepsItsOriginalProofData() {
        // Requires the shared GoalCodec BigInteger binding fix; the old safe-long consumer rejects this producer.
        var actual = LifecycleReducer.continueSuccessor(snapshot(true, FULL64), "episode-successor", NOW);
        var original = new RawJson(actual.result());
        var encoded = LifecyclePublicResultCodec.encode(Kind.CONTINUE_SUCCESSOR, original);
        var wire = object(encoded); var reconciliation = wire.path("succession_reconciliation");
        assertEquals(FULL64.toString(), wire.path("revision").textValue());
        for (String side : List.of("predecessor_binding", "successor_binding")) {
            assertEquals(FULL64.toString(), reconciliation.path(side).path("revision").textValue());
            assertEquals(FULL64.toString(), reconciliation.path(side).path("native_revision").textValue());
            assertTrue(reconciliation.path(side).path("date_raw").isIntegralNumber());
        }
        assertTrue(reconciliation.path("predecessor_character_id").isIntegralNumber());
        assertTrue(reconciliation.path("matched_inherited_title_ids").get(0).isIntegralNumber());
        var restored = LifecyclePublicResultCodec.decode(Kind.CONTINUE_SUCCESSOR, encoded);
        assertEquals(object(original), object(restored));
        assertEquals(OrdinaryCampaignGoal.Verdict.MATCHED,
                GoalCodec.decodeReconciliation(McpJson.encode(object(restored).get("succession_reconciliation"))).verdict());
        assertEquals("episode-successor", actual.driver().session().episodeRunId());
    }

    @Test void decoderRejectsWrongMissingAndNoncanonicalTypedRolesAndNeverGuessesOtherFields() {
        var actual = LifecycleReducer.continueSuccessor(snapshot(true, BigInteger.valueOf(41)), "episode-successor", NOW);
        var original = new RawJson(actual.result());
        var publicResult = LifecyclePublicResultCodec.encode(Kind.CONTINUE_SUCCESSOR, original);
        for (int variant = 0; variant < 7; variant++) {
            var wrong = object(publicResult);
            var binding = (ObjectNode) wrong.path("succession_reconciliation").path("successor_binding");
            switch (variant) {
                case 0 -> binding.remove("revision");
                case 1 -> binding.putNull("revision");
                case 2 -> binding.put("revision", true);
                case 3 -> binding.put("revision", 41);
                case 4 -> binding.put("revision", "041");
                case 5 -> binding.put("revision", "-1");
                case 6 -> binding.put("revision", "41.0");
                default -> throw new AssertionError();
            }
            assertThrows(IllegalArgumentException.class, () -> LifecyclePublicResultCodec.decode(
                    Kind.CONTINUE_SUCCESSOR, new RawJson(McpJson.encode(wrong))));
        }
        var extension = object(original); extension.putObject("unrelated").put("revision", FULL64);
        assertThrows(IllegalArgumentException.class, () -> LifecyclePublicResultCodec.encode(
                Kind.CONTINUE_SUCCESSOR, new RawJson(McpJson.encode(extension))));
        var textExtension = object(original); textExtension.putObject("unrelated").put("revision", "041");
        var roundtrip = LifecyclePublicResultCodec.decode(Kind.CONTINUE_SUCCESSOR,
                LifecyclePublicResultCodec.encode(Kind.CONTINUE_SUCCESSOR, new RawJson(McpJson.encode(textExtension))));
        assertEquals("041", object(roundtrip).path("unrelated").path("revision").textValue());
    }

    @Test void deathMissingAndNullRemainDifferentAndNextEpisodeCountersRemainNumbers() {
        var absent = McpJson.object().put("terminal", true);
        var explicit = absent.deepCopy(); explicit.putNull("revision");
        assertFalse(object(LifecyclePublicResultCodec.encode(Kind.DEATH, raw(absent))).has("revision"));
        assertTrue(object(LifecyclePublicResultCodec.encode(Kind.DEATH, raw(explicit))).path("revision").isNull());
        var next = McpJson.object().put("previous_pid", 123).put("resumed_pid", 124)
                .put("episode_character_id", 73).put("date_raw", 240);
        var encoded = LifecyclePublicResultCodec.encode(Kind.NEXT_EPISODE, raw(next));
        assertEquals(object(raw(next)), object(encoded));
        var unsafe = next.deepCopy().put("unexpected_full_width", FULL64);
        assertThrows(IllegalArgumentException.class,
                () -> LifecyclePublicResultCodec.encode(Kind.NEXT_EPISODE, raw(unsafe)));
    }

    @Test void autoPublicParserConsumesTheSameTypedLifecycleCodecAndRejectsNumericSmallRevision() {
        var observed = snapshot(true, BigInteger.valueOf(41));
        var actual = LifecycleReducer.continueSuccessor(observed, "episode-successor", NOW);
        var source = new LifecycleIdentity("fixture-machine", GAME, "fixture-session", BigInteger.ONE,
                new LifecycleIdentity.Subject(BigInteger.valueOf(73), "episode-original", 1, 1),
                new LifecycleIdentity.Frame("fixture-native:41", BigInteger.valueOf(41), BigInteger.valueOf(41),
                        BigInteger.valueOf(240), true, true),
                new LifecycleIdentity.Character(BigInteger.valueOf(74), true), LifecycleIdentity.TerminalReason.CHANGED,
                new LifecycleIdentity.Evidence(observed.originalEvidence(), ref(bytes("hello")), ref(bytes("manifest")),
                        observed.facts().originalHistoryBasis(), ref(bytes("qualification"))), NOW);
        var wire = McpJson.object().put("status", "observed")
                .put("selected_step", LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR.key().value())
                .put("snapshot_id", "fixture-native:41").put("revision", "41");
        wire.putNull("plan"); wire.putNull("planning_source_frame");
        wire.set("lifecycle_source_frame", LifecycleIdentityCodec.encode(source));
        wire.set("result", McpJson.parse(LifecyclePublicResultCodec.encode(Kind.CONTINUE_SUCCESSOR,
                new RawJson(actual.result())).bytes()));
        assertArrayEquals(raw(wire).bytes(), McpAutoTurnEncoder.parse(raw(wire)).original().bytes());
        var wrong = wire.deepCopy();
        ((ObjectNode) wrong.path("result").path("succession_reconciliation").path("predecessor_binding"))
                .put("revision", 41);
        assertThrows(IllegalArgumentException.class, () -> McpAutoTurnEncoder.parse(raw(wrong)));
    }

    @Test void actualDeathHistoryAndFramedSnapshotUseTheSamePublicCodecAndRestoreOriginalNumericHistory() {
        var observed = snapshot(false, FULL64);
        var actual = LifecycleReducer.death(observed,
                DeathSettlement.normalize(OpportunityJson.toNode(observed.semantic().get("one_life_settlement"))).orElseThrow(),
                new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD, false,
                        Optional.empty(), List.of()), NOW);
        var frame = observed.actual();
        var facts = new DriverObservationFacts(actual.driver(), 3, 7, frame.session(), frame.snapshotId(),
                frame.nativeRevision(), DriverJson.sha256(frame.state().bytes()), FULL64, 2,
                observed.source(), actual.auxiliary(), ref(bytes("actual post-reducer facts")));
        var full = new DriverObservationAssembler().projectFull(frame, facts, observed.originalEvidence());
        var source = assertInstanceOf(LifecycleOriginFactory.Projected.class, LifecycleOriginFactory.project(full,
                ref(bytes("actual hello")), ref(actual.driver().encode()), ref(bytes("actual qualification"))));
        var publicSnapshot = PublicSnapshotCodec.encodeTerminal(full, source.identity(), true);
        var wire = object(publicSnapshot);
        assertEquals(FULL64.toString(), wire.path("native_command_history").get(0).path("result").path("revision").textValue());
        assertEquals(FULL64.toString(), wire.path("scored_terminal").path("revision").textValue());
        assertTrue(wire.path("native_command_history").get(0).path("result").path("episode_character_id").isIntegralNumber());
        var restored = PublicSnapshotCodec.decode(publicSnapshot);
        assertEquals(full.semantic(), restored);
        var originalHistory = OpportunityJson.array(restored.get("native_command_history"), "actual history");
        assertInstanceOf(OpportunityJson.IntegerValue.class,
                OpportunityJson.object(OpportunityJson.object(originalHistory.get(0), "row").get("result"), "result").get("revision"));
    }

    @Test void actualChangedPlayerFramedSnapshotRetainsOriginalAvailableM3ReconciliationAndTypedRevisions() {
        var observed = snapshot(true, FULL64); var frame = observed.actual();
        var facts = new DriverObservationFacts(observed.facts().driver(), 3, 7, frame.session(), frame.snapshotId(),
                frame.nativeRevision(), DriverJson.sha256(frame.state().bytes()), FULL64, 2,
                observed.source(), observed.facts().auxiliary(), ref(bytes("actual changed-player facts")));
        var full = new DriverObservationAssembler().projectFull(frame, facts, observed.originalEvidence());
        var source = assertInstanceOf(LifecycleOriginFactory.Projected.class, LifecycleOriginFactory.project(full,
                ref(bytes("changed-player hello")), ref(facts.driver().encode()), ref(bytes("changed-player qualification"))));
        var encoded = PublicSnapshotCodec.encodeTerminal(full, source.identity(), true);
        var publicReconciliation = object(encoded).path("succession_reconciliation");
        assertEquals(FULL64.toString(), publicReconciliation.path("predecessor_binding").path("revision").textValue());
        assertEquals(FULL64.toString(), publicReconciliation.path("successor_binding").path("native_revision").textValue());
        assertTrue(publicReconciliation.path("predecessor_binding").path("date_raw").isIntegralNumber());
        assertEquals(full.semantic(), PublicSnapshotCodec.decode(encoded));
    }

    private static LifecycleObservationPort.Snapshot snapshot(boolean successor, BigInteger revision) {
        var lifecycle = McpJson.object().put("schema", "xar.ck3.succession-lifecycle-binding/v1")
                .put("lifecycle", successor ? "ordinary_campaign_succession" : "rogue_one_life")
                .put("xar_enabled", "xar_on").put("pact_contract", "fixture-pact")
                .put("source", "fixture-original").put("environment_sha256", "a".repeat(64));
        var document = McpJson.object(McpJson.parse(bytes("""
                {"format_version":2,"pipe_name":"fixture-pipe","bridge_pid":123,"episode_character_id":73,
                 "episode_run_id":"episode-original","last_checkpoint":null,"command_history":[],
                 "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
                 "succession_lifecycle":null,"campaign_goal":null,"rollback_war_failures":[]}
                """)));
        document.set("succession_lifecycle", lifecycle);
        if (successor) document.set("campaign_goal", McpJson.parse(
                GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal("fixture-campaign", 73))));
        var driver = DriverStateSnapshot.decodeComplete(McpJson.encode(document));
        var auxiliary = McpJson.object(); auxiliary.putNull("family_marriage_ledger"); auxiliary.putNull("one_life_strategy");
        if (!successor) auxiliary.set("one_life_strategy", McpJson.parse(CrossRunPlanning.encodeState(CrossRunPlanning.empty())));
        var known = new DriverSnapshotFacts.Known(driver,
                new DriverSnapshotFacts.Stamp(1, 1, GAME, "episode-original", DriverJson.sha256(driver.encode())),
                ref(driver.encode()), List.of(), DriverJson.object(McpJson.encode(auxiliary), 65536),
                Optional.empty(), Optional.empty());
        var state = McpJson.object().put("paused", true).put("map_ready", true).put("speed", 3)
                .put("date_raw", 240).put("snapshot_id", "fixture-native:41").put("revision", revision)
                .put("native_revision", revision).put("episode_run_id", "episode-original")
                .put("one_life_terminal_reason", successor ? "played_character_changed" : "played_character_dead");
        state.putObject("played_character").put("character_id", successor ? 74 : 73).put("alive", successor);
        state.putNull("one_life_settlement"); state.putNull("succession_reconciliation");
        if (!successor) state.set("one_life_settlement", settlement());
        state.putNull("active_event"); state.putNull("pending_character_interaction");
        if (successor) state.set("succession_reconciliation", reconciliation(revision));
        state.putObject("diagnostics").put("bridge_pid", 123).put("connection_generation", 1);
        state.putArray("active_wars"); state.putArray("player_armies");
        var envelope = McpJson.object().put("type", "state_snapshot").put("protocol_version", 1)
                .put("snapshot_id", "fixture-native:41").put("revision", revision);
        envelope.set("state", state); byte[] json = McpJson.encode(envelope);
        byte[] packet = ByteBuffer.allocate(json.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        var actual = new NativeObservationPort.ObservedFrame(
                new NativeObservationPort.TransportSession("fixture-machine", GAME, BigInteger.ONE, "fixture-session"),
                "fixture-native:41", revision, raw(state), packet, NOW);
        return new LifecycleObservationPort.Snapshot(actual,
                new G2Source("fixture-machine", NOW.toString(), "fixture-build", ref(bytes("fixture-source"))),
                DriverJson.object(McpJson.encode(state), 65536), known, ref(packet));
    }

    private static ObjectNode reconciliation(BigInteger revision) {
        var row = McpJson.object().put("schema", "xar.ck3.succession-reconciliation/v1").put("status", "available")
                .put("predecessor_character_id", 73).put("expected_successor_character_id", 74)
                .put("actual_successor_character_id", 74).put("successor_match", true)
                .put("title_distribution_match", true).put("verdict", "matched");
        row.putNull("unavailable_reason");
        row.putArray("expected_inherited_title_ids").add(90); row.putArray("matched_inherited_title_ids").add(90);
        for (String field : List.of("missing_expected_inherited_title_ids", "unexpected_retained_predecessor_title_ids",
                "expected_other_heir_title_ids", "expected_without_heir_title_ids", "observed_additional_successor_title_ids"))
            row.putArray(field);
        row.putObject("predecessor_binding").put("snapshot_id", "fixture-predecessor").put("revision", revision)
                .put("native_revision", revision).put("date_raw", 216).put("episode_run_id", "episode-original")
                .put("episode_character_id", 73);
        row.putObject("successor_binding").put("snapshot_id", "fixture-native:41").put("revision", revision)
                .put("native_revision", revision).put("date_raw", 240);
        return row;
    }
    private static ObjectNode settlement() {
        var row = McpJson.object().put("ready", true).put("commit_serial", 1).put("source_character_id", 73);
        row.putObject("final_score").put("raw", 1234500).put("scale", 100000);
        return row.put("score_before_reject", 15.5).put("record_candidate", 10).put("old_record", 10)
                .put("record_delta", 0).put("blessing_count", 2).put("refusal_count", 1)
                .put("contract_progress", 6).put("record_written", false);
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] value) { return new ExactRef("memory/" + DriverJson.sha256(value), value.length, DriverJson.sha256(value)); }
    private static RawJson raw(ObjectNode value) { return new RawJson(McpJson.encode(value)); }
    private static ObjectNode object(RawJson value) { return McpJson.object(McpJson.parse(value.bytes())); }
}
