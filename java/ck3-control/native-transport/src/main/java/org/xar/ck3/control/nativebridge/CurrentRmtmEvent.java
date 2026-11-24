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

/** Two fixed RMTM event channels; one authored0 option each. Actual private native query custody supplies authority. */
public final class CurrentRmtmEvent {
    public static final String SCHEMA = "ck3.rmtm_event.current267_request.v1";
    public static final String SOURCE_SCHEMA = "ck3.rmtm_event.current267_source.v1";
    public static final String RESULT_SCHEMA = "ck3.rmtm_event.current267_result.v1";
    public static final String BACKEND = "ck3-1.21.0.3-native-application-main-rmtm-event";
    public static final String SUMMARY_DEFINITION = "rmtm.1001";
    public static final String CHAOS_DEFINITION = "tgp_dynastic_cycle.0081";

    public enum Action {
        QUERY_SUMMARY("query_summary","query-rmtm-summary-current-v1","game.query.current-rmtm-summary.v1"),
        ACK_SUMMARY("ack_summary","ack-rmtm-summary-current-v1","game.command.ack-current-rmtm-summary.v1"),
        QUERY_CHAOS("query_chaos","query-rmtm-chaos-current-v1","game.query.current-rmtm-chaos.v1"),
        ACK_CHAOS("ack_chaos","ack-rmtm-chaos-current-v1","game.command.ack-current-rmtm-chaos.v1"),
        CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE("choose_post_succession_first_available",
                "choose-rmtm-post-succession-first-available-current-v1",
                "game.command.choose-current-rmtm-post-succession-first-available.v1");
        private final String wire, step, capability;
        Action(String wire, String step, String capability) { this.wire = wire; this.step = step; this.capability = capability; }
        public String wire() { return wire; }
        public String step() { return step; }
        public String capability() { return capability; }
        public boolean queryOnly() { return this==QUERY_SUMMARY||this==QUERY_CHAOS; }
        public boolean chaos(){return this==QUERY_CHAOS||this==ACK_CHAOS;}
        public Action queryAction(){return chaos()?QUERY_CHAOS:QUERY_SUMMARY;}
        public Action ackAction(){return chaos()?ACK_CHAOS:ACK_SUMMARY;}
        public String definition(){return chaos()?CHAOS_DEFINITION:SUMMARY_DEFINITION;}
        public static Action parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown RMTM fixed event action");
        }
    }
    private CurrentRmtmEvent() { }

    public static NativeRequest request(CoreFrame.Partial actual, Action action, BigInteger provider,
            BigInteger query, Optional<Integer> instanceId) {
        Objects.requireNonNull(actual); Objects.requireNonNull(action); Objects.requireNonNull(instanceId);
        CurrentLetter.unsigned(provider, false); CurrentLetter.unsigned(query, false);
        CurrentRmtmActorTransition.requireCore(actual.prefix());
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
        var fields = StrictJson.object(); fields.set("rmtm_event", claim); fields.set("arguments", StrictJson.object());
        // Outer request ID and original deadline belong exclusively to the transport.
        return new NativeRequest(action.step(), action.capability(), new RawJson(StrictJson.canonical(fields)));
    }

    /** Derived readonly DATA only; this record is not a Native lease, prepared command or actor-epoch proof. */
    public record PostSuccessionChoice(int instanceId, int authoredOptionIndex) {
        public PostSuccessionChoice {
            StrictJson.require(instanceId > 0 && authoredOptionIndex >= 0 && authoredOptionIndex < 64,
                    "Actual event instance and bounded authored option index required");
        }
    }
    /** Exact mirror of the Native finite policy; no caller-supplied option index or event definition is accepted. */
    public static Optional<PostSuccessionChoice> postSuccessionChoice(CurrentRmtmEventSource source,
            int actualActor, int instanceId) {
        Objects.requireNonNull(source);
        if (instanceId <= 0 || !source.caseBound() || !source.sampledTwice() || !source.eventCensus().censusComplete())
            return Optional.empty();
        var specialized = java.util.Set.of("rmtm.1001", "tgp_dynastic_cycle.0081", "lyd.1", "lyd.1000", "lyd.1002", "lyd.1032",
                "ep3_laamps.0003", "bookmark.1070", "gdp_guelph_ghibelline.0500", "xqol.100", "sxat.2", "sxat.4", "xccc.1001");
        CurrentLydSource.EventRow event = null;
        for (var row : source.eventCensus().events()) if (row.instanceId() == instanceId) {
            if (event != null) return Optional.empty();
            event = row;
        }
        if (event == null || event.recipientCharacterId() != actualActor || !event.namedRootBound()
                || !event.windowVisible() || !event.windowEnabled() || specialized.contains(event.definitionKey()))
            return Optional.empty();
        Integer first = null;
        for (var option : event.options()) {
            if (option.permittedRole().isPresent() || option.sourceBoundOptionKey().isPresent()) return Optional.empty();
            if (option.nativeCanSelect() && !option.text().isEmpty()
                    && (first == null || option.authoredOptionIndex() < first)) first = option.authoredOptionIndex();
        }
        return first == null ? Optional.empty() : Optional.of(new PostSuccessionChoice(instanceId, first));
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
        if (value == null || !value.isBoolean()) throw new IOException("Actual RMTM event boolean required: " + key);
        return value.booleanValue();
    }
    static BigInteger decimal(ObjectNode object, String key) throws IOException {
        String text = NativeWire.text(object.get(key));
        if (!text.matches("0|[1-9][0-9]{0,19}")) throw new IOException("Canonical uint64 string required: " + key);
        var n = new BigInteger(text); CurrentLetter.unsigned(n, false); return n;
    }
    static void identity(ObjectNode object, String key, String expected) throws IOException {
        if (!NativeWire.text(object.get(key)).equals(expected)) throw new IOException("Exact RMTM event identity differs: " + key);
    }
}
