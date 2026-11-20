package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Reject malformed DATA only. No template sources, application pin, Root, Native or COMPLETE role is invented. */
class RootUnboundPublicDefinitionsCodecTest {
    @Test void unboundRequestRejectsApplicationRefEvenWhenNullOrOnlyALabel() {
        for (var supplied : java.util.List.<com.fasterxml.jackson.databind.JsonNode>of(
                com.fasterxml.jackson.databind.node.NullNode.getInstance(),
                com.fasterxml.jackson.databind.node.TextNode.valueOf("future"), StrictJson.object())) {
            var request = StrictJson.object().put("schema", RootRuntimeDefinitions.UNBOUND_APPLICATION_SCHEMA);
            request.set("applicationRef", supplied);
            var failed = assertThrows(IOException.class, () -> RootRuntimeDefinitions.decodeUnboundApplication(StrictJson.canonical(request)));
            assertTrue(failed.getMessage().contains("applicationRef"));
        }
    }
    @Test void noLeaseSourceOrDomainDefaultsTurnAnIncompleteRequestIntoV7() {
        var request = StrictJson.object().put("schema", RootRuntimeDefinitions.UNBOUND_APPLICATION_SCHEMA);
        request.put("machineId", "software-data-machine");
        var failed = assertThrows(IOException.class, () -> RootRuntimeDefinitions.decodeUnboundApplication(StrictJson.canonical(request)));
        assertTrue(failed.getMessage().contains("every non-application"));
        request.put("COMPLETE", true);
        assertThrows(IOException.class, () -> RootRuntimeDefinitions.decodeUnboundApplication(StrictJson.canonical(request)));
    }
    @Test void completeConfigurationSchemaCannotMasqueradeAsUnboundApplicationData() {
        var request = StrictJson.object().put("schema", RootRuntimeDefinitionModel.SCHEMA);
        var failed = assertThrows(IOException.class, () -> RootRuntimeDefinitions.decodeUnboundApplication(StrictJson.canonical(request)));
        assertTrue(failed.getMessage().contains("separate input shape"));
    }
}
