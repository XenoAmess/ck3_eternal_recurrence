package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CommandExpectation;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;

/** Durable references for one resume primitive. Qualification reopens both originals under the installed source. */
public record ResumeCoreObservation(ExactRef parentReceipt, ExactRef coreAcknowledgement, Instant observationDeadline) {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final String OPERATION = "resume-map";

    public ResumeCoreObservation {
        Objects.requireNonNull(parentReceipt);
        Objects.requireNonNull(coreAcknowledgement);
        Objects.requireNonNull(observationDeadline);
        require(parentReceipt.bytes() > 0 && coreAcknowledgement.bytes() > 0
                && !parentReceipt.equals(coreAcknowledgement), "Core resume requires distinct parent and query originals");
    }

    /** Structural check. The registered source verifies the committed reservation and independent Core ACK. */
    public void validate(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        require(command.origin() instanceof CommandOrigin.Gameplay && command.expectation() instanceof CommandExpectation.Gameplay
                && command.operation().value().equals(OPERATION) && command.arguments().members().isEmpty()
                && BUILD.executableSha256().equalsIgnoreCase(command.source().exactBuild())
                && command.expected().equals(AdvancePrimitives.expected(command.before(), command.source(),
                        command.operation(), command.arguments())),
                "Core resume requires its unchanged Full111 gameplay resume command");
        var guard = attempt.guard();
        require(command.origin().acceptsGuard(guard.origin()) && command.source().equals(guard.source())
                && command.sessionId().equals(guard.sessionId()) && command.operation().equals(guard.operation())
                && attempt.preparedRequest().step().equals(OPERATION)
                && attempt.preparedRequest().requiredCapability().filter("game.command.resume-map"::equals).isPresent(),
                "Core resume requires the original prepared resume attempt and guard");
        require(dispatch instanceof NativeActionPort.AckReceived && dispatch.requestId().equals(attempt.requestId()),
                "Core resume requires its exact positive original ACK");
        var ack = (NativeActionPort.AckReceived) dispatch;
        var result = AdvancePrimitives.nativeResult(ack, OPERATION);
        require("ck3_1210_full_clock_control_result_v1".equals(result.path("schema").textValue())
                && BUILD.matches(result.path("game_version").textValue(), result.path("executable_sha256").textValue())
                && BUILD.coreFrameAdapterId().equals(result.path("adapter_id").textValue())
                && ("ck3-" + BUILD.version() + "-native-headless-main-thread").equals(result.path("backend").textValue())
                && "submitted".equals(result.path("queue_status").textValue())
                && result.path("effect_attempted").isBoolean() && result.path("effect_attempted").booleanValue()
                && result.path("full_snapshot_before_verified").isBoolean() && result.path("full_snapshot_before_verified").booleanValue(),
                "Core resume requires the original submitted Full111 control result");
        var chronology = ack.custody().orElseThrow(() -> new IllegalArgumentException("Core resume requires original ACK custody"));
        chronology.verify(ack, guard);
        require(!chronology.writeEntered().observedAt().isBefore(attempt.submittedAt())
                && chronology.responseReceived().observedAt().isBefore(observationDeadline)
                && !observationDeadline.isAfter(command.deadline()),
                "Core resume observation escaped the original submitted attempt and deadline");
    }

    public List<ExactRef> references() {
        return List.of(parentReceipt, coreAcknowledgement);
    }
}
