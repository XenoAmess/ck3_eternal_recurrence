package org.xar.ck3.control.application.planning.warexit;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual Driver terminal readiness, separate from tactical preference and raw hello capabilities. */
public final class WarExitCapabilities {
    public enum WhiteVariant { DEFENDER_DE_JURE, DEFENDER_MINOR_RELIGIOUS, DE_JURE_NO_SAFE_ROUTE, CLAIM }
    public enum SurrenderVariant { DE_JURE_NO_SAFE_ROUTE, RAIKTOR_TERMINAL_CONTROL, RAIKTOR_LONG_WAR, TERMINAL_SCORE }
    public enum Fence { NONE, PROPOSAL_COOLDOWN, PERMANENT_SUBMISSION, UNKNOWN_SUBMISSION }
    public record Gate(int warId, Optional<WhiteVariant> white, Optional<SurrenderVariant> surrender,
            Fence whiteFence, Fence surrenderFence) {
        public Gate { require(warId > 0, "original Driver WarID required"); Objects.requireNonNull(white);
            Objects.requireNonNull(surrender); Objects.requireNonNull(whiteFence); Objects.requireNonNull(surrenderFence); }
    }
    public record Projection(Set<OperationKey> steps, List<Gate> gates) {
        public Projection { steps = Set.copyOf(steps); gates = List.copyOf(gates); }
    }
    private static final String QUERY = "game.command.query-war-termination-options-N";
    private static final String WHITE = "game.command.offer-white-peace-N";
    private static final String SURRENDER = "game.command.surrender-war-N";
    private WarExitCapabilities() { }

    /** Ordinary path: never constructs or implicitly enables the separate historical WAR31 research gate. */
    public static Set<OperationKey> steps(OpportunityJson.Obj snapshot, List<OpportunityJson.Obj> realSurvivingHistory,
            Set<String> bridgeCaps) {
        return project(snapshot, realSurvivingHistory, bridgeCaps).steps();
    }

    public static Projection project(OpportunityJson.Obj snapshot, List<OpportunityJson.Obj> realSurvivingHistory,
            Set<String> bridgeCaps) {
        Objects.requireNonNull(snapshot); Objects.requireNonNull(realSurvivingHistory); Objects.requireNonNull(bridgeCaps);
        ObjectNode raw = WarExitEvidence.object(OpportunityJson.toNode(snapshot), "current Driver snapshot");
        if (!WarExitEvidence.trueValue(raw.get("paused"))) return new Projection(Set.of(), List.of());
        List<ObjectNode> history = effectiveAfterRestore(realSurvivingHistory);
        Set<OperationKey> steps = new HashSet<>(); List<Gate> gates = new ArrayList<>();
        String episode = org.xar.ck3.control.contracts.StrictJson.text(raw.get("episode_run_id"));
        for (WarExitEvidence.War war : WarExitEvidence.wars(raw)) {
            Optional<WarExitEvidence.Options> observed = WarExitEvidence.currentOptions(raw, war.warId());
            if (observed.isEmpty()) continue;
            WarExitEvidence.Options options = observed.orElseThrow();
            Optional<WhiteVariant> white = whiteReadiness(snapshot, war.warId());
            Optional<SurrenderVariant> surrender = surrenderReadiness(war, options);
            Fence whiteFence = fence(history, episode, war.warId(), "white_peace", white.orElse(null));
            if (whiteFence == Fence.NONE && WarExitEvidence.whitePeaceCooldown(history, raw, war.warId()).isPresent())
                whiteFence = Fence.PROPOSAL_COOLDOWN;
            Fence surrenderFence = fence(history, episode, war.warId(), "surrender", null);
            if (white.isPresent() && whiteFence == Fence.NONE && bridgeCaps.contains(QUERY) && bridgeCaps.contains(WHITE))
                steps.add(new OperationKey("offer-white-peace-" + war.warId()));
            if (surrender.isPresent() && surrenderFence == Fence.NONE && bridgeCaps.contains(QUERY) && bridgeCaps.contains(SURRENDER))
                steps.add(new OperationKey("surrender-war-" + war.warId()));
            gates.add(new Gate(war.warId(), white, surrender, whiteFence, surrenderFence));
        }
        return new Projection(steps, gates);
    }

    private static Optional<WhiteVariant> whiteReadiness(OpportunityJson.Obj actualFrame, int warId) {
        if (!(OrdinaryWhitePeacePolicy.evaluate(actualFrame, warId) instanceof OrdinaryWhitePeacePolicy.Ready ready))
            return Optional.empty();
        return Optional.of(switch (ready.variant()) {
            case DEFENDER_DE_JURE -> WhiteVariant.DEFENDER_DE_JURE;
            case DEFENDER_MINOR_RELIGIOUS -> WhiteVariant.DEFENDER_MINOR_RELIGIOUS;
            case DE_JURE_NO_SAFE_ROUTE -> WhiteVariant.DE_JURE_NO_SAFE_ROUTE;
            case CLAIM_CB -> WhiteVariant.CLAIM;
        });
    }

