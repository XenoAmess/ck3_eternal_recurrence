package org.xar.ck3.control.admission.deadlinecredit;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure active campaign_deadline_v1 operations. Does not resume, query, persist or award credit. */
public final class CampaignDeadline {
    public static final String SCHEMA = "xar.ck3.campaign-clock-deadline/v1";
    public static final String CALENDAR_PROFILE = "ck3-1.20.0.4-cdate-fixed365-raw24/v1";
    private static final BigInteger DAY = BigInteger.valueOf(24);

    private CampaignDeadline() { }

    /** The calendar implementation lives in planning-runtime, outside this dependency direction. */
    @FunctionalInterface
    public interface CalendarPort {
        CalendarSchedule schedule(String foundingDate, int months);
    }

    /** Calendar-provided identities, including slot zero and the final month. */
    public record CalendarSchedule(String calendarProfile, String foundingDate,
                                   BigInteger foundingRaw, List<BigInteger> boundaryRaws) {
        public CalendarSchedule {
            StrictJson.require(CALENDAR_PROFILE.equals(calendarProfile), "qualified fixed365 calendar profile required");
            StrictJson.text(foundingDate);
            Objects.requireNonNull(foundingRaw, "foundingRaw");
            boundaryRaws = List.copyOf(boundaryRaws);
            StrictJson.require(!boundaryRaws.isEmpty() && foundingRaw.equals(boundaryRaws.getFirst()),
                    "calendar founding slot differs");
            BigInteger previous = null;
            for (BigInteger boundary : boundaryRaws) {
                StrictJson.require(boundary.signum() > 0 && boundary.subtract(foundingRaw).mod(DAY).signum() == 0
                        && (previous == null || boundary.compareTo(previous) > 0),
                        "calendar boundaries must be strictly increasing whole days");
                previous = boundary;
            }
        }
    }

    public record Founding(String campaignId, String startDate, BigInteger startDateRaw, int months) {
        public Founding {
            StrictJson.text(campaignId);
            StrictJson.text(startDate);
            Objects.requireNonNull(startDateRaw, "startDateRaw");
            StrictJson.require(months >= 1 && months <= 360, "campaign requires 1..360 months");
        }
    }

    /** Immutable driver-held state. Reconfiguration compares every founding field and boundary. */
    public record Configuration(Founding founding, String calendarProfile, BigInteger endpointDateRaw,
                                List<BigInteger> boundaryRaws) {
        public Configuration {
            Objects.requireNonNull(founding, "founding");
            StrictJson.require(CALENDAR_PROFILE.equals(calendarProfile), "calendar profile differs");
            Objects.requireNonNull(endpointDateRaw, "endpointDateRaw");
            CalendarSchedule schedule = new CalendarSchedule(calendarProfile, founding.startDate(),
                    founding.startDateRaw(), boundaryRaws);
            boundaryRaws = schedule.boundaryRaws();
            StrictJson.require(boundaryRaws.size() == founding.months() + 1
                    && endpointDateRaw.equals(boundaryRaws.getLast()), "complete fixed founding boundary schedule required");
        }
    }

    public enum Status {
        ADVANCE("advance"), ENDPOINT_REACHED("endpoint_reached"), ENDPOINT_OVERSHOT("endpoint_overshot");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Cap(String campaignId, String calendarProfile, BigInteger startingDateRaw,
                      BigInteger requestedTargetDateRaw, BigInteger boundaryDateRaw,
                      BigInteger endpointDateRaw, BigInteger targetDateRaw, Status status) {
        public Cap {
            StrictJson.text(campaignId);
            StrictJson.require(CALENDAR_PROFILE.equals(calendarProfile), "calendar profile differs");
            Objects.requireNonNull(startingDateRaw, "startingDateRaw");
            Objects.requireNonNull(requestedTargetDateRaw, "requestedTargetDateRaw");
            Objects.requireNonNull(boundaryDateRaw, "boundaryDateRaw");
            Objects.requireNonNull(endpointDateRaw, "endpointDateRaw");
            Objects.requireNonNull(targetDateRaw, "targetDateRaw");
            Objects.requireNonNull(status, "status");
            StrictJson.require(startingDateRaw.signum() > 0 && requestedTargetDateRaw.compareTo(startingDateRaw) > 0
                    && requestedTargetDateRaw.subtract(startingDateRaw).mod(DAY).signum() == 0
                    && boundaryDateRaw.signum() > 0 && boundaryDateRaw.compareTo(endpointDateRaw) <= 0
                    && boundaryDateRaw.subtract(startingDateRaw).mod(DAY).signum() == 0
                    && endpointDateRaw.subtract(startingDateRaw).mod(DAY).signum() == 0
                    && targetDateRaw.equals(requestedTargetDateRaw.min(boundaryDateRaw)), "deadline date identities differ");
            Status expected = startingDateRaw.compareTo(endpointDateRaw) == 0 ? Status.ENDPOINT_REACHED
                    : startingDateRaw.compareTo(endpointDateRaw) > 0 ? Status.ENDPOINT_OVERSHOT : Status.ADVANCE;
            StrictJson.require(status == expected && (status == Status.ADVANCE
                    ? boundaryDateRaw.compareTo(startingDateRaw) > 0 : boundaryDateRaw.equals(endpointDateRaw)),
                    "deadline endpoint status differs");
        }
    }

