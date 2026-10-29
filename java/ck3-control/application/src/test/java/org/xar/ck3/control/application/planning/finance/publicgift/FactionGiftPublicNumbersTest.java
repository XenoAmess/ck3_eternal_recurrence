package org.xar.ck3.control.application.planning.finance.publicgift;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.*;

/** Known path projection only; real native/ledger codecs remain mandatory before business authority. */
final class FactionGiftPublicNumbersTest {
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    @Test void originalWideCandidateFieldsRoundTripAndOpaqueDecimalLexemesRemainExact() {
        RawJson original = raw("{\"status\":\"selected\",\"choice\":{\"snapshot_revision\":18446744073709551615,"
                + "\"native_snapshot_revision\":18446744073709551615,\"definition_stable_hash\":18446744073709551615,"
                + "\"gold_cost_raw\":9223372036854775807,\"minimum_gold_reserve_raw\":1606938044258990275541962092341162602522202993782792835301376},"
                + "\"observation\":{\"snapshot_revision\":18446744073709551615,\"native_snapshot_revision\":18446744073709551615,"
                + "\"player_gold_raw\":-9223372036854775808,\"source_faction_power_raw\":9223372036854775807,"
                + "\"source_faction_discontent_raw\":7,\"recipient_character_id\":303,\"opaque_decimal\":-0.0,"
                + "\"gift_preview\":{\"definition_stable_hash\":18446744073709551615,\"gold_cost_raw\":9223372036854775807}}}");
        RawJson projected = FactionGiftPublicCodec.businessPublic(Method.CANDIDATE, original);
        var node = StrictJson.parse(projected.bytes(), MAX_ARGUMENT_BYTES);
        assertEquals("18446744073709551615", node.path("choice").get("definition_stable_hash").textValue());
        assertEquals("-9223372036854775808", node.path("observation").get("player_gold_raw").textValue());
        assertTrue(node.path("observation").get("recipient_character_id").isIntegralNumber());
        assertTrue(new String(projected.bytes(), StandardCharsets.UTF_8).contains("-0.0"));
        RawJson restored = FactionGiftPublicCodec.businessNative(Method.CANDIDATE, projected);
        assertEquals(DriverJson.object(original.bytes(), MAX_ARGUMENT_BYTES), DriverJson.object(restored.bytes(), MAX_ARGUMENT_BYTES));
        assertEquals(DriverJson.object(original.bytes(), MAX_ARGUMENT_BYTES),
                DriverJson.object(FactionGiftPublicCodec.candidateNative(projected).bytes(), MAX_ARGUMENT_BYTES));
    }
    @Test void pendingAndRootIngressConvertOnlyDeclaredFieldsAndPreserveMissingNullAndOriginalProcessText() {
        RawJson pending = FactionGiftPublicCodec.pendingNative(raw("{\"pre_snapshot_revision\":\"18446744073709551615\","
                + "\"pre_native_snapshot_revision\":null,\"pre_player_gold_raw\":\"-9223372036854775808\","
                + "\"minimum_gold_reserve_raw\":\"-1\",\"source_bridge_creation_date\":\"202610240101.000000+480\","
                + "\"source_faction_id\":303,\"extension_decimal\":1.0}"));
        var node = StrictJson.parse(pending.bytes(), MAX_ARGUMENT_BYTES);
        assertTrue(node.get("pre_snapshot_revision").isIntegralNumber());
        assertTrue(node.get("pre_native_snapshot_revision").isNull()); assertFalse(node.has("post_snapshot_revision"));
        assertEquals("202610240101.000000+480", node.get("source_bridge_creation_date").textValue());
        assertTrue(node.get("source_faction_id").isIntegralNumber());
        assertTrue(new String(pending.bytes(), StandardCharsets.UTF_8).contains("1.0"));
        var root = StrictJson.parse(FactionGiftPublicCodec.rootNative(raw("{\"snapshot_revision\":\"18446744073709551615\",\"player_character_id\":303}")).bytes());
        assertTrue(root.get("snapshot_revision").isIntegralNumber()); assertEquals(303, root.get("player_character_id").intValue());
    }
    @Test void unknownWideFieldsAndInvalidKnownNumbersCannotBeSilentlyCoercedOrRounded() {
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPublicCodec.businessPublic(Method.CANDIDATE,
                raw("{\"observation\":{\"unknown_extension\":18446744073709551615}}")));
        for (String token : new String[]{"true", "1.0", "\"01\"", "\"-0\"", "18446744073709551615"})
            assertThrows(IllegalArgumentException.class, () -> FactionGiftPublicCodec.rootNative(raw("{\"snapshot_revision\":" + token + "}")));
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPublicCodec.businessPublic(Method.CANDIDATE,
                raw("{\"observation\":{\"player_gold_raw\":9223372036854775808}}")));
    }
    @Test void requestObjectSerdePreservesOriginalDecimalCategoriesBeforeTheActualDomainCodec() {
        var request = FactionGiftPublicCodec.decode(Method.CANDIDATE,
                raw("{\"expected_revision\":56,\"same_frame_root\":{\"opaque\":-0.0,\"opaque_integral_decimal\":1.0}}"));
        RawJson encoded = FactionGiftPublicCodec.encode(request);
        String text = new String(encoded.bytes(), StandardCharsets.UTF_8);
        assertTrue(text.contains("-0.0")); assertTrue(text.contains("1.0"));
        assertEquals(request, FactionGiftPublicCodec.decode(Method.CANDIDATE, encoded));
    }
    @Test void actualAppliedCompatibleSourceFrameUsesTheDeclaredWideRevisionPaths() {
        // NativeFinanceEffects.observe appends frame(after) as compatibleResult.source_frame.
        // Keep date and character IDs in their bounded native domain.
        RawJson nativeResult = raw("{\"status\":\"applied\",\"postcondition_verified\":true,\"source_frame\":{"
                + "\"played_character_id\":303,\"native_revision\":18446744073709551615,"
                + "\"date_raw\":53153304,\"snapshot_id\":\"native-after\","
                + "\"revision\":18446744073709551615,\"episode_run_id\":\"episode\"}}");
        for (Method method : new Method[]{Method.SEND, Method.RECEIPT, Method.COLD_RECOVERY}) {
            RawJson publicResult = FactionGiftPublicCodec.businessPublic(method, nativeResult);
            var frame = StrictJson.parse(publicResult.bytes()).get("source_frame");
            assertEquals("18446744073709551615", frame.get("revision").textValue());
            assertEquals("18446744073709551615", frame.get("native_revision").textValue());
            assertTrue(frame.get("played_character_id").isIntegralNumber());
            assertTrue(frame.get("date_raw").isIntegralNumber());
            assertEquals(DriverJson.object(nativeResult.bytes(), MAX_ARGUMENT_BYTES),
                    DriverJson.object(FactionGiftPublicCodec.businessNative(method, publicResult).bytes(), MAX_ARGUMENT_BYTES));
        }
    }
}
