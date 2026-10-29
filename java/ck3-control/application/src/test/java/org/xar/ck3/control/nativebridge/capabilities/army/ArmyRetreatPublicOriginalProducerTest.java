package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;

/** Original Service order producer -> Java narrow public presenter; an ACK never spends independent lifecycle credit. */
final class ArmyRetreatPublicOriginalProducerTest {
    private static Obj obj(JsonNode n) { return DriverJson.object(ArmyJson.bytes(n), DriverJson.MAX_NATIVE_BYTES); }
    private static void pins() throws Exception {
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/tests/unit/test_active_combat_retreat_v1_bridge.py", "6bc83633125c25cda179f386e45a976d2f5ceeb6948588cebdefd3cdfdcfe42e");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py", "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/active_combat_retreat_contract.py", "29eccb1f6f6167a853f1273b662a56f289a276ef2676ffd4cef3ed8fb9b06cfe");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/service.py", "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e");
    }
    private static ObjectNode originals() throws Exception {
        pins(); ObjectNode result = BattleOriginalOracle.call("""
                import importlib.util,json
                path=root/'ck3_autonomous_player'/'tests'/'unit'/'test_active_combat_retreat_v1_bridge.py'
                spec=importlib.util.spec_from_file_location('xar_retreat_public_original',path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                rows=[]
                for name in ('accepted_no_push','accepted_post_push','rejected_route_changed'):
                    options={'publish_post_move':name=='accepted_post_push'}
                    if name=='rejected_route_changed':options['routes']=[[module.TARGET_PROVINCE],[module.MID_PROVINCE,module.TARGET_PROVINCE]]
                    driver,endpoint=module._driver(**options)
                    try:
                        service,preview=module._preview(driver)
                        before=service.snapshot()
                        ack=service.order_active_combat_retreat_v1(**module._order_arguments(preview))
                        rows.append({'name':name,'preview':preview,'before':before,'after':service.snapshot(),'ack':ack,'moves':endpoint.move_count})
                    finally:driver.close()
                print(json.dumps({'rows':rows},allow_nan=False))
                """, ArmyJson.empty()); pins(); return result;
    }
    private static ActiveRetreatProposal.Order order(ObjectNode preview) {
        var source = ActiveRetreatState.source(obj(preview.get("source_binding"))); var target = (ObjectNode)preview.get("target_preview");
        var args = new BattleRetreatPolicy.RetreatOrder(preview.get("selected_public_cunit_id").intValue(), source.revision(), preview.get("combat_id").intValue(), preview.get("side_index").intValue(),
                preview.get("side_scope").textValue().equals("full_side") ? BattleRetreatPolicy.Scope.FULL_SIDE : BattleRetreatPolicy.Scope.OWNER_SUBSET,
                preview.get("target_province_id").intValue(), target.get("candidate_token").textValue());
        return new ActiveRetreatProposal.Order(source, preview.get("selected_owner_character_id").intValue(), args,
                ArmyJson.array(preview.get("affected_public_cunit_ids_in_stored_order"), ArmyJson::i32), ArmyJson.array(preview.get("unaffected_same_side_public_cunit_ids_in_stored_order"), ArmyJson::i32),
                ArmyJson.array(target.get("route_province_ids"), ArmyJson::i32), new Obj(java.util.Map.of()));
    }
    @Test void originalAcceptedAndDefinitiveRejectedServiceACKsRetainEveryOriginalFieldAndNoLifecycleCredit() throws Exception {
        ObjectNode corpus = originals(); assertEquals(3, corpus.get("rows").size());
        for (JsonNode row : corpus.get("rows")) {
            String name = row.get("name").textValue(); ObjectNode expected = (ObjectNode)row.get("ack"), preview = (ObjectNode)row.get("preview");
            var order = order(preview); var before = BattlePublicOriginalProducerTest.captured((ObjectNode)row.get("before")); var after = BattlePublicOriginalProducerTest.captured((ObjectNode)row.get("after"));
            ObjectNode nativeSubmission = expected.get("accepted").booleanValue() ? (ObjectNode)expected.get("underlying_move_result")
                    : ArmyJson.empty().put("accepted", false).put("status", "rejected").put("rejection_reason", expected.get("rejection_reason").textValue());
            Obj result = ArmyRetreatPublicPresenter.order(order, new OperationKey(expected.get("step").textValue()), obj(nativeSubmission), Optional.of(after));
            assertEquals(obj(expected), result, name); assertEquals(20, ((ObjectNode)OpportunityJson.toNode(result)).size());
            var encoded = ArmyPublicWire.encode(result, before.context()); assertEquals(result, ArmyPublicWire.decode(encoded, before.context()), name);
            ObjectNode publicObject = ArmyJson.parse(encoded.bytes()); assertTrue(publicObject.get("expected_snapshot_revision").isTextual());
            assertTrue(publicObject.get("selected_public_cunit_id").isIntegralNumber()); assertTrue(publicObject.get("schema_version").isIntegralNumber());
            assertFalse(publicObject.get("semantic_postcondition").get("full_postcondition_verified").booleanValue());
            assertFalse(publicObject.get("semantic_postcondition").get("combat_id_post_query_performed").booleanValue());
            assertEquals(name.startsWith("accepted") ? 1 : 0, row.get("moves").intValue());
            ObjectNode internalPreview = preview.deepCopy().put("contract_stage", ArmyRetreatTokens.STAGE);
            assertEquals(obj(preview), ArmyRetreatPublicPresenter.preview(obj(internalPreview)), "historical schema literal is not implementation provenance");
            assertEquals(ArmyRetreatTokens.STAGE, internalPreview.get("contract_stage").textValue());
        }
    }
    @Test void missingPartialObservationRemainsPendingAndMalformedNativeACKCannotBecomeARejectionOrSuccess() throws Exception {
        JsonNode row = originals().get("rows").get(1); var order = order((ObjectNode)row.get("preview")); var expected = (ObjectNode)row.get("ack");
        Obj actualNative = obj(expected.get("underlying_move_result")); var step = new OperationKey(expected.get("step").textValue());
        ObjectNode pending = (ObjectNode)OpportunityJson.toNode(ArmyRetreatPublicPresenter.order(order, step, actualNative, Optional.empty()));
        assertEquals("accepted_verification_pending", pending.get("status").textValue()); assertEquals("observation_pending", pending.get("semantic_postcondition").get("status").textValue());
        assertTrue(pending.get("semantic_postcondition").get("observation_native_revision").isNull());
        assertThrows(IllegalArgumentException.class, () -> ArmyRetreatPublicPresenter.order(order, step, obj(ArmyJson.empty().put("accepted", true).put("status", "unknown")), Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> ArmyRetreatPublicPresenter.order(order, step, obj(ArmyJson.empty().put("accepted", false).put("status", "unknown")), Optional.empty()));
        var claimed = ActiveRetreatState.reduce(ActiveRetreatState.reduce(ActiveRetreatState.reduce(ActiveRetreatState.State.initial(), new ActiveRetreatState.StartPreview(order.source())),
                new ActiveRetreatState.FinishPreview(order.source(), obj(((ObjectNode)row.get("preview")).deepCopy().put("contract_stage", ArmyRetreatTokens.STAGE)))), new ActiveRetreatState.StartOrder(order));
        var unknown = ActiveRetreatState.reduce(claimed, new ActiveRetreatState.UnknownOrder(ActiveRetreatState.ClaimKey.of(order), "actual unavailable original child"));
        var restored = ActiveRetreatState.decode(DriverJson.object(DriverJson.encode(ActiveRetreatState.encode(unknown)), DriverJson.MAX_NATIVE_BYTES));
        assertEquals(unknown, restored); assertThrows(IllegalArgumentException.class, () -> ActiveRetreatState.reduce(restored, new ActiveRetreatState.StartOrder(order)));
    }
}
