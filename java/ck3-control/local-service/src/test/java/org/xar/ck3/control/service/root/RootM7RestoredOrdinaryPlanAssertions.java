package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7KernelPlanConsumer;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Checks the real restored Root's next complete ordinary PLAN. It creates no private input or authority. */
public final class RootM7RestoredOrdinaryPlanAssertions {
    private RootM7RestoredOrdinaryPlanAssertions() { }

    private record Planned(PlanningRequest request, PlanningResult result,
            Optional<GiftDomainSource.PendingFrameWait> pending, Optional<String> sourceEpoch, Optional<ExactRef> executable) { }

    /**
     * Call after the previous physical/Driver freeze has unwound. A null native-campaign goal
     * belongs to the separate warm test and cannot supply this positive ordinary-goal input.
     */
    public static PlanningResult requireActual(RootApplicationSession actual,
            RestoreCheckpointService.RestoreBinding binding, RootInstalledCatalog catalog,
            Instant originalDeadline) throws IOException, InterruptedException {
        Objects.requireNonNull(actual); Objects.requireNonNull(binding); Objects.requireNonNull(catalog);
        Objects.requireNonNull(originalDeadline);
        DriverStateSnapshot.Slot originalGoal = binding.savedMaterial().savedDriver().campaignGoal();
        requireSavedGoal(originalGoal);
        var context = catalog.context();
        require(!actual.isRetired() && context.actions() == actual && context.adopted() == actual.driver()
                && context.writer() == actual.writer() && binding.session().equals(actual.identity()),
                "M7 ordinary PLAN requires the actual published restored Root/catalog/binding");
        actual.writer().locked(same -> {
            var origin = binding.requireReboundOrigin(same); origin.requireOriginal(same);
            require(context.requireRestoredOrigin(same) == origin
                    && origin.evidence().pair().equals(binding.savedMaterial().pair())
                    && !origin.evidence().previousOwner().game().equals(actual.identity().game()),
                    "M7 ordinary PLAN lost its actual saved-to-replacement custody");
            return null;
        });
        Planned planned = actual.withPublicPlanning(originalDeadline, (observed, same) -> {
            observed.assertCurrent(same);
            require(context.actions() == actual && context.adopted() == actual.driver()
                    && context.game().generation().equals(actual.identity().game()),
                    "M7 ordinary PLAN crossed its published physical Root");
            PlanningRequest original = RootPlanningInputsFactory.publicRequest(observed, same, originalDeadline);
            require(original.before().game().equals(actual.identity().game())
                    && original.sessionId().equals(actual.identity().sessionId())
                    && catalog.missingStages().isEmpty(),
                    "M7 ordinary PLAN is missing the restored owner or complete installed planner");
            var metadata = context.sources().optionalCurrentMetadata(same);
            var pending = catalog.definitions().finance().preparePendingFrame(context, same, original, observed);
            PlanningResult result = actual.planPublic(original);
            observed.assertCurrent(same);
            if (metadata.isPresent()) metadata.get().requireCurrent(same);
            return new Planned(original, result, pending, metadata.map(m -> m.ownerSourceEpoch()), metadata.map(m -> m.gameExecutable()));
        });
        // Identical production order: the actual opaque Gift token is consumed after the planning scope exits.
        if (planned.pending().isPresent()) planned.pending().orElseThrow().afterPlanning(planned.result());
        PlanningResult result = planned.result();
        require(result instanceof PlanningResult.ActionSelected,
                "M7 ordinary PLAN did not select a current action: " + result.getClass().getSimpleName());
        var selected = (PlanningResult.ActionSelected) result;
        require(result.trace().visits().stream().anyMatch(visit -> visit.stage() == PlanningStage.CAMPAIGN_ADVANCE_CAP),
                "M7 ordinary PLAN did not run the actual campaign stage");
        OrdinaryPolicy.Draft draft = result.trace().finalPlan().orElseThrow(
                () -> new IOException("M7 ordinary PLAN has no actual final draft"));
        require(draft.command().filter(selected.command()::equals).isPresent(),
                "M7 ordinary PLAN selected command differs from the actual final draft");
        requireConsumption(originalGoal, context.source(), planned.sourceEpoch(),
                planned.executable(), planned.request(), draft);
        return planned.result();
    }

    /** Pure assertion boundary shared with component software regressions; never a SAVE or restore issuer. */
    public static OrdinaryCampaignGoal.Goal requireSavedGoal(DriverStateSnapshot.Slot original) throws IOException {
        require(original instanceof DriverStateSnapshot.Value,
                "MISSING_ACTUAL_ORDINARY_GOAL: a retained non-null saved goal is required");
        return GoalCodec.decodeGoal(((DriverStateSnapshot.Value) original).json());
    }