    /** The endpoint producer intentionally retains absent snapshot/revision as explicit JSON null. */
    public record EndpointFrame(BigInteger dateRaw, boolean paused, Optional<String> snapshotId,
                                Optional<BigInteger> revision) {
        public EndpointFrame {
            Objects.requireNonNull(dateRaw, "dateRaw");
            StrictJson.require(dateRaw.signum() > 0, "positive native date required");
            Objects.requireNonNull(snapshotId, "snapshotId");
            Objects.requireNonNull(revision, "revision");
            snapshotId.ifPresent(StrictJson::text);
            revision.ifPresent(value -> StrictJson.require(value.signum() > 0, "positive public revision required"));
        }
    }

    public record EndpointResult(String resultStep, EndpointFrame frame, Cap cap) {
        public EndpointResult {
            StrictJson.text(resultStep);
            Objects.requireNonNull(frame, "frame");
            Objects.requireNonNull(cap, "cap");
            StrictJson.require(cap.status() != Status.ADVANCE && frame.dateRaw().equals(cap.startingDateRaw()),
                    "zero-day endpoint result requires the same observed endpoint frame");
        }
        public int elapsedDays() { return 0; }
        public int requestedHorizonDays() { return 0; }
        public boolean calendarProgressVerified() { return false; }
        public boolean businessSuccessInferred() { return false; }
    }

    public static Configuration configure(Founding founding, CalendarPort calendar,
                                          Optional<Configuration> previous) {
        Objects.requireNonNull(founding, "founding");
        Objects.requireNonNull(calendar, "calendar");
        Objects.requireNonNull(previous, "previous");
        CalendarSchedule schedule = calendar.schedule(founding.startDate(), founding.months());
        StrictJson.require(schedule.foundingDate().equals(founding.startDate())
                && schedule.foundingRaw().equals(founding.startDateRaw()),
                "explicit actual founding date/raw identity differs");
        Configuration next = new Configuration(founding, schedule.calendarProfile(),
                schedule.boundaryRaws().getLast(), schedule.boundaryRaws());
        StrictJson.require(previous.isEmpty() || previous.orElseThrow().equals(next),
                "a live driver cannot replace its founding campaign deadline");
        return next;
    }

    public static Optional<Cap> deadline(Optional<Configuration> configuration,
                                         BigInteger current, BigInteger proposedTargetRaw) {
        Objects.requireNonNull(configuration, "configuration");
        if (configuration.isEmpty()) { return Optional.empty(); }
        Configuration config = configuration.orElseThrow();
        Objects.requireNonNull(current, "current");
        Objects.requireNonNull(proposedTargetRaw, "proposedTargetRaw");
        StrictJson.require(current.compareTo(config.founding().startDateRaw()) >= 0
                && current.subtract(config.founding().startDateRaw()).mod(DAY).signum() == 0
                && proposedTargetRaw.compareTo(current) > 0
                && proposedTargetRaw.subtract(current).mod(DAY).signum() == 0,
                "actual whole-day starting frame and forward target required");
        BigInteger endpoint = config.endpointDateRaw();
        BigInteger boundary = endpoint;
        if (current.compareTo(endpoint) < 0) {
            // Python bisect_right: an already reached monthly boundary advances to the next boundary.
            int low = 0;
            int high = config.boundaryRaws().size();
            while (low < high) {
                int middle = (low + high) >>> 1;
                if (config.boundaryRaws().get(middle).compareTo(current) <= 0) { low = middle + 1; }
                else { high = middle; }
            }
            boundary = config.boundaryRaws().get(low);
        }
        Status status = current.equals(endpoint) ? Status.ENDPOINT_REACHED
                : current.compareTo(endpoint) > 0 ? Status.ENDPOINT_OVERSHOT : Status.ADVANCE;
        return Optional.of(new Cap(config.founding().campaignId(), config.calendarProfile(), current,
                proposedTargetRaw, boundary, endpoint, proposedTargetRaw.min(boundary), status));
    }

    public static EndpointResult endpointResult(EndpointFrame frame, String resultStep, Cap cap) {
        return new EndpointResult(resultStep, frame, cap);
    }
}
