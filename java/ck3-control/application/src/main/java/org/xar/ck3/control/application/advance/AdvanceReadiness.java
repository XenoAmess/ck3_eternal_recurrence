package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Source-bound live feature/history facts are supplied by the existing production assembler, never defaulted. */
public final class AdvanceReadiness {
    private AdvanceReadiness() { }
    @FunctionalInterface public interface Port { Facts inspect(ActionCommand parent, AdvanceObservationPort.Frame frame); }
    public record Facts(ObservationIdentity observed, Set<OperationKey> actionSteps, Set<String> bridgeCapabilities,
            boolean openAssaultLifecycle, boolean unobservableStartedAssault, boolean unresolvedWarDailyWatch,
            int crownRetryMaximumDays, ExactRef originalHistoryEvidence,
            Optional<WarDailyWatch.Context> dailyWatch, boolean readerUnavailableSpeedFiveReady) {
        public Facts {
            Objects.requireNonNull(observed); actionSteps = Set.copyOf(actionSteps); bridgeCapabilities = Set.copyOf(bridgeCapabilities);
            require(crownRetryMaximumDays >= 1 && crownRetryMaximumDays <= 45, "actual bounded crown retry horizon required");
            Objects.requireNonNull(originalHistoryEvidence); require(originalHistoryEvidence.bytes() > 0, "actual history/feature source evidence required");
            Objects.requireNonNull(dailyWatch); dailyWatch.ifPresent(watch -> require(watch.starting().equals(observed), "watch selection crossed its actual full frame"));
        }
        public Facts(ObservationIdentity observed, Set<OperationKey> actionSteps, Set<String> bridgeCapabilities,
                boolean openAssaultLifecycle, boolean unobservableStartedAssault, boolean unresolvedWarDailyWatch,
                int crownRetryMaximumDays, ExactRef originalHistoryEvidence) {
            this(observed,actionSteps,bridgeCapabilities,openAssaultLifecycle,unobservableStartedAssault,unresolvedWarDailyWatch,
                    crownRetryMaximumDays,originalHistoryEvidence,Optional.empty(),false);
        }
    }
    public static boolean h3937(Obj frame) {
        if (!new Text("native-29829-2bc2d599f7f9").equals(frame.get("episode_run_id"))) return false;
        boolean ordinary = frame.get("succession_lifecycle") instanceof Obj lifecycle
                && new Text("ordinary_campaign_succession").equals(lifecycle.get("lifecycle"))
                && frame.get("campaign_goal") instanceof Obj goal
                && new IntegerValue(BigInteger.ONE).equals(goal.get("format_version"))
                && new Text("dynasty_continuity").equals(goal.get("goal_key"))
                && Objects.equals(goal.get("campaign_id"), frame.get("episode_run_id"))
                && frame.get("played_character") instanceof Obj played
                && Objects.equals(goal.get("current_character_id"), played.get("character_id"));
        return !ordinary;
    }
    public static void verify(ActionCommand parent, AdvanceObservationPort.Frame frame, AdvancePlan plan, Facts facts) {
        require(facts.observed().equals(frame.identity()), "timeline history/capability facts are not for the actual current frame");
        require(!h3937(frame.semantic()), "H3937 native date hold remains active");
        require(AdvancePolicy.truth(frame.semantic(), "map_ready"), "life advance requires actual map_ready");
        require(!plan.exactOneDay() || AdvancePolicy.truth(frame.semantic(), "paused"), "exact day requires actual paused frame");
        require(!facts.openAssaultLifecycle() || AdvancePolicy.truth(frame.semantic(), "paused"), "open assault requires a paused rich same-SiegeID snapshot");
        require(!facts.unobservableStartedAssault(), "unobservable assault_started lifecycle cannot authorize resume");
        require(!facts.unresolvedWarDailyWatch(), "previous war daily watch is unresolved; replay forbidden");
        require(plan.horizonDays() <= facts.crownRetryMaximumDays(), "plan failed to consume the actual crown authority retry horizon");
        require(facts.actionSteps().contains(new OperationKey("set-speed-" + plan.speed()))
                && facts.actionSteps().contains(new OperationKey("resume-map")) && facts.actionSteps().contains(new OperationKey("pause-map")), "actual speed/resume/pause native capability absent");
        require(plan.clockMode() == AdvancePlan.ClockMode.POLLED || ClockStatusRead.available(facts.bridgeCapabilities()), "native exact/campaign clock capability absent");
        if (plan.dailyWatch().isPresent()) require(plan.dailyWatch().equals(facts.dailyWatch()) && plan.dailyWatch().orElseThrow().starting().equals(parent.before()),
                "watch plan must consume the exact real enabled roster/owner selection");
        if (ReaderUnavailableSpeed.POLICY.equals(plan.policy())) require(facts.readerUnavailableSpeedFiveReady() && plan.exactOneDay()
                && plan.speed() == 5 && plan.clockMode() == AdvancePlan.ClockMode.EXACT_SENTINEL, "fast hands-off watch lost its real failed-read lineage or native exact clock");
        require(parent.before().game().equals(frame.identity().game()) && parent.source().equals(frame.source()) && parent.sessionId().equals(frame.sessionId())
                && parent.before().frame().episodeRunId().equals(frame.identity().frame().episodeRunId())
                && frame.identity().frame().revision().compareTo(parent.before().frame().revision()) >= 0
                && frame.identity().frame().identity().nativeRevision().compareTo(parent.before().frame().identity().nativeRevision()) >= 0,
                "entry frame left original Game/session/episode/source or regressed");
    }
}