    /**
     * Checks an actual campaign-policy output against the original saved intent and current source.
     * Calling this pure checker alone is not evidence of a complete Root planner or physical restore.
     */
    public static M7KernelPlanConsumer.Consumed requireConsumption(DriverStateSnapshot.Slot originalSavedGoal,
            G2Source actualSource, Optional<String> actualSourceEpoch, Optional<ExactRef> actualExecutable,
            PlanningRequest original, OrdinaryPolicy.Draft actualDraft) throws IOException {
        var retained = requireSavedGoal(originalSavedGoal);
        require(actualSource != null && actualSourceEpoch != null && actualExecutable != null,
                "MISSING_ACTUAL_M7_SOURCE: actual qualified source/epoch/executable containers are required");
        if (actualSourceEpoch.isPresent()) {
            require(actualSourceEpoch.get().matches("[0-9a-f]{64}"), "supplied source epoch must be exact hex");
        }
        if (actualExecutable.isPresent()) {
            require(actualExecutable.get().bytes() > 0, "supplied executable reference must be nonempty");
        }
        Objects.requireNonNull(original); Objects.requireNonNull(actualDraft);
        require(original.source().equals(actualSource) && original.observations().campaignGoal().filter(retained::equals).isPresent(),
                "M7 ordinary PLAN crossed its original saved goal or current source");
        var semanticGoal = original.observations().snapshot().get("campaign_goal");
        require(semanticGoal != null && semanticGoal != OpportunityJson.Nil.INSTANCE
                && OpportunityJson.parse(((DriverStateSnapshot.Value) originalSavedGoal).json()).equals(semanticGoal),
                "M7 ordinary PLAN semantic goal differs from its retained original");
        ActionCommand command = actualDraft.command().orElseThrow(
                () -> new IOException("M7 ordinary PLAN has no selected action consumption"));
        require(command.before().equals(original.before()) && command.source().equals(actualSource)
                && command.sessionId().equals(original.sessionId()),
                "M7 ordinary PLAN command crossed the current request");
        var rawPlan = actualDraft.detail().get("campaign_goal_plan_used");
        var rawConsumption = actualDraft.detail().get("m7_kernel_plan_consumption");
        require(rawPlan != null && rawConsumption != null, "M7 ordinary PLAN omitted its actual goal consumption");
        var expected = OrdinaryCampaignGoal.plan(retained);
        require(GoalCodec.decodePlan(OpportunityJson.encode(rawPlan)).equals(expected),
                "M7 ordinary PLAN changed the original goal policy");
        var consumed = M7KernelPlanConsumer.decode(OpportunityJson.encode(rawConsumption));
        var observation = consumed.observation(); var frame = original.before().frame();
        require(consumed.publication() == M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN
                && consumed.selectedStep().equals(command.operation().value())
                && consumed.campaignGoalPlanUsed().equals(expected) && observation.goal().equals(retained)
                && observation.machineId().equals(original.before().machineId())
                && observation.sourceEpoch().equals(actualSourceEpoch) && observation.executable().equals(actualExecutable)
                && observation.game().pid() == original.before().game().pid()
                && observation.game().creationFiletime().equals(original.before().game().creationFiletime().value().toString())
                && observation.snapshotId().equals(frame.snapshotId()) && observation.revision().equals(frame.revision())
                && observation.nativeRevision().equals(frame.identity().nativeRevision())
                && observation.episodeRunId().equals(frame.episodeRunId())
                && BigInteger.valueOf(observation.actorCharacterId()).equals(frame.identity().player())
                && BigInteger.valueOf(observation.dateRaw()).equals(frame.identity().dateRaw()),
                "M7 ordinary PLAN consumption crossed full saved-goal/current source/Game/frame identity");
        require(Arrays.equals(M7KernelPlanConsumer.encode(consumed),
                M7KernelPlanConsumer.encode(M7KernelPlanConsumer.decode(M7KernelPlanConsumer.encode(consumed)))),
                "M7 ordinary PLAN consumption failed persistence round-trip");
        require(!consumed.gameActionsSubmitted() && !consumed.coldAuthorityGranted()
                && !consumed.replayAuthorized() && consumed.savedDayCredit() == 0,
                "M7 PLAN data cannot grant business or restore credit");
        return consumed;
    }

    public static M7KernelPlanConsumer.Consumed requireConsumption(DriverStateSnapshot.Slot originalSavedGoal,
            G2Source actualSource, String actualSourceEpoch, ExactRef actualExecutable,
            PlanningRequest original, OrdinaryPolicy.Draft actualDraft) throws IOException {
        return requireConsumption(originalSavedGoal, actualSource, Optional.of(actualSourceEpoch), Optional.of(actualExecutable), original, actualDraft);
    }

    private static void require(boolean condition, String reason) throws IOException {
        if (!condition) throw new IOException(reason);
    }
}
