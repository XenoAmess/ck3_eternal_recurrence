package org.xar.ck3.control.wave2.governance.educationneeds;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.governance.education.EducationInputs.Frame;
import org.xar.ck3.control.governance.education.EducationInputs.Status;

/** Immutable projections; no native query, source admission, guardian selection or action authority. */
public final class EducationNeedsModel {
    private EducationNeedsModel() { }
    public enum FocusState {
        UNKNOWN("unknown"), KNOWN_ABSENT("known_absent"), EDUCATION_FOCUS_PRESENT("education_focus_present"), OTHER_FOCUS_PRESENT("other_focus_present");
        private final String wire;
        FocusState(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record FocusManagement(boolean available, FocusState state, String currentKey, Boolean focusAbsent,
                                  Boolean educationFocusPresent, String unavailableReason) {
        public FocusManagement {
            Objects.requireNonNull(state);
            if (!available && (state != FocusState.UNKNOWN || currentKey != null || focusAbsent != null || educationFocusPresent != null)
                    || available && (state == FocusState.UNKNOWN || unavailableReason != null)
                    || state == FocusState.KNOWN_ABSENT && (currentKey != null || !Boolean.TRUE.equals(focusAbsent) || !Boolean.FALSE.equals(educationFocusPresent))
                    || state == FocusState.EDUCATION_FOCUS_PRESENT && (currentKey == null || !Boolean.FALSE.equals(focusAbsent) || !Boolean.TRUE.equals(educationFocusPresent))
                    || state == FocusState.OTHER_FOCUS_PRESENT && (currentKey == null || !Boolean.FALSE.equals(focusAbsent) || !Boolean.FALSE.equals(educationFocusPresent))) {
                throw new IllegalArgumentException("focus-management state and nullable operands disagree");
            }
        }
    }
    public record NeedsRowProjection(int characterId, long childFullId, List<Integer> occurrenceIndices,
                                     Frame focusSourceFrame, FocusManagement focusManagement) {
        public NeedsRowProjection { occurrenceIndices = List.copyOf(occurrenceIndices); }
    }
    /** Deliberately opaque already-validated wire material, never an unconstrained business dictionary. */
    public static final class WireValue {
        private final byte[] bytes;
        WireValue(byte[] bytes) { this.bytes = bytes.clone(); }
        public byte[] bytes() { return bytes.clone(); }
    }
    record LeafAvailability(String key, Status status, String reason) { }
    record Child(NeedsRowProjection projection, List<LeafAvailability> availability, WireValue availabilityWire,
                 WireValue values, WireValue childhoodTraits, WireValue pointTraits, WireValue educationTraits,
                 WireValue stockOptions, WireValue currentOption, WireValue courtOwner) {
        Child { availability = List.copyOf(availability); }
    }
    record Decision(Frame frame, boolean rosterComplete, boolean classificationComplete, Boolean knownEmpty, List<Child> children) {
        Decision { children = List.copyOf(children); }
    }
    record MaterialRow(long childId, WireValue wire) { }
    record Materials(boolean present, boolean collected, String reason, List<MaterialRow> rows) {
        Materials { rows = List.copyOf(rows); }
    }
    record ProviderRow(long childId, List<Integer> occurrences, WireValue wire) {
        ProviderRow { occurrences = List.copyOf(occurrences); }
    }
    record Provider(boolean present, Status status, boolean collected, String reason, List<ProviderRow> rows,
                    WireValue wire, WireValue sourceWire) {
        Provider { rows = List.copyOf(rows); }
    }
    record Request(Decision decision, Materials materials, Provider provider) { }
    public record OrdinaryFrame(BigInteger snapshotRevision, long dateRaw, long playerCharacterId,
                                long gamePid, BigInteger connectionGeneration) {
        public OrdinaryFrame { Objects.requireNonNull(snapshotRevision); Objects.requireNonNull(connectionGeneration); }
    }
    public record OrdinaryRoles(Long actorId, Long recipientId, Long secondaryActorId, Long secondaryRecipientId,
                                Long intermediaryId, Long sixthRoleId) { }
    record OrdinaryContext(Status status, String interactionKey, String unavailableReason, OrdinaryRoles roles,
                           WireValue rolesWire, OrdinaryFrame frame, boolean canSend, boolean readyToInitiate) { }
    public record RequestCandidate(boolean available, boolean roleObservationAvailable, Boolean pairMatchesChild,
                                   long childFullId, Long guardianFullId, Boolean guardianRoleKnownNull,
                                   OrdinaryRoles roles, OrdinaryFrame frame, boolean canSend,
                                   boolean readyToInitiate, String basis, String unavailableReason) { }
}
