package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.contracts.StrictJson;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.m0.RaiktorExitPostcondition;
import org.xar.ck3.control.g2.m0.RaiktorExitPostwarEvidence;
import static org.junit.jupiter.api.Assertions.*;

/** Actual retained original producers -> Java source/current/cleanup/truce join -> complete postcondition consumer. */
final class RaiktorPostwarMigrationTest {
    private static ObjectNode captured;
    @Test void originalBothTerminationRoutesFeedTheRealJavaEvidenceAndPostconditionConsumers() throws Exception {
        for (JsonNode vector : vectors().path("cases")) {
            ObjectNode inputs = (ObjectNode) vector.path("inputs");
            ObjectNode evidence = evidence(inputs);
            sameJson(vector.path("expected_evidence"), evidence);
            ObjectNode result = RaiktorExitPostcondition.provide(inputs.path("action_gate_value"), vector.path("action_result"),
                    inputs.path("post_snapshot_value"), evidence.path("postwar_evidence"), vector.path("checkpoint_restore"));
            sameJson(vector.path("expected_postcondition"), result);
            assertTrue(result.path("postcondition_verified").booleanValue());
            assertTrue(result.path("gen034_closed").booleanValue());
        }
    }
    @Test void actualFrozenPlanProducerCannotBorrowAnAckOrAnotherSourceGeneration() throws Exception {
        ObjectNode vector = (ObjectNode) vectors().path("cases").get(0);
        ObjectNode inputs = (ObjectNode) vector.path("inputs"), gate = (ObjectNode) inputs.path("action_gate_value");
        ObjectNode missing = RaiktorExitPostcondition.provide(gate, vector.path("action_result"), inputs.path("post_snapshot_value"), null, null);
        assertEquals("evidence_required", missing.path("status").textValue()); assertFalse(missing.path("gen034_closed").booleanValue());
        ObjectNode drift = inputs.deepCopy(); ObjectNode regiment = (ObjectNode) drift.path("active_war_bound_value").path("regiments").get(0);
        regiment.put("persistent_regiment_id", regiment.path("persistent_regiment_id").intValue() + 1000);
        assertThrows(IllegalArgumentException.class, () -> evidence(drift));
        ObjectNode crossedBuild = inputs.deepCopy();
        ((ObjectNode) crossedBuild.path("source_capture_value")).put("exe_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        assertThrows(IllegalArgumentException.class, () -> evidence(crossedBuild), "old source creation capture must never qualify current .4");
        ObjectNode skippedSequence = inputs.deepCopy();
        ((ObjectNode) skippedSequence.path("truce_result_values").get(1)).put("query_sequence", 12);
        assertThrows(IllegalArgumentException.class, () -> evidence(skippedSequence));
        JsonNode authorization = gate.path("authorization"), action = authorization.path("action");
        ObjectNode actualFrozen = RaiktorExitPostcondition.bindFrozenPlan(authorization.path("frame"), authorization.path("postcondition_plan"),
                action.path("literal").textValue(), action.path("semantic_action").textValue());
        ObjectNode adapted = inputs.deepCopy(); adapted.set("action_gate_value", actualFrozen);
        ObjectNode adaptedEvidence = evidence(adapted);
        assertTrue(RaiktorExitPostcondition.provide(actualFrozen, vector.path("action_result"), adapted.path("post_snapshot_value"),
                adaptedEvidence.path("postwar_evidence"), vector.path("checkpoint_restore")).path("gen034_closed").booleanValue());
        assertThrows(IllegalArgumentException.class, () -> RaiktorExitPostcondition.bindFrozenPlan(authorization.path("frame"),
                authorization.path("postcondition_plan"), "surrender-war-1", action.path("semantic_action").textValue()));
    }
    private static ObjectNode evidence(ObjectNode inputs) {
        return RaiktorExitPostwarEvidence.provide(inputs.path("action_gate_value"), inputs.path("source_capture_value"),
                inputs.path("source_capture_sha256").textValue(), inputs.path("active_war_bound_value"), inputs.path("post_snapshot_value"),
                inputs.path("cleanup_result_value"), inputs.path("truce_result_values"));
    }
    private static synchronized ObjectNode vectors() throws Exception {
        if (captured == null) {
            verifyOriginals();
            captured = BattleOriginalOracle.call("""
                    import json,sys
                    sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
                    from test_raiktor_three_way_exit_postwar_evidence import _inputs
                    from test_raiktor_three_way_exit_postcondition import _action_result,_checkpoint_restore
                    from xar_autoplayer.simulation.raiktor_three_way_exit_postwar_evidence import provide_raiktor_three_way_exit_postwar_evidence
                    from xar_autoplayer.simulation.raiktor_three_way_exit_postcondition import provide_raiktor_three_way_exit_postcondition
                    cases=[]
                    for route in ('white_peace','surrender'):
                        inputs=_inputs(route)
                        gate=inputs['action_gate_value'];post=inputs['post_snapshot_value']
                        evidence=provide_raiktor_three_way_exit_postwar_evidence(**inputs)
                        action=_action_result(gate,post);checkpoint=_checkpoint_restore(gate,post)
                        result=provide_raiktor_three_way_exit_postcondition(gate,action,post,evidence['postwar_evidence'],checkpoint)
                        cases.append({'inputs':inputs,'expected_evidence':evidence,'action_result':action,
                                      'checkpoint_restore':checkpoint,'expected_postcondition':result})
                    print(json.dumps({'cases':cases},allow_nan=False))
                    """, ArmyJson.empty());
            verifyOriginals();
        }
        return captured.deepCopy();
    }
    private static void verifyOriginals() throws Exception {
        String configured = System.getProperty("xar.repository.root");
        if (configured == null || configured.isBlank()) throw new IllegalStateException("required original producer root is absent");
        Path root = Path.of(configured).toRealPath();
        String[][] pins = {
            {"ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_three_way_exit_postcondition.py","c02e45da6dbe09c3467f38679fe9f5d38e208dd96b87c3d9aa08b032558f441b"},
            {"ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_three_way_exit_postwar_evidence.py","cea277919ec652ad3c782432142a05ed1196e79a188f949b1dd5dea62606ed98"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_source_specific_war_loss_contract.py","aefcd4ba93f4435509650e533c84e4e352472a125a7f4379a9d4b143ca97e4cb"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_war_bound_regiment_contract.py","314c814f56638466580b073e7c926420b588f70f201e94fef5b1b96100783205"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_war_bound_loss_cleanup_contract.py","11c7b77842676251bdb1516472cb15d4115105d4a7b3ab5b994b3430f5f48c61"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_actual_truce_expiry_contract.py","55fe165e5c001cd6858c4c47345fc8343dc270c9d77b7db9678e2d5596cf405c"},
            {"ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_three_way_exit_action_gate.py","c000021ef96f3d8796086cf89027ef3bfb934811fe1625248d00333d4dabf5f0"},
            {"ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_three_way_exit_recommendation.py","65d9faea5f3069a2f16c32fef876521690dc915ee5fbf2f856095098e5f4d0da"},
            {"ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_postcondition.py","c844f1b081141a3789597c7fff9dd3e4c66da2a27876f6c80ac165794d2e2895"},
            {"ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_postwar_evidence.py","f7a654d80dbdb9666019bdfeee135e0b2b5f16afec95ee889980874bf0be56e7"},
            {"ck3_autonomous_player/tests/unit/test_g2_source_specific_war_loss_lifecycle.py","a6ae53a84161a92b1c1d772a661412161d54456e3ff205fae4ca0eddc7a25f71"}};
        for (String[] pin : pins) {
            Path file = root.resolve(pin[0]).toRealPath(); assertTrue(file.startsWith(root));
            assertEquals(pin[1], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), "actual original postwar source drift");
        }
    }
    private static void sameJson(JsonNode expected, JsonNode actual) {
        assertEquals(new String(StrictJson.canonical(expected), StandardCharsets.UTF_8), new String(StrictJson.canonical(actual), StandardCharsets.UTF_8));
    }
}
