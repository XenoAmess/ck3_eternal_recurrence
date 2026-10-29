package org.xar.ck3.control.admission.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;

/** Existing deadline codecs and the one existing fixed365 calendar, in the resident host. */
public final class AdmissionDeadlineProjectionCatalog implements ProjectionPortCatalog {
    private static final CampaignDeadline.CalendarPort CALENDAR = (date, months) ->
            new CampaignDeadline.CalendarSchedule(CampaignCalendar.PROFILE, date,
                    BigInteger.valueOf(CampaignCalendar.dateToRaw(date)), CampaignCalendar.monthBoundaries(date, months)
                            .stream().map(boundary -> BigInteger.valueOf(boundary.raw())).toList());

    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new ConfigurePort()), RegisteredProjection.of(new CapPort()),
                RegisteredProjection.of(new EndpointPort()));
    }

    /** The existing public codec performs both strict decoding and the actual pure producer. */
    private static final class ConfigurePort implements ProjectionPort<CampaignDeadline.Configuration, CampaignDeadline.Configuration> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.CAMPAIGN_DEADLINE_CONFIGURE; }
        @Override public CampaignDeadline.Configuration decode(byte[] raw) {
            ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("founding", "previous_configuration"));
            JsonNode previous = input.get("previous_configuration");
            return CampaignDeadlineCodec.configureFromJson(StrictJson.canonical(input.get("founding")), CALENDAR,
                    previous.isNull() ? Optional.empty() : Optional.of(StrictJson.canonical(previous)));
        }
        @Override public CampaignDeadline.Configuration project(CampaignDeadline.Configuration input) { return input; }
        @Override public byte[] encode(CampaignDeadline.Configuration result) {
            ObjectNode output = StrictJson.object();
            output.set("configuration", StrictJson.parse(CampaignDeadlineCodec.encodeConfiguration(result)));
            output.set("summary", StrictJson.parse(CampaignDeadlineCodec.encodeSummary(result)));
            return StrictJson.canonical(output);
        }
        @Override public int outputMaximumBytes() { return StrictJson.OUTPUT_MAX_BYTES; }
    }

    private static final class CapPort implements ProjectionPort<Optional<CampaignDeadline.Cap>, Optional<CampaignDeadline.Cap>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.CAMPAIGN_DEADLINE_CAP; }
        @Override public Optional<CampaignDeadline.Cap> decode(byte[] raw) {
            ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("configuration", "starting", "proposed_target_raw"));
            JsonNode config = input.get("configuration");
            if (config.isNull()) { return Optional.empty(); }
            // Native frames may have unrelated float fields. Project only the original date operand.
            ObjectNode starting = projectFrame(input.get("starting"), List.of("date_raw"));
            return CampaignDeadlineCodec.deadlineFromJson(Optional.of(StrictJson.canonical(config)), CALENDAR,
                    StrictJson.canonical(starting), StrictJson.canonical(input.get("proposed_target_raw")));
        }
        @Override public Optional<CampaignDeadline.Cap> project(Optional<CampaignDeadline.Cap> input) { return input; }
        @Override public byte[] encode(Optional<CampaignDeadline.Cap> result) {
            ObjectNode output = StrictJson.object();
            if (result.isPresent()) { output.set("cap", StrictJson.parse(CampaignDeadlineCodec.encodeCap(result.orElseThrow()))); }
            else { output.putNull("cap"); }
            return StrictJson.canonical(output);
        }
        @Override public int outputMaximumBytes() { return StrictJson.OUTPUT_MAX_BYTES; }
    }

    private static final class EndpointPort implements ProjectionPort<CampaignDeadline.EndpointResult, CampaignDeadline.EndpointResult> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.CAMPAIGN_DEADLINE_ENDPOINT; }
        @Override public CampaignDeadline.EndpointResult decode(byte[] raw) {
            ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("starting", "result_step", "cap"));
            ObjectNode starting = projectFrame(input.get("starting"), List.of("date_raw", "paused", "snapshot_id", "revision"));
            return CampaignDeadline.endpointResult(CampaignDeadlineCodec.projectEndpointFrame(StrictJson.canonical(starting)),
                    StrictJson.text(input.get("result_step")), CampaignDeadlineCodec.decodeCap(StrictJson.canonical(input.get("cap"))));
        }
        @Override public CampaignDeadline.EndpointResult project(CampaignDeadline.EndpointResult input) { return input; }
        @Override public byte[] encode(CampaignDeadline.EndpointResult result) { return CampaignDeadlineCodec.encodeEndpointResult(result); }
        @Override public int outputMaximumBytes() { return StrictJson.OUTPUT_MAX_BYTES; }
    }

    private static ObjectNode projectFrame(JsonNode frame, List<String> fields) {
        StrictJson.require(frame != null && frame.isObject(), "actual starting frame object required");
        ObjectNode projected = StrictJson.object();
        for (String field : fields) { if (frame.has(field)) { projected.set(field, frame.get(field).deepCopy()); } }
        return projected;
    }
}
