package org.xar.ck3.control.admission.deadlinecredit;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict owned state/cap wire codecs; extensible legacy frames are projected at one boundary. */
public final class CampaignDeadlineCodec {
    private static final BigInteger MAX_INTEGER = BigInteger.ONE.shiftLeft(4096).subtract(BigInteger.ONE);
    private static final Set<String> SUMMARY_FIELDS = Set.of("schema", "campaign_id", "calendar_profile", "start_date",
            "start_date_raw", "months", "endpoint_date_raw");
    private static final Set<String> CONFIG_FIELDS = Set.of("schema", "campaign_id", "calendar_profile", "start_date",
            "start_date_raw", "months", "endpoint_date_raw", "boundary_raws");
    private static final Set<String> CAP_FIELDS = Set.of("schema", "campaign_id", "calendar_profile", "starting_date_raw",
            "requested_target_date_raw", "boundary_date_raw", "endpoint_date_raw", "target_date_raw", "status",
            "policy_choices_changed");

    private CampaignDeadlineCodec() { }

    /** Consumer port: configuration absence retains the old no-cap behavior before inspecting any frame. */
    public static Optional<CampaignDeadline.Cap> deadlineFromJson(Optional<byte[]> configuration,
                                                                 CampaignDeadline.CalendarPort calendar,
                                                                 byte[] startingFrame, byte[] proposedTarget) {
        if (configuration.isEmpty()) { return Optional.empty(); }
        CampaignDeadline.Configuration config = decodeConfiguration(configuration.orElseThrow(), calendar);
        JsonNode starting = StrictJson.parse(startingFrame);
        StrictJson.require(starting.isObject(), "actual starting frame object required");
        return CampaignDeadline.deadline(Optional.of(config), integer(starting.get("date_raw")),
                integer(StrictJson.parse(proposedTarget)));
    }

    /** Consumer port: the original driver retains the returned immutable state; this method never mutates it. */
    public static CampaignDeadline.Configuration configureFromJson(byte[] founding,
                                                                   CampaignDeadline.CalendarPort calendar,
                                                                   Optional<byte[]> previous) {
        return CampaignDeadline.configure(decodeFounding(founding), calendar,
                previous.map(raw -> decodeConfiguration(raw, calendar)));
    }

