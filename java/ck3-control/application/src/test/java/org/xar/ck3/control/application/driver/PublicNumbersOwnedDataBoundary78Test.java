package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.DoubleNode;
import com.fasterxml.jackson.databind.node.IntNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Direct public DATA behavior from the original publicNumbers source. */
public final class PublicNumbersOwnedDataBoundary78Test {
    @Test
    void successfulNumericChecksPreserveTheLaterCallerCallbackFault() {
        ObjectNode ordinary = JsonNodeFactory.instance.objectNode();
        ArrayNode values = ordinary.putArray("safe/~values");
        values.add(new IntNode(7));
        values.add(new BigIntegerNode(new BigInteger("9007199254740991")));
        values.add(new BigIntegerNode(new BigInteger("-9007199254740991")));
        values.add(new DoubleNode(-0.0));
        values.add(new DoubleNode(1.25));
        PublicSnapshotCodec.publicNumbers(ordinary, "/ordinary");
        assertEquals(new BigInteger("-9007199254740991"), values.get(2).bigIntegerValue());
        assertEquals(Double.doubleToRawLongBits(-0.0),
                Double.doubleToRawLongBits(values.get(3).doubleValue()));

        IllegalStateException sentinel = new IllegalStateException("later public object callback");
        JsonNode callerNode = new LaterObjectFaultNode(sentinel);
        IllegalStateException failure = assertThrows(IllegalStateException.class,
                () -> PublicSnapshotCodec.publicNumbers(callerNode, "/caller"));
        assertSame(sentinel, failure);
    }

    @Test
    void numericRejectionsKeepOriginalPathsAndStopBeforeLaterTraversalFaults() {
        IllegalStateException laterFault = new IllegalStateException("later public floating conversion");
        ObjectNode root = JsonNodeFactory.instance.objectNode();
        ArrayNode rows = root.putArray("a/b~c");
        rows.add(new BigIntegerNode(new BigInteger("9007199254740992")));
        rows.add(new FloatingFaultNode(laterFault));
        assertPublicError(root, "/public",
                "unqualified unsafe numeric public role at /public/a~1b~0c/0");

        JsonNode negative = new BigIntegerNode(new BigInteger("-9007199254740992"));
        assertPublicError(negative, "negative",
                "unqualified unsafe numeric public role at negative");

        // Null is a public path argument, not an internal successful message value.
        JsonNode nonfinite = new DoubleNode(Double.POSITIVE_INFINITY);
        assertPublicError(nonfinite, null, "nonfinite public float at null");
    }

    private static void assertPublicError(JsonNode value, String path, String expectedMessage) {
        ContractViolationException failure = assertThrows(ContractViolationException.class,
                () -> PublicSnapshotCodec.publicNumbers(value, path));
        assertEquals(ContractViolationException.class, failure.getClass());
        assertEquals(expectedMessage, failure.getMessage());
        assertNull(failure.getCause());
    }

    /** Public numeric conversions expose caller state; no private validator state is observed. */
    private static final class LaterObjectFaultNode extends BigIntegerNode {
        private static final long serialVersionUID = 1L;
        private final transient IllegalStateException sentinel;
        private transient boolean integerRead;
        private transient boolean floatingRead;

        private LaterObjectFaultNode(IllegalStateException sentinel) {
            super(BigInteger.ZERO);
            this.sentinel = sentinel;
        }

        @Override
        public BigInteger bigIntegerValue() {
            if (integerRead || floatingRead) {
                throw new IllegalStateException("caller integer conversion was repeated or moved");
            }
            integerRead = true;
            return super.bigIntegerValue();
        }

        @Override
        public boolean isFloatingPointNumber() {
            return true;
        }

        @Override
        public double doubleValue() {
            if (!integerRead || floatingRead) {
                throw new IllegalStateException("caller floating conversion was repeated or moved");
            }
            floatingRead = true;
            return 0.5;
        }

        @Override
        public boolean isObject() {
            if (!integerRead || !floatingRead) {
                throw new IllegalStateException("caller object inspection preceded numeric conversions");
            }
            throw sentinel;
        }
    }

    private static final class FloatingFaultNode extends DoubleNode {
        private static final long serialVersionUID = 1L;
        private final transient IllegalStateException sentinel;

        private FloatingFaultNode(IllegalStateException sentinel) {
            super(0.5);
            this.sentinel = sentinel;
        }

        @Override
        public double doubleValue() {
            throw sentinel;
        }
    }
}
