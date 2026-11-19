package org.xar.ck3.control.nativebridge;

import java.util.Objects;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Builds request data from a partial core frame; it conveys no dispatch or completion authority. */
public final class CoreClockControl {
    public static final String SCHEMA = "ck3_1210_core_clock_control_v1";
    public static final String BACKEND = "ck3-1.21.0-native-headless-main-thread";

    private CoreClockControl() {}

    public enum Step {
        PAUSE_MAP("pause-map"),
        RESUME_MAP("resume-map"),
        SET_SPEED_1("set-speed-1"),
        SET_SPEED_2("set-speed-2"),
        SET_SPEED_3("set-speed-3"),
        SET_SPEED_4("set-speed-4"),
        SET_SPEED_5("set-speed-5"),
        SAVE_CHECKPOINT("save-checkpoint");

        private final String wire;

        Step(String wire) { this.wire = wire; }

        public String wire() { return wire; }

        public String requiredCapability() { return "game.command." + wire; }

        public static Step fromWire(String wire) {
            Objects.requireNonNull(wire, "step");
            for (Step step : values()) {
                if (step.wire.equals(wire)) return step;
            }
            throw new IllegalArgumentException("unsupported core clock control step");
        }
    }

    public static NativeRequest request(Step step, CoreFrame.Partial frame) {
        Objects.requireNonNull(step, "step");
        Objects.requireNonNull(frame, "frame");
        StrictJson.require(frame.build()!=ExactCk3Build.CK3_1210_STEAM_26757580||step!=Step.SAVE_CHECKPOINT,
                "this hotfix Core clock profile does not qualify SAVE");
        var fields = StrictJson.object();
        fields.set("core_clock_control", claim(frame));
        return new NativeRequest(step.wire(), step.requiredCapability(),
                new RawJson(StrictJson.canonical(fields)));
    }

    static ObjectNode claim(CoreFrame.Partial frame) {
        Objects.requireNonNull(frame, "frame");
        StrictJson.require(ExactCk3Build.florinCoreFullBuild(frame.build().version(),frame.build().executableSha256()).isPresent(),
                "core clock control requires the exact CK3 1.21.0 build");
        var prefix = frame.prefix();
        var control = StrictJson.object();
        control.put("schema", SCHEMA);
        control.put("game_version", frame.build().version());
        control.put("executable_sha256", frame.build().executableSha256());
        control.put("adapter_id", frame.build().coreFullAdapterId());
        control.put("backend", BACKEND);
        control.put("date_raw", prefix.dateRaw());
        control.put("speed", prefix.speed());
        control.put("paused", prefix.paused());
        control.put("local_player_id", prefix.localPlayerId());
        control.put("map_ready", prefix.mapReady());
        control.put("has_played_character", prefix.hasPlayedCharacter());
        control.put("played_character_id", prefix.playedCharacterId());
        control.put("played_character_alive", prefix.playedCharacterAlive());
        return control;
    }
}
