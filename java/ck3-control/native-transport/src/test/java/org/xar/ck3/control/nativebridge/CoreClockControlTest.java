package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

class CoreClockControlTest {
    private static final Set<String> CONTROL_FIELDS = Set.of(
            "schema", "game_version", "executable_sha256", "adapter_id", "backend", "date_raw",
            "speed", "paused", "local_player_id", "map_ready", "has_played_character",
            "played_character_id", "played_character_alive");

    @Test
    void everyFixedStepHasOnlyTheExactControlBodyAndCapability() {
        assertEquals(Set.of("pause-map", "resume-map", "set-speed-1", "set-speed-2", "set-speed-3",
                "set-speed-4", "set-speed-5", "save-checkpoint"),
                Arrays.stream(CoreClockControl.Step.values()).map(CoreClockControl.Step::wire)
                        .collect(Collectors.toSet()));
        var prefix = new CoreFrame.Prefix(1234567, 3, true, 45, true, true, 67, true);
        for (var step : CoreClockControl.Step.values()) {
            var request = CoreClockControl.request(step, current(prefix));
            assertEquals(step.wire(), request.step());
            assertEquals("game.command." + step.wire(), request.requiredCapability().orElseThrow());
            assertTrue(request.preparationEvidence().isEmpty());
            var root = StrictJson.parse(request.additionalFields().bytes());
            assertEquals(Set.of("core_clock_control"), fields(root));
            var body = root.get("core_clock_control");
            assertEquals(CONTROL_FIELDS, fields(body));
            assertEquals("ck3_1210_core_clock_control_v1", body.get("schema").textValue());
            assertEquals("1.21.0", body.get("game_version").textValue());
            assertEquals("2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc",
                    body.get("executable_sha256").textValue());
            assertEquals("ck3-1.21.0-msvc-x64", body.get("adapter_id").textValue());
            assertEquals("ck3-1.21.0-native-headless-main-thread", body.get("backend").textValue());
            assertPrefix(prefix, body);
            assertFalse(root.has("expected_revision"));
            assertFalse(body.has("expected_revision"));
            assertFalse(root.has("timestamp"));
            assertFalse(body.has("timestamp"));
        }
    }

    @Test
    void oldAndDefaultBuildFramesDoNotBecomeCurrentControlRequests() {
        var prefix = new CoreFrame.Prefix(1, 1, false, -1, false, false, -1, false);
        assertThrows(IllegalArgumentException.class, () -> CoreClockControl.request(
                CoreClockControl.Step.PAUSE_MAP, new CoreFrame.Partial(ExactCk3Build.CK3_12004, prefix)));
        assertThrows(IllegalArgumentException.class, () -> CoreClockControl.request(
                CoreClockControl.Step.SAVE_CHECKPOINT, new CoreFrame.Partial(prefix)));
        assertThrows(NullPointerException.class, () -> CoreClockControl.request(null, current(prefix)));
        assertThrows(NullPointerException.class, () -> CoreClockControl.request(CoreClockControl.Step.PAUSE_MAP, null));
    }

    @Test
    void aCompleteSnapshotClaimCannotSupplyTheRequiredPartialFrame() {
        var prefix = new CoreFrame.Prefix(1, 2, true, 1, true, true, 2, true);
        var original = CoreFramePublicCodec.encode(current(prefix));
        assertInstanceOf(CoreFrame.Partial.class, CoreFrame.decode(original));
        var fullClaim = (ObjectNode) StrictJson.parse(original.bytes());
        fullClaim.put("complete_snapshot", true);
        assertThrows(IllegalArgumentException.class,
                () -> CoreFrame.decode(new RawJson(StrictJson.canonical(fullClaim))));
    }

    @Test
    void signedIdentifiersAndAbsentCharacterSentinelsArePreservedWithoutInference() {
        var signed = new CoreFrame.Prefix(Integer.MIN_VALUE, 5, false, Integer.MIN_VALUE,
                false, true, Integer.MIN_VALUE + 1, false);
        assertPrefix(signed, control(CoreClockControl.Step.SET_SPEED_1, signed));
        var absent = new CoreFrame.Prefix(Integer.MAX_VALUE, 1, true, -1, true, false, -1, false);
        assertPrefix(absent, control(CoreClockControl.Step.RESUME_MAP, absent));
    }

    @Test
    void onlyTheExactFixedStepWiresAreAccepted() {
        for (var step : CoreClockControl.Step.values()) assertSame(step, CoreClockControl.Step.fromWire(step.wire()));
        for (var unknown : Set.of("query-core-frame-v1", "set-speed-0", "set-speed-6", "PAUSE_MAP",
                "pause-map ", "pause-map\n", "")) {
            assertThrows(IllegalArgumentException.class, () -> CoreClockControl.Step.fromWire(unknown));
        }
        assertThrows(NullPointerException.class, () -> CoreClockControl.Step.fromWire(null));
    }

    private static CoreFrame.Partial current(CoreFrame.Prefix prefix) {
        return new CoreFrame.Partial(ExactCk3Build.CK3_1210, prefix);
    }

    private static JsonNode control(CoreClockControl.Step step, CoreFrame.Prefix prefix) {
        return StrictJson.parse(CoreClockControl.request(step, current(prefix)).additionalFields().bytes())
                .get("core_clock_control");
    }

    private static Set<String> fields(JsonNode node) {
        assertTrue(node.isObject());
        var fields = new HashSet<String>();
        node.fieldNames().forEachRemaining(fields::add);
        return fields;
    }

    private static void assertPrefix(CoreFrame.Prefix expected, JsonNode body) {
        assertEquals(expected.dateRaw(), body.get("date_raw").intValue());
        assertEquals(expected.speed(), body.get("speed").intValue());
        assertEquals(expected.paused(), body.get("paused").booleanValue());
        assertEquals(expected.localPlayerId(), body.get("local_player_id").intValue());
        assertEquals(expected.mapReady(), body.get("map_ready").booleanValue());
        assertEquals(expected.hasPlayedCharacter(), body.get("has_played_character").booleanValue());
        assertEquals(expected.playedCharacterId(), body.get("played_character_id").intValue());
        assertEquals(expected.playedCharacterAlive(), body.get("played_character_alive").booleanValue());
    }
}
