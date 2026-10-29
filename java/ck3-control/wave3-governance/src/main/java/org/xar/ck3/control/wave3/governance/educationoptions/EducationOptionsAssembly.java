package org.xar.ck3.control.wave3.governance.educationoptions;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel.Availability;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel.Pair;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel.Row;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel.Rows;

/** Existing Service selected-key filtering and selected/all-off request assembly, without native calls or admission. */
public final class EducationOptionsAssembly {
    public static final String INTERACTION = "educate_child_interaction";
    private EducationOptionsAssembly() { }
    public enum Variant {
        SELECTED("observed_selected_options"), ALL_OFF("explicit_all_options_off");
        private final String wire;
        Variant(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record RequestIntent(Pair pair, List<String> requestedOptionKeys) {
        public RequestIntent {
            Objects.requireNonNull(pair); requestedOptionKeys = List.copyOf(requestedOptionKeys);
            requestedOptionKeys.forEach(EducationOptionsModel::key);
        }
    }
    public record Observation(Optional<Pair> candidatePair, Optional<RequestIntent> selectedIntent) {
        public Observation {
            candidatePair = Objects.requireNonNull(candidatePair); selectedIntent = Objects.requireNonNull(selectedIntent);
            requireDomain(selectedIntent.isEmpty() || candidatePair.isPresent()
                    && selectedIntent.orElseThrow().pair().equals(candidatePair.orElseThrow()), "selected intent differs from observed candidate pair");
        }
    }
    public record Attempt(int observationIndex, RequestIntent intent, Variant variant) {
        public Attempt { requireDomain(observationIndex >= 0, "nonnegative observation index required"); Objects.requireNonNull(intent); Objects.requireNonNull(variant); }
    }
    /** Candidate availability comes from the existing native-final-pair owner; this method cannot infer a guardian. */
    public static Optional<RequestIntent> selectedIntent(Optional<Pair> observedCandidate, Optional<Rows> optionRows) {
        Objects.requireNonNull(observedCandidate); Objects.requireNonNull(optionRows);
        if (observedCandidate.isEmpty() || optionRows.isEmpty() || optionRows.orElseThrow().status() != Availability.AVAILABLE) { return Optional.empty(); }
        LinkedHashSet<String> keys = new LinkedHashSet<>();
        for (Row row : optionRows.orElseThrow().rows()) {
            if (!row.ordinalSelected()) { continue; }
            if (row.canonicalFlagKey() == null) { return Optional.empty(); }
            keys.add(row.canonicalFlagKey());
        }
        return Optional.of(new RequestIntent(observedCandidate.orElseThrow(), List.copyOf(keys)));
    }
    /** Preference's actual observed order is an input. Source, fresh preflight, legality and UNKNOWN guards remain with their owners. */
    public static List<Attempt> attempts(List<Observation> observations, List<Integer> orderedObservationIndices) {
        List<Observation> owned = List.copyOf(observations); List<Integer> order = List.copyOf(orderedObservationIndices);
        for (Integer index : order) { requireDomain(index != null && index >= 0 && index < owned.size(), "preference index outside actual observations"); }
        List<Attempt> result = new ArrayList<>();
        for (Variant variant : Variant.values()) {
            for (int index : order) {
                Observation observation = owned.get(index); Optional<RequestIntent> original = observation.selectedIntent();
                if (variant == Variant.SELECTED) {
                    original.ifPresent(intent -> result.add(new Attempt(index, intent, variant)));
                } else {
                    if (original.isPresent() && original.orElseThrow().requestedOptionKeys().isEmpty()) { continue; }
                    requireDomain(observation.candidatePair().isPresent(), "all-off intent requires the actual observed candidate pair");
                    result.add(new Attempt(index, new RequestIntent(observation.candidatePair().orElseThrow(), List.of()), variant));
                }
            }
        }
        return List.copyOf(result);
    }
    private static void requireDomain(boolean valid, String reason) {
        if (!valid) { throw new ProjectionDomainRejection(reason); }
    }
}
