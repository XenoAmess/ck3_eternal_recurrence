package org.xar.ck3.control.wave3.governance.educationprovider;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.governance.education.EducationInputs.Status;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Binding;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.CultureParameter;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.EducationTraits;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.ExpectedChild;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.FamilyInventory;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Occurrence;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Provider;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.ProviderChild;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Request;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.SelectedChild;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Validation;

/** Complete pure roster/subread validation. Native export qualification stays with its original owner. */
public final class EducationProviderValidator {
    private EducationProviderValidator() { }
    public static final String SOURCE = "same_query_actual4_child_education_inputs";
    public static final String ROLE = "current_living_actual_child_of_first_heir";
    public static final String CULTURE_KEY = "better_ward_education";
    public static final String GUARDIAN_UNKNOWN = "authoritative_educator_identity_not_observed";
    public static final String RITE_UNKNOWN = "target_rite_education_parameters_not_observed";
    public static final String VARIABLES_UNKNOWN = "typed_target_variable_value_access_not_wired";
    public static final String PARTIAL_REASON = "education_child_inputs_partially_observed";
    public static final List<String> EDUCATION_TRAIT_KEYS = traitKeys();

    public static Validation validate(Request request) {
        if (request.provider() == null) { return new Validation(null, List.of(), false, false); }
        require(request.callerCapturedSourceQualified(), "education provider object lacks qualified captured source");
        Binding binding = request.binding(); Provider provider = request.provider();
        require(binding != null, "provider binding required");
        int heir = binding.normalizedFamilyHeir() == null ? -1 : binding.normalizedFamilyHeir();
        require(binding.frame().heirCharacter().signed() == heir, "normalized heir binding changed");
        require(!binding.requestId().isEmpty(), "original request unavailable");
        require(binding.frame().nativeRevision().signum() > 0 && binding.frame().nativeRevision().bitLength() <= 64,
                "native revision must be positive uint64");
        require(provider.requestId().equals(binding.requestId()) && provider.frame().equals(binding.frame()), "same-query binding changed");
        require(provider.queriedEducationTraitKeys().equals(EDUCATION_TRAIT_KEYS), "queried trait catalog changed");
        boolean all = provider.status() == Status.AVAILABLE;
        boolean partial = provider.status() == Status.PARTIAL;
        boolean unavailable = provider.status() == Status.UNAVAILABLE;
        require(all || partial || unavailable, "provider status malformed");
        require(provider.rosterComplete() == !unavailable && provider.collectionAvailable() == !unavailable
                && provider.childObservationComplete() == all, "provider completeness malformed");
        require(provider.rows().size() <= 256, "provider child inventory exceeds 256");
        if (all) { require(provider.unavailableReason() == null, "available provider reason must be null"); }
        else { reason(provider.unavailableReason(), "provider"); }
        if (unavailable) {
            require(provider.rows().isEmpty(), "unavailable provider must retain empty unknown rows");
            return new Validation(provider, List.of(), false, false);
        }
        if (partial) { require(PARTIAL_REASON.equals(provider.unavailableReason()), "partial provider reason changed"); }
        List<ExpectedChild> expected = expectedChildren(request.family(), binding);
        require(provider.rows().size() == expected.size(), "provider child inventory incomplete");
        boolean allAvailable = true;
        for (int index = 0; index < expected.size(); index++) {
            ProviderChild row = provider.rows().get(index); ExpectedChild child = expected.get(index);
            require(row.childFullId() == child.childFullId() && row.occurrenceIndices().equals(child.occurrenceIndices()),
                    "provider child inventory order or occurrence changed");
            require(ROLE.equals(row.roleSource()), "provider child role changed");
            require(row.guardianFullId() == null && row.guardianCultureParameter() == null,
                    "unobserved guardian must retain null");
            require(GUARDIAN_UNKNOWN.equals(row.guardianUnavailableReason()) && RITE_UNKNOWN.equals(row.riteUnavailableReason())
                    && VARIABLES_UNKNOWN.equals(row.educationVariablesUnavailableReason()), "unobserved authoritative reason changed");
            boolean traits = traits(row.educationTraits()); boolean culture = culture(row.cultureParameter());
            allAvailable = allAvailable && traits && culture;
        }
        require(all == allAvailable, "provider status differs from trait and culture subreads");
        return new Validation(provider, expected, false, false);
    }

