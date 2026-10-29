package org.xar.ck3.control.planning.campaigncadence;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit JSON projection boundary. No HTTP host or hidden Python fallback. */
public final class CampaignCadenceCodec {
    private static final ObjectMapper REQUEST_WRITER = new ObjectMapper();
    private CampaignCadenceCodec() { }

    public sealed interface Request permits DateToRaw, RawToDate, Boundaries, Advance, Candidate {
        JsonNode evaluate();
    }
    public record DateToRaw(String date) implements Request {
        public DateToRaw { CampaignCalendar.parse(date); }
        @Override public JsonNode evaluate() { return JsonNodeFactory.instance.numberNode(CampaignCalendar.dateToRaw(date)); }
    }
    public record RawToDate(int raw) implements Request {
        public RawToDate { CampaignCalendar.rawToDate(raw); }
        @Override public JsonNode evaluate() { return JsonNodeFactory.instance.textNode(CampaignCalendar.rawToDate(raw)); }
    }
    public record Boundaries(String startDate, int months) implements Request {
        public Boundaries {
            CampaignCalendar.parse(startDate);
            require(months >= 1 && months <= 360, "cadence requires 1..360 months");
        }
        @Override public JsonNode evaluate() {
            ArrayNode result = JsonNodeFactory.instance.arrayNode();
            for (CampaignCalendar.Boundary row : CampaignCalendar.monthBoundaries(startDate, months)) {
                ArrayNode pair = result.addArray(); pair.add(row.date()); pair.add(row.raw());
            }
            return result;
        }
    }
    public record Advance(int currentRaw, int proposedTargetRaw, String startDate,
            int nextSampleIndex, int months) implements Request {
        public Advance {
            CampaignCalendar.rawToDate(currentRaw); CampaignCalendar.rawToDate(proposedTargetRaw);
            CampaignCalendar.parse(startDate);
            require(months >= 1 && months <= 360 && nextSampleIndex >= 0 && nextSampleIndex <= months + 1,
                    "invalid cadence cursor/configuration");
        }
        @Override public JsonNode evaluate() {
            return CampaignAdvanceCap.plan(currentRaw, proposedTargetRaw, startDate, nextSampleIndex, months).toJson();
        }
    }
    public record Candidate(ObjectNode snapshot, String startDate, String machineId, String observedAtUtc,
            ObjectNode campaignAnchor, int months) implements Request {
        public Candidate {
            require(snapshot != null && campaignAnchor != null, "sample inputs must be objects");
            snapshot = snapshot.deepCopy(); campaignAnchor = campaignAnchor.deepCopy();
            CampaignCalendar.parse(startDate);
            require(months >= 1 && months <= 360, "cadence requires 1..360 months");
            // Nonboundary frames do not consume actor/provenance fields, matching the producer.
        }
        @Override public ObjectNode snapshot() { return snapshot.deepCopy(); }
        @Override public ObjectNode campaignAnchor() { return campaignAnchor.deepCopy(); }
        @Override public JsonNode evaluate() {
            return MonthlyObservation.fromExistingFrame(snapshot, startDate, machineId, observedAtUtc,
                    campaignAnchor, months).map(MonthlyObservation::toJson).map(JsonNode.class::cast)
                    .orElseGet(JsonNodeFactory.instance::nullNode);
        }
    }

    public static Request decode(byte[] input) { return decode(StrictJson.parse(input)); }

