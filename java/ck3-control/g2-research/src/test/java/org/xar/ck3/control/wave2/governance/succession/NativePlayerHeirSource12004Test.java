package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.*;
import static org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirSource12004.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.*;

/** Native I/O boundary supplies original bytes, never a precomputed Java observer result. No live credit. */
final class NativePlayerHeirSource12004Test {
    private static final BigInteger PUBLIC = BigInteger.valueOf(900);
    private static final BigInteger NATIVE = BigInteger.valueOf(31);
    private static final int ACTOR = 31254, HEIR = -2147483647, DATE = 53144328;
    private static Frame frame(int actor) { return new Frame("native-31", PUBLIC, NATIVE, DATE, actor, 0); }

    @Test void originalNativeComponentRoundTripsSignedGenerationIdsAndIndependentRevisions() {
        Component c = component(ACTOR, HEIR, false);
        byte[] root = root(frame(ACTOR), c);
        Parsed parsed = parse(root, frame(ACTOR));
        assertEquals(State.LIVING_CANDIDATE, parsed.state()); assertEquals(HEIR, parsed.component().observation().candidateCharacterId());
        assertArrayEquals(encodeComponent(c), encodeComponent(parsed.component()));
        assertEquals(PUBLIC, frame(ACTOR).publicRevision()); assertNotEquals(PUBLIC, NATIVE);
        assertEquals(new Lineage(-2147483646, -2147483645), parsed.component().observation().candidateLineage());
    }
    @Test void missingExplicitNullAndObservedNullRemainThreeDifferentStates() {
        ObjectNode root = node(root(frame(ACTOR), component(ACTOR, HEIR, false)));
        ObjectNode body = (ObjectNode) root.get("campaign_root_context"); body.remove(COMPONENT);
        assertEquals(State.MISSING, parse(bytes(root), frame(ACTOR)).state());
        body.putNull(COMPONENT); assertEquals(State.EXPLICIT_NULL, parse(bytes(root), frame(ACTOR)).state());
        Component original = component(ACTOR, HEIR, false); Observation o = original.observation();
        Component empty = new Component(NATIVE, true, new Observation(true, null, false, true, o.before(), o.after(), true,
                false, ACTOR, -1, false, true, false, new Lineage(-1, -1), null));
        assertEquals(State.OBSERVED_NULL, parse(root(frame(ACTOR), empty), frame(ACTOR)).state());
    }
    @Test void boolFloatMissingUnknownFieldAndWrongSourceAreRejectedAtActualBoundary() {
        byte[] clean = root(frame(ACTOR), component(ACTOR, HEIR, false));
        for (String raw : new String[]{"true", "31.0", "\"31\""}) {
            ObjectNode changed = node(clean); ((ObjectNode) changed.get("binding")).set("native_revision", json(raw));
            assertThrows(IllegalArgumentException.class, () -> parse(bytes(changed), frame(ACTOR)));
        }
        ObjectNode missing = node(clean); nativeObservation(missing).remove("candidate_character_id");
        assertThrows(IllegalArgumentException.class, () -> parse(bytes(missing), frame(ACTOR)));
        ObjectNode extra = node(clean); nativeObservation(extra).put("continuation_allowed", true);
        assertThrows(IllegalArgumentException.class, () -> parse(bytes(extra), frame(ACTOR)));
        ObjectNode source = node(clean); ((ObjectNode) source.path("campaign_root_context").path(COMPONENT)).put("getter_rva", "0x28C17E0");
        assertThrows(IllegalArgumentException.class, () -> parse(bytes(source), frame(ACTOR)));
        String duplicate = new String(clean, StandardCharsets.UTF_8).replace("\"candidate_present\":true", "\"candidate_present\":true,\"candidate_present\":true");
        assertThrows(IllegalArgumentException.class, () -> parse(duplicate.getBytes(StandardCharsets.UTF_8), frame(ACTOR)));
    }
    @Test void unboundFixtureDeadAndUnavailableNeverBecomeLivingCandidates() {
        byte[] clean = root(frame(ACTOR), component(ACTOR, HEIR, false));
        ObjectNode fixture = node(clean); nativeObservation(fixture).put("source_fixture", true);
        assertEquals(State.FIXTURE, parse(bytes(fixture), frame(ACTOR)).state());
        ObjectNode unbound = node(clean); ((ObjectNode) unbound.path("campaign_root_context").path(COMPONENT)).put("parent_frame_bound", false);
        assertEquals(State.UNBOUND, parse(bytes(unbound), frame(ACTOR)).state());
        ObjectNode dead = node(clean); nativeObservation(dead).put("candidate_alive", false);
        assertEquals(State.DEAD_CANDIDATE, parse(bytes(dead), frame(ACTOR)).state());
        ObjectNode unavailable = node(clean); nativeObservation(unavailable).put("available", false).put("unavailable_reason", "native_read_failed");
        assertEquals(State.UNAVAILABLE, parse(bytes(unavailable), frame(ACTOR)).state());
        ObjectNode stale = node(clean); ((ObjectNode) nativeObservation(stale).get("after")).put("date_raw", DATE + 1);
        assertEquals(State.UNBOUND, parse(bytes(stale), frame(ACTOR)).state());
    }
    @Test void sourceReaderConsumesOriginalOwnerProducerAndPreservesLargeIdentityDecimals() {
        MemoryOwner owner = new MemoryOwner(ACTOR, "old-episode", "134056180000000001");
        Result actual = read(owner, new Limits(MAX_BYTES, 65536), owner.rootRef);
        Observed observed = assertInstanceOf(Observed.class, actual);
        assertEquals(State.LIVING_CANDIDATE, observed.component().state());
        assertEquals("16888498602938861", observed.session().executableFileId());
        assertEquals("134056180000000001", observed.session().game().creationFiletime());
        assertEquals(PUBLIC, observed.frame().publicRevision()); assertEquals(NATIVE, observed.frame().nativeRevision());
        assertTrue(owner.reads >= 6); assertEquals(0, owner.nativeCalls);
    }
    @Test void sourceReaderRejectsByteDriftMissingSessionAndBoolActorWithoutChangingSource() {
        MemoryOwner drift = new MemoryOwner(ACTOR, "old-episode", "134056180000000001");
        drift.data.put(drift.rootRef.path(), new byte[]{'{', '}'});
        assertInstanceOf(Unavailable.class, read(drift, new Limits(MAX_BYTES, 65536), drift.rootRef));
        MemoryOwner missing = new MemoryOwner(ACTOR, "old-episode", "134056180000000001"); missing.current = false;
        assertInstanceOf(Unavailable.class, read(missing, new Limits(MAX_BYTES, 65536), missing.rootRef));
        MemoryOwner bad = new MemoryOwner(ACTOR, "old-episode", "134056180000000001");
        ObjectNode root = node(bad.data.get(bad.rootRef.path())); ((ObjectNode) root.get("campaign_root_context")).put("player_character_id", true);
        bad.rootRef = bad.put("root", bytes(root));
        assertInstanceOf(Unavailable.class, read(bad, new Limits(MAX_BYTES, 65536), bad.rootRef));
    }
    @Test void pairRequiresActualControlledNativeHeirAndNewEpisodeAndKeepsNaturalDeathUnknown() {
        Observed before = observed(new MemoryOwner(ACTOR, "old-episode", "134056180000000001"));
        Observed after = observed(new MemoryOwner(HEIR, "new-episode", "134056180000000001"));
        ControlPair pair = compareControl(before, after);
        assertEquals(PairState.SELECTED_PLAYER_HEIR_NOW_CONTROLLED, pair.state());
        assertFalse(pair.submissionAuthorized()); assertFalse(pair.naturalDeathProven()); assertFalse(pair.realmPreservationProven());
        assertEquals(PairState.EPISODE_NOT_REBOUND, compareControl(before,
                observed(new MemoryOwner(HEIR, "old-episode", "134056180000000001"))).state());
        assertEquals(PairState.CONTROL_DIFFERS, compareControl(before,
                observed(new MemoryOwner(999, "new-episode", "134056180000000001"))).state());
        assertEquals(PairState.GAME_CHANGED, compareControl(before,
                observed(new MemoryOwner(HEIR, "new-episode", "134056180000000002"))).state());
    }

