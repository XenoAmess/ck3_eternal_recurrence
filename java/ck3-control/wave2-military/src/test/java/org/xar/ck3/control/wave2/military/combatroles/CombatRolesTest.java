package org.xar.ck3.control.wave2.military.combatroles;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.combatroles.CombatRoles.*;
import static org.junit.jupiter.api.Assertions.*;

final class CombatRolesTest {
    private static JsonNode golden() throws IOException {
        try (InputStream resource = CombatRolesTest.class.getResourceAsStream("/combatroles/original-producer-golden.json.gz")) {
            assertNotNull(resource, "original producer golden is mandatory; missing environment is not a passing skip");
            try (GZIPInputStream input = new GZIPInputStream(resource)) {
                byte[] raw = input.readNBytes(CombatRolesCodec.MAX_BYTES + 1);
                assertTrue(raw.length <= CombatRolesCodec.MAX_BYTES, "finite decompression budget");
                return StrictJson.parse(raw, CombatRolesCodec.MAX_BYTES);
            }
        }
    }
    private static JsonNode scene(JsonNode golden, String name) {
        for (JsonNode value : golden.get("cases")) if (value.get("name").textValue().equals(name)) return value;
        fail("required original scene missing: " + name); return NullNode.instance;
    }
    private static void sameJson(JsonNode expected, JsonNode actual) {
        assertArrayEquals(StrictJson.canonical(expected, CombatRolesCodec.MAX_BYTES), StrictJson.canonical(actual, CombatRolesCodec.MAX_BYTES));
    }
    private static ObjectNode snapshot(JsonNode golden) {
        JsonNode provenance = golden.get("source_provenance"); ObjectNode snapshot = StrictJson.object();
        for (String field : List.of("snapshot_id", "revision", "native_revision", "date_raw")) snapshot.set(field, provenance.get(field));
        ObjectNode hello = snapshot.putObject("diagnostics").putObject("hello");
        hello.set("game_version", provenance.get("game_version")); hello.set("executable_sha256", provenance.get("executable_sha256"));
        snapshot.put("unrelated_sdk_extension", "retained-by-owner"); return snapshot;
    }
    @Test void originalNativeWholeRowsToAllLegacyConsumersAndJavaAdapter() throws IOException {
        JsonNode golden = golden(); assertEquals("xar.combat-roles-original-producer-golden.v1", golden.get("schema").textValue());
        assertFalse(golden.get("actual_live_qualification").booleanValue()); assertEquals(14, golden.get("cases").size());
        assertFalse(golden.get("machine_id").textValue().isEmpty()); assertFalse(golden.get("source_bindings").isEmpty());
        ObjectNode snapshot = snapshot(golden); Provenance provenance = CombatRolesCodec.provenanceFromSnapshot(snapshot);
        for (JsonNode sample : golden.get("cases")) {
            JsonNode original = sample.get("input"); Inputs input = CombatRolesCodec.decode(StrictJson.canonical(original, CombatRolesCodec.MAX_BYTES));
            sameJson(sample.get("expected_normalized"), CombatRolesCodec.encode(input));
            sameJson(original, CombatRolesCodec.encode(CombatRolesCodec.decode(CombatRolesCodec.encodeBytes(input))));
            sameJson(sample.get("expected_projection"), CombatRolesCodec.encodeProjection(CombatRolesPolicy.project(input, provenance)));
            ArrayNode rows = StrictJson.object().putArray("rows"); ObjectNode row = rows.addObject(); row.put("army_id", 11);
            row.set(CombatRolesCodec.MEMBER, original); row.put("unrelated_native_extension", true);
            sameJson(sample.get("expected_service_family"), CombatRolesCodec.projectSelectedRows(rows, snapshot));
            ObjectNode shared = sharedEnvelope(sample); ArrayNode sharedOutput = CombatRolesCodec.projectQueryFamily(shared, snapshot);
            assertEquals(2, sharedOutput.size()); assertEquals(0, sharedOutput.get(0).path("army_id").intValue());
            assertEquals(11, sharedOutput.get(1).path("army_id").intValue());
            sameJson(sample.get("expected_projection"), sharedOutput.get(0).path("projection"));
            sameJson(sample.get("expected_projection"), sharedOutput.get(1).path("projection"));
            List<ArmyMember> members = CombatRolesCodec.readQueryMembers(shared);
            assertSame(members.get(0).member(), members.get(1).member(), "shared immutable input decoded once");
            assertEquals(2, input.occurrences().size());
            assertThrows(UnsupportedOperationException.class, () -> input.occurrences().clear());
            assertThrows(UnsupportedOperationException.class, () -> input.combatManager().roster().references().clear());
        }
    }
    private static ObjectNode sharedEnvelope(JsonNode sample) {
        ObjectNode envelope = StrictJson.object(); ArrayNode rows = envelope.putArray("army_strengths");
        JsonNode ids = sample.path("shared_transport").path("army_ids");
        for (JsonNode id : ids) rows.addObject().set("army_id", id);
        ObjectNode bundle = envelope.putObject("army_manager_inputs_shared_v1"); bundle.put("schema_version", 1);
        bundle.set("army_ids", ids); bundle.putObject("fields").set(CombatRolesCodec.MEMBER, sample.get("input"));
        return envelope;
    }
    @Test void sharedWireUsesActualBundleRulesBeforeOwnedLeafProjection() throws IOException {
        JsonNode sample = scene(golden(), "active-highbit-attacker-main"); ObjectNode baseline = sharedEnvelope(sample);
        ObjectNode collision = baseline.deepCopy(); ((ObjectNode) collision.path("army_strengths").get(0)).putNull(CombatRolesCodec.MEMBER);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.readQueryMembers(collision));
        ObjectNode order = baseline.deepCopy(); ((ArrayNode) order.path("army_manager_inputs_shared_v1").path("army_ids")).set(0, StrictJson.object().numberNode(11));
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.readQueryMembers(order));
        ObjectNode duplicate = baseline.deepCopy(); ((ObjectNode) duplicate.path("army_strengths").get(1)).put("army_id", 0);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.readQueryMembers(duplicate));
        ObjectNode unknown = baseline.deepCopy(); ((ObjectNode) unknown.path("army_manager_inputs_shared_v1").path("fields")).putObject("unsupported_family");
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.readQueryMembers(unknown));
        ObjectNode malformedOther = baseline.deepCopy(); ((ObjectNode) malformedOther.path("army_manager_inputs_shared_v1").path("fields")).put("current_army_flag31_inputs_v1", false);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.readQueryMembers(malformedOther));
        ObjectNode collisionOther = baseline.deepCopy(); ((ObjectNode) collisionOther.path("army_manager_inputs_shared_v1").path("fields")).putObject("current_army_flag31_inputs_v1");
        ((ObjectNode) collisionOther.path("army_strengths").get(1)).putNull("current_army_flag31_inputs_v1");
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.readQueryMembers(collisionOther));
        ObjectNode extra = baseline.deepCopy(); ((ObjectNode) extra.path("army_manager_inputs_shared_v1")).put("extra", true);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.readQueryMembers(extra));
        ObjectNode nullLeaf = baseline.deepCopy(); ((ObjectNode) nullLeaf.path("army_manager_inputs_shared_v1").path("fields")).putNull(CombatRolesCodec.MEMBER);
        assertInstanceOf(ExplicitNull.class, CombatRolesCodec.readQueryMembers(nullLeaf).get(0).member());
    }
    @Test void rawTokensFieldsRangesAndReadOnlyScopeAreStrict() throws IOException {
        ObjectNode baseline = (ObjectNode) scene(golden(), "active-highbit-attacker-main").get("input");
        String raw = new String(StrictJson.canonical(baseline, CombatRolesCodec.MAX_BYTES), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "2")) {
            byte[] mutation = raw.replace("\"schema_version\":1", "\"schema_version\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(mutation), token);
        }
        String duplicate = raw.replace("\"schema_version\":1", "\"schema_version\":1,\"schema_version\":1");
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode((raw + "{}").getBytes(StandardCharsets.UTF_8)));
        ObjectNode extra = baseline.deepCopy(); extra.put("extra", true); assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(extra));
        ObjectNode missing = baseline.deepCopy(); missing.remove("original_army_manager_loaded"); assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(missing));
        for (String field : List.of("actual_manager_invocation_observed", "future_phase_transition_ready", "full_callback_ready", "full_battle_ready")) {
            ObjectNode claim = baseline.deepCopy(); claim.put(field, true); assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(claim));
        }
        for (String field : List.of("native_calls_executed", "native_writes_executed")) {
            ObjectNode claim = baseline.deepCopy(); claim.put(field, 1); assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(claim));
        }
        for (long outside : new long[] {-1, 4294967296L}) {
            ObjectNode claim = baseline.deepCopy(); ((ObjectNode) claim.path("occurrences").get(0)).put("actual_army_10_raw_u32", outside);
            assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(claim));
        }
    }
    @Test void physicalMembershipGenerationAndDemandedOperandsCannotBeRelabelled() throws IOException {
        JsonNode golden = golden(); ObjectNode baseline = (ObjectNode) scene(golden, "active-both-memberships-manager-duplicates-done").get("input");
        ObjectNode wrongParent = baseline.deepCopy();
        ((ObjectNode) wrongParent.path("occurrences").get(0).path("attacker_side")).put("parent_identity", "another-physical-combat");
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(wrongParent));
        ObjectNode filtered = baseline.deepCopy(); ((ArrayNode) filtered.path("occurrences")).remove(1);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(filtered));
        ObjectNode wrongMatches = baseline.deepCopy(); ((ArrayNode) wrongMatches.path("occurrences").get(0).path("manager_match_indices")).remove(1);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(wrongMatches));
        ObjectNode wrongOwner = baseline.deepCopy(); ((ObjectNode) wrongOwner.path("occurrences").get(0)).put("selected_character_18_raw_u32", 7);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(wrongOwner));
        ObjectNode undemanded = ((ObjectNode) scene(golden, "absent-combat-rule24-pins-available-mode0").get("input")).deepCopy();
        ((ObjectNode) undemanded.path("occurrences").get(0)).put("day_6b4_raw_i32", 0);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(undemanded));
        ObjectNode wrongFullGeneration = baseline.deepCopy(); ((ObjectNode) wrongFullGeneration.path("occurrences").get(0).path("combat_resolution")).put("indexed_full_id_u32", 3);
        assertThrows(ContractViolationException.class, () -> CombatRolesCodec.decode(wrongFullGeneration));
    }
    @Test void missingNullAndUnknownStayDistinctAndNeverForecast() throws IOException {
        JsonNode golden = golden(); ObjectNode snapshot = snapshot(golden); Provenance provenance = CombatRolesCodec.provenanceFromSnapshot(snapshot);
        assertInstanceOf(Missing.class, CombatRolesCodec.readMember(StrictJson.object()));
        ObjectNode explicit = StrictJson.object(); explicit.putNull(CombatRolesCodec.MEMBER);
        assertInstanceOf(ExplicitNull.class, CombatRolesCodec.readMember(explicit));
        sameJson(golden.get("null_expected_projection"), CombatRolesCodec.encodeProjection(CombatRolesPolicy.project(null, provenance)));
        Projection partial = CombatRolesPolicy.project(CombatRolesCodec.decode(scene(golden, "missing-demanded-phase").get("input")), provenance);
        assertFalse(partial.ready()); assertNull(partial.occurrences().get(0).phaseLabel());
        assertFalse(partial.occurrences().get(0).hypotheticalPhaseSelector().ready());
        Projection missingSide = CombatRolesPolicy.project(CombatRolesCodec.decode(scene(golden, "missing-demanded-side-roster").get("input")), provenance);
        assertFalse(missingSide.ready()); assertNull(missingSide.occurrences().get(0).storedSideMembership());
        assertTrue(missingSide.occurrences().get(0).hypotheticalPhaseSelector().ready());
        Projection wrap = CombatRolesPolicy.project(CombatRolesCodec.decode(scene(golden, "phase0-day-wrap").get("input")), provenance);
        assertEquals(Integer.MIN_VALUE, wrap.occurrences().get(0).hypotheticalPhaseSelector().incrementedDay());
        assertEquals(Decision.MANEUVER_WAIT, wrap.occurrences().get(0).hypotheticalPhaseSelector().decision());
        Projection expired = CombatRolesPolicy.project(CombatRolesCodec.decode(scene(golden, "phase0-above-threshold").get("input")), provenance);
        assertEquals(Decision.DURATION_MAIN_WITHOUT_WORKER, expired.occurrences().get(0).hypotheticalPhaseSelector().decision());
        assertNull(expired.occurrences().get(0).hypotheticalPhaseSelector().worker());
    }
    @Test void adapterRetainsLargeExactProvenanceAndOriginalSelectedOrder() throws IOException {
        JsonNode golden = golden(); ObjectNode snapshot = snapshot(golden); BigInteger revision = BigInteger.ONE.shiftLeft(80).add(BigInteger.ONE);
        snapshot.put("revision", revision); snapshot.put("native_revision", revision); snapshot.put("date_raw", revision.negate());
        assertEquals(revision, CombatRolesCodec.provenanceFromSnapshot(snapshot).revision());
        ArrayNode rows = StrictJson.object().putArray("rows"); rows.addObject().put("army_id", 31);
        rows.addObject().put("army_id", 11).putNull(CombatRolesCodec.MEMBER);
        ArrayNode output = CombatRolesCodec.projectSelectedRows(rows, snapshot);
        assertEquals(31, output.get(0).get("army_id").intValue()); assertEquals(11, output.get(1).get("army_id").intValue());
        assertFalse(output.get(0).path("projection").path("ready").booleanValue());
        assertEquals(revision, output.get(1).path("projection").path("source_provenance").path("revision").bigIntegerValue());
    }
}
