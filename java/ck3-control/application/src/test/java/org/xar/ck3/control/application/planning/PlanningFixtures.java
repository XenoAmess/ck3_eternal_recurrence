package org.xar.ck3.control.application.planning;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class PlanningFixtures {
    static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    static final ExactRef SOURCE = new ExactRef("fixture-source", 1, "a".repeat(64));
    static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private PlanningFixtures() { }
    static Obj snapshot() {
        return new Obj(Map.ofEntries(
                Map.entry("paused", new Bool(true)), Map.entry("map_ready", new Bool(true)),
                Map.entry("revision", integer(1)), Map.entry("native_revision", integer(1)),
                Map.entry("date_raw", integer(24000)), Map.entry("snapshot_id", new Text("snapshot-1")),
                Map.entry("episode_run_id", new Text("episode-1")),
                Map.entry("played_character", new Obj(Map.of("character_id", integer(29829), "alive", new Bool(true)))),
                Map.entry("active_wars", new Arr(List.of())), Map.entry("player_armies", new Arr(List.of())),
                Map.entry("diagnostics", new Obj(Map.of("connection_generation", integer(1), "bridge_pid", integer(123))))));
    }
    static IntegerValue integer(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    static PlanningRequest request(Obj snapshot, List<Obj> history, Set<OperationKey> steps) {
        var before = new ObservationIdentity("fixture-machine-1", GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                        BigInteger.ONE, BigInteger.valueOf(24000)), "snapshot-1", BigInteger.ONE, "episode-1"), 1);
        var observed = new PlanningObservation(snapshot, history, steps, Set.of(), Optional.empty(), List.of(),
                Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, new G2Source(before.machineId(), NOW.toString(), "fixture-build", SOURCE),
                "session-1", NOW.plusSeconds(60), observed);
    }
    static ActionCommand command(PlanningRequest request, OperationKey operation, Obj arguments) {
        return new ActionCommand("fixture-action", request.before(), request.source(), request.sessionId(), operation, arguments,
                new ExpectedPostcondition(1, request.before(), request.source(), "fixture-observer/v1",
                        List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
    }
}
