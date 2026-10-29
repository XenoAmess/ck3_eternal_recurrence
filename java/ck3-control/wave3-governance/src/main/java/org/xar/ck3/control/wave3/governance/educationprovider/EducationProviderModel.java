package org.xar.ck3.control.wave3.governance.educationprovider;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.governance.education.EducationInputs.Status;

/** The complete existing provider value contract. These values do not confer native source admission. */
public final class EducationProviderModel {
    private EducationProviderModel() { }
    public record Full32(int signed) { public long raw() { return Integer.toUnsignedLong(signed); } }
    public record Frame(BigInteger nativeRevision, long dateRaw, Full32 playedCharacter, Full32 heirCharacter) {
        public Frame { Objects.requireNonNull(nativeRevision); Objects.requireNonNull(playedCharacter); Objects.requireNonNull(heirCharacter); }
    }
    public record Binding(String requestId, Frame frame, Integer normalizedFamilyHeir) {
        public Binding { Objects.requireNonNull(requestId); Objects.requireNonNull(frame); }
    }
    public record Occurrence(long rawFullId, boolean generationValid, Boolean alive, Boolean childOfHeir, int occurrenceIndex) { }
    public record SelectedChild(Full32 characterId, List<Integer> occurrenceIndices) {
        public SelectedChild { occurrenceIndices = List.copyOf(occurrenceIndices); }
    }
    public record FamilyInventory(Frame descendantFrame, Frame selectedInputsFrame, boolean descendantsAvailable,
                                  boolean rosterComplete, boolean familyPresent, Boolean dataPointerPresent,
                                  int nativeChildCount, Status selectedInputsStatus, List<Occurrence> rawRows,
                                  List<SelectedChild> selectedChildren) {
        public FamilyInventory { rawRows = List.copyOf(rawRows); selectedChildren = List.copyOf(selectedChildren); }
    }
    public record EducationTraits(boolean available, String unavailableReason, List<String> presentTraitKeys) {
        public EducationTraits { presentTraitKeys = presentTraitKeys == null ? null : List.copyOf(presentTraitKeys); }
    }
    public record CultureParameter(String key, boolean available, Long cultureFullId, Boolean value, String unavailableReason) { }
    public record ProviderChild(long childFullId, String roleSource, List<Integer> occurrenceIndices,
                                EducationTraits educationTraits, CultureParameter cultureParameter,
                                Long guardianFullId, CultureParameter guardianCultureParameter,
                                String guardianUnavailableReason, String riteUnavailableReason,
                                String educationVariablesUnavailableReason) {
        public ProviderChild { occurrenceIndices = List.copyOf(occurrenceIndices); }
    }
    public record Provider(String requestId, Frame frame, Status status, String unavailableReason,
                           boolean rosterComplete, boolean collectionAvailable, boolean childObservationComplete,
                           List<String> queriedEducationTraitKeys, List<ProviderChild> rows) {
        public Provider { queriedEducationTraitKeys = List.copyOf(queriedEducationTraitKeys); rows = List.copyOf(rows); }
    }
    public record ExpectedChild(long childFullId, List<Integer> occurrenceIndices) {
        public ExpectedChild { occurrenceIndices = List.copyOf(occurrenceIndices); }
    }
    /** Caller source result is retained as a prerequisite, never minted by this pure leaf. */
    public record Request(boolean callerCapturedSourceQualified, Binding binding,
                          FamilyInventory family, Provider provider) { }
    /** Structural/native-frame projection only: the original query owner still grants source eligibility. */
    public record Validation(Provider provider, List<ExpectedChild> expectedChildren,
                             boolean sourceAdmissionGranted, boolean actionAuthorityGranted) {
        public Validation {
            expectedChildren = List.copyOf(expectedChildren);
            if (sourceAdmissionGranted || actionAuthorityGranted) { throw new IllegalArgumentException("pure provider validation cannot grant source or action admission"); }
        }
    }
}
