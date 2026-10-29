package org.xar.ck3.control.application.battleadvance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;

/** Durable versioned plan from the original paused frame. Typed targets must already have campaign normalization. */
public record BattleAdvancePlan(String step, int startingDateRaw, int targetDateRaw, int speed, Mode mode,
        BattleAdvanceStep.Scope scope, List<Integer> watchArmyIds, Optional<CampaignDeadline.Cap> campaignDeadline) {
    public static final String KEY = "battle_advance_v1";
    public static final String SCHEMA = "xar.ck3.java-battle-sentinel-plan/v1";
    public static final String OBSERVER = "xar.ck3.java-battle-sentinel-observation/v1";
    public static final String ARM_CAPABILITY = "game.command.research-arm-tactical-daily-sentinel-v1-N";
    public static final String STATUS_CAPABILITY = "game.command.research-query-tactical-daily-sentinel-v1";
    public static final String ARM_PREFIX = "research-arm-tactical-daily-sentinel-v1-";
    public static final String CANCEL_PREFIX = "research-cancel-tactical-daily-sentinel-v1-generation-";
    public BattleAdvancePlan {
        Objects.requireNonNull(step); Objects.requireNonNull(mode); Objects.requireNonNull(scope); watchArmyIds = List.copyOf(watchArmyIds);
        campaignDeadline = Objects.requireNonNull(campaignDeadline);
        int maximum = scope == BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW ? 3 : scope == BattleAdvanceStep.Scope.STATIONARY_OBJECTIVE_HOLD ? 7 : 45;
        long delta = (long) targetDateRaw - startingDateRaw;
        require(startingDateRaw >= 0 && delta >= 24 && delta <= maximum * 24L && delta % 24 == 0 && speed >= 1 && speed <= 5,
                "native battle target requires bounded whole days and native speed");
        require(!watchArmyIds.isEmpty() && watchArmyIds.size() <= 64 && watchArmyIds.stream().allMatch(id -> id >= 0)
                && watchArmyIds.equals(watchArmyIds.stream().distinct().sorted().toList()), "complete sorted distinct sentinel watch IDs required");
        campaignDeadline.ifPresent(cap -> require(cap.status() == CampaignDeadline.Status.ADVANCE
                && cap.startingDateRaw().equals(BigInteger.valueOf(startingDateRaw)) && cap.targetDateRaw().equals(BigInteger.valueOf(targetDateRaw)),
                "sentinel plan does not match actual campaign cap"));
    }
    public record Configuration(int routeTimelineSpeed, boolean allowRouteContactHighSpeedAb,
            boolean committedRouteSpeed4LiveReady, boolean committedRouteSpeed5LiveReady,
            boolean objectiveHoldSpeed4LiveReady, boolean objectiveHoldSpeed5LiveReady,
            Optional<CampaignDeadline.Configuration> campaignDeadline) {
        public Configuration { require(routeTimelineSpeed >= 1 && routeTimelineSpeed <= 5, "configured noncombat sentinel speed 1..5 required"); Objects.requireNonNull(campaignDeadline); }
        /** Defaults retain the actual Python live readiness gates; no speed-five strategy promotion. */
        public static Configuration production(Optional<CampaignDeadline.Configuration> deadline) { return new Configuration(3, false, false, false, false, false, deadline); }
        public void speedGate(BattleAdvanceStep.Scope scope, int speed) {
            if (scope != BattleAdvanceStep.Scope.COMMITTED_ROUTE && scope != BattleAdvanceStep.Scope.STATIONARY_OBJECTIVE_HOLD) return;
            require(speed == routeTimelineSpeed, "noncombat sentinel speed differs from configured timeline speed");
            boolean ready = speed <= 3 || (scope == BattleAdvanceStep.Scope.COMMITTED_ROUTE
                    ? speed == 4 && committedRouteSpeed4LiveReady || speed == 5 && committedRouteSpeed5LiveReady
                    : speed == 4 && objectiveHoldSpeed4LiveReady || speed == 5 && objectiveHoldSpeed5LiveReady);
            require(allowRouteContactHighSpeedAb || ready, "noncombat sentinel lacks explicit A/B or scope speed qualification");
        }
    }
    public static BattleAdvancePlan create(BattleAdvanceStep step, BattleAdvanceFrame.Snapshot start, Configuration configuration) {
        require(start.paused() && start.mapReady() && start.decision().isEmpty(), "sentinel needs a paused map without pending player decision");
        List<Integer> watch = start.watch();
        switch (step) {
            case BattleAdvanceStep.Battle ignored -> require(start.activeCombat(watch), "active battle scope requires active watched combat");
            case BattleAdvanceStep.Route route -> require(!start.activeCombat(watch) && !start.activeRetreat(watch)
                    && start.committedRoute(watch, route.armyId(), route.targetProvinceId()), "committed route does not match complete noncombat subject route");
            case BattleAdvanceStep.Hold hold -> {
                BattleAdvanceFrame.HoldState admission = start.hold(watch, hold);
                require(admission.status() == BattleAdvanceFrame.HoldStatus.MATCHED, "stationary objective hold admission failed: " + admission.reason());
            }
        }
        configuration.speedGate(step.scope(), step.speed());
        BigInteger requested = step.requestedTarget().orElse(BigInteger.valueOf(start.owner().dateRaw()).add(BigInteger.valueOf(45 * 24)));
        Optional<CampaignDeadline.Cap> cap = CampaignDeadline.deadline(configuration.campaignDeadline(), BigInteger.valueOf(start.owner().dateRaw()), requested);
        if (cap.isPresent()) {
            require(cap.orElseThrow().status() == CampaignDeadline.Status.ADVANCE, "campaign endpoint reached before tactical clock submission");
            require(step.requestedTarget().isEmpty() || cap.orElseThrow().targetDateRaw().equals(requested), "typed tactical clock was not normalized to campaign deadline");
        }
        BigInteger target = cap.map(CampaignDeadline.Cap::targetDateRaw).orElse(requested);
        // The public parser keeps int64; the actual CDate/strict shared status has an explicit int32 ABI.
        int nativeTarget = target.intValueExact();
        Mode mode = step instanceof BattleAdvanceStep.Battle battle && battle.terminal() ? Mode.TERMINAL_OR_SENTINEL : Mode.DECISION_EPOCH;
        return new BattleAdvancePlan(step.literal(), start.owner().dateRaw(), nativeTarget, step.speed(), mode, step.scope(), watch, cap);
    }
    public String armStep() { return ARM_PREFIX + startingDateRaw + "-to-" + targetDateRaw + "-speed-" + speed
            + "-mode-" + (mode == Mode.DECISION_EPOCH ? "decision" : "terminal") + "-a-" + watchArmyIds.size() + "-"
            + String.join("-", watchArmyIds.stream().map(String::valueOf).toList()); }
    public List<ExpectedValue> expected() { return List.of(new ExpectedBoolean(new FieldKey("battle_advance.completion_verified"), true),
            new ExpectedBoolean(new FieldKey("paused"), true), new ExpectedInteger(new FieldKey("battle_advance.target_date_raw"), BigInteger.valueOf(targetDateRaw)),
            new ExpectedInteger(new FieldKey("battle_advance.timeline_speed"), BigInteger.valueOf(speed)), new ExpectedText(new FieldKey("battle_advance.scope"), scope.name())); }
    public Obj json() {
        var result = new LinkedHashMap<String, Value>(); result.put("schema", new Text(SCHEMA)); result.put("step", new Text(step));
        result.put("starting_date_raw", number(startingDateRaw)); result.put("target_date_raw", number(targetDateRaw)); result.put("speed", number(speed));
        result.put("mode", new Text(mode.name())); result.put("scope", new Text(scope.name()));
        result.put("watch_army_ids", new Arr(watchArmyIds.stream().<Value>map(BattleAdvancePlan::number).toList()));
        result.put("campaign_deadline", campaignDeadline.<Value>map(AdvancePlan::capJson).orElse(Nil.INSTANCE)); return new Obj(result);
    }
    public static BattleAdvancePlan decode(ActionCommand command) {
        require(command.arguments().members().keySet().equals(Set.of(KEY)), "battle composite argument fields differ");
        return decode(object(command.arguments().get(KEY), KEY), command.operation().value());
    }
    public static BattleAdvancePlan decode(Obj row, String operation) {
        require(row.members().keySet().equals(Set.of("schema", "step", "starting_date_raw", "target_date_raw", "speed", "mode", "scope", "watch_army_ids", "campaign_deadline")), "battle plan fields differ");
        require(SCHEMA.equals(text(row.get("schema"), "schema")), "unsupported battle plan version");
        require(operation.equals(text(row.get("step"), "step")), "durable battle plan operation differs");
        Value cap = row.get("campaign_deadline");
        return new BattleAdvancePlan(operation, integer(row.get("starting_date_raw"), "starting_date_raw").intValueExact(),
                integer(row.get("target_date_raw"), "target_date_raw").intValueExact(), integer(row.get("speed"), "speed").intValueExact(),
                Mode.valueOf(text(row.get("mode"), "mode")), BattleAdvanceStep.Scope.valueOf(text(row.get("scope"), "scope")),
                array(row.get("watch_army_ids"), "watch_army_ids").stream().map(item -> integer(item, "army_id").intValueExact()).toList(),
                cap == Nil.INSTANCE ? Optional.empty() : Optional.of(AdvancePlan.capDecode(object(cap, "campaign_deadline"))));
    }
    private static IntegerValue number(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
}
