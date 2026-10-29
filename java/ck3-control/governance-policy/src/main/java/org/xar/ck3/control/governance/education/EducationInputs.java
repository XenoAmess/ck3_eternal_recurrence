package org.xar.ck3.control.governance.education;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Immutable, side-effect-free inputs from the already qualified family query. */
public final class EducationInputs {
    private EducationInputs() { }

    public enum Status {
        AVAILABLE("available"), PARTIAL("partial"), UNAVAILABLE("unavailable"), NOT_OBSERVED("not_observed");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Status fromWire(String value) {
            for (Status item : values()) { if (item.wire.equals(value)) { return item; } }
            throw new IllegalArgumentException("unsupported education status");
        }
    }
    public enum Presence { PRESENT, ABSENT }
    public enum LeafKind { VALUES, CHILDHOOD_TRAITS, NATIVE_FOCUS, EDUCATION_POINT_TRAITS, EDUCATION_TRAITS }
    public record Frame(BigInteger nativeRevision, Long playedCharacterId, Long heirCharacterId, Long dateRaw) {
        public Frame { Objects.requireNonNull(nativeRevision); }
    }
    public record Occurrence(int index, long rawCharacterId, boolean generationValid, Boolean alive,
                             Boolean childOfHeir) { }
    public sealed interface LeafFacts permits Values, Traits, Focus { }
    public record Values(Integer ageMeasureRaw, Integer sexSelectorRaw) implements LeafFacts { }
    public record Traits(List<String> queried, List<String> present) implements LeafFacts {
        public Traits { queried = List.copyOf(queried); present = present == null ? null : List.copyOf(present); }
    }
    public record Focus(Presence presence, String key) implements LeafFacts { }

    /** Wire residue belongs to the codec; defensive bytes retain permitted legacy extension fields. */
    public record Leaf(Status status, String unavailableReason, LeafFacts facts, byte[] validatedWire) {
        public Leaf {
            Objects.requireNonNull(status); Objects.requireNonNull(facts);
            validatedWire = validatedWire.clone();
        }
        @Override public byte[] validatedWire() { return validatedWire.clone(); }
    }
    public record CourtOwner(boolean fieldPresent, boolean sourcePresent, String status, String unavailableReason,
                             long childId, BigInteger nativeRevision, Boolean ownerPresent, Long ownerId,
                             boolean sourceQualified, boolean projectionComplete, boolean identityRoundTrip,
                             boolean sampleStable, byte[] validatedWire) {
        public CourtOwner { validatedWire = validatedWire == null ? null : validatedWire.clone(); }
        @Override public byte[] validatedWire() { return validatedWire == null ? null : validatedWire.clone(); }
    }
    public record ChildRead(int characterId, List<Integer> occurrenceIndices, Leaf values, Leaf childhoodTraits,
                            Leaf nativeFocus, Leaf pointTraits, Leaf educationTraits, CourtOwner courtOwner) {
        public ChildRead { occurrenceIndices = List.copyOf(occurrenceIndices); }
        public Leaf leaf(LeafKind kind) {
            return switch (kind) {
                case VALUES -> values; case CHILDHOOD_TRAITS -> childhoodTraits; case NATIVE_FOCUS -> nativeFocus;
                case EDUCATION_POINT_TRAITS -> pointTraits; case EDUCATION_TRAITS -> educationTraits;
            };
        }
    }
    public record ChildInputs(Frame frame, Status status, String unavailableReason, List<ChildRead> rows) {
        public ChildInputs { rows = List.copyOf(rows); }
    }
    public record Descendants(Frame frame, Status status, String unavailableReason, boolean rosterComplete,
                              List<Occurrence> occurrences, ChildInputs childInputs) {
        public Descendants { occurrences = List.copyOf(occurrences); }
    }
    public record Availability(Status status, String unavailableReason) { }
    public record Child(int characterId, long rawCharacterId, List<Integer> occurrenceIndices, ChildRead read,
                        List<Availability> leafAvailability, boolean complete) {
        public Child { occurrenceIndices = List.copyOf(occurrenceIndices); leafAvailability = List.copyOf(leafAvailability); }
    }
    public record Generation(Frame frame, Status status, String unavailableReason, Status nativeRosterStatus,
                             boolean rosterComplete, boolean classificationComplete, Integer rawOccurrenceCount,
                             int knownCount, Integer count, Boolean exists, Boolean knownEmpty,
                             Status childInputsStatus, boolean complete, List<Child> rows) {
        public Generation { rows = List.copyOf(rows); }
    }
}
