package org.xar.ck3.control.wave2.governance.educationpreference;

import java.math.BigInteger;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusState;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.*;

/** Existing 2/5 focus + 1/5 learning preference, confined to identical operand/source slots. */
public final class EducationRequestPreference {
    public static final String POLICY = "source_informed_request_guardian_skill_preference_12004.v2";
    private static final String IDENTITY_UNAVAILABLE = "request_guardian_profile_identity_unavailable";
    private EducationRequestPreference() { }
    private record Signature(boolean focusAvailable, boolean learningAvailable, SourceBasis focusBasis, SourceBasis learningBasis) { }

    public static Result order(Input input) {
        List<CandidateRecord> candidates = new ArrayList<>();
        Map<Signature, List<CandidateRecord>> groups = new LinkedHashMap<>();
        for (int index = 0; index < input.observations().size(); index++) {
            if (!(input.observations().get(index) instanceof RequestObservation observation)) { continue; }
            GuardianProfile profile = observation.profile().orElse(null);
            boolean bound = profile != null && profile.bindingStatus() == BindingStatus.RESOLVED
                    && profile.childCharacterId() != null && profile.childCharacterId() == observation.intent().childFullId()
                    && profile.characterId() != null && profile.characterId() == observation.intent().guardianFullId()
                    && profile.owningNativeRevision().equals(observation.queryNativeRevision());
            Optional<Skill> focusedSkill = observation.focusManagement().state() == FocusState.EDUCATION_FOCUS_PRESENT
                    ? Skill.forFocus(observation.focusManagement().currentKey()) : Optional.empty();
            Component focus;
            if (focusedSkill.orElse(null) == Skill.MARTIAL) {
                TotalMartial total = bound ? profile.totalMartial().orElse(null) : null;
                boolean sameTarget = total != null && total.targetCharacterId() != null
                        && total.targetCharacterId() == observation.intent().guardianFullId();
                focus = component(sameTarget ? total.observation() : null, 2,
                        bound ? "request_guardian_total_martial_callback_not_observed" : IDENTITY_UNAVAILABLE,
                        SourceBasis.TOTAL_MARTIAL);
            } else {
                focus = component(bound && focusedSkill.isPresent() ? profile.skills().get(focusedSkill.get()) : null,
                        2, bound ? "current_child_education_focus_not_observed" : IDENTITY_UNAVAILABLE, SourceBasis.RAW);
            }
            Component learning = component(bound ? profile.skills().get(Skill.LEARNING) : null, 1, IDENTITY_UNAVAILABLE, SourceBasis.RAW);
            Optional<Score> score = focus.available() || learning.available()
                    ? Optional.of(new Score((focus.available() ? focus.weightedNumerator() : BigInteger.ZERO)
                            .add(learning.available() ? learning.weightedNumerator() : BigInteger.ZERO))) : Optional.empty();
            CandidateRecord record = new CandidateRecord(index, observation.intent(), observation.occurrenceIndices().getFirst(),
                    bound, observation.focusManagement(), observation.focusSourceFrame(), observation.guardianQueryFrame(),
                    observation.profile(), focus, learning, score, focus.available() && learning.available() ? score : Optional.empty());
            candidates.add(record); groups.computeIfAbsent(signature(record), ignored -> new ArrayList<>()).add(record);
        }
        Comparator<CandidateRecord> tie = Comparator.comparingInt(CandidateRecord::firstOccurrenceIndex)
                .thenComparingLong(record -> record.pair().childFullId()).thenComparingLong(record -> record.pair().guardianFullId())
                .thenComparingInt(CandidateRecord::observationIndex);
        Map<Signature, ArrayDeque<CandidateRecord>> orderedGroups = new LinkedHashMap<>();
        groups.forEach((key, records) -> {
            Comparator<CandidateRecord> comparator = key.focusAvailable() || key.learningAvailable()
                    ? Comparator.<CandidateRecord, BigInteger>comparing(record -> record.knownWeightedScore().orElseThrow().numerator())
                            .reversed().thenComparing(tie) : tie;
            records.sort(comparator); orderedGroups.put(key, new ArrayDeque<>(records));
        });
        List<Integer> ordered = new ArrayList<>();
        for (CandidateRecord record : candidates) { ordered.add(orderedGroups.get(signature(record)).removeFirst().observationIndex()); }
        return new Result(candidates, ordered);
    }
    private static Signature signature(CandidateRecord record) {
        return new Signature(record.focus().available(), record.learning().available(), record.focus().sourceBasis(), record.learning().sourceBasis());
    }
    private static Component component(SkillObservation field, int weight, String missingReason, SourceBasis basis) {
        boolean available = field != null && field.available();
        Integer raw = available ? field.value() : null;
        return new Component(available, raw, basis, weight,
                available ? BigInteger.valueOf(raw).multiply(BigInteger.valueOf(weight)) : null,
                available ? null : field != null ? field.unavailableReason() : missingReason);
    }
}
