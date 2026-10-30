package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Gate;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Stamp;
import org.xar.ck3.control.g2.m6.G2M6Contracts.StartOrigin;
import org.xar.ck3.control.wave2.planning.swaymaterial.SwayMaterialReducer;
import org.xar.ck3.control.wave2.planning.swaylifecycle.SwayLifecycleObservation;
import org.xar.ck3.control.wave2.planning.swayretention.SwayTerminalRetention;
import org.xar.ck3.control.wave3.planning.swayphase.SwayPhaseAndFollowing;
import org.xar.ck3.control.wave3.planning.swaystop.SelectedSwayStop;
import org.xar.ck3.control.planning.swayreuse.ReusedSwayOpportunity;

/** Original closed bytes and explicitly synthetic future native observations; no game or writer. */
final class M6IntegrationTest {
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final String BUILD = "1.20.0.4";
    private static final String EXE = M6SourceProducer.EXE;

    @Test void actualClosedLedgerKeepsBothOriginalEpisodesAndDoesNotInventNaturalCompletion() throws Exception {
        byte[] raw = resource("closed-ledger-original.json");
        var evidence = M6SourceProducer.fromClosedLedger(raw, source("closed-original.json", raw));
        assertEquals(2, evidence.episodes().size());
        var current = evidence.episodes().getFirst();
        assertEquals(40526, current.identity().actorCharacterId());
        assertEquals(83887164, current.identity().schemeInstanceId());
        assertEquals(5, current.identity().schemeInstanceGeneration());
        assertEquals(BigInteger.valueOf(25), current.firstNamedGain().orElseThrow().after().points().orElseThrow());
        assertFalse(current.terminal().orElseThrow().instanceTerminalOutcomeObserved());
        var prior = evidence.episodes().get(1);
        assertEquals(31254, prior.identity().actorCharacterId());
        assertEquals(2, prior.identity().schemeInstanceId()); assertEquals(0, prior.identity().schemeInstanceGeneration());
        assertEquals(StartOrigin.UNKNOWN, prior.start().orElseThrow().origin());
        assertArrayEquals(raw, evidence.originalLedger().bytes());
        var assessment = new M6Research().evaluateCampaign(evidence);
        assertFalse(assessment.evidencePacketReady()); assertFalse(assessment.schemeComplete());
        assertFalse(assessment.wholeM6Complete()); assertFalse(assessment.grantsSubmissionAuthority());
        // The immutable ledger includes its original trailing newline. It is evidence bytes,
        // while the G2 body is exactly one JSON token; preserve the ledger through its packet.
        var malformed = assertThrows(G2Exception.class, () -> new G2Request("m6-original", Milestone.M6,
                source("closed-original.json", raw), ProjectionJson.object(raw, M6SourceProducer.MAX_BYTES)));
        assertEquals(G2HttpError.Code.MALFORMED_REQUEST, malformed.code());
        assertEquals("G2 body must start and end at its JSON token; surrounding whitespace rejected", malformed.getMessage());
        byte[] exactPacket = packet(raw, resource("ordinary-start-auto48-original.json"));
        G2Request packetRequest = new G2Request("m6-original-wire", Milestone.M6,
                source("closed-original.packet.json", exactPacket), ProjectionJson.object(exactPacket, M6SourceProducer.MAX_BYTES));
        var wireRequest = G2Wire.decodeRequest(G2Wire.encodeRequest(packetRequest));
        assertArrayEquals(exactPacket, wireRequest.payload().bytes());
        assertArrayEquals(raw, M6SourceProducer.fromEvidencePacket(wireRequest.payload().bytes(), wireRequest.source()).originalLedger().bytes());
        var packetResponse = new M6Research().evaluate(wireRequest);
        var wireResponse = G2Wire.decodeResponse(G2Wire.encodeResponse(packetResponse));
        assertArrayEquals(packetResponse.result().bytes(), wireResponse.result().bytes());
        JsonNode decoded = StrictJson.parse(wireResponse.result().bytes());
        assertEquals("in_progress", decoded.get("milestone_status").textValue());
        assertFalse(decoded.get("whole_m6_complete").booleanValue());
        assertFalse(decoded.get("evidence_packet_ready").booleanValue());
        assertArrayEquals(raw, resource("closed-ledger-original.json"));
    }

