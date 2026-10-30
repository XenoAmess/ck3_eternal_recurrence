package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.m6.M6TerminalSourceCompositionTest.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Raw-source ingress is production code. Prospective end/gain additions are explicitly synthetic. */
public final class M6ServiceCausalAssessmentTest {
    private record Fixture(byte[] packet, G2M6Contracts.CampaignEvidence evidence,
            G2M6Contracts.Episode episode, int gainDate, int terminalDate) { }

    @Test void qualifiedRawDynamicCauseReachesAssessmentWithoutChangingAnyOriginalEvidence() throws Exception {
        Fixture fixture = fixture(true);
        var source = sources(fixture, fixture.terminalDate(), true);
        assertTrue(M6TerminalSourceComposition.compose(fixture.episode(), source.inputs()).cause().isPresent());
        var result = M6ServiceIntegration.compose(fixture.evidence(), List.of(source), new M6Research());
        assertTrue(result.assessment().evidencePacketReady());
        assertTrue(result.assessment().schemeComplete(), "validated source cause must reach the final assessment caller");
        assertFalse(result.assessment().wholeM6Complete());
        assertSame(fixture.evidence(), result.evidence());
        assertFalse(result.evidence().episodes().stream().filter(value -> value.identity().equals(fixture.episode().identity()))
                .findFirst().orElseThrow().terminal().orElseThrow().terminalCauseObserved());
        assertArrayEquals(fixture.evidence().originalLedger().bytes(), result.evidence().originalLedger().bytes());
        JsonNode composed = StrictJson.parse(result.compositions().getFirst().wire().bytes(), M6SourceProducer.MAX_BYTES);
        assertFalse(composed.at("/causal_observation/material_effect_observed").booleanValue());
        assertTrue(composed.get("named_material_observation").isNull());
    }

    @Test void residentRequestCodecAndResearchDispatchConsumeTheSameRawProof() throws Exception {
        Fixture fixture = fixture(true);
        byte[] payload = M6ServiceIntegration.encode(fixture.packet(), ref("synthetic:packet", fixture.packet()),
                List.of(sources(fixture, fixture.terminalDate(), true)));
        G2Request request = new G2Request("m6-source-cause-assessment", Milestone.M6,
                source("synthetic:request", payload), ProjectionJson.object(payload, M6SourceProducer.MAX_BYTES));
        var response = new M6Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
        JsonNode wire = StrictJson.parse(G2Wire.decodeResponse(G2Wire.encodeResponse(response)).result().bytes(), M6SourceProducer.MAX_BYTES);
        assertTrue(wire.at("/assessment/attributed_success_evidence").booleanValue());
        assertTrue(wire.at("/compositions/0/terminal_cause_observed").booleanValue());
        assertFalse(wire.at("/compositions/0/causal_observation/material_effect_observed").booleanValue());
        assertFalse(wire.get("whole_m6_complete").booleanValue());
        assertEquals(0, wire.get("game_day_credit").intValue());
    }

    @Test void rawCauseWithoutAnAlreadyIndependentTerminalDoesNotCreateOne() throws Exception {
        Fixture fixture = fixture(false);
        var result = M6ServiceIntegration.compose(fixture.evidence(), List.of(sources(fixture, fixture.terminalDate(), true)), new M6Research());
        assertTrue(result.compositions().getFirst().cause().isPresent());
        assertTrue(result.evidence().episodes().stream().filter(value -> value.identity().equals(fixture.episode().identity()))
                .findFirst().orElseThrow().terminal().isEmpty());
        assertFalse(result.assessment().schemeComplete());
        assertFalse(result.assessment().evidencePacketReady());
    }

    @Test void plainOriginalEndAndRetainedStatusCannotSupplyAuthoredCause() throws Exception {
        Fixture fixture = fixture(true);
        var result = M6ServiceIntegration.compose(fixture.evidence(), List.of(sources(fixture, fixture.terminalDate(), false)), new M6Research());
        assertTrue(result.assessment().evidencePacketReady());
        assertTrue(result.compositions().getFirst().cause().isEmpty());
        assertFalse(result.assessment().schemeComplete());
    }

    @Test void gainAfterExecutedEndOrEndAfterIndependentTerminalCannotBorrowSourceAttribution() throws Exception {
        Fixture fixture = fixture(true);
        for (int eventDate : List.of(fixture.gainDate() - 1, fixture.terminalDate() + 1)) {
            var result = M6ServiceIntegration.compose(fixture.evidence(), List.of(sources(fixture, eventDate, true)), new M6Research());
            assertTrue(result.compositions().getFirst().cause().isPresent());
            assertTrue(result.assessment().evidencePacketReady());
            assertFalse(result.assessment().schemeComplete());
        }
    }

    @Test void incompleteConsumptionAndMissingOrdinarySourceRemainMissingEvenWithQualifiedCause() throws Exception {
        Fixture fixture = fixture(true);
        ObjectNode ledger = (ObjectNode)StrictJson.parse(fixture.evidence().originalLedger().bytes(), M6SourceProducer.MAX_BYTES);
        ObjectNode resolved = episodeNode(ledger, fixture.episode().identity().actionId());
        ((ObjectNode)resolved.get("terminal_intervention")).put("next_turn_consumed", false);
        byte[] raw = ledger.toString().getBytes(StandardCharsets.UTF_8);
        var evidence = M6SourceProducer.fromClosedLedger(raw, source("synthetic:no-ordinary", raw));
        var result = M6ServiceIntegration.compose(evidence, List.of(sources(fixture, fixture.terminalDate(), true)), new M6Research());
        assertTrue(result.compositions().getFirst().cause().isPresent());
        assertFalse(result.assessment().schemeComplete());
        var assessed = result.assessment().episodes().stream().filter(value -> value.identity().equals(fixture.episode().identity())).findFirst().orElseThrow();
        assertTrue(assessed.missing().contains(G2M6Contracts.Gate.ORDINARY_START));
        assertTrue(assessed.missing().contains(G2M6Contracts.Gate.LATER_ORDINARY_CONSUMPTION));
    }

