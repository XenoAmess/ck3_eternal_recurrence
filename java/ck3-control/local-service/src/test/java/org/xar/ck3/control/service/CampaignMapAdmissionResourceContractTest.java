package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import jakarta.ws.rs.core.Response;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.CampaignMapAdmission;
import org.xar.ck3.control.contracts.CampaignMapAdmissionComposer;
import org.xar.ck3.control.contracts.CampaignMapComposeRequest;
import org.xar.ck3.control.contracts.CampaignMapProtocol;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;

/** Changed adapter path only; full warm/feeder/Queue/reducer acceptance remains MapAdmissionCi. */
class CampaignMapAdmissionResourceContractTest {
    private static CampaignMapComposeRequest request() {
        return new CampaignMapComposeRequest("map-resource-fixture",
                new GameGeneration(200332, new PythonOnlyUInt64(new BigInteger("134371375868945259"))),
                "fixture-recording", new SavedFrame("native:1", 2, 1, 53279400, 40526, "fixture-episode"),
                "2026-10-23T00:00:00Z");
    }

    @Test void persistedTypedRequestPassesThroughAdapterAsOriginalRawReceiptBytes() {
        byte[] input = request().toCanonicalBytes();
        try (Response response = new CampaignMapAdmissionResource().compose(input)) {
            assertEquals(200, response.getStatus());
            byte[] actual = assertInstanceOf(byte[].class, response.getEntity());
            assertArrayEquals(CampaignMapAdmissionComposer.compose(input), actual);
            assertEquals(request().nativeLaunch(), CampaignMapAdmission.fromJson(StrictJson.parse(actual)).game());
            assertEquals(CampaignMapProtocol.PRODUCER, response.getHeaderString(CampaignMapProtocol.PRODUCER_HEADER));
            assertEquals(CampaignMapProtocol.PRODUCER_VERSION, response.getHeaderString(CampaignMapProtocol.VERSION_HEADER));
            assertEquals(CampaignMapComposeRequest.SCHEMA, response.getHeaderString(CampaignMapProtocol.CONTRACT_HEADER));
        }
    }

    @Test void identityRecordSerializationPreservesTheExistingConsumerFieldNames() throws Exception {
        try (Response response = new CampaignMapAdmissionResource().identity()) {
            assertEquals(200, response.getStatus());
            CampaignMapProtocol.ProducerIdentity identity = assertInstanceOf(
                    CampaignMapProtocol.ProducerIdentity.class, response.getEntity());
            ObjectMapper mapper = new ObjectMapper();
            ObjectNode wire = (ObjectNode) mapper.readTree(mapper.writeValueAsBytes(identity));
            assertEquals(8, wire.size());
            assertEquals(CampaignMapComposeRequest.SCHEMA, wire.get("request_schema").textValue());
            assertEquals(CampaignMapProtocol.PRODUCER_VERSION, wire.get("producer_version").textValue());
            assertEquals("org.xar.ck3.control", wire.get("maven_group_id").textValue());
            assertEquals("ck3-control-local-service", wire.get("maven_artifact_id").textValue());
            assertEquals("0.1.0-SNAPSHOT", wire.get("maven_version").textValue());
            assertEquals(CampaignMapAdmissionResource.class.getName(), wire.get("implementation").textValue());
        }
    }

    @Test void falseVisibilityAndOversizeStillReturnSharedErrorRecordsAndHeaders() {
        ObjectNode malformed = request().toJson(); malformed.put("game_map_visible", false);
        byte[][] inputs = {StrictJson.canonical(malformed, StrictJson.INPUT_MAX_BYTES),
                new byte[StrictJson.INPUT_MAX_BYTES + 1]};
        int[] statuses = {400, 413};
        for (int index = 0; index < inputs.length; index++) {
            try (Response response = new CampaignMapAdmissionResource().compose(inputs[index])) {
                assertEquals(statuses[index], response.getStatus());
                CampaignMapProtocol.ContractError error = assertInstanceOf(
                        CampaignMapProtocol.ContractError.class, response.getEntity());
                assertEquals("xar.java-contract-error/v1", error.schema());
                assertEquals("rejected", error.status());
                assertEquals(CampaignMapComposeRequest.SCHEMA, response.getHeaderString(CampaignMapProtocol.CONTRACT_HEADER));
            }
        }
    }
}
