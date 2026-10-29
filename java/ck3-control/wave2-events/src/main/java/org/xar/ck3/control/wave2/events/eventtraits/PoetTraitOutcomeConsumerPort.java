package org.xar.ck3.control.wave2.events.eventtraits;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection;
import org.xar.ck3.control.wave2.events.eventoutcome.EventOutcomeConsumerPort.EpisodeSource;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome;

/** Source/episode/option attachment seam alongside the existing scalar consumer. */
public final class PoetTraitOutcomeConsumerPort {
    private PoetTraitOutcomeConsumerPort() { }
    public sealed interface Attachment permits Rejected, Evaluated { }
    public record Rejected(String reason) implements Attachment { public Rejected { Objects.requireNonNull(reason); } }
    public record Evaluated(EpisodeSource source, VanillaOptionProjection.Result optionProjection,
                            Boolean submissionAckAccepted, PoetTraitOutcome.Evaluation materialResult) implements Attachment {
        public Evaluated { Objects.requireNonNull(source); Objects.requireNonNull(optionProjection); Objects.requireNonNull(materialResult); }
        public boolean actionAuthorized() { return false; }
        public boolean replayAuthorized() { return false; }
        public boolean saveCreditGranted() { return false; }
    }
    public static Attachment attach(EpisodeSource plannedSource, EpisodeSource observedSource,
                                    VanillaOptionProjection.Result optionProjection, PoetTraitOutcome.PlanInput input,
                                    Boolean submissionAckAccepted, PoetTraitOutcome.Selection selection) {
        Objects.requireNonNull(plannedSource); Objects.requireNonNull(observedSource);
        Objects.requireNonNull(optionProjection); Objects.requireNonNull(input);
        if (!plannedSource.equals(observedSource)) return new Rejected("episode_generation_event_or_source_mismatch");
        if (!PoetTraitOutcome.SOURCE_SHA256.equalsIgnoreCase(plannedSource.sourceSha256())
                || optionProjection.binding().sourceAnchors().stream().noneMatch(anchor ->
                    PoetTraitOutcome.SOURCE_PATH.equals(anchor.relativePath())
                    && PoetTraitOutcome.SOURCE_SHA256.equalsIgnoreCase(anchor.registrySha256())
                    && PoetTraitOutcome.SOURCE_SHA256.equalsIgnoreCase(anchor.indexedSha256()))) {
            return new Rejected("event_definition_source_binding_mismatch");
        }
        if (optionProjection.status() != VanillaOptionProjection.Status.PROJECTION_READY || optionProjection.selectedOption() == null
                || optionProjection.checks().values().stream().anyMatch(value -> !value)) return new Rejected("option_projection_not_ready");
        ScalarEventOutcome.Decision decision = input.decision();
        if (decision == null || !Objects.equals(decision.eventDefinitionKey(), optionProjection.binding().eventDefinitionKey())
                || !Objects.equals(decision.ck3Build(), optionProjection.binding().ck3Build())
                || !EventTraitMembership.EXECUTABLE_SHA256.equals(optionProjection.binding().ck3ExeSha256())
                || !BigInteger.valueOf(optionProjection.selectedOption().nativeOptionIndex()).equals(decision.selectedNativeOptionIndex())
                || !BigInteger.valueOf(optionProjection.selectedOption().nativeOptionIndex() + 1L).equals(decision.selectedOptionNumber())) {
            return new Rejected("registered_decision_option_binding_mismatch");
        }
        Optional<PoetTraitOutcome.Expectation> expected = PoetTraitOutcome.plan(input);
        if (expected.isEmpty()) return new Rejected("poet_trait_material_route_not_handled");
        return new Evaluated(plannedSource, optionProjection, submissionAckAccepted, PoetTraitOutcome.evaluate(expected.orElseThrow(), selection));
    }
}
