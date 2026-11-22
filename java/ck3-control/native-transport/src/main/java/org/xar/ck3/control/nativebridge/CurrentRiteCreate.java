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

/** CREATE-family DATA only. Actual private same-transport custody supplies effect authority. */
public final class CurrentRiteCreate {
    public static final String SCHEMA = "ck3.rite_create.current267_request.v1";
    public static final String SOURCE_SCHEMA = "ck3.rite_create.current267_source.v1";
    public static final String RESULT_SCHEMA = "ck3.rite_create.current267_result.v1";
    public static final String BACKEND = "ck3-1.21.0.3-native-application-main-rite-create";
    public static final String STEP = "current-rite-create-v1";
    public static final String CAPABILITY = "game.command.current-rite-create.v1";
    public static final long MAXIMUM_RITE_ID = 0xffff_fffeL;

    public enum Action {
        QUERY("query"), CREATE("create"), QUERY_CONFIRMATION("query_confirmation"), ACCEPT_CONFIRMATION("accept_confirmation");
        private final String wire;
        Action(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public boolean queryOnly() { return this == QUERY || this == QUERY_CONFIRMATION; }
        static Action parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown current Rite CREATE action");
        }
    }
    private CurrentRiteCreate() { }

    public static NativeRequest request(CoreFrame.Partial actual, Action action, long sourceRiteId,
            BigInteger provider, BigInteger query) {
        Objects.requireNonNull(actual); Objects.requireNonNull(action);
        unsigned(provider, false); unsigned(query, false); requireRiteId(sourceRiteId);
        StrictJson.require(actual.build() == ExactCk3Build.CK3_121003_STEAM_26785313, "Exact current267 Core required");
        CurrentLetter.requirePrefix(actual.prefix());
        StrictJson.require(action == Action.QUERY ? provider.signum() == 0 && query.signum() == 0
                : provider.signum() > 0 && query.signum() > 0, "CREATE private query/original-Create custody role differs");
        var build = actual.build();
        var claim = StrictJson.object().put("schema", SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256()).put("adapter_id", build.coreFrameAdapterId())
                .put("backend", BACKEND).put("action", action.wire()).put("expected_source_rite_id", sourceRiteId)
                .put("provider_generation", provider.toString()).put("query_sequence", query.toString());
        var p = actual.prefix();
        claim.putObject("expected_core").put("date_raw", p.dateRaw()).put("speed", p.speed()).put("paused", p.paused())
                .put("local_player_id", p.localPlayerId()).put("map_ready", p.mapReady()).put("has_played_character", p.hasPlayedCharacter())
                .put("played_character_id", p.playedCharacterId()).put("played_character_alive", p.playedCharacterAlive());
        var fields = StrictJson.object(); fields.set("rite_create", claim); fields.set("arguments", StrictJson.object());
        // Only the transport supplies the original outer request ID and deadline.
        return new NativeRequest(STEP, CAPABILITY, new RawJson(StrictJson.canonical(fields)));
    }

    static void requireRiteId(long value) {
        StrictJson.require(value >= 0 && value <= MAXIMUM_RITE_ID, "Actual uint32 Rite ID except FFFFFFFF required");
    }
    static long riteId(JsonNode value) throws IOException {
        return NativeWire.integer(value, BigInteger.ZERO, BigInteger.valueOf(MAXIMUM_RITE_ID)).longValueExact();
    }
    static boolean bool(ObjectNode object, String key) throws IOException {
        var value = object.get(key);
        if (value == null || !value.isBoolean()) throw new IOException("Actual Rite CREATE boolean required: " + key);
        return value.booleanValue();
    }
    static int i32(JsonNode value) throws IOException {
        return NativeWire.integer(value, BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
    }
    static void unsigned(BigInteger value, boolean positive) {
        Objects.requireNonNull(value);
        StrictJson.require(value.signum() >= 0 && (!positive || value.signum() > 0)
                && value.compareTo(NativeWire.UINT64_MAX) <= 0, "Canonical uint64 required");
    }
    static BigInteger decimal(ObjectNode object, String key) throws IOException {
        String text = NativeWire.text(object.get(key));
        if (!text.matches("0|[1-9][0-9]{0,19}")) throw new IOException("Canonical uint64 string required: " + key);
        var value = new BigInteger(text); unsigned(value, false); return value;
    }
    static long signedRaw(ObjectNode object, String key) throws IOException {
        String text = NativeWire.text(object.get(key));
        if (!text.matches("0|-?[1-9][0-9]{0,18}")) throw new IOException("Canonical signed64 string required: " + key);
        return new BigInteger(text).longValueExact();
    }
    static void identity(ObjectNode object, String key, String expected) throws IOException {
        if (!NativeWire.text(object.get(key)).equals(expected)) throw new IOException("Exact Rite CREATE identity mismatch: " + key);
    }
}