    private static Optional<SurrenderVariant> surrenderReadiness(WarExitEvidence.War war, WarExitEvidence.Options options) {
        if (LegacyWarExitPolicy.deJureSurrender(war, options)) return Optional.of(SurrenderVariant.DE_JURE_NO_SAFE_ROUTE);
        var surrender = options.surrender(); ObjectNode raw = options.original();
        boolean base = war.playerSide() == WarExitEvidence.Side.ATTACKER && war.primaryLeader()
                && options.playerSide() == WarExitEvidence.Side.ATTACKER && options.primaryLeader()
                && war.score().filter(value -> value == options.score()).isPresent()
                && options.cbPresent() && options.cbKey().isPresent()
                && WarExitEvidence.trueValue(raw.get("absolute_war_scores_observable"))
                && WarExitEvidence.integerIs(raw.get("attacker_war_score"), options.score())
                && WarExitEvidence.integerIs(raw.get("defender_war_score"), -(long) options.score())
                && surrender.outcome() == WarExitEvidence.Outcome.ATTACKER_DEFEAT
                && surrender.hostageVariant().equals("none") && surrender.nativeLegal()
                && surrender.autoAcceptObservable() && surrender.autoAccept().orElse(false) && surrender.finalAccepts();
        if (!base) return Optional.empty();
        boolean raiktor = options.cbKey().filter("raiktor_claim_cb"::equals).isPresent();
        if (raiktor && options.score() == -100) return Optional.of(SurrenderVariant.RAIKTOR_TERMINAL_CONTROL);
        if (raiktor && options.score() <= -1 && options.durationDays().orElse(-1) >= 730)
            return Optional.of(SurrenderVariant.RAIKTOR_LONG_WAR);
        return options.score() == -100 ? Optional.of(SurrenderVariant.TERMINAL_SCORE) : Optional.empty();
    }

    private static Fence fence(List<ObjectNode> history, String episode, int warId, String outcome, WhiteVariant variant) {
        String literal = (outcome.equals("white_peace") ? "offer-white-peace-" : "surrender-war-") + warId;
        for (int i = history.size() - 1; i >= 0; i--) {
            ObjectNode row = history.get(i);
            if (!WarExitEvidence.textIs(row.get("command"), literal)) continue;
            JsonNode result = row.get("result"); JsonNode action = result == null ? null : result.get("war_termination_result");
            if (WarExitEvidence.falseValue(row.get("ok")) && !(action instanceof ObjectNode)) continue;
            if (!(action instanceof ObjectNode value)) return Fence.UNKNOWN_SUBMISSION;
            JsonNode boundEpisode = value.get("episode_run_id");
            if (boundEpisode != null && boundEpisode.isTextual() && !episode.equals(boundEpisode.textValue())) continue;
            if (!WarExitEvidence.trueValue(row.get("ok")) || !WarExitEvidence.integerIs(value.get("war_id"), warId)
                    || !WarExitEvidence.textIs(boundEpisode, episode)
                    || !(WarExitEvidence.textIs(value.get("status"), "submitted_pending")
                        || WarExitEvidence.textIs(value.get("status"), "applied"))) return Fence.UNKNOWN_SUBMISSION;
            if (!outcome.equals("white_peace")) {
                return WarExitEvidence.textIs(value.get("outcome"), "attacker_defeat")
                        || WarExitEvidence.textIs(value.get("outcome"), "attacker_victory")
                        ? Fence.PERMANENT_SUBMISSION : Fence.UNKNOWN_SUBMISSION;
            }
            if (!WarExitEvidence.textIs(value.get("outcome"), "white_peace")) return Fence.UNKNOWN_SUBMISSION;
            JsonNode cb = value.get("casus_belli");
            if (variant == WhiteVariant.DE_JURE_NO_SAFE_ROUTE && cb instanceof ObjectNode
                    && WarExitEvidence.textIs(cb.get("canonical_key"), "individual_county_de_jure_cb")
                    && WarExitEvidence.integerIs(cb.get("database_index"), 17)) return Fence.PERMANENT_SUBMISSION;
            // The shared 30-day cooldown below handles ordinary known applied/pending proposals.
            return Fence.NONE;
        }
        return Fence.NONE;
    }

    private static List<ObjectNode> effectiveAfterRestore(List<OpportunityJson.Obj> surviving) {
        List<ObjectNode> rows = new ArrayList<>();
        for (OpportunityJson.Obj value : surviving) {
            Optional<String> command = OrdinaryHistory.effectiveCommand(value);
            if (command.filter("restore-checkpoint"::equals).isPresent() && OrdinaryHistory.successful(value)) { rows.clear(); continue; }
            ObjectNode row = WarExitEvidence.object(OpportunityJson.toNode(value), "surviving Driver history").deepCopy();
            if (command.isPresent()) row.put("command", command.orElseThrow()); else row.putNull("command");
            Optional<OpportunityJson.Obj> result = OrdinaryHistory.effectiveCommandResult(value);
            if (result.isPresent()) row.set("result", OpportunityJson.toNode(result.orElseThrow())); else row.putNull("result");
            rows.add(row);
        }
        return List.copyOf(rows);
    }
}

