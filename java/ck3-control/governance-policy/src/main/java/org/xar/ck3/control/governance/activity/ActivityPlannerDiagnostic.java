package org.xar.ck3.control.governance.activity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared exact native planner metadata. This observation grants no configured cost or final Start legality. */
public final class ActivityPlannerDiagnostic {
    private ActivityPlannerDiagnostic() { }
    public enum Kind { ABSENT, FEAST_STAGE_ONE, FEAST_STAGE_TWO, FEAST_STAGE_FIVE, OTHER }
    public record Frame(BigInteger nativeRevision, BigInteger dateRaw, BigInteger actorId) {
        public Frame {
            StrictJson.require(nativeRevision != null && nativeRevision.signum() > 0 && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "positive native revision required");
            StrictJson.require(dateRaw != null && dateRaw.signum() >= 0 && dateRaw.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                    "native date outside int32");
            StrictJson.require(actorId != null && actorId.signum() > 0 && actorId.bitLength() <= 32, "positive full uint32 actor required");
        }
    }
    public static final class Body {
        private final byte[] bytes;
        public Body(byte[] bytes) { this.bytes = StrictJson.canonical(StrictJson.parse(bytes)); }
        public byte[] bytes() { return bytes.clone(); }
        @Override public boolean equals(Object other) { return other instanceof Body value && Arrays.equals(bytes, value.bytes); }
        @Override public int hashCode() { return Arrays.hashCode(bytes); }
    }
    public record Observation(Frame frame, Kind kind, Body original) {
        public Observation { Objects.requireNonNull(frame); Objects.requireNonNull(kind); Objects.requireNonNull(original); }
        public boolean needsConfiguration() { return kind == Kind.ABSENT || kind == Kind.FEAST_STAGE_ONE || kind == Kind.FEAST_STAGE_TWO; }
    }
    private static final Set<String> FIELDS = Set.of("schema", "snapshot_revision", "date_raw", "actor_character_id", "planner_status", "planner_present",
            "widget_attached", "widget_visible", "planning_stage", "host_view_activity_key_source", "host_view_activity_key", "configured_cost_state",
            "final_can_start_state", "raw_pointer_fields_persisted");
    public static Observation decode(byte[] bytes, Frame expected) {
        Objects.requireNonNull(expected); ObjectNode payload = StrictJson.object(StrictJson.parse(bytes), FIELDS);
        StrictJson.require(StrictJson.text(payload.get("schema")).equals("activity-planner-diag-private-read-v1")
                && StrictJson.integer(payload.get("snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX).equals(expected.nativeRevision())
                && StrictJson.integer(payload.get("date_raw"), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE)).equals(expected.dateRaw())
                && StrictJson.integer(payload.get("actor_character_id"), BigInteger.ONE, BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE)).equals(expected.actorId()),
                "planner diagnostic frame drift");
        StrictJson.require(StrictJson.text(payload.get("host_view_activity_key_source")).equals("host_view_current_type")
                && StrictJson.text(payload.get("configured_cost_state")).equals("unknown")
                && StrictJson.text(payload.get("final_can_start_state")).equals("unknown")
                && !bool(payload.get("raw_pointer_fields_persisted")), "diagnostic claims an unobserved cost, start or pointer");
        boolean present = bool(payload.get("planner_present")), attached = bool(payload.get("widget_attached")), visible = bool(payload.get("widget_visible"));
        JsonNode key = payload.get("host_view_activity_key");
        StrictJson.require(key.isNull() || key.isTextual() && key.textValue().matches("[a-z0-9_]{1,95}"), "invalid planner activity key");
        String status = StrictJson.text(payload.get("planner_status")); Kind kind;
        if (status.equals("planner_absent")) {
            StrictJson.require(!present && !attached && !visible && payload.get("planning_stage").isNull() && key.isNull(), "absent planner contains present metadata");
            kind = Kind.ABSENT;
        } else {
            StrictJson.require(status.equals("observed") && present && (attached || !visible), "planner observed binding differs");
            int stage = (int) StrictJson.integer(payload.get("planning_stage"), 0, 5); kind = Kind.OTHER;
            if (key.isTextual() && key.textValue().equals("activity_feast")) kind = switch (stage) {
                case 1 -> Kind.FEAST_STAGE_ONE; case 2 -> Kind.FEAST_STAGE_TWO; case 5 -> Kind.FEAST_STAGE_FIVE; default -> Kind.OTHER;
            };
        }
        return new Observation(expected, kind, new Body(bytes));
    }
    public static byte[] encode(Observation value) { return Objects.requireNonNull(value).original().bytes(); }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "exact planner boolean required"); return value.booleanValue();
    }
}
