package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Synthetic native inputs exercise the real source validator, reducer, cold codec and evidence producer. */
public final class SwayLifecycleTest {
    private static final BigInteger REV = new BigInteger("9223372036854775815");
    private static final BigInteger BIRTH = new BigInteger("134371234567890123");
    private static final int DATE = 53290000;

    @Test void namedGainThenTerminalColdFollowingAndPurgePreserveIndependentOriginalEvidence() {
        Episode episode = episode(0); ObservationIdentity before = source(REV, DATE, 8000);
        var state = SwayLifecycle.empty(episode.identity(), before);
        state = observe(state, episode, before, 0, 20, true);
        assertTrue(state.latest().orElseThrow().active()); assertFalse(state.terminal().isPresent()); assertFalse(state.firstGain().isPresent());
        ObservationIdentity next = source(REV.add(BigInteger.ONE), DATE + 24, 8000);
        state = observe(state, episode, next, 0, 30, true);
        assertTrue(state.material().orElseThrow().incrementalNamedGain()); assertTrue(state.firstGain().isPresent()); assertTrue(SwayLifecycle.mayFinish(state, next, 61));
        var firstGain = state.firstGain().orElseThrow();
        state = SwayLifecycle.consumeFollowing(state, source(REV.add(BigInteger.TWO), DATE + 48, 8000));
        assertFalse(SwayLifecycle.hasPendingFollowing(state));
        ObservationIdentity terminal = source(REV.add(BigInteger.valueOf(3)), DATE + 72, 8000);
        state = observe(state, episode, terminal, 1, 30, true);
        assertTrue(state.terminal().orElseThrow().instanceTerminalOutcomeObserved()); assertFalse(state.terminal().orElseThrow().terminalCauseObserved());
        assertTrue(state.terminal().orElseThrow().eventDateRaw().isEmpty()); assertFalse(state.firstGain().orElseThrow().observed().consumption().equals(firstGain.observed().consumption()));
        assertTrue(SwayLifecycle.observedTerminal(state, terminal));
        byte[] persisted = SwayLifecycle.encode(state);
        String wire = new String(persisted, java.nio.charset.StandardCharsets.UTF_8);
        assertTrue(wire.contains("\"creation_filetime\":\"134371234567890123\"")); assertTrue(wire.contains("\"native_revision\":\"9223372036854775815\""));
        var cold = SwayLifecycle.decode(persisted); assertEquals(state, cold);
        ObservationIdentity later = source(REV.add(BigInteger.valueOf(4)), DATE + 96, 8000);
        cold = SwayLifecycle.consumeFollowing(cold, later);
        var retained = cold.terminal().orElseThrow();
        ObjectNode missing = completion(episode, later, 0); missing.put("instance_present", false); missing.put("instance_source_observed", true);
        missing.put("exact_instance_join_ready", false); missing.put("native_status_observed", false); missing.put("native_terminal_state_observed", false);
        missing.putNull("native_owner_raw"); missing.putNull("native_status_raw"); missing.put("native_status_key", "unobserved");
        cold = SwayLifecycle.observe(cold, episode, inputs(missing, null), later);
        assertEquals(retained, cold.terminal().orElseThrow()); assertEquals(M6SourceProducer.NativeState.UNOBSERVED, cold.latest().orElseThrow().state());
        assertFalse(SwayLifecycle.observedTerminal(cold, later)); assertFalse(SwayLifecycle.mayFinish(cold, later, 61));
        JsonNode exported = StrictJson.parse(SwayLifecycle.interventions(cold).bytes());
        assertTrue(exported.at("/terminal_intervention/next_turn_consumed").booleanValue());
        assertEquals("unknown", exported.at("/terminal_intervention/terminal_cause").textValue());
    }

    @Test void repeatSemanticReadRefreshesProvenanceWithoutRearmingOrErasingFirstGain() {
        Episode episode = episode(16777227); ObservationIdentity first = source(REV, DATE, 8000);
        var state = observe(SwayLifecycle.empty(episode.identity(), first), episode, first, 0, 20, true);
        var second = source(REV.add(BigInteger.ONE), DATE + 24, 8000); state = observe(state, episode, second, 0, 40, true);
        var after = source(REV.add(BigInteger.TWO), DATE + 48, 8000); state = SwayLifecycle.consumeFollowing(state, after);
        var gain = state.firstGain().orElseThrow();
        state = observe(state, episode, after, 0, 40, true);
        assertFalse(state.material().orElseThrow().incrementalNamedGain()); assertEquals(gain, state.firstGain().orElseThrow());
        assertTrue(state.material().orElseThrow().consumption().nextTurnConsumed()); assertFalse(SwayLifecycle.hasPendingFollowing(state));
        assertEquals(after, state.latest().orElseThrow().source());
    }

