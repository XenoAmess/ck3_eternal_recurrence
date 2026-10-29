package org.xar.ck3.control.service;

import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.TestProfile;
import io.quarkus.test.junit.QuarkusTestProfile;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

@QuarkusTest
@TestProfile(ProjectionArtifactInputHttpTest.MachineProfile.class)
class ProjectionArtifactInputHttpTest {
    public static final class MachineProfile implements QuarkusTestProfile {
        @Override public java.util.Map<String, String> getConfigOverrides() {
            return java.util.Map.of("xar.projection.machine-id", org.xar.ck3.control.build.WindowsJobProcess.currentMachineId());
        }
    }
    @TestHTTPResource("/v1/projections/artifact-inputs") URI endpoint;
    @Test void theSameResidentHostDeclaresAnExplicitAbsentScopeWithoutOpeningAnySlot() throws Exception {
        var result = HttpClient.newHttpClient().send(HttpRequest.newBuilder(endpoint).GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, result.statusCode());
        assertEquals("java-quarkus-projection/v1", result.headers().firstValue("X-Xar-Producer").orElseThrow());
        assertEquals("xar.projection-call/v1", result.headers().firstValue("X-Xar-Contract-Revision").orElseThrow());
        var root = StrictJson.parse(result.body()); assertEquals(4, root.size());
        assertEquals("xar.projection-artifact-input-context/v1", root.path("schema").textValue()); assertTrue(root.get("artifact_inputs").isNull());
    }
}
