package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Pure native deadline transaction contract. Existing custody performs every native action and wait. */
public final class DeadlineTransport {
    public static final String ARM_PREFIX = "research-arm-tactical-daily-sentinel-v1-";
    public static final String STATUS_STEP = "research-query-tactical-daily-sentinel-v1";
    public static final String CANCEL_PREFIX = "research-cancel-tactical-daily-sentinel-v1-generation-";
    public static final String CLOCK_SCHEMA = "xar.ck3.campaign-native-date-clock/v1";

    private DeadlineTransport() { }

    /** Declared projection of the existing semantic frame. Missing/null presentation IDs stay nullable. */
    public record Frame(int dateRaw, boolean paused, int speed, Optional<String> snapshotId,
                        Optional<BigInteger> nativeRevision) {
        public Frame {
            require(dateRaw >= 0 && speed >= 1 && speed <= 5, "actual int32 date and policy speed required");
            Objects.requireNonNull(snapshotId, "snapshotId"); Objects.requireNonNull(nativeRevision, "nativeRevision");
            snapshotId.ifPresent(StrictJson::text);
            nativeRevision.ifPresent(revision -> require(revision.signum() >= 0, "nonnegative native revision required"));
            if (snapshotId.isPresent() && nativeRevision.isPresent()) {
                require(snapshotId.orElseThrow().equals("native:" + nativeRevision.orElseThrow()),
                        "frame snapshot/native revision differs");
            }
        }
    }

    /** Reuses the existing typed deadline cap; it does not recompute calendar or reselect gameplay speed. */
    public record PreparedRequest(String invocationId, CampaignDeadline.Cap cap, Frame starting, int speed) {
        public PreparedRequest {
            require(invocationId != null && invocationId.matches("[0-9a-f]{32}"), "canonical invocation identity required");
            Objects.requireNonNull(cap, "cap"); Objects.requireNonNull(starting, "starting");
            require(cap.status() == CampaignDeadline.Status.ADVANCE && starting.paused(),
                    "native campaign deadline requires the original paused advance frame");
            require(cap.startingDateRaw().equals(BigInteger.valueOf(starting.dateRaw())), "deadline starting frame differs");
            require(cap.targetDateRaw().signum() >= 0 && cap.targetDateRaw().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                    "native target is signed int32");
            long delta = cap.targetDateRaw().longValueExact() - starting.dateRaw();
            require(delta >= 24 && delta <= 45 * 24 && delta % 24 == 0 && speed >= 1 && speed <= 5,
                    "campaign native deadline requires a paused1..45 whole-day slice");
        }
        public int targetDateRaw() { return cap.targetDateRaw().intValueExact(); }
        public String armStep() {
            return ARM_PREFIX + starting.dateRaw() + "-to-" + targetDateRaw() + "-speed-" + speed + "-mode-terminal-a-0";
        }
    }

    /** Immutable retained JSON at the legacy extension boundary; integers stay BigInteger and decimals stay BigDecimal. */
    public record JsonDocument(String text) {
        public JsonDocument {
            Objects.requireNonNull(text, "text");
            JsonNode node = StrictJson.parse(text.getBytes(StandardCharsets.UTF_8));
            require(node.isObject(), "legacy receipt object required");
        }
        public static JsonDocument of(JsonNode node) { return new JsonDocument(LegacyJsonValues.text(node)); }
        public JsonNode toJson() { return StrictJson.parse(text.getBytes(StandardCharsets.UTF_8)); }
    }

    public record NativeReceipt(String step, boolean accepted, String status,
                                Optional<Status> sentinel, JsonDocument original) {
        public NativeReceipt {
            StrictJson.text(step); StrictJson.text(status);
            Objects.requireNonNull(sentinel, "sentinel"); Objects.requireNonNull(original, "original");
            JsonNode retained = original.toJson();
            require(step.equals(StrictJson.text(retained.get("step")))
                    && accepted == SentinelObservation.bool(retained.get("accepted"))
                    && status.equals(StrictJson.text(retained.get("status"))),
                    "typed primitive receipt differs from retained original JSON");
            JsonNode retainedSentinel = retained.get("tactical_daily_sentinel");
            Optional<Status> parsed = retainedSentinel == null || retainedSentinel.isNull() ? Optional.empty()
                    : Optional.of(SentinelObservation.decode(retainedSentinel));
            require(sentinel.equals(parsed), "typed primitive sentinel differs from retained original JSON");
        }
    }

