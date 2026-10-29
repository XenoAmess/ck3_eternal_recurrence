package org.xar.ck3.control.application.planning;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/**
 * The original strategy._plan_one_life_terminal_v1 DATA producer.
 * Selecting a displayed step here creates no command, terminal lease, receipt or action permission.
 * The public owner supplies the actual held full snapshot/history and the sole current capability inventory.
 */
public final class OriginalTerminalPlanning {
    private OriginalTerminalPlanning() { }
    private static final OperationKey DEATH = new OperationKey("death-terminal");
    private static final OperationKey NEXT = new OperationKey("start-next-episode");
    private static final OperationKey CONTINUE = new OperationKey("continue-as-reconciled-successor");
    private static final String POLICY = "one-life-turn-v1";
    private static final String SCHEMA = "xar.ck3.succession-lifecycle-binding/v1";
    private static final String SETTLEMENT = "game.state.xar-one-life-settlement";

    /** DATA only. Constructing this value cannot authenticate the supplied snapshot or issue a capability. */
    public record Input(Obj snapshot, List<Obj> history, Set<OperationKey> actionSteps,
            Set<String> bridgeCapabilities, Optional<Goal> campaignGoal, Optional<Obj> crossRunPlan) {
        public Input {
            Objects.requireNonNull(snapshot); history = List.copyOf(history); actionSteps = Set.copyOf(actionSteps);
            bridgeCapabilities = Set.copyOf(bridgeCapabilities); Objects.requireNonNull(campaignGoal); Objects.requireNonNull(crossRunPlan);
            bridgeCapabilities.forEach(StrictJson::text);
            DriverJson.object(DriverJson.encode(snapshot), DriverJson.MAX_NATIVE_BYTES);
        }
    }
    private record Continuation(boolean ready, boolean red, boolean pending) { }

    public static boolean terminalFrame(Obj snapshot) {
        Objects.requireNonNull(snapshot);
        Value reason = snapshot.get("one_life_terminal_reason");
        Value player = snapshot.get("played_character");
        return reason instanceof Text || player instanceof Obj actor && new Bool(false).equals(actor.get("alive"));
    }

    /** The terminal function itself, before service.plan_from_view's real campaign/cross-run annotations. */
    public static Optional<Obj> terminal(Input input) {
        Objects.requireNonNull(input); Obj snapshot = input.snapshot();
        Value rawPlayer = snapshot.get("played_character");
        Obj player = rawPlayer instanceof Obj object ? object : null;
        Value explicit = snapshot.get("one_life_terminal_reason");
        String reason = explicit instanceof Text text ? text.value()
                : player != null && new Bool(false).equals(player.get("alive")) ? "played_character_dead" : null;
        if (reason == null) return Optional.empty();
        Value episode = optional(snapshot, "episode_character_id");
        if (episode != Nil.INSTANCE) StrictJson.require(episode instanceof IntegerValue, "terminal episode actor must retain its JSON integer role");
        Lifecycle lifecycle = lifecycle(snapshot.get("succession_lifecycle"));
        Obj binding = OpportunityJson.object(DriverJson.fromNode(lifecycle.toJson()), "normalized original lifecycle");
        Continuation continuation = continuation(snapshot, reason, input.actionSteps());
        if (lifecycle.lifecycle().equals("unknown")) {
            Obj plan = base("terminal_succession_lifecycle_unbound", Optional.empty(),
                    "the terminal frame has no valid frozen succession lifecycle binding", reason, episode, binding)
                    .with("continue_as_heir_after_death", new Bool(false)).with("heir_gameplay_actions", number(0));
            return Optional.of(plan);
        }
        if (lifecycle.lifecycle().equals("ordinary_campaign_succession")) {
            String phase = continuation.red() ? "ordinary_successor_reconciliation_red"
                    : continuation.pending() ? "ordinary_successor_reconciliation_pending"
                    : continuation.ready() ? "ordinary_successor_continuation_ready" : "ordinary_campaign_terminal_no_successor";
            String detail = continuation.ready()
                    ? "the ordinary campaign can continue on CK3's reconciled played successor without a rogue settlement"
                    : continuation.red() ? "the observed successor or inherited predecessor estate disagrees with the retained expectation"
                    : continuation.pending() ? "the played successor still requires a matched predecessor-estate reconciliation"
                    : "the ordinary campaign has no playable successor";
            return Optional.of(base(phase, continuation.ready() ? Optional.of(CONTINUE) : Optional.empty(),
                    detail, reason, episode, binding).with("settlement_required", new Bool(false))
                    .with("continue_as_heir_after_death", new Bool(continuation.ready())).with("heir_gameplay_actions", number(0)));
        }
        Obj completed = latestEffectiveTerminal(input.history()).orElse(null);
        if (completed != null && new Bool(true).equals(completed.get("terminal"))
                && optional(completed, "score") != Nil.INSTANCE
                && (optional(completed, "settlement_status") == Nil.INSTANCE
                    || new Text("complete").equals(completed.get("settlement_status")))) {
            String phase = continuation.red() ? "terminal_succession_reconciliation_red"
                    : continuation.pending() ? "terminal_successor_reconciliation_pending" : "terminal_complete";
            Optional<OperationKey> step = continuation.ready() ? Optional.of(CONTINUE)
                    : !reason.equals("played_character_changed") && input.actionSteps().contains(NEXT) ? Optional.of(NEXT) : Optional.empty();
            String detail = continuation.ready() ? "the completed life can continue on CK3's reconciled played successor"
                    : continuation.red() ? "the observed successor or inherited predecessor estate disagrees with the retained expectation"
                    : continuation.pending() ? "the played successor still requires a matched predecessor-estate reconciliation"
                    : "this one-life episode is already settled";
            return Optional.of(base(phase, step, detail, reason, episode, binding)
                    .with("score", completed.get("score")).with("continue_as_heir_after_death", new Bool(continuation.ready()))
                    .with("heir_gameplay_actions", number(0)));
        }
        if (completed != null && new Text("settlement_unavailable").equals(completed.get("settlement_status"))
                && new Text("settlement_unavailable").equals(snapshot.get("one_life_settlement_status"))) {
            return Optional.of(base("terminal_settlement_unavailable", Optional.empty(),
                    "the episode is terminal but this bridge cannot publish its score; wait for a settlement-capable backend",
                    reason, episode, binding).with("required_capability", new Text(SETTLEMENT))
                    .with("continue_as_heir_after_death", new Bool(false)).with("heir_gameplay_actions", number(0)));
        }
        Value retainedPlayer = player == null ? Nil.INSTANCE : player;
        if (input.actionSteps().contains(DEATH)) {
            String detail = reason.equals("played_character_changed")
                    ? "CK3 changed the played CharacterID after the episode character; end this one-life episode instead of continuing as the heir"
                    : "the native played character is dead; end this one-life episode";
            return Optional.of(base("terminal_native", Optional.of(DEATH), detail, reason, episode, binding)
                    .with("played_character", retainedPlayer));
        }
        return Optional.of(base("terminal_native_unsupported", Optional.empty(),
                "the backend cannot finalize the detected player death", reason, episode, binding)
                .with("required_step", new Text(DEATH.value())).with("played_character", retainedPlayer));
    }

