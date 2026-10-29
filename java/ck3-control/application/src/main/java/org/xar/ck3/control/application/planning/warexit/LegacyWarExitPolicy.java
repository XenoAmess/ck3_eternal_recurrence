package org.xar.ck3.control.application.planning.warexit;

import static org.xar.ck3.control.application.planning.warexit.WarExitEvidence.integerIs;
import static org.xar.ck3.control.application.planning.warexit.WarExitEvidence.textIs;
import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryWarClaims;
import org.xar.ck3.control.application.planning.PlanningResult.StopReason;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence.Option;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence.Options;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence.Outcome;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence.Side;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence.War;

/** The original route-boundary exit choices. The tactical caller alone reaches these exact positions. */
public final class LegacyWarExitPolicy {
    public enum Position {
        OBJECTIVES_EXHAUSTED_BEFORE_CAPITAL_REGROUP,
        DEFENSIVE_HOLD_EXHAUSTED,
        ACTIVE_ROUTE_UNSAFE_WITHOUT_PREVIEW_TARGET
    }

    /** This is an internal call-boundary value, never decoded from a boolean in a native or test packet. */
    public record TacticalBoundary(Position position, int tacticalWarId, List<OpportunityJson.Obj> routeRejections) {
        public TacticalBoundary {
            Objects.requireNonNull(position); require(tacticalWarId > 0, "actual tactical WarID required");
            routeRejections = List.copyOf(routeRejections);
        }
    }
    private LegacyWarExitPolicy() { }

    /** Original early core 9114-9237: enforce first, then stable full-WarID terminal defeat priority. */
    public static OrdinaryPolicy.Decision evaluateScoreThresholds(PlanningRequest request, OrdinaryPolicy.Draft previous) {
        ObjectNode snapshot = WarExitEvidence.snapshot(request); List<War> wars = WarExitEvidence.wars(snapshot);
        List<ObjectNode> history = WarExitEvidence.effectiveHistorySinceRestore(request);
        for (War war : wars) {
            OperationKey step = new OperationKey("enforce-demands-" + war.warId());
            boolean leadershipUnknown = war.original().get("player_is_primary_war_leader") == null
                    || war.original().get("player_is_primary_war_leader").isNull();
            if (war.score().orElse(Integer.MIN_VALUE) >= 100
                    && (war.primaryLeader() || leadershipUnknown && request.observations().actionSteps().contains(step))) {
                if (!request.observations().actionSteps().contains(step))
                    return new OrdinaryPolicy.Stop(StopReason.UNSUPPORTED_ACTION, "the war reached 100 but enforce demands is not registered");
                return threshold(request, previous, war, "player_victory", "native_war_enforce_demands",
                        "the native war reached 100; enforce demands before more army orders");
            }
        }
        for (War war : wars.stream().sorted(java.util.Comparator.comparingInt(War::warId)).toList()) {
            if (WarExitEvidence.surrenderState(history, snapshot, war.warId()).isPresent()) continue;
            if (WarExitEvidence.whitePeaceCooldown(history, snapshot, war.warId())
                    .filter(value -> value.status().equals("cooldown")).isPresent()) continue;
            Optional<Options> read = WarExitEvidence.currentOptions(snapshot, war.warId());
            if (read.isEmpty()) continue;
            Options options = read.orElseThrow(); Option surrender = options.surrender(); ObjectNode raw = options.original();
            if (request.observations().paused() && attackerIdentity(war, options) && war.score().orElse(0) == -100
                    && WarExitEvidence.trueValue(raw.get("absolute_war_scores_observable"))
                    && integerIs(raw.get("attacker_war_score"), -100) && integerIs(raw.get("defender_war_score"), 100)
                    && options.cbPresent() && options.cbKey().isPresent() && surrender.outcome() == Outcome.ATTACKER_DEFEAT
                    && surrender.hostageVariant().equals("none") && surrender.nativeLegal()
                    && surrender.autoAcceptObservable() && surrender.autoAccept().orElse(false) && surrender.finalAccepts()) {
                Optional<OrdinaryPolicy.Decision> fenced = historyDecision(request, war.warId(), "surrender");
                if (fenced.isPresent()) return fenced.orElseThrow();
                String literal = "surrender-war-" + war.warId();
                if (!request.observations().actionSteps().contains(new OperationKey(literal)))
                    return new OrdinaryPolicy.Stop(StopReason.UNSUPPORTED_ACTION, "terminal -100 surrender is not registered: " + literal);
                return threshold(request, previous, war, "surrender", "native_war_terminal_score_surrender",
                        "the same-frame native row proves terminal defeat and accepted surrender before automatic WarID removal");
            }
        }
        return new OrdinaryPolicy.Keep("no original score threshold selected; continue the original core sequence");
    }