    public record Action(String step, NativeReceipt result) {
        public Action {
            StrictJson.text(step); Objects.requireNonNull(result, "result");
            require(step.equals(result.step()), "outer action and primitive result steps differ");
        }
    }

    public sealed interface SpeedConfiguration permits AlreadyObservedSpeed, SubmittedSpeed { }
    public record AlreadyObservedSpeed(int speed, Optional<String> snapshotId, Optional<BigInteger> nativeRevision,
                                        int dateRaw) implements SpeedConfiguration {
        public AlreadyObservedSpeed {
            require(speed >= 1 && speed <= 5 && dateRaw >= 0, "observed policy speed/date required");
            Objects.requireNonNull(snapshotId, "snapshotId"); Objects.requireNonNull(nativeRevision, "nativeRevision");
        }
    }
    public record SubmittedSpeed(String step) implements SpeedConfiguration {
        public SubmittedSpeed { require(step != null && step.matches("set-speed-[1-5]"), "original speed setter step required"); }
    }

    public enum ObservationKind { NATIVE_STOP_OBSERVED, EARLY_BOUNDARY_CANCEL_RETURNED }

    public record ClockEnvelope(int startingDateRaw, int targetDateRaw, Status armed,
                                 Status stopped, Optional<NativeReceipt> earlyBoundaryCancel,
                                 SpeedConfiguration speedConfiguration) {
        public ClockEnvelope {
            require(startingDateRaw >= 0 && targetDateRaw > startingDateRaw, "forward native date clock required");
            Objects.requireNonNull(armed, "armed"); Objects.requireNonNull(stopped, "stopped");
            Objects.requireNonNull(earlyBoundaryCancel, "earlyBoundaryCancel");
            Objects.requireNonNull(speedConfiguration, "speedConfiguration");
        }
    }

    /** Own action slice only; an existing driver keeps the full semantic snapshot and earlier action prefix. */
    public record Completion(Frame current, ClockEnvelope clock, List<Action> ownActions) {
        public Completion {
            Objects.requireNonNull(current, "current"); Objects.requireNonNull(clock, "clock");
            ownActions = List.copyOf(ownActions);
            require(ownActions.size() >= 2 && ownActions.size() <= 8, "bounded actual deadline action slice required");
        }
    }

    /** This is a protocol observation, never a source/recovery/action admission or saved-day award. */
    public static final class Observation {
        private final PreparedRequest request;
        private final Completion completion;
        private final ObservationKind kind;
        private Observation(PreparedRequest request, Completion completion, ObservationKind kind) {
            this.request = Objects.requireNonNull(request, "request");
            this.completion = Objects.requireNonNull(completion, "completion");
            this.kind = Objects.requireNonNull(kind, "kind");
        }
        public PreparedRequest request() { return request; }
        public Completion completion() { return completion; }
        public ObservationKind kind() { return kind; }
        public boolean replayAllowed() { return false; }
        public boolean nativeAdmissionGranted() { return false; }
        public int savedDayCredit() { return 0; }
    }

