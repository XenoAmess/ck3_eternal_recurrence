package org.xar.ck3.control.wave2.events.eventtraits;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Available;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Frame;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Observation;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Trait;

/** Migration of the existing .9001 native0/1 material branch; no native action or ACK inference. */
public final class PoetTraitOutcome {
    public static final String EVENT = "trait_specific.9001";
    public static final String SOURCE_PATH = "events/trait_specific_events/trait_specific_events.txt";
    public static final String SOURCE_SHA256 = "76A50F2B779E085419279801B1396A1C67C8785831E8859FCEC6D0F088853C3A";
    private PoetTraitOutcome() { }

    public enum Choice {
        POET(0, Trait.LIFESTYLE_POET), JOURNALLER(1, Trait.JOURNALLER);
        private final int nativeIndex;
        private final Trait trait;
        Choice(int nativeIndex, Trait trait) { this.nativeIndex = nativeIndex; this.trait = trait; }
        public int nativeIndex() { return nativeIndex; }
        public Trait trait() { return trait; }
    }
    public enum Status { UNAVAILABLE, FAILED, VERIFIED_CHANGE }
    public enum Reason {
        SAME_FRAME_UNAVAILABLE("same_frame_event_trait_membership_unavailable"),
        NATIVE_OBSERVATION_UNAVAILABLE("native_event_trait_observation_unavailable"),
        NOT_ADDED_OR_BINDING_DIFFERS("event_trait_not_added_or_frame_binding_differs");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record PublicFrame(String snapshotId, BigInteger revision, Frame nativeFrame) {
        public PublicFrame {
            StrictJson.text(snapshotId); Objects.requireNonNull(revision, "revision");
            Objects.requireNonNull(nativeFrame, "nativeFrame");
            StrictJson.require(revision.signum() >= 0, "nonnegative public revision required");
        }
    }
    public record PlanInput(ScalarEventOutcome.Decision decision, PublicFrame frame, Observation membership) {
        public PlanInput { Objects.requireNonNull(frame, "frame"); }
    }
    public record Binding(Choice choice, PublicFrame frame) {
        public Binding { Objects.requireNonNull(choice, "choice"); Objects.requireNonNull(frame, "frame"); }
    }
    public sealed interface Expectation permits Ready, Unavailable { Binding binding(); }
    public record Ready(Binding binding) implements Expectation { public Ready { Objects.requireNonNull(binding); } }
    public record Unavailable(Binding binding, Reason reason) implements Expectation {
        public Unavailable { Objects.requireNonNull(binding); Objects.requireNonNull(reason); }
    }
    /** oldInstanceAdvanced is the independent Driver result, not command acceptance. */
    public record Selection(boolean oldInstanceAdvanced, PublicFrame startingFrame, PublicFrame endingFrame,
                            Observation before, Observation after) { }
    public record Evaluation(Expectation expectation, Status status, Boolean relationSatisfied,
                             Boolean materialChangeObserved, Boolean endingValue, Integer delta, Reason reason) {
        public Evaluation { Objects.requireNonNull(expectation); Objects.requireNonNull(status); }
        public boolean actionAuthorized() { return false; }
        public boolean replayAuthorized() { return false; }
        public boolean saveCreditGranted() { return false; }
    }

    /** Null generic observable_postcondition does not erase this existing dedicated trait branch. */
    public static Optional<Expectation> plan(PlanInput input) {
        Objects.requireNonNull(input, "input");
        ScalarEventOutcome.Decision decision = input.decision();
        if (decision == null || !"recommended".equals(decision.status()) || !EVENT.equals(decision.eventDefinitionKey())
                || !EventTraitMembership.GAME_VERSION.equals(decision.ck3Build())) return Optional.empty();
        Choice choice;
        if (BigInteger.ZERO.equals(decision.selectedNativeOptionIndex())) choice = Choice.POET;
        else if (BigInteger.ONE.equals(decision.selectedNativeOptionIndex())) choice = Choice.JOURNALLER;
        else return Optional.empty();
        Binding binding = new Binding(choice, input.frame());
        boolean ready = input.membership() instanceof Available available
            && available.frame().equals(input.frame().nativeFrame()) && !available.traits().contains(choice.trait());
        return Optional.of(ready ? new Ready(binding) : new Unavailable(binding, Reason.SAME_FRAME_UNAVAILABLE));
    }

