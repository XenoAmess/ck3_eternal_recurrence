package org.xar.ck3.control.application.action.council;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** The issuer and the original writer's registered verifier replay these same pure transitions. */
public final class CouncilContinuationReducer {
    private CouncilContinuationReducer() { }
    public static State issue(State before, List<Retained> prior, Retained next) {
        align(before, prior); StrictJson.require(next.status() == Status.ISSUED, "first continuation state is ISSUED");
        StrictJson.require(before.active().isEmpty() || before.active().orElseThrow().equals(next.request().scope()), "another original action owns the continuation scope");
        StrictJson.require(prior.stream().noneMatch(row -> row.status() != Status.ACK), "ISSUED or UNKNOWN continuation blocks every new request ID");
        StrictJson.require(prior.stream().noneMatch(row -> row.request().requestId().equals(next.request().requestId())), "original continuation request ID is never reused");
        StrictJson.require(prior.isEmpty() || prior.getLast().request().issuedSequence() < next.request().issuedSequence(), "continuation issue sequence must advance");
        var refs = new ArrayList<>(before.records()); refs.add(next.reference());
        return new State(before.machineId(), Optional.of(next.request().scope()), refs, before.completedScopeChain());
    }
    public static State outcome(State before, List<Retained> prior, Retained previous, Retained next, boolean collectedLate) {
        align(before, prior); StrictJson.require(previous.request().equals(next.request()) && before.active().filter(next.request().scope()::equals).isPresent(), "continuation request body/scope is immutable");
        StrictJson.require(previous.status() == Status.ISSUED || collectedLate && previous.status() == Status.UNKNOWN && next.status() == Status.ACK,
                "ACK is immutable; UNKNOWN can only receive the original late ACK, never dispatch again");
        StrictJson.require(next.status() != Status.ISSUED && next.entry().issued().isPresent(), "result requires original issued custody");
        if (previous.entry().issued().isPresent()) StrictJson.require(previous.entry().issued().equals(next.entry().issued()), "late result changed original issued custody");
        else StrictJson.require(next.entry().issued().orElseThrow().record().equals(previous.reference()), "result erased the exact original issued row");
        var refs = new ArrayList<>(before.records()); int index = refs.indexOf(previous.reference());
        StrictJson.require(index >= 0 && index == refs.size() - 1, "only the current last issued continuation may receive its original result");
        refs.set(index, next.reference()); return new State(before.machineId(), before.active(), refs, before.completedScopeChain());
    }
    public static State rotate(State before, List<Retained> prior, ActionReceipt actualSettledParent, ExactRef completeArchive) {
        align(before, prior); Scope scope = before.active().orElseThrow(() -> new IllegalArgumentException("no original scope to archive"));
        StrictJson.require(actualSettledParent.settled() && actualSettledParent.command().actionId().equals(scope.parentActionId())
                && actualSettledParent.bodySha256().equals(scope.parentBodySha256())
                && ActionTransitions.attempt(actualSettledParent.state()).filter(attempt -> attempt.requestId().equals(scope.originalAttemptRequestId())).isPresent(), "only the actual settled original parent may close its continuation scope");
        StrictJson.require(prior.stream().allMatch(row -> row.status() == Status.ACK), "unresolved continuation history cannot be retired or cleared");
        return new State(before.machineId(), Optional.empty(), List.of(), Optional.of(completeArchive));
    }
    private static void align(State before, List<Retained> prior) {
        StrictJson.require(before.records().equals(prior.stream().map(Retained::reference).toList()), "complete current continuation manifest must be consumed");
        StrictJson.require(prior.stream().allMatch(row -> before.active().filter(row.request().scope()::equals).isPresent()), "continuation rows crossed the active parent scope");
    }
}
