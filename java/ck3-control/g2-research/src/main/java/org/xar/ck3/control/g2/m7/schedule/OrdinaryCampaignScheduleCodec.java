package org.xar.ck3.control.g2.m7.schedule;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule.Plan;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule.State;

/** One field authority for durable ordinary goal/calendar state and every fresh scheduling reader. */
public final class OrdinaryCampaignScheduleCodec {
    private static final JsonFactory JSON = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    public static final String STATE_SCHEMA = "xar.ordinary-campaign-schedule-state/v1";
    public static final String PLAN_SCHEMA = "xar.ordinary-campaign-schedule-plan/v1";
    private OrdinaryCampaignScheduleCodec() { }

    public static State decodeState(byte[] raw) { return parseState(parse(raw)); }
    public static State parseState(JsonNode input) {
        ObjectNode row = StrictJson.object(input, Set.of("schema", "goal", "deadline_configuration"));
        integerValueDomain(row);
        constant(row, "schema", STATE_SCHEMA);
        JsonNode configuration = row.get("deadline_configuration");
        return new State(GoalCodec.parseGoal(row.get("goal")), configuration.isNull() ? Optional.empty()
                : Optional.of(CampaignDeadlineCodec.decodeConfiguration(raw(configuration), OrdinaryCampaignSchedule::calendar)));
    }
    public static byte[] encodeState(State value) {
        ObjectNode row = StrictJson.object(); row.put("schema", STATE_SCHEMA);
        row.set("goal", parse(GoalCodec.encodeGoal(value.goal())));
        if (value.deadline().isPresent()) {
            row.set("deadline_configuration", parse(CampaignDeadlineCodec.encodeConfiguration(value.deadline().orElseThrow())));
        } else { row.putNull("deadline_configuration"); }
        return raw(row);
    }

    /** The full planner's existing publication is consumed through its existing single typed reader. */
    public static Plan compose(byte[] input) {
        ObjectNode row = StrictJson.object(parse(input), Set.of("state", "ordinary_plan", "requested_clock_target_raw"));
        return OrdinaryCampaignSchedule.consume(parseState(row.get("state")),
                M7OrdinaryPlanConsumer.decode(field(input, "ordinary_plan")), target(row.get("requested_clock_target_raw")));
    }

    public static byte[] encodePlan(Plan value) {
        ObjectNode row = StrictJson.object(); row.put("schema", PLAN_SCHEMA);
        row.set("state", parse(encodeState(value.state())));
        row.set("ordinary_plan", parse(M7OrdinaryPlanConsumer.encode(value.ordinaryPlan())));
        put(row, "requested_clock_target_raw", value.requestedClockTargetRaw());
        if (value.clockDeadline().isPresent()) {
            row.set("clock_deadline", parse(CampaignDeadlineCodec.encodeCap(value.clockDeadline().orElseThrow())));
        } else { row.putNull("clock_deadline"); }
        row.put("clock_status", value.clockStatus().wire());
        put(row, "effective_clock_target_raw", value.effectiveClockTargetRaw());
        row.put("planner_route", "full_ordinary"); row.put("game_actions_submitted", false);
        row.put("cold_authority_granted", false); row.put("replay_authorized", false); row.put("saved_day_credit", 0);
        return raw(row);
    }

    /** Recompute all projections from persisted producers; a claimed cap/status cannot grant authority. */
    public static Plan decodePlan(byte[] input) {
        ObjectNode row = StrictJson.object(parse(input), Set.of("schema", "state", "ordinary_plan",
                "requested_clock_target_raw", "clock_deadline", "clock_status", "effective_clock_target_raw",
                "planner_route", "game_actions_submitted", "cold_authority_granted", "replay_authorized", "saved_day_credit"));
        constant(row, "schema", PLAN_SCHEMA); constant(row, "planner_route", "full_ordinary");
        for (String field : Set.of("game_actions_submitted", "cold_authority_granted", "replay_authorized")) {
            JsonNode value = row.get(field);
            StrictJson.require(value.isBoolean() && !value.booleanValue(), "ordinary scheduling grants no action, cold or replay authority");
        }
        StrictJson.integer(row.get("saved_day_credit"), 0, 0);
        JsonNode cap = row.get("clock_deadline");
        integerValueDomain(cap);
        Optional<CampaignDeadline.Cap> parsedCap = cap.isNull() ? Optional.empty()
                : Optional.of(CampaignDeadlineCodec.decodeCap(raw(cap)));
        Plan result = new Plan(parseState(row.get("state")), M7OrdinaryPlanConsumer.decode(field(input, "ordinary_plan")),
                target(row.get("requested_clock_target_raw")), parsedCap);
        StrictJson.require(result.clockStatus().wire().equals(StrictJson.text(row.get("clock_status")))
                && result.effectiveClockTargetRaw().equals(target(row.get("effective_clock_target_raw"))),
                "persisted ordinary clock projection differs from its producers");
        return result;
    }

    /** State and cap own an integer-only JSON domain; guard token kinds before any tree encoding. */
    private static void integerValueDomain(JsonNode value) {
        StrictJson.require(value != null, "owned schedule JSON value required");
        Deque<JsonNode> pending = new ArrayDeque<>(); pending.add(value);
        while (!pending.isEmpty()) {
            JsonNode current = pending.removeLast();
            StrictJson.require(!current.isFloatingPointNumber(), "owned schedule state/cap requires exact integer tokens");
            if (current.isContainerNode()) { for (JsonNode child : current) { pending.addLast(child); } }
        }
    }

    /** Original child slice, after the enclosing boundary has validated UTF-8, fields and duplicate keys. */
    static byte[] field(byte[] input, String name) {
        try (JsonParser parser = JSON.createParser(input)) {
            StrictJson.require(parser.nextToken() == JsonToken.START_OBJECT, "schedule enclosing object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                StrictJson.require(parser.currentToken() == JsonToken.FIELD_NAME, "schedule field required");
                String field = parser.currentName(); parser.nextToken();
                int start = Math.toIntExact(parser.currentTokenLocation().getByteOffset());
                parser.skipChildren(); int end = Math.toIntExact(parser.currentLocation().getByteOffset());
                if (name.equals(field)) { return Arrays.copyOfRange(input, start, end); }
            }
            throw new IllegalArgumentException("required original schedule field absent: " + name);
        } catch (IOException error) { throw new IllegalArgumentException("invalid original schedule input", error); }
    }

    private static Optional<BigInteger> target(JsonNode value) {
        StrictJson.require(value != null, "explicit nullable clock target required");
        return value.isNull() ? Optional.empty() : Optional.of(StrictJson.integer(value,
                BigInteger.ONE, OrdinaryCampaignSchedule.MAX_CLOCK_TARGET));
    }
    private static void put(ObjectNode row, String field, Optional<BigInteger> value) {
        if (value.isPresent()) { row.put(field, value.orElseThrow()); } else { row.putNull(field); }
    }
    private static JsonNode parse(byte[] raw) { return StrictJson.parse(raw, M7OrdinaryPlanConsumer.MAX_BYTES); }
    private static byte[] raw(JsonNode value) {
        StrictJson.require(value != null, "missing schedule field cannot become JSON null");
        byte[] result = value.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(result.length <= M7OrdinaryPlanConsumer.MAX_BYTES, "ordinary schedule exceeds explicit byte budget");
        return result;
    }
    private static void constant(ObjectNode row, String field, String expected) {
        StrictJson.require(expected.equals(StrictJson.text(row.get(field))), "ordinary schedule constant differs: " + field);
    }
}
