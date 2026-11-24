package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fixed entry request DATA. Private native custody supplies every actual target and permission. */
public final class CurrentLivingEntry {
    public static final String SCHEMA = "xar.living-entry.request/v1";
    public static final String SOURCE_SCHEMA = "xar.living-entry.source/v1";
    public static final String RESULT_SCHEMA = "xar.living-entry.result/v1";
    public static final String BACKEND = "current267-fixed-living-entry-v1";
    public static final String STEP = "ck3_121003_living_entry.execute";
    public static final String CAPABILITY = "game.command.current-living-fixed-entry.v1";
    public static final String MANAGE_DECISION = "xalw_manage_decision";

    public enum Action {
        QUERY_MANAGE("query_manage", CurrentLivingEntrySource.Kind.MANAGE, true),
        OPEN_MANAGE_LIST("open_manage_list", CurrentLivingEntrySource.Kind.MANAGE, false),
        OPEN_MANAGE_DETAIL("open_manage_detail", CurrentLivingEntrySource.Kind.MANAGE, false),
        CONFIRM_MANAGE("confirm_manage", CurrentLivingEntrySource.Kind.MANAGE, false),
        QUERY_INVENTORY_ENTRY("query_inventory_entry", CurrentLivingEntrySource.Kind.INVENTORY, true),
        OPEN_INVENTORY("open_inventory", CurrentLivingEntrySource.Kind.INVENTORY, false),
        QUERY_DETAIL_ENTRY("query_detail_entry", CurrentLivingEntrySource.Kind.DETAIL, true),
        OPEN_DETAIL("open_detail", CurrentLivingEntrySource.Kind.DETAIL, false);

        private final String wire;
        private final CurrentLivingEntrySource.Kind sourceKind;
        private final boolean queryOnly;
        Action(String wire, CurrentLivingEntrySource.Kind sourceKind, boolean queryOnly) {
            this.wire = wire; this.sourceKind = sourceKind; this.queryOnly = queryOnly;
        }
        public String wire() { return wire; }
        public CurrentLivingEntrySource.Kind sourceKind() { return sourceKind; }
        public boolean queryOnly() { return queryOnly; }
        public String step() { return STEP; }
        public String capability() { return CAPABILITY; }
        public static Action parse(String text) throws IOException {
            for (var action : values()) if (action.wire.equals(text)) return action;
            throw new IOException("Unknown fixed Living entry action");
        }
    }

    private CurrentLivingEntry() { }

    public static NativeRequest request(CoreFrame.Partial actual, Action action,
            BigInteger provider, BigInteger query) {
        Objects.requireNonNull(actual); Objects.requireNonNull(action);
        StrictJson.require(actual.build() == ExactCk3Build.CK3_121003_STEAM_26785313, "Exact current267 Core required");
        requirePrefix(actual.prefix());
        CurrentLivingInventoryQuery.unsigned(provider, false);
        CurrentLivingInventoryQuery.unsigned(query, false);
        StrictJson.require(action.queryOnly() ? provider.signum() == 0 && query.signum() == 0
                : provider.signum() > 0 && query.signum() > 0, "Original query/action generations differ");
        var build = actual.build();
        var claim = StrictJson.object().put("schema", SCHEMA).put("game_version", build.version())
                .put("executable_sha256", build.executableSha256()).put("adapter_id", build.coreFrameAdapterId())
                .put("backend", BACKEND).put("action", action.wire())
                .put("provider_generation", provider).put("query_sequence", query);
        claim.set("expected_core", CurrentLivingInventoryQuery.prefix(actual.prefix()));
        var fields = StrictJson.object(); fields.set("living_entry", claim);
        fields.set("arguments", StrictJson.object());
        // The dedicated Transport writes the strict8 envelope; ID/deadline/actor/target are not caller selectors.
        return new NativeRequest(STEP, CAPABILITY, new RawJson(StrictJson.canonical(fields)));
    }

    public static void requirePrefix(CoreFrame.Prefix prefix) {
        CurrentLivingInventoryQuery.requirePrefix(prefix);
    }

    static CoreFrame.Prefix readCore(JsonNode node) throws IOException {
        var p = StrictJson.object(node, java.util.Set.of("date_raw", "speed", "paused", "local_player_id",
                "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
        return new CoreFrame.Prefix(CurrentLivingInventoryQuery.i32(p.get("date_raw")),
                CurrentLivingInventoryQuery.i32(p.get("speed")), CurrentLivingInventoryQuery.bool(p, "paused"),
                CurrentLivingInventoryQuery.i32(p.get("local_player_id")), CurrentLivingInventoryQuery.bool(p, "map_ready"),
                CurrentLivingInventoryQuery.bool(p, "has_played_character"),
                CurrentLivingInventoryQuery.i32(p.get("played_character_id")), CurrentLivingInventoryQuery.bool(p, "played_character_alive"));
    }

    static void requireActualText(String text) {
        Objects.requireNonNull(text);
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (Character.isHighSurrogate(ch)) {
                StrictJson.require(i + 1 < text.length() && Character.isLowSurrogate(text.charAt(i + 1)),
                        "Unpaired actual-text surrogate"); i++;
            } else StrictJson.require(!Character.isLowSurrogate(ch), "Unpaired actual-text surrogate");
        }
        StrictJson.require(text.getBytes(StandardCharsets.UTF_8).length <= 16384, "Actual text exceeds16KiB UTF8");
        // Empty, embedded NUL, controls and richtext are real read DATA, not a write field.
    }

    static String actualText(JsonNode value) throws IOException {
        if (value == null || !value.isTextual()) throw new IOException("Actual text must be a string");
        String text = value.textValue(); requireActualText(text); return text;
    }
}
