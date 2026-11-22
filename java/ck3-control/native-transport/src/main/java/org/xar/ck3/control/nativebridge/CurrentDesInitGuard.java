package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Readonly DATA encoding. No action lease, actor override or initialization permission. */
public final class CurrentDesInitGuard {
    public static final String SCHEMA = "ck3.des_saved_game_init_guard.current267_request.v1";
    public static final String SOURCE_SCHEMA = "ck3.des_saved_game_init_guard.current267_source.v1";
    public static final String RESULT_SCHEMA = "ck3.des_saved_game_init_guard.current267_result.v1";
    public static final String BACKEND = "ck3-1.21.0.3-native-application-main-des-init-guard";
    public static final String STEP = "query-des-saved-game-init-guard-current-v1";
    public static final String CAPABILITY = "game.query.des-saved-game-init-guard-current.v1";
    public static final String ACTION = "query_guard";
    public static final String GUARD_KEY = "des_saved_game_initialize_gui";

    private CurrentDesInitGuard() { }

    public static NativeRequest request(CoreFrame.Partial actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(actual.build() == ExactCk3Build.CK3_121003_STEAM_26785313,
                "Exact current267 Core required");
        requirePrefix(actual.prefix());
        var build = actual.build();
        var claim = StrictJson.object().put("schema", SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256()).put("adapter_id", build.coreFrameAdapterId())
                .put("backend", BACKEND).put("action", ACTION);
        claim.set("expected_core", prefix(actual.prefix()));
        var fields = StrictJson.object();
        fields.set("des_init_guard", claim);
        fields.set("arguments", StrictJson.object());
        // The transport supplies the original outer request ID and deadline exactly once.
        return new NativeRequest(STEP, CAPABILITY, new RawJson(StrictJson.canonical(fields)));
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
        if (value == null || !value.isBoolean()) throw new IOException("DES init guard boolean required: " + key);
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
            throw new IOException("Exact DES init guard identity mismatch: " + key);
    }
}