    public static Evaluation evaluate(Expectation expected, Selection selection) {
        Objects.requireNonNull(expected, "expected");
        if (expected instanceof Unavailable unavailable) return unavailable(expected, unavailable.reason());
        if (selection == null || !(selection.before() instanceof Available before)
                || !(selection.after() instanceof Available after)) return unavailable(expected, Reason.NATIVE_OBSERVATION_UNAVAILABLE);
        Binding binding = expected.binding(); PublicFrame start = binding.frame(); PublicFrame end = selection.endingFrame();
        boolean bound = selection.oldInstanceAdvanced() && start.equals(selection.startingFrame()) && end != null
            && !start.snapshotId().equals(end.snapshotId()) && end.revision().compareTo(start.revision()) > 0
            && before.frame().equals(start.nativeFrame()) && after.frame().equals(end.nativeFrame())
            && end.nativeFrame().nativeRevision().compareTo(start.nativeFrame().nativeRevision()) > 0
            && end.nativeFrame().playedCharacterId() == start.nativeFrame().playedCharacterId()
            && end.nativeFrame().dateRaw() == start.nativeFrame().dateRaw()
            && !before.traits().contains(binding.choice().trait());
        boolean ending = after.traits().contains(binding.choice().trait());
        boolean changed = bound && ending;
        return new Evaluation(expected, changed ? Status.VERIFIED_CHANGE : Status.FAILED, changed, changed, ending,
            changed ? 1 : 0, changed ? null : Reason.NOT_ADDED_OR_BINDING_DIFFERS);
    }

    /** Emit the original Python material expectation/evaluation JSON domain, including explicit nulls. */
    public static byte[] encode(Expectation expected) { return StrictJson.canonical(base(expected), 8192); }
    public static byte[] encode(Evaluation evaluated) {
        ObjectNode object = base(evaluated.expectation());
        object.put("status", switch (evaluated.status()) {
            case UNAVAILABLE -> "unavailable"; case FAILED -> "failed"; case VERIFIED_CHANGE -> "verified_change";
        });
        nullableBoolean(object, "relation_satisfied", evaluated.relationSatisfied());
        nullableBoolean(object, "material_change_observed", evaluated.materialChangeObserved());
        nullableBoolean(object, "ending_value", evaluated.endingValue());
        if (evaluated.delta() == null) object.putNull("delta"); else object.put("delta", evaluated.delta());
        if (evaluated.reason() == null) object.putNull("unavailable_reason"); else object.put("unavailable_reason", evaluated.reason().wire());
        return StrictJson.canonical(object, 8192);
    }

    private static ObjectNode base(Expectation expected) {
        Objects.requireNonNull(expected, "expected"); Binding binding = expected.binding(); PublicFrame start = binding.frame();
        ObjectNode object = StrictJson.object();
        object.put("schema", ScalarEventOutcome.SCHEMA).put("schema_version", 1).put("event_definition_key", EVENT)
            .put("selected_option_number", binding.choice().nativeIndex() + 1).put("selected_native_option_index", binding.choice().nativeIndex())
            .put("metric", "played_character.event_traits." + binding.choice().trait().wire()).put("trait_key", binding.choice().trait().wire())
            .put("expected_relation", "false_to_true").put("material_change_required_for_evidence", true)
            .put("status", expected instanceof Ready ? "ready" : "unavailable")
            .put("starting_snapshot_id", start.snapshotId()).put("starting_revision", start.revision())
            .put("starting_native_revision", start.nativeFrame().nativeRevision()).put("date_raw", start.nativeFrame().dateRaw())
            .put("character_id", start.nativeFrame().playedCharacterId());
        if (expected instanceof Ready) object.put("starting_value", false).putNull("unavailable_reason");
        else if (expected instanceof Unavailable unavailable) object.putNull("starting_value").put("unavailable_reason", unavailable.reason().wire());
        return object;
    }
    private static Evaluation unavailable(Expectation expected, Reason reason) {
        return new Evaluation(expected, Status.UNAVAILABLE, null, null, null, null, reason);
    }
    private static void nullableBoolean(ObjectNode node, String name, Boolean value) {
        if (value == null) node.putNull(name); else node.put(name, value);
    }
}
