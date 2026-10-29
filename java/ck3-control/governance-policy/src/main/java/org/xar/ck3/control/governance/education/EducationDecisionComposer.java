package org.xar.ck3.control.governance.education;

import static org.xar.ck3.control.governance.education.EducationInputs.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Production education projection. JSON nodes are confined to this wire emitter. */
public final class EducationDecisionComposer {
    public static final String SCHEMA = "family_generation_education_decision_inputs_v1";
    public record Skill(String name, List<String> positive, String negative) {
        public Skill { positive = List.copyOf(positive); }
    }
    public static final List<Skill> SKILLS = List.of(new Skill("diplomacy", List.of("charming", "curious"), "bossy"),
            new Skill("martial", List.of("rowdy", "bossy"), "curious"), new Skill("stewardship", List.of("bossy", "pensive"), "charming"),
            new Skill("intrigue", List.of("charming", "rowdy"), "pensive"), new Skill("learning", List.of("pensive", "curious"), "rowdy"));
    private EducationDecisionComposer() { }
    public static byte[] compose(byte[] input) {
        return EducationInputCodec.encode(emit(EducationGeneration.derive(EducationInputCodec.decode(input))));
    }
    static String leafName(LeafKind kind) {
        return switch (kind) { case VALUES -> "values"; case CHILDHOOD_TRAITS -> "childhood_traits"; case NATIVE_FOCUS -> "native_focus";
            case EDUCATION_POINT_TRAITS -> "education_point_traits"; case EDUCATION_TRAITS -> "education_traits"; };
    }
    private static ObjectNode emit(Generation generation) {
        ObjectNode result = StrictJson.object(); result.put("schema", SCHEMA);
        result.put("qualification", "current_native_child_inputs_and_stock_source_projection");
        frame(result, generation.frame()); common(result, generation);
        result.set("children", generation(generation));
        ArrayNode rows = result.putArray("education_rows");
        for (Child child : generation.rows()) {
            ObjectNode row = rows.addObject(); identity(row, child);
            Leaf observedFocus = child.read() == null ? null : child.read().nativeFocus();
            ObjectNode focus = focus(observedFocus); row.set("current_focus", focus);
            row.set("current_court_owner", courtOwner(child, generation.frame()));
            Leaf childhood = child.read() == null ? null : child.read().childhoodTraits();
            Traits traits = childhood != null && childhood.status() == Status.AVAILABLE ? (Traits) childhood.facts() : null;
            ArrayNode options = row.putArray("stock_skill_options"); JsonNode selected = null;
            for (Skill skill : SKILLS) {
                Boolean affinity = traits == null ? null : skill.positive().stream().anyMatch(traits.present()::contains);
                Boolean disaffinity = traits == null ? null : traits.present().contains(skill.negative());
                ObjectNode option = options.addObject(); option.put("skill_parameter", skill.name()); option.put("focus_key", "education_" + skill.name());
                ObjectNode positive = option.putObject("childhood_affinity"); positive.put("available", affinity != null); nullable(positive, "raw_value", affinity);
                positive.put("basis", "stock_childhood_trait_trigger_source_projection"); strings(positive.putArray("required_any_trait_keys"), skill.positive());
                ObjectNode negative = option.putObject("childhood_disaffinity"); negative.put("available", disaffinity != null); nullable(negative, "raw_value", disaffinity);
                negative.put("basis", "stock_childhood_trait_trigger_source_projection"); negative.put("required_trait_key", skill.negative());
                option.set("source_point_components", EducationPointProjection.emit(child, affinity, disaffinity));
                if (focus.get("available").booleanValue() && option.get("focus_key").equals(focus.get("key"))) { selected = option; }
            }
            if (selected == null) { row.putNull("current_education_skill_inputs"); } else { row.set("current_education_skill_inputs", selected.deepCopy()); }
        }
        result.put("source_projection_only", true); result.put("native_effect_invoked", false); result.put("guardian_role_equivalence_qualified", false);
        result.put("educator_selection_observed", false); result.put("education_outcome_observed", false); return result;
    }
    private static ObjectNode generation(Generation value) {
        ObjectNode result = StrictJson.object(); result.put("schema", "family_generation_education_inputs_v1");
        result.put("source", "derived_current_first_heir_child_education_inputs"); result.put("status", value.status().wire());
        nullable(result, "unavailable_reason", value.unavailableReason()); frame(result, value.frame()); common(result, value);
        result.put("native_roster_status", value.nativeRosterStatus().wire()); nullable(result, "raw_occurrence_count", value.rawOccurrenceCount());
        result.put("known_living_actual_child_count", value.knownCount()); result.put("child_inputs_status", value.childInputsStatus().wire()); result.put("observed_inputs_complete", value.complete());
        ArrayNode rows = result.putArray("rows");
        for (Child child : value.rows()) {
            ObjectNode row = rows.addObject(); identity(row, child); ObjectNode availability = row.putObject("leaf_availability");
            for (LeafKind kind : LeafKind.values()) {
                String name = leafName(kind); Leaf leaf = child.read() == null ? null : child.read().leaf(kind);
                if (leaf == null) { row.putNull(name); } else { row.set(name, EducationInputCodec.parse(leaf.validatedWire())); }
                Availability observed = child.leafAvailability().get(kind.ordinal()); ObjectNode state = availability.putObject(name);
                state.put("status", observed.status().wire()); nullable(state, "unavailable_reason", observed.unavailableReason());
            }
            CourtOwner court = child.read() == null ? null : child.read().courtOwner();
            if (court != null && court.fieldPresent()) { if (!court.sourcePresent()) { row.putNull("court_owner_source"); } else { row.set("court_owner_source", EducationInputCodec.parse(court.validatedWire())); } }
            row.put("observed_inputs_complete", child.complete()); row.put("status", child.complete() ? "available" : "partial");
        }
        return result;
    }
    private static ObjectNode focus(Leaf leaf) {
        ObjectNode result = StrictJson.object(); boolean available = leaf != null && leaf.status() == Status.AVAILABLE;
        result.put("available", available);
        nullable(result, "unavailable_reason", available ? null : leaf == null ? "native_focus_not_observed" : leaf.unavailableReason());
        if (!available) { for (String key : List.of("presence", "key", "known_null", "has_education_focus")) { result.putNull(key); } }
        else {
            Focus focus = (Focus) leaf.facts(); boolean present = focus.presence() == Presence.PRESENT;
            result.put("presence", present ? "present" : "absent"); nullable(result, "key", focus.key()); result.put("known_null", !present);
            result.put("has_education_focus", present && SKILLS.stream().anyMatch(skill -> ("education_" + skill.name()).equals(focus.key())));
        }
        return result;
    }
    private static ObjectNode courtOwner(Child child, Frame frame) {
        CourtOwner source = child.read() == null ? null : child.read().courtOwner();
        boolean bound = source != null && source.sourcePresent() && child.rawCharacterId() < 0xffff_ffffL && source.childId() == child.rawCharacterId()
                && source.nativeRevision().equals(frame.nativeRevision()) && source.sourceQualified() && source.projectionComplete() && source.identityRoundTrip() && source.sampleStable();
        boolean knownNull = bound && source.status().equals("known_null") && Boolean.FALSE.equals(source.ownerPresent()) && source.ownerId() == null;
        boolean resolved = bound && source.status().equals("resolved") && Boolean.TRUE.equals(source.ownerPresent()) && source.ownerId() != null && source.ownerId() < 0xffff_ffffL;
        boolean available = knownNull || resolved;
        ObjectNode result = StrictJson.object(); result.put("available", available); result.put("source_qualified", available);
        nullable(result, "present", available ? resolved : null); nullable(result, "known_null", available ? knownNull : null);
        nullable(result, "owner_character_id_raw", resolved ? source.ownerId() : null); result.put("basis", "current_child_native_court_owner_source_projection");
        String reason = source == null || !source.sourcePresent() ? "court_owner_source_not_observed" : source.unavailableReason() == null || source.unavailableReason().isEmpty() ? "court_owner_source_unavailable" : source.unavailableReason();
        nullable(result, "unavailable_reason", available ? null : reason); return result;
    }
    private static void identity(ObjectNode node, Child child) { node.put("character_id", child.characterId()); node.put("raw_character_id", child.rawCharacterId()); ArrayNode indices = node.putArray("occurrence_indices"); child.occurrenceIndices().forEach(indices::add); }
    private static void frame(ObjectNode node, Frame frame) {
        if (frame == null) { node.putNull("frame"); return; }
        ObjectNode target = node.putObject("frame"); target.put("native_revision", frame.nativeRevision()); nullable(target, "played_character_id", frame.playedCharacterId()); nullable(target, "heir_character_id", frame.heirCharacterId()); nullable(target, "date_raw", frame.dateRaw());
    }
    private static void common(ObjectNode node, Generation value) { node.put("roster_complete", value.rosterComplete()); node.put("living_child_classification_complete", value.classificationComplete()); nullable(node, "living_actual_child_exists", value.exists()); nullable(node, "living_actual_child_count", value.count()); nullable(node, "known_empty", value.knownEmpty()); }
    static void strings(ArrayNode node, List<String> values) { values.forEach(node::add); }
    static void nullable(ObjectNode node, String key, String value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    static void nullable(ObjectNode node, String key, Boolean value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    static void nullable(ObjectNode node, String key, Long value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    static void nullable(ObjectNode node, String key, Integer value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
}
