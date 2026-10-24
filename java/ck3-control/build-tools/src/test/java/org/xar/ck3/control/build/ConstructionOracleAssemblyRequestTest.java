package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

final class ConstructionOracleAssemblyRequestTest {
    private static final String ORACLE =
            "f159d71fdf3086bf75300208ab63fc7bdedc1fea1eeb6a63fcb4a553f37e0d8f";
    private static ControlBuild.FileRef ref(long bytes, String sha) {
        return new ControlBuild.FileRef("D:/synthetic-not-original-capture/input", bytes, sha);
    }

    @Test void historicalClientCannotOccupyCurrentConsumerRole() {
        assertThrows(IllegalArgumentException.class, () ->
                new ConstructionOracleAssemblyRequest.SelectedClient(
                        ref(20532, "bc2bb7240e12fdd8b42c7e1fa37fb5e0b16c865e5081b31b25c4844574ce8557"),
                        "tools.g2_saved_campaign.java_map_admission_client_v1",
                        ConstructionOracleAssemblyRequest.ClientRole.ROOT_SELECTED_CONSUMER_155));
    }

    @Test void originalRoleRequiresExactPinnedBytes() {
        assertThrows(IllegalArgumentException.class, () ->
                new ConstructionOracleAssemblyRequest.ReferenceSource(ref(25678, ORACLE),
                        "ck3_autonomous_player/tests/unit/construction_python_oracle_v1.py",
                        ConstructionOracleAssemblyRequest.ProducerRole.REFERENCE_ORACLE));
    }

    @Test void referenceOriginalCannotReplaceCurrentClient() {
        assertThrows(IllegalArgumentException.class, () ->
                new ConstructionOracleAssemblyRequest.ReferenceSource(ref(25679, ORACLE),
                        "tools/g2_saved_campaign/java_map_admission_client_v1.py",
                        ConstructionOracleAssemblyRequest.ProducerRole.REFERENCE_ORACLE));
    }

    @Test void serializationPreservesExactOriginalIdentityAndRole() throws Exception {
        var original = new ConstructionOracleAssemblyRequest.ReferenceSource(ref(25679, ORACLE),
                "ck3_autonomous_player/tests/unit/construction_python_oracle_v1.py",
                ConstructionOracleAssemblyRequest.ProducerRole.REFERENCE_ORACLE);
        byte[] json = ControlBuild.strictMapper().writeValueAsBytes(original);
        assertEquals(original, ControlBuild.strictMapper().readValue(json,
                ConstructionOracleAssemblyRequest.ReferenceSource.class));
        String unknown = new String(json, StandardCharsets.UTF_8).replaceFirst("\\{", "{\"actual_http\":true,");
        assertThrows(Exception.class, () -> ControlBuild.strictMapper().readValue(unknown,
                ConstructionOracleAssemblyRequest.ReferenceSource.class));
    }

    @Test void requestFileSizesCannotCoerceBooleanFloatingPointOrString() {
        for (String token : List.of("true", "25679.0", "\"25679\"")) {
            byte[] bad = ("{\"reference_sources\":[{\"source_ref\":{\"bytes\":" + token + "}}]}")
                    .getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () ->
                    ConstructionOracleAssemblyRequest.read(bad));
        }
    }

    @Test void sceneAndQueryRetainTheirActualOriginalTestInputs() {
        assertEquals(List.of(
                "ck3_autonomous_player/tests/unit/test_construction_formal_private_consumer.py",
                "ck3_autonomous_player/tests/unit/test_construction_monthly_budget_v1.py",
                "ck3_autonomous_player/tests/unit/test_clan_construction_scope_cash_compound_v1.py"),
                ConstructionOracleAssemblyRequest.requiredInputRelativePaths(ConstructionOracleAssemblyRequest.Leaf.SCENE));
        assertEquals(List.of(
                "ck3_autonomous_player/tests/unit/test_construction_formal_private_consumer.py",
                "ck3_autonomous_player/tests/unit/fixtures/construction_material_outside_projection.json"),
                ConstructionOracleAssemblyRequest.requiredInputRelativePaths(ConstructionOracleAssemblyRequest.Leaf.QUERY));
    }

    @Test void absentSceneInputsCannotInheritStandardReadiness() {
        assertThrows(IllegalArgumentException.class, () ->
                ConstructionOracleAssemblyRequest.selectCaptureInputRefs(
                        ConstructionOracleAssemblyRequest.Leaf.SCENE,
                        java.nio.file.Path.of(System.getProperty("java.io.tmpdir")), List.of(), List.of()));
        assertEquals(1, ConstructionOracleAssemblyRequest.requiredInputRelativePaths(
                ConstructionOracleAssemblyRequest.Leaf.INCOME).size());
        assertEquals(2, ConstructionOracleAssemblyRequest.requiredInputRelativePaths(
                ConstructionOracleAssemblyRequest.Leaf.READBACK).size());
    }

    @Test void leafInputMetadataCannotGrantExecutionCredit() {
        assertThrows(IllegalArgumentException.class, () ->
                new ConstructionOracleAssemblyRequest.CaptureInputs(
                        "xar.construction-capture-inputs/v1", ConstructionOracleAssemblyRequest.Leaf.INCOME,
                        ref(1, ORACLE), List.of(), true));
    }

    @Test void sourcePlanNeverGrantsExecutionCredit() {
        assertThrows(IllegalArgumentException.class, () ->
                new ConstructionOracleAssemblyRequest.Plan(
                        "xar.construction-oracle-assembly-plan/v1", "synthetic-machine",
                        ConstructionOracleAssemblyRequest.Boundary.SOURCE_PLAN_ONLY,
                        ref(1, ORACLE), null, List.of(), null, List.of(), true, false, false));
    }
}
