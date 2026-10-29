package org.xar.ck3.control.wave2.finance.feastterminal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import org.junit.jupiter.api.Test;

/** Default JUnit exercises real catalog discovery and typed dispatch, without Python/process/host launch. */
final class ProbeCompiledTerminalConsumersTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test
    void actualCatalogUsesTheTerminalTypedPortForEveryOriginalProducerCase() throws IOException {
        var result = ProbeCompiledTerminalConsumers.verifyRegisteredProjection(golden());
        assertEquals(48, result.cases());
        assertEquals(41, result.accepted());
        assertEquals(7, result.rejected());
    }

    @Test
    void rejectsDuplicateNamesWrongBooleanAndUnknownGoldenSchemaBeforeDispatch() throws IOException {
        ObjectNode duplicate = golden().deepCopy();
        ((ObjectNode) duplicate.get("cases").get(1)).set("name", duplicate.get("cases").get(0).get("name"));
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledTerminalConsumers.verifyRegisteredProjection(duplicate));
        ObjectNode wrongBoolean = golden().deepCopy();
        ((ObjectNode) wrongBoolean.get("cases").get(0)).put("accepted", 1);
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledTerminalConsumers.verifyRegisteredProjection(wrongBoolean));
        ObjectNode wrongSchema = golden().deepCopy();
        wrongSchema.put("schema", "unknown");
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledTerminalConsumers.verifyRegisteredProjection(wrongSchema));
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = ProbeCompiledTerminalConsumersTest.class.getResourceAsStream("/feastterminal/terminal-producer-golden-v1.json")) {
            if (input == null) throw new IOException("required actual terminal producer golden unavailable");
            return JSON.readTree(input.readAllBytes());
        }
    }
}