    public static CampaignDeadline.Founding decodeFounding(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw),
                Set.of("campaign_id", "start_date", "start_date_raw", "months"));
        return new CampaignDeadline.Founding(StrictJson.text(value.get("campaign_id")),
                StrictJson.text(value.get("start_date")), integer(value.get("start_date_raw")),
                (int) StrictJson.integer(value.get("months"), 1, 360));
    }

    /** Serialized schedules are checked against the one qualified calendar implementation before use. */
    public static CampaignDeadline.Configuration decodeConfiguration(byte[] raw, CampaignDeadline.CalendarPort calendar) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw), CONFIG_FIELDS);
        constant(value, "schema", CampaignDeadline.SCHEMA);
        constant(value, "calendar_profile", CampaignDeadline.CALENDAR_PROFILE);
        CampaignDeadline.Founding founding = new CampaignDeadline.Founding(StrictJson.text(value.get("campaign_id")),
                StrictJson.text(value.get("start_date")), integer(value.get("start_date_raw")),
                (int) StrictJson.integer(value.get("months"), 1, 360));
        JsonNode boundaries = value.get("boundary_raws");
        StrictJson.require(boundaries.isArray() && boundaries.size() == founding.months() + 1,
                "complete JSON array of calendar boundary integers required");
        List<BigInteger> raws = new ArrayList<>();
        for (JsonNode boundary : boundaries) { raws.add(integer(boundary)); }
        CampaignDeadline.Configuration parsed = new CampaignDeadline.Configuration(founding, CampaignDeadline.CALENDAR_PROFILE,
                integer(value.get("endpoint_date_raw")), raws);
        CampaignDeadline.Configuration verified = CampaignDeadline.configure(founding, calendar, Optional.empty());
        StrictJson.require(parsed.equals(verified), "stored campaign boundary schedule differs from qualified calendar");
        return verified;
    }

    public static CampaignDeadline.Cap decodeCap(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw), CAP_FIELDS);
        constant(value, "schema", CampaignDeadline.SCHEMA);
        constant(value, "calendar_profile", CampaignDeadline.CALENDAR_PROFILE);
        StrictJson.require(value.get("policy_choices_changed").isBoolean()
                && !value.get("policy_choices_changed").booleanValue(), "deadline cannot change policy choices");
        String statusWire = StrictJson.text(value.get("status"));
        CampaignDeadline.Status status = switch (statusWire) {
            case "advance" -> CampaignDeadline.Status.ADVANCE;
            case "endpoint_reached" -> CampaignDeadline.Status.ENDPOINT_REACHED;
            case "endpoint_overshot" -> CampaignDeadline.Status.ENDPOINT_OVERSHOT;
            default -> throw new IllegalArgumentException("unknown deadline status: " + statusWire);
        };
        return new CampaignDeadline.Cap(StrictJson.text(value.get("campaign_id")), CampaignDeadline.CALENDAR_PROFILE,
                integer(value.get("starting_date_raw")), integer(value.get("requested_target_date_raw")),
                integer(value.get("boundary_date_raw")), integer(value.get("endpoint_date_raw")),
                integer(value.get("target_date_raw")), status);
    }

    /** Missing/null optional presentation fields both produce explicit null, as the active endpoint producer does. */
    public static CampaignDeadline.EndpointFrame projectEndpointFrame(byte[] raw) {
        JsonNode value = StrictJson.parse(raw);
        StrictJson.require(value.isObject(), "actual starting frame object required");
        JsonNode paused = value.get("paused");
        StrictJson.require(paused == null || paused.isNull() || paused.isBoolean(), "paused must be boolean or absent/null");
        JsonNode snapshot = value.get("snapshot_id");
        JsonNode revision = value.get("revision");
        return new CampaignDeadline.EndpointFrame(integer(value.get("date_raw")),
                paused != null && paused.isBoolean() && paused.booleanValue(),
                snapshot == null || snapshot.isNull() ? Optional.empty() : Optional.of(StrictJson.text(snapshot)),
                revision == null || revision.isNull() ? Optional.empty() : Optional.of(integer(revision)));
    }

    public static byte[] encodeConfiguration(CampaignDeadline.Configuration config) {
        ObjectNode result = summary(config);
        ArrayNode boundaries = result.putArray("boundary_raws");
        config.boundaryRaws().forEach(boundaries::add);
        return StrictJson.canonical(result);
    }

    public static byte[] encodeSummary(CampaignDeadline.Configuration config) {
        return StrictJson.canonical(StrictJson.object(summary(config), SUMMARY_FIELDS));
    }

    public static byte[] encodeCap(CampaignDeadline.Cap cap) { return StrictJson.canonical(capNode(cap)); }

    public static byte[] encodeEndpointResult(CampaignDeadline.EndpointResult result) {
        ObjectNode value = StrictJson.object();
        CampaignDeadline.EndpointFrame frame = result.frame();
        value.put("step", result.resultStep());
        value.put("backend_id", "native-headless");
        value.put("source", "native-composite");
        value.putObject("starting_date").put("date_raw", frame.dateRaw());
        value.putObject("ending_date").put("date_raw", frame.dateRaw());
        value.put("starting_date_raw", frame.dateRaw());
        value.put("ending_date_raw", frame.dateRaw());
        value.put("elapsed_days", result.elapsedDays());
        value.put("requested_horizon_days", result.requestedHorizonDays());
        value.put("progress_status", "campaign_endpoint_reached");
        value.put("paused", frame.paused());
        value.putArray("actions");
        if (frame.snapshotId().isPresent()) { value.put("snapshot_id", frame.snapshotId().orElseThrow()); }
        else { value.putNull("snapshot_id"); }
        if (frame.revision().isPresent()) { value.put("revision", frame.revision().orElseThrow()); }
        else { value.putNull("revision"); }
        value.set("campaign_deadline_v1", capNode(result.cap()));
        value.put("calendar_progress_verified", result.calendarProgressVerified());
        value.put("business_success_inferred", result.businessSuccessInferred());
        return StrictJson.canonical(value);
    }

    private static ObjectNode summary(CampaignDeadline.Configuration config) {
        ObjectNode result = StrictJson.object();
        result.put("schema", CampaignDeadline.SCHEMA);
        result.put("campaign_id", config.founding().campaignId());
        result.put("calendar_profile", config.calendarProfile());
        result.put("start_date", config.founding().startDate());
        result.put("start_date_raw", config.founding().startDateRaw());
        result.put("months", config.founding().months());
        result.put("endpoint_date_raw", config.endpointDateRaw());
        return result;
    }

    private static ObjectNode capNode(CampaignDeadline.Cap cap) {
        ObjectNode result = StrictJson.object();
        result.put("schema", CampaignDeadline.SCHEMA);
        result.put("campaign_id", cap.campaignId());
        result.put("calendar_profile", cap.calendarProfile());
        result.put("starting_date_raw", cap.startingDateRaw());
        result.put("requested_target_date_raw", cap.requestedTargetDateRaw());
        result.put("boundary_date_raw", cap.boundaryDateRaw());
        result.put("endpoint_date_raw", cap.endpointDateRaw());
        result.put("target_date_raw", cap.targetDateRaw());
        result.put("status", cap.status().wire());
        result.put("policy_choices_changed", false);
        return result;
    }

    private static BigInteger integer(JsonNode value) {
        return StrictJson.integer(value, BigInteger.ZERO, MAX_INTEGER);
    }

    private static void constant(ObjectNode value, String field, String expected) {
        StrictJson.require(expected.equals(StrictJson.text(value.get(field))), "constant field differs: " + field);
    }
}
