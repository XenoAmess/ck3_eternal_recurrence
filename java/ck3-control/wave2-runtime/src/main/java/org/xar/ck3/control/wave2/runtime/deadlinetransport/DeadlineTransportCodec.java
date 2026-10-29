package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict owned envelope fields, explicit projection of extensible legacy semantic frames/results. */
public final class DeadlineTransportCodec {
    private static final Set<String> CLOCK_FIELDS = Set.of("schema", "scope", "starting_date_raw", "target_date_raw",
            "armed", "stopped", "early_boundary_cancel", "speed_configuration", "exact_one_day_qualification_claimed");
    private DeadlineTransportCodec() { }

    public static DeadlineTransport.PreparedRequest prepare(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("invocation_id", "cap", "starting_frame", "speed"));
        return new DeadlineTransport.PreparedRequest(StrictJson.text(input.get("invocation_id")),
                CampaignDeadlineCodec.decodeCap(StrictJson.canonical(input.get("cap"))), frame(input.get("starting_frame")),
                (int) StrictJson.integer(input.get("speed"), 1, 5));
    }

    public static DeadlineTransport.Completion completion(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("current_frame", "clock", "actions"));
        JsonNode actions = input.get("actions");
        require(actions.isArray() && actions.size() >= 2 && actions.size() <= 8, "bounded actual action slice required");
        List<DeadlineTransport.Action> parsed = new ArrayList<>();
        for (JsonNode action : actions) {
            // Existing action rows may carry presentation or timings; neither grants any proof.
            require(action.isObject(), "actual action object required");
            parsed.add(new DeadlineTransport.Action(StrictJson.text(action.get("step")), receipt(action.get("result"))));
        }
        return new DeadlineTransport.Completion(frame(input.get("current_frame")), clock(input.get("clock")), parsed);
    }

    public static byte[] observe(byte[] preparedRequest, byte[] completion) {
        DeadlineTransport.Observation observation = DeadlineTransport.observe(prepare(preparedRequest), completion(completion));
        return encodeClock(observation.completion().clock());
    }

    public static byte[] encodeClock(DeadlineTransport.ClockEnvelope clock) {
        return LegacyJsonValues.encode(DeadlineTransport.clockJson(clock));
    }

    public static DeadlineTransport.Frame frame(JsonNode input) {
        require(input != null && input.isObject(), "actual semantic frame object required");
        return new DeadlineTransport.Frame(nonnegativeInt(input.get("date_raw")), SentinelObservation.bool(input.get("paused")),
                (int) StrictJson.integer(input.get("speed"), 1, 5), optionalText(input.get("snapshot_id")),
                optionalInteger(input.get("native_revision")));
    }

    private static DeadlineTransport.ClockEnvelope clock(JsonNode raw) {
        ObjectNode clock = StrictJson.object(raw, CLOCK_FIELDS);
        require(StrictJson.text(clock.get("schema")).equals(DeadlineTransport.CLOCK_SCHEMA)
                && StrictJson.text(clock.get("scope")).equals("campaign_date_deadline"), "native clock schema/scope differs");
        require(!SentinelObservation.bool(clock.get("exact_one_day_qualification_claimed")), "campaign clock cannot claim exact-one-day qualification");
        JsonNode cancel = clock.get("early_boundary_cancel");
        return new DeadlineTransport.ClockEnvelope(nonnegativeInt(clock.get("starting_date_raw")),
                nonnegativeInt(clock.get("target_date_raw")), SentinelObservation.decode(clock.get("armed")),
                SentinelObservation.decode(clock.get("stopped")), cancel.isNull() ? Optional.empty() : Optional.of(receipt(cancel)),
                speed(clock.get("speed_configuration")));
    }

    private static DeadlineTransport.SpeedConfiguration speed(JsonNode raw) {
        require(raw != null && raw.isObject(), "native speed configuration object required");
        String status = StrictJson.text(raw.get("status"));
        if (status.equals("submitted")) {
            ObjectNode row = StrictJson.object(raw, Set.of("status", "step"));
            return new DeadlineTransport.SubmittedSpeed(StrictJson.text(row.get("step")));
        }
        require(status.equals("already_observed"), "unknown native speed configuration status");
        ObjectNode row = StrictJson.object(raw, Set.of("status", "submitted", "observed_speed", "source_snapshot_id",
                "source_native_revision", "source_date_raw"));
        require(!SentinelObservation.bool(row.get("submitted")), "already-observed speed cannot claim submission");
        return new DeadlineTransport.AlreadyObservedSpeed((int) StrictJson.integer(row.get("observed_speed"), 1, 5),
                optionalText(row.get("source_snapshot_id")), optionalInteger(row.get("source_native_revision")),
                nonnegativeInt(row.get("source_date_raw")));
    }

    private static DeadlineTransport.NativeReceipt receipt(JsonNode raw) {
        require(raw != null && raw.isObject(), "actual primitive receipt object required");
        JsonNode sentinel = raw.get("tactical_daily_sentinel");
        return new DeadlineTransport.NativeReceipt(StrictJson.text(raw.get("step")), SentinelObservation.bool(raw.get("accepted")),
                StrictJson.text(raw.get("status")), sentinel == null || sentinel.isNull() ? Optional.empty()
                    : Optional.of(SentinelObservation.decode(sentinel)), DeadlineTransport.JsonDocument.of(raw));
    }

    private static Optional<String> optionalText(JsonNode value) {
        return value == null || value.isNull() ? Optional.empty() : Optional.of(StrictJson.text(value));
    }
    private static Optional<BigInteger> optionalInteger(JsonNode value) {
        return value == null || value.isNull() ? Optional.empty()
                : Optional.of(StrictJson.integer(value, BigInteger.ZERO, StrictJson.UINT64_MAX));
    }
    private static int nonnegativeInt(JsonNode value) { return (int) StrictJson.integer(value, 0, Integer.MAX_VALUE); }
}
