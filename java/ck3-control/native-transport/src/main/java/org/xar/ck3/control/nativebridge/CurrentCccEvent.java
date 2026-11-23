package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fixed xccc.1001 authored .d/.f DATA. Actual private native query custody supplies authority. */
public final class CurrentCccEvent {
    public static final String SCHEMA = "ck3.ccc_event.current267_request.v1";
    public static final String SOURCE_SCHEMA = "ck3.ccc_event.current267_source.v1";
    public static final String RESULT_SCHEMA = "ck3.ccc_event.current267_result.v1";
    public static final String BACKEND = "ck3-1.21.0.3-native-application-main-ccc-event";
    public static final String DEFINITION_KEY = "xccc.1001";

    public enum Action {
        QUERY("query", "query-ccc-event-current-v1", "game.query.current-ccc-event.v1"),
        SELECT_TIER_FOUR("select_tier_four", "select-ccc-event-tier-four-current-v1", "game.command.select-current-ccc-event-tier-four.v1"),
        SELECT_TEMPORARY_CANCEL("select_temporary_cancel", "select-ccc-event-temporary-cancel-current-v1", "game.command.select-current-ccc-event-temporary-cancel.v1");
        private final String wire, step, capability;
        Action(String wire, String step, String capability) { this.wire = wire; this.step = step; this.capability = capability; }
        public String wire() { return wire; }
        public String step() { return step; }
        public String capability() { return capability; }
        public boolean queryOnly() { return this == QUERY; }
        public static Action parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown CCC fixed event action");
        }
    }
    private CurrentCccEvent() { }

    public static NativeRequest request(CoreFrame.Partial actual, Action action, BigInteger provider,
            BigInteger query, Optional<Integer> instanceId) {
        Objects.requireNonNull(actual); Objects.requireNonNull(action); Objects.requireNonNull(instanceId);
        CurrentLetter.unsigned(provider, false); CurrentLetter.unsigned(query, false);
        CurrentCccActorTransition.requireCore(actual.prefix());
        StrictJson.require(actual.build() == ExactCk3Build.CK3_121003_STEAM_26785313, "Exact current267 Core required");
        instanceId.ifPresent(n -> StrictJson.require(n > 0, "Actual positive event instance required"));
        StrictJson.require(action.queryOnly() ? provider.signum() == 0 && query.signum() == 0 && instanceId.isEmpty()
                : provider.signum() > 0 && query.signum() > 0 && instanceId.isPresent(), "Fixed bookmark query/action custody differs");
        var b = actual.build();
        var claim = StrictJson.object().put("schema", SCHEMA).put("game_version", b.version())
                .put("executable_sha256", b.executableSha256()).put("adapter_id", b.coreFrameAdapterId())
                .put("backend", BACKEND).put("action", action.wire())
                .put("provider_generation", provider).put("query_sequence", query);
        claim.set("expected_core", core(actual.prefix()));
        if (instanceId.isPresent()) claim.put("instance_id", instanceId.orElseThrow()); else claim.putNull("instance_id");
        var fields = StrictJson.object(); fields.set("ccc_event", claim); fields.set("arguments", StrictJson.object());
        // Outer request ID and original deadline belong exclusively to the transport.
        return new NativeRequest(action.step(), action.capability(), new RawJson(StrictJson.canonical(fields)));
    }

    static ObjectNode core(CoreFrame.Prefix p) {
        return StrictJson.object().put("date_raw", p.dateRaw()).put("speed", p.speed()).put("paused", p.paused())
                .put("local_player_id", p.localPlayerId()).put("map_ready", p.mapReady()).put("has_played_character", p.hasPlayedCharacter())
                .put("played_character_id", p.playedCharacterId()).put("played_character_alive", p.playedCharacterAlive());
    }
    static int i32(JsonNode value) throws IOException {
        return NativeWire.integer(value, BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
    }
    static boolean bool(ObjectNode object, String key) throws IOException {
        var value = object.get(key);
        if (value == null || !value.isBoolean()) throw new IOException("Actual CCC event boolean required: " + key);
        return value.booleanValue();
    }
    static BigInteger decimal(ObjectNode object, String key) throws IOException {
        String text = NativeWire.text(object.get(key));
        if (!text.matches("0|[1-9][0-9]{0,19}")) throw new IOException("Canonical uint64 string required: " + key);
        var n = new BigInteger(text); CurrentLetter.unsigned(n, false); return n;
    }
    static void identity(ObjectNode object, String key, String expected) throws IOException {
        if (!NativeWire.text(object.get(key)).equals(expected)) throw new IOException("Exact CCC event identity differs: " + key);
    }
}
