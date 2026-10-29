package org.xar.ck3.control.governance.education;

import static org.xar.ck3.control.governance.education.EducationInputs.*;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Same-query identity join and first-seen occurrence grouping, with no acquisition. */
final class EducationGeneration {
    private EducationGeneration() { }
    static Generation derive(Descendants source) {
        if (source == null) {
            return new Generation(null, Status.UNAVAILABLE, "descendants_not_observed", Status.NOT_OBSERVED,
                    false, false, null, 0, null, null, null, Status.NOT_OBSERVED, false, List.of());
        }
        ChildInputs inputs = source.childInputs();
        Status inputStatus = inputs == null ? Status.NOT_OBSERVED : inputs.status();
        if (source.status() != Status.AVAILABLE || !source.rosterComplete()) {
            return new Generation(source.frame(), Status.UNAVAILABLE,
                    source.unavailableReason() == null ? "descendant_roster_incomplete" : source.unavailableReason(),
                    source.status(), source.rosterComplete(), false, null, 0, null, null, null, inputStatus, false, List.of());
        }
        Map<Integer, List<Integer>> groups = new LinkedHashMap<>();
        Map<Integer, Long> rawIds = new LinkedHashMap<>();
        boolean classified = true;
        for (Occurrence occurrence : source.occurrences()) {
            if (!occurrence.generationValid() || Boolean.FALSE.equals(occurrence.alive()) || Boolean.FALSE.equals(occurrence.childOfHeir())) { continue; }
            if (!Boolean.TRUE.equals(occurrence.alive()) || !Boolean.TRUE.equals(occurrence.childOfHeir())) { classified = false; continue; }
            int character = (int) occurrence.rawCharacterId();
            groups.computeIfAbsent(character, ignored -> new ArrayList<>()).add(occurrence.index());
            rawIds.put(character, occurrence.rawCharacterId());
        }
        Map<Integer, ChildRead> byId = new LinkedHashMap<>();
        Status missingStatus = inputs == null ? Status.NOT_OBSERVED : Status.UNAVAILABLE;
        String missingReason = inputs == null ? "child_inputs_not_observed" : inputs.unavailableReason() == null ? "child_input_row_unavailable" : inputs.unavailableReason();
        if (inputs != null) {
            if (!inputs.frame().equals(source.frame())) { missingReason = "child_inputs_frame_mismatch"; }
            else if (inputs.status() != Status.UNAVAILABLE) {
                for (ChildRead read : inputs.rows()) { byId.put(read.characterId(), read); }
                if (byId.size() != inputs.rows().size()) { byId.clear(); missingReason = "child_input_identity_duplicate"; }
            }
        }
        List<Child> children = new ArrayList<>();
        for (Map.Entry<Integer, List<Integer>> group : groups.entrySet()) {
            ChildRead read = byId.get(group.getKey());
            String rowMissing = missingReason;
            if (read != null && !read.occurrenceIndices().equals(group.getValue())) { read = null; rowMissing = "child_input_occurrence_group_mismatch"; }
            List<Availability> availability = new ArrayList<>();
            boolean complete = true;
            for (LeafKind kind : LeafKind.values()) {
                Leaf leaf = read == null ? null : read.leaf(kind);
                Availability current = leaf == null ? new Availability(read == null ? missingStatus : Status.NOT_OBSERVED,
                        read == null ? rowMissing : EducationDecisionComposer.leafName(kind) + "_not_observed") : new Availability(leaf.status(), leaf.unavailableReason());
                availability.add(current);
                if (kind != LeafKind.EDUCATION_TRAITS && current.status() != Status.AVAILABLE) { complete = false; }
            }
            children.add(new Child(group.getKey(), rawIds.get(group.getKey()), group.getValue(), read, availability, complete));
        }
        boolean complete = classified && children.stream().allMatch(Child::complete);
        return new Generation(source.frame(), complete ? Status.AVAILABLE : Status.PARTIAL,
                complete ? null : !classified ? "living_child_classification_incomplete" : "one_or_more_child_inputs_not_available",
                source.status(), true, classified, source.occurrences().size(), groups.size(), classified ? groups.size() : null,
                groups.isEmpty() ? classified ? Boolean.FALSE : null : Boolean.TRUE,
                groups.isEmpty() ? classified ? Boolean.TRUE : null : Boolean.FALSE, inputStatus, complete, children);
    }
}
