package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import org.junit.jupiter.api.Test;

final class RootNativePlanJsonTest {
    record Wire(Instant deadline,Duration timeout) {
        Wire { Objects.requireNonNull(deadline); Objects.requireNonNull(timeout); }
    }
    @Test void actualSharedProducerConsumerRoundTripPreservesInstantAndDuration() throws IOException {
        Wire original=new Wire(Instant.parse("2026-10-23T10:00:00.123456789Z"),Duration.ofMillis(1234));
        byte[] raw=RootNativePlanJson.mapper().writeValueAsBytes(original);
        assertEquals(original,RootNativePlanJson.mapper().readValue(raw,Wire.class));
        String text=new String(raw,java.nio.charset.StandardCharsets.UTF_8);
        assertTrue(text.contains("2026-10-23T10:00:00.123456789Z")); assertTrue(text.contains("PT1.234S"));
    }
    @Test void numberBooleanMissingNullOffsetAndUnknownFieldsCannotCoerceTemporalInputs() {
        for(String invalid:new String[]{
                "{\"deadline\":1,\"timeout\":\"PT1S\"}",
                "{\"deadline\":true,\"timeout\":\"PT1S\"}",
                "{\"deadline\":\"2026-10-23T10:00:00Z\",\"timeout\":1.0}",
                "{\"deadline\":\"2026-10-23T10:00:00Z\",\"timeout\":false}",
                "{\"deadline\":\"2026-10-23T10:00:00+00:00\",\"timeout\":\"PT1S\"}",
                "{\"deadline\":null,\"timeout\":\"PT1S\"}",
                "{\"deadline\":\"2026-10-23T10:00:00Z\"}",
                "{\"deadline\":\"2026-10-23T10:00:00Z\",\"timeout\":\"PT1S\",\"alias\":true}"}) {
            assertThrows(IOException.class,()->RootNativePlanJson.mapper().readValue(invalid,Wire.class),invalid);
        }
    }
}