    /** Same service boundary: campaign goal has priority; a real cross-run plan is added only when supplied. */
    public static Optional<Obj> plan(Input actual) {
        return terminal(actual).map(plan -> {
            if (actual.campaignGoal().isPresent())
                return plan.with("campaign_goal_plan_used", DriverJson.object(
                        GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(actual.campaignGoal().orElseThrow())), DriverJson.MAX_NATIVE_BYTES));
            return actual.crossRunPlan().map(value -> plan.with("cross_run_plan_used", value)).orElse(plan);
        });
    }

    private static Continuation continuation(Obj snapshot, String reason, Set<OperationKey> steps) {
        Obj reconciliation = snapshot.get("succession_reconciliation") instanceof Obj value ? value : null;
        boolean changed = reason.equals("played_character_changed");
        boolean available = reconciliation != null && new Text("available").equals(reconciliation.get("status"));
        boolean ready = changed && available && new Text("matched").equals(reconciliation.get("verdict"))
                && new Bool(true).equals(reconciliation.get("successor_match"))
                && new Bool(true).equals(reconciliation.get("title_distribution_match")) && steps.contains(CONTINUE);
        boolean red = changed && available && !new Text("matched").equals(reconciliation.get("verdict"));
        return new Continuation(ready, red, changed && !ready && !red);
    }
    private static Optional<Obj> latestEffectiveTerminal(List<Obj> history) {
        var rows = OrdinaryHistory.collect(history).rows();
        for (int index = rows.size() - 1; index >= 0; index--) {
            Obj row = rows.get(index);
            if (OrdinaryHistory.successful(row)
                    && OrdinaryHistory.effectiveCommand(row).filter(DEATH.value()::equals).isPresent())
                return OrdinaryHistory.effectiveCommandResult(row);
        }
        return Optional.empty();
    }
    /** Reuse the shared complete lifecycle contract; malformed original bindings become its explicit unknown value. */
    private static Lifecycle lifecycle(Value original) {
        if (original == null || original == Nil.INSTANCE)
            return new Lifecycle("rogue_one_life", Optional.of("xar_on"), "terminal_settlement_required",
                    "legacy-driver-default", Optional.empty());
        try {
            StrictJson.require(original instanceof Obj, "lifecycle object required"); Obj value = (Obj) original;
            StrictJson.require(value.members().keySet().equals(Set.of("schema", "lifecycle", "xar_enabled",
                    "pact_contract", "source", "environment_sha256")), "complete lifecycle fields required");
            StrictJson.require(new Text(SCHEMA).equals(value.get("schema")), "original lifecycle schema required");
            return new Lifecycle(text(value.get("lifecycle"), "lifecycle"), nullableText(value.get("xar_enabled"), "xar_enabled"),
                    text(value.get("pact_contract"), "pact_contract"), text(value.get("source"), "source"),
                    nullableText(value.get("environment_sha256"), "environment_sha256"));
        } catch (IllegalArgumentException malformed) {
            return new Lifecycle("unknown", Optional.empty(), "unknown", "unbound", Optional.empty());
        }
    }
    private static Obj base(String phase, Optional<OperationKey> selected, String detail, String reason, Value episode, Obj lifecycle) {
        var fields = new LinkedHashMap<String, Value>();
        fields.put("policy", new Text(POLICY)); fields.put("phase", new Text(phase));
        fields.put("selected_step", selected.<Value>map(value -> new Text(value.value())).orElse(Nil.INSTANCE));
        fields.put("reason", new Text(detail)); fields.put("terminal_reason", new Text(reason));
        fields.put("episode_character_id", episode); fields.put("succession_lifecycle", lifecycle);
        return new Obj(fields);
    }
    private static IntegerValue number(long value) { return new IntegerValue(java.math.BigInteger.valueOf(value)); }
    private static Value optional(Obj value, String field) { return value.members().containsKey(field) ? value.get(field) : Nil.INSTANCE; }
    private static String text(Value value, String field) { return OpportunityJson.text(value, field); }
    private static Optional<String> nullableText(Value value, String field) {
        return value == Nil.INSTANCE ? Optional.empty() : Optional.of(text(value, field));
    }
}
