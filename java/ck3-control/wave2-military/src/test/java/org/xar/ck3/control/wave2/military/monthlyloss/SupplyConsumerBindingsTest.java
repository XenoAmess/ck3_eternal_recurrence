package org.xar.ck3.control.wave2.military.monthlyloss;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class SupplyConsumerBindingsTest {
    private static final String OPPORTUNITIES = "{\"schema\":\"xar.military-supply-consumer-request/v1\",\"operation\":\"SUCCESSFUL_OCCURRENCES\",\"arguments\":{\"stock\":3,\"capacity\":100,\"monthly\":-1}}";

    @Test void exactIntegerTokensEnterTheActualProductionAdapter() {
        JsonNode actual = exchange(OPPORTUNITIES);
        assertEquals(3, actual.get("successful_bucket_occurrences").intValue());
        for (String token : new String[] {"3.0", "true", "\"3\"", "9223372036854775808"}) {
            assertThrows(IllegalArgumentException.class, () -> exchange(OPPORTUNITIES.replace("\"stock\":3", "\"stock\":" + token)));
        }
        assertThrows(IllegalArgumentException.class, () -> exchange(OPPORTUNITIES.replace("\"stock\":3", "\"stock\":3,\"stock\":3")));
        assertThrows(IllegalArgumentException.class, () -> exchange(OPPORTUNITIES + " null"));
        assertThrows(IllegalArgumentException.class, () -> exchange(OPPORTUNITIES.replace("\"operation\":", "\"extra\":null,\"operation\":")));
        assertThrows(IllegalArgumentException.class, () -> exchange(OPPORTUNITIES.replace("SUCCESSFUL_OCCURRENCES", "missing-route")));
    }

    @Test void missingAndNullRemainDifferentAtTheOperationContract() {
        JsonNode unknown = exchange(OPPORTUNITIES.replace("\"stock\":3", "\"stock\":null"));
        assertFalse(unknown.get("ready").booleanValue());
        assertThrows(IllegalArgumentException.class, () -> exchange(OPPORTUNITIES.replace("\"stock\":3,", "")));
    }

    @Test void reachedOnlySupplyMutationPreservesUnicodeAndExactLongProvenance() {
        String raw = "{\"schema\":\"xar.military-supply-consumer-request/v1\",\"operation\":\"SUPPLY_COMPONENT\",\"arguments\":{\"result\":{\"conditional_post_supply_raw\":9223372036854775807,\"missing_inputs\":[\"earlier\"],\"标记\":\"供给😀\"},\"inputs\":{\"loaded_supply_state_levels\":[]},\"losses\":{}}}";
        JsonNode actual = exchange(raw);
        assertEquals(Long.MAX_VALUE, actual.get("conditional_post_supply_raw").longValue());
        assertEquals("供给😀", actual.get("标记").textValue());
        assertTrue(actual.get("supply_budget_ready").booleanValue());
        assertEquals(0, actual.get("supply_budget_soldiers").intValue());
        assertEquals("earlier", actual.get("missing_inputs").get(0).textValue());
        JsonNode missing = exchange(raw.replace("\"loaded_supply_state_levels\":[]", "\"loaded_supply_state_levels\":null"));
        assertFalse(missing.has("supply_state_index")); assertFalse(missing.has("supply_budget_ready"));
        assertEquals("loaded_supply_state_levels", missing.get("missing_inputs").get(1).textValue());
    }

    @Test void losslessGzipUsesTheActualProbeReaderAndEnforcesBothBounds() throws IOException {
        byte[] raw = "{\"source\":\"供给😀\",\"integer\":9223372036854775807}".getBytes(StandardCharsets.UTF_8);
        byte[] compressed = gzip(raw);
        assertArrayEquals(raw, ProbeCompiledSupplyConsumers.readGolden(compressed, true));
        assertThrows(IOException.class, () -> ProbeCompiledSupplyConsumers.readGolden(Arrays.copyOf(compressed, compressed.length - 3), true));
        byte[] corrupt = compressed.clone(); corrupt[corrupt.length - 5] ^= 1;
        assertThrows(IOException.class, () -> ProbeCompiledSupplyConsumers.readGolden(corrupt, true));
        assertThrows(IOException.class, () -> ProbeCompiledSupplyConsumers.readGolden(new byte[24 * 1024 + 1], true));
        byte[] bomb = gzip(new byte[160 * 1024 + 1]);
        assertThrows(IOException.class, () -> ProbeCompiledSupplyConsumers.readGolden(bomb, true));
    }
    private static JsonNode exchange(String value) { return StrictJson.parse(SupplyConsumerBindings.exchange(value.getBytes(StandardCharsets.UTF_8)), SupplyConsumerBindings.MAX_BYTES); }
    private static byte[] gzip(byte[] value) throws IOException {
        ByteArrayOutputStream packed = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(packed)) { gzip.write(value); }
        return packed.toByteArray();
    }
}
