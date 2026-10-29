package org.xar.ck3.control.governance.education;

import static org.xar.ck3.control.governance.education.EducationInputs.*;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** The exact reached stock-source variant: no educator selection supplied by the family producer. */
final class EducationPointProjection {
    private record Component(String key, String lines, String operation, Boolean predicate, Integer value,
                             String reason, Integer literal, List<Integer> possibilities, int factorNumerator,
                             int factorDenominator, List<Component> beforeCulture) { }
    private EducationPointProjection() { }
    static ObjectNode emit(Child child, Boolean affinityValue, Boolean disaffinityValue) {
        boolean idAvailable = child.characterId() != -1;
        Leaf leaf = child.read() == null ? null : child.read().pointTraits();
        Traits traits = idAvailable && leaf != null && leaf.status() == Status.AVAILABLE ? (Traits) leaf.facts() : null;
        String childReason = !idAvailable ? "child_complete_character_id_unavailable" : leaf == null ? "education_point_traits_not_observed"
                : leaf.status() == Status.UNAVAILABLE ? leaf.unavailableReason() : "child_trait_predicate_unavailable";
        List<Component> success = List.of(
                conditional("child_success_good3", "effects:302-305", predicate(traits, "intellect_good_3"), 20, childReason, "add"),
                conditional("child_success_good2", "effects:306-309", predicate(traits, "intellect_good_2"), 15, childReason, "add"),
                conditional("child_success_good1_or_shrewd", "effects:310-316", predicate(traits, "intellect_good_1", "shrewd"), 10, childReason, "add"));
        List<Component> failure = List.of(
                conditional("child_failure_bad3_or_inbred", "effects:384-390", predicate(traits, "intellect_bad_3", "inbred"), 20, childReason, "add"),
                conditional("child_failure_bad2", "effects:391-394", predicate(traits, "intellect_bad_2"), 15, childReason, "add"),
                conditional("child_failure_bad1_or_dull", "effects:395-401", predicate(traits, "intellect_bad_1", "dull"), 10, childReason, "add"));
        Component successChain = unknownChain("educator_success_trait_chain", "effects:318-339");
        Component failureChain = unknownChain("educator_failure_trait_chain", "effects:403-429");
        Component focus = unknownSkill("educator_focus_skill", "effects:340-344; values:5", 2, 5);
        Component learning = unknownSkill("educator_learning", "effects:345-349; values:6", 1, 5);
        Component culture = conditional("educator_culture", "effects:350-354", null, 10, "selected_educator_culture_parameter_unavailable", "value");
        Component educatorSuccess = new Component("educator_success_expression", "effects:318-357", "add", null, null,
                "educator_success_expression_unavailable", null, null, 0, 0, List.of(successChain, focus, learning));
        Component educatorFailure = new Component("educator_failure_expression", "effects:403-429", "add", null, null,
                "educator_presence_unavailable", null, null, 0, 0, null);
        Component affinity = conditional("child_focus_affinity", "effects:359-363; values:3", idAvailable ? affinityValue : null, 20, "qualified_child_focus_affinity_unavailable", "add");
        Component disaffinity = conditional("child_focus_disaffinity", "effects:365-369; values:4", idAvailable ? disaffinityValue : null, -20, "qualified_child_focus_disaffinity_unavailable", "add");
        Component house = conditional("educator_house", "effects:371-374", null, 5, "selected_educator_house_parameter_unavailable", "add");
        Component noEducator = conditional("no_educator_failure", "effects:430-435", null, 20, "educator_presence_unavailable", "add");
        List<Component> all = new ArrayList<>(success); all.addAll(List.of(successChain, focus, learning, culture, educatorSuccess, affinity, disaffinity, house));
        all.addAll(failure); all.addAll(List.of(failureChain, educatorFailure, noEducator));
        ObjectNode result = StrictJson.object(); result.put("schema", "education_point_source_modifiers_12004.v1");
        result.put("qualification", "pure_source_components_only"); result.put("source_packet_sha256", "8b575eec9130fb1e4fbcfb380b2870e12fdb51c76993259ee88ef26f52e69230");
        if (idAvailable) { result.put("child_character_id", child.characterId()); } else { result.putNull("child_character_id"); }
        result.put("child_identity_available", idAvailable); EducationDecisionComposer.nullable(result, "child_identity_unavailable_reason", idAvailable ? null : "child_complete_character_id_unavailable");
        result.putNull("educator_present"); result.putNull("educator_id"); result.put("educator_values_bound", false);
        ObjectNode components = result.putObject("components"); for (Component item : all) { components.set(item.key(), component(item)); }
        result.set("child_success_traits", sum(success, 0)); result.set("child_failure_traits", sum(failure, 0));
        List<Component> successTotal = new ArrayList<>(success); successTotal.addAll(List.of(educatorSuccess, affinity, disaffinity, house));
        List<Component> failureTotal = new ArrayList<>(failure); failureTotal.addAll(List.of(educatorFailure, noEducator));
        result.set("success_source_components", sum(successTotal, 60)); result.set("failure_source_components", sum(failureTotal, 40));
        result.putNull("normalized_success_probability"); result.put("full_native_ast_ready", false); result.put("education_outcome_ready", false); result.put("native_action_performed", false);
        return result;
    }
    private static Boolean predicate(Traits traits, String... keys) {
        if (traits == null) { return null; }
        for (String key : keys) { if (traits.present().contains(key)) { return true; } }
        return false;
    }
    private static Component conditional(String key, String lines, Boolean predicate, int amount, String reason, String operation) {
        return new Component(key, lines, operation, predicate, predicate == null ? null : predicate ? amount : 0, reason, amount, null, 0, 0, null);
    }
    private static Component unknownChain(String key, String lines) { return new Component(key, lines, "value", null, null, "educator_presence_unavailable", null, List.of(0, 5, 10, 15), 0, 0, null); }
    private static Component unknownSkill(String key, String lines, int numerator, int denominator) { return new Component(key, lines, "add", null, null, "selected_educator_skill_unavailable", null, null, numerator, denominator, null); }
    private static ObjectNode component(Component value) {
        ObjectNode result = StrictJson.object(); result.put("key", value.key()); result.put("source_lines", value.lines()); result.put("source_operation", value.operation());
        EducationDecisionComposer.nullable(result, "predicate", value.predicate()); result.put("available", value.value() != null); rational(result, "source_value", value.value(), 1);
        EducationDecisionComposer.nullable(result, "unavailable_reason", value.value() == null ? value.reason() : null);
        if (value.literal() != null) { result.put("literal_amount", value.literal()); EducationDecisionComposer.nullable(result, "operation_applied", value.predicate()); }
        if (value.possibilities() != null) { ArrayNode possible = result.putArray("possible_source_values"); value.possibilities().forEach(possible::add); }
        if (value.factorDenominator() != 0) { rational(result, "factor", value.factorNumerator(), value.factorDenominator()); }
        if (value.beforeCulture() != null) {
            EducationDecisionComposer.strings(result.putArray("ordered_component_keys"), List.of("educator_success_trait_chain", "educator_focus_skill", "educator_learning", "educator_culture"));
            result.set("before_culture", sum(value.beforeCulture(), 0)); result.put("culture_statement", "value = 10");
        }
        return result;
    }
    private static ObjectNode sum(List<Component> values, int base) {
        int known = base; List<String> missing = new ArrayList<>();
        for (Component component : values) { if (component.value() == null) { missing.add(component.key()); } else { known += component.value(); } }
        ObjectNode result = StrictJson.object(); result.put("available", missing.isEmpty()); rational(result, "source_value", missing.isEmpty() ? known : null, 1);
        rational(result, "known_source_subtotal", known, 1); EducationDecisionComposer.strings(result.putArray("unavailable_components"), missing); result.put("qualification", "source_component_sum"); return result;
    }
    private static void rational(ObjectNode target, String key, Integer numerator, int denominator) {
        if (numerator == null) { target.putNull(key); } else { ObjectNode value = target.putObject(key); value.put("numerator", numerator); value.put("denominator", denominator); }
    }
}
