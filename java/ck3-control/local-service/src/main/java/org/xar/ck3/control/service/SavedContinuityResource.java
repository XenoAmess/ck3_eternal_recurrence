package org.xar.ck3.control.service;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.ContinuityJson;

/** Pure reducer hosted by the existing single loopback service. */
@Path("/v1/continuity/saved-attachment")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public final class SavedContinuityResource {
    public static final String PRODUCER = "java-quarkus-saved-continuity/v1";
    public record Error(String schema, String status, String error) { }
    @POST
    public Response reduce(byte[] body) {
        try {
            var input=SavedContinuityAttachment.decode(body);
            return identified(Response.ok(ContinuityJson.canonical(SavedContinuityAttachment.reduce(input).toJson()), MediaType.APPLICATION_JSON_TYPE),
                    SavedContinuityAttachment.requestSchema(input)).build();
        } catch (IllegalArgumentException error) {
            return identified(Response.status(Response.Status.BAD_REQUEST),SavedContinuityAttachment.REQUEST_SCHEMA)
                    .entity(new Error("xar.java-contract-error/v1", "rejected", error.getMessage())).build();
        }
    }
    private static Response.ResponseBuilder identified(Response.ResponseBuilder response,String contractRevision) {
        return response.header("X-Xar-Producer", PRODUCER)
                .header("X-Xar-Contract-Revision", contractRevision);
    }
}
