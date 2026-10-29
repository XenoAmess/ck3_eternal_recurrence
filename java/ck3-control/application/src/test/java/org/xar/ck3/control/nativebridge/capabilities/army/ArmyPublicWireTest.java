package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original retained Python producer -> full M5 normalization -> lossless public JSON -> same strict domain. */
final class ArmyPublicWireTest {
    @Test void originalRetreatProducerFeedsTheSingleTokenConsumerAndDurableNoReplayReducer() throws Exception {
        verifyRetreatOriginals(); ObjectNode original = BattleOriginalOracle.call("""
                import importlib.util,json
                path=root/'ck3_autonomous_player'/'tests'/'unit'/'test_active_combat_retreat_v1_bridge.py'
                spec=importlib.util.spec_from_file_location('xar_retreat_original_fixture',path)
                module=importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                driver,endpoint=module._driver()
                service,preview=module._preview(driver)
                print(json.dumps({'preview':preview,'token':driver._active_combat_retreat_v1_token},allow_nan=False))
                """, ArmyJson.empty());
        ObjectNode preview = ((ObjectNode) original.get("preview")).deepCopy(); preview.put("contract_stage", ArmyRetreatTokens.STAGE);
        var source = org.xar.ck3.control.application.planning.military.ActiveRetreatState.source(DriverJson.object(ArmyJson.bytes(preview.get("source_binding")), DriverJson.MAX_NATIVE_BYTES));
        var state = org.xar.ck3.control.application.planning.military.ActiveRetreatState.State.initial();
        state = org.xar.ck3.control.application.planning.military.ActiveRetreatState.reduce(state, new org.xar.ck3.control.application.planning.military.ActiveRetreatState.StartPreview(source));
        state = org.xar.ck3.control.application.planning.military.ActiveRetreatState.reduce(state, new org.xar.ck3.control.application.planning.military.ActiveRetreatState.FinishPreview(source, DriverJson.object(ArmyJson.bytes(preview), DriverJson.MAX_NATIVE_BYTES)));
        assertEquals(original.get("token"), OpportunityJson.toNode(ArmyRetreatTokens.capabilityToken(state).orElseThrow()));
        var target = (ObjectNode) preview.get("target_preview");
        var args = new org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.RetreatOrder(preview.get("selected_public_cunit_id").intValue(), source.revision(), preview.get("combat_id").intValue(), preview.get("side_index").intValue(),
                preview.get("side_scope").textValue().equals("full_side") ? org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Scope.FULL_SIDE : org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Scope.OWNER_SUBSET,
                preview.get("target_province_id").intValue(), target.get("candidate_token").textValue());
        var order = new org.xar.ck3.control.application.planning.military.ActiveRetreatProposal.Order(source, preview.get("selected_owner_character_id").intValue(), args,
                ArmyJson.array(preview.get("affected_public_cunit_ids_in_stored_order"), ArmyJson::i32), ArmyJson.array(preview.get("unaffected_same_side_public_cunit_ids_in_stored_order"), ArmyJson::i32), ArmyJson.array(target.get("route_province_ids"), ArmyJson::i32), new Obj(java.util.Map.of()));
        var claimed = org.xar.ck3.control.application.planning.military.ActiveRetreatState.reduce(state, new org.xar.ck3.control.application.planning.military.ActiveRetreatState.StartOrder(order));
        assertTrue(ArmyRetreatTokens.capabilityToken(claimed).isEmpty()); assertTrue(claimed.preview().isEmpty());
        var unknown = org.xar.ck3.control.application.planning.military.ActiveRetreatState.reduce(claimed, new org.xar.ck3.control.application.planning.military.ActiveRetreatState.UnknownOrder(org.xar.ck3.control.application.planning.military.ActiveRetreatState.ClaimKey.of(order), "source-shaped unknown"));
        var restored = org.xar.ck3.control.application.planning.military.ActiveRetreatState.decode(DriverJson.object(DriverJson.encode(org.xar.ck3.control.application.planning.military.ActiveRetreatState.encode(unknown)), DriverJson.MAX_NATIVE_BYTES));
        assertEquals(unknown, restored); assertThrows(IllegalArgumentException.class, () -> org.xar.ck3.control.application.planning.military.ActiveRetreatState.reduce(restored, new org.xar.ck3.control.application.planning.military.ActiveRetreatState.StartOrder(order)));
    }
    private static void verifyRetreatOriginals() throws Exception {
        String configured = System.getProperty("xar.repository.root"); if (configured == null || configured.isBlank()) throw new IllegalStateException("required original-producer property missing: xar.repository.root");
        var root = java.nio.file.Path.of(configured).toRealPath();
        String[][] pins = {
                {"ck3_autonomous_player/tests/unit/test_active_combat_retreat_v1_bridge.py", "6bc83633125c25cda179f386e45a976d2f5ceeb6948588cebdefd3cdfdcfe42e"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py", "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/active_combat_retreat_contract.py", "29eccb1f6f6167a853f1273b662a56f289a276ef2676ffd4cef3ed8fb9b06cfe"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py", "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"}};
        for (String[] pin : pins) { var file = root.resolve(pin[0]).toRealPath(); assertTrue(file.startsWith(root)); byte[] bytes = java.nio.file.Files.readAllBytes(file); assertEquals(pin[1], java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)), "actual original retreat producer drift"); }
    }
    @Test void actualOriginalProducerRoundTripsEveryNestedIntegerWithoutChangingNativeBytes() throws Exception {
        ObjectNode frame = (ObjectNode) BattleOriginalOracle.fixture().get("parent"); int subject = frame.get("subject_public_cunit_id").intValue();
        BigInteger revision = frame.get("snapshot_revision").bigIntegerValue(); long date = frame.get("observed_date_raw").longValue();
        ObjectNode original = BattleOriginalOracle.normalizeControl(frame, subject, revision, date); byte[] bytes = ArmyJson.bytes(original);
        Obj normalized = BattleResponseCodec.normalizeControl(DriverJson.object(bytes, DriverJson.MAX_NATIVE_BYTES), subject, revision, date);
        Context context = context(original.get("selected_owner_character_id").bigIntegerValue(), revision, date);
        RawJson publicValue = ArmyPublicWire.encode(normalized, context); Obj restored = ArmyPublicWire.decode(publicValue, context);
        assertEquals(publicValue, ArmyPublicWire.encode(restored, context));
        assertEquals(publicValue, ArmyPublicWire.encode(BattleResponseCodec.normalizeControl(restored, subject, revision, date), context));
        assertArrayEquals(bytes, ArmyJson.bytes(original)); assertTrue(ArmyJson.parse(publicValue.bytes()).get("snapshot_revision").isTextual());
        ObjectNode changed = ArmyJson.parse(publicValue.bytes()).deepCopy(); changed.put("snapshot_revision", "0005");
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decode(new RawJson(ArmyJson.bytes(changed)), context));
        ObjectNode retyped = ArmyJson.parse(publicValue.bytes()).deepCopy().put("side_index", true);
        Obj malformed = ArmyPublicWire.decode(new RawJson(ArmyJson.bytes(retyped)), context);
        assertThrows(IllegalArgumentException.class, () -> BattleResponseCodec.normalizeControl(malformed, subject, revision, date), "public serialization does not confer native domain qualification");
        assertTrue(ArmyJson.parse(publicValue.bytes()).get("side_index").isIntegralNumber());
        assertFalse(ArmyJson.parse(publicValue.bytes()).has("integer_paths"));
        assertFalse(ArmyJson.parse(publicValue.bytes()).has("public_wire_schema"));
    }
    @Test void fullUnsignedAndSigned64NullMissingAndNumericLookingTextHaveSeparateDomains() {
        ObjectNode raw = ArmyJson.empty().put("sequence", new BigInteger("18446744073709551615")).put("date_raw", Integer.MIN_VALUE).put("combat", Integer.MIN_VALUE).put("unit", 0).put("opaque", "001").put("boolean", true);
        raw.putNull("nullable"); raw.putArray("route").add(1).add(2); raw.putObject("generation").put("creation_filetime", new BigInteger("9007199254740993"));
        Obj value = DriverJson.object(ArmyJson.bytes(raw), DriverJson.MAX_NATIVE_BYTES); Context source = context(BigInteger.ONE, BigInteger.ONE, 1);
        RawJson encoded = ArmyPublicWire.encode(value, source); ObjectNode publicValue = ArmyJson.parse(encoded.bytes());
        assertEquals("18446744073709551615", publicValue.get("sequence").textValue()); assertEquals(Integer.MIN_VALUE, publicValue.get("date_raw").intValue());
        assertTrue(publicValue.get("combat").isIntegralNumber()); assertTrue(publicValue.get("route").get(0).isIntegralNumber());
        assertEquals("001", publicValue.get("opaque").textValue()); assertTrue(publicValue.get("boolean").isBoolean()); assertTrue(publicValue.get("nullable").isNull()); assertFalse(publicValue.has("missing"));
        assertEquals(value, ArmyPublicWire.decode(encoded, source));
        for (String invalid : List.of("-0", "+1", "01", "1.0")) { ObjectNode changed = publicValue.deepCopy().put("sequence", invalid); assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decode(new RawJson(ArmyJson.bytes(changed)), source)); }
        ObjectNode rounded = publicValue.deepCopy().put("sequence", 18446744073709551615.0); assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decode(new RawJson(ArmyJson.bytes(rounded)), source));
        ObjectNode falsePath = publicValue.deepCopy(); falsePath.putArray("integer_paths").add("/sequence"); assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decode(new RawJson(ArmyJson.bytes(falsePath)), source));
        ObjectNode unsafe = raw.deepCopy().put("unregistered_numeric_counter", new BigInteger("9007199254740993"));
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encode(DriverJson.object(ArmyJson.bytes(unsafe), DriverJson.MAX_NATIVE_BYTES), source));
    }
    @Test void actualOriginalMarketRetainsUnsigned32NumbersAndAllTenSigned64ResourceAmounts() throws Exception {
        var original = ArmyMercenaryOriginalProducerTest.original();
        var nativeResult = ((ObjectNode) original.get("result")).deepCopy();
        var snapshot = (ObjectNode) original.get("snapshot");
        var actual = ArmyMercenaryContextCodec.decode(DriverJson.object(ArmyJson.bytes(nativeResult.get("player_mercenary_context")), DriverJson.MAX_NATIVE_BYTES),
                DriverJson.object(ArmyJson.bytes(snapshot), DriverJson.MAX_NATIVE_BYTES));
        nativeResult.set("player_mercenary_context", OpportunityJson.toNode(actual.normalized()));
        nativeResult.remove(List.of("queried_snapshot_id", "queried_revision", "queried_native_revision"));
        var c = context(actual.actor(), snapshot.get("native_revision").bigIntegerValue(), actual.dateRaw().longValueExact());
        var wire = ArmyPublicWire.encode(DriverJson.object(ArmyJson.bytes(nativeResult), DriverJson.MAX_NATIVE_BYTES), c);
        var publicResult = ArmyJson.parse(wire.bytes()); var company = publicResult.get("player_mercenary_context").get("rows").get(0);
        assertTrue(company.get("company_id").isIntegralNumber());
        assertEquals("-9223372036854775808", company.get("final_terms").get("resource_costs_raw").get(1).textValue());
        assertEquals("9223372036854775807", company.get("final_terms").get("resource_costs_raw").get(2).textValue());
        var restored = ArmyPublicWire.decode(wire, c);
        assertEquals(actual.normalized(), ArmyMercenaryContextCodec.decode((Obj) restored.get("player_mercenary_context"), DriverJson.object(ArmyJson.bytes(snapshot), DriverJson.MAX_NATIVE_BYTES)).normalized());
        assertEquals(wire, ArmyPublicWire.encode(restored, c));
    }
    private static Context context(BigInteger actor, BigInteger nativeRevision, long date) {
        var ref = new ExactRef("original-fixture-source", 1, "a".repeat(64)); var source = new G2Source("source-shaped-test-machine", "2026-10-24T00:00:00Z", "1.20.0.4", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor, nativeRevision, BigInteger.valueOf(date)), "fixture:" + nativeRevision, BigInteger.valueOf(9), "fixture-episode");
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "fixture-session", Instant.parse("2026-10-24T00:01:00Z"));
    }
}