    private static Observed observed(MemoryOwner owner) { return assertInstanceOf(Observed.class, read(owner, new Limits(MAX_BYTES, 65536), owner.rootRef)); }
    private static Component component(int actor, int heir, boolean fixture) {
        Core core = new Core(DATE, true, 3, 0, true, true, actor, true);
        return new Component(NATIVE, true, new Observation(true, null, fixture, true, core, core, true, true,
                actor, heir, true, true, true, new Lineage(-2147483646, -2147483645), null));
    }
    private static byte[] root(Frame f, Component c) {
        ObjectNode out = StrictJson.object(); out.put("status", "available").put("query_sequence", 7);
        out.putObject("binding").put("snapshot_id", f.snapshotId()).put("revision", f.publicRevision())
                .put("native_revision", f.nativeRevision()).put("date_raw", f.dateRaw());
        ObjectNode root = out.putObject("campaign_root_context");
        root.put("status", "available").put("snapshot_revision", f.nativeRevision()).put("date_raw", f.dateRaw())
                .put("local_player_id", f.localPlayerId()).put("player_character_id", f.actorCharacterId()).put("player_character_alive", true);
        root.putObject("readiness").put("same_frame_ready", true); root.putObject("provenance").put("executable_sha256", EXE_SHA256);
        root.set(COMPONENT, StrictJson.parse(encodeComponent(c), MAX_BYTES)); return bytes(out);
    }
    private static ObjectNode nativeObservation(ObjectNode root) { return (ObjectNode) root.path("campaign_root_context").path(COMPONENT).path("observation"); }
    private static ObjectNode node(byte[] raw) { return (ObjectNode) StrictJson.parse(raw, MAX_BYTES); }
    private static JsonNode json(String raw) { return StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8)); }
    private static byte[] bytes(JsonNode node) { return StrictJson.canonical(node, MAX_BYTES); }

    private static final class MemoryOwner implements RootOwnedSources {
        final Map<String, byte[]> data = new HashMap<>(); final Session session; final RetainedArtifact artifact;
        ExactRef rootRef; int reads; int nativeCalls; boolean current = true;
        MemoryOwner(int actor, String episode, String birth) {
            ExactRef exe = new ExactRef("D:/fixtures/ck3.exe", 101040248L, EXE_SHA256);
            session = new Session("synthetic-machine", "one-session", new GameIdentity(1234, birth), episode, "2", exe,
                    "16888498602938861", "1791307594040564100");
            ObjectNode measurement = StrictJson.object(); measurement.put("schema", "xar.resume56-current-game-files-readonly-observation/v1")
                    .put("machine_id", session.machineId()).put("observed_at_utc", "2026-10-23T16:00:00Z");
            var files = measurement.putArray("observations");
            files.addObject().put("label", "game_exe").put("stable_during_read", true).put("path", exe.path()).put("bytes", exe.bytes())
                    .put("sha256", EXE_SHA256).put("file_id_decimal", session.executableFileId()).put("mtime_ns_decimal", session.executableMtimeNs());
            files.addObject().put("label", "launcher_settings").put("stable_during_read", true).put("raw_version", "1.20.0.4");
            ExactRef measured = put("measured", bytes(measurement));
            ObjectNode snap = StrictJson.object(); snap.put("snapshot_id", "native-31").put("revision", PUBLIC).put("native_revision", NATIVE)
                    .put("date_raw", DATE).put("episode_run_id", episode).put("paused", true).put("map_ready", true);
            snap.putObject("played_character").put("character_id", actor).put("alive", true);
            ObjectNode diagnostics = snap.putObject("diagnostics"); diagnostics.put("bridge_pid", 1234).put("connection_generation", 2);
            diagnostics.putObject("hello").put("pid", 1234).put("connection_generation", 2).put("ck3_build_match", true)
                    .put("expected_ck3_version", "1.20.0.4").put("expected_ck3_sha256", EXE_SHA256);
            ObjectNode result = StrictJson.object(); result.putNull("meta").putArray("content"); result.set("structured_content", snap);
            result.put("is_error", false).put("result_type", "complete");
            ObjectNode row = StrictJson.object(); row.put("started_at_utc", "2026-10-23T16:00:01Z").put("ended_at_utc", "2026-10-23T16:00:02Z")
                    .put("elapsed_seconds", 1).put("mcp_result_projection_json_utf8_bytes", bytes(result).length);
            row.putObject("request").put("sequence", 1).put("tool", "ck3_semantic_snapshot").putObject("arguments"); row.set("result", result);
            artifact = new RetainedArtifact(session, put("snapshot", bytes(row)), measured, "ck3_semantic_snapshot");
            rootRef = put("root", root(frame(actor), component(actor, actor == HEIR ? ACTOR : HEIR, false)));
        }
        ExactRef put(String key, byte[] raw) {
            String path = "D:/fixtures/" + key + ".json"; data.put(path, raw.clone());
            return new ExactRef(path, raw.length, G2RetainedNativeSourceProvider.sha256(raw));
        }
        @Override public Optional<Session> currentSession() { return current ? Optional.of(session) : Optional.empty(); }
        @Override public Optional<RetainedArtifact> selectedSource(Milestone m, ProjectionJson payload) { return Optional.of(artifact); }
        @Override public byte[] readExact(ExactRef ref, int maximum) throws IOException {
            reads++; byte[] raw = data.get(ref.path()); if (raw == null || raw.length > maximum) throw new IOException("missing or oversized"); return raw.clone();
        }
    }
}
