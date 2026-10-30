package org.xar.ck3.control.wave2.events.choiceplanning;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;

final class UnavailableGuiV2ContextTest {
    @Test void actualNativeUnavailableV2RetainsNonActionableNullOptionsAndAcceptsExactVersionPair() throws Exception {
        try(InputStream input=getClass().getResourceAsStream("/event-gui-v2/ambiguous-no-native-gate.v2.json")) {
            assertNotNull(input);ObjectNode context=(ObjectNode)new ObjectMapper().readTree(input);
            assertTrue(context.get("options").isNull());
            assertTrue(UnavailableEventContextProjection.valid(context,BigInteger.valueOf(16777257),BigInteger.valueOf(741221),BigInteger.valueOf(17)));
            ObjectNode wrong=context.deepCopy();wrong.put("schema_version",1);
            assertFalse(UnavailableEventContextProjection.valid(wrong,BigInteger.valueOf(16777257),BigInteger.valueOf(741221),BigInteger.valueOf(17)));
            ObjectNode actionable=context.deepCopy();actionable.putArray("options");
            assertFalse(UnavailableEventContextProjection.valid(actionable,BigInteger.valueOf(16777257),BigInteger.valueOf(741221),BigInteger.valueOf(17)));
        }
    }
}
