package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import java.nio.charset.StandardCharsets;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeUiParsedReturn;
import static org.junit.jupiter.api.Assertions.*;

final class GuiPublicMetadataTest {
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }

    @Test void actualPublicWideRolesPreserveNullBoundedIdsAndOriginalDecimalTokens() {
        RawJson original=raw("{\"queried_connection_generation\":18446744073709551615,\"gui_context_address\":9007199254740993,\"gui_owner_address\":18446744073709551615,\"army_tooltip\":{\"action_owner_epoch\":9007199254740993,\"later_owner_epoch\":null},\"subject_army_id\":73,\"metric\":1.00}");
        var exported=GuiCodec.encodePublicOriginal(original);var tree=PublicDataJson.object(exported);
        assertEquals("18446744073709551615",tree.get("queried_connection_generation").textValue());
        assertEquals("9007199254740993",tree.get("gui_context_address").textValue());
        assertEquals("18446744073709551615",tree.get("gui_owner_address").textValue());
        assertEquals("9007199254740993",tree.path("army_tooltip").get("action_owner_epoch").textValue());
        assertTrue(tree.path("army_tooltip").get("later_owner_epoch").isNull());
        assertTrue(tree.get("subject_army_id").isIntegralNumber());
        assertEquals(73,tree.get("subject_army_id").intValue());
        assertTrue(new String(exported.bytes(),StandardCharsets.UTF_8).contains("1.00"));
        assertArrayEquals(exported.bytes(),GuiCodec.encodePublicOriginal(exported).bytes());
        for(String bad:Set.of("true","1.5","-1","18446744073709551616","\"01\""))
            assertThrows(IllegalArgumentException.class,()->GuiCodec.encodePublicOriginal(raw("{\"queried_connection_generation\":"+bad+"}")));
    }

    @Test void parsedReferenceRequiresAllFourActualFieldsAndNeverAcceptsValidationCredit() {
        var valid=StrictJson.object().put("path","D:/ck3-state/original.json").put("bytes",1)
                .put("sha256","a".repeat(64)).put("validation_state","unvalidated");
        assertDoesNotThrow(()->GuiPublicMetadata.requireParsedReturnReference(new RawJson(StrictJson.canonical(valid))));
        var atCap=valid.deepCopy().put("bytes",NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
        assertDoesNotThrow(()->GuiPublicMetadata.requireParsedReturnReference(new RawJson(StrictJson.canonical(atCap))));
        var overCap=valid.deepCopy().put("bytes",((long)NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES)+1);
        assertThrows(IllegalArgumentException.class,()->GuiPublicMetadata.requireParsedReturnReference(new RawJson(StrictJson.canonical(overCap))));
        for(String field:Set.of("path","bytes","sha256","validation_state")){
            var missing=valid.deepCopy();missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->GuiPublicMetadata.requireParsedReturnReference(new RawJson(StrictJson.canonical(missing))));
        }
        for(var bad:java.util.List.of(valid.deepCopy().put("bytes",true),valid.deepCopy().put("bytes",1.0),
                valid.deepCopy().put("validation_state","validated"),valid.deepCopy().put("unexpected",0)))
            assertThrows(IllegalArgumentException.class,()->GuiPublicMetadata.requireParsedReturnReference(new RawJson(StrictJson.canonical(bad))));
    }

    @Test void declaredEventUsesTheOriginalNamespaceNumericGrammar() {
        var fields=StrictJson.object().put("expected_revision",1).put("decision_key","borrow_from_holy_order")
                .put("expected_outcome","event_window").put("expected_event_definition_key","holy_order.0200");
        assertDoesNotThrow(()->GuiCodec.decode(GuiContract.Method.CONFIRM_OUTCOME.originalName(),fields));
        for(String bad:Set.of("holy_order","1holy.200","holy-order.200","holy_order.choice","holy_order.12345678901","holy_order.200.extra"))
            assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(GuiContract.Method.CONFIRM_OUTCOME.originalName(),fields.deepCopy().put("expected_event_definition_key",bad)));
        assertThrows(IllegalArgumentException.class,()->GuiPublicMetadata.beforeSource(raw("{}"),raw("null")));
        assertThrows(IllegalArgumentException.class,()->GuiPublicMetadata.beforeSource(raw("[]"),raw("{}")));
    }
}
