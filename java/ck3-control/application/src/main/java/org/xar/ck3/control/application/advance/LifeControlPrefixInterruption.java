package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Retained DATA for a source-owned interrupted initialization, never a completed calendar advance. */
public record LifeControlPrefixInterruption(String actionId, String bodySha256, CompositeExecution execution,
        LifeAdvanceEvidence.FrameRecord ending) {
    public LifeControlPrefixInterruption {
        StrictJson.text(actionId);
        require(bodySha256 != null && bodySha256.matches("[0-9a-f]{64}"), "exact original Life body digest required");
        Objects.requireNonNull(execution); Objects.requireNonNull(ending);
    }
    public void validateParent(ActionCommand parent, CompositeExecution retained) {
        Objects.requireNonNull(parent); Objects.requireNonNull(retained);
        require(actionId.equals(parent.actionId()) && bodySha256.equals(ActionCodec.bodySha256(parent))
                && execution.equals(retained), "interrupted initialization changed its original Life command/execution");
        require(LifeAdvanceComposite.accepts(parent.operation().value()) && retained.handlerId().equals(LifeAdvanceComposite.HANDLER)
                && parent.origin() instanceof CommandOrigin.Gameplay, "registered original gameplay Life parent required");
        var guard = retained.guard();
        require(parent.origin().acceptsGuard(guard.origin()) && guard.source().equals(parent.source())
                && guard.sessionId().equals(parent.sessionId()) && guard.operation().equals(parent.operation())
                && guard.observed().equals(parent.before()), "interrupted Life guard changed its original authority");
        require(!retained.children().isEmpty() && retained.children().size() <= 2, "one finite original initialization prefix required");
        AdvancePlan plan = AdvancePlan.decode(parent);
        require(parent.expected().observerSchema().equals(AdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected())
                && plan.startingDateRaw().equals(parent.before().frame().identity().dateRaw()),
                "interrupted Life plan differs from its complete original expectation");
    }
    public void validateChildren(ActionCommand parent, List<ActionReceipt> canonicalChildren) {
        validateParent(parent, execution);
        canonicalChildren = List.copyOf(canonicalChildren);
        require(canonicalChildren.size() == execution.children().size(), "complete canonical prefix required");
        AdvanceClockArchivedReplay.verifyChildBindings(parent, canonicalChildren);
        AdvancePlan plan = AdvancePlan.decode(parent);
        boolean paused = false, speed = false;
        for (int index = 0; index < canonicalChildren.size(); index++) {
            ActionReceipt child = canonicalChildren.get(index);
            var bound = execution.children().get(index);
            require(bound.actionId().equals(child.command().actionId()) && bound.bodySha256().equals(child.bodySha256())
                    && child.command().arguments().members().isEmpty(), "original prefix child/body/arguments changed");
            require(child.state() instanceof ActionState.Settled, "UNKNOWN, rejected or composite prefix cannot be interrupted as complete");
            var settlement = ((ActionState.Settled) child.state()).settlement();
            String step = child.command().operation().value();
            ActionState.EffectObservation effect;
            if (step.equals("pause-map")) {
                require(!paused && !speed && settlement instanceof ActionState.PauseConfirmed,
                        "only one independently confirmed pause before speed is an initialization prefix");
                paused = true;
                effect = ((ActionState.PauseConfirmed) settlement).observation();
                require(effect.actual().contains(new ExpectedBoolean(new FieldKey("paused"), true)), "original pause post-state missing");
            } else {
                require(step.equals("set-speed-" + plan.speed()) && !speed && settlement instanceof ActionState.Applied,
                        "resume, arm, cancel, foreign speed, duplicate or unconfirmed child is not an initialization prefix");
                speed = true;
                effect = ((ActionState.Applied) settlement).observation();
                require(effect.actual().contains(new ExpectedInteger(new FieldKey("speed"), BigInteger.valueOf(plan.speed()))),
                        "original speed post-state missing");
            }
            require(child.command().expected().observerSchema().equals(AdvancePrimitives.TIMELINE_OBSERVER)
                    && effect.observerSchema().equals(AdvancePrimitives.TIMELINE_OBSERVER)
                    && effect.source().equals(parent.source()) && effect.sessionId().equals(parent.sessionId()),
                    "initialization child has no original typed timeline post-state");
        }
    }
    public void validateFrame(ActionCommand parent, AdvanceObservationPort.Frame actualEnding,
            List<ActionReceipt> canonicalChildren) {
        validateChildren(parent, canonicalChildren);
        var before = parent.before(); var after = actualEnding.identity();
        require(after.equals(ending.identity()) && actualEnding.provenance().equals(ending.provenance())
                && actualEnding.observedAt().equals(ending.observedAt()) && actualEnding.originalEvidence().equals(ending.nativeFrame()),
                "interrupted initialization frame record differs from actual replayed frame");
        require(actualEnding.source().equals(parent.source()) && actualEnding.sessionId().equals(parent.sessionId())
                && after.machineId().equals(before.machineId()) && after.game().equals(before.game())
                && after.observationVersion() == before.observationVersion()
                && after.frame().episodeRunId().equals(before.frame().episodeRunId())
                && after.frame().identity().player().equals(before.frame().identity().player()),
                "interrupted initialization crossed original source/Game/session/episode/actor");
        require(actualEnding.provenance() instanceof ObservationProvenance.Push
                && AdvancePolicy.truth(actualEnding.semantic(), "paused")
                && after.frame().identity().dateRaw().equals(AdvancePlan.decode(parent).startingDateRaw()),
                "interruption requires actual independent paused same-date Native post-state");
        actualEnding.provenance().validate(after, actualEnding.originalEvidence());
        for (ActionReceipt child : canonicalChildren) {
            var settlement = ((ActionState.Settled) child.state()).settlement();
            var effect = settlement instanceof ActionState.Applied applied ? applied.observation()
                    : ((ActionState.PauseConfirmed) settlement).observation();
            var attempt = ActionTransitions.attempt(child.state()).orElseThrow();
            require(!actualEnding.observedAt().isBefore(effect.observedAt())
                    && !effect.observedAt().isBefore(attempt.submittedAt())
                    && actualEnding.provenance().independentOf(attempt.requestId())
                    && after.frame().identity().nativeRevision().compareTo(effect.after().frame().identity().nativeRevision()) >= 0
                    && after.frame().identity().dateRaw().equals(effect.after().frame().identity().dateRaw()),
                    "interrupted initialization lacks actual post-child chronology/date/Native state");
        }
    }
    public List<ExactRef> references() { return List.of(ending.nativeFrame(), ending.driverFacts(), ending.semantic()); }
}