    private record Classification(boolean alive, boolean child) { }
    private static List<ExpectedChild> expectedChildren(FamilyInventory family, Binding binding) {
        require(family != null && family.descendantsAvailable() && family.rosterComplete() && family.familyPresent()
                && (family.selectedInputsStatus() == Status.AVAILABLE || family.selectedInputsStatus() == Status.PARTIAL),
                "provider lacks complete same-query child roster");
        require(binding.frame().equals(family.descendantFrame()) && binding.frame().equals(family.selectedInputsFrame()),
                "provider child frame changed");
        require(family.nativeChildCount() >= 0 && family.nativeChildCount() <= 4096
                && family.rawRows().size() == family.nativeChildCount() && family.dataPointerPresent() != null
                && (family.nativeChildCount() == 0 || family.dataPointerPresent()), "raw roster proof incomplete");
        Map<Long, List<Integer>> groups = new LinkedHashMap<>();
        Map<Long, Classification> classifications = new LinkedHashMap<>();
        for (int index = 0; index < family.rawRows().size(); index++) {
            Occurrence row = family.rawRows().get(index);
            require(row.occurrenceIndex() == index && row.rawFullId() >= 0 && row.rawFullId() <= 0xffff_ffffL
                    && row.generationValid() && row.alive() != null && (!row.alive() || row.childOfHeir() != null),
                    "raw occurrence classification unavailable");
            Classification current = new Classification(row.alive(), row.alive() && Boolean.TRUE.equals(row.childOfHeir()));
            Classification prior = classifications.putIfAbsent(row.rawFullId(), current);
            require(prior == null || prior.equals(current), "duplicate occurrence classification changed");
            if (current.alive() && current.child()) { groups.computeIfAbsent(row.rawFullId(), ignored -> new ArrayList<>()).add(index); }
        }
        require(family.selectedChildren().size() <= 256 && family.selectedChildren().size() == groups.size(),
                "selected child roster incomplete");
        List<ExpectedChild> result = new ArrayList<>(); int index = 0;
        for (Map.Entry<Long, List<Integer>> group : groups.entrySet()) {
            SelectedChild row = family.selectedChildren().get(index++); indices(row.occurrenceIndices());
            require(row.characterId().raw() == group.getKey() && row.occurrenceIndices().equals(group.getValue()),
                    "selected child order changed");
            result.add(new ExpectedChild(group.getKey(), group.getValue()));
        }
        return List.copyOf(result);
    }
    private static boolean traits(EducationTraits value) {
        require(value != null, "education traits required");
        if (value.available()) {
            require(value.unavailableReason() == null && value.presentTraitKeys() != null && value.presentTraitKeys().size() <= 25,
                    "available education traits malformed");
            List<String> expected = EDUCATION_TRAIT_KEYS.stream().filter(value.presentTraitKeys()::contains).toList();
            require(value.presentTraitKeys().equals(expected), "education trait key order or membership changed");
        } else { reason(value.unavailableReason(), "education traits"); require(value.presentTraitKeys() == null, "unavailable traits must retain null"); }
        return value.available();
    }
    private static boolean culture(CultureParameter value) {
        require(value != null && CULTURE_KEY.equals(value.key()), "education culture key changed");
        require(value.cultureFullId() == null || value.cultureFullId() >= 0 && value.cultureFullId() <= 0xffff_ffffL,
                "culture identity must be uint32");
        if (value.available()) { require(value.cultureFullId() != null && value.value() != null && value.unavailableReason() == null,
                "available culture contents malformed"); }
        else { reason(value.unavailableReason(), "education culture"); require(value.value() == null, "unavailable culture must retain null"); }
        return value.available();
    }
    static void indices(List<Integer> value) {
        require(value != null && !value.isEmpty() && value.size() <= 4096, "occurrence group unavailable");
        int previous = -1;
        for (Integer index : value) { require(index != null && index >= 0 && index > previous, "occurrence order changed"); previous = index; }
    }
    static void reason(String value, String name) { require(value != null && !value.isEmpty(), name + " unavailable reason required"); }
    static void require(boolean condition, String reason) { if (!condition) { throw new ProjectionDomainRejection(reason); } }
    private static List<String> traitKeys() {
        List<String> result = new ArrayList<>();
        for (String skill : List.of("diplomacy", "martial", "stewardship", "intrigue", "learning")) {
            for (int rank = 1; rank <= 5; rank++) { result.add("education_" + skill + "_" + rank); }
        }
        return List.copyOf(result);
    }
}
