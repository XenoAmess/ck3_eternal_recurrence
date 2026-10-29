package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.commander.CommanderQualityCodec;

/** Actual formal scan continuation: query, admit native bytes, then select one assignment. */
public final class CommanderQualityPolicy implements OrdinaryPolicy {
    private static final Set<String> PHASES = Set.of("native_war_reconnaissance", "native_war_pursuit",
            "native_war_pursuit_progress", "native_war_counterpolicy_hold");
    private final ExactRef source;
    /** Root reconstructs and installs exact per-Army contracts for every actual captured request. */
    @FunctionalInterface public interface CollectorFactory { CommanderObservationCollector create(PlanningRequest actualRequest); }
    private final CollectorFactory collectors;
    private final PlanningReadPort reads;
    private final MilitaryPlanningDecision.CommandFactory commands;

    public CommanderQualityPolicy(ExactRef source, CollectorFactory collectors, PlanningReadPort reads,
            MilitaryPlanningDecision.CommandFactory commands) {
        this.source = Objects.requireNonNull(source); this.collectors = Objects.requireNonNull(collectors);
        this.reads = Objects.requireNonNull(reads); this.commands = Objects.requireNonNull(commands);
    }
    @Override public PlanningStage stage() { return PlanningStage.COMMANDER_QUALITY; }
    @Override public ExactRef implementationSource() { return source; }

    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        if (previous.kind() != Kind.ORDINARY || !PHASES.contains(previous.phase())) return new NotApplicable("original commander consumer keeps this phase");
        try {
            CommanderObservationCollector collector=Objects.requireNonNull(collectors.create(request));
            if (!new OpportunityJson.Text(previous.phase()).equals(previous.detail().get("phase")))
                return incomplete("original full military baseline plan is absent from the draft detail");
            OpportunityJson.Obj root = input(request, previous.detail());
            List<OpportunityJson.Value> captured = new ArrayList<>();
            int maximum = request.observations().snapshot().get("player_armies") instanceof OpportunityJson.Arr armies
                    ? armies.items().size() + 1 : 1;
            for (int index = 0; index <= maximum; index++) {
                OpportunityJson.Obj reply = OpportunityJson.object(OpportunityJson.parse(
                        CommanderQualityCodec.continuePlan(OpportunityJson.encode(
                                root.with("queries", new OpportunityJson.Arr(captured))))), "commander continuation");
                String status = OpportunityJson.text(reply.get("status"), "commander continuation status");
                if (status.equals("completed")) {
                    OpportunityJson.Obj planned = object(reply.get("planned"), "planned");
                    OpportunityJson.Obj plan = object(planned.get("plan"), "plan");
                    String phase = OpportunityJson.text(plan.get("phase"), "phase");
                    if (!phase.equals("native_commander_quality_assignment")) {
                        return new Annotate(new Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(),
                                previous.command(), previous.purpose(), previous.domain(), plan),
                                "existing formal commander scan completed without replacing the ordinary action");
                    }
                    var selection = select(request, plan);
                    return new Replace(MilitaryPlanningDecision.draft(request, selection, commands), selection.reason());
                }
                if (!status.equals("query")) return incomplete("unsupported commander continuation status: " + status);
                BigInteger army = OpportunityJson.integer(reply.get("army_id"), "army_id");
                BigInteger revision = OpportunityJson.integer(reply.get("expected_revision"), "expected_revision");
                if (army.signum() < 0 || army.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0
                        || !revision.equals(request.before().frame().revision()))
                    return new Stop(PlanningResult.StopReason.INVALID_FRAME, "commander continuation query scope differs");
                PlanningReadResult<CommanderObservationCollector.Observation> observed =
                        collector.collect(reads, request, army.intValueExact());
                OpportunityJson.Obj entry = empty().with("army_id", number(army));
                if (observed instanceof PlanningReadResult.Known<CommanderObservationCollector.Observation> known) {
                    entry = entry.with("proposal_input", known.value().proposalInput())
                            .with("unavailable_reason", OpportunityJson.Nil.INSTANCE);
                } else if (observed instanceof PlanningReadResult.Unavailable<CommanderObservationCollector.Observation> unavailable) {
                    entry = entry.with("proposal_input", OpportunityJson.Nil.INSTANCE)
                            .with("unavailable_reason", new OpportunityJson.Text(unavailable.reason()));
                } else {
                    return incomplete("unrecognized typed commander query result");
                }
                captured.add(entry);
            }
            return incomplete("commander continuation exceeded the actual finite Army scan");
        } catch (ProjectionDomainRejection invalid) {
            return new Stop(PlanningResult.StopReason.INVALID_FRAME, "commander domain input rejected: " + invalid.getMessage());
        } catch (IllegalArgumentException invalid) {
            return new Stop(PlanningResult.StopReason.INVALID_FRAME, "commander adapter input rejected: " + invalid.getMessage());
        }
    }

    private static OpportunityJson.Obj input(PlanningRequest request, OpportunityJson.Obj plan) {
        List<OpportunityJson.Value> capabilities = new ArrayList<>();
        request.observations().bridgeCapabilities().stream().sorted()
                .forEach(value -> capabilities.add(new OpportunityJson.Text(value)));
        return empty().with("schema", new OpportunityJson.Text(CommanderQualityCodec.PLAN_SCHEMA))
                .with("planned", empty().with("revision", number(request.before().frame().revision())).with("plan", plan))
                .with("snapshot", request.observations().snapshot())
                .with("bridge_capabilities", new OpportunityJson.Arr(capabilities))
                .with("queries", new OpportunityJson.Arr(List.of()));
    }

    static MilitaryPlanningDecision.Select select(PlanningRequest request, OpportunityJson.Obj plan) {
        String step = OpportunityJson.text(plan.get("selected_step"), "commander selected_step");
        var selection = object(plan.get("commander_quality_selection"), "commander_quality_selection");
        var proposal = object(selection.get("proposal"), "commander proposal");
        BigInteger army = nonnegativeId(proposal.get("army_id"), "army_id");
        BigInteger character = nonnegativeId(proposal.get("proposed_commander_character_id"), "commander_character_id");
        String exactStep = "assign-army-commander-v1-army-" + army + "-to-character-" + character;
        OpportunityJson.require(step.equals(exactStep), "commander assignment and actual proposal disagree");
        OpportunityJson.Obj arguments = empty().with("army_id", number(army)).with("commander_character_id", number(character))
                .with("native_carmy_id", number(nonnegativeId(proposal.get("native_carmy_id"), "native_carmy_id")))
                .with("owner_character_id", number(nonnegativeId(proposal.get("owner_character_id"), "owner_character_id")))
                .with("date_raw", number(request.before().frame().identity().dateRaw()));
        return new MilitaryPlanningDecision.Select(OpportunityJson.text(plan.get("policy"), "policy"),
                OpportunityJson.text(plan.get("phase"), "phase"), OpportunityJson.text(plan.get("reason"), "reason"),
                new OperationKey(step), arguments, Purpose.WORLD_ACTION, plan);
    }
    private static BigInteger nonnegativeId(OpportunityJson.Value value, String name) {
        BigInteger id = OpportunityJson.integer(value, name);
        OpportunityJson.require(id.signum() >= 0 && id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                "full native int32 " + name + " required");
        return id;
    }
    private static OpportunityJson.Obj object(OpportunityJson.Value value, String name) { return OpportunityJson.object(value, name); }
    private static OpportunityJson.IntegerValue number(BigInteger value) { return new OpportunityJson.IntegerValue(value); }
    private static OpportunityJson.Obj empty() { return new OpportunityJson.Obj(Map.of()); }
    private static Decision incomplete(String reason) {
        return new Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, reason);
    }
}
