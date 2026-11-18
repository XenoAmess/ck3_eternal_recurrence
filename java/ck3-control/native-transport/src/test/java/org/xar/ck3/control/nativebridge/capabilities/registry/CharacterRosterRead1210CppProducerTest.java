package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RawRankedRulerCandidates1210;

/** Actual RAM-reader->wire stdout is mandatory. Later owner/model mutations are untrusted DATA counterexamples,
 * never actual executor, public availability, model-source or Family qualification receipts.
 */
final class CharacterRosterRead1210CppProducerTest {
    private static final String PROPERTY = "xar.native.character-roster1210.cppJsonl";
    private static final int ACTOR = 0x81000001, PEER = 0xFE000002;
    private static final List<String> CASES = List.of("reader_observed", "reader_lifecycle_changed", "owner_missing",
            "revision_changed", "connection_changed", "wrong_tuple");
    private record Sample(String name, byte[] packet, CharacterRosterRead1210.Capture capture) { }

    @Test void actualReaderToWireRemainsOfflineOrUnqualifiedAndReplaysOriginalPacketAndData() throws Exception {
        for (Sample sample : samples()) {
            var actual = sample.capture();
            assertFalse(actual.applicationMainObserved()); assertFalse(actual.rosterAvailable()); assertTrue(actual.sourceProof().isEmpty());
            assertFalse(actual.familyScope().transportInstanceObserved());
            assertEquals("transport_instance_and_model_source_not_observed", actual.familyScope().reason());
            assertEquals(sample.name().startsWith("reader_") ? CharacterRosterRead1210.SourceKind.OFFLINE_FIXTURE
                    : CharacterRosterRead1210.SourceKind.UNQUALIFIED, actual.sourceKind());
            var replay = CharacterRosterRead1210.replay(actual);
            assertArrayEquals(sample.packet(), replay.originalPacket().orElseThrow().bytes());
            assertArrayEquals(actual.originalResult().bytes(), replay.originalResult().bytes());
            assertArrayEquals(actual.manager().original(), replay.manager().original());
            assertEquals(actual.manager().identity(), replay.manager().identity());
            if (sample.name().equals("reader_observed")) {
                assertTrue(actual.manager().observation().available());
                assertEquals(53177016, actual.manager().observation().frame().dateRaw());
                assertEquals(5, actual.manager().observation().frame().speed());
                assertEquals(List.of(PEER, 0, 3, ACTOR), actual.manager().observation().members().stream().map(row -> row.characterId().value()).toList());
                assertFalse(actual.manager().observation().members().get(2).alive());
            } else assertFalse(actual.manager().observation().available());
        }
    }
    @Test void originalCommandCorrelationAndOuterRoleFlagsCannotBePromoted() throws Exception {
        var actual = sample("reader_observed");
        assertThrows(IllegalArgumentException.class, () -> CharacterRosterRead1210.decodeCommandResult(actual.packet(), "other-request"));
        for (String flag : List.of("model_source_observed", "same_owner_family_join_available", "all_living_complete", "interaction_candidates_complete")) {
            ObjectNode packet = tree(actual.packet()); result(packet).put(flag, true);
            assertThrows(IllegalArgumentException.class, () -> decode(packet, actual.name()), flag);
        }
        ObjectNode promoted = tree(actual.packet()); result(promoted).put("application_main_observed", true);
        assertThrows(IllegalArgumentException.class, () -> decode(promoted, actual.name()));
        ObjectNode alias = tree(actual.packet()); result(alias).put("roster_available", true);
        assertThrows(IllegalArgumentException.class, () -> decode(alias, actual.name()));
        ObjectNode changed = tree(actual.packet()); ((ObjectNode) result(changed).at("/data/frame")).put("played_character_id", -1);
        assertThrows(IllegalArgumentException.class, () -> decode(changed, actual.name()));
    }
    @Test void rawFamilyDataCounterexamplesKeepScoresAndManagerMembershipSeparateWithoutOwnerProof() throws Exception {
        var actual = sample("reader_observed").capture();
        var original = family(ACTOR, "89", 7, PEER);
        var audit = FamilyRosterData1210.audit(actual, original, request(ACTOR));
        assertEquals(FamilyRosterData1210.UnjoinedReason.MANAGER_OWNER_NOT_OBSERVED, audit.reason());
        assertArrayEquals(original.bytes(), audit.originalFamily().bytes());
        var family = assertInstanceOf(RawRankedRulerCandidates1210.Partial.class, audit.familyData());
        assertEquals(List.of(10, -5), family.sample().rows().stream().map(row -> row.nativeCandidateScore()).toList());
        assertEquals(List.of(id(0), id(PEER)), audit.separateManagerData().managerMembers().rows().stream().map(row -> row.requestedId()).toList());
        assertFalse(audit.sameOwnerFamilyJoinAvailable()); assertFalse(audit.allLivingComplete()); assertFalse(audit.interactionCandidatesComplete());
        var otherGeneration = FamilyRosterData1210.audit(actual, family(ACTOR, "89", 7, 0xFD000002), request(ACTOR));
        assertInstanceOf(CharacterManagerObservation1210.MemberAbsent.class,
                otherGeneration.separateManagerData().managerMembers().rows().get(1).result());
    }
    @Test void reportedOwnerFieldsStillCannotSupplyMissingModelSourceAndStaleFieldsRemainDistinct() throws Exception {
        // Adversarial reported-proof DATA, not an owner occurrence or Native fixture positive.
        var reported = reportedOwner(sample("reader_observed"));
        var same = FamilyRosterData1210.audit(reported, family(ACTOR, "89", 7, PEER), request(ACTOR));
        assertEquals(FamilyRosterData1210.UnjoinedReason.TRANSPORT_INSTANCE_AND_MODEL_SOURCE_NOT_OBSERVED, same.reason());
        assertFalse(same.sameOwnerFamilyJoinAvailable()); assertFalse(same.transportInstanceObserved());
        for (var variant : List.of(family(0x82000001, "89", 7, PEER), family(ACTOR, "90", 7, PEER), family(ACTOR, "89", 8, PEER))) {
            int actor = ((ObjectNode) FullJsonTree.parse(variant.bytes(), 32768)).path("frame").path("actor_full_id").intValue();
            var changed = FamilyRosterData1210.audit(reported, variant, request(actor));
            assertEquals(FamilyRosterData1210.UnjoinedReason.REPORTED_OWNER_OR_FRAME_MISMATCH, changed.reason());
        }
        ObjectNode wrongModel = (ObjectNode) FullJsonTree.parse(family(ACTOR, "89", 7, PEER).bytes(), 32768);
        ((ObjectNode) wrongModel.get("scope")).put("candidate_source", "other_character_strategy");
        assertThrows(IllegalArgumentException.class, () -> FamilyRosterData1210.audit(reported, new RawJson(bytes(wrongModel)), request(ACTOR)));
        for (String key : List.of("native_revision", "connection_generation", "mailbox_sequence", "pump_epoch")) {
            ObjectNode original = tree(reported.originalPacket().orElseThrow().bytes());
            ((ObjectNode) result(original).get("source_proof")).put(key, 17);
            assertThrows(IllegalArgumentException.class, () -> decode(original, "reader_observed"), "proof counters require decimal strings: " + key);
        }
    }
    private static CharacterRosterRead1210.Capture reportedOwner(Sample original) throws Exception {
        ObjectNode packet = tree(original.packet()); ObjectNode r = result(packet);
        r.put("source_kind", "owned_actor").put("application_main_observed", true).put("roster_available", true).putNull("unavailable_reason");
        r.putObject("source_proof").put("source_domain", "character_manager_maintained_members")
                .put("native_revision", "17").put("connection_generation", "23").put("mailbox_sequence", "71")
                .put("pump_epoch", "89").put("owner_thread_id", 7).put("date_raw", 53177016).put("played_character_id", ACTOR);
        return decode(packet, original.name());
    }
    private static RawRankedRulerCandidates1210.Request request(int actor) {
        return new RawRankedRulerCandidates1210.Request(new RawRankedRulerCandidates1210.Counter("17"),
                new RawRankedRulerCandidates1210.Counter("23"), id(actor), 42, 2);
    }
    /** Synthetic raw Family DATA used only to challenge scope propagation; no actual Family output is substituted. */
    private static RawJson family(int actor, String pump, long owner, int peer) {
        ObjectNode n = StrictJson.object().put("schema", RawRankedRulerCandidates1210.SCHEMA).put("step", RawRankedRulerCandidates1210.STEP)
                .put("game_version", ExactCk3Build.CK3_1210.version()).put("executable_sha256", ExactCk3Build.CK3_1210.executableSha256())
                .put("adapter_id", CharacterManagerObservation1210.ADAPTER).put("status", "partial").put("read_only", true)
                .put("query_sequence", "1").put("raw_source_available", true).put("application_main_observed", true)
                .put("same_frame_verified", true).put("complete_context_qualified", false).put("public_capability_ready", false).putNull("unavailable_reason");
        n.putObject("scope").put("actor_equals_subject", true).put("candidate_source", "current_actor_strategy");
        n.putObject("frame").put("native_revision", "17").put("connection_generation", "23").put("pump_epoch", pump)
                .put("owner_thread_id", owner).put("date_raw", 53177016).put("actor_full_id", actor).put("subject_full_id", actor)
                .put("local_player_id", 7).put("paused", true).put("map_ready", true).put("actor_alive", true);
        var sample = n.putObject("sample").put("native_tier_index", 1).put("native_enumeration_cap", 2).put("native_scoring_cap", 2)
                .put("native_pool_count", 2).put("native_scored_count", 2).put("returned_count", 2);
        var rows = sample.putArray("rows"); rows.addObject().put("candidate_full_id", 0).put("native_candidate_score", 10);
        rows.addObject().put("candidate_full_id", peer).put("native_candidate_score", -5);
        return new RawJson(bytes(n));
    }
    private static List<Sample> samples() throws Exception {
        String configured = System.getProperty(PROPERTY), digest = System.getProperty(PROPERTY + ".sha256");
        if (configured == null || digest == null || !Path.of(configured).isAbsolute() || !digest.matches("[0-9a-f]{64}"))
            throw new java.io.IOException("NOT_RUN: actual roster RAM-reader stdout absolute path and SHA required");
        Path path = Path.of(configured); long size = Files.size(path);
        if (size <= 0 || size > 1024 * 1024) throw new java.io.IOException("bounded actual roster fixture stdout required");
        byte[] raw = Files.readAllBytes(path);
        assertEquals(size, raw.length); assertEquals(digest, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        var lines = java.nio.charset.StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT).onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT)
                .decode(java.nio.ByteBuffer.wrap(raw)).toString().lines().toList();
        assertEquals(CASES.size(), lines.size()); var samples = new ArrayList<Sample>();
        for (int index = 0; index < lines.size(); index++) {
            byte[] line = lines.get(index).getBytes(java.nio.charset.StandardCharsets.UTF_8);
            var envelope = StrictJson.object(FullJsonTree.parse(line, 65536), Set.of("case", "command_result"));
            String name = StrictJson.text(envelope.get("case")); assertEquals(CASES.get(index), name);
            byte[] packet = NativeWire.token(line, "command_result");
            samples.add(new Sample(name, packet, CharacterRosterRead1210.decodeCommandResult(packet, "roster-fixture-" + name)));
        }
        return List.copyOf(samples);
    }
    private static Sample sample(String name) throws Exception { return samples().stream().filter(x -> x.name().equals(name)).findFirst().orElseThrow(); }
    private static CharacterRosterRead1210.Capture decode(ObjectNode packet, String name) throws Exception {
        return CharacterRosterRead1210.decodeCommandResult(bytes(packet), "roster-fixture-" + name);
    }
    private static ObjectNode tree(byte[] raw) { return (ObjectNode) FullJsonTree.parse(raw, 65536); }
    private static ObjectNode result(ObjectNode packet) { return (ObjectNode) packet.get("result"); }
    private static byte[] bytes(ObjectNode value) { return FullJsonTree.encode(value, 65536); }
    private static NativeCharacterId id(int value) { return NativeCharacterId.of(value); }
}
