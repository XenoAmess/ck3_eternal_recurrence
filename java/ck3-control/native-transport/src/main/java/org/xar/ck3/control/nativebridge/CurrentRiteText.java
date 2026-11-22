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

/** Text-family DATA only. Actual private same-transport custody supplies effect authority. */
public final class CurrentRiteText {
    public static final String SCHEMA = "ck3.rite_text.current267_request.v1";
    public static final String SOURCE_SCHEMA = "ck3.rite_text.current267_source.v1";
    public static final String RESULT_SCHEMA = "ck3.rite_text.current267_result.v1";
    public static final String BACKEND = "ck3-1.21.0.3-native-application-main-rite-text";
    public static final String STEP = "current-rite-text-v1";
    public static final String CAPABILITY = "game.command.current-rite-text.v1";
    public static final long MAXIMUM_RITE_ID = 0xffff_fffeL;

    public enum Action {
        QUERY("query"), SET_NAME("set_name"), SET_DESCRIPTION("set_description");
        private final String wire;
        Action(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public boolean queryOnly() { return this == QUERY; }
        static Action parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown current Rite text action");
        }
    }
    private CurrentRiteText() { }

    public static NativeRequest request(CoreFrame.Partial actual, Action action, long sourceRiteId,
            BigInteger provider, BigInteger query, String text) {
        Objects.requireNonNull(actual); Objects.requireNonNull(action);
        unsigned(provider, false); unsigned(query, false); requireRiteId(sourceRiteId); requireText(action, text);
        StrictJson.require(actual.build() == ExactCk3Build.CK3_121003_STEAM_26785313, "Exact current267 Core required");
        CurrentLetter.requirePrefix(actual.prefix());
        StrictJson.require(action == Action.QUERY ? provider.signum() == 0 && query.signum() == 0
                : provider.signum() > 0 && query.signum() > 0, "Text private query custody role differs");
        var build = actual.build();
        var claim = StrictJson.object().put("schema", SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256()).put("adapter_id", build.coreFrameAdapterId())
                .put("backend", BACKEND).put("action", action.wire()).put("expected_source_rite_id", sourceRiteId)
                .put("provider_generation", provider.toString()).put("query_sequence", query.toString()).put("text", text);
        var p = actual.prefix();
        claim.putObject("expected_core").put("date_raw", p.dateRaw()).put("speed", p.speed()).put("paused", p.paused())
                .put("local_player_id", p.localPlayerId()).put("map_ready", p.mapReady()).put("has_played_character", p.hasPlayedCharacter())
                .put("played_character_id", p.playedCharacterId()).put("played_character_alive", p.playedCharacterAlive());
        var fields = StrictJson.object(); fields.set("rite_text", claim); fields.set("arguments", StrictJson.object());
        // Only the transport supplies the original outer request ID and deadline.
        return new NativeRequest(STEP, CAPABILITY, new RawJson(StrictJson.canonical(fields)));
    }

    /** Validates typed DATA only; this does not mint private query custody. */
    public static void requireText(Action action, String text) {
        Objects.requireNonNull(action); Objects.requireNonNull(text);
        if (action == Action.QUERY) {
            StrictJson.require(text.isEmpty(), "Rite text query must carry empty text"); return;
        }
        int scalars = scalarCount(text);
        boolean description = action == Action.SET_DESCRIPTION;
        StrictJson.require(scalars <= (description ? 400 : 30)
                && text.getBytes(StandardCharsets.UTF_8).length <= (description ? 1600 : 120),
                "Rite text exceeds native write bounds");
        for (int offset = 0; offset < text.length();) {
            int value = text.codePointAt(offset); offset += Character.charCount(value);
            boolean allowedControl = description && (value == '\n' || value == '\t');
            StrictJson.require(value >= 0x20 && value != 0x7f || allowedControl, "Rite text contains forbidden control");
        }
    }
    static String actualText(JsonNode value) throws IOException {
        if (value == null || !value.isTextual()) throw new IOException("Actual Rite text string required, empty allowed");
        String text = value.textValue(); requireActualText(text); return text;
    }
    static void requireActualText(String text) {
        Objects.requireNonNull(text); scalarCount(text);
        StrictJson.require(text.getBytes(StandardCharsets.UTF_8).length <= 4096,
                "Actual Rite CString must be valid Unicode within UTF8 read bounds");
    }
    private static int scalarCount(String text) {
        int count = 0;
        for (int offset = 0; offset < text.length(); ++count) {
            char first = text.charAt(offset++);
            if (Character.isHighSurrogate(first)) {
                StrictJson.require(offset < text.length() && Character.isLowSurrogate(text.charAt(offset)),
                        "Unpaired high surrogate is not canonical UTF8"); ++offset;
            } else StrictJson.require(!Character.isLowSurrogate(first), "Unpaired low surrogate is not canonical UTF8");
        }
        return count;
    }

    static void requireRiteId(long value) {
        StrictJson.require(value >= 0 && value <= MAXIMUM_RITE_ID, "Actual uint32 Rite ID except FFFFFFFF required");
    }
    static long riteId(JsonNode value) throws IOException {
        return NativeWire.integer(value, BigInteger.ZERO, BigInteger.valueOf(MAXIMUM_RITE_ID)).longValueExact();
    }
    static boolean bool(ObjectNode object, String key) throws IOException {
        var value = object.get(key);
        if (value == null || !value.isBoolean()) throw new IOException("Actual Rite text boolean required: " + key);
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
    static void identity(ObjectNode object, String key, String expected) throws IOException {
        if (!NativeWire.text(object.get(key)).equals(expected)) throw new IOException("Exact Rite text identity mismatch: " + key);
    }
}
