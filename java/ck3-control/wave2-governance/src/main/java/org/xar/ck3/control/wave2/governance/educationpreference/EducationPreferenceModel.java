package org.xar.ck3.control.wave2.governance.educationpreference;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusManagement;

/** Pure request ordering inputs. These records do not grant ordinary-query or send qualification. */
public final class EducationPreferenceModel {
    private EducationPreferenceModel() { }
    public enum Skill {
        DIPLOMACY("diplomacy"), MARTIAL("martial"), STEWARDSHIP("stewardship"), INTRIGUE("intrigue"), LEARNING("learning");
        private final String wire;
        Skill(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Optional<Skill> forFocus(String key) {
            for (Skill item : values()) { if (("education_" + item.wire).equals(key)) { return Optional.of(item); } }
            return Optional.empty();
        }
    }
    public enum SourceBasis {
        RAW("raw_skill_observation"), TOTAL_MARTIAL("native_character_total_skill_callback");
        private final String wire;
        SourceBasis(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum BindingStatus {
        RESOLVED("resolved"), KNOWN_NULL("known_null"), UNAVAILABLE("unavailable");
        private final String wire;
        BindingStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static BindingStatus fromWire(String value) {
            for (BindingStatus status : values()) { if (status.wire.equals(value)) { return status; } }
            throw new IllegalArgumentException("unknown guardian-profile binding status");
        }
    }
    /** Canonical JSON residue is copied only by the boundary codec; business code never inspects it. */
    public record PreservedJson(String canonicalJson) {
        public PreservedJson { Objects.requireNonNull(canonicalJson); }
    }
    public record Pair(long childFullId, long guardianFullId) {
        public Pair { characterId(childFullId); characterId(guardianFullId); }
    }
    public record SkillObservation(boolean available, Integer value, String unavailableReason) {
        public SkillObservation {
            StrictJson.require(available ? value != null && unavailableReason == null
                    : value == null && reason(unavailableReason), "signed skill availability/value/reason mismatch");
        }
    }
    public record TotalMartial(Long targetCharacterId, SkillObservation observation) {
        public TotalMartial { if (targetCharacterId != null) { characterId(targetCharacterId); } Objects.requireNonNull(observation); }
    }
    public record GuardianProfile(Long childCharacterId, Long characterId, BigInteger owningNativeRevision,
            BindingStatus bindingStatus, Map<Skill, SkillObservation> skills, Optional<TotalMartial> totalMartial,
            PreservedJson original) {
        public GuardianProfile {
            if (childCharacterId != null) { EducationPreferenceModel.characterId(childCharacterId); }
            if (characterId != null) { EducationPreferenceModel.characterId(characterId); }
            uint64(owningNativeRevision); Objects.requireNonNull(bindingStatus); skills = Map.copyOf(skills);
            StrictJson.require(skills.size() == Skill.values().length, "complete five-skill profile inventory required");
            for (Skill skill : Skill.values()) { Objects.requireNonNull(skills.get(skill)); }
            Objects.requireNonNull(totalMartial); Objects.requireNonNull(original);
            if (bindingStatus == BindingStatus.RESOLVED) {
                StrictJson.require(childCharacterId != null && childCharacterId != 0 && characterId != null && characterId != 0,
                        "resolved guardian profile requires complete nonzero IDs");
            }
            for (SkillObservation skill : skills.values()) {
                StrictJson.require(!skill.available() || bindingStatus == BindingStatus.RESOLVED, "available skill requires resolved binding");
            }
            totalMartial.ifPresent(total -> {
                StrictJson.require(Objects.equals(total.targetCharacterId(), characterId), "total-martial/profile target mismatch");
                StrictJson.require(!total.observation().available() || bindingStatus == BindingStatus.RESOLVED, "available total requires resolved binding");
            });
        }
    }
    public sealed interface Observation permits Skipped, RequestObservation { }
    /** Original no-intent observations retain their slots in the outer list and are not ranked. */
    public record Skipped() implements Observation { }
    public record RequestObservation(Pair intent, List<Integer> occurrenceIndices, FocusManagement focusManagement,
            PreservedJson focusSourceFrame, PreservedJson guardianQueryFrame, BigInteger queryNativeRevision,
            Optional<GuardianProfile> profile) implements Observation {
        public RequestObservation {
            Objects.requireNonNull(intent); occurrenceIndices = List.copyOf(occurrenceIndices);
            StrictJson.require(!occurrenceIndices.isEmpty(), "original occurrence group must not be empty");
            occurrenceIndices.forEach(index -> StrictJson.require(index != null && index >= 0, "nonnegative occurrence index required"));
            Objects.requireNonNull(focusManagement); Objects.requireNonNull(focusSourceFrame); Objects.requireNonNull(guardianQueryFrame);
            uint64(queryNativeRevision); Objects.requireNonNull(profile);
        }
    }
    public record Input(List<Observation> observations) {
        public Input { observations = List.copyOf(observations); }
    }
    public record Component(boolean available, Integer rawValue, SourceBasis sourceBasis,
            int weightNumerator, BigInteger weightedNumerator, String unavailableReason) {
        public Component {
            Objects.requireNonNull(sourceBasis);
            StrictJson.require(weightNumerator == 1 || weightNumerator == 2, "existing denominator-five weights required");
            StrictJson.require(available ? rawValue != null && weightedNumerator != null && unavailableReason == null
                    : rawValue == null && weightedNumerator == null && reason(unavailableReason), "component availability mismatch");
            StrictJson.require(!available || weightedNumerator.equals(BigInteger.valueOf(rawValue).multiply(BigInteger.valueOf(weightNumerator))),
                    "component weighted numerator differs from exact original operand");
        }
    }
    public record Score(BigInteger numerator) { public Score { Objects.requireNonNull(numerator); } public int denominator() { return 5; } }
    public record CandidateRecord(int observationIndex, Pair pair, int firstOccurrenceIndex,
            boolean requestProfileIdentityBound, FocusManagement focusManagement, PreservedJson focusSourceFrame,
            PreservedJson guardianQueryFrame, Optional<GuardianProfile> rawProfile, Component focus, Component learning,
            Optional<Score> knownWeightedScore, Optional<Score> completeWeightedScore) {
        public CandidateRecord {
            StrictJson.require(observationIndex >= 0 && firstOccurrenceIndex >= 0, "nonnegative retained indices required");
            Objects.requireNonNull(pair); Objects.requireNonNull(focusManagement); Objects.requireNonNull(focusSourceFrame);
            Objects.requireNonNull(guardianQueryFrame); Objects.requireNonNull(rawProfile); Objects.requireNonNull(focus);
            Objects.requireNonNull(learning); Objects.requireNonNull(knownWeightedScore); Objects.requireNonNull(completeWeightedScore);
        }
    }
    public record Result(List<CandidateRecord> candidates, List<Integer> orderedObservationIndices) {
        public Result { candidates = List.copyOf(candidates); orderedObservationIndices = List.copyOf(orderedObservationIndices); }
    }
    static boolean reason(String value) {
        if (value == null || value.isEmpty()) { return false; }
        StrictJson.text(value);
        return value.codePointCount(0, value.length()) <= 512;
    }
    static void characterId(long value) { StrictJson.require(value >= 0 && value <= 4_294_967_294L, "native uint32 character ID range"); }
    static void uint64(BigInteger value) { StrictJson.require(value != null && value.signum() >= 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "native uint64 revision range"); }
}
