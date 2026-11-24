package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fixed AE2 request DATA; Native retains actual case identity and once custody. */
public final class CurrentZg361Ae2 {
    public static final String SCHEMA = "ck3.zg361_ae2.current267_request.v1";
    public static final String SOURCE_SCHEMA = "ck3.zg361_ae2.current267_source.v1";
    public static final String RESULT_SCHEMA = "ck3.zg361_ae2.current267_result.v1";
    public static final String BACKEND = "ck3-1.21.0.3-native-application-main-zg361-ae2";
    public static final String STEP = "ck3_121003_zg361_ae2.execute";
    public static final String QUERY_CAPABILITY = "game.query.current-zg361-ae2.v1";
    public static final String CONTROLS_CAPABILITY = "game.command.current-zg361-ae2-fixed-controls.v1";
    public static final String PAY_CAPABILITY = "game.command.current-zg361-ae2-pay-now.v1";
    public static final String REVIEW_QUERY_CAPABILITY = "game.query.current-zg361-review-requirements.v1";
    public static final String REVIEW_DETAIL_CAPABILITY = "game.command.current-zg361-review-detail.v1";
    public static final String REVIEW_DEFINITION = "zg361_review_now_decision";
    public static final String EVENT_DEFINITION = "zg361comp.1";
    public static final int AUTHORED_COUNT = 42;

    public enum Action {
        QUERY_CONTROLS("query_controls", CurrentZg361Ae2Source.Kind.CONTROLS, true),
        OPEN_CONTROLS_LIST("open_controls_list", CurrentZg361Ae2Source.Kind.CONTROLS, false),
        OPEN_PRESENT_DETAIL("open_present_detail", CurrentZg361Ae2Source.Kind.CONTROLS, false),
        CONFIRM_PRESENT("confirm_present", CurrentZg361Ae2Source.Kind.CONTROLS, false),
        QUERY_AE2("query_ae2", CurrentZg361Ae2Source.Kind.EVENTS, true),
        CHOOSE_PAY_NOW("choose_pay_now", CurrentZg361Ae2Source.Kind.EVENTS, false),
        OPEN_VERIFY_DETAIL("open_verify_detail", CurrentZg361Ae2Source.Kind.CONTROLS, false),
        CONFIRM_VERIFY("confirm_verify", CurrentZg361Ae2Source.Kind.CONTROLS, false),
        QUERY_REVIEW_REQUIREMENTS("query_review_requirements", CurrentZg361Ae2Source.Kind.REVIEW, true),
        OPEN_REVIEW_DETAIL("open_review_detail", CurrentZg361Ae2Source.Kind.REVIEW, false);

        private final String wire;
        private final CurrentZg361Ae2Source.Kind sourceKind;
        private final boolean queryOnly;
        Action(String wire, CurrentZg361Ae2Source.Kind sourceKind, boolean queryOnly) {
            this.wire = wire; this.sourceKind = sourceKind; this.queryOnly = queryOnly;
        }
        public String wire() { return wire; }
        public CurrentZg361Ae2Source.Kind sourceKind() { return sourceKind; }
        public boolean queryOnly() { return queryOnly; }
        public String step() { return STEP; }
        public String capability() {
            if (this == QUERY_REVIEW_REQUIREMENTS) return REVIEW_QUERY_CAPABILITY;
            if (this == OPEN_REVIEW_DETAIL) return REVIEW_DETAIL_CAPABILITY;
            return queryOnly ? QUERY_CAPABILITY : this == CHOOSE_PAY_NOW ? PAY_CAPABILITY : CONTROLS_CAPABILITY;
        }
        public static Action parse(String text) throws IOException {
            for (var action : values()) if (action.wire.equals(text)) return action;
            throw new IOException("Unknown fixed AE2 action");
        }
    }

    private CurrentZg361Ae2() { }

    public static NativeRequest request(CoreFrame.Partial actual, Action action,
            BigInteger provider, BigInteger query) {
        Objects.requireNonNull(actual); Objects.requireNonNull(action);
        StrictJson.require(actual.build() == ExactCk3Build.CK3_121003_STEAM_26785313, "Exact current267 Core required");
        requirePrefix(actual.prefix());
        CurrentLivingInventoryQuery.unsigned(provider, false);
        CurrentLivingInventoryQuery.unsigned(query, false);
        StrictJson.require(action.queryOnly() ? provider.signum() == 0 && query.signum() == 0
                : provider.signum() > 0 && query.signum() > 0, "AE2 query/action generations differ");
        var build = actual.build();
        var claim = StrictJson.object().put("schema", SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256()).put("adapter_id", build.coreFrameAdapterId())
                .put("backend", BACKEND).put("action", action.wire())
                .put("provider_generation", provider.toString()).put("query_sequence", query.toString());
        claim.set("expected_core", CurrentLivingInventoryQuery.prefix(actual.prefix()));
        var fields = StrictJson.object(); fields.set("zg361_ae2", claim);
        fields.set("arguments", StrictJson.object());
        // Transport supplies strict8 actor/target/ID/deadline; this is not a caller-selected case.
        return new NativeRequest(STEP, action.capability(), new RawJson(StrictJson.canonical(fields)));
    }

    public static void requirePrefix(CoreFrame.Prefix prefix) {
        CurrentLivingInventoryQuery.requirePrefix(prefix);
    }

    static CoreFrame.Prefix readCore(JsonNode node) throws IOException {
        var r = StrictJson.object(node, Set.of("date_raw", "speed", "paused", "local_player_id",
                "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
        return new CoreFrame.Prefix(CurrentLivingInventoryQuery.i32(r.get("date_raw")),
                CurrentLivingInventoryQuery.i32(r.get("speed")), CurrentLivingInventoryQuery.bool(r,"paused"),
                CurrentLivingInventoryQuery.i32(r.get("local_player_id")), CurrentLivingInventoryQuery.bool(r,"map_ready"),
                CurrentLivingInventoryQuery.bool(r,"has_played_character"),
                CurrentLivingInventoryQuery.i32(r.get("played_character_id")), CurrentLivingInventoryQuery.bool(r,"played_character_alive"));
    }

    static void requireActualText(String text, boolean embeddedNul) {
        Objects.requireNonNull(text);
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (Character.isHighSurrogate(ch)) {
                StrictJson.require(i + 1 < text.length() && Character.isLowSurrogate(text.charAt(i + 1)), "Unpaired AE2 text surrogate"); i++;
            } else StrictJson.require(!Character.isLowSurrogate(ch), "Unpaired AE2 text surrogate");
            StrictJson.require(embeddedNul || ch != 0, "Cached Letter text cannot contain embedded NUL");
        }
        StrictJson.require(text.getBytes(StandardCharsets.UTF_8).length <= 16384, "Actual AE2 text exceeds16KiB UTF8");
    }

    static String actualText(JsonNode node, boolean embeddedNul) throws IOException {
        if (node == null || !node.isTextual()) throw new IOException("Actual AE2 string required");
        String value = node.textValue(); requireActualText(value, embeddedNul); return value;
    }
}
