package org.xar.ck3.control.service;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.xar.ck3.control.contracts.CampaignMapAdmissionComposer;
import org.xar.ck3.control.contracts.StrictJson;

/** HTTP adapter only: it never reads a game, file, process, ledger or native pipe. */
@Path("/v1/map-admissions")
@Produces(MediaType.APPLICATION_JSON)
public final class CampaignMapAdmissionResource {
    public static final String PRODUCER = "java-quarkus-map-admission/v1";
    public static final String PRODUCER_VERSION = "0.1.0";
    public static final String REQUEST_SCHEMA = "xar.java-campaign-map-compose-request/v1";

    public record ContractError(String schema, String status, String error) { }

    public record ProducerIdentity(
            String schema,
            String producer,
            String producer_version,
            String request_schema,
            String implementation,
            String maven_group_id,
            String maven_artifact_id,
            String maven_version) { }

    @POST
    @Path("/compose")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response compose(byte[] requestBody) {
        if (requestBody == null || requestBody.length == 0) {
            return rejected("request body must be a nonempty JSON object");
        }
        if (requestBody.length > StrictJson.INPUT_MAX_BYTES) {
            return identified(Response.status(Response.Status.REQUEST_ENTITY_TOO_LARGE))
                    .entity(new ContractError("xar.java-contract-error/v1", "rejected",
                            "request body exceeds 65536 bytes"))
                    .build();
        }
        try {
            // The contracts module validates raw tokens and produces canonical
            // Python-opaque JSON bytes. Do not reparse through a numeric DTO or
            // let Jackson serialize this byte array as a JSON/base64 value.
            byte[] admission = CampaignMapAdmissionComposer.compose(requestBody);
            if (admission.length == 0 || admission.length > StrictJson.OUTPUT_MAX_BYTES) {
                return rejected("admission exceeds the original 16384-byte consumer limit");
            }
            return identified(Response.ok(admission, MediaType.APPLICATION_JSON_TYPE)).build();
        } catch (IllegalArgumentException error) {
            String message = error.getMessage();
            if (message == null || message.isBlank()) {
                message = "request does not satisfy the map admission contract";
            }
            return rejected(message.length() <= 512 ? message : message.substring(0, 512));
        }
    }

    @GET
    @Path("/identity")
    public Response identity() {
        ProducerIdentity identity = new ProducerIdentity(
                "xar.java-map-admission-producer-identity/v1", PRODUCER, PRODUCER_VERSION,
                REQUEST_SCHEMA, CampaignMapAdmissionResource.class.getName(),
                "org.xar.ck3.control", "ck3-control-local-service", "0.1.0-SNAPSHOT");
        return identified(Response.ok(identity)).build();
    }

    private static Response rejected(String message) {
        return identified(Response.status(Response.Status.BAD_REQUEST))
                .entity(new ContractError("xar.java-contract-error/v1", "rejected", message))
                .build();
    }

    private static Response.ResponseBuilder identified(Response.ResponseBuilder response) {
        return response.header("X-Xar-Producer", PRODUCER)
                .header("X-Xar-Producer-Version", PRODUCER_VERSION)
                .header("X-Xar-Contract-Revision", REQUEST_SCHEMA);
    }
}
