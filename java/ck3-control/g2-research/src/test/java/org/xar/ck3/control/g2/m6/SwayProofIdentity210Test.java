package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Base64;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** New SOFTWARE JSON proofs; no native original, Root permission or live source is manufactured. */
public final class SwayProofIdentity210Test {
    private static final BigInteger REV = new BigInteger("9223372036854775815");
    private static final int DATE = 53290000;
    private static final long[][] PAIRS = {{-2, 0}, {0, -2}, {Integer.MIN_VALUE, Integer.MAX_VALUE}, {Integer.MAX_VALUE, Integer.MIN_VALUE}};

    @Test void currentSignedCompletionSurvivesCopiedProofColdRoundtripAndFollowing() {
        for (long[] pair : PAIRS) {
            Episode episode = episode(pair[0], pair[1], false); ObservationIdentity at = source(pair[0], REV, DATE);
            var state = observe(episode, at, completion(episode, at, 0));
            assertTrue(state.latest().orElseThrow().active());
            assertTrue(state.material().orElseThrow().trackedActive());
            assertEquals(pair[0], state.identity().actorCharacterId()); assertEquals(pair[1], state.identity().targetCharacterId());
            assertEquals(Integer.toUnsignedLong((int)pair[0]), StrictJson.parse(state.latest().orElseThrow().proof().inputs().completion().orElseThrow().bytes()).get("native_owner_raw").longValue());
            assertEquals(state, SwayLifecycle.decode(SwayLifecycle.encode(state)));
            var consumed = SwayLifecycle.consumeFollowing(state, source(pair[0], REV.add(BigInteger.ONE), DATE + 24));
            assertFalse(SwayLifecycle.hasPendingFollowing(consumed));
            assertEquals(consumed, SwayLifecycle.decode(SwayLifecycle.encode(consumed)));
        }
    }

    @Test void currentSignedCensusHeaderAndRowsPreserveTheirIndependentMaterialPlane() {
        for (long[] pair : PAIRS) {
            Episode episode = episode(pair[0], pair[1], false); ObservationIdentity at = source(pair[0], REV, DATE);
            ObjectNode census = census(episode, at);
            var state = censusState(episode, at, census);
            assertTrue(state.material().orElseThrow().trackedActive());
            assertTrue(state.latest().isEmpty()); assertTrue(state.terminal().isEmpty());
            assertEquals(state, SwayLifecycle.decode(SwayLifecycle.encode(state)));
            // A valid different census target is allowed, but cannot claim the tracked instance is active.
            ((ObjectNode)census.get("active_sway_instances").get(0)).put("target_character_id", 1);
            assertFalse(censusState(episode, at, census).material().orElseThrow().trackedActive());
        }
    }

