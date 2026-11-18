package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.FlorinWarIdentityCodec;
import org.xar.ck3.control.contracts.semantic.FlorinWarIdentityData;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.contracts.semantic.FlorinWarIdentityData.*;

/** Typed contract round trips are synthetic DATA. Optional integration reads only original packets emitted by the actual C++ reader/serializer. */
final class FlorinWarIdentityDataTest {
    private static final int ACTOR = -2130706431;
    private static final String ID = "war-data-test";
    private static List<UnavailableField> gaps() {
        return java.util.Arrays.stream(RichField.values()).map(field -> new UnavailableField(field, FlorinWarIdentityCodec.RICH_REASON)).toList();
    }
    private static Partial data(Side side, Score score) {
        NativeCharacterId actor = new NativeCharacterId(ACTOR), peer = new NativeCharacterId(0);
        Identity row = new Identity(new WarFullId(-2080374784), actor, side,
                side == Side.ATTACKER ? actor : peer, side == Side.DEFENDER ? actor : peer, peer, true,
                side == Side.ATTACKER ? List.of(actor, peer, actor) : List.of(peer),
                side == Side.DEFENDER ? List.of(actor, peer, actor) : List.of(peer), score, gaps());
        return new Partial(new AvailableCore(new Prefix(53177016, 5, true, 7, true, true, ACTOR, true)),
                List.of(row), score instanceof AvailableScore, new ScanMetrics(3, 2, 1, 4), score instanceof AvailableScore || ((UnavailableScore) score).nativeAttackerRaw().isPresent() ? 2 : 0);
    }
    private static ObjectNode json() { return FlorinWarIdentityCodec.encode(data(Side.ATTACKER, new AvailableScore(17, 17))); }
    private static ObjectNode row(ObjectNode root) { return (ObjectNode) root.get("active_wars").get(0); }
    private static void reject(Consumer<ObjectNode> change) {
        ObjectNode root = json(); change.accept(root);
        assertThrows(IllegalArgumentException.class, () -> FlorinWarIdentityCodec.read(root));
    }

    @Test void signedFullIdsOrderedDuplicatesObservedZeroAndCheckedDefenderSignRoundTrip() {
        for (Side side : Side.values()) for (int raw : new int[] {0, 17, -1234567}) {
            int relative = side == Side.ATTACKER ? raw : -raw;
            Partial original = data(side, new AvailableScore(raw, relative));
            assertEquals(original, FlorinWarIdentityCodec.read(FlorinWarIdentityCodec.encode(original)));
            Identity war = original.activeWars().getFirst();
            assertEquals(-2080374784, war.warId().value()); assertEquals(ACTOR, war.actualPlayerCharacterId().value());
            assertEquals(0, war.primaryOpponentCharacterId().value()); assertNotEquals(7, war.actualPlayerCharacterId().value());
            assertEquals(List.of(new NativeCharacterId(ACTOR), new NativeCharacterId(0), new NativeCharacterId(ACTOR)),
                    side == Side.ATTACKER ? war.attackerParticipantIds() : war.defenderParticipantIds());
        }
        ObjectNode zero = json(); row(zero).put("war_id", 0);
        assertEquals(0, ((Partial) FlorinWarIdentityCodec.read(zero)).activeWars().getFirst().warId().value());
    }

    @Test void unavailableScoresAndIdentityRetainOriginalNullValuesAndReasons() {
        Partial disabled = data(Side.ATTACKER, new UnavailableScore(OptionalInt.empty(), "active_wars_native_calls_not_permitted"));
        ObjectNode disabledJson = FlorinWarIdentityCodec.encode(disabled);
        assertTrue(row(disabledJson).get("player_relative_war_score").isNull());
        assertTrue(row(disabledJson).get("native_attacker_score_raw").isNull());
        assertEquals(disabled, FlorinWarIdentityCodec.read(disabledJson));
        Partial overflow = data(Side.DEFENDER, new UnavailableScore(OptionalInt.of(Integer.MIN_VALUE), "active_wars_relative_score_overflow"));
        assertEquals(overflow, FlorinWarIdentityCodec.read(FlorinWarIdentityCodec.encode(overflow)));
        Unavailable failed = new Unavailable(disabled.coreFrame(), true, 1, "active_wars_identity_changed");
        ObjectNode failedJson = FlorinWarIdentityCodec.encode(failed);
        assertTrue(failedJson.get("active_wars").isNull()); assertTrue(failedJson.get("war_slots_scanned").isNull());
        assertEquals(failed, FlorinWarIdentityCodec.read(failedJson));
        Partial empty = new Partial(disabled.coreFrame(), List.of(), true, new ScanMetrics(0, 0, 0, 0), 0);
        assertTrue(FlorinWarIdentityCodec.encode(empty).get("active_wars").isEmpty());
        assertNotEquals(empty, failed);
    }

