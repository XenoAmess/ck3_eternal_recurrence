package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Shared native timeline primitives; the same coordinator prepares, sends and independently observes each child. */
public final class AdvancePrimitives implements ActionPorts.PreparationPort, ActionPorts.PostconditionPort {
    public static final String TIMELINE_OBSERVER = "xar.ck3.native-timeline-control/v1";
    public static final String CLOCK_OBSERVER = "xar.ck3.native-clock-control/v1";
    private static final Pattern ARM = Pattern.compile("research-arm-tactical-daily-sentinel-v1-(0|[1-9][0-9]*)-to-(0|[1-9][0-9]*)-speed-([1-5])-mode-(terminal|decision)-a-(0|[1-9][0-9]*)(.*)");
    private final AdvanceObservationPort observations;
    private final ClockStatusRead clockStatus;
    private final AdvanceWait waits;
    private final Optional<PendingUiLifeAdvance.Scope> pendingDate;
    public AdvancePrimitives(AdvanceObservationPort observations, ClockStatusRead clockStatus, Clock clock, int maximumFrames) {
        this(observations,clockStatus,clock,maximumFrames,Optional.empty());
    }
    /** The actual Root passes its identical Life scope; no second observer or continuation permission is created. */
    public AdvancePrimitives(AdvanceObservationPort observations, ClockStatusRead clockStatus, Clock clock, int maximumFrames,
            PendingUiLifeAdvance.Scope samePendingDate) {
        this(observations,clockStatus,clock,maximumFrames,Optional.of(Objects.requireNonNull(samePendingDate)));
    }
    private AdvancePrimitives(AdvanceObservationPort observations, ClockStatusRead clockStatus, Clock clock, int maximumFrames,
            Optional<PendingUiLifeAdvance.Scope> pendingDate) {
        this.observations = Objects.requireNonNull(observations); this.clockStatus = Objects.requireNonNull(clockStatus);
        this.waits = new AdvanceWait(observations, clock, maximumFrames);
        this.pendingDate = pendingDate;
    }
    public static boolean supports(OperationKey operation) {
        String step = operation.value();
        return step.equals("pause-map") || step.equals("resume-map") || step.matches("set-speed-[1-5]")
                || ARM.matcher(step).matches() || step.startsWith(ClockStatusRead.CANCEL_PREFIX);
    }
    public record ArmSpec(int startingDateRaw, int targetDateRaw, int speed, String mode, List<Integer> armyIds) {
        public ArmSpec { armyIds = List.copyOf(armyIds); require(targetDateRaw > startingDateRaw && (targetDateRaw - (long) startingDateRaw) % 24 == 0, "whole-day arm required"); }
    }
    public static ArmSpec armSpec(String step) {
        var match = ARM.matcher(step); require(match.matches(), "exact original sentinel arm step required");
        int count = Integer.parseInt(match.group(5)); require(count <= 64, "bounded native watch roster required");
        String tail = match.group(6); List<Integer> ids = new ArrayList<>();
        if (!tail.isEmpty()) {
            require(tail.matches("(?:-(?:0|[1-9][0-9]*))+"), "canonical native watch ID suffix required");
            for (String value : tail.substring(1).split("-")) ids.add(Integer.valueOf(value));
        }
        require(ids.size() == count && ids.stream().allMatch(id -> id >= 0) && ids.stream().distinct().count() == count, "native watch roster count/identity differs");
        return new ArmSpec(Integer.parseInt(match.group(1)), Integer.parseInt(match.group(2)), Integer.parseInt(match.group(3)), match.group(4), ids);
    }
    public static BigInteger cancelGeneration(String step) {
        require(step.startsWith(ClockStatusRead.CANCEL_PREFIX), "generation-bound cancel step required");
        var value = new CrossJsDecimalUInt64(step.substring(ClockStatusRead.CANCEL_PREFIX.length()));
        BigInteger generation = new BigInteger(value.decimal()); require(generation.signum() > 0, "positive original generation required"); return generation;
    }
    public static ActionCommand child(ActionCommand parent, AdvanceObservationPort.Frame current, String actionId, String step, Instant deadline) {
        require(supports(new OperationKey(step)), "only registered timeline primitives can become children");
        require(!deadline.isAfter(parent.deadline()), "child cannot extend original deadline");
        AdvanceWait.binding(parent, current, current);
        var expected = expected(current.identity(), current.source(), new OperationKey(step), new Obj(Map.of()));
        return new ActionCommand(actionId, current.identity(), parent.source(), parent.sessionId(), new OperationKey(step),
                new Obj(Map.of()), expected, parent.claims(), deadline);
    }
    /** Shared Root/basic and child expected producer. Actual Root/native guards still grant command authority. */
    public static ExpectedPostcondition expected(ObservationIdentity actualBefore, org.xar.ck3.control.g2.common.G2Source source,
            OperationKey operation, Obj arguments) {
        Objects.requireNonNull(actualBefore); Objects.requireNonNull(source); Objects.requireNonNull(operation); Objects.requireNonNull(arguments);
        require(actualBefore.machineId().equals(source.machineId()) && supports(operation) && arguments.members().isEmpty(),
                "actual original identity/source and registered argument-free timeline primitive required");
        String step = operation.value(); List<ExpectedValue> values; String schema;
        if (ARM.matcher(step).matches()) {
            ArmSpec arm = armSpec(step); require(actualBefore.frame().identity().dateRaw().equals(BigInteger.valueOf(arm.startingDateRaw())), "native arm must bind actual current date");
            values = armExpected(arm); schema = CLOCK_OBSERVER;
        } else if (step.startsWith(ClockStatusRead.CANCEL_PREFIX)) {
            values = List.of(new ExpectedText(new FieldKey("sentinel.state"), "idle"), new ExpectedText(new FieldKey("sentinel.generation"), cancelGeneration(step).toString())); schema = CLOCK_OBSERVER;
        } else {
            ExpectedValue value = step.startsWith("set-speed-") ? new ExpectedInteger(new FieldKey("speed"), BigInteger.valueOf(Integer.parseInt(step.substring(10))))
                    : step.equals("pause-map") ? new ExpectedBoolean(new FieldKey("paused"), true)
                    : new ExpectedBoolean(new FieldKey("timeline.resume_observed"), true);
            values = List.of(value); schema = TIMELINE_OBSERVER;
        }
        return new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, actualBefore, source, schema, values);
    }
    private static List<ExpectedValue> armExpected(ArmSpec arm) {
        return List.of(new ExpectedText(new FieldKey("sentinel.state"), "armed"),
                new ExpectedInteger(new FieldKey("sentinel.starting_date_raw"), BigInteger.valueOf(arm.startingDateRaw())),
                new ExpectedInteger(new FieldKey("sentinel.target_date_raw"), BigInteger.valueOf(arm.targetDateRaw())),
                new ExpectedInteger(new FieldKey("sentinel.speed"), BigInteger.valueOf(arm.speed())),
                new ExpectedInteger(new FieldKey("sentinel.army_count"), BigInteger.valueOf(arm.armyIds().size())),
                new ExpectedText(new FieldKey("sentinel.mode"), arm.mode().equals("terminal") ? "terminal_or_sentinel" : "decision_epoch"));
    }
    @Override public NativeRequest prepare(ActionCommand command) {
        require(pendingDate.isEmpty() || !pendingDate.orElseThrow().active() || !command.operation().value().equals("resume-map"),
                "actual pending date resume requires its original canonical writer session and preclock originals");
        return prepareRequest(command);
    }
    /** Central preparation runs before INTENT under the original writer; only the source-owned scope can add originals. */
    @Override public NativeRequest prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ActionCommand command,String requestId) {
        Objects.requireNonNull(same);
        NativeRequest base=prepareRequest(command);
        if(pendingDate.isEmpty())return base;
        try {
            NativeRequest actual=pendingDate.orElseThrow().prepare(same,command,requestId,base);
            require(actual.step().equals(base.step()) && actual.requiredCapability().equals(base.requiredCapability())
                    && Arrays.equals(actual.additionalFields().bytes(),base.additionalFields().bytes())
                    && actual.preparationEvidence().containsAll(base.preparationEvidence()),
                    "source-owned preclock preparation changed the exact registered Native request");
            return actual;
        } catch(IOException failure) {throw new UncheckedIOException("actual same-writer pending date preclock unavailable",failure);}
    }
    public static NativeRequest prepareRequest(ActionCommand command) {
        require(supports(command.operation()) && command.arguments().members().isEmpty(), "registered timeline primitive with no extra native fields required");
        String step = command.operation().value(); String capability;
        if (ARM.matcher(step).matches()) { armSpec(step); capability = ClockStatusRead.ARM_CAP; }
        else if (step.startsWith(ClockStatusRead.CANCEL_PREFIX)) { cancelGeneration(step); capability = ClockStatusRead.CANCEL_CAP; }
        else capability = "game.command." + step;
        return new NativeRequest(step, capability, new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        if (dispatch instanceof NativeActionPort.Unknown unknown) return new ActionPorts.Pending("original child submission UNKNOWN; no replay: " + unknown.reason(), List.of(attempt.guard().nativeEvidence()));
        if (!(dispatch instanceof NativeActionPort.AckReceived ack)) return new ActionPorts.Pending("child has no original Native ACK", List.of(attempt.guard().nativeEvidence()));
        if (!ack.nativeOk()) {
            JsonNode raw = StrictJson.parse(ack.originalFrame().bytes());
            JsonNode error = raw.get("error");
            if (error != null && error.isTextual() && !error.textValue().isEmpty())
                return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(), error.textValue(), clockStatus.preserve(ack)));
            return new ActionPorts.Pending("native rejection lacks its exact original error", List.of(clockStatus.preserve(ack)));
        }
        Instant window = ActionObservationWindow.deadline(command);
        AdvanceObservationPort.Frame current = observations.current(command, window);
        if (command.expected().observerSchema().equals(CLOCK_OBSERVER)) {
            ClockStatusRead.Observation read = clockStatus.observe(command, current, window);
            Status actual = read.status(); String step = command.operation().value();
            List<ExpectedValue> values;
            if (ARM.matcher(step).matches()) {
                ArmSpec arm = armSpec(step); Status original = acknowledgedSentinel(ack, step);
                require(actual.equals(original) && actual.generation().decimal().matches("[1-9][0-9]*"), "independent status did not observe the exact original arm generation/content");
                values = statusValues(actual);
                require(values.containsAll(armExpected(arm)), "actual independent arm status differs from requested arm");
            } else {
                BigInteger generation = cancelGeneration(step);
                JsonNode result = nativeResult(ack, step);
                require(result.path("status").isTextual() && result.path("status").textValue().equals("canceled")
                        && actual.state() == org.xar.ck3.control.reconciliation.LateOutcome.State.IDLE
                        && SentinelObservation.nativeGeneration(actual).equals(generation), "independent status did not confirm cancellation of the same generation");
                values = statusValues(actual);
            }
            return new ActionPorts.ControlObserved(new ActionState.ControlApplied(read.receipt(), CLOCK_OBSERVER, values));
        }
        String step = command.operation().value();
        current = waits.until(command, current, frame -> timelineSatisfied(command, frame), window);
        if (!timelineSatisfied(command, current)) return new ActionPorts.Pending("native timeline ACK lacks independently observed state", List.of(current.originalEvidence()));
        List<ExpectedValue> values = step.startsWith("set-speed-") ? List.of(new ExpectedInteger(new FieldKey("speed"), integer(current.semantic().get("speed"), "speed")))
                : step.equals("pause-map") ? PauseConfirmation.actualValues()
                : List.of(new ExpectedBoolean(new FieldKey("timeline.resume_observed"), true));
        var evidence = AdvancePrimitiveEvidence.preserve(command, current, clockStatus.archive());
        var observation = new ActionState.EffectObservation(current.identity(), current.source(), current.sessionId(), TIMELINE_OBSERVER,
                values, current.provenance(), current.observedAt(), current.originalEvidence(), List.of(evidence));
        return step.equals("pause-map") ? new ActionPorts.PauseObserved(observation) : new ActionPorts.EffectObserved(observation);
    }
    private static boolean timelineSatisfied(ActionCommand command, AdvanceObservationPort.Frame frame) {
        String step = command.operation().value();
        if (step.startsWith("set-speed-")) return integer(frame.semantic().get("speed"), "speed").intValueExact() == Integer.parseInt(step.substring(10));
        if (step.equals("pause-map")) return AdvancePolicy.truth(frame.semantic(), "paused");
        // The native daily stop can execute before any running frame is published. This is still
        // a real resume effect only with independent later native revision/date or a new modal.
        return !AdvancePolicy.truth(frame.semantic(), "paused") || frame.identity().frame().identity().dateRaw().compareTo(command.before().frame().identity().dateRaw()) > 0
                || AdvanceProgress.newModal(frame.semantic(), command.before(), Optional.empty()).isPresent();
    }
    public static JsonNode nativeResult(NativeActionPort.AckReceived ack, String step) {
        require(ack.nativeOk() && ack.originalResultToken().isPresent(), "successful native original result required");
        JsonNode node = StrictJson.parse(ack.originalResultToken().orElseThrow().bytes());
        require(node.isObject() && node.path("step").isTextual() && node.path("step").textValue().equals(step)
                && node.path("accepted").isBoolean() && node.path("accepted").booleanValue(), "native original result step/acceptance differs"); return node;
    }
    public static Status acknowledgedSentinel(NativeActionPort.AckReceived ack, String step) {
        return SentinelObservation.decode(nativeResult(ack, step).get("tactical_daily_sentinel"));
    }
    public static List<ExpectedValue> statusValues(Status status) {
        return List.of(new ExpectedText(new FieldKey("sentinel.state"), status.state().name().toLowerCase(java.util.Locale.ROOT)),
                new ExpectedText(new FieldKey("sentinel.generation"), status.generation().decimal()),
                new ExpectedInteger(new FieldKey("sentinel.starting_date_raw"), BigInteger.valueOf(status.startingDateRaw())),
                new ExpectedInteger(new FieldKey("sentinel.target_date_raw"), BigInteger.valueOf(status.targetDateRaw())),
                new ExpectedInteger(new FieldKey("sentinel.speed"), BigInteger.valueOf(status.speed())),
                new ExpectedInteger(new FieldKey("sentinel.army_count"), BigInteger.valueOf(status.armyCount())),
                new ExpectedText(new FieldKey("sentinel.mode"), status.mode().name().toLowerCase(java.util.Locale.ROOT)));
    }
}