    public static Request decode(JsonNode input) {
        require(input instanceof ObjectNode, "cadence request must be an object");
        String operation = StrictJson.text(input.get("operation"));
        return switch (operation) {
            case "date_to_raw" -> {
                ObjectNode object = StrictJson.object(input, Set.of("operation", "date"));
                yield new DateToRaw(StrictJson.text(object.get("date")));
            }
            case "raw_to_date" -> {
                ObjectNode object = StrictJson.object(input, Set.of("operation", "raw"));
                yield new RawToDate(integer(object.get("raw")));
            }
            case "month_boundaries" -> {
                ObjectNode object = StrictJson.object(input, Set.of("operation", "start_date", "months"));
                yield new Boundaries(StrictJson.text(object.get("start_date")), integer(object.get("months")));
            }
            case "plan_advance_cap" -> {
                ObjectNode object = StrictJson.object(input, Set.of("operation", "current_raw", "proposed_target_raw",
                        "start_date", "next_sample_index", "months"));
                yield new Advance(integer(object.get("current_raw")), integer(object.get("proposed_target_raw")),
                        StrictJson.text(object.get("start_date")), integer(object.get("next_sample_index")), integer(object.get("months")));
            }
            case "ordinary_sample_candidate" -> {
                ObjectNode object = StrictJson.object(input, Set.of("operation", "snapshot", "start_date", "machine_id",
                        "observed_at_utc", "campaign_anchor", "months"));
                require(object.get("snapshot") instanceof ObjectNode && object.get("campaign_anchor") instanceof ObjectNode,
                        "sample inputs must be objects");
                yield new Candidate((ObjectNode) object.get("snapshot"), StrictJson.text(object.get("start_date")),
                        StrictJson.text(object.get("machine_id")), StrictJson.text(object.get("observed_at_utc")),
                        (ObjectNode) object.get("campaign_anchor"), integer(object.get("months")));
            }
            default -> throw new IllegalArgumentException("unknown cadence operation");
        };
    }

    public static byte[] evaluate(byte[] input) { return StrictJson.canonical(decode(input).evaluate()); }

    public static byte[] encode(Request request) {
        require(request != null, "cadence request required");
        ObjectNode object = StrictJson.object();
        switch (request) {
            case DateToRaw date -> { object.put("operation", "date_to_raw"); object.put("date", date.date()); }
            case RawToDate date -> { object.put("operation", "raw_to_date"); object.put("raw", date.raw()); }
            case Boundaries boundaries -> {
                object.put("operation", "month_boundaries"); object.put("start_date", boundaries.startDate());
                object.put("months", boundaries.months());
            }
            case Advance advance -> {
                object.put("operation", "plan_advance_cap"); object.put("current_raw", advance.currentRaw());
                object.put("proposed_target_raw", advance.proposedTargetRaw()); object.put("start_date", advance.startDate());
                object.put("next_sample_index", advance.nextSampleIndex()); object.put("months", advance.months());
            }
            case Candidate candidate -> {
                object.put("operation", "ordinary_sample_candidate"); object.set("snapshot", candidate.snapshot());
                object.put("start_date", candidate.startDate()); object.put("machine_id", candidate.machineId());
                object.put("observed_at_utc", candidate.observedAtUtc()); object.set("campaign_anchor", candidate.campaignAnchor());
                object.put("months", candidate.months());
            }
        }
        // Full upstream snapshots may carry unused finite decimal fields. The
        // output projection remains in the integer/string canonical domain;
        // request round trips must not reject those unrelated upstream fields.
        validateJsonValues(object);
        try {
            byte[] raw = REQUEST_WRITER.writeValueAsBytes(object);
            StrictJson.parse(raw); // Revalidate UTF-8, duplicate-free JSON and byte budget.
            return raw;
        } catch (IOException error) {
            throw new ContractViolationException("cannot encode cadence request", error);
        }
    }

    private static void validateJsonValues(JsonNode node) {
        require(node != null, "missing JSON value cannot be serialized as null");
        if (node.isObject()) {
            node.properties().forEach(entry -> {
                if (!entry.getKey().isEmpty()) { StrictJson.text(entry.getKey()); }
                validateJsonValues(entry.getValue());
            });
        } else if (node.isArray()) {
            node.forEach(CampaignCadenceCodec::validateJsonValues);
        } else if (node.isTextual()) {
            if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); }
        } else if (node.isFloatingPointNumber()) {
            require(node.isBigDecimal() || Double.isFinite(node.doubleValue()), "nonfinite JSON decimal");
        } else {
            require(node.isIntegralNumber() || node.isBoolean() || node.isNull(), "unsupported JSON value");
        }
    }

    private static int integer(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
}
