package org.xar.ck3.control.service;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.xar.ck3.control.contracts.CampaignMapAdmissionComposer;
import org.xar.ck3.control.contracts.CampaignMapComposeRequest;
import org.xar.ck3.control.contracts.CampaignMapProtocol;
import org.xar.ck3.control.contracts.StrictJson;

/** HTTP adapter only: it never reads a game, file, process, ledger or native pipe. */
@Path("/v1/map-admissions")
@Produces(MediaType.APPLICATION_JSON)
public final class CampaignMapAdmissionResource {
    @POST
    @Path("/compose")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response compose(byte[] requestBody) {
        if (requestBody == null || requestBody.length == 0) {
            return rejected("request body must be a nonempty JSON object");
        }
        if (requestBody.length > StrictJson.INPUT_MAX_BYTES) {
            return identified(Response.status(Response.Status.REQUEST_ENTITY_TOO_LARGE))
                    .entity(CampaignMapProtocol.rejected("request body exceeds 65536 bytes"))
                    .build();
        }
        try {
            // Return raw canonical bytes; the Python-only FILETIME must not pass through a numeric DTO.
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
        return identified(Response.ok(CampaignMapProtocol.identity(
                CampaignMapAdmissionResource.class.getName()))).build();
    }

    private static Response rejected(String message) {
        return identified(Response.status(Response.Status.BAD_REQUEST))
                .entity(CampaignMapProtocol.rejected(message)).build();
    }

    private static Response.ResponseBuilder identified(Response.ResponseBuilder response) {
        return response.header(CampaignMapProtocol.PRODUCER_HEADER, CampaignMapProtocol.PRODUCER)
                .header(CampaignMapProtocol.VERSION_HEADER, CampaignMapProtocol.PRODUCER_VERSION)
                .header(CampaignMapProtocol.CONTRACT_HEADER, CampaignMapComposeRequest.SCHEMA);
    }
}