    @Test void identityTokensAndSourceTuplesRejectCoercionsAndReadNeverRepairsInput() {
        for (String token : List.of("-1", "2147483648", "-2147483649", "4294967294", "1.0", "true", "null", "\"0\"")) {
            for (String field : List.of("war_id", "actual_player_character_id", "primary_attacker_character_id", "primary_defender_character_id", "primary_opponent_character_id"))
                reject(root -> row(root).set(field, StrictJson.parse(token.getBytes(StandardCharsets.UTF_8))));
        }
        for (String field : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend")) {
            ObjectNode invalid = json(); invalid.put(field, "wrong"); ObjectNode untouched = invalid.deepCopy();
            assertThrows(IllegalArgumentException.class, () -> FlorinWarIdentityCodec.read(invalid));
            assertEquals(untouched, invalid, "a decoder must not rewrite source tuple metadata");
            reject(root -> root.remove(field));
        }
        reject(root -> root.putNull("active_wars")); reject(root -> root.remove("active_wars"));
        reject(root -> row(root).put("player_side", "ATTACKER"));
    }

    @Test void sameActorSidePrimaryScoreAndEachRichGapAreMandatory() {
        reject(root -> row(root).putArray("defender_participant_ids").add(ACTOR));
        reject(root -> row(root).put("actual_player_character_id", -2113929214));
        reject(root -> row(root).put("primary_opponent_character_id", 1));
        reject(root -> row(root).put("player_is_primary_war_leader", false));
        reject(root -> row(root).put("player_relative_war_score", -17));
        reject(root -> row(root).putNull("native_attacker_score_raw"));
        reject(root -> root.put("score_complete", false));
        reject(root -> root.put("same_frame_ready", false));
        reject(root -> root.put("complete_snapshot", true));
        reject(root -> root.put("complete_active_wars_qualified", true));
        for (String field : List.of("targeted_title_ids", "war_objective_province_ids", "objective_province_states",
                "enemy_primary_default_raise_province_id", "allied_armies", "enemy_armies")) {
            reject(root -> ((ObjectNode) row(root).get("rich")).remove(field));
            reject(root -> ((ObjectNode) row(root).get("rich")).putArray(field));
            reject(root -> ((ObjectNode) row(root).get("rich").get(field)).put("status", "available"));
        }
        reject(root -> ((ObjectNode) root.get("core_frame")).put("played_character_id", 1));
        reject(root -> ((ObjectNode) root.get("core_frame")).put("paused", false));
        reject(root -> root.put("participant_records", 3));
    }

    @Test void exactOriginalEnvelopeOutboundAndResultFeedOnlyThePartialFullDataEntry() throws Exception {
        NativeActionPort.AckReceived ack = ack(json(), ID, FlorinWarIdentityCodec.STEP);
        var decoded = FlorinWarIdentityPublicCodec.decodeOutcome(ack);
        var projection = FlorinWarIdentityPublicCodec.projectPartialFull(ack);
        assertInstanceOf(FlorinWarIdentityPublicCodec.PartialFullData.class, projection);
        var partial = (FlorinWarIdentityPublicCodec.PartialFullData) projection;
        assertSame(ack, partial.original()); assertEquals(decoded, partial.warData());
        assertFalse(partial.completeSnapshot()); assertFalse(partial.completeActiveWarsQualified());
        assertEquals(((Partial) decoded).coreFrame(), partial.coreFrame());
        assertThrows(java.io.IOException.class, () -> FlorinWarIdentityPublicCodec.decodeOutcome(ack(json(), ID, "query-core-frame-v1")));
        var missingOutbound = new NativeActionPort.AckReceived(ack.requestId(), ack.nativeOk(), ack.originalResultToken(),
                ack.originalFrame(), ack.originalPacket());
        assertInstanceOf(FlorinWarIdentityPublicCodec.UnavailableRead.class,
                FlorinWarIdentityPublicCodec.projectPartialFull(missingOutbound));
        var unknown = new NativeActionPort.Unknown(ID, "response_wait_unknown", ack.outbound().orElseThrow().originalPacket(), Optional.empty());
        var unavailable = (FlorinWarIdentityPublicCodec.UnavailableRead) FlorinWarIdentityPublicCodec.projectPartialFull(unknown);
        assertSame(unknown, unavailable.original()); assertTrue(unavailable.reason().contains("never replayed"));
    }

