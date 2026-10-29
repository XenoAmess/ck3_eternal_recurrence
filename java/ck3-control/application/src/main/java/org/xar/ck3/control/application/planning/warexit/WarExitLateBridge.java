package org.xar.ck3.control.application.planning.warexit;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult.StopReason;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Late WarCore call positions consume the original history latch, never resubmit a terminal. */
public final class WarExitLateBridge {
    private static final long RESPONSE_WINDOW_RAW = 10L * 24;
    enum ResponseWindow { NONE, ADVANCE_ONE_DAY, UNRESOLVED }
    private WarExitLateBridge() { }

    /** strategy.py:7293-7371; called at 13178/13790 before route-boundary exit selection. */
    public static OrdinaryPolicy.Decision lateResponse(PlanningRequest request, OrdinaryPolicy.Draft previous,
            int tacticalWarId, List<OpportunityJson.Obj> routeRejections) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        require(tacticalWarId > 0, "actual original tactical WarID required");
        List<OpportunityJson.Obj> retainedRejections = List.copyOf(routeRejections);
        ObjectNode snapshot = WarExitEvidence.snapshot(request);
        Optional<WarExitEvidence.War> war = WarExitEvidence.wars(snapshot).stream()
                .filter(value -> value.warId() == tacticalWarId).findFirst();
        if (war.isEmpty()) return new OrdinaryPolicy.Keep("old WarID is absent; no late white-peace response action");
        Optional<WarExitEvidence.Cooldown> submission = WarExitEvidence.whitePeaceCooldown(
                WarExitEvidence.effectiveHistorySinceRestore(request), snapshot, tacticalWarId);
        ResponseWindow response = responseWindow(submission);
        if (response == ResponseWindow.NONE)
            return new OrdinaryPolicy.Keep("no pending white-peace proposal inside the original response branch");
        if (response == ResponseWindow.UNRESOLVED)
            return new OrdinaryPolicy.Stop(StopReason.UNKNOWN_ACTION_UNRESOLVED,
                    "the native white-peace reply observation window elapsed with the old WarID present; never repeat the terminal");
        if (!request.observations().paused())
            return new OrdinaryPolicy.Stop(StopReason.INVALID_FRAME, "late response advance requires the actual paused frame");
        WarExitEvidence.Cooldown pending = submission.orElseThrow();
        OpportunityJson.Obj detail = previous.detail()
                .with("route_rejections", new OpportunityJson.Arr(retainedRejections.stream()
                        .map(value -> (OpportunityJson.Value) value).toList()))
                .with("response_observation_deadline_raw", new OpportunityJson.IntegerValue(
                        BigInteger.valueOf(pending.submittedDateRaw().orElseThrow()).add(BigInteger.valueOf(RESPONSE_WINDOW_RAW))));
        OrdinaryPolicy.Draft annotated = new OrdinaryPolicy.Draft(previous.policy(), previous.phase(), previous.reason(),
                previous.kind(), previous.command(), previous.purpose(), previous.domain(), detail);
        return WarExitPolicies.responseAdvance(request, annotated, war.orElseThrow(),
                "native_war_white_peace_response_window_advance", "white_peace", pending.source());
    }

    /** The exact three original predicates used by the defender-hold admission caller at 16860. */
    public static boolean authorizedExitCandidate(PlanningRequest request, int warId) {
        Objects.requireNonNull(request); require(warId > 0, "original tactical WarID required");
        if (!request.observations().paused()) return false;
        ObjectNode snapshot = WarExitEvidence.snapshot(request);
        Optional<WarExitEvidence.War> war = WarExitEvidence.wars(snapshot).stream()
                .filter(value -> value.warId() == warId).findFirst();
        Optional<WarExitEvidence.Options> options = WarExitEvidence.currentOptions(snapshot, warId);
        return war.isPresent() && options.isPresent()
                && (WarExitPolicies.claimTermsReady(request.observations().snapshot(), warId)
                    || LegacyWarExitPolicy.deJureWhitePeace(request.observations().snapshot(), warId)
                    || LegacyWarExitPolicy.deJureSurrender(war.orElseThrow(), options.orElseThrow()));
    }

    static ResponseWindow responseWindow(Optional<WarExitEvidence.Cooldown> submission) {
        Objects.requireNonNull(submission);
        if (submission.isEmpty()) return ResponseWindow.NONE;
        WarExitEvidence.Cooldown pending = submission.orElseThrow();
        if (!pending.status().equals("cooldown") || !pending.actionStatus().equals("submitted_pending")
                || pending.elapsedRaw().isEmpty() || pending.elapsedRaw().orElseThrow() < 0)
            return ResponseWindow.NONE;
        return pending.elapsedRaw().orElseThrow() < RESPONSE_WINDOW_RAW
                ? ResponseWindow.ADVANCE_ONE_DAY : ResponseWindow.UNRESOLVED;
    }
}

