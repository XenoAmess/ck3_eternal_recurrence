package org.xar.ck3.control.wave3.runtime.timelineowner;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Assessment;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Diagnostics;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Field;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Frame;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.PlayedCharacter;

/** Exact versioned operation envelope and declared projections of extensible existing SDK frames. */
public final class TimelineOwnerCodec {
    public static final String INPUT_SCHEMA = "xar.ck3.timeline-owner-facts-request/v1";
    public static final String OUTPUT_SCHEMA = "xar.ck3.timeline-owner-facts/v1";
    private TimelineOwnerCodec() { }

    public enum Operation { CHANGE, PAUSE_OWNER, RESUME_OWNER, POPUP_OWNER }

    public static Assessment assess(byte[] raw) {
        JsonNode row = StrictJson.parse(raw);
        require(row.isObject(), "timeline owner request object required");
        require(INPUT_SCHEMA.equals(StrictJson.text(row.get("schema"))), "timeline owner schema differs");
        Operation operation = operation(StrictJson.text(row.get("operation")));
        StrictJson.object(row, operation == Operation.POPUP_OWNER
                ? Set.of("schema", "operation", "previous", "refreshed", "settled")
                : Set.of("schema", "operation", "previous", "refreshed"));
        Frame previous = frame(row.get("previous")), refreshed = frame(row.get("refreshed"));
        return switch (operation) {
            case CHANGE -> TimelineOwner.change(previous, refreshed);
            case PAUSE_OWNER -> TimelineOwner.pauseOwner(previous, refreshed);
            case RESUME_OWNER -> TimelineOwner.resumeOwner(previous, refreshed);
            case POPUP_OWNER -> TimelineOwner.popupOwner(previous, refreshed, frame(row.get("settled")));
        };
    }

    public static Frame frame(JsonNode value) {
        require(value != null && value.isObject(), "actual semantic frame projection required");
        return new Frame(integerField(value.get("date_raw")), boolField(value.get("paused")), integerField(value.get("speed")),
                boolField(value.get("map_ready")), field(value.get("active_event"), node -> UiIdentity.fromJson(node, true)),
                field(value.get("pending_character_interaction"), node -> UiIdentity.fromJson(node, false)),
                textField(value.get("one_life_terminal_reason")), integerField(value.get("episode_character_id")),
                textField(value.get("episode_run_id")), integerField(value.get("local_player_id")),
                field(value.get("played_character"), TimelineOwnerCodec::played),
                field(value.get("diagnostics"), TimelineOwnerCodec::diagnostics),
                integerField(value.get("revision")), integerField(value.get("native_revision")));
    }

    public static byte[] encode(Assessment value) {
        ObjectNode row = StrictJson.object(); row.put("schema", OUTPUT_SCHEMA);
        row.put("kind", value.kind().name().toLowerCase(Locale.ROOT)); row.put("reason", value.reason().name().toLowerCase(Locale.ROOT));
        row.put("replay_allowed", false); row.put("action_admission_granted", false);
        row.put("source_admission_granted", false); row.put("saved_day_credit", 0);
        return StrictJson.canonical(row);
    }

    public static Assessment decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "kind", "reason", "replay_allowed",
                "action_admission_granted", "source_admission_granted", "saved_day_credit"));
        require(OUTPUT_SCHEMA.equals(StrictJson.text(row.get("schema"))), "timeline owner facts schema differs");
        for (String name : Set.of("replay_allowed", "action_admission_granted", "source_admission_granted")) {
            require(row.get(name).isBoolean() && !row.get(name).booleanValue(), "facts cannot grant permission");
        }
        StrictJson.integer(row.get("saved_day_credit"), 0, 0);
        String kind = StrictJson.text(row.get("kind")), reason = StrictJson.text(row.get("reason"));
        require(kind.matches("[a-z_]+") && reason.matches("[a-z_]+"), "canonical lowercase fact states required");
        return new Assessment(TimelineOwner.Kind.valueOf(kind.toUpperCase(Locale.ROOT)),
                TimelineOwner.Reason.valueOf(reason.toUpperCase(Locale.ROOT)));
    }

    static Field<BigInteger> integerField(JsonNode value) {
        return field(value, node -> { require(node.isIntegralNumber(), "actual integer required; no bool/float/string"); return node.bigIntegerValue(); });
    }
    private static Field<Boolean> boolField(JsonNode value) {
        return field(value, node -> { require(node.isBoolean(), "actual boolean required"); return node.booleanValue(); });
    }
    private static Field<String> textField(JsonNode value) { return field(value, StrictJson::text); }
    private static <T> Field<T> field(JsonNode value, Function<JsonNode, T> parser) {
        if (value == null) { return Field.missing(); }
        if (value.isNull()) { return Field.explicitNull(); }
        return Field.of(parser.apply(value));
    }
    private static PlayedCharacter played(JsonNode value) {
        require(value.isObject(), "played character object required");
        return new PlayedCharacter(integerField(value.get("character_id")), boolField(value.get("alive")));
    }
    private static Diagnostics diagnostics(JsonNode value) {
        require(value.isObject(), "diagnostics object required");
        return new Diagnostics(integerField(value.get("bridge_pid")), integerField(value.get("connection_generation")));
    }
    private static Operation operation(String value) {
        return switch (value) {
            case "change" -> Operation.CHANGE; case "pause_owner" -> Operation.PAUSE_OWNER;
            case "resume_owner" -> Operation.RESUME_OWNER; case "popup_owner" -> Operation.POPUP_OWNER;
            default -> throw new IllegalArgumentException("unknown timeline owner operation");
        };
    }
}
