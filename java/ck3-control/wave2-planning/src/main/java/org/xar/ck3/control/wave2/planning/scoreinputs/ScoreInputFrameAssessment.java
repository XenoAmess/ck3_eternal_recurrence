package org.xar.ck3.control.wave2.planning.scoreinputs;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.StrictJson;

/** Full pure _frame_reason branch, independent of cash/root DTO normalizers. */
public sealed interface ScoreInputFrameAssessment {
    record Matched(ScoreInputFrame source, ScoreInputFrame current) implements ScoreInputFrameAssessment {
        public Matched {
            require(source != null && current != null && source.equals(current), "exact original/current frame equality required");
        }
    }
    enum Failure {
        SOURCE_MISSING("existing_planning_source_frame_missing"),
        SOURCE_INCOMPLETE("existing_planning_source_frame_incomplete"),
        CURRENT_UNAVAILABLE("current_paused_player_frame_unavailable"),
        SOURCE_CHANGED("existing_planning_source_frame_changed");
        private final String wire;
        Failure(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    enum Field {
        SNAPSHOT_ID("snapshot_id"), REVISION("revision"), NATIVE_REVISION("native_revision"), DATE_RAW("date_raw"),
        EPISODE_RUN_ID("episode_run_id"), ACTOR_CHARACTER_ID("actor_character_id"), BRIDGE_PID("bridge_pid"),
        CONNECTION_GENERATION("connection_generation");
        private final String wire;
        Field(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    record Rejected(Failure failure, Field field) implements ScoreInputFrameAssessment {
        public Rejected {
            require(failure != null && ((failure == Failure.SOURCE_CHANGED) == (field != null)), "explicit frame rejection branch required");
        }
        public String reason() { return failure.wire() + (field == null ? "" : ":" + field.wire()); }
    }

    static ScoreInputFrameAssessment assess(ObjectNode snapshot, JsonNode rawSource) {
        require(snapshot != null, "ordinary snapshot object required");
        if (!(rawSource instanceof ObjectNode source)) { return rejected(Failure.SOURCE_MISSING); }
        if (!textEquals(source.get("schema"), "xar.ck3.planning-source-frame/v1")
                || !textEquals(source.get("status"), "complete")) { return rejected(Failure.SOURCE_INCOMPLETE); }
        if (!actualTrue(snapshot.get("paused")) || !actualTrue(snapshot.get("map_ready"))
                || !(snapshot.get("played_character") instanceof ObjectNode player)
                || !actualTrue(player.get("alive"))
                || !(snapshot.get("diagnostics") instanceof ObjectNode diagnostics)) {
            return rejected(Failure.CURRENT_UNAVAILABLE);
        }
        for (Field field : new Field[] {Field.SNAPSHOT_ID, Field.REVISION, Field.NATIVE_REVISION, Field.DATE_RAW, Field.EPISODE_RUN_ID}) {
            if (!sameTypedField(source.get(field.wire()), snapshot.get(field.wire()), field)) { return changed(field); }
        }
        if (!sameTypedField(source.get("actor_character_id"), player.get("character_id"), Field.ACTOR_CHARACTER_ID)) {
            return changed(Field.ACTOR_CHARACTER_ID);
        }
        for (Field field : new Field[] {Field.BRIDGE_PID, Field.CONNECTION_GENERATION}) {
            if (!sameTypedField(source.get(field.wire()), diagnostics.get(field.wire()), field)) { return changed(field); }
        }
        ObjectNode current = StrictJson.object();
        for (Field field : new Field[] {Field.SNAPSHOT_ID, Field.REVISION, Field.NATIVE_REVISION, Field.DATE_RAW, Field.EPISODE_RUN_ID}) {
            current.set(field.wire(), snapshot.get(field.wire()));
        }
        current.set("actor_character_id", player.get("character_id"));
        current.set("bridge_pid", diagnostics.get("bridge_pid"));
        current.set("connection_generation", diagnostics.get("connection_generation"));
        ObjectNode sourceProjection = StrictJson.object();
        for (Field field : Field.values()) { sourceProjection.set(field.wire(), source.get(field.wire())); }
        return new Matched(ScoreInputFrame.fromJson(sourceProjection), ScoreInputFrame.fromJson(current));
    }

    private static Rejected rejected(Failure failure) { return new Rejected(failure, null); }
    private static Rejected changed(Field field) { return new Rejected(Failure.SOURCE_CHANGED, field); }
    private static boolean actualTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean textEquals(JsonNode value, String expected) { return value != null && value.isTextual() && expected.equals(value.textValue()); }
    private static boolean sameTypedField(JsonNode left, JsonNode right, Field field) {
        if (left == null || right == null || left.isNull() || right.isNull()) { return false; }
        if (field == Field.SNAPSHOT_ID || field == Field.EPISODE_RUN_ID) {
            return left.isTextual() && right.isTextual() && !left.textValue().isEmpty() && left.textValue().equals(right.textValue());
        }
        if (!left.isIntegralNumber() || !right.isIntegralNumber()) { return false; }
        BigInteger minimum = switch (field) {
            case ACTOR_CHARACTER_ID, BRIDGE_PID -> BigInteger.ONE;
            case DATE_RAW -> BigInteger.valueOf(Integer.MIN_VALUE);
            default -> BigInteger.ZERO;
        };
        BigInteger maximum = switch (field) {
            case ACTOR_CHARACTER_ID, BRIDGE_PID -> ScoreInputFrame.UINT32_MAX;
            case DATE_RAW -> BigInteger.valueOf(Integer.MAX_VALUE);
            default -> StrictJson.UINT64_MAX;
        };
        return ScoreInputFrame.inRange(left.bigIntegerValue(), minimum, maximum)
                && ScoreInputFrame.inRange(right.bigIntegerValue(), minimum, maximum)
                && left.bigIntegerValue().equals(right.bigIntegerValue());
    }
}
