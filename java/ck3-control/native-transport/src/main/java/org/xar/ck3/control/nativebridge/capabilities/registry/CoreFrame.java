package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.util.List;
import java.util.Objects;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Named app-main prefix. It cannot be substituted for a complete Driver observation. */
public sealed interface CoreFrame permits CoreFrame.Partial, CoreFrame.Unavailable {
    ExactCk3Build build();
    String STEP = "query-core-frame-v1";
    String CAPABILITY = "game.query.core-frame.v1";
    List<String> EXCLUDED = List.of("treasury", "domain", "military", "campaign");
    Set<String> FIELDS = Set.of("schema","game_version","executable_sha256","adapter_id","backend","status",
            "complete_snapshot","core_available","application_main_observed","unavailable_reason",
            "excluded_snapshot_families","date_raw","speed","paused","local_player_id","map_ready",
            "has_played_character","played_character_id","played_character_alive");
    record Prefix(int dateRaw, int speed, boolean paused, int localPlayerId, boolean mapReady,
            boolean hasPlayedCharacter, int playedCharacterId, boolean playedCharacterAlive) {
        public Prefix {
            RegistryJson.require(speed >= 1 && speed <= 5, "public speed 1..5 required");
            RegistryJson.require(hasPlayedCharacter ? playedCharacterId != -1
                    : playedCharacterId == -1 && !playedCharacterAlive, "absent played-character sentinel drift");
        }
    }
    record Partial(ExactCk3Build build, Prefix prefix) implements CoreFrame {
        public Partial { Objects.requireNonNull(build); Objects.requireNonNull(prefix); }
        public Partial(Prefix prefix) { this(ExactCk3Build.CK3_12004, prefix); }
    }
    record Unavailable(ExactCk3Build build, boolean applicationMainObserved, String reason) implements CoreFrame {
        public Unavailable { Objects.requireNonNull(build); RegistryJson.require(reason != null && !reason.isEmpty(), "unavailable prefix requires a reason"); }
        public Unavailable(boolean applicationMainObserved, String reason) { this(ExactCk3Build.CK3_12004, applicationMainObserved, reason); }
    }
    static String schema(ExactCk3Build build) {
        return switch (build) {
            case CK3_12004 -> "ck3_12004_core_frame_v1";
            case CK3_1210 -> "ck3_1210_core_frame_v1";
        };
    }
    static CoreFrame decode(RawJson original) {
        ObjectNode row = RegistryJson.object(original); RegistryJson.keys(row, FIELDS);
        String version = RegistryJson.text(row.get("game_version"));
        String sha256 = RegistryJson.text(row.get("executable_sha256"));
        ExactCk3Build build;
        if (ExactCk3Build.CK3_12004.matches(version, sha256)) build = ExactCk3Build.CK3_12004;
        else if (ExactCk3Build.CK3_1210.matches(version, sha256)) build = ExactCk3Build.CK3_1210;
        else throw new IllegalArgumentException("core frame exact source mismatch");
        RegistryJson.require(schema(build).equals(RegistryJson.text(row.get("schema")))
                && ("ck3-" + build.version() + "-msvc-x64").equals(RegistryJson.text(row.get("adapter_id")))
                && ("ck3-" + build.version() + "-native-headless-main-thread").equals(RegistryJson.text(row.get("backend"))), "core frame exact source mismatch");
        RegistryJson.require(!RegistryJson.bool(row.get("complete_snapshot")), "core frame must remain partial");
        List<String> excluded = RegistryJson.array(row.get("excluded_snapshot_families")).stream().map(RegistryJson::text).toList();
        RegistryJson.require(excluded.equals(EXCLUDED), "core excluded families mismatch");
        boolean available = RegistryJson.bool(row.get("core_available"));
        boolean observed = RegistryJson.bool(row.get("application_main_observed"));
        if (!available) {
            RegistryJson.require("unavailable".equals(RegistryJson.text(row.get("status"))), "core unavailable status mismatch");
            for (String key : List.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"))
                RegistryJson.require(row.get(key).isNull(), "unavailable prefix must retain explicit null: " + key);
            return new Unavailable(build, observed, RegistryJson.text(row.get("unavailable_reason")));
        }
        RegistryJson.require("partial".equals(RegistryJson.text(row.get("status"))) && observed && row.get("unavailable_reason").isNull(), "observed core partial required");
        return new Partial(build, new Prefix(RegistryJson.int32(row.get("date_raw")), RegistryJson.int32(row.get("speed")),
                RegistryJson.bool(row.get("paused")), RegistryJson.int32(row.get("local_player_id")), RegistryJson.bool(row.get("map_ready")),
                RegistryJson.bool(row.get("has_played_character")), RegistryJson.int32(row.get("played_character_id")), RegistryJson.bool(row.get("played_character_alive"))));
    }
}

