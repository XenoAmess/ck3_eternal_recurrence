package org.xar.ck3.control.nativebridge.capabilities.army;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Concrete full semantic observation through the same held Native/Driver producer. */
public final class ArmyRetreatFrames {
    public record Current(Complete actual, Instant deadline) {
        public Current { Objects.requireNonNull(actual); Objects.requireNonNull(deadline); requirePaused(actual.semantic()); }
        public Context context() { return new Context(actual.identity(), actual.source(), actual.sessionId(), deadline); }
        public ActiveRetreatProposal.SourceFrame source() { return ActiveRetreatProposal.SourceFrame.read(actual.semantic()); }
        public NativeEffectEvidence.FrameBasis basis() { return NativeEffectEvidence.basis(actual); }
        public AdvanceObservationPort.Frame advanceFrame() {
            return new AdvanceObservationPort.Frame(actual.identity(), actual.source(), actual.sessionId(), actual.semantic(),
                    new ObservationProvenance.Push(actual.identity().frame().snapshotId(), actual.identity().frame().identity().nativeRevision(), actual.originalEvidence()), actual.observedAt(), actual.originalEvidence());
        }
    }
    private final java.util.function.Supplier<HeldDriverObservationPort> driver;
    public ArmyRetreatFrames(HeldDriverObservationPort sameHeldDriver) { Objects.requireNonNull(sameHeldDriver); driver = () -> sameHeldDriver; }
    /** Menu-time graph construction defers only the once-bound concrete Driver lookup, never observation authority. */
    public ArmyRetreatFrames(java.util.function.Supplier<HeldDriverObservationPort> actualBoundDriver) { driver = Objects.requireNonNull(actualBoundDriver); }
    public Current current(Instant deadline) throws InterruptedException { return new Current(Objects.requireNonNull(driver.get(), "actual adopted held Driver is unavailable").observe(deadline), deadline); }
    public static void same(Current before, Current after) {
        require(before.actual().identity().equals(after.actual().identity()) && before.actual().source().equals(after.actual().source())
                && before.actual().sessionId().equals(after.actual().sessionId()) && before.source().equals(after.source())
                && before.actual().fullBindingSha256().equals(after.actual().fullBindingSha256()), "retreat read crossed its complete native/Driver source binding");
    }
    public static Obj selected(Current current, PublicUnitId subject) {
        var armies = OpportunityJson.array(current.actual().semantic().get("player_armies"), "player armies");
        List<Obj> matches = armies.stream().map(value -> OpportunityJson.object(value, "player army"))
                .filter(value -> new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(subject.value())).equals(value.get("army_id"))).toList();
        require(matches.size() == 1, "selected retreat CUnit must occur exactly once in current player armies"); Obj selected = matches.getFirst();
        require(OpportunityJson.bool(selected.get("controllable"), "controllable") && OpportunityJson.bool(selected.get("in_combat"), "in_combat")
                && !OpportunityJson.bool(selected.get("retreating"), "retreating"), "selected retreat CUnit is not controllable in active combat");
        require(OpportunityJson.integer(selected.get("owner_character_id"), "owner").equals(current.context().playerId()), "selected retreat CUnit belongs to another actor");
        return selected;
    }
    private static void requirePaused(Obj snapshot) {
        require(OpportunityJson.bool(snapshot.get("paused"), "paused") && OpportunityJson.bool(snapshot.get("map_ready"), "map_ready")
                && OpportunityJson.bool(OpportunityJson.object(snapshot.get("played_character"), "player").get("alive"), "alive"), "retreat requires an actual living paused map");
    }
}
