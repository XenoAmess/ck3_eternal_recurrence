package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Readonly DATA encoding. No action lease, actor override or mutation permission. */
public final class CurrentRiteCreationBlockers {
    public static final String SCHEMA = "ck3.rite_creation_blockers.current267_request.v1";
    public static final String SOURCE_SCHEMA = "ck3.rite_creation_blockers.current267_source.v1";
    public static final String RESULT_SCHEMA = "ck3.rite_creation_blockers.current267_result.v1";
    public static final String BACKEND = "ck3-1.21.0.3-native-application-main-rite-creation-blockers";
    public static final String STEP = "query-current-rite-creation-blockers-v1";
    public static final String CAPABILITY = "game.query.current-rite-creation-blockers.v1";
    public static final String ACTION = "query_blockers";
    public static final long MAXIMUM_RITE_ID = 0xffff_fffeL;

    private CurrentRiteCreationBlockers() { }

    public static NativeRequest request(CoreFrame.Partial actual, long expectedSourceRiteId) {
        Objects.requireNonNull(actual);
        StrictJson.require(actual.build() == ExactCk3Build.CK3_121003_STEAM_26785313,
                "Exact current267 Core required");
        requirePrefix(actual.prefix()); requireRiteId(expectedSourceRiteId);
        var build = actual.build();
        var claim = StrictJson.object().put("schema", SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256()).put("adapter_id", build.coreFrameAdapterId())
                .put("backend", BACKEND).put("action", ACTION).put("expected_source_rite_id", expectedSourceRiteId);
        claim.set("expected_core", prefix(actual.prefix()));
        var fields = StrictJson.object();
        fields.set("rite_creation_blockers", claim);
        fields.set("arguments", StrictJson.object());
        // The transport supplies the original outer request ID and deadline exactly once.
        return new NativeRequest(STEP, CAPABILITY, new RawJson(StrictJson.canonical(fields)));
    }

    static void requireRiteId(long value) {
        StrictJson.require(value >= 0 && value <= MAXIMUM_RITE_ID, "Actual uint32 Rite ID except FFFFFFFF required");
    }
    static long riteId(JsonNode value) throws IOException {
        return NativeWire.integer(value, BigInteger.ZERO, BigInteger.valueOf(MAXIMUM_RITE_ID)).longValueExact();
    }
    static String text(JsonNode value) throws IOException {
        if (value == null || !value.isTextual()) throw new IOException("Actual blockers string required, empty allowed");
        String text = value.textValue(); requireText(text); return text;
    }
    static void requireText(String text) {
        Objects.requireNonNull(text);
        for (int offset = 0; offset < text.length();) {
            char first = text.charAt(offset++);
            if (Character.isHighSurrogate(first)) {
                StrictJson.require(offset < text.length() && Character.isLowSurrogate(text.charAt(offset)),
                        "Unpaired high surrogate is not valid UTF8"); ++offset;
            } else StrictJson.require(!Character.isLowSurrogate(first), "Unpaired low surrogate is not valid UTF8");
        }
        StrictJson.require(text.getBytes(StandardCharsets.UTF_8).length <= 16384, "Actual blockers text exceeds read bound");
        // Actual length-delimited NUL/control/richtext DATA is preserved without filtering.
    }

    static void requirePrefix(CoreFrame.Prefix p) {
        Objects.requireNonNull(p);
        StrictJson.require(p.speed() >= 1 && p.speed() <= 5 && p.paused() && p.localPlayerId() >= 0
                && p.mapReady() && p.hasPlayedCharacter() && p.playedCharacterId() != -1
                && p.playedCharacterAlive(), "Actual paused living map Core required");
    }

    static ObjectNode prefix(CoreFrame.Prefix p) {
        return StrictJson.object().put("date_raw", p.dateRaw()).put("speed", p.speed()).put("paused", p.paused())
                .put("local_player_id", p.localPlayerId()).put("map_ready", p.mapReady())
                .put("has_played_character", p.hasPlayedCharacter()).put("played_character_id", p.playedCharacterId())
                .put("played_character_alive", p.playedCharacterAlive());
    }

    static boolean bool(ObjectNode object, String key) throws IOException {
        var value = object.get(key);
        if (value == null || !value.isBoolean()) throw new IOException("Rite creation blockers boolean required: " + key);
        return value.booleanValue();
    }

    static int i32(JsonNode value) throws IOException {
        return NativeWire.integer(value, BigInteger.valueOf(Integer.MIN_VALUE),
                BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
    }

    static void unsigned(BigInteger value, boolean positive) {
        Objects.requireNonNull(value);
        StrictJson.require(value.signum() >= 0 && (!positive || value.signum() > 0)
                && value.compareTo(NativeWire.UINT64_MAX) <= 0, "Canonical uint64 required");
    }

    static BigInteger decimal(ObjectNode object, String key) throws IOException {
        var text = NativeWire.text(object.get(key));
        if (!text.matches("0|[1-9][0-9]{0,19}")) throw new IOException("Canonical uint64 string required: " + key);
        var value = new BigInteger(text);
        unsigned(value, false);
        return value;
    }

    static void identity(ObjectNode object, String key, String expected) throws IOException {
        if (!NativeWire.text(object.get(key)).equals(expected))
            throw new IOException("Exact Rite creation blockers identity mismatch: " + key);
    }
}
