package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrowsExactly;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.StrictJson;

public class PublicDataJsonDecimalDiagnosticPublicBoundaryTest {
    @Test
    public void literalMemberNamesAndArrayIndicesKeepTheFirstDiagnostic() {
        RawJson original = raw("{\"z\":1.20,\"a/b~\uD83D\uDE00\":[{\"\":-0.00}]}");
        rejectsBoth("original decimal category changed at /a/b~\uD83D\uDE00/0/",
                object("{\"z\":0,\"a/b~\uD83D\uDE00\":[{\"\":0}]}"), original);
        rejectsBoth("original decimal value changed at /a/b~\uD83D\uDE00/0/",
                object("{\"z\":0,\"a/b~\uD83D\uDE00\":[{\"\":2.00}]}"), original);
    }

    @Test
    public void removedSubtreesAndPermittedChangesKeepInputs() {
        rejectsBoth("original decimal removed at /drop/z",
                object("{\"kept\":2}"), raw("{\"drop\":{\"z\":6.70,\"a\":[1.20]},\"kept\":2}"));

        RawJson original = raw("{\"old\":1.20,\"drop\":{\"i\":1},\"arr\":[1,true]}");
        ObjectNode projected = StrictJson.object();
        projected.put("z", "\u6c49");
        projected.set("old", new DecimalTokenNode("1.200"));
        projected.set("arr", object("{\"arr\":[false,null,2]}").get("arr"));
        byte[] originalBefore = original.bytes();
        ObjectNode projectedBefore = projected.deepCopy();
        byte[] expected = "{\"arr\":[false,null,2],\"old\":1.20,\"z\":\"\u6c49\"}"
                .getBytes(StandardCharsets.UTF_8);

        assertArrayEquals(expected, PublicDataJson.encodePreservingDecimals(projected, original).bytes());
        unchanged(originalBefore, projectedBefore, original, projected);
        assertArrayEquals(expected, PublicDataJson.encodePreservingFullMaterial(projected, original).bytes());
        unchanged(originalBefore, projectedBefore, original, projected);
    }

    @Test
    public void deepestDiagnosticsAndDeeperProjectionKeepTheOriginalFailureStage() {
        RawJson objectSource = raw("{\"x\":".repeat(64) + "1.25" + "}".repeat(64));
        rejectsBoth("original decimal category changed at " + "/x".repeat(64),
                objectChain(64), objectSource);

        RawJson mixedSource = raw("{\"x\":[".repeat(32) + "1.25" + "]}".repeat(32));
        ObjectNode mixedProjection = object("{\"x\":[".repeat(32) + "0" + "]}".repeat(32));
        rejectsBoth("original decimal category changed at " + "/x/0".repeat(32),
                mixedProjection, mixedSource);

        // Constructing the deeper projection avoids rejecting it in a parser first.
        // Domain validation precedes the otherwise missing source /first decimal.
        rejectsBoth("bounded complete public DATA node required", objectChain(65),
                raw("{\"first\":1.0}"));
    }

    private static RawJson raw(String json) {
        return new RawJson(json.getBytes(StandardCharsets.UTF_8));
    }

    private static ObjectNode object(String json) {
        return PublicDataJson.object(raw(json));
    }

    private static ObjectNode objectChain(int segments) {
        ObjectNode root = StrictJson.object();
        ObjectNode cursor = root;
        for (int index = 1; index < segments; index++) {
            ObjectNode child = StrictJson.object();
            cursor.set("x", child);
            cursor = child;
        }
        cursor.put("x", 0);
        return root;
    }

    private static void rejectsBoth(String expected, ObjectNode projected, RawJson original) {
        byte[] originalBefore = original.bytes();
        ObjectNode projectedBefore = projected.deepCopy();
        ContractViolationException ordinary = assertThrowsExactly(ContractViolationException.class,
                () -> PublicDataJson.encodePreservingDecimals(projected, original));
        assertEquals(expected, ordinary.getMessage());
        assertNull(ordinary.getCause());
        unchanged(originalBefore, projectedBefore, original, projected);

        ContractViolationException material = assertThrowsExactly(ContractViolationException.class,
                () -> PublicDataJson.encodePreservingFullMaterial(projected, original));
        assertEquals(expected, material.getMessage());
        assertNull(material.getCause());
        unchanged(originalBefore, projectedBefore, original, projected);
    }

    private static void unchanged(byte[] bytes, JsonNode tree, RawJson original, JsonNode projected) {
        assertArrayEquals(bytes, original.bytes());
        assertEquals(tree, projected);
    }
}
