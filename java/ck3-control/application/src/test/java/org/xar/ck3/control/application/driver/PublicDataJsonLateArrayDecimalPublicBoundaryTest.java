package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrowsExactly;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

public class PublicDataJsonLateArrayDecimalPublicBoundaryTest {
    @Test
    public void lateArrayDecimalsKeepTokensAndFirstFailureWithoutChangingInputs() {
        RawJson original = raw("{\"rows\":[17,\"head\",true,null,{\"tag\":\"old\"},-0.00e+2,[false,1.2300E+2],{\"tail\":[0,4.500]}]}");
        JsonNode projected = OpportunityJson.toNode(new OpportunityJson.Obj(Map.of(
                "rows", new OpportunityJson.Arr(List.of(
                        new OpportunityJson.IntegerValue(BigInteger.valueOf(18)),
                        new OpportunityJson.Text("new"),
                        new OpportunityJson.Bool(false),
                        OpportunityJson.Nil.INSTANCE,
                        new OpportunityJson.Obj(Map.of("tag", new OpportunityJson.Text("kept"))),
                        new OpportunityJson.DecimalValue("0.0"),
                        new OpportunityJson.Arr(List.of(new OpportunityJson.Bool(true),
                                new OpportunityJson.DecimalValue("123.0"))),
                        new OpportunityJson.Obj(Map.of("tail", new OpportunityJson.Arr(List.of(
                                new OpportunityJson.IntegerValue(BigInteger.ONE),
                                new OpportunityJson.DecimalValue("4.5"))))))))));
        byte[] originalBefore = original.bytes();
        String projectedBefore = projected.toString();
        byte[] expected = ("{\"rows\":[18,\"new\",false,null,{\"tag\":\"kept\"},-0.00e+2,"
                + "[true,1.2300E+2],{\"tail\":[1,4.500]}]}").getBytes(StandardCharsets.UTF_8);

        RawJson withTail = raw("{\"rows\":[0,\"prefix\",1.20,{\"gone\":[-0.00,9.90]}]}");
        JsonNode changed = retainedProjection("2.0");
        JsonNode equal = retainedProjection("1.200");
        byte[] tailBefore = withTail.bytes();
        String changedBefore = changed.toString();
        String equalBefore = equal.toString();

        // Added after a parent source-level suffix counterexample; not a blind fixture.
        RawJson suffixOriginal = raw("{\"a\":[0,1.20,2]}");
        JsonNode suffixProjected = OpportunityJson.toNode(new OpportunityJson.Obj(Map.of(
                "a", new OpportunityJson.Arr(List.of(
                        new OpportunityJson.IntegerValue(BigInteger.valueOf(9)),
                        new OpportunityJson.DecimalValue("1.200"),
                        new OpportunityJson.IntegerValue(BigInteger.valueOf(8)))))));
        byte[] suffixBefore = suffixOriginal.bytes();
        String suffixProjectedBefore = suffixProjected.toString();
        byte[] suffixExpected = "{\"a\":[9,1.20,8]}".getBytes(StandardCharsets.UTF_8);

        for (boolean fullMaterial : new boolean[] {false, true}) {
            assertArrayEquals(expected, encode(fullMaterial, projected, original).bytes());
            assertArrayEquals(originalBefore, original.bytes());
            assertEquals(projectedBefore, projected.toString());

            assertArrayEquals(suffixExpected, encode(fullMaterial, suffixProjected, suffixOriginal).bytes());
            assertArrayEquals(suffixBefore, suffixOriginal.bytes());
            assertEquals(suffixProjectedBefore, suffixProjected.toString());

            // The retained late element fails before the removed nested tail is checked.
            ContractViolationException changedFailure = assertThrowsExactly(ContractViolationException.class,
                    () -> encode(fullMaterial, changed, withTail));
            assertEquals("original decimal value changed at /rows/2", changedFailure.getMessage());
            assertNull(changedFailure.getCause());
            assertArrayEquals(tailBefore, withTail.bytes());
            assertEquals(changedBefore, changed.toString());

            // Once the retained decimal is equal, the first removed nested decimal is observable.
            ContractViolationException removedFailure = assertThrowsExactly(ContractViolationException.class,
                    () -> encode(fullMaterial, equal, withTail));
            assertEquals("original decimal removed at /rows/3/gone/0", removedFailure.getMessage());
            assertNull(removedFailure.getCause());
            assertArrayEquals(tailBefore, withTail.bytes());
            assertEquals(equalBefore, equal.toString());
        }
    }

    private static JsonNode retainedProjection(String token) {
        return OpportunityJson.toNode(new OpportunityJson.Obj(Map.of(
                "rows", new OpportunityJson.Arr(List.of(
                        new OpportunityJson.IntegerValue(BigInteger.ZERO),
                        new OpportunityJson.Text("prefix"),
                        new OpportunityJson.DecimalValue(token))))));
    }

    private static RawJson raw(String text) {
        return new RawJson(text.getBytes(StandardCharsets.UTF_8));
    }

    private static RawJson encode(boolean fullMaterial, JsonNode projected, RawJson original) {
        return fullMaterial ? PublicDataJson.encodePreservingFullMaterial(projected, original)
                : PublicDataJson.encodePreservingDecimals(projected, original);
    }
}