    @Test void invalidCopiedPublicIdentityTokensCensusRowsAndQueryChangesAreRejected() {
        Episode episode = episode(-2, 0, false); ObservationIdentity at = source(-2, REV, DATE);
        var state = observe(episode, at, completion(episode, at, 0));
        for (String token : new String[]{"-1", "4294967294", "2147483648", "-2147483649", "\"0\"", "true", "0.0", "null"}) {
            ObjectNode persisted = (ObjectNode)StrictJson.parse(SwayLifecycle.encode(state), SwayLifecycle.MAX_BYTES);
            ObjectNode copied = (ObjectNode)StrictJson.parse(episode.originalResolved().bytes()); copied.put("target_character_id", "proof210-token");
            ((ObjectNode)persisted.get("proofs").get(0)).put("original_resolved", Base64.getEncoder().encodeToString(tokenWire(copied, token).bytes()));
            assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.decode(StrictJson.canonical(persisted, SwayLifecycle.MAX_BYTES)), token);
            ObjectNode rowBad = census(episode, at); ((ObjectNode)rowBad.get("active_sway_instances").get(0)).put("target_character_id", "proof210-token");
            ProjectionJson rowWire = tokenWire(rowBad, token);
            assertThrows(IllegalArgumentException.class, () -> censusState(episode, at, rowWire), token);
            ObjectNode headerBad = census(episode, at); headerBad.put("target_character_id", "proof210-token");
            ProjectionJson headerWire = tokenWire(headerBad, token);
            assertThrows(IllegalArgumentException.class, () -> censusState(episode, at, headerWire), token);
        }
        ObjectNode generation = census(episode, at); ((ObjectNode)generation.get("active_sway_instances").get(0)).put("scheme_instance_generation", 1);
        assertThrows(IllegalArgumentException.class, () -> censusState(episode, at, generation));
        ObjectNode stale = census(episode, at); stale.put("snapshot_revision", REV.subtract(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> censusState(episode, at, stale));
        assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.empty(episode.identity(), source(0, REV, DATE)));
    }

    @Test void privateRawOwnerLegacyBuildAndUnattributedTerminalRulesRemainStrict() {
        Episode episode = episode(-2, 0, false); ObservationIdentity at = source(-2, REV, DATE);
        ObjectNode wrongOwner = completion(episode, at, 0); wrongOwner.put("native_owner_raw", -2);
        assertThrows(IllegalArgumentException.class, () -> observe(episode, at, wrongOwner));
        var terminal = observe(episode, at, completion(episode, at, 1));
        assertTrue(terminal.terminal().orElseThrow().instanceTerminalOutcomeObserved());
        assertFalse(terminal.terminal().orElseThrow().terminalCauseObserved());
        assertTrue(terminal.terminal().orElseThrow().eventDateRaw().isEmpty());
        assertEquals(terminal, SwayLifecycle.decode(SwayLifecycle.encode(terminal)));
        Episode legacySigned = episode(-2, 0, true);
        assertThrows(IllegalArgumentException.class, () -> observe(legacySigned, at, completion(legacySigned, at, 0)));
        Episode legacyPositive = episode(7, 8, true); ObservationIdentity positiveAt = source(7, REV, DATE);
        var old = observe(legacyPositive, positiveAt, completion(legacyPositive, positiveAt, 0));
        assertTrue(old.latest().orElseThrow().active()); assertEquals(old, SwayLifecycle.decode(SwayLifecycle.encode(old)));
    }

    private static SwayLifecycle.State observe(Episode episode, ObservationIdentity at, ObjectNode completion) {
        return SwayLifecycle.observe(SwayLifecycle.empty(episode.identity(), at), episode,
                new M6TerminalSourceComposition.Inputs(Optional.of(json(completion)), Optional.empty(), Optional.empty(), Optional.of(json(opinion(episode, at)))), at);
    }
    private static SwayLifecycle.State censusState(Episode episode, ObservationIdentity at, ObjectNode census) {
        return censusState(episode, at, json(census));
    }
    private static SwayLifecycle.State censusState(Episode episode, ObservationIdentity at, ProjectionJson census) {
        return SwayLifecycle.observeCensusMaterial(SwayLifecycle.empty(episode.identity(), at), episode, census, json(opinion(episode, at)), at);
    }
    private static ProjectionJson tokenWire(ObjectNode row, String token) {
        String raw = new String(StrictJson.canonical(row, M6SourceProducer.MAX_BYTES), java.nio.charset.StandardCharsets.UTF_8);
        raw = raw.replace("\"proof210-token\"", token);
        return ProjectionJson.object(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8), M6SourceProducer.MAX_BYTES);
    }
    private static Episode episode(long actor, long target, boolean legacy) {
        Identity id = new Identity("software-proof210", actor, target, 0, 0); ObjectNode resolved = StrictJson.object();
        resolved.put("status", "applied"); resolved.put("postcondition_verified", true); resolved.put("action_id", id.actionId());
        resolved.put("actor_character_id", actor); resolved.put("target_character_id", target);
        ObjectNode receipt = resolved.putObject("native_receipt"); receipt.put("schema", "active-scheme-sway-formal-private-v1"); receipt.put("stage", "applied");
        receipt.put("postcondition_verified", true); receipt.put("action_id", id.actionId()); receipt.put("scheme_instance_id", 0); receipt.put("scheme_instance_generation", 0); build(receipt);
        if (legacy) {
            receipt.put("build_version", "1.20.0.3"); receipt.put("exact_ck3_build", "1.20.0.3");
            receipt.put("executable_sha256", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"); receipt.put("exe_sha256", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
        }
        return new Episode(id, Optional.empty(), Optional.empty(), Optional.empty(), json(resolved));
    }
    private static ObservationIdentity source(long actor, BigInteger revision, int date) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor), revision, BigInteger.valueOf(date)), "software210:" + revision, revision, "software210");
        return new ObservationIdentity("xenoamess-full-tower-eb9d2c1186", new GameGeneration(8000, new PythonOnlyUInt64(new BigInteger("134371234567890123"))), frame, 1);
    }
    private static ObjectNode identity(Episode episode) { ObjectNode row = M6TerminalSourceComposition.identityJson(episode.identity()); row.remove("action_id"); build(row); return row; }
    private static ObjectNode completion(Episode episode, ObservationIdentity at, int status) {
        ObjectNode row = identity(episode); row.put("schema", "xar.ck3.sway_completion.v1"); stamp(row, at); row.put("available", true);
        row.put("instance_present", true); row.put("instance_source_observed", true); row.put("storage_slot_reused", false); row.put("exact_instance_join_ready", true);
        row.put("native_owner_raw", status == 1 ? 0xffff_ffffL : Integer.toUnsignedLong((int)episode.identity().actorCharacterId())); row.put("owner_matches_actor", status == 0);
        row.put("native_status_observed", true); row.put("native_status_raw", status); row.put("native_terminal_state_observed", status == 1);
        row.put("native_status_key", status == 1 ? "terminated_unattributed" : "continue"); row.put("terminal_cause_observed", false); row.put("terminal_cause", "unknown"); return row;
    }
    private static ObjectNode opinion(Episode episode, ObservationIdentity at) {
        ObjectNode row = identity(episode); row.put("schema", "xar.ck3.sway-outcome-opinion-v1"); stamp(row, at); row.put("available", true); row.put("target_opinion_of_actor", 61);
        row.putObject("scheme_sway_opinion").put("observed", true).put("present", true).put("value", 20);
        row.putObject("sway_blocker_opinion").put("observed", true).put("present", false).putNull("value"); return row;
    }
    private static ObjectNode census(Episode episode, ObservationIdentity at) {
        ObjectNode row = identity(episode); row.put("schema", "active-scheme-sway-private-read-v1"); stamp(row, at);
        row.putArray("active_sway_instances").addObject().put("scheme_instance_id", 0).put("scheme_instance_generation", 0).put("target_character_id", episode.identity().targetCharacterId()); return row;
    }
    private static void stamp(ObjectNode row, ObservationIdentity at) { row.put("snapshot_revision", at.frame().identity().nativeRevision()); row.put("date_raw", at.frame().identity().dateRaw()); }
    private static void build(ObjectNode row) { row.put("build_version", M6SourceProducer.BUILD); row.put("executable_sha256", M6SourceProducer.EXE); row.put("exact_ck3_build", M6SourceProducer.BUILD); row.put("exe_sha256", M6SourceProducer.EXE); }
    private static ProjectionJson json(JsonNode row) { return ProjectionJson.object(StrictJson.canonical(row, M6SourceProducer.MAX_BYTES), M6SourceProducer.MAX_BYTES); }
}
