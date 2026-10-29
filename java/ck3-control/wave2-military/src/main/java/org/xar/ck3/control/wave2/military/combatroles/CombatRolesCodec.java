package org.xar.ck3.control.wave2.military.combatroles;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.combatroles.CombatRoles.*;
import org.xar.ck3.control.wave2.military.sharedwire.ArmyManagerSharedWire;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Strict closed leaf codec. The SDK ArmyStrength and snapshot containers are declared projections. */
public final class CombatRolesCodec {
    public static final String MEMBER = "current_army_combat_roles_phase_inputs_v1";
    public static final int MAX_BYTES = 1_048_576;
    private static final String LIMITS = "actual_manager_invocation_observed future_phase_transition_ready full_callback_ready full_battle_ready";
    private CombatRolesCodec() { }
    private static ObjectNode shape(JsonNode value, String fields) { return StrictJson.object(value, Set.of(fields.split(" "))); }
    private static String text(JsonNode node) { return StrictJson.text(node); }
    private static String nullableText(JsonNode node) { return node.isNull() ? null : text(node); }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "actual JSON bool required"); return node.booleanValue(); }
    private static Boolean nullableBool(JsonNode node) { return node.isNull() ? null : bool(node); }
    private static Integer i32(JsonNode node) { return node.isNull() ? null : (int) StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static Long u32(JsonNode node) { return node.isNull() ? null : StrictJson.integer(node, 0, 0xffffffffL); }
    private static Integer u8(JsonNode node) { return node.isNull() ? null : (int) StrictJson.integer(node, 0, 255); }
    private static int requiredI32(JsonNode node) { require(!node.isNull(), "required signed32 missing"); return i32(node); }
    private static State state(ObjectNode node) {
        Status status = switch (text(node.get("status"))) {
            case "available" -> Status.AVAILABLE; case "partial" -> Status.PARTIAL; case "unavailable" -> Status.UNAVAILABLE;
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("status malformed");
        };
        JsonNode reason = node.get("unavailable_reason");
        require(reason != null && reason.isTextual(), "raw unavailable_reason must retain string including empty string");
        if (!reason.textValue().isEmpty()) text(reason);
        return new State(status, reason.textValue());
    }
    private static ArrayNode array(JsonNode node) { require(node instanceof ArrayNode, "native JSON array required"); return (ArrayNode) node; }
    private static List<Integer> indices(JsonNode node) {
        List<Integer> result = new ArrayList<>(); for (JsonNode row : array(node)) result.add(requiredI32(row)); return List.copyOf(result);
    }
    private static Resolution resolution(JsonNode value, boolean generic) {
        ObjectNode node = shape(value, "status ready unavailable_reason registry_loaded used_fallback requested_full_id_u32 registry_capacity_u32 registry_index_u32 indexed_full_id_u32 indexed_identity selection object_identity selected_object_ready"
                + (generic ? " selected_full_id_u32 selected_full_id_read_ready" : ""));
        String selection = nullableText(node.get("selection"));
        SelectionSource source = selection == null ? null : switch (selection) {
            case "registry_full_id" -> SelectionSource.REGISTRY_FULL_ID; case "native_fallback" -> SelectionSource.NATIVE_FALLBACK;
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("selection source malformed");
        };
        return new Resolution(state(node), bool(node.get("ready")), nullableBool(node.get("registry_loaded")),
                nullableBool(node.get("used_fallback")), u32(node.get("requested_full_id_u32")), u32(node.get("registry_capacity_u32")),
                u32(node.get("registry_index_u32")), u32(node.get("indexed_full_id_u32")), nullableText(node.get("indexed_identity")),
                source, nullableText(node.get("object_identity")), bool(node.get("selected_object_ready")),
                generic ? u32(node.get("selected_full_id_u32")) : null,
                generic ? nullableBool(node.get("selected_full_id_read_ready")) : null);
    }
    private static RawReferences rawReferences(JsonNode value) {
        ObjectNode node = shape(value, "status ready unavailable_reason references_ready count_raw_i32 data_identity data_present occurrences observed_occurrence_count");
        List<RawOccurrence> rows = new ArrayList<>();
        for (JsonNode item : array(node.get("occurrences"))) {
            ObjectNode row = shape(item, "status ready unavailable_reason native_index raw_full_id_u32");
            rows.add(new RawOccurrence(state(row), bool(row.get("ready")), requiredI32(row.get("native_index")), u32(row.get("raw_full_id_u32"))));
        }
        return new RawReferences(state(node), bool(node.get("ready")), bool(node.get("references_ready")), i32(node.get("count_raw_i32")),
                nullableText(node.get("data_identity")), nullableBool(node.get("data_present")), rows, requiredI32(node.get("observed_occurrence_count")));
    }
    private static Roster roster(JsonNode value) {
        ObjectNode node = shape(value, "status unavailable_reason data_identity capacity_raw_u32 count_raw_i32 references references_ready");
        List<Reference> rows = new ArrayList<>();
        for (JsonNode item : array(node.get("references"))) {
            ObjectNode row = shape(item, "native_index raw_full_id_u32");
            rows.add(new Reference(requiredI32(row.get("native_index")), u32(row.get("raw_full_id_u32"))));
        }
        return new Roster(state(node), nullableText(node.get("data_identity")), u32(node.get("capacity_raw_u32")),
                i32(node.get("count_raw_i32")), rows, bool(node.get("references_ready")));
    }
    private static Manager manager(JsonNode value) {
        ObjectNode node = shape(value, "status unavailable_reason game_state_identity domain_identity manager_identity secondary_vtable_identity secondary_vtable_matched roster manager_inputs_ready");
        return new Manager(state(node), nullableText(node.get("game_state_identity")), nullableText(node.get("domain_identity")),
                nullableText(node.get("manager_identity")), nullableText(node.get("secondary_vtable_identity")),
                nullableBool(node.get("secondary_vtable_matched")), roster(node.get("roster")), bool(node.get("manager_inputs_ready")));
    }
    private static Side side(JsonNode value) {
        ObjectNode node = shape(value, "status unavailable_reason parent_identity parent_matches_selected_combat armies matching_army_indices matching_membership_ready primary_70_raw_u32 commander_74_raw_u32 owner_matches_primary side_inputs_ready");
        return new Side(state(node), nullableText(node.get("parent_identity")), nullableBool(node.get("parent_matches_selected_combat")),
                roster(node.get("armies")), indices(node.get("matching_army_indices")), bool(node.get("matching_membership_ready")),
                u32(node.get("primary_70_raw_u32")), u32(node.get("commander_74_raw_u32")),
                nullableBool(node.get("owner_matches_primary")), bool(node.get("side_inputs_ready")));
    }
    private static Occurrence occurrence(JsonNode value) {
        ObjectNode node = shape(value, "status unavailable_reason native_index raw_full_id_u32 original_army_resolution same_query_army_selection_matched actual_army_10_raw_u32 army_128_raw_u32 combat_resolution selected_combat_magic_0c_raw_u32 selected_combat_full_id_08_raw_u32 source_active_combat active_combat_inputs_ready manager_match_indices combat_manager_membership_ready army_124_raw_u32 unit_owner_174_raw_u32 unit_resolution character_resolution selected_character_18_raw_u32 owner_inputs_ready attacker_side defender_side phase_6b0_raw_i32 day_6b4_raw_i32 forced_winner_700_raw_i32 finalized_704_raw_u8 processing_705_raw_u8 phase_inputs_ready threshold_required maneuver_threshold_raw_i32 threshold_inputs_ready current_combat_roles_phase_inputs_ready");
        return new Occurrence(state(node), requiredI32(node.get("native_index")), u32(node.get("raw_full_id_u32")),
                resolution(node.get("original_army_resolution"), true), bool(node.get("same_query_army_selection_matched")),
                u32(node.get("actual_army_10_raw_u32")), u32(node.get("army_128_raw_u32")), resolution(node.get("combat_resolution"), false),
                u32(node.get("selected_combat_magic_0c_raw_u32")), u32(node.get("selected_combat_full_id_08_raw_u32")),
                nullableBool(node.get("source_active_combat")), bool(node.get("active_combat_inputs_ready")),
                indices(node.get("manager_match_indices")), bool(node.get("combat_manager_membership_ready")),
                u32(node.get("army_124_raw_u32")), u32(node.get("unit_owner_174_raw_u32")),
                resolution(node.get("unit_resolution"), false), resolution(node.get("character_resolution"), false),
                u32(node.get("selected_character_18_raw_u32")), bool(node.get("owner_inputs_ready")),
                side(node.get("attacker_side")), side(node.get("defender_side")), i32(node.get("phase_6b0_raw_i32")),
                i32(node.get("day_6b4_raw_i32")), i32(node.get("forced_winner_700_raw_i32")), u8(node.get("finalized_704_raw_u8")),
                u8(node.get("processing_705_raw_u8")), bool(node.get("phase_inputs_ready")), bool(node.get("threshold_required")),
                i32(node.get("maneuver_threshold_raw_i32")), bool(node.get("threshold_inputs_ready")),
                bool(node.get("current_combat_roles_phase_inputs_ready")));
    }
    public static Inputs decode(byte[] raw) { return decode(StrictJson.parse(raw, MAX_BYTES)); }
    public static Inputs decode(JsonNode value) {
        if (value.isNull()) return null;
        ObjectNode node = shape(value, "status unavailable_reason schema_version source stage original_army_manager_loaded original_army_manager_identity original_roster combat_manager occurrences raw_roster_references_ready original_army_selections_ready current_combat_roles_phase_inputs_ready "
                + LIMITS + " native_calls_executed native_writes_executed");
        require(StrictJson.integer(node.get("schema_version"), 1, 1) == 1
                && text(node.get("source")).equals("native_current_army_combat_roles_phase_inputs")
                && text(node.get("stage")).equals("observed_current_army_combat_roles_phase_inputs"), "exact current source/stage/version required");
        for (String field : LIMITS.split(" ")) require(!bool(node.get(field)), "current observation cannot credit future/full battle");
        StrictJson.integer(node.get("native_calls_executed"), 0, 0); StrictJson.integer(node.get("native_writes_executed"), 0, 0);
        List<Occurrence> rows = new ArrayList<>(); for (JsonNode row : array(node.get("occurrences"))) rows.add(occurrence(row));
        Inputs result = new Inputs(state(node), nullableBool(node.get("original_army_manager_loaded")),
                nullableText(node.get("original_army_manager_identity")), rawReferences(node.get("original_roster")),
                manager(node.get("combat_manager")), rows, bool(node.get("raw_roster_references_ready")),
                bool(node.get("original_army_selections_ready")), bool(node.get("current_combat_roles_phase_inputs_ready")));
        CombatRolesPolicy.validate(result); return result;
    }
    private static String lower(Enum<?> value) { return value == null ? null : value.name().toLowerCase(Locale.ROOT); }
    private static ObjectNode stateNode(State state) {
        ObjectNode node = StrictJson.object(); node.put("status", lower(state.status())); node.put("unavailable_reason", state.unavailableReason()); return node;
    }
    private static ObjectNode resolutionNode(Resolution value, boolean generic) {
        ObjectNode node = stateNode(value.state()); node.put("ready", value.ready()); node.put("registry_loaded", value.registryLoaded());
        node.put("used_fallback", value.usedFallback()); node.put("requested_full_id_u32", value.requestedFullId());
        node.put("registry_capacity_u32", value.registryCapacity()); node.put("registry_index_u32", value.registryIndex());
        node.put("indexed_full_id_u32", value.indexedFullId()); node.put("indexed_identity", value.indexedIdentity());
        node.put("selection", lower(value.selection())); node.put("object_identity", value.objectIdentity());
        node.put("selected_object_ready", value.selectedObjectReady());
        if (generic) { node.put("selected_full_id_u32", value.selectedFullId()); node.put("selected_full_id_read_ready", value.selectedFullIdReadReady()); }
        return node;
    }
    private static ObjectNode rawReferencesNode(RawReferences value) {
        ObjectNode node = stateNode(value.state()); node.put("ready", value.ready()); node.put("references_ready", value.referencesReady());
        node.put("count_raw_i32", value.count()); node.put("data_identity", value.dataIdentity()); node.put("data_present", value.dataPresent());
        ArrayNode rows = node.putArray("occurrences");
        for (RawOccurrence row : value.occurrences()) { ObjectNode item = stateNode(row.state()); item.put("ready", row.ready());
            item.put("native_index", row.nativeIndex()); item.put("raw_full_id_u32", row.rawFullId()); rows.add(item); }
        node.put("observed_occurrence_count", value.observedCount()); return node;
    }
    private static ObjectNode rosterNode(Roster value) {
        ObjectNode node = stateNode(value.state()); node.put("data_identity", value.dataIdentity()); node.put("capacity_raw_u32", value.capacity());
        node.put("count_raw_i32", value.count()); node.put("references_ready", value.referencesReady()); ArrayNode rows = node.putArray("references");
        for (Reference row : value.references()) { ObjectNode item = rows.addObject(); item.put("native_index", row.nativeIndex()); item.put("raw_full_id_u32", row.rawFullId()); }
        return node;
    }
    private static ObjectNode managerNode(Manager value) {
        ObjectNode node = stateNode(value.state()); node.put("game_state_identity", value.gameStateIdentity()); node.put("domain_identity", value.domainIdentity());
        node.put("manager_identity", value.managerIdentity()); node.put("secondary_vtable_identity", value.secondaryVtableIdentity());
        node.put("secondary_vtable_matched", value.secondaryVtableMatched()); node.set("roster", rosterNode(value.roster()));
        node.put("manager_inputs_ready", value.managerInputsReady()); return node;
    }
    private static void addIndices(ObjectNode node, String field, List<Integer> indices) { ArrayNode rows = node.putArray(field); indices.forEach(rows::add); }
    private static ObjectNode sideNode(Side value) {
        ObjectNode node = stateNode(value.state()); node.put("parent_identity", value.parentIdentity()); node.put("parent_matches_selected_combat", value.parentMatchesSelectedCombat());
        node.set("armies", rosterNode(value.armies())); addIndices(node, "matching_army_indices", value.matchingArmyIndices());
        node.put("matching_membership_ready", value.matchingMembershipReady()); node.put("primary_70_raw_u32", value.primary());
        node.put("commander_74_raw_u32", value.commander()); node.put("owner_matches_primary", value.ownerMatchesPrimary()); node.put("side_inputs_ready", value.sideInputsReady()); return node;
    }
    private static ObjectNode occurrenceNode(Occurrence value) {
        ObjectNode node = stateNode(value.state()); node.put("native_index", value.nativeIndex()); node.put("raw_full_id_u32", value.rawFullId());
        node.set("original_army_resolution", resolutionNode(value.originalArmyResolution(), true));
        node.put("same_query_army_selection_matched", value.sameQueryArmySelectionMatched()); node.put("actual_army_10_raw_u32", value.actualArmyId());
        node.put("army_128_raw_u32", value.armyCombatId()); node.set("combat_resolution", resolutionNode(value.combatResolution(), false));
        node.put("selected_combat_magic_0c_raw_u32", value.combatMagic()); node.put("selected_combat_full_id_08_raw_u32", value.selectedCombatFullId());
        node.put("source_active_combat", value.sourceActiveCombat()); node.put("active_combat_inputs_ready", value.activeCombatInputsReady());
        addIndices(node, "manager_match_indices", value.managerMatchIndices()); node.put("combat_manager_membership_ready", value.combatManagerMembershipReady());
        node.put("army_124_raw_u32", value.armyUnitId()); node.put("unit_owner_174_raw_u32", value.unitOwnerId());
        node.set("unit_resolution", resolutionNode(value.unitResolution(), false)); node.set("character_resolution", resolutionNode(value.characterResolution(), false));
        node.put("selected_character_18_raw_u32", value.selectedCharacterId()); node.put("owner_inputs_ready", value.ownerInputsReady());
        node.set("attacker_side", sideNode(value.attackerSide())); node.set("defender_side", sideNode(value.defenderSide()));
        node.put("phase_6b0_raw_i32", value.phase()); node.put("day_6b4_raw_i32", value.day()); node.put("forced_winner_700_raw_i32", value.forcedWinner());
        node.put("finalized_704_raw_u8", value.finalized()); node.put("processing_705_raw_u8", value.processing());
        node.put("phase_inputs_ready", value.phaseInputsReady()); node.put("threshold_required", value.thresholdRequired());
        node.put("maneuver_threshold_raw_i32", value.maneuverThreshold()); node.put("threshold_inputs_ready", value.thresholdInputsReady());
        node.put("current_combat_roles_phase_inputs_ready", value.currentCombatRolesPhaseInputsReady()); return node;
    }
    private static void limits(ObjectNode node) { for (String field : LIMITS.split(" ")) node.put(field, false);
        node.put("native_calls_executed", 0); node.put("native_writes_executed", 0); }
    public static JsonNode encode(Inputs value) {
        if (value == null) return NullNode.instance;
        CombatRolesPolicy.validate(value);
        ObjectNode node = stateNode(value.state()); node.put("schema_version", 1); node.put("source", "native_current_army_combat_roles_phase_inputs");
        node.put("stage", "observed_current_army_combat_roles_phase_inputs"); node.put("original_army_manager_loaded", value.originalArmyManagerLoaded());
        node.put("original_army_manager_identity", value.originalArmyManagerIdentity()); node.set("original_roster", rawReferencesNode(value.originalRoster()));
        node.set("combat_manager", managerNode(value.combatManager())); ArrayNode rows = node.putArray("occurrences");
        for (Occurrence row : value.occurrences()) rows.add(occurrenceNode(row)); node.put("raw_roster_references_ready", value.rawRosterReferencesReady());
        node.put("original_army_selections_ready", value.originalArmySelectionsReady()); node.put("current_combat_roles_phase_inputs_ready", value.currentCombatRolesPhaseInputsReady()); limits(node); return node;
    }
    public static byte[] encodeBytes(Inputs value) { return StrictJson.canonical(encode(value), MAX_BYTES); }
    private static JsonNode provenanceNode(Provenance value) {
        if (value == null) return NullNode.instance;
        ObjectNode node = StrictJson.object(); node.put("snapshot_id", value.snapshotId()); node.put("revision", value.revision());
        node.put("native_revision", value.nativeRevision()); node.put("date_raw", value.dateRaw()); node.put("game_version", value.gameVersion());
        node.put("executable_sha256", value.executableSha256()); return node;
    }
    public static ObjectNode encodeProjection(Projection value) {
        ObjectNode node = StrictJson.object(); node.put("schema_version", 1); node.put("source", "source_bound_current_army_combat_roles_phase_inputs");
        node.put("stage", "observed_current_army_combat_roles_phase_inputs"); node.put("source_contract_game_version", "1.20.0.3");
        node.put("status", lower(value.status())); node.put("ready", value.ready()); node.put("unavailable_reason", value.unavailableReason());
        node.put("current_combat_roles_phase_inputs_ready", value.ready()); node.set("source_provenance", provenanceNode(value.sourceProvenance()));
        node.set("observed_current_army_combat_roles_phase_inputs", encode(value.observed())); limits(node);
        if (value.observed() != null) { node.set("combat_manager", managerNode(value.observed().combatManager()));
            node.set("original_roster", rawReferencesNode(value.observed().originalRoster())); }
        ArrayNode rows = node.putArray("occurrences");
        for (ProjectedOccurrence row : value.occurrences()) {
            ObjectNode item = occurrenceNode(row.observed()); item.put("ready", row.ready());
            item.put("unavailable_reason", row.ready() ? null : row.observed().state().unavailableReason());
            item.put("stored_side_membership", lower(row.storedSideMembership())); item.put("phase_label", lower(row.phaseLabel()));
            PhaseSelector selector = row.hypotheticalPhaseSelector(); ObjectNode phase = item.putObject("hypothetical_phase_selector");
            phase.put("ready", selector.ready()); phase.put("hypothetical", true); phase.put("input_stage", "observed_current_before_manager_invocation");
            phase.put("post_reselection_inputs_observed", false); phase.put("actual_manager_invocation_observed", false); phase.put("future_phase_transition_ready", false);
            phase.put("decision", lower(selector.decision())); phase.put("worker", lower(selector.worker())); phase.put("incremented_day_raw_i32", selector.incrementedDay());
            phase.put("selected_phase_raw_i32", selector.selectedPhase()); phase.put("selected_day_raw_i32", selector.selectedDay()); rows.add(item);
        }
        return node;
    }
    /** Select only this optional member; other SDK extensions are neither rejected nor reinterpreted. */
    public static Member readMember(JsonNode armyRow) {
        require(armyRow != null && armyRow.isObject(), "ArmyStrength row required");
        if (!armyRow.has(MEMBER)) return new Missing();
        return armyRow.get(MEMBER).isNull() ? new ExplicitNull() : new Present(decode(armyRow.get(MEMBER)));
    }
    private static BigInteger nullableInteger(JsonNode node) {
        if (node == null || node.isNull()) return null;
        require(node.isIntegralNumber(), "provenance must retain exact integer token"); return node.bigIntegerValue();
    }
    private static String optionalText(JsonNode node) { return node == null || node.isNull() ? null : text(node); }
    /** The actual service's six provenance fields, read from its extensible snapshot and hello objects. */
    public static Provenance provenanceFromSnapshot(JsonNode snapshot) {
        require(snapshot != null && snapshot.isObject(), "service snapshot required");
        JsonNode diagnostics = snapshot.path("diagnostics"), hello = diagnostics.path("hello");
        return new Provenance(optionalText(snapshot.get("snapshot_id")), nullableInteger(snapshot.get("revision")),
                nullableInteger(snapshot.get("native_revision")), nullableInteger(snapshot.get("date_raw")),
                optionalText(hello.get("game_version")), optionalText(hello.get("executable_sha256")));
    }
    /** Same selected-row order and optional-member semantics as GameplayBridgeService.query_army_strengths. */
    public static ArrayNode projectSelectedRows(JsonNode rows, JsonNode snapshot) {
        Provenance provenance = provenanceFromSnapshot(snapshot); ArrayNode out = StrictJson.object().putArray(MEMBER);
        for (JsonNode row : array(rows)) {
            require(row.isObject(), "selected ArmyStrength row required"); JsonNode id = row.get("army_id");
            StrictJson.integer(id, 0, Integer.MAX_VALUE);
            Member member = readMember(row); Inputs input = member instanceof Present present ? present.value() : null;
            ObjectNode item = out.addObject(); item.put("army_id", id.bigIntegerValue());
            item.set("projection", encodeProjection(CombatRolesPolicy.project(input, provenance)));
        }
        return out;
    }
    /** Real Driver expansion precedes one owned-family normalization per shared physical JSON object.
     * Distinct equal inline leaves are validated independently; the cache lasts only this query.
     */
    public static List<ArmyMember> readQueryMembers(JsonNode queryResult) {
        require(queryResult instanceof ObjectNode, "army query result object required");
        ObjectNode expanded = ArmyManagerSharedWire.expand((ObjectNode) queryResult, false);
        ArrayNode rows = array(expanded.get("army_strengths"));
        List<ArmyMember> selected = new ArrayList<>(); IdentityHashMap<JsonNode, Member> cache = new IdentityHashMap<>();
        for (int i = 0; i < rows.size(); i++) {
            JsonNode row = rows.get(i); require(row.isObject(), "ArmyStrength row object required");
            long id = StrictJson.integer(row.get("army_id"), 0, Integer.MAX_VALUE);
            JsonNode body = row.get(MEMBER); Member member;
            if (body == null) member = new Missing();
            else if (cache.containsKey(body)) member = cache.get(body);
            else { member = readMember(row); cache.put(body, member); }
            selected.add(new ArmyMember(BigInteger.valueOf(id), member));
        }
        return List.copyOf(selected);
    }
    /** Existing shared/inline query forms converge on one source-bound family projection. */
    public static ArrayNode projectQueryFamily(JsonNode queryResult, JsonNode snapshot) {
        Provenance provenance = provenanceFromSnapshot(snapshot); ArrayNode out = StrictJson.object().putArray(MEMBER);
        for (ArmyMember row : readQueryMembers(queryResult)) {
            Inputs input = row.member() instanceof Present present ? present.value() : null;
            ObjectNode item = out.addObject(); item.put("army_id", row.armyId());
            item.set("projection", encodeProjection(CombatRolesPolicy.project(input, provenance)));
        }
        return out;
    }
}
