package org.xar.ck3.control.wave2.events.eventoutcome;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Evaluation;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Expectation;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.PlanInput;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.RunnerIssue;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Selection;

/** In-process consumer seam, with source/episode identities preserved outside the legacy scalar ABI. */
public final class EventOutcomeConsumerPort {
    private EventOutcomeConsumerPort() { }
    /** sourceSha256 is the event definition digest, not a changing observation receipt digest. */
    public record EpisodeSource(String machineId, String episodeId, String gameGeneration,
                                int eventInstanceId, String sourceSha256) {
        public EpisodeSource {
            StrictJson.text(machineId); StrictJson.text(episodeId); StrictJson.text(gameGeneration);
            // Existing normalize_current_event_window_context_v1 defines a positive signed int32 domain.
            StrictJson.require(eventInstanceId > 0, "current event instance positive int32");
            StrictJson.require(sourceSha256 != null && sourceSha256.matches("[A-Fa-f0-9]{64}"), "source SHA-256");
        }
    }
    public sealed interface Attachment permits Rejected, Evaluated { }
    public record Rejected(String reason) implements Attachment {
        public Rejected { StrictJson.text(reason); }
    }
    public record Evaluated(EpisodeSource episodeSource, VanillaOptionProjection.Result optionProjection,
                            Boolean submissionAckAccepted, Expectation expectation, Evaluation materialResult,
                            Optional<RunnerIssue> runnerIssue) implements Attachment {
        public Evaluated {
            Objects.requireNonNull(episodeSource, "episodeSource");
            Objects.requireNonNull(optionProjection, "optionProjection");
            Objects.requireNonNull(expectation, "expectation");
            Objects.requireNonNull(materialResult, "materialResult");
            Objects.requireNonNull(runnerIssue, "runnerIssue");
        }
        public boolean actionAuthorized() { return false; }
        public boolean replayAuthorized() { return false; }
        public boolean saveCreditGranted() { return false; }
    }

    public static Attachment attach(EpisodeSource plannedSource, EpisodeSource observedSource,
                                    VanillaOptionProjection.Result optionProjection, PlanInput planInput,
                                    Boolean submissionAckAccepted, Selection eventSelection) {
        Objects.requireNonNull(plannedSource, "plannedSource");
        Objects.requireNonNull(observedSource, "observedSource");
        Objects.requireNonNull(optionProjection, "optionProjection");
        Objects.requireNonNull(planInput, "planInput");
        if (!plannedSource.equals(observedSource)) return new Rejected("episode_generation_event_or_source_mismatch");
        if (optionProjection.binding().sourceAnchors().stream().noneMatch(anchor -> anchor.registrySha256().equals(plannedSource.sourceSha256()))) {
            return new Rejected("event_definition_source_binding_mismatch");
        }
        if (optionProjection.status() != VanillaOptionProjection.Status.PROJECTION_READY
                || optionProjection.selectedOption() == null || optionProjection.checks().values().stream().anyMatch(value -> !value)) {
            return new Rejected("option_projection_not_ready");
        }
        ScalarEventOutcome.Decision decision = planInput.decision();
        if (decision == null || !Objects.equals(decision.eventDefinitionKey(), optionProjection.binding().eventDefinitionKey())
                || !Objects.equals(decision.ck3Build(), optionProjection.binding().ck3Build())
                || !BigInteger.valueOf(optionProjection.selectedOption().nativeOptionIndex()).equals(decision.selectedNativeOptionIndex())
                || !BigInteger.valueOf(optionProjection.selectedOption().nativeOptionIndex() + 1L).equals(decision.selectedOptionNumber())) {
            return new Rejected("registered_decision_option_binding_mismatch");
        }
        Optional<Expectation> planned = ScalarEventOutcome.plan(planInput);
        if (planned.isEmpty()) return new Rejected("scalar_material_route_not_handled");
        Expectation expectation = planned.orElseThrow();
        Evaluation evaluation = ScalarEventOutcome.evaluate(expectation, eventSelection);
        // ACK is retained, but only the independent same-character observations decide material result.
        return new Evaluated(plannedSource, optionProjection, submissionAckAccepted, expectation, evaluation,
            ScalarEventOutcome.runnerIssue(expectation, evaluation));
    }
}
