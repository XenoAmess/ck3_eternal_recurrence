package org.xar.ck3.control.service;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayServiceWire;

/** Adapter in the existing single Quarkus host. It consumes supplied compact inputs without native authority. */
@Path("/v1/planning/ordinary-sway")
@Produces(MediaType.APPLICATION_JSON)
public final class OrdinarySwayResource {
    public record ContractError(String schema, String status, String error) { }

    @POST
    @Path("/stage")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response stage(byte[] raw) {
        try {
            StrictJson.require(raw != null && raw.length > 0 && raw.length <= StrictJson.INPUT_MAX_BYTES,
                    "bounded nonempty ordinary stage request required");
            byte[] output = OrdinarySwayServiceWire.stage(raw);
            return Response.ok(output, MediaType.APPLICATION_JSON_TYPE)
                    .header("X-Xar-Producer", "java-ordinary-sway-service/v1").build();
        } catch (IllegalArgumentException failure) {
            return Response.status(Response.Status.BAD_REQUEST).entity(new ContractError(
                    "xar.java-contract-error/v1", "rejected", failure.getMessage())).build();
        }
    }
}