    @Test void actualOrdinaryStartBytesJoinGenerationZeroWithoutGrantingTheUnknownEnd() throws Exception {
        byte[] ledger = resource("closed-ledger-original.json");
        byte[] auto = resource("ordinary-start-auto48-original.json");
        assertEquals("44defd2b790131659d9dbd617b755b98d9d36820789bbc5e8248274152c93c24", sha(auto));
        byte[] packet = packet(ledger, auto);
        var evidence = M6SourceProducer.fromEvidencePacket(packet, source("packet.json", packet));
        var old = evidence.episodes().stream().filter(e -> e.identity().schemeInstanceId() == 2).findFirst().orElseThrow();
        assertEquals(StartOrigin.ORDINARY_FULL_PLANNER, old.start().orElseThrow().origin());
        assertEquals(0, old.identity().schemeInstanceGeneration());
        var result = new M6Research().evaluateCampaign(evidence);
        assertTrue(result.episodes().stream().filter(e -> e.identity().schemeInstanceId() == 2).findFirst()
                .orElseThrow().satisfied().contains(Gate.ORDINARY_START));
        assertFalse(result.evidencePacketReady()); assertFalse(result.schemeComplete());
        ObjectNode drift = object(StrictJson.parse(packet, M6SourceProducer.MAX_BYTES));
        ObjectNode admitted = object(drift.get("ordinary_start_sources").get(0).get("admitted_binding"));
        admitted.put("game_pid", admitted.get("game_pid").longValue() + 1);
        byte[] bad = drift.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class,
                () -> M6SourceProducer.fromEvidencePacket(bad, source("bad-binding.json", bad)));
    }

    @Test void syntheticRetainedTerminalFlowsThroughProducerFollowingAndJsonWithoutBecomingSuccess() throws Exception {
        byte[] auto = resource("ordinary-start-auto48-original.json");
        ObjectNode ledger = syntheticNeutralTerminalLedger(); byte[] before = bytes(ledger);
        byte[] packet = packet(before, auto);
        var initial = new M6Research().evaluateCampaign(
                M6SourceProducer.fromEvidencePacket(packet, source("pending-terminal-packet.json", packet)));
        assertFalse(initial.evidencePacketReady(), "the independently observed new end still needs an ordinary following turn");
        var update = M6LedgerConsumer.followingTurn(before, source("synthetic-terminal.json", before), 31254,
                new Stamp(BigInteger.valueOf(5001), 53190001), M6LedgerConsumer.TurnKind.ORDINARY_AUTO);
        assertTrue(update.episodesChanged() > 0); assertTrue(update.observationsConsumed() > 0);
        assertFalse(update.ledgerCommitted()); assertFalse(update.actionAuthorized());
        byte[] after = update.ledger().bytes(); byte[] closedPacket = packet(after, auto);
        var evidence = M6SourceProducer.fromEvidencePacket(closedPacket, source("closed-terminal-packet.json", closedPacket));
        var result = new M6Research().evaluateCampaign(evidence);
        assertTrue(result.evidencePacketReady(), "real producer, exact native status and actual Java following consumer must close all P55 gates");
        assertFalse(result.schemeComplete(), "terminated_unattributed retains an unknown cause");
        assertFalse(result.wholeM6Complete());
        JsonNode roundtrip = StrictJson.parse(new M6Research().toJson(result).bytes());
        assertTrue(roundtrip.get("evidence_packet_ready").booleanValue());
        assertFalse(roundtrip.get("attributed_success_evidence").booleanValue());
        var again = M6LedgerConsumer.followingTurn(after, source("consumed.json", after), 31254,
                new Stamp(BigInteger.valueOf(5002), 53190002), M6LedgerConsumer.TurnKind.ORDINARY_AUTO);
        assertEquals(0, again.observationsConsumed()); assertArrayEquals(after, again.ledger().bytes());
        assertArrayEquals(before, bytes(ledger), "the proposal must not mutate its original source");
        ObjectNode stopped = object(StrictJson.parse(after));
        object(stopped.get("resolved")).set("stop_intervention", StrictJson.parse("{\"postcondition_verified\":false}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        byte[] stopPacket = packet(bytes(stopped), auto);
        assertFalse(new M6Research().evaluateCampaign(M6SourceProducer.fromEvidencePacket(stopPacket,
                source("typed-stop.json", stopPacket))).evidencePacketReady(), "a typed Stop cannot be credited as a natural terminal");
    }

    @Test void inheritedActorCannotConsumeOrRelabelTheArchivedOriginalAction() throws Exception {
        ObjectNode ledger = object(StrictJson.parse(resource("closed-ledger-original.json")));
        ObjectNode current = object(ledger.get("resolved"));
        JsonNode priorBefore = current.get("previous_interventions").deepCopy();
        current.put("next_turn_consumed", false);
        object(current.get("first_named_gain_intervention")).put("next_turn_consumed", false);
        byte[] pending = bytes(ledger);
        var update = M6LedgerConsumer.followingTurn(pending, source("heir-pending.json", pending), 40526,
                new Stamp(BigInteger.valueOf(5000), 53290000), M6LedgerConsumer.TurnKind.ORDINARY_AUTO);
        assertTrue(update.observationsConsumed() >= 2);
        assertEquals(priorBefore, StrictJson.parse(update.ledger().bytes()).at("/resolved/previous_interventions"));
        var observational = M6LedgerConsumer.followingTurn(pending, source("read-only.json", pending), 40526,
                new Stamp(BigInteger.valueOf(5000), 53290000), M6LedgerConsumer.TurnKind.OBSERVATION_ONLY);
        assertArrayEquals(pending, observational.ledger().bytes());
        assertEquals(0, observational.observationsConsumed());
        var reopened = M6SourceProducer.fromClosedLedger(update.ledger().bytes(), source("heir-consumed.json", update.ledger().bytes()));
        assertEquals(2, reopened.episodes().size());
        assertFalse(new M6Research().evaluateCampaign(reopened).wholeM6Complete());
    }

    @Test void nativeCanContinueOpinionAndMalformedTokensCannotReplaceAnIndependentTerminal() throws Exception {
        ObjectNode root = object(StrictJson.parse(resource("closed-ledger-original.json")));
        ObjectNode resolved = object(root.get("resolved"));
        ObjectNode nativeRead = object(resolved.at("/latest_instance_observation/native_observation"));
        Identity identity = M6SourceProducer.fromClosedLedger(bytes(root), source("original-for-native.json", bytes(root)))
                .episodes().getFirst().identity();
        nativeRead.put("native_can_continue_observed", true); nativeRead.put("native_can_continue", false);
        var completion = M6SourceProducer.fromRawCompletion(bytes(nativeRead), identity);
        assertEquals(M6SourceProducer.NativeState.UNOBSERVED, completion.nativeState());
        assertEquals(Boolean.FALSE, completion.canContinue().orElseThrow());
        for (String token : List.of("true", "5.0", "\"5\"")) {
            ObjectNode invalid = root.deepCopy();
            object(invalid.at("/resolved/native_receipt")).put("scheme_instance_generation", "__invalid_generation__");
            String marked = invalid.toString();
            String marker = "\"__invalid_generation__\"";
            assertEquals(marked.indexOf(marker), marked.lastIndexOf(marker));
            assertTrue(marked.contains(marker));
            byte[] bad = marked.replace(marker, token).getBytes(java.nio.charset.StandardCharsets.UTF_8);
            assertFalse(StrictJson.parse(bad).at("/resolved/native_receipt/scheme_instance_generation").isIntegralNumber(), token);
            assertThrows(ContractViolationException.class,
                    () -> M6SourceProducer.fromClosedLedger(bad, source("invalid-token.json", bad)), token);
        }
        ObjectNode foreign = root.deepCopy(); object(foreign.at("/resolved/first_named_gain_intervention")).put("target_character_id", 34974);
        byte[] bad = bytes(foreign);
        assertThrows(ContractViolationException.class,
                () -> M6SourceProducer.fromClosedLedger(bad, source("foreign-gain.json", bad)));
        assertThrows(ContractViolationException.class, () -> M6SourceProducer.fromClosedLedger(bytes(root),
                source("different-bytes.json", new byte[] {'{','}'})));
    }

    @Test void existingMaterialPhaseRetentionAndFollowingConsumersShareTheSameOriginalJsonDomain() throws Exception {
        ObjectNode ledger = object(StrictJson.parse(resource("closed-ledger-original.json")));
        ObjectNode resolved = object(ledger.get("resolved"));
        ObjectNode pendingInput = StrictJson.object(); pendingInput.set("resolved", resolved.deepCopy());
        var pending = SwayPhaseAndFollowing.pending(bytes(pendingInput));
        assertFalse(pending.snapshotTaken()); assertFalse(pending.submissionAuthorized());
        ObjectNode observation = object(resolved.get("terminal_intervention"));
        ObjectNode retain = StrictJson.object(); retain.putNull("previous"); retain.set("observation", observation.deepCopy());
        var retained = SwayTerminalRetention.evaluate(bytes(retain));
        assertEquals(observation, StrictJson.parse(retained.snapshot().toJson()));
        assertFalse(retained.freshReadCauseAttributed()); assertFalse(retained.submissionAuthorized());
        ObjectNode first = object(resolved.get("first_named_gain_intervention")).deepCopy(); first.put("next_turn_consumed", false);
        ObjectNode following = StrictJson.object(); following.set("material", first);
        following.put("actor_character_id", 40526); following.put("native_revision", 5000); following.put("date_raw", 53290000);
        JsonNode consumed = StrictJson.parse(SwayMaterialReducer.following(bytes(following)).orElseThrow().toJson());
        assertTrue(consumed.get("next_turn_consumed").booleanValue());
        assertEquals(first.get("scheme_sway_opinion"), consumed.get("scheme_sway_opinion"));
        assertNotEquals(first.get("following_native_revision"), consumed.get("following_native_revision"));
    }

    @Test void currentSameValueRefreshRetainsFirstGainAndMissingVersusNullOriginalFields() throws Exception {
        ObjectNode ledger = object(StrictJson.parse(resource("closed-ledger-original.json")));
        ObjectNode resolved = object(ledger.get("resolved"));
        ObjectNode previous = object(resolved.get("material_intervention"));
        ObjectNode opinion = previous.deepCopy(); opinion.put("schema", "xar.ck3.sway-outcome-opinion-v1");
        opinion.put("available", true);
        opinion.put("snapshot_revision", previous.get("source_native_revision").bigIntegerValue().add(BigInteger.ONE));
        opinion.put("date_raw", previous.get("source_date_raw").intValue() + 1);
        ObjectNode census = StrictJson.object(); census.put("schema", "active-scheme-sway-private-read-v1");
        census.put("actor_character_id", 40526); census.put("target_character_id", 34973);
        census.put("exact_ck3_build", BUILD); census.put("exe_sha256", EXE);
        census.set("date_raw", opinion.get("date_raw")); census.putArray("active_sway_instances");
        ObjectNode stageInput = StrictJson.object(); stageInput.set("resolved", resolved.deepCopy()); stageInput.set("opinion_read", opinion);
        stageInput.putObject("source").put("kind", "census").set("sway_read", census);
        var stage = SwayMaterialReducer.stage(bytes(stageInput));
        assertEquals(SwayMaterialReducer.Transition.REFRESHED, stage.transition());
        assertFalse(stage.firstNamedGainCreated());
        JsonNode updated = StrictJson.parse(stage.updatedResolved().orElseThrow().toJson());
        assertEquals(resolved.get("first_named_gain_intervention"), updated.get("first_named_gain_intervention"));
        assertEquals(previous.get("next_turn_consumed"), updated.at("/material_intervention/next_turn_consumed"));
        assertFalse(updated.at("/material_intervention/incremental_named_gain_observed").booleanValue());
        ObjectNode missing = ledger.deepCopy(); object(missing.get("resolved")).remove("first_named_gain_intervention");
        ObjectNode nullable = ledger.deepCopy(); object(nullable.get("resolved")).putNull("first_named_gain_intervention");
        byte[] missingBytes = bytes(missing), nullBytes = bytes(nullable);
        var missingEvidence = M6SourceProducer.fromClosedLedger(missingBytes, source("missing-gain.json", missingBytes));
        var nullEvidence = M6SourceProducer.fromClosedLedger(nullBytes, source("null-gain.json", nullBytes));
        assertTrue(missingEvidence.episodes().getFirst().firstNamedGain().isEmpty());
        assertTrue(nullEvidence.episodes().getFirst().firstNamedGain().isEmpty());
        assertFalse(java.util.Arrays.equals(missingEvidence.originalLedger().bytes(), nullEvidence.originalLedger().bytes()));
        assertArrayEquals(missingBytes, missingEvidence.originalLedger().bytes());
        assertArrayEquals(nullBytes, nullEvidence.originalLedger().bytes());
    }

    @Test void existingLifecycleSelectedStopAndReuseConsumersKeepUnknownStateAndNeverResubmit() throws Exception {
        ObjectNode ledger = object(StrictJson.parse(resource("closed-ledger-original.json")));
        ObjectNode resolved = object(ledger.get("resolved"));
        ObjectNode frame = StrictJson.object(); frame.put("snapshot_id", "native:5000");
        frame.put("revision", 17); frame.put("native_revision", 5000); frame.put("date_raw", 53290000);
        frame.put("paused", true); frame.put("map_ready", true); frame.put("episode_run_id", "synthetic-heir");
        frame.put("episode_character_id", 40526); frame.putNull("one_life_terminal_reason");
        frame.putObject("played_character").put("character_id", 40526).put("alive", true);
        ObjectNode lifecycle = StrictJson.object(); lifecycle.set("resolved", resolved.deepCopy());
        lifecycle.set("before", frame.deepCopy()); lifecycle.put("target_character_id", 34973);
        lifecycle.putObject("permissions").put("completion", true).put("opinion", true).put("termination", true);
        var plan = SwayLifecycleObservation.prepare(bytes(lifecycle)).orElseThrow();
        assertEquals(3, plan.commands().size());
        var failed = SwayLifecycleObservation.complete(plan, List.of(new SwayLifecycleObservation.Failed(
                plan.commands().getFirst(), SwayLifecycleObservation.FailureKind.BRIDGE_UNAVAILABLE,
                "synthetic unavailable; no game called")), plan.before());
        assertEquals(SwayLifecycleObservation.Status.QUERY_FAILED, failed.status());
        assertFalse(failed.requestRetried()); assertFalse(failed.submissionAuthorized()); assertFalse(failed.terminalOutcomeGranted());
        ObjectNode readback = StrictJson.object(); readback.put("schema", "active-scheme-sway-private-read-v1");
        readback.put("queried_revision", 17); readback.put("queried_native_revision", 5000);
        readback.put("snapshot_revision", 5000); readback.put("date_raw", 53290000);
        readback.put("actor_character_id", 40526); readback.put("target_character_id", 34973);
        readback.put("capture_epoch", 1); readback.put("container_generation", BigInteger.ONE);
        readback.put("target_opinion_of_actor", 100); readback.put("active_scheme_count", 0);
        readback.put("native_legal_now", true); readback.put("matching_sway_active", false);
        ObjectNode stop = StrictJson.object(); stop.set("ledger", ledger.deepCopy()); stop.set("snapshot", frame.deepCopy());
        stop.set("readback", readback); stop.putNull("opinion_read"); stop.put("native_stop_entry", "unavailable");
        ObjectNode request = stop.putObject("selected_request"); request.put("expected_revision", 17);
        request.put("target_character_id", 34973); request.put("scheme_instance_id", 83887164);
        request.put("scheme_instance_generation", 5);
        assertEquals(SelectedSwayStop.Operation.RETAIN_EXISTING_SWAY, SelectedSwayStop.plan(bytes(stop)).operation());
        ObjectNode reuse = StrictJson.object(); reuse.set("resolved", resolved.deepCopy());
        reuse.put("actor_character_id", 40526); reuse.put("date_raw", 53290000);
        var gap = ReusedSwayOpportunity.decodeObservationGap(bytes(reuse));
        assertTrue(gap.isPresent());
        assertEquals(ReusedSwayOpportunity.TerminalCause.UNKNOWN, gap.orElseThrow().terminalCause());
        assertEquals(gap, ReusedSwayOpportunity.decodeResult(ReusedSwayOpportunity.encode(gap)));
        assertFalse(new M6Research().evaluateCampaign(M6SourceProducer.fromClosedLedger(bytes(ledger),
                source("same-six-consumer-ledger.json", bytes(ledger)))).evidencePacketReady());
    }

    private static ObjectNode syntheticNeutralTerminalLedger() throws Exception {
        ObjectNode root = object(StrictJson.parse(resource("closed-ledger-original.json")));
        ObjectNode old = object(root.at("/resolved/previous_interventions/0")).deepCopy();
        old.remove("previous_interventions");
        ObjectNode nativeRead = object(old.at("/latest_instance_observation/native_observation")).deepCopy();
        nativeRead.put("snapshot_revision", 5000); nativeRead.put("date_raw", 53190000);
        nativeRead.put("available", true); nativeRead.put("instance_source_observed", true);
        nativeRead.put("instance_present", true); nativeRead.put("storage_slot_reused", false);
        nativeRead.put("exact_instance_join_ready", true); nativeRead.put("native_status_observed", true);
        nativeRead.put("native_status_raw", 1); nativeRead.put("native_owner_raw", 0xffff_ffffL);
        nativeRead.put("native_terminal_state_observed", true); nativeRead.put("native_status_key", "terminated_unattributed");
        nativeRead.put("terminal_cause_observed", false); nativeRead.put("terminal_cause", "unknown");
        ObjectNode terminal = object(old.get("terminal_intervention")).deepCopy();
        terminal.put("source_native_revision", 5000); terminal.put("source_date_raw", 53190000);
        terminal.put("tracked_instance_active", false); terminal.put("instance_terminal_outcome_observed", true);
        terminal.put("native_status_key", "terminated_unattributed"); terminal.put("terminal_cause_observed", false);
        terminal.put("terminal_cause", "unknown"); terminal.put("next_turn_consumed", false);
        terminal.remove(List.of("following_native_revision", "following_date_raw"));
        terminal.set("native_observation", nativeRead); old.set("terminal_intervention", terminal);
        root.set("resolved", old); return root;
    }

    private static byte[] packet(byte[] ledger, byte[] auto) throws Exception {
        JsonNode frame = StrictJson.parse(auto, M6SourceProducer.MAX_BYTES)
                .at("/result/structured_content/planning_source_frame");
        var binding = new M6SourceProducer.OrdinaryStartBinding(
                StrictJson.integer(frame.get("actor_character_id"), 1, 0xffff_fffeL),
                StrictJson.text(frame.get("episode_run_id")), StrictJson.integer(frame.get("bridge_pid"), 1, 0xffff_ffffL));
        return M6SourceProducer.encodeEvidencePacket(ledger, ref("portable-closed-ledger.json", ledger),
                auto, ref("ordinary-auto48-original.json", auto), binding);
    }

    private static G2Source source(String name, byte[] raw) throws Exception {
        return new G2Source(MACHINE, "2026-10-22T20:50:00Z", BUILD, ref(name, raw));
    }
    private static ExactRef ref(String path, byte[] raw) throws Exception { return new ExactRef(path, raw.length, sha(raw)); }
    private static String sha(byte[] raw) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
    private static byte[] resource(String name) throws IOException {
        try (InputStream stream = M6IntegrationTest.class.getResourceAsStream("/" + name)) {
            if (stream == null) { throw new IOException("exact original M6 resource required: " + name + "; no fallback or skip"); }
            return stream.readAllBytes();
        }
    }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "integration source object required"); return (ObjectNode) value;
    }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value, M6SourceProducer.MAX_BYTES); }
}
