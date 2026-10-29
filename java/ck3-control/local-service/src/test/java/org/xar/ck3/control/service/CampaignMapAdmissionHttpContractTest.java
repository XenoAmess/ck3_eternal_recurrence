package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.math.BigInteger;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.CampaignMapAdmission;
import org.xar.ck3.control.contracts.CampaignMapAdmissionComposer;
import org.xar.ck3.control.contracts.CampaignMapComposeRequest;
import org.xar.ck3.control.contracts.CampaignMapProtocol;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;

/** Focused same-host adoption delta; does not replace the original complete Python consumer step. */
@QuarkusTest
class CampaignMapAdmissionHttpContractTest {
    @TestHTTPResource("/v1/map-admissions/compose") URI endpoint;
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    private static CampaignMapComposeRequest request() {
        return new CampaignMapComposeRequest("map-http-fixture",
                new GameGeneration(200332, new PythonOnlyUInt64(new BigInteger("134371375868945259"))),
                "fixture-recording", new SavedFrame("native:1", 2, 1, 53279400, 40526, "fixture-episode"),
                "2026-10-23T00:00:00Z");
    }

    @Test void sharedSerializedRequestProducesTheSameRawReceiptAndAdvertisedIdentityOnActualHttp() throws Exception {
        byte[] serialized = request().toCanonicalBytes();
        HttpResponse<byte[]> response = post(serialized);
        assertEquals(200, response.statusCode());
        headers(response);
        assertTrue(response.headers().firstValue("Content-Type").orElseThrow().startsWith("application/json"));
        assertArrayEquals(CampaignMapAdmissionComposer.compose(serialized), response.body());
        assertEquals(request().nativeLaunch(), CampaignMapAdmission.fromJson(StrictJson.parse(response.body())).game());
        HttpResponse<byte[]> identity = client.send(HttpRequest.newBuilder(base().resolve("/v1/map-admissions/identity"))
                .timeout(Duration.ofSeconds(20)).GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, identity.statusCode());
        headers(identity);
        JsonNode actual = StrictJson.parse(identity.body());
        assertEquals(CampaignMapProtocol.IDENTITY_SCHEMA, actual.get("schema").textValue());
        assertEquals(CampaignMapComposeRequest.SCHEMA, actual.get("request_schema").textValue());
        assertEquals(CampaignMapProtocol.PRODUCER_VERSION, actual.get("producer_version").textValue());
    }

    @Test void actualHttpRejectsFalseVisibilityUsingTheSameSharedErrorWireContract() throws Exception {
        ObjectNode malformed = request().toJson(); malformed.put("decision_text_visible", false);
        HttpResponse<byte[]> response = post(StrictJson.canonical(malformed, StrictJson.INPUT_MAX_BYTES));
        assertEquals(400, response.statusCode());
        headers(response);
        JsonNode error = StrictJson.parse(response.body());
        assertEquals(3, error.size());
        assertEquals(CampaignMapProtocol.ERROR_SCHEMA, error.get("schema").textValue());
        assertEquals("rejected", error.get("status").textValue());
        assertTrue(error.get("error").isTextual());
    }

    private HttpResponse<byte[]> post(byte[] body) throws Exception {
        return client.send(HttpRequest.newBuilder(base().resolve("/v1/map-admissions/compose"))
                .timeout(Duration.ofSeconds(20)).header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofByteArray(body)).build(), HttpResponse.BodyHandlers.ofByteArray());
    }

    private URI base() { return URI.create("http://127.0.0.1:" + endpoint.getPort()); }

    private static void headers(HttpResponse<byte[]> response) {
        assertEquals(CampaignMapProtocol.PRODUCER, response.headers().firstValue(CampaignMapProtocol.PRODUCER_HEADER).orElseThrow());
        assertEquals(CampaignMapProtocol.PRODUCER_VERSION, response.headers().firstValue(CampaignMapProtocol.VERSION_HEADER).orElseThrow());
        assertEquals(CampaignMapComposeRequest.SCHEMA, response.headers().firstValue(CampaignMapProtocol.CONTRACT_HEADER).orElseThrow());
    }
}
