package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.AdvanceRewrite;
import org.xar.ck3.control.application.advance.LifeAdvanceCommands;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.application.planning.military.WarCorePlanner;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real core chooser, Life rewrite/decoder and Root cache. No RootContext or Native authority is invented. */
final class RootPreparedRequestScopeTest {
    private static final ExactRef SOURCE = new ExactRef("software/core", 1, "a".repeat(64));
    private static final OperationKey ADVANCE = new OperationKey("life-advance");

    @Test void equalValueNewRequestReentersTheRealCoreAndPreparesAgain() {
        var first = request();
        var second = new PlanningRequest(first.before(), first.source(), first.sessionId(), first.deadline(), first.observations());
        assertEquals(first, second); assertNotSame(first, second);
        assertReentry(first, second);
    }

    @Test void sameFrameNewDeadlineCannotBorrowTheOldPreparedCommand() {
        var first = request();
        var second = new PlanningRequest(first.before(), first.source(), first.sessionId(), first.deadline().plusSeconds(20), first.observations());
        var commands = assertReentry(first, second);
        assertNotEquals(commands.get(0).deadline(), commands.get(1).deadline());
        assertThrows(IllegalArgumentException.class, () -> LifeAdvanceCommands.requirePrepared(second, ADVANCE,
                new Obj(Map.of()), selectedPlan(), commands.get(0)));
    }

