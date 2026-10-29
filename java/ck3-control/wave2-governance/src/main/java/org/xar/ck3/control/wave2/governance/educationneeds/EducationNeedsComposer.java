package org.xar.ck3.control.wave2.governance.educationneeds;

import static org.xar.ck3.control.contracts.StrictJson.require;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.xar.ck3.control.governance.education.EducationDecisionComposer;
import org.xar.ck3.control.governance.education.EducationInputs.Frame;
import org.xar.ck3.control.governance.education.EducationInputs.Status;

/** Original education needs and native-final-pair projection; no selection or side effects. */
public final class EducationNeedsComposer {
    public static final String SCHEMA = "family_education_needs_12004";
    private EducationNeedsComposer() { }
    public static byte[] compose(byte[] request) { return EducationNeedsCodec.encode(emit(EducationNeedsCodec.request(request))); }
    public static byte[] composeFromDescendants(byte[] descendants) {
        return composeDecision(EducationDecisionComposer.compose(descendants), null, null, null);
    }
    public static byte[] composeDecision(byte[] decision, byte[] materials, byte[] provider, byte[] sourceProof) {
        ObjectNode request = EducationNeedsCodec.object(); request.put("schema", "xar.education-needs.request/v1");
        request.set("decision_inputs", nullableJson(decision)); request.set("child_relation_materials", nullableJson(materials));
        request.set("child_education_provider_inputs", nullableJson(provider)); request.set("child_education_provider_source", nullableJson(sourceProof));
        return compose(EducationNeedsCodec.encode(request));
    }
    public static NeedsRowProjection needsRowProjection(byte[] bytes) {
        JsonNode row = EducationNeedsCodec.parse(bytes); long raw = EducationNeedsCodec.uint32(EducationNeedsCodec.field(row, "raw_character_id"));
        int signed = (int) EducationNeedsCodec.integer(EducationNeedsCodec.field(row, "character_id"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        require(signed == (int) raw, "needs row signed/full ID changed");
        JsonNode management = EducationNeedsCodec.field(row, "focus_management"); boolean available = EducationNeedsCodec.bool(EducationNeedsCodec.field(management, "available"));
        String stateWire = EducationNeedsCodec.text(EducationNeedsCodec.field(management, "state")); FocusState state = null;
        for (FocusState candidate : FocusState.values()) { if (candidate.wire().equals(stateWire)) { state = candidate; } }
        require(state != null && available == (state != FocusState.UNKNOWN), "focus management availability/state changed");
        FocusManagement focus = new FocusManagement(available, state, EducationNeedsCodec.nullableText(EducationNeedsCodec.field(management, "current_key")),
                EducationNeedsCodec.nullableBool(EducationNeedsCodec.field(management, "focus_absent")), EducationNeedsCodec.nullableBool(EducationNeedsCodec.field(management, "education_focus_present")),
                EducationNeedsCodec.nullableText(EducationNeedsCodec.field(management, "unavailable_reason")));
        return new NeedsRowProjection(signed, raw, EducationNeedsCodec.indices(EducationNeedsCodec.field(row, "occurrence_indices")), EducationNeedsCodec.frame(EducationNeedsCodec.field(row, "frame")), focus);
    }
    public static byte[] requestCandidate(byte[] needsRow, byte[] normalizedOrdinaryContext) {
        NeedsRowProjection needs = needsRowProjection(needsRow); OrdinaryContext context = EducationNeedsCodec.ordinary(normalizedOrdinaryContext);
        return EducationNeedsCodec.encode(candidate(deriveCandidate(needs, context), context.rolesWire()));
    }
    public static RequestCandidate candidateProjection(byte[] needsRow, byte[] normalizedOrdinaryContext) {
        return deriveCandidate(needsRowProjection(needsRow), EducationNeedsCodec.ordinary(normalizedOrdinaryContext));
    }
    static RequestCandidate deriveCandidate(NeedsRowProjection needs, OrdinaryContext context) {
        boolean observed = context.status() == Status.AVAILABLE && context.interactionKey().equals("educate_child_interaction");
        Boolean matches = observed ? Long.valueOf(needs.childFullId()).equals(context.roles().secondaryRecipientId()) : null;
        Long guardian = observed ? context.roles().secondaryActorId() : null; boolean available = Boolean.TRUE.equals(matches) && guardian != null;
        String reason = available ? null : !context.interactionKey().equals("educate_child_interaction") ? "ordinary_context_not_education"
                : !observed ? context.unavailableReason() : Boolean.FALSE.equals(matches) ? "native_secondary_recipient_differs_from_child" : "native_secondary_actor_known_null";
        return new RequestCandidate(available, observed, matches, needs.childFullId(), available ? guardian : null, observed ? guardian == null : null,
                context.roles(), context.frame(), context.canSend(), context.readyToInitiate(), available ? "native_final_secondary_actor_and_secondary_recipient" : "", reason);
    }
    static ObjectNode emit(Request request) {
        ObjectNode result = EducationNeedsCodec.object(); result.put("schema", SCHEMA); result.put("source", "current_family_education_observed_inputs");
        result.putNull("frame"); result.put("roster_complete", false); result.put("living_child_classification_complete", false); result.putNull("known_empty");
        ArrayNode rows = result.putArray("rows"); result.put("source_projection_only", true);
        Provider provider = request.provider();
        if (provider.present()) { result.set("query_owned_education_provider_inputs_v1", EducationNeedsCodec.unwire(provider.wire())); result.set("query_owned_education_provider_inputs_source_v1", EducationNeedsCodec.unwire(provider.sourceWire())); }
        Decision decision = request.decision(); if (decision == null) { return result; }
        frame(result, "frame", decision.frame()); result.put("roster_complete", decision.rosterComplete()); result.put("living_child_classification_complete", decision.classificationComplete()); nullable(result, "known_empty", decision.knownEmpty());
        for (Child child : decision.children()) {
            NeedsRowProjection facts = child.projection(); ObjectNode row = rows.addObject(); row.put("character_id", facts.characterId()); row.put("raw_character_id", facts.childFullId());
            ArrayNode indices = row.putArray("occurrence_indices"); facts.occurrenceIndices().forEach(indices::add); frame(row, "frame", facts.focusSourceFrame()); row.set("focus_management", focus(facts.focusManagement()));
            row.set("leaf_availability", EducationNeedsCodec.unwire(child.availabilityWire())); ArrayNode missing = row.putArray("missing_observations");
            for (LeafAvailability availability : child.availability()) { if (availability.status() != Status.AVAILABLE) { missing.add(availability.key()); } }
            row.set("values", EducationNeedsCodec.unwire(child.values())); row.set("childhood_traits", EducationNeedsCodec.unwire(child.childhoodTraits()));
            row.set("education_point_traits", EducationNeedsCodec.unwire(child.pointTraits())); row.set("education_traits", EducationNeedsCodec.unwire(child.educationTraits()));
            row.set("stock_skill_options", EducationNeedsCodec.unwire(child.stockOptions())); row.set("current_education_skill_inputs", EducationNeedsCodec.unwire(child.currentOption())); row.set("current_court_owner", EducationNeedsCodec.unwire(child.courtOwner()));
            row.set("relation_materials", material(facts.childFullId(), request.materials())); if (provider.present()) { row.set("education_provider_inputs", provider(facts, provider)); }
        }
        return result;
    }
    private static ObjectNode material(long child, Materials source) {
        ObjectNode result = EducationNeedsCodec.object(); result.put("observed", source.present()); result.put("collection_available", source.collected());
        MaterialRow matched = null; if (source.collected()) { for (MaterialRow row : source.rows()) { if (row.childId() == child) { matched = row; break; } } }
        if (matched == null) { result.putNull("observation"); } else { result.set("observation", EducationNeedsCodec.unwire(matched.wire())); }
        String reason = !source.present() ? "child_relation_materials_not_observed" : matched != null ? null : source.reason() == null || source.reason().isEmpty() ? "child_material_row_not_observed" : source.reason();
        nullable(result, "unavailable_reason", reason); return result;
    }
    private static ObjectNode provider(NeedsRowProjection child, Provider source) {
        ProviderRow observation = null;
        if (source.collected()) { for (ProviderRow row : source.rows()) { if (row.childId() == child.childFullId()) { observation = row; break; } }
            if (observation == null || !observation.occurrences().equals(child.occurrenceIndices())) { throw new ProjectionDomainRejection("same-query education provider child projection changed"); } }
        ObjectNode result = EducationNeedsCodec.object(); result.put("observed", true); result.put("read_only", true); result.put("status", source.status().wire()); result.put("collection_available", source.collected());
        if (observation == null) { result.putNull("observation"); } else { result.set("observation", EducationNeedsCodec.unwire(observation.wire())); }
        nullable(result, "unavailable_reason", source.reason()); result.put("m6_inputs_complete", false); result.put("guardian_role_equivalence_qualified", false); return result;
    }
    private static ObjectNode focus(FocusManagement focus) {
        ObjectNode result = EducationNeedsCodec.object(); result.put("available", focus.available()); result.put("state", focus.state().wire()); nullable(result, "current_key", focus.currentKey());
        nullable(result, "focus_absent", focus.focusAbsent()); nullable(result, "education_focus_present", focus.educationFocusPresent()); nullable(result, "unavailable_reason", focus.unavailableReason()); return result;
    }
    static ObjectNode candidate(RequestCandidate value, WireValue roles) {
        ObjectNode result = EducationNeedsCodec.object(); result.put("available", value.available()); result.put("role_observation_available", value.roleObservationAvailable()); nullable(result, "pair_matches_child", value.pairMatchesChild());
        result.put("child_full_id", value.childFullId()); nullable(result, "guardian_full_id", value.guardianFullId()); nullable(result, "guardian_role_known_null", value.guardianRoleKnownNull()); result.set("roles", EducationNeedsCodec.unwire(roles));
        OrdinaryFrame source = value.frame(); ObjectNode frame = result.putObject("frame"); frame.put("snapshot_revision", source.snapshotRevision()); frame.put("date_raw", source.dateRaw()); frame.put("player_character_id", source.playerCharacterId()); frame.put("game_pid", source.gamePid()); frame.put("connection_generation", source.connectionGeneration());
        result.put("can_send", value.canSend()); result.put("ready_to_initiate", value.readyToInitiate()); result.put("basis", value.basis()); nullable(result, "unavailable_reason", value.unavailableReason()); return result;
    }
    private static JsonNode nullableJson(byte[] bytes) { return bytes == null ? com.fasterxml.jackson.databind.node.NullNode.getInstance() : EducationNeedsCodec.parse(bytes); }
    private static void frame(ObjectNode target, String key, Frame value) {
        if (value == null) { target.putNull(key); return; } ObjectNode frame = target.putObject(key); frame.put("native_revision", value.nativeRevision()); nullable(frame, "played_character_id", value.playedCharacterId()); nullable(frame, "heir_character_id", value.heirCharacterId()); nullable(frame, "date_raw", value.dateRaw());
    }
    private static void nullable(ObjectNode node, String key, String value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void nullable(ObjectNode node, String key, Boolean value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void nullable(ObjectNode node, String key, Long value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
}