    @Test void sourceDriftWrongGenerationBooleanAndColdTamperingAreRejected() {
        Episode episode = episode(16777227); ObservationIdentity source = source(REV, DATE, 8000);
        var state = observe(SwayLifecycle.empty(episode.identity(), source), episode, source, 0, 20, true);
        ObjectNode wrong = completion(episode, source, 0); wrong.put("scheme_instance_generation", 2);
        assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.observe(state, episode, inputs(wrong, null), source));
        ObjectNode bool = completion(episode, source, 0); bool.put("native_status_raw", true);
        assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.observe(state, episode, inputs(bool, null), source));
        ObjectNode missing = completion(episode, source, 0); missing.remove("native_owner_raw");
        assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.observe(state, episode, inputs(missing, null), source));
        assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.observe(state, episode, inputs(completion(episode, source, 0), null), source(REV, DATE, 8001)));
        ObjectNode tampered = (ObjectNode)StrictJson.parse(SwayLifecycle.encode(state), SwayLifecycle.MAX_BYTES);
        ((ObjectNode)tampered.get("latest")).put("state", "TERMINATED_UNATTRIBUTED");
        assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.decode(StrictJson.canonical(tampered, SwayLifecycle.MAX_BYTES)));
        ObjectNode numeric64 = (ObjectNode)StrictJson.parse(SwayLifecycle.encode(state), SwayLifecycle.MAX_BYTES);
        ((ObjectNode)numeric64.at("/origin/game")).put("creation_filetime", BIRTH);
        assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.decode(StrictJson.canonical(numeric64, SwayLifecycle.MAX_BYTES)));
    }

    @Test void knownZeroAbsentAndUnreadNamedFieldsRemainDifferent() {
        Episode episode = episode(0); ObservationIdentity current = source(REV, DATE, 8000);
        ObjectNode completion = completion(episode, current, 0); ObjectNode opinion = opinion(episode, current, 0);
        ((ObjectNode)opinion.get("scheme_sway_opinion")).put("present", false).putNull("value");
        var absent = SwayLifecycle.observe(SwayLifecycle.empty(episode.identity(), current), episode, inputs(completion, opinion), current);
        assertEquals(Optional.of(BigInteger.ZERO), absent.material().orElseThrow().sway().points());
        ((ObjectNode)opinion.get("scheme_sway_opinion")).put("observed", false);
        var unread = SwayLifecycle.observe(SwayLifecycle.empty(episode.identity(), current), episode, inputs(completion, opinion), current);
        assertTrue(unread.material().orElseThrow().sway().points().isEmpty()); assertNotEquals(absent.material().orElseThrow().sway(), unread.material().orElseThrow().sway());
        assertEquals(unread, SwayLifecycle.decode(SwayLifecycle.encode(unread)));
    }

    @Test void strictExecutionRecordsCannotBorrowAHiddenPhaseAsMaterialTerminalOrAuthoredParent() {
        Episode episode = episode(0); ObservationIdentity current = source(REV, DATE, 8000);
        ObjectNode journal = identity(episode); build(journal); journal.put("schema", "xar.ck3.sway-completion-execution.v1"); journal.put("available", true);
        journal.put("retention_gap", false); journal.put("snapshot_revision", REV); journal.put("date_raw", DATE); journal.put("earliest_sequence", 1); journal.put("latest_sequence", 1);
        ObjectNode row = identity(episode); row.put("sequence", 1); row.put("date_raw", DATE - 24); row.put("source_branch", "hidden_phase_success_source");
        row.put("stock_event", "sway_outcome.0001"); row.put("phase_result", "success"); row.put("executing_input_observed", true); row.put("exact_scope_join_ready", true);
        row.put("message_enqueue_observed", false); row.put("material_effect_observed", false); row.put("native_terminal_state_observed", false); journal.putArray("records").add(row);
        var inputs = new M6TerminalSourceComposition.Inputs(Optional.empty(), Optional.of(json(journal)), Optional.empty(), Optional.empty());
        var state = SwayLifecycle.observe(SwayLifecycle.empty(episode.identity(), current), episode, inputs, current);
        assertTrue(state.phase().isPresent()); assertTrue(state.material().isEmpty()); assertTrue(state.terminal().isEmpty());
        assertFalse(state.phase().orElseThrow().nativeTerminalStateObserved());
        row.put("source_branch", M6TerminalSourceComposition.COMPLETE); row.putNull("stock_event"); row.putNull("phase_result");
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateExecution(json(journal), episode.identity()));
        row.put("native_invocation", true);
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateExecution(json(journal), episode.identity()));
    }

    @Test void recoveredZeroSchemePassesTheActualSharedProducerCompositionAndLifecycle() throws Exception {
        Episode original = episode(0); ObservationIdentity current = source(REV, DATE, 8000);
        ObjectNode resolved = (ObjectNode)StrictJson.parse(original.originalResolved().bytes()); resolved.putNull("native_receipt");
        ObjectNode recovered = identity(original); recovered.put("schema", "xar.ck3.sway-recovered-instance-observation.v1");
        recovered.put("action_id", original.identity().actionId());
        recovered.put("source_kind", "matching_active_readback_recovery"); recovered.put("submission_receipt_available", false);
        ObjectNode active = recovered.putObject("active_instance"); active.put("scheme_instance_id", 0); active.put("scheme_instance_generation", 0);
        active.put("target_character_id", original.identity().targetCharacterId()); active.put("progress", 0); active.put("progress_goal", 10); active.put("is_exposed", false); active.put("is_frozen", false);
        ObjectNode source = recovered.putObject("source_read"); build(source); source.put("schema", "active-scheme-sway-private-read-v1"); source.put("snapshot_revision", REV); source.put("date_raw", DATE);
        for (String key : new String[]{"queried_revision", "capture_epoch", "container_generation"}) source.put(key, 1);
        source.put("queried_native_revision", REV); source.put("queried_snapshot_id", "native:" + REV); source.put("post_snapshot_id", "native:" + REV);
        resolved.set("recovered_instance_observation", recovered); resolved.put("post_native_revision", REV); resolved.put("post_date_raw", DATE);
        ObjectNode ledger = StrictJson.object(); ledger.put("schema", "xar.ck3.active-scheme-sway-formal-private.v1"); ledger.putNull("pending"); ledger.set("resolved", resolved);
        byte[] bytes = StrictJson.canonical(ledger, M6SourceProducer.MAX_BYTES);
        var ref = new ExactRef("fixture:recovered-zero", bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        var evidence = M6SourceProducer.fromClosedLedger(bytes, new G2Source(current.machineId(), "2026-10-23T18:00:00Z", "1.20.0.4", ref));
        var episode = evidence.episodes().getFirst(); assertEquals(0, episode.identity().schemeInstanceId());
        var state = observe(SwayLifecycle.empty(episode.identity(), current), episode, current, 0, 10, true); assertTrue(state.latest().orElseThrow().active());
        assertEquals(state, SwayLifecycle.decode(SwayLifecycle.encode(state)));
        assertThrows(IllegalArgumentException.class, () -> new Identity("sentinel", 31254, 34333, 0xffff_ffffL, 255));
    }

    @Test void copiedSourceBase64UsesItsDeclaredRoleLimitAndIsInternedAcrossConsumers() {
        Episode original = episode(0); ObjectNode resolved = (ObjectNode)StrictJson.parse(original.originalResolved().bytes());
        ((ObjectNode)resolved.get("native_receipt")).put("retained_source_context", "x".repeat(25000));
        Episode episode = new Episode(original.identity(), Optional.empty(), Optional.empty(), Optional.empty(), json(resolved));
        ObservationIdentity source = source(REV, DATE, 8000);
        var state = observe(SwayLifecycle.empty(episode.identity(), source), episode, source, 0, 20, true);
        byte[] raw = SwayLifecycle.encode(state); JsonNode wire = StrictJson.parse(raw, SwayLifecycle.MAX_BYTES);
        assertTrue(wire.at("/proofs/0/original_resolved").textValue().length() > 32768);
        assertEquals(1, wire.get("proofs").size());
        assertEquals(wire.at("/latest/proof_ref"), wire.at("/material/proof_ref"));
        assertEquals(state, SwayLifecycle.decode(raw));
    }

    @Test void censusMaterialSharesGainLogicAndAbsenceNeverCreatesAnExactTerminal() {
        Episode episode = episode(0); ObservationIdentity first = source(REV, DATE, 8000);
        ObjectNode census = identity(episode); build(census); census.put("schema", "active-scheme-sway-private-read-v1"); census.put("snapshot_revision", REV); census.put("date_raw", DATE);
        ObjectNode active = census.putArray("active_sway_instances").addObject(); active.put("scheme_instance_id", 0); active.put("scheme_instance_generation", 0); active.put("target_character_id", episode.identity().targetCharacterId());
        var state = SwayLifecycle.observeCensusMaterial(SwayLifecycle.empty(episode.identity(), first), episode, json(census), json(opinion(episode, first, 10)), first);
        assertTrue(state.latest().isEmpty()); assertTrue(state.material().orElseThrow().trackedActive());
        ObservationIdentity later = source(REV.add(BigInteger.ONE), DATE + 24, 8000); census.put("snapshot_revision", later.frame().identity().nativeRevision()); census.put("date_raw", later.frame().identity().dateRaw());
        state = SwayLifecycle.observeCensusMaterial(state, episode, json(census), json(opinion(episode, later, 30)), later);
        assertTrue(state.firstGain().isPresent()); assertTrue(state.material().orElseThrow().incrementalNamedGain());
        census.putArray("active_sway_instances");
        state = SwayLifecycle.observeCensusMaterial(state, episode, json(census), json(opinion(episode, later, 30)), later);
        assertFalse(state.material().orElseThrow().trackedActive()); assertTrue(state.terminal().isEmpty()); assertTrue(state.latest().isEmpty());
        assertEquals(state, SwayLifecycle.decode(SwayLifecycle.encode(state)));
    }

    private static SwayLifecycle.State observe(SwayLifecycle.State state, Episode episode, ObservationIdentity source, int status, int points, boolean material) {
        return SwayLifecycle.observe(state, episode, inputs(completion(episode, source, status), material ? opinion(episode, source, points) : null), source);
    }
    private static Episode episode(long scheme) {
        var identity = new Identity("sway-fixture-original", 31254, 34333, scheme, (int)(scheme >>> 24));
        ObjectNode resolved = StrictJson.object(); resolved.put("status", "applied"); resolved.put("postcondition_verified", true); resolved.put("action_id", identity.actionId());
        resolved.put("actor_character_id", identity.actorCharacterId()); resolved.put("target_character_id", identity.targetCharacterId());
        ObjectNode receipt = resolved.putObject("native_receipt"); receipt.put("schema", "active-scheme-sway-formal-private-v1"); receipt.put("stage", "applied");
        receipt.put("postcondition_verified", true); receipt.put("action_id", identity.actionId()); receipt.put("scheme_instance_id", scheme); receipt.put("scheme_instance_generation", scheme >>> 24); build(receipt);
        return new Episode(identity, Optional.empty(), Optional.empty(), Optional.empty(), json(resolved));
    }
    private static ObservationIdentity source(BigInteger revision, int date, long pid) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(31254), revision, BigInteger.valueOf(date)), "native:" + revision, revision, "episode-fixture");
        return new ObservationIdentity("xenoamess-full-tower-eb9d2c1186", new GameGeneration(pid, new PythonOnlyUInt64(BIRTH)), frame, 1);
    }
    private static ObjectNode completion(Episode episode, ObservationIdentity source, int status) {
        ObjectNode row = identity(episode); build(row); row.put("schema", "xar.ck3.sway_completion.v1"); row.put("snapshot_revision", source.frame().identity().nativeRevision()); row.put("date_raw", source.frame().identity().dateRaw());
        row.put("available", true); row.put("instance_present", true); row.put("instance_source_observed", true); row.put("storage_slot_reused", false); row.put("exact_instance_join_ready", true);
        row.put("native_owner_raw", status == 1 ? 0xffff_ffffL : episode.identity().actorCharacterId()); row.put("owner_matches_actor", status == 0); row.put("native_status_observed", true); row.put("native_status_raw", status);
        row.put("native_terminal_state_observed", status == 1); row.put("native_status_key", status == 1 ? "terminated_unattributed" : "continue"); row.put("terminal_cause_observed", false); row.put("terminal_cause", "unknown"); return row;
    }
    private static ObjectNode opinion(Episode episode, ObservationIdentity source, int points) {
        ObjectNode row = identity(episode); build(row); row.put("schema", "xar.ck3.sway-outcome-opinion-v1"); row.put("available", true); row.put("snapshot_revision", source.frame().identity().nativeRevision()); row.put("date_raw", source.frame().identity().dateRaw());
        row.put("target_opinion_of_actor", 61); ObjectNode sway = row.putObject("scheme_sway_opinion"); sway.put("observed", true); sway.put("present", true); sway.put("value", points);
        ObjectNode blocker = row.putObject("sway_blocker_opinion"); blocker.put("observed", true); blocker.put("present", false); blocker.putNull("value"); return row;
    }
    private static ObjectNode identity(Episode episode) { ObjectNode row = M6TerminalSourceComposition.identityJson(episode.identity()); row.remove("action_id"); return row; }
    private static void build(ObjectNode row) { row.put("build_version", M6SourceProducer.BUILD); row.put("executable_sha256", M6SourceProducer.EXE); row.put("exact_ck3_build", M6SourceProducer.BUILD); row.put("exe_sha256", M6SourceProducer.EXE); }
    private static ProjectionJson json(JsonNode value) { return ProjectionJson.object(StrictJson.canonical(value, M6SourceProducer.MAX_BYTES), M6SourceProducer.MAX_BYTES); }
    private static M6TerminalSourceComposition.Inputs inputs(JsonNode completion, JsonNode opinion) { return new M6TerminalSourceComposition.Inputs(Optional.ofNullable(completion).map(SwayLifecycleTest::json), Optional.empty(), Optional.empty(), Optional.ofNullable(opinion).map(SwayLifecycleTest::json)); }
}
