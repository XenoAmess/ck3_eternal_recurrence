package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Ordinary public projection DATA regressions, derived from the frozen original source. */
public final class PublicDataJsonPreserveContainerPublicBoundaryTest {
    private static final int FIXTURE_BYTES = 16_384;

    @Test
    void removedObjectMembersAndArrayTailsRetainDecimalChecks() {
        String[][] scenarios = {
            // R1
            {"{\"keep\":1,\"drop\":{\"nested\":[0,2.0]}}",
                    "{\"keep\":1}",
                    "original decimal removed at /drop/nested/1"},
            // R2
            {"{\"drop\":{\"d\":1.0}}",
                    "{}",
                    "original decimal removed at /drop/d"},
            // R3
            {"{\"items\":[1,{\"nested\":[2.0]}]}",
                    "{\"items\":[1]}",
                    "original decimal removed at /items/1/nested/0"},
            // R4
            {"{\"items\":[{\"d\":1.0}]}",
                    "{\"items\":[]}",
                    "original decimal removed at /items/0/d"}
        };
        for (boolean fullMaterial : new boolean[] {false, true}) {
            for (String[] scenario : scenarios) {
                byte[] originalBefore = scenario[0].getBytes(StandardCharsets.UTF_8);
                byte[] projectedBytes = scenario[1].getBytes(StandardCharsets.UTF_8);
                assertTrue(originalBefore.length <= FIXTURE_BYTES);
                assertTrue(projectedBytes.length <= FIXTURE_BYTES);
                RawJson original = new RawJson(originalBefore);
                JsonNode projected = FullJsonTree.parse(projectedBytes, FIXTURE_BYTES);
                assertTrue(projected.isObject());
                byte[] projectedBefore = FullJsonTree.encode(projected, FIXTURE_BYTES);

                ContractViolationException failure = assertThrows(ContractViolationException.class, () -> {
                    if (fullMaterial) {
                        PublicDataJson.encodePreservingFullMaterial(projected, original);
                    } else {
                        PublicDataJson.encodePreservingDecimals(projected, original);
                    }
                });
                assertEquals(ContractViolationException.class, failure.getClass());
                assertEquals(scenario[2], failure.getMessage());
                assertNull(failure.getCause());
                assertArrayEquals(originalBefore, original.bytes());
                assertArrayEquals(projectedBefore, FullJsonTree.encode(projected, FIXTURE_BYTES));
            }
        }
    }

    @Test
    void preservingFirstFailureFollowsRetainedAndRemovedDataOrder() {
        String[][] scenarios = {
            // O1
            {"{\"removed\":2.0,\"kept\":1.0}",
                    "{\"kept\":1}",
                    "original decimal category changed at /kept"},
            // O2
            {"{\"z\":1.0,\"a\":2.0}",
                    "{\"z\":1,\"a\":2}",
                    "original decimal category changed at /a"},
            // O3
            {"{\"dropZ\":3.0,\"dropA\":4.0,\"keep\":0}",
                    "{\"keep\":0}",
                    "original decimal removed at /dropZ"},
            // O4
            {"{\"items\":[1.0,2.0]}",
                    "{\"items\":[1]}",
                    "original decimal category changed at /items/0"}
        };
        for (boolean fullMaterial : new boolean[] {false, true}) {
            for (String[] scenario : scenarios) {
                byte[] originalBefore = scenario[0].getBytes(StandardCharsets.UTF_8);
                byte[] projectedBytes = scenario[1].getBytes(StandardCharsets.UTF_8);
                assertTrue(originalBefore.length <= FIXTURE_BYTES);
                assertTrue(projectedBytes.length <= FIXTURE_BYTES);
                RawJson original = new RawJson(originalBefore);
                JsonNode projected = FullJsonTree.parse(projectedBytes, FIXTURE_BYTES);
                assertTrue(projected.isObject());
                byte[] projectedBefore = FullJsonTree.encode(projected, FIXTURE_BYTES);

                ContractViolationException failure = assertThrows(ContractViolationException.class, () -> {
                    if (fullMaterial) {
                        PublicDataJson.encodePreservingFullMaterial(projected, original);
                    } else {
                        PublicDataJson.encodePreservingDecimals(projected, original);
                    }
                });
                assertEquals(ContractViolationException.class, failure.getClass());
                assertEquals(scenario[2], failure.getMessage());
                assertNull(failure.getCause());
                assertArrayEquals(originalBefore, original.bytes());
                assertArrayEquals(projectedBefore, FullJsonTree.encode(projected, FIXTURE_BYTES));
            }
        }
    }

    @Test
    void nestedNondecimalProjectionKeepsOutputOrderAndInputsUnchanged() {
        for (boolean fullMaterial : new boolean[] {false, true}) {
            // S1
            byte[] originalBefore = "{\"z\":{\"drop\":{\"n\":3},\"a\":2},\"items\":[3,1,{\"drop\":\"x\"}]}".getBytes(StandardCharsets.UTF_8);
            byte[] projectedBytes = "{\"z\":{\"b\":5,\"a\":2},\"items\":[3,1]}".getBytes(StandardCharsets.UTF_8);
            assertTrue(originalBefore.length <= FIXTURE_BYTES);
            assertTrue(projectedBytes.length <= FIXTURE_BYTES);
            RawJson original = new RawJson(originalBefore);
            JsonNode projected = FullJsonTree.parse(projectedBytes, FIXTURE_BYTES);
            assertTrue(projected.isObject());
            byte[] projectedBefore = FullJsonTree.encode(projected, FIXTURE_BYTES);

            RawJson result = fullMaterial
                    ? PublicDataJson.encodePreservingFullMaterial(projected, original)
                    : PublicDataJson.encodePreservingDecimals(projected, original);
            assertArrayEquals("{\"items\":[3,1],\"z\":{\"a\":2,\"b\":5}}".getBytes(StandardCharsets.UTF_8),
                    result.bytes());
            assertArrayEquals(originalBefore, original.bytes());
            assertArrayEquals(projectedBefore, FullJsonTree.encode(projected, FIXTURE_BYTES));
        }
    }
}