    /** An explicit refusal of the supplied native postcondition, separate from codec/internal failures. */
    public static final class ObservationRejection extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        private ObservationRejection(String message) { super(message); }
    }

    private static void requireObservation(boolean condition, String message) {
        if (!condition) { throw new ObservationRejection(message); }
    }

    public static Observation observe(PreparedRequest request, Completion completion) {
        Objects.requireNonNull(request, "request"); Objects.requireNonNull(completion, "completion");
        ClockEnvelope clock = completion.clock();
        int start = request.starting().dateRaw(); int target = request.targetDateRaw(); int end = completion.current().dateRaw();
        requireObservation(completion.current().paused() && end >= start && end <= target && (end - start) % 24 == 0,
                "campaign native deadline did not observe a paused same-calendar ending frame");
        requireObservation(clock.startingDateRaw() == start && clock.targetDateRaw() == target, "native clock request identity differs");
        validateArm(request, clock.armed());
        boolean early = clock.stopped().state() == State.ARMED && end < target;
        if (early) { validateEarlyBoundary(request, completion); }
        else {
            requireObservation(clock.earlyBoundaryCancel().isEmpty(), "triggered native stop cannot also claim cancellation");
            validateStop(request, clock.armed(), clock.stopped(), end);
        }
        validateSpeed(request, clock.speedConfiguration());
        validateActions(request, completion, early);
        return new Observation(request, completion,
                early ? ObservationKind.EARLY_BOUNDARY_CANCEL_RETURNED : ObservationKind.NATIVE_STOP_OBSERVED);
    }

    private static void validateArm(PreparedRequest request, Status arm) {
        requireObservation(arm.state() == State.ARMED && SentinelObservation.nativeGeneration(arm).signum() > 0
                && arm.startingDateRaw() == request.starting().dateRaw() && arm.targetDateRaw() == request.targetDateRaw()
                && arm.lastObservedDateRaw() == request.starting().dateRaw() && arm.triggerDateRaw() == 0
                && arm.speed() == request.speed() && arm.mode() == Mode.TERMINAL_OR_SENTINEL
                && arm.armyCount() == 0 && arm.combatCount() == 0 && arm.completedDailyTicks() == 0
                && arm.intermediatePauseCount() == 0 && arm.triggerFlags() == 0 && arm.triggerReasons().isEmpty()
                && arm.signedDateDeltaFromTargetRaw() == 0 && arm.overshootDays() == -1
                && !arm.pauseWrapperCalled() && !arm.pauseObserved() && !arm.terminalObserved() && !arm.abnormal(),
                "native tactical sentinel arm acknowledgement is inconsistent");
    }

    private static void validateStop(PreparedRequest request, Status arm, Status stop, int end) {
        int elapsed = (end - request.starting().dateRaw()) / 24;
        requireObservation(stop.state() == State.TRIGGERED && !stop.abnormal()
                && stop.generation().equals(arm.generation()) && stop.startingDateRaw() == request.starting().dateRaw()
                && stop.targetDateRaw() == request.targetDateRaw() && stop.lastObservedDateRaw() == end
                && stop.triggerDateRaw() == end && stop.speed() == request.speed()
                && stop.mode() == Mode.TERMINAL_OR_SENTINEL && stop.armyCount() == 0 && stop.combatCount() == 0
                && !stop.triggerReasons().isEmpty() && stop.triggerFlags() != 0 && stop.pauseObserved()
                && stop.signedDateDeltaFromTargetRaw() == end - request.targetDateRaw() && stop.overshootDays() == 0
                && elapsed > 0 && stop.completedDailyTicks() == elapsed,
                "native sentinel stop generation/date/tick postcondition differs");
        requireObservation(stop.triggerReasons().contains("date_deadline") == (end == request.targetDateRaw()),
                "native sentinel deadline reason disagrees with dates");
        boolean nativePause = stop.triggerReasons().contains("native_pause");
        requireObservation(stop.intermediatePauseCount() == (nativePause ? 1 : 0) && stop.pauseWrapperCalled() != nativePause,
                "native sentinel pause ownership disagrees with trigger reasons");
    }

    private static void validateEarlyBoundary(PreparedRequest request, Completion completion) {
        ClockEnvelope clock = completion.clock(); Status stopped = clock.stopped();
        NativeReceipt cancel = clock.earlyBoundaryCancel().orElseThrow(
                () -> new ObservationRejection("early native boundary lacks returned generation-bound cancel"));
        String expected = CANCEL_PREFIX + clock.armed().generation().decimal();
        requireObservation(stopped.generation().equals(clock.armed().generation()) && stopped.startingDateRaw() == request.starting().dateRaw()
                && stopped.targetDateRaw() == request.targetDateRaw() && stopped.speed() == request.speed() && stopped.armyCount() == 0,
                "campaign early-boundary sentinel identity changed");
        requireObservation(cancel.step().equals(expected) && cancel.accepted() && cancel.status().equals("canceled"),
                "campaign early-boundary sentinel cancellation is unconfirmed");
        // Original authority still owns real _life_advance_progressed and its post-cancel fresh read.
        // This branch records that returned proof; it grants no new action or cancellation permission.
    }

    private static void validateSpeed(PreparedRequest request, SpeedConfiguration speed) {
        if (speed instanceof AlreadyObservedSpeed observed) {
            requireObservation(request.starting().speed() == request.speed() && observed.speed() == request.speed()
                    && observed.snapshotId().equals(request.starting().snapshotId())
                    && observed.nativeRevision().equals(request.starting().nativeRevision())
                    && observed.dateRaw() == request.starting().dateRaw(), "already-observed speed source differs");
        } else if (speed instanceof SubmittedSpeed submitted) {
            requireObservation(request.starting().speed() != request.speed() && submitted.step().equals("set-speed-" + request.speed()),
                    "speed setter branch differs from actual starting observation");
        }
    }

    private static void validateActions(PreparedRequest request, Completion completion, boolean early) {
        List<Action> actions = completion.ownActions(); int index = 0;
        if (completion.clock().speedConfiguration() instanceof SubmittedSpeed submitted) {
            Action setter = actions.get(index++);
            requireObservation(setter.step().equals(submitted.step()) && setter.result().accepted(), "actual speed setter receipt absent");
        }
        requireObservation(index < actions.size(), "native Arm action absent");
        Action arm = actions.get(index++);
        requireObservation(arm.step().equals(request.armStep()) && arm.result().accepted() && arm.result().status().equals("available")
                && arm.result().sentinel().equals(Optional.of(completion.clock().armed())), "original native Arm receipt differs");
        if (index < actions.size() && actions.get(index).step().equals("resume-map")) {
            requireObservation(actions.get(index).result().accepted(), "resume acknowledgement rejected or unknown"); index++;
        }
        int pauses = 0;
        while (index < actions.size() && actions.get(index).step().equals("pause-map")) {
            requireObservation(++pauses <= 3, "unbounded native pause attempts");
            NativeReceipt pause = actions.get(index++).result();
            if (!pause.accepted()) {
                JsonNode raw = pause.original().toJson();
                requireObservation(pause.status().equals("rejected") && raw.path("error").isTextual()
                        && raw.path("error").textValue().equals("CK3 map state is unavailable"),
                        "unrecognized native pause rejection");
            }
        }
        requireObservation(index < actions.size(), "native Status action absent");
        Action status = actions.get(index++);
        requireObservation(status.step().equals(STATUS_STEP) && status.result().accepted() && status.result().status().equals("available")
                && status.result().sentinel().equals(Optional.of(completion.clock().stopped())), "original native Status receipt differs");
        if (early) {
            requireObservation(index < actions.size(), "native early-boundary cancel action absent");
            Action cancel = actions.get(index++);
            requireObservation(cancel.result().original().toJson().equals(completion.clock().earlyBoundaryCancel().orElseThrow().original().toJson()),
                    "original native cancel receipt differs");
        }
        requireObservation(index == actions.size(), "extra native deadline actions or repeated resume remain");
    }

    public static ObjectNode clockJson(ClockEnvelope clock) {
        ObjectNode node = StrictJson.object();
        node.put("schema", CLOCK_SCHEMA); node.put("scope", "campaign_date_deadline");
        node.put("starting_date_raw", clock.startingDateRaw()); node.put("target_date_raw", clock.targetDateRaw());
        node.set("armed", SentinelObservation.toJson(clock.armed())); node.set("stopped", SentinelObservation.toJson(clock.stopped()));
        if (clock.earlyBoundaryCancel().isPresent()) { node.set("early_boundary_cancel", clock.earlyBoundaryCancel().orElseThrow().original().toJson()); }
        else { node.putNull("early_boundary_cancel"); }
        ObjectNode speed = node.putObject("speed_configuration");
        if (clock.speedConfiguration() instanceof SubmittedSpeed submitted) {
            speed.put("status", "submitted"); speed.put("step", submitted.step());
        } else if (clock.speedConfiguration() instanceof AlreadyObservedSpeed observed) {
            speed.put("status", "already_observed"); speed.put("submitted", false); speed.put("observed_speed", observed.speed());
            if (observed.snapshotId().isPresent()) { speed.put("source_snapshot_id", observed.snapshotId().orElseThrow()); }
            else { speed.putNull("source_snapshot_id"); }
            if (observed.nativeRevision().isPresent()) { speed.put("source_native_revision", observed.nativeRevision().orElseThrow()); }
            else { speed.putNull("source_native_revision"); }
            speed.put("source_date_raw", observed.dateRaw());
        }
        node.put("exact_one_day_qualification_claimed", false);
        return node;
    }
}
