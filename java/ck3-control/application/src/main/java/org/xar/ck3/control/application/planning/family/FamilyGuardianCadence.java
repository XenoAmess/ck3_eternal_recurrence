package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.math.BigInteger;
import java.util.HashMap;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceCodec;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceModel.*;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceProjectionPort;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianNegativeCadence;

/** Original Service-local completed-negative cache. Cold construction starts empty; no canonical writer or action credit. */
final class FamilyGuardianCadence {
    record Scope(Obj frame, Obj needs, Value heir, Frame typedFrame, Optional<SourceScope> source) { }
    private State state = State.empty();
    Optional<Scope> scope(Obj snapshot, Obj needs, Value heir) {
        if (!yes(snapshot.get("paused")) || !yes(snapshot.get("map_ready"))
                || !array(snapshot.get("active_wars")).isEmpty() || present(snapshot.get("active_event"))
                || present(snapshot.get("pending_character_interaction")) || present(snapshot.get("one_life_terminal_reason"))) return Optional.empty();
        try {
            Obj diagnostics = object(snapshot.get("diagnostics"));
            Obj frame = obj("status", t("complete"), "snapshot_id", snapshot.get("snapshot_id"),
                    "bridge_pid", diagnostics.get("bridge_pid"), "connection_generation", diagnostics.get("connection_generation"),
                    "episode_run_id", snapshot.get("episode_run_id"), "actor_character_id", object(snapshot.get("played_character")).get("character_id"),
                    "date_raw", snapshot.get("date_raw"), "native_revision", snapshot.get("native_revision"), "revision", snapshot.get("revision"));
            Input parsed = parse(frame, needs, heir, obj(), Nil.INSTANCE, rows(List.of()));
            return Optional.of(new Scope(frame, needs, heir, parsed.frame(), GuardianNegativeCadence.sourceScope(parsed.frame(), parsed.materials(), parsed.heirId())));
        } catch (IllegalArgumentException absentCacheInputs) { return Optional.empty(); }
    }
    synchronized Optional<Obj> deferred(Optional<Scope> scope) {
        if (scope.isEmpty()) return Optional.empty(); Scope current = scope.get();
        return GuardianNegativeCadence.deferred(state, current.source(), current.typedFrame()).map(value ->
                decode(new GuardianCadenceProjectionPort().encode(new GuardianCadenceProjectionPort.DeferredResult(Optional.of(value)))));
    }
    synchronized Optional<Obj> observe(BigInteger child, Optional<Scope> scope, Value defaultQuery, Arr attempts) {
        if (scope.isEmpty()) { remove(child); return Optional.empty(); }
        Scope current = scope.get();
        try {
            Input input = parse(current.frame(), current.needs(), current.heir(), decode(GuardianCadenceCodec.encodeState(state)), defaultQuery, attempts);
            ObservationResult result = GuardianNegativeCadence.observe(state, current.source(), current.typedFrame(), input.defaultQuery(), input.attempts(), "life-advance");
            if (result.observation().isEmpty()) { remove(child); return Optional.empty(); }
            state = result.state();
            Obj encoded = decode(new GuardianCadenceProjectionPort().encode(new GuardianCadenceProjectionPort.Observed(result)));
            return Optional.of(object(encoded.get("observation")));
        } catch (IllegalArgumentException cacheNotQualified) { remove(child); return Optional.empty(); }
    }
    synchronized void selectableIntentObserved() { state = State.empty(); }
    synchronized State currentState() { return state; }
    private void remove(BigInteger child) {
        HashMap<Long, NegativeRecord> records = new HashMap<>(state.records()); records.remove(child.longValueExact()); state = new State(records);
    }
    private static Input parse(Obj frame, Obj needs, Value heir, Obj state, Value query, Arr attempts) {
        return GuardianCadenceCodec.decode(bytes(obj("schema", t(GuardianCadenceCodec.SCHEMA), "frame", frame, "needs", needs,
                "heir_id", heir, "state", state, "default_query", query, "attempts", attempts, "selected_step", t("life-advance"))));
    }
    private static boolean present(Value value) { return value != null && value != Nil.INSTANCE; }
}