    /** Enable only after the Native owner runs the real reader/serializer fixture; every matching command_result is decoded. */
    @Test @EnabledIfSystemProperty(named = "xar.florinWar.cppPacketDir", matches = ".+")
    void actualCppReaderSerializerPacketsReachTheSameStrictPartialFullEntry() throws Exception {
        Path directory = Path.of(System.getProperty("xar.florinWar.cppPacketDir"));
        for (String name : List.of("war-attacker", "war-defender", "war-zero-duplicates", "war-empty", "war-score-overflow",
                "war-score-guard", "war-score-changed", "war-owner-unavailable", "war-owner-changed")) {
            Path path = directory.resolve(name + ".json");
            assertTrue(Files.size(path) > 0 && Files.size(path) <= 1_048_576, "bounded actual C++ packet required");
            byte[] packet = Files.readAllBytes(path); JsonNode envelope = StrictJson.parse(packet);
            assertEquals(name, envelope.get("request_id").textValue());
            var data = FlorinWarIdentityPublicCodec.decodePacket(new RawJson(packet), name);
            assertEquals(data, FlorinWarIdentityCodec.read(FlorinWarIdentityCodec.encode(data)));
            byte[] framed = NativeWire.packet(packet);
            var command = (NativeWire.CommandResult) NativeWire.decode(framed);
            // Synthetic test outbound only; original C++ result bytes acquire no invented held/live custody.
            byte[] outbound = NativeWire.execute(name, FlorinWarIdentityCodec.STEP, BigInteger.ZERO, new byte[] {'{', '}'});
            var original = new NativeActionPort.AckReceived(name, true,
                    Optional.of(new RawJson(command.result().token().orElseThrow().value())), new RawJson(packet), framed,
                    Optional.of(new NativeActionPort.OutboundPacket(name, outbound)));
            var projected = (FlorinWarIdentityPublicCodec.PartialFullData) FlorinWarIdentityPublicCodec.projectPartialFull(original);
            assertEquals(data, projected.warData()); assertFalse(projected.completeSnapshot());
            assertFalse(projected.completeActiveWarsQualified()); assertArrayEquals(packet, projected.original().originalFrame().bytes());
            switch (name) {
                case "war-owner-unavailable", "war-owner-changed" -> {
                    assertInstanceOf(Unavailable.class, data);
                    assertEquals(name.equals("war-owner-changed") ? 1 : 0, data.nativeScoreCallsAttempted());
                    assertTrue(envelope.path("result").get("active_wars").isNull());
                }
                case "war-empty" -> {
                    Partial empty = (Partial) data; assertTrue(empty.activeWars().isEmpty());
                    assertTrue(empty.scoreComplete()); assertEquals(0, empty.nativeScoreCallsAttempted());
                }
                default -> {
                    Partial partial = (Partial) data; assertFalse(partial.activeWars().isEmpty());
                    Identity war = partial.activeWars().getFirst(); assertEquals(6, war.richFields().size());
                    if (name.equals("war-attacker")) assertEquals(new AvailableScore(17, 17), war.score());
                    if (name.equals("war-defender")) assertEquals(new AvailableScore(17, -17), war.score());
                    if (name.equals("war-zero-duplicates")) {
                        assertEquals(0, war.warId().value()); assertEquals(new AvailableScore(0, 0), war.score());
                        assertEquals(List.of(war.actualPlayerCharacterId(), new NativeCharacterId(0), war.actualPlayerCharacterId()),
                                war.attackerParticipantIds());
                    }
                    if (name.equals("war-score-overflow")) assertEquals(new UnavailableScore(OptionalInt.of(Integer.MIN_VALUE),
                            "active_wars_relative_score_overflow"), war.score());
                    if (name.equals("war-score-guard")) {
                        assertEquals(0, partial.nativeScoreCallsAttempted());
                        assertEquals(new UnavailableScore(OptionalInt.empty(), "active_wars_score_guard_unavailable"), war.score());
                    }
                    if (name.equals("war-score-changed")) assertEquals(new UnavailableScore(OptionalInt.empty(),
                            "active_wars_score_changed"), war.score());
                }
            }
        }
    }

    private static NativeActionPort.AckReceived ack(ObjectNode result, String id, String step) throws Exception {
        ObjectNode envelope = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode().put("type", "command_result")
                .put("protocol_version", 1).put("request_id", id).put("ok", true);
        envelope.set("result", result);
        RawJson original = RegistryJson.encode(envelope);
        byte[] packet = NativeWire.packet(original.bytes());
        var command = (NativeWire.CommandResult) NativeWire.decode(packet);
        byte[] outbound = NativeWire.execute(id, step, BigInteger.ZERO, new byte[] {'{', '}'});
        return new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(command.result().token().orElseThrow().value())), original,
                packet, Optional.of(new NativeActionPort.OutboundPacket(id, outbound)));
    }
}