    private static List<ActionCommand> assertReentry(PlanningRequest first, PlanningRequest second) {
        Map<String, RootRuntimeCommands.Held> cache = new LinkedHashMap<>();
        Map<String, RootSaveCheckpointCommandProducer.Prepared> checkpoints = new LinkedHashMap<>();
        var preparations = new AtomicInteger();
        var core = core((request, operation, arguments, plan, purpose, domain) -> {
            String id = LifeAdvanceCommands.decisionId(request, operation, arguments, plan);
            var held = RootRuntimeCommands.currentHeld(id, request, cache, checkpoints);
            ActionCommand actual;
            if (held != null) actual = held.command();
            else {
                preparations.incrementAndGet();
                var seed = new ActionCommand(id, request.before(), request.source(), request.sessionId(), operation,
                        arguments.with("plan", plan), new ExpectedPostcondition(1, request.before(), request.source(), AdvancePlan.OBSERVER,
                        List.of(new ExpectedBoolean(new FieldKey("paused"), true))),
                        new Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
                actual = AdvanceRewrite.rewrite(request, seed, operation.value(), Optional.empty());
                cache.put(id, new RootRuntimeCommands.Held(request, operation, arguments, plan, actual, Optional.empty(), Optional.empty()));
            }
            var selected = new MilitaryPlanningDecision.Select(OpportunityJson.text(plan.get("policy"), "policy"),
                    OpportunityJson.text(plan.get("phase"), "phase"), OpportunityJson.text(plan.get("reason"), "reason"),
                    operation, arguments, purpose, plan);
            return new OrdinaryCorePolicy.OwnerPrepared(MilitaryPlanningDecision.PreparedSelection.life(id, request, selected, actual));
        });
        var a = command(core, first);
        assertSame(a, command(core, first)); assertEquals(1, preparations.get());
        var b = command(core, second);
        assertEquals(a.actionId(), b.actionId()); assertEquals(a.before(), b.before());
        assertNotSame(a, b); assertEquals(2, preparations.get()); assertEquals(1, cache.size());
        assertSame(second, cache.get(b.actionId()).request()); assertEquals(second.deadline(), b.deadline());
        assertEquals(selectedPlan(), cache.get(b.actionId()).originalPlan());
        assertSame(b, command(core, second)); assertEquals(2, preparations.get());
        return List.of(a, b);
    }

    private static ActionCommand command(OrdinaryCorePolicy core, PlanningRequest request) {
        return assertInstanceOf(OrdinaryPolicy.Replace.class, core.evaluate(request, OrdinaryPolicy.Draft.empty())).draft().command().orElseThrow();
    }

    private static Obj selectedPlan() {
        return new Obj(Map.of("policy", new Text("one-life-turn-v1"), "phase", new Text("current_life_loop"),
                "selected_step", new Text("life-advance"), "reason", new Text("advance to the next visible event and reassess the realm")));
    }

    private static PlanningRequest request() {
        var now = Instant.parse("2026-10-30T15:47:00Z");
        var source = new G2Source("software-request-scope", now.toString(), "fixture-build", SOURCE);
        var identity = new ObservationIdentity(source.machineId(), new GameGeneration(4242,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(29829), BigInteger.valueOf(19), BigInteger.valueOf(53144328)),
                        "native:19", BigInteger.valueOf(20), "software-episode"), 1);
        Obj snapshot = new Obj(Map.of("paused", new Bool(true), "map_ready", new Bool(true), "speed", new IntegerValue(BigInteger.ONE),
                "player_armies", new Arr(List.of()), "active_wars", new Arr(List.of()), "active_event", Nil.INSTANCE,
                "pending_character_interaction", Nil.INSTANCE, "one_life_terminal_reason", Nil.INSTANCE,
                "top_exclusive_modal_choice_hint", new Obj(Map.of("status", new Text("absent")))))
                .with("revision", new IntegerValue(BigInteger.valueOf(20))).with("native_revision", new IntegerValue(BigInteger.valueOf(19)))
                .with("date_raw", new IntegerValue(BigInteger.valueOf(53144328))).with("snapshot_id", new Text("native:19"))
                .with("episode_run_id", new Text("software-episode"))
                .with("played_character", new Obj(Map.of("character_id", new IntegerValue(BigInteger.valueOf(29829)), "alive", new Bool(true))))
                .with("diagnostics", new Obj(Map.of("bridge_pid", new IntegerValue(BigInteger.valueOf(4242)),
                        "connection_generation", new IntegerValue(BigInteger.ONE))));
        var history = List.of("dynasty-review", "succession-review", "marriage-confirm-response", "war-enforce-demands", "war-disband-armies", "save-checkpoint")
                .stream().map(step -> new Obj(Map.of("command", new Text(step), "ok", new Bool(true)))).toList();
        return new PlanningRequest(identity, source, "software-session", now.plusSeconds(30),
                new PlanningObservation(snapshot, history, Set.of(ADVANCE, new OperationKey("set-speed-5")),
                        Set.of("game.command.query-war-results-window-v1"), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }

    private static OrdinaryCorePolicy core(OrdinaryCorePolicy.CommandBinding binding) {
        return OrdinaryCorePolicy.assemble(SOURCE, continuation -> {
            var leaves = new ArrayList<WarCorePlanner.Leaf>();
            for (var boundary : WarCorePlanner.Boundary.values())
                leaves.add(new WarCorePlanner.Leaf(boundary, SOURCE, (request, previous) -> new MilitaryPlanningDecision.Keep(new Obj(Map.of()))));
            PlanningReadPort reads = new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                    throw new AssertionError("software chooser performs no Native read");
                }
            };
            return new WarCorePlanner(leaves,
                    request -> new WarCorePlanner.KnownTactics(request.before(), new WarCorePlanner.RouteTactics(Set.of(), Set.of())),
                    (request, selected) -> { throw new AssertionError("ordinary core owns this selection"); }, reads,
                    (request, selected) -> { throw new AssertionError("no Native read selected"); }, continuation);
        }, (request, previous) -> new OrdinaryPolicy.Keep("software event source"),
                (request, previous) -> new OrdinaryPolicy.Keep("software council source"),
                (request, previous) -> new OrdinaryPolicy.Keep("software marriage source"),
                (request, previous) -> new OrdinaryPolicy.Keep("software entry source"), binding, step -> step.equals("life-advance")).core();
    }
}