    private static Fixture fixture(boolean withTerminal) throws Exception {
        byte[] held = resource("closed-ledger-original.json"), auto = resource("ordinary-start-auto48-original.json");
        byte[] originalPacket = M6SourceProducer.encodeEvidencePacket(held, ref("fixture:held", held), auto, ref("fixture:auto", auto),
                new M6SourceProducer.OrdinaryStartBinding(31254, "native-31254-6271ac8cd441", 214568));
        var original = M6SourceProducer.fromEvidencePacket(originalPacket, source("fixture:original-packet", originalPacket));
        var ordinary = original.episodes().stream().filter(value -> value.start().orElseThrow().origin() == G2M6Contracts.StartOrigin.ORDINARY_FULL_PLANNER).findFirst().orElseThrow();
        int startDate = ordinary.start().orElseThrow().independentActive().dateRaw();
        int baselineDate = startDate + 48, gainDate = startDate + 72, terminalDate = startDate + 96;
        ObjectNode ledger = (ObjectNode)StrictJson.parse(held, M6SourceProducer.MAX_BYTES);
        ObjectNode resolved = episodeNode(ledger, ordinary.identity().actionId());
        ObjectNode gain = M6TerminalSourceComposition.identityJson(ordinary.identity()); normalized(gain);
        gain.put("baseline_source_native_revision", 5001); gain.put("baseline_source_date_raw", baselineDate);
        gain.put("source_native_revision", 5002); gain.put("source_date_raw", gainDate);
        gain.put("tracked_instance_active", true); gain.put("incremental_named_gain_observed", true);
        gain.putObject("previous_scheme_sway_opinion").put("observed", true).put("present", false).putNull("value");
        gain.putObject("scheme_sway_opinion").put("observed", true).put("present", true).put("value", 25);
        consume(gain, 5003, gainDate + 1); resolved.set("first_named_gain_intervention", gain);
        resolved.remove("terminal_intervention");
        if (withTerminal) {
            ObjectNode raw = completion(ordinary); raw.put("available", true); raw.put("snapshot_revision", 5004); raw.put("date_raw", terminalDate);
            raw.put("instance_source_observed", true); raw.put("instance_present", true); raw.put("storage_slot_reused", false);
            raw.put("exact_instance_join_ready", true); raw.put("native_status_observed", true); raw.put("native_status_raw", 1);
            raw.put("native_owner_raw", 0xffff_ffffL); raw.put("owner_matches_actor", false); raw.put("owner_cleared", true);
            raw.put("native_terminal_state_observed", true); raw.put("native_status_key", "terminated_unattributed");
            ObjectNode terminal = M6TerminalSourceComposition.identityJson(ordinary.identity()); normalized(terminal);
            terminal.put("source_native_revision", 5004); terminal.put("source_date_raw", terminalDate);
            terminal.put("instance_terminal_outcome_observed", true); terminal.put("native_status_key", "terminated_unattributed");
            terminal.put("terminal_cause_observed", false); terminal.put("terminal_cause", "unknown"); terminal.set("native_observation", raw);
            consume(terminal, 5005, terminalDate + 24); resolved.set("terminal_intervention", terminal);
        }
        byte[] synthetic = ledger.toString().getBytes(StandardCharsets.UTF_8);
        byte[] packet = M6SourceProducer.encodeEvidencePacket(synthetic, ref("synthetic:ledger", synthetic), auto, ref("fixture:auto", auto),
                new M6SourceProducer.OrdinaryStartBinding(31254, "native-31254-6271ac8cd441", 214568));
        var evidence = M6SourceProducer.fromEvidencePacket(packet, source("synthetic:packet", packet));
        var episode = evidence.episodes().stream().filter(value -> value.identity().equals(ordinary.identity())).findFirst().orElseThrow();
        return new Fixture(packet, evidence, episode, gainDate, terminalDate);
    }
    private static M6ServiceIntegration.EpisodeSources sources(Fixture fixture, int endDate, boolean causal) {
        var episode = fixture.episode(); ObjectNode execution = journal(episode, true), termination = journal(episode, false);
        ObjectNode parent = parent(episode), end = end(episode, causal);
        parent.put("date_raw", endDate); end.put("date_raw", endDate);
        ((ObjectNode)end.get("native_invocation")).put("pre_date_raw", endDate).put("post_date_raw", endDate);
        execution.withArray("records").add(parent); termination.withArray("records").add(end);
        return new M6ServiceIntegration.EpisodeSources(episode.identity().actionId(), inputs(null, execution, termination, null));
    }
    private static ObjectNode episodeNode(ObjectNode ledger, String action) {
        ObjectNode resolved = (ObjectNode)ledger.get("resolved"); if (resolved.get("action_id").textValue().equals(action)) return resolved;
        for (JsonNode row : resolved.withArray("previous_interventions")) if (row.get("action_id").textValue().equals(action)) return (ObjectNode)row;
        throw new IllegalArgumentException("fixture original action absent");
    }
    private static void normalized(ObjectNode row) { row.put("exact_ck3_build", M6SourceProducer.BUILD); row.put("exe_sha256", M6SourceProducer.EXE); }
    private static void consume(ObjectNode row, int revision, int date) { row.put("next_turn_consumed", true); row.put("following_native_revision", revision); row.put("following_date_raw", date); }
}
