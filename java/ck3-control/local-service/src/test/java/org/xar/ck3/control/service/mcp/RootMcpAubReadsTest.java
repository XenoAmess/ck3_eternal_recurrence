package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

final class RootMcpAubReadsTest {
    @Test void optionalRevisionPreservesMissingNullAndValueAcrossPublicJson() {
        assertInstanceOf(RootMcpAubReads.Missing.class, decode("{}").revision());
        assertInstanceOf(RootMcpAubReads.NullValue.class, decode("{\"expected_revision\":null}").revision());
        assertEquals(new RootMcpAubReads.Value(BigInteger.valueOf(7)), decode("{\"expected_revision\":7}").revision());
        assertEquals(new RootMcpAubReads.Value(BigInteger.ZERO), decode("{\"expected_revision\":0}").revision());
        assertEquals(Optional.empty(), decode("{}").revision().expected());
        assertEquals(Optional.empty(), decode("{\"expected_revision\":null}").revision().expected());
        assertEquals(Optional.of(BigInteger.valueOf(7)), decode("{\"expected_revision\":7}").revision().expected());
        assertEquals(new RootMcpAubReads.Value(new BigInteger("18446744073709551615")),
                decode("{\"expected_revision\":\"18446744073709551615\"}").revision());
        assertEquals(new RootMcpAubReads.Value(BigInteger.ZERO),decode("{\"expected_revision\":\"0\"}").revision());
    }
    @Test void wrongTypesUnsafeIntegersAndExtraNativeFieldsCannotReachTheRootRead() {
        for (String token : new String[] {"true", "1.0", "-1", "9007199254740992",
                "\"01\"","\"+1\"","\"-1\"","\"1.0\"","\"18446744073709551616\"","[]","{}"})
            assertThrows(IllegalArgumentException.class, () -> decode("{\"expected_revision\":" + token + "}"), token);
        assertThrows(IllegalArgumentException.class, () -> decode("{\"expected_revision\":7,\"expected_player_character_id\":1}"));
    }
    private static RootMcpAubReads.Request decode(String json) {
        return RootMcpAubReads.decode(new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,
                Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8)))));
    }
}
