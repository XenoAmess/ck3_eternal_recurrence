package org.xar.ck3.control.governance.crownauthority;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class CrownAuthorityProjectionCatalogTest {
    @Test void allOriginalProducerVectorsTraverseTheRegisteredDomainAndCommonWire() throws IOException {
        assertEquals(20, CrownAuthorityProjectionChecks.golden(fixture()));
    }
    @Test void rawWrongFieldsAndIntegerTokensReachTheActualDomainDecoder() throws IOException {
        assertEquals(25, CrownAuthorityProjectionChecks.rawBoundaries(fixture()));
    }
    @Test void packagedServiceDescriptorAndDeclaredRoleProfileAreReal() {
        assertEquals(3, CrownAuthorityProjectionChecks.discovery());
    }
    private static JsonNode fixture() throws IOException {
        try (InputStream stream = CrownAuthorityProjectionCatalogTest.class.getResourceAsStream("/crownauthority/original-producer-golden.json")) {
            assertNotNull(stream, "the retained actual original producer golden is mandatory");
            return StrictJson.parse(stream.readAllBytes());
        }
    }
}