    private static OrdinaryPolicy.Decision threshold(PlanningRequest request, OrdinaryPolicy.Draft previous, War war,
            String outcome, String phase, String reason) {
        ActionCommand command = terminalCommand(request, war, outcome, Optional.empty());
        OpportunityJson.Obj detail = previous.detail().with("war_id", number(war.warId()))
                .with("selected_step", new OpportunityJson.Text(command.operation().value()))
                .with("requested_outcome", new OpportunityJson.Text(outcome));
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("one-life-turn-v1", phase, reason,
                OrdinaryPolicy.Kind.WAR_EXIT, Optional.of(command), OrdinaryPolicy.Purpose.WORLD_ACTION,
                Optional.of(Domain.war), detail), reason);
    }

    /** Call at strategy.py13201,13720,13813/13827 positions, retaining intervening regroup/hold priorities. */
    public static OrdinaryPolicy.Decision atBoundary(PlanningRequest request, TacticalBoundary boundary,
                                                     OrdinaryPolicy.Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(boundary); Objects.requireNonNull(previous);
        if (!request.observations().paused()) return new OrdinaryPolicy.Keep("terminal selection requires the original paused frame");
        ObjectNode snapshot = WarExitEvidence.snapshot(request);
        List<War> wars = WarExitEvidence.wars(snapshot);
        List<ObjectNode> history = WarExitEvidence.effectiveHistorySinceRestore(request);
        if (boundary.position() != Position.DEFENSIVE_HOLD_EXHAUSTED) {
            for (War war : wars) {
                Optional<Options> read = WarExitEvidence.currentOptions(snapshot, war.warId());
                if (read.isEmpty()) continue;
                Options options = read.orElseThrow();
                boolean white = deJureWhitePeace(request.observations().snapshot(), war.warId());
                boolean surrender = deJureSurrender(war, options);
                if (white || surrender) {
                    // The old route helper chooses white peace first in each original ordered war row.
                    return selected(request, previous, war, white ? "white_peace" : "surrender",
                            white ? "native_war_de_jure_no_safe_route_white_peace" : "native_war_de_jure_no_safe_route_surrender",
                            white ? "de-jure-no-safe-route-terminal-choice-v1" : "de-jure-no-safe-route-emergency-exit-v1",
                            boundary, options);
                }
            }
        }
        if (boundary.position() != Position.OBJECTIVES_EXHAUSTED_BEFORE_CAPITAL_REGROUP) {
            Optional<War> selectedWar = wars.stream().filter(war -> war.warId() == boundary.tacticalWarId()).findFirst();
            if (selectedWar.isPresent()) {
                War war = selectedWar.orElseThrow();
                if (WarExitEvidence.whitePeaceCooldown(history, snapshot, war.warId()).isPresent())
                    return new OrdinaryPolicy.Keep("preserve the original response-window/cooldown branch; do not submit another proposal");
                Optional<Options> options = WarExitEvidence.currentOptions(snapshot, war.warId());
                if (options.isPresent() && defenderProposal(request.observations().snapshot(), war.warId())) {
                    return selected(request, previous, war, "white_peace", "native_war_defender_no_safe_route_white_peace",
                            "defender-no-safe-route-white-peace-proposal-v1", boundary, options.orElseThrow());
                }
            }
        }
        return new OrdinaryPolicy.Keep("no source-bound original exit predicate selected; preserve tactical continuation order");
    }

    public static boolean deJureWhitePeace(OpportunityJson.Obj actualFrame, int warId) {
        return OrdinaryWhitePeacePolicy.evaluate(actualFrame, warId) instanceof OrdinaryWhitePeacePolicy.Ready ready
                && ready.variant() == OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE;
    }

    public static boolean deJureSurrender(War war, Options options) {
        Option surrender = options.surrender();
        return attackerIdentity(war, options) && war.score().isPresent() && war.score().orElseThrow() <= -1
                && options.durationDays().orElse(-1) >= 180 && options.cbPresent()
                && options.cbKey().filter("individual_county_de_jure_cb"::equals).isPresent()
                && surrender.outcome() == Outcome.ATTACKER_DEFEAT && surrender.hostageVariant().equals("none")
                && surrender.nativeLegal() && surrender.autoAcceptObservable() && surrender.autoAccept().orElse(false)
                && surrender.finalAccepts();
    }

    /** A legal positive-quote proposal needs no projected final response; it is not accepted peace. */
    public static boolean defenderProposal(OpportunityJson.Obj actualFrame, int warId) {
        return OrdinaryWhitePeacePolicy.evaluate(actualFrame, warId) instanceof OrdinaryWhitePeacePolicy.Ready ready
                && (ready.variant() == OrdinaryWhitePeacePolicy.Variant.DEFENDER_DE_JURE
                    || ready.variant() == OrdinaryWhitePeacePolicy.Variant.DEFENDER_MINOR_RELIGIOUS);
    }

    private static boolean attackerIdentity(War war, Options options) {
        return war.warId() == options.warId() && war.playerSide() == Side.ATTACKER && war.primaryLeader()
                && options.playerSide() == Side.ATTACKER && options.primaryLeader()
                && war.score().filter(value -> value == options.score()).isPresent();
    }

    /** Consume the Driver's same typed no-replay gate before classifying an absent terminal literal. */
    private static Optional<OrdinaryPolicy.Decision> historyDecision(PlanningRequest request, int warId, String outcome) {
        require(Set.of("white_peace", "surrender").contains(outcome), "historical terminal outcome required");
        WarExitCapabilities.Fence fence = WarExitCapabilities.project(request.observations().snapshot(),
                OrdinaryHistory.collect(request.observations().history()).rows(), request.observations().bridgeCapabilities())
                .gates().stream().filter(gate -> gate.warId() == warId)
                .map(gate -> outcome.equals("white_peace") ? gate.whiteFence() : gate.surrenderFence())
                .findFirst().orElse(WarExitCapabilities.Fence.NONE);
        if (fence == WarExitCapabilities.Fence.UNKNOWN_SUBMISSION)
            return Optional.of(new OrdinaryPolicy.Stop(StopReason.UNKNOWN_ACTION_UNRESOLVED,
                    "the same-WarID terminal has unknown submission evidence; preserve the Driver no-replay fence"));
        if (fence != WarExitCapabilities.Fence.NONE)
            return Optional.of(new OrdinaryPolicy.Keep(
                    "the Driver intentionally withheld this terminal after its known prior submission; continue ordinary tactics without resubmitting"));
        return Optional.empty();
    }

    private static OrdinaryPolicy.Decision selected(PlanningRequest request, OrdinaryPolicy.Draft previous, War war,
            String outcome, String phase, String policy, TacticalBoundary boundary, Options options) {
        String step = outcome.equals("white_peace") ? "offer-white-peace-" + war.warId() : "surrender-war-" + war.warId();
        String capability = outcome.equals("white_peace") ? "game.command.offer-white-peace-N" : "game.command.surrender-war-N";
        Optional<OrdinaryPolicy.Decision> fenced = historyDecision(request, war.warId(), outcome);
        if (fenced.isPresent()) return fenced.orElseThrow();
        if (!request.observations().actionSteps().contains(new OperationKey(step))
                || !request.observations().bridgeCapabilities().contains(capability))
            return new OrdinaryPolicy.Stop(StopReason.UNSUPPORTED_ACTION, "the selected original same-frame terminal is not registered: " + step);
        ActionCommand command = terminalCommand(request, war, outcome, Optional.empty());
        OpportunityJson.Obj detail = previous.detail()
                .with("selected_step", new OpportunityJson.Text(step)).with("war_id", number(war.warId()))
                .with("route_rejections", new OpportunityJson.Arr(boundary.routeRejections().stream()
                        .map(value -> (OpportunityJson.Value) value).toList()))
                .with("terminal_source_options", (OpportunityJson.Obj) OpportunityJson.parse(
                        org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec.encodeWire(options.original())))
                .with("terminal_boundary", new OpportunityJson.Text(boundary.position().name()))
                .with("requested_outcome", new OpportunityJson.Text(outcome))
                .with("peace_accepted", new OpportunityJson.Bool(false));
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(policy, phase,
                "select the existing native-legal terminal at its original tactical boundary; await independent outcome",
                OrdinaryPolicy.Kind.WAR_EXIT, Optional.of(command), OrdinaryPolicy.Purpose.WORLD_ACTION,
                Optional.of(Domain.war), detail), "one original same-frame war exit proposal selected");
    }

    /** Creates a proposal for the sole application writer; no submitter or ledger is called here. */
    public static ActionCommand terminalCommand(PlanningRequest request, War war, String outcome,
                                                 Optional<OpportunityJson.Obj> frozenPostconditionPlan) {
        require(Set.of("white_peace", "surrender", "player_victory").contains(outcome), "typed terminal outcome required");
        String step = switch (outcome) { case "white_peace" -> "offer-white-peace-"; case "surrender" -> "surrender-war-";
            default -> "enforce-demands-"; } + war.warId();
        ExpectedPostcondition expected = new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,
                request.before(), request.source(), OrdinaryWarExitObservation.SCHEMA,
                List.of(new ExpectedInteger(new FieldKey("war_id"), BigInteger.valueOf(war.warId())),
                        new ExpectedBoolean(new FieldKey("war_absence_observed"), true)));
        OpportunityJson.Obj arguments = new OpportunityJson.Obj(Map.of("war_id", number(war.warId()),
                "requested_outcome", new OpportunityJson.Text(outcome), "postcondition_plan",
                frozenPostconditionPlan.<OpportunityJson.Value>map(value -> value).orElse(OpportunityJson.Nil.INSTANCE)));
        Claims claims = ArmyOrdinaryWarClaims.of(request.before().frame().identity().player(), BigInteger.valueOf(war.warId()),
                war.opponent().filter(value -> value > 0).map(BigInteger::valueOf));
        String identity = request.before().machineId() + "|" + request.before().game() + "|"
                + request.before().frame().snapshotId() + "|" + request.before().frame().revision() + "|"
                + request.before().frame().episodeRunId() + "|" + step;
        return new ActionCommand("war-exit:" + digest(identity), request.before(), request.source(), request.sessionId(),
                new OperationKey(step), arguments, expected, claims, request.deadline());
    }

    private static OpportunityJson.IntegerValue number(long value) { return new OpportunityJson.IntegerValue(BigInteger.valueOf(value)); }
    private static String digest(String value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}

