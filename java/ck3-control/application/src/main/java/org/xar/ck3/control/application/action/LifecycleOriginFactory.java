package org.xar.ck3.control.application.action;

import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure projection of actual source-bound lifecycle input. Root must still re-read every physical original under its writer lock. */
public final class LifecycleOriginFactory {
    private LifecycleOriginFactory() { }
    public sealed interface Result permits Projected, Unavailable { }
    public record Projected(LifecycleIdentity identity, OpportunityJson.Obj semantic) implements Result {
        public Projected { Objects.requireNonNull(identity); Objects.requireNonNull(semantic); }
    }
    public record Unavailable(List<String> reasons) implements Result { public Unavailable { reasons = List.copyOf(reasons); StrictJson.require(!reasons.isEmpty(), "explicit lifecycle projection gap required"); } }
    public static Result project(LifecycleObservationPort.Snapshot observed, DriverObservationFacts freshFacts,
            ExactRef originalHello, ExactRef originalDriver, ExactRef completeSourceQualification) {
        return project(observed,freshFacts,originalHello,originalDriver,java.util.Optional.of(completeSourceQualification));
    }
    public static Result project(LifecycleObservationPort.Snapshot observed, DriverObservationFacts freshFacts,
            ExactRef originalHello, ExactRef originalDriver, java.util.Optional<ExactRef> completeSourceQualification) {
        Objects.requireNonNull(observed); Objects.requireNonNull(freshFacts);
        try {
            var old = observed.facts(); var stamp = old.stamp();
            StrictJson.require(freshFacts.driverVersion() == stamp.driverVersion() && freshFacts.episodeEpoch() == stamp.episodeEpoch()
                    && Arrays.equals(freshFacts.driver().encode(), old.driver().encode()) && freshFacts.source().equals(observed.source()),
                    "current lifecycle facts differ from the actual old Driver subject");
            return project(new DriverObservationAssembler.FullSnapshot(observed.actual(), freshFacts, observed.semantic(), observed.originalEvidence(),
                    DriverObservationAssembler.bindingSha256(observed.semantic())), originalHello, originalDriver, completeSourceQualification);
        } catch (IllegalArgumentException | ArithmeticException failure) {
            return new Unavailable(List.of("actual_lifecycle_origin: " + failure.getMessage()));
        }
    }
    /** Pure archived-original replay; no synthetic Known/history witness or current gameplay identity is needed. */
    public static Result project(DriverObservationAssembler.FullSnapshot observed,
            ExactRef originalHello, ExactRef originalDriver, ExactRef completeSourceQualification) {
        return project(observed,originalHello,originalDriver,java.util.Optional.of(completeSourceQualification));
    }
    public static Result project(DriverObservationAssembler.FullSnapshot observed,
            ExactRef originalHello, ExactRef originalDriver, java.util.Optional<ExactRef> completeSourceQualification) {
        return projectActual(observed,originalHello,originalDriver,completeSourceQualification,java.util.Optional.empty());
    }
    /** Pure operator-before DATA only. The actual Root must still qualify exact HELLO/build/source and its canonical request. */
    public static Result projectOperatorBefore(DriverObservationAssembler.FullSnapshot observed,
            ExactRef originalHello, ExactRef originalDriver, ExactRef completeSourceQualification,OperatorPlayerSwitch.Request request) {
        return projectOperatorBefore(observed,originalHello,originalDriver,java.util.Optional.of(completeSourceQualification),request);
    }
    public static Result projectOperatorBefore(DriverObservationAssembler.FullSnapshot observed,
            ExactRef originalHello, ExactRef originalDriver, java.util.Optional<ExactRef> completeSourceQualification,OperatorPlayerSwitch.Request request) {
        return projectActual(observed,originalHello,originalDriver,completeSourceQualification,java.util.Optional.of(Objects.requireNonNull(request)));
    }
    private static Result projectActual(DriverObservationAssembler.FullSnapshot observed,
            ExactRef originalHello,ExactRef originalDriver,java.util.Optional<ExactRef> completeSourceQualification,
            java.util.Optional<OperatorPlayerSwitch.Request> operator) {
        Objects.requireNonNull(observed);
        try {
            var actual = observed.actual(); var freshFacts = observed.facts(); var old = freshFacts.driver();
            StrictJson.require(freshFacts.transport().equals(actual.session()) && freshFacts.snapshotId().equals(actual.snapshotId())
                    && freshFacts.nativeRevision().equals(actual.nativeRevision()) && freshFacts.source().machineId().equals(actual.session().machineId())
                    && freshFacts.publicRevision().equals(OpportunityJson.integer(observed.semantic().get("revision"), "revision"))
                    && freshFacts.nativeStateSha256().equals(ActionCodec.sha256(actual.state().bytes()))
                    && observed.fullBindingSha256().equals(DriverObservationAssembler.bindingSha256(observed.semantic())), "actual current public revision or old Driver subject evidence is unavailable");
            // Reuse the one actual native envelope/state validator; a constructed FullSnapshot is only DATA.
            var replayed = new DriverObservationAssembler().projectFull(actual, freshFacts, observed.originalEvidence());
            StrictJson.require(replayed.semantic().equals(observed.semantic()), "replayed semantic differs from observed DATA");
            StrictJson.require(replayed.fullBindingSha256().equals(observed.fullBindingSha256()), "replayed binding digest differs from observed DATA");
            byte[] driver = old.encode();
            StrictJson.require(originalDriver.bytes() == driver.length && originalDriver.sha256().equals(ActionCodec.sha256(driver)), "original lifecycle Driver reference differs from its exact producer bytes");
            var raw = DriverJson.object(actual.state().bytes(), DriverJson.MAX_NATIVE_BYTES); var semantic = observed.semantic();
            LifecycleIdentity.CurrentPlayer player = currentPlayer(raw);
            for (String key : List.of("date_raw", "paused", "map_ready"))
                StrictJson.require(raw.members().containsKey(key) && raw.get(key).equals(semantic.get(key)), "lifecycle semantic projection changed actual native field: " + key);
            var subject = new LifecycleIdentity.Subject(old.session().actorId(), old.session().episodeRunId(), freshFacts.episodeEpoch(), freshFacts.driverVersion());
            if(operator.isPresent()) {
                OperatorPlayerSwitch.requireBefore(operator.orElseThrow(),FullJsonTree.parse(DriverJson.encode(semantic),DriverJson.MAX_NATIVE_BYTES));
            }
            var reason = deriveReason(player, subject.characterId());
            var reasonInput = freshFacts.originalSemanticFields();
            var priorReason = reasonInput.get("one_life_terminal_reason");
            if (operator.isEmpty() && reasonInput.members().containsKey("one_life_terminal_reason") && priorReason != OpportunityJson.Nil.INSTANCE)
                StrictJson.require(LifecycleIdentity.TerminalReason.fromWire(OpportunityJson.text(priorReason, "one_life_terminal_reason")) == reason,
                        "original lifecycle reason disagrees with actual native current player and old Driver subject");
            if (operator.isEmpty() && semantic.members().containsKey("one_life_terminal_reason") && semantic.get("one_life_terminal_reason") != OpportunityJson.Nil.INSTANCE)
                StrictJson.require(LifecycleIdentity.TerminalReason.fromWire(OpportunityJson.text(semantic.get("one_life_terminal_reason"), "one_life_terminal_reason")) == reason,
                        "lifecycle projection reason drifted from its actual native phase");
            var projected = new java.util.LinkedHashMap<String, OpportunityJson.Value>(semantic.members());
            var provenance = new java.util.LinkedHashMap<String, OpportunityJson.Value>();
            provenance.put("schema", new OpportunityJson.Text(operator.isPresent()
                    ? "xar.java.operator-before-origin-reason-projection/v1" : "xar.java.lifecycle-origin-reason-projection/v1"));
            provenance.put("present", new OpportunityJson.Bool(reasonInput.members().containsKey("one_life_terminal_reason")));
            if (reasonInput.members().containsKey("one_life_terminal_reason")) provenance.put("original_value", priorReason);
            provenance.put("derived_reason", new OpportunityJson.Text(reason.wire()));
            if(operator.isPresent()) {
                provenance.put("original_semantic_present",new OpportunityJson.Bool(semantic.members().containsKey("one_life_terminal_reason")));
                if(semantic.members().containsKey("one_life_terminal_reason"))provenance.put("original_semantic_value",semantic.get("one_life_terminal_reason"));
                var request=operator.orElseThrow();
                provenance.put("operator_request",new OpportunityJson.Obj(java.util.Map.of(
                        "character_id",new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(request.characterId())),
                        "expected_revision",new OpportunityJson.Text(request.expectedRevision().toString()))));
            }
            projected.put("lifecycle_origin_reason_projection", new OpportunityJson.Obj(provenance));
            projected.put("one_life_terminal_reason", new OpportunityJson.Text(reason.wire()));
            var frame = new LifecycleIdentity.Frame(actual.snapshotId(), freshFacts.publicRevision(), actual.nativeRevision(),
                    OpportunityJson.integer(semantic.get("date_raw"), "date_raw"), OpportunityJson.bool(semantic.get("paused"), "paused"), OpportunityJson.bool(semantic.get("map_ready"), "map_ready"));
            var evidence = new LifecycleIdentity.Evidence(observed.originalEvidence(), originalHello, freshFacts.semanticFactsEvidence(), originalDriver, completeSourceQualification);
            return new Projected(new LifecycleIdentity(actual.session().machineId(), actual.session().game(), actual.session().sessionId(),
                    actual.session().connectionGeneration(), subject, frame, player, reason, evidence, actual.observedAt()), new OpportunityJson.Obj(projected));
        } catch (IllegalArgumentException | ArithmeticException failure) {
            return new Unavailable(List.of("actual_lifecycle_origin: " + failure.getMessage()));
        }
    }
    public static LifecycleIdentity.CurrentPlayer currentPlayer(OpportunityJson.Obj actualNativeState) {
        if (!actualNativeState.members().containsKey("played_character")) return new LifecycleIdentity.Missing();
        var value = actualNativeState.get("played_character"); if (value == OpportunityJson.Nil.INSTANCE) return new LifecycleIdentity.Null();
        var player = OpportunityJson.object(value, "actual native played_character");
        return new LifecycleIdentity.Character(OpportunityJson.integer(player.get("character_id"), "character_id"), OpportunityJson.bool(player.get("alive"), "alive"));
    }
    public static LifecycleIdentity.TerminalReason deriveReason(LifecycleIdentity.CurrentPlayer actual, java.math.BigInteger oldSubject) {
        Objects.requireNonNull(actual); NativeCharacterId.of(oldSubject);
        if (actual instanceof LifecycleIdentity.Missing || actual instanceof LifecycleIdentity.Null) return LifecycleIdentity.TerminalReason.MISSING;
        if (!(actual instanceof LifecycleIdentity.Character player)) throw new IllegalArgumentException("unknown native current-player branch");
        if (!player.characterId().equals(oldSubject)) return LifecycleIdentity.TerminalReason.CHANGED;
        StrictJson.require(!player.alive(), "an actual same living subject is ordinary gameplay, not a terminal lifecycle origin");
        return LifecycleIdentity.TerminalReason.DEAD;
    }
}
